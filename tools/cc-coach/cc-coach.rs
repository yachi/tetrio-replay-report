//! cc-coach: grade a human's placements against cold-clear, and roll cold-clear forward from a
//! human's mid-game position. JSONL in, JSONL out, one line per position. Each position is
//! searched single-threaded to a fixed node budget; rayon only parallelises ACROSS positions.
//! Cold-clear's search samples at random, so every search is reseeded first (`seed_for`, the
//! patched `coach_reseed`): same input + same COACH_SEED => byte-identical output.
//!
//! Coordinates: the input is TOP-DOWN (row 0 = top of a 40-row field, this repo's convention).
//! cold-clear is y-UP (field[0] = bottom). `y = 39 - r` is the one flip, done in `to_field` and
//! `cells_td`.
use cold_clear::dag::{advance, coach_reseed, MoveCandidate};
use cold_clear::evaluation::{Evaluator, Standard};
use cold_clear::{BotState, Options};
use libtetris::*;
use rayon::prelude::*;
use serde_json::{json, Value as J};
use std::io::{self, BufRead, Write};

fn piece_of(s: &str) -> Piece {
    match s {
        "I" => Piece::I, "O" => Piece::O, "T" => Piece::T, "L" => Piece::L,
        "J" => Piece::J, "S" => Piece::S, "Z" => Piece::Z,
        _ => panic!("bad piece {:?}", s),
    }
}
fn pname(p: Piece) -> &'static str {
    match p { Piece::I => "I", Piece::O => "O", Piece::T => "T", Piece::L => "L", Piece::J => "J", Piece::S => "S", Piece::Z => "Z" }
}
fn kind_name(k: PlacementKind) -> &'static str {
    match k {
        PlacementKind::None => "none", PlacementKind::Clear1 => "single", PlacementKind::Clear2 => "double",
        PlacementKind::Clear3 => "triple", PlacementKind::Clear4 => "quad", PlacementKind::MiniTspin => "mini_tspin0",
        PlacementKind::MiniTspin1 => "mini_tss", PlacementKind::MiniTspin2 => "mini_tsd", PlacementKind::Tspin => "tspin0",
        PlacementKind::Tspin1 => "tss", PlacementKind::Tspin2 => "tsd", PlacementKind::Tspin3 => "tst",
    }
}
fn to_field(rows: &[J]) -> [[bool; 10]; 40] {
    let mut f = [[false; 10]; 40];
    for (r, row) in rows.iter().enumerate() {
        for (c, ch) in row.as_str().unwrap().chars().take(10).enumerate() {
            f[39 - r][c] = ch != '.';
        }
    }
    f
}
fn cells_td(p: &FallingPiece) -> Vec<[i32; 2]> {
    let mut v: Vec<[i32; 2]> = p.cells().iter().map(|&(x, y)| [x, 39 - y]).collect();
    v.sort();
    v
}
fn field_td(b: &Board) -> Vec<String> {
    let f = b.get_field();
    (0..40).map(|r| (0..10).map(|c| if f[39 - r][c] { '#' } else { '.' }).collect()).collect()
}

/// Build the root board exactly as the bot expects it: field, the bag BEFORE the current piece was
/// drawn, hold, b2b, combo (cold-clear's combo = TETR.IO's + 1: 0 means "no ongoing combo"), then
/// the current piece and the visible next queue pushed through `add_next_piece`, which keeps the bag.
fn root_board(pos: &J) -> Board {
    let mut bag = enumset::EnumSet::<Piece>::empty();
    for p in pos["bagRemain"].as_array().unwrap() { bag.insert(piece_of(p.as_str().unwrap())); }
    let hold = pos["hold"].as_str().map(piece_of);
    let b2b = pos["b2b"].as_i64().unwrap() >= 0;
    let combo = (pos["combo"].as_i64().unwrap() + 1).max(0) as u32;
    let mut b = Board::new_with_state(to_field(pos["field"].as_array().unwrap()), bag, hold, b2b, combo);
    b.add_next_piece(piece_of(pos["current"].as_str().unwrap()));
    for p in pos["next"].as_array().unwrap() { b.add_next_piece(piece_of(p.as_str().unwrap())); }
    b
}

fn options(nodes: u32) -> Options {
    Options {
        mode: MovementMode::ZeroGComplete,
        spawn_rule: SpawnRule::Row19Or20,
        use_hold: true,
        speculate: true,
        pcloop: None,
        min_nodes: 0,
        max_nodes: nodes,
        threads: 1,
    }
}

/// Seed for one search: FNV-1a over (position id, purpose tag), xor the run's COACH_SEED. Same
/// inputs + same COACH_SEED => the same search, in any process, on any thread. A different
/// COACH_SEED is an independent sample, which is how cold-clear's own sampling noise is measured.
fn seed_for(id: &str, tag: &str) -> u64 {
    let base: u64 = std::env::var("COACH_SEED").ok().and_then(|s| s.parse().ok()).unwrap_or(0);
    let mut h: u64 = 0xcbf29ce484222325;
    for b in id.bytes().chain([0u8]).chain(tag.bytes()) { h ^= b as u64; h = h.wrapping_mul(0x100000001b3); }
    h ^ base.wrapping_mul(0x9E3779B97F4A7C15)
}

fn search(bot: &mut BotState<Standard>, eval: &Standard, nodes: u32) {
    while bot.node_count() < nodes {
        match bot.think() {
            Ok(t) => { let r = t.think(eval); bot.finish_thinking(r); }
            Err(_) => break,
        }
    }
}

/// Score groups: contribution of each weight group to the ONE-PLY static evaluation, computed as
/// full - (same weights with that group zeroed). `evaluate` is linear in every weight except
/// `max_well_depth`, which is a cap and is never zeroed, so the groups sum to the full score.
fn groups(e: &Standard, lock: &LockResult, board: &Board, move_time: u32, placed: Piece) -> Vec<(&'static str, i32)> {
    let tot = |w: &Standard| { let (v, r) = w.evaluate(lock, board, move_time, placed); v.value + r.value };
    let full = tot(e);
    let mut out = vec![("total", full)];
    let zeroers: Vec<(&'static str, Box<dyn Fn(&mut Standard)>)> = vec![
        ("holes", Box::new(|w: &mut Standard| { w.cavity_cells = 0; w.cavity_cells_sq = 0; w.overhang_cells = 0; w.overhang_cells_sq = 0; w.covered_cells = 0; w.covered_cells_sq = 0; })),
        ("surface", Box::new(|w: &mut Standard| { w.bumpiness = 0; w.bumpiness_sq = 0; w.row_transitions = 0; })),
        ("height", Box::new(|w: &mut Standard| { w.height = 0; w.top_half = 0; w.top_quarter = 0; w.jeopardy = 0; })),
        ("tslot", Box::new(|w: &mut Standard| { w.tslot = [0; 4]; })),
        ("well", Box::new(|w: &mut Standard| { w.well_depth = 0; w.well_column = [0; 10]; })),
        ("b2b_state", Box::new(|w: &mut Standard| { w.back_to_back = 0; })),
        ("clear_reward", Box::new(|w: &mut Standard| { w.b2b_clear = 0; w.clear1 = 0; w.clear2 = 0; w.clear3 = 0; w.clear4 = 0; w.tspin1 = 0; w.tspin2 = 0; w.tspin3 = 0; w.mini_tspin1 = 0; w.mini_tspin2 = 0; w.perfect_clear = 0; w.combo_garbage = 0; })),
        ("wasted_t", Box::new(|w: &mut Standard| { w.wasted_t = 0; })),
        ("move_time", Box::new(|w: &mut Standard| { w.move_time = 0; })),
    ];
    let mut sum = 0;
    for (name, z) in zeroers {
        let mut w = e.clone();
        z(&mut w);
        let c = full - tot(&w);
        sum += c;
        out.push((name, c));
    }
    out.push(("residual", full - sum));
    out
}

fn groups_json(g: &[(&str, i32)]) -> J {
    let mut m = serde_json::Map::new();
    for (k, v) in g { m.insert(k.to_string(), json!(v)); }
    J::Object(m)
}

/// Board-shape facts a human can act on, independent of cold-clear's weights.
fn shape(b: &Board) -> J {
    let h = b.column_heights();
    let max_h = *h.iter().max().unwrap();
    let mut holes = 0; // empty cells with a filled cell somewhere above in the same column
    for x in 0..10 { for y in 0..h[x as usize] { if !b.occupied(x, y) { holes += 1; } } }
    let bump: i32 = (0..9).map(|x| (h[x] - h[x + 1]).abs()).sum();
    json!({"max_h": max_h, "holes": holes, "bump": bump, "heights": h.to_vec()})
}

fn cand_json(c: &MoveCandidate<cold_clear::evaluation::standard::Value>) -> J {
    json!({"piece": pname(c.mv.kind.0), "hold": c.hold, "cells": cells_td(&c.mv), "kind": kind_name(c.lock.placement_kind),
           "b2b": c.lock.b2b, "pc": c.lock.perfect_clear, "cc_garbage": c.lock.garbage_sent,
           "value": c.evaluation.value, "spike": c.evaluation.spike, "x": c.mv.x, "y": c.mv.y,
           "rot": format!("{:?}", c.mv.kind.1), "tspin": format!("{:?}", c.mv.tspin)})
}

/// Brute-force the FallingPiece whose cells equal `want` (y-up), for a placement cold-clear's
/// movegen did not offer. Its t-spin status is taken from the replay's own verdict.
fn construct(piece: Piece, want: &Vec<[i32; 2]>, spin: &str) -> Option<FallingPiece> {
    for rot in [RotationState::North, RotationState::East, RotationState::South, RotationState::West].iter() {
        for x in -3..13 { for y in -3..43 {
            let fp = FallingPiece { kind: PieceState(piece, *rot), x, y,
                tspin: match spin { "normal" | "full" => TspinStatus::Full, "mini" => TspinStatus::Mini, _ => TspinStatus::None } };
            if &cells_td(&fp) == want { return Some(fp); }
        }}
    }
    None
}

fn move_time_of(board: &Board, fp: &FallingPiece, mode: MovementMode) -> Option<u32> {
    let spawned = SpawnRule::Row19Or20.spawn(fp.kind.0, board)?;
    find_moves(board, spawned, mode).into_iter().find(|p| p.location.same_location(fp)).map(|p| p.inputs.time)
}

/// Equal-effort value of ONE placement: its own reward plus the best a fresh search finds from the
/// board it leaves, with the same node budget for every placement scored this way. This removes
/// the exploration bias of reading values off the main tree, where cold-clear's favourite has been
/// searched far deeper than the human's move and a backed-up MAX is biased upward with effort.
fn duel_value(eval: &Standard, root: &Board, fp: FallingPiece, nodes: u32, seed: u64) -> Option<i32> {
    if !fp.cells().iter().all(|&(x, y)| x >= 0 && x < 10 && y >= 0 && y < 40 && !root.occupied(x, y)) { return None; }
    let mut b = root.clone();
    let l = advance(&mut b, fp);
    let held = fp.kind.0 != root.get_next_piece().ok()?;
    let mt = move_time_of(root, &fp, MovementMode::ZeroGComplete).unwrap_or(0) + if held { 1 } else { 0 };
    let (v, reward) = eval.evaluate(&l, &b, mt, fp.kind.0);
    coach_reseed(seed);
    let mut sub = BotState::<Standard>::new(b, options(nodes));
    search(&mut sub, eval, nodes);
    let mut sc = sub.candidates();
    sc.sort_by(|a, b| b.evaluation.cmp(&a.evaluation));
    Some(reward.value + match sc.first() { Some(s0) => s0.evaluation.value, None => v.value - 1000 })
}

fn grade(pos: &J, nodes: u32) -> J {
    let eval = Standard::default();
    let root = root_board(pos);
    let mut bot = BotState::<Standard>::new(root.clone(), options(nodes));
    let played = &pos["played"];
    let ppiece = piece_of(played["piece"].as_str().unwrap());
    let mut pcells: Vec<[i32; 2]> = played["cells"].as_array().unwrap().iter()
        .map(|c| [c[0].as_i64().unwrap() as i32, c[1].as_i64().unwrap() as i32]).collect();
    pcells.sort();
    let incoming = pos["incoming"].as_u64().unwrap_or(0) as u32;

    // expand the root once, find the player's exact child, force it to be analysed, then search
    coach_reseed(seed_for(pos["id"].as_str().unwrap_or(""), "main"));
    search(&mut bot, &eval, 2);
    let first = bot.candidates();
    let pchild = first.iter().find(|c| c.mv.kind.0 == ppiece && cells_td(&c.mv) == pcells).map(|c| c.mv);
    if let Some(fp) = pchild { bot.force_analysis_line(vec![fp]); }
    search(&mut bot, &eval, nodes);

    let mut cands = bot.candidates();
    if cands.is_empty() {
        return json!({"id": pos["id"], "error": "no candidates (dead)"});
    }
    cands.sort_by(|a, b| b.evaluation.cmp(&a.evaluation));
    let pick = eval.pick_move(cands.clone(), incoming);
    let best = &cands[0];
    let prank = cands.iter().position(|c| c.mv.kind.0 == ppiece && cells_td(&c.mv) == pcells);

    // static one-ply decomposition for the player's board and cold-clear's pick
    let mut root_q = root.clone();
    let ccb = { let mut b = root_q.clone(); let l = advance(&mut b, pick.mv); (b, l) };
    let cc_mt = move_time_of(&root_q, &pick.mv, MovementMode::ZeroGComplete).unwrap_or(0) + if pick.hold { 1 } else { 0 };
    let cc_groups = groups(&eval, &ccb.1, &ccb.0, cc_mt, pick.mv.kind.0);

    // the player's placement as a FallingPiece (cold-clear's own if it generated it)
    let pfp = match prank { Some(i) => Some(cands[i].mv), None => construct(ppiece, &pcells, played["spin"].as_str().unwrap_or("none")) };
    let mut player = json!({"found": prank.is_some(), "rank": prank.map(|r| r + 1), "n": cands.len()});
    if let Some(i) = prank {
        player = json!({"found": true, "rank": i + 1, "n": cands.len(), "value": cands[i].evaluation.value,
            "spike": cands[i].evaluation.spike, "kind": kind_name(cands[i].lock.placement_kind), "cc_garbage": cands[i].lock.garbage_sent});
    }
    let mut player_groups = J::Null;
    let mut player_shape = J::Null;
    let mut est_value = J::Null;
    if let Some(fp) = pfp {
        // a placement must not overlap the field; an overlapping one means the reconstruction drifted
        let legal = fp.cells().iter().all(|&(x, y)| x >= 0 && x < 10 && y >= 0 && y < 40 && !root_q.occupied(x, y));
        if legal {
            let mut b = root_q.clone();
            let l = advance(&mut b, fp);
            let mt = move_time_of(&root_q, &fp, MovementMode::ZeroGComplete).unwrap_or(0) + if fp.kind.0 != root_q.get_next_piece().unwrap() { 1 } else { 0 };
            player_groups = groups_json(&groups(&eval, &l, &b, mt, ppiece));
            player_shape = shape(&b);
            if prank.is_none() {
                // value estimate for a placement outside cold-clear's movegen: search from the
                // resulting board with the same budget, then add the placement's own reward
                let (_, reward) = eval.evaluate(&l, &b, mt, ppiece);
                coach_reseed(seed_for(pos["id"].as_str().unwrap_or(""), "est"));
                let mut sub = BotState::<Standard>::new(b.clone(), options(nodes));
                search(&mut sub, &eval, nodes);
                let mut sc = sub.candidates();
                sc.sort_by(|a, b| b.evaluation.cmp(&a.evaluation));
                if let Some(s0) = sc.first() { est_value = json!(s0.evaluation.value + reward.value); }
                player["kind"] = json!(kind_name(l.placement_kind));
            }
        } else {
            player["illegal"] = json!(true);
        }
    } else {
        player["unconstructible"] = json!(true);
    }
    player["est_value"] = est_value;
    let duel_nodes: u32 = std::env::var("COACH_DUEL").ok().and_then(|s| s.parse().ok()).unwrap_or(0);
    let mut duel = J::Null;
    if duel_nodes > 0 {
        let id = pos["id"].as_str().unwrap_or("");
        let dp = pfp.and_then(|fp| duel_value(&eval, &root_q, fp, duel_nodes, seed_for(id, "duel-human")));
        let dc = duel_value(&eval, &root_q, pick.mv, duel_nodes, seed_for(id, "duel-cc"));
        duel = json!({"player": dp, "cc": dc, "same": pfp.map(|fp| fp.kind.0 == pick.mv.kind.0 && cells_td(&fp) == cells_td(&pick.mv))});
    }

    let plan: Vec<J> = bot.plan().iter().take(8).map(|(fp, l)| json!({"piece": pname(fp.kind.0), "cells": cells_td(fp), "kind": kind_name(l.placement_kind)})).collect();
    json!({
        "id": pos["id"], "nodes": bot.node_count(), "incoming": incoming,
        "pick": cand_json(&pick), "best": cand_json(best),
        "top": cands.iter().take(5).map(cand_json).collect::<Vec<_>>(),
        "player": player, "duel": duel, "player_groups": player_groups, "player_shape": player_shape,
        "cc_groups": groups_json(&cc_groups), "cc_shape": shape(&ccb.0), "plan": plan,
        "all": if std::env::var_os("COACH_ALL").is_some() {
            J::Array(cands.iter().map(|c| json!([pname(c.mv.kind.0), cells_td(&c.mv), c.evaluation.value, c.evaluation.spike])).collect())
        } else { J::Null },
    })
}

/// Roll cold-clear forward k pieces from the position, revealing the TRUE future sequence five
/// pieces ahead at a time, exactly as the player saw it. No garbage arrives (the caller picks
/// windows in which none did for the player either).
fn rollout(pos: &J, nodes: u32) -> J {
    let eval = Standard::default();
    let future: Vec<Piece> = pos["future"].as_array().unwrap().iter().map(|p| piece_of(p.as_str().unwrap())).collect();
    let k = pos["k"].as_u64().unwrap() as usize;
    let mut board = root_board(pos);
    let mut fed = 0usize; // future pieces already revealed beyond the initial visible queue
    let mut steps = vec![];
    // PRESSURE-MATCHED garbage: the rows the human actually received at step j (amount, hole
    // column) enter a pending list after cold-clear's step-j lock and are inserted on its next
    // NON-clearing lock (TETR.IO tanks only on a lock that clears nothing). Cold-clear gets no
    // cancellation credit for its own attack, so it faces at least the human's received garbage.
    let sched: Vec<Vec<(usize, usize)>> = pos["garbage_schedule"].as_array().map(|a| a.iter().map(|t| t.as_array().unwrap().iter()
        .map(|g| (g["amount"].as_u64().unwrap() as usize, g["column"].as_u64().unwrap() as usize)).collect()).collect()).unwrap_or_default();
    let incoming: Vec<u32> = pos["incoming_schedule"].as_array().map(|a| a.iter().map(|v| v.as_u64().unwrap() as u32).collect()).unwrap_or_default();
    // TETR.IO's per-lock garbage cap (`garbage_cap`, the game's garbagecap, 8 by default): at most that
    // many queued rows enter on one lock; the rest stay queued, front first, for the next non-clearing
    // lock. Absent = no cap (the behaviour of the earlier 14-piece rollout pages, kept reproducible).
    let cap: usize = pos["garbage_cap"].as_u64().map(|v| v as usize).unwrap_or(usize::MAX);
    let mut pending: Vec<(usize, usize)> = vec![];
    for j in 0..k {
        coach_reseed(seed_for(pos["id"].as_str().unwrap_or(""), &format!("rollout-{}", j)));
        let mut bot = BotState::<Standard>::new(board.clone(), options(nodes));
        search(&mut bot, &eval, nodes);
        let mut c = bot.candidates();
        if c.is_empty() { steps.push(json!({"dead": true})); break; }
        c.sort_by(|a, b| b.evaluation.cmp(&a.evaluation));
        let pick = eval.pick_move(c, *incoming.get(j).unwrap_or(&0));
        let l = advance(&mut board, pick.mv);
        if let Some(t) = sched.get(j) { pending.extend(t.iter().cloned()); }
        let mut inserted = 0usize;
        if l.cleared_lines.is_empty() && !pending.is_empty() {
            let mut f = board.get_field(); // y-up: f[0] is the bottom row
            let mut rest: Vec<(usize, usize)> = vec![];
            for (amount, col) in pending.drain(..) {
                let take = amount.min(cap - inserted);
                for _ in 0..take {
                    for y in (1..40).rev() { f[y] = f[y - 1]; }
                    let mut row = [true; 10]; if col < 10 { row[col] = false; } f[0] = row;
                    inserted += 1;
                }
                if take < amount { rest.push((amount - take, col)); }
            }
            pending = rest;
            board.set_field(f);
        }
        let topped = board.column_heights().iter().any(|&h| h > 22);
        steps.push(json!({"piece": pname(pick.mv.kind.0), "hold": pick.hold, "cells": cells_td(&pick.mv),
            "kind": kind_name(l.placement_kind), "lines": l.cleared_lines.len(), "b2b": l.b2b, "pc": l.perfect_clear,
            "combo": l.combo, "cc_garbage": l.garbage_sent, "tspin": format!("{:?}", pick.mv.tspin), "garbage_in": inserted, "garbage_waiting": pending.iter().map(|t| t.0).sum::<usize>()}));
        if topped { steps.push(json!({"dead": true, "why": "garbage pushed the stack out"})); break; }
        // reveal one more piece, keeping the visible queue at its original length
        if fed < future.len() { board.add_next_piece(future[fed]); fed += 1; }
    }
    json!({"id": pos["id"], "steps": steps, "final_field": field_td(&board), "final_shape": shape(&board),
           "b2b_end": board.b2b_bonus, "combo_end": board.combo})
}

fn main() {
    let nodes: u32 = std::env::var("CC_NODES").ok().and_then(|s| s.parse().ok()).unwrap_or(10_000);
    let mode = std::env::var("COACH_MODE").unwrap_or_else(|_| "grade".into());
    let lines: Vec<String> = io::stdin().lock().lines().map(|l| l.unwrap()).filter(|l| !l.trim().is_empty()).collect();
    let outs: Vec<String> = lines.par_iter().map(|l| {
        let pos: J = serde_json::from_str(l).unwrap();
        let r = if mode == "rollout" { rollout(&pos, nodes) } else { grade(&pos, nodes) };
        r.to_string()
    }).collect();
    let out = io::stdout();
    let mut out = out.lock();
    for o in outs { writeln!(out, "{}", o).unwrap(); }
}

//! Differential oracle: read 40 rows of 10 chars ('.' empty, else filled) per board on stdin,
//! print the ORIGINAL cold-clear detectors' verdict as JSON. One line in, one line out.
//!
//! INPUT IS TOP-DOWN, row 0 = the top of the field, matching this repo's boards. cold-clear is
//! y-UP: `Board::set_field` walks y ascending and records `column_heights[x] = y + 1`, so its
//! field[0] is the BOTTOM row. The flip happens here, once, and it is the single easiest thing
//! in this bridge to get wrong — feeding it top-down silently reports NO detections on every
//! board, which reads as agreement rather than as a bug.
//!
//! MOVEGEN mode (CC_ORACLE_MOVES=1) is the second question this bridge can answer with the
//! ORIGINAL Rust: not "is there a slot" but "what placements can the mover REACH". It is the
//! external authority for our forecast BFS (`forecast.ts` `bestTspin`), whose reachable-set was
//! only ever checked against a second copy of itself until now. Protocol per record: ONE line
//! holding a single piece letter (I T O S Z L J), then the 40 board rows. Output per record:
//! `{"placements":[[[c,r],[c,r],[c,r],[c,r]], ...]}` — every resting placement `find_moves`
//! returns, each as its four occupied cells in THIS repo's top-down coords (`r = 39 - cc_y`),
//! cells sorted (row, then col) within a placement and placements sorted lexicographically, so
//! the line is canonical and byte-stable. `MovementMode::ZeroGComplete` is used deliberately:
//! `ZeroG`'s fast_mode prunes stack movement and would UNDER-report versus our complete
//! soft-drop BFS, manufacturing false "we reach more" findings. The default (detector) output is
//! untouched, so the committed CI smoke test and `cross-tslot-count.ts` keep passing verbatim.
use cold_clear::evaluation::standard::*;
use libtetris::{find_moves, Board, FallingPiece, MovementMode, Piece, SpawnRule};
use std::io::{self, BufRead, Write};

/// Map a board input letter to cold-clear's `Piece`. Returns `None` for anything else so a
/// malformed piece line fails loudly rather than defaulting to some piece and reporting a
/// plausible-but-wrong placement set.
fn piece_of(ch: char) -> Option<Piece> {
    match ch {
        'I' => Some(Piece::I),
        'O' => Some(Piece::O),
        'T' => Some(Piece::T),
        'L' => Some(Piece::L),
        'J' => Some(Piece::J),
        'S' => Some(Piece::S),
        'Z' => Some(Piece::Z),
        _ => None,
    }
}

/// The four occupied cells of a resting `FallingPiece`, in this repo's top-down coords, sorted
/// (row, col). `cells()` are absolute and y-up; `r = 39 - cc_y` is the one flip, matching
/// `set_field` above.
fn placement_cells(p: &FallingPiece) -> [[i32; 2]; 4] {
    let mut cells: [[i32; 2]; 4] = [[0, 0]; 4];
    for (i, &(x, y)) in p.cells().iter().enumerate() {
        cells[i] = [x, 39 - y];
    }
    cells.sort_by(|a, b| a[1].cmp(&b[1]).then(a[0].cmp(&b[0])));
    cells
}

/// MOVEGEN mode: `find_moves` (ZeroGComplete) for `piece` on `b`, emitted as a canonical line.
fn emit_moves_line(out: &mut impl Write, b: &Board, piece: Piece) {
    // A blocked spawn (roof already full) yields no placements — an honest empty list, not an
    // error, so the differential can treat it as "our BFS must also reach nothing here".
    let placements = match SpawnRule::Row19Or20.spawn(piece, b) {
        Some(spawned) => {
            let mut ps: Vec<[[i32; 2]; 4]> = find_moves(b, spawned, MovementMode::ZeroGComplete)
                .iter()
                .map(|pl| placement_cells(&pl.location))
                .collect();
            ps.sort();
            ps.dedup();
            ps
        }
        None => Vec::new(),
    };
    let body: Vec<String> = placements
        .iter()
        .map(|cells| {
            let parts: Vec<String> = cells.iter().map(|c| format!("[{},{}]", c[0], c[1])).collect();
            format!("[{}]", parts.join(","))
        })
        .collect();
    writeln!(out, "{{\"placements\":[{}]}}", body.join(",")).unwrap();
    out.flush().unwrap();
}

fn main() {
    // MULTI-SLOT is opt-in via CC_ORACLE_SLOTS so the default output stays byte-identical: the
    // committed CI smoke test asserts the empty board's line EXACTLY equals
    // `{"any":false,"hits":[],"lines":0}`, and `cross-tslot-count.ts` reads only `.lines`. With the
    // env set the line gains a trailing `"slots":[...]` field and nothing else moves.
    let emit_slots = std::env::var_os("CC_ORACLE_SLOTS").is_some();

    // MOVEGEN mode is a wholly separate read path (it consumes a leading piece letter), so it
    // branches here and never touches the detector loop below.
    if std::env::var_os("CC_ORACLE_MOVES").is_some() {
        let stdin = io::stdin();
        let out = io::stdout();
        let mut out = out.lock();
        let mut piece: Option<Piece> = None;
        let mut field = [[false; 10]; 40];
        let mut row = 0usize;
        for line in stdin.lock().lines() {
            let line = line.unwrap();
            if line.trim().is_empty() {
                continue;
            }
            if piece.is_none() {
                let ch = line.trim().chars().next().unwrap();
                piece = Some(piece_of(ch).unwrap_or_else(|| panic!("bad piece letter: {:?}", ch)));
                continue;
            }
            for (c, ch) in line.chars().take(10).enumerate() {
                field[39 - row][c] = ch != '.';
            }
            row += 1;
            if row == 40 {
                let mut b = Board::new();
                b.set_field(field);
                emit_moves_line(&mut out, &b, piece.unwrap());
                piece = None;
                field = [[false; 10]; 40];
                row = 0;
            }
        }
        return;
    }

    let stdin = io::stdin();
    let mut field = [[false; 10]; 40];
    let mut row = 0usize;
    let out = io::stdout();
    let mut out = out.lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        if line.trim().is_empty() { continue }
        for (c, ch) in line.chars().take(10).enumerate() { field[39 - row][c] = ch != '.'; }
        row += 1;
        if row == 40 {
            let mut b = Board::new();
            b.set_field(field);
            // Each detector returns the FallingPiece for a slot; cutout_tslot turns that piece into
            // the LINE COUNT the slot clears. `lines` is the max over detected slots — the quantity
            // `bestTspinLines` computes on our side, and the one the metric actually consumes. Until
            // now this bridge reported presence only; the count had no external check at all.
            let dets: [(&str, Option<_>); 6] = [
                ("sky_tslot_right", sky_tslot_right(&b)),
                ("sky_tslot_left",  sky_tslot_left(&b)),
                ("tst_twist_right", tst_twist_right(&b)),
                ("tst_twist_left",  tst_twist_left(&b)),
                ("fin_right",       fin_right(&b)),
                ("fin_left",        fin_left(&b)),
            ];
            let mut hits: Vec<&str> = Vec::new();
            let mut lines = 0usize;
            for (name, opt) in dets {
                if let Some(piece) = opt {
                    hits.push(name);
                    let c = cutout_tslot(b.clone(), piece);
                    if c.lines > lines { lines = c.lines; }
                }
            }
            if emit_slots {
                // cold-clear counts SEVERAL slots the way its own evaluator does (standard.rs
                // `Evaluator::evaluate`): pick the highest-priority detected slot, cut it out, and
                // re-detect on the resulting board — sky first, then a tst that survives cave/corner
                // refinement, then fin. `cutout_tslot` returns a continuation board ONLY after a
                // 2- or 3-line cut (`result: Some`); a single or 0-line cut ends the chain
                // (`result: None`). So `slots` is that CHAIN of line counts, not every coexisting
                // slot: two independent singles read as one, because clearing is the only removal
                // the mechanism has and a single leaves no board to re-detect on. The `for _ in 0..ts`
                // T-availability bound from the evaluator is dropped — this measures board structure,
                // not how many T pieces are in the bag — and a belt cap guards against a non-shrinking
                // loop (each continuation clears >=2 rows, so it terminates well before the cap).
                let mut slots: Vec<usize> = Vec::new();
                let mut cur = b.clone();
                for _ in 0..40 {
                    let loc = sky_tslot_left(&cur)
                        .or_else(|| sky_tslot_right(&cur))
                        .or_else(|| {
                            let tst = tst_twist_left(&cur).or_else(|| tst_twist_right(&cur))?;
                            cave_tslot(&cur, tst).or_else(|| {
                                let corners = cur.occupied(tst.x - 1, tst.y - 1) as usize
                                    + cur.occupied(tst.x + 1, tst.y - 1) as usize
                                    + cur.occupied(tst.x - 1, tst.y + 1) as usize
                                    + cur.occupied(tst.x + 1, tst.y + 1) as usize;
                                if corners >= 3 && cur.on_stack(&tst) { Some(tst) } else { None }
                            })
                        })
                        .or_else(|| fin_left(&cur))
                        .or_else(|| fin_right(&cur));
                    let loc = match loc { Some(l) => l, None => break };
                    let c = cutout_tslot(cur.clone(), loc);
                    slots.push(c.lines);
                    match c.result { Some(nb) => cur = nb, None => break }
                }
                writeln!(out, "{{\"any\":{},\"hits\":{:?},\"lines\":{},\"slots\":{:?}}}",
                    !hits.is_empty(), hits, lines, slots).unwrap();
            } else {
                writeln!(out, "{{\"any\":{},\"hits\":{:?},\"lines\":{}}}", !hits.is_empty(), hits, lines).unwrap();
            }
            out.flush().unwrap();
            field = [[false; 10]; 40]; row = 0;
        }
    }
}

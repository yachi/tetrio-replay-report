//! Differential oracle: read 40 rows of 10 chars ('.' empty, else filled) per board on stdin,
//! print the ORIGINAL cold-clear detectors' verdict as JSON. One line in, one line out.
//!
//! INPUT IS TOP-DOWN, row 0 = the top of the field, matching this repo's boards. cold-clear is
//! y-UP: `Board::set_field` walks y ascending and records `column_heights[x] = y + 1`, so its
//! field[0] is the BOTTOM row. The flip happens here, once, and it is the single easiest thing
//! in this bridge to get wrong — feeding it top-down silently reports NO detections on every
//! board, which reads as agreement rather than as a bug.
use cold_clear::evaluation::standard::*;
use libtetris::Board;
use std::io::{self, BufRead, Write};

fn main() {
    // MULTI-SLOT is opt-in via CC_ORACLE_SLOTS so the default output stays byte-identical: the
    // committed CI smoke test asserts the empty board's line EXACTLY equals
    // `{"any":false,"hits":[],"lines":0}`, and `cross-tslot-count.ts` reads only `.lines`. With the
    // env set the line gains a trailing `"slots":[...]` field and nothing else moves.
    let emit_slots = std::env::var_os("CC_ORACLE_SLOTS").is_some();
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

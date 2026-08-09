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
            writeln!(out, "{{\"any\":{},\"hits\":{:?},\"lines\":{}}}", !hits.is_empty(), hits, lines).unwrap();
            out.flush().unwrap();
            field = [[false; 10]; 40]; row = 0;
        }
    }
}

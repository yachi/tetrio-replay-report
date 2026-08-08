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
            let hits: Vec<&str> = [
                ("sky_tslot_right", sky_tslot_right(&b).is_some()),
                ("sky_tslot_left",  sky_tslot_left(&b).is_some()),
                ("tst_twist_right", tst_twist_right(&b).is_some()),
                ("tst_twist_left",  tst_twist_left(&b).is_some()),
                ("fin_right",       fin_right(&b).is_some()),
                ("fin_left",        fin_left(&b).is_some()),
            ].iter().filter(|(_, h)| *h).map(|(n, _)| *n).collect();
            writeln!(out, "{{\"any\":{},\"hits\":{:?}}}", !hits.is_empty(), hits).unwrap();
            out.flush().unwrap();
            field = [[false; 10]; 40]; row = 0;
        }
    }
}

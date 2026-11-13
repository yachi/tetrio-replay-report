//! extern "C" surface for bun:ffi (pipeline/sim/pc-solver-native.ts). Pieces travel as ASCII
//! letters (b'I' …), 0 = none. Results go into a caller-owned i32 buffer.
use crate::solver::{check, placements, Gen, Memo, Verdict, NONE};

fn piece(c: u8) -> u8 { if c == 0 { NONE } else { c } }
fn gen(engine: i32) -> Gen { if engine != 0 { Gen::Engine } else { Gen::Srs } }

#[no_mangle]
pub extern "C" fn pc_memo_new() -> *mut Memo { Box::into_raw(Box::default()) }

#[no_mangle]
pub unsafe extern "C" fn pc_memo_free(m: *mut Memo) { if !m.is_null() { drop(Box::from_raw(m)); } }

#[no_mangle]
pub unsafe extern "C" fn pc_memo_len(m: *const Memo) -> f64 { if m.is_null() { 0.0 } else { (*m).m.len() as f64 } }

unsafe fn slice<'a, T>(p: *const T, n: u32) -> &'a [T] { if n == 0 || p.is_null() { &[] } else { std::slice::from_raw_parts(p, n as usize) } }

/// pc-miss.ts `check`. Returns 1 (ok: true), 0 (ok: false), 2 (ok: null), -1 (out buffer too small).
/// On 1, `out` = [H, n, then n × (piece, held, c0, c1, c2, c3)]. A null `memo` uses a fresh one.
#[no_mangle]
pub unsafe extern "C" fn pc_check(rows: *const u16, nrows: u32, cur: u8, hold: u8, seq: *const u8, seqlen: u32,
                                  ptr: i32, memo: *mut Memo, max_h: i32, nodes: i32, engine: i32,
                                  out: *mut i32, outcap: u32) -> i32 {
    let rows = slice(rows, nrows);
    let seq = slice(seq, seqlen);
    let mut tmp = Memo::default();
    let memo = if memo.is_null() { &mut tmp } else { &mut *memo };
    match check(rows, piece(cur), piece(hold), seq, ptr as i64, memo, max_h, nodes as i64, gen(engine)) {
        Verdict::False => 0,
        Verdict::Short => 2,
        Verdict::Ok { h, plan } => {
            let need = 2 + 6 * plan.len();
            if need > outcap as usize { return -1; }
            let o = std::slice::from_raw_parts_mut(out, need);
            o[0] = h;
            o[1] = plan.len() as i32;
            for (i, p) in plan.iter().enumerate() {
                let b = &mut o[2 + 6 * i..8 + 6 * i];
                b[0] = p.piece as i32;
                b[1] = p.held as i32;
                for j in 0..4 { b[2 + j] = p.cells[j] as i32; }
            }
            1
        }
    }
}

/// pc-solver.ts `placements` (SRS, or the engine movegen). Returns the count of cell sets, written
/// as 4 i32 each, or -1 if `out` is too small.
#[no_mangle]
pub unsafe extern "C" fn pc_placements(rows: *const u16, nrows: u32, p: u8, h: i32, engine: i32, out: *mut i32, outcap: u32) -> i32 {
    let rows = slice(rows, nrows);
    let v = placements(gen(engine), rows, p, h);
    if v.len() * 4 > outcap as usize { return -1; }
    let o = std::slice::from_raw_parts_mut(out, v.len() * 4);
    for (i, c) in v.iter().enumerate() { for j in 0..4 { o[4 * i + j] = c[j] as i32; } }
    v.len() as i32
}

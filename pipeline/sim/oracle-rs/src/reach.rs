//! `reach()`'s BFS (pipeline/sim/route-demos.ts `searchAll`) in Rust: every resting placement of one
//! piece on one board that the vendored Triangle engine can reach by its own moves (a lateral step, the
//! engine's one-row fall, CW/CCW/180 through its SRS+ kicks), with the shortest path to each distinct
//! arrival spin, in the order the TS search finds them. `reach-native.ts` loads it through bun:ffi and
//! `reach-native.test.ts` holds its answer equal to the TS search's, paths, order and dedup included.
//!
//! Only what the TS search does on the demo engine is ported: SRS+ kicks, the "T-spins" spin rule, a
//! 10-wide board of 40 rows, a rotation that starts with totalRotations 0 (so performKick's maxMovement
//! is false). The start state (where `initiatePiece` spawns the piece) is the TS engine's, passed in.

use crate::data::{KICKS, STATES, T_CORNERS};

const W: usize = 10;
const H: usize = 40;

type Board = [[bool; W]; H];

#[inline]
fn legal(b: &Board, blocks: &[(f64, f64); 4]) -> bool {
    for &(x, y) in blocks.iter() {
        if x < 0.0 || x >= W as f64 || y < 0.0 || y >= H as f64 { return false; }
        if b[y as usize][x as usize] { return false; }
    }
    true
}

#[inline]
fn occupied(b: &Board, x: f64, y: f64) -> bool {
    x < 0.0 || y < 0.0 || x >= W as f64 || y >= H as f64 || b[y as usize][x as usize]
}

/// `absoluteAt({x, y, rotation})`: y is floored.
#[inline]
fn at(sym: usize, x: f64, y: f64, rot: usize) -> [(f64, f64); 4] {
    let s = &STATES[sym][rot];
    let yf = y.floor();
    let mut o = [(0.0, 0.0); 4];
    for i in 0..4 { o[i] = (s[i].0 as f64 + x, -(s[i].1 as f64) + yf); }
    o
}

/// JS `Math.round` (round half up).
#[inline]
fn js_round(x: f64) -> f64 {
    let f = x.floor();
    if x - f >= 0.5 { f + 1.0 } else { f }
}

#[derive(Clone, Copy)]
struct St { x: f64, y: f64, r: usize, spin: u8 } // spin: 0 none (null), 1 mini, 2 normal

/// `fall1`: the engine's `#__internal_fall(1)`, operation for operation.
#[inline]
fn fall1(b: &Board, sym: usize, s: &St) -> Option<St> {
    let mut y1 = js_round(1e6 * (s.y - 1.0)) / 1e6;
    let mut y2 = s.y - 1.0;
    if y1 % 1.0 == 0.0 { y1 -= 1e-6; }
    if y2 % 1.0 == 0.0 { y2 += 2e-6; }
    if !legal(b, &at(sym, s.x, y1, s.r)) || !legal(b, &at(sym, s.x, y2, s.r)) { return None; }
    Some(St { x: s.x, y: y1, r: s.r, spin: 0 })
}

/// `#detectSpinFromCorners` under "T-spins" for the piece at (x, y, rot); "none" for any other piece.
fn detect_spin(b: &Board, sym: usize, x: f64, y: f64, rot: usize, fin_or_tst: bool) -> u8 {
    if sym != 5 { return 0; }
    let s = &STATES[sym][rot];
    let fy = y.floor();
    let mut below = [(0.0, 0.0); 4];
    for i in 0..4 { below[i] = (s[i].0 as f64 + x, -(s[i].1 as f64) + fy - 1.0); }
    if legal(b, &below) { return 0; }
    let (mut corners, mut front) = (0, 0);
    for i in 0..4 {
        let t = T_CORNERS[rot][i];
        if occupied(b, x + t.0 as f64 + 1.0, fy - t.1 as f64 - 1.0) {
            corners += 1;
            if rot as i32 == t.2 || rot as i32 == t.3 { front += 1; }
        }
    }
    if corners < 3 { return 0; }
    let mut spin = 2;
    if front != 2 { spin = 1; }
    if fin_or_tst { spin = 2; }
    spin
}

/// `eng.rotateCW/CCW/180()` from (x, y, r) with totalRotations 0: performKick (SRS+, maxMovement false),
/// then `#__internal_rotate`'s spin. None when no kick fits.
fn rotate(b: &Board, sym: usize, s: &St, amount: i32) -> Option<St> {
    let to = (((s.r as i32 + amount) % 4 + 4) % 4) as usize;
    let st = &STATES[sym][to];
    let base_x = s.x;
    let base_y = s.y.floor();
    let mut init = [(0.0, 0.0); 4];
    for i in 0..4 { init[i] = (base_x + st[i].0 as f64, base_y - st[i].1 as f64); }
    let (nx, ny, kick, id);
    if legal(b, &init) {
        nx = s.x; ny = s.y; kick = (0.0, 0.0); id = 0usize;
    } else {
        let kid = s.r * 4 + to;
        let set = KICKS[sym][kid]?;
        let mut found = None;
        for &(dx, dy) in set.iter() {
            let (dx, dy) = (dx as f64, dy as f64);
            let new_y = s.y.ceil() - 0.1 - dy;
            let fny = new_y.floor();
            let mx = base_x + dx;
            let mut tb = [(0.0, 0.0); 4];
            for j in 0..4 { tb[j] = (mx + st[j].0 as f64, fny - st[j].1 as f64); }
            if legal(b, &tb) { found = Some((s.x + dx, new_y, (dx, -dy))); break; }
        }
        let (a, c, k) = found?;
        nx = a; ny = c; kick = k; id = kid;
    }
    // #isTSpinKick: ids "23"/"03" with kick [1, -2], "21"/"01" with kick [-1, -2]; "00" never
    let tst = id != 0 && (((id == 2 * 4 + 3 || id == 3) && kick.0 == 1.0 && kick.1 == -2.0)
        || ((id == 2 * 4 + 1 || id == 1) && kick.0 == -1.0 && kick.1 == -2.0));
    let spin = detect_spin(b, sym, nx, ny, to, tst);
    Some(St { x: nx, y: ny, r: to, spin })
}

/// Edge codes, in the TS search's order: L R D CW CCW 180.
pub const EDGES: [u8; 6] = [0, 1, 2, 3, 4, 5];

/// Location x is always an integer in [-3, 9] for a legal piece and floor(y) in [0, 42]; the visited
/// table is dense over a margin around that.
const XS: i64 = 24; const X0: i64 = 8;
const YS: i64 = 64; const Y0: i64 = 8;
#[inline]
fn slot(s: &St) -> usize {
    let x = s.x as i64 + X0;
    let y = s.y.floor() as i64 + Y0;
    assert!(x >= 0 && x < XS && y >= 0 && y < YS && s.x.fract() == 0.0, "reach: state out of range");
    (((s.r as i64 * 3 + s.spin as i64) * YS + y) * XS + x) as usize
}

/// One found path: the placement's cells (y * 10 + x, sorted), its arrival spin, its edges.
pub struct Found { pub cells: [u16; 4], pub spin: u8, pub edges: Vec<u8> }

/// The whole search for one (board, piece, start, no180), every found path in discovery order.
pub fn search(b: &Board, sym: usize, start: (f64, f64, usize), no180: bool) -> Vec<Found> {
    let n_slots = (4 * 3 * YS * XS) as usize;
    let mut seen = vec![false; n_slots];
    let mut states: Vec<St> = Vec::with_capacity(1024);
    let mut parent: Vec<(u32, u8)> = Vec::with_capacity(1024);
    let s0 = St { x: start.0, y: start.1, r: start.2, spin: 0 };
    seen[slot(&s0)] = true;
    states.push(s0);
    parent.push((u32::MAX, 255));
    // per resting cells: the spins already recorded (bit per spin code)
    let mut spins_seen: std::collections::HashMap<[u16; 4], u8> = std::collections::HashMap::new();
    let mut out = Vec::new();
    let n_edges = if no180 { 5 } else { 6 };
    let mut qi = 0;
    while qi < states.len() {
        let s = states[qi];
        if fall1(b, sym, &s).is_none() {
            let a = at(sym, s.x, s.y, s.r);
            let mut cells = [0u16; 4];
            for i in 0..4 { cells[i] = (a[i].1 as i64 * W as i64 + a[i].0 as i64) as u16; }
            cells.sort_unstable();
            let e = spins_seen.entry(cells).or_insert(0);
            let bit = 1u8 << s.spin;
            if *e & bit == 0 {
                *e |= bit;
                let mut edges = Vec::new();
                let mut c = qi;
                while parent[c].0 != u32::MAX { edges.push(parent[c].1); c = parent[c].0 as usize; }
                edges.reverse();
                out.push(Found { cells, spin: s.spin, edges });
            }
        }
        for &e in EDGES[..n_edges].iter() {
            let n = match e {
                0 | 1 => {
                    let nx = s.x + if e == 0 { -1.0 } else { 1.0 };
                    if legal(b, &at(sym, nx, s.y, s.r)) { Some(St { x: nx, ..s }) } else { None }
                }
                2 => fall1(b, sym, &s),
                3 => rotate(b, sym, &s, 1),
                4 => rotate(b, sym, &s, -1),
                _ => rotate(b, sym, &s, 2),
            };
            let Some(n) = n else { continue };
            let k = slot(&n);
            if seen[k] { continue; }
            seen[k] = true;
            states.push(n);
            parent.push((qi as u32, e));
        }
        qi += 1;
    }
    out
}

/// The output handle: u16 words, per path [c0, c1, c2, c3, spin, n_edges, edges...].
pub struct ReachOut { data: Vec<u16> }

/// # Safety
/// `board` must point to 400 bytes (row-major, y up, nonzero = filled).
#[no_mangle]
pub unsafe extern "C" fn reach_run(board: *const u8, piece: u32, sx: f64, sy: f64, sr: u32, no180: u32) -> *mut ReachOut {
    if board.is_null() || piece > 6 || sr > 3 { return std::ptr::null_mut(); }
    let raw = std::slice::from_raw_parts(board, W * H);
    let mut b: Board = [[false; W]; H];
    for y in 0..H { for x in 0..W { b[y][x] = raw[y * W + x] != 0; } }
    let found = search(&b, piece as usize, (sx, sy, sr as usize), no180 != 0);
    let mut d = Vec::with_capacity(found.len() * 12);
    for f in found {
        d.extend_from_slice(&f.cells);
        d.push(f.spin as u16);
        d.push(f.edges.len() as u16);
        d.extend(f.edges.iter().map(|&e| e as u16));
    }
    Box::into_raw(Box::new(ReachOut { data: d }))
}

/// # Safety
/// `h` must be a handle from `reach_run` not yet freed.
#[no_mangle]
pub unsafe extern "C" fn reach_out_len(h: *const ReachOut) -> f64 {
    if h.is_null() { return -1.0; }
    (*h).data.len() as f64
}

/// Copies the output into `dst` (room for `len` u16); returns the number copied, -1 if it does not fit.
/// # Safety
/// `h` as for `reach_out_len`; `dst` must have room for `len` u16.
#[no_mangle]
pub unsafe extern "C" fn reach_out_copy(h: *const ReachOut, dst: *mut u16, len: u32) -> i32 {
    if h.is_null() || dst.is_null() { return -1; }
    let d = &(*h).data;
    if d.len() > len as usize { return -1; }
    std::ptr::copy_nonoverlapping(d.as_ptr(), dst, d.len());
    d.len() as i32
}

/// # Safety
/// `h` must be a handle from `reach_run`, freed at most once.
#[no_mangle]
pub unsafe extern "C" fn reach_free(h: *mut ReachOut) {
    if !h.is_null() { drop(Box::from_raw(h)); }
}

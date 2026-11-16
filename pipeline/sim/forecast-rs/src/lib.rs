//! The Rust port of `forecast.ts`'s `bestTspin` (the T-spin BFS over the vendored SRS primitives in
//! `vendor/core/srs.ts`), loaded through bun:ffi by `forecast-native.ts`. Same BFS order, same 40000
//! cap, same two dedup keys (position for expansion, position of a rotation arrival for evaluation),
//! same tie-breaking (the first spin with strictly more lines wins). `forecast-native.test.ts` holds
//! the answer equal to the TS reference.
//!
//! The kick bit the TS search carries is not ported: `detectTSpin` only uses it to choose 'full' over
//! 'mini', and `bestTspin` tests `!== 'none'`, so it never changes the answer. Only the T walks, and
//! the T uses the JLSZT table, which the SRS / SRS+ kickset switch does not touch.

use std::collections::HashSet;

pub const H: i32 = 40;
pub const W: i32 = 10;
const CAP: usize = 40000;

/// `PIECE_DEFINITIONS.T.cells` (vendor/core/pieces.ts), as (dc, dr) per rotation, in order.
const T_CELLS: [[(i32, i32); 4]; 4] = [
    [(1, 0), (0, 1), (1, 1), (2, 1)],
    [(1, 0), (1, 1), (2, 1), (1, 2)],
    [(0, 1), (1, 1), (2, 1), (1, 2)],
    [(1, 0), (0, 1), (1, 1), (1, 2)],
];

/// `JLSZT_KICKS` (vendor/core/srs.ts), indexed [from][dir], dir 0 = CW (+1), 1 = CCW (-1).
const KICKS: [[[(i32, i32); 5]; 2]; 4] = [
    // 0->1, 0->3
    [[(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)], [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)]],
    // 1->2, 1->0
    [[(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)], [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)]],
    // 2->3, 2->1
    [[(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)], [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)]],
    // 3->0, 3->2
    [[(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)], [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)]],
];

#[derive(Clone, Copy, PartialEq, Eq, Hash)]
struct P { rot: u8, col: i32, row: i32 }

/// One board: bit c of row r set when the cell is filled (anything but null in the TS board).
pub struct Board { rows: [u16; H as usize] }

const FULL: u16 = (1 << W) - 1;

impl Board {
    pub fn from_cells(cells: &[u8]) -> Board {
        let mut rows = [0u16; H as usize];
        for r in 0..H as usize {
            for c in 0..W as usize { if cells[r * W as usize + c] != 0 { rows[r] |= 1 << c; } }
        }
        Board { rows }
    }
    #[inline] fn filled(&self, r: i32, c: i32) -> bool { self.rows[r as usize] >> c & 1 == 1 }
    /// `isValidPosition`: off the sides or below the floor is invalid, above the top is free.
    #[inline] fn valid(&self, p: P) -> bool {
        for &(dc, dr) in &T_CELLS[p.rot as usize] {
            let (c, r) = (p.col + dc, p.row + dr);
            if c < 0 || c >= W { return false; }
            if r >= H { return false; }
            if r < 0 { continue; }
            if self.filled(r, c) { return false; }
        }
        true
    }
    #[inline] fn try_move(&self, p: P, dx: i32, dy: i32) -> Option<P> {
        let n = P { rot: p.rot, col: p.col + dx, row: p.row + dy };
        if self.valid(n) { Some(n) } else { None }
    }
    /// `tryRotate`: the first legal kick candidate wins.
    #[inline] fn try_rotate(&self, p: P, dir: usize) -> Option<P> {
        let nr = if dir == 0 { (p.rot + 1) % 4 } else { (p.rot + 3) % 4 };
        for &(dx, dy) in &KICKS[p.rot as usize][dir] {
            let n = P { rot: nr, col: p.col + dx, row: p.row + dy };
            if self.valid(n) { return Some(n); }
        }
        None
    }
    fn hard_drop(&self, p: P) -> P {
        let mut cur = p;
        while let Some(n) = self.try_move(cur, 0, 1) { cur = n; }
        cur
    }
    /// `detectTSpin(board, p, true, _) !== 'none'`: three of the four corners round the centre occupied.
    fn spin(&self, p: P) -> bool {
        let (cx, cy) = (p.col + 1, p.row + 1);
        let occ = |c: i32, r: i32| if c < 0 || c >= W || r >= H { true } else if r < 0 { false } else { self.filled(r, c) };
        [(-1, -1), (1, -1), (-1, 1), (1, 1)].iter().filter(|&&(dc, dr)| occ(cx + dc, cy + dr)).count() >= 3
    }
}

/// The answer; `lines` 0 is the TS `null`.
pub struct Best { pub lines: i32, pub rows: [i32; 5], pub floor: i32 }

/// The visited window of forecast.ts (`visitIndex`), with a set for anything outside it. Any exact
/// set gives the same search; the window only keeps the common case off the hash.
const V_COL_MIN: i32 = -2;
const V_COL_N: i32 = 12;
const V_ROW_MIN: i32 = -4;
const V_ROW_N: i32 = 48;
const V_SIZE: usize = (4 * V_COL_N * V_ROW_N) as usize;
fn vidx(p: P) -> Option<usize> {
    let (c, r) = (p.col - V_COL_MIN, p.row - V_ROW_MIN);
    if c < 0 || c >= V_COL_N || r < 0 || r >= V_ROW_N { None } else { Some(((p.rot as i32 * V_COL_N + c) * V_ROW_N + r) as usize) }
}
struct Seen { tab: [bool; V_SIZE], out: HashSet<P> }
impl Seen {
    fn new() -> Seen { Seen { tab: [false; V_SIZE], out: HashSet::new() } }
    /// True if already marked; marks it either way.
    fn seen_or_mark(&mut self, p: P) -> bool {
        match vidx(p) {
            Some(i) => { let s = self.tab[i]; self.tab[i] = true; s }
            None => !self.out.insert(p),
        }
    }
}

#[derive(Clone, Copy)]
struct Entry { p: P, rot: bool, expand: bool }

pub fn best_tspin(b: &Board) -> Best {
    let mut best = Best { lines: 0, rows: [0; 5], floor: H };
    let spawn = P { rot: 0, col: 3, row: 18 };
    let mut pos = Seen::new();
    let mut rot_seen = Seen::new();
    pos.seen_or_mark(spawn);
    let mut q: Vec<Entry> = Vec::with_capacity(1024);
    q.push(Entry { p: spawn, rot: false, expand: true });
    let mut h = 0;
    while h < q.len() && h < CAP {
        let Entry { p: cur, rot, expand } = q[h];
        h += 1;
        let d = b.hard_drop(cur);
        if d.row == cur.row && rot && b.spin(d) {
            let cells = T_CELLS[d.rot as usize].map(|(dc, dr)| (d.col + dc, d.row + dr));
            let mut rows = b.rows;
            for &(c, r) in &cells { if r >= 0 && r < H { rows[r as usize] |= 1 << c; } }
            let lines = rows.iter().filter(|&&x| x == FULL).count() as i32;
            if lines > best.lines {
                best.lines = lines;
                let mn = cells.iter().map(|&(_, r)| r).min().unwrap();
                best.rows = [cells[0].1, cells[1].1, cells[2].1, cells[3].1, mn - 1];
                let mut floor = -1;
                for &(c, r) in &cells {
                    let below = r + 1;
                    if cells.iter().any(|&(oc, or)| oc == c && or == below) { continue; }
                    if below >= H || b.filled(below, c) { floor = floor.max(below); }
                }
                best.floor = if floor < 0 { H } else { floor };
            }
        }
        if !expand { continue; }
        let nexts = [
            (b.try_move(cur, -1, 0), false), (b.try_move(cur, 1, 0), false), (b.try_move(cur, 0, 1), false),
            (b.try_rotate(cur, 0), true), (b.try_rotate(cur, 1), true),
        ];
        for (n, is_rot) in nexts {
            let Some(n) = n else { continue };
            if !is_rot {
                if pos.seen_or_mark(n) { continue; }
                q.push(Entry { p: n, rot: false, expand: true });
                continue;
            }
            if rot_seen.seen_or_mark(n) { continue; }
            let expand = !pos.seen_or_mark(n);
            q.push(Entry { p: n, rot: true, expand });
        }
    }
    best
}

/// `cells`: H*W bytes row-major, non-zero = filled. `out`: [lines, floor, rows[0..5]].
/// Returns 0, or -1 on a null pointer.
///
/// # Safety
/// `cells` must point at H*W bytes and `out` at 7 i32s.
#[no_mangle]
pub unsafe extern "C" fn forecast_best_tspin(cells: *const u8, out: *mut i32) -> i32 {
    if cells.is_null() || out.is_null() { return -1; }
    let cells = std::slice::from_raw_parts(cells, (H * W) as usize);
    let out = std::slice::from_raw_parts_mut(out, 7);
    let r = best_tspin(&Board::from_cells(cells));
    out[0] = r.lines;
    out[1] = r.floor;
    out[2..7].copy_from_slice(&r.rows);
    0
}

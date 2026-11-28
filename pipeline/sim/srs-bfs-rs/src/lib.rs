//! The Rust port of the 0G-complete BFS that `cross-movegen.test.ts` (`ourReachable`) and
//! `cross-tspin.test.ts` (`spinCandidates`) both run over the vendored SRS primitives in
//! `vendor/core/srs.ts` (`tryMove`, `tryRotate`, `hardDrop`, `isValidPosition`), loaded through
//! bun:ffi by `srs-bfs-native.ts`. Same state key (rotation, col, row), same expansion order
//! (left, right, down, CW, CCW), same kick tables (SRS, or SRS+ for the I piece when asked).
//!
//! It is OUR side of both cross tests and nothing else: the cold-clear side (the `cc-oracle`
//! binary, `cc-tspin.ts`'s rule and kick index) and `detectTSpin` stay TypeScript. `srs-bfs-native.test.ts`
//! holds this answer equal to the TS BFS on seeded boards and a stride of real boards.
//!
//! Output (i32, caller-provided buffer), per mode:
//!   mode 0 (reachable):  every DISTINCT hard-dropped state of a visited state, as `rot, col, row`,
//!                        in first-seen order.
//!   mode 1 (spins):      for each visited state in BFS order and each of CW then CCW: when the
//!                        rotation succeeds and the result cannot fall one row, the six numbers
//!                        `pre_rot, pre_col, pre_row, post_rot, post_col, post_row` (undeduped; the
//!                        caller attaches cold-clear's kick index and dedups).
//! The return value is the number of i32s written, or -1 if the buffer was too small, -2 for a bad
//! argument. Nothing here may panic (the crate builds with panic = "abort").

use std::collections::VecDeque;

pub const H: i32 = 40;
pub const W: i32 = 10;

/// `PIECE_DEFINITIONS[*].cells` (vendor/core/pieces.ts) as (dc, dr), piece order I T O S Z L J.
const CELLS: [[[(i32, i32); 4]; 4]; 7] = [
    // I
    [[(0, 1), (1, 1), (2, 1), (3, 1)], [(2, 0), (2, 1), (2, 2), (2, 3)],
     [(0, 2), (1, 2), (2, 2), (3, 2)], [(1, 0), (1, 1), (1, 2), (1, 3)]],
    // T
    [[(1, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (2, 1), (1, 2)],
     [(0, 1), (1, 1), (2, 1), (1, 2)], [(1, 0), (0, 1), (1, 1), (1, 2)]],
    // O
    [[(1, 0), (2, 0), (1, 1), (2, 1)], [(1, 0), (2, 0), (1, 1), (2, 1)],
     [(1, 0), (2, 0), (1, 1), (2, 1)], [(1, 0), (2, 0), (1, 1), (2, 1)]],
    // S
    [[(1, 0), (2, 0), (0, 1), (1, 1)], [(1, 0), (1, 1), (2, 1), (2, 2)],
     [(1, 1), (2, 1), (0, 2), (1, 2)], [(0, 0), (0, 1), (1, 1), (1, 2)]],
    // Z
    [[(0, 0), (1, 0), (1, 1), (2, 1)], [(2, 0), (1, 1), (2, 1), (1, 2)],
     [(0, 1), (1, 1), (1, 2), (2, 2)], [(1, 0), (0, 1), (1, 1), (0, 2)]],
    // L
    [[(2, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (1, 2), (2, 2)],
     [(0, 1), (1, 1), (2, 1), (0, 2)], [(0, 0), (1, 0), (1, 1), (1, 2)]],
    // J
    [[(0, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (2, 0), (1, 1), (1, 2)],
     [(0, 1), (1, 1), (2, 1), (2, 2)], [(1, 0), (1, 1), (0, 2), (1, 2)]],
];

type K = [(i32, i32); 5];
/// `JLSZT_KICKS`, indexed by the kick key '0->1' '1->0' '1->2' '2->1' '2->3' '3->2' '3->0' '0->3'
/// as `from * 2 + (0 for CW, 1 for CCW)`; every CW transition `r -> r+1` and CCW `r -> r-1` is one of the 8.
const JLSZT: [K; 8] = [
    [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],   // 0->1
    [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],      // 0->3
    [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],     // 1->2
    [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],     // 1->0
    [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],      // 2->3
    [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],   // 2->1
    [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],  // 3->0
    [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],  // 3->2
];
const I_SRS: [K; 8] = [
    [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],    // 0->1
    [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],    // 0->3
    [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],    // 1->2
    [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],    // 1->0
    [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],    // 2->3
    [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],    // 2->1
    [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],    // 3->0
    [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],    // 3->2
];
const I_PLUS: [K; 8] = [
    [(0, 0), (1, 0), (-2, 0), (-2, 1), (1, -2)],    // 0->1
    [(0, 0), (-1, 0), (2, 0), (2, 1), (-1, -2)],    // 0->3
    [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],    // 1->2
    [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],    // 1->0
    [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],    // 2->3
    [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],    // 2->1
    [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],    // 3->0
    [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],    // 3->2
];
const O_KICKS: [K; 8] = [[(0, 0); 5]; 8];

#[derive(Clone, Copy)]
struct P { r: i32, c: i32, y: i32 }

struct Ctx<'a> { board: &'a [u8], piece: usize, kicks: &'a [K; 8] }

impl<'a> Ctx<'a> {
    /// `isValidPosition`: sideways and floor bounds, rows above the board free, a filled cell blocks.
    fn valid(&self, p: P) -> bool {
        for &(dc, dr) in CELLS[self.piece][p.r as usize].iter() {
            let c = p.c + dc;
            let r = p.y + dr;
            if c < 0 || c >= W { return false; }
            if r >= H { return false; }
            if r < 0 { continue; }
            if self.board[(r * W + c) as usize] != 0 { return false; }
        }
        true
    }
    fn mv(&self, p: P, dx: i32, dy: i32) -> Option<P> {
        let q = P { r: p.r, c: p.c + dx, y: p.y + dy };
        if self.valid(q) { Some(q) } else { None }
    }
    /// `tryRotate`: `dir` is +1 (CW) or -1 (CCW); the first legal kick wins.
    fn rot(&self, p: P, dir: i32) -> Option<P> {
        let nr = (p.r + dir + 4) % 4;
        // kick key index: from*2 + (CW 0 / CCW 1), which names exactly `from->to`
        let idx = (p.r * 2 + if dir == 1 { 0 } else { 1 }) as usize;
        for &(dx, dy) in self.kicks[idx].iter() {
            let q = P { r: nr, c: p.c + dx, y: p.y + dy };
            if self.valid(q) { return Some(q); }
        }
        None
    }
    fn drop(&self, p: P) -> P {
        let mut cur = p;
        while let Some(n) = self.mv(cur, 0, 1) { cur = n; }
        cur
    }
}

const COLS: i32 = 24;      // col in [-4, 19]
const COL0: i32 = 4;
const ROWS: i32 = 80;      // row in [-20, 59]
const ROW0: i32 = 20;
fn slot(p: P) -> Option<usize> {
    let c = p.c + COL0;
    let y = p.y + ROW0;
    if c < 0 || c >= COLS || y < 0 || y >= ROWS || p.r < 0 || p.r > 3 { return None; }
    Some((((p.r * ROWS) + y) * COLS + c) as usize)
}

/// See the module header for the layout. `board` is `H * W` bytes, row-major, nonzero = filled.
#[no_mangle]
pub extern "C" fn srs_bfs(board: *const u8, piece: u32, kickset_plus: u32, col: i32, row: i32,
                          mode: u32, out: *mut i32, cap: u32) -> i32 {
    if board.is_null() || out.is_null() || piece > 6 || mode > 1 { return -2; }
    let board = unsafe { std::slice::from_raw_parts(board, (H * W) as usize) };
    let out = unsafe { std::slice::from_raw_parts_mut(out, cap as usize) };
    let kicks: &[K; 8] = match piece {
        0 => if kickset_plus != 0 { &I_PLUS } else { &I_SRS },
        2 => &O_KICKS,
        _ => &JLSZT,
    };
    let cx = Ctx { board, piece: piece as usize, kicks };
    let spawn = P { r: 0, c: col, y: row };
    let mut n = 0usize;
    if !cx.valid(spawn) { return 0; }
    let mut seen = vec![false; (4 * ROWS * COLS) as usize];
    let mut dropped = vec![false; (4 * ROWS * COLS) as usize];
    let mut q: VecDeque<P> = VecDeque::new();
    match slot(spawn) { Some(s) => seen[s] = true, None => return -2 }
    q.push_back(spawn);
    macro_rules! push { ($($v:expr),*) => {{
        let vals = [$($v as i32),*];
        if n + vals.len() > out.len() { return -1; }
        for v in vals { out[n] = v; n += 1; }
    }}; }
    while let Some(cur) = q.pop_front() {
        if mode == 0 {
            let d = cx.drop(cur);
            match slot(d) {
                Some(s) => if !dropped[s] { dropped[s] = true; push!(d.r, d.c, d.y); },
                None => return -2,
            }
        } else {
            for dir in [1, -1] {
                if let Some(post) = cx.rot(cur, dir) {
                    if cx.mv(post, 0, 1).is_some() { continue; }
                    push!(cur.r, cur.c, cur.y, post.r, post.c, post.y);
                }
            }
        }
        let ns = [cx.mv(cur, -1, 0), cx.mv(cur, 1, 0), cx.mv(cur, 0, 1), cx.rot(cur, 1), cx.rot(cur, -1)];
        for nb in ns.into_iter().flatten() {
            match slot(nb) {
                Some(s) => if !seen[s] { seen[s] = true; q.push_back(nb); },
                None => return -2,
            }
        }
    }
    n as i32
}

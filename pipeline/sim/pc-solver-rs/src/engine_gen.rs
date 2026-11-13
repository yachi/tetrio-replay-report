//! The engine movegen `pc-engine-gen.ts` uses (`enginePlacements`): every candidate placement in a
//! frame of height `h` that the vendored Triangle engine can reach from its spawn by shift, one-row
//! fall, CW, CCW and 180 through its SRS+ kicks (`route-demos.ts`'s `reach` BFS), in the TS order.
//!
//! What had to be matched, read off `pipeline/sim/vendor/teto/engine` (not guessed):
//! * spawn (`Tetromino` constructor): x = floor(10/2 - w/2) with w the matrix width (I 4, O 2, the
//!   rest 3), so x = 3 (I), 4 (O), 3 (others); y = boardHeight + 2.04 = 22.04, rotation 0 (SRS+ has
//!   no `spawn_rotation`). `initiatePiece(_, true)` with clutch off (a fresh engine's
//!   `lastWasClear` is false) never moves the spawn, legal or not.
//! * blocks: `absoluteAt` puts block (bx, by) at (x + bx, floor(y) - by), board y-up; `legal` bounds
//!   are 0 <= x < 10 and 0 <= y < 40 (the 40-row state `reach` writes into the engine).
//! * y is fractional but never an integer (22.04 spawn; a kick sets ceil(y) - 0.1 - dy, i.e. x.9; a
//!   fall subtracts 1 rounded to 1e-6), so every move acts on floor(y) alone: a fall tests floor-1,
//!   a kick (dx, dy) lands at (x + dx, floor(y) - dy), and the unkicked test is at (x, floor(y)).
//!   `maxMovement` is false because `reach` zeroes `totalRotations` before every rotation.
//! * kicks: `SRS+` `i_kicks` for I, `kicks` for every other piece (O included: `o_kicks` does not
//!   exist and `oo_kicks` is never selected), keyed `${from}${to}`, 180 included.
//! * the BFS keys a state by (rotation, x, floor y, lastSpin); no move's result depends on lastSpin,
//!   so the reachable (rotation, x, floor y) set — all `enginePlacements` asks about — is the BFS
//!   over those three alone.

use std::collections::HashSet;

const W: i32 = 10;
const ROWS: i32 = 40;

/// Engine tetromino states (`utils/tetromino/data.mjs`, `matrix.data`, the [x, y] of each block).
fn states(piece: u8) -> &'static [[(i8, i8); 4]; 4] {
    const I: [[(i8, i8); 4]; 4] = [
        [(0, 1), (1, 1), (2, 1), (3, 1)], [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(3, 2), (2, 2), (1, 2), (0, 2)], [(1, 3), (1, 2), (1, 1), (1, 0)]];
    const O: [[(i8, i8); 4]; 4] = [
        [(0, 0), (1, 0), (0, 1), (1, 1)], [(1, 0), (1, 1), (0, 0), (0, 1)],
        [(1, 1), (0, 1), (1, 0), (0, 0)], [(0, 1), (0, 0), (1, 1), (1, 0)]];
    const J: [[(i8, i8); 4]; 4] = [
        [(0, 0), (0, 1), (1, 1), (2, 1)], [(2, 0), (1, 0), (1, 1), (1, 2)],
        [(2, 2), (2, 1), (1, 1), (0, 1)], [(0, 2), (1, 2), (1, 1), (1, 0)]];
    const L: [[(i8, i8); 4]; 4] = [
        [(2, 0), (0, 1), (1, 1), (2, 1)], [(2, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 2), (2, 1), (1, 1), (0, 1)], [(0, 0), (1, 2), (1, 1), (1, 0)]];
    const S: [[(i8, i8); 4]; 4] = [
        [(1, 0), (2, 0), (0, 1), (1, 1)], [(2, 1), (2, 2), (1, 0), (1, 1)],
        [(1, 2), (0, 2), (2, 1), (1, 1)], [(0, 1), (0, 0), (1, 2), (1, 1)]];
    const Z: [[(i8, i8); 4]; 4] = [
        [(0, 0), (1, 0), (1, 1), (2, 1)], [(2, 0), (2, 1), (1, 1), (1, 2)],
        [(2, 2), (1, 2), (1, 1), (0, 1)], [(0, 2), (0, 1), (1, 1), (1, 0)]];
    const T: [[(i8, i8); 4]; 4] = [
        [(1, 0), (0, 1), (1, 1), (2, 1)], [(2, 1), (1, 0), (1, 1), (1, 2)],
        [(1, 2), (2, 1), (1, 1), (0, 1)], [(0, 1), (1, 2), (1, 1), (1, 0)]];
    match piece {
        b'I' => &I, b'O' => &O, b'J' => &J, b'L' => &L, b'S' => &S, b'Z' => &Z, b'T' => &T,
        _ => panic!("engine_gen: bad piece {}", piece as char),
    }
}

/// `kicks["SRS+"]`: index [from][to] → (dx, dy) list. `kicks` for J L S Z T O, `i_kicks` for I.
fn kicks(piece: u8, from: usize, to: usize) -> &'static [(i8, i8)] {
    const K: [[&[(i8, i8)]; 4]; 4] = [
        [&[], &[(-1, 0), (-1, -1), (0, 2), (-1, 2)], &[(0, -1), (1, -1), (-1, -1), (1, 0), (-1, 0)], &[(1, 0), (1, -1), (0, 2), (1, 2)]],
        [&[(1, 0), (1, 1), (0, -2), (1, -2)], &[], &[(1, 0), (1, 1), (0, -2), (1, -2)], &[(1, 0), (1, -2), (1, -1), (0, -2), (0, -1)]],
        [&[(0, 1), (-1, 1), (1, 1), (-1, 0), (1, 0)], &[(-1, 0), (-1, -1), (0, 2), (-1, 2)], &[], &[(1, 0), (1, -1), (0, 2), (1, 2)]],
        [&[(-1, 0), (-1, 1), (0, -2), (-1, -2)], &[(-1, 0), (-1, -2), (-1, -1), (0, -2), (0, -1)], &[(-1, 0), (-1, 1), (0, -2), (-1, -2)], &[]],
    ];
    const KI: [[&[(i8, i8)]; 4]; 4] = [
        [&[], &[(1, 0), (-2, 0), (-2, 1), (1, -2)], &[(0, -1)], &[(-1, 0), (2, 0), (2, 1), (-1, -2)]],
        [&[(-1, 0), (2, 0), (-1, 2), (2, -1)], &[], &[(-1, 0), (2, 0), (-1, -2), (2, 1)], &[(1, 0)]],
        [&[(0, 1)], &[(-2, 0), (1, 0), (-2, -1), (1, 2)], &[], &[(2, 0), (-1, 0), (2, -1), (-1, 2)]],
        [&[(1, 0), (-2, 0), (1, 2), (-2, -1)], &[(-1, 0)], &[(1, 0), (-2, 0), (1, -2), (-2, 1)], &[]],
    ];
    if piece == b'I' { KI[from][to] } else { K[from][to] }
}

/// `SHAPES` of emit-replay.ts: each distinct orientation, normalised, cells sorted by (y, x).
fn shapes(piece: u8) -> &'static [[(u8, u8); 4]] {
    match piece {
        b'I' => &[[(0, 0), (1, 0), (2, 0), (3, 0)], [(0, 0), (0, 1), (0, 2), (0, 3)]],
        b'O' => &[[(0, 0), (1, 0), (0, 1), (1, 1)]],
        b'T' => &[[(0, 0), (1, 0), (2, 0), (1, 1)], [(0, 0), (0, 1), (1, 1), (0, 2)],
                  [(1, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (0, 1), (1, 1), (1, 2)]],
        b'S' => &[[(0, 0), (1, 0), (1, 1), (2, 1)], [(1, 0), (0, 1), (1, 1), (0, 2)]],
        b'Z' => &[[(1, 0), (2, 0), (0, 1), (1, 1)], [(0, 0), (0, 1), (1, 1), (1, 2)]],
        b'J' => &[[(0, 0), (1, 0), (2, 0), (0, 1)], [(0, 0), (0, 1), (0, 2), (1, 2)],
                  [(2, 0), (0, 1), (1, 1), (2, 1)], [(0, 0), (1, 0), (1, 1), (1, 2)]],
        b'L' => &[[(0, 0), (1, 0), (2, 0), (2, 1)], [(0, 0), (1, 0), (0, 1), (0, 2)],
                  [(0, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (0, 2), (1, 2)]],
        _ => panic!("engine_gen: bad piece {}", piece as char),
    }
}

struct Board([u16; ROWS as usize]);

impl Board {
    fn new(rows: &[u16]) -> Board {
        let mut b = [0u16; ROWS as usize];
        for (y, r) in rows.iter().take(ROWS as usize).enumerate() { b[y] = r & 0x3ff; }
        Board(b)
    }
    #[inline]
    fn filled(&self, x: i32, y: i32) -> bool { self.0[y as usize] >> x & 1 != 0 }
    /// `legal(absoluteAt({x, y, rotation: r}))`, with `fy` = floor(y).
    #[inline]
    fn legal(&self, st: &[(i8, i8); 4], x: i32, fy: i32) -> bool {
        st.iter().all(|&(bx, by)| {
            let (cx, cy) = (x + bx as i32, fy - by as i32);
            (0..W).contains(&cx) && (0..ROWS).contains(&cy) && !self.filled(cx, cy)
        })
    }
}

// state index: rotation (4) × x in [-4, 13] (18) × floor y in [-4, 47] (52)
const XO: i32 = 4;
const NX: i32 = 18;
const YO: i32 = 4;
const NY: i32 = 52;

/// Every resting placement's cells (sorted ascending) the engine can reach for `piece` on `rows`.
pub fn reachable(rows: &[u16], piece: u8) -> HashSet<[u16; 4]> {
    let b = Board::new(rows);
    let sts = states(piece);
    let idx = |r: usize, x: i32, fy: i32| (r as i32 * NX * NY + (x + XO) * NY + (fy + YO)) as usize;
    let mut seen = vec![false; (4 * NX * NY) as usize];
    let sx = if piece == b'I' { 3 } else if piece == b'O' { 4 } else { 3 };
    let start = (0usize, sx, 22i32);
    let mut queue = vec![start];
    seen[idx(0, sx, 22)] = true;
    let mut out = HashSet::new();
    let mut qi = 0;
    while qi < queue.len() {
        let (r, x, fy) = queue[qi];
        qi += 1;
        let st = &sts[r];
        let can_fall = b.legal(st, x, fy - 1);
        if !can_fall {
            let mut cells = [0u16; 4];
            for (i, &(bx, by)) in st.iter().enumerate() {
                cells[i] = ((fy - by as i32) * W + x + bx as i32) as u16;
            }
            cells.sort_unstable();
            out.insert(cells);
        }
        let mut push = |n: (usize, i32, i32), q: &mut Vec<(usize, i32, i32)>| {
            let k = idx(n.0, n.1, n.2);
            if !seen[k] { seen[k] = true; q.push(n); }
        };
        if b.legal(st, x - 1, fy) { push((r, x - 1, fy), &mut queue); }
        if b.legal(st, x + 1, fy) { push((r, x + 1, fy), &mut queue); }
        if can_fall { push((r, x, fy - 1), &mut queue); }
        for amt in [1usize, 3, 2] {
            let to = (r + amt) % 4;
            let ts = &sts[to];
            let n = if b.legal(ts, x, fy) {
                Some((to, x, fy))
            } else {
                kicks(piece, r, to).iter().map(|&(dx, dy)| (to, x + dx as i32, fy - dy as i32))
                    .find(|&(_, nx, ny)| b.legal(ts, nx, ny))
            };
            if let Some(n) = n { push(n, &mut queue); }
        }
    }
    out
}

/// `enginePlacements(rows, piece, H)` of pc-engine-gen.ts, same list in the same order.
pub fn engine_placements(rows: &[u16], piece: u8, h: usize) -> Vec<Vec<u16>> {
    let b = Board::new(rows);
    let mut reach: Option<HashSet<[u16; 4]>> = None;
    let mut out = Vec::new();
    for shape in shapes(piece) {
        let w = shape.iter().map(|c| c.0).max().unwrap() as usize + 1;
        let sh = shape.iter().map(|c| c.1).max().unwrap() as usize + 1;
        let mut ay = 0;
        while ay + sh <= h {
            for ax in 0..=(W as usize - w) {
                let cells: Vec<(i32, i32)> = shape.iter().map(|&(dx, dy)| ((ax + dx as usize) as i32, (ay + dy as usize) as i32)).collect();
                if cells.iter().any(|&(x, y)| y < ROWS && b.filled(x, y)) { continue; }
                if !cells.iter().any(|&(x, y)| y == 0 || (y - 1 < ROWS && b.filled(x, y - 1))) { continue; }
                let mut key = [0u16; 4];
                for (i, &(x, y)) in cells.iter().enumerate() { key[i] = (y * W + x) as u16; }
                key.sort_unstable();
                let set = reach.get_or_insert_with(|| reachable(rows, piece));
                if set.contains(&key) { out.push(key.to_vec()); }
            }
            ay += 1;
        }
    }
    out
}

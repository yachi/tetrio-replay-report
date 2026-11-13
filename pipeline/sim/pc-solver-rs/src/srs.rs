//! The SRS+ movegen of pc-solver.ts `placements`, ported exactly from the vendored
//! `vendor/core/srs.ts` (tryMove / tryRotate / getPieceCells) with `setKickset('SRS+')`.
//!
//! Board convention matches the TS: a 40-row board, row 0 at the TOP, `+dy` = down. Mask row `y`
//! (y-up, bit x = column x) sits at board row `39 - y`. Output cells are `y*10 + x`, sorted, in the
//! order each distinct cell set was FIRST found by the BFS (the DFS returns the first plan it finds,
//! so this order is part of the answer).

pub const W: i32 = 10;
pub const BROWS: i32 = 40;

/// Piece index: I T O S Z L J (vendor/core/types.ts ALL_PIECE_TYPES order). 0xFF = none.
pub const PIECES: &[u8; 7] = b"ITOSZLJ";

pub fn piece_index(c: u8) -> Option<usize> {
    PIECES.iter().position(|&p| p == c)
}

/// vendor/core/pieces.ts PIECE_DEFINITIONS, [col, row] offsets, (0,0) top-left of the box.
const CELLS: [[[(i8, i8); 4]; 4]; 7] = [
    // I
    [[(0, 1), (1, 1), (2, 1), (3, 1)], [(2, 0), (2, 1), (2, 2), (2, 3)], [(0, 2), (1, 2), (2, 2), (3, 2)], [(1, 0), (1, 1), (1, 2), (1, 3)]],
    // T
    [[(1, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (2, 1), (1, 2)], [(0, 1), (1, 1), (2, 1), (1, 2)], [(1, 0), (0, 1), (1, 1), (1, 2)]],
    // O
    [[(1, 0), (2, 0), (1, 1), (2, 1)], [(1, 0), (2, 0), (1, 1), (2, 1)], [(1, 0), (2, 0), (1, 1), (2, 1)], [(1, 0), (2, 0), (1, 1), (2, 1)]],
    // S
    [[(1, 0), (2, 0), (0, 1), (1, 1)], [(1, 0), (1, 1), (2, 1), (2, 2)], [(1, 1), (2, 1), (0, 2), (1, 2)], [(0, 0), (0, 1), (1, 1), (1, 2)]],
    // Z
    [[(0, 0), (1, 0), (1, 1), (2, 1)], [(2, 0), (1, 1), (2, 1), (1, 2)], [(0, 1), (1, 1), (1, 2), (2, 2)], [(1, 0), (0, 1), (1, 1), (0, 2)]],
    // L
    [[(2, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (1, 2), (2, 2)], [(0, 1), (1, 1), (2, 1), (0, 2)], [(0, 0), (1, 0), (1, 1), (1, 2)]],
    // J
    [[(0, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (2, 0), (1, 1), (1, 2)], [(0, 1), (1, 1), (2, 1), (2, 2)], [(1, 0), (1, 1), (0, 2), (1, 2)]],
];

type Kicks = [[(i8, i8); 5]; 8];
// Index of a kick key: from*2 + (dir==+1 ? 0 : 1); i.e. 0->1, 0->3, 1->2, 1->0, 2->3, 2->1, 3->0, 3->2.
const fn ki(from: usize, cw: bool) -> usize { from * 2 + if cw { 0 } else { 1 } }

// JLSZT_KICKS
const JLSZT: Kicks = {
    let mut k = [[(0i8, 0i8); 5]; 8];
    k[ki(0, true)] = [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)];   // 0->1
    k[ki(1, false)] = [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)];    // 1->0
    k[ki(1, true)] = [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)];     // 1->2
    k[ki(2, false)] = [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)];  // 2->1
    k[ki(2, true)] = [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)];      // 2->3
    k[ki(3, false)] = [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)]; // 3->2
    k[ki(3, true)] = [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)];  // 3->0
    k[ki(0, false)] = [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)];     // 0->3
    k
};

// I_KICKS_PLUS (TETR.IO SRS+)
const IPLUS: Kicks = {
    let mut k = [[(0i8, 0i8); 5]; 8];
    k[ki(0, true)] = [(0, 0), (1, 0), (-2, 0), (-2, 1), (1, -2)];    // 0->1
    k[ki(1, false)] = [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)];   // 1->0
    k[ki(1, true)] = [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)];    // 1->2
    k[ki(2, false)] = [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)];   // 2->1
    k[ki(2, true)] = [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)];    // 2->3
    k[ki(3, false)] = [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)];   // 3->2
    k[ki(3, true)] = [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)];    // 3->0
    k[ki(0, false)] = [(0, 0), (-1, 0), (2, 0), (2, 1), (-1, -2)];   // 0->3
    k
};

/// Board: row r (0 = top) as a 10-bit mask; rows outside [0, 40) handled by `valid`.
struct Board { b: [u16; BROWS as usize] }

impl Board {
    #[inline]
    fn valid(&self, t: usize, rot: usize, col: i32, row: i32) -> bool {
        for &(dc, dr) in &CELLS[t][rot] {
            let c = col + dc as i32;
            let r = row + dr as i32;
            if c < 0 || c >= W { return false; }
            if r >= BROWS { return false; }
            if r < 0 { continue; }
            if self.b[r as usize] >> c & 1 != 0 { return false; }
        }
        true
    }
}

#[derive(Clone, Copy)]
struct P { rot: u8, col: i8, row: i8 }

// seen index: rot (4) x col+4 (16) x row+8 (56)
const SC: usize = 16;
const SR: usize = 56;
#[inline]
fn sidx(p: P) -> usize { (p.rot as usize * SC + (p.col as i32 + 4) as usize) * SR + (p.row as i32 + 8) as usize }

/// pc-solver.ts `placements` (the SRS branch), cells as `y*10+x` sorted ascending.
pub fn srs_placements(rows: &[u16], piece: usize, h: i32) -> Vec<[u8; 4]> {
    let mut board = Board { b: [0; BROWS as usize] };
    for (y, &m) in rows.iter().enumerate() {
        if (y as i32) < BROWS { board.b[(BROWS - 1 - y as i32) as usize] = m & 0x3ff; }
    }
    let start = P { rot: 0, col: 3, row: (BROWS - 1 - (h + 4) - 3) as i8 };
    let mut seen = vec![false; 4 * SC * SR];
    let mut q: Vec<P> = Vec::with_capacity(256);
    let mut out: Vec<[u8; 4]> = Vec::new();
    let mut outk: Vec<u32> = Vec::new();
    seen[sidx(start)] = true;
    q.push(start);
    let kicks: &Kicks = if piece == 0 { &IPLUS } else { &JLSZT };
    let mut i = 0;
    while i < q.len() {
        let p = q[i];
        i += 1;
        let (rot, col, row) = (p.rot as usize, p.col as i32, p.row as i32);
        let down = board.valid(piece, rot, col, row + 1);
        if !down {
            let mut cells = [0u8; 4];
            let mut all = true;
            for (j, &(dc, dr)) in CELLS[piece][rot].iter().enumerate() {
                let y = BROWS - 1 - (row + dr as i32);
                let v = y * W + col + dc as i32;
                // Math.floor(c / W) < H; c may be negative only when y < 0, impossible (row < 40).
                if y >= h { all = false; }
                cells[j] = v as u8;
            }
            if all {
                cells.sort_unstable();
                let k = (cells[0] as u32) | (cells[1] as u32) << 8 | (cells[2] as u32) << 16 | (cells[3] as u32) << 24;
                if !outk.contains(&k) { outk.push(k); out.push(cells); }
            }
        }
        // neighbours in TS order: left, right, down, CW, CCW
        let mut nb: [Option<P>; 5] = [None; 5];
        if board.valid(piece, rot, col - 1, row) { nb[0] = Some(P { rot: p.rot, col: (col - 1) as i8, row: p.row }); }
        if board.valid(piece, rot, col + 1, row) { nb[1] = Some(P { rot: p.rot, col: (col + 1) as i8, row: p.row }); }
        if down { nb[2] = Some(P { rot: p.rot, col: p.col, row: (row + 1) as i8 }); }
        for (slot, cw) in [(3usize, true), (4usize, false)] {
            let nr = if cw { (rot + 1) % 4 } else { (rot + 3) % 4 };
            let ks = if piece == 2 { &[(0i8, 0i8)][..] } else { &kicks[ki(rot, cw)][..] };
            for &(dx, dy) in ks {
                let (c2, r2) = (col + dx as i32, row + dy as i32);
                if board.valid(piece, nr, c2, r2) {
                    nb[slot] = Some(P { rot: nr as u8, col: c2 as i8, row: r2 as i8 });
                    break;
                }
            }
        }
        for n in nb.into_iter().flatten() {
            if BROWS - 1 - n.row as i32 > h + 8 { continue; }
            let s = sidx(n);
            if seen[s] { continue; }
            seen[s] = true;
            q.push(n);
        }
    }
    out
}

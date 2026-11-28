//! 千鳥格子練習場's difficulty search (`pipeline/sim/cutcopy-drills.ts` `minNeedTs`) in Rust: breadth first
//! over every placement of every piece (hold allowed), the depth at which a Cut Copy window build first
//! stands. It is a port of `pipeline/cutcopy_practice_engine.js` (its `placements` BFS, `lock`, `addGarbage`,
//! `matchWindow`, `carry`) plus the search's own `kids` / `windowCanStand` / `buildable`, operation for
//! operation and in the same order: the search keeps the FIRST node per (queue index, hold, board) key, and
//! which node that is decides which garbage events a later node meets. `cutcopy-native.ts` loads it through
//! bun:ffi and `cutcopy-native.test.ts` holds its answers equal to `minNeedTs`'s. The tables are the JS
//! engine's own copy, not `data.rs`'s.

use std::collections::{HashSet, VecDeque};

const W: i32 = 10;
const H: i32 = 40;
/// "IJLOSTZ"
const T_IDX: usize = 5;
const WIDTH: [i32; 7] = [4, 3, 3, 2, 3, 3, 3];
const STATES: [[[(i32, i32); 4]; 4]; 7] = [
    [[(0,1),(1,1),(2,1),(3,1)],[(2,0),(2,1),(2,2),(2,3)],[(3,2),(2,2),(1,2),(0,2)],[(1,3),(1,2),(1,1),(1,0)]],
    [[(0,0),(0,1),(1,1),(2,1)],[(2,0),(1,0),(1,1),(1,2)],[(2,2),(2,1),(1,1),(0,1)],[(0,2),(1,2),(1,1),(1,0)]],
    [[(2,0),(0,1),(1,1),(2,1)],[(2,2),(1,0),(1,1),(1,2)],[(0,2),(2,1),(1,1),(0,1)],[(0,0),(1,2),(1,1),(1,0)]],
    [[(0,0),(1,0),(0,1),(1,1)],[(1,0),(1,1),(0,0),(0,1)],[(1,1),(0,1),(1,0),(0,0)],[(0,1),(0,0),(1,1),(1,0)]],
    [[(1,0),(2,0),(0,1),(1,1)],[(2,1),(2,2),(1,0),(1,1)],[(1,2),(0,2),(2,1),(1,1)],[(0,1),(0,0),(1,2),(1,1)]],
    [[(1,0),(0,1),(1,1),(2,1)],[(2,1),(1,0),(1,1),(1,2)],[(1,2),(2,1),(1,1),(0,1)],[(0,1),(1,2),(1,1),(1,0)]],
    [[(0,0),(1,0),(1,1),(2,1)],[(2,0),(2,1),(1,1),(1,2)],[(2,2),(1,2),(1,1),(0,1)],[(0,2),(0,1),(1,1),(1,0)]],
];
type Kicks = [&'static [(i32, i32)]; 16];
const N: &[(i32, i32)] = &[];
const KI: Kicks = [N, &[(1,0),(-2,0),(-2,1),(1,-2)], &[(0,-1)], &[(-1,0),(2,0),(2,1),(-1,-2)],
    &[(-1,0),(2,0),(-1,2),(2,-1)], N, &[(-1,0),(2,0),(-1,-2),(2,1)], &[(1,0)], &[(0,1)],
    &[(-2,0),(1,0),(-2,-1),(1,2)], N, &[(2,0),(-1,0),(2,-1),(-1,2)], &[(1,0),(-2,0),(1,2),(-2,-1)],
    &[(-1,0)], &[(1,0),(-2,0),(1,-2),(-2,1)], N];
const KX: Kicks = [N, &[(-1,0),(-1,-1),(0,2),(-1,2)], &[(0,-1),(1,-1),(-1,-1),(1,0),(-1,0)],
    &[(1,0),(1,-1),(0,2),(1,2)], &[(1,0),(1,1),(0,-2),(1,-2)], N, &[(1,0),(1,1),(0,-2),(1,-2)],
    &[(1,0),(1,-2),(1,-1),(0,-2),(0,-1)], &[(0,1),(-1,1),(1,1),(-1,0),(1,0)],
    &[(-1,0),(-1,-1),(0,2),(-1,2)], N, &[(1,0),(1,-1),(0,2),(1,2)], &[(-1,0),(-1,1),(0,-2),(-1,-2)],
    &[(-1,0),(-1,-2),(-1,-1),(0,-2),(0,-1)], &[(-1,0),(-1,1),(0,-2),(-1,-2)], N];
/// the JS tables' `null` entries (a rotation with no kick set): ids 0, 5, 10, 15
fn kick_null(id: usize) -> bool { id % 5 == 0 }
const TC: [(i32, i32, usize, usize); 4] = [(-1,-1,3,0),(1,-1,0,1),(1,1,1,2),(-1,1,2,3)];

type Board = [[bool; 10]; 40];

#[derive(Clone, Copy)]
struct St { p: usize, x: i32, y: i32, r: usize, spin: u8 } // spin 0 none, 1 mini, 2 full

fn cells_of(p: usize, x: i32, y: i32, r: usize) -> [(i32, i32); 4] {
    let s = &STATES[p][r];
    [(x + s[0].0, y + s[0].1), (x + s[1].0, y + s[1].1), (x + s[2].0, y + s[2].1), (x + s[3].0, y + s[3].1)]
}
fn occupied(b: &Board, x: i32, y: i32) -> bool { x < 0 || x >= W || y < 0 || y >= H || b[y as usize][x as usize] }
fn legal(b: &Board, c: &[(i32, i32); 4]) -> bool { c.iter().all(|&(x, y)| !occupied(b, x, y)) }
fn spawn(b: &Board, p: usize) -> Option<St> {
    // Math.floor(W / 2 - WIDTH / 2)
    let x = ((W as f64) / 2.0 - (WIDTH[p] as f64) / 2.0).floor() as i32;
    let mut s = St { p, x, y: 17, r: 0, spin: 0 };
    if !legal(b, &cells_of(p, s.x, s.y, 0)) {
        s.y -= 1;
        if !legal(b, &cells_of(p, s.x, s.y, 0)) { return None; }
    }
    Some(s)
}
fn detect_spin(b: &Board, s: &St, tst: bool) -> u8 {
    if s.p != T_IDX { return 0; }
    if legal(b, &cells_of(s.p, s.x, s.y + 1, s.r)) { return 0; }
    let (mut corners, mut front) = (0, 0);
    for t in TC.iter() {
        if occupied(b, s.x + 1 + t.0, s.y + 1 + t.1) { corners += 1; if s.r == t.2 || s.r == t.3 { front += 1; } }
    }
    if corners < 3 { return 0; }
    if tst { return 2; }
    if front == 2 { 2 } else { 1 }
}
fn rotate(b: &Board, s: &St, amount: i32) -> Option<St> {
    let to = (((s.r as i32 + amount) % 4 + 4) % 4) as usize;
    let id = s.r * 4 + to;
    let (nx, ny, kick, used);
    if legal(b, &cells_of(s.p, s.x, s.y, to)) { nx = s.x; ny = s.y; kick = (0, 0); used = false; }
    else {
        if kick_null(id) { return None; }
        let set = if s.p == 0 { KI[id] } else { KX[id] };
        let mut hit = None;
        for &(dx, dy) in set.iter() {
            if legal(b, &cells_of(s.p, s.x + dx, s.y + dy, to)) { hit = Some((dx, dy)); break; }
        }
        match hit { Some((dx, dy)) => { nx = s.x + dx; ny = s.y + dy; kick = (dx, dy); used = true; } None => return None }
    }
    let tst = used && (((id == 11 || id == 3) && kick == (1, 2)) || ((id == 9 || id == 1) && kick == (-1, 2)));
    let mut n = St { p: s.p, x: nx, y: ny, r: to, spin: 0 };
    n.spin = detect_spin(b, &n, tst);
    Some(n)
}
fn shift(b: &Board, s: &St, dx: i32) -> Option<St> {
    if legal(b, &cells_of(s.p, s.x + dx, s.y, s.r)) { Some(St { x: s.x + dx, ..*s }) } else { None }
}
fn down(b: &Board, s: &St) -> Option<St> {
    if legal(b, &cells_of(s.p, s.x, s.y + 1, s.r)) { Some(St { y: s.y + 1, spin: 0, ..*s }) } else { None }
}
fn dropped(b: &Board, s: &St) -> St {
    let mut t = *s;
    while let Some(n) = down(b, &t) { t = n; }
    t
}
fn to_wall(b: &Board, s: &St, dx: i32) -> Option<St> {
    let mut t = *s;
    let mut moved = false;
    while let Some(n) = shift(b, &t, dx) { t = n; moved = true; }
    if moved { Some(t) } else { None }
}
fn cell_key(c: &[(i32, i32); 4]) -> [i32; 4] {
    let mut k = [c[0].1 * W + c[0].0, c[1].1 * W + c[1].0, c[2].1 * W + c[2].0, c[3].1 * W + c[3].0];
    k.sort();
    k
}

/// `placements(b, p)`: every resting placement, in the JS `Map`'s insertion order (first reach of each
/// (cells, spin)).
fn placements(b: &Board, p: usize) -> Vec<St> {
    let st = match spawn(b, p) { Some(s) => s, None => return vec![] };
    let mut seen: HashSet<(i32, i32, usize, u8)> = HashSet::new();
    let mut out_keys: HashSet<([i32; 4], u8)> = HashSet::new();
    let mut out: Vec<St> = vec![];
    let mut q: VecDeque<(St, usize)> = VecDeque::new();
    seen.insert((st.x, st.y, st.r, st.spin));
    q.push_back((st, 0));
    while let Some((s, plen)) = q.pop_front() {
        let d = dropped(b, &s);
        let fin = if d.y == s.y { s } else { d };
        if out_keys.insert((cell_key(&cells_of(fin.p, fin.x, fin.y, fin.r)), fin.spin)) { out.push(fin); }
        if plen > 12 { continue; } // `path.length > 12`, the moves so far
        for m in 0..8 {
            let n = match m {
                0 => shift(b, &s, -1),
                1 => shift(b, &s, 1),
                2 => to_wall(b, &s, -1),
                3 => to_wall(b, &s, 1),
                4 => rotate(b, &s, 1),
                5 => rotate(b, &s, -1),
                6 => rotate(b, &s, 2),
                _ => { let d = dropped(b, &s); if d.y != s.y { Some(d) } else { None } }
            };
            if let Some(n) = n {
                if seen.insert((n.x, n.y, n.r, n.spin)) { q.push_back((n, plen + 1)); }
            }
        }
    }
    out
}

struct Locked { board: Board, lines: usize, cleared: Vec<i32> }
fn lock(b: &Board, s: &St) -> Locked {
    let mut nb = *b;
    for (x, y) in cells_of(s.p, s.x, s.y, s.r) { nb[y as usize][x as usize] = true; }
    let cleared: Vec<i32> = (0..H).filter(|&y| nb[y as usize].iter().all(|&v| v)).collect();
    let mut out = [[false; 10]; 40];
    let mut at = 39i32;
    for y in (0..H).rev() { if cleared.contains(&y) { continue; } out[at as usize] = nb[y as usize]; at -= 1; }
    Locked { board: out, lines: cleared.len(), cleared }
}
fn add_garbage(b: &Board, n: i32, col: usize) -> Board {
    let mut nb = *b;
    for _ in 0..n {
        for y in 0..39 { nb[y] = nb[y + 1]; }
        nb[39] = [true; 10];
        nb[39][col] = false;
    }
    nb
}

/// t and cells are (r, c, ..); cell v: 0 '#', 1 '.', 2 'T'
struct Win { t: [(i32, i32); 4], cells: Vec<(i32, i32, u8)>, follow: Vec<(i32, i32)> }

/// `matchWindow` then `carry`: the first window whose T equals the cells under one translation and whose
/// cells read right decides, and findBuild keeps it only if its follow-up slot survives the clear.
fn build_ok(b: &Board, tcells: &[(i32, i32); 4], cleared: &[i32], wins: &[Win]) -> bool {
    let tk = cell_key(tcells);
    let miny = tcells.iter().map(|c| c.1).min().unwrap();
    let minx = tcells.iter().map(|c| c.0).min().unwrap();
    for w in wins {
        let dy = miny - w.t.iter().map(|t| t.0).min().unwrap();
        let dx = minx - w.t.iter().map(|t| t.1).min().unwrap();
        let mapped = [(w.t[0].1 + dx, w.t[0].0 + dy), (w.t[1].1 + dx, w.t[1].0 + dy),
                      (w.t[2].1 + dx, w.t[2].0 + dy), (w.t[3].1 + dx, w.t[3].0 + dy)];
        if cell_key(&mapped) != tk { continue; }
        let mut ok = true;
        for &(r, c, v) in &w.cells {
            let (x, y) = (c + dx, r + dy);
            if x < 0 || x >= W || y < 0 || y >= H { ok = false; break; }
            if v == 2 { continue; }
            let f = b[y as usize][x as usize];
            if (v == 0 && !f) || (v == 1 && f) { ok = false; break; }
        }
        if !ok { continue; }
        return w.follow.iter().all(|&(r, _)| !cleared.contains(&(r + dy)));
    }
    false
}
fn find_build(b: &Board, wins: &[Win]) -> bool {
    for s in placements(b, T_IDX) {
        if s.spin != 2 { continue; }
        let l = lock(b, &s);
        if l.lines != 2 { continue; }
        if build_ok(b, &cells_of(s.p, s.x, s.y, s.r), &l.cleared, wins) { return true; }
    }
    false
}
fn window_can_stand(b: &Board, wins: &[Win]) -> bool {
    for w in wins {
        let r0 = w.cells.iter().map(|q| q.0).min().unwrap();
        let r1 = w.cells.iter().map(|q| q.0).max().unwrap();
        let c0 = w.cells.iter().map(|q| q.1).min().unwrap();
        let c1 = w.cells.iter().map(|q| q.1).max().unwrap();
        let mut dy = -r0;
        while dy + r1 < H {
            let mut dx = -c0;
            while dx + c1 < W {
                if w.cells.iter().all(|&(r, c, v)| { let f = b[(r + dy) as usize][(c + dx) as usize]; if v == 0 { f } else { !f } }) { return true; }
                dx += 1;
            }
            dy += 1;
        }
    }
    false
}
fn buildable(b: &Board, wins: &[Win]) -> bool { window_can_stand(b, wins) && find_build(b, wins) }

struct Node { board: Board, qi: usize, hold: u8, locks: i32 }
const NO_HOLD: u8 = 255;

fn kids(n: &Node, queue: &[u8], events: &[(i32, i32, i32)]) -> Vec<Node> {
    let mut out = vec![];
    if n.qi >= queue.len() { return out; }
    let cur = queue[n.qi];
    let mut opts: Vec<(u8, u8, usize)> = vec![(cur, n.hold, n.qi + 1)];
    if n.hold == NO_HOLD { if let Some(&nx) = queue.get(n.qi + 1) { opts.push((nx, cur, n.qi + 2)); } }
    else if n.hold != cur { opts.push((n.hold, cur, n.qi + 1)); }
    for (p, h, qi) in opts {
        let mut seen: HashSet<[i32; 4]> = HashSet::new();
        for s in placements(&n.board, p as usize) {
            if !seen.insert(cell_key(&cells_of(s.p, s.x, s.y, s.r))) { continue; }
            let mut nb = lock(&n.board, &s).board;
            let locks = n.locks + 1;
            for &(before, cnt, col) in events { if before == locks { nb = add_garbage(&nb, cnt, col as usize); } }
            out.push(Node { board: nb, qi, hold: h, locks });
        }
    }
    out
}

fn parse_windows(w: &[i32]) -> Vec<Win> {
    let mut i = 0usize;
    let n = w[i]; i += 1;
    let mut out = vec![];
    for _ in 0..n {
        let mut t = [(0, 0); 4];
        for k in 0..4 { t[k] = (w[i], w[i + 1]); i += 2; }
        let nc = w[i] as usize; i += 1;
        let mut cells = vec![];
        for _ in 0..nc { cells.push((w[i], w[i + 1], w[i + 2] as u8)); i += 3; }
        let nf = w[i] as usize; i += 1;
        let mut follow = vec![];
        for _ in 0..nf { follow.push((w[i], w[i + 1])); i += 2; }
        out.push(Win { t, cells, follow });
    }
    out
}

/// board: 400 bytes (row-major, row 0 the top, nonzero filled) = `E.newRun(pz).board`; queue: pieces (0-6,
/// "IJLOSTZ"); hold: a piece or 255; events: `before, n, col` triples (garbage); windows: the flattened list
/// `parse_windows` reads. Returns d >= 0 (a build stands after d pieces), or `-1 - (beyond * 2 + cut)`.
///
/// # Safety
/// every pointer must address its stated number of elements.
#[no_mangle]
pub unsafe extern "C" fn cutcopy_min_need(board: *const u8, queue: *const u8, nq: u32, hold: u32, events: *const i32, ne: u32,
                                          windows: *const i32, nw: u32, cap: u32, frontier: u32) -> i32 {
    let raw = std::slice::from_raw_parts(board, 400);
    let mut b: Board = [[false; 10]; 40];
    for y in 0..40 { for x in 0..10 { b[y][x] = raw[y * 10 + x] != 0; } }
    let queue = std::slice::from_raw_parts(queue, nq as usize);
    let ev3: &[i32] = if ne == 0 { &[] } else { std::slice::from_raw_parts(events, ne as usize * 3) };
    let events: Vec<(i32, i32, i32)> = ev3.chunks(3).map(|c| (c[0], c[1], c[2])).collect();
    let wins = parse_windows(std::slice::from_raw_parts(windows, nw as usize));
    let mut lvl = vec![Node { board: b, qi: 0, hold: hold as u8, locks: 0 }];
    if buildable(&lvl[0].board, &wins) { return 0; }
    for d in 1..=cap {
        let mut nl: Vec<Node> = vec![];
        let mut seen: HashSet<(usize, u8, [u64; 7])> = HashSet::new();
        for s in &lvl {
            for k in kids(s, queue, &events) {
                let mut bits = [0u64; 7];
                for y in 0..40 { for x in 0..10 { if k.board[y][x] { let i = y * 10 + x; bits[i / 64] |= 1u64 << (i % 64); } } }
                if !seen.insert((k.qi, k.hold, bits)) { continue; }
                if buildable(&k.board, &wins) { return d as i32; }
                if d < cap { nl.push(k); }
            }
        }
        lvl = nl;
        if d < cap && lvl.len() > frontier as usize { return -1 - (d as i32 * 2 + 1); }
    }
    -1 - (cap as i32 * 2)
}

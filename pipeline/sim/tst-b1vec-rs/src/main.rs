//! Per-dealt-order bag-1 soft-drop vector of a T-placed or T-held bag-1 board (the new "families" figures).
//!
//! Reads `name#K:c,c,c,c/K:c,c,c,c/...` lines (six pieces, cell = y*10+x, y up from the floor) and prints one JSON object
//! per line, in input order: `{"name":..,"v":"<5040 chars>"}`. Character i is for the i-th dealt order of bag 1 in the
//! order `tst2bag-tp-rs` enumerates them (`perms()`: every permutation of IOTSZJL, built by removing the i-th remaining
//! kind in turn): '.' when no play of the order builds the board, else the least soft-drop cost, a digit.
//!
//! It reproduces the bag-1 phase of `tst2bag-tp-rs`'s `FCounter` (phase 0) and nothing else, rule for rule:
//!   * a piece is placed only where the engine's own search (`oracle_rs::reach::search`, SRS+ kicks, 180 allowed, spawn
//!     at the top, the O one column right) reaches exactly its cells on the board as it stands (earlier board pieces only);
//!   * its soft-drop cost is 1 when a filled cell lies above one of its cells in its column (rows below 12), else 0;
//!   * each dealt piece is placed, or held (empty hold: it goes in and the NEXT piece may only be placed — the `f` flag —
//!     otherwise swapped with the held piece, which is then placed);
//!   * after all seven pieces the six board pieces must all be down; the held piece is whatever is left.
//! The counter keeps every (state, soft-drop) pair; a larger soft-drop total only removes options later, so the least
//! total is the whole content of the phase. `tst-openers-tp-b1.json`'s emitter checks that identity against the counter's
//! own cumulative counts (every division exact) and the test against the pinned binary (`MULTI=1 B1ONLY=1 SDB=n`).
use oracle_rs::reach;
use std::collections::HashMap;
use std::io::{BufRead, Write};

const K: &[u8] = b"IOTSZJL"; // kind code = index+1, as the counter's
const REACH: &[u8] = b"ijlostz";
const INF: u8 = 255;

fn sym_of(k: u8) -> usize { REACH.iter().position(|&c| c == k.to_ascii_lowercase()).expect("piece kind") }
fn bits(cs: &[u16; 4]) -> u128 { cs.iter().fold(0u128, |a, &c| a | 1u128 << c) }

struct Reach { cache: HashMap<(usize, u128), Vec<[u16; 4]>> }
impl Reach {
    fn get(&mut self, occ: u128, sym: usize) -> &Vec<[u16; 4]> {
        self.cache.entry((sym, occ)).or_insert_with(|| {
            let mut b = [[false; 10]; 40];
            for i in 0..128 { if occ >> i & 1 == 1 { b[i / 10][i % 10] = true; } }
            let start = if REACH[sym] == b'o' { (4.0, 22.04, 0) } else { (3.0, 22.04, 0) };
            reach::search(&b, sym, start, false).into_iter().map(|f| f.cells).collect()
        })
    }
}

fn sd_cost(occ: u128, c: &[u16; 4]) -> u8 {
    for &cc in c { let x = cc % 10; let mut y = cc / 10 + 1; while y < 12 { let k = y * 10 + x; if occ >> k & 1 == 1 && !c.contains(&k) { return 1; } y += 1; } }
    0
}

fn perms() -> Vec<Vec<u8>> {
    let mut out = vec![];
    fn r(p: &mut Vec<u8>, rest: &mut Vec<u8>, out: &mut Vec<Vec<u8>>) {
        if rest.is_empty() { out.push(p.clone()); return; }
        for i in 0..rest.len() { let c = rest.remove(i); p.push(c); r(p, rest, out); p.pop(); rest.insert(i, c); }
    }
    r(&mut vec![], &mut b"IOTSZJL".to_vec(), &mut out);
    out
}

/// edge[mask][piece] = Some(cost) when board piece `piece` can be placed on the board holding `mask`.
fn edges(ps: &[(u8, [u16; 4])], rc: &mut Reach) -> Vec<Vec<Option<u8>>> {
    let n = ps.len();
    let mut e = vec![vec![None; n]; 1 << n];
    for m in 0..(1u32 << n) {
        let occ = (0..n).filter(|&i| m >> i & 1 == 1).fold(0u128, |a, i| a | bits(&ps[i].1));
        for i in 0..n {
            if m >> i & 1 == 1 { continue; }
            if rc.get(occ, sym_of(ps[i].0)).iter().any(|c| *c == ps[i].1) { e[m as usize][i] = Some(sd_cost(occ, &ps[i].1)); }
        }
    }
    e
}

fn vector(ps: &[(u8, [u16; 4])], rc: &mut Reach, pm: &[Vec<u8>]) -> String {
    let n = ps.len();
    assert!(n == 6, "a bag-1 board has six pieces");
    let e = edges(ps, rc);
    let idx: Vec<Option<usize>> = K.iter().map(|&k| ps.iter().position(|p| p.0 == k)).collect(); // by kind index
    let full = (1usize << n) - 1;
    // state index: mask (6 bits) * 16 + hold (0 none, 1..=7 kind code) * 2 + f
    let sz = (1usize << n) * 16;
    let mut out = String::with_capacity(pm.len());
    for order in pm {
        let mut cur = vec![INF; sz];
        cur[0] = 0;
        for &kc in order {
            let c = K.iter().position(|&k| k == kc).unwrap(); // kind index 0..7
            let mut nx = vec![INF; sz];
            let put = |nx: &mut Vec<u8>, m: usize, h: usize, f: usize, s: u8| { let i = m * 16 + h * 2 + f; if s < nx[i] { nx[i] = s; } };
            for m in 0..=full { for h in 0..8usize { for f in 0..2usize {
                let s = cur[m * 16 + h * 2 + f];
                if s == INF { continue; }
                if let Some(pi) = idx[c] { if let Some(cost) = e[m][pi] { put(&mut nx, m | 1 << pi, h, 0, s + cost); } }
                if f == 1 { continue; }
                if h == 0 { put(&mut nx, m, c + 1, 1, s); }
                else if let Some(pi) = idx[h - 1] { if let Some(cost) = e[m][pi] { put(&mut nx, m | 1 << pi, c + 1, 0, s + cost); } }
            }}}
            cur = nx;
        }
        let mut best = INF;
        for h in 0..8 { for f in 0..2 { best = best.min(cur[full * 16 + h * 2 + f]); } }
        out.push(if best == INF { '.' } else { (b'0' + best) as char });
    }
    out
}

fn pieces(s: &str) -> Vec<(u8, [u16; 4])> {
    s.split('/').filter(|x| !x.is_empty()).map(|p| {
        let (k, cs) = p.split_once(':').expect("K:cells");
        let mut v: Vec<u16> = cs.split(',').map(|c| c.parse().unwrap()).collect();
        v.sort();
        assert!(v.len() == 4 && v[3] < 128, "piece cells");
        (k.as_bytes()[0], [v[0], v[1], v[2], v[3]])
    }).collect()
}

fn main() {
    let pm = perms();
    let mut rc = Reach { cache: HashMap::new() };
    let so = std::io::stdout(); let mut so = so.lock();
    for l in std::io::stdin().lock().lines() {
        let l = l.unwrap(); if l.is_empty() { continue; }
        let (name, rest) = l.split_once('#').expect("name#pieces");
        let v = vector(&pieces(rest), &mut rc, &pm);
        writeln!(so, "{{\"name\":{:?},\"v\":\"{}\"}}", name, v).unwrap();
        if rc.cache.len() > 400_000 { rc.cache.clear(); }
    }
}

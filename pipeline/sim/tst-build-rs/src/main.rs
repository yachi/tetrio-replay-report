//! One engine-checked placement order per leftover class of docs/tst-openers.html's cards.
//!
//! Reads `id|bag1|bag2|tst` lines: `bag1` and `bag2` are `K:c,c,c,c;...` pieces (cell = y*10+x, y up from the floor),
//! `tst` the four cells of the stood T. Prints one JSON object per line, in input order:
//! `{"id":..,"order":[[K,[c,c,c,c],sd],...],"sd":n,"tst":bool}`, or `"order":null` when no order exists.
//!
//! The order places every bag-1 piece before any bag-2 piece; each step's cells must be a resting placement the vendored
//! engine's own search (`oracle_rs::reach::search`, SRS+ kicks, 180 allowed, spawn at the top) reaches on the board as it
//! stands. `sd` is the counter's soft-drop cost (`tst2bag-tp-rs`): 1 when a filled cell lies above one of the piece's cells
//! in its column. The order minimises the total, then takes the lowest-indexed piece at each step (pieces sorted bag 1
//! first, then by their lowest cell). `tst` is whether the T then reaches the TST cells with a full spin.
//!
//! With `NO180=1` the engine's search drops the 180 rotation (every mode).
//! With `PERMS=1` it prints the 5040 dealt orders, one per line, in the index order `ORDERS=1` uses, and reads nothing.
//! With `ORDERS=1` it prints instead `{"id":..,"v":"<5040 chars>"}`: for each dealt order of bag 2 (the i-th permutation of
//! IOTSZJL in the order `tst2bag-tp-rs`'s `perms()` builds them), the least bag-2 soft-drop cost with which a player with
//! one hold slot builds THIS tiling and fires the TST, as a digit capped at 9, or '.' when no play does. The play follows
//! `tst2bag-tp-rs`'s `FCounter` restricted to the one tiling: bag 1 stands on the board, the hold holds the kind bag 1 left
//! out, and each dealt piece is placed, held (hold empty) or swapped with the held one (once per piece); the order wins when
//! the tiling is full and a T comes out (dealt or swapped) with the TST open, or when all seven are dealt, the tiling is full
//! and the T is held.
use oracle_rs::reach;
use std::collections::HashMap;
use std::io::{BufRead, Write};

const REACH: &[u8] = b"ijlostz";
fn sym_of(k: u8) -> usize { REACH.iter().position(|&c| c == k.to_ascii_lowercase()).expect("piece kind") }
fn bits(cs: &[u16; 4]) -> u128 { cs.iter().fold(0u128, |a, &c| a | 1u128 << c) }

struct Reach { cache: HashMap<(usize, u128), Vec<([u16; 4], u8)>>, no180: bool }
impl Reach {
    fn get(&mut self, occ: u128, sym: usize) -> &Vec<([u16; 4], u8)> {
        let no180 = self.no180;
        self.cache.entry((sym, occ)).or_insert_with(|| {
            let mut b = [[false; 10]; 40];
            for i in 0..128 { if occ >> i & 1 == 1 { b[i / 10][i % 10] = true; } }
            let start = if REACH[sym] == b'o' { (4.0, 22.04, 0) } else { (3.0, 22.04, 0) };
            reach::search(&b, sym, start, no180).into_iter().map(|f| (f.cells, f.spin)).collect()
        })
    }
}

fn pieces(s: &str) -> Vec<(u8, [u16; 4])> {
    s.split(';').filter(|x| !x.is_empty()).map(|p| {
        let (k, cs) = p.split_once(':').expect("K:cells");
        let mut v: Vec<u16> = cs.split(',').map(|c| c.parse().unwrap()).collect();
        v.sort();
        assert!(v.len() == 4 && v[3] < 128, "piece cells");
        (k.as_bytes()[0], [v[0], v[1], v[2], v[3]])
    }).collect()
}

fn sd_cost(occ: u128, c: &[u16; 4]) -> u32 {
    for &cc in c { let x = cc % 10; let mut y = cc / 10 + 1; while y < 12 { let k = y * 10 + x; if occ >> k & 1 == 1 && !c.contains(&k) { return 1; } y += 1; } }
    0
}

fn solve(b1: &[(u8, [u16; 4])], b2: &[(u8, [u16; 4])], tst: &[u16; 4], rc: &mut Reach) -> (Option<Vec<(u8, [u16; 4], u32)>>, u32, bool) {
    let mut ps: Vec<(u8, [u16; 4], u8)> = b1.iter().map(|p| (p.0, p.1, 0)).chain(b2.iter().map(|p| (p.0, p.1, 1))).collect();
    ps.sort_by_key(|p| (p.2, p.1[0], p.1));
    let n = ps.len(); let full = (1u32 << n) - 1;
    let b1m: u32 = (0..n).filter(|&i| ps[i].2 == 0).fold(0, |a, i| a | 1 << i);
    let occ = |m: u32| (0..n).filter(|&i| m >> i & 1 == 1).fold(0u128, |a, i| a | bits(&ps[i].1));
    const INF: u32 = u32::MAX;
    let mut best = vec![INF; 1 << n];
    let fo = occ(full);
    let tst_ok = rc.get(fo, sym_of(b'T')).iter().any(|f| f.0 == *tst && f.1 == 2);
    best[full as usize] = 0;
    // moves out of m, in piece order: (i, cost)
    let mut mv: Vec<Vec<(usize, u32)>> = vec![vec![]; 1 << n];
    for m in (0..full).rev() {
        let o = occ(m);
        for i in 0..n {
            if m >> i & 1 == 1 { continue; }
            if ps[i].2 == 1 && m & b1m != b1m { continue; }
            let m2 = m | 1 << i;
            if best[m2 as usize] == INF { continue; }
            if !rc.get(o, sym_of(ps[i].0)).iter().any(|f| f.0 == ps[i].1) { continue; }
            let c = sd_cost(o, &ps[i].1);
            mv[m as usize].push((i, c));
            best[m as usize] = best[m as usize].min(c + best[m2 as usize]);
        }
    }
    if best[0] == INF { return (None, 0, tst_ok); }
    let mut m = 0u32; let mut out = vec![];
    while m != full {
        let &(i, c) = mv[m as usize].iter().find(|&&(i, c)| c + best[(m | 1 << i) as usize] == best[m as usize]).unwrap();
        out.push((ps[i].0, ps[i].1, c));
        m |= 1 << i;
    }
    (Some(out), best[0], tst_ok)
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

/// The per-dealt-order bag-2 cost string of `ORDERS=1` (see the module docs).
fn orders(b1: &[(u8, [u16; 4])], b2: &[(u8, [u16; 4])], tst: &[u16; 4], pm: &[Vec<u8>], rc: &mut Reach) -> String {
    let n = b2.len(); let full = (1u32 << n) - 1;
    let base = b1.iter().fold(0u128, |a, p| a | bits(&p.1));
    let occ = |m: u32| (0..n).filter(|&i| m >> i & 1 == 1).fold(base, |a, i| a | bits(&b2[i].1));
    let tst_ok = rc.get(occ(full), sym_of(b'T')).iter().any(|f| f.0 == *tst && f.1 == 2);
    if !tst_ok { return ".".repeat(pm.len()); }
    let mut left: Vec<u8> = b"IJLOSTZ".iter().cloned().filter(|k| !b1.iter().any(|p| p.0 == *k)).collect();
    assert!(left.len() == 1, "bag 1 leaves exactly one kind out");
    let h0 = left.pop().unwrap();
    // edge[m][i]: the soft-drop cost of placing b2[i] on bag 1 plus the pieces in m
    let mut edge: Vec<Vec<Option<u8>>> = vec![vec![None; n]; 1 << n];
    for m in 0..=full {
        let o = occ(m);
        for i in 0..n {
            if m >> i & 1 == 1 { continue; }
            if rc.get(o, sym_of(b2[i].0)).iter().any(|f| f.0 == b2[i].1) { edge[m as usize][i] = Some(sd_cost(o, &b2[i].1) as u8); }
        }
    }
    let mut out = String::with_capacity(pm.len());
    for order in pm {
        // state (mask, hold, used) -> least cost
        let mut st: HashMap<(u32, u8, bool), u8> = HashMap::new();
        st.insert((0, h0, false), 0);
        let mut best = u8::MAX;
        for &c in order {
            let mut nx: HashMap<(u32, u8, bool), u8> = HashMap::new();
            let mut put = |k: (u32, u8, bool), v: u8| { let e = nx.entry(k).or_insert(u8::MAX); if v < *e { *e = v; } };
            for (&(m, h, f), &cost) in &st {
                // place `p` out of state m at cost; a T coming out onto a full tiling fires the TST
                let place = |p: u8, h2: u8, out: &mut dyn FnMut((u32, u8, bool), u8), best: &mut u8| {
                    if m == full && p == b'T' { *best = (*best).min(cost); return; }
                    for i in 0..n { if b2[i].0 == p { if let Some(sd) = edge[m as usize][i] { out((m | 1 << i, h2, false), cost + sd); } } }
                };
                place(c, h, &mut put, &mut best);
                if f { continue; }
                if h == 0 { put((m, c, true), cost); } else { place(h, c, &mut put, &mut best); }
            }
            st = nx;
        }
        for (&(m, h, _), &cost) in &st { if m == full && h == b'T' { best = best.min(cost); } }
        out.push(if best == u8::MAX { '.' } else { (b'0' + best.min(9)) as char });
    }
    out
}

fn main() {
    let mut rc = Reach { cache: HashMap::new(), no180: std::env::var("NO180").is_ok() };
    let ord = std::env::var("ORDERS").is_ok();
    let pm = perms();
    let so = std::io::stdout(); let mut so = so.lock();
    if std::env::var("PERMS").is_ok() {
        for p in &pm { writeln!(so, "{}", String::from_utf8_lossy(p)).unwrap(); }
        return;
    }
    for l in std::io::stdin().lock().lines() {
        let l = l.unwrap(); if l.is_empty() { continue; }
        let f: Vec<&str> = l.split('|').collect();
        assert!(f.len() == 4, "id|bag1|bag2|tst");
        let t: Vec<u16> = f[3].split(',').map(|c| c.parse().unwrap()).collect();
        let mut tst = [t[0], t[1], t[2], t[3]]; tst.sort();
        if ord {
            writeln!(so, "{{\"id\":{:?},\"v\":\"{}\"}}", f[0], orders(&pieces(f[1]), &pieces(f[2]), &tst, &pm, &mut rc)).unwrap();
            if rc.cache.len() > 200_000 { rc.cache.clear(); }
            continue;
        }
        let (o, sd, ok) = solve(&pieces(f[1]), &pieces(f[2]), &tst, &mut rc);
        let order = match o {
            None => "null".to_string(),
            Some(v) => format!("[{}]", v.iter().map(|(k, c, s)| format!("[\"{}\",[{},{},{},{}],{}]", *k as char, c[0], c[1], c[2], c[3], s)).collect::<Vec<_>>().join(",")),
        };
        writeln!(so, "{{\"id\":{:?},\"order\":{},\"sd\":{},\"tst\":{}}}", f[0], order, sd, ok).unwrap();
        if rc.cache.len() > 200_000 { rc.cache.clear(); }
    }
}

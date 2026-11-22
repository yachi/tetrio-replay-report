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
use oracle_rs::reach;
use std::collections::HashMap;
use std::io::{BufRead, Write};

const REACH: &[u8] = b"ijlostz";
fn sym_of(k: u8) -> usize { REACH.iter().position(|&c| c == k.to_ascii_lowercase()).expect("piece kind") }
fn bits(cs: &[u16; 4]) -> u128 { cs.iter().fold(0u128, |a, &c| a | 1u128 << c) }

struct Reach { cache: HashMap<(usize, u128), Vec<([u16; 4], u8)>> }
impl Reach {
    fn get(&mut self, occ: u128, sym: usize) -> &Vec<([u16; 4], u8)> {
        self.cache.entry((sym, occ)).or_insert_with(|| {
            let mut b = [[false; 10]; 40];
            for i in 0..128 { if occ >> i & 1 == 1 { b[i / 10][i % 10] = true; } }
            let start = if REACH[sym] == b'o' { (4.0, 22.04, 0) } else { (3.0, 22.04, 0) };
            reach::search(&b, sym, start, false).into_iter().map(|f| (f.cells, f.spin)).collect()
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

fn main() {
    let mut rc = Reach { cache: HashMap::new() };
    let so = std::io::stdout(); let mut so = so.lock();
    for l in std::io::stdin().lock().lines() {
        let l = l.unwrap(); if l.is_empty() { continue; }
        let f: Vec<&str> = l.split('|').collect();
        assert!(f.len() == 4, "id|bag1|bag2|tst");
        let t: Vec<u16> = f[3].split(',').map(|c| c.parse().unwrap()).collect();
        let mut tst = [t[0], t[1], t[2], t[3]]; tst.sort();
        let (o, sd, ok) = solve(&pieces(f[1]), &pieces(f[2]), &tst, &mut rc);
        let order = match o {
            None => "null".to_string(),
            Some(v) => format!("[{}]", v.iter().map(|(k, c, s)| format!("[\"{}\",[{},{},{},{}],{}]", *k as char, c[0], c[1], c[2], c[3], s)).collect::<Vec<_>>().join(",")),
        };
        writeln!(so, "{{\"id\":{:?},\"order\":{},\"sd\":{},\"tst\":{}}}", f[0], order, sd, ok).unwrap();
        if rc.cache.len() > 200_000 { rc.cache.clear(); }
    }
}

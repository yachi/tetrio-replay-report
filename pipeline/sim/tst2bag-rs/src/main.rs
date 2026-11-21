//! 2-bag TST shape enumerator: tilings, engine-reachability DAG (oracle-rs reach, 180 on),
//! hold-aware 2-bag success count (modes A: shape built; B: shape built and a T available for the TST),
//! and the bag-3 PC rate of the residue (pc-solver-rs, engine movegen, maxH 5, 2e6 nodes).
//! Input lines: name|x,y;x,y;...|x,y;x,y;x,y;x,y   (y=0 bottom). Output: one JSON object per line.
use std::collections::HashMap;
use std::io::{BufRead, Write};
use oracle_rs::reach;
use pc_solver_rs::solver::{check, Gen, Memo, Verdict, NONE};

const K: &[u8] = b"IOTSZJL"; // kind code = index+1, T=3
const REACH: &[u8] = b"ijlostz";
const T: u8 = 3;
const FACT: [u64; 8] = [1, 1, 2, 6, 24, 120, 720, 5040];

fn shapes(k: u8) -> Vec<(i32, i32)> {
    match k { b'I' => vec![(0,0),(1,0),(2,0),(3,0)], b'O' => vec![(0,0),(1,0),(0,1),(1,1)], b'T' => vec![(0,0),(1,0),(2,0),(1,1)],
      b'S' => vec![(0,0),(1,0),(1,1),(2,1)], b'Z' => vec![(1,0),(2,0),(0,1),(1,1)], b'J' => vec![(0,0),(1,0),(2,0),(0,1)], _ => vec![(0,0),(1,0),(2,0),(2,1)] }
}
fn rots(k: u8) -> Vec<Vec<(i32, i32)>> {
    let mut out: Vec<Vec<(i32,i32)>> = vec![]; let mut s = shapes(k);
    for _ in 0..4 {
        let mx = s.iter().map(|p| p.0).min().unwrap(); let my = s.iter().map(|p| p.1).min().unwrap();
        let mut n: Vec<(i32,i32)> = s.iter().map(|p| (p.0-mx, p.1-my)).collect(); n.sort();
        if !out.contains(&n) { out.push(n); }
        s = s.iter().map(|p| (p.1, -p.0)).collect();
    }
    out
}
type Pl = (u8, Vec<u16>); // kind letter, sorted cells y*10+x
fn tile(cells: &[(i32,i32)], lim: &HashMap<u8,u32>) -> Vec<Vec<Pl>> {
    let set: std::collections::HashSet<(i32,i32)> = cells.iter().cloned().collect();
    let mut pl: Vec<Pl> = vec![];
    for &k in b"IJLOSTZ" { for r in rots(k) { for &(ax,ay) in cells { for &(dx,dy) in &r {
        let (ox,oy) = (ax-dx, ay-dy); let c: Vec<(i32,i32)> = r.iter().map(|p| (ox+p.0, oy+p.1)).collect();
        if c.iter().all(|p| set.contains(p)) { let mut v: Vec<u16> = c.iter().map(|p| (p.1*10+p.0) as u16).collect(); v.sort(); pl.push((k, v)); }
    }}}}
    pl.sort(); pl.dedup();
    let mut by: HashMap<u16, Vec<usize>> = HashMap::new();
    for (i,p) in pl.iter().enumerate() { for &c in &p.1 { by.entry(c).or_default().push(i); } }
    let mut order: Vec<u16> = cells.iter().map(|p| (p.1*10+p.0) as u16).collect(); order.sort(); // (y,x) order == index order
    let mut sols = vec![]; let mut used = vec![]; let mut cov = std::collections::HashSet::new(); let mut cnt: HashMap<u8,u32> = HashMap::new();
    fn rec(order:&[u16], pl:&[Pl], by:&HashMap<u16,Vec<usize>>, lim:&HashMap<u8,u32>, cov:&mut std::collections::HashSet<u16>, used:&mut Vec<usize>, cnt:&mut HashMap<u8,u32>, sols:&mut Vec<Vec<Pl>>) {
        let Some(&c) = order.iter().find(|c| !cov.contains(c)) else { sols.push(used.iter().map(|&i| pl[i].clone()).collect()); return; };
        for &i in by.get(&c).map(|v| v.as_slice()).unwrap_or(&[]) {
            let p = &pl[i];
            if p.1.iter().any(|q| cov.contains(q)) || *cnt.get(&p.0).unwrap_or(&0) >= lim[&p.0] { continue; }
            *cnt.entry(p.0).or_default() += 1; used.push(i); for &q in &p.1 { cov.insert(q); }
            rec(order, pl, by, lim, cov, used, cnt, sols);
            for &q in &p.1 { cov.remove(&q); } used.pop(); *cnt.get_mut(&p.0).unwrap() -= 1;
        }
    }
    rec(&order, &pl, &by, lim, &mut cov, &mut used, &mut cnt, &mut sols);
    sols
}

struct Reach { cache: HashMap<(usize, u128), Vec<([u16;4], u8)>> }
impl Reach {
    fn get(&mut self, occ: u128, sym: usize) -> &Vec<([u16;4],u8)> {
        self.cache.entry((sym, occ)).or_insert_with(|| {
            let mut b = [[false; 10]; 40];
            for i in 0..128 { if occ >> i & 1 == 1 { b[i/10][i%10] = true; } }
            let start = if REACH[sym] == b'o' { (4.0, 22.04, 0) } else { (3.0, 22.04, 0) };
            reach::search(&b, sym, start, false).into_iter().map(|f| (f.cells, f.spin)).collect()
        })
    }
}
fn sym_of(k: u8) -> usize { REACH.iter().position(|&c| c == k.to_ascii_lowercase()).unwrap() }
fn bits(cs: &[u16]) -> u128 { cs.iter().fold(0u128, |a, &c| a | 1u128 << c) }

struct Dag { n: usize, kind: Vec<u8>, edges: HashMap<u32, Vec<usize>>, full: bool, tst_ok: bool }
fn dag(t: &[Pl], tst: &[u16;4], rc: &mut Reach) -> Dag {
    let n = t.len(); let full_m = (1u32 << n) - 1;
    let occ_of = |m: u32| -> u128 { let mut o = 0; for i in 0..n { if m >> i & 1 == 1 { o |= bits(&t[i].1); } } o };
    let mut edges = HashMap::new(); let mut seen = std::collections::HashSet::new(); seen.insert(0u32);
    let mut q = std::collections::VecDeque::new(); q.push_back(0u32);
    while let Some(m) = q.pop_front() {
        let occ = occ_of(m); let mut e = vec![];
        for i in 0..n { if m >> i & 1 == 0 {
            let want: [u16;4] = [t[i].1[0], t[i].1[1], t[i].1[2], t[i].1[3]];
            if rc.get(occ, sym_of(t[i].0)).iter().any(|f| f.0 == want) { e.push(i); let m2 = m | 1 << i; if seen.insert(m2) { q.push_back(m2); } }
        }}
        edges.insert(m, e);
    }
    let full = seen.contains(&full_m);
    let tst_ok = full && rc.get(occ_of(full_m), sym_of(b'T')).iter().any(|f| f.0 == *tst && f.1 == 2);
    Dag { n, kind: t.iter().map(|p| K.iter().position(|&c| c == p.0).unwrap() as u8 + 1).collect(), edges, full, tst_ok }
}

// state: f<<20 | h<<17 | m
fn enc(m: u32, h: u32, f: u32) -> u32 { f << 20 | h << 17 | m }
struct Counter<'a> { d: &'a Dag, mode_b: bool, memo: HashMap<Vec<u32>, u64> }
enum Step { Win, S(Vec<u32>) }
impl<'a> Counter<'a> {
    fn full(&self) -> u32 { (1u32 << self.d.n) - 1 }
    fn place(&self, m: u32, c: u8, out: &mut Vec<u32>) -> bool {
        if m == self.full() { return self.mode_b && c == T && self.d.tst_ok; }
        if let Some(e) = self.d.edges.get(&m) { for &i in e { if self.d.kind[i] == c { out.push(m | 1 << i); } } }
        false
    }
    fn step(&self, st: &[u32], c: u8) -> Step {
        let mut res: Vec<u32> = vec![]; let mut tmp = vec![];
        for &s in st {
            let f = s >> 20 & 1; let h = s >> 17 & 7; let m = s & 0x1ffff;
            tmp.clear(); if self.place(m, c, &mut tmp) { return Step::Win; }
            for &m2 in &tmp { res.push(enc(m2, h, 0)); }
            if f == 1 { continue; }
            if h == 0 { res.push(enc(m, c as u32, 1)); }
            else { tmp.clear(); if self.place(m, h as u8, &mut tmp) { return Step::Win; } for &m2 in &tmp { res.push(enc(m2, c as u32, 0)); } }
        }
        if !self.mode_b && res.iter().any(|&s| s & 0x1ffff == self.full()) { return Step::Win; }
        res.sort_unstable(); res.dedup(); Step::S(res)
    }
    fn final_ok(&self, st: &[u32]) -> bool {
        st.iter().any(|&s| { let h = s >> 17 & 7; let m = s & 0x1ffff; m == self.full() && (!self.mode_b || (h == T as u32 && self.d.tst_ok)) })
    }
    fn rec(&mut self, st: Vec<u32>, r: u32, phase: u32) -> u64 {
        if r == 0 { if phase == 0 { return self.rec(st, 127, 1); } return self.final_ok(&st) as u64; }
        let mut key = st.clone(); key.push(phase << 8 | r);
        if let Some(&v) = self.memo.get(&key) { return v; }
        let rem = r.count_ones() as usize; let mut tot = 0;
        for i in 0..7 { if r >> i & 1 == 1 {
            match self.step(&st, i as u8 + 1) {
                Step::Win => tot += FACT[rem-1] * if phase == 0 { 5040 } else { 1 },
                Step::S(v) => if !v.is_empty() { tot += self.rec(v, r & !(1 << i), phase); }
            }
        }}
        self.memo.insert(key, tot); tot
    }
}
fn count(d: &Dag, mode_b: bool) -> u64 { if !d.full { return 0; } let mut c = Counter { d, mode_b, memo: HashMap::new() }; c.rec(vec![enc(0,0,0)], 127, 0) }

fn perms() -> Vec<Vec<u8>> { let mut out = vec![]; fn r(p: &mut Vec<u8>, rest: &mut Vec<u8>, out: &mut Vec<Vec<u8>>) { if rest.is_empty() { out.push(p.clone()); return; } for i in 0..rest.len() { let c = rest.remove(i); p.push(c); r(p, rest, out); p.pop(); rest.insert(i, c); } } r(&mut vec![], &mut b"IOTSZJL".to_vec(), &mut out); out }

fn residue(shape: &[u16], tst: &[u16;4]) -> Vec<u16> {
    let all: std::collections::HashSet<u16> = shape.iter().chain(tst.iter()).cloned().collect();
    let mut rows = vec![];
    for y in 0..12u16 { let r: u16 = (0..10).filter(|x| all.contains(&(y*10+x))).fold(0, |a, x| a | 1 << x); if r != 0x3ff { rows.push(r); } }
    while rows.last() == Some(&0) { rows.pop(); }
    rows
}
fn pc_rate(rows: &[u16], left: &[u8], ps: &[Vec<u8>]) -> (u32, u32) {
    let (mut ok, mut unk) = (0, 0);
    for b in ps {
        let (cur, hold, seq): (u8, u8, Vec<u8>) = match left.len() {
            0 => (b[0], NONE, b[1..].to_vec()), 1 => (left[0], NONE, b.clone()), 2 => (left[0], left[1], b.clone()),
            _ => { let mut s = left[2..].to_vec(); s.extend(b); (left[0], left[1], s) }
        };
        let mut memo = Memo::default();
        match check(rows, cur, hold, &seq, 0, &mut memo, 5, 2_000_000, Gen::Engine) { Verdict::Ok{..} => ok += 1, Verdict::Short => unk += 1, Verdict::False => {} }
    }
    (ok, unk)
}

fn run(line: &str, ps: &[Vec<u8>], pcmemo: &mut HashMap<(Vec<u16>, Vec<u8>), (u32,u32)>) -> String {
    let mut parts = line.split('|');
    let name = parts.next().unwrap();
    let parse = |s: &str| -> Vec<(i32,i32)> { s.split(';').map(|p| { let mut q = p.split(','); (q.next().unwrap().parse().unwrap(), q.next().unwrap().parse().unwrap()) }).collect() };
    let cells = parse(parts.next().unwrap()); let tstv = parse(parts.next().unwrap());
    let mut tst = [0u16;4]; for i in 0..4 { tst[i] = (tstv[i].1*10+tstv[i].0) as u16; } tst.sort();
    let lim: HashMap<u8,u32> = b"IJLOSZ".iter().map(|&k| (k,2)).chain([(b'T',1)]).collect();
    let tils = tile(&cells, &lim);
    let shape: Vec<u16> = cells.iter().map(|p| (p.1*10+p.0) as u16).collect();
    let rows = residue(&shape, &tst);
    let mut rc = Reach { cache: HashMap::new() };
    let mut out = vec![];
    for (ti, t) in tils.iter().enumerate() {
        let d = dag(t, &tst, &mut rc);
        let (a, b) = if d.full { (count(&d, false), count(&d, true)) } else { (0, 0) };
        let mut left: Vec<u8> = vec![];
        for &k in b"IJLOSTZ" { let used = t.iter().filter(|p| p.0 == k).count() as i32 + if k == b'T' { 1 } else { 0 }; for _ in used..2 { left.push(k); } }
        let p = if b > 0 { *pcmemo.entry((rows.clone(), left.clone())).or_insert_with(|| pc_rate(&rows, &left, ps)) } else { (0, 0) };
        let pieces: Vec<String> = t.iter().map(|p| format!("[\"{}\",[{}]]", p.0 as char, p.1.iter().map(|c| c.to_string()).collect::<Vec<_>>().join(","))).collect();
        out.push(format!("{{\"id\":{},\"full\":{},\"tst\":{},\"A\":{},\"B\":{},\"left\":\"{}\",\"p5\":{},\"p5u\":{},\"pieces\":[{}]}}", ti, d.full, d.tst_ok, a, b, String::from_utf8(left).unwrap(), p.0, p.1, pieces.join(",")));
    }
    format!("{{\"name\":\"{}\",\"ntil\":{},\"rows\":[{}],\"til\":[{}]}}", name, tils.len(), rows.iter().map(|r| r.to_string()).collect::<Vec<_>>().join(","), out.join(","))
}

fn main() {
    let lines: Vec<String> = std::io::stdin().lock().lines().map(|l| l.unwrap()).filter(|l| !l.is_empty()).collect();
    let nt: usize = std::env::var("JOBS").ok().and_then(|s| s.parse().ok()).unwrap_or(4);
    let ps = std::sync::Arc::new(perms());
    let lines = std::sync::Arc::new(lines);
    let next = std::sync::Arc::new(std::sync::atomic::AtomicUsize::new(0));
    let (tx, rx) = std::sync::mpsc::channel();
    for _ in 0..nt { let (ps, lines, next, tx) = (ps.clone(), lines.clone(), next.clone(), tx.clone()); std::thread::spawn(move || {
        let mut pcm = HashMap::new();
        loop { let i = next.fetch_add(1, std::sync::atomic::Ordering::SeqCst); if i >= lines.len() { break; }
            let t0 = std::time::Instant::now(); let s = run(&lines[i], &ps, &mut pcm);
            eprintln!("{} done in {:?}", lines[i].split('|').next().unwrap(), t0.elapsed()); tx.send(s).unwrap(); }
    }); }
    drop(tx);
    let so = std::io::stdout(); let mut so = so.lock();
    for s in rx { writeln!(so, "{}", s).unwrap(); so.flush().unwrap(); }
}

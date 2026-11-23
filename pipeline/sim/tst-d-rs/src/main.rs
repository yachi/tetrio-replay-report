//! One-pass bag-2 counter (`tst-d`). Input: one MULTI line per bag-1 board (the format of `tst2bag-tp`'s MULTI=1:
//! `name#K:c,c,c,c/...#cells|tst|..#...#sid:left;...`). Output, in input order, one JSON line
//! `{"name":..,"ntil":N,"D":[[per class],[..],[..],[..]]}` (`"D":null` if no tiling holds the board): D[b][k] = number of the
//! 5040 dealt bag-2 orders that, from the end-of-bag-1 state (board built, hold = the kind left out, soft-drop spent 0),
//! reach a winning tiling of class index <= k with bag-2 soft-drop <= b (b = 0,1,2,unlimited), cumulative over classes.
//! This equals what `tst2bag-tp` MULTI=1 counts for phase 1 from soft-drop 0, for all classes and budgets in one pass.
//! tile/rots/Reach/Union/left_of and the soft-drop rule are copied verbatim from `tst2bag-tp`. JOBS=n threads.
use std::collections::HashMap;
use std::io::{BufRead, Write};
use oracle_rs::reach;
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
struct UState { set: Vec<usize>, occ: u128, tils: Vec<usize> }
struct Union { pl: Vec<Pl>, kind: Vec<u8>, til_sets: Vec<Vec<usize>>, nodes: Vec<UState>, index: HashMap<Vec<usize>, u32>, edges: HashMap<u32, Vec<(usize, u32, u32)>>, tst_ok: bool, n: usize, til_tst: Vec<bool> }
impl Union {
    fn node(&mut self, set: Vec<usize>, tils: Vec<usize>) -> u32 {
        if let Some(&i) = self.index.get(&set) { return i; }
        let occ = set.iter().fold(0u128, |a, &p| a | bits(&self.pl[p].1));
        let i = self.nodes.len() as u32; self.index.insert(set.clone(), i); self.nodes.push(UState { set, occ, tils }); i
    }
    fn edges_of(&mut self, id: u32, rc: &mut Reach) -> Vec<(usize, u32)> { self.edges_sd(id, rc).into_iter().map(|(p,c,_)| (p,c)).collect() }
    fn edges_sd(&mut self, id: u32, rc: &mut Reach) -> Vec<(usize, u32, u32)> {
        if let Some(e) = self.edges.get(&id) { return e.clone(); }
        let (set, occ, tils) = { let s = &self.nodes[id as usize]; (s.set.clone(), s.occ, s.tils.clone()) };
        let mut cand: Vec<usize> = tils.iter().flat_map(|&t| self.til_sets[t].iter().cloned()).filter(|p| !set.contains(p)).collect();
        cand.sort(); cand.dedup();
        let mut out = vec![];
        for p in cand {
            let want: [u16;4] = [self.pl[p].1[0], self.pl[p].1[1], self.pl[p].1[2], self.pl[p].1[3]];
            if !rc.get(occ, sym_of(self.pl[p].0)).iter().any(|f| f.0 == want) { continue; }
            let mut s2 = set.clone(); s2.push(p); s2.sort();
            let t2: Vec<usize> = tils.iter().cloned().filter(|&t| self.til_sets[t].binary_search(&p).is_ok()).collect();
            // hard-droppable iff no filled cell above any piece cell in its column
            let mut sd = 0u32;
            for &cc in &want { let x = cc % 10; let mut y = cc / 10 + 1; while y < 12 { let k = y*10 + x; if occ >> k & 1 == 1 && !want.contains(&k) { sd = 1; } y += 1; } }
            let c = self.node(s2, t2); out.push((p, c, sd));
        }
        self.edges.insert(id, out.clone()); out
    }
    fn full_til(&self, id: u32) -> Option<usize> { let s = &self.nodes[id as usize]; if self.til_tst.is_empty() { if s.set.len() == self.n { s.tils.first().cloned() } else { None } } else { s.tils.iter().cloned().find(|&t| self.til_sets[t].len() == s.set.len()) } }
}
fn left_of(t: &[Pl]) -> String {
    let mut left = String::new();
    for &k in b"IJLOSTZ" { let used = t.iter().filter(|p| p.0 == k).count() as i32 + if k == b'T' { 1 } else { 0 }; for _ in used..2 { left.push(k as char); } }
    left
}

// ---- one-pass counter -------------------------------------------------------------------------------------------
// state: f<<31 | h<<28 | sd<<24 | node id   (sd saturates at 3 = "more than 2": counts only for the unlimited budget)
fn senc(id: u32, h: u32, f: u32, sd: u32) -> u32 { f << 31 | h << 28 | sd << 24 | id }
const IDM: u32 = 0xff_ffff;
const NOCLS: u8 = 255;

struct Ctx<'a> {
    u: &'a mut Union, rc: &'a mut Reach, cls: Vec<u8>, ncls: usize,
    info: HashMap<u32, (u8, bool)>, // node -> (least class of an alive full tst-ok tiling, live)
    memo: HashMap<Vec<u32>, Vec<[u16; 4]>>,
}
impl<'a> Ctx<'a> {
    fn info(&mut self, id: u32) -> (u8, bool) {
        if let Some(&v) = self.info.get(&id) { return v; }
        let st = &self.u.nodes[id as usize]; let mut wc = NOCLS; let mut live = false;
        for &t in &st.tils {
            if !self.u.til_tst[t] || self.cls[t] == NOCLS { continue; }
            live = true;
            if self.u.til_sets[t].len() == st.set.len() && self.cls[t] < wc { wc = self.cls[t]; }
        }
        self.info.insert(id, (wc, live)); (wc, live)
    }
    fn step(&mut self, st: &[u32], c: u8, win: &mut [u8; 4]) -> Vec<u32> {
        let mut res: Vec<u32> = vec![];
        for &s in st {
            let f = s >> 31; let h = s >> 28 & 7; let sd = s >> 24 & 3; let id = s & IDM;
            let (wc, _) = self.info(id);
            if c == T && wc != NOCLS && wc < win[sd as usize] { win[sd as usize] = wc; }
            for (p, ch, e) in self.u.edges_sd(id, self.rc) {
                if self.u.kind[p] != c { continue; }
                if !self.info(ch).1 { continue; }
                assert!(ch < 1 << 24);
                res.push(senc(ch, h, 0, (sd + e).min(3)));
            }
            if f == 1 { continue; }
            if h == 0 { res.push(senc(id, c as u32, 1, sd)); }
            else {
                if h == T as u32 && wc != NOCLS && wc < win[sd as usize] { win[sd as usize] = wc; }
                for (p, ch, e) in self.u.edges_sd(id, self.rc) {
                    if self.u.kind[p] != h as u8 { continue; }
                    if !self.info(ch).1 { continue; }
                    res.push(senc(ch, c as u32, 0, (sd + e).min(3)));
                }
            }
        }
        // least soft-drop per (node, hold, f)
        res.sort_unstable_by_key(|&x| (x & !(3 << 24), x));
        res.dedup_by_key(|x| *x & !(3 << 24));
        res
    }
    fn rec(&mut self, st: Vec<u32>, r: u32) -> Vec<[u16; 4]> {
        let mut out = vec![[0u16; 4]; self.ncls];
        if r == 0 {
            let mut win = [NOCLS; 4];
            for &s in &st {
                let h = s >> 28 & 7; let sd = s >> 24 & 3; let (wc, _) = self.info(s & IDM);
                if h == T as u32 && wc != NOCLS && wc < win[sd as usize] { win[sd as usize] = wc; }
            }
            fill(&mut out, &win, 1, None);
            return out;
        }
        let mut key = st.clone(); key.push(r);
        if let Some(v) = self.memo.get(&key) { return v.clone(); }
        let rem = r.count_ones() as usize;
        for i in 0..7 { if r >> i & 1 == 1 {
            let mut win = [NOCLS; 4];
            let v = self.step(&st, i as u8 + 1, &mut win);
            let child = if v.is_empty() { None } else { Some(self.rec(v, r & !(1 << i))) };
            fill(&mut out, &win, FACT[rem - 1] as u16, child.as_ref());
        }}
        self.memo.insert(key, out.clone()); out
    }
}
// out[k][b] += w if some win with class <= k and sd <= b, else child[k][b]
fn fill(out: &mut [[u16; 4]], win: &[u8; 4], w: u16, child: Option<&Vec<[u16; 4]>>) {
    let mut pref = [NOCLS; 4]; let mut m = NOCLS;
    for b in 0..4 { m = m.min(win[b]); pref[b] = m; }
    for k in 0..out.len() { for b in 0..4 {
        if pref[b] != NOCLS && pref[b] as usize <= k { out[k][b] += w; } else if let Some(c) = child { out[k][b] += c[k][b]; }
    }}
}

struct Shapes { tils: HashMap<String, std::sync::Arc<Vec<Vec<Pl>>>>, ok: HashMap<String, bool> }

fn run_d(line: &str, sh: &Shapes, rc: &mut Reach) -> String {
    let f: Vec<&str> = line.split('#').collect();
    let name = f[0];
    let b1p: Vec<Pl> = f[1].split('/').map(|s| { let mut q = s.split(':'); let k = q.next().unwrap().as_bytes()[0]; let mut v: Vec<u16> = q.next().unwrap().split(',').map(|c| c.parse().unwrap()).collect(); v.sort(); (k, v) }).collect();
    let classes: Vec<(usize, String)> = f[f.len()-1].split(';').map(|s| { let mut q = s.split(':'); let a: usize = q.next().unwrap().parse().unwrap(); let l = q.next().unwrap(); (a, if l == "-" { String::new() } else { l.to_string() }) }).collect();
    let mut tils: Vec<Vec<Pl>> = vec![]; let mut til_shape = vec![]; let mut til_tst = vec![];
    for (si, s) in f[2..f.len()-1].iter().enumerate() {
        let mut q = s.split('|'); let cells = q.next().unwrap(); let tst = q.next().unwrap();
        let ok = sh.ok[&format!("{}|{}", cells, tst)];
        for t in sh.tils[cells].iter() { tils.push(t.clone()); til_shape.push(si); til_tst.push(ok); }
    }
    let mut pl: Vec<Pl> = tils.iter().flat_map(|t| t.iter().cloned()).collect(); pl.sort(); pl.dedup();
    let til_sets: Vec<Vec<usize>> = tils.iter().map(|t| { let mut v: Vec<usize> = t.iter().map(|p| pl.binary_search(p).unwrap()).collect(); v.sort(); v }).collect();
    let n = tils[0].len();
    let til_left: Vec<String> = tils.iter().map(|t| left_of(t)).collect();
    let kind: Vec<u8> = pl.iter().map(|p| K.iter().position(|&c| c == p.0).unwrap() as u8 + 1).collect();
    let mut b1: Vec<usize> = b1p.iter().map(|p| pl.binary_search(p).expect("b1 piece not in any tiling")).collect(); b1.sort();
    let keep: Vec<usize> = (0..tils.len()).filter(|&t| b1.iter().all(|p| til_sets[t].binary_search(p).is_ok())).collect();
    let mut u = Union { pl: pl.clone(), kind, til_sets: til_sets.clone(), nodes: vec![], index: HashMap::new(), edges: HashMap::new(), tst_ok: false, n, til_tst: til_tst.clone() };
    let root = u.node(vec![], keep.clone());
    let mut seen = std::collections::HashSet::new(); seen.insert(root); let mut qq = vec![root]; let mut b1_id = None;
    while let Some(id) = qq.pop() { if u.nodes[id as usize].set == b1 { b1_id = Some(id); } for (p, ch) in u.edges_of(id, rc) { if b1.contains(&p) && seen.insert(ch) { qq.push(ch); } } }
    let Some(b1_id) = b1_id else { return format!("{{\"name\":\"{}\",\"ntil\":{},\"D\":null}}", name, keep.len()); };
    // the kind left out of bag 1 is the held one
    let mut have = [false; 8];
    for &p in &b1 { let k = u.kind[p] as usize; assert!(!have[k], "bag-1 board repeats a kind"); have[k] = true; }
    let miss: Vec<u32> = (1..=7u32).filter(|&k| !have[k as usize]).collect();
    assert!(miss.len() == 1, "bag-1 board is not six kinds");
    let cls: Vec<u8> = (0..tils.len()).map(|t| classes.iter().position(|(a, l)| *a == til_shape[t] && *l == til_left[t]).map_or(NOCLS, |i| i as u8)).collect();
    assert!(classes.len() < 255);
    let mut c = Ctx { u: &mut u, rc, cls, ncls: classes.len(), info: HashMap::new(), memo: HashMap::new() };
    let d = c.rec(vec![senc(b1_id, miss[0], 0, 0)], 127);
    let rows: Vec<String> = (0..4).map(|b| format!("[{}]", d.iter().map(|x| x[b].to_string()).collect::<Vec<_>>().join(","))).collect();
    format!("{{\"name\":\"{}\",\"ntil\":{},\"D\":[{}]}}", name, keep.len(), rows.join(","))
}

fn main() {
    let lines: Vec<String> = std::io::stdin().lock().lines().map(|l| l.unwrap()).filter(|l| !l.is_empty()).collect();
    let nt: usize = std::env::var("JOBS").ok().and_then(|s| s.parse().ok()).unwrap_or(4);
    let parse = |s: &str| -> Vec<(i32,i32)> { s.split(';').map(|p| { let mut q = p.split(','); (q.next().unwrap().parse().unwrap(), q.next().unwrap().parse().unwrap()) }).collect() };
    let lim: HashMap<u8,u32> = b"IJLOSZ".iter().map(|&k| (k,2)).chain([(b'T',1)]).collect();
    let mut rc0 = Reach { cache: HashMap::new() };
    let mut sh = Shapes { tils: HashMap::new(), ok: HashMap::new() };
    for l in &lines { let f: Vec<&str> = l.split('#').collect(); for s in &f[2..f.len()-1] {
        let mut q = s.split('|'); let cs = q.next().unwrap(); let tstv = q.next().unwrap();
        if !sh.tils.contains_key(cs) { sh.tils.insert(cs.to_string(), std::sync::Arc::new(tile(&parse(cs), &lim))); }
        let key = format!("{}|{}", cs, tstv);
        if !sh.ok.contains_key(&key) {
            let cells = parse(cs); let tv = parse(tstv);
            let mut tst = [0u16;4]; for i in 0..4 { tst[i] = (tv[i].1*10+tv[i].0) as u16; } tst.sort();
            let occ: u128 = cells.iter().fold(0u128, |a, p| a | 1u128 << (p.1*10+p.0));
            let ok = rc0.get(occ, sym_of(b'T')).iter().any(|f| f.0 == tst && f.1 == 2);
            sh.ok.insert(key, ok);
        }
    }}
    let sh = std::sync::Arc::new(sh);
    let lines = std::sync::Arc::new(lines);
    let next = std::sync::Arc::new(std::sync::atomic::AtomicUsize::new(0));
    let out = std::sync::Arc::new(std::sync::Mutex::new(vec![String::new(); lines.len()]));
    let timing = std::env::var("TIMING").is_ok();
    let hs: Vec<_> = (0..nt).map(|_| { let (sh, lines, next, out) = (sh.clone(), lines.clone(), next.clone(), out.clone()); std::thread::spawn(move || {
        let mut rc = Reach { cache: HashMap::new() };
        loop { let i = next.fetch_add(1, std::sync::atomic::Ordering::SeqCst); if i >= lines.len() { break; }
            if rc.cache.len() > 400_000 { rc.cache.clear(); }
            let t0 = std::time::Instant::now(); let s = run_d(&lines[i], &sh, &mut rc);
            if timing { eprintln!("{} {:?}", lines[i].split('#').next().unwrap(), t0.elapsed()); }
            out.lock().unwrap()[i] = s; }
    }) }).collect();
    for h in hs { h.join().unwrap(); }
    let so = std::io::stdout(); let mut so = so.lock();
    for s in out.lock().unwrap().iter() { writeln!(so, "{}", s).unwrap(); }
}

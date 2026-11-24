//! PC-after-a-T-spin-Double counter for the TST opener ranking (pilot; CONSTRUCTED, quarantined like the rest).
//!
//! pc-solver-rs's DFS (`Ctx::rec`, copied) with one more state bit `tsd`: the plan must contain a T placement that
//! clears exactly two rows and that the engine's own movegen (oracle_rs::reach, the search tst2bag-tp uses for the
//! TST) credits as a FULL T-spin (spin code 2) on the board at that moment. A Perfect Clear without such a lock does
//! not count. A TSD that is itself the PC-completing lock counts (the rule is "contains", not "is followed by").
//!
//! Input lines on stdin: `rows|left`, rows = comma-joined residue rows (bit x of row y, bottom first), left = the leftover
//! class (empty string for none). Per line, over all 5040 bag-3 orders (start state = tst2bag-tp's `pc_rate`):
//!   p5   plain PC count (check(.., 5, 2_000_000)), the number the artefact's classes carry (skip: NOBASE=1)
//!   pt3  TSD+PC count, frames up to 5, 2M nodes per frame
//!   (a bag-4 count, pt4, is deliberately not computed: the pilot's sampled version is dropped)
//! Every plan found is replayed (hold rule, placements, clears, empty at the end, a TSD lock via a fresh reach query);
//! `bad_plans` must be 0. Env: JOBS (threads, 4). Output has no timings (they go to stderr), so a run is deterministic up to line order.
use std::collections::HashMap;
use std::io::{BufRead, Write};
use std::sync::{atomic::{AtomicUsize, Ordering}, Arc};

use oracle_rs::reach;
use pc_solver_rs::solver::{apply, check, filled, frames, placements, Budget, Gen, Memo, Pl, Verdict, FxBuild, MAX_ROWS, NONE, W};
use pc_solver_rs::srs::PIECES;

const T_SYM: usize = 5; // "ijlostz"
const T: u8 = b'T';

/// (occupancy of the board rows, full-T-spin cell sets of a T on it), cached.
#[derive(Default)]
struct ReachCache { m: HashMap<u128, Vec<[u16; 4]>, FxBuild> }
impl ReachCache {
    /// Cells (sorted, y*10+x) of every T placement the engine reaches on `rows` with spin code 2.
    fn full_spins(&mut self, rows: &[u16]) -> &Vec<[u16; 4]> {
        assert!(rows.len() <= 12);
        let mut occ = 0u128;
        for (y, &r) in rows.iter().enumerate() { occ |= ((r & 0x3ff) as u128) << (10 * y); }
        if self.m.len() > 200_000 { self.m.clear(); }
        self.m.entry(occ).or_insert_with(|| {
            let mut b = [[false; 10]; 40];
            for i in 0..120 { if occ >> i & 1 == 1 { b[i / 10][i % 10] = true; } }
            let mut v: Vec<[u16; 4]> = reach::search(&b, T_SYM, (3.0, 22.04, 0), false).into_iter()
                .filter(|f| f.spin == 2).map(|f| { let mut c = f.cells; c.sort(); c }).collect();
            v.sort(); v.dedup(); v
        })
    }
    fn is_full_spin(&mut self, rows: &[u16], cells: &[u8; 4]) -> bool {
        let mut c = [cells[0] as u16, cells[1] as u16, cells[2] as u16, cells[3] as u16]; c.sort();
        self.full_spins(rows).binary_search(&c).is_ok()
    }
}

fn rows_key(rows: &[u16]) -> u128 {
    assert!(rows.len() <= MAX_ROWS, "board too tall for the key");
    let mut k: u128 = rows.len() as u128;
    for (i, &m) in rows.iter().enumerate() { k |= (m as u128 & 0x3ff) << (4 + 10 * i); }
    k
}
fn regions_ok(rows: &[u16], h: i32) -> bool {
    let n = (h * W) as usize;
    let mut empty = [0u8; 160];
    for y in 0..h as usize {
        let m = rows.get(y).copied().unwrap_or(0);
        for x in 0..W as usize { empty[y * 10 + x] = if m >> x & 1 != 0 { 0 } else { 1 }; }
    }
    let mut st: Vec<usize> = Vec::with_capacity(64);
    for s in 0..n {
        if empty[s] == 0 { continue; }
        let mut cnt = 0;
        empty[s] = 0; st.push(s);
        while let Some(c) = st.pop() {
            cnt += 1;
            let x = c % 10; let y = c / 10;
            if x > 0 && empty[c - 1] != 0 { empty[c - 1] = 0; st.push(c - 1); }
            if x < 9 && empty[c + 1] != 0 { empty[c + 1] = 0; st.push(c + 1); }
            if y > 0 && empty[c - 10] != 0 { empty[c - 10] = 0; st.push(c - 10); }
            if (y as i32) < h - 1 && empty[c + 10] != 0 { empty[c + 10] = 0; st.push(c + 10); }
        }
        if cnt % 4 != 0 { return false; }
    }
    true
}
#[inline]
fn pcode(p: u8) -> u128 { PIECES.iter().position(|&q| q == p).map(|i| i as u128 + 1).unwrap_or(0) }

struct Ctx<'a> { seq: &'a [u8], memo: &'a mut Memo, nodes: i64, short: bool, buf: Vec<Vec<u16>>, rc: &'a mut ReachCache }

impl Ctx<'_> {
    #[inline]
    fn at(&self, i: i64) -> u8 { if i >= 0 && (i as usize) < self.seq.len() { self.seq[i as usize] } else { NONE } }
    fn t_left(&self, cur: u8, hold: u8, ptr: i64) -> bool {
        cur == T || hold == T || self.seq.get(ptr.max(0) as usize..).map_or(false, |s| s.contains(&T))
    }

    /// pc-solver-rs `Ctx::rec` with `tsd`; the memo key carries it in bit 126.
    fn rec(&mut self, rows: &[u16], h: i32, cur: u8, hold: u8, ptr: i64, tsd: bool, depth: usize) -> Result<Option<Vec<Pl>>, Budget> {
        if h == 0 && rows.is_empty() { return Ok(if tsd { Some(Vec::new()) } else { None }); }
        if !regions_ok(rows, h) { return Ok(None); }
        let need4 = (h * W - filled(rows)) as i64;
        let avail = self.seq.len() as i64 - ptr + 1 + if hold != NONE { 1 } else { 0 };
        if avail * 4 < need4 { self.short = true; return Ok(None); }
        // no T left to spin with: a plain failure (sound: the T is the only piece that can fire the spin)
        if !tsd && !self.t_left(cur, hold, ptr) { return Ok(None); }
        assert!(rows.len() <= MAX_ROWS && h <= 15);
        let key = rows_key(rows) | (h as u128) << 84 | pcode(cur) << 88 | pcode(hold) << 91 | ((ptr as u64 as u128) & 0xFFFF_FFFF) << 94
            | (tsd as u128) << 126;
        if let Some(m) = self.memo.m.get(&key) { return Ok(m.as_ref().map(|p| p.to_vec())); }
        self.nodes -= 1;
        if self.nodes < 0 { return Err(Budget); }
        let mut opts: [(u8, u8, u8, i64, bool); 2] = [(NONE, NONE, NONE, 0, false); 2];
        let mut no = 0;
        opts[no] = (cur, hold, self.at(ptr), ptr + 1, false); no += 1;
        if hold == NONE {
            if self.at(ptr) != NONE { opts[no] = (self.at(ptr), cur, self.at(ptr + 1), ptr + 2, true); no += 1; }
        } else if hold != cur {
            opts[no] = (hold, cur, self.at(ptr), ptr + 1, true); no += 1;
        }
        if self.buf.len() <= depth { self.buf.push(Vec::with_capacity(16)); }
        for &(pc, nh, nc, np, held) in &opts[..no] {
            if pc == NONE { self.short = true; continue; }
            let list = placements(Gen::Engine, rows, pc, h);
            for cells in list.iter() {
                let mut a = std::mem::take(&mut self.buf[depth]);
                let ah = apply(rows, cells, h, &mut a);
                let mut ntsd = tsd;
                if !tsd && pc == T && h - ah == 2 && self.rc.is_full_spin(rows, cells) { ntsd = true; }
                let me = Pl { piece: pc, cells: *cells, held };
                if ah == 0 && a.is_empty() {
                    self.buf[depth] = a;
                    if !ntsd { continue; }
                    let r = vec![me];
                    self.memo.m.insert(key, Some(r.clone().into_boxed_slice()));
                    return Ok(Some(r));
                }
                if nc == NONE { self.short = true; self.buf[depth] = a; continue; }
                let sub = self.rec(&a, ah, nc, nh, np, ntsd, depth + 1);
                self.buf[depth] = a;
                if let Some(sub) = sub? {
                    let mut r = Vec::with_capacity(sub.len() + 1);
                    r.push(me); r.extend_from_slice(&sub);
                    self.memo.m.insert(key, Some(r.clone().into_boxed_slice()));
                    return Ok(Some(r));
                }
            }
        }
        self.memo.m.insert(key, None);
        Ok(None)
    }
}

fn solve(rows: &[u16], h: i32, cur: u8, hold: u8, seq: &[u8], memo: &mut Memo, nodes: i64, rc: &mut ReachCache) -> Result<Verdict, Budget> {
    let mut cx = Ctx { seq, memo, nodes, short: false, buf: Vec::new(), rc };
    let r = cx.rec(rows, h, cur, hold, 0, false, 0)?;
    Ok(match r { Some(plan) => Verdict::Ok { h, plan }, None => if cx.short { Verdict::Short } else { Verdict::False } })
}
/// pc-miss.ts `check` with the TSD requirement.
fn check_tsd(rows: &[u16], cur: u8, hold: u8, seq: &[u8], memo: &mut Memo, max_h: i32, nodes: i64, rc: &mut ReachCache) -> Verdict {
    let mut unknown = false;
    for h in frames(rows, max_h) {
        match solve(rows, h, cur, hold, seq, memo, nodes, rc) {
            Err(Budget) => unknown = true,
            Ok(Verdict::Ok { h, plan }) => return Verdict::Ok { h, plan },
            Ok(Verdict::Short) => unknown = true,
            Ok(Verdict::False) => {}
        }
    }
    if unknown { Verdict::Short } else { Verdict::False }
}

/// Replay a plan from the start state: hold rule, placement legality (disjoint cells), clears, empty board at the end,
/// and a T lock that clears exactly 2 rows with a full engine spin on the board at that moment.
fn replay(rows0: &[u16], h: i32, cur0: u8, hold0: u8, seq: &[u8], plan: &[Pl], rc: &mut ReachCache) -> bool {
    let at = |i: usize| seq.get(i).copied().unwrap_or(NONE);
    let (mut cur, mut hold, mut ptr) = (cur0, hold0, 0usize);
    let (mut rows, mut hh) = (rows0.to_vec(), h);
    let mut tsd = false;
    let mut tmp = Vec::new();
    for (i, p) in plan.iter().enumerate() {
        if p.held {
            if hold == NONE { if p.piece != at(ptr) { return false; } hold = cur; cur = at(ptr + 1); ptr += 2; }
            else { if p.piece != hold { return false; } hold = cur; cur = at(ptr); ptr += 1; }
        } else { if p.piece != cur { return false; } cur = at(ptr); ptr += 1; }
        let mut padded = rows.clone();
        while (padded.len() as i32) < hh { padded.push(0); }
        for &c in &p.cells { if c as i32 / W >= hh || padded[(c as i32 / W) as usize] >> (c as i32 % W) & 1 != 0 { return false; } }
        let mut cs = p.cells; cs.sort(); if cs[0] == cs[1] || cs[1] == cs[2] || cs[2] == cs[3] { return false; }
        let ah = apply(&rows, &p.cells, hh, &mut tmp);
        if p.piece == T && hh - ah == 2 && rc.is_full_spin(&rows, &p.cells) { tsd = true; }
        rows = tmp.clone(); hh = ah;
        if i + 1 == plan.len() { return hh == 0 && rows.is_empty() && tsd; }
    }
    false
}

fn start(left: &[u8], b: &[u8]) -> (u8, u8, Vec<u8>) {
    match left.len() {
        0 => (b[0], NONE, b[1..].to_vec()), 1 => (left[0], NONE, b.to_vec()), 2 => (left[0], left[1], b.to_vec()),
        _ => { let mut s = left[2..].to_vec(); s.extend(b); (left[0], left[1], s) }
    }
}
fn perms() -> Vec<Vec<u8>> {
    let mut out = vec![];
    fn r(p: &mut Vec<u8>, rest: &mut Vec<u8>, out: &mut Vec<Vec<u8>>) {
        if rest.is_empty() { out.push(p.clone()); return; }
        for i in 0..rest.len() { let c = rest.remove(i); p.push(c); r(p, rest, out); p.pop(); rest.insert(i, c); }
    }
    r(&mut vec![], &mut b"IOTSZJL".to_vec(), &mut out); out
}

fn run(l: &str, ps: &[Vec<u8>], base: bool, rc: &mut ReachCache) -> String {
    let mut it = l.split('|');
    let rows: Vec<u16> = it.next().unwrap().split(',').filter(|s| !s.is_empty()).map(|s| s.parse().unwrap()).collect();
    let left: Vec<u8> = it.next().unwrap_or("").bytes().collect();
    // parity: bags 1+2 are 14 pieces; the TST clears 3 rows of 10; L pieces are left over
    assert_eq!(filled(&rows), 26 - 4 * left.len() as i32, "residue parity for {l}");
    let t0 = std::time::Instant::now();
    let mut p5 = 0; let mut p5u = 0;
    if base {
        for b in ps {
            let (c, h, s) = start(&left, b);
            match check(&rows, c, h, &s, 0, &mut Memo::default(), 5, 2_000_000, Gen::Engine) { Verdict::Ok { .. } => p5 += 1, Verdict::Short => p5u += 1, Verdict::False => {} }
        }
    }
    let (mut pt3, mut pt3u, mut bad) = (0, 0, 0);
    for b in ps {
        let (c, h, s) = start(&left, b);
        match check_tsd(&rows, c, h, &s, &mut Memo::default(), 5, 2_000_000, rc) {
            Verdict::Ok { h: hh, plan } => { pt3 += 1; if !replay(&rows, hh, c, h, &s, &plan, rc) { bad += 1; } }
            Verdict::Short => pt3u += 1,
            Verdict::False => {}
        }
    }
    eprintln!("{l}: {:.2}s", t0.elapsed().as_secs_f64());
    format!("{{\"line\":{:?},\"p5\":{},\"p5u\":{},\"pt3\":{},\"pt3u\":{},\"bad_plans\":{}}}", l, p5, p5u, pt3, pt3u, bad)
}

fn main() {
    let nt: usize = std::env::var("JOBS").ok().and_then(|s| s.parse().ok()).unwrap_or(4);
    let base = std::env::var("NOBASE").is_err();
    let lines: Arc<Vec<String>> = Arc::new(std::io::stdin().lock().lines().map(|l| l.unwrap()).filter(|l| !l.is_empty()).collect());
    let ps = Arc::new(perms()); let next = Arc::new(AtomicUsize::new(0));
    let (tx, rx) = std::sync::mpsc::channel();
    for _ in 0..nt {
        let (ps, lines, next, tx) = (ps.clone(), lines.clone(), next.clone(), tx.clone());
        std::thread::spawn(move || {
            let mut rc = ReachCache::default();
            loop {
                let i = next.fetch_add(1, Ordering::SeqCst); if i >= lines.len() { break; }
                tx.send(run(&lines[i], &ps, base, &mut rc)).unwrap();
            }
        });
    }
    drop(tx);
    let so = std::io::stdout(); let mut so = so.lock();
    for s in rx { writeln!(so, "{}", s).unwrap(); so.flush().unwrap(); }
}

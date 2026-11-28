//! Recount of the learn-these-boards sets, written independently of `tst-sets-rs` (the search) and equal in what it asserts to the
//! numpy recount in `pipeline/sim/emit-tst-openers-tp.py` (`sets_check_obj` / `fixed_check`), which stays the reference
//! (`SETS_NATIVE=off`).
//!
//! stdin: line 1 the search's output JSON (`tst-sets`' stdout); then one line per board, in artefact order, the same lines the
//! search reads: `name|vec|F0|F1|F2|Finf|mate` (the mate field is not read here: the pairs are the ones in line 1, which the
//! caller has already checked against the mirror keys). One objective per run.
//! stdout: one line per budget, `<budget>\t<note>`. Any failed assertion panics (exit 101) with its message on stderr.
//!
//! What is recomputed, per budget: every pair's key table from the board tables; the dominance claims pointwise and that no
//! other board is dominated; every reported set's value and union; k = 1 over all pairs, k = 2 over every pair of the FULL list
//! (not the reduced one), k = 3 by the submodular certificate over the reduced list; every greedy step as the argmax over all
//! pairs; the picks string; every rule tree (leaf labels, figures, depth) and the depth-1 optimum by brute force; and the
//! fixed set's values at every budget.
mod json;
use json::J;
use std::io::Read;
use std::sync::atomic::{AtomicUsize, Ordering};

const B: usize = 5040;
const INFEAS: usize = 10;
const SH: u32 = 13;
const KINDS: &[u8] = b"IOTSZJL";
const BKS: [&str; 4] = ["0", "1", "2", "inf"];

struct Board { vec: Vec<u8>, j: [[u64; 10]; 4], bt: [[u64; 10]; 4] }

fn parse_board(line: &str) -> Board {
    let f: Vec<&str> = line.split('|').collect();
    assert_eq!(f.len(), 7, "board line fields");
    let vec: Vec<u8> = f[1].bytes().map(|c| if c == b'.' { INFEAS as u8 } else { c - b'0' }).collect();
    assert_eq!(vec.len(), B);
    let mut j = [[0u64; 10]; 4]; let mut bt = [[0u64; 10]; 4];
    for bk in 0..4 {
        let (a, b) = f[2 + bk].split_once('/').unwrap();
        for (i, x) in a.split(',').enumerate() { j[bk][i] = x.parse().unwrap(); }
        for (i, x) in b.split(',').enumerate() { bt[bk][i] = x.parse().unwrap(); }
    }
    Board { vec, j, bt }
}

fn lim(bk: usize) -> u8 { if bk == 3 { (INFEAS - 1) as u8 } else { bk as u8 } }

/// (J, built, available) of a board at one order, one budget; (0, 0, false) when over the budget
fn cell(b: &Board, bk: usize, o: usize) -> (u64, u64, bool) {
    let c = b.vec[o];
    if c > lim(bk) { return (0, 0, false); }
    let (j, t) = (b.j[bk][c as usize], b.bt[bk][c as usize]);
    assert!(t < 8192, "built exceeds its 13 bits");
    (j, t, true)
}
fn key_row(b: &Board, bk: usize) -> Vec<u64> { (0..B).map(|o| { let (j, t, a) = cell(b, bk, o); if a { j << SH | t } else { 0 } }).collect() }

fn perms() -> Vec<Vec<u8>> {
    fn r(p: &mut Vec<u8>, rest: &mut Vec<u8>, out: &mut Vec<Vec<u8>>) {
        if rest.is_empty() { out.push(p.clone()); return; }
        for i in 0..rest.len() { let c = rest.remove(i); p.push(c); r(p, rest, out); p.pop(); rest.insert(i, c); }
    }
    let mut out = vec![]; r(&mut vec![], &mut KINDS.to_vec(), &mut out); out
}

/// 28 features per order: 21 "X before Y" then 7 "first is X"
fn features() -> Vec<[bool; 28]> {
    let ps = perms();
    assert_eq!(ps.len(), B);
    ps.iter().map(|p| {
        let pos = |k: u8| p.iter().position(|&c| c == k).unwrap();
        let mut f = [false; 28]; let mut x = 0;
        for i in 0..7 { for j in i + 1..7 { f[x] = pos(KINDS[i]) < pos(KINDS[j]); x += 1; } }
        for k in 0..7 { f[x] = p[0] == KINDS[k]; x += 1; }
        f
    }).collect()
}

/// run f(0..n) on every core, results in index order
fn pmap<T: Send>(n: usize, f: &(dyn Fn(usize) -> T + Sync)) -> Vec<T> {
    let next = AtomicUsize::new(0);
    let th = std::thread::available_parallelism().map(|x| x.get()).unwrap_or(1).min(n.max(1));
    let mut got: Vec<(usize, T)> = std::thread::scope(|s| {
        let hs: Vec<_> = (0..th).map(|_| s.spawn(|| {
            let mut mine = vec![];
            loop { let i = next.fetch_add(1, Ordering::Relaxed); if i >= n { break; } mine.push((i, f(i))); }
            mine
        })).collect();
        hs.into_iter().flat_map(|h| h.join().unwrap()).collect()
    });
    got.sort_by_key(|x| x.0);
    got.into_iter().map(|x| x.1).collect()
}

/// sum over orders of max(x, y), u32 lanes
fn max_sum(x: &[u32], y: &[u32]) -> u64 {
    #[cfg(target_arch = "x86_64")]
    { if is_x86_feature_detected!("avx2") { return unsafe { max_sum_avx2(x, y) }; } }
    max_sum_plain(x, y)
}
#[inline(always)]
fn max_sum_plain(x: &[u32], y: &[u32]) -> u64 {
    let mut total = 0u64;
    for (cx, cy) in x.chunks(32).zip(y.chunks(32)) {
        let mut s = 0u64; // 32 lanes of < 2^27 stay far under 2^64; a u32 chunk sum would also fit but a u64 is exact by construction
        for (a, b) in cx.iter().zip(cy) { s += (*a).max(*b) as u64; }
        total += s;
    }
    total
}
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn max_sum_avx2(x: &[u32], y: &[u32]) -> u64 { max_sum_plain(x, y) }

struct Ctx { key: Vec<Vec<u64>>, j: Vec<Vec<u32>> }

fn val_of(k: &[u64]) -> (u64, u64) { (k.iter().map(|x| x >> SH).sum(), k.iter().map(|x| x & 8191).sum()) }
fn max_rows(rows: &[&[u64]]) -> Vec<u64> { (0..B).map(|o| rows.iter().map(|r| r[o]).max().unwrap_or(0)).collect() }

fn check_budget(raw: &J, boards: &[Board], pr: &[Vec<usize>], feat: &[[bool; 28]], bk: usize) -> String {
    let bks = BKS[bk];
    let r = raw.get("budgets").get(bks);
    let n = pr.len();
    // per candidate: the best key over the pair's boards
    let key: Vec<Vec<u64>> = pmap(n, &|c| {
        let mut k = vec![0u64; B];
        for &i in &pr[c] { for (o, x) in key_row(&boards[i], bk).into_iter().enumerate() { if x > k[o] { k[o] = x; } } }
        k
    });
    let j: Vec<Vec<u32>> = key.iter().map(|k| k.iter().map(|x| (x >> SH) as u32).collect()).collect();
    let cx = Ctx { key, j };
    let key = &cx.key;
    let dominated_by = |v: usize, u: usize| -> bool {
        let (kv, ku) = (&key[v], &key[u]);
        let mut eq = true;
        for o in 0..B { if kv[o] < ku[o] { return false; } if kv[o] != ku[o] { eq = false; } }
        !eq || v < u
    };
    // dominance
    let dom_l = r.get("dominated").arr();
    let mut dom = vec![usize::MAX; n];
    for p in dom_l { let (u, v) = (p.arr()[0].us(), p.arr()[1].us()); assert!(dom[u] == usize::MAX, "dominated listed twice"); dom[u] = v; }
    let reduced: Vec<usize> = (0..n).filter(|&i| dom[i] == usize::MAX).collect();
    assert_eq!(reduced.len(), r.get("reduced").us(), "reduced count ({})", bks);
    let chk: Vec<()> = pmap(dom_l.len(), &|t| {
        let (u, v) = (dom_l[t].arr()[0].us(), dom_l[t].arr()[1].us());
        assert!(dom[v] == usize::MAX && dominated_by(v, u), "dominance claim {} <- {} fails ({})", u, v, bks);
        for &w in reduced.iter().filter(|&&w| w < v) { assert!(!dominated_by(w, u), "dominator of {} is not the earliest ({})", u, bks); }
    });
    let _ = chk;
    let bad: Vec<bool> = pmap(reduced.len(), &|t| { let u = reduced[t]; (0..n).any(|w| w != u && dominated_by(w, u)) });
    for (t, b) in bad.iter().enumerate() { assert!(!b, "board {} is dominated but not listed ({})", reduced[t], bks); }

    let union_of = |s: &[usize]| -> Vec<usize> { let mut u: Vec<usize> = s.iter().flat_map(|&c| pr[c].iter().cloned()).collect(); u.sort(); u.dedup(); u };
    let setval = |s: &[usize]| val_of(&max_rows(&s.iter().map(|&c| &key[c][..]).collect::<Vec<_>>()));
    let check_set = |rec: &J, k: usize| {
        let s = rec.get("set").us_list();
        assert!(s.windows(2).all(|w| w[0] < w[1]) && s.len() == k, "set shape ({}, {:?})", bks, s);
        assert_eq!(setval(&s), (rec.get("pc3").int() as u64, rec.get("built").int() as u64), "set value wrong ({}, {:?})", bks, s);
        assert_eq!(rec.get("ub").us_list(), union_of(&s), "union of boards wrong ({}, {:?})", bks, s);
    };
    let ex_l = r.get("exact").arr();
    for e in ex_l { check_set(e, e.get("k").us()); }
    let ex = |k: usize| ex_l.iter().find(|e| e.get("k").us() == k).expect("exact k");
    let isred = { let mut v = vec![false; n]; for &i in &reduced { v[i] = true; } v };

    // k = 1 over every candidate
    let v1 = pmap(n, &|i| val_of(&key[i]));
    let m1 = *v1.iter().max().unwrap();
    assert_eq!(m1, (ex(1).get("pc3").int() as u64, ex(1).get("built").int() as u64), "k=1 value ({})", bks);
    let first1 = (0..n).find(|&i| v1[i] == m1 && isred[i]).unwrap();
    assert_eq!(ex(1).get("set").us_list(), vec![first1], "k=1 tie rule ({})", bks);

    // k = 2 over every pair of the full list: the best pc3 per row from J alone, then the exact value of the rows' best pairs
    let rows: Vec<(u64, Vec<usize>)> = pmap(n, &|a| {
        let (mut best, mut bl) = (0u64, vec![]);
        for b in a + 1..n {
            let pp = max_sum(&cx.j[a], &cx.j[b]);
            if bl.is_empty() || pp > best { best = pp; bl.clear(); bl.push(b); } else if pp == best { bl.push(b); }
        }
        (best, bl)
    });
    let p2 = rows.iter().filter(|r| !r.1.is_empty()).map(|r| r.0).max().expect("at least one pair");
    let mut bestp = (0u64, 0u64); let mut bestl: Vec<(usize, usize)> = vec![];
    for (a, (best, bl)) in rows.iter().enumerate() {
        if bl.is_empty() || *best != p2 { continue; }
        for &b in bl {
            let v = setval(&[a, b]);
            assert_eq!(v.0, *best);
            if bestl.is_empty() || v > bestp { bestp = v; bestl.clear(); }
            if v == bestp { bestl.push((a, b)); }
        }
    }
    assert_eq!(bestp, (ex(2).get("pc3").int() as u64, ex(2).get("built").int() as u64), "a better pair exists ({})", bks);
    let t2 = bestl.iter().filter(|t| isred[t.0] && isred[t.1]).min().expect("a pair of reduced boards");
    assert_eq!(ex(2).get("set").us_list(), vec![t2.0, t2.1], "pair tie rule ({})", bks);

    // k = 3: the certificate over the reduced list
    let m = reduced.len();
    let f1: Vec<i64> = reduced.iter().map(|&a| cx.j[a].iter().map(|&x| x as i64).sum()).collect();
    let f2: Vec<Vec<i64>> = pmap(m, &|a| (0..m).map(|b| max_sum(&cx.j[reduced[a]], &cx.j[reduced[b]]) as i64).collect());
    let t3 = (ex(3).get("pc3").int() as u64, ex(3).get("built").int() as u64);
    let per_a: Vec<(u64, Vec<Vec<usize>>)> = pmap(m, &|a| {
        let (mut surv, mut best3) = (0u64, vec![]);
        for b in a + 1..m { for c in b + 1..m {
            let ub = f2[a][b] + (f2[a][c] - f1[a]).min(f2[b][c] - f1[b]);
            if ub >= t3.0 as i64 {
                surv += 1;
                let s = [reduced[a], reduced[b], reduced[c]];
                let v = setval(&s);
                assert!(v <= t3, "a better triple exists ({}): {:?}", bks, s);
                if v == t3 { best3.push(s.to_vec()); }
            }
        } }
        (surv, best3)
    });
    let surv: u64 = per_a.iter().map(|x| x.0).sum();
    let best3 = per_a.iter().flat_map(|x| x.1.iter()).min().expect("an optimal triple").clone();
    assert_eq!(ex(3).get("set").us_list(), best3, "triple tie rule ({})", bks);
    let note = format!("reduced {}, triple certificate evaluated {} of {}", m, surv, m * (m.max(1) - 1) * (m.max(2) - 2) / 6);

    // greedy chains: every step the argmax over all candidates, the first of the tied reduced ones
    let step_ok = |prev: &[usize], rec: &J, k: usize| {
        let s = rec.get("set").us_list();
        assert!(prev.iter().all(|p| s.contains(p)) && s.len() == k, "greedy shape ({})", bks);
        let new: Vec<usize> = s.iter().cloned().filter(|x| !prev.contains(x)).collect();
        assert_eq!(new.len(), 1);
        let cur = max_rows(&prev.iter().map(|&c| &key[c][..]).collect::<Vec<_>>());
        let vs: Vec<(u64, u64)> = pmap(n, &|c| { let mk: Vec<u64> = (0..B).map(|o| cur[o].max(key[c][o])).collect(); val_of(&mk) });
        let top = *vs.iter().max().unwrap();
        assert_eq!(top, (rec.get("pc3").int() as u64, rec.get("built").int() as u64), "greedy step {} is not the best ({})", k, bks);
        let want = (0..n).find(|&i| isred[i] && vs[i] == top && !prev.contains(&i)).unwrap();
        assert_eq!(new[0], want, "greedy step {} tie rule ({})", k, bks);
    };
    let mut prev: Vec<usize> = vec![];
    for g in r.get("greedy").arr() { check_set(g, g.get("k").us()); step_ok(&prev, g, g.get("k").us()); prev = g.get("set").us_list(); }
    prev = ex(3).get("set").us_list();
    for g in r.get("from_exact3").arr() { check_set(g, g.get("k").us()); step_ok(&prev, g, g.get("k").us()); prev = g.get("set").us_list(); }

    // picks, over the BOARDS of the exact triple's union
    let ub = union_of(&ex(3).get("set").us_list());
    assert_eq!(r.get("ub").us_list(), ub);
    let cells: Vec<Vec<(u64, u64, bool)>> = ub.iter().map(|&i| (0..B).map(|o| cell(&boards[i], bk, o)).collect()).collect();
    let nu = ub.len();
    let pk: Vec<i32> = (0..B).map(|o| {
        let (mut best, mut arg) = (0u64, -1i32);
        for m in 0..nu { let (jj, t, a) = cells[m][o]; let k = if a { (jj << SH | t) + 1 } else { 0 }; if k > best { best = k; arg = m as i32; } }
        arg
    }).collect();
    let pk_s: String = pk.iter().map(|&x| if x < 0 { 'x' } else { (b'0' + x as u8) as char }).collect();
    assert_eq!(r.get("picks").str(), pk_s, "picks string ({})", bks);

    // rule trees
    let sub: Vec<Vec<u128>> = cells.iter().map(|c| c.iter().map(|&(jj, t, a)| if a { ((jj as u128) << 26) + t as u128 } else { 0 }).collect()).collect();
    let exv = t3;
    fn depth_of(nd: &J) -> usize { if nd.is_leaf() { 0 } else { 1 + depth_of(nd.get("y")).max(depth_of(nd.get("n"))) } }
    fn walk(nd: &J, idx: &[usize], sub: &[Vec<u128>], feat: &[[bool; 28]], out: &mut [i32], bks: &str) {
        if nd.is_leaf() {
            let tot: Vec<u128> = sub.iter().map(|s| idx.iter().map(|&o| s[o]).sum()).collect();
            let mut want = 0usize; for m in 1..tot.len() { if tot[m] > tot[want] { want = m; } }
            assert_eq!(nd.get("m").us(), want, "leaf label ({})", bks);
            for &o in idx { out[o] = want as i32; }
            return;
        }
        let f = nd.get("f").us();
        let (y, no): (Vec<usize>, Vec<usize>) = idx.iter().partition(|&&o| feat[o][f]);
        assert!(!y.is_empty() && !no.is_empty(), "a split with an empty side");
        walk(nd.get("y"), &y, sub, feat, out, bks); walk(nd.get("n"), &no, sub, feat, out, bks);
    }
    let all: Vec<usize> = (0..B).collect();
    for (d, t) in r.get("trees").arr().iter().enumerate() {
        assert_eq!(t.get("depth").us(), d + 1);
        let mut mem = vec![-1i32; B];
        walk(t.get("tree"), &all, &sub, feat, &mut mem, bks);
        let (mut p, mut b_, mut unb, mut diff) = (0u64, 0u64, 0u64, 0u64);
        for o in 0..B {
            let m = mem[o] as usize; let (jj, tt, a) = cells[m][o];
            if a { p += jj; b_ += tt; } else { unb += 1; }
            if pk[o] >= 0 && pk[o] != mem[o] { diff += 1; }
        }
        assert_eq!((p, b_), (t.get("pc3").int() as u64, t.get("built").int() as u64), "rule value depth {} ({})", d + 1, bks);
        assert_eq!(unb, t.get("unbuildable").int() as u64);
        assert_eq!(diff, t.get("differs").int() as u64);
        assert!((p, b_) <= exv);
        assert!(depth_of(t.get("tree")) <= d + 1);
    }
    let t1 = &r.get("trees").arr()[0];
    let mut best1: u128 = (0..nu).map(|m| sub[m].iter().sum::<u128>()).max().unwrap();
    for f in 0..28 {
        let ysel: Vec<bool> = (0..B).map(|o| feat[o][f]).collect();
        if ysel.iter().any(|&x| x) && ysel.iter().any(|&x| !x) {
            let side = |want: bool| (0..nu).map(|m| (0..B).filter(|&o| ysel[o] == want).map(|o| sub[m][o]).sum::<u128>()).max().unwrap();
            best1 = best1.max(side(true) + side(false));
        }
    }
    assert_eq!((t1.get("pc3").int() as u128, t1.get("built").int() as u128), (best1 >> 26, best1 & ((1 << 26) - 1)), "depth-1 tree is not optimal ({})", bks);
    note
}

fn main() {
    let mut inp = String::new();
    std::io::stdin().read_to_string(&mut inp).unwrap();
    let mut lines = inp.lines().filter(|l| !l.is_empty());
    let raw = json::parse(lines.next().expect("raw json"));
    let boards: Vec<Board> = lines.map(parse_board).collect();
    let pr: Vec<Vec<usize>> = raw.get("pairs").arr().iter().map(|p| p.us_list()).collect();
    assert_eq!(raw.get("boards").us(), boards.len());
    let mut seen = vec![false; boards.len()];
    for p in &pr { for &i in p { assert!(!seen[i], "board in two pairs"); seen[i] = true; } }
    assert!(seen.iter().all(|&x| x), "pairs do not partition the boards");
    let feat = features();
    // an optional argument names the one budget to recount (the cheap equality check); the fixed set is always checked
    let only = std::env::args().nth(1);
    for bk in 0..4 {
        if only.as_deref().map_or(false, |o| o != BKS[bk]) { continue; }
        let t = std::time::Instant::now();
        let note = check_budget(&raw, &boards, &pr, &feat, bk);
        eprintln!("budget {} checked ({:?})", BKS[bk], t.elapsed());
        println!("{}\t{}", BKS[bk], note);
    }
    // the fixed set, valued at every budget
    let fx = raw.get("fixed");
    let s = fx.get("set").us_list();
    assert_eq!(s, raw.get("budgets").get("2").get("exact").arr()[2].get("set").us_list());
    let mut ub: Vec<usize> = s.iter().flat_map(|&c| pr[c].iter().cloned()).collect(); ub.sort(); ub.dedup();
    assert_eq!(fx.get("ub").us_list(), ub);
    for bk in 0..4 {
        let rows: Vec<Vec<u64>> = ub.iter().map(|&i| key_row(&boards[i], bk)).collect();
        let v = val_of(&max_rows(&rows.iter().map(|r| &r[..]).collect::<Vec<_>>()));
        let w = fx.get("values").get(BKS[bk]);
        assert_eq!(v, (w.get("pc3").int() as u64, w.get("built").int() as u64), "fixed value ({})", BKS[bk]);
    }
    println!("fixed\tok");
}

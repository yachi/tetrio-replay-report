//! Which small set of TST opener shapes to learn: the set of k candidates (a candidate is a mirror pair {board, its mirror}, a
//! board whose mirror is itself or is not in the pool being a pair of one; learning a shape includes its mirror) that, picking
//! the best BOARD of the union for each first-bag dealt order, maximises the number of (bag-1 order, bag-2 deal, bag-3 deal) triples that build AND get a
//! bag-3 Perfect Clear ("pc3"), per soft-drop budget; then a learnable decision tree over the order.
//!
//! stdin: one line per board, in artefact order: `name|vec|F0|F1|F2|Finf|mate`, `mate` the position of the board's mirror in
//! this list (its own position when it has none); a candidate is the pair {i, mate[i]} listed at the smaller position;
//! `vec` the board's 5040-char first-bag vector
//! ('.' = no build, else the least soft-drop cost digit), each F `J0,..,J9/B0,..,B9` the board's J and built tables by cost
//! code s = 0..9 for that budget (0 where the cost is over the budget). Budgets are 0, 1, 2 soft drops and unlimited.
//! stdout: one JSON object (no timings; those go to stderr).
//!
//! Rules, all total so nothing depends on iteration luck:
//!   * pick: among the set members available at the order (cost <= budget), the larger (J, built), ties to the earlier
//!     board position;
//!   * set value: (pc3, built) = sums of the picked J and built over the 5040 orders; sets compare by larger pc3, then
//!     larger built, then the lexicographically smaller tuple of board positions;
//!   * dominance: u is dominated by v when key_v >= key_u on every order (key = J*8192+built, 0 when unavailable) and the
//!     two keys are not equal everywhere or v is the earlier board. Dominated boards are dropped; the dominator recorded is
//!     the earliest non-dominated one. Replacing a dominated member by its dominator never lowers (pc3, built);
//!   * exact k = 1, 2 by scan, k = 3 by branch and bound on the submodular bound
//!     f(abc) <= f(ab) + min(f(ac) - f(a), f(bc) - f(b)) over pc3; greedy chain k = 1..5 and the greedy extension of the
//!     exact triple;
//!   * tree: optimal depth <= d (d = 1, 2, 3) over 28 binary features of the order (21 "X before Y", 7 "first is X") for the
//!     exact k = 3 set, each leaf labelled with the member maximising the leaf's (sum J, sum built), ties to the smaller
//!     member; a split must beat a leaf strictly, equal splits go to the smaller feature.
use std::io::{BufRead, Write};

const B: usize = 5040;
const INF: u8 = 10;
const KINDS: &[u8] = b"IOTSZJL";
const SH: u32 = 13; // key = J << 13 | built, built <= 5040 < 8192

pub struct Tab {
    pub j: Vec<Vec<u32>>,   // masked J (0 when unavailable)
    pub key: Vec<Vec<u64>>, // J<<13|built, 0 when unavailable
    pub av: Vec<Vec<bool>>,
}

pub fn perms() -> Vec<Vec<u8>> {
    let mut out = vec![];
    fn r(p: &mut Vec<u8>, rest: &mut Vec<u8>, out: &mut Vec<Vec<u8>>) {
        if rest.is_empty() { out.push(p.clone()); return; }
        for i in 0..rest.len() { let c = rest.remove(i); p.push(c); r(p, rest, out); p.pop(); rest.insert(i, c); }
    }
    r(&mut vec![], &mut KINDS.to_vec(), &mut out);
    out
}

struct Board { vec: Vec<u8>, j: [[u64; 10]; 4], bt: [[u64; 10]; 4], mate: usize }

fn limit(bk: usize) -> u8 { [0, 1, 2, INF - 1][bk] }

fn tab_of(boards: &[Board], bk: usize) -> Tab {
    let lim = limit(bk);
    let mut t = Tab { j: vec![], key: vec![], av: vec![] };
    for b in boards {
        let mut j = vec![0u32; B]; let mut k = vec![0u64; B]; let mut a = vec![false; B];
        for o in 0..B {
            let s = b.vec[o];
            if s <= lim { a[o] = true; j[o] = b.j[bk][s as usize] as u32; k[o] = b.j[bk][s as usize] << SH | b.bt[bk][s as usize]; }
        }
        t.j.push(j); t.key.push(k); t.av.push(a);
    }
    t
}

/// the candidate table: per order the best key over the pair's boards (J-major, so also the best J)
fn pair_tab(tb: &Tab, cands: &[Vec<usize>]) -> Tab {
    let mut t = Tab { j: vec![], key: vec![], av: vec![] };
    for c in cands {
        let mut k = vec![0u64; B]; let mut a = vec![false; B];
        for o in 0..B { for &i in c { if tb.av[i][o] { a[o] = true; if tb.key[i][o] > k[o] { k[o] = tb.key[i][o]; } } } }
        t.j.push(k.iter().map(|&x| (x >> SH) as u32).collect()); t.key.push(k); t.av.push(a);
    }
    t
}

fn union(cands: &[Vec<usize>], set: &[usize]) -> Vec<usize> {
    let mut u: Vec<usize> = set.iter().flat_map(|&c| cands[c].iter().cloned()).collect();
    u.sort(); u.dedup(); u
}

fn dominates(key: &Tab, v: usize, u: usize) -> bool {
    let (kv, ku) = (&key.key[v], &key.key[u]);
    let mut eq = true;
    for o in 0..B { if kv[o] < ku[o] { return false; } if kv[o] != ku[o] { eq = false; } }
    !eq || v < u
}

/// (pc3, built) of the set (positions ascending).
pub fn value(t: &Tab, set: &[usize]) -> (u64, u64) {
    let (mut p, mut b) = (0u64, 0u64);
    for o in 0..B {
        let mut m = 0u64;
        for &i in set { let k = t.key[i][o]; if k > m { m = k; } }
        p += m >> SH; b += m & 8191;
    }
    (p, b)
}

fn picks(t: &Tab, set: &[usize]) -> Vec<i32> {
    (0..B).map(|o| {
        let mut best: i64 = -1; let mut arg = -1i32;
        for (m, &i) in set.iter().enumerate() {
            if !t.av[i][o] { continue; }
            let k = t.key[i][o] as i64;
            if k > best { best = k; arg = m as i32; }
        }
        arg
    }).collect()
}

type Val = (u64, u64);
fn better(a: Val, b: Val) -> bool { a > b } // (pc3, built) lexicographic

/// The exact best k-set among `cand` (positions ascending), k = 1, 2, 3.
pub fn exact(t: &Tab, cand: &[usize], k: usize, seed: Option<Vec<usize>>) -> Vec<usize> {
    let n = cand.len();
    let mut best: Option<(Val, Vec<usize>)> = seed.map(|s| (value(t, &s), s));
    let consider = |set: Vec<usize>, v: Val, best: &mut Option<(Val, Vec<usize>)>| {
        let take = match best { None => true, Some((bv, bs)) => better(v, *bv) || (v == *bv && set < *bs) };
        if take { *best = Some((v, set)); }
    };
    let f1: Vec<u64> = cand.iter().map(|&i| t.j[i].iter().map(|&x| x as u64).sum()).collect();
    if k == 1 {
        for a in 0..n { let s = vec![cand[a]]; let v = value(t, &s); consider(s, v, &mut best); }
        return best.unwrap().1;
    }
    let pair = |a: usize, b: usize| -> u64 { t.j[cand[a]].iter().zip(&t.j[cand[b]]).map(|(&x, &y)| x.max(y) as u64).sum() };
    let mut f2 = vec![0u64; n * n];
    for a in 0..n { for b in a + 1..n { let v = pair(a, b); f2[a * n + b] = v; f2[b * n + a] = v; } }
    if k == 2 {
        for a in 0..n { for b in a + 1..n {
            if let Some((bv, _)) = &best { if f2[a * n + b] < bv.0 { continue; } }
            let s = vec![cand[a], cand[b]]; let v = value(t, &s); consider(s, v, &mut best);
        } }
        return best.unwrap().1;
    }
    for a in 0..n { for b in a + 1..n {
        let fab = f2[a * n + b];
        for c in b + 1..n {
            let ub = fab + (f2[a * n + c] - f1[a]).min(f2[b * n + c] - f1[b]);
            if let Some((bv, _)) = &best { if ub < bv.0 { continue; } }
            let s = vec![cand[a], cand[b], cand[c]]; let v = value(t, &s); consider(s, v, &mut best);
        }
    } }
    best.unwrap().1
}

pub fn exact_brute3(t: &Tab, cand: &[usize]) -> (Val, Vec<usize>) {
    let n = cand.len(); let mut best: Option<(Val, Vec<usize>)> = None;
    for a in 0..n { for b in a + 1..n { for c in b + 1..n {
        let s = vec![cand[a], cand[b], cand[c]]; let v = value(t, &s);
        if best.as_ref().map_or(true, |(bv, _)| better(v, *bv)) { best = Some((v, s)); }
    } } }
    best.unwrap()
}

/// add the best board to `set`; ties to the smaller position
fn grow(t: &Tab, cand: &[usize], set: &[usize]) -> Vec<usize> {
    let mut best: Option<(Val, Vec<usize>)> = None;
    for &c in cand {
        if set.contains(&c) { continue; }
        let mut s = set.to_vec(); s.push(c); s.sort();
        let v = value(t, &s);
        if best.as_ref().map_or(true, |(bv, _)| better(v, *bv)) { best = Some((v, s)); }
    }
    best.unwrap().1
}

// ---- the tree -------------------------------------------------------------------------------------------------------------
pub const NF: usize = 28;
pub fn feature_names() -> Vec<String> {
    let mut v = vec![];
    for i in 0..7 { for j in i + 1..7 { v.push(format!("{}<{}", KINDS[i] as char, KINDS[j] as char)); } }
    for i in 0..7 { v.push(format!("first={}", KINDS[i] as char)); }
    v
}
fn features(ps: &[Vec<u8>]) -> Vec<[bool; NF]> {
    ps.iter().map(|p| {
        let pos = |k: u8| p.iter().position(|&c| c == k).unwrap();
        let mut f = [false; NF]; let mut x = 0;
        for i in 0..7 { for j in i + 1..7 { f[x] = pos(KINDS[i]) < pos(KINDS[j]); x += 1; } }
        for i in 0..7 { f[x] = p[0] == KINDS[i]; x += 1; }
        f
    }).collect()
}
pub enum Node { Leaf(usize), Split(usize, Box<Node>, Box<Node>) }
struct TreeCtx<'a> { val: Vec<Vec<u128>>, f: &'a [[bool; NF]] }
impl<'a> TreeCtx<'a> {
    fn leaf(&self, sub: &[u16]) -> (u128, usize) {
        let mut best = (0u128, 0usize);
        for m in 0..self.val.len() {
            let s: u128 = sub.iter().map(|&o| self.val[m][o as usize]).sum();
            if m == 0 || s > best.0 { best = (s, m); }
        }
        best
    }
    fn split(&self, sub: &[u16], f: usize) -> (Vec<u16>, Vec<u16>) {
        let (mut y, mut n) = (vec![], vec![]);
        for &o in sub { if self.f[o as usize][f] { y.push(o) } else { n.push(o) } }
        (y, n)
    }
    fn value(&self, sub: &[u16], d: usize) -> u128 {
        let mut best = self.leaf(sub).0;
        if d == 0 { return best; }
        for f in 0..NF {
            let (y, n) = self.split(sub, f);
            if y.is_empty() || n.is_empty() { continue; }
            let v = self.value(&y, d - 1) + self.value(&n, d - 1);
            if v > best { best = v; }
        }
        best
    }
    fn build(&self, sub: &[u16], d: usize) -> Node {
        let (lv, lm) = self.leaf(sub);
        let mut best = lv; let mut bf = None;
        if d > 0 { for f in 0..NF {
            let (y, n) = self.split(sub, f);
            if y.is_empty() || n.is_empty() { continue; }
            let v = self.value(&y, d - 1) + self.value(&n, d - 1);
            if v > best { best = v; bf = Some(f); }
        } }
        match bf {
            None => Node::Leaf(lm),
            Some(f) => { let (y, n) = self.split(sub, f); Node::Split(f, Box::new(self.build(&y, d - 1)), Box::new(self.build(&n, d - 1))) }
        }
    }
}
fn walk<'a>(n: &'a Node, f: &[bool; NF]) -> usize { match n { Node::Leaf(m) => *m, Node::Split(i, y, no) => walk(if f[*i] { y } else { no }, f) } }
fn node_json(n: &Node) -> String {
    match n { Node::Leaf(m) => format!("{{\"m\":{}}}", m),
        Node::Split(f, y, no) => format!("{{\"f\":{},\"y\":{},\"n\":{}}}", f, node_json(y), node_json(no)) }
}

fn jlist(v: &[usize]) -> String { format!("[{}]", v.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(",")) }
fn setj(t: &Tab, cands: &[Vec<usize>], s: &[usize], k: usize) -> String {
    let (p, b) = value(t, s);
    format!("{{\"k\":{},\"set\":{},\"ub\":{},\"pc3\":{},\"built\":{}}}", k, jlist(s), jlist(&union(cands, s)), p, b)
}

fn parse(line: &str) -> Board {
    let f: Vec<&str> = line.split('|').collect();
    assert_eq!(f.len(), 7, "board line fields");
    let vec: Vec<u8> = f[1].bytes().map(|c| if c == b'.' { INF } else { c - b'0' }).collect();
    assert_eq!(vec.len(), B);
    let mut j = [[0u64; 10]; 4]; let mut bt = [[0u64; 10]; 4];
    for bk in 0..4 {
        let (a, b) = f[2 + bk].split_once('/').unwrap();
        for (i, x) in a.split(',').enumerate() { j[bk][i] = x.parse().unwrap(); }
        for (i, x) in b.split(',').enumerate() { bt[bk][i] = x.parse().unwrap(); }
    }
    Board { vec, j, bt, mate: f[6].parse().unwrap() }
}

fn main() {
    let t0 = std::time::Instant::now();
    let boards: Vec<Board> = std::io::stdin().lock().lines().map(|l| l.unwrap()).filter(|l| !l.is_empty()).map(|l| parse(&l)).collect();
    let n = boards.len();
    let mut cands: Vec<Vec<usize>> = vec![];
    for i in 0..n { let m = boards[i].mate; assert!(m < n && boards[m].mate == i, "mate is an involution");
        if m >= i { cands.push(if m == i { vec![i] } else { vec![i, m] }); } }
    let nc = cands.len();
    let ps = perms();
    let feats = features(&ps);
    let bks = ["0", "1", "2", "inf"];
    let mut sets3: Vec<Vec<usize>> = vec![];
    let mut out = String::from("{\"boards\":");
    out += &n.to_string();
    out += &format!(",\"cands\":{},\"pairs\":{}", nc, format!("[{}]", cands.iter().map(|c| jlist(c)).collect::<Vec<_>>().join(",")));
    out += ",\"features\":[";
    out += &feature_names().iter().map(|s| format!("\"{}\"", s)).collect::<Vec<_>>().join(",");
    out += "],\"budgets\":{";
    for bk in 0..4 {
        let tb = tab_of(&boards, bk);
        let t = pair_tab(&tb, &cands);
        let n = nc;
        // dominance
        let mut dominated = vec![false; n];
        for u in 0..n { for v in 0..n { if v != u && dominates(&t, v, u) { dominated[u] = true; break; } } }
        let reduced: Vec<usize> = (0..n).filter(|&i| !dominated[i]).collect();
        let mut dom_pairs = vec![];
        for u in 0..n { if dominated[u] {
            let v = *reduced.iter().find(|&&v| dominates(&t, v, u)).expect("a maximal dominator");
            dom_pairs.push((u, v));
        } }
        eprintln!("budget {}: {} boards, {} reduced ({:?})", bks[bk], n, reduced.len(), t0.elapsed());
        // greedy chain
        let mut chain: Vec<Vec<usize>> = vec![];
        let mut s: Vec<usize> = vec![];
        for _ in 0..5 { s = grow(&t, &reduced, &s); chain.push(s.clone()); }
        // exact
        let e1 = exact(&t, &reduced, 1, None);
        let e2 = exact(&t, &reduced, 2, Some(chain[1].clone()));
        let e3 = exact(&t, &reduced, 3, Some(chain[2].clone()));
        eprintln!("  exact done ({:?})", t0.elapsed());
        let g4 = grow(&t, &reduced, &e3); let g5 = grow(&t, &reduced, &g4);
        let ub = union(&cands, &e3);
        let pk = picks(&tb, &ub);
        let pk_s: String = pk.iter().map(|&m| if m < 0 { 'x' } else { (b'0' + m as u8) as char }).collect();
        // trees on the exact triple
        let val: Vec<Vec<u128>> = ub.iter().map(|&i| (0..B).map(|o| if tb.av[i][o] { (tb.key[i][o] >> SH) as u128 * (1u128 << 26) + (tb.key[i][o] & 8191) as u128 } else { 0 }).collect()).collect();
        let ctx = TreeCtx { val, f: &feats };
        let all: Vec<u16> = (0..B as u16).collect();
        let mut trees = vec![];
        for d in 1..=3 {
            let tree = ctx.build(&all, d);
            let (mut p, mut b, mut diff, mut unb) = (0u64, 0u64, 0u64, 0u64);
            for o in 0..B {
                let m = walk(&tree, &feats[o]); let i = ub[m];
                if tb.av[i][o] { p += tb.j[i][o] as u64; b += tb.key[i][o] & 8191; } else { unb += 1; }
                if pk[o] >= 0 && pk[o] as usize != m { diff += 1; }
            }
            trees.push(format!("{{\"depth\":{},\"pc3\":{},\"built\":{},\"differs\":{},\"unbuildable\":{},\"tree\":{}}}", d, p, b, diff, unb, node_json(&tree)));
        }
        sets3.push(e3.clone());
        if bk > 0 { out += ","; }
        out += &format!("\"{}\":{{\"reduced\":{},\"dominated\":[{}],", bks[bk], reduced.len(),
            dom_pairs.iter().map(|(u, v)| format!("[{},{}]", u, v)).collect::<Vec<_>>().join(","));
        out += &format!("\"exact\":[{},{},{}],", setj(&t, &cands, &e1, 1), setj(&t, &cands, &e2, 2), setj(&t, &cands, &e3, 3));
        out += &format!("\"greedy\":[{}],", chain.iter().enumerate().map(|(i, s)| setj(&t, &cands, s, i + 1)).collect::<Vec<_>>().join(","));
        out += &format!("\"from_exact3\":[{},{}],", setj(&t, &cands, &g4, 4), setj(&t, &cands, &g5, 5));
        out += &format!("\"ub\":{},\"picks\":\"{}\",\"trees\":[{}]}}", jlist(&ub), pk_s, trees.join(","));
        eprintln!("  budget {} done ({:?})", bks[bk], t0.elapsed());
    }
    // the set learnt for the default budget (<= 2 soft drops), valued at every budget
    out += "},\"fixed\":{\"budget\":\"2\",\"set\":";
    out += &jlist(&sets3[2]);
    out += &format!(",\"ub\":{}", jlist(&union(&cands, &sets3[2])));
    out += ",\"values\":{";
    for bk in 0..4 {
        let t = pair_tab(&tab_of(&boards, bk), &cands);
        let (p, b) = value(&t, &sets3[2]);
        if bk > 0 { out += ","; }
        out += &format!("\"{}\":{{\"pc3\":{},\"built\":{}}}", bks[bk], p, b);
    }
    out += "}}}\n";
    std::io::stdout().write_all(out.as_bytes()).unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;
    // xorshift
    struct R(u64);
    impl R { fn n(&mut self) -> u64 { self.0 ^= self.0 << 13; self.0 ^= self.0 >> 7; self.0 ^= self.0 << 17; self.0 } }
    fn synth(n: usize, seed: u64) -> Tab {
        let mut r = R(seed);
        let (mut j, mut key, mut av) = (vec![], vec![], vec![]);
        for _ in 0..n {
            let mut jj = vec![0u32; B]; let mut kk = vec![0u64; B]; let mut aa = vec![false; B];
            let density = 1 + r.n() % 6;
            for o in 0..B { if r.n() % 7 < density { aa[o] = true; let v = r.n() % 50_000; jj[o] = v as u32; kk[o] = (v << SH) | (r.n() % 5041); } }
            j.push(jj); key.push(kk); av.push(aa);
        }
        Tab { j, key, av }
    }
    #[test]
    fn branch_and_bound_equals_brute_force() {
        for seed in [1u64, 7, 99, 12345] {
            let t = synth(40, seed * 2654435761);
            let cand: Vec<usize> = (0..40).collect();
            let bf = exact_brute3(&t, &cand);
            let bb = exact(&t, &cand, 3, None);
            assert_eq!(value(&t, &bb), bf.0, "seed {}", seed);
            assert_eq!(bb, bf.1, "tie rule, seed {}", seed);
            let seeded = exact(&t, &cand, 3, Some(vec![0, 1, 2]));
            assert_eq!(seeded, bf.1);
        }
    }
    #[test]
    fn pair_candidates_value_the_union_of_their_boards() {
        let tb = synth(12, 31337);
        let cands: Vec<Vec<usize>> = vec![vec![0, 1], vec![2], vec![3, 4], vec![5, 6], vec![7], vec![8, 9]];
        let tp = pair_tab(&tb, &cands);
        for set in [vec![0usize, 2], vec![1, 3, 5], vec![0, 1, 2, 3]] {
            assert_eq!(value(&tp, &set), value(&tb, &union(&cands, &set)));
        }
    }
    #[test]
    fn pairs_equal_brute_force() {
        let t = synth(40, 424242);
        let cand: Vec<usize> = (0..40).collect();
        let mut best: Option<(Val, Vec<usize>)> = None;
        for a in 0..40 { for b in a + 1..40 { let s = vec![a, b]; let v = value(&t, &s); if best.as_ref().map_or(true, |(bv, _)| better(v, *bv)) { best = Some((v, s)); } } }
        assert_eq!(exact(&t, &cand, 2, None), best.unwrap().1);
    }
    #[test]
    fn depth1_tree_is_brute_force() {
        let t = synth(3, 5);
        let ps = perms(); let f = features(&ps);
        let val: Vec<Vec<u128>> = (0..3).map(|i| (0..B).map(|o| if t.av[i][o] { (t.key[i][o] >> SH) as u128 * (1u128 << 26) + (t.key[i][o] & 8191) as u128 } else { 0 }).collect()).collect();
        let ctx = TreeCtx { val: val.clone(), f: &f };
        let all: Vec<u16> = (0..B as u16).collect();
        let mut best = 0u128;
        for fi in 0..NF { let mut s = [[0u128; 3]; 2]; for o in 0..B { for m in 0..3 { s[f[o][fi] as usize][m] += val[m][o]; } }
            best = best.max(s[0].iter().max().unwrap() + s[1].iter().max().unwrap()); }
        let leaf: u128 = (0..3).map(|m| val[m].iter().sum::<u128>()).max().unwrap();
        assert_eq!(ctx.value(&all, 1), best.max(leaf));
    }
}

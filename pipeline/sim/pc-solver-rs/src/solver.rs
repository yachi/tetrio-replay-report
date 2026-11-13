//! pc-solver.ts `apply`, `regionsOk`, `solve`, `frames`, and pc-miss.ts `check`, ported so that
//! every answer (verdict, H, plan, placement order) equals the TS one.
//!
//! Semantics kept on purpose, each of which changes an answer if "fixed":
//! - the `need` (sequence too short) test runs BEFORE the memo lookup, sets `short` and stores nothing;
//! - a memo hit returns the stored plan-or-false WITHOUT touching `short`, so a false stored because a
//!   deeper node ran short reads as a plain false on a later hit;
//! - the budget is decremented only on a memo miss, and running out is an error that leaves every memo
//!   entry already written in place (the TS `throw`), caught per frame by `check`;
//! - `apply` trims trailing empty rows, which is part of the memo key.
use std::collections::HashMap;
use std::hash::{BuildHasherDefault, Hasher};

use crate::srs::{piece_index, srs_placements, PIECES};

pub const W: i32 = 10;
const FULL: u16 = (1 << W) - 1;
pub const NONE: u8 = 0xFF;
/// Rows a memo key can hold (10 bits each in a u128 beside H, cur, hold, ptr).
pub const MAX_ROWS: usize = 8;

/// FxHash (rustc's hasher), written inline.
#[derive(Default, Clone, Copy)]
pub struct Fx(u64);
impl Hasher for Fx {
    #[inline]
    fn write(&mut self, bytes: &[u8]) { for &b in bytes { self.write_u64(b as u64); } }
    #[inline]
    fn write_u64(&mut self, i: u64) { self.0 = (self.0.rotate_left(5) ^ i).wrapping_mul(0x51_7c_c1_b7_27_22_0a_95); }
    #[inline]
    fn write_u128(&mut self, i: u128) { self.write_u64(i as u64); self.write_u64((i >> 64) as u64); }
    #[inline]
    fn finish(&self) -> u64 { self.0 }
}
pub type FxBuild = BuildHasherDefault<Fx>;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Pl { pub piece: u8, pub cells: [u8; 4], pub held: bool }

/// The per-round-player memo (TS `Map<string, Placement[] | false>`). `None` = false.
#[derive(Default)]
pub struct Memo { pub m: HashMap<u128, Option<Box<[Pl]>>, FxBuild> }

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Gen { Srs, Engine }

#[derive(Debug, PartialEq, Eq)]
pub enum Verdict { Ok { h: i32, plan: Vec<Pl> }, False, Short }

pub struct Budget;

// ── movegen caches (a cache never changes an answer) ──
type GenCache = HashMap<(u128, u8, i32), std::rc::Rc<[[u8; 4]]>, FxBuild>;
thread_local! {
    static SRS_CACHE: std::cell::RefCell<GenCache> = Default::default();
    static ENG_CACHE: std::cell::RefCell<GenCache> = Default::default();
}

fn rows_key(rows: &[u16]) -> u128 {
    assert!(rows.len() <= MAX_ROWS, "board too tall for the key");
    let mut k: u128 = rows.len() as u128;
    for (i, &m) in rows.iter().enumerate() { k |= (m as u128 & 0x3ff) << (4 + 10 * i); }
    k
}

fn engine_gen(rows: &[u16], piece: u8, h: i32) -> Vec<[u8; 4]> {
    crate::engine_gen::engine_placements(rows, piece, h as usize)
        .into_iter()
        .map(|c| { assert!(c.len() == 4); [c[0] as u8, c[1] as u8, c[2] as u8, c[3] as u8] })
        .collect()
}

pub fn placements(gen: Gen, rows: &[u16], piece: u8, h: i32) -> std::rc::Rc<[[u8; 4]]> {
    let key = (rows_key(rows), piece, h);
    let cache = match gen { Gen::Srs => &SRS_CACHE, Gen::Engine => &ENG_CACHE };
    if let Some(v) = cache.with(|c| c.borrow().get(&key).cloned()) { return v; }
    let v: std::rc::Rc<[[u8; 4]]> = match gen {
        Gen::Srs => srs_placements(rows, piece_index(piece).expect("bad piece"), h).into(),
        Gen::Engine => engine_gen(rows, piece, h).into(),
    };
    cache.with(|c| {
        let mut c = c.borrow_mut();
        if c.len() > 200_000 { c.clear(); }
        c.insert(key, v.clone());
    });
    v
}

/// pc-solver.ts `apply`: place, clear full rows (rows padded to H), trim trailing empty rows.
pub fn apply(rows: &[u16], cells: &[u8; 4], h: i32, out: &mut Vec<u16>) -> i32 {
    out.clear();
    out.extend_from_slice(rows);
    while (out.len() as i32) < h { out.push(0); }
    for &c in cells { out[(c as i32 / W) as usize] |= 1 << (c as i32 % W); }
    let before = out.len();
    out.retain(|&m| m != FULL);
    let cleared = (before - out.len()) as i32;
    while out.last() == Some(&0) { out.pop(); }
    h - cleared
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
        empty[s] = 0;
        st.push(s);
        while let Some(c) = st.pop() {
            cnt += 1;
            let x = c % 10;
            let y = c / 10;
            if x > 0 && empty[c - 1] != 0 { empty[c - 1] = 0; st.push(c - 1); }
            if x < 9 && empty[c + 1] != 0 { empty[c + 1] = 0; st.push(c + 1); }
            if y > 0 && empty[c - 10] != 0 { empty[c - 10] = 0; st.push(c - 10); }
            if (y as i32) < h - 1 && empty[c + 10] != 0 { empty[c + 10] = 0; st.push(c + 10); }
        }
        if cnt % 4 != 0 { return false; }
    }
    true
}

pub fn filled(rows: &[u16]) -> i32 { rows.iter().map(|m| (m & 0x3ff).count_ones() as i32).sum() }
pub fn height(rows: &[u16]) -> i32 { let mut h = rows.len(); while h > 0 && rows[h - 1] == 0 { h -= 1; } h as i32 }

pub fn frames(rows: &[u16], max_h: i32) -> Vec<i32> {
    let (h, n) = (height(rows), filled(rows));
    (h.max(1)..=max_h).filter(|&hh| (hh * W - n) % 4 == 0 && hh * W - n > 0).collect()
}

#[inline]
fn pcode(p: u8) -> u128 { PIECES.iter().position(|&q| q == p).map(|i| i as u128 + 1).unwrap_or(0) }

struct Ctx<'a> { seq: &'a [u8], memo: &'a mut Memo, nodes: i64, short: bool, gen: Gen, buf: Vec<Vec<u16>> }

impl Ctx<'_> {
    #[inline]
    fn at(&self, i: i64) -> u8 { if i >= 0 && (i as usize) < self.seq.len() { self.seq[i as usize] } else { NONE } }

    /// Returns Ok(None) for false, Ok(Some(plan)) for a plan (pushed onto `plan` in REVERSE order:
    /// the caller reverses), Err on budget.
    fn rec(&mut self, rows: &[u16], h: i32, cur: u8, hold: u8, ptr: i64, depth: usize) -> Result<Option<Vec<Pl>>, Budget> {
        if h == 0 && rows.is_empty() { return Ok(Some(Vec::new())); }
        if !regions_ok(rows, h) { return Ok(None); }
        let need4 = (h * W - filled(rows)) as i64; // need = need4 / 4
        let avail = self.seq.len() as i64 - ptr + 1 + if hold != NONE { 1 } else { 0 };
        if avail * 4 < need4 { self.short = true; return Ok(None); }
        assert!(rows.len() <= MAX_ROWS && h <= 15);
        let key = rows_key(rows) | (h as u128) << 84 | pcode(cur) << 88 | pcode(hold) << 91 | ((ptr as u64 as u128) & 0xFFFF_FFFF) << 94;
        if let Some(m) = self.memo.m.get(&key) {
            return Ok(m.as_ref().map(|p| p.to_vec()));
        }
        self.nodes -= 1;
        if self.nodes < 0 { return Err(Budget); }
        // [placed, newHold, nextCur, nextPtr, held]
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
            let list = placements(self.gen, rows, pc, h);
            for cells in list.iter() {
                let mut a = std::mem::take(&mut self.buf[depth]);
                let ah = apply(rows, cells, h, &mut a);
                let me = Pl { piece: pc, cells: *cells, held };
                if ah == 0 && a.is_empty() {
                    self.buf[depth] = a;
                    let r = vec![me];
                    self.memo.m.insert(key, Some(r.clone().into_boxed_slice()));
                    return Ok(Some(r));
                }
                if nc == NONE { self.short = true; self.buf[depth] = a; continue; }
                let sub = self.rec(&a, ah, nc, nh, np, depth + 1);
                self.buf[depth] = a;
                if let Some(sub) = sub? {
                    let mut r = Vec::with_capacity(sub.len() + 1);
                    r.push(me);
                    r.extend_from_slice(&sub);
                    self.memo.m.insert(key, Some(r.clone().into_boxed_slice()));
                    return Ok(Some(r));
                }
            }
        }
        self.memo.m.insert(key, None);
        Ok(None)
    }
}

/// pc-solver.ts `solve`. Err(Budget) = the TS `throw new Error('budget')`.
pub fn solve(rows: &[u16], h: i32, cur: u8, hold: u8, seq: &[u8], ptr: i64, memo: &mut Memo, nodes: i64, gen: Gen) -> Result<Verdict, Budget> {
    let mut cx = Ctx { seq, memo, nodes, short: false, gen, buf: Vec::new() };
    let r = cx.rec(rows, h, cur, hold, ptr, 0)?;
    Ok(match r {
        Some(plan) => Verdict::Ok { h, plan },
        None => if cx.short { Verdict::Short } else { Verdict::False },
    })
}

/// pc-miss.ts `check`: every frame up to `max_h`, a fresh budget per frame, a budget error marks the
/// answer unknown and moves on to the next frame.
pub fn check(rows: &[u16], cur: u8, hold: u8, seq: &[u8], ptr: i64, memo: &mut Memo, max_h: i32, nodes: i64, gen: Gen) -> Verdict {
    let mut unknown = false;
    for h in frames(rows, max_h) {
        match solve(rows, h, cur, hold, seq, ptr, memo, nodes, gen) {
            Err(Budget) => { unknown = true; }
            Ok(Verdict::Ok { h, plan }) => return Verdict::Ok { h, plan },
            Ok(Verdict::Short) => unknown = true,
            Ok(Verdict::False) => {}
        }
    }
    if unknown { Verdict::Short } else { Verdict::False }
}

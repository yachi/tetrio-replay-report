//! The C ABI `oracle-native.ts` loads through bun:ffi. Nothing here may panic (the crate is built
//! with panic = "abort", which would take bun down with it): every malformed buffer is answered with
//! status 3, and the harness invariant oracle-source.ts throws for is status 2.
//!
//! Input `opts` (f64, `OPTS_LEN` values, in `engine::Opts` field order; booleans are 0/1) and
//! `events` (f64): a sequence of records `[frame, kind, ...]` with
//!   kind 1 keydown  [subframe, key, hoisted]       kind 2 keyup [subframe, key]
//!   kind 3 interaction:garbage [gameid, ackiid, amt, iid, size]
//!   kind 4 interaction_confirm:garbage [iid, gameid, frame]
//!   kind 5 target [n, id_1 .. id_n]
//! in replay order. Output (f64): `[status, topout, nLocks, nGarbageEvents, nSnaps]`, then per lock
//! `[frame, piece, lines, spin, sent, b2b, combo, garbageCleared, allclear, snap, c0, r0 .. c3, r3,
//! nCleared, rows..]`, per garbage event `[frame, amt, lockIndex]`, then each snapshot's 400 cell codes
//! and 400 provenance values.
use crate::engine::{self, Ev, Fatal, Opts, Spin};

pub const OPTS_LEN: usize = 43;
const MAX_FRAMES: f64 = 10_000_000.0;

pub struct Out { data: Vec<f64> }

fn b(x: f64) -> bool { x != 0.0 }

fn opts_from(v: &[f64]) -> Option<Opts> {
    if v.len() != OPTS_LEN { return None; }
    let mut i = 0usize;
    let mut n = || { let x = v[i]; i += 1; x };
    let o = Opts {
        seed: n(), gameid: n(),
        g: n(), gincrease: n(), gmargin: n(),
        gmult: n(), gmult_increase: n(), gmult_margin: n(),
        gcap: n(), gcap_increase: n(), gcap_margin: n(), gcap_max: n(), gcap_absolute: n(),
        gspeed: n(), hole_size: n(), mess_change: n(), mess_within: n(), mess_timeout: n(),
        nosame: b(n()), center: b(n()), opener_phase: n(),
        allclears: b(n()), allclear_garbage: n(), allclear_b2b: n(), b2b_chaining: b(n()),
        clutch: b(n()), lock_resets: n(), lock_time: n(), infinite: b(n()), may20g_mode: b(n()),
        allow180: b(n()), allow_harddrop: b(n()), allow_hold: b(n()), infinite_hold: b(n()),
        arr: n(), das: n(), dcd: n(), sdf: n(), safelock: b(n()), cancel: b(n()), hmay20g: b(n()),
        max_frame: n(), network: b(n()),
    };
    if !(o.max_frame >= -1.0 && o.max_frame <= MAX_FRAMES) || o.max_frame.fract() != 0.0 { return None; }
    if v.iter().any(|x| !x.is_finite()) { return None; }
    Some(o)
}

fn key_of(x: f64) -> Option<u8> {
    if x >= 0.0 && x <= 255.0 && x.fract() == 0.0 { Some(x as u8) } else { None }
}

fn events_from(v: &[f64], max_frame: f64) -> Option<Vec<Vec<Ev>>> {
    let n_frames = if max_frame < 0.0 { 0 } else { max_frame as usize + 1 };
    let mut frames: Vec<Vec<Ev>> = (0..n_frames).map(|_| Vec::new()).collect();
    let mut i = 0usize;
    let take = |i: &mut usize, k: usize| -> Option<&[f64]> {
        if *i + k > v.len() { return None; }
        let s = &v[*i..*i + k];
        *i += k;
        Some(s)
    };
    while i < v.len() {
        let h = take(&mut i, 2)?;
        let (frame, kind) = (h[0], h[1]);
        if !(frame >= 0.0 && frame <= max_frame && frame.fract() == 0.0) { return None; }
        let ev = match kind as i64 {
            1 => { let a = take(&mut i, 3)?; Ev::KeyDown { sub: a[0], key: key_of(a[1])?, hoisted: b(a[2]) } }
            2 => { let a = take(&mut i, 2)?; Ev::KeyUp { sub: a[0], key: key_of(a[1])? } }
            3 => { let a = take(&mut i, 5)?; Ev::Interaction { gameid: a[0], ackiid: a[1], amt: a[2], iid: a[3], size: a[4] } }
            4 => { let a = take(&mut i, 3)?; Ev::Confirm { iid: a[0], gameid: a[1], frame: a[2] } }
            5 => {
                let n = take(&mut i, 1)?[0];
                if !(n >= 0.0 && n.fract() == 0.0 && n <= v.len() as f64) { return None; }
                Ev::Target { ids: take(&mut i, n as usize)?.to_vec() }
            }
            _ => return None,
        };
        if kind.fract() != 0.0 { return None; }
        frames.get_mut(frame as usize)?.push(ev);
    }
    Some(frames)
}

fn spin_code(s: Spin) -> f64 { match s { Spin::None => 0.0, Spin::Mini => 1.0, Spin::Normal => 2.0 } }

fn run_encoded(opts: &[f64], events: &[f64]) -> Vec<f64> {
    let o = match opts_from(opts) { Some(o) => o, None => return vec![3.0, 0.0, 0.0, 0.0, 0.0] };
    let frames = match events_from(events, o.max_frame) { Some(f) => f, None => return vec![3.0, 0.0, 0.0, 0.0, 0.0] };
    let (eng, out) = match engine::run(&o, &frames) {
        Ok(r) => r,
        Err(Fatal::NoPreTick) => return vec![2.0, 0.0, 0.0, 0.0, 0.0],
    };
    let mut d = Vec::with_capacity(5 + eng.locks.len() * 24 + eng.garbage_events.len() * 3 + out.engine_snaps.len());
    d.extend_from_slice(&[0.0, if eng.topout { 1.0 } else { 0.0 }, eng.locks.len() as f64, eng.garbage_events.len() as f64, out.n_snaps as f64]);
    for l in &eng.locks {
        d.extend_from_slice(&[l.frame, l.piece as f64, l.lines, spin_code(l.spin), l.sent, l.b2b, l.combo,
            l.garbage_cleared, if l.allclear { 1.0 } else { 0.0 }, l.snap as f64]);
        for &(c, r) in l.cells.iter() { d.push(c as f64); d.push(r as f64); }
        d.push(l.cleared_rows.len() as f64);
        for &r in &l.cleared_rows { d.push(r as f64); }
    }
    for g in &eng.garbage_events { d.extend_from_slice(&[g.frame, g.amt, g.lock_index as f64]); }
    d.extend_from_slice(&out.engine_snaps);
    d
}

/// # Safety
/// `opts` must point to `n_opts` f64 and `events` to `n_events` f64 (either may be null when its
/// length is 0). The returned handle is freed with `oracle_free`.
#[no_mangle]
pub unsafe extern "C" fn oracle_run(opts: *const f64, n_opts: u32, events: *const f64, n_events: u32) -> *mut Out {
    let o: &[f64] = if opts.is_null() || n_opts == 0 { &[] } else { std::slice::from_raw_parts(opts, n_opts as usize) };
    let e: &[f64] = if events.is_null() || n_events == 0 { &[] } else { std::slice::from_raw_parts(events, n_events as usize) };
    Box::into_raw(Box::new(Out { data: run_encoded(o, e) }))
}

/// # Safety
/// `h` must be a handle from `oracle_run` not yet freed.
#[no_mangle]
pub unsafe extern "C" fn oracle_out_len(h: *const Out) -> f64 {
    if h.is_null() { return -1.0; }
    (*h).data.len() as f64
}

/// Copies the output into `dst` (room for `len` f64); returns the number copied, -1 if it does not fit.
/// # Safety
/// `h` as for `oracle_out_len`; `dst` must have room for `len` f64.
#[no_mangle]
pub unsafe extern "C" fn oracle_out_copy(h: *const Out, dst: *mut f64, len: u32) -> i32 {
    if h.is_null() || dst.is_null() { return -1; }
    let d = &(*h).data;
    if d.len() > len as usize { return -1; }
    std::ptr::copy_nonoverlapping(d.as_ptr(), dst, d.len());
    d.len() as i32
}

/// # Safety
/// `h` must be a handle from `oracle_run`, freed at most once.
#[no_mangle]
pub unsafe extern "C" fn oracle_free(h: *mut Out) {
    if !h.is_null() { drop(Box::from_raw(h)); }
}

/// `f64::ln_1p`, the function the garbage formula uses for JS `Math.log1p` (tested bit for bit).
#[no_mangle]
pub extern "C" fn oracle_log1p(x: f64) -> f64 { x.ln_1p() }

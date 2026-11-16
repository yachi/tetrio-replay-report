//! emit-replay.ts's `instrumentEngine` + `runPlayer`, in Rust: the same engine as `engine::run`, ticked
//! to `max_frame` with no harness catch, recording per lock exactly what those hooks record (see
//! pipeline/sim/replay-native.ts, which decodes this into `runPlayer`'s return value).
//!
//! C ABI (nothing may panic): `replay_run(opts, n, events, n)` takes the buffers `oracle_run` takes and
//! returns a handle holding an f64 buffer and a byte buffer.
//!
//! f64: `[status, nLocks, drawn, holdsTotal, pcs, engineTopLock (-1 = none), garbageCleared, seqLen]`,
//! then per lock `[dframe, lines, spin (0 none, 1 mini, 2 full), held, attack, sent, piece, holdAtLock
//! (-1 = empty), nCells, cell.., nGarbage, (column (NaN = null), amount)..]`. A piece is 0..6 = IJLOSTZ;
//! a cell is yUp * 10 + x. Status: 0 ok, 2 a clearing lock with no pre-tick snapshot, 3 a malformed
//! buffer, 4 the engine threw (emit-replay.ts does not catch), 5 a garbage row of size other than 1.
//!
//! bytes: the piece sequence (`seqLen` letters), then per lock the engine board key `engineKey` builds
//! (rows bottom-up joined by '/', '.' empty, 'G' garbage, the piece letter otherwise).
use crate::engine::{self, Ev, Row, Spin, W};
use crate::ffi::{events_from, opts_from};

const LETTER: [u8; 7] = *b"IJLOSTZ";
const GARBAGE: u8 = 7;

#[derive(Default)]
pub struct Trace {
    pub drawn: u32,
    holds_total: u32,
    in_lock: bool,
    cur_held: u8,
    next_held: u8,
    pending: Vec<(Option<f64>, f64)>,
    bad_size: bool,
    pub attack: f64,
    hold_at_lock: i32,
    pre_cells: Vec<i32>,
    last_frame: f64,
    pcs: u32,
    top_lock: i64,
    garbage_cleared: f64,
    n_locks: u32,
    locks: Vec<f64>,
    keys: Vec<u8>,
}

impl Trace {
    /// `falling.new` with isHold: a hold fired while a lock is still being processed belongs to the next piece.
    pub fn on_hold(&mut self) {
        self.holds_total += 1;
        if self.in_lock { self.next_held = 1; } else { self.cur_held = 1; }
    }
    /// the wrapped `board.insertGarbage`
    pub fn on_garbage(&mut self, column: Option<f64>, amount: f64, size: f64) {
        if size != 1.0 { self.bad_size = true; }
        self.pending.push((column, amount));
    }
    /// `falling.lock.pre`
    pub fn on_lock_pre(&mut self, held: Option<usize>, placed: &[(f64, f64); 4]) {
        self.in_lock = true;
        self.hold_at_lock = held.map(|h| h as i32).unwrap_or(-1);
        self.pre_cells.clear();
        for &(x, y) in placed.iter() {
            if x >= 0.0 && x < W as f64 && y >= 0.0 && y < engine::FULL_H as f64 { self.pre_cells.push((y * W as f64 + x) as i32); }
        }
    }
    /// `falling.lock`
    #[allow(clippy::too_many_arguments)]
    pub fn on_lock(&mut self, board: &[Row], frame: f64, piece: usize, lines: f64, spin: Spin, sent: f64,
                   garbage_cleared: f64, allclear: bool, topout: bool, tag: i32) {
        let spin = match spin { Spin::None => 0.0, Spin::Mini => 1.0, Spin::Normal => 2.0 };
        let mut cells: Vec<i32> = Vec::with_capacity(4);
        if lines > 0.0 {
            // the engine inserts garbage only on a non-clearing lock, so the pre-clear cells are exact
            cells.extend_from_slice(&self.pre_cells);
        } else {
            // the cells this lock placed: the only cells not on the board after the previous lock
            for (y, row) in board.iter().enumerate() {
                for (x, c) in row.iter().enumerate() {
                    if let Some(c) = c { if c.mino != GARBAGE && c.tag == tag { cells.push((y * W + x) as i32); } }
                }
            }
        }
        if topout && self.top_lock < 0 { self.top_lock = self.n_locks as i64; }
        self.locks.extend_from_slice(&[frame - self.last_frame, lines, spin, self.cur_held as f64, self.attack, sent,
            piece as f64, self.hold_at_lock as f64, cells.len() as f64]);
        for &c in &cells { self.locks.push(c as f64); }
        self.locks.push(self.pending.len() as f64);
        for &(col, amt) in &self.pending { self.locks.push(col.unwrap_or(f64::NAN)); self.locks.push(amt); }
        self.last_frame = frame;
        for (y, row) in board.iter().enumerate() {
            if y > 0 { self.keys.push(b'/'); }
            for c in row.iter() {
                self.keys.push(match c { None => b'.', Some(c) if c.mino == GARBAGE => b'G', Some(c) => LETTER[c.mino as usize] });
            }
        }
        if allclear && lines > 0.0 { self.pcs += 1; }
        self.garbage_cleared += garbage_cleared;
        self.n_locks += 1;
        self.pending.clear();
        self.cur_held = self.next_held;
        self.next_held = 0;
        self.in_lock = false;
    }
}

pub struct TraceOut { f: Vec<f64>, s: Vec<u8> }

fn fail(status: f64) -> TraceOut { TraceOut { f: vec![status, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0], s: Vec::new() } }

fn run_traced(opts: &[f64], events: &[f64]) -> TraceOut {
    let o = match opts_from(opts) { Some(o) => o, None => return fail(3.0) };
    let frames = match events_from(events, o.max_frame) { Some(f) => f, None => return fail(3.0) };
    let mut eng = match engine::Engine::new(&o) { Ok(e) => e, Err(_) => return fail(4.0) };
    // the constructor dealt the first piece before any hook existed (instrumentEngine reads it off falling)
    eng.trace = Some(Box::new(Trace { drawn: 1, top_lock: -1, hold_at_lock: -1, ..Default::default() }));
    let empty: Vec<Ev> = Vec::new();
    let mut f = 0usize;
    while (f as f64) <= o.max_frame {
        let evs = frames.get(f).unwrap_or(&empty);
        if eng.tick_fresh(evs).is_err() {
            return if eng.take_fatal().is_some() { fail(2.0) } else { fail(4.0) };
        }
        if eng.trace.as_ref().map(|t| t.bad_size).unwrap_or(false) { return fail(5.0); }
        f += 1;
    }
    let t = match eng.trace.take() { Some(t) => t, None => return fail(3.0) };
    // Queue: whole 7-bags, at least five, topped up before each shift while fewer than 31 remain, so
    // the pieces dealt or queued are the first 7·max(5, ⌈(drawn + 30) / 7⌉) of the bag sequence
    let n_bags = std::cmp::max(5, (t.drawn as usize + 30).div_ceil(7));
    let seq = engine::bag_sequence(o.seed, n_bags);
    let mut s = Vec::with_capacity(seq.len() + t.keys.len());
    for &p in &seq { s.push(LETTER[p as usize]); }
    s.extend_from_slice(&t.keys);
    let mut d = Vec::with_capacity(8 + t.locks.len());
    d.extend_from_slice(&[0.0, t.n_locks as f64, t.drawn as f64, t.holds_total as f64, t.pcs as f64, t.top_lock as f64,
        t.garbage_cleared, seq.len() as f64]);
    d.extend_from_slice(&t.locks);
    TraceOut { f: d, s }
}

/// # Safety
/// As `oracle_run`. The returned handle is freed with `replay_free`.
#[no_mangle]
pub unsafe extern "C" fn replay_run(opts: *const f64, n_opts: u32, events: *const f64, n_events: u32) -> *mut TraceOut {
    let o: &[f64] = if opts.is_null() || n_opts == 0 { &[] } else { std::slice::from_raw_parts(opts, n_opts as usize) };
    let e: &[f64] = if events.is_null() || n_events == 0 { &[] } else { std::slice::from_raw_parts(events, n_events as usize) };
    Box::into_raw(Box::new(run_traced(o, e)))
}

/// # Safety
/// `h` must be a handle from `replay_run` not yet freed.
#[no_mangle]
pub unsafe extern "C" fn replay_f_len(h: *const TraceOut) -> f64 { if h.is_null() { -1.0 } else { (*h).f.len() as f64 } }

/// # Safety
/// As `replay_f_len`.
#[no_mangle]
pub unsafe extern "C" fn replay_s_len(h: *const TraceOut) -> f64 { if h.is_null() { -1.0 } else { (*h).s.len() as f64 } }

/// Copies the f64 buffer into `dst` (room for `len`); returns the count, -1 if it does not fit.
/// # Safety
/// As `replay_f_len`; `dst` must have room for `len` f64.
#[no_mangle]
pub unsafe extern "C" fn replay_f_copy(h: *const TraceOut, dst: *mut f64, len: u32) -> i32 {
    if h.is_null() || dst.is_null() { return -1; }
    let d = &(*h).f;
    if d.len() > len as usize { return -1; }
    std::ptr::copy_nonoverlapping(d.as_ptr(), dst, d.len());
    d.len() as i32
}

/// Copies the byte buffer into `dst` (room for `len`); returns the count, -1 if it does not fit.
/// # Safety
/// As `replay_f_len`; `dst` must have room for `len` bytes.
#[no_mangle]
pub unsafe extern "C" fn replay_s_copy(h: *const TraceOut, dst: *mut u8, len: u32) -> i32 {
    if h.is_null() || dst.is_null() { return -1; }
    let d = &(*h).s;
    if d.len() > len as usize { return -1; }
    std::ptr::copy_nonoverlapping(d.as_ptr(), dst, d.len());
    d.len() as i32
}

/// # Safety
/// `h` must be a handle from `replay_run`, freed at most once.
#[no_mangle]
pub unsafe extern "C" fn replay_free(h: *mut TraceOut) { if !h.is_null() { drop(Box::from_raw(h)); } }

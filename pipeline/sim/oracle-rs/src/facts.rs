//! The engine runs of emit-attack-facts.ts and emit-finesse-facts.ts, in Rust: the same engine as
//! `engine::run`, ticked to `max_frame`, recording per lock what those two emitters' hooks read (see
//! pipeline/sim/facts-native.ts, which decodes this).
//!
//! C ABI (nothing may panic): `facts_run(opts, n, events, n)` takes the buffers `oracle_run` takes and
//! returns a handle holding one f64 buffer.
//!
//! f64: `[status, threw, nLocks]`, then per lock `[piece, keys, softDrop, x0, y0, x1, y1, x2, y2, x3,
//! y3, lines, spin (0 none, 1 mini, 2 full), b2b, combo, garbageCleared, allclear, nRaw, raw.., nOwn,
//! key..]`. A piece is 0..6 = IJLOSTZ; cells are the locked piece's (x, y up from the floor) as
//! `falling.lock.pre` reads them; `keys` is the piece's `falling.keys`; `softDrop` is the engine's
//! ACTION_SOFTDROP flag at `falling.lock.pre`; `raw` is the lock's attack before cancellation
//! (`res.rawGarbage`); b2b and combo are the engine's, floored at 0; `key..` are the key codes pressed
//! on this piece (oracle-native.ts's codes), reset by a hold's `falling.new` and after each lock.
//! Status: 0 ok, 2 a clearing lock with no pre-tick snapshot, 3 a malformed buffer, 4 the engine threw
//! while building. `threw` is 1 when a tick threw (the round ends there; the locks before it stand).
use crate::engine::{self, Spin};
use crate::ffi::{events_from, opts_from};

#[derive(Default)]
pub struct FactsTrace {
    /// `falling.keys` of the piece in play
    keys: f64,
    /// the key codes pressed on the piece in play
    own: Vec<u8>,
    /// lock.pre's reads, held until the lock is recorded: piece, keys, softDrop, cells, raw attack
    pre: Option<(usize, f64, bool, [(f64, f64); 4], Vec<f64>)>,
    out: Vec<f64>,
    n_locks: u32,
}

impl FactsTrace {
    /// `#keydown`, after its processSubframe: every key is recorded; left/right and CW/CCW count one
    /// input, 180 two when the rule set allows it (otherwise the engine returns before counting).
    pub fn on_key(&mut self, key: u8, allow180: bool) {
        self.own.push(key);
        match key {
            0 | 1 | 3 | 4 => self.keys += 1.0,
            5 if allow180 => self.keys += 2.0,
            _ => {}
        }
    }
    /// `falling.new`: a new Tetromino starts at keys 0; a hold's starts a new key list.
    pub fn on_new(&mut self, is_hold: bool) {
        self.keys = 0.0;
        if is_hold { self.own.clear(); }
    }
    /// `falling.lock.pre`
    pub fn on_lock_pre(&mut self, piece: usize, placed: &[(f64, f64); 4], soft_drop: bool, raw: Vec<f64>) {
        self.pre = Some((piece, self.keys, soft_drop, *placed, raw));
    }
    /// `falling.lock`
    #[allow(clippy::too_many_arguments)]
    pub fn on_lock(&mut self, lines: f64, spin: Spin, b2b: f64, combo: f64, garbage_cleared: f64, allclear: bool) {
        let (piece, keys, sd, placed, raw) = match self.pre.take() { Some(p) => p, None => return };
        let spin = match spin { Spin::None => 0.0, Spin::Mini => 1.0, Spin::Normal => 2.0 };
        self.out.extend_from_slice(&[piece as f64, keys, if sd { 1.0 } else { 0.0 }]);
        for &(x, y) in placed.iter() { self.out.push(x); self.out.push(y); }
        self.out.extend_from_slice(&[lines, spin, b2b, combo, garbage_cleared, if allclear { 1.0 } else { 0.0 }]);
        self.out.push(raw.len() as f64);
        self.out.extend_from_slice(&raw);
        self.out.push(self.own.len() as f64);
        for &k in &self.own { self.out.push(k as f64); }
        self.own.clear();
        self.n_locks += 1;
    }
}

pub struct FactsOut { f: Vec<f64> }

fn fail(status: f64) -> FactsOut { FactsOut { f: vec![status, 0.0, 0.0] } }

fn run_facts(opts: &[f64], events: &[f64]) -> FactsOut {
    let o = match opts_from(opts) { Some(o) => o, None => return fail(3.0) };
    let frames = match events_from(events, o.max_frame) { Some(f) => f, None => return fail(3.0) };
    let mut eng = match engine::Engine::new(&o) { Ok(e) => e, Err(_) => return fail(4.0) };
    // the constructor dealt the first piece before any hook existed: it starts at keys 0, no keys pressed
    eng.facts = Some(Box::default());
    let empty = Vec::new();
    let mut threw = false;
    let mut f = 0usize;
    while (f as f64) <= o.max_frame {
        let evs = frames.get(f).unwrap_or(&empty);
        if eng.tick_fresh(evs).is_err() {
            if eng.take_fatal().is_some() { return fail(2.0); }
            threw = true;
            break;
        }
        f += 1;
    }
    let t = match eng.facts.take() { Some(t) => t, None => return fail(3.0) };
    let mut d = Vec::with_capacity(3 + t.out.len());
    d.extend_from_slice(&[0.0, if threw { 1.0 } else { 0.0 }, t.n_locks as f64]);
    d.extend_from_slice(&t.out);
    FactsOut { f: d }
}

/// # Safety
/// As `oracle_run`. The returned handle is freed with `facts_free`.
#[no_mangle]
pub unsafe extern "C" fn facts_run(opts: *const f64, n_opts: u32, events: *const f64, n_events: u32) -> *mut FactsOut {
    let o: &[f64] = if opts.is_null() || n_opts == 0 { &[] } else { std::slice::from_raw_parts(opts, n_opts as usize) };
    let e: &[f64] = if events.is_null() || n_events == 0 { &[] } else { std::slice::from_raw_parts(events, n_events as usize) };
    Box::into_raw(Box::new(run_facts(o, e)))
}

/// # Safety
/// `h` must be a handle from `facts_run` not yet freed.
#[no_mangle]
pub unsafe extern "C" fn facts_f_len(h: *const FactsOut) -> f64 { if h.is_null() { -1.0 } else { (*h).f.len() as f64 } }

/// Copies the f64 buffer into `dst` (room for `len`); returns the count, -1 if it does not fit.
/// # Safety
/// As `facts_f_len`; `dst` must have room for `len` f64.
#[no_mangle]
pub unsafe extern "C" fn facts_f_copy(h: *const FactsOut, dst: *mut f64, len: u32) -> i32 {
    if h.is_null() || dst.is_null() { return -1; }
    let d = &(*h).f;
    if d.len() > len as usize { return -1; }
    std::ptr::copy_nonoverlapping(d.as_ptr(), dst, d.len());
    d.len() as i32
}

/// # Safety
/// `h` must be a handle from `facts_run`, freed at most once.
#[no_mangle]
pub unsafe extern "C" fn facts_free(h: *mut FactsOut) { if !h.is_null() { drop(Box::from_raw(h)); } }

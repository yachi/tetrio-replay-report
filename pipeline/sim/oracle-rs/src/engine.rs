//! A port of the vendored Triangle.js engine (pipeline/sim/vendor/teto/engine/index.mjs and the
//! modules it imports) restricted to the paths `oracle-source.ts` reaches on the rule set it accepts:
//! SRS+ kicks, a 7-bag, T-spin bonuses, the multiplier combo table, the post-2025-05-06 garbage queue,
//! `irs`/`ihs` = "tap". Every method keeps its JS name in a comment and its JS statement order; every
//! JS number is an f64 here unless it is provably an integer index. A JS exception is `Err(Throw)`.
//!
//! The replay harness (oracle-source.ts's tick loop, lock listener and lazy pre-tick snapshot) lives in
//! `run` at the bottom; it records exactly what that harness records.

use crate::data::{KICKS, STATES, T_CORNERS, WIDTH};

pub const W: usize = 10;
pub const FULL_H: usize = 40;
const BOARD_HEIGHT: f64 = 20.0;
const GARBAGE: u8 = 7;

// constants/index.mjs
const ROTATION_LEFT: u32 = 1;
const ROTATION_RIGHT: u32 = 2;
const ROTATION_180: u32 = 4;
const ROTATION_SPIN: u32 = 8;
const ROTATION_MINI: u32 = 16;
const ROTATION_SPIN_ALL: u32 = 32;
const ROTATION_ALL: u32 = 63;
const STATE_WALL: u32 = 64;
const STATE_FLOOR: u32 = 256;
const STATE_ALL: u32 = 64 | 128 | 256 | 512;
const ACTION_IHS: u32 = 1024;
const ACTION_FORCELOCK: u32 = 2048;
const ACTION_SOFTDROP: u32 = 4096;
const ACTION_MOVE: u32 = 8192;
const ACTION_ROTATE: u32 = 16384;

const MAX_SAFE_INTEGER: f64 = 9007199254740991.0;

/// A JS exception thrown inside `Engine.tick`; the harness turns it into a topout.
#[derive(Debug)]
pub struct Throw;

/// An invariant of the harness broken (the TS harness throws past its catch for these).
#[derive(Debug)]
pub enum Fatal {
    NoPreTick,
}

// ── JS number helpers ────────────────────────────────────────────────────────────────────────────
#[inline]
fn js_max(a: f64, b: f64) -> f64 {
    if a.is_nan() || b.is_nan() { f64::NAN } else if a > b { a } else if b > a { b } else if a == 0.0 && b == 0.0 && (a.is_sign_negative() && b.is_sign_negative()) { a } else if a == 0.0 && b == 0.0 { 0.0 } else { a }
}
#[inline]
fn js_min(a: f64, b: f64) -> f64 {
    if a.is_nan() || b.is_nan() { f64::NAN } else if a < b { a } else if b < a { b } else if a == 0.0 && b == 0.0 && (a.is_sign_negative() || b.is_sign_negative()) { -0.0 } else { a }
}
/// Math.round: the nearest integer, ties toward +∞.
#[inline]
pub fn js_round(x: f64) -> f64 {
    if !x.is_finite() { return x; }
    let r = x.floor();
    if x - r >= 0.5 { r + 1.0 } else { r }
}
#[inline]
fn truthy(x: f64) -> bool { x != 0.0 && !x.is_nan() }

// ── utils/rng ────────────────────────────────────────────────────────────────────────────────────
#[derive(Clone)]
struct Rng { value: f64 }
impl Rng {
    fn new(seed: f64) -> Rng {
        let mut v = seed % 2147483647.0;
        if v <= 0.0 { v += 2147483646.0; }
        Rng { value: v }
    }
    fn next(&mut self) -> f64 { self.value = 16807.0 * self.value % 2147483647.0; self.value }
    fn next_float(&mut self) -> f64 { (self.next() - 1.0) / 2147483646.0 }
    fn shuffle(&mut self, a: &mut [u8]) {
        if a.is_empty() { return; }
        let mut i = a.len() - 1;
        while i != 0 {
            let r = (self.next_float() * (i as f64 + 1.0)).floor() as usize;
            a.swap(i, r);
            i -= 1;
        }
    }
}

// ── utils/increase ───────────────────────────────────────────────────────────────────────────────
struct Increase { value: f64, increase: f64, margin: f64, frame: f64 }
impl Increase {
    fn new(base: f64, increase: f64, margin: f64) -> Increase { Increase { value: base, increase, margin, frame: 0.0 } }
    fn tick(&mut self) { self.frame += 1.0; if self.frame > self.margin { self.value += self.increase / 60.0; } }
    fn get(&self) -> f64 { self.value }
}

// ── board ────────────────────────────────────────────────────────────────────────────────────────
/// A board cell: the mino (0..6 = IJLOSTZ, 7 = garbage) and the harness's provenance tag (the index
/// of the lock that placed it; oracle-source.ts tags by cell identity, which survives every splice).
#[derive(Clone, Copy, PartialEq)]
pub struct Cell { pub mino: u8, pub tag: i32 }
pub type Row = [Option<Cell>; W];

/// `legal(blocks, board)` from utils/kicks: the board here is always FULL_H rows of W.
#[inline]
fn legal(board: &[Row], blocks: &[(f64, f64); 4]) -> bool {
    for &(x, y) in blocks.iter() {
        if x < 0.0 || x >= W as f64 || y < 0.0 || y >= board.len() as f64 { return false; }
        if board[y as usize][x as usize].is_some() { return false; }
    }
    true
}

// ── garbage/index.mjs (GarbageQueue) ─────────────────────────────────────────────────────────────
#[derive(Clone)]
struct GItem { frame: f64, amount: f64, size: f64, cid: f64, gameid: f64 }
struct TankOut { amount: f64, size: f64, column: Option<f64>, id: f64 }

pub struct Opts {
    pub seed: f64, pub gameid: f64,
    pub g: f64, pub gincrease: f64, pub gmargin: f64,
    pub gmult: f64, pub gmult_increase: f64, pub gmult_margin: f64,
    pub gcap: f64, pub gcap_increase: f64, pub gcap_margin: f64, pub gcap_max: f64, pub gcap_absolute: f64,
    pub gspeed: f64, pub hole_size: f64, pub mess_change: f64, pub mess_within: f64, pub mess_timeout: f64,
    pub nosame: bool, pub center: bool, pub opener_phase: f64,
    pub allclears: bool, pub allclear_garbage: f64, pub allclear_b2b: f64, pub b2b_chaining: bool,
    pub clutch: bool, pub lock_resets: f64, pub lock_time: f64, pub infinite: bool, pub may20g_mode: bool,
    pub allow180: bool, pub allow_harddrop: bool, pub allow_hold: bool, pub infinite_hold: bool,
    pub arr: f64, pub das: f64, pub dcd: f64, pub sdf: f64, pub safelock: bool, pub cancel: bool, pub hmay20g: bool,
    pub max_frame: f64, pub network: bool,
}

struct GarbageQueue {
    queue: Vec<GItem>,
    last_column: Option<f64>,
    has_changed: bool,
    rng: Rng,
    sent: f64,
    absolute: f64,
}

impl GarbageQueue {
    fn new(o: &Opts) -> GarbageQueue {
        let absolute = if truthy(o.gcap_absolute) { o.gcap_absolute } else { MAX_SAFE_INTEGER };
        GarbageQueue { queue: Vec::new(), last_column: None, has_changed: false, rng: Rng::new(o.seed), sent: 0.0, absolute }
    }
    fn receive(&mut self, item: GItem) -> Result<(), Throw> {
        if item.amount > 0.0 { self.queue.push(item); }
        let cap = self.absolute;
        let mut total = 0.0;
        for q in &self.queue { total += q.amount; }
        while total > cap {
            let excess = total - cap;
            // an empty queue here reads `undefined.amount` in JS: a TypeError
            if self.queue.is_empty() { return Err(Throw); }
            let last = self.queue.len() - 1;
            if self.queue[last].amount <= excess { total -= self.queue[last].amount; self.queue.pop(); }
            else { self.queue[last].amount -= excess; total -= excess; }
        }
        Ok(())
    }
    fn confirm(&mut self, cid: f64, gameid: f64, frame: f64) {
        if let Some(q) = self.queue.iter_mut().find(|g| g.cid == cid && g.gameid == gameid) { q.frame = frame; }
    }
    fn column_width(o: &Opts) -> f64 { js_max(0.0, W as f64 - (o.hole_size - 1.0)) }
    fn reroll(&mut self, o: &Opts) -> f64 {
        let cb = if o.center { js_round(W as f64 / 5.0) } else { 0.0 };
        let col;
        if o.nosame && self.last_column.is_some() {
            let mut c = cb + (self.rng.next_float() * (Self::column_width(o) - 1.0 - 2.0 * cb)).floor();
            if c >= self.last_column.unwrap() { c += 1.0; }
            col = c;
        } else {
            col = cb + (self.rng.next_float() * (Self::column_width(o) - 2.0 * cb)).floor();
        }
        self.last_column = Some(col);
        col
    }
    /// cancel(amount, pieceCount, {openerPhase: false}) → the amount still sent
    fn cancel(&mut self, o: &Opts, amount: f64, piece_count: f64) -> f64 {
        let mut send = amount;
        let mut cancel = 0.0;
        let mut current = 0.0;
        for q in &self.queue { current += q.amount; }
        if piece_count + 1.0 <= o.opener_phase - 0.0 && current >= self.sent { cancel += amount; }
        while (send > 0.0 || cancel > 0.0) && !self.queue.is_empty() {
            self.queue[0].amount -= 1.0;
            if self.queue[0].amount <= 0.0 {
                self.queue.remove(0);
                if self.rng.next_float() < o.mess_change { self.reroll(o); self.has_changed = true; }
            }
            if send > 0.0 { send -= 1.0; } else { cancel -= 1.0; }
        }
        self.sent += send;
        send
    }
    fn tank(&mut self, o: &Opts, frame: f64, cap: f64, hard: bool) -> Vec<TankOut> {
        let mut res = Vec::new();
        if self.queue.is_empty() { return res; }
        // Array.prototype.sort with (a, b) => a.frame - b.frame: stable; frames are finite here
        self.queue.sort_by(|a, b| a.frame.partial_cmp(&b.frame).unwrap_or(std::cmp::Ordering::Equal));
        if truthy(o.mess_timeout) && frame >= 0.0 + o.mess_timeout { self.reroll(o); self.has_changed = true; }
        let lines = js_min(cap, o.gcap_max).floor();
        let mut i = 0.0;
        while i < lines && !self.queue.is_empty() {
            let limit = if hard { frame } else { frame - 1.0 };
            if self.queue[0].frame + o.gspeed > limit { break; }
            self.queue[0].amount -= 1.0;
            let mut col = self.last_column;
            if (col.is_none() || self.rng.next_float() < o.mess_within) && !self.has_changed {
                col = Some(self.reroll(o));
                self.has_changed = true;
            }
            let it = &self.queue[0];
            res.push(TankOut { amount: 1.0, size: it.size, column: col, id: it.cid });
            self.has_changed = false;
            if self.queue[0].amount <= 0.0 {
                self.queue.remove(0);
                if self.rng.next_float() < o.mess_change { self.reroll(o); self.has_changed = true; }
            }
            i += 1.0;
        }
        res
    }
}

// ── multiplayer/ige.mjs ──────────────────────────────────────────────────────────────────────────
struct IgePlayer { id: f64, outgoing: Vec<(f64, f64)> }
struct Ige { players: Vec<IgePlayer>, iid: f64 }
impl Ige {
    fn player(&mut self, id: f64) -> usize {
        match self.players.iter().position(|p| p.id == id) {
            Some(i) => i,
            None => { self.players.push(IgePlayer { id, outgoing: Vec::new() }); self.players.len() - 1 }
        }
    }
    fn send(&mut self, id: f64, amount: f64) {
        if amount == 0.0 { return; }
        let i = self.player(id);
        self.iid += 1.0;
        let iid = self.iid;
        self.players[i].outgoing.push((iid, amount));
    }
    fn receive(&mut self, id: f64, ackiid: f64, amount: f64) -> f64 {
        let i = self.player(id);
        let mut running = amount;
        let mut kept = Vec::new();
        for &(iid, a) in &self.players[i].outgoing {
            if iid <= ackiid { continue; }
            let amt = js_min(a, running);
            let left = a - amt;
            running -= amt;
            if left > 0.0 { kept.push((iid, left)); }
        }
        self.players[i].outgoing = kept;
        running
    }
}

// ── utils/damageCalc (garbageCalcV2, the "multiplier" combo table, no target bonus) ──────────────
#[derive(Clone, Copy, PartialEq)]
pub enum Spin { None, Mini, Normal }

pub fn garbage_calc(b2b: f64, combo: f64, lines: f64, spin: Spin, chaining: bool) -> f64 {
    let mut g: f64 = if lines == 0.0 { 0.0 }
        else if lines == 1.0 { match spin { Spin::Mini => 0.0, Spin::Normal => 2.0, Spin::None => 0.0 } }
        else if lines == 2.0 { match spin { Spin::Mini => 1.0, Spin::Normal => 4.0, Spin::None => 1.0 } }
        else if lines == 3.0 { match spin { Spin::Mini => 2.0, Spin::Normal => 6.0, Spin::None => 2.0 } }
        else if lines == 4.0 { if spin != Spin::None { 10.0 } else { 4.0 } }
        else if lines == 5.0 { if spin != Spin::None { 12.0 } else { 5.0 } }
        else { let t = lines - 5.0; if spin != Spin::None { 12.0 + 2.0 * t } else { 5.0 + t } };
    if lines > 0.0 && b2b > 0.0 {
        if chaining {
            let l = (b2b * 0.8).ln_1p();
            let gains = 1.0 * ((1.0 + l).floor() + (if b2b == 1.0 { 0.0 } else { (1.0 + l % 1.0) / 3.0 }));
            g += gains;
        } else {
            g += 1.0;
        }
    }
    if combo > 0.0 {
        g *= 1.0 + 0.25 * combo;
        if combo > 1.0 { g = js_max((1.0 * combo * 1.25).ln_1p(), g); }
    }
    g
}

// ── utils/tetromino (the falling piece) ──────────────────────────────────────────────────────────
#[derive(Clone)]
struct Falling {
    sym: usize,
    rotation: usize,
    x: f64,
    y: f64, // location[1]
    locking: f64,
    lock_resets: f64,
    rot_resets: f64,
    safe_lock: f64,
    highest_y: f64,
    total_rotations: f64,
    irs: f64,
}
impl Falling {
    fn new(sym: usize, from: Option<&Falling>) -> Falling {
        Falling {
            sym, rotation: 0,
            x: (W as f64 / 2.0 - WIDTH[sym] as f64 / 2.0).floor(),
            y: BOARD_HEIGHT + 2.04,
            locking: 0.0, lock_resets: 0.0, rot_resets: 0.0,
            safe_lock: from.map(|f| f.safe_lock).unwrap_or(0.0),
            highest_y: BOARD_HEIGHT + 2.0,
            total_rotations: 0.0,
            irs: from.map(|f| f.irs).unwrap_or(0.0),
        }
    }
    #[inline]
    fn fy(&self) -> f64 { self.y.floor() }
    /// absoluteAt({x, y, rotation}) — y is floored
    #[inline]
    fn at(&self, x: f64, y: f64, rot: usize) -> [(f64, f64); 4] {
        let s = &STATES[self.sym][rot];
        let yf = y.floor();
        let mut o = [(0.0, 0.0); 4];
        for i in 0..4 { o[i] = (s[i].0 as f64 + x, -(s[i].1 as f64) + yf); }
        o
    }
    #[inline]
    fn abs_blocks(&self) -> [(f64, f64); 4] { self.at(self.x, self.y, self.rotation) }
}

// ── the engine ───────────────────────────────────────────────────────────────────────────────────
struct Shift { held: bool, arr: f64, das: f64, dir: f64 }

pub struct LockRec {
    pub frame: f64,
    pub piece: usize,
    pub lines: f64,
    pub spin: Spin,
    pub sent: f64,
    pub b2b: f64,
    pub combo: f64,
    pub garbage_cleared: f64,
    pub allclear: bool,
    pub cells: [(i32, i32); 4], // (col, sim row y-down)
    pub cleared_rows: Vec<i32>,
    pub snap: i32,
}
pub struct GarbageRec { pub frame: f64, pub amt: f64, pub lock_index: usize }

pub enum Ev {
    KeyDown { sub: f64, key: u8, hoisted: bool },
    KeyUp { sub: f64, key: u8 },
    Interaction { gameid: f64, ackiid: f64, amt: f64, iid: f64, size: f64 },
    Confirm { iid: f64, gameid: f64, frame: f64 },
    Target { ids: Vec<f64> },
}
// key codes (oracle-native.ts): 0 moveLeft 1 moveRight 2 softDrop 3 rotateCCW 4 rotateCW 5 rotate180
// 6 hardDrop 7 hold; anything else is a key the engine ignores after its processSubframe.

pub struct Engine<'o> {
    o: &'o Opts,
    board: Vec<Row>,
    bag: Rng,
    queue: Vec<u8>,
    qpos: usize,
    held: Option<usize>,
    hold_locked: bool,
    falling: Falling,
    last_spin: Option<Spin>,
    last_was_clear: bool,
    combo: f64,
    b2b: f64,
    pieces: f64,
    frame: f64,
    subframe: f64,
    state: u32,
    l_shift: Shift,
    r_shift: Shift,
    last_shift: f64,
    soft_drop: bool,
    gravity: Increase,
    gmult: Increase,
    gcap: Increase,
    garbage: GarbageQueue,
    ige: Ige,
    targets: Vec<f64>,
    // ── harness state (oracle-source.ts) ──
    pub locks: Vec<LockRec>,
    pub garbage_events: Vec<GarbageRec>,
    pub topout: bool,
    pre_tick: Option<[[bool; W]; FULL_H]>,
    fatal: Option<Fatal>,
}

impl<'o> Engine<'o> {
    pub fn new(o: &'o Opts) -> Result<Engine<'o>, Throw> {
        let mut e = Engine {
            o,
            board: vec![[None; W]; FULL_H],
            bag: Rng::new(o.seed),
            queue: Vec::new(),
            qpos: 0,
            held: None,
            hold_locked: false,
            falling: Falling::new(0, None),
            last_spin: None,
            last_was_clear: false,
            combo: -1.0,
            b2b: -1.0,
            pieces: 0.0,
            frame: 0.0,
            subframe: 0.0,
            state: 0,
            l_shift: Shift { held: false, arr: 0.0, das: 0.0, dir: -1.0 },
            r_shift: Shift { held: false, arr: 0.0, das: 0.0, dir: 1.0 },
            last_shift: -1.0,
            soft_drop: false,
            gravity: Increase::new(o.g, o.gincrease, o.gmargin),
            gmult: Increase::new(o.gmult, o.gmult_increase, o.gmult_margin),
            gcap: Increase::new(o.gcap, o.gcap_increase, o.gcap_margin),
            garbage: GarbageQueue::new(o),
            ige: Ige { players: Vec::new(), iid: 0.0 },
            targets: Vec::new(),
            locks: Vec::new(),
            garbage_events: Vec::new(),
            topout: false,
            pre_tick: None,
            fatal: None,
        };
        // init(): the first piece has no previous falling piece to inherit from
        e.next_piece_first()?;
        Ok(e)
    }

    // ── queue ──
    fn shift_queue(&mut self) -> usize {
        // Queue.shift(): repopulate (whole 7-bags) then take the head; the order is the bags concatenated
        if self.qpos >= self.queue.len() {
            let mut b: [u8; 7] = [6, 2, 3, 4, 0, 1, 5]; // [z, l, o, s, i, j, t]
            self.bag.shuffle(&mut b);
            self.queue.drain(..self.qpos);
            self.qpos = 0;
            self.queue.extend_from_slice(&b);
        }
        let p = self.queue[self.qpos] as usize;
        self.qpos += 1;
        p
    }

    // ── harness board hooks: the first board mutation of a tick snapshots the occupancy ──
    fn take_pre_tick(&mut self) {
        if self.pre_tick.is_none() {
            let mut g = [[false; W]; FULL_H];
            for y in 0..FULL_H { for x in 0..W { g[y][x] = self.board[y][x].is_some(); } }
            self.pre_tick = Some(g);
        }
    }

    fn occupied(&self, x: f64, y: f64) -> bool {
        x < 0.0 || y < 0.0 || x >= W as f64 || y >= FULL_H as f64 || self.board[y as usize][x as usize].is_some()
    }
    fn perfect_clear(&self) -> bool { self.board.iter().all(|r| r.iter().all(|c| c.is_none())) }

    // ── flags/predicates ──
    fn is_forced_to_lock(&self) -> bool { self.state & ACTION_FORCELOCK != 0 }
    fn has_hit_wall(&self) -> bool { self.state & STATE_WALL != 0 }
    fn is_20g(&self) -> bool {
        let g = self.gravity.get();
        let is20 = g > BOARD_HEIGHT;
        let mode = self.o.may20g_mode;
        if self.soft_drop {
            let prefer = self.o.hmay20g || (is20 && mode);
            return (self.o.sdf == 41.0 || g * self.o.sdf > BOARD_HEIGHT) && prefer;
        }
        is20 && mode
    }
    fn should_lock(&self) -> bool { !self.o.infinite && self.falling.lock_resets >= self.o.lock_resets }
    fn should_fall_faster(&self) -> bool {
        if self.o.infinite { false } else { self.falling.rot_resets > self.o.lock_resets + 15.0 }
    }

    fn internal_lock(&mut self, sub: f64) -> bool {
        self.falling.locking += sub;
        self.falling.locking > self.o.lock_time || self.is_forced_to_lock() || self.should_lock()
    }

    fn internal_fall(&mut self, value: f64) -> bool {
        let mut y1 = js_round(1e6 * (self.falling.y - value)) / 1e6;
        let mut y2 = self.falling.y - 1.0;
        if y1 % 1.0 == 0.0 { y1 -= 1e-6; }
        if y2 % 1.0 == 0.0 { y2 += 2e-6; }
        let (x, r) = (self.falling.x, self.falling.rotation);
        if !legal(&self.board, &self.falling.at(x, y1, r)) || !legal(&self.board, &self.falling.at(x, y2, r)) { return false; }
        let highest = self.falling.highest_y;
        if highest > y1 { self.falling.highest_y = y1.floor(); }
        self.falling.y = y1;
        self.last_spin = None;
        self.state &= !STATE_FLOOR;
        if y1 < highest || self.o.infinite { self.falling.lock_resets = 0.0; self.falling.rot_resets = 0.0; }
        true
    }

    fn internal_dcd(&mut self) {
        if !self.has_hit_wall() || !truthy(self.o.dcd) { return; }
        self.l_shift.das = js_min(self.l_shift.das, self.o.das - self.o.dcd);
        self.l_shift.arr = self.o.arr;
        self.r_shift.das = js_min(self.r_shift.das, self.o.das - self.o.dcd);
        self.r_shift.arr = self.o.arr;
    }

    fn fall(&mut self, sub: f64) -> Result<(), Throw> {
        if self.falling.safe_lock > 0.0 { self.falling.safe_lock -= 1.0; }
        let mut fall = self.gravity.get() * sub;
        if self.soft_drop {
            if self.o.sdf == 41.0 { fall = 400.0 * sub; } else { fall *= self.o.sdf; fall = js_max(fall, 0.05 * self.o.sdf); }
        }
        if self.should_lock() {
            let below = self.falling.at(self.falling.x, self.falling.y - 1.0, self.falling.rotation);
            if !legal(&self.board, &below) { fall = 20.0; self.state |= ACTION_FORCELOCK; }
        }
        if self.should_fall_faster() {
            fall += 0.5 * sub * (self.falling.rot_resets - (self.o.lock_resets + 15.0));
        }
        let mut df = fall;
        while df > 0.0 {
            let y = self.falling.y;
            if !self.internal_fall(js_min(1.0, df)) {
                if self.internal_lock(sub) {
                    if self.o.safelock { self.falling.safe_lock = 7.0; }
                    self.lock(false)?;
                }
                return Ok(());
            }
            if y.floor() != self.falling.y.floor() { self.state &= !ROTATION_ALL; }
            df -= js_min(1.0, df);
        }
        Ok(())
    }

    // ── rotation ──
    fn detect_spin(&self, fin_or_tst: bool) -> Spin {
        // spinBonuses "T-spins": a T is scored by its corners, anything else is "none"
        if self.falling.sym != 5 { return Spin::None; }
        let f = &self.falling;
        let s = &STATES[f.sym][f.rotation];
        let fy = f.fy();
        let mut below = [(0.0, 0.0); 4];
        for i in 0..4 { below[i] = (s[i].0 as f64 + f.x, -(s[i].1 as f64) + fy - 1.0); }
        if legal(&self.board, &below) { return Spin::None; }
        let mut corners = 0;
        let mut front = 0;
        let rot = f.rotation as i32;
        for i in 0..4 {
            let t = T_CORNERS[f.rotation][i];
            if self.occupied(f.x + t.0 as f64 + 1.0, fy - t.1 as f64 - 1.0) {
                corners += 1;
                if rot == t.2 || rot == t.3 { front += 1; }
            }
        }
        if corners < 3 { return Spin::None; }
        let mut spin = Spin::Normal;
        if front != 2 { spin = Spin::Mini; } // T is in "T-spins".types_mini
        if fin_or_tst { spin = Spin::Normal; }
        spin
    }

    fn rotate(&mut self, amount: i32) {
        let to = (((self.falling.rotation as i32 + amount) % 4 + 4) % 4) as usize;
        self.state |= ACTION_MOVE;
        self.state |= ACTION_ROTATE;
        // #kick → performKick(SRS+, symbol, location, [0, 0], maxMovement, states[to], rotation, to, board)
        let f = &self.falling;
        let max_movement = !self.o.infinite && f.total_rotations > self.o.lock_resets + 15.0;
        let from = f.rotation;
        let s = &STATES[f.sym][to];
        let fy = f.y.floor();
        let base_x = f.x - 0.0;
        let base_y = fy - 0.0;
        let mut init = [(0.0, 0.0); 4];
        for i in 0..4 { init[i] = (base_x + s[i].0 as f64, base_y - s[i].1 as f64); }
        let kick: Option<(f64, f64, (f64, f64), usize)>; // newX, newY, kick, id
        if legal(&self.board, &init) {
            kick = Some((f.x, f.y, (0.0, 0.0), 0));
        } else {
            let id = from * 4 + to;
            match KICKS[f.sym][id] {
                None => kick = None, // kickset undefined: performKick's try/catch returns false
                Some(set) => {
                    let mut found = None;
                    for &(dx, dy) in set.iter() {
                        let (dx, dy) = (dx as f64, dy as f64);
                        let new_y = if max_movement { f.y - dy - 0.0 } else { f.y.ceil() - 0.1 - dy - 0.0 };
                        let fny = new_y.floor();
                        let mx = base_x + dx;
                        let mut tb = [(0.0, 0.0); 4];
                        for j in 0..4 { tb[j] = (mx + s[j].0 as f64, fny - s[j].1 as f64); }
                        if legal(&self.board, &tb) { found = Some((f.x + dx - 0.0, new_y, (dx, -dy), id)); break; }
                    }
                    kick = found;
                }
            }
        }
        if let Some((nx, ny, k, id)) = kick { self.internal_rotate(nx, ny, to, amount, k, id); }
    }

    fn internal_rotate(&mut self, nx: f64, ny: f64, to: usize, mut dir: i32, kick: (f64, f64), id: usize) {
        if dir >= 2 {
            dir = if to > self.falling.rotation { 1 } else { -1 };
            self.state |= ROTATION_180;
        }
        self.falling.x = nx;
        self.falling.y = ny;
        self.falling.rotation = to;
        self.state |= if dir == 1 { ROTATION_RIGHT } else { ROTATION_LEFT };
        self.state &= !(ROTATION_SPIN | ROTATION_MINI | ROTATION_SPIN_ALL);
        if self.falling.lock_resets < 31.0 { self.falling.lock_resets += 1.0; }
        if self.falling.rot_resets < 63.0 { self.falling.rot_resets += 1.0; }
        // #isTSpinKick: ids "23"/"03" with kick [1, -2], "21"/"01" with kick [-1, -2]; "00" never
        let tst = id != 0 && (((id == 2 * 4 + 3 || id == 3) && kick.0 == 1.0 && kick.1 == -2.0)
            || ((id == 2 * 4 + 1 || id == 1) && kick.0 == -1.0 && kick.1 == -2.0));
        let spin = self.detect_spin(tst);
        self.last_spin = Some(spin);
        // spin is a non-empty string in JS, so always truthy
        self.state |= ROTATION_SPIN;
        if spin == Spin::Mini { self.state |= ROTATION_MINI; }
        self.falling.total_rotations += 1.0;
        self.internal_dcd();
        if !self.should_lock() { self.falling.locking = 0.0; }
    }

    // ── spawning and hold ──
    fn next_piece_first(&mut self) -> Result<(), Throw> {
        let p = self.shift_queue();
        self.initiate(p, false, false, true)
    }
    fn next_piece(&mut self, ignore_blockout: bool, is_hold: bool) -> Result<(), Throw> {
        let p = self.shift_queue();
        self.initiate(p, ignore_blockout, is_hold, false)
    }

    fn initiate(&mut self, piece: usize, ignore_blockout: bool, is_hold: bool, first: bool) -> Result<(), Throw> {
        self.internal_dcd();
        self.state &= !(ROTATION_ALL | STATE_ALL | ACTION_FORCELOCK | ACTION_SOFTDROP | ACTION_MOVE | ACTION_ROTATE);
        if !is_hold { self.hold_locked = false; }
        self.falling = if first { Falling::new(piece, None) } else { Falling::new(piece, Some(&self.falling)) };
        if !ignore_blockout && self.consider_blockout() {
            self.state ^= ACTION_IHS;
            self.falling.irs = 0.0;
        } else if self.state & ACTION_IHS != 0 {
            self.state ^= ACTION_IHS;
            self.hold(ignore_blockout)?;
        } else {
            if self.falling.irs != 0.0 {
                // irs is only ever set while the engine sleeps, which it never does here; the rotation
                // amount would be ((irs % 4) + 4) % 4 of a number, so it is still an integer
                let a = self.falling.irs as i32;
                self.rotate(a);
                self.falling.irs = 0.0;
            }
            if !self.consider_blockout() && self.is_20g() { self.slam_to_floor(); }
        }
        Ok(())
    }

    fn consider_blockout(&mut self) -> bool {
        if legal(&self.board, &self.falling.abs_blocks()) { return false; }
        let mut clutched = false;
        if self.last_was_clear && self.o.clutch {
            let (oy, ohy) = (self.falling.y, self.falling.highest_y);
            while self.falling.fy() < FULL_H as f64 {
                self.falling.y += 1.0;
                self.falling.highest_y += 1.0;
                if legal(&self.board, &self.falling.abs_blocks()) { clutched = true; break; }
            }
            if !clutched { self.falling.y = oy; self.falling.highest_y = ohy; }
        }
        !clutched
    }

    fn hold(&mut self, ignore_blockout: bool) -> Result<bool, Throw> {
        if self.hold_locked || !self.o.allow_hold { return Ok(false); }
        self.hold_locked = !self.o.infinite_hold;
        if let Some(save) = self.held {
            self.held = Some(self.falling.sym);
            self.initiate(save, ignore_blockout, true, false)?;
        } else {
            self.held = Some(self.falling.sym);
            self.next_piece(ignore_blockout, true)?;
        }
        self.hold_locked = !self.o.infinite_hold;
        Ok(true)
    }

    fn slam_to_floor(&mut self) { while self.internal_fall(1.0) {} }

    fn hard_drop(&mut self) -> Result<(), Throw> {
        while self.internal_fall(1.0) {}
        self.lock(true)
    }

    // ── board mutations ──
    fn board_add(&mut self, cells: &[(f64, f64); 4], mino: u8, tag: i32) {
        self.take_pre_tick();
        for &(x, y) in cells.iter() {
            if y < 0.0 || y >= FULL_H as f64 || x < 0.0 || x >= W as f64 { continue; }
            self.board[y as usize][x as usize] = Some(Cell { mino, tag });
        }
    }

    /// clearBombsAndLines(placed): no bombs exist (usebombs is refused), so clearBombs only matters for
    /// the TypeError it throws when the lowest placed cell is below the board (state[y - 1] undefined).
    fn clear_bombs_and_lines(&mut self, placed: &[(f64, f64); 4]) -> Result<(f64, f64), Throw> {
        self.take_pre_tick();
        let mut lowest = FULL_H as f64;
        for &(_, y) in placed.iter() { if y < lowest { lowest = y; } }
        if lowest != 0.0 && lowest < 0.0 { return Err(Throw); }
        // clearLines
        let mut lines = Vec::new();
        let mut garbage_cleared = 0.0;
        for idx in 0..self.board.len() {
            let row = &self.board[idx];
            let mut full = true;
            let mut has_garbage = false;
            for x in 0..W {
                match row[x] { None => { full = false; break; } Some(c) => { if c.mino == GARBAGE { has_garbage = true; } } }
            }
            if full { lines.push(idx); if has_garbage { garbage_cleared += 1.0; } }
        }
        for &line in lines.iter().rev() { self.board.remove(line); self.board.push([None; W]); }
        Ok((lines.len() as f64, garbage_cleared))
    }

    /// insertGarbage({amount, size, column}) — rows inserted at the bottom, then
    /// `state.splice(fullHeight - amount - 1, amount)` on the grown array (JS splice semantics).
    fn insert_garbage(&mut self, amount: f64, size: f64, column: Option<f64>) {
        self.take_pre_tick();
        let col = column.unwrap_or(0.0); // `x >= null` compares against 0
        let n = amount as usize;
        let mut rows = Vec::with_capacity(n);
        for _ in 0..n {
            let mut row: Row = [None; W];
            for x in 0..W {
                let xf = x as f64;
                if !(xf >= col && xf < col + size) { row[x] = Some(Cell { mino: GARBAGE, tag: -1 }); }
            }
            rows.push(row);
        }
        self.board.splice(0..0, rows);
        let len = self.board.len() as f64;
        let start = FULL_H as f64 - amount - 1.0;
        let start = if start < 0.0 { js_max(len + start, 0.0) } else { js_min(start, len) } as usize;
        let count = js_max(0.0, js_min(amount, self.board.len() as f64 - start as f64)) as usize;
        self.board.drain(start..start + count);
    }

    // ── #lock ──
    fn lock(&mut self, hard: bool) -> Result<(), Throw> {
        self.hold_locked = false;
        let f = self.falling.clone();
        let s = &STATES[f.sym][f.rotation];
        let fy = f.fy();
        let mut placed = [(0.0, 0.0); 4];
        for i in 0..4 { placed[i] = (f.x + s[i].0 as f64, fy - s[i].1 as f64); }
        let tag = self.locks.len() as i32;
        self.board_add(&placed, f.sym as u8, tag);
        let (lines, garbage_cleared) = self.clear_bombs_and_lines(&placed)?;
        let pc = self.perfect_clear();
        let pc_b2b = pc && self.o.allclears && truthy(self.o.allclear_b2b);
        let mut broke = true; // brokeB2B !== false
        if lines > 0.0 {
            self.combo += 1.0;
            let spun = matches!(self.last_spin, Some(Spin::Mini) | Some(Spin::Normal));
            if (spun || lines >= 4.0) && !pc_b2b { self.b2b += 1.0; broke = false; }
            if pc_b2b { self.b2b += self.o.allclear_b2b; broke = false; }
            if broke { self.b2b = -1.0; }
        } else {
            self.combo = -1.0;
        }
        let spin = self.last_spin.unwrap_or(Spin::None);
        let g = garbage_calc(js_max(self.b2b, 0.0), js_max(self.combo, 0.0), lines, spin, self.o.b2b_chaining);
        let mut events: Vec<f64> = Vec::new();
        if g > 0.0 { events.push((g * self.gmult.get() + 0.0).floor()); }
        if pc && self.o.allclears { events.push((self.o.allclear_garbage * self.gmult.get()).floor()); }
        let mut garbage: Vec<f64> = events.into_iter().filter(|&v| v > 0.0).collect();
        if lines > 0.0 {
            self.last_was_clear = true;
            while !garbage.is_empty() {
                if garbage[0] == 0.0 { garbage.remove(0); continue; }
                let r = self.garbage.cancel(self.o, garbage[0], self.pieces);
                if r == 0.0 { garbage.remove(0); } else { garbage[0] = r; break; }
            }
        } else {
            self.last_was_clear = false;
            let cap = self.gcap.get();
            let tanked = self.garbage.tank(self.o, self.frame, cap, hard);
            let mut tank_events: Vec<(f64, f64)> = Vec::new(); // (iid, amount)
            for t in tanked.iter() {
                self.insert_garbage(t.amount, t.size, t.column);
                match tank_events.last_mut() {
                    Some(last) if last.0 == t.id => last.1 += t.amount,
                    _ => tank_events.push((t.id, t.amount)),
                }
            }
            for &(_, amt) in tank_events.iter() {
                self.garbage_events.push(GarbageRec { frame: self.frame, amt, lock_index: self.locks.len() });
            }
        }
        // falling.lock.pre: the harness reads the piece's cells (still the locked piece) in its y-down frame
        let mut cells = [(0i32, 0i32); 4];
        for i in 0..4 { cells[i] = (placed[i].0 as i32, (FULL_H as f64 - 1.0 - placed[i].1) as i32); }
        self.next_piece(false, false)?;
        self.last_spin = None;
        let topout = !legal(&self.board, &self.falling.abs_blocks());
        if !garbage.is_empty() {
            for ti in 0..self.targets.len() {
                let t = self.targets[ti];
                for &a in garbage.iter() { self.ige.send(t, a); }
            }
        }
        self.pieces += 1.0;

        // ── falling.lock listener (oracle-source.ts) ──
        let sent: f64 = garbage.iter().fold(0.0, |a, &b| a + b);
        let mut cleared_rows = Vec::new();
        if lines > 0.0 {
            let pre = match self.pre_tick { Some(p) => p, None => { self.fatal = Some(Fatal::NoPreTick); return Err(Throw); } };
            let mut g = pre;
            for &(col, row) in cells.iter() {
                let y_up = FULL_H as i32 - 1 - row;
                if y_up >= 0 && y_up < FULL_H as i32 && col >= 0 && col < W as i32 { g[y_up as usize][col as usize] = true; }
            }
            for y_up in 0..FULL_H { if g[y_up].iter().all(|&b| b) { cleared_rows.push(FULL_H as i32 - 1 - y_up as i32); } }
        }
        let allclear = self.perfect_clear();
        self.locks.push(LockRec {
            frame: self.frame, piece: f.sym, lines, spin, sent,
            b2b: js_max(self.b2b, 0.0), combo: js_max(self.combo, 0.0), garbage_cleared, allclear,
            cells, cleared_rows, snap: -1,
        });
        if topout { self.topout = true; }
        Ok(())
    }

    // ── input ──
    fn internal_shift(&mut self) {
        self.state |= ACTION_MOVE;
        let to = self.falling.at(self.falling.x + self.last_shift, self.falling.y, self.falling.rotation);
        if legal(&self.board, &to) {
            self.falling.x += self.last_shift;
            if self.falling.lock_resets < 31.0 { self.falling.lock_resets += 1.0; }
            self.state &= !(ROTATION_ALL | STATE_WALL);
            if self.is_20g() { self.slam_to_floor(); }
            if !self.should_lock() { self.falling.locking = 0.0; }
        } else {
            self.state |= STATE_WALL;
        }
    }

    fn process_shift(&mut self, left: bool, delta: f64) {
        let (das, arr) = (self.o.das, self.o.arr);
        let last = self.last_shift;
        let s = if left { &mut self.l_shift } else { &mut self.r_shift };
        if !s.held || last != s.dir { return; }
        let arr_delta = js_max(0.0, delta - js_max(0.0, das - s.das));
        s.das = js_min(s.das + delta, das);
        if s.das < das { return; }
        s.arr += arr_delta;
        if s.arr < arr { return; }
        let mult = if arr == 0.0 { W as f64 } else { (s.arr / arr).floor() };
        s.arr -= arr * mult;
        let mut i = 0.0;
        while i < mult { self.internal_shift(); i += 1.0; }
    }
    fn process_all_shift(&mut self, delta: f64) {
        self.process_shift(true, delta);
        self.process_shift(false, delta);
    }
    fn process_subframe(&mut self, sub: f64) -> Result<(), Throw> {
        if sub <= self.subframe { return Ok(()); }
        let delta = sub - self.subframe;
        self.process_all_shift(delta);
        self.fall(delta)?;
        self.subframe = sub;
        Ok(())
    }

    fn keydown(&mut self, sub: f64, key: u8, hoisted: bool) -> Result<(), Throw> {
        self.process_subframe(sub)?;
        match key {
            0 | 1 => {
                let das = if hoisted { self.o.das - self.o.dcd } else { 0.0 };
                let arr = self.o.arr;
                let s = if key == 0 { &mut self.l_shift } else { &mut self.r_shift };
                s.held = true;
                s.das = das;
                s.arr = arr;
                self.last_shift = s.dir;
                self.internal_shift();
            }
            2 => self.soft_drop = true,
            3 => self.rotate(-1),
            4 => self.rotate(1),
            5 => { if self.o.allow180 { self.rotate(2); } }
            6 => { if self.o.allow_harddrop && self.falling.safe_lock == 0.0 { self.hard_drop()?; } }
            7 => { self.hold(false)?; }
            _ => {}
        }
        Ok(())
    }

    fn keyup(&mut self, sub: f64, key: u8) -> Result<(), Throw> {
        self.process_subframe(sub)?;
        match key {
            0 => {
                self.l_shift.held = false;
                self.l_shift.das = 0.0;
                self.last_shift = if self.r_shift.held { self.r_shift.dir } else { self.last_shift };
                if self.o.cancel { self.r_shift.arr = self.o.arr; self.r_shift.das = 0.0; }
            }
            1 => {
                self.r_shift.held = false;
                self.r_shift.das = 0.0;
                self.last_shift = if self.l_shift.held { self.l_shift.dir } else { self.last_shift };
                if self.o.cancel { self.l_shift.arr = self.o.arr; self.l_shift.das = 0.0; }
            }
            2 => { self.state |= ACTION_SOFTDROP; self.soft_drop = false; }
            _ => {}
        }
        Ok(())
    }

    fn run_events(&mut self, evs: &[Ev]) -> Result<(), Throw> {
        for e in evs {
            match e {
                Ev::KeyDown { sub, key, hoisted } => self.keydown(*sub, *key, *hoisted)?,
                Ev::KeyUp { sub, key } => self.keyup(*sub, *key)?,
                Ev::Interaction { gameid, ackiid, amt, iid, size } => {
                    let amount = if self.o.network { self.ige.receive(*gameid, *ackiid, *amt) } else { *amt };
                    self.garbage.receive(GItem {
                        frame: MAX_SAFE_INTEGER - self.o.gspeed, amount, size: *size, cid: *iid, gameid: *gameid,
                    })?;
                }
                Ev::Confirm { iid, gameid, frame } => self.garbage.confirm(*iid, *gameid, *frame),
                Ev::Target { ids } => self.targets = ids.clone(),
            }
        }
        Ok(())
    }

    fn tick(&mut self, evs: &[Ev]) -> Result<(), Throw> {
        self.subframe = 0.0;
        if !evs.is_empty() { self.run_events(evs)?; }
        self.frame += 1.0;
        let d = 1.0 - self.subframe;
        self.process_all_shift(d);
        let d = 1.0 - self.subframe;
        self.fall(d)?;
        self.gravity.tick();
        self.gmult.tick();
        self.gcap.tick();
        Ok(())
    }

    /// The y-down sim board (cell codes: 0 empty, 1..7 IJLOSTZ, 8 garbage) and its provenance
    /// (-2 empty, -1 garbage, else the placing lock's index).
    pub fn snapshot(&self, out: &mut Vec<f64>) {
        for r in 0..FULL_H {
            let src = &self.board[FULL_H - 1 - r];
            for c in 0..W { out.push(match src[c] { None => 0.0, Some(cell) => (cell.mino + 1) as f64 }); }
        }
        for r in 0..FULL_H {
            let src = &self.board[FULL_H - 1 - r];
            for c in 0..W {
                out.push(match src[c] { None => -2.0, Some(cell) => if cell.mino == GARBAGE { -1.0 } else { cell.tag as f64 } });
            }
        }
    }
}

pub struct RunOut { pub engine_snaps: Vec<f64>, pub n_snaps: usize, pub threw: bool }

/// oracle-source.ts's tick loop. `frames[f]` holds the events of frame f in replay order.
pub fn run<'o>(o: &'o Opts, frames: &[Vec<Ev>]) -> Result<(Engine<'o>, RunOut), Fatal> {
    let mut snaps = Vec::new();
    let mut n_snaps = 0usize;
    let mut threw = false;
    let mut eng = match Engine::new(o) { Ok(e) => e, Err(_) => { return Ok(dead(o)); } };
    let empty: Vec<Ev> = Vec::new();
    let mut f = 0usize;
    while (f as f64) <= o.max_frame {
        eng.pre_tick = None;
        let evs = frames.get(f).unwrap_or(&empty);
        if eng.tick(evs).is_err() {
            if let Some(fatal) = eng.fatal.take() { return Err(fatal); }
            threw = true;
            break;
        }
        let have = n_snaps_assigned(&eng);
        if have < eng.locks.len() {
            eng.snapshot(&mut snaps);
            for l in eng.locks[have..].iter_mut() { l.snap = n_snaps as i32; }
            n_snaps += 1;
        }
        f += 1;
    }
    if threw { eng.topout = true; }
    Ok((eng, RunOut { engine_snaps: snaps, n_snaps, threw }))
}

fn n_snaps_assigned(e: &Engine) -> usize {
    // locks are snapped in order, so the first unsnapped one is found from the end
    let mut i = e.locks.len();
    while i > 0 && e.locks[i - 1].snap < 0 { i -= 1; }
    i
}

/// createEngine itself throwing (its first piece's spawn) is impossible for an empty board; kept so
/// the harness never panics.
fn dead(o: &Opts) -> (Engine<'_>, RunOut) {
    let e = Engine {
        o, board: vec![[None; W]; FULL_H], bag: Rng::new(o.seed), queue: Vec::new(), qpos: 0, held: None,
        hold_locked: false, falling: Falling::new(0, None), last_spin: None, last_was_clear: false,
        combo: -1.0, b2b: -1.0, pieces: 0.0, frame: 0.0, subframe: 0.0, state: 0,
        l_shift: Shift { held: false, arr: 0.0, das: 0.0, dir: -1.0 }, r_shift: Shift { held: false, arr: 0.0, das: 0.0, dir: 1.0 },
        last_shift: -1.0, soft_drop: false, gravity: Increase::new(0.0, 0.0, 0.0), gmult: Increase::new(0.0, 0.0, 0.0),
        gcap: Increase::new(0.0, 0.0, 0.0), garbage: GarbageQueue::new(o), ige: Ige { players: Vec::new(), iid: 0.0 },
        targets: Vec::new(), locks: Vec::new(), garbage_events: Vec::new(), topout: true, pre_tick: None, fatal: None,
    };
    (e, RunOut { engine_snaps: Vec::new(), n_snaps: 0, threw: true })
}

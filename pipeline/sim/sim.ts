/**
 * TetrioSim — frame-stepped TETR.IO replay simulator.
 *
 * Geometry (SRS kicks, collision, hard drop) is reused from td-opener-trainer's srs.ts.
 * Everything time-, garbage- or spin-related is new; the trainer has none of it.
 *
 * Board is 40 rows: rows 0..19 = buffer, rows 20..39 = visible field.
 */
import type { PieceType } from './vendor/core/types.ts';
import { BOARD_WIDTH } from './vendor/core/types.ts';
import type { Board, ActivePiece } from './vendor/core/srs.ts';
import { getPieceCells, isValidPosition, tryMove, tryRotate, hardDrop, setKickset, JLSZT_KICKS } from './vendor/core/srs.ts';
import { GarbageQueue } from './garbage-queue.ts';

export const H = 40;                  // total rows (20 buffer + 20 visible)
export const SPAWN_ROW = 18;
const BAG: PieceType[] = ['Z', 'L', 'O', 'S', 'I', 'J', 'T'];
export const GARBAGE = 'G' as unknown as PieceType;   // sentinel cell type

// ── PRNG (MINSTD; Poyo-SSB/tetrio-bot-docs Piece_RNG.md) ──
export class Rng {
  private t: number;
  constructor(seed: number) { let t = seed % 2147483647; if (t <= 0) t += 2147483646; this.t = t; }
  next() { return (this.t = (16807 * this.t) % 2147483647); }
  nextFloat() { return (this.next() - 1) / 2147483646; }
  shuffle<T>(a: T[]): T[] {
    for (let i = a.length - 1; i !== 0; i--) {
      const r = Math.floor(this.nextFloat() * (i + 1));
      [a[i], a[r]] = [a[r]!, a[i]!];
    }
    return a;
  }
}
export function makeQueue(seed: number, n: number): PieceType[] {
  const rng = new Rng(seed); const out: PieceType[] = [];
  while (out.length < n) out.push(...rng.shuffle([...BAG]));
  return out.slice(0, n);
}

// ── attack table (hypothesis; fitted against the 2209-event oracle) ──
export interface AttackTable {
  single: number; double: number; triple: number; quad: number;
  tss: number; tsd: number; tst: number; mtss: number; mtsd: number;
  b2b: number; allclear: number;
  comboTable: number[];
}
export const DEFAULT_TABLE: AttackTable = {
  single: 0, double: 1, triple: 2, quad: 4,
  tss: 2, tsd: 4, tst: 6, mtss: 0, mtsd: 1,
  b2b: 1, allclear: 10,
  comboTable: [0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4, 4, 5],
};

export interface Handling { das: number; arr: number; sdf: number; dcd: number }
export interface InEvent { frame: number; sub: number; type: string; key?: string; hoisted?: boolean }
export interface InGarbage {
  frame: number; amt: number; x: number; size: number;
  /** frame of the matching interaction_confirm, if any (halp1/triangle's GarbageQueue.confirm
   *  rewrites the queued entry's frame on confirmation, so this is the real arrival time) */
  confirmFrame?: number;
  /** iid of the interaction (triangle stores this as the queue entry's cid) */
  cid?: number;
  gameid?: number;
  /** the opponent's ack of MY outgoing sends when it sent this batch (network-cancel protocol) */
  ackiid?: number;
}

export interface ClearRecord {
  frame: number; piece: PieceType; lines: number; spin: 'none' | 'mini' | 'full';
  attack: number; sent: number; cancelled: number; b2b: number; combo: number;
  cells: { col: number; row: number }[];      // where the piece locked
  garbageCleared: number;
  clearedRows: number[];   // pre-clear row indices that were full (bottom-most last)
}
export interface SimResult {
  lines: number; placed: number; holds: number;
  clears: Record<string, number>;
  garbage: { sent: number; received: number; cleared: number; attack: number };
  topbtb: number; topcombo: number;
  boards: Board[];            // board AFTER each placement
  records: ClearRecord[];
  events: { frame: number; kind: 'lock' | 'garbage'; }[];
  locks: { frame: number; piece: PieceType; cells: {col:number;row:number}[]; cleared: number; spin: 'none'|'mini'|'full'; allclear: boolean }[];
  garbageEvents: { frame: number; amt: number; lockIndex: number }[];
  provSnaps: (number|null)[][][];   // provenance grid after each lock
  topout: boolean;
}

const emptyRow = () => new Array<PieceType | null>(BOARD_WIDTH).fill(null);
export function emptyBoard(): Board {
  return Array.from({ length: H }, emptyRow) as Board;
}

/**
 * TETR.IO's back-to-back bonus as a function of the b2b chain count — the LOGARITHMIC "level" from
 * the reference attack calculator (skysomorphic/tetrio-attack-calculator `b2bCountToLevel`), not the
 * sim's historical `>=3 ? 2 : 1` cap. Ground truth: 1 for 1-2, 2 for 3-7, 3 for 8-23, 4 for 24-66,
 * 5 for 67-184, 6 for 185-503, 7 for 504-1369, 8 above.
 */
export function b2bLevel(count: number): number {
  if (count <= 0) return 0;
  if (count <= 2) return 1;
  if (count <= 7) return 2;
  if (count <= 23) return 3;
  if (count <= 66) return 4;
  if (count <= 184) return 5;
  if (count <= 503) return 6;
  if (count <= 1369) return 7;
  return 8;
}

/** The T kick-candidate index a rotation used, from its displacement (−1 if none). T only. */
export function tKickIndex(from: number, to: number, dx: number, dy: number): number {
  const seq = JLSZT_KICKS[`${from}->${to}` as keyof typeof JLSZT_KICKS] as readonly [number, number][] | undefined;
  if (!seq) return -1;
  for (let i = 0; i < seq.length; i++) if (seq[i]![0] === dx && seq[i]![1] === dy) return i;
  return -1;
}

/**
 * 3-corner T-spin detection. Returns 'full' | 'mini' | 'none'.
 *
 * The mini→full upgrade for a spin that is not front-filled has two rules the caller selects with
 * `rule`. 'anykick' (the historical default): ANY wall-kick upgrades. 'lastkick': only the last
 * kick candidate (index 4, the TST-style kick) upgrades — this is the ORIGINAL cold-clear /
 * guideline rule (see cc-tspin.ts). Which one TETR.IO actually uses is decided by the replay ige
 * attack values, not by cold-clear; `kickIndex` is the candidate the reaching rotation used.
 */
export function detectTSpin(board: Board, p: ActivePiece, lastWasRotation: boolean, usedKick: boolean,
                            kickIndex = -1, rule: 'anykick' | 'lastkick' = 'anykick'): 'none' | 'mini' | 'full' {
  if (p.type !== 'T' || !lastWasRotation) return 'none';
  // T centre in trainer coords: bounding-box offset (1,1)
  const cx = p.col + 1, cy = p.row + 1;
  const occupied = (c: number, r: number) =>
    c < 0 || c >= BOARD_WIDTH || r >= H ? true : r < 0 ? false : board[r]![c] !== null;
  const corners = [[-1, -1], [1, -1], [-1, 1], [1, 1]] as const;
  const filled = corners.map(([dc, dr]) => occupied(cx + dc, cy + dr));
  const total = filled.filter(Boolean).length;
  if (total < 3) return 'none';
  // "front" corners are the two on the side the T points toward
  const frontByRot: Record<number, number[]> = { 0: [0, 1], 1: [1, 3], 2: [2, 3], 3: [0, 2] };
  const front = frontByRot[p.rotation]!;
  const frontFilled = front.filter(i => filled[i]).length;
  if (frontFilled === 2) return 'full';
  const upgrade = rule === 'lastkick' ? kickIndex === 4 : usedKick;
  return upgrade ? 'full' : 'mini';   // kicked-into-slot upgrades a mini to full
}

export function simulate(
  events: InEvent[], garbageIn: InGarbage[], handling: Handling, seed: number,
  endFrame: number, table: AttackTable,
  opts: { garbagespeed: number; garbagecap: number; locktime: number; gravity: number; sdfMode?: 'abs'|'mult'; eventsFirst?: boolean; insertMode?: 'onPlace'|'immediate'; cancelMode?: 'all'|'inTransit'; insertAfterClear?: boolean; arriveFrame?: 'outer'|'ige'; irs?: boolean; ihs?: boolean; are?: number; lineclearAre?: number; acEmit?: 'separate'|'combined'; acMode?: 'flat'|'b2bonly'|'none'|'replace';
          blockout?: 'strict'|'clutch'|'shiftup'; subframe?: boolean; kickset?: 'SRS'|'SRS+'; specialBonus?: boolean; readyFrom?: 'interaction'|'confirm'; queue?: 'flat'|'reference'; tspinRule?: 'anykick'|'lastkick'; attackModel?: 'legacy'|'exact';
          /** opt-in per-frame trace of the falling piece (col/row/rotation), for the Triangle
           *  frame-differential harness. Behaviour-preserving: called at end of each frame only. */
          trace?: (frame: number, cells: { col: number; row: number }[], rotation: number, type: string) => void },
): SimResult {
  setKickset(opts.kickset ?? 'SRS');
  const queue = makeQueue(seed, 4000);
  let qi = 0;
  let board: Board = emptyBoard();
  let hold: PieceType | null = null, holdUsed = false;
  let lines = 0, placed = 0, holds = 0, topout = false;
  let lastClearWasLines = false;     // did the previous placement clear? gates 'clutch'
  let b2b = -1, combo = -1, topbtb = 0, topcombo = 0;
  let sentTotal = 0, recvTotal = 0, clearedTotal = 0, attackTotal = 0;
  const clears: Record<string, number> = {
    singles: 0, doubles: 0, triples: 0, quads: 0, pentas: 0,
    tspinsingles: 0, tspindoubles: 0, tspintriples: 0,
    minitspinsingles: 0, minitspindoubles: 0, minitspins: 0, realtspins: 0, allclear: 0,
  };
  const boards: Board[] = [], records: ClearRecord[] = [];
  let prov: (number|null)[][] = Array.from({ length: H }, () => new Array<number|null>(BOARD_WIDTH).fill(null));
  const provSnaps: (number|null)[][][] = [];
  const locks: SimResult['locks'] = [];
  const garbageEvents: SimResult['garbageEvents'] = [];
  const evLog: { frame: number; kind: 'lock' | 'garbage' }[] = [];

  // Network garbage-cancel protocol (triangle's IGEHandler, engine/multiplayer/ige.mjs). Incoming
  // garbage is netted against MY still-unacknowledged outgoing sends BEFORE it enters my queue — a
  // separate layer from the local queue cancel below (that one is my attack vs my received garbage).
  // The batch's `ackiid` says how many of my sends the opponent had processed; my outgoing with
  // iid <= ackiid are dropped, and the incoming cancels 1-for-1 against the rest. Missing this made
  // the sim receive garbage the real game had already mutually cancelled (root of 163 drift rounds).
  const igeOut: { iid: number; amount: number }[] = [];
  let igeSendIid = 0;
  const igeReceive = (amount: number, ackiid: number | undefined): number => {
    if (ackiid == null) return amount;      // pre-network replays: no protocol, take the raw amount
    let running = amount, w = 0;
    for (const item of igeOut) {
      if (item.iid <= ackiid) continue;     // already acknowledged by the opponent — drop it
      const amt = Math.min(item.amount, running);
      item.amount -= amt; running -= amt;
      if (item.amount > 0) igeOut[w++] = item;
    }
    igeOut.length = w;
    return running;
  };
  // pending garbage queue: entries become insertable at frame + garbagespeed
  const pending: { ready: number; amt: number; x: number; size: number }[] = [];
  // Faithful port of the reference queue (confirm-gated insertion, cancellable while
  // unconfirmed, frame-sorted). Selected with opts.queue='reference'.
  const useRefQ = opts.queue === 'reference';
  const refQ = new GarbageQueue(opts.garbagespeed);
  const qEvents: { frame: number; kind: 'receive'|'confirm'; g: InGarbage }[] = [];
  if (useRefQ) {
    for (const g of garbageIn) {
      qEvents.push({ frame: g.frame, kind: 'receive', g });
      if (g.confirmFrame != null) qEvents.push({ frame: g.confirmFrame, kind: 'confirm', g });
    }
    qEvents.sort((a, b) => a.frame - b.frame);
  }
  let qi2 = 0;
  const drainRefQ = (frame: number, hard: boolean) => {
    for (const t of refQ.tank(frame, opts.garbagecap, hard)) {
      insertGarbage(t.amount, t.x, t.size);
      garbageEvents.push({ frame, amt: t.amount, lockIndex: locks.length });
    }
  };
  const gq = [...garbageIn].sort((a, b) => a.frame - b.frame);
  let gi = 0;

  let piece: ActivePiece = { type: queue[qi++]!, rotation: 0, col: 3, row: SPAWN_ROW };
  let lastWasRotation = false, usedKick = false, lastKickIndex = -1;
  // DAS/ARR ported verbatim from @haelp/teto's Engine (#activateShift / #processShift /
  // #__internal_shift, engine/index.mjs). The `das` counter charges UP from 0 (fresh tap) or
  // `das - dcd` (hoisted) to `handling.das`; `arr` starts at `handling.arr` and carries a
  // FRACTIONAL remainder across subframes, firing floor(arr/handling.arr) shifts each step. The old
  // count-down `dasTimer/arrTimer` matched only the simple case; it lost the leftover at the DAS→ARR
  // transition and could not fire multiple shifts per subframe, which is why every garbage-free lock
  // divergence vs the oracle carried a COLUMN error (lock-diff-agg.mjs: 37 rounds, 0 pure-row).
  const lShift = { held: false, das: 0, arr: 0, dir: -1 };
  const rShift = { held: false, das: 0, arr: 0, dir: 1 };
  let lastShift = 0;                  // -1 | 0 | +1 — the active direction (triangle's input.lastShift)
  let softHeld = false, gravAcc = 0, groundFrames = 0;
  const held = new Set<string>();
  let areUntil = -1;                 // frames before which no piece exists (entry delay)

  const spawn = (t: PieceType) => {
    piece = { type: t, rotation: 0, col: 3, row: SPAWN_ROW };
    holdUsed = false; lastWasRotation = false; usedKick = false; lastKickIndex = -1; groundFrames = 0; gravAcc = 0;
    // IRS: a rotation key still held at spawn applies immediately
    if (opts.irs && (held.has('rotateCW') || held.has('rotateCCW'))) {
      const n = tryRotate(board, piece, held.has('rotateCW') ? 1 : -1);
      if (n) { usedKick = n.col !== piece.col || n.row !== piece.row;
        lastKickIndex = piece.type === 'T' ? tKickIndex(piece.rotation, n.rotation, n.col - piece.col, n.row - piece.row) : -1;
        piece = n; lastWasRotation = true; }
    }
    if (!isValidPosition(board, piece)) {
      // A blocked spawn is not necessarily death. halp1/triangle's #considerBlockout
      // walks the piece UP through the buffer until it fits, gated on the previous
      // placement having cleared lines ("clutch"). 'shiftup' drops that gate.
      const mode = opts.blockout ?? 'strict';
      const mayClutch = mode === 'shiftup' || (mode === 'clutch' && lastClearWasLines);
      let rescued = false;
      if (mayClutch) {
        for (let row = SPAWN_ROW - 1; row >= 0; row--) {
          const cand = { ...piece, row };
          if (isValidPosition(board, cand)) { piece = cand; rescued = true; break; }
        }
      }
      if (!rescued) topout = true;
    }
  };
  const shift = (d: number) => { const n = tryMove(board, piece, d, 0); if (n) { piece = n; lastWasRotation = false; groundFrames = 0; } };
  // triangle's #activateShift: charge DAS (0 fresh, or `das - dcd` when the direction was already
  // held at spawn) and arm ARR at handling.arr, then this direction becomes lastShift.
  const activateShift = (s: { held: boolean; das: number; arr: number; dir: number }, hoisted?: boolean) => {
    s.held = true;
    s.das = hoisted ? handling.das - handling.dcd : 0;
    s.arr = handling.arr;
    lastShift = s.dir;
  };
  const grounded = () => tryMove(board, piece, 0, 1) === null;

  function insertGarbage(amt: number, x: number, size: number) {
    const b = board.map(r => [...r]) as (PieceType | null)[][];
    for (let i = 0; i < amt; i++) {
      b.shift();
      const row = emptyRow();
      for (let c = 0; c < BOARD_WIDTH; c++) row[c] = GARBAGE;
      for (let s = 0; s < size; s++) row[(x + s) % BOARD_WIDTH] = null;
      b.push(row);
    }
    board = b as Board;
    for (let i = 0; i < amt; i++) {
      prov.shift();
      const pr = new Array<number|null>(BOARD_WIDTH).fill(-1);
      for (let sx = 0; sx < size; sx++) pr[(x + sx) % BOARD_WIDTH] = null;
      prov.push(pr);
    }
    recvTotal += amt;
  }

  function lockPiece(frame: number) {
    const cells = getPieceCells(piece);
    const spin = detectTSpin(board, piece, lastWasRotation, usedKick, lastKickIndex, opts.tspinRule ?? 'anykick');
    const b = board.map(r => [...r]) as (PieceType | null)[][];
    const myIndex = locks.length;
    for (const { col, row } of cells) if (row >= 0 && row < H) { b[row]![col] = piece.type; prov[row]![col] = myIndex; }

    // find + clear full rows
    let cleared = 0, garbageRows = 0;
    // Scanning bottom-up and splicing keeps `row` in ORIGINAL coordinates: splice(row,1)
    // only shifts rows BELOW row, which this loop has already visited.
    const clearedRows: number[] = [];
    for (let row = H - 1; row >= 0; row--) {
      if (b[row]!.every(c => c !== null)) {
        if (b[row]!.some(c => c === GARBAGE)) garbageRows++;
        clearedRows.push(row);
        b.splice(row, 1); prov.splice(row, 1); cleared++;
      }
    }
    while (b.length < H) { b.unshift(emptyRow()); prov.unshift(new Array<number|null>(BOARD_WIDTH).fill(null)); }
    board = b as Board;
    lines += cleared; clearedTotal += garbageRows; placed++;

    // scoring
    let atk = 0, sawAllclear = false;
    const isDifficult = cleared >= 4 || (spin !== 'none' && cleared > 0);
    if (cleared > 0) {
      combo++; topcombo = Math.max(topcombo, combo);
      if (spin === 'full') {
        atk = cleared === 1 ? table.tss : cleared === 2 ? table.tsd : table.tst;
        if (cleared === 1) clears.tspinsingles++; else if (cleared === 2) clears.tspindoubles++; else clears.tspintriples++;
        clears.realtspins++;
      } else if (spin === 'mini') {
        atk = cleared === 1 ? table.mtss : table.mtsd;
        if (cleared === 1) clears.minitspinsingles++; else clears.minitspindoubles++;
        clears.minitspins++;
      } else {
        atk = cleared === 1 ? table.single : cleared === 2 ? table.double : cleared === 3 ? table.triple : cleared === 4 ? table.quad : table.quad + 1;
        if (cleared === 1) clears.singles++; else if (cleared === 2) clears.doubles++;
        else if (cleared === 3) clears.triples++; else if (cleared === 4) clears.quads++; else clears.pentas++;
      }
      const exact = opts.attackModel === 'exact';
      if (isDifficult) {
        b2b++; topbtb = Math.max(topbtb, b2b);
        // 'legacy' (observed, fitted): b2b1->+1, b2b2->+1, b2b3+->+2. 'exact': TETR.IO's logarithmic
        // b2bCountToLevel — identical for b2b 1-7, higher for b2b>=8 (which the fitted rule capped).
        if (b2b > 0) atk += exact ? b2bLevel(b2b) : (b2b >= 3 ? 2 : 1);
      } else b2b = -1;
      // combo is a MULTIPLIER: base*(1+0.25*combo). TETR.IO EXCEPTION (attack calculator): when the
      // base+b2b attack is 0 (a comboing single), the value is floor(log1p(combo*1.25)) instead of 0,
      // so a long single-combo still sends. The fitted 'legacy' path multiplied 0 and sent nothing.
      if (combo > 0) atk = (exact && atk === 0) ? Math.floor(Math.log1p(combo * 1.25))
                                                : Math.floor(atk * (1 + 0.25 * combo));
      // Special bonus: a flat +1 when a spin or a quad CLEARS GARBAGE. In halp1/triangle this
      // is `gSpecialBonus`, added AFTER the garbage multiplier
      // (`garbage.garbage * multiplier + gSpecialBonus`), so it is not scaled by combo or b2b.
      if (opts.specialBonus && garbageRows > 0 && (spin !== 'none' || cleared >= 4)) atk += 1;
      // All-clear bonus. MEASURED (pc-oracle.ts, 158/158 rounds): TETR.IO does NOT fold this into
      // the line-clear attack — it emits a SECOND ige event of amount exactly 10 at the same
      // frame, after the base attack. Folding them into one value (1+10=11) is why the verified
      // prefix collapsed to zero in every round containing a perfect clear: the matcher compared
      // the sim's 11 against the truth's 1 and truncated at the first PC.
      let bonus = 0;
      if (board.every(r => r.every(c => c === null))) {
        clears.allclear++; sawAllclear = true;
        const m = opts.acMode ?? 'flat';
        if (m === 'flat') bonus = table.allclear;
        else if (m === 'b2bonly') { if (b2b > 0) bonus = table.allclear; }
        else if (m === 'replace') { atk = 0; bonus = table.allclear; }
        // 'none' adds nothing
      }
      if ((opts.acEmit ?? 'separate') === 'combined') { atk += bonus; bonus = 0; }

      // cancel pending garbage first, then send the remainder
      const emit = (amount: number) => {
        attackTotal += amount;
        let remaining = amount;
        if (useRefQ) {
          // cancel() ignores frame on purpose: unconfirmed garbage is un-insertable but
          // still cancellable, which is the asymmetry the scalar knobs could not express
          remaining = refQ.cancel(amount);
        } else
        for (let pi = 0; pi < pending.length && remaining > 0; ) {
          const p0 = pending[pi]!;
          // with passthrough disabled, only garbage still IN TRANSIT can be cancelled
          if (opts.cancelMode === 'inTransit' && p0.ready <= frame) { pi++; continue; }
          const take = Math.min(remaining, p0.amt);
          p0.amt -= take; remaining -= take;
          if (p0.amt === 0) pending.splice(pi, 1); else pi++;
        }
        sentTotal += remaining;
        // register the outgoing send so a later incoming batch can be netted against it (igeHandler.send)
        if (remaining > 0) igeOut.push({ iid: ++igeSendIid, amount: remaining });
        records.push({ frame, piece: piece.type, lines: cleared, spin, attack: amount, sent: remaining,
          cancelled: amount - remaining, b2b, combo, cells, garbageCleared: garbageRows, clearedRows });
      };
      emit(atk);
      if (bonus > 0) emit(bonus);
      if (opts.insertAfterClear) {
        let budget = opts.garbagecap;
        while (budget > 0 && pending.length > 0 && pending[0]!.ready <= frame) {
          const p0 = pending[0]!; const take = Math.min(budget, p0.amt);
          insertGarbage(take, p0.x, p0.size);
          garbageEvents.push({ frame, amt: take, lockIndex: locks.length });
          p0.amt -= take; budget -= take; if (p0.amt === 0) pending.shift();
        }
      }
    } else {
      combo = -1;
      if (useRefQ) { drainRefQ(frame, true); }
      else {
      // no clear → pending garbage rises, up to the cap
      let budget = opts.garbagecap;
      while (budget > 0 && pending.length > 0 && pending[0]!.ready <= frame) {
        const p0 = pending[0]!;
        const take = Math.min(budget, p0.amt);
        insertGarbage(take, p0.x, p0.size);
      garbageEvents.push({ frame, amt: take, lockIndex: locks.length });
        p0.amt -= take; budget -= take;
        if (p0.amt === 0) pending.shift();
      }
      }
    }
    lastClearWasLines = cleared > 0;
    locks.push({ frame, piece: piece.type, cells, cleared, spin, allclear: sawAllclear });
    provSnaps.push(prov.map(r => [...r]));
    boards.push(board);
    evLog.push({ frame, kind: 'lock' });
    const delay = cleared > 0 ? (opts.lineclearAre ?? 0) : (opts.are ?? 0);
    areUntil = frame + delay;
    spawn(queue[qi++]!);
    if (opts.ihs && held.has('hold') && !holdUsed && !topout) {
      const prev = hold; hold = piece.type; holds++;
      spawn(prev ?? queue[qi++]!); holdUsed = true;
    }
  }

  const evs = [...events].sort((a, b) => a.frame - b.frame || a.sub - b.sub);
  let ei = 0;
  for (let f = 0; f <= endFrame && !topout; f++) {
    if (useRefQ) {
      while (qi2 < qEvents.length && qEvents[qi2]!.frame <= f) {
        const q = qEvents[qi2++]!;
        if (q.kind === 'receive')
          refQ.receive({ amount: q.g.amt, size: q.g.size, x: q.g.x,
                         cid: q.g.cid ?? 0, gameid: q.g.gameid ?? 0 });
        else refQ.confirm(q.g.cid ?? 0, q.g.gameid ?? 0, q.frame);
      }
    }
    while (gi < gq.length && gq[gi]!.frame <= f) {
      const g = gq[gi++]!;
      // net the incoming against my un-acked outgoing sends BEFORE it enters the queue (igeHandler)
      const net = igeReceive(g.amt, g.ackiid);
      if (net <= 0) continue;
      // triangle's GarbageQueue.confirm(cid, gameid, frame) overwrites the queued entry's
      // frame when the server confirms it, so 'confirm' uses that instead of arrival.
      const arriveAt = (opts.readyFrom === 'confirm' && g.confirmFrame != null) ? g.confirmFrame : g.frame;
      pending.push({ ready: arriveAt + opts.garbagespeed, amt: net, x: g.x, size: g.size });
    }
    if (opts.insertMode === 'immediate') {
      let budget = opts.garbagecap;
      while (budget > 0 && pending.length > 0 && pending[0]!.ready <= f) {
        const p0 = pending[0]!; const take = Math.min(budget, p0.amt);
        insertGarbage(take, p0.x, p0.size);
        garbageEvents.push({ frame: f, amt: take, lockIndex: locks.length });
        p0.amt -= take; budget -= take; if (p0.amt === 0) pending.shift();
      }
    }
    // DAS/ARR advanced by dt frames, ported from triangle's #processShift. TETR.IO records inputs to
    // 0.1-frame precision and runs its handling on that clock; at arr=2 a one-frame rounding error is
    // a whole cell of movement, which is why this is separable from gravity and lock delay.
    const processShift = (s: typeof lShift, dt: number) => {
      if (!s.held || lastShift !== s.dir) return;
      // the part of dt left AFTER finishing the DAS charge spills into ARR this same subframe
      const arrDelta = Math.max(0, dt - Math.max(0, handling.das - s.das));
      s.das = Math.min(s.das + dt, handling.das);
      if (s.das < handling.das) return;
      s.arr += arrDelta;
      if (s.arr < handling.arr) return;
      const mult = handling.arr === 0 ? BOARD_WIDTH : Math.floor(s.arr / handling.arr);
      s.arr -= handling.arr * mult;
      for (let i = 0; i < mult; i++) shift(s.dir);
    };
    const dasArr = (dt: number) => { processShift(lShift, dt); processShift(rShift, dt); };
    // triangle's #fall(delta), ported (engine/index.mjs): fall = gravity*delta, and soft drop replaces
    // it with a floored gravity*delta*sdf (sdf===41 is the instant 400*delta). The floor `0.05*sdf` is
    // NOT scaled by delta — it is per-CALL — so soft drop is applied once per subframe step, exactly as
    // triangle applies #fall once per #processSubframe. The earlier "additive slam is optimal" verdict
    // was an ILLUSION from grafting this formula onto a FRAME-ONCE gravity; the full Triangle oracle
    // (same g=0.02) reproduces the real ige 4.4x better than the old sim, so the fix is the per-subframe
    // interleave below, not the additive rate. Fractional fall is carried in gravAcc across subframes.
    const gravityStep = (delta: number) => {
      let fall = opts.gravity * delta;
      if (softHeld) fall = handling.sdf === 41 ? 400 * delta : Math.max(opts.gravity * delta * handling.sdf, 0.05 * handling.sdf);
      gravAcc += fall;
      while (gravAcc >= 1) { const n = tryMove(board, piece, 0, 1); if (!n) { gravAcc = 0; break; } piece = n; lastWasRotation = false; gravAcc -= 1; }
    };
    // Lock delay stays frame-quantised (the client's lock clock ticks per frame): a grounded piece
    // locks after locktime frames of rest.
    const lockCheck = () => {
      if (grounded()) { if (++groundFrames >= opts.locktime) lockPiece(f); }
      else groundFrames = 0;
    };
    const continuous = () => {
      if (!opts.subframe) dasArr(1);
      gravityStep(1);
      lockCheck();
    };
    const applyEvent = (e: InEvent) => {
      if (e.type === 'keydown') {
        if (e.key) held.add(e.key);
        if (f < areUntil) return;            // entry delay: no piece to control yet
        switch (e.key) {
          // triangle's #keydown for a move: #activateShift then an immediate #__internal_shift (the
          // tap). `hoisted` = the client recorded this direction as already held when the piece
          // spawned, so DAS is pre-charged to `das - dcd` (only `dcd` frames of charge remain). arr
          // starts at `handling.arr`, so the first auto-repeat fires the instant DAS completes.
          case 'moveLeft': activateShift(lShift, e.hoisted); shift(-1); break;
          case 'moveRight': activateShift(rShift, e.hoisted); shift(1); break;
          case 'softDrop': softHeld = true; break;
          case 'rotateCW': case 'rotateCCW': {
            const before = { c: piece.col, r: piece.row, rot: piece.rotation };
            const n = tryRotate(board, piece, e.key === 'rotateCW' ? 1 : -1);
            if (n) { usedKick = n.col !== before.c || n.row !== before.r;
              lastKickIndex = piece.type === 'T' ? tKickIndex(before.rot, n.rotation, n.col - before.c, n.row - before.r) : -1;
              piece = n; lastWasRotation = true; groundFrames = 0; }
            break;
          }
          case 'hold': {
            if (!holdUsed) {
              const prev = hold; hold = piece.type; holds++;
              spawn(prev ?? queue[qi++]!); holdUsed = true;
            }
            break;
          }
          case 'hardDrop': piece = hardDrop(board, piece); lockPiece(f); break;
        }
      } else if (e.type === 'keyup') {
        if (e.key) held.delete(e.key);
        // triangle's #keyup: release the shift, and if the OTHER direction is still held, resume it
        // from scratch (das=0, arr re-armed) and hand it lastShift. The old model dropped to dir=0
        // and never resumed the other direction (measured 0 such releases at the time, but the port
        // matches the engine so the branch is faithful rather than merely rare).
        if (e.key === 'moveLeft') {
          lShift.held = false; lShift.das = 0;
          if (rShift.held) { lastShift = rShift.dir; rShift.arr = handling.arr; rShift.das = 0; }
          else if (lastShift === -1) lastShift = 0;
        }
        if (e.key === 'moveRight') {
          rShift.held = false; rShift.das = 0;
          if (lShift.held) { lastShift = lShift.dir; lShift.arr = handling.arr; lShift.das = 0; }
          else if (lastShift === 1) lastShift = 0;
        }
        if (e.key === 'softDrop') softHeld = false;
      }
    };
    const applyEvents = () => {
      while (ei < evs.length && evs[ei]!.frame === f && !topout) applyEvent(evs[ei++]!);
    };

    if (opts.subframe) {
      // Match triangle's #processSubframe(subframe): advance BOTH DAS/ARR and gravity(#fall) to the
      // event's EXACT subframe (firing any shift/fall that completes in between), THEN handle the event.
      // Interleaving fall per subframe — not once per frame — is what lets soft drop match the client
      // (its per-call floor makes it event-density dependent) and is why the oracle reproduces the real
      // ige far better. Lock delay stays frame-quantised (lockCheck once, at frame end).
      let cur = 0;                            // subframe position within this frame, in [0,1]
      const stepTo = (to: number) => { const d = to - cur; if (d > 0) { dasArr(d); gravityStep(d); cur = to; } };
      while (ei < evs.length && !topout) {
        const e = evs[ei]!;
        if (e.frame > f) break;
        const es = Math.min(1, Math.max(cur, e.sub ?? 0));
        stepTo(es);
        if (topout) break;
        ei++; applyEvent(e);
      }
      if (!topout) stepTo(1);
      if (!topout) lockCheck();
    } else if (opts.eventsFirst) { applyEvents(); continuous(); } else { continuous(); applyEvents(); }
    if (opts.trace && !topout && f >= areUntil) opts.trace(f, getPieceCells(piece), piece.rotation, piece.type);
  }
  return { lines, placed, holds, clears, topbtb, topcombo,
    garbage: { sent: sentTotal, received: recvTotal, cleared: clearedTotal, attack: attackTotal },
    boards, records, events: evLog, locks, garbageEvents, provSnaps, topout };
}

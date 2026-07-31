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
import { getPieceCells, isValidPosition, tryMove, tryRotate, hardDrop } from './vendor/core/srs.ts';

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
export interface InEvent { frame: number; sub: number; type: string; key?: string }
export interface InGarbage { frame: number; amt: number; x: number; size: number }

export interface ClearRecord {
  frame: number; piece: PieceType; lines: number; spin: 'none' | 'mini' | 'full';
  attack: number; sent: number; cancelled: number; b2b: number; combo: number;
  cells: { col: number; row: number }[];      // where the piece locked
  garbageCleared: number;
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

/** 3-corner T-spin detection. Returns 'full' | 'mini' | 'none'. */
export function detectTSpin(board: Board, p: ActivePiece, lastWasRotation: boolean, usedKick: boolean): 'none' | 'mini' | 'full' {
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
  return usedKick ? 'full' : 'mini';   // kicked-into-slot upgrades a mini to full
}

export function simulate(
  events: InEvent[], garbageIn: InGarbage[], handling: Handling, seed: number,
  endFrame: number, table: AttackTable,
  opts: { garbagespeed: number; garbagecap: number; locktime: number; gravity: number; sdfMode?: 'abs'|'mult'; eventsFirst?: boolean; insertMode?: 'onPlace'|'immediate'; cancelMode?: 'all'|'inTransit'; insertAfterClear?: boolean; arriveFrame?: 'outer'|'ige'; irs?: boolean; ihs?: boolean; are?: number; lineclearAre?: number; acEmit?: 'separate'|'combined'; acMode?: 'flat'|'b2bonly'|'none'|'replace';
          blockout?: 'strict'|'clutch'|'shiftup' },
): SimResult {
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

  // pending garbage queue: entries become insertable at frame + garbagespeed
  const pending: { ready: number; amt: number; x: number; size: number }[] = [];
  const gq = [...garbageIn].sort((a, b) => a.frame - b.frame);
  let gi = 0;

  let piece: ActivePiece = { type: queue[qi++]!, rotation: 0, col: 3, row: SPAWN_ROW };
  let lastWasRotation = false, usedKick = false;
  let dir = 0, dasTimer = 0, arrTimer = 0, softHeld = false, gravAcc = 0, groundFrames = 0;
  const held = new Set<string>();
  let areUntil = -1;                 // frames before which no piece exists (entry delay)

  const spawn = (t: PieceType) => {
    piece = { type: t, rotation: 0, col: 3, row: SPAWN_ROW };
    holdUsed = false; lastWasRotation = false; usedKick = false; groundFrames = 0; gravAcc = 0;
    // IRS: a rotation key still held at spawn applies immediately
    if (opts.irs && (held.has('rotateCW') || held.has('rotateCCW'))) {
      const n = tryRotate(board, piece, held.has('rotateCW') ? 1 : -1);
      if (n) { usedKick = n.col !== piece.col || n.row !== piece.row; piece = n; lastWasRotation = true; }
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
    const spin = detectTSpin(board, piece, lastWasRotation, usedKick);
    const b = board.map(r => [...r]) as (PieceType | null)[][];
    const myIndex = locks.length;
    for (const { col, row } of cells) if (row >= 0 && row < H) { b[row]![col] = piece.type; prov[row]![col] = myIndex; }

    // find + clear full rows
    let cleared = 0, garbageRows = 0;
    for (let row = H - 1; row >= 0; row--) {
      if (b[row]!.every(c => c !== null)) {
        if (b[row]!.some(c => c === GARBAGE)) garbageRows++;
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
      if (isDifficult) {
        b2b++; topbtb = Math.max(topbtb, b2b);
        // observed: b2b1 -> +1, b2b2 -> +1, b2b3 -> +2 (B2B chaining escalation)
        if (b2b > 0) atk += b2b >= 3 ? 2 : 1;
      } else b2b = -1;
      // observed: combo is a MULTIPLIER, not additive. (4+1)*1.25 = 6.25 -> 6
      if (combo > 0) atk = Math.floor(atk * (1 + 0.25 * combo));
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
        for (let pi = 0; pi < pending.length && remaining > 0; ) {
          const p0 = pending[pi]!;
          // with passthrough disabled, only garbage still IN TRANSIT can be cancelled
          if (opts.cancelMode === 'inTransit' && p0.ready <= frame) { pi++; continue; }
          const take = Math.min(remaining, p0.amt);
          p0.amt -= take; remaining -= take;
          if (p0.amt === 0) pending.splice(pi, 1); else pi++;
        }
        sentTotal += remaining;
        records.push({ frame, piece: piece.type, lines: cleared, spin, attack: amount, sent: remaining,
          cancelled: amount - remaining, b2b, combo, cells, garbageCleared: garbageRows });
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
    while (gi < gq.length && gq[gi]!.frame <= f) {
      const g = gq[gi++]!;
      pending.push({ ready: g.frame + opts.garbagespeed, amt: g.amt, x: g.x, size: g.size });
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
    const continuous = () => {
    if (dir !== 0) {
      if (dasTimer > 0) { dasTimer--; if (dasTimer === 0) { arrTimer = 0; } }
      else { if (--arrTimer <= 0) { shift(dir); arrTimer = handling.arr || 1; if (!handling.arr) for (let i = 0; i < BOARD_WIDTH; i++) shift(dir); } }
    }
    const sdRate = opts.sdfMode === 'mult' ? opts.gravity * handling.sdf : handling.sdf;
    gravAcc += opts.gravity + (softHeld ? sdRate : 0);
    while (gravAcc >= 1) { const n = tryMove(board, piece, 0, 1); if (!n) break; piece = n; lastWasRotation = false; gravAcc -= 1; }
    if (gravAcc >= 1) gravAcc = 0;

    if (grounded()) { if (++groundFrames >= opts.locktime) lockPiece(f); }
    else groundFrames = 0;
    };
    const applyEvents = () => {
    while (ei < evs.length && evs[ei]!.frame === f && !topout) {
      const e = evs[ei++]!;
      if (e.type === 'keydown') {
        if (e.key) held.add(e.key);
        if (f < areUntil) continue;          // entry delay: no piece to control yet
        switch (e.key) {
          case 'moveLeft': dir = -1; shift(-1); dasTimer = handling.das; break;
          case 'moveRight': dir = 1; shift(1); dasTimer = handling.das; break;
          case 'softDrop': softHeld = true; break;
          case 'rotateCW': case 'rotateCCW': {
            const before = { c: piece.col, r: piece.row };
            const n = tryRotate(board, piece, e.key === 'rotateCW' ? 1 : -1);
            if (n) { usedKick = n.col !== before.c || n.row !== before.r; piece = n; lastWasRotation = true; groundFrames = 0; }
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
        if (e.key === 'moveLeft' && dir === -1) dir = 0;
        if (e.key === 'moveRight' && dir === 1) dir = 0;
        if (e.key === 'softDrop') softHeld = false;
      }
    }
    };
    if (opts.eventsFirst) { applyEvents(); continuous(); } else { continuous(); applyEvents(); }
  }
  return { lines, placed, holds, clears, topbtb, topcombo,
    garbage: { sent: sentTotal, received: recvTotal, cleared: clearedTotal, attack: attackTotal },
    boards, records, events: evLog, locks, garbageEvents, provSnaps, topout };
}

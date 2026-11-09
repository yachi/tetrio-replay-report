/**
 * A perfect-clear solver over a KNOWN piece sequence, for "which placement made the PC impossible".
 *
 * Board: rows y-UP as 10-bit masks (bit x = column x). A PC frame of height H means no piece may
 * put a cell at y >= H; a full row inside the frame clears and the frame shrinks by one. The board
 * is solved when it is empty. Pieces come from (cur, hold, seq[ptr..]) under TETR.IO's hold rule:
 * place cur, or swap cur with hold (an empty hold takes cur and brings the next piece forward).
 *
 * Movegen is a BFS over the vendored SRS tables with TETR.IO's SRS+ I kicks: shift, one-row fall,
 * CW, CCW. It has NO 180 rotation, so it is a SUBSET of what the engine can reach: a solution it
 * finds is playable, while "no solution" is re-checked by the caller with the engine's own BFS
 * (`route-demos.ts` `reach`, which has 180) before it is published.
 */
import type { Board, ActivePiece } from './vendor/core/srs.ts';
import { tryMove, tryRotate, getPieceCells, setKickset } from './vendor/core/srs.ts';
import type { PieceType } from './vendor/core/types.ts';

setKickset('SRS+');

export const W = 10;
const FULL = (1 << W) - 1;
const BROWS = 40;

export interface Placement { piece: string; cells: number[]; held: boolean }

/** Every resting placement of `piece` on `rows` whose cells all lie below `H` (cells as y*10+x). */
const genCache = new Map<string, number[][]>();
type Gen = (rows: number[], piece: string, H: number) => number[][];
let override: Gen | null = null;
/** Swap the movegen (the caller's engine BFS for re-checking a "no solution"); null restores SRS. */
export function setMovegen(g: Gen | null) { override = g; genCache.clear(); }
export function placements(rows: number[], piece: string, H: number): number[][] {
  const ck = `${piece}|${H}|${rows.join(',')}`;
  if (override) {
    const h = genCache.get(ck); if (h) return h;
    const r = override(rows, piece, H); if (genCache.size > 200000) genCache.clear(); genCache.set(ck, r); return r;
  }
  const hit = genCache.get(ck);
  if (hit) return hit;
  const board: (PieceType | null)[][] = Array.from({ length: BROWS }, () => new Array(W).fill(null));
  rows.forEach((m, y) => { for (let x = 0; x < W; x++) if (m >> x & 1) board[BROWS - 1 - y]![x] = 'G' as any; });
  const start: ActivePiece = { type: piece as PieceType, rotation: 0, col: 3, row: BROWS - 1 - (H + 4) - 3 };
  const seen = new Set<string>();
  const out = new Map<string, number[]>();
  const q: ActivePiece[] = [start];
  const k = (p: ActivePiece) => `${p.rotation},${p.col},${p.row}`;
  seen.add(k(start));
  for (let i = 0; i < q.length; i++) {
    const p = q[i]!;
    if (!tryMove(board as Board, p, 0, 1)) {
      const cells = getPieceCells(p).map(c => (BROWS - 1 - c.row) * W + c.col).sort((a, b) => a - b);
      if (cells.every(c => Math.floor(c / W) < H)) out.set(cells.join(','), cells);
    }
    for (const n of [tryMove(board as Board, p, -1, 0), tryMove(board as Board, p, 1, 0), tryMove(board as Board, p, 0, 1),
                     tryRotate(board as Board, p, 1), tryRotate(board as Board, p, -1)]) {
      if (!n) continue;
      if (BROWS - 1 - n.row > H + 8) continue;            // keep the search near the frame
      const nk = k(n);
      if (seen.has(nk)) continue;
      seen.add(nk); q.push(n);
    }
  }
  const res = [...out.values()];
  if (genCache.size > 200000) genCache.clear();
  genCache.set(ck, res);
  return res;
}

/** Place cells, clear full rows below H; returns new rows and how many cleared. */
export function apply(rows: number[], cells: number[], H: number): { rows: number[]; H: number; cleared: number } {
  const r = rows.slice();
  while (r.length < H) r.push(0);
  for (const c of cells) r[Math.floor(c / W)]! |= 1 << (c % W);
  const kept = r.filter(m => m !== FULL);
  const cleared = r.length - kept.length;
  while (kept.length && kept[kept.length - 1] === 0) kept.pop();
  return { rows: kept, H: H - cleared, cleared };
}

/** Every empty region inside the frame must hold a multiple of four cells. */
function regionsOk(rows: number[], H: number): boolean {
  const empty = new Uint8Array(H * W);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) empty[y * W + x] = ((rows[y] ?? 0) >> x & 1) ? 0 : 1;
  const st: number[] = [];
  for (let s = 0; s < H * W; s++) {
    if (!empty[s]) continue;
    let n = 0; empty[s] = 0; st.push(s);
    while (st.length) {
      const c = st.pop()!; n++;
      const x = c % W, y = (c / W) | 0;
      if (x > 0 && empty[c - 1]) { empty[c - 1] = 0; st.push(c - 1); }
      if (x < W - 1 && empty[c + 1]) { empty[c + 1] = 0; st.push(c + 1); }
      if (y > 0 && empty[c - W]) { empty[c - W] = 0; st.push(c - W); }
      if (y < H - 1 && empty[c + W]) { empty[c + W] = 0; st.push(c + W); }
    }
    if (n % 4) return false;
  }
  return true;
}

export const filled = (rows: number[]) => rows.reduce((a, m) => { let n = 0; for (let x = 0; x < W; x++) n += m >> x & 1; return a + n; }, 0);
export const height = (rows: number[]) => { let h = rows.length; while (h && !rows[h - 1]) h--; return h; };

export type Verdict = { ok: true; H: number; plan: Placement[] } | { ok: false } | { ok: null; why: string };

/**
 * Can `rows` be perfect-cleared inside a frame of height H, with the given queue? Memoised per call
 * of `solveAny` by (board, H, cur, hold, ptr). `ok: null` means the sequence ran out first.
 */
export function solve(rows0: number[], H0: number, cur0: string, hold0: string, seq: string, ptr0: number,
                      memo: Map<string, Placement[] | false>, budget: { nodes: number }): Verdict {
  let short = false;
  // memo: key → the remaining plan (placements to the PC) or false
  const rec = (rows: number[], H: number, cur: string, hold: string, ptr: number): Placement[] | false => {
    if (H === 0 && rows.length === 0) return [];
    if (!regionsOk(rows, H)) return false;
    const need = (H * W - filled(rows)) / 4;
    if (seq.length - ptr + 1 + (hold ? 1 : 0) < need) { short = true; return false; }
    const key = `${rows.join(',')}|${H}|${cur}|${hold}|${ptr}`;
    const m = memo.get(key);
    if (m !== undefined) return m;
    if (--budget.nodes < 0) throw new Error('budget');
    const options: [string, string, string, number, boolean][] = [];   // [placed, newHold, nextCur, nextPtr, held]
    options.push([cur, hold, seq[ptr] ?? '', ptr + 1, false]);
    if (hold === '') { if (seq[ptr]) options.push([seq[ptr]!, cur, seq[ptr + 1] ?? '', ptr + 2, true]); }
    else if (hold !== cur) options.push([hold, cur, seq[ptr] ?? '', ptr + 1, true]);
    for (const [pc, nh, nc, np, held] of options) {
      if (!pc) { short = true; continue; }
      for (const cells of placements(rows, pc, H)) {
        const a = apply(rows, cells, H);
        const me: Placement = { piece: pc, cells, held };
        if (a.H === 0 && a.rows.length === 0) { const r = [me]; memo.set(key, r); return r; }
        if (!nc) { short = true; continue; }
        const sub = rec(a.rows, a.H, nc, nh, np);
        if (sub) { const r = [me, ...sub]; memo.set(key, r); return r; }
      }
    }
    memo.set(key, false);
    return false;
  };
  const r = rec(rows0, H0, cur0, hold0, ptr0);
  if (r) return { ok: true, H: H0, plan: r };
  return short ? { ok: null, why: 'sequence too short' } : { ok: false };
}

/** Frames worth trying for a board: H from its height up to `maxH`, with (10H − filled) a multiple of 4. */
export function frames(rows: number[], maxH = 4): number[] {
  const h = height(rows), n = filled(rows), out: number[] = [];
  for (let H = Math.max(h, 1); H <= maxH; H++) if ((H * W - n) % 4 === 0 && H * W - n > 0) out.push(H);
  return out;
}

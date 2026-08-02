/**
 * T-Spin Forecast metric.
 *
 * Wiki definition (harddrop.com/wiki/T-Spin_Forecast): "a playing style that predicts and sets up
 * T-spins in advance. A player stacks so that T-Spins would emerge from line clears or upcoming
 * garbage."
 *
 * Operational form — intent is unobservable, so we measure its signature:
 *   For each executed T-spin at lock k, find the lock j that built the slot's ROOF (the overhang
 *   the T tucks under), via the provenance grid. Then classify by what happened in (j, k]:
 *     forecast_garbage   — the roof is garbage, or garbage rose between j and k
 *                          (the slot did not exist as usable when the overhang was placed)
 *     forecast_lineclear — a line clear occurred between j and k, dropping the stack into the slot
 *     reactive           — neither; the slot was already there and usable
 *   `separation` = k - j in pieces. A larger separation is stronger evidence of intent;
 *   separation == 1 means the overhang was placed by the immediately preceding piece.
 *
 * Reported as a RATE, never a binary claim: some fraction of any forecast bucket is luck.
 */
import { H, detectTSpin } from './sim.ts';
import type { SimResult } from './sim.ts';
import type { Board, ActivePiece } from './vendor/core/srs.ts';
import { tryMove, tryRotate, hardDrop, getPieceCells } from './vendor/core/srs.ts';

/**
 * Was any line-clearing T-spin ALREADY available on this board?
 * Mirrors splice-demo.ts, which verified the BEFORE board offers none and the AFTER board
 * (identical overhang + cavity, one full row removed between them) offers a clean TSD.
 */
export function bestTspinLines(board: Board): number {
  let best = 0;
  const spawn: ActivePiece = { type: 'T', rotation: 0, col: 3, row: 18 };
  const seen = new Set(['0:3:18']);
  const q: { p: ActivePiece; rot: boolean; kick: boolean }[] = [{ p: spawn, rot: false, kick: false }];
  for (let h = 0; h < q.length && h < 40000; h++) {
    const { p: cur, rot, kick } = q[h]!;
    const d = hardDrop(board, cur);
    if (d.row === cur.row && rot && detectTSpin(board, d, true, kick) !== 'none') {
      const after = board.map(r => [...r]) as (string | null)[][];
      for (const c of getPieceCells(d)) if (c.row >= 0 && c.row < H) after[c.row]![c.col] = 'T';
      const lines = after.filter(r => r.every(x => x !== null)).length;
      if (lines > best) best = lines;
    }
    const nexts: [ActivePiece | null, boolean][] = [
      [tryMove(board, cur, -1, 0), false], [tryMove(board, cur, 1, 0), false],
      [tryMove(board, cur, 0, 1), false], [tryRotate(board, cur, 1), true], [tryRotate(board, cur, -1), true]];
    for (const [n, isRot] of nexts) {
      if (!n) continue;
      const k = `${n.rotation}:${n.col}:${n.row}`; if (seen.has(k)) continue; seen.add(k);
      q.push({ p: n, rot: isRot, kick: isRot && (n.col !== cur.col || n.row !== cur.row) });
    }
  }
  return best;
}

/**
 * Was a line-clearing T-spin available at all? Exactly `bestTspinLines(board) > 0`.
 *
 * This was a second, independently written BFS until 2026-07-30. The two agreed on every one of
 * 932 random boards, and the duplication was not merely redundant — the copies carried different
 * BFS caps (20000 vs 40000), a divergence waiting to happen. Merging them removed the divergence;
 * what it does NOT rest on is the caps being provably dead. `q` only grows when a fresh
 * `rotation:col:row` key enters `seen`, so the key space bounds it — but only two of those three
 * coordinates are bounded by the engine. Columns are: `isValidPosition` rejects any cell outside
 * 0..9, and the T's anchor is offset from its cells asymmetrically per rotation, so the anchor
 * runs -1..7 in R (its leftmost cell sits at offset 1), 0..8 in L (its rightmost cell does), and
 * 0..7 in 0/2 — a union of -1..8, still 10 values but not the 0..9 previously assumed, and the
 * 4x10 product is loose because no single rotation admits all ten. Rows are NOT bounded:
 * `vendor/core/srs.ts:129` is `if (row < 0) continue`, so every negative row is a legal position
 * and nothing in the collision test stops a piece climbing. CONDITIONAL on rows staying in
 * [-2, 39] the bound is 4*10*42 = 1680; that side condition needs kick-table reasoning (a piece
 * rises only on a kick, a kick only fires when the [0,0] candidate is blocked, and the JLSZT table
 * lifts at most 2), which is a sketch nobody has turned into a proof. So 1680 is an assumption,
 * the measured max of 688 (bfs-cap.ts, 2000 boards) is the evidence, and `h < 40000` is a LIVE
 * belt rather than dead code.
 */
export function tspinAvailable(board: Board): boolean {
  return bestTspinLines(board) > 0;
}

export type ForecastKind = 'forecast_garbage' | 'forecast_lineclear' | 'reactive';
export interface ForecastRecord {
  lockIndex: number; frame: number; lines: number; spin: 'mini' | 'full';
  kind: ForecastKind; separation: number; roofFrom: number | null; roofIsGarbage: boolean;
  slotOpenedLater?: boolean; determinable?: boolean;
}

/**
 * Strict test — the defining property, verified in splice-demo.ts:
 * was the cell directly BENEATH the roof already empty when the roof was placed?
 *   empty  -> the slot was already open; the overhang was laid onto an existing cavity (reactive)
 *   filled -> the roof sat on solid ground and the cavity opened later, either because a clear
 *             spliced the rows together or because garbage lifted a hole under it (forecast)
 * This replaces "any line clear happened in the window", which counted clears far below the slot
 * that splice nothing.
 */
export function forecastMetric(r: SimResult, strict = true): {
  records: ForecastRecord[];
  totals: Record<ForecastKind, number>;
  tspins: number;
  forecastRate: number;
} {
  const records: ForecastRecord[] = [];
  const totals: Record<ForecastKind, number> = { forecast_garbage: 0, forecast_lineclear: 0, reactive: 0 };

  for (let k = 0; k < r.locks.length; k++) {
    const lk = r.locks[k]!;
    if (lk.spin === 'none' || lk.cleared === 0) continue;

    // The board state the T landed into is the snapshot BEFORE this lock (k-1).
    const prev = k > 0 ? r.provSnaps[k - 1] : null;
    if (!prev) continue;

    // Roof = filled cells directly above the T's own cells.
    const roofProv: (number | null)[] = [];
    for (const c of lk.cells) {
      const above = c.row - 1;
      if (above < 0 || above >= H) continue;
      const p = prev[above]?.[c.col];
      if (p !== null && p !== undefined) roofProv.push(p);
    }
    if (roofProv.length === 0) continue;   // no overhang → not a tucked spin

    const roofIsGarbage = roofProv.some(p => p === -1);
    const placers = roofProv.filter((p): p is number => p !== null && p >= 0);
    // the roof's most recent builder is the piece that "set up" the slot
    const j = placers.length ? Math.max(...placers) : -1;

    // what happened between the roof being built and the T-spin being executed?
    const garbageBetween = r.garbageEvents.some(g => g.lockIndex > j && g.lockIndex <= k);
    let clearBetween = false;
    for (let i = Math.max(j, 0) + 1; i < k; i++) if (r.locks[i]!.cleared > 0) { clearBetween = true; break; }

    // strict gate: was a line-clearing T-spin already available when the roof was placed?
    // (the first attempt tested "is the cell under the roof empty" — that is true by definition
    //  of an overhang, so it returned reactive for all 167 cases and was discarded)
    let slotOpenedLater = true, determinable = false;
    const boardJ = j >= 0 ? r.boards[j] : null;
    if (boardJ) { determinable = true; slotOpenedLater = !tspinAvailable(boardJ); }

    const opened = strict && determinable ? slotOpenedLater : (clearBetween || garbageBetween);

    const kind: ForecastKind =
      !opened ? 'reactive'
      : garbageBetween ? 'forecast_garbage'
      : clearBetween ? 'forecast_lineclear'
      : 'reactive';

    totals[kind]++;
    records.push({ lockIndex: k, frame: lk.frame, lines: lk.cleared, spin: lk.spin,
      kind, separation: j >= 0 ? k - j : -1, roofFrom: j >= 0 ? j : null, roofIsGarbage,
      slotOpenedLater, determinable });
  }
  const tspins = records.length;
  const fc = totals.forecast_garbage + totals.forecast_lineclear;
  return { records, totals, tspins, forecastRate: tspins ? fc / tspins : 0 };
}

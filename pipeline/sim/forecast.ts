/**
 * T-Spin Forecast metric.
 *
 * Wiki definition (harddrop.com/wiki/T-Spin_Forecast): "a playing style that predicts and sets up
 * T-spins in advance. A player stacks so that T-Spins would emerge from line clears or upcoming
 * garbage."
 *
 * The MECHANISM clause is load-bearing and was missing until 2026-08-02. A slot that appears
 * because the player finished building it is not a forecast, however long before the spin the
 * overhang was placed. The C-Spin (TKI積み) opener is exactly that case — "L and J are used to
 * build the overhang" in the first bag — and it was being counted as forecasting.
 *
 * Operational form — intent is unobservable, so we measure its signature:
 *   For each executed T-spin at lock k, find the lock j that built the slot's ROOF (the overhang
 *   the T tucks under), via the provenance grid. Then:
 *     1. did the best available T-spin IMPROVE between j and k? (not merely "was one absent at j",
 *        which discards the wiki's own 1 -> 2 upgrade examples)
 *     2. if so, is the mechanism established?
 *          forecast_garbage   — removing every garbage row strictly reduces what is available at
 *                               k, so the garbage is LOAD-BEARING. Counterfactually verified, and
 *                               validated against the wiki's five garbage pairs, where stripping
 *                               the appended line reproduces the article's own "before" value.
 *          forecast_lineclear — a clear occurred in (j, k] and the garbage is not load-bearing.
 *                               CO-OCCURRENCE ONLY: un-clearing a row needs a re-simulation, not a
 *                               board edit, so this bucket is reported separately and is NOT in
 *                               `forecastRate`. It carries the confound the garbage branch shed.
 *          self_built         — improved, but neither mechanism explains it. Openers land here.
 *     3. otherwise `reactive` — the spin on offer did not get better.
 *   `separation` = k - j in pieces. Note it is NOT evidence of intent on its own: the corpus's
 *   longest separations are openers.
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

/**
 * `forecast_garbage`   improved, and the garbage is LOAD-BEARING — removing it strictly reduces the
 *                      available spin. Causally verified.
 * `forecast_lineclear` improved, a line cleared in the window, and garbage is not load-bearing.
 *                      **Causality is NOT established** — see `forecastMetric`.
 * `self_built`         improved, but the player built the slot themselves. Openers land here.
 * `reactive`           the available spin did not improve between roof and execution.
 */
export type ForecastKind = 'forecast_garbage' | 'forecast_lineclear' | 'self_built' | 'reactive';
export interface ForecastRecord {
  lockIndex: number; frame: number; lines: number; spin: 'mini' | 'full';
  kind: ForecastKind; separation: number; roofFrom: number | null; roofIsGarbage: boolean;
  slotOpenedLater?: boolean; determinable?: boolean;
  /** best T-spin available when the roof was placed, and just before it was executed */
  availAtRoof?: number; availAtSpin?: number;
  /** removing every garbage row strictly reduces what is available at execution */
  garbageLoadBearing?: boolean;
}

/**
 * Forecasts whose mechanism is ESTABLISHED. This is the honest numerator.
 *
 * Callers previously wrote `kind !== 'reactive'` inline in six places. That is why adding a fourth
 * kind is dangerous and why it is now a function: a new kind silently joined the forecast bucket
 * under the old idiom, which is exactly how openers got counted in the first place.
 */
export const isVerifiedForecast = (r: ForecastRecord) => r.kind === 'forecast_garbage';

/** Adds the line-clear bucket, whose causality this simulator cannot test. Report it separately. */
export const isForecastOrUnverified = (r: ForecastRecord) =>
  r.kind === 'forecast_garbage' || r.kind === 'forecast_lineclear';

/** Every row containing a garbage cell removed, stack shifted down — the counterfactual board. */
export function withoutGarbage(board: Board): Board {
  const kept = board.filter(row => !row.some(c => (c as unknown as string) === 'G'));
  const pad = Array.from({ length: board.length - kept.length }, () => Array(10).fill(null));
  return [...pad, ...kept] as Board;
}

/**
 * `strict` (the default) applies the causal rule described above. `strict = false` restores the
 * original co-occurrence behaviour verbatim — any garbage or clear in the window counts — so
 * LOOSE=1 still reproduces the pre-correction figures for comparison.
 */
export function forecastMetric(r: SimResult, strict = true): {
  records: ForecastRecord[];
  totals: Record<ForecastKind, number>;
  tspins: number;
  /** verified only: garbage counterfactually shown to be load-bearing */
  forecastRate: number;
  /** verified + the untestable line-clear bucket. Never print this as "the" rate. */
  unverifiedRate: number;
} {
  const records: ForecastRecord[] = [];
  const totals: Record<ForecastKind, number> = { forecast_garbage: 0, forecast_lineclear: 0, self_built: 0, reactive: 0 };

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

    // Did the available spin IMPROVE between the roof going down and the T going in?
    //
    // This replaces a binary `!tspinAvailable(boardJ)`. That test forced any board already
    // offering ANY spin to `reactive`, which discards the wiki's own Doubles>Garbage examples:
    // two of its five garbage pairs go best 1 -> 2, an already-available single that garbage
    // UPGRADES to a double, presented by the article as forecasting a Double. 34 of this
    // corpus's reactive events have that shape.
    const boardJ = j >= 0 ? r.boards[j] : null;
    const boardK = k > 0 ? r.boards[k - 1] : null;
    const determinable = !!(boardJ && boardK);
    const availAtRoof = boardJ ? bestTspinLines(boardJ) : 0;
    const availAtSpin = boardK ? bestTspinLines(boardK) : 0;
    // `strict` selects the causal rule; loose keeps the original co-occurrence behaviour so
    // LOOSE=1 still reproduces the pre-correction numbers for comparison (auc.ts, run-forecast.ts).
    const improved = (strict && determinable)
      ? availAtSpin > availAtRoof
      : (clearBetween || garbageBetween);

    // Is the garbage LOAD-BEARING? Strip every garbage row and re-ask. If the spin is unchanged,
    // the garbage cannot have created it, however much of it arrived in the window.
    //
    // `garbageBetween` alone is CO-OCCURRENCE, not causation, and at a median separation of ~11
    // pieces some garbage arriving is near-certain — so every memorised opener (the C-Spin builds
    // its overhang from L and J in the first bag) was being labelled forecast_garbage by default.
    // This counterfactual is validated against the wiki's own boards: stripping the appended
    // garbage line reproduces the article's "before" value in all five of its garbage pairs.
    const garbageLoadBearing = !!(boardK && garbageBetween
      && bestTspinLines(withoutGarbage(boardK)) < availAtSpin);

    // Loose mode: the original rule verbatim, co-occurrence and all.
    const kind: ForecastKind = !(strict && determinable)
      ? (!improved ? 'reactive' : garbageBetween ? 'forecast_garbage'
         : clearBetween ? 'forecast_lineclear' : 'reactive')
      : !improved ? 'reactive'
      : garbageLoadBearing ? 'forecast_garbage'
      // No equivalent counterfactual exists for a line clear — un-clearing a row cannot be done
      // by editing the board, only by re-simulating a round whose inputs were conditioned on the
      // clear happening. So this bucket asserts CO-OCCURRENCE ONLY and is reported separately;
      // it carries the same opener confound the garbage branch just had removed.
      : clearBetween ? 'forecast_lineclear'
      // Improved, but neither mechanism accounts for it: the player built the slot. Openers.
      : 'self_built';

    totals[kind]++;
    records.push({ lockIndex: k, frame: lk.frame, lines: lk.cleared, spin: lk.spin,
      kind, separation: j >= 0 ? k - j : -1, roofFrom: j >= 0 ? j : null, roofIsGarbage,
      slotOpenedLater: improved, determinable, availAtRoof, availAtSpin, garbageLoadBearing });
  }
  const tspins = records.length;
  // `forecastRate` is the VERIFIED rate — garbage whose removal changes the answer. The
  // line-clear bucket is deliberately excluded from the headline because its mechanism is
  // asserted rather than tested; it is returned separately so a caller must opt in to it.
  const verified = totals.forecast_garbage;
  const unverified = totals.forecast_lineclear;
  return { records, totals, tspins,
           forecastRate: tspins ? verified / tspins : 0,
           unverifiedRate: tspins ? (verified + unverified) / tspins : 0 };
}

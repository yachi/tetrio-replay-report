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
 *     2. if so, WHICH STEP raised it, and which edit within that step? See `localiseMechanism`.
 *        The window is not treated as one opaque interval — it is walked, and the single step
 *        that produced the executed spin is decomposed into place -> clear -> insert garbage.
 *          forecast_garbage   — the availability crossed on the garbage insertion.
 *          forecast_lineclear — it crossed on the row removal, and a cleared row lay strictly
 *                               inside the slot, so the clear FORMED it rather than moving it.
 *          self_built         — it crossed on the player's own placement. Openers land here.
 *     3. otherwise `reactive` — the spin on offer did not get better.
 *     4. and, independently of all that, WAS THERE A HOLE to close onto when the roof went up?
 *        See `floorOrigin`. Steps 1-3 say which edit brought roof and cavity together and say
 *        nothing about whether the cavity was there first, so until 2026-08-03 a roof dropped on
 *        solid stack that opened up underneath scored exactly like a roof laid over a hole on
 *        purpose. The player's own statement of the metric makes the hole a premise: "putting an
 *        overhang over a few lines far of A HOLE". Adding it took the corpus from 1 of 654 to
 *        0 of 654 — on the single event that reached this clause, one of the cells holding the T
 *        up is garbage that had not arrived when the overhang was placed. Note "one of the cells
 *        holding it up", not "the cell under the nose": whether anything sits under the T's lowest
 *        cell is irrelevant, and reading that cell was the defect this clause was rewritten to fix.
 *
 * Both forecast kinds now rest on the same evidence. Until 2026-08-02 the garbage branch was
 * counterfactually tested while the line-clear branch merely asserted co-occurrence, because
 * un-clearing a row looked impossible — the rows are gone and the player's later inputs were
 * conditioned on the clear. Localising the step dissolves that: at the step itself the pre-clear
 * board is just the previous board plus four cells, so no re-simulation is needed. Auditing the
 * 86 events that assertion had produced found 85 were the player's own placement and 1 was real.
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
export function bestTspin(board: Board): { lines: number; rows: number[] } | null {
  let best = 0, bestRows: number[] = [];
  const spawn: ActivePiece = { type: 'T', rotation: 0, col: 3, row: 18 };
  const seen = new Set(['0:3:18']);
  const q: { p: ActivePiece; rot: boolean; kick: boolean }[] = [{ p: spawn, rot: false, kick: false }];
  for (let h = 0; h < q.length && h < 40000; h++) {
    const { p: cur, rot, kick } = q[h]!;
    const d = hardDrop(board, cur);
    if (d.row === cur.row && rot && detectTSpin(board, d, true, kick) !== 'none') {
      const after = board.map(r => [...r]) as (string | null)[][];
      const cells = getPieceCells(d);
      for (const c of cells) if (c.row >= 0 && c.row < H) after[c.row]![c.col] = 'T';
      const lines = after.filter(r => r.every(x => x !== null)).length;
      if (lines > best) {
        best = lines;
        // The slot is the T's own cells plus the roof directly above them — the rows a line
        // clear would have to fall between in order to have FORMED it rather than moved it.
        const rows = cells.map(c => c.row);
        bestRows = [...rows, Math.min(...rows) - 1];
      }
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
  return best > 0 ? { lines: best, rows: bestRows } : null;
}

/** How many lines the best available T-spin clears; 0 if none is reachable. */
export function bestTspinLines(board: Board): number {
  return bestTspin(board)?.lines ?? 0;
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
 * `forecast_lineclear` improved, and the clear FORMED the slot: a cleared row lay strictly inside
 *                      it, so removing that row is what brought roof and cavity together.
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
  /** removing the garbage that arrived AFTER the roof strictly reduces what is available */
  garbageLoadBearing?: boolean;
  /** which of the causing step's three edits raised the availability, and which step that was */
  mechanism?: Mechanism; mechanismStep?: number;
  /**
   * clause 4: was the clear that closed the gap ITSELF a T-spin?
   *
   * `spec/Forecast.dfy` states the definition as "...cleared by NOT tspin" and proves that a window
   * closed only by spin clears is not a forecast (`CSpinIsNotAForecast`). This file did not test it
   * until 2026-08-06: `localiseMechanism` reads the step's rows and never looked at its `spin`, so a
   * C-Spin's own Triple lowering its own overhang would have been counted. It changes nothing on this
   * corpus — the single line-clear event's closing piece is a vertical I — which is exactly why it
   * needed a probe rather than an eyeball.
   */
  closingClearWasSpin?: boolean;
  /** clause 2: where the cells holding the T up came from */
  floorOrigin?: FloorOrigin; floorFrom?: number | null;
}

/**
 * Where the cells holding the T up came from — clause 2, "the hole was already open when the
 * overhang landed".
 *
 * The kinds above answer WHAT closed the gap. They do not ask whether there was a hole to close
 * onto, and without that a roof laid on solid stack which later opens up underneath scores exactly
 * like a roof laid deliberately over a cavity. The player's own statement of the metric is "putting
 * an overhang over a few lines far of A HOLE"; the hole is a premise, not a consequence.
 *
 * No cell tracking is needed to decide it. `provSnaps[t]` records, for every filled cell, the index
 * of the lock that placed it, so each support's origin is read directly at k-1 and compared with j:
 *
 *   'pre-existed'   every cell holding the piece up was there at j — the roof went up over
 *                   something already present
 *   'arrived-later' at least one of them was placed after j, so at j there was nothing there to
 *                   rest on. One such support is enough: the hole as executed did not pre-exist.
 *   'undetermined'  a support is a garbage cell, garbage both predates and postdates j, and which
 *                   row is which cannot be settled without tracking. Never counted either way.
 *
 * A garbage support is NOT automatically undetermined: if the board held no garbage at all when the
 * roof landed, garbage cannot predate it, and that is decidable from the two snapshots. That single
 * test is what settles the one event this corpus used to publish.
 *
 * EVERY support is judged, not the deepest row alone. A T that tucks under an overhang usually rests
 * on its two shoulders while its nose hangs into a well, so reading the cell under the nose reads an
 * empty cell and learns nothing. Measured over the four committed sessions: the deepest-row cells
 * were a PROPER SUBSET of the genuine supports in all 654 events — 294 missed one support, 204 two,
 * 156 three — and the missed cells carried strictly newer provenance in 258 of the 398 events where
 * both sets were non-empty. There was also a `'field-floor'` verdict, returned both when the nose
 * reached row 39 and when nothing at all sat beneath it; it is gone, because the case it named —
 * a piece held up by the playfield bottom ALONE — occurs 0 times in 654 events across all seven
 * simulator configs. The floor still predates all play, so it simply never raises the maximum.
 */
export type FloorOrigin = 'pre-existed' | 'arrived-later' | 'undetermined';

export function floorOrigin(r: SimResult, k: number, j: number | null): FloorOrigin {
  const lk = r.locks[k]!;
  const prev = r.provSnaps[k - 1];
  if (!prev) return 'undetermined';

  const provs: number[] = [];
  let onFloor = false;
  for (const c of lk.cells) {
    const below = c.row + 1;
    if (below >= H) { onFloor = true; continue; }   // the playfield bottom predates everything
    // No guard is needed for a cell of the T sitting below another: `prev` is the snapshot BEFORE
    // this lock, so every cell the piece is about to occupy is still empty and the null test below
    // already skips it. One was written here and the mutation harness could not kill it — measured,
    // it fires 953 times across the corpus and finds a non-null cell in 0 of them.
    const p = prev[below]?.[c.col];
    if (p === null || p === undefined) continue;    // empty: this cell of the piece rests on nothing
    provs.push(p);
  }
  // held up by the playfield floor and nothing else — measured 0 times, kept so it cannot go wrong
  if (provs.length === 0) return onFloor ? 'pre-existed' : 'undetermined';
  if (j === null) return 'undetermined';

  const garbageRows = (t: number) =>
    r.boards[t]!.filter(row => row.some(c => (c as unknown as string) === 'G')).length;
  let after = false, unknown = false;
  for (const p of provs) {
    if (p >= 0) { if (p > j) after = true; continue; }
    // a garbage support: decidable at the ends, undecidable when garbage straddles the window
    if (garbageRows(j) === 0) after = true;
    else if (r.garbageEvents.some(g => g.lockIndex > j && g.lockIndex <= k)) unknown = true;
  }
  // a support that demonstrably postdates the roof settles it, whatever the others do
  return after ? 'arrived-later' : unknown ? 'undetermined' : 'pre-existed';
}

/** Clause 2 as a verdict: true, false, or `null` for the cases nothing can decide. */
export const holePreExisted = (o: FloorOrigin): boolean | null =>
  o === 'undetermined' ? null : o === 'pre-existed';

/**
 * Forecasts whose mechanism is ESTABLISHED and which had a hole to forecast onto. This is the
 * honest numerator.
 *
 * Callers previously wrote `kind !== 'reactive'` inline in six places. That is why adding a fourth
 * kind is dangerous and why it is now a function: a new kind silently joined the forecast bucket
 * under the old idiom, which is exactly how openers got counted in the first place. Clause 2 is
 * added HERE rather than as a fifth kind for the same reason — the kinds answer which edit closed
 * the gap, and every consumer already routes its numerator through this one predicate.
 */
export const isVerifiedForecast = (r: ForecastRecord) =>
  (r.kind === 'forecast_garbage' || r.kind === 'forecast_lineclear')
  && holePreExisted(r.floorOrigin ?? 'undetermined') === true
  // clause 4 — the gap must have been closed by a clear that was not itself a T-spin
  && r.closingClearWasSpin !== true;

/** `board` with those rows deleted and the stack shifted down — the counterfactual board. */
export function withoutRows(board: Board, rows: Set<number>): Board {
  const kept = board.filter((_, i) => !rows.has(i));
  const pad = Array.from({ length: board.length - kept.length }, () => Array(10).fill(null));
  return [...pad, ...kept] as Board;
}

/**
 * The rows of `boards[k-1]` holding garbage that ARRIVED after the roof went up at lock `j`.
 *
 * This is the deletion set for the counterfactual below, and getting it wrong is not a matter of
 * strictness. The claim under test is that garbage *arriving during the window* is what holds the
 * executed spin up. Deleting every garbage row instead — which is what this used to do — deletes
 * the slot's own floor whenever the T tucks into a well that garbage built long before the roof,
 * and a piece with no floor cannot exist in the counterfactual world at all. The spin vanishes, and
 * "the spin vanished" is exactly the signature the test reads as causation. An over-broad deletion
 * set does not fail loudly; it fails toward the positive.
 *
 * On this corpus that mattered on exactly one event, `yachi 07-28-1 r5 lock 36`, which stripping
 * everything called load-bearing: the row the T tucks into arrived at lock 11 under a roof at lock
 * 33, and the only garbage inside the window is one row at the very bottom of the field, twelve
 * rows below the slot. It also explains why the wiki fixtures never caught it — in all five of the
 * article's garbage pairs the appended line IS the slot, so destroying it is the right answer
 * there, and the oracle inverts only on the shape the article does not contain.
 *
 * Arrival is derived, not tracked, by replaying each step's row edits over one boolean per row: a
 * placement moves no rows; a clear splices out the full rows of `Bpre` and pads the top; an insert
 * shifts rows off the top and pushes the new ones in at the bottom, where they are marked. Seeding
 * at `j` with everything false is what makes the answer relative to the roof, and it needs no
 * special case for `j = -1` (a roof with no placer): the walk starts at lock 0 and every garbage
 * row then on the board counts as having arrived after it.
 *
 * Measured against the boards themselves: the marks reproduce the real garbage mask of `boards[t]`
 * at all 110,927 lock-steps of the four sessions across all seven swept configs, and the marked
 * rows come out ordered oldest-on-top everywhere — including `reference_queue`, the one config that
 * can insert garbage before the piece rather than after it.
 */
export function garbageArrivedAfter(r: SimResult, j: number, k: number): Set<number> {
  let post = new Array<boolean>(H).fill(false);
  for (let t = j + 1; t <= k - 1; t++) {
    const lk = r.locks[t]!;
    const Bpre = r.boards[t - 1]!.map(row => [...row]) as Board;
    for (const c of lk.cells) if (c.row >= 0 && c.row < H) Bpre[c.row]![c.col] = lk.piece as never;
    for (let row = H - 1; row >= 0; row--) {
      if (Bpre[row]!.every(x => x !== null)) { Bpre.splice(row, 1); post.splice(row, 1); }
    }
    while (post.length < H) post.unshift(false);
    for (const g of r.garbageEvents) {
      if (g.lockIndex === t) post = post.slice(g.amt).concat(new Array<boolean>(g.amt).fill(true));
    }
  }
  // A row carrying no garbage is not garbage that arrived, whatever the events claim. On the real
  // corpus the mark and the mask agree at every one of those 110,927 steps, so this narrows nothing
  // there; it is what stops a hand-built SimResult whose garbage events do not match its boards
  // from deleting rows that hold the player's own stack.
  const boardK = r.boards[k - 1]!;
  return new Set(post.flatMap((p, i) =>
    p && boardK[i]!.some(c => (c as unknown as string) === 'G') ? [i] : []));
}

/**
 * Which mechanism raised the available spin — read off the game, not inferred from a window.
 *
 * The counterfactual above answers "is the garbage load-bearing AT EXECUTION", which is a sound
 * question but the wrong moment, and it has no analogue for a line clear at all. Both limits come
 * from treating the whole roof-to-spin window as one opaque interval and asking what co-occurred
 * inside it. They dissolve once the window is walked: `boards[t]` exists after every lock, so the
 * step at which the executed spin became available is observable, and within that one step the
 * simulator does place -> clear -> insert garbage before snapshotting (sim.ts). So the step
 * decomposes into a chain of three edits, each exactly reconstructible:
 *
 *     A    = boards[t-1]                    before the piece
 *     Bpre = A + the locked cells           placed, nothing removed
 *     B    = Bpre minus its full rows       placed and cleared
 *     C    = boards[t]                      and garbage inserted
 *
 * Whichever link the availability crosses IS the mechanism. Nothing is hypothesised: when no
 * garbage arrives, B must equal C cell-for-cell, and `forecastMetric` asserts exactly that.
 *
 * `t` is the step at which the final availability is reached AND HELD to execution, not merely
 * the last step it rose: availability spikes and falls back as the stack changes, and the step
 * that created a slot the player then destroyed is not the step that produced what they executed.
 *
 * The one inconclusive link is Bpre, which still holds the full rows and so blocks the T's path
 * down from spawn. That artifact can only LOWER avail(Bpre), so reaching the target there proves
 * the placement alone sufficed, while failing to reach it proves nothing — and is settled
 * geometrically instead: a clear forms a slot only if a cleared row lies strictly INSIDE it. A
 * cleared row outside the slot's own rows displaces the slot rigidly and cannot have formed it.
 * Where neither the clear nor the piece touches the slot, the answer is `unattributed` rather
 * than a default: an `else` that quietly returns 'placement' is how the opener confound survived
 * the first time.
 */
export type Mechanism = 'garbage' | 'line-clear' | 'placement' | 'unattributed';

export function localiseMechanism(
  r: SimResult, j: number, k: number, target: number, avail: (t: number) => number,
): { step: number; mechanism: Mechanism } {
  let t = k - 1;
  while (t > j && avail(t - 1) >= target) t--;
  // `improved` guarantees avail(j) < target, so the walk always halts above the roof.
  if (t <= j) return { step: t, mechanism: 'unattributed' };

  const A = r.boards[t - 1]!, lk = r.locks[t]!;
  const Bpre = A.map(row => [...row]) as Board;
  for (const c of lk.cells) if (c.row >= 0 && c.row < H) Bpre[c.row]![c.col] = lk.piece as never;
  const clearedRows = Bpre.map((row, i) => row.every(x => x !== null) ? i : -1).filter(i => i >= 0);
  const B = Bpre.map(row => [...row]) as Board;
  for (const row of [...clearedRows].reverse()) B.splice(row, 1);
  for (let i = 0; i < clearedRows.length; i++) B.unshift(Array(10).fill(null) as never);

  // The reconstruction is asserted, never assumed. If these ever fire, the step model is wrong
  // and every mechanism verdict computed from it is fiction — which is exactly the failure that
  // would otherwise present as a plausible reclassification rather than as an error.
  const C = r.boards[t]!;
  const gcells = (b: Board) => b.reduce((n, row) => n + row.filter(c => (c as unknown as string) === 'G').length, 0);
  const garbageArrived = gcells(C) > gcells(B);
  if (clearedRows.length !== lk.cleared)
    throw new Error(`step ${t}: lock cleared ${lk.cleared} rows but the reconstruction found ${clearedRows.length}`);
  if (!garbageArrived && !B.every((row, i) => row.every((c, x) => c === C[i]![x])))
    throw new Error(`step ${t}: reconstruction diverges from boards[${t}] with no garbage inserted`);

  if (bestTspinLines(Bpre) >= target) return { step: t, mechanism: 'placement' };

  if (bestTspinLines(B) >= target) {
    const slot = bestTspin(B);
    if (!slot) return { step: t, mechanism: 'unattributed' };
    // Map the slot's rows back into Bpre's frame: a Bpre row p lands at p + #{cleared rows below}.
    const back = (rB: number) => {
      for (let p = 0; p < H; p++) if (p + clearedRows.filter(cr => cr > p).length === rB) return p;
      return rB;
    };
    const ps = slot.rows.map(back);
    if (clearedRows.some(cr => cr > Math.min(...ps) && cr < Math.max(...ps)))
      return { step: t, mechanism: 'line-clear' };
    // The clear only displaced the slot, so the piece must have formed it — but only if the
    // piece actually went near it. Otherwise neither did, and that is a finding.
    const touches = lk.cells.some(c => {
      const rB = c.row + clearedRows.filter(cr => cr > c.row).length;
      return slot.rows.includes(rB) || slot.rows.includes(rB - 1) || slot.rows.includes(rB + 1);
    });
    return { step: t, mechanism: touches ? 'placement' : 'unattributed' };
  }

  if (avail(t) >= target && garbageArrived) return { step: t, mechanism: 'garbage' };
  return { step: t, mechanism: 'unattributed' };
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
  /** improvements the step model could not explain — must be 0, and is published so it can't hide */
  unattributed: number;
  /** clause 2 across every event: where the cells holding the T up came from */
  floorOrigins: Record<FloorOrigin, number>;
  /** mechanism established AND a hole to close onto; the denominator is every executed tucked spin */
  forecastRate: number;
  /** mechanism established but clause 2 undecidable — reported, never counted either way */
  undecidedClause2: number;
} {
  const records: ForecastRecord[] = [];
  const totals: Record<ForecastKind, number> = { forecast_garbage: 0, forecast_lineclear: 0, self_built: 0, reactive: 0 };
  // Localising a mechanism walks back through the window re-evaluating boards the endpoints
  // already visited, and consecutive events share most of their windows. Memoised per call:
  // the boards are immutable, so this is arithmetic-identical to recomputing.
  const availCache = new Map<number, number>();
  const avail = (t: number) => {
    let v = availCache.get(t);
    if (v === undefined) { v = bestTspinLines(r.boards[t]!); availCache.set(t, v); }
    return v;
  };

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
    const availAtRoof = boardJ ? avail(j) : 0;
    const availAtSpin = boardK ? avail(k - 1) : 0;
    // `strict` selects the causal rule; loose keeps the original co-occurrence behaviour so
    // LOOSE=1 still reproduces the pre-correction numbers for comparison (auc.ts, run-forecast.ts).
    const improved = (strict && determinable)
      ? availAtSpin > availAtRoof
      : (clearBetween || garbageBetween);

    // Strip the garbage that arrived after the roof and re-ask: if the spin is unchanged, that
    // garbage cannot be holding it up at EXECUTION. This no longer classifies anything —
    // `localiseMechanism` does — but it is kept, and recorded, as an independent second opinion on
    // the garbage branch. It is the one instrument here validated directly against the wiki's own
    // boards (stripping the appended garbage line reproduces the article's "before" value in all
    // five of its garbage pairs), so it is worth keeping as an oracle even though it answers at the
    // wrong moment: garbage that made a slot and was then cleared away leaves it nothing to remove.
    // One source of truth classifies; this one observes, and a test asserts the two agree on the
    // corpus. No `garbageBetween` guard: a non-empty deletion set already implies one, since every
    // marked row was pushed in by an event inside the window.
    const arrivedSince = boardK ? garbageArrivedAfter(r, j, k) : new Set<number>();
    const garbageLoadBearing = !!(boardK && arrivedSince.size
      && bestTspinLines(withoutRows(boardK, arrivedSince)) < availAtSpin);

    // Which of the three edits in the causing step did it? Direct observation replaces both the
    // execution-time counterfactual AND the co-occurrence assertion, so the two forecast kinds
    // now rest on the same evidence instead of one being tested and the other asserted.
    const loc = (strict && determinable && improved)
      ? localiseMechanism(r, j, k, availAtSpin, avail) : null;

    // Clause 2, evaluated for every event rather than only the ones that reach the gate, so the
    // report can say how often it is decidable at all instead of only how often it passes.
    const origin = floorOrigin(r, k, j >= 0 ? j : null);
    // The support that decided it: the newest thing holding the piece up, or -1 if any of them is
    // garbage, since garbage has no lock index to be newest by. This read the nose row alone until
    // clause 2 stopped doing so — a diagnostic naming a cell the verdict never consulted is worse
    // than no diagnostic, because it reads like corroboration.
    const supports = lk.cells.map(c => c.row + 1 < H ? r.provSnaps[k - 1]?.[c.row + 1]?.[c.col] : null)
      .filter((p): p is number => p !== null && p !== undefined);
    const floorFrom = supports.length === 0 ? null
      : supports.includes(-1) ? -1 : Math.max(...supports);

    // Loose mode: the original rule verbatim, co-occurrence and all.
    const kind: ForecastKind = !(strict && determinable)
      ? (!improved ? 'reactive' : garbageBetween ? 'forecast_garbage'
         : clearBetween ? 'forecast_lineclear' : 'reactive')
      : !improved ? 'reactive'
      : loc!.mechanism === 'garbage' ? 'forecast_garbage'
      : loc!.mechanism === 'line-clear' ? 'forecast_lineclear'
      // `placement` is the player building their own slot — openers land here. So does
      // `unattributed`, which must stay COUNTED rather than folded away: it means the step model
      // failed to explain an improvement, and a metric that cannot say so will never be corrected.
      : 'self_built';

    // Clause 4 is recorded on every line-clear event rather than folded into `kind`, for the reason
    // clause 2 is: `kind` says which edit closed the gap, which is a fact about the game, and every
    // consumer already routes its numerator through `isVerifiedForecast`.
    const closingClearWasSpin = loc?.mechanism === 'line-clear'
      ? r.locks[loc.step]!.spin !== 'none' : undefined;

    totals[kind]++;
    records.push({ lockIndex: k, frame: lk.frame, lines: lk.cleared, spin: lk.spin, closingClearWasSpin,
      kind, separation: j >= 0 ? k - j : -1, roofFrom: j >= 0 ? j : null, roofIsGarbage,
      slotOpenedLater: improved, determinable, availAtRoof, availAtSpin, garbageLoadBearing,
      mechanism: loc?.mechanism, mechanismStep: loc?.step, floorOrigin: origin, floorFrom });
  }
  const tspins = records.length;
  const verified = records.filter(isVerifiedForecast).length;
  const unattributed = records.filter(x => x.mechanism === 'unattributed').length;
  const floorOrigins: Record<FloorOrigin, number> =
    { 'pre-existed': 0, 'arrived-later': 0, undetermined: 0 };
  for (const x of records) floorOrigins[x.floorOrigin ?? 'undetermined']++;
  // an event whose mechanism holds but whose clause 2 cannot be decided is neither counted nor
  // discarded quietly: it is its own number, so a rate of zero cannot hide an undecidable case
  const undecidedClause2 = records.filter(x =>
    (x.kind === 'forecast_garbage' || x.kind === 'forecast_lineclear')
    && holePreExisted(x.floorOrigin ?? 'undetermined') === null).length;
  return { records, totals, tspins, unattributed, floorOrigins, undecidedClause2,
           forecastRate: tspins ? verified / tspins : 0 };
}

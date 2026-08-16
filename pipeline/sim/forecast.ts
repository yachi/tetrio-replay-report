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
 *          path_opened        — it crossed on the row removal, but the slot was already there and
 *                               merely UNREACHABLE. The clear removed the lid, it did not build
 *                               the room. Not a forecast under `spec/Forecast.dfy` — see below.
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
 *
 * CONTRACT (ROADMAP item 3, closed 2026-08-09): `lines` is how many rows this T-spin would CLEAR
 * if it locked here — every full row of the RESULTING board, because the game clears every full row
 * on lock — NOT only the rows the T's own cells complete. So a full row already on the board before
 * the T is counted. That is game-faithful, not a bug, and it never misattributes: the only board a
 * caller ever hands this that already holds a full row is `localiseMechanism`'s `Bpre` (the pre-clear
 * board, `A + this step's placement`); `A = boards[t-1]` is post-clear so holds none, and `B` and
 * every `avail(t)` board have their full rows removed. Every full row `bestTspin` ever sees was thus
 * completed by that step's own placement, which is exactly what `bestTspinLines(Bpre)` credits.
 */
/**
 * BFS visited set as a direct-address table (CLRS §11.1) rather than a `Set` of built strings.
 *
 * A state is three small integers, and the old key was `` `${rot}:${col}:${row}` `` — a string
 * built, hashed and compared for every edge the search relaxes. Encoding the same triple as one
 * array index removes the allocation and the hash entirely.
 *
 * The window is deliberately WIDER than anything measured, and the fallback is why that is safe
 * rather than sloppy. `bfs-cap.ts` establishes that rows are NOT bounded by the engine —
 * `vendor/core/srs.ts` skips the board lookup for `row < 0` instead of rejecting it, so a piece
 * can in principle climb, and the only ceiling anyone has is the measured [-2, 39] over 2 000
 * boards plus an unwritten kick-table argument. So this table must not *assume* a range: a state
 * outside the window falls back to a `Set`, keyed identically to before. The table is a fast path
 * for the states that occur, not a claim about which states can occur, and `bfs-cap.ts`'s standing
 * warning stays true.
 *
 * Cleared by generation stamp rather than by `.fill(0)`: each call bumps `visitGen` and a slot
 * counts as visited only when it holds the current stamp, so the 2 304-entry table is allocated
 * once for the process instead of once per board.
 */
const V_ROT = 4, V_COL_MIN = -2, V_COL_N = 12, V_ROW_MIN = -4, V_ROW_N = 48;
const visitStamp = new Uint32Array(V_ROT * V_COL_N * V_ROW_N);   // expansion dedup
const rotStamp   = new Uint32Array(V_ROT * V_COL_N * V_ROW_N);   // evaluation dedup: rotation arrivals only
let visitGen = 0;

function visitIndex(rotation: number, col: number, row: number): number {
  const c = col - V_COL_MIN, r = row - V_ROW_MIN;
  if (c < 0 || c >= V_COL_N || r < 0 || r >= V_ROW_N) return -1;
  return (rotation * V_COL_N + c) * V_ROW_N + r;
}

/**
 * What one `bestTspin` call actually explored. Opt-in, and the only reader is `bfs-cap.ts`.
 *
 * `bfs-cap.ts` used to walk its OWN copy of this BFS — it imported `vendor/core/srs.ts` and never
 * imported this file — so it printed the same 688 for the shipped engine and for the 2026-08-10
 * arrival-key fix, and that agreement was worth nothing: a replica cannot disagree with an engine
 * it never calls. Every number that file prints is now this search's.
 *
 * The hot path pays one null test per call and nothing else. `queue` and the spans are derived by
 * walking `q` AFTER the search, inside the `if (trace)`, rather than maintained per edge:
 *   - `queue`     is `q.length`, the (position, arrival) PAIR queue — the thing `h < 40000` bounds
 *   - `positions` is the distinct-position count, which is `expand === true` on exactly the entries
 *     whose `seenOrMark` returned false (the spawn included), so it needs no second set
 *   - the spans are over queued states, which is what makes the row range an observation rather
 *     than the undischarged [-2, 39] assumption the caps exist to survive
 */
export interface BfsTrace { queue: number; positions: number; rowLo: number; rowHi: number; colLo: number; colHi: number }
let trace: BfsTrace | null = null;

/** Run `fn` with tracing on and return the LARGEST search it made. Scoped, so it cannot be left on. */
export function withBfsTrace<T>(fn: () => T): { value: T; trace: BfsTrace } {
  const outer = trace;
  const t: BfsTrace = { queue: 0, positions: 0, rowLo: Infinity, rowHi: -Infinity, colLo: Infinity, colHi: -Infinity };
  trace = t;
  try { return { value: fn(), trace: t }; } finally { trace = outer; }
}

export function bestTspin(board: Board): { lines: number; rows: number[] } | null {
  let best = 0, bestRows: number[] = [];
  const spawn: ActivePiece = { type: 'T', rotation: 0, col: 3, row: 18 };
  // Uint32 wraps after 4.29e9 boards; restarting from 1 over a zeroed table keeps the
  // "holds the current stamp" test honest instead of resurrecting stale marks.
  if (++visitGen === 0xffffffff) { visitStamp.fill(0); visitGen = 1; }
  const gen = visitGen;
  const outside = new Set<string>();
  /** True if this state had already been queued; marks it visited either way. */
  const seenOrMark = (rotation: number, col: number, row: number): boolean => {
    const i = visitIndex(rotation, col, row);
    if (i < 0) {                       // outside the measured window — exact, just slower
      const k = `${rotation}:${col}:${row}`;
      if (outside.has(k)) return true;
      outside.add(k);
      return false;
    }
    if (visitStamp[i] === gen) return true;
    visitStamp[i] = gen;
    return false;
  };
  seenOrMark(0, 3, 18);
  const outsideRot = new Set<string>();
  /**
   * True if a ROTATION arrival at this position was already evaluated; marks it either way.
   *
   * The key deliberately omits the kick bit, and that omission is licensed by exactly one
   * reading: inside `detectTSpin`, `usedKick` is consumed at a single line (`sim.ts:108`) where
   * it chooses `'full'` vs `'mini'` — and both are `!== 'none'`, which is the whole of this
   * search's admission test. So a kicked and an unkicked rotation arrival at the same position
   * are indistinguishable TO `bestTspin`, and one evaluation entry per position suffices.
   *
   * ⚠️ This is NOT a claim that the kick bit is redundant. `usedKick` stays load-bearing for
   * `simulate()` at `sim.ts:216`, which records the actual spin type for scoring, where 'full'
   * and 'mini' are worth different attack. The collapse is valid for `bestTspin` only; do not
   * carry it into any caller that distinguishes the two.
   */
  const rotSeenOrMark = (rotation: number, col: number, row: number): boolean => {
    const i = visitIndex(rotation, col, row);
    if (i < 0) {
      const k = `${rotation}:${col}:${row}`;
      if (outsideRot.has(k)) return true;
      outsideRot.add(k); return false;
    }
    if (rotStamp[i] === gen) return true;
    rotStamp[i] = gen; return false;
  };
  const q: { p: ActivePiece; rot: boolean; kick: boolean; expand: boolean }[] =
    [{ p: spawn, rot: false, kick: false, expand: true }];
  for (let h = 0; h < q.length && h < 40000; h++) {
    const { p: cur, rot, kick, expand } = q[h]!;
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
        // The appended roof is always `topCell - 1`, so a slot topping at row 0 yields roof
        // row -1. That is correct, not a degeneracy: the straddle test at `back()` reads it as
        // `cr > min(rows)` and no cleared row is ever negative, so `cr > -1` is the identical
        // predicate; clamping the roof to 0 would flip `cr = 0` from admitted to rejected and
        // INTRODUCE an inconsistency. Constructible only as a `Board` argument, never as a game
        // state (row 0 needs a 40-row stack that a topout ends first); 0 of 7,544 corpus boards.
        const rows = cells.map(c => c.row);
        bestRows = [...rows, Math.min(...rows) - 1];
      }
    }
    if (!expand) continue;
    const nexts: [ActivePiece | null, boolean][] = [
      [tryMove(board, cur, -1, 0), false], [tryMove(board, cur, 1, 0), false],
      [tryMove(board, cur, 0, 1), false], [tryRotate(board, cur, 1), true], [tryRotate(board, cur, -1), true]];
    for (const [n, isRot] of nexts) {
      if (!n) continue;
      const isKick = isRot && (n.col !== cur.col || n.row !== cur.row);
      // A non-rotation arrival can NEVER satisfy the spin test (`rot` gates it), so it needs no
      // pair entry — it is only ever worth enqueuing to expand a position not yet expanded.
      // Rotation arrivals get the full (position, arrival) evaluation key.
      if (!isRot) {
        if (seenOrMark(n.rotation, n.col, n.row)) continue;
        q.push({ p: n, rot: false, kick: false, expand: true });
        continue;
      }
      if (rotSeenOrMark(n.rotation, n.col, n.row)) continue;
      q.push({ p: n, rot: true, kick: isKick, expand: !seenOrMark(n.rotation, n.col, n.row) });
    }
  }
  if (trace) {
    trace.queue = Math.max(trace.queue, q.length);
    trace.positions = Math.max(trace.positions, q.reduce((n, e) => n + (e.expand ? 1 : 0), 0));
    for (const e of q) {
      trace.rowLo = Math.min(trace.rowLo, e.p.row); trace.rowHi = Math.max(trace.rowHi, e.p.row);
      trace.colLo = Math.min(trace.colLo, e.p.col); trace.colHi = Math.max(trace.colHi, e.p.col);
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
 * what it does NOT rest on is the caps being provably dead. Since 2026-08-10 the search carries
 * TWO dedup keys, so what bounds `q` has to be said twice over:
 *
 * A **position** is `rotation:col:row`, and that is what `seenOrMark`/`visitStamp` key — it is the
 * expansion key, and it is exactly the old one, because a state's successors are a function of the
 * position alone (`tryMove`/`tryRotate` never read how the state was entered). A **queue entry** is
 * a (position, arrival) pair, and `rotSeenOrMark`/`rotStamp` key the second of those: one extra
 * entry per position, admitting a rotation arrival that a shift or a soft-drop would otherwise have
 * marked away. So the queue is bounded by |positions| x |arrivals|, and |arrivals| here is 2.
 *
 * Only two of the three position coordinates are bounded by the engine. Columns are:
 * `isValidPosition` rejects any cell outside 0..9, and the T's anchor is offset from its cells
 * asymmetrically per rotation, so the anchor runs -1..7 in R (its leftmost cell sits at offset 1),
 * 0..8 in L (its rightmost cell does), and 0..7 in 0/2 — a union of -1..8, still 10 values but not
 * the 0..9 previously assumed, and the 4x10 product is loose because no single rotation admits all
 * ten. Rows are NOT bounded: `vendor/core/srs.ts:129` is `if (row < 0) continue`, so every negative
 * row is a legal position and nothing in the collision test stops a piece climbing.
 *
 * Four numbers live nearby and mean four different things; keep them apart:
 *
 * - **1680** = 4*10*42 is the position bound CONDITIONAL on rows staying in [-2, 39]. That side
 *   condition needs kick-table reasoning (a piece rises only on a kick, a kick only fires when the
 *   [0,0] candidate is blocked, and the JLSZT table lifts at most 2), which is a sketch nobody has
 *   turned into a proof. 1680 is therefore an ASSUMPTION, undischarged.
 * - **2304** = 4*12*48 is the size of `visitStamp` (and now of `rotStamp`). It is a direct-address
 *   FAST PATH, not a bound: `visitIndex` returns -1 outside the window and the search falls back to
 *   an exact `Set`, so a position beyond 2304 is slower, never dropped.
 * - **688** is the measured maximum number of distinct POSITIONS over 2 000 boards (`bfs-cap.ts`).
 *   It is key-independent — successors depend on position alone, so splitting the key cannot change
 *   it — and it is not a queue length in either variant.
 * - **848** is the measured maximum PAIR QUEUE under this collapsed 2-valued arrival key. That is
 *   1.23 entries per position, not the 2 the product allows.
 *
 * So `h < 40000` is a LIVE belt rather than dead code — it guards against the unbounded-row case
 * that no proof excludes — and against the measured 848 it leaves 40000/848 ~= 47x of headroom.
 */
export function tspinAvailable(board: Board): boolean {
  return bestTspinLines(board) > 0;
}

/**
 * `forecast_garbage`   improved, and the garbage is LOAD-BEARING — removing it strictly reduces the
 *                      available spin. Causally verified.
 * `forecast_lineclear` improved, and the clear FORMED the slot: a cleared row lay strictly inside
 *                      it, so removing that row is what brought roof and cavity together.
 * `path_opened`        improved, and the clear did it, but by removing an obstruction ABOVE a slot
 *                      that already existed cell for cell and was merely unreachable. See
 *                      `localiseMechanism`'s `access` branch.
 * `self_built`         improved, but the player built the slot themselves. Openers land here.
 * `reactive`           the available spin did not improve between roof and execution.
 *
 * ONLY THE TWO `forecast_` KINDS MAY ENTER THE NUMERATOR, and the prefix is what marks them. That is
 * why the fifth kind is NOT called `forecast_access`: `isVerifiedForecast` tests the two names, and a
 * third `forecast_`-prefixed kind is one careless `startsWith` away from being counted. The exclusion
 * is not a policy choice — `spec/Forecast.dfy`'s clause 3 (`GapClosed`, :506-530) is the
 * strictly-inside rule stated in the hand-written concept spec, and an access event's cleared rows lie
 * OUTSIDE `[roofAt, floorAt]`, so `IsForecast` is false for it. Counting it would put this file in
 * disagreement with the spec, and in this repo the spec is the definition. The spec has no vocabulary
 * for reachability at all (`availAtJ`/`availAtK` are opaque ints), which is the same fact from the
 * other side: `path_opened` is a distinction the concept spec does not draw, so it cannot be a
 * forecast under it.
 */
/**
 * The kinds as a RUNTIME list, with the type derived from it rather than the other way round.
 *
 * Every consumer that needs a zeroed tally builds it from here. A bare object literal is how the
 * `self_built` bug happened — `run-forecast.ts`'s initialiser omitted the kind, `tot[rec.kind]++`
 * evaluated `undefined + 1`, and the printed breakdown was `NaN` for 388 of 654 records while the
 * header count above it stayed right. A `satisfies Record<ForecastKind, number>` would NOT have
 * caught it: there is no tsc step in this repo (see `check_ts_imports`'s header), so a type-level
 * guard here is decorative by construction. Deriving the literal at runtime is the only version
 * that cannot be forgotten.
 */
export const FORECAST_KINDS = [
  'forecast_garbage', 'forecast_lineclear', 'path_opened', 'self_built', 'reactive',
] as const;
export type ForecastKind = typeof FORECAST_KINDS[number];
/** a zeroed tally over every kind — the one place a new kind has to be added */
export const zeroKindTotals = (): Record<ForecastKind, number> =>
  Object.fromEntries(FORECAST_KINDS.map(k => [k, 0])) as Record<ForecastKind, number>;
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

/**
 * WHICH clause disqualified a mechanism-established event — the fact the report used to ASSUME.
 *
 * `isVerifiedForecast` is a boolean, so a consumer that wants to say *why* an event did not count
 * has nothing to read and has to guess. `pipeline/forecast_section.py` guessed: whenever
 * `mechanism_established > forecast_total` it printed clause 2 (「個底係天花板之後先至嚟」) as the
 * reason. That was false on two published reports — 2026-08-09 and 2026-08-14 are both clause 4,
 * and 08-14's sits on the corpus's only DT Cannon round — and no gate could see it, because the
 * renderer and the checker were reading the same absent fact.
 *
 * The verdict is the JOINT one, never a first-match: clause 2 and clause 4 are independent tests
 * and both can reject the same event, so the pairs where both fire are their own values rather
 * than being attributed to whichever was asked first. Clause 2's UNDECIDABLE case is likewise its
 * own value and is not folded into its rejection: "the floor is garbage and garbage straddles the
 * window" is not "the floor arrived later", and printing one as the other is the same class of
 * defect this function exists to end.
 *
 * `null` — not a bucket — for an event whose mechanism is not established at all (`reactive`,
 * `self_built`, `path_opened`). Those are excluded one clause earlier and a caller that bucketed
 * them here would be reporting openers as clause-2 rejections. `path_opened` belongs in that list
 * rather than in the guard above it: its mechanism IS established, and it is still not a forecast —
 * the spec's clause 3 rejects it on geometry, before clauses 2 and 4 are ever reached. Giving it a
 * `ClauseVerdict` would put it in a breakdown whose denominator (`mechanism_established`) it is not
 * in, so the six buckets would stop summing.
 *
 * The mapping back to the boolean is exact and asserted by every caller: `rejectedBy(r) ===
 * 'counted'` iff `isVerifiedForecast(r)`.
 */
export type ClauseVerdict =
  | 'counted'
  | 'floor_arrived_later'
  | 'closing_clear_was_spin'
  | 'floor_arrived_later_and_closing_clear_was_spin'
  | 'floor_undecidable'
  | 'floor_undecidable_and_closing_clear_was_spin';

/** Every verdict, in the order the artifact emits them. `counted` first: it is the numerator. */
export const CLAUSE_VERDICTS: ClauseVerdict[] = [
  'counted',
  'floor_arrived_later',
  'closing_clear_was_spin',
  'floor_arrived_later_and_closing_clear_was_spin',
  'floor_undecidable',
  'floor_undecidable_and_closing_clear_was_spin',
];

export function rejectedBy(r: ForecastRecord): ClauseVerdict | null {
  if (!(r.kind === 'forecast_garbage' || r.kind === 'forecast_lineclear')) return null;
  const hole = holePreExisted(r.floorOrigin ?? 'undetermined');   // clause 2: true / false / null
  const spin = r.closingClearWasSpin === true;                    // clause 4
  if (hole === true) return spin ? 'closing_clear_was_spin' : 'counted';
  if (hole === null) return spin ? 'floor_undecidable_and_closing_clear_was_spin' : 'floor_undecidable';
  return spin ? 'floor_arrived_later_and_closing_clear_was_spin' : 'floor_arrived_later';
}

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
 * at `j` with everything false is what makes the answer relative to the roof. For `j = -1` (a roof
 * with no placer) the walk starts at lock 0, whose pre-board is the empty field — the one place the
 * body substitutes an empty board rather than reading `boards[t - 1]`, so every garbage row then on
 * the board counts as having arrived after the roof.
 *
 * Measured against the boards themselves: the marks reproduce the real garbage mask of `boards[t]`
 * at all 110,927 lock-steps of the four sessions across all seven swept configs, and the marked
 * rows come out ordered oldest-on-top everywhere — including `reference_queue`, the one config that
 * can insert garbage before the piece rather than after it.
 */
export function garbageArrivedAfter(r: SimResult, j: number, k: number): Set<number> {
  let post = new Array<boolean>(H).fill(false);
  // The walk starts at lock 0 when the roof has no placer (`j = -1`), and the board BEFORE lock 0
  // is empty — there is no `boards[-1]` to read. Falling through to `boards[t - 1]!` there threw,
  // which contradicted the promise three lines up; an empty pre-board is what makes that promise
  // true. Width is taken from a real board so this carries no hard-coded 10.
  const width = (r.boards[k - 1] ?? Object.values(r.boards)[0] ?? [[]])[0]!.length;
  const emptyBoard = () => Array.from({ length: H }, () => new Array(width).fill(null)) as Board;
  for (let t = j + 1; t <= k - 1; t++) {
    const lk = r.locks[t]!;
    const Bpre = (r.boards[t - 1] ?? emptyBoard()).map(row => [...row]) as Board;
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
 *
 * `access` IS THE FIFTH VALUE, AND IT EXISTS BECAUSE THE PARAGRAPH ABOVE IS ABOUT FORMATION WHILE
 * `bestTspin` MEASURES REACHABILITY. The geometric test is sound about what it says — a cleared row
 * outside the slot did not form it — and silent about the other way a clear raises availability:
 * removing an obstruction ABOVE a slot that already existed, cell for cell, and was merely
 * unreachable from spawn. The model had nowhere to put that, so it landed in one of two places
 * depending on an irrelevance, whether the causing piece happened to sit beside the slot:
 *
 *     piece does NOT touch  ->  `unattributed`   honest, and counted in the artefact
 *     piece DOES touch      ->  `placement`      confidently wrong, and counted NOWHERE
 *
 * The second half is why this was a defect rather than a curiosity: 2026-08-09's published report
 * said 「玩家自己落嗰隻棋整出嚟」 of a slot that piece did not make. The counter over `unattributed`
 * could only ever see the honest half, so a third event of the class would have arrived in silence.
 *
 * The test is the counterfactual the model never asked — delete the cleared rows FROM `A` ALONE,
 * with the piece never placed, and see whether the target is already reached. Two events in 1789
 * localised records over six sessions, 0 beyond the verified prefixes. `forecast-access-class.test.ts`
 * measures the class independently of this branch and names both.
 *
 * BRANCH ORDER IS MEASURED, NOT CHOSEN, and it is the whole of the design. Placed before the
 * strictly-inside test it reclassifies 9 events — every `forecast_lineclear` in the corpus, i.e. the
 * published numerator, plus 2 more the placement alone also explains; placed after `touches` it
 * reclassifies 1 and leaves the confidently-wrong half exactly as it was, since `touches` gets there
 * first. Here — after the clear's own geometry, before the piece's — it reclassifies 2, which are the
 * 2 the class contains.
 */
export type Mechanism = 'garbage' | 'line-clear' | 'access' | 'placement' | 'unattributed';

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
  if (!garbageArrived) {
    if (!B.every((row, i) => row.every((c, x) => c === C[i]![x])))
      throw new Error(`step ${t}: reconstruction diverges from boards[${t}] with no garbage inserted`);
  } else {
    // ...and when garbage DID arrive, which is exactly when this used to check nothing at all.
    //
    // `!garbageArrived` guarded the only test of the step model, so the model was verified precisely
    // on the steps that cannot violate it and never on the steps that can. Measured 2026-08-08: under
    // `insertMode: 'immediate'` — a legal option, not one of the seven swept — garbage goes in BEFORE
    // the piece, `Bpre` merges pre-garbage rows with post-garbage coordinates, and the metric returned
    // 13 verified forecasts across the four sessions with nothing thrown. A guard conditioned on the
    // very thing that breaks it is not a guard.
    //
    // Insertion is at the bottom and lifts the stack, so C must be B raised by some shift with that
    // many fresh garbage rows underneath. The shift is DERIVED from the boards, never read from
    // `garbageEvents[].amt`: this file already documents (see `garbageArrivedAfter`) that a
    // hand-built SimResult's events need not agree with its boards, and the unit fixtures do exactly
    // that — their boards move by one row while every event says four. Deriving it keeps the check
    // about the step model, which is what is actually in doubt.
    const sameRow = (x: readonly unknown[], y: readonly unknown[]) => x.every((c, i) => c === y[i]);
    let shift = -1;
    for (let s = 1; s < H && shift < 0; s++) {
      // the bottom `s` rows of C are the arrivals, so they must all carry garbage; everything above
      // is B lifted by `s`. Requiring both keeps a large shift from matching vacuously.
      if (!C.slice(H - s).every(row => row.some(c => (c as unknown as string) === 'G'))) continue;
      let ok = true;
      for (let i = 0; i + s < H && ok; i++) if (!sameRow(B[i + s]!, C[i]!)) ok = false;
      if (ok) shift = s;
    }
    if (shift < 0)
      throw new Error(`step ${t}: boards[${t}] is not boards[${t - 1}] placed, cleared and then lifted `
        + `by a garbage insert — the step is not place -> clear -> insert`);
  }

  if (bestTspinLines(Bpre) >= target) return { step: t, mechanism: 'placement' };

  if (bestTspinLines(B) >= target) {
    const slot = bestTspin(B);
    // Unreachable, and not merely in practice: reaching this block needs
    // `bestTspinLines(Bpre) < target`, and `bestTspinLines` is never negative, so `target >= 1`;
    // the block's own condition then gives `bestTspinLines(B) >= 1`, and `bestTspin` returns null
    // exactly when `bestTspinLines` is 0. No argument tuple gets here with a null slot, so no
    // mutant is listed for it — it is here for the type, not the value. Measured 2026-08-09 for
    // the avoidance of doubt: reached 1 time in 389 corpus calls and 18 over the fixture suite,
    // null in 0 of them.
    if (!slot) return { step: t, mechanism: 'unattributed' };
    // Map the slot's rows back into Bpre's frame: a Bpre row p lands at p + #{cleared rows below}.
    const back = (rB: number) => {
      for (let p = 0; p < H; p++) if (p + clearedRows.filter(cr => cr > p).length === rB) return p;
      return rB;
    };
    const ps = slot.rows.map(back);
    if (clearedRows.some(cr => cr > Math.min(...ps) && cr < Math.max(...ps)))
      return { step: t, mechanism: 'line-clear' };
    // The clear did not FORM the slot — but availability here is reachability, so it may still have
    // opened the PATH to one that was already there. Asked of `A` alone, with the piece never
    // placed: if the same rows removed from the pre-board already reach the target, the clear
    // sufficed on its own and crediting the piece beside it would be the confidently-wrong verdict
    // this branch exists to stop. `clearedRows` indexes `Bpre`, which is `A` plus cells and no rows
    // removed, so the two frames coincide and no back-mapping is needed.
    if (bestTspinLines(withoutRows(A, new Set(clearedRows))) >= target)
      return { step: t, mechanism: 'access' };
    // The clear only displaced the slot, so the piece must have formed it — but only if the
    // piece actually went near it. Otherwise neither did, and that is a finding.
    //
    // BOTH EXITS BELOW ARE NOW UNREACHED ON THIS CORPUS, and that is the shape of the repair rather
    // than an accident. Measured 2026-08-16 over all six sessions: 11 records reach this block at
    // all — 9 `formed` above, 2 `access`, and **0** here, either way. Before the `access` branch the
    // `touches` exit fired exactly once (2026-08-09 `-6.ttrm` r7 pinglamb lock 24), and that one
    // firing is the whole defect: a Z whose cells provably sit outside the slot was credited with
    // building it because one cell landed one row above, and the report published
    // 「玩家自己落嗰隻棋整出嚟」 of a slot that piece did not make. The branch absorbed it.
    //
    // So the only thing exercising these two lines is the `DISP_*` fixture in `forecast.test.ts` —
    // which is why that fixture is load-bearing and not decorative. It is the sole killer of the
    // mutant that asks the counterfactual of `Bpre` instead of `A`: `withoutRows(Bpre, clearedRows)`
    // IS `B`, and this block is already inside `bestTspinLines(B) >= target`, so that mutant makes
    // the branch above fire unconditionally — and NO corpus test notices, because on this corpus
    // everything reaching here takes the `access` exit anyway. Kept as live code, not deleted: a
    // clear that displaces a slot the piece did build is an ordinary board, not an impossible one.
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
  /**
   * Admitted T-spins (`spin !== 'none'`) that never became a tucked, line-clearing record — the
   * denominator's EXCLUDED scope, by lock index so a consumer can restrict to its verified prefix.
   * `records` are the tucked line-clearing spins (the published `verified_tspins`); this is where
   * the rest went. `records.length + noSnapshot + untucked` is every line-clearing T-spin, so the
   * published 654 is that set MINUS the untucked and the snapshot-less — which is why the report may
   * not call 654 "all verifiable T-spins". `zeroClear` is a spin that cleared nothing (not part of
   * the line-clearing denominator at all).
   */
  drops: { zeroClear: number[]; noSnapshot: number[]; untucked: number[] };
} {
  const records: ForecastRecord[] = [];
  // Why an admitted T-spin does not reach the tucked, line-clearing record set. Counted, not
  // silently `continue`d, so the denominator's scope is measured — the asymmetry that let the
  // numerator bug live for weeks was that the numerator had a gate and this denominator had none.
  const drops = { zeroClear: [] as number[], noSnapshot: [] as number[], untucked: [] as number[] };
  const totals = zeroKindTotals();
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
    if (lk.spin === 'none') continue;                        // not a T-spin at all
    if (lk.cleared === 0) { drops.zeroClear.push(k); continue; }   // a spin that cleared nothing

    // The board state the T landed into is the snapshot BEFORE this lock (k-1).
    const prev = k > 0 ? r.provSnaps[k - 1] : null;
    if (!prev) { drops.noSnapshot.push(k); continue; }

    // Roof = filled cells directly above the T's own cells.
    const roofProv: (number | null)[] = [];
    for (const c of lk.cells) {
      const above = c.row - 1;
      if (above < 0 || above >= H) continue;
      const p = prev[above]?.[c.col];
      if (p !== null && p !== undefined) roofProv.push(p);
    }
    if (roofProv.length === 0) { drops.untucked.push(k); continue; }   // no overhang → not tucked

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
      // The clear opened the path to a slot that was already there. It gets its own kind rather
      // than widening the line-clear branch, because the report's line-clear gloss
      // 「消嗰行啱啱夾喺天花板同窿位中間」 IS the strictly-inside test — widening the branch would
      // falsify a printed sentence in order to fix a miscount.
      : loc!.mechanism === 'access' ? 'path_opened'
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
  return { records, totals, tspins, unattributed, floorOrigins, undecidedClause2, drops,
           forecastRate: tspins ? verified / tspins : 0 };
}

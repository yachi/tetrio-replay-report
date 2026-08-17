/**
 * The metric against real sessions, not a hand-built board.
 *
 * Synthetic fixtures state what the rule SHOULD do on shapes chosen to exercise it. They cannot
 * state what it does on real play, and two rules that agree on every fixture can disagree wildly
 * on a corpus — which is exactly what happened here: the co-occurrence rule and the causal rule
 * agree on most fixtures and differ by 86 events on 2026-07-28 alone.
 *
 * So this pins the counts, per session. They are REGRESSION PINS, not an oracle: they were
 * produced by this code, and the only external authority behind most of them is the wiki
 * definition and the hand-checked boards of 2026-07-28's one surviving event. A change here is
 * not automatically a bug — but it must be a change someone decided to make, not one that
 * arrived with a refactor.
 *
 * ── WIDENED TO EVERY SESSION (2026-08-16) ───────────────────────────────────────────────────────
 * This file hardcoded 2026-07-28 and pinned `unattributed: 0` inside its bucket `toEqual` —
 * deliberately, because 07-28 carries the corpus's only mechanism-established forecast. The
 * consequence nobody intended: the file never saw any OTHER session, including 2026-08-14, whose
 * `unattributed` was then 1. Same failure mode as `forecast-facts.test.ts` defaulting to
 * `DISCOVERED[0]`: a single hardcoded session reads as coverage but is one session six times.
 *
 * 07-28 keeps its dedicated, hand-verified test below — WIDENING MUST NOT TRADE IT AWAY. Every
 * OTHER session's totals/floors/forecasts/mechanism events are pinned the same way `openers.test.ts`
 * pins its per-session tables: literals produced by this code, not re-derived from it at test time,
 * so a regression has to change a committed number rather than the number silently following the
 * code.
 *
 * ── AND THE `unattributed` EXCEPTION IS GONE, BECAUSE THE MODEL WAS REPAIRED (2026-08-16) ────────
 * That 08-14 event was one half of a class `localiseMechanism` had no bucket for: a clear that
 * removed the LID over a slot which already existed rather than forming it. `access` is the fifth
 * `Mechanism` and `path_opened` the fifth `ForecastKind`, so the event is now classified instead of
 * excepted, and `unattributed` is 0 in every session. The named-exception machinery that carried it
 * (`CORPUS_UNATTRIBUTED_GAP` here, `UNATTRIBUTED_STEP_MODEL_GAP` in forecast-facts.test.ts, both
 * derived from `step-model-gap.ts`) is deleted rather than emptied — an exception list satisfied by
 * nothing is the stale-entry failure its own header forbade. `unattributed` stays a PINNED 0 inside
 * the bucket `toEqual` below: the counter is kept because the next gap is what it is for, and 0 is
 * the strongest statement about it available.
 */
import { test, expect, describe } from 'bun:test';
import { existsSync, readdirSync } from 'node:fs';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';
import { forecastMetric, isVerifiedForecast, type ForecastKind, type FloorOrigin } from './forecast.ts';

const SESSIONS_ROOT = `${import.meta.dir}/../../sessions`;
const SESSION_DIRS = readdirSync(SESSIONS_ROOT, { withFileTypes: true })
  .filter(d => d.isDirectory()).map(d => d.name).sort();
// Narrows to one session for fast iteration, mirroring FORECAST_FACTS in forecast-facts.test.ts.
// An override name that doesn't exist is a real error (typo), not a silent empty run.
const OVERRIDE = process.env.FORECAST_CORPUS_SESSION;
if (OVERRIDE && !SESSION_DIRS.includes(OVERRIDE))
  throw new Error(`FORECAST_CORPUS_SESSION=${OVERRIDE} is not a session under ${SESSIONS_ROOT}`);
const SESSIONS = OVERRIDE ? [OVERRIDE] : SESSION_DIRS;

type Totals = Record<ForecastKind | 'unattributed', number>;
type Floors = Record<FloorOrigin, number>;

const isCSpinTriple = (lk: { piece: string; cleared: number; cells: { col: number; row: number }[] }) => {
  if (lk.piece !== 'T' || lk.cleared !== 3) return false;
  const cols = lk.cells.map(c => c.col), rows = lk.cells.map(c => c.row);
  // vertical T: two columns wide, three rows tall — the shape the wiki diagrams show
  return Math.max(...cols) - Math.min(...cols) === 1 && Math.max(...rows) - Math.min(...rows) === 2;
};

// ONE pass per session over loadCases/runCaseOracle — the C-Spin population and the load-bearing
// counterfactual used to be separate loops re-running the (expensive) oracle a second time; folded
// in here so widening to six sessions doesn't also double the wall clock.
function run(dir: string) {
  const totals: Totals = {
    forecast_garbage: 0, forecast_lineclear: 0, path_opened: 0, self_built: 0, reactive: 0,
    unattributed: 0 };
  const floors: Floors = { 'pre-existed': 0, 'arrived-later': 0, undetermined: 0 };
  const forecasts: string[] = [];
  const mechanismOnly: string[] = [];
  let loadBearingButNotImproved = 0;
  let behindACSpin = 0, counted = 0;
  let casesSeen = 0;
  for (const c of loadCases(dir)) {
    casesSeen++;
    const r = runCaseOracle(c);
    const v = verifiedIndex(r, c.truth);
    if (v < 0) continue;
    for (const rec of forecastMetric(r, true).records) {
      // Same gate both source loops shared (`run()`'s and the C-Spin test's own): everything below
      // is scoped to the verified prefix. Folding the C-Spin scan in under it, rather than before
      // it, is what keeps `behindACSpin`/`counted` identical to the two-loop original.
      if (rec.lockIndex > v) continue;
      totals[rec.kind as ForecastKind]!++;
      floors[rec.floorOrigin!]++;
      if (rec.mechanism === 'unattributed') totals.unattributed!++;
      if (rec.kind === 'forecast_garbage' || rec.kind === 'forecast_lineclear')
        mechanismOnly.push(`${c.user} ${c.file} r${c.round} lock ${rec.lockIndex} ${rec.kind} `
          + `floor ${rec.floorOrigin} from ${rec.floorFrom} roof ${rec.roofFrom}`);
      if (isVerifiedForecast(rec))
        forecasts.push(`${c.user} ${c.file} r${c.round} lock ${rec.lockIndex} ${rec.kind} `
          + `roof ${rec.roofFrom} ${rec.availAtRoof}->${rec.availAtSpin}`);
      // the execution-time counterfactual firing on an event the scalar gate called reactive
      if (rec.kind === 'reactive' && rec.garbageLoadBearing) loadBearingButNotImproved++;
      if (rec.roofFrom !== null) {
        let hit = false;
        for (let t = rec.roofFrom + 1; t < rec.lockIndex; t++) if (isCSpinTriple(r.locks[t]!)) hit = true;
        if (hit) {
          behindACSpin++;
          if (isVerifiedForecast(rec)) counted++;
        }
      }
    }
  }
  return { totals, floors, forecasts, mechanismOnly, loadBearingButNotImproved,
           behindACSpin, counted, casesSeen };
}

// Regression pins. Every session's own audit trail lives beside its entry; 2026-07-28's is the
// richest because it is the one hand-verified event in the corpus (see the dedicated test below).
//
// `path_opened` and the two `self_built` values it moved arrived on 2026-08-16 with the `access`
// mechanism. The whole corpus-wide effect is TWO records — 08-09 (was `self_built`, the confidently
// wrong half) and 08-14 (was `self_built` with mechanism `unattributed`, the honest half) — so every
// other cell here is byte-identical to what it was before, which is the control on the change.
const PINNED_TOTALS: Record<string, Totals> = {
  '2026-07-22': { forecast_garbage: 0, forecast_lineclear: 1, path_opened: 0, self_built: 354, reactive: 424, unattributed: 0 },
  '2026-07-24': { forecast_garbage: 0, forecast_lineclear: 1, path_opened: 0, self_built: 228, reactive: 306, unattributed: 0 },
  // Re-blessed 2026-08-12 for the ORACLE board source (runCaseOracle, verified prefix 24.8% -> 92.3%).
  // Every bucket grew (reactive 121 -> 306, self_built 169 -> 295); forecast_lineclear 1 -> 2 because the
  // longer prefix reaches a SECOND mechanism event, `yachi 07-28-4 r2 lock 29`, which SURVIVES all four
  // clauses (next test) — the hand-sim never reached it.
  '2026-07-28': { forecast_garbage: 0, forecast_lineclear: 2, path_opened: 0, self_built: 295, reactive: 306, unattributed: 0 },
  '2026-08-01': { forecast_garbage: 0, forecast_lineclear: 2, path_opened: 0, self_built: 267, reactive: 327, unattributed: 0 },
  // path_opened: 1 / self_built 232 -> 231. `replay-2026-08-09-6.ttrm` r7 pinglamb lock 24: a Z that
  // cleared row 23 opened a slot at rows 24-26 it did not build, and was credited `placement` purely
  // because a lock cell at B-row 23 satisfies `touches`. This is the half a `unattributed` counter
  // could never see, and it was published as 「玩家自己落嗰隻棋整出嚟」.
  '2026-08-09': { forecast_garbage: 0, forecast_lineclear: 2, path_opened: 1, self_built: 231, reactive: 312, unattributed: 0 },
  // path_opened: 1 / self_built 404 -> 403 / unattributed 1 -> 0. `replay-2026-08-14-0.ttrm` r4 yachi
  // lock 74: the same class with the piece NOT touching, so it used to fall through to `unattributed`
  // and was the corpus's only entry in that bucket.
  '2026-08-14': { forecast_garbage: 0, forecast_lineclear: 1, path_opened: 1, self_built: 403, reactive: 462, unattributed: 0 },
};

const PINNED_FLOORS: Record<string, Floors> = {
  '2026-07-22': { 'pre-existed': 646, 'arrived-later': 81, undetermined: 52 },
  '2026-07-24': { 'pre-existed': 452, 'arrived-later': 46, undetermined: 37 },
  // "clause 2 is decidable for all but three of the 2026-07-28 events" is the historical framing:
  // undetermined rose 9 -> 46 (share 3.0% -> 7.6%) under the same 2026-08-12 re-blessing above, partly
  // the longer prefix reaching more garbage-heavy late boards, partly the oracle's RNG garbage-hole
  // columns making some garbage-straddled events genuinely undecidable.
  '2026-07-28': { 'pre-existed': 504, 'arrived-later': 53, undetermined: 46 },
  '2026-08-01': { 'pre-existed': 508, 'arrived-later': 47, undetermined: 41 },
  '2026-08-09': { 'pre-existed': 449, 'arrived-later': 55, undetermined: 42 },
  '2026-08-14': { 'pre-existed': 714, 'arrived-later': 84, undetermined: 69 },
};

// Population of "a T-spin trailing a C-Spin triple" per session — pinned alongside the verdict so a
// refactor that stopped FINDING C-Spins can't pass vacuously on an empty set. `counted` (the verdict
// that matters) is 0 in every session: no such T-spin is ever counted as a forecast.
const PINNED_CSPIN: Record<string, number> = {
  '2026-07-22': 109, '2026-07-24': 64, '2026-07-28': 89, '2026-08-01': 68, '2026-08-09': 64, '2026-08-14': 109,
};

const PINNED_FORECASTS: Record<string, string[]> = {
  '2026-07-22': ['yachi replay-2026-07-22-10.ttrm r0 lock 99 forecast_lineclear roof 96 0->2'],
  '2026-07-24': ['pinglamb replay-2026-07-24-4.ttrm r4 lock 105 forecast_lineclear roof 100 0->2'],
  '2026-07-28': ['yachi replay-2026-07-28-4.ttrm r2 lock 29 forecast_lineclear roof 23 0->2'],
  '2026-08-01': [
    'yachi replay-2026-08-01-4.ttrm r4 lock 39 forecast_lineclear roof 35 0->1',
    'yachi replay-2026-08-01-7.ttrm r4 lock 136 forecast_lineclear roof 130 0->2',
  ],
  '2026-08-09': ['pinglamb replay-2026-08-09-3.ttrm r8 lock 109 forecast_lineclear roof 100 0->2'],
  // 0 verified forecasts: 08-14's one mechanism event below is rejected at clause 2/4. Not to be
  // confused with that session's `path_opened` event, which is a different lock and never was a
  // forecast candidate — forecast-facts.test.ts traces both.
  '2026-08-14': [],
};

const PINNED_MECHANISM_ONLY: Record<string, string[]> = {
  '2026-07-22': ['yachi replay-2026-07-22-10.ttrm r0 lock 99 forecast_lineclear floor pre-existed from -1 roof 96'],
  '2026-07-24': ['pinglamb replay-2026-07-24-4.ttrm r4 lock 105 forecast_lineclear floor pre-existed from -1 roof 100'],
  '2026-07-28': [
    'yachi replay-2026-07-28-4.ttrm r2 lock 29 forecast_lineclear floor pre-existed from 22 roof 23',
    'pinglamb replay-2026-07-28-6.ttrm r5 lock 32 forecast_lineclear floor arrived-later from -1 roof 19',
  ],
  '2026-08-01': [
    'yachi replay-2026-08-01-4.ttrm r4 lock 39 forecast_lineclear floor pre-existed from -1 roof 35',
    'yachi replay-2026-08-01-7.ttrm r4 lock 136 forecast_lineclear floor pre-existed from 129 roof 130',
  ],
  '2026-08-09': [
    'pinglamb replay-2026-08-09-3.ttrm r8 lock 109 forecast_lineclear floor pre-existed from -1 roof 100',
    'yachi replay-2026-08-09-6.ttrm r6 lock 213 forecast_lineclear floor pre-existed from 191 roof 207',
  ],
  '2026-08-14': ['yachi replay-2026-08-14-2.ttrm r3 lock 18 forecast_lineclear floor pre-existed from 3 roof 12'],
};

for (const SESSION of SESSIONS) {
  const dir = `${SESSIONS_ROOT}/${SESSION}`;
  const R = existsSync(dir) ? run(dir) : null;
  const t = test as unknown as { skipIf: (c: boolean) => typeof test };
  const realData = t.skipIf(R === null);

  describe(SESSION, () => {
    realData('has replay cases for the pins below to mean anything', () => {
      // loadCases on an empty directory returns [] rather than throwing — the exact silent-corpus
      // gap this widening exists to close (see sim-test-corpus-silently-under-covers). The pinned
      // totals below are all non-zero, so they'd already catch this, but this fails closer to the
      // cause.
      expect(R!.casesSeen).toBeGreaterThan(0);
    });

    realData('the buckets are exactly what the audit settled on', () => {
      expect(R!.totals).toEqual(PINNED_TOTALS[SESSION]);
    });

    realData('no improvement in this session is unattributed', () => {
      // Redundant with the `toEqual` above, and kept for the reason the counter itself is kept: this
      // is the assertion whose failure NAMES the thing that went wrong, where the bucket comparison
      // reports a diff of six numbers. It was a named-exception list until the `access` repair
      // (2026-08-16); a bound would be the wrong replacement — an improvement the step model cannot
      // explain is a defect in the model, so the number is 0 and a 1 has to be traced, not absorbed.
      expect(R!.totals.unattributed).toBe(0);
    });

    realData('clause 2\'s floor origins are exactly what the audit settled on', () => {
      expect(R!.floors).toEqual(PINNED_FLOORS[SESSION]);
    });

    realData('the mechanism-established and verified-forecast events are exactly what the audit settled on', () => {
      expect(R!.mechanismOnly).toEqual(PINNED_MECHANISM_ONLY[SESSION]);
      expect(R!.forecasts).toEqual(PINNED_FORECASTS[SESSION]);
    });

    realData('no T-spin following a C-Spin triple is ever counted as a forecast', () => {
      // The population is pinned as well as the verdict — a refactor that stopped FINDING C-Spins
      // would otherwise leave `counted === 0` passing vacuously on an empty set.
      expect(R!.behindACSpin).toBe(PINNED_CSPIN[SESSION]);
      expect(R!.counted).toBe(0);
    });

    realData('the scalar gate and the garbage counterfactual agree on every event', () => {
      // Deletion set restricted to post-roof arrivals: in every session, no executed spin's clause
      // 4 verdict flips when only garbage that arrived after the roof is removed.
      expect(R!.loadBearingButNotImproved).toBe(0);
    });

    if (SESSION === '2026-07-28') {
      realData('one event survives all four clauses on the oracle — a real forecast the hand-sim was blind to', () => {
        // The hand-sim (24.8% coverage) never reached the boards where this forecast happens, so it
        // reported ZERO. The oracle reaches lock 29 of 07-28-4 r2: yachi builds a T-spin-Double slot
        // whose second line was NOT clearable when the setup piece landed (availAtRoof 0) and becomes
        // clearable by lock 29 via his own line clear (availAtSpin 2, floor pre-existed) — the forecast
        // signature. Hand-verified 2026-08-12: a real T-spin double (spin=full, cleared=2) whose attack
        // was fully cancelled by incoming garbage (amt6@f1211 + amt8@f1241, so no ige reached the
        // opponent), its slot in the stack ABOVE the garbage (hole-insensitive). The SECOND mechanism
        // event (07-28-6 lock 32) is still rejected at clause 2 — its nose rests on garbage that had
        // not arrived at the roof. Changing either verdict changes a string, and both are re-asserted
        // above via PINNED_FORECASTS / PINNED_MECHANISM_ONLY; this test exists to carry the narrative.
        expect(R!.forecasts).toEqual(PINNED_FORECASTS['2026-07-28']);
        expect(R!.mechanismOnly).toEqual(PINNED_MECHANISM_ONLY['2026-07-28']);
      });
    }
  });
}

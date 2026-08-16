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
 * `unattributed` is 1 (traced in forecast-facts.test.ts's `UNATTRIBUTED_STEP_MODEL_GAP` — a T-spin
 * Double whose slot was uncovered, not formed, by its closing clear; ROADMAP names the missing
 * `localiseMechanism` bucket). Same failure mode as `forecast-facts.test.ts` defaulting to
 * `DISCOVERED[0]`: a single hardcoded session reads as coverage but is one session six times.
 *
 * 07-28 keeps its dedicated, hand-verified test below — WIDENING MUST NOT TRADE IT AWAY. Every
 * OTHER session's totals/floors/forecasts/mechanism events are pinned the same way `openers.test.ts`
 * pins its per-session tables: literals produced by this code, not re-derived from it at test time,
 * so a regression has to change a committed number rather than the number silently following the
 * code. `unattributed` reuses the same named-exception idiom `forecast-facts.test.ts` uses for
 * `UNATTRIBUTED_STEP_MODEL_GAP` — this file can't import that (non-exported, and the file belongs
 * to a sibling change), so `CORPUS_UNATTRIBUTED_GAP` below is a session-level mirror of it: the
 * facts.json field is per-player, this file's `totals.unattributed` sums both players, and for
 * 2026-08-14 the only player with any is yachi (1), so the two numbers agree by inspection, not by
 * a shared import. Divergence between the two files' pins would itself be worth investigating.
 */
import { test, expect, describe } from 'bun:test';
import { existsSync, readdirSync } from 'node:fs';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';
import { forecastMetric, isVerifiedForecast, type ForecastKind, type FloorOrigin } from './forecast.ts';
import { UNATTRIBUTED_BY_SESSION } from './step-model-gap.ts';

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
    forecast_garbage: 0, forecast_lineclear: 0, self_built: 0, reactive: 0, unattributed: 0 };
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
const PINNED_TOTALS: Record<string, Totals> = {
  '2026-07-22': { forecast_garbage: 0, forecast_lineclear: 1, self_built: 354, reactive: 424, unattributed: 0 },
  '2026-07-24': { forecast_garbage: 0, forecast_lineclear: 1, self_built: 228, reactive: 306, unattributed: 0 },
  // Re-blessed 2026-08-12 for the ORACLE board source (runCaseOracle, verified prefix 24.8% -> 92.3%).
  // Every bucket grew (reactive 121 -> 306, self_built 169 -> 295); forecast_lineclear 1 -> 2 because the
  // longer prefix reaches a SECOND mechanism event, `yachi 07-28-4 r2 lock 29`, which SURVIVES all four
  // clauses (next test) — the hand-sim never reached it.
  '2026-07-28': { forecast_garbage: 0, forecast_lineclear: 2, self_built: 295, reactive: 306, unattributed: 0 },
  '2026-08-01': { forecast_garbage: 0, forecast_lineclear: 2, self_built: 267, reactive: 327, unattributed: 0 },
  '2026-08-09': { forecast_garbage: 0, forecast_lineclear: 2, self_built: 232, reactive: 312, unattributed: 0 },
  // unattributed: 1 is 2026-08-14's named, traced event (yachi, replay-2026-08-14-0.ttrm r4, lock 74)
  // — see CORPUS_UNATTRIBUTED_GAP below and forecast-facts.test.ts's UNATTRIBUTED_STEP_MODEL_GAP.
  '2026-08-14': { forecast_garbage: 0, forecast_lineclear: 1, self_built: 404, reactive: 462, unattributed: 1 },
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
  // 0 verified forecasts: 08-14's one mechanism event below is rejected at clause 2/4 (see
  // forecast-facts.test.ts's trace of the same event under UNATTRIBUTED_STEP_MODEL_GAP).
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

/**
 * `unattributed`'s named-exception list, session-level (this file sums both players; see the file
 * header for why it isn't a shared import with forecast-facts.test.ts's per-player one).
 *
 * `toBe(known)` is exact in both directions like `UNATTRIBUTED_STEP_MODEL_GAP`: a second such event
 * anywhere fails, and so does this one vanishing — `toBeLessThanOrEqual` would only catch the first.
 */
// Derived from the single list in step-model-gap.ts. This was a hand-written mirror of
// UNATTRIBUTED_STEP_MODEL_GAP that agreed with it 'by inspection' — one fact in two places,
// which is the shape this repo has been bitten by three times. Import, do not re-type.
const CORPUS_UNATTRIBUTED_GAP: Record<string, number> = UNATTRIBUTED_BY_SESSION;

test('every CORPUS_UNATTRIBUTED_GAP entry names a session this file actually discovers', () => {
  if (OVERRIDE) return;   // one session in view; the list as a whole is not what is being asked
  for (const s of Object.keys(CORPUS_UNATTRIBUTED_GAP)) expect(SESSION_DIRS).toContain(s);
});

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

    realData('the unattributed bucket matches the named exception, or is zero', () => {
      const known = CORPUS_UNATTRIBUTED_GAP[SESSION] ?? 0;
      expect(R!.totals.unattributed).toBe(known);
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

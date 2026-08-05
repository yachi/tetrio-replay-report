/**
 * The metric against a real session, not a hand-built board.
 *
 * Synthetic fixtures state what the rule SHOULD do on shapes chosen to exercise it. They cannot
 * state what it does on 654 events of real play, and two rules that agree on every fixture can
 * disagree wildly on a corpus — which is exactly what happened here: the co-occurrence rule and
 * the causal rule agree on most fixtures and differ by 86 events in the data.
 *
 * So this pins the counts. They are a REGRESSION PIN, not an oracle: they were produced by this
 * code, and the only external authority behind them is the wiki definition and the hand-checked
 * boards of the one surviving event. A change here is not automatically a bug — but it must be a
 * change someone decided to make, not one that arrived with a refactor.
 *
 * 2026-07-28 is the session that carries the corpus's single mechanism-established forecast, so
 * it pins the positive case rather than only the absence of one.
 */
import { test, expect } from 'bun:test';
import { existsSync } from 'node:fs';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';
import { forecastMetric, isVerifiedForecast, type ForecastKind, type FloorOrigin } from './forecast.ts';

const SESSION = `${import.meta.dir}/../../sessions/2026-07-28`;

const run = () => {
  const totals: Record<string, number> = {
    forecast_garbage: 0, forecast_lineclear: 0, self_built: 0, reactive: 0, unattributed: 0 };
  const floors: Record<FloorOrigin, number> =
    { 'pre-existed': 0, 'arrived-later': 0, undetermined: 0 };
  const forecasts: string[] = [];
  const mechanismOnly: string[] = [];
  let loadBearingButNotImproved = 0;
  for (const c of loadCases(SESSION)) {
    const r = runCase(c, {});
    const v = verifiedIndex(r, c.truth);
    if (v < 0) continue;
    for (const rec of forecastMetric(r, true).records) {
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
    }
  }
  return { totals, floors, forecasts, mechanismOnly, loadBearingButNotImproved };
};

const R = existsSync(SESSION) ? run() : null;
const t = test as unknown as { skipIf: (c: boolean) => typeof test };
const realData = t.skipIf(R === null);

realData('the 2026-07-28 buckets are exactly what the audit settled on', () => {
  expect(R!.totals).toEqual({
    forecast_garbage: 0,
    // the survivor: the ONLY event in 654 across four sessions whose mechanism holds up
    forecast_lineclear: 1,
    self_built: 89,
    reactive: 56,
    // an improvement the step model cannot explain would invalidate the buckets above it
    unattributed: 0,
  });
});

realData('nothing survives all four clauses, and the one that reaches clause 2 is named', () => {
  // A count of zero says nothing about WHY. This names the single event whose mechanism holds —
  // the L at lock 19 leaves an overhang, a full row sits between that overhang and the notch for
  // twelve pieces, the I at lock 31 clears it, the T goes in at 32 — and records that it is
  // rejected because the cell its nose rests on is garbage that had not arrived at lock 19. A
  // regression that re-admits it changes this string rather than silently moving a rate.
  expect(R!.forecasts).toEqual([]);
  expect(R!.mechanismOnly).toEqual([
    'pinglamb replay-2026-07-28-6.ttrm r5 lock 32 forecast_lineclear floor arrived-later from -1 roof 19',
  ]);
});

realData('clause 2 is decidable for all but three of the 2026-07-28 events', () => {
  // Published so a drift in the undecidable count is visible: an implementation that quietly
  // stopped being able to answer would otherwise present as a rate that had not moved.
  //
  // These moved when clause 2 started judging EVERY cell holding the piece up rather than the
  // deepest row alone. The old split read 83 / 48 field-floor / 13 / 2, and the 48 were the
  // giveaway: `field-floor` claimed the playfield bottom was the support, but across all 654
  // events and all seven configs the number of pieces held up by the floor ALONE is zero.
  expect(R!.floors).toEqual({
    'pre-existed': 126, 'arrived-later': 17, undetermined: 3,
  });
});

/**
 * An OUTCOME oracle for the C-Spin, deliberately not a rule the metric follows.
 *
 * The C-Spin (TKI積み) is the confound this metric exists to exclude — harddrop.com/wiki/C-Spin
 * says it "results in a T-Spin Triple which is usually followed by a T-Spin Double within three
 * bags", and that follow-up TSD is scripted, not forecast. Across the four sessions 179 events sit
 * behind such a triple: 175 laid the overhang in bag 1-2 and 173 executed in bag 3.
 *
 * Why a test and not a check in `forecast.ts`: a "vertical T, 3 rows, first bags" rule in the
 * metric would be a named-technique blacklist needing one entry per opener, and it would encode
 * folklore in place of the property that actually decides these — that the slot was already
 * spinnable when the overhang landed, which is what an opener IS. The metric stays ignorant of the
 * C-Spin and gets them right anyway; this asserts it keeps doing so, the same way the wiki fixtures
 * assert against an authority the engine cannot see.
 *
 * The population is pinned as well as the verdict. A refactor that stopped FINDING C-Spins would
 * otherwise leave this passing vacuously on an empty set.
 */
realData('no T-spin following a C-Spin triple is ever counted as a forecast', () => {
  const isCSpinTriple = (lk: { piece: string; cleared: number; cells: { col: number; row: number }[] }) => {
    if (lk.piece !== 'T' || lk.cleared !== 3) return false;
    const cols = lk.cells.map(c => c.col), rows = lk.cells.map(c => c.row);
    // vertical T: two columns wide, three rows tall — the shape the wiki diagrams show
    return Math.max(...cols) - Math.min(...cols) === 1 && Math.max(...rows) - Math.min(...rows) === 2;
  };
  let behindACSpin = 0, counted = 0;
  for (const c of loadCases(SESSION)) {
    const r = runCase(c, {});
    const v = verifiedIndex(r, c.truth);
    if (v < 0) continue;
    for (const rec of forecastMetric(r, true).records) {
      if (rec.lockIndex > v || rec.roofFrom === null) continue;
      let hit = false;
      for (let t = rec.roofFrom + 1; t < rec.lockIndex; t++) if (isCSpinTriple(r.locks[t]!)) hit = true;
      if (!hit) continue;
      behindACSpin++;
      if (isVerifiedForecast(rec)) counted++;
    }
  }
  expect(behindACSpin).toBe(46);
  expect(counted).toBe(0);
});

realData('the scalar gate and the garbage counterfactual now agree on every event', () => {
  // This pinned 1 for as long as the counterfactual deleted every garbage row. The event was
  // `yachi replay-2026-07-28-1 r5 lock 36`, and the row whose removal made the spin vanish is the
  // one the T tucks into, which arrived at lock 11 — 22 locks BEFORE the roof at 33. Deleting the
  // slot's own floor deletes the piece, and the collapse read as proof the garbage was holding it
  // up. The only garbage inside that window is a single row at the very bottom of the field,
  // twelve rows below the slot; deleting just that row leaves the spin intact at two lines.
  //
  // With the deletion set restricted to post-roof arrivals, no event in the corpus disagrees:
  // 121 events have such an arrival and the executed spin survives its removal in all 121. `0` is
  // therefore a much weaker assertion than the `1` it replaces — it now says only that the two
  // instruments never diverge, so the census above and the mutants are what hold the rule in place.
  expect(R!.loadBearingButNotImproved).toBe(0);
});

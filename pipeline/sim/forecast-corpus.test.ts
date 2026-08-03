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
    { 'pre-existed': 0, 'arrived-later': 0, 'field-floor': 0, undetermined: 0 };
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

realData('clause 2 is decidable for all but two of the 2026-07-28 events', () => {
  // Published so a drift in the undecidable count is visible: an implementation that quietly
  // stopped being able to answer would otherwise present as a rate that had not moved.
  expect(R!.floors).toEqual({
    'pre-existed': 83, 'field-floor': 48, 'arrived-later': 13, undetermined: 2,
  });
});

realData('the scalar improvement gate has one known blind spot, and it is one event', () => {
  // `improved` compares a single number either side of the window, so garbage that REPLACES one
  // two-line spin with another leaves it unmoved even though the executed spin depended on the
  // garbage. Here that is one event, found by the execution-time counterfactual disagreeing with
  // the gate. It is pinned rather than fixed: closing it means asking whether the EXECUTED spin
  // depended on the mechanism, not whether the best-available scalar rose.
  expect(R!.loadBearingButNotImproved).toBe(1);
});

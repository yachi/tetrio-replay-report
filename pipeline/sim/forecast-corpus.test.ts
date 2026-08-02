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
import { forecastMetric, isVerifiedForecast, type ForecastKind } from './forecast.ts';

const SESSION = `${import.meta.dir}/../../sessions/2026-07-28`;

const run = () => {
  const totals: Record<string, number> = {
    forecast_garbage: 0, forecast_lineclear: 0, self_built: 0, reactive: 0, unattributed: 0 };
  const forecasts: string[] = [];
  let loadBearingButNotImproved = 0;
  for (const c of loadCases(SESSION)) {
    const r = runCase(c, {});
    const v = verifiedIndex(r, c.truth);
    if (v < 0) continue;
    for (const rec of forecastMetric(r, true).records) {
      if (rec.lockIndex > v) continue;
      totals[rec.kind as ForecastKind]!++;
      if (rec.mechanism === 'unattributed') totals.unattributed!++;
      if (isVerifiedForecast(rec))
        forecasts.push(`${c.user} ${c.file} r${c.round} lock ${rec.lockIndex} ${rec.kind} `
          + `roof ${rec.roofFrom} ${rec.availAtRoof}->${rec.availAtSpin}`);
      // the execution-time counterfactual firing on an event the scalar gate called reactive
      if (rec.kind === 'reactive' && rec.garbageLoadBearing) loadBearingButNotImproved++;
    }
  }
  return { totals, forecasts, loadBearingButNotImproved };
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

realData('the surviving forecast is the hand-checked one, not merely a count of one', () => {
  // A count can stay at 1 while pointing at a different event entirely. This names it: the L at
  // lock 19 leaves an overhang, a full row sits between that overhang and the notch for twelve
  // pieces, the I at lock 31 completes and clears it, and the T goes in at 32.
  expect(R!.forecasts).toEqual([
    'pinglamb replay-2026-07-28-6.ttrm r5 lock 32 forecast_lineclear roof 19 0->2',
  ]);
});

realData('the scalar improvement gate has one known blind spot, and it is one event', () => {
  // `improved` compares a single number either side of the window, so garbage that REPLACES one
  // two-line spin with another leaves it unmoved even though the executed spin depended on the
  // garbage. Here that is one event, found by the execution-time counterfactual disagreeing with
  // the gate. It is pinned rather than fixed: closing it means asking whether the EXECUTED spin
  // depended on the mechanism, not whether the best-available scalar rose.
  expect(R!.loadBearingButNotImproved).toBe(1);
});

/* --- the second opinion -------------------------------------------------------------------
 * `gap-closure.ts` implements the definition as a player states it — an overhang placed above a
 * hole, the lines between them clearing — and shares no code or reasoning with the step
 * localisation in `forecast.ts`. Two instruments agreeing on one event out of 654 is worth far
 * more than either one alone, so the agreement is asserted rather than admired.
 */
import { gapClosure } from './gap-closure.ts';

const gapRun = () => {
  const hits: string[] = [];
  let closed = 0, spinOnly = 0, untraceable = 0;
  for (const c of loadCases(SESSION)) {
    const r = runCase(c, {});
    const v = verifiedIndex(r, c.truth);
    if (v < 0) continue;
    for (const rec of forecastMetric(r, true).records) {
      if (rec.lockIndex > v) continue;
      const g = gapClosure(r, rec);
      if (!g) { untraceable++; continue; }
      if (g.plainRows + g.spinRows === 0) continue;
      closed++;
      if (g.forecast) hits.push(`${c.user} ${c.file} r${c.round} lock ${rec.lockIndex}`);
      else spinOnly++;
    }
  }
  return { hits, closed, spinOnly, untraceable };
};
const G = R === null ? null : gapRun();

realData('a T-spin clear does not count as the lines between clearing', () => {
  // Without this exclusion the test fires on the C-Spin: a T-spin triple takes out three rows under
  // an overhang from the second bag, and the opener scores itself as foresight. Session-local
  // counts; corpus-wide it is 180 of 181 excluded on exactly this rule.
  expect(G!.closed).toBeGreaterThan(0);
  expect(G!.spinOnly).toBe(G!.closed - G!.hits.length);
  expect(G!.hits.length).toBeGreaterThan(0);
});

realData('the two independent instruments name the SAME single event', () => {
  expect(G!.hits).toEqual(['pinglamb replay-2026-07-28-6.ttrm r5 lock 32']);
  // and it is the one the committed metric publishes, reached by localising the mechanism instead
  expect(R!.forecasts).toEqual([
    'pinglamb replay-2026-07-28-6.ttrm r5 lock 32 forecast_lineclear roof 19 0->2',
  ]);
});

realData('the garbage-floor blind spot is measured, not merely mentioned', () => {
  // The T landing on garbage leaves no placing lock to trace, so this instrument is silent there.
  // Pinned because it is the one case the wiki documents most thoroughly and this cannot see.
  expect(G!.untraceable).toBe(2);
});

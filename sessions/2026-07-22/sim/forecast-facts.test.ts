/**
 * Guards on the emitted forecast facts artifact.
 *
 * The point of these is that the artifact must never quietly become MORE confident than the
 * evidence: it is simulator-derived, so its eligibility flag and its reasons are load-bearing
 * and are asserted here rather than left to review.
 */
import { test, expect } from 'bun:test';
import { readFileSync, existsSync } from 'node:fs';

const PATH = `${import.meta.dir}/forecast-facts.json`;

test('the artifact exists and declares itself ineligible for the report', () => {
  expect(existsSync(PATH)).toBe(true);
  const d = JSON.parse(readFileSync(PATH, 'utf8'));
  expect(d.schema).toBe('forecast-facts/1');
  // simulator-derived data must never be promoted to a report claim without the
  // dual-extractor rule being satisfied; this flag is the guard
  expect(d.report_eligible).toBe(false);
  expect(d.not_eligible_because.length).toBeGreaterThanOrEqual(3);
});

test('counts are internally consistent and integers', () => {
  const d = JSON.parse(readFileSync(PATH, 'utf8'));
  expect(d.players.length).toBe(2);
  for (const p of d.players) {
    expect(p.forecast_total).toBe(p.forecast_garbage + p.forecast_lineclear);
    expect(p.verified_tspins).toBe(p.forecast_total + p.reactive);
    expect(p.verified_placements).toBeLessThanOrEqual(p.total_placements);
    for (const k of ['forecast_rate_x1000','sampling_ci95_lo_x1000','sampling_ci95_hi_x1000'])
      expect(Number.isInteger(p[k])).toBe(true);
    // the point estimate must lie inside its own interval
    expect(p.sampling_ci95_lo_x1000).toBeLessThanOrEqual(p.forecast_rate_x1000);
    expect(p.sampling_ci95_hi_x1000).toBeGreaterThanOrEqual(p.forecast_rate_x1000);
    expect(p.sampling_ci95_lo_x1000).toBeGreaterThan(0);      // a 0% lower bound was a real past bug
    expect(p.sampling_ci95_hi_x1000).toBeLessThan(1000);
  }
});

test('simulator uncertainty is smaller than sampling uncertainty', () => {
  const d = JSON.parse(readFileSync(PATH, 'utf8'));
  for (const p of d.players) {
    const sim = p.simulator_range_hi_x1000 - p.simulator_range_lo_x1000;
    const samp = p.sampling_ci95_hi_x1000 - p.sampling_ci95_lo_x1000;
    // If this ever flips, the simulator has become the binding constraint on this number
    // and more simulator work would be worth doing. Today it is not.
    expect(sim).toBeLessThan(samp);
  }
});

test('the two players\' intervals overlap — no difference is claimed', () => {
  const d = JSON.parse(readFileSync(PATH, 'utf8'));
  const [a, b] = d.players;
  const overlap = Math.min(a.sampling_ci95_hi_x1000, b.sampling_ci95_hi_x1000)
                - Math.max(a.sampling_ci95_lo_x1000, b.sampling_ci95_lo_x1000);
  expect(overlap).toBeGreaterThan(0);
});

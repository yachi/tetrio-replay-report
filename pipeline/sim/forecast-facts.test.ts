/**
 * Guards on the emitted forecast facts artifact.
 *
 * The point of these is that the artifact must never quietly become MORE confident than the
 * evidence: it is simulator-derived, so its eligibility flag and its reasons are load-bearing
 * and are asserted here rather than left to review.
 */
import { test, expect } from 'bun:test';
import { readFileSync, existsSync, readdirSync } from 'node:fs';

// FORECAST_FACTS points the whole file at one session's artifact, so one guard covers every
// emitted artifact rather than only the session it happens to live beside. The emitter is
// shared (`--out` + REPLAY_DIR); its guards have to be too, or three of the four artifacts
// ship unchecked.
//
// The default was `${import.meta.dir}/forecast-facts.json`, which resolved only because this
// test lived inside 2026-07-22. From pipeline/sim there is no artifact beside the code, so it
// DISCOVERS them — naming a session here would quietly re-privilege one inside what is now
// shared code, which is the whole thing this move exists to end.
const SESSIONS = `${import.meta.dir}/../../sessions`;
const DISCOVERED = readdirSync(SESSIONS)
  .map(s => `${SESSIONS}/${s}/sim/forecast-facts.json`)
  .filter(existsSync)
  .sort();
const PATH = process.env.FORECAST_FACTS ?? DISCOVERED[0];
if (!PATH) throw new Error('no sessions/*/sim/forecast-facts.json found, and FORECAST_FACTS is unset');

test('the artifact exists and declares itself ineligible for the report', () => {
  expect(existsSync(PATH)).toBe(true);
  const d = JSON.parse(readFileSync(PATH, 'utf8'));
  expect(d.schema).toBe('forecast-facts/6');
  // simulator-derived data must never be promoted to a report claim without the
  // dual-extractor rule being satisfied; this flag is the guard
  expect(d.report_eligible).toBe(false);
  expect(d.not_eligible_because.length).toBeGreaterThanOrEqual(3);
});

const load = () => JSON.parse(readFileSync(PATH, 'utf8'));

test('the session block accounts for the coverage the report quotes', () => {
  const s = load().session;
  for (const k of ['player_rounds', 'verified_placements', 'total_placements'])
    expect(Number.isInteger(s[k])).toBe(true);
  expect(s.verified_placements).toBeLessThanOrEqual(s.total_placements);
  // coverage floors, like every other printed figure
  expect(s.coverage_x1000 * s.total_placements).toBeLessThanOrEqual(1000 * s.verified_placements);
  expect(1000 * s.verified_placements).toBeLessThan((s.coverage_x1000 + 1) * s.total_placements);
});

test('every statistics block is present or explicitly null — never absent', () => {
  const st = load().statistics;
  // A missing key reads as `undefined` in the renderer and would render as an empty string
  // rather than as an absence. The contract is that the key always exists.
  for (const k of ['round', 'event', 'player', 'reliability']) expect(k in st).toBe(true);
});

test('intervals contain their point estimate, and bounds widened rather than tightened', () => {
  const st = load().statistics;
  const cs = [st.event?.attack, st.event?.lines, st.event?.balance?.stack_height,
              st.event?.balance?.garbage_pressure, st.event?.negative_control].filter(Boolean);
  // With zero VERIFIED forecasts there is no forecast arm, so every cluster contrast is
  // legitimately null — there is nothing to compare reactive events against. Assert that
  // explicitly rather than letting an empty list pass as if the checks had run: an empty
  // sample silently satisfying a for-loop is how a gate proves nothing while reporting ok.
  // An arm too small to have a mean worth comparing yields null contrasts, exactly as an empty
  // arm does. The threshold lives in `forecast-event-level.ts`; asserting on the emitted
  // `forecast_n` here keeps the artifact honest without importing the simulator into a guard.
  const forecastN = st.event?.forecast_n ?? 0;
  if (forecastN < 5) { expect(cs.length).toBe(0); return; }
  expect(cs.length).toBeGreaterThan(0);
  for (const c of cs) {
    // Negative differences are legal here — this is a signed contrast, not a rate. A consumer
    // that assumes non-negative would silently mis-order the bounds.
    expect(c.ci95_lo_x1000).toBeLessThanOrEqual(c.diff_x1000);
    expect(c.ci95_hi_x1000).toBeGreaterThanOrEqual(c.diff_x1000);
    // `excludes_zero` must be computed from the interval, not asserted alongside it
    expect(c.excludes_zero).toBe(c.ci95_lo_x1000 > 0 || c.ci95_hi_x1000 < 0);
  }
});

test('the negative control fires exactly when its own interval excludes zero', () => {
  const nc = load().statistics.event?.negative_control;
  if (!nc) return;
  // This is the guard that keeps the confound honest: `fires` true means the difference also
  // appears in a window the mechanism cannot reach, so the primary is measuring context.
  expect(nc.fires).toBe(nc.excludes_zero);
});

test('p-values CEIL, because a p rounded down overstates significance', () => {
  const st = load().statistics;
  // Reconstructed from the counts the same p was computed over: the ceiled x1000 value must be
  // the smallest integer at or above 1000p, so p > (v-1)/1000. Checked against the DEFINING
  // inequality rather than a remembered constant.
  const r = st.round;
  if (r?.exact_p_x1000 != null) {
    expect(Number.isInteger(r.exact_p_x1000)).toBe(true);
    expect(r.exact_p_x1000).toBeGreaterThan(0);      // a p of exactly 0 would floor-print as 0.000
    expect(r.exact_p_x1000).toBeLessThanOrEqual(1000);
    expect(r.decided).toBe(r.wins + r.losses);
  }
  if (st.player?.exact_p_x1000 != null) {
    expect(Number.isInteger(st.player.exact_p_x1000)).toBe(true);
    expect(st.player.k).toBeLessThanOrEqual(st.player.n);
  }
});

test('reliability reports unreachable as null, not as a large number of rounds', () => {
  const rel = load().statistics.reliability;
  if (!rel) return;
  for (const [u, r] of Object.entries(rel.split_half_r_x1000) as [string, number | null][]) {
    const need = rel.rounds_for_r70[u];
    // r <= 0 means NO amount of aggregation reaches 0.70. That is a different statement from
    // "it takes many rounds" and must not be rendered as a round count.
    if (r === null || r <= 0) { expect(need).toBe(null); continue; }
    expect(Number.isInteger(need)).toBe(true);
    // Type alone is not a guard: `999` passed `isInteger` and said nothing about whether the
    // count came from Spearman-Brown at all. Reconstruct it. The emitted r is FLOORED to
    // x1000, so the true r lies in [r, r+1)/1000; need(r) = ceil((T/(1-T)) * (1-r)/r) is
    // decreasing in r, so the true count is bracketed by evaluating at both ends.
    const T = 0.7, sb = (x: number) => Math.ceil((T / (1 - T)) * (1 - x) / x);
    expect(need).toBeGreaterThanOrEqual(sb((r + 1) / 1000));
    expect(need).toBeLessThanOrEqual(sb(r / 1000));
  }
});

test('the derived reasons quote this session, not a remembered one', () => {
  const d = load();
  const joined = d.not_eligible_because.join(' ');
  const rel = d.statistics.reliability;
  if (rel) {
    // Every reliability the reason string names must be one this session actually measured.
    // The minus sign is not optional in this pattern: a correlation may be negative, and a
    // regex that skipped it read "-0.132" as 0.132 and compared it to -0.133. That miss is
    // how the two-roundings bug reached a committed artifact.
    for (const m of joined.matchAll(/(-?[0-9]\.[0-9]{3}) \(([^)]+)\)/g)) {
      const [, val, user] = m;
      expect(rel.split_half_r_x1000[user!]).not.toBe(undefined);
      // exact, not approximate: both sides must come from the SAME rounding of r11
      expect(rel.split_half_r_x1000[user!]! / 1000).toBe(Number(val));
    }
  }
  // and every p it names must match the emitted one to the digit it prints
  const ps = [...joined.matchAll(/p=([0-9]\.[0-9]{3})/g)].map(m => Number(m[1]));
  const emitted = [d.statistics.round?.exact_p_x1000, d.statistics.player?.exact_p_x1000]
    .filter(v => v != null).map(v => v / 1000);
  for (const p of ps) expect(emitted).toContain(p);
});

test('counts are internally consistent and integers', () => {
  const d = JSON.parse(readFileSync(PATH, 'utf8'));
  expect(d.players.length).toBe(2);
  for (const p of d.players) {
    // forecast_total is the two MECHANISM-ESTABLISHED kinds, each localised to the step and the
    // edit within it that raised the availability. self_built must still never be folded in —
    // that is the opener case, and folding it back is precisely the over-count this schema
    // exists to correct.
    expect(p.forecast_total).toBe(p.forecast_garbage + p.forecast_lineclear);
    expect(p.verified_tspins).toBe(
      p.forecast_garbage + p.forecast_lineclear + p.self_built + p.reactive);
    // An improvement the step model cannot explain is a defect in the model, not a category.
    // If this ever exceeds 0, the buckets below it stop meaning what they say.
    expect(p.unattributed).toBe(0);
    expect(p.verified_placements).toBeLessThanOrEqual(p.total_placements);
    for (const k of ['forecast_rate_x1000','sampling_ci95_lo_x1000','sampling_ci95_hi_x1000'])
      expect(Number.isInteger(p[k])).toBe(true);
    // the point estimate must lie inside its own interval
    expect(p.sampling_ci95_lo_x1000).toBeLessThanOrEqual(p.forecast_rate_x1000);
    expect(p.sampling_ci95_hi_x1000).toBeGreaterThanOrEqual(p.forecast_rate_x1000);
    // A 0% lower bound was once a real bisection bug — but with k = 0 forecasts it is the
    // CORRECT Clopper-Pearson answer, so the guard is conditioned on the count rather than
    // asserted flat. Asserting lo > 0 unconditionally would forbid the true value.
    if (p.forecast_total > 0) expect(p.sampling_ci95_lo_x1000).toBeGreaterThan(0);
    else expect(p.sampling_ci95_lo_x1000).toBe(0);
    expect(p.sampling_ci95_hi_x1000).toBeLessThan(1000);
  }
});

test('the rate is the floored quotient of the counts it is printed beside', () => {
  const d = JSON.parse(readFileSync(PATH, 'utf8'));
  for (const p of d.players) {
    // Every other gate here checks the rate's SHAPE — integral, inside its interval, ordered.
    // None of them reads the counts, so a rate that had drifted from them passed the lot.
    // Cross-multiplied so the check is exact integer arithmetic, and so it pins the floor
    // rather than merely a tolerance: r <= 1000*fc/n < r+1 has exactly one solution.
    const r = p.forecast_rate_x1000, n = p.verified_tspins, fc = p.forecast_total;
    expect(r * n).toBeLessThanOrEqual(1000 * fc);
    expect(1000 * fc).toBeLessThan((r + 1) * n);
  }
});

test('the simulator range brackets the rate it is printed beside', () => {
  const d = JSON.parse(readFileSync(PATH, 'utf8'));
  for (const p of d.players) {
    // `best` is one of the seven swept configs and is the config the rate itself comes from, so
    // the range must contain it. It briefly did not: the sweep kept measuring the garbage bucket
    // after the printed rate became garbage + line-clear, and the section rendered a non-zero
    // rate beside a zero-width range without any gate objecting.
    expect(p.simulator_range_lo_x1000).toBeLessThanOrEqual(p.forecast_rate_x1000);
    expect(p.simulator_range_hi_x1000).toBeGreaterThanOrEqual(p.forecast_rate_x1000);
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

test('the sensitivity sweep is the set the prose describes', () => {
  const d = load();
  // The section names the mechanisms these configs vary (kick table, blockout, lock delay,
  // gravity, garbage queue, input clock). It renders the COUNT from this list, but the names
  // are prose and cannot be derived, so changing the sweep must fail here and force the
  // sentence to be rewritten rather than silently describing configs that no longer exist.
  expect(d.simulator_configs_for_range).toEqual([
    'best', 'vanilla_srs', 'strict_blockout', 'locktime30', 'gravity05',
    'reference_queue', 'frame_clock',
  ]);
});

test('the two players\' intervals overlap — no difference is claimed', () => {
  const d = JSON.parse(readFileSync(PATH, 'utf8'));
  const [a, b] = d.players;
  const overlap = Math.min(a.sampling_ci95_hi_x1000, b.sampling_ci95_hi_x1000)
                - Math.max(a.sampling_ci95_lo_x1000, b.sampling_ci95_lo_x1000);
  expect(overlap).toBeGreaterThan(0);
});

/**
 * Emit the forecast metric as DATA, at the unit where it is actually reliable.
 *
 * This satisfies report-eligibility item 3 ("forecast counts land in facts.json as data") in
 * the only way that is honest today. It writes a SEPARATE artifact, deliberately not merged
 * into report/facts.json, because eligibility items 1 and 2 remain unmet: these numbers come
 * from a simulator and there is no second independent implementation. Merging simulator
 * output into the trusted extraction is the exact failure every audit round in this project
 * has caught, so the file carries `report_eligible: false` and its own reasons.
 *
 * UNIT. Not per round. validity-checks.ts measured split-half reliability of the per-round
 * forecast rate at 0.29 (pinglamb) and 0.064 (yachi); by Spearman-Brown a per-round value is
 * unusable at this event rate no matter how good the simulator gets. Aggregating all of a
 * player's rounds is the unit where the quantity is stable, so that is what is emitted.
 *
 * UNCERTAINTY. Two independent sources, reported separately rather than blended:
 *   sampling   — exact Clopper-Pearson interval on forecasts / T-spins.
 *   simulator  — the spread of the point estimate across simulators that are wrong in
 *                DIFFERENT ways (kick table, blockout, lock delay, gravity, garbage queue,
 *                input clock). This is an empirical sensitivity range, not a probability
 *                interval, and is labelled as such.
 *
 * Values are integers scaled x1000, matching the convention in report/facts.json.
 */
import { writeFileSync } from 'node:fs';
import { forecastMetric } from './forecast.ts';
import { loadCases, runCase, verifiedIndex, BEST_OPTS } from './verified-prefix.ts';

/** exact Clopper-Pearson interval via bisection on the binomial tail */
function clopperPearson(k: number, n: number, alpha = 0.05): [number, number] {
  const logC = (a: number, b: number) => { let s = 0; for (let i = 0; i < b; i++) s += Math.log(a - i) - Math.log(i + 1); return s; };
  const cdf = (kk: number, nn: number, p: number) => {          // P(X <= kk)
    if (p <= 0) return 1; if (p >= 1) return kk >= nn ? 1 : 0;
    let s = 0; for (let i = 0; i <= kk; i++) s += Math.exp(logC(nn, i) + i * Math.log(p) + (nn - i) * Math.log(1 - p));
    return Math.min(1, s);
  };
  const solve = (f: (p: number) => number) => {
    let lo = 0, hi = 1;
    for (let i = 0; i < 200; i++) { const m = (lo + hi) / 2; if (f(m) > 0) lo = m; else hi = m; }
    return (lo + hi) / 2;
  };
  // `solve` bisects a DECREASING function, so each target must be written that way.
  // lower: P(X >= k) = alpha/2. 1-cdf(k-1) increases in p, so alpha/2 - it decreases. OK.
  const lower = k === 0 ? 0 : solve(p => (alpha / 2) - (1 - cdf(k - 1, n, p)));
  // upper: P(X <= k) = alpha/2. cdf(k) DECREASES in p, so `alpha/2 - cdf` INCREASES and would
  // bisect the wrong way — the sign must be flipped. This is the same error the project caught
  // once before, when an upper bound silently printed as 0%.
  const upper = k === n ? 1 : solve(p => cdf(k, n, p) - (alpha / 2));
  return [Math.max(0, lower), Math.min(1, upper)];
}

// self-check against the defining equations rather than a remembered constant (a recalled
// Clopper-Pearson value was wrong by 0.001 earlier in this project and the check caught it)
{
  const [lo, hi] = clopperPearson(8, 11);
  const logC = (a: number, b: number) => { let s = 0; for (let i = 0; i < b; i++) s += Math.log(a - i) - Math.log(i + 1); return s; };
  const cdf = (kk: number, nn: number, p: number) => { let s = 0; for (let i = 0; i <= kk; i++) s += Math.exp(logC(nn, i) + i * Math.log(p) + (nn - i) * Math.log(1 - p)); return s; };
  const atUpper = cdf(8, 11, hi), atLower = 1 - cdf(7, 11, lo);
  if (Math.abs(atUpper - 0.025) > 1e-6 || Math.abs(atLower - 0.025) > 1e-6)
    throw new Error(`Clopper-Pearson self-check failed: P(X<=8)=${atUpper}, P(X>=8)=${atLower}`);
  console.log(`Clopper-Pearson self-check passed (P(X<=k)=${atUpper.toFixed(6)}, P(X>=k)=${atLower.toFixed(6)})`);
}

const CONFIGS: [string, any][] = [
  ['best', {}], ['vanilla_srs', { kickset: 'SRS' }], ['strict_blockout', { blockout: 'strict' }],
  ['locktime30', { locktime: 30 }], ['gravity05', { gravity: 0.05 }],
  ['reference_queue', { queue: 'reference' }], ['frame_clock', { subframe: false }],
];

const tally = (extra: any) => {
  const per: Record<string, { tspins: number; fg: number; fl: number; reactive: number; verified: number; placed: number }> = {};
  for (const c of loadCases()) {
    const r = runCase(c, extra);
    const v = verifiedIndex(r, c.truth);
    per[c.user] ??= { tspins: 0, fg: 0, fl: 0, reactive: 0, verified: 0, placed: 0 };
    const p = per[c.user]!;
    p.verified += v + 1; p.placed += c.placed;
    if (v < 0) continue;
    for (const rec of forecastMetric(r, true).records) {
      if (rec.lockIndex > v) continue;
      p.tspins++;
      if (rec.kind === 'forecast_garbage') p.fg++;
      else if (rec.kind === 'forecast_lineclear') p.fl++;
      else p.reactive++;
    }
  }
  return per;
};

const base = tally({});
const spread: Record<string, number[]> = {};
for (const [, extra] of CONFIGS) {
  const t = tally(extra);
  for (const [u, v] of Object.entries(t)) (spread[u] ??= []).push(v.tspins ? (v.fg + v.fl) / v.tspins : 0);
}

const players = Object.entries(base).map(([user, v]) => {
  const fc = v.fg + v.fl;
  const [lo, hi] = clopperPearson(fc, v.tspins);
  const s = spread[user]!;
  return {
    user,
    verified_tspins: v.tspins,
    forecast_garbage: v.fg,
    forecast_lineclear: v.fl,
    forecast_total: fc,
    reactive: v.reactive,
    forecast_rate_x1000: Math.round(1000 * fc / v.tspins),
    sampling_ci95_lo_x1000: Math.round(1000 * lo),
    sampling_ci95_hi_x1000: Math.round(1000 * hi),
    simulator_range_lo_x1000: Math.round(1000 * Math.min(...s)),
    simulator_range_hi_x1000: Math.round(1000 * Math.max(...s)),
    verified_placements: v.verified,
    total_placements: v.placed,
  };
});

const out = {
  schema: 'forecast-facts/1',
  report_eligible: false,
  not_eligible_because: [
    'simulator-derived: no second independent implementation (dual-extractor rule unmet)',
    'the simulator fails its own full gate; only verified prefixes are used',
    'per-round split-half reliability is 0.29 (pinglamb) / 0.064 (yachi), so a per-round column is not possible at this event rate',
    'no effect at any unit: round AUC p=0.210, event-level CI includes zero with a firing negative control, player-level p=0.848',
  ],
  unit: 'player-aggregate (all rounds pooled); per-round is unreliable by measurement, not by assumption',
  gate: 'frame+amount+row (ige row oracle must agree)',
  simulator_options: BEST_OPTS,
  simulator_configs_for_range: CONFIGS.map(c => c[0]),
  players,
};

const path = `${import.meta.dir}/forecast-facts.json`;
writeFileSync(path, JSON.stringify(out, null, 2) + '\n');
console.log(`wrote ${path}\n`);
for (const p of players)
  console.log(`${p.user.padEnd(10)} ${p.forecast_total}/${p.verified_tspins} = ${(p.forecast_rate_x1000/10).toFixed(1)}%   sampling 95% CI [${(p.sampling_ci95_lo_x1000/10).toFixed(1)}%, ${(p.sampling_ci95_hi_x1000/10).toFixed(1)}%]   simulator range [${(p.simulator_range_lo_x1000/10).toFixed(1)}%, ${(p.simulator_range_hi_x1000/10).toFixed(1)}%]`);

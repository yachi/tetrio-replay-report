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
 *
 * SCHEMA 2 adds `session` and `statistics`. Schema 1 emitted only the per-player table, so
 * every OTHER figure the report prints — the round AUC and its p, the event-level difference
 * and its CI, the negative control, the player-level p, the split-half reliabilities — existed
 * only as a printer's stdout and had been typed into pipeline/forecast_section.py as literals.
 * That module renders for every session, so 2026-07-22's numbers would have been published as
 * another session's. Everything the prose says is now emitted here and read from here.
 *
 * `not_eligible_because` is DERIVED from `statistics` for the same reason: it used to state
 * this session's reliabilities and p-values as prose, which is a hardcoded figure wearing a
 * different hat.
 *
 * Every statistics block is nullable. `null` means the quantity could not be computed on this
 * session's data, and the renderer must print an absence — never a 0. A fabricated 0 reads as
 * "measured, and the effect is exactly nothing", which is a finding this data cannot support.
 */
import { writeFileSync } from 'node:fs';
import { forecastMetric } from './forecast.ts';
import { loadCases, runCase, verifiedIndex, BEST_OPTS } from './verified-prefix.ts';
import { collectRows, pairsFor, auc, exactSignP } from './pairs.ts';
import { eventLevel } from './forecast-event-level.ts';
import { validityChecks } from './validity-checks.ts';

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
    // Gated floor convention (`pipeline/fmt.py`): every printed figure in this repo floors, so
    // 約 means "at least this much" and the rendered percent can be read as a lower bound.
    // Rounding broke that here — 14/115 = 121.739 emitted as 122 and the report printed 12.2%.
    // UPPER bounds are the one exception and must CEIL, exactly as `_bound_dp` does: flooring a
    // bound prints an interval tighter than the one that was computed, i.e. a figure stronger
    // than its own evidence. So each interval below can only ever widen, never tighten.
    forecast_rate_x1000: Math.floor(1000 * fc / v.tspins),
    sampling_ci95_lo_x1000: Math.floor(1000 * lo),
    sampling_ci95_hi_x1000: Math.ceil(1000 * hi),
    simulator_range_lo_x1000: Math.floor(1000 * Math.min(...s)),
    simulator_range_hi_x1000: Math.ceil(1000 * Math.max(...s)),
    verified_placements: v.verified,
    total_placements: v.placed,
  };
});

// --- scaling to the x1000 integers, in the direction each kind of figure must round --------
// Point estimates FLOOR, so 約 reads as "at least this much". Interval LOWER bounds floor and
// UPPER bounds ceil, so an interval can only ever widen. P-VALUES CEIL: a p rounded DOWN
// overstates significance, which is the one place where flooring is the unsafe direction.
const pt   = (v: number | null | undefined) => v == null || !Number.isFinite(v) ? null : Math.floor(1000 * v);
const blo  = (v: number | null | undefined) => v == null || !Number.isFinite(v) ? null : Math.floor(1000 * v);
const bhi  = (v: number | null | undefined) => v == null || !Number.isFinite(v) ? null : Math.ceil(1000 * v);
const pval = (v: number | null | undefined) => v == null || !Number.isFinite(v) ? null : Math.ceil(1000 * v);

// --- the round-level probe: does forecast rate predict who won the round? ------------------
const roundRows = collectRows(true);
const roundPairs = pairsFor(roundRows, 'forecast rate');
const roundStat = (() => {
  if (!roundPairs.length) return null;
  const a = auc(roundPairs);
  const p = exactSignP(a.wins, a.losses);
  return { metric: 'forecast rate', auc_x1000: pt(a.auc / 100), wins: a.wins, losses: a.losses,
           ties: a.ties, decided: a.wins + a.losses, exact_p_x1000: pval(p) };
})();

// --- the event-level estimand, its covariate balance and its negative control ---------------
const ev = eventLevel();
const clusterOut = (c: ReturnType<typeof eventLevel>['attack']) => c && ({
  forecast_mean_x1000: pt(c.forecastMean), reactive_mean_x1000: pt(c.reactiveMean),
  diff_x1000: pt(c.diff), ci95_lo_x1000: blo(c.ciLo), ci95_hi_x1000: bhi(c.ciHi),
  // computed from the interval, never asserted by the caller
  excludes_zero: c.excludesZero,
});
const eventStat = ev.events.length ? {
  forecast_n: ev.forecastN, reactive_n: ev.reactiveN,
  attack: clusterOut(ev.attack) ?? null,
  lines: clusterOut(ev.lines) ?? null,
  balance: { stack_height: clusterOut(ev.balance.stackHeight) ?? null,
             garbage_pressure: clusterOut(ev.balance.garbagePressure) ?? null },
  // `fires` true means the difference also appears where the mechanism cannot act, so the
  // primary estimate is measuring context rather than forecasting.
  negative_control: ev.negativeControl
    ? { ...clusterOut(ev.negativeControl)!, fires: ev.negativeControl.excludesZero } : null,
} : null;

// --- the player-level rate against the exposure split --------------------------------------
const playerStat = ev.exposureTest
  ? { user: ev.exposureTest.user, k: ev.exposureTest.k, n: ev.exposureTest.n,
      expected_x1000: pt(ev.exposureTest.expected), exact_p_x1000: pval(ev.exposureTest.p) }
  : null;

// --- can the per-round value correlate with ITSELF? ----------------------------------------
const vc = validityChecks();
const reliability = vc.splitHalf.length ? {
  split_half_r_x1000: Object.fromEntries(vc.splitHalf.map(s => [s.user, pt(s.r11)])),
  scorable_rounds:    Object.fromEntries(vc.splitHalf.map(s => [s.user, s.scorableRounds])),
  // null where r11 <= 0: no amount of aggregation reaches the target, which is a different
  // statement from "it takes many rounds" and must not render as a number.
  rounds_for_r70:     Object.fromEntries(vc.splitHalf.map(s => [s.user, s.roundsForReliability70])),
} : null;

const session = {
  player_rounds: vc.rows.length,
  verified_placements: players.reduce((a, p) => a + p.verified_placements, 0),
  total_placements: players.reduce((a, p) => a + p.total_placements, 0),
  coverage_x1000: (() => {
    const t = players.reduce((a, p) => a + p.total_placements, 0);
    return t ? Math.floor(1000 * players.reduce((a, p) => a + p.verified_placements, 0) / t) : null;
  })(),
};

/**
 * The reasons this artifact is not report-eligible, BUILT FROM the statistics above.
 *
 * Two of them are properties of the method and hold for any session. The rest quote this
 * session's own numbers, and used to be prose literals describing 2026-07-22 — which is how a
 * shared renderer came to state one session's reliabilities as every session's.
 */
function notEligibleBecause(): string[] {
  const why = [
    'simulator-derived: no second independent implementation (dual-extractor rule unmet)',
    'the simulator fails its own full gate; only verified prefixes are used',
  ];
  // Read the ALREADY-SCALED value, never r11 itself. Formatting the raw float here rounded
  // where `pt` floors, so 2026-07-24's pinglamb reliability appeared as -0.132 in this string
  // and -0.133 in the statistics block — one artifact stating one quantity two ways. Rounding
  // a figure twice, by two rules, is the defect this whole schema exists to remove.
  const rs = reliability?.split_half_r_x1000 ?? {};
  const weak = Object.entries(rs).filter(([, v]) => v !== null && v < 700) as [string, number][];
  if (weak.length)
    why.push(`per-round split-half reliability is ${weak.map(([u, v]) => `${(v / 1000).toFixed(3)} (${u})`).join(' / ')}` +
             `, so a per-round column is not possible at this event rate`);
  const noEffect: string[] = [];
  if (roundStat?.exact_p_x1000 != null)
    noEffect.push(`round AUC p=${(roundStat.exact_p_x1000 / 1000).toFixed(3)}`);
  if (eventStat?.attack)
    noEffect.push(eventStat.attack.excludes_zero
      ? `event-level CI excludes zero`
      : `event-level CI includes zero` +
        (eventStat.negative_control?.fires ? ' with a firing negative control' : ''));
  if (playerStat?.exact_p_x1000 != null)
    noEffect.push(`player-level p=${(playerStat.exact_p_x1000 / 1000).toFixed(3)}`);
  if (noEffect.length) why.push(`no effect at any unit: ${noEffect.join(', ')}`);
  return why;
}

const out = {
  schema: 'forecast-facts/2',
  report_eligible: false,
  not_eligible_because: notEligibleBecause(),
  unit: 'player-aggregate (all rounds pooled); per-round is unreliable by measurement, not by assumption',
  gate: 'frame+amount+row (ige row oracle must agree)',
  simulator_options: BEST_OPTS,
  simulator_configs_for_range: CONFIGS.map(c => c[0]),
  players,
  session,
  statistics: { round: roundStat, event: eventStat, player: playerStat, reliability },
};

// `--out <path>` is REQUIRED, and the replay directory comes from REPLAY_DIR via replayDir().
// The default used to be `${import.meta.dir}/forecast-facts.json`, which was only ever right
// because the emitter lived inside 2026-07-22. From pipeline/sim that default would write the
// artifact next to the CODE, where no session would read it and where the .gitignore pattern
// does not reach — so a run with the wrong arguments would look like it succeeded. There is no
// session this emitter belongs to any more, so it must be told.
const argv = process.argv.slice(2);
const oi = argv.indexOf('--out');
if (oi === -1 || !argv[oi + 1])
  throw new Error('--out <path> is required, e.g.\n'
    + '  REPLAY_DIR=sessions/2026-07-22 bun pipeline/sim/emit-forecast-facts.ts \\\n'
    + '    --out sessions/2026-07-22/sim/forecast-facts.json');
const path = argv[oi + 1]!;
writeFileSync(path, JSON.stringify(out, null, 2) + '\n');
console.log(`wrote ${path}\n`);
for (const p of players)
  console.log(`${p.user.padEnd(10)} ${p.forecast_total}/${p.verified_tspins} = ${(p.forecast_rate_x1000/10).toFixed(1)}%   sampling 95% CI [${(p.sampling_ci95_lo_x1000/10).toFixed(1)}%, ${(p.sampling_ci95_hi_x1000/10).toFixed(1)}%]   simulator range [${(p.simulator_range_lo_x1000/10).toFixed(1)}%, ${(p.simulator_range_hi_x1000/10).toFixed(1)}%]`);
console.log(`\nnot report-eligible because:`);
for (const w of out.not_eligible_because) console.log(`  - ${w}`);

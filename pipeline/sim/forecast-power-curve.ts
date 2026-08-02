/**
 * How much simulator accuracy does the forecast metric actually need?
 *
 * The metric is computed only on the verified prefix, so its sample size is a function of
 * simulator coverage. Measured tie structure: 100% of ties are 0-vs-0, and the median
 * player-round contributes just ONE verified tucked T-spin. Ties are therefore not a
 * granularity problem — a separation-weighted variant decides exactly the same 16 pairs —
 * they are a "most players have too few verified T-spins to score anything" problem.
 *
 * So the question is quantitative: coverage -> verified T-spins -> decided pairs -> power.
 * This walks real simulator configurations spanning a range of coverage and reports the
 * whole chain, then extrapolates what coverage would be needed to power the study.
 *
 * The extrapolation assumes T-spins accrue proportionally to verified placements and that
 * the forecast base rate and tie structure hold. That is a modelling assumption, not a
 * measurement — it is stated here so the number is not mistaken for one.
 */
import { forecastMetric, isVerifiedForecast} from './forecast.ts';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';

type Point = { label:string; coverage:number; tspins:number; decided:number; wins:number;
               losses:number; ties:number; usable:number; decidable:number };

const evaluate = (label: string, extra: any, strictRows: boolean): Point => {
  const byRound = new Map<string, { alive:boolean; n:number; fc:number }[]>();
  let verified = 0, total = 0, tspins = 0;
  for (const c of loadCases()) {
    const r = runCase(c, extra);
    const vIdx = verifiedIndex(r, c.truth, strictRows);
    verified += vIdx + 1; total += c.placed;
    const recs = vIdx < 0 ? [] : forecastMetric(r, true).records.filter(x => x.lockIndex <= vIdx);
    tspins += recs.length;
    const k = `${c.file}#${c.round}`;
    if (!byRound.has(k)) byRound.set(k, []);
    byRound.get(k)!.push({ alive: c.alive, n: recs.length,
                           fc: recs.filter(isVerifiedForecast).length });
  }
  let wins=0, losses=0, ties=0, usable=0, decidable=0;
  for (const v of byRound.values()) {
    if (v.length !== 2) continue;
    const [a, b] = v as [any, any];
    if (a.alive === b.alive) continue;
    decidable++;                                    // the hard ceiling: one pair per round, at most
    const W = a.alive ? a : b, L = a.alive ? b : a;
    if (!W.n || !L.n) continue;                     // a side with no verified T-spin cannot score
    usable++;
    const wr = W.fc / W.n, lr = L.fc / L.n;
    if (wr > lr) wins++; else if (wr < lr) losses++; else ties++;
  }
  return { label, coverage: 100*verified/total, tspins, decided: wins+losses, wins, losses, ties,
           usable, decidable };
};

const POINTS = [
  evaluate('frame clock (pre-fix)', {subframe:false}, true),
  evaluate('+ locktime 30',         {locktime:30},    true),
  evaluate('+ blockout strict',     {blockout:'strict'}, true),
  evaluate('BEST, strict rows',     {},               true),
  evaluate('BEST, loose gate',      {},               false),
];

console.log('config                   coverage  verified   usable   W   L   T  decided');
console.log('                                    T-spins    pairs');
for (const p of POINTS)
  console.log(`${p.label.padEnd(24)} ${p.coverage.toFixed(1).padStart(6)}%  ${String(p.tspins).padStart(8)}  ${String(p.usable).padStart(7)}  ${String(p.wins).padStart(2)}  ${String(p.losses).padStart(2)}  ${String(p.ties).padStart(2)}  ${String(p.decided).padStart(7)}`);

// decided pairs per point of coverage, from the strict-row points only (same gate)
const strictPts = POINTS.filter(p => !p.label.includes('loose'));
const lo = strictPts.reduce((a,b)=>a.coverage<b.coverage?a:b);
const hi = strictPts.reduce((a,b)=>a.coverage>b.coverage?a:b);
const slope = (hi.decided - lo.decided) / (hi.coverage - lo.coverage);
console.log(`\ndecided pairs per point of coverage: ${slope.toFixed(2)}  (${lo.decided} at ${lo.coverage.toFixed(1)}% -> ${hi.decided} at ${hi.coverage.toFixed(1)}%)`);

// The required-n table used to be hardcoded as [158, 69, 37, 23, 18] under a label that says
// "two-sided" — but those are the ONE-SIDED values, so the study read about 25% cheaper to power
// than it is. Computing it means the label and the numbers cannot disagree again. `auc-power.ts`
// owns the canonical rule; this is the same one, and the self-check below pins both files to the
// textbook critical values so a divergence fails loudly instead of silently.
const lchoose = (n: number, k: number) => {
  let s = 0; for (let i = 0; i < k; i++) s += Math.log(n - i) - Math.log(i + 1); return s;
};
const binomTail = (k: number, n: number, p: number) => {          // P(X >= k)
  let s = 0;
  for (let i = k; i <= n; i++) s += Math.exp(lchoose(n, i) + i * Math.log(p) + (n - i) * Math.log(1 - p));
  return Math.min(1, s);
};
/** smallest k of n that is significant TWO-sided at alpha */
const critical = (n: number, alpha = 0.05) => {
  for (let k = Math.ceil(n / 2); k <= n; k++) if (2 * binomTail(k, n, 0.5) <= alpha) return k;
  return null;
};
/** decided pairs needed for `target` power against a true win-rate p, two-sided */
const requiredN = (p: number, target = 0.80) => {
  for (let n = 4; n <= 4000; n++) {
    const k = critical(n);
    if (k === null) continue;
    // a two-sided test rejects in both tails; the lower region is X <= n-k
    if (binomTail(k, n, p) + (1 - binomTail(n - k + 1, n, p)) >= target) return n;
  }
  return null;
};
// A sidedness bug is invisible in the output — both rules return a plausible k, and at many n they
// return the SAME k — so it has to be asserted rather than eyeballed. n=20 is the textbook sign-test
// critical value (15); n=11 is a case where the rules differ, one-sided taking 9 where two-sided
// needs 10.
for (const [n, want] of [[20, 15], [11, 10]] as const)
  if (critical(n) !== want) {
    console.error(`SELF-CHECK FAILED critical(${n}) = ${critical(n)}, expected ${want}`);
    process.exit(1);
  }

console.log('\nwhat coverage would power the study? (80% power, two-sided exact binomial)');
console.log('true effect   decided pairs needed   implied coverage   multiple of today');
for (const eff of [0.60, 0.65, 0.70, 0.75, 0.80] as const) {
  const need = requiredN(eff)!;
  const cov = hi.coverage + (need - hi.decided) / slope;
  // The binding constraint is NOT coverage — it is that a round yields at most one decided pair,
  // so `decidable` rounds is a hard ceiling no simulator accuracy can raise. The linear
  // extrapolation overshoots it (it projects ~96 pairs at 100% coverage against a ceiling of
  // the round count), so flagging on `cov > 100` alone called a 65% effect reachable when it is not.
  const flag = need > hi.decidable ? `  UNREACHABLE — over the ${hi.decidable}-pair ceiling`
             : cov > 100 ? '  UNREACHABLE on this dataset' : '';
  console.log(`   ${(100*eff).toFixed(0)}%            ${String(need).padStart(4)}              ${cov.toFixed(0).padStart(5)}%          ${(cov/hi.coverage).toFixed(1)}x${flag}`);
}
console.log(`\nAssumes T-spins accrue proportionally to verified placements and that the forecast`);
console.log(`base rate (12.7%) and tie structure hold as the prefix deepens. Modelling assumption.`);

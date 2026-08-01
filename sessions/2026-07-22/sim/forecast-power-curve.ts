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
import { forecastMetric } from './forecast.ts';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';

type Point = { label:string; coverage:number; tspins:number; decided:number; wins:number;
               losses:number; ties:number; usable:number };

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
                           fc: recs.filter(x => x.kind !== 'reactive').length });
  }
  let wins=0, losses=0, ties=0, usable=0;
  for (const v of byRound.values()) {
    if (v.length !== 2) continue;
    const [a, b] = v as [any, any];
    if (a.alive === b.alive) continue;
    const W = a.alive ? a : b, L = a.alive ? b : a;
    if (!W.n || !L.n) continue;                     // a side with no verified T-spin cannot score
    usable++;
    const wr = W.fc / W.n, lr = L.fc / L.n;
    if (wr > lr) wins++; else if (wr < lr) losses++; else ties++;
  }
  return { label, coverage: 100*verified/total, tspins, decided: wins+losses, wins, losses, ties, usable };
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

console.log('\nwhat coverage would power the study? (80% power, two-sided exact binomial)');
console.log('true effect   decided pairs needed   implied coverage   multiple of today');
for (const [eff, need] of [[0.60,158],[0.65,69],[0.70,37],[0.75,23],[0.80,18]] as const) {
  const cov = hi.coverage + (need - hi.decided) / slope;
  const flag = cov > 100 ? '  UNREACHABLE on this dataset' : '';
  console.log(`   ${(100*eff).toFixed(0)}%            ${String(need).padStart(4)}              ${cov.toFixed(0).padStart(5)}%          ${(cov/hi.coverage).toFixed(1)}x${flag}`);
}
console.log(`\nAssumes T-spins accrue proportionally to verified placements and that the forecast`);
console.log(`base rate (12.7%) and tie structure hold as the prefix deepens. Modelling assumption.`);

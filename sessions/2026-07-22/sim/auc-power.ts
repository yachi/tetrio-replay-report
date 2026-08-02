/**
 * Is the forecast metric's "negative result" statistically licensed, or merely underpowered?
 *
 * forecast-metric.md concluded "no signal" from an AUC resting on ~12 decided pairs. That is
 * a dozen decided comparisons. This asks the question the AUC number cannot answer on its own:
 *
 *   1. What is the confidence interval on that AUC?
 *   2. What effect size could this design have detected at all? (minimum detectable effect)
 *   3. Is it distinguishable from TSD's 60.9%, the benchmark it is being filed alongside?
 *
 * "No signal" and "no power to see a signal" are different claims. Only one of them is about
 * the metric.
 */
import { collectRows, pairsFor, auc, METRICS, type Metric } from './pairs.ts';

// ---- exact binomial helpers (small n, so no normal approximation anywhere) ----
const lgamma = (z: number): number => {   // Lanczos
  const g = [676.5203681218851, -1259.1392167224028, 771.32342877765313, -176.61502916214059,
             12.507343278686905, -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7];
  if (z < 0.5) return Math.log(Math.PI / Math.sin(Math.PI * z)) - lgamma(1 - z);
  z -= 1; let x = 0.99999999999980993;
  for (let i = 0; i < g.length; i++) x += g[i]! / (z + i + 1);
  const t = z + g.length - 0.5;
  return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x);
};
const logC = (n: number, k: number) => lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1);
const binomPmf = (k: number, n: number, p: number) =>
  p === 0 ? (k === 0 ? 1 : 0) : p === 1 ? (k === n ? 1 : 0)
  : Math.exp(logC(n, k) + k * Math.log(p) + (n - k) * Math.log(1 - p));
const binomTail = (k: number, n: number, p: number) => {   // P(X >= k)
  let s = 0; for (let i = k; i <= n; i++) s += binomPmf(i, n, p); return s;
};

/** Clopper-Pearson exact interval, by bisection on the tail probabilities. */
function clopperPearson(k: number, n: number, alpha = 0.05): [number, number] {
  if (n === 0) return [0, 1];
  const solve = (f: (p: number) => number) => {
    let lo = 0, hi = 1;
    for (let i = 0; i < 200; i++) { const m = (lo + hi) / 2; if (f(m) > 0) hi = m; else lo = m; }
    return (lo + hi) / 2;
  };
  // P(X>=k) rises with p, so the lower bound solves an increasing function directly.
  // P(X<=k) FALLS with p, so the upper bound must be negated before the same bisection applies —
  // feeding it in raw returns the left edge of the bracket and prints an upper bound of 0.
  const lower = k === 0 ? 0 : solve(p => binomTail(k, n, p) - alpha / 2);
  const upper = k === n ? 1 : solve(p => alpha / 2 - (1 - binomTail(k + 1, n, p)));
  return [lower, upper];
}

/**
 * Smallest k of n that reaches TWO-sided significance, and the win-rate it implies.
 *
 * Two-sided because the `exact p` column printed beside it is two-sided (`2 * min(tail, tail)`),
 * and a required-n read off a one-sided rule quoted next to a two-sided p understates what the
 * test being reported actually needs — by about 25% here (a true 60% effect wants 199 decided
 * pairs, not 158). The direction was never argued for; the metric has no prior reason to be
 * one-tailed, and every p-value in this file assumes it is not.
 */
function minDetectable(n: number, alpha = 0.05) {
  for (let k = Math.ceil(n / 2); k <= n; k++) if (2 * binomTail(k, n, 0.5) <= alpha) return { k, rate: k / n };
  return null;
}

/** Power to detect a true per-pair win probability p, at n decided pairs. */
function power(n: number, p: number, alpha = 0.05) {
  const md = minDetectable(n, alpha);
  if (!md) return 0;
  // A two-sided test rejects in BOTH tails, and by the null's symmetry the other region is
  // X <= n-k. It contributes ~1e-9 at the effects asked about here, but dropping it would make
  // this the one-sided power of a two-sided rule — the exact mismatch fixed just above.
  return binomTail(md.k, n, p) + (1 - binomTail(n - md.k + 1, n, p));
}

// ---- self-check: these are textbook Clopper-Pearson / binomial values, not this code's output.
// A stats helper that is merely plausible is how the first version printed an upper bound of 0.
const near = (a: number, b: number, tol: number, what: string) => {
  if (Math.abs(a - b) > tol) { console.error(`SELF-CHECK FAILED ${what}: got ${a}, expected ~${b}`); process.exit(1); }
};
{
  const [l0, u0] = clopperPearson(0, 10); near(l0, 0, 1e-9, 'CP(0,10) lower'); near(u0, 0.30850, 1e-4, 'CP(0,10) upper');
  const [l1, u1] = clopperPearson(10, 10); near(l1, 0.69150, 1e-4, 'CP(10,10) lower'); near(u1, 1, 1e-9, 'CP(10,10) upper');
  // The upper bound is pinned by its DEFINING equation, P(X<=k | n, p) = alpha/2, checked below —
  // not by a remembered table value. A recalled 0.94077 was wrong here and failed this check.
  const [l2, u2] = clopperPearson(8, 11); near(l2, 0.39027, 1e-4, 'CP(8,11) lower'); near(u2, 0.9397823, 1e-6, 'CP(8,11) upper');
  {
    let cdf = 0; for (let i = 0; i <= 8; i++) cdf += binomPmf(i, 11, u2);
    near(cdf, 0.025, 1e-7, 'CP upper satisfies P(X<=k)=alpha/2');
    let cdfL = 0; for (let i = 8; i <= 11; i++) cdfL += binomPmf(i, 11, l2);
    near(cdfL, 0.025, 1e-7, 'CP lower satisfies P(X>=k)=alpha/2');
  }
  near(binomTail(8, 11, 0.5), 232 / 2048, 1e-12, 'P(X>=8|n=11,p=.5)');   // C(11,8..11)=232
  near(binomPmf(5, 10, 0.5), 252 / 1024, 1e-12, 'binom pmf(5,10,.5)');
  // minDetectable is two-sided, and a sidedness bug does not announce itself in the output: both
  // rules return a plausible k, and for many n they return the SAME one. n=20 is the textbook
  // sign-test critical value (15, i.e. reject on x>=15 or x<=5) and is one of those; n=11 is a
  // case that discriminates, one-sided taking 9 (P(X>=9)=0.0327) where two-sided needs 10
  // (2*0.0327 = 0.065 > 0.05). Both are needed — the anchor alone would not have caught this.
  near(minDetectable(20)!.k, 15, 0, 'two-sided critical k at n=20');
  near(minDetectable(11)!.k, 10, 0, 'two-sided critical k at n=11');
  // and, over every n the tables below can ask for, k against its DEFINING property rather than
  // against a table: smallest k with 2*P(X>=k) <= alpha. Both halves are needed — significance
  // alone is satisfied by k=n, minimality alone by any k that never reaches significance.
  for (let n = 5; n <= 4000; n++) {
    const md = minDetectable(n);
    if (!md) continue;
    if (2 * binomTail(md.k, n, 0.5) > 0.05)
      { console.error(`SELF-CHECK FAILED minDetectable(${n}): k=${md.k} is not significant`); process.exit(1); }
    if (md.k > Math.ceil(n / 2) && 2 * binomTail(md.k - 1, n, 0.5) <= 0.05)
      { console.error(`SELF-CHECK FAILED minDetectable(${n}): k=${md.k} is not minimal`); process.exit(1); }
  }
  console.log('stats self-check passed (CP intervals, binomial tails and the two-sided critical k)\n');
}

const STRICT = process.env.LOOSE !== '1';
console.log(`rule: ${STRICT ? 'STRICT' : 'LOOSE'}\n`);
const rows = collectRows(STRICT);
console.log(`rounds with a decided winner and verified data on both sides: ${rows.length}\n`);

console.log('metric                 AUC     W   L    T   decided   exact p   95% CI on win-rate');
console.log('-'.repeat(88));
const summary: Record<string, { dec: number; wins: number }> = {};
for (const m of METRICS) {
  const P = pairsFor(rows, m as Metric);
  const a = auc(P);
  const dec = a.wins + a.losses;
  const p = dec ? 2 * Math.min(binomTail(a.wins, dec, 0.5), binomTail(a.losses, dec, 0.5)) : NaN;
  const [lo, hi] = clopperPearson(a.wins, dec);
  summary[m] = { dec, wins: a.wins };
  console.log(`${m.padEnd(20)} ${a.auc.toFixed(1).padStart(5)}%  ${String(a.wins).padStart(2)}  ${String(a.losses).padStart(2)}  ${String(a.ties).padStart(3)}   ${String(dec).padStart(5)}    ${dec ? Math.min(1, p).toFixed(3) : '  -  '}     [${(100 * lo).toFixed(0)}%, ${(100 * hi).toFixed(0)}%]`);
}

console.log('\n--- what could this design have detected? (two-sided, alpha 0.05) ---\n');
console.log('decided   min k (2-sided)    implied win-rate   power vs a TRUE 70%   vs TRUE 80%');
console.log('-'.repeat(84));
for (const m of METRICS) {
  const { dec } = summary[m]!;
  const md = minDetectable(dec);
  console.log(`${String(dec).padStart(5)}     ${md ? String(md.k).padStart(6) : '  none'}           ${md ? (100 * md.rate).toFixed(0) + '%' : '  -'}              ${(100 * power(dec, 0.70)).toFixed(0)}%              ${(100 * power(dec, 0.80)).toFixed(0)}%   [${m}]`);
}

console.log('\n--- is forecast rate distinguishable from TSD 60.9% (the "no signal" benchmark)? ---\n');
const fr = pairsFor(rows, 'forecast rate');
const a = auc(fr);
const dec = a.wins + a.losses;
const [lo, hi] = clopperPearson(a.wins, dec);
console.log(`forecast rate: ${a.wins}/${dec} decided pairs = ${(100 * a.wins / dec).toFixed(1)}% win-rate`);
console.log(`95% CI [${(100 * lo).toFixed(0)}%, ${(100 * hi).toFixed(0)}%] — width ${(100 * (hi - lo)).toFixed(0)} points.`);
console.log(`TSD's 60.9% comes from 129 rounds; this comes from ${dec} decided pairs.`);
console.log(`Those two numbers are not comparable at face value: one of them has ~${(100 * (hi - lo)).toFixed(0)} points of slack.`);

console.log('\n--- decomposing the loose -> strict "collapse" ---\n');
{
  const L = auc(pairsFor(collectRows(false), 'forecast rate'));
  const S = auc(pairsFor(collectRows(true), 'forecast rate'));
  const wrL = L.wins / (L.wins + L.losses), wrS = S.wins / (S.wins + S.losses);
  // Counterfactual: keep the LOOSE effect size, adopt the STRICT tie structure.
  const cfWins = wrL * (S.wins + S.losses);
  const cfAuc = 100 * (cfWins + 0.5 * S.ties) / S.n;
  console.log(`loose   AUC ${L.auc.toFixed(1)}%   ${L.wins}W ${L.losses}L ${L.ties}T   win-rate among decided ${(100 * wrL).toFixed(1)}%`);
  console.log(`strict  AUC ${S.auc.toFixed(1)}%   ${S.wins}W ${S.losses}L ${S.ties}T   win-rate among decided ${(100 * wrS).toFixed(1)}%`);
  console.log(`\nAUC counts a tie as half a win, so a rule that produces more ties is dragged toward 50%`);
  console.log(`regardless of its effect size. Strict ties: ${L.ties} -> ${S.ties} of ${S.n} pairs.`);
  console.log(`\ncounterfactual — loose's effect size carried onto strict's tie structure: AUC ${cfAuc.toFixed(1)}%`);
  const mech = L.auc - cfAuc, real = cfAuc - S.auc;
  console.log(`  of the ${(L.auc - S.auc).toFixed(1)}-point drop: ${mech.toFixed(1)} points is the tie mechanism (${(100 * mech / (L.auc - S.auc)).toFixed(0)}%),`);
  console.log(`  ${real.toFixed(1)} points is the effect estimate actually moving (${(100 * real / (L.auc - S.auc)).toFixed(0)}%).`);
  const [ll, lu] = clopperPearson(L.wins, L.wins + L.losses);
  const [sl, su] = clopperPearson(S.wins, S.wins + S.losses);
  console.log(`\nwin-rate CIs: loose [${(100 * ll).toFixed(0)}%, ${(100 * lu).toFixed(0)}%]  strict [${(100 * sl).toFixed(0)}%, ${(100 * su).toFixed(0)}%] — they overlap across almost their whole range,`);
  console.log(`so "the signal did not survive the correct definition" is not separable from "the correct`);
  console.log(`definition is coarser and resolves less". At this n the data cannot tell those apart.`);
}

console.log('\n--- how many decided pairs would this actually need? (two-sided, 80% power) ---\n');
{
  const need = (p: number, target: number) => {
    for (let n = 5; n <= 4000; n++) if (power(n, p) >= target) return n;
    return null;
  };
  const S = auc(pairsFor(collectRows(true), 'forecast rate'));
  const decided = S.wins + S.losses, tieRate = S.ties / S.n;
  console.log(`current: ${decided} decided pairs out of ${S.n} (tie rate ${(100 * tieRate).toFixed(0)}%)\n`);
  console.log('true effect   decided pairs for 80% power   total pairs at this tie rate   x current');
  console.log('-'.repeat(84));
  for (const p of [0.60, 0.65, 0.70, 0.75, 0.80]) {
    const n = need(p, 0.80);
    const tot = n === null ? null : Math.ceil(n / (1 - tieRate));
    console.log(`   ${(100 * p).toFixed(0)}%          ${n === null ? '  >4000' : String(n).padStart(6)}                       ${tot === null ? '   -' : String(tot).padStart(6)}                  ${tot === null ? '-' : (tot / S.n).toFixed(0) + 'x'}`);
  }
  console.log(`\nThe 2026-07-22 set yields ${S.n} usable pairs from 158 rounds, because coverage is a verified`);
  console.log(`PREFIX. More sessions alone will not fix this at the observed tie rate —`);
  console.log(`reducing ties means a finer-grained metric, or a simulator that verifies deeper into rounds.`);
}

console.log('\n--- cluster bootstrap over matches (pairs within a match are not independent) ---\n');
function rng(seed: number) { let t = seed % 2147483647; if (t <= 0) t += 2147483646;
  return () => ((t = (16807 * t) % 2147483647) - 1) / 2147483646; }
for (const m of METRICS) {
  const P = pairsFor(rows, m as Metric);
  const files = [...new Set(P.map(p => p.file))];
  const byFile = new Map(files.map(f => [f, P.filter(p => p.file === f)]));
  const r = rng(20260730);
  const draws: number[] = [];
  for (let b = 0; b < 4000; b++) {
    const samp: typeof P = [];
    for (let i = 0; i < files.length; i++) samp.push(...byFile.get(files[Math.floor(r() * files.length)]!)!);
    if (samp.length) draws.push(auc(samp).auc);
  }
  draws.sort((x, y) => x - y);
  const q = (t: number) => draws[Math.floor(t * (draws.length - 1))]!;
  console.log(`${m.padEnd(20)} AUC ${auc(P).auc.toFixed(1)}%   bootstrap 95% CI [${q(0.025).toFixed(1)}%, ${q(0.975).toFixed(1)}%]   (${files.length} matches)`);
}

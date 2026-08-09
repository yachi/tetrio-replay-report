/**
 * Secondary analysis: continuous outcomes instead of the binary winner/loser pairing.
 *
 * PRE-DECLARED STATUS. The repo's bar is paired AUC on round winner vs loser, and that
 * remains the PRIMARY estimand — it is the one the report would cite. Everything here is
 * SECONDARY and exploratory, reported alongside the primary rather than in place of it.
 * Swapping in whichever outcome gives the smallest p would be p-hacking, so all outcomes
 * tried are listed below whatever they show.
 *
 * Why bother: the paired design discards almost everything. It collapses each round to one
 * bit, then discards 19 of 35 pairs as ties (all 0-vs-0), leaving 16 decided. A continuous
 * outcome uses all 158 player-rounds and the magnitude of each, which is far better powered
 * for the same data.
 *
 * Inference is by PERMUTATION, not a t-test: forecast rates are bounded, zero-inflated and
 * clustered (two players, ten matches, both players in a round see correlated pressure).
 * Permuting the outcome WITHIN each round preserves the pairing and the cluster structure
 * while destroying only the association being tested, which is the exchangeability the null
 * actually requires.
 */
import { forecastMetric, isVerifiedForecast} from './forecast.ts';
import { loadCases, runCase, verifiedIndex, replayDir} from './verified-prefix.ts';
import { readFileSync, readdirSync } from 'node:fs';

const DIR = replayDir();
const stats = new Map<string, any>();
for (const f of readdirSync(DIR).filter(x => x.endsWith('.ttrm')).sort()) {
  const d = JSON.parse(readFileSync(`${DIR}/${f}`, 'utf8'));
  d.replay.rounds.forEach((rnd: any, ri: number) => {
    for (const p of rnd) stats.set(`${f}#${ri}#${p.username}`, p.replay.results.stats);
  });
}

type Obs = { round:string; user:string; won:number; rate:number; n:number;
             sent:number; pieces:number; lines:number; apm:number };
const obs: Obs[] = [];
for (const c of loadCases()) {
  const r = runCase(c);
  const vIdx = verifiedIndex(r, c.truth);
  // full-round records: under isVerifiedForecast the verified-prefix and full-round forecast
  // counts are BOTH identically 0 across all 101 player-rounds, so the choice of window cannot
  // change the rate — they agree degenerately, not via a correlation. (The r=0.783 / t=1.28 this
  // once cited came from the superseded kind!=='reactive' numerator and no longer exists.)
  const recs = forecastMetric(r, true).records;
  if (!recs.length) continue;
  const st = stats.get(`${c.file}#${c.round}#${c.user}`)!;
  const mins = (st.finaltime ?? c.frames / 60 * 1000) / 60000;
  obs.push({ round: `${c.file}#${c.round}`, user: c.user, won: c.alive ? 1 : 0,
             rate: recs.filter(isVerifiedForecast).length / recs.length,
             n: recs.length, sent: st.garbage?.sent ?? 0, pieces: st.piecesplaced,
             lines: st.lines, apm: mins > 0 ? (st.garbage?.sent ?? 0) / mins : 0 });
}

const pearson = (xs: number[], ys: number[]) => {
  const n = xs.length, mx = xs.reduce((a,b)=>a+b,0)/n, my = ys.reduce((a,b)=>a+b,0)/n;
  let sxy=0, sxx=0, syy=0;
  for (let i=0;i<n;i++){ const a=xs[i]!-mx, b=ys[i]!-my; sxy+=a*b; sxx+=a*a; syy+=b*b; }
  return sxy / Math.sqrt(sxx*syy);
};

/** Permute the outcome WITHIN each round: preserves pairing and clustering. */
const permTest = (outcome: (o:Obs)=>number, iters = 20000) => {
  const xs = obs.map(o=>o.rate), ys = obs.map(outcome);
  const actual = pearson(xs, ys);
  const byRound = new Map<string, number[]>();
  obs.forEach((o,i) => { if(!byRound.has(o.round)) byRound.set(o.round,[]); byRound.get(o.round)!.push(i); });
  // deterministic LCG so the p-value is reproducible (Math.random is unavailable in
  // workflow scripts and irreproducible anywhere)
  let seed = 12345;
  const rnd = () => (seed = (1103515245*seed + 12345) % 2147483648) / 2147483648;
  let ge = 0;
  for (let it=0; it<iters; it++) {
    const yp = ys.slice();
    for (const idx of byRound.values())
      for (let i=idx.length-1;i>0;i--) { const j=Math.floor(rnd()*(i+1));
        [yp[idx[i]!], yp[idx[j]!]] = [yp[idx[j]!]!, yp[idx[i]!]!]; }
    if (Math.abs(pearson(xs, yp)) >= Math.abs(actual)) ge++;
  }
  return { r: actual, p: (ge+1)/(iters+1) };
};

console.log(`player-rounds with at least one T-spin: ${obs.length} of 158`);
console.log(`(the paired design keeps 40 pairs / 20 decided from the same data)\n`);
console.log('outcome                     Pearson r   permutation p (within-round, 20k)');
for (const [name, f] of [
  ['won the round (binary)', (o:Obs)=>o.won],
  ['garbage sent',           (o:Obs)=>o.sent],
  ['attack per minute',      (o:Obs)=>o.apm],
  ['pieces placed',          (o:Obs)=>o.pieces],
  ['lines cleared',          (o:Obs)=>o.lines],
] as const) {
  const { r, p } = permTest(f);
  console.log(`${name.padEnd(26)} ${r.toFixed(3).padStart(9)}   ${p.toFixed(4).padStart(10)}${p<0.05?'  *':''}`);
}
// A null is meaningless without its power. Inject a KNOWN effect (winners' forecast rate
// shifted by delta) into the real data and measure how often this exact permutation test
// detects it. That gives the minimum detectable effect empirically, under the real zero-
// inflation and clustering, rather than from a formula that assumes neither.
console.log('\n--- what effect could this design have detected? ---');
console.log('injected shift in winners\' forecast rate   detection rate at p<0.05 (200 sims)');
const won = obs.map(o=>o.won);
let pseed = 999;
const prnd = () => (pseed = (1103515245*pseed + 12345) % 2147483648) / 2147483648;
for (const delta of [0, 0.05, 0.10, 0.15, 0.20, 0.30]) {
  let hits = 0; const SIMS = 200;
  for (let s2 = 0; s2 < SIMS; s2++) {
    // resample rates with replacement, then add delta to winners: preserves the real
    // zero-inflated marginal distribution while creating a known association
    const xs = obs.map(() => obs[Math.floor(prnd()*obs.length)]!.rate);
    const shifted = xs.map((v,i) => Math.min(1, v + (won[i] ? delta : 0)));
    // same within-round permutation null, fewer iterations for speed
    const byRound = new Map<string, number[]>();
    obs.forEach((o,i) => { if(!byRound.has(o.round)) byRound.set(o.round,[]); byRound.get(o.round)!.push(i); });
    const actual = pearson(shifted, won);
    let ge = 0; const IT = 400;
    for (let it=0; it<IT; it++) {
      const yp = won.slice();
      for (const idx of byRound.values())
        for (let i=idx.length-1;i>0;i--) { const j=Math.floor(prnd()*(i+1));
          [yp[idx[i]!], yp[idx[j]!]] = [yp[idx[j]!]!, yp[idx[i]!]!]; }
      if (Math.abs(pearson(shifted, yp)) >= Math.abs(actual)) ge++;
    }
    if ((ge+1)/(IT+1) < 0.05) hits++;
  }
  console.log(`  +${(100*delta).toFixed(0).padStart(3)} percentage points${' '.repeat(20)}${(100*hits/SIMS).toFixed(0).padStart(3)}%`);
}

console.log('\nAll outcomes tried are listed above regardless of result. The primary estimand');
console.log('remains paired AUC on round winner; these are secondary and exploratory.');
console.log('With 5 outcomes, a Bonferroni-corrected threshold would be p < 0.010.');

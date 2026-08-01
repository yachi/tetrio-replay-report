/**
 * Is the forecast metric SENSITIVE to simulator error?
 *
 * Every attempt so far has tried to make the board provably correct, capping the metric at
 * the verified prefix (17.9% of placements, 16 decided pairs). That is a VERIFICATION
 * argument. The alternative is a VALIDITY argument: if the metric's value is insensitive to
 * the simulator's errors, then computing it on unverified placements does not bias it, and
 * all 14,517 placements become usable instead of 2,595.
 *
 * That claim is falsifiable, and this is the falsification attempt. Two independent tests:
 *
 * 1. PREFIX vs FULL. For each player-round compute the forecast rate on the verified prefix
 *    and on the whole round. If the metric is insensitive, the two agree beyond chance and
 *    the paired difference is centred on zero. If the full-round value drifts, unverified
 *    placements are contaminating it and the extra data is not usable.
 *
 * 2. ACROSS PERTURBED SIMULATORS. Run configurations that are wrong in DIFFERENT ways
 *    (different kick table, blockout, lock delay, gravity, garbage queue). Each produces a
 *    different wrong board. If the per-player forecast rate — and, more importantly, the
 *    SIGN of the between-player difference — is stable across them, the metric is measuring
 *    something that survives the errors. If it flips, it is measuring the simulator.
 *
 * Test 2 is the stronger one: a metric whose player ranking flips under perturbation cannot
 * be reported no matter how many pairs it yields.
 */
import { forecastMetric } from './forecast.ts';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';

type Row = { key:string; user:string; alive:boolean; file:string; round:number;
             nPre:number; fcPre:number; nFull:number; fcFull:number };

const collect = (extra: any): Row[] => {
  const out: Row[] = [];
  for (const c of loadCases()) {
    const r = runCase(c, extra);
    const vIdx = verifiedIndex(r, c.truth);
    const all = forecastMetric(r, true).records;
    const pre = vIdx < 0 ? [] : all.filter(x => x.lockIndex <= vIdx);
    out.push({ key:`${c.file}#${c.round}#${c.user}`, user:c.user, alive:c.alive,
               file:c.file, round:c.round,
               nPre: pre.length, fcPre: pre.filter(x=>x.kind!=='reactive').length,
               nFull: all.length, fcFull: all.filter(x=>x.kind!=='reactive').length });
  }
  return out;
};

const rate = (fc:number, n:number) => n ? fc/n : null;

const aucOf = (rows: Row[], which: 'pre'|'full') => {
  const byRound = new Map<string, Row[]>();
  for (const r of rows) {
    const k = `${r.file}#${r.round}`;
    if (!byRound.has(k)) byRound.set(k, []);
    byRound.get(k)!.push(r);
  }
  let w=0,l=0,t=0,usable=0;
  for (const v of byRound.values()) {
    if (v.length !== 2) continue;
    const [a,b] = v as [Row,Row];
    if (a.alive === b.alive) continue;
    const W = a.alive ? a : b, L = a.alive ? b : a;
    const wr = which==='pre' ? rate(W.fcPre,W.nPre) : rate(W.fcFull,W.nFull);
    const lr = which==='pre' ? rate(L.fcPre,L.nPre) : rate(L.fcFull,L.nFull);
    if (wr === null || lr === null) continue;
    usable++;
    if (wr>lr) w++; else if (wr<lr) l++; else t++;
  }
  return { w, l, t, usable, decided: w+l, auc: 100*(w+0.5*t)/usable };
};

console.log('=== TEST 1: does the metric survive leaving the verified prefix? ===\n');
const base = collect({});
const paired = base.filter(r => r.nPre > 0 && r.nFull > 0)
  .map(r => ({ ...r, pre: rate(r.fcPre,r.nPre)!, full: rate(r.fcFull,r.nFull)! }));
const diffs = paired.map(r => r.full - r.pre);
const mean = diffs.reduce((a,b)=>a+b,0)/diffs.length;
const sd = Math.sqrt(diffs.reduce((a,b)=>a+(b-mean)**2,0)/(diffs.length-1));
const se = sd/Math.sqrt(diffs.length);
// Pearson correlation between the prefix value and the full-round value
const mp = paired.reduce((a,r)=>a+r.pre,0)/paired.length;
const mf = paired.reduce((a,r)=>a+r.full,0)/paired.length;
const cov = paired.reduce((a,r)=>a+(r.pre-mp)*(r.full-mf),0);
const vp = Math.sqrt(paired.reduce((a,r)=>a+(r.pre-mp)**2,0));
const vf = Math.sqrt(paired.reduce((a,r)=>a+(r.full-mf)**2,0));
console.log(`player-rounds with both a prefix and a full value: ${paired.length}`);
console.log(`  mean(full - prefix) = ${mean.toFixed(4)}  sd ${sd.toFixed(4)}  se ${se.toFixed(4)}  t = ${(mean/se).toFixed(2)}`);
console.log(`  correlation(prefix, full) = ${(cov/(vp*vf)).toFixed(3)}`);
const A = aucOf(base,'pre'), B = aucOf(base,'full');
console.log(`\n  AUC on verified prefix : ${A.auc.toFixed(1)}%  W${A.w} L${A.l} T${A.t}  decided ${A.decided}/${A.usable}`);
console.log(`  AUC on FULL rounds     : ${B.auc.toFixed(1)}%  W${B.w} L${B.l} T${B.t}  decided ${B.decided}/${B.usable}`);

console.log('\n=== TEST 2: is the metric stable across simulators that are wrong differently? ===\n');
const CONFIGS: [string, any][] = [
  ['BEST',            {}],
  ['vanilla SRS',     {kickset:'SRS'}],
  ['strict blockout', {blockout:'strict'}],
  ['locktime 30',     {locktime:30}],
  ['gravity 0.05',    {gravity:0.05}],
  ['reference queue', {queue:'reference'}],
  ['frame clock',     {subframe:false}],
];
console.log('config             prefix-AUC  decided   full-AUC  decided   yachi-full  pinglamb-full');
for (const [label, extra] of CONFIGS) {
  const rows = collect(extra);
  const p = aucOf(rows,'pre'), f = aucOf(rows,'full');
  const per = (u:string) => {
    const rs = rows.filter(r=>r.user===u);
    const fc = rs.reduce((a,r)=>a+r.fcFull,0), n = rs.reduce((a,r)=>a+r.nFull,0);
    return n ? (100*fc/n).toFixed(1)+'%' : '-';
  };
  console.log(`${label.padEnd(18)} ${p.auc.toFixed(1).padStart(9)}%  ${String(p.decided).padStart(7)}  ${f.auc.toFixed(1).padStart(8)}%  ${String(f.decided).padStart(7)}   ${per('yachi').padStart(10)}  ${per('pinglamb').padStart(13)}`);
}
console.log('\nIf the full-round AUC and the between-player sign hold across all of these, the');
console.log('metric survives the simulator being wrong in several different ways at once.');

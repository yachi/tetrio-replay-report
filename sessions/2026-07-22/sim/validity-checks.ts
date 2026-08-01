/**
 * Validity prerequisites for every verified-prefix analysis in this directory.
 *
 * CHECK A — informative missingness (MNAR).
 * The prefix ends where the simulator diverges, and divergence plausibly tracks board
 * messiness -> garbage pressure -> losing. If verified-prefix FRACTION predicts winning,
 * then conditioning on verification conditions on a variable downstream of the outcome, and
 * the reported paired AUC is SELECTION-BIASED rather than merely underpowered. That would
 * make the existing 58.6% figure wrong in kind, not just imprecise, so it is checked before
 * anything else is believed.
 *
 * CHECK B — reliability ceiling.
 * At ~1.34 verified T-spins per player-round (zero in 57/158) the per-round rate is close to
 * a single Bernoulli draw of a rare event. Split-half reliability across odd/even rounds
 * within a player bounds how large an observable round-level AUC can be, whatever the true
 * effect: a metric that cannot correlate with itself cannot correlate with winning. If
 * reliability is ~0, a per-ROUND column is impossible in principle at this event rate,
 * independent of simulator coverage — which is a different and stronger statement than
 * "not significant".
 * Spearman-Brown: r_nn = n*r11 / (1 + (n-1)*r11).
 */
import { forecastMetric } from './forecast.ts';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';

type Row = { file:string; round:number; user:string; won:number;
             frac:number; verified:number; placed:number; n:number; fc:number };
const rows: Row[] = [];
for (const c of loadCases()) {
  const r = runCase(c);
  const v = verifiedIndex(r, c.truth) + 1;
  const recs = v === 0 ? [] : forecastMetric(r, true).records.filter(x => x.lockIndex < v);
  rows.push({ file:c.file, round:c.round, user:c.user, won: c.alive ? 1 : 0,
              frac: v / c.placed, verified: v, placed: c.placed,
              n: recs.length, fc: recs.filter(x=>x.kind!=='reactive').length });
}

const pearson = (xs:number[], ys:number[]) => {
  const n=xs.length, mx=xs.reduce((a,b)=>a+b,0)/n, my=ys.reduce((a,b)=>a+b,0)/n;
  let sxy=0,sxx=0,syy=0;
  for (let i=0;i<n;i++){const a=xs[i]!-mx,b=ys[i]!-my;sxy+=a*b;sxx+=a*a;syy+=b*b;}
  return sxx&&syy ? sxy/Math.sqrt(sxx*syy) : 0;
};

console.log('=== CHECK A: is verification informative about the outcome? ===\n');
// paired within round: does the winner get a longer verified prefix than the loser?
const byRound = new Map<string, Row[]>();
for (const r of rows) { const k=`${r.file}#${r.round}`; if(!byRound.has(k)) byRound.set(k,[]); byRound.get(k)!.push(r); }
let wLonger=0, lLonger=0, tie=0;
const deltas:number[] = [];
for (const v of byRound.values()) {
  if (v.length!==2) continue;
  const [a,b]=v as [Row,Row];
  if (a.won===b.won) continue;
  const W=a.won?a:b, L=a.won?b:a;
  deltas.push(W.frac - L.frac);
  if (W.frac>L.frac) wLonger++; else if (W.frac<L.frac) lLonger++; else tie++;
}
const md = deltas.reduce((a,b)=>a+b,0)/deltas.length;
const sdd = Math.sqrt(deltas.reduce((a,b)=>a+(b-md)**2,0)/(deltas.length-1));
console.log(`winner's verified fraction vs loser's, ${deltas.length} rounds:`);
console.log(`  winner longer ${wLonger}   loser longer ${lLonger}   equal ${tie}`);
console.log(`  mean(winner - loser) = ${(100*md).toFixed(2)} pp   sd ${(100*sdd).toFixed(2)}   t = ${(md/(sdd/Math.sqrt(deltas.length))).toFixed(2)}`);
// exact two-sided sign test on the decided rounds
const nSign = wLonger + lLonger, k = Math.max(wLonger, lLonger);
const logC = (n:number,r:number)=>{let s=0;for(let i=0;i<r;i++)s+=Math.log(n-i)-Math.log(i+1);return s;};
let tail=0; for(let i=k;i<=nSign;i++) tail += Math.exp(logC(nSign,i) + nSign*Math.log(0.5));
console.log(`  exact sign test: ${k}/${nSign}, two-sided p = ${Math.min(1,2*tail).toFixed(4)}`);
console.log(`  correlation(verified fraction, won) across all ${rows.length} player-rounds = ${pearson(rows.map(r=>r.frac), rows.map(r=>r.won)).toFixed(3)}`);

console.log('\n=== CHECK B: can the per-round metric correlate with ITSELF? ===\n');
for (const user of [...new Set(rows.map(r=>r.user))]) {
  const rs = rows.filter(r=>r.user===user && r.n>0);
  const odd = rs.filter((_,i)=>i%2===1).map(r=>r.fc/r.n);
  const even = rs.filter((_,i)=>i%2===0).map(r=>r.fc/r.n);
  const m = Math.min(odd.length, even.length);
  const r11 = pearson(odd.slice(0,m), even.slice(0,m));
  const sb = (n:number) => n*r11/(1+(n-1)*r11);
  console.log(`${user}: ${rs.length} scorable rounds, split-half r = ${r11.toFixed(3)}`);
  console.log(`  Spearman-Brown: 2 rounds -> ${sb(2).toFixed(2)}   8 -> ${sb(8).toFixed(2)}   20 -> ${sb(20).toFixed(2)}   40 -> ${sb(40).toFixed(2)}`);
  const need = r11 > 0 ? Math.ceil((0.7*(1-r11))/(r11*(1-0.7))) : Infinity;
  console.log(`  rounds that must be aggregated to reach reliability 0.70: ${Number.isFinite(need)?need:'unreachable (r11 <= 0)'}`);
}
console.log('\nA per-ROUND column needs the per-round value to be reliable. If it is not, the');
console.log('honest unit is a per-PLAYER aggregate, not a per-round comparison.');

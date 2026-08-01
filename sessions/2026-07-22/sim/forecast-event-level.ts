/**
 * The estimand the data can actually support: are forecast T-spins BETTER than reactive ones?
 *
 * Why the unit changed. validity-checks.ts measured split-half reliability of the per-round
 * forecast rate at 0.29 (pinglamb) and 0.064 (yachi) — the per-round value barely correlates
 * with ITSELF. A quantity that cannot correlate with itself cannot correlate with winning, so
 * a per-ROUND column is impossible in principle at ~1.34 T-spins per round, whatever the
 * simulator coverage. That is a stronger and more useful statement than "not significant",
 * and it says the honest units are the EVENT and the PLAYER, not the round.
 *
 * Two analyses, both pre-declared here before being run:
 *
 *   PRIMARY   event-level effectiveness — do forecast T-spins send more attack than reactive
 *             ones? ~212 events (27 forecast, ~185 reactive) rather than 16 decided pairs.
 *   SECONDARY player-level rate — does one player forecast more per opportunity? Exact
 *             binomial against the exposure split, which is a DESCRIPTIVE claim about these
 *             two named players and needs no generalisation to "players in general".
 *
 * Confounding is the main threat to the primary and is handled explicitly: forecast T-spins
 * occur in garbage-active contexts BY DEFINITION, so an unadjusted difference could just be
 * measuring "garbage was falling". Reported alongside are a covariate-balance table and a
 * NEGATIVE CONTROL — attack sent in the window BEFORE the roof was built, which the forecast
 * mechanism cannot influence. A "difference" that also shows up in the negative control is
 * context, not forecasting.
 */
import { forecastMetric } from './forecast.ts';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';

type Ev = { user:string; round:string; kind:string; forecast:boolean;
            attack:number; lines:number; stackHeight:number; garbagePressure:number;
            priorAttack:number };
const evs: Ev[] = [];

for (const c of loadCases()) {
  const r = runCase(c);
  const v = verifiedIndex(r, c.truth);
  if (v < 0) continue;
  const recs = forecastMetric(r, true).records.filter(x => x.lockIndex <= v);
  for (const rec of recs) {
    const lock = r.locks[rec.lockIndex];
    if (!lock) continue;
    const sent = r.records.find(x => x.frame === lock.frame && x.lines > 0);
    const board = r.boards[rec.lockIndex] ?? [];
    let top = board.length;
    for (let y=0; y<board.length; y++) if (board[y]!.some((x:any)=>x!==null)) { top=y; break; }
    // garbage that arrived in the 120 frames before this T-spin
    const gp = c.gin.filter((g:any) => g.frame <= lock.frame && g.frame > lock.frame - 120)
      .reduce((a:number,g:any)=>a+g.amt, 0);
    // NEGATIVE CONTROL: attack sent in the 120 frames BEFORE the roof was built. The
    // forecast mechanism cannot act backwards in time, so this must show no difference.
    const roofLock = rec.roofFrom != null ? r.locks[rec.roofFrom] : null;
    const prior = roofLock
      ? r.records.filter(x => x.frame < roofLock.frame && x.frame >= roofLock.frame - 120)
          .reduce((a,x)=>a+x.sent, 0)
      : 0;
    evs.push({ user:c.user, round:`${c.file}#${c.round}`, kind:rec.kind,
               forecast: rec.kind !== 'reactive', attack: sent?.sent ?? 0,
               lines: lock.cleared, stackHeight: board.length - top,
               garbagePressure: gp, priorAttack: prior });
  }
}

const mean = (xs:number[]) => xs.reduce((a,b)=>a+b,0)/xs.length;
const sd = (xs:number[]) => { const m=mean(xs); return Math.sqrt(xs.reduce((a,b)=>a+(b-m)**2,0)/(xs.length-1)); };
const F = evs.filter(e=>e.forecast), R = evs.filter(e=>!e.forecast);

console.log(`=== PRIMARY: event-level effectiveness ===`);
console.log(`forecast T-spins ${F.length}   reactive ${R.length}   total ${evs.length}\n`);

/** cluster-robust two-sample comparison; clusters are player-rounds (events within a round
 *  share a board and are not independent) */
const clusterTest = (sel:(e:Ev)=>number, label:string) => {
  const d = mean(F.map(sel)) - mean(R.map(sel));
  const clusters = [...new Set(evs.map(e=>e.round))];
  // cluster bootstrap over player-rounds, deterministic seed for reproducibility
  let seed = 4242; const rnd = () => (seed = (1103515245*seed+12345) % 2147483648)/2147483648;
  const boot:number[] = [];
  for (let b=0;b<4000;b++) {
    const pick:Ev[] = [];
    for (let i=0;i<clusters.length;i++) {
      const cl = clusters[Math.floor(rnd()*clusters.length)]!;
      for (const e of evs) if (e.round===cl) pick.push(e);
    }
    const f=pick.filter(e=>e.forecast), r2=pick.filter(e=>!e.forecast);
    if (!f.length || !r2.length) continue;
    boot.push(mean(f.map(sel)) - mean(r2.map(sel)));
  }
  boot.sort((a,b)=>a-b);
  const lo = boot[Math.floor(boot.length*0.025)]!, hi = boot[Math.floor(boot.length*0.975)]!;
  const pooled = Math.sqrt((sd(F.map(sel))**2 + sd(R.map(sel))**2)/2);
  console.log(`${label.padEnd(22)} forecast ${mean(F.map(sel)).toFixed(2).padStart(6)}   reactive ${mean(R.map(sel)).toFixed(2).padStart(6)}   diff ${d.toFixed(2).padStart(6)}   95% CI [${lo.toFixed(2)}, ${hi.toFixed(2)}]${lo>0||hi<0?'  *':''}   d=${(d/pooled).toFixed(2)}`);
};
clusterTest(e=>e.attack, 'attack sent');
clusterTest(e=>e.lines,  'lines cleared');

console.log(`\n--- covariate balance (are the two groups comparable?) ---`);
clusterTest(e=>e.stackHeight,     'stack height');
clusterTest(e=>e.garbagePressure, 'garbage pressure');
console.log(`\n--- NEGATIVE CONTROL (must show NO difference) ---`);
clusterTest(e=>e.priorAttack, 'attack before roof');

console.log(`\n=== SECONDARY: player-level rate, exposure-adjusted ===`);
const users = [...new Set(evs.map(e=>e.user))];
const tot = evs.length, totF = F.length;
for (const u of users) {
  const n = evs.filter(e=>e.user===u).length, f = F.filter(e=>e.user===u).length;
  console.log(`  ${u.padEnd(10)} ${f} forecasts of ${n} T-spins = ${(100*f/n).toFixed(1)}%   (exposure share ${(100*n/tot).toFixed(1)}%)`);
}
// exact two-sided binomial: given totF forecasts, is the split consistent with exposure?
const u0 = users[0]!, n0 = evs.filter(e=>e.user===u0).length, k0 = F.filter(e=>e.user===u0).length;
const p0 = n0/tot;
const logC=(n:number,r:number)=>{let s=0;for(let i=0;i<r;i++)s+=Math.log(n-i)-Math.log(i+1);return s;};
const pmf=(i:number)=>Math.exp(logC(totF,i)+i*Math.log(p0)+(totF-i)*Math.log(1-p0));
const obs=pmf(k0); let p=0; for(let i=0;i<=totF;i++){const v=pmf(i); if(v<=obs*1.0000001) p+=v;}
console.log(`  exact two-sided binomial vs exposure (${k0}/${totF} to ${u0}, expected ${(p0*totF).toFixed(1)}): p = ${Math.min(1,p).toFixed(4)}`);

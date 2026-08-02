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
 *
 * Shape: every statistic is RETURNED by `eventLevel()`, and `import.meta.main` only prints.
 * The prose in pipeline/forecast_section.py is rendered for every session but had this
 * session's figures (0.52 attack, CI [-0.34, 1.28], p = 0.848) typed into it as literals, so
 * another session's section would have published 2026-07-22's numbers as its own. A statistic
 * that is only ever console.logged cannot be consumed as data, which is what made hardcoding
 * it the path of least resistance. `loadCases()` already honours REPLAY_DIR, so the functions
 * below are session-capable as they stand.
 *
 * Anything not computable on the input comes back `null`, never 0/NaN. A session where one
 * arm is empty has no difference to report, and `mean([])` is NaN while a fabricated 0 would
 * read downstream as "measured, and the two arms are equal".
 */
import { forecastMetric, isVerifiedForecast} from './forecast.ts';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';

export type Ev = { user:string; round:string; kind:string; forecast:boolean;
                   attack:number; lines:number; stackHeight:number; garbagePressure:number;
                   priorAttack:number };

/** One row per T-spin inside a verified prefix, with the covariates the balance table reads. */
export function collectEvents(): Ev[] {
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
                 forecast: isVerifiedForecast(rec), attack: sent?.sent ?? 0,
                 lines: lock.cleared, stackHeight: board.length - top,
                 garbagePressure: gp, priorAttack: prior });
    }
  }
  return evs;
}

const mean = (xs:number[]) => xs.reduce((a,b)=>a+b,0)/xs.length;
const sd = (xs:number[]) => { const m=mean(xs); return Math.sqrt(xs.reduce((a,b)=>a+(b-m)**2,0)/(xs.length-1)); };

export interface ClusterStat {
  label: string;
  forecastMean: number; reactiveMean: number; diff: number;
  /** bootstrap percentile bounds; null when no resample kept both arms */
  ciLo: number | null; ciHi: number | null;
  /** true exactly when the CI excludes zero — computed, never asserted */
  excludesZero: boolean;
  /** Cohen's d; null when the pooled sd is 0 (both arms constant) */
  d: number | null;
}

/** cluster-robust two-sample comparison; clusters are player-rounds (events within a round
 *  share a board and are not independent). Returns null when either arm is empty — there is
 *  no difference between a group and nothing. */
export function clusterTest(evs: Ev[], sel:(e:Ev)=>number, label:string): ClusterStat | null {
  const F = evs.filter(e=>e.forecast), R = evs.filter(e=>!e.forecast);
  if (!F.length || !R.length) return null;
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
  const lo = boot.length ? boot[Math.floor(boot.length*0.025)]! : null;
  const hi = boot.length ? boot[Math.floor(boot.length*0.975)]! : null;
  const pooled = Math.sqrt((sd(F.map(sel))**2 + sd(R.map(sel))**2)/2);
  return { label, forecastMean: mean(F.map(sel)), reactiveMean: mean(R.map(sel)), diff: d,
           ciLo: lo, ciHi: hi,
           excludesZero: lo !== null && hi !== null && (lo > 0 || hi < 0),
           d: pooled ? d/pooled : null };
}

export interface PlayerRate { user: string; forecasts: number; tspins: number; exposureShare: number }

export interface EventLevel {
  events: Ev[];
  forecastN: number; reactiveN: number;
  /** PRIMARY — the estimand. null when an arm is empty. */
  attack: ClusterStat | null;
  lines: ClusterStat | null;
  /** are the two groups comparable? */
  balance: { stackHeight: ClusterStat | null; garbagePressure: ClusterStat | null };
  /** must show NO difference; `excludesZero` true means the primary is confounded */
  negativeControl: ClusterStat | null;
  /** SECONDARY — descriptive, about these named players only */
  players: PlayerRate[];
  /** exact two-sided binomial of the forecast split against the exposure split */
  exposureTest: { user: string; k: number; n: number; expected: number; p: number } | null;
}

export function eventLevel(evs: Ev[] = collectEvents()): EventLevel {
  const F = evs.filter(e=>e.forecast);
  const users = [...new Set(evs.map(e=>e.user))];
  const tot = evs.length, totF = F.length;
  const players: PlayerRate[] = users.map(u => ({
    user: u,
    forecasts: F.filter(e=>e.user===u).length,
    tspins: evs.filter(e=>e.user===u).length,
    exposureShare: evs.filter(e=>e.user===u).length / tot,
  }));
  // exact two-sided binomial: given totF forecasts, is the split consistent with exposure?
  let exposureTest: EventLevel['exposureTest'] = null;
  const u0 = users[0];
  if (u0 !== undefined && totF > 0 && tot > 0) {
    const n0 = evs.filter(e=>e.user===u0).length, k0 = F.filter(e=>e.user===u0).length;
    const p0 = n0/tot;
    const logC=(n:number,r:number)=>{let s=0;for(let i=0;i<r;i++)s+=Math.log(n-i)-Math.log(i+1);return s;};
    const pmf=(i:number)=>Math.exp(logC(totF,i)+i*Math.log(p0)+(totF-i)*Math.log(1-p0));
    const obs=pmf(k0); let p=0; for(let i=0;i<=totF;i++){const v=pmf(i); if(v<=obs*1.0000001) p+=v;}
    exposureTest = { user: u0, k: k0, n: totF, expected: p0*totF, p: Math.min(1,p) };
  }
  return {
    events: evs, forecastN: totF, reactiveN: evs.length - totF,
    attack: clusterTest(evs, e=>e.attack, 'attack sent'),
    lines:  clusterTest(evs, e=>e.lines,  'lines cleared'),
    balance: { stackHeight:     clusterTest(evs, e=>e.stackHeight,     'stack height'),
               garbagePressure: clusterTest(evs, e=>e.garbagePressure, 'garbage pressure') },
    negativeControl: clusterTest(evs, e=>e.priorAttack, 'attack before roof'),
    players, exposureTest,
  };
}

/** null-safe fixed-point rendering; a missing statistic must not print as a number. */
const fx = (v: number | null, d: number) => v === null || !Number.isFinite(v) ? 'n/a' : v.toFixed(d);

if (import.meta.main) {
  const S = eventLevel();

  const show = (c: ClusterStat | null, label: string) => {
    if (!c) { console.log(`${label.padEnd(22)} not computable (an arm is empty)`); return; }
    console.log(`${label.padEnd(22)} forecast ${c.forecastMean.toFixed(2).padStart(6)}   reactive ${c.reactiveMean.toFixed(2).padStart(6)}   diff ${c.diff.toFixed(2).padStart(6)}   95% CI [${fx(c.ciLo, 2)}, ${fx(c.ciHi, 2)}]${c.excludesZero?'  *':''}   d=${fx(c.d, 2)}`);
  };

  console.log(`=== PRIMARY: event-level effectiveness ===`);
  console.log(`forecast T-spins ${S.forecastN}   reactive ${S.reactiveN}   total ${S.events.length}\n`);
  show(S.attack, 'attack sent');
  show(S.lines,  'lines cleared');

  console.log(`\n--- covariate balance (are the two groups comparable?) ---`);
  show(S.balance.stackHeight,     'stack height');
  show(S.balance.garbagePressure, 'garbage pressure');
  console.log(`\n--- NEGATIVE CONTROL (must show NO difference) ---`);
  show(S.negativeControl, 'attack before roof');

  console.log(`\n=== SECONDARY: player-level rate, exposure-adjusted ===`);
  for (const p of S.players) {
    console.log(`  ${p.user.padEnd(10)} ${p.forecasts} forecasts of ${p.tspins} T-spins = ${(100*p.forecasts/p.tspins).toFixed(1)}%   (exposure share ${(100*p.exposureShare).toFixed(1)}%)`);
  }
  console.log(S.exposureTest
    ? `  exact two-sided binomial vs exposure (${S.exposureTest.k}/${S.exposureTest.n} to ${S.exposureTest.user}, expected ${S.exposureTest.expected.toFixed(1)}): p = ${S.exposureTest.p.toFixed(4)}`
    : `  exact two-sided binomial vs exposure: not computable (no forecast events)`);
}

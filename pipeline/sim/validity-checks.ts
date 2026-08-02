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
 *
 * Shape: every statistic is RETURNED by `validityChecks()`, and `import.meta.main` only
 * prints. The prose in pipeline/forecast_section.py is rendered for every session but had
 * 07-22's split-half figures (0.29 / 0.064) typed into it as literals, so another session's
 * section would have published these numbers as its own. A statistic that is only ever
 * console.logged cannot be consumed as data, which is what made hardcoding them the path of
 * least resistance. `loadCases()` already honours REPLAY_DIR, so the functions below are
 * session-capable as they stand.
 *
 * Anything not computable on the input comes back `null`, never 0/NaN/Infinity. A later
 * session may have too few scorable rounds for a correlation; `pearson` used to answer 0 for
 * a constant or empty input, and a 0 reads downstream as "measured, and there is no
 * relationship" — a fabricated finding rather than a missing one.
 */
import { forecastMetric } from './forecast.ts';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';

export type Row = { file:string; round:number; user:string; won:number;
                    frac:number; verified:number; placed:number; n:number; fc:number };

/** One row per player-round: the verified prefix and the forecast events inside it. */
export function collectRows(): Row[] {
  const rows: Row[] = [];
  for (const c of loadCases()) {
    const r = runCase(c);
    const v = verifiedIndex(r, c.truth) + 1;
    const recs = v === 0 ? [] : forecastMetric(r, true).records.filter(x => x.lockIndex < v);
    rows.push({ file:c.file, round:c.round, user:c.user, won: c.alive ? 1 : 0,
                frac: v / c.placed, verified: v, placed: c.placed,
                n: recs.length, fc: recs.filter(x=>x.kind!=='reactive').length });
  }
  return rows;
}

/** Pearson r, or null where it is undefined: fewer than 2 observations, or either side
 *  constant. Returning 0 there would publish "no correlation" for "no measurement". */
export const pearson = (xs:number[], ys:number[]): number | null => {
  const n = xs.length;
  if (n < 2 || ys.length !== n) return null;
  const mx=xs.reduce((a,b)=>a+b,0)/n, my=ys.reduce((a,b)=>a+b,0)/n;
  let sxy=0,sxx=0,syy=0;
  for (let i=0;i<n;i++){const a=xs[i]!-mx,b=ys[i]!-my;sxy+=a*b;sxx+=a*a;syy+=b*b;}
  return sxx&&syy ? sxy/Math.sqrt(sxx*syy) : null;
};

const logC = (n:number,r:number)=>{let s=0;for(let i=0;i<r;i++)s+=Math.log(n-i)-Math.log(i+1);return s;};

export interface SignTest { k: number; n: number; p: number }

export interface SelectionBias {
  /** rounds with both players present and a decided outcome — the paired sample */
  decidedRounds: number;
  winnerLonger: number; loserLonger: number; equal: number;
  /** winner minus loser, as a FRACTION of placements (the printer scales to pp) */
  meanDelta: number | null;
  sdDelta: number | null;
  t: number | null;
  /** exact two-sided sign test over the rounds the pair did not tie on */
  signTest: SignTest | null;
  playerRounds: number;
  corrVerifiedFractionWon: number | null;
}

/** CHECK A: does the verified prefix know who won? */
export function checkSelectionBias(rows: Row[]): SelectionBias {
  // paired within round: does the winner get a longer verified prefix than the loser?
  const byRound = new Map<string, Row[]>();
  for (const r of rows) { const k=`${r.file}#${r.round}`; if(!byRound.has(k)) byRound.set(k,[]); byRound.get(k)!.push(r); }
  let winnerLonger=0, loserLonger=0, equal=0;
  const deltas:number[] = [];
  for (const v of byRound.values()) {
    if (v.length!==2) continue;
    const [a,b]=v as [Row,Row];
    if (a.won===b.won) continue;
    const W=a.won?a:b, L=a.won?b:a;
    deltas.push(W.frac - L.frac);
    if (W.frac>L.frac) winnerLonger++; else if (W.frac<L.frac) loserLonger++; else equal++;
  }
  const md = deltas.length ? deltas.reduce((a,b)=>a+b,0)/deltas.length : null;
  const sdd = md !== null && deltas.length > 1
    ? Math.sqrt(deltas.reduce((a,b)=>a+(b-md)**2,0)/(deltas.length-1)) : null;
  // a zero sd makes t infinite rather than large; that is an undefined statistic, not a huge one
  const t = md !== null && sdd ? md/(sdd/Math.sqrt(deltas.length)) : null;
  // exact two-sided sign test on the decided rounds
  const nSign = winnerLonger + loserLonger, k = Math.max(winnerLonger, loserLonger);
  let tail=0; for(let i=k;i<=nSign;i++) tail += Math.exp(logC(nSign,i) + nSign*Math.log(0.5));
  return { decidedRounds: deltas.length, winnerLonger, loserLonger, equal,
           meanDelta: md, sdDelta: sdd, t,
           signTest: nSign > 0 ? { k, n: nSign, p: Math.min(1,2*tail) } : null,
           playerRounds: rows.length,
           corrVerifiedFractionWon: pearson(rows.map(r=>r.frac), rows.map(r=>r.won)) };
}

/** The aggregation sizes the report quotes a Spearman-Brown projection for. */
export const SB_ROUNDS = [2, 8, 20, 40] as const;
/** Reliability the "how many rounds must be aggregated" answer is solved for. */
export const RELIABILITY_TARGET = 0.70;

export interface SplitHalf {
  user: string;
  scorableRounds: number;
  /** odd-vs-even within-player correlation of the per-round forecast rate */
  r11: number | null;
  /** Spearman-Brown projection of r11 to an n-round aggregate */
  spearmanBrown: { rounds: number; r: number | null }[];
  /** rounds that must be aggregated to reach RELIABILITY_TARGET; null when unreachable */
  roundsForReliability70: number | null;
}

/** CHECK B: can the per-round metric correlate with ITSELF? */
export function checkSplitHalf(rows: Row[]): SplitHalf[] {
  return [...new Set(rows.map(r=>r.user))].map(user => {
    const rs = rows.filter(r=>r.user===user && r.n>0);
    const odd = rs.filter((_,i)=>i%2===1).map(r=>r.fc/r.n);
    const even = rs.filter((_,i)=>i%2===0).map(r=>r.fc/r.n);
    const m = Math.min(odd.length, even.length);
    const r11 = pearson(odd.slice(0,m), even.slice(0,m));
    const sb = (n:number) => {
      if (r11 === null) return null;
      const v = n*r11/(1+(n-1)*r11);
      return Number.isFinite(v) ? v : null;
    };
    const T = RELIABILITY_TARGET;
    return { user, scorableRounds: rs.length, r11,
             spearmanBrown: SB_ROUNDS.map(n => ({ rounds: n, r: sb(n) })),
             roundsForReliability70: r11 !== null && r11 > 0
               ? Math.ceil((T*(1-r11))/(r11*(1-T))) : null };
  });
}

export interface ValidityChecks {
  rows: Row[];
  /** CHECK A — is verification informative about the outcome? */
  selectionBias: SelectionBias;
  /** CHECK B — one entry per player, in the order they first appear in the replays */
  splitHalf: SplitHalf[];
}

export function validityChecks(rows: Row[] = collectRows()): ValidityChecks {
  return { rows, selectionBias: checkSelectionBias(rows), splitHalf: checkSplitHalf(rows) };
}

/** null-safe fixed-point rendering; a missing statistic must not print as a number. */
const fx = (v: number | null, d: number) => v === null || !Number.isFinite(v) ? 'n/a' : v.toFixed(d);

if (import.meta.main) {
  const { selectionBias: A, splitHalf } = validityChecks();

  console.log('=== CHECK A: is verification informative about the outcome? ===\n');
  console.log(`winner's verified fraction vs loser's, ${A.decidedRounds} rounds:`);
  console.log(`  winner longer ${A.winnerLonger}   loser longer ${A.loserLonger}   equal ${A.equal}`);
  console.log(`  mean(winner - loser) = ${fx(A.meanDelta===null?null:100*A.meanDelta, 2)} pp   sd ${fx(A.sdDelta===null?null:100*A.sdDelta, 2)}   t = ${fx(A.t, 2)}`);
  console.log(`  exact sign test: ${A.signTest ? `${A.signTest.k}/${A.signTest.n}, two-sided p = ${A.signTest.p.toFixed(4)}` : 'no decided rounds'}`);
  console.log(`  correlation(verified fraction, won) across all ${A.playerRounds} player-rounds = ${fx(A.corrVerifiedFractionWon, 3)}`);

  console.log('\n=== CHECK B: can the per-round metric correlate with ITSELF? ===\n');
  for (const s of splitHalf) {
    console.log(`${s.user}: ${s.scorableRounds} scorable rounds, split-half r = ${fx(s.r11, 3)}`);
    console.log(`  Spearman-Brown: ${s.spearmanBrown.map((x,i)=>`${x.rounds}${i===0?' rounds':''} -> ${fx(x.r, 2)}`).join('   ')}`);
    console.log(`  rounds that must be aggregated to reach reliability 0.70: ${
      s.r11 === null ? 'not computable' : s.roundsForReliability70 ?? 'unreachable (r11 <= 0)'}`);
  }
  console.log('\nA per-ROUND column needs the per-round value to be reliable. If it is not, the');
  console.log('honest unit is a per-PLAYER aggregate, not a per-round comparison.');
}

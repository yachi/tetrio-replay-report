/**
 * Can an academic sequence-alignment algorithm detect MORE forecasts by extending the verified
 * prefix? Asked, measured, answered: NO — and this is the measurement.
 *
 * The forecast metric runs only on the verified prefix (~13.8% of placements), which caps detection.
 * `verifiedIndex` sets that prefix by walking the player's outgoing attacks against the opponent's
 * received stream POSITIONALLY (i vs i) and breaking at the first mismatch — a greedy cut. The
 * classic fix for "one spurious divergence truncates the rest" is global sequence alignment
 * (Needleman–Wunsch, CABIOS 1970) / Smith–Waterman, or DTW for pure timing drift: align the two
 * streams, tolerate a local hiccup, and re-sync.
 *
 * The honesty guardrail is what makes this real and not fiction. A placement may be called verified
 * only if its BOARD provably matches the game, and the board is witnessed by the attack's amount and
 * ige row. So alignment may relax ONLY the positional/timing rigidity; amount and row must still
 * agree, 1:1 (each outgoing attack ↔ one received — a gap on either side is a board divergence, not a
 * benign skip). `relaxedRun` is that maximal honest relaxation: amount+row kept strict, the hard
 * frame<=25 gate replaced by a monotonic drift-tolerant one (an accumulating line-clear delay is
 * fine; a jump backwards is divergence).
 *
 * Result over all four sessions (395 player-rounds): the honest relaxation recovers +1/+0/+1/+0
 * attacks (~13 placements of ~8,500) and 0 -> 0 verified forecasts. The tempting +38/+11/+17/+15 is
 * the LCS-with-GAPS ceiling, and every gap is a non-1:1 match = a real board divergence. So the
 * greedy break is a genuine board error (the wrong garbage-insertion rule; ~6% correct after the
 * first garbage), not a timing artifact an alignment could fix. Extending coverage is a
 * simulator-fidelity problem (system identification of the insertion timing), not an alignment one.
 *
 *   REPLAY_DIR=sessions/2026-07-22 bun pipeline/sim/prefix-alignment-probe.ts
 */
import { loadCases, runCase } from './verified-prefix.ts';
import { matchesIgeY } from './ige-y-oracle.ts';
import { forecastMetric, isVerifiedForecast } from './forecast.ts';

type Atk = { frame: number; amt: number; lines: number; clearedRows: number[] };
type Truth = { frame: number; amt: number; y: number };

const boardMatch = (a: Atk, b: Truth) =>
  a.amt === b.amt && (a.lines === 0 || matchesIgeY(a.clearedRows, a.lines, b.y));

// current greedy prefix: contiguous run of positional matches (frame<=25, amount, row)
function greedyRun(mine: Atk[], truth: Truth[]): number {
  let n = 0;
  for (let i = 0; i < Math.min(mine.length, truth.length); i++) {
    const a = mine[i]!, b = truth[i]!;
    if (Math.abs(a.frame - b.frame) > 25) break;
    if (a.amt !== b.amt) break;
    if (a.lines > 0 && !matchesIgeY(a.clearedRows, a.lines, b.y)) break;
    n++;
  }
  return n;
}

// first break reason after the greedy run
function breakReason(mine: Atk[], truth: Truth[], run: number): string {
  if (run >= Math.min(mine.length, truth.length)) return 'no-break (stream exhausted)';
  const a = mine[run]!, b = truth[run]!;
  if (Math.abs(a.frame - b.frame) > 25) return `frame (Δ=${a.frame - b.frame})`;
  if (a.amt !== b.amt) return `amount (${a.amt} vs ${b.amt})`;
  return 'row';
}

// upper bound: longest common subsequence of mine vs truth under boardMatch (order-preserving, gaps
// allowed). Counts attacks whose BOARD provably matches, ignoring the positional/timing rigidity.
function lcsBoard(mine: Atk[], truth: Truth[]): number {
  const n = mine.length, m = truth.length;
  const dp = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = 1; i <= n; i++) for (let j = 1; j <= m; j++)
    dp[i]![j] = boardMatch(mine[i - 1]!, truth[j - 1]!)
      ? dp[i - 1]![j - 1]! + 1 : Math.max(dp[i - 1]![j]!, dp[i]![j - 1]!);
  return dp[n]![m]!;
}

// The HONEST relaxation: 1:1 amount+row (board constraints kept), but the timing gate replaced by a
// monotonic, drift-tolerant one — frames must be non-decreasing and the drift may grow (an
// accumulating line-clear delay) rather than being hard-capped at 25. Anything that fails amount or
// row still breaks. This is the most an alignment can legitimately buy.
function relaxedRun(mine: Atk[], truth: Truth[]): number {
  let n = 0, drift = 0;
  for (let i = 0; i < Math.min(mine.length, truth.length); i++) {
    const a = mine[i]!, b = truth[i]!;
    if (a.amt !== b.amt) break;                       // board+table constraint — never relaxed
    if (a.lines > 0 && !matchesIgeY(a.clearedRows, a.lines, b.y)) break;   // board constraint — never relaxed
    const d = a.frame - b.frame;
    if (i > 0 && d < drift - 25) break;               // timing must not JUMP BACK (non-monotonic = divergence)
    drift = d; n++;
  }
  return n;
}
const attackFrameOf = (mine: Atk[], run: number) => run > 0 ? mine[run - 1]!.frame : -1;
const locksUpTo = (r: any, vf: number) => { let v = -1; for (let i = 0; i < r.locks.length; i++) if (r.locks[i]!.frame <= vf) v = i; return v; };

const reasons: Record<string, number> = {};
let rounds = 0, greedyTot = 0, lcsTot = 0, relaxedTot = 0, headroomRounds = 0, headroomAttacks = 0;
let placesCur = 0, placesRelax = 0, fcCur = 0, fcRelax = 0;
for (const c of loadCases()) {
  const r = runCase(c);
  const mine = r.records.filter((x: any) => x.sent > 0)
    .map((x: any) => ({ frame: x.frame, amt: x.sent, lines: x.lines, clearedRows: x.clearedRows }));
  if (mine.length === 0 || c.truth.length === 0) continue;
  rounds++;
  const run = greedyRun(mine, c.truth), lcs = lcsBoard(mine, c.truth), relax = relaxedRun(mine, c.truth);
  const key = breakReason(mine, c.truth, run).replace(/Δ=-?\d+/, 'Δ').replace(/\d+ vs \d+/, 'x vs y');
  reasons[key] = (reasons[key] ?? 0) + 1;
  greedyTot += run; lcsTot += lcs; relaxedTot += relax;
  if (lcs > run) { headroomRounds++; headroomAttacks += lcs - run; }

  // forecast counts under the current gate vs the relaxed (timing-aligned) gate
  const vCur = locksUpTo(r, attackFrameOf(mine, run));
  const vRel = locksUpTo(r, attackFrameOf(mine, relax));
  placesCur += vCur + 1; placesRelax += vRel + 1;
  const pre = (idx: number) => ({ ...r, records: [], locks: r.locks.filter((_: any, i: number) => i <= idx) });
  fcCur += forecastMetric(pre(vCur) as any, true).records.filter(isVerifiedForecast).length;
  fcRelax += forecastMetric(pre(vRel) as any, true).records.filter(isVerifiedForecast).length;
}

console.log(`rounds with outgoing attacks: ${rounds}`);
console.log(`greedy verified attacks (current prefix): ${greedyTot}`);
console.log(`relaxed (1:1, timing-aligned) attacks:    ${relaxedTot}   (+${relaxedTot - greedyTot} legit)`);
console.log(`board-match LCS upper bound (w/ gaps):    ${lcsTot}   (+${lcsTot - greedyTot} ceiling)`);
console.log(`verified PLACEMENTS: current ${placesCur} -> relaxed ${placesRelax}  (+${placesRelax - placesCur})`);
console.log(`VERIFIED FORECASTS:  current ${fcCur} -> relaxed ${fcRelax}  (+${fcRelax - fcCur})`);
console.log(`\nfirst-break reason distribution:`);
for (const [k, v] of Object.entries(reasons).sort((a, b) => b[1] - a[1])) console.log(`  ${String(v).padStart(4)}  ${k}`);

/**
 * ROADMAP "Original TODO 1": does ANY board-derived measure predict who won the round?
 *
 * The point of this file is to be cheap and decisive. Items 3 and 4 of that TODO (fixing the
 * post-garbage divergence, writing a second independent simulator) are gated on it: if every
 * candidate lands where `forecast rate` landed, the answer is that board-derived measures do not
 * carry a signal at this sample size, and no amount of simulator fidelity changes that.
 *
 * Five candidates, all computed over the VERIFIED PREFIX only, so nothing here depends on the part
 * of the simulation that is known to diverge:
 *
 *   height at garbage     mean stack height at the moment garbage lands   (lower = calmer)
 *   holes per piece       covered holes on the final board, per placement (lower = cleaner)
 *   well depth            mean depth of the deepest well                  (a proxy for I-dependence)
 *   downstack rate        rows cleared per piece while garbage is on the board
 *   height at end         stack height at the end of the prefix
 *
 * Pairing is winner-vs-loser within a round, through the SAME `decideWinner` the forecast AUC uses.
 * AUC is reported with its decided-pair count, because a tie carries no information and an AUC over
 * mostly-ties is dragged to 50% whatever the effect. p-values are exact sign tests, and are
 * Holm-adjusted across the five metrics — five shots at 0.05 is one false positive every four runs.
 *
 *   bun run board-metrics.ts sessions/2026-07-22 [...]
 */
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';
import { auc, exactSignP, decideWinner } from './pairs.ts';
import { H } from './sim.ts';

const W = 10;
type Board = (string | null)[][];

const heights = (b: Board) => {
  const h = new Array<number>(W).fill(0);
  for (let c = 0; c < W; c++) for (let r = 0; r < H; r++) if (b[r]![c] !== null) { h[c] = H - r; break; }
  return h;
};
const maxHeight = (b: Board) => Math.max(...heights(b));

/** empty cells with at least one filled cell above them in the same column */
function coveredHoles(b: Board) {
  let n = 0;
  for (let c = 0; c < W; c++) {
    let seen = false;
    for (let r = 0; r < H; r++) {
      if (b[r]![c] !== null) seen = true;
      else if (seen) n++;
    }
  }
  return n;
}

/** depth of the deepest column relative to its neighbours; the walls count as full height */
function deepestWell(b: Board) {
  const h = heights(b);
  let best = 0;
  for (let c = 0; c < W; c++) {
    const l = c === 0 ? H : h[c - 1]!, r = c === W - 1 ? H : h[c + 1]!;
    best = Math.max(best, Math.min(l, r) - h[c]!);
  }
  return best;
}

const hasGarbage = (b: Board) => b.some(row => row.some(c => c === 'G'));

export const METRICS = ['height at garbage', 'holes per piece', 'well depth',
                        'downstack rate', 'height at end',
                        // CONTROLS, declared before the result was looked at:
                        //   the same clearing rate with NO garbage on the board — if the winner also
                        //     clears more when nothing is pressing, "downstacks under pressure" is
                        //     just "clears more", and the pressure is decoration
                        'clear rate (no pressure)',
                        //   and exposure: a longer verified prefix is more chances to do anything
                        'verified prefix length'] as const;
export type BoardMetric = (typeof METRICS)[number];

export function valuesFor(r: any, v: number): Record<BoardMetric, number | null> {
  const boards = r.boards as Board[];
  const atGarbage: number[] = [];
  for (const g of r.garbageEvents) {
    if (g.lockIndex > v || g.lockIndex < 1) continue;
    atGarbage.push(maxHeight(boards[g.lockIndex - 1]!));   // the board the garbage landed on
  }
  let wellSum = 0, pressureLocks = 0, pressureCleared = 0, calmLocks = 0, calmCleared = 0;
  for (let t = 0; t <= v; t++) {
    wellSum += deepestWell(boards[t]!);
    if (t === 0) continue;
    if (hasGarbage(boards[t - 1]!)) { pressureLocks++; pressureCleared += r.locks[t]!.cleared; }
    else { calmLocks++; calmCleared += r.locks[t]!.cleared; }
  }
  return {
    'height at garbage': atGarbage.length ? atGarbage.reduce((a, b) => a + b, 0) / atGarbage.length : null,
    'holes per piece': coveredHoles(boards[v]!) / (v + 1),
    'well depth': wellSum / (v + 1),
    'downstack rate': pressureLocks ? pressureCleared / pressureLocks : null,
    'height at end': maxHeight(boards[v]!),
    'clear rate (no pressure)': calmLocks ? calmCleared / calmLocks : null,
    'verified prefix length': v + 1,
  };
}

if (import.meta.main) {
  const sessions = process.argv.slice(2);
  if (!sessions.length) throw new Error('usage: bun run board-metrics.ts <session dir> [...]');

  const byRound = new Map<string, Record<string, { alive: boolean; vals: Record<string, number | null>; v: number }>>();
  for (const session of sessions) {
    process.env.REPLAY_DIR = session;
    for (const c of loadCases(session)) {
      const r = runCase(c, {});
      const v = verifiedIndex(r, c.truth);
      if (v < 0) continue;
      const k = `${session}#${c.file}#${c.round}`;
      if (!byRound.has(k)) byRound.set(k, {});
      byRound.get(k)![c.user] = { alive: c.alive, vals: valuesFor(r, v), v };
    }
  }

  const pairs: Record<string, { win: number; lose: number }[]> = {};
  for (const m of METRICS) pairs[m] = [];
  let rounds = 0;
  for (const vals of byRound.values()) {
    const wl = decideWinner(vals);
    if (!wl) continue;
    rounds++;
    for (const m of METRICS) {
      const w = vals[wl.W]!.vals[m], l = vals[wl.L]!.vals[m];
      if (w == null || l == null) continue;
      if (!Number.isFinite(w) || !Number.isFinite(l)) throw new Error(`non-finite ${m}`);
      pairs[m]!.push({ win: w, lose: l });
    }
  }

  console.log(`rounds with a decided winner and a verified prefix on both sides: ${rounds}\n`);
  console.log('metric                 pairs  decided   AUC     W-L-T        p (exact)   p (Holm)');
  const raw: { m: string; p: number | null; line: string }[] = [];
  for (const m of METRICS) {
    const P = pairs[m]!;
    if (!P.length) { console.log(`  ${m.padEnd(20)} no usable pairs`); continue; }
    const a = auc(P);
    const decided = a.wins + a.losses;
    const p = exactSignP(a.wins, a.losses);
    raw.push({ m, p, line: `  ${m.padEnd(20)} ${String(a.n).padStart(5)} ${String(decided).padStart(8)}`
      + `  ${a.auc.toFixed(1).padStart(5)}%  ${a.wins}-${a.losses}-${a.ties}`.padEnd(22) });
  }
  // Holm: sort ascending, multiply the k-th smallest by (m - k), keep it monotone
  const sorted = [...raw].filter(x => x.p != null).sort((a, b) => a.p! - b.p!);
  const adj = new Map<string, number>();
  let running = 0;
  sorted.forEach((x, i) => {
    running = Math.max(running, Math.min(1, x.p! * (sorted.length - i)));
    adj.set(x.m, running);
  });
  for (const x of raw)
    console.log(`${x.line} ${x.p == null ? '   n/a  ' : x.p.toFixed(3).padStart(8)}   ${(adj.get(x.m) ?? 1).toFixed(3)}`);

  console.log(`\nAUC is P(winner's value > loser's value): below 50% means the winner tends to have LESS.`);
  console.log(`Filed for comparison: forecast rate is 0 for every player, so it ties every pair;`);
  console.log(`tucked T-spins sits at 57.0% on 79 pairs (auc.ts), already under "no signal".`);
}

/**
 * Are the sim's garbage HOLE COLUMNS right?
 *
 * halp1/triangle's tank() re-rolls the hole column PER GARBAGE LINE, gated on
 * `messiness.within`, and keeps `lastColumn` between attacks otherwise. sim.ts instead uses
 * the single transmitted `x` for all `amt` lines of an event. If within > 0 in these games,
 * every multi-line attack has the wrong holes, rows never fill, and the stack grows — which
 * is exactly the observed failure (sim's stack taller than reality in 81% of row mismatches).
 *
 * `stats.garbage.cleared` is exact ground truth for how many garbage lines the player
 * actually cleared, and it is a DIFFERENT oracle from `garbage.received`: you can only clear
 * a garbage row if you can fill its hole, so wrong columns show up here and nowhere else.
 * Comparable only on rounds the sim survives.
 *
 * Control: a deliberately WRONG column model (every hole forced to column 0). If the real
 * model and the control score the same, this oracle cannot see column errors and the test is
 * vacuous — the same self-validation the mutation harness uses.
 */
import { loadCases, runCase } from './verified-prefix.ts';

// attach the two ground-truth garbage stats to each case
import { readFileSync, readdirSync } from 'node:fs';
const DIR = process.env.REPLAY_DIR ?? `${import.meta.dir}/..`;
const truth = new Map<string, { cleared: number; recv: number; lines: number }>();
for (const f of readdirSync(DIR).filter(x => x.endsWith('.ttrm')).sort()) {
  const d = JSON.parse(readFileSync(`${DIR}/${f}`, 'utf8'));
  d.replay.rounds.forEach((rnd: any, ri: number) => {
    for (const p of rnd) truth.set(`${f}#${ri}#${p.username}`,
      { cleared: p.replay.results.stats.garbage.cleared ?? 0,
        recv: p.replay.results.stats.garbage.received ?? 0,
        lines: p.replay.results.stats.lines ?? 0 });
  });
}
const cases = loadCases().map(c => {
  const t = truth.get(`${c.file}#${c.round}#${c.user}`)!;
  return Object.assign(c, { clearedTruth: t.cleared, recvTruth: t.recv, linesTruth: t.lines });
});

// Whole-dataset scoring: every variant is evaluated over ALL 158 player-rounds, so the
// denominator is fixed. Restricting to rounds a variant survives is a selection effect —
// variants that die more survive only the easy (low-garbage) rounds, which flatters them.
const score = (label: string, mutate: (g: any[]) => any[]) => {
  let simLines = 0, realLines = 0, simCleared = 0, realCleared = 0, placed = 0, realPlaced = 0, topout = 0;
  for (const c of cases) {
    const r = runCase({ ...c, gin: mutate(c.gin.map((g: any) => ({ ...g }))) });
    simLines += r.lines; realLines += (c as any).linesTruth;
    simCleared += r.garbage.cleared; realCleared += (c as any).clearedTruth;
    placed += r.placed; realPlaced += c.placed;
    if (r.topout) topout++;
  }
  console.log(`${label.padEnd(30)} lines ${String(simLines).padStart(4)}/${realLines}  garbage-cleared ${String(simCleared).padStart(3)}/${realCleared}  pieces ${String(placed).padStart(5)}/${realPlaced}  topout ${topout}/158`);
};

console.log('Does the sim clear the garbage rows the player cleared?\n');
score('as recorded (single x per event)', g => g);
score('CONTROL: all holes at column 0', g => g.map(x => ({ ...x, x: 0 })));
score('CONTROL: holes shifted by +1', g => g.map(x => ({ ...x, x: (x.x + 1) % 10 })));
// coordinate conventions: is x measured from the other edge, or is it the column of a
// BLOCK rather than the hole?
score('mirrored: 9 - x', g => g.map(x => ({ ...x, x: 9 - x.x })));
for (const d of [2,3,4,5,6,7,8,9])
  score(`shifted by +${d}`, g => g.map(x => ({ ...x, x: (x.x + d) % 10 })));
score('CONTROL: column 4 (modal)', g => g.map(x => ({ ...x, x: 4 })));
score('CONTROL: no garbage at all', () => []);
console.log('\nIf the control scores the same as the recorded model, this oracle cannot see');
console.log('column errors and the comparison is vacuous.');

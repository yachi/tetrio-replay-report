/**
 * The constructed SDPC loops (`analysis/sdpc-loop-demos.json`, from `pipeline/sim/emit-sdpc-loop-demos.ts`;
 * the planner is `pipeline/sim/sdpc-loop-demos.ts`).
 *
 *   1. byte rebuild: the committed artefact is what `build()` produces now (which itself replays every
 *      loop through the engine and throws on any disagreement), and its md5 lines are current.
 *   2. re-run: every loop's inputs, rebuilt from the SD demo's and the DPC half's, played on a fresh
 *      engine, give the committed locks.
 *   3. an independent decode of each loop's locks from an empty board: TSS, TSD, an empty board after
 *      lock 19, the leftover first, a TSD, an empty board after lock 34, no hold, five whole bags.
 *   4. completeness: every SD Perfect Clear demo × every built DPC half with the same leftover is a loop,
 *      once; every DPC Perfect Clear of the catalogue in both hands is built or a named duplicate.
 *   5. mutants: a moved lock, a dropped lock and a held piece each fail the decode.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/sdpc-loop-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { build, serialise, PATHS } from '../sim/sdpc-loop-demos.ts';
import { runDemo } from '../sim/route-demos.ts';
import { placeCells, queueStates, WIDTH } from '../sim/emit-replay.ts';

const ART = `${import.meta.dir}/../../analysis/sdpc-loop-demos.json`;
const committedText = readFileSync(ART, 'utf8');
const A = JSON.parse(committedText);
const SD = JSON.parse(readFileSync(PATHS.stickspinDemos, 'utf8'));
const DPC = JSON.parse(readFileSync(PATHS.dpcSetups, 'utf8'));
const ROUTES = JSON.parse(readFileSync(PATHS.stickspinRoutes, 'utf8'));
const sdBy = new Map<string, any>(SD.demos.map((d: any) => [d.node, d]));
const halfBy = new Map<string, any>(A.dpc_halves.map((h: any) => [h.dpc, h]));
const md5 = (b: string | Buffer) => createHash('md5').update(b).digest('hex');

test('1. byte rebuild and current md5s', () => {
  expect(serialise(build())).toBe(committedText);
  expect(A.report_eligible).toBe(false);
  expect(A.constructed).toBe(true);
  expect(A.inputs.stickspin_demos_md5).toBe(md5(readFileSync(PATHS.stickspinDemos)));
  expect(A.inputs.dpc_setups_md5).toBe(md5(readFileSync(PATHS.dpcSetups)));
  expect(A.inputs.planner_md5).toBe(md5(readFileSync(`${import.meta.dir}/../sim/sdpc-loop-demos.ts`)));
}, 120_000);

test('2. every loop re-runs on a fresh engine to its committed locks', () => {
  for (const L of A.loops) {
    const sd = sdBy.get(L.sd)!, h = halfBy.get(L.dpc)!;
    const inputs = [...sd.inputs, ...h.inputs.map(([f, t, k]: any) => [f + sd.frames, t, k])];
    expect(L.frames).toBe(sd.frames + h.frames);
    const { rec } = runDemo(ROUTES, L.seq, inputs as any, L.frames);
    expect(JSON.stringify(rec.locks)).toBe(JSON.stringify(L.locks));
  }
}, 300_000);

/** From an empty board, independently of the planner: the board after every lock. Returns the problems. */
function decodeProblems(L: any): string[] {
  try { return decode(L); } catch (e) { return [String(e)]; }
}
function decode(L: any): string[] {
  const bad: string[] = [];
  const g: (string | null)[][] = Array.from({ length: 40 }, () => new Array(WIDTH).fill(null));
  const qs = queueStates(L.seq, L.locks);
  const spins: string[] = [];
  L.locks.forEach((lk: any, i: number) => {
    if (lk[5]) bad.push(`lock ${i} holds`);
    const piece = qs[i]!.piece;
    for (const c of placeCells(piece, lk[1])) {
      const y = Math.floor(c / WIDTH), x = c % WIDTH;
      if (g[y]![x]) bad.push(`lock ${i} overlaps`);
      g[y]![x] = piece;
    }
    const full = g.map((r, y) => (r.every(Boolean) ? y : -1)).filter(y => y >= 0);
    if (full.length !== lk[2]) bad.push(`lock ${i} fills ${full.length} rows, records ${lk[2]}`);
    for (let k = full.length - 1; k >= 0; k--) { g.splice(full[k]!, 1); g.push(new Array(WIDTH).fill(null)); }
    if (lk[3] > 0 && lk[2] > 0) spins.push(`${i}:${piece}${lk[3]}/${lk[2]}`);
    const empty = g.every(r => r.every(c => !c));
    if ((i === 19 || i === 34) !== empty) bad.push(`lock ${i}: board ${empty ? '' : 'not '}empty`);
  });
  if (L.locks.length !== 35) bad.push(`${L.locks.length} locks`);
  if (spins.join(' ') !== '6:T2/1 13:T2/2 27:T2/2') bad.push(`spins ${spins.join(' ')}`);
  for (let b = 0; b < 5; b++)
    if ([...L.seq.slice(7 * b, 7 * b + 7)].sort().join('') !== 'IJLOSTZ') bad.push(`bag ${b + 1} is not a 7-bag`);
  if (qs[20]!.piece !== L.leftover || L.seq[20] !== L.leftover) bad.push('the leftover is not placed first');
  return bad;
}

test('3. an independent decode of every loop', () => {
  for (const L of A.loops) expect(`${L.id}: ${decodeProblems(L).join('; ')}`).toBe(`${L.id}: `);
});

test('4. completeness', () => {
  const sds = SD.demos.filter((d: any) => /^2\.(sd|mochi)\.pc#\d+$/.test(d.node));
  const want = new Set<string>();
  for (const sd of sds) for (const h of A.dpc_halves) if (h.leftover === sd.bags[2].unused) want.add(`${sd.node}+${h.dpc}`);
  const ids = A.loops.map((L: any) => L.id);
  expect(new Set(ids).size).toBe(ids.length);
  expect([...want].sort()).toEqual([...ids].sort());
  const all: string[] = [];
  for (const s of DPC.setups) for (const pc of s.pcs) all.push(pc, `${pc}.mirror`);
  const covered = [...A.dpc_halves.map((h: any) => h.dpc), ...A.dpc_unbuilt.map((u: any) => u.dpc)];
  expect(covered.sort()).toEqual(all.sort());
  for (const u of A.dpc_unbuilt) expect(halfBy.has(u.same_as)).toBe(true);   // every unbuilt one is a duplicate
  expect(A.counts.loops).toBe(A.loops.length);
});

test('5. mutants fail the decode', () => {
  const L = A.loops[0];
  const moved = { ...L, locks: L.locks.map((lk: any, i: number) => (i === 25 ? [lk[0], lk[1] + 1, ...lk.slice(2)] : lk)) };
  const dropped = { ...L, locks: L.locks.slice(0, 34) };
  const held = { ...L, locks: L.locks.map((lk: any, i: number) => (i === 21 ? [...lk.slice(0, 5), 1, ...lk.slice(6)] : lk)) };
  for (const m of [moved, dropped, held]) expect(decodeProblems(m).length).toBeGreaterThan(0);
  expect(decodeProblems(L)).toEqual([]);
});

/**
 * The STSD constructed demos (`analysis/stsd-demos.json`, from `pipeline/sim/emit-technique-demos.ts
 * --technique stsd`; the planner is the shared `technique-demos.ts`, STSD's half is
 * `technique-demos-stsd.ts`).
 *
 *   1. byte rebuild: the committed artefact is what `build()` produces now (its `inputs` hash the
 *      transcription, the planner files, `emit-replay.ts` and the corpus matcher).
 *   2. quarantine: `report_eligible: false`, `constructed: true`.
 *   3. the engine re-run: every demo's queue and inputs, replayed on a fresh engine, lock for lock.
 *   4. every `reaches` entry on the demo's own decoded timeline (`reachProblems`), and every drawn
 *      board reached by exactly one demo or named unbuilt (DEMO_UNBUILT, with the planner's reason).
 *   5. THE MATCHER SEES ITS OWN DEMO: the corpus predicate (`windowMatch`, as drawn) fires on the
 *      stood T of every demo, at the board before it, and on no other lock.
 *   6. spins: exactly two T-spins, both full TSDs, at `stood_lock` and `followup_lock`.
 *   7. dealing: whole 7-bags; holds at exactly lock 6 (bag 1's T held), the stood T and the follow-up.
 *   8. the base is ours: the first `base_locks` locks are the terrain's, none a T, and they cover it.
 *   9. mutants: `noReach`, `baseSeeded` (the engine arbiter refuses); `noSpinCheck` is measured
 *      EQUIVALENT (both T slots are reachable only by a spin) and asserted byte-identical; `no180` is a
 *      CONTROL on the checks (it moves one path of roof.i, and every check still passes).
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/stsd-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, reachProblems, drawnCells, type DemoMutants } from '../sim/technique-demos.ts';
import { runDemo, PIECES } from '../sim/route-demos.ts';
import { decodeTimeline, queueStates, placeCells, WIDTH, ROWS } from '../sim/emit-replay.ts';
import { prepare, windowMatch } from '../sim/technique-facts.ts';
import { STSD } from '../sim/technique-profile-stsd.ts';
import { STSD_DEMOS } from '../sim/technique-demos-stsd.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/stsd-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(STSD_DEMOS.transcriptionPath, 'utf8'));
const V = TR.variants.find((v: any) => v.id === STSD_DEMOS.variant);
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));

/** Boards no demo stands on, and the reason the artefact gives. The four garbage boards are the
 *  profile's; the rest are the planner's measured reasons (a terrain whose cell count is not a
 *  multiple of four cannot be built from tetrominoes, and its build board fails with it). */
const DEMO_UNBUILT: Record<string, string> = {
  'build3.jl_hole': '地形有 29 格，唔係 4 嘅倍數：用方塊由空盤砌唔出',
  'build3.jl_hole.terrain': 'build3.jl_hole 砌唔到：地形有 29 格，唔係 4 嘅倍數：用方塊由空盤砌唔出',
  'misfire.garbage': '個窿係一行垃圾嘅窿：垃圾行要對手送先有，砌出嚟嘅示範冇對手，唔可以自己落垃圾',
  'misfire.spin': '係 misfire.garbage 嗰行垃圾上面打嘅，同一個原因砌唔到',
  'recover.j': '係 misfire 之後嘅盤面（有垃圾行），同一個原因砌唔到',
  'recover.j.after': '係 recover.j 之後嘅盤面，同一個原因砌唔到',
  'roof.z': '地形有 21 格，唔係 4 嘅倍數：用方塊由空盤砌唔出',
  'roof.z.terrain': 'roof.z 砌唔到：地形有 21 格，唔係 4 嘅倍數：用方塊由空盤砌唔出',
};
/** Which boards each built demo stands on, pinned. */
const REACHES: Record<string, string[]> = {
  'build3.jl': ['build3.terrain', 'build3.jl', 'basic', 'basic.spin', 'basic.after'],
  'roof.i': ['roof.i.terrain', 'roof.i'],
};

/** Every check on one artefact; null when all pass, else the first failure. */
function checkAll(art: any): string | null {
  if (art.report_eligible !== false || art.constructed !== true) return 'quarantine flags';
  const reached = new Map<string, number>();
  for (const d of art.demos) {
    // 4. reaches
    const bad = reachProblems(TR, V, d);
    if (bad.length) return `${d.node}: ${bad[0]}`;
    if (JSON.stringify(d.reaches.map((r: any) => r.node)) !== JSON.stringify(REACHES[d.node] ?? null))
      return `${d.node}: reaches ${d.reaches.map((r: any) => r.node)}`;
    for (const r of d.reaches) reached.set(r.node, (reached.get(r.node) ?? 0) + 1);
    // 6. spins
    const spins = d.locks.map((l: any, i: number) => [i, l[3], l[2]]).filter((x: any) => x[1] > 0);
    if (JSON.stringify(spins) !== JSON.stringify([[d.stood_lock, 2, 2], [d.followup_lock, 2, 2]]))
      return `${d.node}: spins ${JSON.stringify(spins)}`;
    // 5. the corpus matcher fires on the stood T and on no other lock
    const q = queueStates(d.seq, d.locks);
    const boards: (string | null)[][][] = [];
    try { decodeTimeline(d.seq, d.locks, (b, i) => { boards[i] = b.map(r => [...r]); }); }
    catch (e) { return `${d.node}: does not decode: ${(e as Error).message}`; }
    const P = prepare(TR, V)[0]!;
    const fired: number[] = [];
    d.locks.forEach((lk: any, i: number) => {
      if (q[i]!.piece !== 'T' || i === 0) return;
      const before = [...boards[i - 1]!].reverse().map(r => r.map(c => c ?? '.').join(''));
      const cells = placeCells('T', lk[1]).map(c => ({ row: ROWS - 1 - Math.floor(c / WIDTH), col: c % WIDTH }));
      if (windowMatch(before, cells, P)) fired.push(i);
    });
    if (JSON.stringify(fired) !== JSON.stringify([d.stood_lock])) return `${d.node}: the window fires at ${fired}`;
    // 7. dealing: whole 7-bags, and the three holds
    for (let k = 0; k + 7 <= d.seq.length; k += 7)
      if ([...d.seq.slice(k, k + 7)].sort().join('') !== [...PIECES].sort().join('')) return `${d.node}: bag ${d.seq.slice(k, k + 7)}`;
    const holds = d.locks.map((l: any, i: number) => (l[5] ? i : -1)).filter((i: number) => i >= 0);
    if (JSON.stringify(holds) !== JSON.stringify([6, d.stood_lock, d.followup_lock])) return `${d.node}: holds at ${holds}`;
    if (d.seq[6] !== 'T' || q[6]!.piece === 'T') return `${d.node}: bag 1's T is not dealt last and held`;
    // 8. the base is ours, and built
    const terr = drawnCells(byId.get(d.terrain).rows, TR.empty_letters);
    if (d.base_locks * 4 !== terr.size || !d.roles.startsWith('b'.repeat(d.base_locks))
        || d.roles.slice(d.base_locks).includes('b')) return `${d.node}: base_locks ${d.base_locks} for ${terr.size} cells`;
    const baseCells = d.locks.slice(0, d.base_locks).flatMap((l: any, i: number) => placeCells(q[i]!.piece, l[1]));
    if (q.slice(0, d.base_locks).some(x => x.piece === 'T')
        || baseCells.sort((a: number, b: number) => a - b).join() !== [...terr.keys()].sort((a, b) => a - b).join())
      return `${d.node}: the base locks are not the terrain`;
  }
  const unbuilt = Object.fromEntries(art.unbuilt.map((u: any) => [u.node, u.reason]));
  if (JSON.stringify(Object.entries(unbuilt).sort()) !== JSON.stringify(Object.entries(DEMO_UNBUILT).sort()))
    return `unbuilt ${JSON.stringify(unbuilt)}`;
  for (const n of TR.nodes)
    if ((reached.get(n.id) ?? 0) + (n.id in unbuilt ? 1 : 0) !== 1) return `${n.id}: reached or unbuilt not exactly once`;
  return null;
}

const fresh = build(STSD, STSD_DEMOS);

test('byte rebuild: the committed demos are what the planner produces now', () => {
  expect(serialise(fresh)).toBe(committedText);
});

test('every check passes on the committed artefact', () => {
  expect(checkAll(committed)).toBeNull();
  expect(committed.demos.map((d: any) => d.node)).toEqual(['build3.jl', 'roof.i']);
});

test('the engine re-run: every demo replays lock for lock on a fresh engine', () => {
  for (const d of committed.demos) {
    const { rec } = runDemo(TR, d.seq, d.inputs, d.frames);
    expect(JSON.stringify(rec.locks)).toBe(JSON.stringify(d.locks));
  }
});

test('planted defects turn a check red', () => {
  const plant = (f: (a: any) => void) => { const a = JSON.parse(committedText); f(a); return checkAll(a); };
  // a lock moved: the board stops being the drawing
  expect(plant(a => { a.demos[0].locks[a.demos[0].base_locks - 1][1] += 1; })).not.toBeNull();
  // the follow-up credited no spin
  expect(plant(a => { a.demos[0].locks[a.demos[0].followup_lock][3] = 0; })).not.toBeNull();
  // a reach dropped, an unbuilt reason changed, the quarantine flag flipped
  expect(plant(a => { a.demos[1].reaches.pop(); })).not.toBeNull();
  expect(plant(a => { a.unbuilt[0].reason += '。'; })).not.toBeNull();
  expect(plant(a => { a.report_eligible = true; })).not.toBeNull();
});

const T = 300_000;   // each mutant is one full plan

test('mutants: noReach and baseSeeded are refused by the engine arbiter', () => {
  for (const m of ['noReach', 'baseSeeded'] as (keyof DemoMutants)[])
    expect(() => build(STSD, STSD_DEMOS, { [m]: true })).toThrow(/engine|locked/);
}, T);

/** MEASURED EQUIVALENT: with the spin check off the planner still picks a spin, because the stood T
 *  and the follow-up T reach their cells ONLY by a spin (the engine's move search finds no plain
 *  path under either roof). Asserted byte-identical, so the day a plain path appears is a red build. */
test('equivalent: noSpinCheck changes nothing (both T slots are reachable only by a spin)', () => {
  expect(serialise(build(STSD, STSD_DEMOS, { noSpinCheck: true }))).toBe(committedText);
}, T);

/** A CONTROL on the checks, not on the bytes: without the 180 the planner takes another path for
 *  one lock of roof.i (two CW instead of a 180), and every check still passes — no demo NEEDS a 180. */
test('control: no180 changes a path and no check (no demo needs a 180)', () => {
  const art = build(STSD, STSD_DEMOS, { no180: true });
  expect(checkAll(art)).toBeNull();
  expect(serialise(art)).not.toBe(committedText);
}, T);

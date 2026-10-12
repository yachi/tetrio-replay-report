/**
 * The 迷走砲 constructed demos (`analysis/stray-cannon-demos.json`, from
 * `pipeline/sim/emit-stray-cannon-demos.ts`; the planner is `pipeline/sim/stray-cannon-demos.ts`).
 *
 *   1. byte rebuild: the committed artefact is what `build()` produces now.
 *   2. re-run: every demo's queue and key inputs, fed to a fresh engine through `instrumentEngine`,
 *      lock exactly the committed locks. That is the reachability witness: the engine moved each
 *      piece there from spawn under SRS+.
 *   3. the corpus classifier agrees: each demo, digested like a corpus round, reaches the node it
 *      demonstrates (the two colour readings: off the page by colour as drawn, on it as read).
 *   4. board equality against the drawing, independent of the classifier: the U is empty on the
 *      drawn board and fired next; a PC pattern is the kept-rows composite and ends empty.
 *   5. spins: every U lock is a full T-spin, every other T none; the U line counts the drawing does
 *      not fix are a NAMED list (DEMO_SPIN_LINES), compared both ways.
 *   6. the queue is whole 7-bags, each bag satisfies its node's page condition, holds match flags.
 *   7. a child demo's locks start with its parent's.
 *   8. completeness: every node with a board has one demo or one DEMO_UNBUILT entry with its reason.
 *   9. mutants: each planner rule turned off, and each planted artefact defect, turns a check red.
 *
 * Checks 2-8 are the shared `route-demo-checks.ts` (はちみつ砲's demo test runs the same ones); what
 * stays here is 迷走砲's: its named lists, its data mutants and its controls.
 *
 * Run: bun test pipeline/openers/stray-cannon-demos.test.ts   (about half a minute: one build plus
 * the planner mutants, each a full build)
 */
import { test, expect } from 'bun:test';
import { build, serialise, reach, chainOf, newEngine, type DemoMutants } from '../sim/stray-cannon-demos.ts';
import { WIDTH, ROWS } from '../sim/emit-replay.ts';
import { MEISOU } from '../sim/route-profile-meisou.ts';
import { demoChecks } from './route-demo-checks.ts';

/** Nodes with a board and no demo, and the reason the artefact gives. A node the planner cannot
 *  build is a red build until it is named here. */
const DEMO_UNBUILT: Record<string, string> = {
  '2.ideal.fire.stmb_template': '「p」格冇指定填法；佢嘅例就係 stmb_example 嘅示範',
  '2.normal_OS.tst_donate.after': '最遠放到 LJZSOI；之後：T(U) 由出生位行唔到去',
  '2.z_left.pc#6': '最遠放到 JOI；之後：S 中間隔住嘅行未消，未成形；Z 中間隔住嘅行未消，未成形；L 中間隔住嘅行未消，未成形',
};
/** The line count of every U lock the drawing does not fix (a bag-2 U is a TST, a bag-3 U drawn as
 *  a TSD slot is a TSD; these are the rest), as the engine credits it. */
const DEMO_SPIN_LINES: Record<string, number> = {
  '2.ideal.pc#11': 1,
  '2.normal_OS.tst_donate': 3,
  '2.normal_SO.stsd': 2,
};
/** A plain `t` the engine credited as a spin. Measured empty. */
const DEMO_SPIN_EXCEPTIONS: string[] = [];
/** The two drawings the page colours inconsistently; their demos build the piece the cells must be. */
const DEMO_PIECE_READINGS = ['2.i_early.pc#11', '2.ideal.pc#16'];

// the checks are the shared ones (`route-demo-checks.ts`), bound to 迷走砲's profile and lists
const { routes, byId, checkAll, committedText, committed } = demoChecks(MEISOU, {
  unbuilt: DEMO_UNBUILT, spinLines: DEMO_SPIN_LINES, spinExceptions: DEMO_SPIN_EXCEPTIONS,
  pieceReadings: DEMO_PIECE_READINGS, hold: { node: 'bag1.z_hold', piece: 'Z' },
});

// ── the tests ─────────────────────────────────────────────────────────────────────────────────

let BUILT: string | null = null;
const built = () => (BUILT ??= serialise(build()));

test('rebuilding reproduces the committed stray-cannon-demos.json byte for byte', () => {
  expect(built()).toBe(committedText());
}, 120_000);

test('every demo re-runs, reaches its node, ends on its drawing; the lists are exact', () => {
  const art = committed();
  expect(art.report_eligible).toBe(false);
  expect(art.constructed).toBe(true);
  expect(checkAll(art)).toBeNull();
  // the chain the page calls 基本形 is one demo's chain, not a second demo
  const basic = art.demos.filter((d: any) => d.also.length).map((d: any) => [d.node, d.also]);
  expect(basic).toEqual([['bag1.z_right', ['basic.1']], ['2.ideal', ['basic.2']], ['2.ideal.pc#3', ['basic.3']]]);
  // the readings are exactly the drawings the routes gate names as colour discrepancies
  expect([...DEMO_PIECE_READINGS].sort()).toEqual((routes as any).known_discrepancies
    .filter((k: any) => k.id.endsWith(':colour')).map((k: any) => k.id.replace(/:colour$/, '')).sort());
  // every demo's chain is its node's ancestry
  for (const d of art.demos) expect(chainOf(byId.get(d.node)!, routes).map(n => n.id)).toEqual(d.chain);
}, 120_000);

test('data mutants: each planted defect is caught', () => {
  const fresh = () => JSON.parse(committedText());
  const pick = (a: any, id: string) => a.demos.find((d: any) => d.node === id);
  const muts: [string, (a: any) => void][] = [
    ['a place moved one column', a => { const d = pick(a, '2.ideal.pc#3'); d.locks[17][1] += 1; }],
    ['an input deleted', a => {
      const d = pick(a, '2.ideal');
      const k = d.inputs.findIndex((x: any) => x[1] === 'keydown' && /rotate/.test(x[2]) && x[0] > 400);
      d.inputs.splice(k, 1);
    }],
    ['a TST spin code 2 -> 1', a => { const d = pick(a, '2.ideal'); d.locks[13][3] = 1; }],
    ['2.ideal bag 2 with O before J', a => {
      const d = pick(a, '2.ideal'); const q = d.bags[1].queue;
      d.bags[1].queue = q.replace('J', '#').replace('O', 'J').replace('#', 'O');
      d.seq = d.bags.map((b: any) => b.queue).join('') + d.seq.slice(14);
    }],
    ['a piece swapped between bags', a => { const d = pick(a, 'bag1.z_right'); d.seq = d.seq[7] + d.seq.slice(1, 7) + d.seq[0] + d.seq.slice(8); }],
    ['a child prefix diverges', a => { const d = pick(a, '2.ideal.pc#1'); d.locks[3][0] += 1; }],
    ['a demo removed', a => { a.demos = a.demos.filter((d: any) => d.node !== '2.i_early.pc#4'); }],
    ['an unbuilt entry removed', a => { a.unbuilt = a.unbuilt.slice(1); }],
    ['a U fired as a plain T', a => { const d = pick(a, '2.normal_SO.stsd'); d.letters = d.letters.slice(0, -1) + 't'; }],
  ];
  for (const [what, f] of muts) {
    const a = fresh(); f(a);
    expect(checkAll(a), what).not.toBeNull();
  }
}, 120_000);

test('planner mutants: each rule turned off fails a check or throws', () => {
  for (const m of ['noRowMap', 'noReach', 'noSpinCheck'] as (keyof DemoMutants)[]) {
    let verdict: string | null;
    try { verdict = checkAll(JSON.parse(serialise(build({ [m]: true })))); } catch (e) { verdict = String(e); }
    expect(verdict, m).not.toBeNull();
  }
}, 300_000);

/** Two CONTROLS, measured rather than assumed: each changes which queue or path is chosen (so the
 *  byte rebuild goes red) and every check still passes. `ignoreConditions`: in every drawing the
 *  page's order conditions (%J>%O, %O>%S, ...) are what gravity already requires, so a planner that
 *  ignores them still deals a queue that meets them. `no180`: no demo needs a 180. If either ever
 *  starts failing a check, it has become a mutant like the three above. */
test('controls: ignoreConditions and no180 change the build and break nothing', () => {
  for (const m of ['ignoreConditions', 'no180'] as (keyof DemoMutants)[]) {
    const text = serialise(build({ [m]: true }));
    expect(text === built(), m).toBe(false);
    expect(checkAll(JSON.parse(text)), m).toBeNull();
  }
}, 300_000);

test('reach() finds no path into an enclosed cavity, and finds one into the same cavity opened', () => {
  const eng = newEngine(routes);
  const grid: (string | null)[][] = Array.from({ length: ROWS }, () => new Array(WIDTH).fill(null));
  // rows 0-1 full except a T-down slot at columns 4-6 / 5; rows 2-3 a solid roof
  for (let y = 0; y < 4; y++) for (let x = 0; x < WIDTH; x++) grid[y]![x] = 'G';
  for (const [x, y] of [[4, 1], [5, 1], [6, 1], [5, 0]]) grid[y]![x] = null;
  const target = [[4, 1], [5, 1], [6, 1], [5, 0]].map(([x, y]) => y! * WIDTH + x!);
  expect(reach(eng, grid, 'T', target)).toEqual([]);
  for (let y = 2; y < 4; y++) for (const x of [4, 5, 6]) grid[y]![x] = null;
  expect(reach(eng, grid, 'T', target).length).toBeGreaterThan(0);
});

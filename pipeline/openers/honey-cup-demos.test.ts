/**
 * The はちみつ砲 constructed demos (`analysis/honey-cup-demos.json`, from
 * `pipeline/sim/emit-route-demos.ts --opener honeycup`; the planner is the shared `route-demos.ts`,
 * the opener's half is `demos` in `route-profile-honeycup.ts`).
 *
 *   1. byte rebuild: the committed artefact is what `build()` produces now.
 *   2-8. the shared demo checks (`route-demo-checks.ts`): re-run through `instrumentEngine`, the
 *      corpus classifier reaches the demo's node, board equality against the drawing, spins, whole
 *      7-bags under the page's conditions, prefix sharing, completeness.
 *   9. はちみつ砲's own: the bag-1 J is held because it arrives AFTER L (the page: 遅いほうはホールド);
 *      the hold box carries it into bag 2, and every Perfect Clear ends with the piece its pattern does
 *      not use still held; the five 2.ideal forms' PC patterns run through 2.ideal#1 (`chainVia`).
 *  10. mutants: each planner rule turned off, and each planted artefact defect, turns a check red;
 *      `no180` is a measured CONTROL, `ignoreConditions` here is a MUTANT (see its test).
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/honey-cup-demos.test.ts   (well under a minute)
 */
import { test, expect } from 'bun:test';
import { build as buildFor, serialise, chainOf, type DemoMutants } from '../sim/route-demos.ts';
import { queueStates } from '../sim/emit-replay.ts';
import { HONEYCUP } from '../sim/route-profile-honeycup.ts';
import { demoChecks } from './route-demo-checks.ts';

/** Nodes with a board and no demo, and the reason the artefact gives. A node the planner cannot
 *  build is a red build until it is named here. The illustrations, the mirror and the B-cell REN
 *  board are the profile's; `2.compromise.roof.after` is the planner's measured failure: the page
 *  draws it AFTER its TSD cleared the two rows under it, so its bottom rows are not the board the
 *  L roof's demo leaves. */
const DEMO_UNBUILT: Record<string, string> = {
  'bag1.l_hold': '係「第一巡 六粒形」左右反轉（J↔L、S↔Z），逐格對過；用頁面嘅反轉掣睇',
  '2.ideal.tst': '示意圖：五個理想形共用嘅 TST，每個 2.ideal#k 示範嘅最後一粒就係呢下 TST',
  '2.ideal.after_tst': '示意圖：TST 之後嘅盤面，即係每個 2.ideal#k 示範打完之後嘅盤面',
  '2.compromise.tst': '示意圖：2.compromise 示範嘅最後一粒就係呢下 TST',
  '2.ideal.fire.stmb_template': '「p」格冇指定填法；佢嘅例就係 stmb_example 嘅示範',
  '2.ideal.ren4': '「B」格係我哋嘅讀法（REN 區，13 格，唔係一粒粒方塊），冇得逐粒砌',
  '2.compromise.roof.after': '畫咗嘅舊格唔係上一層示範留低嘅盤面（第 1 欄，由底數第 0 行）',
};
/** The line count of every U lock the drawing does not fix (a bag-2 U is a TST, a PC `t` in the
 *  TSD slot a TSD; these are the rest), as the engine credits it. */
const DEMO_SPIN_LINES: Record<string, number> = {
  '2.compromise.tst_donate': 3,
  '2.compromise.tst_donate.after': 2,
};
/** A plain `t` the engine credited as a spin. Measured empty: pc#12-#15 put the T across a cleared
 *  row and the engine credits no spin. */
const DEMO_SPIN_EXCEPTIONS: string[] = [];
/** Colour-read drawings: the page colours every piece consistently. Measured empty. */
const DEMO_PIECE_READINGS: string[] = [];

const C = demoChecks(HONEYCUP, {
  unbuilt: DEMO_UNBUILT, spinLines: DEMO_SPIN_LINES, spinExceptions: DEMO_SPIN_EXCEPTIONS,
  pieceReadings: DEMO_PIECE_READINGS, hold: { node: 'bag1.j_hold', piece: 'J' },
});
const { routes, byId, committedText, committed } = C;

/** はちみつ砲's own checks, then the shared ones. */
function checkAll(art: any): string | null {
  for (const d of art.demos) {
    const q = queueStates(d.seq, d.locks);
    const last = d.locks.length - 1;
    // 9a. the bag-1 J is held only when it comes after L
    if (d.bags[0].node === 'bag1.j_hold') {
      const b = d.bags[0].queue;
      if (!(b.indexOf('L') < b.indexOf('J'))) return `${d.node}: bag 1 ${b} holds J that came before L`;
    }
    // 9b. a bag-2 board places the held J out of the hold box
    const n = byId.get(d.node)! as any;
    if (n.bag === 2 && !d.letters.slice(6, 14).includes('J')) return `${d.node}: the held J is never placed`;
    // 9c. a Perfect Clear ends with the pattern's unused piece in the hold box
    if (n.list && q[last]!.hold !== n.missing.toUpperCase()) return `${d.node}: hold box ${q[last]!.hold}, not ${n.missing}`;
  }
  return C.checkAll(art);
}

let BUILT: string | null = null;
const built = () => (BUILT ??= serialise(buildFor(HONEYCUP)));

test('rebuilding reproduces the committed honey-cup-demos.json byte for byte', () => {
  expect(built()).toBe(committedText());
}, 120_000);

test('every demo re-runs, reaches its node, ends on its drawing; the lists are exact', () => {
  const art = committed();
  expect(art.report_eligible).toBe(false);
  expect(art.constructed).toBe(true);
  expect(checkAll(art)).toBeNull();
  // the page's three 基本形 are demos' chains, not more demos
  const basic = art.demos.filter((d: any) => d.also.length).map((d: any) => [d.node, d.also]);
  expect(basic).toEqual([['bag1.j_right', ['basic.1']], ['2.ideal#3', ['basic.2']], ['2.ideal.pc#1', ['basic.3']]]);
  // every demo's chain is its node's ancestry, through 2.ideal#1 for the shared after-TST board
  for (const d of art.demos)
    expect(chainOf(byId.get(d.node)!, routes, HONEYCUP.tag, HONEYCUP.demos!.chainVia).map(n => n.id)).toEqual(d.chain);
  for (const d of art.demos.filter((x: any) => x.node.startsWith('2.ideal.pc#')))
    expect(d.chain.slice(0, 2), d.node).toEqual(['bag1.j_hold', '2.ideal#1']);
  // every PC pattern of the page has a demo: none of the fifteen is unbuilt
  expect(art.demos.filter((d: any) => byId.get(d.node)!.list).length)
    .toBe(routes.nodes.filter(n => n.list).length);
}, 120_000);

test('data mutants: each planted defect is caught', () => {
  const fresh = () => JSON.parse(committedText());
  const pick = (a: any, id: string) => a.demos.find((d: any) => d.node === id);
  const muts: [string, (a: any) => void][] = [
    ['a place moved one column', a => { const d = pick(a, '2.ideal.pc#3'); d.locks[17][1] += 1; }],
    ['an input deleted', a => {
      const d = pick(a, '2.ideal#4');
      const k = d.inputs.findIndex((x: any) => x[1] === 'keydown' && /rotate/.test(x[2]) && x[0] > 200);
      d.inputs.splice(k, 1);
    }],
    ['a TST spin code 2 -> 1', a => { const d = pick(a, '2.ideal#1'); d.locks[13][3] = 1; }],
    ['a PC pattern\'s TSD spin code 2 -> 0', a => { const d = pick(a, '2.ideal.pc#2'); d.locks[17][3] = 0; }],
    ['2.compromise bag 2 with J before L', a => {
      const d = pick(a, '2.compromise'); const q = d.bags[1].queue;
      d.bags[1].queue = q.replace('J', '#').replace('L', 'J').replace('#', 'L');
      d.seq = d.bags.map((b: any) => b.queue).join('') + d.seq.slice(14);
    }],
    ['bag 1 with J before L', a => {
      const d = pick(a, 'bag1.j_hold'); const q = d.bags[0].queue;
      d.bags[0].queue = q.replace('J', '#').replace('L', 'J').replace('#', 'L');
      d.seq = d.bags[0].queue + d.seq.slice(7);
    }],
    ['a piece swapped between bags', a => { const d = pick(a, '2.ideal#3'); d.seq = d.seq[7] + d.seq.slice(1, 7) + d.seq[0] + d.seq.slice(8); }],
    ['a child prefix diverges', a => { const d = pick(a, '2.ideal.pc#1'); d.locks[3][0] += 1; }],
    ['a PC ends holding another piece', a => { const d = pick(a, '2.ideal.pc#7'); d.seq = d.seq.slice(0, 14) + 'S' + d.seq.slice(15); }],
    ['a demo removed', a => { a.demos = a.demos.filter((d: any) => d.node !== '2.ideal.pc#14'); }],
    ['an unbuilt entry removed', a => { a.unbuilt = a.unbuilt.slice(1); }],
    ['a U fired as a plain T', a => { const d = pick(a, '2.compromise.tst_donate'); d.letters = d.letters.slice(0, -1) + 't'; }],
  ];
  for (const [what, f] of muts) {
    const a = fresh(); f(a);
    expect(checkAll(a), what).not.toBeNull();
  }
}, 120_000);

test('planner mutants: each rule turned off fails a check or throws', () => {
  for (const m of ['noRowMap', 'noReach', 'noSpinCheck'] as (keyof DemoMutants)[]) {
    let verdict: string | null;
    try { verdict = checkAll(JSON.parse(serialise(buildFor(HONEYCUP, { [m]: true })))); } catch (e) { verdict = String(e); }
    expect(verdict, m).not.toBeNull();
  }
}, 300_000);

/** `no180` is a CONTROL, measured: it changes which paths are chosen (the byte rebuild goes red) and
 *  every check still passes, so no はちみつ砲 demo needs a 180. `ignoreConditions` is NOT a control
 *  here, which is the difference from 迷走砲 worth recording: dropping the page's bag-1 order
 *  (I>L>S) deals J before L, so the held J is the EARLIER of the two, against the page's own rule
 *  (9a) — the condition is not entailed by the board here, it is what the hold depends on. */
test('controls and the ignoreConditions mutant', () => {
  const text = serialise(buildFor(HONEYCUP, { no180: true }));
  expect(text === built(), 'no180 changes the build').toBe(false);
  expect(checkAll(JSON.parse(text)), 'no180').toBeNull();
  let verdict: string | null;
  try { verdict = checkAll(JSON.parse(serialise(buildFor(HONEYCUP, { ignoreConditions: true })))); }
  catch (e) { verdict = String(e); }
  expect(verdict, 'ignoreConditions').not.toBeNull();
}, 300_000);

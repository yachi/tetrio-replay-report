/**
 * The 山岳積み2号 constructed demos (`analysis/mountainous2-demos.json`, from
 * `pipeline/sim/emit-route-demos.ts --opener mountainous2`; the planner is the shared `route-demos.ts`,
 * the opener's half is `demos` in `route-profile-mountainous2.ts`).
 *
 *   1. byte rebuild: the committed artefact is what `build()` produces now.
 *   2-8. the shared demo checks (`route-demo-checks.ts`): re-run through `instrumentEngine`, the
 *      corpus classifier reaches the demo's node (the 4-line and 14-line PC kinds included), board
 *      equality against the drawing, spins, whole 7-bags under the page's conditions, prefix
 *      sharing, completeness.
 *   9. 山岳積み2号's own: the bag-1 L is held only by bag1.l_hold, and only the boards drawn on the
 *      L-held board (2.normal#3, the 4-line PCs) place it out of the hold box; a 4-line PC is the
 *      tenth lock with no spin before it; a 5巡目 PC clears 14 lines over TST + TSD + TSD; the PC
 *      patterns and later boards run through the demo that ends on the page's after-the-spin
 *      illustration (`chainVia`).
 *  10. mutants: each planner rule turned off, and each planted artefact defect, turns a check red;
 *      `no180` and `ignoreConditions` are measured CONTROLS here (see their test).
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/mountainous2-demos.test.ts   (well under a minute)
 */
import { test, expect } from 'bun:test';
import { build as buildFor, serialise, chainOf, type DemoMutants } from '../sim/route-demos.ts';
import { MOUNTAINOUS2, tsdT } from '../sim/route-profile-mountainous2.ts';
import { demoChecks } from './route-demo-checks.ts';

/** Nodes with a board and no demo, and the reason the artefact gives. A node the planner cannot
 *  build is a red build until it is named here. The mirror and the five after-the-spin
 *  illustrations are the profile's; `2.ideal.pc#9` is the planner's measured failure: its T stands
 *  upright in the slot under the S, and every order that reaches it the engine credits as a spin,
 *  while the drawing gives it as a plain `t` (not the TSD slot, so not a spin letter). */
const DEMO_UNBUILT: Record<string, string> = {
  'bag1.j_top': '係原頁左邊嗰幅第一巡圖左右反轉（J↔L、S↔Z），逐格對過；用頁面嘅反轉掣睇',
  '2.ideal.after': '示意圖：TST 之後嘅盤面，即係 2.ideal 示範打完之後嘅盤面',
  '2.normal.after': '示意圖：三個通常形 TST 之後共用嘅盤面，即係 2.normal#1 示範打完之後嘅盤面',
  '2.compromise.after': '示意圖：TST 之後嘅盤面，即係 2.compromise 示範打完之後嘅盤面',
  '2.compromise.fire5.after': '示意圖：兩個 5巡パフェ 3巡目形 TSD 之後共用嘅盤面，即係 2.compromise.fire5#1 示範打完之後嘅盤面',
  '2.compromise.fire5.bag4.after': '示意圖：兩個 4巡目形 TSD 之後共用嘅盤面，即係 2.compromise.fire5.bag4#1 示範打完之後嘅盤面',
  '2.ideal.pc#9': '最遠放到 ZOI；之後：T 行到去但引擎判嘅 spin 唔啱；S 由出生位行唔到去；L 中間隔住嘅行未消，未成形',
};
/** U line counts the drawing does not fix: measured empty — every U here is a bag-2 TST or a board
 *  the page names a TSD (`spin`), and every spin `t` is a PC's TSD-slot T. */
const DEMO_SPIN_LINES: Record<string, number> = {};
/** A plain `t` the engine credited as a spin. Measured empty: the one drawing where every order
 *  spins it (2.ideal.pc#9) is unbuilt instead, never built under an exception. */
const DEMO_SPIN_EXCEPTIONS: string[] = [];
/** Colour-read drawings: every letter on every board is whole pieces (the transcription's rule).
 *  Measured empty. */
const DEMO_PIECE_READINGS: string[] = [];

/** The PC patterns whose `t` is the TSD's T (its four cells the base's bottom slot), and nothing else. */
const TSD_T_PATTERNS = ['2.ideal.pc#1', '2.ideal.pc#2', '2.ideal.pc#3', '2.ideal.pc#4', '2.ideal.pc#5',
                        '2.ideal.pc#6', '2.ideal.pc#7', '2.normal.pc#1', '2.normal.pc#2', '2.normal.pc#3'];

const C = demoChecks(MOUNTAINOUS2, {
  unbuilt: DEMO_UNBUILT, spinLines: DEMO_SPIN_LINES, spinExceptions: DEMO_SPIN_EXCEPTIONS,
  pieceReadings: DEMO_PIECE_READINGS, hold: { node: 'bag1.l_hold', piece: 'L' },
});
const { routes, byId, committedText, committed } = C;

/** 山岳積み2号's own checks, then the shared ones. */
function checkAll(art: any): string | null {
  for (const d of art.demos) {
    const n = byId.get(d.node)! as any;
    const onHold = d.chain[0] === 'bag1.l_hold';
    // 9a. only the L-held chain holds, and its bag 1 holds exactly the L
    if (!onHold && d.locks.some((l: any) => l[5])) return `${d.node}: holds off the L-held chain`;
    if (onHold && d.bags[0].holds !== 1) return `${d.node}: bag 1 holds ${d.bags[0].holds}`;
    // 9b. a board drawn on the L-held board places the carried L in bag 2 (its upper-case L)
    if (onHold && n.bag === 2 && !d.letters.slice(6).includes('L')) return `${d.node}: the held L is never placed`;
    // 9c. a 4-line PC is the tenth lock, with no spin before it
    if (n.list === '2.pc4') {
      if (d.locks.length !== 10 || d.events.length !== 1 || d.events[0].kind !== 'PC') return `${d.node}: not a lone 4-line PC`;
    }
    // 9d. a 5巡目 PC is TST + TSD + TSD, then the PC: 14 lines
    if (n.list === '2.compromise.fire5.pc') {
      const k = d.events.map((e: any) => e.kind).join(' ');
      if (k !== 'TST TSD TSD PC' || d.events.at(-1).lines !== 14) return `${d.node}: events ${k}`;
    }
  }
  return C.checkAll(art);
}

let BUILT: string | null = null;
const built = () => (BUILT ??= serialise(buildFor(MOUNTAINOUS2)));

test('rebuilding reproduces the committed mountainous2-demos.json byte for byte', () => {
  expect(built()).toBe(committedText());
}, 120_000);

test('every demo re-runs, reaches its node, ends on its drawing; the lists are exact', () => {
  const art = committed();
  expect(art.report_eligible).toBe(false);
  expect(art.constructed).toBe(true);
  expect(checkAll(art)).toBeNull();
  // the page's three 基本形 are demos' chains, not more demos
  const basic = art.demos.filter((d: any) => d.also.length).map((d: any) => [d.node, d.also]);
  expect(basic).toEqual([['bag1.l_top', ['basic.1']], ['2.ideal', ['basic.2']], ['2.ideal.pc#3', ['basic.3']]]);
  // every demo's chain is its node's ancestry, through the demo that ends on each illustration
  for (const d of art.demos)
    expect(chainOf(byId.get(d.node)!, routes, MOUNTAINOUS2.tag, MOUNTAINOUS2.demos!.chainVia).map(n => n.id)).toEqual(d.chain);
  for (const d of art.demos.filter((x: any) => x.node.startsWith('2.normal.pc#')))
    expect(d.chain.slice(0, 2), d.node).toEqual(['bag1.l_top', '2.normal#1']);
  for (const d of art.demos.filter((x: any) => x.node.startsWith('2.compromise.fire5.pc#')))
    expect(d.chain.slice(2, 4), d.node).toEqual(['2.compromise.fire5#1', '2.compromise.fire5.bag4#1']);
  // the L-held chain is exactly the boards drawn on the L-held board
  expect(art.demos.filter((d: any) => d.chain[0] === 'bag1.l_hold').map((d: any) => d.node))
    .toEqual(['bag1.l_hold', '2.pc4#1', '2.pc4#2', '2.pc4#3', '2.normal#3']);
  // the spin-letter rule picks exactly the TSD-slot patterns
  expect(routes.nodes.filter(n => tsdT(n, routes)).map(n => n.id)).toEqual(TSD_T_PATTERNS);
  // every PC pattern but the one named unbuilt has a demo
  expect(art.demos.filter((d: any) => byId.get(d.node)!.list).length)
    .toBe(routes.nodes.filter(n => n.list).length - 1);
}, 120_000);

test('data mutants: each planted defect is caught', () => {
  const fresh = () => JSON.parse(committedText());
  const pick = (a: any, id: string) => a.demos.find((d: any) => d.node === id);
  const muts: [string, (a: any) => void][] = [
    ['a place moved one column', a => { const d = pick(a, '2.ideal.pc#3'); d.locks[17][1] += 1; }],
    ['an input deleted', a => {
      const d = pick(a, '2.ideal');
      const k = d.inputs.findIndex((x: any) => x[1] === 'keydown' && /rotate/.test(x[2]) && x[0] > 200);
      d.inputs.splice(k, 1);
    }],
    ['a TST spin code 2 -> 1', a => { const d = pick(a, '2.normal#1'); d.locks[13][3] = 1; }],
    ['a PC pattern\'s TSD spin code 2 -> 0', a => { const d = pick(a, '2.ideal.pc#2'); d.locks[18][3] = 0; }],
    ['2.ideal bag 2 with O before S', a => {
      const d = pick(a, '2.ideal'); const q = d.bags[1].queue;
      d.bags[1].queue = q.replace('S', '#').replace('O', 'S').replace('#', 'O');
      d.seq = d.bags.map((b: any) => b.queue).join('') + d.seq.slice(14);
    }],
    ['a piece swapped between bags', a => { const d = pick(a, '2.compromise'); d.seq = d.seq[7] + d.seq.slice(1, 7) + d.seq[0] + d.seq.slice(8); }],
    ['a child prefix diverges', a => { const d = pick(a, '2.compromise.fire5.pc#3'); d.locks[3][0] += 1; }],
    ['a 4-line PC\'s held L never released', a => { const d = pick(a, '2.pc4#1'); d.locks[8][5] = 0; }],
    ['a hold flag on the L-top chain', a => { const d = pick(a, '2.normal#2'); d.locks[9][5] = 1; }],
    ['a demo removed', a => { a.demos = a.demos.filter((d: any) => d.node !== '2.compromise.fire5.pc#6'); }],
    ['an unbuilt entry removed', a => { a.unbuilt = a.unbuilt.slice(1); }],
    ['a U fired as a plain T', a => { const d = pick(a, '2.compromise.fire34'); d.letters = d.letters.slice(0, -1) + 't'; }],
  ];
  for (const [what, f] of muts) {
    const a = fresh(); f(a);
    expect(checkAll(a), what).not.toBeNull();
  }
}, 120_000);

test('planner mutants: each rule turned off fails a check or throws', () => {
  for (const m of ['noRowMap', 'noReach', 'noSpinCheck'] as (keyof DemoMutants)[]) {
    let verdict: string | null;
    try { verdict = checkAll(JSON.parse(serialise(buildFor(MOUNTAINOUS2, { [m]: true })))); } catch (e) { verdict = String(e); }
    expect(verdict, m).not.toBeNull();
  }
}, 300_000);

/** Both are CONTROLS here, measured: each changes which paths or queues are chosen (the byte
 *  rebuild goes red) and every check still passes. `no180`: no demo needs a 180. `ignoreConditions`:
 *  as on 迷走砲 and unlike はちみつ砲, the page's order conditions (bag 1 J before Z, 2.ideal S before
 *  O, 2.compromise O before S) are what the drawn boards' gravity already requires, so dropping them
 *  deals queues that still satisfy them. Either failing a check later means it has become a mutant. */
const CONTROLS: (keyof DemoMutants)[] = ['no180', 'ignoreConditions'];

test('controls: no180 and ignoreConditions change the build and break nothing', () => {
  for (const m of CONTROLS) {
    const text = serialise(buildFor(MOUNTAINOUS2, { [m]: true }));
    expect(text === built(), `${m} changes the build`).toBe(false);
    expect(checkAll(JSON.parse(text)), m).toBeNull();
  }
}, 300_000);

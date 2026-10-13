/**
 * The ガムシロ積み (Gamushiro Stacking) constructed demos (`analysis/gamushiro-demos.json`, from
 * `pipeline/sim/emit-route-demos.ts --opener gamushiro`; the planner is the shared `route-demos.ts`,
 * the opener's half is `demos` in `route-profile-gamushiro.ts`).
 *
 *   1. byte rebuild: the committed artefact is what `build()` produces now.
 *   2-8. the shared demo checks (`route-demo-checks.ts`): re-run through `instrumentEngine`, the
 *      corpus classifier reaches the demo's node, board equality against the drawing, spins, whole
 *      7-bags under the page's conditions, prefix sharing, completeness.
 *   9. ガムシロ積み's own: only the L-held chain holds, and its bag 1 holds exactly the L; every bag 1
 *      keeps the page's no-hold conditions for the left pattern (J before S, Z before T); the held L
 *      is placed in bag 2; a 4-line PC is the tenth lock with no spin before it; the 8-line PCs are
 *      TST (+ TSD where the T sits in the TSD slot) + PC; the Imperial Cross boards end on the drawing
 *      after the TST.
 *  10. mutants: each planner rule turned off, and each planted artefact defect, turns a check red;
 *      `no180` is a measured CONTROL, `ignoreConditions` a measured MUTANT here (see their tests).
 *
 * NOT CORPUS DATA. Nobody played these games — least of all in this corpus, which reaches the page's
 * bag 1 once (`gamushiro.test.ts`).
 *
 * Run: bun test pipeline/openers/gamushiro-demos.test.ts   (well under a minute)
 */
import { test, expect } from 'bun:test';
import { build as buildFor, serialise, chainOf, type DemoMutants } from '../sim/route-demos.ts';
import { GAMUSHIRO, tsdT, TSD_NOT_FIRED } from '../sim/route-profile-gamushiro.ts';
import { demoChecks } from './route-demo-checks.ts';
import { conditionHolds } from '../sim/route-facts.ts';

/** Nodes with a board and no demo, and the reason the artefact gives. A node the planner cannot
 *  build is a red build until it is named here. The mirror, the three illustrations and the
 *  commented-out template are the profile's; `2.compromise` is the planner's measured failure, and
 *  the reason is the page's TRIGGER, not the board: 「%T>%L%O」 (T dealt before L and O). The planner
 *  reads a `before` pair as PLACEMENT order, and the T is fired last (the TST), so L and O wait on a
 *  piece that is placed after them; it reports 「O 要等 T；L 要等 T」. On the board the order can be
 *  met — the T held on arrival, swapping out the bag-1 L — but the planner deals the T at the held
 *  L's slot only by its own swap rule and does not credit that slot to a `before` pair, so the demo
 *  is not built rather than built with a queue the page's trigger forbids (the ignoreConditions
 *  mutant below builds it, with such a queue). The heading 「%L>%Oの場合」 is no longer a condition:
 *  the transcription names it as a discrepancy (`2.compromise:heading_vs_board`). */
const DEMO_UNBUILT: Record<string, string> = {
  'bag1.right': '係原頁左邊嗰幅第一巡圖左右反轉（J↔L、S↔Z），逐格對過；用頁面嘅反轉掣睇',
  '2.normal.tst': '示意圖：兩個通常形打 TST 嘅位同消嘅三行，即係 2.normal#1 示範最後一粒',
  '2.normal.after': '示意圖：兩個通常形 TST 之後共用嘅盤面，即係 2.normal#1 示範打完之後嘅盤面',
  '2.normal.pc.rest': '「残り55パターン」喺 HTML 註解入面，頁面冇顯示；佢唯一嘅圖係 TST 之後嘅盤面重畫做空白樣板，冇一粒方塊',
  '2.compromise.tst': '示意圖：妥協形打 TST 嘅位同消嘅三行，即係 2.compromise 示範最後一粒',
  '2.compromise': '最遠放到 LJZSI；之後：O 要等 T；L 要等 T；T(U) 要最後先放',
};
/** U line counts the drawing does not fix: measured empty — every U is a bag-2 TST. */
const DEMO_SPIN_LINES: Record<string, number> = {};
/** A plain `t` the engine credited as a spin: measured empty. */
const DEMO_SPIN_EXCEPTIONS: string[] = [];
/** Colour-read drawings: measured empty (every letter is whole pieces, the transcription's rule). */
const DEMO_PIECE_READINGS: string[] = [];

/** The PC patterns fired with a TSD: `t_in_tsd_slot` less TSD_NOT_FIRED (pc#3, measured: the S that
 *  fills the cell beside the slot also roofs it, so the T gets in only by a kick the engine credits
 *  as no full spin; it is built as a plain T, last). pc#4 and pc#8 draw no T in the slot. */
const TSD_T_PATTERNS = ['2.normal.pc#1', '2.normal.pc#2', '2.normal.pc#5', '2.normal.pc#6', '2.normal.pc#7'];

const C = demoChecks(GAMUSHIRO, {
  unbuilt: DEMO_UNBUILT, spinLines: DEMO_SPIN_LINES, spinExceptions: DEMO_SPIN_EXCEPTIONS,
  pieceReadings: DEMO_PIECE_READINGS, hold: { node: 'bag1.left', piece: 'L' },
});
const { routes, byId, committedText, committed } = C;

/** The kinds of T-spin a chain fires, in order, and what it ends on. */
const EVENTS: [RegExp, (id: string) => string][] = [
  [/^bag1\.(left|l_top)$/, () => ''],
  [/^2\.pc4#\d$/, () => 'PC'],
  [/^2\.normal#\d$/, () => 'TST'],
  [/^2\.normal\.pc#\d$/, id => (TSD_T_PATTERNS.includes(id) ? 'TST TSD PC' : 'TST PC')],
  [/^2\.normal\.imperial#\d$/, () => 'TST'],
];

/** ガムシロ積み's own checks, then the shared ones. */
function checkAll(art: any): string | null {
  for (const d of art.demos) {
    const n = byId.get(d.node)! as any;
    const onHold = d.chain[0] === 'bag1.left';
    // 9a. only the L-held chain holds, and its bag 1 holds exactly the L
    if (!onHold && d.locks.some((l: any) => l[5])) return `${d.node}: holds off the L-held chain`;
    if (onHold && (d.bags[0].holds !== 1 || !d.bags[0].order_reading.includes('hold:L@6'))) return `${d.node}: bag 1 does not hold the L`;
    // 9b. every bag 1 keeps the page's no-hold conditions for the left pattern (J before S, Z before T)
    if (conditionHolds((routes as any).bag1.no_hold, d.bags[0].queue, '') !== true)
      return `${d.node}: bag 1 ${d.bags[0].queue} breaks the no-hold conditions`;
    // 9c. a board drawn on the L-held board places the carried L in bag 2 (its upper-case L)
    if (onHold && n.bag >= 2 && !d.letters.slice(6, 14).includes('L')) return `${d.node}: the held L is never placed`;
    // 9d. the chain's spins and its end
    const want = EVENTS.find(([re]) => re.test(d.node))?.[1](d.node);
    const got = d.events.map((e: any) => e.kind).join(' ');
    if (want === undefined || got !== want) return `${d.node}: events ${got}, want ${want}`;
    if (n.list === '2.pc4' && d.locks.length !== 10) return `${d.node}: the 4-line PC is not the tenth lock`;
    if (n.list === '2.normal.pc' && d.events.at(-1).lines !== 8) return `${d.node}: the PC clears ${d.events.at(-1).lines} lines, not 8`;
  }
  return C.checkAll(art);
}

let BUILT: string | null = null;
const built = () => (BUILT ??= serialise(buildFor(GAMUSHIRO)));

test('rebuilding reproduces the committed gamushiro-demos.json byte for byte', () => {
  expect(built()).toBe(committedText());
}, 120_000);

test('every demo re-runs, reaches its node, ends on its drawing; the lists are exact', () => {
  const art = committed();
  expect(art.report_eligible).toBe(false);
  expect(art.constructed).toBe(true);
  expect(checkAll(art)).toBeNull();
  // the page's three 基本形 are demos' nodes, not more demos
  const basic = art.demos.filter((d: any) => d.also.length).map((d: any) => [d.node, d.also]);
  expect(basic).toEqual([['bag1.l_top', ['basic.1']], ['2.normal#1', ['basic.2']], ['2.normal.pc#1', ['basic.3']]]);
  // every demo's chain is its node's ancestry, through the demo that ends on the after-TST board
  for (const d of art.demos)
    expect(chainOf(byId.get(d.node)!, routes, GAMUSHIRO.tag, GAMUSHIRO.demos!.chainVia).map(n => n.id)).toEqual(d.chain);
  for (const d of art.demos.filter((x: any) => /^2\.normal\.(pc|imperial)#/.test(x.node)))
    expect(d.chain.slice(0, 2), d.node).toEqual(['bag1.left', '2.normal#1']);
  // the L-held chain is every board past bag 1: the page draws all of them on the L-held board
  expect(art.demos.filter((d: any) => d.chain[0] !== 'bag1.left').map((d: any) => d.node)).toEqual(['bag1.l_top']);
  // the spin-letter rule picks exactly the TSD patterns, and TSD_NOT_FIRED is the slot flag's remainder
  expect(routes.nodes.filter(n => tsdT(n)).map(n => n.id)).toEqual(TSD_T_PATTERNS);
  expect(routes.nodes.filter((n: any) => n.t_in_tsd_slot && !tsdT(n)).map(n => n.id)).toEqual(Object.keys(TSD_NOT_FIRED));
  // every PC pattern has a demo
  expect(art.demos.filter((d: any) => byId.get(d.node)!.list).length).toBe(routes.nodes.filter(n => n.list).length);
  // bag1.left's demo places six pieces and ends with the L in the hold box
  const left = art.demos.find((d: any) => d.node === 'bag1.left');
  expect([left.locks.length, left.bags[0].unused]).toEqual([6, '']);
}, 120_000);

test('TSD_NOT_FIRED is measured: with pc#3 read as a TSD the planner cannot build it', () => {
  const P = { ...GAMUSHIRO, demos: { ...GAMUSHIRO.demos!, spinLetter: (n: any) => (n.t_in_tsd_slot ? { letter: 't', lines: 2 } : null) } };
  const art = buildFor(P);
  expect(art.unbuilt.map((u: any) => u.node)).toContain('2.normal.pc#3');
  expect(art.unbuilt.find((u: any) => u.node === '2.normal.pc#3').reason).toMatch(/引擎判嘅 spin 唔啱/);
}, 120_000);

test('data mutants: each planted defect is caught', () => {
  const fresh = () => JSON.parse(committedText());
  const pick = (a: any, id: string) => a.demos.find((d: any) => d.node === id);
  const muts: [string, (a: any) => void][] = [
    ['a place moved one column', a => { const d = pick(a, '2.normal.pc#2'); d.locks[17][1] += 1; }],
    ['an input deleted', a => {
      const d = pick(a, '2.normal#2');
      const k = d.inputs.findIndex((x: any) => x[1] === 'keydown' && /rotate/.test(x[2]) && x[0] > 200);
      d.inputs.splice(k, 1);
    }],
    ['a TST spin code 2 -> 1', a => { const d = pick(a, '2.normal#1'); d.locks[13][3] = 1; }],
    ['a PC pattern\'s TSD spin code 2 -> 0', a => {
      const d = pick(a, '2.normal.pc#5'); const i = d.events.find((e: any) => e.kind === 'TSD').lock; d.locks[i][3] = 0;
    }],
    ['2.normal#1 bag 2 with O before L', a => {
      const d = pick(a, '2.normal#1'); const q = d.bags[1].queue;
      d.bags[1].queue = q.replace('L', '#').replace('O', 'L').replace('#', 'O');
      d.seq = d.bags.map((b: any) => b.queue).join('') + d.seq.slice(14);
    }],
    ['bag 1 with S before J', a => {
      const d = pick(a, 'bag1.l_top'); const q = d.bags[0].queue;
      d.bags[0].queue = q.replace('J', '#').replace('S', 'J').replace('#', 'S');
      d.seq = d.bags[0].queue + d.seq.slice(7);
    }],
    ['a piece swapped between bags', a => { const d = pick(a, '2.normal#2'); d.seq = d.seq[7] + d.seq.slice(1, 7) + d.seq[0] + d.seq.slice(8); }],
    ['a child prefix diverges', a => { const d = pick(a, '2.normal.imperial#2'); d.locks[3][0] += 1; }],
    ['the held L never released', a => { const d = pick(a, '2.pc4#2'); const i = d.locks.findIndex((l: any, k: number) => k > 6 && l[5]); d.locks[i][5] = 0; }],
    ['a hold flag on the L-top chain', a => { const d = pick(a, 'bag1.l_top'); d.locks[3][5] = 1; }],
    ['a demo removed', a => { a.demos = a.demos.filter((d: any) => d.node !== '2.normal.pc#8'); }],
    ['an unbuilt entry removed', a => { a.unbuilt = a.unbuilt.slice(1); }],
    ['a U fired as a plain T', a => { const d = pick(a, '2.normal#2'); d.letters = d.letters.slice(0, -1) + 't'; }],
  ];
  for (const [what, f] of muts) {
    const a = fresh(); f(a);
    expect(checkAll(a), what).not.toBeNull();
  }
}, 120_000);

test('planner mutants: each rule turned off fails a check or throws', () => {
  for (const m of ['noRowMap', 'noReach', 'noSpinCheck'] as (keyof DemoMutants)[]) {
    let verdict: string | null;
    try { verdict = checkAll(JSON.parse(serialise(buildFor(GAMUSHIRO, { [m]: true })))); } catch (e) { verdict = String(e); }
    expect(verdict, m).not.toBeNull();
  }
}, 300_000);

/** A MUTANT here, measured, as on はちみつ砲 and unlike 迷走砲, 山岳積み2号 and stick spin: the page's bag-1
 *  no-hold conditions (J before S, Z before T) are NOT forced by gravity — the drawn T stands on the
 *  floor and the Z slides under its nub — so dropping them deals a bag 1 that breaks them, and
 *  2.compromise builds with a queue that breaks its own condition (see DEMO_UNBUILT). */
test('ignoreConditions is a mutant: it deals queues that break the page\'s conditions', () => {
  const art = JSON.parse(serialise(buildFor(GAMUSHIRO, { ignoreConditions: true })));
  expect(checkAll(art)).toMatch(/breaks the (no-hold conditions|page condition)/);
  expect(art.demos.some((d: any) => d.node === '2.compromise')).toBe(true);
}, 300_000);

/** A CONTROL here, measured: it changes which paths are chosen (the byte rebuild goes red) and every
 *  check still passes — no demo needs a 180. Failing a check later means it has become a mutant. */
test('control: no180 changes the build and breaks nothing', () => {
  const text = serialise(buildFor(GAMUSHIRO, { no180: true }));
  expect(text === built(), 'no180 changes the build').toBe(false);
  expect(checkAll(JSON.parse(text))).toBeNull();
}, 300_000);

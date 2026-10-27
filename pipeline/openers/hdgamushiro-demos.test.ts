/**
 * The harddrop ガムシロ積み constructed demos (`analysis/hdgamushiro-demos.json`, from
 * `pipeline/sim/emit-route-demos.ts --opener hdgamushiro`; the planner is the shared `route-demos.ts`,
 * the opener's half is `demos` in `route-profile-hdgamushiro.ts`).
 *
 *   1. byte rebuild: the committed artefact is what `build()` produces now.
 *   2-8. the shared demo checks (`route-demo-checks.ts`): re-run through `instrumentEngine`, the
 *      corpus classifier reaches the demo's node, board equality against the drawing, spins, whole
 *      7-bags under the page's conditions, prefix sharing, completeness.
 *   9. this page's own: only the L-held chain holds, and its bag 1 holds exactly the L; every bag 1
 *      keeps the page's one order (J before S); the held L is placed in bag 2; every form ends on its
 *      TST; the 8-line PCs are TST (+ TSD where the T sits in the TSD slot) + PC, each through the form
 *      whose TST leaves its after board.
 *  10. mutants: each planner rule turned off, and each planted artefact defect, turns a check red;
 *      `no180` and `ignoreConditions` are measured CONTROLS, `noSwapDeal` measured EQUIVALENT.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/hdgamushiro-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { build as buildFor, serialise, chainOf, type DemoMutants } from '../sim/route-demos.ts';
import { HDGAMUSHIRO, tsdT, TSD_NOT_FIRED } from '../sim/route-profile-hdgamushiro.ts';
import { demoChecks } from './route-demo-checks.ts';
import { conditionHolds } from '../sim/route-facts.ts';

/** Nodes with a board and no demo, and the reason the artefact gives: the two mirrors and the six
 *  illustrations (each form family's redraw and after board). Form D IS built: it is too tall for the
 *  classifier, not for the engine. */
const DEMO_UNBUILT: Record<string, string> = {
  'bag1.right': '係 harddrop 第一巡 6 粒圖左右反轉（J↔L、S↔Z），逐格對過；用頁面嘅反轉掣睇',
  'bag1.l_top_right': '係 harddrop 第一巡 7 粒圖左右反轉（J↔L、S↔Z），逐格對過；用頁面嘅反轉掣睇',
  '2.a.redraw': '示意圖：A1 打 TST 前嘅盤面重畫，即係 2.a1 示範最後一粒之前',
  '2.a.after': '示意圖：A1、A2 打完 TST 之後共用嘅盤面，即係 2.a1 示範打完之後嘅盤面',
  '2.b.redraw': '示意圖：B 打 TST 前嘅盤面重畫，即係 2.b 示範最後一粒之前',
  '2.b.after': '示意圖：B 打完 TST 之後嘅盤面，即係 2.b 示範打完之後嘅盤面',
  '2.c.redraw': '示意圖：C 打 TST 前嘅盤面重畫，即係 2.c 示範最後一粒之前',
  '2.c.after': '示意圖：C 打完 TST 之後嘅盤面，即係 2.c 示範打完之後嘅盤面',
};
/** U line counts the drawing does not fix: measured empty — every U is a bag-2 TST. */
const DEMO_SPIN_LINES: Record<string, number> = {};
/** A plain `t` the engine credited as a spin: measured empty. */
const DEMO_SPIN_EXCEPTIONS: string[] = [];
/** Colour-read drawings: measured empty. */
const DEMO_PIECE_READINGS: string[] = [];

/** The PC patterns fired with a TSD: `t_in_tsd_slot` less TSD_NOT_FIRED. */
const TSD_T_PATTERNS = ['2.a.pc#1', '2.a.pc#2', '2.a.pc#5', '2.a.pc#6', '2.b.pc#1', '2.b.pc#3', '2.b.pc#4',
                        '2.b.pc#6', '2.c.pc#4'];
/** The form whose TST leaves each PC family's after board. */
const VIA: Record<string, string> = { '2.a.pc': '2.a1', '2.b.pc': '2.b', '2.c.pc': '2.c' };

const C = demoChecks(HDGAMUSHIRO, {
  unbuilt: DEMO_UNBUILT, spinLines: DEMO_SPIN_LINES, spinExceptions: DEMO_SPIN_EXCEPTIONS,
  pieceReadings: DEMO_PIECE_READINGS, hold: { node: 'bag1.left', piece: 'L' },
});
const { routes, byId, committedText, committed } = C;

const EVENTS: [RegExp, (id: string) => string][] = [
  [/^bag1\.(left|l_top)$/, () => ''],
  [/^2\.(a1|a2|b|c|d)$/, () => 'TST'],
  [/^2\.[abc]\.pc#\d$/, id => (TSD_T_PATTERNS.includes(id) ? 'TST TSD PC' : 'TST PC')],
];

function checkAll(art: any): string | null {
  for (const d of art.demos) {
    const n = byId.get(d.node)! as any;
    const onHold = d.chain[0] === 'bag1.left';
    if (!onHold && d.locks.some((l: any) => l[5])) return `${d.node}: holds off the L-held chain`;
    if (onHold && (d.bags[0].holds !== 1 || !d.bags[0].order_reading.some((r: string) => r.startsWith('hold:L@'))))
      return `${d.node}: bag 1 does not hold the L`;
    if (conditionHolds((routes as any).bag1.requires, d.bags[0].queue, '') !== true)
      return `${d.node}: bag 1 ${d.bags[0].queue} breaks the page's order`;
    if (onHold && n.bag >= 2 && !d.letters.slice(6, 14).includes('L')) return `${d.node}: the held L is never placed`;
    const want = EVENTS.find(([re]) => re.test(d.node))?.[1](d.node);
    const got = d.events.map((e: any) => e.kind).join(' ');
    if (want === undefined || got !== want) return `${d.node}: events ${got}, want ${want}`;
    if (n.list && d.events.at(-1).lines !== 8) return `${d.node}: the PC clears ${d.events.at(-1).lines} lines, not 8`;
  }
  return C.checkAll(art);
}

let BUILT: string | null = null;
const built = () => (BUILT ??= serialise(buildFor(HDGAMUSHIRO)));

test('rebuilding reproduces the committed hdgamushiro-demos.json byte for byte', () => {
  expect(built()).toBe(committedText());
}, 120_000);

test('every demo re-runs, reaches its node, ends on its drawing; the lists are exact', () => {
  const art = committed();
  expect(art.report_eligible).toBe(false);
  expect(art.constructed).toBe(true);
  expect(checkAll(art)).toBeNull();
  for (const d of art.demos)
    expect(chainOf(byId.get(d.node)!, routes, HDGAMUSHIRO.tag, HDGAMUSHIRO.demos!.chainVia).map(n => n.id)).toEqual(d.chain);
  for (const d of art.demos) {
    const n = byId.get(d.node) as any;
    if (n.list) expect(d.chain, d.node).toEqual(['bag1.left', VIA[n.list], d.node]);
  }
  expect(art.demos.filter((d: any) => d.chain[0] !== 'bag1.left').map((d: any) => d.node)).toEqual(['bag1.l_top']);
  expect(routes.nodes.filter(n => tsdT(n)).map(n => n.id)).toEqual(TSD_T_PATTERNS);
  expect(routes.nodes.filter((n: any) => n.t_in_tsd_slot && !tsdT(n)).map(n => n.id)).toEqual(Object.keys(TSD_NOT_FIRED));
  expect(art.demos.filter((d: any) => byId.get(d.node)!.list).length).toBe(routes.nodes.filter(n => n.list).length);
  expect(art.demos.some((d: any) => d.node === '2.d')).toBe(true);
  const left = art.demos.find((d: any) => d.node === 'bag1.left');
  expect([left.locks.length, left.bags[0].unused]).toEqual([6, '']);
}, 120_000);

test('TSD_NOT_FIRED is measured: with each read as a TSD the planner cannot build it', () => {
  const P = { ...HDGAMUSHIRO, demos: { ...HDGAMUSHIRO.demos!, spinLetter: (n: any) => (n.t_in_tsd_slot ? { letter: 't', lines: 2 } : null) } };
  const art = buildFor(P);
  for (const id of Object.keys(TSD_NOT_FIRED)) {
    expect(art.unbuilt.map((u: any) => u.node), id).toContain(id);
    expect(art.unbuilt.find((u: any) => u.node === id).reason, id).toMatch(/引擎判嘅 spin 唔啱/);
  }
}, 120_000);

test('data mutants: each planted defect is caught', () => {
  const fresh = () => JSON.parse(committedText());
  const pick = (a: any, id: string) => a.demos.find((d: any) => d.node === id);
  const muts: [string, (a: any) => void][] = [
    ['a place moved one column', a => { const d = pick(a, '2.a.pc#2'); d.locks[17][1] += 1; }],
    ['an input deleted', a => {
      const d = pick(a, '2.b');
      const k = d.inputs.findIndex((x: any) => x[1] === 'keydown' && /rotate/.test(x[2]) && x[0] > 200);
      d.inputs.splice(k, 1);
    }],
    ['a TST spin code 2 -> 1', a => { const d = pick(a, '2.a1'); d.locks[13][3] = 1; }],
    ['a PC pattern\'s TSD spin code 2 -> 0', a => {
      const d = pick(a, '2.b.pc#3'); const i = d.events.find((e: any) => e.kind === 'TSD').lock; d.locks[i][3] = 0;
    }],
    ['bag 1 with S before J', a => {
      const d = pick(a, 'bag1.l_top'); const q = d.bags[0].queue;
      d.bags[0].queue = q.replace('J', '#').replace('S', 'J').replace('#', 'S');
      d.seq = d.bags[0].queue + d.seq.slice(7);
    }],
    ['a piece swapped between bags', a => { const d = pick(a, '2.c'); d.seq = d.seq[7] + d.seq.slice(1, 7) + d.seq[0] + d.seq.slice(8); }],
    ['a child prefix diverges', a => { const d = pick(a, '2.c.pc#3'); d.locks[3][0] += 1; }],
    ['the held L never released', a => { const d = pick(a, '2.a2'); const i = d.locks.findIndex((l: any, k: number) => k > 6 && l[5]); d.locks[i][5] = 0; }],
    ['a hold flag on the L-top chain', a => { const d = pick(a, 'bag1.l_top'); d.locks[3][5] = 1; }],
    ['a demo removed', a => { a.demos = a.demos.filter((d: any) => d.node !== '2.c.pc#6'); }],
    ['an unbuilt entry removed', a => { a.unbuilt = a.unbuilt.slice(1); }],
    ['a U fired as a plain T', a => { const d = pick(a, '2.b'); d.letters = d.letters.slice(0, -1) + 't'; }],
  ];
  for (const [what, f] of muts) {
    const a = fresh(); f(a);
    expect(checkAll(a), what).not.toBeNull();
  }
}, 120_000);

test('planner mutants: each rule turned off fails a check or throws', () => {
  for (const m of ['noRowMap', 'noReach', 'noSpinCheck'] as (keyof DemoMutants)[]) {
    let verdict: string | null;
    try { verdict = checkAll(JSON.parse(serialise(buildFor(HDGAMUSHIRO, { [m]: true })))); } catch (e) { verdict = String(e); }
    expect(verdict, m).not.toBeNull();
  }
}, 300_000);

/** A CONTROL here, measured, as on 迷走砲 and unlike shiwehi's ガムシロ積み: the page's one order (J
 *  before S) is forced by gravity (the S rests on the J), so dropping it changes which queue is dealt
 *  and every check still passes. Failing a check later means it has become a mutant. */
test('control: ignoreConditions changes the build and breaks nothing', () => {
  const text = serialise(buildFor(HDGAMUSHIRO, { ignoreConditions: true }));
  expect(text === built(), 'ignoreConditions changes the build').toBe(false);
  expect(checkAll(JSON.parse(text))).toBeNull();
}, 300_000);

/** A CONTROL here, measured: it changes which paths are chosen and every check still passes — no demo
 *  needs a 180. */
test('control: no180 changes the build and breaks nothing', () => {
  const text = serialise(buildFor(HDGAMUSHIRO, { no180: true }));
  expect(text === built(), 'no180 changes the build').toBe(false);
  expect(checkAll(JSON.parse(text))).toBeNull();
}, 300_000);

/** EQUIVALENT here, measured: no demo's bag-2 order names a piece dealt at a hold swap (the page draws
 *  no 妥協 form), so the swap-deal credit decides nothing and the build is byte-identical. */
test('noSwapDeal is equivalent here', () => {
  expect(serialise(buildFor(HDGAMUSHIRO, { noSwapDeal: true }))).toBe(built());
}, 300_000);

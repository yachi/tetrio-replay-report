/**
 * The stick spin (SDパフェ) constructed demos (`analysis/stickspin-demos.json`, from
 * `pipeline/sim/emit-route-demos.ts --opener stickspin`; the planner is the shared `route-demos.ts`,
 * the opener's half is `demos` in `route-profile-stickspin.ts`).
 *
 *   1. byte rebuild: the committed artefact is what `build()` produces now.
 *   2-8. the shared demo checks (`route-demo-checks.ts`): re-run through `instrumentEngine`, the
 *      corpus classifier reaches the demo's node (bag1.fire / bag1.pc through the bag-1 spin step),
 *      board equality against the drawing, spins, whole 7-bags under the page's conditions, prefix
 *      sharing, completeness.
 *   9. stick spin's own: no demo holds; bag 1 is six pieces and then the T, fired on lock 7 into the
 *      drawn U as a TSS (stood up for bag1.fire, laid flat for bag1.pc); every bag-2 board fires a
 *      TSD; the PC patterns are TSS + TSD + PC for 8 lines; the attack line's bag 3 is a TST; the
 *      SD-PC fallbacks fire into their separate spin boards (TST, then the Imperial Cross and STMB
 *      Cave TSDs); the chains run through the demo that ends on each after-the-spin illustration.
 *  10. mutants: each planner rule turned off, and each planted artefact defect, turns a check red;
 *      `no180` and `ignoreConditions` are measured CONTROLS here (see their test).
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/stickspin-demos.test.ts   (well under a minute)
 */
import { test, expect } from 'bun:test';
import { build as buildFor, serialise, chainOf, type DemoMutants } from '../sim/route-demos.ts';
import { STICKSPIN } from '../sim/route-profile-stickspin.ts';
import { demoChecks } from './route-demo-checks.ts';
import { conditionHolds } from '../sim/route-facts.ts';

/** Nodes with a board and no demo, and the reason the artefact gives. A node the planner cannot
 *  build is a red build until it is named here. The mirror and the eight illustrations are the
 *  profile's; `2.sd.pc#7` and `2.sd.pc#16` are the planner's measured failures: both stand their T
 *  upright in the column-7 well under an S drawn across a row that clears only after the T, so
 *  whichever goes first, the other cannot (the S is not yet a piece shape; the T has no path in). */
const DEMO_UNBUILT: Record<string, string> = {
  'bag1.right': '係原頁左邊嗰幅第一巡圖左右反轉（J↔L、S↔Z），逐格對過；用頁面嘅反轉掣睇',
  'bag1.fire.after': '示意圖：TSS 之後嘅盤面，即係 bag1.fire 示範打完之後嘅盤面',
  'bag1.pc.after': '示意圖：TSS 之後嘅盤面，即係 bag1.pc 示範打完之後嘅盤面',
  '2.fire.tsd': '示意圖：兩個火力派生 2巡目形打 TSD 嘅位，即係 2.fire#1 示範最後一粒',
  '2.sd.after': '示意圖：TSD 之後嘅盤面，即係 2.sd 示範打完之後嘅盤面',
  '2.sd.tst.spin': '示意圖：TST 嘅位同消嘅行，即係 2.sd.tst 示範最後一粒',
  '2.sd.imperial.spin': '示意圖：Imperial Cross 嘅 TSD 位同消嘅兩行，即係 2.sd.imperial 示範最後一粒',
  '2.sd.stmb.spin': '示意圖：STMB Cave 嘅 TSD 位同消嘅行，即係 2.sd.stmb 示範最後一粒',
  '2.mochi.after': '示意圖：TSD 之後嘅盤面，即係 2.mochi 示範打完之後嘅盤面',
  '2.sd.pc#7': '最遠放到 JZOI；之後：T 由出生位行唔到去；S 中間隔住嘅行未消，未成形',
  '2.sd.pc#16': '最遠放到 LZOI；之後：T 由出生位行唔到去；S 中間隔住嘅行未消，未成形',
};
/** U line counts the drawing does not fix: measured empty — every U is a named spin (bag 1's TSS,
 *  bag 2's TSD, the attack line's TST, the fallbacks' TST and TSDs). */
const DEMO_SPIN_LINES: Record<string, number> = {};
/** A plain `t` the engine credited as a spin. Measured empty: every PC pattern's T is placed without
 *  a spin, so no spin letter is needed either (the profile has no `spinLetter`). */
const DEMO_SPIN_EXCEPTIONS: string[] = [];
/** Colour-read drawings: the page's one slip (`2.mochi.pc#13:colour`), read as the L it has to be. The
 *  shared check requires the classifier to file that demo OFF the page as drawn, which is what makes
 *  the reading necessary rather than decorative. */
const DEMO_PIECE_READINGS: string[] = ['2.mochi.pc#13'];

const C = demoChecks(STICKSPIN, {
  unbuilt: DEMO_UNBUILT, spinLines: DEMO_SPIN_LINES, spinExceptions: DEMO_SPIN_EXCEPTIONS,
  pieceReadings: DEMO_PIECE_READINGS,
});
const { routes, byId, committedText, committed } = C;

/** The kinds of T-spin a chain fires, in order, and what it ends on. */
const EVENTS: [RegExp, string][] = [
  [/^bag1\.left$/, ''],
  [/^bag1\.(fire|pc)$/, 'TSS'],
  [/^2\.(fire#\d|sd|mochi|mochi\.i_right)$/, 'TSS TSD'],
  [/^2\.fire\.td#\d$/, 'TSS TSD TST'],
  [/^2\.sd\.tst$/, 'TSS TSD TST'],
  [/^2\.sd\.(imperial|stmb)$/, 'TSS TSD TSD'],
  [/^2\.(sd|mochi)\.pc#\d+$/, 'TSS TSD PC'],
];

/** stick spin's own checks, then the shared ones. */
function checkAll(art: any): string | null {
  for (const d of art.demos) {
    const n = byId.get(d.node)! as any;
    // 9a. nothing holds
    if (d.locks.some((l: any) => l[5]) || d.bags.some((b: any) => b.holds)) return `${d.node}: holds`;
    // 9b. bag 1 is six pieces, then the T on lock 7: stood up (fire) or laid flat (pc)
    if (d.chain[0] !== 'bag1.left' && (d.letters[6] !== 'U' || d.events[0]?.kind !== 'TSS' || d.events[0].lock !== 6))
      return `${d.node}: lock 7 is not the TSS`;
    // 9b'. bag 1's queue keeps the page's no-hold conditions for the left pattern (O before Z, J before L)
    if (conditionHolds((routes as any).bag1.no_hold, d.bags[0].queue, '') !== true)
      return `${d.node}: bag 1 ${d.bags[0].queue} breaks the no-hold conditions`;
    // 9c. the chain's spins and its end
    const want = EVENTS.find(([re]) => re.test(d.node))?.[1];
    const got = d.events.map((e: any) => e.kind).join(' ');
    if (want === undefined || got !== want) return `${d.node}: events ${got}, want ${want}`;
    if (n.list && d.events.at(-1).lines !== 8) return `${d.node}: the PC clears ${d.events.at(-1).lines} lines, not 8`;
  }
  return C.checkAll(art);
}

let BUILT: string | null = null;
const built = () => (BUILT ??= serialise(buildFor(STICKSPIN)));

test('rebuilding reproduces the committed stickspin-demos.json byte for byte', () => {
  expect(built()).toBe(committedText());
}, 120_000);

test('every demo re-runs, reaches its node, ends on its drawing; the lists are exact', () => {
  const art = committed();
  expect(art.report_eligible).toBe(false);
  expect(art.constructed).toBe(true);
  expect(checkAll(art)).toBeNull();
  // the page's three 基本形 are demos' nodes, not more demos
  const basic = art.demos.filter((d: any) => d.also.length).map((d: any) => [d.node, d.also]);
  expect(basic).toEqual([['bag1.fire', ['basic.1']], ['2.fire.td#1', ['basic.3']]]);
  // every demo's chain is its node's ancestry; a bag-1 board is its own chain
  for (const d of art.demos)
    expect(chainOf(byId.get(d.node)!, routes, STICKSPIN.tag, STICKSPIN.demos!.chainVia).map(n => n.id)).toEqual(d.chain);
  for (const d of art.demos.filter((x: any) => byId.get(x.node)!.bag === 1)) expect(d.chain, d.node).toEqual([d.node]);
  for (const d of art.demos.filter((x: any) => x.node.startsWith('2.fire')))
    expect(d.chain[0], d.node).toBe('bag1.fire');
  for (const d of art.demos.filter((x: any) => /^2\.(sd|mochi)/.test(x.node)))
    expect(d.chain[0], d.node).toBe('bag1.pc');
  for (const d of art.demos.filter((x: any) => x.node.startsWith('2.fire.td#')))
    expect(d.chain.slice(0, 2), d.node).toEqual(['bag1.fire', '2.fire#1']);
  // every PC pattern but the two named unbuilt has a demo
  expect(art.demos.filter((d: any) => byId.get(d.node)!.list).length)
    .toBe(routes.nodes.filter(n => n.list).length - 2);
  // bag1.left's demo places six pieces and leaves the T unplaced, last in its bag
  const left = art.demos.find((d: any) => d.node === 'bag1.left');
  expect([left.locks.length, left.bags[0].unused]).toEqual([6, 'T']);
}, 120_000);

test('data mutants: each planted defect is caught', () => {
  const fresh = () => JSON.parse(committedText());
  const pick = (a: any, id: string) => a.demos.find((d: any) => d.node === id);
  const muts: [string, (a: any) => void][] = [
    ['a place moved one column', a => { const d = pick(a, '2.sd.pc#3'); d.locks[17][1] += 1; }],
    ['an input deleted', a => {
      const d = pick(a, '2.sd');
      const k = d.inputs.findIndex((x: any) => x[1] === 'keydown' && /rotate/.test(x[2]) && x[0] > 200);
      d.inputs.splice(k, 1);
    }],
    ['the TSS spin code 2 -> 1', a => { const d = pick(a, 'bag1.pc'); d.locks[6][3] = 1; }],
    ['a bag-2 TSD spin code 2 -> 0', a => { const d = pick(a, '2.mochi'); d.locks[13][3] = 0; }],
    ['bag 1 with Z before O', a => {
      const d = pick(a, 'bag1.fire'); const q = d.bags[0].queue;
      d.bags[0].queue = q.replace('O', '#').replace('Z', 'O').replace('#', 'Z');
      d.seq = d.bags[0].queue + d.seq.slice(7);
    }],
    ['a piece swapped between bags', a => { const d = pick(a, '2.sd'); d.seq = d.seq[7] + d.seq.slice(1, 7) + d.seq[0] + d.seq.slice(8); }],
    ['a child prefix diverges', a => { const d = pick(a, '2.mochi.pc#5'); d.locks[3][0] += 1; }],
    ['a hold flag', a => { const d = pick(a, '2.fire#2'); d.locks[9][5] = 1; }],
    ['a demo removed', a => { a.demos = a.demos.filter((d: any) => d.node !== '2.sd.stmb'); }],
    ['an unbuilt entry removed', a => { a.unbuilt = a.unbuilt.slice(1); }],
    ['a U fired as a plain T', a => { const d = pick(a, '2.fire.td#3'); d.letters = d.letters.slice(0, -1) + 't'; }],
    ['the colour reading dropped', a => { pick(a, '2.mochi.pc#13').piece_readings = []; }],
  ];
  for (const [what, f] of muts) {
    const a = fresh(); f(a);
    expect(checkAll(a), what).not.toBeNull();
  }
}, 120_000);

test('planner mutants: each rule turned off fails a check or throws', () => {
  for (const m of ['noRowMap', 'noReach'] as (keyof DemoMutants)[]) {
    let verdict: string | null;
    try { verdict = checkAll(JSON.parse(serialise(buildFor(STICKSPIN, { [m]: true })))); } catch (e) { verdict = String(e); }
    expect(verdict, m).not.toBeNull();
  }
}, 300_000);

/** EQUIVALENT here, measured: `noSpinCheck` leaves the artefact byte-identical, because for every U
 *  on this page the shortest engine path into the slot is already a full T-spin clearing the drawn line
 *  count, so the check never rejects the path the planner picks. Named, so the day it stops being
 *  equivalent is a red build; the rule is a mutant on the other three pages. The spin itself is still
 *  checked on every committed lock by the shared check 5. */
test('noSpinCheck is equivalent on this page, and named', () => {
  expect(serialise(buildFor(STICKSPIN, { noSpinCheck: true }))).toBe(built());
}, 300_000);

/** Both are CONTROLS here, measured: each changes which paths or queues are chosen (the byte rebuild
 *  goes red) and every check still passes. `no180`: no demo needs a 180. `ignoreConditions`: the
 *  page's no-hold conditions for bag 1 (O before Z, J before L) are what the drawn board's gravity
 *  already requires — the transcription gate checks each by support (the later piece rests on the
 *  earlier) — so dropping them deals queues that still satisfy them. Either failing a check later
 *  means it has become a mutant. */
const CONTROLS: (keyof DemoMutants)[] = ['no180', 'ignoreConditions'];

test('controls: no180 and ignoreConditions change the build and break nothing', () => {
  for (const m of CONTROLS) {
    const text = serialise(buildFor(STICKSPIN, { [m]: true }));
    expect(text === built(), `${m} changes the build`).toBe(false);
    expect(checkAll(JSON.parse(text)), m).toBeNull();
  }
}, 300_000);

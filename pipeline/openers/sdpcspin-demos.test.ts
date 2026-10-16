/**
 * The SDPC Spin constructed demos (`analysis/sdpcspin-demos.json`, from
 * `pipeline/sim/emit-route-demos.ts --opener sdpcspin`; the planner is the shared `route-demos.ts`,
 * the opener's half is `demos` in `route-profile-sdpcspin.ts`).
 *
 *   1. byte rebuild: the committed artefact is what `build()` produces now.
 *   2-8. the shared demo checks (`route-demo-checks.ts`): re-run through `instrumentEngine`, the
 *      corpus classifier reaches the demo's node (bag1.lj / bag1.jl through the bag-1 spin step, the
 *      `.left` stage boards at six locks), board equality against the drawing, spins, whole 7-bags
 *      under the page's conditions, prefix sharing, completeness.
 *   9. SDPC Spin's own: no demo holds; the two stage boards place six pieces and leave the T; each TSS
 *      board is its stage demo plus the T laid flat on lock 7; the chain's spins in order (TSS, TSD,
 *      TST, then each build's TSDs, the Imperial Cross's two TSDs and a 14-line PC); 3.first.cave's
 *      「J before at least two of T, L and Z」, which the shared planner does not read; the alternate
 *      fourth bags leave the saved I unplaced.
 *  10. the planner's measured failures, re-measured: in 3.second.cspin and 3.third.transition#1 the
 *      engine has a path into the TSD slot only while the bag's Z is not yet placed, in
 *      3.third.transition#2 only while its O is not (the page's 「hold O and tuck it after taking the
 *      TSD」), and in 3.first.cave.stsd the drawn J rests only once the T fills the slot under it. In all
 *      four the T fires BEFORE a piece the board draws; the shared planner fires a snapshot board's U
 *      last, so they are unbuilt, with every node under 3.second.cspin.
 *      The same search shows every Imperial Cross PC pattern roofs its T slot, which is why the profile
 *      frames that PC kind after 28 locks rather than after the last TSD before the PC.
 *  11. mutants: each planner rule turned off, and each planted artefact defect, turns a check red;
 *      what each of the others measured is stated at its own test.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/sdpcspin-demos.test.ts   (well under a minute)
 */
import { test, expect } from 'bun:test';
import { build as buildFor, serialise, chainOf, reach, newEngine, type DemoMutants } from '../sim/route-demos.ts';
import { SDPCSPIN } from '../sim/route-profile-sdpcspin.ts';
import { demoChecks, digestOf } from './route-demo-checks.ts';
import { classify } from '../sim/route-facts.ts';

/** Nodes with a board and no demo, and the reason the artefact gives. A node the planner cannot
 *  build is a red build until it is named here. The two illustrations, the doubly-drawn Z and the two
 *  DT Cannon boards are the profile's; the rest are the planner's measured failures (test 10 says
 *  why each is a fact about the page's drawing order, not a planner bug). */
const DEMO_UNBUILT: Record<string, string> = {
  'bag1.after': '示意圖：TSS 之後嘅盤面（兩種 J/L 顏色消完都係呢幅），即係 bag1.jl 示範打完之後嘅盤面',
  '2.after': '示意圖：TSD 之後嘅盤面，即係 2.tsd 示範打完之後嘅盤面',
  '3.second.cspin.z_early': '同一粒 Z 畫咗兩次（放咗喺 J 上面，原本嘅位用撇號標住）：唔係一個盤面',
  '3.second.cspin.dt#1': 'C-Spin 嘅殘餘用淺色（大寫）畫，但第三巡嗰粒 I 畫成實色，同新嗰粒 I 一齊即係兩粒 I：'
    + '唔係一個巡次嘅砌法（transcription 嘅 known_discrepancies）',
  '3.second.cspin.dt#2': 'C-Spin 嘅殘餘用淺色（大寫）畫，但第三巡嗰粒 I 畫成實色，同新嗰粒 I 一齊即係兩粒 I：'
    + '唔係一個巡次嘅砌法（transcription 嘅 known_discrepancies）',
  '3.first.cave.stsd': '最遠放到 LZSOI；之後：J 由出生位行唔到去；T(U) 要最後先放',
  '3.first.cave.stsd.next': '上一層 3.first.cave.stsd 砌唔到',
  '3.second.cspin': '最遠放到 JZSOLI；之後：T(U) 由出生位行唔到去',
  '3.second.cspin.first#1': '上一層 3.second.cspin 砌唔到',
  '3.second.cspin.first#2': '上一層 3.second.cspin 砌唔到',
  '3.second.cspin.o_first#1': '上一層 3.second.cspin 砌唔到',
  '3.second.cspin.o_first#2': '上一層 3.second.cspin 砌唔到',
  '3.second.cspin.l_first#1': '上一層 3.second.cspin 砌唔到',
  '3.second.cspin.l_first#2': '上一層 3.second.cspin 砌唔到',
  '3.second.cspin.l_first#3': '上一層 3.second.cspin 砌唔到',
  '3.second.cspin.l_first#4': '上一層 3.second.cspin 砌唔到',
  '3.third.transition#1': '最遠放到 LJSOZI；之後：T(U) 由出生位行唔到去',
  '3.third.transition#2': '最遠放到 LJSZOI；之後：T(U) 由出生位行唔到去',
};
/** U line counts the drawing does not fix: the four Imperial Cross PC patterns draw their T (the
 *  Imperial Cross's second TSD, flat in the bottom two body rows) with no named spin. */
const DEMO_SPIN_LINES: Record<string, number> = {
  '3.third.imperial.pc#1': 2, '3.third.imperial.pc#2': 2, '3.third.imperial.pc#3': 2, '3.third.imperial.pc#4': 2,
};
/** A plain `t` the engine credited as a spin: measured empty (no board draws a plain `t`). */
const DEMO_SPIN_EXCEPTIONS: string[] = [];
/** Colour-read drawings: measured empty. */
const DEMO_PIECE_READINGS: string[] = [];

const C = demoChecks(SDPCSPIN, {
  unbuilt: DEMO_UNBUILT, spinLines: DEMO_SPIN_LINES, spinExceptions: DEMO_SPIN_EXCEPTIONS,
  pieceReadings: DEMO_PIECE_READINGS,
});
const { routes, byId, committedText, committed } = C;

/** A demo the classifier files under a SIBLING snapshot, and that sibling. 3.first.trinity.tsd and
 *  3.first.trinity.tss both hang under 3.first.trinity, and the classifier takes the sibling whose
 *  drawing a round reaches FIRST. The TSD board is the board the Trinity's own TSD leaves (its demo
 *  places only the T), so every round that goes on to the TSS passes through it first: the TSS demo is
 *  filed under the TSD at the lock the Trinity's TSD fired, and no round, demo or corpus, can be filed
 *  under the TSS. The page does not say which T fires first (the transcription's `order_note`). */
const CLASSIFIER_SIBLING: Record<string, string> = { '3.first.trinity.tss': '3.first.trinity.tsd' };

/** The kinds of T-spin a chain fires, in order, and what it ends on. */
const EVENTS: [RegExp, string][] = [
  [/^bag1\.(lj|jl)\.left$/, ''],
  [/^bag1\.(lj|jl)$/, 'TSS'],
  [/^2\.tsd$/, 'TSS TSD'],
  [/^3\.(first|second|third)$/, 'TSS TSD TST'],
  [/^3\.(first\.cave|second\.alt#\d|third\.imperial)$/, 'TSS TSD TST TSD'],
  [/^3\.first\.trinity$/, 'TSS TSD TST TSD TSD'],
  [/^3\.first\.trinity\.tsd$/, 'TSS TSD TST TSD TSD TSD'],
  [/^3\.first\.trinity\.tss$/, 'TSS TSD TST TSD TSD TSS'],
  [/^3\.third\.imperial\.pc#\d$/, 'TSS TSD TST TSD TSD PC'],
];

/** 「J needs to come before at least two of T, L, and Z」: a condition shape the shared planner and
 *  `conditionHolds` do not read (they read `all`), so it is checked here, on the bag it names. */
function atLeastHolds(cond: any, queue: string): boolean {
  const { before, count, of } = cond.at_least;
  return of.filter((p: string) => queue.indexOf(before) < queue.indexOf(p)).length >= count;
}

/** SDPC Spin's own checks, then the shared ones. */
function checkAll(art: any): string | null {
  const byNode = new Map<string, any>(art.demos.map((d: any) => [d.node, d]));
  for (const d of art.demos) {
    const n = byId.get(d.node)! as any;
    // 9a. nothing holds
    if (d.locks.some((l: any) => l[5]) || d.bags.some((b: any) => b.holds)) return `${d.node}: holds`;
    // 9b. a stage board places six pieces and leaves the T; a TSS board is its stage demo plus the T
    if (n.derived) {
      if (d.locks.length !== 6 || d.bags[0].unused !== 'T') return `${d.node}: not six pieces with the T left`;
    } else if (n.bag === 1) {
      const stage = byNode.get(n.spin_of);
      if (!stage || JSON.stringify(d.locks.slice(0, 6)) !== JSON.stringify(stage.locks)) return `${d.node}: first six locks are not ${n.spin_of}'s`;
    }
    if (!n.derived && (d.letters[6] !== 'U' || d.events[0]?.kind !== 'TSS' || d.events[0].lock !== 6))
      return `${d.node}: lock 7 is not the TSS`;
    // 9c. the chain's spins and its end
    const want = EVENTS.find(([re]) => re.test(d.node))?.[1];
    const got = d.events.map((e: any) => e.kind).join(' ');
    if (want === undefined || got !== want) return `${d.node}: events ${got}, want ${want}`;
    if (n.list && d.events.at(-1).lines !== 14) return `${d.node}: the PC clears ${d.events.at(-1).lines} lines, not 14`;
    // 9d. the at_least condition, on the bag of the node that states it
    for (const b of d.bags) {
      const c = byId.get(b.node)!.condition;
      if (c?.at_least && !atLeastHolds(c, b.queue)) return `${b.node}: queue ${b.queue} breaks 「${c.at_least.before} before ${c.at_least.count} of ${c.at_least.of.join('')}」`;
    }
    // 9e. the alternate fourth bags save the I: dealt, never placed
    if (n.hold === 'I' && (d.bags.at(-1).unused !== 'I' || d.bags.at(-1).placed.includes('I'))) return `${d.node}: the saved I is placed`;
  }
  // the shared checks, one demo at a time, with the named sibling filing in place of check 3's last step
  const done = C.checkComplete(art);
  if (done) return done;
  for (const d of art.demos) {
    const e = C.checkDemo(d, byNode);
    const sib = CLASSIFIER_SIBLING[d.node];
    if (!sib) { if (e) return e; continue; }
    // every shared check before the snapshot step passed, and the classifier files it under the sibling
    if (e !== `${d.node}: classifier snapshot missing`) return e ?? `${d.node}: classifier reaches it after all`;
    const snaps = classify(SDPCSPIN, [digestOf(d)], routes).cases[0]!.snapshots;
    const parent = byNode.get(byId.get(d.node)!.parent!);
    const at = snaps.find((s: any) => s.node === sib);
    if (!at || at.lock !== parent?.locks.length - 1) return `${d.node}: not filed under ${sib} at its parent's last lock`;
  }
  if (art.demos.some((d: any) => d.piece_readings.length)) return 'piece readings list differs';
  return null;
}

let BUILT: string | null = null;
const built = () => (BUILT ??= serialise(buildFor(SDPCSPIN)));

test('rebuilding reproduces the committed sdpcspin-demos.json byte for byte', () => {
  expect(built()).toBe(committedText());
}, 120_000);

test('every demo re-runs, reaches its node, ends on its drawing; the lists are exact', () => {
  const art = committed();
  expect(art.report_eligible).toBe(false);
  expect(art.constructed).toBe(true);
  expect(checkAll(art)).toBeNull();
  // every demo's chain is its node's ancestry; a bag-1 board is its own chain
  for (const d of art.demos)
    expect(chainOf(byId.get(d.node)!, routes, SDPCSPIN.tag, SDPCSPIN.demos!.chainVia).map(n => n.id)).toEqual(d.chain);
  for (const d of art.demos.filter((x: any) => byId.get(x.node)!.bag === 1)) expect(d.chain, d.node).toEqual([d.node]);
  // past bag 1 every chain runs through bag1.jl and 2.tsd
  for (const d of art.demos.filter((x: any) => byId.get(x.node)!.bag >= 2))
    expect(d.chain.slice(0, 2), d.node).toEqual(['bag1.jl', '2.tsd']);
  // every Imperial Cross PC pattern has a demo
  expect(art.demos.filter((d: any) => byId.get(d.node)!.list).map((d: any) => d.node))
    .toEqual(routes.nodes.filter(n => n.list).map(n => n.id));
  // the demo set, as measured
  expect(art.demos.map((d: any) => d.node)).toEqual([
    'bag1.lj.left', 'bag1.lj', 'bag1.jl.left', 'bag1.jl', '2.tsd', '3.first', '3.second', '3.third', '3.first.cave',
    '3.first.trinity', '3.first.trinity.tsd', '3.first.trinity.tss', '3.second.alt#1', '3.second.alt#2',
    '3.third.imperial', '3.third.imperial.pc#1', '3.third.imperial.pc#2', '3.third.imperial.pc#3', '3.third.imperial.pc#4',
  ]);
}, 120_000);

/** Test 10: why the planner's failures are the page's drawing order. Each case re-runs the engine's
 *  own move search (`reach`) on the drawn board: with every drawn piece there, the piece named has no
 *  resting path into its drawn cells; with the one named piece left out (or, for the STSD's J, the T's
 *  slot filled), it has. */
test('measured: each unbuilt TSD fires before a piece its board draws', () => {
  const W = 10;
  const gridOf = (rows: string[], skip: (ch: string) => boolean) => {
    const g = Array.from({ length: 40 }, () => new Array<string | null>(W).fill(null));
    rows.forEach((r, i) => [...r].forEach((ch, x) => {
      if (ch !== '-' && !skip(ch)) g[rows.length - 1 - i]![x] = ch === 'c' ? 'G' : ch === 'U' ? 'T' : ch.toUpperCase();
    }));
    return g;
  };
  const cellsOf = (rows: string[], L: string) => {
    const t: number[] = [];
    rows.forEach((r, i) => [...r].forEach((ch, x) => { if (ch === L) t.push((rows.length - 1 - i) * W + x); }));
    return t;
  };
  const paths = (id: string, piece: string, letter: string, skip: (ch: string) => boolean) => {
    const rows = (byId.get(id) as any).rows as string[];
    return reach(newEngine(routes), gridOf(rows, ch => ch === letter || skip(ch)), piece, cellsOf(rows, letter)).length;
  };
  for (const [id, late] of [['3.second.cspin', 'z'], ['3.third.transition#1', 'z'], ['3.third.transition#2', 'o']] as const) {
    expect(paths(id, 'T', 'U', () => false), `${id}: T with the ${late} placed`).toBe(0);
    expect(paths(id, 'T', 'U', ch => ch === late), `${id}: T before the ${late}`).toBeGreaterThan(0);
  }
  // and why the PC kind is framed after 28 locks, not after the last TSD: every Imperial Cross PC
  // pattern roofs its T slot, so its TSD fires before the PC's last lock
  for (const n of routes.nodes.filter(x => x.list === '3.third.imperial.pc'))
    expect(paths(n.id, 'T', 'U', () => false), `${n.id}: T into the roofed slot`).toBe(0);
  expect(paths('3.first.cave.stsd', 'J', 'j', ch => ch === 'U'), 'STSD: J over the empty slot').toBe(0);
  expect(paths('3.first.cave.stsd', 'J', 'j', () => false), 'STSD: J once the T fills the slot').toBeGreaterThan(0);
}, 120_000);

test('data mutants: each planted defect is caught', () => {
  const fresh = () => JSON.parse(committedText());
  const pick = (a: any, id: string) => a.demos.find((d: any) => d.node === id);
  const muts: [string, (a: any) => void][] = [
    ['a place moved one column', a => { const d = pick(a, '3.third.imperial.pc#2'); d.locks[30][1] += 1; }],
    ['an input deleted', a => {
      const d = pick(a, '3.first');
      const k = d.inputs.findIndex((x: any) => x[1] === 'keydown' && /rotate/.test(x[2]) && x[0] > 200);
      d.inputs.splice(k, 1);
    }],
    ['the TSS spin code 2 -> 1', a => { const d = pick(a, 'bag1.lj'); d.locks[6][3] = 1; }],
    ['the bag-2 TSD spin code 2 -> 0', a => { const d = pick(a, '2.tsd'); d.locks[13][3] = 0; }],
    ['3.third with O before S', a => {
      const d = pick(a, '3.third'); const q = d.bags[2].queue;
      d.bags[2].queue = q.replace('S', '#').replace('O', 'S').replace('#', 'O');
      d.seq = d.bags.map((b: any) => b.queue).join('') + d.seq.slice(21);
    }],
    ['3.first.cave with J after T, L and Z', a => {
      const d = pick(a, '3.first.cave'); const q = d.bags[3].queue;
      d.bags[3].queue = q.replace('J', '') + 'J';
      d.seq = d.bags.map((b: any) => b.queue).join('') + d.seq.slice(28);
    }],
    ['a piece swapped between bags', a => {
      // bags 1 and 2 deal the same queue here, so swap bag 1's O (index 1) with bag 3's S (index 15)
      const d = pick(a, '3.second'); const q = [...d.seq]; [q[1], q[15]] = [q[15], q[1]]; d.seq = q.join('');
    }],
    ['a child prefix diverges', a => { const d = pick(a, '3.first.trinity.tss'); d.locks[3][0] += 1; }],
    ['a TSS board off its stage demo', a => { const d = pick(a, 'bag1.lj.left'); d.locks[2][0] += 1; }],
    ['a hold flag', a => { const d = pick(a, '3.second'); d.locks[16][5] = 1; }],
    ['the saved I placed', a => { const d = pick(a, '3.second.alt#1'); d.bags[3].unused = ''; }],
    ['a demo removed', a => { a.demos = a.demos.filter((d: any) => d.node !== '3.first.cave'); }],
    ['an unbuilt entry removed', a => { a.unbuilt = a.unbuilt.slice(1); }],
    ['a U fired as a plain T', a => { const d = pick(a, '3.third.imperial'); d.letters = d.letters.slice(0, -1) + 't'; }],
  ];
  for (const [what, f] of muts) {
    const a = fresh(); f(a);
    expect(checkAll(a), what).not.toBeNull();
  }
}, 120_000);

test('planner mutants: each rule turned off fails a check or throws', () => {
  for (const m of ['noRowMap', 'noReach', 'noSpinCheck'] as (keyof DemoMutants)[]) {
    let verdict: string | null;
    try { verdict = checkAll(JSON.parse(serialise(buildFor(SDPCSPIN, { [m]: true })))); } catch (e) { verdict = String(e); }
    expect(verdict, m).not.toBeNull();
  }
}, 300_000);

/** EQUIVALENT here, measured: each leaves the artefact byte-identical. `noSwapDeal`: no demo holds, so
 *  there is no swap slot to deal a piece at. `ignoreConditions`: the one `before` pair the planner reads
 *  (3.third's S before O) is what the drawn board's gravity already requires — an O cell rests on an S
 *  cell, which is how the transcription's `condition_evidence` checks it — and the `at_least` condition
 *  is not read by the planner at all (checked on the queue by 9d instead). Named, so the day either
 *  stops being equivalent is a red build. */
test('noSwapDeal and ignoreConditions are equivalent on this page, and named', () => {
  for (const m of ['noSwapDeal', 'ignoreConditions'] as (keyof DemoMutants)[])
    expect(serialise(buildFor(SDPCSPIN, { [m]: true })), m).toBe(built());
}, 300_000);

/** A CONTROL here, measured: it changes which paths are chosen (the byte rebuild goes red) and every
 *  check still passes — no demo needs a 180, and no unbuilt node becomes buildable with one. */
test('control: no180 changes the build and breaks nothing', () => {
  const text = serialise(buildFor(SDPCSPIN, { no180: true }));
  expect(text === built(), 'no180 changes the build').toBe(false);
  expect(checkAll(JSON.parse(text))).toBeNull();
}, 300_000);

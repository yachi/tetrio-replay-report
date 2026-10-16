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
 *  10. the profile's `uFiresBefore` readings, re-measured: in each named board the engine has no path
 *      into the TSD slot with every drawn piece placed, and has one with the pieces the T must beat left
 *      out (the minimal set); a named piece that is not in the T's way rests on one that is
 *      (U_BEFORE_SUPPORT). So the T fires BEFORE those pieces, the drawn board never stands at any lock,
 *      and the demo reaches it as the last bag's kept-rows composite (the shared check's `u_before`
 *      branch); the classifier files none of them, nor the matchable children under them
 *      (CLASSIFIER_PARENT_UNFILED). The same search shows every Imperial Cross PC pattern roofs its T
 *      slot, which is why the profile frames that PC kind after 28 locks rather than after the last TSD
 *      before the PC.
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
 *  build is a red build until it is named here. All five are the profile's: the two illustrations,
 *  the doubly-drawn Z and the two DT Cannon boards. */
const DEMO_UNBUILT: Record<string, string> = {
  'bag1.after': '示意圖：TSS 之後嘅盤面（兩種 J/L 顏色消完都係呢幅），即係 bag1.jl 示範打完之後嘅盤面',
  '2.after': '示意圖：TSD 之後嘅盤面，即係 2.tsd 示範打完之後嘅盤面',
  '3.second.cspin.z_early': '同一粒 Z 畫咗兩次（放咗喺 J 上面，原本嘅位用撇號標住）：唔係一個盤面',
  '3.second.cspin.dt#1': 'C-Spin 嘅殘餘用淺色（大寫）畫，但第三巡嗰粒 I 畫成實色，同新嗰粒 I 一齊即係兩粒 I：'
    + '唔係一個巡次嘅砌法（transcription 嘅 known_discrepancies）',
  '3.second.cspin.dt#2': 'C-Spin 嘅殘餘用淺色（大寫）畫，但第三巡嗰粒 I 畫成實色，同新嗰粒 I 一齊即係兩粒 I：'
    + '唔係一個巡次嘅砌法（transcription 嘅 known_discrepancies）',
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

/** The profile's `uFiresBefore` nodes: their U fires before the named pieces, so the drawn board never
 *  stands at any lock and the shared check requires the classifier NOT to file them. */
const U_BEFORE = SDPCSPIN.demos!.uFiresBefore!;

/** Measured: a MATCHABLE child of a `uFiresBefore` board, and that parent. The classifier searches a
 *  node's children only under a snapshot it filed, and it never files the parent (its board never
 *  stands), so it never looks for the child: the child's own drawing stands at its last-but-one lock
 *  and is still not filed. The route is not relaxed for it. The unmatchable children
 *  (3.second.cspin.first#2) are not checked by the classifier step at all, so they are not here. */
const CLASSIFIER_PARENT_UNFILED: Record<string, string> = {
  '3.first.cave.stsd.next': '3.first.cave.stsd',
  '3.second.cspin.o_first#2': '3.second.cspin',
  '3.second.cspin.l_first#2': '3.second.cspin',
  '3.second.cspin.l_first#4': '3.second.cspin',
};

/** The kinds of T-spin a chain fires, in order, and what it ends on. */
const EVENTS: [RegExp, string][] = [
  [/^bag1\.(lj|jl)\.left$/, ''],
  [/^bag1\.(lj|jl)$/, 'TSS'],
  [/^2\.tsd$/, 'TSS TSD'],
  [/^3\.(first|second|third)$/, 'TSS TSD TST'],
  [/^3\.(first\.cave|second\.alt#\d|second\.cspin|third\.imperial|third\.transition#\d)$/, 'TSS TSD TST TSD'],
  [/^3\.(first\.cave\.stsd|second\.cspin\.(first|o_first|l_first)#\d)$/, 'TSS TSD TST TSD TSD'],
  [/^3\.first\.cave\.stsd\.next$/, 'TSS TSD TST TSD TSD TSD'],
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
    const unfiled = CLASSIFIER_PARENT_UNFILED[d.node];
    if (unfiled) {
      // every shared check before the snapshot step passed; the parent is a uFiresBefore board, and the
      // classifier filed neither it nor this child
      if (e !== `${d.node}: classifier snapshot missing`) return e ?? `${d.node}: classifier files it after all`;
      if (!(unfiled in U_BEFORE) || byId.get(d.node)!.parent !== unfiled) return `${d.node}: ${unfiled} is not its uFiresBefore parent`;
      const snaps = classify(SDPCSPIN, [digestOf(d)], routes).cases[0]!.snapshots;
      if (snaps.some((s: any) => s.node === unfiled)) return `${d.node}: ${unfiled} filed after all`;
      continue;
    }
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
    '3.first.cave.stsd', '3.first.cave.stsd.next', '3.first.trinity', '3.first.trinity.tsd', '3.first.trinity.tss',
    '3.second.cspin', '3.second.alt#1', '3.second.alt#2', '3.second.cspin.first#1', '3.second.cspin.first#2',
    '3.second.cspin.o_first#1', '3.second.cspin.o_first#2', '3.second.cspin.l_first#1', '3.second.cspin.l_first#2',
    '3.second.cspin.l_first#3', '3.second.cspin.l_first#4', '3.third.imperial', '3.third.imperial.pc#1',
    '3.third.imperial.pc#2', '3.third.imperial.pc#3', '3.third.imperial.pc#4', '3.third.transition#1',
    '3.third.transition#2',
  ]);
  // every uFiresBefore node has a demo, and CLASSIFIER_PARENT_UNFILED is exactly the matchable demos
  // whose parent the profile names: read off the profile, so the two cannot drift apart
  const demoed = new Set(art.demos.map((d: any) => d.node));
  for (const id of Object.keys(U_BEFORE)) expect(demoed.has(id), id).toBe(true);
  expect(Object.keys(CLASSIFIER_PARENT_UNFILED).sort()).toEqual(art.demos.map((d: any) => byId.get(d.node)! as any)
    .filter((n: any) => !n.list && !n.unmatchable && !(n.id in U_BEFORE) && n.parent in U_BEFORE).map((n: any) => n.id).sort());
}, 120_000);

/** A `uFiresBefore` piece that does NOT block the T's path, and the named piece it rests on. Measured
 *  with `reach`: in these three boards the Z's drawn cells have no resting path while the J is absent,
 *  and leaving the Z out alone does not free the T. So the J is what the T must beat, and the Z follows
 *  the J; the set is the pieces forced after the U, not the pieces in the T's way. */
const U_BEFORE_SUPPORT: Record<string, Record<string, string>> = {
  '3.second.cspin.o_first#1': { Z: 'J' },
  '3.second.cspin.l_first#1': { Z: 'J' },
  '3.second.cspin.l_first#3': { Z: 'J' },
};

/** Test 10: why the profile's `uFiresBefore` readings are the page's drawing order, not a planner
 *  choice. Each entry is re-measured with the engine's own move search (`reach`) on the drawn board.
 *  The BLOCKERS (the named pieces not in U_BEFORE_SUPPORT): with every drawn piece there the T has no
 *  resting path into the U cells; with the blockers left out it has; put any one back and it has none
 *  again. Every other named piece is no blocker (leaving it out alone does not free the T) and has no
 *  resting path without the piece it is listed as resting on, so it follows the U through it. */
test('measured: each uFiresBefore TSD fires before the pieces the profile names, and no fewer', () => {
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
  expect(Object.keys(U_BEFORE).length).toBeGreaterThan(0);
  for (const id of Object.keys(U_BEFORE_SUPPORT)) expect(id in U_BEFORE, id).toBe(true);
  for (const [id, named] of Object.entries(U_BEFORE)) {
    const rows = (byId.get(id) as any).rows as string[];
    // each named piece is ONE piece on the drawing, so leaving its letter out leaves out that piece
    for (const p of named) expect(cellsOf(rows, p.toLowerCase()).length, `${id}: ${p} cells`).toBe(4);
    const sup = U_BEFORE_SUPPORT[id] ?? {};
    const blockers = named.filter(p => !(p in sup)).map(p => p.toLowerCase());
    expect(blockers.length, `${id}: no blocker`).toBeGreaterThan(0);
    expect(paths(id, 'T', 'U', () => false), `${id}: T with every drawn piece placed`).toBe(0);
    expect(paths(id, 'T', 'U', ch => named.some(p => p.toLowerCase() === ch)), `${id}: T before ${named.join('')}`).toBeGreaterThan(0);
    expect(paths(id, 'T', 'U', ch => blockers.includes(ch)), `${id}: T before ${blockers.join('')}`).toBeGreaterThan(0);
    for (const back of blockers)
      expect(paths(id, 'T', 'U', ch => blockers.includes(ch) && ch !== back), `${id}: T with ${back} put back`).toBe(0);
    for (const [p, on] of Object.entries(sup)) {
      expect(named.includes(on) && !(on in sup), `${id}: ${p} rests on a blocker`).toBe(true);
      expect(paths(id, 'T', 'U', ch => ch === p.toLowerCase()), `${id}: ${p} alone is no blocker`).toBe(0);
      expect(paths(id, p, p.toLowerCase(), () => false), `${id}: ${p} with ${on} placed`).toBeGreaterThan(0);
      expect(paths(id, p, p.toLowerCase(), ch => ch === on.toLowerCase()), `${id}: ${p} without ${on}`).toBe(0);
    }
  }
  // and why the PC kind is framed after 28 locks, not after the last TSD: every Imperial Cross PC
  // pattern roofs its T slot, so its TSD fires before the PC's last lock
  for (const n of routes.nodes.filter(x => x.list === '3.third.imperial.pc'))
    expect(paths(n.id, 'T', 'U', () => false), `${n.id}: T into the roofed slot`).toBe(0);
  // the STSD's J rests only once the T fills the slot under it, which is the same reading seen from J
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
    ['a uFiresBefore U moved to the end of its bag', a => {
      // 3.second.cspin places IOSJLTZ: swap the T (the U) with the Z after it, keeping the 7-bag
      const d = pick(a, '3.second.cspin'); const L = d.locks.length - 1, b = d.bags.at(-1);
      const sw = (x: string, i: number) => x.slice(0, i) + x[i + 1] + x[i] + x.slice(i + 2);
      [d.locks[L - 1], d.locks[L]] = [d.locks[L], d.locks[L - 1]];
      d.letters = sw(d.letters, L - 1);
      const qi = b.queue.indexOf('T'); b.queue = sw(b.queue, qi); b.placed = sw(b.placed, b.placed.indexOf('T'));
      d.seq = d.bags.map((x: any) => x.queue).join('') + d.seq.slice(7 * d.bags.length);
    }],
    ['a u_before token dropped', a => {
      const d = pick(a, '3.third.transition#2');
      d.bags.at(-1).order_reading = d.bags.at(-1).order_reading.filter((r: string) => !r.startsWith('u_before:'));
    }],
    ['a u_before token on a node the profile does not name', a => { pick(a, '3.second.cspin.l_first#2').bags.at(-1).order_reading.push('u_before:Z'); }],
  ];
  for (const [what, f] of muts) {
    const a = fresh(); f(a);
    expect(checkAll(a), what).not.toBeNull();
  }
}, 120_000);

test('the u_before composite check has teeth: a demo against its sibling\'s drawing fails there', () => {
  // the data mutants above are caught by the re-run check before they reach the end-state branch, so
  // this one changes the DRAWING instead: transition#1's demo read against transition#2's board
  const n = byId.get('3.third.transition#1')! as any, rows = n.rows;
  n.rows = (byId.get('3.third.transition#2') as any).rows;
  try {
    expect(checkAll(JSON.parse(committedText()))).toContain('kept-rows composite is not the drawing');
  } finally { n.rows = rows; }
  expect(checkAll(JSON.parse(committedText()))).toBeNull();
}, 120_000);

test('planner mutants: each rule turned off fails a check or throws', () => {
  for (const m of ['noRowMap', 'noReach', 'noSpinCheck'] as (keyof DemoMutants)[]) {
    let verdict: string | null;
    try { verdict = checkAll(JSON.parse(serialise(buildFor(SDPCSPIN, { [m]: true })))); } catch (e) { verdict = String(e); }
    expect(verdict, m).not.toBeNull();
  }
}, 300_000);

/** A MUTANT, measured: with the profile's `uFiresBefore` ignored the U goes last again, so the eight
 *  boards it names are unbuilt again and so is every demo chained under them (5 more); nothing else
 *  moves. The symptom is asserted as that exact unbuilt set, not as 「some check fails」. */
test('noUBefore: the uFiresBefore boards and their chained children go back to unbuilt', () => {
  const art = JSON.parse(serialise(buildFor(SDPCSPIN, { noUBefore: true })));
  const under = (id: string): boolean => id in U_BEFORE || (!!byId.get(id)!.parent && under(byId.get(id)!.parent!));
  const back = committed().demos.map((d: any) => d.node).filter(under);
  expect(back.length).toBe(13);
  expect(art.unbuilt.map((u: any) => u.node).sort()).toEqual([...Object.keys(DEMO_UNBUILT), ...back].sort());
  expect(checkAll(art)).not.toBeNull();
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

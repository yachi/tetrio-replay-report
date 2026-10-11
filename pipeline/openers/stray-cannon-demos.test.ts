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
 * Run: bun test pipeline/openers/stray-cannon-demos.test.ts   (about half a minute: one build plus
 * the planner mutants, each a full build)
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, runDemo, reach, chainOf, newEngine, readRows, PIECES, DEMOS_PATH,
         type DemoMutants } from '../sim/stray-cannon-demos.ts';
import { decodeTimeline, queueStates, placeCells, WIDTH, ROWS, type Lock } from '../sim/emit-replay.ts';
import { classify, composite, patternMatches, conditionHolds, loadRoutes, type RoundDigest }
  from '../sim/emit-stray-cannon-facts.ts';
import { rowsFromBoard } from './match.ts';

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

const routes = loadRoutes();
const byId = new Map(routes.nodes.map(n => [n.id, n]));
const committedText = () => readFileSync(DEMOS_PATH, 'utf8');
const committed = () => JSON.parse(committedText());

// ── the checks, as functions of an artefact, so each data mutant can be run through them ─────────

const T_OF = (letter: string) => (letter === 'U' ? 'T' : letter.toUpperCase());

/** Boards after every lock, y-UP. */
function boards(d: any): (string | null)[][][] {
  const out: (string | null)[][][] = [];
  decodeTimeline(d.seq, d.locks as Lock[], b => out.push(b.map(r => [...r])));
  return out;
}

/** Does a y-UP board show `rows` (bottom-aligned)? `c` any filled cell, `U` empty (the slot), a
 *  letter that piece, `-` empty; nothing above the drawing. */
function shows(board: (string | null)[][], rows: string[], uEmpty: boolean): boolean {
  for (let y = 0; y < ROWS; y++) for (let x = 0; x < WIDTH; x++) {
    const i = rows.length - 1 - y;
    const ch = i >= 0 ? rows[i]![x]! : '-';
    const v = board[y]![x];
    if (ch === '-' || (ch === 'U' && uEmpty)) { if (v != null) return false; continue; }
    if (v == null) return false;
    if (ch === 'c') continue;
    if (v !== T_OF(ch)) return false;
  }
  return true;
}

/** The demo as a corpus round digest: no recorded game, so there is no prefix to verify (v is the
 *  last lock) and no garbage. */
function digestOf(d: any): RoundDigest {
  const locks: RoundDigest['locks'] = [], rows: RoundDigest['rows'] = [];
  const q = queueStates(d.seq, d.locks);
  const spin = ['none', 'mini', 'full'];
  decodeTimeline(d.seq, d.locks, (b, i, cleared) => {
    const lk = d.locks[i];
    locks.push({ piece: q[i]!.piece,
      cells: placeCells(q[i]!.piece, lk[1]).map(c => ({ col: c % WIDTH, row: ROWS - 1 - Math.floor(c / WIDTH) })),
      cleared: lk[2], spin: spin[lk[3]]!, allclear: lk[2] > 0 && b.every(r => r.every(c => c == null)),
      clearedRows: cleared.map(y => ROWS - 1 - y) });
    rows.push(rowsFromBoard([...b].reverse().map(r => r.map(c => c))));
  });
  return { session: 'demo', file: d.node, round: 0, user: 'demo', match: 0, file_sort_index: 0,
           bag2_order: d.seq.slice(7, 14), v: d.locks.length - 1, height: ROWS, garbage: [],
           n_locks: d.locks.length, locks, rows };
}

/** Every check that reads one demo. Returns the first failure, or null. */
function checkDemo(d: any, all: Map<string, any>): string | null {
  const n = byId.get(d.node);
  if (!n?.rows) return `${d.node}: not a board node`;
  // 6. whole 7-bags, holds, conditions
  if (d.seq.length % 7) return `${d.node}: seq is not whole bags`;
  for (let k = 0; k < d.seq.length; k += 7)
    if ([...d.seq.slice(k, k + 7)].sort().join('') !== [...PIECES].sort().join('')) return `${d.node}: bag ${k / 7} not a 7-bag`;
  if (d.bags.map((b: any) => b.queue).join('') !== d.seq.slice(0, 7 * d.bags.length)) return `${d.node}: bags are not the seq`;
  if (d.bags.reduce((a: number, b: any) => a + b.holds, 0) !== d.locks.filter((l: any) => l[5]).length)
    return `${d.node}: holds do not match the held flags`;
  for (const b of d.bags) {
    const c = byId.get(b.node)!.condition;
    if (c?.all && conditionHolds(c, b.queue, '') !== true) return `${b.node}: queue ${b.queue} breaks the page condition`;
    if (c?.early && b.queue[0] !== c.early) return `${b.node}: ${c.early} is not first in ${b.queue}`;
  }
  if (b1(d) && d.bags[0].queue[0] !== (routes as any).bag1.requires.early) return `${d.node}: bag 1 not L first`;
  // 2. re-run
  let rr;
  try { rr = runDemo(routes, d.seq, d.inputs, d.frames).rec; } catch (e) { return `${d.node}: re-run threw ${e}`; }
  if (JSON.stringify(rr.locks) !== JSON.stringify(d.locks)) return `${d.node}: re-run locks differ`;
  // 7. prefix sharing
  if (d.parent) {
    const p = all.get(d.parent);
    if (!p) return `${d.node}: parent ${d.parent} has no demo`;
    if (JSON.stringify(d.locks.slice(0, p.locks.length)) !== JSON.stringify(p.locks)) return `${d.node}: prefix differs from ${d.parent}`;
    if (d.seq.slice(0, p.locks.length) !== p.seq.slice(0, p.locks.length)) return `${d.node}: seq prefix differs`;
  }
  // 5. spins
  const q = queueStates(d.seq, d.locks);
  for (let i = 0; i < d.locks.length; i++) {
    const L = d.letters[i], lk = d.locks[i];
    if (T_OF(L) !== q[i]!.piece) return `${d.node}: lock ${i} letter ${L} vs piece ${q[i]!.piece}`;
    if (L === 'U') {
      if (lk[3] !== 2) return `${d.node}: U lock ${i} spin ${lk[3]}`;
      const bag = d.bags.findIndex((_: any, k: number) => d.bags.slice(0, k + 1).reduce((a: number, b: any) => a + b.placed.length, 0) > i);
      const bn = byId.get(d.bags[bag].node)! as any;
      const want = bn.bag === 2 ? 3 : bn.has_tsd_slot ? 2 : DEMO_SPIN_LINES[bn.id];
      if (want === undefined || lk[2] !== want) return `${d.node}: U lock ${i} cleared ${lk[2]}, want ${want}`;
    } else if (q[i]!.piece === 'T' && lk[3] !== 0 && !DEMO_SPIN_EXCEPTIONS.includes(d.node)) return `${d.node}: t lock ${i} spun`;
  }
  // 4. board equality
  const B = boards(d);
  const last = d.locks.length - 1;
  if (n.bag === 1) {
    if (!shows(B[last]!, n.rows, false)) return `${d.node}: final board is not the drawing`;
    if (n.id === 'bag1.z_hold' && q[last]!.hold !== 'Z') return `${d.node}: Z is not in the hold box`;
  } else if (n.bag === 2) {
    if (!shows(B[12]!, n.rows, true)) return `${d.node}: board after 13 pieces is not the drawing`;
    if (d.letters[13] !== 'U' || last !== 13) return `${d.node}: lock 14 is not the U`;
  } else if (n.list) {
    if (B[last]!.some(r => r.some(c => c != null))) return `${d.node}: last lock is not a Perfect Clear`;
    if (d.locks.reduce((a: number, l: any) => a + l[2], 0) !== 8) return `${d.node}: not 8 lines`;
  } else if (n.unmatchable) {
    if (!shows(B[last]!, n.rows, false)) return `${d.node}: final board is not the drawing`;
  } else {
    if (!shows(B[last - 1]!, n.rows, true)) return `${d.node}: board before the U is not the drawing`;
    if (d.letters[last] !== 'U') return `${d.node}: last lock is not the U`;
  }
  // 3. the classifier
  const c = classify([digestOf(d)], routes).cases[0];
  if (!c) return `${d.node}: classifier found no bag 1`;
  if (n.bag === 1 && c.bag1.node !== n.id) return `${d.node}: classifier bag 1 ${c.bag1.node}`;
  if (n.bag === 2 && (c.bag2?.node !== n.id || c.bag2.condition_met === false)) return `${d.node}: classifier bag 2 ${c.bag2?.node}`;
  if (n.list) {
    const dg = digestOf(d);
    const tst = dg.locks.findIndex(l => l.piece === 'T' && l.spin === 'full' && l.cleared === 3);
    const comp = composite(dg, tst, last);
    if (!patternMatches(comp, readRows(n.id, n.rows), false, true)) return `${d.node}: composite is not the pattern`;
    if (DEMO_PIECE_READINGS.includes(n.id)) {
      if (c.pc?.node === n.id) return `${d.node}: colour reading not needed?`;
    } else if (c.pc?.node !== n.id) return `${d.node}: classifier PC ${c.pc?.node} ${c.pc?.off_page_under}`;
  }
  if (n.bag === 3 && !n.list && !n.unmatchable && !c.snapshots.some((s: any) => s.node === n.id))
    return `${d.node}: classifier snapshot missing`;
  return null;
}
const b1 = (d: any) => byId.get(d.bags[0].node)!.bag === 1;

/** Completeness: every board node has exactly one demo or one unbuilt entry. */
function checkComplete(art: any): string | null {
  const demos = new Map<string, number>();
  for (const d of art.demos) demos.set(d.node, (demos.get(d.node) ?? 0) + 1);
  const unb = Object.fromEntries(art.unbuilt.map((u: any) => [u.node, u.reason]));
  if (JSON.stringify(unb) !== JSON.stringify(DEMO_UNBUILT)
      && JSON.stringify(Object.entries(unb).sort()) !== JSON.stringify(Object.entries(DEMO_UNBUILT).sort()))
    return `unbuilt ${JSON.stringify(unb)}`;
  for (const n of routes.nodes) {
    if (!n.rows) { if (demos.has(n.id)) return `${n.id}: demo for a node with no board`; continue; }
    const k = (demos.get(n.id) ?? 0) + (n.id in unb ? 1 : 0);
    if (k !== 1) return `${n.id}: ${k} demos/unbuilt entries`;
  }
  for (const id of demos.keys()) if (!byId.has(id)) return `${id}: not a route node`;
  return null;
}
function checkAll(art: any): string | null {
  const c = checkComplete(art);
  if (c) return c;
  const all = new Map<string, any>(art.demos.map((d: any) => [d.node, d]));
  for (const d of art.demos) { const e = checkDemo(d, all); if (e) return e; }
  if (JSON.stringify(art.demos.flatMap((d: any) => d.piece_readings.map((p: any) => p.node)).sort())
      !== JSON.stringify([...DEMO_PIECE_READINGS].sort())) return 'piece readings list differs';
  return null;
}

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

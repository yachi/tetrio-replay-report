/**
 * Property-based tests over random boards — the item forecast-metric.md lists as "Not done".
 *
 * Seeded, so a failure is reproducible: every case prints its seed. No fast-check dependency;
 * the generators here are domain-shaped (stack profiles, garbage rows) rather than uniform noise,
 * because uniform noise almost never produces a spinnable slot and would test nothing.
 *
 * The load-bearing property is EQUIV: `tspinAvailable(b)` and `bestTspinLines(b) > 0` are two
 * independently written implementations of one predicate. If they never disagree, one of them is
 * dead weight — and they carry DIFFERENT BFS caps (20000 vs 40000), which is a latent divergence.
 *
 * The second half of the file applies the same anti-vacuity treatment to `garbageLoadBearing`.
 * See the block comment above `GARBAGE FAMILIES` for what was vacuous and what fixes it.
 */
import { test, expect } from 'bun:test';
import { emptyBoard, H } from './sim.ts';
import { tspinAvailable, bestTspinLines, forecastMetric, garbageArrivedAfter } from './forecast.ts';
import type { SimResult } from './sim.ts';
import type { Board } from './vendor/core/srs.ts';

const W = 10;

/** MINSTD, same family as the piece RNG — deterministic and cheap. */
function rng(seed: number) {
  let t = seed % 2147483647; if (t <= 0) t += 2147483646;
  return () => ((t = (16807 * t) % 2147483647) - 1) / 2147483646;
}

const clone = (b: Board) => b.map(r => [...r]) as (string | null)[][];
const hasFullRow = (b: Board) => b.some(r => r.every(x => x !== null));

/** Stack profile: a random walk of column heights, then holes punched under the surface. */
function genStack(r: () => number): Board {
  const b = emptyBoard().map(row => [...row]) as (string | null)[][];
  let h = 2 + Math.floor(r() * 6);
  const heights: number[] = [];
  for (let c = 0; c < W; c++) {
    h = Math.max(0, Math.min(12, h + Math.floor(r() * 5) - 2));
    heights.push(h);
  }
  for (let c = 0; c < W; c++)
    for (let i = 0; i < heights[c]!; i++) b[H - 1 - i]![c] = 'I';
  const holes = Math.floor(r() * 6);
  for (let i = 0; i < holes; i++) {
    const c = Math.floor(r() * W);
    if (heights[c]! < 1) continue;
    const depth = Math.floor(r() * heights[c]!);
    b[H - 1 - depth]![c] = null;
  }
  return b as Board;
}

/** Garbage-like: solid rows each with one hole, holes sometimes aligned. */
function genGarbage(r: () => number): Board {
  const b = emptyBoard().map(row => [...row]) as (string | null)[][];
  const n = 1 + Math.floor(r() * 8);
  let hole = Math.floor(r() * W);
  for (let i = 0; i < n; i++) {
    if (r() < 0.4) hole = Math.floor(r() * W);
    for (let c = 0; c < W; c++) if (c !== hole) b[H - 1 - i]![c] = 'I';
  }
  return b as Board;
}

/** Sparse noise in the bottom rows — the degenerate case, kept as a control. */
function genNoise(r: () => number): Board {
  const b = emptyBoard().map(row => [...row]) as (string | null)[][];
  const p = 0.3 + r() * 0.5;
  for (let i = 0; i < 8; i++)
    for (let c = 0; c < W; c++) if (r() < p) b[H - 1 - i]![c] = 'I';
  return b as Board;
}

const GENS = [
  ['stack', genStack], ['garbage', genGarbage], ['noise', genNoise],
] as const;

const N = 400;   // per generator

interface Case { gen: string; seed: number; board: Board }
function* cases(): Generator<Case> {
  for (const [name, gen] of GENS)
    for (let s = 1; s <= N; s++) {
      const board = gen(rng(s * 7919));
      if (hasFullRow(board)) continue;   // would already have cleared; not a reachable state
      yield { gen: name, seed: s, board };
    }
}
const ALL = [...cases()];

test(`generators produce boards that actually exercise the probe (${ALL.length} boards)`, () => {
  expect(ALL.length).toBeGreaterThan(900);
  const spinnable = ALL.filter(c => tspinAvailable(c.board)).length;
  console.log(`    boards offering a line-clearing T-spin: ${spinnable}/${ALL.length}`);
  // If nothing is spinnable the whole suite is vacuous — this is the anti-vacuity gate.
  expect(spinnable).toBeGreaterThan(0);
});

test('EQUIV: tspinAvailable(b) === bestTspinLines(b) > 0', () => {
  const bad: string[] = [];
  for (const c of ALL) {
    const a = tspinAvailable(c.board), n = bestTspinLines(c.board);
    if (a !== n > 0) bad.push(`${c.gen}#${c.seed}: available=${a} bestLines=${n}`);
  }
  if (bad.length) console.log(`    disagreements:\n      ${bad.slice(0, 5).join('\n      ')}`);
  expect(bad).toEqual([]);
});

test('RANGE: a T-spin clears at most 3 lines', () => {
  for (const c of ALL) {
    const n = bestTspinLines(c.board);
    if (n < 0 || n > 3) throw new Error(`${c.gen}#${c.seed}: bestTspinLines=${n}`);
  }
});

test('PURITY: neither probe mutates the board it is handed', () => {
  for (const c of ALL.slice(0, 200)) {
    const before = JSON.stringify(c.board);
    tspinAvailable(c.board); bestTspinLines(c.board);
    if (JSON.stringify(c.board) !== before) throw new Error(`${c.gen}#${c.seed} mutated its input`);
  }
});

test('DETERMINISM: repeated calls agree', () => {
  for (const c of ALL.slice(0, 200))
    expect(bestTspinLines(c.board)).toBe(bestTspinLines(c.board));
});

test('EMPTY: a clean board offers no T-spin', () => {
  expect(tspinAvailable(emptyBoard())).toBe(false);
  expect(bestTspinLines(emptyBoard())).toBe(0);
});

/* ========================= GARBAGE FAMILIES ==================================================
 *
 * `garbageLoadBearing` had no non-vacuous test outside one hand fixture.
 *
 * Measured over the verified prefix of all four sessions (654 tucked T-spins): garbage arrives
 * after the roof in 121 of them — a non-empty deletion set — and the flag is true in **0**. So
 * `forecast-corpus.test.ts`'s "the scalar gate and the garbage counterfactual now agree on every
 * event" (`loadBearingButNotImproved === 0`) is `0 === 0`: it would pass identically if the flag
 * were hardcoded `false`, if it were never computed, or if `withoutRows` returned its input. Same
 * for `mechanism === 'garbage'` (0 of 654) and `roofIsGarbage` (0 of 654).
 *
 * The flag IS reachable — this is the reachable case, not the dead-code case — so the fix is a
 * POPULATION rather than a note. `forecast.test.ts` carries one wiki-grounded instance; a single
 * fixture states that the flag can be true, not that it discriminates. These two families are that
 * fixture's shape lifted to a parameter sweep, and the anti-vacuity gate below is the same one the
 * generator test at the top of this file applies: both arms must be non-empty.
 *
 *   A — the wiki's "Forecasting T-Spin Triples > Garbage" geometry, generalised over the well
 *       column and the notch side. The arriving row's hole sits UNDER the well, so it extends the
 *       well by one and the T's landing drops a row — which is the whole trick, because the nub
 *       only lines up with the notch after that shift. avail 0 -> 3, and deleting the arrival puts
 *       it back to 0. Load-bearing.
 *   B — the same slot built entirely in the player's own stack, with garbage arriving BELOW it and
 *       its holes elsewhere, so the stack is lifted rigidly and the landing does not move.
 *       avail 3 -> 3, and deleting the arrival leaves 3. Not load-bearing.
 *
 * B reproduces the corpus's OUTCOME — measured, all 121 real arrivals leave the executed spin
 * standing — not necessarily its geometry, which was not censused. A is an outcome 654 events of
 * real play never produce, which is exactly why it has to be built rather than found.
 *
 * What is NOT here, and is a measured absence rather than an oversight: a case that is BOTH
 * `reactive` and load-bearing — the conjunction the corpus test actually counts. It needs
 * `avail(roof) >= avail(spin)` while the arrival is load-bearing, i.e. the pre-window board must
 * already offer at least what the garbage later produces, on a board that is a STRICT SUBSET of
 * the one the garbage lands on. Every row of a line-clearing T-slot has to be full but for the T's
 * own cells, so a sparser board cannot hold a richer slot at the same depth, and a second slot
 * elsewhere would have to sit in rows that block the descent to the first. No such case was
 * constructed and none occurs in 654 events; the honest statement is that this arm is unpinned.
 */

const allBut = (cols: number[], ch = '#') =>
  [...Array(W)].map((_, i) => (cols.includes(i) ? '.' : ch)).join('');
const only = (cols: number[], ch = '#') =>
  [...Array(W)].map((_, i) => (cols.includes(i) ? ch : '.')).join('');

/** rows given BOTTOM-UP, bottom-aligned into a full-height board. 'G' is garbage. */
const fromBottom = (rows: string[]): Board => {
  const b = Array.from({ length: H }, () => new Array<string | null>(W).fill(null));
  rows.forEach((line, i) => [...line].forEach((ch, c) => {
    if (ch !== '.') b[H - 1 - i]![c] = ch === 'G' ? 'G' : 'I';
  }));
  return b as Board;
};

/** the counterfactual taken from the CONSTRUCTION — the g rows this test inserted, not a derived set */
const dropBottom = (b: Board, g: number): Board =>
  [...Array.from({ length: g }, () => new Array(W).fill(null)), ...b.slice(0, H - g)] as Board;

/** the wall-and-roof the T has to kick past; `s` is the side the notch is on */
const entryRows = (c: number, s: number) => [only([c - s, c - 2 * s]), only([c, c - s]), only([c])];

interface GarbCase {
  fam: 'A' | 'B'; c: number; s: number; g: number; amt: number;
  spin: Board; sim: SimResult;
}

/**
 * A four-lock history: the stack, the roof (lock 1), the garbage arrival (lock 2), the T (lock 3).
 *
 * The whole pre-window stack is attributed to lock 1, so `j` names the roof and the window is
 * exactly the arrival. Locks 0 and 2 place no cells: `garbageArrivedAfter` and `localiseMechanism`
 * both reconstruct each step from `boards[t-1]` plus that lock's cells, so an empty placement is a
 * step that only inserts garbage — which is the step under test.
 *
 * `amt` is swept over the truthful value AND one row more, because the deletion set is derived
 * from the events and then intersected with the rows that actually carry garbage. An over-claiming
 * event marks the stack row above the arrivals, and only that intersection stops it being deleted —
 * which would take the slot's own floor with it and read as causation. Without the over-claiming
 * half of the sweep that guard is unkillable here, and the fixtures in forecast.test.ts already
 * establish that a hand-built SimResult's events need not agree with its boards.
 */
function mkSim(base: Board, spin: Board, g: number, amt: number,
               tCells: { col: number; row: number }[]): SimResult {
  const provOf = (b: Board) => b.map(row =>
    row.map(cell => cell === null ? null : (cell as unknown as string) === 'G' ? -1 : 1));
  const filler = (frame: number) =>
    ({ frame, piece: 'L', cells: [], cleared: 0, spin: 'none', allclear: false });
  return {
    lines: 0, placed: 0, holds: 0, clears: {}, topbtb: 0, topcombo: 0,
    garbage: { sent: 0, received: 0, cleared: 0, attack: 0 },
    boards: [base, base, spin, spin],
    records: [], events: [],
    locks: [filler(0), filler(100), filler(200),
      { frame: 300, piece: 'T', cells: tCells, cleared: 3, spin: 'full', allclear: false }],
    garbageEvents: [{ frame: 200, amt, lockIndex: 2 }],
    provSnaps: [provOf(base), provOf(base), provOf(spin), provOf(spin)],
    topout: false,
  } as unknown as SimResult;
}

function garbCase(fam: 'A' | 'B', c: number, s: number, g: number, hole: number,
                  amt: number): GarbCase | null {
  const n = c + s;
  if (n < 0 || n > 9 || c - 2 * s < 0 || c - 2 * s > 9 || hole === c) return null;
  // A: only the TOPMOST arriving row is holed under the well; deeper ones just hold the stack up.
  const gar = Array.from({ length: g }, (_, i) =>
    allBut([fam === 'A' && i === g - 1 ? c : hole], 'G'));
  const stack = fam === 'A'
    ? [allBut([c, n]), allBut([c]), ...entryRows(c, s)]
    : [allBut([c]), allBut([c, n]), allBut([c]), ...entryRows(c, s)];
  const base = fromBottom(stack), spin = fromBottom([...gar, ...stack]);
  // the T's bar bottoms out on the lowest row of the well: the top arriving row in A, the stack's
  // own bottom row in B. The nub is always the middle of the bar, which is the shift that matters.
  const bottomRow = fam === 'A' ? H - g : H - 1 - g;
  const tCells = [{ col: c, row: bottomRow }, { col: c, row: bottomRow - 1 },
                  { col: c, row: bottomRow - 2 }, { col: n, row: bottomRow - 1 }];
  // The edge columns degenerate (the notch or the wall runs off the field) and offer no spin at
  // all. Dropping them by MEASUREMENT rather than by a column range keeps the filter honest.
  if (bestTspinLines(spin) === 0) return null;
  return { fam, c, s, g, amt, spin, sim: mkSim(base, spin, g, amt, tCells) };
}

const GARB: GarbCase[] = [];
for (const fam of ['A', 'B'] as const)
  for (const s of [-1, 1])
    for (let c = 0; c < W; c++)
      for (const g of [1, 2, 3])
        for (const hole of [0, 9])
          for (const amt of [g, g + 1]) {
            const k = garbCase(fam, c, s, g, hole, amt);
            if (k) GARB.push(k);
          }

const label = (k: GarbCase) => `${k.fam} c=${k.c} s=${k.s} g=${k.g} amt=${k.amt}`;

const REC = GARB.map(k => {
  const out = forecastMetric(k.sim, true);
  if (out.records.length !== 1)
    throw new Error(`${label(k)}: ${out.records.length} records, expected 1`);
  return { ...k, rec: out.records[0]! };
});

test(`GARBAGE-REACHABLE: garbageLoadBearing is true somewhere and false somewhere (${REC.length} cases)`, () => {
  const yes = REC.filter(x => x.rec.garbageLoadBearing);
  const no = REC.filter(x => !x.rec.garbageLoadBearing);
  // MEASURED, not assumed: the flag short-circuits on an empty deletion set, so a case with no
  // in-window arrival would report `false` without ever running the counterfactual. Counting the
  // set the metric itself derives is what says the second conjunct is reached in every case.
  const arrived = REC.filter(x =>
    garbageArrivedAfter(x.sim, x.rec.roofFrom ?? -1, x.rec.lockIndex).size > 0);
  console.log(`    garbage arrived in-window: ${arrived.length}/${REC.length}`
    + `  load-bearing: ${yes.length}  not: ${no.length}`);
  expect(arrived.length).toBe(REC.length);
  // Without both arms every assertion below would hold for a flag that is never computed.
  expect(yes.length).toBeGreaterThan(0);
  expect(no.length).toBeGreaterThan(0);
  expect(yes.every(x => x.fam === 'A')).toBe(true);
  expect(no.every(x => x.fam === 'B')).toBe(true);
  // both halves of the amt sweep survived the degenerate-column filter, in both arms
  for (const arm of [yes, no])
    for (const over of [false, true])
      expect(arm.filter(x => (x.amt > x.g) === over).length).toBeGreaterThan(0);
});

test('GARBAGE-ORACLE: the flag agrees with a deletion set taken from the construction', () => {
  // The flag DERIVES its deletion set by walking the window (`garbageArrivedAfter`). This test
  // knows the answer instead: it inserted the bottom `g` rows itself. Comparing the two is a
  // differential between construction truth and derivation — not a restatement of the expression,
  // which is why the row deletion here is written out rather than reusing `withoutRows`.
  const bad: string[] = [];
  for (const x of REC) {
    const avail = bestTspinLines(x.spin);
    const want = bestTspinLines(dropBottom(x.spin, x.g)) < avail;
    if (x.rec.garbageLoadBearing !== want)
      bad.push(`${label(x)}: flag=${x.rec.garbageLoadBearing} construction=${want}`);
    if (x.rec.availAtSpin !== avail)
      bad.push(`${label(x)}: availAtSpin=${x.rec.availAtSpin} board=${avail}`);
  }
  expect(bad).toEqual([]);
});

test('GARBAGE-CLASSIFIER: a load-bearing arrival is classified forecast_garbage, never reactive', () => {
  // This is `forecast-corpus.test.ts`'s `loadBearingButNotImproved === 0` over a population where
  // the flag is actually true, so the zero says something. The corpus cannot supply one: none of
  // its 121 arrivals is load-bearing, and 0 of 654 events reach `mechanism === 'garbage'` at all.
  const lb = REC.filter(x => x.rec.garbageLoadBearing);
  expect(lb.length).toBeGreaterThan(0);
  expect(lb.filter(x => x.rec.kind === 'reactive')).toEqual([]);
  for (const x of lb) {
    expect(x.rec.kind).toBe('forecast_garbage');
    expect(x.rec.mechanism).toBe('garbage');
    expect(x.rec.availAtRoof).toBe(0);
  }
  // ...and the other arm is genuinely the other verdict, not merely a different flag value.
  for (const x of REC.filter(x => !x.rec.garbageLoadBearing)) expect(x.rec.kind).toBe('reactive');
});

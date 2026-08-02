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
 */
import { test, expect } from 'bun:test';
import { emptyBoard, H } from './sim.ts';
import { tspinAvailable, bestTspinLines } from './forecast.ts';
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

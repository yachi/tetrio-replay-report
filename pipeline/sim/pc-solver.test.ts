/**
 * pc-solver.ts and pc-engine-gen.ts: the rules the missed-PC finder (pc-miss.ts) rests on.
 *   bun test pipeline/sim/pc-solver.test.ts
 */
import { expect, test } from 'bun:test';
import { apply, frames, placements, setMovegen, solve, W } from './pc-solver.ts';
import { enginePlacements } from './pc-engine-gen.ts';

const FULL = (1 << W) - 1;
const rowsOf = (pic: string[]) => pic.slice().reverse().map(r => [...r].reduce((a, c, x) => a | (c === '#' ? 1 << x : 0), 0));

/** Replays a plan from the solver on its own and asserts it really clears the board. */
function replay(rows: number[], H: number, plan: { cells: number[] }[]) {
  let r = rows, h = H;
  for (const p of plan) {
    for (const c of p.cells) {
      expect(Math.floor(c / W)).toBeLessThan(h);
      expect((r[Math.floor(c / W)] ?? 0) >> (c % W) & 1).toBe(0);
    }
    const a = apply(r, p.cells, h); r = a.rows; h = a.H;
  }
  expect(r.length).toBe(0);
  expect(h).toBe(0);
}

test('apply clears full rows inside the frame and shrinks it', () => {
  const a = apply([FULL ^ 0b1111], [0, 1, 2, 3], 2);
  expect(a.cleared).toBe(1);
  expect(a.H).toBe(1);
  expect(a.rows).toEqual([]);
});

test('frames keep (10H − filled) a positive multiple of four', () => {
  expect(frames([], 4)).toEqual([2, 4]);
  expect(frames([FULL ^ 0b11], 4)).toEqual([2, 4]);   // 8 filled: 12 and 32 cells left
});

test('every frame frames() returns has a cell count divisible by four', () => {
  for (const rows of [[], [0b1], [FULL ^ 0b11], [0b111, 0b1]])
    for (const H of frames(rows, 6)) {
      const n = rows.reduce((a, m) => a + [...m.toString(2)].filter(c => c === '1').length, 0);
      expect((H * W - n) % 4).toBe(0);
    }
});

test('a 2-line PC from an empty board with I I O O O… is found and replays', () => {
  // 20 cells: two horizontal I's and three O's fill a 10x2 frame
  const v = solve([], 2, 'I', '', 'IOOO', 0, new Map(), { nodes: 1e6 });
  expect(v.ok).toBe(true);
  if (v.ok) replay([], 2, v.plan);
});

test('S S S S … cannot perfect-clear an empty 4-row frame', () => {
  const v = solve([], 4, 'S', '', 'SSSSSSSSSSSS', 0, new Map(), { nodes: 1e6 });
  expect(v.ok).toBe(false);
});

test('a hold changes the answer: the only fitting piece is reachable through hold alone', () => {
  // one empty I slot along the bottom row's right end
  const rows = rowsOf(['######....']);
  expect(solve(rows, 1, 'O', '', 'O', 0, new Map(), { nodes: 1e5 }).ok).toBe(false);
  const v = solve(rows, 1, 'O', 'I', 'O', 0, new Map(), { nodes: 1e5 });
  expect(v.ok).toBe(true);
  if (v.ok) { expect(v.plan[0]!.held).toBe(true); replay(rows, 1, v.plan); }
});

test('a sequence that runs out is unknown, never "impossible"', () => {
  const v = solve([], 4, 'I', '', 'I', 0, new Map(), { nodes: 1e5 });
  expect(v.ok).toBe(null);
});

test("the engine's movegen reaches every placement the SRS movegen does", () => {
  const boards = [[], rowsOf(['##.#######', '#..#######']), rowsOf(['#.........', '##....####'])];
  for (const rows of boards) for (const p of 'IJLOSTZ') {
    const srs = placements(rows, p, 4).map(c => c.join(','));
    setMovegen(enginePlacements);
    const eng = new Set(placements(rows, p, 4).map(c => c.join(',')));
    setMovegen(null);
    for (const k of srs) expect(eng.has(k)).toBe(true);
  }
});

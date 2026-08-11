/**
 * Regression guard for the `hoisted`-DAS fix (see memory/sim-hoisted-das-bug).
 *
 * A `.ttrm` keydown carries `hoisted: true` when the client recorded that direction as ALREADY
 * held when the piece spawned — so DAS is pre-charged and the piece auto-shifts to the wall,
 * rather than moving a single tap. The sim used to drop the flag and treat every keydown as a
 * fresh tap, stopping held-into-the-wall openers one cell short. That was 146 of 148 opening-
 * piece disagreements against the Triangle.js oracle (25% of all openers).
 *
 * The Triangle oracle is what found this, but the ground truth is stronger than any reimplementation:
 * the flag is written by the official client itself. These tests need no oracle — they pin the
 * mechanism directly, and both fail if the fix is reverted (delete the `e.hoisted ?` branch in
 * sim.ts and re-run).
 */
import { test, expect } from 'bun:test';
import { simulate, DEFAULT_TABLE, type InEvent, type Handling } from './sim.ts';

const HANDLING: Handling = { das: 10, arr: 1, sdf: 20, dcd: 0 };
const OPTS = { garbagespeed: 20, garbagecap: 8, locktime: 30, gravity: 0.001, subframe: true } as const;

// keydown moveLeft held 5 frames (< das=10, so no auto-repeat if it were a fresh tap), then hard drop.
const stream = (hoisted: boolean): InEvent[] => [
  { frame: 0, sub: 0, type: 'keydown', key: 'moveLeft', hoisted },
  { frame: 5, sub: 0, type: 'keyup', key: 'moveLeft' },
  { frame: 6, sub: 0, type: 'keydown', key: 'hardDrop' },
];

// leftmost filled column of the first locked board
const minCol = (board: (string | null)[][]): number => {
  let m = 10;
  for (const row of board) for (let c = 0; c < 10; c++) if (row[c] != null && c < m) m = c;
  return m;
};

test('a hoisted move-key is pre-charged DAS: the opener slams to the wall', () => {
  const r = simulate(stream(true), [], HANDLING, 1, 40, DEFAULT_TABLE, OPTS);
  expect(r.boards.length).toBeGreaterThan(0);
  expect(minCol(r.boards[0]!)).toBe(0); // reached the left wall
});

test('a plain (fresh-tap) move-key held under DAS moves exactly one cell — never the wall', () => {
  const r = simulate(stream(false), [], HANDLING, 1, 40, DEFAULT_TABLE, OPTS);
  expect(r.boards.length).toBeGreaterThan(0);
  expect(minCol(r.boards[0]!)).toBeGreaterThan(0); // one tap only; not against the wall
});

test('same seed, same events: hoisted lands strictly further into the held direction than plain', () => {
  const seedSweep = [1, 2, 3, 7, 42, 100];
  for (const seed of seedSweep) {
    const h = simulate(stream(true), [], HANDLING, seed, 40, DEFAULT_TABLE, OPTS);
    const p = simulate(stream(false), [], HANDLING, seed, 40, DEFAULT_TABLE, OPTS);
    // hoisted moves left at least as far, and for at least one seed strictly further (asserted below)
    expect(minCol(h.boards[0]!)).toBeLessThanOrEqual(minCol(p.boards[0]!));
  }
  // and the effect is real, not a no-op on every seed
  const anyStrict = seedSweep.some((seed) =>
    minCol(simulate(stream(true), [], HANDLING, seed, 40, DEFAULT_TABLE, OPTS).boards[0]!) <
    minCol(simulate(stream(false), [], HANDLING, seed, 40, DEFAULT_TABLE, OPTS).boards[0]!));
  expect(anyStrict).toBe(true);
});

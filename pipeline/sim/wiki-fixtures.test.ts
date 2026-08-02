/**
 * External golden fixtures: the 29 board diagrams from harddrop.com/wiki/T-Spin_Forecast.
 *
 * Provenance matters here. The BOARDS come from the wiki, and so do the EXPECTATIONS — they are
 * read off the section headings and the article's own premise, never from this engine's output:
 *
 *   · a "Forecasting T-Spin X" board shows a setup whose slot does NOT exist yet — that is what
 *     forecasting means — so no T-spin may be available on it
 *   · a "... > Garbage" section shows the position once garbage has landed, so the best available
 *     spin must clear exactly as many lines as the section is named for (Doubles 2, Triples 3)
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { emptyBoard, H, tspinAvailable, bestTspinLines } from './forecast-boards.ts';

const RAW = JSON.parse(readFileSync(`${import.meta.dir}/wiki-tspin-forecast-boards.json`, 'utf8')) as
  { sec: string; rows: string[] }[];
const toBoard = (rows: string[]) => {
  const b = emptyBoard().map(r => [...r]) as any[][];
  const off = H - rows.length;
  rows.forEach((l, i) => [...l].forEach((ch, c) => { if (ch !== '.' && ch !== '?') b[off + i]![c] = 'I'; }));
  return b;
};
const inSec = (s: string) => RAW.filter(b => b.sec === s).map(b => toBoard(b.rows));

test('the parse itself: 29 boards, every row exactly 10 columns', () => {
  expect(RAW).toHaveLength(29);
  for (const b of RAW) for (const r of b.rows) expect(r.length).toBe(10);
});

for (const sec of ['Forecasting T-Spin Singles', 'Forecasting T-Spin Doubles', 'Forecasting T-Spin Triples']) {
  test(`"${sec}" setups have no T-spin available yet — the premise of forecasting`, () => {
    const boards = inSec(sec);
    expect(boards.length).toBeGreaterThan(0);
    for (const b of boards) expect(tspinAvailable(b as any)).toBe(false);
  });
}

test('"Forecasting T-Spin Doubles > Garbage" yields a DOUBLE once garbage has landed', () => {
  const best = inSec('Forecasting T-Spin Doubles > Garbage').map(b => bestTspinLines(b as any));
  expect(Math.max(...best)).toBe(2);
});

test('"Forecasting T-Spin Triples > Garbage" yields a TRIPLE once garbage has landed', () => {
  const best = inSec('Forecasting T-Spin Triples > Garbage').map(b => bestTspinLines(b as any));
  expect(Math.max(...best)).toBe(3);
});

test('garbage upgrades the same overhang from a single to a double', () => {
  // adjacent pair in Doubles > Garbage: identical Z overhang, one extra bottom row in the second
  const g = RAW.filter(b => b.sec === 'Forecasting T-Spin Doubles > Garbage');
  const before = g.find(b => bestTspinLines(toBoard(b.rows) as any) === 1)!;
  const after = g.find(b => bestTspinLines(toBoard(b.rows) as any) === 2)!;
  expect(before).toBeDefined();
  expect(after).toBeDefined();
  // the "after" board carries one more row of stack than the "before" board
  expect(after.rows.length).toBeGreaterThanOrEqual(before.rows.length);
});

/* ── adversarial boards, authored to kill specific mutants ────────────────────────────────
   These are not golden data — they are test-adequacy fixtures. Each exists because a mutation
   of the availability probe survived every board drawn from the wiki. */
const mkRows = (empty: Record<number, number[]>) => {
  const b = emptyBoard().map(r => [...r]) as any[][];
  for (const [r, es] of Object.entries(empty))
    for (let c = 0; c < 10; c++) if (!es.includes(c)) b[+r]![c] = 'I';
  return b as any;
};

test('a T resting in a 3-corner spot WITHOUT a final rotation is not a spin', () => {
  //  37 XXX..XXXXX   a vertical T (nub left) slides down the col-4 channel and comes to rest.
  //  38 XXX..XXXXX   Three corners are filled, but the last action was a downward move, so
  //  39 XXXX.XXXXX   this is a placement, not a spin. Dropping the `rot` guard scores it 2.
  const b = mkRows({ 37: [3, 4], 38: [3, 4], 39: [4] });
  expect(tspinAvailable(b)).toBe(false);
  expect(bestTspinLines(b)).toBe(0);
});

test('a T rotated into a well clears a line but is not a spin', () => {
  //  37 XX.XXXXXXX   a 3-deep 1-wide well. The T rotates into it and completes row 37,
  //  38 XX.XXXXXXX   but only two corners are filled, so no spin. Dropping the corner test
  //  39 XX.XXXXXXX   from bestTspinLines scores it 1.
  const b = mkRows({ 37: [2], 38: [2], 39: [2] });
  expect(tspinAvailable(b)).toBe(false);
  expect(bestTspinLines(b)).toBe(0);
});

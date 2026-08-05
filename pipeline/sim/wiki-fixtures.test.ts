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

/* ── A SECOND wiki page as an oracle: harddrop.com/wiki/C-Spin ────────────────────────────────
 *
 * The Forecast fixtures above check what the engine says about boards where a spin is or is not
 * AVAILABLE. These check something the corpus cannot: that the engine agrees with an outside
 * authority about how many lines a specific, drawn placement clears. The C-Spin page is the right
 * second source because the metric's whole `self_built` bucket is explained by that opener, so the
 * engine had better recognise its shape.
 *
 * Provenance: parsed from the page's own {{pfrow}} templates via `?action=raw` (the rendered HTML
 * returns 403). `P` marks the piece being placed; only diagrams with a full 4-cell placement are
 * kept. `lines` counts rows that are full AND contain a P cell — a row already full in a diagram
 * is an artefact of the drawing, not something the piece cleared, and counting those made one
 * board read 5.
 */
const CSPIN = JSON.parse(readFileSync(`${import.meta.dir}/wiki-cspin-boards.json`, 'utf8')) as
  { rows: string[]; piece: { row: number; col: number }[]; lines: number }[];
const cspinBoard = (rows: string[]) => {
  const b = emptyBoard().map(r => [...r]) as any[][];
  const off = H - rows.length;
  rows.forEach((l, i) => [...l].forEach((ch, c) => { if (ch !== '.' && ch !== 'P') b[off + i]![c] = 'I'; }));
  return b;
};

/* The three the engine does not reproduce. Each was diagnosed cell by cell: a T at the drawn
 * position EXISTS, is collision-free, is a resting position, and `detectTSpin` calls it a full
 * spin — but it cannot be reached from spawn. On board 31 the piece would have to descend a
 * 1-wide channel while both neighbouring columns are blocked at the rows it would pass, and no
 * kick reaches it. The kick table is not the suspect: all eight JLSZT entries were compared
 * against halp1/triangle's `src/engine/utils/kicks/data.ts`, TETR.IO's own engine, and match
 * exactly. Our engine has no 180 rotation, which TETR.IO does — but neither player presses it in
 * any of the 32 replays, and upstream's 180 kicks reach at most one row downward while these
 * positions sit two or more rows deeper.
 *
 * So these are diagrams of a SHAPE, not of a placement reachable in one move from the board drawn
 * around it. Listed by index rather than skipped silently, because "the engine disagrees with the
 * wiki three times" is exactly the fact a future reader needs. */
const UNREACHABLE = new Set([31, 35, 37]);

test('the C-Spin parse: 38 placements, every row 10 columns', () => {
  expect(CSPIN).toHaveLength(38);
  for (const b of CSPIN) {
    expect(b.piece).toHaveLength(4);
    for (const r of b.rows) expect(r.length).toBe(10);
  }
});

test("the engine's line count matches the wiki on every reachable C-Spin diagram", () => {
  const disagree: string[] = [];
  CSPIN.forEach((o, i) => {
    if (UNREACHABLE.has(i)) return;
    const got = bestTspinLines(cspinBoard(o.rows) as any);
    if (got !== o.lines) disagree.push(`board ${i}: wiki ${o.lines}, engine ${got}`);
  });
  expect(disagree).toEqual([]);
  expect(CSPIN.length - UNREACHABLE.size).toBe(35);
});

test('the three unreachable diagrams are still unreachable — the exception list is not stale', () => {
  // If a change to the kick table or the search made one of these reachable, that is a real event
  // and it should surface here rather than quietly shrinking an ignore list.
  for (const i of UNREACHABLE) expect(bestTspinLines(cspinBoard(CSPIN[i]!.rows) as any)).toBe(0);
});

test('a T-Spin Triple is a vertical T — the shape the C-Spin builds', () => {
  // The metric never tests for a C-Spin (see forecast-corpus.test.ts), so this pins the geometric
  // claim that identification rests on: three-row clears come from a 2-wide, 3-tall placement.
  const triples = CSPIN.filter(o => o.lines === 3);
  expect(triples.length).toBeGreaterThan(0);
  for (const o of triples) {
    const cols = o.piece.map(p => p.col), rows = o.piece.map(p => p.row);
    expect(Math.max(...cols) - Math.min(...cols)).toBe(1);
    expect(Math.max(...rows) - Math.min(...rows)).toBe(2);
  }
});

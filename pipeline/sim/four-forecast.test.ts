/**
 * External golden fixtures: the T-Spin Forecast diagrams from four.lol
 * (four.lol/stacking/tetris/#forecasting), a THIRD external corpus alongside harddrop
 * (wiki-fixtures.test.ts) and Tetrisちゃんねる (jp-forecast.test.ts).
 *
 * Provenance is the cleanest of the three. four.lol renders its boards client-side from **fumen**
 * codes (examples credited to kazu); the rendered DOM is build-hashed styled-components and useless
 * as a fixture, but the fumen codes underneath are stable authored content. So the capture is at the
 * fumen layer: the nine forecast-section fumens live in four-forecast-fumens.json, decoded by
 * `py_fumen` (a trusted third-party decoder) into four-forecast-boards.json — 26 frames, because
 * each fumen is a sequence and every page is a frame. This bun test is the CI gate: it needs no
 * fumen decoder, so it checks the committed JSON's integrity, ties it to the committed fumens, and
 * pins two frames as golden anchors. `python3 -m pipeline.sim.extract_four_forecast` re-decodes
 * byte-identically from the fumens (needs py_fumen) — any fumen tool reproduces the same boards,
 * which is the second-implementation check the invariant wants.
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { emptyBoard, H, bestTspinLines } from './forecast-boards.ts';

const DOC = JSON.parse(readFileSync(`${import.meta.dir}/four-forecast-boards.json`, 'utf8')) as
  { boards: { section: string; page: number; rows: string[] }[] };
const FUMENS = JSON.parse(readFileSync(`${import.meta.dir}/four-forecast-fumens.json`, 'utf8')) as
  { section: string; fumen: string }[];
const BOARDS = DOC.boards;
const LEGAL = new Set([...'.#ZSJLOTI']);
const PIECES = new Set([...'ZSJLOTI']);

const toBoard = (rows: string[]) => {
  const b = emptyBoard().map(r => [...r]) as any[][];
  const off = H - rows.length;
  rows.forEach((l, i) => [...l].forEach((ch, c) => { if (ch !== '.') b[off + i]![c] = 'I'; }));
  return b;
};

test('the decode: 26 frames from 9 fumens, every row 10 columns, only legal glyphs', () => {
  expect(FUMENS).toHaveLength(9);
  for (const f of FUMENS) expect(f.fumen.startsWith('v115@')).toBe(true);
  expect(BOARDS).toHaveLength(26);
  for (const b of BOARDS) for (const r of b.rows) {
    expect(r.length).toBe(10);
    for (const ch of r) expect(LEGAL.has(ch)).toBe(true);
  }
});

test('every frame belongs to a fumen section, with the expected expansion', () => {
  const secs = new Set(FUMENS.map(f => f.section));
  for (const b of BOARDS) expect(secs.has(b.section)).toBe(true);
  const per: Record<string, number> = {};
  for (const b of BOARDS) per[b.section] = (per[b.section] ?? 0) + 1;
  expect(per).toEqual({ basic: 11, others: 9, prophecy: 3, 'fixing-misdrops': 3 });
});

test('all seven tetromino colours appear — the decode kept per-cell piece types', () => {
  const seen = new Set<string>();
  for (const b of BOARDS) for (const r of b.rows) for (const ch of r) if (PIECES.has(ch)) seen.add(ch);
  expect([...seen].sort().join('')).toBe('IJLOSTZ');
});

/* Golden anchors: two decoded frames, checked by a human on 2026-08-09 to be valid boards matching
 * the four.lol diagrams. Pinned exactly so a decoder or data drift fails loudly. */
test('golden anchors — the fumen decode is pinned', () => {
  const has = (rows: string[]) => BOARDS.some(b =>
    b.rows.length === rows.length && b.rows.every((r, i) => r === rows[i]));
  expect(has(['.....##...', '...######.', '...#######', '...#######',
              '.#########', '.#########', '#.########'])).toBe(true);        // basic, first frame
  expect(has(['..##...SLL', '#####..SSL', '#####...SL', '#####..###', '#####..###',
              '#####..###', '#####..###', '#####TTT##', '######T###'])).toBe(true);  // prophecy
});

test('every frame loads into the engine without throwing', () => {
  // Smoke only, and NOT bounded at 3 — these frames include mid-sequence states and drawn-complete
  // rows, same as the jp-forecast set. What is guaranteed is a readable board and a non-negative int.
  for (const b of BOARDS) {
    const n = bestTspinLines(toBoard(b.rows) as any);
    expect(Number.isInteger(n)).toBe(true);
    expect(n).toBeGreaterThanOrEqual(0);
  }
});

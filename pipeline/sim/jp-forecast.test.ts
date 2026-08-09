/**
 * External golden fixtures: the 38 T-Spin Forecast (予報の技法) diagrams from Tetrisちゃんねる
 * (tetrisch.github.io/main/technic/forecast.html) — an independent, Japanese-language corpus,
 * distinct from harddrop's 29 (see wiki-fixtures.test.ts).
 *
 * Provenance is the whole point here. Harddrop encodes its boards as HTML cell-tables, so they parse
 * from text. This page ships each board as a composite JPEG, so the grids in jp-forecast-boards.json
 * were read by a DETERMINISTIC pixel sampler (pipeline/sim/extract_jp_forecast.py) over the source
 * images committed under spec/fixtures/jp-forecast/ — never by eye. This test is the CI-side gate: it
 * needs no image decoder, so it checks the committed JSON's integrity, binds it to the committed
 * images, and pins the three boards a human independently read off the source (the golden anchors),
 * so a silent drift in the extractor or the JSON fails loudly. The byte-identity re-extraction from
 * the images is the Python side (`python3 -m pipeline.sim.extract_jp_forecast`), which needs Pillow.
 *
 * What is NOT asserted, and why: harddrop's boards carry section headings ("... > Garbage") that fix
 * the expected spin, so that test can check the engine's verdict against the page's own premise.
 * These 38 are frames of step-by-step sequences with no per-board label, and many are mid-setup
 * states with a floating overhang — so a blanket "no spin available" or "no floating cell" would be
 * false by construction. Over-asserting a semantics the source does not label would be writing for
 * the checker. The teeth here are integrity + palette coverage + the golden anchors.
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { emptyBoard, H, bestTspinLines } from './forecast-boards.ts';

const DOC = JSON.parse(readFileSync(`${import.meta.dir}/jp-forecast-boards.json`, 'utf8')) as
  { boards: { img: string; rows: string[] }[] };
const BOARDS = DOC.boards;
const LEGAL = new Set([...'.#ZSJLOTI']);
const PIECES = new Set([...'ZSJLOTI']);

const toBoard = (rows: string[]) => {
  const b = emptyBoard().map(r => [...r]) as any[][];
  const off = H - rows.length;
  rows.forEach((l, i) => [...l].forEach((ch, c) => { if (ch !== '.') b[off + i]![c] = 'I'; }));
  return b;
};

test('the parse: 38 boards, every row exactly 10 columns, only legal glyphs', () => {
  expect(BOARDS).toHaveLength(38);
  for (const b of BOARDS) for (const r of b.rows) {
    expect(r.length).toBe(10);
    for (const ch of r) expect(LEGAL.has(ch)).toBe(true);
  }
});

test('the JSON is bound to the committed source images, one-to-one', () => {
  const imgs = readdirSync(`${import.meta.dir}/../../spec/fixtures/jp-forecast`)
    .filter(f => f.endsWith('.jpg')).map(f => f.replace(/\.jpg$/, '')).sort();
  expect(imgs).toHaveLength(38);
  expect(BOARDS.map(b => b.img).sort()).toEqual(imgs);
});

test('all seven tetromino colours appear — the classifier palette is fully exercised', () => {
  // If the extractor ever collapsed two guideline colours (e.g. orange L into red Z), a letter
  // would vanish from the corpus. Set-equality catches exactly that.
  const seen = new Set<string>();
  for (const b of BOARDS) for (const r of b.rows) for (const ch of r) if (PIECES.has(ch)) seen.add(ch);
  expect([...seen].sort().join('')).toBe('IJLOSTZ');
});

/* Golden anchors: three boards read off the source JPEGs BY A HUMAN on 2026-08-09, independently of
 * the pixel sampler. They are pinned exactly, so the two readings must keep agreeing — the second
 * independent record this repo's invariant requires, standing in for a second parser. */
const ANCHORS: Record<string, string[]> = {
  foreacast_001: ['..........', '..........', '..........', '..........',
                  '######....', '#########.', '#######.##', '#######.##'],
  foreacast_022: ['..........', '..........', '..........', '..........', '..........',
                  '..ZZ......', '...ZZ#####', '...#######', '...#######', '...#######',
                  '...#######', 'JJ.#######', 'J..#######', 'J..#######'],
  foreacast_038: ['..........', '..........', '..........', '.....OO...',
                  'J....OO...', '...#######', '#.########', '#.########'],
};

test('the golden anchors match — human read and pixel sampler agree', () => {
  const byId = Object.fromEntries(BOARDS.map(b => [b.img, b.rows]));
  for (const [id, rows] of Object.entries(ANCHORS)) expect(byId[id]).toEqual(rows);
});

test('every board loads into the engine without throwing', () => {
  // A smoke test only. NOT bounded at 3: these are full setup diagrams, and some contain rows the
  // artist drew already complete (terrain), which the engine counts — the same drawing artefact the
  // C-Spin fixtures note. What is guaranteed is that every board is a shape the engine can read and
  // return a non-negative integer for, i.e. the format is compatible with forecast-boards.ts.
  for (const b of BOARDS) {
    const n = bestTspinLines(toBoard(b.rows) as any);
    expect(Number.isInteger(n)).toBe(true);
    expect(n).toBeGreaterThanOrEqual(0);
  }
});

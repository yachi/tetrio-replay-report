/**
 * POSITIVE control: generate genuine forecasts and confirm the detector fires — and that its verdict
 * matches the Dafny-proven verdict for the spec's own worked examples.
 *
 * Every other forecast test here is a NEGATIVE control (corpus and external examples that are
 * self-builds/reactive, correctly not counted). None answered "does the detector fire on a REAL
 * forecast at all?" — leaving open the worry that the corpus 0 is a broken, always-rejecting
 * detector. This closes it: the four spec examples with no garbage step are lifted into SimResults
 * and run through the real `forecastMetric`, and its verdict is checked against the verdict the Dafny
 * spec proves (spec/ForecastExamples.dfy, mirrored in forecast-examples.json):
 *
 *   A (accept)       — J overhang over a pre-existing hole, a vertical I clears the 3 rows between
 *                      (non-spin), T tucks for a Double. MUST verify (forecast_lineclear, separation 2).
 *   B (accept-loose) — same shape, one row taken by a Single. The simulator uses the any-clear
 *                      reading (`improved`), so it MUST verify too.
 *   F (reject)       — the T is dropped FLAT, never spun. MUST NOT verify (a non-spin is no forecast).
 *   G (reject)       — the slot was already complete when the roof landed; roof and tuck are adjacent
 *                      (separation 1). MUST NOT verify.
 *
 * `localiseMechanism` asserts every lifted step is boards[t-1]+cells-cleared, so a bad lift throws
 * rather than faking a verdict. This gives the repo's three representations — the ledger data, the
 * Dafny proof, and the simulator detector — one place where they are shown to agree on live boards.
 * (C, D, E need a garbage-insertion step and are covered by the Dafny proofs + wiki-fixtures, not
 * here.)
 */
import { test, expect } from 'bun:test';
import { forecastMetric, isVerifiedForecast } from './forecast.ts';
import { emptyBoard, H } from './sim.ts';
import type { PieceType } from './vendor/core/types.ts';

const W = 10;
type Cell = PieceType | 'G' | null;
const place = (rows: string[]): Cell[][] => {
  const b = emptyBoard().map(r => [...r]) as any[][];
  const off = H - rows.length;
  rows.forEach((l, i) => [...l].forEach((ch, c) => { if (ch !== '.') b[off + i]![c] = (ch === 'X' ? 'I' : ch); }));
  return b as Cell[][];
};
const filled = (c: Cell) => c !== null;

type Step = { panel: string[]; piece: PieceType; spin: 'none' | 'full' };

// Lift an example: an initial board owned by synthetic lock 0, then a placement per step. Added cells
// = whatever is filled in the (bottom-aligned) panel but empty on the live board — so it works across
// the shrink after a clear without tracking glyphs.
function lift(init: string[], steps: Step[]) {
  const board: Cell[][] = place(init);
  const prov: (number | null)[][] = board.map(r => r.map(c => (filled(c) ? 0 : null)));
  const boards: Cell[][][] = [board.map(r => [...r])];
  const provSnaps: (number | null)[][][] = [prov.map(r => [...r])];
  const locks: any[] = [{ frame: 0, piece: 'I', cells: [], cleared: 0, spin: 'none', allclear: false }];
  steps.forEach((s, si) => {
    const idx = si + 1;
    const q = place(s.panel);
    const cells: { col: number; row: number }[] = [];
    for (let r = 0; r < H; r++) for (let c = 0; c < W; c++)
      if (filled(q[r]![c]) && !filled(board[r]![c])) cells.push({ col: c, row: r });
    for (const cell of cells) { board[cell.row]![cell.col] = s.piece; prov[cell.row]![cell.col] = idx; }
    const full: number[] = [];
    for (let r = 0; r < H; r++) if (board[r]!.every(filled)) full.push(r);
    for (const r of full) {
      board.splice(r, 1); board.unshift(new Array(W).fill(null));
      prov.splice(r, 1); prov.unshift(new Array(W).fill(null));
    }
    locks.push({ frame: idx * 100, piece: s.piece, cells, cleared: full.length, spin: s.spin, allclear: false });
    boards.push(board.map(r => [...r])); provSnaps.push(prov.map(r => [...r]));
  });
  return { lines: 0, placed: 0, holds: 0, clears: {}, garbage: { sent: 0, received: 0, cleared: 0, attack: 0 },
    topbtb: 0, topcombo: 0, boards, records: [], events: [], locks, garbageEvents: [], provSnaps, topout: false } as any;
}

// --- Example A: the canonical forecast (spec/example-boards.ts, Dafny-proven) ---------------------
const A = lift(
  ['..........', 'XX....XXX.', 'XX.XXXXXX.', 'XXXXXXXXX.', 'XXXXXXXXX.', 'XXXX.XXXXX', '.XXXXXXXXX'],
  [{ panel: ['..JJ......', 'XXJ...XXX.', 'XXJXXXXXX.', 'XXXXXXXXX.', 'XXXXXXXXX.', 'XXXX.XXXXX', '.XXXXXXXXX'], piece: 'J', spin: 'none' },
   { panel: ['..JJ......', 'XXJ...XXXI', 'XXJXXXXXXI', 'XXXXXXXXXI', 'XXXXXXXXXI', 'XXXX.XXXXX', '.XXXXXXXXX'], piece: 'I', spin: 'none' },
   { panel: ['..JJ......', 'XXJTTTXXXI', 'XXXXTXXXXX', '.XXXXXXXXX'], piece: 'T', spin: 'full' }]);

// --- Example B: same shape, one row by a Single (accept under the loose/any-clear reading) --------
const B = lift(
  ['..........', 'XXX...XX..', 'XXXXXXXX..', 'XXXX.XXXXX', '.XXXXXXXXX'],
  [{ panel: ['...L......', '.LLL......', 'XXX...XX..', 'XXXXXXXX..', 'XXXX.XXXXX', '.XXXXXXXXX'], piece: 'L', spin: 'none' },
   { panel: ['...L......', '.LLL......', 'XXX...XXOO', 'XXXXXXXXOO', 'XXXX.XXXXX', '.XXXXXXXXX'], piece: 'O', spin: 'none' },
   { panel: ['...L......', '.LLL......', 'XXXTTTXXOO', 'XXXXTXXXXX', '.XXXXXXXXX'], piece: 'T', spin: 'full' }]);

// --- Example F (reject): the perfect setup, but the T is dropped FLAT, never spun ----------------
const F = lift(
  ['..........', 'XXX...XXX.', 'XXXXXXXXX.', 'XXXXXXXXX.', 'XXXXXXXXX.', 'XXXX.XXXXX', '.XXXXXXXXX'],
  [{ panel: ['.ZZ.......', '..ZZ......', 'XXX...XXX.', 'XXXXXXXXX.', 'XXXXXXXXX.', 'XXXXXXXXX.', 'XXXX.XXXXX', '.XXXXXXXXX'], piece: 'Z', spin: 'none' },
   { panel: ['.ZZ.......', '..ZZ......', 'XXX...XXXI', 'XXXXXXXXXI', 'XXXXXXXXXI', 'XXXXXXXXXI', 'XXXX.XXXXX', '.XXXXXXXXX'], piece: 'I', spin: 'none' },
   { panel: ['.ZZ....T..', '..ZZ..TTT.', 'XXX...XXXI', 'XXXX.XXXXX', '.XXXXXXXXX'], piece: 'T', spin: 'none' }]);

// --- Example G (reject): the slot was already complete when the roof landed (separation 1) --------
const G = lift(
  ['..........', 'XXX...XXXX', 'XXXX.XXXXX', '.XXXXXXXXX'],
  [{ panel: ['IIII......', 'XXX...XXXX', 'XXXX.XXXXX', '.XXXXXXXXX'], piece: 'I', spin: 'none' },
   { panel: ['IIII......', 'XXXTTTXXXX', 'XXXXTXXXXX', '.XXXXXXXXX'], piece: 'T', spin: 'full' }]);

test('the lifts are valid — the step model never throws (so the verdicts are real)', () => {
  for (const r of [A, B, F, G]) expect(() => forecastMetric(r, true)).not.toThrow();
});

test('Example A: the detector DETECTS the generated forecast (positive control)', () => {
  const out = forecastMetric(A, true);
  const t = out.records.find((r: any) => r.spin === 'full')!;
  expect(t.kind).toBe('forecast_lineclear');
  expect(t.separation).toBe(2);
  expect(t.mechanism).toBe('line-clear');
  expect(t.floorOrigin).toBe('pre-existed');
  expect(t.closingClearWasSpin).toBe(false);
  expect(out.records.filter(isVerifiedForecast).length).toBe(1);   // it FIRES
});

test('Example B: a single-line forecast also verifies (the any-clear reading)', () => {
  const out = forecastMetric(B, true);
  expect(out.records.filter(isVerifiedForecast).length).toBe(1);
});

test('Examples F and G: the near-misses are correctly REJECTED (negative controls)', () => {
  expect(forecastMetric(F, true).records.filter(isVerifiedForecast).length).toBe(0);  // T never spun
  expect(forecastMetric(G, true).records.filter(isVerifiedForecast).length).toBe(0);  // slot pre-complete, sep 1
});

test('the simulator detector agrees with the Dafny-proven verdicts', () => {
  const verdict = (r: any) => forecastMetric(r, true).records.filter(isVerifiedForecast).length > 0;
  // A, B are forecasts in the spec (accept / accept-loose); F, G are rejections.
  expect({ A: verdict(A), B: verdict(B), F: verdict(F), G: verdict(G) })
    .toEqual({ A: true, B: true, F: false, G: false });
});

/**
 * Scaled positive/negative control: GENERATE 100 randomized forecast examples and run the real
 * detector on every one, checking its verdict against each example's known label.
 *
 * generated-forecast.test.ts proves the detector fires on the four spec examples. This fuzzes that
 * at scale: from four base shapes — A, B (genuine forecasts) and F, G (near-misses) — it draws 100
 * examples under a SEEDED PRNG (reproducible), each with a random horizontal MIRROR and a random
 * OVERHANG piece, lifts it into a SimResult, and runs `forecastMetric`. A genuine forecast must
 * verify; a near-miss must not. `localiseMechanism`'s step assertions guard every lift, so a bad
 * reconstruction throws rather than faking a verdict.
 *
 * The mirror axis matters: it proves the detector handles a T-spin of either handedness, not just
 * the drawn orientation. The overhang piece is cosmetic to detection (the roof is read as a filled
 * cell with a lock index, never by shape), so varying it is a robustness check, not a new case.
 *
 * Result: 100/100 classified correctly — every genuine forecast detected, every near-miss rejected.
 * The corpus 0 is a true negative at scale: give the detector a forecast and it fires, every time.
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
  rows.forEach((l, i) => [...l].forEach((ch, c) => { if (ch !== '.') b[off + i]![c] = (ch === 'X' ? 'I' : ch as any); }));
  return b as Cell[][];
};
const filled = (c: Cell) => c !== null;
type Step = { panel: string[]; piece: PieceType; spin: 'none' | 'full' };

function lift(init: string[], steps: Step[]) {
  const board = place(init);
  const prov: (number | null)[][] = board.map(r => r.map(c => (filled(c) ? 0 : null)));
  const boards = [board.map(r => [...r])];
  const provSnaps = [prov.map(r => [...r])];
  const locks: any[] = [{ frame: 0, piece: 'I', cells: [], cleared: 0, spin: 'none', allclear: false }];
  steps.forEach((s, si) => {
    const idx = si + 1, q = place(s.panel), cells: { col: number; row: number }[] = [];
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

// base shapes from spec/example-boards.ts: A,B genuine forecasts; F,G near-misses.
const BASES: Record<string, { init: string[]; steps: { panel: string[]; spin: 'none' | 'full' }[]; forecast: boolean }> = {
  A: { forecast: true, init: ['..........', 'XX....XXX.', 'XX.XXXXXX.', 'XXXXXXXXX.', 'XXXXXXXXX.', 'XXXX.XXXXX', '.XXXXXXXXX'],
    steps: [{ panel: ['..JJ......', 'XXJ...XXX.', 'XXJXXXXXX.', 'XXXXXXXXX.', 'XXXXXXXXX.', 'XXXX.XXXXX', '.XXXXXXXXX'], spin: 'none' },
            { panel: ['..JJ......', 'XXJ...XXXI', 'XXJXXXXXXI', 'XXXXXXXXXI', 'XXXXXXXXXI', 'XXXX.XXXXX', '.XXXXXXXXX'], spin: 'none' },
            { panel: ['..JJ......', 'XXJTTTXXXI', 'XXXXTXXXXX', '.XXXXXXXXX'], spin: 'full' }] },
  B: { forecast: true, init: ['..........', 'XXX...XX..', 'XXXXXXXX..', 'XXXX.XXXXX', '.XXXXXXXXX'],
    steps: [{ panel: ['...L......', '.LLL......', 'XXX...XX..', 'XXXXXXXX..', 'XXXX.XXXXX', '.XXXXXXXXX'], spin: 'none' },
            { panel: ['...L......', '.LLL......', 'XXX...XXOO', 'XXXXXXXXOO', 'XXXX.XXXXX', '.XXXXXXXXX'], spin: 'none' },
            { panel: ['...L......', '.LLL......', 'XXXTTTXXOO', 'XXXXTXXXXX', '.XXXXXXXXX'], spin: 'full' }] },
  F: { forecast: false, init: ['..........', 'XXX...XXX.', 'XXXXXXXXX.', 'XXXXXXXXX.', 'XXXXXXXXX.', 'XXXX.XXXXX', '.XXXXXXXXX'],
    steps: [{ panel: ['.ZZ.......', '..ZZ......', 'XXX...XXX.', 'XXXXXXXXX.', 'XXXXXXXXX.', 'XXXXXXXXX.', 'XXXX.XXXXX', '.XXXXXXXXX'], spin: 'none' },
            { panel: ['.ZZ.......', '..ZZ......', 'XXX...XXXI', 'XXXXXXXXXI', 'XXXXXXXXXI', 'XXXXXXXXXI', 'XXXX.XXXXX', '.XXXXXXXXX'], spin: 'none' },
            { panel: ['.ZZ....T..', '..ZZ..TTT.', 'XXX...XXXI', 'XXXX.XXXXX', '.XXXXXXXXX'], spin: 'none' }] },
  G: { forecast: false, init: ['..........', 'XXX...XXXX', 'XXXX.XXXXX', '.XXXXXXXXX'],
    steps: [{ panel: ['IIII......', 'XXX...XXXX', 'XXXX.XXXXX', '.XXXXXXXXX'], spin: 'none' },
            { panel: ['IIII......', 'XXXTTTXXXX', 'XXXXTXXXXX', '.XXXXXXXXX'], spin: 'full' }] },
};

const mirror = (rows: string[]) => rows.map(r => [...r].reverse().join(''));
const PIECES: PieceType[] = ['J', 'L', 'S', 'Z', 'I', 'O', 'T'];
// seeded PRNG — deterministic and reproducible (Date.now/Math.random are not used)
function mulberry32(a: number) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

test('100 generated forecast examples: the detector classifies every one correctly', () => {
  const rnd = mulberry32(12345);
  const pick = <T,>(arr: T[]) => arr[Math.floor(rnd() * arr.length)]!;
  const N = 100;
  let correct = 0, genuineTot = 0, genuineDet = 0, nearMissFired = 0;
  const wrong: string[] = [];

  for (let i = 0; i < N; i++) {
    const key = pick(['A', 'A', 'A', 'B', 'B', 'B', 'F', 'G']);  // weighted toward genuine
    const base = BASES[key]!;
    const flip = rnd() < 0.5;
    const roof = pick(PIECES.filter(p => p !== 'T'));            // random overhang piece
    const tx = (rows: string[]) => flip ? mirror(rows) : rows;
    const steps: Step[] = base.steps.map((s, si) => ({
      panel: tx(s.panel), piece: si === 0 ? roof : si === base.steps.length - 1 ? 'T' : pick(PIECES), spin: s.spin }));

    let verified = 0, threw = false;
    try { verified = forecastMetric(lift(tx(base.init), steps), true).records.filter(isVerifiedForecast).length; }
    catch { threw = true; }
    const got = verified > 0;
    if (base.forecast) { genuineTot++; if (got) genuineDet++; } else if (got) nearMissFired++;
    if (!threw && got === base.forecast) correct++;
    else wrong.push(`#${i} ${key}${flip ? 'm' : ''} roof=${roof} expect=${base.forecast} got=${got}${threw ? ' THREW' : ''}`);
  }

  expect(wrong).toEqual([]);            // every example classified correctly
  expect(correct).toBe(N);
  expect(genuineTot).toBeGreaterThan(50);   // the draw actually produced genuine forecasts...
  expect(genuineDet).toBe(genuineTot);      // ...and the detector fired on ALL of them
  expect(nearMissFired).toBe(0);            // and on none of the near-misses
});

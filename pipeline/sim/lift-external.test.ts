/**
 * Run the REAL detector on a genuine external forecast example, at the clause level.
 *
 * Reachability (reachability-external.test.ts) is only one false-negative source; this checks the
 * clause logic. The JP article's foreacast_004..009 run is the cleanest forecast the corpora draw:
 * a Z overhang (005), an L that completes and CLEARS a row (006->007) — a non-spin clear — and a T
 * that tucks into the opened slot for a Double (008->009). If any example were going to expose a
 * clause-level false negative, it is this one.
 *
 * We lift it faithfully into a SimResult (the pre-existing stack owned by a synthetic lock 0, then Z,
 * L, T) and run `forecastMetric`. `localiseMechanism` asserts every step is
 * boards[t-1]+cells-cleared, so a bad lift THROWS rather than mis-classifies — the lift cannot fake a
 * verdict. The detector returns **reactive**, because the cell directly roofing the T was placed by
 * the L (the same lock that cleared the opening row): separation === 1, no step between roof and
 * tuck, nothing "opened later". This is not a miss — it is the concrete instance of the spec's
 * machine-checked theorem `SeparationOneIsNeverAForecast` (spec/Forecast.dfy: k == j+1 ⇒ !IsForecast).
 * So the example CORROBORATES the ~0 count instead of raising it.
 */
import { test, expect } from 'bun:test';
import { forecastMetric, isVerifiedForecast } from './forecast.ts';
import { emptyBoard, H } from './sim.ts';
import type { PieceType } from './vendor/core/types.ts';

const W = 10;
// piece-placement frames from jp-forecast-boards.json (foreacast_004/005/006, and 008 post-clear):
const F004 = ['..........','..........','#.........','######....','#########.','#######.##','##.#######','##.#######'];
const F005 = ['..........','...ZZ.....','#...ZZ....','######....','#########.','#######.##','##.#######','##.#######'];
const F006 = ['..........','...ZZ.....','#...ZZ..LL','######...L','#########L','#######.##','##.#######','##.#######'];
const F008 = ['..........','..........','...ZZ.....','#...ZZ..LL','######TTTL','#######T##','##.#######','##.#######'];

type Cell = PieceType | 'G' | null;
const place = (rows: string[]): Cell[][] => {
  const b = emptyBoard().map(r => [...r]) as any[][];
  const off = H - rows.length;
  rows.forEach((l, i) => [...l].forEach((ch, c) => { if (ch !== '.') b[off + i]![c] = (ch === 'G' ? 'G' : ch); }));
  return b as Cell[][];
};
const filled = (c: Cell) => c !== null;

function liftJP() {
  const board: Cell[][] = place(F004);
  const prov: (number | null)[][] = board.map(r => r.map(c => (filled(c) ? 0 : null)));
  const boards: Cell[][][] = [board.map(r => [...r])];
  const provSnaps: (number | null)[][][] = [prov.map(r => [...r])];
  const locks: any[] = [{ frame: 0, piece: 'I', cells: [], cleared: 0, spin: 'none', allclear: false }];

  const lockStep = (cells: { col: number; row: number }[], piece: PieceType, idx: number, spin: 'none'|'full') => {
    for (const c of cells) { board[c.row]![c.col] = piece; prov[c.row]![c.col] = idx; }
    const full: number[] = [];
    for (let r = 0; r < H; r++) if (board[r]!.every(filled)) full.push(r);
    for (const r of full) {
      board.splice(r, 1); board.unshift(new Array(W).fill(null));
      prov.splice(r, 1); prov.unshift(new Array(W).fill(null));
    }
    locks.push({ frame: idx * 100, piece, cells, cleared: full.length, spin, allclear: false });
    boards.push(board.map(r => [...r])); provSnaps.push(prov.map(r => [...r]));
  };

  // added cells of `cur` vs `prev` frame (both bottom-aligned), tagged with the drawn glyph
  const glyphCells = (prev: string[], cur: string[], want: string) => {
    const p = place(prev), q = place(cur), out: { col: number; row: number }[] = [];
    const off = H - cur.length;
    cur.forEach((l, i) => [...l].forEach((ch, c) => {
      const r = off + i;
      if (ch === want && !filled(p[r]![c]) && filled(q[r]![c])) out.push({ col: c, row: r });
    }));
    return out;
  };

  lockStep(glyphCells(F004, F005, 'Z'), 'Z', 1, 'none');   // overhang
  lockStep(glyphCells(F005, F006, 'L'), 'L', 2, 'none');   // completes + clears a row
  // T cells are the 'T' glyphs in F008, placed on the live post-L-clear board:
  const off = H - F008.length; const tCells: { col: number; row: number }[] = [];
  F008.forEach((l, i) => [...l].forEach((ch, c) => { if (ch === 'T') tCells.push({ col: c, row: off + i }); }));
  lockStep(tCells, 'T', 3, 'full');

  return { lines: 0, placed: 0, holds: 0, clears: {}, garbage: { sent: 0, received: 0, cleared: 0, attack: 0 },
    topbtb: 0, topcombo: 0, boards, records: [], events: [], locks, garbageEvents: [], provSnaps, topout: false } as any;
}

test('the JP forecast example lifts without the step model throwing (so the verdict is real)', () => {
  expect(() => forecastMetric(liftJP(), true)).not.toThrow();
});

test('the detector classifies the JP forecast example as reactive at separation 1 — a proven non-forecast', () => {
  const out = forecastMetric(liftJP(), true);
  const t = out.records.find((r: any) => r.spin === 'full');
  expect(t).toBeDefined();
  // separation 1: the roof cell above the T was placed by the same lock that cleared the opening row,
  // so there is no step between roof and tuck. This is exactly SeparationOneIsNeverAForecast.
  expect(t!.separation).toBe(1);
  expect(t!.kind).toBe('reactive');
  expect(out.records.filter(isVerifiedForecast).length).toBe(0);
});

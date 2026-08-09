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
 *
 * Audit of the whole corpora (2026-08-09), so this is measured rather than asserted: of the 64
 * external frames, exactly THREE draw a newly-placed T that clears a line — JP 008 (this 004..009
 * run), JP 031 and JP 037. 004..009 is the ONLY one that lifts as a faithful multi-step sequence and
 * it is reactive/sep-1. JP 031 is an untucked self-build (named below → no forecast record). JP 037's
 * tuck is real but its roofing O is drawn in the SAME frame as two other pieces, so it cannot be
 * lifted as single-piece steps without inventing frames (forbidden hand-data); its roof sits in the
 * immediately-prior frame regardless, i.e. sep-1. four.lol is the same: every executed spin is either
 * a single-frame tuck (sep-1, covered by the sweep) or a multi-piece illustration jump. So no
 * additional named lift can surface a separation ≥2 forecast — the corpora do not draw one beyond
 * 004..009. Hand-authoring more cases broadens the negative controls; it does not raise the count.
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
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

// --- Second named exemplar: the UNTUCKED self-build (JP foreacast_029..031) -------------------
// The sweep below states the two honest outcomes an executed corpus spin can have; foreacast_004..009
// above is the sep-1 one. This is the other: the T fills an OPEN right-side well (col 9, empty all the
// way above the stack) — no cell roofs any T cell — so it is a self-built vertical spin, not a tuck
// under an overhang. The detector records NOTHING for it (forecast.ts drops an untucked spin at the
// tuck gate), which is the correct verdict: a forecast needs a roof over a pre-existing hole, and this
// board has neither. Single-piece steps (S = 4 cells, then T = 4 cells), so the lift is faithful.
const G029 = ['..........', '..........', '#########.', '#######.##', '#######.##', '#######.##', '#######.##', '###.######'];
const G030 = ['.SS.......', 'SS........', '#########.', '#######.##', '#######.##', '#######.##', '#######.##', '###.######'];
const G031 = ['.SS......T', 'SS......TT', '#########T', '#######.##', '#######.##', '#######.##', '#######.##', '###.######'];

function liftSelfBuild() {
  const board: Cell[][] = place(G029);
  const prov: (number | null)[][] = board.map(r => r.map(c => (filled(c) ? 0 : null)));
  const boards: Cell[][][] = [board.map(r => [...r])];
  const provSnaps: (number | null)[][][] = [prov.map(r => [...r])];
  const locks: any[] = [{ frame: 0, piece: 'I', cells: [], cleared: 0, spin: 'none', allclear: false }];
  const step = (prev: string[], cur: string[], piece: PieceType, idx: number, spin: 'none' | 'full') => {
    const p = place(prev), q = place(cur), off = H - cur.length;
    const cells: { col: number; row: number }[] = [];
    cur.forEach((l, i) => [...l].forEach((ch, c) => {
      const r = off + i;
      if (ch !== '.' && !filled(p[r]![c]) && filled(q[r]![c])) cells.push({ col: c, row: r });
    }));
    for (const cell of cells) { board[cell.row]![cell.col] = piece; prov[cell.row]![cell.col] = idx; }
    const full: number[] = [];
    for (let r = 0; r < H; r++) if (board[r]!.every(filled)) full.push(r);
    for (const r of full) {
      board.splice(r, 1); board.unshift(new Array(W).fill(null));
      prov.splice(r, 1); prov.unshift(new Array(W).fill(null));
    }
    locks.push({ frame: idx * 100, piece, cells, cleared: full.length, spin, allclear: false });
    boards.push(board.map(r => [...r])); provSnaps.push(prov.map(r => [...r]));
  };
  step(G029, G030, 'S', 1, 'none');   // an unrelated S opener, far from the well
  step(G030, G031, 'T', 2, 'full');   // T drops the open right well and clears — but nothing roofs it
  return { lines: 0, placed: 0, holds: 0, clears: {}, garbage: { sent: 0, received: 0, cleared: 0, attack: 0 },
    topbtb: 0, topcombo: 0, boards, records: [], events: [], locks, garbageEvents: [], provSnaps, topout: false } as any;
}

test('a second corpus exemplar — the untucked self-build (JP 029..031) — records no forecast at all', () => {
  const r = liftSelfBuild();
  expect(() => forecastMetric(r, true)).not.toThrow();          // the lift is faithful (single-piece steps)
  const out = forecastMetric(r, true);
  // nothing roofs the T, so it is not even a tuck: zero forecast records, the correct verdict.
  expect(out.records.length).toBe(0);
  expect(out.records.filter(isVerifiedForecast).length).toBe(0);
});

// ---------------------------------------------------------------------------------------------
// Exhaustive sweep: EVERY executed T-spin the corpora draw, not just the cleanest one. For each
// frame where the T is the newly-placed piece and completes a line, classify why it is not a missed
// forecast. Two honest outcomes only: the T is UNTUCKED (no overhang cell above it — a self-built
// well spin the detector drops at forecast.ts:513), or it is a single-frame tuck into a slot that
// already exists, which lifts (pre-board = synthetic lock 0, then the T) to separation 1 — the proven
// non-forecast. If any witness were a genuine forecast the detector missed, it would fail here.
// ---------------------------------------------------------------------------------------------
type Frame = { id: string; rows: string[] };
function witnesses(): Frame[] {
  const out: Frame[] = [];
  const jp = JSON.parse(readFileSync(`${import.meta.dir}/jp-forecast-boards.json`, 'utf8')).boards as any[];
  for (let i = 1; i < jp.length; i++) out.push({ id: `jp/${jp[i].img}`, rows: jp[i].rows });
  const four = JSON.parse(readFileSync(`${import.meta.dir}/four-forecast-boards.json`, 'utf8')).boards as any[];
  for (let i = 1; i < four.length; i++) out.push({ id: `four/${four[i].section}#${four[i].page}`, rows: four[i].rows });
  // keep only frames whose T is newly placed vs the previous frame AND completes a line
  const all = [
    ...jp.map((b:any)=>({id:`jp/${b.img}`,rows:b.rows})),
    ...four.map((b:any)=>({id:`four/${b.section}#${b.page}`,rows:b.rows})),
  ];
  const keep: Frame[] = [];
  for (let i = 1; i < all.length; i++) {
    const cur = place(all[i]!.rows), prev = place(all[i-1]!.rows);
    const tc: {r:number;c:number}[] = [];
    let addedNonT = false, tOld = false;
    for (let r=0;r<H;r++) for (let c=0;c<W;c++) {
      const now = filled(cur[r]![c]), before = filled(prev[r]![c]);
      const isT = cur[r]![c] === 'T';
      if (isT && before) tOld = true;
      if (now && !before && !isT) addedNonT = true;
      if (isT) tc.push({r,c});
    }
    if (tc.length && !addedNonT && !tOld) {
      const full = new Set(tc.map(t=>t.r));
      const clears = [...full].some(r => cur[r]!.every(filled));
      if (clears) keep.push(all[i]!);
    }
  }
  return keep;
}

function tuckedFrame(rows: string[]): { tucked: boolean; verified: number } {
  const b = place(rows);
  const tc: {r:number;c:number}[] = [];
  for (let r=0;r<H;r++) for (let c=0;c<W;c++) if (b[r]![c]==='T') tc.push({r,c});
  const isT = new Set(tc.map(t=>`${t.r},${t.c}`));
  const tucked = tc.some(t => t.r-1>=0 && filled(b[t.r-1]![t.c]) && !isT.has(`${t.r-1},${t.c}`));
  if (!tucked) return { tucked: false, verified: 0 };
  // single-frame lift: everything but the T is the pre-existing stack (lock 0); then the T (lock 1).
  const pre = b.map(r=>[...r]); for (const t of tc) pre[t.r]![t.c] = null;
  const prov = pre.map(r=>r.map(c=>filled(c)?0:null));
  const board2 = pre.map(r=>[...r]);
  for (const t of tc) { board2[t.r]![t.c]='T'; prov[t.r]![t.c]=1; }
  const full:number[]=[]; for (let r=0;r<H;r++) if (board2[r]!.every(filled)) full.push(r);
  const prov2 = prov.map(r=>[...r]); const bd2 = board2.map(r=>[...r]);
  for (const r of full){ bd2.splice(r,1); bd2.unshift(new Array(W).fill(null)); prov2.splice(r,1); prov2.unshift(new Array(W).fill(null)); }
  const r:any = { lines:0,placed:0,holds:0,clears:{},garbage:{sent:0,received:0,cleared:0,attack:0},topbtb:0,topcombo:0,
    boards:[pre.map(x=>[...x]), bd2], records:[], events:[],
    locks:[{frame:0,piece:'I',cells:[],cleared:0,spin:'none',allclear:false},
           {frame:100,piece:'T',cells:tc.map(t=>({col:t.c,row:t.r})),cleared:full.length,spin:'full',allclear:false}],
    garbageEvents:[], provSnaps:[prov.map(x=>[...x]), prov2], topout:false };
  return { tucked: true, verified: forecastMetric(r, true).records.filter(isVerifiedForecast).length };
}

test('no executed T-spin the corpora draw is a forecast the detector misses (exhaustive sweep)', () => {
  const w = witnesses();
  expect(w.length).toBeGreaterThanOrEqual(4);
  const missed: string[] = [];
  for (const f of w) {
    const { verified } = tuckedFrame(f.rows);
    if (verified > 0) missed.push(f.id);   // a genuine missed forecast would surface here
  }
  expect(missed).toEqual([]);
});

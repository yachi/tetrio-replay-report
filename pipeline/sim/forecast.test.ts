/**
 * Unit tests for forecastMetric — hand-built cases whose answer is known by inspection.
 * Run: bun test forecast.test.ts
 */
import { test, expect } from 'bun:test';
import { forecastMetric, isVerifiedForecast, isForecastOrUnverified } from './forecast.ts';
import { H } from './sim.ts';
import type { SimResult } from './sim.ts';

const W = 10;
const grid = (filled: Record<string, number>): (number | null)[][] => {
  const g = Array.from({ length: H }, () => new Array<number | null>(W).fill(null));
  for (const [k, v] of Object.entries(filled)) { const [c, r] = k.split(',').map(Number); g[r!]![c!] = v; }
  return g;
};

/** Build a minimal SimResult. The T at lock `k` sits at cells; roof cell is directly above. */
/**
 * Board from ASCII rows, bottom-aligned. '.' empty, 'G' garbage, anything else a placed cell.
 * Needed because the mock used to pass `boards: []`, which made `determinable` false and sent
 * every case down the LOOSE branch — so the strict rule that production actually runs had no
 * unit coverage at all, and the counterfactual could never fire.
 */
export const boardFrom = (rows: string[]): any[][] => {
  const b = Array.from({ length: H }, () => new Array<any>(W).fill(null));
  const off = H - rows.length;
  rows.forEach((line, i) => [...line].forEach((ch, c) => {
    if (ch !== '.') b[off + i]![c] = ch === 'G' ? 'G' : 'I';
  }));
  return b;
};

function mk(opts: {
  tLock: number; tCells: { col: number; row: number }[]; roofOwner: number | null;
  clearsAt?: number[]; garbageAt?: number[]; spin?: 'full' | 'mini' | 'none'; tCleared?: number;
  boardAtRoof?: any[][]; boardAtSpin?: any[][];
}): SimResult {
  const { tLock, tCells, roofOwner, clearsAt = [], garbageAt = [], spin = 'full', tCleared = 2,
          boardAtRoof, boardAtSpin } = opts;
  const locks: SimResult['locks'] = [];
  const provSnaps: (number | null)[][][] = [];
  for (let i = 0; i <= tLock; i++) {
    locks.push({ frame: i * 100, piece: i === tLock ? 'T' : 'L',
      cells: i === tLock ? tCells : [], cleared: clearsAt.includes(i) ? 1 : 0,
      spin: i === tLock ? spin : 'none' });
    // snapshot BEFORE the T lock (index tLock-1) carries the roof
    const filled: Record<string, number> = {};
    if (roofOwner !== null) for (const c of tCells) filled[`${c.col},${c.row - 1}`] = roofOwner;
    provSnaps.push(grid(i === tLock - 1 ? filled : {}));
  }
  locks[tLock]!.cleared = tCleared;
  return {
    lines: 0, placed: 0, holds: 0, clears: {}, topbtb: 0, topcombo: 0,
    garbage: { sent: 0, received: 0, cleared: 0, attack: 0 },
    boards: (() => { const bs: any[] = Array.from({ length: tLock + 1 }, () => undefined);
      if (boardAtRoof && roofOwner !== null) bs[roofOwner] = boardAtRoof;
      if (boardAtSpin) bs[tLock - 1] = boardAtSpin;
      return bs; })(),
    records: [], events: [], locks,
    garbageEvents: garbageAt.map(i => ({ frame: i * 100, amt: 4, lockIndex: i })),
    provSnaps, topout: false,
  } as unknown as SimResult;
}

const T_CELLS = [{ col: 4, row: 30 }, { col: 3, row: 31 }, { col: 4, row: 31 }, { col: 5, row: 31 }];

test('reactive: roof built by the immediately preceding piece, nothing in between', () => {
  const r = forecastMetric(mk({ tLock: 3, tCells: T_CELLS, roofOwner: 2 }));
  expect(r.records).toHaveLength(1);
  expect(r.records[0]!.kind).toBe('reactive');
  expect(r.records[0]!.separation).toBe(1);
});

test('forecast_lineclear: a line clear falls between roof-build and execution', () => {
  const r = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, clearsAt: [2] }));
  expect(r.records[0]!.kind).toBe('forecast_lineclear');
  expect(r.records[0]!.separation).toBe(4);
});

/* Wiki-grounded boards: harddrop's "Forecasting T-Spin Triples > Garbage" pair. The second board
 * is the first with one full row containing a single hole appended at the bottom — a literal
 * garbage line. Measured: roof offers 0, spin offers 3, and spin WITHOUT the garbage offers 0,
 * so the garbage is load-bearing. Using the article's own boards means the fixture cannot drift
 * from the definition the metric claims to implement. */
const ROOF_NO_SPIN = boardFrom([
  "..........", "..........", ".......#..", ".......##.", "........##", "#######.##", "######..##",
]);
const SPIN_VIA_GARBAGE = boardFrom([
  "..........", ".......#..", ".......##.", "........##", "#######.##", "######..##", "GGGGGGG.GG",
]);
/* Same improvement, but the extra row is the PLAYER'S OWN stack rather than garbage. Removing
 * garbage changes nothing, so this is the opener shape: self_built, not a forecast. */
const SPIN_SELF_BUILT = boardFrom([
  "..........", ".......#..", ".......##.", "........##", "#######.##", "######..##", "#######.##",
]);

test('forecast_garbage: the garbage is LOAD-BEARING — remove it and the spin is gone', () => {
  const r = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: ROOF_NO_SPIN, boardAtSpin: SPIN_VIA_GARBAGE }));
  expect(r.records[0]!.kind).toBe('forecast_garbage');
  expect(r.records[0]!.garbageLoadBearing).toBe(true);
  expect(r.records[0]!.availAtRoof).toBe(0);
  expect(r.records[0]!.availAtSpin).toBe(3);
});

test('self_built: garbage arrived but the slot does not depend on it', () => {
  // This is the C-Spin/opener case that was being counted as forecast_garbage: garbage lands in
  // the window, so the old `garbageBetween` co-occurrence test fired, but the player built the
  // slot. Removing the garbage leaves the spin untouched.
  const r = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: ROOF_NO_SPIN, boardAtSpin: SPIN_SELF_BUILT }));
  expect(r.records[0]!.kind).toBe('self_built');
  expect(r.records[0]!.garbageLoadBearing).toBe(false);
});

/* harddrop "Forecasting T-Spin Doubles > Garbage", pair 1: an already-available SINGLE that the
 * garbage line upgrades to a DOUBLE. Measured 1 -> 2, and back to 1 with the garbage removed. */
const UPGRADE_ROOF = boardFrom(["..........", "..........", "..##......", "...#######"]);
const UPGRADE_SPIN = boardFrom(["..........", "..##......", "...#######", "G.GGGGGGGG"]);

test('an already-available spin that GROWS still counts — forecasting an upgrade', () => {
  // Two of the wiki's five garbage pairs go best 1 -> 2, which the article presents as
  // forecasting a Double. The previous binary `!tspinAvailable(boardJ)` forced them all to
  // reactive; 34 of this corpus's 185 reactive events have that shape.
  const r = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: UPGRADE_ROOF, boardAtSpin: UPGRADE_SPIN }));
  expect(r.records[0]!.availAtRoof).toBe(1);
  expect(r.records[0]!.availAtSpin).toBe(2);
  expect(r.records[0]!.kind).toBe('forecast_garbage');
});

test('garbage takes precedence over a clear when it is load-bearing', () => {
  const r = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, clearsAt: [2], garbageAt: [3],
    boardAtRoof: ROOF_NO_SPIN, boardAtSpin: SPIN_VIA_GARBAGE }));
  expect(r.records[0]!.kind).toBe('forecast_garbage');
});

test('no roof (open placement) is not a tucked T-spin and is not counted', () => {
  const r = forecastMetric(mk({ tLock: 3, tCells: T_CELLS, roofOwner: null }));
  expect(r.records).toHaveLength(0);
  expect(r.tspins).toBe(0);
});

test('non-spin placement is not counted', () => {
  const r = forecastMetric(mk({ tLock: 3, tCells: T_CELLS, roofOwner: 2, spin: 'none' }));
  expect(r.records).toHaveLength(0);
});

test('spin that clears no lines is not counted', () => {
  const r = forecastMetric(mk({ tLock: 3, tCells: T_CELLS, roofOwner: 2, tCleared: 0 }));
  expect(r.records).toHaveLength(0);
});

test('garbage strictly BEFORE the roof was built does not count as forecast', () => {
  const r = forecastMetric(mk({ tLock: 5, tCells: T_CELLS, roofOwner: 3, garbageAt: [1] }));
  expect(r.records[0]!.kind).toBe('reactive');
});

test('isVerifiedForecast admits ONLY the causally-verified bucket', () => {
  // The mutation `kind !== 'reactive'` — the idiom this predicate replaced — survived the whole
  // suite until this test existed. That idiom IS the original defect: it readmits self_built
  // (openers) and the untestable line-clear bucket into the forecast numerator. A harness that
  // cannot kill a reversion to it would not have caught the bug it was written for.
  const mkRec = (kind: string) => ({ kind } as any);
  expect(isVerifiedForecast(mkRec('forecast_garbage'))).toBe(true);
  expect(isVerifiedForecast(mkRec('forecast_lineclear'))).toBe(false);
  expect(isVerifiedForecast(mkRec('self_built'))).toBe(false);
  expect(isVerifiedForecast(mkRec('reactive'))).toBe(false);
  // and the wider predicate takes the line-clear bucket but never the opener
  expect(isForecastOrUnverified(mkRec('forecast_lineclear'))).toBe(true);
  expect(isForecastOrUnverified(mkRec('self_built'))).toBe(false);
});

test('forecastRate counts VERIFIED forecasts only; the line-clear bucket is separate', () => {
  const r = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: ROOF_NO_SPIN, boardAtSpin: SPIN_VIA_GARBAGE }));
  expect(r.forecastRate).toBe(1);
  // an opener whose garbage does nothing must NOT move the headline rate
  const sb = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: ROOF_NO_SPIN, boardAtSpin: SPIN_SELF_BUILT }));
  expect(sb.forecastRate).toBe(0);
  expect(sb.unverifiedRate).toBe(0);
  const r2 = forecastMetric(mk({ tLock: 3, tCells: T_CELLS, roofOwner: 2 }));
  expect(r2.forecastRate).toBe(0);
});

test('roof spanning two pieces attributes to the LATEST builder, not the earliest', () => {
  // Roof above the T is built by two different locks: 1 (early) and 5 (late).
  // The setup piece is the one that COMPLETED the roof (5), so separation = 7-5 = 2,
  // and the clear at lock 3 happened BEFORE the roof completed -> reactive, not forecast.
  const tLock = 7;
  const locks: any[] = [];
  const provSnaps: any[] = [];
  for (let i = 0; i <= tLock; i++) {
    locks.push({ frame: i * 100, piece: i === tLock ? 'T' : 'L', cells: i === tLock ? T_CELLS : [],
      cleared: i === 3 ? 1 : (i === tLock ? 2 : 0), spin: i === tLock ? 'full' : 'none' });
    const g = Array.from({ length: H }, () => new Array<number | null>(10).fill(null));
    if (i === tLock - 1) {
      g[T_CELLS[1]!.row - 1]![T_CELLS[1]!.col] = 1;   // early builder
      g[T_CELLS[3]!.row - 1]![T_CELLS[3]!.col] = 5;   // latest builder completes the roof
    }
    provSnaps.push(g);
  }
  const r = forecastMetric({ locks, provSnaps, garbageEvents: [], records: [], boards: [],
    events: [], topout: false, lines: 0, placed: 0, holds: 0, clears: {}, topbtb: 0, topcombo: 0,
    garbage: { sent: 0, received: 0, cleared: 0, attack: 0 } } as any);
  expect(r.records).toHaveLength(1);
  expect(r.records[0]!.roofFrom).toBe(5);
  expect(r.records[0]!.separation).toBe(2);
  expect(r.records[0]!.kind).toBe('reactive');
});

/** Real boards, from the shapes splice-demo.ts verified against the engine. */
import { emptyBoard, tspinAvailable } from './forecast-boards.ts';

/** `boardAtSpin` defaults to AFTER: the board the T actually lands into. It used to be
 *  `emptyBoard()`, which offers no spin at all — so once the rule compares roof against
 *  EXECUTION rather than testing the roof alone, every case here read as "no improvement". */
function mkBoards(boardAtJ: any, boardAtSpin?: any) {
  const tLock = 4, j = 1, roofCol = T_CELLS[1]!.col;
  const locks: any[] = [], provSnaps: any[] = [], boards: any[] = [];
  for (let i = 0; i <= tLock; i++) {
    locks.push({ frame: i * 100, piece: i === tLock ? 'T' : 'L', cells: i === tLock ? T_CELLS : [],
      cleared: i === 2 ? 1 : (i === tLock ? 2 : 0), spin: i === tLock ? 'full' : 'none' });
    const g = Array.from({ length: H }, () => new Array<number | null>(10).fill(null));
    if (i === tLock - 1) g[T_CELLS[1]!.row - 1]![roofCol] = j;
    provSnaps.push(g);
    boards.push(i === j ? boardAtJ : (i === tLock - 1 ? (boardAtSpin ?? AFTER) : emptyBoard()));
  }
  return { locks, provSnaps, boards, garbageEvents: [], records: [], events: [], topout: false,
    lines: 0, placed: 0, holds: 0, clears: {}, topbtb: 0, topcombo: 0,
    garbage: { sent: 0, received: 0, cleared: 0, attack: 0 } } as any;
}
const mk3 = (rows: Record<number, number[]>) => {
  const b = emptyBoard().map(r => [...r]) as any[][];
  for (const [r, empt] of Object.entries(rows))
    for (let c = 0; c < 10; c++) if (!empt.includes(c)) b[+r]![c] = 'I';
  return b;
};
// verified in splice-demo.ts: BEFORE offers no T-spin, AFTER offers a clean TSD
const BEFORE = mk3({ 36: [4, 5], 37: [], 38: [3, 4, 5], 39: [4] });
const AFTER  = mk3({ 37: [4, 5], 38: [3, 4, 5], 39: [4] });

test('fixture sanity: the engine agrees BEFORE has no T-spin and AFTER does', () => {
  expect(tspinAvailable(BEFORE as any)).toBe(false);
  expect(tspinAvailable(AFTER as any)).toBe(true);
});

test('STRICT: no T-spin was available when the roof was placed -> forecast', () => {
  const r = forecastMetric(mkBoards(BEFORE));
  expect(r.records[0]!.determinable).toBe(true);
  expect(r.records[0]!.slotOpenedLater).toBe(true);
  expect(r.records[0]!.kind).toBe('forecast_lineclear');
});

test('STRICT: a T-spin was already available -> reactive, despite a clear in between', () => {
  const r = forecastMetric(mkBoards(AFTER));
  expect(r.records[0]!.slotOpenedLater).toBe(false);
  expect(r.records[0]!.kind).toBe('reactive');   // the loose rule would have said forecast
});

test('STRICT can be disabled, restoring the loose rule', () => {
  expect(forecastMetric(mkBoards(AFTER), false).records[0]!.kind).toBe('forecast_lineclear');
});

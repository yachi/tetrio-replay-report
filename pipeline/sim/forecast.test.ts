/**
 * Unit tests for forecastMetric — hand-built cases whose answer is known by inspection.
 * Run: bun test forecast.test.ts
 */
import { test, expect } from 'bun:test';
import { forecastMetric, isVerifiedForecast, floorOrigin, isForecastOrUnverified } from './forecast.ts';
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
  /** which lock changes the board, and the cells it placed */
  changeAt?: number; stepCells?: { col: number; row: number }[];
}): SimResult {
  const { tLock, tCells, roofOwner, clearsAt = [], garbageAt = [], spin = 'full', tCleared = 2,
          boardAtRoof, boardAtSpin, changeAt, stepCells } = opts;
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
    // Every board in the window must exist and must be reachable from its predecessor by the
    // step that separates them, because localiseMechanism walks the window and asserts its own
    // reconstruction. The old version left holes (`undefined`) either side of two named indices,
    // which was invisible while the rule only ever read those two.
    boards: (() => { const bs: any[] = Array.from({ length: tLock + 1 }, () => undefined);
      if (boardAtRoof && roofOwner !== null) {
        const change = changeAt ?? garbageAt[0] ?? clearsAt[0] ?? tLock - 1;
        for (let i = 0; i <= tLock; i++) bs[i] = i < change ? boardAtRoof : (boardAtSpin ?? boardAtRoof);
        // The piece type has to match what the fixture boards are filled with ('I'), because the
        // reconstruction compares cell CONTENT, not just occupancy — it caught this fixture
        // claiming an L placed cells that the board records as an I.
        if (stepCells) { locks[change]!.cells = stepCells; locks[change]!.piece = 'I'; }
      }
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
/* The opener shape: the same 0 -> 2 improvement, produced by the player's OWN placement. An L
 * lands on the col-2 stack and overhangs col 3, roofing a notch that was already there — which is
 * how a C-Spin builds its overhang, and what the old co-occurrence rule scored as a forecast
 * merely because garbage happened to arrive during the window. Stated as a placement rather than
 * as an appended row, because a board that changes with no piece to account for it is not a state
 * the game can reach — and `localiseMechanism` now says so instead of classifying it. */
const SB_ROOF = boardFrom(["..........", "..........", "###...####", "####.#####"]);
const SB_CELLS = [{ col: 2, row: 35 }, { col: 2, row: 36 }, { col: 2, row: 37 }, { col: 3, row: 37 }];
const SB_SPIN = boardFrom(["..#.......", "..#.......", "..##......", "###...####", "####.#####"]);

test('forecast_garbage: the garbage is LOAD-BEARING — remove it and the spin is gone', () => {
  const r = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: ROOF_NO_SPIN, boardAtSpin: SPIN_VIA_GARBAGE }));
  expect(r.records[0]!.kind).toBe('forecast_garbage');
  expect(r.records[0]!.garbageLoadBearing).toBe(true);
  expect(r.records[0]!.availAtRoof).toBe(0);
  expect(r.records[0]!.availAtSpin).toBe(3);
});

test('self_built: garbage arrived but the PLACEMENT is what raised the spin', () => {
  // The C-Spin/opener case that was being counted as forecast_garbage: garbage lands in the
  // window, so the old `garbageBetween` co-occurrence test fired, but the availability crossed
  // on the player's own piece.
  const r = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: SB_ROOF, boardAtSpin: SB_SPIN, changeAt: 2, stepCells: SB_CELLS }));
  expect(r.records[0]!.availAtRoof).toBe(0);
  expect(r.records[0]!.availAtSpin).toBe(2);
  expect(r.records[0]!.mechanism).toBe('placement');
  expect(r.records[0]!.kind).toBe('self_built');
  expect(r.records[0]!.garbageLoadBearing).toBe(false);
});

/* harddrop "Forecasting T-Spin Doubles > Garbage", pair 1: an already-available SINGLE that the
 * garbage line upgrades to a DOUBLE. Measured 1 -> 2, and back to 1 with the garbage removed. */
const UPGRADE_ROOF = boardFrom(["..........", "..........", "..##......", "...#######"]);
const UPGRADE_SPIN = boardFrom(["..........", "..##......", "...#######", "G.GGGGGGGG"]);

/* A clear that DISPLACES the slot instead of forming it. The J both roofs the notch and completes
 * a row well above it, so the availability crosses on this step and a line does clear — but the
 * cleared row lies outside the slot's own rows, so removing it only moved the slot down bodily.
 * Without the straddle rule this is indistinguishable from the real mechanism, and it is the
 * shape 85 of the corpus's 86 line-clear-labelled events turned out to have. */
const DISP_ROOF = boardFrom(["##.#######", "..........", "..........", "###...####", "####.#####"]);
const DISP_CELLS = [{ col: 2, row: 35 }, { col: 2, row: 36 }, { col: 2, row: 37 }, { col: 3, row: 37 }];
const DISP_SPIN = boardFrom(["..........", "..#.......", "..##......", "###...####", "####.#####"]);

test('a clear that DISPLACES the slot is the placement, not a forecast', () => {
  const r = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, clearsAt: [2],
    boardAtRoof: DISP_ROOF, boardAtSpin: DISP_SPIN, changeAt: 2, stepCells: DISP_CELLS }));
  expect(r.records[0]!.availAtRoof).toBe(0);
  expect(r.records[0]!.availAtSpin).toBe(2);
  // a line DID clear in the window, and the old rule would have scored this a forecast on
  // exactly that fact. The row it removed was nowhere near the slot.
  expect(r.records[0]!.mechanism).toBe('placement');
  expect(r.records[0]!.kind).toBe('self_built');
});

/* Neither mechanism: the slot is already built and merely UNREACHABLE, sealed under a row that is
 * full but for one column. The I completes that row from four rows up, the clear opens the path,
 * and the T walks in. The clear did not form the slot and the piece never went near it, so the
 * answer is `unattributed` — recorded rather than guessed. This never occurs in the corpus, which
 * is why it is here: an untested branch is where a silent default would live. */
const ACC_ROOF = boardFrom(["#########.", "..........", "..##......", "###...####", "####.#####"]);
const ACC_CELLS = [35, 34, 33, 32].map(row => ({ col: 9, row }));
// the I's other three cells survive the clear and ride down with the rest of the stack
const ACC_SPIN = boardFrom([".........#", ".........#", ".........#", "..........",
                            "..##......", "###...####", "####.#####"]);

test('a clear that only opens ACCESS is attributed to neither, and says so', () => {
  const r = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, clearsAt: [2],
    boardAtRoof: ACC_ROOF, boardAtSpin: ACC_SPIN, changeAt: 2, stepCells: ACC_CELLS }));
  expect(r.records[0]!.availAtSpin).toBe(2);
  expect(r.records[0]!.mechanism).toBe('unattributed');
  // it must NOT be counted as a forecast on the strength of a mechanism nobody established
  expect(r.records[0]!.kind).toBe('self_built');
  expect(r.forecastRate).toBe(0);
  expect(r.unattributed).toBe(1);
});

/* Availability OVERSHOOTS and settles back: 0 -> 2 -> 3 -> 2. The step that produced what the
 * player actually executed is the one where the final level was first reached AND held (step 1),
 * not the last step where the number went up (step 2, which reached a 3 that was gone by
 * execution). The distinction is invisible on a monotone window, which is every window in the
 * fixtures above and all 654 events in the corpus — so without this it is untested rule.
 *
 * These three boards are a synthetic TRAJECTORY, not game states: the cell sets that separate
 * them were searched for by availability, and are not tetromino shapes. That is legitimate here
 * because what is under test is the walk over `boards`, which reads only the arithmetic; it would
 * not be legitimate for anything that reasons about how a piece got there. */
const OS0 = boardFrom(["######...#", "######...#", "#######.##"]);
const OS1 = boardFrom(["........#.", "........##", "######..##", "######...#", "#######.##"]);
const OS2 = boardFrom([".......#..", ".......##.", "........##", "#######.##", "######..##", "#######.##"]);
const OS1_CELLS = [{ col: 8, row: 35 }, { col: 8, row: 36 }, { col: 9, row: 36 }, { col: 8, row: 37 }];
const OS2_CELLS = [{ col: 7, row: 34 }, { col: 7, row: 35 }, { col: 6, row: 37 }, { col: 8, row: 38 }];

test('the causing step is where the level was reached and HELD, not the last rise', () => {
  const tLock = 4;
  const locks: any[] = [], provSnaps: any[] = [];
  for (let i = 0; i <= tLock; i++) {
    locks.push({ frame: i * 100, piece: i === tLock ? 'T' : 'I',
      cells: i === tLock ? T_CELLS : i === 1 ? OS1_CELLS : i === 2 ? OS2_CELLS : [],
      cleared: i === tLock ? 2 : 0, spin: i === tLock ? 'full' : 'none' });
    const g = Array.from({ length: H }, () => new Array<number | null>(10).fill(null));
    if (i === tLock - 1) for (const c of T_CELLS) g[c.row - 1]![c.col] = 0;
    provSnaps.push(g);
  }
  const r = forecastMetric({ locks, provSnaps, garbageEvents: [], records: [], events: [],
    boards: [OS0, OS1, OS2, OS1, OS1], topout: false, lines: 0, placed: 0, holds: 0, clears: {},
    topbtb: 0, topcombo: 0, garbage: { sent: 0, received: 0, cleared: 0, attack: 0 } } as any);
  expect(r.records[0]!.availAtRoof).toBe(0);
  expect(r.records[0]!.availAtSpin).toBe(2);
  // step 2 is where availability peaked; step 1 is where the executed level was established
  expect(r.records[0]!.mechanismStep).toBe(1);
});

test('a board that changed without a placement to explain it is an ERROR, not a verdict', () => {
  // The whole step model rests on boards[t] being boards[t-1] plus this lock's cells, minus the
  // rows that filled, plus any garbage. If that is ever false the decomposition is meaningless
  // and every mechanism it reports is fiction — so it must fail loudly rather than classify.
  // Both fixtures in this file broke this rule at first, in ways that looked entirely plausible.
  // the board gains cells that no lock placed
  expect(() => forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0,
    boardAtRoof: SB_ROOF, boardAtSpin: SB_SPIN, changeAt: 2 /* no stepCells: nothing placed */ })))
    .toThrow(/diverges/);
  // and the lock claims a clear the board cannot account for
  expect(() => forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, clearsAt: [2],
    boardAtRoof: SB_ROOF, boardAtSpin: SB_SPIN, changeAt: 2, stepCells: SB_CELLS })))
    .toThrow(/cleared 1 rows/);
});

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

test('isVerifiedForecast wants a mechanism AND a hole that was already there', () => {
  // The mutation `kind !== 'reactive'` — the idiom this predicate replaced — survived the whole
  // suite until this test existed. That idiom IS the original defect: it readmits self_built
  // (openers) into the forecast numerator. A harness that cannot kill a reversion to it would
  // not have caught the bug it was written for. The line-clear bucket joined the numerator on
  // 2026-08-02, when localisation gave it the same evidence the garbage branch already had —
  // which is a change in what can be PROVEN, not a relaxation of the bar. Clause 2 joined on
  // 2026-08-03: the kinds say WHICH edit closed the gap and nothing about whether there was a
  // hole to close onto, so a roof dropped on solid stack that opens up underneath used to score
  // identically to a roof laid over a cavity on purpose.
  const mkRec = (kind: string, floorOrigin = 'pre-existed') => ({ kind, floorOrigin } as any);
  expect(isVerifiedForecast(mkRec('forecast_garbage'))).toBe(true);
  expect(isVerifiedForecast(mkRec('forecast_lineclear'))).toBe(true);
  expect(isVerifiedForecast(mkRec('self_built'))).toBe(false);
  expect(isVerifiedForecast(mkRec('reactive'))).toBe(false);
  // the playfield floor predates every placement, so a nose resting on it had its hole all along
  expect(isVerifiedForecast(mkRec('forecast_lineclear', 'field-floor'))).toBe(true);
  // and the two that must not count, including the one that is merely unknown
  expect(isVerifiedForecast(mkRec('forecast_lineclear', 'arrived-later'))).toBe(false);
  expect(isVerifiedForecast(mkRec('forecast_garbage', 'undetermined'))).toBe(false);
  // a record with no verdict at all is not a pass by omission
  expect(isVerifiedForecast({ kind: 'forecast_garbage' } as any)).toBe(false);
});

test('forecastRate counts mechanism-established forecasts and nothing else', () => {
  const r = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: ROOF_NO_SPIN, boardAtSpin: SPIN_VIA_GARBAGE }));
  expect(r.forecastRate).toBe(1);
  // an opener the player built themselves must NOT move the headline rate
  const sb = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: SB_ROOF, boardAtSpin: SB_SPIN, changeAt: 2, stepCells: SB_CELLS }));
  expect(sb.forecastRate).toBe(0);
  expect(sb.unattributed).toBe(0);
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
    // The clearing piece is lock 3, and it is a REAL piece: the four cells that complete row 37.
    // It used to be lock 2 with no cells at all, against boards that jumped from the roof state
    // to `emptyBoard()` and back — a sequence no game produces, which stopped mattering the
    // moment the rule began walking the window instead of reading its two endpoints.
    locks.push({ frame: i * 100, piece: i === tLock ? 'T' : 'I',
      cells: i === tLock ? T_CELLS : i === 3 ? CLEAR_CELLS : [],
      cleared: i === 3 ? 1 : (i === tLock ? 2 : 0), spin: i === tLock ? 'full' : 'none' });
    const g = Array.from({ length: H }, () => new Array<number | null>(10).fill(null));
    if (i === tLock - 1) g[T_CELLS[1]!.row - 1]![roofCol] = j;
    provSnaps.push(g);
    boards.push(i < 3 ? boardAtJ : (boardAtSpin ?? AFTER));
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
// verified in splice-demo.ts: BEFORE offers no T-spin, AFTER offers a clean TSD.
// BEFORE holds a FULL row 37, so it is the board mid-lock — after the piece, before the rows go.
// PRE_CLEAR is the state the game is actually in beforehand, and CLEAR_CELLS is what closes it.
const BEFORE    = mk3({ 36: [4, 5], 37: [],           38: [3, 4, 5], 39: [4] });
const PRE_CLEAR = mk3({ 36: [4, 5], 37: [6, 7, 8, 9], 38: [3, 4, 5], 39: [4] });
const CLEAR_CELLS = [6, 7, 8, 9].map(col => ({ col, row: 37 }));
const AFTER  = mk3({ 37: [4, 5], 38: [3, 4, 5], 39: [4] });

test('fixture sanity: the engine agrees BEFORE has no T-spin and AFTER does', () => {
  expect(tspinAvailable(BEFORE as any)).toBe(false);
  expect(tspinAvailable(AFTER as any)).toBe(true);
  // and the state before the clearing piece offers none either — the notch is roofed over, so
  // the improvement cannot be credited to anything already present
  expect(tspinAvailable(PRE_CLEAR as any)).toBe(false);
});

test('STRICT: the clear FORMED the slot — a cleared row lay strictly inside it', () => {
  // This is the surviving mechanism, and the only one of the corpus's 86 line-clear-labelled
  // events that turned out to be real: the roof and the cavity were separated by one full row,
  // and removing it brought them together. The T is not reachable before the clear at all.
  const r = forecastMetric(mkBoards(PRE_CLEAR));
  expect(r.records[0]!.determinable).toBe(true);
  expect(r.records[0]!.slotOpenedLater).toBe(true);
  expect(r.records[0]!.mechanism).toBe('line-clear');
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

/**
 * `floorOrigin` directly, on hand-made provenance.
 *
 * Two of its comparisons cannot be reached by any board in the corpus, so the mutation harness had
 * nothing to kill them with: a piece that lays BOTH the roof and the floor under the nose, and a
 * flat T whose two lowest cells rest on cells from two different locks. Neither shape occurs in 654
 * real events, which is a fact about this corpus and not a reason to leave the comparisons untested
 * — a later session could contain either.
 */
const fakeFor = (opts: {
  noseRow: number; noseCols: number[]; provs: (number | null)[];
  garbageRowsAtRoof?: number; garbageEvents?: number[];
}) => {
  const j = 5, k = 9;
  const row = Array(10).fill(null) as (number | null)[];
  opts.noseCols.forEach((c, i) => { row[c] = opts.provs[i] ?? null; });
  const prov = Array.from({ length: H }, () => Array(10).fill(null)) as (number | null)[][];
  prov[opts.noseRow + 1] = row;
  const gRow = Array(10).fill('G');
  const boards = Array.from({ length: k }, () =>
    Array.from({ length: H }, () => Array(10).fill(null)));
  for (let i = 0; i < (opts.garbageRowsAtRoof ?? 0); i++) boards[j]![H - 1 - i] = [...gRow];
  const provSnaps: any[] = Array.from({ length: k }, () => prov);
  return { r: {
    locks: Array.from({ length: k + 1 }, (_, i) => i === k
      ? { cells: opts.noseCols.map(c => ({ col: c, row: opts.noseRow })) } : { cells: [] }),
    provSnaps, boards,
    garbageEvents: (opts.garbageEvents ?? []).map(lockIndex => ({ lockIndex, amt: 1, frame: 0 })),
  } as any, j, k };
};

test('a piece that lays the roof AND the floor under the nose still counts as pre-existing', () => {
  // At the instant that piece locks, both cells exist and so does the cavity between them, so the
  // comparison is `<= j` and not `< j`. Nothing in the corpus has this shape.
  const { r, j, k } = fakeFor({ noseRow: 10, noseCols: [4], provs: [5] });
  expect(floorOrigin(r, k, j)).toBe('pre-existed');
  const later = fakeFor({ noseRow: 10, noseCols: [4], provs: [6] });
  expect(floorOrigin(later.r, later.k, later.j)).toBe('arrived-later');
});

test('when a flat T rests on two locks, the LATER one decides', () => {
  // Taking the older of the two would call a floor pre-existing whenever any part of what the T
  // stands on happens to be old, which is the weaker question.
  const { r, j, k } = fakeFor({ noseRow: 10, noseCols: [3, 5], provs: [2, 8] });
  expect(floorOrigin(r, k, j)).toBe('arrived-later');
  const bothOld = fakeFor({ noseRow: 10, noseCols: [3, 5], provs: [2, 4] });
  expect(floorOrigin(bothOld.r, bothOld.k, bothOld.j)).toBe('pre-existed');
});

test('a garbage floor is undetermined only when garbage straddles the roof', () => {
  const noGarbageThen = fakeFor({ noseRow: 10, noseCols: [4], provs: [-1], garbageRowsAtRoof: 0 });
  expect(floorOrigin(noGarbageThen.r, noGarbageThen.k, noGarbageThen.j)).toBe('arrived-later');
  const straddles = fakeFor({ noseRow: 10, noseCols: [4], provs: [-1],
    garbageRowsAtRoof: 2, garbageEvents: [7] });
  expect(floorOrigin(straddles.r, straddles.k, straddles.j)).toBe('undetermined');
  const allBefore = fakeFor({ noseRow: 10, noseCols: [4], provs: [-1],
    garbageRowsAtRoof: 2, garbageEvents: [3] });
  expect(floorOrigin(allBefore.r, allBefore.k, allBefore.j)).toBe('pre-existed');
});

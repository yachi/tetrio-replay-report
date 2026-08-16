/**
 * Unit tests for forecastMetric — hand-built cases whose answer is known by inspection.
 * Run: bun test forecast.test.ts
 */
import { test, expect } from 'bun:test';
import { forecastMetric, isVerifiedForecast, floorOrigin, garbageArrivedAfter,
         localiseMechanism, bestTspinLines } from './forecast.ts';
import { H } from './sim.ts';
import type { SimResult } from './sim.ts';
import { tryMove, tryRotate, hardDrop, getPieceCells } from './vendor/core/srs.ts';
import type { ActivePiece } from './vendor/core/srs.ts';

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
    // ...and a floor, because a piece resting on nothing at all is not a state the game can reach.
    // This fixture used to leave the cells under the T empty and passed anyway: clause 2 read the
    // one cell under the nose, found it empty, and returned 'field-floor' — "the playfield bottom
    // predates all play" — for a T floating in mid-air at row 31. Lock 0 owns the floor so it can
    // never postdate the roof, which is what these tests are about.
    const noseRow = Math.max(...tCells.map(c => c.row));
    for (const c of tCells) if (c.row === noseRow) filled[`${c.col},${noseRow + 1}`] ??= 0;
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

test('roofIsGarbage discriminates a garbage overhang from a built one (anti-vacuity)', () => {
  // `roofIsGarbage` is 0 of 654 across all four sessions and gates no classification — it is the
  // diagnostic `run-forecast.ts` prints as "roof literally IS garbage (strongest signal)". With no
  // fixture it was 0-of-0: every "0 garbage roofs" reading would hold identically if the flag were
  // hardcoded false, never computed, or read the wrong provenance value. `roofOwner: -1` marks the
  // cells directly above the T as garbage provenance; a real placer index marks them player-built.
  // Both arms must be non-empty, exactly like the `garbageLoadBearing` families — a single instance
  // states the flag CAN be true; the pair states it DISCRIMINATES, which is what the diagnostic claims.
  const garbageRoof = forecastMetric(mk({ tLock: 3, tCells: T_CELLS, roofOwner: -1 })).records;
  const builtRoof = forecastMetric(mk({ tLock: 3, tCells: T_CELLS, roofOwner: 2 })).records;
  expect(garbageRoof).toHaveLength(1);
  expect(builtRoof).toHaveLength(1);
  expect(garbageRoof[0]!.roofIsGarbage).toBe(true);
  expect(builtRoof[0]!.roofIsGarbage).toBe(false);
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

/* ACCESS, and it is now its own mechanism: the slot is already built and merely UNREACHABLE, sealed
 * under a row that is full but for one column. The I completes that row from four rows up, the clear
 * opens the path, and the T walks in. The clear did not FORM the slot — `bestTspin` is a BFS from
 * spawn, so availability is reachability, and removing the lid raises it without building anything.
 *
 * This fixture used to assert `unattributed`/`self_built`, which was the model's answer BEFORE the
 * fifth mechanism existed: nothing here formed the slot and the piece never went near it, so it fell
 * through every branch. The corpus half of that defect — the same class landing on `placement` when
 * the causing piece happened to sit beside the slot — is in forecast-access-class.test.ts. What this
 * fixture pins now is the branch itself, on a board chosen to exercise it rather than found. */
const ACC_ROOF = boardFrom(["#########.", "..........", "..##......", "###...####", "####.#####"]);
const ACC_CELLS = [35, 34, 33, 32].map(row => ({ col: 9, row }));
// the I's other three cells survive the clear and ride down with the rest of the stack
const ACC_SPIN = boardFrom([".........#", ".........#", ".........#", "..........",
                            "..##......", "###...####", "####.#####"]);

test('a clear that only opens ACCESS is its own mechanism, and is not a forecast', () => {
  const r = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, clearsAt: [2],
    boardAtRoof: ACC_ROOF, boardAtSpin: ACC_SPIN, changeAt: 2, stepCells: ACC_CELLS }));
  expect(r.records[0]!.availAtSpin).toBe(2);
  expect(r.records[0]!.mechanism).toBe('access');
  // `path_opened`, NOT `self_built` — the piece did not build this slot, and `self_built` is what
  // the report glosses 「玩家自己落嗰隻棋整出嚟」. And NOT `forecast_lineclear` either: the cleared
  // row lies outside the slot, so `spec/Forecast.dfy`'s clause 3 (the strictly-inside rule) is
  // false for it and it may not enter the numerator.
  expect(r.records[0]!.kind).toBe('path_opened');
  expect(r.forecastRate).toBe(0);
  // and the model no longer has to say "don't know" about it — this is what the repair bought
  expect(r.unattributed).toBe(0);
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

/* The step model itself, asserted. `localiseMechanism` reconstructs Bpre = boards[t-1] + cells and
 * then compares against boards[t]; that comparison used to be skipped whenever garbage arrived
 * (`!garbageArrived &&`), i.e. on exactly the steps that can violate the model. Under
 * insertMode:'immediate' garbage goes in BEFORE the piece, and the metric returned 13 verified
 * forecasts across the four committed sessions with nothing thrown. This board is that shape in
 * miniature: a garbage row appears WITHOUT the stack being lifted, so boards[t] is not boards[t-1]
 * placed, cleared and then raised. */
const GARBAGE_WITHOUT_LIFT = boardFrom([
  "..........", "#......#..", ".......##.", "........##", "#######.##", "######..##", "GGGGGGG.GG",
]);   // SPIN_VIA_GARBAGE with one stray cell at col 0, far from the col-6..9 slot: the spin is still
      // on offer, so the window IS localised, but no lift of ROOF_NO_SPIN produces this board.

test('a garbage step that does not LIFT the stack is rejected, not classified', () => {
  expect(() => forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: ROOF_NO_SPIN, boardAtSpin: GARBAGE_WITHOUT_LIFT })))
    .toThrow(/not .* placed, cleared and then lifted/);
});

/* Kills `metric/lift-shift-unbounded`. Every arriving garbage row is 9/10 full, so a two-row insert
 * whose upper row carries no garbage is not a state the game can reach. Without the "the bottom `s`
 * rows must all be garbage" requirement the shift search accepts it at s = 2. */
const LIFT_BY_TWO_ONE_GARBAGE_ROW = boardFrom([
  ".......#..", ".......##.", "........##", "#######.##", "######..##", "#######.##", "GGGGGGG.GG",
]);   // ROOF_NO_SPIN raised by two, with only the lower inserted row carrying garbage. The upper one
      // is chosen so the board still offers a spin (0 -> 3), because a window that does not improve
      // is never localised and would exercise nothing.

test('a lift whose inserted rows are not all garbage is rejected', () => {
  expect(() => forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: ROOF_NO_SPIN, boardAtSpin: LIFT_BY_TWO_ONE_GARBAGE_ROW })))
    .toThrow(/not .* placed, cleared and then lifted/);
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
  // A 'field-floor' verdict used to sit here, counted true because the playfield bottom predates
  // every placement. It is gone: the same label was returned for a nose on row 39 AND for a nose
  // with nothing at all beneath it, and a piece held up by the floor ALONE occurs zero times in
  // 654 events across seven configs. The floor is still older than everything — it just never
  // raises the maximum provenance, so it needs no verdict of its own.
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

/* ── a SECOND two-placer roof, and this one moves the answer ─────────────────────────────────
 *
 * `Math.max(...placers)` is the whole "the roof's most recent builder is the piece that set up
 * the slot" rule, and no corpus can test it: censused over all 654 tucked T-spins, every roof is
 * exactly ONE cell, so `placers` is a singleton in every real event and `max` and `min` agree by
 * construction. Not an artefact of sample size either — a flat T needs a three-wide pocket and
 * covering a second cell seals its only entry — so more data will never separate them.
 *
 * The fixture above is the only other two-placer board here, and it decides the mutant on the
 * LOOSE branch: it passes `boards: []`, so `determinable` is false and the verdict turns on
 * whether a clear happened to fall inside the window. This one runs the strict rule production
 * runs, and every value `j` feeds moves with it:
 *
 *                       j = max = 4                    j = min = 1
 *   localisation        never runs (no improvement)    step 2, mechanism 'garbage'
 *     availAtRoof       3, i.e. availAtSpin            0
 *   separation          7 - 4 = 3                      7 - 1 = 6
 *   clause 2's base     supports compared with 4       ... compared with 1
 *   deletion set        {} — nothing arrived after 4   {39}, so the garbage reads load-bearing
 *   the ANSWER          reactive, rate 0               forecast_garbage, VERIFIED, rate 1
 *
 * The shape is a roof built AROUND the arrival: lock 1 lays one of its two cells, the garbage
 * that makes the spin lands at lock 2, and lock 4 lays the cell that completes it. Reading the
 * roof as its oldest builder therefore back-dates the window across an arrival the overhang did
 * not yet exist to be waiting for, and publishes a verified forecast for it.
 */
function twoPlacerRoof(supportProv: number): SimResult {
  const k = 7, gLock = 2;
  const locks: any[] = [], provSnaps: any[] = [], boards: any[] = [];
  for (let i = 0; i <= k; i++) {
    locks.push({ frame: i * 100, piece: i === k ? 'T' : 'L', cells: i === k ? T_CELLS : [],
      cleared: i === k ? 2 : 0, spin: i === k ? 'full' : 'none' });
    const g = Array.from({ length: H }, () => new Array<number | null>(W).fill(null));
    if (i === k - 1) {
      g[T_CELLS[1]!.row - 1]![T_CELLS[1]!.col] = 1;   // the earlier of the roof's two cells
      g[T_CELLS[3]!.row - 1]![T_CELLS[3]!.col] = 4;   // the cell that COMPLETES the roof
      // the T's floor. Its provenance is the only thing clause 2 compares against j, so varying
      // it is how the same boards exercise the comparison base as well as the window.
      for (const c of T_CELLS) if (c.row === 31) g[c.row + 1]![c.col] = supportProv;
    }
    provSnaps.push(g);
    boards.push(i < gLock ? ROOF_NO_SPIN : SPIN_VIA_GARBAGE);
  }
  return { locks, provSnaps, boards, records: [], events: [], topout: false,
    garbageEvents: [{ frame: gLock * 100, amt: 4, lockIndex: gLock }],
    lines: 0, placed: 0, holds: 0, clears: {}, topbtb: 0, topcombo: 0,
    garbage: { sent: 0, received: 0, cleared: 0, attack: 0 } } as unknown as SimResult;
}

test('a two-placer roof: the LATEST builder sets the window, and the ANSWER moves with it', () => {
  const f = twoPlacerRoof(0);
  // the fixture's own premises, so a board that quietly stopped exercising this is visible
  expect((f.provSnaps[6]![30] as (number | null)[]).filter(p => p !== null)).toEqual([1, 4]);
  expect(bestTspinLines(f.boards[1]!)).toBe(0);        // before the garbage
  expect(bestTspinLines(f.boards[6]!)).toBe(3);        // after it

  const r = forecastMetric(f);
  const rec = r.records[0]!;
  expect(rec.roofFrom).toBe(4);
  expect(rec.separation).toBe(3);                      // `min` says 6
  expect(rec.availAtRoof).toBe(3);                     // `min` says 0 ...
  expect(rec.availAtSpin).toBe(3);                     // ... against the same 3
  // the garbage landed BEFORE the roof was finished, so nothing improved after the roof and
  // there is no window to localise inside
  expect(rec.kind).toBe('reactive');
  expect(rec.mechanism).toBeUndefined();
  expect(rec.mechanismStep).toBeUndefined();
  // the deletion set is measured from j too: nothing arrived after lock 4
  expect(rec.garbageLoadBearing).toBe(false);
  // and the OUTCOME, not an intermediate: under `min` this same board is a VERIFIED
  // forecast_garbage localised to step 2, and the published rate goes 0 -> 1
  expect(isVerifiedForecast(rec)).toBe(false);
  expect(r.forecastRate).toBe(0);
  // Exhaustive over ForecastKind on purpose, so a new kind has to be acknowledged here rather than
  // appearing in a bucket nobody looks at. `path_opened` arrived that way (2026-08-16) and this was
  // the only assertion in the file it moved: the record is still `reactive` with no mechanism at
  // all (asserted above), because nothing improved after the roof, so there is no window to
  // localise inside and the `access` branch is never reached on this fixture.
  expect(r.totals).toEqual({ forecast_garbage: 0, forecast_lineclear: 0, path_opened: 0,
                             self_built: 0, reactive: 1 });
});

test('a two-placer roof also moves what clause 2 compares its supports against', () => {
  // A floor placed at lock 3: older than the roof's latest builder (4), newer than its earliest
  // (1). Nothing about the floor changed — only which lock it is being asked to predate.
  const rec = forecastMetric(twoPlacerRoof(3)).records[0]!;
  expect(rec.floorFrom).toBe(3);
  expect(rec.floorOrigin).toBe('pre-existed');   // `min` compares with 1 and says 'arrived-later'
  // and with a floor older than BOTH builders the verdict is stable, which is what makes the
  // line above a statement about the comparison base rather than about this particular floor
  expect(forecastMetric(twoPlacerRoof(0)).records[0]!.floorOrigin).toBe('pre-existed');
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
 * The clear that FORMS the slot can be of any size, and need not be a T-spin or the player's own
 * kind of clear — a Double, Triple or Tetris splices the roof onto the cavity exactly as a Single
 * does. `localiseMechanism` already handles it (`clearedRows` is however many rows were full, and
 * the inside-the-slot test maps every one of them back), but until now every fixture here cleared
 * exactly ONE row and so did the corpus's only line-clear event, so nothing said what a multi-row
 * clear does. Measured on the four sessions: 82% of the clears in the verified prefix remove two or
 * more rows, and 191 of the 654 roof->spin windows contain one, so this is not a hypothetical shape.
 *
 * Same post-clear board as the tests above — the one verified to offer a clean TSD — with `n` full
 * rows re-inserted between roof and cavity, each missing exactly the cells of the piece that lands
 * at the causing step. So the step is a real place -> clear -> snapshot, and `localiseMechanism`'s
 * own reconstruction assertion has to agree with the boards it is handed.
 */
const MULTI_ROW: Record<number, { rows: Record<number, number[]>; piece: string; cells: { col: number; row: number }[] }> = {
  1: { rows: { 37: [6, 7, 8, 9] }, piece: 'I', cells: [6, 7, 8, 9].map(col => ({ col, row: 37 })) },
  2: { rows: { 36: [8, 9], 37: [8, 9] }, piece: 'O',
       cells: [{ col: 8, row: 36 }, { col: 9, row: 36 }, { col: 8, row: 37 }, { col: 9, row: 37 }] },
  3: { rows: { 35: [8, 9], 36: [9], 37: [9] }, piece: 'L',
       cells: [{ col: 8, row: 35 }, { col: 9, row: 35 }, { col: 9, row: 36 }, { col: 9, row: 37 }] },
  4: { rows: { 34: [9], 35: [9], 36: [9], 37: [9] }, piece: 'I',
       cells: [34, 35, 36, 37].map(row => ({ col: 9, row })) },
};
const SPLICE_T = [{ col: 3, row: 38 }, { col: 4, row: 38 }, { col: 5, row: 38 }, { col: 4, row: 39 }];
const SPLICE_AFTER = mk3({ 37: [4, 5], 38: [3, 4, 5], 39: [4] });

function spliceOf(n: number) {
  const { rows, piece, cells } = MULTI_ROW[n]!;
  const pre = mk3({ [37 - n]: [4, 5], ...rows, 38: [3, 4, 5], 39: [4] });
  const j = 1, t = 4, k = 5;
  const locks: any[] = [], provSnaps: any[] = [], boards: any[] = [];
  for (let i = 0; i <= k; i++) {
    locks.push({ frame: i * 100, piece: i === k ? 'T' : i === t ? piece : 'I',
      cells: i === k ? SPLICE_T : i === t ? cells : [],
      cleared: i === k ? 2 : i === t ? n : 0, spin: i === k ? 'full' : 'none' });
    const g = Array.from({ length: H }, () => new Array<number | null>(10).fill(null));
    if (i === k - 1) { g[37]![3] = j; g[39]![3] = 0; g[39]![5] = 0; }
    provSnaps.push(g);
    boards.push(i < t ? pre : SPLICE_AFTER);
  }
  return { locks, provSnaps, boards, garbageEvents: [], records: [], events: [], topout: false,
    lines: 0, placed: 0, holds: 0, clears: {}, topbtb: 0, topcombo: 0,
    garbage: { sent: 0, received: 0, cleared: 0, attack: 0 } } as any;
}

/**
 * Clause 4 of `spec/Forecast.dfy`: the clear that closes the gap must not itself be a T-spin —
 * "1,2,3,4,5+ cleared by NOT tspin". The C-Spin is the confound: its own T-Spin Triple is what
 * lowers its own overhang, and counting that would make the opener a forecast by construction.
 *
 * This was UNENFORCED here until 2026-08-06 while the spec proved it (`CSpinIsNotAForecast`), and no
 * test could see it because the corpus's only line-clear event is closed by a vertical I. The
 * fixture below is the same board as above with one field changed.
 */
for (const n of [1, 2, 3, 4]) for (const spin of ['full', 'mini'] as const) {
  test(`STRICT: a ${n}-row clear that is ITSELF a ${spin} T-spin does not count (clause 4)`, () => {
    const f = spliceOf(n);
    // a mini is still a T-spin: "cleared by NOT tspin" does not have a size exemption, and reading
    // only `=== 'full'` here survives every other test in this file
    f.locks[4].spin = spin;
    const rec = forecastMetric(f, true).records[0]!;
    expect(rec.mechanism).toBe('line-clear');       // the gap still closed on the clear ...
    expect(rec.closingClearWasSpin).toBe(true);
    expect(isVerifiedForecast(rec)).toBe(false);    // ... and it is still not a forecast
  });
}

for (const n of [1, 2, 3, 4]) {
  test(`STRICT: a ${n}-row clear that splices roof onto cavity is a forecast`, () => {
    const f = spliceOf(n);
    expect(f.locks[4].spin).toBe('none');
    // the fixture itself, not just the verdict: no spin before, a Double after
    expect(bestTspinLines(f.boards[0])).toBe(0);
    expect(bestTspinLines(f.boards[4])).toBe(2);
    const rec = forecastMetric(f, true).records[0]!;
    expect(rec.mechanism).toBe('line-clear');
    expect(rec.kind).toBe('forecast_lineclear');
    expect(isVerifiedForecast(rec)).toBe(true);
  });
}

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

test('a piece resting on nothing is undetermined, not pre-existing', () => {
  // `provs` empty means every cell under the piece is empty. The old rule returned 'field-floor'
  // here — "the playfield bottom predates all play" — for a piece nowhere near the bottom, and
  // counted it as clause 2 TRUE. It is the branch that made 95 corpus events pass on an inspection
  // that read nothing. Only genuine floor contact may answer, and then only when it is the whole
  // support; anything else is a question the snapshots cannot settle.
  const nothing = fakeFor({ noseRow: 10, noseCols: [4], provs: [null] });
  expect(floorOrigin(nothing.r, nothing.k, nothing.j)).toBe('undetermined');
  const onTheFloor = fakeFor({ noseRow: H - 1, noseCols: [4], provs: [null] });
  expect(floorOrigin(onTheFloor.r, onTheFloor.k, onTheFloor.j)).toBe('pre-existed');
});

test('a support that postdates the roof settles it, even beside an undecidable one', () => {
  // A flat T can rest on one player cell and one garbage cell. If the player cell was placed after
  // the roof, the hole did not pre-exist the overhang and no amount of uncertainty about the
  // garbage changes that — so 'arrived-later' must win over 'undetermined'. Two corpus events have
  // this shape (07-22-3 r1 lock 21, and the published 07-28-6 r5 lock 32), but in both the garbage
  // is DECIDABLE, so neither exercises the precedence. This does.
  const both = fakeFor({ noseRow: 10, noseCols: [3, 5], provs: [8, -1],
    garbageRowsAtRoof: 2, garbageEvents: [7] });
  expect(floorOrigin(both.r, both.k, both.j)).toBe('arrived-later');
  // and with the player cell placed BEFORE the roof, the undecidable garbage does decide
  const onlyGarbageUnknown = fakeFor({ noseRow: 10, noseCols: [3, 5], provs: [2, -1],
    garbageRowsAtRoof: 2, garbageEvents: [7] });
  expect(floorOrigin(onlyGarbageUnknown.r, onlyGarbageUnknown.k, onlyGarbageUnknown.j))
    .toBe('undetermined');
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

/* ---- the counterfactual's deletion set -------------------------------------------------------
 * A garbage row with a hole at `hole`, and a board carrying `holes.length` of them stacked at the
 * bottom — oldest on top, which is the order insertion produces. */
const gRow = (hole: number) => Array.from({ length: W }, (_, c) => c === hole ? null : 'G');
const withGarbage = (holes: number[], extra: { col: number; row: number }[] = []) => {
  const b = Array.from({ length: H }, () => new Array<any>(W).fill(null));
  holes.forEach((hole, i) => { b[H - holes.length + i] = gRow(hole); });
  for (const c of extra) b[c.row]![c.col] = 'I';
  return b;
};

test('the deletion set is the garbage that arrived AFTER the roof, not every garbage row', () => {
  // One row at lock 1, two more at lock 3, roof at lock 2. Insertion pushes the stack up, so at
  // lock 3 the pre-roof row sits at 37 and the two arrivals are the BOTTOM-most rows.
  //
  // This is the whole item: stripping all three is what made `yachi 07-28-1 r5 lock 36` read as a
  // spin that depended on garbage, when the row it tucks into arrived 22 locks before its roof.
  const r = { locks: Array.from({ length: 6 }, () => ({ cells: [], piece: 'I' })),
    boards: [withGarbage([]), withGarbage([5]), withGarbage([5]),
             withGarbage([5, 5, 0]), withGarbage([5, 5, 0])],
    garbageEvents: [{ lockIndex: 1, amt: 1, frame: 0 }, { lockIndex: 3, amt: 2, frame: 0 }] } as any;
  expect(garbageArrivedAfter(r, 2, 5)).toEqual(new Set([38, 39]));
  // measured from lock 0 the same board gives all three — the answer is relative to the roof
  expect(garbageArrivedAfter(r, 0, 5)).toEqual(new Set([37, 38, 39]));
  // and a roof laid after the last arrival leaves nothing to delete
  expect(garbageArrivedAfter(r, 3, 5)).toEqual(new Set());
});

test('a clear inside the window carries the marks down with the rows', () => {
  // Same board, then the player fills the hole in the bottom row at lock 4 and clears it. Rows
  // above drop by one, so the surviving arrival is now row 39 and row 38 is the PRE-roof row that
  // used to be at 37. A walk that skipped the clear would still be marking 38 and 39 and would
  // delete the pre-roof row — the same over-deletion, one step further along.
  const r = { locks: [...Array.from({ length: 4 }, () => ({ cells: [], piece: 'I' })),
      { cells: [{ col: 0, row: H - 1 }], piece: 'I' }, { cells: [], piece: 'I' }],
    boards: [withGarbage([]), withGarbage([5]), withGarbage([5]),
             withGarbage([5, 5, 0]), withGarbage([5, 5])],
    garbageEvents: [{ lockIndex: 1, amt: 1, frame: 0 }, { lockIndex: 3, amt: 2, frame: 0 }] } as any;
  expect(garbageArrivedAfter(r, 2, 5)).toEqual(new Set([39]));
});

test('a garbage event whose rows are not on the board deletes nothing', () => {
  // `mk` below writes garbage EVENTS into fixtures whose boards carry no garbage at all, and the
  // self_built case depends on it. Marking rows the events claim without checking the board would
  // delete four rows of the player's own stack and report the placement as load-bearing garbage.
  const r = { locks: Array.from({ length: 6 }, () => ({ cells: [], piece: 'I' })),
    boards: Array.from({ length: 5 }, () => withGarbage([], [{ col: 0, row: H - 1 }])),
    garbageEvents: [{ lockIndex: 3, amt: 4, frame: 0 }] } as any;
  expect(garbageArrivedAfter(r, 2, 5)).toEqual(new Set());
});

/* ── the early return in localiseMechanism, and why it is not decoration ─────────────────────────
 *
 * `if (bestTspinLines(Bpre) >= target) return 'placement'` says: if the placement ALONE already
 * reached the target, before any row was removed, then the placement sufficed. Dropping it was
 * equivalent for all 654 corpus events and every fixture, because with no clear at the causing
 * step B IS Bpre and the next branch runs the identical test. It was carried in the mutant list as
 * a comment for that reason. This is the board that separates them.
 *
 * Three things had to hold at once, and the first two fight each other:
 *   · the step both places and clears
 *   · Bpre already reaches the target
 *   · the post-clear best slot STRADDLES the cleared row, so without the early return the whole
 *     step is attributed to the line clear
 *
 * The fight: a slot's rows go full, so nothing can descend past them — any ordinary second slot
 * placed above the low well seals it in both Bpre and B, and the low slot is never reachable. The
 * way out is that `bestTspin` counts every full row in the board it produces, including the one
 * about to be cleared. So the high spin need clear nothing of its own: a nook confined to the
 * right, worth exactly 1 in Bpre and 0 in B, which blocks no column.
 */
test('a placement that already reached the target is not credited to the clear beside it', () => {
  const row = (cells: string) => [...cells].map(c => c === '.' ? null : 'I');
  const bd = (rows: Record<number, string>) => {
    const b = Array.from({ length: H }, () => new Array<any>(W).fill(null));
    for (const [r, l] of Object.entries(rows)) b[Number(r)] = row(l);
    return b;
  };
  const A = bd({
    30: ".......##.", 31: "......#..#", 32: "......#..#", 33: "......####",  // the non-clearing nook
    36: "..##......",                                                        // low slot: overhang
    37: "######....",                                                        // the row the I completes
    38: "...#######", 39: "#.########",                                      // low slot: the T's rows
  });
  const cells = [6, 7, 8, 9].map(col => ({ col, row: 37 }));
  const B = bd({
    31: ".......##.", 32: "......#..#", 33: "......#..#", 34: "......####",
    37: "..##......", 38: "...#######", 39: "#.########",
  });
  const r = { boards: { 4: A, 5: B }, garbageEvents: [],
    locks: { 5: { cells, piece: 'I', cleared: 1 } } } as unknown as SimResult;
  const avail = (t: number) => bestTspinLines((r.boards as any)[t] ?? A);

  // the setup itself, so a fixture that quietly stopped exercising the branch is visible
  expect(bestTspinLines(A as any)).toBe(0);          // below target, so the walk stays on this step
  expect(bestTspinLines(B as any)).toBe(2);          // and the post-clear slot is worth more

  // target 1: Bpre reaches it, so the placement is credited — this is the assertion the mutant fails
  expect(localiseMechanism(r, 4, 6, 1, avail)).toEqual({ step: 5, mechanism: 'placement' });
  // target 2: Bpre does NOT reach it, the early return is skipped, and the same board is a
  // line-clear. The two branches genuinely disagree here, which is what "not equivalent" means.
  expect(localiseMechanism(r, 4, 6, 2, avail)).toEqual({ step: 5, mechanism: 'line-clear' });
});

/* ── the EXECUTED spin has never been a mini ─────────────────────────────────────────────────
 *
 * `forecastMetric` admits any `spin !== 'none'` and `bestTspin` counts minis as available, but
 * across the four sessions the verified prefix holds exactly ONE mini lock and it is excluded by
 * the no-roof filter, never by the spin filter — 0 of 654 records. `mk` defaults to 'full', and
 * the clause-4 loop above varies the CLOSING clear's spin, not the executed one, so nothing here
 * had ever run the metric on a mini either.
 *
 * Measured rather than assumed: there is no mini/full asymmetry to find. `lk.spin` is read in
 * exactly two places — the `=== 'none'` admission test and the record's own `spin` field — and
 * neither distinguishes a mini from a full spin. That is the right answer as well as the current
 * one: the wiki's definition is about a slot the player set up in advance, and how many corners
 * the T ended up touching is a fact about the execution, not about the forecast. Clause 4 already
 * refuses a size exemption in the other direction ("cleared by NOT tspin" covers a mini closing
 * clear), so exempting the executed spin would leave the two ends of the same window disagreeing
 * about what a T-spin is.
 *
 * These tests PIN that. A future change that gives minis their own arm — dropping them from the
 * numerator, say, or from the denominator — fails here instead of silently moving the rate.
 */
const MINI_CASES: [string, () => SimResult][] = [
  ['reactive', () => mk({ tLock: 3, tCells: T_CELLS, roofOwner: 2 })],
  ['forecast_garbage', () => mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: ROOF_NO_SPIN, boardAtSpin: SPIN_VIA_GARBAGE })],
  ['self_built', () => mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: SB_ROOF, boardAtSpin: SB_SPIN, changeAt: 2, stepCells: SB_CELLS })],
  ['forecast_lineclear', () => mkBoards(PRE_CLEAR)],
];

for (const [name, build] of MINI_CASES) {
  test(`an executed MINI is classified exactly as the full spin is (${name})`, () => {
    const full = build(), mini = build();
    const k = mini.locks.length - 1;
    expect(full.locks[k]!.spin).toBe('full');
    (mini.locks[k] as { spin: string }).spin = 'mini';
    const a = forecastMetric(full), b = forecastMetric(mini);
    // a mini is a T-spin, so it is not filtered out of the denominator
    expect(b.records).toHaveLength(1);
    expect(b.tspins).toBe(a.tspins);
    expect(b.records[0]!.spin).toBe('mini');
    // and every other field of the record, and every total, is identical
    expect({ ...b.records[0]!, spin: 'full' as const }).toEqual(a.records[0]!);
    expect(b.totals).toEqual(a.totals);
    expect(b.forecastRate).toBe(a.forecastRate);
    expect(isVerifiedForecast(b.records[0]!)).toBe(isVerifiedForecast(a.records[0]!));
  });
}

test('an executed MINI reaches the NUMERATOR — the rate is not a full-spin-only rate', () => {
  // The loop above pins full and mini against each other; this pins the level, so a change that
  // excluded minis from BOTH ends (leaving the two runs equal at 0/0) would still fail.
  const r = forecastMetric(mk({ tLock: 4, tCells: T_CELLS, roofOwner: 0, garbageAt: [2],
    boardAtRoof: ROOF_NO_SPIN, boardAtSpin: SPIN_VIA_GARBAGE, spin: 'mini' }));
  expect(r.tspins).toBe(1);
  expect(r.records[0]!.spin).toBe('mini');
  expect(r.records[0]!.kind).toBe('forecast_garbage');
  expect(isVerifiedForecast(r.records[0]!)).toBe(true);
  expect(r.forecastRate).toBe(1);
});

/* ── clause 2 'undetermined', end to end ─────────────────────────────────────────────────────
 *
 * `undecidedClause2`, and the `clause2_undecided` it is emitted as, are 0 in all four session
 * artifacts. The verdict itself is unit-tested (`floorOrigin` above), but the REPORTING path —
 * the number that exists so a rate of zero cannot hide an undecidable case — had never carried a
 * non-zero value, so nothing said whether an undecidable event even reaches a forecast kind
 * rather than being dropped by an earlier clause.
 *
 * It does, and by the STRICT rule rather than the loose fallback. The shape:
 *   · at the roof (lock 1) the board already holds garbage — its bottom row is one hole wide,
 *     which is what a garbage row looks like — so `garbageRows(j) > 0` and garbage on the board
 *     at execution cannot be assumed to have arrived after the overhang;
 *   · one more row arrives at lock 2, so garbage STRADDLES the window and which row is which is
 *     not settleable from the two snapshots;
 *   · the cells holding the T up are garbage, so that undecidable question is exactly the one
 *     clause 2 has to answer;
 *   · and the slot is formed at lock 3 by a clear, so the MECHANISM is established independently
 *     — this is a forecast_lineclear whose clause 2 is unknown, not an event that failed earlier.
 * Counted as a forecast: no. Counted against: also no. It is its own number, which is the point.
 *
 * The boards are a splice of the shape used above with garbage underneath, and every value here
 * was read off the engine, not off the diagram: 0 at the roof, 0 after the arrival (the garbage
 * lands under the stack and offers nothing on its own), 2 after the clear, and the causing step's
 * reconstruction reproduces `boards[3]` cell for cell.
 *
 * It is NOT `spliceOf`'s board, for a reason worth recording. In that family the row that clears
 * is missing exactly the cells the roof row above it fills, so the four cells the clearing piece
 * has to occupy are a COVERED hole: measured over all seven tetrominoes, no hard-drop landing on
 * that board produces them, in any rotation, with slides allowed. It does not matter there —
 * those tests are about the reconstruction arithmetic — but this fixture is a claim about a
 * situation a game can be in, so its clearing row is open from the top instead (the roof row is
 * short on the right, and the I falls straight down cols 6-9), and `reachableAsLanding` below
 * asserts it against the engine rather than by inspection.
 */
/** `mk3` with the named rows written as GARBAGE — same occupancy, so the engine sees exactly the
 *  same board, but `floorOrigin`'s garbage tests can now see them. */
const mk3g = (rows: Record<number, number[]>, garbage: number[]) => {
  const b = mk3(rows);
  for (const r of garbage) for (let c = 0; c < W; c++) if (b[r]![c] !== null) b[r]![c] = 'G';
  return b;
};
/** cols 4-9 open, so the clearing row below is reachable from directly above */
const UND_OPEN = [4, 5, 6, 7, 8, 9];
const UND_ROOF   = mk3g({ 36: UND_OPEN, 37: [6, 7, 8, 9], 38: [3, 4, 5], 39: [4] }, [39]);
const UND_MORE_G = mk3g({ 35: UND_OPEN, 36: [6, 7, 8, 9], 37: [3, 4, 5], 38: [4], 39: [0] }, [38, 39]);
const UND_SPIN   = mk3g({ 36: UND_OPEN, 37: [3, 4, 5], 38: [4], 39: [0] }, [38, 39]);
const UND_CLEAR_CELLS = [6, 7, 8, 9].map(col => ({ col, row: 36 }));

/**
 * Can `cells` be the landing of SOME piece hard-dropped on `board`? Enumerated the way
 * `bestTspin` enumerates T placements: every reachable `rotation:col:row`, slides and rotations
 * included, keeping the ones the piece cannot fall further from. A hand-drawn placement that no
 * piece can reach is the failure this repo has shipped before, and it is not visible by reading
 * the board.
 */
function reachableAsLanding(board: any[][], cells: { col: number; row: number }[]): string[] {
  const key = (cs: { col: number; row: number }[]) =>
    cs.map(c => `${c.col},${c.row}`).sort().join(' ');
  const want = key(cells);
  const hits: string[] = [];
  for (const type of ['I', 'O', 'L', 'J', 'S', 'Z', 'T'] as const) {
    const seen = new Set(['0:3:18']);
    const q: ActivePiece[] = [{ type, rotation: 0, col: 3, row: 18 }];
    for (let h = 0; h < q.length && h < 60000; h++) {
      const cur = q[h]!;
      const d = hardDrop(board as any, cur);
      if (d.row === cur.row && key(getPieceCells(d)) === want) { hits.push(type); break; }
      for (const n of [tryMove(board as any, cur, -1, 0), tryMove(board as any, cur, 1, 0),
                       tryMove(board as any, cur, 0, 1), tryRotate(board as any, cur, 1),
                       tryRotate(board as any, cur, -1)]) {
        if (!n) continue;
        const kk = `${n.rotation}:${n.col}:${n.row}`;
        if (seen.has(kk)) continue; seen.add(kk); q.push(n);
      }
    }
  }
  return hits;
}

function undecidedFixture(): SimResult {
  const k = 5, j = 1, gLock = 2, cLock = 3;
  const locks: any[] = [], provSnaps: any[] = [], boards: any[] = [];
  for (let i = 0; i <= k; i++) {
    locks.push({ frame: i * 100, piece: i === k ? 'T' : 'I',
      cells: i === k ? T_CELLS : i === cLock ? UND_CLEAR_CELLS : [],
      cleared: i === k ? 2 : i === cLock ? 1 : 0, spin: i === k ? 'full' : 'none' });
    const g = Array.from({ length: H }, () => new Array<number | null>(W).fill(null));
    if (i === k - 1) {
      g[T_CELLS[1]!.row - 1]![T_CELLS[1]!.col] = j;                             // a player-built roof
      for (const c of T_CELLS) if (c.row === 31) g[c.row + 1]![c.col] = -1;     // ... on a garbage floor
    }
    provSnaps.push(g);
    boards.push(i <= j ? UND_ROOF : i < cLock ? UND_MORE_G : UND_SPIN);
  }
  return { locks, provSnaps, boards, records: [], events: [], topout: false,
    garbageEvents: [{ frame: gLock * 100, amt: 1, lockIndex: gLock }],
    lines: 0, placed: 0, holds: 0, clears: {}, topbtb: 0, topcombo: 0,
    garbage: { sent: 0, received: 0, cleared: 0, attack: 0 } } as unknown as SimResult;
}

test('clause 2 undetermined REACHES a forecast kind, and is reported instead of counted', () => {
  const f = undecidedFixture();
  // the trajectory, from the engine — the arrival alone offers nothing, the clear is what forms
  // the slot, so the mechanism verdict cannot be an artefact of the garbage that muddies clause 2
  expect(bestTspinLines(f.boards[1]!)).toBe(0);
  expect(bestTspinLines(f.boards[2]!)).toBe(0);
  expect(bestTspinLines(f.boards[4]!)).toBe(2);
  // and the causing step is a placement the game can actually make
  expect(reachableAsLanding(UND_MORE_G, UND_CLEAR_CELLS)).toEqual(['I']);
  // and the straddle itself: garbage really did arrive inside the window, and the roof really
  // did go up while garbage was already on the board
  expect(garbageArrivedAfter(f, 1, 5)).toEqual(new Set([39]));
  expect(floorOrigin(f, 5, 1)).toBe('undetermined');
  expect(floorOrigin(f, 5, 4)).toBe('pre-existed');   // a roof laid AFTER the arrival is decidable

  const r = forecastMetric(f);
  const rec = r.records[0]!;
  expect(rec.determinable).toBe(true);              // the strict rule, not the loose fallback
  expect(rec.mechanism).toBe('line-clear');
  expect(rec.kind).toBe('forecast_lineclear');      // the mechanism IS established ...
  expect(rec.closingClearWasSpin).toBe(false);      // ... and clause 4 does not block it either
  expect(rec.floorOrigin).toBe('undetermined');     // ... and clause 2 still cannot answer
  expect(rec.floorFrom).toBe(-1);
  expect(isVerifiedForecast(rec)).toBe(false);
  expect(r.forecastRate).toBe(0);
  // the number that stops a zero rate hiding an undecidable case, non-zero for the first time
  expect(r.undecidedClause2).toBe(1);
  expect(r.floorOrigins).toEqual({ 'pre-existed': 0, 'arrived-later': 0, undetermined: 1 });
});

/* ── localiseMechanism's two out-of-contract guards ──────────────────────────────────────────
 *
 * `forecastMetric` only ever calls this with `target === avail(k-1)` and only when `improved`,
 * and under those two preconditions both guards below are unreachable: the walk decrements only
 * while `avail(t-1) >= target`, which makes `avail(t) >= target` an invariant, and `improved`
 * rules out `j === k-1`. Measured 2026-08-09 over all four sessions: 0 of 389 calls take either
 * branch, while 85 of them halt at exactly `t === j + 1` — the walk reaches the boundary
 * constantly and never crosses it.
 *
 * But `localiseMechanism` is exported and the tests in this file call it directly with a
 * hand-chosen `j` and `target`. At those arguments the guards are live, and without them the
 * function invents a mechanism instead of declining to name one. So they are contract tests.
 */

test('a roof at the immediately preceding lock is unattributed, not attributed to that lock', () => {
  const row = (cells: string) => [...cells].map(c => c === '.' ? null : 'I');
  const bd = (rows: Record<number, string>) => {
    const b = Array.from({ length: H }, () => new Array<any>(W).fill(null));
    for (const [r, l] of Object.entries(rows)) b[Number(r)] = row(l);
    return b;
  };
  const A = bd({
    30: ".......##.", 31: "......#..#", 32: "......#..#", 33: "......####",
    36: "..##......", 37: "######....", 38: "...#######", 39: "#.########",
  });
  const B = bd({
    31: ".......##.", 32: "......#..#", 33: "......#..#", 34: "......####",
    37: "..##......", 38: "...#######", 39: "#.########",
  });
  const cells = [6, 7, 8, 9].map(col => ({ col, row: 37 }));
  const r = { boards: { 4: A, 5: B }, garbageEvents: [],
    locks: { 5: { cells, piece: 'I', cleared: 1 } } } as unknown as SimResult;
  const avail = (t: number) => bestTspinLines((r.boards as any)[t] ?? A);

  // j = 5 = k - 1: there is no window between roof and spin, so no step can have raised anything.
  expect(localiseMechanism(r, 5, 6, 1, avail)).toEqual({ step: 5, mechanism: 'unattributed' });
  // the same boards one lock earlier, where the window does contain a step, for contrast
  expect(localiseMechanism(r, 4, 6, 1, avail)).toEqual({ step: 5, mechanism: 'placement' });
});

test('a target the causing step never reaches is unattributed, not credited to the garbage', () => {
  const empty = () => Array.from({ length: H }, () => new Array<any>(W).fill(null));
  const A = empty();
  const C = empty();
  C[H - 1] = Array.from({ length: W }, (_, i) => (i === 3 ? null : 'G'));   // one row pushed in
  const r = { boards: { 4: A, 5: C }, garbageEvents: [{ lockIndex: 5, amt: 1, frame: 0 }],
    locks: { 5: { cells: [], piece: 'I', cleared: 0 } } } as unknown as SimResult;
  const avail = (t: number) => bestTspinLines((r.boards as any)[t] ?? A);

  // the step model holds — garbage really did arrive — but nothing on this board offers a T-spin
  expect(avail(4)).toBe(0);
  expect(avail(5)).toBe(0);
  // ... so a target above that must not be blamed on the insertion just because one happened
  expect(localiseMechanism(r, 4, 6, 99, avail)).toEqual({ step: 5, mechanism: 'unattributed' });
});

test('garbageArrivedAfter starts at an empty pre-board when the roof has no placer (j = -1)', () => {
  const empty = () => Array.from({ length: H }, () => new Array<any>(W).fill(null));
  const b0 = empty();
  b0[H - 1] = Array.from({ length: W }, (_, i) => (i === 3 ? null : 'G'));   // one garbage row at lock 0
  const r = { boards: { 0: b0 }, garbageEvents: [{ lockIndex: 0, amt: 1, frame: 0 }],
    locks: { 0: { cells: [], piece: 'I', cleared: 0 } } } as unknown as SimResult;
  // j = -1: the walk starts at lock 0, whose pre-board is the empty field. Reading boards[-1]
  // used to throw here; the row that arrived at lock 0 counts as after the (absent) roof.
  expect(() => garbageArrivedAfter(r, -1, 1)).not.toThrow();
  expect([...garbageArrivedAfter(r, -1, 1)]).toEqual([H - 1]);
});

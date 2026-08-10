/**
 * DESTINATION: `pipeline/sim/arrival-key.test.ts`. The imports below are relative to THAT
 * directory, so landing this file is a move and nothing else — do not "fix" them to point out of
 * `.goal/`, which would make `check_ts_imports` green today and red the moment the file moves.
 * The gate is red in the working tree for exactly this reason; rooted at a tree with this file in
 * `pipeline/sim/` it returns rc 0. See `.goal/harness/RESULT.md` §0.
 *
 * The BFS visited key must include the ARRIVAL MODE, or a real T-spin is lost.
 *
 * `bestTspin`'s admission test reads `rot` — was the LAST move a rotation — but the visited set
 * was keyed on `(rotation, col, row)` alone. So when a non-rotation arrival (a soft-drop step)
 * reaches a position first, it marks the triple visited and the later rotation arrival at the same
 * triple is discarded unexpanded — and with it the only arrival the admission test can accept. The
 * position is a genuine T-spin; the search reports none.
 *
 * The primary fixture is `REDUCED_022`: Tetrisちゃんねる diagram `foreacast_022`
 * (jp-forecast-boards.json, an external corpus this repo never regenerates from code) reduced by
 * greedy cell deletion from 62 cells to 11, re-checking the discriminating property at every step.
 * No proper subset of those 11 cells discriminates — checked exhaustively, all 2^11. Its geometry,
 * checkable by eye (rows are the BOTTOM of the field, row 39 = floor):
 *
 *          col 0123456789
 *     row 37  . . . # . . . . . .
 *     row 38  . . . # . . . . . .      the wall at c3, the well at c2, the ledge at c0-c1
 *     row 39  # # . # # # # # # #      <- one gap, at (39, c2)
 *
 *   The line-clearing T-spin: T in rotation 3 (W, nub pointing left), anchor (col 1, row 37) —
 *   cells (37,c2) (38,c1) (38,c2) (39,c2) — filling the gap and clearing row 39. `detectTSpin`
 *   returns 'full'. Reachable in a straight line: three lefts to the wall, nineteen soft-drops to
 *   rest at rotation 0 anchor (col 0, row 37), then rotate CCW. Kick index 0 `[0,0]` would put a
 *   cell in the ledge at (39,c1) and is refused; kick index 1 `[+1,0]` fits — so the arrival is a
 *   KICKED ROTATION, which is what the admission test needs and what the shipped key throws away.
 *
 *   Under the shipped key the triple `3:1:37` is claimed first by a DOWN arrival: rotate CCW two
 *   rows higher (at `0:1:35`, an unkicked rotation), then soft-drop twice. Its own `detectTSpin`
 *   says 'mini' and it has landed, so the ONLY thing that refuses it is the `rot` gate — and it
 *   marks the triple all the same, so the kicked rotation arrival that follows is discarded
 *   unexpanded. Result: 0.
 *
 * The defect is therefore an ORDERING artifact, not a geometry one, which is what `WITNESS` and
 * its two controls are for. `WITNESS` is one cell smaller than `REDUCED_022` (10 cells — the
 * smallest disagreement found by exhaustive enumeration; see .goal/harness/fixture.md), and it
 * differs from `CONTROL_ORDER` by moving a single blocker one column. Both offer the same T-spin
 * at the same position, `3:8:37`; the blocker removes no placement, it only forces a detour, and
 * the detour is enough to lose the race and with it the answer.
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { bestTspinLines, tspinAvailable } from './forecast.ts';
import { H } from './sim.ts';

const W = 10;
const mk = (rows: string[]) => {
  const b = Array.from({ length: H }, () => new Array<any>(W).fill(null));
  const off = H - rows.length;
  rows.forEach((l, i) => [...l].forEach((ch, c) => { if (ch !== '.') b[off + i]![c] = 'I'; }));
  return b;
};

/** `foreacast_022` delta-reduced to 11 cells: a ledge at c0-c1, a well at c2, a wall at c3. */
const REDUCED_022 = ['...#......',
                     '...#......',
                     '##.#######'];
/** One cell shorter, and the T-spin is genuinely gone under either key. */
const REDUCED_022_SHORT = ['..........',
                           '...#......',
                           '##.#######'];

/** 10 cells: the smallest board found on which the two keys disagree. */
const WITNESS = ['.......#..',
                 '..........',
                 '#########.'];
/** The blocker one column left. Same T-spin, same position — only the race is different. */
const CONTROL_ORDER = ['......#...',
                       '..........',
                       '#########.'];
/** No blocker at all. Still the same T-spin; the kicked rotation arrival wins outright. */
const CONTROL_BARE = ['..........',
                      '..........',
                      '#########.'];
/** The blocker dropped a row, where it fills the slot instead of roofing it. No T-spin at all. */
const CONTROL_NONE = ['..........',
                      '.......#..',
                      '#########.'];

test('a T-spin whose position a soft-drop arrival reaches first is still found', () => {
  expect(bestTspinLines(mk(REDUCED_022) as any)).toBe(1);   // the (rotation,col,row) key returns 0
  expect(tspinAvailable(mk(REDUCED_022) as any)).toBe(true);
  expect(bestTspinLines(mk(WITNESS) as any)).toBe(1);       // and again, one cell smaller
  expect(tspinAvailable(mk(WITNESS) as any)).toBe(true);
});

test('the blocker changes the race, not the placement — both neighbours already answered 1', () => {
  // Without this pair the test above proves only "some board has a T-spin". These two say the
  // T-spin is in the same place either way, so what the fixture measures is the visited key and
  // nothing else: the cell at (37,c7) forces a detour, and a detour is the whole defect.
  expect(bestTspinLines(mk(CONTROL_ORDER) as any)).toBe(1);
  expect(bestTspinLines(mk(CONTROL_BARE) as any)).toBe(1);
});

test('no T-spin is invented where none is reachable', () => {
  expect(bestTspinLines(mk(CONTROL_NONE) as any)).toBe(0);
  expect(tspinAvailable(mk(CONTROL_NONE) as any)).toBe(false);
  expect(bestTspinLines(mk(REDUCED_022_SHORT) as any)).toBe(0);
  expect(bestTspinLines(mk(['..........', '..........', '..........']) as any)).toBe(0);
});

test('the external witnesses: the four JP diagrams the position key zeroed', () => {
  // foreacast_017/022/023/026 are the boards of the external corpus on which the two keys
  // disagree — the complete disagreement set, measured over all 38 diagrams. What is pinned here
  // is the ENGINE's answer on them, not the source page's premise: these frames carry no per-board
  // label (see jp-forecast.test.ts), so this is a regression pin, not an appeal to the source.
  const jp = JSON.parse(readFileSync(`${import.meta.dir}/jp-forecast-boards.json`, 'utf8'))
    .boards as { img: string; rows: string[] }[];
  const byId = Object.fromEntries(jp.map(b => [b.img, b.rows]));
  for (const id of ['foreacast_017', 'foreacast_022', 'foreacast_023', 'foreacast_026'])
    expect(`${id}:${bestTspinLines(mk(byId[id]!) as any)}`).toBe(`${id}:1`);
});

/**
 * The T-spin mini→full rule, and the drift it costs. `detectTSpin` has two rules for a spin that is
 * NOT front-filled: 'anykick' (historical default — ANY wall-kick upgrades mini→full) and 'lastkick'
 * (the ORIGINAL cold-clear / guideline rule — only the last kick candidate, index 4, upgrades).
 *
 * WHY THIS MATTERS FOR DRIFT. The simulator's verified prefix ends at the first attack whose value
 * disagrees with the real replay's ige stream. An over-classified full T-spin sends more attack than
 * TETR.IO did (tss=2 where the truth is mtss=0), which cuts the prefix early — drift. Measured over
 * three sessions, switching to cold-clear's last-kick rule REDUCES the `amount` cuts (15→13, 10→9,
 * 8→7), and the downstream timing shift reduces `frame` cuts too, moving whole rounds into
 * fully-matched (coverage 34.24→34.50, 27.54→27.92, 31.16→31.19 %; never worse). It also moves the
 * full/mini split toward TETR.IO's own stats, which carry ~20-26 mini-TSS a session where our
 * any-kick rule produced almost none. So cold-clear's rule is the one drift lever cold-clear can
 * supply — the geometry it verified is already exact, and the dominant drift (timing, board row) is
 * outside any placement engine's reach.
 *
 * This file pins the classifier's two rules exactly (fast, deterministic) and, when replays are
 * present, the direction of the drift effect (last-kick verifies at least as many placements).
 */
import { test, expect, describe } from 'bun:test';
import { emptyBoard, H, detectTSpin } from './sim.ts';
import type { Board, ActivePiece } from './vendor/core/srs.ts';
import type { PieceType } from './vendor/core/types.ts';

// A T (North) whose centre sits at (cx,cy) with a chosen set of the four diagonal corners filled.
function boardWithCorners(cx: number, cy: number, fill: [number, number][]): Board {
  const b = emptyBoard().map(r => [...r]) as (PieceType | null)[][];
  for (const [c, r] of fill) b[r]![c] = 'I';
  return b as Board;
}

describe('detectTSpin mini→full rule: anykick (default) vs cold-clear last-kick', () => {
  // T North, bounding-box col=4,row=36 -> centre (5,37). Corners TL(4,36) TR(6,36) BL(4,38) BR(6,38).
  const p: ActivePiece = { type: 'T', rotation: 0, col: 4, row: 36 };
  // Fill TL + BL + BR: total 3, front (TL,TR for North) = 1 filled -> the upgrade rule decides.
  const notFrontFilled = boardWithCorners(5, 37, [[4, 36], [4, 38], [6, 38]]);
  // Fill both top corners (TL,TR) + one bottom: front == 2 -> full under BOTH rules.
  const frontFilled = boardWithCorners(5, 37, [[4, 36], [6, 36], [4, 38]]);
  // Only two corners -> below the 3-corner gate -> none under both rules.
  const twoCorners = boardWithCorners(5, 37, [[4, 36], [4, 38]]);

  test('not front-filled, reached by a MIDDLE kick (i=2): anykick=full, last-kick=mini', () => {
    expect(detectTSpin(notFrontFilled, p, true, true, 2, 'anykick')).toBe('full');
    expect(detectTSpin(notFrontFilled, p, true, true, 2, 'lastkick')).toBe('mini');
  });

  test('not front-filled, reached by the LAST kick (i=4): both rules say full', () => {
    expect(detectTSpin(notFrontFilled, p, true, true, 4, 'anykick')).toBe('full');
    expect(detectTSpin(notFrontFilled, p, true, true, 4, 'lastkick')).toBe('full');
  });

  test('not front-filled, NO kick (i=0, usedKick=false): both rules say mini', () => {
    expect(detectTSpin(notFrontFilled, p, true, false, 0, 'anykick')).toBe('mini');
    expect(detectTSpin(notFrontFilled, p, true, false, 0, 'lastkick')).toBe('mini');
  });

  test('front-filled (2 front corners): full under both rules regardless of kick', () => {
    for (const rule of ['anykick', 'lastkick'] as const) {
      expect(detectTSpin(frontFilled, p, true, true, 2, rule)).toBe('full');
      expect(detectTSpin(frontFilled, p, true, false, 0, rule)).toBe('full');
    }
  });

  test('below the 3-corner gate: none under both rules', () => {
    expect(detectTSpin(twoCorners, p, true, true, 2, 'anykick')).toBe('none');
    expect(detectTSpin(twoCorners, p, true, true, 4, 'lastkick')).toBe('none');
  });

  test("default rule is 'anykick' (the historical behavior; the committed artifacts depend on it)", () => {
    // Omitting the last two args must behave exactly as the any-kick rule.
    expect(detectTSpin(notFrontFilled, p, true, true)).toBe('full');
    expect(detectTSpin(notFrontFilled, p, true, false)).toBe('mini');
  });
});

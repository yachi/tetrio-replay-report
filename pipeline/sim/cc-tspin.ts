// SPDX-FileCopyrightText: Cold Clear contributors
// SPDX-License-Identifier: MPL-2.0
//
// This file is a TypeScript port of MinusKelvin/cold-clear rev
// `279edd7c3177ff8077f6a930193397814b281f27`, `libtetris/src/piece.rs` — the T-spin
// classification `rotate()` performs (the `mini_tspin_corners` / `non_mini_tspin_corners`
// tables and the `total >= 3 → Full iff (i == 4 || mini == 2)` rule).
// Cold Clear is licensed under the Mozilla Public License 2.0; as a Modification under
// MPL-2.0 §1.10(b), this file remains under that licence while the rest of this repository
// stays MIT, as MPL-2.0 §3.3 permits for a Larger Work.
//
// This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
// If a copy of the MPL was not distributed with this file, You can obtain one at
// http://mozilla.org/MPL/2.0/.

/**
 * cold-clear's T-spin classifier, ported from `libtetris/src/piece.rs` `rotate()`.
 *
 * WHY THIS EXISTS. `sim.ts` `detectTSpin` (`sim.ts:93`) classifies every T lock as
 * none/mini/full, and that classification drives `clears.*`, the fitted attack table and the
 * forecast admission test. It had exactly one implementation and no outside check. This is a
 * SECOND method for the same question, transcribed from cold-clear's Rust rather than reasoned
 * from ours — so `cross-tspin.test.ts` can differential them and pin where they agree exactly and
 * where they diverge by a KNOWN rule difference rather than a bug.
 *
 * WHAT COLD-CLEAR DOES (piece.rs `rotate()`). After a T lands in a target orientation using kick
 * candidate index `i` (0..4; `i == 4` is the last/5th, TST-style candidate), cold-clear counts the
 * occupied cells at two corner sets relative to the piece origin (the T CENTRE):
 *   mini = |occupied ∩ mini_tspin_corners(target)|
 *   non  = |occupied ∩ non_mini_tspin_corners(target)|
 *   if mini + non >= 3:  Full  iff (i == 4 || mini == 2)  else Mini
 *   else:                None
 * The two corner sets together are the four diagonal corners of the centre; `mini_tspin_corners`
 * are the two corners on the side the T POINTS toward (the "front" corners), `non_mini` the two
 * behind. So `mini == 2` is "both front corners filled".
 *
 * HOW OURS DIFFERS, AND IT IS EXACTLY ONE THING (risk R5). `detectTSpin` uses the identical
 * four-corner 3-corner gate and the identical front-corner set (see `cross-tspin.test.ts`'s
 * corner-agreement proof), so the NONE-vs-SPIN boundary is the same function. It decides full the
 * same way on `frontFilled == 2` (== cold-clear's `mini == 2`). The ONLY difference: on a spin that
 * is not front-filled, OURS upgrades mini→full on ANY kick (`usedKick`, i.e. i >= 1), cold-clear
 * only on the LAST kick (i == 4). So the divergence set is precisely
 *   ours = 'full' ∧ cc = 'mini'  ⟺  spin ∧ mini != 2 ∧ i ∈ {1,2,3}
 * and the reverse (cc full, ours mini) is impossible: cc-full needs mini==2 or i==4, and both of
 * those make ours full too. This is a guideline-vs-TETR.IO formulation difference, NOT a bug —
 * TETR.IO replays, not cold-clear, are ground truth (engine-verification-plan risk R5).
 *
 * THE KICK INDEX `i`. cold-clear sets `tspin` DURING its `rotate()`, keyed on which kick candidate
 * it used. Our `tryRotate` returns only the resulting piece, but the candidate it used is
 * recoverable: it is the first entry of cold-clear's kick sequence (`cc-srs.ts` `ccKicks`, derived
 * from the same `rotation_points` the Rust rotates by, in our [dx,dy] convention) whose displacement
 * equals the observed (post − pre) — sound because a duplicate-displacement earlier candidate would
 * have been the one `tryRotate` returned (identical position ⇒ identical legality). For the T piece
 * `ccKicks == srs.ts JLSZT_KICKS` entry-for-entry (gated by `cross-srs-tables.test.ts`), so this `i`
 * is genuinely cold-clear's own kick index, not an approximation. `ccKickIndex` computes it.
 *
 * FRAMING — this ports cold-clear's classification FUNCTION, not its mover. It answers "for the
 * exact rotation OUR engine performed (from-state, to-state, kick index, board), what does
 * cold-clear's corner+i rule say?" — holding the arrival fixed. Whether cold-clear's OWN mover would
 * arrive by the same rotation is a separate (reachability) question, covered by `cross-movegen`.
 *
 * COORDINATES. cold-clear is y-UP (y=0 bottom, +y up); ours is row-DOWN (row 0 top, 40 rows, +dy
 * down). This module works entirely in OUR row-down frame: a cold-clear corner offset (ox, oy) in
 * y-up maps to our cell (cx + ox, cy − oy). `occ()` treats walls (x∉0..9) and the floor (row>=40) as
 * occupied and the sky (row<0) as empty — cold-clear's physical `occupied()` in our frame. The
 * conversion is unit-tested FIRST in `cross-tspin.test.ts`, because getting the flip wrong reports
 * "no corners filled" on every board, which reads as agreement (`cc-oracle.rs` / `cc-tslot.ts` house
 * rule: a port that detects nothing agrees with everything).
 *
 * PROVENANCE CAVEAT. This port has not been run against the Rust original (that is item 4's binary
 * `CC_ORACLE_LOCK` mode). Its corner geometry and the none-vs-spin identity are pinned by
 * `cross-tspin.test.ts`, and a liveness assertion there pins that spins are actually produced,
 * because a differential that finds no spins agrees vacuously.
 */
import { ccKicks } from './cc-srs.ts';
import type { PieceType } from './vendor/core/types.ts';
import type { Board, ActivePiece } from './vendor/core/srs.ts';

const H = 40, W = 10;
export type TspinStatus = 'none' | 'mini' | 'full';
type Rot = 0 | 1 | 2 | 3;

/**
 * cold-clear's `Board::occupied` in OUR row-down frame: walls and the floor (below the board) are
 * occupied, the sky (above the board) is empty. Physically identical to cold-clear's y-up rule.
 */
export function occ(board: Board, c: number, r: number): boolean {
  if (c < 0 || c >= W) return true;   // wall
  if (r >= H) return true;            // floor (below the 40-row board)
  if (r < 0) return false;            // sky (above the board)
  return board[r]![c] !== null;
}

// cold-clear's corner tables, transcribed from piece.rs, y-UP offsets (ox, oy) from the T centre.
// mini_tspin_corners = the two corners on the side the T POINTS toward (the "front" corners).
const MINI_CORNERS: Record<Rot, readonly [number, number][]> = {
  0: [[-1, 1], [1, 1]],     // North (points up):    top two
  1: [[1, 1], [1, -1]],     // East  (points right): right two
  2: [[1, -1], [-1, -1]],   // South (points down):  bottom two
  3: [[-1, -1], [-1, 1]],   // West  (points left):  left two
};
const NON_MINI_CORNERS: Record<Rot, readonly [number, number][]> = {
  0: [[1, -1], [-1, -1]],   // North: bottom two (behind)
  1: [[-1, -1], [-1, 1]],   // East:  left two
  2: [[-1, 1], [1, 1]],     // South: top two
  3: [[1, 1], [1, -1]],     // West:  right two
};

/** Count occupied cells among a y-up corner set, applied at the T centre (cx, cy) in our frame. */
function countCorners(board: Board, cx: number, cy: number, corners: readonly [number, number][]): number {
  let n = 0;
  for (const [ox, oy] of corners) if (occ(board, cx + ox, cy - oy)) n++;   // y-up → row-down: cy − oy
  return n;
}

/**
 * cold-clear's `TspinStatus` for a resting T at `piece`, reached using kick candidate index
 * `kickIndex` (0..4). Non-T pieces are never a T-spin.
 */
export function ccTspin(board: Board, piece: ActivePiece, kickIndex: number): TspinStatus {
  if (piece.type !== 'T') return 'none';
  // T centre in our bounding-box coords is offset (1,1) — the same centre `detectTSpin` uses.
  const cx = piece.col + 1, cy = piece.row + 1;
  const mini = countCorners(board, cx, cy, MINI_CORNERS[piece.rotation]);
  const non = countCorners(board, cx, cy, NON_MINI_CORNERS[piece.rotation]);
  if (mini + non < 3) return 'none';
  return (kickIndex === 4 || mini === 2) ? 'full' : 'mini';
}

/**
 * cold-clear's kick index `i` (0..4) for a rotation `from → to` of `piece` that displaced the origin
 * by (dx, dy) in our row-down convention: the first entry of `ccKicks` matching that displacement, or
 * −1 if none matches (which never happens for a rotation `tryRotate` actually performed). See the
 * module header for why "first match" recovers the exact candidate our engine used.
 */
export function ccKickIndex(piece: PieceType, from: Rot, to: Rot, dx: number, dy: number): number {
  const seq = ccKicks(piece, from, to);
  for (let i = 0; i < seq.length; i++) if (seq[i]![0] === dx && seq[i]![1] === dy) return i;
  return -1;
}

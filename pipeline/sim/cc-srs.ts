// SPDX-FileCopyrightText: Cold Clear contributors
// SPDX-License-Identifier: MPL-2.0
//
// This file is a TypeScript port of MinusKelvin/cold-clear `libtetris/src/piece.rs`
// (the `rotation_points()` offset table and the `rotate()` kick derivation).
// Cold Clear is licensed under the Mozilla Public License 2.0; as a Modification under
// MPL-2.0 §1.10(b), this file remains under that licence while the rest of this repository
// stays MIT, as MPL-2.0 §3.3 permits for a Larger Work.
//
// This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
// If a copy of the MPL was not distributed with this file, You can obtain one at
// http://mozilla.org/MPL/2.0/.

/**
 * cold-clear's SRS kick data, ported from MinusKelvin/cold-clear rev
 * `279edd7c3177ff8077f6a930193397814b281f27`, `libtetris/src/piece.rs`.
 *
 * WHY THIS EXISTS. `cross-movegen.test.ts` proves our BFS *reaches* every placement cold-clear's
 * mover reaches, but that gate is deliberately a SUBSET (`cc ⊆ ours`) and — measured — survives a
 * corrupted kick candidate, because our BFS has many non-kick paths to most resting cells. So the
 * reachability differential does not pin the kick VALUES. This does: it derives cold-clear's kick
 * table from the same `rotation_points` the original Rust rotates by, and asserts it entry-for-entry
 * against `srs.ts` — the check that a transposed `[+1,0]→[+2,0]` fails.
 *
 * HOW cold-clear ROTATES. `rotate()` does not carry an explicit per-transition kick table. It stores
 * five "rotation points" per (piece, orientation) and, for a transition a→b, tries the offsets
 * `rotation_points(a)[i] − rotation_points(b)[i]` for i in 0..5 (the SRS Offset method; the first is
 * always (0,0)). `ccKicks()` reproduces exactly that.
 *
 * COORDINATES. cold-clear is y-UP (+y = up); ours is row-down (+dy = DOWN). The x term is identical;
 * the y term negates. That is the one conversion, applied once in `ccKicks`.
 *
 * THREE OUTCOMES, all verified in `cross-srs-tables.test.ts`, none a bug:
 *  - JLSTZ: `ccKicks` equals our `JLSZT_KICKS` EXACTLY, all 8 transitions.
 *  - I: equals our `I_KICKS` up to a single per-transition CONSTANT offset — cold-clear's piece
 *    origin is the rotation centre, ours is the bounding-box corner, and for the 4-wide I those
 *    differ by a whole cell that shifts with orientation. The offset is constant across all five
 *    candidates of a transition, i.e. the kick SEQUENCE is identical; it cancels when applied to the
 *    actual piece cells, which `cross-movegen.test.ts` confirms (I reaches the identical 17 placements
 *    on an empty board).
 *  - O: cold-clear's `rotation_points` move the O on rotation to keep it centred; our O has identity
 *    kicks and identical cells in all four states, so it never moves either way. Same resting cells,
 *    different representation — again confirmed by `cross-movegen.test.ts` (O reaches 9 = 9).
 *
 * NOT AN ORACLE FOR SRS+. `srs.ts` `I_KICKS_PLUS` is TETR.IO's SRS+ (an order-only I-kick change);
 * cold-clear implements guideline SRS only, so this file is silent on it. See `cross-srs-tables`
 * risk-R4 note.
 */
import type { PieceType } from './vendor/core/types.ts';

type P = readonly [number, number];

// rotation_points, transcribed verbatim from piece.rs. Orientation index: 0=North, 1=East,
// 2=South, 3=West (cold-clear's cw cycle N→E→S→W == our rotation 0→1→2→3).
const ROTATION_POINTS: Record<'I' | 'O' | 'JLSTZ', Record<0 | 1 | 2 | 3, P[]>> = {
  O: {
    0: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
    1: [[0, -1], [0, -1], [0, -1], [0, -1], [0, -1]],
    2: [[-1, -1], [-1, -1], [-1, -1], [-1, -1], [-1, -1]],
    3: [[-1, 0], [-1, 0], [-1, 0], [-1, 0], [-1, 0]],
  },
  I: {
    0: [[0, 0], [-1, 0], [2, 0], [-1, 0], [2, 0]],
    1: [[-1, 0], [0, 0], [0, 0], [0, 1], [0, -2]],
    2: [[-1, 1], [1, 1], [-2, 1], [1, 0], [-2, 0]],
    3: [[0, 1], [0, 1], [0, 1], [0, -1], [0, 2]],
  },
  // T, L, J, S, Z all share one table in cold-clear.
  JLSTZ: {
    0: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
    1: [[0, 0], [1, 0], [1, -1], [0, 2], [1, 2]],
    2: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
    3: [[0, 0], [-1, 0], [-1, -1], [0, 2], [-1, 2]],
  },
};

const familyOf = (t: PieceType): 'I' | 'O' | 'JLSTZ' => (t === 'I' ? 'I' : t === 'O' ? 'O' : 'JLSTZ');

/**
 * cold-clear's SRS kick candidate list for `piece` rotating `from → to`, converted into OUR
 * convention (`[dx, dy]`, `+dy = DOWN`). Derived as `rotation_points(from)[i] − rotation_points(to)[i]`
 * with the y term negated.
 */
export function ccKicks(piece: PieceType, from: 0 | 1 | 2 | 3, to: 0 | 1 | 2 | 3): P[] {
  const tbl = ROTATION_POINTS[familyOf(piece)];
  const a = tbl[from], b = tbl[to];
  return a.map((p, i) => [p[0] - b[i]![0], -(p[1] - b[i]![1])] as P);
}

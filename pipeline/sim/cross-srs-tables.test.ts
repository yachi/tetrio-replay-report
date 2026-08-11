/**
 * SRS kick tables, entry-for-entry against the ORIGINAL cold-clear.
 *
 * This is the exact, corpus-free companion to `cross-movegen.test.ts`. That test proves our BFS
 * reaches a superset of cold-clear's placements; measured, it survives a corrupted single kick
 * candidate (our BFS routes around it). This closes that gap: it asserts our kick tables in
 * `vendor/core/srs.ts` equal cold-clear's own (derived from `rotation_points` in `cc-srs.ts`) with no
 * corpus and no tolerance — the check a transposed `[+1,0]→[+2,0]` cannot pass.
 *
 * It reads the REAL exported tables from `srs.ts`, not a transcription, so a mutation to the shipped
 * table flows into the assertion. See `cc-srs.ts` for the three outcomes and why the I constant-shift
 * and the O representation difference are equivalences, not bugs (both additionally confirmed
 * operationally by `cross-movegen.test.ts`).
 */
import { test, expect, describe } from 'bun:test';
import { JLSZT_KICKS, I_KICKS, O_KICKS } from './vendor/core/srs.ts';
import { ccKicks } from './cc-srs.ts';
import type { PieceType } from './vendor/core/types.ts';

type P = readonly [number, number];
const TRANSITIONS: [0 | 1 | 2 | 3, 0 | 1 | 2 | 3][] = [[0, 1], [1, 0], [1, 2], [2, 1], [2, 3], [3, 2], [3, 0], [0, 3]];
const key = (a: number, b: number) => `${a}->${b}` as keyof typeof JLSZT_KICKS;
const eq = (x: P, y: P) => x[0] === y[0] && x[1] === y[1];

describe('SRS kick tables vs original cold-clear rotation_points', () => {
  test('JLSTZ: our JLSZT_KICKS equals cold-clear EXACTLY, all 8 transitions', () => {
    let compared = 0;
    for (const [a, b] of TRANSITIONS) {
      const cc = ccKicks('T', a, b);
      const ours = JLSZT_KICKS[key(a, b)] as P[];
      expect(ours.length).toBe(5);           // anti-vacuity: a real 5-candidate list, not empty
      expect(cc.length).toBe(5);
      for (let i = 0; i < 5; i++) {
        expect(eq(cc[i]!, ours[i]!), `JLSTZ ${a}->${b} candidate ${i}: cc=[${cc[i]}] ours=[${ours[i]}]`).toBe(true);
        compared++;
      }
    }
    expect(compared).toBe(40);               // 8 transitions x 5 candidates
  });

  test('JLSTZ table is shared by all of T,L,J,S,Z (same rotation_points family)', () => {
    for (const t of ['T', 'L', 'J', 'S', 'Z'] as PieceType[])
      for (const [a, b] of TRANSITIONS)
        for (let i = 0; i < 5; i++)
          expect(eq(ccKicks(t, a, b)[i]!, (JLSZT_KICKS[key(a, b)] as P[])[i]!)).toBe(true);
  });

  test('I: our I_KICKS equals cold-clear up to ONE constant per-transition shift (origin convention)', () => {
    // The kick SEQUENCE must be identical modulo a single constant offset shared by all 5 candidates
    // of a transition — the bounding-box vs rotation-centre origin difference for the 4-wide I. A
    // real kick error (a wrong candidate) breaks the "constant across all 5" property.
    let shifts = 0;
    for (const [a, b] of TRANSITIONS) {
      const cc = ccKicks('I', a, b);
      const ours = I_KICKS[key(a, b)] as P[];
      const d0: P = [cc[0]![0] - ours[0]![0], cc[0]![1] - ours[0]![1]];
      for (let i = 0; i < 5; i++) {
        const di: P = [cc[i]![0] - ours[i]![0], cc[i]![1] - ours[i]![1]];
        expect(eq(di, d0), `I ${a}->${b} candidate ${i} shift [${di}] != transition shift [${d0}] — not a pure origin offset`).toBe(true);
      }
      shifts++;
    }
    expect(shifts).toBe(8);
  });

  test('O: identity kicks; cold-clear\'s centre-rotation and ours differ only in representation', () => {
    // Our O never moves on rotation (identity kick + identical cells all 4 states). cold-clear's
    // rotation_points move the O to keep it centred. Equivalence of the RESULTING cells is proven in
    // cross-movegen.test.ts (O reaches 9 = 9 on an empty board); here we just pin that ours is the
    // single-candidate identity so a regression that let O kick would fail.
    for (const [a, b] of TRANSITIONS) {
      const ours = O_KICKS[key(a, b)] as P[];
      expect(ours.length).toBe(1);
      expect(eq(ours[0]!, [0, 0])).toBe(true);
    }
  });

  // I_KICKS_PLUS (TETR.IO SRS+) is intentionally NOT tested here: it is an order-only I-kick change
  // and cold-clear implements guideline SRS only, so cold-clear is not a valid oracle for it (risk R4
  // in the plan). Its authority is TETR.IO replays via ab-kickset.ts, not this file.
});

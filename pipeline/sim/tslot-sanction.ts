/**
 * ONE near-topout sanction, shared by every consumer of the cold-clear differential.
 *
 * Three things ask the same question — "cold-clear names a T-slot our BFS does not reach; is that a
 * defect in our detector, or a known over-count of cold-clear's height patterns?" — and until
 * 2026-08-17 only one of them had an answer. `cross-tslot.test.ts` carried the rule inline;
 * `cross-tslot-count.ts` and `cross-tslot-multi.ts` carried no rule at all, because at the
 * hand-port board source they never saw a board that needed one. Pointing those two at
 * `runCaseOracle` (the board source the published metric consumes) makes them see the same
 * near-topout boards the test already sees, so the rule has to live in one place or the three
 * will drift into three different sanctions for one question.
 *
 * WHAT IS SANCTIONED, and why it is not a licence. On a stack within a few rows of spawn the T can
 * barely manoeuvre, and cold-clear's detectors match COLUMN-HEIGHT patterns rather than reachable
 * placements — so they name a slot no piece can actually be flown into. Verified by hand on
 * 2026-08-01 `replay-2026-08-01-4.ttrm` r0 yachi lock 66 (`sky_tslot_right`): the full reachability
 * BFS enumerates 16 placements uncapped and 0 T-spins, so our search is right and cold-clear
 * over-counts. A slot our search cannot reach is a REAL defect whenever the board is not
 * near-topout — there it would mean a false negative in the instrument every published forecast
 * figure rests on.
 *
 * The classification is returned, never a bare boolean, so all three consumers can print the same
 * evidence line. "6 failures tolerated" says nothing; "tolerated because no spin is reachable and
 * the stack tops out at row 19, three below spawn" is checkable by a reader.
 */
import { detectTSpin, H } from './sim.ts';
import { tryMove, tryRotate, hardDrop, getPieceCells } from './vendor/core/srs.ts';
import type { ActivePiece } from './vendor/core/srs.ts';

/** Only occupancy is read (`null` vs anything), so every consumer's board shape fits. */
type AnyBoard = readonly (readonly unknown[])[];

/**
 * Spawn row 18 is the T's spawn in this engine; `NEAR_TOPOUT_ROW` is 3 rows above it. A board whose
 * highest filled row is at or above this is "near-topout": the piece has almost no room to rotate
 * or shift, which is exactly the regime where a height pattern and a reachability search part ways.
 */
export const NEAR_TOPOUT_ROW = 21;

/** `bestTspin` with the line-clear requirement dropped — the question cold-clear actually asks. */
export function anySpinLines(board: AnyBoard): number | null {
  const spawn: ActivePiece = { type: 'T', rotation: 0, col: 3, row: 18 };
  const seen = new Set(['0:3:18']);
  const q: { p: ActivePiece; rot: boolean; kick: boolean }[] = [{ p: spawn, rot: false, kick: false }];
  for (let h = 0; h < q.length && h < 40000; h++) {
    const { p: cur, rot, kick } = q[h]!;
    const d = hardDrop(board as never, cur);
    if (d.row === cur.row && rot && detectTSpin(board as never, d, true, kick) !== 'none') {
      const after = board.map(r => [...r]);
      for (const c of getPieceCells(d)) if (c.row >= 0 && c.row < H) after[c.row]![c.col] = 'T';
      return after.filter(r => r.every(x => x !== null)).length;
    }
    for (const [n, isRot] of [[tryMove(board as never, cur, -1, 0), false], [tryMove(board as never, cur, 1, 0), false],
        [tryMove(board as never, cur, 0, 1), false], [tryRotate(board as never, cur, 1), true],
        [tryRotate(board as never, cur, -1), true]] as [ActivePiece | null, boolean][]) {
      if (!n) continue;
      const k = `${n.rotation}:${n.col}:${n.row}`;
      if (seen.has(k)) continue; seen.add(k);
      q.push({ p: n, rot: isRot, kick: isRot && (n.col !== cur.col || n.row !== cur.row) });
    }
  }
  return null;
}

/** Highest filled row (lowest index) — a near-spawn value means a near-topout, low-manoeuvre board. */
export function stackTop(board: AnyBoard): number {
  for (let r = 0; r < H; r++) if (board[r]!.some(x => x !== null)) return r;
  return H;
}

export interface TslotSanction {
  /** true = a cold-clear slot our search cannot reach is EXPLAINED here, not a defect. */
  sanctioned: boolean;
  /** highest filled row; `H` on an empty board. */
  stackTop: number;
  /** lines a reachable T-spin would clear, or `null` when the BFS reaches no T-spin at all. */
  anySpinLines: number | null;
  /** one line, the same wording in all three consumers. */
  reason: string;
}

/**
 * Classify a board on which cold-clear names something our search does not.
 *
 * Callers must apply this ONLY where our side found nothing (`bestTspinLines === 0`). A board where
 * both sides find a slot and cold-clear's count is the larger is an under-count, a different defect
 * with a different cause, and no near-topout argument touches it — `cross-tslot-count.ts` has always
 * failed those unconditionally and still does.
 */
export function classify(board: AnyBoard): TslotSanction {
  const spin = anySpinLines(board);
  const top = stackTop(board);
  const sanctioned = !(spin === null && top > NEAR_TOPOUT_ROW);
  const reason = spin !== null
    ? `a T-spin IS reachable (clears ${spin}) — cold-clear counts slots that clear nothing`
    : top > NEAR_TOPOUT_ROW
      ? `no T-spin reachable and stackTop ${top} > ${NEAR_TOPOUT_ROW} — NOT near-topout, a real false negative`
      : `no T-spin reachable, stackTop ${top} <= ${NEAR_TOPOUT_ROW} — near-topout, cold-clear's height pattern over-counts`;
  return { sanctioned, stackTop: top, anySpinLines: spin, reason };
}

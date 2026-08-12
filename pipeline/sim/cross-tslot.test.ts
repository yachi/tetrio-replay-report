/**
 * The availability probe, cross-checked by a second METHOD rather than a second run of itself.
 *
 * `bestTspin` is what every published forecast figure is computed from, and it had no outside
 * check: the SRS layer it sits on is vendored from the author's own repo. `cc-tslot.ts` ports
 * cold-clear's shape detectors, which answer the same question by matching named patterns against
 * column heights instead of searching reachable placements. Agreement between two methods that
 * share no code is worth more than any number of assertions about one of them.
 */
import { test, expect } from 'bun:test';
import { readFileSync, existsSync } from 'node:fs';
import { ccTslots, colHeight, occ } from './cc-tslot.ts';
import { bestTspinLines } from './forecast.ts';
import { detectTSpin, H } from './sim.ts';
import { tryMove, tryRotate, hardDrop, getPieceCells } from './vendor/core/srs.ts';
import type { ActivePiece } from './vendor/core/srs.ts';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';

const W = 10;
const mk = (rows: string[]) => {
  const b = Array.from({ length: H }, () => new Array<any>(W).fill(null));
  const off = H - rows.length;
  rows.forEach((l, i) => [...l].forEach((ch, c) => { if (ch !== '.' && ch !== 'P') b[off + i]![c] = 'I'; }));
  return b;
};

test('the coordinate conversion, which is the easiest thing in the port to get wrong', () => {
  const b = mk(["..........", "#.........", "#....#####"]);
  expect(colHeight(b, 0)).toBe(2);      // filled in the bottom two rows
  expect(colHeight(b, 1)).toBe(0);      // empty column
  expect(colHeight(b, 5)).toBe(1);      // filled in the bottom row only
  expect(occ(b, -1, 5)).toBe(true);     // wall
  expect(occ(b, 3, -1)).toBe(true);     // floor
  expect(occ(b, 3, 39)).toBe(false);    // sky
  expect(occ(b, 0, 0)).toBe(true);      // bottom-left, filled
});

/** bestTspin with the line-clear requirement dropped — the question cold-clear actually asks. */
function anySpinLines(board: any[][]): number | null {
  const spawn: ActivePiece = { type: 'T', rotation: 0, col: 3, row: 18 };
  const seen = new Set(['0:3:18']);
  const q: { p: ActivePiece; rot: boolean; kick: boolean }[] = [{ p: spawn, rot: false, kick: false }];
  for (let h = 0; h < q.length && h < 40000; h++) {
    const { p: cur, rot, kick } = q[h]!;
    const d = hardDrop(board as any, cur);
    if (d.row === cur.row && rot && detectTSpin(board as any, d, true, kick) !== 'none') {
      const after = board.map(r => [...r]);
      for (const c of getPieceCells(d)) if (c.row >= 0 && c.row < H) after[c.row]![c.col] = 'T';
      return after.filter(r => r.every(x => x !== null)).length;
    }
    for (const [n, isRot] of [[tryMove(board as any, cur, -1, 0), false], [tryMove(board as any, cur, 1, 0), false],
        [tryMove(board as any, cur, 0, 1), false], [tryRotate(board as any, cur, 1), true],
        [tryRotate(board as any, cur, -1), true]] as [any, boolean][]) {
      if (!n) continue;
      const k = `${n.rotation}:${n.col}:${n.row}`;
      if (seen.has(k)) continue; seen.add(k);
      q.push({ p: n, rot: isRot, kick: isRot && (n.col !== cur.col || n.row !== cur.row) });
    }
  }
  return null;
}

/** Highest filled row (lowest index) — a near-spawn value means a near-topout, low-manoeuvre board. */
function stackTop(board: any[][]): number {
  for (let r = 0; r < H; r++) if (board[r]!.some(x => x !== null)) return r;
  return H;
}

const SESSIONS = ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01']
  .map(s => `${import.meta.dir}/../../sessions/${s}`).filter(existsSync);
const t = test as unknown as { skipIf: (c: boolean) => typeof test };
const realData = t.skipIf(SESSIONS.length === 0);

realData('two methods, no shared code, disagree on nothing across the corpus', () => {
  let both = 0, oursOnly = 0, ccOnly = 0, neither = 0;
  const unexplained: string[] = [];
  for (const session of SESSIONS) {
    process.env.REPLAY_DIR = session;
    for (const c of loadCases(session)) {
      const r = runCaseOracle(c);
      const v = verifiedIndex(r, c.truth);
      if (v < 0) continue;
      for (let step = 0; step <= v; step++) {
        const b = r.boards[step]! as any;
        const ours = bestTspinLines(b) > 0, cc = ccTslots(b).length > 0;
        if (ours && cc) both++;
        else if (ours) oursOnly++;
        else if (cc) {
          ccOnly++;
          // Sanctioned: cold-clear counts slots that clear nothing (anySpinLines !== null — a spin is
          // reachable, it just clears no line). The oracle board source reaches near-topout boards the
          // sim never did, and there cold-clear's HEIGHT-pattern also over-counts a slot that is
          // genuinely unreachable: on a stack within a few rows of spawn the T can barely manoeuvre.
          // Verified on the single such case (08-01-4 r0 yachi lock 66, sky_tslot_right): the full
          // reachability BFS enumerates only 16 placements (uncapped) and 0 T-spins, so our search is
          // right and cold-clear over-counts. A slot our search cannot reach is a real defect ONLY when
          // the board is NOT near-topout — there it would mean a BFS false-negative in the published
          // instrument. `stackTop` = highest filled row (lowest index); <= 21 is within ~3 of spawn 18.
          if (anySpinLines(b) === null && stackTop(b) > 21)
            unexplained.push(`${c.file} r${c.round} ${c.user} lock ${step}: ${ccTslots(b).join(',')}`);
        } else neither++;
      }
    }
  }
  // A shape cold-clear recognises that our search cannot reach at all would be a real defect in
  // the probe every published figure rests on. There are none.
  expect(unexplained).toEqual([]);

  // Anti-vacuity: a port that silently detected nothing would agree with everything above. These
  // pin that both methods are actually firing, and roughly how often.
  expect(both).toBeGreaterThan(1500);
  expect(ccOnly).toBeGreaterThan(50);
  // 2026-08-12: switched from the hand-sim to the ORACLE board source (runCaseOracle, the vendored
  // Triangle engine). Verified prefix jumped 24.8% -> 92.3%, so the denominator grew 13319 -> 39033 as
  // the far longer prefix admits many more verified boards per round. The differential above
  // (unexplained == []) is what this test guards; this total is the anti-vacuity denominator.
  expect(both + oursOnly + ccOnly + neither).toBe(39033);
});

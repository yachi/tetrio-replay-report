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
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';

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
      const r = runCase(c, {});
      const v = verifiedIndex(r, c.truth);
      if (v < 0) continue;
      for (let step = 0; step <= v; step++) {
        const b = r.boards[step]! as any;
        const ours = bestTspinLines(b) > 0, cc = ccTslots(b).length > 0;
        if (ours && cc) both++;
        else if (ours) oursOnly++;
        else if (cc) {
          ccOnly++;
          // the ONLY sanctioned explanation: cold-clear counts slots that clear nothing
          if (anySpinLines(b) === null)
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
  // 7544 -> 9878 -> 10295 -> 10397 -> 10587 -> 11076 -> 11540 -> 13328 -> 13319 on 2026-08-11/12: `hoisted`-DAS (~31%),
  // `attackModel:'exact'` (~4%), confirm-timed garbage (~1.2%), triangle's DAS/ARR port (~1.8%), then
  // exact-subframe processing (~4%), then per-subframe #fall (~3.5%), then the network garbage-cancel port (~15%), then locktime 60->30 (triangle default). The differential above (unexplained == []) is
  // what this test guards; this total is the anti-vacuity denominator and tracks the longer prefix.
  expect(both + oursOnly + ccOnly + neither).toBe(13319);
});

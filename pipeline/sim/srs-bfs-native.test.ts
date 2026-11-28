/**
 * The Rust BFS (`srs-bfs-rs`) must answer exactly what the TS BFS over the vendored SRS primitives
 * answers, for both modes, in order, on seeded boards (all seven pieces, SRS and SRS+ for I) and on a
 * stride of real verified-prefix boards (`SRS_BFS_NATIVE_FULL=1`: every one). The cross tests use
 * the Rust side as OUR side only; this file is what keeps it honest against the TS reference.
 */
import { test, expect, describe } from 'bun:test';
import { emptyBoard, H } from './sim.ts';
import type { Board } from './vendor/core/srs.ts';
import type { PieceType } from './vendor/core/types.ts';
import { nativeDrops, nativeSpinEdges, tsDrops, tsSpinEdges } from './srs-bfs-native.ts';
import { loadCases, runCase, verifiedIndex } from './verified-prefix.ts';
import { discoverCorpus } from '../corpus-membership.ts';

const W = 10;
const PIECES: PieceType[] = ['I', 'T', 'O', 'S', 'Z', 'L', 'J'];

function randomBoards(seed: number, n: number, maxH: number): Board[] {
  let t = seed % 2147483647; if (t <= 0) t += 2147483646;
  const rnd = () => (t = (16807 * t) % 2147483647) / 2147483647;
  const boards: Board[] = [];
  for (let i = 0; i < n; i++) {
    const b = emptyBoard().map(r => [...r]) as (PieceType | null)[][];
    for (let c = 0; c < W; c++) {
      const h = Math.floor(rnd() * (maxH + 1));
      for (let k = 0; k < h; k++) if (rnd() < 0.78) b[H - 1 - k]![c] = 'I';
    }
    boards.push(b as Board);
  }
  return boards;
}

function compare(boards: Board[], pieces: PieceType[], plusToo: boolean) {
  for (const [bi, board] of boards.entries()) {
    for (const p of pieces) {
      const plusSet = plusToo && p === 'I' ? [false, true] : [false];
      for (const plus of plusSet) {
        const a = nativeDrops(board, p, 3, 18, plus), b = tsDrops(board, p, 3, 18, plus);
        if (JSON.stringify(a) !== JSON.stringify(b)) expect(a, `drops board ${bi} ${p} plus=${plus}`).toEqual(b);
        const c = nativeSpinEdges(board, p, 3, 18, plus), d = tsSpinEdges(board, p, 3, 18, plus);
        if (JSON.stringify(c) !== JSON.stringify(d)) expect(c, `spins board ${bi} ${p} plus=${plus}`).toEqual(d);
      }
    }
  }
}

describe('srs-bfs-rs == the TS BFS', () => {
  test('seeded boards, all pieces, SRS and SRS+ for I, both modes, in order', () => {
    const boards = [...randomBoards(12345, 120, 12), ...randomBoards(67890, 120, 18), ...randomBoards(999, 60, 8)];
    compare(boards, PIECES, true);
  }, 120_000);

  test('an empty board and a spawn-blocked board', () => {
    const blocked = emptyBoard().map(r => [...r]) as (PieceType | null)[][];
    for (let c = 0; c < W; c++) blocked[18]![c] = 'I';
    compare([emptyBoard() as Board, blocked as Board], PIECES, true);
    expect(nativeDrops(blocked as Board, 'T')).toEqual([]);
  }, 120_000);

  test('control: the comparison sees a wrong answer', () => {
    const b = emptyBoard() as Board;
    const good = nativeDrops(b, 'T');
    expect(good.length).toBeGreaterThan(0);
    const bad = good.map(x => [...x] as [number, number, number]);
    bad[0]![1] += 1;
    expect(JSON.stringify(bad)).not.toBe(JSON.stringify(tsDrops(b, 'T')));
    expect(JSON.stringify(good)).toBe(JSON.stringify(tsDrops(b, 'T')));
  });

  const sessions = discoverCorpus(`${import.meta.dir}/../../sessions`).map(d => `${import.meta.dir}/../../sessions/${d}`);
  test.skipIf(sessions.length === 0)('a stride of real verified-prefix boards (SRS_BFS_NATIVE_FULL=1: all)', () => {
    const stride = process.env.SRS_BFS_NATIVE_FULL === '1' ? 1 : 1500;
    const boards: Board[] = [];
    let k = 0;
    for (const session of sessions) {
      process.env.REPLAY_DIR = session;
      for (const c of loadCases(session)) {
        const r = runCase(c, {});
        const v = verifiedIndex(r, c.truth);
        for (let step = 0; step <= v; step++) { if (k++ % stride === 0) boards.push(r.boards[step]!); }
      }
    }
    expect(boards.length).toBeGreaterThan(0);
    compare(boards, ['T', 'I', 'S', 'L'], true);
  }, 600_000);
});

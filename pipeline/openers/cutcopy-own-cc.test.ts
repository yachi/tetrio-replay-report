/**
 * A SECOND IMPLEMENTATION behind our own 千鳥格子 designs (`analysis/cutcopy-own.json`): the ORIGINAL
 * cold-clear, asked about the two T's each demo fires.
 *
 * WHY. Every own design is planned by `technique-demos.ts` over `route-demos.ts`'s `reach()` and
 * accepted by the vendored Triangle engine, so "the T could get there" and "it is a full T-spin
 * clearing two" each had one implementation behind them. This asks cold-clear, which shares no code
 * with either, the same two questions for the stood T and the follow-up T of every published demo,
 * on the board decoded from the demo's own timeline (`decodeTimeline`, from empty) just BEFORE that
 * lock:
 *
 *  (a) REACH — is the T's exact resting placement (its four cells) among the placements
 *      `libtetris::find_moves(ZeroGComplete)` returns? The real Rust binary at `$CC_ORACLE`
 *      (`nix build .#cc-oracle`), `CC_ORACLE_MOVES=1`, the same protocol `cross-movegen.test.ts`
 *      speaks (its line format and canonical key, copied rather than imported, because importing a test
 *      file registers its suite). cold-clear's mover reaches a
 *      SUBSET of ours — it shifts only at rest heights and has no per-cell soft drop, so it misses
 *      mid-height tucks (`cross-movegen.test.ts`, pipeline/sim/README.md) — so a placement it does not
 *      reach is that documented asymmetry, not a failure: it must be NAMED in `CC_UNREACHED` with the
 *      measured reason (a bound would absorb a new one silently).
 *  (b) SPIN — cold-clear's `rotate()` T-spin rule (`cc-tspin.ts`, ported from `piece.rs`; the port's
 *      none-vs-spin boundary is gated against ours in `cross-tspin.test.ts`). The binary's movegen
 *      line carries cells only, not a `TspinStatus`, so the rule is evaluated on the placement. Its
 *      verdict depends on the KICK INDEX only when fewer than both front corners are filled; the
 *      timeline does not record which kick our engine used, so the verdict is taken over EVERY index
 *      0..4 and asserted full under all of them — true exactly when both front corners are filled,
 *      which the test also pins. The LINE COUNT is the rows the four cells complete on that board,
 *      counted here, not read from the engine's lock record.
 *
 * Skipped, like the cross tests, when the binary is absent (the `typescript` job has no nix); CI runs
 * it in verify.yml's `oracle-image` job beside them.
 */
import { test, expect, describe } from 'bun:test';
import { existsSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { decodeTimeline, queueStates, placeCells, WIDTH, ROWS } from '../sim/emit-replay.ts';
import { ccTspin } from '../sim/cc-tspin.ts';
import { getPieceCells } from '../sim/vendor/core/srs.ts';
import type { Board, ActivePiece } from '../sim/vendor/core/srs.ts';
import type { PieceType } from '../sim/vendor/core/types.ts';

const ORACLE = process.env.CC_ORACLE ?? `${import.meta.dir}/../../result/bin/cc-oracle`;
const HAVE_ORACLE = existsSync(ORACLE);
const committed = JSON.parse(readFileSync(`${import.meta.dir}/../../analysis/cutcopy-own.json`, 'utf8'));

/** (demo node, which T) → the measured reason cold-clear's mover does not reach a placement ours did.
 *  Measured empty: cold-clear reaches every own design's two T placements. */
const CC_UNREACHED: Record<string, string> = {};

/** Same canonical key `cross-movegen.test.ts` uses: the four [col,row] cells, top-down, sorted (row, col). */
const keyOf = (cells: [number, number][]) =>
  cells.slice().sort((a, b) => a[1] - b[1] || a[0] - b[0]).map(c => `${c[0]},${c[1]}`).join('|');

/** One oracle call over every (board, piece) case, `CC_ORACLE_MOVES=1` — the protocol of
 *  `cross-movegen.test.ts`'s `ccReachableBatch` (not imported: that test file runs its own suite on import). */
function ccReachable(boards: string[][]): Set<string>[] {
  const input = boards.map(rows => 'T\n' + rows.join('\n')).join('\n') + '\n';
  const res = spawnSync(ORACLE, { input, encoding: 'utf8', env: { ...process.env, CC_ORACLE_MOVES: '1' } });
  if (res.status !== 0) throw new Error('cc-oracle failed: ' + res.stderr);
  const lines = res.stdout.split('\n').filter(l => l.trim());
  if (lines.length !== boards.length) throw new Error(`oracle returned ${lines.length} lines for ${boards.length} cases`);
  return lines.map(l => new Set((JSON.parse(l) as { placements: [number, number][][] }).placements.map(keyOf)));
}

interface Case { node: string; which: 'stood' | 'followup'; rows: string[]; board: Board; cells: [number, number][] }

function cases(): Case[] {
  const out: Case[] = [];
  for (const d of committed.demos) {
    const after: (string | null)[][][] = [];
    decodeTimeline(d.seq, d.locks, (bd, i) => { after[i] = bd.map(r => [...r]); });
    const q = queueStates(d.seq, d.locks);
    for (const [which, i] of [['stood', d.stood_lock], ['followup', d.followup_lock]] as const) {
      if (q[i]!.piece !== 'T') throw new Error(`${d.node}: lock ${i} placed ${q[i]!.piece}, not T`);
      const before = after[i - 1]!;                          // yUp
      const rows: string[] = [];                             // top-down, the oracle's frame
      for (let r = 0; r < ROWS; r++) rows.push(before[ROWS - 1 - r]!.map(c => (c == null ? '.' : 'X')).join(''));
      const board = rows.map(s => [...s].map(ch => (ch === '.' ? null : 'I'))) as (PieceType | null)[][];
      const cells = placeCells('T', d.locks[i][1]).map(c => [c % WIDTH, ROWS - 1 - Math.floor(c / WIDTH)] as [number, number]);
      out.push({ node: d.node, which, rows, board, cells });
    }
  }
  return out;
}

/** The ActivePiece whose cells are exactly `cells` (top-down), searched over all four rotations. */
function pieceOf(cells: [number, number][]): ActivePiece {
  const want = keyOf(cells);
  const found: ActivePiece[] = [];
  for (const rotation of [0, 1, 2, 3] as const)
    for (let col = -2; col < WIDTH; col++) for (let row = -2; row < ROWS; row++) {
      const p: ActivePiece = { type: 'T', rotation, col, row };
      if (keyOf(getPieceCells(p).map(c => [c.col, c.row])) === want) found.push(p);
    }
  if (found.length !== 1) throw new Error(`${found.length} T pieces have cells ${want}`);
  return found[0]!;
}

/** Rows the four cells complete on `board` (top-down), counted on the board, not read from the engine. */
function linesCompleted(board: Board, cells: [number, number][]): number {
  const g = board.map(r => r.map(c => c !== null));
  for (const [c, r] of cells) { expect(g[r]![c]).toBe(false); g[r]![c] = true; }
  return g.filter(r => r.every(Boolean)).length;
}

/** Filled front corners (cold-clear's `mini_tspin_corners`) of a T at `p`: the two the T points at. */
function frontFilled(board: Board, p: ActivePiece): number {
  const cx = p.col + 1, cy = p.row + 1;
  const front: Record<number, [number, number][]> = { 0: [[-1, -1], [1, -1]], 1: [[1, -1], [1, 1]], 2: [[-1, 1], [1, 1]], 3: [[-1, -1], [-1, 1]] };
  return front[p.rotation]!.filter(([dc, dr]) => {
    const c = cx + dc, r = cy + dr;
    return c < 0 || c >= WIDTH || r >= ROWS || (r >= 0 && board[r]![c] !== null);
  }).length;
}

describe.skipIf(!HAVE_ORACLE)('own 千鳥格子 designs vs the original cold-clear', () => {
  const cs = HAVE_ORACLE ? cases() : [];
  const reach = HAVE_ORACLE ? ccReachable(cs.map(c => c.rows)) : [];

  test('every published demo is measured, two T\'s each', () => {
    expect(committed.demos.length).toBeGreaterThan(0);
    expect(cs.length).toBe(2 * committed.demos.length);
    for (const s of reach) expect(s.size).toBeGreaterThan(0);   // a mover reaching nothing agrees with everything
  });

  test('(a) cold-clear\'s find_moves reaches each T placement, or the miss is named', () => {
    const missed: Record<string, string> = {};
    cs.forEach((c, k) => {
      const id = `${c.node}:${c.which}`;
      if (!reach[k]!.has(keyOf(c.cells))) missed[id] = CC_UNREACHED[id] ?? 'UNNAMED';
    });
    expect(missed).toEqual(CC_UNREACHED);
  });

  test('(b) cold-clear\'s rotate() rule: a full T-spin clearing two, under every kick index', () => {
    cs.forEach((c, k) => {
      if (!reach[k]!.has(keyOf(c.cells))) return;            // named in CC_UNREACHED, classification moot
      const p = pieceOf(c.cells);
      expect(p.rotation, `${c.node}:${c.which}`).toBe(2);      // the flat, nub-down T the window anchors
      expect(frontFilled(c.board, p), `${c.node}:${c.which}`).toBe(2);
      for (let i = 0; i <= 4; i++) expect(ccTspin(c.board, p, i), `${c.node}:${c.which} i=${i}`).toBe('full');
      expect(linesCompleted(c.board, c.cells), `${c.node}:${c.which}`).toBe(2);
    });
  });
});

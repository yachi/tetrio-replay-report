/**
 * Is the BFS cap ever reachable? bestTspinLines caps at 40000, tspinAvailable at 20000.
 * If the true state space is far below both, the differing caps are dead numbers and the two
 * functions are equivalent BY CONSTRUCTION, not merely on the boards we sampled.
 *
 * Upper bound on reachable states: 4 rotations x 10 cols x 40 rows = 1600 keys, and the `seen`
 * set is keyed exactly on `rotation:col:row`. Measured here to confirm the bound is real.
 */
import { emptyBoard, H } from './sim.ts';
import { tryMove, tryRotate, hardDrop } from './vendor/core/srs.ts';
import type { Board, ActivePiece } from './vendor/core/srs.ts';

function statesExplored(board: Board): number {
  const spawn: ActivePiece = { type: 'T', rotation: 0, col: 3, row: 18 };
  const seen = new Set(['0:3:18']);
  const q: ActivePiece[] = [spawn];
  for (let h = 0; h < q.length && h < 1e9; h++) {
    const cur = q[h]!;
    hardDrop(board, cur);
    for (const n of [tryMove(board, cur, -1, 0), tryMove(board, cur, 1, 0),
                     tryMove(board, cur, 0, 1), tryRotate(board, cur, 1), tryRotate(board, cur, -1)]) {
      if (!n) continue;
      const k = `${n.rotation}:${n.col}:${n.row}`;
      if (seen.has(k)) continue; seen.add(k); q.push(n);
    }
  }
  return q.length;
}

function rng(seed: number) { let t = seed % 2147483647; if (t <= 0) t += 2147483646;
  return () => ((t = (16807 * t) % 2147483647) - 1) / 2147483646; }

function genStack(r: () => number): Board {
  const b = emptyBoard().map(row => [...row]) as (string | null)[][];
  let h = 2 + Math.floor(r() * 6); const hs: number[] = [];
  for (let c = 0; c < 10; c++) { h = Math.max(0, Math.min(12, h + Math.floor(r() * 5) - 2)); hs.push(h); }
  for (let c = 0; c < 10; c++) for (let i = 0; i < hs[c]!; i++) b[H - 1 - i]![c] = 'I';
  for (let i = 0, n = Math.floor(r() * 6); i < n; i++) {
    const c = Math.floor(r() * 10); if (hs[c]! < 1) continue;
    b[H - 1 - Math.floor(r() * hs[c]!)]![c] = null;
  }
  return b as Board;
}

let max = 0, argmax = 0;
for (let s = 1; s <= 2000; s++) {
  const n = statesExplored(genStack(rng(s * 7919)));
  if (n > max) { max = n; argmax = s; }
}
const empty = statesExplored(emptyBoard());

console.log(`theoretical key bound  4 rot x 10 col x 40 row = ${4 * 10 * H}`);
console.log(`max states explored    ${max}  (seed ${argmax}, over 2000 stack boards)`);
console.log(`empty board            ${empty}`);
console.log(`tspinAvailable cap     20000  -> ${20000 / max}x headroom`);
console.log(`bestTspinLines cap     40000  -> ${40000 / max}x headroom`);
console.log(max < 20000
  ? '\nCAPS ARE UNREACHABLE. The two functions run the identical BFS; the cap difference\ncannot produce a behavioural difference, so equivalence is structural, not sampled.'
  : '\nCAP IS REACHABLE — the two functions can genuinely diverge. Do not merge them.');

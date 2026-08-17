/**
 * How far is the BFS cap from being reached? bestTspinLines caps at 40000, tspinAvailable at
 * 20000 (until they were merged in 2026-07-30). The `seen` set is keyed exactly on
 * `rotation:col:row`, so the key space is what bounds `q`.
 *
 * That bound is only PARTLY derivable. 4 rotations, and 10 anchor columns — but -1..8, not 0..9:
 * `isValidPosition` rejects a cell outside 0..9 and the T's anchor is offset asymmetrically, so R
 * runs -1..7 (leftmost cell at offset 1), L runs 0..8 (rightmost cell at offset 1) and 0/2 run
 * 0..7. Rows are the hole — `vendor/core/srs.ts:129` is `if (row < 0) continue`, so any negative
 * row is a legal position and the engine imposes no ceiling at all. 4 x 10 x 40 = 1600 was
 * therefore never a theorem; it assumed rows 0..39. What stops the climb is the kick table, not
 * the collision test, and nobody has written that argument down.
 *
 * So this file measures rather than derives: it reports the row and column span actually reached
 * as well as the state count, which turns the row range from an assumption into an observation
 * over 2000 boards. Everything it prints is sampled evidence, and the caps stay as live belts.
 *
 * ── IT MEASURES THE SEARCH NOW, NOT A REPLICA OF IT (2026-08-16) ─────────────────────────────────
 * Until this revision it imported `vendor/core/srs.ts` and walked its OWN copy of the BFS, never
 * importing `forecast.ts` at all. So when the 2026-08-10 arrival-key fix split the visited key in
 * two, this file printed the same 688 before and after — and **that agreement was worth nothing as
 * evidence**, because a replica cannot disagree with an engine it never calls. The measured pair
 * queue under the landed key is 848, a number this file could not produce.
 *
 * It now drives `bestTspin` through `withBfsTrace`, so every figure below is the shipped search's.
 * The board generator and the self-check are unchanged, and the self-check deliberately stays on
 * `vendor/core/srs.ts`: it is a claim about what the ENGINE admits as a legal position, which is
 * upstream of any search and is the premise the caps rest on.
 */
import { emptyBoard, H } from './sim.ts';
import { bestTspin, withBfsTrace } from './forecast.ts';
import { isValidPosition } from './vendor/core/srs.ts';
import type { Board, ActivePiece } from './vendor/core/srs.ts';

/**
 * The reason `h < 40000` must survive: the key space is NOT bounded the way the old comment
 * claimed. These are executable witnesses against the engine, so the next person to read
 * "measured max 688, far under the cap" and conclude the cap is dead code hits a failing script
 * instead of a plausible-looking argument. A printed number could not have stopped that — the
 * old derivation sat beside the same 688 for weeks.
 */
function assertKeySpaceIsNotBounded() {
  const b = emptyBoard();
  const at = (rotation: 0 | 1 | 2 | 3, col: number, row: number): ActivePiece =>
    ({ type: 'T', rotation, col, row });
  const fail = (what: string) => { console.error(`SELF-CHECK FAILED ${what}`); process.exit(1); };
  // Rows: srs.ts skips the board lookup for row < 0 instead of rejecting it, so arbitrarily
  // negative rows are legal positions. This is the whole reason 4 x 10 x 40 was never a theorem.
  if (!isValidPosition(b, at(0, 3, -5))) fail('a negative row is rejected — the row factor would now be bounded, so this file (and forecast.ts) needs rewriting, not the cap deleting');
  // Columns: 10 values but -1..8, and asymmetrically — only R reaches -1, only L reaches 8.
  if (!isValidPosition(b, at(1, -1, 18))) fail('rotation R no longer reaches col -1');
  if (!isValidPosition(b, at(3, 8, 18))) fail('rotation L no longer reaches col 8');
  if (isValidPosition(b, at(0, -1, 18)) || isValidPosition(b, at(0, 8, 18)))
    fail('rotation 0 now reaches -1 or 8 — the per-rotation column spans have changed');
}
assertKeySpaceIsNotBounded();

/** The shipped search's own numbers for one board. `queue` is the PAIR queue `h < 40000` bounds. */
function statesExplored(board: Board) {
  return withBfsTrace(() => bestTspin(board)).trace;
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

let maxQ = 0, argmaxQ = 0, maxPos = 0;
const span = { rowLo: Infinity, rowHi: -Infinity, colLo: Infinity, colHi: -Infinity };
for (let s = 1; s <= 2000; s++) {
  const e = statesExplored(genStack(rng(s * 7919)));
  if (e.queue > maxQ) { maxQ = e.queue; argmaxQ = s; }
  maxPos = Math.max(maxPos, e.positions);
  span.rowLo = Math.min(span.rowLo, e.rowLo); span.rowHi = Math.max(span.rowHi, e.rowHi);
  span.colLo = Math.min(span.colLo, e.colLo); span.colHi = Math.max(span.colHi, e.colHi);
}
const empty = statesExplored(emptyBoard());
const rows = span.rowHi - span.rowLo + 1, cols = span.colHi - span.colLo + 1;

console.log(`col span reached       ${span.colLo}..${span.colHi}  (${cols} of the 10 the engine allows: -1..8)`);
console.log(`row span reached       ${span.rowLo}..${span.rowHi}  (${rows} rows; the engine allows ANY row < ${H},`);
console.log(`                       including negatives — srs.ts:129 is \`if (row < 0) continue\`)`);
console.log(`key bound IF rows stay in [-2, ${H - 1}]   4 rot x 10 col x ${H + 2} row = ${4 * 10 * (H + 2)}`);
// TWO numbers, because the search has two dedup keys since 2026-08-10 and only one of them
// bounds the queue the cap tests. Reporting a single "states explored" is what let the pre-fix
// and post-fix engines look identical here.
console.log(`max distinct POSITIONS  ${maxPos}  (rotation:col:row — the expansion key)`);
console.log(`max PAIR QUEUE          ${maxQ}  (seed ${argmaxQ}, over 2000 stack boards; this is`);
console.log(`                        what \`h < 40000\` bounds, at ${(maxQ / maxPos).toFixed(2)} entries per position)`);
console.log(`empty board             ${empty.queue} queued, ${empty.positions} positions`);
console.log(`tspinAvailable cap      20000  -> ${20000 / maxQ}x headroom`);
console.log(`bestTspinLines cap      40000  -> ${40000 / maxQ}x headroom`);
console.log(maxQ < 20000
  ? `\nNO SAMPLED BOARD COMES NEAR EITHER CAP (${maxQ} vs 20000). That is evidence, not a proof:\nthe row range above is measured over 2000 generated stacks, and the engine itself does not\nbound rows, so the caps stay LIVE belts. What makes the merged BFS safe is that there is now\none loop, not that 40000 was shown to be unreachable.`
  : '\nCAP IS REACHABLE — a capped BFS can genuinely truncate. The cap is doing real work.');

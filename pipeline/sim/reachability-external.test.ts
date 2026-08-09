/**
 * Reachability completeness of the availability engine, gated over the external corpora.
 *
 * The detector's numerator rests on `bestTspin` finding every executable T-spin: if it under-reads
 * `avail(t)`, a real improvement is scored `reactive` and a forecast is lost. This runs the
 * reachability differential (reachability-external.ts): every JP / four.lol frame that draws a
 * NEWLY-PLACED, line-clearing T is a witness that a spin of that size is reachable on the board
 * without it, and the engine must re-find one. A miss would be a genuine false negative suppressing
 * the corpus count.
 *
 * Result, committed: the engine reaches every externally-witnessed executed spin (0 misses). So the
 * ~0 forecast count is NOT a reachability false negative — the examples corroborate it. The three
 * C-Spin diagrams the engine cannot reach (wiki-fixtures `UNREACHABLE`) need a 180 rotation the
 * players never press, and none of them is an executed spin here.
 */
import { test, expect } from 'bun:test';
import { run } from './reachability-external.ts';

test('the engine reaches every executed T-spin drawn in the JP and four.lol corpora', () => {
  const { checked } = run();
  // there are real witnesses (guards against the harness silently checking nothing)
  expect(checked.length).toBeGreaterThanOrEqual(5);
  const misses = checked.filter(r => !r.ok);
  expect(misses.map(m => `${m.id}: needs>=${m.expect} got ${m.reached}`)).toEqual([]);
});

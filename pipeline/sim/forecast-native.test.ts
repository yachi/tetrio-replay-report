/**
 * `forecast-rs` (the Rust port of `bestTspin`, loaded by `forecast-native.ts`) against the TS
 * reference `bestTspinTs`: on every board the forecast metric asks `bestTspin` about, the two
 * answers must be equal as JSON — `lines`, the slot's `rows` in order, and the `floor`.
 *
 * The boards are the metric's own: each player-round is replayed (`runCaseOracle`), and where the
 * emitter would run `forecastMetric(r, true)` (a verified prefix exists) it is run here under
 * `withBestTspinBoards`, which hands over every board the search is called with. By default every
 * player-round of 2026-10-20 (the shortest night) plus every SAMPLE_STRIDE-th player-round of the
 * other sessions, in the loader's order (deterministic, no random draw). FORECAST_NATIVE_FULL=1
 * compares all of them. A board seen twice is compared once.
 */
import { test, expect } from 'bun:test';
import { readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { loadCases, runCaseOracle, verifiedIndex } from './verified-prefix.ts';
import { forecastMetric, withBestTspinBoards, bestTspin, bestTspinTs, withBfsTrace } from './forecast.ts';
import { nativeBestTspin } from './forecast-native.ts';
import type { Board } from './vendor/core/srs.ts';

const SESSIONS = resolve(import.meta.dir, '../../sessions');
const FULL = process.env.FORECAST_NATIVE_FULL === '1';
const SHORT = '2026-10-20';
const SAMPLE_STRIDE = 17;

const key = (b: Board) => b.map(r => r.map(x => (x === null ? '.' : 'x')).join('')).join('/');

test(`the Rust bestTspin equals the TS reference (${FULL ? 'every player-round' : `all of ${SHORT}, every ${SAMPLE_STRIDE}th elsewhere`})`, () => {
  let rounds = 0, total = 0, calls = 0, found = 0;
  const seen = new Set<string>();
  const bad: string[] = [];
  for (const s of readdirSync(SESSIONS).sort()) {
    const cases = loadCases(join(SESSIONS, s));
    cases.forEach((c, i) => {
      total++;
      if (!FULL && s !== SHORT && i % SAMPLE_STRIDE !== 0) return;
      const r = runCaseOracle(c);
      if (verifiedIndex(r, c.truth) < 0) return;
      rounds++;
      const boards: Board[] = [];
      withBestTspinBoards(b => boards.push(b), () => forecastMetric(r, true));
      calls += boards.length;
      for (const b of boards) {
        const k = key(b);
        if (seen.has(k)) continue;
        seen.add(k);
        const want = bestTspinTs(b), got = nativeBestTspin(b);
        if (got === undefined) { bad.push(`${s} ${c.file} r${c.round} ${c.user}: board not 40x10`); continue; }
        if (want) found++;
        if (JSON.stringify(want) !== JSON.stringify(got)) bad.push(`${s} ${c.file} r${c.round} ${c.user}: ${k}`);
      }
    });
  }
  console.log(`forecast-native: ${rounds} player-rounds of ${total}, ${calls} bestTspin calls, `
    + `${seen.size} distinct boards (${found} with a T-spin), ${bad.length} differ`);
  expect(bad).toEqual([]);
  expect(seen.size).toBeGreaterThan(FULL ? 30_000 : 2_000);   // a walk that found nothing cannot pass
  expect(found).toBeGreaterThan(0);                          // and boards with an answer were compared
}, FULL ? 7_200_000 : 600_000);

test('a traced call runs the TS reference, so withBfsTrace still reports a search', () => {
  const c = loadCases(join(SESSIONS, SHORT))[0]!;
  const b = runCaseOracle(c).boards[20]!;
  const { value, trace } = withBfsTrace(() => bestTspin(b));
  expect(trace.queue).toBeGreaterThan(0);
  expect(JSON.stringify(value)).toBe(JSON.stringify(bestTspinTs(b)));
});

test('a board that is not 40 x 10 is not ported: the native side declines it', () => {
  const short = Array.from({ length: 20 }, () => Array.from({ length: 10 }, () => null));
  expect(nativeBestTspin(short)).toBeUndefined();
  const narrow = Array.from({ length: 40 }, () => Array.from({ length: 9 }, () => null));
  expect(nativeBestTspin(narrow)).toBeUndefined();
});

/**
 * `oracle-rs` (the Rust port of the oracle replay, loaded by `oracle-native.ts`) against the TS
 * reference `runCaseOracleTs`: the two SimResults must be equal byte for byte as JSON, key order
 * included, which is everything any consumer can read off them.
 *
 * By default every player-round of 2026-10-20 (the shortest night) plus every SAMPLE_STRIDE-th
 * player-round of the other sessions, in the loader's order (deterministic, no random draw).
 * ORACLE_NATIVE_FULL=1 compares all of them. Neither path goes through the oracle cache.
 *
 * Also: `f64::ln_1p` equals JS `Math.log1p` bit for bit over the arguments the garbage formula
 * passes it, and the generated `oracle-rs/src/data.rs` is what `gen-oracle-rs-data.ts` renders now.
 */
import { test, expect } from 'bun:test';
import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { loadCases } from './verified-prefix.ts';
import { runCaseOracleTs, TL_DEFAULTS } from './oracle-source.ts';
import { nativeLog1p, runCaseOracleNative } from './oracle-native.ts';
import { DATA_RS, render } from './gen-oracle-rs-data.ts';

const SESSIONS = resolve(import.meta.dir, '../../sessions');
const FULL = process.env.ORACLE_NATIVE_FULL === '1';
const SHORT = '2026-10-20';
const SAMPLE_STRIDE = 17;

test(`the Rust oracle equals the TS reference (${FULL ? 'every player-round' : `all of ${SHORT}, every ${SAMPLE_STRIDE}th elsewhere`})`, () => {
  let n = 0, total = 0;
  const bad: string[] = [];
  for (const s of readdirSync(SESSIONS).sort()) {
    const cases = loadCases(join(SESSIONS, s));
    cases.forEach((c, i) => {
      total++;
      if (!FULL && s !== SHORT && i % SAMPLE_STRIDE !== 0) return;
      n++;
      const a = JSON.stringify(runCaseOracleTs(c.rawPlayer, c.rawRound!));
      const b = JSON.stringify(runCaseOracleNative(c.rawPlayer, TL_DEFAULTS));
      if (a !== b) bad.push(`${s} ${c.file} r${c.round} ${c.user}`);
    });
  }
  console.log(`oracle-native: ${n} of ${total} player-rounds compared, ${bad.length} differ`);
  expect(bad).toEqual([]);
  expect(n).toBeGreaterThan(FULL ? 3000 : 200);       // a walk that found nothing cannot pass
}, FULL ? 3_600_000 : 600_000);

test('f64::ln_1p is JS Math.log1p, bit for bit, on every argument the garbage formula passes it', () => {
  const bits = new Float64Array(2), view = new BigUint64Array(bits.buffer);
  const bad: number[] = [];
  for (let k = 0; k <= 10_000; k++) {
    for (const x of [k * 0.8, k * 1.25]) {
      bits[0] = Math.log1p(x); bits[1] = nativeLog1p(x);
      if (view[0] !== view[1]) bad.push(x);
    }
  }
  expect(bad).toEqual([]);
});

test('oracle-rs/src/data.rs is what gen-oracle-rs-data.ts renders from the vendored engine', () => {
  expect(readFileSync(DATA_RS, 'utf8')).toBe(render());
});

test('a rule set the port does not carry is refused, never approximated', () => {
  const c = loadCases(join(SESSIONS, SHORT))[0]!;
  const p = c.rawPlayer;
  for (const [k, v] of [['kickset', 'SRS'], ['bagtype', '14-bag'], ['boardwidth', 12], ['can_retry', true], ['usebombs', true]] as const) {
    const player = { ...p, replay: { ...p.replay, options: { ...p.replay.options, [k]: v } } };
    expect(() => runCaseOracleNative(player, TL_DEFAULTS)).toThrow(/unsupported/);
  }
  // the unchanged player is accepted, so the refusals above are about the one option each changes
  expect(() => runCaseOracleNative(p, TL_DEFAULTS)).not.toThrow();
});

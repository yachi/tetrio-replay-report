/**
 * emit-attack-facts.ts's `runRoundNative` (the Rust engine's per-lock reads, oracle-rs/src/facts.rs
 * through facts-native.ts) against its TS reference `runRoundTs` (the vendored engine and its
 * `falling.lock` listener): the two lock lists must be equal byte for byte as JSON, key order included.
 *
 * By default every player-round of 2026-10-20 (the shortest night) plus every SAMPLE_STRIDE-th
 * player-round of the other sessions, in the loader's order (deterministic, no random draw).
 * ATTACK_NATIVE_FULL=1 compares all of them.
 */
import { test, expect } from 'bun:test';
import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { loadCases } from './verified-prefix.ts';
import { runRoundNative, runRoundTs } from './emit-attack-facts.ts';

const SESSIONS = resolve(import.meta.dir, '../../sessions');
const FULL = process.env.ATTACK_NATIVE_FULL === '1';
const SHORT = '2026-10-20';
const SAMPLE_STRIDE = 17;

test(`the Rust engine's attack reads equal runRound's TS reference (${FULL ? 'every player-round' : `all of ${SHORT}, every ${SAMPLE_STRIDE}th elsewhere`})`, () => {
  let n = 0, total = 0, locks = 0;
  const bad: string[] = [];
  for (const s of readdirSync(SESSIONS).sort()) {
    loadCases(join(SESSIONS, s)).forEach((c, i) => {
      total++;
      if (!FULL && s !== SHORT && i % SAMPLE_STRIDE !== 0) return;
      n++;
      const ts = runRoundTs(c);
      locks += ts.length;
      if (JSON.stringify(ts) !== JSON.stringify(runRoundNative(c))) bad.push(`${s} ${c.file} r${c.round} ${c.user}`);
    });
  }
  console.log(`attack-native: ${n} of ${total} player-rounds compared (${locks} locks), ${bad.length} differ`);
  expect(bad).toEqual([]);
  expect(n).toBeGreaterThan(FULL ? 3000 : 200);       // a walk that found nothing cannot pass
}, FULL ? 3_600_000 : 600_000);

test('runRound is the native run unless ATTACK_NATIVE=off', () => {
  const src = readFileSync(join(import.meta.dir, 'emit-attack-facts.ts'), 'utf8');
  expect(src).toContain("process.env.ATTACK_NATIVE === 'off' ? runRoundTs(c) : runRoundNative(c)");
});

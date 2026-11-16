/**
 * emit-finesse-facts.ts's `runRoundNative` (the Rust engine's per-lock reads, oracle-rs/src/facts.rs
 * through facts-native.ts) against its TS reference `runRoundTs` (the vendored engine, its `falling.*`
 * listeners and the re-armed key cache): the two piece lists must be equal byte for byte as JSON, key
 * order included, under the shipped rule and under both of the emitter's mutants (`softDropOnPress`
 * reads the keys pressed on the piece, which the shipped rule does not).
 *
 * By default every player-round of 2026-10-20 (the shortest night) plus every SAMPLE_STRIDE-th
 * player-round of the other sessions, in the loader's order (deterministic, no random draw).
 * FINESSE_NATIVE_FULL=1 compares all of them.
 */
import { test, expect } from 'bun:test';
import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { loadCases } from './verified-prefix.ts';
import { runRoundNative, runRoundTs, type Mutant, type Table } from './emit-finesse-facts.ts';

const SESSIONS = resolve(import.meta.dir, '../../sessions');
const FULL = process.env.FINESSE_NATIVE_FULL === '1';
const SHORT = '2026-10-20';
const SAMPLE_STRIDE = 17;
const MUTANTS: [string, Mutant][] = [['shipped', {}], ['scoreSoftDrop', { scoreSoftDrop: true }], ['softDropOnPress', { softDropOnPress: true }]];

test(`the Rust engine's finesse reads equal runRound's TS reference (${FULL ? 'every player-round' : `all of ${SHORT}, every ${SAMPLE_STRIDE}th elsewhere`})`, () => {
  let n = 0, total = 0, pieces = 0;
  const bad: string[] = [];
  const tables = new Map<string, Table>();
  for (const s of readdirSync(SESSIONS).sort()) {
    loadCases(join(SESSIONS, s)).forEach((c, i) => {
      total++;
      if (!FULL && s !== SHORT && i % SAMPLE_STRIDE !== 0) return;
      n++;
      for (const [name, m] of MUTANTS) {
        const ts = runRoundTs(c, tables, m);
        if (name === 'shipped') pieces += ts.length;
        if (JSON.stringify(ts) !== JSON.stringify(runRoundNative(c, tables, m))) bad.push(`${s} ${c.file} r${c.round} ${c.user} ${name}`);
      }
    });
  }
  console.log(`finesse-native: ${n} of ${total} player-rounds compared (${pieces} pieces, ${MUTANTS.length} rules each), ${bad.length} differ`);
  expect(bad).toEqual([]);
  expect(n).toBeGreaterThan(FULL ? 3000 : 200);       // a walk that found nothing cannot pass
}, FULL ? 3_600_000 : 600_000);

test('runRound is the native run unless FINESSE_NATIVE=off', () => {
  const src = readFileSync(join(import.meta.dir, 'emit-finesse-facts.ts'), 'utf8');
  expect(src).toContain("process.env.FINESSE_NATIVE === 'off' ? runRoundTs(c, tables, mutant) : runRoundNative(c, tables, mutant)");
});

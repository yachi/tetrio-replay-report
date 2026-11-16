/**
 * `runPlayerNative` (replay-native.ts, the Rust engine's instrumented run in oracle-rs/src/trace.rs)
 * against the TS reference `runPlayerTs` (emit-replay.ts: the vendored engine and `instrumentEngine`):
 * the two return values must be equal byte for byte as JSON, key order included — every lock tuple,
 * engine board key, queue read, the piece sequence and each counter.
 *
 * By default every player-round of 2026-10-20 (the shortest night) plus every SAMPLE_STRIDE-th
 * player-round of the other sessions, in the loader's order (deterministic, no random draw).
 * REPLAY_NATIVE_FULL=1 compares all of them. The engine date is each replay file's own `ts`, as
 * emit-replay.ts's `build` passes it.
 */
import { test, expect } from 'bun:test';
import { readdirSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { loadCases } from './verified-prefix.ts';
import { runPlayerTs } from './emit-replay.ts';
import { runPlayerNative } from './replay-native.ts';

const SESSIONS = resolve(import.meta.dir, '../../sessions');
const FULL = process.env.REPLAY_NATIVE_FULL === '1';
const SHORT = '2026-10-20';
const SAMPLE_STRIDE = 17;

function dateOf(dir: string, file: string, cache: Map<string, Date>): Date {
  if (!cache.has(file)) cache.set(file, new Date(JSON.parse(readFileSync(join(dir, file), 'utf8')).ts));
  return cache.get(file)!;
}

test(`the Rust instrumented run equals runPlayer's TS reference (${FULL ? 'every player-round' : `all of ${SHORT}, every ${SAMPLE_STRIDE}th elsewhere`})`, () => {
  let n = 0, total = 0;
  const bad: string[] = [];
  for (const s of readdirSync(SESSIONS).sort()) {
    const dir = join(SESSIONS, s);
    const dates = new Map<string, Date>();
    loadCases(dir).forEach((c, i) => {
      total++;
      if (!FULL && s !== SHORT && i % SAMPLE_STRIDE !== 0) return;
      n++;
      const date = dateOf(dir, c.file, dates);
      const a = JSON.stringify(runPlayerTs(c.rawPlayer, c.rawRound!, date));
      const b = JSON.stringify(runPlayerNative(c.rawPlayer, c.rawRound!, date));
      if (a !== b) bad.push(`${s} ${c.file} r${c.round} ${c.user}`);
    });
  }
  console.log(`replay-native: ${n} of ${total} player-rounds compared, ${bad.length} differ`);
  expect(bad).toEqual([]);
  expect(n).toBeGreaterThan(FULL ? 3000 : 200);       // a walk that found nothing cannot pass
}, FULL ? 3_600_000 : 600_000);

test('a rule set or date the port does not carry is refused, never approximated', () => {
  const dir = join(SESSIONS, SHORT);
  const c = loadCases(dir)[0]!;
  const p = c.rawPlayer, date = dateOf(dir, c.file, new Map());
  for (const [k, v] of [['kickset', 'SRS'], ['bagtype', '14-bag'], ['boardwidth', 12], ['b2bcharging', true], ['usebombs', true]] as const) {
    const player = { ...p, replay: { ...p.replay, options: { ...p.replay.options, [k]: v } } };
    expect(() => runPlayerNative(player, c.rawRound!, date)).toThrow(/unsupported/);
  }
  // the engine's date picks the garbage queue class and the opener phase: an earlier one is refused
  expect(() => runPlayerNative(p, c.rawRound!, new Date('2025-01-01T00:00:00Z'))).toThrow(/unsupported date era/);
  // the unchanged player is accepted, so the refusals above are about the one change each makes
  expect(() => runPlayerNative(p, c.rawRound!, date)).not.toThrow();
});

test('runPlayer is the native run unless REPLAY_NATIVE=off', () => {
  const src = readFileSync(join(import.meta.dir, 'emit-replay.ts'), 'utf8');
  expect(src).toContain("process.env.REPLAY_NATIVE === 'off' ? runPlayerTs(player, roundPlayers, date) : runPlayerNative(player, roundPlayers, date)");
});

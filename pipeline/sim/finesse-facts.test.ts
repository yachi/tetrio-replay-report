/**
 * The finesse-placements artefact (`sessions/<date>/sim/finesse-facts.json`, from `emit-finesse-facts.ts`).
 *
 *   1. byte identity — every committed artefact is what `build()` produces now.
 *   2. the anchor — per player-round, the rule's perfect-piece and fault counts against the
 *      replay's own `results.stats.finesse`, with every disagreeing player-round pinned by NAME and
 *      compared exactly. A new disagreement, or a vanished one, is a red build to investigate, never a
 *      number absorbed under a bound (the `DT_ORDER_IN_OPENER` rule).
 *   3. the empty-board table, hand-checked on placements whose finesse is standard.
 *   4. the soft-drop exemption is load-bearing: without it the anchor collapses, and exempting on PRESS
 *      (the rule before 2026-10-31) instead of TETR.IO's release flag loses agreement (two mutants).
 *
 * Run: bun test pipeline/sim/finesse-facts.test.ts   (rebuilds every session, ~25 s)
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, finesseTable, runRound } from './emit-finesse-facts.ts';
import { loadCases } from './verified-prefix.ts';
import { createEngine } from './vendor/teto/create-engine.mjs';
import { TL_DEFAULTS } from './oracle-source.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';

const SESSIONS = assertCorpusIsEverySessionOnDisk(
  `${import.meta.dir}/../../sessions`,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22', '2026-10-29', '2026-11-01']);
const sessionDir = (d: string) => `${import.meta.dir}/../../sessions/${d}`;
const artefact = (s: string) => `${sessionDir(s)}/sim/finesse-facts.json`;
const load = (s: string) => JSON.parse(readFileSync(artefact(s), 'utf8'));

/** Player-rounds where the engine's counts are not TETR.IO's, each with its reason. EMPTY since
 *  2026-10-31, kept as a named list so a new disagreement is a red build to investigate.
 *  - `admission`: the engine's whole round differs from the game's (replay.test.ts
 *    ADMISSION_EXCEPTIONS), so the board the finesse is read on is not the game's.
 *  - `unexplained`: the round is admitted and still differs.
 *  Until 2026-10-31 this list held 31 rounds under the rule that exempted a piece on whose keys softDrop
 *  was PRESSED; TETR.IO exempts the piece falling when it is RELEASED, which accounts for 17 of them.
 *  The other 14 (11 `admission`, 3 `unexplained`: 09-10-07 r3, 09-11-01 r6, 09-17-05 r0) all went
 *  the same day, when `oracle-source.ts`'s `TL_DEFAULTS.clutch` became TETR.IO's own default (true):
 *  with clutch off the engine blocked out a piece the game walked up after a line clear, so its
 *  board after that moment was not the game's. */
const ANCHOR_EXCEPTIONS: [string, 'admission' | 'unexplained'][] = [];

test('rebuilding every session reproduces its committed finesse-facts.json byte for byte', () => {
  for (const s of SESSIONS) {
    process.env.REPLAY_DIR = sessionDir(s);
    expect(serialise(build(sessionDir(s))), s).toBe(readFileSync(artefact(s), 'utf8'));
  }
}, 120_000);

test('the anchor disagrees exactly where the named list says, and nowhere else', () => {
  const got: string[] = [];
  let rounds = 0, agree = 0, unknown = 0;
  for (const s of SESSIONS) {
    const a = load(s).anchor;
    rounds += a.rounds; agree += a.agree; unknown += a.unknown;
    expect(a.agree + a.unknown + a.exceptions.length, s).toBe(a.rounds);
    for (const e of a.exceptions)
      got.push(`${e.file} r${e.round} ${e.user} perfect ${e.engine.perfect}/${e.replay.perfect} faults ${e.engine.faults}/${e.replay.faults}`);
  }
  expect(got).toEqual(ANCHOR_EXCEPTIONS.map(([k]) => k));
  expect(unknown).toBe(0);
  expect(agree).toBe(rounds - ANCHOR_EXCEPTIONS.length);
});

test('every `admission` exception is a round the replay artefact refuses, and no `unexplained` one is', () => {
  const refused = new Set<string>();
  for (const s of SESSIONS) {
    const d = JSON.parse(readFileSync(`${sessionDir(s)}/sim/replay-facts.json`, 'utf8'));
    for (const r of d.rounds) for (const p of r.players)
      if (!p.admission.ok) refused.add(`${r.file} r${r.round} ${p.user}`);
  }
  for (const [k, why] of ANCHOR_EXCEPTIONS) {
    const id = k.split(' perfect')[0]!;
    expect(refused.has(id), k).toBe(why === 'admission');
  }
});

test('every player total adds up and every ranked placement is consistent', () => {
  for (const s of SESSIONS) {
    const d = load(s);
    expect(d.report_eligible).toBe(false);
    for (const p of d.players) {
      expect(p.scored + p.not_scored.soft_drop + p.not_scored.no_empty_board_path, s).toBe(p.pieces);
      let prev = Infinity;
      for (const m of p.top) {
        expect(m.faults, s).toBeLessThanOrEqual(prev); prev = m.faults;
        expect(m.faulty).toBeGreaterThan(0);
        expect(m.faults).toBeGreaterThanOrEqual(m.faulty);
        expect(m.faulty).toBeLessThanOrEqual(m.scored);
        expect(m.optimal.length).toBeLessThanOrEqual(m.target);
        expect(m.example.keys - m.target).toBe(m.example.excess);
        expect(m.most_common_faulty.n).toBeLessThanOrEqual(m.faulty);
      }
    }
  }
});

test('the empty-board table agrees with standard finesse where it is not in doubt', () => {
  const c: any = loadCases(sessionDir('2026-10-29'))[0];
  const o = c.rawPlayer.replay.options;
  const eng: any = createEngine({ ...TL_DEFAULTS, ...o, g: o.g ?? TL_DEFAULTS.g }, o.gameid,
    c.rawRound.map((p: any) => ({ gameid: p.replay.options.gameid, userid: p.id, username: p.username })));
  const T = (s: string) => finesseTable(eng, s);
  // placements per piece: I 7 flat + 10 upright; O 9; S, Z 8 + 9; J, L, T 8 + 9 + 8 + 9
  expect([...'IOSZJLT'].map(s => T(s).size)).toEqual([17, 9, 17, 17, 34, 34, 34]);
  const O = T('O');
  const cost = (t: any) => [...t.values()].map((v: any) => v.cost).sort((a: number, b: number) => a - b);
  // O: spawn column free, one tap or one DAS anywhere else, two inputs for the columns next to the walls
  expect(cost(O)).toEqual([0, 1, 1, 1, 1, 2, 2, 2, 2]);
  for (const s of 'IOSZJLT') for (const v of T(s).values()) expect(v.path.length).toBeLessThanOrEqual(v.cost);
  // hand-checked against the standard finesse charts: spawn is free, a wall is one DAS, the I's
  // upright columns are reached by rotating next to the wall, and the T's 180 costs two
  const at = (t: any, k: string) => [t.get(k).cost, t.get(k).path.join('')];
  expect(at(T('I'), '3:0 4:0 5:0 6:0')).toEqual([0, '']);
  expect(at(T('I'), '2:0 2:1 2:2 2:3')).toEqual([2, '⇤↻']);
  expect(at(T('I'), '0:0 0:1 0:2 0:3')).toEqual([2, '↻⇤']);
  expect(at(T('O'), '1:0 1:1 2:0 2:1')).toEqual([2, '⇤→']);
  expect(at(T('T'), '3:1 4:0 4:1 5:1')).toEqual([2, '180']);
  expect(at(T('T'), '1:1 2:0 2:1 3:1')).toEqual([4, '←←180']);
});

test('MUTANT: exempting on softDrop PRESS (the rule before 2026-10-31) loses agreement', () => {
  let lost = 0;
  for (const d of ['2026-07-24', '2026-08-01']) {
    process.env.REPLAY_DIR = sessionDir(d);
    lost += load(d).anchor.agree - build(sessionDir(d), { softDropOnPress: true }).anchor.agree;
  }
  expect(lost).toBeGreaterThan(0);
}, 60_000);

test('MUTANT: scoring soft-dropped pieces breaks the anchor (the exemption is load-bearing)', () => {
  const dir = sessionDir('2026-10-29');
  process.env.REPLAY_DIR = dir;
  const mut = build(dir, { scoreSoftDrop: true });
  expect(mut.anchor.agree).toBeLessThan(load('2026-10-29').anchor.agree - 50);
}, 60_000);

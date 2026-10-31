/**
 * The finesse-placements artefact (`sessions/<date>/sim/finesse-facts.json`, from `emit-finesse-facts.ts`).
 *
 *   1. byte identity — every committed artefact is what `build()` produces now.
 *   2. the anchor — per player-round, the fitted rule's perfect-piece and fault counts against the
 *      replay's own `results.stats.finesse`, with every disagreeing player-round pinned by NAME and
 *      compared exactly. A new disagreement, or a vanished one, is a red build to investigate, never a
 *      number absorbed under a bound (the `DT_ORDER_IN_OPENER` rule).
 *   3. the empty-board table, hand-checked on placements whose finesse is standard.
 *   4. the softDrop skip is load-bearing: without it the anchor collapses (a mutant, measured).
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
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22', '2026-10-29']);
const sessionDir = (d: string) => `${import.meta.dir}/../../sessions/${d}`;
const artefact = (s: string) => `${sessionDir(s)}/sim/finesse-facts.json`;
const load = (s: string) => JSON.parse(readFileSync(artefact(s), 'utf8'));

/** Player-rounds where the fitted rule's counts are not TETR.IO's. Several are rounds where the engine
 *  locks a piece past the game's own `piecesplaced` (attack-facts.test.ts LOCKS_PAST_END) or where a
 *  softDrop near a hold moves which piece the skip lands on; none is explained piece by piece. */
const ANCHOR_EXCEPTIONS = [
  'replay-2026-07-22-9.ttrm r1 yachi perfect 76/76 faults 14/13',
  'replay-2026-07-24-2.ttrm r4 pinglamb perfect 132/133 faults 30/28',
  'replay-2026-07-28-1.ttrm r0 yachi perfect 33/33 faults 4/3',
  'replay-2026-07-28-4.ttrm r2 pinglamb perfect 113/112 faults 45/53',
  'replay-2026-07-28-7.ttrm r8 yachi perfect 77/77 faults 18/16',
  'replay-2026-08-01-4.ttrm r7 pinglamb perfect 38/37 faults 8/15',
  'replay-2026-08-01-8.ttrm r0 pinglamb perfect 181/182 faults 37/36',
  'replay-2026-08-09-1.ttrm r2 yachi perfect 93/93 faults 22/21',
  'replay-2026-08-09-4.ttrm r3 pinglamb perfect 47/48 faults 12/8',
  'replay-2026-08-09-6.ttrm r2 pinglamb perfect 128/129 faults 30/28',
  'replay-2026-08-19-1.ttrm r0 pinglamb perfect 102/103 faults 41/38',
  'replay-2026-08-19-10.ttrm r0 pinglamb perfect 95/94 faults 11/11',
  'replay-2026-08-19-5.ttrm r0 pinglamb perfect 28/28 faults 6/5',
  'replay-2026-08-19-8.ttrm r1 pinglamb perfect 100/101 faults 24/21',
  'replay-2026-08-25-03.ttrm r1 pinglamb perfect 222/223 faults 46/44',
  'replay-2026-08-25-05.ttrm r5 yachi perfect 62/64 faults 13/11',
  'replay-2026-09-03-01.ttrm r4 yachi perfect 81/82 faults 8/7',
  'replay-2026-09-10-02.ttrm r2 yachi perfect 55/54 faults 7/11',
  'replay-2026-09-10-07.ttrm r3 pinglamb perfect 44/45 faults 16/14',
  'replay-2026-09-11-01.ttrm r6 yachi perfect 82/81 faults 31/32',
  'replay-2026-09-11-07.ttrm r4 pinglamb perfect 134/135 faults 27/26',
  'replay-2026-09-17-05.ttrm r0 pinglamb perfect 98/99 faults 30/29',
  'replay-2026-09-18-03.ttrm r1 pinglamb perfect 117/116 faults 14/17',
  'replay-2026-09-18-05.ttrm r2 yachi perfect 46/47 faults 16/11',
  'replay-2026-09-18-16.ttrm r7 pinglamb perfect 62/63 faults 14/13',
  'replay-2026-10-03-13.ttrm r4 pinglamb perfect 134/135 faults 18/17',
  'replay-2026-10-09-06.ttrm r4 pinglamb perfect 61/62 faults 20/17',
  'replay-2026-10-12-08.ttrm r1 pinglamb perfect 167/168 faults 44/43',
  'replay-2026-10-22-01.ttrm r6 pinglamb perfect 100/101 faults 12/10',
  'replay-2026-10-22-09.ttrm r3 yachi perfect 107/106 faults 27/17',
  'replay-2026-10-29-02.ttrm r0 pinglamb perfect 105/104 faults 22/30',
];

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
  expect(got).toEqual(ANCHOR_EXCEPTIONS);
  expect(unknown).toBe(0);
  expect(agree).toBe(rounds - ANCHOR_EXCEPTIONS.length);
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

test('MUTANT: scoring softDrop pieces breaks the anchor (the skip is load-bearing)', () => {
  const dir = sessionDir('2026-10-29');
  process.env.REPLAY_DIR = dir;
  const mut = build(dir, { scoreSoftDrop: true });
  expect(mut.anchor.agree).toBeLessThan(load('2026-10-29').anchor.agree - 50);
}, 60_000);

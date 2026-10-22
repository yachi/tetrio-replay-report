/**
 * The attack-sources artefact (`sessions/<date>/sim/attack-facts.json`, from `emit-attack-facts.ts`).
 *
 *   1. byte identity — every committed artefact is what `build()` produces now.
 *   2. the two anchors — the engine's attack total and its clear-type counts against the replay's
 *      own counters, with every disagreeing player-round pinned as a NAMED exception list compared
 *      exactly. A new disagreement, or a vanished one, is a red build to investigate, never a
 *      number absorbed under a bound (the `DT_ORDER_IN_OPENER` rule).
 *   3. the component split sums to the engine's attack, and `classify` refuses a clear it cannot name.
 *
 * Run: bun test pipeline/sim/attack-facts.test.ts   (rebuilds every session, ~30 s)
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, split, classify } from './emit-attack-facts.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';

const SESSIONS = assertCorpusIsEverySessionOnDisk(
  `${import.meta.dir}/../../sessions`,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22']);
const sessionDir = (d: string) => `${import.meta.dir}/../../sessions/${d}`;
const artefact = (s: string) => `${sessionDir(s)}/sim/attack-facts.json`;
const load = (s: string) => JSON.parse(readFileSync(artefact(s), 'utf8'));

/* 2026-10-12 adds nothing to any of the three lists: its 110 player-rounds agree on the attack
 * total and on every clear-type count, and no engine run locks past the game's `piecesplaced`.
 * 2026-10-20 adds nothing either: all 60 of its player-rounds agree on both anchors, and no
 * engine run locks past the game's `piecesplaced`.
 * 2026-10-22 adds two player-rounds to all three lists, both late divergences named in
 * replay.test.ts's ADMISSION_EXCEPTIONS: 01 r6 pinglamb is 08-09-4's shape (one Double missed at
 * the end, one lock past the game's count); 09 r3 yachi is the first entry missing more than one
 * clear (three Singles and a Triple, five locks past the game's 118), past a prefix verified to 107. */
/** Player-rounds where the engine's attack total is not the replay's. Each but 2026-10-22-09 r3 is
 *  the engine missing one Double the game credited at the very end of the round (each is also in
 *  COUNT_EXCEPTIONS). */
const ATTACK_EXCEPTIONS = [
  'replay-2026-08-09-4.ttrm r3 pinglamb engine 33 replay 34',
  'replay-2026-09-18-05.ttrm r2 yachi engine 22 replay 23',
  'replay-2026-10-22-01.ttrm r6 pinglamb engine 91 replay 92',
  'replay-2026-10-22-09.ttrm r3 yachi engine 65 replay 67',
];
/** Player-rounds where some clear-type count disagrees with the replay's counter, off by one each. */
const COUNT_EXCEPTIONS = [
  'replay-2026-08-09-4.ttrm r3 pinglamb {"D":[1,2]}',
  'replay-2026-08-19-10.ttrm r0 pinglamb {"S":[8,7]}',
  'replay-2026-08-25-05.ttrm r5 yachi {"S":[8,9]}',
  'replay-2026-09-18-05.ttrm r2 yachi {"D":[2,3]}',
  'replay-2026-10-09-07.ttrm r1 pinglamb {"S":[9,10]}',
  'replay-2026-10-22-01.ttrm r6 pinglamb {"D":[1,2]}',
  'replay-2026-10-22-09.ttrm r3 yachi {"S":[9,12],"T":[1,2]}',
];
/** Player-rounds where the engine locks pieces past the game's own `piecesplaced`. */
const LOCKS_PAST_END = [
  'replay-2026-07-22-9.ttrm r1 yachi 89/88',
  'replay-2026-07-28-1.ttrm r0 yachi 37/36',
  'replay-2026-07-28-7.ttrm r8 yachi 87/86',
  'replay-2026-08-09-4.ttrm r3 pinglamb 58/54',
  'replay-2026-08-19-10.ttrm r0 pinglamb 103/102',
  'replay-2026-08-19-5.ttrm r0 pinglamb 33/32',
  'replay-2026-09-18-05.ttrm r2 yachi 52/50',
  'replay-2026-10-09-06.ttrm r4 pinglamb 72/70',
  'replay-2026-10-22-01.ttrm r6 pinglamb 108/107',
  'replay-2026-10-22-09.ttrm r3 yachi 123/118',
];

test('rebuilding every session reproduces its committed attack-facts.json byte for byte', () => {
  for (const s of SESSIONS) {
    process.env.REPLAY_DIR = sessionDir(s);
    expect(serialise(build(sessionDir(s))), s).toBe(readFileSync(artefact(s), 'utf8'));
  }
}, 120_000);

test('the anchors disagree exactly where the named lists say, and nowhere else', () => {
  const att: string[] = [], cnt: string[] = [], past: string[] = [];
  let rounds = 0, unknown = 0;
  for (const s of SESSIONS) {
    const a = load(s).anchor;
    rounds += a.attack.rounds; unknown += a.counts.unknown;
    expect(a.counts.rounds).toBe(a.attack.rounds);
    expect(a.attack.agree + a.attack.exceptions.length).toBe(a.attack.rounds);
    expect(a.counts.agree + a.counts.exceptions.length + a.counts.unknown).toBe(a.counts.rounds);
    for (const e of a.attack.exceptions) att.push(`${e.file} r${e.round} ${e.user} engine ${e.engine} replay ${e.replay}`);
    for (const e of a.counts.exceptions) cnt.push(`${e.file} r${e.round} ${e.user} ${JSON.stringify(e.engine_vs_replay)}`);
    for (const e of a.engine_locks_past_game_end) past.push(`${e.file} r${e.round} ${e.user} ${e.locks}/${e.pieces}`);
  }
  expect(rounds).toBeGreaterThan(0);
  expect(unknown).toBe(0);
  expect(att.sort()).toEqual([...ATTACK_EXCEPTIONS].sort());
  expect(cnt.sort()).toEqual([...COUNT_EXCEPTIONS].sort());
  expect(past.sort()).toEqual([...LOCKS_PAST_END].sort());
});

test('per player, the windows add up: pieces exactly, engine attack within the named exceptions', () => {
  for (const s of SESSIONS) {
    const d = load(s);
    for (const p of d.players) {
      const { opener, mid } = p.windows;
      expect(opener.pieces + mid.pieces, `${s} ${p.user}`).toBe(p.pieces);
      const off = d.anchor.attack.exceptions.filter((e: any) => e.user === p.user)
        .reduce((a: number, e: any) => a + e.replay - e.engine, 0);
      expect(opener.attack + mid.attack + off, `${s} ${p.user}`).toBe(p.attack);
      for (const w of [opener, mid]) {
        const parts = Object.values(w.components as Record<string, number>).reduce((a, b) => a + b, 0);
        expect(parts, `${s} ${p.user} components`).toBe(w.attack);
        const byClass = Object.values(w.classes as Record<string, { attack: number }>).reduce((a, c) => a + c.attack, 0);
        expect(byClass, `${s} ${p.user} classes`).toBe(w.attack);
      }
    }
  }
});

test('split(): the five parts always sum to the engine value, residual absorbs what the model misses', () => {
  // TSD at b2b 3, combo 2: base 4, b2b level 2, (4+2)*1.5 = 9 -> combo +3
  expect(split('TSD', 2, 3, 2, 9, 0)).toEqual({ base: 4, b2b: 2, combo: 3, allclear: 0, residual: 0 });
  // the same clear when the engine sent one more (fractional b2b level surviving the multiplier)
  expect(split('TSD', 2, 3, 2, 10, 0).residual).toBe(1);
  // a comboing single: base 0, log1p(4*1.25) = 1.79 -> 1
  expect(split('S', 1, 0, 4, 1, 0)).toEqual({ base: 0, b2b: 0, combo: 1, allclear: 0, residual: 0 });
  // a Perfect Clear on a double: its 10 is its own part, never folded into base
  expect(split('D', 2, 0, 0, 11, 10)).toEqual({ base: 1, b2b: 0, combo: 0, allclear: 10, residual: 0 });
  // a quad breaks nothing and carries b2b; a plain double never does
  expect(split('Q', 4, 1, 0, 5, 0).b2b).toBe(1);
  expect(split('D', 2, 5, 0, 1, 0).b2b).toBe(0);
});

test('classify(): every class in this corpus, and a throw for anything else', () => {
  expect(classify(2, 'normal')).toBe('TSD');
  expect(classify(3, 'normal')).toBe('TST');
  expect(classify(1, 'mini')).toBe('mTSS');
  expect(classify(4, 'none')).toBe('Q');
  expect(() => classify(5, 'none')).toThrow();
  expect(() => classify(3, 'mini')).toThrow();
});

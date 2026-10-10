/**
 * The replay timeline artefact (`sessions/<date>/sim/replay-facts.json`, from `emit-replay.ts`).
 *
 * What is checked, and what each check rules out:
 *
 *   1. byte identity — every committed artefact is what `build()` produces now. `build()` itself
 *      throws unless the emitted timeline, decoded from an empty board, IS the engine's board after
 *      every lock, so a green rebuild is also the round trip over every player-round of the corpus.
 *   2. determinism — two builds of one session are the same bytes (no wall clock, no Math.random).
 *   3. the round trip has teeth — a planted garbage column, hold flag or placement makes
 *      `assertRoundTrip` throw. A round-trip assertion nothing can fail is a comment.
 *   4. admission — the engine's whole-round totals against facts.json, pinned per session as
 *      literals, and the disagreeing player-rounds as a NAMED exception list compared exactly, so a
 *      new disagreement (or a vanished one) is a red build to investigate, never a number absorbed.
 *   5. engine_knockout — the engine board topping out vs the game ending the player, derived from
 *      both inputs and its disagreements pinned as a named list, so a viewer can flag them.
 *
 * Run: bun test pipeline/sim/replay.test.ts   (rebuilds all fifteen sessions, about a minute)
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, runPlayer, assertRoundTrip, decodeTimeline, queueStates, SHAPES,
         KNOCKOUT_ENDINGS, SURVIVAL_ENDINGS,
         encodePlace, placeCells, WIDTH, ROWS, type Lock } from './emit-replay.ts';
import { loadCases } from './verified-prefix.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';

const SESSIONS = assertCorpusIsEverySessionOnDisk(
  `${import.meta.dir}/../../sessions`,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09']);
const sessionDir = (d: string) => `${import.meta.dir}/../../sessions/${d}`;
const artefact = (s: string) => `${sessionDir(s)}/sim/replay-facts.json`;

test('rebuilding every session reproduces its committed replay-facts.json byte for byte', () => {
  for (const s of SESSIONS) {
    process.env.REPLAY_DIR = sessionDir(s);
    expect(serialise(build(sessionDir(s)))).toBe(readFileSync(artefact(s), 'utf8'));
  }
}, 600_000);

test('build is deterministic', () => {
  const s = '2026-07-24';
  expect(serialise(build(sessionDir(s)))).toBe(serialise(build(sessionDir(s))));
}, 120_000);

test('the shape table holds every orientation exactly once, and placement round-trips', () => {
  expect(Object.fromEntries(Object.entries(SHAPES).map(([k, v]) => [k, v.length])))
    .toEqual({ I: 2, O: 1, T: 4, S: 2, Z: 2, J: 4, L: 4 });
  for (const [piece, shapes] of Object.entries(SHAPES)) shapes.forEach((sh, k) => {
    const cells = sh.map(([dx, dy]) => (3 + dy) * WIDTH + 2 + dx).sort((a, b) => a - b);
    const place = encodePlace(piece, cells);
    expect(place).toBe(k * WIDTH * ROWS + 3 * WIDTH + 2);
    expect(placeCells(piece, place).sort((a, b) => a - b)).toEqual(cells);
  });
  // a clipped piece travels as its explicit cells
  expect(encodePlace('T', [395, 396])).toEqual([395, 396]);
  // a J drawn as an L is not a J
  expect(() => encodePlace('J', SHAPES.L![0]!.map(([dx, dy]) => dy * WIDTH + dx))).toThrow();
});

/* ── the round trip has teeth ─────────────────────────────────────────────────────────────────── */
test('assertRoundTrip fails on a planted garbage column, hold flag, placement and line count', () => {
  const dir = sessionDir('2026-07-24');
  const c = loadCases(dir).find(k => k.file === 'replay-2026-07-24-1.ttrm' && k.round === 0)!;
  const ts = JSON.parse(readFileSync(`${dir}/${c.file}`, 'utf8')).ts;
  const run = runPlayer(c.rawPlayer, c.rawRound!, new Date(ts));
  expect(() => assertRoundTrip('control', run.seq, run)).not.toThrow();

  const mutate = (f: (locks: Lock[]) => void) => {
    const locks = JSON.parse(JSON.stringify(run.locks)) as Lock[];
    f(locks);
    return () => assertRoundTrip('mutant', run.seq, { ...run, locks });
  };
  const gi = run.locks.findIndex(lk => lk[4].length > 0);
  expect(gi).toBeGreaterThan(-1);
  expect(mutate(l => { l[gi]![4][0]![0] = (l[gi]![4][0]![0] + 1) % WIDTH; })).toThrow();
  const hi = run.locks.findIndex(lk => lk[5] === 1);
  expect(mutate(l => { l[hi]![5] = 0; })).toThrow();
  const pi = run.locks.findIndex(lk => typeof lk[1] === 'number' && lk[2] === 0);
  expect(mutate(l => { (l[pi]![1] as number) += 1; })).toThrow();
  const ci = run.locks.findIndex(lk => lk[2] > 0);
  expect(mutate(l => { l[ci]![2] -= 1; })).toThrow();
}, 60_000);

test('the committed artefacts decode, and the viewer-side derivations hold on every round', () => {
  for (const s of SESSIONS) {
    const d = JSON.parse(readFileSync(artefact(s), 'utf8'));
    expect(d.report_eligible).toBe(false);
    expect(d.session).toBe(s);
    for (const r of d.rounds) for (const p of r.players) {
      const q = queueStates(r.seq, p.locks);
      expect(q.length).toBe(p.locks.length);
      decodeTimeline(r.seq, p.locks);   // throws on a line count the board does not reproduce
      const n = p.locks.length;
      expect(p.prefix.verified_to).toBeGreaterThanOrEqual(-1);
      expect(p.prefix.verified_to).toBeLessThan(n);
      if (p.prefix.after === 'check_failed') {
        expect(p.prefix.failed_at).toBeGreaterThan(p.prefix.verified_to);
        expect(p.prefix.failed_at).toBeLessThan(n);
      } else expect(p.prefix.failed_at).toBeNull();
      if (p.prefix.after === 'end') expect(p.prefix.verified_to).toBe(n - 1);
      expect(typeof p.ending).toBe('string');
    }
  }
}, 120_000);

/* ── admission ────────────────────────────────────────────────────────────────────────────────── */
/** Player-rounds agreeing with facts.json on pieces, lines, holds, garbage cleared, attack, all
 *  clears and every T-spin clear kind, per session, as literals. Measured 2026-10-04 with `emit-replay.ts`. */
const ADMISSION: Record<string, [number, number]> = {
  '2026-07-22': [157, 158], '2026-07-24': [100, 100], '2026-07-28': [126, 128],
  '2026-08-01': [106, 106], '2026-08-09': [99, 100], '2026-08-14': [168, 168],
  '2026-08-19': [138, 140], '2026-08-25': [145, 146], '2026-09-03': [92, 92],
  '2026-09-10': [130, 130], '2026-09-11': [102, 102], '2026-09-17': [98, 98],
  '2026-09-18': [253, 254], '2026-09-19': [300, 300], '2026-10-03': [292, 292],
  '2026-10-09': [202, 204],
};

/** Every player-round whose engine totals disagree with facts.json, with the disagreement. Mostly
 *  the round's LOSER placing one extra piece at the instant the game ended it; two are real late
 *  divergences (08-09-4 r3 pinglamb, 09-18-05 r2 yachi) that a viewer must flag for their last
 *  seconds. Named rather than bounded: a ninth must be investigated, not absorbed.
 *
 *  2026-10-09 adds the NINTH and TENTH, both pinglamb, both the round's loser by `garbagesmash`,
 *  and both past the end of the verified prefix — so neither touches a lock a viewer is shown as
 *  verified:
 *    replay-2026-10-09-06.ttrm r4 — the engine places 72 pieces against the game's 70, every other
 *      total agreeing. The loser-places-extra shape, but TWO pieces rather than one: the engine's
 *      board tops out at lock 68 (engine_knockout agrees with the ending) and the prefix verifies to
 *      lock 64 of 72, so the two extra locks sit in the unverified tail after the engine's own
 *      death — the end of the round, not a divergence a viewer could mistake for play.
 *    replay-2026-10-09-07.ttrm r1 — pieces agree (98) and the engine clears 47 lines against the
 *      game's 48. A real late divergence, the third after the two above: prefix verified to lock 93
 *      of 98, engine knock-out at lock 95, so the missing clear lies in the last five locks, beyond
 *      the verified boundary the viewer already draws. An eleventh must be investigated the same
 *  way. */
const ADMISSION_EXCEPTIONS = [
  { session: '2026-07-22', file: 'replay-2026-07-22-9.ttrm', round: 1, user: 'yachi', diff: { pieces: [89, 88] } },
  { session: '2026-07-28', file: 'replay-2026-07-28-1.ttrm', round: 0, user: 'yachi', diff: { pieces: [37, 36] } },
  { session: '2026-07-28', file: 'replay-2026-07-28-7.ttrm', round: 8, user: 'yachi', diff: { pieces: [87, 86] } },
  { session: '2026-08-09', file: 'replay-2026-08-09-4.ttrm', round: 3, user: 'pinglamb',
    diff: { pieces: [58, 54], lines: [20, 22], garbage_attack: [33, 34] } },
  { session: '2026-08-19', file: 'replay-2026-08-19-5.ttrm', round: 0, user: 'pinglamb', diff: { pieces: [33, 32] } },
  { session: '2026-08-19', file: 'replay-2026-08-19-10.ttrm', round: 0, user: 'pinglamb',
    diff: { pieces: [103, 102], lines: [46, 45], garbage_cleared: [8, 7] } },
  { session: '2026-08-25', file: 'replay-2026-08-25-05.ttrm', round: 5, user: 'yachi', diff: { lines: [37, 38] } },
  { session: '2026-09-18', file: 'replay-2026-09-18-05.ttrm', round: 2, user: 'yachi',
    diff: { pieces: [52, 50], lines: [23, 25], holds: [22, 21], garbage_cleared: [6, 8],
            garbage_attack: [22, 23] } },
  { session: '2026-10-09', file: 'replay-2026-10-09-06.ttrm', round: 4, user: 'pinglamb', diff: { pieces: [72, 70] } },
  { session: '2026-10-09', file: 'replay-2026-10-09-07.ttrm', round: 1, user: 'pinglamb', diff: { lines: [47, 48] } },
];

test('admission counts are pinned per session, and the exceptions are exactly the named list', () => {
  const found: typeof ADMISSION_EXCEPTIONS = [];
  for (const s of SESSIONS) {
    const d = JSON.parse(readFileSync(artefact(s), 'utf8'));
    const prs = d.rounds.flatMap((r: any) => r.players);
    expect([prs.filter((p: any) => p.admission.ok).length, prs.length]).toEqual(ADMISSION[s]!);
    for (const r of d.rounds) for (const p of r.players)
      if (!p.admission.ok) found.push({ session: s, file: r.file, round: r.round, user: p.user, diff: p.admission.diff });
  }
  expect(found).toEqual(ADMISSION_EXCEPTIONS);
});

/* ── engine knock-out vs the game's ending ────────────────────────────────────────────────────── */
/** Every player-round where the ENGINE's board topping out disagrees with the game ending the
 *  player (gameoverreason topout/garbagesmash). The ending a viewer shows is always gameoverreason;
 *  these are the rounds where it must also flag that the simulated board may differ from the real
 *  one. 22 are `topout` deaths the engine's board survives; one (10-03-01 r1 pinglamb) is the round's
 *  WINNER, whose engine board tops out at lock 52 of 59. Named rather than bounded, exactly like
 *  ADMISSION_EXCEPTIONS: a new one, or one vanishing, is a red build to investigate.
 *
 *  2026-10-09 adds two more of the common class, making 24 `topout` deaths the engine survives:
 *  replay-2026-10-09-08.ttrm r0 pinglamb (34 locks, prefix verified to 26) and
 *  replay-2026-10-09-11.ttrm r4 yachi (171 locks, prefix verified to 162). Both admit cleanly —
 *  every total agrees with facts.json — so the engine placed exactly the game's pieces and its
 *  board simply did not top out on the last one; both last locks are past the verified prefix,
 *  where the engine's garbage-hole columns (seeded RNG, never observed) are free to differ. */
const KNOCKOUT_EXCEPTIONS = [
  { session: '2026-07-22', file: 'replay-2026-07-22-2.ttrm', round: 1, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-07-22', file: 'replay-2026-07-22-7.ttrm', round: 5, user: 'pinglamb', ending: 'topout', lock: null },
  { session: '2026-07-24', file: 'replay-2026-07-24-5.ttrm', round: 2, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-07-24', file: 'replay-2026-07-24-6.ttrm', round: 1, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-08-09', file: 'replay-2026-08-09-6.ttrm', round: 2, user: 'pinglamb', ending: 'topout', lock: null },
  { session: '2026-08-14', file: 'replay-2026-08-14-2.ttrm', round: 4, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-08-19', file: 'replay-2026-08-19-2.ttrm', round: 1, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-08-19', file: 'replay-2026-08-19-9.ttrm', round: 1, user: 'pinglamb', ending: 'topout', lock: null },
  { session: '2026-08-19', file: 'replay-2026-08-19-9.ttrm', round: 8, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-08-25', file: 'replay-2026-08-25-09.ttrm', round: 5, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-09-10', file: 'replay-2026-09-10-04.ttrm', round: 2, user: 'pinglamb', ending: 'topout', lock: null },
  { session: '2026-09-11', file: 'replay-2026-09-11-04.ttrm', round: 4, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-09-18', file: 'replay-2026-09-18-08.ttrm', round: 5, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-09-18', file: 'replay-2026-09-18-12.ttrm', round: 7, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-09-19', file: 'replay-2026-09-19-03.ttrm', round: 2, user: 'pinglamb', ending: 'topout', lock: null },
  { session: '2026-09-19', file: 'replay-2026-09-19-05.ttrm', round: 6, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-09-19', file: 'replay-2026-09-19-06.ttrm', round: 2, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-09-19', file: 'replay-2026-09-19-14.ttrm', round: 6, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-09-19', file: 'replay-2026-09-19-17.ttrm', round: 0, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-09-19', file: 'replay-2026-09-19-20.ttrm', round: 3, user: 'pinglamb', ending: 'topout', lock: null },
  { session: '2026-10-03', file: 'replay-2026-10-03-01.ttrm', round: 1, user: 'pinglamb', ending: 'winner', lock: 52 },
  { session: '2026-10-03', file: 'replay-2026-10-03-02.ttrm', round: 4, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-10-03', file: 'replay-2026-10-03-10.ttrm', round: 8, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-10-09', file: 'replay-2026-10-09-08.ttrm', round: 0, user: 'pinglamb', ending: 'topout', lock: null },
  { session: '2026-10-09', file: 'replay-2026-10-09-11.ttrm', round: 4, user: 'yachi', ending: 'topout', lock: null },
];

test('engine_knockout is consistent with its own definition, and its disagreements are exactly the named list', () => {
  const found: typeof KNOCKOUT_EXCEPTIONS = [];
  for (const s of SESSIONS) {
    const d = JSON.parse(readFileSync(artefact(s), 'utf8'));
    for (const r of d.rounds) for (const p of r.players) {
      const k = p.engine_knockout;
      expect(typeof k.agrees).toBe('boolean');           // required, never defaulted
      if (k.lock !== null) {
        expect(Number.isInteger(k.lock)).toBe(true);
        expect(k.lock).toBeGreaterThanOrEqual(0);
        expect(k.lock).toBeLessThan(p.locks.length);
      }
      const dead = KNOCKOUT_ENDINGS.has(p.ending);
      expect(dead || SURVIVAL_ENDINGS.has(p.ending)).toBe(true);
      // the flag is DERIVED from the two inputs it records; a hand-edited artefact cannot set it freely
      expect(k.agrees).toBe((k.lock !== null) === dead);
      if (!k.agrees) found.push({ session: s, file: r.file, round: r.round, user: p.user, ending: p.ending, lock: k.lock });
    }
  }
  expect(found).toEqual(KNOCKOUT_EXCEPTIONS);
});

test('engineTopLock has teeth: the engine records a topout on a round the game ended by topout', () => {
  // control for the hook itself: a round the list does NOT name, ended by topout, must yield a lock
  const dir = sessionDir('2026-07-24');
  const d = JSON.parse(readFileSync(artefact('2026-07-24'), 'utf8'));
  const r = d.rounds.find((r: any) => r.players.some((p: any) => p.ending === 'topout' && p.engine_knockout.agrees));
  const p = r.players.find((p: any) => p.ending === 'topout' && p.engine_knockout.agrees);
  const c = loadCases(dir).find(k => k.file === r.file && k.round === r.round && k.user === p.user)!;
  const ts = JSON.parse(readFileSync(`${dir}/${c.file}`, 'utf8')).ts;
  const run = runPlayer(c.rawPlayer, c.rawRound!, new Date(ts));
  expect(run.engineTopLock).not.toBeNull();
  expect(run.engineTopLock).toBe(p.engine_knockout.lock);
}, 60_000);

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
 * Run: bun test pipeline/sim/replay.test.ts   (rebuilds every session, a few minutes)
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, runPlayer, assertRoundTrip, decodeTimeline, queueStates, SHAPES,
         KNOCKOUT_ENDINGS, SURVIVAL_ENDINGS,
         encodePlace, placeCells, WIDTH, ROWS, type Lock } from './emit-replay.ts';
import { loadCases } from './verified-prefix.ts';
import { withOracleCache } from './oracle-cache.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';

const SESSIONS = assertCorpusIsEverySessionOnDisk(
  `${import.meta.dir}/../../sessions`,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22', '2026-10-29', '2026-11-01']);
const sessionDir = (d: string) => `${import.meta.dir}/../../sessions/${d}`;
const artefact = (s: string) => `${sessionDir(s)}/sim/replay-facts.json`;

test('rebuilding every session reproduces its committed replay-facts.json byte for byte', () => {
  for (const s of SESSIONS) {
    process.env.REPLAY_DIR = sessionDir(s);
    expect(serialise(build(sessionDir(s)))).toBe(readFileSync(artefact(s), 'utf8'));
  }
}, 600_000);

test('build is deterministic', () => {
  // with the oracle cache OFF, so both builds run the oracle afresh: through the cache the second
  // build's oracle half would be a decode of the first's, and the test would compare it to itself
  const s = '2026-07-24';
  withOracleCache(false, () => {
    expect(serialise(build(sessionDir(s)))).toBe(serialise(build(sessionDir(s))));
  });
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
 *  clears and every T-spin clear kind, per session, as literals. Measured 2026-10-04 with `emit-replay.ts`;
 *  every round admits since 2026-10-31, when `TL_DEFAULTS.clutch` became TETR.IO's own default (true). */
const ADMISSION: Record<string, [number, number]> = {
  '2026-07-22': [158, 158], '2026-07-24': [100, 100], '2026-07-28': [128, 128],
  '2026-08-01': [106, 106], '2026-08-09': [100, 100], '2026-08-14': [168, 168],
  '2026-08-19': [140, 140], '2026-08-25': [146, 146], '2026-09-03': [92, 92],
  '2026-09-10': [130, 130], '2026-09-11': [102, 102], '2026-09-17': [98, 98],
  '2026-09-18': [254, 254], '2026-09-19': [300, 300], '2026-10-03': [292, 292],
  '2026-10-09': [204, 204], '2026-10-12': [110, 110], '2026-10-20': [60, 60],
  '2026-10-22': [126, 126], '2026-10-29': [136, 136], '2026-11-01': [260, 260],
};

/** Every player-round whose engine totals disagree with facts.json. EMPTY since 2026-10-31, and kept
 *  as a named list so a new one is a red build to investigate, not a number absorbed.
 *
 *  It held twelve until then (the per-entry write-ups are in git history, at this comment): mostly
 *  the round's LOSER placing one or two extra pieces at the instant the game ended it, and five
 *  「late divergences」 (08-09-4 r3, 08-19-10 r0, 09-18-05 r2, 10-09-07 r1, 10-22-01 r6, 10-22-09 r3
 *  among them) where the engine lost or gained clears near the end. All twelve had ONE cause:
 *  `oracle-source.ts`'s `TL_DEFAULTS` set `clutch: false`, while TETR.IO's own options list
 *  (tetr.io/js/tetrio.js, 2026-10-23 build, read 2026-10-31) defaults it to true. With clutch off the
 *  engine blocked out a piece the game walks up over the stack after a line clear, so the engine's
 *  round ended (or diverged) where the game's went on. With it on, every one of the 2950
 *  player-rounds admits. */
const ADMISSION_EXCEPTIONS: { session: string; file: string; round: number; user: string; diff: unknown }[] = [];

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
 *  one. Every entry is a `topout` death the engine's board survives (32 since 2026-11-01). Until
 *  2026-10-31 two more were the round's WINNER, whose engine board topped out mid-round (10-03-01 r1
 *  pinglamb at lock 52, 10-29-04 r4 yachi at lock 30): in both a T cleared one row with the stack past
 *  the 20 visible rows, so the next piece spawned overlapping it. TETR.IO clutches that piece (walks it
 *  up until it fits, because the last lock cleared a line) and our engine, with `clutch: false` in
 *  `TL_DEFAULTS`, blocked it out. With TETR.IO's default (true) both vanish. Named rather than bounded, exactly like
 *  ADMISSION_EXCEPTIONS: a new one, or one vanishing, is a red build to investigate.
 *
 *  2026-10-09 adds two more of the common class, making 24 `topout` deaths the engine survives:
 *  replay-2026-10-09-08.ttrm r0 pinglamb (34 locks, prefix verified to 26) and
 *  replay-2026-10-09-11.ttrm r4 yachi (171 locks, prefix verified to 162). Both admit cleanly —
 *  every total agrees with facts.json — so the engine placed exactly the game's pieces and its
 *  board simply did not top out on the last one; both last locks are past the verified prefix,
 *  where the engine's garbage-hole columns (seeded RNG, never observed) are free to differ.
 *
 *  2026-10-12 adds one more of the common class, making 25 `topout` deaths the engine survives:
 *  replay-2026-10-12-02.ttrm r0 pinglamb (37 locks, prefix verified to lock 32, `no_evidence`
 *  after it). It admits cleanly — 10-12 admits 110 of 110 — so the engine placed exactly the
 *  game's pieces and its board did not top out on the last one; the last four locks are past the
 *  verified prefix, the same unobserved-garbage-hole tail as every other entry of this class.
 *
 *  2026-10-20 adds none: `engine_knockout.agrees` is true for all 60 of its player-rounds.
 *
 *  2026-10-22 adds one more of the common class, making 26 `topout` deaths the engine survives:
 *  replay-2026-10-22-02.ttrm r7 yachi (82 locks, prefix verified to lock 80, `no_evidence` after
 *  it). It admits cleanly, so the engine placed exactly the game's pieces and its board did not
 *  top out on the last one; the last two locks are past the verified prefix.
 *
 *  2026-10-29 added THREE. Two are the common class, making 28 `topout` deaths the engine survives,
 *  both pinglamb's in replay-2026-10-29-01.ttrm: r0 (98 locks, prefix verified to lock 14,
 *  `check_failed` at 19, so the last 83 locks are past the prefix) and r4 (69 locks, verified to
 *  lock 62, `no_evidence` after it). Both admit cleanly (10-29 admits 136 of 136), so the engine
 *  placed exactly the game's pieces and its board did not top out on the last one.
 *  The third was
 *  10-29-04 r4 yachi, the second winner-class entry, which 2026-10-31's clutch fix removed (above).
 *
 *  2026-11-01 adds FOUR, all of the common class, making 32 `topout` deaths the engine survives:
 *  replay-2026-11-01-01.ttrm r3 yachi (64 locks, prefix verified to lock 54),
 *  replay-2026-11-01-06.ttrm r4 yachi (88 locks, verified to lock 78),
 *  replay-2026-11-01-13.ttrm r5 pinglamb (54 locks, verified to lock 46) and
 *  replay-2026-11-01-16.ttrm r2 pinglamb (64 locks, verified to lock 54), each `no_evidence` after
 *  its prefix. All four admit cleanly (11-01 admits 260 of 260), so the engine placed exactly the
 *  game's pieces and its board did not top out on the last one; the last locks of each are past
 *  the verified prefix, the unobserved-garbage-hole tail of every other entry. No winner-class entry. */
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
  { session: '2026-10-03', file: 'replay-2026-10-03-02.ttrm', round: 4, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-10-03', file: 'replay-2026-10-03-10.ttrm', round: 8, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-10-09', file: 'replay-2026-10-09-08.ttrm', round: 0, user: 'pinglamb', ending: 'topout', lock: null },
  { session: '2026-10-09', file: 'replay-2026-10-09-11.ttrm', round: 4, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-10-12', file: 'replay-2026-10-12-02.ttrm', round: 0, user: 'pinglamb', ending: 'topout', lock: null },
  { session: '2026-10-22', file: 'replay-2026-10-22-02.ttrm', round: 7, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-10-29', file: 'replay-2026-10-29-01.ttrm', round: 0, user: 'pinglamb', ending: 'topout', lock: null },
  { session: '2026-10-29', file: 'replay-2026-10-29-01.ttrm', round: 4, user: 'pinglamb', ending: 'topout', lock: null },
  { session: '2026-11-01', file: 'replay-2026-11-01-01.ttrm', round: 3, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-11-01', file: 'replay-2026-11-01-06.ttrm', round: 4, user: 'yachi', ending: 'topout', lock: null },
  { session: '2026-11-01', file: 'replay-2026-11-01-13.ttrm', round: 5, user: 'pinglamb', ending: 'topout', lock: null },
  { session: '2026-11-01', file: 'replay-2026-11-01-16.ttrm', round: 2, user: 'pinglamb', ending: 'topout', lock: null },
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

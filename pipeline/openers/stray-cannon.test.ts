/**
 * The 迷走砲 route artefact (`analysis/stray-cannon-facts.json`, from `pipeline/sim/emit-stray-cannon-facts.ts`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. `matched_at_6` per (session, player) equals `opener-facts.json`'s Stray Cannon `exact`. It
 *      compares the FLAG, never a node count: a round can match the 6-lock field and still be
 *      `bag1.z_right` (Z placed 7th on the right), which is most of them.
 *   3. NAMED lists, not bounds: every entry is a real round, resolved by (file, 0-based round) in that
 *      session's replay-facts.json with its match POSITION, and checked per (session, player).
 *   4. mutants: each rule turned off must turn this file red.
 *
 * COST, accepted explicitly: this rebuilds all sixteen sessions through `runCaseOracle` a second
 * time in the `typescript` job (`openers.test.ts` already does once), about a minute. A shared cache
 * across test files would couple them. The mutants reuse ONE digest of the corpus, so they are free.
 *
 * Run: bun test pipeline/openers/stray-cannon.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, digestSession, corpus, ARTEFACT_PATH, type RoundDigest, type Mutants }
  from '../sim/emit-stray-cannon-facts.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22']);

/** Bag 1 matched the 6-lock field, the lock-7 piece was NOT the (mirror-aware) bag-1 Z: a hold. */
const Z_HOLD_BAG1 = [
  '2026-08-19 m8r5 pinglamb',   // 7th J
  '2026-08-25 m1r6 pinglamb',   // 7th I
  '2026-10-03 m5r5 yachi',      // 7th O
  // 2026-10-12: two more, both yachi's, both read off their cases (lock-7 piece against the
  // mirror-aware bag-1 Z) — prefixes 48 and 72, so neither is a prefix-edge reading.
  '2026-10-12 m2r1 yachi',      // mirrored: its bag-1 Z is S, and the 7th is O
  '2026-10-12 m6r5 yachi',      // 7th J
];
/** The 6-lock field matched and the 7th piece WAS the bag-1 Z, placed somewhere off the page. */
const Z_PLACED_ELSEWHERE_BAG1 = [
  '2026-07-22 m2r1 yachi',      // mirrored: its bag-1 Z is S, and the 7th is S
  '2026-08-19 m10r7 yachi',
  '2026-10-03 m2r3 pinglamb',
];
const Z_LEFT_BAG1 = [
  '2026-07-24 m4r1 yachi', '2026-07-28 m4r5 pinglamb', '2026-08-25 m2r3 yachi', '2026-09-19 m4r4 pinglamb',
  '2026-10-22 m1r7 yachi',      // matched z_left at 7 and the 6-lock field; prefix 102, no bag 2
];
const I_EARLY_CASES = ['2026-09-11 m7r2 yachi (mirrored)'];
const TST_DONATE_CASES = [
  '2026-07-24 m1r2 pinglamb', '2026-07-24 m3r5 pinglamb', '2026-08-09 m2r1 pinglamb',
  '2026-08-19 m3r4 pinglamb', '2026-09-18 m10r4 pinglamb', '2026-09-19 m13r2 pinglamb',
  '2026-10-22 m9r4 pinglamb',   // 2.normal_OS at lock 12, the TST donate at 19, prefix 140
];
/** 8-line PCs that are not on the page, named with the node they stop under. */
const PC_OFF_PAGE = [
  '2026-09-10 m7r7 pinglamb under 2.ideal.other',
  '2026-09-17 m1r9 pinglamb under 2.ideal.other',
  '2026-09-18 m3r4 pinglamb under 2.ideal.other',
  '2026-09-18 m13r3 pinglamb under 2.ideal.other',
  '2026-09-18 m13r7 pinglamb under 2.ideal.other',
  '2026-10-03 m18r4 yachi under bag1.z_right.other',   // no bag-2 page match: why PC detection is not gated on bag 2
  '2026-10-09 m4r6 pinglamb under 2.ideal.other',
  '2026-10-22 m2r5 pinglamb under bag1.z_right.other',  // a PC on lock 19 with no TST before it, prefix 105
];
/** A PC that matches patterns of two branches by colour; its own bag-2 branch decides. */
const MULTI_COLOUR_RESOLVED_BY_BRANCH = ['2026-09-17 m4r2 pinglamb'];
/** Measured empty. A first entry is a red build to investigate, never a number to absorb. */
const BAG2_HANDEDNESS_MISMATCH: string[] = [];
const COLOUR_DISAGREE: string[] = [];
const PC_GARBAGE_IN_WINDOW: string[] = [];

/** Page condition (in the handedness the page draws) against the branch actually built, first
 *  measured once the J<->L / S<->Z swap was implemented. Pinned here and nowhere in prose. */
// 2026-10-12 adds the table's first `2.normal_SO` build under a `2.normal_OS` condition:
// pinglamb's replay-2026-10-12-02.ttrm round 1 (m2r2), order as drawn OISJLTZ, prefix 32.
// 2026-10-20 adds 20 bag-2 rounds, every one under its own condition but one: 2.ideal 309 -> 320,
// 2.normal_OS 102 -> 109, 2.normal_SO 30 -> 31, and one more 2.ideal build under a 2.normal_OS
// condition (36 -> 37). No new named-list entry: its 25 bag-1 cases are all bag1.z_right.
// 2026-10-22 adds 34 to 2.ideal (24 under its own condition, 7 under 2.normal_OS, 1 under
// 2.normal_SO; hand-summed from the table's deltas), 7 to 2.normal_OS and 4 to 2.normal_SO,
// and one entry each to Z_LEFT_BAG1, TST_DONATE_CASES and PC_OFF_PAGE.
const CONDITIONS = {
  '2.ideal': { '2.ideal': 344, '2.normal_OS': 44, '2.normal_SO': 13 },
  '2.normal_OS': { '2.ideal': 1, '2.normal_OS': 114, '2.normal_SO': 16 },
  '2.normal_SO': { '2.ideal': 11, '2.normal_OS': 1, '2.normal_SO': 34 },
  '2.i_early': { '2.normal_OS': 1 },
};

const committedText = () => readFileSync(ARTEFACT_PATH, 'utf8');
const committed = () => JSON.parse(committedText());
let DIGESTS: RoundDigest[] | null = null;
const digests = () => (DIGESTS ??= corpus().flatMap(s => digestSession(s)));
const name = (c: any) => `${c.session} m${c.match}r${c.round} ${c.player}`;
const cellOf = (entry: string) => entry.split(' ').filter((_, i) => i === 0 || i === 2).join(' ');

test('the emitter covers exactly the corpus on disk', () => {
  expect(corpus()).toEqual(SESSIONS);
  expect(committed().sessions).toEqual(SESSIONS);
});

test('rebuilding reproduces the committed stray-cannon-facts.json byte for byte', () => {
  expect(serialise(build({}, digests()))).toBe(committedText());
}, 600_000);

test('matched_at_6 equals opener-facts.json\'s Stray Cannon exact in every (session, player) cell', () => {
  const art = committed();
  let cells = 0, total = 0;
  for (const s of SESSIONS) {
    const of = JSON.parse(readFileSync(`${ROOT}/${s}/sim/opener-facts.json`, 'utf8'));
    const sc = of.named_openers.openers.find((o: any) => o.key === 'stray_cannon');
    expect(sc, s).toBeTruthy();
    for (const p of sc.players) {
      const mine = art.cases.filter((c: any) => c.session === s && c.player === p.user && c.bag1.matched_at_6);
      expect(mine.length, `${s} ${p.user}`).toBe(p.exact);
      cells++; total += mine.length;
    }
  }
  expect(cells).toBe(2 * SESSIONS.length);
  expect(total).toBeGreaterThan(0);
});

test('the named lists are exactly what the artefact holds, cell by cell', () => {
  const L = committed().lists;
  const pairs: [string, string[], string[]][] = [
    ['z_hold_bag1', L.z_hold_bag1, Z_HOLD_BAG1],
    ['z_placed_elsewhere_bag1', L.z_placed_elsewhere_bag1, Z_PLACED_ELSEWHERE_BAG1],
    ['z_left_bag1', L.z_left_bag1, Z_LEFT_BAG1],
    ['i_early', L.i_early, I_EARLY_CASES],
    ['tst_donate', L.tst_donate, TST_DONATE_CASES],
    ['pc_off_page', L.pc_off_page, PC_OFF_PAGE],
    ['multi_colour_resolved_by_branch', L.multi_colour_resolved_by_branch, MULTI_COLOUR_RESOLVED_BY_BRANCH],
    ['bag2_handedness_mismatch', L.bag2_handedness_mismatch, BAG2_HANDEDNESS_MISMATCH],
    ['colour_disagree', L.colour_disagree, COLOUR_DISAGREE],
    ['pc_garbage_in_window', L.pc_garbage_in_window, PC_GARBAGE_IN_WINDOW],
  ];
  for (const [k, got, want] of pairs) {
    expect([...got].sort(), k).toEqual([...want].sort());
    // per (session, player): an entry naming a cell the data does not support fails, and so does a
    // deleted real one, whichever cell it is in
    const count = (xs: string[]) => {
      const m: Record<string, number> = {};
      for (const x of xs) m[cellOf(x)] = (m[cellOf(x)] ?? 0) + 1;
      return m;
    };
    expect(count(got), k).toEqual(count(want));
  }
  // the lists are derived from the cases, and the cases agree with them
  const C = committed().cases;
  expect(C.filter((c: any) => c.bag1.node === 'bag1.z_hold').map(name).sort()).toEqual([...Z_HOLD_BAG1].sort());
  expect(C.filter((c: any) => c.pc?.off_page_under).length).toBe(PC_OFF_PAGE.length);
});

test('the page-condition tallies are the measured ones', () => {
  expect(committed().conditions).toEqual(CONDITIONS);
});

test('every case and every named entry resolves to a real round with its match POSITION', () => {
  const art = committed();
  const pos = new Map<string, number>();
  for (const s of SESSIONS) {
    const rf = JSON.parse(readFileSync(`${ROOT}/${s}/sim/replay-facts.json`, 'utf8'));
    for (const r of rf.rounds) pos.set(`${s}|${r.file}|${r.round}`, r.match);
  }
  const byName = new Map<string, any>();
  for (const c of art.cases) {
    const m = pos.get(`${c.session}|${c.file}|${c.round_index0}`);
    expect(m, `${c.session} ${c.file} r${c.round_index0}`).toBeDefined();
    expect(c.match, name(c)).toBe(m!);
    expect(c.round).toBe(c.round_index0 + 1);
    byName.set(name(c), c);
  }
  const strip = (x: string) => x.replace(/ \(mirrored\)$/, '').replace(/ under .*$/, '');
  for (const e of [...Z_HOLD_BAG1, ...Z_PLACED_ELSEWHERE_BAG1, ...Z_LEFT_BAG1, ...I_EARLY_CASES,
                   ...TST_DONATE_CASES, ...PC_OFF_PAGE, ...MULTI_COLOUR_RESOLVED_BY_BRANCH])
    expect(byName.has(strip(e)), e).toBe(true);
});

// ── mutants: each must turn this file red ───────────────────────────────────────────────────

const count = (o: any, id: string) => o.nodes.find((n: any) => n.id === id).cases;
const opp = (o: any, id: string) => o.nodes.find((n: any) => n.id === id).opportunities;
const MUTANTS: [string, Mutants, (o: any) => void][] = [
  ['mirroring disabled', { noMirror: true }, o => expect(count(o, 'bag1.z_right')).toBeLessThan(count(committed(), 'bag1.z_right'))],
  ['bag 2 sampled one lock early', { bag2Early: true }, o => expect(count(o, '2.ideal')).toBe(0)],
  // the lock-7 test is kept, so the 6-lock-first order sends the 6-lock matches that placed Z
  // right to z_placed_elsewhere, not to z_hold (revision 2 had no lock-7 test and read z_hold 592)
  ['bag-1 precedence reverted to z_hold first', { zHoldFirst: true },
   o => expect(o.lists.z_placed_elsewhere_bag1.length).toBeGreaterThan(Z_PLACED_ELSEWHERE_BAG1.length)],
  ['the lock-7 piece test removed', { noLock7Test: true }, o => {
    expect(o.lists.z_hold_bag1.length).toBe(Z_HOLD_BAG1.length + Z_PLACED_ELSEWHERE_BAG1.length);
    expect(o.lists.z_placed_elsewhere_bag1).toEqual([]);
  }],
  ['the lock-7 test made mirror-unaware', { lock7MirrorUnaware: true },
   o => expect(o.lists.z_hold_bag1).toContain('2026-07-22 m2r1 yachi')],
  ['the J<->L / S<->Z swap removed from the mirrored condition', { noSwap: true },
   o => expect(o.conditions).not.toEqual(CONDITIONS)],
  ['PC detection gated on a bag-2 match', { pcNeedsBag2: true },
   o => expect(o.lists.pc_off_page).not.toContain('2026-10-03 m18r4 yachi under bag1.z_right.other')],
  ['match taken from the filename-sort index', { matchFromFilename: true },
   o => expect(o.lists.tst_donate).toContain('2026-08-19 m4r4 pinglamb')],
  ['the garbage stop removed', { noGarbageStop: true },
   o => expect(opp(o, 'bag1.z_hold')).toBeGreaterThan(opp(committed(), 'bag1.z_hold'))],
];

test('every mutant changes the artefact, with the symptom its rule predicts', () => {
  const base = committedText();
  for (const [what, mut, symptom] of MUTANTS) {
    const o = build(mut, digests());
    expect(serialise(o) === base, what).toBe(false);
    symptom(o);
  }
}, 600_000);

test('the mutants that make a PC ambiguous throw instead of choosing', () => {
  // without colour, a PC matches every pattern of its branch by occupancy
  expect(() => build({ noColour: true }, digests())).toThrow(/PC matches/);
  // without branch scoping, 2026-09-17 m4r2 matches normal_OS #1 and i_early #1
  expect(() => build({ unscoped: true }, digests())).toThrow(/2026-09-17 m4r2 pinglamb PC matches/);
}, 600_000);

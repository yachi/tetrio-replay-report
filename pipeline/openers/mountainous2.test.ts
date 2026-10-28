/**
 * The 山岳積み2号 route artefact (`analysis/mountainous2-facts.json`, from `pipeline/sim/emit-route-facts.ts
 * --opener mountainous2`; the rules are the shared `route-facts.ts`, the profile
 * `route-profile-mountainous2.ts`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. `matched_harddrop` per (session, player) equals `opener-facts.json`'s Mountainous Stacking 2
 *      `exact`. It compares the FLAG (the 6-lock L-held board by occupancy — harddrop's field), never
 *      a node count.
 *   3. NAMED lists, not bounds: every entry is a real round, resolved by (file, 0-based round) in that
 *      session's replay-facts.json with its match POSITION, and checked per (session, player). Their
 *      sizes are read off this file, never typed in prose.
 *   4. the per-node counts, the mirror split, the page-condition tallies and the case key order are
 *      pinned.
 *   5. mutants: each rule turned off must turn this file red, with the symptom its rule predicts —
 *      and the rules this corpus cannot exercise are NAMED as equivalent, measured, never dropped.
 *
 * COST, accepted explicitly: one more full-corpus `runCaseOracle` digest in the `typescript` job
 * (about a minute), as `stray-cannon.test.ts` and `honey-cup.test.ts` pay. The mutants reuse ONE
 * digest, so they are free.
 *
 * Run: bun test pipeline/openers/mountainous2.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, digestCorpus, corpus, kindsOf, loadRoutes, type RoundDigest, type Mutants }
  from '../sim/route-facts.ts';
import { MOUNTAINOUS2 } from '../sim/route-profile-mountainous2.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { caseName, checkFlagAgainstOpenerFacts, checkNamedList, checkPositions } from './route-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22']);

/** Bag 1 missed the 7-lock board, matched the 6-lock L-held field, and the 7th piece was NOT the
 *  mirror-aware bag-1 L (J when mirrored): a hold. Most of them go on to place the held L on its tower
 *  spot in bag 2 and build 2.ideal or 2.normal#1 (both drawn on the L-stood board); none builds
 *  2.normal#3 or a 4-line PC, the two routes the page draws on the L-held board. */
const L_HOLD_BAG1: string[] = [
  "2026-07-22 m3r3 yachi", "2026-07-22 m3r4 yachi", "2026-07-22 m4r3 yachi",
  "2026-07-22 m6r1 yachi", "2026-07-22 m7r4 pinglamb", "2026-07-22 m10r9 yachi",
  "2026-07-24 m3r6 yachi", "2026-07-24 m4r3 yachi", "2026-07-28 m2r5 yachi",
  "2026-07-28 m4r4 pinglamb", "2026-07-28 m5r2 pinglamb", "2026-07-28 m6r8 yachi",
  "2026-08-01 m1r2 yachi", "2026-08-01 m1r7 yachi", "2026-08-01 m2r2 yachi",
  "2026-08-01 m2r5 yachi", "2026-08-01 m4r1 pinglamb", "2026-08-01 m4r8 yachi",
  "2026-08-01 m5r6 pinglamb", "2026-08-09 m1r8 yachi", "2026-08-09 m3r6 yachi",
  "2026-08-09 m3r7 yachi", "2026-08-09 m5r3 yachi", "2026-08-09 m5r7 yachi",
  "2026-08-09 m6r1 yachi", "2026-08-09 m6r3 yachi", "2026-08-09 m6r4 yachi",
  "2026-08-14 m1r8 yachi", "2026-08-19 m2r2 yachi", "2026-08-19 m2r4 pinglamb",
  "2026-08-19 m2r6 yachi", "2026-08-19 m5r3 yachi", "2026-08-19 m5r4 yachi",
  "2026-08-19 m7r1 pinglamb", "2026-08-19 m7r1 yachi", "2026-08-19 m10r8 yachi",
  "2026-08-25 m1r1 pinglamb", "2026-08-25 m1r2 yachi", "2026-08-25 m2r2 yachi",
  "2026-08-25 m3r7 yachi", "2026-08-25 m5r4 yachi", "2026-08-25 m5r5 yachi",
  "2026-08-25 m7r5 pinglamb", "2026-08-25 m7r5 yachi", "2026-08-25 m8r2 pinglamb",
  "2026-08-25 m8r6 pinglamb", "2026-08-25 m9r7 yachi", "2026-09-03 m1r9 yachi",
  "2026-09-03 m2r6 yachi", "2026-09-03 m4r6 yachi", "2026-09-10 m1r7 pinglamb",
  "2026-09-10 m4r2 pinglamb", "2026-09-10 m4r2 yachi", "2026-09-10 m6r6 yachi",
  "2026-09-11 m3r3 pinglamb", "2026-09-11 m7r6 yachi", "2026-09-17 m4r5 yachi",
  "2026-09-17 m5r5 yachi", "2026-09-17 m6r6 pinglamb", "2026-09-17 m6r6 yachi",
  "2026-09-17 m7r3 yachi", "2026-09-18 m2r1 yachi", "2026-09-18 m4r5 yachi",
  "2026-09-18 m6r1 pinglamb", "2026-09-18 m6r7 yachi", "2026-09-18 m7r4 pinglamb",
  "2026-09-18 m7r5 pinglamb", "2026-09-18 m7r6 yachi", "2026-09-18 m8r2 yachi",
  "2026-09-18 m10r5 yachi", "2026-09-18 m16r3 yachi", "2026-09-19 m2r5 pinglamb",
  "2026-09-19 m7r4 yachi", "2026-09-19 m8r5 yachi", "2026-09-19 m11r5 pinglamb",
  "2026-09-19 m12r5 yachi", "2026-09-19 m12r6 yachi", "2026-09-19 m13r7 yachi",
  "2026-09-19 m14r7 yachi", "2026-09-19 m15r4 yachi", "2026-09-19 m18r5 yachi",
  "2026-09-19 m20r3 yachi", "2026-10-03 m1r5 yachi", "2026-10-03 m9r4 yachi",
  "2026-10-09 m3r4 yachi", "2026-10-09 m4r2 pinglamb", "2026-10-09 m4r2 yachi",
  "2026-10-09 m5r7 pinglamb", "2026-10-09 m5r7 yachi", "2026-10-09 m9r8 pinglamb",
  "2026-10-12 m2r6 yachi", "2026-10-12 m2r7 yachi", "2026-10-12 m8r7 yachi",
];
/** Measured EMPTY: no 6-lock-only match has the bag-1 L (J when mirrored) placed 7th, so the
 *  hold split never files an outcome — and the two rules that decide it are equivalent on this
 *  corpus (see EQUIVALENT below). A first entry is a red build to investigate. */
const L_PLACED_ELSEWHERE_BAG1: string[] = [];
/** A bag-2 match that needed complete garbage rows stripped from under it (the count in brackets). */
const BAG2_GARBAGE_STRIPPED: string[] = [
  "2026-07-22 m4r6 pinglamb (1)", "2026-07-22 m10r8 pinglamb (6)", "2026-07-24 m1r5 pinglamb (11)",
  "2026-07-24 m6r8 yachi (6)", "2026-07-28 m2r5 pinglamb (6)", "2026-07-28 m2r6 yachi (6)",
  "2026-07-28 m4r7 yachi (6)", "2026-07-28 m5r4 yachi (6)", "2026-07-28 m8r5 yachi (6)",
  "2026-08-01 m1r1 pinglamb (1)", "2026-08-01 m3r3 pinglamb (6)", "2026-08-01 m4r1 pinglamb (6)",
  "2026-08-01 m7r7 pinglamb (6)", "2026-08-09 m1r6 yachi (6)", "2026-08-14 m2r3 yachi (6)",
  "2026-08-14 m2r4 pinglamb (6)", "2026-08-14 m5r6 pinglamb (6)", "2026-08-14 m10r4 yachi (6)",
  "2026-08-19 m1r3 pinglamb (11)", "2026-08-19 m7r1 pinglamb (6)", "2026-08-19 m7r2 yachi (6)",
  "2026-08-25 m1r1 pinglamb (11)", "2026-08-25 m2r7 pinglamb (2)", "2026-08-25 m7r5 pinglamb (6)",
  "2026-08-25 m8r2 pinglamb (6)", "2026-08-25 m9r7 yachi (6)", "2026-08-25 m9r9 yachi (6)",
  "2026-09-10 m1r6 pinglamb (4)", "2026-09-10 m3r4 pinglamb (6)", "2026-09-10 m8r4 yachi (6)",
  "2026-09-11 m3r6 pinglamb (6)", "2026-09-17 m7r4 pinglamb (12)", "2026-09-18 m1r4 yachi (12)",
  "2026-09-18 m6r1 pinglamb (2)", "2026-09-18 m6r4 yachi (2)", "2026-09-18 m7r4 yachi (12)",
  "2026-09-18 m7r7 yachi (2)", "2026-09-18 m12r5 yachi (6)", "2026-09-18 m13r2 yachi (6)",
  "2026-09-19 m1r5 yachi (7)", "2026-09-19 m3r5 pinglamb (4)", "2026-09-19 m5r3 yachi (2)",
  "2026-09-19 m12r6 yachi (6)", "2026-09-19 m13r6 yachi (4)", "2026-09-19 m15r4 pinglamb (6)",
  "2026-09-19 m19r7 yachi (4)", "2026-10-03 m2r8 yachi (6)", "2026-10-03 m4r8 pinglamb (2)",
  "2026-10-03 m5r3 pinglamb (6)", "2026-10-03 m7r5 yachi (6)", "2026-10-03 m7r7 pinglamb (2)",
  "2026-10-03 m9r1 yachi (6)", "2026-10-03 m11r5 yachi (6)", "2026-10-03 m12r1 pinglamb (12)",
  "2026-10-03 m15r3 yachi (9)", "2026-10-03 m18r5 pinglamb (4)", "2026-10-03 m19r5 pinglamb (2)",
  "2026-10-09 m4r2 pinglamb (6)", "2026-10-09 m6r4 pinglamb (11)", "2026-10-09 m8r5 yachi (6)",
  "2026-10-09 m8r6 pinglamb (2)", "2026-10-09 m9r8 pinglamb (1)", "2026-10-09 m9r9 pinglamb (2)",
  "2026-10-09 m12r2 pinglamb (11)", "2026-10-12 m1r4 yachi (6)",
];
/** No bag-2 match: the board before the TST is a strict subset of a bag-2 board. MEASURED, not matched. */
const BAG2_NONE_TST_BEFORE_COMPLETE: string[] = [
  "2026-07-22 m3r6 yachi under 2.ideal+2.compromise", "2026-07-22 m5r1 pinglamb under 2.ideal+2.normal+2.compromise",
  "2026-07-28 m1r1 yachi under 2.ideal+2.normal+2.compromise", "2026-08-19 m9r9 yachi under 2.ideal+2.normal+2.compromise",
  "2026-08-25 m5r2 pinglamb under 2.ideal+2.normal+2.compromise", "2026-09-11 m4r6 yachi under 2.ideal+2.compromise",
  "2026-09-18 m7r6 pinglamb under 2.ideal", "2026-09-18 m14r1 yachi under 2.ideal+2.normal+2.compromise",
  "2026-09-19 m14r6 pinglamb under 2.ideal+2.normal+2.compromise", "2026-10-03 m15r4 pinglamb under 2.ideal+2.normal+2.compromise",
  "2026-10-09 m1r2 pinglamb under 2.ideal+2.normal+2.compromise",
  // 2026-10-20: one, yachi's, a 4-cell subset of all three bag-2 boards at lock 11 (prefix 106).
  "2026-10-20 m3r1 yachi under 2.ideal+2.normal+2.compromise",
];
/** No bag-2 match: the board before the TST is a bag-2 board plus exactly four cells (their letters). MEASURED. */
const BAG2_NONE_EXTRA_PIECE: string[] = [
  "2026-07-22 m4r2 yachi under 2.ideal + O", "2026-07-22 m5r5 yachi under 2.ideal + O",
  "2026-08-19 m2r1 yachi under 2.ideal + I", "2026-09-17 m5r4 yachi under 2.ideal + I",
  "2026-09-18 m5r7 pinglamb under 2.normal + SZ", "2026-09-18 m5r7 yachi under 2.normal + SZ",
  "2026-09-18 m10r6 pinglamb under 2.ideal + O", "2026-09-18 m15r1 yachi under 2.normal + SZ",
  "2026-10-03 m14r6 yachi under 2.ideal + O", "2026-10-09 m4r5 yachi under 2.compromise + LO",
];
/** No bag-2 match: the board before the TST is a bag-2 board with one piece's four cells elsewhere. MEASURED. */
const BAG2_NONE_MOVED_PIECE: string[] = [
  "2026-07-28 m4r4 pinglamb under 2.normal, S moved", "2026-08-01 m2r6 pinglamb under 2.compromise, S moved",
  "2026-08-01 m2r6 yachi under 2.compromise, S moved", "2026-08-09 m6r1 yachi under 2.compromise, Z moved",
  "2026-08-14 m9r3 pinglamb under 2.compromise, S moved", "2026-08-19 m5r4 yachi under 2.compromise, Z moved",
  "2026-08-19 m5r7 yachi under 2.compromise, S moved", "2026-08-25 m1r2 pinglamb under 2.compromise, S moved",
  "2026-08-25 m5r9 pinglamb under 2.compromise, S moved", "2026-09-03 m6r4 yachi under 2.compromise, Z moved",
  "2026-09-10 m4r8 pinglamb under 2.compromise, Z moved", "2026-09-18 m3r2 yachi under 2.compromise, S moved",
  "2026-09-18 m6r6 yachi under 2.compromise, Z moved", "2026-09-19 m2r6 yachi under 2.compromise, Z moved",
  "2026-09-19 m6r6 yachi under 2.compromise, Z moved", "2026-09-19 m10r9 yachi under 2.compromise, S moved",
  "2026-10-03 m20r8 yachi under 2.compromise, Z moved", "2026-10-09 m11r4 pinglamb under 2.compromise, S moved",
];
/** 8-line PCs on no drawn pattern, named with the node they stop under. Every one but 2026-07-24 m4r4
 *  has the occupancy of the page's patterns and other colours: most are one recurring arrangement
 *  (IIII LLL JJ Z over L SS J ZZ, as drawn or mirrored) that the page's 14 「complete」 patterns do not
 *  draw. 2026-09-18 m10r6 is a pc#1 by colour under a bag 2 that missed by an extra O (it is in
 *  BAG2_NONE_EXTRA_PIECE), so it stays off the page: patterns are scoped by the bag-2 match. */
const PC_OFF_PAGE: string[] = [
  "2026-07-22 m10r8 yachi under 2.ideal.other", "2026-07-24 m4r4 yachi under bag1.l_top.other",
  "2026-08-09 m4r8 pinglamb under 2.ideal.other", "2026-08-14 m9r3 yachi under 2.ideal.other",
  "2026-08-19 m1r3 yachi under 2.ideal.other", "2026-08-19 m4r6 pinglamb under 2.ideal.other",
  "2026-08-25 m7r1 pinglamb under 2.ideal.other", "2026-08-25 m7r1 yachi under 2.ideal.other",
  "2026-09-11 m1r4 pinglamb under 2.ideal.other", "2026-09-11 m5r5 yachi under 2.normal#1.other",
  "2026-09-18 m7r4 pinglamb under 2.ideal.other", "2026-09-18 m7r5 pinglamb under 2.ideal.other",
  "2026-09-18 m10r6 pinglamb under bag1.l_top.other", "2026-09-18 m15r5 yachi under 2.normal#1.other",
  "2026-09-19 m4r1 yachi under 2.ideal.other", "2026-09-19 m16r6 pinglamb under 2.ideal.other",
  "2026-10-03 m4r6 pinglamb under 2.ideal.other", "2026-10-03 m10r8 pinglamb under 2.ideal.other",
  "2026-10-09 m12r1 yachi under 2.ideal.other", "2026-10-09 m12r9 yachi under 2.normal#1.other",
];

/** Measured empty. A first entry is a red build to investigate, never a number to absorb. */
const BAG2_HANDEDNESS_MISMATCH: string[] = [];
const COLOUR_DISAGREE: string[] = [];
const PC_GARBAGE_IN_WINDOW: string[] = [];
const MULTI_COLOUR_RESOLVED_BY_GROUP: string[] = [];

/** Both players mirror 山岳積み2号: pinned as a count per player, not a list. */
const MIRRORED_BAG1 = { yachi: 159, pinglamb: 25 };

/** Cases per measured node. No corpus round reaches the 4-line PCs, 2.normal#2/#3 or anything under
 *  2.compromise past its TST: those zeros are COMPARED (the classifier detects all three PC kinds and
 *  the bag-3 and bag-4 snapshot boards; the demos test reaches each one), never "not compared". */
const NODE_CASES: Record<string, number> = {
  'bag1.l_top': 382, 'bag1.l_hold': 93, 'bag1.l_placed_elsewhere': 0,
  '2.pc4#1': 0, '2.pc4#2': 0, '2.pc4#3': 0,
  '2.ideal': 238, '2.normal#1': 100, '2.normal#2': 0, '2.normal#3': 0, '2.compromise': 19,
  '2.ideal.pc#1': 5, '2.ideal.pc#2': 13, '2.ideal.pc#3': 18, '2.ideal.pc#4': 0, '2.ideal.pc#5': 0,
  '2.ideal.pc#6': 0, '2.ideal.pc#7': 1, '2.ideal.pc#8': 0, '2.ideal.pc#9': 0, '2.ideal.pc#10': 0,
  '2.ideal.pc#11': 0, '2.ideal.pc#12': 0, '2.ideal.pc#13': 0, '2.ideal.pc#14': 0,
  '2.normal.pc#1': 3, '2.normal.pc#2': 0, '2.normal.pc#3': 0, '2.normal.pc#4': 0, '2.normal.pc#5': 0,
  '2.normal.pc#6': 0, '2.normal.pc#7': 0, '2.normal.pc#8': 0,
  '2.compromise.fire34': 0, '2.compromise.fire34.bag4': 0, '2.compromise.fire5#1': 0, '2.compromise.fire5#2': 0,
  '2.compromise.fire5.pc#1': 0, '2.compromise.fire5.pc#2': 0, '2.compromise.fire5.pc#3': 0,
  '2.compromise.fire5.pc#4': 0, '2.compromise.fire5.pc#5': 0, '2.compromise.fire5.pc#6': 0,
};
/** Measured nodes the classifier cannot compare, and why (from the routes JSON, never a count of 0). */
const UNMEASURED: Record<string, string> = {
  'overview.derivation_map': 'image_only', 'overview.video': 'video_only', 'bag1.j_top': 'mirror_of: bag1.l_top',
  '2.ideal.after': 'illustration', '2.ideal.fire.pc5_image': 'image_only', '2.normal.after': 'illustration',
  '2.compromise.after': 'illustration', '2.compromise.fire34.cycle1': 'cycle_fragment',
  '2.compromise.fire34.cycle2': 'cycle_fragment', '2.compromise.fire34.cycle3': 'cycle_fragment',
  '2.compromise.fire34.cycle4': 'cycle_fragment', '2.compromise.fire34.bag4.cycle1': 'cycle_fragment',
  '2.compromise.fire34.bag4.cycle2': 'cycle_fragment', '2.compromise.fire5.after': 'illustration',
  '2.compromise.fire5.bag4#1': 'unmatchable: 9 non-empty rows (under the blank top row) > ROWS = 8', '2.compromise.fire5.bag4#2': 'unmatchable: 9 non-empty rows (under the blank top row) > ROWS = 8',
  '2.compromise.fire5.bag4.after': 'illustration',
};

/** The page conditions met by the round's own bag-2 order (our readings: 理想形 S before O, 妥協系 O
 *  before S), against the form actually built, in the handedness the page draws. The 通常形 family's
 *  trigger is a pair of early pairs with no threshold, so it never decides. A sizeable minority of
 *  2.ideal rounds dealt O before S, so the condition is a description of the page, not of the play. */
const CONDITIONS = {
  '2.ideal': { '2.compromise': 44, '2.ideal': 194 },
  '2.compromise': { '2.compromise': 19 },
  '2.normal#1': { '2.compromise': 96, '2.ideal': 4 },
};

/** The case object's key order is part of the artefact's bytes. */
const CASE_KEYS = ['session', 'file', 'round_index0', 'match', 'round', 'player', 'verified_to', 'bag1', 'bag2',
                   'pc', 'snapshots', 'bag2_near', 'deepest', 'deepest_lock', 'verified'];
const BAG1_KEYS = ['node', 'mirrored', 'lock', 'lock7_piece', 'matched_harddrop', 'matched_variants'];
const BAG2_KEYS = ['node', 'mirrored', 'lock', 'order_as_drawn', 'conditions_met', 'condition_met',
                   'handedness_matches_bag1', 'garbage_rows_stripped'];

const committedText = () => readFileSync(MOUNTAINOUS2.artefactPath, 'utf8');
const committed = () => JSON.parse(committedText());
let DIGESTS: RoundDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(MOUNTAINOUS2));

test('the emitter covers exactly the corpus on disk', () => {
  expect(corpus()).toEqual(SESSIONS);
  expect(committed().sessions).toEqual(SESSIONS);
  expect(committed().schema).toBe('mountainous2-facts/1');
  expect(committed().report_eligible).toBe(false);
});

test('rebuilding reproduces the committed mountainous2-facts.json byte for byte', () => {
  expect(serialise(build(MOUNTAINOUS2, {}, digests()))).toBe(committedText());
}, 600_000);

test('matched_harddrop equals opener-facts.json\'s Mountainous Stacking 2 exact in every (session, player) cell', () => {
  const { cells, total } = checkFlagAgainstOpenerFacts(committed(), SESSIONS, ROOT, 'mountainous_2', 'matched_harddrop');
  expect(cells).toBe(2 * SESSIONS.length);
  expect(total).toBeGreaterThan(0);
});

test('the three PC kinds cover every route list once, and a PC is filed by its line count', () => {
  const routes = loadRoutes(MOUNTAINOUS2.routesPath);
  const kinds = kindsOf(MOUNTAINOUS2, routes);
  expect(kinds.map(k => [k.lists, k.lines, k.patterns.length]))
    .toEqual([[['2.ideal.pc', '2.normal.pc'], 8, 22], [['2.pc4'], 4, 3], [['2.compromise.fire5.pc'], 14, 6]]);
  // a profile naming a list the routes do not hold, or leaving one out, fails loudly
  expect(() => kindsOf({ ...MOUNTAINOUS2, pcKinds: MOUNTAINOUS2.pcKinds!.slice(1) }, routes)).toThrow(/pcKinds name lists/);
  // every corpus PC on a pattern is an 8-line one at lock 19 (measured: no 4- or 14-line PC)
  for (const c of committed().cases.filter((c: any) => c.pc)) expect(c.pc.lock, caseName(c)).toBe(19);
});

test('the named lists are exactly what the artefact holds, cell by cell', () => {
  const L = committed().lists;
  const pairs: [string, string[], string[]][] = [
    ['l_hold_bag1', L.l_hold_bag1, L_HOLD_BAG1],
    ['l_placed_elsewhere_bag1', L.l_placed_elsewhere_bag1, L_PLACED_ELSEWHERE_BAG1],
    ['bag2_garbage_stripped', L.bag2_garbage_stripped, BAG2_GARBAGE_STRIPPED],
    ['bag2_none_tst_before_complete', L.bag2_none_tst_before_complete, BAG2_NONE_TST_BEFORE_COMPLETE],
    ['bag2_none_extra_piece', L.bag2_none_extra_piece, BAG2_NONE_EXTRA_PIECE],
    ['bag2_none_moved_piece', L.bag2_none_moved_piece, BAG2_NONE_MOVED_PIECE],
    ['pc_off_page', L.pc_off_page, PC_OFF_PAGE],
    ['multi_colour_resolved_by_branch', L.multi_colour_resolved_by_branch, MULTI_COLOUR_RESOLVED_BY_GROUP],
    ['bag2_handedness_mismatch', L.bag2_handedness_mismatch, BAG2_HANDEDNESS_MISMATCH],
    ['colour_disagree', L.colour_disagree, COLOUR_DISAGREE],
    ['pc_garbage_in_window', L.pc_garbage_in_window, PC_GARBAGE_IN_WINDOW],
  ];
  for (const [k, got, want] of pairs) checkNamedList(k, got, want);
  const C = committed().cases;
  expect(C.filter((c: any) => c.bag1.node === 'bag1.l_hold').map(caseName).sort()).toEqual([...L_HOLD_BAG1].sort());
  expect(C.filter((c: any) => c.pc?.off_page_under).length).toBe(PC_OFF_PAGE.length);
  // no L-held round builds a board the page draws on the L-held board
  for (const c of C.filter((c: any) => c.bag1.node === 'bag1.l_hold'))
    expect(['2.normal#3', '2.pc4#1', '2.pc4#2', '2.pc4#3']).not.toContain(c.bag2?.node ?? c.pc?.node ?? '');
});

test('per-node counts, the mirror split and the page-condition tallies are the measured ones', () => {
  const art = committed();
  for (const [id, n] of Object.entries(NODE_CASES))
    expect(art.nodes.find((x: any) => x.id === id)?.cases, id).toBe(n);
  for (const [id, why] of Object.entries(UNMEASURED)) {
    const n = art.nodes.find((x: any) => x.id === id);
    expect(n?.measured, id).toBe(false);
    expect(n.why, id).toBe(why);
  }
  expect(art.nodes.length).toBe(Object.keys(NODE_CASES).length + Object.keys(UNMEASURED).length);
  const mirrored: Record<string, number> = {};
  for (const c of art.cases) if (c.bag1.mirrored) mirrored[c.player] = (mirrored[c.player] ?? 0) + 1;
  expect(mirrored).toEqual(MIRRORED_BAG1);
  expect(art.conditions).toEqual(CONDITIONS);
  const routes = JSON.parse(readFileSync(MOUNTAINOUS2.routesPath, 'utf8'));
  expect(art.nodes.map((n: any) => n.id)).toEqual([...routes.nodes.map((n: any) => n.id), 'bag1.l_placed_elsewhere']);
  // the anchors: the 4-line PCs count the L-held rounds, the 5巡目 PCs the 2.compromise rounds
  const opp = (id: string) => art.nodes.find((n: any) => n.id === id).opportunities;
  expect(opp('2.pc4#1')).toBe(NODE_CASES['bag1.l_hold']);
  expect(opp('2.compromise.fire5.pc#1')).toBe(NODE_CASES['2.compromise']);
  expect(opp('2.normal.pc#1')).toBe(NODE_CASES['2.normal#1']);
});

test('the case key order is pinned, and bag-3 lists are scoped by the form\'s GROUP', () => {
  const art = committed();
  for (const c of art.cases) {
    expect(Object.keys(c)).toEqual(CASE_KEYS);
    expect(Object.keys(c.bag1)).toEqual(BAG1_KEYS);
    if (c.bag2) expect(Object.keys(c.bag2)).toEqual(BAG2_KEYS);
  }
  const routes = JSON.parse(readFileSync(MOUNTAINOUS2.routesPath, 'utf8'));
  const parent = new Map(routes.nodes.map((n: any) => [n.id, n.parent]));
  const group = new Map(routes.nodes.map((n: any) => [n.id, n.group ?? n.id]));
  const withPc = art.cases.filter((c: any) => c.pc?.node);
  expect(withPc.length).toBeGreaterThan(0);
  for (const c of withPc) expect(parent.get(c.pc.node), caseName(c)).toBe(group.get(c.bag2.node));
  // the 2.normal list is reached through the group, from form 1
  expect(withPc.some((c: any) => c.bag2.node === '2.normal#1' && c.pc.node.startsWith('2.normal.pc#'))).toBe(true);
  expect(art.cases.some((c: any) => c.bag2?.node && c.bag2.garbage_rows_stripped > 0)).toBe(true);
});

test('every case and every named entry resolves to a real round with its match POSITION', () => {
  checkPositions(committed(), SESSIONS, ROOT,
    [...L_HOLD_BAG1, ...BAG2_GARBAGE_STRIPPED, ...BAG2_NONE_TST_BEFORE_COMPLETE, ...BAG2_NONE_EXTRA_PIECE,
     ...BAG2_NONE_MOVED_PIECE, ...PC_OFF_PAGE]);
});

// ── mutants: each must turn this file red ───────────────────────────────────────────────────

const count = (o: any, id: string) => o.nodes.find((n: any) => n.id === id).cases;
const opp = (o: any, id: string) => o.nodes.find((n: any) => n.id === id).opportunities;
const MUTANTS: [string, Mutants, (o: any) => void][] = [
  ['bag-3 scoped by the bag-2 node, not its group', { noGroupScope: true }, o => {
    expect(count(o, '2.normal.pc#1')).toBe(0);
    expect(o.lists.pc_off_page.length).toBe(PC_OFF_PAGE.length + NODE_CASES['2.normal.pc#1']!);
  }],
  ['garbage refused instead of stripped at bag 2', { noGarbageStrip: true }, o => {
    expect(count(o, '2.ideal') + count(o, '2.normal#1')).toBeLessThan(NODE_CASES['2.ideal']! + NODE_CASES['2.normal#1']!);
    expect(o.lists.bag2_garbage_stripped).toEqual([]);
  }],
  ['the hold stage tried before the placed one', { zHoldFirst: true }, o => {
    // a 7-lock round whose 6-lock board is the L-held field placed its L 7th: an outcome, not a hold
    expect(o.lists.l_placed_elsewhere_bag1.length).toBeGreaterThan(0);
    expect(count(o, 'bag1.l_top')).toBeLessThan(NODE_CASES['bag1.l_top']!);
  }],
  ['mirroring disabled', { noMirror: true }, o => expect(count(o, 'bag1.l_top')).toBeLessThan(NODE_CASES['bag1.l_top']!)],
  ['bag 2 sampled one lock early', { bag2Early: true },
   o => expect(count(o, '2.ideal') + count(o, '2.normal#1') + count(o, '2.compromise')).toBe(0)],
  ['the J<->L / S<->Z swap removed from the mirrored condition', { noSwap: true },
   o => expect(o.conditions).not.toEqual(CONDITIONS)],
  ['PCs unscoped', { unscoped: true }, o => expect(o.lists.pc_off_page.length).toBeLessThan(PC_OFF_PAGE.length)],
  ['PC detection only under a matched bag 2', { pcNeedsBag2: true },
   o => expect(o.lists.pc_off_page.length).toBeLessThan(PC_OFF_PAGE.length)],
  ['the garbage stop removed', { noGarbageStop: true },
   o => expect(opp(o, 'bag1.l_hold')).toBeGreaterThan(opp(committed(), 'bag1.l_hold'))],
  ['match taken from the filename-sort index', { matchFromFilename: true },
   o => expect(o.lists.l_hold_bag1).not.toEqual(committed().lists.l_hold_bag1)],
];

/** EQUIVALENT on this corpus, measured: each leaves the artefact byte-identical, because the case
 *  that would exercise it never occurs. `noLock7Test` and `lock7MirrorUnaware`: no 6-lock-only match
 *  has the bag-1 L (or J) placed 7th (L_PLACED_ELSEWHERE_BAG1 is empty). `pcLinesOff`: every corpus
 *  PC after a matched bag 1 is the first kind's 8 lines. Named, so the day one stops being equivalent
 *  is a red build; the rules themselves are exercised by honey-cup.test.ts and, for the PC kinds, by
 *  the demos (which reach a 4-line and a 14-line PC through this classifier). */
const EQUIVALENT: (keyof Mutants)[] = ['noLock7Test', 'lock7MirrorUnaware', 'pcLinesOff'];

test('every mutant changes the artefact, with the symptom its rule predicts', () => {
  const base = committedText();
  for (const [what, mut, symptom] of MUTANTS) {
    const o = build(MOUNTAINOUS2, mut, digests());
    expect(serialise(o) === base, what).toBe(false);
    symptom(o);
  }
}, 600_000);

test('the mutants this corpus cannot exercise are equivalent, and named', () => {
  const base = committedText();
  for (const m of EQUIVALENT) expect(serialise(build(MOUNTAINOUS2, { [m]: true }, digests())), m).toBe(base);
}, 600_000);

test('a PC matched by occupancy alone is ambiguous and throws instead of choosing', () => {
  // the 2.ideal patterns share one occupancy: without colour, an off-page PC matches all of them
  expect(() => build(MOUNTAINOUS2, { noColour: true }, digests())).toThrow(/PC matches/);
}, 600_000);

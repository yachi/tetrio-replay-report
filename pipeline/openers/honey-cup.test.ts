/**
 * The はちみつ砲 route artefact (`analysis/honey-cup-facts.json`, from `pipeline/sim/emit-route-facts.ts
 * --opener honeycup`; the rules are the shared `route-facts.ts`, the profile `route-profile-honeycup.ts`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. `matched_harddrop` per (session, player) equals `opener-facts.json`'s Honey Cup `exact`. It
 *      compares the FLAG (the 7-lock board by occupancy), never a node count.
 *   3. NAMED lists, not bounds: every entry is a real round, resolved by (file, 0-based round) in that
 *      session's replay-facts.json with its match POSITION, and checked per (session, player). Their
 *      sizes are read off this file, never typed in prose.
 *   4. the per-node counts, the page-condition tallies and the case key order are pinned.
 *   5. mutants: each rule turned off must turn this file red, with the symptom its rule predicts.
 *
 * COST, accepted explicitly: one more full-corpus `runCaseOracle` digest in the `typescript` job
 * (about a minute and a half), as `stray-cannon.test.ts` pays; a digest shared across test files
 * would couple them. The mutants reuse ONE digest, so they are free.
 *
 * Run: bun test pipeline/openers/honey-cup.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, digestCorpus, corpus, type RoundDigest, type Mutants } from '../sim/route-facts.ts';
import { HONEYCUP } from '../sim/route-profile-honeycup.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { caseName, checkFlagAgainstOpenerFacts, checkNamedList, checkPositions } from './route-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22',
   '2026-10-29']);

/** Bag 1 missed the 7-lock board, matched the 6-lock held-J field, and the 7th piece was NOT the
 *  mirror-aware bag-1 J (L when mirrored): a hold. */
const J_HOLD_BAG1: string[] = [
  "2026-07-22 m2r5 pinglamb", "2026-07-22 m9r6 yachi", "2026-07-24 m3r3 pinglamb",
  "2026-07-28 m8r9 pinglamb", "2026-08-09 m6r3 pinglamb", "2026-08-19 m3r3 pinglamb",
  "2026-08-19 m6r1 pinglamb", "2026-08-25 m6r4 yachi", "2026-09-03 m2r3 pinglamb",
  "2026-09-10 m6r9 pinglamb", "2026-09-11 m6r2 pinglamb", "2026-09-11 m6r7 pinglamb",
  "2026-09-17 m2r4 pinglamb", "2026-09-17 m7r5 yachi", "2026-09-18 m14r3 yachi",
  "2026-09-19 m17r3 pinglamb", "2026-09-19 m19r5 yachi", "2026-10-03 m15r2 pinglamb",
  "2026-10-03 m15r2 yachi", "2026-10-09 m1r3 pinglamb", "2026-10-09 m1r3 yachi",
  "2026-10-09 m1r6 pinglamb", "2026-10-09 m7r2 pinglamb",
  // 2026-10-20: one, pinglamb's, mirrored (its bag-1 J is L) with an S placed 7th — prefix 25, past
  // the lock-19 TST-donate board it goes on to reach (TST_DONATE_CASES).
  "2026-10-20 m3r3 pinglamb",
];
/** The 6-lock field matched and the 7th piece WAS the bag-1 J (L when mirrored), placed off the page. */
const J_PLACED_ELSEWHERE_BAG1: string[] = [
  "2026-07-22 m3r1 pinglamb", "2026-07-22 m4r2 pinglamb", "2026-07-24 m6r4 pinglamb",
  "2026-08-01 m3r4 pinglamb", "2026-08-09 m6r7 pinglamb", "2026-08-09 m6r9 pinglamb",
  "2026-08-14 m6r1 pinglamb", "2026-08-19 m1r2 pinglamb", "2026-08-19 m8r1 pinglamb",
  "2026-08-19 m8r4 pinglamb", "2026-08-25 m6r2 pinglamb", "2026-09-03 m1r3 pinglamb",
  "2026-09-03 m4r2 pinglamb", "2026-09-10 m3r2 pinglamb", "2026-09-10 m7r8 pinglamb",
  "2026-09-11 m1r8 pinglamb", "2026-09-17 m3r5 pinglamb", "2026-09-18 m3r7 pinglamb",
  "2026-09-18 m11r3 pinglamb", "2026-09-18 m15r4 pinglamb", "2026-09-18 m17r9 pinglamb",
  "2026-09-19 m8r4 pinglamb", "2026-09-19 m9r7 pinglamb", "2026-09-19 m10r8 pinglamb",
  "2026-09-19 m19r3 pinglamb", "2026-09-19 m19r6 pinglamb", "2026-10-03 m6r6 pinglamb",
  "2026-10-09 m3r5 pinglamb", "2026-10-09 m7r7 pinglamb", "2026-10-09 m10r3 pinglamb",
];
/** The compromise form, then the TST-donate board, under its own branch. */
const TST_DONATE_CASES: string[] = [
  "2026-07-22 m7r6 pinglamb", "2026-07-22 m7r8 pinglamb", "2026-07-24 m3r3 pinglamb",
  "2026-07-24 m5r4 pinglamb", "2026-07-24 m5r7 pinglamb", "2026-07-24 m6r1 pinglamb",
  "2026-07-24 m6r4 pinglamb", "2026-07-28 m6r4 pinglamb", "2026-08-01 m3r2 pinglamb",
  "2026-08-01 m4r9 pinglamb", "2026-08-09 m6r7 pinglamb", "2026-08-14 m1r5 pinglamb",
  "2026-08-14 m3r5 pinglamb", "2026-08-14 m5r7 pinglamb", "2026-08-14 m10r7 pinglamb",
  "2026-08-19 m1r2 pinglamb", "2026-08-19 m3r3 pinglamb", "2026-08-19 m4r3 pinglamb",
  "2026-08-19 m5r7 pinglamb", "2026-08-19 m7r3 pinglamb", "2026-08-19 m8r1 pinglamb",
  "2026-08-19 m9r3 pinglamb", "2026-08-25 m1r7 pinglamb", "2026-08-25 m3r4 pinglamb",
  "2026-08-25 m9r6 pinglamb", "2026-09-03 m2r5 pinglamb", "2026-09-03 m2r9 pinglamb",
  "2026-09-03 m5r6 pinglamb", "2026-09-10 m1r5 pinglamb", "2026-09-10 m4r3 pinglamb",
  "2026-09-10 m8r2 pinglamb", "2026-09-11 m1r8 pinglamb", "2026-09-11 m4r3 pinglamb",
  "2026-09-11 m5r1 pinglamb", "2026-09-11 m6r2 pinglamb", "2026-09-17 m1r3 pinglamb",
  "2026-09-17 m4r5 pinglamb", "2026-09-18 m3r7 pinglamb", "2026-09-18 m6r5 pinglamb",
  "2026-09-18 m14r6 pinglamb", "2026-09-19 m4r7 pinglamb", "2026-09-19 m5r7 pinglamb",
  "2026-09-19 m6r4 pinglamb", "2026-09-19 m6r5 pinglamb", "2026-09-19 m8r4 pinglamb",
  "2026-09-19 m10r3 pinglamb", "2026-09-19 m16r5 pinglamb", "2026-09-19 m19r4 pinglamb",
  "2026-09-19 m20r7 pinglamb", "2026-10-03 m6r7 pinglamb", "2026-10-03 m10r6 pinglamb",
  "2026-10-03 m11r4 pinglamb", "2026-10-03 m12r4 pinglamb", "2026-10-03 m14r3 pinglamb",
  "2026-10-03 m16r5 pinglamb", "2026-10-03 m17r6 pinglamb", "2026-10-09 m2r1 pinglamb",
  "2026-10-09 m7r2 pinglamb",
  // 2026-10-12: two, both pinglamb's, both reaching the TST-donate board at lock 19 (prefixes 108
  // and 51); m4r3 needed no garbage stripped, m7r4 two rows (BAG2_GARBAGE_STRIPPED).
  "2026-10-12 m4r3 pinglamb", "2026-10-12 m7r4 pinglamb",
  // 2026-10-20: three, all pinglamb's, all reaching the TST-donate board at lock 19 with no garbage
  // stripped (prefixes 25, 20 and 333); m3r3 is the J_HOLD_BAG1 round, m4r8 the one 2.compromise
  // build of the night whose own condition held (CONDITIONS).
  "2026-10-20 m3r3 pinglamb", "2026-10-20 m4r5 pinglamb", "2026-10-20 m4r8 pinglamb",
  "2026-10-22 m5r1 pinglamb", "2026-10-22 m9r2 pinglamb",
  // 2026-10-29: two, both pinglamb's and mirrored (prefixes 77 and 45).
  "2026-10-29 m1r2 pinglamb", "2026-10-29 m4r5 pinglamb",
];
/** A bag-2 match that needed complete garbage rows stripped from under it (the count in brackets). */
const BAG2_GARBAGE_STRIPPED: string[] = [
  "2026-07-22 m2r5 pinglamb (6)", "2026-07-22 m4r5 pinglamb (2)", "2026-07-22 m5r3 pinglamb (1)",
  "2026-07-22 m7r2 pinglamb (11)", "2026-07-22 m7r6 pinglamb (4)", "2026-07-22 m7r8 pinglamb (6)",
  "2026-07-22 m8r2 pinglamb (4)", "2026-07-22 m8r4 pinglamb (4)", "2026-07-24 m1r1 yachi (6)",
  "2026-07-24 m2r2 pinglamb (2)", "2026-07-24 m2r6 pinglamb (6)", "2026-07-24 m3r8 pinglamb (4)",
  "2026-07-24 m6r3 pinglamb (4)", "2026-07-24 m6r4 pinglamb (4)", "2026-07-28 m3r1 pinglamb (4)",
  "2026-07-28 m3r4 pinglamb (1)", "2026-07-28 m4r8 pinglamb (6)", "2026-07-28 m6r4 pinglamb (4)",
  "2026-07-28 m7r4 pinglamb (7)", "2026-07-28 m8r2 yachi (6)", "2026-07-28 m8r9 pinglamb (4)",
  "2026-08-01 m1r3 pinglamb (1)", "2026-08-01 m3r4 pinglamb (4)", "2026-08-01 m4r3 pinglamb (4)",
  "2026-08-01 m4r4 yachi (6)", "2026-08-01 m6r1 pinglamb (4)", "2026-08-01 m7r1 yachi (6)",
  "2026-08-01 m7r5 pinglamb (1)", "2026-08-09 m2r2 pinglamb (4)", "2026-08-09 m2r3 pinglamb (4)",
  "2026-08-09 m3r2 yachi (6)", "2026-08-09 m4r7 pinglamb (4)", "2026-08-09 m5r6 pinglamb (9)",
  "2026-08-09 m6r7 pinglamb (4)", "2026-08-09 m6r9 pinglamb (4)", "2026-08-14 m1r5 pinglamb (4)",
  "2026-08-14 m1r7 pinglamb (4)", "2026-08-14 m4r8 pinglamb (4)", "2026-08-14 m5r5 pinglamb (4)",
  "2026-08-14 m5r7 pinglamb (4)", "2026-08-14 m6r1 pinglamb (4)", "2026-08-14 m6r7 pinglamb (4)",
  "2026-08-14 m7r3 pinglamb (4)", "2026-08-14 m7r5 pinglamb (4)", "2026-08-14 m7r6 pinglamb (1)",
  "2026-08-14 m8r1 pinglamb (4)", "2026-08-14 m9r1 pinglamb (4)", "2026-08-14 m10r1 pinglamb (6)",
  "2026-08-14 m10r7 pinglamb (4)", "2026-08-14 m11r7 pinglamb (4)", "2026-08-19 m1r2 pinglamb (4)",
  "2026-08-19 m3r5 pinglamb (1)", "2026-08-19 m6r5 pinglamb (4)", "2026-08-19 m8r1 pinglamb (4)",
  "2026-08-19 m8r4 pinglamb (4)", "2026-08-19 m9r3 pinglamb (4)", "2026-08-19 m9r4 pinglamb (4)",
  "2026-08-19 m9r7 pinglamb (4)", "2026-08-25 m1r7 pinglamb (4)", "2026-08-25 m3r5 yachi (6)",
  "2026-08-25 m5r5 pinglamb (12)", "2026-08-25 m6r2 pinglamb (4)", "2026-08-25 m6r5 yachi (6)",
  "2026-08-25 m8r4 pinglamb (4)", "2026-08-25 m8r5 pinglamb (4)", "2026-08-25 m8r9 pinglamb (4)",
  "2026-09-03 m1r7 pinglamb (9)", "2026-09-03 m5r6 pinglamb (4)", "2026-09-03 m6r2 pinglamb (4)",
  "2026-09-03 m6r5 pinglamb (9)", "2026-09-03 m6r6 pinglamb (4)", "2026-09-10 m1r3 pinglamb (12)",
  "2026-09-10 m3r2 pinglamb (4)", "2026-09-10 m3r3 pinglamb (9)", "2026-09-10 m5r6 pinglamb (2)",
  "2026-09-10 m6r5 pinglamb (4)", "2026-09-10 m8r5 yachi (6)", "2026-09-10 m8r8 pinglamb (4)",
  "2026-09-11 m1r8 pinglamb (4)", "2026-09-11 m4r3 pinglamb (4)", "2026-09-11 m4r7 pinglamb (4)",
  "2026-09-11 m6r2 pinglamb (4)", "2026-09-11 m7r7 pinglamb (11)", "2026-09-17 m2r1 pinglamb (9)",
  "2026-09-17 m2r4 pinglamb (4)", "2026-09-17 m3r7 pinglamb (4)", "2026-09-17 m6r2 pinglamb (4)",
  "2026-09-17 m6r5 pinglamb (9)", "2026-09-17 m6r7 pinglamb (7)", "2026-09-17 m7r2 pinglamb (12)",
  "2026-09-18 m1r8 pinglamb (4)", "2026-09-18 m2r4 pinglamb (4)", "2026-09-18 m3r6 pinglamb (4)",
  "2026-09-18 m3r7 pinglamb (4)", "2026-09-18 m3r8 pinglamb (4)", "2026-09-18 m4r2 pinglamb (4)",
  "2026-09-18 m7r2 pinglamb (4)", "2026-09-18 m10r3 pinglamb (11)", "2026-09-18 m14r6 pinglamb (4)",
  "2026-09-18 m15r4 pinglamb (9)", "2026-09-18 m17r5 pinglamb (4)", "2026-09-18 m18r2 pinglamb (4)",
  "2026-09-18 m18r4 pinglamb (2)", "2026-09-19 m1r8 pinglamb (4)", "2026-09-19 m4r7 pinglamb (4)",
  "2026-09-19 m5r5 pinglamb (6)", "2026-09-19 m5r6 pinglamb (4)", "2026-09-19 m6r1 pinglamb (4)",
  "2026-09-19 m8r4 pinglamb (4)", "2026-09-19 m9r3 pinglamb (4)", "2026-09-19 m10r3 pinglamb (4)",
  "2026-09-19 m10r5 pinglamb (4)", "2026-09-19 m10r6 pinglamb (4)", "2026-09-19 m11r3 pinglamb (4)",
  "2026-09-19 m12r7 pinglamb (9)", "2026-09-19 m14r2 pinglamb (6)", "2026-09-19 m16r1 pinglamb (2)",
  "2026-09-19 m16r5 pinglamb (4)", "2026-09-19 m17r1 pinglamb (4)", "2026-09-19 m17r6 pinglamb (4)",
  "2026-09-19 m18r3 pinglamb (4)", "2026-09-19 m19r4 pinglamb (9)", "2026-09-19 m20r5 pinglamb (4)",
  "2026-09-19 m20r6 pinglamb (9)", "2026-09-19 m20r7 pinglamb (1)", "2026-09-19 m20r8 pinglamb (4)",
  "2026-10-03 m2r1 pinglamb (4)", "2026-10-03 m5r4 pinglamb (2)", "2026-10-03 m6r6 pinglamb (4)",
  "2026-10-03 m6r7 pinglamb (4)", "2026-10-03 m7r4 pinglamb (5)", "2026-10-03 m9r5 pinglamb (2)",
  "2026-10-03 m10r1 pinglamb (2)", "2026-10-03 m10r4 yachi (6)", "2026-10-03 m10r6 pinglamb (2)",
  "2026-10-03 m11r4 pinglamb (2)", "2026-10-03 m13r3 pinglamb (4)", "2026-10-03 m14r3 pinglamb (9)",
  "2026-10-03 m14r4 yachi (6)", "2026-10-03 m15r1 pinglamb (2)", "2026-10-03 m15r6 pinglamb (9)",
  "2026-10-03 m16r4 pinglamb (4)", "2026-10-03 m16r5 pinglamb (4)", "2026-10-03 m17r6 pinglamb (4)",
  "2026-10-03 m20r5 pinglamb (9)", "2026-10-09 m1r5 pinglamb (2)", "2026-10-09 m3r5 pinglamb (4)",
  "2026-10-09 m4r4 pinglamb (2)", "2026-10-09 m5r1 pinglamb (2)", "2026-10-09 m5r6 pinglamb (4)",
  "2026-10-09 m5r8 pinglamb (4)", "2026-10-09 m6r6 pinglamb (9)", "2026-10-09 m7r2 pinglamb (2)",
  "2026-10-09 m7r7 pinglamb (4)", "2026-10-09 m8r2 pinglamb (2)", "2026-10-09 m9r4 pinglamb (4)",
  "2026-10-09 m9r5 pinglamb (4)", "2026-10-09 m10r3 pinglamb (7)", "2026-10-09 m11r3 pinglamb (4)",
  "2026-10-09 m11r6 pinglamb (2)", "2026-10-09 m12r3 pinglamb (2)", "2026-10-09 m12r6 pinglamb (2)",
  // 2026-10-12: four. yachi's m3r5 (under 2.ideal#5) is his eleventh entry here and, like all ten
  // before it, strips exactly six rows; the other three are pinglamb's compromise form.
  "2026-10-12 m2r3 pinglamb (4)", "2026-10-12 m3r5 yachi (6)", "2026-10-12 m6r2 pinglamb (3)",
  "2026-10-12 m7r4 pinglamb (2)",
  // 2026-10-20: five. yachi's two are his twelfth and thirteenth entries here — m3r2 strips the usual
  // six, m4r6 (under 2.ideal#3) is the first of his to strip twelve; pinglamb's three are 2.compromise
  // (m1r4) and 2.ideal#4 (m2r1, m4r7).
  "2026-10-20 m1r4 pinglamb (2)", "2026-10-20 m2r1 pinglamb (4)", "2026-10-20 m3r2 yachi (6)",
  "2026-10-20 m4r6 yachi (12)", "2026-10-20 m4r7 pinglamb (4)",
  "2026-10-22 m7r5 yachi (6)", "2026-10-22 m8r2 pinglamb (4)", "2026-10-22 m8r5 pinglamb (4)",
  "2026-10-29 m3r2 yachi (6)", "2026-10-29 m3r5 pinglamb (4)", "2026-10-29 m3r8 pinglamb (4)",
  "2026-10-29 m4r3 pinglamb (6)", "2026-10-29 m6r6 yachi (6)", "2026-10-29 m7r2 pinglamb (4)",
  "2026-10-29 m7r3 pinglamb (4)", "2026-10-29 m7r7 pinglamb (6)", "2026-10-29 m9r2 yachi (6)",
];
/** No bag-2 match: the board before the TST is a strict subset of a bag-2 board. MEASURED, not matched. */
const BAG2_NONE_TST_BEFORE_COMPLETE: string[] = [
  "2026-07-22 m3r1 yachi under 2.ideal", "2026-07-22 m3r2 pinglamb under 2.compromise",
  "2026-07-22 m3r8 pinglamb under 2.ideal", "2026-07-22 m7r8 yachi under 2.ideal",
  "2026-07-22 m8r5 yachi under 2.compromise", "2026-07-22 m9r6 yachi under 2.ideal",
  "2026-07-24 m1r1 pinglamb under 2.ideal", "2026-07-24 m3r5 yachi under 2.ideal",
  "2026-07-28 m6r3 pinglamb under 2.ideal", "2026-08-01 m3r5 pinglamb under 2.ideal",
  "2026-08-01 m5r4 yachi under 2.ideal", "2026-08-09 m3r5 yachi under 2.ideal",
  "2026-08-09 m4r2 yachi under 2.compromise", "2026-08-09 m6r3 pinglamb under 2.compromise",
  "2026-08-14 m11r8 yachi under 2.ideal", "2026-08-19 m3r3 yachi under 2.ideal",
  "2026-08-19 m5r6 yachi under 2.ideal", "2026-08-19 m7r3 yachi under 2.compromise",
  "2026-08-25 m2r6 pinglamb under 2.ideal", "2026-08-25 m3r4 yachi under 2.ideal",
  "2026-08-25 m7r6 pinglamb under 2.ideal", "2026-08-25 m7r7 yachi under 2.ideal",
  "2026-08-25 m8r1 pinglamb under 2.ideal", "2026-08-25 m8r1 yachi under 2.ideal",
  "2026-08-25 m9r8 yachi under 2.ideal", "2026-09-03 m2r2 pinglamb under 2.ideal",
  "2026-09-03 m2r9 yachi under 2.ideal", "2026-09-03 m5r5 pinglamb under 2.ideal",
  "2026-09-10 m3r1 pinglamb under 2.ideal", "2026-09-10 m4r3 yachi under 2.ideal",
  "2026-09-11 m2r3 pinglamb under 2.ideal", "2026-09-11 m3r5 yachi under 2.ideal",
  "2026-09-17 m1r2 pinglamb under 2.compromise", "2026-09-18 m1r3 yachi under 2.ideal",
  "2026-09-18 m10r3 yachi under 2.ideal", "2026-09-18 m14r3 pinglamb under 2.ideal",
  "2026-09-18 m14r3 yachi under 2.ideal", "2026-09-18 m18r3 pinglamb under 2.compromise",
  "2026-09-19 m5r5 yachi under 2.ideal", "2026-09-19 m7r3 yachi under 2.ideal",
  "2026-09-19 m14r1 pinglamb under 2.ideal", "2026-09-19 m14r4 pinglamb under 2.ideal",
  "2026-10-03 m3r8 yachi under 2.ideal", "2026-10-03 m4r5 yachi under 2.ideal",
  "2026-10-03 m6r8 pinglamb under 2.compromise", "2026-10-03 m9r2 pinglamb under 2.compromise",
  "2026-10-03 m10r4 pinglamb under 2.ideal", "2026-10-03 m11r2 pinglamb under 2.ideal",
  "2026-10-03 m12r7 pinglamb under 2.ideal", "2026-10-03 m19r1 pinglamb under 2.compromise",
  "2026-10-09 m3r6 yachi under 2.compromise", "2026-10-09 m6r8 pinglamb under 2.compromise",
  "2026-10-09 m7r4 pinglamb under 2.compromise",
  // 2026-10-12: four, three of them yachi's, every one a 4-cell subset at lock 11 (prefixes 102,
  // 81, 100 and 126) — the TST came before the bag-2 board was complete, as for every entry above.
  "2026-10-12 m4r3 yachi under 2.ideal", "2026-10-12 m5r8 yachi under 2.ideal",
  "2026-10-12 m6r7 yachi under 2.ideal", "2026-10-12 m8r1 pinglamb under 2.compromise",
  // 2026-10-20: one, yachi's, a 4-cell subset at lock 11 (prefix 73) — the same shape as 10-12's four.
  "2026-10-20 m4r3 yachi under 2.ideal",
  "2026-10-22 m4r5 pinglamb under 2.ideal", "2026-10-22 m6r2 yachi under 2.ideal", "2026-10-22 m6r6 yachi under 2.ideal",
  "2026-10-29 m8r3 pinglamb under 2.ideal", "2026-10-29 m8r7 yachi under 2.ideal",
];
/** No bag-2 match: the board before the TST is a bag-2 board plus exactly four cells (their letters). MEASURED. */
const BAG2_NONE_EXTRA_PIECE: string[] = [
  "2026-07-22 m5r6 yachi under 2.ideal + TZ", "2026-07-28 m2r4 yachi under 2.ideal + OT",
  "2026-08-01 m3r2 yachi under 2.ideal + OS", "2026-08-09 m1r3 pinglamb under 2.compromise + ILO",
  "2026-08-09 m3r5 pinglamb under 2.compromise + OZ", "2026-08-14 m9r5 yachi under 2.ideal + L",
  "2026-09-03 m3r4 yachi under 2.ideal + L", "2026-09-03 m4r3 yachi under 2.ideal + J",
  "2026-09-10 m1r5 yachi under 2.ideal + IL", "2026-09-10 m4r6 pinglamb under 2.compromise + IJO",
  "2026-09-17 m7r5 pinglamb under 2.ideal + LO", "2026-09-18 m12r1 pinglamb under 2.ideal + LO",
  "2026-09-18 m14r8 yachi under 2.ideal + JZ", "2026-09-19 m2r1 pinglamb under 2.ideal + J",
  "2026-09-19 m15r1 pinglamb under 2.compromise + JLO", "2026-09-19 m18r7 yachi under 2.ideal + IJ",
  "2026-10-03 m2r4 pinglamb under 2.ideal + I", "2026-10-03 m12r4 yachi under 2.ideal + OT",
  "2026-10-03 m14r2 pinglamb under 2.compromise + ILO", "2026-10-09 m1r7 pinglamb under 2.ideal + JS",
  "2026-10-09 m5r5 pinglamb under 2.compromise + ILO",
  // 2026-10-12: one, mirrored, lock 13, prefix 58 (nine garbage rows stripped before the compare).
  "2026-10-12 m3r3 pinglamb under 2.ideal + J",
  "2026-10-22 m8r6 yachi under 2.ideal + IL",
];
/** No bag-2 match: the board before the TST is a bag-2 board with one piece's four cells elsewhere. MEASURED. */
const BAG2_NONE_MOVED_PIECE: string[] = [
  "2026-07-22 m1r1 pinglamb under 2.ideal, J moved", "2026-07-22 m5r6 pinglamb under 2.ideal, J moved",
  "2026-07-24 m4r3 pinglamb under 2.compromise, O moved",
  "2026-07-24 m5r1 pinglamb under 2.ideal, L moved", "2026-07-24 m6r5 pinglamb under 2.ideal, J moved",
  "2026-07-28 m2r6 pinglamb under 2.ideal, J moved", "2026-07-28 m4r1 pinglamb under 2.ideal, L moved",
  "2026-07-28 m4r1 yachi under 2.ideal, L moved", "2026-08-01 m2r3 pinglamb under 2.ideal, J moved",
  "2026-08-09 m4r5 pinglamb under 2.ideal, J moved", "2026-08-14 m3r3 pinglamb under 2.ideal, J moved",
  "2026-08-14 m7r8 pinglamb under 2.ideal, J moved", "2026-08-19 m6r1 pinglamb under 2.ideal, J moved",
  "2026-08-19 m9r8 pinglamb under 2.compromise, O moved",
  "2026-08-19 m10r4 pinglamb under 2.ideal, J moved",
  "2026-08-19 m10r5 pinglamb under 2.ideal, J moved",
  "2026-08-25 m2r5 pinglamb under 2.ideal, J moved", "2026-08-25 m4r1 pinglamb under 2.ideal, L moved",
  "2026-08-25 m5r1 pinglamb under 2.ideal, L moved", "2026-08-25 m6r1 pinglamb under 2.ideal, L moved",
  "2026-08-25 m8r8 pinglamb under 2.ideal, L moved", "2026-09-03 m3r5 pinglamb under 2.ideal, L moved",
  "2026-09-03 m3r5 yachi under 2.ideal, L moved", "2026-09-03 m4r1 pinglamb under 2.ideal, J moved",
  "2026-09-03 m5r7 pinglamb under 2.ideal, J moved", "2026-09-10 m1r4 pinglamb under 2.ideal, J moved",
  "2026-09-10 m8r5 pinglamb under 2.ideal, J moved", "2026-09-11 m3r5 pinglamb under 2.ideal, L moved",
  "2026-09-11 m3r7 pinglamb under 2.ideal, L moved", "2026-09-11 m6r1 pinglamb under 2.ideal, J moved",
  "2026-09-17 m1r5 pinglamb under 2.ideal, L moved", "2026-09-17 m2r5 pinglamb under 2.ideal, L moved",
  "2026-09-17 m2r6 pinglamb under 2.ideal, L moved", "2026-09-17 m3r5 pinglamb under 2.ideal, J moved",
  "2026-09-17 m6r8 pinglamb under 2.ideal, L moved",
  "2026-09-18 m3r1 pinglamb under 2.compromise, O moved",
  "2026-09-18 m12r3 pinglamb under 2.ideal, L moved",
  "2026-09-18 m17r9 pinglamb under 2.ideal, J moved",
  "2026-09-19 m3r6 pinglamb under 2.ideal, L moved",
  "2026-09-19 m11r2 pinglamb under 2.ideal, J moved",
  "2026-09-19 m19r6 pinglamb under 2.compromise, O moved",
  "2026-09-19 m20r1 pinglamb under 2.ideal, L moved",
  "2026-10-03 m3r5 pinglamb under 2.ideal, L moved",
  "2026-10-03 m13r1 pinglamb under 2.ideal, J moved",
  "2026-10-03 m13r2 pinglamb under 2.ideal, J moved",
  "2026-10-03 m14r7 pinglamb under 2.ideal, J moved",
  "2026-10-03 m15r5 pinglamb under 2.ideal, L moved",
  "2026-10-03 m19r6 pinglamb under 2.ideal, J moved",
  "2026-10-09 m1r3 pinglamb under 2.ideal, L moved", "2026-10-09 m3r2 pinglamb under 2.ideal, J moved",
  // 2026-10-12: two, both pinglamb's, both at lock 12 (prefixes 328 and 109; m8r8 mirrored).
  "2026-10-12 m5r7 pinglamb under 2.ideal, L moved", "2026-10-12 m8r8 pinglamb under 2.ideal, J moved",
  "2026-10-22 m4r1 pinglamb under 2.ideal, J moved", "2026-10-22 m8r6 pinglamb under 2.ideal, L moved",
  "2026-10-29 m4r8 pinglamb under 2.compromise, O moved", "2026-10-29 m7r5 pinglamb under 2.ideal, L moved",
  "2026-10-29 m9r9 pinglamb under 2.ideal, L moved",
];
/** 8-line PCs that are on no drawn pattern, named with the node they stop under. The compromise ones are
 *  NOT filed under the page source's hidden compromise list (html_comment_boards): nothing classifies against it. */
const PC_OFF_PAGE: string[] = [
  "2026-07-28 m7r3 pinglamb under 2.compromise.other",
  "2026-09-03 m4r3 yachi under bag1.j_right.other",
  "2026-09-10 m3r1 pinglamb under bag1.j_right.other",
  "2026-09-17 m2r2 pinglamb under 2.compromise.other",
  "2026-09-19 m16r3 pinglamb under 2.compromise.other",
  "2026-10-03 m4r5 yachi under bag1.j_right.other",
  "2026-10-03 m7r8 pinglamb under 2.compromise.other",
  "2026-10-22 m4r4 pinglamb under 2.compromise.other", "2026-10-22 m5r4 pinglamb under 2.compromise.other",
];

/** Measured empty. A first entry is a red build to investigate, never a number to absorb. */
const BAG2_HANDEDNESS_MISMATCH: string[] = [];
const COLOUR_DISAGREE: string[] = [];
const PC_GARBAGE_IN_WINDOW: string[] = [];
/** A PC matching patterns of two groups by colour: impossible today (one list), so measured empty. */
const MULTI_COLOUR_RESOLVED_BY_GROUP: string[] = [];

/** Both players mirror Honey Cup (unlike 迷走砲): pinned as a count per player, not a list. */
const MIRRORED_BAG1 = { pinglamb: 315, yachi: 93 };

/** Cases per measured node. The five 2.ideal forms share one occupancy, so these split by colour. */
const NODE_CASES: Record<string, number> = {
  'bag1.j_hold': 24, 'bag1.j_right': 674, 'bag1.j_placed_elsewhere': 30,
  '2.ideal#1': 0, '2.ideal#2': 0, '2.ideal#3': 23, '2.ideal#4': 168, '2.ideal#5': 54, '2.compromise': 198,
  // 2026-10-12 adds three bag-3 PCs: two pc#1 (m7r2, pinglamb and yachi, both mirrored) and the
  // corpus's FIRST pc#9 — yachi's m5r1, mirrored, at lock 19 on a prefix verified only to 18, so
  // that case is `verified: false` and the node count carries it as the artefact does.
  // 2026-10-20 adds one bag-3 PC, pinglamb's m4r6 under pc#6 (2 -> 3), mirrored, at lock 19 on a
  // prefix verified only to 14 — the second `verified: false` PC case after 10-12's pc#9, carried the
  // same way.
  // 2026-10-22 adds six bag-3 PCs: one pc#3, two pc#4, two pc#5 (hand-counted from the node deltas).
  // 2026-10-29 adds one, pinglamb's m1r1 under pc#5 (6 -> 7), mirrored, at lock 19 on a prefix
  // verified only to 14 — `verified: false`, carried as 10-12's pc#9 and 10-20's pc#6 are.
  '2.ideal.pc#1': 11, '2.ideal.pc#2': 9, '2.ideal.pc#3': 9, '2.ideal.pc#4': 12, '2.ideal.pc#5': 7,
  '2.ideal.pc#6': 3, '2.ideal.pc#7': 0, '2.ideal.pc#8': 1, '2.ideal.pc#9': 1, '2.ideal.pc#10': 0,
  '2.ideal.pc#11': 0, '2.ideal.pc#12': 0, '2.ideal.pc#13': 0, '2.ideal.pc#14': 0, '2.ideal.pc#15': 0,
  '2.compromise.tst_donate': 67, '2.compromise.tst_donate.after': 0, '2.compromise.roof': 0,
  '2.compromise.roof.after': 0,
};

/** The compromise form's condition (the page's example, など) against the form actually built, in the
 *  handedness the page draws. It holds for a minority of the compromise rounds: never the reason. */
const CONDITIONS = {
  '2.compromise': { '(none)': 168, '2.compromise': 30 },
  '2.ideal#3': { '(none)': 19, '2.compromise': 4 },
  '2.ideal#4': { '(none)': 151, '2.compromise': 17 },
  '2.ideal#5': { '(none)': 42, '2.compromise': 12 },
};

/** The case object's key order is part of the artefact's bytes. */
const CASE_KEYS = ['session', 'file', 'round_index0', 'match', 'round', 'player', 'verified_to', 'bag1', 'bag2',
                   'pc', 'snapshots', 'bag2_near', 'deepest', 'deepest_lock', 'verified'];
const BAG1_KEYS = ['node', 'mirrored', 'lock', 'lock7_piece', 'matched_harddrop', 'matched_variants'];
const BAG2_KEYS = ['node', 'mirrored', 'lock', 'order_as_drawn', 'conditions_met', 'condition_met',
                   'handedness_matches_bag1', 'garbage_rows_stripped'];

const committedText = () => readFileSync(HONEYCUP.artefactPath, 'utf8');
const committed = () => JSON.parse(committedText());
let DIGESTS: RoundDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(HONEYCUP));

test('the emitter covers exactly the corpus on disk', () => {
  expect(corpus()).toEqual(SESSIONS);
  expect(committed().sessions).toEqual(SESSIONS);
  expect(committed().schema).toBe('honey-cup-facts/1');
  expect(committed().report_eligible).toBe(false);
});

test('rebuilding reproduces the committed honey-cup-facts.json byte for byte', () => {
  expect(serialise(build(HONEYCUP, {}, digests()))).toBe(committedText());
}, 600_000);

test('matched_harddrop equals opener-facts.json\'s Honey Cup exact in every (session, player) cell', () => {
  const { cells, total } = checkFlagAgainstOpenerFacts(committed(), SESSIONS, ROOT, 'honey_cup', 'matched_harddrop');
  expect(cells).toBe(2 * SESSIONS.length);
  expect(total).toBeGreaterThan(0);
});

test('the named lists are exactly what the artefact holds, cell by cell', () => {
  const L = committed().lists;
  const pairs: [string, string[], string[]][] = [
    ['j_hold_bag1', L.j_hold_bag1, J_HOLD_BAG1],
    ['j_placed_elsewhere_bag1', L.j_placed_elsewhere_bag1, J_PLACED_ELSEWHERE_BAG1],
    ['tst_donate', L.tst_donate, TST_DONATE_CASES],
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
  // the lists are derived from the cases, and the cases agree with them
  const C = committed().cases;
  expect(C.filter((c: any) => c.bag1.node === 'bag1.j_hold').map(caseName).sort()).toEqual([...J_HOLD_BAG1].sort());
  expect(C.filter((c: any) => c.pc?.off_page_under).length).toBe(PC_OFF_PAGE.length);
});

test('per-node counts, the mirror split and the page-condition tallies are the measured ones', () => {
  const art = committed();
  for (const [id, n] of Object.entries(NODE_CASES))
    expect(art.nodes.find((x: any) => x.id === id)?.cases, id).toBe(n);
  const mirrored: Record<string, number> = {};
  for (const c of art.cases) if (c.bag1.mirrored) mirrored[c.player] = (mirrored[c.player] ?? 0) + 1;
  expect(mirrored).toEqual(MIRRORED_BAG1);
  expect(art.conditions).toEqual(CONDITIONS);
  // every node of the routes JSON is in the artefact, measured or with its reason
  const routes = JSON.parse(readFileSync(HONEYCUP.routesPath, 'utf8'));
  expect(art.nodes.map((n: any) => n.id)).toEqual([...routes.nodes.map((n: any) => n.id), 'bag1.j_placed_elsewhere']);
  expect(art.nodes.find((n: any) => n.id === 'bag1.l_hold').why).toBe('mirror_of: bag1.j_hold');
});

test('the case key order is pinned, and bag-3 lists are scoped by the form\'s GROUP', () => {
  const art = committed();
  for (const c of art.cases) {
    expect(Object.keys(c)).toEqual(CASE_KEYS);
    expect(Object.keys(c.bag1)).toEqual(BAG1_KEYS);
    if (c.bag2) expect(Object.keys(c.bag2)).toEqual(BAG2_KEYS);
  }
  const routes = JSON.parse(readFileSync(HONEYCUP.routesPath, 'utf8'));
  const parent = new Map(routes.nodes.map((n: any) => [n.id, n.parent]));
  const withPc = art.cases.filter((c: any) => c.pc?.node);
  expect(withPc.length).toBeGreaterThan(0);
  for (const c of withPc) {
    expect(c.bag2.node, caseName(c)).toMatch(/^2\.ideal#\d$/);
    expect(parent.get(c.pc.node), caseName(c)).toBe('2.ideal');
  }
  // the strip path is exercised: a matched bag 2 that needed garbage stripped
  expect(art.cases.some((c: any) => c.bag2?.node && c.bag2.garbage_rows_stripped > 0)).toBe(true);
});

test('every case and every named entry resolves to a real round with its match POSITION', () => {
  checkPositions(committed(), SESSIONS, ROOT,
    [...J_HOLD_BAG1, ...J_PLACED_ELSEWHERE_BAG1, ...TST_DONATE_CASES, ...BAG2_GARBAGE_STRIPPED,
     ...BAG2_NONE_TST_BEFORE_COMPLETE, ...BAG2_NONE_EXTRA_PIECE, ...BAG2_NONE_MOVED_PIECE, ...PC_OFF_PAGE]);
});

// ── mutants: each must turn this file red ───────────────────────────────────────────────────

const count = (o: any, id: string) => o.nodes.find((n: any) => n.id === id).cases;
const opp = (o: any, id: string) => o.nodes.find((n: any) => n.id === id).opportunities;
const pcs = (o: any) => o.cases.filter((c: any) => c.pc?.node).length;
const MUTANTS: [string, Mutants, (o: any) => void][] = [
  ['bag-3 scoped by the bag-2 node, not its group', { noGroupScope: true }, o => {
    expect(pcs(o)).toBe(0);
    expect(o.lists.pc_off_page.length).toBeGreaterThan(PC_OFF_PAGE.length);
  }],
  ['garbage refused instead of stripped at bag 2', { noGarbageStrip: true }, o => {
    expect(count(o, '2.ideal#4') + count(o, '2.compromise')).toBeLessThan(NODE_CASES['2.ideal#4']! + NODE_CASES['2.compromise']!);
    expect(o.lists.bag2_garbage_stripped).toEqual([]);
  }],
  ['the hold split removed', { noLock7Test: true }, o => {
    expect(o.lists.j_hold_bag1.length).toBe(J_HOLD_BAG1.length + J_PLACED_ELSEWHERE_BAG1.length);
    expect(o.lists.j_placed_elsewhere_bag1).toEqual([]);
  }],
  ['the hold split made mirror-unaware', { lock7MirrorUnaware: true }, o => {
    expect(o.lists.j_hold_bag1.length).toBeGreaterThan(J_HOLD_BAG1.length);
    expect(o.lists.j_placed_elsewhere_bag1.length).toBeLessThan(J_PLACED_ELSEWHERE_BAG1.length);
  }],
  ['the hold stage tried before the placed one', { zHoldFirst: true },
   o => expect(o.lists.j_placed_elsewhere_bag1.length).toBeGreaterThan(J_PLACED_ELSEWHERE_BAG1.length)],
  ['mirroring disabled', { noMirror: true }, o => expect(count(o, 'bag1.j_right')).toBeLessThan(NODE_CASES['bag1.j_right']!)],
  ['bag 2 sampled one lock early', { bag2Early: true },
   o => expect(count(o, '2.ideal#4') + count(o, '2.compromise')).toBe(0)],
  ['the J<->L / S<->Z swap removed from the mirrored condition', { noSwap: true },
   o => expect(o.conditions).not.toEqual(CONDITIONS)],
  ['any Perfect Clear, whatever its line count', { pcLinesOff: true },
   o => expect(o.cases.filter((c: any) => c.pc).length).toBeGreaterThan(committed().cases.filter((c: any) => c.pc).length)],
  ['the garbage stop removed', { noGarbageStop: true },
   o => expect(opp(o, 'bag1.j_hold')).toBeGreaterThan(opp(committed(), 'bag1.j_hold'))],
  ['match taken from the filename-sort index', { matchFromFilename: true },
   o => expect(o.lists.j_hold_bag1).not.toEqual(committed().lists.j_hold_bag1)],
];

test('every mutant changes the artefact, with the symptom its rule predicts', () => {
  const base = committedText();
  for (const [what, mut, symptom] of MUTANTS) {
    const o = build(HONEYCUP, mut, digests());
    expect(serialise(o) === base, what).toBe(false);
    symptom(o);
  }
}, 600_000);

test('a PC matched by occupancy alone is ambiguous and throws instead of choosing', () => {
  // the fifteen patterns share one occupancy: without colour, every PC matches all of them
  expect(() => build(HONEYCUP, { noColour: true }, digests())).toThrow(/PC matches/);
}, 600_000);

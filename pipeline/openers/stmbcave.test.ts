/**
 * The STMB Cave technique artefact (`analysis/stmbcave-facts.json`, from `pipeline/sim/emit-technique-facts.ts
 * --technique stmbcave`; the rules are the shared `technique-facts.ts`, the profile
 * `technique-profile-stmbcave.ts`, the shape the gated `pipeline/openers/stmbcave-technique.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count in every session and
 *      for every player (`donation.check`, `donation.players`), as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN: `windowMatch` over every U-slot board of every committed `*-routes.json` fires on
 *      exactly the boards the gate records (`cross_source.fires` + `also`).
 *   4. THE OPENER METRIC (`opener-facts.json` `stmb_cave`, harddrop's definition: a >= 3-wide gap under a
 *      TSD overlapping the T's columns). Its `caveAt` is re-implemented HERE (importing
 *      `emit-opener-facts.ts` runs a session) and must reproduce every session's per-player
 *      width_ge_3 / min_depth_ge_2 / in_opener / mid_game exactly; then every STMB Cave hit is one of its
 *      caves, and every one of its caves that is not a hit is NAMED with the geometric reason, re-derived.
 *   5. WHAT DISCRIMINATES: the window's top two rows are the rows the TSD clears, so at the opportunity they
 *      are entailed (NaiveClauseForced; the nub row is the cave's roof, RoofForced). Measured: the cave row
 *      alone, with the T's anchor, gives exactly the headline's hits.
 *   6. THE SDPC SPIN CROSS-CHECK: every round whose SDPC Spin route reached its STMB Cave (`3.first.cave`
 *      in `sdpcspin-facts.json`, harddrop's drawing) with the node verified is a hit at its next T lock;
 *      the rest are named with the reason they are not measured.
 *   7. NAMED lists, not bounds; pinned per-player figures; mutants (the equivalent ones named, measured,
 *      asserted to STAY byte-identical).
 *
 * window_off_board is not listed entry by entry: it is every flat, nub-down T at a TSD whose window leaves
 * the board before the matcher found a mismatch, thousands of them (a TSD on the floor has no row under it).
 * It is pinned per player as a count, and every entry is checked to be such a T with its window off the
 * board in at least one hand and not a hit.
 *
 * Run: bun test pipeline/openers/stmbcave.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest }
  from '../sim/technique-facts.ts';
import { STMBCAVE } from '../sim/technique-profile-stmbcave.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22', '2026-10-29']);
const ART_PATH = `${import.meta.dir}/../../analysis/stmbcave-facts.json`;
const TR = JSON.parse(readFileSync(STMBCAVE.transcriptionPath, 'utf8'));
const H = 40;

/** Every hit: the flat T into the page's window, as drawn or mirrored. */
const STMBCAVE_HITS: string[] = [
  "2026-07-22 m3r7 yachi lock 22", "2026-07-22 m6r3 yachi lock 25 (mirrored)", "2026-07-22 m8r5 yachi lock 54 (mirrored)",
  "2026-07-22 m9r7 yachi lock 52", "2026-07-24 m3r1 yachi lock 106", "2026-07-24 m5r5 yachi lock 40",
  "2026-07-24 m7r3 yachi lock 110 (mirrored)", "2026-07-24 m7r3 yachi lock 114", "2026-07-28 m6r2 pinglamb lock 23",
  "2026-07-28 m6r8 yachi lock 35 (mirrored)", "2026-07-28 m8r3 pinglamb lock 83 (mirrored)", "2026-08-01 m4r2 yachi lock 33",
  "2026-08-01 m6r5 yachi lock 128", "2026-08-01 m7r6 yachi lock 30", "2026-08-09 m3r3 pinglamb lock 25 (mirrored)",
  "2026-08-09 m3r4 pinglamb lock 24 (mirrored)", "2026-08-09 m3r4 pinglamb lock 60", "2026-08-09 m3r6 pinglamb lock 26 (mirrored)",
  "2026-08-14 m1r5 yachi lock 129", "2026-08-14 m4r7 pinglamb lock 23 (mirrored)", "2026-08-14 m5r8 yachi lock 32 (mirrored)",
  "2026-08-14 m9r1 pinglamb lock 34", "2026-08-14 m11r8 yachi lock 96", "2026-08-19 m1r5 yachi lock 40",
  "2026-08-19 m6r1 yachi lock 53 (mirrored)", "2026-08-19 m6r6 yachi lock 22 (mirrored)", "2026-08-19 m8r6 pinglamb lock 27 (mirrored)",
  "2026-08-19 m9r5 pinglamb lock 20 (mirrored)", "2026-08-19 m10r1 pinglamb lock 33 (mirrored)", "2026-08-19 m10r7 pinglamb lock 116",
  "2026-08-25 m1r5 pinglamb lock 22", "2026-08-25 m3r5 pinglamb lock 54", "2026-08-25 m5r1 pinglamb lock 65",
  "2026-08-25 m5r7 pinglamb lock 24 (mirrored)", "2026-08-25 m5r8 pinglamb lock 78", "2026-08-25 m7r5 pinglamb lock 134 (mirrored)",
  "2026-08-25 m8r9 pinglamb lock 76", "2026-08-25 m8r9 pinglamb lock 90 (mirrored)", "2026-09-03 m2r8 yachi lock 25",
  "2026-09-03 m3r4 pinglamb lock 96", "2026-09-03 m5r4 pinglamb lock 109 (mirrored)", "2026-09-03 m6r2 yachi lock 18",
  "2026-09-10 m2r6 yachi lock 34 (mirrored)", "2026-09-10 m8r4 yachi lock 60", "2026-09-11 m1r4 yachi lock 58",
  "2026-09-11 m2r5 yachi lock 217 (mirrored)", "2026-09-17 m2r6 yachi lock 88", "2026-09-17 m3r2 pinglamb lock 184 (mirrored)",
  "2026-09-17 m4r1 pinglamb lock 75 (mirrored)", "2026-09-17 m6r4 pinglamb lock 25", "2026-09-18 m1r7 pinglamb lock 75 (mirrored)",
  "2026-09-18 m2r4 pinglamb lock 23 (mirrored)", "2026-09-18 m3r4 yachi lock 42", "2026-09-18 m8r7 pinglamb lock 34 (mirrored)",
  "2026-09-18 m9r5 yachi lock 48 (mirrored)", "2026-09-18 m11r1 yachi lock 104", "2026-09-18 m13r6 pinglamb lock 150 (mirrored)",
  "2026-09-18 m13r7 pinglamb lock 69", "2026-09-18 m13r7 yachi lock 31", "2026-09-18 m14r2 yachi lock 66",
  "2026-09-18 m16r2 yachi lock 30 (mirrored)", "2026-09-19 m3r1 yachi lock 103 (mirrored)", "2026-09-19 m3r4 yachi lock 93 (mirrored)",
  "2026-09-19 m5r1 yachi lock 27", "2026-09-19 m6r2 yachi lock 152", "2026-09-19 m6r4 pinglamb lock 45",
  "2026-09-19 m6r5 yachi lock 86", "2026-09-19 m8r7 pinglamb lock 50 (mirrored)", "2026-09-19 m11r2 yachi lock 32",
  "2026-09-19 m12r5 pinglamb lock 39", "2026-09-19 m12r6 yachi lock 94", "2026-09-19 m15r8 pinglamb lock 24 (mirrored)",
  "2026-09-19 m16r4 yachi lock 82", "2026-09-19 m18r5 pinglamb lock 51", "2026-09-19 m19r6 pinglamb lock 54",
  "2026-09-19 m20r8 pinglamb lock 96", "2026-10-03 m2r3 yachi lock 21 (mirrored)", "2026-10-03 m3r4 pinglamb lock 23 (mirrored)",
  "2026-10-03 m3r8 yachi lock 24", "2026-10-03 m4r1 yachi lock 28", "2026-10-03 m4r2 yachi lock 21",
  "2026-10-03 m4r7 yachi lock 27", "2026-10-03 m5r6 yachi lock 28", "2026-10-03 m6r3 pinglamb lock 26",
  "2026-10-03 m6r7 yachi lock 286 (mirrored)", "2026-10-03 m10r6 pinglamb lock 88", "2026-10-03 m10r6 pinglamb lock 136",
  "2026-10-03 m11r2 yachi lock 66 (mirrored)", "2026-10-03 m13r4 yachi lock 32", "2026-10-03 m14r2 pinglamb lock 60",
  "2026-10-03 m17r6 yachi lock 117", "2026-10-03 m20r2 pinglamb lock 102", "2026-10-09 m1r5 yachi lock 27",
  "2026-10-09 m1r6 pinglamb lock 47", "2026-10-09 m1r6 pinglamb lock 55 (mirrored)", "2026-10-09 m1r7 yachi lock 28 (mirrored)",
  "2026-10-09 m1r9 pinglamb lock 86", "2026-10-09 m2r5 yachi lock 80 (mirrored)", "2026-10-09 m3r1 yachi lock 31",
  "2026-10-09 m3r8 pinglamb lock 58 (mirrored)", "2026-10-09 m3r8 yachi lock 28", "2026-10-09 m4r4 yachi lock 27",
  "2026-10-09 m4r8 yachi lock 27", "2026-10-09 m5r1 yachi lock 27", "2026-10-09 m5r3 yachi lock 31",
  "2026-10-09 m5r3 yachi lock 38 (mirrored)", "2026-10-09 m5r3 yachi lock 145", "2026-10-09 m6r1 pinglamb lock 30 (mirrored)",
  "2026-10-09 m6r5 yachi lock 27", "2026-10-09 m7r1 yachi lock 27", "2026-10-09 m7r9 pinglamb lock 99",
  "2026-10-09 m8r1 yachi lock 28", "2026-10-09 m8r2 yachi lock 30", "2026-10-09 m8r7 yachi lock 28",
  "2026-10-09 m9r9 yachi lock 31", "2026-10-09 m10r3 yachi lock 56 (mirrored)", "2026-10-09 m11r1 yachi lock 27",
  "2026-10-09 m11r6 yachi lock 33", "2026-10-12 m1r3 yachi lock 145 (mirrored)", "2026-10-12 m3r4 yachi lock 27",
  "2026-10-12 m4r3 yachi lock 21", "2026-10-12 m6r5 pinglamb lock 23", "2026-10-20 m1r3 yachi lock 68",
  "2026-10-20 m1r4 yachi lock 27", "2026-10-20 m1r5 yachi lock 40", "2026-10-20 m2r3 yachi lock 36 (mirrored)",
  "2026-10-20 m3r5 yachi lock 27", "2026-10-20 m4r7 yachi lock 178", "2026-10-22 m1r3 yachi lock 32",
  "2026-10-22 m1r8 yachi lock 82", "2026-10-22 m3r5 yachi lock 249 (mirrored)", "2026-10-22 m4r4 yachi lock 224 (mirrored)",
  "2026-10-22 m8r1 yachi lock 33 (mirrored)", "2026-10-29 m1r6 yachi lock 41 (mirrored)", "2026-10-29 m2r2 pinglamb lock 27 (mirrored)",
  "2026-10-29 m4r4 pinglamb lock 25 (mirrored)", "2026-10-29 m4r6 yachi lock 294", "2026-10-29 m8r5 pinglamb lock 145",
  "2026-10-29 m9r4 yachi lock 38 (mirrored)", "2026-10-29 m9r9 yachi lock 30",
];
const FOLLOWUP_NOT_FIRED: string[] = [
  "2026-07-22 m3r7 yachi lock 22 (next_t_elsewhere at lock 24)", "2026-07-22 m6r3 yachi lock 25 (slot_filled_before_t at lock 26)",
  "2026-07-22 m8r5 yachi lock 54 (slot_filled_before_t at lock 55)", "2026-07-22 m9r7 yachi lock 52 (slot_filled_before_t at lock 53)",
  "2026-07-24 m3r1 yachi lock 106 (slot_filled_before_t at lock 107)", "2026-07-24 m5r5 yachi lock 40 (slot_filled_before_t at lock 41)",
  "2026-07-24 m7r3 yachi lock 110 (next_t_elsewhere at lock 114)", "2026-07-24 m7r3 yachi lock 114 (slot_filled_before_t at lock 115)",
  "2026-07-28 m6r2 pinglamb lock 23 (slot_filled_before_t at lock 24)", "2026-07-28 m8r3 pinglamb lock 83 (slot_filled_before_t at lock 84)",
  "2026-08-01 m4r2 yachi lock 33 (slot_filled_before_t at lock 34)", "2026-08-01 m6r5 yachi lock 128 (slot_filled_before_t at lock 129)",
  "2026-08-01 m7r6 yachi lock 30 (slot_filled_before_t at lock 31)", "2026-08-09 m3r3 pinglamb lock 25 (slot_filled_before_t at lock 29)",
  "2026-08-09 m3r4 pinglamb lock 24 (slot_filled_before_t at lock 25)", "2026-08-09 m3r4 pinglamb lock 60 (slot_filled_before_t at lock 61)",
  "2026-08-09 m3r6 pinglamb lock 26 (slot_filled_before_t at lock 27)", "2026-08-14 m4r7 pinglamb lock 23 (next_t_elsewhere at lock 24)",
  "2026-08-14 m5r8 yachi lock 32 (slot_filled_before_t at lock 34)", "2026-08-14 m9r1 pinglamb lock 34 (slot_filled_before_t at lock 35)",
  "2026-08-14 m11r8 yachi lock 96 (slot_filled_before_t at lock 97)", "2026-08-19 m1r5 yachi lock 40 (next_t_elsewhere at lock 44)",
  "2026-08-19 m6r6 yachi lock 22 (slot_filled_before_t at lock 23)", "2026-08-19 m8r6 pinglamb lock 27 (slot_filled_before_t at lock 29)",
  "2026-08-19 m9r5 pinglamb lock 20 (slot_filled_before_t at lock 22)", "2026-08-19 m10r1 pinglamb lock 33 (slot_filled_before_t at lock 34)",
  "2026-08-19 m10r7 pinglamb lock 116 (slot_filled_before_t at lock 120)", "2026-08-25 m1r5 pinglamb lock 22 (next_t_elsewhere at lock 26)",
  "2026-08-25 m3r5 pinglamb lock 54 (slot_filled_before_t at lock 55)", "2026-08-25 m5r1 pinglamb lock 65 (slot_filled_before_t at lock 66)",
  "2026-08-25 m5r7 pinglamb lock 24 (next_t_elsewhere at lock 32)", "2026-08-25 m5r8 pinglamb lock 78 (slot_filled_before_t at lock 79)",
  "2026-08-25 m7r5 pinglamb lock 134 (slot_filled_before_t at lock 135)", "2026-08-25 m8r9 pinglamb lock 76 (slot_filled_before_t at lock 77)",
  "2026-08-25 m8r9 pinglamb lock 90 (slot_filled_before_t at lock 91)", "2026-09-03 m2r8 yachi lock 25 (slot_filled_before_t at lock 27)",
  "2026-09-03 m3r4 pinglamb lock 96 (slot_filled_before_t at lock 97)", "2026-09-03 m5r4 pinglamb lock 109 (slot_filled_before_t at lock 111)",
  "2026-09-03 m6r2 yachi lock 18 (slot_filled_before_t at lock 20)", "2026-09-10 m2r6 yachi lock 34 (slot_filled_before_t at lock 35)",
  "2026-09-10 m8r4 yachi lock 60 (slot_filled_before_t at lock 61)", "2026-09-11 m1r4 yachi lock 58 (slot_filled_before_t at lock 60)",
  "2026-09-11 m2r5 yachi lock 217 (slot_filled_before_t at lock 219)", "2026-09-17 m2r6 yachi lock 88 (slot_filled_before_t at lock 90)",
  "2026-09-17 m3r2 pinglamb lock 184 (slot_filled_before_t at lock 185)", "2026-09-17 m4r1 pinglamb lock 75 (slot_filled_before_t at lock 76)",
  "2026-09-17 m6r4 pinglamb lock 25 (slot_filled_before_t at lock 26)", "2026-09-18 m1r7 pinglamb lock 75 (slot_filled_before_t at lock 76)",
  "2026-09-18 m2r4 pinglamb lock 23 (slot_filled_before_t at lock 24)", "2026-09-18 m3r4 yachi lock 42 (slot_filled_before_t at lock 43)",
  "2026-09-18 m8r7 pinglamb lock 34 (slot_filled_before_t at lock 38)", "2026-09-18 m9r5 yachi lock 48 (slot_filled_before_t at lock 49)",
  "2026-09-18 m11r1 yachi lock 104 (slot_filled_before_t at lock 105)", "2026-09-18 m13r6 pinglamb lock 150 (slot_filled_before_t at lock 151)",
  "2026-09-18 m13r7 pinglamb lock 69 (slot_filled_before_t at lock 70)", "2026-09-18 m13r7 yachi lock 31 (slot_filled_before_t at lock 32)",
  "2026-09-18 m14r2 yachi lock 66 (slot_filled_before_t at lock 67)", "2026-09-18 m16r2 yachi lock 30 (slot_filled_before_t at lock 33)",
  "2026-09-19 m3r1 yachi lock 103 (slot_filled_before_t at lock 104)", "2026-09-19 m3r4 yachi lock 93 (slot_filled_before_t at lock 94)",
  "2026-09-19 m5r1 yachi lock 27 (slot_filled_before_t at lock 28)", "2026-09-19 m6r2 yachi lock 152 (slot_filled_before_t at lock 154)",
  "2026-09-19 m6r4 pinglamb lock 45 (slot_filled_before_t at lock 47)", "2026-09-19 m6r5 yachi lock 86 (slot_filled_before_t at lock 88)",
  "2026-09-19 m8r7 pinglamb lock 50 (slot_filled_before_t at lock 51)", "2026-09-19 m11r2 yachi lock 32 (slot_filled_before_t at lock 36)",
  "2026-09-19 m12r5 pinglamb lock 39 (slot_filled_before_t at lock 40)", "2026-09-19 m12r6 yachi lock 94 (slot_filled_before_t at lock 95)",
  "2026-09-19 m15r8 pinglamb lock 24 (slot_filled_before_t at lock 25)", "2026-09-19 m16r4 yachi lock 82 (slot_filled_before_t at lock 84)",
  "2026-09-19 m18r5 pinglamb lock 51 (slot_filled_before_t at lock 53)", "2026-09-19 m19r6 pinglamb lock 54 (slot_filled_before_t at lock 55)",
  "2026-09-19 m20r8 pinglamb lock 96 (slot_filled_before_t at lock 97)", "2026-10-03 m2r3 yachi lock 21 (next_t_elsewhere at lock 31)",
  "2026-10-03 m3r4 pinglamb lock 23 (next_t_elsewhere at lock 24)", "2026-10-03 m3r8 yachi lock 24 (slot_filled_before_t at lock 26)",
  "2026-10-03 m4r1 yachi lock 28 (slot_filled_before_t at lock 29)", "2026-10-03 m4r2 yachi lock 21 (slot_filled_before_t at lock 22)",
  "2026-10-03 m4r7 yachi lock 27 (next_t_elsewhere at lock 31)", "2026-10-03 m5r6 yachi lock 28 (slot_filled_before_t at lock 29)",
  "2026-10-03 m6r3 pinglamb lock 26 (slot_filled_before_t at lock 27)", "2026-10-03 m6r7 yachi lock 286 (slot_filled_before_t at lock 287)",
  "2026-10-03 m10r6 pinglamb lock 88 (slot_filled_before_t at lock 89)", "2026-10-03 m10r6 pinglamb lock 136 (slot_filled_before_t at lock 137)",
  "2026-10-03 m11r2 yachi lock 66 (slot_filled_before_t at lock 68)", "2026-10-03 m13r4 yachi lock 32 (slot_filled_before_t at lock 33)",
  "2026-10-03 m14r2 pinglamb lock 60 (slot_filled_before_t at lock 61)", "2026-10-03 m17r6 yachi lock 117 (slot_filled_before_t at lock 121)",
  "2026-10-03 m20r2 pinglamb lock 102 (slot_filled_before_t at lock 103)", "2026-10-09 m1r5 yachi lock 27 (next_t_elsewhere at lock 30)",
  "2026-10-09 m1r6 pinglamb lock 47 (next_t_elsewhere at lock 55)", "2026-10-09 m1r6 pinglamb lock 55 (slot_filled_before_t at lock 56)",
  "2026-10-09 m1r7 yachi lock 28 (slot_filled_before_t at lock 29)", "2026-10-09 m1r9 pinglamb lock 86 (round_ended)",
  "2026-10-09 m2r5 yachi lock 80 (slot_filled_before_t at lock 81)", "2026-10-09 m3r1 yachi lock 31 (round_ended)",
  "2026-10-09 m3r8 yachi lock 28 (next_t_elsewhere at lock 32)", "2026-10-09 m4r4 yachi lock 27 (next_t_elsewhere at lock 29)",
  "2026-10-09 m4r8 yachi lock 27 (next_t_elsewhere at lock 28)", "2026-10-09 m5r1 yachi lock 27 (next_t_elsewhere at lock 29)",
  "2026-10-09 m5r3 yachi lock 31 (slot_filled_before_t at lock 32)", "2026-10-09 m5r3 yachi lock 38 (slot_filled_before_t at lock 39)",
  "2026-10-09 m5r3 yachi lock 145 (slot_filled_before_t at lock 146)", "2026-10-09 m6r1 pinglamb lock 30 (next_t_elsewhere at lock 31)",
  "2026-10-09 m6r5 yachi lock 27 (next_t_elsewhere at lock 32)", "2026-10-09 m7r1 yachi lock 27 (next_t_elsewhere at lock 30)",
  "2026-10-09 m7r9 pinglamb lock 99 (slot_filled_before_t at lock 100)", "2026-10-09 m8r1 yachi lock 28 (slot_filled_before_t at lock 29)",
  "2026-10-09 m8r2 yachi lock 30 (slot_filled_before_t at lock 32)", "2026-10-09 m8r7 yachi lock 28 (slot_filled_before_t at lock 29)",
  "2026-10-09 m9r9 yachi lock 31 (slot_filled_before_t at lock 38)", "2026-10-09 m10r3 yachi lock 56 (slot_filled_before_t at lock 57)",
  "2026-10-09 m11r1 yachi lock 27 (next_t_elsewhere at lock 33)", "2026-10-09 m11r6 yachi lock 33 (slot_filled_before_t at lock 34)",
  "2026-10-12 m1r3 yachi lock 145 (slot_filled_before_t at lock 146)", "2026-10-12 m3r4 yachi lock 27 (next_t_elsewhere at lock 28)",
  "2026-10-12 m4r3 yachi lock 21 (next_t_elsewhere at lock 24)", "2026-10-12 m6r5 pinglamb lock 23 (next_t_elsewhere at lock 24)",
  "2026-10-20 m1r3 yachi lock 68 (slot_filled_before_t at lock 69)", "2026-10-20 m1r4 yachi lock 27 (next_t_elsewhere at lock 28)",
  "2026-10-20 m1r5 yachi lock 40 (slot_filled_before_t at lock 41)", "2026-10-20 m2r3 yachi lock 36 (slot_filled_before_t at lock 37)",
  "2026-10-20 m3r5 yachi lock 27 (next_t_elsewhere at lock 33)", "2026-10-20 m4r7 yachi lock 178 (slot_filled_before_t at lock 180)",
  "2026-10-22 m1r3 yachi lock 32 (slot_filled_before_t at lock 34)", "2026-10-22 m1r8 yachi lock 82 (slot_filled_before_t at lock 83)",
  "2026-10-22 m3r5 yachi lock 249 (slot_filled_before_t at lock 250)", "2026-10-22 m4r4 yachi lock 224 (round_ended)",
  "2026-10-22 m8r1 yachi lock 33 (slot_filled_before_t at lock 34)",
  "2026-10-29 m1r6 yachi lock 41 (slot_filled_before_t at lock 42)", "2026-10-29 m2r2 pinglamb lock 27 (slot_filled_before_t at lock 31)",
  "2026-10-29 m4r4 pinglamb lock 25 (slot_filled_before_t at lock 26)", "2026-10-29 m4r6 yachi lock 294 (slot_filled_before_t at lock 295)",
  "2026-10-29 m8r5 pinglamb lock 145 (slot_filled_before_t at lock 147)", "2026-10-29 m9r4 yachi lock 38 (slot_filled_before_t at lock 39)",
  "2026-10-29 m9r9 yachi lock 30 (slot_filled_before_t at lock 31)",
];
const STMBCAVE_IN_OPENER: string[] = [
  "2026-08-19 m9r5 pinglamb lock 20", "2026-09-03 m6r2 yachi lock 18", "2026-10-03 m2r3 yachi lock 21",
  "2026-10-03 m4r2 yachi lock 21", "2026-10-12 m4r3 yachi lock 21",
];

const GARBAGE_IN_WINDOW: string[] = [];
const RECON_DROPPED_TSD: string[] = [];

/** The opener metric's caves (>= 3 wide, overlapping the T) that are NOT STMB Cave hits, each with the
 *  geometric reason this test re-derives: `centred` the gap is the T's own three columns (the nub over its
 *  middle, nothing to hook an S over); `arm_only` the gap reaches under one arm only, the nub on a filled
 *  cell; `wall` the gap starts under the nub but the window's two cells behind the nub leave the board. */
const CAVE_METRIC_ONLY: string[] = [
  "2026-07-24 m2r3 pinglamb lock 131 (centred, width 3, depth 1)", "2026-07-24 m6r5 pinglamb lock 67 (centred, width 3, depth 1)",
  "2026-07-28 m7r1 yachi lock 98 (centred, width 3, depth 1)", "2026-07-28 m7r6 pinglamb lock 33 (centred, width 3, depth 1)",
  "2026-08-01 m1r4 pinglamb lock 34 (centred, width 3, depth 1)", "2026-08-01 m3r5 pinglamb lock 24 (centred, width 3, depth 1)",
  "2026-08-01 m3r7 pinglamb lock 35 (centred, width 3, depth 1)", "2026-08-01 m3r8 pinglamb lock 34 (centred, width 3, depth 1)",
  "2026-08-01 m5r7 pinglamb lock 60 (centred, width 3, depth 1)", "2026-08-09 m6r2 pinglamb lock 82 (centred, width 3, depth 1)",
  "2026-08-09 m6r2 pinglamb lock 93 (centred, width 3, depth 1)", "2026-08-09 m6r7 pinglamb lock 165 (wall, width 3, depth 1)",
  "2026-08-14 m10r6 yachi lock 23 (centred, width 3, depth 1)", "2026-08-14 m3r4 yachi lock 208 (centred, width 3, depth 1)",
  "2026-08-14 m4r5 yachi lock 47 (centred, width 3, depth 1)", "2026-08-14 m4r8 yachi lock 83 (centred, width 3, depth 1)",
  "2026-08-19 m2r5 pinglamb lock 37 (centred, width 3, depth 1)", "2026-08-19 m4r1 pinglamb lock 25 (centred, width 3, depth 1)",
  "2026-08-19 m9r6 yachi lock 17 (arm_only, width 3, depth 1)", "2026-08-25 m2r7 pinglamb lock 116 (centred, width 3, depth 1)",
  "2026-08-25 m4r2 pinglamb lock 11 (centred, width 3, depth 1)", "2026-08-25 m6r4 pinglamb lock 18 (centred, width 3, depth 1)",
  "2026-09-03 m2r2 pinglamb lock 81 (centred, width 3, depth 1)", "2026-09-03 m4r2 pinglamb lock 67 (centred, width 3, depth 1)",
  "2026-09-10 m5r9 pinglamb lock 36 (centred, width 3, depth 1)", "2026-09-11 m2r5 pinglamb lock 133 (centred, width 3, depth 1)",
  "2026-09-11 m2r6 pinglamb lock 50 (centred, width 3, depth 1)", "2026-09-11 m4r1 pinglamb lock 148 (centred, width 3, depth 1)",
  "2026-09-11 m4r2 yachi lock 26 (centred, width 3, depth 1)", "2026-09-17 m7r4 pinglamb lock 48 (centred, width 3, depth 1)",
  "2026-09-18 m15r1 yachi lock 64 (centred, width 3, depth 1)", "2026-09-18 m9r3 yachi lock 202 (centred, width 3, depth 1)",
  "2026-09-19 m14r4 yachi lock 109 (centred, width 3, depth 1)", "2026-09-19 m14r6 pinglamb lock 37 (centred, width 3, depth 1)",
  "2026-09-19 m17r2 pinglamb lock 32 (centred, width 3, depth 1)", "2026-09-19 m1r8 pinglamb lock 64 (centred, width 3, depth 1)",
  "2026-09-19 m2r3 pinglamb lock 45 (centred, width 3, depth 1)", "2026-10-03 m13r5 pinglamb lock 43 (arm_only, width 3, depth 1)",
  "2026-10-03 m7r7 yachi lock 80 (centred, width 3, depth 1)", "2026-10-09 m11r3 yachi lock 74 (centred, width 3, depth 1)",
  "2026-10-09 m1r9 yachi lock 45 (centred, width 3, depth 1)", "2026-10-09 m4r7 pinglamb lock 89 (centred, width 3, depth 1)",
  "2026-10-09 m6r5 pinglamb lock 36 (centred, width 3, depth 1)", "2026-10-09 m7r5 pinglamb lock 37 (centred, width 3, depth 1)",
  "2026-10-29 m3r5 yachi lock 40 (centred, width 3, depth 1)", "2026-10-29 m5r5 pinglamb lock 36 (centred, width 3, depth 1)",
  "2026-10-29 m6r6 pinglamb lock 46 (centred, width 3, depth 1)", "2026-10-29 m7r2 yachi lock 33 (arm_only, width 3, depth 1)",
  "2026-10-29 m8r6 yachi lock 80 (centred, width 3, depth 1)", "2026-10-29 m9r4 yachi lock 73 (centred, width 3, depth 1)",
  "2026-10-29 m9r8 yachi lock 78 (arm_only, width 3, depth 1)",
];

/** The SDPC Spin rounds that reached its STMB Cave with the node verified: a hit at the next T lock. */
const SDPC_CAVE_HITS: string[] = [
  "2026-10-03 m4r7 yachi lock 27", "2026-10-09 m1r5 yachi lock 27", "2026-10-09 m4r4 yachi lock 27",
  "2026-10-09 m4r8 yachi lock 27", "2026-10-09 m5r1 yachi lock 27", "2026-10-09 m6r5 yachi lock 27",
  "2026-10-09 m7r1 yachi lock 27", "2026-10-20 m1r4 yachi lock 27", "2026-10-20 m3r5 yachi lock 27",
];
/** The SDPC Spin rounds that reached it past their verified prefix: not measured, named. */
const SDPC_CAVE_UNSCORED: string[] = [
  "2026-10-03 m15r5 yachi (node at lock 26, verified to lock 20)",
];

/** Per player: the opportunity (scored full TSDs), split at the 0-based opener window. */
const TSD_DENOM = { pinglamb: { all: 5884, in_opener: 1162, mid_game: 4722 },
                    yachi: { all: 5340, in_opener: 1375, mid_game: 3965 } };
/** Per player: hits, their split, the mirrored ones, the follow-ups that fired. */
const HITS = { pinglamb: { all: 53, in_opener: 1, mid_game: 52, mirrored: 26, garbage_in_window: 0 },
               yachi: { all: 87, in_opener: 4, mid_game: 83, mirrored: 27, garbage_in_window: 0 } };
const FOLLOWUP_FIRED = { pinglamb: 1, yachi: 3 };
/** The controls (the same window at other spins; the ablations; the orientation baseline). */
const CONTROLS = {
  under: { TSS: { pinglamb: 2, yachi: 0 }, TST: { pinglamb: 0, yachi: 0 },
           mini_TSS: { pinglamb: 0, yachi: 0 }, mini_TSD: { pinglamb: 0, yachi: 0 } },
  ablation: { no_must_empty: { pinglamb: 4160, yachi: 3613 }, no_roof: { pinglamb: 53, yachi: 87 },
              t_overlap: { pinglamb: 100, yachi: 108 } },
  orientation_baseline: { pinglamb: 54, yachi: 73 },
};
/** window_off_board, per player: a count with a property check, not a list (see the header). */
const WINDOW_OFF_BOARD = { pinglamb: 2427, yachi: 2416 };

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
  noRoof: 'the window has no row above the T (it is the agreement box, whose top row is the T row), so there is no roof to drop',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(STMBCAVE, m, digests());
const nameOf = (d: TechDigest, lock: number) => `${d.session} m${d.match}r${d.round + 1} ${d.user} lock ${lock}`;
const hitKeys = () => new Set(art().hits.map((h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`));
const keyOf = (d: TechDigest, lock: number) => `${d.session}|${d.file}|${d.round}|${d.user}|${lock}`;

/** Every scored T-spin, exactly as the matcher scores it: inside the prefix, the reconstruction agreeing
 *  on a non-empty set of rows. */
function scored(d: TechDigest) {
  const out: { i: number; withT: boolean[][]; rows: number[]; lk: TechDigest['locks'][number]; board: string[] }[] = [];
  for (const t of d.tspins) {
    if (t.i > d.v) continue;
    const lk = d.locks[t.i]!;
    const withT = t.board.map(s => [...s].map(x => x !== '.'));
    for (const q of lk.cells) withT[q.row]![q.col] = true;
    const rows: number[] = [];
    for (let r = 0; r < H; r++) if (withT[r]!.every(Boolean)) rows.push(r);
    const theirs = [...lk.clearedRows].sort((a, b) => a - b);
    if (rows.length !== theirs.length || !rows.every((x, k) => x === theirs[k]) || !rows.length) continue;
    out.push({ i: t.i, withT, rows, lk, board: t.board });
  }
  return out;
}

/** harddrop's cave, as emit-opener-facts.ts `caveAt` computes it (a second copy, held to its counts). */
function caveAt(withT: boolean[][], cleared: number[], t: { col: number }[]) {
  if (cleared.length !== 2) return null;
  const under = Math.max(...cleared) + 1;
  if (under >= H) return null;
  const tc = new Set(t.map(q => q.col));
  let best: { width: number; minDepth: number; start: number; end: number } | null = null;
  let c = 0;
  while (c < 10) {
    if (withT[under]![c]) { c++; continue; }
    let e = c;
    while (e < 10 && !withT[under]![e]) e++;
    let overlaps = false;
    for (let k = c; k < e; k++) if (tc.has(k)) overlaps = true;
    if (overlaps && e - c >= 3) {
      let minDepth = Infinity;
      for (let k = c; k < e; k++) {
        let d = 0;
        for (let r = under; r < H && !withT[r]![k]; r++) d++;
        minDepth = Math.min(minDepth, d);
      }
      if (!best || e - c > best.width) best = { width: e - c, minDepth, start: c, end: e };
    }
    c = e;
  }
  return best;
}

/** A flat T pointing down: its nub, or null. */
function nubOf(cells: { row: number; col: number }[]) {
  const top = Math.min(...cells.map(q => q.row));
  const up = cells.filter(q => q.row === top), down = cells.filter(q => q.row !== top);
  if (up.length !== 3 || down.length !== 1) return null;
  const n = down[0]!, cs = up.map(q => q.col).sort((a, b) => a - b);
  if (n.row !== top + 1 || cs[0] !== n.col - 1 || cs[2] !== n.col + 1) return null;
  return n;
}

test('the committed artefact is what build() produces now (byte identity)', () => {
  expect(serialise(run({}))).toBe(readFileSync(ART_PATH, 'utf8'));
}, 600_000);

test('quarantined: report_eligible false, no claim ids', () => {
  const a = art();
  expect(a.report_eligible).toBe(false);
  expect(JSON.stringify(a)).not.toMatch(/data-claim|\b[CRG]\d{3}\b|✓/);
  expect(a.sessions).toEqual(SESSIONS);
  expect(a.cross_route).toBeUndefined();
});

test('the scored T-spins are the ones emit-opener-facts.ts scores (the third copy of the loop)', () => {
  const n = checkScoredAgainstOpenerFacts(art(), SESSIONS, ROOT);
  expect(n).toBe(15834);
  expect(art().check.reconstruction_disagreed).toBe(0);
});

test('the Python twin: windowMatch fires on exactly the routes boards the gate records', () => {
  const preps = TR.variants.flatMap((v: any) => prepare(TR, v));
  const got: string[] = [];
  const dir = `${import.meta.dir}`;
  for (const f of readdirSync(dir).filter(x => x.endsWith('-routes.json')).sort()) {
    for (const n of JSON.parse(readFileSync(`${dir}/${f}`, 'utf8')).nodes) {
      if (!n.rows) continue;
      const cells = n.rows.flatMap((r: string, i: number) => [...r].flatMap((ch, c) => ch === 'U' ? [{ row: i, col: c }] : []));
      if (cells.length !== 4) continue;
      const board = n.rows.map((r: string) => [...r].map(ch => ch === '-' || ch === 'U' ? '.' : 'X').join(''));
      for (const P of preps) if (windowMatch(board, cells, P)) got.push(`${f} ${n.id} ${P.id} ${P.mirrored}`);
    }
  }
  const want = [...TR.cross_source.fires, ...TR.cross_source.also]
    .map((e: any) => `${e.file} ${e.node} ${e.variant} ${e.mirrored}`);
  expect(got.sort()).toEqual(want.sort());
  expect(want.length).toBe(1);
});

test('the transcription the artefact read is the committed one, and its window is the gated one', () => {
  const v = TR.variants[0];
  expect(v.window_basis).toBe('agreement');
  expect(v.window).toEqual({ rows: [2, 4], cols: [1, 6] });
  expect(v.t_cells).toEqual([[2, 2], [2, 3], [2, 4], [3, 3]]);
  expect(v.roof_cells).toEqual([]);
});

test('named lists: every hit, every follow-up miss, the opener hits, the empty lists', () => {
  const L = art().lists;
  checkNamedList('stmbcave_hits', L.stmbcave_hits, STMBCAVE_HITS);
  checkNamedList('followup_not_fired', L.followup_not_fired, FOLLOWUP_NOT_FIRED);
  checkNamedList('garbage_in_window', L.garbage_in_window, GARBAGE_IN_WINDOW);
  checkNamedList('stmbcave_in_opener', L.stmbcave_in_opener, STMBCAVE_IN_OPENER);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, RECON_DROPPED_TSD);
  checkHitPositions(art(), SESSIONS, ROOT, [...STMBCAVE_HITS, ...FOLLOWUP_NOT_FIRED, ...STMBCAVE_IN_OPENER]);
  expect(art().hits.length).toBe(STMBCAVE_HITS.length);
});

test('window_off_board: pinned per player, every entry a flat nub-down T whose window leaves the board', () => {
  const L: string[] = art().lists.window_off_board;
  for (const u of ['pinglamb', 'yachi'] as const)
    expect(L.filter(x => x.split(' ')[2] === u).length, u).toBe(WINDOW_OFF_BOARD[u]);
  const v = TR.variants[0];
  const [r0, r1] = v.window.rows, [c0, c1] = v.window.cols;
  const [nr, nc] = v.t_cells.reduce((a: number[], b: number[]) => (b[0]! > a[0]! ? b : a));
  const want = new Set<string>();
  const hits = hitKeys();
  for (const d of digests()) for (const s of scored(d)) {
    if (s.lk.spin !== 'full' || s.lk.cleared !== 2) continue;
    const n = nubOf(s.lk.cells);
    if (!n || hits.has(keyOf(d, s.i))) continue;
    // the window's rows and columns around this nub, as drawn and mirrored
    const rowsOff = n.row + (r0 - nr) < 0 || n.row + (r1 - nr) >= H;
    const drawnOff = rowsOff || n.col + (c0 - nc) < 0 || n.col + (c1 - nc) > 9;
    const mirrOff = rowsOff || n.col - (c1 - nc) < 0 || n.col - (c0 - nc) > 9;
    if (drawnOff || mirrOff) want.add(nameOf(d, s.i));
  }
  for (const x of L) expect(want.has(x), x).toBe(true);
  expect(new Set(L).size).toBe(L.length);
});

test('pinned: denominators, hits, follow-ups, controls', () => {
  const a = art(), v = a.variants.stmbcave;
  for (const u of ['pinglamb', 'yachi'] as const) {
    expect(a.denominators[u].TSD, u).toEqual(TSD_DENOM[u]);
    expect(v.hits_by_player[u], u).toEqual(HITS[u]);
    expect(v.followup_by_player[u].fired, u).toBe(FOLLOWUP_FIRED[u]);
    expect(v.followup_by_player[u].fired + total(v.followup_by_player[u].not_fired)).toBe(HITS[u].all);
  }
  expect(v.controls).toEqual(CONTROLS);
  for (const k of ['no_must_empty', 'no_roof'] as const)
    for (const u of ['pinglamb', 'yachi'] as const) expect(v.controls.ablation[k][u]).toBeGreaterThanOrEqual(HITS[u].all);
});

test('the opener metric: caveAt reproduced, every hit one of its caves, every other cave named', () => {
  const per: Record<string, { w: number; d2: number; io: number; mg: number }> = {};
  const hits = hitKeys();
  const only: string[] = [];
  let hitDepth2 = 0;
  for (const d of digests()) for (const s of scored(d)) {
    const cv = caveAt(s.withT, s.rows, s.lk.cells);
    const wide = !!(cv && cv.width >= 3);
    const isHit = hits.has(keyOf(d, s.i));
    if (isHit) expect(wide, nameOf(d, s.i)).toBe(true);   // every STMB Cave hit is a cave
    if (!wide) continue;
    const p = (per[`${d.session}|${d.user}`] ??= { w: 0, d2: 0, io: 0, mg: 0 });
    p.w++; if (cv!.minDepth >= 2) p.d2++; if (s.i <= art().window_pieces) p.io++; else p.mg++;
    if (isHit) { if (cv!.minDepth >= 2) hitDepth2++; continue; }
    const n = nubOf(s.lk.cells);
    let why = 'other';
    if (s.lk.spin !== 'full') why = 'mini';
    else if (!n) why = 'not_flat';
    else if (cv!.start === n.col - 1 && cv!.end === n.col + 2) why = 'centred';
    else if (cv!.end <= n.col || cv!.start > n.col) why = 'arm_only';
    else if ((cv!.start === n.col && cv!.end === n.col + 3) || (cv!.start === n.col - 2 && cv!.end === n.col + 1)) {
      const dir = cv!.start === n.col ? 1 : -1;
      const behind = [n.col - dir, n.col - 2 * dir];
      why = behind.some(c => c < 0 || c > 9) ? 'wall' : 'other';
    }
    only.push(`${nameOf(d, s.i)} (${why}, width ${cv!.width}, depth ${cv!.minDepth})`);
  }
  for (const s of SESSIONS) {
    const of = JSON.parse(readFileSync(`${ROOT}/${s}/sim/opener-facts.json`, 'utf8'));
    for (const p of of.stmb_cave.players) {
      const m = per[`${s}|${p.user}`] ?? { w: 0, d2: 0, io: 0, mg: 0 };
      expect([m.w, m.d2, m.io, m.mg], `${s} ${p.user}`).toEqual([p.width_ge_3, p.min_depth_ge_2, p.in_opener, p.mid_game]);
    }
  }
  checkNamedList('cave_metric_only', only, CAVE_METRIC_ONLY);
  expect(only.every(x => !x.includes('(other') && !x.includes('(mini') && !x.includes('(not_flat'))).toBe(true);
  // the two counts sum to the opener metric's: the corpus's caves = the hits + the named others
  const caves = Object.values(per).reduce((a, b) => a + b.w, 0);
  expect(caves).toBe(art().hits.length + CAVE_METRIC_ONLY.length);
  // the genuine caves (two rows deep or more) the opener metric counts are all hits
  expect(hitDepth2).toBe(Object.values(per).reduce((a, b) => a + b.d2, 0));
});

test('what discriminates: the cave row alone, with the T anchored, gives exactly the hits', () => {
  const v = TR.variants[0];
  const bottom = v.window.rows[1];
  const preps = prepare(TR, v).map(P => ({ ...P, cells: P.cells.filter(x => x.v === 'T' || x.r === bottom) }));
  const got = new Set<string>();
  for (const d of digests()) for (const s of scored(d)) {
    if (s.lk.spin !== 'full' || s.lk.cleared !== 2) continue;
    if (preps.some(P => !!windowMatch(s.board, s.lk.cells, P))) got.add(keyOf(d, s.i));
  }
  expect([...got].sort()).toEqual([...hitKeys()].sort());
});

test('cross-check: the SDPC Spin rounds that reached its STMB Cave', () => {
  const sd = JSON.parse(readFileSync(`${import.meta.dir}/../../analysis/sdpcspin-facts.json`, 'utf8'));
  const hits = hitKeys();
  const ok: string[] = [], unscored: string[] = [];
  for (const c of sd.cases) {
    const s = c.snapshots.find((x: any) => x.node === '3.first.cave');
    if (!s) continue;
    const d = digests().find(x => x.session === c.session && x.file === c.file && x.round === c.round_index0 && x.user === c.player)!;
    expect(d, `${c.session} ${c.file} ${c.round_index0}`).toBeDefined();
    if (!s.verified || s.lock > d.v) { unscored.push(`${c.session} m${c.match}r${c.round} ${c.player} (node at lock ${s.lock}, verified to lock ${d.v})`); continue; }
    const next = d.locks.findIndex((l, i) => i > s.lock && l.piece === 'T');
    expect(next > s.lock && next <= d.v, `${c.session} m${c.match}r${c.round}`).toBe(true);
    expect(hits.has(keyOf(d, next)), `${c.session} m${c.match}r${c.round} lock ${next}`).toBe(true);
    ok.push(nameOf(d, next));
  }
  checkNamedList('sdpc_cave_hits', ok, SDPC_CAVE_HITS);
  checkNamedList('sdpc_cave_unscored', unscored, SDPC_CAVE_UNSCORED);
});

test('the follow-up row map is verified against the engine at every step it uses', () => {
  const c = art().check;
  expect(c.rowmap_unverified).toBe(31);
  expect(c.rowmap_steps).toBe(275879);
  expect(art().hits.every((h: any) => h.followup.reason !== 'rowmap_unverified')).toBe(true);
});

test('mutants: each rule turned off turns this red with its own symptom', () => {
  const base = serialise(run({}));
  const sum = (a: any, k: string) => total(Object.fromEntries(Object.entries(a.variants.stmbcave.hits_by_player).map(([u, x]: any) => [u, x[k]])));
  const fired = (a: any) => total(Object.fromEntries(Object.entries(a.variants.stmbcave.followup_by_player).map(([u, x]: any) => [u, x.fired])));
  const tsd = (a: any, k = 'all') => a.denominators.pinglamb.TSD[k] + a.denominators.yachi.TSD[k];
  const tss = (a: any) => a.denominators.pinglamb.TSS.all + a.denominators.yachi.TSS.all;
  const b = JSON.parse(base);
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };
  let a = mut({ noMirror: true });
  expect(sum(a, 'mirrored')).toBe(0);
  expect(sum(a, 'all')).toBe(sum(b, 'all') - sum(b, 'mirrored'));

  a = mut({ pastPrefix: true });
  expect(a.denominators.pinglamb.unscored_past_prefix + a.denominators.yachi.unscored_past_prefix).toBe(0);
  expect(tsd(a)).toBeGreaterThan(tsd(b));
  const replayTotal = SESSIONS.reduce((s, x) => s + JSON.parse(readFileSync(`${ROOT}/${x}/sim/opener-facts.json`, 'utf8'))
    .donation.counter_anchor.tspin_clears_replay, 0);
  expect(a.check.tspin_clears_scored).toBe(replayTotal);

  a = mut({ includeMini: true });
  expect(tss(a)).toBe(tss(b) + b.denominators.pinglamb.mini_TSS.all + b.denominators.yachi.mini_TSS.all);

  // the flat T is symmetric, so the anchor alone cannot tell the two hands apart: the must-empty cells
  // (the cave on one side, the filled cells behind the nub on the other) are what do, and without them
  // a lock matches both and the matcher refuses it
  expect(() => run({ noMustEmpty: true })).toThrow(/matches as drawn AND mirrored/);

  a = mut({ tOverlap: true });
  expect(sum(a, 'all')).toBe(total(b.variants.stmbcave.controls.ablation.t_overlap));

  a = mut({ rowAnchorOff1: true });
  expect(sum(a, 'all')).toBe(0);

  // garbage read as EMPTY: no hit moves (no hit has garbage in its window, and no garbage cell sits where
  // the window wants an empty one at an anchored T). What moves is window_off_board: a garbage cell now
  // fails a must-be-filled cell before the matcher reaches the board's edge, so entries leave that list
  a = mut({ garbageEmpty: true });
  const k = (h: any) => `${h.session} ${h.file} ${h.round_index0} ${h.player} ${h.lock}`;
  expect(a.hits.map(k)).toEqual(b.hits.map(k));
  expect(a.lists.window_off_board.length).toBeLessThan(b.lists.window_off_board.length);
  expect(a.lists.window_off_board.every((x: string) => b.lists.window_off_board.includes(x))).toBe(true);

  a = mut({ followupUnmirrored: true });
  expect(a.hits.map(k)).toEqual(b.hits.map(k));
  a.hits.forEach((h: any, i: number) => { if (!h.mirrored) expect(h.followup).toEqual(b.hits[i].followup); });
  expect(a.hits.filter((h: any) => h.mirrored && h.followup.fired).length).toBe(0);
  expect(b.hits.filter((h: any) => h.mirrored && h.followup.fired).length).toBeGreaterThan(0);

  a = mut({ openerLt: true });
  expect(tsd(a, 'in_opener')).toBeLessThan(tsd(b, 'in_opener'));
  expect(tsd(a)).toBe(tsd(b));

  // no row map: the hit's own clear is ABOVE the slot (it does not move it), so only a later clear or
  // garbage row can. Measured: some follow-ups that fired needed one (they stop firing), none fires that
  // did not, and some misses change reason or lock — the hits themselves do not move
  a = mut({ followupNoRowmap: true });
  expect(a.hits.map(k)).toEqual(b.hits.map(k));
  expect(fired(a)).toBeLessThan(fired(b));
  expect(a.hits.every((h: any, i: number) => !h.followup.fired || b.hits[i].followup.fired)).toBe(true);
  expect(a.hits.some((h: any, i: number) => !b.hits[i].followup.fired
    && JSON.stringify(h.followup) !== JSON.stringify(b.hits[i].followup))).toBe(true);

  a = mut({ followupAnyT: true });
  expect(fired(a)).toBeGreaterThan(fired(b));

  for (const [m, why] of Object.entries(EQUIVALENT))
    expect(serialise(run({ [m]: true } as Mutants)), ).toBe(base);
}, 900_000);

/**
 * The 基本的なドネイト (basic donating) technique artefact (`analysis/basicdonating-facts.json`, from
 * `pipeline/sim/emit-technique-facts.ts --technique basicdonating`; the rules are the shared `technique-facts.ts`, the
 * profile `technique-profile-basicdonating.ts`, the qualify rules `basicdonating-qualify.ts`, the shape the gated
 * `pipeline/openers/basicdonating-technique.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count, as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN, on the drawings: `windowMatch` (TS) over every board of the page — at its drawn T on a spin
 *      board, at every resting T placement on any other — fires exactly where the gate's `well_accounting` records it
 *      (the variants' `drawings`), misses exactly the spin board it names (`well_not_fired`), and over every routes
 *      board's U slot fires exactly where `cross_source` records it.
 *   4. THE OTHER PAGES: `other_page` holds iff the hit is a hit of another technique artefact; the common hits per
 *      artefact are pinned. Every 階段のドネイト, STMB Cave and 社畜トレイン hit is a hit here and is given to its page.
 *   5. THE QUALIFY RULES re-derived from the digests, and each rule turned off qualifies exactly the hits failing only
 *      that rule; QUALIFIED_HITS is a named list, and no T is counted twice.
 *   6. pinned per variant and player: denominators, hits, payoffs, controls, the qualify tally; window_off_board per
 *      player as a count with a property check (STMB Cave's treatment: the window holds the row under the nub).
 *   7. matcher mutants, each with its asserted symptom.
 *
 * Run: bun test pipeline/openers/basicdonating.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest, type Cell }
  from '../sim/technique-facts.ts';
import { BASICDONATING } from '../sim/technique-profile-basicdonating.ts';
import { donationQualifier, OTHER_PAGES, type DonationQualifyMutants } from '../sim/basicdonating-qualify.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';
import { W, scored } from './technique-donation-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22']);
const ART_PATH = `${import.meta.dir}/../../analysis/basicdonating-facts.json`;
const TR = JSON.parse(readFileSync(BASICDONATING.transcriptionPath, 'utf8'));
const VARIANTS = ['k1', 'k2', 'k3', 'k4', 'k5', 'k6'];
const USERS = ['pinglamb', 'yachi'] as const;

/** Per player: the opportunities (scored full TSDs), split at the 0-based opener window. */
const DENOM: Record<string, any> = {"pinglamb": {"all": 5636, "in_opener": 1113, "mid_game": 4523}, "yachi": {"all": 5100, "in_opener": 1317, "mid_game": 3783}};
/** Per variant and player: hits, their split, mirrored, garbage in the window. */
const HITS: Record<string, any> = {"k1": {"pinglamb": {"all": 184, "in_opener": 5, "mid_game": 179, "mirrored": 86, "garbage_in_window": 17}, "yachi": {"all": 274, "in_opener": 18, "mid_game": 256, "mirrored": 155, "garbage_in_window": 18}}, "k2": {"pinglamb": {"all": 128, "in_opener": 9, "mid_game": 119, "mirrored": 69, "garbage_in_window": 25}, "yachi": {"all": 111, "in_opener": 8, "mid_game": 103, "mirrored": 64, "garbage_in_window": 16}}, "k3": {"pinglamb": {"all": 73, "in_opener": 6, "mid_game": 67, "mirrored": 38, "garbage_in_window": 9}, "yachi": {"all": 53, "in_opener": 5, "mid_game": 48, "mirrored": 31, "garbage_in_window": 6}}, "k4": {"pinglamb": {"all": 60, "in_opener": 9, "mid_game": 51, "mirrored": 28, "garbage_in_window": 10}, "yachi": {"all": 63, "in_opener": 15, "mid_game": 48, "mirrored": 38, "garbage_in_window": 7}}, "k5": {"pinglamb": {"all": 47, "in_opener": 0, "mid_game": 47, "mirrored": 22, "garbage_in_window": 9}, "yachi": {"all": 36, "in_opener": 1, "mid_game": 35, "mirrored": 15, "garbage_in_window": 4}}, "k6": {"pinglamb": {"all": 25, "in_opener": 0, "mid_game": 25, "mirrored": 13, "garbage_in_window": 8}, "yachi": {"all": 11, "in_opener": 2, "mid_game": 9, "mirrored": 7, "garbage_in_window": 4}}};
/** Per variant and player: the payoff (stored under `followup_by_player`, the shared artefact key). */
const PAYOFF: Record<string, any> = {"k1": {"pinglamb": {"fired": 46, "not_fired": {"i_in_well_not_quad": 13, "past_verified": 4, "round_ended": 6, "well_covered": 19, "well_filled_not_i": 96}}, "yachi": {"fired": 55, "not_fired": {"i_in_well_not_quad": 16, "past_verified": 6, "round_ended": 7, "well_covered": 52, "well_filled_not_i": 138}}}, "k2": {"pinglamb": {"fired": 64, "not_fired": {"i_in_well_not_quad": 13, "past_verified": 1, "round_ended": 4, "well_covered": 13, "well_filled_not_i": 33}}, "yachi": {"fired": 48, "not_fired": {"i_in_well_not_quad": 11, "past_verified": 3, "round_ended": 2, "well_covered": 18, "well_filled_not_i": 29}}}, "k3": {"pinglamb": {"fired": 24, "not_fired": {"i_in_well_not_quad": 7, "past_verified": 1, "round_ended": 3, "well_covered": 8, "well_filled_not_i": 30}}, "yachi": {"fired": 20, "not_fired": {"i_in_well_not_quad": 7, "past_verified": 3, "round_ended": 1, "well_covered": 4, "well_filled_not_i": 18}}}, "k4": {"pinglamb": {"fired": 30, "not_fired": {"i_in_well_not_quad": 9, "past_verified": 1, "round_ended": 1, "well_covered": 3, "well_filled_not_i": 16}}, "yachi": {"fired": 20, "not_fired": {"i_in_well_not_quad": 9, "past_verified": 2, "round_ended": 2, "well_covered": 10, "well_filled_not_i": 20}}}, "k5": {"pinglamb": {"fired": 20, "not_fired": {"i_in_well_not_quad": 7, "past_verified": 2, "round_ended": 2, "well_covered": 2, "well_filled_not_i": 14}}, "yachi": {"fired": 17, "not_fired": {"i_in_well_not_quad": 11, "well_filled_not_i": 8}}}, "k6": {"pinglamb": {"fired": 10, "not_fired": {"i_in_well_not_quad": 7, "well_filled_not_i": 8}}, "yachi": {"fired": 6, "not_fired": {"i_in_well_not_quad": 2, "past_verified": 1, "well_covered": 1, "well_filled_not_i": 1}}}};
const CONTROLS: Record<string, any> = {"k1": {"under": {"TSS": {"pinglamb": 11, "yachi": 14}, "TST": {"pinglamb": 0, "yachi": 0}, "mini_TSS": {"pinglamb": 0, "yachi": 0}, "mini_TSD": {"pinglamb": 0, "yachi": 0}}, "ablation": {"no_must_empty": {"pinglamb": 4877, "yachi": 4146}, "no_roof": {"pinglamb": 544, "yachi": 609}, "t_overlap": {"pinglamb": 3252, "yachi": 2984}}, "orientation_baseline": {"pinglamb": 52, "yachi": 67}}, "k2": {"under": {"TSS": {"pinglamb": 13, "yachi": 22}, "TST": {"pinglamb": 0, "yachi": 0}, "mini_TSS": {"pinglamb": 0, "yachi": 0}, "mini_TSD": {"pinglamb": 0, "yachi": 0}}, "ablation": {"no_must_empty": {"pinglamb": 4877, "yachi": 4146}, "no_roof": {"pinglamb": 414, "yachi": 310}, "t_overlap": {"pinglamb": 3311, "yachi": 3033}}, "orientation_baseline": {"pinglamb": 52, "yachi": 67}}, "k3": {"under": {"TSS": {"pinglamb": 15, "yachi": 9}, "TST": {"pinglamb": 0, "yachi": 0}, "mini_TSS": {"pinglamb": 0, "yachi": 0}, "mini_TSD": {"pinglamb": 0, "yachi": 0}}, "ablation": {"no_must_empty": {"pinglamb": 4877, "yachi": 4146}, "no_roof": {"pinglamb": 357, "yachi": 254}, "t_overlap": {"pinglamb": 3328, "yachi": 3034}}, "orientation_baseline": {"pinglamb": 52, "yachi": 67}}, "k4": {"under": {"TSS": {"pinglamb": 5, "yachi": 13}, "TST": {"pinglamb": 0, "yachi": 0}, "mini_TSS": {"pinglamb": 0, "yachi": 0}, "mini_TSD": {"pinglamb": 0, "yachi": 0}}, "ablation": {"no_must_empty": {"pinglamb": 4877, "yachi": 4146}, "no_roof": {"pinglamb": 224, "yachi": 179}, "t_overlap": {"pinglamb": 1977, "yachi": 1956}}, "orientation_baseline": {"pinglamb": 52, "yachi": 67}}, "k5": {"under": {"TSS": {"pinglamb": 9, "yachi": 8}, "TST": {"pinglamb": 0, "yachi": 0}, "mini_TSS": {"pinglamb": 0, "yachi": 0}, "mini_TSD": {"pinglamb": 0, "yachi": 0}}, "ablation": {"no_must_empty": {"pinglamb": 2668, "yachi": 2547}, "no_roof": {"pinglamb": 152, "yachi": 103}, "t_overlap": {"pinglamb": 1186, "yachi": 1155}}, "orientation_baseline": {"pinglamb": 52, "yachi": 67}}, "k6": {"under": {"TSS": {"pinglamb": 6, "yachi": 3}, "TST": {"pinglamb": 0, "yachi": 0}, "mini_TSS": {"pinglamb": 0, "yachi": 0}, "mini_TSD": {"pinglamb": 0, "yachi": 0}}, "ablation": {"no_must_empty": {"pinglamb": 1616, "yachi": 1448}, "no_roof": {"pinglamb": 78, "yachi": 58}, "t_overlap": {"pinglamb": 552, "yachi": 486}}, "orientation_baseline": {"pinglamb": 52, "yachi": 67}}};
const WINDOW_OFF_BOARD: Record<string, number> = {"pinglamb": 22233, "yachi": 20436};
/** Per player: how many hits qualify, and how many fail each rule (a hit can fail several). */
const QUALIFY: Record<string, any> = {"pinglamb": {"qualified": 128, "not_qualified": {"dpc": 31, "fragment": 258, "garbage_in_shape": 78, "nearer_well": 14, "other_page": 136, "well_covered": 8}}, "yachi": {"qualified": 177, "not_qualified": {"dpc": 11, "fragment": 183, "garbage_in_shape": 55, "nearer_well": 8, "other_page": 200, "ownership_unverified": 6, "well_covered": 6}}};
/** Every hit that qualifies: the page's basic donation, built of whole pieces, at its nearest hole, claimed by no other page. */
const QUALIFIED_HITS: string[] = [
  "2026-07-22 m2r8 yachi k4 lock 141 (mirrored)", "2026-07-22 m2r9 yachi k3 lock 65 (mirrored)",
  "2026-07-22 m3r1 yachi k5 lock 60 (mirrored)", "2026-07-22 m7r8 pinglamb k4 lock 32",
  "2026-07-22 m8r7 yachi k3 lock 60 (mirrored)", "2026-07-22 m10r1 yachi k3 lock 89",
  "2026-07-24 m1r2 pinglamb k1 lock 78", "2026-07-24 m2r4 yachi k6 lock 57", "2026-07-24 m3r3 yachi k1 lock 312",
  "2026-07-24 m4r2 pinglamb k2 lock 32", "2026-07-24 m4r4 pinglamb k2 lock 66 (mirrored)",
  "2026-07-24 m6r4 yachi k1 lock 71", "2026-07-24 m6r5 pinglamb k1 lock 129",
  "2026-07-24 m7r4 pinglamb k3 lock 30 (mirrored)", "2026-07-24 m7r5 pinglamb k1 lock 98",
  "2026-07-24 m7r7 pinglamb k1 lock 54 (mirrored)", "2026-07-28 m2r4 yachi k3 lock 135 (mirrored)",
  "2026-07-28 m3r1 pinglamb k2 lock 16 (mirrored)", "2026-07-28 m3r7 pinglamb k2 lock 17 (mirrored)",
  "2026-07-28 m4r2 yachi k5 lock 152", "2026-07-28 m4r2 yachi k2 lock 182", "2026-07-28 m6r4 pinglamb k1 lock 184",
  "2026-07-28 m6r4 yachi k4 lock 172 (mirrored)", "2026-07-28 m6r4 yachi k1 lock 200 (mirrored)",
  "2026-07-28 m6r5 yachi k2 lock 137", "2026-07-28 m6r5 yachi k3 lock 229", "2026-07-28 m7r3 yachi k2 lock 32",
  "2026-07-28 m7r5 yachi k3 lock 12 (mirrored)", "2026-07-28 m8r6 yachi k5 lock 86 (mirrored)",
  "2026-08-01 m1r3 yachi k2 lock 47", "2026-08-01 m1r4 pinglamb k2 lock 64 (mirrored)",
  "2026-08-01 m1r5 pinglamb k2 lock 26 (mirrored)", "2026-08-01 m1r5 yachi k3 lock 67 (mirrored)",
  "2026-08-01 m1r8 yachi k2 lock 61 (mirrored)", "2026-08-01 m2r3 yachi k1 lock 74",
  "2026-08-01 m3r5 pinglamb k3 lock 92 (mirrored)", "2026-08-01 m4r1 yachi k1 lock 206",
  "2026-08-01 m5r3 pinglamb k1 lock 46", "2026-08-01 m5r3 pinglamb k5 lock 54", "2026-08-01 m5r7 yachi k4 lock 27",
  "2026-08-01 m5r7 yachi k2 lock 180 (mirrored)", "2026-08-01 m6r6 pinglamb k1 lock 67",
  "2026-08-01 m7r2 pinglamb k1 lock 37", "2026-08-01 m7r3 pinglamb k4 lock 57 (mirrored)",
  "2026-08-01 m7r7 yachi k1 lock 63", "2026-08-09 m1r5 pinglamb k2 lock 44", "2026-08-09 m3r3 pinglamb k2 lock 189",
  "2026-08-09 m3r5 pinglamb k1 lock 68 (mirrored)", "2026-08-09 m3r9 pinglamb k3 lock 117",
  "2026-08-09 m4r1 yachi k1 lock 46 (mirrored)", "2026-08-09 m4r2 yachi k1 lock 125",
  "2026-08-09 m4r3 yachi k5 lock 92", "2026-08-09 m4r3 yachi k2 lock 215 (mirrored)",
  "2026-08-09 m4r4 pinglamb k1 lock 46 (mirrored)", "2026-08-09 m5r5 yachi k2 lock 73 (mirrored)",
  "2026-08-09 m6r3 yachi k1 lock 81 (mirrored)", "2026-08-14 m1r4 yachi k3 lock 66",
  "2026-08-14 m2r2 pinglamb k5 lock 42 (mirrored)", "2026-08-14 m2r3 yachi k2 lock 95",
  "2026-08-14 m3r4 yachi k2 lock 59 (mirrored)", "2026-08-14 m3r5 yachi k2 lock 68",
  "2026-08-14 m4r6 pinglamb k3 lock 117 (mirrored)", "2026-08-14 m4r9 yachi k1 lock 27 (mirrored)",
  "2026-08-14 m5r7 pinglamb k2 lock 31", "2026-08-14 m6r1 yachi k1 lock 59 (mirrored)",
  "2026-08-14 m6r8 yachi k6 lock 68", "2026-08-14 m7r5 yachi k4 lock 17 (mirrored)",
  "2026-08-14 m9r4 pinglamb k3 lock 84", "2026-08-14 m9r4 pinglamb k1 lock 215 (mirrored)",
  "2026-08-14 m9r4 yachi k4 lock 30 (mirrored)", "2026-08-14 m10r1 pinglamb k1 lock 40 (mirrored)",
  "2026-08-14 m10r2 pinglamb k1 lock 88 (mirrored)", "2026-08-14 m11r5 pinglamb k2 lock 195 (mirrored)",
  "2026-08-14 m11r5 yachi k3 lock 12 (mirrored)", "2026-08-19 m2r3 pinglamb k3 lock 54",
  "2026-08-19 m2r3 pinglamb k2 lock 137 (mirrored)", "2026-08-19 m5r1 yachi k2 lock 27",
  "2026-08-19 m5r2 pinglamb k6 lock 72 (mirrored)", "2026-08-19 m6r6 pinglamb k2 lock 60",
  "2026-08-19 m6r6 pinglamb k6 lock 135", "2026-08-19 m7r4 yachi k2 lock 83",
  "2026-08-19 m8r2 pinglamb k5 lock 107 (mirrored)", "2026-08-19 m8r5 pinglamb k4 lock 53 (mirrored)",
  "2026-08-19 m9r6 yachi k1 lock 17", "2026-08-19 m10r1 yachi k3 lock 80", "2026-08-25 m2r6 yachi k1 lock 38",
  "2026-08-25 m3r2 pinglamb k1 lock 97 (mirrored)", "2026-08-25 m4r1 yachi k3 lock 71",
  "2026-08-25 m5r3 yachi k4 lock 149 (mirrored)", "2026-08-25 m5r5 yachi k1 lock 35",
  "2026-08-25 m5r6 yachi k4 lock 13 (mirrored)", "2026-08-25 m5r7 yachi k3 lock 64 (mirrored)",
  "2026-08-25 m5r8 pinglamb k1 lock 29 (mirrored)", "2026-08-25 m7r3 yachi k5 lock 85",
  "2026-08-25 m8r4 yachi k4 lock 13 (mirrored)", "2026-08-25 m8r8 pinglamb k1 lock 31",
  "2026-08-25 m9r2 pinglamb k2 lock 34 (mirrored)", "2026-08-25 m9r9 yachi k1 lock 152",
  "2026-09-03 m1r7 pinglamb k2 lock 87", "2026-09-03 m2r4 yachi k3 lock 150 (mirrored)",
  "2026-09-03 m3r4 pinglamb k1 lock 48 (mirrored)", "2026-09-03 m3r5 yachi k4 lock 104",
  "2026-09-03 m4r1 pinglamb k3 lock 72 (mirrored)", "2026-09-03 m5r3 yachi k4 lock 12",
  "2026-09-03 m6r6 yachi k2 lock 19", "2026-09-10 m2r1 pinglamb k4 lock 82",
  "2026-09-10 m2r3 pinglamb k2 lock 54 (mirrored)", "2026-09-10 m2r6 yachi k1 lock 83",
  "2026-09-10 m3r2 yachi k3 lock 67 (mirrored)", "2026-09-10 m3r2 yachi k2 lock 83 (mirrored)",
  "2026-09-10 m4r4 pinglamb k5 lock 37 (mirrored)", "2026-09-10 m4r4 yachi k1 lock 48",
  "2026-09-10 m5r6 yachi k3 lock 18", "2026-09-10 m5r6 yachi k5 lock 100",
  "2026-09-10 m5r8 yachi k5 lock 53 (mirrored)", "2026-09-10 m6r3 pinglamb k3 lock 140 (mirrored)",
  "2026-09-10 m6r5 pinglamb k4 lock 46", "2026-09-10 m6r7 yachi k1 lock 137 (mirrored)",
  "2026-09-10 m6r7 yachi k5 lock 163", "2026-09-10 m6r8 yachi k2 lock 72 (mirrored)",
  "2026-09-10 m6r9 pinglamb k2 lock 64 (mirrored)", "2026-09-10 m7r3 yachi k1 lock 12 (mirrored)",
  "2026-09-10 m7r5 yachi k1 lock 26 (mirrored)", "2026-09-10 m7r5 yachi k1 lock 34 (mirrored)",
  "2026-09-10 m7r7 yachi k2 lock 58 (mirrored)", "2026-09-10 m8r2 yachi k3 lock 31",
  "2026-09-10 m8r4 pinglamb k3 lock 45", "2026-09-11 m1r1 yachi k4 lock 19 (mirrored)",
  "2026-09-11 m2r3 yachi k5 lock 88", "2026-09-11 m3r6 pinglamb k2 lock 38", "2026-09-11 m6r7 pinglamb k1 lock 75",
  "2026-09-11 m7r1 yachi k2 lock 38 (mirrored)", "2026-09-11 m7r1 yachi k4 lock 59 (mirrored)",
  "2026-09-17 m1r1 yachi k4 lock 12 (mirrored)", "2026-09-17 m1r4 yachi k3 lock 135 (mirrored)",
  "2026-09-17 m1r8 yachi k3 lock 53 (mirrored)", "2026-09-17 m2r6 pinglamb k2 lock 17",
  "2026-09-17 m3r3 pinglamb k4 lock 32 (mirrored)", "2026-09-17 m3r6 yachi k4 lock 118",
  "2026-09-17 m3r6 yachi k1 lock 124", "2026-09-17 m3r8 yachi k5 lock 179 (mirrored)",
  "2026-09-17 m4r4 yachi k1 lock 53 (mirrored)", "2026-09-17 m4r4 yachi k1 lock 74 (mirrored)",
  "2026-09-17 m5r1 pinglamb k5 lock 59", "2026-09-17 m6r1 pinglamb k3 lock 23 (mirrored)",
  "2026-09-18 m1r5 pinglamb k5 lock 59 (mirrored)", "2026-09-18 m2r2 pinglamb k5 lock 187",
  "2026-09-18 m2r4 pinglamb k2 lock 89 (mirrored)", "2026-09-18 m5r5 pinglamb k5 lock 48 (mirrored)",
  "2026-09-18 m6r3 yachi k4 lock 13 (mirrored)", "2026-09-18 m6r5 pinglamb k1 lock 38",
  "2026-09-18 m7r1 pinglamb k1 lock 26", "2026-09-18 m7r2 yachi k1 lock 24 (mirrored)",
  "2026-09-18 m8r4 pinglamb k3 lock 70 (mirrored)", "2026-09-18 m8r6 pinglamb k1 lock 10 (mirrored)",
  "2026-09-18 m9r2 yachi k6 lock 13", "2026-09-18 m9r5 pinglamb k4 lock 176",
  "2026-09-18 m10r7 pinglamb k3 lock 48 (mirrored)", "2026-09-18 m11r4 pinglamb k3 lock 101",
  "2026-09-18 m11r5 yachi k4 lock 103", "2026-09-18 m12r3 pinglamb k5 lock 30",
  "2026-09-18 m14r5 pinglamb k3 lock 236", "2026-09-18 m14r8 yachi k4 lock 88", "2026-09-18 m15r7 pinglamb k2 lock 33",
  "2026-09-18 m15r7 yachi k5 lock 21 (mirrored)", "2026-09-18 m16r2 yachi k2 lock 192 (mirrored)",
  "2026-09-18 m16r3 yachi k1 lock 137", "2026-09-18 m16r4 yachi k5 lock 22", "2026-09-18 m16r7 pinglamb k1 lock 53",
  "2026-09-18 m17r2 yachi k1 lock 27 (mirrored)", "2026-09-18 m17r4 yachi k1 lock 33",
  "2026-09-18 m17r6 yachi k4 lock 42 (mirrored)", "2026-09-18 m17r7 yachi k2 lock 24",
  "2026-09-18 m18r4 pinglamb k4 lock 134 (mirrored)", "2026-09-18 m18r5 yachi k4 lock 82 (mirrored)",
  "2026-09-19 m1r2 yachi k4 lock 36 (mirrored)", "2026-09-19 m1r5 yachi k1 lock 138 (mirrored)",
  "2026-09-19 m1r9 pinglamb k2 lock 34", "2026-09-19 m2r2 pinglamb k1 lock 128", "2026-09-19 m3r1 pinglamb k2 lock 75",
  "2026-09-19 m3r2 yachi k1 lock 28", "2026-09-19 m3r3 yachi k1 lock 33", "2026-09-19 m3r6 yachi k1 lock 53",
  "2026-09-19 m5r1 pinglamb k3 lock 53 (mirrored)", "2026-09-19 m5r7 pinglamb k1 lock 41 (mirrored)",
  "2026-09-19 m5r7 yachi k1 lock 28 (mirrored)", "2026-09-19 m6r1 pinglamb k1 lock 117",
  "2026-09-19 m6r2 pinglamb k4 lock 48", "2026-09-19 m7r4 yachi k1 lock 216",
  "2026-09-19 m7r5 yachi k4 lock 192 (mirrored)", "2026-09-19 m8r1 pinglamb k1 lock 60",
  "2026-09-19 m8r1 yachi k2 lock 34", "2026-09-19 m8r2 yachi k4 lock 72 (mirrored)",
  "2026-09-19 m8r6 pinglamb k2 lock 40", "2026-09-19 m8r7 pinglamb k5 lock 27", "2026-09-19 m9r1 pinglamb k1 lock 146",
  "2026-09-19 m9r5 pinglamb k3 lock 54 (mirrored)", "2026-09-19 m10r1 yachi k1 lock 33",
  "2026-09-19 m10r3 yachi k6 lock 14 (mirrored)", "2026-09-19 m12r1 yachi k1 lock 131 (mirrored)",
  "2026-09-19 m12r6 yachi k4 lock 116 (mirrored)", "2026-09-19 m14r8 yachi k1 lock 124 (mirrored)",
  "2026-09-19 m15r4 yachi k3 lock 85 (mirrored)", "2026-09-19 m16r1 yachi k4 lock 58",
  "2026-09-19 m16r6 yachi k2 lock 34 (mirrored)", "2026-09-19 m16r7 yachi k1 lock 49 (mirrored)",
  "2026-09-19 m17r1 pinglamb k2 lock 37 (mirrored)", "2026-09-19 m17r7 pinglamb k2 lock 40",
  "2026-09-19 m18r2 pinglamb k1 lock 66 (mirrored)", "2026-09-19 m18r2 pinglamb k3 lock 191",
  "2026-09-19 m18r7 yachi k1 lock 34", "2026-09-19 m19r1 pinglamb k2 lock 64", "2026-09-19 m19r1 pinglamb k1 lock 110",
  "2026-09-19 m19r1 yachi k4 lock 31", "2026-09-19 m19r6 pinglamb k3 lock 156",
  "2026-09-19 m19r7 pinglamb k1 lock 45 (mirrored)", "2026-09-19 m20r7 pinglamb k6 lock 43 (mirrored)",
  "2026-09-19 m20r8 yachi k2 lock 32", "2026-10-03 m1r3 yachi k3 lock 66 (mirrored)",
  "2026-10-03 m2r6 pinglamb k3 lock 32", "2026-10-03 m2r6 pinglamb k5 lock 47",
  "2026-10-03 m2r8 yachi k3 lock 47 (mirrored)", "2026-10-03 m2r9 pinglamb k4 lock 48",
  "2026-10-03 m2r9 pinglamb k3 lock 134 (mirrored)", "2026-10-03 m3r1 pinglamb k4 lock 15",
  "2026-10-03 m3r1 pinglamb k4 lock 118", "2026-10-03 m3r2 yachi k2 lock 39",
  "2026-10-03 m4r6 yachi k2 lock 54 (mirrored)", "2026-10-03 m5r1 pinglamb k2 lock 38 (mirrored)",
  "2026-10-03 m6r1 pinglamb k4 lock 60", "2026-10-03 m6r1 yachi k1 lock 20", "2026-10-03 m6r3 pinglamb k4 lock 40",
  "2026-10-03 m6r6 yachi k4 lock 12 (mirrored)", "2026-10-03 m6r7 yachi k4 lock 47 (mirrored)",
  "2026-10-03 m7r1 yachi k1 lock 26", "2026-10-03 m8r5 yachi k4 lock 12 (mirrored)",
  "2026-10-03 m9r1 pinglamb k3 lock 272", "2026-10-03 m9r1 yachi k1 lock 94", "2026-10-03 m9r5 yachi k4 lock 50",
  "2026-10-03 m10r5 yachi k2 lock 32", "2026-10-03 m10r6 pinglamb k5 lock 175 (mirrored)",
  "2026-10-03 m11r4 yachi k1 lock 53 (mirrored)", "2026-10-03 m12r2 yachi k4 lock 13 (mirrored)",
  "2026-10-03 m12r7 pinglamb k1 lock 43", "2026-10-03 m13r3 pinglamb k1 lock 29 (mirrored)",
  "2026-10-03 m13r3 yachi k2 lock 99 (mirrored)", "2026-10-03 m13r3 yachi k3 lock 166 (mirrored)",
  "2026-10-03 m13r5 pinglamb k1 lock 43", "2026-10-03 m14r2 pinglamb k2 lock 15 (mirrored)",
  "2026-10-03 m14r5 yachi k2 lock 76", "2026-10-03 m14r7 yachi k4 lock 13 (mirrored)",
  "2026-10-03 m15r3 yachi k1 lock 47", "2026-10-03 m15r3 yachi k4 lock 57",
  "2026-10-03 m15r7 yachi k5 lock 38 (mirrored)", "2026-10-03 m16r3 pinglamb k2 lock 14 (mirrored)",
  "2026-10-03 m16r6 yachi k5 lock 159 (mirrored)", "2026-10-03 m17r1 yachi k1 lock 73 (mirrored)",
  "2026-10-03 m17r5 yachi k1 lock 40 (mirrored)", "2026-10-03 m17r8 pinglamb k5 lock 145",
  "2026-10-03 m19r2 pinglamb k3 lock 21 (mirrored)", "2026-10-03 m20r2 pinglamb k1 lock 319",
  "2026-10-03 m20r7 pinglamb k3 lock 92 (mirrored)", "2026-10-03 m20r7 yachi k4 lock 92 (mirrored)",
  "2026-10-09 m1r7 pinglamb k4 lock 74 (mirrored)", "2026-10-09 m2r1 yachi k1 lock 70",
  "2026-10-09 m2r3 pinglamb k1 lock 32", "2026-10-09 m2r5 yachi k4 lock 13 (mirrored)",
  "2026-10-09 m3r8 pinglamb k2 lock 193", "2026-10-09 m4r2 yachi k1 lock 138 (mirrored)",
  "2026-10-09 m5r1 pinglamb k2 lock 71", "2026-10-09 m5r1 yachi k1 lock 52",
  "2026-10-09 m5r6 yachi k1 lock 20 (mirrored)", "2026-10-09 m5r6 yachi k1 lock 43",
  "2026-10-09 m5r8 yachi k1 lock 19", "2026-10-09 m6r1 yachi k1 lock 31 (mirrored)",
  "2026-10-09 m6r1 yachi k2 lock 95 (mirrored)", "2026-10-09 m6r2 pinglamb k6 lock 53",
  "2026-10-09 m6r6 yachi k1 lock 20", "2026-10-09 m8r2 yachi k1 lock 81", "2026-10-09 m8r3 yachi k1 lock 20",
  "2026-10-09 m8r9 yachi k1 lock 199", "2026-10-09 m9r4 yachi k1 lock 22 (mirrored)",
  "2026-10-09 m9r8 yachi k2 lock 82 (mirrored)", "2026-10-09 m9r8 yachi k3 lock 97 (mirrored)",
  "2026-10-09 m11r2 pinglamb k3 lock 193 (mirrored)", "2026-10-09 m11r5 pinglamb k1 lock 114",
  "2026-10-09 m11r5 yachi k2 lock 29 (mirrored)", "2026-10-09 m12r3 yachi k2 lock 82 (mirrored)",
  "2026-10-09 m12r3 yachi k3 lock 100", "2026-10-12 m1r1 yachi k4 lock 13", "2026-10-12 m2r2 yachi k2 lock 28",
  "2026-10-12 m2r4 pinglamb k5 lock 109", "2026-10-12 m6r2 yachi k3 lock 40",
  "2026-10-12 m6r5 yachi k3 lock 19 (mirrored)", "2026-10-12 m6r5 yachi k1 lock 29 (mirrored)",
  "2026-10-12 m8r2 yachi k2 lock 76", "2026-10-12 m8r3 pinglamb k3 lock 19",
  "2026-10-20 m1r2 pinglamb k2 lock 48 (mirrored)", "2026-10-20 m1r8 yachi k4 lock 48 (mirrored)",
  "2026-10-22 m2r3 pinglamb k2 lock 54 (mirrored)", "2026-10-22 m2r5 yachi k2 lock 80",
  "2026-10-22 m3r5 yachi k3 lock 281 (mirrored)", "2026-10-22 m5r1 yachi k5 lock 31",
  "2026-10-22 m5r4 yachi k2 lock 48", "2026-10-22 m7r2 pinglamb k3 lock 48",
];

/** Per other technique artefact: [its T's that are a hit here, its T's], distinct locks (a T here can be a hit of
 *  two variants). 階段のドネイト and 社畜トレイン are contained whole; STMB Cave is not, by 16 of its T's (measured, not
 *  explained here: the two windows read different cells); 欄干 shares none, its L standing three rows tall in the
 *  well column, which is the page's own intro.l3 mistake. */
const COMMON: Record<string, [number, number]> = {
  stsd: [0, 68], stmbcave: [117, 133], imperialcross: [0, 10], doubledagger: [0, 38], btcannon: [0, 0],
  cutcopy: [0, 2], shachikutrain: [96, 96], parapet: [0, 259], kaidan: [167, 167], dtcannon: [0, 20],
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(BASICDONATING, m, digests());
const hitKey = (h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`;
const dKey = (d: TechDigest) => `${d.session}|${d.file}|${d.round}|${d.user}`;
const hitName = (h: any) =>
  `${h.session} m${h.match}r${h.round} ${h.player} ${h.variant} lock ${h.lock}${h.mirrored ? ' (mirrored)' : ''}`;

/** a drawing as the matcher reads a board: '.' empty, 'X' filled, `drop` cells read empty */
const asBoard = (rows: string[], drop: Set<string> = new Set()) =>
  rows.map((r, i) => [...r].map((ch, c) => ch === '-' || drop.has(`${i},${c}`) ? '.' : 'X').join(''));
/** every resting T placement on a board: four empty cells in a T shape, one on a filled cell or the floor */
function restingT(b: string[]): Cell[][] {
  const shapes = [[[0, 0], [0, 1], [0, 2], [1, 1]], [[0, 1], [1, 0], [1, 1], [1, 2]],
                  [[0, 0], [1, 0], [2, 0], [1, 1]], [[0, 1], [1, 0], [1, 1], [2, 1]]];
  const out: Cell[][] = [];
  for (const sh of shapes) for (let r = 0; r < b.length; r++) for (let c = 0; c < W; c++) {
    const cs = sh.map(([dr, dc]) => ({ row: r + dr!, col: c + dc! }));
    if (!cs.every(q => q.row < b.length && q.col < W && b[q.row]![q.col] === '.')) continue;
    if (cs.some(q => q.row + 1 === b.length || b[q.row + 1]![q.col] !== '.')) out.push(cs);
  }
  return out;
}
const cellsKey = (cs: Cell[] | number[][]) => JSON.stringify(
  (cs as any[]).map(q => Array.isArray(q) ? q : [q.row, q.col]).sort((x, y) => x[0] - y[0] || x[1] - y[1]));
const PREPS = TR.variants.map((v: any) => prepare(TR, v)).flat();

test('the committed artefact is what build() produces now (byte identity)', () => {
  expect(serialise(run({}))).toBe(readFileSync(ART_PATH, 'utf8'));
}, 900_000);

test('quarantined: report_eligible false, no claim ids, six hole windows at offsets 1 to 6', () => {
  const a = art();
  expect(a.report_eligible).toBe(false);
  expect(JSON.stringify(a)).not.toMatch(/data-claim|\b[CRG]\d{3}\b|✓/);
  expect(a.sessions).toEqual(SESSIONS);
  expect(a.cross_route).toBeUndefined();
  expect(Object.keys(a.variants)).toEqual(VARIANTS);
  expect(TR.variants.map((v: any) => v.id)).toEqual(VARIANTS);
  TR.variants.forEach((v: any, i: number) => {
    expect([v.window_basis, v.spin, v.lines, v.well.offset], v.id).toEqual(['well', 'TSD', 2, i + 1]);
    expect(v.payoff).toMatchObject({ kind: 'well_quad', piece: 'I', lines: 4 });
    expect(v.followup).toBeUndefined();
    // the hole's column: four cells, the cell above the donation empty, the two donated filled, the hole under empty
    const col = v.window_extra.cells.map((x: number[]) => x[1]);
    expect(new Set(col).size).toBe(1);
  });
  // the payoff is attributed to harddrop, never to shiwehi.com
  for (const v of TR.variants) expect(v.payoff.note).toContain('harddrop');
});

test('the scored T-spins are the ones emit-opener-facts.ts scores (the third copy of the loop)', () => {
  expect(checkScoredAgainstOpenerFacts(art(), SESSIONS, ROOT)).toBe(15141);
  expect(art().check.reconstruction_disagreed).toBe(0);
  expect(art().check.rowmap_unverified).toBe(30);
  expect(art().check.rowmap_steps).toBe(264047);
});

test('the Python twin on the drawings: windowMatch fires where the gate records it, and nowhere else', () => {
  const got = new Set<string>(), spinFired = new Set<string>();
  for (const n of TR.nodes) {
    let b: string[], cands: Cell[][];
    if (n.kind === 'spin') {
      const p = (n.spin_piece ?? 'T') as string;
      const sc = n.rows.flatMap((r: string, i: number) => [...r].flatMap((ch, c) =>
        ch === p || ch === p.toLowerCase() ? [{ row: i, col: c }] : []));
      b = asBoard(n.rows, new Set(sc.map((q: Cell) => `${q.row},${q.col}`)));
      cands = [sc];
    } else { b = asBoard(n.rows); cands = restingT(b); }
    for (const P of PREPS) for (const cs of cands) if (windowMatch(b, cs, P)) {
      got.add(`${n.id} ${P.id} ${cellsKey(cs)} ${P.mirrored}`);
      if (n.kind === 'spin') spinFired.add(n.id);
    }
  }
  const rec = new Set<string>();
  for (const v of TR.variants) for (const d of v.drawings) rec.add(`${d.board} ${v.id} ${cellsKey(d.t_cells)} ${d.mirrored}`);
  for (const e of TR.well_fires_other) rec.add(`${e.board} ${e.variant} ${cellsKey(e.t_cells)} ${e.mirrored}`);
  expect([...got].sort()).toEqual([...rec].sort());
  const spins = TR.nodes.filter((n: any) => n.kind === 'spin').map((n: any) => n.id);
  expect(spins.filter((id: string) => !spinFired.has(id))).toEqual(TR.well_not_fired.map((e: any) => e.board));
  expect(TR.well_not_fired.map((e: any) => e.board)).toEqual(['intro.l3']);
  // the routes boards, at their U slots (`U` the spin cell, every other non-`-` letter filled)
  const routes: string[] = [];
  for (const f of readdirSync(import.meta.dir).filter(x => x.endsWith('-routes.json')).sort())
    for (const n of JSON.parse(readFileSync(`${import.meta.dir}/${f}`, 'utf8')).nodes) {
      if (!n.rows) continue;
      const u = n.rows.flatMap((r: string, i: number) => [...r].flatMap((ch, c) => ch === 'U' ? [{ row: i, col: c }] : []));
      if (u.length !== 4) continue;
      const b = n.rows.map((r: string) => [...r].map(ch => ch === '-' || ch === 'U' ? '.' : 'X').join(''));
      for (const P of PREPS) if (windowMatch(b, u, P)) routes.push(`${f} ${n.id} ${P.id} ${P.mirrored}`);
    }
  const xs = TR.cross_source;
  expect(routes.sort()).toEqual([...xs.fires, ...xs.also].map((e: any) => `${e.file} ${e.node} ${e.variant} ${e.mirrored}`).sort());
}, 120_000);

test('named lists: the qualifying hits, the empty lists; every named hit resolves to its match position', () => {
  const a = art();
  const q = a.hits.filter((h: any) => h.qualifies);
  checkNamedList('QUALIFIED_HITS', q.map(hitName), QUALIFIED_HITS);
  // a T is counted once: no two qualifying hits share a lock
  expect(new Set(q.map(hitKey)).size).toBe(q.length);
  expect(a.lists.qualified_hits.length).toBe(q.length);
  checkNamedList('recon_dropped_tsd', a.lists.recon_dropped_tsd, []);
  expect(a.lists.basicdonating_hits).toEqual(a.hits.map(hitName));
  checkHitPositions(a, SESSIONS, ROOT, QUALIFIED_HITS);
});

test('pinned: denominators, hits, payoffs, controls, the qualify tally, per variant and player', () => {
  const a = art();
  for (const u of USERS) expect(a.denominators[u].TSD, u).toEqual(DENOM[u]);
  for (const k of VARIANTS) {
    expect(a.variants[k].controls, k).toEqual(CONTROLS[k]);
    for (const u of USERS) {
      expect(a.variants[k].hits_by_player[u], `${k} ${u}`).toEqual(HITS[k][u]);
      expect(a.variants[k].followup_by_player[u], `${k} ${u}`).toEqual(PAYOFF[k][u]);
      expect(PAYOFF[k][u].fired + total(PAYOFF[k][u].not_fired)).toBe(HITS[k][u].all);
      // STRUCTURAL: a TST cannot anchor a flat T, which spans two rows
      expect(CONTROLS[k].under.TST[u]).toBe(0);
    }
  }
  for (const u of USERS) {
    const hs = a.hits.filter((h: any) => h.player === u);
    const tally: Record<string, number> = {};
    for (const h of hs) for (const r of h.not_qualified) tally[r] = (tally[r] ?? 0) + 1;
    expect({ qualified: hs.filter((h: any) => h.qualifies).length, not_qualified: tally }, u).toEqual(QUALIFY[u]);
  }
  expect(QUALIFIED_HITS.length).toBe(QUALIFY.pinglamb.qualified + QUALIFY.yachi.qualified);
});

test('window_off_board: pinned per player, every entry a flat T at a full TSD whose window leaves the board', () => {
  const L: string[] = art().lists.window_off_board;
  for (const u of USERS) expect(L.filter(x => x.split(' ')[2] === u).length, u).toBe(WINDOW_OFF_BOARD[u]);
  expect(new Set(L).size).toBe(L.length);
  const hits = new Set(art().hits.map((h: any) => `${hitKey(h)}|${h.variant}`));
  const by = new Map<string, { d: TechDigest; s: ReturnType<typeof scored>[number] }>();
  for (const d of digests()) for (const s of scored(d))
    by.set(`${d.session} m${d.match}r${d.round + 1} ${d.user} lock ${s.i}`, { d, s });
  for (const x of L) {
    const m = /^(.*) \((k\d)\)$/.exec(x)!;
    const e = by.get(m[1]!)!;
    expect(e, x).toBeDefined();
    expect([e.s.lk.spin, e.s.lk.cleared], x).toEqual(['full', 2]);
    const Ps = PREPS.filter((P: any) => P.id === m[2]);
    expect(Ps.some((P: any) => windowMatch(e.s.board, e.s.lk.cells, P) === null), x).toBe(true);
    expect(hits.has(`${e.d.session}|${e.d.file}|${e.d.round}|${e.d.user}|${e.s.i}|${m[2]}`), x).toBe(false);
  }
}, 600_000);

test('the other pages: other_page iff the T is a hit of another artefact; the common hits, pinned', () => {
  const a = art();
  const mine = new Set(a.hits.map(hitKey));
  const theirs: Record<string, Set<string>> = {};
  for (const k of OTHER_PAGES)
    theirs[k] = new Set(JSON.parse(readFileSync(`${import.meta.dir}/../../analysis/${k}-facts.json`, 'utf8')).hits.map(hitKey));
  const common: Record<string, [number, number]> = {};
  for (const k of OTHER_PAGES) common[k] = [[...theirs[k]!].filter(x => mine.has(x)).length, theirs[k]!.size];
  expect(common).toEqual(COMMON);
  for (const h of a.hits)
    expect(h.not_qualified.includes('other_page'), hitName(h)).toBe(OTHER_PAGES.some(k => theirs[k]!.has(hitKey(h))));
});

test('the qualify rules, re-derived from the digests; each rule off qualifies exactly the hits failing only it', () => {
  const a = art();
  const byD = new Map(digests().map(d => [dKey(d), d]));
  const verdicts = (mut: DonationQualifyMutants) => {
    const q = donationQualifier(BASICDONATING.transcriptionPath, `${import.meta.dir}`, mut);
    return a.hits.map((h: any) => q(h, byD.get(`${h.session}|${h.file}|${h.round_index0}|${h.player}`)!));
  };
  const base = verdicts({});
  a.hits.forEach((h: any, i: number) => {
    expect(base[i]!.qualifies, hitName(h)).toBe(h.qualifies);
    expect(base[i]!.not_qualified, hitName(h)).toEqual(h.not_qualified);
  });
  const RULES: [keyof DonationQualifyMutants, string][] = [
    ['allowFragments', 'fragment'], ['allowGarbage', 'garbage_in_shape'], ['noDpc', 'dpc'],
    ['noOtherPage', 'other_page'], ['noNearer', 'nearer_well'], ['noCovered', 'well_covered'],
  ];
  for (const [m, rule] of RULES) {
    const got = verdicts({ [m]: true });
    const want = a.hits.map((h: any) => h.qualifies || (h.not_qualified.length === 1 && h.not_qualified[0] === rule));
    expect(got.map(v => v.qualifies), m).toEqual(want);
    // live: some hit fails only this rule
    expect(want.filter((x: boolean, i: number) => x && !a.hits[i].qualifies).length, m).toBeGreaterThan(0);
  }
  // no page drawing has a covered well: the rule reads nothing the page draws
  for (const v of TR.variants) for (const d of v.drawings) {
    const rows = TR.nodes.find((n: any) => n.id === d.board).rows as string[];
    const col = (() => {
      const P = PREPS.find((x: any) => x.id === v.id && x.mirrored === d.mirrored)!;
      const cs = d.t_cells.map(([r, c]: number[]) => ({ row: r!, col: c! }));
      const sc = new Set<string>(d.t_cells.map(([r, c]: number[]) => `${r},${c}`));
      const off = windowMatch(asBoard(rows, sc), cs, P);
      expect(off, `${v.id} ${d.board}`).toBeTruthy();
      const top = Math.min(...P.cells.filter((x: any) => x.c === P.well!.c).map((x: any) => x.r));
      return { c: P.well!.c + (off as any).dc, top: top + (off as any).dr };
    })();
    for (let r = 0; r < col.top; r++) expect(rows[r]![col.c], `${v.id} ${d.board} row ${r}`).toBe('-');
  }
}, 600_000);

test('mutants: each rule turned off turns this red with its own symptom', () => {
  const base = serialise(run({}));
  const b = JSON.parse(base);
  const sum = (a: any, k: string) => VARIANTS.reduce((n, v) =>
    n + USERS.reduce((m, u) => m + a.variants[v].hits_by_player[u][k], 0), 0);
  const fired = (a: any) => VARIANTS.reduce((n, v) => n + USERS.reduce((m, u) => m + a.variants[v].followup_by_player[u].fired, 0), 0);
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };
  const k = (h: any) => `${hitKey(h)} ${h.variant} ${h.mirrored}`;

  let a = mut({ noMirror: true });
  expect(sum(a, 'mirrored')).toBe(0);
  expect(sum(a, 'all')).toBe(sum(b, 'all') - sum(b, 'mirrored'));

  // garbage read as EMPTY: a flat T between two garbage holes then fits a window in both hands, which the matcher
  // refuses (measured: the first such T is 2026-07-22 m1r7 pinglamb lock 66)
  expect(() => run({ garbageEmpty: true })).toThrow(/matches as drawn AND mirrored/);

  // the payoff mutants: the hits never move, only the payoffs
  a = mut({ payoffAnyPiece: true });
  expect(a.hits.map(k)).toEqual(b.hits.map(k));
  expect(fired(a)).toBeGreaterThan(fired(b));
  expect(a.hits.filter((h: any) => ['well_filled_not_i', 'i_in_well_not_quad'].includes(h.followup.reason)).length).toBe(0);
  a = mut({ payoffNoQuad: true });
  expect(a.hits.map(k)).toEqual(b.hits.map(k));
  expect(fired(a)).toBe(fired(b) + b.hits.filter((h: any) => h.followup.reason === 'i_in_well_not_quad').length);
}, 1_800_000);

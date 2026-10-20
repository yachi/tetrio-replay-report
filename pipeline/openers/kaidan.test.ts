/**
 * The 階段のドネイト (Kaidan Setups) technique artefact (`analysis/kaidan-facts.json`, from
 * `pipeline/sim/emit-technique-facts.ts --technique kaidan`; the rules are the shared `technique-facts.ts`, the profile
 * `technique-profile-kaidan.ts`, the shape the gated `pipeline/openers/kaidan-technique.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count in every session and for every
 *      player, as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN, on the drawings: `windowMatch` (TS) fires on this page's three builds as drawn and its two
 *      DT砲 boards mirrored, on harddrop's four Kaidan_Setups drawings and Anchor_Set's Kaidan at their recorded slots
 *      and hands, on the Kaidan BT砲's harddrop record holds (mirrored), on the boards harddrop draws with no T at the
 *      recorded placement — once each, and nowhere else; on no drawn T harddrop draws that the gate names as a miss;
 *      and on no routes board at all.
 *   4. THE OTHER FLAT-T WINDOWS: anchored on the same flat T, this window clashes with STMB Cave's, ダブルダガー's,
 *      BT砲's, 千鳥格子's and 欄干's on a cell in every pairing of hands, and their hit sets are disjoint from this one;
 *      with 社畜トレイン's it clashes on NO cell in the same hand, so the common hits are a NAMED list
 *      (SHACHIKUTRAIN_ALSO_KAIDAN), not an assert. STSD's and インペリアルクロス's T stands up and can never share the
 *      anchor.
 *   5. WHAT DISCRIMINATES, measured per window part with the T anchored (the roof row, the cleared rows, the well rows),
 *      and the OTHER TWO maximal agreement boxes (the cleared rows alone; the cleared rows and the well rows, one
 *      column wider and no roof) measured as controls, never asserted against: the window is the only maximal box
 *      holding the roof, which is the one choice in it.
 *   6. DONATION: `donationCols` re-implemented (`technique-donation-checks.ts`, shared with `parapet.test.ts`), every
 *      session's per-player `donation.players[].donations` reproduced exactly, and every hit that is not a donation at
 *      its well column named with its re-derived reason (HIT_NOT_DONATION).
 *   7. NAMED lists, not bounds; pinned per-player figures; the STRUCTURAL zeros re-derived from the window; mutants,
 *      each with its asserted symptom (the equivalent ones named, measured, asserted to STAY byte-identical).
 *   8. THE PAYOFF ON THE PAGE'S OWN DRAWING: a two-lock digest on the basic form (the TSD, then an I into the well the
 *      page draws three deep) gives `i_in_well_not_quad`; the same board with its bottom row repeated once (a well
 *      four deep: a board WE constructed — harddrop's Anchor_Set draws a four-deep Tetris, but on a later board of
 *      that line, not on the board a Kaidan TSD leaves) fires, as drawn and mirrored, and each payoff mutant breaks it.
 *
 * window_off_board is not listed entry by entry: it is every flat, nub-down T at a full TSD whose window leaves the
 * board before the matcher found a mismatch. It is pinned per player as a count, and every entry is checked to be such
 * a T (STMB Cave's and 欄干's treatment, for the same reason).
 *
 * Run: bun test pipeline/openers/kaidan.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, classify, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest, type Cell }
  from '../sim/technique-facts.ts';
import { KAIDAN } from '../sim/technique-profile-kaidan.ts';
import { STSD } from '../sim/technique-profile-stsd.ts';
import { STMBCAVE } from '../sim/technique-profile-stmbcave.ts';
import { IMPERIALCROSS } from '../sim/technique-profile-imperialcross.ts';
import { DOUBLEDAGGER } from '../sim/technique-profile-doubledagger.ts';
import { BTCANNON } from '../sim/technique-profile-btcannon.ts';
import { CUTCOPY } from '../sim/technique-profile-cutcopy.ts';
import { SHACHIKUTRAIN } from '../sim/technique-profile-shachikutrain.ts';
import { PARAPET } from '../sim/technique-profile-parapet.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';
import { H, W, scored, donationVerdict } from './technique-donation-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12']);
const ART_PATH = `${import.meta.dir}/../../analysis/kaidan-facts.json`;
const TR = JSON.parse(readFileSync(KAIDAN.transcriptionPath, 'utf8'));
const V = TR.variants.find((v: any) => v.id === 'kaidan');
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));

const KAIDAN_HITS: string[] = [
  "2026-07-22 m1r5 yachi lock 93 (mirrored)", "2026-07-22 m2r8 pinglamb lock 104 (mirrored)",
  "2026-07-22 m3r1 yachi lock 41 (mirrored)", "2026-07-22 m3r7 yachi lock 87",
  "2026-07-22 m4r4 yachi lock 110 (mirrored)", "2026-07-22 m6r1 pinglamb lock 83", "2026-07-22 m9r2 yachi lock 24",
  "2026-07-22 m9r3 yachi lock 60 (mirrored)", "2026-07-22 m10r7 yachi lock 72 (mirrored)",
  "2026-07-22 m10r8 yachi lock 31", "2026-07-24 m3r1 pinglamb lock 115", "2026-07-24 m3r8 pinglamb lock 24",
  "2026-07-24 m5r5 yachi lock 31", "2026-07-24 m7r2 yachi lock 25", "2026-07-28 m2r8 yachi lock 72",
  "2026-07-28 m3r7 pinglamb lock 32 (mirrored)", "2026-07-28 m6r5 yachi lock 122",
  "2026-07-28 m7r6 yachi lock 74 (mirrored)", "2026-08-01 m1r5 pinglamb lock 208", "2026-08-01 m1r5 yachi lock 75",
  "2026-08-01 m2r4 yachi lock 111", "2026-08-01 m3r5 pinglamb lock 40 (mirrored)", "2026-08-01 m3r5 yachi lock 74",
  "2026-08-01 m4r1 pinglamb lock 186 (mirrored)", "2026-08-01 m4r1 yachi lock 129 (mirrored)",
  "2026-08-01 m4r2 yachi lock 84", "2026-08-01 m6r1 yachi lock 80", "2026-08-01 m6r1 yachi lock 117",
  "2026-08-01 m6r5 yachi lock 120", "2026-08-01 m7r1 yachi lock 170 (mirrored)",
  "2026-08-01 m7r3 pinglamb lock 78 (mirrored)", "2026-08-01 m7r6 yachi lock 66",
  "2026-08-09 m3r3 yachi lock 44 (mirrored)", "2026-08-09 m4r2 pinglamb lock 42 (mirrored)",
  "2026-08-09 m4r3 pinglamb lock 138 (mirrored)", "2026-08-09 m4r6 yachi lock 28 (mirrored)",
  "2026-08-09 m5r5 pinglamb lock 70", "2026-08-09 m6r3 pinglamb lock 77 (mirrored)",
  "2026-08-14 m1r4 pinglamb lock 40 (mirrored)", "2026-08-14 m2r4 pinglamb lock 159",
  "2026-08-14 m2r4 yachi lock 191 (mirrored)", "2026-08-14 m5r8 pinglamb lock 134 (mirrored)",
  "2026-08-14 m7r8 pinglamb lock 41", "2026-08-14 m9r6 pinglamb lock 38", "2026-08-14 m11r2 yachi lock 182",
  "2026-08-19 m1r6 yachi lock 61 (mirrored)", "2026-08-19 m3r4 yachi lock 83",
  "2026-08-19 m3r4 yachi lock 118 (mirrored)", "2026-08-19 m4r8 yachi lock 29",
  "2026-08-19 m5r2 yachi lock 32 (mirrored)", "2026-08-19 m6r2 yachi lock 104", "2026-08-19 m6r3 yachi lock 38",
  "2026-08-19 m6r5 yachi lock 13 (mirrored)", "2026-08-19 m10r2 pinglamb lock 66 (mirrored)",
  "2026-08-19 m10r5 yachi lock 16 (mirrored)", "2026-08-25 m1r6 yachi lock 27 (mirrored)",
  "2026-08-25 m1r9 pinglamb lock 43", "2026-08-25 m3r2 pinglamb lock 242 (mirrored)",
  "2026-08-25 m3r2 yachi lock 85", "2026-08-25 m3r4 yachi lock 36 (mirrored)", "2026-08-25 m4r2 pinglamb lock 29",
  "2026-08-25 m5r8 yachi lock 56 (mirrored)", "2026-08-25 m8r2 pinglamb lock 143 (mirrored)",
  "2026-08-25 m9r2 pinglamb lock 47", "2026-08-25 m9r7 pinglamb lock 108 (mirrored)",
  "2026-09-03 m3r4 pinglamb lock 120", "2026-09-03 m5r4 pinglamb lock 23",
  "2026-09-10 m1r1 pinglamb lock 25 (mirrored)", "2026-09-10 m1r5 pinglamb lock 101 (mirrored)",
  "2026-09-10 m1r7 yachi lock 40", "2026-09-10 m3r4 pinglamb lock 58", "2026-09-10 m3r6 yachi lock 25",
  "2026-09-10 m4r7 yachi lock 34 (mirrored)", "2026-09-10 m5r9 yachi lock 64 (mirrored)",
  "2026-09-10 m6r3 pinglamb lock 86 (mirrored)", "2026-09-10 m7r8 yachi lock 75 (mirrored)",
  "2026-09-10 m8r8 yachi lock 230", "2026-09-11 m1r8 pinglamb lock 107 (mirrored)",
  "2026-09-11 m2r5 yachi lock 135 (mirrored)", "2026-09-11 m3r6 pinglamb lock 52 (mirrored)",
  "2026-09-11 m4r4 pinglamb lock 40 (mirrored)", "2026-09-11 m6r6 pinglamb lock 139",
  "2026-09-11 m6r7 yachi lock 26", "2026-09-17 m1r8 yachi lock 75", "2026-09-17 m2r6 yachi lock 81",
  "2026-09-17 m3r1 yachi lock 26 (mirrored)", "2026-09-17 m3r6 pinglamb lock 130 (mirrored)",
  "2026-09-18 m1r6 pinglamb lock 75", "2026-09-18 m7r4 yachi lock 44", "2026-09-18 m7r6 yachi lock 58",
  "2026-09-18 m14r4 yachi lock 53 (mirrored)", "2026-09-18 m15r7 yachi lock 62 (mirrored)",
  "2026-09-18 m16r2 pinglamb lock 149 (mirrored)", "2026-09-18 m16r3 yachi lock 167 (mirrored)",
  "2026-09-18 m16r4 yachi lock 117", "2026-09-18 m18r1 pinglamb lock 57", "2026-09-18 m18r5 pinglamb lock 55",
  "2026-09-19 m1r2 yachi lock 161", "2026-09-19 m2r1 yachi lock 39 (mirrored)", "2026-09-19 m2r1 yachi lock 65",
  "2026-09-19 m4r3 pinglamb lock 123", "2026-09-19 m5r2 pinglamb lock 72 (mirrored)",
  "2026-09-19 m5r2 yachi lock 10", "2026-09-19 m6r5 yachi lock 72 (mirrored)", "2026-09-19 m7r1 pinglamb lock 43",
  "2026-09-19 m7r4 yachi lock 103 (mirrored)", "2026-09-19 m7r4 yachi lock 148",
  "2026-09-19 m8r2 yachi lock 38 (mirrored)", "2026-09-19 m8r4 yachi lock 67", "2026-09-19 m8r6 yachi lock 23",
  "2026-09-19 m11r2 pinglamb lock 40", "2026-09-19 m12r3 pinglamb lock 14 (mirrored)",
  "2026-09-19 m12r4 yachi lock 42 (mirrored)", "2026-09-19 m12r4 yachi lock 51", "2026-09-19 m14r3 yachi lock 154",
  "2026-09-19 m15r4 pinglamb lock 129 (mirrored)", "2026-09-19 m16r5 yachi lock 49 (mirrored)",
  "2026-09-19 m19r1 pinglamb lock 102 (mirrored)", "2026-09-19 m19r1 yachi lock 23 (mirrored)",
  "2026-09-19 m20r1 pinglamb lock 69 (mirrored)", "2026-09-19 m20r5 pinglamb lock 30",
  "2026-10-03 m4r8 yachi lock 108", "2026-10-03 m5r6 pinglamb lock 61 (mirrored)", "2026-10-03 m7r7 yachi lock 172",
  "2026-10-03 m9r6 pinglamb lock 68", "2026-10-03 m10r1 yachi lock 53", "2026-10-03 m10r6 yachi lock 88 (mirrored)",
  "2026-10-03 m10r6 yachi lock 107 (mirrored)", "2026-10-03 m13r5 yachi lock 104",
  "2026-10-03 m14r2 yachi lock 60 (mirrored)", "2026-10-03 m15r3 pinglamb lock 66",
  "2026-10-03 m17r8 pinglamb lock 135 (mirrored)", "2026-10-09 m1r2 yachi lock 68 (mirrored)",
  "2026-10-09 m2r5 yachi lock 70", "2026-10-09 m2r6 yachi lock 23 (mirrored)",
  "2026-10-09 m3r6 pinglamb lock 49 (mirrored)", "2026-10-09 m3r8 yachi lock 59 (mirrored)",
  "2026-10-09 m4r2 yachi lock 26 (mirrored)", "2026-10-09 m4r2 yachi lock 132",
  "2026-10-09 m5r2 pinglamb lock 33 (mirrored)", "2026-10-09 m5r8 pinglamb lock 38", "2026-10-09 m6r1 yachi lock 53",
  "2026-10-09 m6r8 pinglamb lock 26 (mirrored)", "2026-10-09 m7r6 yachi lock 11", "2026-10-09 m7r8 yachi lock 56",
  "2026-10-09 m10r8 yachi lock 44", "2026-10-09 m11r2 pinglamb lock 116 (mirrored)",
  "2026-10-12 m1r3 pinglamb lock 99 (mirrored)", "2026-10-12 m1r3 yachi lock 81 (mirrored)",
  "2026-10-12 m1r4 yachi lock 70 (mirrored)", "2026-10-12 m3r1 yachi lock 40",
  "2026-10-12 m4r2 pinglamb lock 52 (mirrored)", "2026-10-12 m6r7 pinglamb lock 46",
  "2026-10-12 m8r1 pinglamb lock 45",
];

const PAYOFF_NOT_FIRED: string[] = [
  "2026-07-22 m1r5 yachi lock 93 (well_covered at lock 101)",
  "2026-07-22 m3r1 yachi lock 41 (well_filled_not_i at lock 46)",
  "2026-07-22 m4r4 yachi lock 110 (well_filled_not_i at lock 111)",
  "2026-07-22 m10r7 yachi lock 72 (well_covered at lock 74)",
  "2026-07-22 m10r8 yachi lock 31 (i_in_well_not_quad at lock 34)",
  "2026-07-24 m3r8 pinglamb lock 24 (well_filled_not_i at lock 29)",
  "2026-07-24 m5r5 yachi lock 31 (well_covered at lock 32)",
  "2026-07-24 m7r2 yachi lock 25 (well_covered at lock 32)",
  "2026-07-28 m2r8 yachi lock 72 (well_covered at lock 81)",
  "2026-07-28 m3r7 pinglamb lock 32 (well_covered at lock 39)",
  "2026-08-01 m2r4 yachi lock 111 (well_covered at lock 116)",
  "2026-08-01 m3r5 pinglamb lock 40 (well_covered at lock 45)",
  "2026-08-01 m3r5 yachi lock 74 (well_covered at lock 76)",
  "2026-08-01 m4r1 yachi lock 129 (i_in_well_not_quad at lock 130)",
  "2026-08-01 m4r2 yachi lock 84 (well_filled_not_i at lock 86)",
  "2026-08-01 m6r1 yachi lock 80 (well_filled_not_i at lock 81)",
  "2026-08-01 m6r5 yachi lock 120 (well_covered at lock 121)",
  "2026-08-01 m7r6 yachi lock 66 (well_covered at lock 68)",
  "2026-08-09 m3r3 yachi lock 44 (well_covered at lock 54)",
  "2026-08-09 m4r3 pinglamb lock 138 (well_covered at lock 143)",
  "2026-08-09 m5r5 pinglamb lock 70 (well_covered at lock 79)",
  "2026-08-09 m6r3 pinglamb lock 77 (i_in_well_not_quad at lock 81)",
  "2026-08-14 m2r4 yachi lock 191 (past_verified at lock 193)",
  "2026-08-14 m5r8 pinglamb lock 134 (well_filled_not_i at lock 145)",
  "2026-08-14 m7r8 pinglamb lock 41 (well_filled_not_i at lock 45)",
  "2026-08-14 m9r6 pinglamb lock 38 (i_in_well_not_quad at lock 39)",
  "2026-08-14 m11r2 yachi lock 182 (i_in_well_not_quad at lock 185)",
  "2026-08-19 m1r6 yachi lock 61 (well_covered at lock 62)",
  "2026-08-19 m3r4 yachi lock 83 (well_covered at lock 87)",
  "2026-08-19 m4r8 yachi lock 29 (well_filled_not_i at lock 30)",
  "2026-08-19 m6r2 yachi lock 104 (well_covered at lock 110)",
  "2026-08-19 m6r3 yachi lock 38 (well_filled_not_i at lock 43)",
  "2026-08-19 m6r5 yachi lock 13 (well_covered at lock 17)",
  "2026-08-25 m1r6 yachi lock 27 (well_filled_not_i at lock 36)", "2026-08-25 m3r2 pinglamb lock 242 (round_ended)",
  "2026-08-25 m3r2 yachi lock 85 (i_in_well_not_quad at lock 86)",
  "2026-08-25 m3r4 yachi lock 36 (well_covered at lock 43)",
  "2026-08-25 m9r2 pinglamb lock 47 (i_in_well_not_quad at lock 49)",
  "2026-09-03 m3r4 pinglamb lock 120 (i_in_well_not_quad at lock 121)",
  "2026-09-03 m5r4 pinglamb lock 23 (well_filled_not_i at lock 30)",
  "2026-09-10 m1r1 pinglamb lock 25 (well_covered at lock 33)",
  "2026-09-10 m1r7 yachi lock 40 (well_covered at lock 41)", "2026-09-10 m3r4 pinglamb lock 58 (round_ended)",
  "2026-09-10 m4r7 yachi lock 34 (i_in_well_not_quad at lock 37)",
  "2026-09-11 m3r6 pinglamb lock 52 (well_covered at lock 62)",
  "2026-09-11 m4r4 pinglamb lock 40 (well_filled_not_i at lock 41)",
  "2026-09-11 m6r6 pinglamb lock 139 (i_in_well_not_quad at lock 140)",
  "2026-09-11 m6r7 yachi lock 26 (well_covered at lock 27)",
  "2026-09-17 m1r8 yachi lock 75 (well_filled_not_i at lock 77)",
  "2026-09-17 m2r6 yachi lock 81 (well_covered at lock 83)",
  "2026-09-17 m3r1 yachi lock 26 (i_in_well_not_quad at lock 29)",
  "2026-09-18 m18r1 pinglamb lock 57 (well_filled_not_i at lock 58)",
  "2026-09-19 m1r2 yachi lock 161 (past_verified at lock 164)",
  "2026-09-19 m2r1 yachi lock 65 (well_covered at lock 68)",
  "2026-09-19 m5r2 yachi lock 10 (well_covered at lock 11)",
  "2026-09-19 m7r4 yachi lock 103 (well_covered at lock 107)",
  "2026-09-19 m7r4 yachi lock 148 (well_filled_not_i at lock 151)",
  "2026-09-19 m8r2 yachi lock 38 (well_filled_not_i at lock 42)",
  "2026-09-19 m12r3 pinglamb lock 14 (well_covered at lock 18)",
  "2026-09-19 m12r4 yachi lock 51 (well_covered at lock 53)",
  "2026-09-19 m14r3 yachi lock 154 (well_filled_not_i at lock 155)",
  "2026-09-19 m19r1 yachi lock 23 (well_covered at lock 26)",
  "2026-10-03 m4r8 yachi lock 108 (well_filled_not_i at lock 116)",
  "2026-10-03 m7r7 yachi lock 172 (well_filled_not_i at lock 174)",
  "2026-10-03 m9r6 pinglamb lock 68 (i_in_well_not_quad at lock 69)",
  "2026-10-03 m10r1 yachi lock 53 (well_covered at lock 59)",
  "2026-10-03 m10r6 yachi lock 88 (well_filled_not_i at lock 89)",
  "2026-10-03 m10r6 yachi lock 107 (well_filled_not_i at lock 108)",
  "2026-10-03 m13r5 yachi lock 104 (well_filled_not_i at lock 108)",
  "2026-10-09 m3r6 pinglamb lock 49 (well_filled_not_i at lock 59)",
  "2026-10-09 m3r8 yachi lock 59 (well_filled_not_i at lock 60)",
  "2026-10-09 m4r2 yachi lock 26 (well_filled_not_i at lock 29)",
  "2026-10-09 m4r2 yachi lock 132 (well_covered at lock 137)",
  "2026-10-09 m5r8 pinglamb lock 38 (i_in_well_not_quad at lock 41)",
  "2026-10-09 m6r1 yachi lock 53 (well_filled_not_i at lock 59)", "2026-10-09 m7r6 yachi lock 11 (round_ended)",
  "2026-10-09 m7r8 yachi lock 56 (well_filled_not_i at lock 63)",
  "2026-10-09 m11r2 pinglamb lock 116 (well_filled_not_i at lock 118)",
  "2026-10-12 m1r3 yachi lock 81 (well_filled_not_i at lock 82)",
  "2026-10-12 m1r4 yachi lock 70 (well_covered at lock 71)",
  "2026-10-12 m3r1 yachi lock 40 (well_filled_not_i at lock 44)",
  "2026-10-12 m6r7 pinglamb lock 46 (well_filled_not_i at lock 59)",
  "2026-10-12 m8r1 pinglamb lock 45 (well_covered at lock 52)",
];

const GARBAGE_IN_WINDOW: string[] = [
  "2026-07-22 m1r5 yachi lock 93", "2026-07-22 m2r8 pinglamb lock 104", "2026-07-22 m3r7 yachi lock 87",
  "2026-07-22 m4r4 yachi lock 110", "2026-07-22 m9r2 yachi lock 24", "2026-07-22 m9r3 yachi lock 60",
  "2026-07-22 m10r7 yachi lock 72", "2026-07-22 m10r8 yachi lock 31", "2026-07-24 m3r1 pinglamb lock 115",
  "2026-07-24 m3r8 pinglamb lock 24", "2026-07-28 m2r8 yachi lock 72", "2026-07-28 m3r7 pinglamb lock 32",
  "2026-07-28 m7r6 yachi lock 74", "2026-08-01 m2r4 yachi lock 111", "2026-08-01 m3r5 pinglamb lock 40",
  "2026-08-01 m3r5 yachi lock 74", "2026-08-01 m4r1 pinglamb lock 186", "2026-08-01 m4r1 yachi lock 129",
  "2026-08-01 m4r2 yachi lock 84", "2026-08-01 m6r1 yachi lock 117", "2026-08-01 m6r5 yachi lock 120",
  "2026-08-01 m7r1 yachi lock 170", "2026-08-09 m3r3 yachi lock 44", "2026-08-09 m4r6 yachi lock 28",
  "2026-08-09 m6r3 pinglamb lock 77", "2026-08-14 m1r4 pinglamb lock 40", "2026-08-14 m2r4 yachi lock 191",
  "2026-08-14 m5r8 pinglamb lock 134", "2026-08-14 m7r8 pinglamb lock 41", "2026-08-14 m11r2 yachi lock 182",
  "2026-08-19 m1r6 yachi lock 61", "2026-08-19 m3r4 yachi lock 83", "2026-08-19 m3r4 yachi lock 118",
  "2026-08-19 m6r2 yachi lock 104", "2026-08-19 m6r5 yachi lock 13", "2026-08-19 m10r2 pinglamb lock 66",
  "2026-08-19 m10r5 yachi lock 16", "2026-08-25 m1r6 yachi lock 27", "2026-08-25 m1r9 pinglamb lock 43",
  "2026-08-25 m3r2 pinglamb lock 242", "2026-08-25 m3r4 yachi lock 36", "2026-08-25 m4r2 pinglamb lock 29",
  "2026-08-25 m5r8 yachi lock 56", "2026-08-25 m8r2 pinglamb lock 143", "2026-08-25 m9r7 pinglamb lock 108",
  "2026-09-03 m3r4 pinglamb lock 120", "2026-09-03 m5r4 pinglamb lock 23", "2026-09-10 m1r1 pinglamb lock 25",
  "2026-09-10 m1r5 pinglamb lock 101", "2026-09-10 m3r4 pinglamb lock 58", "2026-09-10 m4r7 yachi lock 34",
  "2026-09-10 m6r3 pinglamb lock 86", "2026-09-10 m8r8 yachi lock 230", "2026-09-11 m1r8 pinglamb lock 107",
  "2026-09-11 m4r4 pinglamb lock 40", "2026-09-17 m1r8 yachi lock 75", "2026-09-17 m2r6 yachi lock 81",
  "2026-09-17 m3r6 pinglamb lock 130", "2026-09-18 m1r6 pinglamb lock 75", "2026-09-18 m7r4 yachi lock 44",
  "2026-09-18 m7r6 yachi lock 58", "2026-09-18 m14r4 yachi lock 53", "2026-09-18 m15r7 yachi lock 62",
  "2026-09-18 m16r2 pinglamb lock 149", "2026-09-18 m18r1 pinglamb lock 57", "2026-09-18 m18r5 pinglamb lock 55",
  "2026-09-19 m1r2 yachi lock 161", "2026-09-19 m4r3 pinglamb lock 123", "2026-09-19 m5r2 pinglamb lock 72",
  "2026-09-19 m5r2 yachi lock 10", "2026-09-19 m6r5 yachi lock 72", "2026-09-19 m7r1 pinglamb lock 43",
  "2026-09-19 m7r4 yachi lock 103", "2026-09-19 m7r4 yachi lock 148", "2026-09-19 m8r6 yachi lock 23",
  "2026-09-19 m11r2 pinglamb lock 40", "2026-09-19 m12r3 pinglamb lock 14", "2026-09-19 m12r4 yachi lock 51",
  "2026-09-19 m14r3 yachi lock 154", "2026-09-19 m15r4 pinglamb lock 129", "2026-09-19 m16r5 yachi lock 49",
  "2026-09-19 m19r1 pinglamb lock 102", "2026-09-19 m20r1 pinglamb lock 69", "2026-09-19 m20r5 pinglamb lock 30",
  "2026-10-03 m7r7 yachi lock 172", "2026-10-03 m9r6 pinglamb lock 68", "2026-10-03 m10r1 yachi lock 53",
  "2026-10-03 m10r6 yachi lock 88", "2026-10-03 m10r6 yachi lock 107", "2026-10-03 m15r3 pinglamb lock 66",
  "2026-10-09 m2r5 yachi lock 70", "2026-10-09 m2r6 yachi lock 23", "2026-10-09 m3r6 pinglamb lock 49",
  "2026-10-09 m4r2 yachi lock 26", "2026-10-09 m5r2 pinglamb lock 33", "2026-10-09 m6r1 yachi lock 53",
  "2026-10-09 m6r8 pinglamb lock 26", "2026-10-09 m7r6 yachi lock 11", "2026-10-09 m10r8 yachi lock 44",
  "2026-10-12 m1r3 yachi lock 81", "2026-10-12 m4r2 pinglamb lock 52", "2026-10-12 m6r7 pinglamb lock 46",
  "2026-10-12 m8r1 pinglamb lock 45",
];

const KAIDAN_IN_OPENER: string[] = [
  "2026-08-19 m6r5 yachi lock 13", "2026-08-19 m10r5 yachi lock 16", "2026-09-19 m5r2 yachi lock 10",
  "2026-09-19 m12r3 pinglamb lock 14", "2026-10-09 m7r6 yachi lock 11",
];

const WELL_DEPTH_LT4: string[] = [
  "2026-07-22 m1r5 yachi lock 93 (3 deep)", "2026-07-22 m3r1 yachi lock 41 (3 deep)",
  "2026-07-22 m3r7 yachi lock 87 (2 deep)", "2026-07-22 m4r4 yachi lock 110 (2 deep)",
  "2026-07-22 m10r8 yachi lock 31 (3 deep)", "2026-07-24 m5r5 yachi lock 31 (2 deep)",
  "2026-07-24 m7r2 yachi lock 25 (3 deep)", "2026-07-28 m2r8 yachi lock 72 (3 deep)",
  "2026-08-01 m1r5 yachi lock 75 (2 deep)", "2026-08-01 m2r4 yachi lock 111 (3 deep)",
  "2026-08-01 m3r5 yachi lock 74 (3 deep)", "2026-08-01 m4r1 yachi lock 129 (3 deep)",
  "2026-08-01 m4r2 yachi lock 84 (2 deep)", "2026-08-01 m7r6 yachi lock 66 (3 deep)",
  "2026-08-09 m3r3 yachi lock 44 (2 deep)", "2026-08-09 m5r5 pinglamb lock 70 (2 deep)",
  "2026-08-09 m6r3 pinglamb lock 77 (2 deep)", "2026-08-14 m2r4 pinglamb lock 159 (2 deep)",
  "2026-08-14 m7r8 pinglamb lock 41 (3 deep)", "2026-08-14 m9r6 pinglamb lock 38 (3 deep)",
  "2026-08-14 m11r2 yachi lock 182 (3 deep)", "2026-08-19 m4r8 yachi lock 29 (2 deep)",
  "2026-08-19 m6r2 yachi lock 104 (2 deep)", "2026-08-25 m1r6 yachi lock 27 (2 deep)",
  "2026-08-25 m3r2 pinglamb lock 242 (3 deep)", "2026-08-25 m3r2 yachi lock 85 (3 deep)",
  "2026-08-25 m3r4 yachi lock 36 (3 deep)", "2026-08-25 m5r8 yachi lock 56 (3 deep)",
  "2026-08-25 m9r2 pinglamb lock 47 (3 deep)", "2026-09-03 m3r4 pinglamb lock 120 (2 deep)",
  "2026-09-10 m1r1 pinglamb lock 25 (3 deep)", "2026-09-10 m3r6 yachi lock 25 (3 deep)",
  "2026-09-10 m4r7 yachi lock 34 (2 deep)", "2026-09-11 m3r6 pinglamb lock 52 (3 deep)",
  "2026-09-11 m6r6 pinglamb lock 139 (2 deep)", "2026-09-11 m6r7 yachi lock 26 (3 deep)",
  "2026-09-17 m1r8 yachi lock 75 (2 deep)", "2026-09-17 m2r6 yachi lock 81 (3 deep)",
  "2026-09-17 m3r1 yachi lock 26 (3 deep)", "2026-09-18 m7r4 yachi lock 44 (3 deep)",
  "2026-09-18 m16r3 yachi lock 167 (3 deep)", "2026-09-18 m16r4 yachi lock 117 (2 deep)",
  "2026-09-19 m1r2 yachi lock 161 (2 deep)", "2026-09-19 m2r1 yachi lock 39 (2 deep)",
  "2026-09-19 m2r1 yachi lock 65 (2 deep)", "2026-09-19 m5r2 yachi lock 10 (2 deep)",
  "2026-09-19 m7r4 yachi lock 148 (2 deep)", "2026-09-19 m8r2 yachi lock 38 (2 deep)",
  "2026-09-19 m12r3 pinglamb lock 14 (3 deep)", "2026-09-19 m12r4 yachi lock 42 (2 deep)",
  "2026-09-19 m12r4 yachi lock 51 (2 deep)", "2026-09-19 m14r3 yachi lock 154 (3 deep)",
  "2026-09-19 m15r4 pinglamb lock 129 (2 deep)", "2026-09-19 m19r1 yachi lock 23 (2 deep)",
  "2026-09-19 m20r1 pinglamb lock 69 (2 deep)", "2026-10-03 m5r6 pinglamb lock 61 (3 deep)",
  "2026-10-03 m9r6 pinglamb lock 68 (3 deep)", "2026-10-03 m10r1 yachi lock 53 (2 deep)",
  "2026-10-03 m10r6 yachi lock 88 (2 deep)", "2026-10-03 m10r6 yachi lock 107 (3 deep)",
  "2026-10-03 m13r5 yachi lock 104 (3 deep)", "2026-10-09 m3r6 pinglamb lock 49 (3 deep)",
  "2026-10-09 m3r8 yachi lock 59 (2 deep)", "2026-10-09 m4r2 yachi lock 26 (2 deep)",
  "2026-10-09 m4r2 yachi lock 132 (2 deep)", "2026-10-09 m5r8 pinglamb lock 38 (2 deep)",
  "2026-10-09 m6r1 yachi lock 53 (2 deep)", "2026-10-09 m7r8 yachi lock 56 (2 deep)",
  "2026-10-12 m1r3 pinglamb lock 99 (2 deep)", "2026-10-12 m1r3 yachi lock 81 (2 deep)",
  "2026-10-12 m8r1 pinglamb lock 45 (2 deep)",
];

const RECON_DROPPED_TSD: string[] = [];

/** The hits that are not harddrop Donations at their well column, each with the first clause it fails (re-derived
 *  in the donation test). */
const HIT_NOT_DONATION: string[] = [
  "2026-07-22 m1r5 yachi lock 93 (filled_above_window)", "2026-07-22 m10r8 yachi lock 31 (filled_above_window)",
  "2026-07-22 m2r8 pinglamb lock 104 (filled_above_window)", "2026-07-22 m3r1 yachi lock 41 (filled_above_window)",
  "2026-07-22 m3r7 yachi lock 87 (filled_above_window)", "2026-07-22 m4r4 yachi lock 110 (filled_above_window)",
  "2026-07-22 m9r3 yachi lock 60 (filled_above_window)", "2026-07-24 m3r1 pinglamb lock 115 (filled_above_window)",
  "2026-07-24 m5r5 yachi lock 31 (cavity_lt4)", "2026-07-24 m7r2 yachi lock 25 (cavity_lt4)",
  "2026-07-28 m2r8 yachi lock 72 (filled_above_window)", "2026-07-28 m3r7 pinglamb lock 32 (filled_above_window)",
  "2026-07-28 m6r5 yachi lock 122 (filled_above_window)", "2026-07-28 m7r6 yachi lock 74 (filled_above_window)",
  "2026-08-01 m1r5 pinglamb lock 208 (filled_above_window)", "2026-08-01 m1r5 yachi lock 75 (filled_above_window)",
  "2026-08-01 m2r4 yachi lock 111 (filled_above_window)", "2026-08-01 m3r5 pinglamb lock 40 (filled_above_window)",
  "2026-08-01 m3r5 yachi lock 74 (filled_above_window)", "2026-08-01 m4r1 yachi lock 129 (filled_above_window)",
  "2026-08-01 m4r2 yachi lock 84 (filled_above_window)", "2026-08-01 m6r1 yachi lock 80 (filled_above_window)",
  "2026-08-01 m7r1 yachi lock 170 (filled_above_window)", "2026-08-01 m7r3 pinglamb lock 78 (filled_above_window)",
  "2026-08-01 m7r6 yachi lock 66 (filled_above_window)", "2026-08-09 m3r3 yachi lock 44 (filled_above_window)",
  "2026-08-09 m4r2 pinglamb lock 42 (filled_above_window)",
  "2026-08-09 m4r3 pinglamb lock 138 (filled_above_window)", "2026-08-09 m4r6 yachi lock 28 (filled_above_window)",
  "2026-08-09 m5r5 pinglamb lock 70 (filled_above_window)", "2026-08-09 m6r3 pinglamb lock 77 (filled_above_window)",
  "2026-08-14 m1r4 pinglamb lock 40 (filled_above_window)", "2026-08-14 m2r4 yachi lock 191 (filled_above_window)",
  "2026-08-14 m2r4 pinglamb lock 159 (filled_above_window)", "2026-08-14 m11r2 yachi lock 182 (filled_above_window)",
  "2026-08-14 m5r8 pinglamb lock 134 (filled_above_window)",
  "2026-08-14 m7r8 pinglamb lock 41 (filled_above_window)", "2026-08-14 m9r6 pinglamb lock 38 (filled_above_window)",
  "2026-08-19 m1r6 yachi lock 61 (filled_above_window)", "2026-08-19 m10r2 pinglamb lock 66 (filled_above_window)",
  "2026-08-19 m10r5 yachi lock 16 (filled_above_window)", "2026-08-19 m3r4 yachi lock 83 (filled_above_window)",
  "2026-08-19 m3r4 yachi lock 118 (filled_above_window)", "2026-08-19 m4r8 yachi lock 29 (filled_above_window)",
  "2026-08-19 m5r2 yachi lock 32 (filled_above_window)", "2026-08-19 m6r2 yachi lock 104 (filled_above_window)",
  "2026-08-19 m6r3 yachi lock 38 (filled_above_window)", "2026-08-25 m1r6 yachi lock 27 (filled_above_window)",
  "2026-08-25 m3r2 pinglamb lock 242 (filled_above_window)", "2026-08-25 m3r2 yachi lock 85 (filled_above_window)",
  "2026-08-25 m3r4 yachi lock 36 (cavity_lt4)", "2026-08-25 m4r2 pinglamb lock 29 (filled_above_window)",
  "2026-08-25 m5r8 yachi lock 56 (filled_above_window)", "2026-08-25 m9r2 pinglamb lock 47 (filled_above_window)",
  "2026-08-25 m9r7 pinglamb lock 108 (filled_above_window)",
  "2026-09-03 m3r4 pinglamb lock 120 (filled_above_window)",
  "2026-09-10 m1r1 pinglamb lock 25 (filled_above_window)",
  "2026-09-10 m1r5 pinglamb lock 101 (filled_above_window)", "2026-09-10 m3r6 yachi lock 25 (filled_above_window)",
  "2026-09-10 m4r7 yachi lock 34 (filled_above_window)", "2026-09-10 m5r9 yachi lock 64 (filled_above_window)",
  "2026-09-10 m6r3 pinglamb lock 86 (filled_above_window)", "2026-09-10 m8r8 yachi lock 230 (filled_above_window)",
  "2026-09-11 m1r8 pinglamb lock 107 (filled_above_window)",
  "2026-09-11 m3r6 pinglamb lock 52 (filled_above_window)", "2026-09-11 m4r4 pinglamb lock 40 (filled_above_window)",
  "2026-09-11 m6r6 pinglamb lock 139 (filled_above_window)", "2026-09-11 m6r7 yachi lock 26 (filled_above_window)",
  "2026-09-17 m1r8 yachi lock 75 (filled_above_window)", "2026-09-17 m2r6 yachi lock 81 (cavity_lt4)",
  "2026-09-17 m3r1 yachi lock 26 (filled_above_window)", "2026-09-18 m7r4 yachi lock 44 (filled_above_window)",
  "2026-09-18 m7r6 yachi lock 58 (filled_above_window)", "2026-09-18 m15r7 yachi lock 62 (filled_above_window)",
  "2026-09-18 m16r2 pinglamb lock 149 (filled_above_window)",
  "2026-09-18 m16r3 yachi lock 167 (filled_above_window)", "2026-09-18 m16r4 yachi lock 117 (cavity_lt4)",
  "2026-09-18 m18r5 pinglamb lock 55 (filled_above_window)", "2026-09-19 m1r2 yachi lock 161 (filled_above_window)",
  "2026-09-19 m2r1 yachi lock 39 (cavity_lt4)", "2026-09-19 m2r1 yachi lock 65 (filled_above_window)",
  "2026-09-19 m4r3 pinglamb lock 123 (filled_above_window)",
  "2026-09-19 m5r2 pinglamb lock 72 (filled_above_window)", "2026-09-19 m5r2 yachi lock 10 (cavity_lt4)",
  "2026-09-19 m6r5 yachi lock 72 (filled_above_window)", "2026-09-19 m7r4 yachi lock 103 (filled_above_window)",
  "2026-09-19 m7r4 yachi lock 148 (filled_above_window)", "2026-09-19 m8r2 yachi lock 38 (filled_above_window)",
  "2026-09-19 m11r2 pinglamb lock 40 (filled_above_window)",
  "2026-09-19 m12r3 pinglamb lock 14 (filled_above_window)", "2026-09-19 m12r4 yachi lock 42 (cavity_lt4)",
  "2026-09-19 m12r4 yachi lock 51 (cavity_lt4)", "2026-09-19 m14r3 yachi lock 154 (filled_above_window)",
  "2026-09-19 m15r4 pinglamb lock 129 (filled_above_window)",
  "2026-09-19 m19r1 pinglamb lock 102 (filled_above_window)", "2026-09-19 m19r1 yachi lock 23 (cavity_lt4)",
  "2026-09-19 m20r1 pinglamb lock 69 (filled_above_window)", "2026-10-03 m4r8 yachi lock 108 (filled_above_window)",
  "2026-10-03 m5r6 pinglamb lock 61 (cavity_lt4)", "2026-10-03 m7r7 yachi lock 172 (filled_above_window)",
  "2026-10-03 m9r6 pinglamb lock 68 (filled_above_window)", "2026-10-03 m10r1 yachi lock 53 (filled_above_window)",
  "2026-10-03 m10r6 yachi lock 88 (filled_above_window)", "2026-10-03 m10r6 yachi lock 107 (filled_above_window)",
  "2026-10-03 m13r5 yachi lock 104 (filled_above_window)", "2026-10-03 m14r2 yachi lock 60 (filled_above_window)",
  "2026-10-03 m15r3 pinglamb lock 66 (filled_above_window)",
  "2026-10-03 m17r8 pinglamb lock 135 (filled_above_window)", "2026-10-09 m1r2 yachi lock 68 (filled_above_window)",
  "2026-10-09 m2r6 yachi lock 23 (filled_above_window)", "2026-10-09 m3r6 pinglamb lock 49 (cavity_lt4)",
  "2026-10-09 m3r8 yachi lock 59 (filled_above_window)", "2026-10-09 m4r2 yachi lock 26 (cavity_lt4)",
  "2026-10-09 m4r2 yachi lock 132 (filled_above_window)", "2026-10-09 m5r8 pinglamb lock 38 (filled_above_window)",
  "2026-10-09 m6r1 yachi lock 53 (filled_above_window)", "2026-10-09 m6r8 pinglamb lock 26 (filled_above_window)",
  "2026-10-09 m7r6 yachi lock 11 (filled_above_window)", "2026-10-09 m7r8 yachi lock 56 (filled_above_window)",
  "2026-10-09 m11r2 pinglamb lock 116 (filled_above_window)",
  "2026-10-12 m1r3 pinglamb lock 99 (filled_above_window)", "2026-10-12 m1r3 yachi lock 81 (filled_above_window)",
  "2026-10-12 m1r4 yachi lock 70 (filled_above_window)", "2026-10-12 m3r1 yachi lock 40 (filled_above_window)",
  "2026-10-12 m4r2 pinglamb lock 52 (filled_above_window)", "2026-10-12 m6r7 pinglamb lock 46 (filled_above_window)",
  "2026-10-12 m8r1 pinglamb lock 45 (cavity_lt4)",
];

/** 社畜トレイン's window and this one agree, anchored on the same flat T in the same hand, on every cell they share:
 *  a lock that is a hit of both is possible, and these are the ones (named, measured, never asserted absent). */
const SHACHIKUTRAIN_ALSO_KAIDAN: string[] = [
  "2026-07-22 m3r1 yachi lock 41", "2026-07-22 m4r4 yachi lock 110", "2026-07-22 m9r2 yachi lock 24",
  "2026-07-22 m10r8 yachi lock 31", "2026-07-24 m3r8 pinglamb lock 24", "2026-07-24 m7r2 yachi lock 25",
  "2026-07-28 m2r8 yachi lock 72", "2026-08-01 m3r5 pinglamb lock 40", "2026-08-01 m4r1 pinglamb lock 186",
  "2026-08-01 m4r2 yachi lock 84", "2026-08-01 m6r1 yachi lock 80", "2026-08-01 m6r1 yachi lock 117",
  "2026-08-01 m7r1 yachi lock 170", "2026-08-09 m5r5 pinglamb lock 70", "2026-08-14 m1r4 pinglamb lock 40",
  "2026-08-14 m5r8 pinglamb lock 134", "2026-08-14 m7r8 pinglamb lock 41", "2026-08-19 m3r4 yachi lock 118",
  "2026-08-19 m10r2 pinglamb lock 66", "2026-08-19 m10r5 yachi lock 16", "2026-08-25 m1r6 yachi lock 27",
  "2026-08-25 m1r9 pinglamb lock 43", "2026-08-25 m5r8 yachi lock 56", "2026-09-03 m5r4 pinglamb lock 23",
  "2026-09-10 m6r3 pinglamb lock 86", "2026-09-11 m1r8 pinglamb lock 107", "2026-09-17 m1r8 yachi lock 75",
  "2026-09-18 m7r6 yachi lock 58", "2026-09-18 m18r5 pinglamb lock 55", "2026-09-19 m6r5 yachi lock 72",
  "2026-09-19 m7r4 yachi lock 148", "2026-09-19 m8r2 yachi lock 38", "2026-09-19 m11r2 pinglamb lock 40",
  "2026-09-19 m12r3 pinglamb lock 14", "2026-09-19 m12r4 yachi lock 51", "2026-10-03 m4r8 yachi lock 108",
  "2026-10-03 m7r7 yachi lock 172", "2026-10-03 m13r5 yachi lock 104", "2026-10-09 m2r5 yachi lock 70",
  "2026-10-09 m3r6 pinglamb lock 49", "2026-10-09 m4r2 yachi lock 26", "2026-10-09 m6r1 yachi lock 53",
  "2026-10-09 m6r8 pinglamb lock 26", "2026-10-09 m7r6 yachi lock 11", "2026-10-09 m7r8 yachi lock 56",
  "2026-10-12 m1r3 yachi lock 81", "2026-10-12 m3r1 yachi lock 40", "2026-10-12 m4r2 pinglamb lock 52",
  "2026-10-12 m6r7 pinglamb lock 46",
];

/** window_off_board, per player: a count with a property check, not a list (see the header). */
const WINDOW_OFF_BOARD = { pinglamb: 753, yachi: 587 };
/** Per player: the opportunities (scored full TSDs), split at the 0-based opener window. */
const DENOM = {
  pinglamb: { all: 5307, in_opener: 1043, mid_game: 4264 },
  yachi: { all: 4751, in_opener: 1242, mid_game: 3509 },
};
/** Per player: hits, their split, mirrored, garbage in the window. */
const HITS = {
  pinglamb: { all: 62, in_opener: 1, mid_game: 61, mirrored: 35, garbage_in_window: 46 },
  yachi: { all: 92, in_opener: 4, mid_game: 88, mirrored: 43, garbage_in_window: 57 },
};
/** Per player: the payoff (stored under `followup_by_player`, the shared artefact key). */
const PAYOFF = {
  pinglamb: { fired: 36, not_fired: { i_in_well_not_quad: 7, round_ended: 2, well_covered: 8, well_filled_not_i: 9 } },
  yachi: { fired: 35, not_fired: { i_in_well_not_quad: 6, past_verified: 2, round_ended: 1, well_covered: 26,
                                   well_filled_not_i: 22 } },
};
const CONTROLS = {
  under: { TSS: { pinglamb: 3, yachi: 8 }, TST: { pinglamb: 0, yachi: 0 },
           mini_TSS: { pinglamb: 0, yachi: 0 }, mini_TSD: { pinglamb: 0, yachi: 0 } },
  ablation: { no_must_empty: { pinglamb: 981, yachi: 795 }, no_roof: { pinglamb: 273, yachi: 228 },
              t_overlap: { pinglamb: 251, yachi: 279 } },
  orientation_baseline: { pinglamb: 43, yachi: 61 },
};
/** What discriminates, measured: full TSDs (not only hits) whose anchored flat T meets ONE part of the window — the
 *  roof row above the cleared rows, the cleared rows, the well rows under them. The cleared rows are entailed by the
 *  clear (NaiveClauseForced) and do the least work; the well rows do the most, and are exactly the `no_roof`
 *  ablation (the cleared rows add nothing to them at a full TSD). */
const PART_ONLY = { above: 3083, cleared: 8786, below: 501 };
/** THE OTHER TWO MAXIMAL AGREEMENT BOXES (the window's note): measured as controls, never asserted against. In
 *  basic.spin's frame: the cleared rows alone (every cell entailed), and the cleared rows with the two well rows, one
 *  column wider to the left and with no roof row. `n` the full TSDs each admits, `hits` how many of this window's hits
 *  are among them. */
const OTHER_MAXIMAL_BOXES = {
  cleared_only: { window: { rows: [2, 3], cols: [3, 9] }, n: 8786, hits: 154 },
  no_roof: { window: { rows: [2, 5], cols: [4, 9] }, n: 451, hits: 136 },
};

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
  followupAnyT: 'the variant carries a payoff, not a follow-up: there is no follow-up T to relax',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(KAIDAN, m, digests());
const nameOf = (d: TechDigest, lock: number) => `${d.session} m${d.match}r${d.round + 1} ${d.user} lock ${lock}`;
const hitKey = (h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`;
const keyOf = (d: TechDigest, lock: number) => `${d.session}|${d.file}|${d.round}|${d.user}|${lock}`;
const USERS = ['pinglamb', 'yachi'] as const;

/** A drawing (rows top first, '-' or '.' empty) as a 40-row matcher board, every other cell filled. */
const pad = (rows: string[]) => [...Array(H - rows.length).fill('.'.repeat(W)),
                                 ...rows.map(r => [...r].map(ch => ch === '-' || ch === '.' ? '.' : 'X').join(''))];
/** a harddrop board as the board before its drawn T and its ghost piece (`U`, `v` read empty) */
const preOf = (rows: string[]) => rows.map(r => r.replace(/[Uv]/g, '-'));
/** every T placement on a board (any lie), resting or not: the window anchors on the cells alone */
function tPlacements(board: string[]) {
  const shapes = [[[0, 0], [0, 1], [0, 2], [1, 1]], [[0, 1], [1, 0], [1, 1], [1, 2]],
                  [[0, 0], [1, 0], [2, 0], [1, 1]], [[0, 1], [1, 0], [1, 1], [2, 1]]];
  const out: Cell[][] = [];
  for (const sh of shapes) for (let r = 0; r < board.length; r++) for (let c = 0; c < W; c++) {
    const cells = sh.map(([dr, dc]) => ({ row: r + dr!, col: c + dc! }));
    if (cells.every(q => q.row < board.length && q.col < W && board[q.row]![q.col] === '.')) out.push(cells);
  }
  return out;
}
const fires = (v: any, board: string[], lock: Cell[]) =>
  prepare(TR, v).filter(P => !!windowMatch(board, lock, P)).map(P => P.mirrored);
/** where the window fires on a drawing: [cells (drawing frame), mirrored] for every T placement */
const firesAnywhere = (rows: string[], v: any = V) => {
  const b = pad(rows), top = H - rows.length;
  return tPlacements(b).flatMap(cs => fires(v, b, cs).map(m => [cs.map(q => [q.row - top, q.col]).sort((x, y) => x[0]! - y[0]! || x[1]! - y[1]!), m]));
};
const sorted = (s: number[][]) => [...s].map(x => [...x]).sort((x, y) => x[0]! - y[0]! || x[1]! - y[1]!);

test('the committed artefact is what build() produces now (byte identity)', () => {
  expect(serialise(run({}))).toBe(readFileSync(ART_PATH, 'utf8'));
}, 600_000);

test('quarantined: report_eligible false, no claim ids, one variant measured at the full TSD', () => {
  const a = art();
  expect(a.report_eligible).toBe(false);
  expect(JSON.stringify(a)).not.toMatch(/data-claim|\b[CRG]\d{3}\b|✓/);
  expect(a.sessions).toEqual(SESSIONS);
  expect(a.cross_route).toBeUndefined();
  expect(Object.keys(a.variants)).toEqual(['kaidan']);
  // every hit carries its well depth, at least the two cells the window entails
  for (const h of a.hits) expect(h.well_depth, `${h.session} ${h.lock}`).toBeGreaterThanOrEqual(2);
});

test('the scored T-spins are the ones emit-opener-facts.ts scores (the third copy of the loop)', () => {
  const n = checkScoredAgainstOpenerFacts(art(), SESSIONS, ROOT);
  expect(n).toBe(14176);
  expect(art().check.reconstruction_disagreed).toBe(0);
});

test('the Python twin on the drawings: windowMatch fires where the gate records it, and nowhere else', () => {
  const xs = TR.cross_source;
  // the page's own builds, as drawn, and its two DT砲 boards, mirrored: at their agreement slots, once
  for (const a of V.agreement) expect(firesAnywhere(byId.get(a.board).rows), a.board)
    .toEqual([[sorted(a.t_cells), a.mirrored]]);
  // the page's boards the gate lists as misses: never
  for (const id of V.misses) expect(firesAnywhere(byId.get(id).rows), id).toEqual([]);
  // harddrop: every drawing at its slot in its hand; every no-T board the gate names at its placement; no drawn T the
  // gate names as a miss (at the T itself, either hand)
  for (const key of ['harddrop', 'harddrop_anchor_set']) {
    const rec = xs[key];
    for (const d of rec.drawings) expect(firesAnywhere(preOf(d.rows)), `${key} #${d.n}`).toEqual([[sorted(d.slot), d.mirrored]]);
    for (const d of rec.fires_without_slot)
      expect(firesAnywhere(preOf(d.rows)), `${key} #${d.n}`).toEqual([[sorted(d.slot), d.mirrored]]);
    for (const d of rec.drawn_t_not_fired) {
      const b = pad(preOf(d.rows)), top = H - d.rows.length;
      expect(fires(V, b, d.slot.map(([r, c]: number[]) => ({ row: r! + top, col: c! }))), `${key} #${d.n}`).toEqual([]);
    }
  }
  expect(firesAnywhere(preOf(xs.harddrop_anchor_set.payoff_drawing.rows))).toEqual([]);
  // the Kaidan BT砲's harddrop record holds, read from btcannon-technique.json: once, mirrored, at its drawn T
  const bt = JSON.parse(readFileSync(`${import.meta.dir}/${xs.bt_cannon.file}`, 'utf8')).cross_source.harddrop;
  const btd = bt[xs.bt_cannon.list].find((e: any) => e.table === xs.bt_cannon.table && e.board === xs.bt_cannon.board);
  const btSlot = btd.rows.flatMap((r: string, i: number) => [...r].flatMap((ch, c) => ch === 'U' ? [[i, c]] : []));
  expect(firesAnywhere(preOf(btd.rows))).toEqual([[sorted(btSlot), true]]);
  // STMB_Cave's Kaidan is drawn one row under the clear: its window leaves the board, so it fires nowhere
  expect(firesAnywhere(preOf(xs.stmb_cave_kaidan.rows))).toEqual([]);
  // the routes boards: no board of any routes file, at any T placement (the gate scans the U slots; this scans all)
  const got: string[] = [];
  for (const f of readdirSync(import.meta.dir).filter(x => x.endsWith('-routes.json')).sort())
    for (const n of JSON.parse(readFileSync(`${import.meta.dir}/${f}`, 'utf8')).nodes) {
      if (!n.rows) continue;
      for (const [cells, m] of firesAnywhere(n.rows.map((r: string) => r.replace(/U/g, '-'))))
        got.push(`${f} ${n.id} ${JSON.stringify(cells)}${m ? ' (mirrored)' : ''}`);
    }
  expect(got).toEqual([]);
  expect([xs.fires, xs.also]).toEqual([[], []]);
  expect(xs.routes_fire_none.length).toBeGreaterThan(0);
}, 120_000);

test('the transcription the artefact read is the committed one, and its window is the gated one', () => {
  expect(TR.variants.length).toBe(1);
  expect(V.window_basis).toBe('agreement');
  expect(V.window).toEqual({ rows: [1, 5], cols: [5, 9] });
  expect([V.spin, V.lines]).toEqual(['TSD', 2]);
  expect(V.t_cells).toEqual([[2, 6], [2, 7], [2, 8], [3, 7]]);
  expect(V.followup).toBeUndefined();
  expect(V.payoff).toMatchObject({ kind: 'well_quad', piece: 'I', lines: 4, well_cell_pre_clear: [4, 9] });
  // the payoff variant carries no follow-up slot, and its well is mirrored with the window
  const [d, m] = prepare(TR, V);
  expect([d!.followup, d!.followupKind, m!.followup, m!.followupKind]).toEqual([[], '', [], '']);
  expect([d!.well, m!.well]).toEqual([{ r: 4, c: 9 }, { r: 4, c: 5 }]);
  expect(TR.empty_letters).toBe('');
  // the payoff is attributed to harddrop, never to shiwehi.com (which names ST積み and よしひろ積み)
  expect(V.payoff.note).toContain('HARDDROP');
  expect(V.payoff.note).toContain(TR.cross_source.harddrop.quote);
});

test('named lists: every hit, every payoff miss, the opener hits, garbage, shallow wells, the empty lists', () => {
  const L = art().lists;
  checkNamedList('kaidan_hits', L.kaidan_hits, KAIDAN_HITS);
  checkNamedList('payoff_not_fired', L.payoff_not_fired, PAYOFF_NOT_FIRED);
  checkNamedList('garbage_in_window', L.garbage_in_window, GARBAGE_IN_WINDOW);
  checkNamedList('kaidan_in_opener', L.kaidan_in_opener, KAIDAN_IN_OPENER);
  checkNamedList('well_depth_lt4', L.well_depth_lt4, WELL_DEPTH_LT4);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, RECON_DROPPED_TSD);
  checkHitPositions(art(), SESSIONS, ROOT, [...KAIDAN_HITS, ...PAYOFF_NOT_FIRED, ...GARBAGE_IN_WINDOW, ...KAIDAN_IN_OPENER,
                                            ...WELL_DEPTH_LT4, ...HIT_NOT_DONATION, ...SHACHIKUTRAIN_ALSO_KAIDAN]);
  expect(art().hits.length).toBe(KAIDAN_HITS.length);
});

test('window_off_board: pinned per player, every entry a flat T at a full TSD whose window leaves the board', () => {
  const L: string[] = art().lists.window_off_board;
  for (const u of USERS) expect(L.filter(x => x.split(' ')[2] === u).length, u).toBe(WINDOW_OFF_BOARD[u]);
  const want = new Set<string>();
  const hits = new Set(art().hits.map(hitKey));
  const Ps = prepare(TR, V);
  for (const d of digests()) for (const s of scored(d)) {
    if (s.lk.spin !== 'full' || s.lk.cleared !== V.lines || hits.has(keyOf(d, s.i))) continue;
    if (Ps.some(P => windowMatch(s.board, s.lk.cells, P) === null) && !Ps.some(P => !!windowMatch(s.board, s.lk.cells, P)))
      want.add(nameOf(d, s.i));
  }
  for (const x of L) expect(want.has(x), x).toBe(true);
  expect(new Set(L).size).toBe(L.length);
  expect(L.length).toBe(want.size);
}, 600_000);

test('pinned: denominators, hits, payoffs, controls; the structural zeros re-derived from the window', () => {
  const a = art();
  for (const u of USERS) {
    expect(a.denominators[u].TSD, u).toEqual(DENOM[u]);
    expect(a.variants.kaidan.hits_by_player[u], u).toEqual(HITS[u]);
    expect(a.variants.kaidan.followup_by_player[u], u).toEqual(PAYOFF[u]);
    expect(PAYOFF[u].fired + total(PAYOFF[u].not_fired)).toBe(HITS[u].all);
  }
  expect(a.variants.kaidan.controls).toEqual(CONTROLS);
  // STRUCTURAL, not measured: under this window a TST cannot anchor — a lock clears only rows it puts a cell in, and
  // the window's flat T spans two rows, so it is re-derived here and not only pinned
  expect(new Set(V.t_cells.map((x: number[]) => x[0])).size).toBe(2);
  for (const u of USERS) expect(a.variants.kaidan.controls.under.TST[u]).toBe(0);
  // the no_roof ablation is the well rows alone: at a full TSD the cleared rows the window reads are entailed
  expect(total(a.variants.kaidan.controls.ablation.no_roof)).toBe(PART_ONLY.below);
  for (const P of prepare(TR, V)) expect(P.cells.filter(x => x.r === 2 || x.r === 3).every(x => x.v !== '.')).toBe(true);
});

test('the other flat-T windows: clashes per hand pairing, and the hit sets', () => {
  const normP = (P: ReturnType<typeof prepare>[number]) => {
    const r = Math.min(...P.T.map(x => x.r)), c = Math.min(...P.T.map(x => x.c));
    return { T: P.T.map(x => `${x.r - r},${x.c - c}`).sort().join(' '),
             cells: new Map(P.cells.map(x => [`${x.r - r},${x.c - c}`, x.v])) };
  };
  const mine = new Set(art().hits.map(hitKey));
  for (const other of [STMBCAVE, DOUBLEDAGGER, BTCANNON, CUTCOPY, SHACHIKUTRAIN, PARAPET]) {
    const tr = JSON.parse(readFileSync(other.transcriptionPath, 'utf8'));
    // every variant of 千鳥格子 (both its windows lay the T flat, nub down; `uncut` included), the others' first
    for (const ov of (other === CUTCOPY ? tr.variants : [tr.variants[0]]))
    for (const a of prepare(TR, V)) for (const b of prepare(tr, ov)) {
      const A = normP(a), B = normP(b);
      expect(A.T, other.key).toBe(B.T);
      const shared = [...A.cells].filter(([k, v]) => B.cells.has(k) && v !== 'T');
      const clash = shared.filter(([k, v]) => B.cells.get(k) !== v);
      // 社畜トレイン: in the same hand the two windows agree on every one of the cells they share
      if (other.key === 'shachikutrain' && a.mirrored === b.mirrored) {
        expect(clash, other.key).toEqual([]);
        expect(shared.length).toBe(TR.cross_source.other_windows.shachikutrain_relation.as_drawn.shared);
      } else expect(clash.length, `${other.key} ${a.mirrored} ${b.mirrored}`).toBeGreaterThan(0);
    }
    const theirs = JSON.parse(readFileSync(other.artefactPath, 'utf8')).hits;
    const both = theirs.filter((h: any) => mine.has(hitKey(h))).map((h: any) => `${h.session} m${h.match}r${h.round} ${h.player} lock ${h.lock}`);
    if (other.key === 'shachikutrain') checkNamedList('SHACHIKUTRAIN_ALSO_KAIDAN', both, SHACHIKUTRAIN_ALSO_KAIDAN);
    else expect(both, other.key).toEqual([]);
  }
  // STSD and インペリアルクロス stand their T up: the anchors differ, so no lock can be a hit of both
  for (const other of [STSD, IMPERIALCROSS]) {
    const tr = JSON.parse(readFileSync(other.transcriptionPath, 'utf8'));
    for (const a of prepare(TR, V)) for (const b of prepare(tr, tr.variants[0])) expect(normP(a).T).not.toBe(normP(b).T);
  }
});

test('what discriminates: each part of the window alone, and the other two maximal boxes, against the headline', () => {
  const hits = new Set(art().hits.map(hitKey));
  const count = (preps: ReturnType<typeof prepare>) => {
    let n = 0, hitsIn = 0;
    for (const d of digests()) for (const s of scored(d)) {
      if (s.lk.spin !== 'full' || s.lk.cleared !== V.lines) continue;
      if (!preps.some(P => !!windowMatch(s.board, s.lk.cells, P))) continue;
      n++;
      if (hits.has(keyOf(d, s.i))) hitsIn++;
    }
    return { n, hitsIn };
  };
  const parts: Record<'above' | 'cleared' | 'below', (r: number) => boolean> = {
    above: r => r < 2, cleared: r => r === 2 || r === 3, below: r => r > 3,
  };
  const got: Record<string, number> = {};
  const headline = art().hits.length;
  for (const [name, keep] of Object.entries(parts)) {
    const { n, hitsIn } = count(prepare(TR, V).map(P => ({ ...P, cells: P.cells.filter(x => x.v === 'T' || keep(x.r)) })));
    expect(hitsIn, name).toBe(headline);
    got[name] = n;
  }
  expect(got).toEqual(PART_ONLY);
  for (const n of Object.values(got)) expect(n).toBeGreaterThan(headline);
  expect(got.below!).toBeLessThan(got.above!);
  expect(got.below!).toBeLessThan(got.cleared!);
  // the other two maximal agreement boxes, measured: what each admits and how many of the hits are among them
  for (const [name, box] of Object.entries(OTHER_MAXIMAL_BOXES)) {
    const { n, hitsIn } = count(prepare(TR, { ...V, window: box.window }));
    expect({ n, hits: hitsIn }, name).toEqual({ n: box.n, hits: box.hits });
  }
}, 600_000);

test('donation: the shipped predicate reproduced per session and player, and every hit that is not one named', () => {
  const count: Record<string, Record<string, number>> = {};
  const hits = new Map<string, any>(art().hits.map((h: any) => [hitKey(h), h]));
  const notDon: string[] = [];
  let hitDon = 0;
  for (const d of digests()) for (const s of scored(d)) {
    let any = false;
    for (let c = 0; c < W; c++) if (donationVerdict(s.withT, s.rows, s.lk.cells, c) === 'donation') any = true;
    (count[d.session] ??= {})[d.user] = (count[d.session]![d.user] ?? 0) + (any ? 1 : 0);
    const h = hits.get(keyOf(d, s.i));
    if (!h) continue;
    // the hit's well column: the well cell, under the offset the window matched at
    const P = prepare(TR, V).find(p => p.mirrored === h.mirrored)!;
    const off = windowMatch(s.board, s.lk.cells, P);
    if (!off) throw new Error(`${nameOf(d, s.i)}: the recorded hit does not match`);
    const why = donationVerdict(s.withT, s.rows, s.lk.cells, P.well!.c + off.dc);
    if (why === 'donation') hitDon++;
    else notDon.push(`${nameOf(d, s.i)} (${why})`);
  }
  for (const sess of SESSIONS) {
    const of = JSON.parse(readFileSync(`${ROOT}/${sess}/sim/opener-facts.json`, 'utf8'));
    expect(Object.keys(count[sess]!).sort(), sess).toEqual(of.donation.players.map((p: any) => p.user).sort());
    for (const p of of.donation.players) expect(count[sess]![p.user], `${sess} ${p.user}`).toBe(p.donations);
  }
  checkNamedList('HIT_NOT_DONATION', notDon, HIT_NOT_DONATION);
  expect(hitDon + notDon.length).toBe(art().hits.length);
  // the window decides the re-opening and the walls INSIDE it; what a hit fails is outside it (a filled cell over the
  // window in the well column) or below it (a well under four deep): never the T's own slot, never the naive clause
  for (const x of HIT_NOT_DONATION) expect(x).toMatch(/ \((filled_above_window|cavity_lt4)\)$/);
}, 600_000);

test('the payoff row map is verified against the engine at every step it uses', () => {
  const c = art().check;
  expect(c.rowmap_unverified).toBe(30);
  expect(c.rowmap_steps).toBe(245899);
  expect(art().hits.every((h: any) => h.followup.reason !== 'rowmap_unverified')).toBe(true);
});

test('mutants: each rule turned off turns this red with its own symptom, or is named equivalent', () => {
  const base = serialise(run({}));
  const b = JSON.parse(base);
  const sum = (a: any, k: string) =>
    total(Object.fromEntries(Object.entries(a.variants.kaidan.hits_by_player).map(([u, x]: any) => [u, x[k]])));
  const fired = (a: any) =>
    total(Object.fromEntries(Object.entries(a.variants.kaidan.followup_by_player).map(([u, x]: any) => [u, x.fired])));
  const den = (a: any, kind: string, k = 'all') => a.denominators.pinglamb[kind][k] + a.denominators.yachi[kind][k];
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };
  const k = (h: any) => `${h.session} ${h.file} ${h.round_index0} ${h.player} ${h.lock}`;

  let a = mut({ noMirror: true });
  expect(sum(a, 'mirrored')).toBe(0);
  expect(sum(a, 'all')).toBe(sum(b, 'all') - sum(b, 'mirrored'));

  a = mut({ pastPrefix: true });
  expect(a.denominators.pinglamb.unscored_past_prefix + a.denominators.yachi.unscored_past_prefix).toBe(0);
  expect(den(a, 'TSD')).toBeGreaterThan(den(b, 'TSD'));

  // a mini spin read as full: the TSS control's denominator gains every mini TSS
  a = mut({ includeMini: true });
  expect(den(a, 'TSS')).toBe(den(b, 'TSS') + den(b, 'mini_TSS'));

  // without the must-empty cells, or the roof row, the window is weaker and its hits are the ablation's
  a = mut({ noMustEmpty: true });
  expect(sum(a, 'all')).toBe(total(b.variants.kaidan.controls.ablation.no_must_empty));
  a = mut({ noRoof: true });
  expect(sum(a, 'all')).toBe(total(b.variants.kaidan.controls.ablation.no_roof));
  expect(sum(a, 'all')).toBe(PART_ONLY.below);

  a = mut({ tOverlap: true });
  expect(sum(a, 'all')).toBe(total(b.variants.kaidan.controls.ablation.t_overlap));

  a = mut({ rowAnchorOff1: true });
  expect(sum(a, 'all')).toBe(0);

  // garbage read as EMPTY: exactly the hits with garbage in their window are lost
  a = mut({ garbageEmpty: true });
  expect(a.hits.map(k)).toEqual(b.hits.filter((h: any) => !h.garbage_in_window).map(k));

  a = mut({ openerLt: true });
  expect(den(a, 'TSD', 'in_opener')).toBeLessThan(den(b, 'TSD', 'in_opener'));
  expect(den(a, 'TSD')).toBe(den(b, 'TSD'));

  // the payoff mutants: the hits never move, only the payoffs
  const payoffOnly = (m: Mutants) => {
    const x = mut(m);
    expect(x.hits.map(k), JSON.stringify(m)).toEqual(b.hits.map(k));
    return x;
  };
  a = payoffOnly({ followupUnmirrored: true });
  a.hits.forEach((h: any, i: number) => { if (!h.mirrored) expect(h.followup).toEqual(b.hits[i].followup); });
  expect(a.hits.filter((h: any) => h.mirrored && h.followup.fired).length)
    .toBeLessThan(b.hits.filter((h: any) => h.mirrored && h.followup.fired).length);
  a = payoffOnly({ followupNoRowmap: true });
  expect(a.hits.filter((h: any, i: number) => JSON.stringify(h.followup) !== JSON.stringify(b.hits[i].followup)).length).toBeGreaterThan(0);
  a = payoffOnly({ payoffAnyPiece: true });
  expect(fired(a)).toBeGreaterThan(fired(b));
  expect(a.hits.filter((h: any) => ['well_filled_not_i', 'i_in_well_not_quad'].includes(h.followup.reason)).length).toBe(0);
  a = payoffOnly({ payoffNoQuad: true });
  expect(a.hits.filter((h: any) => h.followup.reason === 'i_in_well_not_quad').length).toBe(0);
  expect(fired(a)).toBe(fired(b) + b.hits.filter((h: any) => h.followup.reason === 'i_in_well_not_quad').length);

  for (const [m] of Object.entries(EQUIVALENT))
    expect(serialise(run({ [m]: true } as Mutants)), m).toBe(base);
}, 900_000);

/** A two-lock digest from a drawing: the spin into `slot` on `pre` (every non-empty cell filled), then `next` (a
 *  piece's cells, in the frame of the board the spin leaves) with `cleared` lines. Mirrored: columns reflected. */
function drawingDigest(pre: string[], slot: number[][], next: { piece: string; cells: number[][]; cleared: number },
                       o: { mirrored?: boolean } = {}): TechDigest {
  const mc = (c: number) => o.mirrored ? W - 1 - c : c;
  const flip = (r: string) => o.mirrored ? [...r].reverse().join('') : r;
  const board = pad(pre.map(flip)), top = H - pre.length;
  const t: Cell[] = slot.map(([r, c]) => ({ row: r! + top, col: mc(c!) }));
  const g = board.map(r => [...r]);
  for (const q of t) { expect(g[q.row]![q.col]).toBe('.'); g[q.row]![q.col] = 'X'; }
  const full = g.flatMap((r, i) => r.every(x => x !== '.') ? [i] : []);
  const nextCells: Cell[] = next.cells.map(([r, c]) => ({ row: r! + top, col: mc(c!) }));
  const lock = (piece: string, spin: string, cells: Cell[], rows: number[], cleared: number) =>
    ({ piece, spin, cleared, cells, clearedRows: rows, garbage: 0, mapOk: true });
  return { session: 'page', file: 'kaidan', round: 0, match: 1, user: 'page', v: 1,
           locks: [lock('T', 'full', t, full, full.length), lock(next.piece, 'none', nextCells, [], next.cleared)],
           tspins: [{ i: 0, board }] };
}

test('the payoff on the page\'s drawing: a three-deep well refuses the Tetris; a constructed four-deep one fires it', () => {
  const pre: string[] = byId.get('basic.o').rows;
  const one = (dg: TechDigest, m: Mutants = {}) => {
    const c = classify(KAIDAN, TR, [dg], m);
    expect(c.hits.length).toBe(1);
    return c.hits[0]!;
  };
  // the page's own well is three deep: an I into it fills three rows, and the payoff is refused
  const i3 = { piece: 'I', cells: [[3, 9], [4, 9], [5, 9], [6, 9]], cleared: 3 };
  for (const mirrored of [false, true]) {
    const h = one(drawingDigest(pre, V.t_cells, i3, { mirrored }));
    expect([h.mirrored, h.well_depth, h.followup.reason]).toEqual([mirrored, 3, 'i_in_well_not_quad']);
  }
  // CONSTRUCTED by us: the same board with its bottom row repeated once, a well four deep (harddrop's Anchor_Set
  // draws a four-deep Tetris on a later board of that line, not on the board this TSD leaves, so it is not this pair)
  const deep = [...pre, pre[pre.length - 1]!];
  const quad = { piece: 'I', cells: [[4, 9], [5, 9], [6, 9], [7, 9]], cleared: 4 };
  for (const mirrored of [false, true]) {
    const h = one(drawingDigest(deep, V.t_cells, quad, { mirrored }));
    expect([h.mirrored, h.well_depth], `${mirrored}`).toEqual([mirrored, 4]);
    expect(h.followup).toEqual({ lock: 1, fired: true, reason: null });
    // an I that does not clear four: refused, and fired by the mutant that accepts any I
    expect(one(drawingDigest(deep, V.t_cells, { ...quad, cleared: 3 }, { mirrored })).followup.reason).toBe('i_in_well_not_quad');
    expect(one(drawingDigest(deep, V.t_cells, { ...quad, cleared: 3 }, { mirrored }), { payoffNoQuad: true }).followup.fired).toBe(true);
    // another piece into the well: refused, and fired by the mutant that accepts any piece
    expect(one(drawingDigest(deep, V.t_cells, { ...quad, piece: 'J' }, { mirrored })).followup.reason).toBe('well_filled_not_i');
    expect(one(drawingDigest(deep, V.t_cells, { ...quad, piece: 'J' }, { mirrored }), { payoffAnyPiece: true }).followup.fired).toBe(true);
    // the well carried in the drawn columns on a mirrored hit: the I is in another column, and nothing else enters it
    expect(one(drawingDigest(deep, V.t_cells, quad, { mirrored }), { followupUnmirrored: true }).followup.fired).toBe(!mirrored);
  }
});

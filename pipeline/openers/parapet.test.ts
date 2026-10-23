/**
 * The 欄干 (Parapet) technique artefact (`analysis/parapet-facts.json`, from `pipeline/sim/emit-technique-facts.ts
 * --technique parapet`; the rules are the shared `technique-facts.ts`, the profile `technique-profile-parapet.ts`, the
 * shape the gated `pipeline/openers/parapet-technique.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count in every session and for every
 *      player, as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN, on the drawings: `windowMatch` (TS) fires, for each variant (the TSD and the TSS), on BT砲's
 *      page's Parapet, on harddrop's fumen board and on Tetrisチャンネル's two Parapet boards — once, at the recorded
 *      slot, as drawn, and at no other T placement; on this page's two basic forms; on BT砲's 途中BT build at the slot
 *      the gate records; on no Tetrisチャンネル plain-TSD board or bare terrain; and, over every routes board, on exactly
 *      the two same-author 山岳積み2号 boards the gate records (the TSD) and none (the TSS).
 *   4. THE OTHER FLAT-T WINDOWS: anchored on the same flat T, this TSD window clashes with STMB Cave's, ダブルダガー's,
 *      千鳥格子's and 社畜トレイン's on a cell in every pairing of hands, and with BT砲's only when the hands differ (the
 *      BT is built from the Parapet terrain, so in the same hand the two windows agree on every cell they share). The
 *      hit sets are disjoint from all five; the BT one is a NAMED list (empty here) rather than an assert, because
 *      nothing in the windows forbids it.
 *   5. WHAT DISCRIMINATES, measured per window part with the T anchored (above the cleared rows, the cleared rows,
 *      below them: the well), per variant.
 *   6. DONATION: `donationCols` re-implemented (`technique-donation-checks.ts`, shared with `kaidan.test.ts`), every session's
 *      per-player `donation.players[].donations` reproduced exactly, and every hit that is not a donation at its well
 *      column named with its re-derived reason (HIT_NOT_DONATION).
 *   7. NAMED lists, not bounds; pinned per-player figures; the STRUCTURAL zeros re-derived from the window; mutants,
 *      each with its asserted symptom (the equivalent ones named, measured, asserted to STAY byte-identical).
 *   8. THE PAYOFF ON INDEPENDENT DRAWINGS: two-lock digests built from Tetrisチャンネル's 4-deep sequence (012, 013's T,
 *      015's I) and harddrop's fumen (pages 8-10), as drawn and mirrored, through `classify` — the payoff fires, and
 *      each payoff mutant breaks it there.
 *   9. QUALIFIES (`parapet-qualify.ts`, at yachi's request on 2026-10-23, 社畜トレイン's rules carried over): which
 *      hits were BUILT from whole pieces. Pinned per player, the qualifying list and the hits failing one rule alone;
 *      the six cells read (the L and the roof) re-derived from the page's builds; the ownership guard throws on a board
 *      it cannot reproduce; and each rule turned off qualifies exactly the hits whose only failures are rules turned off.
 *
 * window_off_board is not listed entry by entry: it is every T of a variant's shape at that variant's spin whose
 * window leaves the board before the matcher found a mismatch, thousands of them. It is pinned per variant and per
 * player as a count, and every entry is checked to be such a T (STMB Cave's treatment, for the same reason).
 *
 * Run: bun test pipeline/openers/parapet.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, classify, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest, type Cell }
  from '../sim/technique-facts.ts';
import { PARAPET } from '../sim/technique-profile-parapet.ts';
import { STMBCAVE } from '../sim/technique-profile-stmbcave.ts';
import { DOUBLEDAGGER } from '../sim/technique-profile-doubledagger.ts';
import { BTCANNON } from '../sim/technique-profile-btcannon.ts';
import { CUTCOPY } from '../sim/technique-profile-cutcopy.ts';
import { SHACHIKUTRAIN } from '../sim/technique-profile-shachikutrain.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';
import { H, W, scored, donationVerdict } from './technique-donation-checks.ts';
import { parapetQualifier, shapeOffsets as qualifyShape, type ParapetQualifyMutants } from '../sim/parapet-qualify.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22']);
const ART_PATH = `${import.meta.dir}/../../analysis/parapet-facts.json`;
const TR = JSON.parse(readFileSync(PARAPET.transcriptionPath, 'utf8'));
const TSD = TR.variants.find((v: any) => v.id === 'parapet');
const TSS = TR.variants.find((v: any) => v.id === 'parapet_tss');

const PARAPET_HITS: string[] = [
  "2026-07-22 m3r6 yachi lock 29", "2026-07-22 m3r7 pinglamb lock 86 (mirrored)",
  "2026-07-22 m5r1 pinglamb lock 18 (mirrored)", "2026-07-22 m5r7 yachi lock 24 (mirrored)",
  "2026-07-22 m6r4 pinglamb lock 58 (mirrored)", "2026-07-22 m7r6 pinglamb lock 22",
  "2026-07-22 m9r5 pinglamb lock 171", "2026-07-22 m10r4 pinglamb lock 26",
  "2026-07-22 m10r5 yachi lock 92 (mirrored)", "2026-07-22 m10r7 yachi lock 88 (mirrored)",
  "2026-07-24 m1r1 pinglamb lock 18", "2026-07-24 m2r2 pinglamb lock 14",
  "2026-07-24 m3r2 pinglamb lock 79 (mirrored)", "2026-07-24 m6r7 yachi lock 37 (mirrored)",
  "2026-07-24 m7r3 pinglamb lock 118 (mirrored)", "2026-07-24 m7r7 pinglamb lock 39 (mirrored)",
  "2026-07-28 m4r2 yachi lock 166", "2026-07-28 m6r5 yachi lock 40", "2026-07-28 m7r4 yachi lock 38",
  "2026-07-28 m7r9 pinglamb lock 47", "2026-08-01 m1r7 yachi lock 26", "2026-08-01 m2r1 pinglamb lock 14",
  "2026-08-01 m3r3 pinglamb lock 17 (mirrored)", "2026-08-01 m3r3 yachi lock 86",
  "2026-08-01 m5r2 yachi lock 18 (mirrored)", "2026-08-01 m5r2 yachi lock 88",
  "2026-08-01 m7r1 pinglamb lock 82 (mirrored)", "2026-08-01 m7r5 yachi lock 32 (mirrored)",
  "2026-08-09 m1r8 pinglamb lock 57", "2026-08-09 m4r2 pinglamb lock 29",
  "2026-08-09 m5r7 pinglamb lock 27 (mirrored)", "2026-08-09 m5r8 pinglamb lock 122",
  "2026-08-09 m6r2 pinglamb lock 38 (mirrored)", "2026-08-14 m2r4 pinglamb lock 19 (mirrored)",
  "2026-08-14 m3r4 pinglamb lock 39 (mirrored)", "2026-08-14 m4r1 pinglamb lock 45 (mirrored)",
  "2026-08-14 m5r2 pinglamb lock 56", "2026-08-14 m6r3 pinglamb lock 27", "2026-08-14 m7r2 pinglamb lock 17",
  "2026-08-14 m9r3 pinglamb lock 103", "2026-08-14 m10r8 yachi lock 19 (mirrored)", "2026-08-14 m11r2 yachi lock 41",
  "2026-08-14 m11r2 yachi lock 90 (mirrored)", "2026-08-14 m11r7 pinglamb lock 32",
  "2026-08-19 m3r3 pinglamb lock 23", "2026-08-19 m4r7 yachi lock 135", "2026-08-19 m4r8 pinglamb lock 104",
  "2026-08-19 m5r5 yachi lock 39", "2026-08-19 m5r7 pinglamb lock 46", "2026-08-19 m6r6 pinglamb lock 33",
  "2026-08-19 m8r4 pinglamb lock 14", "2026-08-19 m9r9 pinglamb lock 19",
  "2026-08-19 m9r9 pinglamb lock 149 (mirrored)", "2026-08-25 m1r2 yachi lock 68",
  "2026-08-25 m1r7 pinglamb lock 31 (mirrored)", "2026-08-25 m1r7 pinglamb lock 48", "2026-08-25 m1r8 yachi lock 19",
  "2026-08-25 m1r9 pinglamb lock 70 (mirrored)", "2026-08-25 m2r1 yachi lock 60 (mirrored)",
  "2026-08-25 m4r4 yachi lock 45 (mirrored)", "2026-08-25 m6r1 pinglamb lock 110",
  "2026-08-25 m6r1 pinglamb lock 136", "2026-08-25 m6r5 yachi lock 14 (mirrored)", "2026-08-25 m8r6 yachi lock 156",
  "2026-08-25 m8r6 yachi lock 218", "2026-08-25 m9r7 pinglamb lock 84 (mirrored)",
  "2026-09-03 m2r4 pinglamb lock 26 (mirrored)", "2026-09-03 m2r8 pinglamb lock 17", "2026-09-03 m2r8 yachi lock 30",
  "2026-09-03 m3r7 pinglamb lock 18", "2026-09-03 m6r6 pinglamb lock 129 (mirrored)",
  "2026-09-03 m6r6 pinglamb lock 216 (mirrored)", "2026-09-10 m2r3 pinglamb lock 34",
  "2026-09-10 m2r3 pinglamb lock 39", "2026-09-10 m2r7 yachi lock 15", "2026-09-10 m4r6 yachi lock 17",
  "2026-09-11 m2r5 pinglamb lock 134", "2026-09-11 m2r6 pinglamb lock 16",
  "2026-09-11 m3r4 yachi lock 19 (mirrored)", "2026-09-11 m3r5 pinglamb lock 87",
  "2026-09-11 m3r7 pinglamb lock 19 (mirrored)", "2026-09-11 m6r6 yachi lock 124",
  "2026-09-11 m7r5 pinglamb lock 88", "2026-09-11 m7r8 yachi lock 61 (mirrored)",
  "2026-09-17 m1r1 pinglamb lock 19 (mirrored)", "2026-09-17 m1r8 pinglamb lock 18",
  "2026-09-17 m2r7 pinglamb lock 15 (mirrored)", "2026-09-17 m6r2 yachi lock 125 (mirrored)",
  "2026-09-17 m7r4 pinglamb lock 14 (mirrored)", "2026-09-18 m1r5 pinglamb lock 26",
  "2026-09-18 m2r1 yachi lock 22 (mirrored)", "2026-09-18 m2r2 pinglamb lock 65 (mirrored)",
  "2026-09-18 m3r3 yachi lock 29", "2026-09-18 m4r2 pinglamb lock 19 (mirrored)",
  "2026-09-18 m11r5 pinglamb lock 17", "2026-09-18 m11r6 yachi lock 185", "2026-09-18 m12r1 pinglamb lock 15",
  "2026-09-18 m12r3 yachi lock 45", "2026-09-18 m12r4 pinglamb lock 85", "2026-09-18 m13r1 pinglamb lock 86",
  "2026-09-18 m17r3 yachi lock 18 (mirrored)", "2026-09-18 m17r8 yachi lock 45 (mirrored)",
  "2026-09-19 m4r1 pinglamb lock 56", "2026-09-19 m9r1 pinglamb lock 17", "2026-09-19 m9r5 yachi lock 74",
  "2026-09-19 m11r5 yachi lock 26 (mirrored)", "2026-09-19 m12r6 pinglamb lock 17", "2026-09-19 m12r6 yachi lock 15",
  "2026-09-19 m13r3 pinglamb lock 63", "2026-09-19 m13r3 yachi lock 276", "2026-09-19 m15r1 pinglamb lock 31",
  "2026-09-19 m15r8 yachi lock 39 (mirrored)", "2026-09-19 m16r7 pinglamb lock 30",
  "2026-09-19 m17r6 pinglamb lock 17", "2026-09-19 m18r2 pinglamb lock 120 (mirrored)",
  "2026-09-19 m18r5 pinglamb lock 35", "2026-09-19 m19r7 pinglamb lock 27",
  "2026-09-19 m20r6 pinglamb lock 19 (mirrored)", "2026-10-03 m1r5 pinglamb lock 18",
  "2026-10-03 m2r6 yachi lock 32 (mirrored)", "2026-10-03 m3r4 pinglamb lock 24 (mirrored)",
  "2026-10-03 m3r4 yachi lock 19 (mirrored)", "2026-10-03 m3r5 pinglamb lock 19 (mirrored)",
  "2026-10-03 m4r2 pinglamb lock 71 (mirrored)", "2026-10-03 m4r2 yachi lock 32",
  "2026-10-03 m6r1 pinglamb lock 14 (mirrored)", "2026-10-03 m9r6 pinglamb lock 15",
  "2026-10-03 m10r6 pinglamb lock 45", "2026-10-03 m11r2 yachi lock 128", "2026-10-03 m11r4 pinglamb lock 152",
  "2026-10-03 m12r2 pinglamb lock 14", "2026-10-03 m15r1 yachi lock 33", "2026-10-03 m17r3 yachi lock 73 (mirrored)",
  "2026-10-03 m18r3 pinglamb lock 58", "2026-10-03 m20r2 pinglamb lock 216", "2026-10-03 m20r8 pinglamb lock 129",
  "2026-10-09 m2r5 pinglamb lock 16 (mirrored)", "2026-10-09 m2r6 pinglamb lock 14",
  "2026-10-09 m3r5 pinglamb lock 16", "2026-10-09 m5r2 pinglamb lock 68 (mirrored)",
  "2026-10-09 m5r3 pinglamb lock 31", "2026-10-09 m8r6 yachi lock 37 (mirrored)", "2026-10-09 m8r7 pinglamb lock 63",
  "2026-10-09 m8r9 pinglamb lock 112", "2026-10-09 m8r9 yachi lock 127",
  "2026-10-09 m9r1 pinglamb lock 112 (mirrored)", "2026-10-09 m9r7 yachi lock 72 (mirrored)",
  "2026-10-09 m9r9 pinglamb lock 34 (mirrored)", "2026-10-09 m10r6 pinglamb lock 17",
  "2026-10-09 m11r2 yachi lock 192 (mirrored)", "2026-10-09 m12r3 pinglamb lock 101 (mirrored)",
  "2026-10-12 m4r6 pinglamb lock 101", "2026-10-12 m6r7 pinglamb lock 18", "2026-10-12 m6r7 yachi lock 18",
  "2026-10-12 m6r8 pinglamb lock 69 (mirrored)", "2026-10-12 m8r2 yachi lock 144 (mirrored)",
  "2026-10-12 m8r7 pinglamb lock 139", "2026-10-12 m8r7 yachi lock 64", "2026-10-20 m2r4 yachi lock 50",
  "2026-10-20 m3r2 pinglamb lock 24", "2026-10-20 m4r7 pinglamb lock 76 (mirrored)", "2026-10-20 m4r7 pinglamb lock 86",
  "2026-10-20 m4r7 yachi lock 92 (mirrored)",
  "2026-10-22 m1r8 pinglamb lock 44", "2026-10-22 m2r4 pinglamb lock 19", "2026-10-22 m3r3 pinglamb lock 17 (mirrored)", "2026-10-22 m4r5 pinglamb lock 36", "2026-10-22 m6r7 pinglamb lock 27 (mirrored)", "2026-10-22 m7r1 yachi lock 17 (mirrored)", "2026-10-22 m8r1 yachi lock 54", "2026-10-22 m8r7 pinglamb lock 27 (mirrored)", "2026-10-22 m9r5 yachi lock 53 (mirrored)",
];
const PARAPET_TSS_HITS: string[] = [
  "2026-07-22 m3r3 yachi lock 38 (mirrored)", "2026-07-22 m3r4 yachi lock 84", "2026-07-22 m5r5 yachi lock 39",
  "2026-07-22 m10r1 yachi lock 116 (mirrored)", "2026-07-24 m1r1 yachi lock 18",
  "2026-07-24 m2r3 pinglamb lock 86 (mirrored)", "2026-07-24 m4r5 yachi lock 16 (mirrored)",
  "2026-07-24 m5r1 yachi lock 54", "2026-07-28 m1r6 yachi lock 61 (mirrored)", "2026-07-28 m3r5 yachi lock 33",
  "2026-07-28 m6r5 yachi lock 185 (mirrored)", "2026-08-01 m2r2 yachi lock 90 (mirrored)",
  "2026-08-01 m6r1 pinglamb lock 43", "2026-08-01 m7r2 yachi lock 33", "2026-08-09 m1r2 yachi lock 19 (mirrored)",
  "2026-08-09 m3r3 yachi lock 110 (mirrored)", "2026-08-09 m3r6 yachi lock 41 (mirrored)",
  "2026-08-09 m3r8 yachi lock 125 (mirrored)", "2026-08-14 m4r6 yachi lock 207 (mirrored)",
  "2026-08-14 m5r2 yachi lock 81", "2026-08-14 m6r8 pinglamb lock 27 (mirrored)",
  "2026-08-14 m7r3 yachi lock 18 (mirrored)", "2026-08-14 m8r2 yachi lock 46 (mirrored)",
  "2026-08-14 m9r1 yachi lock 54 (mirrored)", "2026-08-14 m11r5 yachi lock 144 (mirrored)",
  "2026-08-19 m5r3 yachi lock 39", "2026-08-19 m6r3 yachi lock 14", "2026-08-19 m9r9 yachi lock 19",
  "2026-08-19 m9r9 yachi lock 41", "2026-08-19 m10r6 pinglamb lock 17", "2026-08-19 m10r8 yachi lock 26 (mirrored)",
  "2026-08-25 m2r1 yachi lock 53 (mirrored)", "2026-08-25 m5r2 yachi lock 73",
  "2026-08-25 m5r8 yachi lock 90 (mirrored)", "2026-08-25 m8r7 pinglamb lock 17", "2026-08-25 m8r7 yachi lock 23",
  "2026-09-03 m1r6 yachi lock 106", "2026-09-03 m4r6 yachi lock 98 (mirrored)",
  "2026-09-03 m5r1 yachi lock 18 (mirrored)", "2026-09-10 m1r5 yachi lock 166 (mirrored)",
  "2026-09-10 m4r1 yachi lock 20 (mirrored)", "2026-09-10 m5r8 pinglamb lock 17", "2026-09-10 m5r8 yachi lock 18",
  "2026-09-11 m1r3 yachi lock 24 (mirrored)", "2026-09-11 m5r2 yachi lock 32 (mirrored)",
  "2026-09-17 m2r7 yachi lock 23", "2026-09-18 m3r7 yachi lock 25", "2026-09-18 m6r4 yachi lock 16 (mirrored)",
  "2026-09-18 m6r6 yachi lock 44", "2026-09-18 m11r4 yachi lock 50", "2026-09-18 m14r5 yachi lock 111",
  "2026-09-18 m15r6 yachi lock 27 (mirrored)", "2026-09-19 m1r5 yachi lock 19", "2026-09-19 m1r6 yachi lock 45",
  "2026-09-19 m5r3 yachi lock 15 (mirrored)", "2026-09-19 m7r4 pinglamb lock 16", "2026-09-19 m9r3 pinglamb lock 19",
  "2026-09-19 m13r6 yachi lock 18", "2026-09-19 m18r2 yachi lock 6 (mirrored)",
  "2026-09-19 m20r6 yachi lock 19 (mirrored)", "2026-10-03 m5r4 yachi lock 75", "2026-10-03 m6r2 yachi lock 137",
  "2026-10-03 m7r5 yachi lock 17 (mirrored)", "2026-10-03 m9r4 pinglamb lock 59 (mirrored)",
  "2026-10-03 m12r6 yachi lock 109 (mirrored)", "2026-10-03 m15r2 yachi lock 64",
  "2026-10-03 m15r5 pinglamb lock 16 (mirrored)", "2026-10-03 m15r7 pinglamb lock 219",
  "2026-10-03 m17r6 yachi lock 105 (mirrored)", "2026-10-03 m20r7 yachi lock 192 (mirrored)",
  "2026-10-03 m20r8 yachi lock 106", "2026-10-09 m3r8 pinglamb lock 17", "2026-10-09 m5r8 yachi lock 66 (mirrored)",
  "2026-10-09 m5r8 yachi lock 75 (mirrored)", "2026-10-09 m7r7 yachi lock 42", "2026-10-09 m8r7 yachi lock 73",
  "2026-10-09 m8r9 yachi lock 81 (mirrored)", "2026-10-09 m12r5 yachi lock 15", "2026-10-12 m7r3 pinglamb lock 17",
  "2026-10-20 m1r1 yachi lock 121", "2026-10-20 m2r1 pinglamb lock 129",
  "2026-10-22 m2r4 yachi lock 17", "2026-10-22 m2r4 yachi lock 75 (mirrored)", "2026-10-22 m6r4 yachi lock 17", "2026-10-22 m7r6 yachi lock 67 (mirrored)", "2026-10-22 m8r4 pinglamb lock 48", "2026-10-22 m9r5 yachi lock 19",
];
const PAYOFF_NOT_FIRED: string[] = [
  "2026-07-22 m5r1 pinglamb lock 18 (parapet: well_covered at lock 23)",
  "2026-07-22 m9r5 pinglamb lock 171 (parapet: well_covered at lock 174)",
  "2026-07-22 m10r4 pinglamb lock 26 (parapet: well_covered at lock 27)",
  "2026-07-22 m10r5 yachi lock 92 (parapet: well_covered at lock 95)",
  "2026-07-24 m2r2 pinglamb lock 14 (parapet: well_covered at lock 21)",
  "2026-07-24 m3r2 pinglamb lock 79 (parapet: i_in_well_not_quad at lock 81)",
  "2026-07-24 m5r1 yachi lock 54 (parapet_tss: well_covered at lock 59)",
  "2026-07-24 m7r7 pinglamb lock 39 (parapet: well_filled_not_i at lock 47)",
  "2026-07-28 m6r5 yachi lock 40 (parapet: well_filled_not_i at lock 41)",
  "2026-07-28 m6r5 yachi lock 185 (parapet_tss: i_in_well_not_quad at lock 186)",
  "2026-07-28 m7r4 yachi lock 38 (parapet: well_filled_not_i at lock 42)",
  "2026-07-28 m7r9 pinglamb lock 47 (parapet: well_covered at lock 50)",
  "2026-08-01 m3r3 yachi lock 86 (parapet: well_filled_not_i at lock 87)",
  "2026-08-01 m5r2 yachi lock 18 (parapet: well_filled_not_i at lock 19)",
  "2026-08-01 m5r2 yachi lock 88 (parapet: well_covered at lock 89)",
  "2026-08-01 m7r1 pinglamb lock 82 (parapet: well_filled_not_i at lock 83)",
  "2026-08-01 m7r2 yachi lock 33 (parapet_tss: well_covered at lock 34)",
  "2026-08-09 m3r3 yachi lock 110 (parapet_tss: well_covered at lock 117)",
  "2026-08-09 m5r7 pinglamb lock 27 (parapet: well_covered at lock 28)",
  "2026-08-09 m6r2 pinglamb lock 38 (parapet: well_filled_not_i at lock 41)",
  "2026-08-14 m2r4 pinglamb lock 19 (parapet: well_covered at lock 20)",
  "2026-08-14 m3r4 pinglamb lock 39 (parapet: well_covered at lock 44)",
  "2026-08-14 m7r2 pinglamb lock 17 (parapet: well_filled_not_i at lock 22)",
  "2026-08-14 m9r3 pinglamb lock 103 (parapet: well_filled_not_i at lock 104)",
  "2026-08-19 m4r7 yachi lock 135 (parapet: well_filled_not_i at lock 137)",
  "2026-08-19 m4r8 pinglamb lock 104 (parapet: well_filled_not_i at lock 105)",
  "2026-08-19 m5r3 yachi lock 39 (parapet_tss: round_ended)",
  "2026-08-19 m5r5 yachi lock 39 (parapet: well_filled_not_i at lock 40)",
  "2026-08-19 m5r7 pinglamb lock 46 (parapet: round_ended)",
  "2026-08-19 m9r9 pinglamb lock 149 (parapet: well_filled_not_i at lock 150)",
  "2026-08-19 m9r9 yachi lock 41 (parapet_tss: well_covered at lock 42)",
  "2026-08-19 m10r8 yachi lock 26 (parapet_tss: well_covered at lock 27)",
  "2026-08-25 m1r2 yachi lock 68 (parapet: past_verified at lock 70)",
  "2026-08-25 m1r7 pinglamb lock 31 (parapet: well_covered at lock 32)",
  "2026-08-25 m1r7 pinglamb lock 48 (parapet: well_filled_not_i at lock 50)",
  "2026-08-25 m1r8 yachi lock 19 (parapet: well_covered at lock 20)",
  "2026-08-25 m1r9 pinglamb lock 70 (parapet: well_filled_not_i at lock 76)",
  "2026-08-25 m2r1 yachi lock 53 (parapet_tss: well_covered at lock 54)",
  "2026-08-25 m5r2 yachi lock 73 (parapet_tss: well_covered at lock 81)",
  "2026-08-25 m6r1 pinglamb lock 110 (parapet: well_filled_not_i at lock 111)",
  "2026-08-25 m6r5 yachi lock 14 (parapet: well_filled_not_i at lock 16)",
  "2026-08-25 m8r6 yachi lock 156 (parapet: well_covered at lock 159)",
  "2026-08-25 m9r7 pinglamb lock 84 (parapet: well_covered at lock 94)",
  "2026-09-03 m1r6 yachi lock 106 (parapet_tss: well_covered at lock 108)",
  "2026-09-03 m2r4 pinglamb lock 26 (parapet: well_covered at lock 27)",
  "2026-09-03 m2r8 pinglamb lock 17 (parapet: well_filled_not_i at lock 18)",
  "2026-09-03 m2r8 yachi lock 30 (parapet: round_ended)",
  "2026-09-03 m5r1 yachi lock 18 (parapet_tss: well_covered at lock 19)",
  "2026-09-03 m6r6 pinglamb lock 129 (parapet: i_in_well_not_quad at lock 131)",
  "2026-09-03 m6r6 pinglamb lock 216 (parapet: well_filled_not_i at lock 217)",
  "2026-09-10 m2r3 pinglamb lock 34 (parapet: well_filled_not_i at lock 35)",
  "2026-09-10 m2r3 pinglamb lock 39 (parapet: well_filled_not_i at lock 41)",
  "2026-09-10 m2r7 yachi lock 15 (parapet: well_filled_not_i at lock 17)",
  "2026-09-10 m4r6 yachi lock 17 (parapet: well_filled_not_i at lock 19)",
  "2026-09-11 m2r5 pinglamb lock 134 (parapet: well_filled_not_i at lock 135)",
  "2026-09-11 m2r6 pinglamb lock 16 (parapet: well_covered at lock 23)",
  "2026-09-11 m3r4 yachi lock 19 (parapet: well_covered at lock 20)",
  "2026-09-11 m3r7 pinglamb lock 19 (parapet: well_covered at lock 22)",
  "2026-09-11 m5r2 yachi lock 32 (parapet_tss: well_covered at lock 38)",
  "2026-09-11 m7r5 pinglamb lock 88 (parapet: past_verified at lock 89)",
  "2026-09-11 m7r8 yachi lock 61 (parapet: well_covered at lock 65)",
  "2026-09-17 m2r7 pinglamb lock 15 (parapet: well_covered at lock 25)",
  "2026-09-17 m6r2 yachi lock 125 (parapet: well_filled_not_i at lock 128)",
  "2026-09-18 m2r2 pinglamb lock 65 (parapet: i_in_well_not_quad at lock 66)",
  "2026-09-18 m3r3 yachi lock 29 (parapet: well_filled_not_i at lock 30)",
  "2026-09-18 m12r3 yachi lock 45 (parapet: well_covered at lock 46)",
  "2026-09-18 m12r4 pinglamb lock 85 (parapet: well_filled_not_i at lock 86)",
  "2026-09-18 m13r1 pinglamb lock 86 (parapet: well_filled_not_i at lock 87)",
  "2026-09-18 m14r5 yachi lock 111 (parapet_tss: well_covered at lock 119)",
  "2026-09-18 m17r3 yachi lock 18 (parapet: well_covered at lock 25)",
  "2026-09-18 m17r8 yachi lock 45 (parapet: past_verified at lock 46)",
  "2026-09-19 m9r1 pinglamb lock 17 (parapet: well_filled_not_i at lock 18)",
  "2026-09-19 m13r3 pinglamb lock 63 (parapet: well_covered at lock 64)",
  "2026-09-19 m13r3 yachi lock 276 (parapet: well_covered at lock 286)",
  "2026-09-19 m15r8 yachi lock 39 (parapet: well_filled_not_i at lock 41)",
  "2026-09-19 m18r2 pinglamb lock 120 (parapet: well_filled_not_i at lock 125)",
  "2026-09-19 m19r7 pinglamb lock 27 (parapet: well_filled_not_i at lock 28)",
  "2026-10-03 m3r4 yachi lock 19 (parapet: well_filled_not_i at lock 20)",
  "2026-10-03 m3r5 pinglamb lock 19 (parapet: well_covered at lock 23)",
  "2026-10-03 m4r2 pinglamb lock 71 (parapet: well_filled_not_i at lock 72)",
  "2026-10-03 m4r2 yachi lock 32 (parapet: well_filled_not_i at lock 37)",
  "2026-10-03 m5r4 yachi lock 75 (parapet_tss: well_covered at lock 77)",
  "2026-10-03 m9r6 pinglamb lock 15 (parapet: well_covered at lock 18)",
  "2026-10-03 m10r6 pinglamb lock 45 (parapet: well_covered at lock 46)",
  "2026-10-03 m12r6 yachi lock 109 (parapet_tss: well_covered at lock 112)",
  "2026-10-03 m15r5 pinglamb lock 16 (parapet_tss: well_covered at lock 25)",
  "2026-10-03 m15r7 pinglamb lock 219 (parapet_tss: well_covered at lock 223)",
  "2026-10-03 m17r3 yachi lock 73 (parapet: well_filled_not_i at lock 76)",
  "2026-10-03 m20r8 pinglamb lock 129 (parapet: well_filled_not_i at lock 130)",
  "2026-10-09 m3r8 pinglamb lock 17 (parapet_tss: well_covered at lock 26)",
  "2026-10-09 m5r3 pinglamb lock 31 (parapet: well_covered at lock 33)",
  "2026-10-09 m7r7 yachi lock 42 (parapet_tss: i_in_well_not_quad at lock 44)",
  "2026-10-09 m8r7 yachi lock 73 (parapet_tss: well_covered at lock 74)",
  "2026-10-09 m8r9 yachi lock 127 (parapet: well_filled_not_i at lock 128)",
  "2026-10-09 m9r9 pinglamb lock 34 (parapet: well_filled_not_i at lock 35)",
  "2026-10-09 m11r2 yachi lock 192 (parapet: well_filled_not_i at lock 194)",
  "2026-10-12 m8r2 yachi lock 144 (parapet: well_filled_not_i at lock 146)",
  "2026-10-12 m8r7 pinglamb lock 139 (parapet: well_filled_not_i at lock 140)",
  "2026-10-12 m8r7 yachi lock 64 (parapet: well_filled_not_i at lock 65)",
  "2026-10-20 m3r2 pinglamb lock 24 (parapet: well_covered at lock 29)",
  "2026-10-20 m4r7 yachi lock 92 (parapet: well_filled_not_i at lock 93)",
  "2026-10-22 m7r1 yachi lock 17 (parapet: i_in_well_not_quad at lock 20)", "2026-10-22 m8r1 yachi lock 54 (parapet: well_filled_not_i at lock 56)", "2026-10-22 m8r4 pinglamb lock 48 (parapet_tss: well_covered at lock 50)",
];
const GARBAGE_IN_WINDOW: string[] = [
  "2026-07-22 m3r3 yachi lock 38 (parapet_tss)", "2026-07-22 m3r4 yachi lock 84 (parapet_tss)",
  "2026-07-22 m3r6 yachi lock 29 (parapet)", "2026-07-22 m3r7 pinglamb lock 86 (parapet)",
  "2026-07-22 m5r1 pinglamb lock 18 (parapet)", "2026-07-22 m5r7 yachi lock 24 (parapet)",
  "2026-07-22 m6r4 pinglamb lock 58 (parapet)", "2026-07-22 m7r6 pinglamb lock 22 (parapet)",
  "2026-07-22 m9r5 pinglamb lock 171 (parapet)", "2026-07-22 m10r1 yachi lock 116 (parapet_tss)",
  "2026-07-22 m10r4 pinglamb lock 26 (parapet)", "2026-07-22 m10r5 yachi lock 92 (parapet)",
  "2026-07-24 m1r1 pinglamb lock 18 (parapet)", "2026-07-24 m1r1 yachi lock 18 (parapet_tss)",
  "2026-07-24 m2r2 pinglamb lock 14 (parapet)", "2026-07-24 m2r3 pinglamb lock 86 (parapet_tss)",
  "2026-07-24 m3r2 pinglamb lock 79 (parapet)", "2026-07-24 m4r5 yachi lock 16 (parapet_tss)",
  "2026-07-24 m5r1 yachi lock 54 (parapet_tss)", "2026-07-24 m6r7 yachi lock 37 (parapet)",
  "2026-07-24 m7r3 pinglamb lock 118 (parapet)", "2026-07-24 m7r7 pinglamb lock 39 (parapet)",
  "2026-07-28 m1r6 yachi lock 61 (parapet_tss)", "2026-07-28 m3r5 yachi lock 33 (parapet_tss)",
  "2026-07-28 m4r2 yachi lock 166 (parapet)", "2026-07-28 m6r5 yachi lock 40 (parapet)",
  "2026-07-28 m6r5 yachi lock 185 (parapet_tss)", "2026-07-28 m7r4 yachi lock 38 (parapet)",
  "2026-07-28 m7r9 pinglamb lock 47 (parapet)", "2026-08-01 m1r7 yachi lock 26 (parapet)",
  "2026-08-01 m2r1 pinglamb lock 14 (parapet)", "2026-08-01 m2r2 yachi lock 90 (parapet_tss)",
  "2026-08-01 m3r3 pinglamb lock 17 (parapet)", "2026-08-01 m5r2 yachi lock 18 (parapet)",
  "2026-08-01 m5r2 yachi lock 88 (parapet)", "2026-08-01 m6r1 pinglamb lock 43 (parapet_tss)",
  "2026-08-01 m7r1 pinglamb lock 82 (parapet)", "2026-08-01 m7r2 yachi lock 33 (parapet_tss)",
  "2026-08-01 m7r5 yachi lock 32 (parapet)", "2026-08-09 m1r2 yachi lock 19 (parapet_tss)",
  "2026-08-09 m1r8 pinglamb lock 57 (parapet)", "2026-08-09 m3r3 yachi lock 110 (parapet_tss)",
  "2026-08-09 m3r6 yachi lock 41 (parapet_tss)", "2026-08-09 m3r8 yachi lock 125 (parapet_tss)",
  "2026-08-09 m4r2 pinglamb lock 29 (parapet)", "2026-08-09 m5r7 pinglamb lock 27 (parapet)",
  "2026-08-09 m5r8 pinglamb lock 122 (parapet)", "2026-08-09 m6r2 pinglamb lock 38 (parapet)",
  "2026-08-14 m2r4 pinglamb lock 19 (parapet)", "2026-08-14 m3r4 pinglamb lock 39 (parapet)",
  "2026-08-14 m4r6 yachi lock 207 (parapet_tss)", "2026-08-14 m5r2 pinglamb lock 56 (parapet)",
  "2026-08-14 m5r2 yachi lock 81 (parapet_tss)", "2026-08-14 m6r8 pinglamb lock 27 (parapet_tss)",
  "2026-08-14 m7r2 pinglamb lock 17 (parapet)", "2026-08-14 m7r3 yachi lock 18 (parapet_tss)",
  "2026-08-14 m8r2 yachi lock 46 (parapet_tss)", "2026-08-14 m9r1 yachi lock 54 (parapet_tss)",
  "2026-08-14 m9r3 pinglamb lock 103 (parapet)", "2026-08-14 m10r8 yachi lock 19 (parapet)",
  "2026-08-14 m11r2 yachi lock 41 (parapet)", "2026-08-14 m11r2 yachi lock 90 (parapet)",
  "2026-08-14 m11r5 yachi lock 144 (parapet_tss)", "2026-08-14 m11r7 pinglamb lock 32 (parapet)",
  "2026-08-19 m3r3 pinglamb lock 23 (parapet)", "2026-08-19 m4r7 yachi lock 135 (parapet)",
  "2026-08-19 m4r8 pinglamb lock 104 (parapet)", "2026-08-19 m5r3 yachi lock 39 (parapet_tss)",
  "2026-08-19 m5r5 yachi lock 39 (parapet)", "2026-08-19 m6r3 yachi lock 14 (parapet_tss)",
  "2026-08-19 m6r6 pinglamb lock 33 (parapet)", "2026-08-19 m8r4 pinglamb lock 14 (parapet)",
  "2026-08-19 m9r9 pinglamb lock 19 (parapet)", "2026-08-19 m9r9 pinglamb lock 149 (parapet)",
  "2026-08-19 m9r9 yachi lock 19 (parapet_tss)", "2026-08-19 m9r9 yachi lock 41 (parapet_tss)",
  "2026-08-19 m10r6 pinglamb lock 17 (parapet_tss)", "2026-08-19 m10r8 yachi lock 26 (parapet_tss)",
  "2026-08-25 m1r2 yachi lock 68 (parapet)", "2026-08-25 m1r7 pinglamb lock 31 (parapet)",
  "2026-08-25 m1r7 pinglamb lock 48 (parapet)", "2026-08-25 m1r8 yachi lock 19 (parapet)",
  "2026-08-25 m1r9 pinglamb lock 70 (parapet)", "2026-08-25 m2r1 yachi lock 53 (parapet_tss)",
  "2026-08-25 m2r1 yachi lock 60 (parapet)", "2026-08-25 m4r4 yachi lock 45 (parapet)",
  "2026-08-25 m5r2 yachi lock 73 (parapet_tss)", "2026-08-25 m5r8 yachi lock 90 (parapet_tss)",
  "2026-08-25 m6r1 pinglamb lock 110 (parapet)", "2026-08-25 m6r1 pinglamb lock 136 (parapet)",
  "2026-08-25 m6r5 yachi lock 14 (parapet)", "2026-08-25 m8r6 yachi lock 156 (parapet)",
  "2026-08-25 m8r7 pinglamb lock 17 (parapet_tss)", "2026-08-25 m8r7 yachi lock 23 (parapet_tss)",
  "2026-08-25 m9r7 pinglamb lock 84 (parapet)", "2026-09-03 m1r6 yachi lock 106 (parapet_tss)",
  "2026-09-03 m2r8 pinglamb lock 17 (parapet)", "2026-09-03 m2r8 yachi lock 30 (parapet)",
  "2026-09-03 m3r7 pinglamb lock 18 (parapet)", "2026-09-03 m4r6 yachi lock 98 (parapet_tss)",
  "2026-09-03 m5r1 yachi lock 18 (parapet_tss)", "2026-09-03 m6r6 pinglamb lock 129 (parapet)",
  "2026-09-03 m6r6 pinglamb lock 216 (parapet)", "2026-09-10 m1r5 yachi lock 166 (parapet_tss)",
  "2026-09-10 m2r3 pinglamb lock 34 (parapet)", "2026-09-10 m2r3 pinglamb lock 39 (parapet)",
  "2026-09-10 m2r7 yachi lock 15 (parapet)", "2026-09-10 m4r1 yachi lock 20 (parapet_tss)",
  "2026-09-10 m4r6 yachi lock 17 (parapet)", "2026-09-10 m5r8 pinglamb lock 17 (parapet_tss)",
  "2026-09-10 m5r8 yachi lock 18 (parapet_tss)", "2026-09-11 m1r3 yachi lock 24 (parapet_tss)",
  "2026-09-11 m2r5 pinglamb lock 134 (parapet)", "2026-09-11 m2r6 pinglamb lock 16 (parapet)",
  "2026-09-11 m3r4 yachi lock 19 (parapet)", "2026-09-11 m3r5 pinglamb lock 87 (parapet)",
  "2026-09-11 m3r7 pinglamb lock 19 (parapet)", "2026-09-11 m5r2 yachi lock 32 (parapet_tss)",
  "2026-09-11 m6r6 yachi lock 124 (parapet)", "2026-09-11 m7r5 pinglamb lock 88 (parapet)",
  "2026-09-11 m7r8 yachi lock 61 (parapet)", "2026-09-17 m1r1 pinglamb lock 19 (parapet)",
  "2026-09-17 m1r8 pinglamb lock 18 (parapet)", "2026-09-17 m2r7 pinglamb lock 15 (parapet)",
  "2026-09-17 m2r7 yachi lock 23 (parapet_tss)", "2026-09-17 m6r2 yachi lock 125 (parapet)",
  "2026-09-17 m7r4 pinglamb lock 14 (parapet)", "2026-09-18 m1r5 pinglamb lock 26 (parapet)",
  "2026-09-18 m2r1 yachi lock 22 (parapet)", "2026-09-18 m2r2 pinglamb lock 65 (parapet)",
  "2026-09-18 m3r3 yachi lock 29 (parapet)", "2026-09-18 m3r7 yachi lock 25 (parapet_tss)",
  "2026-09-18 m4r2 pinglamb lock 19 (parapet)", "2026-09-18 m6r4 yachi lock 16 (parapet_tss)",
  "2026-09-18 m6r6 yachi lock 44 (parapet_tss)", "2026-09-18 m11r4 yachi lock 50 (parapet_tss)",
  "2026-09-18 m11r5 pinglamb lock 17 (parapet)", "2026-09-18 m11r6 yachi lock 185 (parapet)",
  "2026-09-18 m12r1 pinglamb lock 15 (parapet)", "2026-09-18 m12r3 yachi lock 45 (parapet)",
  "2026-09-18 m12r4 pinglamb lock 85 (parapet)", "2026-09-18 m13r1 pinglamb lock 86 (parapet)",
  "2026-09-18 m14r5 yachi lock 111 (parapet_tss)", "2026-09-18 m15r6 yachi lock 27 (parapet_tss)",
  "2026-09-18 m17r3 yachi lock 18 (parapet)", "2026-09-19 m1r5 yachi lock 19 (parapet_tss)",
  "2026-09-19 m1r6 yachi lock 45 (parapet_tss)", "2026-09-19 m4r1 pinglamb lock 56 (parapet)",
  "2026-09-19 m5r3 yachi lock 15 (parapet_tss)", "2026-09-19 m7r4 pinglamb lock 16 (parapet_tss)",
  "2026-09-19 m9r1 pinglamb lock 17 (parapet)", "2026-09-19 m9r3 pinglamb lock 19 (parapet_tss)",
  "2026-09-19 m9r5 yachi lock 74 (parapet)", "2026-09-19 m11r5 yachi lock 26 (parapet)",
  "2026-09-19 m12r6 pinglamb lock 17 (parapet)", "2026-09-19 m12r6 yachi lock 15 (parapet)",
  "2026-09-19 m13r3 pinglamb lock 63 (parapet)", "2026-09-19 m13r3 yachi lock 276 (parapet)",
  "2026-09-19 m13r6 yachi lock 18 (parapet_tss)", "2026-09-19 m15r1 pinglamb lock 31 (parapet)",
  "2026-09-19 m15r8 yachi lock 39 (parapet)", "2026-09-19 m16r7 pinglamb lock 30 (parapet)",
  "2026-09-19 m17r6 pinglamb lock 17 (parapet)", "2026-09-19 m18r2 pinglamb lock 120 (parapet)",
  "2026-09-19 m18r2 yachi lock 6 (parapet_tss)", "2026-09-19 m18r5 pinglamb lock 35 (parapet)",
  "2026-09-19 m19r7 pinglamb lock 27 (parapet)", "2026-09-19 m20r6 pinglamb lock 19 (parapet)",
  "2026-09-19 m20r6 yachi lock 19 (parapet_tss)", "2026-10-03 m1r5 pinglamb lock 18 (parapet)",
  "2026-10-03 m2r6 yachi lock 32 (parapet)", "2026-10-03 m3r4 pinglamb lock 24 (parapet)",
  "2026-10-03 m3r4 yachi lock 19 (parapet)", "2026-10-03 m3r5 pinglamb lock 19 (parapet)",
  "2026-10-03 m4r2 pinglamb lock 71 (parapet)", "2026-10-03 m4r2 yachi lock 32 (parapet)",
  "2026-10-03 m6r1 pinglamb lock 14 (parapet)", "2026-10-03 m6r2 yachi lock 137 (parapet_tss)",
  "2026-10-03 m7r5 yachi lock 17 (parapet_tss)", "2026-10-03 m9r4 pinglamb lock 59 (parapet_tss)",
  "2026-10-03 m9r6 pinglamb lock 15 (parapet)", "2026-10-03 m10r6 pinglamb lock 45 (parapet)",
  "2026-10-03 m11r2 yachi lock 128 (parapet)", "2026-10-03 m11r4 pinglamb lock 152 (parapet)",
  "2026-10-03 m12r2 pinglamb lock 14 (parapet)", "2026-10-03 m12r6 yachi lock 109 (parapet_tss)",
  "2026-10-03 m15r1 yachi lock 33 (parapet)", "2026-10-03 m15r2 yachi lock 64 (parapet_tss)",
  "2026-10-03 m15r5 pinglamb lock 16 (parapet_tss)", "2026-10-03 m15r7 pinglamb lock 219 (parapet_tss)",
  "2026-10-03 m17r6 yachi lock 105 (parapet_tss)", "2026-10-03 m18r3 pinglamb lock 58 (parapet)",
  "2026-10-03 m20r2 pinglamb lock 216 (parapet)", "2026-10-03 m20r8 pinglamb lock 129 (parapet)",
  "2026-10-03 m20r8 yachi lock 106 (parapet_tss)", "2026-10-09 m2r5 pinglamb lock 16 (parapet)",
  "2026-10-09 m2r6 pinglamb lock 14 (parapet)", "2026-10-09 m3r5 pinglamb lock 16 (parapet)",
  "2026-10-09 m3r8 pinglamb lock 17 (parapet_tss)", "2026-10-09 m5r2 pinglamb lock 68 (parapet)",
  "2026-10-09 m5r3 pinglamb lock 31 (parapet)", "2026-10-09 m5r8 yachi lock 66 (parapet_tss)",
  "2026-10-09 m5r8 yachi lock 75 (parapet_tss)", "2026-10-09 m8r6 yachi lock 37 (parapet)",
  "2026-10-09 m8r7 pinglamb lock 63 (parapet)", "2026-10-09 m8r7 yachi lock 73 (parapet_tss)",
  "2026-10-09 m8r9 pinglamb lock 112 (parapet)", "2026-10-09 m8r9 yachi lock 81 (parapet_tss)",
  "2026-10-09 m8r9 yachi lock 127 (parapet)", "2026-10-09 m9r1 pinglamb lock 112 (parapet)",
  "2026-10-09 m9r7 yachi lock 72 (parapet)", "2026-10-09 m9r9 pinglamb lock 34 (parapet)",
  "2026-10-09 m10r6 pinglamb lock 17 (parapet)", "2026-10-09 m11r2 yachi lock 192 (parapet)",
  "2026-10-09 m12r3 pinglamb lock 101 (parapet)", "2026-10-09 m12r5 yachi lock 15 (parapet_tss)",
  "2026-10-12 m4r6 pinglamb lock 101 (parapet)", "2026-10-12 m6r7 pinglamb lock 18 (parapet)",
  "2026-10-12 m6r7 yachi lock 18 (parapet)", "2026-10-12 m6r8 pinglamb lock 69 (parapet)",
  "2026-10-12 m7r3 pinglamb lock 17 (parapet_tss)", "2026-10-12 m8r2 yachi lock 144 (parapet)",
  "2026-10-12 m8r7 pinglamb lock 139 (parapet)", "2026-10-12 m8r7 yachi lock 64 (parapet)",
  "2026-10-20 m1r1 yachi lock 121 (parapet_tss)", "2026-10-20 m2r1 pinglamb lock 129 (parapet_tss)",
  "2026-10-20 m2r4 yachi lock 50 (parapet)", "2026-10-20 m3r2 pinglamb lock 24 (parapet)",
  "2026-10-20 m4r7 pinglamb lock 76 (parapet)", "2026-10-20 m4r7 pinglamb lock 86 (parapet)",
  "2026-10-20 m4r7 yachi lock 92 (parapet)",
  "2026-10-22 m1r8 pinglamb lock 44 (parapet)", "2026-10-22 m2r4 pinglamb lock 19 (parapet)", "2026-10-22 m2r4 yachi lock 17 (parapet_tss)", "2026-10-22 m2r4 yachi lock 75 (parapet_tss)", "2026-10-22 m3r3 pinglamb lock 17 (parapet)", "2026-10-22 m4r5 pinglamb lock 36 (parapet)", "2026-10-22 m6r4 yachi lock 17 (parapet_tss)", "2026-10-22 m6r7 pinglamb lock 27 (parapet)", "2026-10-22 m7r1 yachi lock 17 (parapet)", "2026-10-22 m7r6 yachi lock 67 (parapet_tss)", "2026-10-22 m8r1 yachi lock 54 (parapet)", "2026-10-22 m8r4 pinglamb lock 48 (parapet_tss)", "2026-10-22 m8r7 pinglamb lock 27 (parapet)", "2026-10-22 m9r5 yachi lock 19 (parapet_tss)", "2026-10-22 m9r5 yachi lock 53 (parapet)",
];
const PARAPET_IN_OPENER: string[] = [
  "2026-07-22 m5r1 pinglamb lock 18 (parapet)", "2026-07-24 m1r1 pinglamb lock 18 (parapet)",
  "2026-07-24 m1r1 yachi lock 18 (parapet_tss)", "2026-07-24 m2r2 pinglamb lock 14 (parapet)",
  "2026-07-24 m4r5 yachi lock 16 (parapet_tss)", "2026-08-01 m2r1 pinglamb lock 14 (parapet)",
  "2026-08-01 m3r3 pinglamb lock 17 (parapet)", "2026-08-01 m5r2 yachi lock 18 (parapet)",
  "2026-08-09 m1r2 yachi lock 19 (parapet_tss)", "2026-08-14 m2r4 pinglamb lock 19 (parapet)",
  "2026-08-14 m7r2 pinglamb lock 17 (parapet)", "2026-08-14 m7r3 yachi lock 18 (parapet_tss)",
  "2026-08-14 m10r8 yachi lock 19 (parapet)", "2026-08-19 m6r3 yachi lock 14 (parapet_tss)",
  "2026-08-19 m8r4 pinglamb lock 14 (parapet)", "2026-08-19 m9r9 pinglamb lock 19 (parapet)",
  "2026-08-19 m9r9 yachi lock 19 (parapet_tss)", "2026-08-19 m10r6 pinglamb lock 17 (parapet_tss)",
  "2026-08-25 m1r8 yachi lock 19 (parapet)", "2026-08-25 m6r5 yachi lock 14 (parapet)",
  "2026-08-25 m8r7 pinglamb lock 17 (parapet_tss)", "2026-09-03 m2r8 pinglamb lock 17 (parapet)",
  "2026-09-03 m3r7 pinglamb lock 18 (parapet)", "2026-09-03 m5r1 yachi lock 18 (parapet_tss)",
  "2026-09-10 m2r7 yachi lock 15 (parapet)", "2026-09-10 m4r1 yachi lock 20 (parapet_tss)",
  "2026-09-10 m4r6 yachi lock 17 (parapet)", "2026-09-10 m5r8 pinglamb lock 17 (parapet_tss)",
  "2026-09-10 m5r8 yachi lock 18 (parapet_tss)", "2026-09-11 m2r6 pinglamb lock 16 (parapet)",
  "2026-09-11 m3r4 yachi lock 19 (parapet)", "2026-09-11 m3r7 pinglamb lock 19 (parapet)",
  "2026-09-17 m1r1 pinglamb lock 19 (parapet)", "2026-09-17 m1r8 pinglamb lock 18 (parapet)",
  "2026-09-17 m2r7 pinglamb lock 15 (parapet)", "2026-09-17 m7r4 pinglamb lock 14 (parapet)",
  "2026-09-18 m4r2 pinglamb lock 19 (parapet)", "2026-09-18 m6r4 yachi lock 16 (parapet_tss)",
  "2026-09-18 m11r5 pinglamb lock 17 (parapet)", "2026-09-18 m12r1 pinglamb lock 15 (parapet)",
  "2026-09-18 m17r3 yachi lock 18 (parapet)", "2026-09-19 m1r5 yachi lock 19 (parapet_tss)",
  "2026-09-19 m5r3 yachi lock 15 (parapet_tss)", "2026-09-19 m7r4 pinglamb lock 16 (parapet_tss)",
  "2026-09-19 m9r1 pinglamb lock 17 (parapet)", "2026-09-19 m9r3 pinglamb lock 19 (parapet_tss)",
  "2026-09-19 m12r6 pinglamb lock 17 (parapet)", "2026-09-19 m12r6 yachi lock 15 (parapet)",
  "2026-09-19 m13r6 yachi lock 18 (parapet_tss)", "2026-09-19 m17r6 pinglamb lock 17 (parapet)",
  "2026-09-19 m18r2 yachi lock 6 (parapet_tss)", "2026-09-19 m20r6 pinglamb lock 19 (parapet)",
  "2026-09-19 m20r6 yachi lock 19 (parapet_tss)", "2026-10-03 m1r5 pinglamb lock 18 (parapet)",
  "2026-10-03 m3r4 yachi lock 19 (parapet)", "2026-10-03 m3r5 pinglamb lock 19 (parapet)",
  "2026-10-03 m6r1 pinglamb lock 14 (parapet)", "2026-10-03 m7r5 yachi lock 17 (parapet_tss)",
  "2026-10-03 m9r6 pinglamb lock 15 (parapet)", "2026-10-03 m12r2 pinglamb lock 14 (parapet)",
  "2026-10-03 m15r5 pinglamb lock 16 (parapet_tss)", "2026-10-09 m2r5 pinglamb lock 16 (parapet)",
  "2026-10-09 m2r6 pinglamb lock 14 (parapet)", "2026-10-09 m3r5 pinglamb lock 16 (parapet)",
  "2026-10-09 m3r8 pinglamb lock 17 (parapet_tss)", "2026-10-09 m10r6 pinglamb lock 17 (parapet)",
  "2026-10-09 m12r5 yachi lock 15 (parapet_tss)", "2026-10-12 m6r7 pinglamb lock 18 (parapet)",
  "2026-10-12 m6r7 yachi lock 18 (parapet)", "2026-10-12 m7r3 pinglamb lock 17 (parapet_tss)",
  "2026-10-22 m2r4 pinglamb lock 19 (parapet)", "2026-10-22 m2r4 yachi lock 17 (parapet_tss)", "2026-10-22 m3r3 pinglamb lock 17 (parapet)", "2026-10-22 m6r4 yachi lock 17 (parapet_tss)", "2026-10-22 m7r1 yachi lock 17 (parapet)", "2026-10-22 m9r5 yachi lock 19 (parapet_tss)",
];
const WELL_DEPTH_LT4: string[] = [
  "2026-07-22 m5r5 yachi lock 39 (parapet_tss: 3 deep)", "2026-07-22 m10r1 yachi lock 116 (parapet_tss: 3 deep)",
  "2026-07-22 m10r5 yachi lock 92 (parapet: 2 deep)", "2026-07-24 m2r2 pinglamb lock 14 (parapet: 2 deep)",
  "2026-07-24 m3r2 pinglamb lock 79 (parapet: 3 deep)", "2026-07-24 m7r7 pinglamb lock 39 (parapet: 2 deep)",
  "2026-07-28 m1r6 yachi lock 61 (parapet_tss: 3 deep)", "2026-07-28 m6r5 yachi lock 40 (parapet: 2 deep)",
  "2026-07-28 m6r5 yachi lock 185 (parapet_tss: 2 deep)", "2026-07-28 m7r4 yachi lock 38 (parapet: 2 deep)",
  "2026-07-28 m7r9 pinglamb lock 47 (parapet: 2 deep)", "2026-08-01 m1r7 yachi lock 26 (parapet: 3 deep)",
  "2026-08-01 m3r3 yachi lock 86 (parapet: 3 deep)", "2026-08-01 m5r2 yachi lock 18 (parapet: 2 deep)",
  "2026-08-01 m5r2 yachi lock 88 (parapet: 3 deep)", "2026-08-01 m7r1 pinglamb lock 82 (parapet: 2 deep)",
  "2026-08-09 m3r3 yachi lock 110 (parapet_tss: 2 deep)", "2026-08-09 m3r8 yachi lock 125 (parapet_tss: 2 deep)",
  "2026-08-09 m4r2 pinglamb lock 29 (parapet: 3 deep)", "2026-08-14 m5r2 yachi lock 81 (parapet_tss: 3 deep)",
  "2026-08-14 m6r3 pinglamb lock 27 (parapet: 2 deep)", "2026-08-14 m9r1 yachi lock 54 (parapet_tss: 2 deep)",
  "2026-08-14 m11r2 yachi lock 41 (parapet: 3 deep)", "2026-08-14 m11r2 yachi lock 90 (parapet: 2 deep)",
  "2026-08-19 m4r7 yachi lock 135 (parapet: 2 deep)", "2026-08-19 m5r5 yachi lock 39 (parapet: 2 deep)",
  "2026-08-19 m5r7 pinglamb lock 46 (parapet: 2 deep)", "2026-08-19 m6r6 pinglamb lock 33 (parapet: 3 deep)",
  "2026-08-19 m9r9 pinglamb lock 149 (parapet: 2 deep)", "2026-08-25 m2r1 yachi lock 53 (parapet_tss: 2 deep)",
  "2026-08-25 m2r1 yachi lock 60 (parapet: 3 deep)", "2026-08-25 m5r8 yachi lock 90 (parapet_tss: 3 deep)",
  "2026-08-25 m6r1 pinglamb lock 110 (parapet: 2 deep)", "2026-08-25 m8r6 yachi lock 156 (parapet: 2 deep)",
  "2026-08-25 m9r7 pinglamb lock 84 (parapet: 3 deep)", "2026-09-03 m2r4 pinglamb lock 26 (parapet: 2 deep)",
  "2026-09-03 m6r6 pinglamb lock 129 (parapet: 2 deep)", "2026-09-03 m6r6 pinglamb lock 216 (parapet: 2 deep)",
  "2026-09-10 m2r3 pinglamb lock 39 (parapet: 2 deep)", "2026-09-11 m2r5 pinglamb lock 134 (parapet: 2 deep)",
  "2026-09-11 m3r7 pinglamb lock 19 (parapet: 2 deep)", "2026-09-11 m6r6 yachi lock 124 (parapet: 2 deep)",
  "2026-09-11 m7r5 pinglamb lock 88 (parapet: 3 deep)", "2026-09-11 m7r8 yachi lock 61 (parapet: 2 deep)",
  "2026-09-17 m2r7 pinglamb lock 15 (parapet: 2 deep)", "2026-09-17 m6r2 yachi lock 125 (parapet: 3 deep)",
  "2026-09-18 m2r2 pinglamb lock 65 (parapet: 3 deep)", "2026-09-18 m3r7 yachi lock 25 (parapet_tss: 3 deep)",
  "2026-09-18 m6r4 yachi lock 16 (parapet_tss: 2 deep)", "2026-09-18 m11r6 yachi lock 185 (parapet: 2 deep)",
  "2026-09-18 m12r3 yachi lock 45 (parapet: 2 deep)", "2026-09-18 m12r4 pinglamb lock 85 (parapet: 2 deep)",
  "2026-09-18 m13r1 pinglamb lock 86 (parapet: 2 deep)", "2026-09-18 m14r5 yachi lock 111 (parapet_tss: 2 deep)",
  "2026-09-18 m17r8 yachi lock 45 (parapet: 2 deep)", "2026-09-19 m5r3 yachi lock 15 (parapet_tss: 2 deep)",
  "2026-09-19 m11r5 yachi lock 26 (parapet: 2 deep)", "2026-09-19 m13r3 pinglamb lock 63 (parapet: 3 deep)",
  "2026-09-19 m13r3 yachi lock 276 (parapet: 2 deep)", "2026-10-03 m4r2 pinglamb lock 71 (parapet: 2 deep)",
  "2026-10-03 m4r2 yachi lock 32 (parapet: 2 deep)", "2026-10-03 m5r4 yachi lock 75 (parapet_tss: 3 deep)",
  "2026-10-03 m9r6 pinglamb lock 15 (parapet: 2 deep)", "2026-10-03 m10r6 pinglamb lock 45 (parapet: 2 deep)",
  "2026-10-03 m12r6 yachi lock 109 (parapet_tss: 3 deep)", "2026-10-03 m15r2 yachi lock 64 (parapet_tss: 2 deep)",
  "2026-10-03 m15r5 pinglamb lock 16 (parapet_tss: 2 deep)",
  "2026-10-03 m15r7 pinglamb lock 219 (parapet_tss: 3 deep)",
  "2026-10-03 m17r6 yachi lock 105 (parapet_tss: 3 deep)", "2026-10-03 m20r7 yachi lock 192 (parapet_tss: 3 deep)",
  "2026-10-09 m2r6 pinglamb lock 14 (parapet: 2 deep)", "2026-10-09 m3r8 pinglamb lock 17 (parapet_tss: 2 deep)",
  "2026-10-09 m5r2 pinglamb lock 68 (parapet: 2 deep)", "2026-10-09 m5r8 yachi lock 66 (parapet_tss: 3 deep)",
  "2026-10-09 m7r7 yachi lock 42 (parapet_tss: 2 deep)", "2026-10-09 m8r7 yachi lock 73 (parapet_tss: 2 deep)",
  "2026-10-09 m8r9 yachi lock 127 (parapet: 2 deep)", "2026-10-09 m9r7 yachi lock 72 (parapet: 3 deep)",
  "2026-10-09 m11r2 yachi lock 192 (parapet: 2 deep)", "2026-10-12 m6r8 pinglamb lock 69 (parapet: 2 deep)",
  "2026-10-12 m8r7 pinglamb lock 139 (parapet: 2 deep)", "2026-10-12 m8r7 yachi lock 64 (parapet: 3 deep)",
  "2026-10-20 m4r7 yachi lock 92 (parapet: 3 deep)",
  "2026-10-22 m7r1 yachi lock 17 (parapet: 2 deep)", "2026-10-22 m7r6 yachi lock 67 (parapet_tss: 3 deep)", "2026-10-22 m8r1 yachi lock 54 (parapet: 2 deep)", "2026-10-22 m9r5 yachi lock 19 (parapet_tss: 2 deep)",
];
const RECON_DROPPED_TSD: string[] = [];
const RECON_DROPPED_TSS: string[] = [];
const HIT_NOT_DONATION: string[] = [
  "2026-07-22 m10r1 yachi lock 116 (parapet_tss: filled_above_window)",
  "2026-07-22 m10r5 yachi lock 92 (parapet: filled_above_window)",
  "2026-07-22 m10r7 yachi lock 88 (parapet: filled_above_window)",
  "2026-07-22 m3r3 yachi lock 38 (parapet_tss: filled_above_window)",
  "2026-07-22 m3r4 yachi lock 84 (parapet_tss: filled_above_window)",
  "2026-07-22 m3r7 pinglamb lock 86 (parapet: filled_above_window)",
  "2026-07-22 m5r1 pinglamb lock 18 (parapet: filled_above_window)",
  "2026-07-22 m5r5 yachi lock 39 (parapet_tss: filled_above_window)",
  "2026-07-22 m5r7 yachi lock 24 (parapet: filled_above_window)",
  "2026-07-22 m9r5 pinglamb lock 171 (parapet: filled_above_window)",
  "2026-07-24 m1r1 pinglamb lock 18 (parapet: filled_above_window)",
  "2026-07-24 m2r2 pinglamb lock 14 (parapet: cavity_lt4)",
  "2026-07-24 m3r2 pinglamb lock 79 (parapet: filled_above_window)",
  "2026-07-24 m6r7 yachi lock 37 (parapet: filled_above_window)",
  "2026-07-24 m7r3 pinglamb lock 118 (parapet: filled_above_window)",
  "2026-07-24 m7r7 pinglamb lock 39 (parapet: cavity_lt4)",
  "2026-07-28 m1r6 yachi lock 61 (parapet_tss: filled_above_window)",
  "2026-07-28 m3r5 yachi lock 33 (parapet_tss: filled_above_window)",
  "2026-07-28 m4r2 yachi lock 166 (parapet: filled_above_window)",
  "2026-07-28 m6r5 yachi lock 185 (parapet_tss: filled_above_window)",
  "2026-07-28 m6r5 yachi lock 40 (parapet: filled_above_window)",
  "2026-07-28 m7r4 yachi lock 38 (parapet: filled_above_window)",
  "2026-07-28 m7r9 pinglamb lock 47 (parapet: cavity_lt4)", "2026-08-01 m1r7 yachi lock 26 (parapet: cavity_lt4)",
  "2026-08-01 m2r2 yachi lock 90 (parapet_tss: filled_above_window)",
  "2026-08-01 m3r3 yachi lock 86 (parapet: filled_above_window)",
  "2026-08-01 m5r2 yachi lock 18 (parapet: filled_above_window)",
  "2026-08-01 m5r2 yachi lock 88 (parapet: filled_above_window)",
  "2026-08-01 m7r1 pinglamb lock 82 (parapet: filled_above_window)",
  "2026-08-09 m3r3 yachi lock 110 (parapet_tss: filled_above_window)",
  "2026-08-09 m3r8 yachi lock 125 (parapet_tss: filled_above_window)",
  "2026-08-09 m4r2 pinglamb lock 29 (parapet: cavity_lt4)",
  "2026-08-09 m5r7 pinglamb lock 27 (parapet: filled_above_window)",
  "2026-08-09 m5r8 pinglamb lock 122 (parapet: filled_above_window)",
  "2026-08-09 m6r2 pinglamb lock 38 (parapet: filled_above_window)",
  "2026-08-14 m11r2 yachi lock 41 (parapet: cavity_lt4)",
  "2026-08-14 m11r2 yachi lock 90 (parapet: filled_above_window)",
  "2026-08-14 m11r5 yachi lock 144 (parapet_tss: filled_above_window)",
  "2026-08-14 m11r7 pinglamb lock 32 (parapet: filled_above_window)",
  "2026-08-14 m4r1 pinglamb lock 45 (parapet: filled_above_window)",
  "2026-08-14 m4r6 yachi lock 207 (parapet_tss: filled_above_window)",
  "2026-08-14 m5r2 pinglamb lock 56 (parapet: filled_above_window)",
  "2026-08-14 m5r2 yachi lock 81 (parapet_tss: filled_above_window)",
  "2026-08-14 m6r3 pinglamb lock 27 (parapet: filled_above_window)",
  "2026-08-14 m8r2 yachi lock 46 (parapet_tss: filled_above_window)",
  "2026-08-14 m9r1 yachi lock 54 (parapet_tss: cavity_lt4)",
  "2026-08-14 m9r3 pinglamb lock 103 (parapet: filled_above_window)",
  "2026-08-19 m4r7 yachi lock 135 (parapet: filled_above_window)",
  "2026-08-19 m4r8 pinglamb lock 104 (parapet: filled_above_window)",
  "2026-08-19 m5r3 yachi lock 39 (parapet_tss: filled_above_window)",
  "2026-08-19 m5r5 yachi lock 39 (parapet: filled_above_window)",
  "2026-08-19 m5r7 pinglamb lock 46 (parapet: filled_above_window)",
  "2026-08-19 m6r6 pinglamb lock 33 (parapet: filled_above_window)",
  "2026-08-19 m9r9 pinglamb lock 149 (parapet: filled_above_window)",
  "2026-08-19 m9r9 yachi lock 41 (parapet_tss: filled_above_window)",
  "2026-08-25 m1r2 yachi lock 68 (parapet: filled_above_window)",
  "2026-08-25 m1r7 pinglamb lock 31 (parapet: filled_above_window)",
  "2026-08-25 m1r7 pinglamb lock 48 (parapet: filled_above_window)",
  "2026-08-25 m2r1 yachi lock 53 (parapet_tss: cavity_lt4)",
  "2026-08-25 m2r1 yachi lock 60 (parapet: filled_above_window)",
  "2026-08-25 m5r8 yachi lock 90 (parapet_tss: filled_above_window)",
  "2026-08-25 m6r1 pinglamb lock 110 (parapet: filled_above_window)",
  "2026-08-25 m6r1 pinglamb lock 136 (parapet: filled_above_window)",
  "2026-08-25 m8r6 yachi lock 156 (parapet: filled_above_window)",
  "2026-08-25 m8r6 yachi lock 218 (parapet: filled_above_window)",
  "2026-08-25 m9r7 pinglamb lock 84 (parapet: filled_above_window)",
  "2026-09-03 m1r6 yachi lock 106 (parapet_tss: filled_above_window)",
  "2026-09-03 m2r4 pinglamb lock 26 (parapet: filled_above_window)",
  "2026-09-03 m2r8 pinglamb lock 17 (parapet: filled_above_window)",
  "2026-09-03 m2r8 yachi lock 30 (parapet: filled_above_window)",
  "2026-09-03 m6r6 pinglamb lock 129 (parapet: filled_above_window)",
  "2026-09-03 m6r6 pinglamb lock 216 (parapet: cavity_lt4)",
  "2026-09-10 m1r5 yachi lock 166 (parapet_tss: filled_above_window)",
  "2026-09-10 m2r3 pinglamb lock 34 (parapet: filled_above_window)",
  "2026-09-10 m2r3 pinglamb lock 39 (parapet: filled_above_window)",
  "2026-09-10 m4r1 yachi lock 20 (parapet_tss: filled_above_window)",
  "2026-09-10 m4r6 yachi lock 17 (parapet: filled_above_window)",
  "2026-09-11 m1r3 yachi lock 24 (parapet_tss: filled_above_window)",
  "2026-09-11 m2r5 pinglamb lock 134 (parapet: filled_above_window)",
  "2026-09-11 m3r5 pinglamb lock 87 (parapet: filled_above_window)",
  "2026-09-11 m3r7 pinglamb lock 19 (parapet: cavity_lt4)",
  "2026-09-11 m5r2 yachi lock 32 (parapet_tss: filled_above_window)",
  "2026-09-11 m6r6 yachi lock 124 (parapet: filled_above_window)",
  "2026-09-11 m7r5 pinglamb lock 88 (parapet: filled_above_window)",
  "2026-09-11 m7r8 yachi lock 61 (parapet: filled_above_window)",
  "2026-09-17 m1r1 pinglamb lock 19 (parapet: filled_above_window)",
  "2026-09-17 m1r8 pinglamb lock 18 (parapet: filled_above_window)",
  "2026-09-17 m2r7 pinglamb lock 15 (parapet: cavity_lt4)",
  "2026-09-17 m2r7 yachi lock 23 (parapet_tss: filled_above_window)",
  "2026-09-17 m6r2 yachi lock 125 (parapet: filled_above_window)",
  "2026-09-17 m7r4 pinglamb lock 14 (parapet: filled_above_window)",
  "2026-09-18 m11r4 yachi lock 50 (parapet_tss: filled_above_window)",
  "2026-09-18 m11r6 yachi lock 185 (parapet: filled_above_window)",
  "2026-09-18 m12r1 pinglamb lock 15 (parapet: filled_above_window)",
  "2026-09-18 m12r3 yachi lock 45 (parapet: filled_above_window)",
  "2026-09-18 m12r4 pinglamb lock 85 (parapet: filled_above_window)",
  "2026-09-18 m13r1 pinglamb lock 86 (parapet: filled_above_window)",
  "2026-09-18 m14r5 yachi lock 111 (parapet_tss: filled_above_window)",
  "2026-09-18 m17r8 yachi lock 45 (parapet: filled_above_window)",
  "2026-09-18 m1r5 pinglamb lock 26 (parapet: filled_above_window)",
  "2026-09-18 m2r2 pinglamb lock 65 (parapet: filled_above_window)",
  "2026-09-18 m3r3 yachi lock 29 (parapet: filled_above_window)",
  "2026-09-18 m3r7 yachi lock 25 (parapet_tss: filled_above_window)",
  "2026-09-18 m6r4 yachi lock 16 (parapet_tss: cavity_lt4)",
  "2026-09-19 m11r5 yachi lock 26 (parapet: filled_above_window)",
  "2026-09-19 m13r3 pinglamb lock 63 (parapet: filled_above_window)",
  "2026-09-19 m13r3 yachi lock 276 (parapet: cavity_lt4)",
  "2026-09-19 m15r1 pinglamb lock 31 (parapet: filled_above_window)",
  "2026-09-19 m15r8 yachi lock 39 (parapet: filled_above_window)",
  "2026-09-19 m18r5 pinglamb lock 35 (parapet: filled_above_window)",
  "2026-09-19 m19r7 pinglamb lock 27 (parapet: filled_above_window)",
  "2026-09-19 m1r5 yachi lock 19 (parapet_tss: filled_above_window)",
  "2026-09-19 m20r6 pinglamb lock 19 (parapet: filled_above_window)",
  "2026-09-19 m5r3 yachi lock 15 (parapet_tss: cavity_lt4)",
  "2026-09-19 m9r5 yachi lock 74 (parapet: filled_above_window)",
  "2026-10-03 m10r6 pinglamb lock 45 (parapet: filled_above_window)",
  "2026-10-03 m11r4 pinglamb lock 152 (parapet: filled_above_window)",
  "2026-10-03 m12r6 yachi lock 109 (parapet_tss: filled_above_window)",
  "2026-10-03 m15r1 yachi lock 33 (parapet: filled_above_window)",
  "2026-10-03 m15r2 yachi lock 64 (parapet_tss: filled_above_window)",
  "2026-10-03 m15r5 pinglamb lock 16 (parapet_tss: cavity_lt4)",
  "2026-10-03 m15r7 pinglamb lock 219 (parapet_tss: cavity_lt4)",
  "2026-10-03 m17r3 yachi lock 73 (parapet: filled_above_window)",
  "2026-10-03 m17r6 yachi lock 105 (parapet_tss: filled_above_window)",
  "2026-10-03 m18r3 pinglamb lock 58 (parapet: filled_above_window)",
  "2026-10-03 m20r2 pinglamb lock 216 (parapet: filled_above_window)",
  "2026-10-03 m20r7 yachi lock 192 (parapet_tss: filled_above_window)",
  "2026-10-03 m20r8 pinglamb lock 129 (parapet: filled_above_window)",
  "2026-10-03 m2r6 yachi lock 32 (parapet: filled_above_window)",
  "2026-10-03 m3r4 pinglamb lock 24 (parapet: filled_above_window)",
  "2026-10-03 m3r4 yachi lock 19 (parapet: filled_above_window)",
  "2026-10-03 m3r5 pinglamb lock 19 (parapet: filled_above_window)",
  "2026-10-03 m4r2 pinglamb lock 71 (parapet: filled_above_window)",
  "2026-10-03 m4r2 yachi lock 32 (parapet: filled_above_window)",
  "2026-10-03 m5r4 yachi lock 75 (parapet_tss: filled_above_window)",
  "2026-10-03 m6r2 yachi lock 137 (parapet_tss: filled_above_window)",
  "2026-10-03 m9r4 pinglamb lock 59 (parapet_tss: filled_above_window)",
  "2026-10-03 m9r6 pinglamb lock 15 (parapet: cavity_lt4)",
  "2026-10-09 m11r2 yachi lock 192 (parapet: filled_above_window)",
  "2026-10-09 m12r3 pinglamb lock 101 (parapet: filled_above_window)",
  "2026-10-09 m2r6 pinglamb lock 14 (parapet: filled_above_window)",
  "2026-10-09 m3r8 pinglamb lock 17 (parapet_tss: cavity_lt4)",
  "2026-10-09 m5r2 pinglamb lock 68 (parapet: filled_above_window)",
  "2026-10-09 m5r8 yachi lock 66 (parapet_tss: filled_above_window)",
  "2026-10-09 m5r8 yachi lock 75 (parapet_tss: filled_above_window)",
  "2026-10-09 m7r7 yachi lock 42 (parapet_tss: filled_above_window)",
  "2026-10-09 m8r7 pinglamb lock 63 (parapet: filled_above_window)",
  "2026-10-09 m8r7 yachi lock 73 (parapet_tss: filled_above_window)",
  "2026-10-09 m8r9 pinglamb lock 112 (parapet: filled_above_window)",
  "2026-10-09 m8r9 yachi lock 127 (parapet: filled_above_window)",
  "2026-10-09 m9r1 pinglamb lock 112 (parapet: filled_above_window)",
  "2026-10-09 m9r7 yachi lock 72 (parapet: cavity_lt4)",
  "2026-10-09 m9r9 pinglamb lock 34 (parapet: filled_above_window)",
  "2026-10-12 m4r6 pinglamb lock 101 (parapet: filled_above_window)",
  "2026-10-12 m6r8 pinglamb lock 69 (parapet: filled_above_window)",
  "2026-10-12 m8r2 yachi lock 144 (parapet: filled_above_window)",
  "2026-10-12 m8r7 pinglamb lock 139 (parapet: filled_above_window)",
  "2026-10-12 m8r7 yachi lock 64 (parapet: filled_above_window)",
  "2026-10-20 m1r1 yachi lock 121 (parapet_tss: filled_above_window)",
  "2026-10-20 m2r1 pinglamb lock 129 (parapet_tss: filled_above_window)",
  "2026-10-20 m2r4 yachi lock 50 (parapet: filled_above_window)",
  "2026-10-20 m3r2 pinglamb lock 24 (parapet: filled_above_window)",
  "2026-10-20 m4r7 pinglamb lock 76 (parapet: filled_above_window)",
  "2026-10-20 m4r7 yachi lock 92 (parapet: filled_above_window)",
  "2026-10-22 m1r8 pinglamb lock 44 (parapet: filled_above_window)",
  "2026-10-22 m2r4 yachi lock 75 (parapet_tss: filled_above_window)",
  "2026-10-22 m3r3 pinglamb lock 17 (parapet: filled_above_window)",
  "2026-10-22 m6r7 pinglamb lock 27 (parapet: filled_above_window)",
  "2026-10-22 m7r1 yachi lock 17 (parapet: filled_above_window)",
  "2026-10-22 m7r6 yachi lock 67 (parapet_tss: cavity_lt4)",
  "2026-10-22 m8r1 yachi lock 54 (parapet: filled_above_window)",
  "2026-10-22 m8r4 pinglamb lock 48 (parapet_tss: filled_above_window)",
  "2026-10-22 m8r7 pinglamb lock 27 (parapet: filled_above_window)",
  "2026-10-22 m9r5 yachi lock 19 (parapet_tss: cavity_lt4)",
];

/** window_off_board, per variant and player: a count with a property check, not a list (see the header). */
const WINDOW_OFF_BOARD = { parapet: { pinglamb: 1292, yachi: 1329 }, parapet_tss: { pinglamb: 7, yachi: 121 } };
/** Per player: the opportunities (scored full TSDs and TSSs), split at the 0-based opener window. */
const DENOM = {
  pinglamb: { TSD: { all: 5636, in_opener: 1113, mid_game: 4523 }, TSS: { all: 647, in_opener: 80, mid_game: 567 } },
  yachi: { TSD: { all: 5100, in_opener: 1317, mid_game: 3783 }, TSS: { all: 1051, in_opener: 257, mid_game: 794 } },
};
/** Per variant and player: hits, their split, mirrored, garbage in the window. */
const HITS = {
  parapet: { pinglamb: { all: 111, in_opener: 36, mid_game: 75, mirrored: 42, garbage_in_window: 107 },
             yachi: { all: 61, in_opener: 12, mid_game: 49, mirrored: 29, garbage_in_window: 56 } },
  parapet_tss: { pinglamb: { all: 15, in_opener: 8, mid_game: 7, mirrored: 4, garbage_in_window: 15 },
                 yachi: { all: 72, in_opener: 20, mid_game: 52, mirrored: 38, garbage_in_window: 68 } },
};
/** Per variant and player: the payoff (stored under `followup_by_player`, the shared artefact key). */
const PAYOFF = {
  parapet: {
    pinglamb: { fired: 62, not_fired: { i_in_well_not_quad: 3, past_verified: 1, round_ended: 1, well_covered: 20,
                                        well_filled_not_i: 24 } },
    yachi: { fired: 27, not_fired: { i_in_well_not_quad: 1, past_verified: 2, round_ended: 1, well_covered: 9,
                                     well_filled_not_i: 21 } },
  },
  parapet_tss: {
    pinglamb: { fired: 11, not_fired: { well_covered: 4 } },
    yachi: { fired: 55, not_fired: { i_in_well_not_quad: 2, round_ended: 1, well_covered: 14 } },
  },
};
/** The controls per variant. Under parapet_tss the TSD is a control (the profile's opportunity, in the TSS's place). */
const CONTROLS = {
  parapet: {
    under: { TSS: { pinglamb: 5, yachi: 2 }, TST: { pinglamb: 0, yachi: 0 },
             mini_TSS: { pinglamb: 0, yachi: 0 }, mini_TSD: { pinglamb: 0, yachi: 0 } },
    ablation: { no_must_empty: { pinglamb: 740, yachi: 457 }, no_roof: { pinglamb: 335, yachi: 248 },
                t_overlap: { pinglamb: 701, yachi: 575 } },
    orientation_baseline: { pinglamb: 52, yachi: 67 },
  },
  parapet_tss: {
    under: { TSD: { pinglamb: 0, yachi: 0 }, TST: { pinglamb: 0, yachi: 0 },
             mini_TSS: { pinglamb: 0, yachi: 0 }, mini_TSD: { pinglamb: 0, yachi: 0 } },
    ablation: { no_must_empty: { pinglamb: 19, yachi: 96 }, no_roof: { pinglamb: 15, yachi: 72 },
                t_overlap: { pinglamb: 17, yachi: 72 } },
    orientation_baseline: { pinglamb: 144, yachi: 406 },
  },
};
/** What discriminates, measured: full T-spins of the variant's kind (not only hits) whose anchored T meets ONE part
 *  of the window — the rows above the cleared rows, the cleared rows, the rows under them (the well). The cleared
 *  rows are entailed by the clear (NaiveClauseForced) and do the least work; the well rows under them do the most.
 *  For the TSD the `no_roof` ablation (the window less the row above the T) is exactly `below`. */
const PART_ONLY = { parapet: { above: 6095, cleared: 9381, below: 583 },
                    parapet_tss: { above: 206, cleared: 487, below: 175 } };
/** BT砲's window and this one agree, in the same hand, on every cell they share (the BT is built from the Parapet
 *  terrain): a lock that is a hit of both is possible, so it is named rather than asserted absent. */
const BTCANNON_ALSO_PARAPET: string[] = [];

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(PARAPET, m, digests());
const nameOf = (d: TechDigest, lock: number) => `${d.session} m${d.match}r${d.round + 1} ${d.user} lock ${lock}`;
const hitKey = (h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`;
const keyOf = (d: TechDigest, lock: number) => `${d.session}|${d.file}|${d.round}|${d.user}|${lock}`;
const USERS = ['pinglamb', 'yachi'] as const;
const VIDS = ['parapet', 'parapet_tss'] as const;

/** A drawing (rows top first, '-' or '.' empty) as a 40-row matcher board, every other cell filled. */
const pad = (rows: string[]) => [...Array(H - rows.length).fill('.'.repeat(W)),
                                 ...rows.map(r => [...r].map(ch => ch === '-' || ch === '.' ? '.' : 'X').join(''))];
const cellsAt = (slot: number[][], top: number): Cell[] => slot.map(([row, col]) => ({ row: row! + top, col: col! }));
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
const same = (a: Cell[], b: Cell[]) => a.length === b.length && a.every(q => b.some(x => x.row === q.row && x.col === q.col));
/** where a variant fires on a drawing: [cells (drawing frame), mirrored] for every T placement */
const firesAnywhere = (v: any, rows: string[]) => {
  const b = pad(rows), top = H - rows.length;
  return tPlacements(b).flatMap(cs => fires(v, b, cs).map(m => [cs.map(q => [q.row - top, q.col]).sort((x, y) => x[0]! - y[0]! || x[1]! - y[1]!), m]));
};
const sorted = (s: number[][]) => [...s].map(x => [...x]).sort((x, y) => x[0]! - y[0]! || x[1]! - y[1]!);
const norm = (rows: string[]) => rows.map(r => [...r].map(ch => ch === '.' ? '-' : 'c').join(''));
const image = (n: string) => TR.cross_source.tetrisch.images.find((x: any) => x.file === `parapet_${n}.jpg`);

test('the committed artefact is what build() produces now (byte identity)', () => {
  expect(serialise(run({}))).toBe(readFileSync(ART_PATH, 'utf8'));
}, 600_000);

test('quarantined: report_eligible false, no claim ids, both variants each measured at its own spin', () => {
  const a = art();
  expect(a.report_eligible).toBe(false);
  expect(JSON.stringify(a)).not.toMatch(/data-claim|\b[CRG]\d{3}\b|✓/);
  expect(a.sessions).toEqual(SESSIONS);
  expect(a.cross_route).toBeUndefined();
  expect(a.variant_opportunities).toEqual({ parapet: 'TSD', parapet_tss: 'TSS' });
  expect(Object.keys(a.variants)).toEqual([...VIDS]);
  // every hit carries its well depth, and a payoff hit's depth is at least the two cells the window entails
  for (const h of a.hits) expect(h.well_depth, `${h.session} ${h.lock}`).toBeGreaterThanOrEqual(2);
});

test('the scored T-spins are the ones emit-opener-facts.ts scores (the third copy of the loop)', () => {
  const n = checkScoredAgainstOpenerFacts(art(), SESSIONS, ROOT);
  expect(n).toBe(15141);
  expect(art().check.reconstruction_disagreed).toBe(0);
});

test('the Python twin on the drawings: windowMatch fires where the gate records it, and nowhere else', () => {
  const xs = TR.cross_source;
  const bt = JSON.parse(readFileSync(`${import.meta.dir}/${xs.bt_cannon.file}`, 'utf8'));
  const btRows = (id: string) => bt.nodes.find((n: any) => n.id === id).rows as string[];
  const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));
  for (const v of [TSD, TSS]) {
    // the external drawings: once, at the recorded slot, as drawn; at no other T placement
    const ext: [string, string[], number[][]][] = [
      ['BT砲 parapet', btRows(xs.bt_cannon.drawing), xs.bt_cannon.slots[v.id]],
      ['harddrop', norm(xs.harddrop.pages.pre_t_board.rows), xs.harddrop.slots[v.id]],
      ...Object.keys(xs.tetrisch.slots).map(n => [`tetrisch ${n}`, norm(image(n).rows), xs.tetrisch.slots[n][v.id]] as [string, string[], number[][]]),
    ];
    for (const [name, rows, slot] of ext)
      expect(firesAnywhere(v, rows), `${v.id} ${name}`).toEqual([[sorted(slot), false]]);
    // the page's own two basic forms, at their agreement slots
    for (const a of v.agreement) expect(firesAnywhere(v, byId.get(a.board).rows), `${v.id} ${a.board}`)
      .toEqual([[sorted(a.t_cells), false]]);
    // BT砲's 途中BT build (built on the Parapet terrain): at the cells the gate records
    const bb = xs.bt_cannon.fires.filter((e: any) => e.node === 'bt.build' && e.variant === v.id);
    expect(firesAnywhere(v, btRows('bt.build')), v.id).toEqual(bb.map((e: any) => [sorted(e.cells), false]));
    // Tetrisチャンネル's plain TSD boards and bare terrains: never
    for (const n of ['001', '005', '009', '016']) expect(firesAnywhere(v, norm(image(n).rows)), `${v.id} ${n}`).toEqual([]);
  }
  // the routes boards: the two same-author 山岳積み2号 boards (TSD, as drawn), nothing for the TSS
  const lockOf = (rows: string[], top: number) => rows.flatMap((r, i) => [...r].flatMap((ch, c) => ch === 'U' ? [{ row: i + top, col: c }] : []));
  const got: string[] = [];
  for (const f of readdirSync(import.meta.dir).filter(x => x.endsWith('-routes.json')).sort()) {
    for (const n of JSON.parse(readFileSync(`${import.meta.dir}/${f}`, 'utf8')).nodes) {
      if (!n.rows) continue;
      const b = pad(n.rows.map((r: string) => r.replace(/U/g, '-'))), cells = lockOf(n.rows, H - n.rows.length);
      if (cells.length !== 4) continue;
      for (const v of [TSD, TSS]) for (const m of fires(v, b, cells)) got.push(`${f} ${n.id} ${v.id}${m ? ' (mirrored)' : ''}`);
    }
  }
  expect(got).toEqual(xs.also.map((e: any) => `${e.file} ${e.node} ${e.variant}${e.mirrored ? ' (mirrored)' : ''}`));
  expect(xs.fires).toEqual([]);
  expect(xs.routes_fire_none.length).toBeGreaterThan(0);
});

test('the transcription the artefact read is the committed one, and its windows are the gated ones', () => {
  for (const v of [TSD, TSS]) {
    expect(v.window_basis).toBe('agreement');
    expect(v.window).toEqual({ rows: [1, 5], cols: [1, 5] });
    expect(v.followup).toBeUndefined();
    expect(v.payoff).toMatchObject({ kind: 'well_quad', piece: 'I', lines: 4, well_cell_pre_clear: [4, 2] });
    // the payoff variant carries no follow-up slot, and its well is mirrored with the window
    const [d, m] = prepare(TR, v);
    expect([d!.followup, d!.followupKind, m!.followup, m!.followupKind]).toEqual([[], '', [], '']);
    expect([d!.well, m!.well]).toEqual([{ r: 4, c: 2 }, { r: 4, c: 4 }]);
  }
  expect([TSD.spin, TSD.lines, TSS.spin, TSS.lines]).toEqual(['TSD', 2, 'TSS', 1]);
  expect(TSD.t_cells).toEqual([[2, 2], [2, 3], [2, 4], [3, 3]]);
  expect(TSS.t_cells).toEqual([[1, 3], [2, 3], [2, 4], [3, 3]]);
  expect(TR.empty_letters).toBe('');
  // a variant with both, or neither, of followup and payoff is refused by the matcher
  expect(() => prepare(TR, { ...TSD, followup: { board: 'x', spin: 'TSD', lines: 2, t_cells_pre_clear: [], t_cells_after: [] } })).toThrow();
  expect(() => prepare(TR, { ...TSD, payoff: undefined })).toThrow();
});

test('named lists: every hit, every payoff miss, the opener hits, garbage, shallow wells, the empty lists', () => {
  const L = art().lists;
  checkNamedList('parapet_hits', L.parapet_hits, PARAPET_HITS);
  checkNamedList('parapet_tss_hits', L.parapet_tss_hits, PARAPET_TSS_HITS);
  checkNamedList('payoff_not_fired', L.payoff_not_fired, PAYOFF_NOT_FIRED);
  checkNamedList('garbage_in_window', L.garbage_in_window, GARBAGE_IN_WINDOW);
  checkNamedList('parapet_in_opener', L.parapet_in_opener, PARAPET_IN_OPENER);
  checkNamedList('well_depth_lt4', L.well_depth_lt4, WELL_DEPTH_LT4);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, RECON_DROPPED_TSD);
  checkNamedList('recon_dropped_tss', L.recon_dropped_tss, RECON_DROPPED_TSS);
  checkHitPositions(art(), SESSIONS, ROOT, [...PARAPET_HITS, ...PARAPET_TSS_HITS, ...PAYOFF_NOT_FIRED, ...GARBAGE_IN_WINDOW,
                                            ...PARAPET_IN_OPENER, ...WELL_DEPTH_LT4, ...HIT_NOT_DONATION]);
  expect(art().hits.length).toBe(PARAPET_HITS.length + PARAPET_TSS_HITS.length);
});

test('window_off_board: pinned per variant and player, every entry a T of that variant whose window leaves the board', () => {
  const L: string[] = art().lists.window_off_board;
  for (const vid of VIDS) for (const u of USERS)
    expect(L.filter(x => x.split(' ')[2] === u && x.endsWith(`(${vid})`)).length, `${vid} ${u}`).toBe(WINDOW_OFF_BOARD[vid][u]);
  const want = new Set<string>();
  const hits = new Set(art().hits.map(hitKey));
  for (const d of digests()) for (const s of scored(d)) {
    if (s.lk.spin !== 'full') continue;
    for (const v of [TSD, TSS]) {
      if (s.lk.cleared !== v.lines || hits.has(keyOf(d, s.i))) continue;
      const Ps = prepare(TR, v);
      if (Ps.some(P => windowMatch(s.board, s.lk.cells, P) === null) && !Ps.some(P => !!windowMatch(s.board, s.lk.cells, P)))
        want.add(`${nameOf(d, s.i)} (${v.id})`);
    }
  }
  for (const x of L) expect(want.has(x), x).toBe(true);
  expect(new Set(L).size).toBe(L.length);
  expect(L.length).toBe(want.size);
}, 600_000);

test('pinned: denominators, hits, payoffs, controls; the structural zeros re-derived from the window', () => {
  const a = art();
  for (const u of USERS) {
    expect(a.denominators[u].TSD, u).toEqual(DENOM[u].TSD);
    expect(a.denominators[u].TSS, u).toEqual(DENOM[u].TSS);
  }
  for (const vid of VIDS) {
    const v = a.variants[vid];
    for (const u of USERS) {
      expect(v.hits_by_player[u], `${vid} ${u}`).toEqual(HITS[vid][u]);
      expect(v.followup_by_player[u], `${vid} ${u}`).toEqual(PAYOFF[vid][u]);
      expect(PAYOFF[vid][u].fired + total(PAYOFF[vid][u].not_fired)).toBe(HITS[vid][u].all);
    }
    expect(v.controls, vid).toEqual(CONTROLS[vid]);
  }
  // STRUCTURAL, not measured: each zero below follows from the window, so it is re-derived here and not only pinned.
  // The TSS's T is its window's top row: no cell of the window lies above it, so no_roof is the headline itself
  const tssTop = Math.min(...TSS.t_cells.map((x: number[]) => x[0]!));
  expect(TSS.window.rows[0]).toBe(tssTop);
  for (const u of USERS) expect(a.variants.parapet_tss.controls.ablation.no_roof[u]).toBe(HITS.parapet_tss[u].all);
  // Re-derived, each from the window: (a) under the TSS window a TSD cannot anchor — a full TSD's T is flat (two
  // rows), the TSS window's T is stood (three); (b) under the TSD window a TST cannot anchor — a lock clears only rows
  // it puts a cell in, and the TSD window's T spans two rows; (c) under the TSS window a TST cannot match — the
  // anchored T spans three rows, and every one of them but the cleared row holds a must-empty window cell, so it
  // cannot be full
  const span = (cells: number[][]) => new Set(cells.map(x => x[0])).size;
  expect([span(TSD.t_cells), span(TSS.t_cells)]).toEqual([2, 3]);
  for (const P of prepare(TR, TSS)) {
    const tRows = [...new Set(P.T.map(x => x.r))];
    const blocked = tRows.filter(r => P.cells.some(x => x.r === r && x.v === '.'));
    expect(blocked.length).toBe(tRows.length - TSS.lines);
  }
  for (const u of USERS) {
    expect(a.variants.parapet_tss.controls.under.TSD[u]).toBe(0);
    expect(a.variants.parapet_tss.controls.under.TST[u]).toBe(0);
    expect(a.variants.parapet.controls.under.TST[u]).toBe(0);
  }
});

test('the other flat-T windows: clashes per hand pairing, and the hit sets', () => {
  const normP = (P: ReturnType<typeof prepare>[number]) => {
    const r = Math.min(...P.T.map(x => x.r)), c = Math.min(...P.T.map(x => x.c));
    return { T: P.T.map(x => `${x.r - r},${x.c - c}`).sort().join(' '),
             cells: new Map(P.cells.map(x => [`${x.r - r},${x.c - c}`, x.v])) };
  };
  const mine = new Set(art().hits.map(hitKey));
  for (const other of [STMBCAVE, DOUBLEDAGGER, BTCANNON, CUTCOPY, SHACHIKUTRAIN]) {
    const tr = JSON.parse(readFileSync(other.transcriptionPath, 'utf8'));
    // every variant of 千鳥格子 (both its windows lay the T flat, nub down; `uncut` included), the others' first
    for (const ov of (other === CUTCOPY ? tr.variants : [tr.variants[0]]))
    for (const a of prepare(TR, TSD)) for (const b of prepare(tr, ov)) {
      const A = normP(a), B = normP(b);
      expect(A.T, other.key).toBe(B.T);
      const clash = [...A.cells].filter(([k, v]) => B.cells.has(k) && B.cells.get(k) !== v && v !== 'T');
      // BT砲 is built from this terrain: in the same hand the two windows agree on every shared cell
      if (other.key === 'btcannon' && a.mirrored === b.mirrored) expect(clash, other.key).toEqual([]);
      else expect(clash.length, `${other.key} ${a.mirrored} ${b.mirrored}`).toBeGreaterThan(0);
    }
    const theirs = JSON.parse(readFileSync(other.artefactPath, 'utf8')).hits;
    const both = theirs.filter((h: any) => mine.has(hitKey(h))).map((h: any) => `${h.session} m${h.match}r${h.round} ${h.player} lock ${h.lock}`);
    if (other.key === 'btcannon') checkNamedList('BTCANNON_ALSO_PARAPET', both, BTCANNON_ALSO_PARAPET);
    else expect(both, other.key).toEqual([]);
  }
});

test('what discriminates: each part of the window alone, with the T anchored, against the headline', () => {
  const hits = new Set(art().hits.map(hitKey));
  for (const v of [TSD, TSS]) {
    const cleared = v.id === 'parapet' ? [2, 3] : [3];
    const parts: Record<'above' | 'cleared' | 'below', (r: number) => boolean> = {
      above: r => r < cleared[0]!, cleared: r => cleared.includes(r), below: r => r > cleared[cleared.length - 1]!,
    };
    const got: Record<string, number> = {};
    for (const [name, keep] of Object.entries(parts)) {
      const preps = prepare(TR, v).map(P => ({ ...P, cells: P.cells.filter(x => x.v === 'T' || keep(x.r)) }));
      let n = 0, hitsIn = 0;
      for (const d of digests()) for (const s of scored(d)) {
        if (s.lk.spin !== 'full' || s.lk.cleared !== v.lines) continue;
        if (!preps.some(P => !!windowMatch(s.board, s.lk.cells, P))) continue;
        n++;
        if (hits.has(keyOf(d, s.i))) hitsIn++;
      }
      expect(hitsIn, `${v.id} ${name}`).toBe(art().hits.filter((h: any) => h.variant === v.id).length);
      got[name] = n;
    }
    expect(got, v.id).toEqual(PART_ONLY[v.id as 'parapet']);
    // no single part gives the headline; the well rows under the cleared rows cut the most
    const headline = art().hits.filter((h: any) => h.variant === v.id).length;
    for (const n of Object.values(got)) expect(n).toBeGreaterThan(headline);
    expect(got.below!).toBeLessThan(got.above!);
    expect(got.below!).toBeLessThan(got.cleared!);
  }
  expect(total(art().variants.parapet.controls.ablation.no_roof)).toBe(PART_ONLY.parapet.below);
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
    // the hit's well column: the variant's well cell, under the offset the window matched at
    const v = TR.variants.find((x: any) => x.id === h.variant);
    const P = prepare(TR, v).find(p => p.mirrored === h.mirrored)!;
    const off = windowMatch(s.board, s.lk.cells, P);
    if (!off) throw new Error(`${nameOf(d, s.i)}: the recorded hit does not match`);
    const why = donationVerdict(s.withT, s.rows, s.lk.cells, P.well!.c + off.dc);
    if (why === 'donation') hitDon++;
    else notDon.push(`${nameOf(d, s.i)} (${h.variant}: ${why})`);
  }
  for (const sess of SESSIONS) {
    const of = JSON.parse(readFileSync(`${ROOT}/${sess}/sim/opener-facts.json`, 'utf8'));
    expect(Object.keys(count[sess]!).sort(), sess).toEqual(of.donation.players.map((p: any) => p.user).sort());
    for (const p of of.donation.players) expect(count[sess]![p.user], `${sess} ${p.user}`).toBe(p.donations);
  }
  checkNamedList('HIT_NOT_DONATION', notDon, HIT_NOT_DONATION);
  expect(hitDon + notDon.length).toBe(art().hits.length);
  // the window entails the re-opening INSIDE it; what a hit fails is outside it (a filled cell above the window in
  // the well column) or below it (a well under four deep): never the T's own slot, never the naive clause, never
  // the walls the window checks
  for (const x of HIT_NOT_DONATION) expect(x).toMatch(/: (filled_above_window|cavity_lt4)\)$/);
}, 600_000);

test('the payoff row map is verified against the engine at every step it uses', () => {
  const c = art().check;
  expect(c.rowmap_unverified).toBe(30);
  expect(c.rowmap_steps).toBe(264047);
  expect(art().hits.every((h: any) => h.followup.reason !== 'rowmap_unverified')).toBe(true);
});

test('mutants: each rule turned off turns this red with its own symptom, or is named equivalent', () => {
  const base = serialise(run({}));
  const b = JSON.parse(base);
  const sum = (a: any, k: string, vid = 'parapet') =>
    total(Object.fromEntries(Object.entries(a.variants[vid].hits_by_player).map(([u, x]: any) => [u, x[k]])));
  const fired = (a: any, vid: string) =>
    total(Object.fromEntries(Object.entries(a.variants[vid].followup_by_player).map(([u, x]: any) => [u, x.fired])));
  const den = (a: any, kind: string, k = 'all') => a.denominators.pinglamb[kind][k] + a.denominators.yachi[kind][k];
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };
  const k = (h: any) => `${h.session} ${h.file} ${h.round_index0} ${h.player} ${h.lock} ${h.variant}`;

  let a = mut({ noMirror: true });
  for (const vid of VIDS) {
    expect(sum(a, 'mirrored', vid)).toBe(0);
    expect(sum(a, 'all', vid)).toBe(sum(b, 'all', vid) - sum(b, 'mirrored', vid));
  }

  a = mut({ pastPrefix: true });
  expect(a.denominators.pinglamb.unscored_past_prefix + a.denominators.yachi.unscored_past_prefix).toBe(0);
  expect(den(a, 'TSD')).toBeGreaterThan(den(b, 'TSD'));

  // a mini spin read as full: the TSS denominator gains every mini TSS
  a = mut({ includeMini: true });
  expect(den(a, 'TSS')).toBe(den(b, 'TSS') + den(b, 'mini_TSS'));

  // without the must-empty cells, or the rows above the T, the window is weaker and its hits are the ablation's
  a = mut({ noMustEmpty: true });
  for (const vid of VIDS) expect(sum(a, 'all', vid)).toBe(total(b.variants[vid].controls.ablation.no_must_empty));
  a = mut({ noRoof: true });
  expect(sum(a, 'all')).toBe(total(b.variants.parapet.controls.ablation.no_roof));
  expect(sum(a, 'all')).toBe(PART_ONLY.parapet.below);
  expect(sum(a, 'all', 'parapet_tss')).toBe(sum(b, 'all', 'parapet_tss'));   // the TSS has no roof (structural)

  a = mut({ tOverlap: true });
  for (const vid of VIDS) expect(sum(a, 'all', vid)).toBe(total(b.variants[vid].controls.ablation.t_overlap));

  a = mut({ rowAnchorOff1: true });
  for (const vid of VIDS) expect(sum(a, 'all', vid)).toBe(0);

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
  for (const vid of VIDS) expect(fired(a, vid)).toBeGreaterThan(fired(b, vid));
  expect(a.hits.filter((h: any) => ['well_filled_not_i', 'i_in_well_not_quad'].includes(h.followup.reason)).length).toBe(0);
  a = payoffOnly({ payoffNoQuad: true });
  expect(a.hits.filter((h: any) => h.followup.reason === 'i_in_well_not_quad').length).toBe(0);
  expect(fired(a, 'parapet') + fired(a, 'parapet_tss'))
    .toBe(fired(b, 'parapet') + fired(b, 'parapet_tss') + b.hits.filter((h: any) => h.followup.reason === 'i_in_well_not_quad').length);

  for (const [m] of Object.entries(EQUIVALENT))
    expect(serialise(run({ [m]: true } as Mutants)), m).toBe(base);
}, 900_000);

/** A two-lock digest from a drawing: the spin into `slot` on `pre` (every non-empty cell filled), then `next` (a
 *  piece's cells, in the frame of the board the spin leaves) with `cleared` lines; `garbage` rows pushed in after
 *  the spin; `v` the verified index. Mirrored: columns reflected. */
function drawingDigest(pre: string[], slot: number[][], next: { piece: string; cells: number[][]; cleared: number },
                       o: { mirrored?: boolean; garbage?: number; v?: number; spin?: string } = {}): TechDigest {
  const mc = (c: number) => o.mirrored ? W - 1 - c : c;
  const flip = (r: string) => o.mirrored ? [...r].reverse().join('') : r;
  const board = pad(pre.map(flip)), top = H - pre.length;
  const t: Cell[] = slot.map(([r, c]) => ({ row: r! + top, col: mc(c!) }));
  const g = board.map(r => [...r]);
  for (const q of t) { expect(g[q.row]![q.col]).toBe('.'); g[q.row]![q.col] = 'X'; }
  const full = g.flatMap((r, i) => r.every(x => x !== '.') ? [i] : []);
  const nextCells: Cell[] = next.cells.map(([r, c]) => ({ row: r! + top - (o.garbage ?? 0), col: mc(c!) }));
  const lock = (piece: string, spin: string, cells: Cell[], rows: number[], cleared: number, garbage = 0) =>
    ({ piece, spin, cleared, cells, clearedRows: rows, garbage, mapOk: true });
  return { session: 'page', file: 'parapet', round: 0, match: 1, user: 'page', v: o.v ?? 1,
           locks: [lock('T', o.spin ?? 'full', t, full, full.length, o.garbage ?? 0),
                   lock(next.piece, 'none', nextCells, [], next.cleared)],
           tspins: [{ i: 0, board }] };
}

test('the payoff on independent drawings: Tetrisチャンネル\'s 4-deep sequence and harddrop\'s fumen fire, and each payoff mutant breaks it', () => {
  const tc = TR.cross_source.tetrisch, hd = TR.cross_source.harddrop;
  const tSlot = (n: string) => image(n).rows.flatMap((r: string, i: number) => [...r].flatMap((ch, c) => ch === 'T' ? [[i, c]] : []));
  const iCells = (n: string) => image(n).rows.flatMap((r: string, i: number) => [...r].flatMap((ch, c) => ch === 'I' ? [[i, c]] : []));
  const cases: [string, string[], number[][], number[][]][] = [
    ['tetrisch 012 → 013 → 015', image('012').rows, tSlot('013'), iCells('015')],
    ['harddrop pages 8-10', hd.pages.pre_t_board.rows, hd.pages.t_lock.cells, hd.pages.i_lock.cells],
  ];
  expect(tSlot('013')).toEqual(tc.slots['012'].parapet);
  const one = (dg: TechDigest, m: Mutants = {}) => {
    const c = classify(PARAPET, TR, [dg], m);
    expect(c.hits.length).toBe(1);
    expect(c.hits[0]!.variant).toBe('parapet');
    return c.hits[0]!;
  };
  for (const [name, pre, slot, icell] of cases) for (const mirrored of [false, true]) {
    const quad = { piece: 'I', cells: icell, cleared: 4 };
    const h = one(drawingDigest(pre, slot, quad, { mirrored }));
    expect(h.mirrored, name).toBe(mirrored);
    expect(h.followup, name).toEqual({ lock: 1, fired: true, reason: null });
    expect(h.well_depth, name).toBe(4);
    // an I that does not clear four: refused, and fired by the mutant that accepts any I
    expect(one(drawingDigest(pre, slot, { ...quad, cleared: 3 }, { mirrored })).followup.reason).toBe('i_in_well_not_quad');
    expect(one(drawingDigest(pre, slot, { ...quad, cleared: 3 }, { mirrored }), { payoffNoQuad: true }).followup.fired).toBe(true);
    // another piece into the well: refused, and fired by the mutant that accepts any piece
    expect(one(drawingDigest(pre, slot, { ...quad, piece: 'J' }, { mirrored })).followup.reason).toBe('well_filled_not_i');
    expect(one(drawingDigest(pre, slot, { ...quad, piece: 'J' }, { mirrored }), { payoffAnyPiece: true }).followup.fired).toBe(true);
    // the quad past the verified prefix: refused, and fired by the mutant that reads past it
    expect(one(drawingDigest(pre, slot, quad, { mirrored, v: 0 })).followup.reason).toBe('past_verified');
    expect(one(drawingDigest(pre, slot, quad, { mirrored, v: 0 }), { pastPrefix: true }).followup.fired).toBe(true);
    // four garbage rows under the well before the quad: the row map carries the well up to the I; without it, the
    // carried cell stays below the I and the I reads as covering the well
    const g4 = drawingDigest(pre, slot, quad, { mirrored, garbage: 4 });
    expect(one(g4).followup.fired, name).toBe(true);
    expect(one(g4, { followupNoRowmap: true }).followup.reason, name).toBe('well_covered');
    // the well carried in the drawn columns on a mirrored hit: the I is in another column, and nothing else enters it
    expect(one(drawingDigest(pre, slot, quad, { mirrored }), { followupUnmirrored: true }).followup.fired, name).toBe(!mirrored);
  }
  // Tetrisチャンネル's 2-deep sequence: a hit, its well two deep
  const h2 = classify(PARAPET, TR, [drawingDigest(image('002').rows, tSlot('003'), { piece: 'O', cells: [[0, 0], [0, 1], [1, 0], [1, 1]], cleared: 0 })]).hits;
  expect(h2.map(h => [h.variant, h.well_depth, h.followup.reason])).toEqual([['parapet', 2, 'round_ended']]);
});

/** The hits that qualify (`parapet-qualify.ts`): the L one whole piece, it and the two roof cells whole pieces with
 *  no garbage, and no Perfect Clear within 14 locks either side of the T. */
const QUALIFIED_HITS = [
  '2026-07-22 m5r5 yachi lock 39 (parapet_tss)', '2026-07-22 m9r5 pinglamb lock 171 (parapet)',
  '2026-07-24 m3r2 pinglamb lock 79 (parapet)', '2026-07-24 m7r3 pinglamb lock 118 (parapet)',
  '2026-07-28 m3r5 yachi lock 33 (parapet_tss)', '2026-07-28 m6r5 yachi lock 185 (parapet_tss)',
  '2026-08-01 m5r2 yachi lock 18 (parapet)', '2026-08-19 m6r6 pinglamb lock 33 (parapet)',
  '2026-08-25 m6r1 pinglamb lock 110 (parapet)', '2026-09-03 m2r8 yachi lock 30 (parapet)',
  '2026-09-03 m4r6 yachi lock 98 (parapet_tss)', '2026-09-11 m5r2 yachi lock 32 (parapet_tss)',
  '2026-09-18 m2r2 pinglamb lock 65 (parapet)', '2026-09-18 m14r5 yachi lock 111 (parapet_tss)',
  '2026-09-19 m18r2 yachi lock 6 (parapet_tss)', '2026-10-03 m20r7 yachi lock 192 (parapet_tss)',
  '2026-10-03 m20r8 pinglamb lock 129 (parapet)', '2026-10-09 m7r7 yachi lock 42 (parapet_tss)',
  '2026-10-22 m4r5 pinglamb lock 36 (parapet)', '2026-10-22 m8r1 yachi lock 54 (parapet)'];
/** Hits failing one rule and nothing else; `fragment` and `garbage_in_shape` alone fail none (every such hit also
 *  has its L split), which is why the rule-off check below turns them off beside `allowSplitL`. */
const ONLY: Record<string, string[]> = {
  l_not_one_piece: [
    '2026-07-22 m10r7 yachi lock 88 (parapet)', '2026-07-28 m6r5 yachi lock 40 (parapet)',
    '2026-08-01 m3r3 yachi lock 86 (parapet)', '2026-08-01 m6r1 pinglamb lock 43 (parapet_tss)',
    '2026-08-01 m7r2 yachi lock 33 (parapet_tss)', '2026-08-14 m5r2 yachi lock 81 (parapet_tss)',
    '2026-08-14 m6r3 pinglamb lock 27 (parapet)', '2026-08-14 m9r1 yachi lock 54 (parapet_tss)',
    '2026-08-19 m5r3 yachi lock 39 (parapet_tss)', '2026-08-19 m5r7 pinglamb lock 46 (parapet)',
    '2026-09-03 m2r4 pinglamb lock 26 (parapet)', '2026-09-18 m11r6 yachi lock 185 (parapet)',
    '2026-09-19 m18r2 pinglamb lock 120 (parapet)', '2026-10-03 m5r4 yachi lock 75 (parapet_tss)',
    '2026-10-03 m6r2 yachi lock 137 (parapet_tss)', '2026-10-20 m4r7 yachi lock 92 (parapet)',
    '2026-10-22 m7r1 yachi lock 17 (parapet)', '2026-10-22 m7r6 yachi lock 67 (parapet_tss)'],
  dpc: ['2026-08-14 m6r8 pinglamb lock 27 (parapet_tss)'],
  ownership_unverified: ['2026-08-25 m8r6 yachi lock 156 (parapet)', '2026-08-25 m8r6 yachi lock 218 (parapet)',
                         '2026-09-18 m12r3 yachi lock 45 (parapet)'],
  fragment: [], garbage_in_shape: [],
};
const QUALIFY_BY_PLAYER = {
  pinglamb: { qualified: 8, not_qualified: { dpc: 1, fragment: 106, garbage_in_shape: 12, l_not_one_piece: 117 } },
  yachi: { qualified: 12, not_qualified: { fragment: 98, garbage_in_shape: 18, l_not_one_piece: 118, ownership_unverified: 3 } },
};
const qName = (h: any) => `${h.session} m${h.match}r${h.round} ${h.player} lock ${h.lock} (${h.variant})`;

test('qualifies: pinned per player, the qualifying list, the one-rule failures, the six cells read', () => {
  const a = art();
  expect(a.qualify.by_player).toEqual(QUALIFY_BY_PLAYER);
  expect(a.hits.filter((h: any) => h.qualifies).map(qName)).toEqual(QUALIFIED_HITS);
  expect(a.lists.qualified_hits.length).toBe(QUALIFIED_HITS.length);
  for (const [rule, names] of Object.entries(ONLY))
    expect(a.hits.filter((h: any) => h.not_qualified.join() === rule).map(qName), rule).toEqual(names);
  expect(a.hits.some((h: any) => h.not_qualified.includes('shape_cell_empty'))).toBe(false);
  expect(a.hits.every((h: any) => typeof h.qualifies === 'boolean' && h.qualifies === (h.not_qualified.length === 0))).toBe(true);
  // the L's four cells and the roof's two: what both builds draw as a piece of their own inside the window
  const sh = qualifyShape(TR);
  expect(sh.filter(x => x.l).map(x => [x.dr, x.dc])).toEqual([[-2, -2], [-1, -2], [0, -2], [0, -1]]);
  expect(sh.filter(x => !x.l).map(x => [x.dr, x.dc])).toEqual([[-2, 1], [-2, 2]]);
});

test('qualifies: the ownership guard throws on a board it cannot reproduce', () => {
  const a = art();
  const h = a.hits.find((x: any) => qName(x) === QUALIFIED_HITS[0]);
  const d = digests().find(x => x.session === h.session && x.file === h.file && x.round === h.round_index0 && x.user === h.player)!;
  const q = parapetQualifier(PARAPET.transcriptionPath);
  expect(q(h, d)).toEqual({ qualifies: true, not_qualified: [] });
  const t = d.tspins.find(x => x.i === h.lock)!;
  const r = t.board.findIndex(row => row.includes('.') && /[^.G]/.test(row));
  const bad = { ...d, tspins: d.tspins.map(x => x !== t ? x
    : { ...x, board: x.board.map((row, i) => i !== r ? row : row.replace(/[^.G]/, '.')) }) };
  expect(() => q(h, bad)).toThrow(/ownership disagrees/);
}, 600_000);

test('qualifies: each rule turned off qualifies exactly the hits whose only failures are rules turned off', () => {
  const b = art();
  const runQ = (m: ParapetQualifyMutants) => {
    const P = { ...PARAPET, qualify: { ...PARAPET.qualify!, check: parapetQualifier(PARAPET.transcriptionPath, m) } };
    return JSON.parse(serialise(build(P, {}, digests())));
  };
  const within = (rules: string[]) => b.hits.filter((h: any) => h.not_qualified.every((x: string) => rules.includes(x))).map(qName);
  for (const [m, rules] of [[{ allowSplitL: true }, ['l_not_one_piece']], [{ noDpc: true }, ['dpc']],
                            [{ allowSplitL: true, allowFragments: true }, ['l_not_one_piece', 'fragment']],
                            [{ allowSplitL: true, allowGarbage: true }, ['l_not_one_piece', 'garbage_in_shape']]] as const) {
    const want = within([...rules]);
    expect(want.length, JSON.stringify(m)).toBeGreaterThan(QUALIFIED_HITS.length);
    expect(runQ(m).hits.filter((h: any) => h.qualifies).map(qName), JSON.stringify(m)).toEqual(want);
  }
}, 1_800_000);

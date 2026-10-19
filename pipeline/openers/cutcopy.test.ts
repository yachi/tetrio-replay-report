/**
 * The 千鳥格子 (Cut Copy) technique artefact (`analysis/cutcopy-facts.json`, from `pipeline/sim/emit-technique-facts.ts
 * --technique cutcopy`; the rules are the shared `technique-facts.ts`, the profile `technique-profile-cutcopy.ts`, the
 * shape the gated `pipeline/openers/cutcopy-technique.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count in every session and for
 *      every player (`donation.check`, `donation.players`), as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN, on the drawings: `windowMatch` (TS) fires on each of harddrop's Cut_copy drawings the gate
 *      records, and on the Cut Copy harddrop's BT_Cannon page draws (read out of `btcannon-technique.json`) — once,
 *      at its drawn T, in its recorded hand, and at no other T placement; at no drawn T the gate names as a miss;
 *      on each no-T board the gate records, at its recorded placement; on this page's own drawings at their
 *      agreement slots; on the T-hole build with its Z left out, nowhere (the page's 「Z may go in after the first
 *      T-spin」, which the window does not express); and on no routes board (the gate's `cross_source.fires` is
 *      empty, with its reason).
 *   4. STMB CAVE, ダブルダガー AND BT砲 ARE NOT THIS: all four lay the T flat, nub down; anchored on the same T this
 *      window clashes with each of theirs on a cell in every pairing of hands (re-derived from the transcriptions),
 *      so no lock is a hit of two of them, and none is.
 *   5. WHAT DISCRIMINATES: measured per window part, with the T anchored (the row above the T, the cleared rows,
 *      the row under them), against the headline: no single part gives it. The cleared rows are entailed by the
 *      clear and do no work; the row above and the row below each cut them down (the row below by at least ten
 *      times, the row above by less — both asserted), so those two are what discriminate.
 *   6. NAMED lists, not bounds; pinned per-player figures; mutants, each with its asserted symptom (the one
 *      equivalent mutant named, measured, asserted to STAY byte-identical).
 *   7. THE FOLLOW-UP on the page's own drawings: the TSD into `basic.spin`'s slot, then the T into the slot
 *      `second.spin` draws, as a two-lock digest, as drawn and mirrored — it fires, and the follow-up mutants
 *      break it there as they do on the corpus.
 *
 * window_off_board is not listed entry by entry: it is every flat, nub-down T at a TSD whose window leaves the
 * board before the matcher found a mismatch (the window reaches two columns past one end of the T and three past
 * the other), thousands of them. It is pinned per player as a count, and every entry is checked to be such a T
 * with its window off the board in at least one hand and not a hit (STMB Cave's treatment, for the same reason).
 *
 * Run: bun test pipeline/openers/cutcopy.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, classify, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest, type Cell }
  from '../sim/technique-facts.ts';
import { CUTCOPY } from '../sim/technique-profile-cutcopy.ts';
import { STMBCAVE } from '../sim/technique-profile-stmbcave.ts';
import { DOUBLEDAGGER } from '../sim/technique-profile-doubledagger.ts';
import { BTCANNON } from '../sim/technique-profile-btcannon.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12']);
const ART_PATH = `${import.meta.dir}/../../analysis/cutcopy-facts.json`;
const TR = JSON.parse(readFileSync(CUTCOPY.transcriptionPath, 'utf8'));
const H = 40;

/** Every hit: the flat T into the page's window, as drawn (roof over the T's right end) or mirrored. */
const CUTCOPY_HITS: string[] = [
  "2026-07-22 m1r5 yachi lock 79 (mirrored)", "2026-07-22 m3r8 pinglamb lock 35 (mirrored)",
  "2026-07-22 m8r3 yachi lock 40", "2026-07-22 m8r4 yachi lock 47 (mirrored)", "2026-07-22 m8r8 yachi lock 54",
  "2026-07-24 m3r3 pinglamb lock 242 (mirrored)", "2026-07-24 m7r5 yachi lock 84",
  "2026-07-28 m2r2 pinglamb lock 44", "2026-07-28 m4r1 yachi lock 83", "2026-07-28 m5r2 yachi lock 30",
  "2026-07-28 m5r5 pinglamb lock 62 (mirrored)", "2026-07-28 m6r8 yachi lock 31", "2026-07-28 m7r6 yachi lock 35",
  "2026-07-28 m8r3 yachi lock 53", "2026-08-01 m1r4 pinglamb lock 94", "2026-08-01 m3r5 yachi lock 61",
  "2026-08-01 m5r2 yachi lock 79 (mirrored)", "2026-08-09 m1r6 yachi lock 128 (mirrored)",
  "2026-08-09 m4r4 yachi lock 43", "2026-08-09 m5r3 pinglamb lock 22", "2026-08-09 m5r5 pinglamb lock 60 (mirrored)",
  "2026-08-14 m1r5 yachi lock 124", "2026-08-14 m5r2 yachi lock 51 (mirrored)",
  "2026-08-14 m5r2 yachi lock 105 (mirrored)", "2026-08-14 m9r1 pinglamb lock 53 (mirrored)",
  "2026-08-14 m9r1 yachi lock 89", "2026-08-14 m9r4 pinglamb lock 192 (mirrored)",
  "2026-08-14 m9r4 pinglamb lock 241 (mirrored)", "2026-08-14 m10r8 yachi lock 101",
  "2026-08-14 m11r4 yachi lock 41", "2026-08-14 m11r6 yachi lock 45 (mirrored)", "2026-08-19 m1r6 pinglamb lock 11",
  "2026-08-19 m4r3 pinglamb lock 53 (mirrored)", "2026-08-19 m4r8 yachi lock 76", "2026-08-19 m5r2 pinglamb lock 25",
  "2026-08-19 m6r3 yachi lock 73", "2026-08-19 m6r6 yachi lock 109 (mirrored)",
  "2026-08-25 m1r6 yachi lock 91 (mirrored)", "2026-08-25 m3r2 pinglamb lock 60",
  "2026-08-25 m3r5 pinglamb lock 173", "2026-08-25 m5r3 pinglamb lock 106 (mirrored)",
  "2026-08-25 m8r2 yachi lock 117", "2026-08-25 m8r7 pinglamb lock 199",
  "2026-09-03 m2r2 pinglamb lock 144 (mirrored)", "2026-09-03 m4r1 yachi lock 48",
  "2026-09-03 m4r7 pinglamb lock 40", "2026-09-03 m5r2 yachi lock 62 (mirrored)",
  "2026-09-03 m5r4 yachi lock 100 (mirrored)", "2026-09-03 m6r2 pinglamb lock 51",
  "2026-09-10 m4r5 yachi lock 124 (mirrored)", "2026-09-11 m3r7 yachi lock 19",
  "2026-09-11 m4r1 yachi lock 155 (mirrored)", "2026-09-11 m4r4 yachi lock 27",
  "2026-09-11 m6r2 yachi lock 62 (mirrored)", "2026-09-11 m7r4 yachi lock 31 (mirrored)",
  "2026-09-11 m7r5 yachi lock 107 (mirrored)", "2026-09-17 m1r2 pinglamb lock 58 (mirrored)",
  "2026-09-17 m6r1 yachi lock 72", "2026-09-18 m3r7 yachi lock 46", "2026-09-18 m4r2 pinglamb lock 99",
  "2026-09-18 m6r5 yachi lock 50", "2026-09-18 m15r1 yachi lock 52 (mirrored)",
  "2026-09-18 m15r7 pinglamb lock 46 (mirrored)", "2026-09-18 m16r2 yachi lock 36",
  "2026-09-18 m16r2 yachi lock 215 (mirrored)", "2026-09-18 m17r9 yachi lock 151",
  "2026-09-19 m2r1 yachi lock 95 (mirrored)", "2026-09-19 m3r1 yachi lock 80 (mirrored)",
  "2026-09-19 m3r4 yachi lock 60", "2026-09-19 m3r8 pinglamb lock 137", "2026-09-19 m4r3 yachi lock 32 (mirrored)",
  "2026-09-19 m8r2 yachi lock 58 (mirrored)", "2026-09-19 m8r3 yachi lock 74 (mirrored)",
  "2026-09-19 m8r5 yachi lock 130 (mirrored)", "2026-09-19 m9r1 pinglamb lock 103 (mirrored)",
  "2026-09-19 m9r1 yachi lock 34 (mirrored)", "2026-09-19 m11r1 yachi lock 52", "2026-09-19 m12r3 yachi lock 34",
  "2026-09-19 m14r5 yachi lock 26 (mirrored)", "2026-09-19 m17r2 pinglamb lock 90",
  "2026-09-19 m20r5 pinglamb lock 89", "2026-10-03 m2r9 yachi lock 111 (mirrored)",
  "2026-10-03 m3r1 pinglamb lock 47 (mirrored)", "2026-10-03 m4r2 yachi lock 15 (mirrored)",
  "2026-10-03 m6r1 pinglamb lock 69", "2026-10-03 m8r5 yachi lock 85", "2026-10-03 m9r1 yachi lock 145",
  "2026-10-03 m9r4 yachi lock 164", "2026-10-03 m12r2 yachi lock 32 (mirrored)",
  "2026-10-03 m12r3 pinglamb lock 38 (mirrored)", "2026-10-03 m16r6 pinglamb lock 271",
  "2026-10-03 m17r3 pinglamb lock 87", "2026-10-03 m17r3 pinglamb lock 224", "2026-10-03 m17r3 yachi lock 121",
  "2026-10-03 m18r1 yachi lock 65", "2026-10-03 m20r4 yachi lock 179 (mirrored)", "2026-10-09 m1r4 yachi lock 34",
  "2026-10-09 m1r5 yachi lock 30", "2026-10-09 m4r4 pinglamb lock 66 (mirrored)", "2026-10-09 m7r5 yachi lock 33",
  "2026-10-09 m8r3 pinglamb lock 67", "2026-10-09 m8r7 yachi lock 97", "2026-10-09 m9r1 yachi lock 83",
  "2026-10-09 m9r1 yachi lock 111", "2026-10-09 m9r8 yachi lock 115", "2026-10-12 m2r4 yachi lock 154 (mirrored)",
  "2026-10-12 m3r5 yachi lock 45 (mirrored)", "2026-10-12 m5r6 pinglamb lock 52",
  "2026-10-12 m8r5 yachi lock 163 (mirrored)",
];
const FOLLOWUP_NOT_FIRED: string[] = [
  "2026-07-22 m1r5 yachi lock 79 (slot_filled_before_t at lock 80)",
  "2026-07-22 m8r8 yachi lock 54 (next_t_elsewhere at lock 60)", "2026-07-28 m4r1 yachi lock 83 (round_ended)",
  "2026-07-28 m5r5 pinglamb lock 62 (slot_filled_before_t at lock 63)",
  "2026-07-28 m6r8 yachi lock 31 (next_t_elsewhere at lock 35)",
  "2026-07-28 m7r6 yachi lock 35 (slot_filled_before_t at lock 36)",
  "2026-07-28 m8r3 yachi lock 53 (slot_filled_before_t at lock 54)",
  "2026-08-01 m1r4 pinglamb lock 94 (round_ended)",
  "2026-08-01 m3r5 yachi lock 61 (slot_filled_before_t at lock 62)",
  "2026-08-09 m1r6 yachi lock 128 (slot_filled_before_t at lock 132)",
  "2026-08-09 m5r3 pinglamb lock 22 (slot_filled_before_t at lock 23)",
  "2026-08-14 m1r5 yachi lock 124 (next_t_elsewhere at lock 129)",
  "2026-08-14 m9r4 pinglamb lock 192 (next_t_elsewhere at lock 195)",
  "2026-08-14 m9r4 pinglamb lock 241 (slot_filled_before_t at lock 243)",
  "2026-08-14 m10r8 yachi lock 101 (slot_filled_before_t at lock 102)",
  "2026-08-14 m11r4 yachi lock 41 (slot_filled_before_t at lock 42)",
  "2026-08-19 m4r3 pinglamb lock 53 (slot_filled_before_t at lock 56)",
  "2026-08-19 m5r2 pinglamb lock 25 (slot_filled_before_t at lock 29)",
  "2026-08-19 m6r3 yachi lock 73 (slot_filled_before_t at lock 74)",
  "2026-08-25 m1r6 yachi lock 91 (slot_filled_before_t at lock 92)",
  "2026-08-25 m3r2 pinglamb lock 60 (slot_filled_before_t at lock 61)",
  "2026-08-25 m3r5 pinglamb lock 173 (slot_filled_before_t at lock 174)",
  "2026-08-25 m5r3 pinglamb lock 106 (slot_filled_before_t at lock 107)",
  "2026-08-25 m8r2 yachi lock 117 (slot_filled_before_t at lock 118)",
  "2026-09-03 m5r2 yachi lock 62 (slot_filled_before_t at lock 63)",
  "2026-09-11 m3r7 yachi lock 19 (slot_filled_before_t at lock 20)",
  "2026-09-11 m4r1 yachi lock 155 (slot_filled_before_t at lock 156)",
  "2026-09-11 m4r4 yachi lock 27 (slot_filled_before_t at lock 28)",
  "2026-09-11 m7r5 yachi lock 107 (slot_filled_before_t at lock 108)",
  "2026-09-17 m6r1 yachi lock 72 (slot_filled_before_t at lock 73)",
  "2026-09-18 m3r7 yachi lock 46 (next_t_elsewhere at lock 52)",
  "2026-09-18 m4r2 pinglamb lock 99 (slot_filled_before_t at lock 100)",
  "2026-09-18 m16r2 yachi lock 215 (slot_filled_before_t at lock 216)",
  "2026-09-19 m2r1 yachi lock 95 (slot_filled_before_t at lock 97)",
  "2026-09-19 m3r8 pinglamb lock 137 (slot_filled_before_t at lock 138)",
  "2026-09-19 m4r3 yachi lock 32 (slot_filled_before_t at lock 33)",
  "2026-09-19 m8r3 yachi lock 74 (slot_filled_before_t at lock 79)", "2026-09-19 m8r5 yachi lock 130 (round_ended)",
  "2026-09-19 m9r1 pinglamb lock 103 (slot_filled_before_t at lock 104)",
  "2026-09-19 m9r1 yachi lock 34 (slot_filled_before_t at lock 35)",
  "2026-09-19 m11r1 yachi lock 52 (slot_filled_before_t at lock 53)",
  "2026-10-03 m2r9 yachi lock 111 (slot_filled_before_t at lock 113)",
  "2026-10-03 m4r2 yachi lock 15 (next_t_elsewhere at lock 21)", "2026-10-03 m9r4 yachi lock 164 (round_ended)",
  "2026-10-03 m12r2 yachi lock 32 (slot_filled_before_t at lock 36)",
  "2026-10-03 m12r3 pinglamb lock 38 (slot_filled_before_t at lock 39)",
  "2026-10-03 m16r6 pinglamb lock 271 (past_verified at lock 273)",
  "2026-10-03 m17r3 pinglamb lock 224 (round_ended)",
  "2026-10-03 m17r3 yachi lock 121 (slot_filled_before_t at lock 123)",
  "2026-10-03 m20r4 yachi lock 179 (slot_filled_before_t at lock 180)",
  "2026-10-09 m1r4 yachi lock 34 (next_t_elsewhere at lock 35)",
  "2026-10-09 m7r5 yachi lock 33 (t_in_slot_not_tsd at lock 37)",
  "2026-10-09 m8r7 yachi lock 97 (slot_filled_before_t at lock 99)",
  "2026-10-09 m9r1 yachi lock 83 (slot_filled_before_t at lock 85)",
  "2026-10-09 m9r8 yachi lock 115 (slot_filled_before_t at lock 117)",
];
const GARBAGE_IN_WINDOW: string[] = [
  "2026-07-22 m1r5 yachi lock 79", "2026-07-22 m3r8 pinglamb lock 35", "2026-07-22 m8r3 yachi lock 40",
  "2026-07-22 m8r4 yachi lock 47", "2026-07-22 m8r8 yachi lock 54", "2026-07-24 m3r3 pinglamb lock 242",
  "2026-07-24 m7r5 yachi lock 84", "2026-07-28 m2r2 pinglamb lock 44", "2026-07-28 m4r1 yachi lock 83",
  "2026-07-28 m5r2 yachi lock 30", "2026-07-28 m5r5 pinglamb lock 62", "2026-07-28 m6r8 yachi lock 31",
  "2026-07-28 m7r6 yachi lock 35", "2026-07-28 m8r3 yachi lock 53", "2026-08-01 m1r4 pinglamb lock 94",
  "2026-08-01 m3r5 yachi lock 61", "2026-08-01 m5r2 yachi lock 79", "2026-08-09 m1r6 yachi lock 128",
  "2026-08-09 m4r4 yachi lock 43", "2026-08-09 m5r3 pinglamb lock 22", "2026-08-09 m5r5 pinglamb lock 60",
  "2026-08-14 m1r5 yachi lock 124", "2026-08-14 m5r2 yachi lock 51", "2026-08-14 m5r2 yachi lock 105",
  "2026-08-14 m9r1 pinglamb lock 53", "2026-08-14 m9r1 yachi lock 89", "2026-08-14 m9r4 pinglamb lock 192",
  "2026-08-14 m9r4 pinglamb lock 241", "2026-08-14 m10r8 yachi lock 101", "2026-08-14 m11r4 yachi lock 41",
  "2026-08-14 m11r6 yachi lock 45", "2026-08-19 m4r3 pinglamb lock 53", "2026-08-19 m4r8 yachi lock 76",
  "2026-08-19 m5r2 pinglamb lock 25", "2026-08-19 m6r3 yachi lock 73", "2026-08-19 m6r6 yachi lock 109",
  "2026-08-25 m1r6 yachi lock 91", "2026-08-25 m3r2 pinglamb lock 60", "2026-08-25 m3r5 pinglamb lock 173",
  "2026-08-25 m5r3 pinglamb lock 106", "2026-08-25 m8r2 yachi lock 117", "2026-08-25 m8r7 pinglamb lock 199",
  "2026-09-03 m4r1 yachi lock 48", "2026-09-03 m4r7 pinglamb lock 40", "2026-09-03 m5r2 yachi lock 62",
  "2026-09-03 m5r4 yachi lock 100", "2026-09-03 m6r2 pinglamb lock 51", "2026-09-10 m4r5 yachi lock 124",
  "2026-09-11 m3r7 yachi lock 19", "2026-09-11 m4r1 yachi lock 155", "2026-09-11 m6r2 yachi lock 62",
  "2026-09-11 m7r4 yachi lock 31", "2026-09-11 m7r5 yachi lock 107", "2026-09-17 m1r2 pinglamb lock 58",
  "2026-09-17 m6r1 yachi lock 72", "2026-09-18 m3r7 yachi lock 46", "2026-09-18 m4r2 pinglamb lock 99",
  "2026-09-18 m6r5 yachi lock 50", "2026-09-18 m15r7 pinglamb lock 46", "2026-09-18 m16r2 yachi lock 36",
  "2026-09-18 m17r9 yachi lock 151", "2026-09-19 m2r1 yachi lock 95", "2026-09-19 m3r1 yachi lock 80",
  "2026-09-19 m3r4 yachi lock 60", "2026-09-19 m3r8 pinglamb lock 137", "2026-09-19 m4r3 yachi lock 32",
  "2026-09-19 m8r2 yachi lock 58", "2026-09-19 m8r3 yachi lock 74", "2026-09-19 m8r5 yachi lock 130",
  "2026-09-19 m9r1 pinglamb lock 103", "2026-09-19 m11r1 yachi lock 52", "2026-09-19 m12r3 yachi lock 34",
  "2026-09-19 m17r2 pinglamb lock 90", "2026-09-19 m20r5 pinglamb lock 89", "2026-10-03 m2r9 yachi lock 111",
  "2026-10-03 m3r1 pinglamb lock 47", "2026-10-03 m6r1 pinglamb lock 69", "2026-10-03 m8r5 yachi lock 85",
  "2026-10-03 m9r4 yachi lock 164", "2026-10-03 m12r2 yachi lock 32", "2026-10-03 m16r6 pinglamb lock 271",
  "2026-10-03 m17r3 pinglamb lock 87", "2026-10-03 m17r3 pinglamb lock 224", "2026-10-03 m17r3 yachi lock 121",
  "2026-10-03 m18r1 yachi lock 65", "2026-10-09 m1r4 yachi lock 34", "2026-10-09 m1r5 yachi lock 30",
  "2026-10-09 m4r4 pinglamb lock 66", "2026-10-09 m8r3 pinglamb lock 67", "2026-10-09 m9r1 yachi lock 83",
  "2026-10-09 m9r1 yachi lock 111", "2026-10-09 m9r8 yachi lock 115", "2026-10-12 m2r4 yachi lock 154",
  "2026-10-12 m5r6 pinglamb lock 52", "2026-10-12 m8r5 yachi lock 163",
];
const CUTCOPY_IN_OPENER: string[] = [
  "2026-08-19 m1r6 pinglamb lock 11", "2026-09-11 m3r7 yachi lock 19", "2026-10-03 m4r2 yachi lock 15",
];
const RECON_DROPPED_TSD: string[] = [];
/** window_off_board, per player: a count with a property check, not a list (see the header). */
const WINDOW_OFF_BOARD = { pinglamb: 1648, yachi: 1674 };

/** Per player: the opportunity (scored full TSDs), split at the 0-based opener window. */
const TSD_DENOM = { pinglamb: { all: 5307, in_opener: 1043, mid_game: 4264 },
                    yachi: { all: 4751, in_opener: 1242, mid_game: 3509 } };
/** Per player: hits, their split, the mirrored ones, the ones with garbage in the window, the follow-ups. */
const HITS = { pinglamb: { all: 36, in_opener: 1, mid_game: 35, mirrored: 16, garbage_in_window: 33 },
               yachi: { all: 73, in_opener: 2, mid_game: 71, mirrored: 33, garbage_in_window: 62 } };
const FOLLOWUP = {
  pinglamb: { fired: 20, not_fired: { next_t_elsewhere: 1, past_verified: 1, round_ended: 2, slot_filled_before_t: 12 } },
  yachi: { fired: 34, not_fired: { next_t_elsewhere: 6, round_ended: 3, slot_filled_before_t: 29, t_in_slot_not_tsd: 1 } },
};
/** The controls (the same window at other spins; the ablations; the orientation baseline). */
const CONTROLS = {
  under: { TSS: { pinglamb: 4, yachi: 1 }, TST: { pinglamb: 0, yachi: 0 },
           mini_TSS: { pinglamb: 0, yachi: 0 }, mini_TSD: { pinglamb: 0, yachi: 0 } },
  ablation: { no_must_empty: { pinglamb: 694, yachi: 519 }, no_roof: { pinglamb: 399, yachi: 342 },
              t_overlap: { pinglamb: 44, yachi: 76 } },
  orientation_baseline: { pinglamb: 43, yachi: 61 },
};
/** What discriminates, measured: full TSDs (not only hits) whose anchored T meets ONE part of the window — the
 *  row above the T (the outer slot's arms, the wall beside them, the roof and the cell beyond it), the two rows
 *  the TSD clears, or the row under them (the outer slot's nub cell, walled). The cleared rows are entailed by the
 *  clear and admit every flat, nub-down full TSD whose window is on the board, so they do no work. The row above and
 *  the row below each cut that down — the row below by at least ten times, the row above by less (both asserted
 *  where PART_ONLY is checked) — and neither alone reaches the headline, so those two are what discriminate. The
 *  `no_roof` ablation (the window less the row above the T) is exactly `below`. */
const PART_ONLY = { above: 1477, cleared: 8786, below: 741 };

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(CUTCOPY, m, digests());
const nameOf = (d: TechDigest, lock: number) => `${d.session} m${d.match}r${d.round + 1} ${d.user} lock ${lock}`;
const hitKeys = (a: any = art()) => new Set(a.hits.map((h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`));
const keyOf = (d: TechDigest, lock: number) => `${d.session}|${d.file}|${d.round}|${d.user}|${lock}`;

/** Every scored T-spin, exactly as the matcher scores it: inside the prefix, the reconstruction agreeing
 *  on a non-empty set of rows. */
function scored(d: TechDigest) {
  const out: { i: number; rows: number[]; lk: TechDigest['locks'][number]; board: string[] }[] = [];
  for (const t of d.tspins) {
    if (t.i > d.v) continue;
    const lk = d.locks[t.i]!;
    const withT = t.board.map(s => [...s].map(x => x !== '.'));
    for (const q of lk.cells) withT[q.row]![q.col] = true;
    const rows: number[] = [];
    for (let r = 0; r < H; r++) if (withT[r]!.every(Boolean)) rows.push(r);
    const theirs = [...lk.clearedRows].sort((a, b) => a - b);
    if (rows.length !== theirs.length || !rows.every((x, k) => x === theirs[k]) || !rows.length) continue;
    out.push({ i: t.i, rows, lk, board: t.board });
  }
  return out;
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

/** A drawing (rows top first) in the matcher's frame: `filled` says which letters are filled. */
function asBoard(rows: string[], filled: (ch: string) => boolean) {
  return rows.map(r => [...r].map(ch => filled(ch) ? 'X' : '.').join(''));
}
const cellsOf = (slot: number[][]): Cell[] => slot.map(([row, col]) => ({ row: row!, col: col! }));
/** every flat or stood T placement on a board, resting or not: the window anchors on the cells alone */
function tPlacements(board: string[]) {
  const shapes = [[[0, 0], [0, 1], [0, 2], [1, 1]], [[0, 1], [1, 0], [1, 1], [1, 2]],
                  [[0, 0], [1, 0], [2, 0], [1, 1]], [[0, 1], [1, 0], [1, 1], [2, 1]]];
  const out: Cell[][] = [];
  for (const sh of shapes) for (let r = 0; r < board.length; r++) for (let c = 0; c < 10; c++) {
    const cells = sh.map(([dr, dc]) => ({ row: r + dr!, col: c + dc! }));
    if (cells.every(q => q.row < board.length && q.col < 10 && board[q.row]![q.col] === '.')) out.push(cells);
  }
  return out;
}
const fires = (board: string[], lock: Cell[]) =>
  prepare(TR, TR.variants[0]).filter(P => !!windowMatch(board, lock, P)).map(P => P.mirrored);
const same = (a: Cell[], b: Cell[]) => a.length === b.length && a.every(q => b.some(x => x.row === q.row && x.col === q.col));

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
  expect(n).toBe(14176);
  expect(art().check.reconstruction_disagreed).toBe(0);
});

test('the Python twin on the drawings: windowMatch fires where the gate records it, and nowhere else', () => {
  const hd = TR.cross_source.harddrop;
  const pre = (rows: string[]) => asBoard(rows, ch => ch !== '-' && ch !== 'U');
  // harddrop's Cut_copy drawings: once, at the drawn T, in the recorded hand; at no other placement
  expect(hd.drawings.length).toBe(5);
  expect(hd.drawings.filter((d: any) => d.section === 'Generic Structures').length).toBe(1);
  for (const d of hd.drawings) {
    const board = pre(d.rows), lock = cellsOf(d.slot);
    expect(fires(board, lock), `table ${d.table} board ${d.board}`).toEqual([d.mirrored]);
    for (const cs of tPlacements(board).filter(cs => !same(cs, lock)))
      expect(fires(board, cs), `table ${d.table} board ${d.board}`).toEqual([]);
  }
  // every other drawn T on the page: the window does not fire at it
  expect(hd.drawn_t_not_fired.length).toBe(16);
  for (const d of hd.drawn_t_not_fired)
    expect(fires(pre(d.rows), cellsOf(d.slot)), `table ${d.table} board ${d.board}`).toEqual([]);
  // its boards with no T drawn: the window fires at the recorded placement, in the recorded hand
  expect(hd.fires_without_slot.length).toBe(2);
  for (const d of hd.fires_without_slot)
    expect(fires(pre(d.rows), cellsOf(d.slot)), `table ${d.table} board ${d.board}`).toEqual([d.mirrored]);
  // the Cut Copy harddrop's BT_Cannon page draws, read out of the BT砲 transcription by (table, board)
  const bc = TR.cross_source.bt_cannon;
  const bt = JSON.parse(readFileSync(`${import.meta.dir}/${bc.file}`, 'utf8')).cross_source.harddrop;
  const btBoards = [...bt.drawings, ...bt.drawn_t_not_fired, ...bt.fires_without_slot];
  const e = btBoards.filter((x: any) => x.table === bc.table && x.board === bc.board);
  expect(e.length).toBe(1);
  expect(e[0].note.toLowerCase()).toContain('cut copy');
  const lockOf = (rows: string[]) => rows.flatMap((r, i) => [...r].flatMap((ch, c) => ch === 'U' ? [{ row: i, col: c }] : []));
  const fired = btBoards.filter((x: any) => {
    const board = pre(x.rows), lock = lockOf(x.rows);
    return lock.length ? fires(board, lock).length > 0 : tPlacements(board).some(cs => fires(board, cs).length);
  }).map((x: any) => `${x.table},${x.board}`);
  expect(fired).toEqual([`${bc.table},${bc.board}`]);
  expect(fires(pre(e[0].rows), lockOf(e[0].rows))).toEqual([bc.mirrored]);
  // this page's own drawings of the shape, each at its agreement slot, in its hand
  const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));
  const v = TR.variants[0];
  expect(v.agreement.map((a: any) => [a.board, a.mirrored]).sort())
    .toEqual([...v.fires_on.map((b: string) => [b, false]), ...v.fires_mirrored.map((b: string) => [b, true])].sort());
  for (const a of v.agreement) {
    const board = asBoard(byId.get(a.board).rows, ch => ch !== '-');
    expect(fires(board, cellsOf(a.t_cells)), a.board).toEqual([a.mirrored]);
  }
  // not expressed: the T-hole build with its Z left out (the page lets it go in after the first T-spin)
  const ne = v.not_expressed[0];
  expect([ne.board, ne.less]).toEqual(['hole.osz', 'z']);
  const less = asBoard(byId.get(ne.board).rows, ch => ch !== '-' && !ne.less.includes(ch));
  expect(tPlacements(less).filter(cs => fires(less, cs).length)).toEqual([]);
  // and on no routes board (the gate records none, with its reason)
  const got: string[] = [];
  const dir = `${import.meta.dir}`;
  for (const f of readdirSync(dir).filter(x => x.endsWith('-routes.json')).sort()) {
    for (const n of JSON.parse(readFileSync(`${dir}/${f}`, 'utf8')).nodes) {
      if (!n.rows) continue;
      const cells = lockOf(n.rows);
      if (cells.length !== 4) continue;
      if (fires(pre(n.rows), cells).length) got.push(`${f} ${n.id}`);
    }
  }
  expect(got).toEqual([]);
  expect(TR.cross_source.fires).toEqual([]);
  expect(TR.cross_source.also).toEqual([]);
  expect(TR.cross_source.routes_fire_none.length).toBeGreaterThan(0);
});

test('the transcription the artefact read is the committed one, and its window is the gated one', () => {
  const v = TR.variants[0];
  expect(v.window_basis).toBe('agreement');
  expect(v.window).toEqual({ rows: [2, 5], cols: [4, 9] });
  expect(v.t_cells).toEqual([[3, 6], [3, 7], [3, 8], [4, 7]]);
  expect(v.roof_cells).toEqual([[2, 4], [2, 8], [2, 9]]);
  expect(v.followup).toMatchObject({ spin: 'TSD', lines: 2, t_cells_pre_clear: [[2, 5], [2, 6], [2, 7], [5, 6]] });
  expect(TR.empty_letters).toBe('');
  expect(prepare(TR, v).map(P => P.followupKind)).toEqual(['full:2', 'full:2']);
});

test('named lists: every hit, every follow-up miss, the opener hits, garbage, the empty lists', () => {
  const L = art().lists;
  checkNamedList('cutcopy_hits', L.cutcopy_hits, CUTCOPY_HITS);
  checkNamedList('followup_not_fired', L.followup_not_fired, FOLLOWUP_NOT_FIRED);
  checkNamedList('garbage_in_window', L.garbage_in_window, GARBAGE_IN_WINDOW);
  checkNamedList('cutcopy_in_opener', L.cutcopy_in_opener, CUTCOPY_IN_OPENER);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, RECON_DROPPED_TSD);
  checkHitPositions(art(), SESSIONS, ROOT, [...CUTCOPY_HITS, ...FOLLOWUP_NOT_FIRED, ...GARBAGE_IN_WINDOW, ...CUTCOPY_IN_OPENER]);
  expect(art().hits.length).toBe(CUTCOPY_HITS.length);
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
    const rowsOff = n.row + (r0 - nr) < 0 || n.row + (r1 - nr) >= H;
    const drawnOff = rowsOff || n.col + (c0 - nc) < 0 || n.col + (c1 - nc) > 9;
    const mirrOff = rowsOff || n.col - (c1 - nc) < 0 || n.col - (c0 - nc) > 9;
    if (drawnOff || mirrOff) want.add(nameOf(d, s.i));
  }
  for (const x of L) expect(want.has(x), x).toBe(true);
  expect(new Set(L).size).toBe(L.length);
}, 600_000);

test('pinned: denominators, hits, follow-ups, controls', () => {
  const a = art(), v = a.variants.cutcopy;
  for (const u of ['pinglamb', 'yachi'] as const) {
    expect(a.denominators[u].TSD, u).toEqual(TSD_DENOM[u]);
    expect(v.hits_by_player[u], u).toEqual(HITS[u]);
    expect(v.followup_by_player[u], u).toEqual(FOLLOWUP[u]);
    expect(FOLLOWUP[u].fired + total(FOLLOWUP[u].not_fired)).toBe(HITS[u].all);
  }
  expect(v.controls).toEqual(CONTROLS);
  for (const k of ['no_must_empty', 'no_roof'] as const)
    for (const u of ['pinglamb', 'yachi'] as const) expect(v.controls.ablation[k][u]).toBeGreaterThanOrEqual(HITS[u].all);
});

test('STMB Cave, Double Dagger and BT砲 are not this: anchored on the same flat T, the windows clash in every pairing', () => {
  const norm = (P: ReturnType<typeof prepare>[number]) => {
    const r = Math.min(...P.T.map(x => x.r)), c = Math.min(...P.T.map(x => x.c));
    return { T: P.T.map(x => `${x.r - r},${x.c - c}`).sort().join(' '),
             cells: new Map(P.cells.map(x => [`${x.r - r},${x.c - c}`, x.v])) };
  };
  const mine = hitKeys();
  for (const other of [STMBCAVE, DOUBLEDAGGER, BTCANNON]) {
    const tr = JSON.parse(readFileSync(other.transcriptionPath, 'utf8'));
    for (const a of prepare(TR, TR.variants[0]).map(norm)) for (const b of prepare(tr, tr.variants[0]).map(norm)) {
      expect(a.T, other.key).toBe(b.T);
      const clash = [...a.cells].filter(([k, v]) => b.cells.has(k) && b.cells.get(k) !== v && v !== 'T');
      expect(clash.length, other.key).toBeGreaterThan(0);
    }
    const theirs = JSON.parse(readFileSync(other.artefactPath, 'utf8')).hits;
    const k = (h: any) => `${h.session}|${h.file}|${h.round_index0}|${h.player}|${h.lock}`;
    expect(theirs.filter((h: any) => mine.has(k(h))), other.key).toEqual([]);
  }
});

test('what discriminates: each part of the window alone, with the T anchored, against the headline', () => {
  const v = TR.variants[0];
  const [top] = v.t_cells[0]!;          // the T's row; the nub row is under it
  const parts: Record<keyof typeof PART_ONLY, (r: number) => boolean> = {
    above: r => r < top, cleared: r => r === top || r === top + 1, below: r => r > top + 1,
  };
  const hits = hitKeys();
  const got: Record<string, number> = {};
  for (const [name, keep] of Object.entries(parts)) {
    const preps = prepare(TR, v).map(P => ({ ...P, cells: P.cells.filter(x => x.v === 'T' || keep(x.r)) }));
    let n = 0, hitsIn = 0;
    for (const d of digests()) for (const s of scored(d)) {
      if (s.lk.spin !== 'full' || s.lk.cleared !== 2) continue;
      if (!preps.some(P => !!windowMatch(s.board, s.lk.cells, P))) continue;
      n++;
      if (hits.has(keyOf(d, s.i))) hitsIn++;
    }
    expect(hitsIn, name).toBe(art().hits.length);   // every hit passes each weaker predicate
    got[name] = n;
  }
  expect(got).toEqual(PART_ONLY);
  for (const n of Object.values(PART_ONLY)) expect(n).toBeGreaterThan(art().hits.length);
  // what the comment above claims: the row below cuts the cleared rows by at least ten times, the row above by less
  expect(PART_ONLY.cleared).toBeGreaterThanOrEqual(10 * PART_ONLY.below);
  expect(PART_ONLY.above).toBeLessThan(PART_ONLY.cleared);
  expect(PART_ONLY.cleared).toBeLessThan(10 * PART_ONLY.above);
  // the no_roof ablation (the window less the row above the T) is exactly the `below` part
  expect(total(art().variants.cutcopy.controls.ablation.no_roof)).toBe(PART_ONLY.below);
}, 600_000);

test('the follow-up row map is verified against the engine at every step it uses', () => {
  const c = art().check;
  expect(c.rowmap_unverified).toBe(30);
  expect(c.rowmap_steps).toBe(245899);
  expect(art().hits.every((h: any) => h.followup.reason !== 'rowmap_unverified')).toBe(true);
});

test('mutants: each rule turned off turns this red with its own symptom, or is named equivalent', () => {
  const base = serialise(run({}));
  const sum = (a: any, k: string) => total(Object.fromEntries(Object.entries(a.variants.cutcopy.hits_by_player).map(([u, x]: any) => [u, x[k]])));
  const fired = (a: any) => total(Object.fromEntries(Object.entries(a.variants.cutcopy.followup_by_player).map(([u, x]: any) => [u, x.fired])));
  const tsd = (a: any, k = 'all') => a.denominators.pinglamb.TSD[k] + a.denominators.yachi.TSD[k];
  const tss = (a: any) => a.denominators.pinglamb.TSS.all + a.denominators.yachi.TSS.all;
  const b = JSON.parse(base);
  const mut = (m: Mutants) => { const s = serialise(run(m)); expect(s, JSON.stringify(m)).not.toBe(base); return JSON.parse(s); };
  const k = (h: any) => `${h.session} ${h.file} ${h.round_index0} ${h.player} ${h.lock}`;

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

  // without the must-empty cells, or without the row above the T, the window is weaker and its hits are the
  // ablation's; the T's hand is still decided (no lock matches both)
  a = mut({ noMustEmpty: true });
  expect(sum(a, 'all')).toBe(total(b.variants.cutcopy.controls.ablation.no_must_empty));
  a = mut({ noRoof: true });
  expect(sum(a, 'all')).toBe(total(b.variants.cutcopy.controls.ablation.no_roof));
  expect(sum(a, 'all')).toBe(PART_ONLY.below);

  a = mut({ tOverlap: true });
  expect(sum(a, 'all')).toBe(total(b.variants.cutcopy.controls.ablation.t_overlap));

  a = mut({ rowAnchorOff1: true });
  expect(sum(a, 'all')).toBe(0);

  // garbage read as EMPTY: exactly the hits with garbage in their window are lost
  a = mut({ garbageEmpty: true });
  expect(a.hits.map(k)).toEqual(b.hits.filter((h: any) => !h.garbage_in_window).map(k));

  a = mut({ followupUnmirrored: true });
  expect(a.hits.map(k)).toEqual(b.hits.map(k));
  a.hits.forEach((h: any, i: number) => { if (!h.mirrored) expect(h.followup).toEqual(b.hits[i].followup); });
  expect(a.hits.filter((h: any) => h.mirrored && h.followup.fired).length).toBe(0);
  expect(b.hits.filter((h: any) => h.mirrored && h.followup.fired).length).toBeGreaterThan(0);

  a = mut({ openerLt: true });
  expect(tsd(a, 'in_opener')).toBeLessThan(tsd(b, 'in_opener'));
  expect(tsd(a)).toBe(tsd(b));

  // no row map: the hit's own clear lies BETWEEN the slot's arms and its nub, so the slot is never joined and
  // no follow-up fires; the hits are the same
  a = mut({ followupNoRowmap: true });
  expect(a.hits.map(k)).toEqual(b.hits.map(k));
  expect(fired(a)).toBe(0);
  expect(fired(b)).toBeGreaterThan(0);

  a = mut({ followupAnyT: true });
  expect(fired(a)).toBeGreaterThan(fired(b));

  for (const [m] of Object.entries(EQUIVALENT))
    expect(serialise(run({ [m]: true } as Mutants)), m).toBe(base);
}, 900_000);

/** The page's own TSD → TSD, as a two-lock digest: the board `basic.spin` draws (its T the lock, every other
 *  drawn cell filled), the TSD's clear, then the T into the slot `second.spin` draws. */
function pageDigest(mirrored: boolean, secondSpin = 'full'): TechDigest {
  const node = (id: string) => TR.nodes.find((n: any) => n.id === id).rows as string[];
  const flip = (row: string) => mirrored ? [...row].reverse().join('') : row;
  const pad = (rows: string[]) => [...Array(H - rows.length).fill('.'.repeat(10)), ...rows.map(flip)];
  const read = (rows: string[]) => pad(rows.map(r => [...r].map(ch => ch === '-' || ch === 'T' ? '.' : 'S').join('')));
  const tCells = (rows: string[]): Cell[] => pad(rows).flatMap((r, row) => [...r].flatMap((ch, col) => ch === 'T' ? [{ row, col }] : []));
  const place = (board: string[], cells: Cell[]) => {
    const g = board.map(r => [...r]);
    for (const q of cells) { expect(g[q.row]![q.col]).toBe('.'); g[q.row]![q.col] = 'T'; }
    const full = g.flatMap((r, i) => r.every(x => x !== '.') ? [i] : []);
    const kept = g.filter((_, i) => !full.includes(i)).map(r => r.join(''));
    return { full, after: [...Array(full.length).fill('.'.repeat(10)), ...kept] };
  };
  const b0 = read(node('basic.spin')), t0 = tCells(node('basic.spin'));
  const s0 = place(b0, t0);
  // the board the TSD leaves is the derived after board, letter for letter in occupancy
  expect(s0.after).toEqual(read(node('basic.after')));
  const t1 = tCells(node('second.spin'));
  const s1 = place(s0.after, t1);
  expect([s0.full.length, s1.full.length]).toEqual([2, 2]);
  const lock = (cells: Cell[], spin: string, rows: number[]) =>
    ({ piece: 'T', spin, cleared: rows.length, cells, clearedRows: rows, garbage: 0, mapOk: true });
  return { session: 'page', file: 'cutcopy.php', round: 0, match: 1, user: 'page', v: 1,
           locks: [lock(t0, 'full', s0.full), lock(t1, secondSpin, s1.full)],
           tspins: [{ i: 0, board: b0 }, { i: 1, board: s0.after }] };
}

test('the follow-up search on the page\'s own TSD → TSD: fires as drawn and mirrored, and each follow-up mutant breaks it', () => {
  const fu = (mirrored: boolean, m: Mutants = {}, spin = 'full') => {
    const c = classify(CUTCOPY, TR, [pageDigest(mirrored, spin)], m);
    expect(c.hits.length).toBe(1);
    expect(c.hits[0]!.mirrored).toBe(mirrored);
    return c.hits[0]!.followup;
  };
  for (const m of [false, true]) {
    expect(fu(m)).toEqual({ lock: 1, fired: true, reason: null });
    // no row map: the TSD's two cleared rows split the slot, so it is never joined
    expect(fu(m, { followupNoRowmap: true }).fired).toBe(false);
    // a T in the slot that is not a full TSD: refused, and fired by a follow-up that accepts any T
    expect(fu(m, {}, 'mini')).toEqual({ lock: 1, fired: false, reason: 't_in_slot_not_tsd' });
    expect(fu(m, { followupAnyT: true }, 'mini').fired).toBe(true);
  }
  // the slot carried in the drawn columns on a mirrored hit: the mirrored second TSD lands elsewhere
  expect(fu(false, { followupUnmirrored: true }).fired).toBe(true);
  expect(fu(true, { followupUnmirrored: true })).toEqual({ lock: 1, fired: false, reason: 'next_t_elsewhere' });
});

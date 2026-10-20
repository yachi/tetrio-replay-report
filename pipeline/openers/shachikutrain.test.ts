/**
 * The 社畜トレイン (Shachiku Train) technique artefact (`analysis/shachikutrain-facts.json`, from
 * `pipeline/sim/emit-technique-facts.ts --technique shachikutrain`; the rules are the shared `technique-facts.ts`, the
 * profile `technique-profile-shachikutrain.ts`, the shape the gated `pipeline/openers/shachikutrain-technique.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE THIRD COPY OF THE T-SPIN LOOP, held to `emit-opener-facts.ts`'s own count in every session and for
 *      every player (`donation.check`, `donation.players`), as `stsd.test.ts` holds it.
 *   3. THE PYTHON TWIN, on the drawings: `windowMatch` (TS) fires on each of harddrop's Shachiku_Train drawings the
 *      gate records — once, at its drawn T, in its recorded hand, and at no other T placement; at no drawn T the gate
 *      names as a miss; on this page's own drawings at their agreement slots; and on exactly one routes board, the
 *      same author's stick spin 2.sd (`cross_source.also`).
 *   4. STMB CAVE, MEASURED: on harddrop's STMB_Cave comparison (its table 17) this window fires on the Shachiku Train
 *      board only and STMB Cave's (`stmbcave-technique.json`, by the same TS predicate) on its own variation only.
 *   5. STMB CAVE, ダブルダガー, BT砲 AND 千鳥格子 ARE NOT THIS: all five lay the T flat, nub down; anchored on the same T
 *      this window clashes with each of theirs on a cell in every pairing of hands (re-derived from the
 *      transcriptions), so no lock is a hit of two of them, and none is. Against STMB Cave in the same hand the clash
 *      is exactly two cells, the cell under the nub and its neighbour under one arm (the transcription's `clash`),
 *      which harddrop's 「same shape and steps」 does not mention.
 *   6. WHAT DISCRIMINATES: measured per window part, with the T anchored (the row above the T, the cleared rows,
 *      the row under them), against the headline: no single part gives it. The cleared rows are entailed by the
 *      clear and do no work; the row above and the row below each cut them down (the row below by at least ten
 *      times, the row above by less — both asserted), so those two are what discriminate.
 *   7. NAMED lists, not bounds; pinned per-player figures; mutants, each with its asserted symptom (the equivalent
 *      ones named, measured, asserted to STAY byte-identical).
 *   8. THE FOLLOW-UP on the page's own drawings: the TSD into `basic.spin`'s slot, the page's Z, then the T into the
 *      slot `basic.second` draws, as a three-lock digest, as drawn and mirrored — it fires, and the follow-up mutants
 *      break it there as they do on the corpus.
 *
 * window_off_board is not listed entry by entry: it is every flat, nub-down T at a TSD whose window leaves the
 * board before the matcher found a mismatch (the window reaches one column past one end of the T and two past the
 * other), well over a thousand of them. It is pinned per player as a count, and every entry is checked to be such a
 * T with its window off the board in at least one hand and not a hit (STMB Cave's treatment, for the same reason).
 *
 * Run: bun test pipeline/openers/shachikutrain.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { build, classify, serialise, digestCorpus, prepare, windowMatch, type Mutants, type TechDigest, type Cell }
  from '../sim/technique-facts.ts';
import { SHACHIKUTRAIN } from '../sim/technique-profile-shachikutrain.ts';
import { STMBCAVE } from '../sim/technique-profile-stmbcave.ts';
import { DOUBLEDAGGER } from '../sim/technique-profile-doubledagger.ts';
import { BTCANNON } from '../sim/technique-profile-btcannon.ts';
import { CUTCOPY } from '../sim/technique-profile-cutcopy.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';
import { checkNamedList, checkScoredAgainstOpenerFacts, checkHitPositions } from './technique-facts-checks.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20']);
const ART_PATH = `${import.meta.dir}/../../analysis/shachikutrain-facts.json`;
const TR = JSON.parse(readFileSync(SHACHIKUTRAIN.transcriptionPath, 'utf8'));
const STMB_TR = JSON.parse(readFileSync(STMBCAVE.transcriptionPath, 'utf8'));
const H = 40;

/** Every hit: the flat T into the page's window, as drawn (the roof over the T's left end) or mirrored. */
const SHACHIKUTRAIN_HITS: string[] = [
  "2026-07-22 m3r1 yachi lock 41 (mirrored)", "2026-07-22 m4r4 yachi lock 110 (mirrored)",
  "2026-07-22 m9r2 yachi lock 24", "2026-07-22 m10r8 yachi lock 29", "2026-07-22 m10r8 yachi lock 31",
  "2026-07-22 m10r9 yachi lock 24 (mirrored)", "2026-07-24 m2r3 pinglamb lock 61 (mirrored)",
  "2026-07-24 m3r7 pinglamb lock 82", "2026-07-24 m3r8 pinglamb lock 24", "2026-07-24 m4r1 pinglamb lock 45",
  "2026-07-24 m4r3 yachi lock 24 (mirrored)", "2026-07-24 m7r2 yachi lock 25", "2026-07-28 m1r3 yachi lock 48",
  "2026-07-28 m2r8 yachi lock 72", "2026-07-28 m5r2 yachi lock 24 (mirrored)", "2026-07-28 m7r2 yachi lock 28",
  "2026-08-01 m3r5 pinglamb lock 40 (mirrored)", "2026-08-01 m4r1 pinglamb lock 186 (mirrored)",
  "2026-08-01 m4r2 yachi lock 84", "2026-08-01 m6r1 yachi lock 80", "2026-08-01 m6r1 yachi lock 117",
  "2026-08-01 m7r1 yachi lock 170 (mirrored)", "2026-08-09 m5r5 pinglamb lock 70", "2026-08-09 m6r3 yachi lock 170",
  "2026-08-14 m1r4 pinglamb lock 40 (mirrored)", "2026-08-14 m3r4 yachi lock 123",
  "2026-08-14 m5r8 pinglamb lock 134 (mirrored)", "2026-08-14 m7r8 pinglamb lock 41",
  "2026-08-14 m9r4 yachi lock 105 (mirrored)", "2026-08-14 m9r5 yachi lock 23", "2026-08-19 m2r3 yachi lock 98",
  "2026-08-19 m3r4 yachi lock 118 (mirrored)", "2026-08-19 m7r1 yachi lock 88 (mirrored)",
  "2026-08-19 m7r5 yachi lock 25 (mirrored)", "2026-08-19 m10r2 pinglamb lock 66 (mirrored)",
  "2026-08-19 m10r5 yachi lock 16 (mirrored)", "2026-08-25 m1r6 pinglamb lock 21",
  "2026-08-25 m1r6 yachi lock 27 (mirrored)", "2026-08-25 m1r9 pinglamb lock 43",
  "2026-08-25 m3r3 pinglamb lock 27 (mirrored)", "2026-08-25 m3r7 yachi lock 27",
  "2026-08-25 m5r8 yachi lock 56 (mirrored)", "2026-08-25 m6r6 pinglamb lock 27 (mirrored)",
  "2026-08-25 m7r1 pinglamb lock 28 (mirrored)", "2026-09-03 m3r4 pinglamb lock 222 (mirrored)",
  "2026-09-03 m4r2 pinglamb lock 77 (mirrored)", "2026-09-03 m5r3 yachi lock 20 (mirrored)",
  "2026-09-03 m5r4 pinglamb lock 23", "2026-09-10 m6r3 pinglamb lock 86 (mirrored)", "2026-09-10 m6r3 yachi lock 22",
  "2026-09-11 m1r4 pinglamb lock 27", "2026-09-11 m1r8 pinglamb lock 107 (mirrored)",
  "2026-09-11 m3r1 pinglamb lock 27 (mirrored)", "2026-09-11 m6r6 pinglamb lock 219",
  "2026-09-17 m1r8 yachi lock 75", "2026-09-18 m5r5 pinglamb lock 27 (mirrored)", "2026-09-18 m7r6 yachi lock 58",
  "2026-09-18 m18r5 pinglamb lock 55", "2026-09-19 m6r5 yachi lock 72 (mirrored)", "2026-09-19 m7r4 yachi lock 148",
  "2026-09-19 m7r5 pinglamb lock 156 (mirrored)", "2026-09-19 m8r2 yachi lock 38 (mirrored)",
  "2026-09-19 m8r7 yachi lock 97 (mirrored)", "2026-09-19 m11r2 pinglamb lock 40",
  "2026-09-19 m11r4 yachi lock 68 (mirrored)", "2026-09-19 m12r3 pinglamb lock 14 (mirrored)",
  "2026-09-19 m12r4 yachi lock 51", "2026-09-19 m15r7 pinglamb lock 27 (mirrored)",
  "2026-09-19 m17r1 yachi lock 55 (mirrored)", "2026-10-03 m4r8 yachi lock 108", "2026-10-03 m7r7 yachi lock 172",
  "2026-10-03 m12r1 yachi lock 45 (mirrored)", "2026-10-03 m13r5 yachi lock 104", "2026-10-09 m2r5 yachi lock 70",
  "2026-10-09 m3r6 pinglamb lock 49 (mirrored)", "2026-10-09 m4r2 yachi lock 26 (mirrored)",
  "2026-10-09 m6r1 yachi lock 53", "2026-10-09 m6r8 pinglamb lock 26 (mirrored)", "2026-10-09 m7r2 yachi lock 109",
  "2026-10-09 m7r6 yachi lock 11", "2026-10-09 m7r8 yachi lock 56", "2026-10-12 m1r3 yachi lock 81 (mirrored)",
  "2026-10-12 m3r1 yachi lock 40", "2026-10-12 m4r2 pinglamb lock 52 (mirrored)", "2026-10-12 m6r7 pinglamb lock 46",
  "2026-10-12 m7r2 yachi lock 27", "2026-10-20 m1r8 yachi lock 81", "2026-10-20 m2r1 pinglamb lock 54",
  "2026-10-20 m2r6 yachi lock 27",
];
const FOLLOWUP_NOT_FIRED: string[] = [
  "2026-07-22 m3r1 yachi lock 41 (t_in_slot_not_tsd at lock 46)",
  "2026-07-22 m4r4 yachi lock 110 (slot_filled_before_t at lock 111)",
  "2026-07-22 m10r8 yachi lock 31 (slot_filled_before_t at lock 32)",
  "2026-07-24 m2r3 pinglamb lock 61 (slot_filled_before_t at lock 62)",
  "2026-07-24 m4r3 yachi lock 24 (next_t_elsewhere at lock 33)",
  "2026-07-24 m7r2 yachi lock 25 (slot_filled_before_t at lock 26)", "2026-07-28 m1r3 yachi lock 48 (round_ended)",
  "2026-07-28 m2r8 yachi lock 72 (slot_filled_before_t at lock 74)",
  "2026-07-28 m7r2 yachi lock 28 (slot_filled_before_t at lock 30)",
  "2026-08-01 m3r5 pinglamb lock 40 (next_t_elsewhere at lock 45)",
  "2026-08-01 m4r1 pinglamb lock 186 (slot_filled_before_t at lock 187)",
  "2026-08-01 m4r2 yachi lock 84 (slot_filled_before_t at lock 86)",
  "2026-08-01 m6r1 yachi lock 80 (slot_filled_before_t at lock 81)",
  "2026-08-01 m7r1 yachi lock 170 (slot_filled_before_t at lock 171)",
  "2026-08-09 m5r5 pinglamb lock 70 (slot_filled_before_t at lock 71)",
  "2026-08-14 m3r4 yachi lock 123 (t_in_slot_not_tsd at lock 124)",
  "2026-08-19 m2r3 yachi lock 98 (next_t_elsewhere at lock 100)",
  "2026-08-19 m7r1 yachi lock 88 (next_t_elsewhere at lock 94)",
  "2026-08-19 m7r5 yachi lock 25 (slot_filled_before_t at lock 26)",
  "2026-08-19 m10r2 pinglamb lock 66 (slot_filled_before_t at lock 68)",
  "2026-08-19 m10r5 yachi lock 16 (round_ended)",
  "2026-08-25 m1r9 pinglamb lock 43 (slot_filled_before_t at lock 44)",
  "2026-08-25 m3r7 yachi lock 27 (slot_filled_before_t at lock 28)",
  "2026-08-25 m5r8 yachi lock 56 (slot_filled_before_t at lock 57)",
  "2026-09-03 m4r2 pinglamb lock 77 (slot_filled_before_t at lock 78)",
  "2026-09-10 m6r3 pinglamb lock 86 (slot_filled_before_t at lock 87)",
  "2026-09-10 m6r3 yachi lock 22 (slot_filled_before_t at lock 24)",
  "2026-09-11 m1r4 pinglamb lock 27 (slot_filled_before_t at lock 30)",
  "2026-09-11 m1r8 pinglamb lock 107 (slot_filled_before_t at lock 109)",
  "2026-09-11 m3r1 pinglamb lock 27 (slot_filled_before_t at lock 28)",
  "2026-09-18 m5r5 pinglamb lock 27 (slot_filled_before_t at lock 31)",
  "2026-09-18 m7r6 yachi lock 58 (slot_filled_before_t at lock 60)",
  "2026-09-18 m18r5 pinglamb lock 55 (slot_filled_before_t at lock 58)",
  "2026-09-19 m6r5 yachi lock 72 (slot_filled_before_t at lock 77)",
  "2026-09-19 m7r4 yachi lock 148 (slot_filled_before_t at lock 149)",
  "2026-09-19 m7r5 pinglamb lock 156 (t_in_slot_not_tsd at lock 157)",
  "2026-09-19 m8r2 yachi lock 38 (next_t_elsewhere at lock 40)",
  "2026-09-19 m11r4 yachi lock 68 (slot_filled_before_t at lock 69)",
  "2026-09-19 m12r3 pinglamb lock 14 (slot_filled_before_t at lock 16)",
  "2026-09-19 m12r4 yachi lock 51 (next_t_elsewhere at lock 62)",
  "2026-09-19 m15r7 pinglamb lock 27 (slot_filled_before_t at lock 28)",
  "2026-10-03 m7r7 yachi lock 172 (t_in_slot_not_tsd at lock 174)",
  "2026-10-03 m12r1 yachi lock 45 (slot_filled_before_t at lock 49)",
  "2026-10-09 m2r5 yachi lock 70 (slot_filled_before_t at lock 71)",
  "2026-10-09 m6r8 pinglamb lock 26 (t_in_slot_not_tsd at lock 28)",
  "2026-10-09 m7r6 yachi lock 11 (slot_filled_before_t at lock 12)",
  "2026-10-12 m1r3 yachi lock 81 (slot_filled_before_t at lock 82)",
  "2026-10-12 m3r1 yachi lock 40 (slot_filled_before_t at lock 42)",
  "2026-10-12 m4r2 pinglamb lock 52 (slot_filled_before_t at lock 53)",
  "2026-10-20 m2r1 pinglamb lock 54 (slot_filled_before_t at lock 57)",
];
const GARBAGE_IN_WINDOW: string[] = [
  "2026-07-22 m4r4 yachi lock 110", "2026-07-22 m9r2 yachi lock 24", "2026-07-22 m10r8 yachi lock 31",
  "2026-07-24 m2r3 pinglamb lock 61", "2026-07-24 m3r7 pinglamb lock 82", "2026-07-24 m3r8 pinglamb lock 24",
  "2026-07-24 m4r1 pinglamb lock 45", "2026-07-28 m1r3 yachi lock 48", "2026-07-28 m2r8 yachi lock 72",
  "2026-08-01 m3r5 pinglamb lock 40", "2026-08-01 m4r1 pinglamb lock 186", "2026-08-01 m6r1 yachi lock 117",
  "2026-08-01 m7r1 yachi lock 170", "2026-08-09 m6r3 yachi lock 170", "2026-08-14 m1r4 pinglamb lock 40",
  "2026-08-14 m3r4 yachi lock 123", "2026-08-14 m5r8 pinglamb lock 134", "2026-08-14 m7r8 pinglamb lock 41",
  "2026-08-14 m9r4 yachi lock 105", "2026-08-19 m2r3 yachi lock 98", "2026-08-19 m3r4 yachi lock 118",
  "2026-08-19 m7r1 yachi lock 88", "2026-08-19 m10r2 pinglamb lock 66", "2026-08-19 m10r5 yachi lock 16",
  "2026-08-25 m1r6 pinglamb lock 21", "2026-08-25 m1r6 yachi lock 27", "2026-08-25 m1r9 pinglamb lock 43",
  "2026-09-03 m3r4 pinglamb lock 222", "2026-09-03 m4r2 pinglamb lock 77", "2026-09-03 m5r4 pinglamb lock 23",
  "2026-09-10 m6r3 pinglamb lock 86", "2026-09-11 m1r8 pinglamb lock 107", "2026-09-11 m6r6 pinglamb lock 219",
  "2026-09-18 m7r6 yachi lock 58", "2026-09-18 m18r5 pinglamb lock 55", "2026-09-19 m6r5 yachi lock 72",
  "2026-09-19 m7r4 yachi lock 148", "2026-09-19 m7r5 pinglamb lock 156", "2026-09-19 m8r7 yachi lock 97",
  "2026-09-19 m11r2 pinglamb lock 40", "2026-09-19 m12r3 pinglamb lock 14", "2026-09-19 m12r4 yachi lock 51",
  "2026-09-19 m17r1 yachi lock 55", "2026-10-03 m7r7 yachi lock 172", "2026-10-03 m12r1 yachi lock 45",
  "2026-10-09 m2r5 yachi lock 70", "2026-10-09 m3r6 pinglamb lock 49", "2026-10-09 m6r1 yachi lock 53",
  "2026-10-09 m6r8 pinglamb lock 26", "2026-10-09 m7r6 yachi lock 11", "2026-10-12 m4r2 pinglamb lock 52",
  "2026-10-12 m6r7 pinglamb lock 46", "2026-10-20 m2r1 pinglamb lock 54",
];
const SHACHIKUTRAIN_IN_OPENER: string[] = [
  "2026-08-19 m10r5 yachi lock 16", "2026-08-25 m1r6 pinglamb lock 21", "2026-09-03 m5r3 yachi lock 20",
  "2026-09-19 m12r3 pinglamb lock 14", "2026-10-09 m7r6 yachi lock 11",
];
const RECON_DROPPED_TSD: string[] = [];
/** window_off_board, per player: a count with a property check, not a list (see the header). */
const WINDOW_OFF_BOARD = { pinglamb: 924, yachi: 788 };

/** Per player: the opportunity (scored full TSDs), split at the 0-based opener window. */
const TSD_DENOM = { pinglamb: { all: 5421, in_opener: 1061, mid_game: 4360 },
                    yachi: { all: 4891, in_opener: 1268, mid_game: 3623 } };
/** Per player: hits, their split, the mirrored ones, the ones with garbage in the window, the follow-ups. */
const HITS = { pinglamb: { all: 35, in_opener: 2, mid_game: 33, mirrored: 21, garbage_in_window: 27 },
               yachi: { all: 54, in_opener: 3, mid_game: 51, mirrored: 22, garbage_in_window: 26 } };
const FOLLOWUP = {
  pinglamb: { fired: 16, not_fired: { next_t_elsewhere: 1, slot_filled_before_t: 16, t_in_slot_not_tsd: 2 } },
  yachi: { fired: 23, not_fired: { next_t_elsewhere: 5, round_ended: 2, slot_filled_before_t: 21, t_in_slot_not_tsd: 3 } },
};
/** The controls (the same window at other spins; the ablations; the orientation baseline). */
const CONTROLS = {
  under: { TSS: { pinglamb: 4, yachi: 2 }, TST: { pinglamb: 0, yachi: 0 },
           mini_TSS: { pinglamb: 0, yachi: 0 }, mini_TSD: { pinglamb: 0, yachi: 0 } },
  ablation: { no_must_empty: { pinglamb: 892, yachi: 759 }, no_roof: { pinglamb: 329, yachi: 378 },
              t_overlap: { pinglamb: 59, yachi: 68 } },
  orientation_baseline: { pinglamb: 46, yachi: 64 },
};
/** What discriminates, measured: full TSDs (not only hits) whose anchored T meets ONE part of the window — the
 *  row above the T (the roof over its near end and the cell beyond it, the cell over its middle and the second
 *  slot's arms open), the two rows the TSD clears, or the row under them (the cell under the nub and the S's foot,
 *  the second slot's open nub, the L's foot). The cleared rows are entailed by the
 *  clear and admit every flat, nub-down full TSD whose window is on the board, so they do no work. The row above and
 *  the row below each cut that down — the row below by at least ten times, the row above by less (both asserted
 *  where PART_ONLY is checked) — and neither alone reaches the headline, so those two are what discriminate. The
 *  `no_roof` ablation (the window less the row above the T) is exactly `below`. */
const PART_ONLY = { above: 1203, cleared: 9003, below: 707 };

/** Measured byte-identical on this corpus, each for its reason; asserted to STAY identical. */
const EQUIVALENT: Record<string, string> = {
  noRecon: 'the corpus has no reconstruction disagreement (check.reconstruction_disagreed is 0)',
};

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
let ART: any = null;
const art = () => (ART ??= JSON.parse(readFileSync(ART_PATH, 'utf8')));
const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);
const run = (m: Mutants) => build(SHACHIKUTRAIN, m, digests());
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
const firesWith = (tr: any) => (board: string[], lock: Cell[]) =>
  prepare(tr, tr.variants[0]).filter(P => !!windowMatch(board, lock, P)).map(P => P.mirrored);
const fires = firesWith(TR);
const same = (a: Cell[], b: Cell[]) => a.length === b.length && a.every(q => b.some(x => x.row === q.row && x.col === q.col));
const pre = (rows: string[]) => asBoard(rows, ch => ch !== '-' && ch !== 'U');
const lockOf = (rows: string[]) => rows.flatMap((r, i) => [...r].flatMap((ch, c) => ch === 'U' ? [{ row: i, col: c }] : []));

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
  expect(n).toBe(14538);
  expect(art().check.reconstruction_disagreed).toBe(0);
});

test('the Python twin on the drawings: windowMatch fires where the gate records it, and nowhere else', () => {
  const hd = TR.cross_source.harddrop;
  // harddrop's Shachiku_Train drawings: once, at the drawn T, in the recorded hand; at no other placement
  expect(hd.drawings.length).toBe(22);
  expect(hd.drawings.filter((d: any) => d.section === 'Generic Structure').length).toBe(1);
  for (const d of hd.drawings) {
    const board = pre(d.rows), lock = cellsOf(d.slot);
    expect(fires(board, lock), `table ${d.table} board ${d.board}`).toEqual([d.mirrored]);
    for (const cs of tPlacements(board).filter(cs => !same(cs, lock)))
      expect(fires(board, cs), `table ${d.table} board ${d.board}`).toEqual([]);
  }
  // every other drawn T on the page: the window does not fire at it
  expect(hd.drawn_t_not_fired.length).toBe(11);
  for (const d of hd.drawn_t_not_fired)
    expect(fires(pre(d.rows), cellsOf(d.slot)), `table ${d.table} board ${d.board}`).toEqual([]);
  expect(hd.fires_without_slot).toEqual([]);
  // this page's own drawings of the shape, each at its agreement slot, in its hand, and nowhere else on it
  const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));
  const v = TR.variants[0];
  expect(v.agreement.map((a: any) => [a.board, a.mirrored]).sort())
    .toEqual([...v.fires_on.map((b: string) => [b, false]), ...v.fires_mirrored.map((b: string) => [b, true])].sort());
  for (const a of v.agreement) {
    const board = asBoard(byId.get(a.board).rows, ch => ch !== '-');
    expect(fires(board, cellsOf(a.t_cells)), a.board).toEqual([a.mirrored]);
    for (const cs of tPlacements(board).filter(cs => !same(cs, cellsOf(a.t_cells))))
      expect(fires(board, cs), a.board).toEqual([]);
  }
  // and on exactly one routes board: the same author's stick spin 2.sd, as drawn (the gate's `also`)
  const got: string[] = [];
  const dir = `${import.meta.dir}`;
  for (const f of readdirSync(dir).filter(x => x.endsWith('-routes.json')).sort()) {
    for (const n of JSON.parse(readFileSync(`${dir}/${f}`, 'utf8')).nodes) {
      if (!n.rows) continue;
      const cells = lockOf(n.rows);
      if (cells.length !== 4) continue;
      const h = fires(pre(n.rows), cells);
      if (h.length) got.push(`${f} ${n.id} ${h.join()}`);
    }
  }
  expect(got).toEqual(['stickspin-routes.json 2.sd false']);
  expect(TR.cross_source.fires).toEqual([]);
  expect(TR.cross_source.also.map((e: any) => `${e.file} ${e.node} ${e.mirrored}`)).toEqual(got);
  expect(TR.cross_source.routes_fire_none.length).toBeGreaterThan(0);
});

test('STMB Cave, measured on harddrop\'s comparison: each window fires on its own base only', () => {
  const sc = TR.cross_source.stmb_cave;
  const stmb = firesWith(STMB_TR);
  const got = sc.boards.map((b: any) => ({ shachikutrain: fires(pre(b.rows), cellsOf(b.slot)),
                                           stmbcave: stmb(pre(b.rows), cellsOf(b.slot)) }));
  expect(got).toEqual(sc.boards.map((b: any) => b.fires));
  expect(got).toEqual([{ shachikutrain: [], stmbcave: [false] }, { shachikutrain: [false], stmbcave: [] },
                       { shachikutrain: [], stmbcave: [] }]);
  // the two bases differ in the row under the T, and the cell under the nub is filled on one, empty on the other
  const [o, j] = [sc.boards[0], sc.boards[1]];
  const diff = o.rows.flatMap((r: string, i: number) => [...r].flatMap((ch, c) =>
    (ch === '-') !== (j.rows[i][c] === '-') ? [[i, c]] : []));
  const [nr, nc] = o.slot.reduce((a: number[], b: number[]) => (b[0]! > a[0]! ? b : a));
  expect(diff.some(([r, c]: number[]) => r === nr + 1 && c === nc)).toBe(true);
  expect(diff.every(([r]: number[]) => r === nr + 1)).toBe(true);
});

test('the transcription the artefact read is the committed one, and its window is the gated one', () => {
  const v = TR.variants[0];
  expect(v.window_basis).toBe('agreement');
  expect(v.window).toEqual({ rows: [1, 4], cols: [4, 9] });
  expect(v.t_cells).toEqual([[2, 5], [2, 6], [2, 7], [3, 6]]);
  expect(v.roof_cells).toEqual([[1, 4], [1, 5]]);
  expect(v.followup).toMatchObject({ spin: 'TSD', lines: 2, t_cells_pre_clear: [[1, 7], [1, 8], [1, 9], [4, 8]] });
  expect(TR.empty_letters).toBe('');
  expect(prepare(TR, v).map(P => P.followupKind)).toEqual(['full:2', 'full:2']);
});

test('named lists: every hit, every follow-up miss, the opener hits, garbage, the empty lists', () => {
  const L = art().lists;
  checkNamedList('shachikutrain_hits', L.shachikutrain_hits, SHACHIKUTRAIN_HITS);
  checkNamedList('followup_not_fired', L.followup_not_fired, FOLLOWUP_NOT_FIRED);
  checkNamedList('garbage_in_window', L.garbage_in_window, GARBAGE_IN_WINDOW);
  checkNamedList('shachikutrain_in_opener', L.shachikutrain_in_opener, SHACHIKUTRAIN_IN_OPENER);
  checkNamedList('recon_dropped_tsd', L.recon_dropped_tsd, RECON_DROPPED_TSD);
  checkHitPositions(art(), SESSIONS, ROOT,
                    [...SHACHIKUTRAIN_HITS, ...FOLLOWUP_NOT_FIRED, ...GARBAGE_IN_WINDOW, ...SHACHIKUTRAIN_IN_OPENER]);
  expect(art().hits.length).toBe(SHACHIKUTRAIN_HITS.length);
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
  const a = art(), v = a.variants.shachikutrain;
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

test('STMB Cave, Double Dagger, BT砲 and Cut Copy are not this: anchored on the same flat T, the windows clash in every pairing', () => {
  const norm = (P: ReturnType<typeof prepare>[number]) => {
    const r = Math.min(...P.T.map(x => x.r)), c = Math.min(...P.T.map(x => x.c));
    return { mirrored: P.mirrored, T: P.T.map(x => `${x.r - r},${x.c - c}`).sort().join(' '),
             cells: new Map(P.cells.map(x => [`${x.r - r},${x.c - c}`, x.v])) };
  };
  const mine = hitKeys();
  for (const other of [STMBCAVE, DOUBLEDAGGER, BTCANNON, CUTCOPY]) {
    const tr = JSON.parse(readFileSync(other.transcriptionPath, 'utf8'));
    // every variant of 千鳥格子 (both its windows lay the T flat, nub down; `uncut` included), the others' first
    for (const ov of (other === CUTCOPY ? tr.variants : [tr.variants[0]]))
    for (const a of prepare(TR, TR.variants[0]).map(norm)) for (const b of prepare(tr, ov).map(norm)) {
      expect(a.T, other.key).toBe(b.T);
      const clash = [...a.cells].filter(([k, v]) => b.cells.has(k) && b.cells.get(k) !== v && v !== 'T');
      expect(clash.length, other.key).toBeGreaterThan(0);
      // against STMB Cave in the same hand, the clashes are exactly the cell under the nub (`2,1` from the T's
      // top-left; the nub is `1,1`) and its neighbour under one arm — the transcription's `clash`, which the gate
      // also re-measures. Across hands the two windows are not the same shape at all (more cells clash).
      if (other.key === 'stmbcave' && a.mirrored === b.mirrored) {
        const want = TR.cross_source.stmb_cave.clash[a.mirrored ? 'mirrored' : 'as_drawn'].map(([r, c]: number[]) => `${r},${c}`);
        expect(clash.map(([k]) => k).sort(), other.key).toEqual([...want].sort());
        expect(want, other.key).toEqual(a.mirrored ? ['2,0', '2,1'] : ['2,1', '2,2']);
      }
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
  expect(total(art().variants.shachikutrain.controls.ablation.no_roof)).toBe(PART_ONLY.below);
}, 600_000);

test('the follow-up row map is verified against the engine at every step it uses', () => {
  const c = art().check;
  expect(c.rowmap_unverified).toBe(30);
  expect(c.rowmap_steps).toBe(252000);
  expect(art().hits.every((h: any) => h.followup.reason !== 'rowmap_unverified')).toBe(true);
});

test('mutants: each rule turned off turns this red with its own symptom, or is named equivalent', () => {
  const base = serialise(run({}));
  const sum = (a: any, k: string) => total(Object.fromEntries(Object.entries(a.variants.shachikutrain.hits_by_player).map(([u, x]: any) => [u, x[k]])));
  const fired = (a: any) => total(Object.fromEntries(Object.entries(a.variants.shachikutrain.followup_by_player).map(([u, x]: any) => [u, x.fired])));
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
  expect(sum(a, 'all')).toBe(total(b.variants.shachikutrain.controls.ablation.no_must_empty));
  a = mut({ noRoof: true });
  expect(sum(a, 'all')).toBe(total(b.variants.shachikutrain.controls.ablation.no_roof));
  expect(sum(a, 'all')).toBe(PART_ONLY.below);

  a = mut({ tOverlap: true });
  expect(sum(a, 'all')).toBe(total(b.variants.shachikutrain.controls.ablation.t_overlap));

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

/** The page's own TSD → Z → TSD, as a three-lock digest: the board `basic.spin` draws (its U the lock, every other
 *  drawn cell filled), the TSD's clear, the page's Z (the cells `basic.roofed` adds), then the T into the slot
 *  `basic.second` draws. */
function pageDigest(mirrored: boolean, secondSpin = 'full'): TechDigest {
  const node = (id: string) => TR.nodes.find((n: any) => n.id === id).rows as string[];
  const flip = (row: string) => mirrored ? [...row].reverse().join('') : row;
  const pad = (rows: string[]) => [...Array(H - rows.length).fill('.'.repeat(10)), ...rows.map(flip)];
  const read = (rows: string[], skip = '') => pad(rows.map(r => [...r].map(ch => ch === '-' || ch === 'U' || skip.includes(ch) ? '.' : 'S').join('')));
  const letter = (rows: string[], l: string): Cell[] => pad(rows).flatMap((r, row) => [...r].flatMap((ch, col) => ch === l ? [{ row, col }] : []));
  const place = (board: string[], cells: Cell[]) => {
    const g = board.map(r => [...r]);
    for (const q of cells) { expect(g[q.row]![q.col]).toBe('.'); g[q.row]![q.col] = 'T'; }
    const full = g.flatMap((r, i) => r.every(x => x !== '.') ? [i] : []);
    const kept = g.filter((_, i) => !full.includes(i)).map(r => r.join(''));
    return { full, after: [...Array(full.length).fill('.'.repeat(10)), ...kept] };
  };
  const b0 = read(node('basic.spin')), t0 = letter(node('basic.spin'), 'U');
  const s0 = place(b0, t0);
  // the board the TSD leaves is the derived board less the page's Z, letter for letter in occupancy
  expect(s0.after).toEqual(read(node('basic.roofed'), 'z'));
  const z = letter(node('basic.roofed'), 'z');
  const sz = place(s0.after, z);
  expect(sz.full).toEqual([]);
  const t1 = letter(node('basic.second'), 'U');
  const s1 = place(sz.after, t1);
  expect([s0.full.length, s1.full.length]).toEqual([2, 2]);
  const lock = (piece: string, cells: Cell[], spin: string, rows: number[]) =>
    ({ piece, spin, cleared: rows.length, cells, clearedRows: rows, garbage: 0, mapOk: true });
  return { session: 'page', file: 'shachikutrain.php', round: 0, match: 1, user: 'page', v: 2,
           locks: [lock('T', t0, 'full', s0.full), lock('Z', z, 'none', []), lock('T', t1, secondSpin, s1.full)],
           tspins: [{ i: 0, board: b0 }, { i: 2, board: sz.after }] };
}

test('the follow-up search on the page\'s own TSD → Z → TSD: fires as drawn and mirrored, and each follow-up mutant breaks it', () => {
  const fu = (mirrored: boolean, m: Mutants = {}, spin = 'full') => {
    const c = classify(SHACHIKUTRAIN, TR, [pageDigest(mirrored, spin)], m);
    expect(c.hits.length).toBe(1);
    expect(c.hits[0]!.mirrored).toBe(mirrored);
    return c.hits[0]!.followup;
  };
  for (const m of [false, true]) {
    expect(fu(m)).toEqual({ lock: 2, fired: true, reason: null });
    // no row map: the TSD's two cleared rows split the slot, so it is never joined
    expect(fu(m, { followupNoRowmap: true }).fired).toBe(false);
    // a T in the slot that is not a full TSD: refused, and fired by a follow-up that accepts any T
    expect(fu(m, {}, 'mini')).toEqual({ lock: 2, fired: false, reason: 't_in_slot_not_tsd' });
    expect(fu(m, { followupAnyT: true }, 'mini').fired).toBe(true);
  }
  // the slot carried in the drawn columns on a mirrored hit: on the mirrored board those cells are where the page's
  // Z goes, so the Z fills the unmirrored slot before the second T comes
  expect(fu(false, { followupUnmirrored: true }).fired).toBe(true);
  expect(fu(true, { followupUnmirrored: true })).toEqual({ lock: 1, fired: false, reason: 'slot_filled_before_t' });
});

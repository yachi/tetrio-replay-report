/**
 * The 階段のドネイト (Kaidan Setups) technique profile for `technique-facts.ts`: shiwehi.com's
 * `template/kaidansetup.php`, the ninth mid-game technique page. Data only; every rule is the shared matcher's, and
 * the shape (the agreement-box window, the T cells, the well cell) is the gated transcription
 * `pipeline/openers/kaidan-technique.json`.
 *
 * A staircase, a Z stood on end on its lowest step at the wall, a roof over the slot's end away from the wall: the
 * T laid flat, pointing
 * down (the anchor of STMB Cave, ダブルダガー, BT砲, 千鳥格子, 社畜トレイン and 欄干), clears the two rows the Z's top half
 * is in, and the column beside the Z's foot opens from the top to the floor (a donation). The shape sits in the
 * cleared rows and the two rows under them, all on one board at the TSD's lock, so no sequence of locks is needed; the
 * window counts no steps (it cannot tell a staircase from a flat stack). No shared rule file changed for this profile.
 *
 * THE PAYOFF IS HARDDROP'S. shiwehi.com names no Tetris after a Kaidan (its next step is ST積み or よしひろ積み, which
 * nothing measures); harddrop's Kaidan_Setups and Anchor_Set pages do. So the variant carries 欄干's `well_quad`
 * payoff: the matcher carries the well cell to the first later lock that puts a cell in its column, fired iff that
 * lock, inside the verified prefix, is an I with a cell at or below the carried cell, which the engine records
 * clearing four lines. That the column re-opens and is at least two deep the window itself decides.
 *
 * No `crossRoute`: no committed routes board draws a Kaidan (the gate's `routes_fire_none`).
 */
import type { TechniqueProfile } from './technique-profile.ts';
import { QUALIFY_OPTIONS, techniqueQualifier } from './technique-qualify.ts';
import { DPC_LOCKS } from './shachikutrain-qualify.ts';
import { WHOLE_SHAPE_RULE, withWholeShape } from './technique-wholeshape.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const tag = (h: any) => `lock ${h.lock}${h.mirrored ? ' (mirrored)' : ''}`;

export const KAIDAN: TechniqueProfile = {
  key: 'kaidan',
  tag: 'kaidan',
  transcriptionPath: `${OPENERS}/kaidan-technique.json`,
  artefactPath: `${REPO}/analysis/kaidan-facts.json`,
  hashFiles: {
    classifier: [`${SIM}/technique-facts.ts`, `${SIM}/technique-wholeshape.ts`, `${SIM}/technique-profile.ts`, `${SIM}/technique-profile-kaidan.ts`,
                 `${SIM}/emit-technique-facts.ts`, `${SIM}/route-facts.ts`,
                 `${SIM}/technique-qualify.ts`, `${SIM}/shachikutrain-qualify.ts`],
  },
  opportunity: { spin: 'full', lines: 2 },
  controlSpins: [
    { name: 'TSS', kind: { spin: 'full', lines: 1 } },
    { name: 'TST', kind: { spin: 'full', lines: 3 } },
    { name: 'mini_TSS', kind: { spin: 'mini', lines: 1 } },
    { name: 'mini_TSD', kind: { spin: 'mini', lines: 2 } },
  ],
  anchor: 'spin_t_cells',
  garbage: 'filled',
  artefact: {
    schema: 'technique-facts/1',
    means: 'For every scored T-spin in the corpus (a T with an engine spin credit that cleared lines, inside '
      + 'the verified prefix, passing the reconstruction check), whether the 階段のドネイト (Kaidan Setups) page\'s local '
      + 'shape stood around it: the lock\'s cells are the page\'s T (laid flat, pointing down, at a full TSD, as drawn '
      + 'or mirrored) and every cell of the window around it — the roof over the T\'s end away from the wall in the row above it, the '
      + 'two rows the TSD clears, and the two rows under them, the Z\'s foot and the steps filled and the wall column '
      + '(the well) empty — is filled or empty as drawn. Every hit is followed to the first later piece that enters '
      + 'the well\'s column, to see whether it is the Tetris harddrop\'s pages draw next.',
    notEligible: 'simulator output: which local shape a T went into is read off the vendored Triangle '
      + 'engine\'s boards, and nothing on the corpus side has a second implementation of it. No claim id, '
      + 'no badge, no figure in a report.',
    caveat: 'garbage is read as FILLED inside the window, and its hole columns are the engine\'s seeded-RNG '
      + 'columns, which disagree with the recorded ones (oracle-source.ts): the well cells beside the Z\'s foot can be '
      + 'garbage rows\' holes, so a hit\'s well is the board the oracle offered, and a hit with garbage in its window is '
      + 'named in garbage_in_window for that reason. At a full TSD the two cleared rows are entailed by the clear '
      + '(NaiveClauseForced), and so is the well re-opening inside the window: the payoff (an I clearing 4 into the '
      + 'well, inside the verified prefix, whose attack the replay recorded) is what the window does not decide. The '
      + 'payoff is harddrop\'s next step, not shiwehi.com\'s. The window counts no steps and does not see the Z. Counts '
      + 'only, always N / M with the denominator.',
  },
  rules: () => [
    'opportunity: a full TSD (2 lines) at a 0-based lock index <= the verified index, whose board-before plus its '
      + 'cells makes exactly the rows the engine recorded clearing (the reconstruction check, counted exactly as '
      + 'opener-facts.json donation.check counts it)',
    'match: the lock\'s cells equal the page\'s T under one translation (mirrored: columns reflected in the '
      + 'window), and every other window cell is filled (a piece or garbage) or empty as the page draws it; colour is '
      + 'never compared; cells outside the window are not read',
    'mirrored is tried only when as-drawn fails; a window leaving the board is no match (window_off_board)',
    'payoff: the well cell beside the Z\'s foot carried through every clear and garbage insertion, each step '
      + 'verified against the engine\'s next board, to the first later lock with a cell in its column; fired iff that '
      + 'lock is inside the verified prefix, has a cell at or below the carried cell, is an I and cleared 4 lines '
      + '(otherwise past_verified, well_covered, well_filled_not_i, i_in_well_not_quad, rowmap_unverified, '
      + 'slot_off_board or round_ended); well_depth = the empty cells under the well cell on the board before the '
      + 'spin, garbage filled',
    'controls: the same window at the profile\'s other scored spins; ablations no_must_empty, no_roof and t_overlap '
      + 'at the opportunity; orientation_baseline = opportunities whose T stands up',
  ],
  qualify: {
    rules: [
      `fragment: a key cell — the roof over the slot's end away from the wall (basic.spin row 1, columns 5-6) and the Z stood on end on the lowest step (rows 2-4, columns 8-9), mirrored with the window — belongs to a piece not all four of whose cells are on the board before the T (a line clear cut it)`,
      'garbage_in_shape: a key cell is garbage',
      'shape_cell_empty: a key cell is empty (the window requires it filled, so only a weakened window can admit this)',
      'z_not_one_piece: the four cells the page draws as its Z are not one piece (the page: 「Zを縦置き」)',
      `dpc: the board is empty after one of the ${DPC_LOCKS} locks before the T, the T itself, or one of the ${DPC_LOCKS} after it (the DPC setup)`,
      'ownership_unverified: a lock before the T has a row map the digest could not verify, so its pieces cannot be told apart',
      WHOLE_SHAPE_RULE,
      'qualifies iff none applies; the shape stood at every hit either way',
    ],
    check: withWholeShape(`${OPENERS}/kaidan-technique.json`,
                          techniqueQualifier(`${OPENERS}/kaidan-technique.json`, QUALIFY_OPTIONS.kaidan)),
  },
  lists: (hits, name) => ({
    kaidan_hits: hits.map(h => `${name(h)} ${tag(h)}`),
    payoff_not_fired: hits.filter(h => !h.followup.fired)
      .map(h => `${name(h)} lock ${h.lock} (${h.followup.reason}${h.followup.lock !== null ? ` at lock ${h.followup.lock}` : ''})`),
    garbage_in_window: hits.filter(h => h.garbage_in_window).map(h => `${name(h)} lock ${h.lock}`),
    kaidan_in_opener: hits.filter(h => h.in_opener).map(h => `${name(h)} lock ${h.lock}`),
    well_depth_lt4: hits.filter(h => h.well_depth < 4).map(h => `${name(h)} lock ${h.lock} (${h.well_depth} deep)`),
  }),
};

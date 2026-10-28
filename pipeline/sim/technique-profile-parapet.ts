/**
 * The 欄干 (Parapet) technique profile for `technique-facts.ts`: shiwehi.com's `template/parapet.php`, the eighth
 * mid-game technique page. Data only; every rule is the shared matcher's, and the shape (the agreement-box window,
 * the two variants' T cells, the well cell) is the gated transcription `pipeline/openers/parapet-technique.json`.
 *
 * TWO VARIANTS ON ONE TERRAIN. An L stood on end, shifted one column, its foot under the slot's left end, a roof over
 * its right end. `parapet` is the TSD (the T laid flat, pointing down: the profile's opportunity, as on the seven
 * earlier pages); `parapet_tss` is the TSS the page draws on the same terrain (the T stood up, nub right). The shared
 * matcher measures each variant at the spin its transcription names, so the TSS variant's denominator is the scored
 * full TSSs, which is why TSS is among `controlSpins` here: under the TSD variant it is a control, under the TSS
 * variant it is the opportunity and the TSD takes its place among the controls.
 *
 * THE PAYOFF, NOT A FOLLOW-UP. The page promises no second T-spin. Either spin clears the L's foot out of the column
 * under the T's left arm and leaves a well open from its top to the floor (a donation); harddrop and Tetrisチャンネル
 * draw the next step as a Tetris into it (shiwehi names a Tetris only as its reason to prefer the TSS). So each variant carries a `payoff` (`well_quad`), and the matcher carries the
 * well cell to the first later lock that puts a cell in its column: fired iff that lock, inside the verified prefix,
 * is an I with a cell at or below the carried cell, which the engine records clearing four lines. That the column
 * re-opens and is at least two deep the window itself decides (so neither is reported as a payoff); `well_depth` on
 * each hit is the depth on the board before the spin.
 *
 * No `crossRoute`: the only routes boards the window fires on are two 9-row 山岳積み2号 boards the route artefact
 * cannot match (the gate records them in `cross_source.also`).
 */
import type { TechniqueProfile } from './technique-profile.ts';
import { parapetQualifier } from './parapet-qualify.ts';
import { DPC_LOCKS } from './shachikutrain-qualify.ts';
import { WHOLE_SHAPE_RULE, withWholeShape } from './technique-wholeshape.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const tag = (h: any) => `lock ${h.lock}${h.mirrored ? ' (mirrored)' : ''}`;

export const PARAPET: TechniqueProfile = {
  key: 'parapet',
  tag: 'parapet',
  transcriptionPath: `${OPENERS}/parapet-technique.json`,
  artefactPath: `${REPO}/analysis/parapet-facts.json`,
  hashFiles: {
    classifier: [`${SIM}/technique-facts.ts`, `${SIM}/technique-wholeshape.ts`, `${SIM}/technique-profile.ts`, `${SIM}/technique-profile-parapet.ts`,
                 `${SIM}/emit-technique-facts.ts`, `${SIM}/route-facts.ts`, `${SIM}/parapet-qualify.ts`,
                 `${SIM}/shachikutrain-qualify.ts`],
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
      + 'the verified prefix, passing the reconstruction check), whether the 欄干 (Parapet) page\'s local shape '
      + 'stood around it: the lock\'s cells are the page\'s T (variant parapet: laid flat, pointing down, at a full '
      + 'TSD; variant parapet_tss: stood up, nub right, at a full TSS; as drawn, or mirrored) and every cell of the '
      + 'window around it — the L\'s stem, the slot and the roof in the row above the TSD\'s, the two rows the TSD '
      + 'clears with the L\'s foot under the T\'s arm, and the well two rows deep under it — is filled or empty as '
      + 'drawn. Every hit is followed to the first later piece that enters the well\'s column, to see whether it is '
      + 'the Tetris the page sets up.',
    notEligible: 'simulator output: which local shape a T went into is read off the vendored Triangle '
      + 'engine\'s boards, and nothing on the corpus side has a second implementation of it. No claim id, '
      + 'no badge, no figure in a report.',
    caveat: 'garbage is read as FILLED inside the window, and its hole columns are the engine\'s seeded-RNG '
      + 'columns, which disagree with the recorded ones (oracle-source.ts): the well cells under the T\'s arm can be '
      + 'garbage rows\' holes, so a hit\'s well is the board the oracle offered, and a hit with garbage in its '
      + 'window is named in garbage_in_window for that reason. At a full TSD the two cleared rows are entailed by the '
      + 'clear (NaiveClauseForced), and so is the well re-opening inside the window: the payoff (an I clearing 4 into '
      + 'the well, inside the verified prefix, whose attack the replay recorded) is what the window does not decide. '
      + 'Counts only, always N / M with the denominator.',
  },
  rules: () => [
    'opportunity, per variant: the full T-spin its transcription names (parapet: a TSD clearing 2 lines; parapet_tss: '
      + 'a TSS clearing 1), at a 0-based lock index <= the verified index, whose board-before plus its cells makes '
      + 'exactly the rows the engine recorded clearing (the reconstruction check, counted exactly as '
      + 'opener-facts.json donation.check counts it)',
    'match: the lock\'s cells equal the variant\'s T under one translation (mirrored: columns reflected in the '
      + 'window), and every other window cell is filled (a piece or garbage) or empty as the page draws it; colour is '
      + 'never compared; cells outside the window are not read',
    'mirrored is tried only when as-drawn fails; a window leaving the board is no match (window_off_board, each '
      + 'entry naming its variant)',
    'payoff: the well cell under the T\'s left arm (mirrored: right) carried through every clear and garbage '
      + 'insertion, each step verified against the engine\'s next board, to the first later lock with a cell in its '
      + 'column; fired iff that lock is inside the verified prefix, has a cell at or below the carried cell, is an I '
      + 'and cleared 4 lines (otherwise past_verified, well_covered, well_filled_not_i, i_in_well_not_quad, '
      + 'rowmap_unverified, slot_off_board or round_ended); well_depth = the empty cells under the well cell on the '
      + 'board before the spin, garbage filled',
    'controls, per variant: the same window at the profile\'s other scored spins (under parapet_tss the TSD is one of '
      + 'them); ablations no_must_empty, no_roof and t_overlap at the variant\'s opportunity; orientation_baseline = '
      + 'opportunities whose T stands up',
  ],
  qualify: {
    rules: [
      'fragment: a cell both of the page\'s builds (basic.z, basic.o) draw as a piece of their own inside the window '
        + '(the stood L and the two roof cells, mirrored with the window) belongs to a piece not all four of whose '
        + 'cells are on the board before the T (a line clear cut it)',
      'garbage_in_shape: one of those cells is garbage',
      'shape_cell_empty: one of those cells is empty (the window requires it filled, so only a weakened window can admit this)',
      'l_not_one_piece: the four cells the page draws as its L are not one piece (the page: 「%Lを1列ずらして立てて置き」)',
      `dpc: the board is empty after one of the ${DPC_LOCKS} locks before the T, the T itself, or one of the ${DPC_LOCKS} after it (the DPC setup)`,
      'ownership_unverified: a lock before the T has a row map the digest could not verify, so its pieces cannot be told apart',
      WHOLE_SHAPE_RULE,
      'qualifies iff none applies; the shape stood at every hit either way',
    ],
    check: withWholeShape(`${OPENERS}/parapet-technique.json`,
                          parapetQualifier(`${OPENERS}/parapet-technique.json`)),
  },
  lists: (hits, name) => {
    const of = (v: string) => hits.filter(h => h.variant === v);
    return {
      parapet_hits: of('parapet').map(h => `${name(h)} ${tag(h)}`),
      parapet_tss_hits: of('parapet_tss').map(h => `${name(h)} ${tag(h)}`),
      payoff_not_fired: hits.filter(h => !h.followup.fired)
        .map(h => `${name(h)} lock ${h.lock} (${h.variant}: ${h.followup.reason}${h.followup.lock !== null ? ` at lock ${h.followup.lock}` : ''})`),
      garbage_in_window: hits.filter(h => h.garbage_in_window).map(h => `${name(h)} lock ${h.lock} (${h.variant})`),
      parapet_in_opener: hits.filter(h => h.in_opener).map(h => `${name(h)} lock ${h.lock} (${h.variant})`),
      well_depth_lt4: hits.filter(h => h.well_depth < 4)
        .map(h => `${name(h)} lock ${h.lock} (${h.variant}: ${h.well_depth} deep)`),
    };
  },
};

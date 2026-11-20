/**
 * The ハンバーガー (Hamburger) technique profile for `technique-facts.ts`: harddrop's Hamburger page, the fourteenth
 * mid-game technique page (yachi's request). Data only; every rule is the shared matcher's, and the shape (the
 * agreement-box window, the T's cells, the well under the cover) is the gated transcription
 * `pipeline/openers/hamburger-technique.json`.
 *
 * A flat, nub-down T into a full T-spin Single whose cleared row covers a hole two columns from the nub, on the side
 * away from the roof: the clear drops the cover and the hole under it opens from the top, a well. The page repeats
 * the TSS on the rising stack and ends with an I into the well. So the variant carries 欄干's `well_quad` payoff, not a
 * follow-up: the well cell is carried to the first later piece in its column, and a piece that fills it without a
 * Tetris is the page's repetition (another layer), never a failure of the shape.
 *
 * No `crossRoute`: the bag-1 boards of SDPC Spin and stick spin fire the window (the gate's `cross:` rule), and
 * `hamburger.test.ts` names every corpus hit that is one of those route cases, against the route artefacts.
 */
import type { TechniqueProfile } from './technique-profile.ts';
import { QUALIFY_OPTIONS, techniqueQualifier } from './technique-qualify.ts';
import { DPC_LOCKS } from './shachikutrain-qualify.ts';
import { WHOLE_SHAPE_RULE, withWholeShape } from './technique-wholeshape.ts';
import { withHamburgerCover, withMidGameOnly } from './hamburger-cover.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const tag = (h: any) => `lock ${h.lock}${h.mirrored ? ' (mirrored)' : ''}`;

export const HAMBURGER: TechniqueProfile = {
  key: 'hamburger',
  tag: 'hamburger',
  transcriptionPath: `${OPENERS}/hamburger-technique.json`,
  artefactPath: `${REPO}/analysis/hamburger-facts.json`,
  hashFiles: {
    classifier: [`${SIM}/technique-facts.ts`, `${SIM}/technique-wholeshape.ts`, `${SIM}/technique-profile.ts`, `${SIM}/technique-profile-hamburger.ts`,
                 `${SIM}/emit-technique-facts.ts`, `${SIM}/route-facts.ts`,
                 `${SIM}/technique-qualify.ts`, `${SIM}/shachikutrain-qualify.ts`, `${SIM}/hamburger-cover.ts`],
  },
  opportunity: { spin: 'full', lines: 1 },
  controlSpins: [
    { name: 'TSD', kind: { spin: 'full', lines: 2 } },
    { name: 'TST', kind: { spin: 'full', lines: 3 } },
    { name: 'mini_TSS', kind: { spin: 'mini', lines: 1 } },
    { name: 'mini_TSD', kind: { spin: 'mini', lines: 2 } },
  ],
  anchor: 'spin_t_cells',
  garbage: 'filled',
  artefact: {
    schema: 'technique-facts/1',
    means: 'For every scored T-spin in the corpus (a T with an engine spin credit that cleared lines, inside '
      + 'the verified prefix, passing the reconstruction check), whether harddrop\'s Hamburger local shape stood '
      + 'around it: the lock\'s cells are the page\'s T laid flat, nub down, at a full TSS (as drawn, or mirrored), '
      + 'and every cell of the window around it — the roof over the T\'s far end, the open cells over the well, the '
      + 'row the TSS clears (the cover over the well) and the hole under the cover — is filled or empty as drawn. '
      + 'Every hit is followed to the first later piece that enters the well\'s column, to see whether it is the '
      + 'Tetris the page ends on; a piece that fills the well without one is the page\'s next layer.',
    notEligible: 'simulator output: which local shape a T went into is read off the vendored Triangle '
      + 'engine\'s boards, and nothing on the corpus side has a second implementation of it. No claim id, '
      + 'no badge, no figure in a report.',
    caveat: 'garbage is read as FILLED inside the window, and its hole columns are the engine\'s seeded-RNG '
      + 'columns, never observed directly (oracle-source.ts): the hole under the cover can be a garbage row\'s hole, '
      + 'which counts, so a hit\'s well is the board the oracle offered, and a hit with garbage in its window is named '
      + 'in garbage_in_window for that reason. At a full TSS the cleared row is entailed by the clear '
      + '(NaiveClauseForced), and so is the well re-opening inside the window: the payoff (an I clearing 4 into the '
      + 'well, inside the verified prefix) is what the window does not decide. A payoff reason of well_covered or '
      + 'well_filled_not_i is the page\'s repetition (another layer stacked over the well), not a failure. Counts '
      + 'only, always N / M with the denominator.',
  },
  rules: () => [
    'opportunity: a T lock with spin "full" clearing 1 line, at a 0-based lock index <= the verified index, '
      + 'whose board-before plus its cells makes exactly the rows the engine recorded clearing (the '
      + 'reconstruction check, counted exactly as opener-facts.json donation.check counts it)',
    'match: the lock\'s cells equal the variant\'s flat T under one translation (mirrored: columns reflected in the '
      + 'window), and every other window cell is filled (a piece or garbage) or empty as the page draws it; colour is '
      + 'never compared; cells outside the window are not read',
    'mirrored is tried only when as-drawn fails; a window leaving the board is no match (window_off_board)',
    'payoff: the well cell under the cover, two columns from the nub away from the roof, carried through every clear '
      + 'and garbage insertion, each step verified against the engine\'s next board, to the first later lock with a '
      + 'cell in its column; fired iff that lock is inside the verified prefix, has a cell at or below the carried '
      + 'cell, is an I and cleared 4 lines (otherwise past_verified, well_covered, well_filled_not_i, '
      + 'i_in_well_not_quad, rowmap_unverified, slot_off_board or round_ended); well_depth = the empty cells under '
      + 'the well cell on the board before the spin, garbage filled',
    'controls: the same window at scored full TSD and TST and mini TSS and TSD; ablations no_must_empty, no_roof '
      + 'and t_overlap at the opportunity; orientation_baseline = opportunities whose T stands up',
  ],
  qualify: {
    rules: [
      'fragment: a key cell — the cover over the hole (the cleared row\'s cells at the well and next to the nub: one S '
        + 'or Z, or other complete pieces, one or several, yachi\'s 「用S/Z 砌hamburger 先算，除非有其他完整piece 砌到」) or '
        + 'the roof over the T\'s far end — belongs to a piece not all four of whose cells are on the board before the '
        + 'T (a line clear cut it)',
      'garbage_in_shape: a key cell is garbage (the hole under the cover may be a garbage row\'s hole; the cover may not be garbage)',
      'shape_cell_empty: a key cell is empty (the window requires it filled, so only a weakened window can admit this)',
      'in_opener: the T locks inside the opener window (0-based lock <= WINDOW_PIECES); this is a mid-game page, so an opener hit (SDPC Spin or stick spin bag 1) never counts (yachi: 「開局唔洗計啦，叫得中盤」)',
      `dpc: the board is empty after one of the ${DPC_LOCKS} locks before the T, the T itself, or one of the ${DPC_LOCKS} after it (the DPC setup)`,
      'ownership_unverified: a lock before the T has a row map the digest could not verify, so its pieces cannot be told apart',
      WHOLE_SHAPE_RULE,
      'qualifies iff none applies; the shape stood at every hit either way',
      'cover (a field, not a rule): one_sz when one whole S or Z covers both cover cells, complete_pieces when whole '
        + 'pieces do otherwise, not_complete when a cover cell is garbage or a fragment, null when ownership is unverified',
    ],
    check: withMidGameOnly(withHamburgerCover(withWholeShape(`${OPENERS}/hamburger-technique.json`,
                          techniqueQualifier(`${OPENERS}/hamburger-technique.json`, QUALIFY_OPTIONS.hamburger)))),
  },
  lists: (hits, name) => ({
    hamburger_hits: hits.map(h => `${name(h)} ${tag(h)}`),
    payoff_not_fired: hits.filter(h => !h.followup.fired)
      .map(h => `${name(h)} lock ${h.lock} (${h.followup.reason}${h.followup.lock !== null ? ` at lock ${h.followup.lock}` : ''})`),
    garbage_in_window: hits.filter(h => h.garbage_in_window).map(h => `${name(h)} lock ${h.lock}`),
    cover_one_sz: hits.filter(h => h.cover === 'one_sz').map(h => `${name(h)} lock ${h.lock}`),
    hamburger_in_opener: hits.filter(h => h.in_opener).map(h => `${name(h)} lock ${h.lock}`),
    well_depth_lt4: hits.filter(h => h.well_depth < 4).map(h => `${name(h)} lock ${h.lock} (${h.well_depth} deep)`),
  }),
};

/**
 * The 基本的なドネイト (basic donating) technique profile for `technique-facts.ts`: shiwehi.com's
 * `template/basicdonating.php`, the eleventh mid-game technique page. Data only; every rule is the shared matcher's,
 * and the shape (six hole windows, the T cells, the well cell) is the gated transcription
 * `pipeline/openers/basicdonating-technique.json`.
 *
 * A piece laid over a hole so that only the two rows the TSD clears are filled in the hole's column: the T laid flat,
 * pointing down, clears them and the hole opens again from the top to its floor. The page draws holes 1 to 6 columns
 * from the T's near arm, so there are six variants (k1..k6), each the T's own 2x3 box plus four cells in the hole's
 * column (`window_basis: well`): the cell above the donation empty, the two donated cells filled, the hole under them
 * empty. Nothing else on the board is read, which is the point of a BASIC donation: every named donation (階段, 欄干,
 * STMB Cave, 社畜トレイン's first TSD) is one of these windows plus more, and the qualify rule `other_page` gives such a
 * T to the page that names it.
 *
 * THE PAYOFF IS HARDDROP'S. The page says only that the hole stays open to dig (「下穴が開いた状態を維持」); harddrop's
 * Donation page draws the Tetris into it. So each variant carries 欄干's `well_quad` payoff.
 *
 * No `crossRoute`: the routes boards the windows fire on are recorded in the gate's `cross_source` and are the same
 * T's as STMB Cave's and SDPC Spin's TSS, which other pages already measure.
 */
import type { TechniqueProfile } from './technique-profile.ts';
import { DPC_LOCKS, OTHER_PAGES, SHALLOW_BELOW, donationQualifier } from './basicdonating-qualify.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const tag = (h: any) => `${h.variant} lock ${h.lock}${h.mirrored ? ' (mirrored)' : ''}`;

export const BASICDONATING: TechniqueProfile = {
  key: 'basicdonating',
  tag: 'basicdonating',
  transcriptionPath: `${OPENERS}/basicdonating-technique.json`,
  artefactPath: `${REPO}/analysis/basicdonating-facts.json`,
  hashFiles: {
    classifier: [`${SIM}/technique-facts.ts`, `${SIM}/technique-profile.ts`, `${SIM}/technique-profile-basicdonating.ts`,
                 `${SIM}/emit-technique-facts.ts`, `${SIM}/route-facts.ts`,
                 `${SIM}/basicdonating-qualify.ts`, `${SIM}/technique-qualify.ts`, `${SIM}/shachikutrain-qualify.ts`,
                 ...OTHER_PAGES.map(k => `${OPENERS}/${k}-technique.json`)],
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
      + 'the verified prefix, passing the reconstruction check), whether one of the 基本的なドネイト (basic donating) '
      + 'page\'s six hole windows stood around it: the lock\'s cells are the page\'s T (laid flat, pointing down, at a '
      + 'full TSD, as drawn or mirrored), and in a column 1 to 6 columns from the T\'s near arm the two cells in the rows '
      + 'the TSD clears are filled, the cell above them and the cell under them empty — a piece laid over a hole, '
      + 'donated to the TSD. Every hit is followed to the first later piece that enters the hole\'s column, to see '
      + 'whether it is the Tetris harddrop\'s Donation page draws next.',
    notEligible: 'simulator output: which local shape a T went into is read off the vendored Triangle '
      + 'engine\'s boards, and nothing on the corpus side has a second implementation of it. No claim id, '
      + 'no badge, no figure in a report.',
    caveat: 'garbage is read as FILLED inside the window, and its hole columns are the engine\'s seeded-RNG '
      + 'columns, which disagree with the recorded ones (oracle-source.ts): a hole under a donation can be a garbage '
      + 'row\'s hole, so a hit\'s hole is the board the oracle offered, and a hit with garbage in its window is named in '
      + 'garbage_in_window for that reason. At a full TSD the two cleared rows are entailed by the clear '
      + '(NaiveClauseForced): what discriminates is the empty cell above the donation and the empty hole under it. The '
      + 'windows read nothing else, so most named donations are hits too; the qualify rules give such a T to the page '
      + 'that names it (other_page). The payoff is harddrop\'s next step, not shiwehi.com\'s. Counts only, always N / M '
      + 'with the denominator.',
  },
  rules: () => [
    'opportunity: a full TSD (2 lines) at a 0-based lock index <= the verified index, whose board-before plus its '
      + 'cells makes exactly the rows the engine recorded clearing (the reconstruction check, counted exactly as '
      + 'opener-facts.json donation.check counts it)',
    'match, per variant k1..k6: the lock\'s cells equal the page\'s T under one translation (mirrored: columns '
      + 'reflected in the window), and every other window cell is filled (a piece or garbage) or empty as the page '
      + 'draws it; colour is never compared; cells outside the window are not read; each variant is matched on its '
      + 'own, so a T over two holes is a hit of two variants',
    'mirrored is tried only when as-drawn fails; a window leaving the board is no match (window_off_board)',
    'payoff: the hole\'s cell under the donation carried through every clear and garbage insertion, each step '
      + 'verified against the engine\'s next board, to the first later lock with a cell in its column; fired iff that '
      + 'lock is inside the verified prefix, has a cell at or below the carried cell, is an I and cleared 4 lines '
      + '(otherwise past_verified, well_covered, well_filled_not_i, i_in_well_not_quad, rowmap_unverified, '
      + 'slot_off_board or round_ended); well_depth = the empty cells under the well cell on the board before the '
      + 'spin, garbage filled',
    'controls: the same windows at the profile\'s other scored spins; ablations no_must_empty, no_roof and t_overlap '
      + 'at the opportunity; orientation_baseline = opportunities whose T stands up',
  ],
  qualify: {
    rules: [
      'fragment: a donated cell (the hole\'s column in the two rows the TSD clears, mirrored with the window) belongs '
        + 'to a piece not all four of whose cells are on the board before the T (a line clear cut it)',
      'garbage_in_shape: a donated cell is garbage',
      'shape_cell_empty: a donated cell is empty (the window requires it filled, so only a weakened window can admit this)',
      `dpc: the board is empty after one of the ${DPC_LOCKS} locks before the T, the T itself, or one of the ${DPC_LOCKS} after it (the DPC setup)`,
      'ownership_unverified: a lock before the T has a row map the digest could not verify, so its pieces cannot be told apart',
      `other_page: another technique page's window (${OTHER_PAGES.join(', ')}; any variant, either hand) fires at the same T, so the T is that page's`,
      'nearer_well: a variant with a smaller hole offset fires at the same T, so the T is counted once, at its nearest hole',
      'well_covered: a filled cell anywhere above the window in the hole\'s column, so the clear does not leave the hole open from the top',
      `shallow_well: the nub variant only: fewer than ${SHALLOW_BELOW} empty cells under the nub, so the re-opened column cannot take a Tetris`,
      'qualifies iff none applies; the shape stood at every hit either way',
    ],
    check: donationQualifier(`${OPENERS}/basicdonating-technique.json`, OPENERS),
  },
  lists: (hits, name) => ({
    basicdonating_hits: hits.map(h => `${name(h)} ${tag(h)}`),
    payoff_not_fired: hits.filter(h => !h.followup.fired)
      .map(h => `${name(h)} ${h.variant} lock ${h.lock} (${h.followup.reason}${h.followup.lock !== null ? ` at lock ${h.followup.lock}` : ''})`),
    garbage_in_window: hits.filter(h => h.garbage_in_window).map(h => `${name(h)} ${h.variant} lock ${h.lock}`),
    basicdonating_in_opener: hits.filter(h => h.in_opener).map(h => `${name(h)} ${h.variant} lock ${h.lock}`),
  }),
};

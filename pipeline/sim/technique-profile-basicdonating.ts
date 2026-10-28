/**
 * The 基本的なドネイト (basic donating) technique profile for `technique-facts.ts`: shiwehi.com's
 * `template/basicdonating.php`, the eleventh mid-game technique page.
 *
 * The page teaches a PRINCIPLE over many terrains (「TSDで消える2列だけを埋める」), and since 2026-10-26 it is matched by
 * that principle as yachi states it, not by windows: a piece laid over empty cells so that it overhangs them inside the
 * rows the TSD clears; the clear takes the overhang away and the cells under it are open from the top again
 * (`basicdonating-rule.ts`, the profile's `detect`). Any column, any depth, any distance from the T; the covering cells
 * must be the T or complete pieces, never garbage; a hole covered only by the T's nub is a plain T-spin. The six hole
 * windows (k1..k6) and the nub window that came before are retired: they matched the page's own distances only.
 *
 * THE PAYOFF IS HARDDROP'S. The page says only that the hole stays open to dig (「下穴が開いた状態を維持」); harddrop's
 * Donation page draws the Tetris into it. So the variant carries 欄干's `well_quad` payoff, at the hit's own column
 * (the nearest to the T).
 */
import type { TechniqueProfile } from './technique-profile.ts';
import { OTHER_PAGES, ROUTE_ARTEFACTS, ROUTE_LOCKS, donationQualifier } from './basicdonating-qualify.ts';
import { RULE_ABLATIONS, donationDetector } from './basicdonating-rule.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const tag = (h: any) => `lock ${h.lock} column ${h.donation.columns.map((c: any) => c.col).join('+')}`;

export const BASICDONATING: TechniqueProfile = {
  key: 'basicdonating',
  tag: 'basicdonating',
  transcriptionPath: `${OPENERS}/basicdonating-technique.json`,
  artefactPath: `${REPO}/analysis/basicdonating-facts.json`,
  hashFiles: {
    classifier: [`${SIM}/technique-facts.ts`, `${SIM}/technique-profile.ts`, `${SIM}/technique-profile-basicdonating.ts`,
                 `${SIM}/emit-technique-facts.ts`, `${SIM}/route-facts.ts`, `${SIM}/basicdonating-rule.ts`,
                 `${SIM}/basicdonating-qualify.ts`, `${SIM}/shachikutrain-qualify.ts`,
                 ...OTHER_PAGES.map(k => `${OPENERS}/${k}-technique.json`),
                 ...ROUTE_ARTEFACTS.map(k => `${REPO}/analysis/${k}-facts.json`)],
  },
  opportunity: { spin: 'full', lines: 2 },
  controlSpins: [
    { name: 'TSS', kind: { spin: 'full', lines: 1 } },
    { name: 'TST', kind: { spin: 'full', lines: 3 } },
    { name: 'mini_TSS', kind: { spin: 'mini', lines: 1 } },
    { name: 'mini_TSD', kind: { spin: 'mini', lines: 2 } },
  ],
  anchor: 'spin_t_cells',
  detect: { ablations: RULE_ABLATIONS, match: donationDetector() as any },
  garbage: 'filled',
  artefact: {
    schema: 'technique-facts/1',
    means: 'For every scored T-spin in the corpus (a T with an engine spin credit that cleared lines, inside '
      + 'the verified prefix, passing the reconstruction check), whether it was a DONATION: a piece laid over empty '
      + 'cells so that it overhangs them inside the rows the T-spin clears, so the clear opens those cells from the top '
      + 'again (基本的なドネイト, 「TSDで消える2列だけを埋める」, as yachi states it). Every hit is followed to the first later '
      + 'piece that enters its hole\'s column, to see whether it is the Tetris harddrop\'s Donation page draws next.',
    notEligible: 'simulator output: which board a T went into is read off the vendored Triangle '
      + 'engine\'s boards, and nothing on the corpus side has a second implementation of it. No claim id, '
      + 'no badge, no figure in a report.',
    caveat: 'garbage is read as FILLED, and its hole columns are the engine\'s seeded-RNG columns, which disagree with '
      + 'the recorded ones (oracle-source.ts): a hole under a donation can be a garbage row\'s hole, so a hit\'s hole is '
      + 'the board the oracle offered, and a hit with garbage in its box is named in garbage_in_window. Most named '
      + 'donations are hits too; the qualify rule gives such a T to the page that names it (other_page). The payoff is '
      + 'harddrop\'s next step, not shiwehi.com\'s. Counts only, always N / M with the denominator.',
  },
  rules: () => [
    'opportunity: a full TSD (2 lines) at a 0-based lock index <= the verified index, whose board-before plus its '
      + 'cells makes exactly the rows the engine recorded clearing (the reconstruction check, counted exactly as '
      + 'opener-facts.json donation.check counts it)',
    'match (no window): a column DONATES when, at its topmost cell that is empty, outside the cleared rows and directly '
      + 'under a cleared-row cell, (1) every filled cell of the column above it lies in the cleared rows, (2) each is '
      + 'the T or a cell of a complete piece (all four cells on the board before the T, never garbage), and (3) the cell '
      + 'directly above it is not the T (a hole under the T\'s nub alone is a plain T-spin), and (4) when the piece directly '
      + 'above it locked, the cell under that piece\'s lowest cell in the column was already empty (the hole came first: '
      + 'garbage rising under a piece later covered nothing); the lock is a hit when any '
      + 'column donates; cover = cleared when every covering piece lies inside the cleared rows, else kept',
    'the hit\'s own column (its payoff well and its box): the donating column nearest to the T\'s columns, then the '
      + 'leftmost; the box runs from the row over the cleared rows to the row under that hole, over the T and that column',
    'payoff: the hole\'s top cell carried through every clear and garbage insertion, each step verified against the '
      + 'engine\'s next board, to the first later lock with a cell in its column; fired iff that lock is inside the '
      + 'verified prefix, has a cell at or below the carried cell, is an I and cleared 4 lines (otherwise past_verified, '
      + 'well_covered, well_filled_not_i, i_in_well_not_quad, rowmap_unverified, slot_off_board or round_ended); '
      + 'well_depth = the empty cells from that hole down, garbage filled',
    'controls: the same rule at the profile\'s other scored spins; ablations allow_t_nub (rule 3 dropped), '
      + 'allow_fragment (rule 2 dropped), no_reopen (rule 1 dropped) and allow_late_hole (rule 4 dropped) at the opportunity; orientation_baseline = '
      + 'opportunities whose T stands up',
  ],
  qualify: {
    rules: [
      `other_page: another technique page's window (${OTHER_PAGES.join(', ')}; any variant, either hand) fires at the same T, so the T is that page's`,
      `opener_route: the round is a case of an opener route page (${ROUTE_ARTEFACTS.join(', ')}) that matched a bag-2 board, and the T locks within ${ROUTE_LOCKS} locks after that match, so the T is the route's own continuation`,
      'qualifies iff neither applies; the donation happened at every hit either way',
    ],
    check: donationQualifier(OPENERS, `${REPO}/analysis`),
  },
  lists: (hits, name) => ({
    basicdonating_hits: hits.map(h => `${name(h)} ${tag(h)}`),
    payoff_not_fired: hits.filter(h => !h.followup.fired)
      .map(h => `${name(h)} lock ${h.lock} (${h.followup.reason}${h.followup.lock !== null ? ` at lock ${h.followup.lock}` : ''})`),
    garbage_in_window: hits.filter(h => h.garbage_in_window).map(h => `${name(h)} lock ${h.lock}`),
    basicdonating_in_opener: hits.filter(h => h.in_opener).map(h => `${name(h)} lock ${h.lock}`),
  }),
};

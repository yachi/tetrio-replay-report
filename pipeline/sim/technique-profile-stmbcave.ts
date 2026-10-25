/**
 * The STMB Cave technique profile for `technique-facts.ts`: shiwehi.com's `template/stmbcave.php`, the
 * second mid-game technique page. Data only; every rule is the shared matcher's, and the shape (the
 * agreement-box window, the flat T's cells, the follow-up slot) is the gated transcription
 * `pipeline/openers/stmbcave-technique.json`.
 *
 * No `crossRoute`: the shared cross-route lines are worded for STSD. The cross-check against the SDPC
 * Spin rounds that reached their STMB Cave (`sdpcspin-facts.json`, node `3.first.cave`) and against the
 * opener metric's own cave count (`opener-facts.json` `stmb_cave`) is made in `stmbcave.test.ts`.
 */
import type { TechniqueProfile } from './technique-profile.ts';
import { QUALIFY_OPTIONS, techniqueQualifier } from './technique-qualify.ts';
import { DPC_LOCKS } from './shachikutrain-qualify.ts';
import { WHOLE_SHAPE_RULE, withWholeShape } from './technique-wholeshape.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

export const STMBCAVE: TechniqueProfile = {
  key: 'stmbcave',
  tag: 'stmbcave',
  transcriptionPath: `${OPENERS}/stmbcave-technique.json`,
  artefactPath: `${REPO}/analysis/stmbcave-facts.json`,
  hashFiles: {
    classifier: [`${SIM}/technique-facts.ts`, `${SIM}/technique-wholeshape.ts`, `${SIM}/technique-profile.ts`, `${SIM}/technique-profile-stmbcave.ts`,
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
      + 'the verified prefix, passing the reconstruction check), whether the STMB Cave page\'s local shape stood '
      + 'around it: the lock\'s cells are the page\'s flat T pointing down (as drawn or mirrored) and every cell '
      + 'of the window around it — the two rows the TSD clears and the row under them, from two columns behind '
      + 'the nub to the cave\'s far wall — is filled or empty as drawn. The opportunity is a full T-spin Double; '
      + 'every hit is followed to the next T lock to see whether the second TSD the page draws under the cave fired.',
    notEligible: 'simulator output: which local shape a T went into is read off the vendored Triangle '
      + 'engine\'s boards, and nothing on the corpus side has a second implementation of it. No claim id, '
      + 'no badge, no figure in a report.',
    caveat: 'garbage is read as FILLED inside the window, and its hole columns are the engine\'s seeded-RNG '
      + 'columns, which disagree with the recorded ones (oracle-source.ts); a hit with garbage in its window '
      + 'is named in garbage_in_window for that reason. At a full TSD the window\'s top two rows are entailed by '
      + 'the clear (NaiveClauseForced, RoofForced): only the T\'s orientation and the cave row discriminate. '
      + 'Counts only, always N / M with the denominator.',
  },
  rules: () => [
    'opportunity: a T lock with spin "full" clearing 2 lines, at a 0-based lock index <= the verified index, '
      + 'whose board-before plus its cells makes exactly the rows the engine recorded clearing (the '
      + 'reconstruction check, counted exactly as opener-facts.json donation.check counts it)',
    'match: the lock\'s cells equal the variant\'s flat T under one translation (mirrored: columns '
      + 'reflected in the window), and every other window cell is filled (a piece or garbage) or empty as '
      + 'the page draws it; colour is never compared; cells outside the window are not read',
    'mirrored is tried only when as-drawn fails; a window leaving the board is no match (window_off_board)',
    'follow-up: the page\'s second-TSD slot under the cave carried through every clear and garbage insertion '
      + 'to the next T lock, each step verified against the engine\'s next board; fired iff that T is the slot '
      + 'and a scored full TSD',
    'controls: the same window at scored TSS, TST, mini TSS and mini TSD; ablations no_must_empty, no_roof '
      + 'and t_overlap at the opportunity; orientation_baseline = opportunities whose T stands up',
  ],
  qualify: {
    rules: [
      `fragment: a key cell — the S hooked over the gap, beside the T's far arm (feature.spin row 2, columns 5-6): the piece both of the page's builds place there; the transcription has no roof (the nub row is the cave's roof) — belongs to a piece not all four of whose cells are on the board before the T (a line clear cut it)`,
      'garbage_in_shape: a key cell is garbage',
      'shape_cell_empty: a key cell is empty (the window requires it filled, so only a weakened window can admit this)',
      `dpc: the board is empty after one of the ${DPC_LOCKS} locks before the T, the T itself, or one of the ${DPC_LOCKS} after it (the DPC setup)`,
      'ownership_unverified: a lock before the T has a row map the digest could not verify, so its pieces cannot be told apart',
      WHOLE_SHAPE_RULE,
      'qualifies iff none applies; the shape stood at every hit either way',
    ],
    check: withWholeShape(`${OPENERS}/stmbcave-technique.json`,
                          techniqueQualifier(`${OPENERS}/stmbcave-technique.json`, QUALIFY_OPTIONS.stmbcave)),
  },
  lists: (hits, name) => ({
    stmbcave_hits: hits.map(h => `${name(h)} lock ${h.lock}${h.mirrored ? ' (mirrored)' : ''}`),
    followup_not_fired: hits.filter(h => !h.followup.fired)
      .map(h => `${name(h)} lock ${h.lock} (${h.followup.reason}${h.followup.lock !== null ? ` at lock ${h.followup.lock}` : ''})`),
    garbage_in_window: hits.filter(h => h.garbage_in_window).map(h => `${name(h)} lock ${h.lock}`),
    stmbcave_in_opener: hits.filter(h => h.in_opener).map(h => `${name(h)} lock ${h.lock}`),
  }),
};

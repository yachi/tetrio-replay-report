/**
 * The Double Dagger technique profile for `technique-facts.ts`: shiwehi.com's `template/doubledagger.php`
 * (ダブルダガー), the fourth mid-game technique page. Data only; every rule is the shared matcher's, and the
 * shape (the bounding-box window, the flat T's cells, the follow-up slot) is the gated transcription
 * `pipeline/openers/doubledagger-technique.json`.
 *
 * The opportunity is a full T-spin Double, as STSD's, STMB Cave's and Imperial Cross's: the T laid flat,
 * pointing down, into the upper of two stacked TSD slots, under an overhang over its left end (mirrored:
 * its right end). Its clear drops the overhang onto the lower slot, which is the second TSD.
 *
 * No `crossRoute`: the shared cross-route lines are worded for STSD. The cross-check against the SDPC Spin
 * rounds (`sdpcspin-facts.json`; the second C-Spin build's bag-5 boards are the harddrop drawings the window
 * fires on) is made in `doubledagger.test.ts`.
 */
import type { TechniqueProfile } from './technique-profile.ts';
import { QUALIFY_OPTIONS, techniqueQualifier } from './technique-qualify.ts';
import { DPC_LOCKS } from './shachikutrain-qualify.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

export const DOUBLEDAGGER: TechniqueProfile = {
  key: 'doubledagger',
  tag: 'doubledagger',
  transcriptionPath: `${OPENERS}/doubledagger-technique.json`,
  artefactPath: `${REPO}/analysis/doubledagger-facts.json`,
  hashFiles: {
    classifier: [`${SIM}/technique-facts.ts`, `${SIM}/technique-profile.ts`, `${SIM}/technique-profile-doubledagger.ts`,
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
      + 'the verified prefix, passing the reconstruction check), whether the Double Dagger page\'s local shape '
      + 'stood around it: the lock\'s cells are the page\'s flat T pointing down (as drawn, or mirrored) and every '
      + 'cell of the window around it — the overhang row above the T, the two rows the TSD clears and the lower '
      + 'TSD slot directly under them — is filled or empty as drawn. The opportunity is a full T-spin Double; every '
      + 'hit is followed to the next T lock to see whether the second TSD the page draws in the lower slot fired.',
    notEligible: 'simulator output: which local shape a T went into is read off the vendored Triangle '
      + 'engine\'s boards, and nothing on the corpus side has a second implementation of it. No claim id, '
      + 'no badge, no figure in a report.',
    caveat: 'garbage is read as FILLED inside the window, and its hole columns are the engine\'s seeded-RNG '
      + 'columns, which disagree with the recorded ones (oracle-source.ts); a hit with garbage in its window '
      + 'is named in garbage_in_window for that reason. At a full TSD the two cleared rows are entailed by the '
      + 'clear (NaiveClauseForced): the T\'s orientation, the overhang row and the lower slot discriminate. The '
      + 'page\'s line-between feature (a row between the two slots) is not this window. Counts only, always N / M '
      + 'with the denominator.',
  },
  rules: () => [
    'opportunity: a T lock with spin "full" clearing 2 lines, at a 0-based lock index <= the verified index, '
      + 'whose board-before plus its cells makes exactly the rows the engine recorded clearing (the '
      + 'reconstruction check, counted exactly as opener-facts.json donation.check counts it)',
    'match: the lock\'s cells equal the variant\'s flat T under one translation (mirrored: columns '
      + 'reflected in the window), and every other window cell is filled (a piece or garbage) or empty as '
      + 'the page draws it; colour is never compared; cells outside the window are not read',
    'mirrored is tried only when as-drawn fails; a window leaving the board is no match (window_off_board)',
    'follow-up: the page\'s second-TSD slot (the lower slot, under the dropped overhang) carried through every '
      + 'clear and garbage insertion to the next T lock, each step verified against the engine\'s next board; '
      + 'fired iff that T is the slot and a scored full TSD',
    'controls: the same window at scored TSS, TST, mini TSS and mini TSD; ablations no_must_empty, no_roof '
      + 'and t_overlap at the opportunity; orientation_baseline = opportunities whose T stands up',
  ],
  qualify: {
    rules: [
      `fragment: a key cell — the overhang over the upper slot (the transcription's roof_cells): the S or Z every build places — belongs to a piece not all four of whose cells are on the board before the T (a line clear cut it)`,
      'garbage_in_shape: a key cell is garbage',
      'shape_cell_empty: a key cell is empty (the window requires it filled, so only a weakened window can admit this)',
      `dpc: the board is empty after one of the ${DPC_LOCKS} locks before the T, the T itself, or one of the ${DPC_LOCKS} after it (the DPC setup)`,
      'ownership_unverified: a lock before the T has a row map the digest could not verify, so its pieces cannot be told apart',
      'qualifies iff none applies; the shape stood at every hit either way',
    ],
    check: techniqueQualifier(`${OPENERS}/doubledagger-technique.json`, QUALIFY_OPTIONS.doubledagger),
  },
  lists: (hits, name) => ({
    doubledagger_hits: hits.map(h => `${name(h)} lock ${h.lock}${h.mirrored ? ' (mirrored)' : ''}`),
    followup_not_fired: hits.filter(h => !h.followup.fired)
      .map(h => `${name(h)} lock ${h.lock} (${h.followup.reason}${h.followup.lock !== null ? ` at lock ${h.followup.lock}` : ''})`),
    garbage_in_window: hits.filter(h => h.garbage_in_window).map(h => `${name(h)} lock ${h.lock}`),
    doubledagger_in_opener: hits.filter(h => h.in_opener).map(h => `${name(h)} lock ${h.lock}`),
  }),
};

/**
 * The Cave TSS to TST technique profile for `technique-facts.ts`: harddrop's T-Spin Triple Setups page, its
 * 「Cave TSS to TST」 boards (Garbage Manipulation), the thirteenth mid-game technique page, added at yachi's request
 * on 2026-11-12 from a short (WylieCan'tGame, `vr1N137z038`) playing it. Data only; every rule is the shared
 * matcher's, and the shape (the agreement-box window, the stood T's cells, the follow-up slot) is the gated
 * transcription `pipeline/openers/cavetsstst-technique.json`.
 *
 * An L laid over a one-column cave at the wall: a T stood up into the cave, nub toward the open side, clears the one
 * row under it (a T-spin Single), and its remnant becomes the step a second T stands on: the TST beside it, one
 * column further in, roofed by the stack built over it. The engine credits the first spin as a MINI T-spin Single
 * (only one of the two corners on the nub side is filled; the transcription's `credit: 'mini'`, its corners
 * re-counted by the gate), so the opportunity is a mini TSS, and the follow-up the full TST.
 *
 * No `crossRoute`: no route page draws it (the gate measured the window fires on no routes board).
 */
import type { TechniqueProfile } from './technique-profile.ts';
import { QUALIFY_OPTIONS, techniqueQualifier } from './technique-qualify.ts';
import { DPC_LOCKS } from './shachikutrain-qualify.ts';
import { WHOLE_SHAPE_RULE, withWholeShape } from './technique-wholeshape.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

export const CAVETSSTST: TechniqueProfile = {
  key: 'cavetsstst',
  tag: 'cavetsstst',
  transcriptionPath: `${OPENERS}/cavetsstst-technique.json`,
  artefactPath: `${REPO}/analysis/cavetsstst-facts.json`,
  hashFiles: {
    classifier: [`${SIM}/technique-facts.ts`, `${SIM}/technique-wholeshape.ts`, `${SIM}/technique-profile.ts`, `${SIM}/technique-profile-cavetsstst.ts`,
                 `${SIM}/emit-technique-facts.ts`, `${SIM}/route-facts.ts`,
                 `${SIM}/technique-qualify.ts`, `${SIM}/shachikutrain-qualify.ts`],
  },
  opportunity: { spin: 'mini', lines: 1 },
  controlSpins: [
    { name: 'TSS', kind: { spin: 'full', lines: 1 } },
    { name: 'TSD', kind: { spin: 'full', lines: 2 } },
    { name: 'TST', kind: { spin: 'full', lines: 3 } },
    { name: 'mini_TSD', kind: { spin: 'mini', lines: 2 } },
  ],
  anchor: 'spin_t_cells',
  garbage: 'filled',
  artefact: {
    schema: 'technique-facts/1',
    means: 'For every scored T-spin in the corpus (a T with an engine spin credit that cleared lines, inside '
      + 'the verified prefix, passing the reconstruction check), whether harddrop\'s Cave TSS to TST local shape '
      + 'stood around it: the lock\'s cells are the page\'s T stood up in a one-column cave, nub toward the open '
      + 'side (as drawn, or mirrored), and every cell of the window around it — the L laid over the cave, the '
      + 'cave\'s wall, the open cells beside the T where the TST goes and the row the T clears — is filled or empty '
      + 'as drawn. The opportunity is a MINI T-spin Single (the engine\'s credit for this slot); every hit is '
      + 'followed to the next T lock to see whether the TST the page draws next fired.',
    notEligible: 'simulator output: which local shape a T went into is read off the vendored Triangle '
      + 'engine\'s boards, and nothing on the corpus side has a second implementation of it. No claim id, '
      + 'no badge, no figure in a report.',
    caveat: 'garbage is read as FILLED inside the window, and its hole columns are the engine\'s seeded-RNG '
      + 'columns, never observed directly (oracle-source.ts); a hit with garbage in its window is named in '
      + 'garbage_in_window for that reason. The row the T clears is entailed by the clear (NaiveClauseForced): the '
      + 'overhang above and the open cells beside the T discriminate. Counts only, always N / M with the denominator.',
  },
  rules: () => [
    'opportunity: a T lock with spin "mini" clearing 1 line, at a 0-based lock index <= the verified index, '
      + 'whose board-before plus its cells makes exactly the rows the engine recorded clearing (the '
      + 'reconstruction check, counted exactly as opener-facts.json donation.check counts it)',
    'match: the lock\'s cells equal the variant\'s stood T under one translation (mirrored: columns '
      + 'reflected in the window), and every other window cell is filled (a piece or garbage) or empty as '
      + 'the page draws it; colour is never compared; cells outside the window are not read',
    'mirrored is tried only when as-drawn fails; a window leaving the board is no match (window_off_board)',
    'follow-up: the page\'s TST slot (a second T stood up one column further from the wall, nub toward the first '
      + 'T\'s remnant) carried through every clear and garbage insertion to the next T lock, each step verified '
      + 'against the engine\'s next board; fired iff that T is the slot and a scored full TST',
    'controls: the same window at scored full TSS, TSD, TST and mini TSD; ablations no_must_empty, no_roof '
      + 'and t_overlap at the opportunity; orientation_baseline = opportunities whose T stands up',
  ],
  qualify: {
    rules: [
      `fragment: a key cell — the L laid over the cave, which both drawings place before the TSS — belongs to a piece not all four of whose cells are on the board before the T (a line clear cut it)`,
      'garbage_in_shape: a key cell is garbage',
      'shape_cell_empty: a key cell is empty (the window requires it filled, so only a weakened window can admit this)',
      `dpc: the board is empty after one of the ${DPC_LOCKS} locks before the T, the T itself, or one of the ${DPC_LOCKS} after it (the DPC setup)`,
      'ownership_unverified: a lock before the T has a row map the digest could not verify, so its pieces cannot be told apart',
      WHOLE_SHAPE_RULE,
      'qualifies iff none applies; the shape stood at every hit either way',
    ],
    check: withWholeShape(`${OPENERS}/cavetsstst-technique.json`,
                          techniqueQualifier(`${OPENERS}/cavetsstst-technique.json`, QUALIFY_OPTIONS.cavetsstst)),
  },
  lists: (hits, name) => ({
    cavetsstst_hits: hits.map(h => `${name(h)} lock ${h.lock}${h.mirrored ? ' (mirrored)' : ''}`),
    followup_not_fired: hits.filter(h => !h.followup.fired)
      .map(h => `${name(h)} lock ${h.lock} (${h.followup.reason}${h.followup.lock !== null ? ` at lock ${h.followup.lock}` : ''})`),
    garbage_in_window: hits.filter(h => h.garbage_in_window).map(h => `${name(h)} lock ${h.lock}`),
    cavetsstst_in_opener: hits.filter(h => h.in_opener).map(h => `${name(h)} lock ${h.lock}`),
  }),
};

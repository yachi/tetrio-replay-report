/**
 * The STSD (Super T-Spin Double) technique profile for `technique-facts.ts`: shiwehi.com's
 * `template/stsd.php`, the first mid-game technique page. Data only; every rule is the shared
 * matcher's, and the shape (window, T cells, follow-up slot) is the gated transcription
 * `pipeline/openers/stsd-technique.json`.
 */
import type { TechniqueProfile } from './technique-profile.ts';
import { QUALIFY_OPTIONS, techniqueQualifier } from './technique-qualify.ts';
import { DPC_LOCKS } from './shachikutrain-qualify.ts';
import type { CrossRoute } from './technique-facts.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

export const STSD: TechniqueProfile & { crossRoute: CrossRoute } = {
  key: 'stsd',
  tag: 'stsd',
  transcriptionPath: `${OPENERS}/stsd-technique.json`,
  artefactPath: `${REPO}/analysis/stsd-facts.json`,
  hashFiles: {
    classifier: [`${SIM}/technique-facts.ts`, `${SIM}/technique-profile.ts`, `${SIM}/technique-profile-stsd.ts`,
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
  crossRoute: {
    key: 'sdpcspin:3.first.cave',
    artefact: `${REPO}/analysis/sdpcspin-facts.json`,
    node: '3.first.cave',
    note: 'the rounds whose SDPC Spin route reached its STMB Cave (harddrop draws the STSD as that '
      + 'branch\'s next step, 3.first.cave.stsd, which no corpus round reaches as a whole board): did an '
      + 'STSD hit follow inside the drawn continuation? Measured, each miss with its reason; a round whose '
      + 'node or continuation lies past its verified prefix is named and kept out of the denominator.',
    continuationLastLock: 34,
    continuationNote: 'OUR READING: harddrop draws the STSD (3.first.cave.stsd) as bag 5 of that route; at seven '
      + 'locks a bag with no hold, bag 5 is 0-based locks 28-34, so the continuation is the locks after the node '
      + 'through lock 34. An STSD hit later in the round is recorded as later_hit_lock and not counted.',
  },
  artefact: {
    schema: 'technique-facts/1',
    means: 'For every scored T-spin in the corpus (a T with an engine spin credit that cleared lines, inside '
      + 'the verified prefix, passing the reconstruction check), whether the STSD page\'s local shape stood '
      + 'around it: the lock\'s cells are the page\'s stood T (as drawn or mirrored) and every cell of the '
      + 'page\'s window around it is filled or empty as drawn. The opportunity is a full T-spin Double; '
      + 'every hit is followed to the next T lock to see whether the second TSD the page promises fired.',
    notEligible: 'simulator output: which local shape a T went into is read off the vendored Triangle '
      + 'engine\'s boards, and nothing on the corpus side has a second implementation of it. No claim id, '
      + 'no badge, no figure in a report.',
    caveat: 'garbage is read as FILLED inside the window, and its hole columns are the engine\'s seeded-RNG '
      + 'columns, which disagree with the recorded ones (oracle-source.ts); a hit with garbage in its window '
      + 'is named in garbage_in_window for that reason. Counts only, always N / M with the denominator.',
  },
  rules: () => [
    'opportunity: a T lock with spin "full" clearing 2 lines, at a 0-based lock index <= the verified index, '
      + 'whose board-before plus its cells makes exactly the rows the engine recorded clearing (the '
      + 'reconstruction check, counted exactly as opener-facts.json donation.check counts it)',
    'match: the lock\'s cells equal the variant\'s T cells under one translation (mirrored: columns '
      + 'reflected in the window), and every other window cell is filled (a piece or garbage) or empty as '
      + 'the page draws it; colour is never compared; cells outside the window are not read',
    'mirrored is tried only when as-drawn fails; a window leaving the board is no match (window_off_board)',
    'follow-up: the page\'s second-TSD slot carried through every clear and garbage insertion to the next '
      + 'T lock, each step verified against the engine\'s next board; fired iff that T is the slot and a '
      + 'scored full TSD',
    'controls: the same window at scored TSS, TST, mini TSS and mini TSD; ablations no_must_empty, no_roof '
      + 'and t_overlap at the opportunity; orientation_baseline = opportunities whose T stands up',
  ],
  qualify: {
    rules: [
      `fragment: a key cell — the overhang over the well (basic.spin rows 1, columns 2-3): the cells every build draws as its roof piece (an L, a Z or an I); the cell under it the roof.i build draws as stack, so it is not required fresh — belongs to a piece not all four of whose cells are on the board before the T (a line clear cut it)`,
      'garbage_in_shape: a key cell is garbage',
      'shape_cell_empty: a key cell is empty (the window requires it filled, so only a weakened window can admit this)',
      `dpc: the board is empty after one of the ${DPC_LOCKS} locks before the T, the T itself, or one of the ${DPC_LOCKS} after it (the DPC setup)`,
      'ownership_unverified: a lock before the T has a row map the digest could not verify, so its pieces cannot be told apart',
      'qualifies iff none applies; the shape stood at every hit either way',
    ],
    check: techniqueQualifier(`${OPENERS}/stsd-technique.json`, QUALIFY_OPTIONS.stsd),
  },
  lists: (hits, name) => ({
    stsd_hits: hits.map(h => `${name(h)} lock ${h.lock}${h.mirrored ? ' (mirrored)' : ''}`),
    followup_not_fired: hits.filter(h => !h.followup.fired)
      .map(h => `${name(h)} lock ${h.lock} (${h.followup.reason}${h.followup.lock !== null ? ` at lock ${h.followup.lock}` : ''})`),
    garbage_in_window: hits.filter(h => h.garbage_in_window).map(h => `${name(h)} lock ${h.lock}`),
    stsd_in_opener: hits.filter(h => h.in_opener).map(h => `${name(h)} lock ${h.lock}`),
  }),
};

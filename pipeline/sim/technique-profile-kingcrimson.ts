/**
 * The King Crimson technique profile for `technique-facts.ts`: harddrop's `King_Crimson` page (shiwehi.com has no
 * King Crimson page), the twelfth mid-game technique page. Data only; every rule is the shared matcher's, and the
 * shape (the agreement-box window, the stood T's cells, the follow-up slot) is the gated transcription
 * `pipeline/openers/kingcrimson-technique.json`.
 *
 * 「a T-Spin Triple layered on top of a Super T-Spin Double」: a one-column well under an overhang, a stood-T TST
 * slot directly above an STSD slot. The opportunity is the FIRST spin, a full T-spin TRIPLE with the T stood up
 * (the only page whose opportunity is not a TSD); the TSD is one of the control spins in its place. The follow-up
 * is the STSD: a second T stood up into the lower slot, three rows down, which the engine credits as a full
 * T-spin Double (`followup.lines` 2). The matcher reads both through the transcription's `spin` / `lines` and the
 * profile's `opportunity`, so nothing shared changed.
 *
 * No `crossRoute`: no route page draws a King Crimson (the gate measured the window fires on no routes board).
 * Every follow-up that fires is a hit of the STSD page; `kingcrimson.test.ts` measures and pins that.
 */
import type { TechniqueProfile } from './technique-profile.ts';
import { QUALIFY_OPTIONS, techniqueQualifier } from './technique-qualify.ts';
import { DPC_LOCKS } from './shachikutrain-qualify.ts';
import { WHOLE_SHAPE_RULE, withWholeShape } from './technique-wholeshape.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

export const KINGCRIMSON: TechniqueProfile = {
  key: 'kingcrimson',
  tag: 'kingcrimson',
  transcriptionPath: `${OPENERS}/kingcrimson-technique.json`,
  artefactPath: `${REPO}/analysis/kingcrimson-facts.json`,
  hashFiles: {
    classifier: [`${SIM}/technique-facts.ts`, `${SIM}/technique-wholeshape.ts`, `${SIM}/technique-profile.ts`, `${SIM}/technique-profile-kingcrimson.ts`,
                 `${SIM}/emit-technique-facts.ts`, `${SIM}/route-facts.ts`,
                 `${SIM}/technique-qualify.ts`, `${SIM}/shachikutrain-qualify.ts`],
  },
  opportunity: { spin: 'full', lines: 3 },
  controlSpins: [
    { name: 'TSS', kind: { spin: 'full', lines: 1 } },
    { name: 'TSD', kind: { spin: 'full', lines: 2 } },
    { name: 'mini_TSS', kind: { spin: 'mini', lines: 1 } },
    { name: 'mini_TSD', kind: { spin: 'mini', lines: 2 } },
  ],
  anchor: 'spin_t_cells',
  garbage: 'filled',
  artefact: {
    schema: 'technique-facts/1',
    means: 'For every scored T-spin in the corpus (a T with an engine spin credit that cleared lines, inside '
      + 'the verified prefix, passing the reconstruction check), whether harddrop\'s King Crimson local shape '
      + 'stood around it: the lock\'s cells are the page\'s T stood up, nub toward the open side (as drawn, or '
      + 'mirrored), and every cell of the window around it — the well\'s wall, the overhang over the well, the TST '
      + 'slot, the STSD slot three rows under it and the wall on the open side — is filled or empty as drawn. The '
      + 'opportunity is a full T-spin Triple; every hit is followed to the next T lock to see whether the STSD the '
      + 'page draws next fired.',
    notEligible: 'simulator output: which local shape a T went into is read off the vendored Triangle '
      + 'engine\'s boards, and nothing on the corpus side has a second implementation of it. No claim id, '
      + 'no badge, no figure in a report.',
    caveat: 'garbage is read as FILLED inside the window, and its hole columns are the engine\'s seeded-RNG '
      + 'columns, which disagree with the recorded ones (oracle-source.ts); a hit with garbage in its window '
      + 'is named in garbage_in_window for that reason. At a full TST the three cleared rows are entailed by the '
      + 'clear (NaiveClauseForced): the overhang above and the STSD slot below discriminate. Counts only, always '
      + 'N / M with the denominator.',
  },
  rules: () => [
    'opportunity: a T lock with spin "full" clearing 3 lines, at a 0-based lock index <= the verified index, '
      + 'whose board-before plus its cells makes exactly the rows the engine recorded clearing (the '
      + 'reconstruction check, counted exactly as opener-facts.json donation.check counts it)',
    'match: the lock\'s cells equal the variant\'s stood T under one translation (mirrored: columns '
      + 'reflected in the window), and every other window cell is filled (a piece or garbage) or empty as '
      + 'the page draws it; colour is never compared; cells outside the window are not read',
    'mirrored is tried only when as-drawn fails; a window leaving the board is no match (window_off_board)',
    'follow-up: the page\'s STSD slot (a second T stood up three rows under the TST\'s, nub toward the open side, '
      + 'every cell under the TST\'s cleared rows) carried through every clear and garbage insertion to the next T '
      + 'lock, each step verified against the engine\'s next board; fired iff that T is the slot and a scored full TSD',
    'controls: the same window at scored TSS, TSD, mini TSS and mini TSD; ablations no_must_empty, no_roof '
      + 'and t_overlap at the opportunity; orientation_baseline = opportunities whose T stands up',
  ],
  qualify: {
    rules: [
      `fragment: a key cell — the overhang over the well, the cell every drawing of the shape roofs the well with — belongs to a piece not all four of whose cells are on the board before the T (a line clear cut it)`,
      'garbage_in_shape: a key cell is garbage',
      'shape_cell_empty: a key cell is empty (the window requires it filled, so only a weakened window can admit this)',
      `dpc: the board is empty after one of the ${DPC_LOCKS} locks before the T, the T itself, or one of the ${DPC_LOCKS} after it (the DPC setup)`,
      'ownership_unverified: a lock before the T has a row map the digest could not verify, so its pieces cannot be told apart',
      WHOLE_SHAPE_RULE,
      'qualifies iff none applies; the shape stood at every hit either way',
    ],
    check: withWholeShape(`${OPENERS}/kingcrimson-technique.json`,
                          techniqueQualifier(`${OPENERS}/kingcrimson-technique.json`, QUALIFY_OPTIONS.kingcrimson)),
  },
  lists: (hits, name) => ({
    kingcrimson_hits: hits.map(h => `${name(h)} lock ${h.lock}${h.mirrored ? ' (mirrored)' : ''}`),
    followup_not_fired: hits.filter(h => !h.followup.fired)
      .map(h => `${name(h)} lock ${h.lock} (${h.followup.reason}${h.followup.lock !== null ? ` at lock ${h.followup.lock}` : ''})`),
    garbage_in_window: hits.filter(h => h.garbage_in_window).map(h => `${name(h)} lock ${h.lock}`),
    kingcrimson_in_opener: hits.filter(h => h.in_opener).map(h => `${name(h)} lock ${h.lock}`),
  }),
};

/**
 * The 千鳥格子 (Cut Copy) technique profile for `technique-facts.ts`: shiwehi.com's `template/cutcopy.php`, the
 * sixth mid-game technique page. Data only; every rule is the shared matcher's, and the shape (the agreement-box
 * window, the flat T's cells, the follow-up slot) is the gated transcription
 * `pipeline/openers/cutcopy-technique.json`.
 *
 * The opportunity is a full T-spin Double, as on the five earlier pages: the T laid flat, pointing down, into the
 * inner of two TSD slots interleaved one column apart, under a roof over its right end (mirrored: its left end).
 * Its two cleared rows join the outer slot's arms row to its nub cell, which is the second TSD: the follow-up slot's
 * cells are split by the clear (three above it, one under it) until the first TSD joins them, which the matcher's
 * row map already does (BT砲's TST slot is split the same way), so nothing shared changed.
 *
 * A SECOND VARIANT, harddrop's (`uncut`): harddrop's second generic type, 「Uncut copy」, where the whole second TSD
 * slot lies under the first T's two cleared rows (one column toward the open side) rather than being split by them.
 * The same flat T, the same opportunity (a full TSD), its own agreement-box window and follow-up slot, both in the
 * gated transcription (its board an `external` node, harddrop's own drawing in occupancy). The two windows clash on a
 * cell, so no lock is a hit of both; the matcher measures each variant at the TSD, as 欄干's two variants are measured.
 *
 * No `crossRoute`: no route page draws a Cut Copy (the gate measured the windows fire on no routes board).
 */
import type { TechniqueProfile } from './technique-profile.ts';
import { QUALIFY_OPTIONS, techniqueQualifier } from './technique-qualify.ts';
import { DPC_LOCKS } from './shachikutrain-qualify.ts';

const SIM = import.meta.dir;
/** a hit's variant, for the second type only: the first type's entries read as they always have */
const vtag = (h: any) => h.variant === 'cutcopy' ? '' : `${h.variant}: `;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

export const CUTCOPY: TechniqueProfile = {
  key: 'cutcopy',
  tag: 'cutcopy',
  transcriptionPath: `${OPENERS}/cutcopy-technique.json`,
  artefactPath: `${REPO}/analysis/cutcopy-facts.json`,
  hashFiles: {
    classifier: [`${SIM}/technique-facts.ts`, `${SIM}/technique-profile.ts`, `${SIM}/technique-profile-cutcopy.ts`,
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
      + 'the verified prefix, passing the reconstruction check), whether a Cut Copy\'s local shape stood around it, '
      + 'in either of two variants: cutcopy, the 千鳥格子 page\'s (the lock\'s cells the flat T pointing down, as drawn '
      + 'or mirrored, and every cell of the window around it — the outer slot\'s arms row above the T with the wall '
      + 'beside it and the roof over the T\'s far end, the overhang over the outer slot (which must already stand at '
      + 'the first TSD), the two rows the TSD clears and the outer slot\'s nub cell under them — filled or empty as '
      + 'drawn); and uncut, harddrop\'s second generic type (the same flat T, the row above '
      + 'it, the two rows it clears, and the whole second TSD slot under them). The opportunity is a full T-spin '
      + 'Double for both; every hit is followed to the next T lock to see whether the second TSD fired in its slot.',
    notEligible: 'simulator output: which local shape a T went into is read off the vendored Triangle '
      + 'engine\'s boards, and nothing on the corpus side has a second implementation of it. No claim id, '
      + 'no badge, no figure in a report.',
    caveat: 'garbage is read as FILLED inside the window, and its hole columns are the engine\'s seeded-RNG '
      + 'columns, which disagree with the recorded ones (oracle-source.ts); a hit with garbage in its window '
      + 'is named in garbage_in_window for that reason. At a full TSD the two cleared rows are entailed by the '
      + 'clear (NaiveClauseForced): the T\'s orientation and the rows above and below them discriminate. The page\'s '
      + 'T-hole build with its Z placed after the first T-spin is not this window (the Z is the outer slot\'s wall and '
      + 'its overhang): a Cut Copy whose overhang goes in after the first TSD is no hit. '
      + 'The uncut window is harddrop\'s drawings\' agreement box; shiwehi.com draws no second type. '
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
    'follow-up: the second-TSD slot (cutcopy: the outer slot, split by the first TSD\'s two cleared rows until that '
      + 'TSD joins it; uncut: the whole slot under the cleared rows) carried through every clear and garbage '
      + 'insertion to the next T lock, each step verified against the engine\'s next board; fired iff that T is the '
      + 'slot and a scored full TSD',
    'controls, per variant: the same window at scored TSS, TST, mini TSS and mini TSD; ablations no_must_empty, '
      + 'no_roof and t_overlap at the opportunity; orientation_baseline = opportunities whose T stands up',
  ],
  qualify: {
    rules: [
      `fragment: a key cell — cutcopy: the roof over the T's end, the outer slot's wall and the overhang over the outer slot (roof_cells and window_extra), which every build places; uncut: the overhang over the T's right arm (uncut.spin row 1, column 4) — the other filled cells of that row harddrop draws as plain stack — belongs to a piece not all four of whose cells are on the board before the T (a line clear cut it)`,
      'garbage_in_shape: a key cell is garbage',
      'shape_cell_empty: a key cell is empty (the window requires it filled, so only a weakened window can admit this)',
      `dpc: the board is empty after one of the ${DPC_LOCKS} locks before the T, the T itself, or one of the ${DPC_LOCKS} after it (the DPC setup)`,
      'ownership_unverified: a lock before the T has a row map the digest could not verify, so its pieces cannot be told apart',
      'qualifies iff none applies; the shape stood at every hit either way',
    ],
    check: techniqueQualifier(`${OPENERS}/cutcopy-technique.json`, QUALIFY_OPTIONS.cutcopy),
  },
  lists: (hits, name) => {
    const of = (v: string) => hits.filter(h => h.variant === v);
    const tag = (h: any) => h.variant === 'cutcopy' ? '' : ` (${h.variant})`;
    return {
      cutcopy_hits: of('cutcopy').map(h => `${name(h)} lock ${h.lock}${h.mirrored ? ' (mirrored)' : ''}`),
      uncut_hits: of('uncut').map(h => `${name(h)} lock ${h.lock}${h.mirrored ? ' (mirrored)' : ''}`),
      followup_not_fired: hits.filter(h => !h.followup.fired)
        .map(h => `${name(h)} lock ${h.lock} (${vtag(h)}${h.followup.reason}${h.followup.lock !== null ? ` at lock ${h.followup.lock}` : ''})`),
      garbage_in_window: hits.filter(h => h.garbage_in_window).map(h => `${name(h)} lock ${h.lock}${tag(h)}`),
      cutcopy_in_opener: hits.filter(h => h.in_opener).map(h => `${name(h)} lock ${h.lock}${tag(h)}`),
      /** a hit whose follow-up fired at a lock that is itself a hit: two Cut Copies in a row (Tetrisちゃんねる's 江戸城, harddrop's
       *  repeats) */
      followup_is_a_hit: hits.filter(h => h.followup.fired && hits.some(x => x.session === h.session && x.file === h.file
          && x.round_index0 === h.round_index0 && x.player === h.player && x.lock === h.followup.lock))
        .map(h => {
          const x = hits.find(y => y.session === h.session && y.file === h.file && y.round_index0 === h.round_index0
            && y.player === h.player && y.lock === h.followup.lock)!;
          return `${name(h)} lock ${h.lock}${tag(h)} -> lock ${x.lock}${tag(x)}`;
        }),
    };
  },
};

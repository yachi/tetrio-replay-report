/**
 * The 社畜トレイン (Shachiku Train) technique profile for `technique-facts.ts`: shiwehi.com's
 * `template/shachikutrain.php`, the seventh mid-game technique page. Data only; every rule is the shared matcher's,
 * and the shape (the agreement-box window, the flat T's cells, the follow-up slot) is the gated transcription
 * `pipeline/openers/shachikutrain-technique.json`.
 *
 * The opportunity is a full T-spin Double, as on the six earlier pages: the T laid flat, pointing down, into the slot
 * an S one column off a wall and an L hung over its far end make, under the wall's roof over its near end (mirrored:
 * the other end). Its two cleared rows drop the row above the slot onto the cell beside the S's foot, which is the
 * second TSD: the follow-up slot's cells are split by the clear (its arms above, its nub below) until the first TSD
 * joins them, which the matcher's row map already does (BT砲's TST and 千鳥格子's second TSD are split the same way),
 * so nothing shared changed.
 *
 * No `crossRoute`: the one routes board the gate measured the window firing on is the same author's stick spin
 * `2.sd`, a node no corpus round reaches (analysis/stickspin-facts.json holds no snapshot of it; stickspin.test.ts
 * pins every case stopping at bag 1), so there is no round to follow.
 */
import type { TechniqueProfile } from './technique-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

export const SHACHIKUTRAIN: TechniqueProfile = {
  key: 'shachikutrain',
  tag: 'shachikutrain',
  transcriptionPath: `${OPENERS}/shachikutrain-technique.json`,
  artefactPath: `${REPO}/analysis/shachikutrain-facts.json`,
  hashFiles: {
    classifier: [`${SIM}/technique-facts.ts`, `${SIM}/technique-profile.ts`, `${SIM}/technique-profile-shachikutrain.ts`,
                 `${SIM}/emit-technique-facts.ts`, `${SIM}/route-facts.ts`],
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
      + 'the verified prefix, passing the reconstruction check), whether the 社畜トレイン (Shachiku Train) page\'s local '
      + 'shape stood around it: the lock\'s cells are the page\'s flat T pointing down (as drawn, or mirrored) and every '
      + 'cell of the window around it — the row above the T (the roof over its near end and the cell beyond it, the '
      + 'second slot\'s arms open), the two rows the TSD clears and the row under them (the cell under the nub and the '
      + 'S\'s foot filled, the second slot\'s nub open, the L\'s foot beyond it filled) — is filled or empty as drawn. '
      + 'The opportunity is a full T-spin Double; every hit is followed to the next T lock to see whether the second '
      + 'TSD the page draws fired.',
    notEligible: 'simulator output: which local shape a T went into is read off the vendored Triangle '
      + 'engine\'s boards, and nothing on the corpus side has a second implementation of it. No claim id, '
      + 'no badge, no figure in a report.',
    caveat: 'garbage is read as FILLED inside the window, and its hole columns are the engine\'s seeded-RNG '
      + 'columns, which disagree with the recorded ones (oracle-source.ts); a hit with garbage in its window '
      + 'is named in garbage_in_window for that reason. At a full TSD the two cleared rows are entailed by the '
      + 'clear (NaiveClauseForced): the T\'s orientation and the rows above and below them discriminate. The page\'s '
      + '2x2-hole builds lead to an STSD or a TST rather than the second TSD; a hit there is still a hit, followed to '
      + 'the second TSD like any other. Counts only, always N / M with the denominator.',
  },
  rules: () => [
    'opportunity: a T lock with spin "full" clearing 2 lines, at a 0-based lock index <= the verified index, '
      + 'whose board-before plus its cells makes exactly the rows the engine recorded clearing (the '
      + 'reconstruction check, counted exactly as opener-facts.json donation.check counts it)',
    'match: the lock\'s cells equal the variant\'s flat T under one translation (mirrored: columns '
      + 'reflected in the window), and every other window cell is filled (a piece or garbage) or empty as '
      + 'the page draws it; colour is never compared; cells outside the window are not read',
    'mirrored is tried only when as-drawn fails; a window leaving the board is no match (window_off_board)',
    'follow-up: the page\'s second-TSD slot (split by the first TSD\'s two cleared rows until that TSD joins it) '
      + 'carried through every clear and garbage insertion to the next T lock, each step verified against the '
      + 'engine\'s next board; fired iff that T is the slot and a scored full TSD',
    'controls: the same window at scored TSS, TST, mini TSS and mini TSD; ablations no_must_empty, no_roof '
      + 'and t_overlap at the opportunity; orientation_baseline = opportunities whose T stands up',
  ],
  lists: (hits, name) => ({
    shachikutrain_hits: hits.map(h => `${name(h)} lock ${h.lock}${h.mirrored ? ' (mirrored)' : ''}`),
    followup_not_fired: hits.filter(h => !h.followup.fired)
      .map(h => `${name(h)} lock ${h.lock} (${h.followup.reason}${h.followup.lock !== null ? ` at lock ${h.followup.lock}` : ''})`),
    garbage_in_window: hits.filter(h => h.garbage_in_window).map(h => `${name(h)} lock ${h.lock}`),
    shachikutrain_in_opener: hits.filter(h => h.in_opener).map(h => `${name(h)} lock ${h.lock}`),
  }),
};

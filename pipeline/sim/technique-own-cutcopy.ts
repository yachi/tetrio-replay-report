/**
 * 千鳥格子 (Cut Copy)'s half of the own-design search (`technique-own.ts`): where the window is tried, how far the
 * search goes, how many boards are published, and the artefact's strings. Data only; every rule is the search's
 * and the shared planner's.
 *
 * Offsets 0 and 4 put the window against a wall. The search tries them like the others and finds no candidate at
 * either (a measurement of this search, re-derived by the test, not a claim about the technique): with the window on
 * the floor and no T in the terrain, nothing covers the window's must-fill cells there without stranding a cell.
 */
import type { OwnProfile } from './technique-own.ts';

const SIM = import.meta.dir;
const REPO = `${SIM}/../..`;

export const CUTCOPY_OWN: OwnProfile = {
  key: 'cutcopy',
  tag: 'cutcopy',
  artefactPath: `${REPO}/analysis/cutcopy-own.json`,
  hashFiles: [`${SIM}/technique-own.ts`, `${SIM}/technique-own-cutcopy.ts`, `${SIM}/emit-technique-own.ts`],
  variant: 'cutcopy',
  offsets: [0, 1, 2, 3, 4],
  rowsAbove: 2,
  maxExtra: 4,
  maxSteps: 300,
  maxTried: 5000,
  pick: 2,
  artefact: {
    schema: 'technique-own/1',
    means: 'Boards of OURS carrying the 千鳥格子 window as drawn, found by a search: the window placed on the floor at '
      + 'each column offset, every cover of its must-fill cells by tetrominoes the planner\'s two-bag dealing allows, '
      + 'and each candidate handed, smallest first, to the shared demo planner (technique-demos.ts), which builds it '
      + 'from an empty board, fires the flat T into the window and fires the second TSD in the outer slot. Run '
      + 'through the vendored Triangle engine, which is the arbiter. Every candidate\'s outcome is counted.',
    notEligible: 'constructed, not played, and not any source\'s drawing: the boards, the queue, the hold and the '
      + 'key inputs are ours. No claim id, no badge, no figure in any count of the corpus.',
    caveat: 'the window is placed as drawn, on the floor, with at most two rows above it; a terrain holds no T and at '
      + 'most twelve pieces, because the planner deals the stood T and the follow-up T from two consecutive bags. A '
      + 'board this search does not find is not a board that cannot be built.',
  },
  rules: () => [
    'every board is built from an empty board by pieces out of a 7-bag, no line cleared before the stood T',
    'the stood T is the one T placement at which the corpus window (technique-facts.ts windowMatch, as drawn) matches, '
      + 'and the engine must credit it a full T-spin clearing two lines',
    'the second T must land in the follow-up slot carried through the first clear, a full T-spin clearing two lines',
    'the engine is the arbiter: every lock must land where the plan put it, with its spin, lines and hold flag',
    'each candidate\'s search is capped by a count of planner steps, never by a clock, so the outcome counts are '
      + 'the same on every machine',
  ],
};

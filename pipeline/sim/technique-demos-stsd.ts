/**
 * STSD's half of the constructed demos (`technique-demos.ts`): which build boards get a demo, which
 * boards none can stand on and why, and the artefact's strings. Data only; every rule is the planner's.
 * A file of its own, not part of `technique-profile-stsd.ts`, so a demo edit never stales the corpus
 * artefact `analysis/stsd-facts.json` (whose `emitter_md5` hashes that profile).
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

export const STSD_DEMOS: TechniqueDemoProfile = {
  key: 'stsd',
  tag: 'stsd',
  transcriptionPath: `${OPENERS}/stsd-technique.json`,
  artefactPath: `${REPO}/analysis/stsd-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-stsd.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'stsd',
  chains: [
    { node: 'build3.jl', terrain: 'build3.terrain' },
    { node: 'build3.jl_hole', terrain: 'build3.jl_hole.terrain' },
    { node: 'roof.z', terrain: 'roof.z.terrain' },
    { node: 'roof.i', terrain: 'roof.i.terrain' },
  ],
  unbuilt: {
    'misfire.garbage': '個窿係一行垃圾嘅窿：垃圾行要對手送先有，砌出嚟嘅示範冇對手，唔可以自己落垃圾',
    'misfire.spin': '係 misfire.garbage 嗰行垃圾上面打嘅，同一個原因砌唔到',
    'recover.j': '係 misfire 之後嘅盤面（有垃圾行），同一個原因砌唔到',
    'recover.j.after': '係 recover.j 之後嘅盤面，同一個原因砌唔到',
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per STSD build board the planner can build: from an empty board, the page\'s '
      + 'grey terrain built out of pieces WE chose, then the page\'s own pieces, then the stood T into the window '
      + 'the corpus matcher reads, then the second TSD the page promises. Run through the vendored Triangle engine.',
    notEligible: 'constructed, not played: the queue, the hold and the key inputs are ours, and the terrain\'s '
      + 'pieces are ours too (the page draws it grey). No claim id, no badge, no figure in any count.',
    caveat: 'the page draws its after board with the right side stacked up to the old roof; the demo stacks it with '
      + 'filler pieces of our choosing, compared exactly only inside the variant\'s window columns. Boards that need '
      + 'garbage are not built: a constructed demo has no opponent to send any.',
  },
  rules: () => [
    'a demo starts from an empty board, as every decoder does; the terrain is an exact cover of its grey cells by '
      + 'pieces the planner chose, every one reachable from spawn by the engine\'s own moves, no line cleared',
    'dealing: bag 1\'s T is dealt last in bag 1 and held on arrival, bag 2\'s first piece placed in its stead; bag '
      + '2\'s T is swapped for it and the held T fired as the stood T; the follow-up T is swapped out of the hold '
      + 'when the next piece arrives. Every bag is a whole 7-bag',
    'the stood T is the one T placement at which the corpus window (technique-facts.ts windowMatch, as drawn) '
      + 'matches the build board, and must be credited a full T-spin clearing the variant\'s lines',
    'the follow-up slot is the variant\'s, carried through the stood T\'s clear; the rows it clears are filled '
      + 'first with filler pieces outside the window columns, and it must be a full T-spin clearing the '
      + 'follow-up\'s lines',
    'reaches: board = the board after that lock shows the drawing exactly; spin = that lock\'s cells are the '
      + 'drawing\'s T; after = before that lock the board shows the drawing exactly inside the window columns and '
      + 'filled-where-drawn outside them, and that lock\'s cells are the drawn follow-up slot',
    'the engine is the arbiter: every lock must land where the plan put it, with its spin, lines and hold flag',
  ],
};

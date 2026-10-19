/**
 * STMB Cave's half of the constructed demos (`technique-demos.ts`): which boards a demo is planned on,
 * which boards none can stand on and why, and the artefact's strings. Data only; every rule is the
 * planner's. A file of its own, not part of `technique-profile-stmbcave.ts`, so a demo edit never stales
 * the corpus artefact `analysis/stmbcave-facts.json` (whose `emitter_md5` hashes that profile).
 *
 * Every chain is planned, and the planner's measured reason is what the artefact publishes when it
 * cannot build one; `stmbcave-demos.test.ts` re-derives each reason and the terrain cell counts beside it.
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

export const STMBCAVE_DEMOS: TechniqueDemoProfile = {
  key: 'stmbcave',
  tag: 'stmbcave',
  transcriptionPath: `${OPENERS}/stmbcave-technique.json`,
  artefactPath: `${REPO}/analysis/stmbcave-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-stmbcave.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'stmbcave',
  chains: [
    { node: 'basic.build', terrain: 'basic.build.terrain' },
    { node: 'feature.pre', terrain: 'feature.terrain' },
    { node: 'similar.build', terrain: 'similar.terrain' },
  ],
  unbuilt: {
    'basic.terrain': '原頁將呢幅地形畫偏咗一格（個坑喺第 3 至 5 欄，上面砌好嗰幅喺第 4 至 6 欄，由 0 數）；示範要企嘅係由砌好嗰幅推返出嚟嘅地形，嗰幅點解砌唔到寫喺佢自己度',
    'feature.spin': '係 feature.pre 上面打嘅 T：feature.pre 砌唔到，所以呢幅都冇示範',
    'feature.after': '係 feature.spin 之後嘅盤面，同一個原因冇示範',
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per STMB Cave build board the planner can build: from an empty board, the '
      + 'page\'s grey terrain built out of pieces WE chose, then the page\'s own pieces, then the flat T into the '
      + 'window the corpus matcher reads, then the second TSD the page draws under the cave. Run through the '
      + 'vendored Triangle engine. A board the planner cannot build is published unbuilt with its measured reason.',
    notEligible: 'constructed, not played: the queue, the hold and the key inputs are ours, and the terrain\'s '
      + 'pieces are ours too (the page draws it grey). No claim id, no badge, no figure in any count.',
    caveat: 'the page draws its basic and similar forms as local sketches (the rows the TSD would clear are not '
      + 'drawn full) and its one complete TSD on a stacked board with a three-cell J; a demo stands only on what '
      + 'the planner can build from an empty board without clearing a line.',
  },
  rules: () => [
    'a demo starts from an empty board, as every decoder does; the terrain is an exact cover of its grey cells by '
      + 'pieces the planner chose, every one reachable from spawn by the engine\'s own moves, no line cleared',
    'the page\'s own pieces are the build board\'s lower-case letters, one whole piece per letter',
    'the flat T is the one T placement at which the corpus window (technique-facts.ts windowMatch, as drawn) '
      + 'matches the build board, and must be credited a full T-spin clearing the variant\'s lines',
    'the engine is the arbiter: every lock must land where the plan put it, with its spin, lines and hold flag',
  ],
};

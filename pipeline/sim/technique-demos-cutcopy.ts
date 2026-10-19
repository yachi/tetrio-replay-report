/**
 * 千鳥格子 (Cut Copy)'s half of the constructed demos (`technique-demos.ts`): which boards a demo is planned on,
 * which boards none can stand on and why, and the artefact's strings. Data only; every rule is the planner's. A
 * file of its own, not part of `technique-profile-cutcopy.ts`, so a demo edit never stales the corpus artefact
 * `analysis/cutcopy-facts.json` (whose `emitter_md5` hashes that profile).
 *
 * Both builds the page draws are chains (the T-hole build and the third-column build, each on its own derived
 * terrain), and the planner's measured reason is what the artefact publishes when it cannot build one; the boards
 * with no page pieces (the basic form, its TSD, what it leaves and the second TSD) carry the profile's reason,
 * with the cell count `cutcopy-demos.test.ts` re-derives.
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';

export const CUTCOPY_DEMOS: TechniqueDemoProfile = {
  key: 'cutcopy',
  tag: 'cutcopy',
  transcriptionPath: `${OPENERS}/cutcopy-technique.json`,
  artefactPath: `${REPO}/analysis/cutcopy-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-cutcopy.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'cutcopy',
  chains: [
    { node: 'hole.osz', terrain: 'hole.terrain' },
    { node: 'col3.jz', terrain: 'col3.terrain' },
  ],
  unbuilt: {
    'basic': `基本形冇畫頁面嘅方塊，成幅都係灰色嘅元地形：有 34 格，唔係 4 嘅倍數：${LIMIT}`,
    'basic.spin': '係基本形上面打嘅 TSD：基本形砌唔到，所以呢幅都冇示範',
    'basic.after': '係 basic.spin 之後嘅盤面（由 second.spin 推出嚟），同一個原因冇示範',
    'second.spin': '係 basic.after 上面打嘅第二下 TSD，同一個原因冇示範',
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per 千鳥格子 build board the planner can build: from an empty board, the page\'s '
      + 'grey terrain built out of pieces WE chose, then the page\'s own pieces, then the flat T into the window '
      + 'the corpus matcher reads, then the second TSD the page draws in the outer slot. Run through the vendored '
      + 'Triangle engine. A board the planner cannot build is published unbuilt with its measured reason.',
    notEligible: 'constructed, not played: the queue, the hold and the key inputs are ours, and the terrain\'s '
      + 'pieces are ours too (the page draws it grey). No claim id, no badge, no figure in any count.',
    caveat: 'the page draws its terrains grey, and both its builds mirrored; a demo stands only on what the planner '
      + 'can build from an empty board without clearing a line, and fires the window as drawn.',
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

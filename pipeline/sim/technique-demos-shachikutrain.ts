/**
 * 社畜トレイン (Shachiku Train)'s half of the constructed demos (`technique-demos.ts`): which boards a demo is planned
 * on, which boards none can stand on and why, and the artefact's strings. Data only; every rule is the planner's. A
 * file of its own, not part of `technique-profile-shachikutrain.ts`, so a demo edit never stales the corpus artefact
 * `analysis/shachikutrain-facts.json` (whose `emitter_md5` hashes that profile).
 *
 * Four of the page's builds are chains (the basic form, the two 2x2-hole builds and DT社畜, each on its terrain), and
 * the planner's measured reason is what the artefact publishes when it cannot build one. The 4x2 build is NOT a
 * chain: its pale S (`r`) is a letter the planner would read as a piece R and stop at, which says nothing about the
 * board; its reason is the profile's, the terrain's own (no tiling at all: the hollow cuts it into two parts of six
 * cells), and `shachikutrain-demos.test.ts` re-derives both that and where the planner would have stopped. The boards
 * standing on another board's build carry the profile's reason too, checked against the transcription's own fields.
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const W4 = `元地形有 12 格，係 4 嘅倍數，但中間個窪將佢分開做左右兩舊、每舊 6 格，冇一個由方塊鋪得出嘅鋪法：${LIMIT}`;

export const SHACHIKUTRAIN_DEMOS: TechniqueDemoProfile = {
  key: 'shachikutrain',
  tag: 'shachikutrain',
  transcriptionPath: `${OPENERS}/shachikutrain-technique.json`,
  artefactPath: `${REPO}/analysis/shachikutrain-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-shachikutrain.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'shachikutrain',
  chains: [
    { node: 'basic.build', terrain: 'basic' },
    { node: 'u2.build', terrain: 'u2' },
    { node: 't3.build', terrain: 't3' },
    { node: 'dt', terrain: 'dt.terrain' },
  ],
  unbuilt: {
    'basic.spin': '係 basic.build 上面打嘅 TSD：basic.build 砌唔到，所以呢幅都冇示範',
    'basic.roofed': '係 basic.spin 消完行再加一粒 Z 嘅盤面（由 basic.second 推出嚟），同一個原因冇示範',
    'basic.second': '係 basic.roofed 上面打嘅第二下 TSD，同一個原因冇示範',
    'w4': `w4.build 砌唔到：${W4}`,
    'w4.build': W4,
    'w4.spin': '係 w4.build 上面打嘅 TSD：w4.build 砌唔到，所以呢幅都冇示範',
    'w4.roofed': '係 w4.spin 消完行再加一粒 I 同一粒 Z 嘅盤面（由 w4.second 推出嚟），同一個原因冇示範',
    'w4.second': '係 w4.roofed 上面打嘅第二下 TSD，同一個原因冇示範',
    'u2.spin': '係 u2.build 上面打嘅 TSD：u2.build 砌唔到，所以呢幅都冇示範',
    'u2.after': '係 u2.spin 消完行之後嘅盤面，同一個原因冇示範',
    't3.spin': '係 t3.build 上面打嘅 TSD：t3.build 砌唔到，所以呢幅都冇示範',
    't3.after': '係 t3.spin 消完行之後嘅盤面，同一個原因冇示範',
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per 社畜トレイン build board the planner can build: from an empty board, the page\'s '
      + 'grey terrain built out of pieces WE chose, then the page\'s own pieces, then the flat T into the window '
      + 'the corpus matcher reads, then the second TSD the page draws. Run through the vendored Triangle engine. A '
      + 'board the planner cannot build is published unbuilt with its measured reason.',
    notEligible: 'constructed, not played: the queue, the hold and the key inputs are ours, and the terrain\'s '
      + 'pieces are ours too (the page draws it grey). No claim id, no badge, no figure in any count.',
    caveat: 'the page draws its terrains grey, and DT社畜 mirrored; a demo stands only on what the planner can build '
      + 'from an empty board without clearing a line, and fires the window as drawn.',
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

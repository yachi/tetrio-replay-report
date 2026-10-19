/**
 * Imperial Cross's half of the constructed demos (`technique-demos.ts`): which boards a demo is planned on,
 * which boards none can stand on and why, and the artefact's strings. Data only; every rule is the planner's.
 * A file of its own, not part of `technique-profile-imperialcross.ts`, so a demo edit never stales the corpus
 * artefact `analysis/imperialcross-facts.json` (whose `emitter_md5` hashes that profile).
 *
 * Every chain the page draws a build for is planned (the TSD-shape builds stand on one terrain, so one
 * chain stands for the three of them; the cross-shape build and the ダブルダガー board each stand on their own
 * derived terrain), and the planner's measured reason is what the artefact publishes when it cannot build
 * one; `imperialcross-demos.test.ts` re-derives each reason and the cell counts beside it.
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

export const IMPERIALCROSS_DEMOS: TechniqueDemoProfile = {
  key: 'imperialcross',
  tag: 'imperialcross',
  transcriptionPath: `${OPENERS}/imperialcross-technique.json`,
  artefactPath: `${REPO}/analysis/imperialcross-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-imperialcross.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'imperialcross',
  chains: [
    { node: 'tsd.oz', terrain: 'tsd.terrain' },
    { node: 'cross.z', terrain: 'cross.z.terrain' },
  ],
  unbuilt: {
    'basic': '基本形冇畫頁面嘅方塊，成幅都係灰色嘅元地形（暗灰格當空）：有 29 格，係單數；每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出',
    'basic.t_drop': '係 T 跌入基本形途中嘅示意圖：基本形砌唔到，所以冇示範',
    'basic.t_up': '係 T 跌入基本形途中嘅示意圖：同一個原因冇示範',
    'basic.t_left': '係 T 跌入基本形途中嘅示意圖：同一個原因冇示範',
    'basic.t_down': '係 T 跌入基本形途中嘅示意圖：同一個原因冇示範',
    'basic.spin': '係基本形上面打嘅 T：基本形砌唔到，所以呢幅都冇示範',
    'basic.after': '係 basic.spin 之後嘅盤面，同一個原因冇示範',
    'tsd.ol': '同 tsd.oz 企喺同一幅 TSD 形地形（tsd.terrain）上面，嗰幅點解砌唔到寫喺 tsd.oz 度',
    'tsd.oj': '用 J 砌嘅係 TST 位，唔係呢個手法；而且同 tsd.oz 企喺同一幅地形上面，嗰幅點解砌唔到寫喺 tsd.oz 度',
    'cross.terrain': '十字形元地形有 25 格，係單數：由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出',
    'dagger': '呢幅係ダブルダガー，唔係呢個手法；佢企喺 dagger.terrain 上面',
    'dagger.terrain': 'dagger 嘅地形：dagger 唔係呢個手法，所以冇示範',
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per Imperial Cross build board the planner can build: from an empty board, the '
      + 'page\'s grey terrain built out of pieces WE chose, then the page\'s own pieces, then the T stood into the '
      + 'window the corpus matcher reads, then the second TSD the page draws in the empty arm. Run through the '
      + 'vendored Triangle engine. A board the planner cannot build is published unbuilt with its measured reason.',
    notEligible: 'constructed, not played: the queue, the hold and the key inputs are ours, and the terrain\'s '
      + 'pieces are ours too (the page draws it grey). No claim id, no badge, no figure in any count.',
    caveat: 'the page draws its terrains grey and its cross with an odd number of cells; a demo stands only on '
      + 'what the planner can build from an empty board without clearing a line.',
  },
  rules: () => [
    'a demo starts from an empty board, as every decoder does; the terrain is an exact cover of its grey cells by '
      + 'pieces the planner chose, every one reachable from spawn by the engine\'s own moves, no line cleared',
    'the page\'s own pieces are the build board\'s lower-case letters, one whole piece per letter',
    'the stood T is the one T placement at which the corpus window (technique-facts.ts windowMatch, as drawn) '
      + 'matches the build board, and must be credited a full T-spin clearing the variant\'s lines',
    'the engine is the arbiter: every lock must land where the plan put it, with its spin, lines and hold flag',
  ],
};

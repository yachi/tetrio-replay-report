/**
 * Double Dagger's half of the constructed demos (`technique-demos.ts`): which boards a demo is planned on,
 * which boards none can stand on and why, and the artefact's strings. Data only; every rule is the planner's.
 * A file of its own, not part of `technique-profile-doubledagger.ts`, so a demo edit never stales the corpus
 * artefact `analysis/doubledagger-facts.json` (whose `emitter_md5` hashes that profile).
 *
 * Every build the page draws is a chain (the TSD-shape build and the cross-shape build, each on its own
 * derived terrain), and the planner's measured reason is what the artefact publishes when it cannot build
 * one; the boards with no page pieces (the basic form and the three features) carry the profile's reason,
 * each with its cell count. `doubledagger-demos.test.ts` re-derives every reason and every count.
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';

export const DOUBLEDAGGER_DEMOS: TechniqueDemoProfile = {
  key: 'doubledagger',
  tag: 'doubledagger',
  transcriptionPath: `${OPENERS}/doubledagger-technique.json`,
  artefactPath: `${REPO}/analysis/doubledagger-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-doubledagger.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'doubledagger',
  chains: [
    { node: 'tsd.sj', terrain: 'tsd.sj.terrain' },
    { node: 'cross.z', terrain: 'cross.z.terrain' },
  ],
  unbuilt: {
    'basic': `基本形冇畫頁面嘅方塊，成幅都係灰色嘅元地形（暗灰格當空）：有 34 格，唔係 4 嘅倍數：${LIMIT}`,
    'basic.spin': '係基本形上面打嘅 T：基本形砌唔到，所以呢幅都冇示範',
    'basic.after': '係 basic.spin 之後嘅盤面，同一個原因冇示範',
    'tsd.terrain': 'TSD 形元地形本身冇呢個手法（個窗口喺度唔對到）；示範要企嘅係 tsd.sj 連埋原頁叫人隨便填嗰啲淺色格嘅地形，嗰幅點解砌唔到寫喺 tsd.sj 度',
    'tsd.pink': '係 TSD 形元地形標住粉紅格嘅同一幅（佔格一樣），同一個原因冇示範',
    'cross.terrain': '十字形元地形有 25 格，係單數：每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出',
    'cross.imperial': '呢幅係インペリアルクロス，唔係呢個手法；佢企喺 cross.imperial.terrain 上面',
    'cross.imperial.terrain': 'cross.imperial 嘅地形：cross.imperial 唔係呢個手法，所以冇示範',
    'tetris.spin': `係特徵圖，冇畫頁面嘅方塊：拎走條 I 之後有 70 格，唔係 4 嘅倍數：${LIMIT}`,
    'tetris.after': '係 tetris.spin 之後嘅盤面，同一個原因冇示範',
    'line.spin': `係特徵圖，冇畫頁面嘅方塊：拎走粒 T 之後有 42 格，唔係 4 嘅倍數：${LIMIT}；而且個窗口喺呢幅唔對到（兩個位中間有一行）`,
    'line.after': '係 line.spin 之後嘅盤面，同一個原因冇示範',
    'multi': `係特徵圖，冇畫頁面嘅方塊：有 58 格，唔係 4 嘅倍數：${LIMIT}`,
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per Double Dagger build board the planner can build: from an empty board, the '
      + 'page\'s grey terrain built out of pieces WE chose, then the page\'s own pieces, then the flat T into the '
      + 'window the corpus matcher reads, then the second TSD the page draws in the lower slot. Run through the '
      + 'vendored Triangle engine. A board the planner cannot build is published unbuilt with its measured reason.',
    notEligible: 'constructed, not played: the queue, the hold and the key inputs are ours, and the terrain\'s '
      + 'pieces are ours too (the page draws it grey). No claim id, no badge, no figure in any count.',
    caveat: 'the page draws its terrains grey, with a stack beside its builds the player is told to fill as they '
      + 'like; a demo stands only on what the planner can build from an empty board without clearing a line.',
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

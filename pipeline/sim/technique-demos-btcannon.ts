/**
 * BT砲 (途中BT)'s half of the constructed demos (`technique-demos.ts`): which boards a demo is planned on, which
 * boards none can stand on and why, and the artefact's strings. Data only; every rule is the planner's. A file of
 * its own, not part of `technique-profile-btcannon.ts`, so a demo edit never stales the corpus artefact
 * `analysis/btcannon-facts.json` (whose `emitter_md5` hashes that profile).
 *
 * NO CHAIN. The shared planner reads a build's page pieces as its LOWER-case letters and its terrain as the rest,
 * and this page draws neither build that way: the 欄干 build's terrain carries a lower-case L of its own (so the
 * build less its lower case is not its terrain, which the planner refuses outright), and the 72積み builds draw
 * the pieces the page places in UPPER case and the 72積み stack in lower case. So every board carries the
 * profile's reason, each with the cell count the test re-derives; one of them (s72.3, a terrain of 28 cells) is
 * stopped by that reading alone, and the reason says so rather than calling it unbuildable.
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const ODD = '每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出';
const UPPER = '原頁將佢加嘅方塊畫大楷、72積み 本身嘅方塊畫細楷，而呢個 planner 當細楷係頁面方塊，所以冇排呢幅（係讀法對唔上，唔係量過砌唔到）';

export const BTCANNON_DEMOS: TechniqueDemoProfile = {
  key: 'btcannon',
  tag: 'btcannon',
  transcriptionPath: `${OPENERS}/btcannon-technique.json`,
  artefactPath: `${REPO}/analysis/btcannon-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-btcannon.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'btcannon',
  chains: [],
  unbuilt: {
    'basic': `基本形冇畫頁面嘅方塊，成幅都係灰色嘅元地形：有 45 格，係單數：${ODD}`,
    'basic.spin': '係基本形上面打嘅 TSD：基本形砌唔到，所以呢幅都冇示範',
    'basic.after': '係 basic.spin 之後嘅盤面（由 tst.spin 推出嚟），同一個原因冇示範',
    'tst.spin': '係 basic.after 上面打嘅 TST，同一個原因冇示範',
    'parapet.terrain': `欄干嘅元地形有 35 格，係單數：${ODD}`,
    'parapet': '呢幅係欄干，唔係呢個手法；佢企喺 parapet.terrain 上面，嗰幅砌唔到',
    'bt.terrain': `同 parapet.terrain 一樣嘅元地形（佔格一樣）：有 35 格，係單數：${ODD}`,
    'bt.build': '企喺 bt.terrain 上面，嗰幅有 35 格，係單數，砌唔到；而且佢元地形自己有一粒細楷 L，呢個 planner 會當咗佢係頁面方塊',
    's72.1': `企喺 s72.1.terrain 上面，嗰幅有 26 格，唔係 4 嘅倍數：${LIMIT}`,
    's72.1.terrain': `s72.1 嘅元地形：有 26 格，唔係 4 嘅倍數：${LIMIT}`,
    's72.2': `企喺 s72.2.terrain 上面，嗰幅有 25 格，係單數：${ODD}`,
    's72.2.terrain': `s72.2 嘅元地形：有 25 格，係單數：${ODD}`,
    's72.3': `${UPPER}；佢嘅元地形有 28 格`,
    's72.3.terrain': `s72.3 嘅元地形（28 格）：${UPPER}`,
    's72.4': `企喺 s72.4.terrain 上面，嗰幅有 27 格，係單數：${ODD}`,
    's72.4.terrain': `s72.4 嘅元地形：有 27 格，係單數：${ODD}`,
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per BT砲 build board the planner can build: from an empty board, the page\'s '
      + 'grey terrain built out of pieces WE chose, then the page\'s own pieces, then the flat T into the window '
      + 'the corpus matcher reads, then the TST the page draws next. Run through the vendored Triangle engine. A '
      + 'board no demo stands on is published unbuilt with its reason.',
    notEligible: 'constructed, not played: the queue, the hold and the key inputs are ours, and the terrain\'s '
      + 'pieces are ours too (the page draws it grey). No claim id, no badge, no figure in any count.',
    caveat: 'the page draws its terrains grey; a demo stands only on what the planner can build from an empty board '
      + 'without clearing a line, and it reads a build\'s page pieces as its lower-case letters, which this page\'s '
      + 'builds do not follow.',
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

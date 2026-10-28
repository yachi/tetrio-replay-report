/**
 * 途中DT砲 (mid-game DT Cannon)'s half of the constructed demos (`technique-demos.ts`): which boards a demo is planned
 * on, which boards none can stand on and why, and the artefact's strings. Data only; every rule is the planner's. A
 * file of its own, not part of `technique-profile-dtcannon.ts`, so a demo edit never stales the corpus artefact
 * `analysis/dtcannon-facts.json` (whose `emitter_md5` hashes that profile).
 *
 * NO CHAIN. Every build board on this page holds an ODD number of cells but one (`wait.i`, even and not a multiple of
 * four), and so does every terrain under them but the 待ち terrain's two drawings: an odd board cannot be reached
 * from an empty one at all (each lock adds 4 cells and each clear removes 10). The boards that ARE multiples of four
 * are the DTDT boards (開幕DT砲's residue with the DT shape built on it, drawn as one board with no terrain of its
 * own) and two のそみ砲 illustrations, drawn with no terrain of their own either. Each reason carries the cell count the test re-derives.
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const ODD = '每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出';
const RESIDUE = '呢幅係開幕DT砲打完之後嘅殘局加新方塊，頁面冇另外畫佢嘅元地形，而呢個 planner 要一幅元地形先排得，所以冇排呢幅（係讀法對唔上，唔係量過砌唔到）';
const ILLUS = '係のそみ砲嘅插圖，頁面冇將佢分開畫做元地形同頁面方塊，而呢個 planner 要咁先排得，所以冇排示範（係讀法對唔上，唔係量過砌唔到）';

export const DTCANNON_DEMOS: TechniqueDemoProfile = {
  key: 'dtcannon',
  tag: 'dtcannon',
  transcriptionPath: `${OPENERS}/dtcannon-technique.json`,
  artefactPath: `${REPO}/analysis/dtcannon-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-dtcannon.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'dtcannon',
  chains: [],
  unbuilt: {
    'basic': `基本形冇畫頁面嘅方塊，成幅都係灰色嘅元地形：有 45 格，係單數：${ODD}`,
    'basic.spin': `係基本形上面打嘅 TSD：有 49 格，係單數：${ODD}`,
    'basic.after': `係 basic.spin 之後嘅盤面（由 tst.spin 推出嚟）：有 29 格，係單數：${ODD}`,
    'tst.spin': `係 basic.after 上面打嘅 TST：有 33 格，係單數：${ODD}`,
    'wait.terrain': `待ち嘅元地形有 22 格，唔係 4 嘅倍數：${LIMIT}`,
    'wait.i': `企喺 wait.terrain 上面：有 30 格，唔係 4 嘅倍數：${LIMIT}；而且元地形自己有一粒細楷 Z，呢個 planner 會當咗佢係頁面方塊`,
    'wait.terrain2': `同 wait.terrain 一樣嘅元地形（佔格一樣）：有 22 格，唔係 4 嘅倍數：${LIMIT}`,
    'wait.dt': `企喺 wait.terrain2 上面：有 45 格，係單數：${ODD}`,
    'roof.base': `屋頂未加嘅 TSD 盤面（由 roof.build 推出嚟）：有 29 格，係單數：${ODD}`,
    'roof.so': `企喺 roof.base 上面：有 37 格，係單數：${ODD}`,
    'roof.build': `企喺 roof.base 上面：有 37 格，係單數：${ODD}`,
    'roof.fill': `係插圖：有 33 格，係單數：${ODD}`,
    'done.terrain': `TSD 完成形嘅元地形有 43 格，係單數：${ODD}`,
    'done.build': `企喺 done.terrain 上面：有 51 格，係單數：${ODD}`,
    'done.cells': `係插圖（粉紅格同黃格）：有 51 格，係單數：${ODD}`,
    'jhook.terrain': `J 掛鈎嘅元地形（由 jhook.build 推出嚟）有 57 格，係單數：${ODD}`,
    'jhook.build': `企喺 jhook.terrain 上面：有 61 格，係單數：${ODD}`,
    'dtdt.base': `有 52 格：${RESIDUE}`,
    'dtdt.spin': `係 dtdt.base 上面打嘅 TSD，有 56 格：${RESIDUE}`,
    'dtdt.tst.base': `有 64 格：${RESIDUE}`,
    'dtdt.tst': `係 dtdt.tst.base 上面打嘅 TST，有 68 格：${RESIDUE}`,
    'nozomi.1': `有 28 格：${ILLUS}`,
    'nozomi.2': `有 46 格：${ILLUS}`,
    'nozomi.3': `有 44 格：${ILLUS}`,
    'nozomi.4': `有 58 格：${ILLUS}`,
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per 途中DT砲 build board the planner can build: from an empty board, the page\'s '
      + 'grey terrain built out of pieces WE chose, then the page\'s own pieces, then the flat T into the window '
      + 'the corpus matcher reads, then the TST the page draws next. Run through the vendored Triangle engine. A '
      + 'board no demo stands on is published unbuilt with its reason.',
    notEligible: 'constructed, not played: the queue, the hold and the key inputs are ours, and the terrain\'s '
      + 'pieces are ours too (the page draws it grey). No claim id, no badge, no figure in any count.',
    caveat: 'the page draws its terrains grey; a demo stands only on what the planner can build from an empty board '
      + 'without clearing a line, and every build board on this page holds an odd number of cells or stands on a '
      + 'terrain that is not a multiple of four.',
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

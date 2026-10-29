/**
 * King Crimson's half of the constructed demos (`technique-demos.ts`): which boards a demo is planned on, which boards
 * none can stand on and why, and the artefact's strings. Data only; every rule is the planner's. A file of its own,
 * not part of `technique-profile-kingcrimson.ts`, so a demo edit never stales the corpus artefact
 * `analysis/kingcrimson-facts.json` (whose `emitter_md5` hashes that profile).
 *
 * NO CHAIN. The four boards carrying the shape (the basic setup and the three King Crimsons the page builds) each
 * hold 60 cells: a 52-cell stack under two pieces of the page's own. 52 cells is 13 pieces, and the planner's
 * dealing (two bags, each non-T piece at most once a bag, the page's two pieces counted in them) leaves at most 10
 * for the stack, so the planner finds no cover: measured in the test on each board read with its stack as terrain.
 * Three of those boards draw the rest of the stack in a light grey `q` that the planner reads as a page piece of 44
 * or 51 cells, and the test measures that reading too; the basic setup draws no terrain board of its own. The other
 * boards are TKI 3's own opener and T-spin Doubles (the window fires on none of them, measured), their residues (each
 * holding a cell no tetromino can cover without a line clear) and the builds standing on those residues, and the
 * empty-field illustration's boards. Each reason carries the figure the test re-derives.
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const ODD = '每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出';
const NOCOVER = '當佢地形咁排，planner 量到「地形冇一個由非 T 方塊（每款最多兩粒）砌成嘅鋪法」：52 格要 13 粒，'
  + '兩巡非 T 方塊最多 12 粒，再扣埋頁面嗰兩粒就得 10 粒（係呢個 planner 發牌嘅限制，唔係砌唔出）';
const Q = (n: number) => `呢個 planner 當淺灰色嘅 q 係一粒頁面方塊，量到「頁面嘅 Q 畫咗 ${n} 格，唔係一粒」；`
  + `當 q 係地形咁排，就同基本形一樣：${NOCOVER}`;
const ISOLATED = '最底一行有一格四邊都冇其他格（係俾消行切開咗嘅方塊），冇一粒方塊蓋得到佢而唔蓋空格：' + LIMIT;
const NOT_KC = '個窗口喺呢幅一個 T 位都對唔到（兩個方向都量過），唔係呢個手法嘅形，所以冇示範';

export const KINGCRIMSON_DEMOS: TechniqueDemoProfile = {
  key: 'kingcrimson',
  tag: 'kingcrimson',
  transcriptionPath: `${OPENERS}/kingcrimson-technique.json`,
  artefactPath: `${REPO}/analysis/kingcrimson-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-kingcrimson.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'kingcrimson',
  chains: [],
  unbuilt: {
    'basic': `基本形有 60 格：灰色嘅疊 52 格，加頁面嘅 L 同 S；頁面冇另外畫佢嘅元地形。${NOCOVER}`,
    'basic.spin': '係基本形上面打嘅 TST：基本形砌唔到，所以呢幅都冇示範',
    'basic.after': `係 TST 之後嘅盤面：有 34 格，唔係 4 嘅倍數：${LIMIT}`,
    'tki1.form': `係 TKI 3 開局（24 格）：${NOT_KC}`,
    'tki1.spin': `係 TKI 3 嘅 TSD（28 格）：${NOT_KC}`,
    'tki1.after': `係 TKI 3 嘅 TSD 打完嘅殘局（8 格）：${ISOLATED}`,
    'tki1.z': `企喺 tki1.after 上面（12 格），嗰幅砌唔到；而且${NOT_KC}`,
    'tki1.j': `企喺 tki1.z 上面（16 格），嗰幅砌唔到；而且${NOT_KC}`,
    'tki1.kc': `呢個 King Crimson 有 60 格，左右反轉畫：${Q(44)}`,
    'tki2.form': `同 tki1.form 一樣嘅 TKI 3 開局（24 格）：${NOT_KC}`,
    'tki2.spin': `係 TKI 3 嘅 TSD（28 格）：${NOT_KC}`,
    'tki2.after': `係 TKI 3 嘅 TSD 打完嘅殘局（8 格）：${ISOLATED}`,
    'tki2.build': `企喺 tki2.after 上面（24 格），嗰幅砌唔到；而且${NOT_KC}`,
    'tki2.tsd': `係 TKI 3 嘅第二下 TSD（28 格）：${NOT_KC}`,
    'tki2.tsd.after': `係第二下 TSD 打完嘅殘局（8 格）：${ISOLATED}`,
    'tki2.s': `企喺 tki2.tsd.after 上面（12 格），嗰幅砌唔到；而且${NOT_KC}`,
    'tki2.l': `企喺 tki2.s 上面（16 格），嗰幅砌唔到；而且${NOT_KC}`,
    'tki2.kc': `呢個 King Crimson 有 60 格：${Q(44)}`,
    'empty.j': `得一粒 J（4 格）：${NOT_KC}`,
    'empty.clear': `有 11 格，係單數：${ODD}`,
    'empty.cell': `係插圖，得 1 格，係單數：${ODD}`,
    'empty.kc': `呢個 King Crimson 有 60 格，左右反轉畫，企喺 empty.cell（1 格，係單數）上面：${Q(51)}`,
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per King Crimson build board the planner can build: from an empty board, the '
      + 'page\'s grey stack built out of pieces WE chose, then the page\'s own pieces, then the stood T into the TST '
      + 'slot the corpus window reads, then the STSD under it. Run through the vendored Triangle engine. A board no '
      + 'demo stands on is published unbuilt with its reason.',
    notEligible: 'constructed, not played: the queue, the hold and the key inputs are ours, and the stack\'s '
      + 'pieces are ours too (the page draws it grey). No claim id, no badge, no figure in any count.',
    caveat: 'the page draws its stacks grey; a demo stands only on what the planner can build from an empty board '
      + 'without clearing a line, in two bags; every board carrying this shape holds a 52-cell stack, more than two '
      + 'bags hold, and three of them draw it in a light grey the planner reads as a page piece.',
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

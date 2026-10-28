/**
 * 階段のドネイト (Kaidan Setups)'s half of the constructed demos (`technique-demos.ts`): which boards a demo is planned
 * on, which boards none can stand on and why, and the artefact's strings. Data only; every rule is the planner's. A
 * file of its own, not part of `technique-profile-kaidan.ts`, so a demo edit never stales the corpus artefact
 * `analysis/kaidan-facts.json` (whose `emitter_md5` hashes that profile).
 *
 * Three chains: the four-step basic form (the O roof) on its staircase, and the three-step S and J forms on theirs.
 * Whether the planner builds each is its measured result, published unbuilt with its reason when it cannot (the
 * four-step staircase's cell count is odd, which is a proof). The boards standing on the basic form's chain (the Z
 * alone, the TSD, what it leaves) carry the profile's reason; the two DT砲 boards are not chains: their terrain holds a
 * cell count that is not a multiple of four, and both are drawn mirrored, so the as-drawn window the planner fires
 * would not fit them even built — `kaidan-demos.test.ts` re-derives the counts and measures the hand. A variant with a
 * payoff ends its demo on the stood T (`technique-demos.ts`, 欄干's branch). The Tetris that follows is harddrop's
 * next step: its Anchor_Set page draws an I into a four-deep re-opened column, on a later board of that line rather
 * than on the board a Kaidan TSD leaves (`cross_source.harddrop_anchor_set.payoff_drawing`); it is not constructed.
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const ON_BASIC = '企喺四級樓梯嘅基本形上面：基本形砌唔到，所以呢幅都冇示範';
const DT = (n: number) => `連埋 DT砲 嘅盤面有 ${n} 格，係雙數但唔係 4 嘅倍數：${LIMIT}；而且頁面畫嘅係左右反轉嘅形，planner 用嘅照畫窗口就算砌到都對唔上`;

export const KAIDAN_DEMOS: TechniqueDemoProfile = {
  key: 'kaidan',
  tag: 'kaidan',
  transcriptionPath: `${OPENERS}/kaidan-technique.json`,
  artefactPath: `${REPO}/analysis/kaidan-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-kaidan.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'kaidan',
  chains: [
    { node: 'basic.o', terrain: 'basic.terrain' },
    { node: 's3.s', terrain: 's3.terrain' },
    { node: 's3.j', terrain: 'j3.terrain' },
  ],
  unbuilt: {
    'basic.z': '係四級樓梯（basic.terrain）加一粒 Z：四級樓梯砌唔到（見 basic.o），所以呢幅都冇示範',
    'basic.spin': `TSD ${ON_BASIC}`,
    'basic.after': '係 basic.spin 之後嘅盤面，同一個原因冇示範',
    'dt.amemiya.pre': DT(54),
    'dt.amemiya': `係 dt.amemiya.pre 上面打嘅 TSD：${DT(54)}`,
    'dt.anchor.pre': DT(58),
    'dt.anchor': `係 dt.anchor.pre 上面打嘅 TSD：${DT(58)}`,
    'after.1': '打後嘅示意圖（頁面冇講係 ST積み 定 よしひろ積み），唔係階段のドネイト本身',
    'after.2': '打後嘅示意圖（頁面冇講係 ST積み 定 よしひろ積み），唔係階段のドネイト本身',
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per 階段のドネイト build board the planner can build: from an empty board, the page\'s '
      + 'grey staircase built out of pieces WE chose, then the page\'s own pieces (the Z stood on end, and the roof), '
      + 'then the flat T into the window the corpus matcher reads, a TSD that re-opens the wall column. Run through '
      + 'the vendored Triangle engine. A board the planner cannot build is published unbuilt with its measured reason.',
    notEligible: 'constructed, not played: the queue, the hold and the key inputs are ours, and the terrain\'s '
      + 'pieces are ours too (the page draws it grey). No claim id, no badge, no figure in any count.',
    caveat: 'the page draws its terrains grey and its DT砲 boards mirrored; a demo stands only on what the planner can '
      + 'build from an empty board without clearing a line, and fires the window as drawn. It ends on the TSD, as every '
      + 'payoff variant\'s demo does: the Tetris after it is harddrop\'s next step (its Anchor_Set page draws an I into '
      + 'a four-deep re-opened column, on a later board of that line), and is not constructed.',
  },
  rules: () => [
    'a demo starts from an empty board, as every decoder does; the terrain is an exact cover of its grey cells by '
      + 'pieces the planner chose, every one reachable from spawn by the engine\'s own moves, no line cleared',
    'the page\'s own pieces are the build board\'s lower-case letters, one whole piece per letter',
    'the flat T is the one T placement at which the corpus window (technique-facts.ts windowMatch, as drawn) '
      + 'matches the build board, and must be credited a full T-spin clearing the variant\'s lines',
    'a variant with a payoff in place of a follow-up ends the demo on the stood T',
    'the engine is the arbiter: every lock must land where the plan put it, with its spin, lines and hold flag',
  ],
};

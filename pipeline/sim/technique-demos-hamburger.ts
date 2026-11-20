/**
 * ハンバーガー (Hamburger)'s half of the constructed demos (`technique-demos.ts`): which boards a demo is planned on,
 * which boards none can stand on and why, and the artefact's strings. Data only; every rule is the planner's. A file
 * of its own, not part of `technique-profile-hamburger.ts`, so a demo edit never stales the corpus artefact
 * `analysis/hamburger-facts.json` (whose `emitter_md5` hashes that profile).
 *
 * NO CHAIN. harddrop draws the shape on a 21-cell terrain, an ODD count: each lock adds 4 cells and each line clear
 * removes 10, so no board built from empty holds it. Every other board is that terrain plus pieces, or an
 * illustration of the repetition; each reason carries the figure `hamburger-demos.test.ts` re-derives.
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const ODD = '係單數：每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出';

export const HAMBURGER_DEMOS: TechniqueDemoProfile = {
  key: 'hamburger',
  tag: 'hamburger',
  transcriptionPath: `${OPENERS}/hamburger-technique.json`,
  artefactPath: `${REPO}/analysis/hamburger-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-hamburger.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'hamburger',
  chains: [],
  unbuilt: {
    'terrain': `基本形嘅地形有 21 格，${ODD}`,
    'zbuild': `用 Z 蓋住個窿嘅砌法同地形一樣有 21 格，${ODD}`,
    'softdrop': `T 軟降到一半嘅示意圖有 25 格，${ODD}`,
    'spin': `T 擺入去嘅 TSS 盤面有 25 格，${ODD}`,
    'spin.after': `TSS 打完嘅盤面有 15 格，${ODD}`,
    'repeat': `重複疊多層嘅示意圖有 39 格，${ODD}`,
    'tetris': '最後用 I 打 Tetris 嘅示意圖有 64 格，係 4 嘅倍數，但要先打過幾次 TSS（消過行）先去到，'
      + '而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）',
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per Hamburger build board the planner can build: from an empty board, the '
      + 'terrain built out of pieces WE chose, then the page\'s own pieces, then the flat T into the TSS that opens '
      + 'the well. Run through the vendored Triangle engine. A board no demo stands on is published unbuilt with its '
      + 'reason.',
    notEligible: 'constructed, not played: the queue, the hold and the key inputs are ours, and the terrain\'s '
      + 'pieces are ours too (harddrop draws it grey). No claim id, no badge, no figure in any count.',
    caveat: 'a demo stands only on what the planner can build from an empty board without clearing a line; harddrop '
      + 'draws this technique on a terrain whose cell count is odd, which no such build reaches.',
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

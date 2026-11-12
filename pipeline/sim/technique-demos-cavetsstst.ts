/**
 * Cave TSS to TST's half of the constructed demos (`technique-demos.ts`): which boards a demo is planned on, which
 * boards none can stand on and why, and the artefact's strings. Data only; every rule is the planner's. A file of
 * its own, not part of `technique-profile-cavetsstst.ts`, so a demo edit never stales the corpus artefact
 * `analysis/cavetsstst-facts.json` (whose `emitter_md5` hashes that profile).
 *
 * NO CHAIN. harddrop's terrain is a garbage block and a garbage row with its hole one column in: 10 cells, which no
 * set of tetrominoes placed without a line clear can make (each lock adds 4), and the L hung over it brings it to 14.
 * The board the TSS leaves holds 8 cells, but the only cover of them by tetrominoes uses a T (enumerated in the test),
 * and the planner keeps the T's for the spins. The TST board holds 39 cells, an odd count. Each reason carries the
 * figure the test re-derives.
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const LIMIT = '唔係 4 嘅倍數：要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const ODD = '係單數：每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出';

export const CAVETSSTST_DEMOS: TechniqueDemoProfile = {
  key: 'cavetsstst',
  tag: 'cavetsstst',
  transcriptionPath: `${OPENERS}/cavetsstst-technique.json`,
  artefactPath: `${REPO}/analysis/cavetsstst-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-cavetsstst.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'cavetsstst',
  chains: [],
  unbuilt: {
    'terrain': `地形（一格垃圾加一行窿喺第二格嘅垃圾）有 10 格，${LIMIT}`,
    'tss': `L 搭咗喺窿上面嘅盤面有 14 格，${LIMIT}`,
    'tss.spin': '係 tss 上面打嘅 TSS：tss 砌唔到，所以呢幅都冇示範',
    'tss.after': 'TSS 打完嘅殘局有 8 格，但用方塊鋪佢嘅每一個鋪法都要用一粒 T（成粒 L、T 剩低嗰三格同一格垃圾，量過），'
      + '而 planner 嘅 T 留咗俾 T-spin，地形只用非 T 方塊（係 planner 發牌嘅限制，唔係砌唔出）',
    'tst': `圍住 TST 位砌好嘅疊有 39 格，${ODD}`,
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per Cave TSS to TST build board the planner can build: from an empty board, the '
      + 'terrain built out of pieces WE chose, then the page\'s own pieces, then the stood T into the cave, then the '
      + 'TST beside it. Run through the vendored Triangle engine. A board no demo stands on is published unbuilt '
      + 'with its reason.',
    notEligible: 'constructed, not played: the queue, the hold and the key inputs are ours, and the terrain\'s '
      + 'pieces are ours too (harddrop draws it as garbage). No claim id, no badge, no figure in any count.',
    caveat: 'a demo stands only on what the planner can build from an empty board without clearing a line; harddrop '
      + 'draws this technique on a garbage terrain whose cell count no such build reaches.',
  },
  rules: () => [
    'a demo starts from an empty board, as every decoder does; the terrain is an exact cover of its grey cells by '
      + 'pieces the planner chose, every one reachable from spawn by the engine\'s own moves, no line cleared',
    'the page\'s own pieces are the build board\'s lower-case letters, one whole piece per letter',
    'the stood T is the one T placement at which the corpus window (technique-facts.ts windowMatch, as drawn) '
      + 'matches the build board',
    'the engine is the arbiter: every lock must land where the plan put it, with its spin, lines and hold flag',
  ],
};

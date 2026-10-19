/**
 * 欄干 (Parapet)'s half of the constructed demos (`technique-demos.ts`): which boards a demo is planned on, which
 * boards none can stand on and why, and the artefact's strings. Data only; every rule is the planner's. A file of its
 * own, not part of `technique-profile-parapet.ts`, so a demo edit never stales the corpus artefact
 * `analysis/parapet-facts.json` (whose `emitter_md5` hashes that profile).
 *
 * One chain: the O-roof basic form on its derived terrain, the TSD variant (`parapet`) fired into it. The Z-roof
 * basic form's terrain holds a cell count that is not a multiple of four, so this planner (which never clears a line)
 * cannot build it, and the four boards the page draws on that form (the TSD, the TSS, and what each leaves) stand on
 * it — the profile's reasons, with the cell count `parapet-demos.test.ts` re-derives. A variant with a payoff instead
 * of a follow-up ends its demo on the stood T (`technique-demos.ts`): the page draws no well four deep, so there is no
 * Tetris to construct, and a second chain on the same board (the TSS) would put two demos on one node, which the
 * page's one-block-per-node audit refuses. Both are stated in the artefact's caveat.
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const ON_Z = '企喺 Z 頂嘅基本形（basic.z）上面：嗰幅砌唔到，所以呢幅都冇示範';

export const PARAPET_DEMOS: TechniqueDemoProfile = {
  key: 'parapet',
  tag: 'parapet',
  transcriptionPath: `${OPENERS}/parapet-technique.json`,
  artefactPath: `${REPO}/analysis/parapet-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-parapet.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'parapet',
  chains: [
    { node: 'basic.o', terrain: 'basic.o.terrain' },
  ],
  unbuilt: {
    'basic.z.terrain': `Z 頂基本形嘅元地形有 30 格，唔係 4 嘅倍數：${LIMIT}`,
    'basic.z': `佢嘅元地形（basic.z.terrain）有 30 格，唔係 4 嘅倍數：${LIMIT}`,
    'tsd.spin': `TSD ${ON_Z}`,
    'tsd.after': '係 tsd.spin 之後嘅盤面，同一個原因冇示範',
    'tss.spin': `TSS ${ON_Z}`,
    'tss.after': '係 tss.spin 之後嘅盤面，同一個原因冇示範',
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per 欄干 build board the planner can build: from an empty board, the page\'s grey '
      + 'terrain built out of pieces WE chose, then the page\'s own pieces (the L stood on end, shifted one column, and the '
      + 'roof), then the flat T into the window the corpus matcher reads, a TSD that opens the well under its left '
      + 'arm. Run through the vendored Triangle engine. A board the planner cannot build is published unbuilt with its '
      + 'measured reason.',
    notEligible: 'constructed, not played: the queue, the hold and the key inputs are ours, and the terrain\'s '
      + 'pieces are ours too (the page draws it grey). No claim id, no badge, no figure in any count.',
    caveat: 'the page draws its terrains grey; a demo stands only on what the planner can build from an empty board '
      + 'without clearing a line, and fires the TSD variant as drawn. It ends on the TSD: the page draws its well two '
      + 'deep, so there is no Tetris to construct, and the TSS on the same board is not a second demo (one demo per '
      + 'board).',
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

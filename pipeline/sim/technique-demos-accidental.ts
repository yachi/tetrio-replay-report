/**
 * 意外 T-spin (accidental TSD / TST)'s half of the constructed demos (`technique-demos.ts`). Data only. A file of its
 * own, not part of `technique-profile-accidental.ts`, so a demo edit never stales `analysis/accidental-facts.json`.
 *
 * NO CHAIN. The page has no window, so there is no drawn shape for a demo to build: its boards are a phone video's
 * two T-spins (the TSD before the TST, and the TST), every one with full rows of stack under it. Each board's reason carries the cell
 * count `accidental-demos.test.ts` re-derives: an ODD count is a proof (each lock adds 4 cells and each line clear
 * removes 10, so a board built from empty is always even); an even count that is not a multiple of four is this
 * planner's limit (it never clears a line).
 */
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;

const ODD = '係單數：每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出';
const NOT4 = '係雙數但唔係 4 嘅倍數，要消過行先去到，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';

export const ACCIDENTAL_DEMOS: TechniqueDemoProfile = {
  key: 'accidental',
  tag: 'accidental',
  transcriptionPath: `${OPENERS}/accidental-technique.json`,
  artefactPath: `${REPO}/analysis/accidental-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-accidental.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'tst',
  chains: [],
  unbuilt: {
    'video.tsd': `影片 TSD 嘅地形有 50 格，${NOT4}`,
    'video.tsd.spin': `影片 TSD 嘅盤面（連 T）有 54 格，${NOT4}`,
    'video.tst': `影片 TST 嘅地形有 53 格，${ODD}`,
    'video.tst.spin': `影片 TST 嘅盤面（連 T）有 57 格，${ODD}`,
  },
  artefact: {
    schema: 'technique-demos/1',
    means: 'One constructed replay per accidental T-spin board the planner can build. The page has no window, so '
      + 'there is no shape to build: every board is published unbuilt with its reason.',
    notEligible: 'constructed, not played: no claim id, no badge, no figure in any count.',
    caveat: 'a demo stands only on what the planner can build from an empty board without clearing a line; every '
      + 'board here has full rows of stack under the T, which no such build reaches.',
  },
  rules: () => [
    'a demo starts from an empty board, as every decoder does, and the planner never clears a line',
    'every drawn board is either reached by a demo or published unbuilt with its reason',
  ],
};

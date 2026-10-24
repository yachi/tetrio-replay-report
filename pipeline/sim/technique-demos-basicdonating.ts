/**
 * 基本的なドネイト (basic donating)'s half of the constructed demos (`technique-demos.ts`). Data only; every rule is the
 * planner's. A file of its own, not part of `technique-profile-basicdonating.ts`, so a demo edit never stales the
 * corpus artefact.
 *
 * No chain: the planner builds a page's terrain, then the page's own pieces off a BUILD board (the terrain plus the
 * lower-case pieces, before the T), then fires the window. This page draws no such board: each answer draws the
 * donated pieces and the T together, with the pieces in the cleared rows muted upper case, which the planner does not
 * read as page pieces. So every board is published unbuilt, and the reason is measured from the transcription here
 * (and re-derived by `basicdonating-demos.test.ts`): a terrain with an ODD cell count cannot be built from an empty
 * board at all (each lock adds 4 cells, each clear removes 10), one that is even but not a multiple of four needs a
 * line clear the planner never makes, and the rest are unbuilt for want of a build board alone.
 */
import { readFileSync } from 'node:fs';
import type { TechniqueDemoProfile } from './technique-demo-profile.ts';

const SIM = import.meta.dir;
const OPENERS = `${SIM}/../openers`;
const REPO = `${SIM}/../..`;
const TR = `${OPENERS}/basicdonating-technique.json`;

const NO_BUILD = '頁面將捐嘅方塊同 T 畫埋一幅（消行入面嘅方塊仲畫成淡色大楷），冇一幅淨係擺好方塊、未入 T 嘅板，planner 要嘅 build 板唔存在，所以冇試';
const cells = (rows: string[]) => rows.join('').replace(/-/g, '').length;

/** the measured reason a terrain of `n` cells has no demo */
export function terrainReason(n: number): string {
  if (n % 2) return `地形有 ${n} 格，係單數：每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出`;
  if (n % 4) return `地形有 ${n} 格，唔係 4 嘅倍數：要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）`;
  return `地形有 ${n} 格，係 4 嘅倍數，但${NO_BUILD}`;
}

/** every board's reason, read off the transcription */
export function unbuiltReasons(tr: any): Record<string, string> {
  const by = new Map<string, any>(tr.nodes.map((n: any) => [n.id, n]));
  const terrainOf = new Map<string, string>();
  for (const n of tr.nodes) if (n.kind === 'spin' && n.on) terrainOf.set(n.on, n.id);
  const out: Record<string, string> = {};
  for (const n of tr.nodes) {
    if (n.kind === 'illustration') out[n.id] = '示意圖（T 打完之後點挖、點打 Tetris），唔係捐嘅形本身';
    else if (n.kind === 'after') out[n.id] = `係 ${n.after_of} 打完 TSD 之後嘅盤面，${n.after_of} 冇示範，所以呢幅都冇`;
    else if (n.external)
      out[n.id] = `係 ${n.external} 嘅圖（原頁冇畫）：佢將地形、塞窿嘅 T 同之前嘅堆畫埋一幅，冇一幅淨係地形，冇地形可以砌`;
    else if (n.kind === 'spin' && n.on) out[n.id] = `TSD 企喺 ${n.on} 上面：${terrainReason(cells(by.get(n.on).rows))}`;
    else if (n.kind === 'spin')
      out[n.id] = 'transcription 冇記低呢幅係邊幅地形加方塊（冇 on；題目同答案對唔上嘅見 known_discrepancies），冇地形可以砌';
    else if (terrainOf.has(n.id)) out[n.id] = `係 ${terrainOf.get(n.id)} 嘅地形：${terrainReason(cells(n.rows))}`;
    else if (by.has(`${n.id}.answer`))
      out[n.id] = `係 ${n.id}.answer 嘅題目，但答案唔係呢幅加方塊（見 known_discrepancies），冇示範`;
    else out[n.id] = `捐嘅形（地形同方塊畫埋一幅，冇 T）：${NO_BUILD}`;
  }
  return out;
}

export const BASICDONATING_DEMOS: TechniqueDemoProfile = {
  key: 'basicdonating',
  tag: 'basicdonating',
  transcriptionPath: TR,
  artefactPath: `${REPO}/analysis/basicdonating-demos.json`,
  hashFiles: {
    planner: [`${SIM}/technique-demos.ts`, `${SIM}/technique-demo-profile.ts`, `${SIM}/technique-demos-basicdonating.ts`,
              `${SIM}/emit-technique-demos.ts`, `${SIM}/route-demos.ts`],
  },
  variant: 'k1',
  chains: [],
  unbuilt: unbuiltReasons(JSON.parse(readFileSync(TR, 'utf8'))),
  artefact: {
    schema: 'technique-demos/1',
    means: 'The constructed replays of the 基本的なドネイト page: none. The planner builds a terrain, then the page\'s own '
      + 'pieces off a build board, then fires the window; this page draws its donated pieces and the T on one board, so '
      + 'there is no build board to plan from. Every board is published unbuilt with its measured reason.',
    notEligible: 'constructed, not played: a demo\'s queue, hold and key inputs would be ours. No claim id, no badge, '
      + 'no figure in any count.',
    caveat: 'a terrain\'s cell count decides whether any demo could stand on it from an empty board (odd: never; even '
      + 'but not a multiple of four: only with a line clear, which this planner never makes); the rest are unbuilt for '
      + 'want of a build board, not by measurement of the planner.',
  },
  rules: () => [
    'a demo starts from an empty board, as every decoder does; the terrain is an exact cover of its grey cells by '
      + 'pieces the planner chose, every one reachable from spawn by the engine\'s own moves, no line cleared',
    'the page\'s own pieces are a build board\'s lower-case letters, one whole piece per letter; this page has no build board',
    'every board is unbuilt, with the reason read off the transcription: the terrain\'s cell count, or the missing build board',
  ],
};

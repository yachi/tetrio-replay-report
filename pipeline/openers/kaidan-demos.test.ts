/**
 * The 階段のドネイト (Kaidan Setups) constructed demos (`analysis/kaidan-demos.json`, from
 * `pipeline/sim/emit-technique-demos.ts --technique kaidan`; the planner is the shared `technique-demos.ts`, the Kaidan
 * half is `technique-demos-kaidan.ts`).
 *
 * NO DEMO IS BUILT, and that is the measurement this file pins. The page draws its terrains grey; its three chains
 * are planned, and the planner stops each at its first failing check. This test re-derives every reason from the
 * transcription on its own:
 *
 *   * the four-step staircase (`basic.terrain`) holds an ODD cell count: every lock adds four cells and every line
 *     clear removes ten, so a board built from empty always holds an even count. A proof, not a planner limit;
 *   * the two three-step staircases (`s3.terrain`, `j3.terrain`) are multiples of four and DO tile by tetrominoes
 *     (re-derived here by an exact-cover search over all seven kinds) — but every tiling uses a T, and the planner's
 *     dealing keeps the T's for the spin, so its words 「no cover by non-T pieces」 are the measurement and the
 *     terrain is not unbuildable in general;
 *   * the two DT砲 boards are not chains: their terrains are even but not multiples of four (a limit of THIS planner,
 *     which never clears a line), and both are drawn MIRRORED, so the as-drawn window the planner fires does not fit
 *     them (measured here with the corpus matcher), even if they were built.
 *
 * The payoff branch (a variant with a payoff ends its demo on the stood T) is the shared planner's, exercised on a
 * synthetic terrain by `parapet-demos.test.ts`; no chain here reaches it. The planner's mutants are measured
 * EQUIVALENT on the committed artefact and asserted byte-identical, so the day one starts to matter is a red build.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/kaidan-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, drawnCells, type DemoMutants } from '../sim/technique-demos.ts';
import { SHAPES, WIDTH } from '../sim/emit-replay.ts';
import { prepare, windowMatch } from '../sim/technique-facts.ts';
import { KAIDAN } from '../sim/technique-profile-kaidan.ts';
import { KAIDAN_DEMOS } from '../sim/technique-demos-kaidan.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/kaidan-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(KAIDAN_DEMOS.transcriptionPath, 'utf8'));
const V = TR.variants.find((v: any) => v.id === KAIDAN_DEMOS.variant);
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const ODD = (n: number) => `地形有 ${n} 格，係單數：每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出`;
const NO_COVER = '地形冇一個由非 T 方塊（每款最多兩粒）砌成嘅鋪法';
const ON_BASIC = '企喺四級樓梯嘅基本形上面：基本形砌唔到，所以呢幅都冇示範';
const DT = (n: number) => `連埋 DT砲 嘅盤面有 ${n} 格，係雙數但唔係 4 嘅倍數：${LIMIT}；而且頁面畫嘅係左右反轉嘅形，planner 用嘅照畫窗口就算砌到都對唔上`;
const AFTER = '打後嘅示意圖（頁面冇講係 ST積み 定 よしひろ積み），唔係階段のドネイト本身';

/** Boards no demo stands on, and the reason the artefact gives: the chains' are the planner's measured reasons, the
 *  rest the profile's. */
const DEMO_UNBUILT: Record<string, string> = {
  'basic.o': ODD(39),
  'basic.terrain': `basic.o 砌唔到：${ODD(39)}`,
  'basic.z': '係四級樓梯（basic.terrain）加一粒 Z：四級樓梯砌唔到（見 basic.o），所以呢幅都冇示範',
  'basic.spin': `TSD ${ON_BASIC}`,
  'basic.after': '係 basic.spin 之後嘅盤面，同一個原因冇示範',
  's3.s': NO_COVER,
  's3.terrain': `s3.s 砌唔到：${NO_COVER}`,
  's3.j': NO_COVER,
  'j3.terrain': `s3.j 砌唔到：${NO_COVER}`,
  'dt.amemiya.pre': DT(54),
  'dt.amemiya': `係 dt.amemiya.pre 上面打嘅 TSD：${DT(54)}`,
  'dt.anchor.pre': DT(58),
  'dt.anchor': `係 dt.anchor.pre 上面打嘅 TSD：${DT(58)}`,
  'after.1': AFTER,
  'after.2': AFTER,
};

const fresh = build(KAIDAN, KAIDAN_DEMOS);
const cellSet = (id: string) => new Set(drawnCells(byId.get(id).rows, TR.empty_letters).keys());

/** Every tiling of `cells` (y-UP engine indices) by tetrominoes, at most `limit[kind]` of each kind (absent:
 *  unlimited; 0: none), up to `cap`. */
function tilings(cells: Set<number>, limit: Record<string, number> = {}, cap = 50): number {
  let n = 0;
  const go = (left: Set<number>, used: Record<string, number>) => {
    if (n >= cap) return;
    if (!left.size) { n++; return; }
    const low = [...left].sort((a, b) => Math.floor(a / WIDTH) - Math.floor(b / WIDTH) || a - b)[0]!;
    const seen = new Set<string>();
    for (const kind of Object.keys(SHAPES)) {
      if ((used[kind] ?? 0) >= (limit[kind] ?? Infinity)) continue;
      for (const shape of SHAPES[kind]!) for (const [ox, oy] of shape) {
        const ax = (low % WIDTH) - ox, ay = Math.floor(low / WIDTH) - oy;
        const cs = shape.map(([dx, dy]: [number, number]) => [ax + dx, ay + dy]);
        if (cs.some(([x]) => x < 0 || x >= WIDTH)) continue;
        const idx = cs.map(([x, y]) => y * WIDTH + x).sort((a, b) => a - b);
        if (seen.has(`${kind}:${idx.join()}`) || !idx.every(c => left.has(c))) continue;
        seen.add(`${kind}:${idx.join()}`);
        go(new Set([...left].filter(c => !idx.includes(c))), { ...used, [kind]: (used[kind] ?? 0) + 1 });
      }
    }
  };
  go(cells, {});
  return n;
}

test('byte rebuild: the committed demos are what the planner produces now', () => {
  expect(serialise(fresh)).toBe(committedText);
});

test('quarantined and constructed; no demo built; every board unbuilt exactly once with its reason', () => {
  expect(committed.report_eligible).toBe(false);
  expect(committed.constructed).toBe(true);
  expect(committed.demos).toEqual([]);
  const unbuilt = Object.fromEntries(committed.unbuilt.map((u: any) => [u.node, u.reason]));
  expect(Object.entries(unbuilt).sort()).toEqual(Object.entries(DEMO_UNBUILT).sort());
  expect(committed.unbuilt.length).toBe(TR.nodes.length);
  expect(Object.keys(unbuilt).sort()).toEqual(TR.nodes.map((n: any) => n.id).sort());
  expect(KAIDAN_DEMOS.chains).toEqual([{ node: 'basic.o', terrain: 'basic.terrain' }, { node: 's3.s', terrain: 's3.terrain' },
                                       { node: 's3.j', terrain: 'j3.terrain' }]);
  expect(KAIDAN_DEMOS.variant).toBe('kaidan');
});

test('the reasons, re-derived from the transcription', () => {
  // the four-step staircase: odd — a proof
  expect(cellSet('basic.terrain').size).toBe(39);
  // the three-step staircases: multiples of four that tile, but never without a T
  for (const id of ['s3.terrain', 'j3.terrain']) {
    const c = cellSet(id);
    expect(c.size, id).toBe(28);
    expect(tilings(c), id).toBeGreaterThan(0);
    expect(tilings(c, { T: 0 }), id).toBe(0);
    expect(tilings(c, { T: 0, I: 2, J: 2, L: 2, O: 2, S: 2, Z: 2 }), id).toBe(0);
  }
  // the control: the same search finds a T-free tiling where there is one (a 4x2 block)
  expect(tilings(new Set([0, 1, 2, 3, 10, 11, 12, 13]), { T: 0 })).toBeGreaterThan(0);
  // the DT砲 boards: even, not multiples of four
  for (const [id, n] of [['dt.amemiya.pre', 54], ['dt.anchor.pre', 58]] as [string, number][]) {
    expect(cellSet(id).size, id).toBe(n);
    expect(n % 2 === 0 && n % 4 !== 0).toBe(true);
    expect(DEMO_UNBUILT[id]).toContain(`${cellSet(id).size} 格`);
  }
  // ...and drawn mirrored: at the drawn T the as-drawn window does not fit, the mirrored one does
  for (const a of V.agreement.filter((x: any) => x.mirrored)) {
    const rows: string[] = byId.get(a.board).rows;
    const board = rows.map(r => [...r].map(ch => ch === '-' ? '.' : 'X').join(''));
    const T = a.t_cells.map(([row, col]: number[]) => ({ row, col }));
    expect(prepare(TR, V).map(P => !!windowMatch(board, T, P)), a.board).toEqual([false, true]);
  }
  // the page's pieces on each chain's build board: whole pieces, as the planner reads them
  expect([byId.get('basic.o').adds, byId.get('s3.s').adds, byId.get('s3.j').adds]).toEqual(['o', 'sz', 'jz']);
  // the profile's reasons: the boards each names, by the transcription's own fields
  expect([byId.get('basic.z').on, byId.get('basic.spin').spin_of, byId.get('basic.after').after_of])
    .toEqual(['basic.terrain', 'basic.o', 'basic.spin']);
  expect([byId.get('dt.amemiya').spin_of, byId.get('dt.anchor').spin_of]).toEqual(['dt.amemiya.pre', 'dt.anchor.pre']);
  expect([byId.get('after.1').kind, byId.get('after.2').kind]).toEqual(['illustration', 'illustration']);
});

const T = 300_000;

/** MEASURED EQUIVALENT: every chain stops at a check on the drawing itself (an odd count, no T-free cover), before
 *  the planner's move search, its spin check or the engine arbiter, so none of their mutants can change a byte.
 *  Asserted byte-identical: the day a chain gets past those checks, these turn red. */
test('equivalent: the planner mutants change nothing (no chain reaches what they turn off)', () => {
  for (const m of ['noReach', 'baseSeeded', 'noSpinCheck', 'no180'] as (keyof DemoMutants)[])
    expect(serialise(build(KAIDAN, KAIDAN_DEMOS, { [m]: true })), m).toBe(committedText);
}, T);

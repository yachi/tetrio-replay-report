/**
 * The Imperial Cross constructed demos (`analysis/imperialcross-demos.json`, from `pipeline/sim/emit-technique-demos.ts
 * --technique imperialcross`; the planner is the shared `technique-demos.ts`, Imperial Cross's half is
 * `technique-demos-imperialcross.ts`).
 *
 * NO DEMO IS BUILT, and that is the measurement this file pins. The page draws its terrains grey; each chain
 * is planned, and the planner stops it at its first failing check. This test re-derives every reason from
 * the transcription on its own:
 *
 *   * the basic form and the bare cross hold an ODD number of cells, so no board built from empty is either
 *     of them (every lock adds 4 cells and every clear removes 10) — a proof, not a planner limit;
 *   * the TSD-shape terrain has no tiling by tetrominoes AT ALL (re-derived here by an exact-cover search
 *     over all seven kinds, unlimited): its corner cell's only piece runs down the wall and strands the cell
 *     beside it. So it is reachable only through line clears, which this planner never makes;
 *   * the cross-shape build's terrain (the cross plus the muted stack beside the Z) is even but not a
 *     multiple of four — a limit of THIS planner, worded as one.
 *
 * The profile's own reasons (the boards standing on another board's demo, the TST and ダブルダガー boards that
 * are not this technique) are checked against the transcription's own fields (`spin_of`, `after_of`, `on`,
 * the variant's `misses`). The day a demo is built, `demos` stops being empty here and the demo page's prose
 * (which says none is) must be re-read.
 *
 * The planner's mutants are all measured EQUIVALENT here (no chain reaches the move search, the arbiter or
 * the spin check) and asserted byte-identical, so the day one starts to matter is a red build.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/imperialcross-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, drawnCells, type DemoMutants } from '../sim/technique-demos.ts';
import { SHAPES, WIDTH } from '../sim/emit-replay.ts';
import { IMPERIALCROSS } from '../sim/technique-profile-imperialcross.ts';
import { IMPERIALCROSS_DEMOS } from '../sim/technique-demos-imperialcross.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/imperialcross-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(IMPERIALCROSS_DEMOS.transcriptionPath, 'utf8'));
const V = TR.variants.find((v: any) => v.id === IMPERIALCROSS_DEMOS.variant);
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));

const PLANNER_LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const NO_COVER = '地形冇一個由非 T 方塊（每款最多兩粒）砌成嘅鋪法';

/** Boards no demo stands on, and the reason the artefact gives: twelve are the profile's, four the
 *  planner's measured reasons for its two chains. */
const DEMO_UNBUILT: Record<string, string> = {
  'basic': '基本形冇畫頁面嘅方塊，成幅都係灰色嘅元地形（暗灰格當空）：有 29 格，係單數；每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出',
  'basic.after': '係 basic.spin 之後嘅盤面，同一個原因冇示範',
  'basic.spin': '係基本形上面打嘅 T：基本形砌唔到，所以呢幅都冇示範',
  'basic.t_down': '係 T 跌入基本形途中嘅示意圖：同一個原因冇示範',
  'basic.t_drop': '係 T 跌入基本形途中嘅示意圖：基本形砌唔到，所以冇示範',
  'basic.t_left': '係 T 跌入基本形途中嘅示意圖：同一個原因冇示範',
  'basic.t_up': '係 T 跌入基本形途中嘅示意圖：同一個原因冇示範',
  'cross.terrain': '十字形元地形有 25 格，係單數：由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出',
  'cross.z': `地形有 30 格，唔係 4 嘅倍數：${PLANNER_LIMIT}`,
  'cross.z.terrain': `cross.z 砌唔到：地形有 30 格，唔係 4 嘅倍數：${PLANNER_LIMIT}`,
  'dagger': '呢幅係ダブルダガー，唔係呢個手法；佢企喺 dagger.terrain 上面',
  'dagger.terrain': 'dagger 嘅地形：dagger 唔係呢個手法，所以冇示範',
  'tsd.oj': '用 J 砌嘅係 TST 位，唔係呢個手法；而且同 tsd.oz 企喺同一幅地形上面，嗰幅點解砌唔到寫喺 tsd.oz 度',
  'tsd.ol': '同 tsd.oz 企喺同一幅 TSD 形地形（tsd.terrain）上面，嗰幅點解砌唔到寫喺 tsd.oz 度',
  'tsd.oz': NO_COVER,
  'tsd.terrain': `tsd.oz 砌唔到：${NO_COVER}`,
};

const fresh = build(IMPERIALCROSS, IMPERIALCROSS_DEMOS);
const count = (id: string) => drawnCells(byId.get(id).rows, TR.empty_letters).size;

/** Every tiling of `cells` (y-UP engine indices) by tetrominoes of any kind, any number of each. */
function tilings(cells: Set<number>, cap = 1000): number {
  let n = 0;
  const go = (left: Set<number>) => {
    if (n >= cap) return;
    if (!left.size) { n++; return; }
    const low = [...left].sort((a, b) => Math.floor(a / WIDTH) - Math.floor(b / WIDTH) || a - b)[0]!;
    const seen = new Set<string>();
    for (const kind of Object.keys(SHAPES)) for (const shape of SHAPES[kind]!) for (const [ox, oy] of shape) {
      const ax = (low % WIDTH) - ox, ay = Math.floor(low / WIDTH) - oy;
      const cs = shape.map(([dx, dy]: [number, number]) => [ax + dx, ay + dy]);
      if (cs.some(([x]) => x < 0 || x >= WIDTH)) continue;
      const idx = cs.map(([x, y]) => y * WIDTH + x).sort((a, b) => a - b);
      if (seen.has(idx.join()) || !idx.every(c => left.has(c))) continue;
      seen.add(idx.join());
      go(new Set([...left].filter(c => !idx.includes(c))));
    }
  };
  go(cells);
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
  expect(IMPERIALCROSS_DEMOS.chains).toEqual([{ node: 'tsd.oz', terrain: 'tsd.terrain' },
                                              { node: 'cross.z', terrain: 'cross.z.terrain' }]);
});

test('the planner\'s reasons, re-derived from the transcription', () => {
  // the basic form and the bare cross: odd cell counts (B read as empty), a proof
  expect(count('basic')).toBe(29);
  expect(count('cross.terrain')).toBe(25);
  expect([...byId.get('basic').rows.join('')].filter((ch: string) => /[a-z]/.test(ch) && ch !== 'c')).toEqual([]);
  // the TSD shape: no tiling by any tetromino at all, so not even a planner that allowed T or any count could
  // build it without clearing a line
  const tsd = new Set(drawnCells(byId.get('tsd.terrain').rows, TR.empty_letters).keys());
  expect(tsd.size).toBe(24);
  expect(tilings(tsd)).toBe(0);
  // the control: the same search finds tilings where there are some (a 4x2 block: two I's, two O's, ...)
  expect(tilings(new Set([0, 1, 2, 3, 10, 11, 12, 13]))).toBeGreaterThan(0);
  // the cross-shape build's terrain: even, not a multiple of four
  expect(count('cross.z.terrain')).toBe(30);
  expect(DEMO_UNBUILT['cross.z']).toContain(`${count('cross.z.terrain')} 格`);
  // the profile's reasons: the boards each names, by the transcription's own fields
  expect(byId.get('basic.spin').spin_of).toBe('basic');
  expect(byId.get('basic.after').after_of).toBe('basic.spin');
  for (const id of ['basic.t_drop', 'basic.t_up', 'basic.t_left', 'basic.t_down']) expect(byId.get(id).kind).toBe('illustration');
  for (const id of ['tsd.oz', 'tsd.ol', 'tsd.oj']) expect(byId.get(id).on).toBe('tsd.terrain');
  expect(byId.get('dagger').on).toBe('dagger.terrain');
  for (const id of ['tsd.oj', 'dagger']) expect(V.misses).toContain(id);
});

const T = 300_000;

/** MEASURED EQUIVALENT: every chain stops at a check on the drawing itself (no cover, or a cell count),
 *  before the planner's move search, its spin check or the engine arbiter, so none of their mutants can
 *  change a byte. Asserted byte-identical: the day a chain gets past those checks, these turn red. */
test('equivalent: the planner mutants change nothing (no chain reaches what they turn off)', () => {
  for (const m of ['noReach', 'baseSeeded', 'noSpinCheck', 'no180'] as (keyof DemoMutants)[])
    expect(serialise(build(IMPERIALCROSS, IMPERIALCROSS_DEMOS, { [m]: true })), m).toBe(committedText);
}, T);

/**
 * The BT砲 (途中BT) constructed demos (`analysis/btcannon-demos.json`, from `pipeline/sim/emit-technique-demos.ts
 * --technique btcannon`; the planner is the shared `technique-demos.ts`, BT砲's half is `technique-demos-btcannon.ts`).
 *
 * NO DEMO IS BUILT AND NO CHAIN IS PLANNED, and this file pins why, re-deriving every reason from the transcription:
 *
 *   * the shared planner reads a build's page pieces as its LOWER-case letters and requires the build less them
 *     to be its terrain. The 欄干 build (`bt.build`) stands on a terrain with a lower-case L of its own, so the
 *     planner would refuse it outright; the four 72積み builds draw the page's pieces in UPPER case (measured: the
 *     upper-case letters are exactly each build's `adds`) and the 72積み stack in lower case. No chain is planned.
 *   * so every board carries the profile's reason, and each cell count it prints is re-derived here: the basic form
 *     and three of the terrains hold an ODD number of cells (a proof: every lock adds 4, every clear removes 10),
 *     one is even but not a multiple of four (a planner limit, worded as one), and one, s72.3's, is a multiple of
 *     four — stopped by the reading alone, which its reason says instead of calling it unbuildable.
 *
 * The planner's mutants are all EQUIVALENT here (with no chain nothing reaches them) and asserted byte-identical.
 * The day a chain is added, `demos` may stop being empty and the demo page's prose (which says none is) must be
 * re-read.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/btcannon-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, drawnCells, type DemoMutants } from '../sim/technique-demos.ts';
import { encodePlace } from '../sim/emit-replay.ts';
import { BTCANNON } from '../sim/technique-profile-btcannon.ts';
import { BTCANNON_DEMOS } from '../sim/technique-demos-btcannon.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/btcannon-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(BTCANNON_DEMOS.transcriptionPath, 'utf8'));
const V = TR.variants.find((v: any) => v.id === BTCANNON_DEMOS.variant);
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const ODD = '每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出';
const UPPER = '原頁將佢加嘅方塊畫大楷、72積み 本身嘅方塊畫細楷，而呢個 planner 當細楷係頁面方塊，所以冇排呢幅（係讀法對唔上，唔係量過砌唔到）';

/** Every board no demo stands on, with the reason the artefact gives (all of them the profile's). */
const DEMO_UNBUILT: Record<string, string> = {
  'basic': `基本形冇畫頁面嘅方塊，成幅都係灰色嘅元地形：有 45 格，係單數：${ODD}`,
  'basic.after': '係 basic.spin 之後嘅盤面（由 tst.spin 推出嚟），同一個原因冇示範',
  'basic.spin': '係基本形上面打嘅 TSD：基本形砌唔到，所以呢幅都冇示範',
  'bt.build': '企喺 bt.terrain 上面，嗰幅有 35 格，係單數，砌唔到；而且佢元地形自己有一粒細楷 L，呢個 planner 會當咗佢係頁面方塊',
  'bt.terrain': `同 parapet.terrain 一樣嘅元地形（佔格一樣）：有 35 格，係單數：${ODD}`,
  'parapet': '呢幅係欄干，唔係呢個手法；佢企喺 parapet.terrain 上面，嗰幅砌唔到',
  'parapet.terrain': `欄干嘅元地形有 35 格，係單數：${ODD}`,
  's72.1': `企喺 s72.1.terrain 上面，嗰幅有 26 格，唔係 4 嘅倍數：${LIMIT}`,
  's72.1.terrain': `s72.1 嘅元地形：有 26 格，唔係 4 嘅倍數：${LIMIT}`,
  's72.2': `企喺 s72.2.terrain 上面，嗰幅有 25 格，係單數：${ODD}`,
  's72.2.terrain': `s72.2 嘅元地形：有 25 格，係單數：${ODD}`,
  's72.3': `${UPPER}；佢嘅元地形有 28 格`,
  's72.3.terrain': `s72.3 嘅元地形（28 格）：${UPPER}`,
  's72.4': `企喺 s72.4.terrain 上面，嗰幅有 27 格，係單數：${ODD}`,
  's72.4.terrain': `s72.4 嘅元地形：有 27 格，係單數：${ODD}`,
  'tst.spin': '係 basic.after 上面打嘅 TST，同一個原因冇示範',
};

const fresh = build(BTCANNON, BTCANNON_DEMOS);
const count = (id: string) => drawnCells(byId.get(id).rows, TR.empty_letters).size;
const cellsOf = (rows: string[], letter: string) => [...drawnCells(rows, TR.empty_letters)]
  .filter(([, ch]) => ch === letter).map(([c]) => c).sort((a, b) => a - b);

test('byte rebuild: the committed demos are what the planner produces now', () => {
  expect(serialise(fresh)).toBe(committedText);
});

test('quarantined and constructed; no chain, no demo; every board unbuilt exactly once with its reason', () => {
  expect(committed.report_eligible).toBe(false);
  expect(committed.constructed).toBe(true);
  expect(committed.demos).toEqual([]);
  expect(BTCANNON_DEMOS.chains).toEqual([]);
  const unbuilt = Object.fromEntries(committed.unbuilt.map((u: any) => [u.node, u.reason]));
  expect(Object.entries(unbuilt).sort()).toEqual(Object.entries(DEMO_UNBUILT).sort());
  expect(committed.unbuilt.length).toBe(TR.nodes.length);
  expect(Object.keys(unbuilt).sort()).toEqual(TR.nodes.map((n: any) => n.id).sort());
});

test('why no chain: the builds do not draw their page pieces in lower case on a lower-case-free terrain', () => {
  // the 欄干 build: its terrain carries a lower-case L, so the build less its lower case is not its terrain
  const bt = byId.get('bt.build');
  expect(bt.on).toBe('bt.terrain');
  expect(byId.get('bt.terrain').rows.join('')).toMatch(/l/);
  expect(bt.adds).toBe('jz');
  // the 72積み builds: the upper-case letters are exactly each build's adds, each a whole piece; the lower case
  // (the 72積み stack) is on the terrain
  for (const i of [1, 2, 3, 4]) {
    const n = byId.get(`s72.${i}`), t = byId.get(`s72.${i}.terrain`);
    const upper = [...new Set(n.rows.join('').replace(/[^A-Z]/g, ''))].sort().join('');
    expect(upper, n.id).toBe([...n.adds].sort().join(''));
    for (const L of n.adds) expect(() => encodePlace(L, cellsOf(n.rows, L)), `${n.id} ${L}`).not.toThrow();
    expect(t.rows.join('').replace(/[^a-z]/g, '').replace(/c/g, '').length, t.id).toBeGreaterThan(0);
  }
});

test('the reasons\' cell counts, re-derived from the transcription', () => {
  const want: Record<string, number> = { 'basic': 45, 'parapet.terrain': 35, 'bt.terrain': 35, 's72.1.terrain': 26,
                                         's72.2.terrain': 25, 's72.3.terrain': 28, 's72.4.terrain': 27 };
  for (const [id, n] of Object.entries(want)) {
    expect(count(id), id).toBe(n);
    expect(DEMO_UNBUILT[id], id).toContain(`${n} 格`);
    const kind = n % 2 ? ODD : n % 4 ? LIMIT : UPPER;
    expect(DEMO_UNBUILT[id], id).toContain(kind);
  }
  // the boards standing on another board, by the transcription's own fields
  expect(byId.get('basic.spin').spin_of).toBe('basic');
  expect(byId.get('tst.spin').spin_of).toBe('basic.after');
  expect(byId.get('bt.terrain').same_occupancy_as).toBe('parapet.terrain');
  expect(byId.get('parapet').on).toBe('parapet.terrain');
  expect(V.misses).toContain('parapet');
  for (const i of [1, 2, 3, 4]) expect(byId.get(`s72.${i}`).on).toBe(`s72.${i}.terrain`);
});

const T = 300_000;

/** MEASURED EQUIVALENT: with no chain, nothing reaches the move search, the spin check or the arbiter. */
test('equivalent: the planner mutants change nothing (no chain reaches what they turn off)', () => {
  for (const m of ['noReach', 'baseSeeded', 'noSpinCheck', 'no180'] as (keyof DemoMutants)[])
    expect(serialise(build(BTCANNON, BTCANNON_DEMOS, { [m]: true })), m).toBe(committedText);
}, T);

/**
 * The 途中DT砲 constructed demos (`analysis/dtcannon-demos.json`, from `pipeline/sim/emit-technique-demos.ts
 * --technique dtcannon`; the planner is the shared `technique-demos.ts`, this page's half `technique-demos-dtcannon.ts`).
 *
 * NO DEMO IS BUILT AND NO CHAIN IS PLANNED, and this file pins why, re-deriving every reason from the transcription:
 * every board's cell count is re-counted here, and each reason's kind follows from it — ODD (a proof: every lock
 * adds 4 cells, every clear removes 10, so a board built from empty holds an even count), even but not a multiple
 * of four (a planner limit, worded as one), or a multiple of four, which only the DTDT boards (開幕DT砲's residue,
 * no terrain of its own on the page) and two のそみ砲 illustrations are, and their reasons say so instead of calling
 * them unbuildable.
 *
 * The planner's mutants are all EQUIVALENT here (with no chain nothing reaches them) and asserted byte-identical.
 * The day a chain is added, `demos` may stop being empty and the demo page's prose (which says none is) must be
 * re-read.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/dtcannon-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, drawnCells, type DemoMutants } from '../sim/technique-demos.ts';
import { DTCANNON } from '../sim/technique-profile-dtcannon.ts';
import { DTCANNON_DEMOS } from '../sim/technique-demos-dtcannon.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/dtcannon-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(DTCANNON_DEMOS.transcriptionPath, 'utf8'));
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));

const LIMIT = '要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）';
const ODD = '每粒方塊加 4 格、每消一行減 10 格，由空盤砌出嚟嘅盤面格數一定係雙數，所以砌唔出';
const RESIDUE = '呢幅係開幕DT砲打完之後嘅殘局加新方塊，頁面冇另外畫佢嘅元地形，而呢個 planner 要一幅元地形先排得，所以冇排呢幅（係讀法對唔上，唔係量過砌唔到）';
const ILLUS = '係のそみ砲嘅插圖，頁面冇將佢分開畫做元地形同頁面方塊，而呢個 planner 要咁先排得，所以冇排示範（係讀法對唔上，唔係量過砌唔到）';

/** Every board's cell count, as the reasons print it. */
const CELLS: Record<string, number> = {
  'basic': 45, 'basic.spin': 49, 'basic.after': 29, 'tst.spin': 33, 'wait.terrain': 22, 'wait.i': 30,
  'wait.terrain2': 22, 'wait.dt': 45, 'roof.base': 29, 'roof.so': 37, 'roof.build': 37, 'roof.fill': 33,
  'done.terrain': 43, 'done.build': 51, 'done.cells': 51, 'jhook.terrain': 57, 'jhook.build': 61,
  'dtdt.base': 52, 'dtdt.spin': 56, 'dtdt.tst.base': 64, 'dtdt.tst': 68,
  'nozomi.1': 28, 'nozomi.2': 46, 'nozomi.3': 44, 'nozomi.4': 58,
};

const fresh = build(DTCANNON, DTCANNON_DEMOS);
const count = (id: string) => drawnCells(byId.get(id).rows, TR.empty_letters).size;

test('byte rebuild: the committed demos are what the planner produces now', () => {
  expect(serialise(fresh)).toBe(committedText);
});

test('quarantined and constructed; no chain, no demo; every board unbuilt exactly once', () => {
  expect(committed.report_eligible).toBe(false);
  expect(committed.constructed).toBe(true);
  expect(committed.demos).toEqual([]);
  expect(DTCANNON_DEMOS.chains).toEqual([]);
  expect(committed.unbuilt.length).toBe(TR.nodes.length);
  expect(committed.unbuilt.map((u: any) => u.node).sort()).toEqual(TR.nodes.map((n: any) => n.id).sort());
  expect(Object.keys(CELLS).sort()).toEqual(TR.nodes.map((n: any) => n.id).sort());
});

test('the reasons\' cell counts and kinds, re-derived from the transcription', () => {
  const reason = Object.fromEntries(committed.unbuilt.map((u: any) => [u.node, u.reason]));
  for (const [id, n] of Object.entries(CELLS)) {
    expect(count(id), id).toBe(n);
    expect(reason[id], id).toContain(`${n} 格`);
    const kind = id.startsWith('nozomi') ? ILLUS : n % 2 ? ODD : n % 4 ? LIMIT : RESIDUE;
    expect(reason[id], id).toContain(kind);
    if (kind === RESIDUE) expect(id.startsWith('dtdt'), id).toBe(true);
  }
  // the multiples of four are exactly the DTDT boards and two のそみ砲 illustrations
  expect(Object.entries(CELLS).filter(([, n]) => n % 4 === 0).map(([id]) => id).sort())
    .toEqual(['dtdt.base', 'dtdt.spin', 'dtdt.tst', 'dtdt.tst.base', 'nozomi.1', 'nozomi.3']);
  for (const id of ['nozomi.1', 'nozomi.2', 'nozomi.3', 'nozomi.4']) expect(byId.get(id).kind, id).toBe('illustration');
  // the DTDT boards have no terrain node of their own: the base is derived from the spin board
  expect(byId.get('dtdt.base').derived).toBe(true);
  expect(byId.get('dtdt.spin').on).toBe('dtdt.base');
  // the only even build, wait.i, stands on a terrain carrying a lower-case Z of its own
  expect(byId.get('wait.i').on).toBe('wait.terrain');
  expect(byId.get('wait.terrain').rows.join('')).toMatch(/z/);
});

const T = 300_000;

/** MEASURED EQUIVALENT: with no chain, nothing reaches the move search, the spin check or the arbiter. */
test('equivalent: the planner mutants change nothing (no chain reaches what they turn off)', () => {
  for (const m of ['noReach', 'baseSeeded', 'noSpinCheck', 'no180'] as (keyof DemoMutants)[])
    expect(serialise(build(DTCANNON, DTCANNON_DEMOS, { [m]: true })), m).toBe(committedText);
}, T);

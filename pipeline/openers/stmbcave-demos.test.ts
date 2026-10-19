/**
 * The STMB Cave constructed demos (`analysis/stmbcave-demos.json`, from `pipeline/sim/emit-technique-demos.ts
 * --technique stmbcave`; the planner is the shared `technique-demos.ts`, STMB Cave's half is
 * `technique-demos-stmbcave.ts`).
 *
 * NO DEMO IS BUILT, and that is the measurement this file pins. Every chain is planned, and the planner
 * stops each at its first failing check; this test re-derives each of those reasons from the
 * transcription on its own, and beside them the facts that would stop the chain even if that first check
 * were fixed (a terrain whose cell count is odd cannot be reached from an empty board: every lock adds 4
 * cells and every clear removes 10). The day a demo is built, `demos` stops being empty here and the
 * demo page's prose (which says none is) must be re-read.
 *
 *   1. byte rebuild; 2. quarantine; 3. every board unbuilt exactly once, with the artefact's reason;
 *   4. each planner reason re-derived; 5. the planner's mutants, all measured EQUIVALENT here (no chain
 *      reaches the move search, the arbiter or the spin check) and asserted byte-identical, so the day one
 *      starts to matter is a red build.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/stmbcave-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, drawnCells, type DemoMutants } from '../sim/technique-demos.ts';
import { encodePlace } from '../sim/emit-replay.ts';
import { prepare, windowMatch } from '../sim/technique-facts.ts';
import { STMBCAVE } from '../sim/technique-profile-stmbcave.ts';
import { STMBCAVE_DEMOS } from '../sim/technique-demos-stmbcave.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/stmbcave-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(STMBCAVE_DEMOS.transcriptionPath, 'utf8'));
const V = TR.variants.find((v: any) => v.id === STMBCAVE_DEMOS.variant);
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));

/** Boards no demo stands on, and the reason the artefact gives: three are the profile's (boards that
 *  stand on another board's demo), six the planner's measured reasons for its three chains. */
const DEMO_UNBUILT: Record<string, string> = {
  'basic.build': '地形有 14 格，唔係 4 嘅倍數：要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）',
  'basic.build.terrain': 'basic.build 砌唔到：地形有 14 格，唔係 4 嘅倍數：要消過行先砌得出，而呢個 planner 唔消行（係 planner 嘅限制，唔係砌唔出）',
  'basic.terrain': '原頁將呢幅地形畫偏咗一格（個坑喺第 3 至 5 欄，上面砌好嗰幅喺第 4 至 6 欄，由 0 數）；示範要企嘅係由砌好嗰幅推返出嚟嘅地形，嗰幅點解砌唔到寫喺佢自己度',
  'feature.after': '係 feature.spin 之後嘅盤面，同一個原因冇示範',
  'feature.pre': '頁面嘅 J 畫咗 2 格，唔係一粒',
  'feature.spin': '係 feature.pre 上面打嘅 T：feature.pre 砌唔到，所以呢幅都冇示範',
  'feature.terrain': 'feature.pre 砌唔到：頁面嘅 J 畫咗 2 格，唔係一粒',
  'similar.build': '頁面嘅 S 唔係 S 嘅形',
  'similar.terrain': 'similar.build 砌唔到：頁面嘅 S 唔係 S 嘅形',
};

const fresh = build(STMBCAVE, STMBCAVE_DEMOS);
const cells = (rows: string[], letters: string) => [...drawnCells(rows, TR.empty_letters)]
  .filter(([, ch]) => letters.includes(ch)).map(([c]) => c).sort((a, b) => a - b);

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
  expect(STMBCAVE_DEMOS.chains.map(c => c.node)).toEqual(['basic.build', 'feature.pre', 'similar.build']);
});

test('the planner\'s reasons, re-derived from the transcription', () => {
  // basic.build: its page pieces are a whole Z and a whole S, its terrain is what is left, and that
  // terrain has a cell count that is even but not a multiple of four
  const bb = byId.get('basic.build').rows;
  expect(() => encodePlace('Z', cells(bb, 'z'))).not.toThrow();
  expect(() => encodePlace('S', cells(bb, 's'))).not.toThrow();
  const t1 = drawnCells(byId.get('basic.build.terrain').rows, TR.empty_letters).size;
  expect(t1 % 2).toBe(0);
  expect(t1 % 4).not.toBe(0);
  expect(DEMO_UNBUILT['basic.build']).toContain(`${t1} 格`);
  // and even built, the page's basic form is a local sketch: the T the window anchors on it completes
  // only one row, so it could not be the full TSD the demo has to fire
  const P = prepare(TR, V)[0]!;
  const board = bb.map((r: string) => [...r].map(ch => ch === '-' ? '.' : 'X').join(''));
  const slot = TR.variants[0].agreement.find((a: any) => a.board === 'basic.build').t_cells.map(([row, col]: number[]) => ({ row, col }));
  expect(windowMatch(board, slot, P)).toBeTruthy();
  const withT = bb.map((r: string) => [...r].map(ch => ch !== '-'));
  for (const q of slot) withT[q.row]![q.col] = true;
  expect(withT.filter((r: boolean[]) => r.every(Boolean)).length).toBe(1);
  // feature.pre: its J is two lower-case cells (the third is drawn muted, in the cleared row); and its
  // terrain's cell count is ODD, so no plan could stand on it even with the J redrawn
  const fp = byId.get('feature.pre').rows;
  expect(cells(fp, 'j').length).toBe(2);
  expect(cells(fp, 'J').length).toBe(1);
  expect(DEMO_UNBUILT['feature.pre']).toContain(`${cells(fp, 'j').length} 格`);
  expect(drawnCells(byId.get('feature.terrain').rows, TR.empty_letters).size % 2).toBe(1);
  // similar.build: its s is a Z's shape; and its terrain's cell count is ODD too
  const sb = byId.get('similar.build').rows;
  expect(() => encodePlace('S', cells(sb, 's'))).toThrow();
  expect(() => encodePlace('Z', cells(sb, 's'))).not.toThrow();
  expect(drawnCells(byId.get('similar.terrain').rows, TR.empty_letters).size % 2).toBe(1);
});

const T = 300_000;

/** MEASURED EQUIVALENT: every chain stops at a check on the drawing itself, before the planner's move
 *  search, its spin check or the engine arbiter, so none of their mutants can change a byte. Asserted
 *  byte-identical: the day a chain gets past those checks, these turn red and need real symptoms. */
test('equivalent: the planner mutants change nothing (no chain reaches what they turn off)', () => {
  for (const m of ['noReach', 'baseSeeded', 'noSpinCheck', 'no180'] as (keyof DemoMutants)[])
    expect(serialise(build(STMBCAVE, STMBCAVE_DEMOS, { [m]: true })), m).toBe(committedText);
}, T);

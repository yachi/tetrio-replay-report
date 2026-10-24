/**
 * The 基本的なドネイト (basic donating) constructed demos (`analysis/basicdonating-demos.json`, from
 * `pipeline/sim/emit-technique-demos.ts --technique basicdonating`; the planner is the shared `technique-demos.ts`, the
 * page's half `technique-demos-basicdonating.ts`).
 *
 * NO DEMO IS BUILT, and no chain is planned: the planner builds a terrain, then the page's own pieces off a BUILD board
 * (the terrain plus lower-case pieces, before the T), and this page draws no such board — each answer draws the
 * donated pieces and the T together, the pieces in the cleared rows muted upper case. So every board is published
 * unbuilt, and this test re-derives each reason from the transcription on its own:
 *
 *   * a terrain with an ODD cell count (counted here with the planner's own `drawnCells`) cannot be built from an
 *     empty board at all — every lock adds four cells and every line clear removes ten. A proof;
 *   * one that is even but not a multiple of four needs a line clear, which this planner never makes. A planner limit;
 *   * the rest are unbuilt for want of a build board alone, which is the profile's reading, not a measurement.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/basicdonating-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, drawnCells, type DemoMutants } from '../sim/technique-demos.ts';
import { BASICDONATING } from '../sim/technique-profile-basicdonating.ts';
import { BASICDONATING_DEMOS, unbuiltReasons } from '../sim/technique-demos-basicdonating.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/basicdonating-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(BASICDONATING_DEMOS.transcriptionPath, 'utf8'));
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));
const size = (id: string) => drawnCells(byId.get(id).rows, TR.empty_letters).size;

/** How many boards carry each kind of reason (the reasons themselves are re-derived below, board by board). */
const KINDS = { odd: 14, not_mult4: 6, no_build_board: 46, after: 2, illustration: 2, no_on: 3, question_mismatch: 2,
                external: 1 };

test('byte rebuild: the committed demos are what the planner produces now', () => {
  expect(serialise(build(BASICDONATING, BASICDONATING_DEMOS))).toBe(committedText);
});

test('quarantined and constructed; no demo built; every board unbuilt exactly once with its reason', () => {
  expect(committed.report_eligible).toBe(false);
  expect(committed.constructed).toBe(true);
  expect(committed.demos).toEqual([]);
  expect(BASICDONATING_DEMOS.chains).toEqual([]);
  expect(committed.unbuilt.map((u: any) => u.node).sort()).toEqual(TR.nodes.map((n: any) => n.id).sort());
  expect(new Set(committed.unbuilt.map((u: any) => u.node)).size).toBe(TR.nodes.length);
  const want = unbuiltReasons(TR);
  for (const u of committed.unbuilt) expect(u.reason, u.node).toBe(want[u.node]);
});

test('the reasons, re-derived from the transcription', () => {
  const r = unbuiltReasons(TR);
  const kinds: Record<string, number> = {};
  const add = (k: string) => (kinds[k] = (kinds[k] ?? 0) + 1);
  // the terrain each spin stands on (its `on`), and every node that is some spin's terrain
  const terrainOf = new Map<string, string>();
  for (const n of TR.nodes) if (n.kind === 'spin' && n.on) terrainOf.set(n.on, n.id);
  for (const n of TR.nodes) {
    const terrain = n.kind === 'spin' ? n.on : terrainOf.has(n.id) ? n.id : null;
    if (n.kind === 'illustration') { add('illustration'); continue; }
    if (n.external) { expect(r[n.id], n.id).toContain(n.external); add('external'); continue; }
    if (n.kind === 'after') { expect(r[n.id], n.id).toContain(n.after_of); add('after'); continue; }
    if (terrain) {
      const k = size(terrain);
      expect(r[n.id], n.id).toContain(`地形有 ${k} 格`);
      if (k % 2) { expect(r[n.id]).toContain('單數'); add('odd'); }
      else if (k % 4) { expect(r[n.id]).toContain('唔係 4 嘅倍數'); add('not_mult4'); }
      else { expect(r[n.id]).toContain('build 板唔存在'); add('no_build_board'); }
      continue;
    }
    if (n.kind === 'spin') { expect(r[n.id]).toContain('冇 on'); add('no_on'); continue; }
    if (byId.has(`${n.id}.answer`)) {
      // the question whose answer is not it plus pieces: a known discrepancy, measured by the gate
      expect(TR.known_discrepancies.map((d: any) => d.id ?? d)).toContainEqual(expect.stringContaining(`${n.id}.answer:question`));
      add('question_mismatch'); continue;
    }
    expect(r[n.id], n.id).toContain('build 板唔存在');
    add('no_build_board');
  }
  expect(kinds).toEqual(KINDS);
  expect(total(kinds)).toBe(TR.nodes.length);
  // the control: the parity proof is right — a board built of whole pieces with no clear is a multiple of four
  expect(drawnCells(['jjj-------', '--j-------'], '').size % 4).toBe(0);
});

const total = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);

/** MEASURED EQUIVALENT: no chain is planned, so no planner mutant can change a byte. Asserted byte-identical: the day
 *  a chain is added, these turn red and need their own symptoms. */
test('equivalent: the planner mutants change nothing (no chain is planned)', () => {
  for (const m of ['noReach', 'baseSeeded', 'noSpinCheck', 'no180'] as (keyof DemoMutants)[])
    expect(serialise(build(BASICDONATING, BASICDONATING_DEMOS, { [m]: true })), m).toBe(committedText);
});

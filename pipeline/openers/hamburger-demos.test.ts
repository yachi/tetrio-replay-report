/**
 * The ハンバーガー (Hamburger) constructed demos (`analysis/hamburger-demos.json`, from
 * `pipeline/sim/emit-technique-demos.ts --technique hamburger`; the planner is the shared `technique-demos.ts`, this
 * page's half `technique-demos-hamburger.ts`).
 *
 * NO DEMO IS BUILT AND NO CHAIN IS PLANNED, and this file pins why, re-deriving every reason's figure from the
 * transcription: every board but the Tetris illustration has an ODD cell count (a proof: each lock adds 4 cells and
 * each line clear removes 10, so a board built from empty always holds an even count); the Tetris board is a
 * multiple of four and is reached only through line clears, which the planner never makes (a planner limit).
 *
 * The planner's mutants are all EQUIVALENT here (with no chain nothing reaches them) and asserted byte-identical.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/hamburger-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, drawnCells, type DemoMutants } from '../sim/technique-demos.ts';
import { HAMBURGER } from '../sim/technique-profile-hamburger.ts';
import { HAMBURGER_DEMOS } from '../sim/technique-demos-hamburger.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/hamburger-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(HAMBURGER_DEMOS.transcriptionPath, 'utf8'));
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));
const reason: Record<string, string> = Object.fromEntries(committed.unbuilt.map((u: any) => [u.node, u.reason]));

/** Every board's cell count, as the reasons print it. */
const CELLS: Record<string, number> = {
  terrain: 21, zbuild: 21, softdrop: 25, spin: 25, 'spin.after': 15, repeat: 39, tetris: 64,
};
const fresh = build(HAMBURGER, HAMBURGER_DEMOS);
const count = (id: string) => drawnCells(byId.get(id).rows, TR.empty_letters).size;

test('byte rebuild: the committed demos are what the planner produces now', () => {
  expect(serialise(fresh)).toBe(committedText);
});

test('quarantined and constructed; no chain, no demo; every board unbuilt exactly once', () => {
  expect(committed.report_eligible).toBe(false);
  expect(committed.constructed).toBe(true);
  expect(committed.demos).toEqual([]);
  expect(HAMBURGER_DEMOS.chains).toEqual([]);
  expect(committed.unbuilt.map((u: any) => u.node).sort()).toEqual(TR.nodes.map((n: any) => n.id).sort());
  expect(Object.keys(CELLS).sort()).toEqual(TR.nodes.map((n: any) => n.id).sort());
});

test('every board\'s cell count, re-derived; the odd ones say so, the Tetris board names the planner limit', () => {
  for (const [id, n] of Object.entries(CELLS)) {
    expect(count(id), id).toBe(n);
    expect(reason[id], id).toContain(`${n} 格`);
    if (n % 2) expect(reason[id], id).toContain('係單數');
    else {
      expect(n % 4, id).toBe(0);
      expect(reason[id], id).toContain('planner 嘅限制');
    }
  }
});

test('equivalent: the planner mutants change nothing (no chain reaches what they turn off)', () => {
  for (const m of ['noReach', 'baseSeeded', 'noSpinCheck', 'no180'] as (keyof DemoMutants)[])
    expect(serialise(build(HAMBURGER, HAMBURGER_DEMOS, { [m]: true })), m).toBe(committedText);
}, 300_000);

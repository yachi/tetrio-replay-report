/**
 * The Cave TSS to TST constructed demos (`analysis/cavetsstst-demos.json`, from `pipeline/sim/emit-technique-demos.ts
 * --technique cavetsstst`; the planner is the shared `technique-demos.ts`, this page's half
 * `technique-demos-cavetsstst.ts`).
 *
 * NO DEMO IS BUILT AND NO CHAIN IS PLANNED, and this file pins why, re-deriving every reason:
 *
 *  - every board's cell count is re-counted from the transcription, and each reason's figure follows from it;
 *  - the TSS's residue has exact covers by tetrominoes (all seven kinds, every rotation, enumerated here with a
 *    control that finds T-free covers where there are some) and every one uses a T, which the planner's terrain
 *    never does; that is what the reason says.
 *
 * The planner's mutants are all EQUIVALENT here (with no chain nothing reaches them) and asserted byte-identical.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/cavetsstst-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, drawnCells, type DemoMutants } from '../sim/technique-demos.ts';
import { CAVETSSTST } from '../sim/technique-profile-cavetsstst.ts';
import { CAVETSSTST_DEMOS } from '../sim/technique-demos-cavetsstst.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/cavetsstst-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(CAVETSSTST_DEMOS.transcriptionPath, 'utf8'));
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));
const reason: Record<string, string> = Object.fromEntries(committed.unbuilt.map((u: any) => [u.node, u.reason]));

/** Every board's cell count, as the reasons print it. */
const CELLS: Record<string, number> = { 'terrain': 10, 'tss': 14, 'tss.spin': 18, 'tss.after': 8, 'tst': 39 };
const NOCOVER = '每一個鋪法都要用一粒 T';

const fresh = build(CAVETSSTST, CAVETSSTST_DEMOS);
const count = (id: string) => drawnCells(byId.get(id).rows, TR.empty_letters).size;

/** the seven tetrominoes in every rotation, as cell offsets; T last */
function shapes(): { kind: string; cells: [number, number][] }[] {
  const base: Record<string, [number, number][]> = {
    I: [[0, 0], [0, 1], [0, 2], [0, 3]], O: [[0, 0], [0, 1], [1, 0], [1, 1]], S: [[0, 1], [0, 2], [1, 0], [1, 1]],
    Z: [[0, 0], [0, 1], [1, 1], [1, 2]], J: [[0, 0], [1, 0], [1, 1], [1, 2]], L: [[0, 2], [1, 0], [1, 1], [1, 2]],
    T: [[0, 1], [1, 0], [1, 1], [1, 2]],
  };
  const out: { kind: string; cells: [number, number][] }[] = [];
  for (const [kind, c0] of Object.entries(base)) {
    const seen = new Set<string>();
    let c = c0;
    for (let k = 0; k < 4; k++) {
      c = c.map(([r, q]) => [q, -r] as [number, number]);
      const mr = Math.min(...c.map(x => x[0])), mc = Math.min(...c.map(x => x[1]));
      const n = c.map(([r, q]) => [r - mr, q - mc] as [number, number]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
      const key = JSON.stringify(n);
      if (!seen.has(key)) { seen.add(key); out.push({ kind, cells: n }); }
    }
  }
  return out;
}

/** every exact cover of `cells` (row*10+col) by tetrominoes, as the list of kinds used */
function covers(cells: Set<number>): string[][] {
  const S = shapes(), out: string[][] = [];
  const go = (left: Set<number>, used: string[]) => {
    if (!left.size) { out.push([...used].sort()); return; }
    const first = Math.min(...left), fr = Math.floor(first / 10), fc = first % 10;
    for (const s of S) for (const [ar, ac] of s.cells) {
      const placed = s.cells.map(([r, c]) => (fr + r - ar) * 10 + (fc + c - ac));
      if (s.cells.some(([r, c]) => fc + c - ac < 0 || fc + c - ac > 9)) continue;
      if (!placed.every(p => left.has(p))) continue;
      const next = new Set(left); placed.forEach(p => next.delete(p));
      go(next, [...used, s.kind]);
    }
  };
  go(cells, []);
  return out;
}

test('byte rebuild: the committed demos are what the planner produces now', () => {
  expect(serialise(fresh)).toBe(committedText);
});

test('quarantined and constructed; no chain, no demo; every board unbuilt exactly once', () => {
  expect(committed.report_eligible).toBe(false);
  expect(committed.constructed).toBe(true);
  expect(committed.demos).toEqual([]);
  expect(CAVETSSTST_DEMOS.chains).toEqual([]);
  expect(committed.unbuilt.map((u: any) => u.node).sort()).toEqual(TR.nodes.map((n: any) => n.id).sort());
  expect(Object.keys(CELLS).sort()).toEqual(TR.nodes.map((n: any) => n.id).sort());
});

test('every board\'s cell count, re-derived; odd and not-a-multiple-of-four boards say so', () => {
  for (const [id, n] of Object.entries(CELLS)) {
    expect(count(id), id).toBe(n);
    if (id !== 'tss.spin') expect(reason[id], id).toContain(`${n} 格`);
    if (n % 2) expect(reason[id], id).toContain('係單數');
    else if (n % 4 && id !== 'tss.spin') expect(reason[id], id).toContain('唔係 4 嘅倍數');
  }
  expect(reason['tss.spin']).toContain('tss 砌唔到');
  expect(byId.get('tss.spin').spin_of).toBe('tss');
});

test('MEASURED: every tetromino cover of the TSS residue uses a T', () => {
  const cells = new Set<number>(drawnCells(byId.get('tss.after').rows, TR.empty_letters).keys());
  const all = covers(cells);
  expect(all.length).toBeGreaterThan(0);
  expect(all.every(k => k.includes('T'))).toBe(true);
  // control: the cover search finds T-free covers where there are some (a 2x4 block: two O's, I's, ...)
  expect(covers(new Set([0, 1, 2, 3, 10, 11, 12, 13])).some(k => !k.includes('T'))).toBe(true);
  expect(reason['tss.after']).toContain(NOCOVER);
});

/** MEASURED EQUIVALENT: with no chain, nothing reaches the move search, the spin check or the arbiter. */
test('equivalent: the planner mutants change nothing (no chain reaches what they turn off)', () => {
  for (const m of ['noReach', 'baseSeeded', 'noSpinCheck', 'no180'] as (keyof DemoMutants)[])
    expect(serialise(build(CAVETSSTST, CAVETSSTST_DEMOS, { [m]: true })), m).toBe(committedText);
}, 300_000);

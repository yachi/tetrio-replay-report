/**
 * The Second PC corpus artefact (`analysis/secondpc-facts.json`, from `pipeline/sim/emit-secondpc-facts.ts`; the
 * rules are `secondpc-facts.ts`, the setups the gated `pipeline/openers/secondpc-setups.json`).
 *
 *   1. byte identity: the committed artefact is what `build()` produces now.
 *   2. THE ANCHOR: every player-round's PC points equal the replay's own Perfect Clear counter, and the DPC
 *      artefact's per-player PC points (the loop here is a copy of that one; the two must not drift).
 *   3. EVERY DRAWN SOLUTION MATCHES ITSELF: a synthetic digest per solution (a clear that empties the board,
 *      then the solution's pieces, setup first) is filed as `solution` under its setup, drawn and mirrored.
 *   4. CASES is a NAMED list (case, outcome, pieces before), never a count.
 *   5. MUTANTS: on this corpus no case matches, so all three are EQUIVALENT here, asserted to stay
 *      byte-identical, and killed on the synthetic digests instead, each with its symptom.
 *
 * Run: bun test pipeline/openers/secondpc.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, classify, serialise, loadSetups, mirrorRows, type SecondPcMutants } from '../sim/secondpc-facts.ts';
import { digestCorpus, type TechDigest } from '../sim/technique-facts.ts';
import { assertCorpusIsEverySessionOnDisk } from '../corpus-membership.ts';

const ROOT = `${import.meta.dir}/../../sessions`;
const ARTEFACT = `${import.meta.dir}/../../analysis/secondpc-facts.json`;
const DPC = `${import.meta.dir}/../../analysis/dpc-facts.json`;
const SESSIONS = assertCorpusIsEverySessionOnDisk(ROOT,
  ['2026-07-22', '2026-07-24', '2026-07-28', '2026-08-01', '2026-08-09', '2026-08-14',
   '2026-08-19', '2026-08-25', '2026-09-03', '2026-09-10', '2026-09-11', '2026-09-17',
   '2026-09-18', '2026-09-19', '2026-10-03', '2026-10-09', '2026-10-12', '2026-10-20', '2026-10-22',
   '2026-10-29']);
const H = 40, W = 10;

let DIGESTS: TechDigest[] | null = null;
const digests = () => (DIGESTS ??= digestCorpus(SESSIONS));
const data = loadSetups();
const committed = () => readFileSync(ARTEFACT, 'utf8');
const caseKey = (c: any) => `${c.session} m${c.match}r${c.round} ${c.player} @${c.pc_lock}`;

/** [case, outcome, pieces before the PC's first piece]: both are an eight-line PC into a four-line one */
const CASES: [string, string, number][] = [
  ['2026-09-18 m15r5 yachi @29', 'unmatched', 20],
  ['2026-09-19 m16r3 yachi @29', 'unmatched', 20],
];

test('byte identity: the committed artefact is what build() produces now', () => {
  expect(serialise(build({}, digests()))).toBe(committed());
}, 600_000);

test('anchor: PC points equal the replay\'s allclear counter, and the DPC artefact\'s', () => {
  const art = JSON.parse(committed());
  expect(art.pc_anchor.disagree).toEqual([]);
  expect(art.pc_anchor.rounds_agree).toBe(art.pc_anchor.rounds);
  expect(art.pc_anchor.pcs_replay).toBeGreaterThan(0);
  const dpc = JSON.parse(readFileSync(DPC, 'utf8'));
  for (const [u, p] of Object.entries<any>(art.by_player)) {
    expect(p.pc_points).toBe(dpc.by_player[u].pc_points);
    expect(p.rounds_rowmap_stops).toBe(dpc.by_player[u].rounds_rowmap_stops);
  }
});

/** a digest: an I clearing the bottom row empties the board, then the layout's pieces (setup cells first),
 *  the last one clearing the four rows. `mix` chunks each letter's cells across the setup boundary. */
function synthetic(layout: string[], setupOcc: boolean[][], mix = false): TechDigest {
  const groups: { piece: string; cells: [number, number][] }[] = [];
  for (const inSetup of mix ? [null] : [true, false]) {
    for (const letter of 'IJLOSTZ') {
      const cells: [number, number][] = [];
      for (let r = 0; r < 4; r++) for (let c = 0; c < W; c++)
        if (layout[r]![c] === letter && (inSetup === null || setupOcc[r]![c] === inSetup)) cells.push([r, c]);
      for (let i = 0; i < cells.length; i += 4) groups.push({ piece: letter, cells: cells.slice(i, i + 4) });
    }
  }
  if (mix) groups.sort((a, b) => Number(!a.cells.some(([r, c]) => setupOcc[r]![c])) - Number(!b.cells.some(([r, c]) => setupOcc[r]![c])));
  const empty = { piece: 'I', spin: 'none', cleared: 1, cells: [0, 1, 2, 3].map(c => ({ row: H - 1, col: c })),
                  clearedRows: [H - 1], garbage: 0, mapOk: true };
  const locks = groups.map((g, i) => ({
    piece: g.piece, spin: 'none', cleared: i === groups.length - 1 ? 4 : 0,
    cells: g.cells.map(([r, c]) => ({ row: H - 4 + r, col: c })),
    clearedRows: i === groups.length - 1 ? [H - 4, H - 3, H - 2, H - 1] : [], garbage: 0, mapOk: true,
  }));
  // a second empty board ahead of the layout so the layout is the SECOND PC of the pair
  return { session: 'synthetic', file: 'x', round: 0, match: 1, user: 'p', v: 0, locks: [empty, ...locks],
           tspins: [] } as any;
}
const solved = (setup: any, solId: string, mirrored: boolean) => {
  const sol = data.boards.get(solId)!;
  const setupRows = data.boards.get(setup.id)!;
  const layout = sol.map((row, r) => [...row].map((ch, c) => ch === 'G' ? setupRows[r]![c]! : ch).join(''));
  const occ = setupRows.map(r => [...r].map(ch => ch !== '.'));
  return mirrored ? { layout: mirrorRows(layout), occ: occ.map(r => [...r].reverse()) } : { layout, occ };
};

test('every drawn solution is filed under its setup as a solution, drawn and mirrored, setup first', () => {
  let n = 0;
  for (const s of data.setups) for (const id of s.solutions) for (const mirrored of [false, true]) {
    const { layout, occ } = solved(s, id, mirrored);
    const cs = classify([synthetic(layout, occ)], data).cases;
    expect(cs.length).toBe(1);
    expect(cs[0]!.outcome).toBe('solution');
    expect(cs[0]!.setups).toContain(s.id);
    expect(cs[0]!.solutions).toContain(id);
    expect(cs[0]!.setup_first).toBe(true);
    n++;
  }
  expect(n).toBe(2 * data.setups.reduce((a, s) => a + s.solutions.length, 0));
});

test('cases are a named list', () => {
  const art = JSON.parse(committed());
  expect(art.cases.map((c: any) => [caseKey(c), c.outcome, c.pieces_before])).toEqual(CASES);
  for (const c of art.cases) expect(c.layout.join('').includes('.')).toBe(false);
});

test('mutants: equivalent on this corpus, killed on synthetic digests', () => {
  const ds = digests();
  const key = (cs: any[]) => cs.map(c => `${caseKey(c)} ${c.outcome} ${c.setups.join(',')} ${c.solutions.join(',')}`);
  const real = key(classify(ds, data).cases);
  for (const m of [{ noMirror: true }, { noLetterSwap: true }, { noWholePieces: true }] as SecondPcMutants[])
    expect(key(classify(ds, data, m).cases)).toEqual(real);
  // noMirror / noLetterSwap: a mirrored solution holding J, L, S or Z stops matching
  const s = data.setups.find(x => x.solutions.length && /[JLSZ]/.test(x.pieces))!;
  const { layout, occ } = solved(s, s.solutions[0]!, true);
  const d = synthetic(layout, occ);
  expect(classify([d], data).cases[0]!.setups).toContain(s.id);
  for (const m of [{ noMirror: true }, { noLetterSwap: true }] as SecondPcMutants[])
    expect(classify([d], data, m).cases[0]!.setups).not.toContain(s.id);
  // noWholePieces: a layout whose pieces straddle the setup boundary (same letters, other pieces) matches
  // nothing under the real rule and the drawn solution without it
  let killed = 0;
  for (const x of data.setups) for (const id of x.solutions) {
    const v = solved(x, id, false);
    const mixed = synthetic(v.layout, v.occ, true);
    const realOut = classify([mixed], data).cases[0]!;
    if (realOut.setups.includes(x.id)) continue;
    expect(classify([mixed], data, { noWholePieces: true }).cases[0]!.solutions).toContain(id);
    killed++;
  }
  expect(killed).toBeGreaterThan(0);
}, 600_000);

test('accounting: every PC point is the last of its round, or opens a pair that is a case or counted out', () => {
  const art = JSON.parse(committed());
  for (const p of Object.values<any>(art.by_player))
    expect(p.no_next_pc + p.garbage + p.other_lines + p.cases.all).toBe(p.pc_points);
  const tot = (k: string) => Object.values<any>(art.by_player).reduce((a, p) => a + p[k], 0);
  expect(tot('garbage')).toBeGreaterThan(0);
  expect(tot('other_lines')).toBeGreaterThan(0);
});

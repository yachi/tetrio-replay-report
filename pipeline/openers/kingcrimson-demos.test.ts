/**
 * The King Crimson constructed demos (`analysis/kingcrimson-demos.json`, from `pipeline/sim/emit-technique-demos.ts
 * --technique kingcrimson`; the planner is the shared `technique-demos.ts`, this page's half
 * `technique-demos-kingcrimson.ts`).
 *
 * NO DEMO IS BUILT AND NO CHAIN IS PLANNED, and this file pins why, re-deriving every reason:
 *
 *  - every board's cell count is re-counted from the transcription, and each reason's figure follows from it;
 *  - the four boards carrying the shape are each run through the SHARED planner on an in-memory transcription
 *    (`build`'s `tr` option) with their stack read as terrain, and the planner's own words — no cover by non-T
 *    pieces, each kind at most twice — are what the reasons quote; the three that draw the stack's rest in light
 *    grey `q` are also run as drawn, where the planner reads `q` as a page piece, and its words are quoted too;
 *  - the window (`technique-facts.ts` windowMatch, both hands) is fired at every T placement of every board: it
 *    fires once on each of the four shape boards (in the hand the transcription records) and on no other board,
 *    which is what the reasons calling a board 「唔係呢個手法嘅形」 rest on;
 *  - each residue's isolated cell is re-found (a cell with no drawn neighbour, which no tetromino can cover
 *    without covering an empty cell).
 *
 * The planner's mutants are all EQUIVALENT here (with no chain nothing reaches them) and asserted byte-identical.
 * The day a chain is added, `demos` may stop being empty and the demo page's prose must be re-read.
 *
 * NOT CORPUS DATA. Nobody played these games.
 *
 * Run: bun test pipeline/openers/kingcrimson-demos.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, drawnCells, type DemoMutants } from '../sim/technique-demos.ts';
import { prepare, windowMatch } from '../sim/technique-facts.ts';
import { KINGCRIMSON } from '../sim/technique-profile-kingcrimson.ts';
import { KINGCRIMSON_DEMOS } from '../sim/technique-demos-kingcrimson.ts';

const ART_PATH = `${import.meta.dir}/../../analysis/kingcrimson-demos.json`;
const committedText = readFileSync(ART_PATH, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(KINGCRIMSON_DEMOS.transcriptionPath, 'utf8'));
const byId = new Map<string, any>(TR.nodes.map((n: any) => [n.id, n]));
const reason: Record<string, string> = Object.fromEntries(committed.unbuilt.map((u: any) => [u.node, u.reason]));

/** Every board's cell count, as the reasons print it. */
const CELLS: Record<string, number> = {
  'basic': 60, 'basic.spin': 64, 'basic.after': 34,
  'tki1.form': 24, 'tki1.spin': 28, 'tki1.after': 8, 'tki1.z': 12, 'tki1.j': 16, 'tki1.kc': 60,
  'tki2.form': 24, 'tki2.spin': 28, 'tki2.after': 8, 'tki2.build': 24, 'tki2.tsd': 28, 'tki2.tsd.after': 8,
  'tki2.s': 12, 'tki2.l': 16, 'tki2.kc': 60,
  'empty.j': 4, 'empty.clear': 11, 'empty.cell': 1, 'empty.kc': 60,
};
/** the boards the window fires on, at one T placement each, in this hand */
const SHAPE: Record<string, 'as drawn' | 'mirrored'> = {
  'basic': 'as drawn', 'basic.spin': 'as drawn', 'tki1.kc': 'mirrored', 'tki2.kc': 'as drawn', 'empty.kc': 'mirrored',
};
/** the shape boards, with the page's own pieces (lower-case letters) on each; the rest is the 52-cell stack */
const STACKED: Record<string, { page: RegExp; q: number }> = {
  'basic': { page: /[ls]/g, q: 0 }, 'tki1.kc': { page: /[jz]/g, q: 44 }, 'tki2.kc': { page: /[ls]/g, q: 44 },
  'empty.kc': { page: /[jz]/g, q: 51 },
};
const RESIDUES = ['tki1.after', 'tki2.after', 'tki2.tsd.after'];
const NOT_KC = '個窗口喺呢幅一個 T 位都對唔到';
const NOCOVER = '地形冇一個由非 T 方塊（每款最多兩粒）砌成嘅鋪法';

const fresh = build(KINGCRIMSON, KINGCRIMSON_DEMOS);
const count = (id: string) => drawnCells(byId.get(id).rows, TR.empty_letters).size;

/** Run the shared planner on one synthetic chain added to an in-memory copy of the transcription; every original
 *  board is passed as unbuilt so only the chain's own reasons come back. */
function plannerReason(node: any, terrain: any): string {
  const tr = structuredClone(TR);
  tr.nodes.push(node, terrain);
  const DP = { ...KINGCRIMSON_DEMOS, chains: [{ node: node.id, terrain: terrain.id }],
               unbuilt: Object.fromEntries(TR.nodes.map((n: any) => [n.id, '-'])) };
  const out = build(KINGCRIMSON, DP, {}, { tr });
  expect(out.demos).toEqual([]);
  return out.unbuilt.find((u: any) => u.node === node.id)!.reason;
}

/** every T placement in the board's empty cells (a spin board read with its T taken out) at which the window fires */
function windowFits(id: string): string[] {
  const rows = byId.get(id).rows.map((r: string) => [...r].map(ch => ch === '-' || ch === 'U' ? '.' : 'x').join(''));
  const pad = 40 - rows.length;
  const board = [...Array(pad).fill('.'.repeat(10)), ...rows];
  const TS = [[[0, 0], [0, 1], [0, 2], [1, 1]], [[1, 0], [1, 1], [1, 2], [0, 1]],
              [[0, 0], [1, 0], [2, 0], [1, 1]], [[0, 1], [1, 1], [2, 1], [1, 0]]];
  const out: string[] = [];
  for (const P of prepare(TR, TR.variants[0])) for (let r = 0; r < 40; r++) for (let c = 0; c < 10; c++) for (const s of TS) {
    const cells = s.map(([dr, dc]) => ({ row: r + dr!, col: c + dc! }));
    if (cells.some(q => q.row >= 40 || q.col >= 10 || board[q.row]![q.col] !== '.')) continue;
    if (windowMatch(board, cells, P)) out.push(P.mirrored ? 'mirrored' : 'as drawn');
  }
  return out;
}

test('byte rebuild: the committed demos are what the planner produces now', () => {
  expect(serialise(fresh)).toBe(committedText);
});

test('quarantined and constructed; no chain, no demo; every board unbuilt exactly once', () => {
  expect(committed.report_eligible).toBe(false);
  expect(committed.constructed).toBe(true);
  expect(committed.demos).toEqual([]);
  expect(KINGCRIMSON_DEMOS.chains).toEqual([]);
  expect(committed.unbuilt.length).toBe(TR.nodes.length);
  expect(committed.unbuilt.map((u: any) => u.node).sort()).toEqual(TR.nodes.map((n: any) => n.id).sort());
  expect(Object.keys(CELLS).sort()).toEqual(TR.nodes.map((n: any) => n.id).sort());
});

test('every board\'s cell count, re-derived; odd and not-a-multiple-of-four boards say so', () => {
  for (const [id, n] of Object.entries(CELLS)) {
    expect(count(id), id).toBe(n);
    if (id !== 'basic.spin') expect(reason[id], id).toContain(`${n} 格`);
    if (n % 2) expect(reason[id], id).toContain('係單數');
  }
  expect(reason['basic.after']).toContain('唔係 4 嘅倍數');
});

test('the window fires once on each shape board, in its recorded hand, and on no other board', () => {
  for (const n of TR.nodes) {
    const fits = windowFits(n.id);
    if (SHAPE[n.id]) expect(fits, n.id).toEqual([SHAPE[n.id]!]);
    else expect(fits, n.id).toEqual([]);
    if (reason[n.id]!.includes(NOT_KC)) expect(fits, n.id).toEqual([]);
  }
  // every board neither a shape board, a residue nor an odd or 4n-less board is unbuilt for not being the shape
  for (const id of ['tki1.form', 'tki1.spin', 'tki1.z', 'tki1.j', 'tki2.form', 'tki2.spin', 'tki2.build', 'tki2.tsd',
                    'tki2.s', 'tki2.l', 'empty.j']) expect(reason[id], id).toContain(NOT_KC);
  // the hands agree with the transcription's agreement drawings
  const agree = new Map<string, boolean>(TR.variants[0].agreement.map((a: any) => [a.board, a.mirrored]));
  for (const id of ['tki1.kc', 'tki2.kc', 'empty.kc']) expect(agree.get(id), id).toBe(SHAPE[id] === 'mirrored');
  for (const id of ['tki1.kc', 'empty.kc']) expect(reason[id], id).toContain('左右反轉');
});

test('each residue holds a cell with no drawn neighbour, so no tetromino covers it without a line clear', () => {
  for (const id of RESIDUES) {
    const cells = drawnCells(byId.get(id).rows, TR.empty_letters);
    const lone = [...cells.keys()].filter(c => ![c - 10, c + 10, c % 10 ? c - 1 : -1, c % 10 < 9 ? c + 1 : -1]
      .some(d => d >= 0 && cells.has(d)));
    expect(lone.length, id).toBeGreaterThan(0);
    expect(lone.every(c => c < 10), id).toBe(true);   // on the bottom row, as the reason says
    expect(reason[id], id).toContain('最底一行有一格四邊都冇其他格');
  }
  // the builds on a residue name the board they stand on
  for (const [id, on] of [['tki1.z', 'tki1.after'], ['tki1.j', 'tki1.z'], ['tki2.build', 'tki2.after'],
                          ['tki2.s', 'tki2.tsd.after'], ['tki2.l', 'tki2.s']]) {
    expect(byId.get(id!).on, id).toBe(on);
    expect(reason[id!], id).toContain(`企喺 ${on} 上面`);
  }
});

test('MEASURED: the shared planner, on each shape board with its stack as terrain, finds no cover', () => {
  for (const [id, { page, q }] of Object.entries(STACKED)) {
    const rows: string[] = byId.get(id).rows.map((r: string) => r.replace(/q/g, 'c'));
    const terr = rows.map(r => r.replace(page, '-'));
    expect(drawnCells(terr, TR.empty_letters).size, id).toBe(52);            // 13 pieces
    expect(rows.join('').replace(/[c-]/g, '').length, id).toBe(8);          // the page's two pieces
    const got = plannerReason({ id: `${id}.syn`, kind: 'build', rows }, { id: `${id}.syn.t`, kind: 'base', rows: terr });
    expect(got, id).toBe(NOCOVER);
    expect(reason[id], id).toContain(NOCOVER);
    expect(byId.get(id).rows.join('').split('q').length - 1, id).toBe(q);   // the light-grey cells, as drawn
  }
});

test('MEASURED: as drawn, the planner reads the light grey q as a page piece', () => {
  for (const [id, { q }] of Object.entries(STACKED)) {
    if (!q) continue;
    const node = byId.get(id), on = byId.get(node.on);
    const got = plannerReason({ ...node, id: `${id}.syn` }, { ...on, id: `${id}.syn.t` });
    expect(got, id).toBe(`頁面嘅 Q 畫咗 ${q} 格，唔係一粒`);
    expect(reason[id], id).toContain(got);
  }
});

const T = 300_000;

/** MEASURED EQUIVALENT: with no chain, nothing reaches the move search, the spin check or the arbiter. */
test('equivalent: the planner mutants change nothing (no chain reaches what they turn off)', () => {
  for (const m of ['noReach', 'baseSeeded', 'noSpinCheck', 'no180'] as (keyof DemoMutants)[])
    expect(serialise(build(KINGCRIMSON, KINGCRIMSON_DEMOS, { [m]: true })), m).toBe(committedText);
}, T);

/**
 * 千鳥格子 (Cut Copy) boards of OUR OWN design (`analysis/cutcopy-own.json`, from `pipeline/sim/emit-technique-own.ts
 * --technique cutcopy`; the search is `technique-own.ts`, Cut Copy's half `technique-own-cutcopy.ts`, and every board
 * is planned by the shared demo planner `technique-demos.ts`).
 *
 * What this file re-derives, each from scratch:
 *
 *   * the candidate list at every offset (the enumeration is fast): its size, and each published board is the
 *     candidate the artefact says it is;
 *   * each published board's demo, planned again, equal to the committed one byte for byte;
 *   * each demo decoded from an empty board on its own (`decodeTimeline`): the board before the stood T is the
 *     published board, the window matches there (`windowMatch`, as drawn), and both T's are full T-spins
 *     clearing two lines;
 *   * no published board is a source's drawing: none has the occupancy of any transcribed board, as drawn or
 *     mirrored;
 *   * against a wall (offsets 0 and 4) there is no candidate at all: a count of this search, not a claim that no
 *     Cut Copy can stand against a wall (a real game deals T's into the stack, and this terrain holds none).
 *
 * What it does NOT re-derive: the outcome counts of the candidates tried before each stop. Those need the whole
 * search (about half a second of engine per candidate) and are re-derived by re-running the emitter, which writes
 * the same bytes on every machine (the search is capped by a count of steps, never by a clock); set OWN_FULL=1 to
 * have this file do it.
 *
 * NOT CORPUS DATA AND NOT A SOURCE'S DRAWING. Nobody played these games and nobody drew these boards.
 *
 * Run: bun test pipeline/openers/cutcopy-own.test.ts
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, candidates, planOwn, rowsOf, serialise, windowGrid } from '../sim/technique-own.ts';
import { reachProblems } from '../sim/technique-demos.ts';
import { decodeTimeline, queueStates, placeCells, WIDTH, ROWS } from '../sim/emit-replay.ts';
import { prepare, windowMatch } from '../sim/technique-facts.ts';
import { CUTCOPY } from '../sim/technique-profile-cutcopy.ts';
import { CUTCOPY_DEMOS } from '../sim/technique-demos-cutcopy.ts';
import { CUTCOPY_OWN as OP } from '../sim/technique-own-cutcopy.ts';
import { md5Files } from '../sim/route-facts.ts';

const committedText = readFileSync(OP.artefactPath, 'utf8');
const committed = JSON.parse(committedText);
const TR = JSON.parse(readFileSync(CUTCOPY_DEMOS.transcriptionPath, 'utf8'));
const V = TR.variants.find((v: any) => v.id === OP.variant);

test('the artefact is quarantined and names its search', () => {
  expect(committed.report_eligible).toBe(false);
  expect(committed.constructed).toBe(true);
  expect(committed.own).toBe(true);
  expect(committed.search.offsets).toEqual(OP.offsets);
  expect(committed.search.rows_above).toBe(OP.rowsAbove);
  expect(committed.search.max_extra).toBe(OP.maxExtra);
  expect(committed.search.max_steps).toBe(OP.maxSteps);
  expect(committed.search.max_tried).toBe(OP.maxTried);
  expect(committed.search.window).toEqual(windowGrid(TR, V).g);
  expect(committed.boards.map((b: any) => b.id)).toEqual(committed.demos.map((d: any) => d.node));
  expect(committed.boards.length).toBeGreaterThan(0);
});

test('the artefact is current: every input it hashes is the file on disk', () => {
  expect(committed.inputs.transcription_md5).toBe(md5Files([CUTCOPY_DEMOS.transcriptionPath]));
  expect(committed.inputs.search_md5).toBe(md5Files(OP.hashFiles));
  expect(committed.inputs.planner_md5).toBe(md5Files(CUTCOPY_DEMOS.hashFiles.planner));
  expect(committed.inputs.classifier_md5).toBe(md5Files(CUTCOPY.hashFiles.classifier));
});

const CANDS = new Map<number, number[][]>(OP.offsets.map(o => [o, candidates(TR, V, o, OP.rowsAbove, OP.maxExtra)]));

test('every offset\'s candidate count, every stop, and every published board, re-derived', () => {
  for (const o of committed.search.per_offset) {
    const c = CANDS.get(o.offset)!;
    expect(o.candidates).toBe(c.length);
    expect(o.built.length).toBeLessThanOrEqual(OP.pick);
    // the search stops on its pick-th build, at its cap, or when it runs out
    expect(o.tried).toBe(o.built.length === OP.pick
      ? Math.max(...o.built.map((id: string) => Number(id.split('.').pop()))) : Math.min(c.length, OP.maxTried));
    expect(o.not_tried).toBe(c.length - o.tried);
    expect(Object.values(o.outcomes).reduce((a: number, b: any) => a + b, 0)).toBe(o.tried);
    expect(o.outcomes.built ?? 0).toBe(o.built.length);
  }
  for (const b of committed.boards) {
    expect(b.id).toBe(`own.${b.offset}.${b.candidate}`);
    const cells = CANDS.get(b.offset)![b.candidate - 1]!;
    expect(b.rows).toEqual(rowsOf(cells));
    expect(b.cells).toBe(cells.length);
  }
});

test('against a wall there is no candidate; away from it there are', () => {
  expect(CANDS.get(0)!.length).toBe(0);
  expect(CANDS.get(4)!.length).toBe(0);
  for (const o of [1, 2, 3]) expect(CANDS.get(o)!.length).toBeGreaterThan(0);
});

test('each published board: planned again, byte for byte the committed demo', () => {
  for (const b of committed.boards) {
    const r = planOwn(CUTCOPY, CUTCOPY_DEMOS, TR, b.id, b.rows, OP.maxSteps);
    expect(r.demo).not.toBeNull();
    expect(JSON.stringify(r.demo)).toBe(JSON.stringify(committed.demos.find((d: any) => d.node === b.id)));
  }
});

test('each demo, decoded on its own: the board, the window, two full TSDs', () => {
  const prep = prepare(TR, V)[0]!;
  for (const d of committed.demos) {
    const b = committed.boards.find((x: any) => x.id === d.node);
    const boards: (string | null)[][][] = [];
    decodeTimeline(d.seq, d.locks, (bd, i) => { boards[i] = bd.map(r => [...r]); });
    const q = queueStates(d.seq, d.locks);
    // the board before the stood T is the published board, every cell
    const before = boards[d.stood_lock - 1]!;
    const top = b.rows.length;
    for (let y = 0; y < ROWS; y++) for (let x = 0; x < WIDTH; x++) {
      const drawn = y < top ? b.rows[top - 1 - y][x] === 'c' : false;
      expect(before[y]![x] !== null).toBe(drawn);
    }
    // the window, as drawn, at the stood T
    const cells = [...placeCells('T', d.locks[d.stood_lock][1])];
    const topFirst = [...before].reverse().map(r => r.map(c => c ?? '.').join(''));
    expect(windowMatch(topFirst, cells.map(c => ({ row: ROWS - 1 - Math.floor(c / WIDTH), col: c % WIDTH })), prep))
      .not.toBeNull();
    for (const i of [d.stood_lock, d.followup_lock]) {
      expect(q[i]!.piece).toBe('T');
      expect(d.locks[i][3]).toBe(2);
      expect(d.locks[i][2]).toBe(2);
    }
    const tr2 = { ...TR, nodes: [...TR.nodes, { id: b.id, rows: b.rows }, { id: `${b.id}.terrain`, rows: b.rows }] };
    expect(reachProblems(tr2, V, d)).toEqual([]);
  }
});

test('no published board is a source\'s drawing', () => {
  const occ = (rows: string[]) => {
    const t = rows.map(r => [...r].map(ch => (ch === '-' || (TR.empty_letters ?? '').includes(ch) ? '.' : '#')).join(''));
    while (t.length && !t[0]!.includes('#')) t.shift();
    return t.join('/');
  };
  const drawn = new Set(TR.nodes.flatMap((n: any) => [occ(n.rows), occ(n.rows.map((r: string) => [...r].reverse().join('')))]));
  for (const b of committed.boards) expect(drawn.has(occ(b.rows))).toBe(false);
});

test.skipIf(!process.env.OWN_FULL)('OWN_FULL: the whole search rebuilds the committed artefact byte for byte', () => {
  expect(serialise(build(CUTCOPY, CUTCOPY_DEMOS, OP))).toBe(committedText);
}, 3_600_000);

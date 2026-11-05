/**
 * The TS half of `video-examples.json`'s gate (the Python half is `check_video_examples.py`):
 *
 *   1. every technique example's `whole_board` is what `technique-wholeshape.ts` (the corpus rule) finds at its T,
 *      with every unread `?` cell read empty AND read filled — the rule is not run on the video by any emitter,
 *      so the drawing the page names is re-derived here;
 *   2. every example's `key_cells` (and `one_piece` groups) are the cells the page's own qualify module names —
 *      `technique-qualify.ts`'s `keyOffsets` with `QUALIFY_OPTIONS`, or 欄干's and 社畜トレイン's own
 *      `shapeOffsets` — placed at the T's lowest cell, mirrored with the hand. The Python gate recomputes the
 *      reasons from those cells, so this is what ties its approximation to the corpus rule's cells;
 *   3. a mutant: an example's hand flipped, or its T read one column over, breaks (1).
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { wholeShapes, wholeShapeMatch } from '../sim/technique-wholeshape.ts';
import { QUALIFY_OPTIONS, keyOffsets } from '../sim/technique-qualify.ts';
import { shapeOffsets as parapetOffsets } from '../sim/parapet-qualify.ts';
import { shapeOffsets as shachikuOffsets } from '../sim/shachikutrain-qualify.ts';

const DIR = import.meta.dir;
const doc = JSON.parse(readFileSync(`${DIR}/video-examples.json`, 'utf8'));
const tr = (k: string) => JSON.parse(readFileSync(`${DIR}/${k}-technique.json`, 'utf8'));
const boardOf = (id: string) => doc.boards.find((b: any) => b.id === id);
type RC = [number, number];
const key = (cs: RC[]) => cs.map(([r, c]) => `${r},${c}`).sort().join(' ');

function before(b: any, unreadFilled: boolean, t: RC[]): string[] {
  const T = new Set(t.map(([r, c]) => `${r},${c}`));
  return b.rows.map((row: string, r: number) => [...row].map((ch, c) =>
    T.has(`${r},${c}`) ? '.' : ch === '?' ? (unreadFilled ? 'G' : '.') : ch).join(''));
}

function whole(ex: any, t: RC[]) {
  const S = wholeShapes(tr(ex.page)).get(ex.variant)!;
  return [false, true].map(u => wholeShapeMatch(before(boardOf(ex.board), u, t), t.map(([row, col]) => ({ row, col })), S));
}

function expectedKeys(ex: any): { key: RC[]; groups: { name: string; cells: RC[] }[] } {
  const b = boardOf(ex.board);
  const t: RC[] = b.t_cells;
  const low = t.reduce((a, x) => x[0] > a[0] ? x : a);
  const sg = ex.mirrored ? -1 : 1;
  const at = (x: { dr: number; dc: number }): RC => [low[0] + x.dr, low[1] + sg * x.dc];
  const T = tr(ex.page);
  if (ex.page === 'parapet') {
    const sh = parapetOffsets(T);
    return { key: sh.map(at), groups: [{ name: 'l', cells: sh.filter(x => x.l).map(at) }] };
  }
  if (ex.page === 'shachikutrain') return { key: shachikuOffsets(T).map(at), groups: [] };
  const o = keyOffsets(T, QUALIFY_OPTIONS[ex.page] ?? {}).get(ex.variant)!;
  return { key: o.key.map(at), groups: o.one.map(g => ({ name: g.name, cells: g.cells.map(at) })) };
}

test('every technique example stands as the drawing it names, whatever the unread cells are', () => {
  expect(doc.technique_examples.length).toBeGreaterThan(0);
  for (const ex of doc.technique_examples) {
    const got = whole(ex, boardOf(ex.board).t_cells);
    for (const m of got) {
      expect(m, `${ex.board} ${ex.page}`).not.toBeNull();
      expect(m!.board, `${ex.board} ${ex.page}`).toBe(ex.whole_board);
    }
  }
});

test('every example\'s key cells are the cells its page\'s qualify module names', () => {
  for (const ex of doc.technique_examples) {
    const want = expectedKeys(ex);
    expect(key(ex.key_cells), `${ex.board} ${ex.page}`).toBe(key(want.key));
    const got = (ex.one_piece ?? []).map((g: any) => `${g.name}:${key(g.cells)}`).sort();
    expect(got, `${ex.board} ${ex.page}`).toEqual(want.groups.map(g => `${g.name}:${key(g.cells)}`).sort());
  }
});

test('mutants: a T read one column over, and a key cell list read in the other hand, are caught', () => {
  let moved = 0, flipped = 0;
  for (const ex of doc.technique_examples) {
    const t: RC[] = boardOf(ex.board).t_cells.map(([r, c]: RC) => [r, c + 1] as RC);
    if (t.every(([, c]) => c < 10) && whole(ex, t).some(m => m === null || m.board !== ex.whole_board)) moved++;
    const other = expectedKeys({ ...ex, mirrored: !ex.mirrored });
    if (key(other.key) !== key(ex.key_cells)) flipped++;
  }
  expect(moved).toBeGreaterThan(0);
  expect(flipped).toBe(doc.technique_examples.length);
});

/**
 * The WHOLE drawn shape, not the window: a qualify rule every technique page adds to its own (yachi, 2026-10-25:
 * 「人哋係睇特定形狀，你就求其話 TSpin 就算」, and 「係」 to this rule's demo). The window (`technique-facts.ts`) is
 * the box every drawing of a shape agrees on, so it is small and local: STMB Cave's reads three rows, and a one-deep
 * dimple passes it. A hit qualifies only if ONE of the source's own drawings of the variant stands on the board around
 * the T, cell for cell by occupancy (colour ignored), in either hand.
 *
 * A drawing's region (`drawingRegion`), in its own frame:
 *   - the T's four cells;
 *   - every ENCLOSED empty component (empty cells with a filled cell above them in the same column, joined by edges)
 *     that touches the T or has a cell between the row above the T and three rows under the T's lowest row — the
 *     cave, the slot under an overhang, the hole a donation covers;
 *   - the bounding box of those, grown by one cell on every side, clipped to the drawing (a drawing's bottom row is
 *     not read as standing on the floor, so nothing under it is required).
 * Every cell of the region is required as drawn: filled or empty. A drawn cell is empty when it is `-`, `.`, `U`
 * (the T it places) or one of the transcription's `empty_letters`; every other letter is filled. On the board, a
 * cell under the floor is filled, one above the top is empty, and one past a side wall is no match.
 *
 * The drawings are the variant's own board, and every `agreement` / `drawings` entry naming a node of the same
 * transcription; drawings from other sites that the transcription holds only by reference are not read here.
 */
import type { Cell } from './technique-facts.ts';
import { loadTranscription } from './technique-facts.ts';

export interface RegionCell { r: number; c: number; filled: boolean }
export interface WholeShape { board: string; width: number; t: [number, number][]; region: RegionCell[] }

const EMPTY = new Set(['-', '.', 'U']);

export function drawingRegion(rows: string[], t: [number, number][], emptyLetters = ''): RegionCell[] {
  const H = rows.length, W = rows[0]!.length;
  const isT = (r: number, c: number) => t.some(([a, b]) => a === r && b === c);
  const filled = (r: number, c: number) => {
    if (isT(r, c)) return false;
    const ch = rows[r]![c]!;
    return !(EMPTY.has(ch) || emptyLetters.includes(ch));
  };
  const enclosed = (r: number, c: number) => !filled(r, c) && !isT(r, c)
    && Array.from({ length: r }, (_, y) => y).some(y => filled(y, c));
  const ttop = Math.min(...t.map(([r]) => r)), tbot = Math.max(...t.map(([r]) => r));
  const keep = new Map<string, [number, number]>(t.map(([r, c]) => [`${r},${c}`, [r, c]]));
  const seen = new Set<string>();
  for (let r = Math.max(0, ttop - 1); r < H; r++) for (let c = 0; c < W; c++) {
    if (seen.has(`${r},${c}`) || !enclosed(r, c)) continue;
    const comp: [number, number][] = [], st: [number, number][] = [[r, c]], inComp = new Set<string>();
    while (st.length) {
      const [y, x] = st.pop()!;
      const k = `${y},${x}`;
      if (inComp.has(k) || y < 0 || y >= H || x < 0 || x >= W || !(enclosed(y, x) || isT(y, x))) continue;
      inComp.add(k); comp.push([y, x]);
      st.push([y + 1, x], [y - 1, x], [y, x + 1], [y, x - 1]);
    }
    for (const k of inComp) seen.add(k);
    if (comp.some(([y, x]) => isT(y, x)) || comp.some(([y]) => y >= ttop - 1 && y <= tbot + 3))
      for (const [y, x] of comp) keep.set(`${y},${x}`, [y, x]);
  }
  const ks = [...keep.values()];
  const r0 = Math.max(0, Math.min(...ks.map(([y]) => y)) - 1), r1 = Math.min(H - 1, Math.max(...ks.map(([y]) => y)) + 1);
  const c0 = Math.max(0, Math.min(...ks.map(([, x]) => x)) - 1), c1 = Math.min(W - 1, Math.max(...ks.map(([, x]) => x)) + 1);
  const out: RegionCell[] = [];
  for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) out.push({ r, c, filled: filled(r, c) });
  return out;
}

/** Every drawing of each variant, with its region. */
export function wholeShapes(tr: any): Map<string, WholeShape[]> {
  const nodes = new Map<string, any>(tr.nodes.map((n: any) => [n.id, n]));
  const empt: string = tr.empty_letters ?? '';
  const out = new Map<string, WholeShape[]>();
  for (const v of tr.variants) {
    const ds: { board: string; t_cells: [number, number][] }[] =
      [{ board: v.board, t_cells: v.t_cells }, ...(v.agreement ?? []), ...(v.drawings ?? [])];
    const list: WholeShape[] = [], dup = new Set<string>();
    for (const d of ds) {
      const n = nodes.get(d.board);
      if (!n) continue;
      const k = `${d.board}|${JSON.stringify(d.t_cells)}`;
      if (dup.has(k)) continue;
      dup.add(k);
      list.push({ board: d.board, width: n.rows[0].length, t: d.t_cells, region: drawingRegion(n.rows, d.t_cells, empt) });
    }
    if (!list.length) throw new Error(`whole shape: variant ${v.id} has no drawing in its transcription`);
    out.set(v.id, list);
  }
  return out;
}

const norm = (cs: [number, number][]) => {
  const s = [...cs].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  return s.map(([r, c]) => `${r - s[0]![0]},${c - s[0]![1]}`).join(';');
};

/** The first drawing (id, and the hand it stands in) found on `board` (the board before the T; row 0 the top, `.`
 *  empty) with the T at `cells`, or null. */
export function wholeShapeMatch(board: string[], cells: Cell[], shapes: WholeShape[]):
    { board: string; mirrored: boolean } | null {
  const H = board.length, W = board[0]!.length;
  const ct = cells.map(x => [x.row, x.col] as [number, number]);
  const ctKey = norm(ct);
  const ct0 = [...ct].sort((a, b) => a[0] - b[0] || a[1] - b[1])[0]!;
  for (const s of shapes) for (const mir of [false, true]) {
    const flip = (c: number) => mir ? s.width - 1 - c : c;
    const dt = s.t.map(([r, c]) => [r, flip(c)] as [number, number]);
    if (norm(dt) !== ctKey) continue;
    const dt0 = [...dt].sort((a, b) => a[0] - b[0] || a[1] - b[1])[0]!;
    const dr = ct0[0] - dt0[0], dc = ct0[1] - dt0[1];
    let ok = true;
    for (const x of s.region) {
      const R = x.r + dr, C = flip(x.c) + dc;
      if (C < 0 || C >= W) { ok = false; break; }
      const f = R >= H ? true : R < 0 ? false : board[R]![C]! !== '.';
      if (f !== x.filled) { ok = false; break; }
    }
    if (ok) return { board: s.board, mirrored: mir };
  }
  return null;
}

export const WHOLE_SHAPE_RULE = 'not_whole_shape: none of the source page\'s own drawings of the variant (its board and '
  + 'its agreement drawings) stands around the T cell for cell by occupancy, in either hand — each drawing read as the '
  + 'T, every enclosed hole touching it or within three rows under it, and a one-cell margin (technique-wholeshape.ts)';

/** Wrap a profile's `qualify.check` with the whole-shape rule. */
export function withWholeShape(transcriptionPath: string,
                               check: (h: any, d: any) => { qualifies: boolean; not_qualified: string[] },
                               mut: { off?: boolean } = {}) {
  const shapes = wholeShapes(loadTranscription(transcriptionPath));
  return (h: any, d: any) => {
    const res = check(h, d);
    if (mut.off || res.not_qualified.includes('ownership_unverified')) return res;
    const S = shapes.get(h.variant);
    if (!S) throw new Error(`whole shape: no drawings for variant ${h.variant}`);
    const t = d.tspins.find((x: any) => x.i === h.lock);
    if (!t) throw new Error(`whole shape: no T-spin at lock ${h.lock}`);
    if (wholeShapeMatch(t.board, d.locks[h.lock].cells, S)) return res;
    const nq = [...res.not_qualified, 'not_whole_shape'];
    return { qualifies: false, not_qualified: nq };
  };
}

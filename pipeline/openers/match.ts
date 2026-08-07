/**
 * Name the opener a board is playing, by comparing it with the community catalogue.
 *
 * No dependencies: `opener-fields.json` holds the catalogue already decoded (see fetch-catalogue.ts).
 *
 * THE RULE, stated so it can fail. After N locks with no line clear and no garbage, a board holds
 * exactly 4N cells. Any catalogue page with 4N cells is a candidate, and the board played that
 * opener iff the two fields are equal cell-for-cell — as drawn, or mirrored (columns reversed with
 * L<->J and S<->Z swapped), because the catalogue draws one handedness only.
 *
 * OCCUPANCY, NOT COLOUR. Many catalogue pages are drawn all-grey ('X' = "any piece"), which is why
 * opener_db's own front-end greys fumens before comparing. Colour keys are computed and exported
 * anyway, but a colour comparison against a grey page can only ever fail, so occupancy is the key
 * that decides and colour is reported as extra evidence when both sides have it.
 *
 * Exact equality answers "did they play this move for move". Hamming distance over the
 * bottom-aligned grid answers the question that survives contact with real play: one or two cells
 * apart is a variant, eight cells apart is a different opener.
 */
import { readFileSync } from 'node:fs';

export interface Page { name: string; tag: string | null; fumen: string; page: number; rows: string[] }
export interface Catalogue { provenance: Record<string, unknown>; pages: Page[] }

export const ROWS = 8;          // tall enough for a full first bag; boards taller than this cannot
                                // be first-bag states anyway, and a fixed height makes distance total

export function loadCatalogue(dir = import.meta.dir): Catalogue {
  return JSON.parse(readFileSync(`${dir}/opener-fields.json`, 'utf8')) as Catalogue;
}

export const cellsOf = (rows: string[]) => rows.join('').split('').filter(c => c !== '.').length;

/** bottom-aligned, exactly ROWS rows; '#' filled, '.' empty */
export function occGrid(rows: string[]): string[] {
  const occ = rows.map(r => [...r].map(c => (c === '.' ? '.' : '#')).join(''));
  const pad = Array.from({ length: Math.max(0, ROWS - occ.length) }, () => '..........');
  return [...pad, ...occ].slice(-ROWS);
}

const SWAP: Record<string, string> = { L: 'J', J: 'L', S: 'Z', Z: 'S' };
export const mirrorRows = (rows: string[]) =>
  rows.map(r => [...r].reverse().map(c => SWAP[c] ?? c).join(''));

export const keyOf = (grid: string[]) => grid.join('/');

export function distance(a: string[], b: string[]): number {
  let d = 0;
  for (let i = 0; i < ROWS; i++) for (let c = 0; c < 10; c++) if (a[i]![c] !== b[i]![c]) d++;
  return d;
}

export interface Prepared { name: string; cells: number; grid: string[]; mirror: string[]; page: Page }

export function prepare(pages: Page[]): Prepared[] {
  return pages.map(p => ({
    name: p.name, cells: cellsOf(p.rows), page: p,
    grid: occGrid(p.rows), mirror: occGrid(mirrorRows(p.rows)),
  }));
}

/** exact lookup: every catalogue name whose field equals this grid, and which way round */
export function exactMatches(grid: string[], prepared: Prepared[]) {
  const k = keyOf(grid);
  const asDrawn = new Set<string>(), asMirror = new Set<string>();
  for (const p of prepared) {
    if (keyOf(p.grid) === k) asDrawn.add(p.name);
    else if (keyOf(p.mirror) === k) asMirror.add(p.name);
  }
  return { asDrawn: [...asDrawn], asMirror: [...asMirror] };
}

/** nearest page by Hamming distance, restricted to pages with the same cell count */
export function nearest(grid: string[], prepared: Prepared[], filter?: (p: Prepared) => boolean) {
  const cells = grid.join('').split('').filter(c => c === '#').length;
  let best = { d: Number.POSITIVE_INFINITY, name: '', mirrored: false };
  for (const p of prepared) {
    if (p.cells !== cells) continue;
    if (filter && !filter(p)) continue;
    const d0 = distance(grid, p.grid);
    if (d0 < best.d) best = { d: d0, name: p.name, mirrored: false };
    const d1 = distance(grid, p.mirror);
    if (d1 < best.d) best = { d: d1, name: p.name, mirrored: true };
  }
  return best;
}

/** A simulator board (40 rows of piece letters or null) as trimmed row strings. */
export function rowsFromBoard(board: (string | null)[][]): string[] | null {
  const rows = board.map(r => r.map(c => (c === null ? '.' : c)).join(''));
  const first = rows.findIndex(r => r !== '..........');
  return first < 0 ? null : rows.slice(first);
}

/** The catalogue's C-Spin entries. Named openers only — the wiki's C-Spin is a FAMILY, and the
 *  catalogue holds a handful of its members, which is what bounds any negative result here. */
export const isCSpin = (name: string) => /c-?spin/i.test(name);

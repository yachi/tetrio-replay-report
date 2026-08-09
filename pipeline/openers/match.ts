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
 *  catalogue holds a handful of its members, which is what bounds any negative result here.
 *
 *  READ THE NAMES THIS SELECTS BEFORE QUOTING A NEGATIVE FROM IT. All three are substring hits and
 *  not one of them is the C-Spin as harddrop draws it: `Fake C-Spin {JP: 偽TKI}` is by its own name
 *  a *fake*, `Secspin` is a different opener whose name merely ends in the letters, and the third is
 *  a compound page listing `SDPC-Spin` among eight names. So "0 rounds near a catalogued C-Spin"
 *  computed over THIS set alone would be a statement about a set that arguably contains no C-Spin —
 *  which is why `NAME_SETS` below carries wider readings and the emitter reports all of them. */
export const isCSpin = (name: string) => /c-?spin/i.test(name);

/** TKI, the family the C-Spin is commonly identified with (`TKI-3 {Alt: TKI, JP: 開幕TSD}` and
 *  three relatives, 18 pages). Kept separate from `isCSpin` rather than merged into it because
 *  whether C-Spin *is* TKI is a taxonomy question this repo has no authority to settle. Reporting
 *  both sets side by side settles the only thing that matters instead: whether the answer moves. */
export const isTKI = (name: string) => /TKI/i.test(name);

/** DT Cannon proper — the canonical 開幕DT砲 and the variants that name themselves after it.
 *  The `(^|[^A-Za-z])` guard is load-bearing: a bare /DT ?Cannon/ also matches `SDT Cannon`,
 *  `SDDT Cannon`, `SZDT Cannon` and `NEWDT Cannon` by substring, which would quietly widen the
 *  "canonical" set to five openers it does not contain. Those live in `isDTFamily` instead. */
export const isDTCannon = (name: string) => /(^|[^A-Za-z])DT ?Cannon/i.test(name);

/** The widest defensible DT reading: any opener whose name carries "DT" at all (48 openers,
 *  115 pages) — DDT, SDDT, SZDT, 91DT, Perfect DT and the rest. This is deliberately over-broad.
 *  A negative that survives the over-broad set is not a negative about set membership. */
export const isDTFamily = (name: string) => /DT/i.test(name);

/** The named page sets the opener metrics are reported over, narrowest first within each subject.
 *
 *  Every set is emitted WITH ITS MEMBER NAMES (see emit-opener-facts.ts) so a reader can audit what
 *  a number ranges over instead of trusting a regex they cannot see. The pairing is the point: a
 *  distance reported over one set alone cannot be told apart from an artefact of choosing that set.
 */
export const NAME_SETS: { key: string; label: string; test: (name: string) => boolean }[] = [
  { key: 'cspin', label: 'C-Spin (by name)', test: isCSpin },
  { key: 'cspin_or_tki', label: 'C-Spin or TKI', test: n => isCSpin(n) || isTKI(n) },
  { key: 'dt_cannon', label: 'DT Cannon', test: isDTCannon },
  { key: 'dt_family', label: 'DT family (widest)', test: isDTFamily },
];

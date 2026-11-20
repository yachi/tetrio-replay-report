/**
 * ハンバーガー's cover, as yachi reads it (「用S/Z 砌hamburger 先算，除非有其他完整piece 砌到」): the cells of the row the
 * TSS clears at the well and between it and the nub (the first is the cell over the hole) count if one S or Z covers
 * them, and also if other complete pieces do (one or several), as long as every cover cell belongs to a piece whose
 * four cells are all still on the board. Garbage and fragments never count. The qualify rules `fragment` /
 * `garbage_in_shape` over those cells are `technique-qualify.ts`'s, with the cover among the key cells
 * (`QUALIFY_OPTIONS.hamburger`); no single piece is required. This wrapper adds one field to every hit, so the page
 * can show the split:
 *
 *   `cover`: 'one_sz' (one S or Z, whole), 'complete_pieces' (whole pieces, not one S or Z), 'not_complete' (a cover
 *   cell is garbage or a fragment), or null (the row map before the T could not be verified, so no owner is known).
 *
 * Piece ownership is `shachikutrain-qualify.ts`'s `owners`, the board the qualifier already checked cell for cell.
 */
import type { Hit, TechDigest } from './technique-facts.ts';
import { owners } from './shachikutrain-qualify.ts';

const H = 40, W = 10;
/** the cover cells relative to the T's lowest cell (its nub), as drawn: the well two columns left, and the cell between */
export const COVER_OFFSETS = [{ dr: 0, dc: -2 }, { dr: 0, dc: -1 }];
export type CoverKind = 'one_sz' | 'complete_pieces' | 'not_complete' | null;

export function hamburgerCover(h: Hit, d: TechDigest): CoverKind {
  const own = owners(d, h.lock);
  if (own.bad !== null && own.bad < h.lock) return null;
  const g = h.lock > 0 ? own.boards[h.lock - 1]! : Array.from({ length: H }, () => new Array(W).fill(-2));
  const low = d.locks[h.lock]!.cells.reduce((a, b) => b.row > a.row ? b : a);
  const sgn = h.mirrored ? -1 : 1;
  const count = new Map<number, number>();
  for (const row of g) for (const o of row) if (o >= 0) count.set(o, (count.get(o) ?? 0) + 1);
  const os = COVER_OFFSETS.map(x => {
    const r = low.row + x.dr, c = low.col + sgn * x.dc;
    return r >= 0 && r < H && c >= 0 && c < W ? g[r]![c]! : -3;
  });
  if (os.some(o => o < 0 || count.get(o)! < 4)) return 'not_complete';
  const one = new Set(os).size === 1 && ['S', 'Z'].includes(d.locks[os[0]!]!.piece);
  return one ? 'one_sz' : 'complete_pieces';
}

/** a qualify check with each hit's `cover` added */
export function withHamburgerCover(check: (h: any, d: any) => { qualifies: boolean; not_qualified: string[] }) {
  return (h: any, d: any) => ({ ...check(h, d), cover: hamburgerCover(h, d) });
}

/** a qualify check that also fails every hit inside the opener window (`in_opener`): a mid-game page counts no opener hit */
export function withMidGameOnly(check: (h: any, d: any) => { qualifies: boolean; not_qualified: string[] }) {
  return (h: any, d: any) => {
    const r = check(h, d);
    if (!h.in_opener) return r;
    return { ...r, qualifies: false, not_qualified: [...r.not_qualified, 'in_opener'] };
  };
}

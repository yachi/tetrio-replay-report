/**
 * Which hits of a mid-game technique were BUILT as one, not merely shaped like one: a profile's `qualify` hook
 * (`technique-profile.ts`), read by `technique-facts.ts`'s `assemble`, for every technique page whose own rules are
 * the shared ones below. 社畜トレイン (`shachikutrain-qualify.ts`) and 欄干 (`parapet-qualify.ts`) keep their own
 * modules, written first; this one carries the same rules to the other seven pages, at yachi's request on 2026-10-23
 * (「睇埋其他中盤」), and to 途中DT砲, added after them. A hit failing any rule stays in `hits` (the shape did stand)
 * with `qualifies: false` and every rule it fails named.
 *
 *   1. `fragment` / `garbage_in_shape`: the variant's KEY cells — the pieces a player places to make the shape — are
 *      each a cell of a COMPLETE piece, all four of its cells still on the board before the T, and never garbage.
 *      By default the key cells are the transcription's `roof_cells` and `window_extra` cells: the window's filled
 *      cells above the rows the spin clears, which every page draws as the pieces it builds (the overhang, and on
 *      BT砲's page the J, Z and L beside the slot). The cleared rows are entailed by any clear and the rows under
 *      them are the stack the page draws grey, so neither is required to be fresh. A profile may name the key cells
 *      itself (`keyCells`, in the variant's board frame), with its reading beside them.
 *   2. `<name>_not_one_piece`: where the page's instruction names one piece (階段のドネイト's 「Zを縦置き」), the cells
 *      it draws as that piece are one piece (`onePiece`).
 *   3. `dpc`: no Perfect Clear within `DPC_LOCKS` locks before or after the T (社畜トレイン's rule 3).
 *
 * Piece ownership is `shachikutrain-qualify.ts`'s `owners`, checked cell for cell against the board the matcher
 * read; a hit whose row map could not be verified up to the T is `ownership_unverified`.
 */
import type { Hit, TechDigest } from './technique-facts.ts';
import { loadTranscription } from './technique-facts.ts';
import { DPC_LOCKS, owners } from './shachikutrain-qualify.ts';

const H = 40, W = 10;

export interface TechniqueQualifyOptions {
  /** per variant id: the key cells in the variant's board frame (default: roof_cells + window_extra cells) */
  keyCells?: Record<string, [number, number][]>;
  /** per variant id: groups of cells (board frame) the page draws as ONE piece, named for the rule */
  onePiece?: Record<string, { name: string; cells: [number, number][] }[]>;
}
/** Each page's key cells, in its variants' board frames (the profiles pass these; the test reads them). */
export const QUALIFY_OPTIONS: Record<string, TechniqueQualifyOptions> = {
  // the overhang over the well: every build draws it as its roof piece (an L, a Z or an I); the cell under it roof.i draws as stack
  stsd: { keyCells: { stsd: [[1, 2], [1, 3]] } },
  // the S hooked over the gap, beside the T's far arm: the piece both builds place there (the transcription has no roof)
  stmbcave: { keyCells: { stmbcave: [[2, 5], [2, 6]] } },
  // roof_cells: the O and the Z or L every build places over the cross
  imperialcross: {},
  // roof_cells: the S or Z every build places over the upper slot
  doubledagger: {},
  // roof_cells: the J or I against the wall, the Z laid over the slot and the L's top, which every build places
  btcannon: {},
  // cutcopy: roof_cells + window_extra; uncut: the overhang over the T's right arm alone (the rest of that row harddrop draws as stack)
  cutcopy: { keyCells: { uncut: [[1, 4]] } },
  // the roof over the slot's end away from the wall, and the Z stood on end on the lowest step (one piece: 「Zを縦置き」)
  kaidan: { keyCells: { kaidan: [[1, 5], [1, 6], [2, 9], [3, 8], [3, 9], [4, 8]] },
      onePiece: { kaidan: [{ name: 'z', cells: [[2, 9], [3, 8], [3, 9], [4, 8]] }] } },
  // the overhang over the TST stem: the one window cell every build places as a piece (the rest of the roof is
  // drawn as stack on some of them)
  dtcannon: { keyCells: { dtcannon: [[1, 2]] } },
  // King Crimson: the overhang over the well (row 0, over the wall and the well), which every drawing roofs the
  // well with; the wall under it (roof_cells' third cell) is the stack the page draws grey, so it is not a key cell
  kingcrimson: { keyCells: { kingcrimson: [[0, 6], [0, 7]] } },
};

export interface TechniqueQualifyMutants { allowFragments?: boolean; allowGarbage?: boolean; allowSplit?: boolean;
                                           noDpc?: boolean }

/** The key cells of each variant, relative to the T's lowest cell, as drawn. */
export function keyOffsets(tr: any, opts: TechniqueQualifyOptions = {}): Map<string, { key: { dr: number; dc: number }[];
                                                                                          one: { name: string; cells: { dr: number; dc: number }[] }[] }> {
  const out = new Map<string, any>();
  for (const v of tr.variants) {
    const tc: [number, number][] = v.t_cells;
    const nr = Math.max(...tc.map(([r]) => r));
    const low = tc.filter(([r]) => r === nr);
    if (low.length !== 1) throw new Error(`technique qualify: variant ${v.id}'s T has no single lowest cell`);
    const nc = low[0]![1];
    const rows: string[] = tr.nodes.find((n: any) => n.id === v.board).rows;
    const cells: [number, number][] = opts.keyCells?.[v.id]
      ?? [...(v.roof_cells ?? []), ...(v.window_extra?.cells ?? [])];
    // an EXPLICIT empty list is a variant with no piece of its own to check (基本的なドネイト's hole under the nub,
    // where the T fills the cells another variant's piece would); a default that comes out empty is an error
    if (!cells.length && !opts.keyCells?.[v.id]) throw new Error(`technique qualify: variant ${v.id} has no key cells`);
    const [r0, r1] = v.window.rows, [c0, c1] = v.window.cols;
    const extra = new Set((v.window_extra?.cells ?? []).map(([r, c]: [number, number]) => `${r},${c}`));
    for (const [r, c] of cells) {
      // a key cell is a cell the window requires FILLED, so the matcher has already read it as stack
      if (!((r >= r0 && r <= r1 && c >= c0 && c <= c1) || extra.has(`${r},${c}`)))
        throw new Error(`technique qualify: variant ${v.id}'s key cell ${r},${c} is outside its window`);
      const ch = rows[r]![c]!;
      if (ch === '-' || ch === '.' || tc.some(([a, b]) => a === r && b === c))
        throw new Error(`technique qualify: variant ${v.id}'s key cell ${r},${c} is not drawn filled (${ch})`);
    }
    const rel = (cs: [number, number][]) => cs.map(([r, c]) => ({ dr: r - nr, dc: c - nc }));
    out.set(v.id, { key: rel(cells), one: (opts.onePiece?.[v.id] ?? []).map(g => {
      if (g.cells.length !== 4) throw new Error(`technique qualify: ${g.name} is not four cells`);
      return { name: g.name, cells: rel(g.cells) };
    }) });
  }
  return out;
}

export function techniqueQualifier(transcriptionPath: string, opts: TechniqueQualifyOptions = {},
                                   mut: TechniqueQualifyMutants = {}) {
  const tr = loadTranscription(transcriptionPath);
  const offs = keyOffsets(tr, opts);
  return (h: Hit, d: TechDigest): { qualifies: boolean; not_qualified: string[] } => {
    const reasons: string[] = [];
    const lk = d.locks[h.lock]!;
    const t = d.tspins.find(x => x.i === h.lock)!;
    const own = owners(d, h.lock + DPC_LOCKS);
    if (own.bad !== null && own.bad < h.lock) return { qualifies: false, not_qualified: ['ownership_unverified'] };
    const g = h.lock > 0 ? own.boards[h.lock - 1]! : Array.from({ length: H }, () => new Array(W).fill(-2));
    for (let r = 0; r < H; r++) for (let c = 0; c < W; c++) {
      const ch = t.board[r]![c]!, o = g[r]![c]!;
      const ok = ch === '.' ? o === -2 || (o === -1 && t.board[r]!.includes('G')) : ch === 'G' ? o === -1 : o >= 0 && d.locks[o]!.piece === ch;
      if (!ok) throw new Error(`technique qualify: ${h.session} m${h.match}r${h.round} ${h.player} lock ${h.lock}: `
        + `ownership disagrees with the board at ${r},${c} (${ch} vs ${o})`);
    }
    const V = offs.get(h.variant);
    if (!V) throw new Error(`technique qualify: no key cells for variant ${h.variant}`);
    const low = lk.cells.reduce((a, b) => b.row > a.row ? b : a);
    const sgn = h.mirrored ? -1 : 1;
    const at = (x: { dr: number; dc: number }) => {
      const r = low.row + x.dr, c = low.col + sgn * x.dc;
      return r >= 0 && r < H && c >= 0 && c < W ? g[r]![c]! : -3;
    };
    const count = new Map<number, number>();
    for (const row of g) for (const o of row) if (o >= 0) count.set(o, (count.get(o) ?? 0) + 1);
    let frag = false, garb = false, empty = false;
    for (const x of V.key) {
      const o = at(x);
      if (o === -1) garb = true;
      else if (o < 0) empty = true;
      else if (count.get(o)! < 4) frag = true;
    }
    if (empty) reasons.push('shape_cell_empty');
    if (frag && !mut.allowFragments) reasons.push('fragment');
    if (garb && !mut.allowGarbage) reasons.push('garbage_in_shape');
    if (!mut.allowSplit) for (const grp of V.one) if (new Set(grp.cells.map(at)).size !== 1) reasons.push(`${grp.name}_not_one_piece`);
    if (!mut.noDpc) {
      const isEmpty = (k: number) => own.boards[k]!.every(row => row.every(o => o === -2));
      for (let k = Math.max(0, h.lock - DPC_LOCKS); k <= h.lock + DPC_LOCKS && k < own.boards.length; k++)
        if (isEmpty(k)) { reasons.push('dpc'); break; }
    }
    return { qualifies: reasons.length === 0, not_qualified: reasons };
  };
}

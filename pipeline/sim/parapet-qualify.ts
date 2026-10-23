/**
 * Which 欄干 (Parapet) hits were BUILT as one, not merely shaped like one: the profile's `qualify` hook
 * (`technique-profile.ts`), read by `technique-facts.ts`'s `assemble`, the rules 社畜トレイン's hook
 * (`shachikutrain-qualify.ts`) applies, carried over at yachi's request on 2026-10-23. A hit failing any
 * of them stays in `hits` (the shape did stand) with `qualifies: false` and every rule it fails named.
 *
 *   1. `fragment` / `garbage_in_shape`: the cells both of the page's builds (basic.z, basic.o) draw as a
 *      piece of their own inside the window — the stood L and the two roof cells over the slot's right
 *      end, mirrored with the window — are each a cell of a COMPLETE piece, all four of its cells still on
 *      the board before the T, and never garbage.
 *   2. `l_not_one_piece`: the four cells the page draws as its L are not one piece. The page's whole
 *      instruction is 「%Lを1列ずらして立てて置き」, so a stem and foot made of two pieces is not it.
 *   3. `dpc`: no Perfect Clear within `DPC_LOCKS` locks before or after the T (社畜トレイン's rule 3).
 *
 * The Kaidan rule of 社畜トレイン does not apply: the Kaidan and Parapet windows clash in every pairing of
 * hands (kaidan.test.ts), so no lock is a hit of both. Piece ownership is `shachikutrain-qualify.ts`'s
 * `owners`, checked cell for cell against the board the matcher read.
 */
import type { Hit, TechDigest } from './technique-facts.ts';
import { loadTranscription } from './technique-facts.ts';
import { DPC_LOCKS, owners } from './shachikutrain-qualify.ts';

const H = 40, W = 10;

export interface ParapetQualifyMutants { allowFragments?: boolean; allowGarbage?: boolean; allowSplitL?: boolean;
                                         noDpc?: boolean }

/** Cells inside the window that every build drawing draws as its own piece (not 'c', not empty), relative
 *  to the T's lowest cell, with whether each is part of the page's L. */
export function shapeOffsets(tr: any): { dr: number; dc: number; l: boolean }[] {
  const v = tr.variants[0];
  const tc: [number, number][] = v.t_cells;
  const nr = Math.max(...tc.map(([r]) => r)), nc = tc.find(([r]) => r === nr)![1];
  const builds = tr.nodes.filter((n: any) => n.kind === 'build').map((n: any) => n.rows as string[]);
  if (builds.length < 2) throw new Error('parapet qualify: expected the page\'s builds');
  const [r0, r1] = v.window.rows, [c0, c1] = v.window.cols;
  const out: { dr: number; dc: number; l: boolean }[] = [];
  for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) {
    const chs = builds.map((b: string[]) => b[r]![c]!);
    if (chs.every((ch: string) => /[a-z]/.test(ch) && ch !== 'c')) out.push({ dr: r - nr, dc: c - nc, l: chs.every((ch: string) => ch === 'l') });
  }
  if (out.filter(x => x.l).length !== 4) throw new Error('parapet qualify: the builds do not agree on a four-cell L');
  return out;
}

export function parapetQualifier(transcriptionPath: string, mut: ParapetQualifyMutants = {}) {
  const tr = loadTranscription(transcriptionPath);
  const shape = shapeOffsets(tr);
  // every variant's lowest T cell is the window's centre column, so mirroring about it mirrors the window
  for (const v of tr.variants) {
    const tc: [number, number][] = v.t_cells;
    const nr = Math.max(...tc.map(([r]) => r));
    const low = tc.filter(([r]) => r === nr);
    if (low.length !== 1 || 2 * low[0]![1] !== v.window.cols[0] + v.window.cols[1])
      throw new Error(`parapet qualify: variant ${v.id}'s lowest T cell is not the window's centre`);
  }
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
      if (!ok) throw new Error(`parapet qualify: ${h.session} m${h.match}r${h.round} ${h.player} lock ${h.lock}: `
        + `ownership disagrees with the board at ${r},${c} (${ch} vs ${o})`);
    }
    const low = lk.cells.reduce((a, b) => b.row > a.row ? b : a);
    const sgn = h.mirrored ? -1 : 1;
    const count = new Map<number, number>();
    for (const row of g) for (const o of row) if (o >= 0) count.set(o, (count.get(o) ?? 0) + 1);
    let frag = false, garb = false, empty = false;
    const lOwners = new Set<number>();
    for (const x of shape) {
      const o = g[low.row + x.dr]![low.col + sgn * x.dc]!;
      if (x.l) lOwners.add(o);
      if (o === -1) garb = true;
      else if (o < 0) empty = true;
      else if (count.get(o)! < 4) frag = true;
    }
    if (empty) reasons.push('shape_cell_empty');
    if (frag && !mut.allowFragments) reasons.push('fragment');
    if (garb && !mut.allowGarbage) reasons.push('garbage_in_shape');
    if (!mut.allowSplitL && lOwners.size !== 1) reasons.push('l_not_one_piece');
    if (!mut.noDpc) {
      const isEmpty = (k: number) => own.boards[k]!.every(row => row.every(o => o === -2));
      for (let k = Math.max(0, h.lock - DPC_LOCKS); k <= h.lock + DPC_LOCKS && k < own.boards.length; k++)
        if (isEmpty(k)) { reasons.push('dpc'); break; }
    }
    return { qualifies: reasons.length === 0, not_qualified: reasons };
  };
}

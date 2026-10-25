/**
 * Which 基本的なドネイト (basic donation) hits count on THIS page: the profile's `qualify` hook (`technique-profile.ts`),
 * read by `technique-facts.ts`'s `assemble`. The six hole windows say a piece laid over a hole k columns from the T's
 * arm fills exactly the two rows the TSD clears; these rules say whether that is the page's donation and no other's.
 * A hit failing any of them stays in `hits` (the shape stood) with `qualifies: false` and every rule it fails named.
 *
 *   1. `fragment` / `garbage_in_shape`, `dpc`: the shared rules (`technique-qualify.ts`). The key cells are the two
 *      donated cells, the hole's column in the rows the TSD clears: each a cell of a complete piece, never garbage
 *      (the page: 「TSDで消える2列だけを埋める」 — a piece laid there, not what clears or garbage left); and no Perfect
 *      Clear within `DPC_LOCKS` locks either side of the T. The `nub` variant (harddrop's hole under the T's own
 *      nub) has no donated cells — the T fills them — so `garbage_in_shape` reads its whole window instead: any
 *      garbage there (in practice a garbage well under the nub) fails it; `fragment` has nothing to read.
 *   2. `other_page`: no other technique page's window fires at the same T (any of its variants, either hand). Many of
 *      them are donations — the page names its %Sドネイト as 階段のドネイト, its %LドネイトA as 欄干 and its
 *      %S%ZドネイトA as STMB Cave, and the Shachiku Train's first TSD is a donation one column past the arm (the
 *      transcriptions' `other_windows`, measured) — so a T another page claims is that page's, counted once.
 *   3. `nearer_well`: a smaller-k window fires at the same T. A T can fill two holes at once (the page's own Q16 and
 *      Q17 answers draw it); the T is counted once, at its nearest hole. The nub window never claims a T (rule 6: it
 *      is no donation), so a k hit is not blocked by it.
 *   4. `well_covered`: a filled cell anywhere above the window in the hole's column, so the clear does not leave the
 *      hole open from the top (harddrop's re-opening clause). No drawing on the page has one (measured by the facts
 *      test on every drawing).
 *   5. `shallow_well`, the `nub` variant only: fewer than 4 empty cells under the nub (`well_depth`), so the column
 *      the clear re-opens cannot take a Tetris. The window asks for 2, which any TSD over a dent satisfies; a
 *      donation keeps a Tetris well open (harddrop's Donation page draws a cavity of at least 4, the shipped
 *      donation predicate's D = 4). The k variants are left as the page draws them: its boards are cropped below the
 *      hole, so they fix no depth.
 *   6. `t_covers_hole`, the `nub` variant only, always: the hole is covered by the T itself. yachi's definition
 *      (2026-10-24): a donation covers the hole TEMPORARILY with other pieces, which the TSD clears so the hole is
 *      open again; the T is not the cover. So no nub hit counts on this page. The variant and harddrop's drawing
 *      stay, so the page can show the shape harddrop calls a donation and say why it is not counted here (the
 *      社畜トレイン precedent: the shape is drawn, the corpus counts 0).
 *
 * Every other technique's transcription is read here, so each is in the profile's hashed files.
 */
import type { Hit, TechDigest } from './technique-facts.ts';
import { loadTranscription, prepare, windowMatch } from './technique-facts.ts';
import { DPC_LOCKS } from './shachikutrain-qualify.ts';
import { techniqueQualifier } from './technique-qualify.ts';

/** The other technique pages whose windows `other_page` reads, by transcription file name. */
export const OTHER_PAGES = ['stsd', 'stmbcave', 'imperialcross', 'doubledagger', 'btcannon', 'cutcopy', 'shachikutrain',
                            'parapet', 'kaidan', 'dtcannon'];

export interface DonationQualifyMutants { allowFragments?: boolean; allowGarbage?: boolean; noDpc?: boolean;
                                          noOtherPage?: boolean; noNearer?: boolean; noCovered?: boolean;
                                          noShallow?: boolean; noTCovers?: boolean }

/** The nub's hole must take an I: at least this many empty cells under the nub. */
export const SHALLOW_BELOW = 4;

/** Per variant: the two donated cells (the window_extra's 2nd and 3rd), in the variant's board frame. */
export function donatedCells(tr: any): Record<string, [number, number][]> {
  const out: Record<string, [number, number][]> = {};
  for (const v of tr.variants) {
    // under the nub the T itself fills the hole's column in the rows the TSD clears: no piece is donated
    if (v.well.side === 'nub') { out[v.id] = []; continue; }
    const ex: [number, number][] = v.window_extra.cells;
    if (ex.length !== 4) throw new Error(`basicdonating qualify: ${v.id}'s window_extra is not four cells`);
    out[v.id] = [ex[1]!, ex[2]!];
  }
  return out;
}

export function donationQualifier(transcriptionPath: string, openersDir: string, mut: DonationQualifyMutants = {}) {
  const tr = loadTranscription(transcriptionPath);
  const shared = techniqueQualifier(transcriptionPath, { keyCells: donatedCells(tr) },
    { allowFragments: mut.allowFragments, allowGarbage: mut.allowGarbage, noDpc: mut.noDpc });
  const others = OTHER_PAGES.flatMap(k => {
    const o = loadTranscription(`${openersDir}/${k}-technique.json`);
    return o.variants.flatMap((v: any) => prepare(o, v));
  });
  const offset = new Map<string, number>(tr.variants.map((v: any) => [v.id, v.well.offset]));
  const nub = new Set<string>(tr.variants.filter((v: any) => v.well.side === 'nub').map((v: any) => v.id));
  const mine = tr.variants.flatMap((v: any) => prepare(tr, v));
  return (h: Hit, d: TechDigest): { qualifies: boolean; not_qualified: string[] } => {
    // the shared rules first; the three below read only the board at the T, so they are asked even when the
    // shared half stops at ownership_unverified
    const reasons = [...shared(h, d).not_qualified];
    // the nub has no donated piece for the shared garbage rule to read, so the rule reads its whole window: a hole
    // under the nub walled or floored by garbage is the garbage well, not a hole the player built
    if (nub.has(h.variant) && h.garbage_in_window && !mut.allowGarbage && !reasons.includes('ownership_unverified'))
      reasons.push('garbage_in_shape');
    const lk = d.locks[h.lock]!;
    const t = d.tspins.find(x => x.i === h.lock)!;
    if (!mut.noOtherPage && others.some((P: any) => !!windowMatch(t.board, lk.cells, P))) reasons.push('other_page');
    const k = offset.get(h.variant)!;
    // the nub window is no donation (rule 6), so it never claims a T from a farther hole
    if (!mut.noNearer && mine.some((P: any) => !nub.has(P.id) && offset.get(P.id)! < k && !!windowMatch(t.board, lk.cells, P)))
      reasons.push('nearer_well');
    if (!mut.noCovered) {
      // the window's own cells in the hole's column, re-read on the board at this hit's offset and hand
      const P = mine.find((x: any) => x.id === h.variant && x.mirrored === h.mirrored)!;
      const off = windowMatch(t.board, lk.cells, P);
      if (!off) throw new Error(`basicdonating qualify: ${h.variant} does not fire at its own hit`);
      const top = Math.min(...P.cells.filter((x: any) => x.c === P.well!.c).map((x: any) => x.r));
      const col = P.well!.c + off.dc;
      for (let R = 0; R < top + off.dr; R++) if (t.board[R]![col] !== '.') { reasons.push('well_covered'); break; }
    }
    if (!mut.noShallow && nub.has(h.variant)) {
      if (h.well_depth === undefined) throw new Error(`basicdonating qualify: nub hit with no well_depth`);
      if (h.well_depth < SHALLOW_BELOW) reasons.push('shallow_well');
    }
    if (!mut.noTCovers && nub.has(h.variant)) reasons.push('t_covers_hole');
    return { qualifies: reasons.length === 0, not_qualified: reasons };
  };
}

export { DPC_LOCKS };

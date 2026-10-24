/**
 * Which 基本的なドネイト (basic donation) hits count on THIS page: the profile's `qualify` hook (`technique-profile.ts`),
 * read by `technique-facts.ts`'s `assemble`. The six hole windows say a piece laid over a hole k columns from the T's
 * arm fills exactly the two rows the TSD clears; these rules say whether that is the page's donation and no other's.
 * A hit failing any of them stays in `hits` (the shape stood) with `qualifies: false` and every rule it fails named.
 *
 *   1. `fragment` / `garbage_in_shape`, `dpc`: the shared rules (`technique-qualify.ts`). The key cells are the two
 *      donated cells, the hole's column in the rows the TSD clears: each a cell of a complete piece, never garbage
 *      (the page: 「TSDで消える2列だけを埋める」 — a piece laid there, not what clears or garbage left); and no Perfect
 *      Clear within `DPC_LOCKS` locks either side of the T.
 *   2. `other_page`: no other technique page's window fires at the same T (any of its variants, either hand). Many of
 *      them are donations — the page names its %Sドネイト as 階段のドネイト, its %LドネイトA as 欄干 and its
 *      %S%ZドネイトA as STMB Cave, and the Shachiku Train's first TSD is a donation one column past the arm (the
 *      transcriptions' `other_windows`, measured) — so a T another page claims is that page's, counted once.
 *   3. `nearer_well`: a smaller-k window fires at the same T. A T can fill two holes at once (the page's own Q16 and
 *      Q17 answers draw it); the T is counted once, at its nearest hole.
 *   4. `well_covered`: a filled cell anywhere above the window in the hole's column, so the clear does not leave the
 *      hole open from the top (harddrop's re-opening clause). No drawing on the page has one (measured by the facts
 *      test on every drawing).
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
                                          noOtherPage?: boolean; noNearer?: boolean; noCovered?: boolean }

/** Per variant: the two donated cells (the window_extra's 2nd and 3rd), in the variant's board frame. */
export function donatedCells(tr: any): Record<string, [number, number][]> {
  const out: Record<string, [number, number][]> = {};
  for (const v of tr.variants) {
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
  const mine = tr.variants.flatMap((v: any) => prepare(tr, v));
  return (h: Hit, d: TechDigest): { qualifies: boolean; not_qualified: string[] } => {
    // the shared rules first; the three below read only the board at the T, so they are asked even when the
    // shared half stops at ownership_unverified
    const reasons = [...shared(h, d).not_qualified];
    const lk = d.locks[h.lock]!;
    const t = d.tspins.find(x => x.i === h.lock)!;
    if (!mut.noOtherPage && others.some((P: any) => !!windowMatch(t.board, lk.cells, P))) reasons.push('other_page');
    const k = offset.get(h.variant)!;
    if (!mut.noNearer && mine.some((P: any) => offset.get(P.id)! < k && !!windowMatch(t.board, lk.cells, P)))
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
    return { qualifies: reasons.length === 0, not_qualified: reasons };
  };
}

export { DPC_LOCKS };

/**
 * Which 基本的なドネイト (basic donation) hits count on THIS page: the profile's `qualify` hook (`technique-profile.ts`),
 * read by `technique-facts.ts`'s `assemble`. The donation rule (`basicdonating-rule.ts`) already decides the shape AND
 * the build — every covering cell the T or a complete piece, never garbage — so one rule is left (yachi, 2026-10-26:
 * 「有啲已經係其他pattern」):
 *
 *   `other_page`: no other technique page's window fires at the same T (any of its variants, either hand). Many of
 *   them are donations — the page names its %Sドネイト as 階段のドネイト, its %LドネイトA as 欄干 and its %S%ZドネイトA
 *   as STMB Cave, and the Shachiku Train's first TSD is a donation one column past the arm — so a T another page
 *   claims is that page's, counted once.
 *
 * A hit failing it stays in `hits` (the donation happened) with `qualifies: false`. Every other technique's
 * transcription is read here, so each is in the profile's hashed files.
 */
import type { Hit, TechDigest } from './technique-facts.ts';
import { loadTranscription, prepare, windowMatch } from './technique-facts.ts';

/** The other technique pages whose windows `other_page` reads, by transcription file name. */
export const OTHER_PAGES = ['stsd', 'stmbcave', 'imperialcross', 'doubledagger', 'btcannon', 'cutcopy', 'shachikutrain',
                            'parapet', 'kaidan', 'dtcannon'];

export interface DonationQualifyMutants { noOtherPage?: boolean }

export function donationQualifier(openersDir: string, mut: DonationQualifyMutants = {}) {
  const others = OTHER_PAGES.flatMap(k => {
    const o = loadTranscription(`${openersDir}/${k}-technique.json`);
    return o.variants.flatMap((v: any) => prepare(o, v));
  });
  return (h: Hit, d: TechDigest): { qualifies: boolean; not_qualified: string[] } => {
    const reasons: string[] = [];
    const lk = d.locks[h.lock]!;
    const t = d.tspins.find(x => x.i === h.lock)!;
    if (!mut.noOtherPage && others.some((P: any) => !!windowMatch(t.board, lk.cells, P))) reasons.push('other_page');
    return { qualifies: reasons.length === 0, not_qualified: reasons };
  };
}

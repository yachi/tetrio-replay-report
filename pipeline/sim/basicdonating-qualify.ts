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
 *   `opener_route` (yachi, 2026-10-27, on 10-22 m8r1 pinglamb lock 24, 迷走砲's 「STMB cave の形」 TSD): the round is a
 *   case of an opener route page that matched a bag-2 board, and the T locks within `ROUTE_LOCKS` locks after that
 *   bag-2 match (two bags). Those T-spins are the route's own continuation: the 迷走砲 page draws its third-bag TSDs
 *   with placeholder cells, so no window can claim them, and most of them are this TSD. The route artefacts
 *   (`ROUTE_ARTEFACTS`) are read here, so emit them BEFORE this page's facts; each is in the profile's hashed files.
 *
 * A hit failing either stays in `hits` (the donation happened) with `qualifies: false`. Every other technique's
 * transcription is read here, so each is in the profile's hashed files.
 */
import { readFileSync } from 'node:fs';
import type { Hit, TechDigest } from './technique-facts.ts';
import { loadTranscription, prepare, windowMatch } from './technique-facts.ts';

/** The other technique pages whose windows `other_page` reads, by transcription file name. */
export const OTHER_PAGES = ['stsd', 'stmbcave', 'imperialcross', 'doubledagger', 'btcannon', 'cutcopy', 'shachikutrain',
                            'parapet', 'kaidan', 'dtcannon'];

/** The opener route artefacts `opener_route` reads, under `analysis/`. */
export const ROUTE_ARTEFACTS = ['stray-cannon', 'honey-cup', 'mountainous2', 'stickspin', 'gamushiro', 'sdpcspin'];
/** Two bags after the bag-2 match. */
export const ROUTE_LOCKS = 14;

export interface DonationQualifyMutants { noOtherPage?: boolean; noOpenerRoute?: boolean }

const routeKey = (s: string, f: string, r: number, p: string) => `${s}|${f}|${r}|${p}`;

/** Every route case's bag-2 lock, keyed by (session, file, round_index0, player); several routes may share a round. */
export function routeBag2Locks(analysisDir: string): Map<string, number[]> {
  const out = new Map<string, number[]>();
  for (const k of ROUTE_ARTEFACTS) {
    const a = JSON.parse(readFileSync(`${analysisDir}/${k}-facts.json`, 'utf8'));
    if (!Array.isArray(a.cases)) throw new Error(`${k}-facts.json has no cases`);
    for (const c of a.cases) {
      if (!c.bag2) continue;
      if (typeof c.bag2.lock !== 'number') throw new Error(`${k}-facts.json: a bag-2 case has no lock`);
      const key = routeKey(c.session, c.file, c.round_index0, c.player);
      out.set(key, [...(out.get(key) ?? []), c.bag2.lock]);
    }
  }
  return out;
}

export function donationQualifier(openersDir: string, analysisDir: string, mut: DonationQualifyMutants = {}) {
  const bag2 = routeBag2Locks(analysisDir);
  const others = OTHER_PAGES.flatMap(k => {
    const o = loadTranscription(`${openersDir}/${k}-technique.json`);
    return o.variants.flatMap((v: any) => prepare(o, v));
  });
  return (h: Hit, d: TechDigest): { qualifies: boolean; not_qualified: string[] } => {
    const reasons: string[] = [];
    const lk = d.locks[h.lock]!;
    const t = d.tspins.find(x => x.i === h.lock)!;
    if (!mut.noOtherPage && others.some((P: any) => !!windowMatch(t.board, lk.cells, P))) reasons.push('other_page');
    const b2 = bag2.get(routeKey(h.session, h.file, h.round_index0, h.player)) ?? [];
    if (!mut.noOpenerRoute && b2.some(b => h.lock > b && h.lock <= b + ROUTE_LOCKS)) reasons.push('opener_route');
    return { qualifies: reasons.length === 0, not_qualified: reasons };
  };
}

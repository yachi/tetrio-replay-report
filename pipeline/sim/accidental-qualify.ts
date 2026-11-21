/**
 * Which 意外 T-spin (accidental TSD / TST) hits count: the profile's `qualify` hook (`technique-profile.ts`), read by
 * `technique-facts.ts`'s `assemble`. The detector (`technique-profile-accidental.ts`) only says the spin is a full TST,
 * or a full TSD whose T stands up; this page is defined by what it is NOT (yachi: 「Add 中盤，accidental tsd tst」), so
 * every rule here is an exclusion:
 *
 *   `in_opener`: the T locks inside the opener window (0-based lock <= WINDOW_PIECES). A TST there is an opener's own
 *   (C-Spin, Honey Cup, …), so the page is mid-game only.
 *
 *   `other_page`: another technique page's window (`OTHER_PAGES`, any variant whose spin clears the same rows, either
 *   hand) fires at the same T, so the T is that page's. 基本的なドネイト is left out on purpose: its rule fires on most
 *   T-spins that open a hole, and a stood TSD that donates is still not a drawn technique.
 *
 *   `opener_route` / `opener_spin`: 基本的なドネイト's two route rules, reused (`basicdonating-qualify.ts`): the T locks
 *   within `ROUTE_LOCKS` locks after an opener route case's bag-2 match, or is that case's bag-1 spin. Those T-spins are
 *   the route page's own continuation, drawn there, so they are not accidental.
 *
 * A hit failing any stays in `hits` with `qualifies: false`. The route artefacts are read here, so emit them BEFORE
 * this page's facts; they and every other transcription are in the profile's hashed files.
 */
import type { Hit, TechDigest } from './technique-facts.ts';
import { loadTranscription, prepare, windowMatch } from './technique-facts.ts';
import { WINDOW_PIECES } from './opener-window.ts';
import { ROUTE_LOCKS, routeBag1SpinLocks, routeBag2Locks } from './basicdonating-qualify.ts';

/** Every other technique page whose windows `other_page` reads, by transcription file name. */
export const OTHER_PAGES = ['stsd', 'stmbcave', 'imperialcross', 'doubledagger', 'btcannon', 'cutcopy', 'shachikutrain',
                            'parapet', 'kaidan', 'dtcannon', 'kingcrimson', 'cavetsstst', 'hamburger'];

export interface AccidentalQualifyMutants { noOpener?: boolean; noOtherPage?: boolean; noOpenerRoute?: boolean; noOpenerSpin?: boolean }

const routeKey = (s: string, f: string, r: number, p: string) => `${s}|${f}|${r}|${p}`;

export function accidentalQualifier(openersDir: string, analysisDir: string, mut: AccidentalQualifyMutants = {}) {
  const bag2 = routeBag2Locks(analysisDir);
  const bag1 = routeBag1SpinLocks(analysisDir);
  const others = OTHER_PAGES.flatMap(k => {
    const o = loadTranscription(`${openersDir}/${k}-technique.json`);
    return o.variants.flatMap((v: any) => prepare(o, v).map((P: any) => ({ P, lines: v.lines as number })));
  });
  return (h: Hit, d: TechDigest): { qualifies: boolean; not_qualified: string[] } => {
    const reasons: string[] = [];
    const lk = d.locks[h.lock]!;
    const t = d.tspins.find(x => x.i === h.lock)!;
    if (!mut.noOpener && h.lock <= WINDOW_PIECES) reasons.push('in_opener');
    if (!mut.noOtherPage && others.some(o => o.lines === lk.cleared && !!windowMatch(t.board, lk.cells, o.P))) reasons.push('other_page');
    const key = routeKey(h.session, h.file, h.round_index0, h.player);
    if (!mut.noOpenerRoute && (bag2.get(key) ?? []).some(b => h.lock > b && h.lock <= b + ROUTE_LOCKS)) reasons.push('opener_route');
    if (!mut.noOpenerSpin && (bag1.get(key) ?? []).includes(h.lock)) reasons.push('opener_spin');
    return { qualifies: reasons.length === 0, not_qualified: reasons };
  };
}

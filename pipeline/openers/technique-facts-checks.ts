/**
 * The checks every mid-game technique artefact's test makes, written ONCE (the sibling of
 * `route-facts-checks.ts`, whose named-list check it re-exports rather than copies).
 *
 *   * the scored T-spin set is the one `emit-opener-facts.ts` scores — the third copy of that loop
 *     (`technique-facts.ts`) held to the same count, per session and per player;
 *   * every hit resolves by (file, 0-based round) in its session's replay-facts.json to its match
 *     POSITION, and every named entry names a hit or a cross-route round.
 */
import { expect } from 'bun:test';
import { readFileSync } from 'node:fs';
export { checkNamedList, cellOf, roundOf } from './route-facts-checks.ts';
import { roundOf } from './route-facts-checks.ts';

/** `check.by_session` against each session's `opener-facts.json` `donation.check` (the count and the
 *  disagreements) and `donation.players[].tspin_clears_scored` (per player). */
export function checkScoredAgainstOpenerFacts(art: any, sessions: string[], root: string) {
  let total = 0;
  for (const s of sessions) {
    const of = JSON.parse(readFileSync(`${root}/${s}/sim/opener-facts.json`, 'utf8'));
    const mine = art.check.by_session[s];
    expect(mine, `${s}: no by_session entry`).toBeDefined();
    expect(mine.tspin_clears, `${s} tspin_clears`).toBe(of.donation.check.tspin_clears);
    expect(mine.reconstruction_disagreed, `${s} reconstruction_disagreed`).toBe(of.donation.check.reconstruction_disagreed);
    // a missing player is a failure, never a 0 (the 全消 lesson): the key sets must be equal first
    expect(Object.keys(mine.players).sort(), `${s} players`).toEqual(of.donation.players.map((p: any) => p.user).sort());
    for (const p of of.donation.players) {
      const n = mine.players[p.user];
      if (typeof n !== 'number') throw new Error(`${s} ${p.user}: no tspin_clears_scored in the technique artefact`);
      expect(n, `${s} ${p.user} tspin_clears_scored`).toBe(p.tspin_clears_scored);
    }
    total += mine.tspin_clears;
  }
  expect(total).toBe(art.check.tspin_clears_scored);
  return total;
}

/** Every hit resolves to its match POSITION; every named entry names a hit or a cross-route round. */
export function checkHitPositions(art: any, sessions: string[], root: string, named: string[]) {
  const pos = new Map<string, number>();
  for (const s of sessions) {
    const rf = JSON.parse(readFileSync(`${root}/${s}/sim/replay-facts.json`, 'utf8'));
    for (const r of rf.rounds) pos.set(`${s}|${r.file}|${r.round}`, r.match);
  }
  const names = new Set<string>();
  for (const h of art.hits) {
    const m = pos.get(`${h.session}|${h.file}|${h.round_index0}`);
    expect(m, `${h.session} ${h.file} r${h.round_index0}`).toBeDefined();
    expect(h.match).toBe(m!);
    expect(h.round).toBe(h.round_index0 + 1);
    names.add(`${h.session} m${h.match}r${h.round} ${h.player}`);
  }
  for (const r of art.cross_route?.by_round ?? []) names.add(r.round);
  for (const e of named) expect(names.has(roundOf(e)), e).toBe(true);
}

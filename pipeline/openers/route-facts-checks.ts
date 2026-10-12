/**
 * The checks every opener's route-artefact test makes, written ONCE (`honey-cup.test.ts`; the 迷走砲
 * test, `stray-cannon.test.ts`, predates this file and keeps its own copies, which say the same
 * thing). A check kept in two test files drifts the way a rule kept in two gates does.
 *
 *   * the flag equals `opener-facts.json`'s `exact` for the opener in every (session, player) cell —
 *     the FLAG, never a node count;
 *   * a named list equals the artefact's, as a set AND per (session, player) cell;
 *   * every case and every named entry resolves to a real round with its match POSITION.
 */
import { expect } from 'bun:test';
import { readFileSync } from 'node:fs';

export const caseName = (c: any) => `${c.session} m${c.match}r${c.round} ${c.player}`;
/** `2026-07-22 m2r1 yachi …` -> `2026-07-22 yachi`: the (session, player) cell an entry is in */
export const cellOf = (entry: string) => entry.split(' ').filter((_, i) => i === 0 || i === 2).join(' ');
/** an entry's round name, with any `(…)`, ` under …` or other annotation after the player cut off */
export const roundOf = (entry: string) => entry.split(' ').slice(0, 3).join(' ');

/** `flag` per (session, player) equals the opener's `exact` in that session's opener-facts.json. */
export function checkFlagAgainstOpenerFacts(art: any, sessions: string[], root: string, key: string,
                                            flag: string): { cells: number; total: number } {
  let cells = 0, total = 0;
  for (const s of sessions) {
    const of = JSON.parse(readFileSync(`${root}/${s}/sim/opener-facts.json`, 'utf8'));
    const op = of.named_openers.openers.filter((o: any) => o.key === key);
    expect(op.length, `${s}: opener-facts.json entries for ${key}`).toBe(1);
    for (const p of op[0].players) {
      const mine = art.cases.filter((c: any) => c.session === s && c.player === p.user && c.bag1[flag]);
      expect(mine.length, `${s} ${p.user} ${flag}`).toBe(p.exact);
      cells++; total += mine.length;
    }
  }
  return { cells, total };
}

/** A named list against the artefact's: the same set, and the same count in every cell, so an
 *  entry naming a cell the data does not support fails, and so does a deleted real one. */
export function checkNamedList(label: string, got: string[], want: string[]) {
  expect([...got].sort(), label).toEqual([...want].sort());
  const count = (xs: string[]) => {
    const m: Record<string, number> = {};
    for (const x of xs) m[cellOf(x)] = (m[cellOf(x)] ?? 0) + 1;
    return m;
  };
  expect(count(got), label).toEqual(count(want));
}

/** Every case resolves by (file, 0-based round) in its session's replay-facts.json to its match
 *  POSITION, and every named entry names a case. */
export function checkPositions(art: any, sessions: string[], root: string, named: string[]) {
  const pos = new Map<string, number>();
  for (const s of sessions) {
    const rf = JSON.parse(readFileSync(`${root}/${s}/sim/replay-facts.json`, 'utf8'));
    for (const r of rf.rounds) pos.set(`${s}|${r.file}|${r.round}`, r.match);
  }
  const byName = new Set<string>();
  for (const c of art.cases) {
    const m = pos.get(`${c.session}|${c.file}|${c.round_index0}`);
    expect(m, `${c.session} ${c.file} r${c.round_index0}`).toBeDefined();
    expect(c.match, caseName(c)).toBe(m!);
    expect(c.round).toBe(c.round_index0 + 1);
    byName.add(caseName(c));
  }
  for (const e of named) expect(byName.has(roundOf(e)), e).toBe(true);
}

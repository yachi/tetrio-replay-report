/**
 * A hand-written session list, checked against disk, in BOTH directions.
 *
 * `finesse-counters.test.ts` and `openers.test.ts` each pin per-session literals — round
 * counts, fault totals, exact-match counts — against a list of session dates typed into the
 * file. Both already fail when a listed session STOPS being readable; neither notices one that
 * ARRIVES. That is half a guard, and the missing half is the one a seventh session trips: the
 * list simply does not name it, every assertion below still passes over the six it does name,
 * and a shorter corpus is indistinguishable from a clean run. It is the same shape as the two
 * stale loops in verify.yml and the four-session lists that sat through 08-09 and 08-14.
 *
 * WHY A LIST SURVIVES AT ALL rather than globbing the corpus. Both callers assert pinned
 * literals that only exist for a session somebody has measured; globbing would admit an
 * unmeasured session straight into a `toBe(...)` with no measurement behind it. So the list
 * stays and MEMBERSHIP is what gets gated — the trade `check_loo.PUBLISHED` already makes
 * ("Every measurable session must appear"). Adding a session is meant to fail here first, and
 * the failure names what to do: add it WITH its literals.
 *
 * The check runs at module scope in both callers, not inside a test, so it cannot be skipped
 * by a `skipIf` or hidden in a test that does not run.
 */
import { existsSync, readdirSync } from 'node:fs';

/**
 * Every session directory on disk, by the only thing that makes one a session: it holds
 * replays. Deliberately NOT keyed on a `sim/` or `report/` subdirectory — those are outputs of
 * other tools, and keying on one makes the corpus depend on whether an unrelated artifact
 * happened to have been written yet. Same predicate as `forecast-saturation.test.ts` and
 * `check_provenance.sessionDirs`.
 */
export function sessionsOnDisk(sessionsRoot: string): string[] {
  if (!existsSync(sessionsRoot)) return [];
  return readdirSync(sessionsRoot)
    .filter(s => existsSync(`${sessionsRoot}/${s}`)
      && readdirSync(`${sessionsRoot}/${s}`).some(f => f.endsWith('.ttrm')))
    .sort();
}

/**
 * The corpus, discovered — for the files that pin NO per-session literal and so need no list.
 *
 * Throws on an empty corpus rather than returning `[]`, because every assertion downstream passes
 * vacuously over an empty array and a sweep over nothing prints exactly like a clean one. Callers
 * that deliberately support a session-less checkout want `sessionsOnDisk` and their own `skipIf`.
 *
 * This is NOT the discovery `sim-test-corpus-silently-under-covers` warns about. That memory is
 * about keying the corpus on INCIDENTAL filesystem state — `forecast-saturation.test.ts` admitted a
 * session only once some other tool had written it a `sim/` directory, so the corpus depended on
 * whether an unrelated artifact happened to exist yet. `.ttrm` is not incidental: it is what makes
 * a session a session, and it is the predicate `forecast-saturation.test.ts` and
 * `forecast-access-class.test.ts` were both moved to when that hole was closed.
 */
export function discoverCorpus(sessionsRoot: string): string[] {
  const disk = sessionsOnDisk(sessionsRoot);
  if (!disk.length)
    throw new Error(`corpus discovery: no session directories with .ttrm replays under ${sessionsRoot}`);
  return disk;
}

/**
 * Throws unless `listed` is exactly the sessions on disk. Returns `listed` unchanged so the
 * caller reads `const SESSIONS = assertCorpusIsEverySessionOnDisk(root, [...])` and keeps the
 * array it already had.
 */
export function assertCorpusIsEverySessionOnDisk(sessionsRoot: string, listed: string[]): string[] {
  const disk = sessionsOnDisk(sessionsRoot);
  const missing = disk.filter(s => !listed.includes(s));
  const extra = listed.filter(s => !disk.includes(s));
  const dupes = [...new Set(listed.filter(s => listed.filter(x => x === s).length > 1))].sort();
  const problems: string[] = [];
  if (missing.length)
    problems.push(`${missing.length} session(s) on disk that this file does not cover: `
      + `${missing.join(', ')} — a shorter corpus is indistinguishable from a clean run, so add `
      + `them together with their pinned literals`);
  if (extra.length)
    problems.push(`${extra.length} session(s) listed here that are not on disk: ${extra.join(', ')}`);
  if (dupes.length)
    problems.push(`listed more than once: ${dupes.join(', ')}`);
  // An empty corpus is its own failure: every assertion downstream passes vacuously over an
  // empty array, which is the shape `openers.test.ts` already records paying for when a `?? 0`
  // let a corpus of defaults agree with itself.
  if (!disk.length)
    problems.push(`no session directories with .ttrm replays under ${sessionsRoot}`);
  if (problems.length) throw new Error('corpus membership: ' + problems.join('; '));
  return listed;
}

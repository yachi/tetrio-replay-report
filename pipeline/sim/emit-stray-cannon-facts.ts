/**
 * 迷走砲 (Stray Cannon) route classifier: the deepest node of shiwehi.com's route tree that each
 * corpus round reaches, over every session at once.
 *
 *   bun pipeline/sim/emit-stray-cannon-facts.ts --out analysis/stray-cannon-facts.json
 *
 * A SHIM since the route pages were generalised: every rule is in the shared classifier
 * `route-facts.ts` (read its header for the walk), every 迷走砲 constant and string in
 * `route-profile-meisou.ts`. This file binds the two with the signatures the 迷走砲 tests and the
 * CLAUDE.md commands use, and is the entry file hashed into `emitter_md5`.
 *
 * The 迷走砲 walk, in the profile's terms. Bag 1, PLACED FIRST: the clean board after 7 locks against
 * `bag1.z_right`, then `bag1.z_left`, as drawn and mirrored; only when neither matches is the board
 * after 6 locks compared with `bag1.z_hold`, and then the piece placed at lock 7 is read and compared
 * with the MIRROR-AWARE bag-1 Z (Z as drawn, S when mirrored): not that piece -> `bag1.z_hold`, the
 * only node that asserts a hold; that piece -> the outcome `bag1.z_placed_elsewhere`. `matched_at_6`
 * is a FLAG, not a node. Bag 2 after 13 pieces (0-based lock 12), before any garbage. Bag 3: the
 * 8-line PC after a TST, scoped to the round's own branch; the snapshot routes under their branch.
 */
import { writeFileSync } from 'node:fs';
import { loadRoutes as loadAt, digestSession as digestAt, classify as classifyAt, composite as compositeAt,
         patternMatches as patternAt, inputs as inputsAt, assemble as assembleAt, build as buildAt,
         serialise, SESSIONS_ROOT, type RoundDigest, type Routes, type Mutants, type Classified }
  from './route-facts.ts';
import { MEISOU } from './route-profile-meisou.ts';

export { BAG1_PLACED_LOCKS, BAG1_HOLD_LOCKS, BAG2_LOCK, EVENT_LOCKS, SNAPSHOT_LOCKS, PC_ROWS, PC_LINES }
  from './route-profile-meisou.ts';
export { initialRowmap, advanceRowmap, conditionHolds, serialise, corpus } from './route-facts.ts';
export type { DigestLock, RoundDigest, RouteNode, Routes, Mutants, Classified } from './route-facts.ts';

export const ROUTES_PATH = MEISOU.routesPath;
export const ARTEFACT_PATH = MEISOU.artefactPath;

export const loadRoutes = (path = ROUTES_PATH): Routes => loadAt(path);
export const digestSession = (session: string, root = SESSIONS_ROOT): RoundDigest[] =>
  digestAt(session, root, { snapshotLocks: MEISOU.snapshotLocks, tag: MEISOU.tag });
export const classify = (digests: RoundDigest[], routes: Routes, mut: Mutants = {}) =>
  classifyAt(MEISOU, digests, routes, mut);
export const composite = (d: RoundDigest, tstI: number, end: number) =>
  compositeAt(d, tstI, end, MEISOU.pcRows, MEISOU.tag);
export const patternMatches = (comp: string[], rows: string[], mirrored: boolean, colour: boolean) =>
  patternAt(comp, rows, mirrored, colour, MEISOU.pcRows);
export const inputs = (sessions: string[], root = SESSIONS_ROOT) => inputsAt(MEISOU, sessions, root);
export const assemble = (cls: Classified, routes: Routes, sessions: string[], inp: ReturnType<typeof inputs>) =>
  assembleAt(MEISOU, cls, routes, sessions, inp);
export const build = (mut: Mutants = {}, digests?: RoundDigest[]) => buildAt(MEISOU, mut, digests);

if (import.meta.main) {
  const outIx = process.argv.indexOf('--out');
  const text = serialise(build());
  if (outIx > 0) writeFileSync(process.argv[outIx + 1]!, text);
  else process.stdout.write(text);
}

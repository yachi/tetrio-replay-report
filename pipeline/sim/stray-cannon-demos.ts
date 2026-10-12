/**
 * 迷走砲 (Stray Cannon) CONSTRUCTED DEMOS: one replay per drawn route node of shiwehi.com's page,
 * built from an empty board by placing the pieces one at a time, and run through the vendored
 * Triangle engine.
 *
 *   bun pipeline/sim/emit-stray-cannon-demos.ts --out analysis/stray-cannon-demos.json
 *
 * A SHIM since the route pages were generalised: the planner is the shared `route-demos.ts` (read
 * its header: the engine is the arbiter, the row map, the U slot), and every 迷走砲 constant, colour
 * reading and string is in `route-profile-meisou.ts`. This file binds the two with the signatures
 * the 迷走砲 test uses, and is the entry file hashed into `planner_md5`.
 *
 * NOT CORPUS DATA. Nobody played these games: the artefact says `report_eligible: false` and
 * `constructed: true`, and nothing that draws from it carries a claim id, a ✓ or a `data-claim`.
 */
import { readRows as readRowsWith, planBag as planBagFor, demoNodes as demoNodesFor, chainOf as chainOfTagged,
         build as buildFor, type BagSpec, type DemoMutants } from './route-demos.ts';
import type { RouteNode, Routes } from './route-facts.ts';
import { MEISOU, PIECE_READINGS, DEMO_UNBUILT } from './route-profile-meisou.ts';

export { PIECE_READINGS, DEMO_UNBUILT };
export { FRAMES_PER_INPUT, DEMO_HANDLING, DEMO_OPTIONS, demoDate, PIECES, newEngine, reach, inputsOf, runDemo,
         placeCells, queueStates, serialise } from './route-demos.ts';
export type { Edge, Path, Group, DemoMutants, BagSpec, Lock } from './route-demos.ts';

export const DEMOS_PATH = MEISOU.demosPath;

/** A node's rows with 迷走砲's colour readings applied. */
export const readRows = (id: string, rows: string[]) => readRowsWith(id, rows, PIECE_READINGS, MEISOU.tag);
export const planBag = (eng: any, st: any, spec: BagSpec, mut: DemoMutants, fail: string[]) =>
  planBagFor(MEISOU, eng, st, spec, mut, fail);
export const demoNodes = (routes: Routes) => demoNodesFor(MEISOU, routes);
export const chainOf = (n: RouteNode, routes: Routes) => chainOfTagged(n, routes, MEISOU.tag);
export const build = (mut: DemoMutants = {}) => buildFor(MEISOU, mut);

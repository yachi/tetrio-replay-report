/**
 * COLD CLEAR CORROBORATION of the route-order DAG's edges (`analysis/<opener>-orders.json`).
 *
 * An edge [subset, group] of a node's DAG says: on the board the subset leaves, the engine's own
 * `reach()` gets the group's piece onto the group's cells. That is one engine's verdict, which is why
 * the orders artefact is quarantined. This asks the ORIGINAL cold-clear mover (`libtetris::find_moves`,
 * `MovementMode::ZeroGComplete`, through `nix/cold-clear-oracle/cc-oracle.rs` with `CC_ORACLE_MOVES=1`)
 * the same question per edge: are the target cells among cold-clear's resting placements for that
 * piece on that board? It corroborates CELLS only, never the spin the planner required.
 *
 * Each edge is `corroborated` or `ours_only`. An `ours_only` edge is triaged by re-running `reach()`
 * with `{ no180: true }` under the same spin filter `nodeDag` applied:
 *   - `tuck`  still reachable without a 180: the known `cc ⊆ ours` asymmetry (cold-clear shifts the
 *             piece sideways only at rest heights, our BFS at any height; see `cross-movegen.test.ts`);
 *   - `180`   reachable only with a 180 (cold-clear's mover has no 180 in guideline SRS);
 * plus the flag `i_srs_plus` when the piece is I (cold-clear kicks with guideline SRS, the engine with
 * SRS+, whose I kicks differ).
 *
 * THE PARENT LOOP BELOW IS A COPY of `build()`'s `stateOf` in `route-orders.ts`, which does not export
 * its per-node DAGs. The copy is guarded, not trusted: every DAG's edges must equal the committed
 * orders artefact's edges for that node, or this throws.
 *
 *   bun pipeline/sim/emit-route-orders-cc.ts --opener sdpcspin --out analysis/sdpcspin-orders-cc.json
 *
 * The binary is `$CC_ORACLE`, else `result/bin/cc-oracle` resolved from this file. Its store path is
 * not portable, so the artefact records the nix rev parsed out of the store path name instead.
 */
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, realpathSync, writeFileSync } from 'node:fs';
import { nodeDag, accepts, allOrders } from './route-orders.ts';
import { newEngine, reach, planBag, chainOf, demoNodes, demoProfile, specFor, emptyGrid } from './route-demos.ts';
import { WIDTH, ROWS } from './emit-replay.ts';
import { loadRoutes, md5Files } from './route-facts.ts';
import { openerFromArgv } from './route-openers.ts';
import type { RouteProfile } from './route-profile.ts';

export const ORACLE = process.env.CC_ORACLE ?? `${import.meta.dir}/../../result/bin/cc-oracle`;
export const HAVE_ORACLE = existsSync(ORACLE);

const md5 = (b: string | Buffer) => createHash('md5').update(b).digest('hex');
export const ordersPath = (P: RouteProfile) => `${import.meta.dir}/../../analysis/${P.tag}-orders.json`;
export const ccPath = (P: RouteProfile) => `${import.meta.dir}/../../analysis/${P.tag}-orders-cc.json`;

/** The nix rev of the oracle build, from its store path name (`…-cc-oracle-0-unstable-<rev>`). */
export function oracleRev(path = ORACLE): string {
  const real = realpathSync(path);
  const m = real.match(/cc-oracle-[^/]*-unstable-([0-9a-f]+)\//);
  if (!m) throw new Error(`orders-cc: cannot read a nix rev out of ${real}`);
  return m[1]!;
}

/** Cell `yUp * WIDTH + x` → cold-clear's top-down [col, row], canonical key sorted (row, col). */
const keyOfTarget = (cells: number[]) =>
  cells.map(c => [c % WIDTH, ROWS - 1 - Math.floor(c / WIDTH)] as [number, number])
    .sort((a, b) => a[1] - b[1] || a[0] - b[0]).map(c => `${c[0]},${c[1]}`).join('|');
const keyOfPairs = (pairs: [number, number][]) =>
  pairs.slice().sort((a, b) => a[1] - b[1] || a[0] - b[0]).map(c => `${c[0]},${c[1]}`).join('|');

export function build(P: RouteProfile) {
  if (!HAVE_ORACLE) throw new Error(`orders-cc: no oracle at ${ORACLE}`);
  const orders = JSON.parse(readFileSync(ordersPath(P), 'utf8'));
  const byNode = new Map<string, any>(orders.nodes.map((n: any) => [n.node, n]));
  const DP = demoProfile(P);
  const routes = loadRoutes(P.routesPath);
  const eng = newEngine(routes);
  // ── a copy of route-orders.ts build()'s parent loop (guarded by the edge equality below) ──
  const cache = new Map<string, any>();
  const stateOf = (n: any): any => {
    if (cache.has(n.id)) return cache.get(n.id);
    const chain = chainOf(n, routes, P.tag, DP.chainVia);
    const parent = chain.length > 1 ? stateOf(chain[chain.length - 2]!) : { grid: emptyGrid(), placements: [], bags: [] };
    const st = parent ? planBag(P, eng, parent, specFor(P, n, routes), {}, []) : null;
    cache.set(n.id, st);
    return st;
  };
  type Rec = { node: string; s: number; g: number; piece: string; spinSlot: boolean; rows: string[]; target: number[] };
  const recs: Rec[] = [];
  const seenNodes: string[] = [];
  for (const n of demoNodes(P, routes)) {
    const want = byNode.get(n.id);
    if (!want) continue;                     // refused in the orders artefact: no DAG to corroborate
    const chain = chainOf(n, routes, P.tag, DP.chainVia);
    const pn = chain.length > 1 ? chain[chain.length - 2]! : null;
    const parent = pn ? stateOf(pn) : { grid: emptyGrid(), placements: [], bags: [] };
    const dag = nodeDag(P, eng, n, routes, parent);
    if (JSON.stringify(dag.edges) !== JSON.stringify(want.edges))
      throw new Error(`orders-cc: ${n.id} DAG edges differ from the committed orders artefact`);
    seenNodes.push(n.id);
    for (const [s, g] of dag.edges) {
      recs.push({ node: n.id, s, g, piece: dag.groups[g]!.piece, spinSlot: dag.groups[g]!.spin_slot,
                  rows: dag.boards.get(s)!, target: dag.targets.get(`${s},${g}`)! });
    }
  }
  if (seenNodes.join() !== orders.nodes.map((n: any) => n.node).join())
    throw new Error('orders-cc: node set differs from the committed orders artefact');
  // ── one oracle call for every edge, in edge order ──
  const input = recs.map(r => r.piece + '\n' + [...r.rows].reverse().join('\n')).join('\n') + '\n';
  const res = spawnSync(ORACLE, { input, encoding: 'utf8', env: { ...process.env, CC_ORACLE_MOVES: '1' },
                                  maxBuffer: 1 << 28 });
  if (res.status !== 0) throw new Error('orders-cc: cc-oracle failed: ' + res.stderr);
  const lines = res.stdout.split('\n').filter(l => l.trim());
  if (lines.length !== recs.length) throw new Error(`orders-cc: oracle returned ${lines.length} lines for ${recs.length} edges`);
  const out = new Map<string, any[]>(seenNodes.map(id => [id, []]));
  recs.forEach((r, j) => {
    const cc = new Set((JSON.parse(lines[j]!).placements as [number, number][][]).map(keyOfPairs));
    let entry: any[];
    if (cc.has(keyOfTarget(r.target))) entry = [r.s, r.g, 'corroborated'];
    else {
      const grid = r.rows.map(row => [...row].map(ch => (ch === '.' ? null : ch)));
      // the spin filter nodeDag applied to this edge
      const ok = (p: any) => r.spinSlot ? p.spin === 'normal' : (r.piece !== 'T' || p.spin === null);
      const no180 = reach(eng, grid, r.piece, r.target, { no180: true }).filter(ok);
      entry = [r.s, r.g, 'ours_only', no180.length ? 'tuck' : '180'];
      if (r.piece === 'I') entry.push('i_srs_plus');
    }
    out.get(r.node)!.push(entry);
  });
  const ordersText = readFileSync(ordersPath(P));
  return {
    schema: 'route-orders-cc/1',
    opener: P.tag,
    report_eligible: false,
    means: 'per edge of each node\'s route-order DAG: whether the original cold-clear mover reaches the edge\'s target cells for that piece on that board (cells only, never the spin)',
    oracle: { binary: 'cc-oracle (nix/cold-clear-oracle)', nix_rev: oracleRev(),
              mode: 'CC_ORACLE_MOVES=1: libtetris::find_moves, MovementMode::ZeroGComplete, guideline SRS, spawn Row19Or20' },
    classes: {
      corroborated: 'the target cells are one of cold-clear\'s resting placements',
      ours_only: 'they are not; triaged by reach() with no180 under the edge\'s own spin filter',
      tuck: 'still reachable without a 180: the cc ⊆ ours asymmetry (cold-clear shifts only at rest heights)',
      '180': 'reachable only with a 180',
      i_srs_plus: 'flag: the piece is I (cold-clear kicks with guideline SRS, the engine with SRS+)',
    },
    inputs: {
      routes_md5: orders.inputs.routes_md5,
      orders_md5: orders.inputs.orders_md5,
      orders_artefact_md5: md5(ordersText),
      cc_emitter_md5: md5Files([`${import.meta.dir}/emit-route-orders-cc.ts`]),
    },
    nodes: seenNodes.map(id => ({ node: id, edges: out.get(id)! })),
  };
}

/** One node per line, metadata pretty-printed (as the orders artefact). */
export function serialise(out: any): string {
  const { nodes, ...rest } = out;
  const head = JSON.stringify({ ...rest, nodes: '\u0000' }, null, 1);
  return head.replace('"\\u0000"', '[\n' + nodes.map((d: any) => '  ' + JSON.stringify(d)).join(',\n') + '\n ]') + '\n';
}

/** Per node, how many orders `accepts()` keeps if only the corroborated edges are kept (empty hold). */
export function survivors(orders: any, cc: any): { node: string; all: number; cc_only: number }[] {
  const ORDERS = allOrders();
  const ccBy = new Map<string, any[]>(cc.nodes.map((n: any) => [n.node, n.edges]));
  return orders.nodes.map((n: any) => {
    const edges = ccBy.get(n.node)!.filter(e => e[2] === 'corroborated').map(e => [e[0], e[1]] as [number, number]);
    const dag = { groups: n.groups, edges, full: (1 << n.k) - 1, full_ok: n.full_ok };
    return { node: n.node, all: n.counts.empty, cc_only: ORDERS.filter(q => accepts(dag, q, null)).length };
  });
}

if (import.meta.main) {
  const t0 = performance.now();
  const P = openerFromArgv(process.argv);
  const out = build(P);
  const text = serialise(out);
  const ix = process.argv.indexOf('--out');
  if (ix > 0) writeFileSync(process.argv[ix + 1]!, text);
  else process.stdout.write(text);
  const all = out.nodes.flatMap(n => n.edges);
  const tally: Record<string, number> = {};
  for (const e of all) { const k = e.slice(2).join('/'); tally[k] = (tally[k] ?? 0) + 1; }
  console.error(`nodes ${out.nodes.length}, edges ${all.length}, ${JSON.stringify(tally)}, `
    + `${((performance.now() - t0) / 1000).toFixed(1)} s`);
  const orders = JSON.parse(readFileSync(ordersPath(P), 'utf8'));
  for (const s of survivors(orders, out)) console.error(`  ${s.node.padEnd(28)} accepted ${s.all}, with cc-corroborated edges only ${s.cc_only}`);
}

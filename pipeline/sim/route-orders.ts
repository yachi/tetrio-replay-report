/**
 * WHICH DEALT ORDERS BUILD EACH DRAWN ROUTE NODE — the engine half of the route-order count.
 *
 * Quarantined like the demos: one engine decides which placements are reachable, so the artefact says
 * `report_eligible: false`, and nothing here enters a claim, a badge or a corpus count. Cold Clear
 * corroborates the reachable CELLS of each edge (`route-orders-cc.json`), never its spin.
 *
 * The question splits in two, and only the second half is mathematics:
 *
 *   1. ENGINE. A node's drawing is a set of piece groups whose cells are fixed in the drawing's own
 *      rows; a row clears when it is full. So the board after placing a SET of the groups does not
 *      depend on the order they went in (theorem T1, proved in `spec/RouteOrders.dfy` and
 *      `lean/RouteOrders`, and checked here on every node: two orders reaching one set must leave one
 *      board, or this module throws). The buildable placement orders are therefore the paths from
 *      the empty set to the full set in a DAG over at most 2^7 subsets. An edge S -> S + g exists when
 *      the engine's own `reach()` gets g's piece to its cells on board(S) with the spin the planner
 *      requires, under the planner's rules (`uLast`, `uFiresBefore`, the U's line count, a Perfect
 *      Clear at the end). The page's ORDER CONDITIONS are deliberately not edges: the count tests them.
 *
 *   2. HOLD (no Tetris rules; theorems T2 and T4). The bag deals its seven pieces in an order Q, then
 *      one piece of the next bag, '*', which may enter the hold and may never be placed. Per placement
 *      the player places the current piece, or swaps it with the held piece and places that, or — hold
 *      empty — holds the current piece and places the one after. Q builds the node iff some sequence of
 *      those choices places the groups in an order that is a DAG path. A drawing with fewer than seven
 *      groups is the bag's FIRST k placements; its other pieces are dealt but never placed here.
 *
 * Bag-to-bag: a node is enumerated from an empty hold and from "the next piece already held" (the two
 * states a whole-bag parent can leave), and T4 says those accept the same orders; the artefact carries
 * both counts and the test asserts they agree. A parent that does not place a whole bag is refused.
 */
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { newEngine, reach, planBag, chainOf, demoNodes, demoProfile, PIECES, groupsOf, applyCells,
         specFor, cloneGrid, emptyGrid, gridKey, type Group } from './route-demos.ts';
import { encodePlace, WIDTH } from './emit-replay.ts';
import { loadRoutes, initialRowmap, advanceRowmap, md5Files, type RouteNode } from './route-facts.ts';
import type { RouteProfile } from './route-profile.ts';

/** Each field turns ONE rule of the hold search off; the test requires each to change a count. */
export interface OrderMutants {
  noSwap?: boolean;        // the held piece can never come out
  noHoldFirst?: boolean;   // an empty hold cannot take the current piece (case c dropped)
  placeStar?: boolean;     // the next bag's piece '*' may be placed, as any group the DAG allows
  noStar?: boolean;        // the stream ends at the bag: the last swap cannot pull the next piece in
}

/** The 5040 dealt orders, in a fixed rank: lexicographic in the index of each piece in PIECES. */
export function allOrders(): string[] {
  const out: string[] = [];
  const rec = (pre: string, left: string) => {
    if (!left) { out.push(pre); return; }
    for (let i = 0; i < left.length; i++) rec(pre + left[i], left.slice(0, i) + left.slice(i + 1));
  };
  rec('', PIECES);
  return out;
}

export interface NodeDag {
  groups: { letter: string; piece: string; carried: boolean; spin_slot: boolean }[];
  /** [subset, group index]: group g is placeable on board(subset) */
  edges: [number, number][];
  full: number;
  /** the full set's board is the drawing (and, for a Perfect Clear node, empty) */
  full_ok: boolean;
  /** board rows per reached subset (y-up row strings), for the Cold Clear corroboration */
  boards: Map<number, string[]>;
  /** per edge, the target cells (yUp * WIDTH + x) the engine reached */
  targets: Map<string, number[]>;
}

const rowsOf = (g: any): string[] => g.map((r: any[]) => r.map(c => (c ? String(c)[0] : '.')).join(''));

export function nodeDag(P: RouteProfile, eng: any, n: RouteNode, routes: any, parent: any): NodeDag {
  const DP = demoProfile(P);
  const spec: any = specFor(P, n, routes);
  const carriedIn = parent.held && !parent.heldNext ? parent.held : null;
  const groups: Group[] = groupsOf(n, DP.pieceReadings, P.tag,
    { carried: carriedIn, spinLetter: spec.spinLetter ?? null, spinCells: spec.spinCells ?? [] });
  const uBefore: string[] = spec.uBefore ?? [];
  const k = groups.length;
  const states = new Map<number, { grid: any; rowmap: number[] }>([[0, { grid: cloneGrid(parent.grid), rowmap: initialRowmap() }]]);
  const edges: [number, number][] = [];
  const targets = new Map<string, number[]>();
  for (let s = 0; s < (1 << k); s++) {
    const st = states.get(s);
    if (!st) continue;
    const left = groups.filter((_, i) => !(s & (1 << i)));
    groups.forEach((g, i) => {
      if (s & (1 << i)) return;
      if (spec.uLast && g.spinSlot && left.some(o => o !== g && !(uBefore.includes(o.piece) && !o.carried))) return;
      if (!g.spinSlot && !g.carried && uBefore.includes(g.piece) && left.some(o => o.spinSlot)) return;
      const target: number[] = [];
      for (const [x, d] of g.cells) {
        const e = st.rowmap.indexOf(d);
        if (e < 0) return;
        target.push(e * WIDTH + x);
      }
      if (target.some(c => st.grid[Math.floor(c / WIDTH)][c % WIDTH] != null)) return;
      try { encodePlace(g.piece, target); } catch { return; }
      const want = (p: any) => g.spinSlot ? p.spin === 'normal' : (g.piece !== 'T' || p.spin === null);
      const cand = reach(eng, st.grid, g.piece, target).filter(want);
      if (!cand.length) return;
      const ng = cloneGrid(st.grid);
      const cl = applyCells(ng, g.piece, cand[0]!.cells);
      if (g.spinSlot && spec.uLines != null && cl.length !== spec.uLines) return;
      const t = s | (1 << i);
      const rm = advanceRowmap(st.rowmap, cl);
      const seen = states.get(t);
      // T1 on real data: a second order into the same set must leave the same board
      if (seen && (gridKey(seen.grid) !== gridKey(ng) || seen.rowmap.join() !== rm.join()))
        throw new Error(`route-orders: ${n.id} set ${t} reached with two boards`);
      if (!seen) states.set(t, { grid: ng, rowmap: rm });
      edges.push([s, i]);
      targets.set(`${s},${i}`, [...target].sort((a, b) => a - b));
    });
  }
  const full = (1 << k) - 1;
  const fs = states.get(full);
  const full_ok = !!fs && (!spec.pc || fs.grid.every((r: any[]) => r.every(c => c == null)));
  const boards = new Map<number, string[]>();
  for (const [s, st] of states) boards.set(s, rowsOf(st.grid));
  return { groups: groups.map(g => ({ letter: g.letter, piece: g.piece, carried: !!g.carried, spin_slot: g.spinSlot })),
           edges, full, full_ok, boards, targets };
}

/** THE HOLD SEARCH. `held0`: 'C' (a carried piece), a dealt piece letter, or null. Returns whether some
 *  sequence of place / swap / hold-first choices places every group along DAG edges. */
export function accepts(dag: Pick<NodeDag, 'groups' | 'edges' | 'full' | 'full_ok'>, order: string,
                        held0: string | null, mut: OrderMutants = {}): boolean {
  if (!dag.full_ok) return false;
  const out = new Map<number, Set<number>>();
  for (const [s, g] of dag.edges) { if (!out.has(s)) out.set(s, new Set()); out.get(s)!.add(g); }
  const dealt = new Map<string, number>();
  dag.groups.forEach((g, i) => { if (!g.carried) dealt.set(g.piece, i); });
  const carried = dag.groups.findIndex(g => g.carried);
  const stream = mut.noStar ? [...order] : [...order, '*'];
  const groupOf = (tok: string | null): number =>
    tok === null ? -1 : tok === 'C' ? carried : dealt.get(tok) ?? -1;
  const seen = new Set<string>();
  const go = (s: number, i: number, h: string | null): boolean => {
    if (s === dag.full) return true;
    const key = `${s},${i},${h}`;
    if (seen.has(key)) return false;
    seen.add(key);
    const can = (g: number) => g >= 0 && !(s & (1 << g)) && !!out.get(s)?.has(g);
    const cur = stream[i];
    if (cur === undefined) return false;
    const gc = groupOf(cur);
    if (can(gc) && go(s | (1 << gc), i + 1, h)) return true;                 // place the current piece
    if (cur === '*' && mut.placeStar) {                                       // the mutant: '*' as any group
      for (let g = 0; g < dag.groups.length; g++) if (can(g) && go(s | (1 << g), i + 1, h)) return true;
    }
    if (h !== null && !mut.noSwap) {
      const gh = groupOf(h);
      if (can(gh) && go(s | (1 << gh), i + 1, cur)) return true;             // swap, place the held one
    }
    if (h === null && !mut.noHoldFirst && cur !== '*') {
      const nx = stream[i + 1];
      const gn = nx === undefined ? -1 : groupOf(nx);
      if (can(gn) && go(s | (1 << gn), i + 2, cur)) return true;             // hold it, place the next
    }
    return false;
  };
  return go(0, 0, held0);
}

/** 5040 bits, bit j = order j of `allOrders()`, LSB first within each byte, as hex. */
export function bitsHex(bits: boolean[]): string {
  const bytes = new Uint8Array(Math.ceil(bits.length / 8));
  bits.forEach((b, j) => { if (b) bytes[j >> 3]! |= 1 << (j & 7); });
  return Buffer.from(bytes).toString('hex');
}

/** The page's order condition on one dealt order: `all` before-pairs, or `at_least` (one piece before
 *  at least `count` of `of`). null for a condition this cannot decide. */
export function conditionOn(cond: any, order: string): boolean | null {
  if (!cond) return null;
  if (cond.all) return cond.all.every((c: any) => order.indexOf(c.before[0]) < order.indexOf(c.before[1]));
  if (cond.at_least) {
    const a = cond.at_least, ia = order.indexOf(a.before);
    return a.of.filter((p: string) => ia < order.indexOf(p)).length >= a.count;
  }
  return null;
}

const md5 = (b: string | Buffer) => createHash('md5').update(b).digest('hex');

export function build(P: RouteProfile, mut: OrderMutants = {}) {
  const DP = demoProfile(P);
  const routes = loadRoutes(P.routesPath);
  const eng = newEngine(routes);
  const ORDERS = allOrders();
  const cache = new Map<string, any>();
  const stateOf = (n: RouteNode): any => {
    if (cache.has(n.id)) return cache.get(n.id);
    const chain = chainOf(n, routes, P.tag, DP.chainVia);
    const parent = chain.length > 1 ? stateOf(chain[chain.length - 2]!) : { grid: emptyGrid(), placements: [], bags: [] };
    const st = parent ? planBag(P, eng, parent, specFor(P, n, routes), {}, []) : null;
    cache.set(n.id, st);
    return st;
  };
  const nodes: any[] = [];
  const refused: { node: string; reason: string }[] = [];
  for (const n of demoNodes(P, routes)) {
    const chain = chainOf(n, routes, P.tag, DP.chainVia);
    const pn = chain.length > 1 ? chain[chain.length - 2]! : null;
    const parent = pn ? stateOf(pn) : { grid: emptyGrid(), placements: [], bags: [] };
    if (!parent) { refused.push({ node: n.id, reason: `parent ${pn!.id} has no demo` }); continue; }
    // the premise of enumerating a fresh bag: the parent placed a whole bag (or there is no parent)
    const lastBag = parent.bags.at(-1);
    if (lastBag && lastBag.placed.length + (lastBag.unused?.length ?? 0) !== 7) throw new Error(`route-orders: ${n.id} parent bag is not a 7-bag`);
    if (lastBag && lastBag.unused) { refused.push({ node: n.id, reason: `parent ${pn!.id} leaves ${lastBag.unused} unplaced` }); continue; }
    const dag = nodeDag(P, eng, n, routes, parent);
    const carriedIn = parent.held && !parent.heldNext ? parent.held : null;
    const modes: Record<string, boolean[]> = {};
    if (carriedIn) modes[`carried:${carriedIn}`] = ORDERS.map(q => accepts(dag, q, 'C', mut));
    else {
      modes.empty = ORDERS.map(q => accepts(dag, q, null, mut));
      modes.next = ORDERS.map(q => accepts(dag, q.slice(1), q[0]!, mut));
    }
    const first = Object.values(modes)[0]!;
    const cond = n.condition && !n.condition.bag1 ? n.condition : null;
    let condition: any = null;
    if (cond) {
      const sat = ORDERS.map(q => conditionOn(cond, q));
      if (sat.some(v => v === null)) throw new Error(`route-orders: ${n.id} condition not decidable`);
      const c = (f: (a: boolean, s: boolean) => boolean) => first.filter((a, j) => f(a, sat[j]!)).length;
      condition = { condition: cond, stated: sat.filter(Boolean).length,
                    built_and_stated: c((a, s) => a && s), built_not_stated: c((a, s) => a && !s),
                    stated_not_built: c((a, s) => !a && s) };
    }
    nodes.push({
      node: n.id, bag: n.bag, parent: pn?.id ?? null,
      groups: dag.groups, k: dag.groups.length, subsets: dag.boards.size, full_ok: dag.full_ok,
      edges: dag.edges,
      counts: Object.fromEntries(Object.entries(modes).map(([m, b]) => [m, b.filter(Boolean).length])),
      accepted: Object.fromEntries(Object.entries(modes).map(([m, b]) => [m, bitsHex(b)])),
      condition,
    });
  }
  return {
    schema: 'route-orders/1',
    opener: P.tag,
    report_eligible: false,
    constructed: true,
    means: 'for every drawn route node a demo builds, which of the 5040 orders a 7-bag can deal let a player with one hold slot place the drawing\'s pieces in an order the engine can build, on the board the node\'s demo parent leaves',
    not_eligible_because: 'which placements are reachable is one engine\'s (Cold Clear corroborates the cells of each edge, never its spin); the hold combinatorics are proved, the edges are not',
    rules: {
      orders: 'lexicographic permutations of the piece indices of IOTSZJL; accepted bit j = order j, LSB first in each byte, hex',
      stream: 'the bag\'s 7 pieces, then one next-bag piece that may enter the hold and is never placed',
      moves: 'place the current piece; or swap with the held piece and place it; or, hold empty, hold the current piece and place the next',
      edges: '[subset, group]: the engine reaches the group\'s cells on the subset\'s board with the planner\'s spin, uLast, uFiresBefore and line-count rules; the page\'s order conditions are NOT edges',
      partial_bag: 'a drawing with fewer than 7 groups is the bag\'s first k placements',
      modes: 'empty: the bag starts with an empty hold; next: with its first piece already held (theorem T4: the same orders)',
    },
    inputs: {
      routes_md5: md5(readFileSync(P.routesPath)),
      planner_md5: md5Files(P.hashFiles.planner),
      orders_md5: md5Files([`${import.meta.dir}/route-orders.ts`, `${import.meta.dir}/emit-route-orders.ts`]),
    },
    nodes,
    refused,
  };
}

/** One node per line, metadata pretty-printed. */
export function serialise(out: any): string {
  const { nodes, ...rest } = out;
  const head = JSON.stringify({ ...rest, nodes: '\u0000' }, null, 1);
  return head.replace('"\\u0000"', '[\n' + nodes.map((d: any) => '  ' + JSON.stringify(d)).join(',\n') + '\n ]') + '\n';
}

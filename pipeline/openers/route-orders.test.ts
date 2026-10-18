/**
 * The route-order count (`analysis/sdpcspin-orders.json`, from `pipeline/sim/emit-route-orders.ts
 * --opener sdpcspin`; all the logic is `pipeline/sim/route-orders.ts`).
 *
 *   1. byte rebuild: the committed artefact is what `build(SDPCSPIN)` produces now.
 *   2. every `accepted` bitset decodes to 5040 bits whose popcount is the node's count, and the
 *      `empty` and `next` bits are equal node by node (theorem T4, checked empirically on the data).
 *   3. every condition table is what `conditionOn()` gives over the decoded bits.
 *   4. the hold-search mutants (`OrderMutants`), run through `accepts()` over each committed DAG:
 *      each changes a count, or is named EQUIVALENT with its measured reason and asserted to change
 *      nothing. The mutants touch only `accepts()`, and (1) pins the DAG, so this is the same as a
 *      `build(SDPCSPIN, mut)` without re-running the engine four times.
 *   5. the premise of enumerating a fresh bag: each node's parent (from `chainOf`) placed a whole
 *      7-bag, or the node is a root; `refused` is empty, by name.
 *   6. the partial-bag nodes (k < 7: the bag's first k placements) are named.
 *   7. a hand-checked tiny DAG fixture: verdicts traced by hand below.
 *
 * NOT CORPUS DATA, and the edges are one engine's (see the module header). Cold Clear's corroboration
 * of the edges is `route-orders-cc.test.ts`.
 *
 * Run: bun test pipeline/openers/route-orders.test.ts   (about twenty seconds)
 */
import { test, expect } from 'bun:test';
import { readFileSync } from 'node:fs';
import { build, serialise, accepts, allOrders, conditionOn, bitsHex, type OrderMutants } from '../sim/route-orders.ts';
import { chainOf, demoNodes, demoProfile } from '../sim/route-demos.ts';
import { loadRoutes } from '../sim/route-facts.ts';
import { SDPCSPIN } from '../sim/route-profile-sdpcspin.ts';

const PATH = `${import.meta.dir}/../../analysis/sdpcspin-orders.json`;
const TEXT = readFileSync(PATH, 'utf8');
const A = JSON.parse(TEXT);
const ORDERS = allOrders();
/** The artefact's node carries `k`, not `full`; `accepts()` needs the full set. */
const dagOf = (n: any) => ({ groups: n.groups, edges: n.edges, full: (1 << n.k) - 1, full_ok: n.full_ok });

function decode(hex: string): boolean[] {
  const bytes = Buffer.from(hex, 'hex');
  expect(bytes.length).toBe(Math.ceil(ORDERS.length / 8));
  return ORDERS.map((_, j) => ((bytes[j >> 3]! >> (j & 7)) & 1) === 1);
}

/** Nodes whose drawing has fewer than seven groups: the bag's first k placements. */
const PARTIAL_BAG: Record<string, number> = {
  'bag1.lj.left': 6, 'bag1.jl.left': 6,                // the derived stage boards, the T still to come
  '3.second.alt#1': 6, '3.second.alt#2': 6,            // the alternate fourth bags, the saved I unplaced
  '3.first.cave.stsd.next': 2, '3.first.trinity.tsd': 1, '3.first.trinity.tss': 3,
};
/** Nodes the orders build refuses (a parent leaving pieces unplaced): measured empty for SDPC Spin. */
const REFUSED: string[] = [];

test('1. byte rebuild: the committed artefact is build(SDPCSPIN)', () => {
  expect(serialise(build(SDPCSPIN))).toBe(TEXT);
}, 60_000);

test('2. accepted bits: popcount is the count, and empty == next per node (T4 on the data)', () => {
  expect(ORDERS.length).toBe(5040);
  expect(new Set(ORDERS).size).toBe(5040);
  for (const n of A.nodes) {
    // no SDPC Spin node carries a piece in from an earlier bag, so every node has the two modes
    expect(Object.keys(n.counts).sort()).toEqual(['empty', 'next']);
    expect(Object.keys(n.accepted).sort()).toEqual(['empty', 'next']);
    expect(n.groups.every((g: any) => !g.carried)).toBe(true);
    const e = decode(n.accepted.empty), x = decode(n.accepted.next);
    expect(e.filter(Boolean).length).toBe(n.counts.empty);
    expect(x.filter(Boolean).length).toBe(n.counts.next);
    expect(bitsHex(e)).toBe(n.accepted.empty);
    expect(e).toEqual(x);
    // and the bits are accepts() over the committed DAG, order by order
    const d = dagOf(n);
    expect(bitsHex(ORDERS.map(q => accepts(d, q, null)))).toBe(n.accepted.empty);
    expect(bitsHex(ORDERS.map(q => accepts(d, q.slice(1), q[0]!)))).toBe(n.accepted.next);
  }
});

test('3. condition tables recomputed from the bits with conditionOn()', () => {
  const conditioned: string[] = [];
  for (const n of A.nodes) {
    if (!n.condition) continue;
    conditioned.push(n.node);
    const bits = decode(n.accepted.empty);
    const sat = ORDERS.map(q => conditionOn(n.condition.condition, q));
    expect(sat.every(v => v !== null)).toBe(true);
    const c = (f: (a: boolean, s: boolean) => boolean) => bits.filter((a, j) => f(a, sat[j]!)).length;
    expect({ condition: n.condition.condition, stated: sat.filter(Boolean).length,
             built_and_stated: c((a, s) => a && s), built_not_stated: c((a, s) => a && !s),
             stated_not_built: c((a, s) => !a && s) }).toEqual(n.condition);
  }
  expect(conditioned).toEqual(CONDITIONED);
});

/** Nodes carrying an order condition the count tests (bag-1 conditions excluded, as build() does). */
const CONDITIONED = ['3.third', '3.first.cave', '3.second.cspin.o_first#1', '3.second.cspin.o_first#2',
  '3.second.cspin.l_first#1', '3.second.cspin.l_first#2', '3.second.cspin.l_first#3', '3.second.cspin.l_first#4'];

/** Per mutant: the nodes whose (empty, next) counts change, measured. */
const MUTANT_CHANGES: Record<keyof OrderMutants, number> = {
  noSwap: 32,       // every node: the held piece can never come out
  noHoldFirst: 32,  // every node's EMPTY count falls to the in-order orders; NEXT is untouched (T4 broken)
  placeStar: 0,     // EQUIVALENT, see below
  noStar: 25,       // every k = 7 node; the seven k < 7 nodes never reach the next bag's piece
};
/** Mutants that change nothing on this data, and why (measured). */
const EQUIVALENT: Partial<Record<keyof OrderMutants, string>> = {
  placeStar: "equivalent on this data, measured (0 of 32 nodes move), and independently measured by "
    + "spec/route_orders_data.py --mutants: '*' is reached only once every dealt piece is placed or held, "
    + 'so at most one group is unplaced, and placing \'*\' as it uses the same edge as the swap or the plain '
    + 'placement. spec/RouteOrders.dfy still kills the mutant at the proof level.',
};

test('4. each hold mutant changes a count, or is named equivalent', () => {
  for (const key of Object.keys(MUTANT_CHANGES) as (keyof OrderMutants)[]) {
    const mut: OrderMutants = { [key]: true };
    const changed: string[] = [];
    let emptyNe = 0;
    for (const n of A.nodes) {
      const d = dagOf(n);
      const e = ORDERS.filter(q => accepts(d, q, null, mut)).length;
      const x = ORDERS.filter(q => accepts(d, q.slice(1), q[0]!, mut)).length;
      if (e !== n.counts.empty || x !== n.counts.next) changed.push(n.node);
      if (e !== x) emptyNe++;
      if (key === 'noHoldFirst') {
        expect(x).toBe(n.counts.next);               // the next-held mode never takes case (c) first
        expect(e).toBeLessThan(n.counts.empty);
      }
      if (key === 'noStar') expect(changed.includes(n.node)).toBe(n.k === 7);
    }
    expect(changed.length).toBe(MUTANT_CHANGES[key]);
    if (key in EQUIVALENT) expect(changed).toEqual([]);
    else expect(changed.length).toBeGreaterThan(0);
    // dropping case (c) makes T4 false on every node
    if (key === 'noHoldFirst') expect(emptyNe).toBe(A.nodes.length);
  }
});

test('5. premise: each parent placed a whole 7-bag or the node is a root; refused is empty', () => {
  expect(A.refused.map((r: any) => r.node)).toEqual(REFUSED);
  const routes = loadRoutes(SDPCSPIN.routesPath);
  const DP = demoProfile(SDPCSPIN);
  const ids = demoNodes(SDPCSPIN, routes).map(n => n.id).filter(id => !REFUSED.includes(id));
  expect(A.nodes.map((n: any) => n.node)).toEqual(ids);
  const byId = new Map<string, any>(A.nodes.map((n: any) => [n.node, n]));
  const byRoute = new Map(routes.nodes.map(n => [n.id, n]));
  const roots: string[] = [];
  for (const n of A.nodes) {
    const chain = chainOf(byRoute.get(n.node)!, routes, SDPCSPIN.tag, DP.chainVia);
    const pn = chain.length > 1 ? chain[chain.length - 2]!.id : null;
    expect(n.parent).toBe(pn);
    if (pn === null) { roots.push(n.node); continue; }
    const parent = byId.get(pn);
    expect(parent).toBeDefined();
    expect(parent.k).toBe(7);
    expect(parent.groups.every((g: any) => !g.carried)).toBe(true);
  }
  expect(roots).toEqual(['bag1.lj.left', 'bag1.lj', 'bag1.jl.left', 'bag1.jl']);
});

test('6. the partial-bag nodes are named', () => {
  const partial = Object.fromEntries(A.nodes.filter((n: any) => n.k < 7).map((n: any) => [n.node, n.k]));
  expect(partial).toEqual(PARTIAL_BAG);
  for (const n of A.nodes) {
    expect(n.k).toBe(n.groups.length);
    expect(n.full_ok).toBe(true);
  }
});

// ── 7. hand-checked fixtures ─────────────────────────────────────────────────────────────────────
const G = (piece: string) => ({ letter: piece.toLowerCase(), piece, carried: false, spin_slot: false });
/** two groups, one edge order: S (group 0) then Z (group 1) */
const TWO = { groups: [G('S'), G('Z')], edges: [[0, 0], [1, 1]] as [number, number][], full: 3, full_ok: true };
/** seven groups, one edge order: I O T S Z J L, one edge per subset */
const SEVEN = { groups: [...'IOTSZJL'].map(G), full: 127, full_ok: true,
                edges: [0, 1, 2, 3, 4, 5, 6].map(i => [(1 << i) - 1, i] as [number, number]) };

test('7. hand-traced verdicts on two tiny DAGs', () => {
  // SZIOTJL, empty hold: place S (a), place Z (a). Needs no hold.
  expect(accepts(TWO, 'SZIOTJL', null)).toBe(true);
  expect(accepts(TWO, 'SZIOTJL', null, { noHoldFirst: true, noSwap: true, noStar: true })).toBe(true);
  // ZSIOTJL, empty hold: Z has no edge from {}; only case (c) moves — hold Z, place S; then swap Z out
  // for I and place Z. Without case (c) nothing can move at i = 0.
  expect(accepts(TWO, 'ZSIOTJL', null)).toBe(true);
  expect(accepts(TWO, 'ZSIOTJL', null, { noHoldFirst: true })).toBe(false);
  // ZISOTJL: hold Z needs I placed next (case c), and I is no group; Z cannot be placed first; and with
  // the hold empty nothing else moves. False by every rule.
  expect(accepts(TWO, 'ZISOTJL', null)).toBe(false);
  // T4 on the fixture: the next-held mode of ZSIOTJL is hold Z, stream SIOTJL
  expect(accepts(TWO, 'SIOTJL', 'Z')).toBe(true);
  expect(accepts(TWO, 'SIOTJL', 'Z', { noHoldFirst: true })).toBe(true);
  // a full DAG that is not full_ok accepts nothing
  expect(accepts({ ...TWO, full_ok: false }, 'SZIOTJL', null)).toBe(false);

  // SEVEN, OITSZJL from empty: O has no edge from {} -> case (c): hold O, place I (i = 2, h = O). Then at
  // every step the current piece is one ahead of the chain: swap — place O, hold T; place T, hold S;
  // place S, hold Z; place Z, hold J; place J, hold L; and at i = 7 the current token is the next
  // bag's '*': swap — place L, hold '*'. Full. Only the '*' swap places L.
  expect(accepts(SEVEN, 'OITSZJL', null)).toBe(true);
  expect(accepts(SEVEN, 'OITSZJL', null, { noStar: true })).toBe(false);
  expect(accepts(SEVEN, 'OITSZJL', null, { noSwap: true })).toBe(false);
  expect(accepts(SEVEN, 'OITSZJL', null, { noHoldFirst: true })).toBe(false);
  // in chain order nothing needs the hold
  expect(accepts(SEVEN, 'IOTSZJL', null, { noStar: true, noSwap: true, noHoldFirst: true })).toBe(true);
  // a piece two places early cannot be fixed with one hold slot: OTISZJL
  expect(accepts(SEVEN, 'OTISZJL', null)).toBe(false);
  // TIOSZJL: hold T, place I (c); O is current and placeable: place O (a), T still held; then S is current
  // and T's turn: swap — place T, hold S; and so on, the '*' swap placing L. A held piece may wait.
  expect(accepts(SEVEN, 'TIOSZJL', null)).toBe(true);
  expect(accepts(SEVEN, 'TIOSZJL', null, { noStar: true })).toBe(false);
  // Over all 5040 orders: MEASURED 64 (the list was read, every one is the chain with at most one hold
  // run), and the empty and next-held modes agree. A regression pin on the fixture, not a hand count.
  const n = ORDERS.filter(q => accepts(SEVEN, q, null)).length;
  const m = ORDERS.filter(q => accepts(SEVEN, q.slice(1), q[0]!)).length;
  expect(n).toBe(m);
  // TWO over all orders: 480 accepted (by hand: S0Z1, S0Z2, Z0S1 and xS1Z2, 4 x 120), 120 of them
  // (the orders that deal S then Z first) need no case (c).
  expect(ORDERS.filter(q => accepts(TWO, q, null)).length).toBe(480);
  expect(ORDERS.filter(q => accepts(TWO, q, null, { noHoldFirst: true })).length).toBe(120);
  expect(n).toBe(64);
});

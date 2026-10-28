/**
 * Cold Clear's corroboration of the route-order DAG (`analysis/sdpcspin-orders-cc.json`, from
 * `pipeline/sim/emit-route-orders-cc.ts --opener sdpcspin`).
 *
 *   1. against the committed orders artefact: the same nodes, every edge present exactly once and in
 *      order, classes valid, the inputs' md5s the orders artefact's own.
 *   2. per-class counts, and every `ours_only` edge pinned by NAME per class (never a bound): a new
 *      one is a red build to triage.
 *   3. only when the oracle binary exists: re-query cold-clear and require the artefact byte for byte.
 *      The binary is a nix build (`result/bin/cc-oracle`, or `$CC_ORACLE`); CI has it only in the
 *      aarch64-linux `oracle-image` job, so elsewhere this skips with the reason printed.
 *
 * Cold Clear corroborates CELLS, never spins: a corroborated T-spin edge says only that cold-clear can
 * rest the T on those cells.
 *
 * Run: bun test pipeline/openers/route-orders-cc.test.ts
 */
import { test, expect } from 'bun:test';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { build, serialise, HAVE_ORACLE, ORACLE } from '../sim/emit-route-orders-cc.ts';
import { SDPCSPIN } from '../sim/route-profile-sdpcspin.ts';
import { md5Files } from '../sim/route-facts.ts';

const ORDERS_TEXT = readFileSync(`${import.meta.dir}/../../analysis/sdpcspin-orders.json`, 'utf8');
const ORDERS = JSON.parse(ORDERS_TEXT);
const CC_TEXT = readFileSync(`${import.meta.dir}/../../analysis/sdpcspin-orders-cc.json`, 'utf8');
const CC = JSON.parse(CC_TEXT);

/** The ours_only edges, `node:subset,group`, per class, measured: eighteen O edges and four S edges
 *  that our engine reaches without a 180 and cold-clear does not (the cc ⊆ ours tuck asymmetry), and
 *  twelve S, Z and L edges whose only engine path uses a 180. None is an I, so no edge carries the
 *  `i_srs_plus` flag. All are under 3.third (asserted in test 2). */
const OURS_ONLY: Record<string, string[]> = {
  tuck: [
    ...[4, 5, 6, 7, 10, 11, 12, 13, 14, 15].map(s => `3.third.imperial:${s},4`),   // O
    ...[10, 11, 74, 75].map(s => `3.third.imperial.pc#2:${s},4`),                  // O
    ...[10, 11, 74, 75].map(s => `3.third.imperial.pc#3:${s},4`),                  // O
    ...[4, 5, 6, 7].map(s => `3.third.transition#1:${s},4`),                      // S
  ],
  '180': [
    '3.third.imperial.pc#1:26,5', '3.third.imperial.pc#1:27,5',                  // Z
    '3.third.imperial.pc#1:42,4', '3.third.imperial.pc#1:43,4',                  // S
    '3.third.imperial.pc#1:90,5', '3.third.imperial.pc#1:91,5',                  // Z
    '3.third.imperial.pc#1:106,4', '3.third.imperial.pc#1:107,4',                // S
    ...[98, 102, 106, 110].map(s => `3.third.imperial.pc#4:${s},4`),              // L
  ],
};
const I_SRS_PLUS: string[] = [];
const CORROBORATED = 3517;

test('1. the CC artefact covers the orders artefact edge for edge', () => {
  expect(CC.opener).toBe(ORDERS.opener);
  expect(CC.report_eligible).toBe(false);
  expect(CC.inputs.routes_md5).toBe(ORDERS.inputs.routes_md5);
  expect(CC.inputs.orders_md5).toBe(ORDERS.inputs.orders_md5);
  expect(CC.inputs.orders_artefact_md5).toBe(createHash('md5').update(ORDERS_TEXT).digest('hex'));
  expect(CC.oracle.nix_rev).toBe('279edd7');
  // Without the binary, test 3 skips, so an emitter edit must still make the artefact stale here.
  expect(CC.inputs.cc_emitter_md5).toBe(md5Files([`${import.meta.dir}/../sim/emit-route-orders-cc.ts`]));
  expect(CC.nodes.map((n: any) => n.node)).toEqual(ORDERS.nodes.map((n: any) => n.node));
  ORDERS.nodes.forEach((o: any, j: number) => {
    const c = CC.nodes[j];
    expect(c.edges.map((e: any[]) => [e[0], e[1]])).toEqual(o.edges);
    expect(new Set(c.edges.map((e: any[]) => `${e[0]},${e[1]}`)).size).toBe(o.edges.length);
    for (const e of c.edges) {
      if (e[2] === 'corroborated') { expect(e.length).toBe(3); continue; }
      expect(e[2]).toBe('ours_only');
      expect(['tuck', '180']).toContain(e[3]);
      const isI = o.groups[e[1]].piece === 'I';
      expect(e.length).toBe(isI ? 5 : 4);
      if (isI) expect(e[4]).toBe('i_srs_plus');
    }
  });
});

test('2. per-class counts and the ours_only edges by name', () => {
  const by: Record<string, string[]> = { tuck: [], '180': [] };
  const iFlag: string[] = [];
  let corroborated = 0;
  for (const n of CC.nodes) for (const e of n.edges) {
    if (e[2] === 'corroborated') { corroborated++; continue; }
    by[e[3]]!.push(`${n.node}:${e[0]},${e[1]}`);
    if (e[4] === 'i_srs_plus') iFlag.push(`${n.node}:${e[0]},${e[1]}`);
  }
  expect(by).toEqual(OURS_ONLY);
  expect(iFlag).toEqual(I_SRS_PLUS);
  expect(corroborated).toBe(CORROBORATED);
  // anti-vacuity: a coordinate flip corroborates nothing, so most edges must be corroborated
  const total = CC.nodes.reduce((a: number, n: any) => a + n.edges.length, 0);
  expect(total).toBe(ORDERS.nodes.reduce((a: number, n: any) => a + n.edges.length, 0));
  expect(corroborated / total).toBeGreaterThan(0.9);
});

test.skipIf(!HAVE_ORACLE)('3. re-query cold-clear: the artefact is what the oracle answers now', () => {
  expect(serialise(build(SDPCSPIN))).toBe(CC_TEXT);
}, 120_000);
if (!HAVE_ORACLE) console.log(`route-orders-cc: test 3 skipped — no cold-clear oracle at ${ORACLE} `
  + '(nix build .#cc-oracle, or set CC_ORACLE; in CI only the aarch64-linux oracle-image job has it)');

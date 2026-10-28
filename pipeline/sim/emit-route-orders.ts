/**
 * Emit an opener's route-order count: for each drawn node a demo builds, which of the 5040 dealt
 * orders a one-slot hold can build it from. All the work is in `route-orders.ts`; this file is argv
 * and file IO only.
 *
 *   bun pipeline/sim/emit-route-orders.ts --opener sdpcspin --out analysis/sdpcspin-orders.json
 */
import { writeFileSync } from 'node:fs';
import { build, serialise } from './route-orders.ts';
import { openerFromArgv } from './route-openers.ts';

if (import.meta.main) {
  const t0 = performance.now();
  const out = build(openerFromArgv(process.argv));
  const text = serialise(out);
  const ix = process.argv.indexOf('--out');
  if (ix > 0) writeFileSync(process.argv[ix + 1]!, text);
  else process.stdout.write(text);
  console.error(`nodes ${out.nodes.length}, refused ${out.refused.length}, ${text.length} bytes, `
    + `${((performance.now() - t0) / 1000).toFixed(1)} s`);
  for (const n of out.nodes) console.error(`  ${n.node.padEnd(28)} k=${n.k} subsets=${n.subsets} ${JSON.stringify(n.counts)}`
    + (n.condition ? ` cond stated=${n.condition.stated} built∧stated=${n.condition.built_and_stated} built∧¬stated=${n.condition.built_not_stated} stated∧¬built=${n.condition.stated_not_built}` : ''));
  for (const r of out.refused) console.error(`  refused ${r.node}: ${r.reason}`);
}

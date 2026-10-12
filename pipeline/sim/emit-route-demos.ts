/**
 * Emit an opener's constructed demo replays. All the work is in `route-demos.ts`; this file is argv
 * and file IO only. An opener whose profile has no `demos` half fails loudly.
 *
 *   bun pipeline/sim/emit-route-demos.ts --opener meisou --out analysis/stray-cannon-demos.json
 */
import { writeFileSync } from 'node:fs';
import { build, serialise } from './route-demos.ts';
import { openerFromArgv } from './route-openers.ts';

if (import.meta.main) {
  const t0 = performance.now();
  const out = build(openerFromArgv(process.argv));
  const text = serialise(out);
  const ix = process.argv.indexOf('--out');
  if (ix > 0) writeFileSync(process.argv[ix + 1]!, text);
  else process.stdout.write(text);
  console.error(`demos ${out.demos.length}, unbuilt ${out.unbuilt.length}, ${text.length} bytes, `
    + `${((performance.now() - t0) / 1000).toFixed(1)} s`);
  for (const u of out.unbuilt) console.error(`  unbuilt ${u.node}: ${u.reason}`);
}

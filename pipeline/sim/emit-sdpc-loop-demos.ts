/**
 * Emit the constructed SDPC loops. All the work is in `sdpc-loop-demos.ts`; this file is argv and file IO.
 *
 *   bun pipeline/sim/emit-sdpc-loop-demos.ts --out analysis/sdpc-loop-demos.json
 */
import { writeFileSync } from 'node:fs';
import { build, serialise } from './sdpc-loop-demos.ts';

if (import.meta.main) {
  const t0 = performance.now();
  const out = build();
  const text = serialise(out);
  const ix = process.argv.indexOf('--out');
  if (ix > 0) writeFileSync(process.argv[ix + 1]!, text);
  else process.stdout.write(text);
  console.error(`loops ${out.loops.length}, ${JSON.stringify(out.counts)}, ${text.length} bytes, `
    + `${((performance.now() - t0) / 1000).toFixed(1)} s`);
  for (const u of out.dpc_unbuilt) if (!u.same_as) console.error(`  unbuilt ${u.dpc}: ${u.reason}`);
}

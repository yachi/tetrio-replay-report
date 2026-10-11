/**
 * Emit `analysis/stray-cannon-demos.json`: the 迷走砲 constructed demo replays. All the work is in
 * `stray-cannon-demos.ts`; this file is argv and file IO only.
 *
 *   bun pipeline/sim/emit-stray-cannon-demos.ts --out analysis/stray-cannon-demos.json
 */
import { writeFileSync } from 'node:fs';
import { build, serialise } from './stray-cannon-demos.ts';

if (import.meta.main) {
  const t0 = performance.now();
  const out = build();
  const text = serialise(out);
  const ix = process.argv.indexOf('--out');
  if (ix > 0) writeFileSync(process.argv[ix + 1]!, text);
  else process.stdout.write(text);
  console.error(`demos ${out.demos.length}, unbuilt ${out.unbuilt.length}, ${text.length} bytes, `
    + `${((performance.now() - t0) / 1000).toFixed(1)} s`);
  for (const u of out.unbuilt) console.error(`  unbuilt ${u.node}: ${u.reason}`);
}

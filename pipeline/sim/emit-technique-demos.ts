/**
 * Emit a mid-game technique's constructed demo replays. All the work is in `technique-demos.ts`;
 * this file is argv and file IO only. Emit AFTER the corpus artefact: the demos hash the matcher.
 *
 *   bun pipeline/sim/emit-technique-demos.ts --technique stsd --out analysis/stsd-demos.json
 */
import { writeFileSync } from 'node:fs';
import { build, serialise } from './technique-demos.ts';
import { techniqueFromArgv, TECHNIQUE_DEMOS } from './techniques.ts';

if (import.meta.main) {
  const t0 = performance.now();
  const P = techniqueFromArgv(process.argv);
  const DP = TECHNIQUE_DEMOS[P.key];
  if (!DP) throw new Error(`${P.key} has no demo profile`);
  const out = build(P, DP);
  const text = serialise(out);
  const ix = process.argv.indexOf('--out');
  if (ix > 0) writeFileSync(process.argv[ix + 1]!, text);
  else process.stdout.write(text);
  console.error(`demos ${out.demos.length}, unbuilt ${out.unbuilt.length}, ${text.length} bytes, `
    + `${((performance.now() - t0) / 1000).toFixed(1)} s`);
  for (const u of out.unbuilt) console.error(`  unbuilt ${u.node}: ${u.reason}`);
}

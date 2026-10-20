/**
 * Emit a mid-game technique's own-design search (`technique-own.ts`). This file is argv and file IO only.
 *
 *   bun pipeline/sim/emit-technique-own.ts --technique cutcopy --out analysis/cutcopy-own.json
 */
import { writeFileSync } from 'node:fs';
import { build, serialise } from './technique-own.ts';
import { techniqueFromArgv, TECHNIQUE_DEMOS, TECHNIQUE_OWN } from './techniques.ts';

if (import.meta.main) {
  const t0 = performance.now();
  const P = techniqueFromArgv(process.argv);
  const DP = TECHNIQUE_DEMOS[P.key], OP = TECHNIQUE_OWN[P.key];
  if (!DP || !OP) throw new Error(`${P.key} has no own-design profile`);
  const out = build(P, DP, OP);
  const text = serialise(out);
  const ix = process.argv.indexOf('--out');
  if (ix > 0) writeFileSync(process.argv[ix + 1]!, text);
  else process.stdout.write(text);
  console.error(`boards ${out.boards.length}, ${text.length} bytes, ${((performance.now() - t0) / 1000).toFixed(1)} s`);
  for (const o of out.search.per_offset) console.error(`  offset ${o.offset}: ${o.candidates} candidates, ${JSON.stringify(o.outcomes)}`);
}

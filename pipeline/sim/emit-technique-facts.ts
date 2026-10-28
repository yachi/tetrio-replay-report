/**
 * Emit a mid-game technique's corpus artefact: every scored T-spin at which the technique page's
 * local shape stood. All the work is in `technique-facts.ts`; this file is argv and file IO only.
 *
 *   bun pipeline/sim/emit-technique-facts.ts --technique stsd --out analysis/stsd-facts.json
 */
import { writeFileSync } from 'node:fs';
import { build, serialise } from './technique-facts.ts';
import { techniqueFromArgv } from './techniques.ts';

if (import.meta.main) {
  const P = techniqueFromArgv(process.argv);
  const text = serialise(build(P));
  const ix = process.argv.indexOf('--out');
  if (ix > 0) writeFileSync(process.argv[ix + 1]!, text);
  else process.stdout.write(text);
}

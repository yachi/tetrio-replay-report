/**
 * Emit the DPC corpus artefact. All the work is in `dpc-facts.ts`; this file is argv and file IO only.
 *
 *   bun pipeline/sim/emit-dpc-facts.ts --out analysis/dpc-facts.json
 */
import { writeFileSync } from 'node:fs';
import { build, serialise } from './dpc-facts.ts';

if (import.meta.main) {
  const text = serialise(build());
  const ix = process.argv.indexOf('--out');
  if (ix > 0) writeFileSync(process.argv[ix + 1]!, text);
  else process.stdout.write(text);
}

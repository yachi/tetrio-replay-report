/**
 * Emit the Second PC corpus artefact. All the work is in `secondpc-facts.ts`; this file is argv and file IO only.
 *
 *   bun pipeline/sim/emit-secondpc-facts.ts --out analysis/secondpc-facts.json
 */
import { writeFileSync } from 'node:fs';
import { build, serialise } from './secondpc-facts.ts';

if (import.meta.main) {
  const text = serialise(build());
  const ix = process.argv.indexOf('--out');
  if (ix > 0) writeFileSync(process.argv[ix + 1]!, text);
  else process.stdout.write(text);
}

/**
 * Emit 千鳥格子練習場's drills (`cutcopy-drills.ts`). This file is argv and file IO only.
 *
 *   bun pipeline/sim/emit-cutcopy-drills.ts --out analysis/cutcopy-drills.json
 */
import { writeFileSync } from 'node:fs';
import { build, serialise } from './cutcopy-drills.ts';

if (import.meta.main) {
  const t0 = performance.now();
  const out = build();
  const text = serialise(out);
  const ix = process.argv.indexOf('--out');
  if (ix > 0) writeFileSync(process.argv[ix + 1]!, text);
  else process.stdout.write(text);
  console.error(`drills ${out.drills.length}, dropped ${out.dropped.length}, ${text.length} bytes, ${((performance.now() - t0) / 1000).toFixed(1)} s`);
  for (const d of out.drills) console.error(`  ${d.id} need ${d.need} ${d.difficulty.label} (min ${d.difficulty.min}) second ${d.second}`);
  for (const d of out.dropped) console.error(`  dropped ${d.id}: ${d.reason} ${d.detail ?? ''}`);
}

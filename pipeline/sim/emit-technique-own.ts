/**
 * Emit a mid-game technique's own-design search (`technique-own.ts`). This file is argv, process and file IO only.
 *
 *   bun pipeline/sim/emit-technique-own.ts --technique cutcopy --out analysis/cutcopy-own.json
 *
 * Each offset is searched in its own child process (`--part <offset>`, which prints that offset's part as JSON),
 * and the parts are assembled in the profile's offset order, so the bytes written do not depend on which child
 * finished first. OWN_PROGRESS=1 prints each child's progress.
 */
import { writeFileSync } from 'node:fs';
import { assemble, searchOffset, serialise } from './technique-own.ts';
import { techniqueFromArgv, TECHNIQUE_DEMOS, TECHNIQUE_OWN } from './techniques.ts';

if (import.meta.main) {
  const t0 = performance.now();
  const P = techniqueFromArgv(process.argv);
  const DP = TECHNIQUE_DEMOS[P.key], OP = TECHNIQUE_OWN[P.key];
  if (!DP || !OP) throw new Error(`${P.key} has no own-design profile`);
  const pi = process.argv.indexOf('--part');
  if (pi > 0) {
    process.stdout.write(JSON.stringify(searchOffset(P, DP, OP, Number(process.argv[pi + 1]))));
  } else {
    const parts = await Promise.all(OP.offsets.map(async off => {
      const child = Bun.spawn(['bun', import.meta.path, '--technique', P.key, '--part', String(off)],
                              { stdout: 'pipe', stderr: 'inherit' });
      const text = await new Response(child.stdout).text();
      if (await child.exited !== 0) throw new Error(`own search: offset ${off} failed`);
      return JSON.parse(text);
    }));
    const out = assemble(P, DP, OP, parts);
    const text = serialise(out);
    const ix = process.argv.indexOf('--out');
    if (ix > 0) writeFileSync(process.argv[ix + 1]!, text);
    else process.stdout.write(text);
    console.error(`boards ${out.boards.length}, ${text.length} bytes, ${((performance.now() - t0) / 1000).toFixed(1)} s`);
    for (const o of out.search.per_offset)
      console.error(`  offset ${o.offset}: ${o.candidates} candidates, ${o.tried} tried, ${JSON.stringify(o.outcomes)}`);
  }
}

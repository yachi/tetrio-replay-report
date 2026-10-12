/**
 * Emit an opener's route artefact: the deepest node of its shiwehi.com route tree each corpus round
 * reaches. All the work is in `route-facts.ts`; this file is argv and file IO only.
 *
 *   bun pipeline/sim/emit-route-facts.ts --opener honeycup --out analysis/honey-cup-facts.json
 *   bun pipeline/sim/emit-route-facts.ts --opener meisou --out analysis/stray-cannon-facts.json
 *
 * It is はちみつ砲's entry file (hashed into that artefact's `emitter_md5`); 迷走砲 keeps its own
 * entry, `emit-stray-cannon-facts.ts`, and either command produces the same 迷走砲 bytes.
 */
import { writeFileSync } from 'node:fs';
import { build, serialise } from './route-facts.ts';
import { openerFromArgv } from './route-openers.ts';

if (import.meta.main) {
  const P = openerFromArgv(process.argv);
  const text = serialise(build(P));
  const ix = process.argv.indexOf('--out');
  if (ix > 0) writeFileSync(process.argv[ix + 1]!, text);
  else process.stdout.write(text);
}

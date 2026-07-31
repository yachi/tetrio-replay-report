import { readFileSync } from 'node:fs';
import { makeQueue } from './sim.ts';
const d = JSON.parse(readFileSync(`${import.meta.dir}/../replay-2026-07-22-2.ttrm`,'utf8'));
const rnd = d.replay.rounds[4];
for (const p of rnd) {
  const seed = p.replay.options.seed;
  console.log(p.username, 'seed', seed, 'holds', p.replay.results.stats.holds);
  console.log('  queue:', makeQueue(seed, 24).join(''));
  const hd = p.replay.events.filter((e:any)=>e.type==='keydown'&&e.data.key==='hardDrop').map((e:any)=>e.frame);
  const ho = p.replay.events.filter((e:any)=>e.type==='keydown'&&e.data.key==='hold').map((e:any)=>e.frame);
  console.log('  hardDrops', hd.length, hd.slice(0,14).join(','));
  console.log('  holds    ', ho.length, ho.slice(0,14).join(','));
}

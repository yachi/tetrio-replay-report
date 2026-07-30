/**
 * Is "7 sim perfect clears vs 19 real" a bug, or a denominator artefact?
 *
 * pc.ts compares the sim's WHOLE-ROUND allclear count against results.stats.clears.allclear,
 * also whole-round. But the sim is only trustworthy on a verified PREFIX (13.8% of placements
 * overall; median reach ~41% of a round's pieces). Comparing a prefix-accurate simulator to a
 * whole-round oracle counts every PC the sim never got the chance to see as a miss.
 *
 * Two things decide whether a real gap remains:
 *   (a) how much of each round the sim actually covers, and
 *   (b) WHERE in a round perfect clears happen. If they cluster in the opener — which is where
 *       the sim IS verified — then coverage cannot excuse the miss and the gap is real.
 * (b) is the load-bearing one, and it is measurable from the sim's own PC lock indices.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';

const DIR = (process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);
const opts = { garbagespeed: 30, garbagecap: 8, locktime: 30, gravity: 0.02, sdfMode: 'abs' as const,
               insertMode: 'onPlace' as const, cancelMode: 'all' as const };

let simPC = 0, realPC = 0, tot = 0, spurious = 0;
const rows: { file: string; rnd: number; who: string; simPC: number; realPC: number;
              simPieces: number; realPieces: number; verified: number; pcAt: number[] }[] = [];

for (const f of readdirSync(DIR).filter(x => x.endsWith('.ttrm')).sort()) {
  const d = JSON.parse(readFileSync(`${DIR}/${f}`, 'utf8'));
  d.replay.rounds.forEach((rnd: any, ri: number) => {
    if (rnd.length !== 2) return;
    const P = rnd.map((p: any) => ({ p, rp: p.replay, gameid: p.replay.options.gameid }));
    for (const [me, other] of [[P[0], P[1]], [P[1], P[0]]] as any[]) {
      const ev = me.rp.events.filter((e: any) => e.type === 'keydown' || e.type === 'keyup')
        .map((e: any) => ({ frame: e.frame, sub: e.data.subframe ?? 0, type: e.type, key: e.data.key }));
      const gin = me.rp.events.filter((e: any) => e.type === 'ige' && e.data.type === 'interaction' && e.data.data?.type === 'garbage')
        .map((e: any) => ({ frame: e.frame, amt: e.data.data.amt, x: e.data.data.x, size: e.data.data.size }));
      const truth = other.rp.events.filter((e: any) => e.type === 'ige' && e.data.type === 'interaction'
        && e.data.data?.type === 'garbage' && e.data.data.gameid === me.gameid)
        .map((e: any) => ({ frame: e.data.data.frame ?? e.frame, amt: e.data.data.amt }))
        .sort((a: any, b: any) => a.frame - b.frame);

      const r = simulate(ev, gin, me.rp.options.handling, me.rp.options.seed, me.rp.frames, DEFAULT_TABLE, opts);

      // verified prefix, same construction the forecast metric uses
      const mine = r.records.filter(x => x.sent > 0);
      let vf = -1;
      for (let i = 0; i < Math.min(mine.length, truth.length); i++) {
        if (Math.abs(mine[i]!.frame - truth[i]!.frame) <= 25 && mine[i]!.sent === truth[i]!.amt) vf = mine[i]!.frame; else break;
      }
      let vIdx = -1;
      for (let i = 0; i < r.locks.length; i++) if (r.locks[i]!.frame <= vf) vIdx = i;

      const pcAt = r.locks.map((l, i) => ({ l, i })).filter(x => (x.l as any).allclear).map(x => x.i);
      const rp = me.rp.results.stats.clears.allclear ?? 0;
      simPC += r.clears.allclear; realPC += rp; tot++;
      if (r.clears.allclear > rp) spurious++;
      rows.push({ file: f, rnd: ri, who: me.p.username, simPC: r.clears.allclear, realPC: rp,
                  simPieces: r.locks.length, realPieces: me.rp.results.stats.piecesplaced, verified: vIdx + 1, pcAt });
    }
  });
}

console.log(`player-rounds: ${tot}`);
console.log(`  sim perfect clears  : ${simPC}`);
console.log(`  real perfect clears : ${realPC}`);
console.log(`  rounds where the sim INVENTS one : ${spurious}\n`);

const frac = rows.map(r => r.realPieces ? r.simPieces / r.realPieces : 0).sort((a, b) => a - b);
const vfrac = rows.map(r => r.realPieces ? r.verified / r.realPieces : 0).sort((a, b) => a - b);
const med = (a: number[]) => a[Math.floor(a.length / 2)]!;
console.log(`sim reach   : median ${(100 * med(frac)).toFixed(0)}% of a round's real pieces`);
console.log(`verified    : median ${(100 * med(vfrac)).toFixed(0)}% of a round's real pieces`);
const totalReal = rows.reduce((s, r) => s + r.realPieces, 0);
const totalVer = rows.reduce((s, r) => s + r.verified, 0);
console.log(`pooled verified coverage: ${totalVer}/${totalReal} = ${(100 * totalVer / totalReal).toFixed(1)}%\n`);

// Where do perfect clears sit in a round? Use the sim's own PC lock indices.
const all = rows.flatMap(r => r.pcAt);
console.log(`sim PC lock indices (0-based piece number within the round):`);
console.log(`  ${all.sort((a, b) => a - b).join(', ')}`);
console.log(`  -> ${all.filter(i => i < 12).length}/${all.length} occur within the first 12 pieces\n`);

// Rounds where a real PC happened. How much of those rounds did the sim verify?
const withReal = rows.filter(r => r.realPC > 0);
console.log(`player-rounds containing a real PC: ${withReal.length} (holding ${withReal.reduce((s, r) => s + r.realPC, 0)} PCs)`);
console.log(`  of those, sim verified median ${(100 * med(withReal.map(r => r.realPieces ? r.verified / r.realPieces : 0).sort((a, b) => a - b))).toFixed(0)}% of the round`);
console.log(`  sim found ${withReal.reduce((s, r) => s + r.simPC, 0)} PCs in exactly those rounds\n`);

console.log('per-round detail where real PCs happened (sim/real, verified pieces / real pieces):');
for (const r of withReal.sort((a, b) => b.realPC - a.realPC))
  console.log(`  ${r.file.slice(-9).padEnd(10)} r${String(r.rnd).padStart(2)} ${r.who.padEnd(9)} PC ${r.simPC}/${r.realPC}   verified ${String(r.verified).padStart(3)}/${String(r.realPieces).padStart(3)} pieces (${(100 * r.verified / r.realPieces).toFixed(0)}%)  simReached ${r.simPieces}`);

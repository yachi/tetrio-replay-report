/**
 * Dump one player-round in detail: every sim lock (piece, cells, cleared, spin, attack)
 * beside the ground-truth attack stream, so the first real divergence is visible rather
 * than inferred. Usage: FILE=replay-...ttrm ROUND=0 USER=yachi bun run inspect-round.ts
 */
import { readFileSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
import { replayDir } from './verified-prefix.ts';
const DIR = replayDir();
const FILE = process.env.FILE!, ROUND = Number(process.env.ROUND ?? 0), USER = process.env.USER_!;
const opts = {garbagespeed:30, garbagecap:8, locktime:30, gravity:0.02, sdfMode:'abs' as const,
              insertMode:'onPlace' as const, cancelMode:'all' as const, acEmit:'separate' as const,
              subframe: process.env.SUBFRAME !== '0'};

const d = JSON.parse(readFileSync(`${DIR}/${FILE}`,'utf8'));
const rnd = d.replay.rounds[ROUND];
const me = rnd.find((p:any)=>p.username===USER), other = rnd.find((p:any)=>p.username!==USER);
const ev = me.replay.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
  .map((e:any)=>({frame:e.frame, sub:e.data.subframe??0, type:e.type, key:e.data.key}));
const gin = me.replay.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
  .map((e:any)=>({frame:e.frame, amt:e.data.data.amt, x:e.data.data.x, size:e.data.data.size}));
const truth = other.replay.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'
  && e.data.data?.type==='garbage' && e.data.data.gameid===me.replay.options.gameid)
  .map((e:any)=>({frame:e.data.data.frame??e.frame, amt:e.data.data.amt})).sort((a:any,b:any)=>a.frame-b.frame);

const r = simulate(ev, gin, me.replay.options.handling, me.replay.options.seed, me.replay.frames, DEFAULT_TABLE, opts);
const st = me.replay.results.stats;
console.log(`${FILE} round ${ROUND} ${USER}`);
console.log(`sim : placed ${r.placed} lines ${r.lines} topout ${r.topout}`);
console.log(`real: placed ${st.piecesplaced} lines ${st.lines}`);
console.log(`sim  clears:`, JSON.stringify(r.clears));
console.log(`real clears:`, JSON.stringify(st.clears));
console.log(`incoming garbage events:`, JSON.stringify(gin));
console.log(`truth outgoing attacks :`, JSON.stringify(truth));
console.log(`sim   outgoing attacks :`, JSON.stringify(r.records.filter(x=>x.sent>0).map(x=>({f:x.frame,amt:x.sent}))));
console.log(`\nsim locks that cleared anything, and every lock near the first truth attack:`);
const firstTruth = truth[0]?.frame ?? Infinity;
for (let i=0;i<r.locks.length;i++) {
  const l = r.locks[i]!;
  const near = Math.abs(l.frame-firstTruth) < 300;
  if (l.cleared>0 || near)
    console.log(`  #${String(i).padStart(3)} f${String(l.frame).padStart(5)} ${l.piece} cleared=${l.cleared} spin=${l.spin}${l.allclear?' PC':''}${l.cleared>0?'':''}`);
}
console.log(`\ngarbage insertions:`, JSON.stringify(r.garbageEvents));

const AT = process.env.AT ? Number(process.env.AT) : -1;
if (AT >= 0) {
  const b = r.boards[AT];
  console.log(`\nboard after lock #${AT} (piece ${r.locks[AT]?.piece}, frame ${r.locks[AT]?.frame}):`);
  if (b) for (let y=0;y<b.length;y++) {
    if (b[y].every((c:any)=>c===null)) continue;
    console.log(`  ${String(y).padStart(2)} |${b[y].map((c:any)=>c===null?'.':c==='G'?'#':c).join('')}|`);
  }
  console.log(`  cells of that lock:`, JSON.stringify(r.locks[AT]?.cells));
}

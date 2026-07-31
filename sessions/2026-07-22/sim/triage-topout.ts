/**
 * Why does the sim top out in 151/158 rounds?
 *
 * Two candidate causes, measured against ground truth rather than argued:
 *   (A) the sim inserts MORE garbage than the client did  -> board is buried
 *   (B) the block-out predicate is too strict             -> sim dies on a board
 *       the client survived (halp1/triangle's #considerBlockout shifts a blocked
 *       spawn UP through the buffer when the previous placement cleared lines;
 *       sim.ts has no such rule -- see ab-insertafterclear.ts for the ordering A/B)
 *
 * Discriminator: at the moment of top-out, report the sim's cumulative received
 * garbage vs the player's final stats.garbage.received, and the stack height.
 * If (A), sim-received >> real-received well before death. If (B), sim-received
 * tracks real and the stack is merely tall.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE, SPAWN_ROW } from './sim.ts';
const DIR = (process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);
const opts = {garbagespeed:30, garbagecap:8, locktime:30, gravity:0.02, sdfMode:'abs' as const,
               insertMode:'onPlace' as const, cancelMode:'all' as const, acEmit:'separate' as const};

type Row = { file:string; user:string; topout:boolean; placed:number; realPlaced:number;
             simRecv:number; realRecv:number; simSent:number; realSent:number;
             simLines:number; realLines:number; height:number };
const rows: Row[] = [];

for (const f of readdirSync(DIR).filter(x=>x.endsWith('.ttrm')).sort()) {
  const d = JSON.parse(readFileSync(`${DIR}/${f}`,'utf8'));
  for (const rnd of d.replay.rounds) { if (rnd.length!==2) continue;
    for (const me of rnd) {
      const rp = me.replay;
      const ev = rp.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
        .map((e:any)=>({frame:e.frame, sub:e.data.subframe??0, type:e.type, key:e.data.key}));
      const gin = rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
        .map((e:any)=>({frame:e.frame, amt:e.data.data.amt, x:e.data.data.x, size:e.data.data.size}));
      const r = simulate(ev, gin, rp.options.handling, rp.options.seed, rp.frames, DEFAULT_TABLE, opts);
      const st = rp.results.stats;
      // stack height at the end: topmost non-empty row, expressed as rows above the floor
      const board = r.boards[r.boards.length-1] ?? [];
      let top = board.length;
      for (let y=0; y<board.length; y++) if (board[y].some((c:any)=>c!==null)) { top=y; break; }
      rows.push({file:f, user:me.username, topout:r.topout, placed:r.placed, realPlaced:st.piecesplaced,
                 simRecv:r.garbage.received, realRecv:st.garbage.received ?? 0,
                 simSent:r.garbage.sent, realSent:st.garbage.sent ?? 0,
                 simLines:r.lines, realLines:st.lines, height: board.length - top});
    }}}

const sum = (f:(r:Row)=>number) => rows.reduce((a,r)=>a+f(r),0);
const med = (f:(r:Row)=>number) => { const v=rows.map(f).sort((a,b)=>a-b); return v[Math.floor(v.length/2)]!; };
const to = rows.filter(r=>r.topout);

console.log(`rounds ${rows.length}  topout ${to.length}`);
console.log(`garbage received  sim ${sum(r=>r.simRecv)}  real ${sum(r=>r.realRecv)}  ratio ${(sum(r=>r.simRecv)/sum(r=>r.realRecv)).toFixed(2)}`);
console.log(`garbage sent      sim ${sum(r=>r.simSent)}  real ${sum(r=>r.realSent)}  ratio ${(sum(r=>r.simSent)/sum(r=>r.realSent)).toFixed(2)}`);
console.log(`pieces placed     sim ${sum(r=>r.placed)}  real ${sum(r=>r.realPlaced)}  medFrac ${med(r=>r.placed/r.realPlaced).toFixed(3)}`);
console.log(`lines             sim ${sum(r=>r.simLines)}  real ${sum(r=>r.realLines)}`);
console.log(`\nAt death: median stack height ${med(r=>r.height)} rows (spawn row ${SPAWN_ROW} of ${rows[0]!.height >= 0 ? 40 : 40}; block-out needs height >= ${40-SPAWN_ROW})`);

// The discriminator: how much garbage had the sim eaten by the time it died,
// relative to everything the client ate over the WHOLE round?
const over = rows.filter(r=>r.simRecv > r.realRecv).length;
const under = rows.filter(r=>r.simRecv < r.realRecv).length;
console.log(`sim received MORE than the client did (whole round): ${over}/${rows.length}`);
console.log(`sim received LESS: ${under}/${rows.length}`);
console.log(`median sim/real received ratio: ${med(r=> r.realRecv>0 ? r.simRecv/r.realRecv : 1).toFixed(2)}`);

console.log('\nworst 12 by received-ratio:');
for (const r of [...rows].filter(r=>r.realRecv>0).sort((a,b)=>b.simRecv/b.realRecv - a.simRecv/a.realRecv).slice(0,12))
  console.log(`  ${r.file.padEnd(28)} ${r.user.padEnd(12)} recv ${String(r.simRecv).padStart(4)}/${String(r.realRecv).padStart(4)}  pieces ${String(r.placed).padStart(4)}/${String(r.realPlaced).padStart(4)}  lines ${String(r.simLines).padStart(3)}/${String(r.realLines).padStart(3)}  h${r.height}`);

/**
 * A/B: is the block-out predicate why the sim tops out in 151/158 rounds?
 *
 * strict  — current behaviour: spawn overlaps a block => dead.
 * clutch  — halp1/triangle #considerBlockout: walk the piece up through the buffer
 *           until it fits, but only if the previous placement cleared lines.
 * shiftup — same walk, ungated.
 *
 * Gate on verified-prefix coverage against the opponent's ige stream, not on
 * survival: surviving longer is worthless if the extra pieces land wrong.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
import { replayDir } from './verified-prefix.ts';
const DIR = replayDir();
const base = {garbagespeed:30, garbagecap:8, locktime:30, gravity:0.02, sdfMode:'abs' as const,
              insertMode:'onPlace' as const, cancelMode:'all' as const, acEmit:'separate' as const};

for (const blockout of ['strict','clutch','shiftup'] as const) {
  let ver=0, real=0, tot=0, full=0, topouts=0, zero=0, simLines=0, realLines=0, simPC=0, realPC=0, placed=0;
  const ratios: number[] = [];
  for (const f of readdirSync(DIR).filter(x=>x.endsWith('.ttrm')).sort()) {
    const d = JSON.parse(readFileSync(`${DIR}/${f}`,'utf8'));
    for (const rnd of d.replay.rounds) { if (rnd.length!==2) continue;
      const P = rnd.map((p:any)=>({p, rp:p.replay, gameid:p.replay.options.gameid}));
      for (const [me,other] of [[P[0],P[1]],[P[1],P[0]]] as any[]) {
        const ev = me.rp.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
          .map((e:any)=>({frame:e.frame, sub:e.data.subframe??0, type:e.type, key:e.data.key}));
        const gin = me.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
          .map((e:any)=>({frame:e.frame, amt:e.data.data.amt, x:e.data.data.x, size:e.data.data.size}));
        const truth = other.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'
          && e.data.data?.type==='garbage' && e.data.data.gameid===me.gameid)
          .map((e:any)=>({frame:e.data.data.frame??e.frame, amt:e.data.data.amt}))
          .sort((a:any,b:any)=>a.frame-b.frame);
        const r = simulate(ev, gin, me.rp.options.handling, me.rp.options.seed, me.rp.frames,
                           DEFAULT_TABLE, {...base, blockout});
        const mine = r.records.filter(x=>x.sent>0);
        let vf=-1;
        for (let i=0;i<Math.min(mine.length,truth.length);i++) {
          if (Math.abs(mine[i]!.frame-truth[i]!.frame)<=25 && mine[i]!.sent===truth[i]!.amt) vf=mine[i]!.frame; else break;
        }
        let vIdx=-1; for (let i=0;i<r.locks.length;i++) if (r.locks[i]!.frame<=vf) vIdx=i;
        const st = me.rp.results.stats;
        ver += vIdx+1; real += st.piecesplaced; tot++; placed += r.placed;
        if (vIdx+1 >= st.piecesplaced) full++;
        if (r.topout) topouts++;
        if (r.lines === 0) zero++;
        simLines += r.lines; realLines += st.lines;
        if (st.lines > 0) ratios.push(r.lines/st.lines);
        simPC += r.clears.allclear; realPC += st.clears.allclear ?? 0;
      }}}
  ratios.sort((a,b)=>a-b);
  const med = ratios[Math.floor(ratios.length/2)] ?? 0;
  console.log(`${blockout.padEnd(8)} coverage ${(100*ver/real).toFixed(1)}%  full ${full}/${tot}  topout ${topouts}/${tot}  zero-line ${zero}/${tot}  pieces ${placed}/${real}  lines ${simLines}/${realLines}  medRatio ${med.toFixed(3)}  PC ${simPC}/${realPC}`);
}

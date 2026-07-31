/**
 * A/B: does inserting queued garbage on LINE-CLEARING placements too (after the
 * all-clear check) beat inserting only on no-clear placements?
 *
 * Motivated by halp1/triangle's engine core, where the PC predicate is read
 * immediately after clearLines and BEFORE insertGarbage — i.e. insertion is not
 * gated on "cleared no lines", it is gated on ordering. `insertAfterClear` was a
 * dead opt in sim.ts (declared, never set by any caller); this exercises it.
 *
 * Metrics: verified-prefix coverage (the real gate), plus top-out rate and the
 * sim/real line ratio, which is where the sim actually fails.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
const DIR = (process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);
const base = {garbagespeed:30, garbagecap:8, locktime:30, gravity:0.02, sdfMode:'abs' as const,
              insertMode:'onPlace' as const, cancelMode:'all' as const, acEmit:'separate' as const};

for (const iac of [false, true]) {
  let ver=0, real=0, tot=0, fullyVerified=0, topouts=0, zeroLine=0;
  let simLines=0, realLines=0, simPC=0, realPC=0;
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
                           DEFAULT_TABLE, {...base, insertAfterClear: iac});
        const mine = r.records.filter(x=>x.sent>0);
        let vf=-1;
        for (let i=0;i<Math.min(mine.length,truth.length);i++) {
          if (Math.abs(mine[i]!.frame-truth[i]!.frame)<=25 && mine[i]!.sent===truth[i]!.amt) vf=mine[i]!.frame; else break;
        }
        let vIdx=-1; for (let i=0;i<r.locks.length;i++) if (r.locks[i]!.frame<=vf) vIdx=i;
        const st = me.rp.results.stats;
        ver += vIdx+1; real += st.piecesplaced; tot++;
        if (vIdx+1 >= st.piecesplaced) fullyVerified++;
        if (r.topout) topouts++;
        if (r.lines === 0) zeroLine++;
        simLines += r.lines; realLines += st.lines;
        if (st.lines > 0) ratios.push(r.lines/st.lines);
        simPC += r.clears.allclear; realPC += st.clears.allclear ?? 0;
      }}}
  ratios.sort((a,b)=>a-b);
  const med = ratios[Math.floor(ratios.length/2)] ?? 0;
  console.log(`insertAfterClear=${String(iac).padEnd(5)} coverage ${ver}/${real} = ${(100*ver/real).toFixed(1)}%  full ${fullyVerified}/${tot}  topout ${topouts}/${tot}  zero-line ${zeroLine}/${tot}  lines ${simLines}/${realLines}  medRatio ${med.toFixed(3)}  PC ${simPC}/${realPC}`);
}

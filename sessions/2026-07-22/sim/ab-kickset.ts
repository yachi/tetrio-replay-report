/**
 * A/B: vanilla SRS vs TETR.IO's SRS+ I-piece kick order, and the +1 special bonus.
 *
 * SRS and SRS+ contain the same candidates for 0<->1, 0<->3, 1<->2, 2<->3; only the ORDER
 * differs, and the first legal candidate wins — so this only changes outcomes when two
 * candidates are both legal, which is the ambiguous well/overhang case.
 *
 * specialBonus is halp1/triangle's gSpecialBonus: +1 flat when a spin or quad clears
 * garbage. It is an engine OPTION there, and it measurably HURTS here, which is evidence
 * that it is disabled in these games. Kept off; recorded so it is not re-tried blind.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
const DIR = (process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);
const base = {garbagespeed:30, garbagecap:8, locktime:60, gravity:0.0167, sdfMode:'abs' as const,
              insertMode:'onPlace' as const, cancelMode:'all' as const, acEmit:'separate' as const,
              subframe:true, blockout:'shiftup' as const};
for (const [lbl, extra] of [
  ['SRS',                {kickset:'SRS' as const}],
  ['SRS+',               {kickset:'SRS+' as const}],
  ['SRS+ +specialBonus', {kickset:'SRS+' as const, specialBonus:true}],
] as const) {
  let ver=0, real=0, tot=0, topouts=0, zero=0, simLines=0, realLines=0, simPC=0, realPC=0, placed=0;
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
                           DEFAULT_TABLE, {...base, ...extra});
        const mine = r.records.filter(x=>x.sent>0);
        let vf=-1;
        for (let i=0;i<Math.min(mine.length,truth.length);i++) {
          if (Math.abs(mine[i]!.frame-truth[i]!.frame)<=25 && mine[i]!.sent===truth[i]!.amt) vf=mine[i]!.frame; else break;
        }
        let vIdx=-1; for (let i=0;i<r.locks.length;i++) if (r.locks[i]!.frame<=vf) vIdx=i;
        const st = me.rp.results.stats;
        ver += vIdx+1; real += st.piecesplaced; tot++; placed += r.placed;
        if (r.topout) topouts++;
        if (r.lines === 0) zero++;
        simLines += r.lines; realLines += st.lines;
        simPC += r.clears.allclear; realPC += st.clears.allclear ?? 0;
      }}}
  console.log(`${lbl.padEnd(18)} coverage ${(100*ver/real).toFixed(2)}%  topout ${topouts}/${tot}  zero-line ${zero}/${tot}  pieces ${placed}/${real}  lines ${simLines}/${realLines}  PC ${simPC}/${realPC}`);
}

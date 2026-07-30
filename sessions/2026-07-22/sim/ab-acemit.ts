/** A/B: does emitting the all-clear bonus as its own event extend the verified prefix? */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
const DIR=(process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);
const base={garbagespeed:30,garbagecap:8,locktime:30,gravity:0.02,sdfMode:'abs' as const,
            insertMode:'onPlace' as const,cancelMode:'all' as const};
for(const mode of ['combined','separate'] as const){
  let ver=0, real=0, pcRoundsVer=0, pcRoundsTot=0, fullyVerified=0, tot=0;
  for(const f of readdirSync(DIR).filter(x=>x.endsWith('.ttrm')).sort()){
    const d=JSON.parse(readFileSync(`${DIR}/${f}`,'utf8'));
    for(const rnd of d.replay.rounds){ if(rnd.length!==2) continue;
      const P=rnd.map((p:any)=>({p,rp:p.replay,gameid:p.replay.options.gameid}));
      for(const [me,other] of [[P[0],P[1]],[P[1],P[0]]] as any[]){
        const ev=me.rp.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
          .map((e:any)=>({frame:e.frame,sub:e.data.subframe??0,type:e.type,key:e.data.key}));
        const gin=me.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
          .map((e:any)=>({frame:e.frame,amt:e.data.data.amt,x:e.data.data.x,size:e.data.data.size}));
        const truth=other.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'
          &&e.data.data?.type==='garbage'&&e.data.data.gameid===me.gameid)
          .map((e:any)=>({frame:e.data.data.frame??e.frame,amt:e.data.data.amt})).sort((a:any,b:any)=>a.frame-b.frame);
        const r=simulate(ev,gin,me.rp.options.handling,me.rp.options.seed,me.rp.frames,DEFAULT_TABLE,{...base,acEmit:mode});
        const mine=r.records.filter(x=>x.sent>0);
        let vf=-1; for(let i=0;i<Math.min(mine.length,truth.length);i++){
          if(Math.abs(mine[i]!.frame-truth[i]!.frame)<=25&&mine[i]!.sent===truth[i]!.amt) vf=mine[i]!.frame; else break; }
        let vIdx=-1; for(let i=0;i<r.locks.length;i++) if(r.locks[i]!.frame<=vf) vIdx=i;
        ver+=vIdx+1; real+=me.rp.results.stats.piecesplaced; tot++;
        if(vIdx+1>=me.rp.results.stats.piecesplaced) fullyVerified++;
        if((me.rp.results.stats.clears.allclear??0)>0){ pcRoundsTot++; if(vIdx+1>0) pcRoundsVer++; }
      }}}
  console.log(`${mode.padEnd(9)} pooled verified ${ver}/${real} = ${(100*ver/real).toFixed(1)}%   PC-rounds with any verified prefix: ${pcRoundsVer}/${pcRoundsTot}   fully verified rounds: ${fullyVerified}/${tot}`);
}

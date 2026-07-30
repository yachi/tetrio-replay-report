const STRICT = process.env.LOOSE !== '1';
/** Does forecast rate predict who won the round? Same paired-AUC probe the repo uses. */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
import { forecastMetric } from './forecast.ts';
const DIR=(process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);
const opts={garbagespeed:30,garbagecap:8,locktime:30,gravity:0.02,sdfMode:'abs' as const,
            insertMode:'onPlace' as const,cancelMode:'all' as const};
const pairs:{win:number;lose:number;label:string}[]=[]; const rows:any[]=[];
for(const file of readdirSync(DIR).filter(f=>f.endsWith('.ttrm')).sort()){
  const d=JSON.parse(readFileSync(`${DIR}/${file}`,'utf8'));
  for(const rnd of d.replay.rounds){ if(rnd.length!==2) continue;
    const P=rnd.map((p:any)=>({p,rp:p.replay,gameid:p.replay.options.gameid}));
    const vals:Record<string,any>={};
    for(const [me,other] of [[P[0],P[1]],[P[1],P[0]]] as any[]){
      const ev=me.rp.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
        .map((e:any)=>({frame:e.frame,sub:e.data.subframe??0,type:e.type,key:e.data.key}));
      const gin=me.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
        .map((e:any)=>({frame:e.frame,amt:e.data.data.amt,x:e.data.data.x,size:e.data.data.size}));
      const truth=other.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'
        &&e.data.data?.type==='garbage'&&e.data.data.gameid===me.gameid)
        .map((e:any)=>({frame:e.data.data.frame??e.frame,amt:e.data.data.amt})).sort((a:any,b:any)=>a.frame-b.frame);
      const r=simulate(ev,gin,me.rp.options.handling,me.rp.options.seed,me.rp.frames,DEFAULT_TABLE,opts);
      const mine=r.records.filter(x=>x.sent>0);
      let vf=-1; for(let i=0;i<Math.min(mine.length,truth.length);i++){
        if(Math.abs(mine[i]!.frame-truth[i]!.frame)<=25&&mine[i]!.sent===truth[i]!.amt) vf=mine[i]!.frame; else break; }
      let vIdx=-1; for(let i=0;i<r.locks.length;i++) if(r.locks[i]!.frame<=vf) vIdx=i;
      const recs=vIdx<0?[]:forecastMetric(r, STRICT).records.filter(x=>x.lockIndex<=vIdx);
      const fc=recs.filter(x=>x.kind!=='reactive').length;
      vals[me.p.username]={alive:me.p.alive,n:recs.length,fc,rate:recs.length?fc/recs.length:null,
        perPiece:vIdx>=0?fc/(vIdx+1):null,verified:vIdx+1};
    }
    const names=Object.keys(vals);
    if(names.length!==2) continue;
    const [a,b]=names as [string,string];
    const W=vals[a]!.alive?a:b, L=vals[a]!.alive?b:a;
    if(vals[W]!.alive===vals[L]!.alive) continue;      // need exactly one winner
    rows.push({W,L,...vals});
    for(const [metric,key] of [['forecast rate','rate'],['forecast per piece','perPiece'],['forecast count','fc'],['tucked T-spins','n']] as const){
      const w=vals[W]![key], l=vals[L]![key];
      if(w===null||l===null) continue;
      pairs.push({win:w,lose:l,label:metric});
    }
  }
}
console.log(`rounds with a decided winner and verified data on both sides: ${rows.length}\n`);
for(const m of ['forecast rate','forecast per piece','forecast count','tucked T-spins']){
  const P=pairs.filter(p=>p.label===m);
  if(!P.length){console.log(`  ${m.padEnd(20)} no usable pairs`);continue;}
  const wins=P.filter(p=>p.win>p.lose).length, ties=P.filter(p=>p.win===p.lose).length;
  const auc=100*(wins+0.5*ties)/P.length;
  console.log(`  ${m.padEnd(20)} AUC ${auc.toFixed(1)}%   (n=${P.length} pairs, ${ties} ties)`);
}
console.log(`\nreference from repo CLAUDE.md — TSD 60.9 · TST 55.8 are already filed under "No signal"`);

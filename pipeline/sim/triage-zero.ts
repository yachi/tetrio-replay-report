/** How many rounds does the sim get catastrophically wrong (near-zero lines vs a real player)? */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
import { replayDir } from './verified-prefix.ts';
const DIR=replayDir();
const opts={garbagespeed:30,garbagecap:8,locktime:30,gravity:0.02,sdfMode:'abs' as const,
            insertMode:'onPlace' as const,cancelMode:'all' as const};
let zero=0, tot=0, topout=0; const ratios:number[]=[]; const zeroRounds:string[]=[];
for(const f of readdirSync(DIR).filter(x=>x.endsWith('.ttrm')).sort()){
  const d=JSON.parse(readFileSync(`${DIR}/${f}`,'utf8'));
  d.replay.rounds.forEach((rnd:any,ri:number)=>{ if(rnd.length!==2) return;
    for(const me of rnd.map((p:any)=>({p,rp:p.replay}))){
      const ev=me.rp.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
        .map((e:any)=>({frame:e.frame,sub:e.data.subframe??0,type:e.type,key:e.data.key}));
      const gin=me.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
        .map((e:any)=>({frame:e.frame,amt:e.data.data.amt,x:e.data.data.x,size:e.data.data.size}));
      const r=simulate(ev,gin,me.rp.options.handling,me.rp.options.seed,me.rp.frames,DEFAULT_TABLE,opts);
      const rl=me.rp.results.stats.lines, rp=me.rp.results.stats.piecesplaced;
      tot++; if(r.topout) topout++;
      ratios.push(rl? r.lines/rl : 1);
      if(rl>0 && r.lines===0){ zero++; zeroRounds.push(`${f.slice(-9)} r${ri} ${me.p.username}: sim 0 lines/${r.locks.length}p vs real ${rl} lines/${rp}p${r.topout?' [sim topped out]':''}`); }
    }});}
ratios.sort((a,b)=>a-b);
console.log(`player-rounds: ${tot}`);
console.log(`sim topped out: ${topout}/${tot}`);
console.log(`sim cleared ZERO lines while the real player cleared some: ${zero}/${tot}`);
console.log(`sim/real line ratio — median ${ratios[Math.floor(ratios.length/2)]!.toFixed(2)}, p25 ${ratios[Math.floor(ratios.length*0.25)]!.toFixed(2)}, p75 ${ratios[Math.floor(ratios.length*0.75)]!.toFixed(2)}`);
console.log(`\nzero-line rounds:`); for(const z of zeroRounds.slice(0,15)) console.log('  '+z);

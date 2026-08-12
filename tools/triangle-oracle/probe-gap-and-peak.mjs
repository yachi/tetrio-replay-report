import { readdirSync, existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
// 1) receive->confirm gap distribution (ground-truth, straight from the .ttrm)
const gaps=[];
for(const d of dirs){ for(const f of readdirSync(`${SESS}/${d}`).filter(x=>x.endsWith(".ttrm"))){
  const dd=JSON.parse(readFileSync(`${SESS}/${d}/${f}`,"utf8"));
  for(const rnd of dd.replay.rounds){ if(!Array.isArray(rnd))continue;
    for(const p of rnd){ const evs=p.replay?.events; if(!evs)continue;
      const recv=new Map(), conf=new Map();
      for(const e of evs){ if(e.type!=="ige"||e.data?.data?.type!=="garbage")continue;
        if(e.data.type==="interaction") recv.set(e.data.data.iid,e.frame);
        if(e.data.type==="interaction_confirm") conf.set(e.data.data.iid,e.frame);
      }
      for(const[iid,rf]of recv){ if(conf.has(iid)) gaps.push(conf.get(iid)-rf); }
    }}}}
gaps.sort((a,b)=>a-b);
const mean=gaps.reduce((a,b)=>a+b,0)/gaps.length;
const med=gaps[Math.floor(gaps.length/2)];
console.log(`receive->confirm gap over ${gaps.length} batches: mean=${mean.toFixed(1)} median=${med} min=${gaps[0]} max=${gaps[gaps.length-1]} p10=${gaps[Math.floor(gaps.length*.1)]} p90=${gaps[Math.floor(gaps.length*.9)]}`);
console.log(`=> confirm+20 averages receive+${(mean+20).toFixed(1)}, but per-batch-variable (recorded), not a constant`);
// 2) per-session peak of confirm sweep
console.log("\nper-session confirm-timing peak (verified locks):");
for(const d of dirs){ let cases; try{cases=loadCases(`${SESS}/${d}`);}catch{continue;}
  let best=-1,bestSp=0,at20=0;
  for(const sp of [14,16,18,20,22,24,26]){ let s=0; for(const c of cases){ let r;try{r=runCase(c,{readyFrom:'confirm',garbagespeed:sp});}catch{continue;} s+=verifiedIndex(r,c.truth)+1;}
    if(sp===20)at20=s; if(s>best){best=s;bestSp=sp;} }
  console.log(`  ${d.slice(5)}: peak at speed ${bestSp} (${best}); speed20=${at20}  ${bestSp===20?'<-peak IS documented':`(peak ${bestSp>20?'>':'<'}20)`}`);
}

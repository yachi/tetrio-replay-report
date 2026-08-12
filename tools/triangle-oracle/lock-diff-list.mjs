import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
import { replayRound } from "./oracle.mjs";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const enc=(b)=>{let o="";for(let r=20;r<40;r++)for(let c=0;c<10;c++){const x=b[r][c];o+=x==null?".":x==="G"?"G":"#";}return o;};
const hasG=(s)=>s.includes("G");
const dirs = readdirSync(SESS).filter(x=>existsSync(`${SESS}/${x}`)&&readdirSync(`${SESS}/${x}`).some(f=>f.endsWith(".ttrm"))).sort();
const hits=[];
for(const dir of dirs){ let cases; try{cases=loadCases(`${SESS}/${dir}`);}catch{continue;}
  const parsed={};
  for(const c of cases){
    if(!parsed[c.file]) parsed[c.file]=JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`,"utf8"));
    const rp=parsed[c.file].replay.rounds[c.round]; const player=rp.find(p=>p.username===c.user); if(!player)continue;
    let sim,tri; try{sim=runCase(c);}catch{continue;} if(!sim.locks.length)continue;
    try{tri=replayRound(player,rp,{untilFrame:sim.locks[Math.min(12,sim.locks.length-1)].frame+2});}catch{continue;}
    for(let i=0;i<Math.min(12,sim.locks.length);i++){
      const f=sim.locks[i].frame, t=tri.gridAt(f); if(t===undefined)break;
      const s=enc(sim.boards[i]); if(s===t)continue; if(hasG(s)||hasG(t))break;
      hits.push({dir:dir.slice(5),file:c.file,round:c.round,user:c.user,lock:i,piece:sim.locks[i].piece,frame:f});
      break;
    }
  }
}
hits.sort((a,b)=>a.lock-b.lock);
console.log(`remaining garbage-free lock divergences: ${hits.length}`);
for(const h of hits.slice(0,12)) console.log(`  ${h.dir} ${h.file.replace('replay-','').replace('.ttrm','')} r${h.round} ${h.user} lock${h.lock} piece=${h.piece} f${h.frame}`);

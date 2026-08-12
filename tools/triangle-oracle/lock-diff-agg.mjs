// Classify the FIRST locked-piece divergence (sim vs Triangle) by row vs column, corpus-wide,
// garbage-free locks only — the drift-relevant signal (a lock in the wrong place truncates the prefix).
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
import { replayRound } from "./oracle.mjs";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const enc=(b)=>{let o="";for(let r=20;r<40;r++)for(let c=0;c<10;c++){const x=b[r][c];o+=x==null?".":x==="G"?"G":"#";}return o;};
const hasG=(s)=>s.includes("G");
const dirs = readdirSync(SESS).filter(x=>existsSync(`${SESS}/${x}`)&&readdirSync(`${SESS}/${x}`).some(f=>f.endsWith(".ttrm"))).sort();
const cls={none:0,colOnly:0,rowOnly:0,both:0}; const lockIdx=[];
for(const dir of dirs){ let cases; try{cases=loadCases(`${SESS}/${dir}`);}catch{continue;}
  const parsed={};
  for(const c of cases){
    if(!parsed[c.file]) parsed[c.file]=JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`,"utf8"));
    const rp=parsed[c.file].replay.rounds[c.round]; const player=rp.find(p=>p.username===c.user); if(!player)continue;
    let sim,tri; try{sim=runCase(c);}catch{continue;} if(!sim.locks.length)continue;
    try{tri=replayRound(player,rp,{untilFrame:sim.locks[Math.min(12,sim.locks.length-1)].frame+2});}catch{continue;}
    let found=null;
    for(let i=0;i<Math.min(12,sim.locks.length);i++){
      const f=sim.locks[i].frame, t=tri.gridAt(f); if(t===undefined)break;
      const s=enc(sim.boards[i]); if(s===t) continue; if(hasG(s)||hasG(t)) break;
      // diff cells: positions present in one but not the other
      const S=new Set(), T=new Set();
      for(let r=0;r<20;r++)for(let cc=0;cc<10;cc++){ if(s[r*10+cc]!=="."&&t[r*10+cc]===".") S.add([r,cc].join()); if(t[r*10+cc]!=="."&&s[r*10+cc]===".") T.add([r,cc].join()); }
      const rows=new Set(), cols=new Set();
      for(const k of [...S,...T]){ const [r,cc]=k.split(",").map(Number); rows.add(r); cols.add(cc); }
      // heuristic: if the differing cells share columns (same cols, different rows) => rowOnly (height);
      // if same rows different cols => colOnly (DAS). Compare the column-sets and row-sets of S vs T.
      const scols=new Set([...S].map(k=>k.split(",")[1])), tcols=new Set([...T].map(k=>k.split(",")[1]));
      const srows=new Set([...S].map(k=>k.split(",")[0])), trows=new Set([...T].map(k=>k.split(",")[0]));
      const colDiff=[...scols].sort().join()!==[...tcols].sort().join();
      const rowDiff=[...srows].sort().join()!==[...trows].sort().join();
      found={i, kind: colDiff&&rowDiff?"both":colDiff?"colOnly":rowDiff?"rowOnly":"both"};
      break;
    }
    if(!found) cls.none++; else { cls[found.kind]++; lockIdx.push(found.i); }
  }
}
console.log("first garbage-free LOCK divergence, row vs col:");
console.log(JSON.stringify(cls,null,1));
const hist={}; for(const i of lockIdx) hist[i]=(hist[i]||0)+1;
console.log("by lock index:", JSON.stringify(hist));

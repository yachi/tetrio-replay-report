// Where does the sim first diverge from the Triangle oracle over the FULL round (garbage included)?
// The garbage-free early game now matches; this finds the remaining gap (later locks / garbage).
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
import { replayRound } from "./oracle.mjs";
const ROOT=fileURLToPath(new URL("../../",import.meta.url)); const SESS=`${ROOT}sessions`;
const enc=(b)=>{let o="";for(let r=20;r<40;r++)for(let c=0;c<10;c++){const x=b[r][c];o+=x==null?".":x==="G"?"G":"#";}return o;};
const dirs=readdirSync(SESS).filter(x=>existsSync(`${SESS}/${x}`)&&readdirSync(`${SESS}/${x}`).some(f=>f.endsWith(".ttrm"))).sort();
const firstDivLock=[]; let matchAll=0, gCause=0, placeCause=0;
for(const dir of dirs){ let cases; try{cases=loadCases(`${SESS}/${dir}`);}catch{continue;}
  const parsed={};
  for(const c of cases){
    if(!parsed[c.file]) parsed[c.file]=JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`,"utf8"));
    const rp=parsed[c.file].replay.rounds[c.round]; const player=rp.find(p=>p.username===c.user); if(!player)continue;
    let sim; try{sim=runCase(c);}catch{continue;} if(!sim.locks.length)continue;
    const nCheck=Math.min(sim.locks.length,30);
    let tri; try{tri=replayRound(player,rp,{untilFrame:sim.locks[nCheck-1].frame+2});}catch{continue;}
    let found=null;
    for(let i=0;i<nCheck;i++){
      const f=sim.locks[i].frame, t=tri.gridAt(f); if(t===undefined)break;
      const s=enc(sim.boards[i]); if(s===t)continue;
      // does the divergence involve garbage rows (G present in one, not matching)?
      const sg=(s.match(/G/g)||[]).length, tg=(t.match(/G/g)||[]).length;
      found={i, gDiff: sg!==tg};
      break;
    }
    if(!found){ matchAll++; }
    else { firstDivLock.push(found.i); if(found.gDiff) gCause++; else placeCause++; }
  }
}
firstDivLock.sort((a,b)=>a-b);
console.log(`rounds where sim matches Triangle for all ${30} checked locks: ${matchAll}/592`);
console.log(`rounds that diverge: ${firstDivLock.length}, first-divergence lock median ${firstDivLock[Math.floor(firstDivLock.length/2)]}, min ${firstDivLock[0]}`);
console.log(`  divergence involves a GARBAGE-row-count mismatch: ${gCause}   pure placement (same garbage): ${placeCause}`);
const hist={}; for(const i of firstDivLock) { const b=i<6?"0-5":i<12?"6-11":i<20?"12-19":"20+"; hist[b]=(hist[b]||0)+1; }
console.log("  first-divergence lock buckets:", JSON.stringify(hist));

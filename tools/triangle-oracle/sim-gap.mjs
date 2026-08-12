// The sim's TRUE attack match vs real (the sim emits all-clear separately, acEmit:'separate', so its
// records are already correct) — quantify the gap to the oracle's 100% ceiling.
import { readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
const ROOT=fileURLToPath(new URL("../../",import.meta.url)); const SESS=`${ROOT}sessions`;
const dirs=readdirSync(SESS).filter(x=>existsSync(`${SESS}/${x}`)&&readdirSync(`${SESS}/${x}`).some(f=>f.endsWith(".ttrm"))).sort();
let matched=0,totalReal=0,exhaust=0,rounds=0; const cls={frame:0,amount:0,short:0,exhausted:0};
for(const dir of dirs){ let cases; try{cases=loadCases(`${SESS}/${dir}`);}catch{continue;}
  for(const c of cases){ let sim; try{sim=runCase(c);}catch{continue;}
    const sends=sim.records.filter(r=>r.sent>0).map(r=>({frame:r.frame,amt:r.sent})); const truth=c.truth; totalReal+=truth.length; rounds++;
    let i=0; for(;i<Math.min(sends.length,truth.length);i++){ if(Math.abs(sends[i].frame-truth[i].frame)>25){cls.frame++;break;} if(sends[i].amt!==truth[i].amt){cls.amount++;break;} matched++; }
    if(i>=Math.min(sends.length,truth.length)){ if(sends.length!==truth.length)cls.short++; else {cls.exhausted++;exhaust++;} }
  }
}
console.log(`SIM-vs-real: ${matched}/${totalReal} attacks = ${(100*matched/totalReal).toFixed(1)}%  (oracle ceiling: 100%)`);
console.log(`rounds matching EXHAUSTIVELY: ${exhaust}/${rounds} = ${(100*exhaust/rounds).toFixed(1)}%  (oracle: 98.3%)`);
console.log("first-mismatch cause:", JSON.stringify(cls));

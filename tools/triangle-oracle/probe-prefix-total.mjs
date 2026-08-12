import { readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter(x=>existsSync(`${SESS}/${x}`)&&readdirSync(`${SESS}/${x}`).some(f=>f.endsWith(".ttrm"))).sort();
let tot=0, per={};
for(const d of dirs){ let cases; try{cases=loadCases(`${SESS}/${d}`);}catch{continue;}
  let s=0; for(const c of cases){ let sim; try{sim=runCase(c);}catch{continue;} s+=verifiedIndex(sim,c.truth)+1; }
  per[d.slice(5)]=s; tot+=s;
}
console.log("verified locks per session:", JSON.stringify(per));
console.log("TOTAL:", tot);

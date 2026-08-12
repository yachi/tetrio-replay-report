// Does triangle's soft-drop model + a HIGHER gravity beat the current additive-slam prefix (13173)?
import { readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
const ROOT=fileURLToPath(new URL("../../",import.meta.url)); const SESS=`${ROOT}sessions`;
const dirs=readdirSync(SESS).filter(x=>existsSync(`${SESS}/${x}`)&&readdirSync(`${SESS}/${x}`).some(f=>f.endsWith(".ttrm"))).sort();
const all=[]; for(const d of dirs){ try{ for(const c of loadCases(`${SESS}/${d}`)) all.push(c);}catch{} }
function total(extra){ let s=0; for(const c of all){ let sim; try{sim=runCase(c,extra);}catch{continue;} s+=verifiedIndex(sim,c.truth)+1; } return s; }
console.log(`baseline (additive slam, g=0.02): ${total({})}`);
console.log("triangle soft-drop model, gravity sweep:");
let best=0,bestG=0;
for(const g of [0.02,0.05,0.1,0.15,0.2,0.3,0.5,0.8,1.0,1.5]){
  const t=total({sdfModel:'triangle', gravity:g});
  if(t>best){best=t;bestG=g;}
  console.log(`  g=${String(g).padStart(4)}: ${t}`);
}
console.log(`best triangle-model: g=${bestG} -> ${best}  (baseline additive 13173)`);

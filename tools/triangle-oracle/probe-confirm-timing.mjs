import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
const allCases = []; for (const d of dirs) { try { for (const c of loadCases(`${SESS}/${d}`)) allCases.push(c); } catch {} }
console.log(`cases: ${allCases.length}`);
function total(extra){ let s=0; for(const c of allCases){ let sim; try{sim=runCase(c,extra);}catch{continue;} s+=verifiedIndex(sim,c.truth)+1; } return s; }
const base = total({});
console.log(`\nBASELINE (readyFrom=interaction default, speed 30): ${base}\n`);
console.log("readyFrom=confirm sweep:");
let best=base, bestLabel="baseline(recv+30)";
for (const sp of [10,12,14,16,18,20,22,24,26,28,30]) {
  const t = total({ readyFrom: 'confirm', garbagespeed: sp });
  const d = t - base, mark = sp===20?"  <- documented garbagespeed":"";
  if (t>best){best=t;bestLabel=`confirm+${sp}`;}
  console.log(`  confirm + ${String(sp).padStart(2)}: ${t}  (${d>=0?'+':''}${d})${mark}`);
}
console.log("\nreadyFrom=interaction (receive) sweep for reference:");
for (const sp of [24,26,28,30,32]) {
  const t = total({ readyFrom: 'interaction', garbagespeed: sp });
  console.log(`  recv    + ${String(sp).padStart(2)}: ${t}  (${t-base>=0?'+':''}${t-base})`);
}
console.log(`\nBEST: ${bestLabel} = ${best}  (${best-base>=0?'+':''}${best-base} vs baseline)`);

import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
function run(extra){ let vsum=0, n=0, full=0; for(const dir of dirs){ let cases; try{cases=loadCases(`${SESS}/${dir}`);}catch{continue;} for(const c of cases){ let sim; try{sim=runCase(c,extra);}catch{continue;} const v=verifiedIndex(sim,c.truth); const sent=sim.records.filter(x=>x.sent>0).length; n++; vsum+=v+1; if(v+1>=Math.min(sent,c.truth.length)&&c.truth.length>0) full++; } } return {vsum,n,full}; }
const A=run({}); const B=run({attackModel:'exact'});
console.log(`               total verified locks   cases fully-verified`);
console.log(`default        ${String(A.vsum).padStart(8)}            ${A.full}/${A.n}`);
console.log(`attackModel=exact ${String(B.vsum).padStart(5)}            ${B.full}/${B.n}`);
console.log(`delta          ${B.vsum-A.vsum>=0?'+':''}${B.vsum-A.vsum}  (${((100*(B.vsum-A.vsum))/A.vsum).toFixed(1)}%)   fully-verified ${B.full-A.full>=0?'+':''}${B.full-A.full}`);

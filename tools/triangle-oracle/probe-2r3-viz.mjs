import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
// Boards from the PUBLISHED source. This read `oracleSim` from oracle-forecast.mjs until
// 2026-08-16, when that file's own reconstruction was deleted — see its header for the 26.9%
// inadmissible-provenance measurement that withdrew the candidate this probe was drawing.
import { runCaseOracle as oracleSim } from "../../pipeline/sim/oracle-source.ts";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const d = JSON.parse(readFileSync(`${ROOT}sessions/2026-07-28/replay-2026-07-28-2.ttrm`,"utf8"));
const rp = d.replay.rounds[3];
const player = rp.find(p=>p.username==="pinglamb");
const ora = oracleSim(player, rp);
const show = (k, label) => {
  const b = ora.boards[k]; if(!b){console.log(`lock ${k}: no board`);return;}
  // trim empty top rows
  let start=0; while(start<39 && b[start].every(c=>c==null)) start++;
  console.log(`\n--- lock ${k} (${label}) frame ${ora.locks[k]?.frame} piece=${ora.locks[k]?.piece} spin=${ora.locks[k]?.spin} cleared=${ora.locks[k]?.cleared} ---`);
  for(let r=Math.max(0,start-1);r<40;r++){
    const row=b[r].map(c=>c==null?".":c==="G"?"G":"#").join("");
    console.log(`  ${String(r).padStart(2)} ${row}`);
  }
};
for(const k of [11,12,13,14,15]) show(k, k===12?"ROOF":k===15?"T-SPIN":"");

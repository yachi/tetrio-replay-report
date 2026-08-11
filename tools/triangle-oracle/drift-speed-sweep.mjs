// Garbagespeed sweep — the evidence that garbage TIMING is NOT a drift lever (2026-08-11 deep dive).
// TETR.IO's documented garbagespeed is 20 (the "0.333s / 20-frame travel time"; the .ttrm's stored
// garbagemargin=10800 / garbageincrease=0.008 / b2bchaining=true pin these as `default`-preset rooms,
// and both `default` and `tetra league` presets in @haelp/teto set garbagespeed=20, garbagecap=8,
// garbagecapincrease=0, garbagecapmax=40). But the verified prefix (the real drift metric, vs the ige)
// peaks at speed ~28, per session 28/26/32/30/32 — NEVER 20 — and ground-truth 20 is 1.7–6.9% WORSE.
// So the sim's fitted 30 already sits at the peak; the ~8-frame gap is TETR.IO's undocumented "active"
// system (flagged as a TODO in @haelp/teto's GarbageQueue.tank), which no published spec explains and
// only a live capture could pin. Conclusion: do NOT adopt the documented 20; garbage params are spent
// as a ground-truth drift lever (unlike the exact ATTACK formula, where the documented value WAS the fix).
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
const allCases = []; for (const d of dirs) { try { for (const c of loadCases(`${SESS}/${d}`)) allCases.push(c); } catch {} }
function totalPrefix(speed){ let s=0; for(const c of allCases){ let sim; try{sim=runCase(c,{garbagespeed:speed});}catch{continue;} s+=verifiedIndex(sim,c.truth)+1; } return s; }
console.log("garbagespeed sweep — total verified locks (higher = less drift):");
let best=-1,bestS=0;
for(const sp of [14,16,18,20,22,24,26,28,30,32,34]){ const t=totalPrefix(sp); if(t>best){best=t;bestS=sp;} console.log(`  speed ${String(sp).padStart(2)}: ${t}${sp===30?"  <- current fitted":""}${sp===20?"  <- ground-truth default preset":""}`); }
console.log(`\npeak: speed ${bestS} (${best} locks)`);

// Garbagespeed sweep.
//
// CURRENT (measured 2026-08-15, six-session corpus, `runCase`'s BEST_OPTS default garbagespeed=20):
// the verified prefix now PEAKS AT THE DOCUMENTED VALUE, speed 20 — 20226 locks corpus-wide. Per
// session (this script's own per-session table below, `bun drift-speed-sweep.mjs`): outright peak
// in 4 of 6 sessions (07-22, 07-24, 07-28, 08-14) and TIED for peak in the other 2 — 2026-08-01 ties
// 18 and 20 at 2793 locks each, 2026-08-09 ties 20 and 22 at 2740 locks each. This reverses the
// 2026-08-11 finding below.
//
// ORIGINAL 2026-08-11 finding (five-session corpus, kept for history — since falsified by later sim
// fixes, not by this script changing): TETR.IO's documented garbagespeed is 20 (the "0.333s / 20-frame
// travel time"; the .ttrm's stored garbagemargin=10800 / garbageincrease=0.008 / b2bchaining=true pin
// these as `default`-preset rooms, and both `default` and `tetra league` presets in @haelp/teto set
// garbagespeed=20, garbagecap=8, garbagecapincrease=0, garbagecapmax=40). But the verified prefix (the
// real drift metric, vs the ige) peaked at speed ~28, per session 28/26/32/30/32 — NEVER 20 — and
// ground-truth 20 was 1.7-6.9% WORSE. So the sim's THEN-fitted 30 already sat at the peak; the ~8-frame
// gap was attributed to TETR.IO's undocumented "active" system (flagged as a TODO in @haelp/teto's
// GarbageQueue.tank). Conclusion at the time: do NOT adopt the documented 20 — a conclusion that three
// later sim fixes (documented-garbagespeed default itself, the garbage-cancel protocol port
// (+2357 locks), and locktime 60->30) went on to falsify: the sim's default is 20 today, and it is now
// also the measured peak.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
const SPEEDS = [14,16,18,20,22,24,26,28,30,32,34];

// Load per-session, not pooled, so the per-session table below and the corpus total share exactly
// one set of runCase() results — no second pass that could drift from the first.
const bySession = {};
for (const d of dirs) { try { bySession[d] = loadCases(`${SESS}/${d}`); } catch {} }

function totalPrefix(cases, speed){ let s=0; for(const c of cases){ let sim; try{sim=runCase(c,{garbagespeed:speed});}catch{continue;} s+=verifiedIndex(sim,c.truth)+1; } return s; }

// Per-session sweep and peak (per-speed totals, corpus total = sum over sessions).
console.log("garbagespeed sweep — per session (verified locks, higher = less drift):");
const perSessionTotals = {}; for (const sp of SPEEDS) perSessionTotals[sp] = 0;
for (const d of Object.keys(bySession)) {
  const cases = bySession[d];
  const row = {}; for (const sp of SPEEDS) { row[sp] = totalPrefix(cases, sp); perSessionTotals[sp] += row[sp]; }
  const best = Math.max(...SPEEDS.map((sp) => row[sp]));
  const peaks = SPEEDS.filter((sp) => row[sp] === best);
  const tag = peaks.length > 1 ? `TIE @ ${best}` : `@ ${best}`;
  console.log(`  ${d}: peak=${peaks.join(",")} ${tag}   ${SPEEDS.map((sp) => `${sp}:${row[sp]}`).join(" ")}`);
}

console.log("\ngarbagespeed sweep — corpus total (sum of the per-session table above):");
let best=-1,bestS=0;
for(const sp of SPEEDS){ const t=perSessionTotals[sp]; if(t>best){best=t;bestS=sp;} console.log(`  speed ${String(sp).padStart(2)}: ${t}${sp===20?"  <- ground-truth default preset AND current sim default":""}`); }
console.log(`\npeak: speed ${bestS} (${best} locks)`);

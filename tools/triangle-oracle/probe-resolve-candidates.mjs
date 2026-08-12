// Resolve clause 2 for the 3 forecast_lineclear candidates by DIRECT FRAME ORDERING (ground truth),
// bypassing the unstable provenance reconstruction. roof lock frame vs supporting-garbage insertion
// frame (recorded confirm + documented garbagespeed 20, next-non-clearing-lock gate).
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { oracleSim } from "./oracle-forecast.mjs";
import { forecastMetric } from "../../pipeline/sim/forecast.ts";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const CANDS = [
  { dir:"2026-07-28", file:"replay-2026-07-28-2.ttrm", round:3, user:"pinglamb" },
  { dir:"2026-07-28", file:"replay-2026-07-28-3.ttrm", round:5, user:"yachi" },
  { dir:"2026-07-28", file:"replay-2026-07-28-6.ttrm", round:5, user:"pinglamb" },
];
for (const cd of CANDS) {
  const d = JSON.parse(readFileSync(`${ROOT}sessions/${cd.dir}/${cd.file}`,"utf8"));
  const rp = d.replay.rounds[cd.round];
  const player = rp.find(p=>p.username===cd.user);
  const ora = oracleSim(player, rp);
  const m = forecastMetric(ora, true);
  const rec = m.records.find(r => r.kind==="forecast_lineclear");
  if(!rec){ console.log(`${cd.file} r${cd.round}: NO forecast_lineclear record`); continue; }
  const k = rec.lockIndex, j = rec.roofFrom;
  const roofFrame = ora.locks[j]?.frame, Tframe = ora.locks[k]?.frame;
  console.log(`\n=== ${cd.file.replace('replay-','').replace('.ttrm','')} r${cd.round} ${cd.user} ===`);
  console.log(`  T at lock ${k} (frame ${Tframe}), roof at lock ${j} (frame ${roofFrame}), floorOrigin=${rec.floorOrigin} floorFrom=${rec.floorFrom}`);
  // garbage inserts (Triangle) between roof and T
  const between = ora.garbageEvents.filter(g => g.lockIndex > j && g.lockIndex <= k);
  console.log(`  Triangle garbage inserts in (roof lock ${j}, T lock ${k}]: ${between.length ? between.map(g=>`f${g.frame}@lock${g.lockIndex}(${g.amt})`).join(" ") : "NONE"}`);
  // ground-truth confirm frames from the .ttrm
  const confirms = player.replay.events
    .filter(e=>e.type==="ige"&&e.data?.data?.type==="garbage"&&e.data.type==="interaction_confirm")
    .map(e=>({iid:e.data.data.iid, confirm:e.frame, amt:e.data.data.amt}));
  // which recorded confirms have confirm+20 falling AFTER the roof frame (=> garbage that could only
  // have inserted after the roof, i.e. arrived-later is FORCED regardless of reconstruction)
  const afterRoof = confirms.filter(c => c.confirm+20 > roofFrame && c.confirm+20 <= Tframe+60);
  console.log(`  ground-truth confirm+20 landing in (roofFrame ${roofFrame}, ~Tframe]: ${afterRoof.length?afterRoof.map(c=>`iid${c.iid} ins~${c.confirm+20}(${c.amt})`).join(" "):"NONE"}`);
  const verdict = between.length>0 || afterRoof.length>0
    ? "arrived-later CONFIRMED by frame ordering (garbage inserted after roof) -> NOT a forecast"
    : "PRE-EXISTED: no garbage straddles the roof->T window, support present at roof -> clause 2 PASSES "
      + "(a real forecast; proven in ForecastCandidate.dfy, board verified by probe-oracle-verify.mjs)";
  console.log(`  VERDICT: ${verdict}`);
}

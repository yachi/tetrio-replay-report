import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { Classes } from "@haelp/teto";
const Game = Classes.Game;
import { loadCases } from "../../pipeline/sim/verified-prefix.ts";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const TL_DEFAULTS = { g:0.02,boardwidth:10,boardheight:20,kickset:"SRS+",bagtype:"7-bag",combotable:"multiplier",
  spinbonuses:"T-spins",garbageblocking:"combo blocking",garbagetargetbonus:"none",clutch:false,stock:0,
  garbagemultiplier:1,garbagespeed:20,garbageholesize:1,messiness_change:1,messiness_nosame:false,
  messiness_timeout:0,messiness_inner:0,messiness_center:false,garbageabsolutecap:0,garbagecapincrease:0,
  garbagecapmax:40,garbagecap:8,garbagecapmargin:0,usebombs:false,roundmode:"down",openerphase:0,
  garbagespecialbonus:false,allclears:true,allclear_garbage:10,allclear_b2b:0,b2bcharging:false,
  infinite_movement:false,lockresets:15,locktime:30,gravitymay20g:false,allow180:true,allow_harddrop:true,
  display_hold:true,can_undo:false,can_retry:false,infinite_hold:false,stride:false,passthrough:"zero" };
const d = JSON.parse(readFileSync(`${ROOT}sessions/2026-07-28/replay-2026-07-28-2.ttrm`,"utf8"));
const rp = d.replay.rounds[3];
const player = rp.find(p=>p.username==="pinglamb");
const o = player.replay.options;
const players = rp.map(p=>({gameid:p.replay.options.gameid, userid:p.id, username:p.username}));
const eng = Game.createEngine({...TL_DEFAULTS,...o,g:o.g??0.02}, o.gameid, players);
const byFrame = new Map();
for(const e of player.replay.events){ if(!byFrame.has(e.frame))byFrame.set(e.frame,[]); byFrame.get(e.frame).push(e); }
const sends=[]; let curFrame=0, lockN=0;
eng.events.on("falling.lock",(res)=>{ const rec={lock:lockN,frame:curFrame,lines:res.lines,spin:res.spin};
  // find any attack-ish field
  for(const k of ["garbage","attack","sent","send","gb","out"]) if(res[k]!=null) rec[k]=res[k];
  lockN++; sends.push(rec); });
const total = player.replay.frames ?? 2000;
for(let f=0; f<=total && lockN<18; f++){ curFrame=f; const r=eng.tick(byFrame.get(f)||[]); if(r&&r.topout)break; }
console.log("oracle locks (lock,frame,lines,spin,+attack fields) through lock 17:");
for(const s of sends) console.log("  "+JSON.stringify(s));
const cases = loadCases(`${ROOT}sessions/2026-07-28`);
const c = cases.find(x=>x.file==="replay-2026-07-28-2.ttrm"&&x.round===3&&x.user==="pinglamb");
console.log("\nrecorded TRUTH (sent frame/amt) first 10:");
for(const t of c.truth.slice(0,10)) console.log(`  f${t.frame} amt${t.amt}`);

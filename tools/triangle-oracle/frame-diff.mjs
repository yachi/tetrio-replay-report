// Per-frame falling-piece differential: sim.ts vs Triangle. Prints the first frame where the two
// engines' falling-piece cell SETS diverge, for one round/player, so a movement mechanic can be
// matched to Triangle's code.  Usage: bun frame-diff.mjs <sessionDir> <file> <round> <user>
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { Classes } from "@haelp/teto";
const Game = Classes.Game;
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const [,, sess="2026-07-24", file="replay-2026-07-24-7.ttrm", roundS="3", user="pinglamb"] = process.argv;
const round = +roundS;
const TL = { g:0.02,boardwidth:10,boardheight:20,kickset:"SRS+",bagtype:"7-bag",combotable:"multiplier",
  spinbonuses:"T-spins",garbageblocking:"combo blocking",garbagetargetbonus:"none",clutch:false,stock:0,
  garbagemultiplier:1,garbagespeed:20,garbageholesize:1,messiness_change:1,messiness_nosame:false,
  messiness_timeout:0,messiness_inner:0,messiness_center:false,garbageabsolutecap:0,garbagecapincrease:0,
  garbagecapmax:40,garbagecap:8,garbagecapmargin:0,usebombs:false,roundmode:"down",openerphase:0,
  garbagespecialbonus:false,allclears:true,allclear_garbage:10,allclear_b2b:0,b2bcharging:false,
  infinite_movement:false,lockresets:15,locktime:30,gravitymay20g:false,allow180:true,allow_harddrop:true,
  display_hold:true,can_undo:false,can_retry:false,infinite_hold:false,stride:false,passthrough:"zero" };
const d = JSON.parse(readFileSync(`${ROOT}sessions/${sess}/${file}`,"utf8"));
const rp = d.replay.rounds[round];
const player = rp.find(p=>p.username===user);
const o = player.replay.options;
const players = rp.map(p=>({gameid:p.replay.options.gameid, userid:p.id, username:p.username}));

// Triangle per-frame falling cells (sim coords: col=x, row=39-y)
const eng = Game.createEngine({...TL,...o,g:o.g??0.02}, o.gameid, players);
const byFrame = new Map();
for(const e of player.replay.events){ if(!byFrame.has(e.frame))byFrame.set(e.frame,[]); byFrame.get(e.frame).push(e); }
const triFrames = new Map();
const total = Math.min(player.replay.frames ?? 2000, 800);
for(let f=0; f<=total; f++){ const r=eng.tick(byFrame.get(f)||[]);
  let cells=null; try{ cells = eng.falling.absoluteBlocks.map(([x,y])=>`${x},${39-y}`).sort(); }catch{}
  triFrames.set(f, cells); if(r&&r.topout)break; }

// sim per-frame falling cells via trace hook
const cases = loadCases(`${ROOT}sessions/${sess}`);
const c = cases.find(x=>x.file===file && x.round===round && x.user===user);
const simFrames = new Map();
runCase(c, { trace: (f, cells)=>{ simFrames.set(f, cells.map(z=>`${z.col},${z.row}`).sort()); } });

// compare
let firstDiff=null;
const eqAt=(f)=>{ const t=triFrames.get(f), s=simFrames.get(f); if(!t||!s) return true; return t.length===s.length && t.every((v,i)=>v===s[i]); };
for(let f=0; f<=total; f++){
  if(eqAt(f)) continue;
  // require the divergence to PERSIST >=3 frames (skip transient spawn-row / gravity-order blips)
  let persist=true; for(let g=f; g<=Math.min(total,f+3); g++){ if(eqAt(g)){persist=false;break;} }
  if(persist){ firstDiff=f; break; }
}
if(firstDiff==null){ console.log("no falling-piece divergence in first",total,"frames"); process.exit(0); }
console.log(`FIRST falling-piece divergence at frame ${firstDiff}`);
for(let f=Math.max(0,firstDiff-2); f<=firstDiff+2; f++){
  const t=triFrames.get(f), s=simFrames.get(f);
  const evs=(byFrame.get(f)||[]).filter(e=>e.type==="keydown"||e.type==="keyup").map(e=>`${e.type}:${e.data.key}${e.data.hoisted?"(H)":""}@${(e.data.subframe??0).toFixed(2)}`).join(" ");
  console.log(`  f${f}  sim=[${(s||[]).join(" ")}]  tri=[${(t||[]).join(" ")}]  ${evs?"EV "+evs:""}`);
}

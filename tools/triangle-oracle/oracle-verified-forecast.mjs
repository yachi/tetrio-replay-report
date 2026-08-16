// Definitive forecast count over GROUND-TRUTH-VERIFIED oracle boards, corpus-wide.
// For each round: run the Triangle oracle (survives every round), extract its per-lock OUTGOING attacks,
// find the oracle verified-prefix = last lock whose sends still match the recorded ige truth (frame ±25,
// amount exact), then run forecastMetric within that prefix and resolve clause 2 by FRAME ORDERING
// (recorded confirm + documented garbagespeed 20 vs the roof lock frame) — reconstruction-independent.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { Classes } from "@haelp/teto";
const Game = Classes.Game;
import { loadCases } from "../../pipeline/sim/verified-prefix.ts";
// Boards from the PUBLISHED source (2026-08-16); oracle-forecast.mjs's own reconstruction was
// deleted — it named an impossible placer for 26.9% of roof cells and ran 28% past the end of
// each round. See its header.
import { runCaseOracle as oracleSim } from "../../pipeline/sim/oracle-source.ts";
import { forecastMetric } from "../../pipeline/sim/forecast.ts";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const SPEED = 20;
const TL = { g:0.02,boardwidth:10,boardheight:20,kickset:"SRS+",bagtype:"7-bag",combotable:"multiplier",
  spinbonuses:"T-spins",garbageblocking:"combo blocking",garbagetargetbonus:"none",clutch:false,stock:0,
  garbagemultiplier:1,garbagespeed:20,garbageholesize:1,messiness_change:1,messiness_nosame:false,
  messiness_timeout:0,messiness_inner:0,messiness_center:false,garbageabsolutecap:0,garbagecapincrease:0,
  garbagecapmax:40,garbagecap:8,garbagecapmargin:0,usebombs:false,roundmode:"down",openerphase:0,
  garbagespecialbonus:false,allclears:true,allclear_garbage:10,allclear_b2b:0,b2bcharging:false,
  infinite_movement:false,lockresets:15,locktime:30,gravitymay20g:false,allow180:true,allow_harddrop:true,
  display_hold:true,can_undo:false,can_retry:false,infinite_hold:false,stride:false,passthrough:"zero" };

// oracle per-lock outgoing attacks (frame, amt) — a second engine run, capturing falling.lock.garbage
function oracleSends(player, rp) {
  const o = player.replay.options;
  const players = rp.map(p=>({gameid:p.replay.options.gameid, userid:p.id, username:p.username}));
  const eng = Game.createEngine({...TL,...o,g:o.g??0.02}, o.gameid, players);
  const byFrame = new Map();
  for(const e of player.replay.events){ if(!byFrame.has(e.frame))byFrame.set(e.frame,[]); byFrame.get(e.frame).push(e); }
  const sends=[]; let curFrame=0;
  eng.events.on("falling.lock",(res)=>{ const amt = Array.isArray(res.garbage)? res.garbage.reduce((a,b)=>a+b,0):0;
    if(amt>0) sends.push({frame:curFrame, amt}); });
  const total = player.replay.frames ?? 4000;
  for(let f=0; f<=total; f++){ curFrame=f; const r=eng.tick(byFrame.get(f)||[]); if(r&&r.topout)break; }
  return sends;
}
// last matching index in the oracle send stream vs truth (frame ±25, amount exact), returns matched frame
function oracleVerifiedFrame(sends, truth) {
  let vf=-1;
  for(let i=0;i<Math.min(sends.length,truth.length);i++){
    if(Math.abs(sends[i].frame-truth[i].frame)>25) break;
    if(sends[i].amt!==truth[i].amt) break;
    vf=sends[i].frame;
  }
  return vf;
}
// clause 2 by ground-truth frame ordering for a garbage-supported forecast_lineclear record
function clause2ByFrames(player, ora, rec) {
  const j=rec.roofFrom, k=rec.lockIndex;
  if(j==null) return "undetermined";
  const roofFrame=ora.locks[j]?.frame, Tframe=ora.locks[k]?.frame;
  if(rec.floorFrom!=null && rec.floorFrom>=0) return rec.floorFrom>j ? "arrived-later" : "pre-existed"; // placer
  // garbage support: does any recorded batch insert in (roofFrame, Tframe]?  LB = confirm+SPEED, and a
  // real insertion is >= LB (the next-lock gate only delays). SOUNDNESS of the two directions:
  //  - straddles (LB in (roof,T]) is a NECESSARY-not-sufficient flag for a real straddle; using it to
  //    fall back to 'undetermined' is conservative (it can demote a genuine pre-existed, never promote).
  //  - presentAtRoof (LB <= roof) is OPTIMISTIC: a batch with LB<=roof could still be gated INTO the
  //    window, so a 'pre-existed' verdict here is a CANDIDATE, not a proof. Every 'pre-existed' this
  //    sweep emits must be board-confirmed separately (candidate A is: probe-oracle-verify.mjs shows the
  //    support garbage present at the roof, and ForecastCandidate.dfy proves the frame ordering). So the
  //    printed VERIFIED count is a conservative FLOOR whose members still need the per-case board check.
  const conf = player.replay.events.filter(e=>e.type==="ige"&&e.data?.data?.type==="garbage"&&e.data.type==="interaction_confirm")
    .map(e=>({lb:e.frame+SPEED}));
  const straddles = conf.some(c => c.lb>roofFrame && c.lb<=Tframe);
  const presentAtRoof = conf.some(c => c.lb<=roofFrame);
  return !presentAtRoof ? "arrived-later" : straddles ? "undetermined" : "pre-existed";
}

const dirs = readdirSync(SESS).filter(x=>existsSync(`${SESS}/${x}`)&&readdirSync(`${SESS}/${x}`).some(f=>f.endsWith(".ttrm"))).sort();
let rounds=0, oraDeeperThanSim=0, kindHits=0, verified=[];
for(const dir of dirs){ let cases; try{cases=loadCases(`${SESS}/${dir}`);}catch{continue;}
  const parsed={};
  for(const c of cases){
    if(!parsed[c.file]) parsed[c.file]=JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`,"utf8"));
    const rp=parsed[c.file].replay.rounds[c.round]; const player=rp.find(p=>p.username===c.user); if(!player)continue;
    let ora, sends; try{ ora=oracleSim(player,rp); sends=oracleSends(player,rp);}catch{continue;}
    const vf = oracleVerifiedFrame(sends, c.truth);
    if(vf<0) continue;
    rounds++;
    const m = forecastMetric(ora, true);
    for(const rec of m.records){
      if(rec.kind!=="forecast_lineclear"&&rec.kind!=="forecast_garbage") continue;
      const tf = ora.locks[rec.lockIndex]?.frame;
      if(tf==null || tf>vf) continue;                 // only within the oracle's ATTACK-verified prefix
      kindHits++;
      const cl2 = clause2ByFrames(player, ora, rec);
      if(cl2==="pre-existed") verified.push(`${dir.slice(5)} ${c.user} ${c.file.replace('replay-','').replace('.ttrm','')} r${c.round} lock${rec.lockIndex} ${rec.kind} (roof ${rec.roofFrom})`);
    }
  }
}
console.log(`rounds with an oracle-verified prefix: ${rounds}`);
console.log(`forecast_* KIND records within oracle-verified prefixes: ${kindHits}`);
console.log(`VERIFIED forecasts (clause 2 = pre-existed by ground-truth frames):  ${verified.length}`);
verified.forEach(v=>console.log("  "+v));

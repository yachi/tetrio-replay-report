// Corrected ceiling: emit each res.garbage segment as a SEPARATE send (TETR.IO emits base and the
// all-clear +10 as separate ige events), matching how c.truth records them.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { Classes } from "@haelp/teto";
const Game = Classes.Game;
import { loadCases } from "../../pipeline/sim/verified-prefix.ts";
const ROOT=fileURLToPath(new URL("../../",import.meta.url)); const SESS=`${ROOT}sessions`;
const TL={g:0.02,boardwidth:10,boardheight:20,kickset:"SRS+",bagtype:"7-bag",combotable:"multiplier",spinbonuses:"T-spins",garbageblocking:"combo blocking",garbagetargetbonus:"none",clutch:false,stock:0,garbagemultiplier:1,garbagespeed:20,garbageholesize:1,messiness_change:1,messiness_nosame:false,messiness_timeout:0,messiness_inner:0,messiness_center:false,garbageabsolutecap:0,garbagecapincrease:0,garbagecapmax:40,garbagecap:8,garbagecapmargin:0,usebombs:false,roundmode:"down",openerphase:0,garbagespecialbonus:false,allclears:true,allclear_garbage:10,allclear_b2b:0,b2bcharging:false,infinite_movement:false,lockresets:15,locktime:30,gravitymay20g:false,allow180:true,allow_harddrop:true,display_hold:true,can_undo:false,can_retry:false,infinite_hold:false,stride:false,passthrough:"zero"};
function oracleSends(player,rp){ const o=player.replay.options; const players=rp.map(p=>({gameid:p.replay.options.gameid,userid:p.id,username:p.username}));
  let eng; try{eng=Game.createEngine({...TL,...o,g:o.g??TL.g},o.gameid,players);}catch{return null;}
  const byFrame=new Map(); for(const e of player.replay.events){ if(!byFrame.has(e.frame))byFrame.set(e.frame,[]); byFrame.get(e.frame).push(e);}
  const sends=[]; let cur=0, topout=false;
  eng.events.on("falling.lock",(res)=>{ if(Array.isArray(res.garbage)) for(const g of res.garbage) if(g>0) sends.push({frame:cur,amt:g}); });
  try{ for(let f=0;f<=(player.replay.frames??4000);f++){ cur=f; const r=eng.tick(byFrame.get(f)||[]); if(r&&r.topout){topout=true;break;} } }catch{}
  return {sends,topout}; }
const dirs=readdirSync(SESS).filter(x=>existsSync(`${SESS}/${x}`)&&readdirSync(`${SESS}/${x}`).some(f=>f.endsWith(".ttrm"))).sort();
let matched=0,totalReal=0,exhaustRounds=0,rounds=0; const cls={frame:0,amount:0,short:0,exhausted:0};
for(const dir of dirs){ let cases; try{cases=loadCases(`${SESS}/${dir}`);}catch{continue;}
  const parsed={};
  for(const c of cases){ if(!parsed[c.file])parsed[c.file]=JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`,"utf8"));
    const rp=parsed[c.file].replay.rounds[c.round]; const player=rp.find(p=>p.username===c.user); if(!player)continue;
    const os=oracleSends(player,rp); if(!os)continue; const {sends}=os; const truth=c.truth; totalReal+=truth.length; rounds++;
    let i=0; for(;i<Math.min(sends.length,truth.length);i++){ if(Math.abs(sends[i].frame-truth[i].frame)>25){cls.frame++;break;} if(sends[i].amt!==truth[i].amt){cls.amount++;break;} matched++; }
    if(i>=Math.min(sends.length,truth.length)){ if(sends.length!==truth.length)cls.short++; else {cls.exhausted++; exhaustRounds++;} }
  }
}
console.log(`CORRECTED oracle-vs-real ceiling: ${matched}/${totalReal} attacks = ${(100*matched/totalReal).toFixed(1)}%`);
console.log(`rounds matching EXHAUSTIVELY: ${exhaustRounds}/${rounds} = ${(100*exhaustRounds/rounds).toFixed(1)}%`);
console.log("first-mismatch cause:", JSON.stringify(cls));

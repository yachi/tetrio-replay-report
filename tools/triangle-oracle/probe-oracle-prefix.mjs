import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { Classes } from "@haelp/teto";
const Game = Classes.Game;
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
const ROOT=fileURLToPath(new URL("../../",import.meta.url)); const SESS=`${ROOT}sessions`;
const TL={g:0.02,boardwidth:10,boardheight:20,kickset:"SRS+",bagtype:"7-bag",combotable:"multiplier",spinbonuses:"T-spins",garbageblocking:"combo blocking",garbagetargetbonus:"none",clutch:false,stock:0,garbagemultiplier:1,garbagespeed:20,garbageholesize:1,messiness_change:1,messiness_nosame:false,messiness_timeout:0,messiness_inner:0,messiness_center:false,garbageabsolutecap:0,garbagecapincrease:0,garbagecapmax:40,garbagecap:8,garbagecapmargin:0,usebombs:false,roundmode:"down",openerphase:0,garbagespecialbonus:false,allclears:true,allclear_garbage:10,allclear_b2b:0,b2bcharging:false,infinite_movement:false,lockresets:15,locktime:30,gravitymay20g:false,allow180:true,allow_harddrop:true,display_hold:true,can_undo:false,can_retry:false,infinite_hold:false,stride:false,passthrough:"zero"};
function oracleSends(player, rp){
  const o=player.replay.options; const players=rp.map(p=>({gameid:p.replay.options.gameid,userid:p.id,username:p.username}));
  let eng; try{eng=Game.createEngine({...TL,...o,g:o.g??TL.g},o.gameid,players);}catch{return null;}
  const byFrame=new Map(); for(const e of player.replay.events){ if(!byFrame.has(e.frame))byFrame.set(e.frame,[]); byFrame.get(e.frame).push(e);}
  const sends=[]; let cur=0;
  eng.events.on("falling.lock",(res)=>{ const amt=Array.isArray(res.garbage)?res.garbage.reduce((a,b)=>a+b,0):0; if(amt>0) sends.push({frame:cur,amt}); });
  const total=player.replay.frames??4000;
  try{ for(let f=0;f<=total;f++){ cur=f; const r=eng.tick(byFrame.get(f)||[]); if(r&&r.topout)break; } }catch{return null;}
  return sends;
}
function vprefix(sends, truth){ let v=0; for(let i=0;i<Math.min(sends.length,truth.length);i++){ if(Math.abs(sends[i].frame-truth[i].frame)>25)break; if(sends[i].amt!==truth[i].amt)break; v++; } return v; }
const dirs=readdirSync(SESS).filter(x=>existsSync(`${SESS}/${x}`)&&readdirSync(`${SESS}/${x}`).some(f=>f.endsWith(".ttrm"))).sort();
let oraTot=0, simTot=0, oraWins=0, simWins=0, n=0;
for(const dir of dirs){ let cases; try{cases=loadCases(`${SESS}/${dir}`);}catch{continue;}
  const parsed={};
  for(const c of cases){
    if(!parsed[c.file]) parsed[c.file]=JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`,"utf8"));
    const rp=parsed[c.file].replay.rounds[c.round]; const player=rp.find(p=>p.username===c.user); if(!player)continue;
    const sends=oracleSends(player,rp); if(!sends)continue;
    let sim; try{sim=runCase(c);}catch{continue;}
    const ov=vprefix(sends,c.truth);
    const sv=verifiedIndex(sim,c.truth)+1;  // sim verified locks; but compare attack-prefix
    // sim attack-prefix (number of matching sent-attacks):
    const mine=sim.records.filter(x=>x.sent>0); let sap=0; for(let i=0;i<Math.min(mine.length,c.truth.length);i++){ if(Math.abs(mine[i].frame-c.truth[i].frame)>25)break; if(mine[i].sent!==c.truth[i].amt)break; sap++; }
    oraTot+=ov; simTot+=sap; n++;
    if(ov>sap)oraWins++; else if(sap>ov)simWins++;
  }
}
console.log(`over ${n} rounds — matching sent-attacks vs the REAL ige:`);
console.log(`  ORACLE (triangle) total: ${oraTot}`);
console.log(`  SIM total:               ${simTot}`);
console.log(`  rounds oracle > sim: ${oraWins}   sim > oracle: ${simWins}`);

// PROOF v2: proper cleared-row reconstruction. Snapshot the y-up board before each tick; at lock,
// pre-clear board = snapshot + piece cells; full rows = clearedRows (convert y-up -> sim y-down).
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { Classes } from "@haelp/teto";
const Game = Classes.Game;
import { loadCases } from "../../pipeline/sim/verified-prefix.ts";
import { matchesIgeY } from "../../pipeline/sim/ige-y-oracle.ts";
const ROOT=fileURLToPath(new URL("../../",import.meta.url)); const SESS=`${ROOT}sessions`;
const TL={g:0.02,boardwidth:10,boardheight:20,kickset:"SRS+",bagtype:"7-bag",combotable:"multiplier",spinbonuses:"T-spins",garbageblocking:"combo blocking",garbagetargetbonus:"none",clutch:false,stock:0,garbagemultiplier:1,garbagespeed:20,garbageholesize:1,messiness_change:1,messiness_nosame:false,messiness_timeout:0,messiness_inner:0,messiness_center:false,garbageabsolutecap:0,garbagecapincrease:0,garbagecapmax:40,garbagecap:8,garbagecapmargin:0,usebombs:false,roundmode:"down",openerphase:0,garbagespecialbonus:false,allclears:true,allclear_garbage:10,allclear_b2b:0,b2bcharging:false,infinite_movement:false,lockresets:15,locktime:30,gravitymay20g:false,allow180:true,allow_harddrop:true,display_hold:true,can_undo:false,can_retry:false,infinite_hold:false,stride:false,passthrough:"zero"};
function oracleRecords(player, rp){
  const o=player.replay.options; const players=rp.map(p=>({gameid:p.replay.options.gameid,userid:p.id,username:p.username}));
  const eng=Game.createEngine({...TL,...o,g:o.g??TL.g},o.gameid,players);
  const byFrame=new Map(); for(const e of player.replay.events){ if(!byFrame.has(e.frame))byFrame.set(e.frame,[]); byFrame.get(e.frame).push(e);}
  const W=10; const snap=()=>{ const st=eng.board.state; const g=[]; for(let r=0;r<st.length;r++){ const row=new Array(W).fill(false); for(let c=0;c<W;c++){ if(st[r]?.[c]!=null) row[c]=true; } g.push(row);} return g; };
  let preTick=snap(); const records=[]; let pending=null;
  eng.events.on("falling.lock.pre",()=>{ const f=eng.falling; pending={cells:f.absoluteBlocks.map(([x,y])=>[x,y])}; });
  eng.events.on("falling.lock",(res)=>{
    const sent=(res.garbage||[]).reduce((a,b)=>a+b,0);
    let clearedRows=[];
    if(res.lines>0 && pending){
      const g=preTick.map(r=>r.slice()); // y-up board before this tick
      for(const [x,y] of pending.cells){ if(y>=0&&y<g.length&&x>=0&&x<W) g[y][x]=true; }
      for(let y=0;y<g.length;y++){ if(g[y].every(Boolean)) clearedRows.push(39-y); } // full row -> sim y-down
    }
    records.push({frame:eng.frame, sent, lines:res.lines, clearedRows});
    pending=null;
  });
  try{ const maxF=player.replay.frames??20000; for(let f=0;f<=maxF;f++){ preTick=snap(); const r=eng.tick(byFrame.get(f)||[]); if(r&&r.topout)break; } }catch{}
  return records;
}
function vIndex(records, truth){
  const mine=records.filter(x=>x.sent>0); let vf=-1;
  for(let i=0;i<Math.min(mine.length,truth.length);i++){ const a=mine[i],b=truth[i];
    if(Math.abs(a.frame-b.frame)>25)break; if(a.sent!==b.amt)break;
    if(a.lines>0 && !matchesIgeY(a.clearedRows,a.lines,b.y))break; vf=a.frame; }
  return {matched:mine.filter(m=>m.frame<=vf).length,total:truth.length};
}
const SESSION=process.argv[2]||"2026-07-22";
const cases=loadCases(`${SESS}/${SESSION}`);
const parsed={}; let totMatched=0,totTruth=0,rounds=0,full=0;
for(const c of cases){
  if(!parsed[c.file]) parsed[c.file]=JSON.parse(readFileSync(`${SESS}/${SESSION}/${c.file}`,"utf8"));
  const rp=parsed[c.file].replay.rounds[c.round]; const player=rp.find(p=>p.username===c.user); if(!player)continue;
  let recs; try{recs=oracleRecords(player,rp);}catch{continue;}
  const v=vIndex(recs,c.truth); totMatched+=v.matched; totTruth+=v.total; rounds++;
  if(v.matched===v.total && v.total>0) full++;
}
console.log(`ORACLE v2 [${SESSION}]: ${totMatched}/${totTruth} = ${(100*totMatched/totTruth).toFixed(1)}%  full-round: ${full}/${rounds}`);

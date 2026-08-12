// Compare the FULL 40-row board (not just bottom 20) sim vs Triangle, to find the TRUE first
// divergence including upper rows of tall stacks. Classifies: garbage-count, or pure placement,
// and whether the FIRST divergence is a row(height) or col difference in the diverging piece.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { Classes } from "@haelp/teto";
const Game = Classes.Game;
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
const ROOT=fileURLToPath(new URL("../../",import.meta.url)); const SESS=`${ROOT}sessions`;
const TL={g:0.02,boardwidth:10,boardheight:20,kickset:"SRS+",bagtype:"7-bag",combotable:"multiplier",spinbonuses:"T-spins",garbageblocking:"combo blocking",garbagetargetbonus:"none",clutch:false,stock:0,garbagemultiplier:1,garbagespeed:20,garbageholesize:1,messiness_change:1,messiness_nosame:false,messiness_timeout:0,messiness_inner:0,messiness_center:false,garbageabsolutecap:0,garbagecapincrease:0,garbagecapmax:40,garbagecap:8,garbagecapmargin:0,usebombs:false,roundmode:"down",openerphase:0,garbagespecialbonus:false,allclears:true,allclear_garbage:10,allclear_b2b:0,b2bcharging:false,infinite_movement:false,lockresets:15,locktime:30,gravitymay20g:false,allow180:true,allow_harddrop:true,display_hold:true,can_undo:false,can_retry:false,infinite_hold:false,stride:false,passthrough:"zero"};
// full 40-row encode from Triangle board.state (y-up): sim row = 39 - y
const triFull=(st)=>{ const g=Array.from({length:40},()=>".".repeat(10).split("")); for(let y=0;y<st.length&&y<40;y++){const sr=39-y; for(let c=0;c<10;c++){const t=st[y]?.[c]; g[sr][c]=t==null?".":t.mino==="gb"?"G":"#";}} return g.map(r=>r.join("")).join(""); };
const simFull=(b)=>{ let o=""; for(let r=0;r<40;r++)for(let c=0;c<10;c++){const x=b[r][c]; o+=x==null?".":x==="G"?"G":"#";} return o; };
const gc=(s)=>(s.match(/G/g)||[]).length;
const dirs=readdirSync(SESS).filter(x=>existsSync(`${SESS}/${x}`)&&readdirSync(`${SESS}/${x}`).some(f=>f.endsWith(".ttrm"))).sort();
const cls={match:0,garbage:0,placement:0}; const firstLocks=[];
for(const dir of dirs){ let cases; try{cases=loadCases(`${SESS}/${dir}`);}catch{continue;}
  const parsed={};
  for(const c of cases){
    if(!parsed[c.file]) parsed[c.file]=JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`,"utf8"));
    const rp=parsed[c.file].replay.rounds[c.round]; const player=rp.find(p=>p.username===c.user); if(!player)continue;
    let sim; try{sim=runCase(c);}catch{continue;} if(sim.locks.length<10)continue;
    const o=player.replay.options; const players=rp.map(p=>({gameid:p.replay.options.gameid,userid:p.id,username:p.username}));
    let eng; try{eng=Game.createEngine({...TL,...o,g:o.g??TL.g},o.gameid,players);}catch{continue;}
    const byFrame=new Map(); for(const e of player.replay.events){ if(!byFrame.has(e.frame))byFrame.set(e.frame,[]); byFrame.get(e.frame).push(e);}
    // capture Triangle full board at each sim lock frame
    const nCheck=Math.min(sim.locks.length,80);
    const wantFrames=new Set(sim.locks.slice(0,nCheck).map(l=>l.frame));
    const triAt=new Map(); const maxF=sim.locks[nCheck-1].frame+2;
    try{ for(let f=0;f<=maxF;f++){ const r=eng.tick(byFrame.get(f)||[]); if(wantFrames.has(f)) triAt.set(f, triFull(eng.board.state)); if(r&&r.topout)break; } }catch{continue;}
    let found=null;
    for(let i=0;i<nCheck;i++){ const f=sim.locks[i].frame; const t=triAt.get(f); if(t===undefined)break; const s=simFull(sim.boards[i]); if(s===t)continue;
      found={i, gb: gc(s)!==gc(t)}; break; }
    if(!found) cls.match++; else { cls[found.gb?"garbage":"placement"]++; firstLocks.push(found.i); }
  }
}
firstLocks.sort((a,b)=>a-b);
console.log("FULL 40-row board sim-vs-Triangle (80 locks):");
console.log(JSON.stringify(cls));
console.log(`diverging: first-lock median ${firstLocks.length?firstLocks[Math.floor(firstLocks.length/2)]:"-"}, min ${firstLocks[0]}`);

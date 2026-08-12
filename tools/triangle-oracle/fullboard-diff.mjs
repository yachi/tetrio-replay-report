// TRUE full-40-row board differential sim vs Triangle, with the SAME recorded-hole injection oracle.mjs
// uses (raw Triangle re-rolls hole columns from its RNG; the sim and the real game use the recorded x, so
// comparing against a non-injected engine falsely flags every garbage row). Same-frame multilocks compare
// only the LAST lock of each frame.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { Classes } from "@haelp/teto";
const Game = Classes.Game;
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
const ROOT=fileURLToPath(new URL("../../",import.meta.url)); const SESS=`${ROOT}sessions`;
const TL={g:0.02,boardwidth:10,boardheight:20,kickset:"SRS+",bagtype:"7-bag",combotable:"multiplier",spinbonuses:"T-spins",garbageblocking:"combo blocking",garbagetargetbonus:"none",clutch:false,stock:0,garbagemultiplier:1,garbagespeed:20,garbageholesize:1,messiness_change:1,messiness_nosame:false,messiness_timeout:0,messiness_inner:0,messiness_center:false,garbageabsolutecap:0,garbagecapincrease:0,garbagecapmax:40,garbagecap:8,garbagecapmargin:0,usebombs:false,roundmode:"down",openerphase:0,garbagespecialbonus:false,allclears:true,allclear_garbage:10,allclear_b2b:0,b2bcharging:false,infinite_movement:false,lockresets:15,locktime:30,gravitymay20g:false,allow180:true,allow_harddrop:true,display_hold:true,can_undo:false,can_retry:false,infinite_hold:false,stride:false,passthrough:"zero"};
const simFull=(b)=>{ let o=""; for(let r=0;r<40;r++)for(let c=0;c<10;c++){const x=b[r][c];o+=x==null?".":x==="G"?"G":"#";} return o;};
const gc=(s)=>(s.match(/G/g)||[]).length;
// build a hole-injected Triangle engine (copied from oracle.mjs) and capture full 40-row boards at wanted frames
function triBoards(player, rp, wantFrames, maxF){
  const o=player.replay.options; const players=rp.map(p=>({gameid:p.replay.options.gameid,userid:p.id,username:p.username}));
  const eng=Game.createEngine({...TL,...o,g:o.g??TL.g},o.gameid,players);
  const byFrame=new Map(); for(const e of player.replay.events){ if(!byFrame.has(e.frame))byFrame.set(e.frame,[]); byFrame.get(e.frame).push(e);}
  const loads=player.replay.events.filter(e=>e.type==="ige"&&e.data?.data?.type==="garbage"&&e.data.type==="interaction").map(e=>({amt:e.data.data.amt,x:e.data.data.x,iid:e.data.data.iid}));
  const iidToX=new Map(loads.map(l=>[l.iid,l.x]));
  const holeFIFO=[]; eng.events.on("garbage.tank",(ev)=>{ const x=iidToX.has(ev.iid)?iidToX.get(ev.iid):ev.column; for(let i=0;i<ev.amount;i++)holeFIFO.push(x); });
  const holeWidth=10-(o.garbageholesize??1); const gbTile=()=>({mino:"gb",connections:0});
  const gRowIdx=()=>{ const st=eng.board.state,idx=[]; for(let r=0;r<st.length;r++) if(st[r].filter(t=>t&&t.mino==="gb").length>=holeWidth) idx.push(r); return idx; };
  let prevG=0,hi=0;
  const injectHoles=()=>{ const idx=gRowIdx(); if(idx.length>prevG){ const K=idx.length-prevG,st=eng.board.state,bottomK=idx.slice(0,K); for(let k=0;k<K;k++){ const r=bottomK[k],wantX=holeFIFO[hi+k]; const cur=st[r].findIndex(t=>t==null||t.mino!=="gb"); if(wantX!=null&&cur!==wantX){ st[r][cur]=gbTile(); st[r][wantX]=null; } } hi+=K; } prevG=idx.length; };
  const enc40=()=>{ let o2=""; const st=eng.board.state; for(let vr=0;vr<40;vr++){ const r=39-vr; for(let c=0;c<10;c++){ const t=st[r]?.[c]; o2+=t==null?".":t.mino==="gb"?"G":"#"; } } return o2; };
  const out=new Map();
  try{ for(let f=0;f<=maxF;f++){ const r=eng.tick(byFrame.get(f)||[]); injectHoles(); if(wantFrames.has(f)) out.set(f, enc40()); if(r&&r.topout)break; } }catch{}
  return out;
}
const dirs=readdirSync(SESS).filter(x=>existsSync(`${SESS}/${x}`)&&readdirSync(`${SESS}/${x}`).some(f=>f.endsWith(".ttrm"))).sort();
const cls={match:0,garbage:0,placement:0}; const firstLocks=[];
for(const dir of dirs){ let cases; try{cases=loadCases(`${SESS}/${dir}`);}catch{continue;}
  const parsed={};
  for(const c of cases){
    if(!parsed[c.file]) parsed[c.file]=JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`,"utf8"));
    const rp=parsed[c.file].replay.rounds[c.round]; const player=rp.find(p=>p.username===c.user); if(!player)continue;
    let sim; try{sim=runCase(c);}catch{continue;} if(sim.locks.length<10)continue;
    const nCheck=Math.min(sim.locks.length,80);
    const want=new Set(sim.locks.slice(0,nCheck).map(l=>l.frame));
    const tri=triBoards(player,rp,want,sim.locks[nCheck-1].frame+2);
    let found=null;
    for(let i=0;i<nCheck;i++){ const f=sim.locks[i].frame;
      if(i+1<sim.locks.length&&sim.locks[i+1].frame===f) continue;
      const t=tri.get(f); if(t===undefined)break; const s=simFull(sim.boards[i]); if(s===t)continue;
      found={i, gb: gc(s)!==gc(t)}; break; }
    if(!found) cls.match++; else { cls[found.gb?"garbage":"placement"]++; firstLocks.push(found.i); }
  }
}
firstLocks.sort((a,b)=>a-b);
console.log("TRUE full-40-row board sim-vs-Triangle (hole-injected, 80 locks):");
console.log(JSON.stringify(cls));
console.log(`diverging first-lock: median ${firstLocks.length?firstLocks[Math.floor(firstLocks.length/2)]:"-"}, min ${firstLocks[0]??"-"}`);

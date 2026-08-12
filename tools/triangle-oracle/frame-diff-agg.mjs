// Aggregate first-falling-divergence classification across the corpus, to rank which movement
// mechanic to match to Triangle first. Classifies the first PERSISTENT divergence (one that is
// still present 3 frames later, to skip 1-frame spawn/gravity-ordering blips).
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { Classes } from "@haelp/teto";
const Game = Classes.Game;
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const TL = { g:0.02,boardwidth:10,boardheight:20,kickset:"SRS+",bagtype:"7-bag",combotable:"multiplier",
  spinbonuses:"T-spins",garbageblocking:"combo blocking",garbagetargetbonus:"none",clutch:false,stock:0,
  garbagemultiplier:1,garbagespeed:20,garbageholesize:1,messiness_change:1,messiness_nosame:false,
  messiness_timeout:0,messiness_inner:0,messiness_center:false,garbageabsolutecap:0,garbagecapincrease:0,
  garbagecapmax:40,garbagecap:8,garbagecapmargin:0,usebombs:false,roundmode:"down",openerphase:0,
  garbagespecialbonus:false,allclears:true,allclear_garbage:10,allclear_b2b:0,b2bcharging:false,
  infinite_movement:false,lockresets:15,locktime:30,gravitymay20g:false,allow180:true,allow_harddrop:true,
  display_hold:true,can_undo:false,can_retry:false,infinite_hold:false,stride:false,passthrough:"zero" };
const dirs = readdirSync(SESS).filter(x=>existsSync(`${SESS}/${x}`)&&readdirSync(`${SESS}/${x}`).some(f=>f.endsWith(".ttrm"))).sort();
const cls = { none:0, colOnly:0, rowOnly:0, both:0, countMismatch:0 };
let firstFrames=[];
const N_LIMIT = 300;
for(const dir of dirs){ let cases; try{cases=loadCases(`${SESS}/${dir}`);}catch{continue;}
  const parsed={};
  for(const c of cases){
    if(!parsed[c.file]) parsed[c.file]=JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`,"utf8"));
    const rp=parsed[c.file].replay.rounds[c.round]; const player=rp.find(p=>p.username===c.user); if(!player)continue;
    const o=player.replay.options;
    const players=rp.map(p=>({gameid:p.replay.options.gameid,userid:p.id,username:p.username}));
    let eng; try{ eng=Game.createEngine({...TL,...o,g:o.g??0.02}, o.gameid, players);}catch{continue;}
    const byFrame=new Map(); for(const e of player.replay.events){ if(!byFrame.has(e.frame))byFrame.set(e.frame,[]); byFrame.get(e.frame).push(e);}
    const total=Math.min(player.replay.frames??2000, N_LIMIT);
    const tri=new Map();
    try{ for(let f=0;f<=total;f++){ const r=eng.tick(byFrame.get(f)||[]); let cells=null; try{cells=eng.falling.absoluteBlocks.map(([x,y])=>[x,39-y]);}catch{} tri.set(f,cells); if(r&&r.topout)break; } }catch{continue;}
    const sim=new Map();
    try{ runCase(c,{trace:(f,cells)=>{ sim.set(f, cells.map(z=>[z.col,z.row])); }}); }catch{continue;}
    // find first divergence that persists >=3 frames
    let first=null, kind=null;
    for(let f=0; f<=total; f++){
      const t=tri.get(f), s=sim.get(f); if(!t||!s) continue;
      const key=(a)=>a.map(z=>z.join(",")).sort().join("|");
      if(key(t)===key(s)) continue;
      // persistent?
      let persist=false;
      for(let g=f; g<=Math.min(total,f+3); g++){ const tg=tri.get(g), sg=sim.get(g); if(tg&&sg&&key(tg)!==key(sg)){persist=true;} else {persist=false;break;} }
      if(!persist) continue;
      // classify
      const tcol=new Set(t.map(z=>z[0])), scol=new Set(s.map(z=>z[0]));
      const trow=new Set(t.map(z=>z[1])), srow=new Set(s.map(z=>z[1]));
      const colDiff = t.length!==s.length || [...tcol].sort().join()!==[...scol].sort().join();
      const rowDiff = t.length!==s.length || [...trow].sort().join()!==[...srow].sort().join();
      first=f; kind = t.length!==s.length ? "countMismatch" : (colDiff&&rowDiff)?"both":colDiff?"colOnly":"rowOnly";
      break;
    }
    if(first==null) cls.none++;
    else { cls[kind]++; firstFrames.push(first); }
  }
}
firstFrames.sort((a,b)=>a-b);
console.log("first PERSISTENT falling-piece divergence, classified over the corpus:");
console.log(JSON.stringify(cls,null,1));
console.log(`median first-divergence frame: ${firstFrames.length?firstFrames[Math.floor(firstFrames.length/2)]:"-"}, min ${firstFrames[0]}, count ${firstFrames.length}`);

const STRICT = process.env.LOOSE !== '1';
/**
 * Run the forecast metric, but ONLY over the verified prefix of each round.
 * The opponent's ige stream gives a per-attack oracle; a T-spin is counted only if it occurs
 * before the first attack divergence, i.e. on a board still provably matching the real game.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
import { forecastMetric, type ForecastKind } from './forecast.ts';
const DIR=(process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);
const opts={garbagespeed:30,garbagecap:8,locktime:30,gravity:0.02,sdfMode:'abs' as const,
            insertMode:'onPlace' as const,cancelMode:'all' as const};

const byUser:Record<string,{tot:Record<ForecastKind,number>;tspins:number;verifiedPieces:number;
  totalPieces:number;seps:number[]}> = {};
let roundsUsed=0, verifiedLocks=0, totalLocks=0;
const ALL:any[]=[];
for(const file of readdirSync(DIR).filter(f=>f.endsWith('.ttrm')).sort()){
  const d=JSON.parse(readFileSync(`${DIR}/${file}`,'utf8'));
  for(const rnd of d.replay.rounds){ if(rnd.length!==2) continue;
    const P=rnd.map((p:any)=>({p,rp:p.replay,gameid:p.replay.options.gameid}));
    for(const [me,other] of [[P[0],P[1]],[P[1],P[0]]] as any[]){
      const ev=me.rp.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
        .map((e:any)=>({frame:e.frame,sub:e.data.subframe??0,type:e.type,key:e.data.key}));
      const gin=me.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
        .map((e:any)=>({frame:e.frame,amt:e.data.data.amt,x:e.data.data.x,size:e.data.data.size}));
      const truth=other.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'
        &&e.data.data?.type==='garbage'&&e.data.data.gameid===me.gameid)
        .map((e:any)=>({frame:e.data.data.frame??e.frame,amt:e.data.data.amt})).sort((a:any,b:any)=>a.frame-b.frame);
      const r=simulate(ev,gin,me.rp.options.handling,me.rp.options.seed,me.rp.frames,DEFAULT_TABLE,opts);
      const mine=r.records.filter(x=>x.sent>0);
      // verified prefix: frame of the last attack that matched truth in both frame and amount
      let verifiedFrame=-1;
      for(let i=0;i<Math.min(mine.length,truth.length);i++){
        if(Math.abs(mine[i]!.frame-truth[i]!.frame)<=25 && mine[i]!.sent===truth[i]!.amt) verifiedFrame=mine[i]!.frame;
        else break;
      }
      let vIdx=-1; for(let i=0;i<r.locks.length;i++) if(r.locks[i]!.frame<=verifiedFrame) vIdx=i;
      const u=me.p.username;
      byUser[u]??={tot:{forecast_garbage:0,forecast_lineclear:0,reactive:0},tspins:0,
                   verifiedPieces:0,totalPieces:0,seps:[]};
      byUser[u]!.verifiedPieces+=vIdx+1; byUser[u]!.totalPieces+=me.rp.results.stats.piecesplaced;
      verifiedLocks+=vIdx+1; totalLocks+=me.rp.results.stats.piecesplaced;
      if(vIdx<0) continue;
      roundsUsed++;
      const fm=forecastMetric(r, STRICT);
      for(const rec of fm.records){ if(rec.lockIndex>vIdx) continue;
        byUser[u]!.tot[rec.kind]++; byUser[u]!.tspins++; byUser[u]!.seps.push(rec.separation);
        ALL.push({u,...rec}); }
    }
  }
}
console.log(`=== T-Spin Forecast — verified-prefix only ===`);
console.log(`rounds contributing: ${roundsUsed}/158`);
console.log(`board coverage: ${verifiedLocks}/${totalLocks} placements (${(100*verifiedLocks/totalLocks).toFixed(1)}%) provably match the real game\n`);
for(const [u,v] of Object.entries(byUser)){
  const fc=v.tot.forecast_garbage+v.tot.forecast_lineclear;
  const med=v.seps.length?[...v.seps].sort((a,b)=>a-b)[Math.floor(v.seps.length/2)]:0;
  console.log(`${u}`);
  console.log(`  tucked T-spins on verified board : ${v.tspins}`);
  console.log(`    forecast (garbage)   : ${v.tot.forecast_garbage}`);
  console.log(`    forecast (line clear): ${v.tot.forecast_lineclear}`);
  console.log(`    reactive             : ${v.tot.reactive}`);
  console.log(`  forecast rate: ${v.tspins?(100*fc/v.tspins).toFixed(1):'n/a'}%   median setup separation: ${med} pieces`);
}

console.log('\n=== robustness cuts ===');
for(const minSep of [1,2,3,5]){
  const sub=ALL.filter(r=>r.separation>=minSep);
  const fc=sub.filter(r=>r.kind!=='reactive').length;
  console.log(`  separation >= ${minSep}: n=${String(sub.length).padStart(3)}  forecast=${String(fc).padStart(3)} (${sub.length?(100*fc/sub.length).toFixed(1):'-'}%)`);
}
const rg=ALL.filter(r=>r.roofIsGarbage);
console.log(`  roof literally IS garbage (strongest signal): ${rg.length}/${ALL.length}`);
console.log(`  separation == 1 (overhang was the immediately preceding piece): ${ALL.filter(r=>r.separation===1).length}`);
const dist:Record<number,number>={}; for(const r of ALL) dist[r.separation]=(dist[r.separation]||0)+1;
console.log('  separation distribution:', Object.entries(dist).sort((a,b)=>+a[0]-+b[0]).slice(0,10).map(([k,v])=>`${k}:${v}`).join(' '));

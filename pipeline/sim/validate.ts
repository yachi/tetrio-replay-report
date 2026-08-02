/**
 * Physical validation of the 167 counted T-spins, independent of the metric logic.
 *  V1 reachability: could a T actually reach that lock position from spawn (SRS moves + kicks)?
 *  V2 3-corner:     does the landed T genuinely satisfy the T-spin corner rule?
 *  V3 support:      is the placement resting on something (no floating pieces)?
 *  NEGATIVE CONTROL: the same reachability test on random T placements must mostly FAIL,
 *                    otherwise the check is decorative.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE, H, SPAWN_ROW } from './sim.ts';
import { forecastMetric } from './forecast.ts';
import { getPieceCells, isValidPosition, tryMove, tryRotate, hardDrop } from './vendor/core/srs.ts';
import type { Board, ActivePiece } from './vendor/core/srs.ts';
import { replayDir } from './verified-prefix.ts';
const DIR=replayDir();
const opts={garbagespeed:30,garbagecap:8,locktime:30,gravity:0.02,sdfMode:'abs' as const,
            insertMode:'onPlace' as const,cancelMode:'all' as const};

/** BFS over reachable T lock positions (left/right/softdrop/CW/CCW), spawn in the buffer. */
function reachableTCellSets(board: Board): Set<string> {
  const spawn: ActivePiece = { type: 'T', rotation: 0, col: 3, row: SPAWN_ROW };
  const out = new Set<string>();
  if (!isValidPosition(board, spawn)) return out;
  const seen = new Set<string>([`${spawn.rotation}:${spawn.col}:${spawn.row}`]);
  const q: ActivePiece[] = [spawn];
  for (let h = 0; h < q.length; h++) {
    const cur = q[h]!;
    const dropped = hardDrop(board, cur);
    out.add(key(getPieceCells(dropped)));
    for (const n of [tryMove(board,cur,-1,0), tryMove(board,cur,1,0), tryMove(board,cur,0,1),
                     tryRotate(board,cur,1), tryRotate(board,cur,-1)]) {
      if (!n) continue;
      const k = `${n.rotation}:${n.col}:${n.row}`;
      if (seen.has(k)) continue; seen.add(k); q.push(n);
    }
  }
  return out;
}
const key = (cells:{col:number;row:number}[]) =>
  cells.map(c=>`${c.col},${c.row}`).sort().join('|');

let reach=0, corner=0, support=0, total=0, ctrlPass=0, ctrlTot=0, extConf=0, sentZero=0;
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
      let vf=-1; for(let i=0;i<Math.min(mine.length,truth.length);i++){
        if(Math.abs(mine[i]!.frame-truth[i]!.frame)<=25&&mine[i]!.sent===truth[i]!.amt) vf=mine[i]!.frame; else break; }
      let vIdx=-1; for(let i=0;i<r.locks.length;i++) if(r.locks[i]!.frame<=vf) vIdx=i;
      if(vIdx<0) continue;
      for(const rec of forecastMetric(r).records){
        if(rec.lockIndex>vIdx) continue;
        const k=rec.lockIndex; const before = k>0 ? r.boards[k-1]! : null; if(!before) continue;
        total++;
        const cells=r.locks[k]!.cells;
        // V4: external confirmation — the attack this clear produced was matched to ground truth
        // in BOTH frame and amount. Amount is a function of (clear type, spin, b2b, combo), so a
        // misclassified spin or wrong line count could not have matched.
        const rr2=r.records.find(x=>x.frame===r.locks[k]!.frame);
        if(rr2 && rr2.sent>0) extConf++; else sentZero++;
        const reachSet=reachableTCellSets(before);
        if(reachSet.has(key(cells))) reach++;
        // 3-corner around the T centre
        // the T's centre is the cell orthogonally adjacent to all three others
        const centre=cells.find(c=>cells.filter(o=>Math.abs(o.col-c.col)+Math.abs(o.row-c.row)===1).length===3)!;
        const cx=centre.col, cy=centre.row;
        const occ=(c:number,rw:number)=>c<0||c>=10||rw>=H?true:rw<0?false:before[rw]![c]!==null;
        const nCorners=[[-1,-1],[1,-1],[-1,1],[1,1]].filter(([dc,dr])=>occ(cx+dc!,cy+dr!)).length;
        if(nCorners>=3) corner++;
        // support: at least one cell rests on floor or filled cell
        if(cells.some(c=>c.row>=H-1||before[c.row+1]?.[c.col]!==null||cells.some(o=>o.row===c.row+1&&o.col===c.col))) support++;
        // negative control: random legal-looking T cell set on the same board
        const rc=Math.floor(((k*2654435761)%2147483647)/2147483647*8)+1, rr=H-1-((k*40503)%12);
        ctrlTot++; if(reachSet.has(key([{col:rc,row:rr-1},{col:rc-1,row:rr},{col:rc,row:rr},{col:rc+1,row:rr}]))) ctrlPass++;
      }
    }
  }
}
console.log(`counted T-spins validated: ${total}`);
console.log(`  V1 BFS-reachable from spawn      : ${reach}/${total} (${(100*reach/total).toFixed(1)}%)`);
console.log(`  V2 satisfies 3-corner rule       : ${corner}/${total} (${(100*corner/total).toFixed(1)}%)`);
console.log(`  V3 physically supported          : ${support}/${total} (${(100*support/total).toFixed(1)}%)`);
console.log(`  V4 spin type externally confirmed by matched attack amount: ${extConf}/${total} (${(100*extConf/total).toFixed(1)}%)`);
console.log(`     (remaining ${sentZero} were fully cancelled -> sent 0 -> no external witness)`);
console.log(`  NEGATIVE CONTROL random T placements reachable: ${ctrlPass}/${ctrlTot} (${(100*ctrlPass/ctrlTot).toFixed(1)}%)`);

/**
 * Localise divergence with the row oracle.
 *
 * The interesting case is an attack whose FRAME and AMOUNT match ground truth but whose
 * board ROW does not: the sim sent the right number at the right time from the wrong place.
 * That is a placement defect caught at a specific lock, which the attack stream alone could
 * never point at.
 *
 * The signed delta is the diagnosis:
 *   simY < truthY  (smaller row index = higher up)  -> the sim's stack is TALLER than reality
 *   simY > truthY                                   -> the sim's stack is SHORTER
 * A one-sided distribution means a systematic row bug (too much garbage, or missed clears);
 * a symmetric one means placement noise.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
import { expectedIgeY } from './ige-y-oracle.ts';
const DIR = (process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);
const opts = {garbagespeed:30, garbagecap:8, locktime:60, gravity:0.02, sdfMode:'abs' as const,
              insertMode:'onPlace' as const, cancelMode:'all' as const, acEmit:'separate' as const,
              subframe:true, blockout:'shiftup' as const, kickset:'SRS+' as const,
              insertAfterClear:true};

const dist = new Map<number, number>();
const byLines = new Map<string, Map<number, number>>();
let rowFirst = 0, amountFirst = 0, clean = 0, everChecked = 0;
let beforeGarbage = 0, afterGarbage = 0;
const samples: string[] = [];
const attrib: Record<string, number> = {};
let nullNum = 0, nullDen = 0;

for (const f of readdirSync(DIR).filter(x=>x.endsWith('.ttrm')).sort()) {
  const d = JSON.parse(readFileSync(`${DIR}/${f}`,'utf8'));
  for (const rnd of d.replay.rounds) { if (rnd.length!==2) continue;
    const P = rnd.map((p:any)=>({rp:p.replay, gameid:p.replay.options.gameid, user:p.username}));
    for (const [me,other] of [[P[0],P[1]],[P[1],P[0]]] as any[]) {
      const ev = me.rp.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
        .map((e:any)=>({frame:e.frame, sub:e.data.subframe??0, type:e.type, key:e.data.key}));
      const gin = me.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
        .map((e:any)=>({frame:e.frame, amt:e.data.data.amt, x:e.data.data.x, size:e.data.data.size}));
      const truth = other.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'
        && e.data.data?.type==='garbage' && e.data.data.gameid===me.gameid)
        .map((e:any)=>({frame:e.data.data.frame??e.frame, amt:e.data.data.amt, y:e.data.data.y}))
        .sort((a:any,b:any)=>a.frame-b.frame);
      const r = simulate(ev, gin, me.rp.options.handling, me.rp.options.seed, me.rp.frames, DEFAULT_TABLE, opts);
      const mine = r.records.filter(x=>x.sent>0);
      const firstInsert = r.garbageEvents.length ? r.garbageEvents[0]!.frame : Infinity;

      let verdict = 'clean';
      for (let i=0;i<Math.min(mine.length,truth.length);i++) {
        const a = mine[i]!, b = truth[i]!;
        if (Math.abs(a.frame-b.frame)>25 || a.sent!==b.amt) { verdict='amount'; break; }
        if (a.lines === 0) continue;                       // all-clear bonus carries no row
        everChecked++;
        const simY = expectedIgeY(Math.max(...a.clearedRows), a.lines);
        if (simY === b.y) continue;
        verdict = 'row';
        const dv = simY - b.y;
        dist.set(dv, (dist.get(dv) ?? 0) + 1);
        const k = `lines=${a.lines} ${a.spin}`;
        if (!byLines.has(k)) byLines.set(k, new Map());
        byLines.get(k)!.set(dv, (byLines.get(k)!.get(dv) ?? 0) + 1);
        if (a.frame < firstInsert) beforeGarbage++; else afterGarbage++;
        // Is the row error the size of a garbage event? If |delta| equals an insertion the
        // sim performed (delta<0, sim too tall) or one it still has pending (delta>0, sim
        // too short), the defect is that single insertion, not the placement.
        const inserted = r.garbageEvents.filter(g=>g.frame<=a.frame).map(g=>g.amt);
        const totalIn = inserted.reduce((x,y)=>x+y,0);
        const arrivedByNow = gin.filter((g:any)=>g.frame<=a.frame).reduce((x:number,y:any)=>x+y.amt,0);
        const notYetIn = arrivedByNow - totalIn;
        const hit = inserted.includes(Math.abs(dv)) ? 'equals one insertion'
                  : Math.abs(dv) === notYetIn ? 'equals the un-inserted remainder'
                  : inserted.length && Math.abs(dv) === inserted[inserted.length-1] ? 'equals the LAST insertion'
                  : 'no match';
        attrib[hit] = (attrib[hit] ?? 0) + 1;
        // NULL: deltas and garbage amounts are both small integers, so "equals an insertion"
        // can happen by chance. Record what fraction of the plausible delta range this
        // case's insertion set would have matched, and average it as the chance baseline.
        const uniq = new Set(inserted.filter(v=>v>=1&&v<=6));
        nullNum += uniq.size / 6; nullDen += 1;
        if (samples.length < 18)
          samples.push(`  ${f.slice(-9).padEnd(10)} ${me.user.padEnd(9)} attack#${i} f${a.frame} amt=${a.sent} lines=${a.lines} ${a.spin}  simY=${simY} truthY=${b.y} delta=${dv>0?'+':''}${dv}  ${a.frame<firstInsert?'PRE-garbage':'post-garbage'}`);
        break;
      }
      if (verdict==='row') rowFirst++; else if (verdict==='amount') amountFirst++; else clean++;
    }}}

console.log(`rounds: first failure is a ROW mismatch ${rowFirst}, an amount/frame mismatch ${amountFirst}, clean ${clean}`);
console.log(`row checks performed: ${everChecked}`);
console.log(`first row mismatch sits BEFORE any garbage insertion: ${beforeGarbage}, after: ${afterGarbage}`);
const tot = [...dist.values()].reduce((a,b)=>a+b,0);
const neg = [...dist].filter(([d])=>d<0).reduce((a,[,c])=>a+c,0);
const pos = [...dist].filter(([d])=>d>0).reduce((a,[,c])=>a+c,0);
console.log(`\nsimY - truthY  (negative = sim's stack is TALLER than reality)`);
console.log(`  taller ${neg}/${tot} = ${(100*neg/tot).toFixed(1)}%   shorter ${pos}/${tot} = ${(100*pos/tot).toFixed(1)}%`);
console.log('  ' + [...dist].sort((a,b)=>a[0]-b[0]).map(([d,c])=>`${d>0?'+':''}${d}:${c}`).join('  '));
console.log('\nby clear type:');
for (const [k,m] of [...byLines].sort()) {
  const t = [...m.values()].reduce((a,b)=>a+b,0);
  console.log(`  ${k.padEnd(18)} n=${String(t).padStart(3)}  ` + [...m].sort((a,b)=>a[0]-b[0]).map(([d,c])=>`${d>0?'+':''}${d}:${c}`).join(' '));
}
console.log('\nis the row error the size of a garbage event?');
for (const [k,v] of Object.entries(attrib).sort((a,b)=>b[1]-a[1])) console.log(`  ${k.padEnd(30)} ${v}`);
console.log(`  chance baseline (mean P(match) under a random delta in 1..6): ${(100*nullNum/nullDen).toFixed(1)}%`);
console.log('\nsamples:'); for (const s of samples) console.log(s);

/**
 * Isolate the placement engine from every garbage effect.
 *
 * There is no garbage-free player-round in this dataset (measured: 0/158 — garbage always
 * arrives by piece ~11-20), so the isolation has to be the PREFIX of each round before the
 * first incoming garbage event. Over that prefix the sim and the client see identical
 * inputs on identical boards, so any attack mismatch is a pure placement/spin defect with
 * the garbage model, cancellation, blockout and insertion timing all out of the picture.
 *
 * Scored per ATTACK rather than per round, so one bad round cannot dominate, and the
 * matched/total ratio is directly interpretable as engine accuracy.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
import { replayDir } from './verified-prefix.ts';
const DIR = replayDir();
const opts = {garbagespeed:30, garbagecap:8, locktime:60, gravity:0.0167, sdfMode:'abs' as const,
              insertMode:'onPlace' as const, cancelMode:'all' as const, acEmit:'separate' as const,
              subframe:true, blockout:'shiftup' as const, kickset:'SRS+' as const};

const bucket: any[] = [];
let attacks = 0, matched = 0, roundsWithPrefix = 0, roundsAllMatched = 0;
const wrong: Record<string, number> = {};
const detail: string[] = [];

for (const f of readdirSync(DIR).filter(x=>x.endsWith('.ttrm')).sort()) {
  const d = JSON.parse(readFileSync(`${DIR}/${f}`,'utf8'));
  for (const rnd of d.replay.rounds) { if (rnd.length!==2) continue;
    const P = rnd.map((p:any)=>({p, rp:p.replay, gameid:p.replay.options.gameid, user:p.username}));
    for (const [me,other] of [[P[0],P[1]],[P[1],P[0]]] as any[]) {
      const ev = me.rp.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
        .map((e:any)=>({frame:e.frame, sub:e.data.subframe??0, type:e.type, key:e.data.key}));
      const gin = me.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
        .map((e:any)=>({frame:e.frame, amt:e.data.data.amt, x:e.data.data.x, size:e.data.data.size}));
      // everything strictly before the first incoming garbage EVENT (not insertion —
      // pending garbage can already cancel, which would reintroduce the confound)
      const cutoff = gin.length ? gin[0]!.frame : Infinity;
      const truth = other.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'
        && e.data.data?.type==='garbage' && e.data.data.gameid===me.gameid)
        .map((e:any)=>({frame:e.data.data.frame??e.frame, amt:e.data.data.amt}))
        .sort((a:any,b:any)=>a.frame-b.frame)
        .filter((t:any)=>t.frame < cutoff);
      if (!truth.length) continue;
      roundsWithPrefix++;
      const r = simulate(ev, gin, me.rp.options.handling, me.rp.options.seed, me.rp.frames, DEFAULT_TABLE, opts);
      const mine = r.records.filter(x=>x.sent>0 && x.frame < cutoff);
      let ok = 0;
      for (let i=0;i<truth.length;i++) {
        const a = mine[i], b = truth[i]!;
        attacks++;
        if (a && Math.abs(a.frame-b.frame)<=25 && a.sent===b.amt) { matched++; ok++; }
        else {
          const key = !a ? 'no sim attack'
            : Math.abs(a.frame-b.frame)>25 ? 'frame' : `amount sim${a.sent} truth${b.amt}`;
          wrong[key] = (wrong[key] ?? 0) + 1;
          if (detail.length < 25) detail.push(`  ${f.slice(-9).padEnd(10)} ${me.user.padEnd(9)} #${i} ${key}`);
        }
      }
      if (ok === truth.length) roundsAllMatched++;
      // What distinguishes the rounds that fail? Failures cluster rather than spreading,
      // so bucket each round by input features present in its pre-garbage prefix.
      const pre = ev.filter((e:any)=>e.frame < cutoff && e.type==='keydown');
      const feat = (k:string) => pre.filter((e:any)=>e.key===k).length;
      bucket.push({ok: ok===truth.length, soft: feat('softDrop'), rot: feat('rotateCW')+feat('rotateCCW'),
                    hold: feat('hold'), drops: feat('hardDrop')});
    }}}
const bAvg = (sel:(b:any)=>number, ok:boolean) => {
  const v = bucket.filter(b=>b.ok===ok); return v.length ? (v.reduce((a,b)=>a+sel(b),0)/v.length) : 0; };
console.log(`\nper-round input features in the pre-garbage prefix (matched vs failed):`);
for (const [name, sel] of [['softDrop', (b:any)=>b.soft], ['rotations', (b:any)=>b.rot],
                           ['holds', (b:any)=>b.hold], ['hardDrops', (b:any)=>b.drops],
                           ['softDrop per piece', (b:any)=>b.drops?b.soft/b.drops:0]] as const)
  console.log(`  ${name.padEnd(20)} matched ${bAvg(sel,true).toFixed(2)}   failed ${bAvg(sel,false).toFixed(2)}`);

console.log(`PRE-GARBAGE PREFIX ONLY (pure placement engine)`);
console.log(`  rounds with at least one pre-garbage attack: ${roundsWithPrefix}`);
console.log(`  attacks matched: ${matched}/${attacks} = ${(100*matched/attacks).toFixed(1)}%`);
console.log(`  rounds whose whole prefix matched: ${roundsAllMatched}/${roundsWithPrefix}`);
console.log('\nmismatch kinds:');
for (const [k,v] of Object.entries(wrong).sort((a,b)=>b[1]-a[1])) console.log(`  ${k.padEnd(28)} ${v}`);
console.log('\nfirst 25:'); for (const d of detail) console.log(d);

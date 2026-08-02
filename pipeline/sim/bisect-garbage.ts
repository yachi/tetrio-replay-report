/**
 * Where exactly does the sim first diverge, relative to the first garbage insertion?
 *
 * Oracle: the opponent's ige stream timestamps every attack I sent. Walk my attacks
 * against it and report the FIRST mismatch — its frame, sim amount vs truth amount,
 * and how many locks / frames separate it from the first garbage insertion.
 *
 *   mismatch BEFORE first insert   -> the defect is not garbage at all
 *   mismatch AT the insert lock    -> insertion CONTENT is wrong (hole column, amount)
 *   mismatch a few locks AFTER     -> insertion TIMING is wrong
 *
 * Never localise a board bug from an attack delta alone (attack values cascade through
 * B2B and combo), so this reports the raw distance and lets the histogram speak.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
import { replayDir } from './verified-prefix.ts';
const DIR = replayDir();
const opts = {garbagespeed:30, garbagecap:8, locktime:60, gravity:0.0167, sdfMode:'abs' as const,
              insertMode:'onPlace' as const, cancelMode:'all' as const, acEmit:'separate' as const,
              subframe: process.env.SUBFRAME !== '0', blockout:'shiftup' as const, kickset:'SRS+' as const};

type R = { file:string; user:string; firstBadIdx:number; badFrame:number; simAmt:number; truthAmt:number;
           reason:string; insertFrame:number; locksBetween:number; nAttacks:number; nTruth:number };
const out: R[] = [];

for (const f of readdirSync(DIR).filter(x=>x.endsWith('.ttrm')).sort()) {
  const d = JSON.parse(readFileSync(`${DIR}/${f}`,'utf8'));
  for (const rnd of d.replay.rounds) { if (rnd.length!==2) continue;
    const P = rnd.map((p:any)=>({p, rp:p.replay, gameid:p.replay.options.gameid, user:p.username}));
    for (const [me,other] of [[P[0],P[1]],[P[1],P[0]]] as any[]) {
      const ev = me.rp.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
        .map((e:any)=>({frame:e.frame, sub:e.data.subframe??0, type:e.type, key:e.data.key}));
      const gin = me.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
        .map((e:any)=>({frame:e.frame, amt:e.data.data.amt, x:e.data.data.x, size:e.data.data.size}));
      const truth = other.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'
        && e.data.data?.type==='garbage' && e.data.data.gameid===me.gameid)
        .map((e:any)=>({frame:e.data.data.frame??e.frame, amt:e.data.data.amt}))
        .sort((a:any,b:any)=>a.frame-b.frame);
      const r = simulate(ev, gin, me.rp.options.handling, me.rp.options.seed, me.rp.frames, DEFAULT_TABLE, opts);
      const mine = r.records.filter(x=>x.sent>0);
      const insertFrame = r.garbageEvents.length ? r.garbageEvents[0]!.frame : Infinity;

      let bad = -1, reason = 'none', simAmt = -1, truthAmt = -1, badFrame = -1;
      for (let i=0;i<Math.max(mine.length,truth.length);i++) {
        const a = mine[i], b = truth[i];
        if (!a && !b) break;
        if (!a) {
          // Confounder: if the sim is already dead, EVERY later truth attack is "missing".
          // That is death, not a divergence — label it so it cannot masquerade as one.
          const lastLock = r.locks.length ? r.locks[r.locks.length-1]!.frame : -1;
          // Second confounder: "no attack" can mean "cleared nothing" OR "cleared but the
          // whole attack was cancelled by pending garbage". Those are different bugs —
          // a board defect vs a cancellation-model defect — so separate them here.
          const nearby = r.records.some(x => Math.abs(x.frame - b!.frame) <= 25 && x.lines > 0);
          bad=i; reason = (r.topout && b!.frame > lastLock) ? 'sim already dead'
                        : nearby ? 'sim cleared but cancelled to 0' : 'sim cleared nothing';
          badFrame=b!.frame; truthAmt=b!.amt; break;
        }
        if (!b) { bad=i; reason='sim spurious attack'; badFrame=a.frame; simAmt=a.sent; break; }
        if (Math.abs(a.frame-b.frame)>25) { bad=i; reason='frame'; badFrame=a.frame; simAmt=a.sent; truthAmt=b.amt; break; }
        if (a.sent!==b.amt) { bad=i; reason='amount'; badFrame=a.frame; simAmt=a.sent; truthAmt=b.amt; break; }
      }
      // how many of the sim's locks sit between the first insertion and the first bad attack
      let locksBetween = -1;
      if (bad>=0 && insertFrame<Infinity) {
        locksBetween = r.locks.filter(l=>l.frame>insertFrame && l.frame<=badFrame).length;
        if (badFrame < insertFrame) locksBetween = -r.locks.filter(l=>l.frame>badFrame && l.frame<=insertFrame).length;
      }
      out.push({file:f, user:me.user, firstBadIdx:bad, badFrame, simAmt, truthAmt, reason,
                insertFrame, locksBetween, nAttacks:mine.length, nTruth:truth.length});
    }}}

const clean = out.filter(r=>r.firstBadIdx>=0);
console.log(`rounds ${out.length}   with a first-mismatch ${clean.length}   fully matching ${out.length-clean.length}`);

const by = (k:(r:R)=>string) => { const m=new Map<string,number>(); for(const r of clean) m.set(k(r),(m.get(k(r))??0)+1);
  return [...m].sort((a,b)=>b[1]-a[1]); };
console.log('\nfirst-mismatch reason:');
for (const [k,v] of by(r=>r.reason)) console.log(`  ${k.padEnd(22)} ${v}`);

console.log('\nfirst mismatch vs first garbage insertion:');
const before = clean.filter(r=>r.badFrame < r.insertFrame).length;
const noIns  = clean.filter(r=>r.insertFrame===Infinity).length;
const atIns  = clean.filter(r=>r.insertFrame<Infinity && r.locksBetween===0).length;
const after  = clean.filter(r=>r.insertFrame<Infinity && r.locksBetween>0).length;
console.log(`  mismatch BEFORE any insertion : ${before}`);
console.log(`  round never inserted garbage  : ${noIns}`);
console.log(`  mismatch AT the insert lock   : ${atIns}`);
console.log(`  mismatch AFTER insertion      : ${after}`);
const dist = clean.filter(r=>r.locksBetween>0).map(r=>r.locksBetween).sort((a,b)=>a-b);
if (dist.length) console.log(`  locks between insert and mismatch: median ${dist[Math.floor(dist.length/2)]}  p90 ${dist[Math.floor(dist.length*0.9)]}  max ${dist[dist.length-1]}`);

// The cleanest signal: rounds that diverge with NO garbage on the board yet.
const pre = clean.filter(r=>r.badFrame < r.insertFrame);
console.log(`\n=== ${pre.length} rounds diverge BEFORE any garbage — pure placement-engine defects ===`);
const pm=new Map<string,number>(); for(const r of pre) pm.set(r.reason,(pm.get(r.reason)??0)+1);
for (const [k,v] of [...pm].sort((a,b)=>b[1]-a[1])) console.log(`  ${k.padEnd(22)} ${v}`);
for (const r of pre.slice(0,20))
  console.log(`  ${r.file.slice(-9).padEnd(10)} ${r.user.padEnd(9)} attack#${String(r.firstBadIdx).padStart(2)} ${r.reason.padEnd(19)} sim ${String(r.simAmt).padStart(3)} truth ${String(r.truthAmt).padStart(3)}  frame ${r.badFrame}`);

console.log('\nfirst 15 mismatches after insertion:');
for (const r of clean.filter(r=>r.locksBetween>=0).slice(0,15))
  console.log(`  ${r.file.slice(-9).padEnd(10)} ${r.user.padEnd(9)} idx ${String(r.firstBadIdx).padStart(2)} ${r.reason.padEnd(20)} sim ${String(r.simAmt).padStart(3)} truth ${String(r.truthAmt).padStart(3)}  +${r.locksBetween} locks after insert`);

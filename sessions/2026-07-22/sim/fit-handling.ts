/**
 * Fit DAS/ARR from ground truth instead of trusting the recorded handling values.
 *
 * All 158 rounds declare handling {das:10, arr:2, sdf:20, dcd:0}. If the sim's clock
 * interprets those correctly, coverage should peak AT das=10, arr=2. A peak somewhere
 * else means the interpretation is wrong (units, off-by-one, or when the charge starts),
 * and the offset says which.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
const DIR = (process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);
const base = {garbagespeed:30, garbagecap:8, locktime:30, gravity:0.02, sdfMode:'abs' as const,
              insertMode:'onPlace' as const, cancelMode:'all' as const, acEmit:'separate' as const,
              subframe:true};

// preload once; the sweep is over ~30 configs
type Case = { ev:any[]; gin:any[]; truth:any[]; handling:any; seed:number; frames:number; placed:number };
const cases: Case[] = [];
for (const f of readdirSync(DIR).filter(x=>x.endsWith('.ttrm')).sort()) {
  const d = JSON.parse(readFileSync(`${DIR}/${f}`,'utf8'));
  for (const rnd of d.replay.rounds) { if (rnd.length!==2) continue;
    const P = rnd.map((p:any)=>({p, rp:p.replay, gameid:p.replay.options.gameid}));
    for (const [me,other] of [[P[0],P[1]],[P[1],P[0]]] as any[]) {
      cases.push({
        ev: me.rp.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
          .map((e:any)=>({frame:e.frame, sub:e.data.subframe??0, type:e.type, key:e.data.key})),
        gin: me.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
          .map((e:any)=>({frame:e.frame, amt:e.data.data.amt, x:e.data.data.x, size:e.data.data.size})),
        truth: other.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'
          && e.data.data?.type==='garbage' && e.data.data.gameid===me.gameid)
          .map((e:any)=>({frame:e.data.data.frame??e.frame, amt:e.data.data.amt}))
          .sort((a:any,b:any)=>a.frame-b.frame),
        handling: me.rp.options.handling, seed: me.rp.options.seed,
        frames: me.rp.frames, placed: me.rp.results.stats.piecesplaced });
    }}}

const score = (das:number, arr:number) => {
  let ver=0, real=0, lines=0;
  for (const c of cases) {
    const r = simulate(c.ev, c.gin, {...c.handling, das, arr}, c.seed, c.frames, DEFAULT_TABLE, base);
    const mine = r.records.filter(x=>x.sent>0);
    let vf=-1;
    for (let i=0;i<Math.min(mine.length,c.truth.length);i++) {
      if (Math.abs(mine[i]!.frame-c.truth[i]!.frame)<=25 && mine[i]!.sent===c.truth[i]!.amt) vf=mine[i]!.frame; else break;
    }
    let vIdx=-1; for (let i=0;i<r.locks.length;i++) if (r.locks[i]!.frame<=vf) vIdx=i;
    ver += vIdx+1; real += c.placed; lines += r.lines;
  }
  return {cov: 100*ver/real, lines};
};

console.log(`declared handling: das=${cases[0]!.handling.das} arr=${cases[0]!.handling.arr}\n`);
const dases = [6,8,9,10,11,12];
const arrs  = [1,1.5,2,2.5,3];
let best = {cov:-1, das:0, arr:0};
console.log('cov%    ' + arrs.map(a=>`arr=${a}`.padStart(8)).join(''));
for (const das of dases) {
  const row: string[] = [];
  for (const arr of arrs) {
    const s = score(das, arr);
    if (s.cov > best.cov) best = {cov:s.cov, das, arr};
    row.push(s.cov.toFixed(1).padStart(8));
  }
  console.log(`das=${String(das).padEnd(4)}` + row.join(''));
}
console.log(`\nbest: das=${best.das} arr=${best.arr} -> ${best.cov.toFixed(1)}%`);

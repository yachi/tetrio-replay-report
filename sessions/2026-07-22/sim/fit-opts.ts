/**
 * Coordinate ascent over every semantic knob in sim.ts, scored by verified-prefix
 * coverage against the opponent's ige stream.
 *
 * Hand-simulating one piece at a time was not converging: each knob is individually
 * plausible and the interactions are what matter. This sweeps them jointly and reports
 * which ones actually move the number, so dead knobs can be deleted rather than kept
 * as untested hypotheses (see insertAfterClear, which sat unset in the opts type).
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
const DIR = (process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);

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

const score = (o:any) => {
  let ver=0, real=0;
  for (const c of cases) {
    const r = simulate(c.ev, c.gin, c.handling, c.seed, c.frames, DEFAULT_TABLE, o);
    const mine = r.records.filter(x=>x.sent>0);
    let vf=-1;
    for (let i=0;i<Math.min(mine.length,c.truth.length);i++) {
      if (Math.abs(mine[i]!.frame-c.truth[i]!.frame)<=25 && mine[i]!.sent===c.truth[i]!.amt) vf=mine[i]!.frame; else break;
    }
    let vIdx=-1; for (let i=0;i<r.locks.length;i++) if (r.locks[i]!.frame<=vf) vIdx=i;
    ver += vIdx+1; real += c.placed;
  }
  return 100*ver/real;
};

let cur: any = {garbagespeed:30, garbagecap:8, locktime:30, gravity:0.02, sdfMode:'abs',
                insertMode:'onPlace', cancelMode:'all', acEmit:'separate', subframe:true};
const KNOBS: [string, any[]][] = [
  ['subframe',        [true, false]],
  ['eventsFirst',     [false, true]],
  ['blockout',        ['strict','shiftup','clutch']],
  ['insertMode',      ['onPlace','immediate']],
  ['insertAfterClear',[false, true]],
  ['cancelMode',      ['all','inTransit']],
  ['arriveFrame',     ['outer','ige']],
  ['garbagespeed',    [0, 10, 20, 30, 40, 60]],
  ['garbagecap',      [4, 6, 8, 10, 12, 20]],
  ['locktime',        [30, 60]],
  ['gravity',         [0.02, 0.0167, 0.05]],
  ['sdfMode',         ['abs','mult']],
  ['are',             [0, 7]],
  ['lineclearAre',    [0, 7, 25]],
  ['irs',             [false, true]],
  ['ihs',             [false, true]],
  ['acMode',          ['flat','b2bonly','none','replace']],
];

let bestScore = score(cur);
console.log(`baseline ${bestScore.toFixed(2)}%`);
for (let pass = 1; pass <= 2; pass++) {
  let improved = false;
  for (const [k, vals] of KNOBS) {
    let bv = cur[k], bs = bestScore;
    for (const v of vals) {
      if (v === cur[k]) continue;
      const s = score({...cur, [k]: v});
      if (s > bs + 1e-9) { bs = s; bv = v; }
    }
    if (bs > bestScore + 1e-9) {
      console.log(`  pass${pass} ${k}: ${JSON.stringify(cur[k])} -> ${JSON.stringify(bv)}   ${bestScore.toFixed(2)}% -> ${bs.toFixed(2)}%`);
      cur = {...cur, [k]: bv}; bestScore = bs; improved = true;
    }
  }
  if (!improved) { console.log(`  pass${pass}: no knob improved — converged`); break; }
}
console.log(`\nbest ${bestScore.toFixed(2)}%`);
console.log(JSON.stringify(cur, null, 1));

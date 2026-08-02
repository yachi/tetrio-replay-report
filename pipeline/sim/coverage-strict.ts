/**
 * Coverage under the STRICT gate: an attack counts as reproduced only if frame, amount AND
 * the board row (ige `y`, see ige-y-oracle.ts) all agree.
 *
 * The loose gate (frame + amount) can be satisfied by a wrong board that happens to send
 * the same number at the same time — attack values collapse a lot of board state into one
 * integer. Adding y is the first per-attack constraint on WHERE the clear happened, so this
 * is the honest number and the right thing to optimise against.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
import { matchesIgeY } from './ige-y-oracle.ts';
import { replayDir } from './verified-prefix.ts';
const DIR = replayDir();

/** frame of the interaction_confirm matching a queued interaction (same cid+iid) */
const CONFIRM = (rp:any, cid:number, iid:number): number|undefined => {
  const c = rp.events.find((e:any)=>e.type==='ige' && e.data.type==='interaction_confirm'
    && e.data.data?.type==='garbage' && e.data.data.cid===cid && e.data.data.iid===iid);
  return c ? c.frame : undefined;
};

const base = {garbagespeed:30, garbagecap:8, locktime:60, gravity:0.0167, sdfMode:'abs' as const,
              insertMode:'onPlace' as const, cancelMode:'all' as const, acEmit:'separate' as const,
              blockout:'shiftup' as const, kickset:'SRS+' as const};

type Case = { ev:any[]; gin:any[]; truth:any[]; handling:any; seed:number; frames:number; placed:number };
const cases: Case[] = [];
for (const f of readdirSync(DIR).filter(x=>x.endsWith('.ttrm')).sort()) {
  const d = JSON.parse(readFileSync(`${DIR}/${f}`,'utf8'));
  for (const rnd of d.replay.rounds) { if (rnd.length!==2) continue;
    const P = rnd.map((p:any)=>({rp:p.replay, gameid:p.replay.options.gameid}));
    for (const [me,other] of [[P[0],P[1]],[P[1],P[0]]] as any[]) {
      cases.push({
        ev: me.rp.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
          .map((e:any)=>({frame:e.frame, sub:e.data.subframe??0, type:e.type, key:e.data.key})),
        gin: me.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
          .map((e:any)=>({frame:e.frame, amt:e.data.data.amt, x:e.data.data.x, size:e.data.data.size,
            confirmFrame: CONFIRM(me.rp ?? rp, e.data.data.cid, e.data.data.iid)})),
        truth: other.rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'
          && e.data.data?.type==='garbage' && e.data.data.gameid===me.gameid)
          .map((e:any)=>({frame:e.data.data.frame??e.frame, amt:e.data.data.amt, y:e.data.data.y}))
          .sort((a:any,b:any)=>a.frame-b.frame),
        handling: me.rp.options.handling, seed: me.rp.options.seed,
        frames: me.rp.frames, placed: me.rp.results.stats.piecesplaced });
    }}}

const run = (label: string, extra: any) => {
  let loose=0, strict=0, real=0, yChecked=0, yOK=0;
  for (const c of cases) {
    const r = simulate(c.ev, c.gin, c.handling, c.seed, c.frames, DEFAULT_TABLE, {...base, ...extra});
    const mine = r.records.filter(x=>x.sent>0);
    let lf=-1, sf=-1, broke=false;
    for (let i=0;i<Math.min(mine.length,c.truth.length);i++) {
      const a=mine[i]!, b=c.truth[i]!;
      const ok = Math.abs(a.frame-b.frame)<=25 && a.sent===b.amt;
      if (!ok) break;
      lf = a.frame;                       // loose prefix advances independently
      // the all-clear bonus is its own event with no clear of its own; it carries no
      // meaningful row, so only row-check events that came from an actual line clear
      if (!broke && a.lines > 0) {
        yChecked++;
        if (matchesIgeY(a.clearedRows, a.lines, b.y)) yOK++;
        else broke = true;                // strict prefix stops here; loose keeps going
      }
      if (!broke) sf = a.frame;
    }
    const idx = (f:number) => { let v=-1; for (let i=0;i<r.locks.length;i++) if (r.locks[i]!.frame<=f) v=i; return v+1; };
    loose += idx(lf); strict += idx(sf); real += c.placed;
  }
  console.log(`${label.padEnd(20)} loose ${(100*loose/real).toFixed(2)}%   STRICT ${(100*strict/real).toFixed(2)}%   row-agreement ${yOK}/${yChecked} = ${(100*yOK/yChecked).toFixed(1)}%`);
};

run('frame-clock', {subframe:false});
run('subframe', {subframe:true});
run('subframe locktime30', {subframe:true, locktime:30});
run('subframe SRS', {subframe:true, kickset:'SRS'});
run('subframe strictBlock', {subframe:true, blockout:'strict'});
// The garbage-total test (triage-garbage-totals.ts, fixed cohort) says cancellation
// should not touch garbage that has already landed — only what is still in transit.
run('+cancel inTransit', {subframe:true, cancelMode:'inTransit'});
run('+insert immediate', {subframe:true, insertMode:'immediate'});
run('+inTransit +immediate', {subframe:true, cancelMode:'inTransit', insertMode:'immediate'});
// triangle rewrites a queued entry's frame on interaction_confirm, so the confirm event is
// the real arrival time; the interaction is only the provisional announcement.
run('readyFrom=confirm', {subframe:true, readyFrom:'confirm'});
run('confirm speed0', {subframe:true, readyFrom:'confirm', garbagespeed:0});
run('confirm speed30', {subframe:true, readyFrom:'confirm', garbagespeed:30});

/**
 * Exact test of the garbage model, unconfounded by early death.
 *
 * localise-rows.ts showed the sim's board is off by a WHOLE GARBAGE EVENT at the first row
 * mismatch — 16/21 cases, against a 31.7% chance baseline (deltas and garbage amounts are
 * both small integers, so the baseline is needed). 81% of the time the sim's stack is
 * TALLER, i.e. it inserted garbage reality did not.
 *
 * `stats.garbage.received` is exact ground truth for how much garbage actually entered the
 * field over the round. It is only comparable when the sim survives the whole round, so
 * restrict to rounds where the sim placed every piece the player placed. On those the
 * comparison is exact and the garbage model is fully testable.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
const DIR = (process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);

/** frame of the interaction_confirm matching a queued interaction (same cid+iid) */
const CONFIRM = (rp:any, cid:number, iid:number): number|undefined => {
  const c = rp.events.find((e:any)=>e.type==='ige' && e.data.type==='interaction_confirm'
    && e.data.data?.type==='garbage' && e.data.data.cid===cid && e.data.data.iid===iid);
  return c ? c.frame : undefined;
};

const base = {garbagespeed:30, garbagecap:8, locktime:60, gravity:0.02, sdfMode:'abs' as const,
              insertMode:'onPlace' as const, cancelMode:'all' as const, acEmit:'separate' as const,
              subframe:true, blockout:'shiftup' as const, kickset:'SRS+' as const};

// Selection effect: each config survives a DIFFERENT set of rounds, so comparing
// exact/survived across configs compares different populations. Score every config on the
// same fixed cohort — the rounds that survive under all of them.
const CONFIGS: [string, any][] = [
  ['baseline', {}],
  ['garbagecap 4', {garbagecap:4}],
  ['garbagecap 12', {garbagecap:12}],
  ['garbagecap 20', {garbagecap:20}],
  ['speed 0', {garbagespeed:0}],
  ['speed 60', {garbagespeed:60}],
  ['cancel inTransit', {cancelMode:'inTransit'}],
  ['insert immediate', {insertMode:'immediate'}],
  ['insertAfterClear', {insertAfterClear:true}],
  ['inTransit+immediate', {cancelMode:'inTransit', insertMode:'immediate'}],
  ['inTransit+speed0', {cancelMode:'inTransit', garbagespeed:0}],
  ['readyFrom=confirm', {readyFrom:'confirm'}],
  ['confirm speed0', {readyFrom:'confirm', garbagespeed:0}],
];

type Row = { key:string; ev:any[]; gin:any[]; handling:any; seed:number; frames:number; placed:number; recv:number };
const rows: Row[] = [];
for (const f of readdirSync(DIR).filter(x=>x.endsWith('.ttrm')).sort()) {
  const d = JSON.parse(readFileSync(`${DIR}/${f}`,'utf8'));
  for (const [ri,rnd] of d.replay.rounds.entries()) { if (rnd.length!==2) continue;
    for (const me of rnd) {
      const rp = me.replay, st = rp.results.stats;
      rows.push({ key:`${f}#${ri}#${me.username}`,
        ev: rp.events.filter((e:any)=>e.type==='keydown'||e.type==='keyup')
          .map((e:any)=>({frame:e.frame, sub:e.data.subframe??0, type:e.type, key:e.data.key})),
        gin: rp.events.filter((e:any)=>e.type==='ige'&&e.data.type==='interaction'&&e.data.data?.type==='garbage')
          .map((e:any)=>({frame:e.frame, amt:e.data.data.amt, x:e.data.data.x, size:e.data.data.size,
            confirmFrame: CONFIRM(me.rp ?? rp, e.data.data.cid, e.data.data.iid)})),
        handling: rp.options.handling, seed: rp.options.seed, frames: rp.frames,
        placed: st.piecesplaced, recv: st.garbage.received ?? 0 });
    }}}

const survivors = new Map<string, Set<string>>();
for (const [label, extra] of CONFIGS) {
  const s = new Set<string>();
  for (const c of rows) {
    const r = simulate(c.ev, c.gin, c.handling, c.seed, c.frames, DEFAULT_TABLE, {...base, ...extra});
    if (r.placed >= c.placed) s.add(c.key);
  }
  survivors.set(label, s);
}
const cohort = rows.filter(c => CONFIGS.every(([l]) => survivors.get(l)!.has(c.key)));
console.log(`fixed cohort (survives under every config): ${cohort.length} player-rounds\n`);
console.log('config                 exact  over  under   sim/real       mean delta');
for (const [label, extra] of CONFIGS) {
  let exact=0, over=0, under=0, sim=0, real=0;
  for (const c of cohort) {
    const r = simulate(c.ev, c.gin, c.handling, c.seed, c.frames, DEFAULT_TABLE, {...base, ...extra});
    const dv = r.garbage.received - c.recv;
    sim += r.garbage.received; real += c.recv;
    if (dv===0) exact++; else if (dv>0) over++; else under++;
  }
  console.log(`${label.padEnd(22)} ${String(exact).padStart(5)} ${String(over).padStart(5)} ${String(under).padStart(6)}   ${String(sim).padStart(4)}/${String(real).padEnd(5)}  ${((sim-real)/cohort.length).toFixed(2).padStart(8)}`);
}


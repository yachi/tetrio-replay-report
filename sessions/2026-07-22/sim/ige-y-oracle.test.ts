/**
 * Regression guard for the ige `y` oracle (see ige-y-oracle.ts).
 *
 * Two layers: the formula itself on hand-worked cases, and the empirical agreement rate on
 * the real replays. The second is the one that matters — it is what makes y usable as a
 * board-row oracle, and it will fail loudly if a sim change quietly breaks the board while
 * leaving attack amounts intact (exactly the failure the loose gate cannot see).
 */
import { test, expect } from 'bun:test';
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';
import { expectedIgeY, matchesIgeY } from './ige-y-oracle.ts';

test('y is the centre of the cleared block, rounded toward the bottom', () => {
  expect(expectedIgeY(39, 1)).toBe(39);            // single: the row itself
  expect(expectedIgeY(39, 2)).toBe(39);            // double: still the bottom row
  expect(expectedIgeY(38, 3)).toBe(37);            // triple spanning 36..38 -> 37
  expect(expectedIgeY(25, 4)).toBe(24);            // quad spanning 22..25 -> 24
  expect(expectedIgeY(28, 3)).toBe(27);
});

test('matchesIgeY needs a real clear to compare against', () => {
  expect(matchesIgeY([], 0, 30)).toBe(false);
  expect(matchesIgeY([38, 37, 36], 3, 37)).toBe(true);
  expect(matchesIgeY([38, 37, 36], 3, 38)).toBe(false);
});

test('board rows agree with ground truth on at least 90% of verified attacks', () => {
  const DIR = (process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);
  const opts = {garbagespeed:30, garbagecap:8, locktime:60, gravity:0.02, sdfMode:'abs' as const,
                insertMode:'onPlace' as const, cancelMode:'all' as const, acEmit:'separate' as const,
                subframe:true, blockout:'shiftup' as const, kickset:'SRS+' as const};
  let checked = 0, ok = 0;
  for (const f of readdirSync(DIR).filter(x=>x.endsWith('.ttrm')).sort()) {
    const d = JSON.parse(readFileSync(`${DIR}/${f}`,'utf8'));
    for (const rnd of d.replay.rounds) { if (rnd.length!==2) continue;
      const P = rnd.map((p:any)=>({rp:p.replay, gameid:p.replay.options.gameid}));
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
        for (let i=0;i<Math.min(mine.length,truth.length);i++) {
          const a = mine[i]!, b = truth[i]!;
          if (Math.abs(a.frame-b.frame)>25 || a.sent!==b.amt) break;   // verified prefix only
          if (a.lines === 0) continue;                                 // all-clear bonus event
          checked++;
          if (matchesIgeY(a.clearedRows, a.lines, b.y)) ok++;
        }
      }}}
  expect(checked).toBeGreaterThan(200);          // anti-vacuity: the loop must actually run
  expect(ok / checked).toBeGreaterThan(0.90);
});

/**
 * In rounds that contain a real perfect clear, the verified prefix is median ZERO pieces —
 * the first attack already disagrees with ground truth. That is a much sharper failure than
 * "the board drifts": it says the disagreement is present at the very first line clear.
 *
 * This prints, for every player-round holding a real PC, the first few sim attacks beside the
 * first few ground-truth attacks from the opponent's ige stream. If the sim reached the canonical
 * PC-opener window (piece 9/19) and still scored no all-clear, coverage cannot excuse the miss.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE } from './sim.ts';

const DIR = (process.env.REPLAY_DIR ?? `${import.meta.dir}/..`);
const opts = { garbagespeed: 30, garbagecap: 8, locktime: 30, gravity: 0.02, sdfMode: 'abs' as const,
               insertMode: 'onPlace' as const, cancelMode: 'all' as const };

let coveredMiss = 0, uncoveredMiss = 0, hit = 0;

for (const f of readdirSync(DIR).filter(x => x.endsWith('.ttrm')).sort()) {
  const d = JSON.parse(readFileSync(`${DIR}/${f}`, 'utf8'));
  d.replay.rounds.forEach((rnd: any, ri: number) => {
    if (rnd.length !== 2) return;
    const P = rnd.map((p: any) => ({ p, rp: p.replay, gameid: p.replay.options.gameid }));
    for (const [me, other] of [[P[0], P[1]], [P[1], P[0]]] as any[]) {
      const real = me.rp.results.stats.clears.allclear ?? 0;
      if (!real) continue;
      const ev = me.rp.events.filter((e: any) => e.type === 'keydown' || e.type === 'keyup')
        .map((e: any) => ({ frame: e.frame, sub: e.data.subframe ?? 0, type: e.type, key: e.data.key }));
      const gin = me.rp.events.filter((e: any) => e.type === 'ige' && e.data.type === 'interaction' && e.data.data?.type === 'garbage')
        .map((e: any) => ({ frame: e.frame, amt: e.data.data.amt, x: e.data.data.x, size: e.data.data.size }));
      const truth = other.rp.events.filter((e: any) => e.type === 'ige' && e.data.type === 'interaction'
        && e.data.data?.type === 'garbage' && e.data.data.gameid === me.gameid)
        .map((e: any) => ({ frame: e.data.data.frame ?? e.frame, amt: e.data.data.amt }))
        .sort((a: any, b: any) => a.frame - b.frame);

      const r = simulate(ev, gin, me.rp.options.handling, me.rp.options.seed, me.rp.frames, DEFAULT_TABLE, opts);
      const sent = r.records.filter(x => x.sent > 0);
      const simPC = r.clears.allclear;
      const reached = r.locks.length;
      const covered = reached > 19;   // did the sim run through the canonical PC-opener window?
      if (simPC >= real) hit++; else if (covered) coveredMiss++; else uncoveredMiss++;

      // first garbage arrival — the sim is credible only before this
      const firstGarbage = r.garbageEvents.length ? r.garbageEvents[0]!.lockIndex : Infinity;

      console.log(`\n${f.slice(-9)} r${ri} ${me.p.username}  PC sim=${simPC} real=${real}  reached ${reached} pieces  firstGarbage@piece ${firstGarbage === Infinity ? '-' : firstGarbage}`);
      console.log(`  sim sent  : ${sent.slice(0, 6).map(x => `${x.sent}@${x.frame}`).join('  ') || '(none)'}`);
      console.log(`  truth     : ${truth.slice(0, 6).map((x: any) => `${x.amt}@${x.frame}`).join('  ') || '(none)'}`);
      const firstBad = (() => {
        for (let i = 0; i < Math.min(sent.length, truth.length); i++)
          if (!(Math.abs(sent[i]!.frame - truth[i]!.frame) <= 25 && sent[i]!.sent === truth[i]!.amt)) return i;
        return -1;
      })();
      console.log(`  first disagreement at attack #${firstBad}` +
        (firstBad >= 0 && sent[firstBad] && truth[firstBad]
          ? `  sim ${sent[firstBad]!.sent}@${sent[firstBad]!.frame}  vs truth ${truth[firstBad]!.amt}@${truth[firstBad]!.frame}` : ''));
      // what did the sim score on its own first clears?
      console.log(`  sim first clears: ${r.records.filter(x => x.lines > 0).slice(0, 6).map(x => `${x.lines}L${x.spin !== 'none' ? '/' + x.spin : ''}=atk${x.attack}`).join('  ') || '(none)'}`);
    }
  });
}
console.log(`\n\nrounds where sim matched the PC count : ${hit}`);
console.log(`MISSED despite simulating past piece 19 : ${coveredMiss}   <- coverage cannot excuse these`);
console.log(`missed without reaching piece 19        : ${uncoveredMiss}`);

/**
 * ONE definition of "the board provably matches the real game", shared by every consumer.
 *
 * The forecast metric is only meaningful on boards that provably match the real game, so it
 * is computed over the verified prefix of each round. That made the metric's sample size a
 * function of simulator accuracy — which is why it was starved: at the old settings only
 * 14.1% of placements were verified, leaving ~12 decided winner/loser pairs.
 *
 * Two things widen it:
 *   1. BEST_OPTS — the settings established by fit-opts.ts / ab-subframe.ts / ab-kickset.ts.
 *      The sub-frame input clock alone moved coverage 14.1% -> 19.6%.
 *   2. strictRows — also require the ige row oracle to agree (ige-y-oracle.ts). This SHRINKS
 *      the prefix but makes it honest: 7.4% of attacks match on frame and amount while coming
 *      from the wrong board row, and a forecast computed on such a board is fiction.
 *
 * Extracted because pairs.ts, run-forecast.ts and coverage-strict.ts each had their own copy
 * of this loop and had already drifted (pairs.ts and run-forecast.ts still ran the pre-fix
 * settings). One implementation, one set of numbers.
 */
import { readFileSync, readdirSync } from 'node:fs';
import { simulate, DEFAULT_TABLE, type SimResult } from './sim.ts';
import { matchesIgeY } from './ige-y-oracle.ts';

export const BEST_OPTS = {
  garbagespeed: 30, garbagecap: 8, locktime: 60, gravity: 0.02, sdfMode: 'abs' as const,
  insertMode: 'onPlace' as const, cancelMode: 'all' as const, acEmit: 'separate' as const,
  subframe: true, blockout: 'shiftup' as const, kickset: 'SRS+' as const,
};

export interface Case {
  file: string; round: number; user: string; alive: boolean;
  ev: any[]; gin: any[]; truth: { frame: number; amt: number; y: number }[];
  handling: any; seed: number; frames: number; placed: number;
}

export function loadCases(dir = process.env.REPLAY_DIR ?? `${import.meta.dir}/..`): Case[] {
  const out: Case[] = [];
  for (const file of readdirSync(dir).filter(f => f.endsWith('.ttrm')).sort()) {
    const d = JSON.parse(readFileSync(`${dir}/${file}`, 'utf8'));
    d.replay.rounds.forEach((rnd: any, round: number) => {
      if (rnd.length !== 2) return;
      const P = rnd.map((p: any) => ({ p, rp: p.replay, gameid: p.replay.options.gameid }));
      for (const [me, other] of [[P[0], P[1]], [P[1], P[0]]] as any[]) {
        out.push({
          file, round, user: me.p.username, alive: me.p.alive,
          ev: me.rp.events.filter((e: any) => e.type === 'keydown' || e.type === 'keyup')
            .map((e: any) => ({ frame: e.frame, sub: e.data.subframe ?? 0, type: e.type, key: e.data.key })),
          gin: me.rp.events.filter((e: any) => e.type === 'ige' && e.data.type === 'interaction' && e.data.data?.type === 'garbage')
            .map((e: any) => ({ frame: e.frame, amt: e.data.data.amt, x: e.data.data.x, size: e.data.data.size,
              cid: e.data.data.iid, gameid: e.data.data.gameid,
              // the reference queue times insertion from the CONFIRM event, not the arrival
              confirmFrame: me.rp.events.find((k: any) => k.type === 'ige'
                && k.data.type === 'interaction_confirm' && k.data.data?.type === 'garbage'
                && k.data.data.iid === e.data.data.iid && k.data.data.gameid === e.data.data.gameid)?.frame })),
          truth: other.rp.events.filter((e: any) => e.type === 'ige' && e.data.type === 'interaction'
            && e.data.data?.type === 'garbage' && e.data.data.gameid === me.gameid)
            .map((e: any) => ({ frame: e.data.data.frame ?? e.frame, amt: e.data.data.amt, y: e.data.data.y }))
            .sort((a: any, b: any) => a.frame - b.frame),
          handling: me.rp.options.handling, seed: me.rp.options.seed,
          frames: me.rp.frames, placed: me.rp.results.stats.piecesplaced,
        });
      }
    });
  }
  return out;
}

export function runCase(c: Case, extra: any = {}): SimResult {
  return simulate(c.ev, c.gin, c.handling, c.seed, c.frames, DEFAULT_TABLE, { ...BEST_OPTS, ...extra });
}

/**
 * Index of the last lock on a board that provably matches the real game (-1 if none).
 * With strictRows, an attack must also agree with the ige row oracle.
 */
export type Gate =
  | 'frame+amount'        // original: attack timing and value
  | 'frame+amount+row'    // + the ige row oracle
  | 'frame+row';          // BOARD-only: drop the attack value

/**
 * Index of the last lock on a board that provably matches the real game (-1 if none).
 *
 * Gate choice matters and is not cosmetic. The forecast metric needs the BOARD to be right;
 * the attack VALUE is a downstream function of the board AND the attack table, so truncating
 * the prefix at a table error throws away board that is actually correct. 'frame+row' keeps
 * the two board constraints (when the clear happened, and where on the board) and drops the
 * one that mixes in a separate model. It is not weaker in the board sense — it swaps a
 * board+table constraint for a purely positional one.
 */
export function verifiedIndex(r: SimResult, truth: Case['truth'], gate: Gate | boolean = 'frame+amount+row'): number {
  const g: Gate = gate === true ? 'frame+amount+row' : gate === false ? 'frame+amount' : gate;
  const mine = r.records.filter(x => x.sent > 0);
  let vf = -1;
  for (let i = 0; i < Math.min(mine.length, truth.length); i++) {
    const a = mine[i]!, b = truth[i]!;
    if (Math.abs(a.frame - b.frame) > 25) break;
    if (g !== 'frame+row' && a.sent !== b.amt) break;
    // the all-clear bonus is its own event and carries no clear of its own, so no row to check
    if (g !== 'frame+amount' && a.lines > 0 && !matchesIgeY(a.clearedRows, a.lines, b.y)) break;
    vf = a.frame;
  }
  let vIdx = -1;
  for (let i = 0; i < r.locks.length; i++) if (r.locks[i]!.frame <= vf) vIdx = i;
  return vIdx;
}

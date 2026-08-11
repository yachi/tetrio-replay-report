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
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { simulate, DEFAULT_TABLE, type SimResult } from './sim.ts';
import { matchesIgeY } from './ige-y-oracle.ts';

/**
 * Where the .ttrm replays live. ONE definition, and it refuses to guess.
 *
 * This was `process.env.REPLAY_DIR ?? ${import.meta.dir}/..` written out in 26 separate files.
 * That default worked only because the code sat inside a session directory, so `..` happened to
 * be 2026-07-22 — which is exactly why the instrument could not be shared, and how three
 * sessions' artifacts came to be produced by a script living inside a fourth's.
 *
 * Moving to pipeline/sim makes `..` the pipeline directory, which holds no replays. That is the
 * dangerous kind of wrong: readdirSync on it SUCCEEDS and the .ttrm filter returns an EMPTY
 * list, so all 26 callers would quietly compute over zero rounds and emit an artifact full of
 * zeroes instead of failing. So there is no positional default any more, and an empty match is
 * an error rather than an answer.
 */
export function replayDir(dir = process.env.REPLAY_DIR): string {
  if (!dir)
    throw new Error(
      'REPLAY_DIR is not set. The simulator lives in pipeline/sim and is session-agnostic, so it '
      + 'cannot infer which replays you mean.\n'
      + '  REPLAY_DIR=sessions/2026-07-22 bun pipeline/sim/<script>.ts');
  const abs = resolve(dir);
  if (!existsSync(abs)) throw new Error(`REPLAY_DIR does not exist: ${abs}`);
  const n = readdirSync(abs).filter(f => f.endsWith('.ttrm')).length;
  // Zero replays is the silent failure this function exists to prevent: downstream it is
  // indistinguishable from "this session genuinely had no rounds".
  if (n === 0) throw new Error(`no .ttrm replays in REPLAY_DIR: ${abs}`);
  return abs;
}

export const BEST_OPTS = {
  garbagespeed: 30, garbagecap: 8, locktime: 60, gravity: 0.02, sdfMode: 'abs' as const,
  insertMode: 'onPlace' as const, cancelMode: 'all' as const, acEmit: 'separate' as const,
  subframe: true, blockout: 'shiftup' as const, kickset: 'SRS+' as const,
  // TETR.IO's documented attack formula (logarithmic b2b level + log1p zero-base combo), not the
  // historical fit — the biggest single drift lever found (see attack-model.test.ts). Ground-truth,
  // so it is the default now rather than opt-in; the byte-stability that kept it 'legacy' is the same
  // conservatism the hoisted-DAS fix overrode. Attack amount is board-independent, so it moves only
  // the verified-prefix length (and thus the quarantined forecast/opener counts), never facts.json.
  attackModel: 'exact' as const,
};

export interface Case {
  file: string; round: number; user: string; alive: boolean;
  ev: any[]; gin: any[]; truth: { frame: number; amt: number; y: number }[];
  handling: any; seed: number; frames: number; placed: number;
  /**
   * The round's own clear counts, straight from `results.stats.clears` — the GAME's tally, not
   * this simulator's, and covering the whole round rather than the verified prefix. Carried here
   * so a consumer can publish a figure that does not depend on the simulator at all, and can say
   * so. `extract.py` and `extract2.ts` read the same field into facts.json independently, where
   * the cross-extractor gate compares them, so the number is already twice-derived.
   */
  clears: Record<string, number>;
}

export function loadCases(dir = replayDir()): Case[] {
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
            .map((e: any) => ({ frame: e.frame, sub: e.data.subframe ?? 0, type: e.type, key: e.data.key, hoisted: e.data.hoisted })),
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
          clears: me.rp.results.stats.clears ?? {},
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

// Drill the DOMINANT drift-cut cause: "sim-shorter" (53.6%, six sessions, 407/760 — measured 2026-08-15
// via `bun drift-cut.mjs`) — the sim produces fewer sent-attacks than the real player, with no mismatch
// in the overlap. Is it a BUG (sim under-produces / tops out early from over-inserted garbage) or
// CORRECT (the player is the round's loser, so the sim rightly ends when they die)? Discriminator:
// alive (did the player survive?) + sim.topout + how far short + how early the sim's simulation ends
// vs the round length.
//
// This 53.6% was 45% over the five-session corpus before later sim fixes (documented-garbagespeed
// default, the garbage-cancel protocol port, locktime 60->30) — NOT because of the sixth session.
// Re-running drift-cut.mjs's own classification restricted to the SAME five sessions gives 53.5% today
// (317/592), and 2026-08-14 alone is 53.6% (90/168): the 8.5-point move from 45% to 53.6% is almost
// entirely those later sim fixes, and adding 2026-08-14 moves the corpus rate by only ~0.1 point.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();

let shorter = 0;
const bucket = { "dead&topout": 0, "dead&no-topout": 0, "ALIVE&topout": 0, "ALIVE&no-topout": 0 };
let shortfallSum = 0, earlyStopSum = 0, n = 0;
const aliveExamples = [];
for (const dir of dirs) {
  let cases; try { cases = loadCases(`${SESS}/${dir}`); } catch { continue; }
  for (const c of cases) {
    let sim; try { sim = runCase(c); } catch { continue; }
    const mine = sim.records.filter((x) => x.sent > 0), truth = c.truth;
    // reproduce verifiedIndex's break test to isolate the "no break, sim ran out" case
    let broke = false; const lim = Math.min(mine.length, truth.length);
    for (let i = 0; i < lim; i++) { const a = mine[i], b = truth[i];
      if (Math.abs(a.frame - b.frame) > 25) { broke = true; break; }
      if (a.sent !== b.amt) { broke = true; break; } }
    if (broke || mine.length >= truth.length) continue;
    shorter++; n++;
    const dead = c.alive === false;               // player did NOT survive the round
    const topout = !!sim.topout;                    // sim's board topped out
    bucket[`${dead ? "dead" : "ALIVE"}&${topout ? "topout" : "no-topout"}`]++;
    shortfallSum += truth.length - mine.length;
    const lastLock = sim.locks.length ? sim.locks[sim.locks.length - 1].frame : 0;
    earlyStopSum += (c.frames - lastLock);
    if (!dead && aliveExamples.length < 12)
      aliveExamples.push(`${dir.slice(5)} ${c.user} ${c.file.replace('replay-','').replace('.ttrm','')} r${c.round}: sim ${mine.length} vs real ${truth.length} attacks, topout=${topout}, simEnds@${lastLock}/${c.frames}`);
  }
}
console.log(`"sim-shorter" cases: ${shorter}`);
console.log(`\nWHO are they? (dead = player lost the round; ALIVE = player won — under-production is a BUG only here)`);
for (const k of Object.keys(bucket)) console.log(`  ${k.padEnd(18)} ${bucket[k]}`);
console.log(`\navg attacks short: ${(shortfallSum / n).toFixed(1)}   avg frames the sim stops early: ${(earlyStopSum / n).toFixed(0)}`);
console.log(`\nALIVE (winner) sim-shorter — the potential BUG cases:`);
console.log(aliveExamples.length ? aliveExamples.map(e => "  " + e).join("\n") : "  none — every sim-shorter case is a round loser (CORRECT, not a bug)");

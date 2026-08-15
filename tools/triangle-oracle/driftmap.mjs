// Corpus drift map: diff the project sim against the Triangle oracle at every lock, across all sessions.
// Reuses the project's own sim (loadCases/runCase) so the comparison is sim-vs-oracle on the same inputs.
// Run:  cd tools/triangle-oracle && bun install && bun driftmap.mjs
//       bun driftmap.mjs --prefix     same comparison, restricted to each case's verified prefix
//
// `--prefix` exists because the README publishes BOTH rates and they answer different questions.
// The whole-round rate is dragged down by the topout flood past the prefix; the prefix rate is the
// one the quarantined sections actually rest on. It was published for a while with no command that
// produced it — the reproduction path was a scratchpad file nobody committed — which is the same
// defect as a figure quoted from memory. Now the flag prints it.
//
// NOTE: this is NOT cross-extract.mjs's number and the two must not be conflated. Here a lock counts
// if it matches INDIVIDUALLY; cross-extract counts only the CONTIGUOUS agreeing prefix, stopping at
// the first divergence. Same denominator, different question, and this one is always the higher.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
import { replayRound } from "./oracle.mjs";

const PREFIX_ONLY = process.argv.slice(2).includes("--prefix");

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS)
  .filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm")))
  .sort();

// sim board (40 rows, rows 20..39 = visible) -> top-down 10x20 '.'/G/#, matching the oracle's enc
const encSim = (b) => { let o = ""; for (let r = 20; r < 40; r++) for (let c = 0; c < 10; c++) { const cell = b[r][c]; o += cell == null ? "." : cell === "G" ? "G" : "#"; } return o; };

console.log("session        cases  locks  bitExact  %exact   earlyDrift(<80% of round)");
let gCases = 0, gLocks = 0, gExact = 0; const early = [];
for (const dir of dirs) {
  const path = `${SESS}/${dir}`;
  let cases;
  try { cases = loadCases(path); } catch (e) { console.log(`${dir}: loadCases failed: ${e.message}`); continue; }
  const parsed = {};
  let cCases = 0, cLocks = 0, cExact = 0, cEarly = 0;
  for (const c of cases) {
    if (!parsed[c.file]) parsed[c.file] = JSON.parse(readFileSync(`${path}/${c.file}`, "utf8"));
    const round = parsed[c.file].replay.rounds[c.round];
    const player = round.find((p) => p.username === c.user);
    if (!player) continue;
    let sim, tri;
    try { sim = runCase(c); } catch { continue; }
    try { tri = replayRound(player, round, { untilFrame: c.frames + 2 }); } catch { continue; }
    // --prefix: stop at the last lock the sim is verified against the ige, so the denominator is
    // the verified prefix rather than the whole round. `verifiedIndex` < 0 means nothing verified.
    let upto = sim.locks.length;
    if (PREFIX_ONLY) {
      const v = verifiedIndex(sim, c.truth);
      if (v < 0) continue;
      upto = Math.min(sim.locks.length, v + 1);
    }
    let exact = 0, firstBad = null;
    for (let i = 0; i < upto; i++) {
      const f = sim.locks[i].frame, t = tri.gridAt(f);
      if (t === undefined) continue;
      if (encSim(sim.boards[i]) === t) exact++; else if (firstBad === null) firstBad = f;
    }
    cCases++; cLocks += upto; cExact += exact;
    if (firstBad !== null && firstBad < 0.8 * c.frames) { cEarly++; early.push(`${dir}/${c.file} r${c.round} ${c.user}: firstDrift@${firstBad}/${c.frames}`); }
  }
  const pct = cLocks ? ((100 * cExact) / cLocks).toFixed(1) : "—";
  console.log(`${dir.padEnd(12)}  ${String(cCases).padStart(4)}  ${String(cLocks).padStart(5)}  ${String(cExact).padStart(7)}  ${String(pct).padStart(6)}   ${cEarly}`);
  gCases += cCases; gLocks += cLocks; gExact += cExact;
}
console.log("-".repeat(70));
console.log(`TOTAL         ${String(gCases).padStart(4)}  ${String(gLocks).padStart(5)}  ${String(gExact).padStart(7)}  ${((100 * gExact) / gLocks).toFixed(1).padStart(6)}`);
console.log("\nEarly-divergence cases (sim vs oracle disagree before the topout flood — attribution needs a live spot-check):");
console.log(early.length ? early.slice(0, 20).join("\n") + (early.length > 20 ? `\n... +${early.length - 20} more` : "") : "  none");

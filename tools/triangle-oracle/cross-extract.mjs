// Triangle-as-second-extractor prototype. A finding is DUAL-BACKED when every board it reads is
// bit-exact between our sim and Triangle — i.e. its lock sits before the first sim-vs-oracle
// divergence (firstBad). Measures how much of each quarantined section two independent engines
// agree on, which is the dual-implementation backing the quarantine is waiting for.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
import { forecastMetric } from "../../pipeline/sim/forecast.ts";
import { replayRound } from "./oracle.mjs";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
const encSim = (b) => { let o = ""; for (let r = 20; r < 40; r++) for (let c = 0; c < 10; c++) { const cell = b[r][c]; o += cell == null ? "." : cell === "G" ? "G" : "#"; } return o; };
const OPENER_WINDOW = 21; // pieces the opener ordering metric scores

// per-section tallies
const fc = { total: 0, dual: 0, byKind: {} };
let openRounds = 0, openDual = 0;
let prefixLocks = 0, prefixDual = 0;

for (const dir of dirs) {
  let cases; try { cases = loadCases(`${SESS}/${dir}`); } catch { continue; }
  const parsed = {};
  for (const c of cases) {
    if (!parsed[c.file]) parsed[c.file] = JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`, "utf8"));
    const rp = parsed[c.file].replay.rounds[c.round];
    const player = rp.find((p) => p.username === c.user);
    if (!player) continue;
    let sim, tri; try { sim = runCase(c); } catch { continue; } if (!sim.locks.length) continue;
    try { tri = replayRound(player, rp, { untilFrame: c.frames + 2 }); } catch { continue; }
    const v = verifiedIndex(sim, c.truth); if (v < 0) continue;

    // first lock where sim and Triangle disagree (agreement is bit-exact board at the lock frame)
    let firstBad = Infinity;
    for (let i = 0; i < sim.locks.length; i++) {
      const t = tri.gridAt(sim.locks[i].frame); if (t === undefined) continue;
      if (encSim(sim.boards[i]) !== t) { firstBad = i; break; }
    }
    // dual-backed prefix = min(verified prefix v, firstBad-1)
    const dualTop = Math.min(v, firstBad - 1);

    // prefix coverage
    prefixLocks += v + 1;
    prefixDual += Math.max(0, dualTop + 1);

    // forecast events (already restricted to the verified prefix)
    for (const rec of forecastMetric(sim, true).records) {
      if (rec.lockIndex > v) continue;
      fc.total++;
      fc.byKind[rec.kind] = fc.byKind[rec.kind] || { total: 0, dual: 0 };
      fc.byKind[rec.kind].total++;
      if (rec.lockIndex <= dualTop) { fc.dual++; fc.byKind[rec.kind].dual++; }
    }

    // opener ordering window: dual-backed iff the whole first-21-piece window is bit-exact
    const win = Math.min(OPENER_WINDOW - 1, v);
    openRounds++;
    if (dualTop >= win) openDual++;
  }
}

const pct = (a, b) => b ? `${(100 * a / b).toFixed(1)}%` : "—";
console.log(`=== verified-prefix coverage ===`);
console.log(`  ${prefixDual}/${prefixLocks} locks bit-exact sim==Triangle (${pct(prefixDual, prefixLocks)})`);
console.log(`\n=== FORECAST section (fully quarantined) ===`);
console.log(`  events in verified prefix: ${fc.total}   dual-backed: ${fc.dual} (${pct(fc.dual, fc.total)})`);
for (const k of Object.keys(fc.byKind).sort()) console.log(`    ${k.padEnd(18)} ${fc.byKind[k].dual}/${fc.byKind[k].total} dual (${pct(fc.byKind[k].dual, fc.byKind[k].total)})`);
console.log(`\n=== OPENER ordering window (first ${OPENER_WINDOW} pieces) ===`);
console.log(`  rounds whose opening window is fully dual-backed: ${openDual}/${openRounds} (${pct(openDual, openRounds)})`);

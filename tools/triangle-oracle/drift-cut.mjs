// Classify WHY the verified prefix cuts — the actual drift metric (sim's sent-attack records vs the
// REAL ige), no oracle involved. verifiedIndex breaks at the first attack where |frame|>25, amount
// differs, or the ige row oracle fails. If one cause dominates systematically (as `hoisted` did for
// openings), it's the next drift win. Records direction/magnitude so a systematic bias is visible.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
import { matchesIgeY } from "../../pipeline/sim/ige-y-oracle.ts";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();

const cause = { frame: 0, amount: 0, row: 0, "exhausted-both": 0, "sim-shorter": 0, "sim-longer": 0 };
const frameDelta = {}, amtDelta = {}, breakIdx = {};
let n = 0;
const examples = [];
for (const dir of dirs) {
  let cases; try { cases = loadCases(`${SESS}/${dir}`); } catch { continue; }
  for (const c of cases) {
    let sim; try { sim = runCase(c, process.env.EXACT ? {attackModel:"exact"} : {}); } catch { continue; }
    const mine = sim.records.filter((x) => x.sent > 0), truth = c.truth;
    n++;
    let broke = null, bi = -1;
    const lim = Math.min(mine.length, truth.length);
    for (let i = 0; i < lim; i++) {
      const a = mine[i], b = truth[i];
      if (Math.abs(a.frame - b.frame) > 25) { broke = "frame"; bi = i; frameDelta[Math.sign(a.frame - b.frame)] = (frameDelta[Math.sign(a.frame - b.frame)] || 0) + 1; break; }
      if (a.sent !== b.amt) { broke = "amount"; bi = i; const s = Math.sign(a.sent - b.amt); amtDelta[s] = (amtDelta[s] || 0) + 1; break; }
      if (a.lines > 0 && !matchesIgeY(a.clearedRows, a.lines, b.y)) { broke = "row"; bi = i; break; }
    }
    if (broke === null) {
      if (mine.length === truth.length) cause["exhausted-both"]++;
      else if (mine.length < truth.length) cause["sim-shorter"]++;
      else cause["sim-longer"]++;
    } else {
      cause[broke]++;
      const b2 = bi <= 0 ? "0" : bi <= 2 ? "1-2" : bi <= 5 ? "3-5" : bi <= 15 ? "6-15" : ">15";
      breakIdx[b2] = (breakIdx[b2] || 0) + 1;
      if (examples.length < 10 && (broke === "amount" || broke === "frame"))
        examples.push(`${dir.slice(5)} ${c.user} ${c.file.replace('replay-','').replace('.ttrm','')} r${c.round}: ${broke} @attack ${bi}  sim(f${mine[bi].frame},a${mine[bi].sent}) vs real(f${truth[bi].frame},a${truth[bi].amt})`);
    }
  }
}
const pct = (k) => `${(100 * k / n).toFixed(1)}%`;
console.log(`drift-cut cause across ${n} cases (why the verified prefix ends):`);
for (const k of Object.keys(cause)) console.log(`  ${k.padEnd(16)} ${String(cause[k]).padStart(4)}  ${pct(cause[k])}`);
console.log(`\nbreak happens at attack index:`); for (const k of ["0","1-2","3-5","6-15",">15"]) console.log(`  ${k.padStart(5)}: ${breakIdx[k] || 0}`);
console.log(`\nframe-break direction (sign of sim-real frame; >0 = sim LATER): ${JSON.stringify(frameDelta)}`);
console.log(`amount-break direction (sign of sim-real amount; >0 = sim sent MORE): ${JSON.stringify(amtDelta)}`);
console.log(`\nexamples:`); for (const e of examples) console.log("  " + e);

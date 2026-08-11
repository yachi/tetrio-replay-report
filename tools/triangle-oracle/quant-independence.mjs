// Quantify the STRENGTH of the dual-backed agreement, per DualExtractor.dfy's lemma: agreement on a
// shared input is uninformative. Here the shared input is concrete — on garbage-bearing boards BOTH
// engines write the same recorded hole `x`, so agreement on those boards is partly forced. So split
// every dual-backed finding into:
//   INDEPENDENT  — board is garbage-free at the finding's lock: sim & Triangle derived it from scratch
//                  (movement/gravity/lock/clear), two genuinely separate clean-room implementations.
//   COUPLED      — garbage present: agreement is partly on the shared recorded holes, weaker evidence.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
import { forecastMetric } from "../../pipeline/sim/forecast.ts";
import { replayRound } from "./oracle.mjs";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
const encSim = (b) => { let o = ""; for (let r = 20; r < 40; r++) for (let c = 0; c < 10; c++) { const cell = b[r][c]; o += cell == null ? "." : cell === "G" ? "G" : "#"; } return o; };
const hasG = (b) => { for (let r = 20; r < 40; r++) for (let c = 0; c < 10; c++) if (b[r][c] === "G") return true; return false; };
const OPENER_WINDOW = 21;
// Wilson 95% lower bound on a proportion — the conservative read of a rate.
const wilsonLo = (k, n) => { if (!n) return 0; const z = 1.96, p = k / n, d = 1 + z * z / n; return ((p + z * z / (2 * n) - z * Math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)) / d); };

// forecast events: total / dual / dual&independent / dual&coupled
const fc = { total: 0, dual: 0, indep: 0, coupled: 0 };
// opener rounds: dual / dual&independent(window garbage-free) / dual&coupled
const op = { rounds: 0, dual: 0, indep: 0, coupled: 0 };
// prefix locks baseline
const px = { total: 0, dual: 0, gfree: 0, dualGfree: 0 };

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

    let firstBad = Infinity;
    for (let i = 0; i < sim.locks.length; i++) { const t = tri.gridAt(sim.locks[i].frame); if (t === undefined) continue; if (encSim(sim.boards[i]) !== t) { firstBad = i; break; } }
    const dualTop = Math.min(v, firstBad - 1);

    for (let i = 0; i <= v && i < sim.boards.length; i++) { px.total++; const g = hasG(sim.boards[i]); if (!g) px.gfree++; if (i <= dualTop) { px.dual++; if (!g) px.dualGfree++; } }

    for (const rec of forecastMetric(sim, true).records) {
      if (rec.lockIndex > v) continue;
      fc.total++;
      if (rec.lockIndex <= dualTop) {
        fc.dual++;
        const b = sim.boards[rec.lockIndex]; // board the event reads
        if (b && hasG(b)) fc.coupled++; else fc.indep++;
      }
    }

    const win = Math.min(OPENER_WINDOW - 1, v);
    op.rounds++;
    if (dualTop >= win) {
      op.dual++;
      let anyG = false; for (let i = 0; i <= win; i++) if (sim.boards[i] && hasG(sim.boards[i])) { anyG = true; break; }
      if (anyG) op.coupled++; else op.indep++;
    }
  }
}

const pct = (a, b) => b ? (100 * a / b).toFixed(1) : "—";
const line = (label, k, n) => `  ${label.padEnd(34)} ${String(k).padStart(5)}/${String(n).padStart(5)}  ${pct(k, n).padStart(5)}%   (Wilson 95% lower ${(100 * wilsonLo(k, n)).toFixed(1)}%)`;
console.log("VALUE OF THE DUAL-BACKING, decomposed by independence (DualExtractor.dfy: shared-input agreement is weak)\n");
console.log("verified-prefix locks");
console.log(line("bit-exact (dual)", px.dual, px.total));
console.log(line("  of which garbage-free (INDEP)", px.dualGfree, px.dual));
console.log(line("garbage-free overall (baseline)", px.gfree, px.total));
console.log("\nFORECAST events");
console.log(line("dual-backed", fc.dual, fc.total));
console.log(line("  INDEPENDENT (garbage-free board)", fc.indep, fc.total));
console.log(line("  COUPLED (garbage on board)", fc.coupled, fc.total));
console.log(`  independent share of dual-backed: ${pct(fc.indep, fc.dual)}%`);
console.log("\nOPENER rounds (opening window)");
console.log(line("dual-backed", op.dual, op.rounds));
console.log(line("  INDEPENDENT (garbage-free window)", op.indep, op.rounds));
console.log(line("  COUPLED (garbage in window)", op.coupled, op.rounds));
console.log(`  independent share of dual-backed: ${pct(op.indep, op.dual)}%`);

// Classify the FIRST sim-vs-oracle divergence in each case, now that openings are fixed.
// Question: is the leading divergence garbage-TIMING (diffuse, needs live calibration) or another
// systematic PLACEMENT bug like `hoisted` (a clean, free win)? Same playbook that found hoisted.
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
import { replayRound } from "./oracle.mjs";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
const encSim = (b) => { let o = ""; for (let r = 20; r < 40; r++) for (let c = 0; c < 10; c++) { const cell = b[r][c]; o += cell == null ? "." : cell === "G" ? "G" : "#"; } return o; };
const countG = (s) => (s.match(/G/g) || []).length;

let total = 0, agree = 0;
const cls = { "garbage-count": 0, "placement-#": 0, "mixed": 0 };
let nearGarbage = 0; const gapHist = {};
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
    total++;
    // find first divergent lock
    let bad = -1, s = "", t = "";
    for (let i = 0; i < sim.locks.length; i++) {
      const f = sim.locks[i].frame, tt = tri.gridAt(f); if (tt === undefined) continue;
      const ss = encSim(sim.boards[i]);
      if (ss !== tt) { bad = i; s = ss; t = tt; break; }
    }
    if (bad < 0) { agree++; continue; }
    // classify the difference at the first divergent lock
    const gDiff = countG(s) !== countG(t);
    let pDiff = false; for (let k = 0; k < s.length; k++) if ((s[k] === "#") !== (t[k] === "#")) { pDiff = true; break; }
    if (gDiff && !pDiff) cls["garbage-count"]++; else if (pDiff && !gDiff) cls["placement-#"]++; else cls["mixed"]++;
    // how close is the first divergent lock to a garbage arrival into this player?
    const lf = sim.locks[bad].frame;
    const gfr = (c.gin || []).map((g) => g.frame);
    if (gfr.length) {
      const nearest = Math.min(...gfr.map((g) => Math.abs(g - lf)));
      if (nearest <= 60) nearGarbage++;
      const bucket = nearest <= 30 ? "<=30" : nearest <= 60 ? "31-60" : nearest <= 150 ? "61-150" : ">150";
      gapHist[bucket] = (gapHist[bucket] || 0) + 1;
    }
  }
}
const div = total - agree;
console.log(`cases: ${total}   agree end-to-end: ${agree}   diverge somewhere: ${div}`);
console.log(`\nfirst-divergence KIND (what differs at the first bad lock):`);
console.log(`  garbage cells only (G count differs) : ${cls["garbage-count"]}  <- timing class`);
console.log(`  piece cells only   (# placement)     : ${cls["placement-#"]}  <- another hoisted-like bug?`);
console.log(`  mixed                                : ${cls["mixed"]}`);
console.log(`\nfirst-divergence PROXIMITY to a garbage arrival into this player:`);
console.log(`  within 60 frames of a garbage arrival: ${nearGarbage}/${div} (${(100*nearGarbage/div).toFixed(0)}%)`);
for (const k of ["<=30","31-60","61-150",">150"]) console.log(`  ${k.padStart(7)}: ${gapHist[k] || 0}`);

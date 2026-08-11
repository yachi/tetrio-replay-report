// Find the earliest, cleanest garbage-free PURE-placement divergence (sim vs oracle) and dump it with
// the piece + inputs, so a single mis-placed piece can be root-caused (the next mini-hoisted).
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
import { replayRound } from "./oracle.mjs";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
const enc = (b) => { let o = ""; for (let r = 20; r < 40; r++) for (let c = 0; c < 10; c++) { const cell = b[r][c]; o += cell == null ? "." : cell === "G" ? "G" : "#"; } return o; };
const hasG = (s) => s.includes("G");

const hits = [];
for (const dir of dirs) {
  let cases; try { cases = loadCases(`${SESS}/${dir}`); } catch { continue; }
  const parsed = {};
  for (const c of cases) {
    if (!parsed[c.file]) parsed[c.file] = JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`, "utf8"));
    const rp = parsed[c.file].replay.rounds[c.round]; const player = rp.find((p) => p.username === c.user);
    if (!player) continue;
    let sim, tri; try { sim = runCase(c); } catch { continue; } if (!sim.locks.length) continue;
    try { tri = replayRound(player, rp, { untilFrame: sim.locks[Math.min(10, sim.locks.length - 1)].frame + 2 }); } catch { continue; }
    for (let i = 0; i < Math.min(10, sim.locks.length); i++) {
      const f = sim.locks[i].frame, t = tri.gridAt(f); if (t === undefined) break;
      const s = enc(sim.boards[i]);
      if (s === t) continue;
      if (hasG(s) || hasG(t)) break;            // garbage-free only
      // pure placement: difference is in # cells (no garbage anywhere)
      const lk = sim.locks[i];
      hits.push({ dir, c, i, f, s, t, piece: lk.piece, cells: lk.cells });
      break;
    }
  }
}
hits.sort((a, b) => a.i - b.i);
console.log(`earliest garbage-free pure-placement divergences: ${hits.length}\n`);
for (const h of hits.slice(0, 4)) {
  const events = h.c.ev.filter((e) => e.frame <= h.f && e.frame >= (h.i > 0 ? 0 : 0)).slice(-14);
  console.log(`### ${h.dir.slice(5)} ${h.c.user} ${h.c.file.replace('replay-','').replace('.ttrm','')} r${h.c.round}  lock ${h.i} frame ${h.f}  piece=${h.piece}`);
  const sr = h.s.match(/.{10}/g), tr = h.t.match(/.{10}/g);
  let start = 0; while (start < 19 && sr[start] === ".........." && tr[start] === "..........") start++;
  console.log("   sim         oracle      diff");
  for (let r = start; r < 20; r++) { const d = sr[r].split("").map((ch, k) => ch === tr[r][k] ? " " : "^").join(""); console.log(`   ${sr[r]}  ${tr[r]}  ${d}`); }
  console.log("");
}

// Localize a single early divergence: dump sim vs oracle boards at the first N divergent locks.
// Usage: bun diag.mjs <file> <round> <user> [maxDivergences=3]
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase } from "../../pipeline/sim/verified-prefix.ts";
import { replayRound } from "./oracle.mjs";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const [file, roundArg, user, maxDiv = "3"] = process.argv.slice(2);
const round = Number(roundArg), maxD = Number(maxDiv);

// find the session dir holding this file
import { readdirSync, existsSync } from "node:fs";
const SESS = `${ROOT}sessions`;
let path = null;
for (const d of readdirSync(SESS)) {
  if (existsSync(`${SESS}/${d}/${file}`)) { path = `${SESS}/${d}`; break; }
}
if (!path) { console.error("file not found in any session"); process.exit(1); }

const cases = loadCases(path);
const c = cases.find((x) => x.file === file && x.round === round && x.user === user);
if (!c) { console.error("case not found; available:", cases.filter(x=>x.file===file&&x.round===round).map(x=>x.user)); process.exit(1); }

const data = JSON.parse(readFileSync(`${path}/${file}`, "utf8"));
const roundPlayers = data.replay.rounds[round];
const player = roundPlayers.find((p) => p.username === user);

const encSim = (b) => { let o = ""; for (let r = 20; r < 40; r++) for (let cc = 0; cc < 10; cc++) { const cell = b[r][cc]; o += cell == null ? "." : cell === "G" ? "G" : "#"; } return o; };
const sim = runCase(c);
const tri = replayRound(player, roundPlayers, { untilFrame: c.frames + 2 });

// find garbage arrival frames (from the case's gin/truth) for context
const garbFrames = (c.gin || []).map((g) => g.frame).sort((a, b) => a - b);
console.log(`case ${file} r${round} ${user}  frames=${c.frames}  locks=${sim.locks.length}`);
console.log(`garbage-into-this-player frames: ${garbFrames.slice(0, 12).join(",")}${garbFrames.length > 12 ? " …" : ""}`);

const show = (s20, label) => {
  const rows = [];
  for (let r = 0; r < 20; r++) rows.push(s20.slice(r * 10, r * 10 + 10));
  // trim leading empty rows for compactness
  let start = 0; while (start < 19 && rows[start] === "..........") start++;
  return rows.slice(start).map((row) => `${label==="sim"?"S ":"O "}${row}`).join("\n");
};

let shown = 0;
for (let i = 0; i < sim.locks.length && shown < maxD; i++) {
  const f = sim.locks[i].frame, t = tri.gridAt(f);
  if (t === undefined) continue;
  const s = encSim(sim.boards[i]);
  if (s === t) continue;
  shown++;
  const preGarbage = garbFrames.filter((g) => g <= f).length === 0;
  console.log(`\n=== divergence #${shown} at lock ${i} frame ${f}  (${preGarbage ? "BEFORE any garbage" : "after garbage@" + garbFrames.filter(g=>g<=f).slice(-1)[0]}) ===`);
  // side by side
  const sr = []; for (let r = 0; r < 20; r++) sr.push(s.slice(r*10, r*10+10));
  const tr = []; for (let r = 0; r < 20; r++) tr.push(t.slice(r*10, r*10+10));
  let start = 0; while (start < 19 && sr[start] === ".........." && tr[start] === "..........") start++;
  console.log("   sim         oracle      diff");
  for (let r = start; r < 20; r++) {
    const diff = sr[r].split("").map((ch, k) => ch === tr[r][k] ? " " : "^").join("");
    console.log(`   ${sr[r]}  ${tr[r]}  ${diff}`);
  }
}
if (shown === 0) console.log("no divergence found in locks (may be a garbage-timing-only case)");

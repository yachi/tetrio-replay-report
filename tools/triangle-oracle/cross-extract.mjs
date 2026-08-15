// Triangle-as-second-extractor. A finding is DUAL-BACKED when every board it reads is bit-exact
// between our sim and Triangle — i.e. its lock sits before the first sim-vs-oracle divergence
// (firstBad). This is the dual-EXTRACTOR agreement the forecast/opener quarantine is missing —
// two independent engines producing identical boards — and is distinct from the Dafny-proven ✓.
//
//   bun cross-extract.mjs            print the coverage table
//   bun cross-extract.mjs --out P    write the manifest to P (default: ./dual-backed.json)
//   bun cross-extract.mjs --check    fail if the committed manifest is stale (reproducibility gate)
//
// The manifest is a TOOLS artifact: it needs @haelp/teto (161 pkgs), so it is not rebuilt by the
// main CI, and its gate lives here rather than in pipeline/. Counts are integers so the JSON is
// byte-stable; percentages are derived at read time, never stored.
import { readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadCases, runCase, verifiedIndex } from "../../pipeline/sim/verified-prefix.ts";
import { forecastMetric } from "../../pipeline/sim/forecast.ts";
import { replayRound } from "./oracle.mjs";

const ROOT = fileURLToPath(new URL("../../", import.meta.url));
const HERE = fileURLToPath(new URL("./", import.meta.url));
const SESS = `${ROOT}sessions`;
const dirs = readdirSync(SESS).filter((x) => existsSync(`${SESS}/${x}`) && readdirSync(`${SESS}/${x}`).some((f) => f.endsWith(".ttrm"))).sort();
const encSim = (b) => { let o = ""; for (let r = 20; r < 40; r++) for (let c = 0; c < 10; c++) { const cell = b[r][c]; o += cell == null ? "." : cell === "G" ? "G" : "#"; } return o; };
const OPENER_WINDOW = 21; // pieces the opener ordering metric scores

// build the per-session dual-backed tallies
const sessions = {};
let gPrefix = { total: 0, dual: 0 };
for (const dir of dirs) {
  let cases; try { cases = loadCases(`${SESS}/${dir}`); } catch { continue; }
  const parsed = {};
  const S = { prefix_locks: 0, prefix_dual: 0, forecast: { total: 0, dual: 0, by_kind: {} }, opener_rounds: 0, opener_dual: 0 };
  for (const c of cases) {
    if (!parsed[c.file]) parsed[c.file] = JSON.parse(readFileSync(`${SESS}/${dir}/${c.file}`, "utf8"));
    const rp = parsed[c.file].replay.rounds[c.round];
    const player = rp.find((p) => p.username === c.user);
    if (!player) continue;
    let sim, tri; try { sim = runCase(c); } catch { continue; } if (!sim.locks.length) continue;
    try { tri = replayRound(player, rp, { untilFrame: c.frames + 2 }); } catch { continue; }
    const v = verifiedIndex(sim, c.truth); if (v < 0) continue;

    let firstBad = Infinity;
    for (let i = 0; i < sim.locks.length; i++) {
      const t = tri.gridAt(sim.locks[i].frame); if (t === undefined) continue;
      if (encSim(sim.boards[i]) !== t) { firstBad = i; break; }
    }
    const dualTop = Math.min(v, firstBad - 1); // last lock both engines agree on within the prefix

    S.prefix_locks += v + 1;
    S.prefix_dual += Math.max(0, dualTop + 1);

    for (const rec of forecastMetric(sim, true).records) {
      if (rec.lockIndex > v) continue;
      S.forecast.total++;
      const k = S.forecast.by_kind[rec.kind] || (S.forecast.by_kind[rec.kind] = { total: 0, dual: 0 });
      k.total++;
      if (rec.lockIndex <= dualTop) { S.forecast.dual++; k.dual++; }
    }

    const win = Math.min(OPENER_WINDOW - 1, v);
    S.opener_rounds++;
    if (dualTop >= win) S.opener_dual++;
  }
  // sort by_kind keys for byte-stability
  S.forecast.by_kind = Object.fromEntries(Object.keys(S.forecast.by_kind).sort().map((k) => [k, S.forecast.by_kind[k]]));
  sessions[dir] = S;
  gPrefix.total += S.prefix_locks; gPrefix.dual += S.prefix_dual;
}

const manifest = {
  schema: "dual-backed/1",
  what: "Two-engine (dual-EXTRACTOR) confirmation of the quarantined sim-derived sections. An event " +
        "is dual-backed when the project sim and Triangle.js (@haelp/teto) produce bit-exact boards " +
        "through its lock over the verified prefix. This is engine AGREEMENT, NOT a Dafny proof — it " +
        "does not carry a claim id or a ✓ badge, and it never merges into facts.json.",
  engines: ["pipeline/sim", "@haelp/teto (Triangle.js)"],
  verified_prefix_locks: gPrefix,
  sessions,
};
const json = JSON.stringify(manifest, null, 2) + "\n";

const argv = process.argv.slice(2);
const outIdx = argv.indexOf("--out");
const outPath = outIdx >= 0 ? argv[outIdx + 1] : `${HERE}dual-backed.json`;

const pct1 = (a, b) => (b ? (100 * a / b).toFixed(1) : "—");

// The three percentages the README publishes are DERIVED at read time — the manifest stores only
// counts, so byte-identity of the JSON says nothing about the prose. That gap is not hypothetical:
// the figures sat at their 08ed03c values through two regenerations that moved every one of them.
// So --check gates the prose too, and a paragraph it cannot parse is a FAILURE, never a skip —
// a rewording that silently disables the check is the same bug wearing a different hat.
function checkReadme(totals) {
  const path = `${HERE}README.md`;
  if (!existsSync(path)) return [`README.md not found at ${path}`];
  const md = readFileSync(path, "utf8");
  const re = /agree bit-exact on \*\*([\d.]+)%\*\* of locks, backing \*\*([\d.]+)%\*\* of\s+forecast events and \*\*([\d.]+)%\*\* of opener rounds/;
  const m = md.match(re);
  if (!m) return ["README.md: could not find the published coverage sentence. If you reworded it, " +
                  "update the regex in cross-extract.mjs so the figures stay gated."];
  const want = [pct1(totals.locks.dual, totals.locks.total),
                pct1(totals.forecast.dual, totals.forecast.total),
                pct1(totals.opener.dual, totals.opener.total)];
  const names = ["locks bit-exact", "forecast events dual-backed", "opener rounds dual-backed"];
  return want.flatMap((w, i) => (m[i + 1] === w ? [] : [`README.md says ${m[i + 1]}% for ${names[i]}; the manifest gives ${w}%`]));
}

let ft = 0, fd = 0, ort = 0, ord = 0;
for (const S of Object.values(sessions)) { ft += S.forecast.total; fd += S.forecast.dual; ort += S.opener_rounds; ord += S.opener_dual; }
const totals = { locks: gPrefix, forecast: { total: ft, dual: fd }, opener: { total: ort, dual: ord } };

if (argv.includes("--check")) {
  const cur = existsSync(outPath) ? readFileSync(outPath, "utf8") : "";
  if (cur !== json) { console.error(`STALE: ${outPath} differs from a fresh run. Regenerate with --out.`); process.exit(1); }
  const bad = checkReadme(totals);
  if (bad.length) { for (const b of bad) console.error(`STALE PROSE: ${b}`); process.exit(1); }
  console.log(`ok  ${outPath} reproduces byte-for-byte, and README.md's 3 published figures match it`);
} else if (outIdx >= 0 || argv.includes("--write")) {
  writeFileSync(outPath, json);
  console.log(`wrote ${outPath}`);
} else {
  const pct = (a, b) => `${pct1(a, b)}%`;
  console.log(`=== verified-prefix coverage ===\n  ${gPrefix.dual}/${gPrefix.total} locks bit-exact sim==Triangle (${pct(gPrefix.dual, gPrefix.total)})`);
  console.log(`\n=== FORECAST ===\n  ${fd}/${ft} events dual-backed (${pct(fd, ft)})`);
  console.log(`\n=== OPENER ===\n  ${ord}/${ort} rounds fully dual-backed in the opening window (${pct(ord, ort)})`);
  console.log(`\n(write the manifest with --out ./dual-backed.json; check it with --check)`);
}

// Independent TypeScript implementation of the facts.json extractor.
// Written from SCHEMA.md only (extract.py was not read).

import { readFileSync, writeFileSync, readdirSync } from "fs";
import { join, dirname } from "path";

const REPORT_DIR = dirname(decodeURIComponent(new URL(import.meta.url).pathname));
const PARENT_DIR = join(REPORT_DIR, "..");
const PLAYERS = ["yachi", "pinglamb"] as const;

const warnings: string[] = [];

function warn(msg: string) {
  warnings.push(msg);
}

// Mandatory rounding rule: floor(v*1000 + 0.5) in IEEE-754 double arithmetic.
function x1000(v: unknown, ctx: string): number {
  if (v === null || v === undefined) {
    warn(`${ctx}: missing/null numeric value, using 0`);
    return 0;
  }
  const n = Number(v);
  if (!Number.isFinite(n)) {
    warn(`${ctx}: non-finite numeric value (${v}), using 0`);
    return 0;
  }
  return Math.floor(n * 1000 + 0.5);
}

function intVal(v: unknown, ctx: string): number {
  if (v === null || v === undefined) {
    warn(`${ctx}: missing/null value, using 0`);
    return 0;
  }
  const n = Number(v);
  if (!Number.isFinite(n)) {
    warn(`${ctx}: non-finite value (${v}), using 0`);
    return 0;
  }
  return Math.trunc(n);
}

function fileIndex(filename: string): number {
  // replay-2026-07-24-1.ttrm -> 1 ; ... replay-2026-07-24-7.ttrm -> 7
  const m = filename.match(/^replay-2026-07-24-(\d+)\.ttrm$/);
  if (!m) throw new Error(`Unrecognized filename pattern: ${filename}`);
  return parseInt(m[1], 10);
}

function extractGarbageEvents(events: any[], ctx: string): { frame: number; amt: number }[] {
  if (!Array.isArray(events)) {
    warn(`${ctx}: events missing/not array, using empty garbage_events`);
    return [];
  }
  const out: { frame: number; amt: number }[] = [];
  for (const e of events) {
    if (e?.type !== "ige") continue;
    const data = e?.data;
    if (data?.type !== "interaction_confirm") continue;
    const inner = data?.data;
    if (inner?.type !== "garbage") continue;
    out.push({
      frame: intVal(data?.frame, `${ctx} garbage_event data.frame`),
      amt: intVal(inner?.amt, `${ctx} garbage_event data.data.amt`),
    });
  }
  return out;
}

function extractLeaderboardEntry(entry: any, ctx: string) {
  const stats = entry?.stats ?? {};
  if (!entry?.stats) warn(`${ctx}: leaderboard entry missing stats, using 0s`);
  return {
    wins: intVal(entry?.wins, `${ctx} wins`),
    apm_x1000: x1000(stats?.apm, `${ctx} stats.apm`),
    pps_x1000: x1000(stats?.pps, `${ctx} stats.pps`),
    vs_x1000: x1000(stats?.vsscore, `${ctx} stats.vsscore`),
    garbagesent: intVal(stats?.garbagesent, `${ctx} stats.garbagesent`),
    garbagereceived: intVal(stats?.garbagereceived, `${ctx} stats.garbagereceived`),
    kills: intVal(stats?.kills, `${ctx} stats.kills`),
  };
}

function extractRoundPlayer(player: any, ctx: string) {
  const stats = player?.stats ?? {};
  if (!player?.stats) warn(`${ctx}: round player missing stats, using 0s`);

  const resultsStats = player?.replay?.results?.stats ?? {};
  if (!player?.replay?.results?.stats) {
    warn(`${ctx}: missing replay.results.stats, using 0s for results-derived fields`);
  }

  const clearsRaw = resultsStats?.clears ?? {};
  if (!resultsStats?.clears) warn(`${ctx}: missing results.stats.clears, using 0s`);

  const garbageRaw = resultsStats?.garbage ?? {};
  if (!resultsStats?.garbage) warn(`${ctx}: missing results.stats.garbage, using 0s`);

  const finesseRaw = resultsStats?.finesse ?? {};
  if (!resultsStats?.finesse) warn(`${ctx}: missing results.stats.finesse, using 0s`);

  const events = player?.replay?.events;
  if (!Array.isArray(events)) warn(`${ctx}: missing replay.events, garbage_events will be empty`);

  return {
    lifetime: intVal(player?.lifetime, `${ctx} lifetime`),
    alive: player?.alive === true,
    apm_x1000: x1000(stats?.apm, `${ctx} stats.apm`),
    pps_x1000: x1000(stats?.pps, `${ctx} stats.pps`),
    vs_x1000: x1000(stats?.vsscore, `${ctx} stats.vsscore`),
    garbagesent: intVal(stats?.garbagesent, `${ctx} stats.garbagesent`),
    garbagereceived: intVal(stats?.garbagereceived, `${ctx} stats.garbagereceived`),
    kills: intVal(stats?.kills, `${ctx} stats.kills`),

    lines: intVal(resultsStats?.lines, `${ctx} results.stats.lines`),
    pieces: intVal(resultsStats?.piecesplaced, `${ctx} results.stats.piecesplaced`),
    inputs: intVal(resultsStats?.inputs, `${ctx} results.stats.inputs`),
    holds: intVal(resultsStats?.holds, `${ctx} results.stats.holds`),
    topcombo: intVal(resultsStats?.topcombo, `${ctx} results.stats.topcombo`),
    topbtb: intVal(resultsStats?.topbtb, `${ctx} results.stats.topbtb`),
    tspins: intVal(resultsStats?.tspins, `${ctx} results.stats.tspins`),
    clears: {
      singles: intVal(clearsRaw?.singles, `${ctx} clears.singles`),
      doubles: intVal(clearsRaw?.doubles, `${ctx} clears.doubles`),
      triples: intVal(clearsRaw?.triples, `${ctx} clears.triples`),
      quads: intVal(clearsRaw?.quads, `${ctx} clears.quads`),
      tspin_singles: intVal(clearsRaw?.tspinsingles, `${ctx} clears.tspinsingles`),
      tspin_doubles: intVal(clearsRaw?.tspindoubles, `${ctx} clears.tspindoubles`),
      tspin_triples: intVal(clearsRaw?.tspintriples, `${ctx} clears.tspintriples`),
      mini_tspin_singles: intVal(clearsRaw?.minitspinsingles, `${ctx} clears.minitspinsingles`),
      mini_tspin_doubles: intVal(clearsRaw?.minitspindoubles, `${ctx} clears.minitspindoubles`),
      allclear: intVal(clearsRaw?.allclear, `${ctx} clears.allclear`),
    },
    garbage_attack: intVal(garbageRaw?.attack, `${ctx} garbage.attack`),
    garbage_cleared: intVal(garbageRaw?.cleared, `${ctx} garbage.cleared`),
    maxspike: intVal(garbageRaw?.maxspike, `${ctx} garbage.maxspike`),
    finesse_faults: intVal(finesseRaw?.faults, `${ctx} finesse.faults`),
    finesse_perfect: intVal(finesseRaw?.perfectpieces, `${ctx} finesse.perfectpieces`),
    garbage_events: extractGarbageEvents(events, ctx),
  };
}

function extractMatch(filename: string, raw: any) {
  const index = fileIndex(filename);
  const ctxBase = `${filename}`;

  const ts = raw?.ts;
  if (typeof ts !== "string") warn(`${ctxBase}: top-level ts is not a string`);

  const leaderboard = raw?.replay?.leaderboard;
  if (!Array.isArray(leaderboard)) {
    throw new Error(`${ctxBase}: replay.leaderboard missing or not an array`);
  }

  const leaderboardOut: Record<string, ReturnType<typeof extractLeaderboardEntry>> = {};
  const score: Record<string, number> = {};
  for (const entry of leaderboard) {
    const username = entry?.username;
    if (typeof username !== "string") {
      warn(`${ctxBase}: leaderboard entry missing username, skipping`);
      continue;
    }
    const parsed = extractLeaderboardEntry(entry, `${ctxBase} leaderboard[${username}]`);
    leaderboardOut[username] = parsed;
    score[username] = parsed.wins;
  }

  // winner = username with max leaderboard wins
  let winner = "";
  let maxWins = -Infinity;
  for (const p of PLAYERS) {
    const w = score[p] ?? 0;
    if (w > maxWins) {
      maxWins = w;
      winner = p;
    }
  }

  const roundsRaw = raw?.replay?.rounds;
  if (!Array.isArray(roundsRaw)) {
    throw new Error(`${ctxBase}: replay.rounds missing or not an array`);
  }

  const rounds = roundsRaw.map((roundPlayers: any[], roundIdx: number) => {
    const rctx = `${ctxBase} round[${roundIdx}]`;
    if (!Array.isArray(roundPlayers) || roundPlayers.length !== 2) {
      throw new Error(`${rctx}: expected exactly 2 player objects, got ${roundPlayers?.length}`);
    }

    const playersOut: Record<string, ReturnType<typeof extractRoundPlayer>> = {};
    let roundWinner = "";
    let aliveCount = 0;

    for (const p of roundPlayers) {
      const username = p?.username;
      if (typeof username !== "string") {
        throw new Error(`${rctx}: player object missing username`);
      }
      const parsed = extractRoundPlayer(p, `${rctx} player[${username}]`);
      playersOut[username] = parsed;
      if (parsed.alive) {
        roundWinner = username;
        aliveCount++;
      }
    }

    if (aliveCount !== 1) {
      warn(`${rctx}: expected exactly 1 alive player, found ${aliveCount}; winner may be inaccurate`);
    }

    return {
      index: roundIdx,
      winner: roundWinner,
      players: playersOut,
    };
  });

  return {
    index,
    file: filename,
    ts,
    winner,
    score: {
      [PLAYERS[0]]: score[PLAYERS[0]] ?? 0,
      [PLAYERS[1]]: score[PLAYERS[1]] ?? 0,
    },
    leaderboard: leaderboardOut,
    rounds,
  };
}

function main() {
  const files = readdirSync(PARENT_DIR).filter((f) => f.endsWith(".ttrm"));
  if (files.length !== 7) {
    warn(`Expected 7 .ttrm files, found ${files.length}`);
  }

  const matches = files
    .map((f) => {
      const raw = JSON.parse(readFileSync(join(PARENT_DIR, f), "utf-8"));
      return extractMatch(f, raw);
    })
    .sort((a, b) => a.index - b.index);

  const output = {
    players: [...PLAYERS],
    matches,
  };

  const outPath = join(REPORT_DIR, "facts2.json");
  writeFileSync(outPath, JSON.stringify(output, null, 2));

  // ---- Sanity checks ----
  const totalWins: Record<string, number> = { [PLAYERS[0]]: 0, [PLAYERS[1]]: 0 };
  let totalRounds = 0;
  console.log("Per-file (score, winner):");
  for (const m of matches) {
    totalWins[PLAYERS[0]] += m.score[PLAYERS[0]];
    totalWins[PLAYERS[1]] += m.score[PLAYERS[1]];
    totalRounds += m.rounds.length;
    console.log(
      `  [${m.index}] ${m.file}: score=${JSON.stringify(m.score)} winner=${m.winner} rounds=${m.rounds.length}`
    );
  }
  console.log("Total match wins per player:", totalWins);
  console.log("Total rounds across all files:", totalRounds);
  console.log("Total matches:", matches.length);

  if (warnings.length) {
    console.error(`\n${warnings.length} warning(s):`);
    for (const w of warnings) console.error("  WARN:", w);
  } else {
    console.error("\nNo warnings.");
  }

  console.log("\nOutput written to:", outPath);
}

main();

#!/usr/bin/env python3
"""Extract facts.json from TETR.IO .ttrm replay files per SCHEMA.md."""
import json
import math
import os
import re
import sys

PARENT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
OUT_PATH = os.path.join(os.path.dirname(__file__), "facts.json")
PLAYERS = ["yachi", "pinglamb"]

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)


def x1(v):
    """floor(v + 0.5) - for values that are already in their final unit."""
    if v is None:
        return 0
    return math.floor(v + 0.5)


def x1000(v):
    """floor(v*1000 + 0.5) in IEEE-754 double arithmetic."""
    if v is None:
        return 0
    return math.floor(v * 1000 + 0.5)


def file_index(fname):
    """Match index from the filename's trailing number.

    Session-agnostic: the suffix after the final '-' is the index, and an empty
    suffix means 1 (TETR.IO names the first export of a batch without a number,
    e.g. replay-2026-07-22-.ttrm alongside replay-2026-07-22-2.ttrm).
    """
    m = re.match(r".*?-(\d*)\.ttrm$", fname)
    if not m:
        raise ValueError(f"Unexpected filename: {fname}")
    return int(m.group(1)) if m.group(1) else 1


def get(d, key, default, ctx):
    if d is None:
        warn(f"{ctx}: parent dict is None, field '{key}' -> default {default}")
        return default
    v = d.get(key, None)
    if v is None:
        warn(f"{ctx}: missing/null field '{key}' -> default {default}")
        return default
    return v


def extract_leaderboard_entry(entry, ctx):
    stats = entry.get("stats") or {}
    if not entry.get("stats"):
        warn(f"{ctx}: missing/null 'stats' -> defaults for stats fields")
    return {
        "wins": get(entry, "wins", 0, ctx),
        "apm_x1000": x1000(get(stats, "apm", 0, ctx + ".stats")),
        "pps_x1000": x1000(get(stats, "pps", 0, ctx + ".stats")),
        "vs_x1000": x1000(get(stats, "vsscore", 0, ctx + ".stats")),
        "garbagesent": get(stats, "garbagesent", 0, ctx + ".stats"),
        "garbagereceived": get(stats, "garbagereceived", 0, ctx + ".stats"),
        "kills": get(stats, "kills", 0, ctx + ".stats"),
    }


def extract_clears(clears, ctx):
    if clears is None:
        warn(f"{ctx}: missing/null 'clears' -> defaults 0 for all clear fields")
        clears = {}
    return {
        "singles": get(clears, "singles", 0, ctx),
        "doubles": get(clears, "doubles", 0, ctx),
        "triples": get(clears, "triples", 0, ctx),
        "quads": get(clears, "quads", 0, ctx),
        "tspin_singles": get(clears, "tspinsingles", 0, ctx),
        "tspin_doubles": get(clears, "tspindoubles", 0, ctx),
        "tspin_triples": get(clears, "tspintriples", 0, ctx),
        "mini_tspin_singles": get(clears, "minitspinsingles", 0, ctx),
        "mini_tspin_doubles": get(clears, "minitspindoubles", 0, ctx),
        "mini_tspin_triples": get(clears, "minitspintriples", 0, ctx),
        "tspin_quads": get(clears, "tspinquads", 0, ctx),
        "pentas": get(clears, "pentas", 0, ctx),
        "real_tspins": get(clears, "realtspins", 0, ctx),
        "mini_tspins": get(clears, "minitspins", 0, ctx),
        "allclear": get(clears, "allclear", 0, ctx),
    }


def extract_garbage_events(events, ctx):
    out = []
    if events is None:
        warn(f"{ctx}: missing/null 'events' -> empty garbage_events")
        return out
    for e in events:
        if e.get("type") != "ige":
            continue
        data = e.get("data") or {}
        if data.get("type") != "interaction_confirm":
            continue
        inner = data.get("data") or {}
        if inner.get("type") != "garbage":
            continue
        frame = data.get("frame")
        amt = inner.get("amt")
        if frame is None:
            warn(f"{ctx}: garbage ige event missing 'data.frame' -> default 0")
            frame = 0
        if amt is None:
            warn(f"{ctx}: garbage ige event missing 'data.data.amt' -> default 0")
            amt = 0
        out.append({"frame": frame, "amt": amt})
    return out


def extract_round_player(player, ctx):
    username = player.get("username")
    if username is None:
        warn(f"{ctx}: missing 'username'")
    stats = player.get("stats")
    if stats is None:
        warn(f"{ctx}: missing/null 'stats' -> defaults for top-level stats fields")
        stats = {}

    replay = player.get("replay") or {}
    if not player.get("replay"):
        warn(f"{ctx}: missing/null 'replay' -> defaults for results/events fields")
    results = replay.get("results") or {}
    if replay and not replay.get("results"):
        warn(f"{ctx}: missing/null 'replay.results' -> defaults for results fields")
    rstats = results.get("stats") or {}
    if results and not results.get("stats"):
        warn(f"{ctx}: missing/null 'replay.results.stats' -> defaults")

    garbage = rstats.get("garbage")
    if rstats and garbage is None:
        warn(f"{ctx}: missing/null 'results.stats.garbage' -> defaults 0")
    garbage = garbage or {}

    finesse = rstats.get("finesse")
    if rstats and finesse is None:
        warn(f"{ctx}: missing/null 'results.stats.finesse' -> defaults 0")
    finesse = finesse or {}

    clears = rstats.get("clears") if rstats else None

    events = replay.get("events")

    return username, {
        "lifetime": get(player, "lifetime", 0, ctx),
        "alive": bool(get(player, "alive", False, ctx)),
        "apm_x1000": x1000(get(stats, "apm", 0, ctx + ".stats")),
        "pps_x1000": x1000(get(stats, "pps", 0, ctx + ".stats")),
        "vs_x1000": x1000(get(stats, "vsscore", 0, ctx + ".stats")),
        "garbagesent": get(stats, "garbagesent", 0, ctx + ".stats"),
        "garbagereceived": get(stats, "garbagereceived", 0, ctx + ".stats"),
        "kills": get(stats, "kills", 0, ctx + ".stats"),
        "lines": get(rstats, "lines", 0, ctx + ".results.stats"),
        "pieces": get(rstats, "piecesplaced", 0, ctx + ".results.stats"),
        "inputs": get(rstats, "inputs", 0, ctx + ".results.stats"),
        "holds": get(rstats, "holds", 0, ctx + ".results.stats"),
        "topcombo": get(rstats, "topcombo", 0, ctx + ".results.stats"),
        "topbtb": get(rstats, "topbtb", 0, ctx + ".results.stats"),
        "tspins": get(rstats, "tspins", 0, ctx + ".results.stats"),
        "clears": extract_clears(clears, ctx + ".results.stats.clears"),
        "garbage_attack": get(garbage, "attack", 0, ctx + ".results.stats.garbage"),
        "garbage_cleared": get(garbage, "cleared", 0, ctx + ".results.stats.garbage"),
        "maxspike": get(garbage, "maxspike", 0, ctx + ".results.stats.garbage"),
        "finesse_faults": get(finesse, "faults", 0, ctx + ".results.stats.finesse"),
        "finesse_perfect": get(finesse, "perfectpieces", 0, ctx + ".results.stats.finesse"),
        "finesse_combo": get(finesse, "combo", 0, ctx + ".results.stats.finesse"),
        "score": get(rstats, "score", 0, ctx + ".results.stats"),
        "combo_power": get(rstats, "combopower", 0, ctx + ".results.stats"),
        "btb_power": get(rstats, "btbpower", 0, ctx + ".results.stats"),
        "garbage_sent_raw": get(garbage, "sent", 0, ctx + ".results.stats.garbage"),
        "garbage_sent_nomult": get(garbage, "sent_nomult", 0, ctx + ".results.stats.garbage"),
        "maxspike_nomult": get(garbage, "maxspike_nomult", 0, ctx + ".results.stats.garbage"),
        "garbage_received_raw": get(garbage, "received", 0, ctx + ".results.stats.garbage"),
        "finaltime_ms": x1(get(rstats, "finaltime", 0, ctx + ".results.stats")),
        "gameoverreason": str(get(results, "gameoverreason", "", ctx + ".results")),
        "garbage_events": extract_garbage_events(events, ctx + ".replay.events"),
    }


def extract_match(fname):
    path = os.path.join(PARENT_DIR, fname)
    with open(path) as f:
        d = json.load(f)

    idx = file_index(fname)
    ts = d.get("ts")
    if ts is None:
        warn(f"{fname}: missing/null top-level 'ts'")

    replay = d["replay"]
    leaderboard_list = replay.get("leaderboard") or []
    leaderboard = {}
    score = {}
    for entry in leaderboard_list:
        uname = entry.get("username")
        if uname not in PLAYERS:
            warn(f"{fname}: unexpected leaderboard username '{uname}'")
            continue
        leaderboard[uname] = extract_leaderboard_entry(entry, f"{fname}.leaderboard[{uname}]")
        score[uname] = leaderboard[uname]["wins"]

    for p in PLAYERS:
        if p not in leaderboard:
            warn(f"{fname}: player '{p}' missing from leaderboard -> defaults 0")
            leaderboard[p] = {
                "wins": 0, "apm_x1000": 0, "pps_x1000": 0, "vs_x1000": 0,
                "garbagesent": 0, "garbagereceived": 0, "kills": 0,
            }
            score[p] = 0

    winner = max(PLAYERS, key=lambda p: leaderboard[p]["wins"])

    rounds_out = []
    for r_idx, round_players in enumerate(replay.get("rounds") or []):
        if len(round_players) != 2:
            warn(f"{fname}.rounds[{r_idx}]: expected 2 players, got {len(round_players)}")
        players_out = {}
        round_winner = None
        for p_obj in round_players:
            uname, pdata = extract_round_player(p_obj, f"{fname}.rounds[{r_idx}].{p_obj.get('username')}")
            players_out[uname] = pdata
            if pdata["alive"]:
                if round_winner is not None:
                    warn(f"{fname}.rounds[{r_idx}]: multiple players alive==true")
                round_winner = uname
        if round_winner is None:
            warn(f"{fname}.rounds[{r_idx}]: no player alive==true -> winner=None")
        rounds_out.append({
            "index": r_idx,
            "winner": round_winner,
            "players": players_out,
        })

    return {
        "index": idx,
        "file": fname,
        "ts": ts,
        "winner": winner,
        "score": {p: score[p] for p in PLAYERS},
        "leaderboard": leaderboard,
        "rounds": rounds_out,
    }


def main():
    files = [f for f in os.listdir(PARENT_DIR) if f.endswith(".ttrm")]
    if not files:
        raise SystemExit(f"no .ttrm files found in {PARENT_DIR}")

    matches = [extract_match(f) for f in files]
    matches.sort(key=lambda m: m["index"])

    facts = {
        "players": PLAYERS,
        "matches": matches,
    }

    with open(OUT_PATH, "w") as f:
        json.dump(facts, f, indent=2)

    for w in WARNINGS:
        print(f"WARNING: {w}", file=sys.stderr)

    print(f"Wrote {OUT_PATH} with {len(matches)} matches, {len(WARNINGS)} warnings.", file=sys.stderr)


if __name__ == "__main__":
    main()

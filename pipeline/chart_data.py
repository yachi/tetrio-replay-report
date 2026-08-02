"""Derive the report's `chart-data` island from facts.json.

The island is what every chart in report.html reads: the per-match scoreboard
strip, the VS small multiples, the clear-type bars, the tape chart and the match
timeline all parse this one JSON blob. It used to be baked into the HTML by
hand, which meant the charts could disagree with facts.json and no gate would
notice — the opposite of what this repo claims about its numbers.

Everything here is a pure function of facts.json. The x1000 integers are divided
back to floats *only* at this boundary, because the charts plot them; claims
never see a float.
"""

CLEAR_KEYS = ["singles", "doubles", "triples", "quads",
              "tspin_singles", "tspin_doubles", "tspin_triples", "allclear"]

# T-spins that cleared lines, by size. The raw `tspins` counter is deliberately
# NOT part of this sum: it counts spins that cleared nothing, so it is larger,
# and conflating the two has misread the clear chart before.
TSPIN_CLEAR_KEYS = ["tspin_singles", "tspin_doubles", "tspin_triples"]
MINI_TSPIN_KEYS = ["mini_tspin_singles", "mini_tspin_doubles", "mini_tspin_triples"]


def _x(v):
    """An x1000 integer back to the float the charts plot."""
    return v / 1000


def per_match(facts):
    p1, p2 = facts["players"]
    out = []
    for m in facts["matches"]:
        lb = m["leaderboard"]
        row = {"index": m["index"],
               "score": {p1: m["score"][p1], p2: m["score"][p2]},
               "winner": m["winner"]}
        for pl in (p1, p2):
            row[pl] = {"apm": _x(lb[pl]["apm_x1000"]),
                       "pps": _x(lb[pl]["pps_x1000"]),
                       "vs": _x(lb[pl]["vs_x1000"])}
        out.append(row)
    return out


def grouped_clears(facts):
    p1, p2 = facts["players"]
    out = {pl: {k: 0 for k in CLEAR_KEYS} for pl in (p1, p2)}
    for pl in (p1, p2):
        out[pl]["tspin_total"] = 0
        out[pl]["mini_tspin_total"] = 0
    for m in facts["matches"]:
        for r in m["rounds"]:
            for pl, p in r["players"].items():
                c = p["clears"]
                for k in CLEAR_KEYS:
                    out[pl][k] += c.get(k, 0)
                out[pl]["tspin_total"] += sum(c.get(k, 0) for k in TSPIN_CLEAR_KEYS)
                out[pl]["mini_tspin_total"] += sum(c.get(k, 0) for k in MINI_TSPIN_KEYS)
    return out


def totals(facts):
    """Session totals per player, plus the four rates the tape chart plots.

    `queued_garbage` is the sum of the ige interaction_confirm amounts — attack
    aimed at the player *before* cancelling — and is consistently larger than
    `garbagereceived`, which is what actually materialised as garbage rows. The
    gap between them is the cancel rate. The report says 射埋 vs 食 for exactly
    this reason and the two must never be summed together.
    """
    p1, p2 = facts["players"]
    sums = ["pieces", "garbage_attack", "garbage_cleared", "garbagereceived",
            "finesse_faults", "finesse_perfect", "holds", "kills"]
    # Counts stay ints (they are counts); the four rates below are the only floats.
    out: dict[str, dict[str, float]] = {pl: {k: 0 for k in sums} for pl in (p1, p2)}
    for pl in (p1, p2):
        out[pl].update(topbtb_max=0, topcombo_max=0, queued_garbage=0,
                       tspins_raw_total=0)
    for m in facts["matches"]:
        for r in m["rounds"]:
            for pl, p in r["players"].items():
                t = out[pl]
                for k in sums:
                    t[k] += p.get(k, 0)
                t["topbtb_max"] = max(t["topbtb_max"], p["topbtb"])
                t["topcombo_max"] = max(t["topcombo_max"], p["topcombo"])
                t["queued_garbage"] += sum(g["amt"] for g in p["garbage_events"])
                t["tspins_raw_total"] += p["tspins"]
    for pl in (p1, p2):
        t = out[pl]
        pieces = t["pieces"]
        t["finesse_fault_rate"] = t["finesse_faults"] / pieces if pieces else 0
        t["finesse_perfect_rate"] = t["finesse_perfect"] / pieces if pieces else 0
        t["attack_per_piece"] = t["garbage_attack"] / pieces if pieces else 0
        t["hold_rate"] = t["holds"] / pieces if pieces else 0
        q = t["queued_garbage"]
        t["cancel_rate"] = (q - t["garbagereceived"]) / q if q else 0
    return out


def round_series(facts):
    """Every round in session order — the x axis of the VS small multiples."""
    p1, p2 = facts["players"]
    out = []
    g = 0
    for m in facts["matches"]:
        for ri, r in enumerate(m["rounds"]):
            row = {"g": g, "match": m["index"], "round_in_match": ri,
                   "winner": r["winner"]}
            for pl in (p1, p2):
                p = r["players"][pl]
                row[pl] = {"vs": _x(p["vs_x1000"]), "apm": _x(p["apm_x1000"]),
                           "pps": _x(p["pps_x1000"]),
                           "lifetime_s": _x(p["lifetime"])}
            out.append(row)
            g += 1
    return out


def match_boundaries(facts):
    """Where each match starts in `round_series`, so a chart can band by match."""
    out = []
    g = 0
    for m in facts["matches"]:
        n = len(m["rounds"])
        out.append({"index": m["index"], "start_g": g, "n_rounds": n})
        g += n
    return out


def extreme_rounds(facts):
    """The session's longest and shortest round, as indices into `round_series`.

    The small multiples mark these rounds. They used to be a literal in the inline
    script — `r.g === 14 || r.g === 26` — computed once for 2026-07-24 and then
    copied forward into 07-28 and 08-01 along with the rest of the report. In those
    two sessions the marks landed on two unremarkable rounds (a 53s and a 75s; an
    85s and a 25s) while the actual extremes went unmarked: 07-28's 168-second
    marathon and 08-01's 206-second one.

    Nothing could have caught that, because a hardcoded index is never *wrong* in a
    way a checker can see — it is just about a different session. Deriving it here
    puts it inside `build_report --check`, so it cannot be stale again.
    """
    rows = round_series(facts)
    if not rows:
        return {}
    dur = {}
    g = 0
    for m in facts["matches"]:
        for r in m["rounds"]:
            dur[g] = max(d["lifetime"] for d in r["players"].values())
            g += 1
    return {"longest_g": max(dur, key=lambda k: dur[k]),
            "shortest_g": min(dur, key=lambda k: dur[k])}


def build(facts):
    # `players` is emitted so the page's renderers can key by position instead of
    # by name; the inline script used to say `m.score.yachi` outright, which is
    # what stopped a report from being reused for any other pair of players.
    return {"players": list(facts["players"]),
            "per_match": per_match(facts),
            "grouped_clears": grouped_clears(facts),
            "totals": totals(facts),
            "round_series": round_series(facts),
            "extreme_rounds": extreme_rounds(facts),
            "match_boundaries": match_boundaries(facts)}

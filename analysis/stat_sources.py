"""Re-derive every corpus figure CLAUDE.md publishes about the THREE stat objects.

    python3 -m analysis.stat_sources            # print every figure
    python3 -m analysis.stat_sources --json     # the same, as JSON

A round carries three stat objects — `player.stats` (a live in-game tick),
`player.replay.results.stats` (the final snapshot) and `results.aggregatestats` (the final
rate triple) — and CLAUDE.md's two long bullets about them are almost entirely counts of how
often those three disagree. Every one of those counts was measured ONCE, by hand, over the
760 player-rounds of the first six sessions, and typed into prose. The corpus reached 900 and
nothing said so: they were the 冇第二份 class, honestly scoped ("measured over the first six
sessions, not re-run") and therefore never red.

This module is what re-derives them, and `pipeline/check_stat_sources.py` is the gate that
compares the published sentences against it. Nothing here reads a session list — the replays
are globbed off disk, so a session added is a session measured.

WHERE EACH FIGURE COMES FROM, because two of them cannot come from the same place.
`facts.json` keeps ONE source per field by design: the rate triple is `aggregatestats`, and
`kills`/`garbagesent`/`garbagereceived` are the live tick. So a count of how often two sources
disagree cannot be computed from `facts.json` at all — it has to read the `.ttrm`. The one
figure that must NOT be read from the `.ttrm` is the VS-split guard's firing count, because
the guard runs over `facts.json`'s rounded integers (`vs_x1000`, `finaltime_ms`) and a float
reconstruction of it would be a different question wearing the same words.
"""
import argparse
import glob
import json
import math
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VS_K = 100_000_000                      # pipeline/claims/generators._VS_K
GUARD_TRIGGER = VS_K / 2                # `resid * 2 >= _VS_K` in intense_round_vs_split

# The rate triple, named in BOTH objects. `player.stats` spells the third `vsscore` and so
# does `aggregatestats`; writing `vs` here made every one of the 900 rounds look stale, which
# is the kind of wrong that reads like a finding.
RATE_KEYS = ("apm", "pps", "vsscore")


def replay_files(root=REPO):
    """Every `.ttrm` on disk, sorted. No session list: a session added is a session measured."""
    return sorted(glob.glob(os.path.join(root, "sessions", "*", "*.ttrm")))


def player_rounds(root=REPO):
    """One row per player-round, carrying all three stat objects unmerged."""
    rows = []
    for path in replay_files(root):
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
        for ri, pair in enumerate(raw["replay"].get("rounds") or []):
            for p in pair:
                res = (p.get("replay") or {}).get("results") or {}
                rows.append({
                    "file": os.path.basename(path), "round": ri,
                    "user": p.get("username"), "alive": bool(p.get("alive")),
                    "tick": p.get("stats") or {},
                    "final": res.get("stats") or {},
                    "agg": res.get("aggregatestats") or {},
                })
    return rows


def leaderboard_entries(root=REPO):
    out = []
    for path in replay_files(root):
        with open(path, encoding="utf-8") as fh:
            out += list(json.load(fh)["replay"].get("leaderboard") or [])
    return out


def facts_rounds(root=REPO):
    """One row per player-round out of the committed facts.json — the extracted view."""
    rows = []
    for fj in sorted(glob.glob(os.path.join(root, "sessions", "*", "report", "facts.json"))):
        with open(fj, encoding="utf-8") as fh:
            fa = json.load(fh)
        for mi, m in enumerate(fa["matches"]):
            for ri, r in enumerate(m["rounds"]):
                for pl, d in r["players"].items():
                    rows.append({"session": os.path.basename(os.path.dirname(
                        os.path.dirname(fj))), "m": mi + 1, "r": ri + 1, "user": pl, **d})
    return rows


def derive(root=REPO):
    rows, facts = player_rounds(root), facts_rounds(root)
    n = len(rows)
    out = {"player_rounds": n, "sessions": len(set(os.path.basename(os.path.dirname(p))
                                                   for p in replay_files(root)))}

    # --- the live tick against the final rate triple ------------------------------------
    stale = [r for r in rows if any(r["tick"].get(k) != r["agg"].get(k) for k in RATE_KEYS)]
    out["tick_stale"] = len(stale)
    out["tick_stale_survivor"] = sum(1 for r in stale if r["alive"])
    out["tick_apm_high"] = sum(1 for r in stale
                               if (r["tick"].get("apm") or 0) > (r["agg"].get("apm") or 0))

    # --- T recovered from pps, and the two finaltime routes that do not work -------------
    worst_int = worst_apm = worst_vs = 0.0
    floor_wrong, worst_floor = 0, 0.0
    worst_secs, secs_over = 0.0, 0
    for r in rows:
        pieces, pps = r["final"].get("piecesplaced"), r["agg"].get("pps")
        g = r["final"].get("garbage") or {}
        atk, cle = g.get("attack"), g.get("cleared")
        vs, apm, ft = r["agg"].get("vsscore"), r["agg"].get("apm"), r["final"].get("finaltime")
        if not pps or pieces is None or atk is None or cle is None:
            continue
        frames = 60.0 * pieces / pps
        worst_int = max(worst_int, abs(frames - round(frames)))
        T = round(frames) / 60.0
        if apm:
            worst_apm = max(worst_apm, abs(60.0 * atk / T - apm) / apm)
        if vs:
            worst_vs = max(worst_vs, abs(100.0 * (atk + cle) / T - vs) / vs)
        if ft is None:
            continue
        ft_ms = math.floor(ft + 0.5)                     # extract.py's x1

        def resid_at(t):
            """The worst relative residual over ALL THREE rates at a candidate clock `t`.

            All three, not VS alone. The published 「245 of the 760」 is 245 only when PPS is
            in the max — VS and APM alone give 243, and the two rounds between them are the
            whole difference. The reconstruction is of `aggregatestats`, which is a triple, so
            the triple is what a route has to reproduce.
            """
            worst = 0.0
            for value, model in ((apm, 60.0 * atk / t), (vs, 100.0 * (atk + cle) / t),
                                 (r["agg"].get("pps"), pieces / t)):
                if value:
                    worst = max(worst, abs(model - value) / value)
            return worst

        if math.floor(ft_ms * 60 / 1000) != round(frames):
            floor_wrong += 1
            Tf = math.floor(ft_ms * 60 / 1000) / 60.0
            if Tf:
                worst_floor = max(worst_floor, resid_at(Tf))
        Ts = ft_ms / 1000.0
        if Ts:
            d = resid_at(Ts)
            worst_secs = max(worst_secs, d)
            secs_over += d > 1e-4
    out.update(frames_integer_to=worst_int, resid_apm=worst_apm, resid_vs=worst_vs,
               floor_wrong=floor_wrong, floor_worst=worst_floor,
               secs_worst=worst_secs, secs_over_1e4=secs_over)

    # --- the T-free identity: the checkable form, with no frame count in it ---------------
    worst_free, n_free = 0.0, 0
    for r in rows:
        g = r["final"].get("garbage") or {}
        atk, cle = g.get("attack"), g.get("cleared")
        apm, vs = r["agg"].get("apm"), r["agg"].get("vsscore")
        if not apm or not vs or atk is None or cle is None:
            continue
        n_free += 1
        lhs, rhs = vs * 60.0 * atk, apm * 100.0 * (atk + cle)
        scale = max(abs(lhs), abs(rhs))
        if scale:
            worst_free = max(worst_free, abs(lhs - rhs) / scale)
    out.update(identity_worst=worst_free, identity_rounds=n_free)

    # --- kills, which runs the OTHER way --------------------------------------------------
    kdiff = [r for r in rows if r["final"].get("kills") != r["tick"].get("kills")]
    out["kills_disagree"] = len(kdiff)
    out["kills_live1_final0_survivor"] = sum(
        1 for r in kdiff
        if (r["tick"].get("kills"), r["final"].get("kills"), r["alive"]) == (1, 0, True))

    # --- the two garbage counters, which are a different measure anyway -------------------
    for tick_key, final_key in (("garbagesent", "sent"), ("garbagereceived", "received")):
        out[f"{tick_key}_differ"] = sum(
            1 for r in rows
            if r["tick"].get(tick_key) != (r["final"].get("garbage") or {}).get(final_key))

    # --- finesse: two units, four defensible rates, one of them meaningless ---------------
    faults = perfect = pieces_tot = 0
    nonperf_rounds = faults_exceed = 0
    worst_ratio, worst_row = 0.0, None
    for r in rows:
        fin = r["final"].get("finesse") or {}
        f, pf, pc = fin.get("faults"), fin.get("perfectpieces"), r["final"].get("piecesplaced")
        if f is None or pf is None or pc is None:
            continue
        faults += f
        perfect += pf
        pieces_tot += pc
        nonperf = pc - pf
        if nonperf > 0:
            nonperf_rounds += 1
            faults_exceed += f > nonperf
            if f / nonperf > worst_ratio:
                worst_ratio, worst_row = f / nonperf, (r["file"], r["round"], r["user"], f, nonperf)
    out.update(finesse_faults=faults, finesse_nonperfect=pieces_tot - perfect,
               finesse_per_faulty_piece=faults / (pieces_tot - perfect),
               finesse_faults_exceed=faults_exceed, finesse_nonperfect_rounds=nonperf_rounds,
               finesse_fault_rate=100 * faults / pieces_tot,
               finesse_faulty_share=100 * (1 - perfect / pieces_tot),
               finesse_tetrio_figure=100 * perfect / pieces_tot,
               finesse_meaningless=100 * faults / (faults + perfect),
               finesse_worst_round=worst_row)

    # --- the VS-split guard, over facts.json's integers, which is where the guard runs ----
    fires, worst_frac, worst_guard = 0, 0.0, None
    for d in facts:
        resid = abs(d["vs_x1000"] * d["finaltime_ms"]
                    - VS_K * (d["garbage_attack"] + d["garbage_cleared"]))
        if resid >= GUARD_TRIGGER:
            fires += 1
        frac = resid / GUARD_TRIGGER
        if frac > worst_frac:
            worst_frac = frac
            worst_guard = (d["session"], d["m"], d["r"], d["user"],
                           d["garbage_attack"] + d["garbage_cleared"])
    out.update(vs_guard_rounds=len(facts), vs_guard_fires=fires,
               vs_guard_worst_frac=worst_frac, vs_guard_worst=worst_guard,
               vs_guard_headroom=(1 / worst_frac) if worst_frac else None,
               vs_guard_would_need=(round(worst_guard[4] / worst_frac)
                                    if worst_frac and worst_guard else None))

    # --- the leaderboard has no aggregatestats, which is why it stays on the live tick ----
    lb = leaderboard_entries(root)
    out["leaderboard_entries"] = len(lb)
    out["leaderboard_with_agg"] = sum(1 for e in lb if e.get("aggregatestats"))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    d = derive()
    if args.json:
        print(json.dumps(d, indent=2, sort_keys=True, default=list))
        return 0
    for k in sorted(d):
        print(f"{k:32} {d[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Why one player's attack per piece is higher than the other's — the corpus roll-up.

    python3 -m analysis.app_decomposition           # print every figure
    python3 -m analysis.app_decomposition --json    # the same, as JSON

Reads every committed `sessions/*/sim/attack-facts.json` (globbed, no session list) and rolls the
per-session counts up into the figures CLAUDE.md publishes in 「每粒攻擊點解爭」. Nothing here
re-runs the engine: the per-session artefacts are byte-gated by `pipeline/sim/attack-facts.test.ts`,
so a figure derived from them cannot drift from the replays without that test going red first, and
there is no committed corpus JSON to go stale beside them.

The decomposition is `pipeline.attack_section.decompose`, the SAME function the report section
prints, so the corpus figure and each session's figure cannot use two definitions of one split.
`pipeline/check_app_decomposition.py` is the gate on the published sentences.

Trust tier: the clear-type COUNTS are anchored per player-round against the replay's own counters
(see the `anchor` totals below); attack per clear and the component split are one engine's. The
sentences that quote these figures must say which kind each is.
"""
import argparse
import glob
import json
import os
from fractions import Fraction

from pipeline.attack_section import decompose

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FACTS = os.path.join("sim", "attack-facts.json")


def artefacts(root=REPO):
    """Every session's artefact, by session date. No list: a session emitted is a session counted."""
    out = {}
    for path in sorted(glob.glob(os.path.join(root, "sessions", "*", FACTS))):
        with open(path, encoding="utf-8") as fh:
            out[os.path.basename(os.path.dirname(os.path.dirname(path)))] = json.load(fh)
    return out


def _add_window(acc, w):
    acc["pieces"] += w["pieces"]
    acc["attack"] += w["attack"]
    acc["lines"] += w["lines"]
    for k, c in w["classes"].items():
        cell = acc["classes"].setdefault(k, {"n": 0, "attack": 0})
        cell["n"] += c["n"]
        cell["attack"] += c["attack"]
    for k, v in w["components"].items():
        acc["components"][k] = acc["components"].get(k, 0) + v


def _empty_player(user):
    win = lambda: {"pieces": 0, "attack": 0, "lines": 0, "classes": {}, "components": {}}  # noqa: E731
    return {"user": user, "rounds": 0, "pieces": 0, "attack": 0, "lines": 0,
            "windows": {"opener": win(), "mid": win()}}


def pool(arts):
    """Per-user totals over the given artefacts, in the artefact's own player shape."""
    P = {}
    for a in arts:
        for p in a["players"]:
            q = P.setdefault(p["user"], _empty_player(p["user"]))
            for k in ("rounds", "pieces", "attack", "lines"):
                q[k] += p[k]
            for w in ("opener", "mid"):
                _add_window(q["windows"][w], p["windows"][w])
    return P


def _hi_lo(P):
    a, b = sorted(P.values(), key=lambda p: Fraction(p["attack"], p["pieces"]))
    return b, a


def _class_rate(p, k, window=None):
    ws = (window,) if window else ("opener", "mid")
    return Fraction(sum(p["windows"][w]["classes"].get(k, {"n": 0})["n"] for w in ws), p["pieces"])


def derive(root=REPO):
    arts = artefacts(root)
    if not arts:
        raise SystemExit("app_decomposition: no sessions/*/sim/attack-facts.json — emit them first")
    P = pool(arts.values())
    if len(P) != 2:
        raise SystemExit(f"app_decomposition: expected two players, found {sorted(P)}")
    hi, lo = _hi_lo(P)
    d = decompose(hi, lo)

    # per-session sign of the clear-type rate gap, hi minus lo
    signs = {}
    for k in ("TSD", "TST", "Q", "TSS"):
        n = 0
        for a in arts.values():
            by = {p["user"]: p for p in a["players"]}
            n += _class_rate(by[hi["user"]], k) > _class_rate(by[lo["user"]], k)
        signs[k] = n

    # match-level jackknife: the gap with each match removed, exhaustively (no seed, no draw)
    rows = [r for a in arts.values() for r in a["per_match"]]
    matches = sorted({r["file"] for r in rows})
    tot = {u: [0, 0] for u in P}
    for r in rows:
        tot[r["user"]][0] += r["attack"]
        tot[r["user"]][1] += r["pieces"]
    drops = []
    for f in matches:
        t = {u: list(v) for u, v in tot.items()}
        for r in rows:
            if r["file"] == f:
                t[r["user"]][0] -= r["attack"]
                t[r["user"]][1] -= r["pieces"]
        drops.append(Fraction(*t[hi["user"]]) - Fraction(*t[lo["user"]]))

    by_window = {k: {u: (P[u]["windows"]["opener"]["classes"].get(k, {"n": 0})["n"],
                         P[u]["windows"]["mid"]["classes"].get(k, {"n": 0})["n"]) for u in P}
                 for k in ("TSD", "TST")}
    windows = {a["window_pieces"] for a in arts.values()}
    if len(windows) != 1:
        raise SystemExit(f"app_decomposition: sessions disagree on window_pieces {sorted(windows)}")

    anchor = {k: {"rounds": sum(a["anchor"][k]["rounds"] for a in arts.values()),
                  "agree": sum(a["anchor"][k]["agree"] for a in arts.values())}
              for k in ("attack", "counts")}
    return {
        "sessions": len(arts), "matches": len(matches),
        "hi": hi, "lo": lo, "decomposition": d, "signs": signs,
        "jackknife": (min(drops), max(drops)),
        "replay_gap": Fraction(hi["attack"], hi["pieces"]) - Fraction(lo["attack"], lo["pieces"]),
        "anchor": anchor, "by_window": by_window, "window_pieces": windows.pop(),
    }


def _jsonable(x):
    if isinstance(x, Fraction):
        return float(x)
    if isinstance(x, dict):
        return {k: _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x


def main(argv=None):
    ap = argparse.ArgumentParser(description="the APP-gap corpus roll-up")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    d = derive()
    if args.json:
        print(json.dumps(_jsonable(d), indent=1, ensure_ascii=False))
        return 0
    dd = d["decomposition"]
    print(f"{d['sessions']} sessions, {d['matches']} matches; anchors {d['anchor']}")
    for p in (d["lo"], d["hi"]):
        print(f"  {p['user']:9} APP {p['attack'] / p['pieces']:.4f}  lines/piece {p['lines'] / p['pieces']:.4f}"
              f"  attack/line {p['attack'] / p['lines']:.4f}")
    print(f"  gap x100 (engine) {float(dd['gap']) * 100:+.3f}  opener {float(dd['windows']['opener']) * 100:+.3f}"
          f"  mid {float(dd['windows']['mid']) * 100:+.3f}  mix {float(dd['mix']) * 100:+.3f}"
          f"  value {float(dd['value']) * 100:+.3f}")
    for k, m, v in sorted(dd["terms"], key=lambda t: -abs(t[1])):
        print(f"    {k:5} mix {float(m) * 100:+.3f}  value {float(v) * 100:+.3f}")
    print(f"  sessions with {d['hi']['user']} higher: {d['signs']}")
    print(f"  jackknife over matches, gap x100: [{float(d['jackknife'][0]) * 100:.3f}, "
          f"{float(d['jackknife'][1]) * 100:.3f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

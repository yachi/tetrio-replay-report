"""Gate: every 約-figure in hand-written text must be a FLOORED datum.

    python3 -m pipeline.check_prose_figures sessions/2026-07-24/report

約 means "about this much, at least" — the reports settled on flooring so the word
means one thing everywhere. A figure that was *rounded* instead reads as a
different number from the one the proofs cover: 約262.6 and 約262.5 are the same
`vs_x1000 == 262582`, and both used to appear in one report.

The generators floor by construction (`pipeline/fmt.py`), so this checks the
surfaces a person writes: the hand ledgers, the prose files, and whatever prose
sits directly in report.html. Generated regions are skipped because they are
already covered, and the claims-data island is skipped because it is built from
the ledgers this checks — reporting it too would just double-count.

A figure counts as:
  ok           some datum floors to it at that precision
  ROUNDED      no datum floors to it, but one rounds to it — a real defect
  unresolved   no datum produces it either way; printed for a human to judge,
               because it is usually a sum or a difference this cannot resolve
"""
import argparse
import glob
import json
import os
import re
import sys

from pipeline.claims import generators

def _strings(node, path=""):
    """Every string leaf in a decoded JSON document, with a dotted path label.

    Deliberately structure-agnostic: a prose file's shape is the section author's
    business, and a checker that knows the shape is a checker that stops looking
    when the shape changes.
    """
    if isinstance(node, str):
        if node.strip():
            yield path or "(root)", node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _strings(v, f"{path}[{i}]")


GENERATED = re.compile(r"<!-- BEGIN generated .*?<!-- END generated [a-z-]+ -->", re.S)
CLAIMS_ISLAND = re.compile(r"<!-- CLAIMS_DATA_START -->.*?<!-- CLAIMS_DATA_END -->", re.S)
TAG = re.compile(r"<[^>]+>")

# Every way the text marks an approximation: 約 in the Cantonese, ~ and ≈ in the
# english_gloss (which ships inside the claims island, so it is just as visible).
APPROX = r"(?:約|~|≈)"
# (regex, precision) — 2dp before 1dp, so 「約1.84」 is not read as 「約1.8」.
# `min` is excluded: a figure in minutes is floored against a different divisor,
# and the only one in the corpus is already correct.
PATTERNS = [(re.compile(APPROX + r"\s?\d+\.\d\d(?!\d)(?!\s?min)"), 2),
            (re.compile(APPROX + r"\s?\d+\.\d(?!\d)(?!\s?min)"), 1),
            (re.compile(APPROX + r"\s?\d+(?!\.)\s?(?:秒|s\b)"), 0)]
FIGURE = re.compile(r"\d+(?:\.\d+)?")


def pools(facts):
    """The integers a figure can legitimately come from."""
    x1000, lifetimes = set(), set()
    for m in facts["matches"]:
        for lb in m["leaderboard"].values():
            x1000.update(lb[k] for k in ("apm_x1000", "pps_x1000", "vs_x1000"))
        for r in m["rounds"]:
            for p in r["players"].values():
                x1000.update(p[k] for k in ("apm_x1000", "pps_x1000", "vs_x1000"))
                # Both clocks. `lifetime` and `finaltime_ms` differ by a fraction of a
                # second and floor to DIFFERENT whole seconds often enough to matter:
                # 最癲一局 prints each player's own finaltime, and 169748 ms floors to
                # 169 while no `lifetime` in that session does. Holding only one of the
                # two left a correctly floored figure unresolvable.
                lifetimes.add(p["lifetime"])
                lifetimes.add(p["finaltime_ms"])
    # The derived quantities the generators also print with 約: per-round means, and
    # the per-piece rates split by whether the round was won. Without them a correctly
    # floored derived figure matches no datum, collides with some *unrelated* datum's
    # rounded rendering, and is reported as a defect — 約0.73 (an APP rate) was read
    # as the rounding of a 0.728 PPS. The gate has to know every integer a generator
    # can legitimately format, or it cries wolf at exactly the figures it added.
    rounds = [r for m in facts["matches"] for r in m["rounds"]]
    for pl in facts["players"]:
        for k in ("apm_x1000", "pps_x1000", "vs_x1000"):
            vals = [r["players"][pl][k] for r in rounds]
            if vals:
                x1000.add(sum(vals) // len(vals))
        for f in ("garbage_attack", "inputs", "garbage_cleared"):
            for won in (True, False):
                sel = [r for r in rounds if (r["winner"] == pl) == won]
                num = sum(r["players"][pl][f] for r in sel)
                den = sum(r["players"][pl]["pieces"] for r in sel)
                if den:
                    x1000.add((num * 1000) // den)
    # 最癲一局's figures, which are derived per-ROUND and so are covered by none of the
    # above: the two halves of the VS split (10^8·counter/finaltime_ms, the same x1000
    # scale as vs_x1000) and that round's two per-piece rates. The aggregate per-piece
    # rates added just above are session-wide and floor to different integers. Without
    # these the gate reported the split's own figures as unresolved — i.e. it was
    # shrugging at exactly the numbers the new section added.
    best = generators._intense_round(facts)
    if best:
        rnd = best[2]
        for p in rnd["players"].values():
            for f in ("garbage_attack", "garbage_cleared"):
                if p["finaltime_ms"]:
                    x1000.add(generators._VS_K * p[f] // p["finaltime_ms"])
                if p["pieces"]:
                    x1000.add(1000 * p[f] // p["pieces"])
    return x1000, lifetimes


def renderings(value, precision, x1000, lifetimes):
    """(floored, rounded) sets of printable figures at this precision.

    A one-decimal figure can be an x1000 stat (約262.5) or a duration in seconds
    (約128.5秒); both are the same arithmetic on a milliseconds/×1000 integer, so
    the pools are merged for that precision.
    """
    if precision == 0:
        pool, div = lifetimes, 1000
        return ({v // div for v in pool}, {round(v / div) for v in pool})
    pool = (x1000 | lifetimes) if precision == 1 else x1000
    step = 10 ** (3 - precision)
    scale = 10 ** precision
    return ({v // step / scale for v in pool},
            {round(v / 1000, precision) for v in pool})


def surfaces(report_dir):
    """(label, identifier, text) for every published surface."""
    out = []
    # Every ledger, the generated one included. This used to list only the hand
    # ledgers, on the grounds that the generators floor by construction. They did
    # not: several families formatted the Cantonese with the flooring helper and the
    # english_gloss with a bare `:.1f`, so one claim published 約167.9 and
    # "VS 168.0" for the same datum, and the flat-rate family printed a bound
    # *tighter* than its own lemma proved. Trusting the generator is what let that
    # ship for three sessions, so the gate now measures it instead.
    for rel in sorted(n for n in os.listdir(report_dir)
                      if n.startswith("claims") and n.endswith(".json")
                      and "proof-map" not in n):
        with open(os.path.join(report_dir, rel), encoding="utf-8") as fh:
            claims = json.load(fh)
        # The gloss is checked as well as the Cantonese: it travels in the
        # claims island, so a rounded figure there is just as published.
        out += [(rel, c["id"], c["canto"]) for c in claims]
        out += [(rel, f'{c["id"]}.gloss', c.get("english_gloss") or "")
                for c in claims]
    # Every prose file, and every string in it — NOT a list of known filenames and
    # known fields. That is how this check silently narrowed once: moving 關鍵時刻
    # out of report.html and into prose/moments.json took its figures out of the
    # scan, because the region it left behind is generated (and so skipped below)
    # while the new file was not on the list. The count went DOWN and nothing said
    # so. Walking prose/*.json means the next prose file is covered on the day it
    # is written, and fields nobody thought to enumerate — hero's tags, a card's
    # title — are covered too.
    for path in sorted(glob.glob(os.path.join(report_dir, "prose", "*.json"))):
        rel = f"prose/{os.path.basename(path)}"
        with open(path, encoding="utf-8") as fh:
            out += [(rel, label, text) for label, text in _strings(json.load(fh))]
    report = os.path.join(report_dir, "report.html")
    if os.path.exists(report):
        with open(report, encoding="utf-8") as fh:
            html = fh.read()
        hand = TAG.sub(" ", CLAIMS_ISLAND.sub(" ", GENERATED.sub(" ", html)))
        out.append(("report.html", "hand-written prose", hand))
    return out


def scan(report_dir):
    with open(os.path.join(report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    x1000, lifetimes = pools(facts)
    cache = {p: renderings(None, p, x1000, lifetimes) for p in (0, 1, 2)}

    rounded, unresolved, ok = [], [], 0
    for label, ident, text in surfaces(report_dir):
        seen = set()
        for pat, precision in PATTERNS:
            for m in pat.finditer(text):
                span = (m.start(), m.end())
                if any(s <= span[0] < e for s, e in seen):
                    continue
                seen.add(span)
                figure = FIGURE.search(m.group(0)).group(0)
                value = float(figure) if precision else int(figure)
                floors, rounds = cache[precision]
                if value in floors:
                    ok += 1
                elif value in rounds:
                    rounded.append((label, ident, m.group(0).strip(), precision))
                else:
                    unresolved.append((label, ident, m.group(0).strip()))
    return ok, rounded, unresolved


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir")
    args = ap.parse_args(argv)

    ok, rounded, unresolved = scan(args.report_dir)
    for label, ident, printed in unresolved:
        print(f"  --  unresolved {label} {ident}: {printed} "
              f"(no datum prints this either way — check by hand)")
    for label, ident, printed, precision in rounded:
        print(f"FAIL {label} {ident}: {printed} is rounded, not floored "
              f"({precision} dp)", file=sys.stderr)
    if rounded:
        print(f"\n{len(rounded)} rounded figure(s): 約 must mean the floored value "
              f"everywhere, as pipeline/fmt.py emits it", file=sys.stderr)
        return 1
    print(f"  ok  {ok} 約-figures in hand-written text are all floored"
          + (f"; {len(unresolved)} unresolved" if unresolved else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

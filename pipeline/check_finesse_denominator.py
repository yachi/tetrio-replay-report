"""Gate: a per-piece rate must name its denominator, and must not pose as a share.

    python3 -m pipeline.check_finesse_denominator sessions/2026-08-14/report
    python3 -m pipeline.check_finesse_denominator sessions/2026-08-14/report --selftest

`finesse.perfectpieces` counts PIECES; `finesse.faults` counts fault EVENTS, and one
piece can register several. Pooled over six sessions that is 11 865 faults over 7 510
non-perfect pieces — 1.580 each — so the two counters are on different units and there
are four defensible "finesse fault rates":

    faults / pieces            16.83%   fault events per piece
    1 - perfect / pieces       10.65%   the share of pieces that were faulty
    perfect / pieces           89.35%   what TETR.IO itself displays
    faults / (faults+perfect)  15.85%   on no meaningful denominator

The tape chart plotted the first and labelled it 「finesse 失誤率」, formatted as
`(v*100).toFixed(1)+"%"` — so it printed 16.8% under a label a reader parses as the
second, which is 10.65%. It shipped in all six reports.

Two rules, because the defect has two halves:

1. **The label must name the denominator.** 「每粒」 in the row label, matching
   「每粒攻擊」 beside it and `generators.py`'s 「每粒方塊嘅 finesse 失誤」.
2. **A percentage rendering asserts a share, so an unbounded per-piece rate may not
   use one.** This is the half a label alone does not fix: 16.8% reads as a share
   whatever the label says. The corpus refutes the share reading directly — in 650 of
   750 player-rounds the faults outnumber the non-perfect pieces, and 07-24 m2r0 puts
   7 faults on a single non-perfect piece. `hold_rate` keeps its percentage because a
   hold IS at most one per piece; that is what `SHARE` records.

Every accessor the chart reads must be classified. An unclassified key fails rather
than passing unchecked, so adding a row forces the COUNT/SHARE/EVENT_RATE decision
instead of leaving it to whoever writes the label.

**This gate reads the whole document, generated regions included** — unlike
`check_prose_figures`, which skips them on the grounds that the generators are
disciplined. The tape chart is neither: its renderer lives in each session's committed
shell, outside every generated region, so `build_report --check` never saw it and the
mislabel survived six sessions. A gate that skipped the un-generated shell would have
skipped the only place this bug has ever lived.
"""
import argparse
import glob
import json
import os
import re
import sys

# What each `chart_data.totals` key the tape chart can plot actually is.
#   COUNT       an absolute count — nothing to name
#   SHARE       numerator and denominator are the same unit, bounded by 1 — a
#               percentage is honest and the noun already implies the denominator
#   EVENT_RATE  events over pieces, NOT bounded by 1 — must name 每粒 and must not
#               be rendered as a percentage
COUNT, SHARE, EVENT_RATE = "COUNT", "SHARE", "EVENT_RATE"
KINDS = {
    "pieces": COUNT,
    "garbage_attack": COUNT,
    "garbage_cleared": COUNT,
    "garbagereceived": COUNT,
    "queued_garbage": COUNT,
    "finesse_faults": COUNT,
    "finesse_perfect": COUNT,
    "holds": COUNT,
    "kills": COUNT,
    "topbtb_max": COUNT,
    "topcombo_max": COUNT,
    "tspins_raw_total": COUNT,
    # a hold is at most one per piece, and a cancel is a fraction of what was queued
    "hold_rate": SHARE,
    "cancel_rate": SHARE,
    # perfect pieces ARE pieces, so this one is a share of the same unit
    "finesse_perfect_rate": SHARE,
    # lines of attack per piece, and fault EVENTS per piece — neither bounded by 1
    "attack_per_piece": EVENT_RATE,
    "finesse_fault_rate": EVENT_RATE,
}

# Ways a label can name pieces as the denominator.
DENOMINATOR = ("每粒", "每一粒", "per piece", "per-piece")

# A row of the tape chart, in either shape the committed reports use: the newer
# positional accessor, and the player-hardcoded one that four reports still carry.
ROW = re.compile(
    r'\{\s*label:\s*"(?P<label>[^"]*)"\s*,\s*'
    r'(?:get:\s*function\s*\(s\)\s*\{\s*return\s+s\.(?P<key1>\w+);\s*\}'
    r'|y:\s*t\.\w+\.(?P<key2>\w+)\s*,\s*p:\s*t\.\w+\.\w+)'
    r'\s*,\s*fmt:\s*function\s*\(v\)\s*\{\s*return\s+(?P<fmt>[^;]+);')

PERCENT = re.compile(r'\+\s*"%"|"%"\s*\+|\*\s*100\b')

# The Cantonese label class this gate is named for. 失誤次數 (a COUNT) is deliberately
# not matched: a count has no denominator to name.
RATE_TERM = re.compile(r"失誤率")
WINDOW = 24

TAG = re.compile(r"<[^>]+>")


def _strings(node, path=""):
    if isinstance(node, str):
        if node.strip():
            yield path or "(root)", node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _strings(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _strings(v, f"{path}[{i}]")


def text_surfaces(report_dir, html):
    """(label, identifier, text) for every surface a reader sees the term on."""
    out = []
    for rel in sorted(n for n in os.listdir(report_dir)
                      if n.startswith("claims") and n.endswith(".json")
                      and "proof-map" not in n):
        with open(os.path.join(report_dir, rel), encoding="utf-8") as fh:
            claims = json.load(fh)
        out += [(rel, c["id"], c["canto"]) for c in claims]
    for path in sorted(glob.glob(os.path.join(report_dir, "prose", "*.json"))):
        rel = f"prose/{os.path.basename(path)}"
        with open(path, encoding="utf-8") as fh:
            out += [(rel, label, text) for label, text in _strings(json.load(fh))]
    # The whole document, generated regions included — see the module docstring.
    out.append(("report.html", "rendered text", TAG.sub(" ", html)))
    return out


def chart_problems(html):
    """Every tape-chart row whose label or format misstates what it plots."""
    bad, rows = [], []
    for m in ROW.finditer(html):
        key = m.group("key1") or m.group("key2")
        label, fmt = m.group("label"), m.group("fmt")
        rows.append((key, label))
        kind = KINDS.get(key)
        if kind is None:
            bad.append(f"chart row {label!r} plots {key!r}, which "
                       f"pipeline/check_finesse_denominator.KINDS does not classify — "
                       f"add it as COUNT, SHARE or EVENT_RATE")
            continue
        if kind != EVENT_RATE:
            continue
        if not any(tok in label for tok in DENOMINATOR):
            bad.append(f"chart row {label!r} plots {key!r}, an events-per-piece rate, "
                       f"but the label names no denominator (expected one of "
                       f"{'/'.join(DENOMINATOR)})")
        if PERCENT.search(fmt):
            bad.append(f"chart row {label!r} plots {key!r} as a percentage; a "
                       f"percentage asserts a share, and this rate is not bounded by 1")
    return bad, rows


def text_problems(surfaces):
    bad, seen = [], 0
    for label, ident, text in surfaces:
        flat = TAG.sub(" ", text)
        for m in RATE_TERM.finditer(flat):
            seen += 1
            before = flat[max(0, m.start() - WINDOW):m.start()]
            if not any(tok in before for tok in DENOMINATOR):
                bad.append(f"{label} {ident}: 「{flat[max(0, m.start() - 18):m.end()].strip()}」"
                           f" names no denominator — say 每粒方塊嘅 finesse 失誤率, because "
                           f"faults/piece and the faulty-piece share are different numbers")
    return bad, seen


def problems(report_dir, html):
    chart, rows = chart_problems(html)
    text, seen = text_problems(text_surfaces(report_dir, html))
    return chart + text, rows, seen


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir")
    ap.add_argument("--selftest", action="store_true",
                    help="prove the gate fires: a control plus named planted mutants")
    args = ap.parse_args(argv)

    report = os.path.join(args.report_dir, "report.html")
    if not os.path.exists(report):
        print(f"FAIL {report} does not exist", file=sys.stderr)
        return 1
    with open(report, encoding="utf-8") as fh:
        html = fh.read()

    if args.selftest:
        return _selftest(args.report_dir, html)

    bad, rows, seen = problems(args.report_dir, html)
    for b in bad:
        print(f"FAIL {b}", file=sys.stderr)
    if bad:
        print(f"\n{len(bad)} unnamed denominator(s). faults/pieces is 16.83% and the "
              f"faulty-piece share is 10.65%; a label that names neither picks for the "
              f"reader.", file=sys.stderr)
        return 1
    rated = sum(1 for k, _ in rows if KINDS.get(k) == EVENT_RATE)
    print(f"  ok  {len(rows)} chart row(s), {rated} per-piece rate(s) naming 每粒 and "
          f"rendered as rates; {seen} 失誤率 mention(s) carry a denominator")
    return 0


def _selftest(report_dir, html):
    """The gate must accept the committed report and reject every corruption of it."""
    if ROW.search(html) is None:
        print("FAIL selftest: no tape-chart row to corrupt — the gate reads nothing",
              file=sys.stderr)
        return 1
    if not any(KINDS.get(k) == EVENT_RATE
               for k in (r[0] for r in chart_problems(html)[1])):
        print("FAIL selftest: this report plots no EVENT_RATE row, so rule 1 is "
              "untested here", file=sys.stderr)
        return 1

    cases = [("control: the committed report", report_dir, html, False)]

    # Every events-per-piece row, not just the first: both 每粒攻擊 and the finesse row
    # are EVENT_RATE, and a mutant that only ever corrupts one of them would leave the
    # other's label and format untested.
    evs = [mm for mm in ROW.finditer(html)
           if KINDS.get(mm.group("key1") or mm.group("key2")) == EVENT_RATE]
    for ev in evs:
        row, label, fmt = ev.group(0), ev.group("label"), ev.group("fmt")
        key = ev.group("key1") or ev.group("key2")

        def swap(new_row, ev=ev):
            return html[:ev.start()] + new_row + html[ev.end():]

        # M1 — the label stops naming the denominator. This is the shipped defect.
        stripped = label
        for tok in DENOMINATOR:
            stripped = stripped.replace(tok, "")
        cases.append((f"M1 {key}: label loses its denominator "
                      f"({label!r} -> {stripped!r})",
                      report_dir, swap(row.replace(f'"{label}"', f'"{stripped}"', 1)), True))

        # M2 — the value goes back to a percentage. A label alone does not fix this:
        # 16.8% reads as a share however the row is titled.
        cases.append((f"M2 {key}: rendered as a percentage", report_dir,
                      swap(row.replace(fmt, '(v * 100).toFixed(1) + "%"', 1)), True))

        # M3 — completeness: a row plotting a key nobody classified must fail, not pass.
        cases.append((f"M3 {key}: the row plots an unclassified key", report_dir,
                      swap(row.replace(key, "some_new_rate")), True))

    # M4 — the prose half. Planted rather than taken from the session, so the mutant
    # runs on every session and not only the two whose prose happens to use the term.
    # Appended to the end of the document: these reports carry no </body>, and an
    # anchor that is simply absent would have silently skipped both cases — which is
    # how it first ran, leaving the text rule with no mutant at all.
    cases.append(("M4 prose prints 失誤率 with no denominator", report_dir,
                  html + "\n<p>finesse 失誤率高過對手</p>\n", True))
    # M5 — the negative control. The same sentence WITH the denominator must be
    # accepted, so the gate is not merely banning the word.
    cases.append(("M5 (negative control) the same sentence names 每粒方塊", report_dir,
                  html + "\n<p>每粒方塊嘅 finesse 失誤率高過對手</p>\n", False))
    # M6 — the other negative control: a SHARE row keeps its percentage. Without this
    # the gate could be passing by banning percentages outright.
    share = next((mm for mm in ROW.finditer(html)
                  if KINDS.get(mm.group("key1") or mm.group("key2")) == SHARE), None)
    if share is not None and PERCENT.search(share.group("fmt")):
        cases.append((f"M6 (negative control) SHARE row {share.group('label')!r} keeps "
                      f"its percentage", report_dir, html, False))

    ok = True
    for name, rd, doc, must_fail in cases:
        failed = bool(problems(rd, doc)[0])
        good = failed == must_fail
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: "
              f"{'rejected' if failed else 'accepted'}"
              f"{'' if good else '  <- expected ' + ('rejection' if must_fail else 'acceptance')}")
    print(f"{'ok ' if ok else 'FAIL'} selftest "
          f"{sum(1 for c in cases if c[3])} corruptions, "
          f"{'all caught' if ok else 'SOME MISSED'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

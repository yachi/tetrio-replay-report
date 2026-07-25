"""Generate the derived parts of a session's report.html.

    python3 -m pipeline.build_report sessions/2026-07-24/report
    python3 -m pipeline.build_report sessions/2026-07-24/report --check

The report is part generated, part hand-written Cantonese prose. This writes only
the generated parts, each inside its own marker region (see `pipeline/region.py`),
so it is idempotent and safe to re-run over a report someone has edited around.

Sections handled so far:

  chart-data   the JSON island every chart reads — per-match scoreboard, the VS
               small multiples, clear-type bars, the tape chart, match boundaries.

`--check` regenerates in memory and exits non-zero if the committed report differs,
which is what CI runs: the charts and facts.json cannot drift apart unnoticed.
"""
import argparse
import json
import os
import sys

from pipeline import chart_data, region

CHART_START, CHART_END = region.markers("chart-data", "pipeline/build_report.py")
# The island must precede the claims island, which is where the page's inline
# script starts reading data from.
CHART_ANCHOR = "<!-- CLAIMS_DATA_START -->"


def chart_section(facts):
    blob = json.dumps(chart_data.build(facts), ensure_ascii=False,
                      separators=(",", ":"))
    return ('<script type="application/json" id="chart-data">\n'
            f"{blob}\n"
            "</script>")


SECTIONS = [("chart-data", CHART_START, CHART_END, CHART_ANCHOR, chart_section)]


def render(html, facts):
    """Apply every generated section to `html`. Returns (html, [(name, how)])."""
    applied = []
    for name, start, end, anchor, build in SECTIONS:
        html, how = region.replace(html, start, end, build(facts), anchor)
        applied.append((name, how))
    return html, applied


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir", help="a session's report/ directory")
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 1 if the committed report differs")
    args = ap.parse_args(argv)

    with open(os.path.join(args.report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    report_path = os.path.join(args.report_dir, "report.html")
    with open(report_path, encoding="utf-8") as fh:
        before = fh.read()

    after, applied = render(before, facts)

    if args.check:
        if after != before:
            print(f"DRIFT: {report_path} differs from what facts.json generates "
                  f"({', '.join(n for n, _ in applied)}) — run "
                  f"`python3 -m pipeline.build_report {args.report_dir}`", file=sys.stderr)
            return 1
        print(f"ok  {report_path} — generated sections match facts.json "
              f"({', '.join(n for n, _ in applied)})")
        return 0

    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(after)
    for name, how in applied:
        print(f"{how}: {name} -> {report_path}")
    # Re-running must be a no-op; proving it here costs nothing and is the whole
    # reason the sections are marker-scoped.
    again, _ = render(after, facts)
    if again != after:
        print("BUG: build_report is not idempotent", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

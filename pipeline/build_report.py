"""Generate the derived parts of a session's report.html.

    python3 -m pipeline.build_report sessions/2026-07-24/report
    python3 -m pipeline.build_report sessions/2026-07-24/report --check

The report is part generated, part hand-written Cantonese prose. This writes only
the generated parts, each inside its own marker region (see `pipeline/region.py`),
so it is idempotent and safe to re-run over a report someone has edited around.

Sections handled so far:

  hero         the eyebrow, headline, scoreboard and lede. Numbers (date, names,
               series score) come from facts.json; the Cantonese comes from
               `<report_dir>/prose/hero.json`.
  chart-data   the JSON island every chart reads — per-match scoreboard, the VS
               small multiples, clear-type bars, the tape chart, match boundaries.

`--check` regenerates in memory and exits non-zero if the committed report differs,
which is what CI runs: the report and facts.json cannot drift apart unnoticed.
"""
import argparse
import json
import os
import sys

from pipeline import appendix, chart_data, forecast_section, hero, matches, records, region


def chart_section(ctx):
    blob = json.dumps(chart_data.build(ctx["facts"]), ensure_ascii=False,
                      separators=(",", ":"))
    return ('<script type="application/json" id="chart-data">\n'
            f"{blob}\n"
            "</script>")


def hero_section(ctx):
    return hero.build(ctx["facts"], hero.load_prose(ctx["report_dir"]),
                      ctx["report_dir"])


def match_copy_section(ctx):
    return matches.build(ctx["facts"],
                         matches.load_prose(ctx["report_dir"], ctx["facts"]))


def records_section(ctx):
    return records.build(ctx["facts"], ctx["report_dir"])


def appendix_section(ctx):
    return appendix.section(ctx["facts"], ctx["report_dir"])


def forecast_sec(ctx):
    # Sourced from the SESSION's sim/forecast-facts.json, not facts.json — see the module
    # docstring. Quarantined from the claims pipeline on purpose: one simulator, no second
    # independent implementation, so the dual-extractor trust argument does not cover it.
    # Returns None for a session with no such file, and render() then skips the region
    # entirely rather than writing an empty one.
    return forecast_section.section(forecast_section.load(ctx["report_dir"]))


def claims_island(ctx):
    return appendix.island(ctx["report_dir"])


# (name, anchor to insert before when the region is absent, builder, markers)
# `markers` is None unless a region predates this module and owns a different
# comment pair — the claims island does, and anything that finds it by name
# (check_prose_figures skips it) keeps working because it kept them.
#
# Order is document order for a report being built from nothing: hero, records
# before the coaching section, appendix before the footer, then the islands.
SECTIONS = [
    ("hero", '<section id="matches">', hero_section, None),
    ("records", '<section id="coaching">', records_section, None),
    ("appendix", '<footer class="report-footer">', appendix_section, None),
    # after the proof appendix, so a reader meets the trust chain before the thing
    # that is explicitly outside it
    ("forecast", '<footer class="report-footer">', forecast_sec, None),
    ("chart-data", "<!-- CLAIMS_DATA_START -->", chart_section, None),
    ("match-copy", "<!-- CLAIMS_DATA_START -->", match_copy_section, None),
    ("claims-data", '<footer class="report-footer">', claims_island,
     (appendix.ISLAND_START, appendix.ISLAND_END)),
]


def render(html, ctx):
    """Apply every generated section to `html`. Returns (html, [(name, how)])."""
    applied = []
    for name, anchor, build, markers in SECTIONS:
        body = build(ctx)
        if body is None:           # section does not apply to this session
            continue
        start, end = markers or region.markers(name, "pipeline/build_report.py")
        html, how = region.replace(html, start, end, body, anchor)
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
    ctx = {"facts": facts, "report_dir": args.report_dir}
    report_path = os.path.join(args.report_dir, "report.html")
    with open(report_path, encoding="utf-8") as fh:
        before = fh.read()

    after, applied = render(before, ctx)

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
    again, _ = render(after, ctx)
    if again != after:
        print("BUG: build_report is not idempotent", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

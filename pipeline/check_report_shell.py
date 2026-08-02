"""No hand-written `<section>` may survive in a report body.

    python3 -m pipeline.check_report_shell sessions/2026-08-01/report

Every section of the report is generated from a prose file into a marker region
(`pipeline/region.py`). What is left in `report.html` is the *shell*: the `<head>`,
the stylesheet, the inline script, the footer, and the marker pairs themselves.

This gate exists because the claim "the report body is fully generated" was written
into CLAUDE.md while it was true of every section except one. It was checked by
reading `build_report.SECTIONS` and counting entries, which is a check of the
generator's intentions rather than of the document — and `<section id="matches">`
sat there hand-written the whole time, invisible to that method.

So the check runs the other way round: scan the DOCUMENT for sections, and require
each one to fall inside a generated region. A future session that pastes prose back
into `report.html` fails here rather than quietly reintroducing the thing P5 removed.

The round table carries its own marker pair with different wording (it predates
`region.py`), so both spellings are recognised.
"""
import argparse
import os
import re
import sys

# Both marker dialects: the one `region.py` writes, and build_round_table's older pair.
REGIONS = re.compile(
    r"<!-- BEGIN generated .*?<!-- END generated [a-z-]+ -->"
    r"|<!-- CLAIMS_DATA_START -->.*?<!-- CLAIMS_DATA_END -->", re.S)
# The id is pulled out of the matched tag rather than made an optional group in the
# same pattern: an optional group next to `[^>]*` prefers to match empty, so every
# section reported as "(no id)" even when it had one — a diagnostic that misleads
# whoever has to fix the failure.
SECTION = re.compile(r"<section\b[^>]*>")
TAG_ID = re.compile(r'\bid="([^"]*)"')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir")
    args = ap.parse_args(argv)

    path = os.path.join(args.report_dir, "report.html")
    with open(path, encoding="utf-8") as fh:
        html = fh.read()

    spans = [m.span() for m in REGIONS.finditer(html)]
    inside = lambda i: any(a <= i < b for a, b in spans)  # noqa: E731

    stray = []
    for m in SECTION.finditer(html):
        if inside(m.start()):
            continue
        found = TAG_ID.search(m.group(0))
        stray.append((found.group(1) if found else "(no id)",
                      html.count("\n", 0, m.start()) + 1))

    if stray:
        print(f"FAIL {path}: {len(stray)} <section> outside any generated region — "
              f"the report body must be generated from prose files, not typed into "
              f"the HTML:", file=sys.stderr)
        for sid, line in stray:
            print(f"  line {line}: <section id=\"{sid}\">", file=sys.stderr)
        print("  Move it into a prose file and add a pipeline/build_report.py SECTIONS "
              "entry, the way 關鍵時刻 / 數據對決 / 建議 / 戰況 were.", file=sys.stderr)
        return 1

    print(f"  ok  {len(spans)} generated regions; every <section> in the body is "
          f"inside one")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

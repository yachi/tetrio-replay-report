"""Gate: the forecast section's rendered numbers must match sim/forecast-facts.json.

    python3 -m pipeline.check_forecast_section sessions/2026-07-22/report

The rest of the report is protected by Dafny lemmas over facts.json. This section is not —
it is simulator-derived and deliberately outside that chain — so it needs its own guard, or
its numbers could drift from their source with nothing to catch it.

Two things are checked:
  1. every per-player figure in the rendered HTML is exactly what the JSON says;
  2. the section still declares itself unproved. A future edit that quietly drops the
     "未經證明" heading or mints a claim badge here would be promoting simulator output into
     the trust chain, which is precisely what this section exists to avoid.
"""
import json
import os
import re
import sys

from pipeline import forecast_section, region

BADGE = re.compile(r"data-claim|claim-badge|已驗證")


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("usage: check_forecast_section <report dir>", file=sys.stderr)
        return 2
    report_dir = argv[0]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data = forecast_section.load(root)
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()

    start, end = region.markers("forecast", "pipeline/build_report.py")
    i, j = doc.find(start), doc.find(end)
    if i < 0 or j < 0:
        print("FAIL forecast region missing from report.html", file=sys.stderr)
        return 1
    body = doc[i:j]

    bad = []
    for p in data["players"]:
        want = [f"{p['forecast_total']} / {p['verified_tspins']}",
                f"{p['forecast_rate_x1000'] / 10:.1f}%",
                f"[{p['sampling_ci95_lo_x1000'] / 10:.1f}%, {p['sampling_ci95_hi_x1000'] / 10:.1f}%]",
                f"[{p['simulator_range_lo_x1000'] / 10:.1f}%, {p['simulator_range_hi_x1000'] / 10:.1f}%]"]
        for w in want:
            if w not in body:
                bad.append(f"{p['user']}: rendered HTML is missing {w!r}")

    if data.get("report_eligible") is not False:
        bad.append("forecast-facts.json no longer declares report_eligible:false")
    if "未經證明" not in body:
        bad.append("the section no longer declares itself unproved (未經證明)")
    if BADGE.search(body):
        bad.append("the section carries a claim badge — simulator output must not be badged")

    for b in bad:
        print(f"FAIL {b}", file=sys.stderr)
    if bad:
        return 1
    print(f"ok  forecast section matches {forecast_section.FACTS} "
          f"({len(data['players'])} players) and stays outside the claims chain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

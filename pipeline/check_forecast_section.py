"""Gate: the forecast section's rendered numbers must match sim/forecast-facts.json.

    python3 -m pipeline.check_forecast_section sessions/2026-07-22/report

The rest of the report is protected by Dafny lemmas over facts.json. This section is not —
it is simulator-derived and deliberately outside that chain — so it needs its own guard, or
its numbers could drift from their source with nothing to catch it.

Three things are checked:
  1. the committed region is EXACTLY what rendering this session's JSON produces;
  2. every per-player figure in the rendered HTML is what the JSON says;
  3. the section still declares itself unproved. A future edit that quietly drops the
     "未經證明" heading or mints a claim badge here would be promoting simulator output into
     the trust chain, which is precisely what this section exists to avoid.

Check 1 is the one that matters, and it replaced a gate that could not have caught the bug it
was written for. Checking that each JSON figure APPEARS in the HTML is a containment test: it
passes just as happily when the section also contains a figure that came from nowhere. Every
statistic in the method note — the AUC and its p, the event-level difference and its CI, the
player p, the split-half reliabilities, the coverage — was a hardcoded literal describing
2026-07-22, in a module rendered for EVERY session, and this gate reported ok on all four.

Re-rendering and comparing is complete rather than sampled: any figure the renderer would not
produce from this session's data is a difference, whether it is stale, extra, or invented. It
is the same argument `verify-session` already makes twice — the extractor must reproduce its
committed facts, and codegen must reproduce its committed .dfy.
"""
import difflib
import json
import os
import re
import sys

from pipeline import forecast_section, region

BADGE = re.compile(r"data-claim|claim-badge|已驗證")


def problems(data, doc):
    """Every reason `doc`'s forecast region disagrees with `data`; empty means it agrees.

    Split out of `main` so the self-test can feed it a deliberately corrupted document in
    memory. A gate that can only be exercised against the one committed file it already passes
    on has never been shown to fail, and this one demonstrably could not catch the bug it
    existed for.
    """
    start, end = region.markers("forecast", "pipeline/build_report.py")
    i, j = doc.find(start), doc.find(end)

    if data is None:
        # A session with no simulator output must have no forecast section. Asserted rather
        # than skipped: a stray region here would be one session's numbers in another's report.
        if i >= 0 or j >= 0:
            return [f"has a forecast region but no {forecast_section.FACTS_REL}"]
        return []

    if i < 0 or j < 0:
        return ["forecast region missing from report.html"]
    body = doc[i:j]

    bad = []

    # 1. the committed region must be exactly what this session's data renders to. Everything
    #    below is a containment test and cannot see a figure that came from nowhere; this can.
    committed = doc[i + len(start):j]
    expected = "\n" + forecast_section.section(data) + "\n"
    if committed != expected:
        diff = list(difflib.unified_diff(
            expected.splitlines(), committed.splitlines(),
            fromfile="rendered from forecast-facts.json", tofile="committed report.html",
            lineterm="", n=1))
        bad.append("the committed forecast region is not what this session's data renders to:\n"
                   + "\n".join("      " + d for d in diff[:40]))
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

    return bad


def _selftest(report_dir):
    """Controls: the gate must PASS the committed pair and FAIL every corruption of it.

    The planted-figure cases are the acceptance criterion for this gate's rewrite. Before it,
    the method note's statistics were literals describing 2026-07-22 while the module rendered
    for every session — so pasting one session's AUC into another's report was exactly the
    undetected failure, and it must now be caught.
    """
    data = forecast_section.load(report_dir)
    if data is None:
        print(f"FAIL selftest needs a session WITH forecast data; {report_dir} has none",
              file=sys.stderr)
        return 1
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()

    cases = []           # (name, data, doc, must_fail)
    cases.append(("control: the committed pair agrees", data, doc, False))

    # Plant a FOREIGN figure — the same shape the renderer emits, a different value. Each of
    # these is a real number from this corpus, so none of them looks out of place by eye.
    for name, old, new in [
        ("planted AUC (58.5% -> 58.6%)", "58.5%", "58.6%"),
        ("planted round p (0.211 -> 0.210)", "0.211", "0.210"),
        ("planted player p (0.849 -> 0.848)", "0.849", "0.848"),
        ("planted reliability (0.291 -> 0.29)", "0.291（", "0.29（"),
        ("planted coverage (17.8% -> 17.9%)", "17.8%", "17.9%"),
    ]:
        if old in doc:
            cases.append((name, data, doc.replace(old, new, 1), True))

    # A figure changed in the JSON without rebuilding the report is the same drift seen from
    # the other side, and the containment-only gate could not see this one either.
    stale = json.loads(json.dumps(data))
    if (stale.get("statistics") or {}).get("round"):
        stale["statistics"]["round"]["auc_x1000"] = 700
        cases.append(("data moved but the report was not rebuilt", stale, doc, True))

    # And the invariants the section exists to hold. The badge must be planted INSIDE the
    # forecast region: the document's first `section-title` belongs to an earlier, legitimately
    # badged section, and a control that corrupts the wrong part of the file proves nothing.
    anchor = "T-Spin Forecast（未經證明）"
    if anchor in doc:
        cases.append(("a claim badge appears on simulator output", data,
                      doc.replace(anchor, anchor + '<span class="claim-badge">✓</span>', 1), True))
        cases.append(("the section stops declaring itself unproved", data,
                      doc.replace(anchor, "T-Spin Forecast", 1), True))
    eligible = json.loads(json.dumps(data))
    eligible["report_eligible"] = True
    cases.append(("the artifact declares itself report-eligible", eligible, doc, True))

    ok = True
    for name, d, dc, must_fail in cases:
        failed = bool(problems(d, dc))
        good = failed == must_fail
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: "
              f"{'rejected' if failed else 'accepted'}"
              f"{'' if good else '  <- expected ' + ('rejection' if must_fail else 'acceptance')}")
    print(f"{'ok ' if ok else 'FAIL'} selftest {sum(1 for c in cases if c[3])} corruptions, "
          f"{'all caught' if ok else 'SOME MISSED'}")
    return 0 if ok else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("usage: check_forecast_section <report dir> [--selftest]", file=sys.stderr)
        return 2
    report_dir = argv[0]
    if "--selftest" in argv:
        return _selftest(report_dir)

    data = forecast_section.load(report_dir)
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()

    bad = problems(data, doc)
    for b in bad:
        print(f"FAIL {report_dir}: {b}", file=sys.stderr)
    if bad:
        return 1
    if data is None:
        print(f"ok  {report_dir} has no forecast data and no forecast section")
        return 0
    print(f"ok  forecast section matches {forecast_section.FACTS_REL} "
          f"({len(data['players'])} players) and stays outside the claims chain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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

    start, end = region.markers("forecast", "pipeline/build_report.py")
    i, j = doc.find(start), doc.find(end)
    if i < 0 or j < 0:
        print("FAIL selftest: no forecast region to corrupt", file=sys.stderr)
        return 1
    head, body, tail = doc[:i + len(start)], doc[i + len(start):j], doc[j:]

    cases = []           # (name, data, doc, must_fail)
    cases.append(("control: the committed pair agrees", data, doc, False))

    # Plant a foreign value over EVERY figure the section renders, one at a time. Derived from
    # the region rather than written as constants for two reasons: it is session-agnostic, and
    # it makes the control a completeness statement — every number in the section is shown to
    # be load-bearing, rather than the handful someone remembered to list.
    #
    # The corruption must be applied INSIDE the region. Replacing across the whole document
    # hits an earlier, legitimate occurrence first, and the gate then rightly ignores it — that
    # false alarm fired twice while writing this.
    seen = set()
    for m in re.finditer(r"\d+\.\d+", body):
        tok = m.group(0)
        if tok in seen:
            continue
        seen.add(tok)
        # bump the last digit, so the planted value stays the same shape and the same width
        alt = tok[:-1] + str((int(tok[-1]) + 1) % 10)
        cases.append((f"planted figure {tok} -> {alt}", data,
                      head + body[:m.start()] + alt + body[m.end():] + tail, True))

    # A figure changed in the JSON without rebuilding the report is the same drift seen from
    # the other side, and the containment-only gate could not see this one either.
    #
    # WHICH field is moved has to be decided by re-rendering, not written down. This was
    # hardcoded to statistics.round.auc_x1000 and stopped meaning anything on 2026-08-06, when
    # the round AUC became undecidable (a forecast rate of 0 for every player ties every pair)
    # and dropped out of the prose. The mutation was still planted, the render was unchanged,
    # and the case failed as "accepted" — the selftest correctly reporting a hole in itself
    # rather than passing on a corruption that no longer corrupted anything.
    rendered = forecast_section.section(data)
    moved = None
    for path in (("statistics", "round", "auc_x1000"),
                 ("players", 0, "verified_tspins"),
                 ("players", 0, "reactive"),
                 ("players", 0, "self_built"),
                 ("players", 0, "forecast_rate_x1000")):
        stale = json.loads(json.dumps(data))
        node = stale
        try:
            for k in path[:-1]:
                node = node[k]
            if not isinstance(node[path[-1]], int):
                continue
            node[path[-1]] += 7
        except (KeyError, IndexError, TypeError):
            continue
        if forecast_section.section(stale) != rendered:
            moved = (".".join(str(k) for k in path), stale)
            break
    if moved is None:
        # Not a skip: if no field of the JSON changes what the section renders, this gate is
        # comparing the report against nothing and the whole file is decorative.
        print("FAIL selftest: no JSON field moves the render — the gate cannot see its data",
              file=sys.stderr)
        return 1
    cases.append((f"data moved but the report was not rebuilt ({moved[0]})", moved[1], doc, True))

    # And the invariants the section exists to hold. The badge must be planted INSIDE the
    # forecast region: the document's first `section-title` belongs to an earlier, legitimately
    # badged section, and a control that corrupts the wrong part of the file proves nothing.
    anchor = "T-Spin Forecast（未經證明）"
    if anchor in body:
        cases.append(("a claim badge appears on simulator output", data,
                      head + body.replace(anchor, anchor + '<span class="claim-badge">✓</span>', 1) + tail, True))
        cases.append(("the section stops declaring itself unproved", data,
                      head + body.replace(anchor, "T-Spin Forecast", 1) + tail, True))
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

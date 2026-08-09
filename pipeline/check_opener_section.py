"""Gate: the opener section's rendered numbers must match sim/opener-facts.json.

    python3 -m pipeline.check_opener_section sessions/2026-08-09/report
    python3 -m pipeline.check_opener_section sessions/2026-08-09/report --selftest

The sibling of `check_forecast_section.py`, and it exists for the same reason: the rest of the
report is protected by Dafny lemmas over facts.json, this section is deliberately outside that
chain, so without its own guard its numbers could drift from their source with nothing to catch
it. The argument for re-rendering rather than sampling is spelled out there and is not repeated.

Four things are checked:
  1. the committed region is EXACTLY what rendering this session's JSON produces;
  2. every per-player ordering figure appears in the rendered HTML;
  3. the section still declares itself unproved and carries no claim badge — promoting simulator
     output into the trust chain is precisely what this section exists to avoid;
  4. the section never states a C-Spin COUNT. This one is specific to this section and is the
     reason it needs its own gate rather than a copy of the forecast one. The slot-geometry
     share is ~9-in-10 for Triples and ~1-in-10 for Doubles, which makes it a Triple-shape
     detector; the control paragraph saying so is load-bearing, and a future edit that keeps the
     share while dropping the control would publish "89% of these were C-Spins" — a claim the
     data cannot support and the exact misreading the cross-tab was built to prevent.
"""
import difflib
import json
import os
import re
import sys

from pipeline import opener_section, region

BADGE = re.compile(r"data-claim|claim-badge|已驗證")

# The control the slot-geometry table may not be published without: the Doubles share, which is
# what makes the Triples share readable as a shape test. Matched on the sentence's own words
# rather than on a number, so it survives the numbers changing between sessions.
CONTROL_MARKERS = ("但消兩行嘅只有", "唔可以當成")


def problems(data, doc):
    """Every reason `doc`'s opener region disagrees with `data`; empty means it agrees."""
    start, end = region.markers("openers", "pipeline/build_report.py")
    i, j = doc.find(start), doc.find(end)

    if data is None:
        # A session with no simulator output must have no opener section. Asserted rather than
        # skipped: a stray region here would be one session's numbers in another's report, which
        # is the bug the forecast section actually shipped before it became session-scoped.
        if i >= 0 or j >= 0:
            return [f"has an opener region but no {opener_section.FACTS_REL}"]
        return []

    if i < 0 or j < 0:
        return ["opener region missing from report.html"]
    body = doc[i:j]
    bad = []

    # 1. exact re-render. Everything below is a containment test and cannot see a figure that
    #    came from nowhere; this can.
    committed = doc[i + len(start):j]
    # `section` returns None only for data None, which returned above; asserting it keeps the
    # type readable rather than leaving a `str | None` to be concatenated.
    rendered = opener_section.section(data)
    assert rendered is not None
    expected = "\n" + rendered + "\n"
    if committed != expected:
        diff = list(difflib.unified_diff(
            expected.splitlines(), committed.splitlines(),
            fromfile="rendered from opener-facts.json", tofile="committed report.html",
            lineterm="", n=1))
        bad.append("the committed opener region is not what this session's data renders to:\n"
                   + "\n".join("      " + d for d in diff[:40]))

    # 2. the ordering figures, which are the section's spine
    for p in data["ordering"]["players"]:
        for w in (str(p["rounds_scored"]), str(p["rounds_with_both"]),
                  str(p["cspin_order"]), str(p["dt_order"])):
            if w not in body:
                bad.append(f"{p['user']}: rendered HTML is missing ordering figure {w!r}")

    # 3. the quarantine invariants
    if data.get("report_eligible") is not False:
        bad.append("opener-facts.json no longer declares report_eligible:false")
    if "未經證明" not in body:
        bad.append("the section no longer declares itself unproved (未經證明)")
    if BADGE.search(body):
        bad.append("the section carries a claim badge — simulator output must not be badged")

    # 4. the slot-geometry control must accompany the slot-geometry share
    if data["slot_geometry"]["rows"] and any(r["n"] for r in data["slot_geometry"]["rows"]):
        for marker in CONTROL_MARKERS:
            if marker not in body:
                bad.append(f"the slot-geometry control is gone ({marker!r} missing) — the share "
                           "may not be published without the Doubles comparison beside it")

    return bad


def _selftest(report_dir):
    """Controls: the gate must PASS the committed pair and FAIL every corruption of it."""
    data = opener_section.load(report_dir)
    if data is None:
        print(f"FAIL selftest needs a session WITH opener data; {report_dir} has none",
              file=sys.stderr)
        return 1
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()

    start, end = region.markers("openers", "pipeline/build_report.py")
    i, j = doc.find(start), doc.find(end)
    if i < 0 or j < 0:
        print("FAIL selftest: no opener region to corrupt", file=sys.stderr)
        return 1
    head, body, tail = doc[:i + len(start)], doc[i + len(start):j], doc[j:]

    cases = [("control: the committed pair agrees", data, doc, False)]

    # Plant a foreign value over every distinct number the section renders, one at a time.
    # Derived from the region rather than listed as constants, so the control is a completeness
    # statement about the section's figures instead of the handful someone remembered.
    # The corruption is applied INSIDE the region: replacing across the whole document hits an
    # earlier legitimate occurrence first, which the gate then rightly ignores.
    seen = set()
    for m in re.finditer(r"\d+(?:\.\d+)?", body):
        tok = m.group(0)
        if tok in seen:
            continue
        seen.add(tok)
        alt = tok[:-1] + str((int(tok[-1]) + 1) % 10)      # same shape, same width
        cases.append((f"planted figure {tok} -> {alt}", data,
                      head + body[:m.start()] + alt + body[m.end():] + tail, True))

    # A figure changed in the JSON without rebuilding the report is the same drift from the
    # other side. WHICH field moves the render is decided by re-rendering rather than written
    # down, so this case cannot quietly stop corrupting anything the way the forecast gate's
    # hardcoded field did when the round AUC dropped out of its prose.
    rendered = opener_section.section(data)
    moved = None
    for path in (("ordering", "players", 0, "cspin_order"),
                 ("ordering", "players", 0, "rounds_with_both"),
                 ("first_bag", "clean"),
                 ("slot_geometry", "rows", 0, "n"),
                 ("catalogue", "pages")):
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
        if opener_section.section(stale) != rendered:
            moved = (".".join(str(k) for k in path), stale)
            break
    if moved is None:
        # Not a skip: if no field of the JSON changes what the section renders, this gate is
        # comparing the report against nothing and the whole file is decorative.
        print("FAIL selftest: no JSON field moves the render — the gate cannot see its data",
              file=sys.stderr)
        return 1
    cases.append((f"data moved but the report was not rebuilt ({moved[0]})", moved[1], doc, True))

    anchor = "C-Spin 同 DT 砲（未經證明）"
    if anchor in body:
        cases.append(("a claim badge appears on simulator output", data,
                      head + body.replace(anchor, anchor + '<span class="claim-badge">✓</span>', 1)
                      + tail, True))
        cases.append(("the section stops declaring itself unproved", data,
                      head + body.replace(anchor, "C-Spin 同 DT 砲", 1) + tail, True))

    # The control paragraph is the reason the slot-geometry share may be printed at all, so
    # deleting it while keeping the table must be a failure and not a cosmetic edit.
    for marker in CONTROL_MARKERS:
        if marker in body:
            cases.append((f"the slot-geometry control sentence is deleted ({marker})", data,
                          head + body.replace(marker, "", 1) + tail, True))

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
        print("usage: check_opener_section <report dir> [--selftest]", file=sys.stderr)
        return 2
    report_dir = argv[0]
    if "--selftest" in argv:
        return _selftest(report_dir)

    data = opener_section.load(report_dir)
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()

    bad = problems(data, doc)
    for b in bad:
        print(f"FAIL {report_dir}: {b}", file=sys.stderr)
    if bad:
        return 1
    if data is None:
        print(f"ok  {report_dir} has no opener data and no opener section")
        return 0
    print(f"ok  opener section matches {opener_section.FACTS_REL} "
          f"({len(data['ordering']['players'])} players) and stays outside the claims chain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

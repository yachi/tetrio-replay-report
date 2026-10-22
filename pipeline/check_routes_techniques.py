"""Gate: 定式路線同中盤手法 stays a quarantined re-render, and 建議's tagged items stay traceable to it.

    python3 -m pipeline.check_routes_techniques sessions/2026-10-09/report
    python3 -m pipeline.check_routes_techniques sessions/2026-10-09/report --selftest

`build_report --check` already re-renders both regions, so a HAND edit is caught there. What it
cannot catch is a CODE edit or a PROSE edit that says more than the tier allows: the generator and
the committed report then agree with each other and both overreach. Checked:

  1. no section data -> no region; section data -> exactly the region rendering it produces;
  2. the region carries its eyebrow, its 「（未經證明）」 title and every sentence in
     `routes_techniques_section.REQUIRED` (the quarantine, 「冇對到唔代表冇打過」, the stick spin /
     SDPC Spin overlap, the no-win-rate rule);
  3. no claim badge, `data-claim` or ✓ inside the region;
  4. 建議's tagged items: every `sim_recs` entry renders as exactly one `<li class="cs-sim">`
     carrying `coaching.SIM_TAG` (and the tag appears nowhere else), none carries a badge, the
     section carries `coaching.SIM_NOTE`, a session with tagged items has the region, and **every
     Arabic figure in a tagged item is a figure the region prints**.

What 4 does NOT establish, said plainly: that a figure is the RIGHT one of the region's figures. It
is a membership test over the region's printed numbers, so 「打咗 20 次」 passes when 20 is printed
anywhere in the region. It stops a number nobody measured; matching each sentence to its cell is
still the author's job, and the region links every cell to the replay moment it counts.

`--selftest` plants one corruption per check and fails unless every one is rejected.
"""
import json
import os
import re
import sys

from pipeline import coaching, region
from pipeline import routes_techniques_section as RT

_LI = re.compile(r'<li class="cs-sim">(.*?)</li>', re.S)


def _coaching_body(doc):
    start, end = region.markers("coaching", "pipeline/build_report.py")
    if start not in doc:
        return None
    i = doc.index(start) + len(start)
    return doc[i:doc.index(end, i)]


def problems(doc, expected, sims):
    """`expected` is the region the section renders (None: no section); `sims` is the authored
    sim_recs, flattened in column order."""
    out = []
    body = RT.region_body(doc)
    if expected is None:
        if body is not None:
            out.append("report has a routes-techniques region but the session generates none")
    elif body is None:
        out.append("the session has route / technique data but the report has no routes-techniques region")
    else:
        for m in (RT.EYEBROW, RT.TITLE) + RT.REQUIRED:
            if m not in body:
                out.append(f"control sentence missing: {m}")
        if "data-claim" in body or "badge" in body or "✓</" in body:
            out.append("a claim badge appears on simulator output")
        if body.strip() != expected.strip():
            out.append("the region is not what rendering the route / technique artefacts produces")

    cb = _coaching_body(doc) or ""
    lis = _LI.findall(cb)
    if len(lis) != len(sims):
        out.append(f"{len(sims)} tagged 建議 items authored, {len(lis)} rendered")
    if cb.count(coaching.SIM_TAG) != len(sims):
        out.append("the 未經證明 tag appears on something other than exactly the tagged items")
    if sims and coaching.SIM_NOTE not in cb:
        out.append("tagged 建議 items without the note saying what the tag means")
    if sims and body is None:
        out.append("tagged 建議 items cite a routes-techniques section the report does not have")
    pool = RT.figures(body or "")
    for i, li in enumerate(lis, 1):
        if not li.split("</span>", 1)[-1].startswith(coaching.SIM_TAG):
            out.append(f"tagged item {i} does not open with its 未經證明 tag")
        if "data-claim" in li or "badge" in li or "✓" in li:
            out.append(f"tagged item {i} carries a claim badge")
        text = li.split(coaching.SIM_TAG, 1)[-1]
        stray = sorted(RT.numbers(text) - pool, key=int)
        if stray:
            out.append(f"tagged item {i} prints {stray}, which routes-techniques does not")
    return out


def _load(report_dir):
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()
    with open(os.path.join(report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    expected = RT.build(facts, report_dir)
    prose = coaching.load_prose(report_dir, facts)
    sims = [t for p in facts["players"] for t in prose["columns"][p].get("sim_recs", [])]
    return doc, expected, sims


def _selftest(report_dir):
    doc, expected, sims = _load(report_dir)
    body = RT.region_body(doc)
    if expected is None or body is None or not sims:
        print(f"FAIL selftest needs a session with the section and tagged items; {report_dir} has "
              "neither", file=sys.stderr)
        return 1
    head, tail = doc.split(body, 1)
    cases = [("the committed report as it stands", doc, expected, sims, False)]
    for m in (RT.EYEBROW, RT.TITLE) + RT.REQUIRED:
        cases.append((f"a control sentence is deleted ({m[:24]}…)",
                      head + body.replace(m, "", 1) + tail, expected, sims, True))
    cases.append(("a claim badge appears in the region",
                  head + body.replace(RT.TITLE, RT.TITLE + '<span class="badge" data-claim="C001"></span>', 1)
                  + tail, expected, sims, True))
    cases.append(("a table cell edited by hand", head + body.replace("<b>", "<b>9", 1) + tail,
                  expected, sims, True))
    s, e = region.markers(RT.NAME, "pipeline/build_report.py")
    cases.append(("the region removed while the session has data",
                  doc.replace(s + body + e, ""), expected, sims, True))
    cases.append(("a region with no data behind it", doc, None, sims, True))
    first = _LI.search(doc)
    li = first.group(0)
    cases.append(("a tagged item loses its tag", doc.replace(li, li.replace(coaching.SIM_TAG, "", 1), 1),
                  expected, sims, True))
    cases.append(("a tagged item gains a badge",
                  doc.replace(li, li.replace("</li>", '<span class="badge" data-claim="C001"></span></li>'), 1),
                  expected, sims, True))
    cases.append(("a tagged item prints a figure the section does not",
                  doc.replace(li, li.replace("</li>", "（98765 次）</li>"), 1), expected, sims, True))
    cases.append(("a tagged item dropped from the page", doc.replace(li, "", 1), expected, sims, True))
    cases.append(("the tag's note deleted", doc.replace(coaching.SIM_NOTE, "", 1), expected, sims, True))
    cases.append(("a proved item wears the tag",
                  doc.replace('<li><span class="rec-num">1</span>',
                              '<li><span class="rec-num">1</span>' + coaching.SIM_TAG, 1), expected, sims, True))

    ok = True
    for name, d, ex, sm, must_fail in cases:
        bad = problems(d, ex, sm)
        good = bool(bad) == must_fail
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: {'rejected' if bad else 'accepted'}"
              + (f" ({bad[0]})" if bad and not must_fail else ""))

    # the loader refuses a badge in an authored tagged item before anything renders
    with open(os.path.join(report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    real = coaching.json.load

    def badged(fh):
        out = real(fh)
        p = facts["players"][0]
        out["columns"][p]["sim_recs"] = ['x<span class="badge" data-claim="C001"></span>']
        return out

    coaching.json.load = badged
    try:
        coaching.load_prose(report_dir, facts)
        refused = False
    except SystemExit:
        refused = True
    finally:
        coaching.json.load = real
    ok &= refused
    print(f"  {'ok ' if refused else 'BAD'} the loader refuses a badge in sim_recs")
    print(f"{'ok ' if ok else 'FAIL'} selftest {sum(1 for c in cases if c[4]) + 1} corruptions")
    return 0 if ok else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("usage: check_routes_techniques <report dir> [--selftest]", file=sys.stderr)
        return 2
    if "--selftest" in argv:
        return _selftest(argv[0])
    doc, expected, sims = _load(argv[0])
    bad = problems(doc, expected, sims)
    for b in bad:
        print(f"FAIL {argv[0]}: {b}", file=sys.stderr)
    if bad:
        return 1
    print(f"ok  {argv[0]}: " + ("no routes-techniques section" if expected is None else
          f"routes-techniques re-renders, stays quarantined, and {len(sims)} tagged 建議 items trace to it"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

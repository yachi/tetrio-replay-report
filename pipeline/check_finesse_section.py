"""Gate: the 最多犯錯嘅 finesse 擺位 section stays a faithful, quarantined render of sim/finesse-facts.json.

    python3 -m pipeline.check_finesse_section sessions/2026-10-29/report
    python3 -m pipeline.check_finesse_section sessions/2026-10-29/report --selftest

`build_report --check` already re-renders the region, so a HAND edit to the report is caught
there. What it cannot catch is a CODE edit to `finesse_section.py` that drops a control sentence:
the generator and the committed report then agree with each other and both say less than they
must. That is the job of this gate, the same job `check_opener_section` does for its section.

Checked:
  1. no artefact -> no region; an artefact -> exactly the region rendering it produces;
  2. the region carries every sentence in `finesse_section.REQUIRED`: the quarantine statement, the
     anchor against TETR.IO's own finesse counters, the statement that the rule is fitted, the
     softDrop exclusion, and the unit note (fault events, several per piece);
  3. no claim badge or `data-claim` inside the region;
  4. the artefact itself still says `report_eligible: false`;
  5. the anchor is internally whole: agree + exceptions + unknown == rounds;
  6. every ranked placement is consistent (faults >= faulty pieces >= 1, faulty <= scored) and the
     list is in descending order of faults.

`--selftest` plants one corruption per check and fails unless every one is rejected, plus a player
with no faulty placement, which must render its own sentence.
"""
import json
import os
import sys

from pipeline import finesse_section, region

NAME = "finesse-placements"


def _region(doc):
    start, end = region.markers(NAME, "pipeline/build_report.py")
    if start not in doc:
        return None
    i = doc.index(start) + len(start)
    return doc[i:doc.index(end, i)]


def problems(data, doc, players, positions):
    out = []
    body = _region(doc)
    if data is None:
        if body is not None:
            out.append("report has a finesse-placements region but the session has no artefact")
        return out
    if body is None:
        return ["the session has sim/finesse-facts.json but the report has no finesse-placements region"]
    if data.get("report_eligible") is not False:
        out.append("the artefact declares itself report-eligible")
    a = data["anchor"]
    if a["agree"] + len(a["exceptions"]) + a.get("unknown", 0) != a["rounds"]:
        out.append("the anchor does not add up to its rounds")
    for p in data["players"]:
        prev = None
        for m in p["top"]:
            if not (m["faults"] >= m["faulty"] >= 1 and m["faulty"] <= m["scored"]):
                out.append(f"{p['user']}: placement {m['piece']} col {m['col']} has inconsistent counts")
            if prev is not None and m["faults"] > prev:
                out.append(f"{p['user']}: placements are not in descending order of faults")
            prev = m["faults"]
    for m in finesse_section.REQUIRED:
        if m not in body:
            out.append(f"control sentence missing: {m}")
    if "data-claim" in body or "claim-badge" in body or "✓</" in body:
        out.append("a claim badge appears on engine output")
    expected = finesse_section.section(data, players, positions)
    if body.strip() != (expected or "").strip():
        out.append("the region is not what rendering sim/finesse-facts.json produces")
    return out


def _load(report_dir):
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()
    with open(os.path.join(report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    return finesse_section.load(report_dir), doc, facts["players"], finesse_section.positions(facts)


def _selftest(report_dir):
    data, doc, players, pos = _load(report_dir)
    body = _region(doc)
    if data is None or body is None:
        print(f"FAIL selftest needs a session with finesse data; {report_dir} has none", file=sys.stderr)
        return 1
    head, tail = doc.split(body, 1)
    cp = lambda: json.loads(json.dumps(data))
    cases = [("the committed report as it stands", data, doc, False)]
    for m in finesse_section.REQUIRED:
        cases.append((f"a control sentence is deleted ({m})", data, head + body.replace(m, "", 1) + tail, True))
    title = finesse_section.TITLE
    cases.append(("a claim badge appears", data,
                  head + body.replace(title, title + '<span class="claim-badge">✓</span>', 1) + tail, True))
    elig = cp(); elig["report_eligible"] = True
    cases.append(("the artefact declares itself report-eligible", elig, doc, True))
    moved = cp(); moved["players"][0]["top"][0]["faults"] += 7
    cases.append(("data moved but the report was not rebuilt", moved, doc, True))
    broken = cp(); broken["anchor"]["agree"] -= 1
    cases.append(("an anchor that no longer adds up", broken, doc, True))
    order = cp(); t = order["players"][0]["top"]; t[0], t[1] = t[1], t[0]
    cases.append(("placements out of order", order, doc, True))
    zero = cp(); zero["players"][0]["top"][0]["faulty"] = 0
    cases.append(("a ranked placement with no faulty piece", zero, doc, True))
    start, end = region.markers(NAME, "pipeline/build_report.py")
    cases.append(("an artefact with no region", data, doc.replace(body, "").replace(start, "").replace(end, ""), True))

    ok = True
    for name, d, dc, must_fail in cases:
        failed = bool(problems(d, dc, players, pos))
        good = failed == must_fail
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: {'rejected' if failed else 'accepted'}")

    empty = cp(); empty["players"][0]["top"] = []
    e = finesse_section.section(empty, players, pos)
    e_ok = e is not None and "呢晚冇一個擺位有多按" in e
    ok &= e_ok
    print(f"  {'ok ' if e_ok else 'BAD'} a player with no faulty placement renders its own sentence")
    print(f"{'ok ' if ok else 'FAIL'} selftest {sum(1 for c in cases if c[3])} corruptions + 1 branch")
    return 0 if ok else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("usage: check_finesse_section <report dir> [--selftest]", file=sys.stderr)
        return 2
    if "--selftest" in argv:
        return _selftest(argv[0])
    data, doc, players, pos = _load(argv[0])
    bad = problems(data, doc, players, pos)
    for b in bad:
        print(f"FAIL {argv[0]}: {b}", file=sys.stderr)
    if bad:
        return 1
    print(f"ok  {argv[0]}: " + ("no finesse data and no section" if data is None else
          "finesse-placements matches sim/finesse-facts.json and stays outside the claims chain"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

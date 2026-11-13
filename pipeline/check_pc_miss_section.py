"""Gate: the 行錯咗嗰一步 section stays a faithful, quarantined render of sim/pc-miss-facts.json.

    python3 -m pipeline.check_pc_miss_section sessions/2026-10-20/report
    python3 -m pipeline.check_pc_miss_section sessions/2026-10-20/report --selftest

`build_report --check` re-renders the region, so a HAND edit to the report is caught there. This gate
catches a CODE edit that drops a control sentence, and re-derives what the renderer trusts:

  1. no artefact -> no region; an artefact -> exactly the region rendering it produces;
  2. the region carries every sentence in `pc_miss_section.REQUIRED` (quarantine, preview-only,
     verified prefix, the solver's plan is one of many, possible ≠ intended, the selection rule);
  3. no claim badge or `data-claim` inside the region;
  4. the artefact says `report_eligible: false`;
  5. every REPORTED miss (placement, in_preview, verified) carries the category this gate computes
     on its own from the miss's board (a second implementation of `pc-miss.ts`'s `category`), and no
     other miss carries one;
  6. every reported miss's plan really clears its board: replayed here row by row, every cell empty
     when placed, every row full at the end, as many rows as `plan_H`;
  7. the placement drawn is the one that was played: its cells sit on empty cells of the board before.

`--selftest` plants one corruption per check and fails unless every one is rejected.
"""
import json
import os
import sys

from pipeline import pc_miss_section, region

NAME = "pc-miss"
FULL = 1023


def _region(doc):
    start, end = region.markers(NAME, "pipeline/build_report.py")
    if start not in doc:
        return None
    i = doc.index(start) + len(start)
    return doc[i:doc.index(end, i)]


def holes(g):
    n = 0
    for x in range(10):
        seen = False
        for y in range(len(g) - 1, -1, -1):
            if g[y][x] != ".":
                seen = True
            elif seen:
                n += 1
    return n


def height(g):
    return max([i + 1 for i, r in enumerate(g) if r.strip(".")] + [0])


def category(m):
    st = m["state"]
    g = pc_miss_section.with_placement(st["grid"], st["cells"], st["piece"])
    if holes(g) > holes(st["grid"]):
        return "hole"
    if height(g) > m["plan_H"]:
        return "over"
    return "hold" if m["plan"][0]["piece"] != st["piece"] else "spot"


def plan_clears(m):
    rows = [sum(1 << x for x, c in enumerate(r) if c != ".") for r in m["state"]["grid"]]
    h = m["plan_H"]
    rows = (rows + [0] * h)[:max(h, len(rows))]
    if any(rows[h:]):
        return False
    rows = rows[:h]
    for p in m["plan"]:
        if len(p["cells"]) != 4:
            return False
        for c in p["cells"]:
            y, x = divmod(c, 10)
            if y >= len(rows) or rows[y] >> x & 1:
                return False
            rows[y] |= 1 << x
        rows = [r for r in rows if r != FULL]
    return not rows


def data_problems(data):
    out = []
    if data.get("report_eligible") is not False:
        out.append("the artefact declares itself report-eligible")
    for r in data["rounds"]:
        for w in r["windows"]:
            for m in w["misses"]:
                where = f"m{r['match']} round {r['round']} {r['user']} lock {m['i']}"
                if not pc_miss_section.reported(m):
                    if "category" in m:
                        out.append(f"{where}: a miss that is not reported carries a category")
                    continue
                if m.get("category") != category(m):
                    out.append(f"{where}: category {m.get('category')} is not {category(m)}")
                if not plan_clears(m):
                    out.append(f"{where}: the plan does not clear its board")
                g = m["state"]["grid"]
                for c in m["state"]["cells"]:
                    y, x = divmod(c, 10)
                    if y < len(g) and g[y][x] != ".":
                        out.append(f"{where}: the placement overlaps the board before it")
                        break
    return out


def problems(data, doc, report_dir):
    body = _region(doc)
    if data is None:
        return ["report has a pc-miss region but the session has no artefact"] if body is not None else []
    if body is None:
        return ["the session has sim/pc-miss-facts.json but the report has no pc-miss region"]
    out = data_problems(data)
    for m in pc_miss_section.REQUIRED:
        if m not in body:
            out.append(f"control sentence missing: {m}")
    if "data-claim" in body or "claim-badge" in body or "✓</" in body:
        out.append("a claim badge appears on solver output")
    if out:
        return out
    with open(os.path.join(report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    session_dir = os.path.dirname(os.path.abspath(report_dir))
    try:
        expected = pc_miss_section.section(data, facts["players"],
                                           pc_miss_section.Locator(session_dir, data["session"]))
    except SystemExit as e:
        return [f"the renderer refuses the artefact: {e}"]
    if body.strip() != (expected or "").strip():
        out.append("the region is not what rendering sim/pc-miss-facts.json produces")
    return out


def _load(report_dir):
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()
    return pc_miss_section.load(report_dir), doc


def _first_reported(d):
    for r in d["rounds"]:
        for w in r["windows"]:
            for m in w["misses"]:
                if pc_miss_section.reported(m):
                    return m
    raise SystemExit("selftest needs a session with a reported miss")


def _selftest(report_dir):
    data, doc = _load(report_dir)
    body = _region(doc)
    if data is None or body is None:
        print(f"FAIL selftest needs a session with pc-miss data; {report_dir} has none", file=sys.stderr)
        return 1
    head, tail = doc.split(body, 1)
    cp = lambda: json.loads(json.dumps(data))
    cases = [("the committed report as it stands", data, doc, False)]
    for m in pc_miss_section.REQUIRED:
        cases.append((f"a control sentence is deleted ({m})", data, head + body.replace(m, "", 1) + tail, True))
    title = pc_miss_section.TITLE
    cases.append(("a claim badge appears", data,
                  head + body.replace(title, title + '<span class="claim-badge">✓</span>', 1) + tail, True))
    elig = cp(); elig["report_eligible"] = True
    cases.append(("the artefact declares itself report-eligible", elig, doc, True))
    cat = cp(); m = _first_reported(cat)
    m["category"] = next(k for k, _, _ in pc_miss_section.CATEGORIES if k != m["category"])
    cases.append(("a reported miss carries the wrong category", cat, doc, True))
    plan = cp(); m = _first_reported(plan); m["plan"] = m["plan"][:-1]
    cases.append(("a plan with its last piece dropped", plan, doc, True))
    hand = cp(); m = _first_reported(hand)
    k = next(j for j, p in enumerate(m["plan"]) if not p["held"]); m["plan"][k]["held"] = True
    cases.append(("an animated plan the hand cannot deal (a step marked held)", hand, doc, True))
    # that case must be refused by the renderer's hand replay, not only by the region's text moving
    why = problems(hand, doc, report_dir)
    hand_ok = any("the hand deals" in w for w in why)
    print(f"  {'ok ' if hand_ok else 'BAD'} the held-flag mutant is refused by the hand replay itself")
    over = cp(); m = _first_reported(over); m["state"]["cells"] = [c for c in m["state"]["cells"]]
    g = m["state"]["grid"]; filled = next(y * 10 + x for y, r in enumerate(g) for x, ch in enumerate(r) if ch != ".")
    m["state"]["cells"][0] = filled
    cases.append(("a placement drawn on a filled cell", over, doc, True))
    stray = cp()
    for r in stray["rounds"]:
        for w in r["windows"]:
            for mm in w["misses"]:
                if not pc_miss_section.reported(mm):
                    mm["category"] = "spot"
                    break
    cases.append(("a miss that is not reported carries a category", stray, doc, True))
    moved = cp(); m = _first_reported(moved); m["i"] += 1
    cases.append(("data moved but the report was not rebuilt", moved, doc, True))
    start, end = region.markers(NAME, "pipeline/build_report.py")
    cases.append(("an artefact with no region", data, doc.replace(body, "").replace(start, "").replace(end, ""), True))

    ok = hand_ok
    for name, d, dc, must_fail in cases:
        failed = bool(problems(d, dc, report_dir))
        good = failed == must_fail
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: {'rejected' if failed else 'accepted'}")
    print(f"{'ok ' if ok else 'FAIL'} selftest {sum(1 for c in cases if c[3])} corruptions")
    return 0 if ok else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("usage: check_pc_miss_section <report dir> [--selftest]", file=sys.stderr)
        return 2
    if "--selftest" in argv:
        return _selftest(argv[0])
    data, doc = _load(argv[0])
    bad = problems(data, doc, argv[0])
    for b in bad:
        print(f"FAIL {argv[0]}: {b}", file=sys.stderr)
    if bad:
        return 1
    print(f"ok  {argv[0]}: " + ("no pc-miss data and no section" if data is None else
          "pc-miss matches sim/pc-miss-facts.json and stays outside the claims chain"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

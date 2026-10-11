"""Gate: the 攻擊由邊度嚟 section stays a faithful, quarantined render of sim/attack-facts.json.

    python3 -m pipeline.check_attack_section sessions/2026-10-09/report
    python3 -m pipeline.check_attack_section sessions/2026-10-09/report --selftest

`build_report --check` already re-renders the region, so a HAND edit to the report is caught
there. What it cannot catch is a CODE edit to `attack_section.py` that drops a control sentence:
the generator and the committed report then agree with each other and both say less than they
must. That is the job of this gate, the same job `check_opener_section` does for its section.

Checked:
  1. no artefact -> no region; an artefact -> exactly the region rendering it produces;
  2. the region carries every sentence in `attack_section.REQUIRED`. Each is the licence for a
     table beside it: the quarantine statement, the two anchors (attack total and clear-type
     counts against the replay's own counters), the statement that per-clear attack has one
     implementation, the statement that the section is not about who won, and the rounding note
     that stops the component table being read as summing to the digit;
  3. no claim badge or `data-claim` inside the region — promoting engine output into the trust
     chain is what the section exists to avoid;
  4. the artefact itself still says `report_eligible: false`;
  5. the anchors are internally whole: agree + exceptions (+ unknown) == rounds.

`--selftest` plants one corruption per check and fails unless every one is rejected, plus the two
branches no session exercises (the lower-APP player listed first, and a tie), which must render.
"""
import json
import os
import sys

from pipeline import attack_section, region

NAME = "attack-sources"


def _region(doc):
    start, end = region.markers(NAME, "pipeline/build_report.py")
    if start not in doc:
        return None
    i = doc.index(start) + len(start)
    return doc[i:doc.index(end, i)]


def problems(data, doc, players):
    out = []
    body = _region(doc)
    if data is None:
        if body is not None:
            out.append("report has an attack-sources region but the session has no artefact")
        return out
    if body is None:
        return ["the session has sim/attack-facts.json but the report has no attack-sources region"]
    if data.get("report_eligible") is not False:
        out.append("the artefact declares itself report-eligible")
    for k in ("attack", "counts"):
        a = data["anchor"][k]
        if a["agree"] + len(a["exceptions"]) + a.get("unknown", 0) != a["rounds"]:
            out.append(f"anchor.{k} does not add up to its rounds")
    for m in attack_section.REQUIRED:
        if m not in body:
            out.append(f"control sentence missing: {m}")
    if "data-claim" in body or "claim-badge" in body or "✓</" in body:
        out.append("a claim badge appears on engine output")
    expected = attack_section.section(data, players)
    if body.strip() != (expected or "").strip():
        out.append("the region is not what rendering sim/attack-facts.json produces")
    return out


def _load(report_dir):
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()
    with open(os.path.join(report_dir, "facts.json"), encoding="utf-8") as fh:
        players = json.load(fh)["players"]
    return attack_section.load(report_dir), doc, players


def _selftest(report_dir):
    data, doc, players = _load(report_dir)
    body = _region(doc)
    if data is None or body is None:
        print(f"FAIL selftest needs a session with attack data; {report_dir} has none", file=sys.stderr)
        return 1
    head, tail = doc.split(body, 1)
    cases = [("the committed report as it stands", data, doc, False)]
    for m in attack_section.REQUIRED:
        cases.append((f"a control sentence is deleted ({m})", data, head + body.replace(m, "", 1) + tail, True))
    title = attack_section.TITLE
    cases.append(("a claim badge appears", data,
                  head + body.replace(title, title + '<span class="claim-badge">✓</span>', 1) + tail, True))
    elig = json.loads(json.dumps(data)); elig["report_eligible"] = True
    cases.append(("the artefact declares itself report-eligible", elig, doc, True))
    moved = json.loads(json.dumps(data)); moved["players"][0]["windows"]["mid"]["classes"]["TSD"]["n"] += 7
    cases.append(("data moved but the report was not rebuilt", moved, doc, True))
    broken = json.loads(json.dumps(data)); broken["anchor"]["attack"]["agree"] -= 1
    cases.append(("an anchor that no longer adds up", broken, doc, True))
    cases.append(("an artefact with no region", data, doc.replace(body, "").replace(
        region.markers(NAME, "pipeline/build_report.py")[0], "").replace(
        region.markers(NAME, "pipeline/build_report.py")[1], ""), True))

    ok = True
    for name, d, dc, must_fail in cases:
        failed = bool(problems(d, dc, players))
        good = failed == must_fail
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: {'rejected' if failed else 'accepted'}")

    # the branches no session takes: players listed the other way round, and a tie
    rev = attack_section.section(data, list(reversed(players)))
    ok &= rev is not None and attack_section.REQUIRED[0] in rev
    tie = json.loads(json.dumps(data))
    a, b = tie["players"]
    b["attack"], b["pieces"] = a["attack"], a["pieces"]
    t = attack_section.section(tie, players)
    tie_ok = t is not None and "兩個人嘅每粒攻擊一樣" in t
    ok &= tie_ok
    print(f"  {'ok ' if rev else 'BAD'} reversed player order renders")
    print(f"  {'ok ' if tie_ok else 'BAD'} a tie renders its own sentence")
    print(f"{'ok ' if ok else 'FAIL'} selftest {sum(1 for c in cases if c[3])} corruptions + 2 branches")
    return 0 if ok else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("usage: check_attack_section <report dir> [--selftest]", file=sys.stderr)
        return 2
    if "--selftest" in argv:
        return _selftest(argv[0])
    data, doc, players = _load(argv[0])
    bad = problems(data, doc, players)
    for b in bad:
        print(f"FAIL {argv[0]}: {b}", file=sys.stderr)
    if bad:
        return 1
    print(f"ok  {argv[0]}: " + ("no attack data and no section" if data is None else
          "attack-sources matches sim/attack-facts.json and stays outside the claims chain"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

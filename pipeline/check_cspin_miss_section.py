"""Gate: the C-Spin 冇砌 section stays a faithful, quarantined render of sim/cspin-miss-facts.json.

    python3 -m pipeline.check_cspin_miss_section sessions/2026-10-20/report
    python3 -m pipeline.check_cspin_miss_section sessions/2026-10-20/report --selftest

`build_report --check` re-renders the region, so a HAND edit to the report is caught there. This gate
catches a CODE edit that drops a control sentence, and re-derives what the renderer trusts:

  1. no artefact -> no region; an artefact -> exactly the region rendering it produces;
  2. the region carries every sentence in `cspin_miss_section.REQUIRED`;
  3. no claim badge or `data-claim` inside the region;
  4. the artefact says `report_eligible: false`;
  5. the counts are recomputed from the windows (cold-clear fired, the player fired, both, neither), and
     the cases are exactly the windows where cold-clear fired and the player did not;
  6. no case has a C-Spin slot ready at one of the player's T's (`ready_at_t` empty);
  7. the player's first placement in every case is the one the replay page decodes at that lock (with the
     garbage the replay inserts at that lock added under it): the same
     piece, and the board after it equal by occupancy (`replay_section.decode_boards`, a second
     implementation of the engine's board), so the card's replay link lands on the move it describes.

The renderer itself re-checks every board it draws against the next committed one (`ladder`).
`--selftest` plants one corruption per check and fails unless every one is rejected.
"""
import json
import os
import sys

from pipeline import cspin_miss_section as CM, region
from pipeline import replay_page as RP, replay_section as RS

NAME = "cspin-miss"


def _region(doc):
    start, end = region.markers(NAME, "pipeline/build_report.py")
    if start not in doc:
        return None
    i = doc.index(start) + len(start)
    return doc[i:doc.index(end, i)]


def count_problems(data):
    out = []
    if data.get("report_eligible") is not False:
        out.append("the artefact declares itself report-eligible")
    tally = {}
    want = []
    for w in data["windows"]:
        u = w["id"].split("/")[2]
        t = tally.setdefault(u, {"windows": 0, "cc": 0, "miss": 0, "both": 0, "human_only": 0})
        cc, hu = bool(w["cc"]["fire"]), bool(w["human"]["fire"])
        t["windows"] += 1
        t["cc"] += cc
        t["miss"] += cc and not hu
        t["both"] += cc and hu
        t["human_only"] += hu and not cc
        if cc and not hu:
            want.append(w["id"])
        if w.get("ready_at_t"):
            out.append(f"{w['id']}: a C-Spin slot was ready at one of the player's T's")
    got = data["counts"]["by_player"]
    for u in sorted(set(tally) | set(got)):
        if tally.get(u) != {k: v for k, v in got.get(u, {}).items()}:
            out.append(f"{u}: counts {got.get(u)} are not the windows' {tally.get(u)}")
    if data["counts"]["windows"] != len(data["windows"]):
        out.append(f"counts.windows {data['counts']['windows']} is not {len(data['windows'])}")
    if [c["id"] for c in data["cases"]] != want:
        out.append("the cases are not exactly the windows where cold-clear fired and the player did not")
    return out


def _rows(board_up):
    """decode_boards' y-UP board as 40 top-down occupancy rows."""
    rows = ["".join("." if c is None else "X" for c in r) for r in board_up]
    rows = rows[::-1]
    return ["." * 10] * (CM.H - len(rows)) + rows[-CM.H:] if len(rows) < CM.H else rows[-CM.H:]


def replay_problems(data, report_dir):
    session_dir = os.path.dirname(os.path.abspath(report_dir))
    rdata, facts = RP.load(session_dir)
    if rdata is None:
        return ["the session has no replay facts to check the cases' moves against"] if data["cases"] else []
    RS.check_artefact(rdata)
    out = []
    for c in data["cases"]:
        at = [(mi, ri) for mi, m in enumerate(facts["matches"]) if m["file"] == c["file"]
              for ri, fr in enumerate(m["rounds"]) if fr["index"] == c["round"]]
        if len(at) != 1:
            out.append(f"{c['id']}: {len(at)} rounds in facts.json")
            continue
        pl = RS.round_payload(rdata, facts, *at[0])
        p = [p for p in pl["players"] if p["user"] == c["user"]][0]
        # decode_boards yields the LIVE grid; copy each board to keep it
        dec = [(pc, full, [list(r) for r in b])
               for pc, full, b in RS.decode_boards(rdata, pl["seq"], p["locks"], RS.NEXT_SHOWN)]
        if c["lock"] >= len(dec):
            out.append(f"{c['id']}: the replay has no lock {c['lock']}")
            continue
        piece, _full, board = dec[c["lock"]]
        first = c["human"][0]
        if piece != first["piece"]:
            out.append(f"{c['id']}: the replay's lock {c['lock']} is {piece}, the case says {first['piece']}")
            continue
        after, _ = CM.lock_clear(CM.pad(c["field"]), first["cells"], first["piece"])
        # the case's field is the board before the lock's garbage; the replay inserts that garbage
        # under the stack before placing the piece, which leaves the same occupancy as adding it after
        for column, amount in p["locks"][c["lock"]][4]:
            row = "X" * column + "." + "X" * (9 - column)
            after = after[amount:] + [row] * amount
        if CM.occ(after) != CM.occ(_rows(board)):
            out.append(f"{c['id']}: the board after the player's move is not the replay's board after lock {c['lock']}")
    return out


def problems(data, doc, report_dir):
    body = _region(doc)
    if data is None:
        return ["report has a cspin-miss region but the session has no artefact"] if body is not None else []
    if body is None:
        return ["the session has sim/cspin-miss-facts.json but the report has no cspin-miss region"]
    out = count_problems(data)
    for m in CM.REQUIRED:
        if m not in body:
            out.append(f"control sentence missing: {m}")
    if "data-claim" in body or "claim-badge" in body or "✓</" in body:
        out.append("a claim badge appears on bot output")
    if out:
        return out
    out = replay_problems(data, report_dir)
    if out:
        return out
    with open(os.path.join(report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    session_dir = os.path.dirname(os.path.abspath(report_dir))
    try:
        expected = CM.section(data, facts["players"], CM.Locator(session_dir, data["session"]))
    except SystemExit as e:
        return [f"the renderer refuses the artefact: {e}"]
    if body.strip() != (expected or "").strip():
        out.append("the region is not what rendering sim/cspin-miss-facts.json produces")
    return out


def _load(report_dir):
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()
    return CM.load(report_dir), doc


def _selftest(report_dir):
    data, doc = _load(report_dir)
    body = _region(doc)
    if data is None or body is None or not data["cases"]:
        print(f"FAIL selftest needs a session with a C-Spin case; {report_dir} has none", file=sys.stderr)
        return 1
    head, tail = doc.split(body, 1)
    cp = lambda: json.loads(json.dumps(data))
    cases = [("the committed report as it stands", data, doc, False)]
    for m in CM.REQUIRED:
        cases.append((f"a control sentence is deleted ({m})", data, head + body.replace(m, "", 1) + tail, True))
    title = CM.TITLE
    cases.append(("a claim badge appears", data,
                  head + body.replace(title, title + '<span class="claim-badge">✓</span>', 1) + tail, True))
    elig = cp(); elig["report_eligible"] = True
    cases.append(("the artefact declares itself report-eligible", elig, doc, True))
    cnt = cp(); u = next(iter(cnt["counts"]["by_player"])); cnt["counts"]["by_player"][u]["miss"] += 1
    cases.append(("a count that is not the windows'", cnt, doc, True))
    drop = cp(); drop["cases"] = drop["cases"][1:]
    cases.append(("a case dropped from the list", drop, doc, True))
    ready = cp(); w = next(w for w in ready["windows"] if w["id"] == ready["cases"][0]["id"])
    w["ready_at_t"] = [0]
    cases.append(("a case whose slot was ready at a T (a misdrop)", ready, doc, True))
    lock = cp(); lock["cases"][0]["lock"] += 1
    cases.append(("a case moved one lock off its replay move", lock, doc, True))
    cell = cp(); c0 = cell["cases"][0]["human"][0]["cells"][0]; c0[0] = (c0[0] + 5) % 10
    cases.append(("the player's first move drawn in the wrong place", cell, doc, True))
    ccb = cp(); b = ccb["cases"][0]["cc_boards"]
    if b:
        b[0] = b[0][1:] + [b[0][-1]]
        cases.append(("a cold-clear board that is not the one its step leaves", ccb, doc, True))
    fire = cp(); w = next(w for w in fire["windows"] if w["id"] == fire["cases"][0]["id"])
    w["cc"]["steps"][w["cc"]["at"]]["piece"] = "S"
    cases.append(("cold-clear's deciding step is not a T", fire, doc, True))
    start, end = region.markers(NAME, "pipeline/build_report.py")
    cases.append(("an artefact with no region", data, doc.replace(body, "").replace(start, "").replace(end, ""), True))

    ok = True
    for name, d, dc, must_fail in cases:
        try:
            failed = bool(problems(d, dc, report_dir))
        except SystemExit:
            failed = True
        good = failed == must_fail
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: {'rejected' if failed else 'accepted'}")
    print(f"{'ok ' if ok else 'FAIL'} selftest {sum(1 for c in cases if c[3])} corruptions")
    return 0 if ok else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("usage: check_cspin_miss_section <report dir> [--selftest]", file=sys.stderr)
        return 2
    if "--selftest" in argv:
        return _selftest(argv[0])
    data, doc = _load(argv[0])
    bad = problems(data, doc, argv[0])
    for b in bad:
        print(f"FAIL {argv[0]}: {b}", file=sys.stderr)
    if bad:
        return 1
    print(f"ok  {argv[0]}: " + ("no cspin-miss data and no section" if data is None else
          "cspin-miss matches sim/cspin-miss-facts.json and stays outside the claims chain"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Gate: the round-replay region must be exactly what this session's replay-facts.json renders to.

    python3 -m pipeline.check_replay_section sessions/2026-10-03/report
    python3 -m pipeline.check_replay_section sessions/2026-10-03/report --selftest

The third quarantined section's guard, the sibling of `check_opener_section.py` and
`check_forecast_section.py`, for the same reason: the rest of the report is protected by lemmas over
facts.json and this section is deliberately outside that chain, so without its own gate its region
could drift from its source, or be promoted into the chain, with nothing to say so.

Checked:
  1. the committed region is EXACTLY a re-render of `sim/replay-facts.json` + `facts.json` (which
     includes the inlined player script, `replay_player.js`, so an edit to that file without a
     rebuild is drift too) — and a session with no artefact, or no round `_intense_round` selects,
     carries no region at all;
  2. the artefact declares `report_eligible: false` (render refuses otherwise, and so does this);
  3. no claim badge, `data-claim` or 已驗證 anywhere inside the region — a ✓ on simulator boards is
     the promotion this section exists to avoid;
  4. every sentence the quarantine rests on is present (`replay_section.REQUIRED`): the eyebrow, the
     「未經證明」 title, 「冇 claim 編號、冇 ✓ 標記」, the drawn-drop-path sentence, the hole-column
     sentence and the three-state boundary sentence, plus the flag wording;
  5. the region assigns no markup through innerHTML / outerHTML / insertAdjacentHTML /
     document.write — report.html allows exactly one innerHTML, and it is not here.

Every check has a mutant in `--selftest`. A check with no mutant proving it fires is a comment.
"""
import difflib
import json
import os
import re
import sys

from pipeline import region, replay_section

BADGE = re.compile(r"data-claim|claim-badge|已驗證")
MARKUP_SINK = re.compile(r"\binnerHTML\b|\bouterHTML\b|insertAdjacentHTML|document\.write")
START, END = region.markers(replay_section.SECTION_ID, "pipeline/build_report.py")


def _load(report_dir):
    with open(os.path.join(report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()
    return replay_section.load(report_dir), facts, doc


def _render(data, facts):
    """The region body, or None; a render that refuses (SystemExit) is reported as a string."""
    try:
        return replay_section.section(replay_section.payload(data, facts)), None
    except SystemExit as e:
        return None, str(e)


def problems(data, facts, doc):
    """Every reason `doc`'s replay region disagrees with `data`; empty means it agrees."""
    i, j = doc.find(START), doc.find(END)
    if data is not None and data.get("report_eligible") is not False:
        return ["replay-facts.json no longer declares report_eligible:false"]
    rendered, refused = _render(data, facts)
    if refused:
        return [f"the artefact does not render: {refused}"]
    if rendered is None:
        if i >= 0 or j >= 0:
            return ["has a round-replay region but this session renders none "
                    f"(no {replay_section.FACTS_REL}, or no round long enough to select)"]
        return []
    if i < 0 or j < 0:
        return ["round-replay region missing from report.html"]
    body = doc[i + len(START):j]
    bad = []
    expected = "\n" + rendered + "\n"
    if body != expected:
        diff = list(difflib.unified_diff(
            expected.splitlines(), body.splitlines(), fromfile="rendered from replay-facts.json",
            tofile="committed report.html", lineterm="", n=1))
        bad.append("the committed round-replay region is not what this session's data renders "
                   "to:\n" + "\n".join("      " + d[:200] for d in diff[:40]))
    if BADGE.search(body):
        bad.append("the section carries a claim badge — simulator boards must not be badged")
    for s in replay_section.REQUIRED:
        if s not in body:
            bad.append(f"a quarantine sentence is gone: {s[:40]!r}…")
    if MARKUP_SINK.search(body):
        bad.append("the region assigns markup (innerHTML or similar) — build nodes instead")
    return bad


def _selftest(report_dir):
    """Controls: PASS the committed pair, FAIL every corruption of it."""
    data, facts, doc = _load(report_dir)
    i, j = doc.find(START), doc.find(END)
    if data is None or i < 0:
        print(f"FAIL selftest needs a session WITH a round-replay region; {report_dir} has none",
              file=sys.stderr)
        return 1
    head, body, tail = doc[:i + len(START)], doc[i + len(START):j], doc[j:]

    def edit(new_body):
        return head + new_body + tail

    cases = [("control: the committed pair agrees", data, doc, True, None)]
    title = replay_section.TITLE_MARK
    cases.append(("a claim badge on simulator output", data,
                  edit(body.replace(title, title + '<span class="claim-badge">✓</span>', 1)),
                  True, "claim badge"))
    cases.append(("a data-claim attribute inside the region", data,
                  edit(body.replace('class="rp-player"', 'class="rp-player" data-claim="C001"', 1)),
                  True, "claim badge"))
    for s in replay_section.REQUIRED:
        cases.append((f"required sentence deleted ({s[:16]}…)", data,
                      edit(body.replace(s, "")), s in body, "quarantine sentence is gone"))
    cases.append(("an innerHTML assignment in the player", data,
                  edit(body.replace('"use strict";', '"use strict";\n  document.body.innerHTML = "";', 1)),
                  True, "assigns markup"))
    eligible = json.loads(json.dumps(data))
    eligible["report_eligible"] = True
    cases.append(("the artefact declares itself report-eligible", eligible, doc, True,
                  "report_eligible"))
    gone = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n*", "", doc, flags=re.S)
    cases.append(("the region is deleted while the artefact exists", data, gone, True,
                  "region missing"))
    cases.append(("a region sits there with no artefact", None, doc, True, "renders none"))
    # Data moved without a rebuild. Which datum is decided by the render, not written down: the
    # selected round's first player's `frames` feeds the payload verbatim.
    stale = json.loads(json.dumps(data))
    sel = replay_section.select(facts)
    m = facts["matches"][sel[0]]
    rr = next(r for r in stale["rounds"] if r["file"] == m["file"] and r["round"] == sel[2]["index"])
    rr["players"][0]["frames"] += 7
    cases.append(("data moved but the report was not rebuilt (frames)", stale, doc,
                  _render(stale, facts)[0] != _render(data, facts)[0], "not what this session"))

    # `want` is the substring of the ONE problem this mutant targets (None for the control). Every
    # content mutant is also caught by the exact re-render, so "rejected" alone would pass with the
    # targeted check deleted; requiring its own message is what proves each check fires by itself.
    ok = True
    for name, d, dc, applies, want in cases:
        if not applies:
            print(f"  BAD {name}: the mutant did not apply — the sentence is not in the region")
            ok = False
            continue
        found = problems(d, facts, dc)
        failed = bool(found)
        must_fail = want is not None
        good = (not failed) if want is None else any(want in f for f in found)
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: {'rejected' if failed else 'accepted'}"
              f"{'' if good else '  <- expected ' + ('rejection' if must_fail else 'acceptance')}")
    n = sum(1 for c in cases if c[4])
    print(f"{'ok ' if ok else 'FAIL'} selftest {n} corruptions, {'all caught' if ok else 'SOME MISSED'}")
    return 0 if ok else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("usage: check_replay_section <report dir> [--selftest]", file=sys.stderr)
        return 2
    report_dir = argv[0]
    if "--selftest" in argv:
        return _selftest(report_dir)
    data, facts, doc = _load(report_dir)
    bad = problems(data, facts, doc)
    for b in bad:
        print(f"FAIL {report_dir}: {b}", file=sys.stderr)
    if bad:
        return 1
    if START not in doc:
        print(f"ok  {report_dir} renders no round replay and carries no region")
        return 0
    print(f"ok  round-replay region matches {replay_section.FACTS_REL} and stays outside the "
          "claims chain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

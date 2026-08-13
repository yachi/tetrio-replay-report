"""Gate: the opener section's rendered numbers must match sim/opener-facts.json.

    python3 -m pipeline.check_opener_section sessions/2026-08-09/report
    python3 -m pipeline.check_opener_section sessions/2026-08-09/report --selftest

The sibling of `check_forecast_section.py`, and it exists for the same reason: the rest of the
report is protected by Dafny lemmas over facts.json, this section is deliberately outside that
chain, so without its own guard its numbers could drift from their source with nothing to catch
it. The argument for re-rendering rather than sampling is spelled out there and is not repeated.

Nine things are checked:
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
  5. the ORDERING table keeps its class control. `cspin_order` counts a Triple before a Double,
     and harddrop files 38 openers under that signature, so the count names a class. Drop the
     paragraph and the table beside it becomes the C-Spin count checks 4 exists to prevent.
  6. the NAMED-OPENER table keeps its three: the baseline column (the `<=N` band discriminates
     nothing, only an exact match does), the alias warning (two openers sharing a first-bag
     field are the same rounds twice), and the PCO ceiling (PCO is defined by an outcome, and
     the only trustworthy source for that outcome is facts.json, never this simulator).
  7. the PERFECT CLEAR TIMING keeps the two sentences that license it: the per-round agreement
     between the simulator's Perfect Clear count and the replay's own, and harddrop's ten-piece
     deadline. Those piece numbers are the only simulator figures in this section that a verified
     source could have contradicted; printing them without saying it did not is the same overclaim
     as a badge, and without the deadline "landed on piece 20" has nothing to be late for.
  8. the DONATION table keeps its well-provenance paragraph. Every donation in this corpus sits on
     a garbage-derived well, and the board source keeps the engine's seeded-RNG hole columns, which
     disagree with the ige-recorded ones 97 of 103 times — so the count is a statement about a
     SHAPE the board offered and never about which column a player donated into. Drop the paragraph
     and a shape count becomes "this player donated into that well" 21 times, which is the strongest
     claim in this section and the one the data supports least.
  9. the STMB CAVE table keeps BOTH cross-tabs. By depth: nearly every >=3-wide hit is one row
     deep, i.e. a dimple. By lines: the same gap fires MORE often under T-spin Triples, where it is
     ordinary TST residue. Either one alone leaves the count readable as a cave count, so both are
     demanded, together with the class note saying harddrop's own page calls the shape a Sky Prop
     variant that Shachiku Train shares — the same rule as the ordering table's class control.

Every one of these controls has a mutant in `--selftest` that deletes its sentence and expects
a rejection. A control with no mutant proving it fires is a comment, not a gate.
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

# The control the ORDERING table may not be published without, and the most load-bearing of the
# four. `cspin_order` counts a Triple before a Double, and harddrop files 38 openers under
# `Triple Double openers` — C-Spin, Honey Cup, Stray Cannon and Mountainous Stacking among them —
# so the number names a CLASS. Delete this paragraph and the table beside it reads as a C-Spin
# count, which is exactly the claim this section spent three tables refusing to make.
CLASS_MARKERS = ("分唔出呢一類入面邊個定式",)

# The control the NAMED-OPENER table may not be published without. Its `≤N 格` column is ~90% for
# every opener AND for the control set, so it discriminates nothing; only an exact match does.
# Losing the sentence that says so turns a similarity score into a repertoire claim.
NAMED_MARKERS = ("睇「一模一樣」嗰欄",)

# Two named openers with an identical first-bag field are the same rounds counted twice. The rows
# stay (the reader asked for MS1, MS2 and MS3 by name); the sentence forbidding their addition is
# what keeps the table honest.
ALIAS_MARKER = "唔可以加埋一齊"

# PCO is defined by an OUTCOME, and the outcome has a trustworthy source that is not this
# simulator. The sentence naming that source is the ceiling on the whole row.
PCO_MARKER = "clears.allclear"

# The timing figures ("this session's perfect clears landed on pieces 15 and 20") are the only
# numbers in this section that a VERIFIED source could have contradicted, and the only reason they
# may be printed is that it did not: the simulator's per-round count was compared with the replay's
# own counter for every round. Two sentences carry that, and each is a separate way of publishing
# the timing dishonestly if it goes:
#   - the agreement figure — without it the timing is an unchecked simulator number wearing the
#     same typeface as the checked ones;
#   - harddrop's own ten-piece deadline — without it "landed on piece 20" has nothing to be late
#     FOR, and the row reads as a PCO count rather than as the refutation of one.
TIMING_MARKERS = ("個回合啱", "harddrop 畫 PCO 嘅死線")

# The control the DONATION table may not be published without, and the one this section's board
# source forces. Two sentences, each closing a different way of over-reading the count:
#   - where the well came from — every donation here sits on a garbage-derived well, so the count
#     is about a board the opponent built, not a Tetris well the player kept;
#   - the oracle's 97-of-103 garbage-hole-column disagreement, which is what turns "donated into
#     that column" into an unsupportable claim while leaving "this shape occurred" standing.
DONATION_MARKERS = ("條井邊度嚟", "垃圾窿嗰條欄")

# The STMB Cave table's two cross-tabs, kept as separate constants because they are demanded under
# DIFFERENT conditions: the depth sentence exists only when there is a wide gap to be shallow, while
# the Triple comparison is printed whenever there is anything to cross-tab — including the session
# where the Doubles count is zero and the Triples count is not, which is the control working.
CAVE_DEPTH_MARKER = "淨係深一行"
CAVE_TRIPLE_MARKERS = ("嘅 T-spin 底下出現咗", "TST 本身嘅殘形")

# And its class note, the same rule as CLASS_MARKERS one table up: harddrop's own page says the cave
# "is just Sky Prop but with 3 columns wide hole" and that a variation shares Shachiku Train's shape,
# so the geometry names a family. Without this the table reads as a count of one named technique.
CAVE_CLASS_MARKERS = ("唔係邊一個定式",)


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

    # 5. the ordering table may not be published without the class control
    if data.get("ordering_class") and any(p["rounds_with_both"]
                                          for p in data["ordering"]["players"]):
        for marker in CLASS_MARKERS:
            if marker not in body:
                bad.append(
                    f"the ordering class control is gone ({marker!r} missing) — "
                    f"{data['ordering_class']['openers']} catalogued openers share the "
                    "Triple-before-Double signature, so the count may not stand alone as a "
                    "C-Spin figure")

    # 6. the named-opener table's own controls
    no = data.get("named_openers")
    if no and any(p["boards_scored"] for o in no["openers"] for p in o["players"]):
        for marker in NAMED_MARKERS:
            if marker not in body:
                bad.append(f"the named-opener baseline control is gone ({marker!r} missing) — "
                           "the exact-match column may not be published without the control "
                           "column that says the ≤N band discriminates nothing")
        if any(o["occupancy_aliases"] for o in no["openers"]) and ALIAS_MARKER not in body:
            bad.append(f"the occupancy-alias warning is gone ({ALIAS_MARKER!r} missing) — two "
                       "openers share a first-bag field, so their rows are the same rounds and a "
                       "reader must be told not to add them")
    if data.get("session_perfect_clears") and PCO_MARKER not in body:
        bad.append(f"the PCO ceiling is gone ({PCO_MARKER!r} missing) — PCO is defined by an "
                   "outcome, and the row may not be published without the verified source that "
                   "bounds it")

    # 7. Perfect Clear TIMING is the one simulator figure here with a verified counterpart, so it
    #    is published only together with the comparison against it. Checked when the artifact says
    #    the comparison passed AND the session has a perfect clear to place — a session with none
    #    renders no timing sentence and must not be asked for one.
    timing = data.get("perfect_clear_timing")
    spc = data.get("session_perfect_clears")
    # The same condition `_pco_note` renders the timing sentence under, written once here rather
    # than approximated: a gate that demands a control the section had no reason to print fails
    # the honest report and teaches everyone to delete the gate.
    if timing and timing["check"]["agrees"] and spc and sum(spc["per_player"].values()):
        for marker in TIMING_MARKERS:
            if marker not in body:
                bad.append(f"the Perfect Clear timing control is gone ({marker!r} missing) — "
                           "the piece numbers come from the simulator and may only be published "
                           "beside the per-round count check that licenses them and beside "
                           "harddrop's own deadline that gives them a meaning")

    # 8. the donation count may not be published without the paragraph saying whose well it was and
    #    what the board source cannot establish about it. Conditioned on there BEING a donation,
    #    which is the same condition `_donation_note` renders under: an artifact predating the
    #    metric, or a session that donated nothing, has no such paragraph and must not be asked for
    #    one.
    dn = data.get("donation")
    if dn and sum(p["donations"] for p in dn["players"]):
        for marker in DONATION_MARKERS:
            if marker not in body:
                bad.append(f"the donation well-provenance control is gone ({marker!r} missing) — "
                           "every donation here sits on a garbage-derived well and the board "
                           "source's hole columns disagree with the ige-recorded ones 97 of 103 "
                           "times, so the count may not be published as which well was donated "
                           "into")

    # 9. the cave count may not be published without either cross-tab. Same split as the section
    #    renders them under: the depth sentence needs a wide gap to exist, the Triple comparison
    #    and the class note need only a scored T-spin to compare against.
    sc = data.get("stmb_cave")
    if sc:
        scored = sum(p["tspin_doubles_scored"] for p in sc["players"])
        scored += sc["triple_control"]["tspin_triples_scored"]
        if sum(p["width_ge_3"] for p in sc["players"]) and CAVE_DEPTH_MARKER not in body:
            bad.append(f"the cave depth control is gone ({CAVE_DEPTH_MARKER!r} missing) — a "
                       "3-wide gap one row deep is a dimple, and the width count may not be "
                       "published without the depth cross-tab that says how many were")
        if scored:
            for marker in (*CAVE_TRIPLE_MARKERS, *CAVE_CLASS_MARKERS):
                if marker not in body:
                    bad.append(
                        f"the cave Triple/class control is gone ({marker!r} missing) — the same "
                        "shape fires under T-spin Triples as ordinary TST residue, and harddrop "
                        "files the geometry as a Sky Prop variant, so the count names a family "
                        "and may not stand alone as an STMB Cave figure")

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
    # Every control paragraph is the reason its table may be printed at all, so deleting one while
    # keeping its table must be a failure and not a cosmetic edit. Listed together because they
    # are the same rule applied four times, and because a control with no mutant proving it fires
    # is a comment, not a gate.
    # The list is enumerated by name and is NOT derived, so a control added to `problems` without a
    # line here has no mutant and is a comment. Every marker constant in this module belongs in it.
    for marker in (*CONTROL_MARKERS, *CLASS_MARKERS, *NAMED_MARKERS, ALIAS_MARKER,
                   PCO_MARKER, *TIMING_MARKERS, *DONATION_MARKERS, CAVE_DEPTH_MARKER,
                   *CAVE_TRIPLE_MARKERS, *CAVE_CLASS_MARKERS):
        if marker in body:
            cases.append((f"a control sentence is deleted ({marker})", data,
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

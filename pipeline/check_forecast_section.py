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

# The fifth bucket's sentence, in the ANCHOR_MARKERS shape `check_opener_section` uses, and for the
# same reason: checks 1-2 compare the render against the renderer, so they are blind to a sentence
# the renderer stops producing. Measured — deleting the `path_opened` paragraph and REBUILDING the
# six reports leaves every other case here green, because both sides then agree on a section that
# no longer mentions the bucket. Its events would be published as 「其餘 N 個個窿位本身冇變好」,
# which is a different false sentence from the 「玩家自己落嗰隻棋整出嚟」 this bucket was created to
# retract, and just as invisible.
#
# TWO anchors, and both are demanded, in the shape `check_opener_section`'s ANCHOR_MARKERS use: one
# for the CLAIM the bucket rests on, one for WHY it is not a forecast. Keeping only the second would
# let the claim drift past what the predicate proves — the first draft asserted the slot was
# unchanged cell for cell, which the branch never tests. Keeping only the first would let the reason
# clause be replaced by a different wrong one — the exact defect commit 4d0f2f5 fixed two paragraphs
# down, where a rejection reason was hardcoded and shipped false in two reports.
#
# The first anchor is the COUNTERFACTUAL, deliberately, not 「唔係整咗個窿位出嚟」: both sentences are
# true, but only the counterfactual is the thing `localiseMechanism`'s `access` branch actually
# computes, so it is the one whose loss would leave the paragraph claiming more than it can show.
#
# Every anchor must be free of markup. 「消行<strong>通咗條路</strong>」 reads as one phrase in the
# source and is not one in the document; a marker written across that tag matches nothing, and a
# check that can never pass looks exactly like a check that can never fail until it is run.
PATH_OPENED_MARKERS = (
    "消嗰行自己一個就已經夠",           # the claim: the counterfactual the `access` branch computes
    "單睇消嗰行喺邊就已經唔合格",        # the reason: clause 3, on geometry, before 2 and 4 are asked
)


def render(data) -> str:
    """`forecast_section.section(data)` for an artifact that HAS one. Never None.

    `section` returns None for a session with no `sim/forecast-facts.json`, which is a real case
    for `build_report` and not one for any caller in this file: all five sites have already
    established `data is not None` (`problems` returns early, `_selftest` bails, and every mutant
    is a deep copy of a non-None artifact). Pyright cannot see that across the call, and three of
    the five concatenate the result, so the narrowing is stated here once instead of five times.

    It RAISES rather than substituting `""`. An empty section string is not a safe default: it
    compares equal to a report whose forecast region is empty, so 「the renderer produced nothing」
    would render as 「the report matches」 — the `?? 0` shape one type over, and the gate would go
    green on the artifact it exists to check.

    TypeError, not ValueError, and the distinction is load-bearing: `_selftest` swallows ValueError
    in two places (the partition assert, which is an expected outcome for a deliberately incoherent
    mutant). A None here is a broken contract, not an expected outcome, and must not be caught by
    either of them.
    """
    out = forecast_section.section(data)
    if out is None:
        raise TypeError("forecast_section.section returned None for a non-None artifact — "
                        "this file only ever renders sessions that have forecast data")
    return out


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
    expected = "\n" + render(data) + "\n"
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

    # 3. a session that HAS path_opened events must say so. Only demanded when the bucket fired:
    #    four of the six sessions have none, and a section that printed 「0 個」 there would be
    #    publishing a measured zero where the honest rendering is an absence.
    if sum(p["path_opened"] for p in data["players"]):
        for mk in PATH_OPENED_MARKERS:
            if mk not in body:
                bad.append(f"the artifact has path_opened events but the section never says so "
                           f"({mk!r} missing) — they read as 「其餘」")

    if data.get("report_eligible") is not False:
        bad.append("forecast-facts.json no longer declares report_eligible:false")
    if "未經證明" not in body:
        bad.append("the section no longer declares itself unproved (未經證明)")
    if BADGE.search(body):
        bad.append("the section carries a claim badge — simulator output must not be badged")

    return bad


def _one_rejection(data, verdict):
    """`data` with exactly one mechanism-established event rejected, and `verdict` the reason.

    Built so the clause mutant below has the same teeth on every session. Three of the six have
    `mechanism_established == forecast_total` and therefore no rejection to re-bucket; re-using
    whatever a session happens to hold would make the case vacuous on exactly those three and
    still print `ok`.

    Only the ONE player is touched, and only the fields the rejection implies, so two calls with
    different `verdict` differ in nothing but the clause — which is what makes a difference in the
    rendered section attributable to the clause and to nothing else. Returns None when no player
    has a mechanism-established event, which the caller must treat as a failure of the selftest
    rather than as a skip.
    """
    d = json.loads(json.dumps(data))
    for p in d["players"]:
        if p["mechanism_established"] < 1:
            continue
        rb = p["rejected_by"]
        for k in rb:
            rb[k] = 0
        rb["counted"] = p["mechanism_established"] - 1
        rb[verdict] = 1
        p["forecast_total"] = rb["counted"]
        p["clause2_undecided"] = (rb["floor_undecidable"]
                                  + rb["floor_undecidable_and_closing_clear_was_spin"])
        return d
    return None


def _one_path_opened(data):
    """`data` with exactly one of a player's `reactive` events re-bucketed as `path_opened`.

    MANUFACTURED rather than perturbed, for the reason `_one_rejection` is: four of the six
    sessions have `path_opened == 0`, so a mutant that moved whatever a session happened to hold
    would be vacuous on exactly those four and still print `ok`.

    The move is between two buckets of the same partition, so the five still sum to
    `verified_tspins` — this case exercises the bucket's SENTENCE and its effect on the 「其餘」
    remainder, and leaves the partition assert to `_broken_partition` below. Returns None when no
    player has a reactive event, which the caller must treat as a failure rather than a skip.
    """
    d = json.loads(json.dumps(data))
    for p in d["players"]:
        if p["reactive"] < 1:
            continue
        p["reactive"] -= 1
        p["path_opened"] += 1
        return d
    return None


def _broken_partition(data):
    """`data` with a `path_opened` that no other bucket paid for.

    The five buckets are exhaustive over `verified_tspins`, so this is not a smaller 「其餘」 — it
    is an artifact whose buckets and denominator disagree, and the section must refuse to render
    rather than publish a breakdown that outnumbers its own denominator.

    Measured with the assert deleted: this input still RENDERS, one 個 larger, so the case's
    outcome goes `raised` -> `rejected` and only an expectation that distinguishes the two catches
    it. That is the whole reason the case wants a RAISE rather than "some complaint" — a rejection
    here means the section was willing to publish the incoherent artifact and the gate merely
    noticed the report had not been rebuilt to match it.
    """
    d = json.loads(json.dumps(data))
    d["players"][0]["path_opened"] += 1
    return d


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
    rendered = render(data)
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
        try:
            differs = render(stale) != rendered
        except ValueError:
            # Bumping one bucket breaks the five-way partition, so the section refuses to render
            # it at all. That is the partition assert doing its job, but it is NOT this case: this
            # one needs an artifact the section will happily render DIFFERENTLY. Skip to a field
            # outside the partition. The refusal has its own case below.
            continue
        if differs:
            moved = (".".join(str(k) for k in path), stale)
            break
    if moved is None:
        # Not a skip: if no field of the JSON changes what the section renders, this gate is
        # comparing the report against nothing and the whole file is decorative.
        print("FAIL selftest: no JSON field moves the render — the gate cannot see its data",
              file=sys.stderr)
        return 1
    cases.append((f"data moved but the report was not rebuilt ({moved[0]})", moved[1], doc, True))

    # ── WHICH CLAUSE rejected an event must move the render ──────────────────────────────────
    #
    # Every mutant above moves a NUMBER. None of them can see a sentence whose reason never
    # varies, and from 2026-08-03 to 2026-08-16 that is exactly what this section had: whenever
    # `mechanism_established > forecast_total` it printed clause 2 (「個底係天花板之後先至嚟」),
    # while 2026-08-09 and 2026-08-14 were rejected by clause 4. Both reports shipped the false
    # sentence and this gate said ok on both, because re-rendering compares the renderer against
    # itself and neither side read the fact.
    #
    # So the mutant re-attributes an event between two clauses and requires the rendered sentence
    # to change. If it does not, the branch is decorative and the defect is back.
    #
    # `_one_rejection` MANUFACTURES the rejection rather than re-bucketing an existing one, so the
    # case has teeth on every session — three of the six have no uncounted event at all, and a
    # mutant that quietly does nothing there is the hole this whole exercise is about. The control
    # (same data, matching document) is what makes the failure attributable to the clause: without
    # it, a malformed document would produce the same rejection and prove nothing.
    a, b = _one_rejection(data, "floor_arrived_later"), _one_rejection(data, "closing_clear_was_spin")
    if a is None or b is None:
        print("FAIL selftest: no player has a mechanism-established event to re-attribute — "
              "the clause mutant would prove nothing", file=sys.stderr)
        return 1
    doc_a = head + "\n" + render(a) + "\n" + tail
    cases.append(("control: clause 2 rejects, and the report says so", a, doc_a, False))
    cases.append(("the artifact says clause 4 rejected it, the report still says clause 2",
                  b, doc_a, True))

    # ── THE FIFTH BUCKET MUST HAVE ITS OWN SENTENCE ──────────────────────────────────────────
    #
    # Before `path_opened` existed, its two events were split between `self_built` and
    # `unattributed` by an irrelevance, and the `self_built` half is what published
    # 「玩家自己落嗰隻棋整出嚟」 of a slot that piece did not make. A fifth bucket read by nobody
    # would land in 「其餘」 and be published as 「個窿位本身冇變好」 instead — a different wrong
    # sentence, equally invisible to a gate that only compares numbers.
    #
    # So: re-bucket one reactive event as path_opened and require the rendered section to move.
    # Manufactured, so the case has teeth on all six sessions rather than on the two that hold one.
    po = _one_path_opened(data)
    if po is None:
        print("FAIL selftest: no player has a reactive event to re-bucket — "
              "the path_opened mutant would prove nothing", file=sys.stderr)
        return 1
    doc_po = head + "\n" + render(po) + "\n" + tail
    cases.append(("control: an event is path_opened, and the report says so", po, doc_po, False))
    cases.append(("the artifact moved an event into path_opened, the report was not rebuilt",
                  po, doc, True))
    cases.append(("the report claims a path_opened event the artifact does not have",
                  data, doc_po, True))
    # One case per anchor, on every session. Each is caught by check 1 as well — both fire on the
    # same input, so these do not ATTRIBUTE the rejection to the marker, and they cannot: the
    # failure the markers exist for is a renderer that stops emitting the sentence, which no
    # selftest built out of the live renderer can plant. That one was mutation-tested by hand (see
    # PATH_OPENED_MARKERS) and is the reason the check is here rather than only in review. What
    # these cases DO pin is that each anchor is present in the render at all — the first version of
    # this marker was written across a `<strong>` tag, matched nothing, and would have been a check
    # that fails forever rather than one that catches anything.
    for mk in PATH_OPENED_MARKERS:
        cases.append((f"the bucket's sentence loses {mk!r}",
                      po, doc_po.replace(mk, ""), True))

    # And the partition itself. `path_opened` is inside the five buckets that exhaust
    # `verified_tspins`, so an artifact where they do not add up must not render at all: 「其餘」
    # is a remainder, and printing one computed from four of five buckets is how this bucket
    # would have been dropped silently. Expects a RAISE, not merely a rejection: see
    # `_broken_partition` for the measurement that distinguishes the two.
    cases.append(("the buckets do not partition the denominator",
                  _broken_partition(data), doc, "raise"))

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
        # `must_fail` is False (must accept), True (must report problems) or "raise" (the input is
        # incoherent and the section must refuse to render it). The third is its own outcome and
        # not a kind of the second: an assert that has been deleted leaves the input rendering
        # perfectly well, so a case that accepted "rejected OR raised" would be satisfied by the
        # difference the deleted assert no longer catches.
        try:
            failed, raised = bool(problems(d, dc)), False
        except ValueError:
            failed, raised = True, True
        want = {False: "acceptance", True: "rejection", "raise": "a refusal to render"}[must_fail]
        good = raised if must_fail == "raise" else (failed == must_fail and not raised)
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: "
              f"{'raised' if raised else 'rejected' if failed else 'accepted'}"
              f"{'' if good else '  <- expected ' + want}")
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

"""Generate the derived parts of a session's report.html.

    python3 -m pipeline.build_report sessions/2026-07-24/report
    python3 -m pipeline.build_report sessions/2026-07-24/report --check

The report is part generated, part hand-written Cantonese prose. This writes only
the generated parts, each inside its own marker region (see `pipeline/region.py`),
so it is idempotent and safe to re-run over a report someone has edited around.

Sections handled so far:

  hero         the eyebrow, headline, scoreboard and lede. Numbers (date, names,
               series score) come from facts.json; the Cantonese comes from
               `<report_dir>/prose/hero.json`.
  chart-data   the JSON island every chart reads — per-match scoreboard, the VS
               small multiples, clear-type bars, the tape chart, match boundaries.

`--check` regenerates in memory and exits non-zero if the committed report differs,
which is what CI runs: the report and facts.json cannot drift apart unnoticed.
"""
import argparse
import json
import os
import sys

from pipeline import (appendix, chart_data, claim_cards, coaching, forecast_section, hero,
                      intense_round, matches, moments, opener_section, pc_section, records, region,
                      stats_section)
from pipeline.claims import generators


def chart_section(ctx):
    blob = json.dumps(chart_data.build(ctx["facts"]), ensure_ascii=False,
                      separators=(",", ":"))
    return ('<script type="application/json" id="chart-data">\n'
            f"{blob}\n"
            "</script>")


def hero_section(ctx):
    return hero.build(ctx["facts"], hero.load_prose(ctx["report_dir"]),
                      ctx["report_dir"])


def match_copy_section(ctx):
    return matches.build(ctx["facts"],
                         matches.load_prose(ctx["report_dir"], ctx["facts"]))


def matches_section(ctx):
    return matches.section(ctx["facts"],
                           matches.load_prose(ctx["report_dir"], ctx["facts"]))


def stats_sec(ctx):
    return stats_section.build(ctx["facts"],
                               stats_section.load_prose(ctx["report_dir"]))


def moments_section(ctx):
    return moments.build(ctx["facts"], moments.load_prose(ctx["report_dir"]))


def coaching_section(ctx):
    # Takes facts like matches.py's loader does — it validates that the prose has a
    # column for each player rather than trusting the file to name them right.
    return coaching.build(ctx["facts"],
                          coaching.load_prose(ctx["report_dir"], ctx["facts"]))


def records_section(ctx):
    return records.build(ctx["facts"], ctx["report_dir"])


def intense_sec(ctx):
    """最癲一局 — the highest-combined-VS round, deep-dived. None when the session has
    no qualifying round, or no `intense_round_*` claims to read the figures out of."""
    return intense_round.build(ctx["facts"], ctx["report_dir"])


def pc_sec(ctx):
    # Built from the session's own claims, like records_section — so the figures are the
    # proved ones. Returns None for a session with no Perfect Clear (no claims, no
    # section) rather than a table of zeroes, which would read as a measured result.
    return pc_section.build(ctx["facts"], ctx["report_dir"])


def appendix_section(ctx):
    return appendix.section(ctx["facts"], ctx["report_dir"])


def forecast_sec(ctx):
    # Sourced from the SESSION's sim/forecast-facts.json, not facts.json — see the module
    # docstring. Quarantined from the claims pipeline on purpose: one simulator, no second
    # independent implementation, so the dual-extractor trust argument does not cover it.
    # Returns None for a session with no such file, and render() then skips the region
    # entirely rather than writing an empty one.
    return forecast_section.section(forecast_section.load(ctx["report_dir"]))


def opener_sec(ctx):
    # Same quarantine as forecast_sec, same source discipline: the SESSION's
    # sim/opener-facts.json, never facts.json. Returns None for a session with no such file.
    return opener_section.section(opener_section.load(ctx["report_dir"]))


def claims_island(ctx):
    return appendix.island(ctx["report_dir"])


# (name, anchor to insert before when the region is absent, builder, markers)
# `markers` is None unless a region predates this module and owns a different
# comment pair — the claims island does, and anything that finds it by name
# (check_prose_figures skips it) keeps working because it kept them.
#
# Order is document order for a report being built from nothing: hero, records
# before the coaching section, appendix before the footer, then the islands.
SECTIONS = [
    ("hero", '<!-- BEGIN generated matches', hero_section, None),
    ("matches", '<!-- BEGIN generated stats', matches_section, None),
    ("stats", '<!-- BEGIN generated moments', stats_sec, None),
    ("moments", '<!-- BEGIN generated records', moments_section, None),
    ("records", '<section id="coaching">', records_section, None),
    # after the records grid: 全消 is a record-shaped number whose point is the
    # column NEXT to it, so it reads as a correction to the tile above rather than
    # a fresh headline.
    #
    # Anchored on the coaching region's BEGIN MARKER, not on `<section id="coaching">`.
    # That section tag lives INSIDE the coaching region, so inserting before it puts the
    # new block inside a region a later pass rewrites — build_report then reports
    # "inserted: perfect-clear" and the finished file contains nothing, because coaching
    # replaced the span the block had just been placed in. Anchor on a marker, which is
    # by definition outside every other region.
    # 最癲一局 sits between the records grid and 全消: both are round-level blocks, and
    # this one explains a single round where 全場之最 ranks every round on one column.
    # Anchored on the 全消 region's BEGIN marker — a marker comment, never a
    # `<section id=...>` tag, which would put it inside a span a later pass rewrites.
    #
    # A CHAIN, because 全消 is itself conditional and self-inserting. Anchoring on it
    # alone is right only for a report that already carries it, and 2026-08-19 — the
    # first session built from a fresh skeleton since 最癲一局 shipped — is where that
    # broke: neither region existed yet, this one is processed first, and the build
    # died on a missing anchor. Every earlier report had 全消 in it before 最癲一局 was
    # ever written, so the ordering was never exercised. The coaching marker is the
    # fallback because the SKELETON always emits it, and falling back to it still
    # yields document order — this block inserts before coaching, then 全消 inserts
    # before coaching too and lands between them. A session with an intense round and
    # NO All Clear needs the fallback permanently, not just on the first build.
    ("intense-round", ('<!-- BEGIN generated perfect-clear',
                       '<!-- BEGIN generated coaching'), intense_sec, None),
    ("perfect-clear", '<!-- BEGIN generated coaching', pc_sec, None),
    ("coaching", '<section id="rounds">', coaching_section, None),
    ("appendix", '<footer class="report-footer">', appendix_section, None),
    # after the proof appendix, so a reader meets the trust chain before the thing
    # that is explicitly outside it
    ("forecast", '<footer class="report-footer">', forecast_sec, None),
    # after the forecast section, so the two quarantined sections sit together below the
    # trust chain rather than one of them being stranded among the proved ones
    ("openers", '<footer class="report-footer">', opener_sec, None),
    ("chart-data", "<!-- CLAIMS_DATA_START -->", chart_section, None),
    ("match-copy", "<!-- CLAIMS_DATA_START -->", match_copy_section, None),
    ("claims-data", '<footer class="report-footer">', claims_island,
     (appendix.ISLAND_START, appendix.ISLAND_END)),
]


def render(html, ctx):
    """Apply every generated section to `html`. Returns (html, [(name, how)])."""
    applied = []
    for name, anchor, build, markers in SECTIONS:
        body = build(ctx)
        start, end = markers or region.markers(name, "pipeline/build_report.py")
        if body is None:
            # The section does not apply to this session — so it must not be SITTING there. Skipping
            # silently is how a region goes stale and survives `--check`: the builder produces
            # nothing, `render` leaves the committed markup alone, the document is unchanged and the
            # drift gate reports agreement. That reads as "still true" and is really "no longer
            # generated". The forecast and opener sections have their own gates that assert this;
            # doing it here covers every section, including the ones that do not.
            if start in html:
                raise SystemExit(
                    f"{name}: this session generates no such section, but report.html still "
                    f"contains its region. Delete the {start!r}…{end!r} block — leaving it would "
                    "publish numbers nothing regenerates.")
            continue
        html, how = region.replace(html, start, end, body, anchor)
        applied.append((name, how))
    return html, applied


def _selftest(report_dir):
    """The two failures that pass `--check` unless something refuses them.

    Both are silent by nature — one leaves a region nothing regenerates, the other drops a row from
    a table that still looks complete — so each guard gets a planted defect proving it fires. A
    guard no mutation can kill is decorative, which is the rule the .dfy lemmas are held to and
    there is no reason a generator should be held to less.
    """
    with open(os.path.join(report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    ctx = {"facts": facts, "report_dir": report_dir}
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()

    cases, ok = [], True

    # 1. a builder that stops producing its section while the region is still committed
    saved = SECTIONS[:]
    try:
        for i, (name, anchor, _build, markers) in enumerate(saved):
            start, _ = markers or region.markers(name, "pipeline/build_report.py")
            if start not in doc:
                continue
            SECTIONS[i] = (name, anchor, lambda _ctx: None, markers)
            try:
                render(doc, ctx)
                cases.append((f"{name} stops generating but its region stays", False))
            except SystemExit:
                cases.append((f"{name} stops generating but its region stays", True))
            finally:
                SECTIONS[i] = saved[i]
    finally:
        SECTIONS[:] = saved

    # 2. a perfect-clear claim whose spec no longer has the shape the section reads
    claims = claim_cards.load(report_dir)
    if any(c["family"] == "pc_rounds" for c in claims):
        real = claim_cards.load

        def blinded(rd, *a, **k):
            out = real(rd, *a, **k)
            for c in out:
                if c["family"] == "pc_rounds":
                    c["spec"] = {"p": "and", "xs": []}      # readable JSON, unreadable shape
                    break
            return out

        claim_cards.load = blinded
        try:
            pc_section.build(facts, report_dir)
            cases.append(("a pc_rounds claim's spec changes shape", False))
        except SystemExit:
            cases.append(("a pc_rounds claim's spec changes shape", True))
        finally:
            claim_cards.load = real
    else:
        print("  --  no pc_rounds claim in this session; its guard is not exercised here")

    # 3. the ledger and generators.INTENSE_AXES disagree about which columns were compared.
    # 最癲一局 counts AXES, so a column the axis map names but the claim never proved would
    # silently drop out of that count — the plausible default ("level") is exactly the `?? 0`
    # shape this repo has shipped before. intense_round._dir refuses instead, and this is
    # what proves it refuses.
    if any(c["family"] == "intense_round_edges" for c in claims):
        real = claim_cards.load
        dropped = generators.INTENSE_AXES[0][1][0][0]

        def unproved(rd, *a, **k):
            out = real(rd, *a, **k)
            for c in out:
                if c["family"] == "intense_round_edges":
                    c["spec"] = {"p": "and", "xs": [
                        x for x in c["spec"]["xs"]
                        if (x.get("a") or {}).get("f") != dropped]}
                    break
            return out

        claim_cards.load = unproved
        try:
            intense_round.build(facts, report_dir)
            cases.append((f"intense_round_edges stops proving {dropped}", False))
        except SystemExit:
            cases.append((f"intense_round_edges stops proving {dropped}", True))
        finally:
            claim_cards.load = real
    else:
        print("  --  no intense_round_edges claim in this session; its guard is not "
              "exercised here")

    for name, caught in cases:
        ok &= caught
        print(f"  {'ok ' if caught else 'BAD'} {name}: {'rejected' if caught else 'ACCEPTED'}")
    print(f"{'ok ' if ok else 'FAIL'} selftest {len(cases)} planted defects, "
          f"{'all caught' if ok else 'SOME MISSED'}")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir", help="a session's report/ directory")
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 1 if the committed report differs")
    ap.add_argument("--selftest", action="store_true",
                    help="plant the defects the guards exist for and require each to be caught")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest(args.report_dir)

    with open(os.path.join(args.report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    ctx = {"facts": facts, "report_dir": args.report_dir}
    report_path = os.path.join(args.report_dir, "report.html")
    with open(report_path, encoding="utf-8") as fh:
        before = fh.read()

    after, applied = render(before, ctx)

    if args.check:
        if after != before:
            print(f"DRIFT: {report_path} differs from what facts.json generates "
                  f"({', '.join(n for n, _ in applied)}) — run "
                  f"`python3 -m pipeline.build_report {args.report_dir}`", file=sys.stderr)
            return 1
        print(f"ok  {report_path} — generated sections match facts.json "
              f"({', '.join(n for n, _ in applied)})")
        return 0

    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(after)
    for name, how in applied:
        print(f"{how}: {name} -> {report_path}")
    # Re-running must be a no-op; proving it here costs nothing and is the whole
    # reason the sections are marker-scoped.
    again, _ = render(after, ctx)
    if again != after:
        print("BUG: build_report is not idempotent", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

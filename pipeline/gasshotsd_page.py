"""合掌TSDパフェ 全路線 — the Gassho TSD route pages: one overview and the constructed demo page.

There is no per-branch page and no bag-1-only page: no corpus round reaches bag 1
(`gasshotsd.test.ts` pins the empty case list), and a node page with no case is refused by the
shared renderer rather than rendered empty. The day a round matches, that page is added with the case.

    python3 -m pipeline.gasshotsd_page --out-dir /tmp/gh   # render every page into a directory
    python3 -m pipeline.gasshotsd_page --selftest          # the audit's mutants

The renderer and every audit rule are the shared `route_page.py`. This file is Gassho TSD's
`RouteSiteProfile`. Its words are `gasshotsd_prose.json`.

NO FLAG and NO HOLD, as stick spin: harddrop's opener transcription draws no Gassho field, and
nothing on the page asserts a held piece in our own words (the source's ホールド stays inside the
quoted sentence). Second-shade letters and the muted `C` are this page's cells.

Inputs, all committed: `pipeline/openers/gasshotsd-routes.json` (transcribed and gated by
`extract_gasshotsd_routes`), `analysis/gasshotsd-facts.json` (`emit-route-facts.ts --opener
gasshotsd`), `analysis/gasshotsd-demos.json` (`emit-route-demos.ts --opener gasshotsd`), and each
session's `sim/replay-facts.json` + `report/facts.json`.
"""
import os

from pipeline.route_page import HERE, RouteSite, RouteSiteProfile

#: second shade (a later piece of the same letter) and the muted grey of a row the TSD clears
GASSHOTSD_CSS = """
  .scb-cm { fill: var(--muted); opacity: .45; }
  .scb-i2 { fill: #00b7ff; opacity: .55; } .scb-o2 { fill: #eeee00; opacity: .55; }
  .scb-j2 { fill: #0011ff; opacity: .55; } .scb-l2 { fill: #ff7b00; opacity: .55; }
  .scb-s2 { fill: #33ff00; opacity: .55; } .scb-z2 { fill: #ff0000; opacity: .55; }
  .scb-t2 { fill: #8400ff; opacity: .55; }
"""

GASSHOTSD_SITE = RouteSiteProfile(
    module="gasshotsd_page",
    prefix="gasshotsd",
    routes_rel=os.path.join("pipeline", "openers", "gasshotsd-routes.json"),
    facts_rel=os.path.join("analysis", "gasshotsd-facts.json"),
    demos_rel=os.path.join("analysis", "gasshotsd-demos.json"),
    prose_path=os.path.join(HERE, "gasshotsd_prose.json"),
    routes_schema="gasshotsd-routes/1",
    facts_schema="gasshotsd-facts/1",
    demos_schema="gasshotsd-demos/1",
    page_schema="gasshotsd-page/1",
    # no corpus case, so no node page: render_node_page refuses a page with no cases
    node_pages=(),
    bag1_order=("bag1.left", "bag1.right", "bag1.i_early"),
    bag2_order=("2.zjo", "2.slo", "2.donate.a", "2.donate.b", "2.stsd", "2.ren"),
    bag2_extra=("2.tsd", "2.tsd.after", "2.zjo.after", "2.slo.after", "2.oz", "2.oz.after", "2.holdi",
                "2.flat", "2.flat.after"),
    bag3_parents=("2.tsd", "2.preplace", "2.oz", "2.holdi", "2.donate", "2.stsd", "2.ren"),
    hold_node=None,
    hold_piece="T",
    hold_heading_key="",
    flag_field=None,
    harddrop_key=None,
    flag_prose="bag1_counts",
    bag1_quote_keys=("requires_verbatim", "no_hold_verbatim", "side_verbatim"),
    overview_nodes=("overview.diagram", "refs.commented"),
    overview_quote_ids=("overview.intro", "2.pc4", "2.zjo"),
    derived_after="bag1.right",
    bag2_lock=9,
    pc_lines=4,
    cell_classes={"C": "cm", "h": "i2", "n": "o2", "k": "j2", "m": "l2", "r": "s2", "y": "z2", "u": "t2"},
    extra_css=GASSHOTSD_CSS,
    max_page_bytes=3_000_000,
    near_lists=(("subset", "bag2_none_tsd_before_complete"), ("superset", "bag2_none_extra_piece"),
                ("moved", "bag2_none_moved_piece"), ("unexplained", "bag2_none_unexplained"),
                ("stripped", "bag2_garbage_stripped")),
    selftest_targets={
        "empty_node": "2.zjo", "text_only": "refs.commented",
        "unmatchable": "2.flat", "elsewhere_node": "bag1.i_early",
        "demo_built": "bag1.left", "demo_unbuilt": "bag1.right",
        "demo_never_holds": "bag1.left", "demo_missing": "bag1.left",
    },
)

SITE = RouteSite(GASSHOTSD_SITE)
OVERVIEW = SITE.OVERVIEW
DEMO_PAGE = SITE.DEMO_PAGE
PROSE = SITE.PROSE
load_inputs = SITE.load_inputs
load_demos = SITE.load_demos
render_all = SITE.render_all
audit_all = SITE.audit_all


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

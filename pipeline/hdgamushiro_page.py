"""ガムシロ積み（harddrop 版）— harddrop's Gamushiro Stacking page as route pages: one overview, the
bag-1-only page and the constructed demo page. The same opener as `gamushiro_page.py` (shiwehi.com's
page), drawn by another site: harddrop draws the second bag as five forms (A1 and A2 one occupancy, B,
C, D) and an 8-line Perfect Clear list under each of A, B and C, which shiwehi.com draws only for its
two 通常 forms. The two pages link each other.

    python3 -m pipeline.hdgamushiro_page --out-dir /tmp/hg   # render every page into a directory
    python3 -m pipeline.hdgamushiro_page --selftest          # the audit's mutants

The renderer and every audit rule are the shared `route_page.py`; this file is the page's
`RouteSiteProfile`, its words `hdgamushiro_prose.json`. No shared code changed for it: the source
credit is SDPC Spin's `source_credit` branch (harddrop publishes no licence), the hold split
山岳積み2号's, and no flag (no 六個具名定式 column draws this opener).

Inputs, all committed: `pipeline/openers/hdgamushiro-routes.json` (transcribed and gated by
`extract_hdgamushiro_routes`, whose cross-source is shiwehi.com's committed transcription),
`analysis/hdgamushiro-facts.json`, `analysis/hdgamushiro-demos.json`, and each session's
`sim/replay-facts.json` + `report/facts.json`.
"""
import os

from pipeline.route_page import HERE, RouteSite, RouteSiteProfile

#: the bag-1 L, held and placed in bag 2: muted l, outlined (山岳積み2号's, ガムシロ積み's)
HDGAMUSHIRO_CSS = """
  .scb-lm { fill: #d8904d; stroke: var(--ink); stroke-width: 1.5; }
"""

HDGAMUSHIRO_SITE = RouteSiteProfile(
    module="hdgamushiro_page",
    prefix="hdgamushiro",
    routes_rel=os.path.join("pipeline", "openers", "hdgamushiro-routes.json"),
    facts_rel=os.path.join("analysis", "hdgamushiro-facts.json"),
    demos_rel=os.path.join("analysis", "hdgamushiro-demos.json"),
    prose_path=os.path.join(HERE, "hdgamushiro_prose.json"),
    routes_schema="hdgamushiro-routes/1",
    facts_schema="hdgamushiro-facts/1",
    demos_schema="hdgamushiro-demos/1",
    page_schema="hdgamushiro-page/1",
    node_pages=(("bag1-only", None),),
    bag1_order=("bag1.l_top", "bag1.left", "bag1.right", "bag1.l_top_right", "bag1.l_placed_elsewhere"),
    bag2_order=("2.a1", "2.a2", "2.b", "2.c"),
    # Form D is a branch but not measured (ten rows tall): drawn among the extras with its reason
    bag2_extra=("2.d", "2.a.redraw", "2.a.after", "2.b.redraw", "2.b.after", "2.c.redraw", "2.c.after"),
    bag3_parents=("2.a", "2.b", "2.c"),
    hold_node="bag1.left",
    hold_piece="L",
    hold_heading_key="l_hold_heading",
    flag_field=None,
    harddrop_key=None,
    flag_prose="bag1_counts",
    bag1_quote_keys=("requires_verbatim", "seven_verbatim"),
    overview_nodes=(),
    overview_quote_ids=("overview.intro", "overview.bag1", "2.forms", "3.pc"),
    derived_after="bag1.right",
    bag2_lock=12,
    pc_lines=8,
    cell_classes={"L": "lm"},
    extra_css=HDGAMUSHIRO_CSS,
    see_also=("gamushiro.html", "see_also"),
    max_page_bytes=3_000_000,
    near_lists=(("subset", "bag2_none_tst_before_complete"), ("superset", "bag2_none_extra_piece"),
                ("moved", "bag2_none_moved_piece"), ("unexplained", "bag2_none_unexplained"),
                ("stripped", "bag2_garbage_stripped")),
    selftest_targets={
        "empty_node": "2.b", "text_only": "2.a.pc.rest",
        "unmatchable": "2.d", "node_page": "bag1-only", "node_page_node": "bag1.l_top",
        "elsewhere_node": "bag1.l_placed_elsewhere", "demo_built": "2.a.pc#1",
        "demo_unbuilt": "2.b.after", "demo_never_holds": "bag1.l_top",
        "demo_missing": "2.c.pc#5",
    },
)

SITE = RouteSite(HDGAMUSHIRO_SITE)
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

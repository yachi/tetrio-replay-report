"""SDPC Spin 全路線 — the SDPC Spin route pages: one overview, the bag-1-only page, one page for the
rounds that reached bag 2's TSD (the source draws one bag-2 board, so there is one bag-2 page), and
the constructed demo page.

    python3 -m pipeline.sdpcspin_page --out-dir /tmp/sd   # render every page into a directory
    python3 -m pipeline.sdpcspin_page --selftest          # the audit's mutants

The renderer and every audit rule are the shared `route_page.py` (read its header: inputs, pages,
quarantine, figures), the same code 迷走砲, はちみつ砲, 山岳積み2号, stick spin and ガムシロ積み bind;
this file is SDPC Spin's `RouteSiteProfile`. Its words are `sdpcspin_prose.json`.

THE FIRST ROUTE PAGE NOT FROM shiwehi.com. The source is harddrop's SDPC_Spin page (Ecchou's opener,
read as wikitext), and harddrop publishes no licence, so the header's credit comes from the prose's
`source_credit` (the shared default is shiwehi.com's terms). Bag 1 has a second source — harddrop's
SDPC page, `cross_source` in the routes JSON — and nothing from bag 2 on does: the page says so in a
REQUIRED sentence (`page_sentences.source`), so every page carries it.

What this page needs, each a profile switch or a generic branch in the shared renderer that leaves
the other five openers' bytes alone:

* NO FLAG and NO HOLD, as stick spin: no 六個具名定式 column draws SDPC Spin, and nothing on the page
  asserts a hold. The source's own transition board says 「hold O and tuck it」; it is quoted text,
  which the shared 「hold」 rule now exempts exactly as the % rule always did.
* A DEEP TREE. `bag3_parents` places by id prefix, so the three bag-3 builds (children of `2.tsd`
  whose ids do not start with it) are parents of their own: everything from bag 3 to bag 6 is drawn
  under 第三巡, and the prose says so.
* An `at_least` condition (the STMB Cave's 「J before at least two of T, L and Z」), a branch the
  shared condition reader now has.
* Muted letters: the DT Cannon boards draw the C-Spin's residue in upper case, and the 「Z too early」
  board marks the Z's usual cells (`v`).

Inputs, all committed: `pipeline/openers/sdpcspin-routes.json` (transcribed and gated by
`extract_sdpcspin_routes`), `analysis/sdpcspin-facts.json` (`emit-route-facts.ts --opener
sdpcspin`), `analysis/sdpcspin-demos.json` (`emit-route-demos.ts --opener sdpcspin`), and each
session's `sim/replay-facts.json` + `report/facts.json`.
"""
import os

from pipeline.route_page import HERE, RouteSite, RouteSiteProfile

#: the cells only this page draws: the C-Spin's residue the DT Cannon boards draw in upper case
#: (muted piece colours), and the Z's usual cells the 「Z too early」 board marks (`v`, outlined)
SDPCSPIN_CSS = """
  .scb-jm { fill: #4d57d8; opacity: .55; } .scb-lm { fill: #d8904d; opacity: .55; }
  .scb-om { fill: #cfcf4d; opacity: .55; } .scb-sm { fill: #69d24d; opacity: .55; }
  .scb-zm { fill: #d84d4d; opacity: .55; }
  .scb-zv { fill: none; stroke: #d64f4a; stroke-width: 1.5; stroke-dasharray: 2 2; }
"""

SDPCSPIN_SITE = RouteSiteProfile(
    module="sdpcspin_page",
    prefix="sdpcspin",
    routes_rel=os.path.join("pipeline", "openers", "sdpcspin-routes.json"),
    facts_rel=os.path.join("analysis", "sdpcspin-facts.json"),
    demos_rel=os.path.join("analysis", "sdpcspin-demos.json"),
    prose_path=os.path.join(HERE, "sdpcspin_prose.json"),
    routes_schema="sdpcspin-routes/1",
    facts_schema="sdpcspin-facts/1",
    demos_schema="sdpcspin-demos/1",
    page_schema="sdpcspin-page/1",
    node_pages=(("tsd", "2.tsd"), ("bag1-only", None)),
    bag1_order=("bag1.jl", "bag1.lj", "bag1.jl.left", "bag1.lj.left", "bag1.after"),
    bag2_order=("2.tsd",),
    bag2_extra=("2.after",),
    # by id prefix: the three bag-3 builds hang off 2.tsd, everything after them off their own ids
    bag3_parents=("2.tsd", "3.first", "3.second", "3.third"),
    hold_node=None,
    hold_piece="T",
    hold_heading_key="",
    flag_field=None,
    harddrop_key=None,
    flag_prose="bag1_counts",
    bag1_quote_keys=("sdpc_verbatim",),
    overview_nodes=(),
    overview_quote_ids=("overview.intro", "bag3.ways", "bag3.center"),
    derived_after="bag1.jl",
    bag2_lock=12,
    pc_lines=8,
    cell_classes={"J": "jm", "L": "lm", "O": "om", "S": "sm", "Z": "zm", "v": "zv"},
    extra_css=SDPCSPIN_CSS,
    max_page_bytes=3_000_000,
    near_lists=(("subset", "bag2_none_tsd_before_complete"), ("superset", "bag2_none_extra_piece"),
                ("moved", "bag2_none_moved_piece"), ("unexplained", "bag2_none_unexplained"),
                ("stripped", "bag2_garbage_stripped")),
    selftest_targets={
        "empty_node": "3.third.imperial", "text_only": "3.first.trinity.donate",
        "unmatchable": "3.first.cave.stsd", "node_page": "tsd", "node_page_node": "2.tsd",
        "elsewhere_node": "bag1.jl.left", "demo_built": "3.third.imperial.pc#1",
        "demo_unbuilt": "3.second.cspin.z_early", "demo_never_holds": "bag1.jl",
        "demo_missing": "3.first", "demo_spin_last": ("bag1.jl", "bag1.lj", "2.tsd"),
        # a T fired before named pieces (`u_before:`): its U lock moved to the end must fail
        "demo_u_before": ("3.second.cspin", "3.second.cspin.o_first#1", "3.third.transition#2"),
    },
)

SITE = RouteSite(SDPCSPIN_SITE)
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

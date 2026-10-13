"""ガムシロ積み 全路線 — the Gamushiro Stacking route pages: one overview, the bag-1-only page and the
constructed demo page. There is no page per bag-2 branch because no corpus round reaches one: the
corpus holds very few Gamushiro bag 1s at all (`gamushiro.test.ts` pins them by name), and a node
page with no case is refused by the shared renderer rather than rendered empty — stick spin's
precedent, decided from the artefact, not assumed.

    python3 -m pipeline.gamushiro_page --out-dir /tmp/gm   # render every page into a directory
    python3 -m pipeline.gamushiro_page --selftest          # the audit's mutants

The renderer and every audit rule are the shared `route_page.py` (read its header: inputs, pages,
quarantine, figures), the same code 迷走砲, はちみつ砲, 山岳積み2号 and stick spin bind; this file is
ガムシロ積み's `RouteSiteProfile`. Its words are `gamushiro_prose.json`.

A REFERENCE OPENER. Unlike the other four, this page is not here because the corpus's two players
play it: they barely do, and the overview says so with the count read off the artefact. It is here
because shiwehi.com's own survey of strong Puyo Puyo Tetris 2 players' openers names it the most-used
opener of a 2024 tournament winner; the routes JSON's `source.why_this_opener` records that page's
provenance and its own caveat about the sample, and the prose cites no more than it says.

What this page combines, each an existing profile switch (no shared code changed for it):

* 山岳積み2号's HOLD SPLIT with stick spin's NO FLAG: `bag1.left` (the L-held six-lock board) is the
  one node that earns 「hold」; harddrop's opener transcription draws no Gamushiro field, so there is
  no 六個具名定式 column (`flag_field=None`, `harddrop_key=None`) and the bag-1 sentence is formatted
  with the bag-1 nodes' own counts, naming the cross-check that replaces the flag (the ordering
  metric, in `gamushiro.test.ts`).
* the muted upper-case cells the source draws: `L` the held bag-1 L, `C` the rows a TST clears.
* the near-miss lists named after the TST, plus `unexplained`, which is where its one bag-2
  comparison lands.

Inputs, all committed: `pipeline/openers/gamushiro-routes.json` (transcribed and gated by
`extract_gamushiro_routes`), `analysis/gamushiro-facts.json` (`emit-route-facts.ts --opener
gamushiro`), `analysis/gamushiro-demos.json` (`emit-route-demos.ts --opener gamushiro`), and each
session's `sim/replay-facts.json` + `report/facts.json`.
"""
import os

from pipeline.route_page import HERE, RouteSite, RouteSiteProfile

#: the cells only this page draws: the bag-1 L, held and placed in bag 2 (muted l, outlined, as
#: 山岳積み2号), and the source's light grey in the rows a TST clears
GAMUSHIRO_CSS = """
  .scb-lm { fill: #d8904d; stroke: var(--ink); stroke-width: 1.5; }
  .scb-cl { fill: var(--muted); opacity: .3; }
"""

GAMUSHIRO_SITE = RouteSiteProfile(
    module="gamushiro_page",
    prefix="gamushiro",
    routes_rel=os.path.join("pipeline", "openers", "gamushiro-routes.json"),
    facts_rel=os.path.join("analysis", "gamushiro-facts.json"),
    demos_rel=os.path.join("analysis", "gamushiro-demos.json"),
    prose_path=os.path.join(HERE, "gamushiro_prose.json"),
    routes_schema="gamushiro-routes/1",
    facts_schema="gamushiro-facts/1",
    demos_schema="gamushiro-demos/1",
    page_schema="gamushiro-page/1",
    node_pages=(("bag1-only", None),),
    bag1_order=("bag1.l_top", "bag1.left", "bag1.right", "bag1.l_placed_elsewhere"),
    bag2_order=("2.normal#1", "2.normal#2"),
    # 2.compromise is a branch but not measured (ten rows tall): `bag2_order` reads every node's case
    # count, so it is drawn among the extras, after the measured branches, with its reason
    bag2_extra=("2.compromise", "2.pc4#1", "2.pc4#2", "2.pc4#3", "2.normal.tst", "2.compromise.tst"),
    bag3_parents=("2.normal",),
    hold_node="bag1.left",
    hold_piece="L",
    hold_heading_key="l_hold_heading",
    flag_field=None,
    harddrop_key=None,
    flag_prose="bag1_counts",
    bag1_quote_keys=("requires_verbatim", "hold_verbatim", "no_hold_verbatim", "side_verbatim"),
    overview_nodes=(),
    overview_quote_ids=("overview.intro", "overview.pc4_rare", "overview.mountainous2"),
    derived_after="bag1.right",
    bag2_lock=12,
    pc_lines=8,
    cell_classes={"L": "lm", "C": "cl"},
    extra_css=GAMUSHIRO_CSS,
    max_page_bytes=3_000_000,
    near_lists=(("subset", "bag2_none_tst_before_complete"), ("superset", "bag2_none_extra_piece"),
                ("moved", "bag2_none_moved_piece"), ("unexplained", "bag2_none_unexplained"),
                ("stripped", "bag2_garbage_stripped")),
    selftest_targets={
        "empty_node": "2.normal#2", "text_only": "2.normal.tst",
        "unmatchable": "2.compromise", "node_page": "bag1-only", "node_page_node": "bag1.l_top",
        "elsewhere_node": "bag1.l_placed_elsewhere", "demo_built": "2.normal.pc#1",
        "demo_unbuilt": "2.compromise", "demo_never_holds": "bag1.l_top",
        "demo_missing": "2.normal.pc#5",
    },
)

SITE = RouteSite(GAMUSHIRO_SITE)
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

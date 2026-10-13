"""山岳積み2号 全路線 — the Mountainous Stacking 2 route pages: one overview, one replay page per
bag-2 branch (the three 通常形 forms share one page, as they share one group on the source page),
the bag-1-only page and the constructed demo page.

    python3 -m pipeline.mountainous2_page --out-dir /tmp/ms2   # render every page into a directory
    python3 -m pipeline.mountainous2_page --selftest           # the audit's mutants

The renderer and every audit rule are the shared `route_page.py` (read its header: inputs, pages,
quarantine, figures), the same code 迷走砲's `stray_cannon_page.py` and はちみつ砲's
`honey_cup_page.py` bind; this file is 山岳積み2号's `RouteSiteProfile` — its file names, schemas,
node orders, the node that earns 「hold」, the board letter only this page draws (the bag-1 L held
into bag 2, upper-case `L`) and the targets its selftest plants into. Its words are
`mountainous2_prose.json`.

Two things this page has that the other two do not, both carried by the shared renderer without a
profile switch: a Perfect Clear list drawn in BAG 2 (`2.pc4`, 4 lines, on the L-held bag-1 board),
which the overview draws under 第二巡 through `bag2_extra`; and lists whose line count is not the
profile's `pc_lines` (`2.pc4` 4, the 5巡パフェ 14), read from the transcription's own `pc_lines` /
`total_lines`.

Inputs, all committed: `pipeline/openers/mountainous2-routes.json` (the shiwehi.com page,
transcribed and gated by `extract_mountainous2_routes`), `analysis/mountainous2-facts.json` (which
corpus round reached which route node, `pipeline/sim/emit-route-facts.ts --opener mountainous2`),
`analysis/mountainous2-demos.json` (`emit-route-demos.ts --opener mountainous2`), and each session's
`sim/replay-facts.json` + `report/facts.json`.
"""
import os

from pipeline.route_page import HERE, RouteSite, RouteSiteProfile

#: the cell only this page draws. L: the bag-1 L, held and placed in bag 2 (muted l, outlined).
MOUNTAINOUS2_CSS = """
  .scb-lm { fill: #d8904d; stroke: var(--ink); stroke-width: 1.5; }
"""

MOUNTAINOUS2_SITE = RouteSiteProfile(
    module="mountainous2_page",
    prefix="mountainous2",
    routes_rel=os.path.join("pipeline", "openers", "mountainous2-routes.json"),
    facts_rel=os.path.join("analysis", "mountainous2-facts.json"),
    demos_rel=os.path.join("analysis", "mountainous2-demos.json"),
    prose_path=os.path.join(HERE, "mountainous2_prose.json"),
    routes_schema="mountainous2-routes/1",
    facts_schema="mountainous2-facts/1",
    demos_schema="mountainous2-demos/1",
    page_schema="mountainous2-page/1",
    node_pages=(("bag1-only", None), ("ideal", "2.ideal"), ("normal", "2.normal"),
                ("compromise", "2.compromise")),
    bag1_order=("bag1.l_top", "bag1.l_hold", "bag1.j_top", "bag1.l_placed_elsewhere"),
    bag2_order=("2.ideal", "2.normal#1", "2.normal#2", "2.normal#3", "2.compromise"),
    bag2_extra=("2.pc4#1", "2.pc4#2", "2.pc4#3"),
    bag3_parents=("2.ideal", "2.normal", "2.compromise"),
    hold_node="bag1.l_hold",
    hold_piece="L",
    hold_heading_key="l_hold_heading",
    flag_field="matched_harddrop",
    harddrop_key="mountainous_2",
    flag_prose="matched_harddrop",
    bag1_quote_keys=("requires_verbatim", "also_verbatim", "side_verbatim", "mirror_note_verbatim"),
    overview_nodes=("overview.derivation_map", "overview.video"),
    overview_quote_ids=("overview.intro", "overview.pc4_rare", "overview.setup_rate"),
    derived_after="bag1.j_top",
    bag2_lock=12,
    pc_lines=8,
    cell_classes={"L": "lm"},
    extra_css=MOUNTAINOUS2_CSS,
    max_page_bytes=3_000_000,
    selftest_targets={
        "empty_node": "2.normal#2", "text_only": "2.compromise.fire34.cycle1",
        "unmatchable": "2.compromise.fire5.bag4#1", "node_page": "ideal", "node_page_node": "2.ideal.pc#7",
        "elsewhere_node": "bag1.l_placed_elsewhere", "demo_built": "2.ideal.pc#3",
        "demo_unbuilt": "2.ideal.pc#9", "demo_never_holds": "bag1.l_top",
        "demo_missing": "2.compromise.fire5.pc#6",
    },
)

SITE = RouteSite(MOUNTAINOUS2_SITE)
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

"""はちみつ砲 全路線 — the Honey Cup route pages: one overview, one replay page per bag-2 branch
(the five 理想形 forms share one page, as they share one group on the source page), the bag-1-only
page and the constructed demo page.

    python3 -m pipeline.honey_cup_page --out-dir /tmp/hc   # render every page into a directory
    python3 -m pipeline.honey_cup_page --selftest          # the audit's mutants

The renderer and every audit rule are the shared `route_page.py` (read its header: inputs, pages,
quarantine, figures), the same code 迷走砲's `stray_cannon_page.py` binds; this file is はちみつ砲's
`RouteSiteProfile` — its file names, schemas, node orders, the node that earns 「hold」, the board
letters only this page draws (the held J, the cleared-row C, the REN region B) and the targets its
selftest plants into. Its words are `honey_cup_prose.json`.

Inputs, all committed: `pipeline/openers/honeycup-routes.json` (the shiwehi.com page, transcribed
and gated by `extract_honeycup_routes`), `analysis/honey-cup-facts.json` (which corpus round reached
which route node, `pipeline/sim/emit-route-facts.ts --opener honeycup`), `analysis/honey-cup-
demos.json` (`emit-route-demos.ts --opener honeycup`), and each session's `sim/replay-facts.json` +
`report/facts.json`.
"""
import os

from pipeline.route_page import HERE, RouteSite, RouteSiteProfile

#: the cells only this page draws. J: the bag-1 J, held and placed in bag 2 (muted j, outlined).
#: C: a grey cell in a row the drawn spin clears. I/Z: muted i/z inside those rows. B: the REN region.
HONEYCUP_CSS = """
  .scb-jm { fill: #4a72d1; stroke: var(--ink); stroke-width: 1.5; }
  .scb-cl { fill: var(--muted); opacity: .3; }
  .scb-im { fill: #3fb8c4; opacity: .5; } .scb-zm { fill: #d64f4a; opacity: .5; }
  .scb-b { fill: var(--ink); opacity: .7; }
"""

HONEYCUP_SITE = RouteSiteProfile(
    module="honey_cup_page",
    prefix="honey-cup",
    routes_rel=os.path.join("pipeline", "openers", "honeycup-routes.json"),
    facts_rel=os.path.join("analysis", "honey-cup-facts.json"),
    demos_rel=os.path.join("analysis", "honey-cup-demos.json"),
    prose_path=os.path.join(HERE, "honey_cup_prose.json"),
    routes_schema="honeycup-routes/1",
    facts_schema="honey-cup-facts/1",
    demos_schema="honey-cup-demos/1",
    page_schema="honey-cup-page/1",
    node_pages=(("bag1-only", None), ("ideal", "2.ideal"), ("compromise", "2.compromise")),
    bag1_order=("bag1.j_right", "bag1.j_hold", "bag1.l_hold", "bag1.j_placed_elsewhere"),
    bag2_order=("2.ideal#1", "2.ideal#2", "2.ideal#3", "2.ideal#4", "2.ideal#5", "2.compromise"),
    bag2_extra=("2.ideal.tst", "2.ideal.after_tst", "2.compromise.tst"),
    bag3_parents=("2.ideal", "2.compromise"),
    hold_node="bag1.j_hold",
    hold_piece="J",
    hold_heading_key="j_hold_heading",
    flag_field="matched_harddrop",
    harddrop_key="honey_cup",
    flag_prose="matched_harddrop",
    bag1_quote_keys=("requires_verbatim", "side_verbatim", "mirror_note_verbatim"),
    overview_nodes=("overview.derivation_map",),
    overview_quote_ids=("overview.max_damage", "overview.setup_rate"),
    derived_after="bag1.j_hold",
    bag2_lock=12,
    pc_lines=8,
    cell_classes={"J": "jm", "C": "cl", "I": "im", "Z": "zm", "B": "b"},
    extra_css=HONEYCUP_CSS,
    max_page_bytes=3_000_000,
    selftest_targets={
        "empty_node": "2.ideal#1", "text_only": "2.ideal.ren4",
        "unmatchable": "2.ideal.fire.stmb_example", "node_page": "ideal", "node_page_node": "2.ideal.pc#7",
        "elsewhere_node": "bag1.j_placed_elsewhere", "demo_built": "2.ideal.pc#3",
        "demo_unbuilt": "2.compromise.roof.after", "demo_never_holds": "bag1.j_right",
        "demo_missing": "2.ideal.pc#14",
    },
)

SITE = RouteSite(HONEYCUP_SITE)
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

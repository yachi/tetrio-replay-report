"""迷走砲 全路線 — the Stray Cannon route pages: one overview plus one replay page per bag-2 node.

    python3 -m pipeline.stray_cannon_page --out-dir /tmp/sc   # render every page into a directory
    python3 -m pipeline.stray_cannon_page --selftest          # the audit's mutants

A SHIM since the route pages were generalised: the renderer and every audit rule are the shared
`route_page.py` (read its header: inputs, pages, quarantine, figures); this file is 迷走砲's
`RouteSiteProfile` — its file names, schemas, node orders, the node that earns 「hold」 and the
targets its selftest plants into — and the module-level names `bin/build-docs` and CI use. Its words
are `stray_cannon_prose.json`.

Inputs, all committed: `pipeline/openers/meisou-routes.json` (the shiwehi.com page, transcribed and
gated by `extract_meisou_routes`), `analysis/stray-cannon-facts.json` (which corpus round reached
which route node, written by `pipeline/sim/emit-stray-cannon-facts.ts`), `analysis/stray-cannon-
demos.json`, and each session's `sim/replay-facts.json` + `report/facts.json`.
"""
import os

from pipeline.route_page import (HERE, REPO, RouteSite, RouteSiteProfile, case_count, case_key, demo_slug,  # noqa: F401
                                 round_key)

MEISOU_SITE = RouteSiteProfile(
    module="stray_cannon_page",
    prefix="stray-cannon",
    routes_rel=os.path.join("pipeline", "openers", "meisou-routes.json"),
    facts_rel=os.path.join("analysis", "stray-cannon-facts.json"),
    demos_rel=os.path.join("analysis", "stray-cannon-demos.json"),
    prose_path=os.path.join(HERE, "stray_cannon_prose.json"),
    routes_schema="meisou-routes/1",
    facts_schema="stray-cannon-facts/1",
    demos_schema="stray-cannon-demos/1",
    page_schema="stray-cannon-page/1",
    node_pages=(("bag1-only", None), ("ideal", "2.ideal"), ("normal-os", "2.normal_OS"),
                ("normal-so", "2.normal_SO"), ("i-early", "2.i_early")),
    bag1_order=("bag1.z_right", "bag1.z_left", "bag1.z_hold", "bag1.z_placed_elsewhere"),
    bag2_order=("2.ideal", "2.normal_OS", "2.normal_SO", "2.i_early", "2.z_left"),
    bag3_parents=("2.ideal", "2.normal_OS", "2.normal_SO", "2.i_early", "2.z_left"),
    hold_node="bag1.z_hold",
    hold_piece="Z",
    hold_heading_key="z_hold_heading",
    flag_field="matched_at_6",
    harddrop_key="stray_cannon",
    flag_prose="matched_at_6",
    bag1_quote_keys=("requires_verbatim", "z_note_verbatim"),
    overview_nodes=("overview.derivation_map", "overview.video"),
    overview_quote_ids=("overview.max_damage",),
    derived_after="bag1.z_right",
    bag2_lock=12,
    pc_lines=8,
    selftest_targets={
        "empty_node": "2.ideal.pc#7", "text_only": "2.ideal.ren4",
        "unmatchable": "2.ideal.fire.stmb_example", "node_page": "ideal", "node_page_node": "2.ideal.pc#16",
        "elsewhere_node": "bag1.z_placed_elsewhere", "demo_built": "2.ideal.pc#3",
        "demo_unbuilt": "2.z_left.pc#6", "demo_never_holds": "2.ideal", "demo_missing": "2.i_early.pc#4",
    },
)

SITE = RouteSite(MEISOU_SITE)
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

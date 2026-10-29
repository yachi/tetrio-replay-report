"""stick spin（SDパフェ）全路線 — the stick spin route pages: one overview, the bag-1-only page and
the constructed demo page. There is no page per bag-2 branch because no corpus round reaches bag 2:
every case stops at bag 1 (`stickspin.test.ts` says why, round by round), and a node page with no
case is refused by the shared renderer rather than rendered empty.

    python3 -m pipeline.stickspin_page --out-dir /tmp/ss   # render every page into a directory
    python3 -m pipeline.stickspin_page --selftest          # the audit's mutants

The renderer and every audit rule are the shared `route_page.py` (read its header: inputs, pages,
quarantine, figures), the same code 迷走砲, はちみつ砲 and 山岳積み2号 bind; this file is stick
spin's `RouteSiteProfile`. Its words are `stickspin_prose.json`.

Three things this page needs that the other three do not, each a profile switch in the shared
renderer that leaves their bytes alone:

* NO FLAG. harddrop's opener transcription has no stick spin field, so `opener-facts.json` has no
  六個具名定式 column to compare with (`flag_field=None`, `harddrop_key=None`); the bag-1 sentence is
  formatted with the bag-1 nodes' own counts instead, and names the cross-check that replaces the
  flag (Double-first openers against stick-spin bag 1, in `stickspin.test.ts`).
* NO HOLD. Nothing on this page asserts a hold (`hold_node=None`): 「hold」 may appear only in the
  bag-1 sentence, which quotes the page's own no-hold conditions.
* Its own near-miss lists (`near_lists`): named after the TSD, plus the `near` and `unexplained`
  kinds, and the muted upper-case letters the source draws in the rows a spin clears.

Inputs, all committed: `pipeline/openers/stickspin-routes.json` (transcribed and gated by
`extract_stickspin_routes`), `analysis/stickspin-facts.json` (`emit-route-facts.ts --opener
stickspin`), `analysis/stickspin-demos.json` (`emit-route-demos.ts --opener stickspin`), and each
session's `sim/replay-facts.json` + `report/facts.json`.
"""
import os

from pipeline.route_page import HERE, RouteSite, RouteSiteProfile

#: the cells only this page draws: the source's muted upper case, a cell in a row the drawn spin
#: clears (C grey, I J L O S Z the piece), in the renderer's muted colours
STICKSPIN_CSS = """
  .scb-cl { fill: var(--muted); opacity: .3; }
  .scb-im { fill: #4db1d8; opacity: .55; } .scb-jm { fill: #4d57d8; opacity: .55; }
  .scb-lm { fill: #d8904d; opacity: .55; } .scb-om { fill: #cfcf4d; opacity: .55; }
  .scb-sm { fill: #69d24d; opacity: .55; } .scb-zm { fill: #d84d4d; opacity: .55; }
"""

STICKSPIN_SITE = RouteSiteProfile(
    module="stickspin_page",
    prefix="stickspin",
    routes_rel=os.path.join("pipeline", "openers", "stickspin-routes.json"),
    facts_rel=os.path.join("analysis", "stickspin-facts.json"),
    demos_rel=os.path.join("analysis", "stickspin-demos.json"),
    prose_path=os.path.join(HERE, "stickspin_prose.json"),
    routes_schema="stickspin-routes/1",
    facts_schema="stickspin-facts/1",
    demos_schema="stickspin-demos/1",
    page_schema="stickspin-page/1",
    node_pages=(("bag1-only", None),),
    bag1_order=("bag1.pc", "bag1.fire", "bag1.left", "bag1.right"),
    bag2_order=("2.sd", "2.mochi", "2.mochi.i_right", "2.fire#1", "2.fire#2"),
    bag2_extra=("bag1.pc.after", "bag1.fire.after", "2.fire.tsd"),
    bag3_parents=("2.sd", "2.mochi", "2.fire"),
    hold_node=None,
    hold_piece="T",
    hold_heading_key="",
    flag_field=None,
    harddrop_key=None,
    flag_prose="bag1_counts",
    bag1_quote_keys=("requires_verbatim", "no_hold_verbatim", "side_verbatim"),
    overview_nodes=(),
    overview_quote_ids=("overview.intro", "2.sd.intro", "2.mochi.intro"),
    derived_after="bag1.right",
    bag2_lock=12,
    pc_lines=8,
    cell_classes={"C": "cl", "I": "im", "J": "jm", "L": "lm", "O": "om", "S": "sm", "Z": "zm"},
    extra_css=STICKSPIN_CSS,
    max_page_bytes=3_000_000,
    near_lists=(("subset", "bag2_none_tsd_before_complete"), ("superset", "bag2_none_extra_piece"),
                ("moved", "bag2_none_moved_piece"), ("near", "bag2_none_near"),
                ("unexplained", "bag2_none_unexplained"), ("stripped", "bag2_garbage_stripped")),
    selftest_targets={
        "empty_node": "2.sd", "text_only": "2.fire.bag4",
        "unmatchable": "2.fire.td#1", "node_page": "bag1-only", "node_page_node": "bag1.pc",
        "elsewhere_node": "bag1.left", "demo_built": "2.sd.pc#3",
        "demo_unbuilt": "2.sd.tst.spin", "demo_never_holds": "bag1.pc",
        "demo_missing": "2.mochi.pc#6", "demo_spin_last": ("bag1.pc", "bag1.fire", "2.sd.tst"),
    },
)

SITE = RouteSite(STICKSPIN_SITE)
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

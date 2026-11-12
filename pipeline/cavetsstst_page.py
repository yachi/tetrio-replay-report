"""Cave TSS to TST 中盤手法 — harddrop's Cave TSS to TST technique pages: one overview and the constructed demo page.

    python3 -m pipeline.cavetsstst_page --out-dir /tmp/cavetsstst   # render both pages into a directory
    python3 -m pipeline.cavetsstst_page --selftest                  # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs, pages,
quarantine, figures); this file is Cave TSS to TST's `TechniqueSiteProfile`, and its words are
`cavetsstst_prose.json`.

Inputs, all committed: `pipeline/openers/cavetsstst-technique.json` (transcribed and gated by
`extract_cavetsstst_shapes`), `analysis/cavetsstst-facts.json` (`emit-technique-facts.ts --technique cavetsstst`)
and `analysis/cavetsstst-demos.json` (`emit-technique-demos.ts --technique cavetsstst`).

The source is harddrop's T-Spin Triple Setups page (three boards under Garbage Manipulation), so the prose carries
a `source_credit` (King Crimson's precedent). The first technique page whose opportunity is a MINI T-spin: the
engine credits the Cave TSS as a mini T-spin Single, so `opportunity` is the denominators key `mini_TSS` and
`opportunity_word` names it for the demo page. Two letters beyond the route pages': `c`, harddrop's dark grey
(placed before, any piece or garbage) and `q`, its grey (the stack built around the TST slot, filled, no piece).
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

CAVETSSTST_CSS = """
  .scb-qq { fill: var(--muted); opacity: .3; }
"""

PROFILE = TechniqueSiteProfile(
    module="cavetsstst_page",
    prefix="cavetsstst",
    transcription_rel=os.path.join("pipeline", "openers", "cavetsstst-technique.json"),
    facts_rel=os.path.join("analysis", "cavetsstst-facts.json"),
    demos_rel=os.path.join("analysis", "cavetsstst-demos.json"),
    prose_path=os.path.join(HERE, "cavetsstst_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="cavetsstst",
    opportunity="mini_TSS",
    opportunity_word="mini TSS",
    cell_classes={"q": "qq"},
    extra_css=CAVETSSTST_CSS,
    max_page_bytes=1_000_000,
    selftest_board="tss.after",
    corpus_qualified_only=True,
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

"""King Crimson 中盤手法 — harddrop's King Crimson technique pages: one overview and the constructed demo page.

    python3 -m pipeline.kingcrimson_page --out-dir /tmp/kingcrimson   # render both pages into a directory
    python3 -m pipeline.kingcrimson_page --selftest                   # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs, pages,
quarantine, figures); this file is King Crimson's `TechniqueSiteProfile`, and its words are `kingcrimson_prose.json`.

Inputs, all committed: `pipeline/openers/kingcrimson-technique.json` (transcribed and gated by
`extract_kingcrimson_shapes`), `analysis/kingcrimson-facts.json` (`emit-technique-facts.ts --technique kingcrimson`)
and `analysis/kingcrimson-demos.json` (`emit-technique-demos.ts --technique kingcrimson`).

The first technique page whose source is harddrop rather than shiwehi.com (shiwehi.com draws no King Crimson), and
the first whose opportunity is a T-spin TRIPLE, so the prose carries a `source_credit` (SDPC Spin's precedent:
harddrop publishes no licence, every page credits it by link) and `opportunity` is `TST`. The one letter this page
draws beyond the route pages' is `q`, harddrop's light-grey Q: the rest of the stack, filled, no piece (our reading).
`U` keeps the route pages' dashed slot: it is where the T goes.
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

KINGCRIMSON_CSS = """
  .scb-qq { fill: var(--muted); opacity: .3; }
"""

PROFILE = TechniqueSiteProfile(
    module="kingcrimson_page",
    prefix="kingcrimson",
    transcription_rel=os.path.join("pipeline", "openers", "kingcrimson-technique.json"),
    facts_rel=os.path.join("analysis", "kingcrimson-facts.json"),
    demos_rel=os.path.join("analysis", "kingcrimson-demos.json"),
    prose_path=os.path.join(HERE, "kingcrimson_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="kingcrimson",
    opportunity="TST",
    cell_classes={"q": "qq"},
    extra_css=KINGCRIMSON_CSS,
    max_page_bytes=1_000_000,
    selftest_board="basic.after",
    corpus_qualified_only=True,
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

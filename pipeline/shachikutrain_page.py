"""社畜トレイン（Shachiku Train）中盤手法 — the Shachiku Train technique pages: one overview and the constructed demo page.

    python3 -m pipeline.shachikutrain_page --out-dir /tmp/shachikutrain   # render both pages into a directory
    python3 -m pipeline.shachikutrain_page --selftest                     # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs, pages,
quarantine, figures); this file is Shachiku Train's `TechniqueSiteProfile`, and its words are
`shachikutrain_prose.json`.

Inputs, all committed: `pipeline/openers/shachikutrain-technique.json` (transcribed and gated by
`extract_shachikutrain_shapes`), `analysis/shachikutrain-facts.json` (`emit-technique-facts.ts --technique
shachikutrain`) and `analysis/shachikutrain-demos.json` (`emit-technique-demos.ts --technique shachikutrain`).

The letters this page draws beyond the route pages': `r` the page's pale S, and `J L O S` a piece placed before the
first TSD in the renderer's muted colour (the route pages' `Z` class already draws an upper-case Z, outlined).
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

SHACHIKUTRAIN_CSS = """
  .scb-rp { fill: #4caf50; opacity: .4; }
  .scb-jm { fill: #4a72d1; opacity: .55; } .scb-sm { fill: #4caf50; opacity: .55; }
  .scb-lm { fill: #e08a35; opacity: .55; } .scb-om { fill: #d9b638; opacity: .55; }
"""

PROFILE = TechniqueSiteProfile(
    module="shachikutrain_page",
    prefix="shachikutrain",
    transcription_rel=os.path.join("pipeline", "openers", "shachikutrain-technique.json"),
    facts_rel=os.path.join("analysis", "shachikutrain-facts.json"),
    demos_rel=os.path.join("analysis", "shachikutrain-demos.json"),
    prose_path=os.path.join(HERE, "shachikutrain_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="shachikutrain",
    opportunity="TSD",
    cell_classes={"r": "rp", "J": "jm", "S": "sm", "L": "lm", "O": "om"},
    extra_css=SHACHIKUTRAIN_CSS,
    max_page_bytes=1_000_000,
    selftest_board="basic.second",
    corpus_qualified_only=True,
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

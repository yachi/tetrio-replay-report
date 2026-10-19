"""ダブルダガー (Double Dagger) 中盤手法 — the Double Dagger technique pages: one overview and the
constructed demo page.

    python3 -m pipeline.doubledagger_page --out-dir /tmp/doubledagger   # render both pages into a directory
    python3 -m pipeline.doubledagger_page --selftest                    # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs,
pages, quarantine, figures); this file is Double Dagger's `TechniqueSiteProfile`, and its words are
`doubledagger_prose.json`.

Inputs, all committed: `pipeline/openers/doubledagger-technique.json` (transcribed and gated by
`extract_doubledagger_shapes`), `analysis/doubledagger-facts.json` (`emit-technique-facts.ts --technique
doubledagger`) and `analysis/doubledagger-demos.json` (`emit-technique-demos.ts --technique doubledagger`).

The letters this page draws beyond the route pages': `C` an earlier cell muted (in a spin board's cleared
rows, or the stack a build tells the player to fill), `T` and `I` the spin piece's cells in a cleared row,
`B` a dark-grey cell (read as empty) and `p` the pink cell that must be empty, drawn pink rather than as the
route pages' dashed placeholder.
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

DOUBLEDAGGER_CSS = """
  .scb-cl { fill: var(--muted); opacity: .3; }
  .scb-tm { fill: #9b5fd0; opacity: .55; } .scb-im { fill: #3fb8c4; opacity: .55; }
  .scb-open { fill: var(--muted); opacity: .12; }
  .scb-pk { fill: #ff33ff; opacity: .45; }
"""

PROFILE = TechniqueSiteProfile(
    module="doubledagger_page",
    prefix="doubledagger",
    transcription_rel=os.path.join("pipeline", "openers", "doubledagger-technique.json"),
    facts_rel=os.path.join("analysis", "doubledagger-facts.json"),
    demos_rel=os.path.join("analysis", "doubledagger-demos.json"),
    prose_path=os.path.join(HERE, "doubledagger_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="doubledagger",
    opportunity="TSD",
    cell_classes={"C": "cl", "T": "tm", "I": "im", "B": "open", "p": "pk"},
    extra_css=DOUBLEDAGGER_CSS,
    max_page_bytes=1_000_000,
    selftest_board="basic.after",
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

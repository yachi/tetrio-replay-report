"""インペリアルクロス (Imperial Cross) 中盤手法 — the Imperial Cross technique pages: one overview and the
constructed demo page.

    python3 -m pipeline.imperialcross_page --out-dir /tmp/imperialcross   # render both pages into a directory
    python3 -m pipeline.imperialcross_page --selftest                     # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs,
pages, quarantine, figures); this file is Imperial Cross's `TechniqueSiteProfile`, and its words are
`imperialcross_prose.json`.

Inputs, all committed: `pipeline/openers/imperialcross-technique.json` (transcribed and gated by
`extract_imperialcross_shapes`), `analysis/imperialcross-facts.json` (`emit-technique-facts.ts --technique
imperialcross`) and `analysis/imperialcross-demos.json` (`emit-technique-demos.ts --technique imperialcross`).

The letters this page draws beyond the route pages': `C` an earlier cell muted (in the spin board's cleared
rows, or the stack a cross-shape build assumes), `T` the T's cells in a cleared row, and `B` a cell the
basic form leaves open (read as empty), drawn dark.
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

IMPERIALCROSS_CSS = """
  .scb-cl { fill: var(--muted); opacity: .3; }
  .scb-tm { fill: #9b5fd0; opacity: .55; }
  .scb-open { fill: var(--muted); opacity: .12; }
"""

PROFILE = TechniqueSiteProfile(
    module="imperialcross_page",
    prefix="imperialcross",
    transcription_rel=os.path.join("pipeline", "openers", "imperialcross-technique.json"),
    facts_rel=os.path.join("analysis", "imperialcross-facts.json"),
    demos_rel=os.path.join("analysis", "imperialcross-demos.json"),
    prose_path=os.path.join(HERE, "imperialcross_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="imperialcross",
    opportunity="TSD",
    cell_classes={"C": "cl", "T": "tm", "B": "open"},
    extra_css=IMPERIALCROSS_CSS,
    max_page_bytes=1_000_000,
    selftest_board="basic.after",
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

"""STMB Cave 中盤手法 — the STMB Cave technique pages: one overview and the constructed demo page.

    python3 -m pipeline.stmbcave_page --out-dir /tmp/stmbcave   # render both pages into a directory
    python3 -m pipeline.stmbcave_page --selftest                # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs,
pages, quarantine, figures); this file is STMB Cave's `TechniqueSiteProfile`, and its words are
`stmbcave_prose.json`.

Inputs, all committed: `pipeline/openers/stmbcave-technique.json` (transcribed and gated by
`extract_stmbcave_shapes`), `analysis/stmbcave-facts.json` (`emit-technique-facts.ts --technique
stmbcave`) and `analysis/stmbcave-demos.json` (`emit-technique-demos.ts --technique stmbcave`).

The letters this page draws beyond the route pages': `C` an earlier cell in a row the spin clears and
`T J Z S L O` a piece's cells there (all muted, our reading, checked by the gate).
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

STMBCAVE_CSS = """
  .scb-cl { fill: var(--muted); opacity: .3; }
  .scb-tm { fill: #9b5fd0; opacity: .55; } .scb-jm { fill: #4a72d1; opacity: .55; }
  .scb-zm { fill: #d64f4a; opacity: .55; } .scb-sm { fill: #4caf50; opacity: .55; }
  .scb-lm { fill: #e08a35; opacity: .55; } .scb-om { fill: #d9b638; opacity: .55; }
"""

PROFILE = TechniqueSiteProfile(
    module="stmbcave_page",
    prefix="stmbcave",
    transcription_rel=os.path.join("pipeline", "openers", "stmbcave-technique.json"),
    facts_rel=os.path.join("analysis", "stmbcave-facts.json"),
    demos_rel=os.path.join("analysis", "stmbcave-demos.json"),
    prose_path=os.path.join(HERE, "stmbcave_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="stmbcave",
    opportunity="TSD",
    cell_classes={"C": "cl", "T": "tm", "J": "jm", "Z": "zm", "S": "sm", "L": "lm", "O": "om"},
    extra_css=STMBCAVE_CSS,
    max_page_bytes=1_000_000,
    selftest_board="feature.after",
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

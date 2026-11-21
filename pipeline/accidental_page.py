"""意外 T-spin（accidental TSD / TST）中盤手法 — the overview and the constructed demo page.

    python3 -m pipeline.accidental_page --out-dir /tmp/accidental   # render both pages into a directory
    python3 -m pipeline.accidental_page --selftest                  # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs, pages,
quarantine, figures); this file is the page's `TechniqueSiteProfile`, and its words are `accidental_prose.json`.

Inputs, all committed: `pipeline/openers/accidental-technique.json` (transcribed and gated by
`extract_accidental_shapes`), `analysis/accidental-facts.json` (`emit-technique-facts.ts --technique accidental`) and
`analysis/accidental-demos.json` (`emit-technique-demos.ts --technique accidental`).

The page has no source site: it is yachi's request with yachi's own phone recording, which is not committed or shown, so
the prose carries a whole `source_line` in place of the shared web-page credit. One variant, `tst`, `window_basis:
spin_rule`: a full TST whose slot the previous T-spin's clear uncovered, one column of it then open to the sky, the roof over that column placed after it.
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

# C: a cell of a row the spin clears, drawn muted
ACCIDENTAL_CSS = """
  .scb-cl { fill: var(--muted); opacity: .3; }
"""

PROFILE = TechniqueSiteProfile(
    module="accidental_page",
    prefix="accidental",
    transcription_rel=os.path.join("pipeline", "openers", "accidental-technique.json"),
    facts_rel=os.path.join("analysis", "accidental-facts.json"),
    demos_rel=os.path.join("analysis", "accidental-demos.json"),
    prose_path=os.path.join(HERE, "accidental_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="tst",
    opportunity="TST",
    cell_classes={"C": "cl"},
    extra_css=ACCIDENTAL_CSS,
    max_page_bytes=1_000_000,
    selftest_board="video.tst",
    corpus_qualified_only=True,
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

"""STSD 中盤手法 — the STSD technique pages: one overview and the constructed demo page.

    python3 -m pipeline.stsd_page --out-dir /tmp/stsd   # render both pages into a directory
    python3 -m pipeline.stsd_page --selftest            # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs,
pages, quarantine, figures); this file is STSD's `TechniqueSiteProfile`, and its words are
`stsd_prose.json`.

Inputs, all committed: `pipeline/openers/stsd-technique.json` (transcribed and gated by
`extract_stsd_shapes`), `analysis/stsd-facts.json` (`emit-technique-facts.ts --technique stsd`) and
`analysis/stsd-demos.json` (`emit-technique-demos.ts --technique stsd`).

The letters this page draws beyond the route pages': `C` an earlier cell in a row a spin clears and
`T` / `J` the spin piece's cells there (all muted, our reading, checked by the gate), and `B` the
EMPTY hole of a garbage row, drawn as an outlined cell.
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

STSD_CSS = """
  .scb-cl { fill: var(--muted); opacity: .3; }
  .scb-tm { fill: #9b5fd0; opacity: .55; } .scb-jm { fill: #4a72d1; opacity: .55; }
  .scb-hole { fill: none; stroke: var(--ink); stroke-width: 1.5; }
"""

PROFILE = TechniqueSiteProfile(
    module="stsd_page",
    prefix="stsd",
    transcription_rel=os.path.join("pipeline", "openers", "stsd-technique.json"),
    facts_rel=os.path.join("analysis", "stsd-facts.json"),
    demos_rel=os.path.join("analysis", "stsd-demos.json"),
    prose_path=os.path.join(HERE, "stsd_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="stsd",
    opportunity="TSD",
    cell_classes={"C": "cl", "T": "tm", "J": "jm", "B": "hole"},
    extra_css=STSD_CSS,
    max_page_bytes=1_000_000,
    corpus_qualified_only=True,
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

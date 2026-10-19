"""欄干（Parapet）中盤手法 — the Parapet technique pages: one overview and the constructed demo page.

    python3 -m pipeline.parapet_page --out-dir /tmp/parapet   # render both pages into a directory
    python3 -m pipeline.parapet_page --selftest               # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs, pages,
quarantine, figures); this file is Parapet's `TechniqueSiteProfile`, and its words are `parapet_prose.json`.
It is the first profile with a second variant (`more_variants`): the TSS on the same terrain, whose figures are
keyed `parapet_tss:<key>` and whose headings overlay the prose's `more_variants.parapet_tss`.

Inputs, all committed: `pipeline/openers/parapet-technique.json` (transcribed and gated by
`extract_parapet_shapes`), `analysis/parapet-facts.json` (`emit-technique-facts.ts --technique parapet`) and
`analysis/parapet-demos.json` (`emit-technique-demos.ts --technique parapet`).

The letters this page draws beyond the route pages': `C` an earlier cell muted in a spin board's cleared rows,
and `T` the spin's T in a cleared row, muted.
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

PARAPET_CSS = """
  .scb-cl { fill: var(--muted); opacity: .3; }
  .scb-tm { fill: #9b5fd0; opacity: .55; }
"""

PROFILE = TechniqueSiteProfile(
    module="parapet_page",
    prefix="parapet",
    transcription_rel=os.path.join("pipeline", "openers", "parapet-technique.json"),
    facts_rel=os.path.join("analysis", "parapet-facts.json"),
    demos_rel=os.path.join("analysis", "parapet-demos.json"),
    prose_path=os.path.join(HERE, "parapet_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="parapet",
    opportunity="TSD",
    cell_classes={"C": "cl", "T": "tm"},
    extra_css=PARAPET_CSS,
    max_page_bytes=1_000_000,
    selftest_board="tsd.after",
    more_variants=(("parapet_tss", "TSS"),),
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

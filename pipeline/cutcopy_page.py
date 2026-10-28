"""千鳥格子（Cut Copy）中盤手法 — the Cut Copy technique pages: one overview and the constructed demo page.

    python3 -m pipeline.cutcopy_page --out-dir /tmp/cutcopy   # render both pages into a directory
    python3 -m pipeline.cutcopy_page --selftest               # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs, pages,
quarantine, figures); this file is Cut Copy's `TechniqueSiteProfile`, and its words are `cutcopy_prose.json`.

Inputs, all committed: `pipeline/openers/cutcopy-technique.json` (transcribed and gated by
`extract_cutcopy_shapes`), `analysis/cutcopy-facts.json` (`emit-technique-facts.ts --technique cutcopy`) and
`analysis/cutcopy-demos.json` (`emit-technique-demos.ts --technique cutcopy`), `analysis/cutcopy-own.json` (boards of
our own design, `emit-technique-own.ts --technique cutcopy`) and `analysis/cutcopy-selfplay.json` (games cold-clear
played alone, `emit-cutcopy-selfplay.ts`), the last two played on the demo page.

The letters this page draws beyond the route pages': `C` an earlier cell muted in a spin board's cleared rows,
and `T` the spin's T in a cleared row, muted. A second variant (`uncut`, harddrop's second generic type) is printed
after the first, its board and after board harddrop's drawings (`external` nodes, each tagged on the page).
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

CUTCOPY_CSS = """
  .scb-cl { fill: var(--muted); opacity: .3; }
  .scb-tm { fill: #9b5fd0; opacity: .55; }
"""

PROFILE = TechniqueSiteProfile(
    module="cutcopy_page",
    prefix="cutcopy",
    transcription_rel=os.path.join("pipeline", "openers", "cutcopy-technique.json"),
    facts_rel=os.path.join("analysis", "cutcopy-facts.json"),
    demos_rel=os.path.join("analysis", "cutcopy-demos.json"),
    prose_path=os.path.join(HERE, "cutcopy_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="cutcopy",
    opportunity="TSD",
    cell_classes={"C": "cl", "T": "tm"},
    extra_css=CUTCOPY_CSS,
    max_page_bytes=1_000_000,
    selftest_board="second.spin",
    # harddrop's second generic type (Uncut copy), measured at the same TSD
    more_variants=(("uncut", "TSD"),),
    showcase=True,
    # boards of ours (technique-own.ts's search), played on the demo page after the drawn boards
    own_rel=os.path.join("analysis", "cutcopy-own.json"),
    # games cold-clear played alone (cutcopy-selfplay.ts), played on the demo page after the own designs
    selfplay_rel=os.path.join("analysis", "cutcopy-selfplay.json"),
    corpus_qualified_only=True,
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

"""階段のドネイト（Kaidan Setups）中盤手法 — the Kaidan technique pages: one overview and the constructed demo page.

    python3 -m pipeline.kaidan_page --out-dir /tmp/kaidan   # render both pages into a directory
    python3 -m pipeline.kaidan_page --selftest              # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs, pages,
quarantine, figures); this file is Kaidan's `TechniqueSiteProfile`, and its words are `kaidan_prose.json`.
No shared file changed for this page.

Inputs, all committed: `pipeline/openers/kaidan-technique.json` (transcribed and gated by
`extract_kaidan_shapes`), `analysis/kaidan-facts.json` (`emit-technique-facts.ts --technique kaidan`) and
`analysis/kaidan-demos.json` (`emit-technique-demos.ts --technique kaidan`).

The letters this page draws beyond the route pages': `C` an earlier cell drawn muted, `T` the spin's T in a
cleared row, muted, and `I J L O S` a piece's cell in a cleared row, muted (the route pages' `Z` class already
draws an upper-case Z, outlined).
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

KAIDAN_CSS = """
  .scb-cl { fill: var(--muted); opacity: .3; }
  .scb-tm { fill: #9b5fd0; opacity: .55; }
  .scb-im { fill: #2fb4d9; opacity: .55; } .scb-jm { fill: #4a72d1; opacity: .55; }
  .scb-lm { fill: #e08a35; opacity: .55; } .scb-om { fill: #d9b638; opacity: .55; }
  .scb-sm { fill: #4caf50; opacity: .55; }
"""

PROFILE = TechniqueSiteProfile(
    module="kaidan_page",
    prefix="kaidan",
    transcription_rel=os.path.join("pipeline", "openers", "kaidan-technique.json"),
    facts_rel=os.path.join("analysis", "kaidan-facts.json"),
    demos_rel=os.path.join("analysis", "kaidan-demos.json"),
    prose_path=os.path.join(HERE, "kaidan_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="kaidan",
    opportunity="TSD",
    cell_classes={"C": "cl", "T": "tm", "I": "im", "J": "jm", "L": "lm", "O": "om", "S": "sm"},
    extra_css=KAIDAN_CSS,
    max_page_bytes=1_000_000,
    selftest_board="basic.after",
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

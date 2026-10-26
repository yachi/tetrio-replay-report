"""基本的なドネイト（basic donating）中盤手法 — the basic donating technique pages: one overview and the constructed
demo page.

    python3 -m pipeline.basicdonating_page --out-dir /tmp/bd   # render both pages into a directory
    python3 -m pipeline.basicdonating_page --selftest          # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs, pages,
quarantine, figures); this file is the page's `TechniqueSiteProfile`, and its words are `basicdonating_prose.json`.
No shared file changed for this page.

Inputs, all committed: `pipeline/openers/basicdonating-technique.json` (transcribed and gated by
`extract_basicdonating_shapes`), `analysis/basicdonating-facts.json` (`emit-technique-facts.ts --technique
basicdonating`) and `analysis/basicdonating-demos.json` (`emit-technique-demos.ts --technique basicdonating`).

One variant, `rule`, a TSD matched by the donation rule (`pipeline/sim/basicdonating-rule.ts`, yachi's, 2026-10-26)
in place of a window; the six hole windows (k1..k6) and the nub window are retired. Its window section draws the T of
the page's first drawing, and each case's thumbnail is the hit's box (the T and its own column). The letters this page
draws beyond the route pages': `C` an earlier cell
in a cleared row, muted, and `I J L O S` a piece's cell in a cleared row, muted (the route pages' `Z` class already
draws an upper-case Z, outlined).
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

BASICDONATING_CSS = """
  .scb-cl { fill: var(--muted); opacity: .3; }
  .scb-im { fill: #2fb4d9; opacity: .55; } .scb-jm { fill: #4a72d1; opacity: .55; }
  .scb-lm { fill: #e08a35; opacity: .55; } .scb-om { fill: #d9b638; opacity: .55; }
  .scb-sm { fill: #4caf50; opacity: .55; }
"""

PROFILE = TechniqueSiteProfile(
    module="basicdonating_page",
    prefix="basicdonating",
    transcription_rel=os.path.join("pipeline", "openers", "basicdonating-technique.json"),
    facts_rel=os.path.join("analysis", "basicdonating-facts.json"),
    demos_rel=os.path.join("analysis", "basicdonating-demos.json"),
    prose_path=os.path.join(HERE, "basicdonating_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="rule",
    opportunity="TSD",
    cell_classes={"C": "cl", "I": "im", "J": "jm", "L": "lm", "O": "om", "S": "sm"},
    extra_css=BASICDONATING_CSS,
    max_page_bytes=3_000_000,
    selftest_board="intro.z.after",
    corpus_qualified_only=True,
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

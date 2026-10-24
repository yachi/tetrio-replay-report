"""途中DT砲（DT砲）中盤手法 — the mid-game DT Cannon technique pages: one overview and the constructed demo page.

    python3 -m pipeline.dtcannon_page --out-dir /tmp/dtcannon   # render both pages into a directory
    python3 -m pipeline.dtcannon_page --selftest                # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs, pages,
quarantine, figures); this file is 途中DT砲's `TechniqueSiteProfile`, and its words are `dtcannon_prose.json`.

Inputs, all committed: `pipeline/openers/dtcannon-technique.json` (transcribed and gated by
`extract_dtcannon_shapes`), `analysis/dtcannon-facts.json` (`emit-technique-facts.ts --technique dtcannon`)
and `analysis/dtcannon-demos.json` (`emit-technique-demos.ts --technique dtcannon`).

The letters this page draws beyond the route pages': `C` an earlier cell muted (in a spin board's cleared rows,
or the stack a build places beside the slot), the upper-case `I J L O S Z` a piece's cell drawn muted (the route
pages' `Z` is a placeholder, so this profile re-maps it), `p` the page's pink cell and `y` the one unread letter
on DTDT's TST board, both read as filled (the route pages' `p` is a dashed outline, so it is re-mapped too). `U`
keeps the route pages' dashed slot: it is where the T goes.
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

DTCANNON_CSS = """
  .scb-cl { fill: var(--muted); opacity: .3; }
  .scb-im { fill: #3fb8c4; opacity: .55; } .scb-jm { fill: #4a72d1; opacity: .55; }
  .scb-om { fill: #d9b638; opacity: .55; } .scb-sm { fill: #4caf50; opacity: .55; }
  .scb-zm { fill: #d64f4a; opacity: .55; } .scb-lm { fill: #e08a35; opacity: .55; }
  .scb-pk { fill: #e06fb0; } .scb-yy { fill: var(--muted); opacity: .55; stroke: var(--ink); stroke-width: 1; }
"""

PROFILE = TechniqueSiteProfile(
    module="dtcannon_page",
    prefix="dtcannon",
    transcription_rel=os.path.join("pipeline", "openers", "dtcannon-technique.json"),
    facts_rel=os.path.join("analysis", "dtcannon-facts.json"),
    demos_rel=os.path.join("analysis", "dtcannon-demos.json"),
    prose_path=os.path.join(HERE, "dtcannon_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="dtcannon",
    opportunity="TSD",
    cell_classes={"C": "cl", "I": "im", "J": "jm", "L": "lm", "O": "om", "S": "sm", "Z": "zm",
                  "p": "pk", "y": "yy"},
    extra_css=DTCANNON_CSS,
    max_page_bytes=1_000_000,
    selftest_board="tst.spin",
    corpus_qualified_only=True,
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

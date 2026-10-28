"""BT砲（途中BT）中盤手法 — the BT砲 technique pages: one overview and the constructed demo page.

    python3 -m pipeline.btcannon_page --out-dir /tmp/btcannon   # render both pages into a directory
    python3 -m pipeline.btcannon_page --selftest                # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs, pages,
quarantine, figures); this file is BT砲's `TechniqueSiteProfile`, and its words are `btcannon_prose.json`.

Inputs, all committed: `pipeline/openers/btcannon-technique.json` (transcribed and gated by
`extract_btcannon_shapes`), `analysis/btcannon-facts.json` (`emit-technique-facts.ts --technique btcannon`)
and `analysis/btcannon-demos.json` (`emit-technique-demos.ts --technique btcannon`).

The letters this page draws beyond the route pages': `C` an earlier cell muted in a spin board's cleared rows,
and the upper-case `I J O S Z` of the 72積み builds, the pieces the page places, in muted piece colours (the
route pages' `Z` is a placeholder, so this profile re-maps it). `U` keeps the route pages' dashed slot: it is
where the T goes.
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

BTCANNON_CSS = """
  .scb-cl { fill: var(--muted); opacity: .3; }
  .scb-im { fill: #3fb8c4; opacity: .55; } .scb-jm { fill: #4a72d1; opacity: .55; }
  .scb-om { fill: #d9b638; opacity: .55; } .scb-sm { fill: #4caf50; opacity: .55; }
  .scb-zm { fill: #d64f4a; opacity: .55; }
"""

PROFILE = TechniqueSiteProfile(
    module="btcannon_page",
    prefix="btcannon",
    transcription_rel=os.path.join("pipeline", "openers", "btcannon-technique.json"),
    facts_rel=os.path.join("analysis", "btcannon-facts.json"),
    demos_rel=os.path.join("analysis", "btcannon-demos.json"),
    prose_path=os.path.join(HERE, "btcannon_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="btcannon",
    opportunity="TSD",
    cell_classes={"C": "cl", "I": "im", "J": "jm", "O": "om", "S": "sm", "Z": "zm"},
    extra_css=BTCANNON_CSS,
    max_page_bytes=1_000_000,
    selftest_board="tst.spin",
    corpus_qualified_only=True,
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

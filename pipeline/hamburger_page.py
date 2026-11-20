"""ハンバーガー（Hamburger）中盤手法 — harddrop's Hamburger technique pages: one overview and the constructed demo page.

    python3 -m pipeline.hamburger_page --out-dir /tmp/hamburger   # render both pages into a directory
    python3 -m pipeline.hamburger_page --selftest                 # the audit's mutants

The renderer and every audit rule are the shared `technique_page.py` (read its header: inputs, pages,
quarantine, figures); this file is Hamburger's `TechniqueSiteProfile`, and its words are `hamburger_prose.json`.

Inputs, all committed: `pipeline/openers/hamburger-technique.json` (transcribed and gated by
`extract_hamburger_shapes`), `analysis/hamburger-facts.json` (`emit-technique-facts.ts --technique hamburger`) and
`analysis/hamburger-demos.json` (`emit-technique-demos.ts --technique hamburger`).

The source is harddrop's Hamburger page, so the prose carries a `source_credit` (King Crimson's precedent). The
opportunity is a full TSS. The overview and the index card split the qualifying hits by each hit's `cover`
(`hamburger-cover.ts`: one S/Z against other whole pieces), through the opt-in `split_field`. Every letter the
transcription draws is a route-page letter, so no cell class is added.
"""
import os

from pipeline.technique_page import HERE, TechniqueSite, TechniqueSiteProfile

PROFILE = TechniqueSiteProfile(
    module="hamburger_page",
    prefix="hamburger",
    transcription_rel=os.path.join("pipeline", "openers", "hamburger-technique.json"),
    facts_rel=os.path.join("analysis", "hamburger-facts.json"),
    demos_rel=os.path.join("analysis", "hamburger-demos.json"),
    prose_path=os.path.join(HERE, "hamburger_prose.json"),
    transcription_schema="technique-shapes/1",
    facts_schema="technique-facts/1",
    demos_schema="technique-demos/1",
    variant="hamburger",
    opportunity="TSS",
    max_page_bytes=1_000_000,
    selftest_board="spin.after",
    corpus_qualified_only=True,
    split_field="cover",
)

SITE = TechniqueSite(PROFILE)


def main(argv=None):
    return SITE.main(argv, __doc__)


if __name__ == "__main__":
    raise SystemExit(main())

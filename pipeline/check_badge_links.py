"""Every badge in a report must resolve to a claim the report actually carries.

    python3 -m pipeline.check_badge_links sessions/2026-08-01/report

A badge is `<span class="badge" data-claim="G014">`, rendered by the page from the
`claims-data` island. When the cited id is not in that island the badge renders
`⏳ G014` linked to an anchor that does not exist — which reads as "still being
proved" rather than as the typo it is. `check_proof_links` does not catch this: it
checks the proof map against the Dafny, one layer further in, and is happy while
the prose points somewhere else entirely.

Three ways a citation goes wrong, and this checks all three:

1. **The id does not exist.** A hand-edited badge with a typo, or one left behind
   after a claim was renumbered. Every prose citation is resolved against the island.

2. **The shorthand is not expandable.** Match-card copy is authored as `<b>G004</b>`
   and expanded in the browser by `expandShorthandBadges`. That function's regex is
   read out of the report **itself** rather than assumed here, because the bug this
   guards against was precisely a narrower regex than the prose: it matched
   `[CR]\\d{3}`, so every `<b>G0xx</b>` in 07-28's match copy stayed literal text on
   the page. Counting `.badge[data-status]` in the DOM does not catch that either —
   the badge is simply never created. It was found by reading a screenshot.

3. **The citation is not a badge at all.** The generated sections print bare ids —
   `<p class="ir-note">Claim：G084 · G085 · …` and `<td class="pc-cid">G080 · G081 ✓</td>`
   — which carry no `data-claim` and no `<b>`, so checks 1 and 2 never saw them and
   nothing renders ⏳. They are still citations to a reader, and on 2026-07-22 and
   2026-07-24 they name claims those reports do not carry. Scanned over every
   generated REGION rather than by label, because the two sections spell the same act
   two ways and the second has no label to key on.

The island is the right authority to check against rather than the ledgers: it is
what the page has, so it is what a reader's badge can resolve to.
"""
import argparse
import json
import os
import re
import sys

ISLAND = re.compile(r'<script type="application/json" id="claims-data">(.*?)</script>', re.S)
MATCH_COPY = re.compile(r'<script type="application/json" id="match-copy">(.*?)</script>', re.S)
DATA_CLAIM = re.compile(r'data-claim="([^"]+)"')
# Scripts are stripped before the prose scan. `expandShorthandBadges` BUILDS the
# attribute (`'data-claim="' + id + '"'`), so scanning the raw file reports the
# renderer's own template as an unresolvable citation — a checker failing on the
# code that makes the thing it checks.
SCRIPT = re.compile(r"<script\b.*?</script>", re.S)
EXPANDER = re.compile(r"function expandShorthandBadges[^{]*\{\s*return \w+\.replace\(/(.*?)/g")
# Any <b>…</b> that LOOKS like a claim citation. Deliberately wider than any
# expander regex: the point is to find shorthand the page would fail to expand.
SHORTHAND_LIKE = re.compile(r"<b>([A-Za-z]{1,2}\d{2,4})</b>")
# Plain-text citations, scanned over every GENERATED REGION rather than by label.
#
# `intense_round.py` prints `<p class="ir-note">Claim：G084 · G085 · …` and `pc_section.py` prints
# `<td class="pc-cid">G080 · G081 ✓</td>` — same act, two markups, and the second carries no label at
# all. A checker keyed on `Claim：` sees the first and silently misses the second, which is the
# enumerate-the-containers trap this repo keeps paying for (`check_prose_figures` naming prose files
# one by one, `verify.yml` testing for a single `hand_claims.py`). A generated region is machine-
# produced, so a bare claim-id token inside one IS a citation by construction, and a section added
# later is covered without anyone remembering to register its markup.
GENERATED_REGION = re.compile(r"<!-- BEGIN generated .*?-->(.*?)<!-- END generated [^>]*-->", re.S)
PLAIN_CITE_ID = re.compile(r"\b([A-Z]\d{3})\b")

# Sessions whose plain-text citations name claims their island does not carry, exact and per id.
#
# 2026-07-22 and 2026-07-24 are the only two, and the cause is structural rather than a typo: their
# committed `claims-proof-map.json` covers the HAND ledgers only, so `appendix._rows` caps their
# islands at 54 and 52 rows, while `intense_round` and `pc_section` cite generated claims that are
# genuinely proved behind a separate map. The four later sessions carry all their ledgers and have
# no gap at all. Resolving it means extending those two islands — which moves the pinned 54/52 row
# counts and must be done for `pc_section` in the same stroke — so it is a decision recorded in
# ROADMAP (最癲一局 item 7), not something to paper over here.
PLAIN_CITE_ISLAND_GAP = {
    "2026-07-22": [
        "G016", "G017", "G018", "G019", "G020", "G021", "G022", "G023", "G024", "G025",
        "G043", "G044", "G045", "G065", "G070", "G071", "G072", "G073", "G074", "G075",
        "G076", "G077", "G080", "G081", "G082", "G083", "G084", "G085", "G086", "G087",
        "G088", "G089", "G090"
    ],
    "2026-07-24": [
        "G014", "G015", "G016", "G017", "G018", "G019", "G020", "G021", "G022", "G023",
        "G041", "G042", "G043", "G064", "G069", "G070", "G071", "G072", "G073", "G074",
        "G075", "G076", "G079", "G080", "G081", "G082", "G083", "G084", "G085", "G086",
        "G087", "G088", "G089"
    ],
}


def island_ids(html, path):
    m = ISLAND.search(html)
    if not m:
        raise SystemExit(f"{path}: no claims-data island — the badges have nothing to "
                         f"resolve against")
    data = json.loads(m.group(1))
    claims = data.get("claims")
    if isinstance(claims, dict):
        return set(claims)
    return {c["id"] for c in (claims or [])}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir")
    args = ap.parse_args(argv)

    path = os.path.join(args.report_dir, "report.html")
    with open(path, encoding="utf-8") as fh:
        html = fh.read()

    known = island_ids(html, path)
    problems = []

    # 1. every data-claim resolves
    cited = sorted(set(DATA_CLAIM.findall(SCRIPT.sub("", html))))
    for cid in cited:
        if cid not in known:
            problems.append(f'data-claim="{cid}" is not in the claims-data island '
                            f"({len(known)} claims) — it will render ⏳ and link nowhere")

    # 2. every shorthand the authored copy uses is one the page can expand
    m = EXPANDER.search(html)
    if not m:
        problems.append("expandShorthandBadges not found, or its regex is not in the "
                        "form this checker reads — the shorthand check did not run")
        expander = None
    else:
        expander = re.compile(m.group(1))

    shorthand = set()
    mc = MATCH_COPY.search(html)
    if mc:
        # The island is JSON, so the copy's markup arrives escaped; decode it first
        # or every <b> below is invisible to the scan.
        for card in (json.loads(mc.group(1)).get("cards") or {}).values():
            shorthand |= {(card.get("body") or ""), (card.get("title") or "")}
    blob = "\n".join(shorthand)
    for cid in sorted(set(SHORTHAND_LIKE.findall(blob))):
        token = f"<b>{cid}</b>"
        if expander is not None and not expander.search(token):
            problems.append(f"{token} in match-card copy is not matched by "
                            f"expandShorthandBadges — it stays literal text on the page")
        elif cid not in known:
            problems.append(f"{token} in match-card copy expands to a badge for {cid}, "
                            f"which is not in the claims-data island")

    # 3. PLAIN-TEXT citations, which are citations to a reader whatever their markup.
    #
    # `intense_round.py` and `pc_section.py` print `<p class="ir-note">Claim：G084 · G085 · …`.
    # Those ids carry no `data-claim` and no `<b>` wrapper, so checks 1 and 2 never saw them and
    # `expandShorthandBadges` never turns them into badges — they are literal text by design, and
    # the ROADMAP's reading of this as "close to the failure check_badge_links exists to prevent"
    # is wrong in a way worth keeping straight: nothing renders ⏳ here. What IS wrong is narrower
    # and real — a 2026-07-22 reader is told "Claim：G084" and cannot find G084 in that report,
    # because those two sessions' islands hold only their hand ledgers (54 and 52 rows) while their
    # generated ledgers sit behind a separate proof map.
    #
    # NAMED, NOT TOLERATED BY A BOUND, and exact in both directions — the `DT_ORDER_IN_OPENER`
    # shape. An inequality would absorb a 23rd; this list means a new one has to be looked at, and
    # an entry that stops naming a real dead reference fails too, so extending the island later
    # cannot leave a stale exemption behind.
    plain = set()
    for body in GENERATED_REGION.findall(SCRIPT.sub("", html)):
        plain |= set(PLAIN_CITE_ID.findall(body))
    dead = sorted(cid for cid in plain if cid not in known)
    # `report_dir` is `sessions/<date>/report`, so the session is its parent's name.
    session = os.path.basename(os.path.dirname(os.path.abspath(args.report_dir)))
    allowed = PLAIN_CITE_ISLAND_GAP.get(session, [])
    for cid in dead:
        if cid not in allowed:
            problems.append(f'plain-text "Claim：{cid}" is not in the claims-data island '
                            f"({len(known)} claims) — the reader is pointed at a claim this "
                            f"report does not carry")
    for cid in allowed:
        if cid not in dead:
            problems.append(f"PLAIN_CITE_ISLAND_GAP names {cid} for {session}, but it resolves "
                            f"now — a stale exemption is as bad as a missing one; drop it")

    if problems:
        print(f"FAIL {path}: {len(problems)} unresolvable badge citation(s)", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1

    print(f"  ok  {len(cited)} badge citation(s) and "
          f"{len(set(SHORTHAND_LIKE.findall(blob)))} shorthand citation(s) all resolve "
          f"to the island's {len(known)} claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

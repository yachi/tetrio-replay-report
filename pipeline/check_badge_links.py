"""Every badge in a report must resolve to a claim the report actually carries.

    python3 -m pipeline.check_badge_links sessions/2026-08-01/report

A badge is `<span class="badge" data-claim="G014">`, rendered by the page from the
`claims-data` island. When the cited id is not in that island the badge renders
`⏳ G014` linked to an anchor that does not exist — which reads as "still being
proved" rather than as the typo it is. `check_proof_links` does not catch this: it
checks the proof map against the Dafny, one layer further in, and is happy while
the prose points somewhere else entirely.

Two ways a citation goes wrong, and this checks both:

1. **The id does not exist.** A hand-edited badge with a typo, or one left behind
   after a claim was renumbered. Every prose citation is resolved against the island.

2. **The shorthand is not expandable.** Match-card copy is authored as `<b>G004</b>`
   and expanded in the browser by `expandShorthandBadges`. That function's regex is
   read out of the report **itself** rather than assumed here, because the bug this
   guards against was precisely a narrower regex than the prose: it matched
   `[CR]\\d{3}`, so every `<b>G0xx</b>` in 07-28's match copy stayed literal text on
   the page. Counting `.badge[data-status]` in the DOM does not catch that either —
   the badge is simply never created. It was found by reading a screenshot.

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

"""Decode four.lol's T-Spin Forecast diagrams (fumen → board grids).

A third external source, and the cleanest of the three to capture. four.lol
(four.lol/stacking/tetris/#forecasting) is a Gatsby site whose board diagrams are drawn
client-side from **fumen** (テト譜) codes — the examples are credited to *kazu*. The rendered
DOM is build-hashed styled-components (useless as a durable fixture), but the fumen codes
underneath are stable authored content, so this captures at that layer: the nine forecast-section
fumens are committed in `four-forecast-fumens.json`, and this script decodes them with the
`py_fumen` library — a trusted third-party decoder, so the boards are machine-derived, not read by
eye. Any fumen tool re-derives the same boards, which is the second-implementation check the repo's
invariant wants.

Each fumen is a SEQUENCE, so it decodes to several pages; every page is one board frame. The nine
fumens expand to 26 frames across four subsections (basic, others, prophecy, fixing-misdrops).
Boards are rendered top-to-bottom, '.' empty, '#' stack, and the tetromino letter for a coloured
cell — the same convention as jp-forecast-boards.json.

    python3 -m pipeline.sim.extract_four_forecast            # re-decode and check byte-identity
    python3 -m pipeline.sim.extract_four_forecast --write     # (re)write four-forecast-boards.json
    python3 -m pipeline.sim.extract_four_forecast --json       # print, write nothing

Needs `py_fumen` (`pip install py-fumen`). The CI gate that reads the committed JSON is the bun
test four-forecast.test.ts, which needs no fumen decoder.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FUMENS = os.path.join(HERE, "four-forecast-fumens.json")
ARTIFACT = os.path.join(HERE, "four-forecast-boards.json")
SOURCE_URL = "https://four.lol/stacking/tetris/#forecasting"

FIELD_H = 23  # fumen playfield height (y = 0 is the bottom row)


def _board(field) -> list[str]:
    """A decoded fumen field → board rows, top-to-bottom, '.'/'#'/piece-letter."""
    rows = ["".join(field.at(x, y) for x in range(10)) for y in range(FIELD_H - 1, -1, -1)]
    rows = [r.replace("_", ".").replace("X", "#") for r in rows]
    i = 0                                  # trim fully-empty rows off the TOP only
    while i < len(rows) - 1 and set(rows[i]) == {"."}:
        i += 1
    return rows[i:]


def extract_all() -> list[dict]:
    import py_fumen
    src = json.load(open(FUMENS, encoding="utf-8"))
    out = []
    for item in src:
        for page_i, page in enumerate(py_fumen.decode(item["fumen"])):
            out.append({"section": item["section"], "page": page_i,
                        "rows": _board(page.get_field())})
    return out


def render(boards: list[dict]) -> str:
    return json.dumps(
        {"_note": ("T-Spin Forecast diagrams from four.lol (examples credited to kazu), decoded "
                   "from the committed fumen codes by pipeline/sim/extract_four_forecast.py. Each "
                   "fumen is a sequence; every page is one frame. '.' empty, '#' stack, tetromino "
                   "letter for a piece cell. A third external corpus — see wiki-fixtures (harddrop) "
                   "and jp-forecast (Tetrisちゃんねる)."),
         "source": SOURCE_URL,
         "fumens": "pipeline/sim/four-forecast-fumens.json",
         "boards": boards},
        ensure_ascii=False, indent=1) + "\n"


def main(argv: list[str]) -> int:
    if "--write" in argv:
        boards = extract_all()
        open(ARTIFACT, "w", encoding="utf-8").write(render(boards))
        print(f"wrote {os.path.relpath(ARTIFACT)} ({len(boards)} frames)")
        return 0
    if "--json" in argv:
        sys.stdout.write(render(extract_all()))
        return 0
    want = render(extract_all())
    have = open(ARTIFACT, encoding="utf-8").read() if os.path.exists(ARTIFACT) else None
    if have != want:
        print(f"FAIL  {os.path.relpath(ARTIFACT)} is "
              f"{'missing' if have is None else 'stale'}; run --write", file=sys.stderr)
        return 1
    print(f"ok — {len(json.loads(want)['boards'])} frames re-decode byte-identical from the fumens")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

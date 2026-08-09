"""Extract the 38 T-Spin Forecast diagrams from Tetrisちゃんねる into machine-readable boards.

Provenance, and why this is a SCRIPT and not a transcription. The harddrop wiki renders its
forecast boards as HTML cell-tables, so `wiki-tspin-forecast-boards.json` could be parsed from
text. The Japanese page 「予報の技法 T-Spin Forecast」 (tetrisch.github.io/main/technic/forecast.html)
ships each board as a composite JPEG instead. Reading 38 images by eye into grids would be exactly
the single-source hand data this repo forbids — so the boards are read by a DETERMINISTIC pixel
sampler here, and this file is the second, independent record of how every cell was decided. The
images themselves are committed under spec/fixtures/jp-forecast/, so the extraction re-runs offline
and any edit to it shows up as a diff against the committed JSON.

The grid is exact: every image is 400px wide = 10 columns of 40px, and a whole number of 40px rows.
Each cell is one flat guideline colour, so the centre patch classifies unambiguously to the nearest
reference — empty, stack, or one of the seven tetromino colours. A cell whose nearest reference is
farther than MAX_DIST is NOT guessed: the extractor raises, because an unrecognised colour means the
page changed and the output can no longer be trusted.

    python3 -m pipeline.sim.extract_jp_forecast            # re-extract and check byte-identity
    python3 -m pipeline.sim.extract_jp_forecast --write     # (re)write jp-forecast-boards.json
    python3 -m pipeline.sim.extract_jp_forecast --json       # print, write nothing

Needs Pillow (`pip install Pillow`); the CI gate that reads the committed JSON is the bun test
jp-forecast.test.ts, which needs no image decoder.
"""
from __future__ import annotations

import glob
import json
import os
import sys

CELL = 40  # px; every image is a clean 40px grid, 10 columns wide

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(os.path.dirname(HERE), "..", "spec", "fixtures", "jp-forecast")
ARTIFACT = os.path.join(HERE, "jp-forecast-boards.json")
SOURCE_URL = "https://tetrisch.github.io/main/technic/forecast.html"

# The guideline palette, measured from the images (a 12px centre patch, clustered). Each maps to the
# character the board grid uses: '.' empty, '#' stack, and the tetromino letter for a piece cell.
REF = {
    (240, 240, 216): ".",   # empty (beige)
    (96, 96, 96): "#",      # stack / filled
    (216, 72, 48): "Z",     # red
    (48, 168, 96): "S",     # green
    (240, 192, 24): "O",    # yellow
    (216, 120, 24): "L",    # orange
    (48, 120, 168): "J",    # blue
    (120, 72, 144): "T",    # purple
    (48, 144, 192): "I",    # cyan
}
# A cell centre farther than this (Euclidean, RGB) from every reference is not classified but raised
# on. The nearest two references (empty vs stack) are ~200 apart, so 80 is comfortably inside the gap.
MAX_DIST = 80.0


def _classify(rgb: tuple[int, int, int]) -> str:
    best, bestd = None, 1e9
    for ref, ch in REF.items():
        d = sum((a - b) ** 2 for a, b in zip(rgb, ref)) ** 0.5
        if d < bestd:
            best, bestd = ch, d
    if bestd > MAX_DIST:
        raise ValueError(f"cell colour {rgb} is {bestd:.0f} from the nearest reference — "
                         f"unrecognised, refusing to guess")
    return best


def _cell_rgb(px, c: int, r: int) -> tuple[int, int, int]:
    """Average a 12px centre patch of cell (c, r), dodging the grid lines and JPEG ringing."""
    R = G = B = n = 0
    for x in range(c * CELL + 14, c * CELL + 26):
        for y in range(r * CELL + 14, r * CELL + 26):
            pr, pg, pb = px[x, y]
            R += pr; G += pg; B += pb; n += 1
    return (R // n, G // n, B // n)


def extract_one(path: str) -> list[str]:
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if w != 10 * CELL or h % CELL != 0:
        raise ValueError(f"{os.path.basename(path)} is {w}x{h}, not a 10-wide {CELL}px grid")
    px = im.load()
    return ["".join(_classify(_cell_rgb(px, c, r)) for c in range(10))
            for r in range(h // CELL)]


def extract_all() -> list[dict]:
    out = []
    for path in sorted(glob.glob(os.path.join(IMG_DIR, "foreacast_*.jpg"))):
        name = os.path.splitext(os.path.basename(path))[0]
        out.append({"img": name, "rows": extract_one(path)})
    if not out:
        raise ValueError(f"no images found in {IMG_DIR}")
    return out


def render(boards: list[dict]) -> str:
    return json.dumps(
        {"_note": ("The 38 T-Spin Forecast (予報の技法) diagrams from Tetrisちゃんねる, extracted from "
                   "the source JPEGs by a deterministic pixel sampler (pipeline/sim/"
                   "extract_jp_forecast.py). '.' empty, '#' stack, tetromino letter for a piece cell. "
                   "An independent, image-based corpus — NOT the harddrop 29."),
         "source": SOURCE_URL,
         "images": "spec/fixtures/jp-forecast/",
         "boards": boards},
        ensure_ascii=False, indent=1) + "\n"


def main(argv: list[str]) -> int:
    if "--write" in argv:
        open(ARTIFACT, "w", encoding="utf-8").write(render(extract_all()))
        print(f"wrote {os.path.relpath(ARTIFACT)} ({len(extract_all())} boards)")
        return 0
    if "--json" in argv:
        sys.stdout.write(render(extract_all()))
        return 0
    # default: re-extract and check byte-identity to the committed JSON
    want = render(extract_all())
    have = open(ARTIFACT, encoding="utf-8").read() if os.path.exists(ARTIFACT) else None
    if have != want:
        print(f"FAIL  {os.path.relpath(ARTIFACT)} is "
              f"{'missing' if have is None else 'stale'}; run --write", file=sys.stderr)
        return 1
    print(f"ok — {len(extract_all())} boards re-extract byte-identical from the committed images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

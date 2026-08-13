"""Transcribe harddrop.com's Donation and STMB Cave pages into `wiki-tspin-techniques.json`.

    python3 -m pipeline.openers.extract_wiki_techniques            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_wiki_techniques --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_wiki_techniques --html-dir <dir> --write   # re-transcribe

WHY THIS EXISTS, and why it is a sibling of `extract_wiki_openers` rather than more rows in it.

`wiki-openers.json` answers "is the opening board this opener's field, cell for cell". That question
only makes sense at a known lock count off a known empty board. A Donation and an STMB Cave are
MID-GAME techniques: they are shapes that appear on an arbitrary stack at an arbitrary time, so
there is no board to compare against and no lock count to sample at. What is transcribable about
them is their GEOMETRY — a plugged well with a four-deep cavity under it, a floating T-Spin Double
over a three-wide cave — plus the boards harddrop itself draws to show the geometry holding and,
crucially, NOT holding.

So this file ships CONTROLS, not fields. Each technique carries positive boards the geometry must
fire on and the page's own negative board it must reject. A detector that cannot be run against a
board the wiki itself labels "a case where an S donation does not work" is a detector nobody has
falsified.

WHAT A BAD TRANSCRIPTION WOULD BREAK. These boards are the only external oracle a shape detector
has. Get a cell wrong and the detector is tuned against a board harddrop never drew — the gate goes
green, the metric is measured against this repo's own drawing, and the dual-source argument the
whole project rests on is quietly replaced by a tautology. That is the same failure the golden-data
rule exists to prevent, which is why `extract()` LOCATES every control by matching its cells against
the fetched page and dies if the page no longer draws it, rather than trusting the strings below.

THE CLASS CONTROL, AND WHY IT IS THE ARTICLE'S OWN LIST. The ordering metric in the opener section
gets its control from `Category:Triple Double openers`, because that category IS the shape class
being measured. STMB Cave has no such category. Measured against the fetched category listings:

  Category:Mid-game T-Spin setups      63 pages, holds BOTH Donation and STMB Cave — but it is a
                                       WHEN, not a shape: Kaidan, Nuki and T-Spin Forecast are in it
                                       and share no geometry with a floating TSD
  Category:Back-to-Back T-Spin setups  38 pages, and STMB Cave IS NOT IN IT — a category that omits
                                       the technique cannot be that technique's class
  Category:Donation setups              2 pages, and the category page itself is a REDLINK (it does
                                       not exist); a class of two, one of which is the article, is
                                       self-reference, not a control

harddrop has no "floating T-Spin" category at all. So the defensible class is the one the STMB Cave
article draws itself: the six techniques its own "Variants, Other Uses, and Comparisons" section
names as things an STMB Cave can be confused with or is a case of. That list is quoted VERBATIM and
`extract()` asserts every sentence still appears on the page, because a class this repo paraphrased
would be a class chosen to fit the result — the exact objection the opener section's category
control exists to answer.

WHY THE SOURCE HTML IS NOT COMMITTED. The two articles are 2.4 MB of markup whose every cell is a
separate <img>; the transcription is a few KB. What is committed is the transcription plus each
page's sha256 and oldid, so a re-fetch either reproduces the file byte for byte or names the page
that changed. Re-fetching needs network and is therefore NOT a CI gate; what CI runs is `verify()`,
which is offline and replays every control's T placement to check the geometry it claims.

A NOTE ON WHAT `boards()` DROPS. It rejects any diagram holding a `PTet` (the piece being placed) or
a digit cell, because those are annotations rather than occupancy. On the Donation page that drops
4 of 92 tables — and those 4 are the only diagrams that draw the T explicitly. Every board here is
therefore the field WITHOUT the T, and the T placement is carried alongside in `t_cells` so a
consumer can replay it. `verify()` does exactly that.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from .extract_wiki_openers import (
    EMPTY,
    WIDTH,
    boards,
    cells_of,
    has_full_row,
    mirror,
    occupancy,
    trim,
)

HERE = Path(__file__).resolve().parent
OUT = HERE / 'wiki-tspin-techniques.json'

OLDID = re.compile(r'oldid=(\d+)')
#: the "Categories:" footer of an article
CATLINKS = re.compile(r'<div id="mw-normal-catlinks".*?</div>', re.S)
CAT_NAME = re.compile(r'title="Category:([^"(]*?)(?: \(page does not exist\))?">')
#: a category listing's own count, e.g. "The following 63 pages are in this category, out of 63 total"
CAT_DECLARES = re.compile(
    r'The following ([\d,]+) pages? (?:are|is) in this category, out of ([\d,]+) total')
CAT_MEMBER = re.compile(r'<li><a href="[^"]*" title="([^"]*)">')


def _text(html: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html)).strip()


# ── geometry, replayed rather than asserted ────────────────────────────────────────────────────
def is_t_shape(cells: list[list[int]]) -> bool:
    """Four cells forming a T tetromino: three in a row, plus a nub on the middle one.

    Checked rather than assumed because a `t_cells` list is hand-transcribed from a drawing, and a
    typo that moves the nub off centre produces a shape no T can make — which would make every
    "this placement clears two rows" figure below a claim about a piece that does not exist.

    Only the two FLAT orientations are accepted, because every control here is a T-Spin Double or
    Single whose T lies on its side. A vertical T (three cells in a column) is rejected, so adding
    such a control fails this check loudly rather than being scored by a shape test that never
    considered it — the safe direction for a rule that exists to catch transcription slips.
    """
    if len(cells) != 4:
        return False
    by_row: dict[int, list[int]] = {}
    for c, r in cells:
        by_row.setdefault(r, []).append(c)
    if len(by_row) != 2:
        return False
    (ra, ca), (rb, cb) = sorted((r, sorted(cs)) for r, cs in by_row.items())
    if rb != ra + 1:
        return False
    for flat, nub in ((ca, cb), (cb, ca)):
        if len(flat) == 3 and len(nub) == 1 and flat == [flat[0], flat[0] + 1, flat[0] + 2]:
            return nub[0] == flat[1]
    return False


def place(rows: list[str], cells: list[list[int]]) -> list[str] | None:
    """Drop a T onto the board. `None` if any cell is off the board or already occupied."""
    grid = [list(r) for r in rows]
    for c, r in cells:
        if not (0 <= r < len(grid) and 0 <= c < WIDTH) or grid[r][c] != EMPTY:
            return None
        grid[r][c] = 'T'
    return [''.join(r) for r in grid]


def cleared(rows: list[str]) -> int:
    return sum(1 for r in rows if all(c != EMPTY for c in r))


def well_cavity(rows: list[str], col: int) -> int | None:
    """Empty cells under the lowest filled cell of `col`, or None if that column is not a well.

    "Not a well" means either nothing is filled in the column, or the space under the lowest filled
    cell is not contiguous — a second plug further down would make "cavity 4" describe two separate
    holes, and the donation's whole point is that ONE hole is plugged and reopened.
    """
    filled = [r for r in range(len(rows)) if rows[r][col] != EMPTY]
    if not filled:
        return None
    below = range(max(filled) + 1, len(rows))
    if any(rows[r][col] != EMPTY for r in below):
        return None
    return len(below)


def walled(rows: list[str], col: int, depth: int) -> bool:
    """Both neighbours of the well are filled across its deepest `depth` cavity rows.

    Without this, "a four-deep cavity" is satisfied by an open shaft on the edge of a stack, which
    is not a Tetris well at all — it is the outside of the board.
    """
    rows_below = list(range(len(rows) - depth, len(rows)))
    for r in rows_below:
        for n in (col - 1, col + 1):
            if 0 <= n < WIDTH and rows[r][n] == EMPTY:
                return False
    return True


def cave_under_nub(rows: list[str], cells: list[list[int]]) -> tuple[int, int] | None:
    """The contiguous empty run in the row beneath the T's nub, as (first_col, width).

    This is what makes an STMB Cave *floating*: the T-Spin Double is not resting on the stack, it is
    suspended over a gap. The row is found from the nub rather than declared, so a transcription
    cannot label a board with a cave it does not have.
    """
    nub = max(cells, key=lambda cr: cr[1])
    r = nub[1] + 1
    if r >= len(rows):
        return None
    row = rows[r]
    if row[nub[0]] != EMPTY:
        return None
    lo = hi = nub[0]
    while lo > 0 and row[lo - 1] == EMPTY:
        lo -= 1
    while hi + 1 < WIDTH and row[hi + 1] == EMPTY:
        hi += 1
    return lo, hi - lo + 1


# ── what to take from each page ────────────────────────────────────────────────────────────────
# Every `rows` below is asserted to appear on the fetched page, so this table is a LOCATOR, not a
# source. `t_cells` is (col, row) and cannot be located — the diagrams that draw the T use `PTet`
# annotation cells and are dropped by `boards()` — so it is transcribed by eye and then REPLAYED by
# `verify()`, which is what turns it back into a checkable statement.
DONATION_CONTROLS: list[dict] = [
    {
        'name': 'S Donation', 'kind': 'positive', 'spin': 'double', 'heading': 'Natural Donations',
        'rows': ['...J......', 'GGGJJJ..S.', 'GGGGG...SS', 'GGGGGG.GGS',
                 'GGGGGGGGG.', 'GGGGGGGGG.', 'GGGGGGGGG.', 'GGGGGGGGG.'],
        't_cells': [[5, 2], [6, 2], [7, 2], [6, 3]], 'well_col': 9,
    },
    {
        'name': 'J Donation', 'kind': 'positive', 'spin': 'double', 'heading': 'Natural Donations',
        'rows': ['...OO.....', 'GGGOO.....', 'GGGG...JJJ', 'GGGGG.GGGJ',
                 'GGGGGGGGG.', 'GGGGGGGGG.', 'GGGGGGGGG.', 'GGGGGGGGG.'],
        't_cells': [[4, 2], [5, 2], [6, 2], [5, 3]], 'well_col': 9,
    },
    {
        'name': 'O Donation', 'kind': 'positive', 'spin': 'double', 'heading': 'Natural Donations',
        'rows': ['....SS....', 'GGGSS...OO', 'GGGGGG.GOO', 'GGGGGGGGG.',
                 'GGGGGGGGG.', 'GGGGGGGGG.', 'GGGGGGGGG.'],
        't_cells': [[5, 1], [6, 1], [7, 1], [6, 2]], 'well_col': 9,
    },
    # ── the minimal pair ───────────────────────────────────────────────────────────────────────
    # These last two boards are drawn one after the other in "T-Spin Single Donations" and differ
    # by EXACTLY ONE CELL — (4, 2), filled in the first and empty in the second. The first clears a
    # row; the second, which the page captions "A case where an S donation does not work:", clears
    # nothing. That one cell is the whole control: a detector keyed on the T's own four cells, or
    # on the S plug, or on the well, sees two identical boards and calls them both donations. Only
    # a detector that checks the row actually fills can tell them apart, and this pair is the
    # cheapest possible proof that it does. `near_miss` below pins the one-cell distance so the
    # pair cannot silently drift into two unrelated boards.
    {
        'name': 'S Donation (T-Spin Single)', 'kind': 'positive', 'spin': 'single',
        'heading': 'T-Spin Single Donations',
        'rows': ['.......OO.', '.......OO.', 'GGGGG...SS', 'GGGGGG.SS.',
                 'GGGGGGGGG.', 'GGGGGGGGG.', 'GGGGGGGGG.', 'GGGGGGGGG.'],
        't_cells': [[5, 2], [6, 2], [7, 2], [6, 3]], 'well_col': 9,
    },
    {
        'name': 'S Donation (does not work)', 'kind': 'negative', 'spin': None,
        'heading': 'T-Spin Single Donations',
        'rows': ['.......OO.', '.......OO.', 'GGGG....SS', 'GGGGGG.SS.',
                 'GGGGGGGGG.', 'GGGGGGGGG.', 'GGGGGGGGG.', 'GGGGGGGGG.'],
        't_cells': [[5, 2], [6, 2], [7, 2], [6, 3]], 'well_col': None,
        # harddrop draws the outcome itself, as its own diagram with literal T cells. So this T
        # placement is LOCATED on the page rather than transcribed by eye: `verify()` replays the
        # four cells onto the board above and requires the result to equal the drawing below.
        # Neither row fills — the stack is one cell short at row 2 and the well is open at row 3.
        't_drawn': ['.......OO.', '.......OO.', 'GGGG.TTTSS', 'GGGGGGTSS.',
                    'GGGGGGGGG.', 'GGGGGGGGG.', 'GGGGGGGGG.', 'GGGGGGGGG.'],
    },
]

#: The two "T-Spin Single Donations" boards above, and the caption that makes the second a control.
NEAR_MISS = {
    'works': 'S Donation (T-Spin Single)',
    'fails': 'S Donation (does not work)',
    'says': 'A case where an S donation does not work:',
    'differing_cells': [[4, 2]],
}

STMB_CONTROLS: list[dict] = [
    {
        'name': 'Z base, S overhang', 'kind': 'positive', 'heading': 'Basic Structures',
        'rows': ['....Z.....', '...ZZ.....', 'GGGZ...SSG', 'GGGGG.SSGG',
                 'GGGGG...GG', 'GGGGG...GG'],
        't_cells': [[4, 2], [5, 2], [6, 2], [5, 3]],
    },
    {
        'name': 'O tower, S overhang', 'kind': 'positive', 'heading': 'Basic Structures',
        'rows': ['...OO.....', '...OO.....', 'GGGG...SSG', 'GGGGG.SSGG',
                 'GGGGG...GG', 'GGGGG...GG'],
        't_cells': [[4, 2], [5, 2], [6, 2], [5, 3]],
    },
    {
        'name': 'O tower, Z overhang (mirrored)', 'kind': 'positive', 'heading': 'Basic Structures',
        'rows': ['........OO', '........OO', 'GGGGZZ...G', 'GGGGGZZ.GG',
                 'GGGGG...GG', 'GGGGG...GG'],
        't_cells': [[6, 2], [7, 2], [8, 2], [7, 3]],
    },
    {
        # The page's "Even without S/Z ... Commonly L, J and I" case. It is in the control set
        # because it is the one positive whose base is neither S nor Z: a detector keyed on the
        # base PIECE rather than on the cave GEOMETRY passes the other three and fails this one.
        'name': 'L and I base, Z overhang', 'kind': 'positive', 'heading': 'Basic Structures',
        'rows': ['.......ZZ.', 'GIIII...ZZ', 'GGGLLL.GGG', 'GGGL...GGG',
                 'GGGG...GGG', 'GGGG...GGG'],
        't_cells': [[5, 1], [6, 1], [7, 1], [6, 2]],
    },
    {
        # The page draws each setup in two steps: the base alone, then the base with the overhang
        # that closes the cave. This is the FIRST step of the very first positive above — the same
        # Z base over the same 3-wide gap, with nothing over it. No T fits, so it is not a floating
        # T-Spin Double, and it is the negative the positives need: everything a base-piece or
        # cave-width test looks at is already present here. Only the overhang is missing.
        'name': 'Z base, no overhang yet', 'kind': 'negative', 'heading': 'Basic Structures',
        'rows': ['....Z.....', '...ZZ.....', 'GGGZ.....G', 'GGGGG...GG',
                 'GGGGG...GG', 'GGGGG...GG'],
        't_cells': None,
    },
]

#: The class control. Every string is quoted verbatim from the STMB Cave article's "Variants, Other
#: Uses, and Comparisons" section and asserted to still be there by `extract()`.
CONFUSABLE: list[dict] = [
    {
        'technique': 'Cut copy',
        'says': 'Compare these variations of STMB Cave below with Cut copy. By definition, Cut copy '
                'is a technique where one invests a T shape underneath a T-Spin Double and the '
                'overhang for the second T-Spin could be placed beforehand for two consecutive '
                'T-Spin Doubles.',
    },
    {
        'technique': 'Shachiku Train',
        'says': 'Compare this variation of STMB Cave below with Shachiku Train. Although this '
                'variation uses a floating T-Spin Double over 3 columns wide hole, this still has '
                'the same shape and steps as Shachiku Train.',
    },
    {
        'technique': 'Sky Prop',
        'says': 'Compare these variations of STMB Cave below with Sky Prop. On some cases, STMB '
                'Cave is just Sky Prop but with 3 columns wide hole.',
    },
    {
        'technique': 'Kaidan',
        'says': 'Compare this variation of STMB Cave below with Kaidan. On these kinds of terrain, '
                'one could choose either one of these techniques depending on their NEXT queue '
                'after the T-Spin Double or the terrain left over after the T-Spin Double.',
    },
    {
        'technique': 'Bennxt Prop',
        'says': 'It is moderately hard to spot the opportunity, but one could make a T-Spin Double '
                'cut T-Spin Double by using STMB Cave. One can also cut more than a one T-Spin '
                'Double. This technique is called Bennxt Prop, named after the player who '
                'introduced it.',
    },
    {
        # the one sentence that ties the two pages in this file together
        'technique': 'Pelican Opener',
        'says': 'An STMB Cave could be used along with Donation T-Spin Double for effective usage '
                'of pieces. As similarly seen in the Pelican Opener shown.',
    },
]

#: Categories fetched as EVIDENCE for the paragraph above, not as controls. Each is recorded with
#: what disqualifies it, and `verify()` re-checks the disqualifying fact rather than the prose.
CATEGORY_EVIDENCE: list[dict] = [
    {
        'name': 'Mid-game T-Spin setups', 'page': 'Category_Mid-game_T-Spin_setups',
        'holds': ['Donation', 'STMB Cave'],
        'verdict': 'too broad — a WHEN, not a shape; 63 pages including Kaidan, Nuki and T-Spin '
                   'Forecast, which share no geometry with a floating T-Spin Double',
    },
    {
        'name': 'Back-to-Back T-Spin setups', 'page': 'Category_Back-to-Back_T-Spin_setups',
        'holds': ['Donation'],
        'verdict': 'does not contain STMB Cave at all — a category that omits the technique cannot '
                   'be that technique\'s class',
    },
    {
        'name': 'Donation setups', 'page': 'Category_Donation_setups',
        'holds': ['Donation', 'Triple Donation Double Attack Setups'],
        'verdict': 'a class of two whose category page is a redlink; one of the two IS the article, '
                   'so quoting it as a control would be self-reference',
    },
]

#: The revisions this file was transcribed from, pinned as literals so `verify()` has something to
#: check the JSON's own provenance block AGAINST. Without this the block is self-consistent by
#: construction — `extract()` writes the hash and `verify()` reads the hash it wrote — and a
#: re-transcription against a page harddrop had since edited would rewrite every board and every
#: figure, print OK, and leave nothing anywhere saying the source had moved. These three numbers
#: per page were verified twice, from the fetched bytes, before being written down. A legitimate
#: re-fetch of a NEWER revision is supposed to fail here: bump these deliberately, having read the
#: page's diff, rather than letting a silent update through.
PINNED_PROVENANCE: dict[str, dict] = {
    'Donation': {
        'oldid': 37456, 'bytes': 1481953,
        'sha256': 'a601102d15885aae6cc5c2a90a8d1f43de263fd4e437a96c63e4e5b4a7dc4863',
    },
    'STMB_Cave': {
        'oldid': 41496, 'bytes': 952341,
        'sha256': '4345eff6296e30a56171033819ff859b888a094817867f1f38d92278fd5cc05f',
    },
}

TECHNIQUES: list[dict] = [
    {
        'key': 'donation', 'wiki': 'Donation', 'page': 'Donation',
        'definition': 'Donating is a method of "plugging" up the Tetris hole to send a T-Spin.',
        'also_says': 'After the T-Spin, the Tetris hole is opened up once again to allow the '
                     'continuation of Tetris or downstacking.',
        'controls': DONATION_CONTROLS,
        'geometry': {'cavity_cells': 4, 'walled_deepest_rows': 4},
    },
    {
        'key': 'stmb_cave', 'wiki': 'STMB Cave', 'page': 'STMB_Cave',
        'definition': 'An STMB Cave is a floating T-Spin Double setup.',
        'also_says': 'It is typically created over a 3-wide gap using an S or Z piece as its base.',
        'controls': STMB_CONTROLS,
        # `min_width` is READ OUT of `also_says` ("over a 3-wide gap"), which is why that sentence
        # is quoted and asserted rather than summarised — the number has to keep its source.
        'geometry': {'min_width': 3},
    },
]


# ── transcription ──────────────────────────────────────────────────────────────────────────────
def _read(html_dir: Path, name: str) -> str:
    p = html_dir / f'raw-{name}.html'
    if not p.exists():
        raise SystemExit(
            f'missing {p}. Fetch the page first, e.g.\n'
            f'  firecrawl scrape "https://harddrop.com/wiki/{name.replace("Category_", "Category:")}" '
            f'--format rawHtml -o {html_dir}/raw-{name}.html')
    return p.read_text(encoding='utf8', errors='replace')


def _provenance(name: str, html: str) -> dict:
    ids = OLDID.findall(html)
    return {
        'page': name.replace('Category_', 'Category:'),
        'url': f'https://harddrop.com/wiki/{name.replace("Category_", "Category:")}',
        'oldid': int(max(ids, key=int)) if ids else None,
        'sha256': hashlib.sha256(html.encode('utf8', 'replace')).hexdigest(),
        'bytes': len(html),
    }


def _locate(html: str, control: dict, key: str) -> int:
    """Index (1-based, within the page's kept diagrams) of the board this control transcribes.

    Matching is on the drawn CELLS, not on occupancy and not on position, and exactly one match is
    required. Position would break the moment harddrop inserts a diagram; occupancy alone would let
    two different pieces building the same silhouette stand in for each other, and for STMB Cave the
    base piece is the thing the page's own text is about.
    """
    want = trim(control['rows'])
    hits = [i for i, b in enumerate(boards(html), 1) if trim(b['rows']) == want]
    if len(hits) != 1:
        raise SystemExit(
            f'{key}/{control["name"]}: found {len(hits)} diagrams matching this board, expected 1. '
            f'The wiki page changed — read it, then update the control deliberately rather than '
            f'relaxing the match.')
    return hits[0]


def _quoted(html: str, text: str, where: str) -> None:
    if text not in _text(html):
        raise SystemExit(
            f'{where}: this sentence is no longer on the page, so it is no longer a quotation:\n'
            f'  {text}')


def _category(html_dir: Path, spec: dict) -> dict:
    html = _read(html_dir, spec['page'])
    body = html[html.find('mw-pages'):]
    members = [m for m in CAT_MEMBER.findall(body) if not m.startswith('Category:')]
    d = CAT_DECLARES.search(html)
    declares = int(d.group(1).replace(',', '')) if d else None
    if declares is not None and declares != len(members):
        raise SystemExit(
            f'{spec["name"]}: the page declares {declares} members but {len(members)} were '
            f'scraped. Read the listing before adjusting the scrape.')
    for name in spec['holds']:
        if name not in members:
            raise SystemExit(f'{spec["name"]}: expected member {name!r} is not in the listing')
    return {
        'name': spec['name'],
        'url': f'https://harddrop.com/wiki/Category:{spec["page"].replace("Category_", "")}',
        'declares': declares,
        'members': len(members),
        'holds_donation': 'Donation' in members,
        'holds_stmb_cave': 'STMB Cave' in members,
        'verdict': spec['verdict'],
        'provenance': _provenance(spec['page'], html),
    }


def extract(html_dir: Path) -> dict:
    out: dict = {
        'schema': 'wiki-tspin-techniques/1',
        'source': 'harddrop.com/wiki',
        'why': 'a Donation and an STMB Cave are mid-game geometries, not opening fields, so what is '
               'transcribable is the shape plus the boards harddrop draws it holding and not '
               'holding; the negative controls are the only external falsification a shape detector '
               'has',
        'cell_legend': {'.': 'empty', '#': 'occupied (occupancy view)', 'T': 'the placed T',
                        'IJLOSTZ': 'that piece as drawn', 'G': 'grey — any piece'},
        'coordinates': 't_cells are [col, row]; row 0 is the top row of `rows` as stored',
        'provenance': [],
    }

    for spec in TECHNIQUES:
        html = _read(html_dir, spec['page'])
        prov = _provenance(spec['page'], html)
        pin = PINNED_PROVENANCE[spec['page']]
        drift = {k: (prov[k], v) for k, v in pin.items() if prov[k] != v}
        if drift:
            raise SystemExit(
                f'{spec["page"]}: the fetched page is not the pinned revision — '
                + '; '.join(f'{k} is {got!r}, pinned {want!r}' for k, (got, want) in drift.items())
                + '. Read the page\'s diff, then bump PINNED_PROVENANCE deliberately: every board '
                  'and every figure below is transcribed from the pinned revision.')
        out['provenance'].append(prov)
        _quoted(html, spec['definition'], f'{spec["key"]}: definition')
        _quoted(html, spec['also_says'], f'{spec["key"]}: also_says')

        cats = CATLINKS.search(html)
        categories = CAT_NAME.findall(cats.group(0)) if cats else []

        controls = []
        for c in spec['controls']:
            rows = trim(c['rows'])
            index = _locate(html, c, spec['key'])
            if c['heading'] != boards(html)[index - 1]['heading']:
                raise SystemExit(
                    f'{spec["key"]}/{c["name"]}: drawn under '
                    f'{boards(html)[index - 1]["heading"]!r}, not {c["heading"]!r}')
            entry = {
                'name': c['name'], 'kind': c['kind'], 'heading': c['heading'],
                'diagram_index': index, 'rows': rows, 'occupancy': occupancy(rows),
                'cells': cells_of(rows), 't_cells': c['t_cells'],
            }
            if c['t_cells'] is not None:
                placed = place(rows, c['t_cells'])
                entry['clears'] = cleared(placed) if placed else None
            else:
                entry['clears'] = 0
            if c.get('t_drawn'):
                # the page draws the outcome; require our replay to reproduce it, and require the
                # drawing to be a diagram that is really there
                drawn = trim(c['t_drawn'])
                if place(rows, c['t_cells']) != drawn:
                    raise SystemExit(
                        f'{spec["key"]}/{c["name"]}: replaying t_cells does not reproduce the '
                        f"page's own drawing of the placement")
                entry['t_drawn'] = drawn
                entry['t_drawn_index'] = _locate(html, {'rows': drawn, 'name': c['name']},
                                                 spec['key'])
            if spec['key'] == 'donation':
                entry['spin'] = c['spin']
                entry['well_col'] = c['well_col']
                entry['cavity'] = (None if c['well_col'] is None
                                   else well_cavity(rows, c['well_col']))
            else:
                cave = (None if c['t_cells'] is None else cave_under_nub(rows, c['t_cells']))
                entry['cave_first_col'] = None if cave is None else cave[0]
                entry['cave_width'] = None if cave is None else cave[1]
            controls.append(entry)

        block = {
            'wiki': spec['wiki'],
            'url': f'https://harddrop.com/wiki/{spec["page"]}',
            'definition': spec['definition'],
            'also_says': spec['also_says'],
            'categories': categories,
            'controls': controls,
        }
        block.update(spec['geometry'])
        if spec['key'] == 'donation':
            _quoted(html, NEAR_MISS['says'], 'donation: near_miss caption')
            block['near_miss'] = dict(NEAR_MISS)
        if spec['key'] == 'stmb_cave':
            for c in CONFUSABLE:
                _quoted(html, c['says'], f'confusable/{c["technique"]}')
            block['confusable'] = {
                'why': 'harddrop has no "floating T-Spin" category; Mid-game T-Spin setups is a '
                       'WHEN rather than a shape, Back-to-Back T-Spin setups does not contain STMB '
                       'Cave, and Donation setups is a two-member redlink — so the defensible class '
                       'is the one the article names itself',
                'source_section': 'Variants, Other Uses, and Comparisons',
                'techniques': [c['technique'] for c in CONFUSABLE],
                'says': CONFUSABLE,
                'category_evidence': [_category(html_dir, s) for s in CATEGORY_EVIDENCE],
            }
        out[spec['key']] = block

    return out


# ── verification (offline; this is what CI runs) ───────────────────────────────────────────────
def verify(data: dict) -> list[str]:
    """Offline consistency. Returns a list of problems; empty means the file is sound."""
    bad: list[str] = []
    declared = {s['key']: s for s in TECHNIQUES}
    if set(declared) - set(data):
        bad.append(f'missing technique block(s): {sorted(set(declared) - set(data))}')

    seen: list[tuple[str, tuple[str, ...]]] = []
    for key, spec in declared.items():
        block = data.get(key)
        if not block:
            continue
        if not block.get('controls'):
            bad.append(f'{key}: no controls')
        kinds = {c['kind'] for c in block.get('controls', [])}
        for want in ('positive', 'negative'):
            if want not in kinds:
                bad.append(f'{key}: no {want} control — the geometry has never been falsified')

        for c in block.get('controls', []):
            where = f'{key}/{c["name"]}'
            rows = c['rows']
            if any(len(r) != WIDTH for r in rows):
                bad.append(f'{where}: a row is not {WIDTH} cells wide')
                continue
            if has_full_row(rows):
                bad.append(f'{where}: a full row would have cleared — not a board state')
            if rows and rows[0] == EMPTY * WIDTH:
                bad.append(f'{where}: board is not top-trimmed')
            if cells_of(rows) != c['cells']:
                bad.append(f'{where}: cell count disagrees with the drawing')
            if occupancy(rows) != c['occupancy']:
                bad.append(f'{where}: occupancy view disagrees with the drawing')
            seen.append((where, tuple(occupancy(rows))))

            placed = None
            if c['t_cells'] is not None:
                if not is_t_shape(c['t_cells']):
                    bad.append(f'{where}: t_cells are not a T tetromino')
                placed = place(rows, c['t_cells'])
                if placed is None:
                    bad.append(f'{where}: the T does not fit — a cell is occupied or off the board')
                elif cleared(placed) != c['clears']:
                    bad.append(f'{where}: replaying the T clears {cleared(placed)} row(s), '
                               f'not the {c["clears"]} recorded')
                if c.get('t_drawn') and placed != c['t_drawn']:
                    bad.append(f'{where}: replaying t_cells does not reproduce the page\'s own '
                               f'drawing of the placement')
            if c['kind'] == 'negative' and c['clears']:
                bad.append(f'{where}: the negative control clears {c["clears"]} row(s) — it is not '
                           f'a counterexample')
            if c['kind'] == 'positive' and not c['clears']:
                bad.append(f'{where}: the positive control clears nothing')

            if key == 'donation' and c['kind'] == 'positive':
                want = block['cavity_cells']
                depth = block['walled_deepest_rows']
                col = c['well_col']
                if col is None:
                    bad.append(f'{where}: a positive donation with no well column')
                    continue
                cav = well_cavity(rows, col)
                if cav != c['cavity']:
                    bad.append(f'{where}: column {col} has cavity {cav}, not the {c["cavity"]} '
                               f'recorded')
                # `cavity_cells` is the T-Spin DOUBLE donation's geometry — the four-deep Tetris
                # hole the technique is named for. The T-Spin Single donations plug a different
                # well (the page draws a five-deep one), so holding them to the same number would
                # be asserting a shape the page does not draw.
                if c['spin'] == 'double' and cav != want:
                    bad.append(f'{where}: column {col} has cavity {cav}, and a T-Spin Double '
                               f'donation plugs a {want}-deep well')
                if c['spin'] == 'double' and c['clears'] != 2:
                    bad.append(f'{where}: a T-Spin Double donation that clears {c["clears"]} rows')
                if c['spin'] == 'single' and c['clears'] != 1:
                    bad.append(f'{where}: a T-Spin Single donation that clears {c["clears"]} rows')
                if not walled(rows, col, depth):
                    bad.append(f'{where}: the well is not walled across its deepest {depth} '
                               f'cavity rows — an open shaft is not a well')
            if key == 'stmb_cave' and c['kind'] == 'positive':
                cave = cave_under_nub(rows, c['t_cells'])
                if cave is None:
                    bad.append(f'{where}: no cave under the T\'s nub — the T-Spin Double is not '
                               f'floating')
                    continue
                first, width = cave
                if [first, width] != [c['cave_first_col'], c['cave_width']]:
                    bad.append(f'{where}: the cave is {width} wide at column {first}, not the '
                               f'{c["cave_width"]} at {c["cave_first_col"]} recorded')
                if width < block['min_width']:
                    bad.append(f'{where}: the cave is {width} wide, under the '
                               f'{block["min_width"]}-wide gap the page describes')
                t_cols = {col for col, _ in c['t_cells']}
                if not (t_cols & set(range(first, first + width))):
                    bad.append(f'{where}: the cave does not sit under the T — columns '
                               f'{sorted(t_cols)} vs {list(range(first, first + width))}')

        # The minimal pair. If these two boards ever drift apart by more than the one cell the wiki
        # draws between them, the negative stops being a near miss and becomes just another board —
        # and "our detector rejects it" stops being evidence of anything.
        nm = block.get('near_miss')
        if key == 'donation':
            if not nm:
                bad.append(f'{key}: no near_miss — the negative control is not pinned to the '
                           f'board it differs from')
            else:
                by_name = {c['name']: c for c in block.get('controls', [])}
                works, fails = by_name.get(nm['works']), by_name.get(nm['fails'])
                if not works or not fails:
                    bad.append(f'{key}/near_miss: names a control that is not in the file')
                elif len(works['rows']) != len(fails['rows']):
                    bad.append(f'{key}/near_miss: the two boards are not the same height')
                else:
                    diff = [[c, r] for r in range(len(works['rows'])) for c in range(WIDTH)
                            if works['rows'][r][c] != fails['rows'][r][c]]
                    if diff != nm['differing_cells']:
                        bad.append(f'{key}/near_miss: the boards differ at {diff}, not at the '
                                   f'{nm["differing_cells"]} recorded')
                    if len(diff) != 1:
                        bad.append(f'{key}/near_miss: {len(diff)} cells apart — a near miss is one '
                                   f'cell, otherwise the negative proves nothing about the positive')
                    if works['clears'] == fails['clears']:
                        bad.append(f'{key}/near_miss: both boards clear {works["clears"]} row(s), '
                                   f'so the pair does not separate anything')

        prov = {p['page']: p for p in data.get('provenance', [])}
        p = prov.get(spec['page'])
        pin = PINNED_PROVENANCE[spec['page']]
        if not p:
            bad.append(f'{key}: no provenance for {spec["page"]}')
        else:
            for field, want in pin.items():
                if p.get(field) != want:
                    bad.append(f'{key}: provenance {field} for {spec["page"]} is {p.get(field)!r}, '
                               f'not the pinned {want!r} — this file was transcribed from a '
                               f'different revision than it claims')

    # a control set holding the same board twice, even mirrored, is one control wearing two names
    for i, (wa, oa) in enumerate(seen):
        for wb, ob in seen[i + 1:]:
            if oa == ob or tuple(mirror(list(oa))) == ob:
                bad.append(f'{wa} and {wb} are the same board up to mirroring')

    conf = data.get('stmb_cave', {}).get('confusable', {})
    names = conf.get('techniques') or []
    if not names:
        bad.append('the confusable class is empty — the STMB Cave metric has no control')
    for name in ('Sky Prop', 'Shachiku Train'):
        if name not in names:
            bad.append(f'{name} is missing from the confusable class — the control no longer '
                       f'covers the techniques the article compares itself against')
    if len(set(names)) != len(names):
        bad.append('the confusable class has a duplicate')
    if {c['technique'] for c in conf.get('says', [])} != set(names):
        bad.append('a confusable technique has no quoted sentence, or vice versa')

    ev = {e['name']: e for e in conf.get('category_evidence', [])}
    if not ev:
        bad.append('no category evidence — the reason a category is not the control is unsupported')
    b2b = ev.get('Back-to-Back T-Spin setups')
    if b2b and b2b['holds_stmb_cave']:
        bad.append('Back-to-Back T-Spin setups now contains STMB Cave, so the stated reason for '
                   'rejecting it as the class is no longer true')
    mid = ev.get('Mid-game T-Spin setups')
    if mid and not (mid['holds_stmb_cave'] and mid['holds_donation']):
        bad.append('Mid-game T-Spin setups no longer holds both techniques')
    for e in ev.values():
        if e['declares'] is not None and e['declares'] != e['members']:
            bad.append(f'{e["name"]}: declares {e["declares"]} members but records {e["members"]}')
    return bad


def selftest() -> int:
    """A verifier nothing can fail is decorative. Plant each defect it claims to catch."""
    if not OUT.exists():
        print(f'selftest: {OUT.name} does not exist — run --write first', file=sys.stderr)
        return 1
    if verify(json.loads(OUT.read_text())):
        print('selftest: the committed file does not verify — fix that first', file=sys.stderr)
        return 1

    def mutate(fn, label):
        d = json.loads(OUT.read_text())
        fn(d)
        if not verify(d):
            print(f'selftest FAILED: {label} was not caught', file=sys.stderr)
            return False
        print(f'  killed: {label}')
        return True

    def pos(d, key):
        return next(c for c in d[key]['controls'] if c['kind'] == 'positive')

    def widen_row(d):
        pos(d, 'donation')['rows'][0] += 'G'

    def fill_row(d):
        pos(d, 'donation')['rows'][0] = 'G' * WIDTH

    def untrim(d):
        c = pos(d, 'donation')
        c['rows'].insert(0, EMPTY * WIDTH)
        c['occupancy'].insert(0, EMPTY * WIDTH)

    def shallow_well(d):
        # cavity 4 -> 3, in isolation: drop the bottom row rather than plugging it, which would
        # also complete a row and let the full-row check take the kill instead
        c = pos(d, 'donation')
        c['cells'] -= cells_of(c['rows'][-1:])
        c['rows'].pop()
        c['occupancy'].pop()
        c['cavity'] -= 1

    def unwall_well(d):
        # open the wall beside the well on its deepest cavity row — an open shaft, not a well
        c = pos(d, 'donation')
        r = c['rows'][-1]
        i = c['well_col'] - 1
        c['rows'][-1] = r[:i] + EMPTY + r[i + 1:]
        c['occupancy'][-1] = occupancy([c['rows'][-1]])[0]
        c['cells'] -= 1

    def bad_cavity_note(d):
        pos(d, 'donation')['cavity'] += 1

    def move_nub(d):
        c = pos(d, 'donation')
        c['t_cells'][3] = [c['t_cells'][3][0] + 1, c['t_cells'][3][1]]

    def collide_t(d):
        c = pos(d, 'donation')
        c['t_cells'] = [[0, len(c['rows']) - 1], [1, len(c['rows']) - 1],
                        [2, len(c['rows']) - 1], [1, len(c['rows']) - 2]]

    def negative_that_clears(d):
        neg = next(c for c in d['donation']['controls'] if c['kind'] == 'negative')
        neg['clears'] = 2

    def drop_negative(d):
        d['stmb_cave']['controls'] = [c for c in d['stmb_cave']['controls']
                                      if c['kind'] != 'negative']

    def narrow_cave(d):
        # wall the cave in to 2 wide: the T-Spin Double is no longer over a 3-wide gap
        c = pos(d, 'stmb_cave')
        r = c['cave_first_col']
        row = len(c['rows']) - 1
        nub = max(c['t_cells'], key=lambda cr: cr[1])
        row = nub[1] + 1
        i = r if r != nub[0] else r + c['cave_width'] - 1
        c['rows'][row] = c['rows'][row][:i] + 'G' + c['rows'][row][i + 1:]
        c['occupancy'][row] = occupancy([c['rows'][row]])[0]
        c['cells'] += 1
        c['cave_width'] -= 1
        if i == r:
            c['cave_first_col'] += 1

    def bad_cave_note(d):
        pos(d, 'stmb_cave')['cave_width'] += 1

    def wrong_clears(d):
        pos(d, 'stmb_cave')['clears'] = 1

    def drop_confusable(d):
        conf = d['stmb_cave']['confusable']
        conf['techniques'] = [t for t in conf['techniques'] if t != 'Sky Prop']
        conf['says'] = [s for s in conf['says'] if s['technique'] != 'Sky Prop']

    def empty_confusable(d):
        d['stmb_cave']['confusable']['techniques'] = []
        d['stmb_cave']['confusable']['says'] = []

    def unquoted_confusable(d):
        d['stmb_cave']['confusable']['says'] = d['stmb_cave']['confusable']['says'][1:]

    def b2b_holds_stmb(d):
        ev = next(e for e in d['stmb_cave']['confusable']['category_evidence']
                  if e['name'] == 'Back-to-Back T-Spin setups')
        ev['holds_stmb_cave'] = True

    def miscount_category(d):
        d['stmb_cave']['confusable']['category_evidence'][0]['members'] += 1

    def drop_category_evidence(d):
        d['stmb_cave']['confusable']['category_evidence'] = []

    def duplicate_control(d):
        cs = d['stmb_cave']['controls']
        dup = json.loads(json.dumps(cs[0]))
        dup['name'] = 'a second name for the same board'
        cs.append(dup)

    def break_t_drawn(d):
        c = next(x for x in d['donation']['controls'] if x.get('t_drawn'))
        c['t_drawn'][0] = 'G' + c['t_drawn'][0][1:]

    def widen_near_miss(d):
        # push the two "T-Spin Single Donations" boards a second cell apart
        nm = d['donation']['near_miss']
        c = next(x for x in d['donation']['controls'] if x['name'] == nm['fails'])
        r = c['rows'][0]
        i = r.index(EMPTY)
        c['rows'][0] = r[:i] + 'G' + r[i + 1:]
        c['occupancy'][0] = occupancy([c['rows'][0]])[0]
        c['cells'] += 1

    def bad_near_miss_note(d):
        d['donation']['near_miss']['differing_cells'] = [[0, 0]]

    def drop_near_miss(d):
        del d['donation']['near_miss']

    def single_as_double(d):
        # relabel the T-Spin Single donation as a Double: its well is five deep, not four
        next(c for c in d['donation']['controls']
             if c.get('spin') == 'single')['spin'] = 'double'

    def bad_sha(d):
        d['provenance'][0]['sha256'] = 'nope'

    def bad_oldid(d):
        d['provenance'][0]['oldid'] = 'nope'

    def bad_bytes(d):
        d['provenance'][0]['bytes'] = 0

    def drop_technique(d):
        del d['stmb_cave']

    ok = all([
        mutate(widen_row, 'a board row that is not 10 cells wide'),
        mutate(fill_row, 'a full row (a state that would have cleared)'),
        mutate(untrim, 'a board that is not top-trimmed'),
        mutate(shallow_well, "a donation well one cell shallower than the page's four"),
        mutate(unwall_well, 'a donation well unwalled on its deepest cavity row'),
        mutate(bad_cavity_note, 'a recorded cavity depth the board does not have'),
        mutate(move_nub, "a T whose nub is off centre — not a tetromino"),
        mutate(collide_t, 'a T placed on cells that are already occupied'),
        mutate(negative_that_clears, 'a negative control recorded as clearing rows'),
        mutate(drop_negative, 'the negative control removed'),
        mutate(break_t_drawn, "a replay that no longer reproduces the page's drawn placement"),
        mutate(widen_near_miss, 'the minimal pair pushed two cells apart'),
        mutate(bad_near_miss_note, 'a recorded differing cell the boards do not differ at'),
        mutate(drop_near_miss, 'the minimal pair removed'),
        mutate(single_as_double, 'a T-Spin Single donation relabelled as a Double'),
        mutate(narrow_cave, 'an STMB cave narrowed to 2 wide'),
        mutate(bad_cave_note, 'a recorded cave width the board does not have'),
        mutate(wrong_clears, 'a clear count that replaying the T contradicts'),
        mutate(drop_confusable, 'Sky Prop dropped from the confusable class'),
        mutate(empty_confusable, 'the confusable class emptied'),
        mutate(unquoted_confusable, 'a confusable technique left without its quoted sentence'),
        mutate(b2b_holds_stmb, 'the Back-to-Back category recorded as containing STMB Cave'),
        mutate(miscount_category, "a category member count disagreeing with the page's own"),
        mutate(drop_category_evidence, 'the category evidence removed'),
        mutate(duplicate_control, 'the same board added twice under two names'),
        mutate(bad_sha, 'a malformed provenance sha256'),
        mutate(bad_oldid, 'a malformed provenance oldid'),
        mutate(bad_bytes, 'a zero provenance byte count'),
        mutate(drop_technique, 'a whole technique block removed'),
    ])
    print('selftest: all mutants killed' if ok else 'selftest: FAILED')
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or '').split('\n')[0])
    ap.add_argument('--html-dir', type=Path,
                    help='directory of raw-<Page>.html snapshots; required with --write')
    ap.add_argument('--write', action='store_true', help='rewrite wiki-tspin-techniques.json')
    ap.add_argument('--selftest', action='store_true', help='prove the verifier has teeth')
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    if args.write:
        if not args.html_dir:
            ap.error('--write needs --html-dir')
        data = extract(args.html_dir)
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(f'wrote {OUT.relative_to(HERE.parent.parent)}')
    else:
        data = json.loads(OUT.read_text())

    problems = verify(data)
    for spec in TECHNIQUES:
        block = data[spec['key']]
        pos = [c for c in block['controls'] if c['kind'] == 'positive']
        neg = [c for c in block['controls'] if c['kind'] == 'negative']
        geo = ', '.join(f'{k}={block[k]}' for k in spec['geometry'])
        print(f'  {spec["key"]:11s} {len(pos)} positive + {len(neg)} negative control(s)  {geo}')
        for c in block['controls']:
            if spec['key'] == 'donation':
                detail = (f'well col {c["well_col"]}, cavity {c["cavity"]}'
                          if c['well_col'] is not None else 'no well')
            else:
                detail = (f'cave {c["cave_width"]} wide at col {c["cave_first_col"]}'
                          if c['cave_width'] is not None else 'no cave')
            print(f'      {c["kind"]:8s} #{c["diagram_index"]:<3d} clears {c["clears"]}  '
                  f'{detail:32s} {c["name"]}')
    conf = data['stmb_cave']['confusable']
    print(f'  confusable class: {len(conf["techniques"])} techniques named by the article itself — '
          f'{", ".join(conf["techniques"])}')
    for e in conf['category_evidence']:
        print(f'      Category:{e["name"]:28s} {e["members"]:2d} pages, '
              f'STMB Cave {"in" if e["holds_stmb_cave"] else "ABSENT"}  — {e["verdict"][:48]}…')
    if problems:
        for p in problems:
            print(f'FAIL {p}', file=sys.stderr)
        return 1
    print('wiki-tspin-techniques.json OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

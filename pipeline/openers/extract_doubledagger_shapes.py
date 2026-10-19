"""Transcribe shiwehi.com's ダブルダガー (Double Dagger) page into `doubledagger-technique.json`.

    python3 -m pipeline.openers.extract_doubledagger_shapes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_doubledagger_shapes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_doubledagger_shapes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_doubledagger_shapes --html-dir <dir> --write  # ...and rewrite

The fourth MID-GAME TECHNIQUE page (中盤テンプレ・ドネイト), after STSD, STMB Cave and インペリアルクロス: two
TSD slots stacked one directly on top of the other, the upper one roofed by a two-cell overhang over its
left end. The T goes in laid FLAT, pointing down, into the upper slot — 「TSDを打つと、もう一度TSDを打てる形
が残ります」 — and its two cleared rows drop the overhang onto the lower slot, where it is the roof of the
second TSD. The page draws it once as drawn (the overhang left) and four times mirrored (the overhang right).

DECISION: the spin is a TSD (a full T-spin, 2 lines) and the anchor is the T's four cells — the T laid flat,
nub down, exactly as STMB Cave's. So the window predicate expresses it and the matcher (`technique-facts.ts`)
is untouched. The window is STSD's default, the BOUNDING BOX of the T, the roof above it and the follow-up
slot (rows 1-5, columns 2-5 of the spin board): no other drawing of the shape disagrees with the spin board
inside it, so the opt-in agreement box is not needed (it would also have reached the wall and the headroom
row, which the page draws as no part of the shape).

WHERE THE TRANSCRIPTION COMES FROM. `NODES` is a literal, hand-checked transcription of the page's RAW
HTML, fetched the way STSD's was: curl through the session proxy, TLS verification on, with a CA bundle
adding the Let's Encrypt YE2 intermediate shiwehi.com omits. Fourteen boards, plain text in
`<div class="ttt">`, one row per line, three of them ten or nine rows tall (the spec's `max_rows` is 10 for
that reason). The page is not committed; CI cannot fetch it.

THE PAGE DRAWS TWO BUILDS AND THREE FEATURES, and every board is transcribed: the basic form with its TSD
and what it leaves; built FROM A TSD SHAPE (a %J or %L into the slot's open corner and a %S or %Z roof on
the other side — usable only when the cell opposite the roof, the pink one, is empty) and FROM A CROSS (a %Z
laid on it; a %Z one column left builds インペリアルクロス instead, so that board is a miss); then the three
features: a TETRIS through a well under both slots (the slots do not shift sideways, unlike インペリアルクロス),
a LINE allowed between the two slots, and THREE or more stacked (マルチダガー).

WHAT THE WINDOW CAN DISCRIMINATE. Its rows 2-3 are the rows the TSD clears, so at a full TSD their filled
cells are entailed by the clear (NaiveClauseForced). What discriminates is the T's orientation (flat, nub
down: the lock anchors it), the overhang row above (the roof over the T's left end, the cell beside it
filled, the two cells over the rest of the T empty) and the two rows below: the lower slot, directly under
the upper one. The window does NOT reach the lower slot's far wall (column 6) — the bounding box stops at
the follow-up slot — so a hit says the lower slot is open, and the follow-up table says whether the second
TSD came.

WHAT THE WINDOW DOES NOT EXPRESS, measured and named rather than fitted (`not_expressed`): the page's own
second feature, a line between the two slots (`line.spin`). The window wants the lower slot directly under
the upper one; with the line row taken out the window fires on that drawing, mirrored, at the drawn T
(`extra_checks` measures both halves). The variant is the page's basic form; the line feature is a
different spacing of the same idea and is reported, not matched.

CROSS-SOURCES (both measured, both named):

  * harddrop's SDPC Spin page (another author, `sdpcspin-routes.json`): four of its second C-Spin build's
    bag-5 boards put the T "in the slot the build makes" directly on top of the C-Spin's own residue slot,
    the build's Z (or S) the overhang — the window fires on all four (one as drawn, three mirrored). No
    routes board is LABELLED ダブルダガー (the label pattern finds nothing), so `labelled_not_fired` is empty.
  * shiwehi.com's own インペリアルクロス page (the same author, `imperialcross-technique.json`): it draws this
    technique as its `dagger` board (a miss of its own window) and this page draws インペリアルクロス as its
    `cross.imperial` board. `extra_checks` measures both ways: this window fires once, mirrored, on that
    page's `dagger` and on none of its other boards, and that page's window fires once on `cross.imperial`
    and on none of this page's Double Dagger boards. Same author, so corroboration and not independence.

WHAT IS AN INFERENCE, flagged in the JSON (`reading`, the legend) rather than in prose only:

  * `B` (dark grey, #444444 in the page's renderer): on the basic form, cells the page leaves open (the
    spin board draws them empty); on the TSD-shape terrain, the cells the shape is built in (both T slots
    and the cells the %J goes into). Read as EMPTY on both; the window reads none where it fires.
  * `p` (pink, #ff33ff): the one cell opposite the roof that must be empty for the TSD-shape build — the
    page says so. Read as EMPTY; it is the cell the build's %J fills, and it lies outside the window, so the
    corpus window never tests it (`extra_checks` measures both).
  * upper-case `C`, `T` and `I` in a spin board: the cleared rows, muted (checked by the spin rule). Upper-
    case `C` on the two builds is in a row no spin clears: OUR READING, the stack the page tells the player
    to fill 「適当に」 (薄い灰色の部分は適当に埋めてください). The builds stand on DERIVED terrains (the build
    less its page pieces), and `extra_checks` measures that each is the drawn terrain plus those cells.
  * the two sentences that name the build pieces draw them as mino icons (`<span class="mino jmino">`), which
    the page's text drops; they are quoted as the text reads (`icons` lists what is missing) and not used as
    captions.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from pipeline.openers import technique_transcription as TT
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS
from pipeline.openers.route_transcription import EMPTY, bottom
from pipeline.openers.technique_transcription import node

HERE = Path(__file__).resolve().parent
OUT = HERE / 'doubledagger-technique.json'
IMPERIAL = HERE / 'imperialcross-technique.json'

ALPHABET = frozenset('-cCBTtjszpI')
#: the tallest board (the tetris feature) is ten rows
MAX_ROWS = 10


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/doubledagger.php',
    'title': 'ダブルダガー(Double Dagger)',
    'author': 'しゑひ(shiwehi)',
    'updated': '2020-06-20',
    'fetched': '2026-10-17',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle '
                    'that adds the Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), '
                    'the method STSD, STMB Cave, インペリアルクロス, 山岳積み2号 and stick spin used. The snapshot is '
                    'the page\'s raw HTML, byte for byte; every board is plain text in it, 14 ten-wide boards '
                    'in page order.',
    'snapshot_file': 'doubledagger.html',
    'snapshot_sha256': 'e768d2425624de15dd78c5acb6243880e96dc7d6bcbd87e0899fe14aad41dd1e',
    'snapshot_bytes': 25000,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable '
                     'in CI: the page is not committed and cannot be fetched there. Re-check with '
                     '--html-dir after any refetch; an HTML hash moves with ANY byte of the page (ads, '
                     'sidebar, a date), so a moved hash means "read the board diff", not "the boards '
                     'changed". Sentences are compared against the page with its tags dropped.',
    'renderer': {
        'url': 'https://shiwehi.com/tetris/mutual/column-exp.js?date=20210408',
        'read': '2026-10-19',
        'sha256': '95c431a4147f9c30fc0e1bae935e6af6f5669c3d2fa1edfc388848e69ab62570',
        'sha256_note': 'the same bytes STSD recorded, re-fetched for this page to read the pink cell\'s colour',
        'colorMap_used': {'c': '#a3a3a3', 'C': '#cccccc', 'B': '#444444', 'p': '#ff33ff', 'T': '#954dd8',
                          'I': '#4db1d8', 'j s z': '#0011ff #33ff00 #ff0000', '-': '#000000'},
        'mirror_button': 'body.reversed swaps j<->l, s<->z (and upper case); the page names %J or %L and %S or %Z',
    },
    'decorative_images': ['ダブルダガー(Double Dagger)タイトル画像'],
    'references': ['./imperialcross.php (インペリアルクロス, linked twice: the alternative build and the tetris feature)'],
    'unfetched': [],
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ',
    '-': 'empty',
    'c': 'a cell filled before this diagram (any piece, or garbage), grey',
    'j s z': 'a cell of that piece',
    'T': 'a cell of the T in a row the spin clears (muted; OUR READING, checked: every upper-case row is a full row)',
    'I': 'a cell of the I in a row the tetris clears (muted; checked the same way)',
    'C': 'on a spin board, an earlier cell in a row the spin clears (muted; checked the same way); on the two '
         'builds, in a row no spin clears, the stack the page tells the player to fill as they like (OUR READING)',
    'B': 'dark grey: on the basic form, a cell the page leaves open (the spin board draws it empty); on the '
         'TSD-shape terrain, a cell the shape is built in (OUR READING: read as EMPTY on both)',
    'p': 'pink: the cell opposite the roof that must be EMPTY for the TSD-shape build (the page says so); read '
         'as empty',
    '%X': 'the X piece',
}

QUOTES = [
    {'id': 'intro', 'verbatim': 'ここでは、ダブルダガー(Double Dagger)という、TSDを2回打つことができる'
                                '中盤テンプレについて紹介していきます。'},
    {'id': 'h.basic', 'verbatim': '基本形とラインの消し方'},
    {'id': 'basic', 'verbatim': '基本形は上図の通りです。'},
    {'id': 'spin', 'verbatim': 'ここから、TSDを打つと、もう一度TSDを打てる形が残ります。'},
    {'id': 'h.build', 'verbatim': '元地形からの組み方と特徴'},
    {'id': 'h.tsd', 'verbatim': 'TSD形からの組み方'},
    {'id': 'tsd', 'verbatim': '1つ目の組み方としては、既に完成されたTSDの形からやを置き、反対側にやで屋根を付ける方法です。',
     'icons': ['%J', '%L', '%S', '%Z'],
     'icons_note': 'the page draws the four pieces as mino icons (<span class="mino jmino"> and so on) in the four '
                   'gaps 「から_や_を置き、反対側に_や_で」; the text drops them. Not used as a caption.'},
    {'id': 'fill', 'verbatim': '薄い灰色の部分は適当に埋めてください。'},
    {'id': 'tsd.why', 'verbatim': 'TSDを打つ準備をしていたのに%Tが遅い場合などに組んでおくことでBack-to-backを狙えます。'},
    {'id': 'pink', 'verbatim': '屋根の反対側(ピンクマス)が埋まっていないときにのみ使えます。'},
    {'id': 'h.cross', 'verbatim': '十字形からの組み方'},
    {'id': 'cross', 'verbatim': '2つ目に、既に完成された十字形からやを乗せて作る方法です。',
     'icons': ['%S', '%Z'],
     'icons_note': 'the page draws the two pieces as mino icons in the gaps 「から_や_を乗せて」; the text drops them. '
                   'Not used as a caption.'},
    {'id': 'imperial', 'verbatim': 'ダブルダガーを組む代わりにインペリアルクロスを組むこともできます。'},
    {'id': 'h.feature', 'verbatim': '特徴'},
    {'id': 'tetris', 'verbatim': 'インペリアルクロスと異なり穴が左右にズレないので、下穴が直列で空いている場合に'
                                 'テトリスを打つことができる。'},
    {'id': 'line', 'verbatim': '2つのT-spinの間に邪魔にならなければラインが入っていても良い。'},
    {'id': 'multi', 'verbatim': '3つ以上重ねることもできる(マルチダガー(Multi Dagger))'},
]

NODES = [
    {'id': 'basic', 'kind': 'base', 'caption_quote': 'basic',
     'label': 'the basic form: two TSD slots stacked, the upper one roofed over its left end; the dark-grey cells are left open',
     'rows': _b('BBBB--BBBB BBcc--BBBB ccc---cccc cccc-ccccc ccc---cccc cccc-ccccc')},
    {'id': 'basic.spin', 'kind': 'spin', 'spin_of': 'basic', 'spin': 'TSD', 'lines': 2, 'caption_quote': 'spin',
     'label': 'the T laid flat, pointing down, into the upper slot: a TSD',
     'rows': _b('---------- --cc------ CCCTTTCCCC CCCCTCCCCC ccc---cccc cccc-ccccc')},
    {'id': 'basic.after', 'kind': 'after', 'after_of': 'basic.spin', 'caption_quote': 'spin',
     'label': 'what the TSD leaves: the overhang dropped onto the lower slot, a second TSD slot',
     'rows': _b('---------- ---------- ---------- --cc------ ccc---cccc cccc-ccccc')},
    {'id': 'tsd.terrain', 'kind': 'base', 'caption_quote': 'h.tsd',
     'label': 'the TSD shape: a finished TSD slot with a step beside it; dark grey where the shape is built',
     'rows': _b('---------- ---------- ---BBBB--- ccccBBB--- cccBBBcccc ccccBccccc')},
    {'id': 'tsd.sj', 'kind': 'build', 'on': 'tsd.sj.terrain', 'adds': 'sj', 'caption_quote': 'tsd.why',
     'label': 'a J stood into the corner and an S roof on the other side (the stack beside them drawn muted)',
     'rows': _b('---------- --ss--j--- Css---jCCC cccc-jjCCC ccc---cccc cccc-ccccc')},
    {'id': 'tsd.pink', 'kind': 'base', 'same_occupancy_as': 'tsd.terrain', 'caption_quote': 'pink',
     'label': 'the TSD shape again, the cell opposite the roof marked pink: it must be empty',
     'rows': _b('---------- ---------- ---------- cccc--p--- ccc---cccc cccc-ccccc')},
    {'id': 'cross.terrain', 'kind': 'base', 'caption_quote': 'h.cross', 'label': 'the cross shape, finished, no roof',
     'rows': _b('---------- ---------- ---------- cccc-ccccc ccc---cccc cccc-ccccc')},
    {'id': 'cross.z', 'kind': 'build', 'on': 'cross.z.terrain', 'adds': 'z', 'caption_quote': 'fill',
     'label': 'a Z laid over the cross\'s right arm: the overhang on the RIGHT, the page\'s mirrored hand',
     'rows': _b('---------- -----zz--- CCC---zzCC cccc-ccccc ccc---cccc cccc-ccccc')},
    {'id': 'cross.imperial', 'kind': 'build', 'on': 'cross.imperial.terrain', 'adds': 'z', 'caption_quote': 'imperial',
     'label': 'the Z one column left: インペリアルクロス, a different technique',
     'rows': _b('---------- ----zz---- CC---zzCCC cccc-ccccc ccc---cccc cccc-ccccc')},
    {'id': 'tetris.spin', 'kind': 'spin', 'spin_piece': 'I', 'spin': 'tetris', 'lines': 4, 'caption_quote': 'tetris',
     'label': 'a Double Dagger (mirrored) over a well in the same column: an I through the well, a tetris',
     'rows': _b('---------- -----cc--- ccc---cccc cccc-ccccc ccc---cccc cccc-ccccc '
                'CCCCICCCCC CCCCICCCCC CCCCICCCCC CCCCICCCCC')},
    {'id': 'tetris.after', 'kind': 'after', 'after_of': 'tetris.spin', 'caption_quote': 'tetris',
     'label': 'what the tetris leaves: the Double Dagger, untouched',
     'rows': _b('---------- ---------- ---------- ---------- ---------- -----cc--- ccc---cccc cccc-ccccc '
                'ccc---cccc cccc-ccccc')},
    {'id': 'line.spin', 'kind': 'spin', 'spin': 'TSD', 'lines': 2, 'caption_quote': 'line',
     'label': 'a line between the two slots (mirrored): the T into the upper slot, a TSD',
     'rows': _b('---------- ---------- ---------- -----cc--- CCCTTTCCCC CCCCTCCCCC ccc--ccccc ccc---cccc '
                'cccc-ccccc')},
    {'id': 'line.after', 'kind': 'after', 'after_of': 'line.spin', 'caption_quote': 'line',
     'label': 'what that TSD leaves: the overhang over the line, the lower slot under it',
     'rows': _b('---------- ---------- ---------- ---------- ---------- -----cc--- ccc--ccccc ccc---cccc '
                'cccc-ccccc')},
    {'id': 'multi', 'kind': 'base', 'caption_quote': 'multi',
     'label': 'three slots stacked (マルチダガー, mirrored), the third under a line',
     'rows': _b('---------- -----cc--- ccc---cccc cccc-ccccc ccc---cccc cccc-ccccc ccc--ccccc ccc---cccc '
                'cccc-ccccc')},
    # ── derived: drawn nowhere on the page ──
    {'id': 'tsd.sj.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'tsd.sj less its s and j: the TSD shape with the muted stack the page tells the player to fill',
     'rows': _b('---------- ---------- C------CCC cccc---CCC ccc---cccc cccc-ccccc')},
    {'id': 'cross.z.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'cross.z less its z: the cross with the muted stack on both sides of where the Z goes',
     'rows': _b('---------- ---------- CCC-----CC cccc-ccccc ccc---cccc cccc-ccccc')},
    {'id': 'cross.imperial.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'cross.imperial less its z: the cross with the muted stack on both sides of where the Z goes',
     'rows': _b('---------- ---------- CC-----CCC cccc-ccccc ccc---cccc cccc-ccccc')},
]

#: the variant's window, in basic.spin's frame
VARIANTS = [{
    'id': 'doubledagger', 'board': 'basic.spin', 'spin': 'TSD', 'lines': 2,
    'window': {'rows': [1, 5], 'cols': [2, 5]},
    't_cells': [[2, 3], [2, 4], [2, 5], [3, 4]],
    'roof_cells': [[1, 2], [1, 3]],
    'window_note': 'in basic.spin\'s frame, row 0 the top: the bounding box of the T, the overhang above it and the '
                   'follow-up slot. Rows 2-3 are the rows the TSD clears (entailed by the clear at a full TSD, '
                   'NaiveClauseForced); row 1 is the overhang (the roof over the T\'s left end and the cell beside it '
                   'filled, the two cells over the rest of the T empty); rows 4-5 are the lower slot, directly under '
                   'the upper one, with the wall behind it. The lower slot\'s far wall (column 6) and the headroom row '
                   'are outside. Occupancy only, never colour; garbage is filled.',
    'followup': {'board': 'basic.after', 'spin': 'TSD', 'lines': 2,
                 't_cells_pre_clear': [[4, 3], [4, 4], [4, 5], [5, 4]],
                 't_cells_after': [[4, 3], [4, 4], [4, 5], [5, 4]],
                 'note': 'the flat T into the lower slot, under the dropped overhang. It lies below the two cleared '
                         'rows, so the TSD does not move it; the matcher carries it through every later clear to the '
                         'next T.'},
    'fires_on': ['basic', 'tsd.sj'],
    #: the page's mirrored drawings: the window fires on each exactly once, mirrored (`extra_checks`; the
    #: shared rule (e) takes only as-drawn boards). Spin boards are read with their spin piece taken out.
    'fires_mirrored': ['cross.z', 'tetris.spin', 'tetris.after', 'multi'],
    'misses': ['tsd.terrain', 'tsd.pink', 'cross.terrain', 'cross.imperial', 'basic.after', 'line.after'],
    #: the page draws these as Double Daggers and the window does not fire on them: measured, not fitted
    'not_expressed': [
        {'board': 'line.spin', 'between_rows': [6],
         'reason': 'the page\'s second feature: a line between the two slots. The window wants the lower slot '
                   'directly under the upper one, so it does not fire; with the line row (row 6) taken out it '
                   'fires, mirrored, at the drawn T. A different spacing of the same idea, reported and not matched'},
    ],
}]

CROSS_SOURCE = {
    'kind': 'routes',
    'label_pattern': 'dagger',
    'note': 'the window, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot board '
            'of every committed *-routes.json, with the U cells as the T. `fires` is the independent drawer '
            '(harddrop\'s SDPC Spin page, another author): the T in the slot its second C-Spin build makes, '
            'directly on top of the C-Spin\'s residue slot, the build\'s Z or S the overhang. No routes board is '
            'labelled as this technique. The same author\'s インペリアルクロス page is checked in `technique_pages`.',
    'fires': [
        {'file': 'sdpcspin-routes.json', 'node': '3.second.cspin.first#2', 'variant': 'doubledagger', 'mirrored': False,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': 'harddrop\'s SDPC Spin, second C-Spin build, bag 5 first build: the T in the slot the build makes, '
                 'the Z overhang over its left end, the residue\'s slot directly under it'},
        {'file': 'sdpcspin-routes.json', 'node': '3.second.cspin.o_first#2', 'variant': 'doubledagger', 'mirrored': True,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': 'the same, O before L: the overhang over the right end (mirrored)'},
        {'file': 'sdpcspin-routes.json', 'node': '3.second.cspin.l_first#2', 'variant': 'doubledagger', 'mirrored': True,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': 'the same, L before O, the I at the right wall (mirrored)'},
        {'file': 'sdpcspin-routes.json', 'node': '3.second.cspin.l_first#4', 'variant': 'doubledagger', 'mirrored': True,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': 'the same, L before O, the I at column 6 (mirrored)'},
    ],
    'also': [],
    'labelled_not_fired': [],
    'technique_pages': {
        'file': 'imperialcross-technique.json',
        'page': 'https://shiwehi.com/tetris/template/imperialcross.php',
        'theirs_is_ours': {'node': 'dagger', 'mirrored': True,
                           'note': 'that page\'s 「インペリアルクロスを組む代わりにダブルダガーを組むこともできます」 board: '
                                   'this window fires on it once, mirrored, and on none of that page\'s other boards'},
        'ours_is_theirs': {'node': 'cross.imperial',
                           'note': 'this page\'s 「ダブルダガーを組む代わりにインペリアルクロスを組むこともできます」 board: '
                                   'that page\'s window fires on it once, and on none of this page\'s Double Dagger boards'},
        'independence': 'the same author (shiwehi.com) on both pages: corroboration, not an independent drawing',
    },
    'unfetched': ['https://harddrop.com/wiki/SDPC_Spin is read from sdpcspin-routes.json, not refetched here'],
}

KNOWN_DISCREPANCIES: list[dict] = []

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'doubledagger',
        'source': SOURCE,
        'terms': TERMS,
        'legend': LEGEND,
        'empty_letters': 'Bp',
        'quotes': QUOTES,
        'nodes': NODES,
        'page_order': PAGE_ORDER,
        'basic_form': [],
        'variants': VARIANTS,
        'cross_source': CROSS_SOURCE,
        'known_discrepancies': KNOWN_DISCREPANCIES,
    }


# ── technique-only rules ─────────────────────────────────────────────────────────────────────────
def _pre(n: dict) -> list[str]:
    """A board as the T went into it: a spin board with its spin piece taken out."""
    if n['kind'] != 'spin':
        return n['rows']
    p = n.get('spin_piece', 'T')
    return [''.join(EMPTY if ch in (p, p.lower()) else ch for ch in row) for row in n['rows']]


def _fires(data, v, spec, rows):
    return [(frozenset(cs), m) for cs in TT.t_placements(rows, spec) for m in (False, True)
            if TT.window_fires(data, v, spec, rows, cs, m)]


def _clears(rows, spec, cells) -> int:
    o = TT.occ_of(rows, spec)
    o = [''.join('#' if (r, c) in cells else ch for c, ch in enumerate(row)) for r, row in enumerate(o)]
    return len(TT.full_rows(o))


def _window_reads(data, v, spec, lock, mirrored):
    f = TT.frame_map(data, v, spec, set(lock), mirrored)
    (r0, r1), (c0, c1) = v['window']['rows'], v['window']['cols']
    return {f(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}


def extra_checks(data: dict):
    bad, measured = [], set()
    by = {n['id']: n for n in data['nodes']}
    v = data['variants'][0]
    # mirror: every mirrored drawing fires once, mirrored, at a placement clearing two rows
    for bid in v.get('fires_mirrored', []):
        if bid not in by:
            bad.append(f'mirror: fires_mirrored names no node {bid!r}')
            continue
        rows = _pre(by[bid])
        hits = _fires(data, v, SPEC, rows)
        if len(hits) != 1 or not hits[0][1]:
            bad.append(f'mirror: the window fires {len(hits)} time(s) on {bid}, not once mirrored')
        elif _clears(rows, SPEC, hits[0][0]) != 2:
            bad.append(f'mirror: the window fires on {bid} at a placement that does not clear two rows')
    listed = set(v.get('fires_on', [])) | set(v.get('fires_mirrored', [])) | set(v.get('misses', [])) \
        | {e['board'] for e in v.get('not_expressed', [])} | {v['board']}
    for n in data['nodes']:
        if not n.get('derived') and n['id'] not in listed:
            bad.append(f'mirror: drawn board {n["id"]} is in none of fires_on, fires_mirrored, misses, not_expressed')
    # line: a Double Dagger the page draws and the window does not express — measured both halves
    for e in v.get('not_expressed', []):
        n = by.get(e['board'])
        if n is None or not e.get('reason'):
            bad.append(f'line: not_expressed {e.get("board")!r} names no node or carries no reason')
            continue
        rows, sc = _pre(n), TT.spin_cells(n) if n['kind'] == 'spin' else set()
        cands = [sc] if sc else [set(cs) for cs in TT.t_placements(rows, SPEC)]
        if any(TT.window_fires(data, v, SPEC, rows, cs, m) for cs in cands for m in (False, True)) or _fires(data, v, SPEC, rows):
            bad.append(f'line: the window fires on {e["board"]}, listed as not expressed')
        cut = sorted(e.get('between_rows', []))
        less = [row for r, row in enumerate(rows) if r not in cut]
        shift = lambda cs: {(r - sum(1 for x in cut if x < r), c) for r, c in cs}
        if not cut or not sc or not all(TT.is_empty(ch, SPEC) or ch == 'c' for r in cut for ch in rows[r]):
            bad.append(f'line: {e["board"]}.between_rows {cut} are not rows of earlier cells under its spin')
        elif [(frozenset(cs), m) for cs, m in _fires(data, v, SPEC, less)] != [(frozenset(shift(sc)), True)]:
            bad.append(f'line: with rows {cut} taken out, the window does not fire once, mirrored, at {e["board"]}\'s T')
    # pink: the one cell that must be empty for the TSD-shape build is the build's J cell, outside the window
    pink = {(r, c) for r, row in enumerate(by['tsd.pink']['rows']) for c, ch in enumerate(row) if ch == 'p'}
    sj = by['tsd.sj']['rows']
    if len(pink) != 1 or len(by['tsd.pink']['rows']) != len(sj) or any(sj[r][c] != 'j' for r, c in pink):
        bad.append('pink: the pink cell is not one cell the build\'s J fills')
    else:
        hits = _fires(data, v, SPEC, sj)
        if len(hits) == 1 and pink & _window_reads(data, v, SPEC, hits[0][0], hits[0][1]):
            bad.append('pink: the window reads the pink cell (the corpus would test the build condition)')
    # B: the open cells are empty on the basic form's spin board; the TSD shape's are empty or the build's j
    spin = by['basic.spin']['rows']
    if any(ch == 'B' and spin[r][c] != EMPTY for r, row in enumerate(by['basic']['rows']) for c, ch in enumerate(row)):
        bad.append('B: a cell the basic form draws B is not empty on basic.spin')
    if any(ch == 'B' and sj[r][c] not in (EMPTY, 'j') for r, row in enumerate(by['tsd.terrain']['rows'])
           for c, ch in enumerate(row)):
        bad.append('B: a cell the TSD shape draws B is filled by something other than the build\'s J')
    for bid in v.get('fires_on', []):
        rows = by[bid]['rows']
        for cs, m in _fires(data, v, SPEC, rows):
            if any(rows[r][c] in 'Bp' for r, c in _window_reads(data, v, SPEC, cs, m)):
                bad.append(f'B: the window reads a dark-grey or pink cell where it fires on {bid}')
    # build: each derived terrain is the drawn terrain plus its muted cells, which lie above the slots
    for d, base in (('tsd.sj.terrain', 'tsd.terrain'), ('cross.z.terrain', 'cross.terrain'),
                    ('cross.imperial.terrain', 'cross.terrain')):
        less = [''.join(EMPTY if ch == 'C' else ch for ch in row) for row in by[d]['rows']]
        if bottom(TT.occ_of(less, SPEC), TT.MAX_ROWS) != bottom(TT.occ_of(by[base]['rows'], SPEC), TT.MAX_ROWS):
            bad.append(f'build: {d} less its C cells is not {base}')
        if any('C' in row for row in by[d]['rows'][-2:]):
            bad.append(f'build: {d} draws a C cell inside the lower slot\'s rows')
    # imperial: the two pages draw each other's technique, and each window fires on the other's drawing only
    ts = data['cross_source'].get('technique_pages')
    if not ts:
        bad.append('imperial: no technique_pages record')
    else:
        imp = json.loads((HERE / ts['file']).read_text())
        ispec = TT.TechniqueSpec(out=HERE / ts['file'], build=lambda: imp, alphabet=frozenset(),
                                 empty_letters=imp.get('empty_letters', ''), max_rows=MAX_ROWS)
        mine = []
        for n in imp['nodes']:
            hits = _fires(data, v, SPEC, _pre(n)) if not n.get('derived') else []
            if hits:
                mine.append((n['id'], [m for _cs, m in hits]))
        want = [(ts['theirs_is_ours']['node'], [ts['theirs_is_ours']['mirrored']])]
        if mine != want:
            bad.append(f'imperial: this window fires on {ts["file"]} boards {mine}, not {want}')
        iv = imp['variants'][0]
        theirs = []
        for n in data['nodes']:
            if n.get('derived'):
                continue
            rows = _pre(n)
            k = sum(1 for cs in TT.t_placements(rows, ispec) for m in (False, True)
                    if TT.window_fires(imp, iv, ispec, rows, cs, m))
            if k:
                theirs.append((n['id'], k))
        if theirs != [(ts['ours_is_theirs']['node'], 1)]:
            bad.append(f'imperial: that page\'s window fires on this page\'s boards {theirs}, '
                       f'not once on {ts["ours_is_theirs"]["node"]}')
        if ts['ours_is_theirs']['node'] not in v.get('misses', []):
            bad.append('imperial: this page\'s インペリアルクロス board is not one of the window\'s misses')
    return bad, measured


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='Bp',
    upper_groups={'T': 'merge', 'I': 'merge'}, max_rows=MAX_ROWS,
    extra_checks=extra_checks,
)


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def _set(rows, r, c, ch):
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _var(d):
    return d['variants'][0]


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'tsd.terrain')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: d['page_order'].reverse(), 'page_order swapped', 'grammar:'),
    (lambda d: node(d, 'basic.spin').__setitem__('spin_of', 'nowhere'), 'a dangling reference', 'grammar:'),
    (lambda d: d.__setitem__('empty_letters', 'B'), 'the pink cell no longer read as empty', 'grammar:'),
    (lambda d: _set(node(d, 'tsd.sj')['rows'], 5, 0, '-'), 'a build board cell flipped', 'build:'),
    (lambda d: _set(node(d, 'cross.z.terrain')['rows'], 2, 9, '-'), 'the derived terrain edited', 'build:'),
    (lambda d: _set(node(d, 'tsd.pink')['rows'], 4, 0, '-'), 'the pink board not the TSD shape', 'build:'),
    (lambda d: (_set(node(d, 'basic.spin')['rows'], 3, 4, 'C'), _set(node(d, 'basic.spin')['rows'], 1, 4, 't')),
     'the T pointing up', 'spin:'),
    (lambda d: _set(node(d, 'basic.spin')['rows'], 2, 0, 'c'), 'a cleared row drawn unmuted', 'spin:'),
    (lambda d: node(d, 'basic.spin').__setitem__('lines', 1), 'the spin\'s line count', 'spin:'),
    (lambda d: node(d, 'tetris.spin').__setitem__('lines', 3), 'the tetris\'s line count', 'spin:'),
    (lambda d: _set(node(d, 'basic.after')['rows'], 3, 4, 'c'), 'the after board not what the spin leaves', 'discrepancy:'),
    (lambda d: _set(node(d, 'tetris.after')['rows'], 9, 0, '-'), 'the tetris\'s after board edited', 'discrepancy:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [2, 6]), 'the window widened to the far wall', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [3, 5]), 'the window narrowed by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [2, 5]), 'the window without the overhang row', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [1, 3]), 'the window without the lower slot', 'window:'),
    (lambda d: _var(d)['roof_cells'].pop(), 'a roof cell unnamed', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('t_cells_after', [[3, 3], [3, 4], [3, 5], [4, 4]]),
     'the follow-up slot read a row too high', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('lines', 1), 'the follow-up line count', 'window:'),
    (lambda d: _var(d)['fires_on'].append('cross.z'), 'a mirrored build listed as firing as drawn', 'window:'),
    (lambda d: _var(d)['misses'].append('basic'), 'a board it fires on listed as a miss', 'window:'),
    (lambda d: _var(d)['fires_mirrored'].append('cross.imperial'), 'the インペリアルクロス build listed as firing', 'mirror:'),
    (lambda d: _var(d)['fires_mirrored'].remove('multi'), 'a drawn board in no list', 'mirror:'),
    (lambda d: _set(node(d, 'multi')['rows'], 1, 5, '-'), 'the multi board\'s roof removed', 'mirror:'),
    (lambda d: _var(d)['not_expressed'][0].__setitem__('between_rows', [7]), 'the wrong row read as the line', 'line:'),
    (lambda d: _var(d)['not_expressed'][0].__setitem__('reason', ''), 'not_expressed without a reason', 'line:'),
    (lambda d: _var(d)['not_expressed'][0].__setitem__('board', 'tetris.spin'), 'a firing board listed as not expressed', 'line:'),
    (lambda d: (_set(node(d, 'tsd.pink')['rows'], 3, 6, '-'), _set(node(d, 'tsd.pink')['rows'], 3, 5, 'p')),
     'the pink cell moved off the J', 'pink:'),
    (lambda d: (_set(node(d, 'tsd.terrain')['rows'], 2, 2, 'B'), _set(node(d, 'tsd.terrain')['rows'], 2, 3, '-')),
     'a dark-grey cell where the build puts its S', 'B:'),
    (lambda d: _set(node(d, 'basic')['rows'], 0, 4, 'c'), 'a cell the basic form draws filled where the spin board is empty', 'spin:'),
    (lambda d: _set(node(d, 'tsd.sj')['rows'], 2, 7, 'c'), 'a muted stack cell drawn lower-case', 'build:'),
    (lambda d: d['cross_source']['technique_pages']['theirs_is_ours'].__setitem__('mirrored', False),
     'that page\'s dagger read as drawn', 'imperial:'),
    (lambda d: d['cross_source']['technique_pages']['ours_is_theirs'].__setitem__('node', 'cross.z'),
     'that page\'s window credited on the wrong board', 'imperial:'),
    (lambda d: d['cross_source']['fires'][0].__setitem__('node', '3.second.cspin.first#1'), 'a cross-route node renamed', 'cross:'),
    (lambda d: d['cross_source']['fires'].pop(), 'a firing routes board unrecorded', 'cross:'),
    (lambda d: d['cross_source'].__setitem__('fires', []), 'no cross source', 'cross:'),
    (lambda d: node(d, 'cross.z').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['known_discrepancies'].append({'id': 'tsd.sj:colour', 'note': 'x'}), 'a stale discrepancy', 'discrepancy:'),
    (lambda d: _set(node(d, 'tsd.sj')['rows'], 1, 2, 'z'), 'a piece broken', 'discrepancy:'),
]


def selftest() -> int:
    return TT.run_selftest(SPEC, MUTANTS, {'board': ('Css---jCCC', 'Css---jCCc'),
                                           'text': ('十字形からの組み方', '十字型からの組み方')})


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))

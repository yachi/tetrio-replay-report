"""Transcribe shiwehi.com's STSD page into `stsd-technique.json`.

    python3 -m pipeline.openers.extract_stsd_shapes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_stsd_shapes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_stsd_shapes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_stsd_shapes --html-dir <dir> --write  # ...and rewrite

The first MID-GAME TECHNIQUE page (中盤テンプレ・ドネイト), and the reason the technique gate exists:
an STSD always sits on a partial stack, so its boards are a LOCAL SHAPE around one T, never a whole
board from an empty one. What the matcher (`pipeline/sim/technique-facts.ts`) compares is the
`window` of the variant below, anchored on the T's cells; every rule the techniques share is
`technique_transcription.py`'s, once.

WHERE THE TRANSCRIPTION COMES FROM. `NODES` is a literal, hand-checked transcription of the page's
RAW HTML, fetched the way 山岳積み2号's and stick spin's were: curl through the session proxy, TLS
verification on, with a CA bundle adding the Let's Encrypt YE2 intermediate shiwehi.com omits. Twelve
boards, plain text in `<div class="ttt">`, one row per line, drawn by the site's `column-exp.js`
(the same bytes the route pages recorded, re-fetched and re-hashed for this page). The page is not
committed; CI cannot fetch it.

THE CROSS-SOURCE is not a field and not a catalogue entry: it is the other drawings this repo already
holds. harddrop's SDPC Spin page (transcribed in `sdpcspin-routes.json`, a different author on a
different site) draws two stood-T boards on its STMB Cave → STSD branch, and the window fires on
exactly those two, one as drawn and one mirrored — checked by the gate on every push, by the same
predicate the matcher uses. It also fires on one board the 山岳積み2号 page (same author as this
page) draws without calling it an STSD, which is named as measured, not explained.

WHAT IS AN INFERENCE, flagged in the JSON (`reading`) rather than in prose only:

  * `B` (the renderer's #444444) is read as an EMPTY cell drawn highlighted — the garbage hole. The
    spin rule checks it: the misfire board's T fills that cell.
  * upper-case letters are a spin's cleared rows in the renderer's muted colours (`T` the T's,
    `J` the J's, `C` an earlier cell's), except on the misfire's first board, where the `C` row is a
    GARBAGE row (no spin is drawn there; the sentence under it names おじゃまブロック).
  * the board after the basic STSD draws row 4 filled right of the overhang, which the spin cannot
    leave by itself: read as the page assuming the player has filled it, named as a discrepancy, and
    used as the board the follow-up TSD is checked on.
  * the roof boards' terrains are not drawn; each is DERIVED (the board less its j and its roof
    piece) and carries no caption.
  * the 3-wide-well section says 「1つ目の組み方」 and draws only one: recorded, not read further.
"""
from __future__ import annotations

import copy
from pathlib import Path

from pipeline.openers import technique_transcription as TT
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS
from pipeline.openers.technique_transcription import node

HERE = Path(__file__).resolve().parent
OUT = HERE / 'stsd-technique.json'

ALPHABET = frozenset('-cjlztiCTJB')


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/stsd.php',
    'title': 'STSD(Super T-Spin Double)',
    'author': 'しゑひ(shiwehi)',
    'created': '2020-07-18',
    'updated': '2020-07-18',
    'fetched': '2026-10-17',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle '
                    'that adds the Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), '
                    'the method 山岳積み2号 and stick spin used. The snapshot is the page\'s raw HTML, byte '
                    'for byte; every board is plain text in it, 12 ten-wide boards in page order.',
    'snapshot_file': 'stsd.html',
    'snapshot_sha256': 'e0b9be8b78268ef648d94e4f906d88d2baf7997c0c68e6036805c436cdfd5f0f',
    'snapshot_bytes': 24423,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable '
                     'in CI: the page is not committed and cannot be fetched there. Re-check with '
                     '--html-dir after any refetch; an HTML hash moves with ANY byte of the page (ads, '
                     'sidebar, a date), so a moved hash means "read the board diff", not "the boards '
                     'changed". Sentences are compared against the page with its tags dropped.',
    'renderer': {
        'url': 'https://shiwehi.com/tetris/mutual/column-exp.js?date=20210408',
        'read': '2026-10-17',
        'sha256': '95c431a4147f9c30fc0e1bae935e6af6f5669c3d2fa1edfc388848e69ab62570',
        'sha256_note': 'the same bytes 山岳積み2号 and stick spin recorded, re-fetched for this page',
        'colorMap_used': {'c': '#a3a3a3', 'C': '#cccccc', 'B': '#444444', 'T': '#954dd8',
                          'J': '#4d57d8', 't j l z i': '#8400ff #0011ff #ff7b00 #ff0000 #00b7ff',
                          '-': '#000000'},
        'mirror_button': 'body.reversed swaps j<->l, s<->z (and upper case); the page says the recovery '
                         'piece is %L when mirrored',
    },
    'decorative_images': ['STSD(Super T-Spin Double)タイトル画像'],
    'video': {'id': '-YZyjNNMSOw', 'start': 181, 'quote': 'video.permission',
              'note': 'embedded explainer by I凜; not transcribed, not used'},
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ',
    '-': 'empty',
    'c': 'a cell filled before this diagram (any piece, or garbage), grey',
    'j l z i': 'a cell of that piece',
    't': 'a cell of the T the spin placed, in a row it does not clear',
    'T': 'a cell of the T in a row the spin clears (muted; OUR READING, checked: every upper-case row is a full row)',
    'J': 'a cell of the recovery J in a row its spin clears (muted; OUR READING, checked the same way)',
    'C': 'an earlier cell in a row a spin clears (muted); on misfire.garbage only, a garbage row (OUR READING)',
    'B': 'an EMPTY cell drawn dark grey: the hole in a garbage row (OUR READING, checked: the misfire\'s T fills it)',
    '%X': 'the X piece',
}

QUOTES = [
    {'id': 'intro', 'verbatim': 'ここでは、STSD(Super T-Spin Double)という、TSDを2回打つことができる中盤テンプレについて紹介していきます。'},
    {'id': 'video.permission', 'verbatim': '※投稿主であるI凜さんに許可を得た上で動画を掲載しています。'},
    {'id': 'h.basic', 'verbatim': '基本形とラインの消し方'},
    {'id': 'basic', 'verbatim': '基本形は上図の通りです。'},
    {'id': 'basic.spin', 'verbatim': 'ここから、以下のように%Tを縦向きに入れてTSDを打つと、もう一度TSDを打てる形が残ります。'},
    {'id': 'h.build', 'verbatim': '元地形からの組み方と特徴'},
    {'id': 'h.build3', 'verbatim': '3列空きからの組み方'},
    {'id': 'build3', 'verbatim': '1つ目の組み方としては、3列の下穴から%J・%Lを立てて作る方法です。'},
    {'id': 'build3.hole', 'verbatim': '真ん中に穴があっても問題なく組むことができます。'},
    {'id': 'roof', 'verbatim': '屋根のミノは高さによって使い分けてください。'},
    {'id': 'h.caution', 'verbatim': '注意点とリカバリー'},
    {'id': 'misfire', 'verbatim': 'おじゃまブロックの出現で上図のような穴ができてしまうと、不発になってしまいます。'},
    {'id': 'recover', 'verbatim': 'このような場合、%J(左右反転の場合は%L)を回転入れすることによってリカバリーができます(ブーメラン)。'},
]

NODES = [
    {'id': 'basic', 'kind': 'base', 'caption_quote': 'basic', 'label': 'the basic shape',
     'rows': _b('---------- --cc------ ---c------ cc-ccccccc c--ccccccc c--ccccccc')},
    {'id': 'basic.spin', 'kind': 'spin', 'spin_of': 'basic', 'spin': 'TSD', 'lines': 2, 'caption_quote': 'basic.spin',
     'label': 'the T stood up into it, nub left: a TSD clearing the two rows over the nub',
     'rows': _b('---------- --cc------ ---c------ CCTCCCCCCC CTTCCCCCCC c-tccccccc')},
    {'id': 'basic.after', 'kind': 'after', 'after_of': 'basic.spin', 'caption_quote': 'basic.spin',
     'label': 'what the TSD leaves: a TSD slot under the old roof',
     'rows': _b('---------- ---------- ---------- --cc------ ---ccccccc c-cccccccc')},
    {'id': 'build3.terrain', 'kind': 'base', 'caption_quote': 'h.build3', 'label': 'the terrain: a 3-wide well',
     'rows': _b('---------- ---------- ----cccccc ---ccccccc ---ccccccc')},
    {'id': 'build3.jl', 'kind': 'build', 'on': 'build3.terrain', 'adds': 'jl', 'same_occupancy_as': 'basic',
     'caption_quote': 'build3', 'label': 'a J and an L stood in the well',
     'rows': _b('---------- --ll------ ---l------ jj-lcccccc j--ccccccc j--ccccccc')},
    {'id': 'build3.jl_hole', 'kind': 'build', 'on': 'build3.jl_hole.terrain', 'adds': 'jl', 'caption_quote': 'build3.hole',
     'label': 'the same, over a hole in the row below',
     'rows': _b('--ll------ ---l------ jj-lcccccc j--ccccccc j--ccccccc c-cccccccc')},
    {'id': 'roof.z', 'kind': 'build', 'on': 'roof.z.terrain', 'adds': 'jz', 'caption_quote': 'roof',
     'label': 'a Z for the roof',
     'rows': _b('--zz------ ---zz----- jj-ccccccc j--ccccccc j--ccccccc')},
    {'id': 'roof.i', 'kind': 'build', 'on': 'roof.i.terrain', 'adds': 'ij', 'caption_quote': 'roof',
     'label': 'an I for the roof, one row higher',
     'rows': _b('---------- --iiii---- ---ccccccc jj-ccccccc j--ccccccc j--ccccccc')},
    {'id': 'misfire.garbage', 'kind': 'illustration', 'extends': 'build3.jl', 'extra_bottom_rows': 1,
     'caption_quote': 'misfire', 'muted_rows_reading': 'garbage',
     'label': 'a garbage row arrives with its hole under the T\'s column',
     'rows': _b('--ll------ ---l------ jj-lcccccc j--ccccccc j--ccccccc CCBCCCCCCC')},
    {'id': 'misfire.spin', 'kind': 'spin', 'spin_of': 'misfire.garbage', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'misfire', 'label': 'the T drops through into the hole: a TSD on the wrong rows (不発)',
     'rows': _b('--ll------ ---l------ jj-lcccccc j-tccccccc CTTCCCCCCC CCTCCCCCCC')},
    {'id': 'recover.j', 'kind': 'spin', 'spin_piece': 'J', 'spin': 'J-spin', 'lines': 2, 'caption_quote': 'recover',
     'label': 'the recovery: a J spun in (the boomerang), clearing two rows that are not adjacent',
     'rows': _b('--cc------ ---c------ CCJCCCCCCC c-jccccccc CJJCCCCCCC cc-ccccccc')},
    {'id': 'recover.j.after', 'kind': 'after', 'after_of': 'recover.j', 'caption_quote': 'recover',
     'label': 'what the J leaves',
     'rows': _b('---------- ---------- --cc------ ---c------ c-cccccccc cc-ccccccc')},
    # ── derived: drawn nowhere on the page ──
    {'id': 'build3.jl_hole.terrain', 'kind': 'derived', 'derived': True, 'extends': 'build3.terrain',
     'extra_bottom_rows': 1, 'reading': 'build3.jl_hole less its j and l: the 3-wide well over a row holed at column 1',
     'rows': _b('---------- ---------- ----cccccc ---ccccccc ---ccccccc c-cccccccc')},
    {'id': 'roof.z.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'roof.z less its j and z: a 3-wide well three rows deep, no step',
     'rows': _b('---------- ---------- ---ccccccc ---ccccccc ---ccccccc')},
    {'id': 'roof.i.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'roof.i less its j and i: a 3-wide well four rows deep, no step',
     'rows': _b('---------- ---------- ---ccccccc ---ccccccc ---ccccccc ---ccccccc')},
]

VARIANTS = [{
    'id': 'stsd', 'board': 'basic.spin', 'spin': 'TSD', 'lines': 2,
    'window': {'rows': [1, 5], 'cols': [0, 3]},
    't_cells': [[3, 2], [4, 1], [4, 2], [5, 2]],
    'roof_cells': [[1, 2], [1, 3], [2, 3]],
    'window_note': 'in basic.spin\'s frame, row 0 the top: the bounding box of the T, the roof above it and '
                   'the follow-up slot. Row 0 (headroom) and everything right of column 3 is outside: the '
                   'cleared rows\' cells there are entailed by the clear (NaiveClauseForced), the rest is '
                   'grey on the page. Occupancy only, never colour; garbage is filled.',
    'followup': {'board': 'basic.after', 'spin': 'TSD', 'lines': 2,
                 't_cells_pre_clear': [[2, 0], [2, 1], [2, 2], [5, 1]],
                 't_cells_after': [[4, 0], [4, 1], [4, 2], [5, 1]],
                 'note': 'the flat T into the slot under the old roof. On basic.after as DRAWN it clears two '
                         'rows; on the board the spin actually leaves it would clear one, because row 4 right '
                         'of the roof is only filled on the drawing (basic.after:after).'},
    'fires_on': ['basic', 'build3.jl', 'build3.jl_hole', 'roof.z', 'roof.i'],
    'misses': ['misfire.garbage', 'misfire.spin'],
}]

CROSS_SOURCE = {
    'kind': 'routes',
    'label_pattern': 'stsd',
    'note': 'the window, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot '
            'board of every committed *-routes.json, with the U cells as the T. `fires` is the independent '
            'drawer (harddrop\'s SDPC Spin page, another author); `also` is measured and named, not explained.',
    'fires': [
        {'file': 'sdpcspin-routes.json', 'node': '3.first.cave.stsd.next', 'variant': 'stsd', 'mirrored': False,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': 'harddrop\'s STMB Cave into STSD, the stood T after the flat TSD'},
        {'file': 'sdpcspin-routes.json', 'node': '3.first.trinity.tsd', 'variant': 'stsd', 'mirrored': True,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': 'the Trinity\'s stood T into the cave its TSD leaves, nub right'},
    ],
    'also': [
        {'file': 'mountainous2-routes.json', 'node': '2.compromise.fire34.bag4', 'variant': 'stsd', 'mirrored': False,
         'page': 'https://shiwehi.com/tetris/template/mountainous2.php',
         'note': 'the same author\'s 4巡目 vertical T slot, not labelled STSD on that page: measured'},
    ],
    'labelled_not_fired': [
        {'file': 'meisou-routes.json', 'node': '2.normal_SO.stsd',
         'reason': 'its U is the FLAT T into the bottom TSD, fired before the stood T; this page draws the stood T first'},
        {'file': 'sdpcspin-routes.json', 'node': '3.first.cave.stsd',
         'reason': 'its U is the FLAT T into the bottom TSD, fired before the stood T (its continuation, '
                   '3.first.cave.stsd.next, is in fires)'},
        {'file': 'sdpcspin-routes.json', 'node': '3.first.trinity',
         'reason': 'a Trinity built 「instead of the STSD」 (its label): a different technique'},
        {'file': 'sdpcspin-routes.json', 'node': '3.first.cave',
         'reason': 'the STMB Cave\'s own TSD (its label names the STSD it leads to)'},
    ],
    'same_author_corroboration': 'meisou-routes.json 2.normal_SO.stsd (shiwehi.com, the same author): not independent',
    'unfetched': ['https://harddrop.com/wiki/STSD — not fetched, not claimed'],
}

KNOWN_DISCREPANCIES = [
    {'id': 'basic.after:after',
     'note': 'the board after the basic STSD draws row 4 filled from column 3 to the wall; the spin itself '
             'leaves only column 3 there (and its surviving t cell is drawn grey). Read as the page '
             'assuming the right side has been stacked up to the roof; the follow-up slot is checked on the '
             'board as drawn.'},
    {'id': 'misfire.spin:colour',
     'note': 'the misfire draws the J\'s cell in a cleared row as C (grey) where recover.j draws its J\'s '
             'cleared cells as J, so the j there is three cells: the renderer convention applied '
             'inconsistently, not a different piece'},
]

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'stsd',
        'source': SOURCE,
        'terms': TERMS,
        'legend': LEGEND,
        'empty_letters': 'B',
        'quotes': QUOTES,
        'nodes': NODES,
        'page_order': PAGE_ORDER,
        'basic_form': [],
        'variants': VARIANTS,
        'cross_source': CROSS_SOURCE,
        'known_discrepancies': KNOWN_DISCREPANCIES,
    }


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='B',
    upper_groups={'T': 'merge', 'J': 'merge'},
)


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def _set(rows, r, c, ch):
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _var(d):
    return d['variants'][0]


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'basic')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: d['page_order'].reverse(), 'page_order swapped', 'grammar:'),
    (lambda d: node(d, 'basic.spin').__setitem__('spin_of', 'nowhere'), 'a dangling reference', 'grammar:'),
    (lambda d: _set(node(d, 'build3.jl')['rows'], 4, 5, '-'), 'a build board cell flipped', 'build:'),
    (lambda d: (_set(node(d, 'basic.spin')['rows'], 5, 2, 'c'), _set(node(d, 'basic.spin')['rows'], 5, 1, 't')),
     'the T moved one cell', 'spin:'),
    (lambda d: _set(node(d, 'basic.spin')['rows'], 3, 0, 'c'), 'a cleared row drawn unmuted', 'spin:'),
    (lambda d: node(d, 'basic.spin').__setitem__('lines', 3), 'the spin\'s line count', 'spin:'),
    (lambda d: node(d, 'basic.after').__setitem__('rows', ['-' * 10] * 3 + ['--cc------', '---c------', 'c-cccccccc']),
     'the after board corrected to what the spin leaves', 'discrepancy:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [0, 4]), 'the window widened by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [1, 4]), 'the window excluding a T cell', 'window:'),
    (lambda d: _var(d)['roof_cells'].pop(), 'a roof cell dropped', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('t_cells_pre_clear', [[2, 1], [2, 2], [2, 3], [5, 2]]),
     'the follow-up slot moved', 'window:'),
    (lambda d: _set(node(d, 'basic.spin')['rows'], 1, 0, 'c'), 'a must-empty window cell filled on the drawing', 'window:'),
    (lambda d: _set(node(d, 'basic.spin')['rows'], 5, 5, 'z'), 'a piece letter outside the window', 'window:'),
    (lambda d: _var(d)['fires_on'].append('build3.terrain'), 'a board it cannot fire on listed', 'window:'),
    (lambda d: _var(d)['misses'].append('basic'), 'a board it fires on listed as a miss', 'window:'),
    (lambda d: _set(node(d, 'misfire.garbage')['rows'], 5, 2, 'C'), 'the hole B read as filled', 'spin:'),
    (lambda d: _set(node(d, 'build3.jl_hole')['rows'], 0, 2, 'j'), 'a piece broken', 'discrepancy:'),
    (lambda d: _var(d)['followup'].__setitem__('lines', 1), 'the follow-up line count', 'window:'),
    (lambda d: d['cross_source']['fires'][0].__setitem__('node', '3.first.cave.stsd.nxt'),
     'a cross-route node renamed', 'cross:'),
    (lambda d: d['cross_source']['also'].clear(), 'a measured cross-route board unnamed', 'cross:'),
    (lambda d: d['cross_source']['labelled_not_fired'].pop(0), 'a labelled board neither firing nor named', 'cross:'),
    (lambda d: d['cross_source']['fires'].clear(), 'no cross source', 'cross:'),
    (lambda d: node(d, 'roof.i').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['known_discrepancies'].append({'id': 'roof.z:colour', 'note': 'x'}), 'a stale discrepancy', 'discrepancy:'),
]


def _no_j_merge(spec):
    s = copy.copy(spec)
    s.upper_groups = {'T': 'merge'}
    return s


SPEC_MUTANTS = [
    (_no_j_merge, 'upper_groups without J (recover.j loses its J)', 'discrepancy:'),
]


def selftest() -> int:
    return TT.run_selftest(SPEC, MUTANTS, {'board': ('c-tccccccc', 'c-tcccccc-'),
                                           'text': ('基本形は上図の通りです。', '基本形は下図の通りです。')},
                           SPEC_MUTANTS)


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))

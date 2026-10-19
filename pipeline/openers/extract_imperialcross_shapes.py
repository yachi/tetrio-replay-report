"""Transcribe shiwehi.com's インペリアルクロス (Imperial Cross) page into `imperialcross-technique.json`.

    python3 -m pipeline.openers.extract_imperialcross_shapes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_imperialcross_shapes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_imperialcross_shapes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_imperialcross_shapes --html-dir <dir> --write  # ...and rewrite

The third MID-GAME TECHNIQUE page (中盤テンプレ・ドネイト), after STSD and STMB Cave: a cross-shaped hole
(a "+": one cell, then three, then one, down one column) under a Z-shaped overhang. The T goes in STOOD
UP with its nub pointing right — 「%Tを縦向きに入れてTSDを打つ」 — so it fills the cross's top, centre,
bottom and right arm and leaves the LEFT arm empty. Its two cleared rows are the cross's top and bottom
rows, which are NOT adjacent; the row between them keeps the empty arm, and with the overhang above it
that is a second TSD slot: 「もう一度TSDを打てる形が残ります」.

DECISION: the spin is a TSD (a full T-spin, 2 lines — the engine credits the line count, not whether the
rows touch) and the anchor is the T's four cells, as STSD's and STMB Cave's. So the window predicate
expresses it and the matcher (`technique-facts.ts`) is untouched. The T is stood with its nub right
(mirrored: nub left, the right arm empty), which is not STSD's T (nub left INTO the cavity, on a board with
no cross): the two windows disagree on the cell beside the nub.

WHERE THE TRANSCRIPTION COMES FROM. `NODES` is a literal, hand-checked transcription of the page's RAW
HTML, fetched the way STSD's was: curl through the session proxy, TLS verification on, with a CA bundle
adding the Let's Encrypt YE2 intermediate shiwehi.com omits. Fourteen boards, plain text in
`<div class="ttt">`, one row per line. The page is not committed; CI cannot fetch it.

THE PAGE DRAWS THREE STARTING POINTS, and every one is transcribed: the basic form (元地形 is the page's
word for any starting terrain), built FROM A TSD SHAPE (TSD形: %O and then %Z or %L hooked over it; a %J
there builds a TST instead, the page says, so it is a miss) and FROM A CROSS (十字形: a %Z laid flat over
it; a different %Z placement builds ダブルダガー, a different technique, so that board is a miss too).

WHY THE WINDOW IS THE AGREEMENT BOX (`window_basis: agreement`), not STSD's bounding box of T, roof and
follow-up. That box is columns 0-4 in the spin board's frame, and its top-right corner (row 1, column 4)
is EMPTY on the spin board but FILLED on the page's own TSD-shape build (the stood %Z), and drawn `B` on the
basic form — the dark-grey cells the page leaves open. A bounding-box window would refuse the page's own
build. So the window is the box every drawing of the shape agrees on: this page's four (the basic form and
its three builds) and ガムシロ積み's two Imperial Cross boards (another page of the same site, transcribed
in another file, `gamushiro-routes.json`). It comes out rows 1-5, columns 0-3 of the spin board: the two
rows of overhang over the cross and the cross's three rows, from the wall side of the empty arm to the
nub. The gate checks it is exactly that box (every drawing fires once at its slot, and widening it by a
row or a column on any side meets a disagreement or leaves a drawing). It reads NO `B` cell when it fires
on the basic form — the page's open region and the window do not overlap, which `extra_checks` measures.

WHAT THE WINDOW CAN DISCRIMINATE. The T's rows: the cross's top and bottom rows are the rows the TSD
clears, so their filled cells are entailed by the clear at a full TSD (NaiveClauseForced). The middle row
is not cleared, and its EMPTY left arm is the cell that tells this T from STSD's (whose nub fills it) — and
forces the clear to be the two non-adjacent rows, since that row cannot be full. The two rows above are the
overhang: the stem's top cell has an empty cell over it and the nub's corner a filled one, which is the
second TSD's roof.

THE FOLLOW-UP is the second TSD: a T laid flat, pointing down, into the empty arm, under the overhang.
The page draws the after board BEFORE the stack beside that slot is built (its row is only full once the
right side is stacked up to the overhang), so on the drawing the slot fills ONE row; the TSD it promises
fills two. That is the gate's opt-in `followup.drawn_lines` (with its note), not a discrepancy.

WHAT IS AN INFERENCE, flagged in the JSON (`reading`) rather than in prose only:

  * `B` (dark grey, #444444 in the page's renderer) on the basic form: cells the page leaves OPEN — every
    later drawing of that board draws them empty. Read as EMPTY (the matcher's occupancy), and outside the
    window wherever it fires.
  * upper-case `C` and `T` in the spin board: the cleared rows, muted (checked by the spin rule). Upper-case
    `C` in the cross-shape builds is in a row no spin clears: OUR READING, the stack the page assumes beside
    the build (it is the rest of the row the second TSD clears). Those builds stand on DERIVED terrains (the
    build less its %Z), and `extra_checks` measures that each is the drawn 十字形 terrain plus those cells.
  * boards 2-5 draw the T on its way in (stood, up, nub left, flat): illustrations, never matched.
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
OUT = HERE / 'imperialcross-technique.json'
GAMUSHIRO = HERE / 'gamushiro-routes.json'

ALPHABET = frozenset('-cCBtTjlzso')


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/imperialcross.php',
    'title': 'インペリアルクロス(Imperial Cross)',
    'author': 'しゑひ(shiwehi)',
    'updated': '2020-06-20',
    'fetched': '2026-10-17',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle '
                    'that adds the Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), '
                    'the method STSD, STMB Cave, 山岳積み2号 and stick spin used. The snapshot is the page\'s raw '
                    'HTML, byte for byte; every board is plain text in it, 14 ten-wide boards in page order.',
    'snapshot_file': 'imperialcross.html',
    'snapshot_sha256': '819c2f5ac322448209e009d7c9cc7232368972c362354709da064b6a8cda545b',
    'snapshot_bytes': 24103,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable '
                     'in CI: the page is not committed and cannot be fetched there. Re-check with '
                     '--html-dir after any refetch; an HTML hash moves with ANY byte of the page (ads, '
                     'sidebar, a date), so a moved hash means "read the board diff", not "the boards '
                     'changed". Sentences are compared against the page with its tags dropped.',
    'renderer': {
        'url': 'https://shiwehi.com/tetris/mutual/column-exp.js?date=20210408',
        'note': 'the same script URL STSD\'s page loads (its bytes and colour map recorded in '
                'stsd-technique.json: B #444444, C #cccccc, c #a3a3a3, - #000000); not re-hashed for this page',
        'mirror_button': 'body.reversed swaps j<->l, s<->z (and upper case)',
    },
    'decorative_images': ['インペリアルクロス(Imperial Cross)タイトル画像'],
    'references': ['./doubledagger.php (ダブルダガー, linked from the last sentence: a different technique)'],
    'unfetched': ['the ダブルダガー page — not transcribed, not claimed'],
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ',
    '-': 'empty',
    'c': 'a cell filled before this diagram (any piece, or garbage), grey',
    'j l z s o': 'a cell of that piece',
    't': 'a cell of the T, in a row it does not clear (on the illustrations: the T on its way in)',
    'T': 'a cell of the T in a row the spin clears (muted; OUR READING, checked: every upper-case row is a full row)',
    'C': 'on the spin board, an earlier cell in a row the spin clears (muted; checked the same way); on the '
         'cross-shape builds, in a row no spin clears, the stack the page assumes beside the build (OUR READING)',
    'B': 'dark grey on the basic form only: a cell the page leaves open, drawn empty on every later drawing of '
         'that board (OUR READING: read as EMPTY; the window reads none of them)',
    '%X': 'the X piece',
}

QUOTES = [
    {'id': 'intro', 'verbatim': 'ここでは、インペリアルクロス(Imperial Cross)という、TSDを2回打つことができる'
                                '中盤テンプレについて紹介していきます。'},
    {'id': 'h.basic', 'verbatim': '基本形とラインの消し方'},
    {'id': 'basic', 'verbatim': '基本形は上図の通りです。'},
    {'id': 'spin', 'verbatim': 'ここから、以下のように%Tを縦向きに入れてTSDを打つと、もう一度TSDを打てる形が残ります。'},
    {'id': 'h.build', 'verbatim': '元地形からの組み方と特徴'},
    {'id': 'h.tsd', 'verbatim': 'TSD形からの組み方'},
    {'id': 'tsd', 'verbatim': '1つ目の組み方としては、既に完成されたTSDの形から%Zや%Lを引っ掛けて作る方法です。'},
    {'id': 'tsd.j', 'verbatim': '%Jが来た場合には代わりにTSTを組むことができます。'},
    {'id': 'h.cross', 'verbatim': '十字形からの組み方'},
    {'id': 'cross', 'verbatim': '2つ目に、既に完成された十字形から%Zを乗せて作る方法です。'},
    {'id': 'dagger', 'verbatim': 'インペリアルクロスを組む代わりにダブルダガーを組むこともできます。'},
]

NODES = [
    {'id': 'basic', 'kind': 'base', 'caption_quote': 'basic',
     'label': 'the basic form: the cross under a Z-shaped overhang; the dark-grey cells are left open',
     'rows': _b('--BBBBBBBB --ccBBBBBB ---ccBBBBB cc-ccccccc c---cccccc cc-ccccccc')},
    {'id': 'basic.t_drop', 'kind': 'illustration', 'caption_quote': 'spin',
     'label': 'the T on its way in: stood up at the left wall',
     'rows': _b('t--------- ttcc------ t--cc----- cc-ccccccc c---cccccc cc-ccccccc')},
    {'id': 'basic.t_up', 'kind': 'illustration', 'caption_quote': 'spin',
     'label': 'the T on its way in: pointing up, under the overhang',
     'rows': _b('---------- -tcc------ tttcc----- cc-ccccccc c---cccccc cc-ccccccc')},
    {'id': 'basic.t_left', 'kind': 'illustration', 'caption_quote': 'spin',
     'label': 'the T on its way in: stood, nub left, in the cross',
     'rows': _b('---------- --cc------ ---cc----- cctccccccc ctt-cccccc cctccccccc')},
    {'id': 'basic.t_down', 'kind': 'illustration', 'caption_quote': 'spin',
     'label': 'the T on its way in: flat, pointing down, in the cross',
     'rows': _b('---------- --cc------ ---cc----- cc-ccccccc ctttcccccc cctccccccc')},
    {'id': 'basic.spin', 'kind': 'spin', 'spin_of': 'basic', 'spin': 'TSD', 'lines': 2, 'caption_quote': 'spin',
     'label': 'the T stood, nub right: a TSD clearing the cross\'s top and bottom rows, not adjacent',
     'rows': _b('---------- --cc------ ---cc----- CCTCCCCCCC c-ttcccccc CCTCCCCCCC')},
    {'id': 'basic.after', 'kind': 'after', 'after_of': 'basic.spin', 'caption_quote': 'spin',
     'label': 'what the TSD leaves: the empty arm under the overhang, a second TSD slot',
     'rows': _b('---------- ---------- ---------- --cc------ ---cc----- c-ttcccccc')},
    {'id': 'tsd.terrain', 'kind': 'base', 'caption_quote': 'tsd', 'label': 'the TSD shape: a finished TSD slot, no roof',
     'rows': _b('---------- cc--cccccc c---cccccc cc-ccccccc')},
    {'id': 'tsd.oz', 'kind': 'build', 'on': 'tsd.terrain', 'adds': 'oz', 'caption_quote': 'tsd',
     'label': 'an O and a Z stood into the TSD slot\'s open corner: the cross under the overhang',
     'rows': _b('---------- --oo------ --ooz----- ---zz----- cc-zcccccc c---cccccc cc-ccccccc')},
    {'id': 'tsd.ol', 'kind': 'build', 'on': 'tsd.terrain', 'adds': 'ol', 'caption_quote': 'tsd',
     'label': 'an O and an L hooked into the same corner: the same cross',
     'rows': _b('---------- --oo------ --oo------ ---lll---- cc-lcccccc c---cccccc cc-ccccccc')},
    {'id': 'tsd.oj', 'kind': 'build', 'on': 'tsd.terrain', 'adds': 'oj',
     'caption_note': 'the page\'s sentence for this board is quote tsd.j, checked verbatim against the snapshot '
                     'and NOT rendered as its caption: it holds 来, the Japanese glyph the page audit\'s '
                     'simplified-character check cannot tell from the simplified one',
     'label': 'with a J instead: a TST slot, not an Imperial Cross',
     'rows': _b('---------- --oo------ --oo------ ---jj----- cc-jcccccc c--jcccccc cc-ccccccc')},
    {'id': 'cross.terrain', 'kind': 'base', 'caption_quote': 'cross', 'label': 'the cross shape, finished, no roof',
     'rows': _b('---------- cc-ccccccc c---cccccc cc-ccccccc')},
    {'id': 'cross.z', 'kind': 'build', 'on': 'cross.z.terrain', 'adds': 'z', 'caption_quote': 'cross',
     'label': 'a Z laid flat over the cross: the overhang (the stack beside it drawn muted)',
     'rows': _b('---------- ---------- --zz------ ---zzCCCCC cc-ccccccc c---cccccc cc-ccccccc')},
    {'id': 'dagger', 'kind': 'build', 'on': 'dagger.terrain', 'adds': 'z', 'caption_quote': 'dagger',
     'label': 'the Z one column right: ダブルダガー, a different technique',
     'rows': _b('---------- ---------- ---zz----- C---zzCCCC cc-ccccccc c---cccccc cc-ccccccc')},
    # ── derived: drawn nowhere on the page ──
    {'id': 'cross.z.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'cross.z less its z: the cross with the muted stack beside where the Z goes',
     'rows': _b('---------- ---------- ---------- -----CCCCC cc-ccccccc c---cccccc cc-ccccccc')},
    {'id': 'dagger.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'dagger less its z: the cross with the muted stack on both sides of where the Z goes',
     'rows': _b('---------- ---------- ---------- C-----CCCC cc-ccccccc c---cccccc cc-ccccccc')},
]

#: the variant's window, in basic.spin's frame
VARIANTS = [{
    'id': 'imperialcross', 'board': 'basic.spin', 'spin': 'TSD', 'lines': 2,
    'window_basis': 'agreement',
    'window': {'rows': [1, 5], 'cols': [0, 3]},
    't_cells': [[3, 2], [4, 2], [4, 3], [5, 2]],
    'roof_cells': [[1, 2], [1, 3], [2, 3]],
    'window_note': 'in basic.spin\'s frame, row 0 the top: the AGREEMENT BOX of every drawing in `agreement` and '
                   'ガムシロ積み\'s two Imperial Cross boards. Rows 3 and 5 are the rows the TSD clears (entailed by '
                   'the clear at a full TSD, NaiveClauseForced); row 4 is the cross\'s middle row, its LEFT arm empty '
                   '(column 1), which no T but this stood one leaves and which keeps the two cleared rows apart; rows '
                   '1-2 are the overhang: the stem\'s top cell has an empty cell over it, the nub\'s corner a filled '
                   'one. Column 4 is outside: the top cell of it disagrees (empty here, the stood Z on tsd.oz, B on '
                   'the basic form). Occupancy only, never colour; garbage is filled.',
    'untested_drawn': {'cells': [], 'reason': ''},
    'agreement': [
        {'board': 'basic', 't_cells': [[3, 2], [4, 2], [4, 3], [5, 2]], 'mirrored': False},
        {'board': 'tsd.oz', 't_cells': [[4, 2], [5, 2], [5, 3], [6, 2]], 'mirrored': False},
        {'board': 'tsd.ol', 't_cells': [[4, 2], [5, 2], [5, 3], [6, 2]], 'mirrored': False},
        {'board': 'cross.z', 't_cells': [[4, 2], [5, 2], [5, 3], [6, 2]], 'mirrored': False},
    ],
    'followup': {'board': 'basic.after', 'spin': 'TSD', 'lines': 2,
                 't_cells_pre_clear': [[2, 0], [2, 1], [2, 2], [4, 1]],
                 't_cells_after': [[4, 0], [4, 1], [4, 2], [5, 1]],
                 'drawn_lines': 1,
                 'drawn_note': 'the page draws basic.after before the stack right of the overhang is built: the '
                               'flat T fills the bottom row there and not the one above it, whose cells right of the '
                               'overhang are still empty. The TSD the page promises (もう一度TSDを打てる形) clears both '
                               'once that side is stacked up, which is what the matcher scores.',
                 'note': 'the flat T, pointing down, into the empty arm under the overhang (pre-clear: the row above '
                         'the cross and the arm, two cleared rows apart). It lies inside the window; the matcher '
                         'carries it through every clear to the next T.'},
    'fires_on': ['basic', 'tsd.oz', 'tsd.ol', 'cross.z'],
    'misses': ['tsd.terrain', 'tsd.oj', 'cross.terrain', 'dagger', 'basic.after'],
}]


def gamushiro_drawings() -> list[dict]:
    """ガムシロ積み's Imperial Cross boards (`gamushiro-routes.json`, its own transcription and gate) as
    agreement drawings: no slot is drawn there, so the T cells are declared here, in that board's frame, and
    the agreement rule checks the window fires there once, at exactly that slot, in exactly that hand."""
    nodes = {n['id']: n for n in json.loads(GAMUSHIRO.read_text())['nodes']}
    return [{'name': f'gamushiro-routes.json {nid}', 'rows': nodes[nid]['rows'],
             't_cells': [[6, 3], [7, 3], [7, 4], [8, 3]], 'mirrored': False}
            for nid in ('2.normal.imperial#1', '2.normal.imperial#2')]


CROSS_SOURCE = {
    'kind': 'routes',
    'label_pattern': 'imperial',
    'note': 'the window, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot board '
            'of every committed *-routes.json, with the U cells as the T. `fires` is the independent drawer '
            '(harddrop\'s SDPC Spin page, another author); `also` is measured and named, not explained. '
            'ガムシロ積み\'s two boards are the window\'s `agreement` drawings, not a cross-check of it.',
    'agreement_external': [
        {'file': 'gamushiro-routes.json', 'node': '2.normal.imperial#1'},
        {'file': 'gamushiro-routes.json', 'node': '2.normal.imperial#2'},
    ],
    'fires': [
        {'file': 'sdpcspin-routes.json', 'node': '3.third.imperial', 'variant': 'imperialcross', 'mirrored': True,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': 'harddrop\'s SDPC Spin: the Imperial Cross of its third C-Spin build, the T stood with its nub left'},
    ],
    'also': [
        {'file': 'stickspin-routes.json', 'node': '2.sd.imperial.spin', 'variant': 'imperialcross', 'mirrored': True,
         'note': 'shiwehi.com\'s stick spin page (the same author as this one): its SD-PC fallback, the nub left'},
    ],
    'labelled_not_fired': [
        {'file': 'gamushiro-routes.json', 'node': '2.normal.imperial#1',
         'reason': 'no T slot drawn (no U); one of the window\'s agreement drawings, its slot declared there'},
        {'file': 'gamushiro-routes.json', 'node': '2.normal.imperial#2',
         'reason': 'no T slot drawn (no U); one of the window\'s agreement drawings, its slot declared there'},
        {'file': 'sdpcspin-routes.json', 'node': '3.third.imperial.pc#1',
         'reason': 'the SECOND TSD (a flat T into the empty arm) inside a Perfect Clear pattern: the follow-up, '
                   'not the stood T the window anchors on'},
        {'file': 'sdpcspin-routes.json', 'node': '3.third.imperial.pc#2',
         'reason': 'the second TSD inside a Perfect Clear pattern, as pc#1'},
        {'file': 'sdpcspin-routes.json', 'node': '3.third.imperial.pc#3',
         'reason': 'the second TSD inside a Perfect Clear pattern, as pc#1'},
        {'file': 'sdpcspin-routes.json', 'node': '3.third.imperial.pc#4',
         'reason': 'the second TSD inside a Perfect Clear pattern, as pc#1'},
        {'file': 'stickspin-routes.json', 'node': '2.sd.imperial',
         'reason': 'the board before its T: no T slot drawn (no U); its spin board is 2.sd.imperial.spin'},
    ],
    'unfetched': ['https://harddrop.com/wiki/SDPC_Spin is read from sdpcspin-routes.json, not refetched here'],
}

KNOWN_DISCREPANCIES: list[dict] = []

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'imperialcross',
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


def extra_checks(data: dict):
    bad, measured = [], set()
    by = {n['id']: n for n in data['nodes']}
    v = data['variants'][0]
    # the agreement drawings from ガムシロ積み are the ones the cross-source block records
    want = [(e['file'], e['node']) for e in data['cross_source'].get('agreement_external', [])]
    got = [tuple(d['name'].split(' ', 1)) for d in gamushiro_drawings()]
    if want != got:
        bad.append(f'cross: agreement_external {want} is not the drawings the gate reads {got}')
    # the page's open region: the window reads no B cell where it fires on the basic form
    b = by['basic']['rows']
    for cs in TT.t_placements(b, SPEC):
        for m in (False, True):
            if TT.window_fires(data, v, SPEC, b, cs, m):
                f = TT.frame_map(data, v, SPEC, cs, m)
                (r0, r1), (c0, c1) = v['window']['rows'], v['window']['cols']
                cells = {f(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
                if any(b[r][c] == 'B' for r, c in cells):
                    bad.append('B: the window reads a cell the basic form leaves open (B)')
    # every B cell is drawn empty on the spin board (the page's later drawing of the same board)
    spin = by['basic.spin']['rows']
    if any(ch == 'B' and spin[r][c] != EMPTY for r, row in enumerate(b) for c, ch in enumerate(row)):
        bad.append('B: a cell the basic form draws B is not empty on basic.spin')
    # the cross-shape builds' derived terrains are the drawn 十字形 terrain plus their muted cells
    for d in ('cross.z.terrain', 'dagger.terrain'):
        less = [''.join(EMPTY if ch == 'C' else ch for ch in row) for row in by[d]['rows']]
        if bottom(less, TT.MAX_ROWS) != bottom(by['cross.terrain']['rows'], TT.MAX_ROWS):
            bad.append(f'build: {d} less its C cells is not cross.terrain')
        if any('C' in row for row in by[d]['rows'][-3:]):
            bad.append(f'build: {d} draws a C cell inside the cross terrain\'s rows')
    return bad, measured


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='B',
    upper_groups={'T': 'merge'},
    extra_checks=extra_checks,
    external_drawings=lambda: gamushiro_drawings(),
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
    (lambda d: d.__setitem__('empty_letters', ''), 'B no longer read as empty', 'grammar:'),
    (lambda d: _set(node(d, 'tsd.ol')['rows'], 6, 0, '-'), 'a build board cell flipped', 'build:'),
    (lambda d: _set(node(d, 'cross.z.terrain')['rows'], 3, 9, '-'), 'the derived terrain edited', 'build:'),
    (lambda d: (_set(node(d, 'basic.spin')['rows'], 4, 3, 'c'), _set(node(d, 'basic.spin')['rows'], 4, 1, 't')),
     'the T stood nub left (STSD\'s T)', 'spin:'),
    (lambda d: _set(node(d, 'basic.spin')['rows'], 3, 0, 'c'), 'a cleared row drawn unmuted', 'spin:'),
    (lambda d: node(d, 'basic.spin').__setitem__('lines', 1), 'the spin\'s line count', 'spin:'),
    (lambda d: _set(node(d, 'basic.after')['rows'], 4, 0, 'c'), 'the after board not what the spin leaves', 'discrepancy:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [0, 4]), 'the window widened to the bounding box', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [1, 3]), 'the window narrowed by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [2, 5]), 'the window without the overhang\'s top row', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [0, 5]), 'the window up to the headroom row', 'window:'),
    (lambda d: _var(d)['roof_cells'].pop(), 'a roof cell unnamed', 'window:'),
    (lambda d: _var(d)['untested_drawn']['cells'].append([4, 5]), 'an empty cell named untested', 'window:'),
    (lambda d: _var(d)['agreement'][1].__setitem__('mirrored', True), 'a build read mirrored', 'window:'),
    (lambda d: _var(d)['agreement'][3].__setitem__('t_cells', [[4, 2], [5, 1], [5, 2], [6, 2]]),
     'a slot read with STSD\'s T', 'window:'),
    (lambda d: _var(d).__setitem__('agreement', []), 'the page\'s own drawings dropped from the agreement', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('t_cells_after', [[3, 0], [3, 1], [3, 2], [4, 1]]),
     'the follow-up slot read without the two cleared rows', 'window:'),
    (lambda d: _var(d)['followup'].pop('drawn_lines'), 'the drawn after board read as complete', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('drawn_lines', 2), 'drawn_lines equal to lines', 'window:'),
    (lambda d: _var(d)['followup'].pop('drawn_note'), 'drawn_lines without its note', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('lines', 1), 'the follow-up line count', 'window:'),
    (lambda d: _var(d)['fires_on'].append('tsd.oj'), 'the TST build listed as a firing', 'window:'),
    (lambda d: _var(d)['misses'].append('cross.z'), 'a board it fires on listed as a miss', 'window:'),
    (lambda d: _set(node(d, 'tsd.oz')['rows'], 2, 4, 'o'), 'a piece broken', 'discrepancy:'),
    (lambda d: d['cross_source']['fires'][0].__setitem__('node', '3.third.imperia'), 'a cross-route node renamed', 'cross:'),
    (lambda d: d['cross_source']['also'].clear(), 'a firing routes board unrecorded', 'cross:'),
    (lambda d: d['cross_source']['labelled_not_fired'].pop(), 'a labelled board neither firing nor named', 'cross:'),
    (lambda d: d['cross_source']['fires'].clear(), 'no cross source', 'cross:'),
    (lambda d: d['cross_source']['agreement_external'].pop(), 'an agreement drawing unrecorded', 'cross:'),
    (lambda d: _set(node(d, 'basic')['rows'], 1, 3, 'B'), 'a window cell drawn open', 'B:'),
    (lambda d: node(d, 'cross.z').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['known_discrepancies'].append({'id': 'tsd.oj:colour', 'note': 'x'}), 'a stale discrepancy', 'discrepancy:'),
]


def _no_external(spec):
    s = copy.copy(spec)
    s.external_drawings = None
    return s


def _stickspin_as_drawn(spec):
    """stick spin's cross (nub left) declared as drawn: the agreement rule must refuse the hand."""
    s = copy.copy(spec)
    n = {x['id']: x for x in json.loads((HERE / 'stickspin-routes.json').read_text())['nodes']}['2.sd.imperial']
    s.external_drawings = lambda: gamushiro_drawings() + [
        {'name': 'stick spin read as drawn', 'rows': n['rows'], 't_cells': [[3, 6], [4, 5], [4, 6], [5, 6]],
         'mirrored': False}]
    return s


SPEC_MUTANTS = [
    (_no_external, 'no external drawing (the window checked against this page alone)', 'window:'),
    (_stickspin_as_drawn, 'a mirrored drawing declared as drawn', 'window:'),
]


def selftest() -> int:
    return TT.run_selftest(SPEC, MUTANTS, {'board': ('c-ttcccccc', 'c--tcccccc'),
                                           'text': ('十字形からの組み方', '十字型からの組み方')},
                           SPEC_MUTANTS)


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))

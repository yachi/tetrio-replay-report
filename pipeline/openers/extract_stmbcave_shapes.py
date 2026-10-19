"""Transcribe shiwehi.com's STMB Cave page into `stmbcave-technique.json`.

    python3 -m pipeline.openers.extract_stmbcave_shapes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_stmbcave_shapes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_stmbcave_shapes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_stmbcave_shapes --html-dir <dir> --write  # ...and rewrite

The second MID-GAME TECHNIQUE page (中盤テンプレ・ドネイト), after STSD: a T-spin Double whose T is laid
FLAT, pointing down, over a gap three columns wide that starts under its nub and runs away from the
overhang — the "cave" — with an S (or Z) hooked over the gap's other two columns. The spin is a TSD and
the anchor is the T's four cells, exactly as STSD's: what differs is only the window, so this page is a
data addition to the shared gate (`technique_transcription.py`) and matcher (`technique-facts.ts`).

WHERE THE TRANSCRIPTION COMES FROM. `NODES` is a literal, hand-checked transcription of the page's RAW
HTML, fetched the way STSD's was: curl through the session proxy, TLS verification on, with a CA bundle
adding the Let's Encrypt YE2 intermediate shiwehi.com omits. Seven boards, plain text in
`<div class="ttt">`, one row per line. The page is not committed; CI cannot fetch it.

WHY THE WINDOW IS THE AGREEMENT BOX (`window_basis: agreement`), not STSD's bounding box. The page draws
its one complete TSD (`feature.spin`) on a stacked board: the J, Z, L and O above the T are the rest of
the stack and are drawn differently on every other drawing of the shape. Under STSD's rule every one of
them would sit in the window. So the window is the box on which every drawing of the shape agrees cell
for cell — this page's three (the complete TSD, the basic form and the similar form, the last mirrored)
and harddrop's four positive STMB_Cave diagrams (`wiki-tspin-techniques.json`, another author on another
site) — and the gate checks that it is exactly that box: every drawing fires it once at its slot, and
widening it by a row or a column on any side meets a disagreement. It comes out three rows by six
columns: the T's row, its nub row and the row under them, from two columns behind the nub to the cave's
far wall. The page's roof (the stood Z over the T's back arm) is NOT in it: on `feature.spin` the cell
beside it is the L that roofs the NEXT TSD, which no other drawing has, and a rectangle cannot keep one
without the other.

WHAT THE WINDOW CAN AND CANNOT DISCRIMINATE. Its top two rows are the two rows the TSD clears, so at the
opportunity (a full TSD) every filled cell in them is entailed by the clear (NaiveClauseForced) — the
cave's roof is the nub row, which roofs it by definition (RoofForced / RoofCannotDiscriminate in
`spec/DonationCave.dfy`), and no roof test is added. What discriminates is the T's orientation (flat,
pointing down, the lock anchoring it) and the cave row: two filled cells behind the nub, the three cave
cells empty, the far wall filled. `stmbcave.test.ts` measures that the cave row alone gives the
headline.

THE FOLLOW-UP is the page's own claim (「TSDの地形でSTMB caveを行うと連続してTSDを狙うことができます」):
the TSD slot `feature.after` draws under the cave. It lies outside the window, so a hit on a terrain
with no such slot is still an STMB cave, and the follow-up table says how often the second TSD came.

WHAT IS AN INFERENCE, flagged in the JSON (`reading`) rather than in prose only:

  * upper-case letters are the spin's cleared rows in the renderer's muted colours (`C` an earlier
    cell, `T` the T, `J Z S L O` the pieces); the spin rule checks every upper-case row is a full row.
  * the basic form's terrain is drawn one column LEFT of the board built on it: named as a discrepancy
    (`basic.terrain:shift`), measured by this module, and the build is checked on the terrain it stands
    on, DERIVED (the board less its z and s).
  * the complete TSD has no drawn board before its T: DERIVED (`feature.pre`, the board less its T).
  * `feature.spin` draws its J as three cells and an L-coloured piece in a J's shape, and the similar
    form an S-coloured piece in a Z's shape: colour discrepancies, read as the renderer's colours used
    loosely, not other pieces (occupancy is all the matcher reads).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from pipeline.openers import technique_transcription as TT
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS
from pipeline.openers.route_transcription import EMPTY
from pipeline.openers.technique_transcription import node

HERE = Path(__file__).resolve().parent
OUT = HERE / 'stmbcave-technique.json'
WIKI = HERE / 'wiki-tspin-techniques.json'

ALPHABET = frozenset('-cCjlzstioJZTSLO')


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/stmbcave.php',
    'title': 'STMB Cave',
    'author': 'しゑひ(shiwehi)',
    'updated': '2021-03-23',
    'fetched': '2026-10-17',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle '
                    'that adds the Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), '
                    'the method STSD, 山岳積み2号 and stick spin used. The snapshot is the page\'s raw HTML, '
                    'byte for byte; every board is plain text in it, 7 ten-wide boards in page order.',
    'snapshot_file': 'stmbcave.html',
    'snapshot_sha256': 'd97c21d6eb70e868ca2ee2cd465cf4d9bc5a2a1f6f2e5132c8f2cde1ad66f88f',
    'snapshot_bytes': 25448,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable '
                     'in CI: the page is not committed and cannot be fetched there. Re-check with '
                     '--html-dir after any refetch; an HTML hash moves with ANY byte of the page (ads, '
                     'sidebar, a date), so a moved hash means "read the board diff", not "the boards '
                     'changed". Sentences are compared against the page with its tags dropped.',
    'renderer': {
        'url': 'https://shiwehi.com/tetris/mutual/column-exp.js?date=20210408',
        'note': 'the same script URL STSD\'s page loads (its bytes recorded in stsd-technique.json); not '
                're-hashed for this page',
        'mirror_button': 'body.reversed swaps j<->l, s<->z (and upper case); the page says %S(%Z) and '
                         '%Z(%S) for the two hands',
    },
    'decorative_images': ['STMB Caveタイトル画像'],
    'video': {'id': '-YZyjNNMSOw', 'start': 261, 'quote': 'video.permission',
              'note': 'embedded explainer by I凜 (the same video STSD\'s page embeds, a later start); not '
                      'transcribed, not used'},
    'references': ['https://tetrisch.github.io/main/ts/stmbcave.html (Tetrisちゃんねる; the page writes the '
                   'URL twice in one href)', 'https://four.lol/methods/stmb'],
    'unfetched': ['the two reference pages above — not fetched, not claimed'],
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ',
    '-': 'empty',
    'c': 'a cell filled before this diagram (any piece, or garbage), grey',
    'j l z s o i': 'a cell of that piece',
    'C': 'an earlier cell in a row the spin clears (muted; OUR READING, checked: every upper-case row is a full row)',
    'T J Z S L O': 'a cell of that piece in a row the spin clears (muted; OUR READING, checked the same way)',
    '%X': 'the X piece',
}

QUOTES = [
    {'id': 'intro', 'verbatim': 'ここでは、STMB caveというドネイトについて紹介していきます。'},
    {'id': 'name', 'verbatim': 'STMB caveの名前の由来は、STMB caveを紹介していた人が名前に付けていたタグ(STMB)と、'
                               'ドネイトの形状(cave=洞穴)から付けられているそうです。'},
    {'id': 'video.permission', 'verbatim': '※投稿主であるI凜さんに許可を得た上で動画を掲載しています。'},
    {'id': 'h.basic', 'verbatim': '基本形とラインの消し方'},
    {'id': 'basic', 'verbatim': 'STMB caveは、左右の高さが同じ3列の幅があるときに%S(%Z)を引っ掛けて、反対側に%Z(%S)'
                                'を立てることでTSDの形を作るドネイトです。'},
    {'id': 'h.feature', 'verbatim': 'STMB caveの特徴と類似形'},
    {'id': 'feature', 'verbatim': 'STMB caveは1段削るだけで、下穴に干渉せずTSDを作ることができます。'},
    {'id': 'feature.chain', 'verbatim': 'そのため、TSDの地形でSTMB caveを行うと連続してTSDを狙うことができます。'},
    {'id': 'h.similar', 'verbatim': '類似形'},
    {'id': 'similar', 'verbatim': '以下の様な形の場合、%Lを寝かせることによって、同等の形を作ることができます。'},
]

NODES = [
    {'id': 'basic.terrain', 'kind': 'base', 'caption_quote': 'basic', 'label': 'the terrain: a 3-wide gap, both sides level',
     'rows': _b('---------- ---------- ---------- ---------- ccc---cccc ccc---cccc')},
    {'id': 'basic.build', 'kind': 'build', 'on': 'basic.build.terrain', 'adds': 'zs', 'caption_quote': 'basic',
     'label': 'an S hooked over the gap and a Z stood on the other side: the TSD slot over the cave',
     'rows': _b('---------- ---z------ --zz------ --z---ss-- cccc-ssccc cccc---ccc')},
    {'id': 'feature.terrain', 'kind': 'base', 'caption_quote': 'feature',
     'label': 'the gap over a TSD terrain (a hole under its middle column)',
     'rows': _b('---------- ---------- ---------- ccc---cccc ccc---cccc cccc-ccccc')},
    {'id': 'feature.spin', 'kind': 'spin', 'spin_of': 'feature.pre', 'on': 'feature.pre', 'adds': 'T',
     'spin': 'TSD', 'lines': 2, 'caption_quote': 'feature',
     'label': 'the T laid flat into the slot, the stack around it filled up: a TSD clearing one row of the gap',
     'rows': _b('j-z------- jzz--llloo JZTTTSSLOO CCCTSSCCCC ccc---cccc cccc-ccccc')},
    {'id': 'feature.after', 'kind': 'after', 'after_of': 'feature.spin', 'caption_quote': 'feature.chain',
     'label': 'what the TSD leaves: the cave over the TSD terrain, roofed for a second TSD',
     'rows': _b('---------- c-c------- ccc--ccccc ccc---cccc cccc-ccccc')},
    {'id': 'similar.terrain', 'kind': 'base', 'caption_quote': 'similar', 'label': 'the similar terrain: a 4-wide gap over a 3-wide one',
     'rows': _b('---------- ---------- ---------- cc----cccc cc----cccc ccc---cccc')},
    {'id': 'similar.build', 'kind': 'build', 'on': 'similar.terrain', 'adds': 'ils', 'caption_quote': 'similar',
     'label': 'an L laid flat makes the same shape, mirrored (an I under the hooked side)',
     'rows': _b('---------- ------ss-- iiii---ss- cclll-cccc ccl---cccc ccc---cccc')},
    # ── derived: drawn nowhere on the page ──
    {'id': 'basic.build.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'basic.build less its z and s: the gap one column right of where basic.terrain draws it',
     'rows': _b('---------- ---------- ---------- ---------- cccc---ccc cccc---ccc')},
    {'id': 'feature.pre', 'kind': 'derived', 'derived': True, 'on': 'feature.terrain', 'adds': 'jzsloJZSLO',
     'reading': 'feature.spin less its T: the board the T went into',
     'rows': _b('j-z------- jzz--llloo JZ---SSLOO CCC-SSCCCC ccc---cccc cccc-ccccc')},
]

#: the variant's window, in feature.spin's frame
VARIANTS = [{
    'id': 'stmbcave', 'board': 'feature.spin', 'spin': 'TSD', 'lines': 2,
    'window_basis': 'agreement',
    'window': {'rows': [2, 4], 'cols': [1, 6]},
    't_cells': [[2, 2], [2, 3], [2, 4], [3, 3]],
    'roof_cells': [],
    'window_note': 'in feature.spin\'s frame, row 0 the top: the AGREEMENT BOX of every drawing in `agreement` '
                   'and harddrop\'s four positive STMB_Cave diagrams. Rows 2-3 are the two rows the TSD clears '
                   '(entailed by the clear at a full TSD, NaiveClauseForced: the nub row is the cave\'s roof, '
                   'RoofForced); row 4 is the cave row: two filled cells behind the nub, the three cave cells '
                   'empty, the far wall filled. Occupancy only, never colour; garbage is filled.',
    'untested_drawn': {
        'cells': [[0, 0], [0, 2], [1, 0], [1, 1], [1, 2], [1, 5], [1, 6], [1, 7], [1, 8], [1, 9]],
        'reason': 'the J, Z, L and O above the T: feature.spin is the page\'s stacked board, and no other drawing '
                  'of the shape agrees on these cells (the L at row 1, column 5 roofs the NEXT TSD, which the '
                  'basic and similar forms and harddrop\'s diagrams do not draw), so they are outside the '
                  'agreement box and not read',
    },
    'agreement': [
        {'board': 'feature.pre', 't_cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'mirrored': False},
        {'board': 'basic.build', 't_cells': [[3, 3], [3, 4], [3, 5], [4, 4]], 'mirrored': False},
        {'board': 'similar.build', 't_cells': [[2, 4], [2, 5], [2, 6], [3, 5]], 'mirrored': True},
    ],
    'followup': {'board': 'feature.after', 'spin': 'TSD', 'lines': 2,
                 't_cells_pre_clear': [[4, 3], [4, 4], [4, 5], [5, 4]],
                 't_cells_after': [[3, 3], [3, 4], [3, 5], [4, 4]],
                 'note': 'the flat T into the TSD slot the cave sits on, which feature.after draws (one row '
                         'shorter than feature.spin; compared bottom-aligned). It lies OUTSIDE the window: a hit '
                         'on a terrain with no such slot is still an STMB Cave, and the follow-up reports it.'},
    'fires_on': ['feature.pre'],
    'misses': ['basic.terrain', 'feature.terrain', 'similar.terrain', 'basic.build.terrain'],
}]

#: harddrop's STMB_Cave diagrams this gate reads out of `wiki-tspin-techniques.json` (transcribed and
#: gated by `extract_wiki_techniques`): the positives are external `agreement` drawings, the negative
#: must not fire anywhere
HARDDROP = {
    'file': 'wiki-tspin-techniques.json',
    'key': 'stmb_cave',
    'page': 'https://harddrop.com/wiki/STMB_Cave',
    'positives': [3, 6, 9, 18],
    'negatives': [2],
    'mirrored_reading': 'OUR READING, checked: a diagram whose cave starts left of its nub is the mirrored '
                        'hand; the agreement rule requires it to fire in exactly that orientation',
}

CROSS_SOURCE = {
    'kind': 'routes',
    'label_pattern': 'stmb',
    'note': 'the window, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot '
            'board of every committed *-routes.json, with the U cells as the T. `fires` is the independent '
            'drawer (harddrop\'s SDPC Spin page, another author); `also` is measured and named, not explained. '
            'harddrop\'s own STMB_Cave diagrams are the window\'s `agreement` drawings, not a cross-check of it.',
    'harddrop': HARDDROP,
    'fires': [
        {'file': 'sdpcspin-routes.json', 'node': '3.first.cave', 'variant': 'stmbcave', 'mirrored': True,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': 'harddrop\'s SDPC Spin: the STMB Cave of its first C-Spin build, the cave left of the nub'},
    ],
    'also': [],
    'labelled_not_fired': [
        {'file': 'honeycup-routes.json', 'node': '2.ideal.fire.stmb_template',
         'reason': 'a template with placeholder cells and no T slot drawn (no U): nothing to anchor on'},
        {'file': 'honeycup-routes.json', 'node': '2.ideal.fire.stmb_example',
         'reason': 'an example board with no T slot drawn (no U): nothing to anchor on'},
        {'file': 'meisou-routes.json', 'node': '2.ideal.fire.stmb_template',
         'reason': 'a template with placeholder cells and no T slot drawn (no U): nothing to anchor on'},
        {'file': 'meisou-routes.json', 'node': '2.ideal.fire.stmb_example',
         'reason': 'an example board with no T slot drawn (no U): nothing to anchor on'},
        {'file': 'sdpcspin-routes.json', 'node': '3.first.cave.stsd',
         'reason': 'the STSD the cave leads to (its label names the STMB Cave before it): a different technique'},
        {'file': 'sdpcspin-routes.json', 'node': '3.first.cave.stsd.next',
         'reason': 'the STSD\'s stood T, after the cave (its label names the STMB Cave before it)'},
        {'file': 'stickspin-routes.json', 'node': '2.sd.stmb',
         'reason': 'the cave before its T: no T slot drawn (no U); its spin board is 2.sd.stmb.spin'},
        {'file': 'stickspin-routes.json', 'node': '2.sd.stmb.spin',
         'reason': 'the same author\'s STMB Cave over a gap FOUR columns wide: the window\'s far wall (filled on '
                   'every agreement drawing) is empty there. Measured, not explained'},
    ],
    'same_author_corroboration': 'stickspin-routes.json 2.sd.stmb.spin (shiwehi.com, the same author): not independent',
    'unfetched': ['https://harddrop.com/wiki/SDPC_Spin is read from sdpcspin-routes.json, not refetched here'],
}

KNOWN_DISCREPANCIES = [
    {'id': 'feature.spin:colour',
     'note': 'the stacked board draws its J as three cells (column 0) and an L-coloured piece in a J\'s shape '
             '(row 1, columns 5-7, with row 2, column 7): the renderer\'s colours used loosely, read by '
             'occupancy only, which is all the matcher compares'},
    {'id': 'feature.pre:colour',
     'note': 'feature.spin less its T, so the same two pieces as feature.spin:colour'},
    {'id': 'similar.build:colour',
     'note': 'the similar form\'s S-coloured piece is drawn in a Z\'s shape (rows 1-2, columns 6-8): read by '
             'occupancy; the page\'s own sentence names only the L laid flat'},
    {'id': 'basic.terrain:shift',
     'note': 'the basic form\'s terrain draws its gap in columns 3-5; the board built on it (basic.build) has '
             'the gap in columns 4-6. Read as the terrain drawn one column left; the build is checked on the '
             'terrain it stands on, derived (basic.build.terrain), and this module measures the shift.'},
]

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'stmbcave',
        'source': SOURCE,
        'terms': TERMS,
        'legend': LEGEND,
        'empty_letters': '',
        'quotes': QUOTES,
        'nodes': NODES,
        'page_order': PAGE_ORDER,
        'basic_form': [],
        'variants': VARIANTS,
        'cross_source': CROSS_SOURCE,
        'known_discrepancies': KNOWN_DISCREPANCIES,
    }


# ── harddrop's drawings ──────────────────────────────────────────────────────────────────────────
def _hd_controls():
    return {c['diagram_index']: c for c in json.loads(WIKI.read_text())['stmb_cave']['controls']}


def _hd_rows(c):
    return [''.join(EMPTY if ch == '.' else ch for ch in r) for r in c['rows']]


def harddrop_drawings(data: dict | None = None) -> list[dict]:
    """harddrop's positive diagrams as agreement drawings. `t_cells` there are [col, row]; the hand is
    read off the cave: a cave that starts left of the nub is the mirrored one."""
    data = data or build()
    hd = data['cross_source']['harddrop']
    out = []
    ctl = _hd_controls()
    for i in hd['positives']:
        c = ctl[i]
        cells = [[r, col] for col, r in c['t_cells']]
        nub = max(cells)                      # the lowest T cell, the nub
        out.append({'name': f'harddrop STMB_Cave diagram {i}', 'rows': _hd_rows(c), 't_cells': cells,
                    'mirrored': c['cave_first_col'] < nub[1]})
    return out


def _holes(rows, k=0):
    """The empty cells of a board's non-empty rows (the gap), every column moved `k` to the right."""
    return {(r, c + k) for r, row in enumerate(rows) if row.strip(EMPTY)
            for c, ch in enumerate(row) if ch == EMPTY}


def extra_checks(data: dict):
    bad, measured = [], set()
    hd = data['cross_source'].get('harddrop', {})
    ctl = _hd_controls()
    kinds = {i: c['kind'] for i, c in ctl.items()}
    if sorted(hd.get('positives', [])) != sorted(i for i, k in kinds.items() if k == 'positive') \
            or sorted(hd.get('negatives', [])) != sorted(i for i, k in kinds.items() if k == 'negative'):
        bad.append(f'harddrop: the recorded diagrams {hd.get("positives")} / {hd.get("negatives")} are not '
                   f'{HARDDROP["file"]}\'s positives and negatives')
    # the negative control: harddrop's 「no overhang yet」 board fires nowhere, either hand
    for i in hd.get('negatives', []):
        rows = _hd_rows(ctl[i])
        for v in data['variants']:
            if any(TT.window_fires(data, v, SPEC, rows, cs, m) for cs in TT.t_placements(rows, SPEC) for m in (False, True)):
                bad.append(f'harddrop: {v["id"]} fires on harddrop\'s negative diagram {i}')
    # the basic terrain's shift, measured: drawn one column left of the board built on it
    by = {n['id']: n for n in data['nodes']}
    t, d = by['basic.terrain']['rows'], by['basic.build.terrain']['rows']
    # the gap is the board's empty cells; drawn one column left, the rest of the row is filled either way
    if len(t) != len(d):
        bad.append('build: basic.build.terrain is not as tall as basic.terrain')
    elif _holes(t) == _holes(d):
        pass
    elif _holes(t, 1) == _holes(d):
        measured.add('basic.terrain:shift')
    else:
        bad.append('build: basic.build.terrain\'s gap is neither basic.terrain\'s nor one column right of it')
    return bad, measured


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='',
    upper_groups={u: 'merge' for u in 'TJZSLO'},
    extra_checks=extra_checks,
    external_drawings=lambda: harddrop_drawings(),
)


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def _set(rows, r, c, ch):
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _var(d):
    return d['variants'][0]


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'basic.terrain')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: d['page_order'].reverse(), 'page_order swapped', 'grammar:'),
    (lambda d: node(d, 'feature.spin').__setitem__('spin_of', 'nowhere'), 'a dangling reference', 'grammar:'),
    (lambda d: _set(node(d, 'similar.build')['rows'], 5, 0, '-'), 'a build board cell flipped', 'build:'),
    (lambda d: _set(node(d, 'feature.pre')['rows'], 0, 1, 'j'), 'the derived board edited', 'build:'),
    (lambda d: (_set(node(d, 'feature.spin')['rows'], 3, 3, 'C'), _set(node(d, 'feature.spin')['rows'], 3, 4, 'T')),
     'the T moved one cell', 'spin:'),
    (lambda d: _set(node(d, 'feature.spin')['rows'], 3, 0, 'c'), 'a cleared row drawn unmuted', 'spin:'),
    (lambda d: node(d, 'feature.spin').__setitem__('lines', 1), 'the spin\'s line count', 'spin:'),
    (lambda d: _set(node(d, 'feature.after')['rows'], 1, 1, 'c'), 'the after board not what the spin leaves', 'discrepancy:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [1, 7]), 'the window widened by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [1, 5]), 'the window narrowed by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [2, 3]), 'the window without its cave row', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [1, 4]), 'the window up to the roof row', 'window:'),
    (lambda d: _var(d)['untested_drawn']['cells'].pop(), 'an untested piece letter unnamed', 'window:'),
    (lambda d: _var(d)['untested_drawn']['cells'].append([5, 4]), 'an empty cell named untested', 'window:'),
    (lambda d: _var(d)['roof_cells'].append([1, 2]), 'a roof cell outside the window', 'window:'),
    (lambda d: _var(d)['agreement'][2].__setitem__('mirrored', False), 'the similar form read as drawn', 'window:'),
    (lambda d: _var(d)['agreement'][1].__setitem__('t_cells', [[3, 2], [3, 3], [3, 4], [4, 3]]),
     'a slot moved one column', 'window:'),
    (lambda d: _var(d).__setitem__('agreement', []), 'only one page drawing left in the agreement', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('t_cells_after', [[4, 3], [4, 4], [4, 5], [5, 4]]),
     'the follow-up slot read without the height shift', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('lines', 1), 'the follow-up line count', 'window:'),
    (lambda d: _var(d)['fires_on'].append('feature.terrain'), 'a board it cannot fire on listed', 'window:'),
    (lambda d: _var(d)['misses'].append('basic.build'), 'a board it fires on listed as a miss', 'window:'),
    (lambda d: _set(node(d, 'basic.build')['rows'], 1, 3, 'j'), 'a piece broken', 'discrepancy:'),
    (lambda d: d['cross_source']['fires'][0].__setitem__('node', '3.first.cav'), 'a cross-route node renamed', 'cross:'),
    (lambda d: d['cross_source']['labelled_not_fired'].pop(0), 'a labelled board neither firing nor named', 'cross:'),
    (lambda d: d['cross_source']['fires'].clear(), 'no cross source', 'cross:'),
    (lambda d: d['cross_source']['harddrop']['negatives'].clear(), 'harddrop\'s negative dropped', 'harddrop:'),
    (lambda d: node(d, 'similar.build').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['known_discrepancies'].append({'id': 'similar.terrain:colour', 'note': 'x'}), 'a stale discrepancy', 'discrepancy:'),
    (lambda d: node(d, 'basic.build.terrain').__setitem__('rows', node(d, 'basic.terrain')['rows']) or
     node(d, 'basic.build').__setitem__('rows', ['-' * 10, '--z-------', '-zz-------', '-z---ss---', 'ccc-ssCccc', 'ccc---cccc']),
     'the basic form redrawn on its terrain', 'discrepancy:'),
]


def _no_external(spec):
    s = copy.copy(spec)
    s.external_drawings = None
    return s


def _negative_as_positive(spec):
    s = copy.copy(spec)
    neg = _hd_controls()[2]
    s.external_drawings = lambda: harddrop_drawings() + [{'name': 'harddrop negative', 'rows': _hd_rows(neg),
                                                          't_cells': [[2, 4], [2, 5], [2, 6], [3, 5]], 'mirrored': False}]
    return s


SPEC_MUTANTS = [
    (_no_external, 'no external drawing (the window checked against this page alone)', 'window:'),
    (_negative_as_positive, 'harddrop\'s negative read as a positive', 'window:'),
]


def selftest() -> int:
    return TT.run_selftest(SPEC, MUTANTS, {'board': ('cccc-ssccc', 'cccc--sccc'),
                                           'text': ('類似形', '同類形')},
                           SPEC_MUTANTS)


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))

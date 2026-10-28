"""Transcribe harddrop's Gamushiro Stacking page (its bag-2 forms and 8-line PC lists) into `hdgamushiro-routes.json`.

    python3 -m pipeline.openers.extract_hdgamushiro_routes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_hdgamushiro_routes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_hdgamushiro_routes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_hdgamushiro_routes --html-dir <dir> --write  # ...and rewrite

The seventh opener ROUTE page, and the second for one opener: shiwehi.com's ガムシロ積み page is
`gamushiro-routes.json`; this is harddrop's own page for the same opener (by Mr. Goods), which draws
what that page does not — two more bag-2 forms that can still take the 8-line PC (Form B, the O beside
the I at the left; Form C, the O in the middle) with six PC solutions each, and a fifth form (Form D)
that cannot. Both pages are kept, side by side, rather than merged: one routes file has one source.

WHAT IS TRANSCRIBED, AND WHAT IS NOT. The page draws 119 boards. This file transcribes boards 8 to 40
(0-based, every board of the page in page order): the First Bag setup (four boards), the Second Bag
forms (five) and the Third Bag (Perfect Clear) section (three lists of a redraw, an after-the-TST board
and six PC solutions). Boards 0-7 (the Introduction, an overview of one route) and 41-118 (the other
continuations: Imperial Cross, Center 4-wide, Nil-cross, Trinity, TST, DT Cannon, the 10- and 14-line PCs
and the ideal / compromise 14-line routes) are named in `source.boards_not_transcribed` with a reason
each. `--html-dir` still reads the page's board count and refuses a page whose count moved.

WHERE IT COMES FROM. The page's WIKITEXT, revision 37490 (the same revision ガムシロ積み's HTML
cross-source pins), fetched through `api.php` with Python's urllib (never curl); `source` records the
revision's own sha1 beside our sha256, so `check_wikitext_sources` discovers this file and refetches the
revision every week. Boards are `{{pfstart}}` templates read by `route_transcription.wikitext_boards`,
with two readings this page needs (`source.wikitext_readings`): it draws an ordinary T as `T` (the bag-1
T, the PC solutions' T) and only the spun T as `P`, so `T` reads `t`; and it draws the held bag-1 L as
the two-letter `LL` on the Second Bag boards and as `-L` on their redraws, both read `L`.

THE CROSS-SOURCE IS SHIWEHI.COM'S PAGE, through `gamushiro-routes.json` (another author, another
site; both committed, so rule 2 is offline): the two bag-1 boards, the two forms both pages draw (Form
A1 = 2.normal#1, Form A2 = 2.normal#2) and harddrop's six L → O PC solutions (shiwehi's 2.normal.pc#1-6,
in the same order) are equal cell for cell, every U read as empty. Forms B, C and D and their PC lists
have no second source.

WHAT IS AN INFERENCE, flagged in the JSON:

  * which Second Bag board is which form. The page names forms only in its later 「Form A1 and A2
    (L → O)」 … 「Form D (O → L)」 headings; the five boards are read in that order (checked where the
    later sections redraw them: board 50 is board 16 with the held L greyed, board 46 builds on board
    14's O beside the I). The arrows are kept as labels and NOT read as dealing orders: Form A2 draws its
    O under both Ls while its heading says L → O.
  * the PC lists are anchored where the page draws them: the L → O list after Form A1's redraw, and it
    applies to Form A2 too because the two share one occupancy (checked), as shiwehi's 2.normal group.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers.extract_sdpcspin_routes import TERMS as HARDDROP_TERMS
from pipeline.openers.route_transcription import EMPTY, after_spin, bottom, mirror, node, setcell, t_slot

HERE = Path(__file__).resolve().parent
OUT = HERE / 'hdgamushiro-routes.json'
SHIWEHI = 'gamushiro-routes.json'

ALPHABET = frozenset('-ijlostzcUL')


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://harddrop.com/wiki/Gamushiro_Stacking',
    'edit_url': 'https://harddrop.com/w/index.php?title=Gamushiro_Stacking&action=edit',
    'title': 'Gamushiro Stacking',
    'author': 'Mr. Goods (page text: 「created by \'\'Mr. Goods\'\'」)',
    'site': 'harddrop.com (Hard Drop Tetris Wiki, MediaWiki)',
    'updated': '2023-11-01',
    'updated_note': 'the timestamp of the pinned revision, read from the API',
    'oldid': 37490,
    'oldid_note': 'the revision ガムシロ積み\'s HTML cross-source (gamushiro-routes.json) pins too; the page\'s newest on 2026-10-27',
    'pageid': 6672,
    'categories': ['T-Spin techniques', 'T-Spin openers', 'Triple Double openers', 'Perfect Clear techniques',
                   'Perfect Clear openers'],
    'fetched': '2026-10-27',
    'fetch_method': 'the revision\'s own bytes from the MediaWiki API (`api.php?action=query&prop=revisions&titles=Gamushiro_Stacking'
                    '&rvprop=ids|sha1|size|timestamp|content&rvslots=main&format=json`), with Python\'s urllib and '
                    '`check_wikitext_sources.USER_AGENT` (NOT curl); the API\'s sha1 checked against sha1 of the bytes. '
                    'Boards are {{pfstart}} … {{pfend}} templates, 119 of them, read by route_transcription.wikitext_boards',
    'revision_sha1': '76796a37af838b8fac62bbef96b2963c68d0da1b',
    'revision_timestamp': '2023-11-01T18:52:20Z',
    'revision_note': 'MediaWiki\'s own sha1 of revision 37490 (read 2026-10-27 from the API), equal to sha1 of the saved bytes',
    'snapshot_file': 'Gamushiro_Stacking.wikitext',
    'snapshot_sha256': '81d6b2ec20144dce03d78d7c5551f2f7996ca34a8ba9bd517614bc197fb9f7b8',
    'snapshot_bytes': 34227,
    'snapshot_note': 'sha256 of the revision\'s bytes as the API serves them. The page is not committed; the weekly '
                     '`wikitext-sources` job refetches the pinned revision, checks both hashes and re-runs --html-dir, '
                     'and fails when the page has a newer revision',
    'wikitext_readings': {'T': 't', '-L': 'L'},
    'wikitext_readings_note': 'OUR READING: the page draws the spun T as P (read U, the shared default) and every other T as T, '
                              'so T reads t here (the default reads it U, SDPC Spin\'s page using T for the spun T); the held '
                              'bag-1 L is drawn LL on the Second Bag boards (read L by default) and -L on their redraws',
    'boards_not_transcribed': [
        {'boards': [0, 7], 'heading': 'Introduction',
         'reason': 'an overview of one route (the 7-lock bag 1, Form A1, its TST, the board after it, a TSD and a PC), every board '
                   'redrawn in the sections below'},
        {'boards': [41, 118], 'heading': 'Third Bag and later (Other continuations); Perfect Clear after 10 or 14 lines; '
                                         'ideal shape / compromise shape subspecies → Always 14-lines PC',
         'reason': 'continuations past the 8-line PC (Imperial Cross, Center 4-wide, Nil-cross, Trinity, TST, DT Cannon, DT Cannon 2, '
                   'the 10- and 14-line PCs, the 14-line routes): not transcribed in this pass, so nothing here is a claim about them'},
    ],
    'boards_note': 'indexes are 0-based over every board of the page in page order',
    'references_listed': ['https://tetris-matome.com/gamushiro/', 'https://harddrop.com/wiki/Yamaha_Stacking',
                          'https://harddrop.com/wiki/Mountainous_Stacking', 'https://harddrop.com/wiki/PC-Spin'],
    'references_note': 'the page\'s See also and External links, as URLs; none of them is read here',
}

#: shiwehi.com's ガムシロ積み page, through its committed transcription: rule 2's `routes_file` route
CROSS_PAIRS = [['bag1.left', 'bag1.left'], ['bag1.l_top', 'bag1.l_top'],
               ['2.a1', '2.normal#1'], ['2.a2', '2.normal#2']] + [
              [f'2.a.pc#{i}', f'2.normal.pc#{i}'] for i in range(1, 7)]

CROSS_SOURCE = {
    'kind': 'routes_file',
    'file': SHIWEHI,
    'pairs': CROSS_PAIRS,
    'what': 'shiwehi.com\'s ガムシロ積み page (gamushiro.php, 2024-08-01 版), transcribed and gated in gamushiro-routes.json: '
            'another author on another site. Each pair is equal cell for cell with every U read as empty (shiwehi draws the two '
            '通常 forms with the TST slot empty, this page with the T in it), as drawn or mirrored',
    'not_covered': 'Forms B, C and D and the J → O and S → O PC lists: shiwehi draws none of them, so they have no second source',
}

TERMS = {**HARDDROP_TERMS,
         'read': '2026-10-15, for SDPC Spin (the same wiki, no licence published); not re-read for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ, align at the BOTTOM row',
    '-': 'empty (a blank cell or {{pfrowblank}})',
    'i o t s z j l': 'a cell of that piece (the page\'s single upper-case letter; T is an ordinary T here, see source.wikitext_readings)',
    'c': 'a cell placed before this diagram, drawn grey G (checked: exactly the bag-1 board, or what the TST leaves)',
    'L': 'the bag-1 L, held and placed in bag 2: the page\'s LL (Second Bag) and -L (the redraws). OUR READING, checked: on Forms A1, '
         'B, C and D its four cells are exactly where bag1.l_top stands the L',
    'U': 'the T in its TST slot, drawn P (purple)',
    'label_jp': 'the source\'s own words (here English): a heading or the bullet over a list, never a caption of ours',
}

#: Every sentence the transcription leans on, verbatim from the wikitext (markup kept, so --html-dir
#: finds each byte for byte); every `*_verbatim` field below must be one of these (`_hd_checks`).
QUOTES = [
    {'id': 'overview.intro', 'figure': None,
     'verbatim': "'''Gamushiro Stacking''' (ガムシロ積み) is a T-Spin [[opener]] created by ''Mr. Goods''. It is a [[Triple Double Attack]] opener."},
    {'id': 'overview.bag1', 'figure': None,
     'verbatim': 'In the first bag, only the J piece is required before the S. If the mirrored setup is considered, it is always possible to stack the first bag.'},
    {'id': 'bag1.requires', 'figure': None,
     'verbatim': 'You only need the J piece before S (L before Z in the mirrored setup). The L piece is kept on hold as it will be used along with the second bag.'},
    {'id': 'bag1.seven', 'figure': '7', 'verbatim': 'Here is the first bag with all 7 pieces:'},
    {'id': '2.forms', 'figure': '2 / 4',
     'verbatim': 'The second bag is always placed in one of these ways. The first 2 ways are the most desirable ways. The first 4 ways can result in a Perfect Clear.'},
    {'id': '3.pc', 'figure': '8',
     'verbatim': 'In the case of the first 4 forms mentioned, you can get a [[Perfect Clear]] after 8 total lines.'},
    {'id': '2.a.pc', 'figure': '99.09% / 22', 'verbatim': 'L → O (99.09% PC rate, 22 minimal solutions)'},
    {'id': '2.b.pc', 'figure': '96.94% / 19', 'verbatim': 'J → O (96.94% PC rate, 19 minimal solutions)'},
    {'id': '2.c.pc', 'figure': '86.59% / 15', 'verbatim': 'S → O (86.59% PC rate, 15 minimal solutions)'},
    {'id': 'form.a', 'figure': None, 'verbatim': '=== Form A1 and A2 (L → O) ==='},
    {'id': 'form.b', 'figure': None, 'verbatim': '=== Form B (J → O) ==='},
    {'id': 'form.c', 'figure': None, 'verbatim': '=== Form C (S → O) ==='},
    {'id': 'form.d', 'figure': None, 'verbatim': '=== Form D (O → L) ==='},
]

BAG1 = {
    'locks': 6,
    'hold': 'L',
    'requires_verbatim': 'You only need the J piece before S (L before Z in the mirrored setup). The L piece is kept on hold as it will be used along with the second bag.',
    'requires': {'all': [{'before': ['J', 'S']}], 'early': None, 'node': 'bag1.left'},
    'requires_note': 'read as an order, checked against bag1.left by support (an S cell rests on a J cell)',
    'seven_verbatim': 'Here is the first bag with all 7 pieces:',
    'seven_note': 'the 7-lock board (the L stood on the O) and its mirror; read as bag1.l_top, the board ガムシロ積み\'s page draws as 基本形 1',
}

KNOWN_DISCREPANCIES = [
    {'id': '2.a.pc:stated_vs_drawn', 'what': 'the page states 22 minimal solutions for L → O and draws 6'},
    {'id': '2.a.pc:non_exhaustive', 'what': 'the 6 drawn L → O solutions are not every way to take the PC'},
    {'id': '2.b.pc:stated_vs_drawn', 'what': 'the page states 19 minimal solutions for J → O and draws 6'},
    {'id': '2.b.pc:non_exhaustive', 'what': 'the 6 drawn J → O solutions are not every way to take the PC'},
    {'id': '2.c.pc:stated_vs_drawn', 'what': 'the page states 15 minimal solutions for S → O and draws 6'},
    {'id': '2.c.pc:non_exhaustive', 'what': 'the 6 drawn S → O solutions are not every way to take the PC'},
    {'id': '2.a2:arrow_vs_board',
     'what': 'Form A2 is headed L → O with Form A1, but its O lies under both Ls (the held one and the bag-2 one rest on it): the '
             'arrow is not the order its pieces went down, so no form\'s arrow is read as a dealing order'},
    {'id': 'forms:no_names_on_boards',
     'what': 'the five Second Bag boards carry no names; the forms are named only by later headings (Form A1 and A2 … Form D), read '
             'in board order'},
]


def _form(nid, k, label, heading, rows, **kw) -> dict:
    return {'id': nid, 'bag': 2, 'parent': None, 'base': 'bag1.left', 'spin': 'TST', 'locks': 13,
            'label_jp': heading, 'label': label, 'form_heading_verbatim': f'=== {heading} ===', 'board': k,
            'condition': None, 'rows': _b(rows), **kw}


#: Every node, in page order (the PC patterns are inserted after their anchor by `build`).
NODES: list[dict] = [
    {'id': 'bag1.left', 'bag': 1, 'parent': None, 'locks': 6, 'board': 8,
     'label_jp': 'First Bag setup',
     'label': 'bag 1 with the L held (the first First Bag setup board; shiwehi\'s bag1.left)',
     'rows': _b('---------- s------i-- ss----ti-- js-zzttioo jjj-zztioo')},
    {'id': 'bag1.right', 'bag': 1, 'parent': None, 'locks': 6, 'board': 9,
     'label_jp': 'First Bag setup — Mirrored', 'label': 'bag 1 with the J held, mirrored',
     'mirror_of': 'bag1.left',
     'rows': _b('---------- --i------z --it----zz ooittss-zl ooitss-lll')},
    {'id': 'bag1.l_top', 'bag': 1, 'parent': None, 'locks': 7, 'board': 10,
     'label_jp': 'First Bag setup — the first bag with all 7 pieces',
     'label': 'bag 1 with all seven pieces: the L stood on the O at the right (shiwehi\'s bag1.l_top)',
     'rows': _b('---------- --------l- s------il- ss----till js-zzttioo jjj-zztioo')},
    {'id': 'bag1.l_top_right', 'bag': 1, 'parent': None, 'locks': 7, 'board': 11,
     'label_jp': 'First Bag setup — the first bag with all 7 pieces, Mirrored', 'label': 'the seven-piece bag 1, mirrored',
     'mirror_of': 'bag1.l_top',
     'rows': _b('---------- -j-------- -ji------z jjit----zz ooittss-zl ooitss-lll')},
    _form('2.a1', 12, 'Form A1: the O on the held L at the right (shiwehi\'s 2.normal#1)', 'Form A1 and A2 (L → O)',
          '---------- ---------- ---------- i-------oo i-------oo ijj-----ll ij----ssLl cjUzzsscLl ccUUzzccLL ccUccccccc ccc-cccccc',
          group='2.a', variant=1),
    _form('2.a2', 13, 'Form A2: the O at the right under both Ls (shiwehi\'s 2.normal#2)', 'Form A1 and A2 (L → O)',
          '---------- ---------- ---------- i-------ll i-------Ll ijj-----Ll ij----ssLL cjUzzsscoo ccUUzzccoo ccUccccccc ccc-cccccc',
          group='2.a', variant=2),
    _form('2.b', 14, 'Form B: the O beside the I at the left', 'Form B (J → O)',
          '---------- ---------- ---------- ioo------- ioo------- ijj-----ll ij----ssLl cjUzzsscLl ccUUzzccLL ccUccccccc ccc-cccccc'),
    _form('2.c', 15, 'Form C: the O in the middle, on the S', 'Form C (S → O)',
          '---------- ---------- ---------- i--------- i-----oo-- ijj---ooll ij----ssLl cjUzzsscLl ccUUzzccLL ccUccccccc ccc-cccccc'),
    _form('2.d', 16, 'Form D: the I stood at the right wall, the O and L stacked over the held L', 'Form D (O → L)',
          '---------- -------l-- -------l-- -------ll- -------ooi -jj----ooi -j----ssLi cjUzzsscLi ccUUzzccLL ccUccccccc ccc-cccccc',
          unmatchable='10 non-empty rows > ROWS = 8',
          pc_note='the page says only the first 4 forms can take the PC: no PC list hangs under Form D'),
    {'id': '2.a.redraw', 'bag': 2, 'parent': '2.a', 'node_kind': 'illustration', 'board': 17, 'redraw_of': '2.a1',
     'label_jp': 'Third Bag (Perfect Clear) — L → O', 'label': 'Form A1 redrawn over its PC list (checked: the same board)',
     'rows': _b('---------- i-------oo i-------oo ijj-----ll ij----ssLl cjUzzsscLl ccUUzzccLL ccUccccccc ccc-cccccc')},
    {'id': '2.a.after', 'bag': 2, 'parent': '2.a', 'node_kind': 'illustration', 'board': 18, 'after_of': '2.a1',
     'label': 'Forms A1 and A2 after the TST (checked by occupancy; the two forms leave one board)',
     'rows': _b('---------- ---------- ---------- ---------- i-------oo i-------oo ijj-----ll ij----ssll ccc-cccccc')},
    {'id': '2.b.redraw', 'bag': 2, 'parent': '2.b', 'node_kind': 'illustration', 'board': 25, 'redraw_of': '2.b',
     'label_jp': 'Third Bag (Perfect Clear) — J → O', 'label': 'Form B redrawn over its PC list (checked: the same board)',
     'rows': _b('---------- ioo------- ioo------- ijj-----ll ij----ssLl cjUzzsscLl ccUUzzccLL ccUccccccc ccc-cccccc')},
    {'id': '2.b.after', 'bag': 2, 'parent': '2.b', 'node_kind': 'illustration', 'board': 26, 'after_of': '2.b',
     'label': 'Form B after the TST (checked by occupancy)',
     'rows': _b('---------- ---------- ---------- ---------- ioo------- ioo------- ijj-----ll ij----ssll ccc-cccccc')},
    {'id': '2.c.redraw', 'bag': 2, 'parent': '2.c', 'node_kind': 'illustration', 'board': 33, 'redraw_of': '2.c',
     'label_jp': 'Third Bag (Perfect Clear) — S → O', 'label': 'Form C redrawn over its PC list (checked: the same board)',
     'rows': _b('---------- i--------- i-----oo-- ijj---ooll ij----ssLl cjUzzsscLl ccUUzzccLL ccUccccccc ccc-cccccc')},
    {'id': '2.c.after', 'bag': 2, 'parent': '2.c', 'node_kind': 'illustration', 'board': 34, 'after_of': '2.c',
     'label': 'Form C after the TST (checked by occupancy)',
     'rows': _b('---------- ---------- ---------- ---------- i--------- i-----oo-- ijj---ooll ij----ssll ccc-cccccc')},
]

GROUPS = [
    {'id': '2.a', 'heading': 'Form A1 and A2 (L → O)', 'drawn': 2,
     'text_verbatim': 'The second bag is always placed in one of these ways. The first 2 ways are the most desirable ways. The first 4 ways can result in a Perfect Clear.',
     'note': 'the page\'s first two ways, one occupancy (checked), one PC list'},
]

LISTS = [
    {'id': '2.a.pc', 'parent': '2.a', 'base': '2.a.after', 'bag': 3, 'heading': 'L → O', 'board_first': 19,
     'rate_verbatim': 'L → O (99.09% PC rate, 22 minimal solutions)', 'stated_pattern_count': 22,
     'shown': 6, 'rest_stated': 0, 'complete': False, 'total_lines': 8, 'total_lines_quote': '3.pc',
     'rows': ['---------- cjiiiillcc cjjjsszlcc cccsszzlcc cctttzcccc ccctcccccc',
              '---------- cjiiiioocc cjjjssoocc cccsslllcc cctttlcccc ccctcccccc',
              '---------- ciiiilllcc cjjjsloocc cccjssoocc cctttscccc ccctcccccc',
              '---------- coojjtttcc coojsstlcc cccsslllcc cciiiicccc cccjcccccc',
              '---------- ciiiizoocc cjjjzzoocc cccjzlllcc cctttlcccc ccctcccccc',
              '---------- cjzziiiicc cjjjlloocc ccczzloocc cctttlcccc ccctcccccc']},
    {'id': '2.b.pc', 'parent': '2.b', 'base': '2.b.after', 'bag': 3, 'heading': 'J → O', 'board_first': 27,
     'rate_verbatim': 'J → O (96.94% PC rate, 19 minimal solutions)', 'stated_pattern_count': 19,
     'shown': 6, 'rest_stated': 0, 'complete': False, 'total_lines': 8, 'total_lines_quote': '3.pc',
     'rows': ['---------- cccooiiiil cccoozzlll cccjjjzzcc cctttjcccc ccctcccccc',
              '---------- cccjjiiiil cccjszzlll cccjsszzcc cctttscccc ccctcccccc',
              '---------- cccoosiiii cccoosslll cccjjjslcc cctttjcccc ccctcccccc',
              '---------- cccjjjiiii cccoojzlll cccoozzlcc cctttzcccc ccctcccccc',
              '---------- cccjjtttoo cccjsstloo cccsslllcc cciiiicccc cccjcccccc',
              '---------- cccjsslloo cccjjjzloo cccsszzlcc cctttzcccc ccctcccccc']},
    {'id': '2.c.pc', 'parent': '2.c', 'base': '2.c.after', 'bag': 3, 'heading': 'S → O', 'board_first': 35,
     'rate_verbatim': 'S → O (86.59% PC rate, 15 minimal solutions)', 'stated_pattern_count': 15,
     'shown': 6, 'rest_stated': 0, 'complete': False, 'total_lines': 8, 'total_lines_quote': '3.pc',
     'rows': ['---------- ciiiillloo cjjjslccoo cccjsscccc cctttscccc ccctcccccc',
              '---------- cllliiiioo clstttccoo cccjjjcccc ccsstjcccc cccscccccc',
              '---------- cllliiiioo clsjjjccoo ccctttcccc ccsstjcccc cccscccccc',
              '---------- cjzziiiioo cjjjllccoo ccczzlcccc cctttlcccc ccctcccccc',
              '---------- cllliiiioo cltttjccoo cccssjcccc ccssjjcccc ccctcccccc',
              '---------- cstttllloo csstzlccoo cccjjjcccc ccszzjcccc ccczcccccc']},
]

#: where each list's patterns are inserted in page order: after this node
_LIST_AFTER = {'2.a.pc': '2.a.after', '2.b.pc': '2.b.after', '2.c.pc': '2.c.after'}

#: the solutions each list counts and does not draw: the page states the count and nothing else, so
#: each is a text-only node whose `page_text` must still be on the page.
NON_BOARD = {f'{k}.rest': 'text_only' for k in ('2.a.pc', '2.b.pc', '2.c.pc')}


def _rest_node(lst: dict, drawn: int) -> dict:
    return {'id': f'{lst["id"]}.rest', 'bag': lst['bag'], 'parent': lst['parent'], 'node_kind': 'text_only',
            'label_jp': f'{lst["heading"]}（冇畫嘅解法）',
            'page_text': f'{lst["stated_pattern_count"]} minimal solutions',
            'note': f'the page states {lst["stated_pattern_count"]} minimal solutions and draws {drawn}; the rest are not on it'}


def _pattern_nodes(lst: dict) -> list[dict]:
    out = []
    for i, text in enumerate(lst['rows'], 1):
        rows = _b(text)
        pieces = ''.join(sorted({ch for r in rows for ch in r if ch in 'ijlostz'}))
        out.append({'id': f'{lst["id"]}#{i}', 'bag': lst['bag'], 'parent': lst['parent'],
                    'base': lst['base'], 'list': lst['id'], 'index': i, 'board': lst['board_first'] + i - 1,
                    'listed_under': 'shown', 'label_jp': f'{lst["heading"]} {i}', 'pieces': pieces, 'rows': rows})
    return out


PAGE_ORDER = (
    ['bag1.left', 'bag1.right', 'bag1.l_top', 'bag1.l_top_right', '2.a1', '2.a2', '2.b', '2.c', '2.d']
    + ['2.a.redraw', '2.a.after'] + [f'2.a.pc#{i}' for i in range(1, 7)]
    + ['2.b.redraw', '2.b.after'] + [f'2.b.pc#{i}' for i in range(1, 7)]
    + ['2.c.redraw', '2.c.after'] + [f'2.c.pc#{i}' for i in range(1, 7)]
)


def _tsd_slot(rows: list[str]) -> bool:
    """The four t cells are the flat ttt-over-t shape in the body's bottom two rows: where every
    after-the-TST board here leaves its only TSD-shaped gap (ガムシロ積み's position test)."""
    body = bottom(rows, 0)
    return sum(r.count('t') for r in body) == 4 and t_slot(body[-2:], 't') == 'flat'


SLOT_FLAGS = {'has_u_slot': lambda rows: t_slot(rows) is not None,
              't_in_tsd_slot': _tsd_slot}

SLOT_FLAG_MEANING = {
    'has_u_slot': 'the pattern draws a U (T-spin slot) cell',
    't_in_tsd_slot': 'the pattern\'s four t cells are the flat ttt-over-t shape in its BOTTOM TWO body rows, where the board after the '
                     'TST leaves its only TSD-shaped gap: a TSD before the PC (gamushiro-routes.json\'s flag, the same test)',
}


def build() -> dict:
    nodes = copy.deepcopy(NODES)
    for lst in LISTS:
        at = next(i for i, n in enumerate(nodes) if n['id'] == _LIST_AFTER[lst['id']]) + 1
        pats = _pattern_nodes(lst)
        nodes[at:at] = pats + [_rest_node(lst, len(pats))]
    for n in nodes:
        if 'list' in n:
            for k, fn in SLOT_FLAGS.items():
                n[k] = fn(n['rows'])
    lists = []
    for lst in LISTS:
        drawn = sum(1 for n in nodes if n.get('list') == lst['id'])
        lists.append({**{k: v for k, v in lst.items() if k != 'rows'}, 'drawn': drawn})
    return {
        'schema': 'hdgamushiro-routes/1',
        'source': SOURCE,
        'cross_source': CROSS_SOURCE,
        'terms': TERMS,
        'legend': LEGEND,
        'quotes': QUOTES,
        'bag1': BAG1,
        'basic_form': [],
        'groups': GROUPS,
        'lists': lists,
        'slot_flags': SLOT_FLAG_MEANING,
        'known_discrepancies': KNOWN_DISCREPANCIES,
        'page_order': PAGE_ORDER,
        'nodes': nodes,
    }


# ── this page's own rules ──────────────────────────────────────────────────────────────────────
def _verbatims(obj, path=''):
    """Every `*_verbatim` string in a dict tree, with where it sits."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.endswith('_verbatim') and isinstance(v, str):
                yield f'{path}.{k}', v
            else:
                yield from _verbatims(v, f'{path}.{k}')
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _verbatims(v, f'{path}[{i}]')


def _cells(rows: list[str], letters: str) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(rows) for c, x in enumerate(row) if x in letters}


def _rests_on(rows: list[str], below: str, above: str) -> bool:
    """Some cell of piece `above` sits directly on a cell of piece `below`."""
    lo = _cells(rows, below)
    return any((r + 1, c) in lo for r, c in _cells(rows, above))


def _hd_checks(data: dict, ctx: dict) -> tuple[list[str], set[str]]:
    bad: list[str] = []
    found: set[str] = set()
    boards, by_id = ctx['boards'], ctx['by_id']
    nodes = data.get('nodes', [])
    quotes = {q['id']: q for q in data.get('quotes', [])}

    qtext = [q['verbatim'] for q in quotes.values()]
    for where, v in _verbatims({k: data.get(k) for k in ('bag1', 'groups', 'nodes', 'lists')}):
        if not any(v in q for q in qtext):
            bad.append(f'verbatim: {where} is not one of the quoted sentences')

    # bag 1: J before S, by support; the seven-piece board is the six-piece one plus four l cells
    b1 = data.get('bag1', {})
    rb = boards.get(b1.get('requires', {}).get('node'))
    for c in b1.get('requires', {}).get('all', []):
        a, b = c['before']
        if rb is None or a not in RT.PIECES or b not in RT.PIECES or not _rests_on(rb, a.lower(), b.lower()):
            bad.append(f'bag1-order: on bag1.left no {b} cell rests on a {a} cell')
    top, left = boards.get('bag1.l_top'), boards.get('bag1.left')
    h = 12
    if top is None or left is None or bottom([r.replace('l', EMPTY) for r in top], h) != bottom(left, h) or \
            len(_cells(bottom(top, h), 'l')) != 4:
        bad.append('bag1-top: bag1.l_top is not bag1.left plus four l cells')
    else:
        # the held L: on Forms A1, B, C and D its cells are exactly where bag1.l_top stands the L
        for f in ('2.a1', '2.b', '2.c', '2.d'):
            if f not in boards or _cells(bottom(boards[f], h), 'L') != _cells(bottom(top, h), 'l'):
                bad.append(f'held-l: {f}\'s L is not where bag1.l_top stands the L')
        a2 = boards.get('2.a2')
        if a2 and len(_cells(a2, 'L')) == 4 and _rests_on(a2, 'o', 'L') and _rests_on(a2, 'L', 'l'):
            found.add('2.a2:arrow_vs_board')

    # every form fires a TST from its U cells; a redraw is its form; forms are named in board order
    forms = [n for n in nodes if n.get('bag') == 2 and n.get('spin')]
    for n in forms:
        if after_spin(n['rows'])[1] != 3 or len(_cells(n['rows'], 'U')) != 4:
            bad.append(f'spin: {n["id"]} names a TST but its U cells clear {after_spin(n["rows"])[1]} rows')
    heads = [n.get('form_heading_verbatim') for n in forms]
    if heads != [quotes[k]['verbatim'] for k in ('form.a', 'form.a', 'form.b', 'form.c', 'form.d')] or \
            [n['board'] for n in forms] != sorted(n['board'] for n in forms):
        bad.append('forms: the five forms are not the page\'s five Form headings in board order')
    else:
        found.add('forms:no_names_on_boards')
    for n in nodes:
        if n.get('redraw_of') and bottom(n['rows'], 0) != bottom(boards.get(n['redraw_of'], []), 0):
            bad.append(f'redraw: {n["id"]} is not {n["redraw_of"]}')
    a1, a2 = boards.get('2.a1'), boards.get('2.a2')
    if not a1 or not a2 or RT.occ(bottom(a1, 0)) != RT.occ(bottom(a2, 0)):
        bad.append('group: Forms A1 and A2 no longer share one occupancy')
    if any(n.get('board') != k for k, n in zip(range(8, 41), [by_id[i] for i in data.get('page_order', []) if i in by_id])):
        bad.append('board: a node\'s board index is not its place in the page (boards 8-40)')

    # every list's total, re-derived: the PC body plus the TST its base board leaves; and its quote
    for lst in data.get('lists', []):
        pats = [n for n in nodes if n.get('list') == lst['id']]
        after = by_id.get(lst.get('base'), {})
        if not pats or after.get('after_of') not in boards:
            bad.append(f'lines: {lst["id"]} has no patterns or no after-the-TST base')
            continue
        total = len(bottom(pats[0]['rows'], 0)) + after_spin(boards[after['after_of']])[1]
        if total != lst.get('total_lines') or f'{lst["total_lines"]} total lines' not in \
                quotes.get(lst.get('total_lines_quote'), {}).get('verbatim', ''):
            bad.append(f'lines: {lst["id"]} clears {total} lines, the page says {lst.get("total_lines")}')
        if f'{lst["stated_pattern_count"]} minimal solutions' not in lst.get('rate_verbatim', ''):
            bad.append(f'lines: {lst["id"]} stated count is not the page\'s')
        if not any(n.get('t_in_tsd_slot') for n in pats):
            bad.append(f'category: {lst["id"]} has no TSD before its PC (a Triple Double opener)')
    return bad, found


SPEC = RT.TranscriptionSpec(
    out=OUT, build=build, alphabet=ALPHABET, non_board=NON_BOARD,
    harddrop=None,
    routes_file={'file': SHIWEHI, 'pairs': CROSS_PAIRS},
    board_kinds=frozenset({'illustration'}),
    pc_lines=8, prior_letters='',
    upper_groups={'L': 'separate'},
    slot_flags=SLOT_FLAGS, occupancy_class_parents=1, extra_checks=_hd_checks)


def verify(data: dict) -> list[str]:
    return RT.verify(data, SPEC)


def drift(data: dict) -> list[str]:
    return RT.drift(data, SPEC)


# ── selftest ───────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    """A gate nothing can fail is decorative. Plant one defect per rule, each in a named id."""

    def drop_pattern(d):
        d['nodes'] = [n for n in d['nodes'] if n['id'] != '2.b.pc#6']

    def break_mirror(d):
        setcell(node(d, 'bag1.l_top_right')['rows'], 1, 1, '-')

    def shift_left(d):
        n = node(d, 'bag1.left')
        n['rows'] = ['-' + r[:-1] for r in n['rows']]

    def a1_off(d):
        setcell(node(d, '2.a1')['rows'], 3, 0, 'o')                     # an i drawn o

    def pc_off(d):
        setcell(node(d, '2.a.pc#2')['rows'], 1, 2, 'j')                 # an i drawn j

    def bad_cell(d):
        setcell(node(d, '2.d')['rows'], 1, 0, 'p')

    def flag_flip(d):
        n = node(d, '2.c.pc#2')
        n['t_in_tsd_slot'] = not n['t_in_tsd_slot']

    def drop_discrepancy(d):
        d['known_discrepancies'] = [x for x in d['known_discrepancies'] if x['id'] != '2.b.pc:stated_vs_drawn']

    def c_cells(d):
        setcell(node(d, '2.c.pc#1')['rows'], 1, 1, 'c')

    def wrong_after(d):
        node(d, '2.b.after')['after_of'] = '2.c'

    def base_off(d):
        setcell(node(d, '2.b')['rows'], 7, 7, 'z')                      # a bag-1 c cell drawn z

    def no_reason(d):
        node(d, '2.d')['unmatchable'] = ''

    def wrong_spin(d):
        n = node(d, '2.b')
        setcell(n['rows'], 9, 2, 'c')                                   # the U's bottom cell drawn grey

    def total_lines(d):
        next(x for x in d['lists'] if x['id'] == '2.a.pc')['total_lines'] = 9

    def unquoted(d):
        node(d, '2.c')['form_heading_verbatim'] = '=== Form C (O → S) ==='

    def bag1_order(d):
        d['bag1']['requires']['all'][0]['before'] = ['S', 'J']

    def held_l(d):
        n = node(d, '2.b')
        setcell(n['rows'], 6, 8, 'l')
        setcell(n['rows'], 6, 9, 'L')                                    # the held L and the bag-2 l swap a cell

    def redraw(d):
        setcell(node(d, '2.c.redraw')['rows'], 1, 0, '-')

    def group_occ(d):
        setcell(node(d, '2.a2')['rows'], 3, 8, '-')

    def board_index(d):
        node(d, '2.c')['board'] = 14

    def form_order(d):
        a, b = node(d, '2.b'), node(d, '2.c')
        a['form_heading_verbatim'], b['form_heading_verbatim'] = b['form_heading_verbatim'], a['form_heading_verbatim']

    def stated(d):
        next(x for x in d['lists'] if x['id'] == '2.c.pc')['stated_pattern_count'] = 16

    def cross_pairs(d):
        d['cross_source']['pairs'] = d['cross_source']['pairs'][:-1]

    mutants = [
        (drop_pattern, 'a dropped PC pattern', 'list-count:'),
        (break_mirror, 'the mirrored 7-piece board no longer the mirror', 'mirror-of:'),
        (shift_left, 'bag1.left shifted one column', 'routes-file:'),
        (a1_off, 'Form A1 off shiwehi\'s 2.normal#1', 'routes-file:'),
        (pc_off, 'an L → O solution off shiwehi\'s', 'routes-file:'),
        (cross_pairs, 'the recorded pairs not the spec\'s', 'routes-file:'),
        (bad_cell, 'a cell outside the alphabet', 'grammar:'),
        (flag_flip, 'a t_in_tsd_slot flag flipped', 'grammar:'),
        (drop_discrepancy, 'a dropped known discrepancy', 'discrepancy:'),
        (c_cells, 'a c cell where the TST leaves none', 'c-cells:'),
        (wrong_after, 'an after board read off the wrong form', 'after-of:'),
        (base_off, 'a bag-2 form whose c cells are not bag 1', 'bag2-base:'),
        (no_reason, 'an unmatchable node with no reason', 'grammar:'),
        (wrong_spin, 'a form whose U no longer clears three rows', 'spin:'),
        (total_lines, 'the 8-line total misstated', 'lines:'),
        (stated, 'a stated solution count off the page', 'lines:'),
        (unquoted, 'a verbatim field that is not on the page', 'verbatim:'),
        (bag1_order, 'the bag-1 order reversed', 'bag1-order:'),
        (held_l, 'the held L off bag1.l_top\'s L', 'held-l:'),
        (redraw, 'a redraw that is not its form', 'redraw:'),
        (group_occ, 'Forms A1 and A2 no longer one occupancy', 'group:'),
        (board_index, 'a node\'s board index off the page', 'board:'),
        (form_order, 'two form headings swapped', 'forms:'),
    ]
    spec_mutants = [
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'routes_file': None}),
         'no cross-source at all', 'harddrop:'),
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'routes_file': {
            'file': SHIWEHI, 'pairs': CROSS_PAIRS[:-1] + [['2.a.pc#6', '2.normal.pc#7']]}}),
         'a solution paired with the wrong shiwehi pattern', 'routes-file:'),
    ]
    return RT.run_selftest(SPEC, mutants, {'board': ('{{pfrow|J|S| |Z|Z|T|T|I|O|O}}', '{{pfrow|J|S| |Z|Z| |T|I|O|O}}'),
                                           'text': ('19 minimal solutions', '18 minimal solutions'),
                                           'hand_edit': '2.d', 'quote': '2.forms'},
                           spec_mutants)


def main() -> int:
    return RT.main(SPEC, selftest, __doc__)


if __name__ == '__main__':
    raise SystemExit(main())

"""Transcribe shiwehi.com's BT砲(途中BT) page into `btcannon-technique.json`.

    python3 -m pipeline.openers.extract_btcannon_shapes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_btcannon_shapes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_btcannon_shapes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_btcannon_shapes --html-dir <dir> --write  # ...and rewrite

The fifth MID-GAME TECHNIQUE page (中盤テンプレ・ドネイト), after STSD, STMB Cave, インペリアルクロス and ダブルダガー:
「TSD→TSTを打つことができる中盤テンプレ」. A TSD slot with a stood TST slot running up its left end and down
under its nub column's neighbour; the T goes in laid FLAT, pointing down (←AA: 「屋根下に寄せてから右回転、右回転」),
and its two cleared rows drop the overhang above onto the TST slot, where the second T stands up into an
ordinary TST (←A). The page calls it 途中BT to tell it from 開幕BT砲, the opener of the same name; this is the
mid-game form, derived from 欄干 and from 72積み, and it is a TECHNIQUE page, not a route page: the shape is
matched on a partial stack at any lock, never as a whole board from an empty one.

DECISION: the spin is a TSD (a full T-spin, 2 lines) and the anchor is the T's four cells — the T laid flat, nub
down, as STMB Cave's and ダブルダガー's. So the window predicate expresses it and the matcher (`technique-facts.ts`)
is untouched. The follow-up is a TST (`followup.lines` 3), which the matcher already reads from the
transcription (`followupKind`), so nothing there changed either.

WHY THE WINDOW IS THE AGREEMENT BOX (`window_basis: agreement`), not STSD's bounding box. The page's TSD board
draws the whole stack right of the slots as filled rows above the T, so every one of those cells is a "roof
cell" and STSD's rule would make the window the whole board. So the window is the box on which every drawing
of the shape agrees: this page's six (the basic form and its five builds) and harddrop's BT_Cannon page's
seventeen (another site, other authors, `cross_source.harddrop`; seven of them under its own 「Mid-game BT
Cannon」 heading, among them the same 欄干 conversion this page draws). It comes out seven rows by four
columns: the wall column, the TST slot, the TSD's three columns, from the TST's overhang down to the TST
slot's bottom cell. Widening it meets a disagreement (the stack right of the TSD differs between drawings) or
leaves the basic form's board.

THREE SHARED-GATE CHANGES CAME WITH IT, all in unhashed Python and all opt-in (every other technique's gate,
selftest and `--html-dir` output was compared byte for byte before and after):

  * `spin_piece: U` reads as a T. The page draws the T it places in the renderer's `U` (a light purple cell
    with a dark dot), and the gate's spin rule looked the letter up as a piece.
  * an EMPTY `cross_source.fires` is accepted when `routes_fire_none` says why and the window is an agreement
    box with external drawings: no committed routes board draws a BT (measured), and rule (g) firing the
    window on each of harddrop's seventeen drawings is the independent check `fires` stands for elsewhere.
  * `TechniqueSpec.html_checks`: `--html-dir` re-checks the harddrop wikitext snapshot beside the page (MediaWiki's
    sha1 and our sha256, every recorded drawing letter for letter, and that the recorded drawings are EXACTLY the
    page's boards whose drawn T the window fires on). Because that makes the window choose its own external
    drawings, every OTHER drawn T on the page is recorded too (`drawn_t_not_fired`: its lie, its line count,
    why the window misses it, measured, and a note read off the page), so a drawing of the shape the window
    misses is a red build to name, never a board silently left out.

WHERE THE TRANSCRIPTION COMES FROM. `NODES` is a literal, hand-checked transcription of the page's RAW HTML,
fetched the way STSD's was: curl through the session proxy, TLS verification on, with a CA bundle adding the
Let's Encrypt YE2 intermediate shiwehi.com omits. Eleven boards, plain text in `<div class="ttt">`, one row per
line. The page is not committed; CI cannot fetch it. harddrop's page is read as the pinned revision's own
bytes from the MediaWiki API (urllib, a descriptive User-Agent, never curl), the way SDPC Spin's was.

THE CATALOGUES ARE NOT A CROSS-SOURCE, measured: `opener-fields.json` carries two BT Cannon and two Super Speed BT
Cannon fields, all four rows tall — bag 1 only, before the overhang — so the seven-row window cannot be placed on
them at all (`extra_checks` measures every placement off the board); `wiki-openers.json` draws no BT field.

WHAT IS AN INFERENCE, flagged in the JSON (`reading`, the legend) rather than in prose only:

  * `U` is the T the spin places (the renderer's "the T goes here" cell, drawn on the TSD and the TST boards);
    upper-case `C` the cleared rows, muted (checked by the spin rule).
  * the TST board is drawn after the TSD with its own T in; the board between them, which the page does not
    draw, is DERIVED (`basic.after`, the TST board less its U) and measured to be what the TSD leaves.
  * on the four 72積み builds the upper-case `I J S O Z` are the pieces the page places (the renderer's muted
    colours) and the lower-case pieces the 72積み stack beside the well, which the page varies with the
    stack's height: OUR READING. Each build stands on a DERIVED terrain (the board less its upper case).
  * harddrop's cell codes: `P` is the placed T (read `U`), blank empty, every other code its letter in lower
    case (`G` grey, `Q` the page's light grey), all filled.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import tempfile
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers import technique_transcription as TT
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS
from pipeline.openers.route_transcription import EMPTY, WIDTH, after_spin, bottom
from pipeline.openers.technique_transcription import node

HERE = Path(__file__).resolve().parent
OUT = HERE / 'btcannon-technique.json'

ALPHABET = frozenset('-cCUjlozsIJOSZ')


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/btcannon.php',
    'title': 'BT砲(途中BT)(Mid-game BT Cannon)',
    'author': 'しゑひ(shiwehi)',
    'created': '2021-07-03',
    'updated': '2021-07-03',
    'fetched': '2026-10-17',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle '
                    'that adds the Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), '
                    'the method STSD, STMB Cave, インペリアルクロス, ダブルダガー, 山岳積み2号 and stick spin used. The '
                    'snapshot is the page\'s raw HTML, byte for byte; every board is plain text in it, 11 '
                    'ten-wide boards in page order.',
    'snapshot_file': 'btcannon.html',
    'snapshot_sha256': '9776ac75c870e71aebe0d45bf1a24b20a7246317cd821416cbcf6586392708d0',
    'snapshot_bytes': 26960,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable '
                     'in CI: the page is not committed and cannot be fetched there. Re-check with '
                     '--html-dir after any refetch (with harddrop\'s BT_Cannon.wikitext beside it); an HTML '
                     'hash moves with ANY byte of the page (ads, sidebar, a date), so a moved hash means "read '
                     'the board diff", not "the boards changed". Sentences are compared against the page with '
                     'its tags dropped.',
    'renderer': {
        'url': 'https://shiwehi.com/tetris/mutual/column-exp.js?date=20210408',
        'read': '2026-10-19',
        'sha256': '95c431a4147f9c30fc0e1bae935e6af6f5669c3d2fa1edfc388848e69ab62570',
        'sha256_note': 'the same bytes STSD recorded, re-fetched for this page to read U and the upper-case pieces',
        'colorMap_used': {'c': '#a3a3a3', 'C': '#cccccc', 'U': '#c8a6ff with a #8400ff dot (gradientMap)',
                          'j l o z s': '#0011ff #ff7b00 #eeee00 #ff0000 #33ff00',
                          'I J O S Z': '#4db1d8 #4d57d8 #cfcf4d #69d24d #d84d4d', '-': '#000000'},
        'mirror_button': 'body.reversed swaps j<->l, s<->z (and upper case); the page draws only one hand',
    },
    'decorative_images': ['BT砲(途中BT)(Mid-game BT Cannon)タイトル画像', 'BT砲の消し方 (an animated gif, not transcribed)'],
    'references': ['./btcannonopener.php (開幕BT砲, linked twice; the second link points at dtcannonopener.php)',
                   './parapet.php (欄干)', './dtcannon.php (途中DT)', 'https://four.lol/methods/bt-cannon (the page\'s own reference)'],
    'unfetched': ['https://four.lol/methods/bt-cannon (the page\'s own reference; harddrop\'s BT_Cannon page is the '
                  'second source read instead)'],
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ',
    '-': 'empty',
    'c': 'a cell filled before this diagram (any piece, or garbage), grey',
    'j l o z s': 'a cell of that piece; on the 72積み builds, the 72積み stack beside the well (OUR READING)',
    'I J O S Z': 'on the 72積み builds, a cell of a piece the page places to build the shape, in the renderer\'s '
                 'muted colours (OUR READING; each is checked to be a whole piece)',
    'U': 'a cell of the T the spin places (the renderer\'s light purple with a dark dot)',
    'C': 'an earlier cell in a row the spin clears (muted; checked: every upper-case row of a spin board is a full row)',
    '%X': 'the X piece',
}

QUOTES = [
    {'id': 'intro', 'verbatim': 'ここでは、BT砲(BT Cannon)と呼ばれる、TSD→TSTを打つことができる中盤テンプレについて紹介していきます。'},
    {'id': 'name', 'verbatim': '開幕BT砲と区別するために途中BT砲(途中BT)とも呼ばれます。'},
    {'id': 'h.shape', 'verbatim': 'BT砲の形と消し方'},
    {'id': 'shape', 'verbatim': 'BT砲の形は以下の通りで、TSDを打った後にTSTを打つことができます。'},
    {'id': 'h.rotate', 'verbatim': '回転方法'},
    {'id': 'keys', 'verbatim': 'switchのキーで解説していきます。'},
    {'id': 'rotate1', 'verbatim': '屋根下に寄せてから右回転、右回転です。'},
    {'id': 'rotate2', 'verbatim': '初めに壁に寄せてから右回転です。'},
    {'id': 'tst', 'verbatim': '1つ目の%Tさえ入れることができれば、2つ目は普通のTSTです。'},
    {'id': 'h.build', 'verbatim': 'BT砲の作り方'},
    {'id': 'h.parapet', 'verbatim': '欄干からの派生'},
    {'id': 'parapet', 'verbatim': 'BT砲は開幕以外で組むことは中々難しいと思われがちですが、実は欄干を組む形からBT砲にすることができます。'},
    {'id': 'caution', 'verbatim': 'ただし、途中DTと同様に下穴を塞いでしまうので注意してください。'},
    {'id': 'h.parapet.make', 'verbatim': 'ここからこうすれば欄干'},
    {'id': 'h.bt.make', 'verbatim': 'こうすると途中BT'},
    {'id': 'h.72', 'verbatim': '72積みからの派生'},
    {'id': 's72', 'verbatim': 'また、72積みから2列側の高さに応じて以下のように組むことで途中BT砲を打つことができます。'},
    {'id': 'caution72', 'verbatim': 'ただし、途中DT同様に下穴を塞いでしまうので注意してください。'},
]

_TERRAIN = '---------- ---------- ---------- l--------- l---cccccc ll-ccccccc c-cccccccc c-cccccccc'

NODES = [
    {'id': 'basic', 'kind': 'base', 'caption_quote': 'shape',
     'label': 'the basic form: a TSD slot roofed over its right end, a TST slot up its left end and under it',
     'rows': _b('cc-------- c--------- c-cccccccc c--ccccccc c---cccccc cc-ccccccc c-cccccccc')},
    {'id': 'basic.spin', 'kind': 'spin', 'spin_of': 'basic', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'rotate1', 'label': 'the T laid flat, pointing down, under the roof: a TSD',
     'rows': _b('cc-------- c--------- c-cccccccc c--ccccccc CUUUCCCCCC CCUCCCCCCC c-cccccccc')},
    {'id': 'tst.spin', 'kind': 'spin', 'spin_of': 'basic.after', 'on': 'basic.after', 'adds': 'U', 'spin_piece': 'U',
     'spin': 'TST', 'lines': 3, 'caption_quote': 'tst',
     'label': 'what the TSD leaves, with the second T stood up into it: a TST (the page draws this board, not the one before it)',
     'rows': _b('---------- ---------- cc-------- c--------- CUCCCCCCCC CUUCCCCCCC CUCCCCCCCC')},
    {'id': 'parapet.terrain', 'kind': 'base', 'caption_quote': 'h.parapet.make',
     'label': 'the terrain: a two-high L against the wall, a hole under the TSD row',
     'rows': _b(_TERRAIN)},
    {'id': 'parapet', 'kind': 'build', 'on': 'parapet.terrain', 'adds': 'o', 'caption_quote': 'h.parapet.make',
     'label': 'an O on it: 欄干 (Parapet), a different technique', 'rows':
     _b('---------- ---------- ---oo----- l--oo----- l---cccccc ll-ccccccc c-cccccccc c-cccccccc')},
    {'id': 'bt.terrain', 'kind': 'base', 'same_occupancy_as': 'parapet.terrain', 'caption_quote': 'h.bt.make',
     'label': 'the same terrain again', 'rows': _b(_TERRAIN)},
    {'id': 'bt.build', 'kind': 'build', 'on': 'bt.terrain', 'adds': 'jz', 'caption_quote': 'parapet',
     'label': 'a J stood against the wall and a Z laid over the slot instead: 途中BT', 'rows':
     _b('jj-------- j--------- j-zz------ l--zz----- l---cccccc ll-ccccccc c-cccccccc c-cccccccc')},
    {'id': 's72.1', 'kind': 'build', 'on': 's72.1.terrain', 'adds': 'IJZ', 'caption_quote': 's72',
     'label': 'from 72積み, the two-wide side one row tall: an I, a J and a Z', 'rows':
     _b('---------- IJJ------- IJ-------- IJ-ZZ----- Il--ZZ---- cl---ccccc cll-cccccc cc-ccccccc')},
    {'id': 's72.2', 'kind': 'build', 'on': 's72.2.terrain', 'adds': 'SOZ', 'caption_quote': 's72',
     'label': 'from 72積み, the two-wide side holding a Z: an S, an O and a Z', 'rows':
     _b('---------- -SS------- SS-------- OO-ZZ----- OO--ZZ---- zz---ccccc czz-cccccc cc-ccccccc')},
    {'id': 's72.3', 'kind': 'build', 'on': 's72.3.terrain', 'adds': 'JZ', 'caption_quote': 's72',
     'label': 'from 72積み, the two-wide side holding a J and an S: a J and a Z', 'rows':
     _b('---------- -JJ------- -J-------- sJ-ZZ----- ss--ZZ---- js---ccccc jjj-cccccc cc-ccccccc')},
    {'id': 's72.4', 'kind': 'build', 'on': 's72.4.terrain', 'adds': 'IJZ', 'caption_quote': 's72',
     'label': 'from 72積み, the two-wide side holding an L and an O: an I, a J and a Z', 'rows':
     _b('I--------- IJJ------- IJ-------- IJ-ZZ----- oo--ZZ---- oo---ccccc lll-cccccc lc-ccccccc')},
    # ── derived: drawn nowhere on the page ──
    {'id': 'basic.after', 'kind': 'derived', 'derived': True,
     'reading': 'tst.spin less its U: what the TSD leaves (measured to be basic.spin after its clear, by occupancy); '
                'its rows the TST clears are drawn muted, as the page draws them on tst.spin',
     'rows': _b('---------- ---------- cc-------- c--------- C-CCCCCCCC C--CCCCCCC C-CCCCCCCC')},
    {'id': 's72.1.terrain', 'kind': 'derived', 'derived': True,
     'reading': 's72.1 less its I, J and Z: the 72積み stack with an L on the two-wide side',
     'rows': _b('---------- ---------- ---------- ---------- -l-------- cl---ccccc cll-cccccc cc-ccccccc')},
    {'id': 's72.2.terrain', 'kind': 'derived', 'derived': True,
     'reading': 's72.2 less its S, O and Z: the 72積み stack with a Z on the two-wide side',
     'rows': _b('---------- ---------- ---------- ---------- ---------- zz---ccccc czz-cccccc cc-ccccccc')},
    {'id': 's72.3.terrain', 'kind': 'derived', 'derived': True,
     'reading': 's72.3 less its J and Z: the 72積み stack with an S and a J on the two-wide side',
     'rows': _b('---------- ---------- ---------- s--------- ss-------- js---ccccc jjj-cccccc cc-ccccccc')},
    {'id': 's72.4.terrain', 'kind': 'derived', 'derived': True,
     'reading': 's72.4 less its I, J and Z: the 72積み stack with an O and an L on the two-wide side',
     'rows': _b('---------- ---------- ---------- ---------- oo-------- oo---ccccc lll-cccccc lc-ccccccc')},
]

#: the variant's window, in basic.spin's frame
VARIANTS = [{
    'id': 'btcannon', 'board': 'basic.spin', 'spin': 'TSD', 'lines': 2,
    'window_basis': 'agreement',
    'window': {'rows': [0, 6], 'cols': [0, 3]},
    't_cells': [[4, 1], [4, 2], [4, 3], [5, 2]],
    'roof_cells': [[0, 0], [0, 1], [1, 0], [2, 0], [2, 2], [2, 3], [3, 0], [3, 3]],
    'window_note': 'in basic.spin\'s frame, row 0 the top: the AGREEMENT BOX of this page\'s six drawings of the shape '
                   'and harddrop\'s seventeen. Column 0 is the wall; rows 4-5 are the rows the TSD clears (entailed by '
                   'the clear at a full TSD, NaiveClauseForced); above them the roof over the T\'s right end (row 3), '
                   'the TST slot running up column 1 with the cell beside it filled (row 2), the cell over it empty '
                   '(row 1) and the TST\'s overhang (row 0); under them the TST slot\'s bottom cell, walled both sides '
                   '(row 6). Everything right of column 3 is outside: the drawings disagree there. Occupancy only, '
                   'never colour; garbage is filled.',
    'agreement': [
        {'board': 'basic', 't_cells': [[4, 1], [4, 2], [4, 3], [5, 2]], 'mirrored': False},
        {'board': 'bt.build', 't_cells': [[4, 1], [4, 2], [4, 3], [5, 2]], 'mirrored': False},
        {'board': 's72.1', 't_cells': [[5, 2], [5, 3], [5, 4], [6, 3]], 'mirrored': False},
        {'board': 's72.2', 't_cells': [[5, 2], [5, 3], [5, 4], [6, 3]], 'mirrored': False},
        {'board': 's72.3', 't_cells': [[5, 2], [5, 3], [5, 4], [6, 3]], 'mirrored': False},
        {'board': 's72.4', 't_cells': [[5, 2], [5, 3], [5, 4], [6, 3]], 'mirrored': False},
    ],
    'followup': {'board': 'basic.after', 'spin': 'TST', 'lines': 3,
                 't_cells_pre_clear': [[2, 1], [3, 1], [3, 2], [6, 1]],
                 't_cells_after': [[4, 1], [5, 1], [5, 2], [6, 1]],
                 'note': 'the T stood up into the TST slot, nub right (the page: 「初めに壁に寄せてから右回転」). Before the '
                         'TSD its cells are split by the two cleared rows (three above them, one under them); the TSD '
                         'joins them, and the matcher carries the slot through every later clear to the next T.'},
    'fires_on': ['basic', 'bt.build', 's72.1', 's72.2', 's72.3', 's72.4'],
    'misses': ['parapet.terrain', 'parapet', 'bt.terrain', 'tst.spin', 'basic.after'],
}]


def _hd(table: int, board: int, section: str, mirrored: bool, rows: str) -> dict:
    return {'table': table, 'board': board, 'section': section, 'mirrored': mirrored, 'rows': _b(rows)}


#: the note every stood T into a T-spin Triple carries in `drawn_t_not_fired`
STOOD_TST = ('a stood T into a T-spin Triple (the BT\'s own TST, or a C-Spin\'s): the window anchors on the TSD\'s flat T '
             'pointing down, so it cannot fire here by construction')


def _miss(table: int, board: int, section: str, t: str, lines: int, window: str, note: str, rows: str) -> dict:
    return {'table': table, 'board': board, 'section': section, 't': t, 'lines': lines, 'window': window,
            'note': note, 'rows': _b(rows)}


#: what the four T-spin Doubles revision 44634 adds after its OBT Cannon's TST belong to
OBT = "the OBT Cannon's LST continuation (revision 44634)"

#: harddrop's BT_Cannon page: every board on it whose drawn T (`P`) the window fires on, read with `hd_cell`
HARDDROP = {
    'page': 'https://harddrop.com/wiki/BT_Cannon',
    'title': 'BT Cannon',
    'oldid': 44634,
    'revision_sha1': '10021bb04ca0f4d1e2def255173fd27570616eaf',
    'revision_timestamp': '2026-10-21T15:45:11Z',
    'fetched': '2026-10-24',
    'fetch_method': 'the pinned revision\'s own bytes from the MediaWiki API (api.php?action=query&prop=revisions&'
                    'revids=44634&rvprop=ids|sha1|size|timestamp|content&rvslots=main), with Python\'s urllib and a '
                    'descriptive User-Agent (NOT curl); the API\'s sha1 equals the sha1 of the bytes, and 44634 was the '
                    'page\'s latest revision when fetched. It re-pins 41529 (2024-12-27, fetched 2026-10-19), '
                    'which 44634 only extends: its first 1850 lines are 41529\'s byte for byte, and it adds the OBT '
                    'Cannon (LST extension) and Mechanical Heart Variation sections, tables 41-47 (two of them boards '
                    'outside any table, read as one-board tables by `_tabled`), so every earlier (table, board) is '
                    'unchanged',
    'snapshot_file': 'BT_Cannon.wikitext',
    'snapshot_sha256': 'c8337b03e05e841c6b2ffe261140c621580eb50dd4e03a218a56ae4a032fa8dd',
    'snapshot_bytes': 50846,
    'snapshot_note': 'not committed: check_wikitext_sources refetches the pinned revision weekly through api.php and '
                     're-checks it with --wikitext-dir; a person re-checks it with --html-dir, the file beside '
                     'btcannon.html',
    'author_note': 'BT Cannon was invented by TCM-β (the page\'s first sentence); the page is harddrop\'s, edited by '
                   'its wiki editors — another site and other authors than shiwehi.com',
    'reading': {'blank': '-', 'P': 'U, the T placed into the spin (the slot the agreement rule fires the window at)',
                'other': 'any other code, its last letter in lower case (G grey, Q light grey, a two-letter Lx the '
                         'muted x), every one FILLED; a bare - code is read as empty'},
    'drawings': [
        _hd(0, 3, 'Basic Opening', True, '---------- ----ll---- -----l---- iiii-lgggg lll--sgggg ltUUUssgoo tttUzzsjoo iiii-zzjjj'),
        _hd(1, 3, 'Basic Opening', True, '---------- ----ll---- -----l---- iiii-lz--- lll--zzj-- ltUUUzsjjj tttUzzssoo iiii-zzsoo'),
        _hd(2, 3, 'Special β ●-hiro', True, '---------- ----ll---- -----loo-i jjss-looli jss--jllli jzUUUjoosi zztUjjooss zttt-iiiis'),
        _hd(5, 2, 'BT Cannon C-Spin', True, '---------- ---z---lli oozz----li oozjjss-li jjjjss--si oojjtUUUss ooltttUzzs llliiii-zz'),
        _hd(7, 2, 'BT Cannon C-Spin', False, '---------- lll---s--- lz----ssoo zz-iiiisoo zz--jjjooi zzUUUjjooi zssUtjjjli ss-tttllli'),
        _hd(10, 0, 'BT Cannon C-Spin In-Depth', True, '---------- ---z---jjj oozz----sj ooziiii-ss ggglll--gs ggglgUUUgg ggggggUggg ggggggg-gg'),
        _hd(10, 1, 'BT Cannon C-Spin In-Depth', True, '---------- ---z---lli oozz----li oozjjss-li gggjss--gi gggjgUUUgg ggggggUggg ggggggg-gg'),
        _hd(24, 4, 'TSM to BT', False, '---------- ------s--z jjj---sszz ggj--ooszl gg---oolll gg-iiiiggg gg--gggggg ggUUUggggg gggUgggggg gg-ggggggg'),
        _hd(27, 0, 'Mid-game BT Cannon', False, '---------- ---------- -jj------- -j-------- ij-zzqqqqq il--zzqqqq ilUUUggggg illUgggggg gg-ggggggg'),
        _hd(27, 1, 'Mid-game BT Cannon', False, '---------- zz-------- szz------- ss-------- ss-iiiiqqq ss--gggggg jsUUUggggg jjjUgggggg gg-ggggggg'),
        _hd(27, 2, 'Mid-game BT Cannon', False, '---------- ---------- ijj--ll--- ij---llqqq ij-llllqqq iz--iiiiqq zzUUUggggg zssUgggggg ss-ggggggg'),
        _hd(28, 1, 'Mid-game BT Cannon', False, '---------- -jj------- -j-------- ij-zzqqqqq il--zzqqqq ilUUUggggg illUgggggg gg-ggggggg'),
        _hd(29, 1, 'Mid-game BT Cannon', False, '---------- jj-------- j--------- j-iiiiqqqq l--zzqqqqq lUUUzzgggg llUggggggg g-gggggggg'),
        _hd(32, 0, 'Mid-game BT Cannon', True, '---------- ------ll-- -------l-- qqqqss-lqq qqqss--jqq iiiiUUUjjj gggggUgggg gggggg-ggg'),
        _hd(34, 0, 'Mid-game BT Cannon', True, '---------- ---------j ---------j --------jj ---------i ---z--ss-i oozztss--i ooztttUUUi gggggggUgg gggggggg-g ggggggg-gg'),
        # revision 44634's OBT Cannon (BT Cannon LST Extension), drawn twice: the same TSD board as table 5 board 2
        _hd(41, 2, 'BT Cannon LST Extension (OBT Cannon)', True, '---------- ---z---lli oozz----li oozjjss-li jjjjss--si oojjtUUUss ooltttUzzs llliiii-zz'),
        _hd(43, 2, 'Z and O Before T', True, '---------- ---z---lli oozz----li oozjjss-li jjjjss--si oojjtUUUss ooltttUzzs llliiii-zz'),
    ],
    #: every OTHER board with a drawn T (`P`, four cells) on the page: the window does not fire at it in either hand,
    #: each named with what the T is, measured (`t` the T's lie, `lines` the rows it clears, `window` why it does not
    #: fire: the T is not the window's flat T pointing down, the window leaves the board, or a window cell disagrees)
    #: and a note read off the page around it. With `drawings` this is EVERY drawn T on the page, so the agreement
    #: drawings are not chosen by the window: a drawn T the window misses is a red build until it is named here
    'drawn_t_not_fired': [
        _miss(3, 2, 'Special β ●-hiro', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ----ll---- -----loo-i jjssUlooli jssUUjllli ztttUiiiis'),
        _miss(5, 3, 'BT Cannon C-Spin', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---------- ---------- ---z---lli oozz----li oozjjssUli jjjjssUUsi llliiiiUzz'),
        _miss(6, 1, 'BT Cannon C-Spin', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- lll------- lz-------- zz-------i zssoojj--i sssooj---i jjssijUzzi joosilUUzz joozilUlli oozzill-li'),
        _miss(6, 2, 'BT Cannon C-Spin', 'flat-down', 2, 'leaves the board', "the C-Spin's T-spin Double, after its TST, in the floor rows with no TST slot under it",
              '---------- ---------- ---------- ---------- lll------- lz-------- zz-------i zssoojj--i sssoojUUUi oozzillUli'),
        _miss(7, 3, 'BT Cannon C-Spin', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---------- ---------- lll---s--- lz----ssoo zzUiiiisoo zzUUjjjooi ssUtttllli'),
        _miss(8, 1, 'BT Cannon C-Spin', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- --------oo --------oo i------ssz i--lljsszz i---ljjjzi issUlzooji ssUUzzooji lllUzlsjji lz-lllssoo'),
        _miss(8, 2, 'BT Cannon C-Spin', 'flat-down', 2, 'leaves the board', "the C-Spin's T-spin Double, after its TST, in the floor rows with no TST slot under it",
              '---------- ---------- ---------- ---------- --------oo --------oo i------ssz i--lljsszz iUUUljjjzi lzUlllssoo'),
        _miss(11, 0, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- s--------- ssooi--zz- jsooil--zz jjjgil-ggg ggggill-gg gggggggUgg ggggggUUgg gggggggUgg'),
        _miss(11, 1, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- i--------- iloos--zz- ilooss--zz illgjs-ggg ggggjjj-gg gggggggUgg ggggggUUgg gggggggUgg'),
        _miss(11, 2, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- --s------- jjssi--zz- joosil--zz joogil-ggg ggggill-gg gggggggUgg ggggggUUgg gggggggUgg'),
        _miss(12, 0, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- oo-------- oo-------- szz------i sszzljj--i gslllj---i gggggjUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(12, 1, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---------- --zz------ sllzz----i ssloojj--i gslooj---i gggggjUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(12, 2, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---oo----- ---oo----- --sll----i zzssljj--i gzzslj---i gggggjUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(12, 3, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---------- zz-------- szzll----i ssooljj--i gsoolj---i gggggjUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(12, 4, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---------- oo-------- oosll----i zzssljj--i gzzslj---i gggggjUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(13, 0, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- --zz------ lllzz----i lssoojj--i ssgooj---i gggggjUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(13, 1, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- --ls------ lllss----i oozzsjj--i oogzzj---i gggggjUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(13, 2, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- -z--l----- zzlll----i zssoojj--i ssgooj---i gggggjUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(14, 0, 'BT Cannon C-Spin In-Depth', 'flat-down', 2, 'leaves the board', "a T-spin Double among the fifth bag's options (Trinity / STSD / 4-wide), in the floor rows with no TST slot under it",
              '---------- ---------- --------ll ---------l gg----ss-l gggggss--g ggggggg--g ggggggUUUg gggggggUgg'),
        _miss(14, 1, 'BT Cannon C-Spin In-Depth', 'flat-down', 2, 'leaves the board', "a T-spin Double among the fifth bag's options (Trinity / STSD / 4-wide), in the floor rows with no TST slot under it",
              '---------- --ssz----- jsszzi---- jjjzli---- ggllli---- gggggi---g ggggggg--g ggggggUUUg gggggggUgg'),
        _miss(22, 0, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- --z------- -zz------- -zsll----i oossljj--i oogslj---i gggggjUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(22, 1, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---------- ----zz---- --sllzz--i oossljj--i oogslj---i gggggjUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(22, 2, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---------- ---ss----- --sslll--i oozzljj--i oogzzj---i gggggjUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(22, 3, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ----jj---- ----js---- ----jss--i oozzlls--i oogzzl---i ggggglUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(22, 4, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---------- j----s---- jjj--ss--i oozzlls--i oogzzl---i ggggglUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(22, 5, 'BT Cannon C-Spin In-Depth', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---------- --j--s---- --jjjss--i oozzlls--i oogzzl---i ggggglUggi ggggggUUgg ggggggUggg ggggggg-gg'),
        _miss(24, 0, 'TSM to BT', 'stood', 1, "not the window's T", "the T-spin Mini the 'TSM to BT' section makes the offset hole with, stood against the wall",
              '---------- ---------- ---------- ---------- ---------- l--------- l--------U lls-j---UU oossjjjzzU oo-siiiizz'),
        _miss(25, 0, 'TSM to BT', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---------- ------s--z jjj---sszz ggj--ooszl gg---oolll ggUiiiiggg ggUUgggggg ggUggggggg'),
        _miss(25, 2, 'TSM to BT', 'flat-up', 1, "not the window's T", "a flat T pointing UP into one row, in the 'TSM to BT' example's later bags",
              '---------- -------jjj i------zsj il----zzss il----zoos ill---goog ggg---gggg gggU-ggggg ggUUUggggg'),
        _miss(28, 0, 'Mid-game BT Cannon', 'flat-down', 2, 'disagrees', 'the Kaidan the page fires on the same base, for comparison with board 1 beside it (recorded as a drawing): no TST slot beside the T',
              '---------- ---------- ---------- -----zz--- ggsUUUzzgg ggssUggggg gg-sgggggg gg-ggggggg'),
        _miss(31, 0, 'Mid-game BT Cannon', 'flat-down', 2, 'disagrees', "the Cut Copy the page recommends before offering the BT: the TST slot's column beside the T is filled",
              '---------- ----z----- ioozz--s-- ioozl--ss- ijlll---sl ijjjUUUlll gggggUgggg gggggg-ggg'),
        _miss(34, 1, 'Mid-game BT Cannon', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---------- ---------- ---------g ---------g --------gg --lzz----g lllgzzggUg gggggggUUg ggggggggUg ggggggg-gg'),
        _miss(41, 3, 'BT Cannon LST Extension (OBT Cannon)', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---------- ---------- ---z---lli oozz----li oozjjssUli jjjjssUUsi llliiiiUzz'),
        _miss(42, 0, 'BT Cannon LST Extension (OBT Cannon)', 'flat-down', 2, 'leaves the board',
              f"the T-spin Double of {OBT}'s third bag, in the floor rows with no TST slot under it",
              '---------- ---------- ---------- -------sll ---zi--ssl oozziUUUsl oozgijUggg'),
        _miss(42, 2, 'BT Cannon LST Extension (OBT Cannon)', 'flat-down', 2, 'leaves the board',
              f"the T-spin Double of {OBT}'s fourth bag, in the floor rows with no TST slot under it",
              '---------- ---------i --------ji ---szz--ji l--sszzjji lUUUsooggg llUggooggg'),
        _miss(42, 3, 'BT Cannon LST Extension (OBT Cannon)', 'flat-down', 2, 'disagrees',
              f"the T-spin Double of {OBT}'s fifth bag: no TST slot beside the T (the wall column is filled)",
              '---------i ---------i -------ooi -------ooi ---zzlljjg sUUUzzljgg ssUgggljgg gs-ggggggg'),
        _miss(42, 4, 'BT Cannon LST Extension (OBT Cannon)', 'flat-down', 2, 'disagrees',
              f"the T-spin Double of {OBT}'s sixth bag: no TST slot beside the T (the wall column is filled)",
              '---------- ------i--g ---jjji--g l--zzjiggg lUUUzziggg llUggggggg gg-ggggggg'),
        _miss(43, 3, 'Z and O Before T', 'stood', 3, "not the window's T", STOOD_TST,
              '---------- ---------- ---------- ---z---lli oozz----li oozjjssUli jjjjssUUsi llliiiiUzz'),
    ],
    #: boards with no T drawn on which the window fires at a resting placement (the same shape one step before
    #: the page draws its T, or harddrop's STSD continuation's terrain): measured and recorded letter for letter,
    #: not agreement drawings (the agreement rule anchors on a drawn slot); `mirrored` is None, the hand unread
    'fires_without_slot': [
        _hd(0, 1, 'Basic Opening', None, '---------- ----ll---- -----l---- iiii-l---- lll--s---- lt---ss-oo ttt-zzsjoo iiii-zzjjj'),
        _hd(0, 2, 'Basic Opening', None, '---------- ----ll---- -----l---- iiii-lgggg lll--sgggg lt---ssgoo ttt-zzsjoo iiii-zzjjj'),
        _hd(1, 2, 'Basic Opening', None, '---------- ----ll---- -----l---- iiii-lz--- lll--zzj-- lt---zsjjj ttt-zzssoo iiii-zzsoo'),
        _hd(2, 0, 'Special β ●-hiro', None, '---------- ----ll---- -----loo-i jjss-looli jss--jllli jz---joosi zzt-jjooss zttt-iiiis'),
        _hd(5, 1, 'BT Cannon C-Spin', None, '---------- ---z---lli oozz----li oozjjss-li jjjjss--si oojjt---ss oolttt-zzs llliiii-zz'),
        _hd(7, 1, 'BT Cannon C-Spin', None, '---------- lll---s--- lz----ssoo zz-iiiisoo zz--jjjooi zz---jjooi zss-tjjjli ss-tttllli'),
        _hd(35, 0, 'BT Cannon STSD', None, '---------- ----gggggg -----ggggg gggg-ggggg ggg--ggggg gg---ggggg ggg-gggggg gggk-ggggg'),
        _hd(41, 1, 'BT Cannon LST Extension (OBT Cannon)', None, '---------- ---z---lli oozz----li oozjjss-li jjjjss--si oojjt---ss oolttt-zzs llliiii-zz'),
        _hd(43, 1, 'Z and O Before T', None, '---------- ---z---lli oozz----li oozjjss-li jjjjss--si oojjt---ss oolttt-zzs llliiii-zz'),
    ],
}

CATALOGUE = {
    'file': 'opener-fields.json',
    'names': ['BT Cannon {JP: BT砲 or 開幕BT砲}', 'Super Speed BT Cannon {JP: 超BT}'],
    'reason': 'four-row bag-1 fields, drawn before the overhang the TSD needs: the seven-row window cannot be placed on '
              'them (every placement leaves the board), so they are no cross-source. wiki-openers.json draws no BT field.',
}

CROSS_SOURCE = {
    'kind': 'routes',
    'label_pattern': 'btcannon',
    'note': 'the window, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot board of every '
            'committed *-routes.json, with the U cells as the T: it fires on none (no route page draws a BT). The '
            'independent drawer is harddrop\'s BT_Cannon page instead (`harddrop`), whose seventeen boards with a drawn '
            'T the window fires on are the window\'s external `agreement` drawings: rule (g) fires the window on each, '
            'once, at its drawn T, in its recorded hand.',
    'routes_fire_none': 'no committed routes file draws a BT Cannon (measured: the window fires on none of their U-slot '
                        'boards); the cross-check is harddrop\'s own BT_Cannon page, read below',
    'harddrop': HARDDROP,
    'catalogue': CATALOGUE,
    'fires': [],
    'also': [],
    'labelled_not_fired': [],
}

KNOWN_DISCREPANCIES: list[dict] = []

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'btcannon',
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
def hd_cell(code: str) -> str:
    """One harddrop cell code in this file's reading of it (HARDDROP['reading'])."""
    c = code.strip()
    if c == '' or c == '-':
        return EMPTY
    return 'U' if c == 'P' else c[-1].lower()


def _slot(rows: list[str]) -> list[list[int]]:
    return sorted([r, c] for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == 'U')


def t_lie(data: dict, rows: list[str]) -> tuple[str, int, str]:
    """What a drawn T (`U`) on a harddrop board is, measured: its lie (`stood`, `flat-down` — the window's T —
    or `flat-up`), the rows it clears, and why the window does not fire at it: the T is not the window's,
    the window leaves the board in both hands, or a window cell disagrees (`fires` if it fires after all)."""
    slot = _slot(rows)
    rs = sorted({r for r, _ in slot})
    lie = 'stood' if len(rs) == 3 else ('flat-down' if sum(1 for r, _ in slot if r == rs[0]) == 3 else 'flat-up')
    lines = sum(1 for r in rs if EMPTY not in rows[r])
    v = data['variants'][0]
    pre = [row.replace('U', EMPTY) for row in rows]
    lock = {tuple(x) for x in slot}
    if any(TT.window_fires(data, v, SPEC, pre, lock, m) for m in (False, True)):
        return lie, lines, 'fires'
    if lie != 'flat-down':
        return lie, lines, "not the window's T"
    off = []
    for m in (False, True):
        W = TT.window_cells(data, v, SPEC, m)
        D = {k for k, x in W.items() if x == 'T'}
        dr = min(r for r, _ in lock) - min(r for r, _ in D)
        dc = min(c for _, c in lock) - min(c for _, c in D)
        off.append(any(not (0 <= r + dr < len(rows) and 0 <= c + dc < WIDTH) for r, c in W))
    return lie, lines, 'leaves the board' if all(off) else 'disagrees'


def harddrop_drawings(data: dict | None = None) -> list[dict]:
    """harddrop's drawings as agreement drawings: the slot is the drawn T (`U`), read as empty."""
    data = data or build()
    out = []
    for d in data['cross_source']['harddrop']['drawings']:
        out.append({'name': f'harddrop BT_Cannon table {d["table"]} board {d["board"]} ({d["section"]})',
                    'rows': [row.replace('U', EMPTY) for row in d['rows']],
                    't_cells': _slot(d['rows']), 'mirrored': d['mirrored']})
    return out


def _tabled(text: str) -> str:
    """The wikitext with every board that stands outside any `{| |}` table wrapped in a table of its own, so the
    shared reader (which refuses a loose board) reads it as a one-board table in page order. harddrop's revision
    44634 draws two such boards (the OBT Cannon section's Alternative Build and its Mechanical Heart Variation);
    every board before them sits in a table, so the (table, board) of every earlier drawing is unchanged."""
    out, depth, last, start = [], 0, 0, None
    for m in RT.WIKI_TOKEN.finditer(text):
        tok = m.group(0)
        if tok == '{|':
            depth += 1
        elif tok == '|}':
            depth -= 1
        elif depth == 0 and tok in ('{{pfstart}}', '{{sstart}}'):
            start = m.start()
        elif depth == 0 and tok == '{{pfend}}' and start is not None:
            out.append(text[last:start] + '{|\n|' + text[start:m.end()] + '\n|}')
            last, start = m.end(), None
    return ''.join(out) + text[last:]


def _sections(text: str) -> list[str | None]:
    """The heading each `{|` table of a wikitext sits under, in table order."""
    heads = [(m.start(), m.group(2).strip()) for m in re.finditer(r'^(=+)\s*(.*?)\s*\1\s*$', text, re.M)]
    out = []
    for m in re.finditer(r'\{\|', text):
        h = [x for x in heads if x[0] < m.start()]
        out.append(h[-1][1] if h else None)
    return out


def harddrop_page_problems(data: dict, text: str) -> list[str]:
    """The recorded drawings against a harddrop wikitext: each letter for letter at its (table, board) under its
    heading, and the record COMPLETE both ways — the drawings are exactly the boards whose drawn T the window
    fires on (either hand), `drawn_t_not_fired` exactly every other board with a drawn T, and `fires_without_slot`
    exactly the boards with no T drawn on which it fires. So every drawn T on the page is in one list or the other,
    and a drawn T the window misses is named rather than silently left out."""
    hd = data['cross_source']['harddrop']
    text = _tabled(text)
    try:
        tables = RT.wikitext_tables(text)
    except ValueError as e:
        return [f'harddrop: the wikitext does not parse: {e}']
    secs = _sections(text)
    if len(secs) != len(tables):
        return [f'harddrop: {len(tables)} tables but {len(secs)} table openings']
    bad = []
    boards = {(i, j): [''.join(hd_cell(c) for c in row) for row in b]
              for i, t in enumerate(tables) for j, b in enumerate(t)}
    for d in hd['drawings'] + hd['drawn_t_not_fired'] + hd['fires_without_slot']:
        k = (d['table'], d['board'])
        if boards.get(k) != d['rows']:
            bad.append(f'harddrop: table {k[0]} board {k[1]} is not the recorded drawing (page {boards.get(k)})')
        elif secs[k[0]] != d['section']:
            bad.append(f'harddrop: table {k[0]} sits under {secs[k[0]]!r}, not {d["section"]!r}')
    v = data['variants'][0]
    slotted, unslotted, missed = [], [], []
    for (i, j), rows in sorted(boards.items()):
        slot = {tuple(x) for x in _slot(rows)}
        pre = [row.replace('U', EMPTY) for row in rows]
        if len(slot) == 4:
            hands = [m for m in (False, True) if TT.window_fires(data, v, SPEC, pre, slot, m)]
            if hands:
                slotted.append((i, j, hands))
            else:
                missed.append((i, j))
        elif not slot and any(TT.window_fires(data, v, SPEC, pre, cs, m)
                              for cs in TT.t_placements(pre, SPEC) for m in (False, True)):
            unslotted.append((i, j))
    want = [(d['table'], d['board'], [d['mirrored']]) for d in hd['drawings']]
    if sorted(slotted) != sorted(want):
        bad.append(f'harddrop: the window fires at the drawn T of {slotted}, the record holds {want}')
    named = sorted((e['table'], e['board']) for e in hd['drawn_t_not_fired'])
    if sorted(missed) != named:
        bad.append(f'harddrop: the window misses the drawn T of {sorted(missed)}, drawn_t_not_fired names {named}')
    if sorted(unslotted) != sorted((e['table'], e['board']) for e in hd['fires_without_slot']):
        bad.append(f'harddrop: with no T drawn the window fires on {unslotted}, the record names '
                   f'{[(e["table"], e["board"]) for e in hd["fires_without_slot"]]}')
    return bad


def harddrop_snapshot_checks(data: dict, html_dir: Path) -> list[str]:
    """`--html-dir`: the pinned harddrop revision beside the page snapshot (a missing file is a failure)."""
    hd = data['cross_source']['harddrop']
    p = Path(html_dir) / hd['snapshot_file']
    if not p.exists():
        return [f'harddrop: {hd["snapshot_file"]} is not in {html_dir} — fetch it beside the page']
    raw = p.read_bytes()
    bad = []
    if hashlib.sha256(raw).hexdigest() != hd['snapshot_sha256'] or len(raw) != hd['snapshot_bytes']:
        bad.append(f'harddrop: hash: sha256/bytes {hashlib.sha256(raw).hexdigest()} / {len(raw)} are not the recorded ones')
    if hashlib.sha1(raw).hexdigest() != hd['revision_sha1']:
        bad.append(f'harddrop: hash: sha1 {hashlib.sha1(raw).hexdigest()} is not MediaWiki\'s revision sha1')
    return bad + harddrop_page_problems(data, raw.decode('utf8'))


# ── technique-only rules ─────────────────────────────────────────────────────────────────────────
def extra_checks(data: dict):
    bad, measured = [], set()
    by = {n['id']: n for n in data['nodes']}
    xs = data['cross_source']
    hd = xs.get('harddrop', {})
    # harddrop: every recorded drawing is ten wide with one drawn T, and they hold the page's mid-game section
    for d in hd.get('drawings', []):
        slot = _slot(d['rows'])
        ys = {(c, len(d['rows']) - 1 - r) for r, c in slot}
        if any(len(r) != WIDTH for r in d['rows']) or len(slot) != 4 or RT._norm(ys) not in RT._shapes('t'):
            bad.append(f'harddrop: table {d["table"]} board {d["board"]} is not a ten-wide board with one drawn T')
    if not any(d['section'] == 'Mid-game BT Cannon' for d in hd.get('drawings', [])):
        bad.append('harddrop: no recorded drawing from harddrop\'s own Mid-game BT Cannon section')
    if len({(d['table'], d['board']) for d in hd.get('drawings', [])}) != len(hd.get('drawings', [])):
        bad.append('harddrop: a drawing recorded twice')
    v = data['variants'][0]
    # the agreement rule reads the drawings through the spec (the pristine build); these are the data's, so a
    # drawing edited in the data is checked the same way here: the window fires at its drawn T, in its recorded
    # hand, and at no other resting placement of either hand
    for d in hd.get('drawings', []):
        pre = [row.replace('U', EMPTY) for row in d['rows']]
        hits = [(frozenset(cs), m) for cs in TT.t_placements(pre, SPEC) for m in (False, True)
                if TT.window_fires(data, v, SPEC, pre, cs, m)]
        if hits != [(frozenset(tuple(x) for x in _slot(d['rows'])), d['mirrored'])]:
            bad.append(f'harddrop: the window fires {len(hits)} time(s) on table {d["table"]} board {d["board"]}, '
                       f'not once at its drawn T ({"mirrored" if d["mirrored"] else "as drawn"})')
    seen = {(d['table'], d['board']) for d in hd.get('drawings', [])}
    for d in hd.get('drawn_t_not_fired', []):
        k = (d['table'], d['board'])
        slot = _slot(d['rows'])
        ys = {(c, len(d['rows']) - 1 - r) for r, c in slot}
        if any(len(r) != WIDTH for r in d['rows']) or len(slot) != 4 or RT._norm(ys) not in RT._shapes('t'):
            bad.append(f'harddrop: table {k[0]} board {k[1]} (drawn_t_not_fired) is not a ten-wide board with one drawn T')
            continue
        got = t_lie(data, d['rows'])
        if got != (d['t'], d['lines'], d['window']) or got[2] == 'fires':
            bad.append(f'harddrop: table {k[0]} board {k[1]} is {got}, drawn_t_not_fired records '
                       f'{(d["t"], d["lines"], d["window"])}')
        if not d.get('note', '').strip():
            bad.append(f'harddrop: table {k[0]} board {k[1]} is in drawn_t_not_fired with no note')
        if k in seen:
            bad.append(f'harddrop: table {k[0]} board {k[1]} recorded twice')
        seen.add(k)
    for d in hd.get('fires_without_slot', []):
        if _slot(d['rows']) or not any(TT.window_fires(data, v, SPEC, d['rows'], cs, m)
                                       for cs in TT.t_placements(d['rows'], SPEC) for m in (False, True)):
            bad.append(f'harddrop: table {d["table"]} board {d["board"]} draws a T, or the window does not fire on it')
    if sorted(a['board'] for a in v.get('agreement', [])) != sorted(v.get('fires_on', [])):
        bad.append('window: the page\'s drawings of the shape (fires_on) are not the agreement\'s page drawings')
    # after: the TSD's after board is derived (the page draws it with the TST's T in), so the after rule is made here
    sp = by['basic.spin']
    got, _n = after_spin([''.join('t' if (r, c) in TT.spin_cells(sp) else ('-' if TT.is_empty(ch, SPEC) else 'c')
                                  for c, ch in enumerate(row)) for r, row in enumerate(sp['rows'])])
    if bottom(TT.occ_of(got, SPEC), TT.MAX_ROWS) != bottom(TT.occ_of(by['basic.after']['rows'], SPEC), TT.MAX_ROWS):
        measured.add('basic.after:after')
    if data['variants'][0]['followup']['board'] != 'basic.after' or by['tst.spin'].get('spin_of') != 'basic.after':
        bad.append('after: the follow-up is not read on the derived board the TST stands on')
    # catalogue: the opener catalogue's BT fields are bag 1 only, and the window cannot be placed on them at all
    cat = xs.get('catalogue', {})
    pages = [p for p in json.loads((HERE / cat.get('file', 'opener-fields.json')).read_text())['pages']
             if p['name'] in cat.get('names', [])]
    if not cat.get('names') or {p['name'] for p in pages} != set(cat['names']):
        bad.append(f'catalogue: {cat.get("names")} are not names in {cat.get("file")}')
    for p in pages:
        rows = [''.join(EMPTY if ch == '.' else 'c' for ch in r) for r in p['rows']]
        # False where the T is not the window's flat T; wherever it is, the window leaves the board (None)
        res = {TT.window_fires(data, v, SPEC, rows, cs, m) for cs in TT.t_placements(rows, SPEC) for m in (False, True)}
        if True in res or None not in res:
            bad.append(f'catalogue: the window is not off the board at every placement of its T on {p["name"]} ({res})')
    if any('BT' in json.dumps(o) for o in json.loads((HERE / 'wiki-openers.json').read_text())['openers']):
        bad.append('catalogue: wiki-openers.json now carries a BT field — read it as a cross-source')
    # build: each 72積み build's upper case is whole pieces, and the terrain keeps the 72積み stack's well column
    for i in range(1, 5):
        t, b = by[f's72.{i}.terrain']['rows'], by[f's72.{i}']['rows']
        if t[-1] != b[-1] or t[-1][2] != EMPTY or t[-1].count(EMPTY) != 1 or any(ch.isupper() for row in t for ch in row):
            bad.append(f'build: s72.{i}.terrain is not the 72積み stack less the page\'s upper-case pieces')
    return bad, measured


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='',
    upper_groups={u: 'separate' for u in 'IJOSZ'},
    extra_checks=extra_checks,
    external_drawings=lambda: harddrop_drawings(),
    html_checks=harddrop_snapshot_checks,
    # the same checks read nothing but the pinned wikitext, so a weekly api.php refetch can run them
    wikitext_checks=harddrop_snapshot_checks,
    synthetic_wikitext=lambda d: {d['cross_source']['harddrop']['snapshot_file']: _synthetic_harddrop(d)},
)


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def _set(rows, r, c, ch):
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _var(d):
    return d['variants'][0]


def _hdd(d, i):
    return d['cross_source']['harddrop']['drawings'][i]


def _hdm(d, table, board):
    return next(x for x in d['cross_source']['harddrop']['drawn_t_not_fired'] if (x['table'], x['board']) == (table, board))


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'parapet.terrain')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: d['page_order'].reverse(), 'page_order swapped', 'grammar:'),
    (lambda d: node(d, 'tst.spin').__setitem__('spin_of', 'nowhere'), 'a dangling reference', 'grammar:'),
    (lambda d: _set(node(d, 'bt.build')['rows'], 7, 0, '-'), 'a build board cell flipped', 'build:'),
    (lambda d: _set(node(d, 's72.3.terrain')['rows'], 7, 9, '-'), 'a derived terrain edited', 'build:'),
    (lambda d: _set(node(d, 'basic.after')['rows'], 2, 2, 'c'), 'the derived after board edited', 'build:'),
    (lambda d: _set(node(d, 'bt.terrain')['rows'], 4, 4, '-'), 'the second terrain not the first', 'build:'),
    (lambda d: (_set(node(d, 'basic.spin')['rows'], 5, 2, 'C'), _set(node(d, 'basic.spin')['rows'], 3, 2, 'U')),
     'the T pointing up', 'spin:'),
    (lambda d: _set(node(d, 'basic.spin')['rows'], 4, 0, 'c'), 'a cleared row drawn unmuted', 'spin:'),
    (lambda d: node(d, 'basic.spin').__setitem__('lines', 3), 'the TSD\'s line count', 'spin:'),
    (lambda d: node(d, 'tst.spin').__setitem__('lines', 2), 'the TST\'s line count', 'spin:'),
    (lambda d: (_set(node(d, 'tst.spin')['rows'], 4, 1, 'C'), _set(node(d, 'tst.spin')['rows'], 4, 2, 'U'),
                _set(node(d, 'basic.after')['rows'], 4, 1, 'C'), _set(node(d, 'basic.after')['rows'], 4, 2, '-')),
     'the TST\'s T not a T', 'spin:'),
    (lambda d: (_set(node(d, 'basic.after')['rows'], 1, 4, 'c'), _set(node(d, 'tst.spin')['rows'], 1, 4, 'c')),
     'the after board not what the TSD leaves', 'discrepancy:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [0, 4]), 'the window widened by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [0, 2]), 'the window narrowed by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [1, 6]), 'the window without the TST\'s overhang', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [0, 5]), 'the window without the TST\'s bottom cell', 'window:'),
    (lambda d: _var(d)['roof_cells'].pop(), 'a roof cell unnamed', 'window:'),
    (lambda d: _var(d)['agreement'][2].__setitem__('mirrored', True), 'a 72積み build read mirrored', 'window:'),
    (lambda d: _var(d)['agreement'][1].__setitem__('t_cells', [[4, 2], [4, 3], [4, 4], [5, 3]]),
     'a slot moved one column', 'window:'),
    (lambda d: _var(d).__setitem__('agreement', []), 'no page drawing in the agreement', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('t_cells_pre_clear', [[2, 1], [3, 1], [3, 2], [4, 1]]),
     'the follow-up\'s bottom cell read inside the cleared rows', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('lines', 2), 'the follow-up read as a TSD', 'window:'),
    (lambda d: _var(d)['fires_on'].append('parapet'), '欄干 listed as firing', 'window:'),
    (lambda d: _var(d)['misses'].append('s72.2'), 'a board it fires on listed as a miss', 'window:'),
    (lambda d: _set(node(d, 's72.1')['rows'], 1, 1, 'Z'), 'an upper-case piece broken', 'discrepancy:'),
    (lambda d: _set(node(d, 'bt.build')['rows'], 0, 1, 'z'), 'a piece broken', 'discrepancy:'),
    (lambda d: _hdd(d, 8).__setitem__('mirrored', True), 'a harddrop drawing read mirrored', 'harddrop:'),
    (lambda d: _set(_hdd(d, 8)['rows'], 2, 1, '-'), 'a harddrop drawing\'s overhang dropped', 'harddrop:'),
    (lambda d: _set(d['cross_source']['harddrop']['fires_without_slot'][0]['rows'], 1, 4, '-'),
     'a no-T harddrop board the window does not fire on', 'harddrop:'),
    (lambda d: _set(_hdd(d, 0)['rows'], 5, 2, 't'), 'a harddrop drawing with no drawn T', 'harddrop:'),
    (lambda d: [x.__setitem__('section', 'Basic Opening') for x in d['cross_source']['harddrop']['drawings']],
     'harddrop\'s mid-game section dropped', 'harddrop:'),
    (lambda d: d['cross_source']['harddrop']['drawings'].append(copy.deepcopy(_hdd(d, 0))), 'a harddrop drawing twice', 'harddrop:'),
    (lambda d: _hdm(d, 28, 0).__setitem__('t', 'stood'), 'a missed drawn T\'s lie misrecorded', 'harddrop:'),
    (lambda d: _hdm(d, 28, 0).__setitem__('window', 'leaves the board'), 'why the window misses a drawn T misrecorded', 'harddrop:'),
    (lambda d: _hdm(d, 31, 0).__setitem__('lines', 3), 'a missed drawn T\'s line count misrecorded', 'harddrop:'),
    (lambda d: _hdm(d, 6, 2).__setitem__('note', ''), 'a missed drawn T with no note', 'harddrop:'),
    (lambda d: d['cross_source']['harddrop']['drawn_t_not_fired'].append(
        {**copy.deepcopy(_hdd(d, 8)), 't': 'flat-down', 'lines': 2, 'window': 'disagrees', 'note': 'x'}),
     'a drawing the window fires on filed as a miss', 'harddrop:'),
    (lambda d: d['cross_source']['catalogue']['names'].append('Not An Opener'), 'a catalogue name that is not there', 'catalogue:'),
    (lambda d: d['cross_source'].pop('routes_fire_none'), 'no routes board and no reason', 'cross:'),
    (lambda d: d['cross_source']['fires'].append({'file': 'sdpcspin-routes.json', 'node': '3.first.cave',
                                                  'variant': 'btcannon', 'mirrored': True}),
     'a routes board recorded that does not fire', 'cross:'),
    (lambda d: node(d, 's72.4').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['known_discrepancies'].append({'id': 'bt.build:colour', 'note': 'x'}), 'a stale discrepancy', 'discrepancy:'),
]


def _no_external(spec):
    s = copy.copy(spec)
    s.external_drawings = None
    return s


def _parapet_as_drawing(spec):
    s = copy.copy(spec)
    rows = node(build(), 'parapet')['rows']
    s.external_drawings = lambda: harddrop_drawings() + [{'name': '欄干 as a BT', 'rows': rows,
                                                          't_cells': [[4, 1], [4, 2], [4, 3], [5, 2]], 'mirrored': False}]
    return s


SPEC_MUTANTS = [
    (_no_external, 'no external drawing (the window checked against this page alone)', 'window:'),
    (_parapet_as_drawing, '欄干 read as a drawing of the shape', 'window:'),
]


def _synthetic_harddrop(data: dict) -> str:
    """A wikitext holding the recorded drawings at their (table, board), every other board blank, each table
    under its recorded heading — the selftest's stand-in for the page CI cannot fetch."""
    hd = data['cross_source']['harddrop']
    every = hd['drawings'] + hd['drawn_t_not_fired'] + hd['fires_without_slot']
    n = max(d['table'] for d in every) + 1
    tables = [[] for _ in range(n)]
    for d in sorted(every, key=lambda x: (x['table'], x['board'])):
        t = tables[d['table']]
        while len(t) < d['board']:
            t.append([EMPTY * WIDTH] * 4)
        t.append(d['rows'])
    for t in tables:
        if not t:
            t.append([EMPTY * WIDTH] * 4)
    sec = {d['table']: d['section'] for d in every}
    out, last = [], None
    for i, t in enumerate(tables):
        s = sec.get(i, last)
        if s != last:
            out.append(f'\n== {s} ==\n')
            last = s
        out.append(RT.synthetic_wikitext([t]))
    return '\n'.join(out)


def selftest() -> int:
    rc = TT.run_selftest(SPEC, MUTANTS, {'board': ('CUUUCCCCCC', 'CUUUCCCCCc'), 'text': ('72積みからの派生', '72積みからの派性')},
                         SPEC_MUTANTS)
    base = build()
    text = _synthetic_harddrop(base)
    plants = {
        'a recorded drawing redrawn on the page': text.replace('{{pfrow|I|L|P|P|P|G|G|G|G|G}}', '{{pfrow|I|L|P|P|P|G|G|G|G| }}', 1),
        'a board the window fires on left unrecorded': text.replace('|}', '|{{pfstart}} ' + ' '.join(
            '{{pfrow|' + '|'.join(RT.wikitext_page_cell(ch) for ch in r) + '}}' for r in _hdd(base, 0)['rows'])
            + ' {{pfend}} |}', 1),
        'a heading renamed': text.replace('== Mid-game BT Cannon ==', '== Midgame BT Cannon ==', 1),
        'a no-T board the window fires on left unrecorded': text.replace('|}', '|{{pfstart}} ' + ' '.join(
            '{{pfrow|' + '|'.join(RT.wikitext_page_cell(ch) for ch in r) + '}}'
            for r in base['cross_source']['harddrop']['fires_without_slot'][0]['rows']) + ' {{pfend}} |}', 1),
    }
    ok = rc == 0
    clean = [x for x in harddrop_page_problems(base, text)]
    if clean or 'Mid-game BT Cannon' not in text:
        print(f'selftest FAILED: the synthetic harddrop page does not verify ({clean[:2]})')
        ok = False
    unnamed = copy.deepcopy(base)
    unnamed['cross_source']['harddrop']['drawn_t_not_fired'] = [
        x for x in unnamed['cross_source']['harddrop']['drawn_t_not_fired'] if (x['table'], x['board']) != (31, 0)]
    got = harddrop_page_problems(unnamed, text)
    if not any('drawn_t_not_fired names' in x for x in got):
        print(f'selftest FAILED: a drawn T the window misses, left out of the record, was not caught ({got[:2]})')
        ok = False
    else:
        print('  killed: a drawn T the window misses left out of the record  [harddrop:]')
    for label, page in plants.items():
        got = harddrop_page_problems(base, page)
        if page == text or not any(x.startswith('harddrop:') for x in got):
            print(f'selftest FAILED: {label} was not caught ({got[:2]})')
            ok = False
        else:
            print(f'  killed: {label}  [harddrop:]')
    # a board outside any table (revision 44634 draws two) is read, not refused or dropped: a firing drawing
    # appended as a loose board must come back as an unrecorded drawing, never as a parse failure or nothing
    loose = text + '\n{{pfstart}}\n' + '\n'.join(
        '{{pfrow|' + '|'.join(RT.wikitext_page_cell(ch) for ch in r) + '}}' for r in _hdd(base, 0)['rows']) + '\n{{pfend}}\n'
    got = harddrop_page_problems(base, loose)
    if not any('the window fires at the drawn T of' in x for x in got) or any('does not parse' in x for x in got):
        print(f'selftest FAILED: a loose board was not read as a one-board table ({got[:2]})')
        ok = False
    else:
        print('  killed: a firing drawing outside any table left unrecorded  [harddrop:]')
    with tempfile.TemporaryDirectory() as td:
        missing = harddrop_snapshot_checks(base, Path(td))
        (Path(td) / base['cross_source']['harddrop']['snapshot_file']).write_text(text)
        hashed = harddrop_snapshot_checks(base, Path(td))
    if not any('is not in' in x for x in missing) or not any('hash:' in x for x in hashed):
        print(f'selftest FAILED: the harddrop snapshot (missing={missing[:1]}, hashed={hashed[:1]})')
        ok = False
    else:
        print('  killed: the harddrop snapshot missing / its bytes not the pinned revision  [harddrop:]')
    print('selftest: harddrop checks all caught' if ok else 'selftest: FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))

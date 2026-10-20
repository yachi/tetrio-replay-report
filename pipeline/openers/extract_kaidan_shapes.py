"""Transcribe shiwehi.com's 階段のドネイト (Kaidan Setups) page into `kaidan-technique.json`.

    python3 -m pipeline.openers.extract_kaidan_shapes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_kaidan_shapes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_kaidan_shapes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_kaidan_shapes --html-dir <dir> --write  # ...and rewrite

The ninth MID-GAME TECHNIQUE page (中盤テンプレ・ドネイト), after STSD, STMB Cave, インペリアルクロス, ダブルダガー, BT砲,
千鳥格子, 社畜トレイン and 欄干: 「階段のドネイト」. A staircase four steps or more (the page's 「4段以上の階段」); a Z stood
on end on its lowest step, at the wall, makes a T slot, an O roofs the slot's end away from the wall, and the T laid flat, pointing down, clears the two
rows the Z's top half sits in — which leaves the column the Z's foot was beside open from the top to the floor (the
page: 「T-spinを打ちつつ地形を平らにすることができます」). A donation.

DECISION: ONE VARIANT, a full TSD with the flat, nub-down T (the anchor of STMB Cave, ダブルダガー, BT砲, 千鳥格子, 社畜トレイン
and 欄干), and a `payoff` in place of a follow-up (欄干's `well_quad`). The window predicate expresses the shape exactly
as it is, so NO SHARED RULE FILE CHANGED for this page: not the matcher, the planner, the gate or the renderer. The
「staircase over several locks」 that an earlier note in this repo guessed a Kaidan would need is not one: measured, the
staircase sits in the two rows the TSD clears (entailed by the clear, NaiveClauseForced) and in the two rows under them
(the well), all on one board at the TSD's lock, so no sequence of locks is needed. The window does not tell a staircase
from a flat stack: it holds only the steps beside the slot. harddrop's own page builds the same edge from other pieces
and from line clears (its 「Filling the Bottom Gap」, 「Line Clearing the Edge」 and 「Twist」 sections); those drawings carry
no T and the window fires on none of them, so that it would fire once each is completed is REASONED from its reading
occupancy only, not measured. The window counts no steps and
does not see the Z: the four-step basic form and the page's three-step S and J forms are one window (it fires on all
three).

THE PAYOFF, AND WHOSE IT IS. shiwehi.com names no Tetris: its next step is ST積み or よしひろ積み (「階段のドネイトを打った後は
ST積みやよしひろ積みへ移行できます」), which nothing here measures. harddrop says it: its Kaidan_Setups page (「After
performing the T-Spin Double, the empty column should be open again. The Kaidan setup is especially effective in games
that reward a Back-to-Back bonus.」), and its Anchor_Set page draws the I clearing four into the column a Kaidan
re-opened (`cross_source.harddrop_anchor_set.payoff_drawing`, checked under `payoff:`). So the variant carries 欄干's
`well_quad` payoff, attributed to harddrop in its note and in the prose, and the gate's rule (d') checks it on the
drawing: the well column is empty top to bottom on the after board and its filled cells on the spin board are the Z's
two, both in rows the spin clears.

WHY THE WINDOW IS THE AGREEMENT BOX (`window_basis: agreement`), and the one choice in it. The basic form draws an O
over the slot's end away from the wall and a stack to the left, none of it the shape. Over this page's three builds, its two DT砲
boards (drawn mirrored), harddrop's four Kaidan_Setups drawings, harddrop Anchor_Set's Kaidan (mirrored) and the Kaidan
BT砲's harddrop record holds (mirrored), anchored on the T, there are THREE maximal boxes on which every drawing agrees:
the cleared rows alone (all entailed), the cleared rows with the two well rows (no roof), and this one, the row above the
T, the cleared rows and the well rows, five by five. It is the only maximal box holding the roof, which is why it is the
window; the other two are measured in the facts test as controls (`OTHER_MAXIMAL_BOXES`), never asserted against. Its
bounds: left and up, harddrop's mid-board Kaidan (its L roof fills the cell two left of the T's arm, one row up);
right, this page drawing its well against the wall (widening right leaves the board); down, the S and J forms end at
the second well row; up, the O's top row against the S and J forms.

WHERE THE TRANSCRIPTION COMES FROM. `NODES` is a literal, hand-checked transcription of the page's RAW HTML, fetched the
way STSD's was: curl through the session proxy, TLS verification on, with a CA bundle adding the Let's Encrypt YE2
intermediate shiwehi.com omits. Eleven boards, plain text in `<div class="ttt">`, one row per line. harddrop's two
pages (Kaidan_Setups, and Anchor_Set) are the pinned revisions' own bytes from the MediaWiki API (urllib, a descriptive
User-Agent, never curl), read with `kd_cell` (below) and addressed by (table, board) through BT砲's `_sections`, so one
heading reading serves every harddrop transcription. Both pins carry `revision_sha1`, so `check_wikitext_sources`
discovers them by structure and re-reads them weekly through `--wikitext-dir`; the shiwehi page is re-read only by a
person with `--html-dir`.

THE HARDDROP READING (`kd_cell`), measured from the playfield template's images (File:<code>Tet.png, sha1s recorded in
`cell_images`): blank, `-` and `--` are EMPTY (`--Tet.png` is the same bytes as `-Tet.png`, white); a digit is FILLED
(`1Tet.png`..`4Tet.png` are dark cells with a numeral); `P` and `SP` are the T the page places (`U`; BT砲's `hd_cell`
reads only a bare `P` so, and reads `SP` as a piece `p`); `'X` is the X the page places next (`v`, read EMPTY on the
board before it — Anchor_Set's ghost I); `S` followed by a letter is that letter in the template's second skin, read
like the letter. Every other code is delegated to `hd_cell`, and `reading:` holds the two readers to the same occupancy
on every code of both pages and to the same letter on every code but the recorded special ones.

WHAT IS AN INFERENCE, flagged in the JSON (`reading`, the legend) rather than in prose only:

  * upper-case `C` and `T` in a spin board: the cleared rows, muted (checked by the spin rule); upper case on the two
    after-the-spin illustrations is an earlier stack drawn muted, NOT cleared rows (`illus:` checks no row of it is full).
  * the page names its two 「打後」 boards by no name (ST積み or よしひろ積み), so the transcription assigns none.
  * the two DT砲 boards draw the T as `U`; each is a spin board on a derived board, itself with its `U` read empty.
  * the definition's 「上手のように」 is the page's own typo for 「上図のように」 (quoted as printed; `reading_note`).
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
from pipeline.openers.extract_btcannon_shapes import _sections, hd_cell
from pipeline.openers.extract_cutcopy_shapes import hd_slots
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS
from pipeline.openers.route_transcription import EMPTY, WIDTH
from pipeline.openers.technique_transcription import node

HERE = Path(__file__).resolve().parent
OUT = HERE / 'kaidan-technique.json'
#: where the `other:` rule reads the other technique transcriptions; the selftest points it at a planted one
TECHNIQUE_DIR = HERE
BT_FILE = 'btcannon-technique.json'
SHACHIKU_FILE = 'shachikutrain-technique.json'
WIKI_FILE = 'wiki-tspin-techniques.json'

ALPHABET = frozenset('-cCtTUzZoOsSjJlLiI')


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/kaidansetup.php',
    'title': '階段のドネイト(Kaidan Setups)',
    'author': 'しゑひ(shiwehi)',
    'updated': '2021-03-23',
    'fetched': '2026-10-19',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle '
                    'that adds the Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), '
                    'the method STSD, STMB Cave, インペリアルクロス, ダブルダガー, BT砲, 千鳥格子, 社畜トレイン, 欄干, 山岳積み2号 '
                    'and stick spin used. The snapshot is the page\'s raw HTML, byte for byte; every board is plain '
                    'text in it, 11 ten-wide boards in page order.',
    'snapshot_file': 'kaidansetup.html',
    'snapshot_sha256': '3d501dd72bf6e163838d46bc6322cda1c962b9083017e6917aa40b8827d45dee',
    'snapshot_bytes': 26696,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable '
                     'in CI: the page is not committed and cannot be fetched there. Re-check with '
                     '--html-dir after any refetch (with harddrop\'s Kaidan_Setups.wikitext, Anchor_Set.wikitext and '
                     'STMB_Cave.wikitext beside it); an HTML hash moves with ANY byte of the page (ads, sidebar, a '
                     'date), so a moved hash means "read the board diff", not "the boards changed". Sentences are '
                     'compared against the page with its tags dropped.',
    'decorative_images': ['階段のドネイト(Kaidan Setups)タイトル画像', 'the related-page thumbnails (Tスピン, 開幕DT砲からの派生, '
                          'あめみや砲, アンカーセット, 脱初心者のための基本的なドネイト)'],
    'references': ['./derivedtcannonop.php (開幕DT砲からの派生)', './amemiyacannon.php (あめみや砲)',
                   './anchorset.php (アンカーセット; not matched, see ROADMAP.md)',
                   './basicdonating.php (脱初心者のための基本的なドネイト)'],
    'unfetched': ['the embedded video https://www.youtube.com/embed/-YZyjNNMSOw?start=152 (I凜\'s explanation, embedded '
                  'with permission per the page): not transcribed'],
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ',
    '-': 'empty',
    'c': 'a cell filled before this diagram (any piece, or garbage), grey',
    'i j l o s z': 'a cell of that piece, placed to build the shape',
    't': 'a cell of a T in a row no spin clears (the second 打後 board\'s stood T)',
    'T': 'a cell of the T in a row the spin clears (muted; OUR READING, checked: every upper-case row of a spin board '
         'is a full row)',
    'U': 'a cell of the T the spin places on the DT砲 boards (the renderer\'s light purple)',
    'C': 'on a spin board, an earlier cell in a row the spin clears (muted; checked the same way); on the two 打後 '
         'boards, an earlier stack drawn muted, in rows that are NOT full (`illus:`; the second board\'s stood T '
         'completes a row of unmuted cells below them)',
    'I J L O S Z': 'a cell of that piece in a row the spin clears, drawn muted',
    '%X': 'the X piece',
}

QUOTES = [
    {'id': 'intro', 'verbatim': 'ここでは、階段のドネイト(Kaidan Setups)という、ドネイトについて紹介していきます。'},
    {'id': 'h.basic', 'verbatim': '基本系'},
    {'id': 'def', 'verbatim': '階段のドネイトとは、上手のように4段以上の階段ができている時に、%Zを縦向きに置くことによって%Tの形を作り、'
                              '屋根をつけてT-spinを狙っていくというドネイトの一種です。',
     'reading_note': '「上手のように」 is the page\'s own typo for 「上図のように」 (as the figures above it); quoted as printed'},
    {'id': 'flat', 'verbatim': '図を見ると分かるように、T-spinを打ちつつ地形を平らにすることができます。'},
    {'id': 'three', 'verbatim': 'また、下図のように階段が3段しかない場合にも%Sや%Jを使用することによって階段のドネイトを打つことができます。'},
    {'id': 'h.after', 'verbatim': '打後'},
    {'id': 'after', 'verbatim': '階段のドネイトを打った後はST積みやよしひろ積みへ移行できます。'},
    {'id': 'h.dt', 'verbatim': '開幕DT砲後の階段のドネイト'},
    {'id': 'dt', 'verbatim': '開幕DT砲の派生として階段のドネイトを打つことができます。'},
    {'id': 'amemiya', 'verbatim': '%Lをソフトドロップした後に打つことができます。'},
    {'id': 'cap.amemiya', 'verbatim': 'あめみや砲'},
    {'id': 'anchor', 'verbatim': '%Jでアンカーセットを行って打つことができます。'},
    {'id': 'cap.anchor', 'verbatim': 'アンカーセットを用いた階段のドネイト'},
]

NODES = [
    {'id': 'basic.terrain', 'kind': 'base', 'caption_quote': 'h.basic',
     'label': 'a staircase of four steps down to the right wall, the wall column open two rows deep',
     'rows': _b('---------- ---------- cccccc---- ccccccc--- cccccccc-- ccccccccc- ccccccccc-')},
    {'id': 'basic.z', 'kind': 'build', 'on': 'basic.terrain', 'adds': 'z', 'caption_quote': 'def',
     'label': 'a Z stood on end on the lowest step, at the wall: the T\'s slot',
     'rows': _b('---------- ---------- cccccc---z ccccccc-zz ccccccccz- ccccccccc- ccccccccc-')},
    {'id': 'basic.o', 'kind': 'build', 'on': 'basic.z', 'adds': 'o', 'caption_quote': 'def',
     'label': 'an O roofing the slot\'s end away from the wall',
     'rows': _b('-----oo--- -----oo--- cccccc---z ccccccc-zz ccccccccz- ccccccccc- ccccccccc-')},
    {'id': 'basic.spin', 'kind': 'spin', 'spin_of': 'basic.o', 'spin': 'TSD', 'lines': 2, 'caption_quote': 'def',
     'label': 'the T laid flat, pointing down: a TSD clearing the two rows the Z\'s top half is in',
     'rows': _b('-----oo--- -----oo--- CCCCCCTTTZ CCCCCCCTZZ ccccccccz- ccccccccc- ccccccccc-')},
    {'id': 'basic.after', 'kind': 'after', 'after_of': 'basic.spin', 'caption_quote': 'flat',
     'label': 'what the TSD leaves: the stack flat, and the wall column open from the top to the floor (the O drawn grey)',
     'rows': _b('---------- ---------- -----cc--- -----cc--- ccccccccc- ccccccccc- ccccccccc-')},
    {'id': 's3.s', 'kind': 'build', 'on': 's3.terrain', 'adds': 'sz', 'caption_quote': 'three',
     'label': 'three steps: the Z and an S roofing the slot\'s end away from the wall',
     'rows': _b('---------- -----ss--- ccccss---z ccccccc-zz ccccccccz- ccccccccc-')},
    {'id': 's3.j', 'kind': 'build', 'on': 'j3.terrain', 'adds': 'jz', 'caption_quote': 'three',
     'label': 'three steps: the Z and a J roofing the slot\'s end away from the wall, over a hole under its stem',
     'rows': _b('---------- -----jj--- cccccj---z cccccjc-zz ccccccccz- ccccccccc-')},
    {'id': 'after.1', 'kind': 'illustration', 'caption_quote': 'after',
     'label': 'after a Kaidan, the next stack begun (the page does not say which of ST積み and よしひろ積み)',
     'rows': _b('-----ss--- CCCCss---z CCCCCcc-zz CCCCCcc-z- ccccccccc- ccccccccc- ccccccccc-')},
    {'id': 'after.2', 'kind': 'illustration', 'caption_quote': 'after',
     'label': 'after a Kaidan, the next stack begun with a stood T at the wall, which completes one row (the page names '
              'neither board)',
     'rows': _b('---------- -----ss--- CCCCss---t CCCCCcc-tt ccccccccct ccccccccc- ccccccccc-')},
    {'id': 'dt.amemiya', 'kind': 'spin', 'on': 'dt.amemiya.pre', 'adds': 'U', 'spin_of': 'dt.amemiya.pre',
     'spin_piece': 'U', 'spin': 'TSD', 'lines': 2, 'caption_quote': 'cap.amemiya',
     'label': 'after the DT砲 opener, the あめみや砲 branch (the L soft-dropped first): the Kaidan\'s TSD, mirrored',
     'rows': _b('---------- ---------- ---zz----i SUUUZZJJJI SSUCCCCCJI -scccccc-i -lcccccccc -lcccccccc '
                '-llccccccc')},
    {'id': 'dt.anchor', 'kind': 'spin', 'on': 'dt.anchor.pre', 'adds': 'U', 'spin_of': 'dt.anchor.pre',
     'spin_piece': 'U', 'spin': 'TSD', 'lines': 2, 'caption_quote': 'cap.anchor',
     'label': 'after the DT砲 opener, an アンカーセット with the J, then the Kaidan\'s TSD, mirrored',
     'rows': _b('---------i ---------i ---zz---li SUUUZZOOLI SSUCCCOOLL -scccccccc -jcccccccc -jcccccccc '
                'jj-ccccccc')},
    # ── derived: drawn nowhere on the page ──
    {'id': 's3.terrain', 'kind': 'derived', 'derived': True,
     'reading': 's3.s less its S and Z: three steps',
     'rows': _b('---------- ---------- cccc------ ccccccc--- cccccccc-- ccccccccc-')},
    {'id': 'j3.terrain', 'kind': 'derived', 'derived': True,
     'reading': 's3.j less its J and Z: three steps, a hole under the J\'s stem',
     'rows': _b('---------- ---------- ccccc----- ccccc-c--- cccccccc-- ccccccccc-')},
    {'id': 'dt.amemiya.pre', 'kind': 'derived', 'derived': True,
     'reading': 'dt.amemiya with its U read empty: the slot the T goes into',
     'rows': _b('---------- ---------- ---zz----i S---ZZJJJI SS-CCCCCJI -scccccc-i -lcccccccc -lcccccccc '
                '-llccccccc')},
    {'id': 'dt.anchor.pre', 'kind': 'derived', 'derived': True,
     'reading': 'dt.anchor with its U read empty: the slot the T goes into',
     'rows': _b('---------i ---------i ---zz---li S---ZZOOLI SS-CCCOOLL -scccccccc -jcccccccc -jcccccccc '
                'jj-ccccccc')},
]

_T = [[2, 6], [2, 7], [2, 8], [3, 7]]
_DT_T = [[3, 1], [3, 2], [3, 3], [4, 2]]
_PAYOFF_NOTE = ('a Tetris into the column the TSD re-opens: HARDDROP\'s next step, not shiwehi.com\'s. harddrop\'s Kaidan_Setups '
                'page: 「After performing the T-Spin Double, the empty column should be open again. The Kaidan setup is '
                'especially effective in games that reward a Back-to-Back bonus.」; its Anchor_Set page draws the I '
                'clearing four into that column (cross_source.harddrop_anchor_set.payoff_drawing). shiwehi.com names no '
                'Tetris: its next step is ST積み or よしひろ積み, which nothing here measures. The matcher carries the well cell '
                'to the first later lock that puts a cell in its column and asks whether that lock is an I the engine '
                'credits with four lines')

#: the variant's window, in basic.spin's frame
VARIANTS = [{
    'id': 'kaidan', 'board': 'basic.spin', 'spin': 'TSD', 'lines': 2,
    'window_basis': 'agreement',
    'window': {'rows': [1, 5], 'cols': [5, 9]},
    't_cells': _T,
    'roof_cells': [[1, 5], [1, 6]],
    'window_note': 'in basic.spin\'s frame, row 0 the top: the AGREEMENT BOX of this page\'s three builds and two DT砲 '
                   'boards (mirrored), harddrop\'s four Kaidan_Setups drawings, harddrop Anchor_Set\'s Kaidan (mirrored) '
                   'and the Kaidan BT砲\'s harddrop record holds (mirrored). Row 1 is the row above the T: the roof over its '
                   'end away from the wall filled, the cells over its nub, its far arm and the Z\'s top empty; rows 2-3 are the rows the '
                   'TSD clears (entailed by the clear at a full TSD, NaiveClauseForced); rows 4-5 are the two rows under '
                   'them: the Z\'s foot and the steps filled, the wall column (the well) empty. THE ONE CHOICE: there are '
                   'three maximal boxes on which every drawing agrees (the cleared rows alone; the cleared rows and the '
                   'well rows; this one), and this is the only one holding the roof. Occupancy only, never colour; garbage '
                   'is filled.',
    'untested_drawn': {'cells': [[0, 5], [0, 6]],
                       'reason': 'the O roof\'s top row: the S and J forms roof the slot with a piece one row lower and '
                                 'draw nothing there, so the drawings disagree one row above the window'},
    'agreement': [
        {'board': 'basic.o', 't_cells': _T, 'mirrored': False},
        {'board': 's3.s', 't_cells': _T, 'mirrored': False},
        {'board': 's3.j', 't_cells': _T, 'mirrored': False},
        {'board': 'dt.amemiya.pre', 't_cells': _DT_T, 'mirrored': True},
        {'board': 'dt.anchor.pre', 't_cells': _DT_T, 'mirrored': True},
    ],
    'payoff': {'kind': 'well_quad', 'board': 'basic.after', 'piece': 'I', 'lines': 4,
               'well_cell_pre_clear': [4, 9], 'well_cell_after': [4, 9], 'note': _PAYOFF_NOTE},
    'fires_on': ['basic.o', 's3.s', 's3.j'],
    #: the page's mirrored drawings: the window fires on each exactly once, mirrored (`dt:`; the shared rule (e)
    #: takes only as-drawn boards), at the DT砲's own drawn T
    'fires_mirrored': ['dt.amemiya.pre', 'dt.anchor.pre'],
    'misses': ['basic.terrain', 'basic.z', 'basic.after', 's3.terrain', 'j3.terrain', 'after.1', 'after.2'],
}]

#: File:<code>Tet.png, the playfield template's cell images (Template:Pfrow draws File:{{{n}}}Tet.png), read once
#: through api.php imageinfo on 2026-10-19 and looked at; sha1 is MediaWiki's. Hand-measured: nothing re-fetches them
CELL_IMAGES = {
    '': {'file': 'Tet.png', 'sha1': '4a13b4b3a08a50a8071886b018675b558a926659', 'reads': 'empty (white)'},
    '-': {'file': '-Tet.png', 'sha1': '9e1b403ca10552c673fd936a775506ece6e71da4', 'reads': 'empty (white)'},
    '--': {'file': '--Tet.png', 'sha1': '9e1b403ca10552c673fd936a775506ece6e71da4',
           'reads': 'empty (white; the same bytes as -Tet.png)'},
    '1': {'file': '1Tet.png', 'sha1': '6ea1e1f134e34947d537d6c7ecc4096851931a2c',
          'reads': 'filled (a dark cell with a numeral)'},
    '2': {'file': '2Tet.png', 'sha1': 'cdb5218ba0f48435ebf25711e5d6920a882f1903',
          'reads': 'filled (a dark cell with a white numeral)'},
    '3': {'file': '3Tet.png', 'sha1': '1a599fead6d8ec95ec9f065b19382e8ef4c37f54',
          'reads': 'filled (a dark cell with a white numeral)'},
    '4': {'file': '4Tet.png', 'sha1': '40e079cd59fc1ee68dfd1fd26fb1cac95cfff188',
          'reads': 'filled (a dark cell with a white numeral)'},
    'P': {'file': 'PTet.png', 'sha1': '72e099fc958e4708a34b407164e07473093799d1',
          'reads': 'the T placed (white, a T-coloured margin)'},
    'SP': {'file': 'SPTet.png', 'sha1': '9ad7b972afebe1cac23290b7050256627b2f0cca',
           'reads': 'the T placed, the second skin (white, a T-coloured margin)'},
    "'I": {'file': "'ITet.png", 'sha1': '1a159d4dbc3c85e4ef31ad8942a8792dbae37f75',
           'reads': 'the I placed next (white, an I-coloured margin)'},
}

#: the codes `kd_cell` reads differently from BT砲's `hd_cell` (every other code is delegated to it)
READING = {
    'blank, - and --': 'empty',
    'a digit': 'g, FILLED (hd_cell reads it as the digit itself, also filled)',
    'P and SP': 'U, the T the page places (hd_cell reads SP as a piece p)',
    "'X": 'v, the X the page places next, read EMPTY on the board before it (hd_cell reads it as the piece, filled)',
    'S followed by a letter': 'that letter, lower case: the template\'s second skin (as hd_cell)',
    'other': 'hd_cell: its last letter in lower case (G grey, Q a lighter grey), every one FILLED',
    'slots': 'a board\'s U cells are partitioned into T\'s (千鳥格子\'s hd_slots); each T is one slot, read with every U '
             'and v cell of the board empty',
}


def _hd(n: int, table: int, board: int, section: str, mirrored: bool, slot: list, rows: str) -> dict:
    return {'n': n, 'table': table, 'board': board, 'section': section, 'mirrored': mirrored, 'slot': slot,
            'rows': _b(rows)}


def _miss(n: int, table: int, board: int, section: str, slot: list, lie: tuple, note: str, rows: str) -> dict:
    t, lines, window = lie
    return {'n': n, 'table': table, 'board': board, 'section': section, 'slot': slot, 't': t, 'lines': lines,
            'window': window, 'note': note, 'rows': _b(rows)}


def _nos(n: int, table: int, board: int, section: str, mirrored: bool, slot: list, rows: str) -> dict:
    return {'n': n, 'table': table, 'board': board, 'section': section, 'mirrored': mirrored, 'slot': slot,
            'rows': _b(rows)}


GF, SS, GT, TR = 'General Formation', 'Step by Step', 'General Tips', 'Transfers'
TD, LB, FU, UU = 'T-Spin Double Replacements', 'Line Clear Base', 'Followups', 'Useful Usages'

#: the cells `kd_cell` reads with its own rule, per code: [table, board, row, col], measured off each page
SPECIAL_KAIDAN = {'--': [[1, 0, 3, 6], [1, 0, 3, 7], [1, 0, 3, 8], [1, 0, 3, 9], [1, 0, 4, 7], [1, 0, 4, 8], [1, 0, 4, 9], [1, 0,
    5, 8], [1, 0, 5, 9], [2, 1, 3, 0], [2, 1, 3, 1], [2, 1, 3, 2], [2, 1, 3, 3], [2, 1, 3, 4], [2, 1, 3, 5], [2,
    1, 3, 6], [2, 1, 3, 7], [2, 1, 3, 8], [2, 1, 3, 9], [2, 1, 4, 0], [2, 1, 4, 1], [2, 1, 4, 2], [2, 1, 4, 3],
    [2, 1, 4, 4], [2, 1, 4, 5], [2, 1, 4, 6], [2, 1, 4, 7], [2, 1, 4, 8], [2, 1, 4, 9], [4, 0, 4, 0], [4, 0, 5,
    0], [4, 1, 4, 0], [4, 1, 5, 0], [4, 2, 4, 0], [4, 2, 5, 0], [4, 3, 4, 0], [4, 3, 5, 0], [7, 1, 2, 5], [7, 2,
    2, 5], [7, 2, 3, 5]], '1': [[3, 0, 5, 8], [3, 1, 5, 8], [4, 0, 5, 1], [4, 0, 5, 2], [4, 0, 5, 3], [4, 0, 5,
    4], [4, 0, 5, 5], [4, 0, 5, 7], [4, 0, 5, 8], [4, 0, 5, 9], [4, 1, 5, 1], [4, 1, 5, 2], [4, 1, 5, 3], [4, 1,
    5, 4], [4, 1, 5, 5], [4, 1, 5, 7], [4, 1, 5, 8], [4, 1, 5, 9], [4, 2, 5, 1], [4, 2, 5, 2], [4, 2, 5, 3], [4,
    2, 5, 4], [4, 2, 5, 5], [4, 2, 5, 7], [4, 2, 5, 8], [4, 2, 5, 9], [4, 3, 5, 1], [4, 3, 5, 2], [4, 3, 5, 3],
    [4, 3, 5, 4], [4, 3, 5, 5], [4, 3, 5, 7], [4, 3, 5, 8], [4, 3, 5, 9]], '2': [[3, 0, 4, 7], [3, 1, 4, 7], [4,
    0, 4, 1], [4, 0, 4, 2], [4, 0, 4, 3], [4, 0, 4, 4], [4, 0, 4, 7], [4, 0, 4, 8], [4, 0, 4, 9], [4, 1, 4, 1],
    [4, 1, 4, 2], [4, 1, 4, 3], [4, 1, 4, 4], [4, 1, 4, 7], [4, 1, 4, 8], [4, 1, 4, 9], [4, 2, 4, 1], [4, 2, 4,
    2], [4, 2, 4, 3], [4, 2, 4, 4], [4, 2, 4, 7], [4, 2, 4, 8], [4, 2, 4, 9], [4, 3, 4, 1], [4, 3, 4, 2], [4, 3,
    4, 3], [4, 3, 4, 4], [4, 3, 4, 7], [4, 3, 4, 8], [4, 3, 4, 9]], '3': [[3, 0, 3, 6], [3, 1, 3, 6]], '4': [[3,
    0, 2, 5], [3, 1, 2, 5]], 'SP': [[0, 2, 3, 6], [0, 2, 3, 7], [0, 2, 3, 8], [0, 2, 4, 7], [2, 0, 3, 6], [2, 0,
    3, 7], [2, 0, 3, 8], [2, 0, 4, 7], [4, 2, 2, 3], [4, 2, 2, 4], [4, 2, 2, 5], [4, 2, 3, 4], [27, 2, 2, 6],
    [27, 2, 2, 7], [27, 2, 2, 8], [27, 2, 3, 7], [30, 2, 2, 7], [30, 2, 3, 6], [30, 2, 3, 7], [30, 2, 4, 7],
    [31, 2, 3, 6], [31, 2, 3, 7], [31, 2, 3, 8], [31, 2, 4, 7], [32, 1, 3, 6], [32, 1, 3, 7], [32, 1, 3, 8],
    [32, 1, 4, 7], [33, 1, 2, 6], [33, 1, 2, 7], [33, 1, 2, 8], [33, 1, 3, 7], [34, 1, 2, 9], [34, 1, 3, 8],
    [34, 1, 3, 9], [34, 1, 4, 9], [34, 2, 3, 6], [34, 2, 3, 7], [34, 2, 3, 8], [34, 2, 4, 7]]}

SPECIAL_ANCHOR = {"'I": [[1, 2, 1, 0], [1, 2, 2, 0], [1, 2, 3, 0], [1, 2, 4, 0], [2, 2, 3, 1], [2, 2, 4, 1], [2, 2, 5, 1], [2, 2,
    6, 1], [10, 1, 4, 0], [10, 1, 5, 0], [10, 1, 6, 0], [10, 1, 7, 0], [11, 1, 2, 1], [11, 1, 3, 1], [11, 1, 4,
    1], [11, 1, 5, 1], [12, 0, 3, 0], [12, 0, 4, 0], [12, 0, 5, 0], [12, 0, 6, 0], [14, 1, 2, 5], [14, 1, 3, 5],
    [14, 1, 4, 5], [14, 1, 5, 5], [15, 1, 2, 4], [15, 1, 3, 4], [15, 1, 4, 4], [15, 1, 5, 4], [16, 2, 2, 5],
    [16, 2, 3, 5], [16, 2, 4, 5], [16, 2, 5, 5], [17, 2, 3, 6], [17, 2, 4, 6], [17, 2, 5, 6], [17, 2, 6, 6]],
    '1': [[3, 0, 4, 2]], '2': [[3, 0, 3, 2]], '3': [[3, 0, 2, 2]], '4': [[3, 0, 1, 2]], 'P': [[7, 0, 4, 1], [7,
    0, 4, 2], [7, 0, 4, 3], [7, 0, 5, 2], [7, 1, 3, 2], [7, 1, 4, 2], [7, 1, 4, 3], [7, 1, 5, 2], [9, 0, 5, 1],
    [9, 0, 5, 2], [9, 0, 5, 3], [9, 0, 6, 2], [9, 1, 4, 2], [9, 1, 5, 1], [9, 1, 5, 2], [9, 1, 6, 2], [9, 2, 3,
    1], [9, 2, 4, 1], [9, 2, 4, 2], [9, 2, 5, 1], [10, 0, 3, 1], [10, 0, 3, 2], [10, 0, 3, 3], [10, 0, 4, 2],
    [11, 0, 1, 2], [11, 0, 2, 2], [11, 0, 2, 3], [11, 0, 3, 2], [12, 1, 6, 7], [12, 1, 6, 8], [12, 1, 6, 9],
    [12, 1, 7, 8]]}

#: harddrop's Kaidan_Setups page (the title "Kaidan" redirects here): every board with a drawn T the window fires at
HARDDROP = {
    'page': 'https://harddrop.com/wiki/Kaidan_Setups',
    'title': 'Kaidan Setups',
    'oldid': 37594,
    'revision_sha1': '698d8565e9a95ed38ed7989a4d7a153c319bfe0f',
    'revision_timestamp': '2023-11-01T22:37:17Z',
    'fetched': '2026-10-19',
    'fetch_method': 'the latest revision\'s own bytes from the MediaWiki API (api.php?action=query&prop=revisions&'
                    'titles=Kaidan_Setups&rvprop=ids|sha1|size|timestamp|content&rvslots=main), with Python\'s urllib '
                    'and a descriptive User-Agent (NOT curl); the API\'s sha1 equals the sha1 of the bytes, and 37594 was '
                    'the page\'s latest revision when fetched',
    'snapshot_file': 'Kaidan_Setups.wikitext',
    'snapshot_sha256': 'b7d13f7e9f5c7e68e903cc9d61c4c5259095c80596fdd259f3d1b1147f107b5e',
    'snapshot_bytes': 28991,
    'snapshot_note': 'not committed: check_wikitext_sources refetches the pinned revision weekly through api.php and '
                     're-checks it with --wikitext-dir; a person re-checks it with --html-dir, the file beside '
                     'kaidansetup.html',
    'author_note': 'harddrop\'s page, edited by its wiki editors: another site and other authors than shiwehi.com, and a '
                   'page the shiwehi.com page does not cite (found by its title, which "Kaidan" redirects to), so it is '
                   'independent of it',
    'categories': ['Mid-game T-Spin setups', 'T-Spin setups', 'T-Spin techniques'],
    'quote': 'After performing the T-Spin Double, the empty column should be open again. The Kaidan setup is '
             'especially effective in games that reward a Back-to-Back bonus.',
    'board_counts': [4, 4, 3, 2, 4, 2, 2, 3, 3, 4, 2, 2, 2, 2, 1, 2, 2, 2, 3, 2, 4, 4, 2, 2, 4, 3, 2, 4, 3, 2, 3, 3, 4, 3, 3],
    'reading': READING,
    #: the cells whose code kd_cell reads with its own rule ([table, board, row, col] per code): checked on the page
    'special_cells': SPECIAL_KAIDAN,
    'drawings': [
        _hd(2, 0, 2, GF, False, [[3, 6], [3, 7], [3, 8], [4, 7]],
            '---------- ---------- ggggggg--- ggggggUUUz gggggggUzz ggggggggz- ggggggggg-'),
        _hd(8, 2, 0, SS, False, [[3, 6], [3, 7], [3, 8], [4, 7]],
            '---------- -----oo--- -----oo--- ggggggUUUz gggggggUzz ggggggggz- ggggggggg-'),
        _hd(15, 4, 2, GT, False, [[2, 3], [2, 4], [2, 5], [3, 4]],
            '---l------ -lll------ gggUUUzggg ggggUzzggg -ggggz-ggg -ggggg-ggg'),
        _hd(92, 33, 1, TR, False, [[2, 6], [2, 7], [2, 8], [3, 7]],
            'gggg------ gggglll--- gggglgUUUz gggggggUzz ggggggggz- ggggggggg-'),
    ],
    #: every OTHER drawn T on the page: the window does not fire at it in either hand, each named with what the T is,
    #: measured (`t` its lie, `lines` the rows it fills as drawn, `window` why it does not fire) and a note read off
    #: the page around it. With `drawings` this is EVERY drawn T on the page
    'drawn_t_not_fired': [
        _miss(74, 27, 2, LB, [[2, 6], [2, 7], [2, 8], [3, 7]], ('flat-down', 2, 'disagrees'),
              'the Line Clear Base: the hole sits under the T\'s right arm, not beside the Z\'s foot (the window\'s well '
              'cells (1,9) and (4,9) and the step (4,8) disagree)',
              '-----oo--- -----oo--j ggggggUUUj gggggggUjj gggggggg-g ggggggggg-'),
        _miss(83, 30, 2, TD, [[2, 7], [3, 6], [3, 7], [4, 7]], ('stood', 1, "not the window's T"),
              'a T-Spin Double Replacement: an Imperial TSS (the T stood up)',
              '---------- ------l--- ----lllU-- ggggggUU-- gggggggUoo ggggggggg-'),
        _miss(86, 31, 2, TD, [[3, 6], [3, 7], [3, 8], [4, 7]], ('flat-down', 1, 'leaves the board'),
              'a T-Spin Double Replacement: the TSD slot fired as a TSS (one row fills)',
              '---------- ------l--- ----lll--- ggggggUUU- gggggggUoo ggggggggg-'),
        _miss(88, 32, 1, TR, [[3, 6], [3, 7], [3, 8], [4, 7]], ('flat-down', 2, 'leaves the board'),
              'a Transfer: the Kaidan drawn one row above the board\'s floor, so the window\'s second well row is under '
              'the drawing',
              'gggg------ gggggoo--- gggggoo--- ggggggUUUz gggggggUzz ggggggggz-'),
        _miss(95, 34, 1, TR, [[2, 9], [3, 8], [3, 9], [4, 9]], ('stood', 1, "not the window's T"),
              'a Transfer: a stood T at the wall in the Z\'s place',
              '---------- -----ss--- ggggss---U gggglll-UU ggggggggzU ggggggggg-'),
        _miss(96, 34, 2, TR, [[3, 6], [3, 7], [3, 8], [4, 7]], ('flat-down', 2, 'leaves the board'),
              'a Transfer: the TSD over the stood T of the board before, drawn one row above the floor',
              '---------- ---------- -----ss--- ggggssUUUt gggglllUtt ggggggggg-'),
    ],
    #: boards with no T drawn on which the window fires at a resting placement
    'fires_without_slot': [
        _nos(1, 0, 1, GF, False, [[3, 6], [3, 7], [3, 8], [4, 7]],
             '---------- ---------- ggggggg--- gggggg---z ggggggg-zz ggggggggz- ggggggggg-'),
        _nos(6, 1, 2, SS, False, [[3, 6], [3, 7], [3, 8], [4, 7]],
             '---------- -----oo--- -----oo--- gggggg---z ggggggg-zz ggggggggz- ggggggggg-'),
        _nos(14, 4, 1, GT, False, [[2, 3], [2, 4], [2, 5], [3, 4]],
             '---l------ -lll------ ggg---zggg gggg-zzggg -ggggz-ggg -ggggg-ggg'),
        _nos(18, 5, 1, GT, False, [[2, 6], [2, 7], [2, 8], [3, 7]],
             '-----oo--- -----oo--- gggggg---z ggggggg-zz ggggggggz- ggggggggg-'),
        _nos(20, 6, 1, GT, False, [[2, 6], [2, 7], [2, 8], [3, 7]],
             '-----oo--- -----oo--- gggggg---z ggggggg-zz ggggggggz- ggggggggg-'),
        _nos(78, 28, 2, TD, False, [[4, 6], [4, 7], [4, 8], [5, 7]],
             '---------- ---------- -----oo--- -----oo--- gggggg---z ggggggg-zz ggggggggz- ggggggggg- ggggggggg-'),
        _nos(91, 33, 0, TR, False, [[2, 6], [2, 7], [2, 8], [3, 7]],
             'gggg------ gggglll--- gggglg---z ggggggg-zz ggggggggz- ggggggggg-'),
    ],
}

#: harddrop's Anchor_Set page: its Kaidan (a drawing), its Tetris after one (the payoff drawing) and every other drawn T
HARDDROP_ANCHOR_SET = {
    'page': 'https://harddrop.com/wiki/Anchor_Set',
    'title': 'Anchor Set',
    'oldid': 40815,
    'revision_sha1': '0bfdd986120f5dd20cdc8b6a3b615b84bc7db415',
    'revision_timestamp': '2024-10-05T01:12:14Z',
    'fetched': '2026-10-19',
    'fetch_method': 'the latest revision\'s own bytes from the MediaWiki API, as Kaidan_Setups\' (urllib, NOT curl); '
                    '40815 was the page\'s latest revision when fetched',
    'snapshot_file': 'Anchor_Set.wikitext',
    'snapshot_sha256': 'f936bc67866039667595b5c8478d7733165cf3c3bf0f9bb43fbf9c5586fc158f',
    'snapshot_bytes': 10665,
    'snapshot_note': 'not committed: check_wikitext_sources refetches it weekly as Kaidan_Setups\'',
    'author_note': 'harddrop\'s page (another site than shiwehi.com); pinned here so a later アンカーセット pass starts from a '
                   'pinned source',
    'categories': ['Tetris techniques'],
    'quote': 'Anchor Set could be used with Kaidan for extra firepower. This one is especially used with the J anchor.',
    'board_counts': [1, 4, 4, 1, 2, 2, 1, 2, 1, 3, 2, 2, 2, 1, 3, 3, 4, 4],
    'reading': READING,
    'special_cells': SPECIAL_ANCHOR,
    'drawings': [
        _hd(21, 10, 0, UU, True, [[3, 1], [3, 2], [3, 3], [4, 2]],
            '---------- ---------i ---zz--lli sUUUzzooli ssUgggooli -sgggggggg -jgggggggg -jgggggggg jj-ggggggg'),
    ],
    #: the I clearing four into the column the Kaidan re-opened (`'I` cells: one vertical I in column 0)
    'payoff_drawing': {'n': 22, 'table': 10, 'board': 1, 'section': UU, 'column': 0, 'cleared': 4,
                       'note': 'the board beside #21 in the same table (a later board of that line, not what #21\'s TSD '
                               'leaves, by occupancy): the ghost I placed into the column the Kaidan re-opened, at the left '
                               'wall, four deep',
                       'rows': _b('---------- ---------- -l-------- -l----ss-g vllggssggg vggggggggg vggggggggg '
                                  'vggggggggg gg-ggggggg')},
    'drawn_t_not_fired': [
        _miss(15, 7, 0, FU, [[4, 1], [4, 2], [4, 3], [5, 2]], ('flat-down', 2, 'leaves the board'),
              'a Followup: a TSD over the anchor\'s hole, at the board\'s floor',
              '---------- ---------- -z-------j zz-------j zUUUiiiijj ggUggggggg'),
        _miss(16, 7, 1, FU, [[3, 2], [4, 2], [4, 3], [5, 2]], ('stood', 3, "not the window's T"),
              'a Followup: a TST into the anchor\'s hole',
              '---------- -ss------- ss-------- ooUzzqqqqq ooUUzzqqqq ggUggggggg'),
        _miss(18, 9, 0, FU, [[5, 1], [5, 2], [5, 3], [6, 2]], ('flat-down', 2, 'leaves the board'),
              'a Followup: a TSD at the board\'s floor',
              '---------- ---------- ---------- ---------- g--zz----- gUUUzziiii ggUggggggg'),
        _miss(19, 9, 1, FU, [[4, 2], [5, 1], [5, 2], [6, 2]], ('stood', 2, "not the window's T"),
              'a Followup: a stood T into the anchor\'s hole',
              '---------- -oo------- soo------- ss-------- gsUzzqqqqq gUU-zzqqqq ggUggggggg'),
        _miss(20, 9, 2, FU, [[3, 1], [4, 1], [4, 2], [5, 1]], ('stood', 2, "not the window's T"),
              'a Followup: a stood T beside the anchor',
              '---------- jj-------- j--------- jUllqqqqqq gUUlqqqqqq gU-lqqqqqq gg-ggggggg'),
        _miss(23, 11, 0, UU, [[1, 2], [2, 2], [2, 3], [3, 2]], ('stood', 1, "not the window's T"),
              'a Useful Usage: a stood T over an L anchor',
              '---------- l-Uzz----- l-UUzz---- llUggggggg l-gggggggg l-gggggggg ll-ggggggg'),
        _miss(26, 12, 1, UU, [[6, 7], [6, 8], [6, 9], [7, 8]], ('flat-down', 2, 'leaves the board'),
              'a Useful Usage: a TSD at the board\'s floor',
              '---------- ---------- ---------- ---------- ---------- oo----jj-- oolllzjUUU jjlgggggUg'),
    ],
    'fires_without_slot': [],
}

#: the Kaidan BT砲's harddrop record holds (its own note names it): read from btcannon-technique.json, never copied
BT_CANNON = {
    'file': BT_FILE,
    'list': 'drawn_t_not_fired',
    'table': 28, 'board': 0, 'mirrored': True,
    'page': 'https://harddrop.com/wiki/BT_Cannon',
    'note': 'the Kaidan harddrop\'s BT_Cannon page fires on the same base as a mid-game BT (its record\'s own note names '
            'it): this window fires on it once, mirrored, at its drawn T',
}

#: harddrop's STMB_Cave page, its last table: an STMB Cave variation beside a Kaidan. Pinned by 社畜トレイン's
#: `cross_source.stmb_cave` (the same revision), NOT re-pinned here: this record names no revision sha1
STMB_CAVE_KAIDAN = {
    'pin': f'{SHACHIKU_FILE} cross_source.stmb_cave',
    'page': 'https://harddrop.com/wiki/STMB_Cave',
    'table': 20, 'board': 1,
    'caption': 'Compare this variation of STMB Cave below with [[Kaidan]]. On these kinds of terrain, one could choose '
               'either one of these techniques depending on their NEXT queue after the T-Spin Double or the terrain '
               'left over after the T-Spin Double.',
    'slot': [[3, 3], [3, 4], [3, 5], [4, 4]],
    't': 'flat-down', 'lines': 2, 'window': 'leaves the board',
    'note': 'the Kaidan is drawn one row under the clear: the window\'s second well row is under the drawing, so it '
            'leaves the board in both hands (measured)',
    'rows': _b('---------- oo-------- ooss---j-- gssUUUzjjj ggggUzzggg gggggz-ggg'),
}

#: measured: this window over every board of every other committed technique transcription (`kaidan_fires_on`), and
#: every other technique window over every drawing this file holds (`fires_on_kaidan`); `other:` holds both complete
OTHER_WINDOWS = {
    'kaidan_fires_on': [{'file': 'btcannon-technique.json', 'board': 'cross_source.harddrop.drawn_t_not_fired[29]', 'cells': [[4,
        3], [4, 4], [4, 5], [5, 4]], 'mirrored': [True]}, {'file': 'shachikutrain-technique.json', 'board':
        'nodes.u2.spin', 'cells': [[2, 1], [2, 2], [2, 3], [3, 2]], 'mirrored': [False]}, {'file':
        'shachikutrain-technique.json', 'board': 'nodes.t3.spin', 'cells': [[2, 1], [2, 2], [2, 3], [3, 2]],
        'mirrored': [False]}, {'file': 'shachikutrain-technique.json', 'board': 'nodes.dt', 'cells': [[3,
        2], [3, 3], [3, 4], [4, 3]], 'mirrored': [True]}, {'file': 'shachikutrain-technique.json', 'board':
        'nodes.u2.build', 'cells': [[2, 1], [2, 2], [2, 3], [3, 2]], 'mirrored': [False]}, {'file':
        'shachikutrain-technique.json', 'board': 'nodes.t3.build', 'cells': [[2, 1], [2, 2], [2, 3], [3,
        2]], 'mirrored': [False]}, {'file': 'shachikutrain-technique.json', 'board':
        'cross_source.harddrop.drawings[2]', 'cells': [[3, 3], [3, 4], [3, 5], [4, 4]], 'mirrored':
        [False]}, {'file': 'shachikutrain-technique.json', 'board': 'cross_source.harddrop.drawings[3]',
        'cells': [[3, 5], [3, 6], [3, 7], [4, 6]], 'mirrored': [False]}, {'file':
        'shachikutrain-technique.json', 'board': 'cross_source.harddrop.drawings[4]', 'cells': [[3, 4], [3,
        5], [3, 6], [4, 5]], 'mirrored': [False]}, {'file': 'shachikutrain-technique.json', 'board':
        'cross_source.harddrop.drawings[7]', 'cells': [[3, 3], [3, 4], [3, 5], [4, 4]], 'mirrored':
        [False]}, {'file': 'shachikutrain-technique.json', 'board': 'cross_source.harddrop.drawings[9]',
        'cells': [[3, 3], [3, 4], [3, 5], [4, 4]], 'mirrored': [False]}, {'file':
        'shachikutrain-technique.json', 'board': 'cross_source.harddrop.drawings[12]', 'cells': [[3, 4], [3,
        5], [3, 6], [4, 5]], 'mirrored': [True]}, {'file': 'shachikutrain-technique.json', 'board':
        'cross_source.harddrop.drawings[19]', 'cells': [[5, 5], [5, 6], [5, 7], [6, 6]], 'mirrored':
        [False]}, {'file': 'shachikutrain-technique.json', 'board': 'cross_source.harddrop.drawings[20]',
        'cells': [[4, 5], [4, 6], [4, 7], [5, 6]], 'mirrored': [False]}, {'file':
        'shachikutrain-technique.json', 'board': 'cross_source.harddrop.drawings[21]', 'cells': [[3, 5], [3,
        6], [3, 7], [4, 6]], 'mirrored': [False]}, {'file': 'shachikutrain-technique.json', 'board':
        'cross_source.harddrop.drawn_t_not_fired[9]', 'cells': [[2, 3], [2, 4], [2, 5], [3, 4]], 'mirrored':
        [False]}],
    'fires_on_kaidan': [{'file': 'imperialcross-technique.json', 'variant': 'imperialcross', 'board': 'harddrop_anchor_set #19',
        'cells': [[4, 2], [5, 1], [5, 2], [6, 2]], 'mirrored': [True]}, {'file': 'parapet-technique.json',
        'variant': 'parapet', 'board': 'harddrop_anchor_set #23', 'cells': [[2, 1], [2, 2], [2, 3], [3, 2]],
        'mirrored': [False]}, {'file': 'parapet-technique.json', 'variant': 'parapet_tss', 'board':
        'harddrop_anchor_set #23', 'cells': [[1, 2], [2, 2], [2, 3], [3, 2]], 'mirrored': [False]}, {'file':
        'shachikutrain-technique.json', 'variant': 'shachikutrain', 'board': 'harddrop #15', 'cells': [[2,
        3], [2, 4], [2, 5], [3, 4]], 'mirrored': [False]}, {'file': 'shachikutrain-technique.json',
        'variant': 'shachikutrain', 'board': 'harddrop #14', 'cells': [[2, 3], [2, 4], [2, 5], [3, 4]],
        'mirrored': [False]}, {'file': 'stsd-technique.json', 'variant': 'stsd', 'board':
        'harddrop_anchor_set #20', 'cells': [[3, 1], [4, 1], [4, 2], [5, 1]], 'mirrored': [True]}],
    #: anchored on the same flat T, in the same hand: the cells both windows read (the T aside) and where they clash
    'shachikutrain_relation': {'as_drawn': {'shared': 16, 'clash': []}, 'mirrored': {'shared': 16, 'clash': []}},
}

CROSS_SOURCE = {
    'kind': 'routes',
    'label_pattern': 'kaidan',
    'note': 'the window, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot board of every '
            'committed *-routes.json, with the U cells as the T: it fires on none, and no node is labelled 階段 or Kaidan. '
            'The independent drawer is harddrop instead: its Kaidan_Setups and Anchor_Set pages and the Kaidan its '
            'BT_Cannon page draws, whose drawings are the window\'s external `agreement` drawings (rule (g) fires the '
            'window on each, once, at its drawn T, in its recorded hand).',
    'routes_fire_none': 'no committed routes file draws a Kaidan (measured: the window fires on none of their U-slot '
                        'boards at any resting placement, and no node is labelled 階段 or Kaidan); the cross-check is '
                        'harddrop\'s own pages, read below',
    'harddrop': HARDDROP,
    'harddrop_anchor_set': HARDDROP_ANCHOR_SET,
    'bt_cannon': BT_CANNON,
    'stmb_cave_kaidan': STMB_CAVE_KAIDAN,
    #: every other committed technique window against this page's drawings, and this window against theirs:
    #: measured, complete both ways (`other:`)
    'other_windows': OTHER_WINDOWS,
    'fires': [],
    'also': [],
    'labelled_not_fired': [],
}

KNOWN_DISCREPANCIES: list[dict] = []

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'kaidan',
        'source': SOURCE,
        'terms': TERMS,
        'legend': LEGEND,
        'cell_images': CELL_IMAGES,
        'empty_letters': '',
        'quotes': QUOTES,
        'nodes': NODES,
        'page_order': PAGE_ORDER,
        'basic_form': [],
        'variants': VARIANTS,
        'cross_source': CROSS_SOURCE,
        'known_discrepancies': KNOWN_DISCREPANCIES,
    }


# ── the harddrop reading ─────────────────────────────────────────────────────────────────────────
def special(code: str) -> bool:
    """A code `kd_cell` reads with its own rule rather than by delegating to `hd_cell`."""
    c = code.strip()
    return c.isdigit() or c in ('--', 'P', 'SP') or c.startswith("'")


def kd_cell(code: str) -> str:
    """One harddrop cell code in this file's reading of it (`READING`)."""
    c = code.strip()
    if c in ('', '-', '--'):
        return EMPTY
    if c.isdigit():
        return 'g'
    if c in ('P', 'SP'):
        return 'U'
    if c.startswith("'"):
        return 'v'
    return hd_cell(c)


def _pre(rows: list[str]) -> list[str]:
    """A harddrop board as the board before its drawn T (and before its ghost piece): `U` and `v` read empty."""
    return [row.replace('U', EMPTY).replace('v', EMPTY) for row in rows]


def _var(data: dict) -> dict:
    return data['variants'][0]


def _hands(data: dict, rows: list[str], slot) -> list[bool]:
    return [m for m in (False, True) if TT.window_fires(data, _var(data), SPEC, _pre(rows), {tuple(x) for x in slot}, m)]


def _fires_anywhere(data: dict, rows: list[str]) -> list[tuple]:
    pre = _pre(rows)
    return [([list(x) for x in sorted(cs)], m) for cs in TT.t_placements(pre, SPEC) for m in (False, True)
            if TT.window_fires(data, _var(data), SPEC, pre, cs, m)]


def t_lie(data: dict, rows: list[str], slot) -> tuple[str, int, str]:
    """What one drawn T on a harddrop board is, measured: its lie (`stood`, `flat-down` — the window's T — or
    `flat-up`), the rows it fills as drawn, and why the window does not fire at it: the T is not the window's, the
    window leaves the board in both hands, or a window cell disagrees (`fires` if it fires after all)."""
    rs = sorted({r for r, _ in slot})
    lie = 'stood' if len(rs) == 3 else ('flat-down' if sum(1 for r, _ in slot if r == rs[0]) == 3 else 'flat-up')
    lines = sum(1 for r in rs if EMPTY not in rows[r])
    if _hands(data, rows, slot):
        return lie, lines, 'fires'
    if lie != 'flat-down':
        return lie, lines, "not the window's T"
    v, lock = _var(data), {tuple(x) for x in slot}
    off = []
    for m in (False, True):
        W = TT.window_cells(data, v, SPEC, m)
        D = {k for k, x in W.items() if x == 'T'}
        dr = min(r for r, _ in lock) - min(r for r, _ in D)
        dc = min(c for _, c in lock) - min(c for _, c in D)
        off.append(any(not (0 <= r + dr < len(rows) and 0 <= c + dc < WIDTH) for r, c in W))
    return lie, lines, 'leaves the board' if all(off) else 'disagrees'


def bt_record(data: dict) -> dict:
    return json.loads((TECHNIQUE_DIR / data['cross_source']['bt_cannon']['file']).read_text())['cross_source']['harddrop']


def bt_drawing(data: dict | None = None) -> dict:
    """The Kaidan harddrop's BT_Cannon page draws, read out of `btcannon-technique.json` by (table, board)."""
    data = data or build()
    bc = data['cross_source']['bt_cannon']
    rec = bt_record(data)
    e = [x for x in rec.get(bc['list'], []) if (x['table'], x['board']) == (bc['table'], bc['board'])]
    if len(e) != 1:
        raise ValueError(f'{bc["file"]} records {len(e)} boards at table {bc["table"]} board {bc["board"]} in {bc["list"]}')
    slot = hd_slots(e[0]['rows'])
    if len(slot) != 1:
        raise ValueError(f'{bc["file"]} table {bc["table"]} board {bc["board"]} does not draw one T')
    return {'name': f'harddrop BT_Cannon table {bc["table"]} board {bc["board"]} (read from {bc["file"]})',
            'rows': _pre(e[0]['rows']), 't_cells': slot[0], 'mirrored': bc['mirrored'], 'record': e[0]}


def harddrop_drawings(data: dict | None = None) -> list[dict]:
    """The two harddrop pages' drawings as agreement drawings: the slot is the drawn T, every drawn T read empty."""
    data = data or build()
    xs = data['cross_source']
    out = []
    for key, title in (('harddrop', 'Kaidan_Setups'), ('harddrop_anchor_set', 'Anchor_Set')):
        for d in xs[key]['drawings']:
            out.append({'name': f'harddrop {title} #{d["n"]} (table {d["table"]} board {d["board"]}, {d["section"]})',
                        'rows': _pre(d['rows']), 't_cells': d['slot'], 'mirrored': d['mirrored']})
    return out


def external_drawings() -> list[dict]:
    d = bt_drawing()
    return harddrop_drawings() + [{k: d[k] for k in ('name', 'rows', 't_cells', 'mirrored')}]


# ── the harddrop pages, read ─────────────────────────────────────────────────────────────────────
def _page_boards(text: str) -> tuple[dict, list, list, list]:
    """(table, board) -> rows in kd reading; the heading per table; the board count per table; every
    [table, board, row, col, code] of the page."""
    tables = RT.wikitext_tables(text)
    secs = _sections(text)
    if len(secs) != len(tables):
        raise ValueError(f'{len(tables)} tables but {len(secs)} table openings')
    boards, cells = {}, []
    for i, t in enumerate(tables):
        for j, b in enumerate(t):
            boards[(i, j)] = [''.join(kd_cell(c) for c in row) for row in b]
            cells += [[i, j, r, c, code.strip()] for r, row in enumerate(b) for c, code in enumerate(row)]
    return boards, secs, [len(t) for t in tables], cells


def _special_cells(cells: list) -> dict:
    out: dict = {}
    for i, j, r, c, code in cells:
        if special(code):
            out.setdefault(code, []).append([i, j, r, c])
    return {k: sorted(v) for k, v in sorted(out.items())}


def page_problems(data: dict, key: str, text: str) -> list[str]:
    """One harddrop page against its record: each recorded board letter for letter at its (table, board) under its
    heading, numbered in page order; the board counts and the special cells as recorded; `kd_cell` against
    `hd_cell` on every code (`reading:`); and the record COMPLETE both ways — `drawings` exactly the drawn T's the
    window fires at (either hand), `drawn_t_not_fired` exactly every other drawn T, `fires_without_slot` exactly the
    boards with no T drawn on which it fires."""
    rec = data['cross_source'][key]
    tag = 'harddrop'
    try:
        boards, secs, counts, cells = _page_boards(text)
    except ValueError as e:
        return [f'{tag}: {key}: the wikitext does not parse: {e}']
    bad = []
    if counts != rec['board_counts']:
        bad.append(f'{tag}: {key}: the page\'s board counts per table are {counts}, not the recorded ones')
    order = {k: n for n, k in enumerate(sorted(boards))}
    recorded = rec['drawings'] + rec['drawn_t_not_fired'] + rec['fires_without_slot'] + (
        [rec['payoff_drawing']] if 'payoff_drawing' in rec else [])
    for d in recorded:
        k = (d['table'], d['board'])
        if boards.get(k) != d['rows']:
            bad.append(f'{tag}: {key}: table {k[0]} board {k[1]} is not the recorded drawing (page {boards.get(k)})')
        elif secs[k[0]] != d['section'] or order.get(k) != d['n']:
            bad.append(f'{tag}: {key}: table {k[0]} board {k[1]} is #{order.get(k)} under {secs[k[0]]!r}, not '
                       f'#{d["n"]} under {d["section"]!r}')
    # reading: the two readers agree on occupancy everywhere and on the letter wherever kd_cell delegates
    for i, j, r, c, code in cells:
        a, h = kd_cell(code), hd_cell(code)
        if (a == EMPTY) != (h == EMPTY):
            bad.append(f'reading: {key}: code {code!r} at table {i} board {j} is {a!r} here and {h!r} in hd_cell')
            break
        if not special(code) and a != h:
            bad.append(f'reading: {key}: code {code!r} is read {a!r} here and {h!r} by hd_cell, and is no special code')
            break
    if _special_cells(cells) != rec['special_cells']:
        bad.append(f'reading: {key}: the page\'s special cells are not the recorded ones')
    fired, missed, unslotted = [], [], []
    for (i, j), rows in sorted(boards.items()):
        try:
            slots = hd_slots(rows)
        except ValueError as e:
            bad.append(f'{tag}: {key}: table {i} board {j}: {e}')
            continue
        for s in slots:
            hands = _hands(data, rows, s)
            (fired if hands else missed).append((i, j, str(s), hands) if hands else (i, j, str(s)))
        if not slots and _fires_anywhere(data, rows):
            unslotted.append((i, j))
    want = sorted((d['table'], d['board'], str(d['slot']), [d['mirrored']]) for d in rec['drawings'])
    if sorted(fired) != want:
        bad.append(f'{tag}: {key}: the window fires at the drawn T of {sorted(fired)}, the record holds {want}')
    named = sorted((e['table'], e['board'], str(e['slot'])) for e in rec['drawn_t_not_fired'])
    if sorted(missed) != named:
        bad.append(f'{tag}: {key}: the window misses the drawn T of {sorted(missed)}, drawn_t_not_fired names {named}')
    if sorted(unslotted) != sorted((e['table'], e['board']) for e in rec['fires_without_slot']):
        bad.append(f'{tag}: {key}: with no T drawn the window fires on {unslotted}, the record names '
                   f'{[(e["table"], e["board"]) for e in rec["fires_without_slot"]]}')
    if 'quote' in rec and re.sub(r'\s+', ' ', rec['quote']) not in re.sub(r'\s+', ' ', text):
        bad.append(f'{tag}: {key}: the recorded quote is not on the page')
    return bad


def stmb_page_problems(data: dict, text: str) -> list[str]:
    """harddrop STMB_Cave's last table against the record (the revision 社畜トレイン pins): the board letter for letter
    and the table's caption."""
    sk = data['cross_source']['stmb_cave_kaidan']
    try:
        tables = RT.wikitext_tables(text)
    except ValueError as e:
        return [f'stmb: the wikitext does not parse: {e}']
    bad = []
    rows = None
    if sk['table'] < len(tables) and sk['board'] < len(tables[sk['table']]):
        rows = [''.join(kd_cell(c) for c in row) for row in tables[sk['table']][sk['board']]]
    if rows != sk['rows']:
        bad.append(f'stmb: STMB_Cave table {sk["table"]} board {sk["board"]} is not the recorded Kaidan (page {rows})')
    if sk['table'] != len(tables) - 1:
        bad.append(f'stmb: table {sk["table"]} is not the STMB_Cave page\'s last table ({len(tables)} tables)')
    opens = [m.start() for m in re.finditer(r'^\{\|', text, re.M)]
    seg = text[opens[sk['table']]:text.find('|}', opens[sk['table']])] if sk['table'] < len(opens) else ''
    if sk['caption'] not in seg:
        bad.append(f'stmb: table {sk["table"]} does not carry the recorded caption')
    return bad


def _snapshot(rec: dict, html_dir: Path, tag: str) -> tuple[list[str], str | None]:
    p = Path(html_dir) / rec['snapshot_file']
    if not p.exists():
        return [f'{tag}: {rec["snapshot_file"]} is not in {html_dir} — fetch it beside the page'], None
    raw = p.read_bytes()
    bad = []
    if hashlib.sha256(raw).hexdigest() != rec['snapshot_sha256'] or len(raw) != rec['snapshot_bytes']:
        bad.append(f'{tag}: hash: sha256/bytes {hashlib.sha256(raw).hexdigest()} / {len(raw)} are not the recorded ones')
    if hashlib.sha1(raw).hexdigest() != rec['revision_sha1']:
        bad.append(f'{tag}: hash: sha1 {hashlib.sha1(raw).hexdigest()} is not MediaWiki\'s revision sha1')
    return bad, raw.decode('utf8')


def harddrop_snapshot_checks(data: dict, html_dir: Path) -> list[str]:
    """`--wikitext-dir` (and the harddrop half of `--html-dir`): the two pinned revisions this file records (a missing
    file is a failure)."""
    bad = []
    for key, tag in (('harddrop', 'harddrop'), ('harddrop_anchor_set', 'anchor')):
        b, text = _snapshot(data['cross_source'][key], html_dir, tag)
        bad += b
        if text is not None:
            bad += page_problems(data, key, text)
    return bad


def snapshot_checks(data: dict, html_dir: Path) -> list[str]:
    """`--html-dir`: the two pinned revisions, and STMB_Cave's (pinned by 社畜トレイン, read here by its hashes there)."""
    bad = harddrop_snapshot_checks(data, html_dir)
    pin = json.loads((TECHNIQUE_DIR / SHACHIKU_FILE).read_text())['cross_source']['stmb_cave']
    b, text = _snapshot(pin, html_dir, 'stmb')
    bad += b
    if text is not None:
        bad += stmb_page_problems(data, text)
    return bad


# ── technique-only rules ─────────────────────────────────────────────────────────────────────────
def _other(path: Path) -> tuple[dict, TT.TechniqueSpec]:
    other = json.loads(path.read_text())
    return other, TT.TechniqueSpec(out=path, build=lambda: other, alphabet=frozenset(),
                                   empty_letters=other.get('empty_letters', ''), max_rows=99)


def _walk_boards(o, path: str, out: list) -> None:
    """Every board a transcription's `cross_source` holds: a dict with ten-wide string `rows`."""
    if isinstance(o, dict):
        rows = o.get('rows')
        if isinstance(rows, list) and rows and all(isinstance(r, str) and len(r) == WIDTH for r in rows):
            out.append((path, o))
        for k, v in o.items():
            _walk_boards(v, f'{path}.{k}', out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            _walk_boards(v, f'{path}[{i}]', out)


def other_boards(other: dict, ospec: TT.TechniqueSpec) -> list[tuple[str, list[str]]]:
    """Every board of another technique transcription, as the board before its drawn piece: its nodes (a spin board
    with its spin cells read empty, any `U` empty) and every board its `cross_source` records (`U`, `v` and the
    image and fumen readings' `.` read empty)."""
    out = []
    for n in other['nodes']:
        sc = TT.spin_cells(n) if n['kind'] == 'spin' else set()
        out.append((f'nodes.{n["id"]}', [''.join(EMPTY if (r, c) in sc or ch == 'U' else ch for c, ch in enumerate(row))
                                         for r, row in enumerate(n['rows'])]))
    found: list = []
    _walk_boards(other.get('cross_source', {}), 'cross_source', found)
    for path, o in found:
        out.append((path, [''.join(EMPTY if ch in 'Uv.' else ch for ch in row) for row in o['rows']]))
    return out


def kaidan_fires_on(data: dict) -> list[dict]:
    """This window over every board of every other committed technique transcription, at every resting placement."""
    got = []
    for f in sorted(TECHNIQUE_DIR.glob('*-technique.json')):
        if f.name == OUT.name:
            continue
        other, ospec = _other(f)
        for path, rows in other_boards(other, ospec):
            for cs in TT.t_placements(rows, ospec):
                hands = [m for m in (False, True) if TT.window_fires(data, _var(data), ospec, rows, cs, m)]
                if hands:
                    got.append({'file': f.name, 'board': path, 'cells': sorted([r, c] for r, c in cs),
                                'mirrored': hands})
    return got


def kaidan_drawings(data: dict) -> list[tuple[str, list[str]]]:
    """Every drawing this transcription holds, as the board before its T: its nodes (spin cells empty) and both
    harddrop pages' recorded boards."""
    out = []
    for n in data['nodes']:
        sc = TT.spin_cells(n) if n['kind'] == 'spin' else set()
        out.append((f'nodes.{n["id"]}', [''.join(EMPTY if (r, c) in sc or ch == 'U' else ch for c, ch in enumerate(row))
                                         for r, row in enumerate(n['rows'])]))
    for key in ('harddrop', 'harddrop_anchor_set'):
        rec = data['cross_source'].get(key)
        if rec is None:
            continue    # the `harddrop:` rule reports the missing record
        for lst in ('drawings', 'drawn_t_not_fired', 'fires_without_slot'):
            for d in rec[lst]:
                out.append((f'{key} #{d["n"]}', _pre(d['rows'])))
        if 'payoff_drawing' in rec:
            out.append((f'{key} #{rec["payoff_drawing"]["n"]}', _pre(rec['payoff_drawing']['rows'])))
    return out


def fires_on_kaidan(data: dict) -> list[dict]:
    """Every other committed technique window (each variant) over every drawing this transcription holds."""
    got = []
    mine = kaidan_drawings(data)
    for f in sorted(TECHNIQUE_DIR.glob('*-technique.json')):
        if f.name == OUT.name:
            continue
        other, ospec = _other(f)
        for v in other['variants']:
            for name, rows in mine:
                for cs in TT.t_placements(rows, ospec):
                    hands = [m for m in (False, True) if TT.window_fires(other, v, ospec, rows, cs, m)]
                    if hands:
                        got.append({'file': f.name, 'variant': v['id'], 'board': name,
                                    'cells': sorted([r, c] for r, c in cs), 'mirrored': hands})
    return got


def _norm_window(d: dict, v: dict, spec: TT.TechniqueSpec, m: bool) -> dict:
    W = TT.window_cells(d, v, spec, m)
    T = [k for k, x in W.items() if x == 'T']
    r0, c0 = min(r for r, _ in T), min(c for _, c in T)
    return {(r - r0, c - c0): x for (r, c), x in W.items()}


def shachikutrain_relation(data: dict) -> dict:
    """This window against 社畜トレイン's, anchored on the same flat T in the same hand: how many cells both read and
    where they clash (offsets from the T's top-left), per hand."""
    other, ospec = _other(TECHNIQUE_DIR / SHACHIKU_FILE)
    out = {}
    for m, name in ((False, 'as_drawn'), (True, 'mirrored')):
        a = _norm_window(data, _var(data), SPEC, m)
        b = _norm_window(other, other['variants'][0], ospec, m)
        both = [k for k in a if k in b and 'T' not in (a[k], b[k])]
        out[name] = {'shared': len(both), 'clash': sorted([r, c] for r, c in both if a[(r, c)] != b[(r, c)])}
    return out


def extra_checks(data: dict):
    bad, measured = [], set()
    by = {n['id']: n for n in data['nodes']}
    v = _var(data)
    xs = data['cross_source']
    # listed: every drawn board is in fires_on, fires_mirrored or misses, is the variant's board, or is a DT砲 spin
    # board whose board-before is in fires_mirrored
    dt_spins = [n['id'] for n in data['nodes'] if n['kind'] == 'spin' and n.get('spin_of') in v.get('fires_mirrored', [])]
    listed = set(v.get('fires_on', [])) | set(v.get('fires_mirrored', [])) | set(v.get('misses', [])) | {v['board']}
    for n in data['nodes']:
        if n['id'] not in listed | set(dt_spins):
            bad.append(f'listed: board {n["id"]} is in none of fires_on, fires_mirrored, misses')
    want = sorted([(b, False) for b in v.get('fires_on', [])] + [(b, True) for b in v.get('fires_mirrored', [])])
    if sorted((a['board'], a['mirrored']) for a in v.get('agreement', [])) != want:
        bad.append('listed: the page\'s agreement drawings are not fires_on (as drawn) and fires_mirrored (mirrored)')
    # dt: each DT砲 board's drawn U is one T clearing two rows (the spin rule), its board-before is its derived board,
    # and the window fires on that board once, MIRRORED, exactly at the drawn U
    if len(dt_spins) != 2:
        bad.append(f'dt: {len(dt_spins)} DT砲 spin boards on fires_mirrored boards, not the page\'s two')
    for sid in dt_spins:
        n = by[sid]
        u = sorted([r, c] for r, row in enumerate(n['rows']) for c, ch in enumerate(row) if ch == 'U')
        pre = by[n['spin_of']]['rows']
        if n.get('spin_piece') != 'U' or n.get('on') != n['spin_of'] or n.get('adds') != 'U':
            bad.append(f'dt: {sid} is not a U spin board on its derived board-before')
        hits = [(sorted([r, c] for r, c in cs), m) for cs in TT.t_placements(pre, SPEC) for m in (False, True)
                if TT.window_fires(data, v, SPEC, pre, cs, m)]
        if hits != [(u, True)]:
            bad.append(f'dt: the window fires {hits} on {n["spin_of"]}, not once, mirrored, at {sid}\'s drawn U {u}')
        ag = next((a for a in v['agreement'] if a['board'] == n['spin_of']), None)
        if ag is None or sorted(ag['t_cells']) != u or not ag['mirrored']:
            bad.append(f'dt: {n["spin_of"]}\'s agreement slot is not {sid}\'s drawn U, mirrored')
        fr = TT.full_rows(TT.occ_of(n['rows'], SPEC))
        up = sorted({r for r, row in enumerate(n['rows']) for ch in row if ch.isupper()})
        if fr != up:
            bad.append(f'dt: {sid}\'s upper-case rows {up} are not its full rows {fr}')
    # illus: the 打後 boards' upper case is an earlier stack drawn muted, not cleared rows: no row holding it is full;
    # and the stood T the second draws is not this window's T (the window fires nowhere on either)
    for n in data['nodes']:
        if n['kind'] != 'illustration':
            continue
        up = {r for r, row in enumerate(n['rows']) if any(ch.isupper() for ch in row)}
        if not up or up & set(TT.full_rows(TT.occ_of(n['rows'], SPEC))):
            bad.append(f'illus: {n["id"]} draws a muted cell in a full row, or draws none')
        t = {(r, c) for r, row in enumerate(n['rows']) for c, ch in enumerate(row) if ch == 't'}
        if t:
            pre = [''.join(EMPTY if (r, c) in t else ch for c, ch in enumerate(row)) for r, row in enumerate(n['rows'])]
            ys = {(c, len(n['rows']) - 1 - r) for r, c in t}
            if RT._norm(ys) not in RT._shapes('t') or any(TT.window_fires(data, v, SPEC, pre, t, m) for m in (False, True)):
                bad.append(f'illus: {n["id"]}\'s t is no T, or is this window\'s T')
    # harddrop: every recorded entry is a ten-wide board; its slot one of its drawn T's; measured on the DATA (the
    # agreement rule reads the pristine build through the spec)
    for key in ('harddrop', 'harddrop_anchor_set'):
        rec = xs.get(key)
        if not rec:
            bad.append(f'harddrop: no {key} record')
            continue
        seen = set()
        for d in rec.get('drawings', []):
            k = (d['table'], d['board'], str(d['slot']))
            try:
                slots = hd_slots(d['rows'])
            except ValueError as e:
                bad.append(f'harddrop: {key} #{d["n"]}: {e}')
                continue
            if any(len(r) != WIDTH for r in d['rows']) or d['slot'] not in slots:
                bad.append(f'harddrop: {key} #{d["n"]} is not a ten-wide board drawing its slot as a T')
                continue
            hits = [(frozenset(map(tuple, cs)), m) for cs, m in _fires_anywhere(data, d['rows'])]
            if hits != [(frozenset(tuple(x) for x in d['slot']), d['mirrored'])]:
                bad.append(f'harddrop: the window fires {len(hits)} time(s) on {key} #{d["n"]}, not once at its drawn T '
                           f'({"mirrored" if d["mirrored"] else "as drawn"})')
            if k in seen:
                bad.append(f'harddrop: {key} #{d["n"]} recorded twice')
            seen.add(k)
        for d in rec.get('drawn_t_not_fired', []):
            k = (d['table'], d['board'], str(d['slot']))
            try:
                slots = hd_slots(d['rows'])
            except ValueError as e:
                bad.append(f'harddrop: {key} #{d["n"]}: {e}')
                continue
            if any(len(r) != WIDTH for r in d['rows']) or d['slot'] not in slots:
                bad.append(f'harddrop: {key} #{d["n"]} (drawn_t_not_fired) does not draw its slot as a T')
                continue
            got = t_lie(data, d['rows'], d['slot'])
            if got != (d['t'], d['lines'], d['window']) or got[2] == 'fires':
                bad.append(f'harddrop: {key} #{d["n"]} slot {d["slot"]} is {got}, drawn_t_not_fired records '
                           f'{(d["t"], d["lines"], d["window"])}')
            if not d.get('note', '').strip():
                bad.append(f'harddrop: {key} #{d["n"]} is in drawn_t_not_fired with no note')
            if k in seen:
                bad.append(f'harddrop: {key} #{d["n"]} slot {d["slot"]} recorded twice')
            seen.add(k)
        for d in rec.get('fires_without_slot', []):
            hits = _fires_anywhere(data, d['rows'])
            if any('U' in r for r in d['rows']) or hits != [(d['slot'], d['mirrored'])]:
                bad.append(f'harddrop: {key} #{d["n"]} draws a T, or the window does not fire on it once at {d["slot"]}')
    if not any(d['section'] == 'General Formation' for d in xs.get('harddrop', {}).get('drawings', [])):
        bad.append('harddrop: no recorded drawing from the Kaidan page\'s own General Formation section')
    # payoff: Anchor_Set's I into the re-opened column: its `v` cells are one vertical I in the recorded column and it
    # fills exactly four rows; the board sits beside the recorded Kaidan drawing in the same table
    pd = xs.get('harddrop_anchor_set', {}).get('payoff_drawing')
    if not pd:
        bad.append('payoff: no payoff_drawing (the drawing the payoff is attributed to is required, never defaulted)')
    else:
        g = [(r, c) for r, row in enumerate(pd['rows']) for c, ch in enumerate(row) if ch == 'v']
        o = TT.occ_of(_pre(pd['rows']), SPEC)
        full = TT.full_rows([''.join('#' if (r, c) in g else ch for c, ch in enumerate(row)) for r, row in enumerate(o)])
        rows = sorted(r for r, _ in g)
        if (len(g) != 4 or {c for _, c in g} != {pd['column']} or rows != list(range(rows[0], rows[0] + 4))
                or len(full) != pd['cleared']):
            bad.append(f'payoff: {pd["n"]}\'s ghost cells {g} are not one vertical I in column {pd["column"]} clearing '
                       f'{pd["cleared"]}')
        tb = [(d['table'], d['board']) for d in xs['harddrop_anchor_set']['drawings']]
        if (pd['table'], pd['board'] - 1) not in tb:
            bad.append(f'payoff: {pd["n"]} is not the board beside the recorded Kaidan drawing in its table')
    # bt: the Kaidan BT砲's record holds: its own note names a Kaidan
    bc = xs.get('bt_cannon')
    if not bc:
        bad.append('bt: no bt_cannon record')
    else:
        try:
            d = bt_drawing(data)
        except (OSError, ValueError, KeyError) as e:
            bad.append(f'bt: {e}')
        else:
            if 'kaidan' not in d['record'].get('note', '').lower():
                bad.append(f'bt: {bc["file"]} table {bc["table"]} board {bc["board"]}\'s own note does not name a Kaidan')
    # stmb: STMB_Cave's last table, pinned by 社畜トレイン (same oldid); the Kaidan there leaves the window, and its
    # caption is the sentence wiki-tspin-techniques.json quotes
    sk = xs.get('stmb_cave_kaidan')
    if not sk:
        bad.append('stmb: no stmb_cave_kaidan record')
    else:
        pin = json.loads((TECHNIQUE_DIR / SHACHIKU_FILE).read_text())['cross_source'].get('stmb_cave', {})
        if 'revision_sha1' in sk or 'oldid' in sk:
            bad.append('stmb: the STMB_Cave record re-pins a revision (社畜トレイン pins it)')
        if pin.get('page') != sk['page']:
            bad.append(f'stmb: {SHACHIKU_FILE}\'s stmb_cave record is not the STMB_Cave page')
        wiki = json.loads((HERE / WIKI_FILE).read_text())
        says = {s['technique']: s['says'] for s in wiki['stmb_cave']['confusable']['says']}
        if says.get('Kaidan', '') != sk['caption'].replace('[[', '').replace(']]', ''):
            bad.append(f'stmb: the recorded caption is not the sentence {WIKI_FILE} quotes for Kaidan')
        try:
            slots = hd_slots(sk['rows'])
        except ValueError as e:
            bad.append(f'stmb: {e}')
        else:
            if slots != [sk['slot']] or t_lie(data, sk['rows'], sk['slot']) != (sk['t'], sk['lines'], sk['window']):
                bad.append(f'stmb: the STMB_Cave Kaidan is {t_lie(data, sk["rows"], sk["slot"])}, the record holds '
                           f'{(sk["t"], sk["lines"], sk["window"])}')
    # other: every other technique window against this page's drawings, and this window against theirs: complete,
    # both ways; and the relation to 社畜トレイン's window, re-measured
    ow = xs.get('other_windows', {})
    key = lambda e: json.dumps(e, sort_keys=True)
    got = kaidan_fires_on(data)
    if sorted(map(key, got)) != sorted(map(key, ow.get('kaidan_fires_on', []))):
        bad.append(f'other: this window fires on the other transcriptions\' boards at {got}, the record holds '
                   f'{ow.get("kaidan_fires_on")}')
    got = fires_on_kaidan(data)
    if sorted(map(key, got)) != sorted(map(key, ow.get('fires_on_kaidan', []))):
        bad.append(f'other: the other windows fire on this transcription\'s drawings at {got}, the record holds '
                   f'{ow.get("fires_on_kaidan")}')
    try:
        rel = shachikutrain_relation(data)
    except (OSError, KeyError) as e:
        bad.append(f'other: {e!r}')
    else:
        if rel != ow.get('shachikutrain_relation'):
            bad.append(f'other: anchored on the same flat T, this window and 社畜トレイン\'s are {rel}, the record holds '
                       f'{ow.get("shachikutrain_relation")}')
    # cross: no routes node is labelled as this technique by its Japanese name either
    for f in sorted(HERE.glob('*-routes.json')):
        for n in json.loads(f.read_text())['nodes']:
            text = ' '.join(str(n.get(k, '')) for k in ('id', 'label', 'label_jp')).lower()
            if '階段' in text:
                bad.append(f'cross: {f.name} {n["id"]} is labelled as this technique')
    return bad, measured


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='',
    upper_groups={'T': 'merge', 'Z': 'merge', 'S': 'merge', 'J': 'merge', 'I': 'merge', 'O': 'merge', 'L': 'merge'},
    max_rows=9,
    extra_checks=extra_checks,
    external_drawings=external_drawings,
    html_checks=snapshot_checks,
    # the two pinned revisions alone: what a weekly api.php refetch can supply
    wikitext_checks=harddrop_snapshot_checks,
)


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def _raw_code(ch: str) -> str:
    return {EMPTY: ' ', 'U': 'P', 'v': "'I", 'g': 'G'}.get(ch, ch.upper())


def synthetic_page(data: dict, key: str) -> str:
    """A faithful stand-in for a harddrop page CI cannot fetch: every recorded board at its (table, board) under its
    heading, every other board blank, the special cells' codes in place, and the quote."""
    rec = data['cross_source'][key]
    boards = {}
    sections = {}
    for d in rec['drawings'] + rec['drawn_t_not_fired'] + rec['fires_without_slot'] + (
            [rec['payoff_drawing']] if 'payoff_drawing' in rec else []):
        boards[(d['table'], d['board'])] = [[_raw_code(ch) for ch in row] for row in d['rows']]
        sections[d['table']] = d['section']
    for code, cells in rec['special_cells'].items():
        for t, b, r, c in cells:
            bd = boards.setdefault((t, b), [])
            while len(bd) <= r:
                bd.append([' '] * WIDTH)
            bd[r][c] = code
    out, last = [], None
    for i, n in enumerate(rec['board_counts']):
        s = sections.get(i, last)
        if s != last:
            out.append(f'\n== {s} ==\n')
            last = s
        bs = []
        for j in range(n):
            rows = boards.get((i, j), [[' '] * WIDTH] * 4)
            bs.append('|{{pfstart}} ' + ' '.join('{{pfrow|' + '|'.join(r) + '}}' for r in rows) + ' {{pfend}}')
        out.append('{| ' + ' '.join(bs) + ' |}')
    if 'quote' in rec:
        out.append(rec['quote'])
    return '\n'.join(out)


def _synthetic_stmb(data: dict) -> str:
    sk = data['cross_source']['stmb_cave_kaidan']
    tables = [[[EMPTY * WIDTH] * 4] for _ in range(sk['table'])] + [[[EMPTY * WIDTH] * 4, sk['rows']]]
    w = '\n'.join(RT.synthetic_wikitext([t]) for t in tables)
    k = w.rfind('|}')
    return w[:k] + f'\n|+ {sk["caption"]}\n' + w[k:]


SPEC.synthetic_wikitext = lambda d: {d['cross_source'][k]['snapshot_file']: synthetic_page(d, k)
                                     for k in ('harddrop', 'harddrop_anchor_set')}


def _set(rows, r, c, ch):
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _hdr(d, key='harddrop'):
    return d['cross_source'][key]


def _rec(d, key, n):
    rec = d['cross_source'][key]
    return next(x for x in rec['drawings'] + rec['drawn_t_not_fired'] + rec['fires_without_slot'] if x['n'] == n)


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'basic.terrain')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: d['page_order'].reverse(), 'page_order swapped', 'grammar:'),
    (lambda d: node(d, 'basic.after').__setitem__('after_of', 'nowhere'), 'a dangling reference', 'grammar:'),
    (lambda d: _var(d).__setitem__('followup', {'board': 'basic.after'}), 'a variant with a follow-up and a payoff',
     'grammar:'),
    (lambda d: _set(node(d, 'basic.o')['rows'], 4, 0, '-'), 'a build board cell flipped', 'build:'),
    (lambda d: _set(node(d, 'j3.terrain')['rows'], 3, 5, 'c'), 'the J form\'s hole filled in its terrain', 'build:'),
    (lambda d: _set(node(d, 'dt.anchor.pre')['rows'], 8, 9, '-'), 'a DT砲 board-before edited', 'build:'),
    (lambda d: (_set(node(d, 'basic.spin')['rows'], 3, 7, 'C'), _set(node(d, 'basic.spin')['rows'], 1, 7, 'T')),
     'the T pointing up', 'spin:'),
    (lambda d: _set(node(d, 'basic.spin')['rows'], 2, 0, 'c'), 'a cleared row drawn unmuted', 'spin:'),
    (lambda d: node(d, 'dt.amemiya').__setitem__('lines', 3), 'a DT砲 TSD\'s line count', 'spin:'),
    (lambda d: _set(node(d, 'basic.after')['rows'], 0, 0, 'c'), 'the after board not what the TSD leaves',
     'discrepancy:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [4, 9]), 'the window widened by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [2, 5]), 'the window without its roof row (another maximal box)',
     'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [1, 4]), 'the window without its second well row', 'window:'),
    (lambda d: _var(d)['roof_cells'].pop(), 'a roof cell unnamed', 'window:'),
    (lambda d: _var(d)['untested_drawn']['cells'].pop(), 'the O\'s top row left unnamed', 'window:'),
    (lambda d: _var(d)['agreement'][3].__setitem__('mirrored', False), 'あめみや砲 read as drawn', 'window:'),
    (lambda d: _var(d)['agreement'][1].__setitem__('t_cells', [[2, 5], [2, 6], [2, 7], [3, 6]]),
     'a slot moved one column', 'window:'),
    (lambda d: _var(d)['payoff'].__setitem__('well_cell_pre_clear', [4, 8]), 'the well read under the Z\'s foot',
     'window:'),
    (lambda d: _var(d)['payoff'].__setitem__('well_cell_after', [2, 9]), 'the well cell mapped wrongly', 'window:'),
    (lambda d: _var(d)['payoff'].__setitem__('lines', 3), 'the payoff read as a triple', 'window:'),
    (lambda d: _set(node(d, 'basic.after')['rows'], 6, 9, 'c'), 'the well column not open on the after board',
     'window:'),
    (lambda d: _var(d)['misses'].append('basic.o'), 'a board it fires on listed as a miss', 'window:'),
    (lambda d: _var(d)['fires_on'].append('dt.anchor.pre'), 'a mirrored drawing listed as firing as drawn', 'window:'),
    (lambda d: _var(d)['misses'].remove('after.2'), 'a drawn board in no list', 'listed:'),
    (lambda d: _var(d)['fires_mirrored'].remove('dt.anchor.pre'), 'a DT砲 drawing in no list', 'listed:'),
    (lambda d: node(d, 'dt.anchor').__setitem__('on', 'dt.amemiya.pre'), 'a DT砲 board on the other\'s board-before',
     'dt:'),
    (lambda d: _var(d)['agreement'][4].__setitem__('t_cells', [[3, 2], [3, 3], [3, 4], [4, 3]]),
     'a DT砲 slot not its drawn U', 'dt:'),
    (lambda d: (_set(node(d, 'after.1')['rows'], 1, 6, 'c'), _set(node(d, 'after.1')['rows'], 1, 7, 'c'),
                _set(node(d, 'after.1')['rows'], 1, 8, 'c')), 'an 打後 board drawing a full row', 'illus:'),
    (lambda d: _hdr(d)['drawings'][0].__setitem__('mirrored', True), 'a harddrop drawing read mirrored', 'harddrop:'),
    (lambda d: _set(_hdr(d)['drawings'][2]['rows'], 1, 3, '-'), 'harddrop #15\'s L roof dropped', 'harddrop:'),
    (lambda d: _hdr(d)['drawings'][1].__setitem__('slot', [[3, 5], [3, 6], [3, 7], [4, 6]]), 'a harddrop slot moved',
     'harddrop:'),
    (lambda d: [x.__setitem__('section', TR) for x in _hdr(d)['drawings']], 'the general formation dropped', 'harddrop:'),
    (lambda d: _hdr(d)['drawings'].append(copy.deepcopy(_hdr(d)['drawings'][0])), 'a harddrop drawing twice',
     'harddrop:'),
    (lambda d: _rec(d, 'harddrop', 83).__setitem__('t', 'flat-down'), 'a missed drawn T\'s lie misrecorded',
     'harddrop:'),
    (lambda d: _rec(d, 'harddrop', 74).__setitem__('window', 'leaves the board'), 'why the window misses misrecorded',
     'harddrop:'),
    (lambda d: _rec(d, 'harddrop', 86).__setitem__('lines', 2), 'a missed T\'s line count misrecorded', 'harddrop:'),
    (lambda d: _rec(d, 'harddrop', 88).__setitem__('note', ''), 'a missed drawn T with no note', 'harddrop:'),
    (lambda d: _rec(d, 'harddrop', 78).__setitem__('mirrored', True), 'a no-T board read as firing mirrored',
     'harddrop:'),
    (lambda d: _rec(d, 'harddrop_anchor_set', 21).__setitem__('mirrored', False), 'Anchor_Set\'s Kaidan read as drawn',
     'harddrop:'),
    (lambda d: d['cross_source'].pop('harddrop_anchor_set'), 'no Anchor_Set record', 'harddrop:'),
    (lambda d: _hdr(d, 'harddrop_anchor_set')['payoff_drawing'].__setitem__('cleared', 3), 'the Tetris read as a triple',
     'payoff:'),
    (lambda d: _set(_hdr(d, 'harddrop_anchor_set')['payoff_drawing']['rows'], 4, 0, 'g'), 'the ghost I three cells',
     'payoff:'),
    (lambda d: _hdr(d, 'harddrop_anchor_set')['payoff_drawing'].__setitem__('board', 0),
     'the payoff drawing beside no recorded Kaidan', 'payoff:'),
    (lambda d: _hdr(d, 'harddrop_anchor_set').pop('payoff_drawing'), 'no payoff drawing', 'payoff:'),
    (lambda d: d['cross_source']['bt_cannon'].__setitem__('board', 1), 'the BT_Cannon board misnamed', 'bt:'),
    (lambda d: d['cross_source'].pop('bt_cannon'), 'no BT_Cannon record', 'bt:'),
    (lambda d: d['cross_source']['stmb_cave_kaidan'].__setitem__('window', 'disagrees'),
     'the STMB_Cave Kaidan\'s miss misrecorded', 'stmb:'),
    (lambda d: d['cross_source']['stmb_cave_kaidan'].__setitem__('oldid', 41496), 'the STMB_Cave revision re-pinned',
     'stmb:'),
    (lambda d: d['cross_source']['stmb_cave_kaidan'].__setitem__('caption', 'Compare this.'),
     'the caption not the quoted one', 'stmb:'),
    (lambda d: d['cross_source']['other_windows']['kaidan_fires_on'].pop(), 'a board this window fires on unrecorded',
     'other:'),
    (lambda d: d['cross_source']['other_windows']['fires_on_kaidan'].pop(), 'another window on a Kaidan unrecorded',
     'other:'),
    (lambda d: d['cross_source']['other_windows']['shachikutrain_relation']['as_drawn'].__setitem__('clash', [[3, 1]]),
     'the 社畜トレイン relation read as a clash', 'other:'),
    (lambda d: d['cross_source'].pop('routes_fire_none'), 'no independent routes board and no reason', 'cross:'),
    (lambda d: node(d, 'dt.anchor').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['known_discrepancies'].append({'id': 'basic.z:colour', 'note': 'x'}), 'a stale discrepancy',
     'discrepancy:'),
    (lambda d: _set(node(d, 's3.s')['rows'], 1, 5, 'z'), 'a piece broken', 'discrepancy:'),
]


def _no_external(spec):
    s = copy.copy(spec)
    s.external_drawings = None
    return s


def _line_clear_base_as_drawing(spec):
    """harddrop #74 (the Line Clear Base, the hole under the T's right arm) read as a drawing of the shape."""
    s = copy.copy(spec)
    d = next(x for x in build()['cross_source']['harddrop']['drawn_t_not_fired'] if x['n'] == 74)
    s.external_drawings = lambda: external_drawings() + [{'name': 'harddrop #74 as a drawing', 'rows': _pre(d['rows']),
                                                          't_cells': d['slot'], 'mirrored': False}]
    return s


SPEC_MUTANTS = [
    (_no_external, 'no external drawing (the window checked against this page alone)', 'window:'),
    (_line_clear_base_as_drawing, 'harddrop\'s Line Clear Base read as a drawing of the shape', 'window:'),
]


def _other_plant_problems(planted: bool) -> list[str]:
    """The `other:` rule run with TECHNIQUE_DIR pointed at a temporary directory holding the transcriptions it reads by
    name and one more: planted, a node that is this page's own build board (the window must fire on it); not
    planted, the same file with that board emptied (a control: no new firing)."""
    global TECHNIQUE_DIR
    base = build()
    b = copy.deepcopy(node(base, 'basic.o'))
    b['id'] = 'planted'
    if not planted:
        b['rows'] = [EMPTY * len(r) for r in b['rows']]
    fake = {'nodes': [b], 'variants': [], 'empty_letters': ''}
    saved = TECHNIQUE_DIR
    with tempfile.TemporaryDirectory() as td:
        for f in saved.glob('*-technique.json'):
            if f.name != OUT.name:
                (Path(td) / f.name).write_text(f.read_text())
        (Path(td) / 'planted-technique.json').write_text(json.dumps(fake))
        TECHNIQUE_DIR = Path(td)
        try:
            bad, _measured = extra_checks(base)
        finally:
            TECHNIQUE_DIR = saved
    return [x for x in bad if x.startswith('other:')]


def selftest() -> int:
    rc = TT.run_selftest(SPEC, MUTANTS, {'board': ('CCCCCCTTTZ', 'CCCCCCTTTc'),
                                         'text': ('4段以上の階段', '5段以上の階段')}, SPEC_MUTANTS)
    ok = rc == 0
    base = build()
    pages = {k: synthetic_page(base, k) for k in ('harddrop', 'harddrop_anchor_set')}
    stext = _synthetic_stmb(base)
    clean = [x for k, t in pages.items() for x in page_problems(base, k, t)] + stmb_page_problems(base, stext)
    if clean:
        print(f'selftest FAILED: the synthetic harddrop pages do not verify ({clean[:2]})')
        ok = False
    hd, an = pages['harddrop'], pages['harddrop_anchor_set']
    row = lambda r: '{{pfrow|' + '|'.join(_raw_code(ch) for ch in r) + '}}'
    d2 = _rec(base, 'harddrop', 2)['rows']
    plants = {
        'a recorded drawing redrawn on the page': ('harddrop', hd.replace(row(d2[2]), row(d2[2][:-1] + 'g'), 1)),
        'a board the window fires on left unrecorded': ('harddrop', hd.replace('|}', '|{{pfstart}} ' + ' '.join(
            row(r) for r in d2) + ' {{pfend}} |}', 1)),
        'a heading renamed': ('harddrop', hd.replace('== General Formation ==', '== General Formations ==', 1)),
        'a no-T board the window fires on left unrecorded': ('harddrop', hd.replace('|}', '|{{pfstart}} ' + ' '.join(
            row(r) for r in _pre(d2)) + ' {{pfend}} |}', 1)),
        'a digit cell where none is recorded': ('harddrop', hd.replace('{{pfrow|', '{{pfrow|3|', 1).replace(
            '{{pfrow|3| |', '{{pfrow|3|', 1)),
        'the drawn T\'s SP skin written P': ('harddrop', hd.replace('|SP|', '|P|', 1)),
        'the quote edited': ('harddrop', hd.replace('Back-to-Back bonus', 'B2B bonus', 1)),
        'the payoff drawing\'s ghost I edited': ('harddrop_anchor_set', an.replace("|'I|", '| |', 1)),
        'a board count changed': ('harddrop_anchor_set', an.replace(' |}', ' |{{pfstart}} {{pfrowblank}} {{pfend}} |}', 1)),
    }
    for label, (key, page) in plants.items():
        got = page_problems(base, key, page)
        if page == pages[key] or not any(x.startswith(('harddrop:', 'reading:')) for x in got):
            print(f'selftest FAILED: {label} was not caught ({got[:2]})')
            ok = False
        else:
            print(f'  killed: {label}  [{got[0].split(":")[0]}:]')
    for label, (key, n) in (('a drawn T the window misses left out of the record', ('harddrop', 96)),
                            ('an Anchor_Set drawn T left out of the record', ('harddrop_anchor_set', 23))):
        unnamed = copy.deepcopy(base)
        rec = unnamed['cross_source'][key]
        rec['drawn_t_not_fired'] = [x for x in rec['drawn_t_not_fired'] if x['n'] != n]
        got = page_problems(unnamed, key, pages[key])
        if not any('drawn_t_not_fired names' in x for x in got):
            print(f'selftest FAILED: {label} was not caught ({got[:2]})')
            ok = False
        else:
            print(f'  killed: {label}  [harddrop:]')
    for label, page in (('the STMB_Cave Kaidan redrawn', stext.replace('{{pfrow|G|G|G|G|G|Z| |G|G|G}}',
                                                                        '{{pfrow|G|G|G|G|G|Z|G|G|G|G}}', 1)),
                        ('the STMB_Cave caption gone', stext.replace('NEXT queue', 'next queue', 1))):
        got = stmb_page_problems(base, page)
        if page == stext or not got:
            print(f'selftest FAILED: {label} was not caught ({got[:2]})')
            ok = False
        else:
            print(f'  killed: {label}  [stmb:]')
    with tempfile.TemporaryDirectory() as td:
        missing = harddrop_snapshot_checks(base, Path(td))
        for k, t in pages.items():
            (Path(td) / base['cross_source'][k]['snapshot_file']).write_text(t)
        hashed = harddrop_snapshot_checks(base, Path(td))
    if not any('is not in' in x for x in missing) or sum('hash:' in x for x in hashed) < 4:
        print(f'selftest FAILED: the harddrop snapshots (missing={missing[:2]}, hashed={hashed[:4]})')
        ok = False
    else:
        print('  killed: a harddrop snapshot missing / its bytes not the pinned revision  [harddrop: anchor:]')
    for planted, label in ((True, 'this page\'s own build board planted in another technique transcription'),
                           (False, 'control: the same file with that board emptied')):
        got = _other_plant_problems(planted)
        if bool(got) != planted:
            print(f'selftest FAILED: {label}: other: reported {got[:2]}')
            ok = False
        else:
            print(f'  {"killed" if planted else "control quiet"}: {label}  [other:]')
    print('selftest: harddrop, payoff and other checks all caught' if ok else 'selftest: FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))

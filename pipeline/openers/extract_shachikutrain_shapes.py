"""Transcribe shiwehi.com's 社畜トレイン (Shachiku Train) page into `shachikutrain-technique.json`.

    python3 -m pipeline.openers.extract_shachikutrain_shapes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_shachikutrain_shapes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_shachikutrain_shapes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_shachikutrain_shapes --html-dir <dir> --write  # ...and rewrite

The seventh MID-GAME TECHNIQUE page (中盤テンプレ・ドネイト), after STSD, STMB Cave, インペリアルクロス, ダブルダガー, BT砲
and 千鳥格子: 「TSDを2回打つドネイト」. An S laid one column off a wall and an L hung over its far end make a TSD slot;
the T goes in laid FLAT, pointing down, under the wall's roof over its near end (the page's grey stack; harddrop
draws a Z there). Its two cleared rows drop the row above the slot onto the cell beside the S's foot, which is a
second TSD slot; a Z roofs it, and the second T goes in flat too (the page: 「その後%Zで屋根を付けてもう一度TSDを打ちます」).

DECISION: the spin is a TSD (a full T-spin, 2 lines) and the anchor is the T's four cells — the T laid flat, nub
down, as STMB Cave's, ダブルダガー's, BT砲's and 千鳥格子's. So the window predicate expresses it and the matcher
(`technique-facts.ts`) is untouched. The follow-up is the second TSD, whose four cells are split by the first
TSD's two cleared rows (its arms above them, its nub under them); the matcher's row map joins them, as it does for
BT砲's TST and 千鳥格子's second TSD. Nothing shared changed: no gate rule, no hashed file.

WHY THE WINDOW IS THE AGREEMENT BOX (`window_basis: agreement`, STMB Cave's opt-in), not STSD's bounding box. The
basic form draws the whole stack left of the slot as grey rows above the T, so every one of those cells is a "roof
cell" and STSD's rule would take in the whole stack. So the window is the box on which every drawing of the shape
agrees: this page's five (the basic form, the 4x2 build, the two 2x2-hole builds and the DT社畜 build, drawn
MIRRORED) and every drawing on harddrop's own Shachiku_Train page (another site, other authors, pinned below) whose
drawn T it fires at — that page's every OTHER drawn T recorded with why it misses, so the set is not chosen. It
comes out four rows by six columns: the row above the T (the roof over its near end and the cell beyond it
filled, the cell over its middle and the second slot's arms empty), the two rows the TSD clears, and the row under
them (the cell under the nub and the S's foot filled, the second slot's nub cell empty, the L's foot beyond it
filled). Widening it meets a disagreement (above: harddrop's and the page's 2x2 builds put the roof's Z there;
below: the 2x2 and DT社畜 builds leave the second nub's under-cell open; left: the 4x2 build) or leaves a drawing
(right: the basic form's second slot runs to the wall).

WHERE THE TRANSCRIPTION COMES FROM. `NODES` is a literal, hand-checked transcription of the page's RAW HTML,
fetched the way STSD's was: curl through the session proxy, TLS verification on, with a CA bundle adding the Let's
Encrypt YE2 intermediate shiwehi.com omits. Thirteen boards, plain text in `<div class="ttt">`, one row per line.
The page is not committed; CI cannot fetch it. harddrop's two pages (Shachiku_Train, and STMB_Cave for its
comparison) are read as the pinned revisions' own bytes from the MediaWiki API (urllib, a descriptive User-Agent,
never curl), the way BT砲's and 千鳥格子's were; harddrop's cell reading (`hd_cell`, `_sections`) is BT砲's and the
T partition (`hd_slots`) 千鳥格子's, imported, so the three harddrop transcriptions read one code one way.

THIS PAGE DRAWS ITS SPINS UNMUTED, so no board here is a gate `spin` board. The shared spin rule requires every cell
of a row the spin clears to be drawn upper case; this page draws the T as `U` and leaves the cleared rows in their
own colours (the basic form's first TSD has no muted cell at all). So each board with a T drawn is a `build` on a
DERIVED board (that board less its `U`), and this module's `tsd:` rule checks what the spin rule would: the `U` is
one T, it clears exactly two rows of its board, and the board less it is the derived board, exactly. The window's
agreement drawings and `fires_on` boards are those derived boards, with the slot empty.

THE PAGE'S VARIANTS, decided one by one (`extra_checks` measures each):

  * the basic form and the 4x2 build: the first TSD is the window's, and the T the page draws next is exactly the
    window's follow-up slot (re-anchored at each build's T) — expressed, both steps.
  * the 2x2-hole builds (「STSDの地形が現れます」, and the TST terrain): the first TSD is the window's (it fires once on
    each), but the page's next step is NOT the second TSD: the cell under the follow-up's nub is open (the hole), and
    what the page names next is an STSD or a TST in it. Recorded in `not_expressed`, measured: the follow-up T fills
    no row of the drawn after board, and STSD's own window (stsd-technique.json) fires on neither after board.
  * DT社畜 (開幕DT砲からの派生): one board, the build before the first TSD, drawn mirrored; the window fires on it once,
    mirrored — expressed. What the build keeps under the follow-up's nub (the DT砲's hole, open three rows down and
    cut off by the drawing's bottom edge, where the L shows three cells) is not drawn and not expressed (`not_expressed`).

STMB CAVE, MEASURED, NOT ASSUMED. harddrop's STMB_Cave page (wiki-tspin-techniques.json) says a variation of it
「has the same shape and steps as Shachiku Train」. Its table 17 draws that variation (an O base: a cave three
wide under the T), the Shachiku Train it compares (a J base) and the second TSD. Measured (`stmb:`): this window
fires on the J base only and STMB Cave's window on the O base only; anchored on the same flat T the two windows
clash at TWO cells, both in the row under the nub row: the cell under the nub and its neighbour under one arm (the
right arm as drawn, the left mirrored; STMB Cave: empty, the cave three wide; this page: filled, the J). They agree
in the cleared rows, the only other rows both read: STMB Cave's window does not read the row above the T, so
「the same shape」 is measured there by this window alone. The two clashing cells and the rows both windows read are
recorded (`clash`, `rows_both_read`) and the gate re-measures them (`stmb:`); harddrop's own Shachiku_Train page
draws the same comparison (its tables 10 and 11), and the gate holds the boards equal.

WHAT IS AN INFERENCE, flagged in the JSON (`reading`, the legend) rather than in prose only:

  * `U` is the T the spin places, `r` a pale S (the renderer's translucent green, mirrored to pale red), upper
    case an earlier cell the page draws in the renderer's muted colour — inconsistently (the 4x2 second board's L
    and the 2x2 after boards' O stay lower case).
  * each derived board is a drawing less its `U` (or its page pieces), checked letter for letter; the board between
    the two TSDs, which the page draws only with the Z and the second T in, is measured to be what the first TSD
    leaves, plus the Z (and on the 4x2 build an I against the wall).
  * harddrop's cell codes: `P` is the placed T (read `U`), blank empty, every other code its last letter in lower
    case, every one filled (`'S` the ghost of an S, `1`/`2` the wall's height marks).
"""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers import technique_transcription as TT
from pipeline.openers.extract_btcannon_shapes import _sections, hd_cell
from pipeline.openers.extract_cutcopy_shapes import hd_slots
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS
from pipeline.openers.route_transcription import EMPTY, WIDTH, after_spin, bottom
from pipeline.openers.technique_transcription import node

HERE = Path(__file__).resolve().parent
OUT = HERE / 'shachikutrain-technique.json'
#: where the `cross:` rule reads the other technique transcriptions; the selftest points it at a planted one
TECHNIQUE_DIR = HERE
STMB_FILE = 'stmbcave-technique.json'
STSD_FILE = 'stsd-technique.json'
WIKI_FILE = 'wiki-tspin-techniques.json'

ALPHABET = frozenset('-cUijlorszJLOSZ')


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/shachikutrain.php',
    'title': '社畜トレイン(Shachiku Train)',
    'author': 'しゑひ(shiwehi)',
    'created': '2020-10-31',
    'updated': '2020-10-31',
    'fetched': '2026-10-19',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle '
                    'that adds the Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), '
                    'the method STSD, STMB Cave, インペリアルクロス, ダブルダガー, BT砲, 千鳥格子, 山岳積み2号 and stick spin '
                    'used. The snapshot is the page\'s raw HTML, byte for byte; every board is plain text in it, 13 '
                    'ten-wide boards in page order.',
    'snapshot_file': 'shachikutrain.html',
    'snapshot_sha256': '874a21bbd92d38e3cae92a150d19f17529a3b0afa180b35d4d9c10a0b7d6d1b1',
    'snapshot_bytes': 24908,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable '
                     'in CI: the page is not committed and cannot be fetched there. Re-check with '
                     '--html-dir after any refetch (with harddrop\'s Shachiku_Train.wikitext and STMB_Cave.wikitext '
                     'beside it); an HTML hash moves with ANY byte of the page (ads, sidebar, a date), so a moved '
                     'hash means "read the board diff", not "the boards changed". Sentences are compared against the '
                     'page with its tags dropped.',
    'renderer': {
        'url': 'https://shiwehi.com/tetris/mutual/column-exp.js?date=20210408',
        'read': '2026-10-19',
        'sha256': '95c431a4147f9c30fc0e1bae935e6af6f5669c3d2fa1edfc388848e69ab62570',
        'sha256_note': 'the same bytes STSD and BT砲 recorded, re-fetched for this page to read `r` and the upper case',
        'colorMap_used': {'c': '#a3a3a3', 'U': '#c8a6ff with a #8400ff dot (gradientMap)',
                          'i j l o s z': '#00b7ff #0011ff #ff7b00 #eeee00 #33ff00 #ff0000',
                          'r': '#a6ffa6, a translucent green (gradientMap), the S colour pale',
                          'J L O S Z': '#4d57d8 #d8904d #cfcf4d #69d24d #d84d4d', '-': '#000000'},
        'mirror_button': 'body.reversed swaps j<->l, s<->z, r<->y (and upper case); the page draws only one hand',
    },
    'decorative_images': ['社畜トレイン(Shachiku Train)タイトル画像'],
    'references': ['https://tetrisch.github.io/main/technic/train.html (the page\'s own reference, Tetrisチャンネル)',
                   'https://four.lol/methods/dt-cannon (the page\'s own reference)',
                   'https://twitter.com/Inami10126124/status/1313321189478068224 (the page\'s own reference)',
                   './stsd.php', './derivedtcannonop.php (開幕DT砲からの派生)', './mechanicaltsdv3.php (a related page)'],
    'unfetched': ['the page\'s three references (Tetrisチャンネル, four.lol, a tweet): harddrop\'s Shachiku_Train page, which '
                  'the page does not cite, is the second source read instead'],
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ',
    '-': 'empty',
    'c': 'a cell filled before this diagram (any piece, or garbage), grey',
    'i j l o s z': 'a cell of that piece, placed to build the shape',
    'r': 'a cell of an S the page draws pale (the renderer\'s translucent green; its mirror button turns it pale red, '
         'as it turns s into z): OUR READING, checked: its cells are one S on the board that places it',
    'U': 'a cell of the T the spin places (the renderer\'s light purple with a dark dot); this page draws its spins '
         'UNMUTED, so a board with a T is a build on the board less its U (`tsd:` checks the two rows it clears)',
    'J L O S Z': 'a cell placed before the first TSD, drawn in the renderer\'s muted colour on the boards after it: OUR '
                 'READING, and the page is not consistent (the 4x2 second board keeps its L, the 2x2 after boards their '
                 'O, lower case)',
    '%X': 'the X piece',
}

QUOTES = [
    {'id': 'intro', 'verbatim': 'ここでは、社畜トレイン(Shachiku Train)という、TSDを2回打つドネイトについて紹介していきます。'},
    {'id': 'h.basic', 'verbatim': '基本形と組み方・ラインの消し方'},
    {'id': 'basic', 'verbatim': '下図のように%S%Lを用いてTSDの形を打ち、その後%Zで屋根を付けてもう一度TSDを打ちます。'},
    {'id': 'w4', 'verbatim': '4x2の窪みが空いていれば段を組みつつ打つことができます。'},
    {'id': 'h.u2', 'verbatim': '下穴が2x2マス空いているときの社畜トレイン'},
    {'id': 'u2', 'verbatim': '下穴が2x2マス空いているときに社畜トレインを打つことで、STSDの地形が現れます。'},
    {'id': 't3', 'verbatim': 'また、下穴の形によってはTSTの地形が現れます。'},
    {'id': 'h.dt', 'verbatim': '開幕DT砲からの社畜トレイン(DT社畜)'},
    {'id': 'dt.intro', 'verbatim': '開幕DT砲からの派生の1つとして社畜トレインを組むこともできます。'},
    {'id': 'dt', 'verbatim': '%S%Zが早い時に下図のようにすることで組むことができます。'},
    {'id': 'h.ref', 'verbatim': '参考ページ'},
]

NODES = [
    {'id': 'basic', 'kind': 'base', 'caption_quote': 'h.basic',
     'label': 'the basic form\'s terrain: a stack to the left, two rows deep beside it, a well at the right wall',
     'rows': _b('---------- cccccc---- ccccc----- cccccc---- cccccc---- ccccccccc- ccccccccc-')},
    {'id': 'basic.spin', 'kind': 'build', 'on': 'basic.build', 'adds': 'U', 'spin_piece': 'U', 'spin': 'TSD',
     'lines': 2, 'caption_quote': 'basic',
     'label': 'an S one column off the stack, an L hung over its far end, and the T laid flat, pointing down, under the '
              'stack\'s roof: a TSD',
     'rows': _b('---------- cccccc---- cccccUUUll ccccccUssl ccccccss-l ccccccccc- ccccccccc-')},
    {'id': 'basic.second', 'kind': 'build', 'on': 'basic.roofed', 'adds': 'U', 'spin_piece': 'U', 'spin': 'TSD',
     'lines': 2, 'caption_quote': 'basic',
     'label': 'what the TSD leaves, a Z roofing the second slot, and the second T laid flat into it: a second TSD (the '
              'page draws this board, not the one before the Z)',
     'rows': _b('---------- -------z-- ------zz-- cccccczUUU ccccccSSUL ccccccccc- ccccccccc-')},
    {'id': 'w4', 'kind': 'base', 'caption_quote': 'w4',
     'label': 'a hollow four wide and two deep',
     'rows': _b('---------- ---------- ---------- ccc----ccc ccc----ccc')},
    {'id': 'w4.spin', 'kind': 'build', 'on': 'w4.build', 'adds': 'U', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'w4',
     'label': 'the S and L in the hollow, a pale S, a J and an O stacked around them, and the T laid flat: a TSD',
     'rows': _b('--------oo -rr----joo rrUUUlljjj cccUsslccc cccss-lccc')},
    {'id': 'w4.second', 'kind': 'build', 'on': 'w4.roofed', 'adds': 'U', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'w4',
     'label': 'what the TSD leaves, an I against the wall and a Z roofing the second slot, and the second T in it',
     'rows': _b('i--------- i---z----- i--zz---OO irrzUUUJOO cccSSUlccc')},
    {'id': 'u2', 'kind': 'base', 'caption_quote': 'h.u2',
     'label': 'a hole two wide and two deep under the slot\'s row',
     'rows': _b('---------- ---------- ------cccc ------cccc ------cccc cccc--cccc cccc--cccc')},
    {'id': 'u2.spin', 'kind': 'build', 'on': 'u2.build', 'adds': 'U', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'u2',
     'label': 'an O against the wall, the S and L, a Z roofing the T\'s near end, and the T laid flat: a TSD',
     'rows': _b('-z-------- zz-------- zUUUllcccc ooUsslcccc ooss-lcccc cccc--cccc cccc--cccc')},
    {'id': 'u2.after', 'kind': 'after', 'after_of': 'u2.spin', 'caption_quote': 'u2',
     'label': 'what the TSD leaves: the S\'s foot over the hole, an STSD\'s terrain',
     'rows': _b('---------- ---------- -Z-------- ZZ-------- ooSS-Lcccc cccc--cccc cccc--cccc')},
    {'id': 't3', 'kind': 'base', 'caption_quote': 't3',
     'label': 'the same, with one more cell filled at the hole\'s bottom',
     'rows': _b('---------- ---------- ------cccc ------cccc ------cccc cccc--cccc cccc-ccccc')},
    {'id': 't3.spin', 'kind': 'build', 'on': 't3.build', 'adds': 'U', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 't3',
     'label': 'the same build and TSD over it',
     'rows': _b('-z-------- zz-------- zUUUllcccc ooUsslcccc ooss-lcccc cccc--cccc cccc-ccccc')},
    {'id': 't3.after', 'kind': 'after', 'after_of': 't3.spin', 'caption_quote': 't3',
     'label': 'what the TSD leaves: a TST\'s terrain',
     'rows': _b('---------- ---------- -Z-------- ZZ-------- ooSS-Lcccc cccc--cccc cccc-ccccc')},
    {'id': 'dt', 'kind': 'build', 'on': 'dt.terrain', 'adds': 'jlsz', 'caption_quote': 'dt',
     'label': 'DT社畜: from the DT砲 opener with S and Z early, a J and a Z against the wall, an S hung over the slot '
              '(mirrored; no T drawn)',
     'rows': _b('---------- ----s----- ----ss---- jj---scccc jzz-cccccc j-zzcccccc --llcccccc ---lcccccc')},
    # ── derived: drawn nowhere on the page ──
    {'id': 'basic.build', 'kind': 'derived', 'derived': True, 'on': 'basic', 'adds': 'ls',
     'reading': 'basic.spin less its U: the slot the T goes into, the basic form plus the S and the L',
     'rows': _b('---------- cccccc---- ccccc---ll cccccc-ssl ccccccss-l ccccccccc- ccccccccc-')},
    {'id': 'basic.roofed', 'kind': 'derived', 'derived': True,
     'reading': 'basic.second less its U: what the first TSD leaves (measured to be basic.spin after its clear, by '
                'occupancy) plus the Z',
     'rows': _b('---------- -------z-- ------zz-- ccccccz--- ccccccSS-L ccccccccc- ccccccccc-')},
    {'id': 'w4.build', 'kind': 'derived', 'derived': True, 'on': 'w4', 'adds': 'jlors',
     'reading': 'w4.spin less its U: the slot the T goes into',
     'rows': _b('--------oo -rr----joo rr---lljjj ccc-sslccc cccss-lccc')},
    {'id': 'w4.roofed', 'kind': 'derived', 'derived': True,
     'reading': 'w4.second less its U: what the first TSD leaves (measured to be w4.spin after its clear, by '
                'occupancy) plus the I and the Z',
     'rows': _b('i--------- i---z----- i--zz---OO irrz---JOO cccSS-lccc')},
    {'id': 'u2.build', 'kind': 'derived', 'derived': True, 'on': 'u2', 'adds': 'losz',
     'reading': 'u2.spin less its U: the slot the T goes into',
     'rows': _b('-z-------- zz-------- z---llcccc oo-sslcccc ooss-lcccc cccc--cccc cccc--cccc')},
    {'id': 't3.build', 'kind': 'derived', 'derived': True, 'on': 't3', 'adds': 'losz',
     'reading': 't3.spin less its U: the slot the T goes into',
     'rows': _b('-z-------- zz-------- z---llcccc oo-sslcccc ooss-lcccc cccc--cccc cccc-ccccc')},
    {'id': 'dt.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'dt less its J, L, S and Z: the DT砲 stack the page builds on',
     'rows': _b('---------- ---------- ---------- ------cccc ----cccccc ----cccccc ----cccccc ----cccccc')},
]

#: the follow-up slot (the second TSD), in basic.spin's frame and in basic.roofed's
_FU_PRE = [[1, 7], [1, 8], [1, 9], [4, 8]]
_FU_AFTER = [[3, 7], [3, 8], [3, 9], [4, 8]]

#: the variant's window, in basic.spin's frame
VARIANTS = [{
    'id': 'shachikutrain', 'board': 'basic.spin', 'spin': 'TSD', 'lines': 2,
    'window_basis': 'agreement',
    'window': {'rows': [1, 4], 'cols': [4, 9]},
    't_cells': [[2, 5], [2, 6], [2, 7], [3, 6]],
    'roof_cells': [[1, 4], [1, 5]],
    'window_note': 'in basic.spin\'s frame, row 0 the top: the AGREEMENT BOX of this page\'s drawings of the shape '
                   'and harddrop\'s Shachiku_Train drawings. Row 1 is the row above the T: the roof over its near end and the cell '
                   'beyond it filled, the cell over its middle and the second slot\'s arms empty; rows 2-3 are the rows '
                   'the TSD clears (entailed by the clear at a full TSD, NaiveClauseForced); row 4 is the row under them: '
                   'the cell under the nub and the S\'s foot filled, the second slot\'s nub cell empty, the L\'s foot '
                   'beyond it filled. The second slot\'s roof (the Z) is outside: the page places it after the first TSD. '
                   'Occupancy only, never colour; garbage is filled.',
    'untested_drawn': {'cells': [], 'reason': ''},
    'agreement': [
        {'board': 'basic.build', 't_cells': [[2, 5], [2, 6], [2, 7], [3, 6]], 'mirrored': False},
        {'board': 'w4.build', 't_cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'mirrored': False},
        {'board': 'u2.build', 't_cells': [[2, 1], [2, 2], [2, 3], [3, 2]], 'mirrored': False},
        {'board': 't3.build', 't_cells': [[2, 1], [2, 2], [2, 3], [3, 2]], 'mirrored': False},
        {'board': 'dt', 't_cells': [[3, 2], [3, 3], [3, 4], [4, 3]], 'mirrored': True},
    ],
    'followup': {'board': 'basic.roofed', 'spin': 'TSD', 'lines': 2,
                 't_cells_pre_clear': _FU_PRE,
                 't_cells_after': _FU_AFTER,
                 'note': 'the flat T, pointing down, into the second slot. Before the TSD its cells are split by the two '
                         'cleared rows (its arms above them, its nub under them); the TSD joins them, the Z roofs them, '
                         'and the matcher carries the slot through every later clear to the next T.'},
    'fires_on': ['basic.build', 'w4.build', 'u2.build', 't3.build'],
    #: the page's mirrored drawing: the window fires on it exactly once, mirrored (`extra_checks`; the shared rule (e)
    #: takes only as-drawn boards)
    'fires_mirrored': ['dt'],
    'misses': ['basic', 'basic.spin', 'basic.second', 'basic.roofed', 'w4', 'w4.spin', 'w4.second', 'w4.roofed',
               'u2', 'u2.spin', 'u2.after', 't3', 't3.spin', 't3.after', 'dt.terrain'],
    #: the second step the page draws, per build: the window's follow-up slot re-anchored at the build's T is the T
    #: the page draws on that board (`extra_checks`)
    'second_drawn': [{'build': 'basic.build', 'board': 'basic.second'},
                     {'build': 'w4.build', 'board': 'w4.second'}],
    #: what the page draws next that the window's follow-up is not: measured, not fitted
    'not_expressed': [
        {'build': 'u2.build', 'after': 'u2.after', 'quote': 'u2', 'next': 'STSD', 'fills': 1,
         'reason': 'the page\'s next step is the STSD whose terrain the TSD uncovers, not the second TSD: the cell under '
                   'the follow-up slot\'s nub is the open 2x2 hole, the page draws no roof and no stack beside the slot\'s '
                   'arms (the follow-up T fills one row of the drawn after board, a TSD two), and STSD\'s own window fires '
                   'nowhere on it (its roof is not built yet). A hit on this terrain is still a hit, counted with the '
                   'follow-up\'s own outcome; the STSD is the STSD page\'s'},
        {'build': 't3.build', 'after': 't3.after', 'quote': 't3', 'next': 'TST', 'fills': 1,
         'reason': 'the page\'s next step is the TST whose terrain the TSD uncovers, not the second TSD: the cell under '
                   'the follow-up slot\'s nub is open, the page draws no roof and no stack beside the slot\'s arms (the '
                   'follow-up T fills one row of the drawn after board), and STSD\'s window fires nowhere on it either. '
                   'A TST has no window on this page'},
        {'build': 'dt', 'after': None, 'quote': 'dt.intro', 'next': 'DT砲',
         'reason': 'the build keeps the DT砲\'s hole under the follow-up slot\'s nub (open three rows down, mirrored), and '
                   'the drawing stops there: its L shows three cells, the fourth under the bottom edge. What the page '
                   'builds next from the DT砲 is not drawn, so nothing past the second TSD is read'},
    ],
}]


def _hd(table: int, board: int, section: str, mirrored: bool, slot: list, rows: str) -> dict:
    return {'table': table, 'board': board, 'section': section, 'mirrored': mirrored, 'slot': slot, 'rows': _b(rows)}


def _miss(table: int, board: int, section: str, slot: list, t: str, lines: int, window: str, note: str,
          rows: str) -> dict:
    return {'table': table, 'board': board, 'section': section, 'slot': slot, 't': t, 'lines': lines,
            'window': window, 'note': note, 'rows': _b(rows)}


GS, VO = 'Generic Structure', 'Variations, Other Uses, and Comparisons'
_DONATION = '「Company Train could be used along with Donation T-Spin Double」'

#: harddrop's Shachiku_Train page: every board on it with a drawn T (`P`) the window fires on, read with `hd_cell`
HARDDROP = {
    'page': 'https://harddrop.com/wiki/Shachiku_Train',
    'title': 'Shachiku Train',
    'oldid': 41468,
    'revision_sha1': 'aec937b73a2c6f418ece2bf57f8b57ac96e2be0f',
    'revision_timestamp': '2024-12-27T06:07:00Z',
    'fetched': '2026-10-19',
    'fetch_method': 'the latest revision\'s own bytes from the MediaWiki API (api.php?action=query&prop=revisions&'
                    'titles=Shachiku_Train&rvprop=ids|sha1|size|timestamp|content&rvslots=main), with Python\'s urllib '
                    'and a descriptive User-Agent (NOT curl); the API\'s sha1 equals the sha1 of the bytes, and 41468 was '
                    'the page\'s latest revision when fetched',
    'snapshot_file': 'Shachiku_Train.wikitext',
    'snapshot_sha256': '41e975cb5391eaa98d43948272c8312633b0bbce3f4158ef77099de3fbab4f14',
    'snapshot_bytes': 13081,
    'snapshot_note': 'not committed: check_wikitext_sources refetches the pinned revision weekly through api.php and '
                     're-checks it with --wikitext-dir; a person re-checks it with --html-dir, the file beside '
                     'shachikutrain.html',
    'author_note': 'harddrop\'s page, edited by its wiki editors (it calls the technique Company Train as well): another '
                   'site and other authors than shiwehi.com, and a page the shiwehi.com page does not cite (found by its '
                   'title), so it is independent of it',
    'reading': {'blank': '-', 'P': 'U, the T placed into the spin (the slot the agreement rule fires the window at)',
                'other': 'any other code, its last letter in lower case (G grey, \'S the ghost of an S, 1 and 2 the '
                         'wall\'s height marks), every one FILLED (BT砲\'s hd_cell)',
                'slots': 'a board\'s U cells are partitioned into T\'s (千鳥格子\'s hd_slots); each T is one slot, read with '
                         'every U cell of the board empty'},
    'drawings': [
        _hd(1, 0, GS, False, [[3, 5], [3, 6], [3, 7], [4, 6]],
            '---------- -----z---- ggggzz---- ggggzUUUll ggggggUssl ggggggss-l ggggggggg- ggggggggg- ggggggggg-'),
        _hd(2, 0, VO, False, [[3, 5], [3, 6], [3, 7], [4, 6]],
            '---------- -----z---- ggggzz---- ggggzUUUll ggggggUssl ggggggss-l ggggggg--- ggggggg--- ggggggg---'),
        _hd(3, 2, VO, False, [[3, 3], [3, 4], [3, 5], [4, 4]],
            '---------- ---z----i- --zz----i- oozUUUllij ooggUsslij ggggss-ljj gggggg-ggg gggggg-ggg gggggg-ggg'),
        _hd(4, 0, VO, False, [[3, 5], [3, 6], [3, 7], [4, 6]],
            '---------- ---------- ----ss---- gggssUUUll ggggggUjjl gggggggj-l gggggggj-g gggggggg-g gggggggg-g'),
        _hd(4, 1, VO, False, [[3, 4], [3, 5], [3, 6], [4, 5]],
            '---------i ---oo----i ---oo----i ggggUUUzzi gggggUsszz gggggss-oo ggggggg-oo ggggggg-gg ggggggg-gg'),
        _hd(4, 2, VO, False, [[4, 1], [4, 2], [4, 3], [5, 2]],
            '---------- l-----i--- l-----i--- ll----izz- gUUUssijzz ggUssoojjj gggg-ooggg ggggg-gggg ggggg-gggg'),
        _hd(4, 3, VO, True, [[6, 3], [6, 4], [6, 5], [7, 4]],
            '---------- ---------- ---------- ---------- l--------- l----zz--- llsUUUzzgg oossUggggg oo-sgggggg'),
        _hd(4, 4, VO, False, [[3, 3], [3, 4], [3, 5], [4, 4]],
            '---------- --oo-----z j-oo----zz jjjUUUsszl iiiiUsslll gggggg-ggg gggggg-ggg gggggg-ggg gggggg-ggg'),
        _hd(5, 0, VO, True, [[3, 3], [3, 4], [3, 5], [4, 4]],
            '---------- l--------- l----zz--- llsUUUzzgg oossUggggg oo-sgggggg'),
        _hd(7, 0, VO, False, [[3, 3], [3, 4], [3, 5], [4, 4]],
            '---------- --oo-----z j-oo----zz jjjUUUsszl iiiiUsslll gggggg-ggg gggggg-ggg gggggg-ggg gggggg-ggg'),
        _hd(9, 2, VO, False, [[4, 3], [4, 4], [4, 5], [5, 4]],
            '---------- ---------- ---z------ ggzz----gg ggzUUUssgg gggjUssggg gggjjj-ggg'),
        _hd(10, 0, VO, False, [[3, 3], [3, 4], [3, 5], [4, 4]],
            '---------- ---z------ ggzz----gg ggzUUUssgg gggjUssggg gggjjj-ggg'),
        _hd(12, 0, VO, True, [[3, 4], [3, 5], [3, 6], [4, 5]],
            '---------- -ss------- ss----iiii oojjUUUggg oojzzUgggg ggj-zzgggg ggg-gggggg ggg-gggggg ggg-gggggg'),
        _hd(13, 0, VO, False, [[4, 2], [4, 3], [4, 4], [5, 3]],
            '---------- -s-------- -ss------- oos------- ooUUUiiiil gggUjjjlll ggggg-jggg ggggggg-gg'),
        _hd(13, 1, VO, False, [[5, 4], [5, 5], [5, 6], [6, 5]],
            '---------- ---------- ---------- -g--z----- -ggzz----l gggzUUUlll gggggUgggg ggggggg-gg'),
        _hd(14, 1, VO, False, [[6, 4], [6, 5], [6, 6], [7, 5]],
            '---------- ---------- ---------- ---------- ----z----- ---zz----i gggzUUUlli gggggUssli gggggss-li'),
        _hd(14, 2, VO, False, [[6, 4], [6, 5], [6, 6], [7, 5]],
            '---------- ---------- ---------- ---------- ----z----- ---zz----l gggzUUUlll gggggUssoo gggggss-oo'),
        _hd(15, 0, VO, True, [[3, 5], [3, 6], [3, 7], [4, 6]],
            '---------- -------lll -------loo iiiizUUUoo jjjzzsUggg --jz-ssggg -gggggsggg -ggggggggg -ggggggggg'),
        _hd(15, 1, VO, True, [[3, 5], [3, 6], [3, 7], [4, 6]],
            '---------- ---------- -------zz- liiiiUUUzz lllssgUooj --ss-ggooj -gggggggjj -ggggggggg -ggggggggg'),
        _hd(17, 0, VO, False, [[5, 5], [5, 6], [5, 7], [6, 6]],
            '---------- gggg------ gggg------ gggg-z---- ggggzz---- ggggzUUUll ggggggUssl ggggggss-l gggggggg-g'),
        _hd(17, 1, VO, False, [[4, 5], [4, 6], [4, 7], [5, 6]],
            '---------- ---------- ---------- ggggjj---- ggggjUUUll ggggjgUssl ggggggss-l gggggggg-g gggggggg-g'),
        _hd(17, 2, VO, False, [[3, 5], [3, 6], [3, 7], [4, 6]],
            '---------- -----z---- ggoozz---- ggoozUUUll ggiiiiUssl ggggggss-l gggggggg-g gggggggg-g gggggggg-g'),
    ],
    #: every OTHER drawn T on the page: the window does not fire at it in either hand, each named with what the T
    #: is, measured (`t` its lie, `lines` the rows it clears as drawn, `window` why it does not fire) and a note read
    #: off the page around it. With `drawings` this is EVERY drawn T on the page
    'drawn_t_not_fired': [
        _miss(1, 1, GS, [[4, 7], [4, 8], [4, 9], [5, 8]], 'flat-down', 2, 'leaves the board',
              'the generic structure\'s second TSD: the T into the second slot after the first TSD (this window\'s '
              'follow-up, not its T)',
              '---------- ---------- -------z-- -----gzz-- ggggggzUUU ggggggggUg ggggggggg- ggggggggg- ggggggggg-'),
        _miss(6, 0, VO, [[3, 3], [3, 4], [3, 5], [4, 4]], 'flat-down', 2, 'disagrees',
              '「Compare the 4th example of the Company Train\'s variations above with Kaidan Setups (both L and J are '
              'just swapped)」: the Kaidan drawing, a J where the 4th example has its L',
              '---------- -j-------- -j---zz--- jjsUUUzzgg oossUggggg oo-sgggggg'),
        _miss(8, 0, VO, [[3, 4], [3, 5], [3, 6], [4, 5]], 'flat-down', 2, 'disagrees',
              '「Compare the 5th example of the Company Train\'s variations above with Cut Copy (S is just shifted one '
              'column to the right)」: the Cut Copy drawing (千鳥格子\'s window does not fire on it either, measured)',
              '---------- --loo----- -zloo----j zzllUUUssj ziiiiUssjj gggggg-ggg gggggg-ggg gggggg-ggg gggggg-ggg'),
        _miss(9, 3, VO, [[5, 5], [5, 6], [5, 7], [6, 6]], 'flat-down', 2, 'leaves the board',
              'the 4x2-hole variation\'s second TSD (「One could place down the floating S and the overhang before '
              'spinning J in」)',
              '---------- ---------- ---------- -----z---- ---gzz---- ggggzUUUgg ggggggUggg'),
        _miss(11, 0, VO, [[3, 3], [3, 4], [3, 5], [4, 4]], 'flat-down', 2, 'disagrees',
              '「Compare the example of the Company Train\'s variation above with STMB Cave (O base is used instead of '
              'J)」: the STMB Cave drawing, a cave three wide under the T (STMB Cave\'s window fires on it, measured)',
              '---------- ---z------ ggzz----gg ggzUUUssgg ggooUssggg ggoo---ggg'),
        _miss(12, 1, VO, [[4, 2], [4, 3], [4, 4], [5, 3]], 'flat-down', 2, 'disagrees',
              'the second TSD of 「making the overhang for the second T-Spin Double on the other side of the build '
              'before the T for the first T-Spin Double comes」',
              '---------- ---------- ---------- -gg--lll-- ggUUUlgggg gggUgggggg ggg-gggggg ggg-gggggg ggg-gggggg'),
        _miss(13, 2, VO, [[6, 6], [6, 7], [6, 8], [7, 7]], 'flat-down', 2, 'leaves the board',
              'the last TSD of 「three or more consecutive Company Trains」 on diagonal holes',
              '---------- ---------- ---------- i--------- i-----z--- ig--gzz--- iggggzUUUg gggggggUgg'),
        _miss(14, 0, VO, [[6, 7], [7, 7], [7, 8], [8, 7]], 'stood', 3, "not the window's T",
              'the T-Spin Triple 「Company Train could also be used as a direct follow-up to」, before the Company Train',
              '---------- ----z----- ---zz----- gggz------ ggggg-ss-- gggggss--- gggggggUgg gggggggUUg gggggggUgg'),
        _miss(15, 2, VO, [[4, 3], [4, 4], [4, 5], [5, 4]], 'flat-down', 2, 'disagrees',
              f'{_DONATION}: the third drawing of its first table',
              '---------- --i------- --i--s---- --i--ssjjj ooiUUUsggj ooggUggggg -ggggggggg -ggggggggg -ggggggggg'),
        _miss(16, 0, VO, [[2, 3], [2, 4], [2, 5], [3, 4]], 'flat-down', 2, 'disagrees',
              f'{_DONATION}: the first drawing of its second table',
              '---------- iiii------ gjjUUUzzll gjooUsszzl gjooss---l gggggg-ggg gggggg-ggg gggggg-ggg'),
        _miss(16, 1, VO, [[3, 5], [3, 6], [3, 7], [4, 6]], 'flat-down', 2, 'disagrees',
              f'{_DONATION}: the second drawing of its second table',
              '---------- -----z---- ----zz---- ggggzUUUss ggggggUssg gggggg-ggg gggggg-ggg gggggg-ggg'),
    ],
    #: boards with no T drawn on which the window fires at a resting placement
    'fires_without_slot': [],
    #: every other committed technique window, at every drawn T of the page and on every board with none: where it
    #: fires (measured; the gate holds the list complete both ways)
    #: kaidan-technique.json's window (階段のドネイト, the ninth technique page) fires at ten of these drawn T's, measured:
    #: anchored on the same flat T the two windows clash on no cell (kaidan-technique.json's `shachikutrain_relation`)
    'other_windows': [{'table': 11, 'board': 0, 'file': 'stmbcave-technique.json', 'mirrored': [False]},
                      {'table': 3, 'board': 2, 'file': 'kaidan-technique.json', 'mirrored': [False]},
                      {'table': 4, 'board': 0, 'file': 'kaidan-technique.json', 'mirrored': [False]},
                      {'table': 4, 'board': 1, 'file': 'kaidan-technique.json', 'mirrored': [False]},
                      {'table': 4, 'board': 4, 'file': 'kaidan-technique.json', 'mirrored': [False]},
                      {'table': 7, 'board': 0, 'file': 'kaidan-technique.json', 'mirrored': [False]},
                      {'table': 12, 'board': 0, 'file': 'kaidan-technique.json', 'mirrored': [True]},
                      {'table': 16, 'board': 0, 'file': 'kaidan-technique.json', 'mirrored': [False]},
                      {'table': 17, 'board': 0, 'file': 'kaidan-technique.json', 'mirrored': [False]},
                      {'table': 17, 'board': 1, 'file': 'kaidan-technique.json', 'mirrored': [False]},
                      {'table': 17, 'board': 2, 'file': 'kaidan-technique.json', 'mirrored': [False]}],
}

#: harddrop's STMB_Cave page, table 17: the variation it says 「has the same shape and steps as Shachiku Train」, the
#: Shachiku Train it compares, and the second TSD. `fires` is measured per window, in the hand it fires (`stmb:`)
STMB_CAVE = {
    'page': 'https://harddrop.com/wiki/STMB_Cave',
    'oldid': 41496,
    'oldid_note': 'the revision wiki-tspin-techniques.json pins for its STMB_Cave transcription (checked equal)',
    'revision_sha1': '9be6de771a3ca9bc42cec4be9e0ab3df25cf41a4',
    'revision_timestamp': '2024-12-27T16:27:37Z',
    'fetched': '2026-10-19',
    'fetch_method': 'the pinned revision\'s own bytes from the MediaWiki API, as Shachiku_Train\'s (urllib, NOT curl); '
                    '41496 was the page\'s latest revision when fetched',
    'snapshot_file': 'STMB_Cave.wikitext',
    'snapshot_sha256': 'b19a6b917858b3342f4d5afaf5e7bc5d191902e29421ff2e2f82b8444c31faf0',
    'snapshot_bytes': 19937,
    'table': 17,
    'caption': 'Compare this variation of STMB Cave below with [[Shachiku Train]]. Although this variation uses a '
               'floating T-Spin Double over 3 columns wide hole, this still has the same shape and steps as Shachiku Train.',
    'boards': [
        {'board': 0, 'what': 'the STMB Cave variation: an O base, a cave three wide under the T',
         'slot': [[3, 3], [3, 4], [3, 5], [4, 4]], 'fires': {'shachikutrain': [], 'stmbcave': [False]},
         'same_as': [11, 0], 'rows': _b('---------- ---z------ ggzz----gg ggzUUUssgg ggooUssggg ggoo---ggg')},
        {'board': 1, 'what': 'the Shachiku Train it compares: a J base under the T',
         'slot': [[3, 3], [3, 4], [3, 5], [4, 4]], 'fires': {'shachikutrain': [False], 'stmbcave': []},
         'same_as': [10, 0], 'rows': _b('---------- ---z------ ggzz----gg ggzUUUssgg gggjUssggg gggjjj-ggg')},
        {'board': 2, 'what': 'the second TSD, after either',
         'slot': [[4, 5], [4, 6], [4, 7], [5, 6]], 'fires': {'shachikutrain': [], 'stmbcave': []},
         'same_as': [9, 3], 'same_note': 'harddrop\'s Shachiku_Train page draws it with one more empty row on top',
         'rows': _b('---------- ---------- -----z---- ---gzz---- ggggzUUUgg ggggggUggg')},
    ],
    #: offsets (row, column) from the T's top-left, per hand (both windows in the same hand); rows relative to the T's
    #: row. Measured by the gate from the two transcriptions' windows (`stmb:`), never typed for the prose to carry
    'clash': {'as_drawn': [[2, 1], [2, 2]], 'mirrored': [[2, 0], [2, 1]]},
    'rows_both_read': [0, 1, 2],
    'relation': 'measured: anchored on the same flat T the two windows clash at two cells, both in the row under the nub '
                'row: the cell under the nub and its neighbour under one arm (`clash`; STMB Cave empty, the cave three '
                'wide; this window filled, the J), so each fires on its own base only. They agree in the cleared rows, '
                'the only other rows both read (`rows_both_read`): STMB Cave\'s window does not read the row above the T',
}

CROSS_SOURCE = {
    'kind': 'routes',
    'label_pattern': 'shachiku',
    'note': 'the window, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot board of every '
            'committed *-routes.json, with the U cells as the T: it fires on one, the same author\'s stick spin 2.sd (`also`). '
            'The independent drawer is harddrop instead: its Shachiku_Train page (`harddrop`), whose drawings are the '
            'window\'s external `agreement` drawings (rule (g) fires the window on each, once, at its drawn T, in its '
            'recorded hand), and its STMB_Cave page\'s comparison (`stmb_cave`), measured against both windows.',
    'routes_fire_none': 'no routes board by another author draws a Shachiku Train (measured: the window fires on one '
                        'U-slot board of every committed routes file, shiwehi.com\'s own stick spin 2.sd, recorded in '
                        '`also`, and no node is labelled 社畜 or Shachiku); the independent cross-check is harddrop\'s '
                        'own pages, read below',
    'harddrop': HARDDROP,
    'stmb_cave': STMB_CAVE,
    'fires': [],
    'also': [
        {'file': 'stickspin-routes.json', 'node': '2.sd', 'variant': 'shachikutrain', 'mirrored': False,
         'page': 'https://shiwehi.com/tetris/template/stickspin.php',
         'note': 'shiwehi.com\'s stick spin page (the same author): its SDパフェ bag-2 board, whose TSD the window fires on '
                 'as drawn. Measured, not explained; not independent'},
    ],
    'labelled_not_fired': [],
}

KNOWN_DISCREPANCIES: list[dict] = [
    {'id': 'w4.second:colour',
     'note': 'the 4x2 build\'s second board draws the L\'s one surviving cell lower case, where it draws the other cells '
             'placed before the first TSD upper case: one l cell is no whole L (the rest of it was in the cleared rows)'},
    {'id': 'w4.roofed:colour',
     'note': 'w4.second less its U, so the same lone l cell'},
    {'id': 'dt:colour',
     'note': 'the DT社畜 board draws three cells of its L: the fourth would be under the drawing\'s bottom edge (the three '
             'are an L less its bottom cell)'},
]

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'shachikutrain',
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
def _pre(rows: list[str]) -> list[str]:
    return [row.replace('U', EMPTY) for row in rows]


def _hands(data: dict, rows: list[str], slot) -> list[bool]:
    v = data['variants'][0]
    return [m for m in (False, True) if TT.window_fires(data, v, SPEC, _pre(rows), {tuple(x) for x in slot}, m)]


def _fires_anywhere(data: dict, rows: list[str]) -> list[tuple]:
    v, pre = data['variants'][0], _pre(rows)
    return [([list(x) for x in sorted(cs)], m) for cs in TT.t_placements(pre, SPEC) for m in (False, True)
            if TT.window_fires(data, v, SPEC, pre, cs, m)]


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
    v, lock = data['variants'][0], {tuple(x) for x in slot}
    off = []
    for m in (False, True):
        W = TT.window_cells(data, v, SPEC, m)
        D = {k for k, x in W.items() if x == 'T'}
        dr = min(r for r, _ in lock) - min(r for r, _ in D)
        dc = min(c for _, c in lock) - min(c for _, c in D)
        off.append(any(not (0 <= r + dr < len(rows) and 0 <= c + dc < WIDTH) for r, c in W))
    return lie, lines, 'leaves the board' if all(off) else 'disagrees'


def harddrop_drawings(data: dict | None = None) -> list[dict]:
    """harddrop's Shachiku_Train drawings as agreement drawings: the slot is its drawn T, every drawn T read empty."""
    data = data or build()
    return [{'name': f'harddrop Shachiku_Train table {d["table"]} board {d["board"]} ({d["section"]})',
             'rows': _pre(d['rows']), 't_cells': d['slot'], 'mirrored': d['mirrored']}
            for d in data['cross_source']['harddrop']['drawings']]


def external_drawings() -> list[dict]:
    return harddrop_drawings()


def _boards(text: str) -> tuple[dict, list]:
    tables = RT.wikitext_tables(text)
    secs = _sections(text)
    if len(secs) != len(tables):
        raise ValueError(f'{len(tables)} tables but {len(secs)} table openings')
    return ({(i, j): [''.join(hd_cell(c) for c in row) for row in b] for i, t in enumerate(tables) for j, b in enumerate(t)},
            secs)


def harddrop_page_problems(data: dict, text: str) -> list[str]:
    """The recorded drawings against the harddrop Shachiku_Train wikitext: each letter for letter at its (table, board)
    under its heading, and the record COMPLETE both ways — `drawings` exactly the drawn T's the window fires at
    (either hand), `drawn_t_not_fired` exactly every other drawn T, `fires_without_slot` exactly the boards with no T
    drawn on which it fires."""
    hd = data['cross_source']['harddrop']
    try:
        boards, secs = _boards(text)
    except ValueError as e:
        return [f'harddrop: the wikitext does not parse: {e}']
    bad = []
    for d in hd['drawings'] + hd['drawn_t_not_fired'] + hd['fires_without_slot']:
        k = (d['table'], d['board'])
        if boards.get(k) != d['rows']:
            bad.append(f'harddrop: table {k[0]} board {k[1]} is not the recorded drawing (page {boards.get(k)})')
        elif secs[k[0]] != d['section']:
            bad.append(f'harddrop: table {k[0]} sits under {secs[k[0]]!r}, not {d["section"]!r}')
    fired, missed, unslotted = [], [], []
    for (i, j), rows in sorted(boards.items()):
        try:
            slots = hd_slots(rows)
        except ValueError as e:
            bad.append(f'harddrop: table {i} board {j}: {e}')
            continue
        for s in slots:
            hands = _hands(data, rows, s)
            (fired if hands else missed).append((i, j, str(s), hands) if hands else (i, j, str(s)))
        if not slots and _fires_anywhere(data, rows):
            unslotted.append((i, j))
    want = sorted((d['table'], d['board'], str(d['slot']), [d['mirrored']]) for d in hd['drawings'])
    if sorted(fired) != want:
        bad.append(f'harddrop: the window fires at the drawn T of {sorted(fired)}, the record holds {want}')
    named = sorted((e['table'], e['board'], str(e['slot'])) for e in hd['drawn_t_not_fired'])
    if sorted(missed) != named:
        bad.append(f'harddrop: the window misses the drawn T of {sorted(missed)}, drawn_t_not_fired names {named}')
    if sorted(unslotted) != sorted((e['table'], e['board']) for e in hd['fires_without_slot']):
        bad.append(f'harddrop: with no T drawn the window fires on {unslotted}, the record names '
                   f'{[(e["table"], e["board"]) for e in hd["fires_without_slot"]]}')
    return bad


def stmb_page_problems(data: dict, text: str) -> list[str]:
    """The STMB_Cave comparison against its wikitext: the recorded boards are table `table`'s, letter for letter, and
    the table carries the recorded caption."""
    sc = data['cross_source']['stmb_cave']
    try:
        boards, _secs = _boards(text)
    except ValueError as e:
        return [f'stmb: the wikitext does not parse: {e}']
    bad = []
    got = [rows for (i, _j), rows in sorted(boards.items()) if i == sc['table']]
    if got != [b['rows'] for b in sc['boards']]:
        bad.append(f'stmb: table {sc["table"]} of the STMB_Cave page is not the recorded boards (page {got})')
    import re
    opens = [m.start() for m in re.finditer(r'^\{\|', text, re.M)]
    seg = text[opens[sc['table']]:text.find('|}', opens[sc['table']])] if sc['table'] < len(opens) else ''
    if sc['caption'] not in seg:
        bad.append(f'stmb: table {sc["table"]} does not carry the recorded caption')
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
    """`--html-dir`: the two pinned harddrop revisions beside the page snapshot (a missing file is a failure)."""
    bad, text = _snapshot(data['cross_source']['harddrop'], html_dir, 'harddrop')
    if text is not None:
        bad += harddrop_page_problems(data, text)
    b2, t2 = _snapshot(data['cross_source']['stmb_cave'], html_dir, 'stmb')
    bad += b2
    if t2 is not None:
        bad += stmb_page_problems(data, t2)
    return bad


# ── technique-only rules ─────────────────────────────────────────────────────────────────────────
def _clears(rows, cells) -> int:
    o = TT.occ_of(rows, SPEC)
    o = [''.join('#' if (r, c) in cells else ch for c, ch in enumerate(row)) for r, row in enumerate(o)]
    return len(TT.full_rows(o))


def _less(rows: list[str], letters: str) -> list[str]:
    return [''.join(EMPTY if ch in letters else ch for ch in row) for row in rows]


def _other(fname: str) -> tuple[dict, dict, TT.TechniqueSpec]:
    """Another committed technique transcription, its first variant, and a spec its window can be evaluated with."""
    other = json.loads((HERE / fname).read_text())
    ospec = TT.TechniqueSpec(out=HERE / fname, build=lambda: other, alphabet=frozenset(),
                             empty_letters=other.get('empty_letters', ''), max_rows=99)
    return other, other['variants'][0], ospec


def _stmb_clash(data: dict) -> tuple[dict, list[int]]:
    """This window against STMB Cave's, both anchored on the same flat T in the same hand: the cells (row, column
    from the T's top-left) where one needs filled and the other empty, per hand, and the rows (relative to the T's
    row) both windows read."""
    other, ov, ospec = _other(STMB_FILE)

    def norm(d, var, spec, m):
        W = TT.window_cells(d, var, spec, m)
        T = [k for k, x in W.items() if x == 'T']
        r0, c0 = min(r for r, _ in T), min(c for _, c in T)
        return {(r - r0, c - c0): x for (r, c), x in W.items()}
    clash, rows = {}, None
    for m, name in ((False, 'as_drawn'), (True, 'mirrored')):
        a, b = norm(data, data['variants'][0], SPEC, m), norm(other, ov, ospec, m)
        clash[name] = sorted([r, c] for (r, c) in a if (r, c) in b and a[(r, c)] != b[(r, c)] and 'T' not in
                             (a[(r, c)], b[(r, c)]))
        rows = sorted({r for r, _ in a} & {r for r, _ in b})
    return clash, rows


def _fires_other(fname: str, rows: list[str]) -> list[tuple]:
    other, ov, ospec = _other(fname)
    pre = _pre(rows)
    return [(sorted(cs), m) for cs in TT.t_placements(pre, ospec) for m in (False, True)
            if TT.window_fires(other, ov, ospec, pre, cs, m)]


def _offset(v: dict, slot) -> tuple[int, int]:
    """The translation from the variant's frame to a build's drawn T (as drawn)."""
    tc = v['t_cells']
    return (min(r for r, _ in slot) - min(r for r, _ in tc), min(c for _, c in slot) - min(c for _, c in tc))


def extra_checks(data: dict):
    bad, measured = [], set()
    by = {n['id']: n for n in data['nodes']}
    v = data['variants'][0]
    xs = data['cross_source']
    # tsd: every board with a T drawn (`U`) is a build on the board less it; its U is one T clearing exactly two rows
    # (what the shared spin rule checks, for a page that draws its spins unmuted)
    for n in data['nodes']:
        u = {(r, c) for r, row in enumerate(n['rows']) for c, ch in enumerate(row) if ch == 'U'}
        if not u:
            continue
        if n.get('spin_piece') != 'U' or n.get('adds') != 'U' or n.get('kind') != 'build':
            bad.append(f'tsd: {n["id"]} draws a T but is not a build adding its U')
            continue
        ys = {(c, len(n['rows']) - 1 - r) for r, c in u}
        if len(u) != 4 or RT._norm(ys) not in RT._shapes('t'):
            bad.append(f'tsd: {n["id"]}\'s U cells are not one T')
        elif _clears(_less(n['rows'], 'U'), u) != n.get('lines') or n.get('lines') != 2 or n.get('spin') != 'TSD':
            bad.append(f'tsd: {n["id"]}\'s T does not clear the two rows of a TSD')
        if n.get('on') not in by or by[n['on']]['rows'] != _less(n['rows'], 'U'):
            bad.append(f'tsd: {n["id"]} less its U is not its derived board {n.get("on")!r}')
    # pale: the `r` cells of the board that places them are one S
    for n in data['nodes']:
        rc = [(c, len(n['rows']) - 1 - r) for r, row in enumerate(n['rows']) for c, ch in enumerate(row) if ch == 'r']
        if rc and 'r' in n.get('adds', '') and (len(rc) != 4 or RT._norm(rc) not in RT._shapes('s')):
            bad.append(f'pale: {n["id"]}\'s r cells are not one S')
    if not any('r' in n.get('adds', '') for n in data['nodes']):
        bad.append('pale: no board places the pale S')
    # mirror: every mirrored drawing fires once, mirrored, at a placement clearing two rows; every drawn board is listed
    for bid in v.get('fires_mirrored', []):
        if bid not in by:
            bad.append(f'mirror: fires_mirrored names no node {bid!r}')
            continue
        rows = by[bid]['rows']
        hits = _fires_anywhere(data, rows)
        if len(hits) != 1 or not hits[0][1]:
            bad.append(f'mirror: the window fires {len(hits)} time(s) on {bid}, not once mirrored')
        elif _clears(rows, {tuple(x) for x in hits[0][0]}) != 2:
            bad.append(f'mirror: the window fires on {bid} at a placement that does not clear two rows')
    listed = set(v.get('fires_on', [])) | set(v.get('fires_mirrored', [])) | set(v.get('misses', [])) | {v['board']}
    for n in data['nodes']:
        if n['id'] not in listed:
            bad.append(f'mirror: board {n["id"]} is in none of fires_on, fires_mirrored, misses')
    want = sorted([(b, False) for b in v.get('fires_on', [])] + [(b, True) for b in v.get('fires_mirrored', [])])
    if sorted((a['board'], a['mirrored']) for a in v.get('agreement', [])) != want:
        bad.append('mirror: the page\'s agreement drawings are not fires_on (as drawn) and fires_mirrored (mirrored)')
    # after: each board between the two TSDs is what the first TSD leaves plus the pieces the page adds before the
    # second T; each 2x2 after board is checked by the shared after rule
    for spin_id, roofed, extra in (('basic.spin', 'basic.roofed', 'z'), ('w4.spin', 'w4.roofed', 'iz')):
        sp = by[spin_id]
        got, _n = after_spin([''.join('t' if (r, c) in TT.spin_cells(sp) else ('-' if TT.is_empty(ch, SPEC) else 'c')
                                      for c, ch in enumerate(row)) for r, row in enumerate(sp['rows'])])
        less = _less(by[roofed]['rows'], extra)
        if bottom(TT.occ_of(got, SPEC), TT.MAX_ROWS) != bottom(TT.occ_of(less, SPEC), TT.MAX_ROWS):
            measured.add(f'{roofed}:after')
    if v['followup']['board'] != 'basic.roofed':
        bad.append('after: the follow-up is not read on the board the second T goes into')
    # second: the T the page draws next is the window's follow-up slot, re-anchored at the build's T and carried
    # through its two cleared rows
    for e in v.get('second_drawn', []):
        ag = next((a for a in v['agreement'] if a['board'] == e['build']), None)
        if ag is None or e['board'] not in by:
            bad.append(f'second: {e} names no agreement drawing or no board')
            continue
        dr, dc = _offset(v, ag['t_cells'])
        sb = by[e['build']]['rows']
        fr = TT.full_rows(TT.occ_of([''.join('#' if [r, c] in ag['t_cells'] else ch for c, ch in enumerate(row))
                                     for r, row in enumerate(sb)], SPEC))
        slot = {(r + dr + sum(1 for x in fr if x > r + dr), c + dc) for r, c in v['followup']['t_cells_pre_clear']}
        shift = len(sb) - len(by[e['board']]['rows'])
        slot = {(r - shift, c) for r, c in slot}
        drawn = TT.spin_cells(by[e['board']])
        if slot != drawn:
            bad.append(f'second: the follow-up slot at {e["build"]}\'s T is {sorted(slot)}, {e["board"]} draws '
                       f'{sorted(drawn)}')
    # later: what the page draws next that the follow-up is not, measured. The cell under the follow-up slot's nub
    # (inside the drawing; a board that ends above it shows no opening) is open on exactly the builds listed; on each
    # drawn after board the follow-up T is empty-slotted and fills exactly `fills` rows (a TSD fills two), and STSD's
    # own window fires nowhere on it
    qids = {q['id'] for q in data['quotes']}
    under_open = {}
    nr, nc = max(v['followup']['t_cells_pre_clear'])      # the follow-up's nub (its lowest cell)
    for ag in v['agreement']:
        rows = by[ag['board']]['rows']
        R, C = TT.frame_map(data, v, SPEC, {tuple(x) for x in ag['t_cells']}, ag['mirrored'])(nr + 1, nc)
        under_open[ag['board']] = 0 <= R < len(rows) and 0 <= C < WIDTH and TT.is_empty(rows[R][C], SPEC)
    for e in v.get('not_expressed', []):
        if e.get('build') not in by or not e.get('reason') or e.get('quote') not in qids:
            bad.append(f'later: not_expressed {e.get("build")!r} names no board, no quote or carries no reason')
            continue
        if not e.get('after'):
            continue
        a = by.get(e['after'])
        ag = next((x for x in v['agreement'] if x['board'] == e['build']), None)
        if a is None or ag is None or ag['mirrored'] or by.get(a.get('after_of', ''), {}).get('on') != e['build']:
            bad.append(f'later: {e["after"]} is not the after board of {e["build"]}\'s TSD')
            continue
        dr, dc = _offset(v, ag['t_cells'])
        shift = len(by[v['followup']['board']]['rows']) - len(a['rows'])
        slot = {(r + dr - shift, c + dc) for r, c in v['followup']['t_cells_after']}
        if any(not TT.is_empty(a['rows'][r][c], SPEC) for r, c in slot):
            bad.append(f'later: the follow-up slot is not empty on {e["after"]}')
        elif _clears(a['rows'], slot) != e.get('fills'):
            bad.append(f'later: the follow-up T fills {_clears(a["rows"], slot)} row(s) of {e["after"]}, not {e.get("fills")}')
        if e.get('fills') == v['followup']['lines']:
            bad.append(f'later: {e["after"]} is listed as not expressed but the follow-up T would be a full TSD on it')
        if _fires_other(STSD_FILE, a['rows']):
            bad.append(f'later: STSD\'s window fires on {e["after"]} (record it)')
    for b, op in under_open.items():
        if op != any(e['build'] == b for e in v.get('not_expressed', [])):
            bad.append(f'later: {b}\'s cell under the follow-up\'s nub is {"open" if op else "not open"}, '
                       f'{"not " if op else ""}in not_expressed')
    # harddrop: every recorded entry is ten wide; its slot is one of its drawn T's; checked here on the DATA (the
    # agreement rule reads the pristine build through the spec)
    hd = xs.get('harddrop', {})
    seen = set()
    for d in hd.get('drawings', []):
        k = (d['table'], d['board'], str(d['slot']))
        try:
            slots = hd_slots(d['rows'])
        except ValueError as e:
            bad.append(f'harddrop: table {k[0]} board {k[1]}: {e}')
            continue
        if any(len(r) != WIDTH for r in d['rows']) or d['slot'] not in slots:
            bad.append(f'harddrop: table {k[0]} board {k[1]} is not a ten-wide board drawing its slot as a T')
            continue
        hits = [(frozenset(map(tuple, cs)), m) for cs, m in _fires_anywhere(data, d['rows'])]
        if hits != [(frozenset(tuple(x) for x in d['slot']), d['mirrored'])]:
            bad.append(f'harddrop: the window fires {len(hits)} time(s) on table {k[0]} board {k[1]}, not once at its '
                       f'drawn T ({"mirrored" if d["mirrored"] else "as drawn"})')
        if k in seen:
            bad.append(f'harddrop: table {k[0]} board {k[1]} recorded twice')
        seen.add(k)
    if not any(d['section'] == 'Generic Structure' for d in hd.get('drawings', [])):
        bad.append('harddrop: no recorded drawing from the page\'s own Generic Structure section')
    for d in hd.get('drawn_t_not_fired', []):
        k = (d['table'], d['board'], str(d['slot']))
        try:
            slots = hd_slots(d['rows'])
        except ValueError as e:
            bad.append(f'harddrop: table {k[0]} board {k[1]}: {e}')
            continue
        if any(len(r) != WIDTH for r in d['rows']) or d['slot'] not in slots:
            bad.append(f'harddrop: table {k[0]} board {k[1]} (drawn_t_not_fired) does not draw its slot as a T')
            continue
        got = t_lie(data, d['rows'], d['slot'])
        if got != (d['t'], d['lines'], d['window']) or got[2] == 'fires':
            bad.append(f'harddrop: table {k[0]} board {k[1]} slot {d["slot"]} is {got}, drawn_t_not_fired records '
                       f'{(d["t"], d["lines"], d["window"])}')
        if not d.get('note', '').strip():
            bad.append(f'harddrop: table {k[0]} board {k[1]} is in drawn_t_not_fired with no note')
        if k in seen:
            bad.append(f'harddrop: table {k[0]} board {k[1]} slot {d["slot"]} recorded twice')
        seen.add(k)
    # every other committed technique window over every board of the page: where it fires, complete both ways
    got = []
    every = hd.get('drawings', []) + hd.get('drawn_t_not_fired', [])
    for f in sorted(HERE.glob('*-technique.json')):
        if f.name == OUT.name:
            continue
        other, ov, ospec = _other(f.name)
        for d in every:
            hands = [m for m in (False, True)
                     if TT.window_fires(other, ov, ospec, _pre(d['rows']), {tuple(x) for x in d['slot']}, m)]
            if hands:
                got.append({'table': d['table'], 'board': d['board'], 'file': f.name, 'mirrored': hands})
    if sorted(got, key=str) != sorted(hd.get('other_windows', []), key=str):
        bad.append(f'harddrop: the other technique windows fire on {got}, other_windows records {hd.get("other_windows")}')
    for d in hd.get('fires_without_slot', []):
        hits = _fires_anywhere(data, d['rows'])
        if any('U' in r for r in d['rows']) or hits != [(d['slot'], d['mirrored'])]:
            bad.append(f'harddrop: table {d["table"]} board {d["board"]} draws a T, or the window does not fire on it '
                       f'once at {d["slot"]} ({"mirrored" if d["mirrored"] else "as drawn"})')
    # stmb: harddrop's STMB_Cave comparison, measured against this window and STMB Cave's
    sc = xs.get('stmb_cave')
    if not sc:
        bad.append('stmb: no stmb_cave record')
    else:
        wiki = json.loads((HERE / WIKI_FILE).read_text())
        pin = {p['page']: p for p in wiki['provenance']}.get('STMB_Cave', {})
        if pin.get('oldid') != sc['oldid']:
            bad.append(f'stmb: the STMB_Cave revision {sc["oldid"]} is not the one {WIKI_FILE} pins ({pin.get("oldid")})')
        says = {s['technique']: s['says'] for s in wiki['stmb_cave']['confusable']['says']}
        if says.get('Shachiku Train', '') not in sc['caption'].replace('[[', '').replace(']]', ''):
            bad.append(f'stmb: the recorded caption is not the sentence {WIKI_FILE} quotes for Shachiku Train')
        hd_boards = {(d['table'], d['board']): d['rows'] for d in hd.get('drawings', []) + hd.get('drawn_t_not_fired', [])}
        for b in sc['boards']:
            slot = {tuple(x) for x in b['slot']}
            pre = _pre(b['rows'])
            other, ov, ospec = _other(STMB_FILE)
            got = {'shachikutrain': [m for m in (False, True) if TT.window_fires(data, v, SPEC, pre, slot, m)],
                   'stmbcave': [m for m in (False, True) if TT.window_fires(other, ov, ospec, pre, slot, m)]}
            if got != b['fires']:
                bad.append(f'stmb: on STMB_Cave table {sc["table"]} board {b["board"]} the windows fire {got}, '
                           f'the record holds {b["fires"]}')
            trim = lambda rows: [r for k, r in enumerate(rows) if any(x != EMPTY for x in ''.join(rows[:k + 1]))]
            if trim(hd_boards.get(tuple(b['same_as']), [])) != trim(b['rows']):
                bad.append(f'stmb: STMB_Cave table {sc["table"]} board {b["board"]} is not Shachiku_Train table '
                           f'{b["same_as"][0]} board {b["same_as"][1]} (empty rows on top aside)')
        if [sorted(b['fires']['shachikutrain'] + b['fires']['stmbcave']) for b in sc['boards']].count([False]) != 2:
            bad.append('stmb: the comparison is not one board per window')
        clash, rows_both = _stmb_clash(data)
        if clash != sc.get('clash'):
            bad.append(f'stmb: anchored on the same flat T the two windows clash at {clash}, the record holds '
                       f'{sc.get("clash")}')
        if rows_both != sc.get('rows_both_read'):
            bad.append(f'stmb: the rows both windows read are {rows_both}, the record holds {sc.get("rows_both_read")}')
    # same author: this window fires on no board of the other shiwehi.com technique transcriptions (measured)
    for f in sorted(TECHNIQUE_DIR.glob('*-technique.json')):
        if f.name == OUT.name:
            continue
        other = json.loads(f.read_text())
        ospec = TT.TechniqueSpec(out=f, build=lambda: other, alphabet=frozenset(),
                                 empty_letters=other.get('empty_letters', ''), max_rows=99)
        for n in other['nodes']:
            sc2 = TT.spin_cells(n) if n['kind'] == 'spin' else set()
            pre = [''.join(EMPTY if (r, c) in sc2 or ch == 'U' else ch for c, ch in enumerate(row))
                   for r, row in enumerate(n['rows'])]
            if any(TT.window_fires(data, v, ospec, pre, cs, m) for cs in TT.t_placements(pre, ospec) for m in (False, True)):
                bad.append(f'cross: this window fires on {f.name} {n["id"]} (record it, or measure why not)')
    # cross: no routes node is labelled as this technique by its Japanese name either
    for f in sorted(HERE.glob('*-routes.json')):
        for n in json.loads(f.read_text())['nodes']:
            text = ' '.join(str(n.get(k, '')) for k in ('id', 'label', 'label_jp')).lower()
            if '社畜' in text or 'shachiku' in text or 'company train' in text:
                bad.append(f'cross: {f.name} {n["id"]} is labelled as this technique')
    return bad, measured


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='',
    extra_checks=extra_checks,
    external_drawings=external_drawings,
    html_checks=harddrop_snapshot_checks,
    # the same checks read nothing but the pinned wikitext, so a weekly api.php refetch can run them
    wikitext_checks=harddrop_snapshot_checks,
    synthetic_wikitext=lambda d: {d['cross_source']['harddrop']['snapshot_file']: _synthetic_harddrop(d),
                                   d['cross_source']['stmb_cave']['snapshot_file']: _synthetic_stmb(d)},
)


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def _set(rows, r, c, ch):
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _var(d):
    return d['variants'][0]


def _hdd(d, i):
    return d['cross_source']['harddrop']['drawings'][i]


def _hdm(d, table, board, k=0):
    return [x for x in d['cross_source']['harddrop']['drawn_t_not_fired'] if (x['table'], x['board']) == (table, board)][k]


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'u2')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: d['page_order'].reverse(), 'page_order swapped', 'grammar:'),
    (lambda d: node(d, 'u2.after').__setitem__('after_of', 'nowhere'), 'a dangling reference', 'grammar:'),
    (lambda d: _set(node(d, 'w4.build')['rows'], 4, 0, '-'), 'a derived build cell flipped', 'build:'),
    (lambda d: _set(node(d, 'dt.terrain')['rows'], 7, 9, '-'), 'a derived terrain edited', 'build:'),
    (lambda d: _set(node(d, 'dt')['rows'], 7, 9, '-'), 'a build board not its terrain plus its pieces', 'build:'),
    (lambda d: (_set(node(d, 'basic.spin')['rows'], 3, 6, 's'), _set(node(d, 'basic.spin')['rows'], 1, 6, 'U')),
     'the T pointing up', 'tsd:'),
    (lambda d: node(d, 'w4.spin').__setitem__('lines', 3), 'a TSD\'s line count', 'tsd:'),
    (lambda d: node(d, 'u2.spin').__setitem__('adds', 'Uz'), 'a T board adding more than its T', 'tsd:'),
    (lambda d: (_set(node(d, 'basic.spin')['rows'], 1, 5, '-'), _set(node(d, 'basic.build')['rows'], 1, 5, '-'),
                _set(node(d, 'basic')['rows'], 1, 5, '-')), 'the roof over the T\'s near end taken off', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [3, 9]), 'the window widened by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [5, 9]), 'the window narrowed by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [0, 4]), 'the window widened to the second slot\'s roof', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [1, 3]), 'the window without the row under the T', 'window:'),
    (lambda d: _var(d)['roof_cells'].pop(), 'a roof cell unnamed', 'window:'),
    (lambda d: _var(d)['agreement'][4].__setitem__('mirrored', False), 'DT社畜 read as drawn', 'window:'),
    (lambda d: _var(d)['agreement'][1].__setitem__('t_cells', [[2, 3], [2, 4], [2, 5], [3, 4]]),
     'a slot moved one column', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('t_cells_pre_clear', [[1, 7], [1, 8], [1, 9], [2, 8]]),
     'the follow-up\'s nub read inside the cleared rows', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('lines', 3), 'the follow-up read as a TST', 'window:'),
    (lambda d: _var(d)['misses'].append('basic.build'), 'a board it fires on listed as a miss', 'window:'),
    (lambda d: _var(d)['fires_on'].append('dt'), 'the mirrored build listed as firing as drawn', 'window:'),
    (lambda d: _var(d)['fires_mirrored'].remove('dt'), 'a board in no list', 'mirror:'),
    (lambda d: _var(d)['fires_mirrored'].append('u2'), 'a terrain listed as firing mirrored', 'mirror:'),
    (lambda d: (_set(node(d, 'w4.spin')['rows'], 0, 4, 'r'), _set(node(d, 'w4.build')['rows'], 0, 4, 'r'),
                _set(node(d, 'w4.spin')['rows'], 2, 0, '-'), _set(node(d, 'w4.build')['rows'], 2, 0, '-')),
     'the pale S drawn as no S', 'pale:'),
    (lambda d: (_set(node(d, 'basic.roofed')['rows'], 4, 8, '-'), _set(node(d, 'basic.second')['rows'], 4, 8, '-')),
     'the board between the TSDs not what the first one leaves', 'second:'),
    (lambda d: _var(d)['second_drawn'][1].__setitem__('build', 'u2.build'), 'the second T read off the wrong build',
     'second:'),
    (lambda d: _var(d)['not_expressed'][0].__setitem__('fills', 2), 'the after board read as ready for a TSD', 'later:'),
    (lambda d: _var(d)['not_expressed'][0].__setitem__('reason', ''), 'not_expressed without a reason', 'later:'),
    (lambda d: _var(d)['not_expressed'][0].__setitem__('quote', 'nope'), 'not_expressed naming no quote', 'later:'),
    (lambda d: _var(d)['not_expressed'].pop(2), 'DT社畜\'s open under-cell not listed', 'later:'),
    (lambda d: _var(d)['not_expressed'][1].__setitem__('after', 'u2.after'), 'the TST board read off the STSD one',
     'later:'),
    (lambda d: _set(node(d, 'u2.spin')['rows'], 0, 1, 'o'), 'a piece broken', 'discrepancy:'),
    (lambda d: d['known_discrepancies'].pop(), 'a measured discrepancy unnamed', 'discrepancy:'),
    (lambda d: _hdd(d, 0).__setitem__('mirrored', True), 'a harddrop drawing read mirrored', 'harddrop:'),
    (lambda d: _set(_hdd(d, 0)['rows'], 2, 4, '-'), 'a harddrop drawing\'s roof dropped', 'harddrop:'),
    (lambda d: _hdd(d, 3).__setitem__('slot', [[3, 4], [3, 5], [3, 6], [4, 5]]), 'a harddrop slot moved', 'harddrop:'),
    (lambda d: [x.__setitem__('section', VO) for x in d['cross_source']['harddrop']['drawings']],
     'the generic structure dropped', 'harddrop:'),
    (lambda d: d['cross_source']['harddrop']['drawings'].append(copy.deepcopy(_hdd(d, 0))), 'a harddrop drawing twice',
     'harddrop:'),
    (lambda d: _hdm(d, 14, 0).__setitem__('t', 'flat-down'), 'a missed drawn T\'s lie misrecorded', 'harddrop:'),
    (lambda d: _hdm(d, 11, 0).__setitem__('window', 'leaves the board'), 'why the window misses misrecorded', 'harddrop:'),
    (lambda d: _hdm(d, 1, 1).__setitem__('lines', 1), 'a missed T\'s line count misrecorded', 'harddrop:'),
    (lambda d: _hdm(d, 8, 0).__setitem__('note', ''), 'a missed drawn T with no note', 'harddrop:'),
    (lambda d: d['cross_source']['harddrop']['other_windows'].clear(), 'STMB Cave\'s window on the page unrecorded',
     'harddrop:'),
    (lambda d: d['cross_source']['stmb_cave'].__setitem__('oldid', 41495), 'the STMB_Cave revision not the pinned one',
     'stmb:'),
    (lambda d: d['cross_source']['stmb_cave']['boards'][0]['fires'].__setitem__('stmbcave', []),
     'STMB Cave\'s window on its own variation unrecorded', 'stmb:'),
    (lambda d: d['cross_source']['stmb_cave']['boards'][1]['fires'].__setitem__('shachikutrain', [True]),
     'the compared Shachiku Train read mirrored', 'stmb:'),
    (lambda d: d['cross_source']['stmb_cave']['boards'][0].__setitem__('same_as', [10, 0]),
     'the comparison read as the wrong Shachiku_Train board', 'stmb:'),
    (lambda d: d['cross_source']['stmb_cave'].__setitem__('caption', 'Compare this.'), 'the caption not the quoted one',
     'stmb:'),
    (lambda d: d['cross_source'].pop('stmb_cave'), 'no STMB_Cave record', 'stmb:'),
    (lambda d: d['cross_source']['stmb_cave']['clash'].__setitem__('as_drawn', [[2, 1]]),
     'the two windows read as clashing at the cell under the nub alone', 'stmb:'),
    (lambda d: d['cross_source']['stmb_cave'].__setitem__('rows_both_read', [-1, 0, 1, 2]),
     'the row above the T read as measured by both windows', 'stmb:'),
    (lambda d: d['cross_source']['also'].clear(), 'the stick spin board unrecorded', 'cross:'),
    (lambda d: d['cross_source'].pop('routes_fire_none'), 'no independent routes board and no reason', 'cross:'),
    (lambda d: node(d, 'dt').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['known_discrepancies'].append({'id': 'u2.spin:colour', 'note': 'x'}), 'a stale discrepancy',
     'discrepancy:'),
]


def _no_external(spec):
    s = copy.copy(spec)
    s.external_drawings = None
    return s


def _stmb_as_drawing(spec):
    s = copy.copy(spec)
    sc = build()['cross_source']['stmb_cave']['boards'][0]
    s.external_drawings = lambda: external_drawings() + [{'name': 'STMB Cave\'s variation as a drawing',
                                                          'rows': _pre(sc['rows']), 't_cells': sc['slot'],
                                                          'mirrored': False}]
    return s


SPEC_MUTANTS = [
    (_no_external, 'no external drawing (the window checked against this page alone)', 'window:'),
    (_stmb_as_drawing, 'harddrop\'s STMB Cave variation read as a drawing of the shape', 'window:'),
]


def _synthetic_wikitext(rec_boards: dict, sections: dict, captions: dict | None = None) -> str:
    """A wikitext holding the given boards at their (table, board), every other board blank, each table under its
    recorded heading — the selftest's stand-in for the pages CI cannot fetch."""
    n = max(t for t, _ in rec_boards) + 1
    tables = [[] for _ in range(n)]
    for (t, b), rows in sorted(rec_boards.items()):
        tt = tables[t]
        while len(tt) < b:
            tt.append([EMPTY * WIDTH] * 4)
        tt.append(rows)
    for tt in tables:
        if not tt:
            tt.append([EMPTY * WIDTH] * 4)
    out, last = [], None
    for i, tt in enumerate(tables):
        s = sections.get(i, last)
        if s != last:
            out.append(f'\n== {s} ==\n')
            last = s
        w = RT.synthetic_wikitext([tt])
        if captions and i in captions:
            w = w.replace('|}', f'|+ {captions[i]}\n|}}', 1)
        out.append(w)
    return '\n'.join(out)


def _synthetic_harddrop(data: dict) -> str:
    hd = data['cross_source']['harddrop']
    every = {(d['table'], d['board']): d for d in hd['drawings'] + hd['drawn_t_not_fired'] + hd['fires_without_slot']}
    return _synthetic_wikitext({k: d['rows'] for k, d in every.items()}, {k[0]: d['section'] for k, d in every.items()})


def _synthetic_stmb(data: dict) -> str:
    sc = data['cross_source']['stmb_cave']
    return _synthetic_wikitext({(sc['table'], b['board']): b['rows'] for b in sc['boards']}, {sc['table']: 'Variants'},
                               {sc['table']: sc['caption']})


def _cross_plant_problems(planted: bool) -> list[str]:
    """The `cross:` rule run with TECHNIQUE_DIR pointed at a temporary directory holding one other transcription:
    planted, a node that is this page's own TSD board (the window must fire on it); not planted, the same file with
    that board's T moved out of the window (a control: the rule must stay quiet)."""
    global TECHNIQUE_DIR
    base = build()
    spin = copy.deepcopy(next(n for n in base['nodes'] if n['id'] == base['variants'][0]['board']))
    if not planted:
        spin['rows'] = [EMPTY * len(r) for r in spin['rows']]
    fake = {'nodes': [spin], 'empty_letters': base.get('empty_letters', '')}
    saved = TECHNIQUE_DIR
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / 'planted-technique.json').write_text(json.dumps(fake))
        TECHNIQUE_DIR = Path(td)
        try:
            bad, _measured = extra_checks(base)
        finally:
            TECHNIQUE_DIR = saved
    return [x for x in bad if x.startswith('cross:')]


def selftest() -> int:
    rc = TT.run_selftest(SPEC, MUTANTS, {'board': ('cccccUUUll', 'cccccUUUlc'), 'text': ('4x2の窪み', '4x2の凹み')},
                         SPEC_MUTANTS)
    base = build()
    text, stext = _synthetic_harddrop(base), _synthetic_stmb(base)
    row = lambda r: '{{pfrow|' + '|'.join(RT.wikitext_page_cell(ch) for ch in r) + '}}'
    ok = rc == 0
    clean = harddrop_page_problems(base, text) + stmb_page_problems(base, stext)
    if clean or 'Generic Structure' not in text:
        print(f'selftest FAILED: the synthetic harddrop pages do not verify ({clean[:2]})')
        ok = False
    plants = {
        'a recorded drawing redrawn on the page': (harddrop_page_problems, text.replace(
            row(_hdd(base, 0)['rows'][3]), row(_hdd(base, 0)['rows'][3][:-1] + '-'), 1)),
        'a board the window fires on left unrecorded': (harddrop_page_problems, text.replace('|}', '|{{pfstart}} ' + ' '.join(
            row(r) for r in _hdd(base, 0)['rows']) + ' {{pfend}} |}', 1)),
        'a heading renamed': (harddrop_page_problems, text.replace('== Generic Structure ==', '== Generic Structures ==', 1)),
        'a no-T board the window fires on left unrecorded': (harddrop_page_problems, text.replace('|}', '|{{pfstart}} ' + ' '.join(
            row(r) for r in _pre(_hdd(base, 0)['rows'])) + ' {{pfend}} |}', 1)),
        'a board whose drawn cells are no T\'s': (harddrop_page_problems, text.replace('|}', '|{{pfstart}} ' + ' '.join(
            row(r) for r in ['UUU-------', 'U---------']) + ' {{pfend}} |}', 1)),
        'the STMB_Cave comparison redrawn': (stmb_page_problems, stext.replace(
            row(base['cross_source']['stmb_cave']['boards'][0]['rows'][5]), row('ggoo--gggg'), 1)),
        'the STMB_Cave caption gone': (stmb_page_problems, stext.replace('same shape and steps', 'same steps', 1)),
    }
    for label, drop in (('a drawn T the window misses left out of the record', (11, 0)),
                        ('the generic structure\'s second TSD left out of the record', (1, 1))):
        unnamed = copy.deepcopy(base)
        hd = unnamed['cross_source']['harddrop']
        k = next(i for i, x in enumerate(hd['drawn_t_not_fired']) if (x['table'], x['board']) == drop)
        hd['drawn_t_not_fired'].pop(k)
        got = harddrop_page_problems(unnamed, text)
        if not any('drawn_t_not_fired names' in x for x in got):
            print(f'selftest FAILED: {label} was not caught ({got[:2]})')
            ok = False
        else:
            print(f'  killed: {label}  [harddrop:]')
    for label, (fn, page) in plants.items():
        got = fn(base, page)
        if page in (text, stext) or not any(x.startswith(('harddrop:', 'stmb:')) for x in got):
            print(f'selftest FAILED: {label} was not caught ({got[:2]})')
            ok = False
        else:
            print(f'  killed: {label}  [{got[0].split(":")[0]}:]')
    with tempfile.TemporaryDirectory() as td:
        missing = harddrop_snapshot_checks(base, Path(td))
        (Path(td) / base['cross_source']['harddrop']['snapshot_file']).write_text(text)
        (Path(td) / base['cross_source']['stmb_cave']['snapshot_file']).write_text(stext)
        hashed = harddrop_snapshot_checks(base, Path(td))
    if (not any('is not in' in x for x in missing) or sum('hash:' in x for x in hashed) < 4):
        print(f'selftest FAILED: the harddrop snapshots (missing={missing[:2]}, hashed={hashed[:4]})')
        ok = False
    else:
        print('  killed: a harddrop snapshot missing / its bytes not the pinned revision  [harddrop: stmb:]')
    for planted, label in ((True, 'this page\'s own TSD board planted in another technique transcription'),
                           (False, 'control: the same file with that board emptied')):
        got = _cross_plant_problems(planted)
        if bool(got) != planted:
            print(f'selftest FAILED: {label}: cross: reported {got[:2]}')
            ok = False
        else:
            print(f'  {"killed" if planted else "control quiet"}: {label}  [cross:]')
    print('selftest: harddrop checks all caught' if ok else 'selftest: FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))

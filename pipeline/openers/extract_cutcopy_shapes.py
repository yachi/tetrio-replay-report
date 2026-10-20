"""Transcribe shiwehi.com's 千鳥格子 (Cut Copy) page into `cutcopy-technique.json`.

    python3 -m pipeline.openers.extract_cutcopy_shapes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_cutcopy_shapes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_cutcopy_shapes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_cutcopy_shapes --html-dir <dir> --write  # ...and rewrite

The sixth MID-GAME TECHNIQUE page (中盤テンプレ・ドネイト), after STSD, STMB Cave, インペリアルクロス, ダブルダガー and
BT砲: 「TSDを2回打つことができる中盤テンプレ」. Two TSD slots interleaved one column apart: the T goes in laid
FLAT, pointing down, into the inner slot (its arms one row, its nub the row under), under a roof over its right
end; its two cleared rows drop the outer slot's arms row onto the outer slot's nub cell, which is the second TSD
(the page: 「もう一度TSDを打てる形が残ります」). harddrop calls it Cut copy and says the same thing: the second
T-Spin is "cut" by the first, and only its bottom half is saved underneath.

DECISION: the spin is a TSD (a full T-spin, 2 lines) and the anchor is the T's four cells — the T laid flat, nub
down, as STMB Cave's, ダブルダガー's and BT砲's. So the window predicate expresses it and the matcher
(`technique-facts.ts`) is untouched. The follow-up is a second TSD whose four cells are split by the two cleared
rows before the first one fires (three above them, one under them); the matcher's row map joins them, as it does
for BT砲's TST, so nothing shared changed. The page writes 「縦向きに入れて」 (put the T in upright) and DRAWS it
flat: OUR READING is that the T drops in upright and turns into the drawn flat slot; the window reads the drawing.

WHY THE WINDOW IS THE AGREEMENT BOX (`window_basis: agreement`, STMB Cave's opt-in), not STSD's bounding box. The
spin board draws the whole stack left of the slots as filled rows above the T, so every one of those cells is a
"roof cell" and STSD's rule would make the window the whole board. So the window is the box on which every drawing
of the shape agrees: this page's three (the basic form, and its two builds, both drawn MIRRORED), six from
harddrop (another site, other authors): five on its own Cut_copy page, pinned below, and the one its BT_Cannon
page draws, read from `btcannon-technique.json` (this read 「seven」 until 2026-10-20: five and one are six), and
two of Tetrisちゃんねる's (below). It comes out four rows by six columns: the outer slot's arms row
with the inner slot's roof beside it, the two rows the TSD clears, and the outer slot's nub row under them.
Widening it meets a disagreement (above it, harddrop's and the page's builds fill the two cells the basic form
leaves open over the roof) or leaves a drawing (left, the second build sits against the wall; right and down, the
basic form ends).

WHERE THE TRANSCRIPTION COMES FROM. `NODES` is a literal, hand-checked transcription of the page's RAW HTML,
fetched the way STSD's was: curl through the session proxy, TLS verification on, with a CA bundle adding the
Let's Encrypt YE2 intermediate shiwehi.com omits. Five boards, plain text in `<div class="ttt">`, one row per line.
The page is not committed; CI cannot fetch it. harddrop's page (the one the page itself cites, 「Cut copy - Hard
Drop」) is read as the pinned revision's own bytes from the MediaWiki API (urllib, a descriptive User-Agent, never
curl), the way BT砲's and SDPC Spin's were.

NO GATE RULE CHANGED. Every rule here is the shared gate's or this module's `extra_checks`; the harddrop reading
(`hd_cell`, `_sections`) is imported from BT砲's module so the two harddrop transcriptions read one cell code one
way. harddrop's Cut_copy page draws one board with THREE T's on it (yakine's repeating pattern), which BT砲's
page-completeness check (one drawn T per board) cannot read, so this module partitions every board's drawn cells
into T's and records each T on its own (`slot`).

WHAT THE WINDOW DOES NOT EXPRESS, measured and named rather than fitted (`not_expressed`): the page's own
sentence 「(Z)は1回目のT-spinを打った後に置いても構いません」 — the T-hole build's Z may go in after the first
T-spin. One of its cells (`decides`) is the outer slot's wall beside its arms row, which every drawing fills; the
window reads no other cell of that Z, so with the Z left out it fires nowhere on the build (`extra_checks` measures
both: which cells of the Z decide, and that the build less the Z fires nowhere), and a Cut Copy built that way is no hit.

A SECOND VARIANT, harddrop's (`uncut`). harddrop's page draws TWO generic Cut Copies: the first type above, and the
second, 「Uncut copy」, where the WHOLE second TSD slot is saved under the first T rather than its bottom half (its
arms one row under the two cleared rows, one column toward the roofless side; its nub under them). shiwehi.com draws
only the first. Measured, a single-T window expresses the second as well: anchored on the same flat T it is the
agreement box of harddrop's eight drawings of it (its Generic Structures board, the S/Z/J variation of fumen #3 twice,
the two T's of its repeat, one T of yakine's repeating pattern, the second T of the three-TSD mix, and the T under an
STSD), five rows by six columns: the row above the T (the slot and its walls), the two rows the TSD clears, and the
second slot's arms row and nub row under them. Its follow-up is that second slot, whose cells the first TSD does not
split (they are under it). The variant's board is harddrop's own Generic Structures drawing, transcribed into this
file as an EXTERNAL node (`external: harddrop`, never in `page_order`, which is shiwehi.com's page) in occupancy only,
with the after board harddrop draws beside it; `extra_checks` holds both to the harddrop record letter for letter
by occupancy. Its window clashes with the first type's on a cell (the second slot's arm beside the nub), so no lock
is a hit of both. It fires, mirrored, on the STMB Cave page's own 「TSDの地形でSTMB caveを行うと連続してTSDを狙うことが
できます」 boards (`stmbcave-technique.json` `feature.spin`, and `feature.pre`, the same board before its T): harddrop
says the second type 「could be easily mistaken with STMB Cave」, and on that page the two are the same board. Recorded
(`also_technique`), not fitted. harddrop's own STMB Cave comparison (table 3 board 1, its cave two rows deep) is no
hit: the window walls the second slot's nub.

WHAT ELSE harddrop's page draws, decided by measurement and kept with its reason (`drawn_t_not_fired`): the stood T
on the L-built board after the Parapet comparison (a TSS; the window's T is flat), the second and third T's of
yakine's pattern (read with every T empty, the board never stands at once; the third's window leaves the board), and
the four Donation boards (a donation, not a Cut Copy slot under the T). The deeper-hole S variation (table 4 board 3,
again table 5 board 1) is no separate variant: it is a drawing of the first type's window already.

Tetrisちゃんねる (`cross_source.tetrisch`, another site and author): its 千鳥格子 page's ten images, committed under
`spec/fixtures/tetrisch-cutcopy/` and read with the jp-forecast pixel sampler, as 欄干's are. 001-007 are the basic
sequence: the terrain, the T dropped UPRIGHT into the hole (002), the same T turned flat into the TSD slot (003: the
two T's share their centre, which is the shiwehi page's 「縦向きに入れて」, now drawn by a second site), what it leaves
(004), the second T upright (005) and flat (006: the follow-up slot), and what that leaves (007). 008 is 001's board
coloured by which TSD each row belongs to (its colours mark rows, not pieces; same occupancy, checked). 009 is 江戸城
(Edo Castle): three TSDs nested, 「TSDをTSDで挟んだような地形」. Measured, it is NOT a new shape: the window fires on it
once, as drawn, at the innermost T; that TSD's follow-up slot is the middle T, and on the board the first TSD leaves the
window fires again, MIRRORED, at the middle T, whose own follow-up slot is the outer T — so 江戸城 is two Cut Copies in
a row, in alternating hands (the page's own 「交互にずれている」), and the matcher already reads it as a hit whose
follow-up lock is itself a hit. 010 overlays the two columns the T needs kept open; the sampler refuses it (an
annotation). The upright and plain T's are no window's T (stood), and the window fires on no bare terrain or after
board.

DECLINED (`source.declined`): howtotetris.com's Cut Copy lesson and four.lol were checked and not used: both state
that all rights are reserved and no part may be reproduced without permission, so none of their diagrams is
transcribed, committed or published.

WHAT IS AN INFERENCE, flagged in the JSON (`reading`, the legend) rather than in prose only:

  * upper-case `C` and `T` in a spin board: the cleared rows, muted (checked by the spin rule).
  * the page draws what the first TSD leaves only with the second T already in (`second.spin`); the board between
    them, which the page does not draw, is DERIVED (`basic.after`, that board less its T) and measured to be what
    the first TSD leaves.
  * the two builds' grey terrains are DERIVED (each build less its page pieces).
  * harddrop's cell codes: `P` is the placed T (read `U`), blank empty, every other code its last letter in lower
    case, every one filled (BT砲's reading, imported).
  * the external `uncut` nodes: harddrop's drawings in occupancy only (`c`, `C` in the cleared rows, `T`).
  * Tetrisちゃんねる's images: the sampler's letters; 008's and 009's colours mark which TSD a row belongs to.
"""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import tempfile
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers import technique_transcription as TT
from pipeline.openers.extract_btcannon_shapes import _sections, hd_cell
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS
from pipeline.openers.route_transcription import EMPTY, WIDTH, after_spin, bottom
from pipeline.openers.technique_transcription import node

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT = HERE / 'cutcopy-technique.json'
#: Tetrisちゃんねる's ten images, committed byte for byte
IMG_DIR = REPO / 'spec' / 'fixtures' / 'tetrisch-cutcopy'
#: where the `cross:` rule reads the other technique transcriptions; the selftest points it at a planted one
TECHNIQUE_DIR = HERE
BT_FILE = 'btcannon-technique.json'

ALPHABET = frozenset('-cCTjosz')


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/cutcopy.php',
    'title': '千鳥格子(Cut Copy)',
    'author': 'しゑひ(shiwehi)',
    'published': '2020-10-11',
    'updated': '2020-10-14',
    'fetched': '2026-10-17',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle '
                    'that adds the Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), '
                    'the method STSD, STMB Cave, インペリアルクロス, ダブルダガー, BT砲, 山岳積み2号 and stick spin used. '
                    'The snapshot is the page\'s raw HTML, byte for byte; every board is plain text in it, 5 '
                    'ten-wide boards in page order.',
    'snapshot_file': 'cutcopy.html',
    'snapshot_sha256': '7e8326ddd334fa9cd62fb728e2f2682a2e97e6ea6f99c57a7357c2c02eaad83c',
    'snapshot_bytes': 24010,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable '
                     'in CI: the page is not committed and cannot be fetched there. Re-check with '
                     '--html-dir after any refetch (with harddrop\'s Cut_copy.wikitext beside it); an HTML '
                     'hash moves with ANY byte of the page (ads, sidebar, a date), so a moved hash means "read '
                     'the board diff", not "the boards changed". Sentences are compared against the page with '
                     'its tags dropped.',
    'decorative_images': ['千鳥格子(Cut Copy)タイトル画像'],
    'commented_out': ['a 動画版解説 section (a video by I凜, embedded with permission) inside an HTML comment: not '
                      'rendered, not transcribed'],
    'references': ['https://harddrop.com/wiki/Cut_copy (the page\'s own 参考ページ, read below as cross_source.harddrop)'],
    'unfetched': [],
    #: other sites checked for more drawings of the technique and NOT used, each with why
    'declined': [
        {'url': 'https://howtotetris.com/11-cut-copy', 'checked': '2026-10-20',
         'reason': 'the site states 「All Rights Reserved. No part of this site or its content may be reproduced, '
                   'distributed, or published without permission.」: checked, and none of its diagrams is transcribed, '
                   'committed or published'},
        {'url': 'https://four.lol/', 'checked': '2026-10-20',
         'reason': 'the site reserves all rights (no reproduction without permission), and its methods index lists no '
                   'Cut Copy page (/methods/cut-copy answers 404): checked, and nothing of it is used'},
    ],
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ',
    '-': 'empty',
    'c': 'a cell filled before this diagram (any piece, or garbage), grey',
    'j o s z': 'a cell of that piece, placed to build the shape',
    'T': 'a cell of the T in a row the spin clears (muted; OUR READING, checked: every upper-case row is a full row)',
    'C': 'an earlier cell in a row the spin clears (muted; checked the same way)',
    '%X': 'the X piece',
}

QUOTES = [
    {'id': 'intro', 'verbatim': 'ここでは、千鳥格子(Cut Cpoy)という、TSDを2回打つことができる中盤テンプレについて紹介していきます。',
     'typo_note': 'the page writes 「Cut Cpoy」 here and 「Cut Copy」 in its title; quoted as written'},
    {'id': 'h.basic', 'verbatim': '基本形とラインの消し方'},
    {'id': 'basic', 'verbatim': '基本形は上図の通りです。'},
    {'id': 'spin', 'verbatim': 'ここから、以下のようにを縦向きに入れてTSDを打つと、もう一度TSDを打てる形が残ります。',
     'icons': ['%T'],
     'icons_note': 'the page draws the T as a mino icon (<span class="mino tmino">) in the gap 「ように_を縦向きに」; the '
                   'text drops it. Not used as a caption. 縦向き (upright) against a T the boards draw flat: OUR READING '
                   'is that the T drops in upright and turns into the flat slot; the window reads the drawing'},
    {'id': 'h.build', 'verbatim': '元地形からの組み方と特徴'},
    {'id': 'build', 'verbatim': 'あまり自分で形を組んでいく形ではなく、穴がせり上がってきたときなどに組むことが多い。'},
    {'id': 'h.hole', 'verbatim': 'T穴からの組み方'},
    {'id': 'hole', 'verbatim': 'Tの形の穴がある場合、()を穴からずらして置くことで、千鳥格子を組むことができます。',
     'icons': ['%S', '%Z'],
     'icons_note': 'the page draws the two pieces as mino icons in the gaps 「場合、_(_)を」; the text drops them. Not '
                   'used as a caption.'},
    {'id': 'z_later', 'verbatim': 'は1回目のT-spinを打った後に置いても構いません。',
     'icons': ['%Z'],
     'icons_note': 'the sentence opens with a %Z mino icon the text drops. Not used as a caption; it is the reason for '
                   'the variant\'s not_expressed entry'},
    {'id': 'h.col3', 'verbatim': '3列目穴からの組み方'},
    {'id': 'col3', 'verbatim': '4列目でT-spinを組もうと思っていた時に、3列目穴がせり上がってきた場合、LST積みの要領で、を端2列に組むことで、'
                               '千鳥格子を組むことができます。',
     'icons': ['%J', '%Z'],
     'icons_note': 'the page draws the two pieces as mino icons in the gap 「要領で、__を端2列に」; the text drops them. '
                   'Not used as a caption.'},
    {'id': 'h.ref', 'verbatim': '参考ページ'},
    {'id': 'ref', 'verbatim': 'Cut copy - Hard Drop'},
]

NODES = [
    {'id': 'basic', 'kind': 'base', 'caption_quote': 'basic',
     'label': 'the basic form: two TSD slots interleaved one column apart, the inner one roofed over its right end',
     'rows': _b('---------- ----cc---- ccccc---cc cccccc---c ccccccc-cc cccccc-ccc')},
    {'id': 'basic.spin', 'kind': 'spin', 'spin_of': 'basic', 'spin': 'TSD', 'lines': 2, 'caption_quote': 'h.basic',
     'label': 'the T laid flat, pointing down, into the inner slot: a TSD',
     'rows': _b('---------- ----cc---- ccccc---cc CCCCCCTTTC CCCCCCCTCC cccccc-ccc')},
    {'id': 'second.spin', 'kind': 'spin', 'spin_of': 'basic.after', 'on': 'basic.after', 'adds': 'T', 'spin': 'TSD',
     'lines': 2, 'caption_quote': 'h.basic',
     'label': 'what the TSD leaves, with the second T laid flat into the outer slot: a second TSD (the page draws this '
              'board, not the one before it)',
     'rows': _b('---------- ---------- ---------- ----cc---- CCCCCTTTCC CCCCCCTCCC')},
    {'id': 'hole.osz', 'kind': 'build', 'on': 'hole.terrain', 'adds': 'osz', 'caption_quote': 'h.hole',
     'label': 'from a T-shaped hole: an S laid beside the hole, offset by a column, an O and a Z over it (mirrored)',
     'rows': _b('---------- ---oo--zz- cccoo---zz cccc---ssc ccccc-sscc cccccc-ccc')},
    {'id': 'col3.jz', 'kind': 'build', 'on': 'col3.terrain', 'adds': 'jz', 'caption_quote': 'h.col3',
     'label': 'a hole in the third column risen under a TSD slot: a J and a Z stacked against the wall (mirrored)',
     'rows': _b('---------z --------zz --------zj ----cc---j ccccc---jj cccccc-ccc ccccccc-cc')},
    # ── derived: drawn nowhere on the page ──
    {'id': 'basic.after', 'kind': 'derived', 'derived': True,
     'reading': 'second.spin less its T: what the first TSD leaves (measured to be basic.spin after its clear, by '
                'occupancy); its rows the second TSD clears are drawn muted, as the page draws them on second.spin',
     'rows': _b('---------- ---------- ---------- ----cc---- CCCCC---CC CCCCCC-CCC')},
    {'id': 'hole.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'hole.osz less its O, S and Z: the T-shaped hole the page builds from',
     'rows': _b('---------- ---------- ccc------- cccc-----c ccccc---cc cccccc-ccc')},
    {'id': 'col3.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'col3.jz less its J and Z: the TSD slot with the hole risen under it, the right two columns open',
     'rows': _b('---------- ---------- ---------- ----cc---- ccccc----- cccccc-ccc ccccccc-cc')},
    # ── external: harddrop's second generic type, drawn nowhere on this page ──
    {'id': 'uncut.spin', 'kind': 'spin', 'external': 'harddrop', 'source_board': {'table': 1, 'board': 3},
     'spin': 'TSD', 'lines': 2,
     'label': 'harddrop\'s second generic type, 「Uncut copy」: the flat T into the upper slot, the whole second TSD slot '
              'saved under it',
     'reading': 'harddrop Cut_copy table 1 board 3 (Generic Structures) in occupancy only: every drawn cell c, C in the '
                'rows the TSD clears, its P the T',
     'rows': _b('---------- cc--cccccc CCTTTCCCCC CCCTCCCCCC c---cccccc cc-ccccccc')},
    {'id': 'uncut.after', 'kind': 'after', 'after_of': 'uncut.spin', 'external': 'harddrop',
     'source_board': {'table': 1, 'board': 4},
     'label': 'what the first TSD leaves: the second slot, roofed by the row that dropped onto it',
     'reading': 'harddrop Cut_copy table 1 board 4 in occupancy only',
     'rows': _b('---------- ---------- ---------- cc--cccccc c---cccccc cc-ccccccc')},
]

#: the variant's window, in basic.spin's frame
VARIANTS = [{
    'id': 'cutcopy', 'board': 'basic.spin', 'spin': 'TSD', 'lines': 2,
    'window_basis': 'agreement',
    'window': {'rows': [2, 5], 'cols': [4, 9]},
    't_cells': [[3, 6], [3, 7], [3, 8], [4, 7]],
    'roof_cells': [[2, 4], [2, 8], [2, 9]],
    'window_note': 'in basic.spin\'s frame, row 0 the top: the AGREEMENT BOX of this page\'s three drawings of the shape, '
                   'harddrop\'s six and Tetrisちゃんねる\'s two. Row 2 is the outer slot\'s arms row: its three cells empty, the wall beside them '
                   'filled, and on the other side the roof over the T\'s right end and the cell beyond it filled; rows 3-4 '
                   'are the rows the TSD clears (entailed by the clear at a full TSD, NaiveClauseForced); row 5 the outer '
                   'slot\'s nub cell, under the T\'s left arm, walled both sides. The outer slot\'s roof (the row above) '
                   'is outside: harddrop\'s and the page\'s builds fill the cells the basic form leaves open there. '
                   'Occupancy only, never colour; garbage is filled.',
    'untested_drawn': {'cells': [], 'reason': ''},
    'agreement': [
        {'board': 'basic', 't_cells': [[3, 6], [3, 7], [3, 8], [4, 7]], 'mirrored': False},
        {'board': 'hole.osz', 't_cells': [[3, 4], [3, 5], [3, 6], [4, 5]], 'mirrored': True},
        {'board': 'col3.jz', 't_cells': [[4, 5], [4, 6], [4, 7], [5, 6]], 'mirrored': True},
    ],
    'followup': {'board': 'basic.after', 'spin': 'TSD', 'lines': 2,
                 't_cells_pre_clear': [[2, 5], [2, 6], [2, 7], [5, 6]],
                 't_cells_after': [[4, 5], [4, 6], [4, 7], [5, 6]],
                 'note': 'the flat T, pointing down, into the outer slot. Before the TSD its cells are split by the two '
                         'cleared rows (its arms above them, its nub under them); the TSD joins them, and the matcher '
                         'carries the slot through every later clear to the next T.'},
    'fires_on': ['basic'],
    #: the page's mirrored drawings: the window fires on each exactly once, mirrored (`extra_checks`; the shared
    #: rule (e) takes only as-drawn boards)
    'fires_mirrored': ['hole.osz', 'col3.jz'],
    'misses': ['second.spin', 'basic.after', 'hole.terrain', 'col3.terrain', 'uncut.spin', 'uncut.after'],
    #: a Cut Copy the page describes and the window does not fire on: measured, not fitted
    'not_expressed': [
        {'board': 'hole.osz', 'less': 'z', 'quote': 'z_later', 'decides': [[2, 8]],
         'reason': 'the page lets the T-hole build\'s Z go in after the first T-spin. One of its cells (`decides`) is '
                   'the outer slot\'s wall beside its arms row, which every drawing fills; the window reads none of its '
                   'other three, so with the Z left out the window fires nowhere on the build: a Cut Copy built in that '
                   'order is no hit'},
    ],
}, {
    'id': 'uncut', 'board': 'uncut.spin', 'spin': 'TSD', 'lines': 2,
    'window_basis': 'agreement',
    'window': {'rows': [1, 5], 'cols': [0, 5]},
    't_cells': [[2, 2], [2, 3], [2, 4], [3, 3]],
    'roof_cells': [[1, 0], [1, 1], [1, 4], [1, 5]],
    'window_note': 'in uncut.spin\'s frame (harddrop\'s Generic Structures drawing), row 0 the top: the AGREEMENT BOX of '
                   'harddrop\'s eight drawings of the second type. Row 1 is the row above the T: open over its left arm '
                   'and middle, filled over its right arm (the overhang) and beyond it, and filled two cells to the left; '
                   'rows 2-3 the rows the TSD clears (entailed by the clear at a full TSD, NaiveClauseForced); rows 4-5 '
                   'the second slot, whole, one column toward the open side: its arms row walled both sides, its nub '
                   'walled both sides. Occupancy only, never colour; garbage is filled.',
    'untested_drawn': {'cells': [], 'reason': ''},
    'agreement': [],
    'followup': {'board': 'uncut.after', 'spin': 'TSD', 'lines': 2,
                 't_cells_pre_clear': [[4, 1], [4, 2], [4, 3], [5, 2]],
                 't_cells_after': [[4, 1], [4, 2], [4, 3], [5, 2]],
                 'note': 'the flat T, pointing down, into the second slot under the cleared rows. The first TSD does not '
                         'split it (it is under both cleared rows), and the row above the T drops onto it as its roof.'},
    'fires_on': [],
    #: every board of shiwehi.com's page, and what the second type's TSD leaves: the second type's window fires on none
    'misses': ['basic', 'basic.spin', 'second.spin', 'hole.osz', 'col3.jz', 'basic.after', 'hole.terrain',
               'col3.terrain', 'uncut.after'],
}]


def _hd(variant: str, table: int, board: int, section: str, mirrored: bool, slot: list, rows: str,
        note: str | None = None) -> dict:
    e = {'variant': variant, 'table': table, 'board': board, 'section': section, 'mirrored': mirrored, 'slot': slot,
         'rows': _b(rows)}
    if note:
        e['note'] = note
    return e


def _miss(table: int, board: int, section: str, slot: list, t: str, lines: int, window: str, note: str,
          rows: str, other_window: dict | None = None) -> dict:
    e = {'table': table, 'board': board, 'section': section, 'slot': slot, 't': t, 'lines': lines,
         'window': window, 'note': note, 'rows': _b(rows)}
    if other_window:
        e['other_window'] = other_window
    return e


GS, VO = 'Generic Structures', 'Variations, Other Uses and Comparisons'
_YAKINE = ('yakine\'s repeating pattern of the second type: three T\'s drawn on one board, read with all three slots '
           'empty (a board that never stands at once)')
_DONATION = '「Using Cut copy along with Donation」: a donation, not the first type\'s slot under the T'

#: harddrop's Cut_copy page: every board on it with a drawn T (`P`) a window fires on, read with `hd_cell`, each
#: naming the variant it is a drawing of
HARDDROP = {
    'page': 'https://harddrop.com/wiki/Cut_copy',
    'title': 'Cut copy',
    'oldid': 41553,
    'revision_sha1': '6ae90fe69461e63a769266f9b40da0863ebf6eb0',
    'revision_timestamp': '2024-12-27T16:34:13Z',
    'fetched': '2026-10-19',
    'fetch_method': 'the latest revision\'s own bytes from the MediaWiki API (api.php?action=query&prop=revisions&'
                    'titles=Cut_copy&rvprop=ids|sha1|size|timestamp|content&rvslots=main), with Python\'s urllib and a '
                    'descriptive User-Agent (NOT curl); the API\'s sha1 equals the sha1 of the bytes, and 41553 was the '
                    'page\'s latest revision when fetched',
    'snapshot_file': 'Cut_copy.wikitext',
    'snapshot_sha256': '25520605b93ebe009bf203dcee3e4d9197e42e5c728dd4bf08cd7b642f201940',
    'snapshot_bytes': 14323,
    'snapshot_note': 'not committed: check_wikitext_sources refetches the pinned revision weekly through api.php and '
                     're-checks it with --wikitext-dir; a person re-checks it with --html-dir, the file beside '
                     'cutcopy.html',
    'author_note': 'harddrop\'s page, edited by its wiki editors (it credits the repeating pattern to yakine): another '
                   'site and other authors than shiwehi.com, and the page shiwehi.com cites as its reference',
    'reading': {'blank': '-', 'P': 'U, the T placed into the spin (the slot the agreement rule fires the window at)',
                'other': 'any other code, its last letter in lower case (G grey), every one FILLED (BT砲\'s hd_cell)',
                'slots': 'a board\'s U cells are partitioned into T\'s; each T is one slot, read with every U cell of '
                         'the board empty'},
    'drawings': [
        _hd('cutcopy', 0, 3, GS, False, [[4, 3], [4, 4], [4, 5], [5, 4]],
            '---------- --z------- -zz--oo--l gz---oolll gzzUUUgggg ggzzUggggg ggg-gggggg'),
        _hd('uncut', 1, 3, GS, False, [[2, 2], [2, 3], [2, 4], [3, 3]],
            '---------- gg--zzgggg ggUUUzzggg lllUoogggg l---oogggg gg-ggggggg',
            'the page\'s second type, 「Uncut copy」: the whole second T-Spin Double saved underneath (the external node '
            'uncut.spin is this board)'),
        _hd('uncut', 2, 3, VO, False, [[3, 2], [3, 3], [3, 4], [4, 3]],
            '---------- oo--s----- oo--ssgggg zzUUUsgggg gzzUjggggg g---jggggg gg-jjggggg',
            '「Cut copy could be made using pieces other than the generic structure」 (fumen #3, S/Z/J): the second '
            'type\'s full slot under the T'),
        _hd('uncut', 3, 0, VO, False, [[3, 2], [3, 3], [3, 4], [4, 3]],
            '---------- oo--s----- oo--ssgggg zzUUUsgggg gzzUjggggg g---jggggg gg-jjggggg',
            'the same variation again, beside STMB Cave for comparison'),
        _hd('cutcopy', 4, 3, VO, False, [[4, 3], [4, 4], [4, 5], [5, 4]],
            '---------- --z------- -zz------- gz---ggggg ggsUUUgggg ggssUggggg ggg-gggggg'),
        _hd('cutcopy', 5, 1, VO, False, [[4, 3], [4, 4], [4, 5], [5, 4]],
            '---------- --z------- -zz------- gz---ggggg ggsUUUgggg ggssUggggg ggg-gggggg'),
        _hd('uncut', 7, 1, VO, False, [[4, 3], [4, 4], [4, 5], [5, 4]],
            '---------- ------z--- -oo--zz--- joo--zl--- jjjUUUlggg iiiiUllggg gg---ssggg ggg-ssgggg ggg---gggg '
            'gggg-ggggg',
            '「Repeating the second type of Cut copy」: the first T, over the second type\'s full slot'),
        _hd('uncut', 7, 2, VO, True, [[6, 2], [6, 3], [6, 4], [7, 3]],
            '---------- ---------- ---------- ------z--- -oo--zz--- joo--zl--- ggUUUssggg gggUssgggg ggg---gggg '
            'gggg-ggggg',
            'the same repeat, its second T over the next full slot: the first T\'s follow-up is itself a second-type '
            'Cut Copy, mirrored'),
        _hd('uncut', 8, 1, VO, True, [[3, 3], [3, 4], [3, 5], [4, 4]],
            '---------- ggoo---zgg ggoo--zzgg ggsUUUzlgg ggssUlllgg ggjsUUUzgg ggjjjUzzgg gggUUUzlgg ggggUlllgg',
            _YAKINE + '; its first T'),
        _hd('cutcopy', 9, 1, VO, False, [[4, 3], [4, 4], [4, 5], [5, 4]],
            '---------- --z------- -zz--lllgg jz---loogg jjjUUUoogg iiiiUssggg ggg-ssgggg ggg---gggg gggg-ggggg'),
        _hd('uncut', 9, 2, VO, True, [[5, 2], [5, 3], [5, 4], [6, 3]],
            '---------- ---------- ---------- --z------- -zz--lllgg jzUUUloogg gggUssgggg ggg---gggg gggg-ggggg',
            '「mix both types of Cut copy to make three consecutive T-Spin Doubles」: the second T, over the second '
            'type\'s full slot (the first T, board 1, is a first-type drawing)'),
        _hd('cutcopy', 11, 2, VO, True, [[7, 4], [7, 5], [7, 6], [8, 5]],
            '---------- ----jj---- g---j----- g---j-zzll giiii--zzl ggggg--ggl ggggg---gg ggggUUUggg gggggUgggg '
            'gggggg-ggg'),
        _hd('uncut', 12, 2, VO, False, [[6, 3], [6, 4], [6, 5], [7, 4]],
            '---------- i-ss------ iss----ggg ioo-jjjggg ioo--gjggg ggg--ggggg gggUUUgggg ggggUggggg gg---ggggg '
            'ggg-gggggg',
            '「make a Cut copy underneath an STSD」, its second drawing: the T over the second type\'s full slot'),
    ],
    #: every OTHER drawn T on the page: no window fires at it in either hand, each named with what the T is,
    #: measured (`t` its lie, `lines` the rows it clears as drawn, `window` why no window fires: not a window's T,
    #: every window leaves the board, or a cell disagrees) and a note read off the page around it. With `drawings`
    #: this is EVERY drawn T on the page
    'drawn_t_not_fired': [
        _miss(3, 1, VO, [[3, 2], [3, 3], [3, 4], [4, 3]], 'flat-down', 2, 'disagrees',
              'STMB Cave, drawn beside the variation for comparison (「Compare the variation of Cut copy above with STMB '
              'Cave」): its cave is two rows deep, where the second type walls its nub',
              '---------- ----s----- ----ssgggg zzUUUsgggg gzzUoogggg g---oogggg g---gggggg'),
        _miss(6, 1, VO, [[3, 4], [4, 4], [4, 5], [5, 4]], 'stood', 1, "not the window's T",
              'a stood T into one row, on the L-built board drawn after the Parapet comparison: a TSS, where both '
              'windows\' T is flat. Measured, 欄干\'s TSS window fires at exactly this T, as drawn (`other_window`): it '
              'is a Parapet TSS drawn on the Cut copy page, not a Cut Copy',
              '---------- -jj------- -j-------- gjl-Uggggg ggl-UUgggg ggllUggggg ggg-gggggg ggg-gggggg',
              {'file': 'parapet-technique.json', 'variant': 'parapet_tss', 'mirrored': False}),
        _miss(8, 1, VO, [[5, 4], [5, 5], [5, 6], [6, 5]], 'flat-down', 2, 'disagrees', _YAKINE + '; its second T',
              '---------- ggoo---zgg ggoo--zzgg ggsUUUzlgg ggssUlllgg ggjsUUUzgg ggjjjUzzgg gggUUUzlgg ggggUlllgg'),
        _miss(8, 1, VO, [[7, 3], [7, 4], [7, 5], [8, 4]], 'flat-down', 2, 'leaves the board', _YAKINE + '; its third T',
              '---------- ggoo---zgg ggoo--zzgg ggsUUUzlgg ggssUlllgg ggjsUUUzgg ggjjjUzzgg gggUUUzlgg ggggUlllgg'),
        _miss(10, 0, VO, [[4, 4], [4, 5], [4, 6], [5, 5]], 'flat-down', 2, 'disagrees', _DONATION,
              '---------- ---------- ---oo----- ---oo----- iiiiUUUssz jjjggUsszz --jggg-gz-'),
        _miss(10, 1, VO, [[3, 3], [3, 4], [3, 5], [4, 4]], 'flat-down', 2, 'disagrees', _DONATION,
              '---------- -----oo-l- -----oo-l- gzzUUUssll ggzzUssgjj gg---gggj- ggg-ggggj-'),
        _miss(10, 2, VO, [[4, 5], [4, 6], [4, 7], [5, 6]], 'flat-down', 2, 'disagrees', _DONATION,
              '---------- ---------- g--------- g------zz- giiiiUUUzz glllssUggg gl-ss-gggg'),
        _miss(10, 3, VO, [[3, 4], [3, 5], [3, 6], [4, 5]], 'flat-down', 2, 'disagrees', _DONATION,
              '---------- ---------- -j----zz-i sjjjUUUzzi sslllUgggi -sl---gggi -ggg-ggggg'),
    ],
    #: the after board harddrop draws beside its second type (the external node uncut.after is this board)
    'after_drawn': [
        _hd('uncut', 1, 4, GS, False, [], '---------- ---------- ---------- gg--zzgggg l---oogggg gg-ggggggg',
            'what the second type\'s first TSD leaves: the second slot, roofed by the row that dropped onto it'),
    ],
    #: boards with no T drawn on which a window fires at a resting placement: the same shape one step before
    #: the page draws its T, recorded letter for letter; `mirrored` is the hand it fires in
    'fires_without_slot': [
        _hd('cutcopy', 0, 2, GS, False, [[4, 3], [4, 4], [4, 5], [5, 4]],
            '---------- --z------- -zz--oo--l gz---oolll gzz---gggg ggzz-ggggg ggg-gggggg'),
        _hd('uncut', 1, 2, GS, False, [[2, 2], [2, 3], [2, 4], [3, 3]],
            '---------- gg--zzgggg gg---zzggg lll-oogggg l---oogggg gg-ggggggg'),
        _hd('uncut', 2, 2, VO, False, [[3, 2], [3, 3], [3, 4], [4, 3]],
            '---------- oo--s----- oo--ssgggg zz---sgggg gzz-jggggg g---jggggg gg-jjggggg'),
        _hd('cutcopy', 11, 1, VO, True, [[7, 4], [7, 5], [7, 6], [8, 5]],
            '---------- ---------- g--------- g--------- g--------- gggoo--zz- gggoo---zz gggg---ssg ggggg-ssgg '
            'gggggg-ggg'),
        _hd('uncut', 12, 1, VO, False, [[5, 3], [5, 4], [5, 5], [6, 4]],
            '---------- -------ggg -------ggg -----s-ggg goo--ssggg goo---sggg glll-ggggg gl---ggggg ggg-gggggg'),
    ],
}

#: Tetrisちゃんねる's 千鳥格子 page: its text and its ten images, committed under spec/fixtures/tetrisch-cutcopy/
_TC_IMAGES = [
    ('001', '4680ef5d4f0712e1bbb738cc37334ffa14f39fc8da60e567f074db5bbd2fb206', 33387,
     '.......... .......... .......... ###..##### ##...##### ###...#### ####.##### ###.######'),
    ('002', 'addbc3b6a1010059bbf0b17a2649cddfd3b84318a8b15e44c715172b76da35d2', 34226,
     '.......... .......... .......... ###..##### ##..T##### ###TT.#### ####T##### ###.######'),
    ('003', 'a29c32639ba1aa2bb0de0944fd4dc6f0cfc9f2006d0cfb7fa43797488bc03348', 34473,
     '.......... .......... .......... ###..##### ##...##### ###TTT#### ####T##### ###.######'),
    ('004', '3b807900ad66c6e5fe5bc915ed8f7b86dc2b26fc6a81feeb9e0bc308ca365fad', 32923,
     '.......... .......... .......... .......... .......... ###..##### ##...##### ###.######'),
    ('005', '01d0bf6a542d5a67ba4ed1a0c616b8f855f87d596f62d68e390654d0633acc7f', 34475,
     '.......... .......... .......... .......... .......... ###T.##### ##.TT##### ###T######'),
    ('006', '0bc66823cefa1c71e2009191c0852423e641f6846603693bfd93d010b55151cc', 33648,
     '.......... .......... .......... .......... .......... ###..##### ##TTT##### ###T######'),
    ('007', '6055697bfa32ffdc577ab1d6d1c2fe92000381e3a7c782c8122b80afb162b1ab', 31714,
     '.......... .......... .......... .......... .......... .......... .......... ###..#####'),
    ('008', '0c3d275a11d77723564372b687166d394764abfd2a3d5271a4eb7c49a1e799e9', 39871,
     '.......... .......... .......... ###..##### JJ...JJJJJ ZZZ...ZZZZ ZZZZ.ZZZZZ JJJ.JJJJJJ'),
    ('009', 'c85fce697c823375318080e11cdd66e0c55ed975279cdd53dd7007405ef8dda3', 42628,
     '.......... .......... SSS...SSSS JJ...JJJJJ ZZZ...ZZZZ ZZZZ.ZZZZZ JJJ.JJJJJJ SSSS.SSSSS'),
    ('010', '8dd611dcb209594de027172dac3148a4778901e49d9cdfacbce5c098a1c9e89c', 50381, None),
]


def _img(n: str, sha: str, size: int, rows: str | None) -> dict:
    e = {'file': f'cutcopy_{n}.jpg', 'sha256': sha, 'bytes': size}
    if rows is None:
        e['annotation'] = ('the two columns the T needs kept open, drawn as a translucent grey band over 009\'s board (「Tミノを'
                           '入れるための2列を確保」): the sampler refuses it, a translucent cell being no piece colour')
    else:
        e['rows'] = rows.split()
    return e


TETRISCH = {
    'page': 'https://tetrisch.github.io/main/ts/cutcopy.html',
    'title': '千鳥格子 Cut Copy',
    'fetched': '2026-10-20',
    'fetch_method': 'curl through the session proxy, TLS verification ON (the page and its ten images, '
                    '../img/t-spin/cutcopy_0NN.jpg, byte for byte; fetched twice that day, the bytes identical)',
    'snapshot_file': 'tetrisch_cutcopy.html',
    'snapshot_sha256': '827947f214bb85485feacd474d3f440b0fad59647eabf644afb4d6ae7f8eec14',
    'snapshot_bytes': 5656,
    'terms': 'not stated on the page; credited by link',
    'author_note': 'Tetrisちゃんねる: another site and another author than shiwehi.com and harddrop',
    'quotes': ['千鳥格子はTSDを2回連続で行う技です．', '千鳥格子はTSDをTSDで挟んだような地形です．', '挟む量をふやすことも可能です．',
               'その際はTミノを入れるための2列を確保することを意識してください．', '下穴が1マス横にずれている場合に可能です．',
               '江戸城の場合は交互にずれている場合，トリル下穴の場合に可能です．', '綺麗な地形が残るのでスムーズに他の技へ移行できるでしょう．'],
    'images_dir': 'spec/fixtures/tetrisch-cutcopy',
    'reading': {'.': 'empty', '#': 'grey, filled', 'other': 'a letter its piece, filled (the jp-forecast sampler\'s '
                                                           'reading, pipeline.sim.extract_jp_forecast.extract_one); in '
                                                           '008 and 009 the colours mark which TSD a row belongs to, '
                                                           'not pieces'},
    'images': [_img(*x) for x in _TC_IMAGES],
    #: what each image is, by number (the page's order): the basic sequence, the T dropped upright and then turned
    #: flat, twice; the same board coloured as one TSD sandwiched by another; three nested (江戸城); an annotation
    'basic': {'terrain': '001', 'upright': '002', 'spin': '003', 'after': '004',
              'second_upright': '005', 'second_spin': '006', 'second_after': '007'},
    'coloured': {'image': '008', 'same_occupancy_as': '001'},
    'edo': {'image': '009', 'tsds': 3,
            'reading': 'three TSDs nested, each row coloured by its TSD; measured below as two Cut Copies in a row'},
    #: the window's slot on the boards it is checked on as an agreement drawing (as drawn): 001 at 003's T, 009 at its
    #: innermost T
    'slots': {'001': [[5, 3], [5, 4], [5, 5], [6, 4]], '009': [[4, 3], [4, 4], [4, 5], [5, 4]]},
}

#: harddrop's BT_Cannon page draws one Cut Copy, which `btcannon-technique.json` records (with its oldid and hash)
#: among the drawn T's the BT window misses; read from there, never copied
BT_CANNON = {
    'file': BT_FILE,
    'table': 31, 'board': 0, 'mirrored': True,
    'page': 'https://harddrop.com/wiki/BT_Cannon',
    'note': 'the Cut Copy harddrop\'s BT_Cannon page recommends before offering the BT (its record\'s own note names '
            'it): this window fires on it once, mirrored, at its drawn T, and on no other board that record holds',
}

CROSS_SOURCE = {
    'kind': 'routes',
    'label_pattern': 'cut copy',
    'note': 'the windows, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot board of '
            'every committed *-routes.json, with the U cells as the T: they fire on none (no route page draws a Cut Copy). '
            'The independent drawers are harddrop and Tetrisちゃんねる instead: harddrop\'s Cut_copy page (`harddrop`, the '
            'page this page cites; both variants), the Cut Copy its BT_Cannon page draws (`bt_cannon`), and two of '
            'Tetrisちゃんねる\'s images (`tetrisch`). Their drawings are the windows\' external `agreement` drawings: rule (g) '
            'fires each variant\'s window on each of its drawings, once, at its drawn T, in its recorded hand.',
    'routes_fire_none': 'no committed routes file draws a Cut Copy (measured: the window fires on none of their U-slot '
                        'boards, and no node is labelled 千鳥格子 or Cut Copy); the cross-check is harddrop\'s own pages, '
                        'read below',
    'harddrop': HARDDROP,
    'tetrisch': TETRISCH,
    'bt_cannon': BT_CANNON,
    'fires': [],
    'also': [],
    'labelled_not_fired': [],
    #: boards of the other committed technique transcriptions a window fires on (measured both ways in `cross:`)
    'also_technique': [
        {'file': 'stmbcave-technique.json', 'node': 'feature.pre', 'variant': 'uncut', 'mirrored': True,
         'cells': [[2, 2], [2, 3], [2, 4], [3, 3]],
         'note': 'the STMB Cave page\'s 「TSDの地形でSTMB caveを行うと連続してTSDを狙うことができます」: an STMB Cave over a TSD '
                 'terrain is, on that board, harddrop\'s second type (「could be easily mistaken with STMB Cave」). Same '
                 'author: a relation, recorded, not fitted'},
        {'file': 'stmbcave-technique.json', 'node': 'feature.spin', 'variant': 'uncut', 'mirrored': True,
         'cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'note': 'the same board with its T in (read with the T taken out)'},
    ],
}

KNOWN_DISCREPANCIES: list[dict] = []

#: shiwehi.com's page only: a derived board is drawn nowhere, an external one on another site
PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived') and not n.get('external')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'cutcopy',
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
_T_SHAPES = {RT._norm(s) for s in RT._shapes('t')}


def _is_t(cells) -> bool:
    return len(cells) == 4 and RT._norm({(c, -r) for r, c in cells}) in _T_SHAPES


def hd_slots(rows: list[str]) -> list[list[list[int]]]:
    """A board's drawn T's: its `U` cells partitioned into T's, each sorted, the T's in reading order. A board whose
    `U` cells are not exactly one way to partition into T's is an error, never a guess."""
    U = sorted((r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == 'U')
    ts = [frozenset(cb) for cb in itertools.combinations(U, 4) if _is_t(cb)]

    def part(left: frozenset):
        if not left:
            return [[]]
        first = min(left)
        return [[t] + p for t in ts if first in t and t <= left for p in part(left - t)]
    ps = part(frozenset(U))
    if len(ps) != 1:
        raise ValueError(f'{len(ps)} ways to read the drawn cells {U} as T\'s')
    return sorted(sorted([r, c] for r, c in t) for t in ps[0])


def _pre(rows: list[str]) -> list[str]:
    return [row.replace('U', EMPTY) for row in rows]


def _var_of(data: dict, vid: str | None) -> dict:
    return data['variants'][0] if vid is None else next(v for v in data['variants'] if v['id'] == vid)


def _hands(data: dict, rows: list[str], slot, vid: str | None = None) -> list[bool]:
    """The hands one variant's window (the first type's by default) fires in at `slot` on a board (its U cells empty)."""
    v = _var_of(data, vid)
    return [m for m in (False, True) if TT.window_fires(data, v, SPEC, _pre(rows), {tuple(x) for x in slot}, m)]


def _fires_anywhere(data: dict, rows: list[str], vid: str | None = None) -> list[tuple]:
    v, pre = _var_of(data, vid), _pre(rows)
    return [([list(x) for x in sorted(cs)], m) for cs in TT.t_placements(pre, SPEC) for m in (False, True)
            if TT.window_fires(data, v, SPEC, pre, cs, m)]


def _hands_any(data: dict, rows: list[str], slot) -> list[tuple]:
    """(variant, hand) for every variant's window that fires at `slot`."""
    return [(v['id'], m) for v in data['variants'] for m in _hands(data, rows, slot, v['id'])]


def _fires_any(data: dict, rows: list[str]) -> list[tuple]:
    """(variant, cells, hand) for every variant's window, at every resting T placement it fires at."""
    return [(v['id'], cs, m) for v in data['variants'] for cs, m in _fires_anywhere(data, rows, v['id'])]


def t_lie(data: dict, rows: list[str], slot) -> tuple[str, int, str]:
    """What one drawn T on a harddrop board is, measured: its lie (`stood`, `flat-down` — the windows' T — or
    `flat-up`), the rows it fills as drawn, and why no window fires at it: the T is not the windows', every window
    leaves the board in both hands, or a window cell disagrees (`fires` if one fires after all)."""
    rs = sorted({r for r, _ in slot})
    lie = 'stood' if len(rs) == 3 else ('flat-down' if sum(1 for r, _ in slot if r == rs[0]) == 3 else 'flat-up')
    lines = sum(1 for r in rs if EMPTY not in rows[r])
    if _hands_any(data, rows, slot):
        return lie, lines, 'fires'
    if lie != 'flat-down':
        return lie, lines, "not the window's T"
    lock = {tuple(x) for x in slot}
    off = []
    for v in data['variants']:
        for m in (False, True):
            W = TT.window_cells(data, v, SPEC, m)
            D = {k for k, x in W.items() if x == 'T'}
            dr = min(r for r, _ in lock) - min(r for r, _ in D)
            dc = min(c for _, c in lock) - min(c for _, c in D)
            off.append(any(not (0 <= r + dr < len(rows) and 0 <= c + dc < WIDTH) for r, c in W))
    return lie, lines, 'leaves the board' if all(off) else 'disagrees'


def harddrop_drawings(data: dict | None = None) -> list[dict]:
    """harddrop's Cut_copy drawings as agreement drawings of their variant: the slot is its drawn T, every drawn T
    read as empty."""
    data = data or build()
    return [{'name': f'harddrop Cut_copy table {d["table"]} board {d["board"]} ({d["section"]})',
             'rows': _pre(d['rows']), 't_cells': d['slot'], 'mirrored': d['mirrored'], 'variant': d['variant']}
            for d in data['cross_source']['harddrop']['drawings']]


def norm_tc(rows: list[str]) -> list[str]:
    """A Tetrisちゃんねる image in this file's letters: '.' empty, every other letter filled (`c`)."""
    return [''.join(EMPTY if ch == '.' else 'c' for ch in row) for row in rows]


def tc_image(data: dict, n: str) -> dict:
    e = [x for x in data['cross_source']['tetrisch']['images'] if x['file'] == f'cutcopy_{n}.jpg']
    if len(e) != 1:
        raise ValueError(f'tetrisch: {len(e)} images cutcopy_{n}.jpg recorded')
    return e[0]


def tetrisch_drawings(data: dict | None = None) -> list[dict]:
    """Tetrisちゃんねる's two pre-T boards as agreement drawings of the first type, as drawn: 001 at 003's T, 009 at its
    innermost T."""
    data = data or build()
    tc = data['cross_source']['tetrisch']
    return [{'name': f'Tetrisちゃんねる cutcopy_{n}.jpg', 'rows': norm_tc(tc_image(data, n)['rows']),
             't_cells': tc['slots'][n], 'mirrored': False, 'variant': 'cutcopy'} for n in sorted(tc['slots'])]


def bt_record(data: dict) -> dict:
    """The BT_Cannon page's harddrop record, from the committed BT砲 transcription."""
    return json.loads((HERE / data['cross_source']['bt_cannon']['file']).read_text())['cross_source']['harddrop']


def bt_drawing(data: dict | None = None) -> dict:
    """The Cut Copy harddrop's BT_Cannon page draws, read out of `btcannon-technique.json` by (table, board)."""
    data = data or build()
    bc = data['cross_source']['bt_cannon']
    rec = bt_record(data)
    e = [x for x in rec['drawings'] + rec['drawn_t_not_fired'] + rec['fires_without_slot']
         if (x['table'], x['board']) == (bc['table'], bc['board'])]
    if len(e) != 1:
        raise ValueError(f'{bc["file"]} records {len(e)} boards at table {bc["table"]} board {bc["board"]}')
    slot = hd_slots(e[0]['rows'])
    if len(slot) != 1:
        raise ValueError(f'{bc["file"]} table {bc["table"]} board {bc["board"]} does not draw one T')
    return {'name': f'harddrop BT_Cannon table {bc["table"]} board {bc["board"]} (read from {bc["file"]})',
            'rows': _pre(e[0]['rows']), 't_cells': slot[0], 'mirrored': bc['mirrored'], 'record': e[0]}


def external_drawings() -> list[dict]:
    d = bt_drawing()
    return (harddrop_drawings() + [{**{k: d[k] for k in ('name', 'rows', 't_cells', 'mirrored')}, 'variant': 'cutcopy'}]
            + tetrisch_drawings())


def harddrop_page_problems(data: dict, text: str) -> list[str]:
    """The recorded drawings against the harddrop wikitext: each letter for letter at its (table, board) under its
    heading, and the record COMPLETE both ways — `drawings` exactly the drawn T's a window fires at (its variant, its
    hand), `drawn_t_not_fired` exactly every other drawn T, `fires_without_slot` exactly the boards with no T drawn on
    which a window fires. A board's drawn cells are read as T's (`hd_slots`), so a board drawing several T's is read T
    by T."""
    hd = data['cross_source']['harddrop']
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
    for d in _hd_boards(hd):
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
            hands = _hands_any(data, rows, s)
            (fired if hands else missed).append((i, j, str(s), sorted(hands)) if hands else (i, j, str(s)))
        if not slots:
            for vid, cs, m in _fires_any(data, rows):
                unslotted.append((i, j, vid, str(cs), m))
    want = sorted((d['table'], d['board'], str(d['slot']), [(d['variant'], d['mirrored'])]) for d in hd['drawings'])
    if sorted(fired) != want:
        bad.append(f'harddrop: the windows fire at the drawn T of {sorted(fired)}, the record holds {want}')
    named = sorted((e['table'], e['board'], str(e['slot'])) for e in hd['drawn_t_not_fired'])
    if sorted(missed) != named:
        bad.append(f'harddrop: no window fires at the drawn T of {sorted(missed)}, drawn_t_not_fired names {named}')
    wantu = sorted((e['table'], e['board'], e['variant'], str(e['slot']), e['mirrored']) for e in hd['fires_without_slot'])
    if sorted(unslotted) != wantu:
        bad.append(f'harddrop: with no T drawn the windows fire on {sorted(unslotted)}, the record names {wantu}')
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


def tetrisch_snapshot_checks(data: dict, html_dir: Path) -> list[str]:
    """The Tetrisちゃんねる page and its images beside the shiwehi snapshot (a person's --html-dir only)."""
    bad = []
    tc = data['cross_source']['tetrisch']
    p = Path(html_dir) / tc['snapshot_file']
    if not p.exists():
        bad.append(f'tetrisch: {tc["snapshot_file"]} is not in {html_dir} — fetch it beside the page')
    else:
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != tc['snapshot_sha256'] or len(raw) != tc['snapshot_bytes']:
            bad.append('tetrisch: hash: the page is not the recorded bytes')
        import html as _html
        import re
        flat = re.sub(r'\s+', '', _html.unescape(re.sub(r'<[^>]+>', '', raw.decode('utf8'))))
        for q in tc['quotes']:
            if q not in flat:
                bad.append(f'tetrisch: quote {q!r} is not on the page')
        imgs = re.findall(r'img/t-spin/(cutcopy_\d+\.jpg)', raw.decode('utf8'))
        if imgs != sorted(x['file'] for x in tc['images']):
            bad.append(f'tetrisch: the page shows {imgs}, the record holds {len(tc["images"])} images in page order')
    d = Path(html_dir) / Path(tc['images_dir']).name
    from pipeline.sim.extract_jp_forecast import extract_one
    try:
        import PIL  # noqa: F401  (extract_one imports it lazily; a missing Pillow is one named failure, not ten)
        pillow = True
    except ImportError:
        pillow = False
        bad.append('tetrisch: pillow: Pillow is not installed, so the images are checked by hash only and not re-read '
                   '(pip install Pillow)')
    for e in tc['images']:
        p = d / e['file']
        if not p.exists():
            bad.append(f'tetrisch: {e["file"]} is not in {d}')
            continue
        if hashlib.sha256(p.read_bytes()).hexdigest() != e['sha256']:
            bad.append(f'tetrisch: hash: {e["file"]} is not the recorded bytes')
        if not pillow:
            continue
        try:
            got = extract_one(str(p))
        except ValueError:
            got = None
        if got != e.get('rows'):
            bad.append(f'tetrisch: {e["file"]} re-reads as {got}, the record holds {e.get("rows")}')
    return bad


def snapshot_checks(data: dict, html_dir: Path) -> list[str]:
    return harddrop_snapshot_checks(data, html_dir) + tetrisch_snapshot_checks(data, html_dir)


# ── the external drawings, checked ───────────────────────────────────────────────────────────────
def hd_occ(rows: list[str]) -> list[str]:
    """A harddrop drawing in this file's occupancy letters: the drawn T `T`, every other filled cell `c`, or `C` in a
    row that is full with the T in."""
    return [''.join(EMPTY if ch == EMPTY else ('T' if ch == 'U' else ('C' if EMPTY not in row else 'c')) for ch in row)
            for row in rows]


def _hd_boards(hd: dict) -> list[dict]:
    return hd.get('drawings', []) + hd.get('drawn_t_not_fired', []) + hd.get('fires_without_slot', []) \
        + hd.get('after_drawn', [])


def _check_external(data: dict, by: dict) -> list[str]:
    """An `external` node is a harddrop drawing transcribed into this file: its rows are that record's board in
    occupancy letters, and the second variant's window is defined on one of that variant's own drawings."""
    bad = []
    hd = data['cross_source'].get('harddrop', {})
    for n in data['nodes']:
        if not n.get('external'):
            continue
        sb = n.get('source_board') or {}
        e = [d for d in _hd_boards(hd) if (d['table'], d['board']) == (sb.get('table'), sb.get('board'))]
        if n['external'] != 'harddrop' or len(e) != 1 or n.get('derived') or n['id'] in data['page_order']:
            bad.append(f'external: {n["id"]} names no single harddrop board, or is in the page order')
        elif n['rows'] != hd_occ(e[0]['rows']):
            bad.append(f'external: {n["id"]} is not harddrop table {sb["table"]} board {sb["board"]} in occupancy')
    for vv in data['variants']:
        if not by[vv['board']].get('external'):
            continue
        sb = by[vv['board']]['source_board']
        if not any((d['table'], d['board'], d.get('variant')) == (sb['table'], sb['board'], vv['id'])
                   for d in hd.get('drawings', [])):
            bad.append(f'external: {vv["id"]}\'s board {vv["board"]} is not one of its own harddrop drawings')
    for d in hd.get('after_drawn', []):
        if any('U' in r for r in d['rows']) or not d.get('note'):
            bad.append(f'external: after_drawn table {d["table"]} board {d["board"]} draws a T or carries no note')
    return bad


# ── Tetrisちゃんねる, checked ────────────────────────────────────────────────────────────────────────
def _occ(rows: list[str]) -> list[str]:
    return [''.join(EMPTY if ch in '.-' else '#' for ch in row) for row in rows]


def _with(rows: list[str], cells, ch: str = '#') -> list[str]:
    s = {tuple(x) for x in cells}
    return [''.join(ch if (r, c) in s else x for c, x in enumerate(row)) for r, row in enumerate(rows)]


def _full(rows: list[str]) -> list[int]:
    return [r for r, row in enumerate(rows) if EMPTY not in row]


def _clear(rows: list[str]) -> list[str]:
    full = _full(rows)
    return [EMPTY * WIDTH] * len(full) + [row for r, row in enumerate(rows) if r not in full]


def _letter_cells(rows: list[str], ch: str = 'T') -> list[list[int]]:
    return [[r, c] for r, row in enumerate(rows) for c, x in enumerate(row) if x == ch]


def _centre(cells) -> tuple:
    s = {tuple(x) for x in cells}
    return next(((r, c) for r, c in s if sum((r + a, c + b) in s for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0))) == 3),
                None)


def carry(data: dict, v: dict, lock, hand: bool, board: list[str]) -> list[list[int]]:
    """The variant's follow-up slot on `board` after a hit at `lock` (in `hand`): mapped into the board's frame, then
    through the hit's own clear (a row above a cleared row moves down by the cleared rows under it)."""
    f = TT.frame_map(data, v, SPEC, {tuple(x) for x in lock}, hand)
    full = _full(_occ(_with(board, lock)))
    return sorted([r + sum(1 for x in full if x > r), c] for r, c in (f(*x) for x in v['followup']['t_cells_pre_clear']))


def _check_tetrisch(data: dict) -> list[str]:
    bad = []
    tc = data['cross_source'].get('tetrisch')
    if not tc:
        return ['tetrisch: no Tetrisちゃんねる record (another site\'s drawings are required, never defaulted)']
    names = [x['file'] for x in tc['images']]
    if names != [f'cutcopy_{i:03d}.jpg' for i in range(1, 11)]:
        bad.append(f'tetrisch: the images recorded are {names}, not cutcopy_001..010 in page order')
    for e in tc['images']:
        if ('rows' in e) == ('annotation' in e):
            bad.append(f'tetrisch: {e["file"]} is neither a board nor an annotation (or both)')
        elif 'rows' in e and (len(e['rows']) != 8 or any(len(r) != WIDTH for r in e['rows'])):
            bad.append(f'tetrisch: {e["file"]} is not an 8-row, ten-wide board')
        p = IMG_DIR / e['file']
        if not p.exists():
            bad.append(f'tetrisch: {e["file"]} is not committed under {IMG_DIR.relative_to(REPO)}')
            continue
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != e['sha256'] or len(raw) != e['bytes']:
            bad.append(f'tetrisch: the committed {e["file"]} is not the recorded bytes')
    v = data['variants'][0]
    try:
        img = {x['file'][8:11]: x for x in tc['images']}
        rows = lambda n: norm_tc(img[n]['rows'])
        B = tc['basic']
        # the basic sequence: twice, the T dropped upright, then turned flat about the same centre into the slot
        base = rows(B['terrain'])
        for up, sp, af in ((B['upright'], B['spin'], B['after']),
                           (B['second_upright'], B['second_spin'], B['second_after'])):
            tu, ts = _letter_cells(img[up]['rows']), _letter_cells(img[sp]['rows'])
            if len(tu) != 4 or len({r for r, _ in tu}) != 3 or not _is_t(tu):
                bad.append(f'tetrisch: cutcopy_{up}\'s T is not a T stood upright')
            if len(ts) != 4 or len({r for r, _ in ts}) != 2 or not _is_t(ts):
                bad.append(f'tetrisch: cutcopy_{sp}\'s T is not a flat T')
            if _occ(_with(base, tu)) != _occ(img[up]['rows']) or _occ(_with(base, ts)) != _occ(img[sp]['rows']):
                bad.append(f'tetrisch: cutcopy_{up} / cutcopy_{sp} are not the board before them with their T in')
            if _centre(tu) is None or _centre(tu) != _centre(ts):
                bad.append(f'tetrisch: the upright T of cutcopy_{up} and the flat T of cutcopy_{sp} do not share a centre')
            if len(_full(_occ(img[sp]['rows']))) != 2 or _clear(_occ(img[sp]['rows'])) != _occ(img[af]['rows']):
                bad.append(f'tetrisch: cutcopy_{af} is not what cutcopy_{sp}\'s TSD leaves')
            if _fires_any(data, rows(af)):
                bad.append(f'tetrisch: a window fires on the after board cutcopy_{af}')
            if sp == B['spin']:
                if _fires_any(data, base) != [('cutcopy', sorted(ts), False)] or sorted(ts) != tc['slots'][B['terrain']]:
                    bad.append(f'tetrisch: the windows fire {_fires_any(data, base)} on cutcopy_{B["terrain"]}, not the '
                               f'first type once, as drawn, at cutcopy_{sp}\'s T')
                nxt = _letter_cells(img[B['second_spin']]['rows'])
                if carry(data, v, ts, False, base) != sorted(nxt):
                    bad.append(f'tetrisch: the follow-up slot carried through cutcopy_{sp}\'s clear is not '
                               f'cutcopy_{B["second_spin"]}\'s T')
            base = rows(af)
        if _occ(img[tc['coloured']['image']]['rows']) != _occ(img[tc['coloured']['same_occupancy_as']]['rows']):
            bad.append('tetrisch: the coloured board is not the basic terrain by occupancy')
        # 江戸城: a hit, whose follow-up slot is a hit in the other hand, whose follow-up is the last TSD
        E = tc['edo']
        board, lock, hand = rows(E['image']), tc['slots'][E['image']], False
        if _fires_any(data, board) != [('cutcopy', sorted(lock), False)]:
            bad.append(f'tetrisch: the windows fire {_fires_any(data, board)} on cutcopy_{E["image"]}, not once at its '
                       'innermost T, as drawn')
        n = 0
        while True:
            n += 1
            if len(_full(_occ(_with(board, lock)))) != 2:
                bad.append(f'tetrisch: 江戸城 TSD {n} does not clear two rows')
                break
            fu = carry(data, v, lock, hand, board)
            board = _clear(_occ(_with(board, lock)))
            hits = _fires_any(data, board)
            if n < E['tsds'] - 1:
                if hits != [('cutcopy', fu, not hand)]:
                    bad.append(f'tetrisch: after 江戸城 TSD {n} the windows fire {hits}, not the first type once at the '
                               f'follow-up slot, {"as drawn" if hand else "mirrored"}')
                    break
                lock, hand = fu, not hand
            else:
                if hits or any(board[r][c] != EMPTY for r, c in fu) or len(_full(_occ(_with(board, fu)))) != 2 \
                        or any(ch != EMPTY for row in _clear(_occ(_with(board, fu))) for ch in row):
                    bad.append(f'tetrisch: 江戸城\'s last TSD is not the follow-up slot of TSD {n}, or leaves a stack')
                n += 1
                break
        if n != E['tsds']:
            bad.append(f'tetrisch: 江戸城 is {n} TSDs, the record says {E["tsds"]}')
        annotated = sorted(x['file'][8:11] for x in tc['images'] if 'annotation' in x)
        used = sorted(list(B.values()) + [tc['coloured']['image'], E['image']] + annotated)
        if used != sorted(img) or annotated != ['010']:
            bad.append(f'tetrisch: the sequences and annotations do not account for every image once ({used})')
        if sorted(tc['slots']) != sorted([B['terrain'], E['image']]):
            bad.append('tetrisch: the agreement slots are not the basic terrain and 江戸城')
    except (KeyError, ValueError, TypeError) as e:
        bad.append(f'tetrisch: {e!r}')
    return bad


# ── technique-only rules ─────────────────────────────────────────────────────────────────────────
def _spin_pre(n: dict) -> list[str]:
    """A board as the T went into it: a spin board with its spin piece taken out."""
    if n['kind'] != 'spin':
        return n['rows']
    return [''.join(EMPTY if ch in ('T', 't') else ch for ch in row) for row in n['rows']]


def _clears(rows, cells) -> int:
    o = TT.occ_of(rows, SPEC)
    o = [''.join('#' if (r, c) in cells else ch for c, ch in enumerate(row)) for r, row in enumerate(o)]
    return len(TT.full_rows(o))


def extra_checks(data: dict):
    bad, measured = [], set()
    by = {n['id']: n for n in data['nodes']}
    v = data['variants'][0]
    xs = data['cross_source']
    # mirror: every mirrored drawing fires once, mirrored, at a placement clearing two rows; every drawn board is listed
    for bid in v.get('fires_mirrored', []):
        if bid not in by:
            bad.append(f'mirror: fires_mirrored names no node {bid!r}')
            continue
        rows = _spin_pre(by[bid])
        hits = _fires_anywhere(data, rows)
        if len(hits) != 1 or not hits[0][1]:
            bad.append(f'mirror: the window fires {len(hits)} time(s) on {bid}, not once mirrored')
        elif _clears(rows, {tuple(x) for x in hits[0][0]}) != 2:
            bad.append(f'mirror: the window fires on {bid} at a placement that does not clear two rows')
    listed = set(v.get('fires_on', [])) | set(v.get('fires_mirrored', [])) | set(v.get('misses', [])) | {v['board']}
    for n in data['nodes']:
        if not n.get('derived') and not n.get('external') and n['id'] not in listed:
            bad.append(f'mirror: drawn board {n["id"]} is in none of fires_on, fires_mirrored, misses')
        if n.get('external') and n['id'] not in v.get('misses', []):
            bad.append(f'mirror: the external board {n["id"]} is not in the first type\'s misses')
    for vv in data['variants'][1:]:
        if set(vv.get('misses', [])) | {vv['board']} != set(by):
            bad.append(f'mirror: {vv["id"]}\'s misses and board are not every board of the file')
    want = sorted([(b, False) for b in v.get('fires_on', [])] + [(b, True) for b in v.get('fires_mirrored', [])])
    if sorted((a['board'], a['mirrored']) for a in v.get('agreement', [])) != want:
        bad.append('mirror: the page\'s agreement drawings are not fires_on (as drawn) and fires_mirrored (mirrored)')
    # later: a Cut Copy the page describes and the window does not express, both halves measured
    qids = {q['id'] for q in data['quotes']}
    if not v.get('not_expressed'):
        bad.append('later: no not_expressed record (the page\'s own 「(Z)は1回目のT-spinを打った後に置いても構いません」 '
                   'reading is required, never defaulted)')
    for e in v.get('not_expressed') or []:
        n = by.get(e.get('board'))
        if n is None or not e.get('reason') or e.get('quote') not in qids:
            bad.append(f'later: not_expressed {e.get("board")!r} names no node, no quote or carries no reason')
            continue
        less = [''.join(EMPTY if ch in e['less'] else ch for ch in row) for row in n['rows']]
        # the piece read as placed later is the one the quoted sentence names (its mino icon)
        icons = {i[1:].lower() for q in data['quotes'] if q['id'] == e['quote'] for i in q.get('icons', [])}
        if set(e['less']) != icons:
            bad.append(f'later: {e["board"]} less {e["less"]!r} is not the piece {sorted(icons)} its sentence names')
        if not e['less'] or less == n['rows'] or not set(e['less']) <= set(n.get('adds', '')):
            bad.append(f'later: {e["board"]} less {e["less"]!r} is not that board less some of its page pieces')
        elif _fires_any(data, less):
            bad.append(f'later: a window fires on {e["board"]} less {e["less"]!r}, listed as not expressed')
        if not _fires_anywhere(data, n['rows']):
            bad.append(f'later: the window does not fire on {e["board"]} with its pieces in either')
        # decides: exactly the cells of the later piece whose removal ALONE stops the window, measured cell by cell
        cells = [(r, c) for r, row in enumerate(n['rows']) for c, ch in enumerate(row) if ch in e['less']]
        deciding = sorted([r, c] for r, c in cells if not _fires_anywhere(
            data, [''.join(EMPTY if (rr, cc) == (r, c) else ch for cc, ch in enumerate(row))
                   for rr, row in enumerate(n['rows'])]))
        if deciding != sorted(e.get('decides') or []):
            bad.append(f'later: the cells of {e["board"]}\'s {e["less"]!r} that alone stop the window are {deciding}, '
                       f'not_expressed records {e.get("decides")}')
    # after: the first TSD's after board is derived (the page draws it with the second T in), so the after rule is here
    sp = by['basic.spin']
    got, _n = after_spin([''.join('t' if (r, c) in TT.spin_cells(sp) else ('-' if TT.is_empty(ch, SPEC) else 'c')
                                  for c, ch in enumerate(row)) for r, row in enumerate(sp['rows'])])
    if bottom(TT.occ_of(got, SPEC), TT.MAX_ROWS) != bottom(TT.occ_of(by['basic.after']['rows'], SPEC), TT.MAX_ROWS):
        measured.add('basic.after:after')
    if v['followup']['board'] != 'basic.after' or by['second.spin'].get('spin_of') != 'basic.after':
        bad.append('after: the follow-up is not read on the derived board the second TSD stands on')
    fa = {tuple(x) for x in v['followup']['t_cells_after']}
    if fa != TT.spin_cells(by['second.spin']):
        bad.append('after: the follow-up slot is not the T second.spin draws')
    # harddrop: every recorded entry is ten wide; its slot is one of its drawn T's; checked here on the DATA (the
    # agreement rule reads the pristine build through the spec)
    hd = xs.get('harddrop')
    if not hd:
        bad.append('harddrop: no harddrop record (the Cut_copy page this page cites is required, never defaulted)')
        hd = {}
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
        hits = [(frozenset(map(tuple, cs)), vid, m) for vid, cs, m in _fires_any(data, d['rows'])]
        if hits != [(frozenset(tuple(x) for x in d['slot']), d.get('variant'), d['mirrored'])]:
            bad.append(f'harddrop: the windows fire {len(hits)} time(s) on table {k[0]} board {k[1]}, not once, the '
                       f'{d.get("variant")} window at its drawn T ({"mirrored" if d["mirrored"] else "as drawn"})')
        if k in seen:
            bad.append(f'harddrop: table {k[0]} board {k[1]} recorded twice')
        seen.add(k)
    for vv in data['variants']:
        if not any(d['section'] == 'Generic Structures' and d.get('variant') == vv['id'] for d in hd.get('drawings', [])):
            bad.append(f'harddrop: no recorded drawing of {vv["id"]} from the page\'s own Generic Structures section')
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
        ow = d.get('other_window')
        if ow:
            # another technique's window, named as what this T is: it must fire here, at the drawn T, in its hand
            other = json.loads((TECHNIQUE_DIR / ow['file']).read_text())
            ospec = TT.TechniqueSpec(out=TECHNIQUE_DIR / ow['file'], build=lambda: other, alphabet=frozenset(),
                                     empty_letters=other.get('empty_letters', ''), max_rows=99)
            ov = next((x for x in other['variants'] if x['id'] == ow['variant']), None)
            pre = _pre(d['rows'])
            hits = [] if ov is None else [(sorted([r, c] for r, c in cs), m) for cs in TT.t_placements(pre, ospec)
                                          for m in (False, True) if TT.window_fires(other, ov, ospec, pre, cs, m)]
            if hits != [(sorted(d['slot']), ow['mirrored'])]:
                bad.append(f'harddrop: table {k[0]} board {k[1]}: {ow["file"]} {ow["variant"]} fires {hits}, not once at '
                           f'the drawn T')
        if k in seen:
            bad.append(f'harddrop: table {k[0]} board {k[1]} slot {d["slot"]} recorded twice')
        seen.add(k)
    for d in hd.get('fires_without_slot', []):
        hits = _fires_any(data, d['rows'])
        if any('U' in r for r in d['rows']) or hits != [(d.get('variant'), d['slot'], d['mirrored'])]:
            bad.append(f'harddrop: table {d["table"]} board {d["board"]} draws a T, or the window does not fire on it '
                       f'once at {d["slot"]} ({"mirrored" if d["mirrored"] else "as drawn"})')
    if hd and hd.get('page') not in ' '.join(data['source'].get('references', [])):
        bad.append('harddrop: the harddrop page read is not the one the page cites as its reference')
    # bt: the Cut Copy harddrop's BT_Cannon page draws, read out of the BT砲 transcription; this window fires on that
    # record's boards there and nowhere else, and the BT record's own note names it a Cut Copy
    bc = xs.get('bt_cannon')
    if not bc:
        bad.append('bt: no bt_cannon record')
    else:
        try:
            rec = bt_record(data)
            d = bt_drawing(data)
        except (OSError, ValueError, KeyError) as e:
            bad.append(f'bt: {e}')
        else:
            if 'cut copy' not in d['record'].get('note', '').lower():
                bad.append(f'bt: {bc["file"]} table {bc["table"]} board {bc["board"]}\'s own note does not name a Cut Copy')
            got = []
            for e in rec['drawings'] + rec['drawn_t_not_fired'] + rec['fires_without_slot']:
                slots = hd_slots(e['rows'])
                for s in slots:
                    if _hands_any(data, e['rows'], s):
                        got.append((e['table'], e['board'], _hands_any(data, e['rows'], s)))
                if not slots and _fires_any(data, e['rows']):
                    got.append((e['table'], e['board'], None))
            if got != [(bc['table'], bc['board'], [('cutcopy', bc['mirrored'])])]:
                bad.append(f'bt: this window fires on {bc["file"]}\'s harddrop boards {got}, not once at '
                           f'table {bc["table"]} board {bc["board"]} ({"mirrored" if bc["mirrored"] else "as drawn"})')
    # same author and others: the windows over every board of the other committed technique transcriptions, every
    # resting T, both hands — exactly the boards `also_technique` records (measured both ways)
    got = []
    for f in sorted(TECHNIQUE_DIR.glob('*-technique.json')):
        if f.name == OUT.name:
            continue
        other = json.loads(f.read_text())
        ospec = TT.TechniqueSpec(out=f, build=lambda: other, alphabet=frozenset(),
                                 empty_letters=other.get('empty_letters', ''), max_rows=99)
        for n in other['nodes']:
            sc = TT.spin_cells(n) if n['kind'] == 'spin' else set()
            pre = [''.join(EMPTY if (r, c) in sc else ch for c, ch in enumerate(row)) for r, row in enumerate(n['rows'])]
            for vv in data['variants']:
                for cs in TT.t_placements(pre, ospec):
                    for m in (False, True):
                        if TT.window_fires(data, vv, ospec, pre, cs, m):
                            got.append((f.name, n['id'], vv['id'], str(sorted([r, c] for r, c in cs)), m))
    want = sorted((e['file'], e['node'], e['variant'], str(e['cells']), e['mirrored']) for e in xs.get('also_technique', []))
    if sorted(got) != want:
        bad.append(f'cross: the windows fire on the other technique transcriptions at {sorted(got)}, also_technique '
                   f'records {want} (record it, or measure why not)')
    if any(not e.get('note') for e in xs.get('also_technique', [])):
        bad.append('cross: an also_technique entry carries no note')
    bad += _check_external(data, by)
    dec = data['source'].get('declined')
    if not dec or any(not (e.get('url') and e.get('checked') and e.get('reason')) for e in dec):
        bad.append('declined: the sites checked and not used (rights) must each carry a url, a date and a reason')
    bad += _check_tetrisch(data)
    # cross: no routes node is labelled as this technique by its Japanese name either
    for f in sorted(HERE.glob('*-routes.json')):
        for n in json.loads(f.read_text())['nodes']:
            text = ' '.join(str(n.get(k, '')) for k in ('id', 'label', 'label_jp')).lower()
            if '千鳥' in text or 'cutcopy' in text or 'cut copy' in text:
                bad.append(f'cross: {f.name} {n["id"]} is labelled as this technique')
    return bad, measured


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='',
    upper_groups={'T': 'merge'},
    extra_checks=extra_checks,
    external_drawings=external_drawings,
    html_checks=lambda d, h: snapshot_checks(d, h),
    # the same checks read nothing but the pinned wikitext, so a weekly api.php refetch can run them
    wikitext_checks=harddrop_snapshot_checks,
    synthetic_wikitext=lambda d: {d['cross_source']['harddrop']['snapshot_file']: _synthetic_harddrop(d)},
)


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def _set(rows, r, c, ch):
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _var(d, i=0):
    return d['variants'][i]


def _hdd(d, i, board=None):
    """A harddrop drawing: by index, or by (table, board)."""
    ds = d['cross_source']['harddrop']['drawings']
    return ds[i] if board is None else next(x for x in ds if (x['table'], x['board']) == (i, board))


def _tc(d, n):
    return next(x for x in d['cross_source']['tetrisch']['images'] if x['file'] == f'cutcopy_{n}.jpg')


def _hdm(d, table, board, k=0):
    return [x for x in d['cross_source']['harddrop']['drawn_t_not_fired'] if (x['table'], x['board']) == (table, board)][k]


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'hole.terrain')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: d['page_order'].reverse(), 'page_order swapped', 'grammar:'),
    (lambda d: node(d, 'second.spin').__setitem__('spin_of', 'nowhere'), 'a dangling reference', 'grammar:'),
    (lambda d: _set(node(d, 'hole.osz')['rows'], 5, 0, '-'), 'a build board cell flipped', 'build:'),
    (lambda d: _set(node(d, 'col3.terrain')['rows'], 6, 9, '-'), 'a derived terrain edited', 'build:'),
    (lambda d: _set(node(d, 'basic.after')['rows'], 3, 0, 'c'), 'the derived after board edited', 'build:'),
    (lambda d: (_set(node(d, 'basic.spin')['rows'], 4, 7, 'C'), _set(node(d, 'basic.spin')['rows'], 2, 7, 'T')),
     'the T pointing up', 'spin:'),
    (lambda d: _set(node(d, 'basic.spin')['rows'], 3, 0, 'c'), 'a cleared row drawn unmuted', 'spin:'),
    (lambda d: node(d, 'basic.spin').__setitem__('lines', 3), 'the TSD\'s line count', 'spin:'),
    (lambda d: node(d, 'second.spin').__setitem__('lines', 1), 'the second TSD\'s line count', 'spin:'),
    (lambda d: _set(node(d, 'basic')['rows'], 0, 4, 'c'), 'the basic form not the spin board less its T', 'spin:'),
    (lambda d: (_set(node(d, 'basic.after')['rows'], 1, 4, 'c'), _set(node(d, 'second.spin')['rows'], 1, 4, 'c')),
     'the after board not what the TSD leaves', 'discrepancy:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [3, 9]), 'the window widened by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [5, 9]), 'the window narrowed by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [1, 5]), 'the window widened to the outer slot\'s roof', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [2, 4]), 'the window without the outer slot\'s nub', 'window:'),
    (lambda d: _var(d)['roof_cells'].pop(), 'a roof cell unnamed', 'window:'),
    (lambda d: _var(d)['agreement'][1].__setitem__('mirrored', False), 'the T-hole build read as drawn', 'window:'),
    (lambda d: _var(d)['agreement'][2].__setitem__('t_cells', [[4, 6], [4, 7], [4, 8], [5, 7]]),
     'a slot moved one column', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('t_cells_pre_clear', [[2, 5], [2, 6], [2, 7], [3, 6]]),
     'the follow-up\'s nub read inside the cleared rows', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('lines', 3), 'the follow-up read as a TST', 'window:'),
    (lambda d: _var(d)['misses'].append('basic'), 'a board it fires on listed as a miss', 'window:'),
    (lambda d: _var(d)['fires_on'].append('hole.osz'), 'a mirrored build listed as firing as drawn', 'window:'),
    (lambda d: _var(d)['fires_mirrored'].remove('col3.jz'), 'a drawn board in no list', 'mirror:'),
    (lambda d: _var(d)['fires_mirrored'].append('hole.terrain'), 'the T-hole terrain listed as firing', 'mirror:'),
    (lambda d: _var(d)['not_expressed'][0].__setitem__('less', 's'), 'the wrong piece read as placed later', 'later:'),
    (lambda d: _var(d)['not_expressed'][0].__setitem__('reason', ''), 'not_expressed without a reason', 'later:'),
    (lambda d: _var(d)['not_expressed'][0].__setitem__('quote', 'nope'), 'not_expressed naming no quote', 'later:'),
    (lambda d: _var(d).pop('not_expressed'), 'the not_expressed record dropped', 'later:'),
    (lambda d: _var(d)['not_expressed'][0].__setitem__('decides', [[2, 8], [2, 9]]),
     'two of the Z\'s cells read as deciding', 'later:'),
    (lambda d: _var(d)['not_expressed'][0].pop('decides'), 'the deciding cells unrecorded', 'later:'),
    (lambda d: d['cross_source'].pop('harddrop'), 'no harddrop record', 'harddrop:'),
    (lambda d: _set(node(d, 'hole.osz')['rows'], 1, 4, 'z'), 'a piece broken', 'discrepancy:'),
    (lambda d: _hdd(d, 0).__setitem__('mirrored', True), 'a harddrop drawing read mirrored', 'harddrop:'),
    (lambda d: _set(_hdd(d, 0)['rows'], 3, 1, '-'), 'a harddrop drawing\'s outer wall dropped', 'harddrop:'),
    (lambda d: _hdd(d, 11, 2).__setitem__('slot', [[7, 3], [7, 4], [7, 5], [8, 4]]), 'a harddrop slot moved', 'harddrop:'),
    (lambda d: [x.__setitem__('section', 'Variations, Other Uses and Comparisons')
                for x in d['cross_source']['harddrop']['drawings']], 'the generic structure dropped', 'harddrop:'),
    (lambda d: d['cross_source']['harddrop']['drawings'].append(copy.deepcopy(_hdd(d, 0))), 'a harddrop drawing twice',
     'harddrop:'),
    (lambda d: _hdm(d, 6, 1).__setitem__('t', 'flat-down'), 'a missed drawn T\'s lie misrecorded', 'harddrop:'),
    (lambda d: _hdm(d, 3, 1).__setitem__('window', 'leaves the board'), 'why the window misses misrecorded', 'harddrop:'),
    (lambda d: _hdm(d, 8, 1, 1).__setitem__('lines', 3), 'a missed T\'s line count misrecorded', 'harddrop:'),
    (lambda d: _hdm(d, 10, 2).__setitem__('note', ''), 'a missed drawn T with no note', 'harddrop:'),
    (lambda d: _hdm(d, 6, 1)['other_window'].__setitem__('variant', 'parapet'), 'the Parapet TSS read as its TSD',
     'harddrop:'),
    (lambda d: _hdm(d, 8, 1, 1).__setitem__('slot', [[5, 4], [5, 5], [5, 6], [6, 5]]), 'a T recorded twice', 'harddrop:'),
    (lambda d: _set(d['cross_source']['harddrop']['fires_without_slot'][0]['rows'], 3, 1, '-'),
     'a no-T harddrop board the window does not fire on', 'harddrop:'),
    (lambda d: d['source'].__setitem__('references', []), 'the cited page not the one read', 'harddrop:'),
    (lambda d: d['cross_source']['bt_cannon'].__setitem__('board', 1), 'the BT_Cannon board misnamed', 'bt:'),
    (lambda d: d['cross_source']['bt_cannon'].__setitem__('mirrored', False), 'the BT_Cannon Cut Copy read as drawn', 'bt:'),
    (lambda d: d['cross_source'].pop('bt_cannon'), 'no BT_Cannon record', 'bt:'),
    (lambda d: d['cross_source'].pop('routes_fire_none'), 'no routes board and no reason', 'cross:'),
    (lambda d: d['cross_source']['fires'].append({'file': 'sdpcspin-routes.json', 'node': '3.first.cave',
                                                  'variant': 'cutcopy', 'mirrored': True}),
     'a routes board recorded that does not fire', 'cross:'),
    (lambda d: node(d, 'col3.jz').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['known_discrepancies'].append({'id': 'hole.osz:colour', 'note': 'x'}), 'a stale discrepancy',
     'discrepancy:'),
    # the second variant, harddrop's second type
    (lambda d: _hdd(d, 1, 3).__setitem__('variant', 'cutcopy'), 'a second-type drawing read as the first type',
     'harddrop:'),
    (lambda d: [x.__setitem__('section', 'Variations, Other Uses and Comparisons') for x in
                d['cross_source']['harddrop']['drawings'] if x['variant'] == 'uncut'],
     'the second type\'s generic structure dropped', 'harddrop:'),
    (lambda d: _set(node(d, 'uncut.spin')['rows'], 1, 7, '-'), 'the external board not its harddrop drawing', 'external:'),
    (lambda d: node(d, 'uncut.after')['source_board'].__setitem__('board', 3), 'the external after board misnamed',
     'external:'),
    (lambda d: d['cross_source']['harddrop'].pop('after_drawn'), 'the drawn after board unrecorded', 'external:'),
    (lambda d: d['page_order'].append('uncut.spin'), 'an external board in shiwehi.com\'s page order', 'grammar:'),
    (lambda d: _var(d, 1)['window'].__setitem__('rows', [1, 4]), 'the second type without its nub row', 'window:'),
    (lambda d: _var(d, 1)['window'].__setitem__('cols', [1, 5]), 'the second type\'s window narrowed', 'window:'),
    (lambda d: _var(d, 1)['followup'].__setitem__('t_cells_pre_clear', [[4, 2], [4, 3], [4, 4], [5, 3]]),
     'the second slot read under the T', 'window:'),
    (lambda d: _var(d, 1)['misses'].remove('basic'), 'a page board not listed for the second type', 'mirror:'),
    (lambda d: _var(d, 0)['misses'].remove('uncut.spin'), 'the second type\'s board in no first-type list', 'mirror:'),
    (lambda d: d['cross_source']['also_technique'].pop(), 'an STMB Cave board the second type fires on unrecorded',
     'cross:'),
    (lambda d: d['cross_source']['also_technique'][0].__setitem__('mirrored', False), 'the STMB Cave relation\'s hand',
     'cross:'),
    (lambda d: d['source'].pop('declined'), 'the declined sources dropped', 'declined:'),
    (lambda d: d['source']['declined'][0].__setitem__('reason', ''), 'a declined source with no reason', 'declined:'),
    # Tetrisちゃんねる
    (lambda d: d['cross_source'].pop('tetrisch'), 'no Tetrisちゃんねる record', 'tetrisch:'),
    (lambda d: _tc(d, '004').__setitem__('sha256', '0' * 64), 'a committed image\'s hash', 'tetrisch:'),
    (lambda d: _set(_tc(d, '002')['rows'], 4, 4, '.'), 'the upright T read with a cell missing', 'tetrisch:'),
    (lambda d: (_set(_tc(d, '002')['rows'], 4, 4, '#'), _set(_tc(d, '002')['rows'], 4, 3, 'T')),
     'the upright T turned about another centre', 'tetrisch:'),
    (lambda d: _set(_tc(d, '004')['rows'], 7, 3, '#'), 'the after board not what the TSD leaves', 'tetrisch:'),
    (lambda d: _set(_tc(d, '008')['rows'], 7, 3, 'J'), 'the coloured board not the basic terrain', 'tetrisch:'),
    (lambda d: d['cross_source']['tetrisch']['edo'].__setitem__('tsds', 2), '江戸城 read as two TSDs', 'tetrisch:'),
    (lambda d: _set(_tc(d, '009')['rows'], 7, 4, 'S'), '江戸城\'s last TSD filled in', 'tetrisch:'),
    (lambda d: _tc(d, '010').pop('annotation'), 'the annotation image unread', 'tetrisch:'),
    (lambda d: d['cross_source']['tetrisch']['slots'].pop('009'), '江戸城 not an agreement drawing', 'tetrisch:'),
]


def _no_external(spec):
    s = copy.copy(spec)
    s.external_drawings = None
    return s


def _second_type_as_drawing(spec):
    s = copy.copy(spec)
    m = next(x for x in build()['cross_source']['harddrop']['drawings'] if (x['table'], x['board']) == (1, 3))
    s.external_drawings = lambda: external_drawings() + [{'name': 'the second type as a drawing', 'rows': _pre(m['rows']),
                                                          't_cells': m['slot'], 'mirrored': False, 'variant': 'cutcopy'}]
    return s


def _stmb_as_second_type(spec):
    s = copy.copy(spec)
    m = next(x for x in build()['cross_source']['harddrop']['drawn_t_not_fired'] if (x['table'], x['board']) == (3, 1))
    s.external_drawings = lambda: external_drawings() + [{'name': 'STMB Cave as the second type', 'rows': _pre(m['rows']),
                                                          't_cells': m['slot'], 'mirrored': False, 'variant': 'uncut'}]
    return s


def _no_tetrisch(spec):
    s = copy.copy(spec)
    s.external_drawings = lambda: [d for d in external_drawings() if not d['name'].startswith('Tetris')]
    return s


SPEC_MUTANTS = [
    (_no_external, 'no external drawing (the window checked against this page alone)', 'window:'),
    (_second_type_as_drawing, 'harddrop\'s second type read as a drawing of the first', 'window:'),
    (_stmb_as_second_type, 'harddrop\'s STMB Cave comparison read as a drawing of the second type', 'window:'),
]


def _synthetic_harddrop(data: dict) -> str:
    """A wikitext holding the recorded boards at their (table, board), every other board blank, each table under its
    recorded heading — the selftest's stand-in for the page CI cannot fetch."""
    hd = data['cross_source']['harddrop']
    every = {}
    for d in _hd_boards(hd):
        every[(d['table'], d['board'])] = d
    n = max(t for t, _ in every) + 1
    tables = [[] for _ in range(n)]
    for (t, b), d in sorted(every.items()):
        tt = tables[t]
        while len(tt) < b:
            tt.append([EMPTY * WIDTH] * 4)
        tt.append(d['rows'])
    for tt in tables:
        if not tt:
            tt.append([EMPTY * WIDTH] * 4)
    sec = {t: d['section'] for (t, _b2), d in every.items()}
    out, last = [], None
    for i, tt in enumerate(tables):
        s = sec.get(i, last)
        if s != last:
            out.append(f'\n== {s} ==\n')
            last = s
        out.append(RT.synthetic_wikitext([tt]))
    return '\n'.join(out)


def _synthetic_tetrisch(data: dict) -> str:
    """A faithful stand-in for the Tetrisちゃんねる page: its quoted sentences and its images, in page order."""
    tc = data['cross_source']['tetrisch']
    body = '<br>'.join(tc['quotes']) + '\n' + '\n'.join(
        f'<img src="../img/t-spin/{e["file"]}" width="176" height="140" alt="cc">' for e in tc['images'])
    return f'<html><body>{body}</body></html>'


def _cross_plant_problems(planted: bool) -> list[str]:
    """The `cross:` rule run with TECHNIQUE_DIR pointed at a temporary directory holding the committed transcriptions and one more:
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
        # the other committed transcriptions too, so the recorded relations (`also_technique`) still hold
        for f in HERE.glob('*-technique.json'):
            if f.name != OUT.name:
                (Path(td) / f.name).write_bytes(f.read_bytes())
        (Path(td) / 'planted-technique.json').write_text(json.dumps(fake))
        TECHNIQUE_DIR = Path(td)
        try:
            bad, _measured = extra_checks(base)
        finally:
            TECHNIQUE_DIR = saved
    return [x for x in bad if x.startswith('cross:')]


def selftest() -> int:
    rc = TT.run_selftest(SPEC, MUTANTS, {'board': ('CCCCCCTTTC', 'CCCCCCTTTc'), 'text': ('T穴からの組み方', 'T穴からの組方')},
                         SPEC_MUTANTS)
    base = build()
    text = _synthetic_harddrop(base)
    row = lambda r: '{{pfrow|' + '|'.join(RT.wikitext_page_cell(ch) for ch in r) + '}}'
    plants = {
        'a recorded drawing redrawn on the page': text.replace(row(_hdd(base, 0)['rows'][3]),
                                                               row(_hdd(base, 0)['rows'][3][:-1] + '-'), 1),
        'a board the window fires on left unrecorded': text.replace('|}', '|{{pfstart}} ' + ' '.join(
            row(r) for r in _hdd(base, 0)['rows']) + ' {{pfend}} |}', 1),
        'a heading renamed': text.replace('== Generic Structures ==', '== Generic Structure ==', 1),
        'a no-T board the window fires on left unrecorded': text.replace('|}', '|{{pfstart}} ' + ' '.join(
            row(r) for r in base['cross_source']['harddrop']['fires_without_slot'][0]['rows']) + ' {{pfend}} |}', 1),
        'a board whose drawn cells are no T\'s': text.replace('|}', '|{{pfstart}} ' + ' '.join(
            row(r) for r in ['UUU-------', 'U---------']) + ' {{pfend}} |}', 1),
    }
    ok = rc == 0
    clean = harddrop_page_problems(base, text)
    if clean or 'Generic Structures' not in text:
        print(f'selftest FAILED: the synthetic harddrop page does not verify ({clean[:2]})')
        ok = False
    for label, drop in (('a drawn T the window misses left out of the record', (3, 1)),
                        ('one of three T\'s on a board left out of the record', (8, 1))):
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
    for label, page in plants.items():
        got = harddrop_page_problems(base, page)
        if page == text or not any(x.startswith('harddrop:') for x in got):
            print(f'selftest FAILED: {label} was not caught ({got[:2]})')
            ok = False
        else:
            print(f'  killed: {label}  [harddrop:]')
    # --html-dir, Tetrisちゃんねる's half: a synthetic page and the committed images, clean and corrupted
    tc = base['cross_source']['tetrisch']
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        if not any('is not in' in x for x in tetrisch_snapshot_checks(base, p)):
            print('selftest FAILED: a missing Tetrisちゃんねる snapshot was not caught')
            ok = False
        (p / Path(tc['images_dir']).name).mkdir()
        for e in tc['images']:
            (p / Path(tc['images_dir']).name / e['file']).write_bytes((IMG_DIR / e['file']).read_bytes())
        page = _synthetic_tetrisch(base)
        (p / tc['snapshot_file']).write_text(page)
        clean = [x for x in tetrisch_snapshot_checks(base, p) if 'hash:' not in x and 'pillow:' not in x]
        if clean:
            print(f'selftest FAILED: the synthetic Tetrisちゃんねる page does not verify ({clean[:2]})')
            ok = False
        for label, text in (('a Tetrisちゃんねる sentence edited', page.replace('交互にずれている', '交互にずらしている')),
                            ('a Tetrisちゃんねる image left unrecorded',
                             page + '<img src="../img/t-spin/cutcopy_011.jpg">'),
                            ('Tetrisちゃんねる\'s images out of order',
                             page.replace('cutcopy_008.jpg', 'X').replace('cutcopy_009.jpg', 'cutcopy_008.jpg')
                             .replace('X', 'cutcopy_009.jpg'))):
            (p / tc['snapshot_file']).write_text(text)
            got = [x for x in tetrisch_snapshot_checks(base, p) if 'hash:' not in x and 'pillow:' not in x]
            if not got:
                print(f'selftest FAILED: {label} was not caught')
                ok = False
            else:
                print(f'  killed: {label}  [tetrisch:]')
        (p / tc['snapshot_file']).write_text(page)
        img = p / Path(tc['images_dir']).name / 'cutcopy_003.jpg'
        img.write_bytes((IMG_DIR / 'cutcopy_006.jpg').read_bytes())
        got = tetrisch_snapshot_checks(base, p)
        if not any('cutcopy_003.jpg' in x for x in got):
            print(f'selftest FAILED: an image swapped was not caught ({got[:2]})')
            ok = False
        else:
            print('  killed: a Tetrisちゃんねる image swapped for another  [tetrisch:]')
    with tempfile.TemporaryDirectory() as td:
        missing = harddrop_snapshot_checks(base, Path(td))
        (Path(td) / base['cross_source']['harddrop']['snapshot_file']).write_text(text)
        hashed = harddrop_snapshot_checks(base, Path(td))
    if not any('is not in' in x for x in missing) or not any('hash:' in x for x in hashed):
        print(f'selftest FAILED: the harddrop snapshot (missing={missing[:1]}, hashed={hashed[:1]})')
        ok = False
    else:
        print('  killed: the harddrop snapshot missing / its bytes not the pinned revision  [harddrop:]')
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

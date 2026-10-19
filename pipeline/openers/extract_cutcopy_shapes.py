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
of the shape agrees: this page's three (the basic form, and its two builds, both drawn MIRRORED) and seven from
harddrop (another site, other authors): five on its own Cut_copy page, pinned below, and the one its BT_Cannon
page draws, read from `btcannon-technique.json`. It comes out four rows by six columns: the outer slot's arms row
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
T-spin. Two of its cells are the outer slot's wall beside its arms, which every drawing fills; with the Z left
out the window fires nowhere on the build (`extra_checks` measures it), so a Cut Copy built that way is no hit.

WHAT IS AN INFERENCE, flagged in the JSON (`reading`, the legend) rather than in prose only:

  * upper-case `C` and `T` in a spin board: the cleared rows, muted (checked by the spin rule).
  * the page draws what the first TSD leaves only with the second T already in (`second.spin`); the board between
    them, which the page does not draw, is DERIVED (`basic.after`, that board less its T) and measured to be what
    the first TSD leaves.
  * the two builds' grey terrains are DERIVED (each build less its page pieces).
  * harddrop's cell codes: `P` is the placed T (read `U`), blank empty, every other code its last letter in lower
    case, every one filled (BT砲's reading, imported).
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
OUT = HERE / 'cutcopy-technique.json'
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
]

#: the variant's window, in basic.spin's frame
VARIANTS = [{
    'id': 'cutcopy', 'board': 'basic.spin', 'spin': 'TSD', 'lines': 2,
    'window_basis': 'agreement',
    'window': {'rows': [2, 5], 'cols': [4, 9]},
    't_cells': [[3, 6], [3, 7], [3, 8], [4, 7]],
    'roof_cells': [[2, 4], [2, 8], [2, 9]],
    'window_note': 'in basic.spin\'s frame, row 0 the top: the AGREEMENT BOX of this page\'s three drawings of the shape '
                   'and harddrop\'s six. Row 2 is the outer slot\'s arms row: its three cells empty, the wall beside them '
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
    'misses': ['second.spin', 'basic.after', 'hole.terrain', 'col3.terrain'],
    #: a Cut Copy the page describes and the window does not fire on: measured, not fitted
    'not_expressed': [
        {'board': 'hole.osz', 'less': 'z', 'quote': 'z_later',
         'reason': 'the page lets the T-hole build\'s Z go in after the first T-spin. Two of its cells are the outer '
                   'slot\'s wall beside its arms row, which every drawing fills, so with the Z left out the window fires '
                   'nowhere on the build: a Cut Copy built in that order is no hit'},
    ],
}]


def _hd(table: int, board: int, section: str, mirrored: bool, slot: list, rows: str) -> dict:
    return {'table': table, 'board': board, 'section': section, 'mirrored': mirrored, 'slot': slot, 'rows': _b(rows)}


def _miss(table: int, board: int, section: str, slot: list, t: str, lines: int, window: str, note: str,
          rows: str) -> dict:
    return {'table': table, 'board': board, 'section': section, 'slot': slot, 't': t, 'lines': lines,
            'window': window, 'note': note, 'rows': _b(rows)}


GS, VO = 'Generic Structures', 'Variations, Other Uses and Comparisons'
_SECOND = ('the page\'s second type, 「Uncut copy」: the whole second T-Spin Double saved underneath, so a full TSD '
           'slot lies under the T rather than the first type\'s half')
_YAKINE = ('yakine\'s repeating pattern of the second type: three T\'s drawn on one board, read with all three slots '
           'empty (a board that never stands at once)')
_DONATION = '「Using Cut copy along with Donation」: a donation, not the first type\'s slot under the T'

#: harddrop's Cut_copy page: every board on it with a drawn T (`P`) the window fires on, read with `hd_cell`
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
    'snapshot_note': 'not committed, and not discovered by check_wikitext_sources (which reads *-routes.json): '
                     're-check with --html-dir, the file beside cutcopy.html',
    'author_note': 'harddrop\'s page, edited by its wiki editors (it credits the repeating pattern to yakine): another '
                   'site and other authors than shiwehi.com, and the page shiwehi.com cites as its reference',
    'reading': {'blank': '-', 'P': 'U, the T placed into the spin (the slot the agreement rule fires the window at)',
                'other': 'any other code, its last letter in lower case (G grey), every one FILLED (BT砲\'s hd_cell)',
                'slots': 'a board\'s U cells are partitioned into T\'s; each T is one slot, read with every U cell of '
                         'the board empty'},
    'drawings': [
        _hd(0, 3, GS, False, [[4, 3], [4, 4], [4, 5], [5, 4]],
            '---------- --z------- -zz--oo--l gz---oolll gzzUUUgggg ggzzUggggg ggg-gggggg'),
        _hd(4, 3, VO, False, [[4, 3], [4, 4], [4, 5], [5, 4]],
            '---------- --z------- -zz------- gz---ggggg ggsUUUgggg ggssUggggg ggg-gggggg'),
        _hd(5, 1, VO, False, [[4, 3], [4, 4], [4, 5], [5, 4]],
            '---------- --z------- -zz------- gz---ggggg ggsUUUgggg ggssUggggg ggg-gggggg'),
        _hd(9, 1, VO, False, [[4, 3], [4, 4], [4, 5], [5, 4]],
            '---------- --z------- -zz--lllgg jz---loogg jjjUUUoogg iiiiUssggg ggg-ssgggg ggg---gggg gggg-ggggg'),
        _hd(11, 2, VO, True, [[7, 4], [7, 5], [7, 6], [8, 5]],
            '---------- ----jj---- g---j----- g---j-zzll giiii--zzl ggggg--ggl ggggg---gg ggggUUUggg gggggUgggg '
            'gggggg-ggg'),
    ],
    #: every OTHER drawn T on the page: the window does not fire at it in either hand, each named with what the T
    #: is, measured (`t` its lie, `lines` the rows it clears as drawn, `window` why it does not fire) and a note read
    #: off the page around it. With `drawings` this is EVERY drawn T on the page
    'drawn_t_not_fired': [
        _miss(1, 3, GS, [[2, 2], [2, 3], [2, 4], [3, 3]], 'flat-down', 2, 'disagrees', _SECOND,
              '---------- gg--zzgggg ggUUUzzggg lllUoogggg l---oogggg gg-ggggggg'),
        _miss(2, 3, VO, [[3, 2], [3, 3], [3, 4], [4, 3]], 'flat-down', 2, 'disagrees',
              '「Cut copy could be made using pieces other than the generic structure」: the second type\'s full slot '
              'under the T', '---------- oo--s----- oo--ssgggg zzUUUsgggg gzzUjggggg g---jggggg gg-jjggggg'),
        _miss(3, 0, VO, [[3, 2], [3, 3], [3, 4], [4, 3]], 'flat-down', 2, 'disagrees',
              'the same variation again, beside STMB Cave for comparison',
              '---------- oo--s----- oo--ssgggg zzUUUsgggg gzzUjggggg g---jggggg gg-jjggggg'),
        _miss(3, 1, VO, [[3, 2], [3, 3], [3, 4], [4, 3]], 'flat-down', 2, 'disagrees',
              'STMB Cave, drawn beside the variation for comparison (「Compare the variation of Cut copy above with STMB '
              'Cave」)', '---------- ----s----- ----ssgggg zzUUUsgggg gzzUoogggg g---oogggg g---gggggg'),
        _miss(6, 1, VO, [[3, 4], [4, 4], [4, 5], [5, 4]], 'stood', 1, "not the window's T",
              'a stood T into one row, on the L-built board drawn after the Parapet comparison',
              '---------- -jj------- -j-------- gjl-Uggggg ggl-UUgggg ggllUggggg ggg-gggggg ggg-gggggg'),
        _miss(7, 1, VO, [[4, 3], [4, 4], [4, 5], [5, 4]], 'flat-down', 2, 'disagrees',
              '「Repeating the second type of Cut copy」: the first T, over the second type\'s full slot',
              '---------- ------z--- -oo--zz--- joo--zl--- jjjUUUlggg iiiiUllggg gg---ssggg ggg-ssgggg ggg---gggg '
              'gggg-ggggg'),
        _miss(7, 2, VO, [[6, 2], [6, 3], [6, 4], [7, 3]], 'flat-down', 2, 'disagrees',
              'the same repeat, its second T over the next full slot',
              '---------- ---------- ---------- ------z--- -oo--zz--- joo--zl--- ggUUUssggg gggUssgggg ggg---gggg '
              'gggg-ggggg'),
        _miss(8, 1, VO, [[3, 3], [3, 4], [3, 5], [4, 4]], 'flat-down', 2, 'disagrees', _YAKINE,
              '---------- ggoo---zgg ggoo--zzgg ggsUUUzlgg ggssUlllgg ggjsUUUzgg ggjjjUzzgg gggUUUzlgg ggggUlllgg'),
        _miss(8, 1, VO, [[5, 4], [5, 5], [5, 6], [6, 5]], 'flat-down', 2, 'disagrees', _YAKINE,
              '---------- ggoo---zgg ggoo--zzgg ggsUUUzlgg ggssUlllgg ggjsUUUzgg ggjjjUzzgg gggUUUzlgg ggggUlllgg'),
        _miss(8, 1, VO, [[7, 3], [7, 4], [7, 5], [8, 4]], 'flat-down', 2, 'leaves the board', _YAKINE,
              '---------- ggoo---zgg ggoo--zzgg ggsUUUzlgg ggssUlllgg ggjsUUUzgg ggjjjUzzgg gggUUUzlgg ggggUlllgg'),
        _miss(9, 2, VO, [[5, 2], [5, 3], [5, 4], [6, 3]], 'flat-down', 2, 'disagrees',
              '「mix both types of Cut copy to make three consecutive T-Spin Doubles」: the second T, over the second '
              'type\'s full slot (the first T, board 1, is a first-type Cut Copy and is a drawing)',
              '---------- ---------- ---------- --z------- -zz--lllgg jzUUUloogg gggUssgggg ggg---gggg gggg-ggggg'),
        _miss(10, 0, VO, [[4, 4], [4, 5], [4, 6], [5, 5]], 'flat-down', 2, 'disagrees', _DONATION,
              '---------- ---------- ---oo----- ---oo----- iiiiUUUssz jjjggUsszz --jggg-gz-'),
        _miss(10, 1, VO, [[3, 3], [3, 4], [3, 5], [4, 4]], 'flat-down', 2, 'disagrees', _DONATION,
              '---------- -----oo-l- -----oo-l- gzzUUUssll ggzzUssgjj gg---gggj- ggg-ggggj-'),
        _miss(10, 2, VO, [[4, 5], [4, 6], [4, 7], [5, 6]], 'flat-down', 2, 'disagrees', _DONATION,
              '---------- ---------- g--------- g------zz- giiiiUUUzz glllssUggg gl-ss-gggg'),
        _miss(10, 3, VO, [[3, 4], [3, 5], [3, 6], [4, 5]], 'flat-down', 2, 'disagrees', _DONATION,
              '---------- ---------- -j----zz-i sjjjUUUzzi sslllUgggi -sl---gggi -ggg-ggggg'),
        _miss(12, 2, VO, [[6, 3], [6, 4], [6, 5], [7, 4]], 'flat-down', 2, 'disagrees',
              '「make a Cut copy underneath an STSD」, its second drawing: the T over the second type\'s full slot',
              '---------- i-ss------ iss----ggg ioo-jjjggg ioo--gjggg ggg--ggggg gggUUUgggg ggggUggggg gg---ggggg '
              'ggg-gggggg'),
    ],
    #: boards with no T drawn on which the window fires at a resting placement: the same shape one step before
    #: the page draws its T, recorded letter for letter; `mirrored` is the hand it fires in
    'fires_without_slot': [
        _hd(0, 2, GS, False, [[4, 3], [4, 4], [4, 5], [5, 4]],
            '---------- --z------- -zz--oo--l gz---oolll gzz---gggg ggzz-ggggg ggg-gggggg'),
        _hd(11, 1, VO, True, [[7, 4], [7, 5], [7, 6], [8, 5]],
            '---------- ---------- g--------- g--------- g--------- gggoo--zz- gggoo---zz gggg---ssg ggggg-ssgg '
            'gggggg-ggg'),
    ],
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
    'note': 'the window, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot board of every '
            'committed *-routes.json, with the U cells as the T: it fires on none (no route page draws a Cut Copy). The '
            'independent drawer is harddrop instead: its Cut_copy page (`harddrop`, the page this page cites) and the '
            'Cut Copy its BT_Cannon page draws (`bt_cannon`). Their drawings are the window\'s external `agreement` '
            'drawings: rule (g) fires the window on each, once, at its drawn T, in its recorded hand.',
    'routes_fire_none': 'no committed routes file draws a Cut Copy (measured: the window fires on none of their U-slot '
                        'boards, and no node is labelled 千鳥格子 or Cut Copy); the cross-check is harddrop\'s own pages, '
                        'read below',
    'harddrop': HARDDROP,
    'bt_cannon': BT_CANNON,
    'fires': [],
    'also': [],
    'labelled_not_fired': [],
}

KNOWN_DISCREPANCIES: list[dict] = []

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


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
    """harddrop's Cut_copy drawings as agreement drawings: the slot is its drawn T, every drawn T read as empty."""
    data = data or build()
    return [{'name': f'harddrop Cut_copy table {d["table"]} board {d["board"]} ({d["section"]})',
             'rows': _pre(d['rows']), 't_cells': d['slot'], 'mirrored': d['mirrored']}
            for d in data['cross_source']['harddrop']['drawings']]


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
    return harddrop_drawings() + [{k: d[k] for k in ('name', 'rows', 't_cells', 'mirrored')}]


def harddrop_page_problems(data: dict, text: str) -> list[str]:
    """The recorded drawings against the harddrop wikitext: each letter for letter at its (table, board) under its
    heading, and the record COMPLETE both ways — `drawings` exactly the drawn T's the window fires at (either hand),
    `drawn_t_not_fired` exactly every other drawn T, `fires_without_slot` exactly the boards with no T drawn on which
    it fires. A board's drawn cells are read as T's (`hd_slots`), so a board drawing several T's is read T by T."""
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
        if not n.get('derived') and n['id'] not in listed:
            bad.append(f'mirror: drawn board {n["id"]} is in none of fires_on, fires_mirrored, misses')
    want = sorted([(b, False) for b in v.get('fires_on', [])] + [(b, True) for b in v.get('fires_mirrored', [])])
    if sorted((a['board'], a['mirrored']) for a in v.get('agreement', [])) != want:
        bad.append('mirror: the page\'s agreement drawings are not fires_on (as drawn) and fires_mirrored (mirrored)')
    # later: a Cut Copy the page describes and the window does not express, both halves measured
    qids = {q['id'] for q in data['quotes']}
    for e in v.get('not_expressed', []):
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
        elif _fires_anywhere(data, less):
            bad.append(f'later: the window fires on {e["board"]} less {e["less"]!r}, listed as not expressed')
        if not _fires_anywhere(data, n['rows']):
            bad.append(f'later: the window does not fire on {e["board"]} with its pieces in either')
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
    if not any(d['section'] == 'Generic Structures' for d in hd.get('drawings', [])):
        bad.append('harddrop: no recorded drawing from the page\'s own Generic Structures section')
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
    for d in hd.get('fires_without_slot', []):
        hits = _fires_anywhere(data, d['rows'])
        if any('U' in r for r in d['rows']) or hits != [(d['slot'], d['mirrored'])]:
            bad.append(f'harddrop: table {d["table"]} board {d["board"]} draws a T, or the window does not fire on it '
                       f'once at {d["slot"]} ({"mirrored" if d["mirrored"] else "as drawn"})')
    if hd.get('page') not in ' '.join(data['source'].get('references', [])):
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
                    if _hands(data, e['rows'], s):
                        got.append((e['table'], e['board'], _hands(data, e['rows'], s)))
                if not slots and _fires_anywhere(data, e['rows']):
                    got.append((e['table'], e['board'], None))
            if got != [(bc['table'], bc['board'], [bc['mirrored']])]:
                bad.append(f'bt: this window fires on {bc["file"]}\'s harddrop boards {got}, not once at '
                           f'table {bc["table"]} board {bc["board"]} ({"mirrored" if bc["mirrored"] else "as drawn"})')
    # same author: this window fires on no board of the other shiwehi.com technique transcriptions (measured)
    for f in sorted(HERE.glob('*-technique.json')):
        if f.name == OUT.name:
            continue
        other = json.loads(f.read_text())
        ospec = TT.TechniqueSpec(out=f, build=lambda: other, alphabet=frozenset(),
                                 empty_letters=other.get('empty_letters', ''), max_rows=99)
        for n in other['nodes']:
            sc = TT.spin_cells(n) if n['kind'] == 'spin' else set()
            pre = [''.join(EMPTY if (r, c) in sc else ch for c, ch in enumerate(row)) for r, row in enumerate(n['rows'])]
            if any(TT.window_fires(data, v, ospec, pre, cs, m) for cs in TT.t_placements(pre, ospec) for m in (False, True)):
                bad.append(f'cross: this window fires on {f.name} {n["id"]} (record it, or measure why not)')
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
    html_checks=harddrop_snapshot_checks,
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
    (lambda d: _set(node(d, 'hole.osz')['rows'], 1, 4, 'z'), 'a piece broken', 'discrepancy:'),
    (lambda d: _hdd(d, 0).__setitem__('mirrored', True), 'a harddrop drawing read mirrored', 'harddrop:'),
    (lambda d: _set(_hdd(d, 0)['rows'], 3, 1, '-'), 'a harddrop drawing\'s outer wall dropped', 'harddrop:'),
    (lambda d: _hdd(d, 4).__setitem__('slot', [[7, 3], [7, 4], [7, 5], [8, 4]]), 'a harddrop slot moved', 'harddrop:'),
    (lambda d: [x.__setitem__('section', 'Variations, Other Uses and Comparisons')
                for x in d['cross_source']['harddrop']['drawings']], 'the generic structure dropped', 'harddrop:'),
    (lambda d: d['cross_source']['harddrop']['drawings'].append(copy.deepcopy(_hdd(d, 0))), 'a harddrop drawing twice',
     'harddrop:'),
    (lambda d: _hdm(d, 6, 1).__setitem__('t', 'flat-down'), 'a missed drawn T\'s lie misrecorded', 'harddrop:'),
    (lambda d: _hdm(d, 1, 3).__setitem__('window', 'leaves the board'), 'why the window misses misrecorded', 'harddrop:'),
    (lambda d: _hdm(d, 8, 1, 1).__setitem__('lines', 3), 'a missed T\'s line count misrecorded', 'harddrop:'),
    (lambda d: _hdm(d, 10, 2).__setitem__('note', ''), 'a missed drawn T with no note', 'harddrop:'),
    (lambda d: _hdm(d, 8, 1, 2).__setitem__('slot', [[3, 3], [3, 4], [3, 5], [4, 4]]), 'a T recorded twice', 'harddrop:'),
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
]


def _no_external(spec):
    s = copy.copy(spec)
    s.external_drawings = None
    return s


def _second_type_as_drawing(spec):
    s = copy.copy(spec)
    m = next(x for x in build()['cross_source']['harddrop']['drawn_t_not_fired'] if (x['table'], x['board']) == (1, 3))
    s.external_drawings = lambda: external_drawings() + [{'name': 'the second type as a drawing', 'rows': _pre(m['rows']),
                                                          't_cells': m['slot'], 'mirrored': False}]
    return s


SPEC_MUTANTS = [
    (_no_external, 'no external drawing (the window checked against this page alone)', 'window:'),
    (_second_type_as_drawing, 'harddrop\'s second type read as a drawing of the shape', 'window:'),
]


def _synthetic_harddrop(data: dict) -> str:
    """A wikitext holding the recorded boards at their (table, board), every other board blank, each table under its
    recorded heading — the selftest's stand-in for the page CI cannot fetch."""
    hd = data['cross_source']['harddrop']
    every = {}
    for d in hd['drawings'] + hd['drawn_t_not_fired'] + hd['fires_without_slot']:
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
    for label, drop in (('a drawn T the window misses left out of the record', (1, 3)),
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

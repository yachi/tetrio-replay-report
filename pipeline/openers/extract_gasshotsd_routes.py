"""Transcribe shiwehi.com's 合掌TSDパフェ (Gassho TSD) route page into `gasshotsd-routes.json`.

    python3 -m pipeline.openers.extract_gasshotsd_routes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_gasshotsd_routes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_gasshotsd_routes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_gasshotsd_routes --html-dir <dir> --write  # ...and rewrite

The seventh opener ROUTE page, after SDPC Spin. It is a bag-1 OPENING (開幕テンプレ), not a TST opener
and not a mid-game technique: the bag-1 T is stacked in the stack, and the opening TSD is the bag-2 T
into the 3-wide hole. Every rule the openers share is `route_transcription.py`'s, once; this file holds
the transcription, its `SPEC` and the rules only this page needs (`_gassho_checks`).

WHERE THE TRANSCRIPTION COMES FROM. `BOARDS` below is a literal, hand-checked transcription of the
page's RAW HTML, fetched the way 山岳積み2号's was: curl through the session proxy, TLS verification
on, with a CA bundle adding the Let's Encrypt YE2 intermediate shiwehi.com omits. The hash is of the
page's own bytes. The page is not committed; CI cannot fetch it. Boards are plain text in
`<div class="ttt">`, one row per line, 36 of them. There are no fumen codes on the page.

WHAT IS AN INFERENCE, flagged in the JSON rather than in prose only:

  * the catalogue node is `bag1.left`, the hole-empty 基本形 (the T already stacked, no `U`). The
    TSD-overlay board (`2.tsd`) is the same occupancy with the hole drawn `U`; putting that board in
    the catalogue fails rule 2, so it is an illustration.
  * the I-early board is the same occupancy coloured differently (the page says 同形). It is not a
    second bag-1 shape and not a catalogue field.
  * 「4ラインパフェ」 and 「6ラインパフェ」 count the TSD's two lines. The drawn PC bodies are 2 rows
    and 4 rows (`pc_lines` 2 and 4). A list checked at 6 fails rule 3.
  * upper-case `C` is a cell of an earlier bag in a row the TSD clears (the renderer's muted grey).
    `h n k m r y u` are the renderer's second shade of I O J L S Z T.
  * under the ZJO heading the page says 「SLOを先置き」. That is the page's typo; the board is Z, J
    and O. Recorded in `known_discrepancies`, not copied as the setup.
  * the 63-stack board is 9 rows and the REN-after board is 10. Both are taller than the classifier's
    8 rows, so both are `unmatchable`.

THE TERMS are the same shiwehi.com terms page 迷走砲 links to, imported from that transcription
rather than copied (read 2026-10-11 there; not re-read for this page).
"""
from __future__ import annotations

import copy
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS
from pipeline.openers.route_transcription import EMPTY, after_spin, bottom, mirror, node, occ, setcell, t_slot

HERE = Path(__file__).resolve().parent
OUT = HERE / 'gasshotsd-routes.json'

ALPHABET = frozenset('-ijlostzcUChnkmryu')
#: the renderer's second shade, a later piece of the same letter (column-exp.js colorMap)
SHADE = {'h': 'i', 'n': 'o', 'k': 'j', 'm': 'l', 'r': 's', 'y': 'z', 'u': 't'}
CATALOGUE_NAME = 'Gassho TSD PC {JP: 合掌TSDパフェ}'


def _b(text: str) -> list[str]:
    return text.split()


#: the 36 boards in page order, each exactly as `<div class="ttt">` draws it
BOARDS = [
    '---------- ijj------l ij---zslll ijt-zzssoo itttz--soo',
    '---------- j------lli jjjzs---li oozzss-tli ooz--sttti',
    '---------- ttt------l jt---zslll jjj-zzssoo iiiiz--soo',
    '---------- ijj------l ij---zslll ijt-zzssoo itttz--soo',
    '---------- ccc------c CCUUUCCCCC CCCUCCCCCC ccccc--ccc',
    '---------- ---------- ---------- CCCjjjlllC CCCCCjlCCC',
    '---------- ---------- ---zz-s--- ----zzssoo ---iiiisoo',
    '---------- ---------- l--cc-c--- lUUUcccccc llUccccccc',
    '---------- oo-----jjz oo-----jzz ccc----jzc CCUUUCCCCC CCCUCCCCCC ccccc--ccc',
    '---------- ccsllihccc ccsslihccc cccslihccc cccccihccc',
    '---------- ccsiiiiccc ccsslllccc cccslnnccc cccccnnccc',
    '---------- ccsuuuiccc ccsslliccc cccsuliccc cccccliccc',
    '---------- ccsiiiiccc ccssyylccc cccslllccc cccccyyccc',
    '---------- ccsllmmccc ccsslkkccc cccslkmccc ccccckmccc',
    '---------- ccsllkkccc ccsslmmccc cccslkmccc ccccckmccc',
    '---------- ccsiiiiccc ccssrllccc cccsrrlccc cccccrlccc',
    '---------- ccslliiiic ccssljsscc cccsljjjcc cccccssccc',
    '---------- oo-----lll oo-----lss ccc----ssc CCUUUCCCCC CCCUCCCCCC ccccc--ccc',
    '---------- ccjjjihccc cczzjihccc ccczzihccc cccccihccc',
    '---------- ccnnjjjccc ccnnzzjccc ccciiiiccc ccccczzccc',
    '---------- cczzuuuccc cciiiijccc ccczzujccc cccccjjccc',
    '---------- ccyyjjjccc cciiiizccc cccyyzzccc ccccczjccc',
    '---------- ccriiiiccc ccrrjjjccc cccrzzjccc ccccczzccc',
    '---------- ccjjjkkccc cczzjkuccc ccczzuuccc ccccckuccc',
    '---------- ccjjjmmccc cczzjumccc ccczzuuccc cccccumccc',
    '---------- ccjjjmmccc cczzjkkccc ccczzkmccc ccccckmccc',
    '---------- ccjjjkkccc cczzjmmccc ccczzkmccc ccccckmccc',
    '---------- ---------- ---------- loo------- loo----j-z llUUUssjzz cccUssjjzc cc---ccccc ccc-cccccc ccccc--ccc',
    '---------- ---------- ---------- jjj------- ooj----l-z ooUUUlllzz cccUiiiizc cc---ccccc ccc-cccccc ccccc--ccc',
    '---------- ---------- ---------- ccc------- ccc----c-c cc---ccccc ccc-cccccc ccccc--ccc',
    '---------- -------jjj -------zzj --------zz -------lll j------lss jjj----ssc CCUUUCCCCC CCCUCCCCCC ccccc--ccc',
    '---------- ---------- ---------- -------jjj CCCCC--zzj CCCCC---zz CCCCCi-lll CCCooi-lss cccooi-ssc ccccci-ccc',
    '---------- ---------- ---------i ------zz-i j------zzi jjj----ooi ccc----ooc CCUUUCCCCC CCCUCCCCCC ccccc--ccc',
    '---------- ---------- ---------- ---------- ---------i ------zz-i j------zzi jjj-ss-ooi cccss--ooc ccccc--ccc',
    '---------- ---------- i------jjj il-----ooj il----sooz ill---sszz ccc----szc CCUUUCCCCC CCCUCCCCCC ccccc--ccc',
    'i------lll i------loo i------joo is-----jjj css----ccc ccs----ccc ccUUUzcccc cccUzzcccc ccc-z--ccc ccccc--ccc',
]


def _rows(i: int) -> list[str]:
    """Board `i` (1-based, page order)."""
    return _b(BOARDS[i - 1])


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/gasshotsd.php',
    'title': '合掌TSDパフェ(Gassho TSD Opener)',
    'updated': '2026-08-10',
    'created': '2021-02-04',
    'fetched': '2026-11-26',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle '
                    'that adds the Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), '
                    'the method 山岳積み2号 used. The snapshot is the page\'s raw HTML, byte for byte; every '
                    'board is plain text in it, 36 ten-wide boards in page order. No fumen codes.',
    'snapshot_file': 'gasshotsd.html',
    'snapshot_sha256': '9a6082ed37415dc74e979b17e77ce14ab30cf9386fe4116e3eb57dd900e86229',
    'snapshot_bytes': 33283,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable '
                     'in CI: the page is not committed and cannot be fetched there. Re-check with '
                     '--html-dir after any refetch; an HTML hash moves with ANY byte of the page.',
    'video': 'https://www.youtube.com/watch?v=w-9uFdHtm7s',
    'renderer': {
        'url': 'https://shiwehi.com/tetris/mutual/column-exp.js?date=20210408',
        'read': '2026-11-26',
        'sha256': '95c431a4147f9c30fc0e1bae935e6af6f5669c3d2fa1edfc388848e69ab62570',
        'sha256_note': 'the same bytes 山岳積み2号 recorded on 2026-10-12, re-fetched for this page',
        'colorMap_used': {
            'c': '#a3a3a3', 'C': '#cccccc', 'U': '#c8a6ff with a #8400ff radial dot',
            'h n k m r y u': 'second shade of I O J L S Z T (#b0e7ff #ffffcc #a6bbff #ffcea6 #a6ffa6 #ffa6a6 #c8a6ff)',
            '-': '#000000',
        },
        'rows': 'textContent split on whitespace, one row per token; .ttt is drawn, one row per line',
        'mirror_button': 'body.reversed swaps j<->l, s<->z, k<->m, r<->y (and upper case)',
    },
    'decorative_images': ['合掌TSDパフェ(Gassho TSD Opener)タイトル画像', '合掌TSDパフェの派生概要図'],
    'related_pages': ['./tsdopener.php', './antifatetsd.php', './stsd.php', './biginnertemplate.php'],
    'references_commented': 'the 参考ページ block is inside an HTML comment and names にはち砲 / Hachispin, '
                            'not this opener; not used as a source',
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ, align at the BOTTOM row',
    '-': 'empty',
    'i o t s z j l': 'a cell of that piece',
    'c': 'a cell filled before this diagram (earlier bags), grey',
    'C': 'the same, in a row the TSD clears, drawn in the renderer\'s muted grey (OUR READING, checked: every C row is a row the U slot clears)',
    'U': 'the TSD slot (the 3-wide hole). Not the bag-1 T, which is already stacked as t',
    'h n k m r y u': 'the renderer\'s second shade of I O J L S Z T: a later piece of that letter',
    '%X': "the X piece; '%T>%J' means T before J; '%O・%S>%L' means both O and S before L",
}

QUOTES = [
    {'id': 'overview.intro', 'figure': None,
     'verbatim': 'ここでは、合掌TSDパフェ(Gassho TSD PC Opener)というTSDから6ラインパフェを狙う開幕テンプレについて紹介していきます。'},
    {'id': 'basic.mirror', 'figure': None,
     'verbatim': '形は上の通りで、左右反転できます。ここでは左図で統一して説明していきますが、右下にある反転ボタンを押すことで左右反転の図を見ることができます。'},
    {'id': 'bag1.i_early', 'figure': None,
     'verbatim': '一応下記のように同形を組むこともできますが、%Iが早い時には開幕TSDを打つ人が多いのでは無いでしょうか。'},
    {'id': 'bag1.requires', 'figure': None,
     'verbatim': '1巡目の組み方は上図の通りで、%O%S%Zや%T%S%Zが早い時に組むと良いでしょう。'},
    {'id': 'bag1.no_hold', 'figure': None, 'verbatim': 'ホールド無しで組める条件は以下の通りです。'},
    {'id': 'bag1.no_hold.os_l', 'figure': None, 'verbatim': '%O・%S>%L'},
    {'id': 'bag1.no_hold.t_j', 'figure': None, 'verbatim': '%T>%J'},
    {'id': '2.pc4', 'figure': '5.71%',
     'verbatim': '2巡目の%T%J%Lが早い場合にはTSDを打ってから4ラインパフェを取ることができます(5.71%)。',
     'fraction': '288/5040',
     'fraction_note': 'OUR READING of the printed 5.71%: 288/5040 = 5.714…%, the share of 7! orders. The page prints neither 288 nor 5040, and draws one 2-row solution, not 288'},
    {'id': '2.zjo', 'figure': '95.24%',
     'verbatim': '3ミノ先置きの場合、%Z%J%Oの3ミノであれば高いパフェ率(95.24%)を維持することができます。',
     'fraction': '20/21',
     'fraction_note': 'OUR READING of the printed 95.24%: 20/21 = 95.238…%. The page prints neither 20 nor 21'},
    {'id': '2.zjo.typo', 'figure': '95.24%',
     'verbatim': '%S%L%Oを先置きした場合、パフェの取り方は以下の通りです。(95.24%)',
     'note': 'under the ZJO heading. The setup board is O, J and Z. SLO is the page\'s typo; the real SLO sentence is 2.slo.patterns'},
    {'id': '2.oz', 'figure': '100%',
     'verbatim': '%O%Zの2ミノ先置きの場合、2巡目の初め2ミノが「%L>%S」や「%J>%S」の場合にも対応でき100%でパフェを取ることができます。'},
    {'id': '2.slo', 'figure': None,
     'verbatim': '%Z%Jが遅い場合には、パフェ率は下がりますが%S%Lを先置きすることができます。',
     'note': 'the page states no percentage for the SLO pre-place'},
    {'id': '2.slo.patterns', 'figure': None,
     'verbatim': '%S%L%Oを先置きした場合パフェパターンは多いですが、実戦で使用できそうなものは以下の5パターンでしょう。'},
    {'id': '2.holdi', 'figure': None,
     'verbatim': 'また、2巡目の%Iが遅く、3巡目の%T%J%Lが早い場合には%Iをホールドしたまま下図のようなパフェを狙うことができることも一応覚えておくと良いでしょう。'},
    {'id': '2.donate', 'figure': None, 'verbatim': 'ILJが早い場合には、下記のように積んでドネイトTSDを打つことができます。'},
    {'id': '2.flat', 'figure': None, 'verbatim': 'ミノ順が合わない場合などは、下図などのように積んで63積みに移行します。'},
    {'id': '2.stsd', 'figure': None, 'verbatim': 'もしくは、STSDに派生することができます。'},
    {'id': '2.ren', 'figure': '100%',
     'verbatim': '2巡目は%Jをホールドしておけば、%O%S%Z循環で100%組むことができます。'},
]


BAG1 = {
    'locks': 7,
    'requires_verbatim': QUOTES[3]['verbatim'],
    'requires': {'early_pairs': [['O', 'S', 'Z'], ['T', 'S', 'Z']], 'illustrative': True},
    'requires_note': '「%O%S%Zや%T%S%Zが早い」: the page gives no threshold. Not a trigger the classifier decides',
    'no_hold_verbatim': QUOTES[4]['verbatim'],
    'no_hold': {'all': [{'before': ['O', 'L']}, {'before': ['S', 'L']}, {'before': ['T', 'J']}],
                'node': 'bag1.left'},
    'no_hold_items_verbatim': ['%O・%S>%L', '%T>%J'],
    'no_hold_note': 'the left pattern without hold. %O・%S>%L is both O and S before L (L rests on each); %T>%J is T before J. Checked by support on bag1.left',
    'side_verbatim': QUOTES[1]['verbatim'],
    'side': None,
    'side_note': 'the page says the diagram mirrors and to follow the left one; it names no piece that picks the side',
    'i_early_verbatim': QUOTES[2]['verbatim'],
    'i_early_note': 'the I-early drawing is the same occupancy as bag1.left (同形), coloured differently. Not a second bag-1 node of the matcher and not a catalogue field',
}


def _piece(nid, bag, parent, board, **extra):
    row = {
        'id': nid, 'bag': bag, 'parent': parent, 'rows': _rows(board),
        'label': extra.pop('label', nid),
    }
    row.update(extra)
    if 'U' in ''.join(row['rows']):
        row['spin'] = 'TSD'
    return row


def _pattern(list_id, index, board, parent):
    return {
        'id': f'{list_id}#{index}', 'bag': 2, 'parent': parent, 'list': list_id, 'index': index,
        'base': _BASE_OF[list_id], 'rows': _rows(board), 'listed_under': 'shown',
        'label': f'{list_id} #{index}',
    }


# list id -> the derived residue its c/C cells must equal. Filled before the patterns are built.
_BASE_OF = {
    '2.pc4': '2.tsd.after',
    '2.zjo.pc': '2.zjo.after',
    '2.slo.pc': '2.slo.after',
    '2.holdi.pc': '2.slo.after',
    '2.oz.pc': '2.oz.after',
}


def _page_nodes() -> list[dict]:
    """Every node the page draws, in an order `page_order` can name. Derived residues are added in build()."""
    n = []
    n.append(_piece('bag1.left', 1, None, 1, label='bag 1, the hole-empty 基本形 (T stacked, no U)'))
    n.append(_piece('bag1.right', 1, None, 2, mirror_of='bag1.left',
                    label='bag 1 mirrored (J<->L, S<->Z)'))
    n.append(_piece('bag1.i_early', 1, 'bag1.left', 3, node_kind='same_shape',
                    label='I early: the same occupancy as bag1.left, coloured differently'))
    n.append(_piece('2.tsd', 2, 'bag1.left', 5, node_kind='illustration',
                    label='the TSD slot drawn on the 基本形 (U in the hole; not a second shape)'))
    n.append(_pattern('2.pc4', 1, 6, '2.tsd'))
    n.append(_piece('2.pc4.follow', 3, '2.tsd', 7, label='after the 4-line PC: I O S Z, then wait for L'))
    n.append(_piece('2.pc4.next', 3, '2.tsd', 8, label='the next TSD, L in the well'))
    n.append(_piece('2.zjo', 2, 'bag1.left', 9, group='2.preplace',
                    label='ZJO pre-place, then the TSD'))
    for k, board in enumerate(range(10, 17), start=1):
        n.append(_pattern('2.zjo.pc', k, board, '2.preplace'))
    n.append(_pattern('2.oz.pc', 1, 17, '2.oz'))
    n.append(_piece('2.slo', 2, 'bag1.left', 18, group='2.preplace',
                    label='SLO pre-place, then the TSD'))
    for k, board in enumerate(range(19, 24), start=1):
        n.append(_pattern('2.slo.pc', k, board, '2.preplace'))
    for k, board in enumerate(range(24, 28), start=1):
        n.append(_pattern('2.holdi.pc', k, board, '2.holdi'))
    n.append(_piece('2.donate.a', 2, 'bag1.left', 28, group='2.donate',
                    label='donation TSD, first drawing'))
    n.append(_piece('2.donate.b', 2, 'bag1.left', 29, group='2.donate',
                    label='donation TSD, second drawing'))
    n.append(_piece('2.donate.after', 3, '2.donate', 30, after_of='2.donate.a',
                    label='what both donation drawings leave after the TSD'))
    n.append(_piece('2.flat', 2, 'bag1.left', 31,
                    unmatchable='9 rows: taller than the classifier\'s 8, so the 63-stack pre-TSD board is not compared',
                    label='flat stack into 63-stack, before the TSD'))
    n.append(_piece('2.flat.after', 3, '2.flat', 32, label='63-stack after more pieces (not the bare TSD residue)'))
    n.append(_piece('2.stsd', 2, 'bag1.left', 33, label='STSD branch, the TSD still open'))
    n.append(_piece('2.stsd.after', 3, '2.stsd', 34, label='STSD continuation (S placed; not the bare TSD residue)'))
    n.append(_piece('2.ren', 2, 'bag1.left', 35, label='center-well REN branch, the TSD still open'))
    n.append(_piece('2.ren.after', 3, '2.ren', 36,
                    unmatchable='10 rows: taller than the classifier\'s 8, so the REN-after board is not compared',
                    label='REN after the second TSD'))
    return n


NON_BOARD = {
    'overview.diagram': 'image_only',
    'refs.commented': 'text_only',
    '2.oz': 'text_only',
    '2.holdi': 'text_only',
}


def _non_board() -> list[dict]:
    return [
        {'id': 'overview.diagram', 'bag': 1, 'parent': None, 'node_kind': 'image_only',
         'page_text': '合掌TSDパフェの派生概要図',
         'label': 'the route diagram, an image, no board'},
        {'id': 'refs.commented', 'bag': 1, 'parent': None, 'node_kind': 'text_only',
         'page_text': 'にはち砲 - テトリス開幕テンプレWiki',
         'label': 'the 参考ページ block, inside an HTML comment, names Hachispin'},
        {'id': '2.oz', 'bag': 2, 'parent': 'bag1.left', 'node_kind': 'text_only',
         'page_text': QUOTES[10]['verbatim'],
         'label': 'OZ pre-place: the page draws the PC, not a separate setup board'},
        {'id': '2.holdi', 'bag': 2, 'parent': '2.preplace', 'node_kind': 'text_only',
         'page_text': QUOTES[13]['verbatim'],
         'label': 'hold the I and chase the PC the SLO residue leaves'},
    ]


BASIC_FORM = [
    {'id': 'basic.1', 'same_as': 'bag1.left', 'rows': _rows(4),
     'note': 'the 1巡目 diagram is the 基本形 again, the same cells'},
]

LISTS = [
    {'id': '2.pc4', 'parent': '2.tsd', 'base': '2.tsd.after', 'bag': 2,
     'pc_lines': 2, 'rest_stated': 0, 'stated_pattern_count': None, 'complete': False,
     'heading': '理想形(TSD→4ラインパフェ)',
     'note': 'one 2-row body. The page\'s 4ライン counts the TSD\'s 2 as well (2+2). Rate 5.71% = 288/5040, our reading; the page draws one solution'},
    {'id': '2.zjo.pc', 'parent': '2.preplace', 'base': '2.zjo.after', 'bag': 2,
     'pc_lines': 4, 'rest_stated': 0, 'stated_pattern_count': None, 'complete': False,
     'heading': '3ミノ先置き(ZJO)',
     'note': 'seven 4-row bodies. The page\'s 6ライン is 2+4. Rate 95.24% = 20/21, our reading. The heading\'s next sentence says SLO; that is the typo'},
    {'id': '2.slo.pc', 'parent': '2.preplace', 'base': '2.slo.after', 'bag': 2,
     'pc_lines': 4, 'rest_stated': 0, 'stated_pattern_count': None, 'complete': False,
     'heading': '3ミノ先置き(SLO)',
     'note': 'five 4-row bodies the page calls the practical ones of a larger set. No percentage is stated for this pre-place'},
    {'id': '2.holdi.pc', 'parent': '2.holdi', 'base': '2.slo.after', 'bag': 2,
     'pc_lines': 4, 'rest_stated': 0, 'stated_pattern_count': None, 'complete': False,
     'heading': 'hold I, on the SLO residue',
     'note': 'four 4-row examples (「のような」). Same residue as the SLO list. No percentage'},
    {'id': '2.oz.pc', 'parent': '2.oz', 'base': '2.oz.after', 'bag': 2,
     'pc_lines': 4, 'rest_stated': 0, 'stated_pattern_count': 1, 'complete': True,
     'heading': '2ミノ先置き(OZ)',
     'note': 'the one drawn 4-row shape. The page says 100% and draws one board, not a partial catalogue'},
]

PAGE_ORDER = [
    'bag1.left', 'bag1.right', 'bag1.i_early', 'basic.1', '2.tsd', '2.pc4#1', '2.pc4.follow',
    '2.pc4.next', '2.zjo',
    *[f'2.zjo.pc#{k}' for k in range(1, 8)],
    '2.oz.pc#1', '2.slo',
    *[f'2.slo.pc#{k}' for k in range(1, 6)],
    *[f'2.holdi.pc#{k}' for k in range(1, 5)],
    '2.donate.a', '2.donate.b', '2.donate.after', '2.flat', '2.flat.after', '2.stsd', '2.stsd.after',
    '2.ren', '2.ren.after',
]

KNOWN_DISCREPANCIES = [
    {'id': 'bag1.right:mirror',
     'what': 'the right 基本形 is the left one mirrored (J<->L, S<->Z), so bag 1 is one shape'},
    {'id': 'bag1.i_early:same_occupancy',
     'what': 'the I-early board fills exactly the cells bag1.left fills (the page says 同形) and is not a second bag-1 occupancy'},
    {'id': '2.pc4:non_exhaustive',
     'what': 'the 4-line PC rate is 5.71% and the page draws one 2-row solution'},
    {'id': '2.zjo.pc:non_exhaustive',
     'what': 'seven ZJO solutions are drawn; the stated rate is 95.24% (20/21), not a count of seven'},
    {'id': '2.zjo.pc:slo_typo',
     'what': 'under the ZJO heading the page says 「%S%L%Oを先置き」. The setup board is O, J and Z. Not copied as the setup'},
    {'id': '2.slo.pc:non_exhaustive',
     'what': 'the page says the SLO PC patterns are many and draws the five it calls practical. No rate is stated'},
    {'id': '2.holdi.pc:non_exhaustive',
     'what': 'the hold-I PCs are introduced as examples (のような) and four are drawn'},
    {'id': 'refs.commented:hachispin',
     'what': 'the 参考ページ block is inside an HTML comment and names にはち砲 / Hachispin, a different opener'},
    {'id': '2.oz.pc#1:colour',
     'what': 'the OZ solution draws two S pieces in the same letter (8 s cells). The second shade is what the other PC lists use to separate them; this drawing does not'},
    {'id': '2.flat:colour',
     'what': 'the 63-stack drawing has two J pieces in the same letter (8 j cells), on a board the classifier does not compare (9 rows)'},
]


def _c_skeleton(rows: list[str]) -> list[str]:
    """The PC's grey cells only: the residue a bag-2 list is built on, for a list whose setup is not drawn."""
    return [''.join(ch if ch == 'c' else EMPTY for ch in r) for r in rows]


def _derived(nid, parent, rows, label):
    return {'id': nid, 'bag': 2, 'parent': parent, 'rows': rows, 'derived': True,
            'node_kind': 'illustration', 'label': label}


def build() -> dict:
    nodes = _page_nodes() + _non_board()
    by = {n['id']: n for n in nodes}
    nodes += [
        _derived('2.tsd.after', '2.tsd', after_spin(by['2.tsd']['rows'])[0],
                 'what 2.tsd leaves after the TSD (derived; the 4-line PC\'s grey cells)'),
        _derived('2.zjo.after', '2.zjo', after_spin(by['2.zjo']['rows'])[0],
                 'what 2.zjo leaves after the TSD (derived; the ZJO PC\'s grey cells)'),
        _derived('2.slo.after', '2.slo', after_spin(by['2.slo']['rows'])[0],
                 'what 2.slo leaves after the TSD (derived; the SLO and hold-I PCs\' grey cells)'),
        _derived('2.oz.after', '2.oz', _c_skeleton(by['2.oz.pc#1']['rows']),
                 'the OZ PC\'s grey cells, derived (the page draws no OZ setup)'),
    ]
    lists = []
    for lst in LISTS:
        drawn = sum(1 for n in nodes if n.get('list') == lst['id'])
        lists.append({**lst, 'drawn': drawn, 'shown': drawn - lst['rest_stated']})
    return {
        'schema': 'gasshotsd-routes/1',
        'source': SOURCE,
        'terms': TERMS,
        'legend': LEGEND,
        'quotes': QUOTES,
        'bag1': BAG1,
        'basic_form': BASIC_FORM,
        'groups': [
            {'id': '2.preplace', 'drawn': 2,
             'note': 'ZJO and SLO fill the same cells; J/Z versus L/S tells them apart'},
            {'id': '2.donate', 'drawn': 2,
             'note': 'the two donation drawings fill the same cells; colour tells them apart'},
        ],
        'lists': lists,
        'known_discrepancies': KNOWN_DISCREPANCIES,
        'page_order': PAGE_ORDER,
        'nodes': nodes,
    }


def _cells_of(rows, ch):
    return {(r, c) for r, row in enumerate(rows) for c, x in enumerate(row) if x == ch}


def _verbatims(obj, path=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f'{path}{k}'
            if k.endswith('verbatim') and isinstance(v, str):
                yield here, v
            elif k.endswith('verbatim') and isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, str):
                        yield f'{here}[{i}]', item
            else:
                yield from _verbatims(v, here + '.')
    elif isinstance(obj, list):
        for v in obj:
            yield from _verbatims(v, path)


def _shade_bad(rows) -> list[str]:
    """Second-shade letters are whole tetrominoes of the piece they shade. Standard letters are rule 7's."""
    bad = []
    h = len(rows)
    groups: dict[str, list[tuple[int, int]]] = {}
    for i, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in SHADE:
                groups.setdefault(ch, []).append((x, h - 1 - i))
    for ch, cs in groups.items():
        letter = SHADE[ch]
        if len(cs) != 4 or (RT._norm(cs) not in RT._shapes(letter)
                            and RT._norm([(x, y) for x, y in cs]) not in RT._shapes(letter)):
            # the kept-rows frame: drop rows the group does not touch, as rule 7 does
            ys = sorted({y for _, y in cs})
            gap = [y for y in range(ys[0], ys[-1] + 1) if y not in set(ys)]
            kept = [(x, y - sum(1 for g in gap if g < y)) for x, y in cs]
            if len(cs) != 4 or (RT._norm(cs) not in RT._shapes(letter)
                                and RT._norm(kept) not in RT._shapes(letter)):
                bad.append(ch)
    return bad


def _gassho_checks(data: dict, ctx: dict) -> tuple[list[str], set[str]]:
    bad: list[str] = []
    found: set[str] = set()
    boards, by_id = ctx['boards'], ctx['by_id']
    nodes = data.get('nodes', [])
    quotes = {q['id']: q for q in data.get('quotes', [])}

    qtext = [q['verbatim'] for q in quotes.values()]
    for where, v in _verbatims({'bag1': data.get('bag1'), 'nodes': nodes}):
        if not any(v in q or v == q for q in qtext):
            bad.append(f'verbatim: {where} is not one of the quoted sentences')

    b1 = data.get('bag1', {})
    nh = b1.get('no_hold', {})
    left = boards.get(nh.get('node'))
    for c in nh.get('all', []):
        a, b = (p.lower() for p in c.get('before', ['?', '?']))
        if left is None or not any((r + 1, x) in _cells_of(left, a) for r, x in _cells_of(left, b)):
            bad.append(f'bag1-order: on {nh.get("node")} no {b.upper()} cell rests on a {a.upper()} cell, so '
                       f'{a.upper()} before {b.upper()} is not what the board needs')
    if b1.get('no_hold_items_verbatim') != ['%O・%S>%L', '%T>%J']:
        bad.append('bag1-order: the no-hold bullets are not the page\'s two items')

    # the right board being the mirror is the measured fact the discrepancy names
    right, left_rows = boards.get('bag1.right'), boards.get('bag1.left')
    if right and left_rows and bottom(right, RT.ROWS) == mirror(bottom(left_rows, RT.ROWS)):
        found.add('bag1.right:mirror')
    # I-early is the same occupancy, not a second shape
    early = boards.get('bag1.i_early')
    if early and left_rows and occ(bottom(early, 0)) == occ(bottom(left_rows, 0)):
        found.add('bag1.i_early:same_occupancy')
    else:
        bad.append('same-shape: bag1.i_early is no longer the occupancy of bag1.left')
    if by_id.get('bag1.i_early', {}).get('node_kind') != 'same_shape':
        bad.append('same-shape: bag1.i_early must stay out of the matcher (node_kind same_shape)')

    # the U overlay is the 基本形's occupancy with the hole drawn, and must not be matched as its own shape
    tsd = boards.get('2.tsd')
    if tsd and left_rows:
        hole = occ([r.replace('U', EMPTY) for r in bottom(tsd, 0)])
        if hole != occ(bottom(left_rows, 0)):
            bad.append('tsd-overlay: 2.tsd with U read as empty is not bag1.left')
    if by_id.get('2.tsd', {}).get('node_kind') != 'illustration':
        bad.append('tsd-overlay: 2.tsd must stay an illustration (the catalogue node is bag1.left)')

    # every U board is a flat TSD clearing two rows, and every muted C row is one of those rows
    for n in nodes:
        rows = n.get('rows')
        if not rows or 'U' not in ''.join(rows):
            if n.get('spin'):
                bad.append(f'spin: {n["id"]} names a spin and draws no U')
            continue
        if n.get('spin') != 'TSD' or t_slot(rows) != 'flat' or after_spin(rows)[1] != 2:
            bad.append(f'spin: {n["id"]} is not a flat TSD clearing 2 rows')
        filled = [r.replace('U', 't') for r in rows]
        full = {i for i, r in enumerate(filled) if EMPTY not in r}
        muted = [i for i, r in enumerate(rows) if 'C' in r]
        if any(i not in full for i in muted):
            bad.append(f'muted: {n["id"]} draws C on rows {muted}, the TSD clears rows {sorted(full)}')

    # both donation drawings clear to the one after board
    after_b = boards.get('2.donate.after')
    for src in ('2.donate.a', '2.donate.b'):
        if src not in boards or after_b is None:
            bad.append(f'after-of: {src} or 2.donate.after is missing')
            continue
        left_, cl = after_spin(boards[src])
        h = max(len(left_), len(after_b))
        if cl != 2 or occ(bottom(left_, h)) != occ(bottom(after_b, h)):
            bad.append(f'after-of: 2.donate.after is not what {src} leaves')

    # the printed percentages are the fractions named beside them, and SLO states none
    pc4, zjo = quotes.get('2.pc4', {}), quotes.get('2.zjo', {})
    if pc4.get('figure') != '5.71%' or abs(288 / 5040 * 100 - 5.71) > 0.005:
        bad.append('rate: the 4-line PC figure is not 5.71% = 288/5040')
    if zjo.get('figure') != '95.24%' or abs(20 / 21 * 100 - 95.24) > 0.005:
        bad.append('rate: the ZJO figure is not 95.24% = 20/21')
    # piece markers are `%Z`, not a rate. A stated rate would be digits in the figure or the sentence.
    slo = quotes.get('2.slo', {})
    if slo.get('figure') is not None or any(ch.isdigit() for ch in slo.get('verbatim', '')):
        bad.append('rate: the SLO sentence states a percentage (the page does not)')
    # the ZJO section's next sentence names SLO. That is the typo, measured off the quote and the board.
    typo = quotes.get('2.zjo.typo', {}).get('verbatim', '')
    zjo_rows = boards.get('2.zjo', [])
    zjo_pieces = {ch for r in zjo_rows for ch in r if ch in 'ijlostz'}
    if '%S%L%Oを先置き' in typo and zjo_pieces == set('ojz'):
        found.add('2.zjo.pc:slo_typo')
    else:
        bad.append('typo: the ZJO section no longer says SLO over an OJZ setup')

    if 'にはち砲' in by_id.get('refs.commented', {}).get('page_text', ''):
        found.add('refs.commented:hachispin')

    for n in nodes:
        rows = n.get('rows')
        if rows and _shade_bad(rows):
            bad.append(f'shade: {n["id"]} second-shade letters are not whole pieces ({_shade_bad(rows)})')

    # a list checked at 6 is the failure the page's own 「6ライン」 invites: the body is 4, or 2
    for lst in data.get('lists', []):
        if lst.get('pc_lines') == 6:
            bad.append(f'pc: {lst["id"]} is checked at 6 lines; the drawn body is not 6 (the TSD\'s 2 are not in the drawing)')
    return bad, found


SPEC = RT.TranscriptionSpec(
    out=OUT, build=build, alphabet=ALPHABET, non_board=NON_BOARD,
    harddrop=None,
    catalogue={'name': CATALOGUE_NAME, 'nodes': ['bag1.left']},
    board_kinds=frozenset({'illustration', 'same_shape'}),
    pc_lines=4, prior_letters='C',
    upper_groups={},
    occupancy_class_parents=2, extra_checks=_gassho_checks)


def verify(data: dict) -> list[str]:
    return RT.verify(data, SPEC)


def selftest() -> int:
    def break_mirror(d):
        setcell(node(d, 'bag1.right')['rows'], 1, 0, '-')

    def i_early_off(d):
        setcell(node(d, 'bag1.i_early')['rows'], 1, 0, '-')

    def overlay_matched(d):
        node(d, '2.tsd').pop('node_kind')

    def pc_at_6(d):
        next(x for x in d['lists'] if x['id'] == '2.zjo.pc')['pc_lines'] = 6

    def drop_typo(d):
        next(q for q in d['quotes'] if q['id'] == '2.zjo.typo')['verbatim'] = 'ZJOを先置きした場合。'

    def drop_discrepancy(d):
        d['known_discrepancies'] = [x for x in d['known_discrepancies'] if x['id'] != '2.zjo.pc:slo_typo']

    def basic_off(d):
        setcell(d['basic_form'][0]['rows'], 1, 0, 'o')

    def tall(d):
        node(d, '2.flat').pop('unmatchable')

    def no_reason(d):
        node(d, '2.ren.after')['unmatchable'] = ''

    def lost_text(d):
        d['nodes'] = [n for n in d['nodes'] if n['id'] != 'refs.commented']

    def order_flip(d):
        d['bag1']['no_hold']['all'][2]['before'] = ['J', 'T']

    def bad_cell(d):
        setcell(node(d, 'bag1.left')['rows'], 1, 0, 'p')

    def shade_broken(d):
        # an h that is no longer an I
        setcell(node(d, '2.zjo.pc#1')['rows'], 1, 6, 's')

    def rate_off(d):
        next(q for q in d['quotes'] if q['id'] == '2.pc4')['figure'] = '6%'

    def u_as_catalogue(spec):
        s = copy.copy(spec)
        s.catalogue = {'name': spec.catalogue['name'], 'nodes': ['2.tsd']}
        return s

    mutants = [
        (break_mirror, 'the right board no longer the left mirrored', 'mirror-of:'),
        (i_early_off, 'I-early no longer the same occupancy', 'discrepancy:'),
        (overlay_matched, 'the U overlay treated as its own shape', 'tsd-overlay:'),
        (pc_at_6, 'a 4-row PC list checked at 6 lines', 'pc:'),
        (drop_typo, 'the ZJO section no longer saying SLO', 'typo:'),
        (drop_discrepancy, 'the SLO-typo discrepancy dropped', 'discrepancy:'),
        (basic_off, 'the 1巡目 diagram off the 基本形', 'basic-form:'),
        (tall, 'the 9-row board not marked unmatchable', 'grammar:'),
        (no_reason, 'an unmatchable node with no reason', 'grammar:'),
        (lost_text, 'the commented references node deleted', 'non-board:'),
        (order_flip, 'T before J reversed', 'bag1-order:'),
        (bad_cell, 'a cell outside the alphabet', 'grammar:'),
        (shade_broken, 'a second-shade I that is not an I', 'shade:'),
        (rate_off, 'the 4-line figure no longer 5.71%', 'rate:'),
    ]
    return RT.run_selftest(
        SPEC, mutants,
        {'board': ('ijj------l', 'ijj-----xl'), 'text': ('にはち砲 - テトリス開幕テンプレWiki', '（gone）'),
         'hand_edit': 'bag1.left', 'quote': 'overview.intro'},
        spec_mutants=[(u_as_catalogue, 'the U overlay used as the catalogue node', 'catalogue:')])


def main(argv=None):
    return RT.main(SPEC, selftest, __doc__)


if __name__ == '__main__':
    raise SystemExit(main())

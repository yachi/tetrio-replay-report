"""Transcribe shiwehi.com's stick spin (SDパフェ) route page into `stickspin-routes.json`.

    python3 -m pipeline.openers.extract_stickspin_routes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_stickspin_routes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_stickspin_routes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_stickspin_routes --html-dir <dir> --write  # ...and rewrite

The fourth opener ROUTE page, after 迷走砲, はちみつ砲 and 山岳積み2号, and the first whose bag 1
ENDS IN A T-SPIN: six pieces (`bag1.left`, or its mirror), then the T as the seventh lock into a
T-spin Single, stood up (火力派生, `bag1.fire`) or laid flat (パフェ派生, `bag1.pc`). Under 火力派生:
two bag-2 TSD forms (`2.fire`) and four bag-3 TD-attack TST forms (`2.fire.td`). Under パフェ派生:
the SDパフェ (SingleYou) bag-2 TSD (`2.sd`), its bag-3 Perfect Clear list and three fallbacks
(TST派生, インペリアルクロス派生, STMB Cave派生), and the もっちパフェ (Mochi PC) bag-2 TSD (`2.mochi`,
plus its I-on-the-right variant) with its own PC list. Every rule the openers share is
`route_transcription.py`'s, once; this file holds the transcription, its `SPEC` and the rules only
this page needs (`_stickspin_checks`).

WHERE THE TRANSCRIPTION COMES FROM. `NODES` below is a literal, hand-checked transcription of the
page's RAW HTML, fetched the way 山岳積み2号's was: curl through the session proxy, TLS verification
on, with a CA bundle adding the Let's Encrypt YE2 intermediate shiwehi.com omits. The hash is of
the page's own bytes, comparable with 山岳積み2号's kind of hash and NOT with the markdown renderings
迷走砲 and はちみつ砲 hashed. The page is not committed; CI cannot fetch it. Boards are plain text in
`<div class="ttt">` (some `ttt small`), one row per line, drawn by the site's `column-exp.js` (the
same file 山岳積み2号 records, re-read for this page).

THE CROSS-SOURCE IS NOT HARDDROP, and that is a fact about this repo rather than about the opener.
harddrop has a Stickspin page (the shiwehi page cites it), but `wiki-openers.json` transcribes seven
openers and this is not one of them, so there is no harddrop field to compare with (and no 六個具名定式
column). Rule 2 instead uses the shared gate's `catalogue` route: Ivan's opener database
(`opener-fields.json`) files 「Single Double PC … / Stickspin …」 as one entry with four fields, and
those four are exactly `bag1.fire` and `bag1.pc` with the T placed in their U cells, as drawn and
mirrored, by occupancy (the catalogue carries no colour). Adding a harddrop field would change every
session's `opener-facts.json`, which this page has no business doing.

WHAT IS AN INFERENCE, flagged in the JSON rather than in prose only:

  * upper-case letters are the rows a spin clears, drawn in the renderer's muted colour (`C` light
    grey); the page has no legend. Rule 3 checks the reading on every board that carries them (each
    upper-case row is exactly a row the U slot clears, and nothing else is upper case).
  * the after-the-TSS boards keep the T's surviving cells as `U`, not `t`: read as the T, checked
    against the board before the spin letter for letter (`_stickspin_checks`).
  * the bag-1 condition (%O>%Z, %J>%L) is the page's condition for building the left pattern
    WITHOUT HOLD; read as orders, and checked against the board by support (the later piece rests on
    the earlier one). Calling the TD-attack boards bag 3 and the bag-2 boards' bases the
    after-the-TSS boards is the page's own heading structure (1巡目 / 2巡目 / 3巡目→4巡目).

THE TERMS are the same shiwehi.com terms page 迷走砲 links to, imported from that transcription
rather than copied (read 2026-10-11 there; not re-read for this page).
"""
from __future__ import annotations

import copy
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS
from pipeline.openers.route_transcription import (EMPTY, after_spin, bottom, mirror, node, setcell,
                                                  t_slot)

HERE = Path(__file__).resolve().parent
OUT = HERE / 'stickspin-routes.json'

ALPHABET = frozenset('-ijlostzcUCIJLOSZ')
#: the renderer's muted (cleared-row) colours, read back as their piece
UPPER = {'I': 'i', 'J': 'j', 'L': 'l', 'O': 'o', 'S': 's', 'Z': 'z', 'C': 'c'}


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/stickspin.php',
    'title': 'stick spin(SDパフェ)',
    'updated': '2022-08-06',
    'created': '2022-08-06',
    'fetched': '2026-10-13',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle '
                    'that adds the Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), '
                    'the method 山岳積み2号 used. The snapshot is the page\'s raw HTML, byte for byte; every '
                    'board is plain text in it, 60 ten-wide boards in page order. Comparable with '
                    '山岳積み2号\'s hash (both raw HTML), not with the markdown renderings 迷走砲 and はちみつ砲 '
                    'hashed.',
    'snapshot_file': 'stickspin.html',
    'snapshot_sha256': '0d10263ee4794900d0cb94f99a3c39dcea3d9fdfe52be709f1a8b5038dc45366',
    'snapshot_bytes': 35167,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable '
                     'in CI: the page is not committed and cannot be fetched there. Re-check with '
                     '--html-dir after any refetch; an HTML hash moves with ANY byte of the page (ads, '
                     'sidebar, a date), so a moved hash means "read the board diff", not "the boards '
                     'changed". Sentences are compared against the page with its tags dropped.',
    'renderer': {
        'url': 'https://shiwehi.com/tetris/mutual/column-exp.js?date=20210408',
        'read': '2026-10-13',
        'sha256': '95c431a4147f9c30fc0e1bae935e6af6f5669c3d2fa1edfc388848e69ab62570',
        'sha256_note': 'the same bytes 山岳積み2号 recorded on 2026-10-12, re-fetched for this page',
        'colorMap_used': {'c': '#a3a3a3', 'C': '#cccccc', 'U': '#c8a6ff with a #8400ff radial dot',
                          'I J L O S Z': 'muted i j l o s z (#4db1d8 #4d57d8 #d8904d #cfcf4d #69d24d '
                                         '#d84d4d)', '-': '#000000'},
        'rows': 'textContent split on whitespace, one row per token; .ttt and .tetTableText are both '
                'drawn, `small` only changes the cell size',
        'mirror_button': 'body.reversed swaps j<->l, s<->z (and upper case) and reverses nothing else in '
                         'the char map; the canvas is redrawn mirrored',
    },
    'decorative_images': ['stick spin(SDパフェ)タイトル画像'],
    'references_listed': ['https://w.atwiki.jp/tetrismaps/pages/423.html',
                          'https://harddrop.com/wiki/Stickspin',
                          'https://four.lol/openers/sd-pc'],
    'related_pages': ['./imperialcross.php', './stmbcave.php'],
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ, align at the BOTTOM row',
    '-': 'empty',
    'i o t s z j l': 'a cell of that piece',
    'c': 'a cell filled before this diagram (earlier bags), grey',
    'U': 'the T-spin slot; on an after-the-TSS board, the T\'s surviving cells (OUR READING, checked letter for letter against the board before the spin)',
    'I J L O S Z C': 'a cell of that piece (C: an earlier cell) in a row the spin clears, drawn in the renderer\'s muted colour (page legend: none; OUR READING, checked: every upper-case row is a row the U slot clears)',
    '%X': "the X piece; '%O>%Z' means O before Z",
}


#: Every sentence the transcription leans on, verbatim. `--html-dir` finds each on the page (tags
#: dropped), and every `*_verbatim` field below must be one of these (`_stickspin_checks`).
QUOTES = [
    {'id': 'overview.intro', 'figure': None,
     'verbatim': 'ここでは、stick spin(SDパフェ)という、多くの場合、初順からTSS→TSD→TST→TSDを打つことができる、もしくはTSS→TSD(→TSD)→8ラインパフェを狙うことができる開幕テンプレについて紹介していきます。'},
    {'id': 'basic.o_early', 'figure': None, 'verbatim': '開幕で%Oが早いときに打つことができるテンプレの1つです。'},
    {'id': 'basic.tss', 'figure': None, 'verbatim': 'また、初巡でTSSを打てるため、相手の開幕パフェを阻止することができます。'},
    {'id': 'basic.b2b', 'figure': None, 'verbatim': 'また、その後back-to-backを維持したままTSDを打つことができます。'},
    {'id': 'basic.side', 'figure': None, 'verbatim': '%Jと%Lのどちらが早いかで左右を使い分けると良いでしょう。'},
    {'id': 'bag1.requires', 'figure': None,
     'verbatim': '1巡目の組み方は上図の通りで、%Oが早い時にソフトドロップ無しで組むことができます。'},
    {'id': 'bag1.no_hold', 'figure': None, 'verbatim': '左のパターンがホールド無しで組める条件は以下の通りです。'},
    {'id': 'bag1.no_hold.o_z', 'figure': None, 'verbatim': '%O>%Z'},
    {'id': 'bag1.no_hold.j_l', 'figure': None, 'verbatim': '%J>%L'},
    {'id': 'bag1.side', 'figure': None,
     'verbatim': '%J%Lのどちらが早いかによって左右を決めると良いでしょう。(ここでは、以下左のパターンで説明していきますが、右下にある反転ボタンを押すことで左右反転の図を見ることができます。)'},
    {'id': 'bag1.fire', 'figure': None, 'verbatim': '火力派生の場合、1巡目は%Tを立てるようにTスピンを打ちます。'},
    {'id': '2.fire', 'figure': None,
     'verbatim': '火力派生の場合、2巡目は下図のどちらかの形を組むことでTSDを打つことができます。'},
    {'id': '2.fire.soft_s', 'figure': None, 'verbatim': '(%Sはソフトドロップで後入れできます。)'},
    {'id': '2.fire.td', 'figure': None,
     'verbatim': '3巡目は以下いずれかのTDアタックの形に組むことで、3巡目TST→4巡目TSDを打つことができます。'},
    {'id': '2.fire.td.sz', 'figure': None, 'verbatim': '%Sと%Zの位置だけ正しく置ければあとは何とかなるかなと思います。'},
    {'id': 'bag1.pc', 'figure': None, 'verbatim': 'パフェ派生の場合、1巡目は%Tを寝かせるようにTスピンを打ちます。'},
    {'id': '2.sd.intro', 'figure': '97.18% / 約52%',
     'verbatim': 'SDパフェ派生は、2巡目にTSDを打ってから3巡目に97.18%でパフェを取ることができ、そのうち約52%でパフェを取る前にTSD又はTSSを打つことができます。'},
    {'id': '2.sd', 'figure': None, 'verbatim': 'SDパフェ派生の場合、2巡目は下図の形で必ずTSDを打つことができます。'},
    {'id': '2.sd.pc', 'figure': '97.18%', 'verbatim': '3巡目は97.18%でパフェを取ることができます。',
     'note': 'the page prints this sentence twice, word for word: under SDパフェ and under もっちパフェ'},
    {'id': '2.sd.pc.rest', 'figure': '14通り', 'verbatim': 'その他の取り方(14通り)'},
    {'id': '2.sd.fallback', 'figure': None, 'verbatim': 'パフェが取れない場合は様々な形に移行できます。'},
    {'id': '2.mochi.intro', 'figure': '100%',
     'verbatim': 'もっちパフェ派生は2巡目にTSDを打ってから、3巡目に100%でパフェを取ることができる派生です。'},
    {'id': '2.mochi', 'figure': None, 'verbatim': 'もっちパフェ派生の場合、2巡目は下図の形でTSDを打ちます。'},
    {'id': '2.mochi.i_right', 'figure': '99.96%',
     'verbatim': '%Iが早い場合には99.96%にパフェ率は下がりますが%Iを右側に立てても良いです。'},
    {'id': '2.mochi.pc', 'figure': '97.18%', 'verbatim': '3巡目は97.18%でパフェを取ることができます。',
     'note': 'word for word the 2.sd.pc sentence, under the もっちパフェ heading, whose own introduction says 100%'},
    {'id': '2.mochi.pc.rest', 'figure': '9通り', 'verbatim': 'その他の取り方(9通り)'},
]


BAG1 = {
    'requires_verbatim': '1巡目の組み方は上図の通りで、%Oが早い時にソフトドロップ無しで組むことができます。',
    'requires': {'early': ['O'], 'illustrative': True},
    'requires_note': 'the condition for building WITHOUT SOFT DROP, not a trigger; the 基本形 sentence says the same (開幕で%Oが早いとき)',
    'no_hold_verbatim': '左のパターンがホールド無しで組める条件は以下の通りです。',
    'no_hold': {'all': [{'before': ['O', 'Z']}, {'before': ['J', 'L']}], 'node': 'bag1.left'},
    'no_hold_items_verbatim': ['%O>%Z', '%J>%L'],
    'no_hold_note': 'the left pattern\'s condition for building WITHOUT HOLD; each order is checked against bag1.left by support (a cell of the later piece rests on a cell of the earlier one). The right pattern\'s (its mirror: O>S, L>J) is not stated',
    'side_verbatim': '%J%Lのどちらが早いかによって左右を決めると良いでしょう。(ここでは、以下左のパターンで説明していきますが、右下にある反転ボタンを押すことで左右反転の図を見ることができます。)',
    'side': {'decided_by': ['J', 'L'], 'which': None},
    'side_note': 'the page does not say which side goes with which piece in this sentence; the no-hold list gives J before L for the left one',
    'tss_lock': 7,
    'tss_note': 'six pieces and then the T: every bag-1 board below is six pieces, and the T is the bag\'s seventh lock, into a T-spin Single, stood up (火力派生) or laid flat (パフェ派生)',
}


BASIC_FORM = [
    {
        'id': 'basic.1',
        'same_as': 'bag1.fire',
        'rows': _b('---------- ---------- ---------- ---------- -z-------- zzU------i zUU----lli ooUssjjjli ooss---jli'),
        'canvas': 'tetCanvas0',
    },
    {
        'id': 'basic.2',
        'same_as': '2.fire.tsd',
        'differs': 'the two rows the TSD clears are drawn in the pieces\' own colours, not the muted ones',
        'recolour': {'I': 'i', 'C': 'c', 'J': 'j', 'Z': 'z', 'S': 's', 'L': 'l'},
        'rows': _b('---------- ---------- i--------- ioo------- ioo------z icUUUjjjzz cccUslljzc ccc-sslccc cccc-slccc'),
        'canvas': 'tetCanvas1',
    },
    {
        'id': 'basic.3',
        'same_as': '2.fire.td#1',
        'rows': _b('i--------- i--------- i--------- i-ss--jj-- css---jloo cccUzzjloo cccUUzzllc cccUcccccc cccc-ccccc'),
        'canvas': 'tetCanvas2',
    },
]


KNOWN_DISCREPANCIES = [
    {
        'id': 'bag1.right:mirror',
        'what': 'the right bag-1 board is the left one mirrored with J<->L, S<->Z (cell for cell), so the page has ONE bag-1 shape, not two',
    },
    {
        'id': '2.fire:no_conditions',
        'what': 'two 火力派生 bag-2 forms (J or L laid flat beside the TSD slot) and no condition saying which: the page says どちらかの形',
    },
    {
        'id': '2.fire.tsd:form1_colours',
        'what': 'the TSD board is drawn after BOTH bag-2 forms (→ after the second) but in the colours of the first (JJJ / SLLJ); its occupancy fits both',
    },
    {
        'id': '2.fire.td:no_conditions',
        'what': 'four TD-attack bag-3 forms and no condition saying which; the page says only the S and Z must be placed right (checked: all four put S and Z on the same cells)',
    },
    {
        'id': '2.fire.bag4:not_drawn',
        'what': 'the 3巡目→4巡目 sentence names a bag-4 TSD; the page draws no bag-4 board',
    },
    {
        'id': '2.mochi.pc:rate_conflict',
        'what': 'the もっちパフェ introduction says 3巡目に100%でパフェ; its 3巡目 sentence says 97.18%, word for word the SDパフェ 3巡目 sentence',
    },
    {
        'id': '2.mochi.pc#13:colour',
        'what': 'the 13th もっちパフェ pattern draws five j cells and three l: the cell in column 10 of its fourth row (ccccjtoocj) is the L\'s fourth cell in the kept-rows frame (the third row, ccccjjoozz, clears under it), drawn in the J\'s colour',
    },
    {
        'id': '2.mochi.i_right:no_pc_drawn',
        'what': 'the I-on-the-right もっちパフェ variant states a PC rate (99.96%) and no PC pattern is drawn for it: the drawn もっちパフェ patterns sit on the I-on-the-left board',
    },
]


#: Every node, in page order (the PC patterns are inserted after their `after` boards by `build`).
NODES: list[dict] = [
    {
        'id': 'bag1.left',
        'bag': 1,
        'parent': None,
        'locks': 6,
        'label_jp': '1巡目とミノ順',
        'label_jp_note': 'the section heading; the page draws this board with no caption of its own (its sentence calls it 左のパターン)',
        'label': "bag 1 less the T (the page's left pattern)",
        'rows': _b('---------- -z-------- zz-------i z------lli oo-ssjjjli ooss---jli'),
    },
    {
        'id': 'bag1.right',
        'bag': 1,
        'parent': None,
        'locks': 6,
        'label_jp': '1巡目とミノ順',
        'label_jp_note': 'the section heading; the page draws this board with no caption of its own',
        'label': "bag 1 less the T, mirrored (the page's right pattern)",
        'mirror_of': 'bag1.left',
        'classifier_note': 'exactly bag1.left mirrored with J<->L and S<->Z swapped (checked cell for cell); a mirror-aware classifier must treat it as the SAME node, not a second branch',
        'rows': _b('---------- --------s- i-------ss ijj------s ijlllzz-oo ijl---zzoo'),
    },
    {
        'id': 'bag1.fire',
        'bag': 1,
        'parent': 'bag1.left',
        'spin_of': 'bag1.left',
        'locks': 7,
        'spin': 'TSS',
        't_orientation': 'stood',
        'label_jp': '火力派生(stick Spin) 1巡目',
        'label': 'bag 1 with the T stood up into a T-spin Single (the attack line)',
        'rows': _b('---------- -z-------- zzU------i zUU----lli ooUssjjjli ooss---jli'),
    },
    {
        'id': 'bag1.fire.after',
        'bag': 1,
        'parent': 'bag1.fire',
        'label': 'attack line, after the TSS',
        'node_kind': 'illustration',
        'after_of': 'bag1.fire',
        'rows': _b('---------- ---------- -z-------- zzU------i zUU----lli ooss---jli'),
    },
    {
        'id': '2.fire#1',
        'bag': 2,
        'parent': None,
        'base': 'bag1.fire.after',
        'spin': 'TSD',
        'label_jp': '火力派生(stick Spin) 2巡目 1',
        'label': 'attack bag 2, form 1 (J laid flat beside the TSD slot, in its top row)',
        'group': '2.fire',
        'variant': 1,
        'condition': None,
        'spin_board': '2.fire.tsd',
        'rows': _b('---------- i--------- ioo------- ioo------z ic---jjjzz ccc-slljzc ccc-sslccc cccc-slccc'),
    },
    {
        'id': '2.fire#2',
        'bag': 2,
        'parent': None,
        'base': 'bag1.fire.after',
        'spin': 'TSD',
        'label_jp': '火力派生(stick Spin) 2巡目 2',
        'label': 'attack bag 2, form 2 (L laid flat beside the TSD slot, in its top row)',
        'group': '2.fire',
        'variant': 2,
        'condition': None,
        'spin_board': '2.fire.tsd',
        'rows': _b('---------- i--------- ioo------- ioo------z ic---lllzz ccc-sljjzc ccc-ssjccc cccc-sjccc'),
    },
    {
        'id': '2.fire.tsd',
        'bag': 2,
        'parent': '2.fire',
        'label_jp': '火力派生(stick Spin) 2巡目 →',
        'label': 'attack bag 2 with the TSD slot and the cleared rows highlighted (drawn in form 1\'s colours)',
        'node_kind': 'illustration',
        'rows': _b('---------- i--------- ioo------- ioo------z ICUUUJJJZZ CCCUSLLJZC ccc-sslccc cccc-slccc'),
    },
    {
        'id': '2.fire.td#1',
        'bag': 3,
        'parent': '2.fire',
        'base': '2.fire#1',
        'base_note': 'the base is the board BEFORE the TSD (2.fire#1), because the page draws no after-the-TSD board for this branch; '
                     '2.sd.pc and 2.mochi.pc are based on a drawn after-the-TSD board instead. Both bag-2 forms share one '
                     'occupancy, so they leave the same board after the TSD (checked)',
        'spin': 'TST',
        'label_jp': '火力派生(stick Spin) 3巡目→4巡目 1',
        'label': 'attack bag 3, TD attack form 1 (I stood at the left wall)',
        'group': '2.fire.td',
        'variant': 1,
        'condition': None,
        'unmatchable': '9 non-empty rows > ROWS = 8',
        'rows': _b('i--------- i--------- i--------- i-ss--jj-- css---jloo cccUzzjloo cccUUzzllc cccUcccccc cccc-ccccc'),
    },
    {
        'id': '2.fire.td#2',
        'bag': 3,
        'parent': '2.fire',
        'base': '2.fire#1',
        'spin': 'TST',
        'label_jp': '火力派生(stick Spin) 3巡目→4巡目 2',
        'label': 'attack bag 3, TD attack form 2 (O at the left, I at the right wall)',
        'group': '2.fire.td',
        'variant': 2,
        'condition': None,
        'rows': _b('---------- ---------- oo-------i ooss--l--i css---l-ji cccUzzllji cccUUzzjjc cccUcccccc cccc-ccccc'),
    },
    {
        'id': '2.fire.td#3',
        'bag': 3,
        'parent': '2.fire',
        'base': '2.fire#1',
        'spin': 'TST',
        'label_jp': '火力派生(stick Spin) 3巡目→4巡目 3',
        'label': 'attack bag 3, TD attack form 3 (J and L over O, I at the right wall)',
        'group': '2.fire.td',
        'variant': 3,
        'condition': None,
        'rows': _b('---------- ---------- ------j--i --ss--jjji css---llli cccUzzlooi cccUUzzooc cccUcccccc cccc-ccccc'),
    },
    {
        'id': '2.fire.td#4',
        'bag': 3,
        'parent': '2.fire',
        'base': '2.fire#1',
        'spin': 'TST',
        'label_jp': '火力派生(stick Spin) 3巡目→4巡目 4',
        'label': 'attack bag 3, TD attack form 4 (L over O and J, I at the right wall)',
        'group': '2.fire.td',
        'variant': 4,
        'condition': None,
        'rows': _b('---------- ---------- --------li --ss--llli css---ooji cccUzzooji cccUUzzjjc cccUcccccc cccc-ccccc'),
    },
    {
        'id': '2.fire.bag4',
        'bag': 4,
        'parent': '2.fire.td',
        'node_kind': 'text_only',
        'label_jp': '3巡目→4巡目',
        'page_text': '3巡目TST→4巡目TSDを打つことができます。',
        'note': 'the page names a bag-4 TSD after the TST and draws no bag-4 board',
    },
    {
        'id': 'bag1.pc',
        'bag': 1,
        'parent': 'bag1.left',
        'spin_of': 'bag1.left',
        'locks': 7,
        'spin': 'TSS',
        't_orientation': 'flat',
        'label_jp': 'パフェ派生(SDパフェ・もっちパフェ) 1巡目',
        'label_jp_note': 'the section heading; the page gives this board no 1巡目 heading of its own, only the sentence 1巡目は%Tを寝かせるように',
        'label': 'bag 1 with the T laid flat into a T-spin Single (the Perfect Clear line)',
        'rows': _b('---------- -z-------- zz-------i zUUU---lli ooUssjjjli ooss---jli'),
    },
    {
        'id': 'bag1.pc.after',
        'bag': 1,
        'parent': 'bag1.pc',
        'label': 'Perfect Clear line, after the TSS',
        'node_kind': 'illustration',
        'after_of': 'bag1.pc',
        'rows': _b('---------- ---------- -z-------- zz-------i zUUU---lli ooss---jli'),
    },
    {
        'id': '2.sd',
        'bag': 2,
        'parent': None,
        'base': 'bag1.pc.after',
        'spin': 'TSD',
        'label_jp': 'SDパフェ派生(SingleYou) 2巡目',
        'label': 'SD-PC bag 2',
        'condition': None,
        'condition_note': 'the page states no order condition choosing SDパフェ over もっちパフェ',
        'rows': _b('---------- i--------- ioo------- iooz---jjj iczz----lj cczUUUlllc ccccUssccc ccccss-ccc'),
    },
    {
        'id': '2.sd.after',
        'bag': 2,
        'parent': '2.sd',
        'label': 'SD-PC, after the TSD',
        'node_kind': 'illustration',
        'after_of': '2.sd',
        'rows': _b('---------- ---------- ---------- i--------- ioo------- iooz---jjj iczz----lj ccccss-ccc'),
    },
    {
        'id': '2.sd.tst',
        'bag': 3,
        'parent': '2.sd',
        'base': '2.sd.after',
        'spin': 'TST',
        'spin_board': '2.sd.tst.spin',
        'label_jp': 'パフェが取れない場合 TST派生',
        'label': 'SD-PC fallback: TST',
        'text_verbatim': 'パフェが取れない場合は様々な形に移行できます。',
        'rows': _b('---------- c----ss--- ccc-ss---- ccccoo-ccc ccccoo--cc cccccc-ccc'),
    },
    {
        'id': '2.sd.tst.spin',
        'bag': 3,
        'parent': '2.sd.tst',
        'label_jp': 'パフェが取れない場合 TST派生 →',
        'label': 'SD-PC fallback TST, with the slot and the cleared rows highlighted',
        'node_kind': 'illustration',
        'rows': _b('---------- c----ss--- ccc-ss---- CCCCOOUCCC CCCCOOUUCC CCCCCCUCCC'),
    },
    {
        'id': '2.sd.imperial',
        'bag': 3,
        'parent': '2.sd',
        'base': '2.sd.after',
        'spin': 'TSD',
        'spin_board': '2.sd.imperial.spin',
        'label_jp': 'パフェが取れない場合 インペリアルクロス派生',
        'label': 'SD-PC fallback: Imperial Cross (a TSD whose two cleared rows are not adjacent)',
        'rows': _b('---------- c---lll--- ccc-lz---- cccczz-ccc ccccz---cc cccccc-ccc'),
    },
    {
        'id': '2.sd.imperial.spin',
        'bag': 3,
        'parent': '2.sd.imperial',
        'label_jp': 'パフェが取れない場合 インペリアルクロス派生 →',
        'label': 'SD-PC fallback Imperial Cross, with the slot and the two cleared rows highlighted',
        'node_kind': 'illustration',
        'rows': _b('---------- c---lll--- ccc-lz---- CCCCZZUCCC cccczUU-cc CCCCCCUCCC'),
    },
    {
        'id': '2.sd.stmb',
        'bag': 3,
        'parent': '2.sd',
        'base': '2.sd.after',
        'spin': 'TSD',
        'spin_board': '2.sd.stmb.spin',
        'label_jp': 'パフェが取れない場合 STMB Cave派生',
        'label': 'SD-PC fallback: STMB Cave',
        'rows': _b('---l------ clll---zz- ccc---sszz cccc-ssccc cccc----cc cccccc-ccc'),
    },
    {
        'id': '2.sd.stmb.spin',
        'bag': 3,
        'parent': '2.sd.stmb',
        'label_jp': 'パフェが取れない場合 STMB Cave派生 →',
        'label': 'SD-PC fallback STMB Cave, with the slot and the cleared rows highlighted',
        'node_kind': 'illustration',
        'rows': _b('---l------ clll---zz- CCCUUUSSZZ CCCCUSSCCC cccc----cc cccccc-ccc'),
    },
    {
        'id': '2.mochi',
        'bag': 2,
        'parent': None,
        'base': 'bag1.pc.after',
        'spin': 'TSD',
        'label_jp': 'もっちパフェ派生(Mochi PC) 2巡目',
        'label': 'Mochi PC bag 2 (I laid flat at the top left)',
        'condition': None,
        'condition_note': 'the page states no order condition choosing もっちパフェ over SDパフェ',
        'rows': _b('---------- iiii------ jjss------ jssz------ jczz----l- cczUUUlllc ccccUooccc cccc-ooccc'),
    },
    {
        'id': '2.mochi.after',
        'bag': 2,
        'parent': '2.mochi',
        'label': 'Mochi PC, after the TSD',
        'node_kind': 'illustration',
        'after_of': '2.mochi',
        'rows': _b('---------- ---------- ---------- iiii------ jjss------ jssz------ jczz----l- cccc-ooccc'),
    },
    {
        'id': '2.mochi.i_right',
        'bag': 2,
        'parent': None,
        'base': 'bag1.pc.after',
        'spin': 'TSD',
        'label_jp': 'もっちパフェ派生(Mochi PC) 2巡目 (%Iが早い場合)',
        'label': 'Mochi PC bag 2 with the I stood at the right wall',
        'condition_verbatim': '%Iが早い場合には99.96%にパフェ率は下がりますが%Iを右側に立てても良いです。',
        'condition': {'early': 'I'},
        'rows': _b('---------- ---------i jjss-----i jssz-----i jczz----li cczUUUlllc ccccUooccc cccc-ooccc'),
    },
]


#: The page's PC lists, in page order. `shown` / `rest_stated` are the page's own split
#: (「その他の取り方(N通り)」, behind a <details>).
_SD_PC_ROWS = [
    'cjjjillloo cccjilssoo ccccissccc ccccitttcc cccccctccc',
    'ciiiijjzoo ccclljzzoo ccccljzccc ccccltttcc cccccctccc',
    'ciiiijssoo ccclljjjoo cccclssccc ccccltttcc cccccctccc',
    'ciiiitttoo cccjjjtzoo cccclllccc ccccljzzcc cccccczccc',
    'ciiiislloo ccczzssloo cccczzsccc ccccjjjlcc ccccccjccc',
    'ciiiistttl ccczzsslll cccczzsccc ccccjjjtcc ccccccjccc',
    'ciiiijjjoo ccczzssjoo cccczztccc ccccssttcc cccccctccc',
    'cjjjiiiioo cccjltttoo cccclzzccc ccccllzzcc cccccctccc',
    'cjjjstttoo cccjsstzoo cccclllccc cccclszzcc cccccczccc',
    'cjjjiiiioo cccjlllzoo cccctttccc ccccltzzcc cccccczccc',
    'ciiiitttoo ccczzjjjoo cccczzlccc ccccllljcc cccccctccc',
    'ciiiijjjoo ccclltttoo cccclstccc cccclssjcc ccccccsccc',
    'cjjjitttoo cccjillloo ccccizzccc ccccilzzcc cccccctccc',
    'ciiiitttoo ccclljssoo cccclssccc ccccljjjcc cccccctccc',
    'cjjjlllzoo cccjltzzoo cccctttccc cccciiiicc cccccczccc',
    'ciiiissloo ccczzllloo cccczztccc ccccssttcc cccccctccc',
    'ciiiilljoo ccctttljoo cccctssccc ccccssjjcc cccccclccc',
    'cjjjtttzoo cccjiiiioo cccclllccc ccccltzzcc cccccczccc',
    'cjjjlllzoo cccjstttoo ccccsstccc cccclszzcc cccccczccc',
]

_MOCHI_PC_ROWS = [
    'cccctttjjj ccccitllsj ccccioolss ccccioolcs cccciccccc',
    'ccccjjiiii ccccjtttll ccccjztssl cccczzsscl cccczccccc',
    'ccccjjtlli ccccjtttli ccccjzooli cccczzooci cccczccccc',
    'ccccjjzooi ccccjzzooi ccccjzttti ccccllltci cccclccccc',
    'cccctttssi ccccjtsszi ccccjjjzzi cccclllzci cccclccccc',
    'ccccooiiii ccccoozzll ccccjjtzzl ccccjtttcl ccccjccccc',
    'ccccjjjooi cccczzjooi cccctzzssi ccccttssci cccctccccc',
    'ccccooiiii ccccoossll ccccjjtttl ccccjsstcl ccccjccccc',
    'cccctttloo ccccillloo ccccizzjjj ccccitzzcj cccciccccc',
    'cccclllooi ccccjjjooi cccclzjssi cccczzssci cccczccccc',
    'ccccllljjj cccclzoosj cccczzooss cccciiiics cccczccccc',
    'ccccsllooi ccccsslooi ccccjjttti ccccjsltci ccccjccccc',
    'cccciiiill cccctttzzl ccccjjoozz ccccjtoocj ccccjccccc',
    'ccccjjiiii ccccjzztll ccccootttl ccccoozzcl ccccjccccc',
]

#: several boards that share ONE continuation (or none drawn). `drawn` is the page's own count.
GROUPS = [
    {'id': '2.fire', 'heading': '火力派生(stick Spin) 2巡目', 'drawn': 2,
     'text_verbatim': '火力派生の場合、2巡目は下図のどちらかの形を組むことでTSDを打つことができます。'},
    {'id': '2.fire.td', 'heading': '火力派生(stick Spin) 3巡目→4巡目', 'drawn': 4,
     'text_verbatim': '3巡目は以下いずれかのTDアタックの形に組むことで、3巡目TST→4巡目TSDを打つことができます。',
     'shared_verbatim': '%Sと%Zの位置だけ正しく置ければあとは何とかなるかなと思います。',
     'shared_pieces': ['S', 'Z'],
     'shared_note': 'checked: all four forms put the S and the Z on the same cells'},
]

_COUNT_NOTE = ('the page states no total: it shows 5 and counts the rest behind 「その他の取り方(N通り)」, which is '
               'checked against the drawn rest; read as complete because the page gives a PC rate over them')

LISTS = [
    {'id': '2.sd.pc', 'parent': '2.sd', 'base': '2.sd.after', 'bag': 3, 'heading': 'SDパフェ派生(SingleYou) 3巡目',
     'rows': _SD_PC_ROWS, 'stated_pattern_count': None, 'shown': 5, 'rest_stated': 14, 'complete': True,
     'count_note': _COUNT_NOTE,
     'pc_lines': 7, 'total_lines': 8, 'total_lines_quote': 'overview.intro',
     'pc_lines_note': 'the 5-row body plus the bag-2 TSD before it; the page\'s 8ライン counts the bag-1 TSS too '
                      '(TSS 1 + TSD 2 + 5), which `_stickspin_checks` re-derives along the base chain'},
    {'id': '2.mochi.pc', 'parent': '2.mochi', 'base': '2.mochi.after', 'bag': 3, 'heading': 'もっちパフェ派生(Mochi PC) 3巡目',
     'rows': _MOCHI_PC_ROWS, 'stated_pattern_count': None, 'shown': 5, 'rest_stated': 9, 'complete': True,
     'count_note': _COUNT_NOTE,
     'pc_lines': 7, 'total_lines': 8, 'total_lines_quote': 'overview.intro',
     'pc_lines_note': 'as 2.sd.pc: the 5-row body plus the TSD, 8 lines with the TSS'},
]

#: where each list's patterns are inserted in page order: after this node
_LIST_AFTER = {'2.sd.pc': '2.sd.after', '2.mochi.pc': '2.mochi.i_right'}

#: The page's content that has no board. Identified by reading the page; `--html-dir` checks each
#: node's `page_text` is still on it.
NON_BOARD = {
    '2.fire.bag4': 'text_only',
}


def _pattern_nodes(lst: dict) -> list[dict]:
    out = []
    for i, text in enumerate(lst['rows'], 1):
        rows = _b(text)
        pieces = ''.join(sorted({ch for r in rows for ch in r if ch in 'ijlostz'}))
        out.append({'id': f'{lst["id"]}#{i}', 'bag': lst['bag'], 'parent': lst['parent'],
                    'base': lst['base'], 'list': lst['id'], 'index': i,
                    'listed_under': 'shown' if i <= lst['shown'] else 'rest',
                    'label_jp': f'{lst["heading"]} {i}', 'pieces': pieces, 'rows': rows})
    return out


#: The order boards appear on the page. `--html-dir` compares a snapshot against exactly this.
PAGE_ORDER = (
    ['basic.1', 'basic.2', 'basic.3', 'bag1.left', 'bag1.right', 'bag1.fire', 'bag1.fire.after',
     '2.fire#1', '2.fire#2', '2.fire.tsd'] + [f'2.fire.td#{k}' for k in range(1, 5)]
    + ['bag1.pc', 'bag1.pc.after', '2.sd', '2.sd.after'] + [f'2.sd.pc#{i}' for i in range(1, 20)]
    + ['2.sd.tst', '2.sd.tst.spin', '2.sd.imperial', '2.sd.imperial.spin', '2.sd.stmb', '2.sd.stmb.spin',
       '2.mochi', '2.mochi.after', '2.mochi.i_right'] + [f'2.mochi.pc#{i}' for i in range(1, 15)]
)

#: the list-node flags, computed from the cells and re-checked by the gate
SLOT_FLAGS = {'has_u_slot': lambda rows: t_slot(rows) is not None,
              't_flat_shape': lambda rows: t_slot(rows, 't') == 'flat'}

#: what each flag means, published beside them. NOT the other pages' `t_in_tsd_slot`: on this page the
#: PC body is framed AFTER the TSD, so a PC pattern's t is never the TSD's T, and the flag is the flat
#: ttt-over-t SHAPE drawn anywhere (an independent audit found it true with the t on the surface)
SLOT_FLAG_MEANING = {
    'has_u_slot': 'the pattern draws a U (T-spin slot) cell',
    't_flat_shape': 'the pattern\'s t cells form the flat ttt-over-t shape ANYWHERE on the board; a shape test, not a '
                    'position test, and not a TSD (the PC body is framed after the TSD): nothing downstream reads it',
}


def build() -> dict:
    nodes = copy.deepcopy(NODES)
    for lst in LISTS:
        at = next(i for i, n in enumerate(nodes) if n['id'] == _LIST_AFTER[lst['id']]) + 1
        nodes[at:at] = _pattern_nodes(lst)
    for n in nodes:
        if 'list' in n:
            for k, fn in SLOT_FLAGS.items():
                n[k] = fn(n['rows'])
    lists = []
    for lst in LISTS:
        drawn = sum(1 for n in nodes if n.get('list') == lst['id'])
        lists.append({**{k: v for k, v in lst.items() if k != 'rows'}, 'drawn': drawn})
    return {
        'schema': 'stickspin-routes/1',
        'source': SOURCE,
        'terms': TERMS,
        'legend': LEGEND,
        'quotes': QUOTES,
        'bag1': BAG1,
        'basic_form': BASIC_FORM,
        'groups': GROUPS,
        'lists': lists,
        'slot_flags': SLOT_FLAG_MEANING,
        'known_discrepancies': KNOWN_DISCREPANCIES,
        'page_order': PAGE_ORDER,
        'nodes': nodes,
    }


# ── stick spin's own rules, and its half of the shared gate ────────────────────────────────────
_SPIN_LINES = {'TSS': 1, 'TSD': 2, 'TST': 3}

#: Ivan's opener database names one entry for the whole family; its four fields are the two bag-1
#: TSS boards, T placed, as drawn and mirrored (rule 2's `catalogue` route)
CATALOGUE_NAME = ('Single Double PC {Abbreviated: SDPC, Alt name: Singleyou, JP: SDパフェ} / Motchi PC '
                  '{JP: もっちパフェ} / Stickspin {JP: None} / SDPC-Spin {JP: None} / SDPC Extension {JP: None} / '
                  'Pyramid SDTD {JP: ピラミッドSDTD} / O Base SST {JP: O土台SST} / CHATEAUpener {JP: None}')


def _cond_pieces(cond) -> list:
    """Every piece a condition names, through `all` / `any` / `before` / `early`."""
    if isinstance(cond, list):
        return [p for c in cond for p in _cond_pieces(c)]
    if not isinstance(cond, dict):
        return []
    out = []
    for k in ('all', 'any'):
        out += _cond_pieces(cond.get(k, []))
    for k in ('before', 'early', 'decided_by'):
        v = cond.get(k, [])
        out += v if isinstance(v, list) else [v]
    return out


def _verbatims(obj, path=''):
    """Every `*_verbatim` string (or list of strings) in a dict tree, with where it sits."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.endswith('_verbatim') and isinstance(v, str):
                yield f'{path}.{k}', v
            elif k.endswith('_verbatim') and isinstance(v, list):
                for i, s in enumerate(v):
                    yield f'{path}.{k}[{i}]', s
            else:
                yield from _verbatims(v, f'{path}.{k}')
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _verbatims(v, f'{path}[{i}]')


def _letters(rows: list[str]) -> list[str]:
    """A board read with the muted (cleared-row) colours as their piece, and U as the T."""
    return [''.join(UPPER.get(c, 't' if c == 'U' else c) for c in r) for r in rows]


def _spin_rows(n: dict, boards: dict) -> list[str] | None:
    """The board whose U cells fire `n`'s spin: its own, or its `spin_board`'s."""
    if n.get('spin_board') in boards:
        return boards[n['spin_board']]
    if 'rows' in n and 'U' in ''.join(n['rows']):
        return n['rows']
    return None


def _cells_of(rows: list[str], ch: str) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(rows) for c, x in enumerate(row) if x == ch}


def _stickspin_checks(data: dict, ctx: dict) -> tuple[list[str], set[str]]:
    """The rules only this page needs, and the source discrepancies they measure."""
    bad: list[str] = []
    found: set[str] = set()
    boards, by_id, groups = ctx['boards'], ctx['by_id'], ctx['groups']
    nodes = data.get('nodes', [])
    quotes = {q['id']: q for q in data.get('quotes', [])}

    # every sentence the transcription leans on is a quote, so --html-dir finds it on the page
    qtext = [q['verbatim'] for q in quotes.values()]
    for where, v in _verbatims({k: data.get(k) for k in ('bag1', 'groups', 'nodes', 'lists')}):
        if not any(v in q for q in qtext):
            bad.append(f'verbatim: {where} is not one of the quoted sentences')

    # conditions name pieces; the side rule names J and L
    b1 = data.get('bag1', {})
    conds = [b1.get('requires'), b1.get('no_hold'), b1.get('side')] + [g.get('condition') for g in groups.values()]
    conds += [n.get('condition') for n in nodes]
    if any(p not in RT.PIECES for c in conds for p in _cond_pieces(c)):
        bad.append('condition: a condition names something that is not a piece')
    if sorted(b1.get('side', {}).get('decided_by', [])) != ['J', 'L']:
        bad.append('bag1-side: the side rule no longer names J and L')

    # the no-hold orders, read against the left board by support: some cell of the later piece sits
    # directly on a cell of the earlier one (gravity, not a planner)
    nh = b1.get('no_hold', {})
    left = boards.get(nh.get('node'))
    for c in nh.get('all', []):
        a, b = (p.lower() for p in c.get('before', ['?', '?']))
        if left is None or not any((r + 1, x) in _cells_of(left, a) for r, x in _cells_of(left, b)):
            bad.append(f'bag1-order: on {nh.get("node")} no {b.upper()} cell rests on a {a.upper()} cell, so '
                       f'%{a.upper()}>%{b.upper()} is not what the board needs')
    if [f'%{c["before"][0]}>%{c["before"][1]}' for c in nh.get('all', [])] != b1.get('no_hold_items_verbatim'):
        bad.append('bag1-order: the no-hold orders are not the page\'s listed items')

    # bag 1 is six pieces; each TSS board is it plus one T, stood or flat, clearing exactly one row
    for n in nodes:
        if 'spin_of' not in n:
            continue
        src = boards.get(n['spin_of'])
        if src is None or 'rows' not in n:
            bad.append(f'bag1-spin: {n["id"]} spin_of {n["spin_of"]!r} names no board')
            continue
        h = max(len(src), len(n['rows']))
        mine, theirs = bottom(n['rows'], h), bottom(src, h)
        u = _cells_of(mine, 'U')
        xy = [(x, h - 1 - r) for r, x in u]
        if [r.replace('U', EMPTY) for r in mine] != theirs or len(u) != 4 or (
                RT._norm(xy) not in RT._shapes('t')):
            bad.append(f'bag1-spin: {n["id"]} is not {n["spin_of"]} plus one T in its U cells')
        if after_spin(n['rows'])[1] != _SPIN_LINES.get(n.get('spin')):
            bad.append(f'spin: {n["id"]} names a {n.get("spin")} but its U slot clears '
                       f'{after_spin(n["rows"])[1]} rows')
        if (t_slot(n['rows']) == 'flat') != (n.get('t_orientation') == 'flat'):
            bad.append(f'bag1-spin: {n["id"]} t_orientation {n.get("t_orientation")!r} disagrees with its U cells')
    if sum(len(_cells_of(boards.get('bag1.left', []), ch)) for ch in 'ijlosz') != 24 or any(
            _cells_of(boards.get('bag1.left', []), ch) for ch in 'tUc'):
        bad.append('bag1-spin: bag1.left is not six pieces with no T')

    # the right bag-1 board is the left one mirrored: one shape, not two (rule `mirror-of` checks it)
    if any(n.get('mirror_of') and 'rows' in n and n['mirror_of'] in boards
           and bottom(n['rows'], RT.ROWS) == mirror(bottom(boards[n['mirror_of']], RT.ROWS)) for n in nodes):
        found.add('bag1.right:mirror')

    # a spin named on a board is the spin its U cells fire (its own, or its spin board's); every
    # upper-case (muted) row is exactly a row that spin clears
    for n in nodes:
        if 'spin_of' in n or not n.get('spin'):
            continue
        sr = _spin_rows(n, boards)
        if sr is None or after_spin(sr)[1] != _SPIN_LINES.get(n['spin']):
            bad.append(f'spin: {n["id"]} names a {n["spin"]} but its U slot clears '
                       f'{None if sr is None else after_spin(sr)[1]} rows')
    for n in nodes:
        rows = n.get('rows')
        if not rows or not any(c in UPPER for r in rows for c in r):
            continue
        filled = [r.replace('U', 't') for r in rows]
        muted = [i for i, r in enumerate(rows) if any(c in UPPER for c in r)]
        full = [i for i, r in enumerate(filled) if EMPTY not in r]
        if muted != full or any(c.islower() for i in muted for c in rows[i]):
            bad.append(f'muted: {n["id"]} draws muted rows {muted} where its spin clears rows {full}')

    # an after board is the board before its spin, cleared, letter for letter (U read as the T)
    for n in nodes:
        if n.get('after_of') in boards and 'rows' in n:
            left_, _ = after_spin(_letters(boards[n['after_of']]))
            h = max(len(left_), len(n['rows']))
            if bottom(left_, h) != bottom(_letters(n['rows']), h):
                bad.append(f'after-letters: {n["id"]} is not {n["after_of"]} cleared, letter for letter')

    # a group's forms share ONE occupancy; a group with no per-form condition is a measured gap; a
    # group whose sentence says only some pieces matter puts those pieces on the same cells
    for g in groups.values():
        members = [n for n in nodes if n.get('group') == g['id'] and 'rows' in n]
        occs = {tuple(RT.occ(bottom(n['rows'], RT.ROWS + 2))) for n in members}
        if g['id'] == '2.fire' and len(occs) != 1:
            bad.append(f'group: the forms of {g["id"]} no longer share one occupancy')
        for p in g.get('shared_pieces', []):
            if len({frozenset(_cells_of(bottom(n['rows'], RT.ROWS + 2), p.lower())) for n in members}) != 1:
                bad.append(f'group: the forms of {g["id"]} do not all put the {p} on the same cells')
        if members and all(n.get('condition') is None for n in members):
            found.add(f'{g["id"]}:no_conditions')

    # the TSD board drawn after both bag-2 forms: occupancy fits each, colours fit which?
    sb = boards.get('2.fire.tsd')
    if sb:
        drawn = _letters([r.replace('U', EMPTY) for r in sb])
        fits = [m['id'] for m in nodes if m.get('spin_board') == '2.fire.tsd' and 'rows' in m
                and bottom(m['rows'], RT.ROWS) == bottom(drawn, RT.ROWS)]
        users = [m['id'] for m in nodes if m.get('spin_board') == '2.fire.tsd']
        if fits == ['2.fire#1'] and len(users) == 2:
            found.add('2.fire.tsd:form1_colours')
        elif fits != users:
            bad.append(f'spin-board: 2.fire.tsd matches the colours of {fits} among {users}')

    # PC lists: the stated total re-derived along the base chain; a bag-2 board with a stated rate
    # and no list drawn on it; the もっちパフェ rate stated two ways
    for lst in data.get('lists', []):
        pats = [n for n in nodes if n.get('list') == lst['id']]
        if lst.get('total_lines') is not None and pats:
            total, cur, seen = len(bottom(pats[0]['rows'], 0)), lst.get('base'), set()
            while cur in by_id and cur not in seen:
                seen.add(cur)
                b = by_id[cur]
                if b.get('after_of') in boards:
                    total += after_spin(boards[b['after_of']])[1]
                    cur = by_id[b['after_of']].get('base')
                else:
                    cur = b.get('base')
            if total != lst['total_lines']:
                bad.append(f'lines: {lst["id"]} clears {total} lines over its line, the page says '
                           f'{lst["total_lines"]}')
            if f'{lst["total_lines"]}ライン' not in quotes.get(lst.get('total_lines_quote'), {}).get('verbatim', ''):
                bad.append(f'lines: quote {lst.get("total_lines_quote")!r} does not state '
                           f'{lst["total_lines"]}ライン for {lst["id"]}')
        rest = quotes.get(f'{lst["id"]}.rest', {}).get('verbatim', '')
        if f'({lst.get("rest_stated")}通り)' not in rest:
            bad.append(f'list-rest: {lst["id"]} rest_stated {lst.get("rest_stated")} is not the page\'s 通り count')
    listed = {lst['parent'] for lst in data.get('lists', [])}
    for n in nodes:
        q = quotes.get(n['id'], {})
        if n.get('bag') == 2 and 'rows' in n and n.get('node_kind') is None and 'list' not in n \
                and '%' in (q.get('figure') or '') and 'パフェ率' in q.get('verbatim', '') \
                and n['id'] not in listed:
            found.add(f'{n["id"]}:no_pc_drawn')
    intro, pc = quotes.get('2.mochi.intro', {}), quotes.get('2.mochi.pc', {})
    if intro.get('figure') and pc.get('figure') and intro['figure'] != pc['figure']:
        found.add('2.mochi.pc:rate_conflict')

    # the page names a bag-4 TSD and draws no bag-4 board
    if any(n.get('node_kind') == 'text_only' and n.get('bag') == 4 for n in nodes) and not any(
            n.get('bag') == 4 and 'rows' in n for n in nodes):
        found.add('2.fire.bag4:not_drawn')
    return bad, found


SPEC = RT.TranscriptionSpec(
    out=OUT, build=build, alphabet=ALPHABET, non_board=NON_BOARD,
    harddrop=None,
    catalogue={'name': CATALOGUE_NAME, 'nodes': ['bag1.fire', 'bag1.pc']},
    board_kinds=frozenset({'illustration'}),
    pc_lines=7, prior_letters='',
    upper_groups={'I': 'merge', 'J': 'merge', 'L': 'merge', 'O': 'merge', 'S': 'merge', 'Z': 'merge'},
    slot_flags=SLOT_FLAGS, occupancy_class_parents=2, extra_checks=_stickspin_checks)


def verify(data: dict) -> list[str]:
    return RT.verify(data, SPEC)


def drift(data: dict) -> list[str]:
    return RT.drift(data, SPEC)


# ── selftest ───────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    """A gate nothing can fail is decorative. Plant one defect per rule, each in a named stick spin id."""

    def drop_pattern(d):
        d['nodes'] = [n for n in d['nodes'] if n['id'] != '2.mochi.pc#14']

    def break_mirror(d):
        setcell(node(d, 'bag1.right')['rows'], 1, 8, '-')            # one s cell of the mirror

    def fire_off(d):
        setcell(node(d, 'bag1.fire')['rows'], 1, 1, '-')             # a z cell gone from the TSS board

    def t_moved(d):
        n = node(d, 'bag1.pc')
        setcell(n['rows'], 3, 3, '-')
        setcell(n['rows'], 3, 4, 'U')                                 # the flat T slid one column

    def orientation(d):
        node(d, 'bag1.fire')['t_orientation'] = 'flat'

    def base_off(d):
        setcell(node(d, 'bag1.pc.after')['rows'], 2, 1, '-')         # a cell of the SD bag-2 base gone

    def ghost_group(d):
        node(d, '2.fire#2')['group'] = '2.fire.nowhere'

    def bad_cell(d):
        setcell(node(d, '2.sd.tst')['rows'], 0, 0, 'p')

    def flag_flip(d):
        n = node(d, '2.sd.pc#4')
        n['t_flat_shape'] = not n['t_flat_shape']

    def drop_discrepancy(d):
        d['known_discrepancies'] = [x for x in d['known_discrepancies'] if x['id'] != '2.mochi.pc:rate_conflict']

    def recolour(d):
        setcell(node(d, '2.mochi')['rows'], 1, 0, 'j')                # an i cell drawn as j

    def dup_form(d):
        node(d, '2.fire#2')['rows'] = list(node(d, '2.fire#1')['rows'])

    def basic_off(d):
        setcell(d['basic_form'][1]['rows'], 2, 0, 'o')               # basic.2's i drawn o

    def tall(d):
        node(d, '2.fire.td#2')['rows'].insert(0, 'i---------')
        node(d, '2.fire.td#2')['rows'][1] = 'i---------'
        node(d, '2.fire.td#2')['rows'][2] = 'i---------'

    def no_reason(d):
        node(d, '2.fire.td#1')['unmatchable'] = ''

    def c_cells(d):
        setcell(node(d, '2.sd.stmb')['rows'], 0, 9, 'c')              # a c where 2.sd.after has none

    def lost_text(d):
        d['nodes'] = [n for n in d['nodes'] if n['id'] != '2.fire.bag4']

    def wrong_after(d):
        node(d, '2.mochi.after')['after_of'] = '2.sd'

    def after_letters(d):
        setcell(node(d, 'bag1.fire.after')['rows'], 5, 2, 'o')        # an s cell of the after board drawn o

    def side_rule(d):
        d['bag1']['side']['decided_by'] = ['J', 'O']

    def order_flip(d):
        d['bag1']['no_hold']['all'][0]['before'] = ['Z', 'O']

    def wrong_spin(d):
        node(d, '2.sd.imperial')['spin'] = 'TST'

    def tss_lines(d):
        node(d, 'bag1.pc')['spin'] = 'TSD'

    def muted_row(d):
        n = node(d, '2.sd.stmb.spin')
        n['rows'][4] = n['rows'][4].upper()                           # a row the spin does not clear, muted

    def spin_board_off(d):
        setcell(node(d, '2.sd.tst.spin')['rows'], 1, 0, '-')          # the spin board off its board

    def total_lines(d):
        next(x for x in d['lists'] if x['id'] == '2.sd.pc')['total_lines'] = 9

    def rest_count(d):
        n = next(x for x in d['lists'] if x['id'] == '2.mochi.pc')
        n['rest_stated'], n['shown'] = 10, 4
        for p in d['nodes']:
            if p.get('list') == '2.mochi.pc' and p['index'] == 5:
                p['listed_under'] = 'rest'

    def unquoted(d):
        node(d, '2.mochi.i_right')['condition_verbatim'] = '%Iが早い場合には100%です。'

    def cond_piece(d):
        node(d, '2.mochi.i_right')['condition']['early'] = 'X'

    def pc_lines(d):
        next(x for x in d['lists'] if x['id'] == '2.sd.pc')['pc_lines'] = 8

    def sz_moved(d):
        n = node(d, '2.fire.td#3')
        setcell(n['rows'], 3, 2, '-')
        setcell(n['rows'], 3, 4, 's')                                 # one S cell elsewhere

    def form_colours(d):
        node(d, '2.fire.tsd')['rows'][4] = 'ICUUULLLZZ'               # the TSD board in form 2's roof colour

    def pc_drawn(d):
        x = next(x for x in d['lists'] if x['id'] == '2.mochi.pc')
        x['parent'] = '2.mochi.i_right'                               # a list drawn on the I-right board

    def bag4_drawn(d):
        node(d, '2.fire.td#4')['bag'] = 4                             # a bag-4 board appears

    mutants = [
        (drop_pattern, 'a dropped PC pattern', 'list-count:'),
        (break_mirror, 'the right board no longer the left mirrored', 'mirror-of:'),
        (fire_off, 'the stood-T board off the bag-1 board', 'bag1-spin:'),
        (t_moved, 'the flat T moved out of its slot', 'bag1-spin:'),
        (orientation, 'a stood T called flat', 'bag1-spin:'),
        (base_off, 'a bag-2 base cell gone from bag1.pc.after', 'bag2-base:'),
        (ghost_group, 'a group no node declares', 'grammar:'),
        (bad_cell, 'a cell outside the alphabet', 'grammar:'),
        (flag_flip, 'a t_flat_shape flag flipped', 'grammar:'),
        (drop_discrepancy, 'a dropped known discrepancy', 'discrepancy:'),
        (recolour, 'one cell of the Mochi board recoloured', 'discrepancy:'),
        (dup_form, 'two 2.fire forms made equal by colour', 'distinct:'),
        (basic_off, 'a 基本形 board off its node', 'basic-form:'),
        (tall, 'a 9-row board not marked unmatchable', 'grammar:'),
        (no_reason, 'an unmatchable node with no reason', 'grammar:'),
        (c_cells, 'a c cell where the SD TSD leaves none', 'c-cells:'),
        (lost_text, 'a deleted text-only node', 'non-board:'),
        (wrong_after, 'mochi.after read off the wrong spin', 'after-of:'),
        (after_letters, 'an after board recoloured', 'after-letters:'),
        (side_rule, 'the bag-1 side rule naming another piece', 'bag1-side:'),
        (order_flip, 'a no-hold order reversed', 'bag1-order:'),
        (wrong_spin, 'a TSD fallback named a TST', 'spin:'),
        (tss_lines, 'the TSS named a TSD', 'spin:'),
        (muted_row, 'a muted row the spin does not clear', 'muted:'),
        (spin_board_off, 'a spin board off its board', 'spin-board:'),
        (total_lines, 'the 8ライン total misstated', 'lines:'),
        (rest_count, 'the 9通り rest misstated', 'list-rest:'),
        (unquoted, 'a verbatim field that is not on the page', 'verbatim:'),
        (cond_piece, 'a condition naming a non-piece', 'condition:'),
        (pc_lines, 'the PC list checked at 8 body lines', 'pc:'),
        (sz_moved, 'a TD form with its S moved', 'group:'),
        (form_colours, 'the TSD board in neither form\'s colours', 'spin-board:'),
        (pc_drawn, 'a PC list on the I-right board makes its gap unmeasured', 'discrepancy:'),
        (bag4_drawn, 'a bag-4 board makes the bag-4 gap unmeasured', 'discrepancy:'),
    ]
    spec_mutants = [
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'catalogue': {**s.catalogue, 'name': s.catalogue['name'][:-1]}}),
         'the catalogue entry name changed', 'catalogue:'),
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'catalogue': {**s.catalogue, 'nodes': ['bag1.fire']}}),
         'one catalogue node dropped (a field left unmatched)', 'catalogue:'),
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'catalogue': {**s.catalogue, 'nodes': ['bag1.fire', 'bag1.left']}}),
         'the catalogue node changed to the board without the T', 'catalogue:'),
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'catalogue': None}),
         'no cross-source at all', 'harddrop:'),
    ]
    return RT.run_selftest(SPEC, mutants, {'board': ('cccjltttoo', 'cccj-tttoo'),
                                           'text': ('3巡目TST→4巡目TSD', '3巡目TST→4巡目TSS'),
                                           'hand_edit': '2.sd', 'quote': '2.mochi.i_right'},
                           spec_mutants)


def main() -> int:
    return RT.main(SPEC, selftest, __doc__)


if __name__ == '__main__':
    raise SystemExit(main())

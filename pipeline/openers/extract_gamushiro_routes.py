"""Transcribe shiwehi.com's ガムシロ積み (Gamushiro Stacking) route page into `gamushiro-routes.json`.

    python3 -m pipeline.openers.extract_gamushiro_routes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_gamushiro_routes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_gamushiro_routes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_gamushiro_routes --html-dir <dir> --write  # ...and rewrite

The fifth opener ROUTE page, after 迷走砲, はちみつ砲, 山岳積み2号 and stick spin, and the first that is
a REFERENCE opener for this corpus rather than one its two players use: it is the most-used opener of
しゃけごはん (shiwehi's strongertemplate.php, July 2024), not of yachi or pinglamb. One bag-1 shape
(six pieces with the L held, or its mirror; `bag1.l_top` is the same board with the L placed on the
O), a bag-2 four-line Perfect Clear list on the L-held board (`2.pc4`), two 通常 bag-2 forms sharing
one occupancy (`2.normal#1` %L>%O, `2.normal#2` %O>%T%L) that fire one TST drawn on its own board
(`2.normal.tst`), the bag-3 8-line PC list after it (`2.normal.pc`, 8 of the page's stated 63), two
インペリアルクロス boards for when no PC is taken, and a 妥協 bag-2 form (`2.compromise`) with its TST.
Every rule the openers share is `route_transcription.py`'s, once; this file holds the transcription,
its `SPEC` and the rules only this page needs (`_gamushiro_checks`).

WHERE THE TRANSCRIPTION COMES FROM. `NODES` below is a literal, hand-checked transcription of the
page's RAW HTML, fetched the way 山岳積み2号's and stick spin's were: curl through the session proxy,
TLS verification on, with a CA bundle adding the Let's Encrypt YE2 intermediate shiwehi.com omits.
The hash is of the page's own bytes. The page is not committed; CI cannot fetch it. Boards are plain
text in `<div class="ttt">`, one row per line, drawn by the site's `column-exp.js` (re-fetched for
this page: the same bytes 山岳積み2号 and stick spin recorded). ONE of the page's 25 boards sits inside
an HTML comment (a 「残り55パターン」 block, never rendered): it is kept as a `commented_out` node so the
raw-HTML snapshot check still sees every board in order, and it is unmatchable.

THE CROSS-SOURCE IS HARDDROP'S OWN GAMUSHIRO PAGE, NOT `wiki-openers.json`. That transcription
carries seven openers and lists Gamushiro Stacking only as a member of Category:Triple_Double_openers;
Ivan's catalogue (`opener-fields.json`) has no entry. Adding a field to `wiki-openers.json` would
re-emit every session's `opener-facts.json` (the 六個具名定式 table reads it), which a reference page
has no business doing. So rule 2 uses the shared gate's `harddrop_page` route: harddrop's
Gamushiro_Stacking page (oldid 37490, fetched 2026-10-13) read by `extract_wiki_openers.boards`, the
parser `wiki-openers.json` itself is transcribed with, and the four diagrams under its 「First Bag
setup」 heading recorded in `cross_source` with the page's hash. They are, cell for cell and in
colour, `bag1.left` and `bag1.l_top` as drawn and mirrored: an independent drawing of both bag-1
boards, the 7-lock one included (so `bag1.l_top` is a bag-1 board on harddrop's reading, not only a
基本形 summary). `--html-dir` re-parses that page from the same directory. Two further ties are this
page's own rules: the category membership (the route fires its TST before the TSD, as a Triple
Double opener must), and the sentence 「山岳積み2号と%Iの位置がずれた形」 checked against harddrop's
Mountainous Stacking 2 field in `wiki-openers.json`: delete the I's column from each and the rest is
equal letter for letter.

WHAT IS AN INFERENCE, flagged in the JSON rather than in prose only:

  * upper-case `L` has no legend on the page; the renderer draws it muted orange. It is read as the
    bag-1 L, held (「%Lをホールドしておきます」) and placed in bag 2, exactly 山岳積み2号's reading:
    the boards carrying an `L` have `c` cells exactly the L-held six-lock board (rule 3). `C` is the
    renderer's light grey in the rows a TST clears (checked: every `C` row is a row the U slot clears).
  * 「%J%Zが早い」 is read as an early PAIR, checked by support (each rests something else on it);
    「%J>%S」「%Z>%T」 (the left pattern's no-hold condition) and the two 通常 headings 「%L>%O」 and
    「%O>%T%L」 are read as ORDERS, each checked against its board where the board forces one (a
    cell of the later piece resting on the earlier, or the earlier piece filling a row the TST
    clears); the 妥協 trigger 「%T>%L%O」 is a stated trigger the board does not force, recorded as such.
    The 妥協 board's own heading 「%L>%O」 is NOT read as an order: its bag-2 l rests on the O and only
    the held L lies under it, so it is a named discrepancy (`2.compromise:heading_vs_board`).
  * the no-hold condition and 「%Lをホールドしておきます」 sit side by side: read as "no hold beyond the L".
  * the インペリアルクロス boards are called bag 3 by OUR READING (the page says only パフェを取れない場合).

THE TERMS are the same shiwehi.com terms page 迷走砲 links to, imported from that transcription
rather than copied (read 2026-10-11 there; not re-read for this page).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS
from pipeline.openers.route_transcription import EMPTY, after_spin, bottom, mirror, node, setcell, t_slot

HERE = Path(__file__).resolve().parent
OUT = HERE / 'gamushiro-routes.json'
WIKI = HERE / 'wiki-openers.json'
MOUNTAINOUS2 = HERE / 'mountainous2-routes.json'

ALPHABET = frozenset('-ijlostzcULC')


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/gamushiro.php',
    'title': 'ガムシロ積み(Gamushiro Stacking)',
    'updated': '2024-08-01',
    'fetched': '2026-10-13',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle '
                    'that adds the Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), '
                    'the method 山岳積み2号 and stick spin used. The snapshot is the page\'s raw HTML, byte for '
                    'byte; every board is plain text in it, 25 ten-wide boards in page order (one of them '
                    'inside an HTML comment). Comparable with 山岳積み2号\'s and stick spin\'s hashes (raw '
                    'HTML), not with the markdown renderings 迷走砲 and はちみつ砲 hashed.',
    'snapshot_file': 'gamushiro.html',
    'snapshot_sha256': '5817c58d2927514f462b0cee6ef31c8b9a6621488545c87c8e4f1593523e6f81',
    'snapshot_bytes': 29700,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable '
                     'in CI: the page is not committed and cannot be fetched there. Re-check with '
                     '--html-dir after any refetch (with harddrop\'s page, cross_source, beside it); an '
                     'HTML hash moves with ANY byte of the page (ads, sidebar, a date), so a moved hash '
                     'means "read the board diff", not "the boards changed". Sentences are compared '
                     'against the page with its tags dropped.',
    'renderer': {
        'url': 'https://shiwehi.com/tetris/mutual/column-exp.js?date=20210408',
        'read': '2026-10-13',
        'sha256': '95c431a4147f9c30fc0e1bae935e6af6f5669c3d2fa1edfc388848e69ab62570',
        'sha256_note': 'the same bytes 山岳積み2号 and stick spin recorded, re-fetched for this page',
        'colorMap_used': {'c': '#a3a3a3', 'C': '#cccccc', 'L': '#d8904d (muted l)',
                          'U': '#c8a6ff with a #8400ff radial dot', '-': '#000000'},
        'rows': 'textContent split on whitespace, one row per token',
        'mirror_button': 'body.reversed swaps j<->l, s<->z (and upper case) and reverses nothing else in '
                         'the char map; the canvas is redrawn mirrored',
    },
    'decorative_images': ['ガムシロ積み(Gamushiro Stacking)タイトル画像'],
    'references_listed': ['https://tetrisopener.wicurio.com/index.php?%E3%82%AC%E3%83%A0%E3%82%B7%E3%83%AD%E7%A9%8D%E3%81%BF',
                          'https://w.atwiki.jp/tetrismaps/pages/195.html'],
    'references_note': 'the wicurio page (fetched 2026-10-13) draws its boards as images only, so it is not '
                       'a machine-checkable source; the cross-source is harddrop\'s page (cross_source)',
    'related_pages': ['./mountainous2.php', './honeycup.php', './pancake.php', './dpc.php', './3rdpc.php',
                      './imperialcross.php'],
    'why_this_opener': {
        'reading': 'a REFERENCE opener: not one this corpus\'s two players are known to use (the corpus count is '
                   'analysis/gamushiro-facts.json\'s, never typed here). It is here because shiwehi.com\'s own survey '
                   'of the opener templates strong Puyo Puyo Tetris 2 players used names it as the most-used opener '
                   'of しゃけごはん, the winner of the GRAND MASTERS rank of the PPT2 section of the 2024-07-28 '
                   '「Tetris® Block Party」 online tournament',
        'url': 'https://shiwehi.com/tetris/template/strongertemplate.php',
        'title': '強い人はどんな開幕テンプレを使っているのか(2024年)',
        'updated': '2024-08-21',
        'fetched': '2026-10-13',
        'fetch_method': 'the same curl method as `source` (TLS verification on, the YE2 bundle); raw HTML, not committed, not gated',
        'snapshot_sha256': '7dba7454965206c112f77382d53b44d820fac035ae81a152a60862b511ece830',
        'snapshot_bytes': 45991,
        'surveyed': 'streams dated 2024-07-12 to 2024-07-31, games against Tetris players only',
        'counts_as_printed': {'ガムシロ積み': 48, 'はちみつ砲': 23, '合計': 83,
                              'tournament_only': {'はちみつ砲': 14, 'ガムシロ積み': 13, '合計': 29}},
        'source_caveat': 'the page itself warns the sample may be biased: しゃけごはん does not stream, so information is '
                         'scarce; inside the tournament\'s 29 games the two openers were used about equally (はちみつ砲 14, '
                         'ガムシロ積み 13); and about two thirds of the games (62 of 81 in its own words, against the table\'s '
                         'total of 83) were against あめみやたいよう, who plays ガムシロ積み almost exclusively, which may '
                         'inflate its count',
        'not_checked': 'hand-read on 2026-10-13; no gate re-reads this page. The pages quote only the two counts and the caveat',
    },
}

#: harddrop's own Gamushiro page, read by the parser wiki-openers.json is transcribed with. Rule 2's
#: `harddrop_page` route compares `bag1.left` and `bag1.l_top` with these four fields; `--html-dir`
#: re-parses the page (`route_transcription.check_cross_source`).
CROSS_SOURCE = {
    'kind': 'harddrop_page',
    'page': 'Gamushiro_Stacking',
    'url': 'https://harddrop.com/wiki/Gamushiro_Stacking',
    'oldid': 37490,
    'oldid_note': 'wgRevisionId and wgCurRevisionId of the fetched page; the only oldid it carries',
    'fetched': '2026-10-13',
    'fetch_method': 'curl through the session proxy, TLS verification ON (no extra CA needed). The snapshot '
                    'is the page\'s raw HTML; it is not committed',
    'snapshot_file': 'Gamushiro_Stacking.html',
    'snapshot_sha256': 'feab02ba2c0abc0a9e06ea8a12e65fd063979ec21312787268a7c5c3ef761880',
    'snapshot_bytes': 1825312,
    'parser': 'pipeline.openers.extract_wiki_openers.boards, fields trimmed by its trim(): the parser '
              'wiki-openers.json is transcribed with',
    'heading': 'First Bag setup',
    'fields': [
        ['S......I..', 'SS....TI..', 'JS.ZZTTIOO', 'JJJ.ZZTIOO'],
        ['..I......Z', '..IT....ZZ', 'OOITTSS.ZL', 'OOITSS.LLL'],
        ['........L.', 'S......IL.', 'SS....TILL', 'JS.ZZTTIOO', 'JJJ.ZZTIOO'],
        ['.J........', '.JI......Z', 'JJIT....ZZ', 'OOITTSS.ZL', 'OOITSS.LLL'],
    ],
    'fields_note': 'the page\'s four diagrams under 「First Bag setup」, in order: the L-held six-lock board, '
                   'its mirror, the seven-lock board with the L on the O, its mirror',
    'why_not_wiki_openers': 'wiki-openers.json transcribes seven openers and has no Gamushiro field; adding '
                            'one would re-emit every session\'s opener-facts.json (the 六個具名定式 table reads '
                            'it). Ivan\'s catalogue (opener-fields.json) has no Gamushiro entry either',
    'category': {'name': 'Triple Double openers', 'member': 'Gamushiro Stacking',
                 'where': 'wiki-openers.json triple_double_category.members'},
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ, align at the BOTTOM row',
    '-': 'empty',
    'i o t s z j l': 'a cell of that piece',
    'c': 'a cell filled before this diagram (earlier bags), grey',
    'L': 'the bag-1 L, held (「%Lをホールドしておきます」) and placed in bag 2, drawn in a muted L colour (page legend: none; OUR READING, as for 山岳積み2号: the c cells of every board drawing it are exactly the L-held board)',
    'C': 'an earlier cell in a row the TST clears, drawn light grey (page legend: none; OUR READING, checked: every C row is a row the U slot clears)',
    'U': 'the T-spin slot',
    '%X': "the X piece; '%J>%S' means J before S",
}


#: Every sentence the transcription leans on, verbatim. `--html-dir` finds each on the page (tags
#: dropped), and every `*_verbatim` field below must be one of these (`_gamushiro_checks`).
QUOTES = [
    {'id': 'overview.intro', 'figure': '8ライン',
     'verbatim': 'ここでは、ガムシロ積み(Gamushiro Stacking)という、TDアタック→8ラインパフェを狙う開幕テンプレについて紹介していきます。'},
    {'id': 'overview.pc4_rare', 'figure': None, 'verbatim': 'また、稀に4ラインパフェを狙うこともできます。'},
    {'id': 'basic.ideal', 'figure': '8段',
     'verbatim': 'TST→TSD→8段パフェが理想ルートで、中開け4列RENにも派生できます。'},
    {'id': 'overview.mountainous2', 'figure': None, 'verbatim': '山岳積み2号と%Iの位置がずれた形になります。'},
    {'id': 'basic.mirror', 'figure': None, 'verbatim': '左右反転図が見たい場合は右下のボタンを押してください。'},
    {'id': 'merit.lines21', 'figure': '21ライン',
     'verbatim': '最大TST→TSD→8段パフェで21ラインという高火力を狙うことができる。',
     'note': '21 is attack sent, not lines cleared; nothing here re-derives it'},
    {'id': 'merit.setup_rate', 'figure': '100%', 'verbatim': '1巡目のセットアップ率が左右反転含めて100%と高め。'},
    {'id': 'merit.ren', 'figure': None, 'verbatim': '中開けRENに派生できる。'},
    {'id': 'demerit.tsd', 'figure': None,
     'verbatim': 'パフェルートの際、はちみつ砲と比較するとTSDを打てない可能性が高い。'},
    {'id': 'demerit.patterns', 'figure': None, 'verbatim': 'パフェパターンが多いためパフェが若干見づらい。'},
    {'id': 'bag1.requires', 'figure': None, 'verbatim': '1巡目の組み方は上図の通りで、%J%Zが早い必要があります。'},
    {'id': 'bag1.hold', 'figure': None, 'verbatim': '%Lをホールドしておきます。'},
    {'id': 'bag1.no_hold', 'figure': None, 'verbatim': '左のパターンがホールド無しで組める条件は以下の通りです。'},
    {'id': 'bag1.no_hold.j_s', 'figure': None, 'verbatim': '%J>%S'},
    {'id': 'bag1.no_hold.z_t', 'figure': None, 'verbatim': '%Z>%T'},
    {'id': 'bag1.side', 'figure': None,
     'verbatim': 'ここでは、以下左のパターン(%Lホールド)で説明していきますが、右下にある反転ボタンを押すことで左右反転の図を見ることができます。'},
    {'id': '2.pc4', 'figure': '3パターン26.19%', 'verbatim': 'ガムシロ積みでは3パターン26.19%で4ラインパフェを狙うことができます。'},
    {'id': '2.pc4.rare', 'figure': None,
     'verbatim': '使用頻度は高くないと思いますが、覚えておけば奇襲にもなるかもしれません。'},
    {'id': '2.normal', 'figure': '2パターン',
     'verbatim': '組み分けとしては%Oが早いかどうかで2パターンで殆どの場合同じ形になります。'},
    {'id': '2.normal#1', 'figure': None, 'verbatim': '%L>%Oの場合',
     'note': 'a heading; the page prints the same words again over the 妥協 form'},
    {'id': '2.normal#2', 'figure': None, 'verbatim': '%O>%T%Lの場合', 'note': 'a heading'},
    {'id': '2.normal.tst', 'figure': None, 'verbatim': 'その後TSTを打ちます。'},
    {'id': '2.normal.pc.rate', 'figure': '99.09%', 'verbatim': 'その後3巡目に99.09%の確率でパフェを取ることができます。'},
    {'id': '2.normal.pc.tsd', 'figure': None, 'verbatim': 'ミノ順によってはTSDを打ってからパフェを取ることができます。'},
    {'id': '2.normal.pc.after', 'figure': None, 'verbatim': '8段パフェを取った後はDPCや3回目パフェを狙うことができます。'},
    {'id': '2.normal.pc', 'figure': '63 / 8', 'verbatim': '(最小63パターン中高確率8パターン)'},
    {'id': '2.normal.pc.rest', 'figure': '55', 'verbatim': '残り55パターン', 'rendered': False,
     'note': 'the summary of a <details> block that sits inside an HTML comment: in the raw HTML, never rendered'},
    {'id': '2.normal.imperial', 'figure': None,
     'verbatim': 'また、パフェを取れない場合には下図のようにインペリアルクロスを組むことで火力を継続することができます。'},
    {'id': '2.compromise', 'figure': None, 'verbatim': '%T>%L%Oの場合には通常系が組めないため、妥協形を組みます。'},
]


BAG1 = {
    'locks': 6,
    'hold': 'L',
    'hold_verbatim': '%Lをホールドしておきます。',
    'requires_verbatim': '1巡目の組み方は上図の通りで、%J%Zが早い必要があります。',
    'requires': {'early': ['J', 'Z'], 'node': 'bag1.left'},
    'requires_note': 'OUR READING of 「%J%Zが早い」 as an early PAIR; checked against bag1.left by support (each of J and Z has another piece resting on it)',
    'no_hold_verbatim': '左のパターンがホールド無しで組める条件は以下の通りです。',
    'no_hold': {'all': [{'before': ['J', 'S']}, {'before': ['Z', 'T']}], 'node': 'bag1.left'},
    'no_hold_items_verbatim': ['%J>%S', '%Z>%T'],
    'no_hold_note': 'the left pattern\'s condition, read as orders and checked against bag1.left by support (a cell of the later piece rests on a cell of the earlier one). It sits beside 「%Lをホールドしておきます」, so OUR READING is "no hold beyond the L"; the right pattern\'s (its mirror: L>Z, S>T) is not stated',
    'side_verbatim': 'ここでは、以下左のパターン(%Lホールド)で説明していきますが、右下にある反転ボタンを押すことで左右反転の図を見ることができます。',
    'side': None,
    'side_note': 'unlike 山岳積み2号 and stick spin, this page names no piece that decides the side',
    'mountainous2': {'quote': 'overview.mountainous2', 'i_column': 7, 'mountainous2_i_column': 0,
                     'note': 'the page\'s 「山岳積み2号と%Iの位置がずれた形」, checked against harddrop\'s Mountainous Stacking 2 field (wiki-openers.json mountainous_2): delete column i_column from bag1.left and column mountainous2_i_column from that field, and the rest is equal letter for letter'},
}


BASIC_FORM = [
    {
        'id': 'basic.1',
        'same_as': 'bag1.l_top',
        'rows': _b('---------- ---------- ---------- --------l- s------il- ss----till js-zzttioo jjj-zztioo'),
        'canvas': 'tetCanvas0',
    },
    {
        'id': 'basic.2',
        'same_as': '2.normal#1',
        'differs': 'the TST slot drawn U (its cells are 2.normal.tst\'s U cells, checked) and the held L drawn as an earlier cell (c)',
        'recolour': {'-': 'U', 'L': 'c'},
        'rows': _b('i-------oo i-------oo ijj-----ll ij----sscl cjUzzssccl ccUUzzcccc ccUccccccc ccc-cccccc'),
        'canvas': 'tetCanvas1',
    },
    {
        'id': 'basic.3',
        'same_as': '2.normal.pc#1',
        'differs': 'the TSD T is drawn U instead of t',
        'recolour': {'t': 'U'},
        'rows': _b('---------- ---------- ---------- cjiiiillcc cjjjsszlcc cccsszzlcc ccUUUzcccc cccUcccccc'),
        'canvas': 'tetCanvas2',
    },
]


KNOWN_DISCREPANCIES = [
    {
        'id': 'bag1.right:mirror',
        'what': 'the right bag-1 board is the left one mirrored with J<->L, S<->Z (cell for cell), so the page has ONE bag-1 shape, not two',
    },
    {
        'id': '2.normal.pc:stated_vs_drawn',
        'what': 'the page states 63 patterns (最小63パターン) and draws 8 (中高確率8パターン)',
    },
    {
        'id': '2.normal.pc:non_exhaustive',
        'what': 'the 8 drawn PC patterns are the page\'s high-probability subset, not every way to take the PC',
    },
    {
        'id': '2.normal.pc:rest_commented_out',
        'what': 'the 「残り55パターン」 block is inside an HTML comment, so the page never renders it, and its only board is 2.normal.after redrawn as an empty template: the other 55 patterns are not drawn anywhere',
    },
    {
        'id': '2.normal.imperial:no_conditions',
        'what': 'two インペリアルクロス boards (the I at the left wall, or the I and J at column 6-7 under the O) and no condition saying which',
    },
    {
        'id': '2.compromise:heading_vs_board',
        'what': 'the 妥協 board is headed 「%L>%Oの場合」, but its bag-2 l rests on the O: only the held bag-1 L lies under the O, so the heading cannot be a bag-2 dealing order (a bag-2 L dealt before the O, with the T already in the hold, has nowhere to go); read as the held L placed before the O, and not used as a queue condition',
    },
    {
        'id': 'overview:ren_not_drawn',
        'what': 'the 基本形 sentence names a 中開け4列REN derivation (and メリット a 中開けREN one); the page draws none',
    },
]


#: Every node, in page order (the PC patterns are inserted after their anchor by `build`).
NODES: list[dict] = [
    {
        'id': 'bag1.left',
        'bag': 1,
        'parent': None,
        'locks': 6,
        'label_jp': '1巡目とミノ順',
        'label_jp_note': 'the section heading; the page draws this board with no caption of its own (its sentence calls it 左のパターン(%Lホールド))',
        'label': "bag 1 with the L held (the page's left pattern; harddrop's first First Bag setup field)",
        'rows': _b('---------- ---------- s------i-- ss----ti-- js-zzttioo jjj-zztioo'),
    },
    {
        'id': 'bag1.right',
        'bag': 1,
        'parent': None,
        'locks': 6,
        'label_jp': '1巡目とミノ順',
        'label_jp_note': 'the section heading; the page draws this board with no caption of its own',
        'label': "bag 1 with the J held, mirrored (the page's right pattern)",
        'mirror_of': 'bag1.left',
        'classifier_note': 'exactly bag1.left mirrored with J<->L and S<->Z swapped (checked cell for cell); a mirror-aware classifier must treat it as the SAME node, not a second branch',
        'rows': _b('---------- ---------- --i------z --it----zz ooittss-zl ooitss-lll'),
    },
    {
        'id': 'bag1.l_top',
        'bag': 1,
        'parent': None,
        'locks': 7,
        'drawn_as': 'basic.1',
        'label_jp': '基本形 1',
        'label_jp_note': 'drawn only as the first 基本形 board',
        'label': 'bag 1 with the L placed on the O at the right (drawn only as 基本形 1; harddrop draws it under First Bag setup)',
        'derivation': 'bag1.left plus four l cells (checked), on exactly the cells where the held L stands in the 通常 %L>%O form and the 妥協 form (their upper-case L, checked)',
        'rows': _b('---------- ---------- ---------- --------l- s------il- ss----till js-zzttioo jjj-zztioo'),
    },
    {
        'id': '2.normal#1',
        'bag': 2,
        'parent': None,
        'base': 'bag1.left',
        'spin': 'TST',
        'spin_board': '2.normal.tst',
        'label_jp': '通常ルート %L>%Oの場合',
        'label': 'normal bag 2, form 1 (%L>%O: the held L on the O at the right, the bag-2 L and the O over it)',
        'group': '2.normal',
        'variant': 1,
        'condition_verbatim': '%L>%Oの場合',
        'condition': {'all': [{'before': ['L', 'O']}]},
        'condition_evidence': [{'before': ['L', 'O'], 'by': 'support'}],
        'condition_note': 'OUR READING of the heading as L before O; the board forces it (the O rests on the bag-2 L)',
        'rows': _b('i-------oo i-------oo ijj-----ll ij----ssLl cj-zzsscLl cc--zzccLL cc-ccccccc ccc-cccccc'),
    },
    {
        'id': '2.normal#2',
        'bag': 2,
        'parent': None,
        'base': 'bag1.left',
        'spin': 'TST',
        'spin_board': '2.normal.tst',
        'label_jp': '通常ルート %O>%T%Lの場合',
        'label': 'normal bag 2, form 2 (%O>%T%L: the O at the right, the held L and the bag-2 L over it)',
        'group': '2.normal',
        'variant': 2,
        'condition_verbatim': '%O>%T%Lの場合',
        'condition': {'all': [{'before': ['O', 'T']}, {'before': ['O', 'L']}]},
        'condition_evidence': [{'before': ['O', 'T'], 'by': 'spin_rows'}, {'before': ['O', 'L'], 'by': 'support'}],
        'condition_note': 'OUR READING of 「%O>%T%L」 as O before T and O before L; the board forces both (the O fills rows the TST clears; the held L rests on the O)',
        'rows': _b('i-------ll i-------Ll ijj-----Ll ij----ssLL cj-zzsscoo cc--zzccoo cc-ccccccc ccc-cccccc'),
    },
    {
        'id': '2.normal.tst',
        'bag': 2,
        'parent': '2.normal',
        'label_jp': '通常ルート その後TSTを打ちます',
        'label': 'normal bag 2 with the TST slot and the three cleared rows highlighted (both forms share it)',
        'node_kind': 'illustration',
        'text_verbatim': 'その後TSTを打ちます。',
        'rows': _b('c-------cc c-------cc ccc-----cc cc----cccc CCUCCCCCCC CCUUCCCCCC CCUCCCCCCC ccc-cccccc'),
    },
    {
        'id': '2.normal.after',
        'bag': 2,
        'parent': '2.normal',
        'label': 'normal, after the TST (both forms collapse to it; checked)',
        'node_kind': 'illustration',
        'after_of': '2.normal.tst',
        'rows': _b('---------- ---------- ---------- c-------cc c-------cc ccc-----cc cc----cccc ccc-cccccc'),
    },
    {
        'id': '2.normal.pc.rest',
        'bag': 3,
        'parent': '2.normal',
        'node_kind': 'commented_out',
        'label_jp': '残り55パターン',
        'page_text': '残り55パターン',
        'label': 'the 「残り55パターン」 template, inside an HTML comment (never rendered)',
        'unmatchable': 'inside an HTML comment, so not on the rendered page; it is 2.normal.after redrawn as an empty template that was never filled (checked)',
        'rows': _b('c-------cc c-------cc ccc-----cc cc----cccc ccc-cccccc'),
    },
    {
        'id': '2.normal.imperial#1',
        'bag': 3,
        'parent': '2.normal',
        'base': '2.normal.after',
        'label_jp': 'インペリアルクロス 1',
        'label': 'normal, no PC: Imperial Cross form 1 (the I at the left wall)',
        'bag_note': 'OUR READING of the bag: the page says only パフェを取れない場合',
        'group': '2.normal.imperial',
        'variant': 1,
        'condition': None,
        'unmatchable': '9 non-empty rows > ROWS = 8',
        'rows': _b('i--------- i--------- i--------- i---ss---- c--sszoocc c---zzoocc ccc-zlllcc cc---lcccc ccc-cccccc'),
    },
    {
        'id': '2.normal.imperial#2',
        'bag': 3,
        'parent': '2.normal',
        'base': '2.normal.after',
        'label_jp': 'インペリアルクロス 2',
        'label': 'normal, no PC: Imperial Cross form 2 (the I and J at columns 6-7, the O on the right-hand stack at columns 8-9)',
        'bag_note': 'OUR READING of the bag: the page says only パフェを取れない場合',
        'group': '2.normal.imperial',
        'variant': 2,
        'condition': None,
        'rows': _b('---------- ------i--- ------i-oo ----ssijoo c--sszijcc c---zzjjcc ccc-zlllcc cc---lcccc ccc-cccccc'),
    },
    {
        'id': '2.compromise',
        'bag': 2,
        'parent': None,
        'base': 'bag1.left',
        'spin': 'TST',
        'spin_board': '2.compromise.tst',
        'label_jp': '妥協ルート(2巡目) %L>%Oの場合',
        'label': 'compromise bag 2 (%T>%L%O; headed %L>%O: the held L at the right, the O and the I over it, the bag-2 L on the O)',
        'condition_verbatim': '%T>%L%Oの場合には通常系が組めないため、妥協形を組みます。',
        'condition': {'all': [{'before': ['T', 'L']}, {'before': ['T', 'O']}]},
        'condition_evidence': [
            {'before': ['T', 'L'], 'by': None,
             'note': 'the stated trigger (通常系が組めない): a choice the board does not force'},
            {'before': ['T', 'O'], 'by': None,
             'note': 'the stated trigger (通常系が組めない): a choice the board does not force'},
        ],
        'condition_note': 'OUR READING: the trigger 「%T>%L%O」 as T before L and T before O. The heading 「%L>%Oの場合」 (the only case drawn) is NOT read as a bag-2 order: the O rests on the held bag-1 L (an L placed before the O), while the bag-2 l rests on the O, so a bag-2 L dealt before the O could not be placed where it is drawn (the hold already holds the T). Named discrepancy 2.compromise:heading_vs_board',
        'heading_verbatim': '%L>%Oの場合',
        'unmatchable': '10 non-empty rows > ROWS = 8',
        'rows': _b('-------l-- -------l-- -------ll- -------ooi -jj----ooi -j----ssLi cj-zzsscLi cc--zzccLL cc-ccccccc ccc-cccccc'),
    },
    {
        'id': '2.compromise.tst',
        'bag': 2,
        'parent': '2.compromise',
        'label_jp': '妥協ルート →',
        'label': 'compromise bag 2 with the TST slot and the three cleared rows highlighted',
        'node_kind': 'illustration',
        'unmatchable': '10 non-empty rows > ROWS = 8',
        'rows': _b('-------c-- -------c-- -------cc- -------ccc -cc----ccc -c----cccc CCUCCCCCCC CCUUCCCCCC CCUCCCCCCC ccc-cccccc'),
    },
]


#: The page's PC lists, in page order. `shown` / `rest_stated` are the page's own split.
_PC4_ROWS = [
    '---------- cLLjjsscoo ccLjssccoo ccLccccccc cccjcccccc',
    '---------- cLLiiiicoo ccLlllccoo ccLccccccc ccclcccccc',
    '---------- cjjjtttcoo ccLLLtccoo ccLccccccc cccjcccccc',
]

_NORMAL_PC_ROWS = [
    'cjiiiillcc cjjjsszlcc cccsszzlcc cctttzcccc ccctcccccc',
    'cjiiiioocc cjjjssoocc cccsslllcc cctttlcccc ccctcccccc',
    'ciiiilllcc cjjjsloocc cccjssoocc cctttscccc ccctcccccc',
    'coojjtttcc coojsstlcc cccsslllcc cciiiicccc cccjcccccc',
    'ciiiizoocc cjjjzzoocc cccjzlllcc cctttlcccc ccctcccccc',
    'cjzziiiicc cjjjlloocc ccczzloocc cctttlcccc ccctcccccc',
    'coojssllcc coojjjzlcc cccsszzlcc cctttzcccc ccctcccccc',
    'coozzsllcc coojjsslcc cccjzzslcc cciiiicccc cccjcccccc',
]

#: several boards that share ONE continuation (or one heading): a list's `parent` names the group,
#: each member names it in `group`. `drawn` is the page's own count, not derived.
GROUPS = [
    {'id': '2.normal', 'heading': '通常ルート(2巡目→3巡目)', 'drawn': 2,
     'condition_verbatim': '組み分けとしては%Oが早いかどうかで2パターンで殆どの場合同じ形になります。',
     'condition': {'decided_by': ['O']},
     'condition_note': 'the family\'s split; each form\'s own heading is its condition'},
    {'id': '2.normal.imperial', 'heading': '通常ルート(2巡目→3巡目)', 'drawn': 2,
     'text_verbatim': 'また、パフェを取れない場合には下図のようにインペリアルクロスを組むことで火力を継続することができます。'},
]

LISTS = [
    {'id': '2.pc4', 'parent': 'bag1.left', 'base': 'bag1.left', 'bag': 2, 'heading': '2巡目パフェルート',
     'rows': _PC4_ROWS, 'stated_pattern_count': 3, 'shown': 3, 'rest_stated': 0, 'complete': True,
     'rate_verbatim': 'ガムシロ積みでは3パターン26.19%で4ラインパフェを狙うことができます。',
     'pc_lines': 4, 'total_lines': 4, 'total_lines_quote': '2.pc4',
     'pc_lines_note': 'a 4-line PC drawn in bag 2 on the L-held board: no spin before it'},
    {'id': '2.normal.pc', 'parent': '2.normal', 'base': '2.normal.after', 'bag': 3, 'heading': '通常ルート 3巡目',
     'rows': _NORMAL_PC_ROWS, 'stated_pattern_count': 63, 'shown': 8, 'rest_stated': 0, 'complete': False,
     'rest_in_comment': 55,
     'rate_verbatim': 'その後3巡目に99.09%の確率でパフェを取ることができます。',
     'total_lines': 8, 'total_lines_quote': 'basic.ideal',
     'pc_lines_note': 'the 5-row body plus the TST before it; the page\'s 8段 is re-derived along the base chain'},
]

#: where each list's patterns are inserted in page order: after this node
_LIST_AFTER = {'2.pc4': 'bag1.l_top', '2.normal.pc': '2.normal.after'}

#: The page's content that has no board (none: the title image is decorative, the REN is text only).
NON_BOARD: dict = {}


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


#: The order boards appear on the page (raw HTML). `--html-dir` compares a snapshot against exactly this.
PAGE_ORDER = (
    ['basic.1', 'basic.2', 'basic.3', 'bag1.left', 'bag1.right']
    + [f'2.pc4#{i}' for i in range(1, 4)]
    + ['2.normal#1', '2.normal#2', '2.normal.tst', '2.normal.after']
    + [f'2.normal.pc#{i}' for i in range(1, 9)]
    + ['2.normal.pc.rest', '2.normal.imperial#1', '2.normal.imperial#2', '2.compromise', '2.compromise.tst']
)


def _tsd_slot(rows: list[str]) -> bool:
    """The four t cells are the flat ttt-over-t shape in the body's bottom two rows: where
    2.normal.after leaves its only TSD-shaped gap. A POSITION test, unlike stick spin's shape test."""
    body = bottom(rows, 0)
    return sum(r.count('t') for r in body) == 4 and t_slot(body[-2:], 't') == 'flat'


#: the list-node flags, computed from the cells and re-checked by the gate
SLOT_FLAGS = {'has_u_slot': lambda rows: t_slot(rows) is not None,
              't_in_tsd_slot': _tsd_slot}

SLOT_FLAG_MEANING = {
    'has_u_slot': 'the pattern draws a U (T-spin slot) cell',
    't_in_tsd_slot': 'the pattern\'s four t cells are the flat ttt-over-t shape in its BOTTOM TWO body rows, where '
                     '2.normal.after leaves its only TSD-shaped gap: the TSD the page says comes first ミノ順によっては. '
                     'A position test (stick spin\'s t_flat_shape is a shape test)',
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
        'schema': 'gamushiro-routes/1',
        'source': SOURCE,
        'cross_source': CROSS_SOURCE,
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


# ── ガムシロ積み's own rules, and its half of the shared gate ───────────────────────────────────
_SPIN_LINES = {'TSS': 1, 'TSD': 2, 'TST': 3}
#: a piece named in a condition, as the letters that draw it (the held L is upper case, the T is U)
_LETTERS = {'L': 'lL', 'T': 'tU'}


def _cond_pieces(cond) -> list:
    """Every piece a condition names, through `all` / `any` / `before` / `early` / `decided_by`."""
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


def _cells(rows: list[str], letters: str) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(rows) for c, x in enumerate(row) if x in letters}


def _rests_on(rows: list[str], below: str, above: str) -> bool:
    """Some cell of piece `above` sits directly on a cell of piece `below` (gravity, not a planner)."""
    lo = _cells(rows, _LETTERS.get(below, below.lower()))
    return any((r + 1, c) in lo for r, c in _cells(rows, _LETTERS.get(above, above.lower())))


def _supports_other(rows: list[str], piece: str) -> bool:
    """Some cell of another piece sits directly on a cell of `piece`."""
    mine = _LETTERS.get(piece, piece.lower())
    lo = _cells(rows, mine)
    return any((r + 1, c) in lo for r, row in enumerate(rows) for c, x in enumerate(row)
               if x not in mine and x != EMPTY)


def _gamushiro_checks(data: dict, ctx: dict) -> tuple[list[str], set[str]]:
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

    # conditions name pieces
    b1 = data.get('bag1', {})
    conds = [b1.get('requires'), b1.get('no_hold')] + [g.get('condition') for g in groups.values()]
    conds += [n.get('condition') for n in nodes]
    if any(p not in RT.PIECES for c in conds for p in _cond_pieces(c)):
        bad.append('condition: a condition names something that is not a piece')

    # bag 1: the early pair each carries another piece; the no-hold orders by support
    req = b1.get('requires', {})
    rb = boards.get(req.get('node'))
    for p in req.get('early', []):
        if rb is None or not _supports_other(rb, p):
            bad.append(f'bag1-order: on {req.get("node")} nothing rests on the {p}, so %{p} need not be early')
    nh = b1.get('no_hold', {})
    nb = boards.get(nh.get('node'))
    for c in nh.get('all', []):
        a, b = c.get('before', ['?', '?'])
        if nb is None or not _rests_on(nb, a, b):
            bad.append(f'bag1-order: on {nh.get("node")} no {b} cell rests on a {a} cell, so %{a}>%{b} is not '
                       'what the board needs')
    if [f'%{c["before"][0]}>%{c["before"][1]}' for c in nh.get('all', [])] != b1.get('no_hold_items_verbatim'):
        bad.append('bag1-order: the no-hold orders are not the page\'s listed items')

    # bag1.l_top is bag1.left plus one L, on the cells the held L takes in 2.normal#1 and 2.compromise
    top, left = boards.get('bag1.l_top'), boards.get('bag1.left')
    if top and left:
        h = max(len(top), len(left), 10)
        lt = bottom(top, h)
        if bottom([r.replace('l', EMPTY) for r in top], h) != bottom(left, h) or len(_cells(lt, 'l')) != 4:
            bad.append('bag1-top: bag1.l_top is not bag1.left plus four l cells')
        for other in ('2.normal#1', '2.compromise'):
            if other not in boards or _cells(bottom(boards[other], h), 'L') != _cells(lt, 'l'):
                bad.append(f'bag1-top: bag1.l_top\'s L is not where {other} draws the held L')
    else:
        bad.append('bag1-top: bag1.l_top or bag1.left is missing')

    # the right bag-1 board is the left one mirrored: one shape, not two (rule `mirror-of` checks it)
    if any(n.get('mirror_of') and 'rows' in n and n['mirror_of'] in boards
           and bottom(n['rows'], RT.ROWS) == mirror(bottom(boards[n['mirror_of']], RT.ROWS)) for n in nodes):
        found.add('bag1.right:mirror')

    # a spin named on a board is the spin its spin board fires; every C row is a row it clears
    for n in nodes:
        if not n.get('spin'):
            continue
        sr = boards.get(n.get('spin_board')) if n.get('spin_board') else n.get('rows')
        if sr is None or 'U' not in ''.join(sr) or after_spin(sr)[1] != _SPIN_LINES.get(n['spin']):
            bad.append(f'spin: {n["id"]} names a {n["spin"]} but its U slot clears '
                       f'{None if sr is None else after_spin(sr)[1]} rows')
    for n in nodes:
        rows = n.get('rows')
        if not rows or 'C' not in ''.join(rows):
            continue
        muted = [i for i, r in enumerate(rows) if 'C' in r]
        full = [i for i, r in enumerate(r.replace('U', 't') for r in rows) if EMPTY not in r]
        if muted != full or any(ch not in 'CU' for i in muted for ch in rows[i]):
            bad.append(f'muted: {n["id"]} draws C rows {muted} where its spin clears rows {full}')

    # 基本形 2 draws its TST slot exactly where the shared spin board does
    b2 = next((b for b in data.get('basic_form', []) if b['id'] == 'basic.2'), None)
    if b2 is None or '2.normal.tst' not in boards or (
            _cells(bottom(b2['rows'], RT.ROWS), 'U') != _cells(bottom(boards['2.normal.tst'], RT.ROWS), 'U')):
        bad.append('basic-spin: basic.2\'s U cells are not 2.normal.tst\'s')

    # node conditions: every order has its evidence, and the evidence holds on the board
    for n in nodes:
        cond, ev = n.get('condition'), n.get('condition_evidence')
        if not cond:
            continue
        pairs = [c.get('before') for c in cond.get('all', [])]
        if [e.get('before') for e in ev or []] != pairs:
            bad.append(f'order: {n["id"]} condition_evidence does not cover its condition, pair for pair')
            continue
        rows = n['rows']
        for e in ev:
            a, b = e['before']
            if e['by'] == 'support':
                ok = _rests_on(rows, a, b)
            elif e['by'] == 'spin_rows':
                sb = boards.get(n.get('spin_board'), rows)
                h = max(len(sb), len(rows))
                cleared = {i for i, r in enumerate(bottom([x.replace('U', 't') for x in sb], h)) if EMPTY not in r}
                ok = b == 'T' and any(r in cleared for r, _ in _cells(bottom(rows, h), _LETTERS.get(a, a.lower())))
            else:
                ok = bool(e.get('note'))
            if not ok:
                bad.append(f'order: {n["id"]} %{a}>%{b} ({e["by"]}) does not hold on its board')

    # a group's forms share ONE occupancy where they share a spin board; no per-form condition is a gap
    for g in groups.values():
        members = [n for n in nodes if n.get('group') == g['id'] and 'rows' in n]
        if len({n.get('spin_board') for n in members}) == 1 and members[0].get('spin_board') and len(
                {tuple(RT.occ(bottom(n['rows'], RT.ROWS + 2))) for n in members}) != 1:
            bad.append(f'group: the forms of {g["id"]} no longer share one occupancy')
        if members and all(n.get('condition') is None for n in members):
            found.add(f'{g["id"]}:no_conditions')

    # a list's stated total line count is re-derived along its base chain: the body, plus every spin
    # from the PC's base back to bag 1
    for lst in data.get('lists', []):
        pats = [n for n in nodes if n.get('list') == lst['id']]
        if lst.get('total_lines') is None or not pats:
            continue
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
            bad.append(f'lines: {lst["id"]} clears {total} lines over its line, the page says {lst["total_lines"]}')
        qv = quotes.get(lst.get('total_lines_quote'), {}).get('verbatim', '')
        if f'{lst["total_lines"]}段' not in qv and f'{lst["total_lines"]}ライン' not in qv:
            bad.append(f'lines: quote {lst.get("total_lines_quote")!r} does not state {lst["total_lines"]} lines '
                       f'for {lst["id"]}')

    # the commented-out 残り55 block: its board is the after-TST board, an unfilled template
    rest = by_id.get('2.normal.pc.rest')
    after = boards.get('2.normal.after')
    if rest and after and rest.get('node_kind') == 'commented_out' and 'unmatchable' in rest and (
            bottom(rest.get('rows', []), 0) == bottom(after, 0)) and (
            f'残り{next((x.get("rest_in_comment") for x in data.get("lists", []) if x["id"] == "2.normal.pc"), "?")}パターン'
            == quotes.get('2.normal.pc.rest', {}).get('verbatim')):
        found.add('2.normal.pc:rest_commented_out')

    # the 妥協 heading 「%L>%O」 holds only through the held L: the bag-2 l rests on the O
    cp = by_id.get('2.compromise')
    if cp and cp.get('heading_verbatim') == '%L>%Oの場合' and 'rows' in cp and (
            _rests_on(cp['rows'], 'O', 'l') and any(
                (r + 1, c) in _cells(cp['rows'], 'L') for r, c in _cells(cp['rows'], 'o'))) and not any(
            c.get('before') == ['L', 'O'] for c in (cp.get('condition') or {}).get('all', [])):
        found.add('2.compromise:heading_vs_board')

    # the 基本形 sentence names a 中開け4列REN derivation the page does not draw
    if '中開け4列REN' in quotes.get('basic.ideal', {}).get('verbatim', '') and not any(
            'ren' in n['id'] for n in nodes):
        found.add('overview:ren_not_drawn')

    # 「山岳積み2号と%Iの位置がずれた形」 against harddrop's Mountainous Stacking 2 field: delete the I's
    # column from each and what is left is equal, letter for letter (as drawn or mirrored)
    m2 = b1.get('mountainous2', {})
    wiki = json.loads(WIKI.read_text())
    m2f = [f['rows'] for o in wiki['openers'] if o['key'] == 'mountainous_2' for f in o['fields']]
    ic, mc = m2.get('i_column'), m2.get('mountainous2_i_column')
    if left is None or ic is None or mc is None or m2.get('quote') not in quotes or \
            '山岳積み2号' not in quotes[m2['quote']]['verbatim']:
        bad.append('i-shift: the 山岳積み2号 relation is not recorded against a quote')
    else:
        ours = [r.replace('-', '.').upper() for r in bottom(left, 0)]

        def cut(rows, col):
            return [r[:col] + r[col + 1:] for r in rows]

        def i_col(rows, col):
            return [r[col] for r in rows if r[col] != '.'] == ['I'] * 4 and sum(r.count('I') for r in rows) == 4
        hit = any(i_col(ours, ic) and i_col(f, mc) and cut(ours, ic) == cut(f, mc) for f in m2f)
        if not hit:
            bad.append(f'i-shift: bag1.left less its column {ic} is not harddrop\'s Mountainous Stacking 2 '
                       f'field less its column {mc}')
    # and 山岳積み2号's own page says the same of this one (its transcription quotes it)
    m2q = {q['id']: q['verbatim'] for q in json.loads(MOUNTAINOUS2.read_text())['quotes']}
    if 'ガムシロ積みと%Iの位置がずれた形' not in m2q.get('overview.gamushiro', ''):
        bad.append('i-shift: 山岳積み2号\'s transcription no longer quotes its own ガムシロ積み sentence')

    # harddrop files the opener under Triple Double openers; the route fires its TST, then a TSD
    cat = (data.get('cross_source') or {}).get('category', {})
    members = wiki.get('triple_double_category', {}).get('members', [])
    if cat.get('member') not in members or wiki['triple_double_category'].get('name') != cat.get('name'):
        bad.append(f'category: {cat.get("member")!r} is not a member of harddrop\'s {cat.get("name")!r} '
                   '(wiki-openers.json)')
    if not (all(n.get('spin') == 'TST' for n in nodes if n.get('group') == '2.normal')
            and any(n.get('t_in_tsd_slot') for n in nodes if n.get('list') == '2.normal.pc')):
        bad.append('category: the 通常 route no longer fires a TST and then a TSD (a Triple Double opener)')
    return bad, found


SPEC = RT.TranscriptionSpec(
    out=OUT, build=build, alphabet=ALPHABET, non_board=NON_BOARD,
    harddrop=None,
    harddrop_page={'nodes': ['bag1.left', 'bag1.l_top']},
    board_kinds=frozenset({'illustration', 'commented_out'}),
    pc_lines=8, prior_letters='',
    upper_groups={'L': 'separate'},
    slot_flags=SLOT_FLAGS, occupancy_class_parents=1, extra_checks=_gamushiro_checks)


def verify(data: dict) -> list[str]:
    return RT.verify(data, SPEC)


def drift(data: dict) -> list[str]:
    return RT.drift(data, SPEC)


# ── selftest ───────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    """A gate nothing can fail is decorative. Plant one defect per rule, each in a named ガムシロ積み id."""

    def drop_pattern(d):
        d['nodes'] = [n for n in d['nodes'] if n['id'] != '2.normal.pc#8']

    def break_mirror(d):
        setcell(node(d, 'bag1.right')['rows'], 2, 9, '-')            # one z cell of the mirror

    def shift_left(d):
        n = node(d, 'bag1.left')
        n['rows'] = ['-' + r[:-1] for r in n['rows']]

    def field_off(d):
        f = d['cross_source']['fields'][2]
        f[0] = '.......L..'                                             # harddrop's L moved one column

    def top_off(d):
        for rows in (node(d, 'bag1.l_top')['rows'], d['basic_form'][0]['rows']):
            setcell(rows, 3, 8, '-')
            setcell(rows, 3, 7, 'l')                                   # the L leans one column left

    def ghost_group(d):
        node(d, '2.normal#2')['group'] = '2.normal.nowhere'

    def bad_cell(d):
        setcell(node(d, '2.normal.imperial#1')['rows'], 0, 9, 'p')

    def flag_flip(d):
        n = node(d, '2.normal.pc#4')
        n['t_in_tsd_slot'] = not n['t_in_tsd_slot']

    def drop_discrepancy(d):
        d['known_discrepancies'] = [x for x in d['known_discrepancies'] if x['id'] != '2.normal.pc:rest_commented_out']

    def recolour(d):
        setcell(node(d, '2.normal#1')['rows'], 0, 0, 'o')              # an i cell drawn as o

    def dup_form(d):
        node(d, '2.normal#2')['rows'] = list(node(d, '2.normal#1')['rows'])

    def basic_off(d):
        setcell(d['basic_form'][2]['rows'], 3, 1, 'i')                # basic.3's j drawn i

    def tall(d):
        node(d, '2.normal#1')['rows'].insert(0, 'i---------')

    def no_reason(d):
        node(d, '2.normal.imperial#2')['unmatchable'] = ''

    def c_cells(d):
        setcell(node(d, '2.normal.pc#2')['rows'], 0, 1, 'c')            # a c where 2.normal.after has none

    def wrong_after(d):
        node(d, '2.normal.after')['after_of'] = '2.compromise.tst'

    def pc4_short(d):
        n = node(d, '2.pc4#2')
        n['rows'] = n['rows'][:-1]                                      # a 3-line PC drawn

    def wrong_spin(d):
        node(d, '2.compromise')['spin'] = 'TSD'

    def muted_row(d):
        setcell(node(d, '2.normal.tst')['rows'], 3, 0, 'C')            # a C outside the cleared rows

    def basic_spin(d):
        b = d['basic_form'][1]['rows']
        setcell(b, 6, 2, '-')
        setcell(b, 7, 3, 'U')                                           # the 基本形 slot one row down

    def total_lines(d):
        next(x for x in d['lists'] if x['id'] == '2.normal.pc')['total_lines'] = 9

    def unquoted(d):
        node(d, '2.compromise')['condition_verbatim'] = '%T>%Oの場合には通常系が組めないため、妥協形を組みます。'

    def cond_piece(d):
        d['bag1']['requires']['early'] = ['J', 'X']

    def bag1_order(d):
        d['bag1']['no_hold']['all'][0]['before'] = ['S', 'J']

    def early_o(d):
        d['bag1']['requires']['early'] = ['J', 'O']                   # nothing rests on the bag-1 O

    def order(d):
        node(d, '2.normal#1')['condition_evidence'][0]['before'] = ['O', 'L']
        node(d, '2.normal#1')['condition']['all'][0]['before'] = ['O', 'L']

    def order_spin(d):
        n = node(d, '2.normal#1')                                      # form 1's O fills no TST row
        n['condition']['all'][0]['before'] = ['O', 'T']
        n['condition_evidence'][0] = {'before': ['O', 'T'], 'by': 'spin_rows'}

    def order_uncovered(d):
        node(d, '2.normal#2')['condition_evidence'].pop()

    def i_shift(d):
        d['bag1']['mountainous2']['i_column'] = 6

    def category(d):
        d['cross_source']['category']['member'] = 'Gamushiro'

    def rest_filled(d):
        setcell(node(d, '2.normal.pc.rest')['rows'], 0, 1, 'i')

    def ren_drawn(d):
        node(d, '2.normal.imperial#2')['id'] = '2.normal.ren'

    def group_occ(d):
        setcell(node(d, '2.normal#2')['rows'], 0, 8, '-')              # form 2's top cell gone

    def heading_as_order(d):
        n = node(d, '2.compromise')                                    # the heading read as a bag-2 order
        n['condition']['all'].append({'before': ['L', 'O']})
        n['condition_evidence'].append({'before': ['L', 'O'], 'by': 'support'})

    def no_provenance(d):
        d['cross_source']['oldid'] = None

    mutants = [
        (drop_pattern, 'a dropped PC pattern', 'list-count:'),
        (break_mirror, 'the right board no longer the left one mirrored', 'mirror-of:'),
        (shift_left, 'bag1.left shifted one column', 'harddrop-page:'),
        (field_off, 'one harddrop field moved off', 'harddrop-page:'),
        (no_provenance, 'the harddrop page without its oldid', 'harddrop-page:'),
        (top_off, 'the 7-lock L moved off the held-L cells', 'bag1-top:'),
        (ghost_group, 'a group no node declares', 'grammar:'),
        (bad_cell, 'a cell outside the alphabet', 'grammar:'),
        (flag_flip, 'a t_in_tsd_slot flag flipped', 'grammar:'),
        (drop_discrepancy, 'a dropped known discrepancy', 'discrepancy:'),
        (recolour, 'one cell of a 2.normal form recoloured', 'discrepancy:'),
        (dup_form, 'two 2.normal forms made equal by colour', 'distinct:'),
        (basic_off, 'a 基本形 board off its node', 'basic-form:'),
        (tall, 'a 9-row board not marked unmatchable', 'grammar:'),
        (no_reason, 'an unmatchable node with no reason', 'grammar:'),
        (c_cells, 'a c cell where the TST leaves none', 'c-cells:'),
        (wrong_after, 'normal.after read off the wrong spin', 'after-of:'),
        (pc4_short, 'a bag-2 PC that is not 4 lines', 'pc:'),
        (wrong_spin, 'a TST board named a TSD', 'spin:'),
        (muted_row, 'a C cell in a row the TST does not clear', 'muted:'),
        (basic_spin, 'the 基本形 TST slot off the spin board', 'basic-spin:'),
        (total_lines, 'the 8段 total misstated', 'lines:'),
        (unquoted, 'a verbatim field that is not on the page', 'verbatim:'),
        (cond_piece, 'a condition naming a non-piece', 'condition:'),
        (bag1_order, 'a no-hold order reversed', 'bag1-order:'),
        (early_o, 'an early piece nothing rests on', 'bag1-order:'),
        (order, 'a bag-2 order the board does not force', 'order:'),
        (order_spin, 'an O>T order on a form whose O fills no TST row', 'order:'),
        (order_uncovered, 'a condition order with no evidence', 'order:'),
        (i_shift, 'the 山岳積み2号 I column misplaced', 'i-shift:'),
        (category, 'a category member harddrop does not list', 'category:'),
        (rest_filled, 'the commented-out template filled in', 'discrepancy:'),
        (ren_drawn, 'a REN node appearing makes the REN gap unmeasured', 'discrepancy:'),
        (group_occ, 'the two 通常 forms no longer one occupancy', 'group:'),
        (heading_as_order, 'the 妥協 heading read as a bag-2 order', 'discrepancy:'),
    ]
    spec_mutants = [
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'harddrop_page': {'nodes': ['bag1.left']}}),
         'the 7-lock node dropped (two harddrop fields left unmatched)', 'harddrop-page:'),
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'harddrop_page': {'nodes': ['bag1.left', '2.normal#1']}}),
         'a bag-2 board named against the first-bag fields', 'harddrop-page:'),
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'harddrop_page': None}),
         'no cross-source at all', 'harddrop:'),
    ]
    return RT.run_selftest(SPEC, mutants, {'board': ('cccsslllcc', 'ccc-slllcc'),
                                           'text': ('残り55パターン', '残り54パターン'),
                                           'hand_edit': '2.compromise', 'quote': '2.normal.pc.tsd'},
                           spec_mutants)


def main() -> int:
    return RT.main(SPEC, selftest, __doc__)


if __name__ == '__main__':
    raise SystemExit(main())

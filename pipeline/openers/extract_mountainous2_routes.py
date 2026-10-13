"""Transcribe shiwehi.com's 山岳積み2号 (Mountainous Stacking 2) route page into `mountainous2-routes.json`.

    python3 -m pipeline.openers.extract_mountainous2_routes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_mountainous2_routes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_mountainous2_routes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_mountainous2_routes --html-dir <dir> --write  # ...and rewrite

The third opener ROUTE page, after 迷走砲 and はちみつ砲: one bag-1 shape (the L stood on its end at
the right of the stack, or the J mirrored), a bag-2 four-line Perfect Clear list on the L-held
6-lock board, three bag-2 families — 理想形 (one form), 通常形 (three forms sharing one
occupancy) and 妥協系 — each firing a TST, the 8-line PC lists under the first two, and under 妥協系
a 火力重視 3-4巡目 line (with the page's hold-L and J/L cycle fragments) and a 5-bag 14-line PC line.
Every rule the openers share is `route_transcription.py`'s, once; this file holds the
transcription, its `SPEC` and the rules only this page needs (`_mountainous2_checks`).

WHERE THE TRANSCRIPTION COMES FROM, AND WHY THE SNAPSHOT IS HTML HERE. `NODES` below is a literal,
hand-checked transcription. Unlike the other two pages, this one was fetched as RAW HTML with plain
curl through the session proxy: the server omits its Let's Encrypt YE2 intermediate, so the fetch
supplied that intermediate as an extra CA file (TLS verification stayed on). The two earlier
transcriptions hashed a MARKDOWN rendering (MCP web_fetch) because curl got a 403 there; this one
hashes the page's own bytes. The two hashes therefore name different kinds of object and are not
comparable: a markdown hash moves when the renderer changes, an HTML hash moves when ANY byte of the
page does (an ad slot, a sidebar link). Either way a moved hash means "read the board diff", which
`--html-dir` prints. The page is not committed; CI cannot fetch it.

The boards are plain text inside `<div class="tetTableText">`, one row per line, drawn by the site's
`column-exp.js` (its colour map is recorded in `source.renderer`). Six of those divs are NOT 10-wide
boards: the page's 4-wide and 3-wide cycle diagrams (`haba4` / `haba3`, written on one line). They
are kept as `cycle_fragment` nodes with their own rows, never as boards, and `_mountainous2_checks`
places the first of each set back inside the board it is drawn from.

WHAT IS AN INFERENCE, flagged in the JSON rather than in prose only:

  * upper-case `L` has no legend on the page. It is read as the bag-1 L, NOT stood on the tower:
    held into bag 2 (harddrop: "the L piece is held until the second bag"). Rule 3 checks the
    reading — the boards carrying an `L` have `c` cells exactly the L-less 6-lock board, which is
    harddrop's Mountainous Stacking 2 field cell for cell (rule 2) — and a board that draws both
    `L` and `l` (2.pc4#2, 2.normal#3) shows the `l` is the bag-2 one.
  * `bag1.l_hold` (that 6-lock board) is DERIVED: the page draws only the 7-lock board with the L on
    its end; the gate checks the derivation is exactly that board less its four `l` cells.
  * "%S%O" / "%O%S" are read as ORDERS (S before O for 理想形, O before S for 妥協系), since read as
    sets the two triggers would be the same; "%I%L or %O%J が早い" is read as two early PAIRS.

THE TERMS are the same shiwehi.com terms page 迷走砲 links to, and are imported from that
transcription rather than copied (read 2026-10-11 there; not re-read for this page).
"""
from __future__ import annotations

import copy
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS
from pipeline.openers.route_transcription import EMPTY, after_spin, bottom, mirror, node, setcell, t_slot

HERE = Path(__file__).resolve().parent
OUT = HERE / 'mountainous2-routes.json'

ALPHABET = frozenset('-ijlostzcUL')


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/mountainous2.php',
    'title': '山岳積み2号(Mountainous Stacking 2)',
    'updated': '2024-10-16',
    'created': '2021-12-30',
    'fetched': '2026-10-12',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle '
                    'that adds the Let\'s Encrypt YE2 intermediate (fetched from '
                    'letsencrypt.org/certs/gen-y/int-ye2.pem) because shiwehi.com omits it from its '
                    'chain. The snapshot is the page\'s raw HTML, byte for byte; every board is plain '
                    'text in it, 52 ten-wide boards in page order plus six cycle fragments. NOT the '
                    'markdown rendering the 迷走砲 and はちみつ砲 transcriptions hashed (MCP web_fetch, '
                    'because curl got HTTP 403 there): the two kinds of hash are not comparable.',
    'snapshot_file': 'mountainous2.html',
    'snapshot_sha256': 'e7e7107e089e76d40555b114f6eee654caa4e812d1696d9372156a322602c44f',
    'snapshot_bytes': 38268,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable '
                     'in CI: the page is not committed and cannot be fetched there. Re-check with '
                     '--html-dir after any refetch; an HTML hash moves with ANY byte of the page (ads, '
                     'sidebar, a date), so a moved hash means "read the board diff", not "the boards '
                     'changed". Sentences are compared against the page with its tags dropped.',
    'renderer': {
        'url': 'https://shiwehi.com/tetris/mutual/column-exp.js?date=20210408',
        'read': '2026-10-12',
        'sha256': '95c431a4147f9c30fc0e1bae935e6af6f5669c3d2fa1edfc388848e69ab62570',
        'colorMap_used': {'c': '#a3a3a3', 'U': '#c8a6ff with a #8400ff radial dot',
                          'L': '#d8904d (muted l)', '-': '#000000'},
        'rows': 'textContent split on whitespace, one row per token; a first row 10 wide gets class '
                'haba10, anything else (the haba4 / haba3 cycle diagrams) is drawn at its own width',
        'mirror_button': 'body.reversed swaps j<->l, s<->z (and upper case) and reverses nothing else in '
                         'the char map; the canvas is redrawn mirrored',
    },
    'decorative_images': ['山岳積み2号(Mountainous Stacking 2)タイトル画像'],
    'references_listed': ['https://tetristemplate.info/sangaku2/',
                          'https://harddrop.com/wiki/Mountainous_Stacking#Mountainous_Stacking_2',
                          'https://x.com/dot_TIZ/status/1804861229598667074'],
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ, align at the BOTTOM row',
    '-': 'empty',
    'i o t s z j l': 'a cell of that piece',
    'c': 'a cell filled before this diagram (earlier bags), grey',
    'L': 'the bag-1 L, not stood on the tower but held into bag 2, drawn in a muted L colour (page legend: none; OUR READING, consistent with harddrop\'s "the L piece is held until the second bag")',
    'U': 'the T-spin slot',
    'cycle fragment': 'a 4-wide (haba4) or 3-wide (haba3) diagram of one region; its c means "not one of these pieces", not "filled" (all four O/S/Z cycles draw c in their corners, over an empty board cell in cycle 1)',
    '%X': "the X piece; '%J>%Z' means J before Z; '%S%O' is OUR READING as S before O",
}


#: Every sentence the transcription leans on, verbatim. `--html-dir` finds each on the page (tags
#: dropped), and every `*_verbatim` field below must be one of these (`_mountainous2_checks`).
QUOTES = [
    {'id': 'overview.intro', 'figure': None,
     'verbatim': 'という、積み込み→TSTから8ラインパフェを狙うor中開けRENに派生する開幕テンプレについて紹介していきます。'},
    {'id': 'overview.pc4_rare', 'figure': None, 'verbatim': 'また、稀に4ラインパフェを狙うこともできます。'},
    {'id': 'overview.gamushiro', 'figure': None, 'verbatim': 'ガムシロ積みと%Iの位置がずれた形になります。'},
    {'id': 'overview.setup_rate', 'figure': '66.67% / 100%',
     'verbatim': 'セットアップ率は片側で66.67%、左右反転も含めると100%となりますが、2巡目にミノ順による組み分けが発生します。'},
    {'id': 'overview.bag2_three', 'figure': '3パターン',
     'verbatim': '2巡目にパフェ派生に行こうと思うと派生が多いため、覚える量が多い。(このページでは2巡目は3パターンのみ紹介)',
     'note': 'in context (「2巡目にパフェ派生に行こうと思うと…」) the three are the bag-2 Perfect Clear patterns, i.e. the 2.pc4 list, which the page also counts as 3パターン; the page also has three bag-2 board families, which this sentence does not count'},
    {'id': 'bag1.requires', 'figure': None,
     'verbatim': '1巡目の組み方は上図の通りで、%J>%Zもしくは%L%Sが早いと組むことができます。'},
    {'id': 'bag1.also', 'figure': None,
     'verbatim': 'また、%O%S%Zが早い時も%J%Lのどちらが早いかを判断することでソフドロ無しで組むことができます。'},
    {'id': 'bag1.side', 'figure': None, 'verbatim': '%J%Lのどちらが早いかによって左右を決めると良いでしょう。'},
    {'id': 'bag1.mirror_note', 'figure': None,
     'verbatim': '(ここでは、以下左のパターンで説明していきますが、右下にある反転ボタンを押すことで左右反転の図を見ることができます。)'},
    {'id': 'bag1.l_left_omitted', 'figure': None,
     'verbatim': '%Lを左に置くパフェ率の高い派生もありますが、このページでは省略します。'},
    {'id': '2.pc4', 'figure': '3パターン26.19%',
     'verbatim': '山岳積み2号では3パターン26.19%で4ラインパフェを狙うことができます。'},
    {'id': '2.ideal', 'figure': None, 'verbatim': '2巡目が%S%Oの場合、下図のように理想形を組むことができます。'},
    {'id': '2.ideal.pc', 'figure': '14パターン：パフェ率97.94%',
     'verbatim': '3巡目はTSDを打ちつつパフェを狙います。(14パターン：パフェ率97.94%)'},
    {'id': 'after_pc', 'figure': None, 'verbatim': '8段パフェを取った後はDPCや3回目パフェを狙うことができます。',
     'note': 'drawn under both 8-line PC lists'},
    {'id': '2.ideal.fire', 'figure': '5巡パフェ(14段パフェ)',
     'verbatim': '%Tが遅い等でパフェを取らない場合等には、下図のように組むことで火力を維持しつつ5巡パフェ(14段パフェ)を狙うことができます。'},
    {'id': '2.normal', 'figure': None, 'verbatim': '2巡目に%I%Lor%O%Jが早い場合には、通常形を組むことができます。'},
    {'id': '2.normal.pc', 'figure': '8パターン：パフェ率96.90%',
     'verbatim': '3巡目はTSDを打ちつつパフェを狙います。(8パターン：パフェ率96.90%)'},
    {'id': '2.compromise', 'figure': None, 'verbatim': '%O%Sの場合には、妥協系を組むことになります。'},
    {'id': '2.compromise.fire34', 'figure': None, 'verbatim': '火力重視で安定した地形にする組み方はこちら。'},
    {'id': '2.compromise.fire34.cycle', 'figure': '100%',
     'verbatim': '3巡目は%Lをホールドしつつ、%O%S%Z循環で100%組むことができます。'},
    {'id': '2.compromise.fire34.bag4.cycle', 'figure': '100%',
     'verbatim': '4巡目は上図のように%J%L循環で100%組むことができます。'},
    {'id': '2.compromise.fire5', 'figure': '5巡パフェ(14段パフェ)',
     'verbatim': 'もしくは、下図のように組むことで火力を維持しつつ5巡パフェ(14段パフェ)を狙うことができます。'},
    {'id': '2.compromise.fire5.pc', 'figure': '6パターン：パフェ率100%',
     'verbatim': '5巡目はパフェを狙います。(6パターン：パフェ率100%)'},
]


BAG1 = {
    'requires_verbatim': '1巡目の組み方は上図の通りで、%J>%Zもしくは%L%Sが早いと組むことができます。',
    'requires': {'any': [{'before': ['J', 'Z']}, {'early': ['L', 'S']}], 'illustrative': True},
    'requires_note': 'a SUFFICIENT condition, not the trigger: the next sentence widens it (%O%S%Z early also '
                     'works), and the page states 66.67% one side / 100% with the mirror',
    'also_verbatim': 'また、%O%S%Zが早い時も%J%Lのどちらが早いかを判断することでソフドロ無しで組むことができます。',
    'also': {'early': ['O', 'S', 'Z'], 'then_decided_by': ['J', 'L']},
    'side_verbatim': '%J%Lのどちらが早いかによって左右を決めると良いでしょう。',
    'side': {'decided_by': ['J', 'L'], 'which': None},
    'side_note': 'the page does not say which side goes with which piece',
    'mirror_note_verbatim': '(ここでは、以下左のパターンで説明していきますが、右下にある反転ボタンを押すことで左右反転の図を見ることができます。)',
    'omitted_verbatim': '%Lを左に置くパフェ率の高い派生もありますが、このページでは省略します。',
}


BASIC_FORM = [
    {
        'id': 'basic.1',
        'same_as': 'bag1.l_top',
        'rows': _b('---------- ---------- ---------- ------l--- ------l--- is----ll-- iss----t-- ijs-zzttoo ijjj-zztoo'),
        'canvas': 'tetCanvas0',
    },
    {
        'id': 'basic.2',
        'same_as': '2.ideal',
        'rows': _b('---------- ---------- jjoo------ jsoo--c--i jss---clli ccsUzzccli cccUUzzcli cccUcccccc cccc-ccccc'),
        'canvas': 'tetCanvas1',
    },
    {
        'id': 'basic.3',
        'same_as': '2.ideal.pc#3',
        'differs': 'the TSD T is drawn U instead of t',
        'recolour': {'t': 'U'},
        'rows': _b('---------- ---------- ---------- ---------- iiiijjzlll ccccjzzlss ccccjzcssc cccUUUcccc ccccUccccc'),
        'canvas': 'tetCanvas2',
    },
]


KNOWN_DISCREPANCIES = [
    {
        'id': 'bag1.right:mirror',
        'what': 'the right bag-1 board is the left one mirrored with J<->L, S<->Z (cell for cell), so the page has ONE bag-1 shape, not two',
    },
    {
        'id': '2.ideal.pc:no_tsd',
        'what': 'the sentence says 3巡目はTSDを打ちつつ, but pc#8-#14 do not put the T in the TSD slot (ccctttcccc / cccctccccc): pc#8 draws no T at all, pc#9-#14 draw it elsewhere (across a cleared row)',
    },
    {
        'id': '2.normal.pc:no_tsd',
        'what': 'the same sentence over the 通常形 list, and pc#4-#8 do not put the T in the TSD slot: pc#7 draws no T at all, the others draw it elsewhere',
    },
    {
        'id': '2.normal:no_conditions',
        'what': 'three 通常形 forms under one stated trigger (%I%L or %O%J early) and no condition saying which form to build',
    },
    {
        'id': '2.compromise.fire5:no_conditions',
        'what': 'two 5巡パフェ bag-3 forms and no condition saying which',
    },
    {
        'id': '2.compromise.fire5.bag4:no_conditions',
        'what': 'two 5巡パフェ bag-4 forms and no condition saying which',
    },
    {
        'id': 'overview:ren_not_drawn',
        'what': 'the introduction names a 中開けREN derivation; the page draws none',
    },
]


#: Every node, in page order (the PC patterns are inserted after their `after` boards by `build`).
NODES: list[dict] = [
    {
        'id': 'overview.derivation_map',
        'bag': 0,
        'parent': None,
        'node_kind': 'image_only',
        'label_jp': '山岳積み2号の組み方概略図(簡単ver.)',
        'page_text': '山岳積み2号の組み方概要図(簡単ver.)',
        'image': 'img/mountainous21.png',
        'note': 'the overview diagram (image); the heading says 概略図, the image alt (page_text) 概要図',
    },
    {
        'id': 'overview.video',
        'bag': 0,
        'parent': None,
        'node_kind': 'video_only',
        'label_jp': '解説動画',
        'page_text': 'https://www.youtube.com/embed/V_L3uo3eP9I',
        'note': 'an embedded explanation video (posted by くぷりん, shown with permission per the page); no board',
    },
    {
        'id': 'bag1.l_top',
        'bag': 1,
        'parent': None,
        'locks': 7,
        'label_jp': '1巡目とミノ順',
        'label_jp_note': 'the section heading; the page draws this board with no caption of its own (its sentence calls it 以下左のパターン)',
        'label': "bag 1, the L stood on its end at the right (the page's left pattern)",
        'rows': _b('---------- ------l--- ------l--- is----ll-- iss----t-- ijs-zzttoo ijjj-zztoo'),
    },
    {
        'id': 'bag1.j_top',
        'bag': 1,
        'parent': None,
        'locks': 7,
        'label_jp': '1巡目とミノ順',
        'label_jp_note': 'the section heading; the page draws this board with no caption of its own',
        'label': "bag 1, mirrored: the J stood on its end at the left (the page's right pattern)",
        'mirror_of': 'bag1.l_top',
        'classifier_note': 'exactly bag1.l_top mirrored with J<->L and S<->Z swapped (checked cell for cell); a mirror-aware classifier must treat it as the SAME node, not a second branch',
        'rows': _b('---------- ---j------ ---j------ --jj----zi --t----zzi oottss-zli ootss-llli'),
    },
    {
        'id': 'bag1.l_hold',
        'bag': 1,
        'parent': None,
        'locks': 6,
        'derived': True,
        'derived_from': 'bag1.l_top',
        'derivation': 'bag1.l_top less its four l cells (checked): the 6-lock board with the L held, which is harddrop\'s Mountainous Stacking 2 field cell for cell (rule 2). The page never draws it alone; it is the c cells of every board that draws the upper-case L',
        'label': 'bag 1 with the L held (harddrop\'s field; not drawn alone on the page)',
        'rows': _b('is-------- iss----t-- ijs-zzttoo ijjj-zztoo'),
    },
    {
        'id': '2.ideal',
        'bag': 2,
        'parent': None,
        'base': 'bag1.l_top',
        'spin': 'TST',
        'label_jp': '理想形 2巡目',
        'label': 'ideal bag 2',
        'condition_verbatim': '2巡目が%S%Oの場合、下図のように理想形を組むことができます。',
        'condition': {'all': [{'before': ['S', 'O']}]},
        'condition_note': "OUR READING of 「%S%O」 as S before O: 妥協系 is triggered by 「%O%S」, and read as a set the two would be the same trigger",
        'rows': _b('---------- jjoo------ jsoo--c--i jss---clli ccsUzzccli cccUUzzcli cccUcccccc cccc-ccccc'),
    },
    {
        'id': '2.ideal.after',
        'bag': 2,
        'parent': '2.ideal',
        'label': 'ideal, after the TST',
        'node_kind': 'illustration',
        'after_of': '2.ideal',
        'rows': _b('---------- ---------- ---------- ---------- cccc------ cccc--c--c ccc---cccc cccc-ccccc'),
    },
    {
        'id': '2.ideal.fire.pc5_image',
        'bag': 3,
        'parent': '2.ideal',
        'node_kind': 'image_only',
        'label_jp': 'TDパフェ系テンプレ TSDからの5巡パフェ派生',
        'page_text': 'TDパフェ系テンプレ TSDからの5巡パフェ派生',
        'image': 'img/td35matome1.png',
        'text_verbatim': '%Tが遅い等でパフェを取らない場合等には、下図のように組むことで火力を維持しつつ5巡パフェ(14段パフェ)を狙うことができます。',
        'note': 'a generic TD-PC-family chart (the same image はちみつ砲 shows), not specific to this opener',
    },
    {
        'id': '2.normal#1',
        'bag': 2,
        'parent': None,
        'base': 'bag1.l_top',
        'spin': 'TST',
        'label_jp': '通常形 2巡目 1',
        'label': 'normal bag 2, form 1 (O and J on the left)',
        'group': '2.normal',
        'variant': 1,
        'condition': None,
        'rows': _b('---------- --------ss oojj--cssi ooj---clli ccjUzzccli cccUUzzcli cccUcccccc cccc-ccccc'),
    },
    {
        'id': '2.normal#2',
        'bag': 2,
        'parent': None,
        'base': 'bag1.l_top',
        'spin': 'TST',
        'label_jp': '通常形 2巡目 2',
        'label': 'normal bag 2, form 2 (I and J on the left, O on the right)',
        'group': '2.normal',
        'variant': 2,
        'condition': None,
        'rows': _b('---------- --------ss iiii--cssl jjj---clll ccjUzzccoo cccUUzzcoo cccUcccccc cccc-ccccc'),
    },
    {
        'id': '2.normal#3',
        'bag': 2,
        'parent': None,
        'base': 'bag1.l_hold',
        'spin': 'TST',
        'label_jp': '通常形 2巡目 3',
        'label': 'normal bag 2, form 3 (the held L placed at the right wall; the bag-2 L stands where the bag-1 L stood on 2.normal#1, sharing 2 of its 4 cells)',
        'group': '2.normal',
        'variant': 3,
        'condition': None,
        'base_note': 'the only bag-2 form on the L-held board: its c cells are bag1.l_hold, not bag1.l_top (rule 3)',
        'rows': _b('---------- --------LL iiii--lllL jjj---lssL ccjUzzssoo cccUUzzcoo cccUcccccc cccc-ccccc'),
    },
    {
        'id': '2.normal.after',
        'bag': 2,
        'parent': '2.normal',
        'label': 'normal, after the TST (all three forms collapse to it; checked)',
        'node_kind': 'illustration',
        'after_of': '2.normal#1',
        'rows': _b('---------- ---------- ---------- ---------- --------cc cccc--cccc ccc---cccc cccc-ccccc'),
    },
    {
        'id': '2.compromise',
        'bag': 2,
        'parent': None,
        'base': 'bag1.l_top',
        'spin': 'TST',
        'label_jp': '妥協系 2巡目',
        'label': 'compromise bag 2',
        'condition_verbatim': '%O%Sの場合には、妥協系を組むことになります。',
        'condition': {'all': [{'before': ['O', 'S']}]},
        'condition_note': "OUR READING of 「%O%S」 as O before S (see 2.ideal)",
        'rows': _b('-ss------- ss-------- oojj--c--i ooj---clli ccjUzzccli cccUUzzcli cccUcccccc cccc-ccccc'),
    },
    {
        'id': '2.compromise.after',
        'bag': 2,
        'parent': '2.compromise',
        'label': 'compromise, after the TST',
        'node_kind': 'illustration',
        'after_of': '2.compromise',
        'rows': _b('---------- ---------- ---------- -cc------- cc-------- cccc--c--c ccc---cccc cccc-ccccc'),
    },
    {
        'id': '2.compromise.fire34',
        'bag': 3,
        'parent': '2.compromise',
        'base': '2.compromise.after',
        'spin': 'TSD',
        'label_jp': '火力重視 3巡目',
        'label': 'compromise, attack-first bag 3 (the L held while O/S/Z cycle in, then placed)',
        'text_verbatim': '火力重視で安定した地形にする組み方はこちら。',
        'hold_verbatim': '3巡目は%Lをホールドしつつ、%O%S%Z循環で100%組むことができます。',
        'hold': 'L',
        'hold_note': 'the page says the L is held during bag 3; the board shows where it ends up (lll over l, columns 6-8)',
        'rows': _b('---------- i-j------- i-j---lll- ijj---lzs- icc---zzss cc----zoos cccc--cooc cccUUUcccc ccccUccccc'),
    },
    {
        'id': '2.compromise.fire34.cycle1',
        'bag': 3,
        'parent': '2.compromise.fire34',
        'node_kind': 'cycle_fragment',
        'haba': 4,
        'fragment_rows': ['czsc', 'zzss', 'zoos', 'cooc'],
        'page_text': 'czsc zzss zoos cooc',
        'fragment_of': '2.compromise.fire34',
        'at': [3, 6],
        'label': 'O/S/Z cycle 1: the arrangement drawn in 2.compromise.fire34',
    },
    {
        'id': '2.compromise.fire34.cycle2',
        'bag': 3,
        'parent': '2.compromise.fire34',
        'node_kind': 'cycle_fragment',
        'haba': 4,
        'fragment_rows': ['czzc', 'oozz', 'ooss', 'cssc'],
        'page_text': 'czzc oozz ooss cssc',
        'label': 'O/S/Z cycle 2',
    },
    {
        'id': '2.compromise.fire34.cycle3',
        'bag': 3,
        'parent': '2.compromise.fire34',
        'node_kind': 'cycle_fragment',
        'haba': 4,
        'fragment_rows': ['cooc', 'sooz', 'sszz', 'cszc'],
        'page_text': 'cooc sooz sszz cszc',
        'label': 'O/S/Z cycle 3',
    },
    {
        'id': '2.compromise.fire34.cycle4',
        'bag': 3,
        'parent': '2.compromise.fire34',
        'node_kind': 'cycle_fragment',
        'haba': 4,
        'fragment_rows': ['cssc', 'ssoo', 'zzoo', 'czzc'],
        'page_text': 'cssc ssoo zzoo czzc',
        'label': 'O/S/Z cycle 4',
    },
    {
        'id': '2.compromise.fire34.bag4',
        'bag': 4,
        'parent': '2.compromise.fire34',
        'base': '2.compromise.fire34',
        'spin': 'TSD',
        'label_jp': '火力重視 4巡目',
        'label': 'compromise, attack-first bag 4 (J/L cycle on the left; a vertical T slot)',
        'text_verbatim': '4巡目は上図のように%J%L循環で100%組むことができます。',
        'rows': _b('---------- jjj------- llj---zooi clc--zzooi clc--zccci ccc---ccci cccssUcccc ccssUUcccc cccc-Ucccc'),
    },
    {
        'id': '2.compromise.fire34.bag4.cycle1',
        'bag': 4,
        'parent': '2.compromise.fire34.bag4',
        'node_kind': 'cycle_fragment',
        'haba': 3,
        'fragment_rows': ['jjj', 'llj', 'clc', 'clc'],
        'page_text': 'jjj llj clc clc',
        'fragment_of': '2.compromise.fire34.bag4',
        'at': [1, 0],
        'label': 'J/L cycle 1: the arrangement drawn in 2.compromise.fire34.bag4',
    },
    {
        'id': '2.compromise.fire34.bag4.cycle2',
        'bag': 4,
        'parent': '2.compromise.fire34.bag4',
        'node_kind': 'cycle_fragment',
        'haba': 3,
        'fragment_rows': ['lll', 'ljj', 'cjc', 'cjc'],
        'page_text': 'lll ljj cjc cjc',
        'label': 'J/L cycle 2',
    },
    {
        'id': '2.compromise.fire5#1',
        'bag': 3,
        'parent': '2.compromise',
        'base': '2.compromise.after',
        'spin': 'TSD',
        'label_jp': '火力派生 5巡パフェ狙い 3巡目 1',
        'label': 'compromise, 5-bag PC line, bag 3 form 1',
        'group': '2.compromise.fire5',
        'variant': 1,
        'condition': None,
        'rows': _b('---------- izz------- ijzz------ ijjj------ iccss--loo ccss---loo cccc--cllc cccUUUcccc ccccUccccc'),
    },
    {
        'id': '2.compromise.fire5#2',
        'bag': 3,
        'parent': '2.compromise',
        'base': '2.compromise.after',
        'spin': 'TSD',
        'label_jp': '火力派生 5巡パフェ狙い 3巡目 2',
        'label': 'compromise, 5-bag PC line, bag 3 form 2',
        'group': '2.compromise.fire5',
        'variant': 2,
        'condition': None,
        'rows': _b('---------- ioo------- iool------ illl------ iccss--jjz ccss---jzz cccc--cjzc cccUUUcccc ccccUccccc'),
    },
    {
        'id': '2.compromise.fire5.after',
        'bag': 3,
        'parent': '2.compromise.fire5',
        'label': '5-bag PC line, after the bag-3 TSD (both forms collapse to it; checked)',
        'node_kind': 'illustration',
        'after_of': '2.compromise.fire5#1',
        'rows': _b('---------- ccc------- cccc------ cccc------ ccccc--ccc cccc---ccc cccc--cccc'),
    },
    {
        'id': '2.compromise.fire5.bag4#1',
        'bag': 4,
        'parent': '2.compromise.fire5',
        'base': '2.compromise.fire5.after',
        'spin': 'TSD',
        'label': 'compromise, 5-bag PC line, bag 4 form 1 (OUR READING of the bag; the page gives no caption)',
        'group': '2.compromise.fire5.bag4',
        'variant': 1,
        'condition': None,
        'unmatchable': '9 non-empty rows (under the blank top row) > ROWS = 8',
        'rows': _b('---------- jj-------- joo------- joo------i ccc---slli cccc--ssli ccccUUUsli cccccUzccc cccc-zzccc cccc-zcccc'),
    },
    {
        'id': '2.compromise.fire5.bag4#2',
        'bag': 4,
        'parent': '2.compromise.fire5',
        'base': '2.compromise.fire5.after',
        'spin': 'TSD',
        'label': 'compromise, 5-bag PC line, bag 4 form 2 (OUR READING of the bag; the page gives no caption)',
        'group': '2.compromise.fire5.bag4',
        'variant': 2,
        'condition': None,
        'unmatchable': '9 non-empty rows (under the blank top row) > ROWS = 8',
        'rows': _b('---------- ls-------- lss------- lls------i ccc---ooji cccc--ooji ccccUUUjji cccccUzccc cccc-zzccc cccc-zcccc'),
    },
    {
        'id': '2.compromise.fire5.bag4.after',
        'bag': 4,
        'parent': '2.compromise.fire5.bag4',
        'label': '5-bag PC line, after the bag-4 TSD (both forms collapse to it; checked)',
        'node_kind': 'illustration',
        'after_of': '2.compromise.fire5.bag4#1',
        'rows': _b('---------- cc-------- ccc------- ccc------c ccc---cccc cccc--cccc cccc-ccccc cccc-ccccc'),
    },
]


#: The page's PC lists, in page order. `shown` / `rest_stated` are the page's own split (「残りNパターン」).
_PC4_ROWS = [
    '---------- ccLLjjssoo cccLjsscoo cccLcccccc ccccjccccc',
    '---------- ccLLiiiioo cccLlllcoo cccLcccccc cccclccccc',
    '---------- ccjjjtttoo cccLLLtcoo cccLcccccc ccccjccccc',
]

_IDEAL_PC_ROWS = [
    '---------- iiiillljjj cccclssooj ccccsscooc ccctttcccc cccctccccc',
    '---------- iiiijjjlll ccccoojlss ccccoocssc ccctttcccc cccctccccc',
    '---------- iiiijjzlll ccccjzzlss ccccjzcssc ccctttcccc cccctccccc',
    '---------- iiiijjzloo ccccjzzloo ccccjzcllc ccctttcccc cccctccccc',
    '---------- iiiijjzzoo ccccjllloo ccccjlczzc ccctttcccc cccctccccc',
    '---------- iiiiooljss ccccllljjj ccccoocssc ccctttcccc cccctccccc',
    '---------- iiiiooljjz ccccllljzz ccccoocjzc ccctttcccc cccctccccc',
    '---------- iiiijjzloo ccccjzzloo ccccsscllc cccsszcccc ccccjccccc',
    '---------- iiiisllloo ccccsszzoo cccctsczzc cccttlcccc cccctccccc',
    '---------- iiiillljjj cccctttooj ccccsscooc cccsstcccc cccclccccc',
    '---------- iiiillljjz cccctttjzz ccccsscjzc cccsstcccc cccclccccc',
    '---------- iiiitoojjz ccccsoojzz ccccsscjzc cccttscccc cccctccccc',
    '---------- iiiitllloo ccccslzzoo ccccssczzc cccttscccc cccctccccc',
    '---------- iiiitjzzoo ccccsjjjoo ccccssczzc cccttscccc cccctccccc',
]

_NORMAL_PC_ROWS = [
    '---------- oojiiiilll oojjjsslcc ccccsscccc ccctttcccc cccctccccc',
    '---------- oollljiiii oolzzjjjcc cccczzcccc ccctttcccc cccctccccc',
    '---------- jiiiioolll jjjzzoolcc cccczzcccc ccctttcccc cccctccccc',
    '---------- ooiiiizlll ootttzzlcc ccccjjcccc ccctjzcccc ccccjccccc',
    '---------- oostttiiii oosstlllcc ccccjjcccc cccsjlcccc ccccjccccc',
    '---------- oostttzlll oosstzzlcc ccccjjcccc cccsjzcccc ccccjccccc',
    '---------- ooiiiizlll oojjjzzlcc ccccsscccc cccsszcccc ccccjccccc',
    '---------- oosjjjzlll oossizzlcc ccccizcccc cccsijcccc cccciccccc',
]

_PC5_ROWS = [
    '---------- cctttiiiiz ccctssoozz cccssloozc ccclllcccc ccccjjcccc ccccjccccc ccccjccccc',
    '---------- cctttoolll ccctzoolss ccczzjjssc ccczijcccc ccccijcccc cccciccccc cccciccccc',
    '---------- cciiiissoo ccczzsstoo cccllltttc ccclzzcccc ccccjjcccc ccccjccccc ccccjccccc',
    '---------- cctttssloo ccctsszloo cccjizzllc cccjjjcccc ccccizcccc cccciccccc cccciccccc',
    '---------- cczzjjiiii ccczztttss cccllltssc cccloocccc ccccoocccc ccccjccccc ccccjccccc',
    '---------- ccjjjtttoo cccsjizzoo cccssitzzc cccllicccc cccclicccc cccclccccc ccccsccccc',
]

#: several boards that share ONE continuation: a list's `parent` (or an after board's) names the
#: group, and each member names it in `group`. `drawn` is the page's own count, not derived.
GROUPS = [
    {'id': '2.normal', 'heading': '通常形 2巡目', 'drawn': 3,
     'condition_verbatim': '2巡目に%I%Lor%O%Jが早い場合には、通常形を組むことができます。',
     'condition': {'any': [{'early': ['I', 'L']}, {'early': ['O', 'J']}]},
     'condition_note': 'OUR READING: two early PAIRS; the page gives the trigger for the family, never for a form'},
    {'id': '2.compromise.fire5', 'heading': '3巡目 - 火力派生 5巡パフェ狙い', 'drawn': 2,
     'heading_note': 'the page\'s one heading over this line; it covers bag 3 and, with no text between, the bag-4 boards below',
     'text_verbatim': 'もしくは、下図のように組むことで火力を維持しつつ5巡パフェ(14段パフェ)を狙うことができます。'},
    {'id': '2.compromise.fire5.bag4', 'heading': '3巡目 - 火力派生 5巡パフェ狙い', 'drawn': 2,
     'heading_note': 'OUR READING that these two are bag 4: the page has no 4巡目 heading or sentence for them; they follow the bag-3 TSD board with no text between, and each draws a second TSD on it (checked against the base chain)'},
]

LISTS = [
    {'id': '2.pc4', 'parent': 'bag1.l_hold', 'base': 'bag1.l_hold', 'bag': 2, 'heading': '2巡目4ラインパフェ',
     'rows': _PC4_ROWS, 'stated_pattern_count': 3, 'shown': 3, 'rest_stated': 0, 'complete': True,
     'pc_lines': 4, 'pc_lines_note': 'a 4-line PC drawn in bag 2 on the L-held board: no spin before it'},
    {'id': '2.ideal.pc', 'parent': '2.ideal', 'base': '2.ideal.after', 'bag': 3, 'heading': '3巡目 - パフェ狙い',
     'rows': _IDEAL_PC_ROWS, 'stated_pattern_count': 14, 'shown': 4, 'rest_stated': 10, 'complete': True},
    {'id': '2.normal.pc', 'parent': '2.normal', 'base': '2.normal.after', 'bag': 3, 'heading': '3巡目',
     'rows': _NORMAL_PC_ROWS, 'stated_pattern_count': 8, 'shown': 3, 'rest_stated': 5, 'complete': True},
    {'id': '2.compromise.fire5.pc', 'parent': '2.compromise.fire5.bag4', 'base': '2.compromise.fire5.bag4.after',
     'bag': 5, 'heading': '5巡目', 'rows': _PC5_ROWS, 'stated_pattern_count': 6, 'shown': 6, 'rest_stated': 0,
     'complete': True, 'pc_lines': 9, 'total_lines': 14, 'total_lines_quote': '2.compromise.fire5',
     'pc_lines_note': 'the 7-row body plus the bag-4 TSD before it; the page\'s 14段 counts every bag of the line '
                      '(TST 3 + TSD 2 + TSD 2 + 7), which `_mountainous2_checks` re-derives along the base chain'},
]

#: where each list's patterns are inserted in page order: after this node
_LIST_AFTER = {'2.pc4': 'bag1.l_hold', '2.ideal.pc': '2.ideal.after', '2.normal.pc': '2.normal.after',
               '2.compromise.fire5.pc': '2.compromise.fire5.bag4.after'}

#: The page's content that has no board. Identified by reading the page; `--html-dir` checks each
#: node's `page_text` is still on it.
NON_BOARD = {
    'overview.derivation_map': 'image_only',
    'overview.video': 'video_only',
    '2.ideal.fire.pc5_image': 'image_only',
    '2.compromise.fire34.cycle1': 'cycle_fragment',
    '2.compromise.fire34.cycle2': 'cycle_fragment',
    '2.compromise.fire34.cycle3': 'cycle_fragment',
    '2.compromise.fire34.cycle4': 'cycle_fragment',
    '2.compromise.fire34.bag4.cycle1': 'cycle_fragment',
    '2.compromise.fire34.bag4.cycle2': 'cycle_fragment',
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
    ['basic.1', 'basic.2', 'basic.3', 'bag1.l_top', 'bag1.j_top']
    + [f'2.pc4#{i}' for i in range(1, 4)]
    + ['2.ideal', '2.ideal.after'] + [f'2.ideal.pc#{i}' for i in range(1, 15)]
    + [f'2.normal#{k}' for k in range(1, 4)] + ['2.normal.after'] + [f'2.normal.pc#{i}' for i in range(1, 9)]
    + ['2.compromise', '2.compromise.after', '2.compromise.fire34', '2.compromise.fire34.bag4',
       '2.compromise.fire5#1', '2.compromise.fire5#2', '2.compromise.fire5.after',
       '2.compromise.fire5.bag4#1', '2.compromise.fire5.bag4#2', '2.compromise.fire5.bag4.after']
    + [f'2.compromise.fire5.pc#{i}' for i in range(1, 7)]
)

#: the list-node flags, computed from the cells and re-checked by the gate
SLOT_FLAGS = {'has_u_slot': lambda rows: t_slot(rows) is not None,
              't_in_tsd_slot': lambda rows: t_slot(rows, 't') == 'flat'}


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
        'schema': 'mountainous2-routes/1',
        'source': SOURCE,
        'terms': TERMS,
        'legend': LEGEND,
        'quotes': QUOTES,
        'bag1': BAG1,
        'basic_form': BASIC_FORM,
        'groups': GROUPS,
        'lists': lists,
        'known_discrepancies': KNOWN_DISCREPANCIES,
        'page_order': PAGE_ORDER,
        'nodes': nodes,
    }


# ── 山岳積み2号's own rules, and its half of the shared gate ─────────────────────────────────────
_SPIN_LINES = {'TST': 3, 'TSD': 2}


def _cond_pieces(cond) -> list:
    """Every piece a condition names, through `all` / `any` / `before` / `early`."""
    if isinstance(cond, list):
        return [p for c in cond for p in _cond_pieces(c)]
    if not isinstance(cond, dict):
        return []
    out = []
    for k in ('all', 'any'):
        out += _cond_pieces(cond.get(k, []))
    for k in ('before', 'early', 'then_decided_by', 'decided_by'):
        v = cond.get(k, [])
        out += v if isinstance(v, list) else [v]
    return out


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


def _mountainous2_checks(data: dict, ctx: dict) -> tuple[list[str], set[str]]:
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

    # conditions (bag 1, groups, nodes) name pieces; the bag-1 side rule names J and L
    b1 = data.get('bag1', {})
    conds = [b1.get('requires'), b1.get('also'), b1.get('side')] + [g.get('condition') for g in groups.values()]
    conds += [n.get('condition') for n in nodes]
    if any(p not in RT.PIECES for c in conds for p in _cond_pieces(c)):
        bad.append('condition: a condition names something that is not a piece')
    if sorted(b1.get('side', {}).get('decided_by', [])) != ['J', 'L']:
        bad.append('bag1-side: the side rule no longer names J and L')

    # the 6-lock L-held board is exactly the drawn 7-lock board less its four l cells
    hold, top = by_id.get('bag1.l_hold', {}), by_id.get('bag1.l_top', {})
    if 'rows' in hold and 'rows' in top:
        less = bottom([r.replace('l', EMPTY) for r in top['rows']], RT.ROWS)
        if bottom(hold['rows'], RT.ROWS) != less or sum(r.count('l') for r in top['rows']) != 4:
            bad.append('bag1-hold: bag1.l_hold is not bag1.l_top less its four l cells')
    else:
        bad.append('bag1-hold: bag1.l_hold or bag1.l_top is missing')

    # the right bag-1 board is the left one mirrored: one shape, not two (rule `mirror-of` checks it)
    if any(n.get('mirror_of') and 'rows' in n and n['mirror_of'] in boards
           and bottom(n['rows'], RT.ROWS) == mirror(bottom(boards[n['mirror_of']], RT.ROWS)) for n in nodes):
        found.add('bag1.right:mirror')

    # a spin named on a board is the spin its U cells fire
    for n in nodes:
        if n.get('spin') and 'rows' in n and 'U' in ''.join(n['rows']):
            if after_spin(n['rows'])[1] != _SPIN_LINES.get(n['spin']):
                bad.append(f'spin: {n["id"]} names a {n["spin"]} but its U slot clears '
                           f'{after_spin(n["rows"])[1]} rows')

    # a group's forms share ONE occupancy and collapse to the one after-board drawn for the group;
    # a group with no per-form condition is a measured source gap
    for g in groups.values():
        members = [n for n in nodes if n.get('group') == g['id'] and 'rows' in n]
        if len({tuple(RT.occ(bottom(n['rows'], RT.ROWS + 2))) for n in members}) != 1:
            bad.append(f'group: the forms of {g["id"]} no longer share one occupancy')
        afters = [n for n in nodes if n.get('after_of') in {m['id'] for m in members}]
        for a in afters:
            for m in members:
                left, _ = after_spin(m['rows'])
                h = max(len(left), len(a['rows']))
                if RT.occ(bottom(left, h)) != RT.occ(bottom(a['rows'], h)):
                    bad.append(f'group: {m["id"]} does not collapse to {a["id"]} after its spin')
        if members and all(n.get('condition') is None for n in members):
            found.add(f'{g["id"]}:no_conditions')

    # a PC list whose sentence says TSD, with a pattern that does not fire one, contradicts it
    for lst in data.get('lists', []):
        q = quotes.get(lst['id'])
        pats = [n for n in nodes if n.get('list') == lst['id']]
        if q and 'TSD' in q['verbatim'] and any(not n.get('t_in_tsd_slot') for n in pats):
            found.add(f'{lst["id"]}:no_tsd')
        # a list's stated total line count is re-derived along its base chain: the body, plus every
        # spin from the PC's base back to bag 1
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
            if f'{lst["total_lines"]}段' not in quotes.get(lst.get('total_lines_quote'), {}).get('verbatim', ''):
                bad.append(f'lines: quote {lst.get("total_lines_quote")!r} does not state '
                           f'{lst["total_lines"]}段 for {lst["id"]}')

    # a cycle fragment: one row per page token, all one width, whole pieces; the one drawn from a
    # board sits inside it, piece cell for piece cell. A fragment's c means "not one of these
    # pieces" (LEGEND), so it may sit over anything, an EMPTY board cell included: all four O/S/Z
    # cycles draw c in their corners, and cycle 1's top-right corner is empty on its board. That is
    # the page's convention, not a slip, so it is not a discrepancy.
    for n in nodes:
        if n.get('node_kind') != 'cycle_fragment':
            continue
        fr = n.get('fragment_rows', [])
        if not fr or any(len(r) != n.get('haba') for r in fr) or ' '.join(fr) != n.get('page_text') or (
                any(ch not in 'cijlostz' for r in fr for ch in r)):
            bad.append(f'fragment: {n["id"]} rows are not its page text at width {n.get("haba")}')
            continue
        if RT.piece_groups_ok(fr, {}):
            bad.append(f'fragment: {n["id"]} letters are not whole pieces')
        if 'fragment_of' in n:
            src = boards.get(n['fragment_of'])
            r0, c0 = n.get('at', [0, 0])
            if src is None or r0 + len(fr) > len(src) or c0 + n['haba'] > RT.WIDTH:
                bad.append(f'fragment: {n["id"]} does not fit inside {n["fragment_of"]}')
                continue
            for dr, row in enumerate(fr):
                for dc, ch in enumerate(row):
                    under = src[r0 + dr][c0 + dc]
                    if ch != 'c' and ch != under:
                        bad.append(f'fragment: {n["id"]} is not drawn from {n["fragment_of"]} at {n.get("at")}')
                        break

    # the introduction names a 中開けREN derivation the page does not draw
    if '中開けREN' in quotes.get('overview.intro', {}).get('verbatim', '') and not any(
            'ren' in n['id'] for n in nodes):
        found.add('overview:ren_not_drawn')
    return bad, found


SPEC = RT.TranscriptionSpec(
    out=OUT, build=build, alphabet=ALPHABET, non_board=NON_BOARD,
    harddrop={'key': 'mountainous_2', 'node': 'bag1.l_hold'},
    board_kinds=frozenset({'illustration'}),
    pc_lines=8, prior_letters='',
    upper_groups={'L': 'separate'},
    slot_flags=SLOT_FLAGS, occupancy_class_parents=2, extra_checks=_mountainous2_checks)


def verify(data: dict) -> list[str]:
    return RT.verify(data, SPEC)


def drift(data: dict) -> list[str]:
    return RT.drift(data, SPEC)


# ── selftest ───────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    """A gate nothing can fail is decorative. Plant one defect per rule, each in a named 山岳積み2号 id."""

    def drop_pattern(d):
        d['nodes'] = [n for n in d['nodes'] if n['id'] != '2.normal.pc#8']

    def flip_hold(d):
        setcell(node(d, 'bag1.l_hold')['rows'], 1, 1, '-')            # one s cell of the L-held board

    def break_mirror(d):
        setcell(node(d, 'bag1.j_top')['rows'], 3, 8, '-')            # one z cell of the mirror

    def top_off(d):
        setcell(node(d, 'bag1.l_top')['rows'], 1, 6, '-')            # one l cell of the tower gone

    def ghost_group(d):
        node(d, '2.normal#2')['group'] = '2.normal.nowhere'

    def bad_cell(d):
        setcell(node(d, '2.compromise.fire34')['rows'], 0, 0, 'p')

    def flag_flip(d):
        n = node(d, '2.ideal.pc#9')
        n['t_in_tsd_slot'] = not n['t_in_tsd_slot']

    def drop_discrepancy(d):
        d['known_discrepancies'] = [x for x in d['known_discrepancies'] if x['id'] != '2.normal.pc:no_tsd']

    def recolour(d):
        setcell(node(d, '2.normal#2')['rows'], 2, 0, 'o')            # an i cell drawn as o

    def harddrop_off(d):
        n = node(d, 'bag1.l_hold')
        n['rows'] = ['-' + r[:-1] for r in n['rows']]

    def dup_form(d):
        node(d, '2.normal#2')['rows'] = list(node(d, '2.normal#1')['rows'])

    def basic_off(d):
        setcell(d['basic_form'][1]['rows'], 2, 0, 'o')              # basic.2's j drawn o

    def tall(d):
        node(d, '2.compromise.fire34.bag4')['rows'].insert(0, 'i---------')

    def no_reason(d):
        node(d, '2.compromise.fire5.bag4#1')['unmatchable'] = ''

    def c_cells(d):
        setcell(node(d, '2.compromise.fire34')['rows'], 1, 9, 'c')   # a c where compromise.after has none

    def lost_fragment(d):
        d['nodes'] = [n for n in d['nodes'] if n['id'] != '2.compromise.fire34.cycle3']

    def wrong_after(d):
        node(d, '2.normal.after')['after_of'] = '2.compromise'

    def side_rule(d):
        d['bag1']['side']['decided_by'] = ['J', 'O']

    def pc4_short(d):
        n = node(d, '2.pc4#2')
        n['rows'] = n['rows'][:-1]                                    # a 3-line PC drawn

    def pc4_base(d):
        node(d, '2.pc4#1')['base'] = 'bag1.l_top'                     # the PC4 read off the tower board

    def normal3_base(d):
        node(d, '2.normal#3')['base'] = 'bag1.l_top'

    def wrong_spin(d):
        node(d, '2.compromise.fire34.bag4')['spin'] = 'TST'

    def no_collapse(d):
        setcell(node(d, '2.compromise.fire5#2')['rows'], 1, 0, '-')   # one cell above the TSD gone

    def total_lines(d):
        next(x for x in d['lists'] if x['id'] == '2.compromise.fire5.pc')['total_lines'] = 13

    def unquoted(d):
        node(d, '2.compromise')['condition_verbatim'] = '%S%Oの場合には、妥協系を組むことになります。'

    def frag_moved(d):
        node(d, '2.compromise.fire34.bag4.cycle1')['at'] = [1, 1]

    def frag_text(d):
        node(d, '2.compromise.fire34.cycle2')['fragment_rows'][0] = 'czzz'

    def cond_piece(d):
        d['groups'][0]['condition']['any'][0]['early'] = ['I', 'X']

    def five_pc_lines(d):
        next(x for x in d['lists'] if x['id'] == '2.compromise.fire5.pc')['pc_lines'] = 8

    def ren_drawn(d):
        node(d, 'overview.video')['id'] = 'overview.ren_video'

    mutants = [
        (drop_pattern, 'a dropped PC pattern', 'list-count:'),
        (flip_hold, 'one cell of bag1.l_hold flipped', 'bag1-hold:'),
        (break_mirror, 'the J-top board no longer the L-top board mirrored', 'mirror-of:'),
        (top_off, 'a bag-2 base cell gone from bag1.l_top', 'bag2-base:'),
        (ghost_group, 'a group no node declares', 'grammar:'),
        (bad_cell, 'a cell outside the alphabet', 'grammar:'),
        (flag_flip, 'a t_in_tsd_slot flag flipped', 'grammar:'),
        (drop_discrepancy, 'a dropped known discrepancy', 'discrepancy:'),
        (recolour, 'one cell of a 2.normal form recoloured', 'discrepancy:'),
        (harddrop_off, 'the harddrop board shifted one column', 'harddrop:'),
        (dup_form, 'two 2.normal forms made equal by colour', 'distinct:'),
        (basic_off, 'a 基本形 board off its node', 'basic-form:'),
        (tall, 'a 9-row board not marked unmatchable', 'grammar:'),
        (no_reason, 'an unmatchable node with no reason', 'grammar:'),
        (c_cells, 'a c cell where the compromise TST leaves none', 'c-cells:'),
        (lost_fragment, 'a deleted cycle fragment', 'non-board:'),
        (wrong_after, 'normal.after read off the wrong spin', 'after-of:'),
        (side_rule, 'the bag-1 side rule naming another piece', 'bag1-side:'),
        (pc4_short, 'a bag-2 PC that is not 4 lines', 'pc:'),
        (pc4_base, 'a bag-2 PC read off the 7-lock board', 'bag2-base:'),
        (normal3_base, '2.normal#3 read off the 7-lock board', 'bag2-base:'),
        (wrong_spin, 'a TSD board named a TST', 'spin:'),
        (no_collapse, 'a 5巡 bag-3 form that no longer collapses with its sibling', 'group:'),
        (total_lines, 'the 14段 total misstated', 'lines:'),
        (unquoted, 'a verbatim field that is not on the page', 'verbatim:'),
        (frag_moved, 'a cycle fragment placed off its board', 'fragment:'),
        (frag_text, 'a cycle fragment off its page text', 'fragment:'),
        (cond_piece, 'a condition naming a non-piece', 'condition:'),
        (five_pc_lines, 'the 5巡 PC list checked at 8 lines', 'pc:'),
        (ren_drawn, 'a REN node appearing makes the REN gap unmeasured', 'discrepancy:'),
    ]
    spec_mutants = [
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'harddrop': {'key': 'mountainous_3', 'node': 'bag1.l_hold'}}),
         'the harddrop key changed to Mountainous Stacking 3', 'harddrop:'),
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'harddrop': {'key': 'mountainous_2', 'node': 'bag1.l_top'}}),
         'the harddrop node changed to the 7-lock board', 'harddrop:'),
    ]
    return RT.run_selftest(SPEC, mutants, {'board': ('ccccsscllc', 'cccc-scllc'),
                                           'text': ('組み方概要図', '組み方概略図X'),
                                           'hand_edit': '2.compromise', 'quote': '2.normal.pc'},
                           spec_mutants)


def main() -> int:
    return RT.main(SPEC, selftest, __doc__)


if __name__ == '__main__':
    raise SystemExit(main())

"""Transcribe shiwehi.com's はちみつ砲 (Honey Cup) route page into `honeycup-routes.json`.

    python3 -m pipeline.openers.extract_honeycup_routes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_honeycup_routes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_honeycup_routes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_honeycup_routes --html-dir <dir> --write  # ...and rewrite

The second opener ROUTE page, after 迷走砲 (`extract_meisou_routes.py`): one bag-1 shape (held J,
or held L mirrored), five bag-2 ideal forms that share one occupancy and one compromise form, a
fifteen-pattern bag-3 Perfect Clear list, and two TST-donate / roof continuations. Every rule two
openers share is `route_transcription.py`'s, once; this file holds the transcription, its `SPEC`
and the rules only this page needs (`_honeycup_checks`).

WHERE THE TRANSCRIPTION COMES FROM, AND WHY THE PAGE IS NOT COMMITTED. `NODES` below is a literal,
hand-checked transcription. Plain curl through the proxy gets a 403, so CI cannot fetch the page;
what is committed is the transcription plus the sha256 of the markdown snapshot it was checked
against (MCP `web_fetch`, full content). That snapshot DOES hold every rendered board: all 36, in
page order, which `--html-dir` re-derives from it, so a redrawn, added or removed diagram fails
rather than being silently absent. The hash names the snapshot; it does not reproduce it.

WHAT THE SNAPSHOT DOES NOT HOLD. The page source carries 33 more boards and two sentences inside
HTML comments: a "Heart" 5-bag PC list and a twelve-pattern compromise PC list (「84.31%」). They are
not rendered on the page and are not in the snapshot; they were hand-copied from one raw-HTML fetch
(Firecrawl `rawHtml`) with no second fetch to check them against. They are kept as PROVENANCE
(`html_comment_boards`), never as route nodes, and nothing classifies against them.

WHAT IS AN INFERENCE, flagged in the JSON rather than in prose only:

  * upper-case `J` has no legend on the page. It is read as the bag-1 J, held, then placed in bag 2
    (the page: 遅いほうはホールドしておきます). Rule 3 checks the reading: a bag-2 board's `c` cells
    are exactly its bag-1 base, so the `J` cells are not bag-1 cells.
  * `bag1.j_right` is drawn only as 基本形 1 (`drawn_as`); it is the 7-lock board harddrop draws
    (rule 2). The page's bag-1 section draws the 6-lock held-J board and its mirror.
  * `B` (only in the REN derivation) and the muted `I`/`Z`/`C` shading (only in the TST
    illustrations) have no legend either; neither is ever matched.

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
OUT = HERE / 'honeycup-routes.json'

ALPHABET = frozenset('-ijlostzcUJCIZpB')


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/honeycup.php',
    'title': 'はちみつ砲(Honey Cup)',
    'updated': '2025-08-03',
    'created': '2021-12-25',
    'fetched': '2026-10-12',
    'fetch_method': 'mcp__Parallel_Search__web_fetch with full_content=true, which renders the page to '
                    'markdown (a leading "-" on a board row comes back escaped as "\\-" and is '
                    'unescaped); the snapshot holds every rendered board, 36 in page order. The boards '
                    'inside HTML comments (html_comment_boards) came from one raw-HTML fetch '
                    '(mcp__Firecrawl__firecrawl_scrape formats=[rawHtml]) and are not in the snapshot. '
                    'Plain curl through the proxy gets HTTP 403, so CI cannot refetch.',
    'snapshot_file': 'honeycup.md',
    'snapshot_sha256': 'df03d90d1a7c4d8c31e71274576df2f9b304606b9b124dc4562da25aafc40817',
    'snapshot_bytes': 8103,
    'snapshot_note': 'sha256 of the markdown snapshot this transcription was checked against. Not '
                     're-verifiable in CI: the page is not committed and cannot be fetched there. '
                     'Re-check with --html-dir after any refetch; a renderer change alone will move '
                     'the hash, so a moved hash means "read the board diff", not "the page changed". '
                     'The raw-HTML-only material (html_comment_boards, the hidden quotes) is NOT covered '
                     'by this hash.',
    'renderer': {
        'url': 'https://shiwehi.com/tetris/mutual/column-exp.js?date=20210408',
        'read': '2026-10-12',
        'colorMap_used': {'c': '#a3a3a3', 'C': '#cccccc', 'U': '#c8a6ff with a #8400ff radial dot',
                          'p': '#ff33ff', 'B': '#444444', 'J': '#4d57d8 (muted j)', 'I': '#4db1d8 (muted i)',
                          'Z': '#d84d4d (muted z)', '-': '#000000'},
        'mirror_button': 'body.reversed swaps j<->l, s<->z (and upper case) and reverses nothing else in '
                         'the char map; the canvas is redrawn mirrored',
    },
    'decorative_images': ['はちみつ砲(Honey Cup)タイトル画像'],
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ, align at the BOTTOM row',
    '-': 'empty',
    'i o t s z j l': 'a cell of that piece',
    'c': 'a cell filled before this diagram (earlier bags), grey',
    'C': 'a grey cell in a row the drawn spin clears (lighter grey #cccccc)',
    'J': 'the bag-1 J, held and placed in bag 2, drawn in a muted J colour (page legend: none; OUR READING, consistent with the text 遅いほうはホールド)',
    'I Z': 'only in 2.compromise.tst: muted i/z cells inside the cleared rows',
    'U': 'the T-spin slot',
    'p': 'placeholder: any filling (STMB template only)',
    'B': 'dark grey #444444, only in 2.ideal.ren4: OUR READING, the REN region; no legend on the page',
    '%X': "the X piece; '%I>%L>%S' means I before L before S",
}


QUOTES = [
    {
        'id': 'overview.max_damage',
        'figure': '21ライン',
        'verbatim': 'TST→TSD→8段パフェで21ラインという高火力を狙うことができる。',
    },
    {
        'id': 'overview.setup_rate',
        'figure': '65.56%',
        'verbatim': '1巡目のセットアップ率が左右反転含めて65.56%と低め。',
    },
    {
        'id': '2.ideal.pc',
        'figure': '14パターン：パフェ率96.87%',
        'verbatim': '理想形に組んだ場合、3巡目にはTSDを打ちつつ8段パフェを狙うことができます。(14パターン：パフェ率96.87%)',
    },
    {
        'id': '2.ideal.fire',
        'figure': '5巡パフェ(14段パフェ)',
        'verbatim': 'もしくは、%Tが遅い等でパフェを取らない場合等には、下図のように組むことで火力を維持しつつ5巡パフェ(14段パフェ)を狙うことができます。',
    },
    {
        'id': '2.ideal.fire.stmb',
        'figure': None,
        'verbatim': '上記の5巡パフェを狙えない場合でも、下図の形にしたときに高さが同じ3マス空きの形ができるため、STMB caveの形を組むことができます。',
    },
    {
        'id': 'hidden.meisou_complement',
        'figure': '100%',
        'rendered': False,
        'verbatim': 'はちみつ砲は迷走砲との補完相性も良く、はちみつ砲+迷走砲のセットアップ率が100%となっていることも特徴です。',
        'note': 'inside an HTML comment; not shown on the page',
    },
    {
        'id': 'hidden.compromise.pc',
        'figure': '84.31%',
        'rendered': False,
        'verbatim': '妥協形に組んだ場合、3巡目にはTSDを打ちつつ8段パフェを狙うことができます。(84.31%)',
        'note': 'inside an HTML comment; not shown on the page',
    },
]


BAG1 = {
    'requires_verbatim': '1巡目の組み方は上図の通りで、少なくとも%Iが早い必要があります。',
    'requires': {'early': 'I'},
    'hold_free_verbatim': '%I>%L>%S',
    'hold_free': {'applies_to': 'bag1.j_hold', 'before': ['I', 'L', 'S']},
    'side_verbatim': '%J%Lのどちらが早いかによって左右を決める、遅いほうはホールドしておきます。',
    'side': {'later_of': ['J', 'L'], 'is': 'held'},
    'mirror_note_verbatim': '(ここでは、以下左のパターン(%Jホールド)で説明していきますが、右下にある反転ボタンを押すことで左右反転の図を見ることができます。)',
}


BASIC_FORM = [
    {
        'id': 'basic.1',
        'same_as': 'bag1.j_right',
        'rows': _b('---------- ---------- ---------- ---------j -ss------j ssl----tjj lll-zzttoo iiii-zztoo'),
        'canvas': 'tetCanvas0',
        'snapshot_line': 24,
    },
    {
        'id': 'basic.2',
        'same_as': '2.ideal#3',
        'differs': 'the held J is drawn c (grey) instead of J, and the TST slot is drawn U',
        'recolour': {'J': 'c', '-': 'U'},
        'rows': _b('---------- iiii------ jjss--oo-- jss---oolc jccUzzlllc cccUUzzccc cccUcccccc cccc-ccccc'),
        'canvas': 'tetCanvas1',
        'snapshot_line': 33,
    },
    {
        'id': 'basic.3',
        'same_as': '2.ideal.pc#1',
        'differs': 'the TSD T is drawn U instead of t',
        'recolour': {'t': 'U'},
        'rows': _b('---------- ---------- ---------- iiiillljjj cccclsszzj ccccsscczz cccUUUcccc ccccUccccc'),
        'canvas': 'tetCanvas2',
        'snapshot_line': 42,
    },
]


KNOWN_DISCREPANCIES = [
    {
        'id': '2.ideal.pc:stated_vs_drawn',
        'what': 'the page states 14 patterns and draws 15 (5 shown + 残り10); all 15 are distinct and all 15 are kept',
    },
    {
        'id': '2.ideal.pc:no_tsd',
        'what': 'the sentence says 3巡目にはTSDを打ちつつ, but pc#11-#15 fill the TSD slot with other pieces: pc#11 draws no T at all (pieces ijlosz), pc#12-#15 draw the T elsewhere (across a cleared row). Only pc#1-#10 have the T in the TSD slot (ccctttcccc / cccctccccc)',
    },
    {
        'id': '2.compromise.tst:highlight',
        'what': "in the highlighted copy the cleared-row cells are upper-cased (muted) for i, c, z but NOT for the l, l, j at row 4 (from the top), columns 6-8, which stay full colour (snapshot line 340 'ICCUZZlljJ'); the held J is upper case in both copies, so its highlight is not visible. Occupancy is unaffected",
    },
    {
        'id': 'bag1.right:mirror',
        'what': 'the right bag-1 board is the left one mirrored with J<->L, S<->Z (cell for cell), so the page has ONE bag-1 shape, not two',
    },
    {
        'id': '2.ideal.bag2:no_conditions',
        'what': 'five bag-2 variants and no stated order condition for any of them',
    },
]


#: PROVENANCE ONLY: the boards inside HTML comments, hand-copied from one raw-HTML fetch. Never
#: route nodes; nothing classifies against them.
HTML_COMMENT_BOARDS_NOTE = {
    'note': 'boards inside HTML comments in the raw HTML (fetched via Firecrawl rawHtml, 2026-10-12); NOT rendered on the page, NOT in the markdown snapshot, NOT covered by snapshot_sha256. Hand-copied; every row 10 cells and every piece letter a multiple of 4 (checked). Recorded for completeness, not as route nodes',
    'sections': {
        'heart.SL': 'Heart%S%L埋めパターン | 3巡目の%Iの位置は4巡目に%O>%Jか%O>%Lかで置き分けると良いです。',
        'heart.OL': 'Heart%O%L埋めパターン |',
        'compromise.pc': '3巡目 - パフェ狙い (妥協形) | 妥協形に組んだ場合、3巡目にはTSDを打ちつつ8段パフェを狙うことができます。(84.31%)',
    },
}

HTML_COMMENT_BOARDS_LIST = [
    {'section': 'heart.SL', 'group': '1',
     'rows': _b('---------- ---------i ---------i ---z-----i oozz--j--i oozUUUjsll ccccUjjssl cccc--ccsl ccc---cccc cccc-ccccc')},
    {'section': 'heart.SL', 'group': '1',
     'rows': _b('---------- ---------- j--------- jjjz-----c oozz-isllc oozc-isslc cccc-icslc cccc-icccc cccUUUcccc ccccUccccc')},
    {'section': 'heart.SL', 'group': '1',
     'rows': _b('---------- ---------- ---------- tttsszjloo ctsszzjloo cccczjjllc cccciccccc cccciccccc cccciccccc cccciccccc')},
    {'section': 'heart.SL', 'group': '2',
     'rows': _b('i--------- i--------- i--------- i--z------ oozz--j--- oozUUUjsll ccccUjjssl cccc--ccsl ccc---cccc cccc-ccccc')},
    {'section': 'heart.SL', 'group': '2',
     'rows': _b('---------- ---------- c--------- cjjz-----l cjzz-islll cjzc-issoo cccc-icsoo cccc-icccc cccUUUcccc ccccUccccc')},
    {'section': 'heart.SL', 'group': '2',
     'rows': _b('---------- ---------- ---------- tttsszjloo ctsszzjloo cccczjjllc cccciccccc cccciccccc cccciccccc cccciccccc')},
    {'section': 'heart.OL', 'group': '1',
     'rows': _b('i--------- i--------- i--------- iz-------- zzss--j--- zssUUUjlll ccccUjjloo cccc--ccoo ccc---cccc cccc-ccccc')},
    {'section': 'heart.OL', 'group': '1',
     'rows': _b('---------- ---------- c-------oo cjjj----oo czzji---ss cczzi--ssl cccci-clll cccci-cccc cccUUUcccc ccccUccccc')},
    {'section': 'heart.OL', 'group': '1',
     'rows': _b('---------- ---------- ---------- tttssoolll ctssjoolcc ccccjjjzcc cccccizzcc cccccizccc cccccicccc cccccicccc')},
    {'section': 'heart.OL', 'group': '2',
     'rows': _b('i--------- i--------- i--------- iz-------- zzss--j--- zssUUUjlll ccccUjjloo cccc--ccoo ccc---cccc cccc-ccccc')},
    {'section': 'heart.OL', 'group': '2',
     'rows': _b('---------- ---------- c--------- csll---z-- cssl-izzoo ccsl-izjoo cccc-icjjj cccc-icccc cccUUUcccc ccccUccccc')},
    {'section': 'heart.OL', 'group': '2',
     'rows': _b('---------- ---------- ---------- zztttssooj czztsslooj cccclllcjj cccciccccc cccciccccc cccciccccc cccciccccc')},
    {'section': 'heart.OL', 'group': '2',
     'rows': _b('---------- ---------- ---------- zztttsslll czztjjjloo ccccssjcoo cccciccccc cccciccccc cccciccccc cccciccccc')},
    {'section': 'heart.OL', 'group': '3',
     'rows': _b('i--------- i--------- i--------- iz-------- zzss--j--- zssUUUjlll ccccUjjloo cccc--ccoo ccc---cccc cccc-ccccc')},
    {'section': 'heart.OL', 'group': '3',
     'rows': _b('---------- ---------- c-------ss cjjj---ssi czzj--llli cczz--looi cccc--cooi cccc--cccc cccUUUcccc ccccUccccc')},
    {'section': 'heart.OL', 'group': '3',
     'rows': _b('---------- ---------- ---------- zz-----lll czz-i--lcc ccccissccc ccccsscccc ccccijcccc ccccijcccc ccccjjcccc')},
    {'section': 'heart.OL', 'group': '3',
     'rows': _b('---------- ---------- ---------- zztttsslll czztjjjloo ccccssjcoo cccciccccc cccciccccc cccciccccc cccciccccc')},
    {'section': 'heart.OL', 'group': '4',
     'rows': _b('---------- ---------- i-z------- izz------- izss--j--- issUUUjlll ccccUjjloo cccc--ccoo ccc---cccc cccc-ccccc')},
    {'section': 'heart.OL', 'group': '4',
     'rows': _b('---------- ---------- s--------- ssll---z-- cscli-zzoo cccli-zjoo cccci-cjjj cccci-cccc cccUUUcccc ccccUccccc')},
    {'section': 'heart.OL', 'group': '4',
     'rows': _b('---------- ---------- ---------- tttsszjlll ctsszzjloo cccczjjcoo cccccicccc cccccicccc cccccicccc cccccicccc')},
    {'section': 'heart.OL', 'group': '4',
     'rows': _b('---------- ---------- ---------- zztttoosll czztjoossl ccccjjjcsl cccccicccc cccccicccc cccccicccc cccccicccc')},
    {'section': 'compromise.pc', 'group': 'shown',
     'rows': _b('---------- lljiiiiooc cljjjssooc clccsscccc ccctttcccc cccctccccc')},
    {'section': 'compromise.pc', 'group': 'shown',
     'rows': _b('---------- lliiiizooc cljjjzzooc clccjzcccc ccctttcccc cccctccccc')},
    {'section': 'compromise.pc', 'group': 'shown',
     'rows': _b('---------- iiiijjzooc cllljzzooc clccjzcccc ccctttcccc cccctccccc')},
    {'section': 'compromise.pc', 'group': 'shown',
     'rows': _b('---------- iiiijssooc cllljjjooc clccsscccc ccctttcccc cccctccccc')},
    {'section': 'compromise.pc', 'group': 'rest 残り8パターン',
     'rows': _b('---------- iiiijjzooc cllljzzooc clccsscccc cccsszcccc ccccjccccc')},
    {'section': 'compromise.pc', 'group': 'rest 残り8パターン',
     'rows': _b('---------- llsiiiiooc clsstttooc clccjjcccc cccsjtcccc ccccjccccc')},
    {'section': 'compromise.pc', 'group': 'rest 残り8パターン',
     'rows': _b('---------- lliiiizooc cltttzzooc clccjjcccc ccctjzcccc ccccjccccc')},
    {'section': 'compromise.pc', 'group': 'rest 残り8パターン',
     'rows': _b('---------- llsjjjzooc clssizzooc clccizcccc cccsijcccc cccciccccc')},
    {'section': 'compromise.pc', 'group': 'rest 残り8パターン',
     'rows': _b('---------- lljtttzooc cljjjzzooc clccsscccc cccsszcccc cccctccccc')},
    {'section': 'compromise.pc', 'group': 'rest 残り8パターン',
     'rows': _b('---------- llstttjjjc clssiiiijc clccoocccc cccsoocccc cccctccccc')},
    {'section': 'compromise.pc', 'group': 'rest 残り8パターン',
     'rows': _b('---------- llstttzooc clsstzzooc clccjjcccc cccsjzcccc ccccjccccc')},
    {'section': 'compromise.pc', 'group': 'rest 残り8パターン',
     'rows': _b('---------- tttjlllooc ciiiissooc ctccsscccc cccjjjcccc cccclccccc')},
]


#: Every node, in page order (the PC patterns are inserted after `2.ideal.after_tst` by `build`).
NODES: list[dict] = [
    {
        'id': 'overview.derivation_map',
        'bag': 0,
        'parent': None,
        'node_kind': 'image_only',
        'label_jp': 'はちみつ砲の派生概要図(簡単ver.)',
        'page_text': 'はちみつ砲の派生概要図(簡単ver.)',
        'image': 'img/honeycup1.png',
        'note': 'the derivation overview diagram (image, 簡単ver.)',
    },
    {
        'id': 'bag1.j_hold',
        'bag': 1,
        'parent': None,
        'locks': 6,
        'label_jp': '1巡目 (左: %Jホールド)',
        'label': "bag 1, J held (the page's left pattern)",
        'rows': _b('---------- ---------- -ss------- ssl----t-- lll-zzttoo iiii-zztoo'),
    },
    {
        'id': 'bag1.l_hold',
        'bag': 1,
        'parent': None,
        'locks': 6,
        'label_jp': '1巡目 (右: %Lホールド)',
        'label': "bag 1, L held (the page's right pattern)",
        'mirror_of': 'bag1.j_hold',
        'classifier_note': 'exactly bag1.j_hold mirrored with J<->L and S<->Z swapped (checked cell for cell); a mirror-aware classifier must treat it as the SAME node, not a second branch',
        'rows': _b('---------- ---------- -------zz- --t----jzz oottss-jjj ootss-iiii'),
    },
    {
        'id': 'bag1.j_right',
        'bag': 1,
        'parent': None,
        'locks': 7,
        'label_jp': '基本形 1 (%J右置き)',
        'label': 'bag 1, J placed on the right (drawn only as basic form 1)',
        'drawn_as': 'basic.1',
        'derivation': 'bag1.j_hold plus a 4-cell J at the right wall: exactly the cells the uppercase (held) J occupies in 2.ideal#3-#5 (checked)',
        'note': "the page's text says the later of J/L is held; this 7-lock board is drawn only in 基本形 and is not described as a variant in 1巡目とミノ順",
        'rows': _b('---------- ---------- ---------- ---------j -ss------j ssl----tjj lll-zzttoo iiii-zztoo'),
    },
    {
        'id': '2.ideal#1',
        'bag': 2,
        'parent': None,
        'base': 'bag1.j_hold',
        'spin': 'TST',
        'label_jp': '理想形 2巡目 1',
        'label': 'ideal bag 2, variant 1 (held J on the left)',
        'held_j_side': 'left',
        'condition': None,
        'condition_note': 'the page gives one shared sentence for all five (ミノ順に応じて) and no per-variant order condition; which variant is built is read off the board, not off a stated condition',
        'rows': _b('---------- iiii------ JJss--jj-- Jss---jlll Jcc-zzjloo ccc--zzcoo ccc-cccccc cccc-ccccc'),
        'group': '2.ideal',
        'variant': 1,
        'spin_board': '2.ideal.tst',
    },
    {
        'id': '2.ideal#2',
        'bag': 2,
        'parent': None,
        'base': 'bag1.j_hold',
        'spin': 'TST',
        'label_jp': '理想形 2巡目 2',
        'label': 'ideal bag 2, variant 2 (held J on the left)',
        'held_j_side': 'left',
        'condition': None,
        'condition_note': 'the page gives one shared sentence for all five (ミノ順に応じて) and no per-variant order condition; which variant is built is read off the board, not off a stated condition',
        'rows': _b('---------- iiii------ JJss--lj-- Jss---ljjj Jcc-zzlloo ccc--zzcoo ccc-cccccc cccc-ccccc'),
        'group': '2.ideal',
        'variant': 2,
        'spin_board': '2.ideal.tst',
    },
    {
        'id': '2.ideal#3',
        'bag': 2,
        'parent': None,
        'base': 'bag1.j_hold',
        'spin': 'TST',
        'label_jp': '理想形 2巡目 3',
        'label': 'ideal bag 2, variant 3 (held J on the right)',
        'held_j_side': 'right',
        'condition': None,
        'condition_note': 'the page gives one shared sentence for all five (ミノ順に応じて) and no per-variant order condition; which variant is built is read off the board, not off a stated condition',
        'rows': _b('---------- iiii------ jjss--oo-- jss---oolJ jcc-zzlllJ ccc--zzcJJ ccc-cccccc cccc-ccccc'),
        'group': '2.ideal',
        'variant': 3,
        'spin_board': '2.ideal.tst',
    },
    {
        'id': '2.ideal#4',
        'bag': 2,
        'parent': None,
        'base': 'bag1.j_hold',
        'spin': 'TST',
        'label_jp': '理想形 2巡目 4',
        'label': 'ideal bag 2, variant 4 (held J on the right)',
        'held_j_side': 'right',
        'condition': None,
        'condition_note': 'the page gives one shared sentence for all five (ミノ順に応じて) and no per-variant order condition; which variant is built is read off the board, not off a stated condition',
        'rows': _b('---------- illl------ ilss--jj-- iss---jooJ icc-zzjooJ ccc--zzcJJ ccc-cccccc cccc-ccccc'),
        'group': '2.ideal',
        'variant': 4,
        'spin_board': '2.ideal.tst',
    },
    {
        'id': '2.ideal#5',
        'bag': 2,
        'parent': None,
        'base': 'bag1.j_hold',
        'spin': 'TST',
        'label_jp': '理想形 2巡目 5',
        'label': 'ideal bag 2, variant 5 (held J on the right)',
        'held_j_side': 'right',
        'condition': None,
        'condition_note': 'the page gives one shared sentence for all five (ミノ順に応じて) and no per-variant order condition; which variant is built is read off the board, not off a stated condition',
        'rows': _b('---------- ijjj------ iooj--ls-- ioo---lssJ icc-zzllsJ ccc--zzcJJ ccc-cccccc cccc-ccccc'),
        'group': '2.ideal',
        'variant': 5,
        'spin_board': '2.ideal.tst',
    },
    {
        'id': '2.ideal.tst',
        'bag': 2,
        'parent': '2.ideal',
        'label_jp': 'TST (消える段)',
        'label': 'ideal TST: generic illustration, cleared rows in C',
        'node_kind': 'illustration',
        'unmatchable': 'generic: every bag-2 cell drawn c/C, the three cleared rows in C (light grey); occupancy equals each 2.ideal#k board plus the U slot',
        'rows': _b('---------- cccc------ cccc--cc-- ccc---cccc CCCUCCCCCC CCCUUCCCCC CCCUCCCCCC cccc-ccccc'),
    },
    {
        'id': '2.ideal.after_tst',
        'bag': 2,
        'parent': '2.ideal',
        'label_jp': 'TST後',
        'label': 'ideal, after the TST',
        'node_kind': 'illustration',
        'note': 'all five 2.ideal#k boards collapse to this exact occupancy after the TST (checked by simulating the U slot fill and the 3-row clear)',
        'rows': _b('---------- ---------- ---------- ---------- cccc------ cccc--cc-- ccc---cccc cccc-ccccc'),
        'after_of': '2.ideal.tst',
    },
    {
        'id': '2.ideal.fire.pc5_image_1',
        'bag': 3,
        'parent': '2.ideal',
        'node_kind': 'image_only',
        'label_jp': 'はちみつ砲理想形 空中TSDからの5巡パフェ派生',
        'page_text': 'はちみつ砲理想形 空中TSDからの5巡パフェ派生',
        'image': 'img/td35honey1.png',
    },
    {
        'id': '2.ideal.fire.pc5_image_2',
        'bag': 3,
        'parent': '2.ideal',
        'node_kind': 'image_only',
        'label_jp': 'TDパフェ系テンプレ TSDからの5巡パフェ派生',
        'page_text': 'TDパフェ系テンプレ TSDからの5巡パフェ派生',
        'image': 'img/td35matome1.png',
        'note': 'a generic TD-PC-family chart, not specific to Honey Cup',
    },
    {
        'id': '2.ideal.fire.stmb_template',
        'bag': 3,
        'parent': '2.ideal',
        'base': '2.ideal.after_tst',
        'label_jp': 'STMB cave の形',
        'unmatchable': 'placeholder cells (p, magenta): any filling is allowed; also 9 rows > ROWS = 8',
        'rows': _b('---------- ---------- ---------- ---------- iiii---ppp cccc---ppp cccc--ccpp ccc---cccc cccc-ccccc'),
    },
    {
        'id': '2.ideal.fire.stmb_example',
        'bag': 3,
        'parent': '2.ideal.fire.stmb_template',
        'base': '2.ideal.after_tst',
        'label_jp': '例',
        'label': 'STMB cave example',
        'unmatchable': '9 rows > ROWS = 8',
        'rows': _b('---------- -------sll -------ssl ---zz---sl iiiizz-ooj cccc---ooj cccc--ccjj ccc---cccc cccc-ccccc'),
    },
    {
        'id': '2.ideal.ren4',
        'bag': 3,
        'parent': '2.ideal',
        'base': '2.ideal.after_tst',
        'label_jp': '4列REN派生',
        'label': 'centre 4-wide REN off the TSD (タネ3)',
        'text_verbatim': 'また、基本形に組んだ場合はTSDを打った残りの地形がタネ3となるのでそのまま中開けRENに派生することもできます。',
        'unmatchable': 'B cells (dark grey #444444, no legend on the page): OUR READING, the REN stack region / pieces still to come; 13 cells, not whole pieces',
        'rows': _b('---BBBB--- ---BBBB--- ccccBBB--- ccccBBcc-- cccUUUcccc ccccUccccc'),
    },
    {
        'id': '2.compromise',
        'bag': 2,
        'parent': None,
        'base': 'bag1.j_hold',
        'spin': 'TST',
        'label_jp': '妥協形 2巡目',
        'label': 'compromise bag 2',
        'condition_verbatim': '%L・%Z>%J・%Oの場合など、上の組み方ができない場合は以下のように組み、TSTを打ちます。',
        'condition': {
            'all': [
                {'before': ['L', 'J']},
                {'before': ['L', 'O']},
                {'before': ['Z', 'J']},
                {'before': ['Z', 'O']},
            ],
            'illustrative': True,
        },
        'condition_note': "「など」: an example, not the exhaustive trigger; the stated case is 'when the ideal shapes cannot be built'. %J here is OUR READING as the bag-2 J (the bag-1 J is held)",
        'rows': _b('--------oo i-------oo i-ss--l-jj iss---l-jJ icc-zzlljJ ccc--zzcJJ ccc-cccccc cccc-ccccc'),
        'spin_board': '2.compromise.tst',
    },
    {
        'id': '2.compromise.tst',
        'bag': 2,
        'parent': '2.compromise',
        'label_jp': '妥協形 TST',
        'label': 'compromise with the TST slot and cleared rows highlighted',
        'node_kind': 'illustration',
        'note': 'same occupancy as 2.compromise plus the U slot (checked); cleared-row cells drawn in upper case (lighter shade)',
        'rows': _b('--------oo i-------oo i-ss--l-jj iss---l-jJ ICCUZZlljJ CCCUUZZCJJ CCCUCCCCCC cccc-ccccc'),
    },
    {
        'id': '2.compromise.tst_donate',
        'bag': 3,
        'parent': '2.compromise',
        'base': '2.compromise',
        'label_jp': '3巡目 - TSTドネイト',
        'label': 'compromise bag 3: TST donate, before',
        'condition_verbatim': 'また、%Tが遅いなどでパフェルートに行かない場合、%S>%Zであれば以下のようにドネイトを組むことで火力を維持しつつ綺麗に組み上げることができます。',
        'condition': {'all': [{'before': ['S', 'Z']}]},
        'rows': _b('---------- jj------oo j-----l-oo jUzzlllicc cUUzzssicc cUccsscicc ccc---cicc cccc-ccccc'),
    },
    {
        'id': '2.compromise.tst_donate.after',
        'bag': 3,
        'parent': '2.compromise.tst_donate',
        'base': '2.compromise.tst_donate',
        'label_jp': 'TSTドネイト → 後',
        'label': 'TST donate, after: a Z roof over the TSD slot',
        'rows': _b('---------- jj-------- js-----ioo jss---zioo ccs--zzicc c----zcicc cccUUUcccc ccccUccccc'),
    },
    {
        'id': '2.compromise.roof',
        'bag': 3,
        'parent': '2.compromise.tst_donate',
        'base': '2.compromise.tst_donate',
        'label_jp': '3巡目 (L屋根)',
        'label': 'after the TST donate, an L roof over the TSD slot (the page\'s second continuation)',
        'note': 'drawn as the second pair under 3巡目 - TSTドネイト; its c cells are exactly what the TST donate '
                'leaves (rule 3), so it continues the donate, beside tst_donate.after (the Z roof)',
        'text_verbatim': '%Zか%L屋根を付けてTSDを打ちつつ、綺麗な地形を保つことができます。',
        'rows': _b('---------- jj-------- js-----ioo jss----ioo ccsl---icc clll--cicc ccc---cccc cccc-ccccc'),
    },
    {
        'id': '2.compromise.roof.after',
        'bag': 3,
        'parent': '2.compromise.roof',
        'base': '2.compromise.roof',
        'label_jp': '→ (Z屋根)',
        'label': 'then a Z over the L roof, and the TSD fired',
        'note': 'drawn 6 rows high because it is the board AFTER the TSD: the L roof\'s bottom two rows held the '
                'TSD slot, and a T in it clears them (rule `continues` checks the slot is one T)',
        'rows': _b('---------- jj-------- js-----ioo jss---zioo ccsl-zzicc clll-zcicc'),
        'continues': {'cleared_below': 2},
    },
]


_PC_ROWS = [
    '---------- iiiillljjj cccclsszzj ccccsscczz ccctttcccc cccctccccc',
    '---------- iiiijjzsll ccccjzzssl ccccjzccsl ccctttcccc cccctccccc',
    '---------- iiiilllooj cccclssooj ccccssccjj ccctttcccc cccctccccc',
    '---------- iiiijjzlll ccccjzzloo ccccjzccoo ccctttcccc cccctccccc',
    '---------- iiiijjjsll ccccoojssl ccccooccsl ccctttcccc cccctccccc',
    '---------- iiiiloojjj ccccloozzj ccccllcczz ccctttcccc cccctccccc',
    '---------- iiiijsszzl ccccjjjlll ccccsscczz ccctttcccc cccctccccc',
    '---------- iiiijsslll ccccjjjloo ccccssccoo ccctttcccc cccctccccc',
    '---------- iiiiooljjj cccclllzzj ccccoocczz ccctttcccc cccctccccc',
    '---------- iiiijjjzzl ccccoojlll ccccoocczz ccctttcccc cccctccccc',
    '---------- iiiijjzlll ccccjzzloo ccccssccoo cccsszcccc ccccjccccc',
    '---------- iiiilllooj cccctttooj ccccssccjj cccsstcccc cccclccccc',
    '---------- iiiillljjj cccctttzzj ccccsscczz cccsstcccc cccclccccc',
    '---------- iiiitoojjj ccccsoozzj ccccsscczz cccttscccc cccctccccc',
    '---------- iiiitoozzl ccccsoolll ccccsscczz cccttscccc cccctccccc',
]


_PC_META = [
    {'pieces': 'ijlstz', 'missing': 'o'},
    {'pieces': 'ijlstz', 'missing': 'o'},
    {'pieces': 'ijlost', 'missing': 'z'},
    {'pieces': 'ijlotz', 'missing': 's'},
    {'pieces': 'ijlost', 'missing': 'z'},
    {'pieces': 'ijlotz', 'missing': 's'},
    {'pieces': 'ijlstz', 'missing': 'o'},
    {'pieces': 'ijlost', 'missing': 'z'},
    {'pieces': 'ijlotz', 'missing': 's'},
    {'pieces': 'ijlotz', 'missing': 's'},
    {'pieces': 'ijlosz', 'missing': 't'},
    {'pieces': 'ijlost', 'missing': 'z'},
    {'pieces': 'ijlstz', 'missing': 'o'},
    {'pieces': 'ijostz', 'missing': 'l'},
    {'pieces': 'ilostz', 'missing': 'j'},
]

#: several bag-2 boards that share ONE bag-3 list: the list's `parent` names the group, and each
#: member names it in `group`. `drawn` is the page's own count of the forms, not derived.
GROUPS = [
    {'id': '2.ideal', 'heading': '理想形 2巡目',
     'verbatim': '2巡目はホールドしてあるミノ順に応じて%Jも含めて基本的に以下の形のいずれかに積みます。',
     'after_verbatim': 'いずれかの形に組むことで必ずTSTを打つことでできます。',
     'hedge': '「基本的に」: the page hedges, so a bag 2 off these five is not off the route by the page\'s own words',
     'drawn': 5},
]

#: the PC list. `shown` / `rest_stated` are the page's own split (「残りNパターン」), so the drawn count
#: is checked against two things the page says, not one.
LISTS = [
    {'id': '2.ideal.pc', 'parent': '2.ideal', 'heading': '3巡目 - パフェ狙い',
     'stated_pattern_count': 14, 'shown': 5, 'rest_stated': 10, 'complete': True,
     'after_pc_verbatim': '8段パフェを取った後は DPC や 3回目パフェ を狙うことができます。'},
]

#: The page's content that has no board. Identified by reading the page; `--html-dir` checks each
#: node's `page_text` is still on it.
NON_BOARD = {
    'overview.derivation_map': 'image_only',
    '2.ideal.fire.pc5_image_1': 'image_only',
    '2.ideal.fire.pc5_image_2': 'image_only',
}


def _pattern_nodes() -> list[dict]:
    out = []
    for lst in LISTS:
        for i, (text, meta) in enumerate(zip(_PC_ROWS, _PC_META), 1):
            out.append({'id': f'{lst["id"]}#{i}', 'bag': 3, 'parent': lst['parent'],
                        'base': '2.ideal.after_tst', 'list': lst['id'], 'index': i,
                        'listed_under': 'shown' if i <= lst['shown'] else 'rest',
                        'label_jp': f'{lst["heading"]} {i}', **meta, 'rows': _b(text)})
    return out


#: The order boards appear on the page. `--html-dir` compares a snapshot against exactly this.
PAGE_ORDER = (
    ['basic.1', 'basic.2', 'basic.3', 'bag1.j_hold', 'bag1.l_hold']
    + [f'2.ideal#{k}' for k in range(1, 6)] + ['2.ideal.tst', '2.ideal.after_tst']
    + [f'2.ideal.pc#{i}' for i in range(1, 16)]
    + ['2.ideal.fire.stmb_template', '2.ideal.fire.stmb_example', '2.ideal.ren4', '2.compromise',
       '2.compromise.tst', '2.compromise.tst_donate', '2.compromise.tst_donate.after', '2.compromise.roof',
       '2.compromise.roof.after']
)

#: the list-node flags, computed from the cells and re-checked by the gate
SLOT_FLAGS = {'has_u_slot': lambda rows: t_slot(rows) is not None,
              't_in_tsd_slot': lambda rows: t_slot(rows, 't') == 'flat'}


def build() -> dict:
    nodes = copy.deepcopy(NODES)
    at = next(i for i, n in enumerate(nodes) if n['id'] == '2.ideal.after_tst') + 1
    nodes[at:at] = _pattern_nodes()
    for n in nodes:
        if 'list' in n:
            for k, fn in SLOT_FLAGS.items():
                n[k] = fn(n['rows'])
    lists = []
    for lst in LISTS:
        drawn = sum(1 for n in nodes if n.get('list') == lst['id'])
        lists.append({**lst, 'drawn': drawn})
    return {
        'schema': 'honeycup-routes/1',
        'source': SOURCE,
        'terms': TERMS,
        'legend': LEGEND,
        'quotes': QUOTES,
        'bag1': BAG1,
        'basic_form': BASIC_FORM,
        'groups': GROUPS,
        'lists': lists,
        'known_discrepancies': KNOWN_DISCREPANCIES,
        'html_comment_boards': {**HTML_COMMENT_BOARDS_NOTE, 'boards': HTML_COMMENT_BOARDS_LIST},
        'page_order': PAGE_ORDER,
        'nodes': nodes,
    }


# ── はちみつ砲's own rules, and its half of the shared gate ────────────────────────────────────────
def _honeycup_checks(data: dict, ctx: dict) -> tuple[list[str], set[str]]:
    """The rules only this page needs, and the source discrepancies they measure."""
    bad: list[str] = []
    found: set[str] = set()
    boards, by_id, groups = ctx['boards'], ctx['by_id'], ctx['groups']
    nodes = data.get('nodes', [])

    # the bag-1 side rule is rendered, never evaluated: its pieces must still be pieces
    side = data.get('bag1', {}).get('side', {})
    if sorted(side.get('later_of', [])) != ['J', 'L'] or side.get('is') != 'held':
        bad.append('bag1-side: the side rule no longer names J and L, the later one held')
    hf = data.get('bag1', {}).get('hold_free', {})
    if hf.get('applies_to') not in by_id or any(p not in RT.PIECES for p in hf.get('before', [])):
        bad.append('bag1-side: the hold-free order names something that is not a node / piece')

    # the right bag-1 board is the left one mirrored: one shape, not two (rule `mirror-of` checks it)
    if any(n.get('mirror_of') and 'rows' in n and n['mirror_of'] in boards
           and bottom(n['rows'], RT.ROWS) == mirror(bottom(boards[n['mirror_of']], RT.ROWS)) for n in nodes):
        found.add('bag1.right:mirror')

    # a group's forms share ONE occupancy, so colour decides between them
    for g in groups.values():
        members = [n for n in nodes if n.get('group') == g['id'] and 'rows' in n]
        occs = {tuple(RT.occ(bottom(n['rows'], RT.ROWS))) for n in members}
        if len(occs) != 1:
            bad.append(f'group: the forms of {g["id"]} no longer share one occupancy ({len(occs)} kinds)')
        if members and all(n.get('condition') is None for n in members):
            found.add(f'{g["id"]}.bag2:no_conditions')

    # the PC list's sentence says TSD; a pattern without the T in the TSD slot contradicts it
    quote = next((q for q in data.get('quotes', []) if q['id'] == '2.ideal.pc'), None)
    pats = [n for n in nodes if n.get('list') == '2.ideal.pc']
    if quote and 'TSD' in quote['verbatim'] and any(not n.get('t_in_tsd_slot') for n in pats):
        found.add('2.ideal.pc:no_tsd')

    # an illustration's highlight: every cell in the rows its spin clears is shaded (upper case)
    for n in nodes:
        if n.get('node_kind') != 'illustration' or 'U' not in ''.join(n.get('rows', [])):
            continue
        filled = [r.replace('U', 't') for r in n['rows']]
        cleared = [r for r in filled if EMPTY not in r]
        if any(ch.islower() and ch != 't' for r in cleared for ch in r):
            found.add(f'{n["id"]}:highlight')

    # the 3-row TST every ideal form fires is the one the PC list's lines count
    after = by_id.get('2.ideal.after_tst', {})
    if after.get('after_of') in boards and after_spin(boards[after['after_of']])[1] != 3:
        bad.append('tst: 2.ideal.tst does not clear 3 rows')
    return bad, found


SPEC = RT.TranscriptionSpec(
    out=OUT, build=build, alphabet=ALPHABET, non_board=NON_BOARD,
    harddrop={'key': 'honey_cup', 'node': 'bag1.j_right'},
    board_kinds=frozenset({'illustration'}),
    pc_lines=8, prior_letters='',
    upper_groups={'J': 'separate', 'I': 'merge', 'Z': 'merge'},
    slot_flags=SLOT_FLAGS, occupancy_class_parents=1, extra_checks=_honeycup_checks,
    placeholders='pB')


def verify(data: dict) -> list[str]:
    return RT.verify(data, SPEC)


def drift(data: dict) -> list[str]:
    return RT.drift(data, SPEC)


# ── selftest ───────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    """A gate nothing can fail is decorative. Plant one defect per rule, each in a named はちみつ砲 id."""

    def drop_pattern(d):
        d['nodes'] = [n for n in d['nodes'] if n['id'] != '2.ideal.pc#15']

    def flip_hold(d):
        setcell(node(d, 'bag1.j_hold')['rows'], 2, 1, '-')           # one s cell of bag 1 emptied

    def break_mirror(d):
        setcell(node(d, 'bag1.l_hold')['rows'], 2, 7, '-')           # one z cell of the mirror

    def no_collapse(d):
        setcell(node(d, '2.ideal#2')['rows'], 6, 3, 'c')             # the TST slot filled

    def ghost_group(d):
        node(d, '2.ideal#4')['group'] = '2.ideal.nowhere'

    def b_cell(d):
        setcell(node(d, '2.compromise.tst_donate')['rows'], 0, 0, 'B')

    def flag_flip(d):
        n = node(d, '2.ideal.pc#12')
        n['t_in_tsd_slot'] = not n['t_in_tsd_slot']

    def drop_discrepancy(d):
        d['known_discrepancies'] = [x for x in d['known_discrepancies'] if x['id'] != '2.ideal.pc:no_tsd']

    def recolour_form(d):
        setcell(node(d, '2.ideal#5')['rows'], 1, 1, 'i')              # a j cell drawn as i

    def shift_right(d):
        n = node(d, 'bag1.j_right')
        n['rows'] = ['-' + r[:-1] for r in n['rows']]
        d['basic_form'][0]['rows'] = list(n['rows'])

    def dup_form(d):
        node(d, '2.ideal#2')['rows'] = list(node(d, '2.ideal#1')['rows'])

    def basic_off(d):
        setcell(d['basic_form'][1]['rows'], 3, 9, 'z')                # the grey held J drawn z

    def tall(d):
        node(d, '2.compromise.roof')['rows'].insert(0, 'i---------')

    def no_reason(d):
        node(d, '2.ideal.ren4')['unmatchable'] = ''

    def c_cells(d):
        setcell(node(d, '2.compromise.tst_donate.after')['rows'], 7, 4, 'c')

    def lost_image(d):
        d['nodes'] = [n for n in d['nodes'] if n['id'] != '2.ideal.fire.pc5_image_2']

    def wrong_tst(d):
        node(d, '2.ideal.after_tst')['after_of'] = '2.compromise.tst'

    def side_rule(d):
        d['bag1']['side']['later_of'] = ['J', 'O']

    def no_slot(d):
        setcell(node(d, '2.compromise.roof')['rows'], 6, 3, 'c')      # the TSD slot under the roof filled

    def roof_lost(d):
        setcell(node(d, '2.compromise.roof.after')['rows'], 5, 1, '-')  # an L cell of the roof gone

    mutants = [
        (drop_pattern, 'a dropped PC pattern', 'list-count:'),
        (flip_hold, 'one cell of bag1.j_hold flipped', 'bag2-base:'),
        (break_mirror, 'the L-hold board no longer the J-hold board mirrored', 'mirror-of:'),
        (no_collapse, 'a 2.ideal form that no longer collapses to after_tst', 'spin-board:'),
        (ghost_group, 'a group no node declares', 'grammar:'),
        (b_cell, 'a B cell on a board that is not the REN one', 'placeholder:'),
        (flag_flip, 'a t_in_tsd_slot flag flipped', 'grammar:'),
        (drop_discrepancy, 'a dropped known discrepancy', 'discrepancy:'),
        (recolour_form, 'one cell of a 2.ideal form recoloured', 'discrepancy:'),
        (shift_right, 'the harddrop board shifted one column', 'harddrop:'),
        (dup_form, 'two 2.ideal forms made equal by colour', 'distinct:'),
        (basic_off, 'a 基本形 board off its node', 'basic-form:'),
        (tall, 'a 9-row board not marked unmatchable', 'grammar:'),
        (no_reason, 'an unmatchable node with no reason', 'grammar:'),
        (c_cells, 'a c cell where the donate leaves none', 'c-cells:'),
        (lost_image, 'a deleted image node', 'non-board:'),
        (wrong_tst, 'after_tst read off the wrong spin', 'after-of:'),
        (side_rule, 'the bag-1 side rule naming another piece', 'bag1-side:'),
        (no_slot, 'the roof with no T slot left to clear', 'continues:'),
        (roof_lost, 'the board after the roof no longer containing it', 'continues:'),
    ]
    spec_mutants = [
        (lambda s: RT.TranscriptionSpec(**{**s.__dict__, 'harddrop': {'key': 'stray_cannon', 'node': 'bag1.j_right'}}),
         'the harddrop key changed to another opener', 'harddrop:'),
    ]
    return RT.run_selftest(SPEC, mutants, {'board': ('ccccUccccc', 'cccc-ccccc'),
                                           'text': ('派生概要図', '派生概略図'),
                                           'hand_edit': '2.compromise', 'quote': '2.ideal.pc'},
                           spec_mutants)


def main() -> int:
    return RT.main(SPEC, selftest, __doc__)


if __name__ == '__main__':
    raise SystemExit(main())

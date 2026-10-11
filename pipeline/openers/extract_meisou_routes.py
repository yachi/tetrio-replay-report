"""Transcribe shiwehi.com's 迷走砲 (Stray Cannon) route page into `meisou-routes.json`.

    python3 -m pipeline.openers.extract_meisou_routes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_meisou_routes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_meisou_routes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_meisou_routes --html-dir <dir> --write  # ...and rewrite

WHY THIS IS A THIRD FILE and not more rows in `wiki-openers.json`. That file feeds sixteen
byte-identity-gated `sim/opener-facts.json` artefacts, and it answers one question about one lock
count ("is the opening board this opener's field"). The 迷走砲 page is a ROUTE: two bag-1 shapes,
five bag-2 branches chosen by piece order, and up to sixteen bag-3 finishes under each. That is a
tree, and a tree has properties a flat list of fields does not — every child is built on what its
parent leaves after its T-spin, and that is checkable without the page.

WHERE THE TRANSCRIPTION COMES FROM, AND WHY THE PAGE IS NOT COMMITTED. `SPEC` below is a literal,
hand-checked transcription. The page itself cannot be fetched from CI (plain curl gets a 403
through the proxy; the only working route was an MCP `web_fetch`, which renders the page to
markdown), so what is committed is the transcription plus the sha256 of the markdown snapshot it
was checked against. That hash is NOT re-verifiable in CI — it names the snapshot, it does not
reproduce it. Whoever refetches saves the markdown as `<dir>/meisou.md` and runs `--html-dir`:
every board drawn on the page is located in page order and compared with `page_order`, so a
redrawn, added or removed diagram fails rather than being silently absent.

Two transcriptions agree on all 54 boards in page order: the scratch transcription the plan was
written from, and the snapshot this file was checked against on 2026-10-11. The number is not
typed anywhere the gate reads; it is `len(page_order)`, and `--html-dir` re-derives it from the page.

WHAT IS AN INFERENCE. Two things here are this repo's reading, not the page's, and both are
flagged in the JSON rather than in prose only:

  * upper-case `Z` has no legend on the page. It is read as the bag-1 Z drawn in colour inside a
    bag-2 diagram. Rule 3 checks the reading mechanically: wherever `Z` appears, its cells are
    exactly the bag-1 base's own `z` cells.
  * `bag1.z_left` is not drawn on its own. It is DERIVED from the 2.z_left board: z_hold's 24 cells
    plus the four `Z` cells. Rule 3 checks both halves of that.

WHAT IS NOT COMMITTED: the merits/demerits prose, the HTML, the images. Only the boards, the short
condition lines, and the page's own figures with their sentence (attributed, never recomputed).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'meisou-routes.json'
WIKI = HERE / 'wiki-openers.json'

WIDTH = 10
#: `match.ts`'s `ROWS`. A board taller than this cannot be compared by the classifier at all.
ROWS = 8
EMPTY = '-'
ALPHABET = frozenset('-ijlostzcUZp')
PIECES = frozenset('IJLOSTZ')
NODE_KINDS = frozenset({'image_only', 'text_only'})
SWAP = {'l': 'j', 'j': 'l', 's': 'z', 'z': 's', 'Z': 'S'}


# ── the transcription ──────────────────────────────────────────────────────────────────────────
def _b(text: str) -> list[str]:
    """A board literal: one row per line, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/meisou.php',
    'title': '迷走砲(Stray Cannon)',
    'updated': '2026-04-11',
    'fetched': '2026-10-11',
    'fetch_method': 'mcp__Parallel_Search__web_fetch with full_content=true, which renders the page '
                    'to markdown (a leading "-" on a board row comes back escaped as "\\-" and is '
                    'unescaped). Plain curl through the proxy gets HTTP 403, so CI cannot refetch.',
    'snapshot_file': 'meisou.md',
    'snapshot_sha256': 'a224fb464f8c566fdcd7f28e7d794e15645897388a606fad110beac45f23a09e',
    'snapshot_bytes': 10088,
    'snapshot_note': 'sha256 of the markdown snapshot this transcription was checked against. Not '
                     're-verifiable in CI: the page is not committed and cannot be fetched there. '
                     'Re-check with --html-dir after any refetch; a renderer change alone will move '
                     'the hash, so a moved hash means "read the board diff", not "the page changed".',
    'decorative_images': ['迷走砲(Stray Cannon)タイトル画像'],
}

TERMS = {
    'url': 'https://shiwehi.com/tetris/explanation/terms.php',
    'dated': '2023-05-12',
    'read': '2026-10-11',
    'allows': 'non-commercial HP/blog use without contacting the admin',
    'excludes': '営利目的 sites (e.g. Google AdSense)',
    'requests': 'URL credit or a heads-up',
    'how_met': 'source link in every page header; no ads on GitHub Pages',
}

LEGEND = {
    'orientation': 'rows listed top to bottom exactly as the page draws them; 10 columns, column 0 '
                   'is the left wall. Heights differ between diagrams (some omit empty top rows), '
                   'so every comparison aligns boards at the BOTTOM row',
    '-': 'empty',
    'i o t s z j l': 'a cell of that piece',
    'c': 'a cell filled before this diagram (earlier bags), drawn grey on the page',
    'U': 'the T-spin slot: where the T goes',
    'Z': 'OUR READING, no legend on the page: the bag-1 Z drawn in colour inside a bag-2 diagram',
    'p': 'placeholder: any filling (only in the STMB cave template)',
    '%X': "the page's notation for the X piece; '%J>%O' means J comes before O",
}

#: the page's own figures, each with the sentence it sits in. Attributed, never recomputed.
QUOTES = [
    {'id': 'overview.max_damage', 'figure': '21ライン',
     'verbatim': '最大TST→TSD→8段パフェで21ラインという高火力を狙うことができる。'},
    {'id': '2.ideal.pc', 'figure': '14パターン：パフェ率97.94%',
     'verbatim': '3巡目はTSDを打ちつつパフェを狙います。(14パターン：パフェ率97.94%)'},
    {'id': '2.normal_OS.pc', 'figure': 'TSDPC率18.10%,TSSPC率42.86%',
     'verbatim': '3巡目はTSDを打ち、運が良ければパフェを狙うことができます。'
                 '(TSDPC率18.10%,TSSPC率42.86%)'},
    {'id': '2.i_early.pc', 'figure': '12パターン85.28%',
     'verbatim': '3巡目はTSDを打ち、運が良ければパフェを狙うことができます。(12パターン85.28%)'},
    {'id': '2.z_left.pc', 'figure': '9パターン：パフェ率84.25%',
     'verbatim': '3巡目はTSDを打ちつつパフェを狙います。(9パターン：パフェ率84.25%)'},
]

BAG1 = {
    'requires_verbatim': '1巡目の組み方は上図の通りで、%Lが早い必要があります。',
    'requires': {'early': 'L'},
    'hold_free_verbatim': '%J>%Z',
    'hold_free': {'before': ['J', 'Z']},
    'z_note_verbatim': 'パフェ重視の場合は%Zをホールドしておきたいですが、'
                       '拘らない場合には下図の位置に置いてしまって構いません。',
}

#: The three-diagram sequence under 基本形. Each must equal the node it names (bottom-aligned).
BASIC_FORM = [
    {'id': 'basic.1', 'same_as': 'bag1.z_right', 'rows': _b('''
        ---------- ---------- ---------- ---------- i------zz- ils-t--jzz ilsstt-joo illst-jjoo''')},
    {'id': 'basic.2', 'same_as': '2.ideal', 'rows': _b('''
        ---------- ------ooji s--z--ooji sszz---jji cszlllUcci ccclcUUccc ccccccUccc ccccc-cccc''')},
    {'id': 'basic.3', 'same_as': '2.ideal.pc#3', 'rows': _b('''
        ---------- ---------- ---------- jjjslliiii zzjsslcccc czzcslcccc ccccUUUccc cccccUcccc''')},
]

_PC_ROWS = {
    '2.ideal.pc': [
        '---------- jjjllliiii zzjloocccc czzcoocccc ccccUUUccc cccccUcccc',
        '---------- llljjjiiii loozzjcccc cooczzcccc ccccUUUccc cccccUcccc',
        '---------- jjjslliiii zzjsslcccc czzcslcccc ccccUUUccc cccccUcccc',
        '---------- slloojiiii ssloojcccc cslcjjcccc ccccUUUccc cccccUcccc',
        '---------- oojslliiii oojsslcccc cjjcslcccc ccccUUUccc cccccUcccc',
        '---------- slljjjiiii sslzzjcccc cslczzcccc ccccUUUccc cccccUcccc',
        '---------- oosslliiii oojjjlcccc csscjlcccc ccccUUUccc cccccUcccc',
        '---------- zzljooiiii llljjjcccc czzcoocccc ccccUUUccc cccccUcccc',
        '---------- slljooiiii ssljjjcccc cslcoocccc ccccUUUccc cccccUcccc',
        '---------- oojslliiii oojsslcccc cjjczzcccc ccccszzccc ccccclcccc',
        '---------- oojjjziiii oosszzcccc cssczUcccc ccccjUUccc cccccUcccc',
        '---------- llljjjiiii lootttcccc cooczzcccc cccctzzccc cccccjcccc',
        '---------- slljjjiiii ssltttcccc cslczzcccc cccctzzccc cccccjcccc',
        '---------- sllootiiii ssloozcccc cslczzcccc cccczttccc ccccctcccc',
        '---------- oojjjtiiii oossjzcccc cssczzcccc cccczttccc ccccctcccc',
        '---------- oossltiiii oolllzcccc czzczzcccc cccczttccc ccccctcccc',
    ],
    '2.normal_OS.pc': [
        'iccslloojj iccssloojc icccslccjc icccUUUccc cccccUcccc',
        'icczzloojj iccllloojc iccczzccjc icccUUUccc cccccUcccc',
    ],
    '2.i_early.pc': [
        '---------- ijjslloocc ijcssloocc ijccslcccc icccUUUccc cccccUcccc',
        '---------- ijjzzloocc ijcllloocc ijcczzcccc icccUUUccc cccccUcccc',
        '---------- ijjoosslcc ijcoolllcc ijccsscccc icccUUUccc cccccUcccc',
        '---------- llloojjjcc lzcoossjcc zzccsscccc zcccUUUccc cccccUcccc',
        '---------- lllzzjjjcc oociiiijcc oocczzcccc lccctttccc ccccctcccc',
        '---------- ijjootttcc ijcoolllcc ijccslcccc icccsstccc cccccscccc',
        '---------- ijjslloocc ijcssloocc ijcczzcccc icccszzccc ccccclcccc',
        '---------- ijjoolllcc ijcoozsscc ijcczzcccc iccczssccc ccccclcccc',
        '---------- ijjstttlcc ijcsslllcc ijcczzcccc icccszzccc ccccctcccc',
        '---------- ijjstttzcc ijcsstzzcc ijccllcccc icccslzccc ccccclcccc',
        '---------- jjjiiiizcc oocjjjzzcc ooccsjcccc lcccsszccc cccccscccc',
        '---------- lllstttzcc oocssjzzcc ooccsjcccc lcccjjzccc ccccctcccc',
    ],
    '2.z_left.pc': [
        '---------- jjciiiiloo jcczzllloo jccczzcccc ccccUUUccc cccccUcccc',
        '---------- jjcooiiiil jccoosslll jcccsscccc ccccUUUccc cccccUcccc',
        '---------- jjcsiiiioo jccssllloo jcccslcccc ccccUUUccc cccccUcccc',
        '---------- jjciiiizoo jcctttzzoo jcccllcccc cccctlzccc ccccclcccc',
        '---------- jjcsiiiioo jccsstttoo jcccllcccc ccccsltccc ccccclcccc',
        '---------- jjcslllzoo jccssizzoo jccclicccc ccccsizccc cccccicccc',
        '---------- jjcstttloo jccssllloo jccczzcccc ccccszzccc ccccctcccc',
        '---------- jjcstttzoo jccsstzzoo jcccllcccc ccccslzccc ccccclcccc',
        '---------- jjcsiiiioo jccssllloo jccczzcccc ccccszzccc ccccclcccc',
    ],
}

#: the PC lists. `shown` / `rest_stated` are the page's own split (「残りNパターン」), so the
#: drawn count is checked against two things the page says, not one.
LISTS = [
    {'id': '2.ideal.pc', 'parent': '2.ideal', 'heading': '3巡目 - パフェ狙い',
     'stated_pattern_count': 14, 'shown': 6, 'rest_stated': 10, 'complete': True,
     'after_pc_verbatim': '8段パフェを取った後はDPCや3回目パフェを狙うことができます。'},
    {'id': '2.normal_OS.pc', 'parent': '2.normal_OS', 'heading': '3巡目 TSD→パフェ',
     'stated_pattern_count': None, 'shown': 2, 'rest_stated': 0, 'complete': False,
     'list_note_verbatim': '等'},
    {'id': '2.i_early.pc', 'parent': '2.i_early', 'heading': '3巡目 TSD→パフェ',
     'stated_pattern_count': 12, 'shown': 5, 'rest_stated': 7, 'complete': True,
     'after_pc_verbatim': '8段パフェを取った後はDPCや3回目パフェを狙うことができます。'},
    {'id': '2.z_left.pc', 'parent': '2.z_left', 'heading': '3巡目 TSD→パフェ',
     'stated_pattern_count': 9, 'shown': 3, 'rest_stated': 6, 'complete': True,
     'after_pc_verbatim': '8段パフェを取った後はDPCや3回目パフェを狙うことができます。'},
]

#: Where the page disagrees with itself. Rule 5 re-derives this set from LISTS and the drawn
#: patterns; a new entry fails until it is read and named here.
KNOWN_DISCREPANCIES = [
    {'id': '2.ideal.pc:stated_vs_drawn',
     'what': 'the page states 14 patterns and draws 16 (6 shown + 残り10); all 16 are kept'},
    {'id': '2.normal_OS.pc:non_exhaustive',
     'what': 'the O>S PC list ends in 「等」 and states no pattern count; its 2 diagrams are '
             'examples, so a PC off this list is not off the page\'s route'},
    {'id': '2.ideal.pc#16:colour',
     'what': 'z has 6 cells and s 2: the zz at row 2 (from the bottom), columns 1-2, and the ss at '
             'row 4, columns 2-3, are one S across the cleared row between them (snapshot line 232)'},
    {'id': '2.i_early.pc#11:colour',
     'what': 'j has 7 cells and l 1: the jjj at row 4 (from the bottom), columns 0-2, and the l at '
             'row 1, column 0, are one L across the two cleared rows between them (snapshot line 443)'},
]

#: The page's content that has no board: images, the video, and the one route the page names in
#: text and never draws. Identified by reading the page; nothing on disk can derive it, so it is
#: a NAMED list, and `--html-dir` checks each node's `page_text` still appears on the page.
NON_BOARD = {
    'overview.derivation_map': 'image_only',
    'overview.video': 'image_only',
    '2.ideal.l_rotate_in': 'image_only',
    '2.ideal.ren4': 'text_only',
    '2.ideal.fire': 'image_only',
}

#: Every node, in page order. Board nodes carry `rows`; non-board nodes carry `node_kind`.
NODES: list[dict] = [
    {'id': 'overview.derivation_map', 'bag': 0, 'parent': None, 'node_kind': 'image_only',
     'label_jp': '迷走砲の派生概要図', 'page_text': '迷走砲の派生概要図', 'note': 'the derivation overview diagram (image)'},
    {'id': 'overview.video', 'bag': 0, 'parent': None, 'node_kind': 'image_only',
     'label_jp': '解説動画', 'page_text': '解説動画', 'note': 'an embedded explanation video by くいものくれ'},
    {'id': 'bag1.z_hold', 'bag': 1, 'parent': None, 'locks': 6,
     'label_jp': '1巡目 (%Zホールド)', 'label': 'bag 1, Z not placed (the page\'s hold variant)',
     'rows': _b('---------- ---------- i--------- ils-t--j-- ilsstt-joo illst-jjoo')},
    {'id': 'bag1.z_right', 'bag': 1, 'parent': None, 'locks': 7,
     'label_jp': '1巡目 (%Z右置き)', 'label': 'bag 1, Z placed on the right',
     'rows': _b('---------- ---------- i------zz- ils-t--jzz ilsstt-joo illst-jjoo')},
    {'id': 'bag1.z_left', 'bag': 1, 'parent': None, 'locks': 7, 'derived': True,
     'derived_from': '2.z_left',
     'derivation': 'bag1.z_hold plus the four upper-case Z cells of the 2.z_left board; the page '
                   'draws this bag-1 shape only inside its bag-2 diagram',
     'label_jp': '1巡目 (%Z左置き)', 'label': 'bag 1, Z placed on the left (derived)',
     'rows': _b('---------- zz-------- izz------- ils-t--j-- ilsstt-joo illst-jjoo')},
    {'id': '2.ideal', 'bag': 2, 'parent': None, 'base': 'bag1.z_right', 'spin': 'TST',
     'label_jp': '理想形', 'label': 'ideal',
     'condition_verbatim': '%J>%Oの場合に組むことができます。',
     'condition': {'all': [{'before': ['J', 'O']}]},
     'rows': _b('---------- ------ooji s--z--ooji sszz---jji cszlllUcci ccclcUUccc ccccccUccc '
                'ccccc-cccc')},
    {'id': '2.ideal.l_rotate_in', 'bag': 2, 'parent': '2.ideal', 'node_kind': 'image_only',
     'label_jp': '迷走砲のJミノの回転入れ', 'page_text': '迷走砲のJミノの回転入れ',
     'note': 'image; the text says the bag-2 %L can be rotated in after Z (左回転) while the image '
             'caption says Jミノ'},
    {'id': '2.ideal.ren4', 'bag': 3, 'parent': '2.ideal', 'node_kind': 'text_only',
     'label_jp': '中開け4列REN', 'page_text': '中開け4列RENにも派生できます',
     'text_verbatim': 'TST→TSD→8段パフェが理想ルートで、中開け4列RENにも派生できます。',
     'note': 'the page derives it in one sentence and draws no diagram'},
    {'id': '2.ideal.fire', 'bag': 3, 'parent': '2.ideal', 'node_kind': 'image_only',
     'label_jp': '3巡目 - 火力派生 5巡パフェ狙い',
     'page_text': 'TDパフェ系テンプレ TSDからの5巡パフェ派生',
     'text_verbatim': '%Tが遅い等でパフェを取らない場合等には、下図のように組むことで火力を維持しつつ'
                      '5巡パフェ(14段パフェ)を狙うことができます。',
     'note': 'the 5-bag PC shape exists only as an image (TDパフェ系テンプレ TSDからの5巡パフェ派生)'},
    {'id': '2.ideal.fire.stmb_template', 'bag': 3, 'parent': '2.ideal.fire', 'base': '2.ideal',
     'label_jp': 'STMB cave の形', 'unmatchable': 'placeholder cells (p): any filling is allowed',
     'rows': _b('---------- ---------- ppp---iiii ppp---cccc cppc--cccc cccc---ccc ccccc-cccc')},
    {'id': '2.ideal.fire.stmb_example', 'bag': 3, 'parent': '2.ideal.fire', 'base': '2.ideal',
     'label_jp': 'STMB cave の形 (例)',
     'unmatchable': '例: one arbitrary filling of the template\'s placeholder cells, so a match '
                    'would be a match to one illustration, not to the route (drawn 9 rows high, '
                    '8 under an empty top row)',
     'rows': _b('---------- jjz------- jzz------- jz---ss--- lll-ssiiii loo---cccc cooc--cccc '
                'cccc---ccc ccccc-cccc')},
    {'id': '2.normal_OS', 'bag': 2, 'parent': None, 'base': 'bag1.z_right', 'spin': 'TST',
     'label_jp': '通常形 %O>%S', 'label': 'normal, O before S',
     'condition_verbatim': '%O>%Jの場合には、%Oと%Sの順番によって下図の2パターンで組み分けることができます。'
                           ' / %O>%Sの場合',
     'condition': {'all': [{'before': ['O', 'J']}, {'before': ['O', 'S']}]},
     'rows': _b('-jj------- -js------i -jss--zz-i -oos---zzi coolllUcci ccclcUUccc ccccccUccc '
                'ccccc-cccc')},
    {'id': '2.normal_OS.tst_donate', 'bag': 3, 'parent': '2.normal_OS', 'base': '2.normal_OS',
     'label_jp': 'TSTドネイト', 'label': 'TST donate (no PC), before',
     'text_verbatim': 'もし%Tが遅い等でパフェを狙わない場合には、下記の様に組んでTSTドネイトを打って'
                      '火力を継続することができます。',
     'rows': _b('---------- -oo-----ll -ooj-----l iccjjjssUl icczzssUUc iccczzccUc iccc---ccc '
                'ccccc-cccc')},
    {'id': '2.normal_OS.tst_donate.after', 'bag': 3, 'parent': '2.normal_OS.tst_donate',
     'base': '2.normal_OS.tst_donate', 'label_jp': 'TSTドネイト → 後',
     'label': 'TST donate, after',
     'rows': _b('---------- --------ll ioo-----zl ioos---zzl iccss-jzcc icccs-jjjc ccccUUUccc '
                'cccccUcccc')},
    {'id': '2.normal_SO', 'bag': 2, 'parent': None, 'base': 'bag1.z_right', 'spin': 'TST',
     'label_jp': '通常形 %S>%O', 'label': 'normal, S before O',
     'condition_verbatim': '%O>%Jの場合には、%Oと%Sの順番によって下図の2パターンで組み分けることができます。'
                           ' / %S>%Oの場合',
     'condition': {'all': [{'before': ['O', 'J']}, {'before': ['S', 'O']}]},
     'rows': _b('---------- -joo-----i -joo--zz-i jjss---zzi csslllUZZi ccclcUUcZZ ccccccUccc '
                'ccccc-cccc')},
    {'id': '2.normal_SO.stsd', 'bag': 3, 'parent': '2.normal_SO', 'base': '2.normal_SO',
     'label_jp': 'STSD (パフェ無し)',
     'text_verbatim': '上図の形のようにTST→TSDからSTSDの形を組むことができます。(パフェ無し)',
     'rows': _b('---------- ---jj---s- iooj----ss iooj-zzlls iccc--zzlc iccc--cclc ccccUUUccc '
                'cccccUcccc')},
    {'id': '2.i_early', 'bag': 2, 'parent': None, 'base': 'bag1.z_right', 'spin': 'TST',
     'label_jp': '別パターン 2巡目%I早', 'label': 'I early in bag 2',
     'condition_verbatim': '2巡目に%Iが早い場合、上図のように組むこともできます。',
     'condition': {'early': 'I', 'note': 'the page gives no position threshold for "early"'},
     'rows': _b('--------jj --s-----ji --ss--zzji -oos---zzi coolllUcci ccclcUUccc ccccccUccc '
                'ccccc-cccc')},
    {'id': '2.z_left', 'bag': 2, 'parent': None, 'base': 'bag1.z_left', 'spin': 'TST',
     'label_jp': '別パターン 1巡目%z左置き', 'label': 'bag-1 Z placed on the left',
     'condition_verbatim': '%Zの置き場所が違うので使用頻度は低いですが、'
                           'パフェ率を高めたい場合には覚えておくと良いでしょう。',
     'condition': {'bag1': 'bag1.z_left'},
     'rows': _b('--z------- -zz------- -zoo--jjji ZZoo---sji cZZlllUssi ccclcUUcsi ccccccUccc '
                'ccccc-cccc')},
]


def _pattern_nodes() -> list[dict]:
    out = []
    for lst in LISTS:
        for i, text in enumerate(_PC_ROWS[lst['id']], 1):
            out.append({'id': f'{lst["id"]}#{i}', 'bag': 3, 'parent': lst['parent'],
                        'base': lst['parent'], 'list': lst['id'], 'index': i,
                        'listed_under': 'shown' if i <= lst['shown'] else 'rest',
                        'label_jp': f'{lst["heading"]} {i}', 'rows': _b(text)})
    return out


#: The order boards appear on the page. `--html-dir` compares a snapshot against exactly this.
PAGE_ORDER = (
    ['basic.1', 'basic.2', 'basic.3', 'bag1.z_hold', 'bag1.z_right', '2.ideal']
    + [f'2.ideal.pc#{i}' for i in range(1, 17)]
    + ['2.ideal.fire.stmb_template', '2.ideal.fire.stmb_example', '2.normal_OS',
       '2.normal_OS.pc#1', '2.normal_OS.pc#2', '2.normal_OS.tst_donate',
       '2.normal_OS.tst_donate.after', '2.normal_SO', '2.normal_SO.stsd', '2.i_early']
    + [f'2.i_early.pc#{i}' for i in range(1, 13)]
    + ['2.z_left'] + [f'2.z_left.pc#{i}' for i in range(1, 10)]
)


# ── board geometry ─────────────────────────────────────────────────────────────────────────────
def t_slot(rows: list[str]) -> str | None:
    """`flat` for the UUU-over-U TSD slot, `other` for any other U, None for none."""
    cells = [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == 'U']
    if not cells:
        return None
    by_row: dict[int, list[int]] = {}
    for r, c in cells:
        by_row.setdefault(r, []).append(c)
    if len(cells) == 4 and len(by_row) == 2:
        (ra, ca), (rb, cb) = sorted((r, sorted(cs)) for r, cs in by_row.items())
        if rb == ra + 1 and len(ca) == 3 and ca == [ca[0], ca[0] + 1, ca[0] + 2] and cb == [ca[1]]:
            return 'flat'
    return 'other'


def build() -> dict:
    nodes = copy.deepcopy(NODES) + _pattern_nodes()
    for n in nodes:
        if 'list' in n:
            slot = t_slot(n['rows'])
            n['has_u_slot'] = slot is not None
            n['has_tsd_slot'] = slot == 'flat'
    lists = []
    for lst in LISTS:
        drawn = sum(1 for n in nodes if n.get('list') == lst['id'])
        lists.append({**lst, 'drawn': drawn})
    return {
        'schema': 'meisou-routes/1',
        'source': SOURCE,
        'terms': TERMS,
        'legend': LEGEND,
        'quotes': QUOTES,
        'bag1': BAG1,
        'basic_form': BASIC_FORM,
        'lists': lists,
        'known_discrepancies': KNOWN_DISCREPANCIES,
        'page_order': PAGE_ORDER,
        'nodes': nodes,
    }


def bottom(rows: list[str], height: int) -> list[str]:
    """Strip leading empty rows, then pad (with empty rows on top) to `height`."""
    first = next((i for i, r in enumerate(rows) if r != EMPTY * WIDTH), len(rows))
    rows = rows[first:]
    return [EMPTY * WIDTH] * max(0, height - len(rows)) + rows


def mirror(rows: list[str]) -> list[str]:
    return [''.join(SWAP.get(c, c) for c in reversed(r)) for r in rows]


def occ(rows: list[str]) -> list[str]:
    return [''.join('#' if c != EMPTY else '.' for c in r) for r in rows]


def after_spin(rows: list[str]) -> tuple[list[str], int]:
    """Put the T into every U cell, clear full rows, and return (board, rows cleared)."""
    filled = [r.replace('U', 't') for r in rows]
    keep = [r for r in filled if EMPTY in r]
    cleared = len(filled) - len(keep)
    return [EMPTY * WIDTH] * cleared + keep, cleared


def cells(rows: list[str], pred) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if pred(ch)}


#: One drawing per piece, y-UP (x, y); every rotation is derived, never typed.
_PIECE_BASE = {'i': [(0, 0), (1, 0), (2, 0), (3, 0)], 'o': [(0, 0), (1, 0), (0, 1), (1, 1)],
               't': [(0, 0), (1, 0), (2, 0), (1, 1)], 's': [(0, 0), (1, 0), (1, 1), (2, 1)],
               'z': [(1, 0), (2, 0), (0, 1), (1, 1)], 'j': [(0, 0), (1, 0), (2, 0), (0, 1)],
               'l': [(0, 0), (1, 0), (2, 0), (2, 1)]}


def _norm(cs):
    mx, my = min(x for x, _ in cs), min(y for _, y in cs)
    return tuple(sorted((x - mx, y - my) for x, y in cs))


def _shapes(letter):
    out, cur = set(), _PIECE_BASE[letter]
    for _ in range(4):
        out.add(_norm(cur))
        cur = [(y, -x) for x, y in cur]
    return out


def piece_groups_ok(rows: list[str]) -> list[str]:
    """Rule 7: every letter group of a board is one tetromino of that letter, either as drawn or
    with the rows it straddles (and does not touch) removed — the kept-rows frame a later piece is
    drawn in after rows under it have cleared. Returns the letters that are not."""
    h = len(rows)
    groups: dict[str, list[tuple[int, int]]] = {}
    for i, row in enumerate(rows):
        for x, ch in enumerate(row):
            key = 't' if ch == 'U' else ('Z' if ch == 'Z' else ch)
            if key in _PIECE_BASE or key == 'Z':
                groups.setdefault(key, []).append((x, h - 1 - i))
    bad = []
    for key, cs in sorted(groups.items()):
        letter = 'z' if key == 'Z' else key
        if len(cs) != 4:
            bad.append(key)
            continue
        ys = sorted({y for _, y in cs})
        gap = [y for y in range(ys[0], ys[-1] + 1) if y not in ys]
        kept = [(x, y - sum(1 for g in gap if g < y)) for x, y in cs]
        if _norm(cs) not in _shapes(letter) and _norm(kept) not in _shapes(letter):
            bad.append(key)
    return bad


# ── the gate ───────────────────────────────────────────────────────────────────────────────────
def verify(data: dict) -> list[str]:
    """Every rule in the plan's §1. Returns problems; each starts with its rule's tag."""
    bad: list[str] = []
    nodes = data.get('nodes', [])
    ids = [n.get('id') for n in nodes]
    by_id = {n['id']: n for n in nodes if 'id' in n}
    boards = {n['id']: n['rows'] for n in nodes if 'rows' in n}
    boards.update({b['id']: b['rows'] for b in data.get('basic_form', [])})

    # ── provenance ──
    terms = data.get('terms', {})
    for k in ('url', 'dated', 'read', 'allows', 'excludes', 'requests', 'how_met'):
        if not terms.get(k):
            bad.append(f'terms: provenance field {k!r} is missing')
    for k in ('url', 'updated', 'fetched', 'fetch_method', 'snapshot_sha256'):
        if not data.get('source', {}).get(k):
            bad.append(f'source: provenance field {k!r} is missing')

    # ── rule 1: grammar ──
    all_ids = ids + [b['id'] for b in data.get('basic_form', [])]
    if len(all_ids) != len(set(all_ids)):
        bad.append('grammar: duplicate ids')
    for n in nodes:
        nid = n.get('id', '?')
        has_board = 'rows' in n
        has_kind = 'node_kind' in n
        if has_board == has_kind:
            bad.append(f'exclusive-or: {nid} must carry exactly one of a board or a node_kind')
        if has_kind and n['node_kind'] not in NODE_KINDS:
            bad.append(f'grammar: {nid} has unknown node_kind {n["node_kind"]!r}')
        if 'unmatchable' in n and not n['unmatchable']:
            bad.append(f'grammar: {nid} is unmatchable without a reason')
        if has_board:
            rows = n['rows']
            if any(len(r) != WIDTH for r in rows):
                bad.append(f'grammar: {nid} has a row that is not {WIDTH} wide')
            if any(ch not in ALPHABET for r in rows for ch in r):
                bad.append(f'grammar: {nid} has a cell outside {"".join(sorted(ALPHABET))}')
            if 'unmatchable' not in n:
                if any('p' in r for r in rows):
                    bad.append(f'placeholder: {nid} has a p cell but is not marked unmatchable')
                if len(bottom(rows, 0)) > ROWS:
                    bad.append(f'grammar: {nid} is taller than {ROWS} rows but not unmatchable')
        for ref in ('parent', 'base', 'derived_from'):
            if n.get(ref) is not None and n[ref] not in by_id:
                bad.append(f'grammar: {nid} {ref} {n[ref]!r} names no node')
        if 'list' in n:
            if nid != f'{n["list"]}#{n.get("index")}':
                bad.append(f'id-index: {nid} does not match its list {n["list"]!r} and index '
                           f'{n.get("index")}')
            slot = t_slot(n['rows'])
            if n.get('has_tsd_slot') != (slot == 'flat') or n.get('has_u_slot') != (slot is not None):
                bad.append(f'grammar: {nid} has_tsd_slot / has_u_slot disagree with its U cells')
        cond = n.get('condition')
        if cond is not None:
            pieces = [p for c in cond.get('all', []) for p in c.get('before', [])]
            pieces += [cond['early']] if 'early' in cond else []
            if any(p not in PIECES for p in pieces) or (
                    'bag1' in cond and cond['bag1'] not in by_id):
                bad.append(f'grammar: {nid} condition names something that is not a piece/node')

    # every non-board feature of the page is still a node, with the kind it was read as
    for nid, kind in NON_BOARD.items():
        if by_id.get(nid, {}).get('node_kind') != kind:
            bad.append(f'non-board: {nid} ({kind}) is missing or changed kind')
    for n in nodes:
        if 'node_kind' in n and (n['id'] not in NON_BOARD or not n.get('page_text')):
            bad.append(f'non-board: {n["id"]} is not on the named list or has no page_text')

    # the page order covers every page-drawn board exactly once
    po = data.get('page_order', [])
    drawn = [i for i in all_ids if i in boards and not by_id.get(i, {}).get('derived')]
    if sorted(po) != sorted(drawn) or len(po) != len(set(po)):
        bad.append('page_order: does not list every drawn board exactly once')

    # ── rule 2: cross-source against harddrop ──
    wiki = json.loads(WIKI.read_text())
    sc = next(o for o in wiki['openers'] if o['key'] == 'stray_cannon')
    hd = {tuple(f['rows']) for f in sc['fields']}
    if 'bag1.z_hold' in boards:
        ours = [r.replace('-', '.').upper() for r in bottom(boards['bag1.z_hold'], 0)]
        mine = {tuple(ours), tuple(r.upper() for r in mirror([x.lower() for x in ours]))}
        if not (mine & hd):
            bad.append('harddrop: bag1.z_hold disagrees with wiki-openers.json stray_cannon '
                       'cell for cell, as drawn and mirrored')
    else:
        bad.append('harddrop: bag1.z_hold is missing')

    # ── rule 3: internal consistency ──
    for n in nodes:
        nid = n.get('id', '?')
        base = n.get('base')
        if 'rows' not in n or base not in boards:
            continue
        if n.get('bag') == 2:
            # every bag-2 board contains its bag-1 base, reading upper-case Z as the bag-1 Z
            h = max(ROWS, len(n['rows']))
            mine = bottom(n['rows'], h)
            theirs = bottom(boards[base], h)
            old = cells(mine, lambda ch: ch in 'cZ')
            if old != cells(theirs, lambda ch: ch != EMPTY):
                bad.append(f'bag2-base: {nid} c/Z cells are not exactly {base}\'s cells')
            if not cells(mine, lambda ch: ch == 'Z') <= cells(theirs, lambda ch: ch == 'z'):
                bad.append(f'bag2-base: {nid} draws Z where {base} has no bag-1 z')
            continue
        after, cleared = after_spin(boards[base])
        if cleared == 0:
            bad.append(f'c-cells: {base} clears no row when its T goes in')
        h = max(len(after), len(n['rows']))
        if cells(bottom(n['rows'], h), lambda ch: ch == 'c') != cells(
                bottom(after, h), lambda ch: ch != EMPTY):
            bad.append(f'c-cells: {nid} c cells are not what {base} leaves after its spin')
        placed = cells(n['rows'], lambda ch: ch not in (EMPTY, 'c', 'p'))
        if 'p' not in ''.join(n['rows']) and len(placed) % 4:
            bad.append(f'c-cells: {nid} places {len(placed)} cells, not whole pieces')
        if 'list' in n:
            body = bottom(n['rows'], 0)
            if any(EMPTY in r for r in body) or len(body) + cleared != 8:
                bad.append(f'pc: {nid} is not an 8-line perfect clear over {base}')
    if 'bag1.z_left' in boards and 'bag1.z_hold' in boards:
        zl = bottom(boards['bag1.z_left'], ROWS)
        zh = bottom(boards['bag1.z_hold'], ROWS)
        diff = {(r, c) for r in range(ROWS) for c in range(WIDTH) if zl[r][c] != zh[r][c]}
        if (any(zh[r][c] != EMPTY or zl[r][c] != 'z' for r, c in diff) or len(diff) != 4):
            bad.append(f'z_left: bag1.z_left is not bag1.z_hold plus exactly 4 z cells '
                       f'({len(diff)} differ)')
        src = by_id.get(by_id['bag1.z_left'].get('derived_from'), {})
        if 'rows' in src:
            zcells = cells(bottom(src['rows'], ROWS), lambda ch: ch == 'Z')
            if zcells != diff:
                bad.append('z_left: bag1.z_left\'s z cells are not the Z cells of the board it is '
                           'derived from')
    for b in data.get('basic_form', []):
        tgt = boards.get(b['same_as'])
        if tgt is None or bottom(b['rows'], ROWS) != bottom(tgt, ROWS):
            bad.append(f'basic-form: {b["id"]} is not the board of {b["same_as"]}')

    # ── rule 4: distinctness, derived here and never typed ──
    bag2 = [n for n in nodes if n.get('bag') == 2 and 'rows' in n]
    for i, a in enumerate(bag2):
        for b in bag2[i + 1:]:
            ga, gb = occ(bottom(a['rows'], ROWS)), occ(bottom(b['rows'], ROWS))
            if ga == gb or ga == occ(mirror(bottom(b['rows'], ROWS))):
                bad.append(f'distinct: bag-2 boards {a["id"]} and {b["id"]} are equal')
    pats = [n for n in nodes if 'list' in n]
    seen: dict[tuple, str] = {}
    for n in pats:
        g = tuple(bottom(n['rows'], ROWS))
        for key in (g, tuple(mirror(list(g)))):
            other = seen.get((n['parent'],) + key)
            if other:
                bad.append(f'distinct: duplicate pattern {n["id"]} equals {other} by colour')
        seen[(n['parent'],) + g] = n['id']
    classes: dict[tuple, list[str]] = {}
    for n in pats:
        classes.setdefault(tuple(occ([r.replace('U', EMPTY) for r in n['rows']])), []).append(
            n['parent'])
    largest = max(classes.values(), key=len) if classes else []
    if not classes or max(len(v) for v in classes.values()) < 2 or len(set(largest)) < 2:
        bad.append('occupancy-classes: bag-3 patterns became distinct by occupancy, so the shape '
                   'that forces a colour comparison no longer holds')

    # ── rule 5: known source discrepancies ──
    found = set()
    for lst in data.get('lists', []):
        n_drawn = sum(1 for n in pats if n['list'] == lst['id'])
        n_rest = sum(1 for n in pats if n['list'] == lst['id'] and n['listed_under'] == 'rest')
        if n_drawn != lst.get('drawn') or n_rest != lst.get('rest_stated') or (
                n_drawn - n_rest != lst.get('shown')):
            bad.append(f'list-count: {lst["id"]} draws {n_drawn} ({n_rest} under 残り), its '
                       f'record says {lst.get("drawn")} ({lst.get("rest_stated")})')
        if lst.get('stated_pattern_count') is not None and lst['stated_pattern_count'] != n_drawn:
            found.add(f'{lst["id"]}:stated_vs_drawn')
        if not lst.get('complete'):
            found.add(f'{lst["id"]}:non_exhaustive')
    # ── rule 7: piece decomposition. Every letter is whole pieces of that letter, in the kept-rows
    # frame; a drawing that colours a piece in another piece's colour is a source discrepancy ──
    for n in nodes:
        if 'rows' in n and 'p' not in ''.join(n['rows']) and piece_groups_ok(n['rows']):
            found.add(f'{n["id"]}:colour')
    for b in data.get('basic_form', []):
        if piece_groups_ok(b['rows']):
            found.add(f'{b["id"]}:colour')
    named = {d['id'] for d in data.get('known_discrepancies', [])}
    for d in sorted(found - named):
        bad.append(f'discrepancy: {d} is not on the named list — read the page, then name it')
    for d in sorted(named - found):
        bad.append(f'discrepancy: {d} is named but no longer measured')
    return bad


def drift(data: dict) -> list[str]:
    return [] if data == build() else ['drift: meisou-routes.json differs from SPEC — rerun --write']


# ── the page snapshot (offline re-check after a refetch) ─────────────────────────────────────────
BOARD_ROW = re.compile(r'^[-a-zA-Z]{10}$')


def page_boards(md: str) -> list[list[str]]:
    """Every board in a markdown snapshot, in page order: runs of 10-wide board rows."""
    out, cur = [], []
    for line in md.split('\n'):
        s = line.replace('\\-', '-').rstrip()
        if BOARD_ROW.match(s):
            cur.append(s)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def check_snapshot(data: dict, html_dir: Path) -> list[str]:
    p = html_dir / data['source']['snapshot_file']
    raw = p.read_bytes()
    bad = []
    sha = hashlib.sha256(raw).hexdigest()
    if sha != data['source']['snapshot_sha256']:
        bad.append(f'snapshot: sha256 {sha} is not the recorded one (read the board diff below)')
    rows = {n['id']: n['rows'] for n in data['nodes'] if 'rows' in n}
    rows.update({b['id']: b['rows'] for b in data['basic_form']})
    text = raw.decode('utf8')
    for n in data['nodes']:
        if 'page_text' in n and n['page_text'] not in text:
            bad.append(f'snapshot: {n["id"]}\'s page_text {n["page_text"]!r} is not on the page')
    want = [rows[i] for i in data['page_order']]
    got = page_boards(text)
    if got != want:
        bad.append(f'snapshot: the page draws {len(got)} boards, page_order has {len(want)}')
        for k, (a, b) in enumerate(zip(got, want)):
            if a != b:
                bad.append(f'snapshot: board {k + 1} ({data["page_order"][k]}) differs: '
                           f'page {a} vs transcription {b}')
                break
    return bad


# ── selftest ───────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    """A gate nothing can fail is decorative. Plant one defect per rule, require its own message."""
    base = build()
    if verify(base) or drift(json.loads(OUT.read_text())):
        print('selftest: the committed file does not verify — fix that first', file=sys.stderr)
        return 1

    def node(d, nid):
        return next(n for n in d['nodes'] if n['id'] == nid)

    def setcell(rows, r, c, ch):
        rows[r] = rows[r][:c] + ch + rows[r][c + 1:]

    def flip(d):
        setcell(node(d, '2.ideal.pc#1')['rows'], 3, 0, 'o')       # a c cell becomes a piece

    def swap_id(d):
        a, b = node(d, '2.ideal.pc#1'), node(d, '2.ideal.pc#2')
        a['id'], b['id'] = b['id'], a['id']

    def shift_hold(d):
        n = node(d, 'bag1.z_hold')
        n['rows'] = ['-' + r[:-1] for r in n['rows']]

    def delete_pattern(d):
        d['nodes'] = [n for n in d['nodes'] if n['id'] != '2.i_early.pc#12']

    def duplicate_pattern(d):
        n = copy.deepcopy(node(d, '2.z_left.pc#2'))
        n['index'] = 10
        n['id'] = '2.z_left.pc#10'
        d['nodes'].append(n)

    def drop_discrepancy(d):
        d['known_discrepancies'] = d['known_discrepancies'][1:]

    def recolour(d):
        setcell(node(d, '2.ideal.pc#1')['rows'], 1, 0, 'l')        # one j cell drawn as l

    def drop_colour(d):
        d['known_discrepancies'] = [x for x in d['known_discrepancies']
                                    if x['id'] != '2.ideal.pc#16:colour']

    def drop_text_only(d):
        d['nodes'] = [n for n in d['nodes'] if n.get('node_kind') != 'text_only']

    def fifth_z(d):
        setcell(node(d, 'bag1.z_left')['rows'], 1, 2, 'z')

    def both(d):
        node(d, '2.ideal.pc#5')['node_kind'] = 'image_only'

    def placeholder(d):
        setcell(node(d, '2.normal_SO.stsd')['rows'], 1, 0, 'p')

    def no_excludes(d):
        del d['terms']['excludes']

    def bag2_cell(d):
        setcell(node(d, '2.i_early')['rows'], 7, 5, 'c')            # fills the bag-1 hole

    def wrong_z(d):
        setcell(node(d, '2.normal_SO')['rows'], 6, 0, 'Z')          # a Z where bag 1 has i

    def bag2_dup(d):
        node(d, '2.i_early')['rows'] = list(node(d, '2.normal_OS')['rows'])

    def lose_class(d):
        # keep one pattern per occupancy class, as if the page drew no two alike
        seen_occ, keep = set(), []
        for n in d['nodes']:
            if 'list' in n:
                k = tuple(occ([r.replace('U', EMPTY) for r in n['rows']]))
                if k in seen_occ:
                    continue
                seen_occ.add(k)
            keep.append(n)
        d['nodes'] = keep

    def basic_off(d):
        setcell(d['basic_form'][0]['rows'], 4, 1, 'i')

    def tall(d):
        node(d, '2.ideal')['rows'].insert(0, 'i---------')

    def no_reason(d):
        node(d, '2.ideal.fire.stmb_example')['unmatchable'] = ''

    mutants = [
        (flip, 'a flipped cell', 'c-cells:'),
        (swap_id, 'a swapped id', 'id-index:'),
        (shift_hold, 'the z_hold field shifted one column', 'harddrop:'),
        (delete_pattern, 'a deleted pattern', 'discrepancy:'),
        (duplicate_pattern, 'a duplicated pattern', 'distinct:'),
        (drop_discrepancy, 'a dropped discrepancy entry', 'discrepancy:'),
        (recolour, 'one cell of a whole piece recoloured', 'discrepancy:'),
        (drop_colour, 'the pc#16 colour discrepancy dropped', 'discrepancy:'),
        (drop_text_only, 'a deleted text_only node', 'non-board:'),
        (fifth_z, 'z_left given a fifth Z cell', 'z_left:'),
        (both, 'a node with both a board and a node_kind', 'exclusive-or:'),
        (placeholder, 'a p cell in a node that is not unmatchable', 'placeholder:'),
        (no_excludes, 'terms.excludes deleted', 'terms:'),
        (bag2_cell, 'a bag-2 c cell where bag 1 is empty', 'bag2-base:'),
        (wrong_z, 'an upper-case Z off the bag-1 z cells', 'bag2-base:'),
        (bag2_dup, 'two bag-2 boards made equal', 'distinct:'),
        (lose_class, 'bag-3 patterns made distinct by occupancy', 'occupancy-classes:'),
        (basic_off, 'a 基本形 board off its node', 'basic-form:'),
        (tall, 'a 9-row board not marked unmatchable', 'grammar:'),
        (no_reason, 'an unmatchable node with no reason', 'grammar:'),
    ]
    ok = True
    for fn, label, tag in mutants:
        d = copy.deepcopy(base)
        fn(d)
        problems = verify(d)
        if not any(p.startswith(tag) for p in problems):
            print(f'selftest FAILED: {label} was not caught by {tag!r} (got {problems[:3]})',
                  file=sys.stderr)
            ok = False
        else:
            print(f'  killed: {label}  [{tag}]')
    # the drift gate itself
    d = copy.deepcopy(base)
    node(d, '2.ideal')['label'] = 'edited by hand'
    if drift(d):
        print('  killed: a hand edit to the committed JSON  [drift:]')
    else:
        print('selftest FAILED: a hand edit was not caught by drift', file=sys.stderr)
        ok = False
    # the snapshot locator: one row changed in a synthetic snapshot
    import tempfile
    rows = {n['id']: n['rows'] for n in base['nodes'] if 'rows' in n}
    rows.update({b['id']: b['rows'] for b in base['basic_form']})
    md = '\n\n'.join('\n'.join(('\\' + r) if r.startswith('-') else r for r in rows[i])
                     for i in base['page_order']) + '\n'
    md += '\n'.join(n['page_text'] for n in base['nodes'] if 'page_text' in n) + '\n'
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / base['source']['snapshot_file']
        p.write_text(md)
        clean = [x for x in check_snapshot(base, Path(td)) if not x.startswith('snapshot: sha256')]
        p.write_text(md.replace('cccccUcccc', 'ccccc-cccc', 1))
        dirty = check_snapshot(base, Path(td))
        p.write_text(md.replace('中開け4列REN', '中開け5列REN'))
        lost = check_snapshot(base, Path(td))
    if clean or not any('differs' in x for x in dirty):
        print(f'selftest FAILED: snapshot locator (clean={clean}, dirty={dirty[:2]})',
              file=sys.stderr)
        ok = False
    else:
        print('  killed: a redrawn board in the page snapshot  [snapshot:]')
    if not any("page_text" in x for x in lost):
        print('selftest FAILED: a non-board feature gone from the snapshot was not caught',
              file=sys.stderr)
        ok = False
    else:
        print('  killed: a non-board feature gone from the page snapshot  [snapshot:]')
    print('selftest: all mutants killed' if ok else 'selftest: FAILED')
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or '').split('\n')[0])
    ap.add_argument('--html-dir', type=Path,
                    help='directory holding the markdown snapshot (meisou.md) of a refetch')
    ap.add_argument('--write', action='store_true', help='rewrite meisou-routes.json from SPEC')
    ap.add_argument('--selftest', action='store_true', help='prove the verifier has teeth')
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    data = build()
    problems = verify(data)
    if args.html_dir:
        problems += check_snapshot(data, args.html_dir)
    if args.write and not problems:
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(f'wrote {OUT.relative_to(HERE.parent.parent)}')
    if not args.write:
        problems += drift(json.loads(OUT.read_text()))

    nodes = data['nodes']
    n_boards = sum(1 for n in nodes if 'rows' in n)
    kinds: dict[str, int] = {}
    for n in nodes:
        if 'node_kind' in n:
            kinds[n['node_kind']] = kinds.get(n['node_kind'], 0) + 1
    print(f'  {len(nodes)} nodes: {n_boards} with a board, '
          + ', '.join(f'{v} {k}' for k, v in sorted(kinds.items()))
          + f'; {sum(1 for n in nodes if "unmatchable" in n)} unmatchable')
    print(f'  {len(data["page_order"])} boards in page order '
          f'(+{sum(1 for n in nodes if n.get("derived"))} derived)')
    for lst in data['lists']:
        print(f'  {lst["id"]:16s} drawn {lst["drawn"]:2d} (shown {lst["shown"]}, rest '
              f'{lst["rest_stated"]}), stated {lst["stated_pattern_count"]}')
    classes: dict[tuple, int] = {}
    for n in nodes:
        if 'list' in n:
            k = tuple(occ([r.replace('U', EMPTY) for r in n['rows']]))
            classes[k] = classes.get(k, 0) + 1
    print(f'  bag-3 occupancy classes (raw rows, U empty): '
          f'{sorted(classes.values(), reverse=True)} — colour decides, occupancy cannot')
    if problems:
        for p in problems:
            print(f'FAIL {p}', file=sys.stderr)
        return 1
    print('meisou-routes.json OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

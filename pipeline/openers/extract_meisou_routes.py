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

THE GATE IS SHARED. Every rule both route pages need is in `route_transcription.py`, once; this file
holds the 迷走砲 transcription, its `SPEC` (alphabet, harddrop field, the upper-case Z reading) and
its one rule nothing else has (`_z_left_check`), plus its selftest mutants.
"""
from __future__ import annotations

import copy
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers.route_transcription import (EMPTY, ROWS, WIDTH, bottom, cells, node, occ,
                                                  setcell, t_slot)

HERE = Path(__file__).resolve().parent
OUT = HERE / 'meisou-routes.json'

ALPHABET = frozenset('-ijlostzcUZp')


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


# ── 迷走砲's own rule, and its half of the shared gate ──────────────────────────────────────────
def _z_left_check(data: dict, ctx: dict) -> tuple[list[str], set[str]]:
    """Rule 3, 迷走砲 only: `bag1.z_left` is DERIVED — z_hold plus exactly the four `Z` cells of the
    board it is derived from."""
    bad: list[str] = []
    boards, by_id = ctx['boards'], ctx['by_id']
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
    return bad, set()


SPEC = RT.TranscriptionSpec(
    out=OUT, build=build, alphabet=ALPHABET, non_board=NON_BOARD,
    harddrop={'key': 'stray_cannon', 'node': 'bag1.z_hold'},
    pc_lines=8, prior_letters='Z', upper_groups={'Z': 'separate'},
    slot_flags={'has_u_slot': lambda rows: t_slot(rows) is not None,
                'has_tsd_slot': lambda rows: t_slot(rows) == 'flat'},
    occupancy_class_parents=2, extra_checks=_z_left_check)


def verify(data: dict) -> list[str]:
    return RT.verify(data, SPEC)


def drift(data: dict) -> list[str]:
    return RT.drift(data, SPEC)


# ── selftest ───────────────────────────────────────────────────────────────────────────────────
def selftest() -> int:
    """A gate nothing can fail is decorative. Plant one defect per rule, require its own message."""
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
    return RT.run_selftest(SPEC, mutants, {'board': ('cccccUcccc', 'ccccc-cccc'),
                                           'text': ('中開け4列REN', '中開け5列REN'),
                                           'hand_edit': '2.ideal'})


def main() -> int:
    return RT.main(SPEC, selftest, __doc__)


if __name__ == '__main__':
    raise SystemExit(main())

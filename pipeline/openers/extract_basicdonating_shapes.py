"""Transcribe shiwehi.com's 脱初心者のための基本的なドネイト page into `basicdonating-technique.json`.

    python3 -m pipeline.openers.extract_basicdonating_shapes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_basicdonating_shapes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_basicdonating_shapes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_basicdonating_shapes --html-dir <dir> --write  # ...and rewrite

The eleventh MID-GAME TECHNIQUE page (中盤テンプレ・ドネイト), and the first that teaches a PRINCIPLE rather than
one shape: 「ドネイトを行う際の意識として最も重要なのは、TSDで消える2列だけを埋めるという意識です」. A piece (or two)
is laid over a hole so that its cells in the column fill exactly the two rows the TSD will clear; the TSD
clears them, and the hole under them is open again. The page draws five one-piece forms, seven two-piece
forms, eight two-wide-hole forms and two T-spin FIN forms, and twenty-three practice questions with their
answers. No two of them agree on the stack between the T and the hole.

DECISION (since 2026-10-26, yachi's rule; the six hole windows k1..k6 and the nub window are retired): no window.
The spin is a TSD and a column DONATES when, at its topmost cell that is empty, in no row the T makes full and
directly under a cell of such a row, every filled cell of the column above it lies in those rows (so the clear
opens it from the top) and the cell above it is not the T (a hole under the T's nub alone is a plain T-spin). Any
column, any depth, any distance from the T. In play each covering cell must also be the T or a complete piece,
never garbage; ownership is not drawn, so this gate reads the occupancy half (`technique_transcription.
rule_columns`, the Python twin of `basicdonating-rule.ts`). One variant, `rule` (`window_basis: rule`), on the
page's first one-piece form; its `window` is only the T's box, where the page draws it.

THE RULE DOES NOT CHOOSE ITS OWN EVIDENCE: `rule_accounting` (the shared gate) applies it to every board of the
page, at its drawn T (a spin board) or at every resting T placement making exactly two rows full (any other
board), and every place it fires must be the variant's `drawings` entry with its donating holes measured; every
spin board it misses must be a `rule_not_fired` entry with a reason (the 3-row L mistake; harddrop's nub-only
board). The forms the page names as another page's technique (階段のドネイト, 欄干, STMB Cave) are donations
too: the qualify rule `other_page` gives such a T to that page.

WHERE THE TRANSCRIPTION COMES FROM. `NODES` is checked against the page's raw HTML (`basicdonating.html`,
fetched with curl through a CA bundle adding the Let's Encrypt YE2 intermediate the server omits, TLS
verification on, as STSD, BT砲, 階段のドネイト and 途中DT砲 were). The page indents some of its boards with a
tab, so the snapshot is read with `page_boards(indented=True)` (`TechniqueSpec.snapshot_indented`). 75 boards,
in page order.

WHAT IS AN INFERENCE, flagged in the legend: `U` is the T the spin places; upper case is a cell in a row the
spin clears, muted (checked by the spin rule on every spin board), and on a form drawn without its T the
rows the T would clear (read as filled). `t` on the TO-cyclone form is a T piece placed before the spin.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from pipeline.openers import technique_transcription as TT
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS

HERE = Path(__file__).resolve().parent
OUT = HERE / 'basicdonating-technique.json'

ALPHABET = frozenset('-cCUijlostzIJLOSZ')
MAX_ROWS = 9


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/basicdonating.php',
    'title': '脱初心者のための基本的なドネイト',
    'author': 'しゑひ(shiwehi)',
    'created': '2021-03-22',
    'updated': '2024-10-07',
    'fetched': '2026-10-24',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle that adds the '
                    'Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), the method STSD, BT砲, '
                    '階段のドネイト and 途中DT砲 used. The snapshot is the page\'s raw HTML, byte for byte; every board is '
                    'plain text in it (some rows indented with a tab), 75 ten-wide boards in page order.',
    'snapshot_file': 'basicdonating.html',
    'snapshot_sha256': '78241b0782ca525efeec541e04b9d03e7c0b30767a87b2609880ee72e42a3849',
    'snapshot_bytes': 51066,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable in CI: the page '
                     'is not committed and cannot be fetched there. Re-check with --html-dir after any refetch; an HTML '
                     'hash moves with ANY byte of the page (ads, sidebar, a date), so a moved hash means "read the board '
                     'diff", not "the boards changed". Sentences are compared against the page with its tags dropped.',
    'renderer': {
        'url': 'https://shiwehi.com/tetris/mutual/column-exp.js?date=20210408',
        'read': 'not re-fetched for this page: the same URL 途中DT砲 read on 2026-10-24 (its colour map is recorded '
                'there); this page draws no letter outside the ones that page and STSD read',
    },
    'decorative_images': ['脱初心者のための基本的なドネイト タイトル画像'],
    'references': ['./applieddonating.php (応用的なドネイト, not transcribed)', './kaidansetup.php (階段のドネイト)',
                   './parapet.php (欄干)', './stmbcave.php (STMB Cave)', './tspin.php',
                   'Donation | Tetris Wiki | Fandom', 'TETRiS TRAiNER TRÈS-BiEN', 'ドネイト Donating | Tetrisちゃんねる',
                   '【テトリス/豆知識】深い2列穴を埋めるドネイト【VOICEVOX解説】 by dotTIZ',
                   '自作ドネイト「LJサイクロン」、「TOサイクロン」【ぷよテト2】'],
    'unfetched': ['./applieddonating.php'],
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ',
    '-': 'empty',
    'c': 'a cell filled before this diagram (any piece, or garbage), grey',
    'i j l o s t z': 'a cell of that piece ( a T placed before the spin, on the TO-cyclone form)',
    'I J L O S Z': 'a cell of that piece in a row a spin clears, drawn muted; checked whole with its lower-case cells',
    'U': 'a cell of the T the spin places (the renderer\'s "the T goes here")',
    'C': 'an earlier cell in a row a spin clears, muted (checked on every spin board); on a form drawn without '
         'its T, a cell of the rows the T would clear (OUR READING: filled)',
    '%X': 'the X piece',
}

QUOTES = [
    {'id': 'title', 'verbatim': '脱初心者のための基本的なドネイト'},
    {'id': 'definition', 'verbatim': 'とは、テトリスにおいてBack-To-Backを維持するためにわざと下穴を塞いでTスピンを打つ技術のことです。'},
    {'id': 'h.consciousness', 'verbatim': 'ドネイトを行う時の意識'},
    {'id': 'consciousness', 'verbatim': 'ドネイトを行う際の意識として最も重要なのは、TSDで消える2列だけを埋めるという意識です。(TSSの1列にする場合も有。)'},
    {'id': 'z', 'verbatim': '下図では%Zを使用して、ちょうどTSDで消える2列分だけを埋めることができたため、下穴が開いた状態を維持することができています。'},
    {'id': 'l3', 'verbatim': 'しかし、こちらの下図では、2列ではなく3列を埋めてしまったため、下穴が埋まってしまい、掘りにくい形となってしまいました。'},
    {'id': 'tetris', 'verbatim': 'このような場合は、無理にTスピンでラインを消そうとせずに、空Tスピンで地形を整えてからテトリスを打つという選択肢もある、ということを覚えておくと良いでしょう。'},
    {'id': 'h.one', 'verbatim': '1ミノドネイト'},
    {'id': 'one', 'verbatim': '1つのミノで作ることができるドネイトです。'},
    {'id': 'one.named', 'verbatim': 'は名前が付いているため知っている人も多いかもしれませんが、それ以外のミノを使用したドネイトも非常に使用しやすいため、覚えておくとTスピンの幅が広がります。'},
    {'id': 'h.one.forms', 'verbatim': '1ミノドネイトの形'},
    {'id': 'h.one.q', 'verbatim': '1ミノドネイトの練習問題'},
    {'id': 'question', 'verbatim': 'TSDを打ってください。'},
    {'id': 'answer', 'verbatim': '解答'},
    {'id': 'h.two', 'verbatim': '2ミノドネイト'},
    {'id': 'two', 'verbatim': '2つのミノを使用して作るドネイトです。'},
    {'id': 'h.two.forms', 'verbatim': '2ミノドネイトの形'},
    {'id': 'h.hole', 'verbatim': '2列幅の穴を埋める2ミノドネイトの形'},
    {'id': 'hole4', 'verbatim': 'これは%Iを立てた後に%S/%Zの1ミノドネイトやってるのと同じですね。'},
    {'id': 'hole5', 'verbatim': 'これは%Iを立てた後に%Oの1ミノドネイトやってるのと同じです。'},
    {'id': 'h.fin', 'verbatim': 'T-spin FINを打つ2ミノドネイトの形'},
    {'id': 'fin', 'verbatim': 'T-spin FINは残る地形があまり良くないので実戦で使うかは怪しいですが、一応掲載しておきます。'},
    {'id': 'h.two.q', 'verbatim': '2ミノドネイトの練習問題'},
]

NODES = [
    {'id': 'intro.terrain', 'kind': 'base', 'caption_quote': 'consciousness',
     'label': 'a terrain with a two-deep well at the wall and a TSD slot', 'rows': _b('---------- ----cc---- -----ccccc -cc-cccccc -ccccccccc -ccccccccc')},
    {'id': 'intro.z', 'kind': 'spin', 'on': 'intro.terrain', 'adds': 'UZz', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2, 'caption_quote': 'z',
     'label': 'the Z fills exactly the two rows the TSD clears: the well stays open', 'rows': _b('---------- -z--cc---- ZZUUUCCCCC ZCCUCCCCCC -ccccccccc -ccccccccc')},
    {'id': 'intro.z.after', 'kind': 'after', 'after_of': 'intro.z', 'caption_quote': 'z',
     'label': 'what that TSD leaves: the well open from the top', 'rows': _b('---------- ---------- ---------- -z--cc---- -ccccccccc -ccccccccc')},
    {'id': 'intro.l3', 'kind': 'spin', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2, 'caption_quote': 'l3',
     'label': 'the L fills three rows, not two: its top cell is left over the well', 'rows': _b('---------- ll--cc---- LCUUUCCCCC LCCUCCCCCC -ccccccccc -ccccccccc')},
    {'id': 'intro.l3.after', 'kind': 'after', 'after_of': 'intro.l3', 'caption_quote': 'l3',
     'label': 'what that TSD leaves: the well covered', 'rows': _b('---------- ---------- ll--cc---- -ccccccccc -ccccccccc')},
    {'id': 'intro.empty_t', 'kind': 'illustration', 'caption_quote': 'tetris',
     'label': 'the alternative: a T-spin that clears nothing, to tidy the terrain', 'rows': _b('---------- ----cc---- -cUUUccccc -ccUcccccc -ccccccccc -ccccccccc')},
    {'id': 'intro.tetris', 'kind': 'illustration', 'caption_quote': 'tetris',
     'label': '...and then a Tetris into the well', 'rows': _b('---------- ----cc---- ICUUUCCCCC ICCUCCCCCC ICCCCCCCCC ICCCCCCCCC')},
    {'id': 'one.o', 'kind': 'base', 'caption_quote': 'h.one.forms',
     'label_jp': '%Oドネイト', 'rows': _b('---------- ----cc---- oo---CCCCC ooC-CCCCCC -ccccccccc -ccccccccc')},
    {'id': 'one.s', 'kind': 'base', 'caption_quote': 'h.one.forms',
     'label_jp': '%Sドネイト(=階段のドネイト)', 'rows': _b('---------- ---cc----- s---CCCCCC ss-CCCCCCC -scccccccc -ccccccccc')},
    {'id': 'one.z', 'kind': 'base', 'caption_quote': 'h.one.forms',
     'label_jp': '%Zドネイト', 'rows': _b('---------- -z--cc---- zz---CCCCC zCC-CCCCCC -ccccccccc -ccccccccc')},
    {'id': 'one.l_a', 'kind': 'base', 'caption_quote': 'h.one.forms',
     'label_jp': '%LドネイトA(=欄干)', 'rows': _b('---------- l--cc----- l---CCCCCC ll-CCCCCCC c-cccccccc c-cccccccc')},
    {'id': 'one.l_b', 'kind': 'base', 'caption_quote': 'h.one.forms',
     'label_jp': '%LドネイトB', 'rows': _b('---------- -----cc--- lll---CCCC lCCC-CCCCC -ccccccccc -ccccccccc')},
    {'id': 'q1.1', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q1 (1ミノ)', 'rows': _b('---------- ---------- ---------- cc-------- ccc-----cc cccc-c--cc cccccc-ccc cccccc-ccc')},
    {'id': 'q1.1.answer', 'kind': 'spin', 'on': 'q1.1', 'adds': 'OUl', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q1 (1ミノ), the answer: the donation and the T',
     'rows': _b('---------- --l------- --l------- ccll------ CCCUUUOOCC CCCCUCOOCC cccccc-ccc cccccc-ccc')},
    {'id': 'q1.2', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q2 (1ミノ)', 'rows': _b('---------- ---------- ---------- ---------- cccccc---- ccccccc--- cccccccc-- ccccccccc-')},
    {'id': 'q1.2.answer', 'kind': 'spin', 'on': 'q1.2', 'adds': 'UZoz', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q2 (1ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- -----oo--- -----oo--- CCCCCCUUUZ CCCCCCCUZZ ccccccccz- ccccccccc-')},
    {'id': 'q1.3', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q3 (1ミノ)', 'rows': _b('---------- ---------- ---------- ---------- -----ccccc c-cc-ccccc cccc-ccccc cccc-ccccc')},
    {'id': 'q1.3.answer', 'kind': 'spin', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q3 (1ミノ), the answer: the donation and the T',
     'rows': _b('---------- ----z----- ---zz----- ---zs----- CUUUSSCCCC CCUCCSCCCC ccccc-cccc ccccc-cccc')},
    {'id': 'q1.4', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q4 (1ミノ)', 'rows': _b('---------- ---------- ---------- ---------- -------ccc cc-ccc-ccc cccccc-ccc cccccc-ccc')},
    {'id': 'q1.4.answer', 'kind': 'spin', 'on': 'q1.4', 'adds': 'JUZz', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q4 (1ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- -z-------- zz-------- ZUUUJJJCCC CCUCCCJCCC cccccc-ccc cccccc-ccc')},
    {'id': 'q1.5', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q5 (1ミノ)', 'rows': _b('---------- ---------- --------cc ---ccc---c ---cccc-cc -ccccccccc -ccccccccc -ccccccccc')},
    {'id': 'q1.5.answer', 'kind': 'spin', 'on': 'q1.5', 'adds': 'JUZjz', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q5 (1ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- -zj-----cc ZZJCCCUUUC ZJJCCCCUCC -ccccccccc -ccccccccc -ccccccccc')},
    {'id': 'q1.6', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q6 (1ミノ)', 'rows': _b('---------- ---------- ---------- ---------- ------cccc ---c-ccccc -ccccccccc -ccccccccc')},
    {'id': 'q1.6.answer', 'kind': 'spin', 'on': 'q1.6', 'adds': 'JOUj', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q6 (1ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- ---------- --jj------ OOJUUUCCCC OOJCUCCCCC -ccccccccc -ccccccccc')},
    {'id': 'two.jz_a', 'kind': 'base', 'caption_quote': 'h.two.forms',
     'label_jp': '%J%ZドネイトA', 'rows': _b('--z------- -zz------- jz---CCCCC jjj-CCCCCC -ccccccccc -ccccccccc')},
    {'id': 'two.jz_b', 'kind': 'base', 'caption_quote': 'h.two.forms',
     'label_jp': '%J%ZドネイトB', 'rows': _b('---------- --zz-j---- ---zzjCCCC C-CCjjCCCC cccc-ccccc cccc-ccccc')},
    {'id': 'two.sz_a', 'kind': 'base', 'caption_quote': 'h.two.forms',
     'label_jp': '%S%ZドネイトA(=STMB Cave)', 'rows': _b('--z------- -zz------- Cz---ssCCC CCC-ssCCCC ccc---cccc cccc-ccccc')},
    {'id': 'two.sz_b', 'kind': 'base', 'caption_quote': 'h.two.forms',
     'label_jp': '%S%ZドネイトB', 'rows': _b('--z------- -zz------- sz---CCCCC ssC-CCCCCC -scccccccc -ccccccccc')},
    {'id': 'two.js_a', 'kind': 'base', 'caption_quote': 'h.two.forms',
     'label_jp': '%J%SドネイトA', 'rows': _b('---------- ------cc-- jjss---CCC jssCC-CCCC j-cccccccc c-cccccccc')},
    {'id': 'two.js_b', 'kind': 'base', 'caption_quote': 'h.two.forms',
     'label_jp': '%J%SドネイトB', 'rows': _b('---------- --ss------ jss---CCCC jjjC-CCCCC --cccccccc --cccccccc')},
    {'id': 'two.oz', 'kind': 'base', 'caption_quote': 'h.two.forms',
     'label_jp': '%O%Zドネイト(=鶏頭くびき)', 'rows': _b('---------- -z--cc---- zz---CCCCC zoo-CCCCCC -ooccccccc -ccccccccc')},
    {'id': 'hole2.a', 'kind': 'base', 'caption_quote': 'h.hole',
     'label_jp': '高さ2マスのとき(%S/%Z>%I)', 'rows': _b('---------- -iccc--ccc -iccc--ccc -iccc--ccc siCCC---CC ssCCCC-CCC -scccccccc')},
    {'id': 'hole2.b', 'kind': 'base', 'caption_quote': 'h.hole',
     'label_jp': '高さ2マスのとき(%S/%Z>%I), the other hand of the hole', 'rows': _b('---------- i-ccc--ccc i-ccc--ccc i-ccc--ccc izCCC---CC zzCCCC-CCC z-cccccccc')},
    {'id': 'hole3.a', 'kind': 'base', 'caption_quote': 'h.hole',
     'label_jp': '高さ3マスのとき(%J・%L)', 'rows': _b('---------- l-ccc--ccc l-ccc--ccc llCCC---CC jjCCCC-CCC j-cccccccc j-cccccccc')},
    {'id': 'hole3.b', 'kind': 'base', 'caption_quote': 'h.hole',
     'label_jp': '高さ3マスのとき(%J・%L), the other hand of the hole', 'rows': _b('---------- -jccc--ccc -jccc--ccc jjCCC---CC llCCCC-CCC -lcccccccc -lcccccccc')},
    {'id': 'hole4.a', 'kind': 'base', 'caption_quote': 'h.hole',
     'label_jp': '高さ4マスのとき(%I>%S/%Z)', 'rows': _b('---------- s-ccc--ccc ssCCC---CC isCCCC-CCC i-cccccccc i-cccccccc i-cccccccc')},
    {'id': 'hole4.b', 'kind': 'base', 'caption_quote': 'h.hole',
     'label_jp': '高さ4マスのとき(%I>%S/%Z), the other hand of the hole', 'rows': _b('---------- -zccc--ccc zzCCC---CC ziCCCC-CCC -icccccccc -icccccccc -icccccccc')},
    {'id': 'hole5.a', 'kind': 'base', 'caption_quote': 'h.hole',
     'label_jp': '高さ5マスのとき(%I>%O)', 'rows': _b('--ccc--ccc ooCCC---CC ooCCCC-CCC i-cccccccc i-cccccccc i-cccccccc i-cccccccc')},
    {'id': 'hole5.b', 'kind': 'base', 'caption_quote': 'h.hole',
     'label_jp': '高さ5マスのとき(%I>%O), the other hand of the hole', 'rows': _b('--ccc--ccc ooCCC---CC ooCCCC-CCC -icccccccc -icccccccc -icccccccc -icccccccc')},
    {'id': 'fin.lj', 'kind': 'base', 'caption_quote': 'h.fin',
     'label_jp': '%L+屋根(LJサイクロン)', 'rows': _b('---------- ---jjjcccc -----jcccc -----ccccc lll--CCCCC lCCC-CCCCC -ccccccccc -ccccccccc')},
    {'id': 'fin.to', 'kind': 'base', 'caption_quote': 'h.fin',
     'label_jp': '%T%O+屋根(TOサイクロン)', 'rows': _b('---------- --jjj----- ----jccccc ----cccccc OO--CCCCCC OOt-CCCCCC -tttcccccc -ccccccccc -ccccccccc')},
    {'id': 'q2.1', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q1 (2ミノ)', 'rows': _b('---------- ---------- ---------- ccc------c ccc-----cc ccc----ccc ccc-cccccc ccc-cccccc')},
    {'id': 'q2.1.answer', 'kind': 'spin', 'on': 'q2.1', 'adds': 'JUZz', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q1 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- -----z---- ccc-zz---c CCCJZUUUCC CCCJJJUCCC ccc-cccccc ccc-cccccc')},
    {'id': 'q2.2', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q2 (2ミノ)', 'rows': _b('---------- ---------- ---------- cc------cc cc--cc-ccc ccc-cccccc ccc-cccccc ccc-cccccc')},
    {'id': 'q2.2.answer', 'kind': 'spin', 'on': 'q2.2', 'adds': 'LSUls', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q2 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- --l-ss---- CCLSSUUUCC CCLLCCUCCC ccc-cccccc ccc-cccccc ccc-cccccc')},
    {'id': 'q2.3', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q3 (2ミノ)', 'rows': _b('---------- ---------- c--------- cc-----ccc ccc---cccc ccc---cccc ccc---cccc ccc-cccccc')},
    {'id': 'q2.3.answer', 'kind': 'spin', 'on': 'q2.3', 'adds': 'SUj', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q3 (2ミノ), the answer: the donation and the T',
     'rows': _b('--j------- --j------- cjj------- CCUUUSSCCC CCCUSSCCCC ccc---cccc ccc---cccc ccc-cccccc')},
    {'id': 'q2.4', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q4 (2ミノ)', 'rows': _b('---------- ---------- cc-------- ccccc----- cccccc-c-- cccccccc-- ccccccccc- ccccccccc-')},
    {'id': 'q2.4.answer', 'kind': 'spin', 'on': 'q2.4', 'adds': 'SUZsz', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q4 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- -------s-- cc-----ss- CCCCCUUUSZ CCCCCCUCZZ ccccccccz- ccccccccc- ccccccccc-')},
    {'id': 'q2.5', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q5 (2ミノ)', 'rows': _b('---------- ---------- cc-------- c-------cc cc-cc---cc cccccc--cc cccccc-ccc cccccc-ccc')},
    {'id': 'q2.5.answer', 'kind': 'spin', 'on': 'q2.5', 'adds': 'LUZl', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q5 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- cc-------- CUUUZZLLCC CCUCCZZLCC cccccc-lcc cccccc-ccc cccccc-ccc')},
    {'id': 'q2.6', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q6 (2ミノ)', 'rows': _b('---------- ---------- ---------- ---------- ------cccc ---c-ccccc -ccccccccc -ccccccccc')},
    {'id': 'q2.6.answer', 'kind': 'spin', 'on': 'q2.6', 'adds': 'JSUs', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q6 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- ---------- --ss------ JSSUUUCCCC JJJCUCCCCC -ccccccccc -ccccccccc')},
    {'id': 'q2.7', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q7 (2ミノ)', 'rows': _b('---------- ---------- ---------- ccc-----cc ccc----ccc ccc-c-cccc ccc-cccccc ccc-cccccc')},
    {'id': 'q2.7.answer', 'kind': 'spin', 'on': 'q2.7', 'adds': 'JSUjs', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q7 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- ----ss---- CCCSSUUUCC CCCJJJUCCC ccc-cjcccc ccc-cccccc ccc-cccccc')},
    {'id': 'q2.8', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q8 (2ミノ)', 'rows': _b('---------- ---------- ---------- cccc------ ccccc-c--- ccccccccc- ccccccccc- ccccccccc-')},
    {'id': 'q2.8.answer', 'kind': 'spin', 'on': 'q2.8', 'adds': 'LUZz', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q8 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- ------zz-- CCCCUUUZZL CCCCCUCLLL ccccccccc- ccccccccc- ccccccccc-')},
    {'id': 'q2.9', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q9 (2ミノ)', 'rows': _b('---------- ---------- cccccc---- ccccc----- cccccc---- ccccccc--- ccccccccc- ccccccccc-')},
    {'id': 'q2.9.answer', 'kind': 'spin', 'on': 'q2.9', 'adds': 'OSUos', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q9 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- cccccc--s- CCCCCUUUSS CCCCCCUOOS cccccccoo- ccccccccc- ccccccccc-')},
    {'id': 'q2.10', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q10 (2ミノ)', 'rows': _b('---------- ---------- ---------- ------cc-- --cccccc-- ---ccccc-- c-cccccc-- cccccccc--')},
    {'id': 'q2.10.answer', 'kind': 'spin', 'on': 'q2.10', 'adds': 'SUis', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q10 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- ---------i ------cc-i --cccccc-i UUUCCCCCSi CUCCCCCCSS cccccccc-s')},
    {'id': 'q2.11', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q11 (2ミノ)', 'rows': _b('---------- ---------- ---------- ----cccc-- cc---ccc-- ccc-cccc-- cccccccc-- cccccccc--')},
    {'id': 'q2.11.answer', 'kind': 'spin', 'on': 'q2.11', 'adds': 'JLUj', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q11 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- --------L- ----ccccL- CCUUUCCCLL CCCUCCCCJJ ccccccccj- ccccccccj-')},
    {'id': 'q2.12', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q12 (2ミノ)', 'rows': _b('---------- ---------- ccccc----- cccc---c-- ccccc-cc-- cccccccc-- cccccccc-- cccccccc--')},
    {'id': 'q2.12.answer', 'kind': 'spin', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q12 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- ccccc--c-z CCCCUUUCZZ CCCCCUCCZI cccccccc-i cccccccc-i cccccccc-i')},
    {'id': 'q2.13', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q13 (2ミノ)', 'rows': _b('---------- ---------- ---------- ---------- ---------- --c---cccc --cc-ccccc --cccccccc')},
    {'id': 'q2.13.answer', 'kind': 'spin', 'on': 'q2.13', 'adds': 'LSUls', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q13 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- ---------- ---------- -lll------ SLCUUUCCCC SSCCUCCCCC -scccccccc')},
    {'id': 'q2.14', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q14 (2ミノ)', 'rows': _b('---------- ---------- ---------c -------ccc c-ccc--ccc ccccc--ccc ccccc--ccc ccccc-cccc')},
    {'id': 'q2.14.answer', 'kind': 'spin', 'on': 'q2.14', 'adds': 'JLUZjl', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q14 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ------j--- --ZZ--j--c UUUZZJJCCC CUCCCLLCCC ccccc-lccc ccccc-lccc ccccc-cccc')},
    {'id': 'q2.15', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q15 (2ミノ)', 'rows': _b('---------- ---------- ---------- c--------- c--------- cc-----c-- ccccc-cc-- cccccccc--')},
    {'id': 'q2.15.answer', 'kind': 'spin', 'on': 'q2.15', 'adds': 'ISUZis', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q15 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---------- --------i- c-------i- c--ss---i- CCSSUUUCIZ CCCCCUCCZZ ccccccccZ-')},
    {'id': 'q2.16', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q16 (2ミノ)', 'rows': _b('---------- ---------- ---------- cccc------ ccccc----- ccccc----- ccccccccc- ccccccccc-')},
    {'id': 'q2.16.answer', 'kind': 'spin', 'on': 'q2.16', 'adds': 'JLUlo', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q16 (2ミノ), the answer: the donation and the T',
     'rows': _b('---------- ---oo----- ---oo----- CCCCUUUJJJ CCCCCULLLJ ccccc-l--- ccccccccc- ccccccccc-')},
    {'id': 'q2.17', 'kind': 'base', 'caption_quote': 'question',
     'label': 'Q17 (2ミノ)', 'rows': _b('---------- ---------- ccc------- ccc-----cc ccc-----cc ccccc-cccc ccccc-cccc ccccc-cccc')},
    {'id': 'q2.17.answer', 'kind': 'spin', 'on': 'q2.17', 'adds': 'SUZs', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'answer', 'label': 'Q17 (2ミノ), the answer: the donation and the T',
     'rows': _b('--------s- --------ss CCCSZZUUUS CCCSSZZUCC ccc-s---cc ccccc-cccc ccccc-cccc ccccc-cccc')},
    # ── external: harddrop's Donation T-Spin Double, the hole under the T's own nub, drawn nowhere on this page ──
    {'id': 'nub.hd', 'kind': 'spin', 'external': 'harddrop', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'source_board': {'file': 'shachikutrain-technique.json', 'record': 'cross_source.harddrop.drawn_t_not_fired',
                      'table': 16, 'board': 1},
     'label': 'harddrop\'s 「Donation T-Spin Double」: the T\'s nub fills the two rows the TSD clears over a hole '
              'three deep, which is open again after the clear',
     'reading': 'harddrop Shachiku_Train table 16 board 1, recorded (and pinned) in shachikutrain-technique.json\'s '
                'cross_source.harddrop.drawn_t_not_fired, in occupancy only: every drawn cell c, C in the rows the TSD '
                'clears, the T U',
     'rows': _b('---------- -----c---- ----cc---- CCCCCUUUCC CCCCCCUCCC cccccc-ccc cccccc-ccc cccccc-ccc')},
]

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived') and not n.get('external')]


#: every board of the page at which the rule fires, at its drawn T (a spin board) or at a resting T placement making
#: two rows full (a form or a question drawn without its T), with every donating column's hole cell: complete both
#: ways (`rule_accounting`). Every answer and every form the page draws is here; no question is.
DRAWINGS: list = [
    {'board': 'intro.z', 't_cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'holes': [[4, 0]]},
    {'board': 'one.o', 't_cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'holes': [[4, 0]]},
    {'board': 'one.s', 't_cells': [[2, 1], [2, 2], [2, 3], [3, 2]], 'holes': [[4, 0]]},
    {'board': 'one.z', 't_cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'holes': [[4, 0]]},
    {'board': 'one.l_a', 't_cells': [[2, 1], [2, 2], [2, 3], [3, 2]], 'holes': [[4, 1]]},
    {'board': 'one.l_b', 't_cells': [[2, 3], [2, 4], [2, 5], [3, 4]], 'holes': [[4, 0]]},
    {'board': 'q1.1.answer', 't_cells': [[4, 3], [4, 4], [4, 5], [5, 4]], 'holes': [[6, 6]]},
    {'board': 'q1.2.answer', 't_cells': [[4, 6], [4, 7], [4, 8], [5, 7]], 'holes': [[6, 9]]},
    {'board': 'q1.3.answer', 't_cells': [[4, 1], [4, 2], [4, 3], [5, 2]], 'holes': [[6, 5]]},
    {'board': 'q1.4.answer', 't_cells': [[4, 1], [4, 2], [4, 3], [5, 2]], 'holes': [[6, 6]]},
    {'board': 'q1.5.answer', 't_cells': [[3, 6], [3, 7], [3, 8], [4, 7]], 'holes': [[5, 0]]},
    {'board': 'q1.6.answer', 't_cells': [[4, 3], [4, 4], [4, 5], [5, 4]], 'holes': [[6, 0]]},
    {'board': 'two.jz_a', 't_cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'holes': [[4, 0]]},
    {'board': 'two.jz_b', 't_cells': [[2, 0], [2, 1], [2, 2], [3, 1]], 'holes': [[4, 4]]},
    {'board': 'two.sz_a', 't_cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'holes': [[4, 4], [4, 5]]},
    {'board': 'two.sz_b', 't_cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'holes': [[4, 0]]},
    {'board': 'two.js_a', 't_cells': [[2, 4], [2, 5], [2, 6], [3, 5]], 'holes': [[4, 1]]},
    {'board': 'two.js_b', 't_cells': [[2, 3], [2, 4], [2, 5], [3, 4]], 'holes': [[4, 0], [4, 1]]},
    {'board': 'two.oz', 't_cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'holes': [[4, 0]]},
    {'board': 'hole2.a', 't_cells': [[4, 5], [4, 6], [4, 7], [5, 6]], 'holes': [[6, 0]]},
    {'board': 'hole2.b', 't_cells': [[4, 5], [4, 6], [4, 7], [5, 6]], 'holes': [[6, 1]]},
    {'board': 'hole3.a', 't_cells': [[3, 5], [3, 6], [3, 7], [4, 6]], 'holes': [[5, 1]]},
    {'board': 'hole3.b', 't_cells': [[3, 5], [3, 6], [3, 7], [4, 6]], 'holes': [[5, 0]]},
    {'board': 'hole4.a', 't_cells': [[2, 5], [2, 6], [2, 7], [3, 6]], 'holes': [[4, 1]]},
    {'board': 'hole4.b', 't_cells': [[2, 5], [2, 6], [2, 7], [3, 6]], 'holes': [[4, 0]]},
    {'board': 'hole5.a', 't_cells': [[1, 5], [1, 6], [1, 7], [2, 6]], 'holes': [[3, 1]]},
    {'board': 'hole5.b', 't_cells': [[1, 5], [1, 6], [1, 7], [2, 6]], 'holes': [[3, 0]]},
    {'board': 'fin.lj', 't_cells': [[3, 4], [4, 3], [4, 4], [5, 4]], 'holes': [[6, 0]]},
    {'board': 'fin.to', 't_cells': [[3, 3], [4, 2], [4, 3], [5, 3]], 'holes': [[6, 0]]},
    {'board': 'q2.1.answer', 't_cells': [[4, 5], [4, 6], [4, 7], [5, 6]], 'holes': [[6, 3]]},
    {'board': 'q2.2.answer', 't_cells': [[3, 5], [3, 6], [3, 7], [4, 6]], 'holes': [[5, 3]]},
    {'board': 'q2.3.answer', 't_cells': [[3, 2], [3, 3], [3, 4], [4, 3]], 'holes': [[5, 4], [5, 5]]},
    {'board': 'q2.4.answer', 't_cells': [[3, 5], [3, 6], [3, 7], [4, 6]], 'holes': [[5, 9]]},
    {'board': 'q2.5.answer', 't_cells': [[3, 1], [3, 2], [3, 3], [4, 2]], 'holes': [[5, 6]]},
    {'board': 'q2.6.answer', 't_cells': [[4, 3], [4, 4], [4, 5], [5, 4]], 'holes': [[6, 0]]},
    {'board': 'q2.7.answer', 't_cells': [[3, 5], [3, 6], [3, 7], [4, 6]], 'holes': [[5, 3]]},
    {'board': 'q2.8.answer', 't_cells': [[3, 4], [3, 5], [3, 6], [4, 5]], 'holes': [[5, 9]]},
    {'board': 'q2.9.answer', 't_cells': [[3, 5], [3, 6], [3, 7], [4, 6]], 'holes': [[5, 9]]},
    {'board': 'q2.10.answer', 't_cells': [[5, 0], [5, 1], [5, 2], [6, 1]], 'holes': [[7, 8]]},
    {'board': 'q2.11.answer', 't_cells': [[4, 2], [4, 3], [4, 4], [5, 3]], 'holes': [[6, 9]]},
    {'board': 'q2.12.answer', 't_cells': [[3, 4], [3, 5], [3, 6], [4, 5]], 'holes': [[5, 8]]},
    {'board': 'q2.13.answer', 't_cells': [[5, 3], [5, 4], [5, 5], [6, 4]], 'holes': [[7, 0]]},
    {'board': 'q2.14.answer', 't_cells': [[3, 0], [3, 1], [3, 2], [4, 1]], 'holes': [[5, 5]]},
    {'board': 'q2.15.answer', 't_cells': [[5, 4], [5, 5], [5, 6], [6, 5]], 'holes': [[7, 9]]},
    {'board': 'q2.16.answer', 't_cells': [[3, 4], [3, 5], [3, 6], [4, 5]], 'holes': [[5, 7], [5, 8], [5, 9]]},
    {'board': 'q2.17.answer', 't_cells': [[2, 6], [2, 7], [2, 8], [3, 7]], 'holes': [[4, 3], [4, 5], [4, 6]]},
]

VARIANTS = [
    {
        'id': 'rule', 'board': 'intro.z', 'spin': 'TSD', 'lines': 2, 'window_basis': 'rule',
        'window': {'rows': [2, 3], 'cols': [2, 4]}, 't_cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'roof_cells': [],
        'rule': 'a column donates when, at its topmost cell that is empty, in no row the T makes full and directly under '
                'a cell of such a row, every filled cell of the column above it is in those rows (so the clear opens it '
                'from the top) and the cell above it is not the T; in play each covering cell must also be the T or a '
                'complete piece, never garbage (ownership is not drawn, so the gate reads the occupancy half)',
        'payoff': {'kind': 'well_quad', 'board': 'intro.z', 'piece': 'I', 'lines': 4, 'well_cell_pre_clear': [4, 0],
                   'well_cell_after': [4, 0],
                   'note': 'harddrop\'s, not the page\'s: the page says only that the hole stays open to dig '
                           '(「下穴が開いた状態を維持」); the Tetris into it is the Donation page\'s next step. The well '
                           'cell is the hit\'s own column\'s hole (the nearest to the T), under the cleared rows, so the '
                           'clear does not move it'},
        'drawings': DRAWINGS,
    },
]

RULE_NOT_FIRED: list = [
    {'board': 'intro.l3', 'reason': 'the page\'s own mistake: the L fills three rows, not two, so a filled cell of the '
                                    'column lies under the rows the TSD clears and the hole stays covered '
                                    '(「2列ではなく3列を埋めてしまった」)'},
    {'board': 'nub.hd', 'reason': 'harddrop\'s 「Donation T-Spin Double」: only the T\'s nub covers the hole, which yachi '
                                  'reads as a plain T-spin (2026-10-26: 「呢個係普通tspin」), so the rule\'s clause 3 '
                                  'refuses it'},
]

#: measured by the `other:` rule: every other technique window over every board of this page, the record the
#: qualify rule `other_page` mirrors in play (a T another page's window fires on is that page's, not this one's)
OTHER_WINDOWS = {
    'fires_on_donation': [
        {'file': 'kaidan-technique.json', 'variant': 'kaidan', 'board': 'one.s', 'cells': [[2, 1], [2, 2], [2, 3], [3, 2]], 'mirrored': [True]},
        {'file': 'kaidan-technique.json', 'variant': 'kaidan', 'board': 'q1.1.answer', 'cells': [[4, 3], [4, 4], [4, 5], [5, 4]], 'mirrored': [False]},
        {'file': 'kaidan-technique.json', 'variant': 'kaidan', 'board': 'q1.2.answer', 'cells': [[4, 6], [4, 7], [4, 8], [5, 7]], 'mirrored': [False]},
        {'file': 'parapet-technique.json', 'variant': 'parapet', 'board': 'one.l_a', 'cells': [[2, 1], [2, 2], [2, 3], [3, 2]], 'mirrored': [False]},
        {'file': 'parapet-technique.json', 'variant': 'parapet_tss', 'board': 'one.l_a', 'cells': [[1, 2], [2, 2], [2, 3], [3, 2]], 'mirrored': [False]},
        {'file': 'shachikutrain-technique.json', 'variant': 'shachikutrain', 'board': 'q1.1.answer', 'cells': [[4, 3], [4, 4], [4, 5], [5, 4]], 'mirrored': [False]},
        {'file': 'stmbcave-technique.json', 'variant': 'stmbcave', 'board': 'two.sz_a', 'cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'mirrored': [False]},
        {'file': 'stmbcave-technique.json', 'variant': 'stmbcave', 'board': 'q2.3.answer', 'cells': [[3, 2], [3, 3], [3, 4], [4, 3]], 'mirrored': [False]},
        {'file': 'stmbcave-technique.json', 'variant': 'stmbcave', 'board': 'q2.17.answer', 'cells': [[2, 6], [2, 7], [2, 8], [3, 7]], 'mirrored': [True]},
    ],
}

CROSS_SOURCE = {
    'other_windows': OTHER_WINDOWS,
    'fires': [
        {'file': 'sdpcspin-routes.json', 'node': '3.first.cave', 'variant': 'rule', 'mirrored': False,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': "harddrop's SDPC Spin (another author): its STMB Cave's Z fills the two cleared rows of the column one past the T's arm, the cave open under it (STMB Cave's own window fires too, so in play the T is that page's)"},
        {'file': 'sdpcspin-routes.json', 'node': '3.second.cspin.first#2', 'variant': 'rule', 'mirrored': False,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': "harddrop's SDPC Spin: a bag-5 TSD of the second C-Spin build, over the C-Spin's residue slot (the ダブルダガー shape)"},
        {'file': 'sdpcspin-routes.json', 'node': '3.second.cspin.o_first#2', 'variant': 'rule', 'mirrored': False,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': 'the same build, its O-first order'},
        {'file': 'sdpcspin-routes.json', 'node': '3.second.cspin.l_first#2', 'variant': 'rule', 'mirrored': False,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': 'the same build, its L-first order'},
        {'file': 'sdpcspin-routes.json', 'node': '3.second.cspin.l_first#4', 'variant': 'rule', 'mirrored': False,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': 'the same build, its L-first order, the next board'},
        {'file': 'sdpcspin-routes.json', 'node': '3.third.imperial', 'variant': 'rule', 'mirrored': False,
         'page': 'https://harddrop.com/wiki/SDPC_Spin',
         'note': "harddrop's SDPC Spin: the Imperial Cross TSD; the cross's far arm is covered only inside the cleared rows"},
    ],
    'also': [
        {'file': 'mountainous2-routes.json', 'node': '2.compromise.fire5.bag4#1', 'variant': 'rule', 'mirrored': False,
         'note': "the same author's 山岳積み2号: a bag-4 TSD of the 5巡パフェ, a hole covered only inside the cleared rows"},
        {'file': 'mountainous2-routes.json', 'node': '2.compromise.fire5.bag4#2', 'variant': 'rule', 'mirrored': False,
         'note': 'the same board, its second form'},
        {'file': 'stickspin-routes.json', 'node': '2.sd', 'variant': 'rule', 'mirrored': False,
         'note': "the same author's stick spin: the SDパフェ bag-2 STMB Cave, the cave one past the T's arm"},
        {'file': 'stickspin-routes.json', 'node': '2.sd.imperial.spin', 'variant': 'rule', 'mirrored': False,
         'note': "stick spin's Imperial Cross TSD"},
        {'file': 'stickspin-routes.json', 'node': '2.sd.stmb.spin', 'variant': 'rule', 'mirrored': False,
         'note': 'the SDパフェ STMB Cave with its T drawn'},
    ],
}

KNOWN_DISCREPANCIES: list = [
    {'id': 'intro.l3:colour', 'note': 'the mistake\'s L is drawn as a J\'s shape in L\'s colour (its top cell over '
                                      'the hole, two muted below); occupancy is what the page means'},
    {'id': 'q2.17.answer:colour', 'note': 'the answer\'s two S pieces are drawn in one letter, so the S cells are '
                                          'eight, not four; read as two S pieces by occupancy'},
    {'id': 'q2.10.answer:muting', 'note': 'one cell of a row the TSD clears is drawn unmuted'},
    {'id': 'q2.11.answer:muting', 'note': 'two cells above the rows the TSD clears are drawn muted'},
    {'id': 'q2.14.answer:muting', 'note': 'two cells above the rows the TSD clears are drawn muted'},
    {'id': 'q2.15.answer:muting', 'note': 'one cell under the rows the TSD clears is drawn muted'},
    {'id': 'q1.3.answer:question', 'note': 'the answer draws the question\'s bottom hole one column over (column 5, '
                                           'not 4) and its stack around it differently, so it is not the question plus '
                                           'its pieces (no `on`)'},
    {'id': 'q2.12.answer:question', 'note': 'the answer draws one grey cell (row 2, column 7) its question leaves empty, '
                                            'so it is not the question plus its pieces (no `on`)'},
]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'basicdonating',
        'source': SOURCE,
        'terms': TERMS,
        'legend': LEGEND,
        'empty_letters': '',
        'quotes': QUOTES,
        'nodes': NODES,
        'page_order': PAGE_ORDER,
        'basic_form': [],
        'variants': VARIANTS,
        'rule_not_fired': RULE_NOT_FIRED,
        'cross_source': CROSS_SOURCE,
        'known_discrepancies': KNOWN_DISCREPANCIES,
    }


# ── technique-only rules ─────────────────────────────────────────────────────────────────────────
TECHNIQUE_DIR = HERE
#: the page's forms it names as another page's technique: (node, that page's transcription, variant)
NAMED_FORMS = [
    ('one.s', 'kaidan-technique.json', 'kaidan'),           # %Sドネイト(=階段のドネイト)
    ('one.l_a', 'parapet-technique.json', 'parapet'),       # %LドネイトA(=欄干)
    ('two.sz_a', 'stmbcave-technique.json', 'stmbcave'),    # %S%ZドネイトA(=STMB Cave)
]


def _other(path: Path):
    other = json.loads(path.read_text())
    return other, TT.TechniqueSpec(out=path, build=lambda: other, alphabet=frozenset(),
                                   empty_letters=other.get('empty_letters', ''), max_rows=99)


def _pre(n: dict) -> list[str]:
    """A node as the board before its spin: the spin cells (and any `U`) read empty."""
    sc = TT.spin_cells(n) if n['kind'] == 'spin' else set()
    return [''.join('-' if (r, c) in sc or ch == 'U' else ch for c, ch in enumerate(row))
            for r, row in enumerate(n['rows'])]


def _cells(cs) -> list:
    return sorted([r, c] for r, c in cs)


def fires_on_donation(data: dict) -> list[dict]:
    """Every other committed technique window (each variant) over every board of this page, at every resting T."""
    got = []
    mine = [(n['id'], _pre(n)) for n in data['nodes']]
    for f in sorted(TECHNIQUE_DIR.glob('*-technique.json')):
        if f.name == OUT.name:
            continue
        other, ospec = _other(f)
        for v in other['variants']:
            for name, rows in mine:
                for cs in TT.t_placements(rows, SPEC):
                    hands = [m for m in (False, True) if TT.window_fires(other, v, ospec, rows, cs, m)]
                    if hands:
                        got.append({'file': f.name, 'variant': v['id'], 'board': name, 'cells': _cells(cs),
                                    'mirrored': hands})
    return got


def _hd_occ(rows: list[str]) -> list[str]:
    """A harddrop record's board (the T `U`, every other drawn cell a letter) in this file's occupancy letters:
    `U` kept, a drawn cell `C` in a row that would be full with the T and `c` elsewhere, empty `-`."""
    full = {r for r, row in enumerate(rows) if '-' not in row}
    return [''.join('-' if ch == '-' else 'U' if ch == 'U' else ('C' if r in full else 'c') for ch in row)
            for r, row in enumerate(rows)]


def _check_external(data: dict, byid: dict) -> list[str]:
    """An `external` node is a harddrop drawing another transcription records and pins (no second pin here): its
    rows are that record's board in occupancy, and the record names it by table and board."""
    bad = []
    for n in data['nodes']:
        if not n.get('external'):
            continue
        sb = n.get('source_board') or {}
        try:
            other = json.loads((TECHNIQUE_DIR / sb['file']).read_text())
            rec = other
            for part in sb['record'].split('.'):
                rec = rec[part]
        except (KeyError, OSError, TypeError):
            bad.append(f'external: {n["id"]} names no record ({sb})')
            continue
        e = [d for d in rec if (d.get('table'), d.get('board')) == (sb.get('table'), sb.get('board'))]
        if n['external'] != 'harddrop' or len(e) != 1 or n['id'] in data['page_order']:
            bad.append(f'external: {n["id"]} names no single harddrop board, or is in the page order')
        elif n['rows'] != _hd_occ(e[0]['rows']):
            bad.append(f'external: {n["id"]} is not {sb["file"]}\'s table {sb["table"]} board {sb["board"]} in occupancy')
    return bad


def extra_checks(data: dict):
    bad: list[str] = []
    xs = data.get('cross_source', {})
    ow = xs.get('other_windows', {})
    key = lambda e: json.dumps(e, sort_keys=True)
    # other: complete both ways — the record is what the qualify rule `other_page` reads in play
    for name, fn in (('fires_on_donation', fires_on_donation),):
        got = fn(data)
        if sorted(map(key, got)) != sorted(map(key, ow.get(name, []))):
            bad.append(f'other: {name} is measured as {len(got)} entries, the record holds '
                       f'{len(ow.get(name, []))} that differ')
    # named: a form the page names as another page's technique is one that page's window fires on, at a T the
    # board allows, AND a donation by the rule (the qualify rule `other_page` then gives it to that page)
    byid = {n['id']: n for n in data['nodes']}
    fon = ow.get('fires_on_donation', [])
    drawn = {d['board'] for v in data['variants'] for d in v.get('drawings', [])}
    for nid, f, vid in NAMED_FORMS:
        if nid not in byid:
            bad.append(f'named: {nid} is no node')
            continue
        if not any(e['board'] == nid and e['file'] == f and e['variant'] == vid for e in fon):
            bad.append(f'named: {nid} is named as {f}\'s technique, and its window fires nowhere on it')
        if nid not in drawn:
            bad.append(f'named: {nid} is named as a donation (another page\'s), and the rule does not fire on it')
    bad += _check_external(data, byid)
    # question: an answer drawn without `on` is one the page draws with a grey cell its question does not have
    # (or without one it has); that is a `<id>:question` discrepancy, and an answer that IS its question plus its
    # pieces must carry `on`
    measured: set[str] = set()
    for n in data['nodes']:
        if n['kind'] != 'spin' or not n['id'].endswith('.answer') or 'on' in n:
            continue
        q = byid.get(n['id'][:-len('.answer')])
        if q is None:
            continue
        h = max(len(q['rows']), len(n['rows']))
        pad = lambda rows: ['-' * 10] * (h - len(rows)) + list(rows)
        qa, aa = pad(q['rows']), pad(n['rows'])
        lost = [(r, c) for r in range(h) for c in range(10) if qa[r][c] != '-' and aa[r][c] == '-']
        grey = [(r, c) for r in range(h) for c in range(10) if qa[r][c] == '-' and aa[r][c] in 'cC']
        if lost or grey:
            measured.add(f'{n["id"]}:question')
        else:
            bad.append(f'question: {n["id"]} is its question plus pieces and carries no `on`')
    return bad, measured


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='',
    upper_groups={u: 'merge' for u in 'IJLOSZ'},
    max_rows=MAX_ROWS,
    extra_checks=extra_checks,
    snapshot_indented=True,
    muting_slips=True,
)


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def node(d: dict, nid: str) -> dict:
    return next(n for n in d['nodes'] if n['id'] == nid)


def var(d: dict, vid: str) -> dict:
    return next(v for v in d['variants'] if v['id'] == vid)


def _set(rows: list, r: int, c: int, ch: str) -> None:
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _drop_named(d: dict, nid: str) -> None:
    ow = d['cross_source']['other_windows']['fires_on_donation']
    ow[:] = [e for e in ow if e['board'] != nid]


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'q1.1')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: _set(node(d, 'q1.6.answer')['rows'], 7, 5, '-'), 'an answer not its question plus its pieces', 'build:'),
    (lambda d: var(d, 'rule')['drawings'].pop(), 'a drawing the rule fires on unrecorded', 'rule:'),
    (lambda d: var(d, 'rule')['drawings'].append({'board': 'q1.1', 't_cells': [[0, 0], [0, 1], [0, 2], [1, 1]],
                                                  'holes': [[2, 0]]}), 'a drawing recorded that the rule misses', 'rule:'),
    (lambda d: var(d, 'rule')['drawings'][0]['holes'].append([9, 9]), 'a drawing\'s holes not the measured ones',
     'rule:'),
    (lambda d: d['rule_not_fired'].pop(0), 'the 3-row L mistake unrecorded', 'rule:'),
    (lambda d: d['rule_not_fired'].append({'board': 'q2.1.answer', 'reason': 'x'}),
     'an answer the rule fires on named as missed', 'rule:'),
    (lambda d: var(d, 'rule')['window'].__setitem__('cols', [1, 4]), 'the window not the T\'s box', 'window:'),
    (lambda d: var(d, 'rule')['payoff'].__setitem__('lines', 3), 'the payoff not a Tetris', 'window:'),
    (lambda d: var(d, 'rule')['payoff']['well_cell_pre_clear'].__setitem__(0, 5), 'the payoff cell not the hole',
     'window:'),
    (lambda d: d['known_discrepancies'].pop(), 'a discrepancy unnamed', 'discrepancy:'),
    (lambda d: d['known_discrepancies'].append({'id': 'q1.1.answer:muting', 'note': 'x'}), 'a stale discrepancy',
     'discrepancy:'),
    (lambda d: node(d, 'q1.1.answer').pop('on'), 'an answer that is its question plus pieces with no `on`', 'question:'),
    (lambda d: d['cross_source']['fires'].pop(), 'a routes board the window fires on unrecorded', 'cross:'),
    (lambda d: d['cross_source']['other_windows']['fires_on_donation'].pop(), 'another window on this page unrecorded',
     'other:'),
    (lambda d: _drop_named(d, 'one.s'), 'the named 階段のドネイト form no longer the Kaidan window\'s', 'named:'),
    (lambda d: d['variants'].append(copy.deepcopy(d['variants'][0])), 'two rule variants', 'rule:'),
    (lambda d: _set(node(d, 'nub.hd')['rows'], 7, 0, '-'), 'the external board not harddrop\'s', 'external:'),
    (lambda d: node(d, 'nub.hd')['source_board'].__setitem__('board', 0), 'the external board pointing elsewhere',
     'external:'),
    (lambda d: d['page_order'].append('nub.hd'), 'the external board in the page order', 'grammar:'),
]


def selftest() -> int:
    return TT.run_selftest(SPEC, MUTANTS, {'board': ('CUUUOOCC', 'CUUUOOCc'), 'text': ('解答', '解笞')})


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))

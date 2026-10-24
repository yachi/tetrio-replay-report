"""Transcribe shiwehi.com's DT砲(途中DT) page into `dtcannon-technique.json`.

    python3 -m pipeline.openers.extract_dtcannon_shapes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_dtcannon_shapes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_dtcannon_shapes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_dtcannon_shapes --html-dir <dir> --write  # ...and rewrite

The tenth MID-GAME TECHNIQUE page (中盤テンプレ・ドネイト): 「TSD→TSTを打つことができる中盤テンプレ」. A TSD slot,
a TST slot standing on its nub column — one cell under the nub, the stem running up over the T's middle under an
overhang — so the T goes in laid FLAT, pointing down, its two cleared rows drop the overhang onto the stem, and
the second T stands up into an ordinary TST, nub toward the wall (「2つ目は普通のTSTです」). The page calls it 途中DT
to tell it from 開幕DT砲, the opener of the same name; this is the mid-game form, built from a TSD waiting for an I
(72積み), from a TSD waiting for its roof, and from a finished TSD, and it is a TECHNIQUE page: the shape is matched
on a partial stack at any lock, never as a whole board from an empty one.

DECISION: the spin is a TSD (a full T-spin, 2 lines) and the anchor is the T's four cells — the flat, nub-down T
of STMB Cave, ダブルダガー, BT砲, 千鳥格子, 社畜トレイン, 欄干 and 階段のドネイト. The follow-up is a TST (`followup.lines`
3), which the matcher already reads (BT砲). NO SHARED FILE CHANGED: the matcher, the planner, the gate and the
renderer are untouched; this is a data addition.

WHAT TELLS IT FROM BT砲, measured in the facts test: both are TSD → TST, but BT砲's TST stands beside the T's left
end (its bottom cell under the T's left arm, its overhang against the wall), while this one stands over the nub
column (its bottom cell under the nub). Anchored on the same flat T the two windows clash on a cell.

WHY THE WINDOW IS THE AGREEMENT BOX (`window_basis: agreement`). The page draws its builds on whole stacks whose
cells right of the slots differ (72積み, a 63積み roof, a finished TSD with a J hooked over it, DTDT's opener
residue), so STSD's bounding box would read cells the drawings disagree on. The window is the box every drawing
of the shape agrees on: this page's eight (the basic form, its five builds, DTDT's TSD and the board のそみ砲
leaves, the last two found by the window firing on them and then measured to be the shape) and the two DT Cannon
continuations harddrop's SDPC Spin page draws (another site, other authors; `sdpcspin-routes.json`'s
`3.second.cspin.dt#1` / `#2`, mirrored). It comes out seven rows by four columns: the wall column, the TST's
left wall, the stem, and the overhang's second column, from the overhang down to the stem's bottom cell. Widening
it meets a disagreement (row 0 holds the J hook and the O of two builds; the column right of it holds every
build's own stack) or leaves the basic form's board.

WHERE THE TRANSCRIPTION COMES FROM. `NODES` is checked against the page's raw HTML (`dtcannon.html`, fetched with
curl through a CA bundle adding the Let's Encrypt YE2 intermediate the server omits, TLS verification on), and the
page's renderer colour map (`column-exp.js`, hashed in `SOURCE['renderer']`) is what the two letters the other
pages never drew (`p`, `y`) are read from. It was first transcribed from a markdown rendering (its hash is kept in
`fetch_method`); the raw HTML agrees with that transcription board for board. Twenty boards, in page order.
harddrop's DT_Cannon page is a redirect to Double Triple Cannon Setups, whose revision is pinned in
`HARDDROP` and read with `hd_cell`; `harddrop_checks` holds its drawings, misses and near misses complete both ways.

THE CATALOGUES ARE NOT A CROSS-SOURCE, measured: `opener-fields.json`'s DT Cannon fields are five and six rows
tall — bag 1 and 2, before the overhang the TST needs — so the seven-row window cannot be placed on them at all;
`wiki-openers.json` draws no DT field.

WHAT IS AN INFERENCE, flagged in the JSON (`reading`, the legend) rather than in prose only:

  * `U` is the T the spin places; upper-case `C` the earlier cells in a row the spin clears, muted (checked by
    the spin rule). On the build boards the page also draws the stack beside the slot in upper case (the I-wait
    form's right side): read as a cell placed by the build, filled.
  * the TST board is drawn after the TSD with its own T in; the board between them, which the page does not draw,
    is DERIVED (`basic.after`, the TST board less its U) and measured to be what the TSD leaves.
  * the TSD-roof section draws its S-shaped piece in the Z's letter and its Z-shaped piece in the S's (named
    `:colour` discrepancies); occupancy only is ever compared.
  * on the finished-TSD section `p` is the page's pink cell (「下図ピンクマスを埋めないように黄色マスを埋める」) and the
    lone `o` its yellow cell: markers, read as filled, no pieces.
  * on DTDT's TST board `y` is a letter no other transcribed page draws, two rows of a Z's shape: read as filled.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers import technique_transcription as TT
from pipeline.openers.extract_btcannon_shapes import _sections
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS
from pipeline.openers.route_transcription import EMPTY, WIDTH, after_spin, bottom
from pipeline.openers.technique_transcription import node

HERE = Path(__file__).resolve().parent
OUT = HERE / 'dtcannon-technique.json'

ALPHABET = frozenset('-cCUijlozsIJLOSZpy')
MAX_ROWS = 11


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/dtcannon.php',
    'title': 'DT砲(途中DT)(Mid-game Double Triple Cannon)',
    'author': 'しゑひ(shiwehi)',
    'created': '2021-04-02',
    'updated': '2024-08-29',
    'fetched': '2026-10-24',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle that adds the '
                    'Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), the method STSD, BT砲 and '
                    '階段のドネイト used. The snapshot is the page\'s raw HTML, byte for byte; every board is plain text in '
                    'it, 20 ten-wide boards in page order. (The first transcription, 2026-10-23, was checked against a '
                    'markdown rendering, sha256 b069e04f665c1a5cba7704efaa58957aa4f519785eabeef496afc1d6d33014f8, 8120 '
                    'bytes, because the host was refused then; every board and every quote is the same against this raw '
                    'HTML, and the page\'s creation_date meta is 2021-04-02, not the 2021-04-01 that version recorded.)',
    'snapshot_file': 'dtcannon.html',
    'snapshot_sha256': 'cd4a82c025962c9475091d674f7f2542842de43a0bb6ca9343577dd501c41986',
    'snapshot_bytes': 31366,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable in CI: the page '
                     'is not committed and cannot be fetched there. Re-check with --html-dir after any refetch (with '
                     'harddrop\'s Double_Triple_Cannon_Setups.wikitext beside it); an HTML hash moves with ANY byte of '
                     'the page (ads, sidebar, a date), so a moved hash means "read the board diff", not "the boards '
                     'changed". Sentences are compared against the page with its tags dropped.',
    'renderer': {
        'url': 'https://shiwehi.com/tetris/mutual/column-exp.js?date=20210408',
        'read': '2026-10-24',
        'sha256': '95c431a4147f9c30fc0e1bae935e6af6f5669c3d2fa1edfc388848e69ab62570',
        'sha256_note': 'the same bytes STSD and BT砲 recorded, re-fetched for this page to read `p` and `y`',
        'colorMap_used': {
            'p': '#ff33ff (pink): the finished-TSD section\'s marker cell',
            'y': '#ffa6a6 with a rgba(255,0,0,0.5) gradient, the pale Z; reversedCharMap swaps it with r, the pale S',
            'c C U': '#a3a3a3, #cccccc, #c8a6ff with a #8400ff dot (gradientMap)',
            'j l o z s i': '#0011ff #ff7b00 #eeee00 #ff0000 #33ff00 #00b7ff',
            '-': '#000000',
        },
        'mirror_button': 'body.reversed swaps j<->l, s<->z (and upper case, and r<->y); the page draws only one hand',
    },
    'decorative_images': ['DT砲(途中DT)(Mid-game Double Triple Cannon)タイトル画像', 'DT砲の消し方 (an animated gif, not transcribed)'],
    'references': ['./dtcannonopener.php (開幕DT砲)', './derivedtcannonop.php (開幕DT砲からの派生, DTDT)',
                   './mrtspinsstd.php (Mr. T-Spin\'s STD, のそみ砲)', './tspin.php'],
    'unfetched': [],
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ',
    '-': 'empty',
    'c': 'a cell filled before this diagram (any piece, or garbage), grey',
    'i j l o z s': 'a cell of that piece',
    'I J L O S Z': 'a cell of that piece drawn muted (in a row a spin clears, or a piece placed earlier); checked '
                   'whole with its lower-case cells',
    'U': 'a cell of the T the spin places (the renderer\'s "the T goes here")',
    'C': 'an earlier cell in a row the spin clears (muted; checked on every spin board), or on a build board a cell '
         'of the stack the build places beside the slot, drawn muted (OUR READING)',
    'p': 'the finished-TSD section\'s pink cell (the renderer\'s #ff33ff), the one the page says must stay open '
         'while the yellow one is filled (「下図ピンクマスを埋めないように黄色マスを埋める」); a marker, read as filled (OUR '
         'READING)',
    'y': 'a letter on DTDT\'s TST board alone, four cells in a Z\'s shape: the renderer\'s pale Z (#ffa6a6, the '
         'mirror partner of `r`, the pale S); the page does not say what the pale colour marks, so it is read as '
         'filled, no piece (OUR READING)',
    '%X': 'the X piece',
}

QUOTES = [
    {'id': 'h.shape', 'verbatim': 'DT砲の形と消し方'},
    {'id': 'shape', 'verbatim': 'DT砲の形は以下の通りで、その名の通り、TSDを打った後にTSTを打つことができます。'},
    {'id': 'h.rotate', 'verbatim': '回転方法'},
    {'id': 'keys', 'verbatim': 'switchのキーで解説していきます。'},
    {'id': 'rotate2', 'verbatim': '初めに右回転をしてから壁に寄せ、下におろしてから左回転、左回転です。'},
    {'id': 'tst', 'verbatim': '1つ目の%Tさえ入れることができれば、2つ目は普通のTSTです。'},
    {'id': 'h.build', 'verbatim': 'DT砲の作り方'},
    {'id': 'h.wait', 'verbatim': 'TSD屋根付き1列待ちの形'},
    {'id': 'wait', 'verbatim': 'DT砲の最も作りやすい形は、TSDの形を作って%I待ちをしている時に、代わりに%J%Lを立てて作る方法です。'},
    {'id': 'wait.normal', 'verbatim': '通常上図のようになるところを、下図のようにすることでDT砲の形を作れます。'},
    {'id': 'hole', 'verbatim': '穴が2マス以上必要'},
    {'id': 'wait.any', 'verbatim': '上図では72積みの形で説明していますが、同様の形があればどこでも構いません。'},
    {'id': 'h.roof', 'verbatim': 'TSD屋根待ちの形から'},
    {'id': 'roof', 'verbatim': 'TSDの屋根待ちの状態から下図のようにして途中DTを組むことができます。'},
    {'id': 'roof.l', 'verbatim': '基本的には%L(左右反転の場合は%S)を使用します。'},
    {'id': 'roof.fill', 'verbatim': 'この方法でDT砲を作った時、TSTを打つ前に%Zの左上のマスを埋める必要がありますが、63積みの3側に'
                                   '低い屋根を付けた場合は、%I以外で埋めようとすると%Tが入らなくなってしまうので注意してください。'},
    {'id': 'h.done', 'verbatim': 'TSD完成形から'},
    {'id': 'done', 'verbatim': 'TSDの形が完成している状態からも、条件によっては途中DTを組むことができます。'},
    {'id': 'done.wall', 'verbatim': '屋根が無い側の壁は2マスまで'},
    {'id': 'done.j', 'verbatim': '逆に、屋根がある側の壁は%Jを引っ掛けることができるので、屋根にプラスして4マスまで高くすることができます。'},
    {'id': 'h.derived', 'verbatim': '開幕テンプレ後の派生としてのDT砲'},
    {'id': 'derived', 'verbatim': '開幕テンプレからの派生としてDT砲を組むテンプレもいくつか存在します。'},
    {'id': 'h.dtdt', 'verbatim': 'DTDT(開幕DT砲からの派生)'},
    {'id': 'h.nozomi', 'verbatim': 'のそみ砲(Mr.T-Spin\'s STDからの派生)'},
    {'id': 'nozomi', 'verbatim': 'のそみ砲と呼ばれるDT砲派生が存在します。'},
]

_WAIT = '---------- ---------- ---------- ---------- ---zz----- ----zz---- cc-ccccccc cc-ccccccc'

NODES = [
    {'id': 'basic', 'kind': 'base', 'caption_quote': 'shape',
     'label': 'the basic form: a TSD slot, and a TST slot standing on its nub column under an overhang',
     'rows': _b('---------- --cc------ ---c------ cc-ccccccc c--ccccccc c---cccccc cc-ccccccc cc-ccccccc')},
    {'id': 'basic.spin', 'kind': 'spin', 'spin_of': 'basic', 'spin_piece': 'U', 'spin': 'TSD', 'lines': 2,
     'caption_quote': 'shape', 'label': 'the T laid flat, pointing down, into the TSD slot',
     'rows': _b('---------- --cc------ ---c------ cc-ccccccc c--ccccccc CUUUCCCCCC CCUCCCCCCC cc-ccccccc')},
    {'id': 'tst.spin', 'kind': 'spin', 'spin_of': 'basic.after', 'on': 'basic.after', 'adds': 'U', 'spin_piece': 'U',
     'spin': 'TST', 'lines': 3, 'caption_quote': 'tst',
     'label': 'what the TSD leaves, with the second T stood up into it: a TST (the page draws this board, not the one before it)',
     'rows': _b('---------- ---------- ---------- --cc------ ---c------ CCUCCCCCCC CUUCCCCCCC CCUCCCCCCC')},
    {'id': 'wait.terrain', 'kind': 'base', 'caption_quote': 'wait',
     'label': 'a TSD slot roofed by a Z, waiting for an I in the column beside it (72積み)', 'rows': _b(_WAIT)},
    {'id': 'wait.i', 'kind': 'build', 'on': 'wait.terrain', 'adds': 'iC', 'caption_quote': 'wait.normal',
     'label': 'what usually happens: the I goes into the column, the stack beside the slot built up',
     'rows': _b('---------- ---------- i--------- i--------- i--zz----- i---zzCCCC cc-ccccccc cc-ccccccc')},
    {'id': 'wait.terrain2', 'kind': 'base', 'same_occupancy_as': 'wait.terrain', 'caption_quote': 'wait.normal',
     'label': 'the same terrain again', 'rows': _b(_WAIT)},
    {'id': 'wait.dt', 'kind': 'build', 'on': 'wait.terrain2', 'adds': 'jlC', 'caption_quote': 'wait.normal',
     'label': 'a J and an L stood up instead: the DT shape', 'rows':
     _b('---------- --ll------ ---l------ jj-lCCCCCC j--zzCCCCC j---zzCCCC cc-ccccccc cc-ccccccc')},
    {'id': 'roof.so', 'kind': 'build', 'on': 'roof.base', 'adds': 'so', 'caption_quote': 'roof',
     'label': 'the TSD roofed with an O and the S-lettered piece over it: by occupancy the DT shape too (measured)',
     'rows':
     _b('---------- ----ss---- -----ss--- --zz-oo--- -zz--oo--- ccc---cccc cccc-ccccc cccc-ccccc')},
    {'id': 'roof.build', 'kind': 'build', 'on': 'roof.base', 'adds': 'li', 'caption_quote': 'roof.l',
     'label': 'an L stood up and an I laid flat instead: the DT shape', 'rows':
     _b('---------- ----ll---- -----l---- --zz-l---- -zz--iiii- ccc---cccc cccc-ccccc cccc-ccccc')},
    {'id': 'roof.fill', 'kind': 'illustration', 'caption_quote': 'roof.fill',
     'label': 'the cell over the Z\'s upper left filled by an I before the TST (63積み with a low roof)', 'rows':
     _b('---------- ---------- i--------- i--SS----- i---SS---- iZZ-OOCCCC ZZ--OOCCCC ccc-cccccc')},
    {'id': 'done.terrain', 'kind': 'base', 'caption_quote': 'done',
     'label': 'a finished TSD slot', 'rows':
     _b('---------- ---------- -----ccccc -----ccccc ccc--ccccc ccc---cccc cccc-ccccc cccc-ccccc')},
    {'id': 'done.build', 'kind': 'build', 'on': 'done.terrain', 'adds': 'oi', 'caption_quote': 'done',
     'label': 'an I laid beside it and an O over the stem: the DT shape', 'rows':
     _b('----oo---- ----oo---- -----ccccc iiii-ccccc ccc--ccccc ccc---cccc cccc-ccccc cccc-ccccc')},
    {'id': 'done.cells', 'kind': 'illustration', 'caption_quote': 'done.wall',
     'label': 'the pink cell that must stay open and the yellow cell to fill (the side without a roof two high at most)',
     'rows': _b('---------- ---------- ----cccccc --p--ccccc ---o-ccccc ccc--ccccc ccc---cccc cccc-ccccc cccc-ccccc')},
    {'id': 'jhook.build', 'kind': 'build', 'on': 'jhook.terrain', 'adds': 'j', 'caption_quote': 'done.j',
     'label': 'the side with the roof built four high, a J hooked over it', 'rows':
     _b('----jj---- ----jccccc ----jccccc -----ccccc cccc-ccccc ccc--ccccc ccc---cccc cccc-ccccc cccc-ccccc')},
    {'id': 'dtdt.spin', 'kind': 'spin', 'spin_of': 'dtdt.base', 'on': 'dtdt.base', 'adds': 'U', 'spin_piece': 'U',
     'spin': 'TSD', 'lines': 2, 'caption_quote': 'h.dtdt',
     'label': 'DTDT: the DT shape built on 開幕DT砲\'s residue, its TSD drawn', 'rows':
     _b('---------- ---------- ---------- -----z---- --ll-zz--- ---lssz--i jj-lcssooi j--ccccooi JUUUCCCCCI '
        'CCUCCCCCCC cc-ccccccc')},
    {'id': 'dtdt.tst', 'kind': 'spin', 'spin_of': 'dtdt.tst.base', 'on': 'dtdt.tst.base', 'adds': 'U', 'spin_piece': 'U',
     'spin': 'TST', 'lines': 3, 'caption_quote': 'h.dtdt',
     'label': 'DTDT later: its TST drawn, with the next bag stacked over it', 'rows':
     _b('---------- -------yy- --------yy -----ss-oo i---ss--oo iljjjc---z ilccjcc-zz illcccc-zc CCUCCCCCCC '
        'CUUCCCCCCC CCUCCCCCCC')},
    {'id': 'nozomi.1', 'kind': 'illustration', 'caption_quote': 'nozomi',
     'label': 'のそみ砲, from Mr. T-Spin\'s STD: its T-spin Single drawn', 'rows':
     _b('---------- ---------- ---------- ---------i ----j----i ----j----i l--jj--z-i LUUUSSZZOO llUss-z-oo')},
    {'id': 'nozomi.2', 'kind': 'illustration', 'caption_quote': 'nozomi',
     'label': 'のそみ砲: a T-spin Triple drawn', 'rows':
     _b('---------- --------l- --------l- --------ll -oo------c SOOZCIJJUC SSZZCIJUUC CSZCCIJCUC cccccic-cc')},
    {'id': 'nozomi.3', 'kind': 'illustration', 'caption_quote': 'nozomi',
     'label': 'のそみ砲: a stood T clearing one row', 'rows':
     _b('---------- ---------- --------zi ----ss-zzi ---ss--zci ---jj---ci llljoo-Ucc lccjoo-UUc CCCCCCCUCC')},
    {'id': 'nozomi.4', 'kind': 'illustration', 'caption_quote': 'nozomi',
     'label': 'のそみ砲: the board it leaves, the DT shape built on it (measured)', 'rows':
     _b('---------- ---i--szz- ---i--sszz llli---scc looicc-ccc joocc--ccc jjjcc---cc cccccc-ccc cccccc-ccc')},
    # ── derived: drawn nowhere on the page ──
    {'id': 'basic.after', 'kind': 'derived', 'derived': True,
     'reading': 'tst.spin less its U: what the TSD leaves (measured to be basic.spin after its clear, by occupancy); '
                'its rows the TST clears are drawn muted, as the page draws them on tst.spin',
     'rows': _b('---------- ---------- ---------- --cc------ ---c------ CC-CCCCCCC C--CCCCCCC CC-CCCCCCC')},
    {'id': 'roof.base', 'kind': 'derived', 'derived': True,
     'reading': 'roof.build less its L and I (equally roof.so less its S-letter and O): the TSD waiting for its roof',
     'rows': _b('---------- ---------- ---------- --zz------ -zz------- ccc---cccc cccc-ccccc cccc-ccccc')},
    {'id': 'jhook.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'jhook.build less its J: the finished TSD with the roof side four high',
     'rows': _b('---------- -----ccccc -----ccccc -----ccccc cccc-ccccc ccc--ccccc ccc---cccc cccc-ccccc cccc-ccccc')},
    {'id': 'dtdt.base', 'kind': 'derived', 'derived': True,
     'reading': 'dtdt.spin less its U: the DTDT board before its TSD',
     'rows': _b('---------- ---------- ---------- -----z---- --ll-zz--- ---lssz--i jj-lcssooi j--ccccooi J---CCCCCI '
                'CC-CCCCCCC cc-ccccccc')},
    {'id': 'dtdt.tst.base', 'kind': 'derived', 'derived': True,
     'reading': 'dtdt.tst less its U: the DTDT board before its TST, the next bag over it',
     'rows': _b('---------- -------yy- --------yy -----ss-oo i---ss--oo iljjjc---z ilccjcc-zz illcccc-zc CC-CCCCCCC '
                'C--CCCCCCC CC-CCCCCCC')},
]

_SLOT = [[5, 1], [5, 2], [5, 3], [6, 2]]
_SLOT2 = [[5, 3], [5, 4], [5, 5], [6, 4]]

#: the variant's window, in basic.spin's frame
VARIANTS = [{
    'id': 'dtcannon', 'board': 'basic.spin', 'spin': 'TSD', 'lines': 2,
    'window_basis': 'agreement',
    'window': {'rows': [1, 7], 'cols': [0, 3]},
    't_cells': _SLOT,
    'roof_cells': [[1, 2], [1, 3], [2, 3], [3, 0], [3, 1], [3, 3], [4, 0], [4, 3]],
    'window_note': 'in basic.spin\'s frame, row 0 the top: the AGREEMENT BOX of this page\'s eight drawings of the shape '
                   'and harddrop SDPC Spin\'s two DT Cannon continuations. Column 0 is the wall; rows 5-6 are the rows '
                   'the TSD clears (entailed by the clear at a full TSD, NaiveClauseForced); above them the TST slot\'s '
                   'nub row (row 4: the stem over the T\'s middle and the nub toward the wall, walled both sides), the '
                   'stem\'s row walled both sides (row 3), the overhang\'s second cell (row 2) and the overhang over the '
                   'stem (row 1); under them the stem\'s bottom cell, walled both sides (row 7). Everything right of '
                   'column 3, and row 0, is outside: the drawings disagree there. Occupancy only, never colour; '
                   'garbage is filled.',
    'agreement': [
        {'board': 'basic', 't_cells': _SLOT, 'mirrored': False},
        {'board': 'wait.dt', 't_cells': _SLOT, 'mirrored': False},
        {'board': 'roof.build', 't_cells': _SLOT2, 'mirrored': False},
        {'board': 'done.build', 't_cells': _SLOT2, 'mirrored': False},
        {'board': 'jhook.build', 't_cells': [[6, 3], [6, 4], [6, 5], [7, 4]], 'mirrored': False},
        {'board': 'dtdt.base', 't_cells': [[8, 1], [8, 2], [8, 3], [9, 2]], 'mirrored': False},
        {'board': 'roof.so', 't_cells': _SLOT2, 'mirrored': False},
        {'board': 'nozomi.4', 't_cells': [[6, 5], [6, 6], [6, 7], [7, 6]], 'mirrored': False},
    ],
    'followup': {'board': 'basic.after', 'spin': 'TST', 'lines': 3,
                 't_cells_pre_clear': [[3, 2], [4, 1], [4, 2], [7, 2]],
                 't_cells_after': [[5, 2], [6, 1], [6, 2], [7, 2]],
                 'note': 'the T stood up into the TST slot, nub toward the wall (the page: 「2つ目は普通のTSTです」). '
                         'Before the TSD its cells are split by the two cleared rows (three above them, the stem\'s '
                         'bottom cell under them, under the TSD\'s nub); the TSD joins them, and the matcher carries the '
                         'slot through every later clear to the next T.'},
    'fires_on': ['basic', 'wait.dt', 'roof.so', 'roof.build', 'done.build', 'jhook.build', 'dtdt.base', 'nozomi.4'],
    'misses': ['wait.terrain', 'wait.i', 'wait.terrain2', 'roof.fill', 'done.terrain', 'done.cells',
               'tst.spin', 'basic.after', 'dtdt.tst', 'nozomi.1', 'nozomi.2', 'nozomi.3'],
}]

#: harddrop SDPC Spin's DT Cannon continuations, as `sdpcspin-routes.json` transcribes them
ROUTES_DRAWINGS = {'file': 'sdpcspin-routes.json', 'nodes': ['3.second.cspin.dt#1', '3.second.cspin.dt#2'],
                   'mirrored': True,
                   'note': 'harddrop\'s SDPC Spin page (another site, other authors) draws a DT Cannon on its second '
                           'C-Spin build\'s residue, in two forms, mirrored; the U cells are the TSD\'s T'}

CATALOGUE = {
    'file': 'opener-fields.json',
    'names': ['DT Cannon {JP: 開幕DT砲} / Double Triple Cannon / Azunyan Cannon {JP: あずにゃん砲}',
              'DT Cannon 2 {JP: 開幕DT砲2号}', 'Super Speed DT Cannon {JP: 超DT}'],
    'reason': 'five- and six-row opener fields, drawn before the overhang the TST needs: the seven-row window cannot be '
              'placed on them (every placement leaves the board), so they are no cross-source. wiki-openers.json '
              'draws no DT field.',
}

def _hd(table: int, board: int, section: str | None, mirrored: bool, text: str, **kw) -> dict:
    return {'table': table, 'board': board, 'section': section, 'mirrored': mirrored, 'rows': text.split(), **kw}


HARDDROP = {
    'page': 'https://harddrop.com/wiki/Double_Triple_Cannon_Setups',
    'title': 'Double Triple Cannon Setups',
    'redirect_from': 'https://harddrop.com/wiki/DT_Cannon (a #REDIRECT page, revision 16028, 2014-02-10)',
    'oldid': 42401,
    'revision_sha1': 'b65fa20b9eb07853093c76841e7350767785e0ef',
    'revision_timestamp': '2025-03-10T13:29:27Z',
    'fetched': '2026-10-24',
    'fetch_method': 'the pinned revision\'s own bytes from the MediaWiki API (api.php?action=query&prop=revisions&'
                    'titles=DT_Cannon&redirects=1&rvprop=ids|sha1|size|timestamp|content&rvslots=main), with Python\'s '
                    'urllib and a descriptive User-Agent (NOT curl); the API\'s sha1 equals the sha1 of the bytes, and '
                    '42401 was the page\'s latest revision when fetched',
    'snapshot_file': 'Double_Triple_Cannon_Setups.wikitext',
    'snapshot_sha256': '21ea01e0214d4dffafc5e51752a9370530fcb39769bec6615f5c38a13f2f833f',
    'snapshot_bytes': 42123,
    'snapshot_note': 'not committed: check_wikitext_sources refetches the pinned revision weekly through api.php and '
                     're-checks it with --wikitext-dir; a person re-checks it with --html-dir, the file beside '
                     'dtcannon.html',
    'author_note': 'the setup is designed by TKI (the page\'s first sentence); the page is harddrop\'s, edited by its '
                   'wiki editors — another site and other authors than shiwehi.com',
    'reading': {'blank': '-, -- and an empty cell', 'P SP': 'U, the T placed into the spin (SP muted, in a cleared row)',
                "'T -T": "empty: a marker for a T still to come (two DT STSD drawings)",
                'other': 'any other code, its last letter in lower case (G grey, Q light grey, a two-letter Sx the '
                         'muted x), every one FILLED'},
    'note': 'every one of the page\'s 133 boards is in exactly one list or none, measured both ways by '
            'harddrop_page_problems: a board in none draws no T, the window fires nowhere on it, and it has no near '
            'miss (a terrain without its overhang, a step between two drawings, or another setup altogether). The '
            '`drawings` are agreement drawings, and they do not move the window: it is the same box without them '
            '(the page\'s drawings and SDPC Spin\'s already fix it), so they corroborate it and decide nothing',
    'drawings': [
        _hd(1, 0, None, False, '-----gg--- ------g--- ggggg-gggg gggg--gggg ggggUUUggg gggggUgggg ggggg-gggg'),
        _hd(37, 3, 'Similar DT Attack', False, '---------- ---------- -----z---- --llzz---i ---lzs---i jj-lgssooi j--gggsooi gUUUgggggg ggUggggggg jg-ggggggg'),
        _hd(38, 3, 'Dulse Flame (Darth Flame)', False, '---------- --gg------ ---gqqqqqq gg-gqqqqqq g--ggqqqqq gUUUggqggg ggUggggggg gg-ggggggg g-gggggggg'),
    ],
    'drawn_t_not_fired': [
        _hd(1, 3, None, False, '---------- ---------- -----gg--- ------g--- gggggUgggg ggggUUgggg gggggUgggg', t='stood', lines=3, window="not the window's T", note="the page's opening animation, its TST: a stood T"),
        _hd(33, 1, 'DT STSD', False, '---------- --gg------ ---ggggggg gg-ggggggg g--ggggggg gUUUgggggg ggUggggggg g--ggggggg', t='flat-down', lines=2, window='disagrees', note="DT STSD's first TSD: harddrop's own text, 「one further cell is empty at the bottom」, is the one window cell that disagrees (filled in every drawing of the window, empty here)"),
        _hd(33, 3, 'DT STSD', False, '---------- ---------- ---------- --gg------ ---ggggggg ggUggggggg gUUggggggg g-Uggggggg', t='stood', lines=2, window="not the window's T", note="DT STSD: the STSD's stood T, after the first TSD"),
        _hd(33, 5, 'DT STSD', False, '---------- ---------- ---------- ---------- ---------- --gg------ UUUggggggg gU-ggggggg', t='flat-down', lines=1, window='disagrees', note='DT STSD: its last T, drawn flat after the earlier clears; it fills one row as drawn'),
        _hd(34, 2, 'DT STSD', False, '---------- -----qqqqq -----qqqqq ---llqqqqq ----lqqqqq lllUlqqqqq lzUUjqqqqq zz-Ujqqqqq z--jjqqqqq', t='stood', lines=2, window="not the window's T", note="DT STSD stacked one line higher: the STSD's stood T"),
        _hd(35, 2, 'Similar DT Attack', False, '---------- --ll--s--- ---lzzssoo ---lgzzsoo ---ggiiiig gUUUgggggg ggUggggggg -g-ggggggg', t='flat-down', lines=2, window='disagrees', note="Similar DT Attack's TSD: the S takes the O's place, so the TST's left wall is not the window's"),
        _hd(35, 5, 'Similar DT Attack', False, '---------- ---------- ---------- --gg--g--- ---ggggggg ggUggggggg gUUggggggg ggUggggggg', t='stood', lines=3, window="not the window's T", note='Similar DT Attack: its TST, a stood T'),
        _hd(37, 5, 'Similar DT Attack', False, '---------- jj-------- j----ss--- j-zzssiwww l--zzgiwww l-ggggioog ll-gggioog ggUggggggg gUUggggggg ggUggggggg', t='stood', lines=3, window="not the window's T", note='Similar DT Attack: its TST, a stood T'),
        _hd(38, 0, 'Dulse Flame (Darth Flame)', False, '---------- ---------- ---------- ---ll----- ----l----- oo-sl----- oo-ss----U j-zzs---UU jjjzziiiiU', t='stood', lines=1, window="not the window's T", note='Dulse Flame: its opening T-Spin Mini, a stood T clearing one row'),
        _hd(39, 1, 'Dulse Flame (Darth Flame)', False, '---------- --gg------ ---gqqqqqq ggUgqqqqqq gUUggqqqqq ggUggggggg g-gggggggg', t='stood', lines=3, window="not the window's T", note='Dulse Flame: its TST, a stood T'),
        _hd(39, 3, 'Dulse Flame (Darth Flame)', False, '---------- ---------- ---------- ---------- --gg------ UUUgqqqqqq gUgggggggg', t='flat-down', lines=2, window='disagrees', note="Dulse Flame: the further TSD under the overhang the DT Cannon left (the page's Triple Double Attack shape), not the window's"),
    ],
    'fires_without_slot': [
        _hd(0, 0, None, False, '-----gg--- ------g--- ggggg-gggg gggg--gggg gggg---ggg ggggg-gggg ggggg-gggg'),
        _hd(2, 0, 'Empty Field Setups', False, '---------- --ll------ ---l------ jj-ltggggg j--tttiggg j---ssizzg oo-sslijzz oo-lllijjj'),
        _hd(3, 0, 'Empty Field Setups', False, '---------- ---------- ---------- ---------- ----i----- --lli---s- ---li--zss jj-liizzss j--llizzss j---lizzss oo-jliztss oo-jjjttts'),
        _hd(3, 1, 'Empty Field Setups', False, '---------- ------jj-- ------j--- ----zzj-ll ----izz--l --llioo-sl ---lioozss jj-liizzss j--llizzss j---lizzss oo-jliztss oo-jjjttts'),
        _hd(4, 0, 'Empty Field Setups', False, '---------- --oo------ --oo------ ---l------ jj-lgggggg j--llggggg j---tgggsg oo-tttzzss oo-iiiizzs'),
        _hd(4, 1, 'Empty Field Setups', False, '---------- --oo------ --oo------ ---l------ jj-lgggggg j--llsgggg j---tsszzg oo-tttsjzz oo-iiiijjj'),
        _hd(4, 2, 'Empty Field Setups', False, '---------- --s------- --ss------ ---s------ jj-ooggggg j--ooggggz j---tgggzz oo-tttggzl oo-iiiilll'),
        _hd(4, 3, 'Empty Field Setups', False, '---------- ---------- --zz------ ---zz----- jj-ooggggg j--ooggggg j---tggggg oo-tttgggg oo-iiiiggg'),
        _hd(4, 4, 'Empty Field Setups', False, '---------- --oo------ --oo----ss ---l---ssi jj-lzzjjji j--llzzlji j---tlllsi oo-tttzzss oo-iiiizzs'),
        _hd(5, 0, 'Empty Field Setups', False, '---------- ---------- --ll------ ---l------ jj-lgggggg j--jjjgggi j---zjslli oo-zztssli oo-ztttsli'),
        _hd(5, 1, 'Empty Field Setups', False, '---------- ---------- --ll------ ---l------ jj-lsszggg j--sszzggi j---zzslli oo-zztssli oo-ztttsli'),
        _hd(5, 2, 'Empty Field Setups', False, '---------- ---------- --zz------ ---zz----- jj-ooggggg j--ooggggi j---zgslli oo-zztssli oo-ztttsli'),
        _hd(5, 3, 'Empty Field Setups', False, '---------- ----l----- --lll----- ---jj----- jj-jsggggg j--jssgggi j---zsslli oo-zztssli oo-ztttsli'),
        _hd(6, 0, 'Empty Field Setups', False, '---------- ---ss----- --ssz----- ---zz----- jj-ztgslli j--tttssli j---oolsli oo-joolzzi oo-jjjllzz'),
        _hd(6, 1, 'Empty Field Setups', False, '---------- ---------- --ttt----- ---tss---i jj-sslzzgi j--llllzzi j---oolzzi oo-joollzz oo-jjjiiii'),
        _hd(7, 0, 'Empty Field Setups', False, '---------- --s------- --ss------ ---sz----- jj-zzggggg j--zjggggg j---jggggg oo-jjggggl oo-iiiilll'),
        _hd(7, 1, 'Empty Field Setups', False, '---------- ---------- --ttt----- ---tz----- jj-zzggggg j--zjggggg j---jgggss oo-jjggssl oo-iiiilll'),
        _hd(8, 0, 'Empty Field Setups', False, '---------- --s------- --ss------ ---sz----- jj-zzggggg j--zjggggg j---jggggg oo-jjlgggg oo-llliiii'),
        _hd(8, 1, 'Empty Field Setups', False, '---------- ---------- --ttt----- ---tz----- jj-zzggggg j--zjggggg j---jggggg oo-jjlgggg oo-llliiii'),
        _hd(9, 0, 'Empty Field Setups', True, '---------- i-----jj-- i--l--j--- illlzzj-ll isszjzz--l sszzjs---l oozjjss-oo ooiiiis-oo'),
        _hd(10, 0, 'Empty Field Setups', False, '---------- --s------- --ss------ ---s------ jj-sgggggz j--ssgggzz j---sgglzt oo-oollltt oo-ooiiiit'),
        _hd(10, 1, 'Empty Field Setups', False, '---------- ---ss----- --ssz----- ---zz----- jj-ztggggg j--tttgggg j---ssgggg oo-sslgggg oo-llliiii'),
        _hd(10, 2, 'Empty Field Setups', False, '---------- ---------- --ll------ ---l------ jj-ltggggg j--tttiggg j---ssizzg oo-sslijzz oo-lllijjj'),
        _hd(10, 3, 'Empty Field Setups', False, '---------- ---------- --ll------ ---l------ jj-ltggggg j--tttiggg j---zjilsg oo-zzjilss oo-zjjills'),
        _hd(10, 4, 'Empty Field Setups', False, '---------- ---------- --ll------ ---l------ jj-lssgggg j--sstgggi j---zttggi oo-zztlggi oo-zlllggi'),
        _hd(11, 0, 'Empty Field Setups', False, '---------- --ll------ ---l------ jj-ltggggg j--tttiggg j---ssizzg oo-sslijzz oo-lllijjj'),
        _hd(12, 0, 'Empty Field Setups', False, '---------- --ll------ ---l------ jj-ltggggg j--tttiggg j---zjilsg oo-zzjilss oo-zjjills'),
        _hd(13, 0, 'Empty Field Setups', False, '---------- -----s---- --ll-ss--- ---lzzs--i jj-lgzzooi j--ggggooi j---gggggi gg-ggggggg gg-ggggggg'),
        _hd(13, 1, 'Empty Field Setups', False, '---------- ---------z --ll----zz ---l--sszi jj-lgssooi j--ggggooi j---gggggi gg-ggggggg gg-ggggggg'),
        _hd(13, 2, 'Empty Field Setups', False, '---------- ---------- --lls--z-- ---lsszz-i jj-lgszooi j--ggggooi j---gggggi gg-ggggggg gg-ggggggg'),
        _hd(13, 3, 'Empty Field Setups', False, '---------- ---------- --ll----ss ---lzz-ssi jj-lgzzooi j--ggggooi j---gggggi gg-ggggggg gg-ggggggg'),
        _hd(13, 4, 'Empty Field Setups', False, '---------- ---ss----- --sszl---- ---zzl---i jj-zgllooi j--ggggooi j---gggggi gg-ggggggg gg-ggggggg'),
        _hd(14, 1, 'Lower Notch and Overhang', False, '---------- --zz------ ---zz----- gg-oo----- g--ooggggg g---gggggg gg-ggggggg gg-ggggggg'),
        _hd(14, 2, 'Lower Notch and Overhang', False, '---------- --ll------ ---l------ gg-lss---- g--ssggggg g---gggggg gg-ggggggg gg-ggggggg'),
        _hd(14, 3, 'Lower Notch and Overhang', False, '--oo------ --oo------ ---l------ gg-l------ g--llggggg g---gggggg gg-ggggggg gg-ggggggg'),
        _hd(14, 4, 'Lower Notch and Overhang', False, '---------- --ll------ ---lj----- gg-lj----- g--jjggggg g---gggggg gg-ggggggg gg-ggggggg'),
        _hd(15, 1, 'Lower Notch and Overhang', False, '---------- --ll------ ---l------ gg-l------ g--llggggg g---lggggg gg-glggggg gg-ggggggg'),
        _hd(15, 2, 'Lower Notch and Overhang', False, '--oo------ --oo------ ---jj----- gg-ji----- g--jiggggg g---iggggg gg-giggggg gg-ggggggg'),
        _hd(16, 1, 'Lower Notch and Overhang', False, '--s------- --ss------ ---sz----- gg-zz----- g--zgggggg g---gggggg gg-ggggggg gg-ggggggg'),
        _hd(16, 2, 'Lower Notch and Overhang', False, '---------- --zz------ ---zz----- gg-lll---- g--lgggggg g---gggggg gg-ggggggg gg-ggggggg'),
        _hd(16, 3, 'Lower Notch and Overhang', False, '--oo------ --oo------ ---t------ gg-tt----- g--tgggggg g---gggggg gg-ggggggg gg-ggggggg'),
        _hd(17, 1, 'Lower Notch and Overhang', False, '--ll------ ---l------ gg-l------ g--zz-gggg g---zzgggg gg-ggggggg gg-ggggggg'),
        _hd(17, 2, 'Lower Notch and Overhang', False, '--zz------ ---zz----- gg-sll---- g--sslgggg g---slgggg gg-ggggggg gg-ggggggg'),
        _hd(17, 3, 'Lower Notch and Overhang', False, '--ll------ ---l------ gg-ltjj--- g--ttjgggg g---tjgggg gg-ggggggg gg-ggggggg'),
        _hd(33, 0, 'DT STSD', False, '---------- --gg------ ---ggggggg gg-ggggggg g--ggggggg g---gggggg gg-ggggggg gq-ggggggg', note='DT STSD\'s terrain with its one further empty cell drawn light grey (Q); read as filled, as every Q is, so it is the DT Cannon and the window fires'),
        _hd(38, 2, 'Dulse Flame (Darth Flame)', False, '---------- --ll------ ---l------ jj-l------ j--gg----- j---gi-zoo gg-ggizzoo gg-ggizssg g-gggissgg'),
        _hd(40, 0, 'Stacking DT Cannons', False, '---------- ---------- ---------- ---zgggggg --zzgggggg --zllggggg ---llggggg jj-llggggg j--llggggg j---zggggg oo-zzggggg oo-zgggggg jj-sgggggg j--ssggggg j---sggggg oo-ooggggg oo-ooggggg'),
    ],
    'near_misses': [
        _hd(18, 1, 'Higher Notch', False, 'jj-ggggggg j--ggggggg j---gggggg gg-ggggggg gg-ggggggg', misses=[{'t_cells': [[2, 1], [2, 2], [2, 3], [3, 2]], 'mirrored': False, 'disagree': [], 'off_board': 8}], note='Higher Notch, drawn cropped: every window cell on the board agrees and the eight above it, the overhang rows, are not drawn'),
        _hd(19, 1, 'Higher Notch', False, 'lll-gggggg lg--gggggg gg---ggggg ggg-gggggg ggg-gggggg', misses=[{'t_cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'mirrored': False, 'disagree': [], 'off_board': 8}], note='Higher Notch, drawn cropped: every window cell on the board agrees and the eight above it, the overhang rows, are not drawn'),
        _hd(20, 1, 'Higher Notch', False, 'ttt-gggggg gt--gggggg gg---ggggg ggg-gggggg ggg-gggggg', misses=[{'t_cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'mirrored': False, 'disagree': [], 'off_board': 8}], note='Higher Notch, drawn cropped: every window cell on the board agrees and the eight above it, the overhang rows, are not drawn'),
        _hd(21, 1, 'Higher Notch', False, 'iiii-ggggg ggg--ggggg ggg---gggg gggg-ggggg gggg-ggggg', misses=[{'t_cells': [[2, 3], [2, 4], [2, 5], [3, 4]], 'mirrored': False, 'disagree': [], 'off_board': 8}], note='Higher Notch, drawn cropped: every window cell on the board agrees and the eight above it, the overhang rows, are not drawn'),
        _hd(22, 1, 'Higher Notch', False, '-ss-gggggg ss--gggggg gg---ggggg ggg-gggggg ggg-gggggg', misses=[{'t_cells': [[2, 2], [2, 3], [2, 4], [3, 3]], 'mirrored': False, 'disagree': [], 'off_board': 8}], note='Higher Notch, drawn cropped: every window cell on the board agrees and the eight above it, the overhang rows, are not drawn'),
        _hd(34, 0, 'DT STSD', False, '---------- ---------- ---lloos-- ----loossi ijj-ltzzsi ij--tttzzi ij---zjooi iss-zzjool ss--zjjlll', misses=[{'t_cells': [[6, 2], [6, 3], [6, 4], [7, 3]], 'mirrored': False, 'disagree': [[8, 2]], 'off_board': 0}], note='DT STSD: the one disagreeing cell is the cell harddrop leaves empty for the STSD'),
        _hd(34, 1, 'DT STSD', False, '---------- --zz------ ---zzqqqqq jj-oollqsq j--ooilsss j---zilsss jj-zzioost j--zlioott j-llliiiit', misses=[{'t_cells': [[5, 1], [5, 2], [5, 3], [6, 2]], 'mirrored': False, 'disagree': [[7, 1]], 'off_board': 0}], note='DT STSD stacked one line higher: the one disagreeing cell is the cell harddrop leaves empty for the STSD'),
    ],
    'u_not_one_t': [
        _hd(38, 1, 'Dulse Flame (Darth Flame)', False, '---------- ---------- ---------- ---------- ---ll----- ----l----- oo-sl----- oo-ss----U j-zzs---UU', note='three U cells: the Dulse Flame mini\'s T after the row it cleared'),
    ],
}

CROSS_SOURCE = {
    'kind': 'routes',
    'label_pattern': 'dt',
    'note': 'the window, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot board of every '
            'committed *-routes.json, with the U cells as the T: it fires on harddrop SDPC Spin\'s two DT Cannon '
            'continuations, mirrored, and on nothing else. The same two boards are external agreement drawings '
            '(`routes_drawings`), beside harddrop\'s own DT Cannon page (`harddrop`): its drawings whose drawn T '
            'the window fires on, and every other board of that page the window fires on or nearly does, recorded.',
    'routes_drawings': ROUTES_DRAWINGS,
    'harddrop': HARDDROP,
    'catalogue': CATALOGUE,
    'fires': [{'file': 'sdpcspin-routes.json', 'node': n, 'variant': 'dtcannon', 'mirrored': True}
              for n in ROUTES_DRAWINGS['nodes']],
    'also': [],
    'labelled_not_fired': [],
}

_SWAP = ('the TSD-roof section draws its S-shaped piece in the Z\'s letter and its Z-shaped piece in the S\'s (the 72積み section draws its Z as a Z); transcribed as drawn, occupancy only is compared')
_DTSWAP = ('DTDT\'s boards draw the S-shaped piece in the Z\'s letter and the Z-shaped piece in the S\'s, as the TSD-roof section does; transcribed as drawn, occupancy only is compared')

KNOWN_DISCREPANCIES: list[dict] = [
    {'id': 'roof.so:colour', 'note': _SWAP},
    {'id': 'roof.build:colour', 'note': _SWAP},
    {'id': 'roof.base:colour', 'note': _SWAP + ' (the derived terrain keeps the page\'s letters)'},
    {'id': 'roof.fill:colour', 'note': _SWAP},
    {'id': 'dtdt.spin:colour', 'note': _DTSWAP},
    {'id': 'dtdt.base:colour', 'note': _DTSWAP + ' (the derived board keeps the page\'s letters)'},
    {'id': 'done.cells:colour', 'note': 'the yellow cell is one cell, drawn in the O\'s letter: a marker, not a piece'},
]

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'dtcannon',
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


def _slot(rows: list[str]) -> list[list[int]]:
    return sorted([r, c] for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == 'U')


def routes_drawings(data: dict | None = None) -> list[dict]:
    """harddrop SDPC Spin's DT Cannon boards as agreement drawings: the slot is the drawn T (`U`), read as empty."""
    data = data or build()
    rd = data['cross_source']['routes_drawings']
    nodes = {n['id']: n for n in json.loads((HERE / rd['file']).read_text())['nodes']}
    out = []
    for nid in rd['nodes']:
        rows = nodes[nid]['rows']
        out.append({'name': f'{rd["file"]} {nid} (harddrop SDPC Spin)',
                    'rows': [row.replace('U', EMPTY) for row in rows],
                    't_cells': _slot(rows), 'mirrored': rd['mirrored']})
    return out


# ── technique-only rules ─────────────────────────────────────────────────────────────────────────
# ── harddrop's drawings ──────────────────────────────────────────────────────────────────────────
def hd_cell(code: str) -> str:
    """One harddrop cell code in this file's reading of it (HARDDROP['reading'])."""
    c = code.strip()
    if c in ('', '-', '--') or c in ("'T", '-T'):
        return EMPTY
    if c in ('P', 'SP'):
        return 'U'
    return c[-1].lower()


def hd_boards(text: str) -> dict:
    """Every board of a harddrop wikitext in this file's reading, keyed (table, board)."""
    return {(i, j): [''.join(hd_cell(c) for c in row) for row in b]
            for i, t in enumerate(RT.wikitext_tables(text)) for j, b in enumerate(t)}


def _pre(rows: list[str]) -> list[str]:
    return [row.replace('U', EMPTY) for row in rows]


def _fires(data: dict, rows: list[str]) -> list[tuple]:
    v, pre = data['variants'][0], _pre(rows)
    return [(frozenset(cs), m) for cs in TT.t_placements(pre, SPEC) for m in (False, True)
            if TT.window_fires(data, v, SPEC, pre, cs, m)]


def t_lie(data: dict, rows: list[str]) -> tuple[str, int, str]:
    """What a drawn T (`U`) on a harddrop board is, measured: its lie (`stood`, `flat-down` — the window's T —
    or `flat-up`), the rows it clears, and why the window does not fire at it: the T is not the window's,
    the window leaves the board in both hands, or a window cell disagrees (`fires` if it fires after all)."""
    slot = _slot(rows)
    rs = sorted({r for r, _ in slot})
    lie = 'stood' if len(rs) == 3 else ('flat-down' if sum(1 for r, _ in slot if r == rs[0]) == 3 else 'flat-up')
    lines = sum(1 for r in rs if EMPTY not in rows[r])
    v, pre, lock = data['variants'][0], _pre(rows), {tuple(x) for x in slot}
    if any(TT.window_fires(data, v, SPEC, pre, lock, m) for m in (False, True)):
        return lie, lines, 'fires'
    if lie != 'flat-down':
        return lie, lines, "not the window's T"
    off = [TT.window_fires(data, v, SPEC, pre, lock, m) is None for m in (False, True)]
    return lie, lines, 'leaves the board' if all(off) else 'disagrees'


def near_misses(data: dict, rows: list[str]) -> list[dict]:
    """The window's NEAR MISSES on a board with no T drawn on which it fires nowhere: every flat, nub-down T
    placement (its four cells empty) that fills its own two rows — a full TSD by occupancy — at which, in
    some hand, the window either disagrees with the board at exactly ONE cell and stays on it, or agrees with
    every cell on the board and leaves it. Each with the disagreeing cells (board frame) and the window cells
    off the board — so a drawing of another DT form is named with the cell that tells it apart."""
    v, out, H = data['variants'][0], [], len(rows)
    for r in range(H - 1):
        for c in range(WIDTH - 2):
            T = [(r, c), (r, c + 1), (r, c + 2), (r + 1, c + 1)]
            if any(rows[a][b] != EMPTY for a, b in T):
                continue
            if any(any(rows[a][k] == EMPTY and (a, k) not in T for k in range(WIDTH)) for a in (r, r + 1)):
                continue
            for m in (False, True):
                W = TT.window_cells(data, v, SPEC, m)
                f = TT.frame_map(data, v, SPEC, set(T), m)
                dis, off = [], 0
                for (a, b), x in W.items():
                    R, C = f(a, b)
                    if not (0 <= R < H and 0 <= C < WIDTH):
                        off += 1
                    elif x != 'T' and (x == '#') != (rows[R][C] != EMPTY):
                        dis.append([R, C])
                if (off == 0 and len(dis) == 1) or (off and not dis):
                    out.append({'t_cells': [list(x) for x in T], 'mirrored': m, 'disagree': sorted(dis), 'off_board': off})
    return out


def harddrop_drawings(data: dict | None = None) -> list[dict]:
    """harddrop's drawings as agreement drawings: the slot is the drawn T (`U`), read as empty."""
    data = data or build()
    return [{'name': f'harddrop Double_Triple_Cannon_Setups table {d["table"]} board {d["board"]} ({d["section"]})',
             'rows': _pre(d['rows']), 't_cells': _slot(d['rows']), 'mirrored': d['mirrored']}
            for d in data['cross_source']['harddrop']['drawings']]


def _hd_every(hd: dict) -> list[dict]:
    return hd['drawings'] + hd['drawn_t_not_fired'] + hd['fires_without_slot'] + hd['near_misses'] + hd['u_not_one_t']


def harddrop_page_problems(data: dict, text: str) -> list[str]:
    """The recorded boards against a harddrop wikitext: each letter for letter at its (table, board) under its
    heading, and the record COMPLETE both ways — `drawings` exactly the boards whose drawn T the window fires on,
    `drawn_t_not_fired` exactly every other board with one drawn T, `fires_without_slot` exactly the boards with
    no T drawn on which it fires, `near_misses` exactly the boards with no T drawn on which it fires nowhere and
    has a near miss (`near_misses()`), and `u_not_one_t` exactly the boards whose drawn cells are not one T."""
    hd = data['cross_source']['harddrop']
    try:
        boards = hd_boards(text)
    except ValueError as e:
        return [f'harddrop: the wikitext does not parse: {e}']
    secs = _sections(text)
    bad = []
    for d in _hd_every(hd):
        k = (d['table'], d['board'])
        if boards.get(k) != d['rows']:
            bad.append(f'harddrop: table {k[0]} board {k[1]} is not the recorded drawing (page {boards.get(k)})')
        elif secs[k[0]] != d['section']:
            bad.append(f'harddrop: table {k[0]} sits under {secs[k[0]]!r}, not {d["section"]!r}')
    got = {'drawings': [], 'drawn_t_not_fired': [], 'fires_without_slot': [], 'near_misses': [], 'u_not_one_t': []}
    v = data['variants'][0]
    for k, rows in sorted(boards.items()):
        slot = {tuple(x) for x in _slot(rows)}
        if len(slot) == 4:
            hands = [m for m in (False, True) if TT.window_fires(data, v, SPEC, _pre(rows), slot, m)]
            got['drawings' if hands else 'drawn_t_not_fired'].append(k)
        elif slot:
            got['u_not_one_t'].append(k)
        elif _fires(data, rows):
            got['fires_without_slot'].append(k)
        elif near_misses(data, rows):
            got['near_misses'].append(k)
    for key, ks in got.items():
        rec = sorted((d['table'], d['board']) for d in hd[key])
        if sorted(ks) != rec:
            bad.append(f'harddrop: {key} on the page is {sorted(ks)}, the record holds {rec}')
    return bad


def harddrop_snapshot_checks(data: dict, html_dir: Path) -> list[str]:
    """`--html-dir` / `--wikitext-dir`: the pinned harddrop revision (a missing file is a failure)."""
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


def harddrop_checks(data: dict) -> list[str]:
    """The record read on its own (the data's copy, so an edit to it is caught without the page): each list's
    boards are what its name says, measured with the same functions the page check uses."""
    hd = data['cross_source'].get('harddrop')
    if not hd:
        return ['harddrop: no harddrop record (the DT Cannon page is required, never defaulted)']
    bad, seen = [], set()
    for d in _hd_every(hd):
        k = (d['table'], d['board'])
        if k in seen:
            bad.append(f'harddrop: table {k[0]} board {k[1]} recorded twice')
        seen.add(k)
        if any(len(r) != WIDTH for r in d['rows']):
            bad.append(f'harddrop: table {k[0]} board {k[1]} is not ten wide')
    for d in hd['drawings']:
        if _fires(data, d['rows']) != [(frozenset(tuple(x) for x in _slot(d['rows'])), d['mirrored'])]:
            bad.append(f'harddrop: the window does not fire once, at the drawn T ({"mirrored" if d["mirrored"] else "as drawn"}), '
                       f'on table {d["table"]} board {d["board"]}')
    for d in hd['drawn_t_not_fired']:
        got = t_lie(data, d['rows']) if len(_slot(d['rows'])) == 4 else None
        if got is None or got != (d['t'], d['lines'], d['window']) or got[2] == 'fires':
            bad.append(f'harddrop: table {d["table"]} board {d["board"]} is {got}, drawn_t_not_fired records '
                       f'{(d.get("t"), d.get("lines"), d.get("window"))}')
        if not d.get('note', '').strip():
            bad.append(f'harddrop: table {d["table"]} board {d["board"]} is in drawn_t_not_fired with no note')
    for d in hd['fires_without_slot']:
        if _slot(d['rows']) or not _fires(data, d['rows']):
            bad.append(f'harddrop: table {d["table"]} board {d["board"]} draws a T, or the window does not fire on it')
    for d in hd['near_misses']:
        if _slot(d['rows']) or _fires(data, d['rows']) or near_misses(data, d['rows']) != d['misses'] \
                or not d.get('note', '').strip():
            bad.append(f'harddrop: table {d["table"]} board {d["board"]}\'s near misses are {near_misses(data, d["rows"])}, '
                       f'the record holds {d.get("misses")} (or it carries no note)')
    for d in hd['u_not_one_t']:
        if len(_slot(d['rows'])) in (0, 4) or not d.get('note', '').strip():
            bad.append(f'harddrop: table {d["table"]} board {d["board"]} draws no T or exactly one, or carries no note')
    return bad


def _synthetic_harddrop(data: dict) -> str:
    """A wikitext holding the recorded boards at their (table, board), every other board blank, each table under
    its recorded heading — the selftest's stand-in for the page CI cannot fetch."""
    hd = data['cross_source']['harddrop']
    every = _hd_every(hd)
    n = max(d['table'] for d in every) + 1
    tables = [[] for _ in range(n)]
    secs = [None] * n
    for d in sorted(every, key=lambda x: (x['table'], x['board'])):
        t = tables[d['table']]
        while len(t) < d['board']:
            t.append([EMPTY * WIDTH] * 4)
        t.append(d['rows'])
        secs[d['table']] = d['section']
    out, last = [], None
    for i, t in enumerate(tables):
        if secs[i] and secs[i] != last:
            out.append(f'== {secs[i]} ==')
            last = secs[i]
        out.append('{|')
        for b in t or [[EMPTY * WIDTH] * 4]:
            out.append('|{{pfstart}}')
            for row in b:
                cells = ['P' if ch == 'U' else ('' if ch == EMPTY else ch.upper()) for ch in row]
                out.append('{{pfrow|' + '|'.join(cells) + '}}')
            out.append('{{pfend}}')
        out.append('|}')
    return '\n'.join(out) + '\n'


def extra_checks(data: dict):
    bad, measured = [], set()
    by = {n['id']: n for n in data['nodes']}
    xs = data['cross_source']
    v = data['variants'][0]
    bad += harddrop_checks(data)
    # routes drawings: the named boards exist, are labelled DT Cannon, draw one T, and fire once at it mirrored
    rd = xs.get('routes_drawings', {})
    rnodes = {n['id']: n for n in json.loads((HERE / rd.get('file', 'sdpcspin-routes.json')).read_text())['nodes']}
    for nid in rd.get('nodes', []):
        n = rnodes.get(nid)
        if not n or 'DT Cannon' not in n.get('label_jp', '') + n.get('label', ''):
            bad.append(f'routes: {nid} is not a DT Cannon board of {rd.get("file")}')
            continue
        pre = [row.replace('U', EMPTY) for row in n['rows']]
        slot = frozenset(tuple(x) for x in _slot(n['rows']))
        hits = [(frozenset(cs), m) for cs in TT.t_placements(pre, SPEC) for m in (False, True)
                if TT.window_fires(data, v, SPEC, pre, cs, m)]
        if len(slot) != 4 or hits != [(slot, rd.get('mirrored'))]:
            bad.append(f'routes: the window fires {len(hits)} time(s) on {nid}, not once at its drawn T')
    if not rd.get('nodes'):
        bad.append('routes: no routes drawing recorded')
    if sorted(a['board'] for a in v.get('agreement', [])) != sorted(v.get('fires_on', [])):
        bad.append('window: the page\'s drawings of the shape (fires_on) are not the agreement\'s page drawings')
    # after: the TSD's after board is derived (the page draws it with the TST's T in), so the after rule is made here
    sp = by['basic.spin']
    got, _n = after_spin([''.join('t' if (r, c) in TT.spin_cells(sp) else ('-' if TT.is_empty(ch, SPEC) else 'c')
                                  for c, ch in enumerate(row)) for r, row in enumerate(sp['rows'])])
    if bottom(TT.occ_of(got, SPEC), TT.MAX_ROWS) != bottom(TT.occ_of(by['basic.after']['rows'], SPEC), TT.MAX_ROWS):
        measured.add('basic.after:after')
    if v['followup']['board'] != 'basic.after' or by['tst.spin'].get('spin_of') != 'basic.after':
        bad.append('after: the follow-up is not read on the derived board the TST stands on')
    # hole: the page's 「穴が2マス以上必要」 is the stem's bottom cell under the nub — empty in every drawing of the shape
    W = TT.window_cells(data, v, SPEC, False)
    (r1, c_nub) = (v['window']['rows'][1], [c for r, c in v['t_cells'] if r == max(r for r, _ in v['t_cells'])][0])
    if W.get((r1, c_nub)) != '.':
        bad.append('hole: the cell under the TSD\'s nub is not a must-empty cell of the window')
    # catalogue: the opener catalogue's DT fields are too short for the window to be placed on
    cat = xs.get('catalogue', {})
    pages = [p for p in json.loads((HERE / cat.get('file', 'opener-fields.json')).read_text())['pages']
             if p['name'] in cat.get('names', [])]
    if not cat.get('names') or {p['name'] for p in pages} != set(cat['names']):
        bad.append(f'catalogue: {cat.get("names")} are not names in {cat.get("file")}')
    for p in pages:
        rows = [''.join(EMPTY if ch == '.' else 'c' for ch in r) for r in p['rows']]
        res = {TT.window_fires(data, v, SPEC, rows, cs, m) for cs in TT.t_placements(rows, SPEC) for m in (False, True)}
        if True in res or None not in res:
            bad.append(f'catalogue: the window is not off the board at every placement of its T on {p["name"]} ({res})')
    if any('DT' in o['wiki'] for o in json.loads((HERE / 'wiki-openers.json').read_text())['openers']):
        bad.append('catalogue: wiki-openers.json now carries a DT field — read it as a cross-source')
    # markers: the finished-TSD section's pink and yellow cells are single cells, not pieces
    dc = by['done.cells']['rows']
    if sum(row.count('p') for row in dc) != 1 or sum(row.count('o') for row in dc) != 1:
        bad.append('markers: done.cells does not draw one pink and one yellow cell')
    return bad, measured


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='',
    upper_groups={u: 'merge' for u in 'IJLOSZ'},
    max_rows=MAX_ROWS,
    extra_checks=extra_checks,
    external_drawings=lambda: routes_drawings() + harddrop_drawings(),
    html_checks=harddrop_snapshot_checks,
    # the same checks read nothing but the pinned wikitext, so a weekly api.php refetch can run them
    wikitext_checks=harddrop_snapshot_checks,
    synthetic_wikitext=lambda d: {d['cross_source']['harddrop']['snapshot_file']: _synthetic_harddrop(d)},
)


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def _set(rows, r, c, ch):
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _var(d):
    return d['variants'][0]


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'wait.terrain')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: d['page_order'].reverse(), 'page_order swapped', 'grammar:'),
    (lambda d: node(d, 'tst.spin').__setitem__('spin_of', 'nowhere'), 'a dangling reference', 'grammar:'),
    (lambda d: _set(node(d, 'wait.dt')['rows'], 7, 0, '-'), 'a build board cell flipped', 'build:'),
    (lambda d: _set(node(d, 'roof.base')['rows'], 7, 9, '-'), 'a derived terrain edited', 'build:'),
    (lambda d: _set(node(d, 'basic.after')['rows'], 2, 2, 'c'), 'the derived after board edited', 'build:'),
    (lambda d: _set(node(d, 'wait.terrain2')['rows'], 4, 4, '-'), 'the second terrain not the first', 'build:'),
    (lambda d: (_set(node(d, 'basic.spin')['rows'], 6, 2, 'C'), _set(node(d, 'basic.spin')['rows'], 4, 2, 'U')),
     'the T pointing up', 'spin:'),
    (lambda d: _set(node(d, 'basic.spin')['rows'], 5, 0, 'c'), 'a cleared row drawn unmuted', 'spin:'),
    (lambda d: node(d, 'basic.spin').__setitem__('lines', 3), 'the TSD\'s line count', 'spin:'),
    (lambda d: node(d, 'tst.spin').__setitem__('lines', 2), 'the TST\'s line count', 'spin:'),
    (lambda d: (_set(node(d, 'basic.after')['rows'], 1, 5, 'c'), _set(node(d, 'tst.spin')['rows'], 1, 5, 'c')),
     'the after board not what the TSD leaves', 'discrepancy:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [0, 4]), 'the window widened by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [0, 2]), 'the window narrowed by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [2, 7]), 'the window without the overhang', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [1, 6]), 'the window without the stem\'s bottom cell', 'window:'),
    (lambda d: _var(d)['roof_cells'].pop(), 'a roof cell unnamed', 'window:'),
    (lambda d: _var(d)['agreement'][2].__setitem__('mirrored', True), 'a build read mirrored', 'window:'),
    (lambda d: _var(d)['agreement'][1].__setitem__('t_cells', [[5, 2], [5, 3], [5, 4], [6, 3]]),
     'a slot moved one column', 'window:'),
    (lambda d: _var(d).__setitem__('agreement', []), 'no page drawing in the agreement', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('t_cells_pre_clear', [[3, 2], [4, 1], [4, 2], [5, 2]]),
     'the follow-up\'s bottom cell read inside the cleared rows', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('lines', 2), 'the follow-up read as a TSD', 'window:'),
    (lambda d: _var(d)['fires_on'].append('wait.i'), 'the usual I-wait board listed as firing', 'window:'),
    (lambda d: _var(d)['misses'].append('done.build'), 'a board it fires on listed as a miss', 'window:'),
    (lambda d: _set(node(d, 'wait.dt')['rows'], 1, 2, 'j'), 'a piece broken', 'discrepancy:'),
    (lambda d: d['cross_source']['routes_drawings']['nodes'].append('3.second.cspin'), 'a routes board that is not a DT',
     'routes:'),
    (lambda d: d['cross_source']['routes_drawings'].__setitem__('mirrored', False), 'the routes drawings read as drawn',
     'routes:'),
    (lambda d: d['cross_source']['catalogue']['names'].append('Not An Opener'), 'a catalogue name that is not there', 'catalogue:'),
    (lambda d: d['cross_source']['fires'].pop(), 'a routes board that fires left unrecorded', 'cross:'),
    (lambda d: _set(node(d, 'done.cells')['rows'], 3, 2, '-'), 'the pink marker dropped', 'markers:'),
    (lambda d: node(d, 'nozomi.1').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['known_discrepancies'].append({'id': 'wait.dt:colour', 'note': 'x'}), 'a stale discrepancy', 'discrepancy:'),
]


def _no_external(spec):
    s = copy.copy(spec)
    s.external_drawings = None
    return s


def _normal_roof_as_drawing(spec):
    s = copy.copy(spec)
    rows = node(build(), 'wait.i')['rows']
    s.external_drawings = lambda: routes_drawings() + harddrop_drawings() + [{'name': 'the usual I-wait board as a DT', 'rows': rows,
                                                         't_cells': [[5, 1], [5, 2], [5, 3], [6, 2]], 'mirrored': False}]
    return s


def _hdl(d, key, table, board):
    return next(x for x in d['cross_source']['harddrop'][key] if (x['table'], x['board']) == (table, board))


MUTANTS += [
    (lambda d: d['cross_source'].pop('harddrop'), 'no harddrop record', 'harddrop:'),
    (lambda d: _hdl(d, 'drawings', 37, 3).__setitem__('mirrored', True), 'a harddrop drawing read mirrored', 'harddrop:'),
    (lambda d: _set(_hdl(d, 'drawings', 38, 3)['rows'], 1, 2, '-'), 'a harddrop drawing\'s overhang dropped', 'harddrop:'),
    (lambda d: _set(_hdl(d, 'fires_without_slot', 2, 0)['rows'], 1, 2, '-'),
     'a no-T harddrop board the window does not fire on', 'harddrop:'),
    (lambda d: _hdl(d, 'drawn_t_not_fired', 33, 1).__setitem__('window', 'leaves the board'),
     'why the window misses a drawn T misrecorded', 'harddrop:'),
    (lambda d: _hdl(d, 'drawn_t_not_fired', 35, 5).__setitem__('lines', 2), 'a missed drawn T\'s line count misrecorded',
     'harddrop:'),
    (lambda d: _hdl(d, 'drawn_t_not_fired', 39, 1).__setitem__('note', ''), 'a missed drawn T with no note', 'harddrop:'),
    (lambda d: _hdl(d, 'near_misses', 34, 0)['misses'][0].__setitem__('disagree', [[8, 3]]),
     'a near miss\'s disagreeing cell misrecorded', 'harddrop:'),
    (lambda d: _set(_hdl(d, 'near_misses', 18, 1)['rows'], 4, 2, 'g'), 'a near miss that is no near miss', 'harddrop:'),
    (lambda d: _hdl(d, 'u_not_one_t', 38, 1).__setitem__('note', ''), 'a board of stray U cells with no note', 'harddrop:'),
    (lambda d: d['cross_source']['harddrop']['drawings'].append(copy.deepcopy(_hdl(d, 'drawings', 1, 0))),
     'a harddrop drawing twice', 'harddrop:'),
]


SPEC_MUTANTS = [
    (_no_external, 'no external drawing (the window checked against this page alone)', 'window:'),
    (_normal_roof_as_drawing, 'the usual I-wait board read as a drawing of the shape', 'window:'),
]


def selftest() -> int:
    return TT.run_selftest(SPEC, MUTANTS, {'board': ('CUUUCCCCCC', 'CUUUCCCCCc'), 'text': ('TSD完成形から', 'TSD完成形かち')},
                           SPEC_MUTANTS)


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))

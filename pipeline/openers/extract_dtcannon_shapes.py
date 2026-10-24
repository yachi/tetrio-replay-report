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

WHERE THE TRANSCRIPTION COMES FROM, and what that does not establish. shiwehi.com could not be fetched from this
session (the environment's network policy refuses the host, HTTP 403 at CONNECT), so `NODES` is checked against
the markdown rendering the Parallel web_fetch service returned (`full_content=true`), the route used for 迷走砲
and はちみつ砲: a leading `-` on a board row comes back escaped as `\\-` and is unescaped by the shared reader.
Twenty boards, in page order. The page's renderer colour map was NOT re-read for this page, so two letters the
other pages never drew (`p`, `y`) are read from the page text alone (the legend says so). Re-check against the
raw HTML with `--html-dir` once the host can be reached; the hash will move (a different rendering), the boards
must not.

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
import json
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers import technique_transcription as TT
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
    'created': '2021-04-01',
    'updated': '2024-08-29',
    'fetched': '2026-10-23',
    'fetch_method': 'mcp__Parallel_Search__web_fetch with full_content=true, which renders the page to markdown (a '
                    'leading "-" on a board row comes back escaped as "\\-" and is unescaped), the route 迷走砲 and '
                    'はちみつ砲 were read by. Plain curl through the session proxy is refused for shiwehi.com in this '
                    'environment (HTTP 403 at CONNECT), so the raw HTML was not read and CI cannot refetch. 20 '
                    'ten-wide boards in page order.',
    'snapshot_file': 'dtcannon.md',
    'snapshot_sha256': 'b069e04f665c1a5cba7704efaa58957aa4f519785eabeef496afc1d6d33014f8',
    'snapshot_bytes': 8120,
    'snapshot_note': 'sha256 of the markdown snapshot this transcription was checked against, saved verbatim from '
                     'the fetch. Not re-verifiable in CI: the page is not committed and cannot be fetched there. '
                     'Re-check with --html-dir after any refetch; a raw-HTML or a re-rendered fetch moves the hash, '
                     'so a moved hash means "read the board diff", not "the boards changed".',
    'renderer_note': 'the page\'s colour map was not read for this page (the host is unreachable from this session); '
                     'the letters BT砲 recorded from shiwehi.com\'s column-exp.js are read the same way here, and `p` '
                     'and `y` from the page\'s own text (legend)',
    'decorative_images': ['DT砲(途中DT)(Mid-game Double Triple Cannon)タイトル画像', 'DT砲の消し方 (an animated gif, not transcribed)'],
    'references': ['./dtcannonopener.php (開幕DT砲)', './derivedtcannonop.php (開幕DT砲からの派生, DTDT)',
                   './mrtspinsstd.php (Mr. T-Spin\'s STD, のそみ砲)', './tspin.php'],
    'unfetched': ['the raw HTML of this page (the host is refused by this session\'s network policy)',
                  'https://harddrop.com/wiki/DT_Cannon (harddrop is refused too; its SDPC Spin page, transcribed in '
                  'sdpcspin-routes.json, is the second source read instead)'],
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
    'p': 'the finished-TSD section\'s pink cell, the one the page says must stay open while the yellow one is '
         'filled (「下図ピンクマスを埋めないように黄色マスを埋める」); a marker, read as filled (OUR READING)',
    'y': 'a letter on DTDT\'s TST board alone, two rows of a Z\'s shape; its colour was not read (OUR READING: '
         'filled, no piece)',
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

CROSS_SOURCE = {
    'kind': 'routes',
    'label_pattern': 'dt',
    'note': 'the window, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot board of every '
            'committed *-routes.json, with the U cells as the T: it fires on harddrop SDPC Spin\'s two DT Cannon '
            'continuations, mirrored, and on nothing else. The same two boards are the window\'s external agreement '
            'drawings (`routes_drawings`).',
    'routes_drawings': ROUTES_DRAWINGS,
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
def extra_checks(data: dict):
    bad, measured = [], set()
    by = {n['id']: n for n in data['nodes']}
    xs = data['cross_source']
    v = data['variants'][0]
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
    external_drawings=lambda: routes_drawings(),
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
    s.external_drawings = lambda: routes_drawings() + [{'name': 'the usual I-wait board as a DT', 'rows': rows,
                                                         't_cells': [[5, 1], [5, 2], [5, 3], [6, 2]], 'mirrored': False}]
    return s


SPEC_MUTANTS = [
    (_no_external, 'no external drawing (the window checked against this page alone)', 'window:'),
    (_normal_roof_as_drawing, 'the usual I-wait board read as a drawing of the shape', 'window:'),
]


def selftest() -> int:
    return TT.run_selftest(SPEC, MUTANTS, {'board': ('CUUUCCCCCC', 'CUUUCCCCCc'), 'text': ('TSD完成形から', 'TSD完成形かち')},
                           SPEC_MUTANTS)


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))

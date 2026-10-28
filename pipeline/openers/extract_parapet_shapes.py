"""Transcribe shiwehi.com's 欄干 (Parapet) page into `parapet-technique.json`.

    python3 -m pipeline.openers.extract_parapet_shapes            # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_parapet_shapes --selftest # prove the verifier has teeth
    python3 -m pipeline.openers.extract_parapet_shapes --html-dir <dir>          # re-check a refetch
    python3 -m pipeline.openers.extract_parapet_shapes --html-dir <dir> --write  # ...and rewrite

The eighth MID-GAME TECHNIQUE page (中盤テンプレ・ドネイト), after STSD, STMB Cave, インペリアルクロス, ダブルダガー, BT砲,
千鳥格子 and 社畜トレイン: 「TSDもしくはTSSを打つことができるドネイト」. An L stood on end, shifted one column (the page: 「%Lを1列ずらして
立てて置き」; it says nothing about the wall), its foot under the T's left arm, and a roof over the T's right end: the T laid flat, pointing down, clears the two rows that
hold the T's arm and the L's foot, and the column under that arm opens from the top to the floor — a donation. The
same terrain takes a TSS: the T stood up, nub right, clears only the foot's row, and the well stays open one row
higher (the page: 「打後の地形が1段高くなるためその後テトリスを送りやすい」).

DECISION: TWO VARIANTS, each measured at the spin its board draws. `parapet` is the TSD (a full T-spin, 2 lines,
the flat T, nub down, the anchor of STMB Cave, ダブルダガー, BT砲, 千鳥格子 and 社畜トレイン); `parapet_tss` is the TSS
on the same terrain (the T stood, nub right; 1 line). The shared matcher reads a variant's opportunity off its
`spin`/`lines` (`technique-facts.ts`), so the TSS variant is measured at full TSSs, with the TSD among its controls.

THE PAYOFF, NOT A FOLLOW-UP. The page draws no second T-spin. What harddrop and Tetrisチャンネル draw or say comes
next is a Tetris into the well the spin kept open (shiwehi names a Tetris only as its reason to fire the TSS rather
than the TSD), so each variant carries `payoff` (an I clearing 4 into the
well cell) in place of `followup`, and the gate's rule (d') checks it on the drawing: the well column is empty top
to bottom on the after board, and every filled cell of it on the spin board is in a row the spin clears (the
re-opening clause, on the DRAWING). That the column re-opens, and that the well is at least two deep, the window
already decides (its must-empty cells under the arm, and its cleared rows), so neither is a payoff: the matcher's
`wellPayoff` measures whether the next piece into the well is an I the engine credits with four lines.

WHY THE WINDOW IS THE AGREEMENT BOX (`window_basis: agreement`, STMB Cave's opt-in), not STSD's bounding box. The
basic form draws a stack right of the slot and a Z (or an O) over it, none of it part of the shape (the two basic
forms differ there). So the window is the box every drawing of the shape agrees on: this page's two basic forms;
the one BT砲's page draws (`btcannon-technique.json`'s `parapet`, same author, the L against the wall); harddrop's
Parapet page (another site, its author Chopin); and Tetrisチャンネル's two (another site; the page this page cites).
Five rows by five columns: the roof row (the L's stem, the slot's two open cells, the roof over the T's right end),
the two rows the TSD clears, and the well's two rows under the T's left arm, walled both sides. Widening it leaves a
drawing (left: BT砲's draws the L against the wall) or meets a disagreement (above: the two basic forms' roofs and
harddrop's S; right: harddrop's S again).

WHERE THE TRANSCRIPTION COMES FROM. `NODES` is a literal, hand-checked transcription of the page's RAW HTML, fetched
the way STSD's was: curl through the session proxy, TLS verification on, with a CA bundle adding the Let's Encrypt
YE2 intermediate shiwehi.com omits. Six boards, plain text in `<div class="ttt">`, one row per line. harddrop's
Parapet page is the pinned revision's own bytes from the MediaWiki API (urllib, a descriptive User-Agent, never
curl); it draws ONE fumen and no pfrow table, decoded once with knewjade's tetris-fumen 1.1.3 (installed for the
decode only; `pipeline/` has no dependency on it) and recorded page by page below — the decode is NOT re-run in CI,
which is an open item, named. Tetrisチャンネル's page is its HTML and its sixteen JPEGs, committed under
`spec/fixtures/tetrisch-parapet/` and read with the jp-forecast pixel sampler (`extract_jp_forecast.extract_one`),
which reads fifteen of them and refuses the sixteenth (008, an annotation: the digits 4-3-2-1 painted on white well
cells). Of these three only harddrop's is a pinned MediaWiki revision, so `check_wikitext_sources` discovers it and
refetches it weekly through api.php (`wikitext_checks`, the harddrop half of `--html-dir`); the shiwehi HTML and the
Tetrisチャンネル page and images are not re-read weekly: an open item.

WHAT IS AN INFERENCE, flagged in the JSON (`reading`, the legend) rather than in prose only:

  * upper-case `C` and `T` in a spin board: the cleared rows, muted (checked by the spin rule).
  * the two basic forms' grey terrains are DERIVED (each form less its page pieces).
  * the TSS slots on the external drawings are OUR READING of their terrain: harddrop, Tetrisチャンネル and BT砲's page
    draw only the TSD there (`window_note`).
  * harddrop's fumen: `G` grey (filled), every other letter its piece (filled); Tetrisチャンネル's images: `#` grey,
    a letter its piece, `.` empty (the sampler's reading).
"""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers import technique_transcription as TT
from pipeline.openers.extract_meisou_routes import TERMS as MEISOU_TERMS
from pipeline.openers.route_transcription import EMPTY, WIDTH, after_spin, bottom
from pipeline.openers.technique_transcription import node

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT = HERE / 'parapet-technique.json'
#: where the `cross:` rule reads the other technique transcriptions; the selftest points it at a planted one
TECHNIQUE_DIR = HERE
BT_FILE = 'btcannon-technique.json'
IMG_DIR = REPO / 'spec' / 'fixtures' / 'tetrisch-parapet'

ALPHABET = frozenset('-cCTlotz')


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://shiwehi.com/tetris/template/parapet.php',
    'title': '欄干(Parapet)',
    'author': 'しゑひ(shiwehi)',
    'published': '2020-10-11',
    'updated': '2021-03-23',
    'fetched': '2026-10-19',
    'fetch_method': 'curl through the session proxy, TLS verification ON, with --cacert naming a bundle '
                    'that adds the Let\'s Encrypt YE2 intermediate (shiwehi.com omits it from its chain), '
                    'the method STSD, STMB Cave, インペリアルクロス, ダブルダガー, BT砲, 千鳥格子, 社畜トレイン, 山岳積み2号 and '
                    'stick spin used. The snapshot is the page\'s raw HTML, byte for byte; every board is plain text '
                    'in it, 6 ten-wide boards in page order.',
    'snapshot_file': 'parapet.html',
    'snapshot_sha256': 'c2e8b4cc3cadd40737decbccfd5a10890f4aad8e8d935ebe46a78cd86ae7945d',
    'snapshot_bytes': 23409,
    'snapshot_note': 'sha256 of the raw HTML this transcription was checked against. Not re-verifiable '
                     'in CI: the page is not committed and cannot be fetched there. Re-check with '
                     '--html-dir after any refetch (with harddrop\'s Parapet.wikitext, Tetrisチャンネル\'s '
                     'tetrisch_parapet.html and its tetrisch-parapet/ images beside it); an HTML hash moves with ANY '
                     'byte of the page (ads, sidebar, a date), so a moved hash means "read the board diff", not "the '
                     'boards changed". Sentences are compared against the page with its tags dropped.',
    'decorative_images': ['欄干(Parapet)タイトル画像'],
    'references': ['https://tetrisch.github.io/main/technic/parapet.html (the page\'s own 参考ページ, read below as '
                   'cross_source.tetrisch)'],
    'unfetched': [],
}

TERMS = {**MEISOU_TERMS,
         'read': '2026-10-11, for 迷走砲: the same terms page, linked from this page\'s footer; not re-read '
                 'for this page'}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall',
    '-': 'empty',
    'c': 'a cell filled before this diagram (any piece, or garbage), grey',
    'l o z': 'a cell of that piece, placed to build the shape',
    't': 'a cell of the T in a row the spin does not clear',
    'T': 'a cell of the T in a row the spin clears (muted; OUR READING, checked: every upper-case row is a full row)',
    'C': 'an earlier cell in a row the spin clears (muted; checked the same way)',
    '%X': 'the X piece',
}

QUOTES = [
    {'id': 'intro', 'verbatim': 'ここでは、欄干(Parapet)という、TSDもしくはTSSを打つことができるドネイトについて紹介していきます。'},
    {'id': 'h.basic', 'verbatim': '基本形と組み方・ラインの消し方'},
    {'id': 'basic', 'verbatim': '基本形は上図の通りです。'},
    {'id': 'build', 'verbatim': '%Tの形が開いているときに、%Lを1列ずらして立てて置き、反対側に屋根をつけることでこの形を作ることができます。'},
    {'id': 'spins', 'verbatim': 'ここから以下のようにしてTSDかTSSを打つことができます。'},
    {'id': 'h.tsd', 'verbatim': 'TSD'},
    {'id': 'h.tss', 'verbatim': 'TSS'},
    {'id': 'why_tss', 'verbatim': 'TSDではなくTSSを打つ理由としては、相手の攻撃の相殺がTSSで良い場合に余計な攻撃を送らずに縦穴をキープでき、'
                                  '打後の地形が1段高くなるためその後テトリスを送りやすいことです。'},
    {'id': 'h.ref', 'verbatim': '参考ページ'},
    {'id': 'ref', 'verbatim': '欄干 Parapet Tetrisチャンネル'},
]

NODES = [
    {'id': 'basic.z', 'kind': 'build', 'on': 'basic.z.terrain', 'adds': 'lz', 'caption_quote': 'basic',
     'label': 'the basic form with a Z roof: an L stood on end, shifted one column (the page\'s 「1列ずらして」), its '
              'foot under the slot\'s left end, and a Z over the slot\'s right end',
     'rows': _b('---------- cl--zz---- cl---zzccc cll-cccccc cc-ccccccc cc-ccccccc')},
    {'id': 'basic.o', 'kind': 'build', 'on': 'basic.o.terrain', 'adds': 'lo', 'caption_quote': 'build',
     'label': 'the basic form with an O roof',
     'rows': _b('----oo---- cl--oo---- cl---ccccc cll-cccccc cc-ccccccc cc-ccccccc')},
    {'id': 'tsd.spin', 'kind': 'spin', 'spin_of': 'basic.z', 'spin': 'TSD', 'lines': 2, 'caption_quote': 'h.tsd',
     'label': 'the T laid flat, pointing down: a TSD clearing the rows of the T\'s arm and the L\'s foot',
     'rows': _b('---------- cc--cc---- CCTTTCCCCC CCCTCCCCCC cc-ccccccc cc-ccccccc')},
    {'id': 'tsd.after', 'kind': 'after', 'after_of': 'tsd.spin',
     'label': 'what the TSD leaves: the column under the T\'s left arm open from the top to the floor',
     'rows': _b('---------- ---------- ---------- cc--cc---- cc-ccccccc cc-ccccccc')},
    {'id': 'tss.spin', 'kind': 'spin', 'spin_of': 'basic.z', 'spin': 'TSS', 'lines': 1, 'caption_quote': 'h.tss',
     'label': 'the same terrain, the T stood up, nub right: a TSS clearing only the L\'s foot row',
     'rows': _b('---------- cc-tcc---- cc-ttccccc CCCTCCCCCC cc-ccccccc cc-ccccccc')},
    {'id': 'tss.after', 'kind': 'after', 'after_of': 'tss.spin',
     'label': 'what the TSS leaves: the same well, open one row higher',
     'rows': _b('---------- ---------- cc-ccc---- cc-ccccccc cc-ccccccc cc-ccccccc')},
    # ── derived: drawn nowhere on the page ──
    {'id': 'basic.z.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'basic.z less its L and Z: the open T slot the page builds from',
     'rows': _b('---------- c--------- c------ccc c---cccccc cc-ccccccc cc-ccccccc')},
    {'id': 'basic.o.terrain', 'kind': 'derived', 'derived': True,
     'reading': 'basic.o less its L and O',
     'rows': _b('---------- c--------- c----ccccc c---cccccc cc-ccccccc cc-ccccccc')},
]

_WINDOW = {'rows': [1, 5], 'cols': [1, 5]}
_TSD_T = [[2, 2], [2, 3], [2, 4], [3, 3]]
_TSS_T = [[1, 3], [2, 3], [2, 4], [3, 3]]
_PAYOFF_NOTE = ('a Tetris into the well under the T\'s left arm, the next step harddrop and Tetrisチャンネル draw '
                '(harddrop: an I into the well on the fumen\'s next page; Tetrisチャンネル: parapet_015). shiwehi names a '
                'Tetris only as its reason to fire the TSS instead of the TSD (「TSDではなくTSSを打つ理由…その後テトリスを'
                '送りやすい」), never as what follows the TSD. The matcher carries the well cell to the first later lock '
                'that puts a cell in its column and asks whether that lock is an I the engine credits with four lines')

#: the variants' windows, in tsd.spin's frame (both the same box)
VARIANTS = [
    {'id': 'parapet', 'board': 'tsd.spin', 'spin': 'TSD', 'lines': 2,
     'window_basis': 'agreement',
     'window': _WINDOW,
     't_cells': _TSD_T,
     'roof_cells': [[1, 1], [1, 4], [1, 5]],
     'window_note': 'in tsd.spin\'s frame, row 0 the top: the AGREEMENT BOX of this page\'s two basic forms, BT砲\'s '
                    'page\'s Parapet, harddrop\'s and Tetrisチャンネル\'s two. Row 1: the L\'s stem, the slot\'s two open '
                    'cells, the roof over the T\'s right end; rows 2-3: the rows the TSD clears (entailed by the clear at a '
                    'full TSD, NaiveClauseForced), holding the L\'s foot under the T\'s left arm; rows 4-5: the well under '
                    'that arm, two deep and walled both sides. Column 0 is outside (BT砲\'s draws the L against the wall), '
                    'row 0 and column 6 are outside (the roofs and harddrop\'s S disagree there). Occupancy only, never '
                    'colour; garbage is filled.',
     'untested_drawn': {'cells': [], 'reason': ''},
     'agreement': [
         {'board': 'basic.z', 't_cells': _TSD_T, 'mirrored': False},
         {'board': 'basic.o', 't_cells': _TSD_T, 'mirrored': False},
     ],
     'payoff': {'kind': 'well_quad', 'board': 'tsd.after', 'piece': 'I', 'lines': 4,
                'well_cell_pre_clear': [4, 2], 'well_cell_after': [4, 2], 'note': _PAYOFF_NOTE},
     'fires_on': ['basic.z', 'basic.o'],
     'misses': ['tss.spin', 'tsd.after', 'tss.after']},
    {'id': 'parapet_tss', 'board': 'tss.spin', 'spin': 'TSS', 'lines': 1,
     'window_basis': 'agreement',
     'window': _WINDOW,
     't_cells': _TSS_T,
     'roof_cells': [],
     'window_note': 'the same box as the TSD\'s, the T stood up with its nub right: (2,2) is must-empty now (the slot '
                    'cell the stood T leaves open over the foot), and nothing above the T is in the window, so the '
                    'variant has no roof. The TSS slots on BT砲\'s page\'s, harddrop\'s and Tetrisチャンネル\'s drawings '
                    'are OUR READING of their terrain: those pages draw only the TSD there.',
     'untested_drawn': {'cells': [], 'reason': ''},
     'agreement': [
         {'board': 'basic.z', 't_cells': _TSS_T, 'mirrored': False},
         {'board': 'basic.o', 't_cells': _TSS_T, 'mirrored': False},
     ],
     'payoff': {'kind': 'well_quad', 'board': 'tss.after', 'piece': 'I', 'lines': 4,
                'well_cell_pre_clear': [4, 2], 'well_cell_after': [4, 2], 'note': _PAYOFF_NOTE},
     'fires_on': ['basic.z', 'basic.o'],
     'misses': ['tsd.spin', 'tsd.after', 'tss.after']},
]

#: harddrop's Parapet page: one fumen, decoded once (see the module docstring), its pages recorded here
HARDDROP = {
    'page': 'https://harddrop.com/wiki/Parapet',
    'title': 'Parapet',
    'oldid': 31260,
    'revision_sha1': '3a0657075072ac9592432879d262e94740fdbdb4',
    'revision_timestamp': '2021-10-14T06:40:48Z',
    'fetched': '2026-10-19',
    'fetch_method': 'the latest revision\'s own bytes from the MediaWiki API (https://harddrop.com/w/api.php?action=query'
                    '&prop=revisions&titles=Parapet&rvprop=ids|sha1|size|timestamp|content&rvslots=main), with Python\'s '
                    'urllib and a descriptive User-Agent (NOT curl); the API\'s sha1 equals the sha1 of the bytes, and '
                    '31260 was the page\'s latest revision when fetched',
    'snapshot_file': 'Parapet.wikitext',
    'snapshot_sha256': '253fea77080fd6edf959e23b3b19a73b20066b2e5204e864ac8619943c48d01a',
    'snapshot_bytes': 1169,
    'snapshot_note': 'not committed: check_wikitext_sources refetches the pinned revision weekly through api.php and '
                     're-checks it with --wikitext-dir; a person re-checks it with --html-dir, the file beside '
                     'parapet.html',
    'author_note': 'harddrop\'s page (「Introduced by Chopin」): another site and another author than shiwehi.com',
    'categories': ['T-Spin techniques', 'T-Spin setups', 'Mid-game T-Spin setups'],
    'quote': 'If the hole is deep enough, then this directly connects to a btb tetris.',
    'fumen': 'm110@jdA3mbC3mbC3mbC3ibH3gbI3gbI3gbI3gbE3pbA4G7?eK0JB/KBK2bKecKocqocqMBNoclNBZcBAAA',
    'decoder': 'tetris-fumen@1.1.3 (knewjade), decoded once into the pages below, as fetch-catalogue.ts vendors '
               'opener fields; pipeline/ has no dependency on it and CI does not re-run the decode (an open item)',
    'reading': {'.': 'empty', 'G': 'grey, filled', 'other': 'a letter its piece, filled'},
    'pages': {
        'pre_t_board': {
            'page': 9, 'note': 'the field page 9 locks its T into (pages 0-7 the terrain, the Z, the S and the L, '
                               'whose pages 3-6 are movement frames), the top row page 0\'s and page 2\'s',
            'rows': ['..G.....S.', 'GGGL..ZZSS', 'GGGL...ZZS', 'GGGLL.GGGG', 'GGGG.GGGGG', 'GGGG.GGGGG',
                     'GGGG.GGGGG', 'GGGG.GGGGG']},
        't_lock': {'page': 9, 'operation': 'T reverse x5 y5, lock', 'cells': [[2, 4], [2, 5], [2, 6], [3, 5]],
                   'cleared_rows': [2, 3]},
        'i_lock': {'page': 10, 'operation': 'I left x4 y1, lock', 'cells': [[4, 4], [5, 4], [6, 4], [7, 4]],
                   'cleared': 4, 'note': 'on the board the T\'s clear leaves (two empty rows on top), the well\'s column'},
    },
    #: the slot each variant's window is checked at on the pre-T board: the TSD's the T page 9 locks; the TSS's OUR READING
    'slots': {'parapet': [[2, 4], [2, 5], [2, 6], [3, 5]], 'parapet_tss': [[1, 5], [2, 5], [2, 6], [3, 5]]},
    'drawn_t_not_fired': [
        {'page': 8, 'operation': 'T right x4 y6, not a lock', 'cells': [[0, 4], [1, 4], [1, 5], [2, 4]],
         'note': 'a movement frame of the same T before it turns into the slot (lock false): no T lands there'},
    ],
}

#: Tetrisチャンネル's Parapet page: its text and its sixteen images, committed under spec/fixtures/tetrisch-parapet/
_TC_IMAGES = [
    ('001', '253c8a2d946a393d77c3c35183e40414038a1b2969e95d5f994ef84682a583ab', 34310,
     '.......... .......... .......... .......... ##........ ##...##### ###.###### ###.######'),
    ('002', '206d8b5b6012cbbcd6a100c8315bc226e651a70a70517f725a2b9071d1775d40', 38492,
     '.......... .......... .......... ..L..ZZ.OO ##L...ZZOO ##LL.##### ###.###### ###.######'),
    ('003', '36ff38ebc9ecb62ac13bda1b546ff1d1d7e293f1d23b8c3b6022879b671e9324', 36513,
     '.......... .......... .......... ..#..##.## ###TTT#### ####T##### ###.###### ###.######'),
    ('004', '8c8f506ef5b6f76d9d6f84543dae271afd08003b963e3a5df06488e0cdb19030', 34048,
     '.......... .......... .......... .......... .......... ..#..##.## ###.###### ###.######'),
    ('005', '4635b6b3a4bb2dbea26bbc7662c202d1984c4e2b8c2c741d4c4945c7f96ca2b0', 37700,
     '.......... .......... ....L..... ....LZZ.OO ##..LLZZOO ##...##### ###.###### ###.######'),
    ('006', 'ea944be17a5f1486111be45bc3719f229a72ceead807c6ca200eedae4802d27c', 36373,
     '.......... .......... ....#..... ....###.## ##..###### ##TTT##### ###T###### ###.######'),
    ('007', '480dba3ffd1a7de3aeb9dc002f18bd30053b10d42d6112ed06ede5f5d093e906', 33992,
     '.......... .......... .......... .......... ....#..... ....###.## ##..###### ###.######'),
    ('008', '493f782b802e296884eb1cde39675de445b64d053331d11902328424b8f14768', 37518, None),
    ('009', '6c902ea94e3c39842c574bd9ceb2803c686b6ea46430d7abc98327a27fccca92', 39059,
     '....L..... ....LZZ.OO ##..LLZZOO ##...##### ###.###### ###.###### ###.###### ###.######'),
    ('010', 'd96c3b5c489c3837fd37b0872027c51f80a41cccacfecc2212f7a3371a6d449f', 36322,
     '....#..... ....###.## ##..###### ##TTT##### ###T###### ###.###### ###.###### ###.######'),
    ('011', '189bc202602608948edb4c6226fb6ccac2749a2a759c93d1381ca3a5ee2d3f6b', 35256,
     '.......... .......... ....#..... ....###.## ##..###### ###.###### ###.###### ###.######'),
    ('012', '2faa74bcf436f45ff42c1a5a74e6d977e5fffa1ecc68ecace800ec4c3bb82db7', 39195,
     '.......... ..L..ZZ.OO ##L...ZZOO ##LL.##### ###.###### ###.###### ###.###### ###.######'),
    ('013', 'b23aa07174bfe21b9a2b89b4051190460e32d1849bb751826a2313c0794457cf', 36595,
     '.......... ..#..##.## ###TTT#### ####T##### ###.###### ###.###### ###.###### ###.######'),
    ('014', 'c47bb57b74bfa53ea210fe6d9fd8333ca24adf8d48c3078b80e5104ab16732b2', 35282,
     '.......... .......... .......... ..#..##.## ###.###### ###.###### ###.###### ###.######'),
    ('015', 'ec8b1aa529e284c64901e29933d62ac6c4381da865acd94e28cea25607a96d53', 36549,
     '.......... .......... .......... ..#..##.## ###I###### ###I###### ###I###### ###I######'),
    ('016', '5df2f74abf31b1588cdf8fd071438096d59386fbcd89302104758c2113f48062', 35267,
     '.......... .......... ##........ ##...##### ###.###### ###.###### ###.###### ###.######'),
]


def _img(n: str, sha: str, size: int, rows: str | None) -> dict:
    e = {'file': f'parapet_{n}.jpg', 'sha256': sha, 'bytes': size}
    if rows is None:
        e['annotation'] = ('the digits 4-3-2-1 painted on white well cells (the depth of the well beside the 4-deep '
                           'terrain 016): the sampler refuses it, a white cell being no piece colour')
    else:
        e['rows'] = rows.split()
    return e


TETRISCH = {
    'page': 'https://tetrisch.github.io/main/technic/parapet.html',
    'title': '欄干 Parapet',
    'fetched': '2026-10-19',
    'fetch_method': 'curl through the session proxy, TLS verification ON (the page and its sixteen images, '
                    '../img/vstec/parapet_0NN.jpg, byte for byte)',
    'snapshot_file': 'tetrisch_parapet.html',
    'snapshot_sha256': '0a30496d92396a73b744dc7e44bc2ad1cb6c0fd8b894abb8d4a92489091c956e',
    'snapshot_bytes': 5956,
    'terms': 'not stated on the page; credited by link',
    'author_note': 'Tetrisチャンネル: another site and another author than shiwehi.com, and the page shiwehi.com cites as '
                   'its reference',
    'quotes': ['欄干はLJミノを用いたTSDアプローチの1つです．', 'ドネイトの一種です．',
               'このとき，TSD地形をそのまま利用すると以下のようになります．',
               'この違いが大きく影響するのは下穴がちょうど4つの時です．', 'そのままTSDを打つとテトリスが打てません．',
               '欄干を行うと4列を保つことができます．'],
    'images_dir': 'spec/fixtures/tetrisch-parapet',
    'reading': {'.': 'empty', '#': 'grey, filled', 'other': 'a letter its piece, filled (the jp-forecast sampler\'s '
                                                           'reading, pipeline.sim.extract_jp_forecast.extract_one)'},
    'images': [_img(*x) for x in _TC_IMAGES],
    #: what each image is, by number: the page draws Parapet on a 2-deep well and on a 4-deep one, and the plain TSD
    #: on both terrains beside it (its own control: the nub plugs the well)
    'sequences': [
        {'kind': 'parapet', 'terrain': '001', 'pre': '002', 'spin': '003', 'after': '004', 'well_depth': 2},
        {'kind': 'plain_tsd', 'terrain': '001', 'pre': '005', 'spin': '006', 'after': '007'},
        {'kind': 'plain_tsd', 'terrain': '016', 'pre': '009', 'spin': '010', 'after': '011'},
        {'kind': 'parapet', 'terrain': '016', 'pre': '012', 'spin': '013', 'after': '014', 'quad': '015',
         'well_depth': 4},
    ],
    #: the slots each variant is checked at on the Parapet pre-boards: the TSD's the spin image's T; the TSS's OUR READING
    'slots': {'002': {'parapet': [[4, 3], [4, 4], [4, 5], [5, 4]], 'parapet_tss': [[3, 4], [4, 4], [4, 5], [5, 4]]},
              '012': {'parapet': [[2, 3], [2, 4], [2, 5], [3, 4]], 'parapet_tss': [[1, 4], [2, 4], [2, 5], [3, 4]]}},
    'drawn_t_not_fired': [
        {'image': '006', 'pre': '005', 'reason': 'the plain TSD: rel (+2,0) is filled, the nub plugs the well'},
        {'image': '010', 'pre': '009', 'reason': 'the plain TSD: rel (+2,0) is filled, the nub plugs the well'},
    ],
}

#: BT砲's page draws a Parapet (its `parapet` board) and a 途中BT on the same terrain (`bt.build`): same author.
#: The BT window's own `misses` already list `parapet`
BT_CANNON = {
    'file': BT_FILE,
    'drawing': 'parapet',
    'slots': {'parapet': [[4, 1], [4, 2], [4, 3], [5, 2]], 'parapet_tss': [[3, 2], [4, 2], [4, 3], [5, 2]]},
    'fires': [{'node': 'bt.build', 'variant': 'parapet', 'cells': [[4, 1], [4, 2], [4, 3], [5, 2]]},
              {'node': 'bt.build', 'variant': 'parapet_tss', 'cells': [[3, 2], [4, 2], [4, 3], [5, 2]]},
              {'node': 'parapet', 'variant': 'parapet', 'cells': [[4, 1], [4, 2], [4, 3], [5, 2]]},
              {'node': 'parapet', 'variant': 'parapet_tss', 'cells': [[3, 2], [4, 2], [4, 3], [5, 2]]}],
    'note': 'both windows fire, as drawn, on BT砲\'s page\'s Parapet (an agreement drawing) and on its 途中BT build '
            '(「実は欄干を組む形からBT砲にすることができます」: the BT is built from the Parapet terrain, so its board holds '
            'the Parapet slot too). A relation, not a clash; and on no other board of that transcription',
}

#: 基本的なドネイト (`basicdonating-technique.json`) draws a %LドネイトA and names it 欄干: both windows fire on it at its T
#: (and the TSS window at the stood T), so this page's corpus hits are that page's named form, which its own count drops
NAMED_BY = {
    'file': 'basicdonating-technique.json',
    'fires': [{'node': 'one.l_a', 'variant': 'parapet', 'cells': [[2, 1], [2, 2], [2, 3], [3, 2]], 'mirrored': False},
              {'node': 'one.l_a', 'variant': 'parapet_tss', 'cells': [[1, 2], [2, 2], [2, 3], [3, 2]],
               'mirrored': False}],
    'note': 'same author (shiwehi.com): the 基本的なドネイト page\'s 1ミノドネイト forms include 「%LドネイトA(=欄干)」, drawn '
            'without its T; on no other board of that transcription',
}

CROSS_SOURCE = {
    'kind': 'routes',
    'label_pattern': 'parapet',
    'note': 'the windows, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot board of '
            'every committed *-routes.json, with the U cells as the T: the TSD window fires on two 山岳積み2号 boards '
            '(same author, unlabelled: `also`), the TSS window on none. The independent drawers are harddrop and '
            'Tetrisチャンネル instead; their drawings are the windows\' external `agreement` drawings: rule (g) fires each '
            'window on each, once, at its slot, as drawn.',
    'routes_fire_none': 'no routes board by another author draws a Parapet (measured: the windows fire only on the two '
                        'same-author 山岳積み2号 boards below, and no node is labelled 欄干 or Parapet); the cross-check is '
                        'harddrop\'s and Tetrisチャンネル\'s pages, read below',
    'harddrop': HARDDROP,
    'tetrisch': TETRISCH,
    'bt_cannon': BT_CANNON,
    'named_by': NAMED_BY,
    'fires': [],
    'also': [
        {'file': 'mountainous2-routes.json', 'node': '2.compromise.fire5.bag4#1', 'variant': 'parapet',
         'mirrored': False, 'note': 'same author (shiwehi.com), unlabelled: a 9-row board the route artefact cannot '
                                    'match, so no cross-route'},
        {'file': 'mountainous2-routes.json', 'node': '2.compromise.fire5.bag4#2', 'variant': 'parapet',
         'mirrored': False, 'note': 'the same, its second drawing'},
    ],
    'labelled_not_fired': [],
}

KNOWN_DISCREPANCIES: list[dict] = []

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'parapet',
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


# ── the external drawings ────────────────────────────────────────────────────────────────────────
def norm(rows: list[str]) -> list[str]:
    """A harddrop or Tetrisチャンネル board in this file's letters: '.' empty, every other code filled (grey `c`, a
    piece its lower-case letter)."""
    return [''.join(EMPTY if ch == '.' else ('c' if ch in 'G#' else ch.lower()) for ch in row) for row in rows]


def _image(data: dict, n: str) -> dict:
    e = [x for x in data['cross_source']['tetrisch']['images'] if x['file'] == f'parapet_{n}.jpg']
    if len(e) != 1:
        raise ValueError(f'tetrisch: {len(e)} images parapet_{n}.jpg recorded')
    return e[0]


def bt_board(data: dict) -> list[str]:
    bc = data['cross_source']['bt_cannon']
    other = json.loads((TECHNIQUE_DIR / bc['file']).read_text())
    return node(other, bc['drawing'])['rows']


def drawings(data: dict) -> list[dict]:
    """Every external drawing, per variant: {'name', 'rows', 't_cells', 'mirrored', 'variant'}."""
    xs = data['cross_source']
    out = []
    for vid in (v['id'] for v in data['variants']):
        out.append({'name': f'BT砲 page\'s Parapet ({xs["bt_cannon"]["file"]} {xs["bt_cannon"]["drawing"]})',
                    'rows': bt_board(data), 't_cells': xs['bt_cannon']['slots'][vid], 'mirrored': False,
                    'variant': vid})
        hd = xs['harddrop']
        out.append({'name': 'harddrop Parapet fumen, the board page 9 locks its T into',
                    'rows': norm(hd['pages']['pre_t_board']['rows']), 't_cells': hd['slots'][vid], 'mirrored': False,
                    'variant': vid})
        tc = xs['tetrisch']
        for n in sorted(tc['slots']):
            out.append({'name': f'Tetrisチャンネル parapet_{n}.jpg', 'rows': norm(_image(data, n)['rows']),
                        't_cells': tc['slots'][n][vid], 'mirrored': False, 'variant': vid})
    return out


def external_drawings() -> list[dict]:
    return drawings(build())


# ── technique-only rules ─────────────────────────────────────────────────────────────────────────
def _var(data: dict, vid: str) -> dict:
    return next(v for v in data['variants'] if v['id'] == vid)


def _fires_anywhere(data: dict, v: dict, rows: list[str]) -> list[tuple]:
    return [([list(x) for x in sorted(cs)], m) for cs in TT.t_placements(rows, SPEC) for m in (False, True)
            if TT.window_fires(data, v, SPEC, rows, cs, m)]


def _hands(data: dict, v: dict, rows: list[str], cells) -> list[bool]:
    return [m for m in (False, True) if TT.window_fires(data, v, SPEC, rows, {tuple(x) for x in cells}, m)]


def _with(rows: list[str], cells, ch: str = 'c') -> list[str]:
    s = {tuple(x) for x in cells}
    return [''.join(ch if (r, c) in s else x for c, x in enumerate(row)) for r, row in enumerate(rows)]


def _full(rows: list[str]) -> list[int]:
    return [r for r, row in enumerate(rows) if EMPTY not in row]


def _clear(rows: list[str]) -> list[str]:
    full = _full(rows)
    kept = [row for r, row in enumerate(rows) if r not in full]
    return [EMPTY * WIDTH] * len(full) + kept


def _occ(rows: list[str]) -> list[str]:
    return [''.join(EMPTY if ch in '.-' else '#' for ch in row) for row in rows]


def _depth(rows: list[str], r: int, c: int) -> int:
    n = 0
    while r < len(rows) and rows[r][c] == EMPTY:
        n += 1
        r += 1
    return n


def _well_on(data: dict, v: dict, slot) -> tuple[int, int]:
    """The variant's pre-clear well cell, mapped to a drawing whose spin goes into `slot` (as drawn)."""
    f = TT.frame_map(data, v, SPEC, {tuple(x) for x in slot}, False)
    return f(*v['payoff']['well_cell_pre_clear'])


def _check_tetrisch(data: dict) -> list[str]:
    bad = []
    tc = data['cross_source'].get('tetrisch')
    if not tc:
        return ['tetrisch: no Tetrisチャンネル record (the page this page cites is required, never defaulted)']
    names = sorted(x['file'] for x in tc['images'])
    if names != [f'parapet_{i:03d}.jpg' for i in range(1, 17)]:
        bad.append(f'tetrisch: the images recorded are {names}, not parapet_001..016')
    for e in tc['images']:
        if ('rows' in e) == ('annotation' in e):
            bad.append(f'tetrisch: {e["file"]} is neither a board nor an annotation (or both)')
        elif 'rows' in e and (len(e['rows']) != 8 or any(len(r) != WIDTH for r in e['rows'])):
            bad.append(f'tetrisch: {e["file"]} is not an 8-row, ten-wide board')
        p = IMG_DIR / e['file']
        if not p.exists():
            bad.append(f'tetrisch: {e["file"]} is not committed under {IMG_DIR.relative_to(REPO)}')
            continue
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != e['sha256'] or len(raw) != e['bytes']:
            bad.append(f'tetrisch: the committed {e["file"]} is not the recorded bytes')
    try:
        img = {x['file'][8:11]: x for x in tc['images']}
        used = set()
        for s in tc['sequences']:
            for k in ('terrain', 'pre', 'spin', 'after', 'quad'):
                if k in s:
                    used.add(s[k])
            pre, spin, after = (img[s[k]]['rows'] for k in ('pre', 'spin', 'after'))
            t = [[r, c] for r, row in enumerate(spin) for c, ch in enumerate(row) if ch == 'T']
            if len(t) != 4 or _occ(_with(pre, t, 'T')) != _occ(spin):
                bad.append(f'tetrisch: parapet_{s["spin"]} is not parapet_{s["pre"]} with its T in, by occupancy')
            if _clear(_occ(spin)) != _occ(after):
                bad.append(f'tetrisch: parapet_{s["after"]} is not what parapet_{s["spin"]}\'s spin leaves')
            terr = norm(img[s['terrain']]['rows'])
            if any(terr[r][c] != EMPTY and norm(pre)[r][c] == EMPTY for r in range(8) for c in range(WIDTH)):
                bad.append(f'tetrisch: parapet_{s["pre"]} is not built on parapet_{s["terrain"]}')
            for v in data['variants']:
                if s['kind'] == 'parapet':
                    slot = tc['slots'][s['pre']][v['id']]
                    hits = _fires_anywhere(data, v, norm(pre))
                    if hits != [(sorted(slot), False)]:
                        bad.append(f'tetrisch: {v["id"]} fires {hits} on parapet_{s["pre"]}, not once at its slot')
                    if v['id'] == 'parapet' and sorted(t) != sorted(slot):
                        bad.append(f'tetrisch: the TSD slot on parapet_{s["pre"]} is not parapet_{s["spin"]}\'s T')
                    # the well depth, read off the drawing at the variant's own well cell (both variants: one well)
                    r, c = _well_on(data, v, slot)
                    if _depth(norm(pre), r, c) != s['well_depth']:
                        bad.append(f'tetrisch: the {v["id"]} well on parapet_{s["pre"]} is {_depth(norm(pre), r, c)} '
                                   f'deep, not {s["well_depth"]}')
                else:
                    if _fires_anywhere(data, v, norm(pre)) or _hands(data, v, norm(pre), t):
                        bad.append(f'tetrisch: {v["id"]} fires on the plain TSD parapet_{s["pre"]}')
                for k in ('terrain',):
                    if _fires_anywhere(data, v, norm(img[s[k]]['rows'])):
                        bad.append(f'tetrisch: {v["id"]} fires on the bare terrain parapet_{s[k]}')
            if 'quad' in s:
                quad = img[s['quad']]['rows']
                icells = [(r, c) for r, row in enumerate(quad) for c, ch in enumerate(row) if ch == 'I']
                less = [''.join('.' if ch == 'I' else ch for ch in row) for row in quad]
                if less != after or len(icells) != 4 or len(_full(norm(quad))) != 4:
                    bad.append(f'tetrisch: parapet_{s["quad"]} is not parapet_{s["after"]} with an I clearing 4')
                wr, wc = _well_on(data, _var(data, 'parapet'), tc['slots'][s['pre']]['parapet'])
                if any(c != wc for _r, c in icells):
                    bad.append(f'tetrisch: the I of parapet_{s["quad"]} is not in the well column')
        annotated = sorted(x['file'][8:11] for x in tc['images'] if 'annotation' in x)
        if sorted(list(used) + annotated) != sorted(img) or annotated != ['008']:
            bad.append(f'tetrisch: the sequences and annotations do not account for every image once '
                       f'({sorted(used)} + {annotated})')
        for e in tc['drawn_t_not_fired']:
            spin = img[e['image']]['rows']
            t = [[r, c] for r, row in enumerate(spin) for c, ch in enumerate(row) if ch == 'T']
            if any(_hands(data, v, norm(img[e['pre']]['rows']), t) for v in data['variants']) or not e.get('reason'):
                bad.append(f'tetrisch: parapet_{e["image"]}\'s T fires, or carries no reason')
        named = sorted(e['image'] for e in tc['drawn_t_not_fired'])
        plain = sorted(s['spin'] for s in tc['sequences'] if s['kind'] == 'plain_tsd')
        if named != plain:
            bad.append(f'tetrisch: drawn_t_not_fired names {named}, the plain TSD spins are {plain}')
    except (KeyError, ValueError) as e:
        bad.append(f'tetrisch: {e!r}')
    return bad


def _check_harddrop(data: dict) -> list[str]:
    hd = data['cross_source'].get('harddrop')
    if not hd:
        return ['hd: no harddrop record (the Parapet page is required, never defaulted)']
    bad = []
    pages = hd['pages']
    pre = norm(pages['pre_t_board']['rows'])
    t = pages['t_lock']['cells']
    if any(pre[r][c] != EMPTY for r, c in t):
        bad.append('hd: the T lock is not on empty cells of the pre-T board')
    with_t = _with(pre, t)
    if _full(with_t) != pages['t_lock']['cleared_rows']:
        bad.append(f'hd: the T lock makes rows {_full(with_t)} full, not the recorded {pages["t_lock"]["cleared_rows"]}')
    cleared = _clear(with_t)
    icells = pages['i_lock']['cells']
    if any(cleared[r][c] != EMPTY for r, c in icells) or len({c for _r, c in icells}) != 1:
        bad.append('hd: the I lock is not a vertical I on empty cells of the cleared board')
    elif len(_full(_with(cleared, icells))) != pages['i_lock']['cleared']:
        bad.append(f'hd: the I lock makes {len(_full(_with(cleared, icells)))} rows full, not {pages["i_lock"]["cleared"]}')
    tsd = _var(data, 'parapet')
    if sorted(hd['slots']['parapet']) != sorted(t):
        bad.append('hd: the TSD slot is not the T page 9 locks')
    for v in data['variants']:
        if _fires_anywhere(data, v, pre) != [(sorted(hd['slots'][v['id']]), False)]:
            bad.append(f'hd: {v["id"]} does not fire once, as drawn, at its slot on the pre-T board')
        for e in hd['drawn_t_not_fired']:
            if _hands(data, v, pre, e['cells']) or not e.get('note'):
                bad.append(f'hd: {v["id"]} fires at page {e["page"]}\'s T, or it carries no note')
    wr, wc = _well_on(data, tsd, t)
    if any(c != wc for _r, c in icells):
        bad.append('hd: the I is not in the well column under the T\'s left arm')
    if hd['fumen'] not in ('',) and not hd['fumen'].startswith('m110@'):
        bad.append('hd: the fumen is not a v110 fumen')
    return bad


def extra_checks(data: dict):
    bad, measured = [], set()
    by = {n['id']: n for n in data['nodes']}
    xs = data['cross_source']
    # listed: every drawn board is in each variant's fires_on, misses or is its own board; the agreement boards are
    # exactly fires_on
    for v in data['variants']:
        listed = set(v.get('fires_on', [])) | set(v.get('misses', [])) | {v['board']}
        for n in data['nodes']:
            if not n.get('derived') and n['id'] not in listed:
                bad.append(f'listed: drawn board {n["id"]} is in none of {v["id"]}\'s fires_on, misses')
        if sorted(a['board'] for a in v.get('agreement', [])) != sorted(v.get('fires_on', [])):
            bad.append(f'listed: {v["id"]}\'s agreement drawings are not its fires_on')
        if any(a['mirrored'] for a in v.get('agreement', [])):
            bad.append(f'listed: {v["id"]} reads a page drawing mirrored (the page draws none)')
    if [v['id'] for v in data['variants']] != ['parapet', 'parapet_tss'] or \
            [(v['spin'], v['lines']) for v in data['variants']] != [('TSD', 2), ('TSS', 1)]:
        bad.append('listed: the variants are not the TSD and the TSS')
    if any(v['window'] != data['variants'][0]['window'] for v in data['variants']):
        bad.append('listed: the two variants do not share one window')
    # tetrisch and hd: the two other sites, measured
    bad += _check_tetrisch(data)
    bad += _check_harddrop(data)
    # bt and cross: every board of every other committed technique transcription, each variant, every resting T
    bc = xs.get('bt_cannon')
    got_bt = []
    # a page that NAMES its form as this technique (基本的なドネイト's %LドネイトA(=欄干)): where the windows fire on it,
    # recorded and re-measured (an opt-in record; a fire on any other technique board is still a failure)
    nb = xs.get('named_by')
    got_nb = []
    for f in sorted(TECHNIQUE_DIR.glob('*-technique.json')):
        if f.name == OUT.name:
            continue
        other = json.loads(f.read_text())
        ospec = TT.TechniqueSpec(out=f, build=lambda: other, alphabet=frozenset(),
                                 empty_letters=other.get('empty_letters', ''), max_rows=99)
        for n in other['nodes']:
            sc = TT.spin_cells(n) if n['kind'] == 'spin' else set()
            pre = [''.join(EMPTY if (r, c) in sc or ch == 'U' else ch for c, ch in enumerate(row))
                   for r, row in enumerate(n['rows'])]
            for v in data['variants']:
                for cs in TT.t_placements(pre, ospec):
                    for m in (False, True):
                        if TT.window_fires(data, v, ospec, pre, cs, m):
                            if bc and f.name == bc['file'] and not m:
                                got_bt.append({'node': n['id'], 'variant': v['id'], 'cells': sorted([r, c] for r, c in cs)})
                            elif nb and f.name == nb['file']:
                                got_nb.append({'node': n['id'], 'variant': v['id'],
                                               'cells': sorted([r, c] for r, c in cs), 'mirrored': m})
                            else:
                                bad.append(f'cross: {v["id"]} fires on {f.name} {n["id"]}'
                                           f'{" (mirrored)" if m else ""} (record it, or measure why not)')
    if not bc:
        bad.append('bt: no bt_cannon record')
    else:
        key = lambda e: (e['node'], e['variant'], e['cells'])
        if sorted(got_bt, key=key) != sorted(bc['fires'], key=key):
            bad.append(f'bt: the windows fire on {bc["file"]} at {sorted(map(key, got_bt))}, the record holds '
                       f'{sorted(map(key, bc["fires"]))}')
        try:
            btv = json.loads((TECHNIQUE_DIR / bc['file']).read_text())['variants'][0]
            if bc['drawing'] not in btv.get('misses', []):
                bad.append(f'bt: {bc["file"]}\'s own window does not list {bc["drawing"]} as a miss')
        except (OSError, KeyError, IndexError) as e:
            bad.append(f'bt: {e!r}')
    if nb:
        key = lambda e: (e['node'], e['variant'], e['cells'], e['mirrored'])
        if sorted(got_nb, key=key) != sorted(nb['fires'], key=key):
            bad.append(f'cross: the windows fire on {nb["file"]} at {sorted(map(key, got_nb))}, named_by holds '
                       f'{sorted(map(key, nb["fires"]))}')
    # cross: no routes node is labelled as this technique by its Japanese name either
    for f in sorted(HERE.glob('*-routes.json')):
        for n in json.loads(f.read_text())['nodes']:
            text = ' '.join(str(n.get(k, '')) for k in ('id', 'label', 'label_jp')).lower()
            if '欄干' in text:
                bad.append(f'cross: {f.name} {n["id"]} is labelled as this technique')
    # the after boards (the shared after rule measures them; restated for the payoff's board here)
    for v in data['variants']:
        if by.get(v['payoff']['board'], {}).get('after_of') != v['board']:
            bad.append(f'listed: {v["id"]}\'s payoff board is not its spin board\'s after board')
    return bad, measured


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='',
    upper_groups={'T': 'merge'},
    extra_checks=extra_checks,
    external_drawings=external_drawings,
)


# ── --html-dir: the pinned harddrop revision and the Tetrisチャンネル page beside the shiwehi snapshot ───────────
def harddrop_snapshot_checks(data: dict, html_dir: Path) -> list[str]:
    """The pinned harddrop revision alone (hashes, its one fumen, the quote): what a weekly api.php refetch can re-check."""
    bad = []
    hd = data['cross_source']['harddrop']
    p = Path(html_dir) / hd['snapshot_file']
    if not p.exists():
        bad.append(f'hd: {hd["snapshot_file"]} is not in {html_dir} — fetch it beside the page')
    else:
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != hd['snapshot_sha256'] or len(raw) != hd['snapshot_bytes']:
            bad.append(f'hd: hash: sha256/bytes {hashlib.sha256(raw).hexdigest()} / {len(raw)} are not the recorded ones')
        if hashlib.sha1(raw).hexdigest() != hd['revision_sha1']:
            bad.append(f'hd: hash: sha1 {hashlib.sha1(raw).hexdigest()} is not MediaWiki\'s revision sha1')
        text = raw.decode('utf8')
        if hd['fumen'] not in text or text.count('<fumen>') != 1:
            bad.append('hd: the page does not hold the recorded fumen verbatim, as its one fumen')
        if hd['quote'] not in text:
            bad.append('hd: the recorded quote is not on the page')
        if '{{pfrow' in text:
            bad.append('hd: the page holds pfrow tables now — transcribe them')
    return bad


def tetrisch_snapshot_checks(data: dict, html_dir: Path) -> list[str]:
    """The Tetrisチャンネル page and its images beside the shiwehi snapshot (a person's --html-dir only)."""
    bad = []
    tc = data['cross_source']['tetrisch']
    p = Path(html_dir) / tc['snapshot_file']
    if not p.exists():
        bad.append(f'tetrisch: {tc["snapshot_file"]} is not in {html_dir} — fetch it beside the page')
    else:
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != tc['snapshot_sha256'] or len(raw) != tc['snapshot_bytes']:
            bad.append('tetrisch: hash: the page is not the recorded bytes')
        import html as _html
        import re
        flat = _html.unescape(re.sub(r'<[^>]+>', '', raw.decode('utf8')))
        flat = re.sub(r'\s+', '', flat)
        for q in tc['quotes']:
            if q not in flat:
                bad.append(f'tetrisch: quote {q!r} is not on the page')
        imgs = re.findall(r'img/vstec/(parapet_\d+\.jpg)', raw.decode('utf8'))
        if sorted(imgs) != sorted(x['file'] for x in tc['images']):
            bad.append(f'tetrisch: the page shows {sorted(imgs)}, the record holds {len(tc["images"])} images')
    d = Path(html_dir) / Path(tc['images_dir']).name
    from pipeline.sim.extract_jp_forecast import extract_one
    try:
        import PIL  # noqa: F401  (extract_one imports it lazily; a missing Pillow is one named failure, not sixteen)
        pillow = True
    except ImportError:
        pillow = False
        bad.append('tetrisch: pillow: Pillow is not installed, so the images are checked by hash only and not re-read '
                   '(pip install Pillow)')
    for e in tc['images']:
        p = d / e['file']
        if not p.exists():
            bad.append(f'tetrisch: {e["file"]} is not in {d}')
            continue
        if hashlib.sha256(p.read_bytes()).hexdigest() != e['sha256']:
            bad.append(f'tetrisch: hash: {e["file"]} is not the recorded bytes')
        if not pillow:
            continue
        try:
            got = extract_one(str(p))
        except ValueError:
            got = None
        if got != e.get('rows'):
            bad.append(f'tetrisch: {e["file"]} re-reads as {got}, the record holds {e.get("rows")}')
    return bad


def snapshot_checks(data: dict, html_dir: Path) -> list[str]:
    return harddrop_snapshot_checks(data, html_dir) + tetrisch_snapshot_checks(data, html_dir)


def _synthetic_harddrop(data: dict) -> str:
    """A faithful stand-in for the harddrop page CI cannot fetch: its quote and its one fumen, no pfrow table."""
    hd = data['cross_source']['harddrop']
    return f"'''Parapet''' {hd['quote']}\n<fumen>code={hd['fumen']}</fumen>\n"


SPEC.html_checks = snapshot_checks
# the harddrop half reads nothing but the pinned wikitext, so a weekly api.php refetch can run it
SPEC.wikitext_checks = harddrop_snapshot_checks
SPEC.synthetic_wikitext = lambda d: {d['cross_source']['harddrop']['snapshot_file']: _synthetic_harddrop(d)}


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def _set(rows, r, c, ch):
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _v(d, i=0):
    return d['variants'][i]


def _tc_img(d, n):
    return _image(d, n)


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'basic.z.terrain')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: d['page_order'].reverse(), 'page_order swapped', 'grammar:'),
    (lambda d: node(d, 'tsd.spin').__setitem__('spin_of', 'nowhere'), 'a dangling reference', 'grammar:'),
    (lambda d: _v(d).__setitem__('followup', {'board': 'tsd.after'}), 'a variant with a follow-up and a payoff',
     'grammar:'),
    (lambda d: _v(d, 1).pop('payoff'), 'a variant with neither a follow-up nor a payoff', 'grammar:'),
    (lambda d: _set(node(d, 'basic.o')['rows'], 4, 0, '-'), 'a build board cell flipped', 'build:'),
    (lambda d: _set(node(d, 'basic.z.terrain')['rows'], 5, 9, '-'), 'a derived terrain edited', 'build:'),
    (lambda d: (_set(node(d, 'tsd.spin')['rows'], 3, 3, 'C'), _set(node(d, 'tsd.spin')['rows'], 1, 3, 'T')),
     'the T pointing up', 'spin:'),
    (lambda d: _set(node(d, 'tsd.spin')['rows'], 2, 0, 'c'), 'a cleared row drawn unmuted', 'spin:'),
    (lambda d: node(d, 'tsd.spin').__setitem__('lines', 3), 'the TSD\'s line count', 'spin:'),
    (lambda d: node(d, 'tss.spin').__setitem__('lines', 2), 'the TSS\'s line count', 'spin:'),
    (lambda d: _set(node(d, 'tsd.after')['rows'], 0, 9, 'c'), 'the after board not what the TSD leaves',
     'discrepancy:'),
    (lambda d: _v(d)['window'].__setitem__('cols', [1, 6]), 'the window widened by a column', 'window:'),
    (lambda d: _v(d, 1).__setitem__('window', {'rows': [2, 5], 'cols': [1, 5]}),
     'the TSS window without its top row', 'window:'),
    (lambda d: _v(d)['roof_cells'].pop(), 'a roof cell unnamed', 'window:'),
    (lambda d: _v(d)['agreement'][1].__setitem__('mirrored', True), 'an O-roof basic form read mirrored', 'window:'),
    (lambda d: _v(d, 1)['agreement'][0].__setitem__('t_cells', _TSD_T), 'the TSS read at the TSD\'s slot', 'window:'),
    (lambda d: _v(d)['payoff'].__setitem__('well_cell_pre_clear', [4, 3]), 'the well read under the nub', 'window:'),
    (lambda d: _v(d)['payoff'].__setitem__('well_cell_after', [3, 2]), 'the well cell mapped wrongly', 'window:'),
    (lambda d: _v(d)['payoff'].__setitem__('lines', 3), 'the payoff read as a triple', 'window:'),
    (lambda d: _v(d, 1)['payoff'].__setitem__('board', 'tsd.after'), 'the TSS payoff on the TSD\'s after board',
     'window:'),
    (lambda d: _set(node(d, 'tsd.after')['rows'], 4, 2, 'c'), 'the well column not open on the after board',
     'window:'),
    (lambda d: _v(d)['misses'].append('basic.z'), 'a board it fires on listed as a miss', 'window:'),
    (lambda d: _v(d, 1)['fires_on'].append('tsd.after'), 'an after board listed as firing', 'window:'),
    (lambda d: _v(d)['misses'].remove('tss.after'), 'a drawn board in no list', 'listed:'),
    (lambda d: d['cross_source']['harddrop']['pages']['t_lock'].__setitem__('cleared_rows', [2]),
     'harddrop\'s T clearing one row', 'hd:'),
    (lambda d: d['cross_source']['harddrop']['pages']['i_lock'].__setitem__('cleared', 3),
     'harddrop\'s I clearing three', 'hd:'),
    (lambda d: d['cross_source']['harddrop']['slots'].__setitem__('parapet', [[2, 3], [2, 4], [2, 5], [3, 4]]),
     'harddrop\'s TSD slot moved a column', 'hd:'),
    (lambda d: d['cross_source']['harddrop']['drawn_t_not_fired'][0].__setitem__('note', ''),
     'harddrop\'s movement frame with no note', 'hd:'),
    (lambda d: d['cross_source'].pop('harddrop'), 'no harddrop record', 'hd:'),
    (lambda d: _set(_tc_img(d, '002')['rows'], 7, 3, '#'), 'Tetrisチャンネル\'s 2-deep well filled at the floor',
     'tetrisch:'),
    (lambda d: d['cross_source']['tetrisch']['sequences'][3].__setitem__('well_depth', 3), 'the 4-deep well read as 3',
     'tetrisch:'),
    (lambda d: d['cross_source']['tetrisch']['sequences'][1].__setitem__('kind', 'parapet'),
     'the plain TSD read as a Parapet', 'tetrisch:'),
    (lambda d: d['cross_source']['tetrisch']['images'].pop(7), 'the annotation image dropped', 'tetrisch:'),
    (lambda d: _tc_img(d, '015').__setitem__('sha256', '0' * 64), 'a committed image\'s hash', 'tetrisch:'),
    (lambda d: _set(_tc_img(d, '015')['rows'], 7, 3, '#'), 'the quad read with no I at the floor', 'tetrisch:'),
    (lambda d: d['cross_source']['tetrisch']['drawn_t_not_fired'].pop(), 'a plain TSD spin left unnamed',
     'tetrisch:'),
    (lambda d: d['cross_source']['tetrisch'].pop('slots'), 'the Tetrisチャンネル slots dropped', 'tetrisch:'),
    (lambda d: d['cross_source']['bt_cannon']['fires'].pop(), 'a BT砲 board the windows fire on unrecorded', 'bt:'),
    (lambda d: d['cross_source'].pop('bt_cannon'), 'no BT砲 record', 'bt:'),
    (lambda d: d['cross_source']['named_by']['fires'].pop(), 'the 基本的なドネイト 欄干 form unrecorded', 'cross:'),
    (lambda d: d['cross_source']['also'].pop(), 'a same-author routes board unrecorded', 'cross:'),
    (lambda d: d['cross_source'].pop('routes_fire_none'), 'no reason for the empty fires', 'cross:'),
    (lambda d: node(d, 'basic.o').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['known_discrepancies'].append({'id': 'basic.z:colour', 'note': 'x'}), 'a stale discrepancy',
     'discrepancy:'),
    (lambda d: _set(node(d, 'basic.z')['rows'], 1, 4, 'o'), 'a piece broken', 'discrepancy:'),
]


def _no_external(spec):
    s = copy.copy(spec)
    s.external_drawings = None
    return s


def _tss_external_only_tsd(spec):
    """The external drawings for the TSD alone: the TSS window then has no drawing from another site."""
    s = copy.copy(spec)
    s.external_drawings = lambda: [d for d in external_drawings() if d['variant'] == 'parapet']
    return s


def _plain_tsd_as_drawing(spec):
    s = copy.copy(spec)
    b = build()
    img = _image(b, '005')
    spin = _image(b, '006')['rows']
    t = [[r, c] for r, row in enumerate(spin) for c, ch in enumerate(row) if ch == 'T']
    s.external_drawings = lambda: external_drawings() + [{'name': 'the plain TSD as a drawing', 'rows': norm(img['rows']),
                                                          't_cells': t, 'mirrored': False, 'variant': 'parapet'}]
    return s


SPEC_MUTANTS = [
    (_no_external, 'no external drawing (the window checked against this page alone)', 'window:'),
    (_tss_external_only_tsd, 'the TSS window with no external drawing of its own', 'window:'),
    (_plain_tsd_as_drawing, 'Tetrisチャンネル\'s plain TSD read as a drawing of the shape', 'window:'),
]


def _cross_plant_problems(planted: bool) -> list[str]:
    """The `cross:` rule run with TECHNIQUE_DIR pointed at a temporary directory holding the BT砲 and 基本的なドネイト
    transcriptions and one other: planted, a node that is this page's own TSD board (the window must fire on it); not
    planted, the same file with that board emptied (a control: the rule must stay quiet)."""
    global TECHNIQUE_DIR
    base = build()
    spin = copy.deepcopy(node(base, 'tsd.spin'))
    if not planted:
        spin['rows'] = [EMPTY * len(r) for r in spin['rows']]
    fake = {'nodes': [spin], 'empty_letters': ''}
    saved = TECHNIQUE_DIR
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / 'planted-technique.json').write_text(json.dumps(fake))
        (Path(td) / BT_FILE).write_text((saved / BT_FILE).read_text())
        (Path(td) / NAMED_BY['file']).write_text((saved / NAMED_BY['file']).read_text())
        TECHNIQUE_DIR = Path(td)
        try:
            bad, _measured = extra_checks(base)
        finally:
            TECHNIQUE_DIR = saved
    return [x for x in bad if x.startswith('cross:')]


def _synthetic_tetrisch(data: dict) -> str:
    tc = data['cross_source']['tetrisch']
    body = '<br>'.join(tc['quotes']) + '\n' + '\n'.join(
        f'<img src="../img/vstec/{e["file"]}" width="176" height="140" alt="parapet">' for e in tc['images'])
    return f'<html><body>{body}</body></html>'


def selftest() -> int:
    rc = TT.run_selftest(SPEC, MUTANTS, {'board': ('CCTTTCCCCC', 'CCTTTCCCCc'),
                                         'text': ('TSDではなくTSSを打つ理由', 'TSDではなくTSSを打つ理屈')},
                         SPEC_MUTANTS)
    ok = rc == 0
    base = build()
    for planted, label in ((True, 'this page\'s own TSD board planted in another technique transcription'),
                           (False, 'control: the same file with that board emptied')):
        got = _cross_plant_problems(planted)
        if bool(got) != planted:
            print(f'selftest FAILED: {label}: cross: reported {got[:2]}')
            ok = False
        else:
            print(f'  {"killed" if planted else "control quiet"}: {label}  [cross:]')
    # --html-dir: a synthetic harddrop page and Tetrisチャンネル page, clean and corrupted
    hd = base['cross_source']['harddrop']
    tc = base['cross_source']['tetrisch']
    wiki = _synthetic_harddrop(base)
    plants = {
        'harddrop\'s fumen edited': ('hd', wiki.replace(hd['fumen'][-6:], 'AAAAAA')),
        'harddrop\'s page gains a pfrow table': ('hd', wiki + '{{pfstart}} {{pfrow|G}} {{pfend}}'),
        'a Tetrisチャンネル sentence edited': ('tc', _synthetic_tetrisch(base).replace('4列を保つ', '4列を守る')),
        'a Tetrisチャンネル image left unrecorded': ('tc', _synthetic_tetrisch(base) + '<img src="../img/vstec/parapet_017.jpg">'),
    }
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        missing = snapshot_checks(base, p)
        if not any('is not in' in x for x in missing):
            print(f'selftest FAILED: a missing snapshot was not caught ({missing[:2]})')
            ok = False
        else:
            print('  killed: the harddrop / Tetrisチャンネル snapshots missing  [hd:, tetrisch:]')
        (p / Path(tc['images_dir']).name).mkdir()
        for e in tc['images']:
            (p / Path(tc['images_dir']).name / e['file']).write_bytes((IMG_DIR / e['file']).read_bytes())
        (p / hd['snapshot_file']).write_text(wiki)
        (p / tc['snapshot_file']).write_text(_synthetic_tetrisch(base))
        clean = [x for x in snapshot_checks(base, p) if 'hash:' not in x and 'pillow:' not in x]
        if clean:
            print(f'selftest FAILED: the synthetic snapshots do not verify ({clean[:2]})')
            ok = False
        for label, (which, text) in plants.items():
            (p / hd['snapshot_file']).write_text(wiki if which != 'hd' else text)
            (p / tc['snapshot_file']).write_text(_synthetic_tetrisch(base) if which != 'tc' else text)
            got = [x for x in snapshot_checks(base, p) if 'hash:' not in x and 'pillow:' not in x]
            if not got:
                print(f'selftest FAILED: {label} was not caught')
                ok = False
            else:
                print(f'  killed: {label}  [{got[0].split(":")[0]}:]')
        (p / hd['snapshot_file']).write_text(wiki)
        (p / tc['snapshot_file']).write_text(_synthetic_tetrisch(base))
        img = p / Path(tc['images_dir']).name / 'parapet_015.jpg'
        img.write_bytes((IMG_DIR / 'parapet_014.jpg').read_bytes())
        got = snapshot_checks(base, p)
        if not any('parapet_015.jpg' in x for x in got):
            print(f'selftest FAILED: an image swapped was not caught ({got[:2]})')
            ok = False
        else:
            print('  killed: a Tetrisチャンネル image swapped for another  [tetrisch:]')
    print('selftest: cross and snapshot checks all caught' if ok else 'selftest: FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))

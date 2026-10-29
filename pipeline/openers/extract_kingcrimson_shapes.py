"""Transcribe harddrop's King Crimson page into `kingcrimson-technique.json`.

    python3 -m pipeline.openers.extract_kingcrimson_shapes                  # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_kingcrimson_shapes --selftest       # prove the verifier has teeth
    python3 -m pipeline.openers.extract_kingcrimson_shapes --html-dir <dir> # re-check the three pinned revisions
    python3 -m pipeline.openers.extract_kingcrimson_shapes --wikitext-dir <dir>  # the same, as the weekly job runs it
    python3 -m pipeline.openers.extract_kingcrimson_shapes --html-dir <dir> --write  # ...and rewrite

The first MID-GAME TECHNIQUE page whose primary source is NOT shiwehi.com. harddrop's King_Crimson page: 「a
T-Spin Triple layered on top of a Super T-Spin Double which can be performed when the playfield has a single block
in the bottom left or bottom right corner」. One column well under an overhang; a stood-T TST slot directly above
an STSD slot. shiwehi.com draws no King Crimson (measured 2026-10-29: its template index lists none, and
`template/kingcrimson.php` answers 404), so harddrop's page is the primary source and its pinned revision is the
snapshot every board is checked against.

DECISION: the spin is a TST (a full T-spin, 3 lines) and the anchor is the T's four cells — the T STOOD UP, nub
toward the open side (right as drawn, left mirrored), the T of STSD's stood slot one storey higher. The follow-up
is the STSD under it, which the engine credits as a full T-spin Double (2 lines): the stood T going into the lower
slot (`followup.lines` 2). The cleared rows are all ABOVE the lower slot, so the follow-up slot is not split by the
TST's clear (no row map is needed to join it; the matcher carries it all the same).

WHY THE WINDOW IS THE AGREEMENT BOX (`window_basis: agreement`). The page draws the shape four times on four stacks
(the basic setup, the two TKI 3 continuations, the empty-field setup) and the stacks left of the well differ, so a
bounding box of T, roof and follow-up would read cells the drawings disagree on. The window is the box every drawing
agrees on: this page's four, and two drawings on two OTHER harddrop pages, selected by those pages' own King Crimson
label (never by the window): T-Spin Triple Setups (the table after its 「[[King Crimson]] is a technique」 paragraph,
its TST drawn) and Super T-Spin Double (the board under its 「Combination Setups」 King Crimson bullet). It comes out
eight rows by four columns: the well's wall column, the well, the STSD's nub column and the far wall column, from the
overhang down to the STSD's bottom cell. Widening it meets a disagreement (column 5 of the overhang's row is filled on
Super T-Spin Double and empty on the basic setup) or leaves the basic setup's board (row 0 is its top, row 7 its floor,
column 9 the wall).

WHERE THE TRANSCRIPTION COMES FROM. Every board is read off the pinned revision's own bytes (MediaWiki API, urllib,
a descriptive User-Agent, never curl) by `route_transcription.wikitext_cell` with `source.wikitext_readings`, and
`--html-dir` / `--wikitext-dir` re-read all three pinned revisions. The snapshots are not committed (as SDPC Spin's,
BT砲's and every other harddrop page's): `check_wikitext_sources` refetches them weekly.

WHAT IS AN INFERENCE, flagged in the JSON (`legend`, `reading`) rather than in prose only:

  * harddrop never mutes a cleared row, so every spin board is a named `:muting` discrepancy (the spec's opt-in
    `muting_slips`): the rows a spin clears are drawn in the same letters as the rest.
  * `p` (lower case) on the basic setup's second board is the T it places (read `U`, like `P`); `s` (lower case) is
    one cell of the S drawn lighter (read as the S: the four cells are one S); `Q` is the page's light grey, the
    rest of the stack (read `q`, filled, no piece).
  * the Super T-Spin Double drawing draws no T: its slot (`t_cells`) is OUR READING, the stood T under its overhang
    exactly where the T-Spin Triple Setups drawing draws it, mirrored.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import tempfile
from pathlib import Path

from pipeline.openers import route_transcription as RT
from pipeline.openers import technique_transcription as TT
from pipeline.openers.extract_btcannon_shapes import _sections, _tabled, hd_cell
from pipeline.openers.route_transcription import EMPTY, WIDTH
from pipeline.openers.technique_transcription import node

HERE = Path(__file__).resolve().parent
OUT = HERE / 'kingcrimson-technique.json'

ALPHABET = frozenset('-cqUijlozs')
MAX_ROWS = 9


def _b(text: str) -> list[str]:
    """A board literal: one row per string, top to bottom, as the page draws it."""
    return text.split()


SOURCE = {
    'url': 'https://harddrop.com/wiki/King_Crimson',
    'edit_url': 'https://harddrop.com/w/index.php?title=King_Crimson&action=edit',
    'title': 'King Crimson',
    'site': 'harddrop.com (Hard Drop Tetris Wiki, MediaWiki)',
    'author_note': 'the page is harddrop\'s, edited by its wiki editors; it names no inventor',
    'categories': ['T-Spin techniques', 'T-Spin setups', 'Back-to-Back T-Spin setups', 'Mid-game T-Spin setups'],
    'oldid': 40474,
    'revision_sha1': '36620f5cbf949bedf07cbb23a32ba1cb4b0a3e81',
    'revision_timestamp': '2024-09-20T23:05:19Z',
    'updated': '2024-09-20',
    'revision_note': 'MediaWiki\'s own sha1 of revision 40474 (read 2026-10-29 from the API), equal to sha1 of the saved '
                     'bytes: a second authority beside snapshot_sha256, which is ours; 40474 was the page\'s latest '
                     'revision when fetched',
    'fetched': '2026-10-29',
    'fetch_method': 'the pinned revision\'s own bytes from the MediaWiki API (api.php?action=query&prop=revisions&'
                    'titles=King_Crimson&rvprop=ids|sha1|content|timestamp&rvslots=main&format=json&formatversion=2), '
                    'with Python\'s urllib and a descriptive User-Agent (NOT curl). Boards are {{pfstart}} … {{pfend}} '
                    'templates, 22 of them in 5 {| |} tables, read by route_transcription.wikitext_tables / wikitext_cell '
                    'with `wikitext_readings`',
    'snapshot_file': 'King_Crimson.wikitext',
    'snapshot_sha256': 'c23faf3753cc79a6c7d74e950e5a06d23a7d1f27bd6f5aebad25c2bb5d4109bd',
    'snapshot_bytes': 5876,
    'snapshot_note': 'sha256 of the revision\'s bytes as the API serves them (newlines kept). The page is not committed; '
                     'the weekly `wikitext-sources` job refetches the pinned revision, checks both hashes and re-runs '
                     '--wikitext-dir, and fails when the page has a newer revision. A person re-checks it with '
                     '--html-dir, the two cross-source pages beside it.',
    'wikitext_readings': {'p': 'U', 's': 's', 'Q': 'q'},
    'wikitext_readings_note': 'route_transcription.wikitext_cell reads blank as -, G as c, P as U and an upper-case piece '
                              'letter as its lower case; this page also draws `p` (the basic setup\'s placed T, read U), '
                              '`s` (one S cell drawn lighter, read as the S) and `Q` (light grey, the rest of the stack, '
                              'read q: filled, no piece)',
    'shiwehi': {'checked': '2026-10-29',
                'index': 'https://shiwehi.com/tetris/template/ (its 中盤テンプレ・ドネイト list names no King Crimson)',
                'guessed_url': 'https://shiwehi.com/tetris/template/kingcrimson.php (HTTP 404)',
                'note': 'no shiwehi.com page draws a King Crimson, so harddrop\'s page is the primary source'},
    'references_listed': ['https://harddrop.com/wiki/T-Spin_Double', 'https://harddrop.com/wiki/T-Spin_Triple',
                          'https://harddrop.com/wiki/Super_T-Spin_Double', 'https://harddrop.com/wiki/Nil-cross',
                          'https://harddrop.com/wiki/TKI_3_Opening'],
    'references_note': 'the page\'s own [[links]], as URLs; Super T-Spin Double is read (cross_source), the rest are not',
}

TERMS = {
    'url': 'https://harddrop.com/wiki/Hard_Drop_Tetris_Wiki:About',
    'dated': 'not stated: harddrop publishes no licence or terms page for wiki content',
    'read': '2026-10-15, for SDPC Spin (sdpcspin-routes.json): the page footer and the About page it links (no body); '
            'not re-read for this page',
    'allows': 'not stated (no licence is published)',
    'excludes': 'not stated (no licence is published)',
    'requests': 'not stated; credited by link, as this repo credits every harddrop page it reads',
    'how_met': 'source link to the harddrop page in every page header; no ads on GitHub Pages',
}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall; heights differ',
    '-': 'empty',
    'c': 'a cell drawn grey (harddrop G): placed before this diagram, any piece or garbage',
    'q': 'a cell drawn light grey (harddrop Q): the rest of the stack, filled, no piece (OUR READING)',
    'i j l o z s': 'a cell of that piece (harddrop\'s upper-case letters; one lower-case s is a lighter S cell)',
    'U': 'a cell of the T the spin places (harddrop P, and the basic setup\'s lower-case p)',
    'muting': 'harddrop never draws the rows a spin clears muted, so no board here uses upper case; every spin board '
              'is a named `:muting` discrepancy',
}

QUOTES = [
    {'id': 'def', 'verbatim': "A '''King Crimson''' is a [[T-Spin Triple]] layered on top of a [[Super T-Spin Double]] "
                              'which can be performed when the playfield has a single block in the bottom left or bottom '
                              'right corner.'},
    {'id': 'tki', 'verbatim': 'It can also be used as a continuation of the [[TKI_3_Opening|TKI 3]] opener.'},
    {'id': 'h.basic', 'verbatim': "'''Basic setup:'''"},
    {'id': 'h.tki', 'verbatim': '== Continuation from TKI 3 =='},
    {'id': 'tki.bonus', 'verbatim': 'After the first or second T-Spin from a [[TKI_3_Opening|TKI 3]] setup, a King '
                                    'Crimson bonus is possible.'},
    {'id': 'tki.warn', 'verbatim': 'This is usually not suggested due to its high height and the 3 T pieces necessary '
                                   'to complete the setup.'},
    {'id': 'h.first', 'verbatim': "'''First T-Spin'''"},
    {'id': 'h.second', 'verbatim': "'''Second T-Spin'''"},
    {'id': 'h.empty', 'verbatim': '== Empty Field Setup =='},
    {'id': 'clear', 'verbatim': 'Clear'},
]

_TKI = '---------- ---------- ---------- ---------- ---------- ---jjj---- l--zzjs--- l---zzssoo ll-iiiisoo'
_TKI_SPIN = '---------- ---------- ---------- ---------- ---------- ---jjj---- l--zzjs--- lUUUzzssoo llUiiiisoo'
_TKI_AFTER = '---------- ---------- ---------- ---------- ---------- ---------- ---------- ---jjj---- l--zzjs---'


def _n(nid: str, table: int, board: int, kind: str, quote: str, label: str, rows: str, **kw) -> dict:
    return {'id': nid, 'table': table, 'board': board, 'kind': kind, 'caption_quote': quote, 'label': label,
            'rows': _b(rows), **kw}


NODES = [
    # ── table 0: Basic setup ──
    _n('basic', 0, 0, 'base', 'def', 'the basic setup: a one-column well under an overhang, a TST slot over an STSD slot',
       '------cc-- ccccccc--- ccccccc-ll ccccccc--l ccccccc-sl ccccccc-ss ccccccc--s ccccccc--c'),
    _n('basic.spin', 0, 1, 'spin', 'def', 'the T stood up into the upper slot: a T-spin Triple',
       '------cc-- ccccccc--- cccccccUll cccccccUUl cccccccUsl ccccccc-ss ccccccc--s ccccccc--c',
       spin_of='basic', spin_piece='U', spin='TST', lines=3),
    _n('basic.after', 0, 2, 'after', 'def', 'what the TST leaves: the STSD under the overhang',
       '---------- ---------- ---------- ------cc-- ccccccc--- ccccccc-ss ccccccc--s ccccccc--c', after_of='basic.spin'),
    # ── table 1: Continuation from TKI 3, First T-Spin ──
    _n('tki1.form', 1, 0, 'base', 'tki.bonus', 'TKI 3', _TKI),
    _n('tki1.spin', 1, 1, 'spin', 'tki.bonus', 'TKI 3\'s T-spin Double', _TKI_SPIN,
       spin_of='tki1.form', spin_piece='U', spin='TSD', lines=2),
    _n('tki1.after', 1, 2, 'after', 'tki.bonus', 'what the TSD leaves', _TKI_AFTER, after_of='tki1.spin'),
    _n('tki1.z', 1, 3, 'build', 'tki.bonus', 'a Z stood against the left wall, the TKI residue drawn grey',
       '---------- ---------- ---------- ---------- ---------- -z-------- zz-------- z--ccc---- c--cccc---',
       on='tki1.after', adds='z'),
    _n('tki1.j', 1, 4, 'build', 'tki.bonus', 'a J hooked over it: the overhang\'s wall',
       '---------- ---------- ---------- jj-------- j--------- jz-------- zz-------- z--ccc---- c--cccc---',
       on='tki1.z', adds='j'),
    _n('tki1.kc', 1, 5, 'build', 'tki.bonus', 'the King Crimson, the rest of the stack drawn light grey (mirrored)',
       '---------- --qq------ ---qqqqqqq jj-qqqqqqq j--qqqqqqq jz-qqqqqqq zz-qqqqqqq z--cccqqqq c--ccccqqq',
       on='tki1.j', adds='q'),
    # ── tables 2 and 3: Continuation from TKI 3, Second T-Spin (the page draws it in two tables) ──
    _n('tki2.form', 2, 0, 'base', 'tki.bonus', 'TKI 3 again', _TKI, same_occupancy_as='tki1.form'),
    _n('tki2.spin', 2, 1, 'spin', 'tki.bonus', 'TKI 3\'s T-spin Double again', _TKI_SPIN,
       spin_of='tki2.form', spin_piece='U', spin='TSD', lines=2),
    _n('tki2.after', 2, 2, 'after', 'tki.bonus', 'what the TSD leaves', _TKI_AFTER, after_of='tki2.spin'),
    _n('tki2.build', 2, 3, 'build', 'tki.bonus', 'a Z, an O, an I and a J built for TKI 3\'s second T-spin Double',
       '---------- ---------- ---------- ---------- ---------- -z-------- zz-iiii--j zooccc---j coocccc-jj',
       on='tki2.after', adds='zoij'),
    _n('tki2.tsd', 2, 4, 'spin', 'tki.bonus', 'TKI 3\'s second T-spin Double',
       '---------- ---------- ---------- ---------- ---------- -z-------- zz-iiii--j zoocccUUUj cooccccUjj',
       spin_of='tki2.build', spin_piece='U', spin='TSD', lines=2),
    _n('tki2.tsd.after', 2, 5, 'after', 'tki.bonus', 'what the second TSD leaves',
       '---------- ---------- ---------- ---------- ---------- ---------- ---------- -z-------- zz-iiii--j',
       after_of='tki2.tsd'),
    _n('tki2.s', 3, 0, 'build', 'tki.bonus', 'an S stood against the right wall, the residue drawn grey',
       '---------- ---------- ---------- ---------- ---------- --------s- --------ss -c-------s cc-cccc--c',
       on='tki2.tsd.after', adds='s'),
    _n('tki2.l', 3, 1, 'build', 'tki.bonus', 'an L hooked over it: the TST slot\'s far wall',
       '---------- ---------- ---------- --------ll ---------l --------sl --------ss -c-------s cc-cccc--c',
       on='tki2.s', adds='l'),
    _n('tki2.kc', 3, 2, 'build', 'tki.bonus', 'the King Crimson, the rest of the stack drawn light grey (as drawn)',
       '---------- ------qq-- qqqqqqq--- qqqqqqq-ll qqqqqqq--l qqqqqqq-sl qqqqqqq-ss qcqqqqq--s ccqcccc--c',
       on='tki2.l', adds='q'),
    # ── table 4: Empty Field Setup ──
    _n('empty.j', 4, 0, 'base', 'h.empty', 'a J laid flat in the bottom corner',
       '---------- ---------- ---------- ---------- ---------- ---------- ---------- j--------- jjj-------'),
    _n('empty.clear', 4, 1, 'build', 'clear', 'the bottom row filled and cleared',
       '---------- ---------- ---------- ---------- ---------- ---------- ---------- j--------- jjjqqqqqqq',
       on='empty.j', adds='q'),
    _n('empty.cell', 4, 2, 'illustration', 'clear', 'the single block in the bottom corner the clear leaves',
       '---------- ---------- ---------- ---------- ---------- ---------- ---------- ---------- j---------'),
    _n('empty.kc', 4, 3, 'build', 'def', 'the King Crimson on it (mirrored)',
       '---------- --qq------ ---qqqqqqq jj-qqqqqqq j--qqqqqqq jz-qqqqqqq zz-qqqqqqq z--qqqqqqq c--qqqqqqq',
       on='empty.cell', adds='jzq'),
]

_SLOT = [[2, 7], [3, 7], [3, 8], [4, 7]]

VARIANTS = [{
    'id': 'kingcrimson', 'board': 'basic.spin', 'spin': 'TST', 'lines': 3,
    'window_basis': 'agreement',
    'window': {'rows': [0, 7], 'cols': [6, 9]},
    't_cells': _SLOT,
    'roof_cells': [[0, 6], [0, 7], [1, 6]],
    'window_note': 'in basic.spin\'s frame, row 0 the top: the AGREEMENT BOX of this page\'s four drawings of the shape '
                   'and two drawings on two other harddrop pages, each selected by that page\'s own King Crimson label. '
                   'Column 6 is the well\'s wall (filled top to bottom), column 7 the well (the overhang over it in row '
                   '0, empty from row 1 down), column 8 the TST slot\'s far side and the STSD\'s nub column, column 9 '
                   'the wall column on the open side. Rows 2-4 are the rows the TST clears (entailed by the clear at a '
                   'full TST, NaiveClauseForced); above them the overhang (row 0) and the row under it (row 1, open on '
                   'the far side); under them the STSD slot (rows 5-7: its nub row walled by the far column\'s S, its '
                   'bottom cell under the T, the cell beside it open). Left of column 6, and above row 0, is outside: '
                   'the drawings disagree there (column 5 of row 0) or one of them ends (the basic setup\'s top row). '
                   'Occupancy only, never colour; garbage is filled.',
    'agreement': [
        {'board': 'basic', 't_cells': _SLOT, 'mirrored': False},
        {'board': 'tki1.kc', 't_cells': [[3, 2], [4, 1], [4, 2], [5, 2]], 'mirrored': True},
        {'board': 'tki2.kc', 't_cells': [[3, 7], [4, 7], [4, 8], [5, 7]], 'mirrored': False},
        {'board': 'empty.kc', 't_cells': [[3, 2], [4, 1], [4, 2], [5, 2]], 'mirrored': True},
    ],
    'untested_drawn': {'cells': [], 'reason': ''},
    'followup': {'board': 'basic.after', 'spin': 'TSD', 'lines': 2,
                 't_cells_pre_clear': [[5, 7], [6, 7], [6, 8], [7, 7]],
                 't_cells_after': [[5, 7], [6, 7], [6, 8], [7, 7]],
                 'note': 'the STSD: a second T stood up into the lower slot, nub toward the open side, credited as a '
                         'full T-spin Double (the page: 「a [[T-Spin Triple]] layered on top of a [[Super T-Spin '
                         'Double]]」). Its cells are all under the TST\'s three cleared rows, so the clear does not move '
                         'or split them; the matcher carries the slot to the next T all the same.'},
    'fires_on': ['basic', 'tki2.kc'],
    'misses': ['basic.after', 'tki1.form', 'tki1.spin', 'tki1.after', 'tki1.z', 'tki1.j',
               'tki2.form', 'tki2.spin', 'tki2.after', 'tki2.build', 'tki2.tsd', 'tki2.tsd.after', 'tki2.s', 'tki2.l',
               'empty.j', 'empty.clear', 'empty.cell'],
}]


def _p(table: int, board: int, role: str, mirrored: bool | None, rows: str, note: str) -> dict:
    return {'table': table, 'board': board, 'role': role, 'mirrored': mirrored, 'rows': _b(rows), 'note': note}


_API = ('the pinned revision\'s own bytes from the MediaWiki API (api.php?action=query&prop=revisions&titles=<title>&'
        'rvprop=ids|sha1|content|timestamp&rvslots=main&format=json&formatversion=2), with Python\'s urllib and a '
        'descriptive User-Agent (NOT curl); the API\'s sha1 equals the sha1 of the bytes, and the revision was the '
        'page\'s latest when fetched')

#: two OTHER harddrop pages (other editors) that draw a King Crimson, each drawing selected by the page's own label:
#: the first `{| |}` table after `label_text`. Every board of that table is recorded (`role` drawing or other), and
#: over the WHOLE page the window fires on no board but the recorded drawings and `fires_elsewhere`
PAGES = [
    {
        'page': 'https://harddrop.com/wiki/T-Spin_Triple_Setups',
        'title': 'T-Spin Triple Setups',
        'oldid': 42323,
        'revision_sha1': '0e64836c95d3214bb8c83a5151cbe72763717aef',
        'revision_timestamp': '2025-02-21T13:50:15Z',
        'fetched': '2026-10-29',
        'fetch_method': _API,
        'snapshot_file': 'T-Spin_Triple_Setups.wikitext',
        'snapshot_sha256': '8ae446b1b7d9b4e8733fd0f4338b1b0279e8fb2609f9c5e612e2e8ee5a0a2042',
        'snapshot_bytes': 48802,
        'snapshot_note': 'not committed: check_wikitext_sources refetches the pinned revision weekly through api.php '
                         'and re-checks it with --wikitext-dir',
        'label_text': '[[King Crimson]] is a technique that results in a \'\'\'T-Spin Triple\'\'\' followed by a STSD',
        'section': 'Setups involving T-Spin Triples',
        'table': 29,
        'boards': [
            _p(29, 0, 'drawing', True, '---------- --ll------ ---lgggggg jjUlgggggg jUUggggggg jzUggggggg zz-ggggggg '
               'z--ggggggg g--ggggggg', 'the King Crimson with its TST drawn (P), mirrored: an L as the overhang'),
            _p(29, 1, 'other', None, '---------- ---------- ---------- ---------- --ll------ ---lgggggg zz-ggggggg '
               'z--ggggggg g--ggggggg', 'what the TST leaves'),
            _p(29, 2, 'other', None, '---------- ---------- ---------- ---------- --ll------ ---lgggggg zzUggggggg '
               'zUUggggggg g-Uggggggg', 'the STSD\'s stood T (the follow-up), its first T-spin Double'),
            _p(29, 3, 'other', None, '---------- ---------- ---------- ---------- ---------- ---------- --ll------ '
               '---lgggggg g-tggggggg', 'what that TSD leaves, the T\'s last cell'),
            _p(29, 4, 'other', None, '---------- ---------- ---------- ---------- ---------- ---------- --ll------ '
               'UUUlgggggg gUtggggggg', 'the STSD\'s second T-spin Double'),
        ],
        'fires_elsewhere': [],
    },
    {
        'page': 'https://harddrop.com/wiki/Super_T-Spin_Double',
        'title': 'Super T-Spin Double',
        'oldid': 42285,
        'revision_sha1': '3799c44caf1d39c2b65ea16af371886b8010df8d',
        'revision_timestamp': '2025-02-05T04:11:45Z',
        'fetched': '2026-10-29',
        'fetch_method': _API,
        'snapshot_file': 'Super_T-Spin_Double.wikitext',
        'snapshot_sha256': 'c7d490ebd8304154b0953c9fdc577f16728848ab8f21f2abf2328fda79ba360b',
        'snapshot_bytes': 31380,
        'snapshot_note': 'not committed: check_wikitext_sources refetches the pinned revision weekly through api.php '
                         'and re-checks it with --wikitext-dir',
        'label_text': "* '''[[King Crimson]]'''",
        'section': 'Combination Setups',
        'table': 34,
        'boards': [
            _p(34, 0, 'drawing', False, '---------- gggggggg-- ggggggg--- ggggggg-ll ggggggg--l ggggggg-sl ggggggg-ss '
               'ggggggg--s ggggggg--g', 'the King Crimson, as drawn, no T drawn: its slot is OUR READING (`t_cells`)'),
        ],
        'drawing_slots': {'0': [[3, 7], [4, 7], [4, 8], [5, 7]]},
        'fires_elsewhere': [],
    },
]

CROSS_SOURCE = {
    'kind': 'harddrop_pages',
    'label_pattern': 'crimson',
    'note': 'the window, by the gate\'s predicate (technique_transcription.window_fires), over every U-slot board of '
            'every committed *-routes.json, with the U cells as the T: it fires on none (no route page draws a King '
            'Crimson). The independent drawers are two other harddrop pages (`pages`), whose King Crimson drawings are '
            'the window\'s external `agreement` drawings: rule (g) fires the window on each, once, at its slot, in its '
            'recorded hand.',
    'routes_fire_none': 'no committed routes file draws a King Crimson (measured: the window fires on none of their '
                        'U-slot boards); the cross-check is two other harddrop pages, read below',
    'pages': PAGES,
    #: every board of every OTHER committed technique transcription on which the window fires (spin boards at their
    #: drawn T, every other board at every resting placement of a T), measured by `other_technique_fires`
    'other_techniques': [],
    'fires': [],
    'also': [],
    'labelled_not_fired': [],
}

KNOWN_DISCREPANCIES = [
    {'id': f'{i}:muting', 'note': 'harddrop draws the rows the spin clears in the same letters as the rest (it never '
                                  'mutes a cleared row), so the spin rule\'s upper case is named here, board by board'}
    for i in ('basic.spin', 'tki1.spin', 'tki2.spin', 'tki2.tsd')
] + [{'id': 'empty.cell:colour', 'note': 'the single block the empty-field clear leaves is one cell of the J (the page '
                                         'draws it in the J\'s letter): a piece cut by a line clear, not a whole J'}]

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'kingcrimson',
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


# ── the other harddrop pages ─────────────────────────────────────────────────────────────────────
def _slot(rows: list[str]) -> list[list[int]]:
    return sorted([r, c] for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == 'U')


def page_slots(pg: dict, d: dict) -> list[list[int]]:
    """A recorded drawing's slot: its drawn T, or (no T drawn) the page record's `drawing_slots` reading."""
    s = _slot(d['rows'])
    return s if s else pg.get('drawing_slots', {}).get(str(d['board']), [])


def harddrop_drawings(data: dict | None = None) -> list[dict]:
    """The two other pages' drawings as agreement drawings: the slot read as empty."""
    data = data or build()
    out = []
    for pg in data['cross_source']['pages']:
        for d in pg['boards']:
            if d['role'] == 'drawing':
                out.append({'name': f'harddrop {pg["title"]} table {d["table"]} board {d["board"]}',
                            'rows': [row.replace('U', EMPTY) for row in d['rows']],
                            't_cells': page_slots(pg, d), 'mirrored': d['mirrored']})
    return out


def _fires(data: dict, rows: list[str]) -> list[tuple[frozenset, bool]]:
    """Where the window fires on a harddrop board: at its drawn T (either hand) if it draws one, else at every
    resting placement of a T (either hand)."""
    v = data['variants'][0]
    slot = {tuple(x) for x in _slot(rows)}
    pre = [row.replace('U', EMPTY) for row in rows]
    cands = [slot] if len(slot) == 4 else ([] if slot else TT.t_placements(pre, SPEC))
    return [(frozenset(cs), m) for cs in cands for m in (False, True) if TT.window_fires(data, v, SPEC, pre, cs, m)]


def page_problems(data: dict, pg: dict, text: str) -> list[str]:
    """One other page against its wikitext: the first table after `label_text` is `table`, under `section`; its
    boards are exactly the recorded boards, letter for letter; the window fires on each `drawing` once, at its slot,
    in its recorded hand, and on no `other` board; over the whole page it fires on no board but those drawings and
    `fires_elsewhere`. So the drawings are chosen by the page's own label, and every firing on the page is named."""
    tag = f'harddrop {pg["title"]}'
    text = _tabled(text)
    try:
        tables = RT.wikitext_tables(text)
    except ValueError as e:
        return [f'{tag}: the wikitext does not parse: {e}']
    secs = _sections(text)
    k = text.find(pg['label_text'])
    if k < 0:
        return [f'{tag}: the label {pg["label_text"]!r} is not on the page']
    after = text[:k].count('{|')
    bad = []
    if after != pg['table'] or after >= len(tables):
        return bad + [f'{tag}: the first table after the label is table {after}, the record says {pg["table"]}']
    if secs[after] != pg['section']:
        bad.append(f'{tag}: table {after} sits under {secs[after]!r}, not {pg["section"]!r}')
    boards = {(i, j): [''.join(hd_cell(c) for c in row) for row in b] for i, t in enumerate(tables) for j, b in enumerate(t)}
    got = [boards[(after, j)] for j in range(len(tables[after]))]
    want = [d['rows'] for d in pg['boards']]
    if got != want or [d['board'] for d in pg['boards']] != list(range(len(want))):
        bad.append(f'{tag}: table {after}\'s boards are not the recorded ones (page {len(got)}, record {len(want)})')
    fired = set()
    for (i, j), rows in boards.items():
        if _fires(data, rows):
            fired.add((i, j))
    want_fired = {(d['table'], d['board']) for d in pg['boards'] if d['role'] == 'drawing'} | \
                 {(e['table'], e['board']) for e in pg.get('fires_elsewhere', [])}
    if fired != want_fired:
        bad.append(f'{tag}: the window fires on {sorted(fired)}, the record names {sorted(want_fired)}')
    return bad


def other_page_checks(data: dict, html_dir: Path) -> list[str]:
    """The two other pinned harddrop pages beside the primary (a missing file is a failure)."""
    bad = []
    for pg in data['cross_source']['pages']:
        p = Path(html_dir) / pg['snapshot_file']
        if not p.exists():
            bad.append(f'harddrop {pg["title"]}: {pg["snapshot_file"]} is not in {html_dir} — fetch it beside the page')
            continue
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != pg['snapshot_sha256'] or len(raw) != pg['snapshot_bytes']:
            bad.append(f'harddrop {pg["title"]}: hash: sha256/bytes {hashlib.sha256(raw).hexdigest()} / {len(raw)} '
                       f'are not the recorded ones')
        if hashlib.sha1(raw).hexdigest() != pg['revision_sha1']:
            bad.append(f'harddrop {pg["title"]}: hash: sha1 {hashlib.sha1(raw).hexdigest()} is not MediaWiki\'s revision sha1')
        bad += page_problems(data, pg, raw.decode('utf8'))
    return bad


def wikitext_checks(data: dict, html_dir: Path) -> list[str]:
    """`--wikitext-dir`: all three pinned revisions. The primary page through the shared snapshot reader (its hash
    line tagged `source: hash:`, the line the weekly selftest excuses offline), plus MediaWiki's sha1."""
    src = data['source']
    p = Path(html_dir) / src['snapshot_file']
    if not p.exists():
        return [f'source: {src["snapshot_file"]} is not in {html_dir}']
    bad = [('source: hash: ' + x[len('snapshot: '):]) if 'sha256' in x and x.startswith('snapshot: sha256') else x
           for x in RT.check_snapshot(data, Path(html_dir))]
    raw = p.read_bytes()
    try:
        sizes = [len(t) for t in RT.wikitext_tables(raw.decode('utf8'))]
    except ValueError:
        sizes = None   # the shared reader has already reported it
    if sizes is not None and sizes != [sum(1 for n in data['nodes'] if n['table'] == t) for t in range(len(sizes))]:
        bad.append(f'source: the page\'s tables hold {sizes} boards, the nodes\' (table, board) say otherwise')
    if hashlib.sha1(raw).hexdigest() != src['revision_sha1'] or len(raw) != src['snapshot_bytes']:
        bad.append(f'source: hash: sha1/bytes {hashlib.sha1(raw).hexdigest()} / {len(raw)} are not the recorded ones')
    return bad + other_page_checks(data, html_dir)


# ── other technique transcriptions ───────────────────────────────────────────────────────────────
def other_technique_fires(data: dict) -> list[dict]:
    """The window over every board of every other committed `*-technique.json`: a spin board at its drawn spin
    (the T only), any other board at every resting placement of a T, both hands, read with that file's empty letters."""
    v = data['variants'][0]
    out = []
    for f in sorted(HERE.glob('*-technique.json')):
        if f == OUT:
            continue
        od = json.loads(f.read_text())
        sp = copy.copy(SPEC)
        sp.empty_letters = od.get('empty_letters', '')
        for n in od.get('nodes', []):
            rows = n.get('rows')
            if not rows:
                continue
            if n.get('kind') == 'spin':
                sc = TT.spin_cells(n)
                if n.get('spin_piece', 'T').lower() not in ('t', 'u'):
                    continue
                pre = [''.join(EMPTY if (r, c) in sc else ch for c, ch in enumerate(row)) for r, row in enumerate(rows)]
                cands = [sc]
            else:
                pre = [row.replace('U', EMPTY) for row in rows]
                cands = TT.t_placements(pre, sp)
            filled = (lambda R, C, pre=pre, sp=sp: not TT.is_empty(pre[R][C], sp))
            for m in (False, True):
                if any(TT.window_fires(data, v, sp, pre, cs, m, filled) for cs in cands):
                    out.append({'file': f.name, 'node': n['id'], 'mirrored': m})
    return out


# ── technique-only rules ─────────────────────────────────────────────────────────────────────────
def extra_checks(data: dict):
    bad, measured = [], set()
    by = {n['id']: n for n in data['nodes']}
    v = data['variants'][0]
    xs = data['cross_source']
    # every board of the page is accounted for: the variant's board, its follow-up board, a drawing of the shape
    # (agreement), or a board it is checked to fire on or to miss
    acc = [v['board'], *(a['board'] for a in v.get('agreement', [])), *v.get('fires_on', []), *v.get('misses', [])]
    left = [n['id'] for n in data['nodes'] if n['id'] not in acc]
    if left:
        bad.append(f'window: boards neither a drawing, fired on nor missed: {left}')
    mirrored_drawings = [a['board'] for a in v.get('agreement', []) if a['mirrored']]
    if sorted(a['board'] for a in v.get('agreement', []) if not a['mirrored']) != sorted(v.get('fires_on', [])):
        bad.append('window: the page\'s as-drawn drawings of the shape (agreement) are not fires_on')
    for b in mirrored_drawings:
        if b in v.get('misses', []):
            bad.append(f'window: {b} is a drawing of the shape and a miss')
    # the page's table and board of every node: page order, with the boards of a table numbered from 0
    seen = [(n['table'], n['board']) for n in data['nodes']]
    want = []
    for n in data['nodes']:
        t = n['table']
        want.append((t, sum(1 for m in data['nodes'][:data['nodes'].index(n)] if m['table'] == t)))
    tabs = sorted({t for t, _ in seen})
    if seen != want or tabs != list(range(len(tabs))) or [t for t, _ in seen] != sorted(t for t, _ in seen):
        bad.append('page: the nodes\' (table, board) are not the page order, each table\'s boards numbered from 0')
    # the other pages: each drawing, as recorded in the DATA, fires once at its slot in its hand and nowhere else
    for pg in xs.get('pages', []):
        for d in pg['boards']:
            if any(len(r) != WIDTH for r in d['rows']):
                bad.append(f'harddrop {pg["title"]}: table {d["table"]} board {d["board"]} is not ten wide')
                continue
            got = _fires(data, d['rows'])
            if d['role'] == 'drawing':
                slot = frozenset(tuple(x) for x in page_slots(pg, d))
                if got != [(slot, d['mirrored'])]:
                    bad.append(f'harddrop {pg["title"]}: the window fires {len(got)} time(s) on table {d["table"]} '
                               f'board {d["board"]}, not once at its slot ({"mirrored" if d["mirrored"] else "as drawn"})')
            elif got:
                bad.append(f'harddrop {pg["title"]}: table {d["table"]} board {d["board"]} is recorded `other` and the '
                           f'window fires on it')
            if not d.get('note', '').strip():
                bad.append(f'harddrop {pg["title"]}: table {d["table"]} board {d["board"]} carries no note')
        if not any(d['role'] == 'drawing' for d in pg['boards']):
            bad.append(f'harddrop {pg["title"]}: no drawing recorded')
    # the follow-up: the STSD slot under the TST slot, the stood T one storey lower
    fu = sorted(tuple(x) for x in v['followup']['t_cells_pre_clear'])
    if fu != sorted((r + 3, c) for r, c in (tuple(x) for x in v['t_cells'])):
        bad.append('window: the follow-up slot is not the TST slot one T lower (three rows down, the same columns)')
    # other techniques: the window fires on exactly the recorded boards
    key = lambda e: (e['file'], e['node'], e['mirrored'])
    got = sorted(map(key, other_technique_fires(data)))
    want = sorted(map(key, xs.get('other_techniques', [])))
    if got != want:
        bad.append(f'other: the window fires on {got} of the other technique transcriptions, the record names {want}')
    return bad, measured


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='',
    upper_groups={}, max_rows=MAX_ROWS, muting_slips=True,
    extra_checks=extra_checks,
    external_drawings=lambda: harddrop_drawings(),
    # `--html-dir` runs the shared snapshot reader over the primary page itself; this adds the two other pages
    html_checks=other_page_checks,
    # what a weekly api.php refetch can run: all three pinned revisions (the primary through the shared reader)
    wikitext_checks=wikitext_checks,
    synthetic_wikitext=lambda d: {d['source']['snapshot_file']: _synthetic_primary(d),
                                  **{pg['snapshot_file']: _synthetic_page(pg) for pg in d['cross_source']['pages']}},
    synthetic_snapshot=lambda d: _synthetic_primary(d),
)


# ── synthetic pages (selftests) ──────────────────────────────────────────────────────────────────
def _synthetic_primary(data: dict) -> str:
    """The primary page rebuilt from the transcription: its tables in page order, its quotes as text."""
    n = max(x['table'] for x in data['nodes']) + 1
    tables = [[node(data, i)['rows'] for i in data['page_order'] if node(data, i)['table'] == t] for t in range(n)]
    return ' '.join(q['verbatim'] for q in data['quotes']) + '\n' + RT.synthetic_wikitext(tables)


def _synthetic_page(pg: dict) -> str:
    """Another page rebuilt: blank one-board tables up to the recorded table, its heading, the label, the table."""
    blank = [[EMPTY * WIDTH] * 4]
    head = RT.synthetic_wikitext([blank] * pg['table'])
    return (head + f'\n== {pg["section"]} ==\n' + pg['label_text'] + '\n'
            + RT.synthetic_wikitext([[d['rows'] for d in pg['boards']]]))


# ── selftest ─────────────────────────────────────────────────────────────────────────────────────
def _set(rows, r, c, ch):
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _var(d):
    return d['variants'][0]


def _pg(d, i):
    return d['cross_source']['pages'][i]


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'basic')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: d['page_order'].reverse(), 'page_order swapped', 'grammar:'),
    (lambda d: node(d, 'basic.spin').__setitem__('spin_of', 'nowhere'), 'a dangling reference', 'grammar:'),
    (lambda d: _set(node(d, 'tki1.j')['rows'], 8, 0, '-'), 'a build board cell flipped', 'build:'),
    (lambda d: _set(node(d, 'tki2.form')['rows'], 8, 9, '-'), 'a repeated board not the same occupancy', 'build:'),
    (lambda d: node(d, 'basic.spin').__setitem__('lines', 2), 'the TST\'s line count', 'spin:'),
    (lambda d: (_set(node(d, 'basic.spin')['rows'], 3, 8, 'c'), _set(node(d, 'basic.spin')['rows'], 3, 6, 'U')),
     'the TST\'s T not a T', 'spin:'),
    (lambda d: _set(node(d, 'basic.after')['rows'], 4, 7, 'c'), 'the after board not what the TST leaves', 'discrepancy:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [5, 9]), 'the window widened by a column', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('cols', [7, 9]), 'the window without the well\'s wall', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [1, 7]), 'the window without the overhang', 'window:'),
    (lambda d: _var(d)['window'].__setitem__('rows', [0, 6]), 'the window without the STSD\'s bottom cell', 'window:'),
    (lambda d: _var(d)['roof_cells'].pop(), 'a roof cell unnamed', 'window:'),
    (lambda d: _var(d)['agreement'][1].__setitem__('mirrored', False), 'a mirrored drawing read as drawn', 'window:'),
    (lambda d: _var(d)['agreement'][2].__setitem__('t_cells', [[4, 7], [5, 7], [5, 8], [6, 7]]),
     'a drawing\'s slot moved a row down', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('t_cells_pre_clear', [[4, 7], [5, 7], [5, 8], [6, 7]]),
     'the follow-up slot a row higher', 'window:'),
    (lambda d: _var(d)['followup'].__setitem__('lines', 3), 'the follow-up read as a TST', 'window:'),
    (lambda d: _var(d)['fires_on'].append('tki1.kc'), 'a mirrored drawing listed as firing as drawn', 'window:'),
    (lambda d: _var(d)['misses'].append('tki2.kc'), 'a board it fires on listed as a miss', 'window:'),
    (lambda d: _var(d)['misses'].remove('empty.cell'), 'a page board accounted nowhere', 'window:'),
    (lambda d: _set(node(d, 'tki1.form')['rows'], 8, 0, 'j'), 'a piece broken', 'discrepancy:'),
    (lambda d: d['known_discrepancies'].pop(), 'a harddrop spin board\'s unmuted rows unnamed', 'discrepancy:'),
    (lambda d: node(d, 'tki1.kc').__setitem__('board', 9), 'a node\'s board index', 'page:'),
    (lambda d: node(d, 'tki2.s').__setitem__('table', 2), 'a node\'s table index', 'page:'),
    (lambda d: _pg(d, 0)['boards'][0].__setitem__('mirrored', False), 'an other page\'s drawing read as drawn',
     'harddrop'),
    (lambda d: _set(_pg(d, 1)['boards'][0]['rows'], 1, 6, '-'), 'an other page\'s overhang dropped', 'harddrop'),
    (lambda d: _pg(d, 0)['boards'][1].__setitem__('role', 'drawing'), 'an other board recorded as a drawing', 'harddrop'),
    (lambda d: _pg(d, 0)['boards'][2].__setitem__('note', ''), 'an other board with no note', 'harddrop'),
    (lambda d: d['cross_source']['other_techniques'].append({'file': 'stsd-technique.json', 'node': 'basic',
                                                             'mirrored': False}),
     'an other technique board recorded that does not fire', 'other:'),
    (lambda d: d['cross_source'].pop('routes_fire_none'), 'no routes board and no reason', 'cross:'),
    (lambda d: d['cross_source']['fires'].append({'file': 'sdpcspin-routes.json', 'node': '3.first.cave',
                                                  'variant': 'kingcrimson', 'mirrored': True}),
     'a routes board recorded that does not fire', 'cross:'),
    (lambda d: node(d, 'tki2.kc').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['known_discrepancies'].append({'id': 'basic:colour', 'note': 'x'}), 'a stale discrepancy', 'discrepancy:'),
]


def _no_external(spec):
    s = copy.copy(spec)
    s.external_drawings = None
    return s


def _tki_as_drawing(spec):
    """TKI 3's board read as a King Crimson drawing (a slot it does not have): the agreement rule must refuse it."""
    s = copy.copy(spec)
    rows = node(build(), 'tki1.form')['rows']
    s.external_drawings = lambda: harddrop_drawings() + [{'name': 'TKI 3 as a King Crimson', 'rows': rows,
                                                          't_cells': [[6, 1], [7, 1], [7, 2], [8, 1]], 'mirrored': True}]
    return s


SPEC_MUTANTS = [
    (_no_external, 'no external drawing (the window checked against this page alone)', 'window:'),
    (_tki_as_drawing, 'TKI 3 read as a drawing of the shape', 'window:'),
]


def selftest() -> int:
    rc = TT.run_selftest(SPEC, MUTANTS,
                         {'board': ('{{pfrow|G|G|G|G|G|G|G|P|L|L}}', '{{pfrow|G|G|G|G|G|G|G| |L|L}}'),
                          'text': ('King Crimson bonus is possible', 'King Crimson bonus is impossible')},
                         SPEC_MUTANTS)
    ok = rc == 0
    base = build()
    pages = SPEC.synthetic_wikitext(base)
    for pg in base['cross_source']['pages']:
        text = pages[pg['snapshot_file']]
        clean = page_problems(base, pg, text)
        if clean:
            print(f'selftest FAILED: the synthetic {pg["title"]} page does not verify ({clean[:2]})')
            ok = False
            continue
        first = pg['boards'][0]['rows']
        loose = RT.synthetic_wikitext([[first]])
        plants = {
            'a recorded board redrawn': text.replace('{{pfrow|' + '|'.join(RT.wikitext_page_cell(ch) for ch in first[1])
                                                     + '}}', '{{pfrow|' + '|'.join(' ' for _ in first[1]) + '}}', 1),
            'the label moved off the page': text.replace(pg['label_text'], 'King Crimson elsewhere', 1),
            'a heading renamed': text.replace(f'== {pg["section"]} ==', '== Renamed ==', 1),
            'a firing drawing elsewhere on the page left unrecorded': text + '\n' + loose,
        }
        for label, page in plants.items():
            got = page_problems(base, pg, page)
            if page == text or not any(x.startswith('harddrop') for x in got):
                print(f'selftest FAILED: {pg["title"]}: {label} was not caught ({got[:2]})')
                ok = False
            else:
                print(f'  killed: {pg["title"]}: {label}  [harddrop]')
    with tempfile.TemporaryDirectory() as td:
        missing = wikitext_checks(base, Path(td))
        for f, t in pages.items():
            (Path(td) / f).write_text(t)
        hashed = wikitext_checks(base, Path(td))
    if not any('is not in' in x for x in missing) or not any(': hash: ' in x for x in hashed) \
            or any(': hash: ' not in x for x in hashed):
        print(f'selftest FAILED: the pinned revisions (missing={missing[:1]}, hashed={hashed[:3]})')
        ok = False
    else:
        print('  killed: a pinned revision missing / its bytes not the pinned revision (and nothing else)  [hash:]')
    print('selftest: King Crimson checks all caught' if ok else 'selftest: FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))

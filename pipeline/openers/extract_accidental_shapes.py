"""Transcribe the 意外 T-spin (accidental TSD / TST) boards into `accidental-technique.json`.

    python3 -m pipeline.openers.extract_accidental_shapes                   # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_accidental_shapes --selftest        # prove the verifier has teeth
    python3 -m pipeline.openers.extract_accidental_shapes --html-dir <dir>  # re-check the video file by hash
    python3 -m pipeline.openers.extract_accidental_shapes --html-dir <dir> --write  # ...and rewrite

yachi asked for it on 2026-11-20 (「Add 中盤，accidental tsd tst」) with an 11-second phone recording of a
TETR.IO game: a T-spin that nobody built as a named setup, the stack just happened to leave a slot a T could spin
into. No site draws such a page, so this file is the only transcription, and its primary source is the video file
itself (yachi's own upload, not committed; its sha256 and size are recorded and `--html-dir` re-reads them).

DECISION: the technique is a RULE over a round's locks, not a shape (`window_basis: spin_rule`), refined with
yachi on 2026-11-20 (「係TSpin 完意外地有個tst 形，再加個屋頂就食得」; 「再加多一粒就即食tst」). A full TST at lock j
counts when the previous T-spin i of the round cleared lines, no T locks between them, j's four T cells (mapped back
through every clear and garbage row between) were covered before i's clear and empty right after it, at least one
column's top T cell was open to the sky right after it (access), and over such a column the lowest filled cell above
the T before j belongs to a piece placed after i (the roof; any number of roof pieces), and the slot box (the T rows
and the row under them, the T's columns and one each side) was already complete right after i's clear, so only the
roof is built between them (slot built; yachi 2026-11-21: 「擺完頂就食得，唔洗點砌，啲examples 要砌好多，唔算」) —
`technique-profile-accidental.ts`. It must also be mid-game and owned by no other technique page or opener route (the
qualify hook, `accidental-qualify.ts`). An earlier, stricter reading (the whole slot roofless after i, one piece
filling the cell over j's nub) was dropped because yachi's own video fails it: the cell over the nub was filled before
the TSD. No single drawing holds a round's locks, so no drawing can fire it: the boards here are examples, checked for
what a drawing CAN show (the T's box and the lines each spin clears), and the video pair is measured against the slot
clauses (`extra_checks`), which it satisfies.

WHAT IS A READING, flagged in the JSON (`legend`, `video.reading`):

  * the two video boards are read by eye off two frames (phone camera at an angle; no palette sampling), rows
    only as deep as the slot needs; `c` filled, `C` filled in a row the spin clears, `U` the T.
  * the video's first T-spin (at about 4.0 s) is a TSD with the T flat, nub down; it is drawn as the T-spin before
    the TST (`prev_spin_of`), never as a variant board.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path

from pipeline.openers import technique_transcription as TT
from pipeline.openers.technique_transcription import node

HERE = Path(__file__).resolve().parent
OUT = HERE / 'accidental-technique.json'

ALPHABET = frozenset('-cCU')
MAX_ROWS = 8
VIDEO_FILE = 'PXL_20261120_153445271.mp4'
VIDEO_SHA256 = 'c7a1d16ab3347e76c6ed2ef52a80ebccc315f7bac9eb26b50300bdc6ff4b1510'
VIDEO_BYTES = 12908032


def _b(text: str) -> list[str]:
    return text.split()


def _less_u(rows: list[str]) -> list[str]:
    return [r.replace('U', '-') for r in rows]


SOURCE = {
    'url': f'upload: {VIDEO_FILE} (yachi\'s own phone recording of a TETR.IO game, sent in the project thread on '
           '2026-11-20; no public URL)',
    'title': '意外 T-spin (accidental TSD / TST): yachi\'s recording',
    'site': 'none: yachi\'s own upload',
    'author_note': 'the recording and the request are yachi\'s; no site draws a page for this technique',
    'request': 'Add 中盤，accidental tsd tst',
    'fetched': '2026-11-20',
    'fetch_method': 'the file as uploaded to the thread; probed with ffprobe (1920x1080, 30000/1001 fps, 11.13 s) and '
                    'read by eye off single frames extracted with ffmpeg',
    'snapshot_file': VIDEO_FILE,
    'snapshot_sha256': VIDEO_SHA256,
    'snapshot_bytes': VIDEO_BYTES,
    'snapshot_note': 'sha256 and size of the uploaded file, ours alone (no second authority). The video is NOT '
                     'committed and nothing refetches it; `--html-dir <dir>` holding the file re-checks both.',
}

TERMS = {
    'url': 'none: yachi\'s own recording, sent to this project; not republished (no frame is committed or shown)',
    'allows': 'use inside this project, at yachi\'s request',
    'how_met': 'the boards are read off it by hand; the file stays out of the repository and the site',
}

LEGEND = {
    'orientation': 'rows top to bottom as drawn; 10 columns, column 0 the left wall',
    '-': 'empty',
    'c': 'a filled cell (any piece or garbage; the video is read by occupancy only)',
    'C': 'a filled cell in a row the spin clears (muted)',
    'U': 'a cell of the T the spin places',
}

QUOTES = [
    {'id': 'request', 'verbatim': 'Add 中盤，accidental tsd tst'},
]

_TSD_VIDEO = _b('--------cc -cccc---cc CCCCUUUCCC CCCCCUCCCC ccccc-cccc ccccc--ccc ccccc-cccc')
_TST_VIDEO = _b('----cc---- c--ccc---- cccccc---- cccccc--cc ccccc---cc CCCCCUCCCC CCCCCUUCCC CCCCCUCCCC')

NODES = [
    {'id': 'video.tsd', 'kind': 'derived', 'derived': True,
     'label': 'the video at about 4.0 s, before the T: a flat slot, nub down',
     'rows': _less_u(_TSD_VIDEO)},
    {'id': 'video.tsd.spin', 'kind': 'spin', 'caption_quote': 'request',
     'label': 'the video\'s first T-spin (about 4.0 s): a TSD, the T flat, nub down; the T-spin before the TST',
     'rows': _TSD_VIDEO, 'on': 'video.tsd', 'adds': 'U', 'spin_of': 'video.tsd', 'spin_piece': 'U',
     'spin': 'TSD', 'lines': 2, 'time_s': 4.0, 'prev_spin_of': 'video.tst.spin'},
    {'id': 'video.tst', 'kind': 'derived', 'derived': True,
     'label': 'the video at about 9.0 s, before the T: a slot one column wide, three deep, open to one side',
     'rows': _less_u(_TST_VIDEO)},
    {'id': 'video.tst.spin', 'kind': 'spin', 'caption_quote': 'request',
     'label': 'the video\'s second T-spin (about 9.0 s): a TST, the T stood up, nub right',
     'rows': _TST_VIDEO, 'on': 'video.tst', 'adds': 'U', 'spin_of': 'video.tst', 'spin_piece': 'U',
     'spin': 'TST', 'lines': 3, 'time_s': 9.0},
]


def _t_cells(rows):
    return [[r, c] for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == 'U']


def _box(cells):
    return {'rows': [min(r for r, _ in cells), max(r for r, _ in cells)],
            'cols': [min(c for _, c in cells), max(c for _, c in cells)]}


VARIANTS = [
    {'id': 'tst', 'board': 'video.tst.spin', 'spin': 'TST', 'lines': 3, 'window_basis': 'spin_rule',
     'window': _box(_t_cells(_TST_VIDEO)), 't_cells': _t_cells(_TST_VIDEO), 'roof_cells': [],
     'rule_note': 'a full T-spin Triple at lock j whose slot the previous T-spin i opened: i cleared lines, no T '
                  'locks between them, j\'s four T cells (mapped back through every clear and garbage row between) '
                  'were covered before i\'s clear and empty right after it, at least one column\'s top T cell was '
                  'open to the sky right after it, over such a column pieces placed after i roof the slot, and the slot '
                  'box (the T rows and the row under them, the T\'s columns and one each side) was already complete '
                  'right after i\'s clear, so only the roof is built between them; '
                  'mid-game (lock > 21), at a T no other technique page and no opener route owns '
                  '(accidental-qualify.ts). The window is the T\'s own box: the rule reads the round\'s locks, not '
                  'a drawn shape.',
     'fires_on': [], 'misses': []},
]

VIDEO = {
    'file': VIDEO_FILE,
    'sha256': VIDEO_SHA256,
    'bytes': VIDEO_BYTES,
    'probe': '1920x1080, 30000/1001 fps, 11.13 s (ffprobe); a phone filming a monitor',
    'reading': 'two boards read by eye off single frames (about 4.0 s and 9.0 s), occupancy only, rows only as deep '
               'as the slot needs; the T\'s cells are where it locked',
}

CROSS_SOURCE = {
    'kind': 'rule',
    'note': 'the variants are rules over the corpus (window_basis spin_rule): no drawing fires them by construction, '
            'so there is no window for a routes board or another site\'s drawing to check. The exclusions are '
            'measured instead, in accidental.test.ts: every qualifying hit has no other technique page\'s hit at '
            'the same T and no opener route owns it.',
    'routes_fire_none': 'a spin_rule variant fires on no board (technique_transcription.window_fires returns False '
                        'for it), so no routes board is recorded',
    'video': VIDEO,
    'fires': [],
    'also': [],
    'labelled_not_fired': [],
}

KNOWN_DISCREPANCIES: list = []

PAGE_ORDER = [n['id'] for n in NODES if not n.get('derived')]


def build() -> dict:
    return {
        'schema': 'technique-shapes/1',
        'technique': 'accidental',
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


def _clear(rows):
    """a spin board with its T filled, full rows cleared, empty rows in at the top"""
    filled = [''.join('c' if ch != '-' else '-' for ch in r) for r in rows]
    kept = [r for r in filled if '-' in r]
    return ['-' * 10] * (len(rows) - len(kept)) + kept


def _open(rows, cells):
    return all(all(rows[r][c] == '-' or (r, c) in cells for r in range(rr)) for rr, c in cells)


def video_pair(prev_rows, tst_rows):
    """The rule's clauses on a drawn pair (the two boards bottom-aligned): the TST's T cells were covered before the
    previous spin's clear and empty right after it; the clear opened at least one T column to the sky (its top T cell);
    over such a column the lowest filled cell above the T on the TST board was empty right after the clear, i.e.
    placed after the previous spin (the roof); and every filled cell of the slot box on the TST board (the T rows and
    the row under them, the T's columns and one each side) was filled right after the clear (slot built: only the
    roof is added)."""
    filled = [''.join('c' if ch != '-' else '-' for ch in r) for r in prev_rows]
    keep = [i for i, r in enumerate(filled) if '-' in r]
    after = _clear(prev_rows)
    pad = len(after) - len(keep)
    off = len(tst_rows) - len(after)
    t = _t_cells(tst_rows)
    cells = {(r - off, c) for r, c in t}
    if any(r < 0 for r, _ in cells):
        return 'off_board'
    pre = {(keep[r - pad], c) for r, c in cells if r >= pad}
    if len(pre) < len(cells) or _open(filled, pre):
        return 'not_covered'
    if any(after[r][c] != '-' for r, c in cells):
        return 'filled'
    tops = [(r, c) for r, c in t if not any(c2 == c and r2 < r for r2, c2 in t)]
    access = [(r, c) for r, c in tops if _open(after, {(r - off, c)})]
    if not access:
        return 'no_access'
    roofed = False
    for r, c in access:
        for rr in range(r - 1, -1, -1):
            if tst_rows[rr][c] in '-U':
                continue
            if rr - off < 0 or after[rr - off][c] == '-':
                roofed = True
            break
    if not roofed:
        return 'not_roofed'
    rs, cs = [r for r, _ in t], [c for _, c in t]
    for r in range(min(rs), min(len(tst_rows) - 1, max(rs) + 1) + 1):
        for c in range(max(0, min(cs) - 1), min(9, max(cs) + 1) + 1):
            if tst_rows[r][c] in '-U':
                continue
            if r - off < 0 or after[r - off][c] == '-':
                return 'slot_built'
    return 'ok'


def extra_checks(data: dict):
    bad, measured = [], set()
    by = {n['id']: n for n in data['nodes']}
    # every spin board is a variant's board or the T-spin before one
    boards = {v['board'] for v in data['variants']}
    for n in data['nodes']:
        if n['kind'] != 'spin' or n['id'] in boards:
            continue
        nxt = n.get('prev_spin_of')
        if nxt not in boards:
            bad.append(f'rule: spin board {n["id"]} is no variant\'s board and the T-spin before none')
            continue
        got = video_pair(n['rows'], by[nxt]['rows'])
        if got != 'ok':
            measured.add(f'{nxt}:{got}')
    for v in data['variants']:
        n = by[v['board']]
        if n.get('spin') != v['spin']:
            bad.append(f'rule: {v["id"]}\'s board is a {n.get("spin")}, not a {v["spin"]}')
        if v['spin'] != 'TST':
            bad.append(f'rule: {v["id"]} takes a {v["spin"]}; the rule takes a TST only')
    vid = data['cross_source'].get('video', {})
    if vid.get('sha256') != data['source'].get('snapshot_sha256') or vid.get('bytes') != data['source'].get('snapshot_bytes'):
        bad.append('video: the video record and the source snapshot disagree')
    for n in data['nodes']:
        if n['id'].startswith('video.') and n['kind'] == 'spin' and not n.get('time_s'):
            bad.append(f'video: {n["id"]} names no time in the video')
    return bad, measured


def snapshot_check(data: dict, d: Path) -> list[str]:
    src = data['source']
    p = Path(d) / src['snapshot_file']
    if not p.exists():
        return [f'snapshot: {src["snapshot_file"]} is not in {d}']
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != src['snapshot_sha256'] or len(raw) != src['snapshot_bytes']:
        return [f'snapshot: {src["snapshot_file"]} is not the recorded file (sha256/bytes differ)']
    return []


SPEC = TT.TechniqueSpec(
    out=OUT, build=lambda: copy.deepcopy(build()), alphabet=ALPHABET, empty_letters='',
    upper_groups={}, max_rows=MAX_ROWS,
    extra_checks=extra_checks,
    snapshot_check=snapshot_check,
)


def _set(rows, r, c, ch):
    rows[r] = rows[r][:c] + ch + rows[r][c + 1:]


def _var(d, k):
    return d['variants'][k]


MUTANTS = [
    (lambda d: d['source'].pop('snapshot_sha256'), 'source hash dropped', 'provenance:'),
    (lambda d: _set(node(d, 'video.tst')['rows'], 0, 0, 'x'), 'a cell outside the alphabet', 'grammar:'),
    (lambda d: d['page_order'].reverse(), 'page_order swapped', 'grammar:'),
    (lambda d: _var(d, 0).__setitem__('followup', {'board': 'video.tst', 'spin': 'TSD', 'lines': 2}),
     'a follow-up on a spin_rule variant', 'grammar:'),
    (lambda d: _set(node(d, 'video.tst')['rows'], 0, 9, 'c'), 'the derived board not the spin board less its T',
     'build:'),
    (lambda d: node(d, 'video.tst.spin').__setitem__('lines', 2), 'the TST\'s line count', 'spin:'),
    (lambda d: _set(node(d, 'video.tst.spin')['rows'], 6, 0, 'c'), 'a cleared row drawn unmuted', 'spin:'),
    (lambda d: _var(d, 0)['window'].__setitem__('cols', [4, 6]), 'the window wider than the T', 'window:'),
    (lambda d: _var(d, 0).__setitem__('roof_cells', [[4, 5]]), 'a roof on a rule variant', 'window:'),
    (lambda d: _var(d, 0).update(board='video.tsd.spin', spin='TSD', lines=2, t_cells=_t_cells(_TSD_VIDEO),
                                 window=_box(_t_cells(_TSD_VIDEO))),
     'the TSD taken as the variant', 'rule:'),
    (lambda d: node(d, 'video.tsd.spin').pop('prev_spin_of'), 'the TSD tied to no TST', 'rule:'),
    (lambda d: d['known_discrepancies'].append({'id': 'video.tst.spin:not_roofed', 'note': 'x'}),
     'a stale discrepancy', 'discrepancy:'),
    (lambda d: [_set(node(d, k)['rows'], r, 5, '-') for k in ('video.tst', 'video.tst.spin') for r in (0, 1, 2, 3)],
     'the TST\'s roof taken away', 'discrepancy:'),
    (lambda d: [_set(node(d, k)['rows'], 1, 5, 'c') for k in ('video.tsd', 'video.tsd.spin')],
     'the column over the TST\'s stem left covered after the TSD', 'discrepancy:'),
    (lambda d: [_set(node(d, k)['rows'], 6, 4, '-') for k in ('video.tsd', 'video.tsd.spin')],
     'a slot wall of the TST missing right after the TSD (built between the spins)', 'discrepancy:'),
    (lambda d: node(d, 'video.tst.spin').__setitem__('caption_quote', 'nope'), 'a caption naming no quote', 'quote:'),
    (lambda d: d['cross_source']['video'].__setitem__('sha256', '0' * 64), 'the video record disagreeing', 'video:'),
    (lambda d: node(d, 'video.tsd.spin').pop('time_s'), 'a video board with no time', 'video:'),
    (lambda d: d['cross_source'].pop('routes_fire_none'), 'no routes board and no reason', 'cross:'),
]


def selftest() -> int:
    return TT.run_selftest(SPEC, MUTANTS, {})


if __name__ == '__main__':
    raise SystemExit(TT.main(SPEC, selftest, __doc__))

"""Transcribe the DPC setups of とんぼ's video into `dpc-setups.json`, and gate the transcription.

    python3 -m pipeline.openers.extract_dpc_setups                      # verify the committed file (offline, CI)
    python3 -m pipeline.openers.extract_dpc_setups --selftest           # prove the verifier has teeth
    python3 -m pipeline.openers.extract_dpc_setups --video <mp4>        # re-read every board off the video
    python3 -m pipeline.openers.extract_dpc_setups --video <mp4> --write  # ...and rewrite the file

THE SOURCE is one YouTube video: とんぼ_テトリス初心者講座, 「【テトリス初心者講座】超火力！TDパフェ後のDPCテンプレ解説」
(`1Wr8VbNfnIg`, 17:47). Its last part is a catalogue of the setups it teaches, one still page per case, each
titled by the piece left over after the TD opener's Perfect Clear and the order the next pieces come in
(「Oミノ残し：O>Z」), labelled with the setup's name (【くるまDPC】, 【JB_DPC】, 【トラックDPC】, 【2ラインパフェ】),
and drawing the board to build (組み方) beside the Perfect Clears that finish it (パフェ). Those pages are what
this file transcribes (`PAGES`, with the time of the frame read). The video's earlier teaching part is quoted
on the page, never transcribed.

NOTHING OF THE VIDEO IS COMMITTED. No frame, no clip: the boards are transcribed as text and every page links
the video at the page's time. YouTube does not let this sandbox fetch it (yt-dlp is refused), so it was
downloaded through www.snapyt.app; `source.file` records the sha256 and size of that download (720p MP4,
SnapYT's bytes — so the hash is ours, with no second authority behind it, which is weaker than the harddrop
pages this file used to transcribe, whose revisions MediaWiki's own sha1 pins). `check_wikitext_sources` does
not discover this file (it pins no revision), so nothing refetches it weekly: a re-read needs the video and
`--video`, run by a person.

THE TRANSCRIPTION IS A READ, NOT A HAND COPY. The video draws its boards in flat palette colours on a green
board, so `read_frame` (below) finds every board on a frame (a connected region that is not background, ten
columns wide) and samples each cell's centre against the palette (`PALETTE`): black `.`, the seven pieces, and
grey `G` (cells from before the setup, on a パフェ board). A cell that matches nothing is `?`; a `?` row at the
board's top or bottom edge (a marker under the board, a partial strip above it) is dropped, and a `?` anywhere
else is a failure, never a guess. `--video` re-reads every page's frame and compares the WHOLE board list.
Which board on a page is which (組み方 or パフェ, and which 組み方 a パフェ finishes) is the only hand input:
`PAGES[*].layout`, in the reader's order (top to bottom in bands of 100 px, then left to right).

WHAT IS DERIVED, AND CHECKED HERE. A 組み方 board drawing no `G` and no full row is a SETUP. The video never
draws the T in it; the T is the unique T placement (any orientation, resting on the stack or the floor, on
empty cells) that completes two rows — a T-spin Double, which every setup in the video fires (rule `t:` fails
on none or several). Each setup becomes a `setups` entry with
  * `t_cells`: the four T cells, as (row, col) from the top of the frame (`frame_rows` rows: the topmost row
    holding a stack or T cell, down to the floor);
  * `lines`: the rows the T completes (two);
  * `base`: the board by occupancy, the T's cells empty, leading empty rows dropped; its cells must be whole
    pieces (`pieces`, seven: the left-over piece and one bag);
  * `same_as`: the other setups with the identical base AND T cells. The video draws one SHAPE with
    different pieces in several cases (the left-over S or Z standing where an O stands); the corpus matcher
    reads occupancy, so it reports every name a shape carries;
  * `pcs`: the パフェ boards the page draws for it.
Rule `pc:` is the one cross-check the video supplies on itself: every パフェ board is all full rows, its
non-`G` cells whole pieces, and its `G` cells EXACTLY the residue of the board it finishes (the setup with its
T placed and the two rows cleared, bottom-aligned). So a mis-read cell in a 組み方 board, or a T derived in the
wrong place, fails against boards drawn separately. The 2ラインパフェ page is not a T-spin setup (a two-line
Perfect Clear, then a stack with a T in it): its boards are recorded (`clear`, `board`) and checked by rule
`pc:` the same way, and it makes no `setups` entry.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'dpc-setups.json'
W = 10
PIECES = set('IJLOSTZ')
LETTERS = PIECES | {'.', 'G'}
VIDEO = '1Wr8VbNfnIg'
WATCH = f'https://www.youtube.com/watch?v={VIDEO}'

#: the four T tetrominoes, as (row, col) offsets from their top-left
T_SHAPES = [frozenset(s) for s in (
    {(0, 0), (0, 1), (0, 2), (1, 1)},       # flat, nub down
    {(0, 1), (1, 0), (1, 1), (1, 2)},       # flat, nub up
    {(0, 0), (1, 0), (2, 0), (1, 1)},       # stood, nub right
    {(0, 1), (1, 1), (2, 1), (1, 0)},       # stood, nub left
)]

#: The catalogue pages: the frame read (seconds; the page's last second on screen, when every board is drawn),
#: the page's start (for the link), its title and label as the video writes them, and its layout: one entry per
#: board in the reader's order, ('setup' | 'clear' | 'board' | 'pc', index of the board a 'pc' finishes).
PAGES = [
    {'key': 'p01', 't': 645, 'start': 603, 'title': 'Oミノ残し：O>Z', 'label': 'くるまDPC',
     'layout': [('setup', None), ('pc', 0), ('pc', 0)]},
    {'key': 'p02', 't': 692, 'start': 649, 'title': 'Oミノ残し：O>S', 'label': 'くるまDPC',
     'layout': [('setup', None), ('pc', 0), ('pc', 0)]},
    {'key': 'p03', 't': 738, 'start': 696, 'title': 'Oミノ残し：S>O', 'label': 'JB_DPC',
     'layout': [('setup', None)] + [('pc', 0)] * 4},
    {'key': 'p04', 't': 785, 'start': 742, 'title': 'Oミノ残し：Z>O', 'label': 'JB_DPC',
     'layout': [('setup', None)] + [('pc', 0)] * 4},
    {'key': 'p05', 't': 831, 'start': 789, 'title': 'Oミノ残し：I,L,J,O', 'label': '2ラインパフェ',
     'layout': [('clear', None), ('pc', 2), ('board', None)]},
    {'key': 'p06', 't': 877, 'start': 835, 'title': 'Sミノ残し：O>S', 'label': 'くるまDPC',
     'layout': [('setup', None), ('pc', 0), ('pc', 0)]},
    {'key': 'p07', 't': 924, 'start': 881, 'title': 'Sミノ残し：S>O', 'label': 'トラックDPC',
     'layout': [('setup', None)] + [('pc', 0)] * 6},
    {'key': 'p08', 't': 970, 'start': 928, 'title': 'Zミノ残し：O>Z', 'label': 'くるまDPC',
     'layout': [('setup', None), ('pc', 0), ('pc', 0)]},
    {'key': 'p09', 't': 1017, 'start': 974, 'title': 'Zミノ残し：Z>O', 'label': 'トラックDPC',
     'layout': [('setup', None)] + [('pc', 0)] * 6},
    {'key': 'p10', 't': 1063, 'start': 1021, 'title': 'Oミノ残し：簡単Ver（この二つを覚えるだけ）', 'label': '',
     'layout': [('setup', None), ('pc', 0), ('pc', 0), ('setup', None)] + [('pc', 3)] * 5,
     # the page writes no name; the teaching part (519-569 s) builds these two from one fixed O: くるまDPC when O
     # comes before J, 「TSD DPC(Iずらし)」 when J comes first. A reading, recorded as one.
     'names': ['くるまDPC', 'TSD DPC(Iずらし)'], 'names_from': 519},
]

#: The source record, held here so the committed file cannot drift from it (`file` is filled by `--write`).
SOURCE = {
    'kind': 'youtube',
    'video': VIDEO,
    'url': WATCH,
    'title': '【テトリス初心者講座】超火力！TDパフェ後のDPCテンプレ解説',
    'channel': 'とんぼ_テトリス初心者講座 (@Tonbo_tetris)',
    'duration_s': 1067,
    'catalogue': 'the still pages from 603 s to the end, one per case: 組み方 and パフェ boards',
    'fetched': '2026-10-29, 720p MP4 through www.snapyt.app (yt-dlp is refused in this sandbox)',
    'terms': 'nothing of the video is committed or published: no frame, no clip; every page links the video at '
             'the page\'s time',
    'definition': {
        'quote': ['今回はTD系テンプレを打った後に続けられる', '強力なテンプレ', 'いわゆるDPCを解説するのだ', 'DPCは',
                  '3巡パフェ後テンプレや', '8段パフェ後テンプレとも呼ばれていて', '山岳積み二号などのTD系テンプレで',
                  'パフェが決まった後にさらに高確率で', 'Tスピンダブルとパーフェクトクリアが', '狙えるテンプレなのだ'],
        'from': 4, 'to': 34,
        'url': f'{WATCH}&t=4s',
    },
}
MEANS = ('The DPC setups とんぼ\'s video catalogues (its still pages from 603 s): per page the boards as read off '
         'the frame (組み方 setups and the パフェ boards finishing them), and per setup the board by occupancy with '
         'the unique T placement that completes two rows. A transcription of one video, read by a palette reader '
         'and cross-checked by the residue each パフェ board draws; not corpus data.')


class Bad(Exception):
    pass


# ------------------------------------------------------------------ reading a frame

#: the video's flat cell colours (RGB), measured on its frames
PALETTE = {'.': (0, 0, 0), 'I': (0, 150, 150), 'Z': (152, 0, 0), 'L': (150, 100, 0), 'J': (0, 0, 186),
           'O': (152, 152, 0), 'S': (0, 152, 0), 'T': (150, 0, 150), 'G': (150, 150, 150)}
#: frame rows the boards live in: below the page title, down to the chalk tray (the lowest boards end near 668)
BAND = (70, 686)
#: the channel's corner logo (x0, y0, x1, y1), left out of the board mask so it never joins a board's region; the
#: board cells under its corner are still sampled, and read as drawn (the logo sits beside them, not over them)
LOGO = (1110, 648, 1280, 720)


def _cls(p) -> str | None:
    best = min(PALETTE, key=lambda k: sum((a - b) ** 2 for a, b in zip(p, PALETTE[k])))
    if sum((a - b) ** 2 for a, b in zip(p, PALETTE[best])) ** .5 < 40:
        return best
    return '.' if max(p) < 60 else None


def _on_board(p) -> bool:
    r, g, b = p
    if r > 190 and g > 190 and b > 190:                       # white text and arrows
        return False
    return not (g > 95 and r < 70 and 35 < b < 120 and g - b > 25)  # the green chalkboard


def read_frame(image) -> list[list[str]]:
    """Every board on a frame (a PIL image), in reading order: top to bottom in bands of 100 px, then left to
    right. A board is a connected non-background region at least 8 px a column; its rows are sampled from the
    bottom up (a partial strip on top is dropped by rounding), each cell by a 3x3 vote round its centre."""
    im = image.convert('RGB')
    w, h = im.size
    px = im.load()
    mask = [[BAND[0] <= y < BAND[1] and not (LOGO[0] <= x < LOGO[2] and LOGO[1] <= y < LOGO[3])
             and _on_board(px[x, y]) for x in range(w)] for y in range(h)]
    seen = [[False] * w for _ in range(h)]
    found = []
    for y0 in range(0, h, 2):
        for x0 in range(0, w, 2):
            if not mask[y0][x0] or seen[y0][x0]:
                continue
            st, xs, ys = [(x0, y0)], [], []
            seen[y0][x0] = True
            while st:
                x, y = st.pop()
                xs.append(x)
                ys.append(y)
                for a, b in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= a < w and 0 <= b < h and mask[b][a] and not seen[b][a]:
                        seen[b][a] = True
                        st.append((a, b))
            if len(xs) < 4000:
                continue
            left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
            cw = (right - left + 1) / W
            if cw < 8:
                continue
            rows = []
            for i in range(int((bottom - top + 1) / cw + 0.35)):
                cy = bottom + 1 - (i + .5) * cw
                row = ''
                for c in range(W):
                    cx = left + (c + .5) * cw
                    votes: dict = {}
                    for ox in (-cw * .2, 0, cw * .2):
                        for oy in (-cw * .2, 0, cw * .2):
                            k = _cls(px[int(cx + ox), int(cy + oy)])
                            votes[k] = votes.get(k, 0) + 1
                    k = max(votes, key=votes.get)
                    row += k or '?'
                rows.append(row)
            found.append(((top // 100, left), rows[::-1]))
    found.sort(key=lambda f: f[0])
    out = []
    for _, rows in found:
        while rows and '?' in rows[-1]:
            rows.pop()
        while rows and '?' in rows[0]:
            rows.pop(0)
        out.append(rows)
    return out


def frame_at(video: Path, t: float, td: Path):
    from PIL import Image
    f = td / f'{t}.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', str(video), '-frames:v', '1', str(f)],
                   check=True)
    return Image.open(f)


# ------------------------------------------------------------------ deriving

def occ(rows: list[str]) -> list[str]:
    """Occupancy, leading empty rows dropped."""
    o = [''.join('.' if c == '.' else 'x' for c in r) for r in rows]
    while o and o[0] == '.' * W:
        o.pop(0)
    return o


def role_ok(role: str, rows: list[str]) -> str | None:
    cells = ''.join(rows)
    nonempty = [r for r in rows if r != '.' * W]
    full = [r for r in nonempty if '.' not in r]
    if role == 'pc':
        return None if 'G' in cells and nonempty and len(full) == len(nonempty) else 'a パフェ board must draw G and only full rows'
    if 'G' in cells:
        return f'a {role} board draws G'
    if role == 'clear':
        return None if nonempty and len(full) == len(nonempty) else 'a clear board must be full rows'
    if full:
        return f'a {role} board has a full row'
    return None


def tsd(rows: list[str]) -> list[tuple[int, int]]:
    """The unique T placement completing two rows on a board drawn without its T. Raises Bad otherwise."""
    h = len(rows)
    filled = lambda r, c: r >= h or (0 <= c < W and r >= 0 and rows[r][c] != '.')
    found = []
    for sh in T_SHAPES:
        for r0 in range(-2, h):
            for c0 in range(-1, W):
                cs = {(r0 + a, c0 + b) for a, b in sh}
                if any(r < 0 or r >= h or c < 0 or c >= W or rows[r][c] != '.' for r, c in cs):
                    continue
                if not any(filled(r + 1, c) and (r + 1, c) not in cs for r, c in cs):
                    continue                                   # not resting on anything
                full = [r for r in range(h) if all(rows[r][c] != '.' or (r, c) in cs for c in range(W))]
                if len(full) == 2:
                    found.append(sorted(cs))
    if len(found) != 1:
        raise Bad(f'{len(found)} T placements complete two rows: {found}')
    return found[0]


def residue(rows: list[str], t: list[tuple[int, int]] | None) -> list[str]:
    """Occupancy after placing T (if any) and clearing the full rows, leading empty rows dropped."""
    g = [list('.' if ch == '.' else 'x' for ch in r) for r in rows]
    for r, c in t or []:
        g[r][c] = 'x'
    return occ([''.join(r) for r in g if '.' in r])


def derive(pages: list[dict]) -> tuple[list[dict], list[dict]]:
    """(boards, setups) from the read pages ({key, title, label, layout, boards: [rows]}). Raises Bad."""
    boards, setups = [], []
    for pg in pages:
        if len(pg['boards']) != len(pg['layout']):
            raise Bad(f'layout: {pg["key"]}: {len(pg["boards"])} boards read, the layout names {len(pg["layout"])}')
        ts: dict[int, list] = {}
        for i, ((role, of), rows) in enumerate(zip(pg['layout'], pg['boards'])):
            bid = f'{pg["key"]}.{i:03d}'
            if any(len(r) != W or set(r) - LETTERS for r in rows):
                raise Bad(f'letters: {bid}: a ragged row or an unread cell')
            why = role_ok(role, rows)
            if why:
                raise Bad(f'role: {bid}: {why}')
            boards.append({'id': bid, 'page': pg['key'], 'role': role, 'of': None if of is None else f'{pg["key"]}.{of:03d}',
                           'rows': rows})
            if role == 'setup':
                try:
                    ts[i] = tsd(rows)
                except Bad as e:
                    raise Bad(f't: {bid}: {e}')
        for i, ((role, of), rows) in enumerate(zip(pg['layout'], pg['boards'])):
            if role != 'pc':
                continue
            bid = f'{pg["key"]}.{i:03d}'
            if of is None or not 0 <= of < len(pg['layout']) or pg['layout'][of][0] == 'pc':
                raise Bad(f'pc: {bid}: finishes no recorded board')
            want = residue(pg['boards'][of], ts.get(of))
            got = occ([''.join('x' if ch == 'G' else '.' for ch in r) for r in rows])
            if got != want:
                raise Bad(f'pc: {bid}: its G cells {got} are not the residue {want} of {pg["key"]}.{of:03d}')
            n = sum(ch in PIECES for r in rows for ch in r)
            if n % 4:
                raise Bad(f'pc: {bid}: {n} non-G cells, not whole pieces')
        for i, rows in enumerate(pg['boards']):
            odd = sorted(k for k in PIECES if sum(r.count(k) for r in rows) % 4)
            if odd:
                raise Bad(f'pieces: {pg["key"]}.{i:03d}: {odd} drawn in a count of cells no whole pieces make')
        setup_ix = [j for j, (ro, _) in enumerate(pg['layout']) if ro == 'setup']
        for i, t in ts.items():
            rows = pg['boards'][i]
            bid = f'{pg["key"]}.{i:03d}'
            top = min([r for r, row in enumerate(rows) if row != '.' * W] + [r for r, _ in t])
            frame = rows[top:]
            tc = [[r - top, c] for r, c in t]
            base = occ([''.join('.' if ch == '.' else 'x' for ch in row) for row in frame])
            n = sum(row.count('x') for row in base)
            if n % 4:
                raise Bad(f'base: {bid}: {n} cells, not whole pieces')
            name = pg['names'][setup_ix.index(i)] if 'names' in pg else pg['label']
            setups.append({'id': bid, 'page': pg['key'], 'heading': [name, pg['title']], 'base': base,
                           't_cells': tc, 'frame_rows': len(frame), 'lines': 2, 'pieces': n // 4,
                           'cleared_before': 0,
                           'pcs': [f'{pg["key"]}.{j:03d}' for j, (ro, of) in enumerate(pg['layout'])
                                   if ro == 'pc' and of == i]})
    key: dict = {}
    for s in setups:
        key.setdefault((tuple(s['base']), tuple(map(tuple, s['t_cells']))), []).append(s['id'])
    for s in setups:
        s['same_as'] = [x for x in key[(tuple(s['base']), tuple(map(tuple, s['t_cells'])))] if x != s['id']]
    return boards, setups


def pages_of(data: dict) -> list[dict]:
    """The read pages, back out of the committed file (the layout from `PAGES`, the rows from `boards`)."""
    out = []
    for p in PAGES:
        mine = [b for b in data['boards'] if b['page'] == p['key']]
        out.append({**p, 'boards': [b['rows'] for b in mine]})
    return out


# ------------------------------------------------------------------ checks

def offline_checks(data: dict) -> list[str]:
    """The committed file alone: the page records agree with `PAGES`, and every board's role, every setup and
    every residue re-derive from the recorded rows."""
    bad = []
    if [p['key'] for p in data['pages']] != [p['key'] for p in PAGES]:
        bad.append('pages: the recorded pages are not PAGES')
    for rec, p in zip(data['pages'], PAGES):
        for k in ('t', 'start', 'title', 'label', 'names', 'names_from'):
            if rec.get(k) != p.get(k):
                bad.append(f'pages: {p["key"]}.{k} is {rec.get(k)!r}, PAGES says {p.get(k)!r}')
        if rec.get('url') != f'{WATCH}&t={p["start"]}s':
            bad.append(f'pages: {p["key"]}.url does not link the video at the page')
    if {k: v for k, v in data['source'].items() if k != 'file'} != SOURCE:
        bad.append('source: the recorded source is not SOURCE')
    if data.get('means') != MEANS:
        bad.append('means: the recorded means is not MEANS')
    for k in ('sha256', 'bytes'):
        if k not in data['source'].get('file', {}):
            bad.append(f'source: the downloaded file has no {k}')
    for b in data['boards']:
        if not b['id'].startswith(b['page'] + '.'):
            bad.append(f'boards: {b["id"]} is not on page {b["page"]}')
    if bad:
        return bad
    try:
        boards, setups = derive(pages_of(data))
    except Bad as e:
        return [str(e)]
    if boards != data['boards']:
        bad.append(f'boards: re-derived roles differ ({[a["id"] for a, b in zip(boards, data["boards"]) if a != b][:3]})')
    if setups != data['setups']:
        bad.append('setups: re-derived from the recorded boards, they differ from the recorded setups')
    return bad


def video_checks(data: dict, video: Path) -> list[str]:
    """`--video`: the file hashed against the record, every page's frame re-read, every board compared."""
    bad = []
    raw = video.read_bytes()
    if hashlib.sha256(raw).hexdigest() != data['source']['file']['sha256'] or len(raw) != data['source']['file']['bytes']:
        bad.append(f'hash: {video.name} is not the recorded download (sha256 {hashlib.sha256(raw).hexdigest()})')
    with tempfile.TemporaryDirectory() as td:
        for p in PAGES:
            got = read_frame(frame_at(video, p['t'], Path(td)))
            want = [b['rows'] for b in data['boards'] if b['page'] == p['key']]
            if got != want:
                bad.append(f'read: {p["key"]} at {p["t"]} s reads {len(got)} boards that differ from the recorded '
                           f'{len(want)} (first: {[i for i, (a, b) in enumerate(zip(got, want)) if a != b][:3]})')
    return bad


def write(video: Path) -> int:
    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    raw = video.read_bytes()
    pages = []
    with tempfile.TemporaryDirectory() as td:
        for p in PAGES:
            pages.append({**p, 'boards': read_frame(frame_at(video, p['t'], Path(td)))})
    try:
        boards, setups = derive(pages)
    except Bad as e:
        print(f'FAIL {e}')
        return 1
    src = {**SOURCE, 'file': {'format': 'MP4, 1280x720', 'sha256': hashlib.sha256(raw).hexdigest(),
                              'bytes': len(raw)}}
    data = {
        'schema': 'dpc-setups/2',
        'means': MEANS,
        'source': src,
        'pages': [{'key': p['key'], 't': p['t'], 'start': p['start'], 'title': p['title'], 'label': p['label'],
                   **({'names': p['names'], 'names_from': p['names_from']} if 'names' in p else {}),
                   'url': f'{WATCH}&t={p["start"]}s'} for p in PAGES],
        'boards': boards,
        'setups': setups,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n')
    print(f'wrote {OUT.relative_to(HERE.parent.parent)}: {len(boards)} boards, {len(setups)} setups')
    return 0


def report(bad: list[str], what: str) -> int:
    for x in bad:
        print(f'FAIL {x}')
    if not bad:
        print(f'ok  {what}')
    return 1 if bad else 0


class _Frame:
    """A pixel grid with the three things `read_frame` asks of a PIL image (`convert`, `size`, `load`), so the
    reader's selftest needs no Pillow and runs in CI's docs job."""
    def __init__(self, w: int, h: int, fill):
        self.size, self._px = (w, h), [[fill] * w for _ in range(h)]

    def convert(self, mode):
        return self

    def load(self):
        px = self._px

        class _Access:
            def __getitem__(self, xy):
                return px[xy[1]][xy[0]]
        return _Access()

    def rect(self, x0, y0, x1, y1, fill, outline):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self._px[y][x] = outline if x in (x0, x1) or y in (y0, y1) else fill


def render_frame(boards: list[list[str]]):
    """A synthetic frame drawing `boards` the way the video does (flat cells, dark grid, green board), three
    to a 260 px band, for the reader's selftest."""
    im = _Frame(1280, 720, (8, 122, 67))
    for k, rows in enumerate(boards):
        cw, x0 = 30, 60 + 420 * (k % 3)
        y0 = 100 + 260 * (k // 3)
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                im.rect(x0 + c * cw, y0 + r * cw, x0 + (c + 1) * cw - 1, y0 + (r + 1) * cw - 1, PALETTE[ch], (30, 30, 30))
    return im


def selftest() -> int:
    data = json.loads(OUT.read_text())
    survived = killed = 0

    def expect(label, bad, want):
        nonlocal survived, killed
        if bool(bad) == want:
            killed += want
            print(f'  {"killed" if want else "passed"}: {label}')
        else:
            survived += 1
            print(f'  {"SURVIVED" if want else "FAILED control"}: {label} {bad[:2]}', file=sys.stderr)

    expect('the committed file (control)', offline_checks(data), False)
    s0 = data['setups'][0]

    def with_rows(bid, fn):
        d = copy.deepcopy(data)
        b = next(b for b in d['boards'] if b['id'] == bid)
        b['rows'] = fn(b['rows'])
        return d

    def set_cell(rows, r, c, ch):
        return [row[:c] + ch + row[c + 1:] if i == r else row for i, row in enumerate(rows)]
    b0 = next(b for b in data['boards'] if b['id'] == s0['id'])
    top = len(b0['rows']) - s0['frame_rows']
    tr, tc = s0['t_cells'][0]
    expect('a T cell filled in the setup (no T-spin Double left)',
           offline_checks(with_rows(s0['id'], lambda rows: set_cell(rows, top + tr, tc, 'O'))), True)
    br, bc = next((i, j) for i, row in enumerate(b0['rows']) for j, ch in enumerate(row)
                  if ch in PIECES and (i - top, j) not in map(tuple, s0['t_cells']) and i < len(b0['rows']) - 1
                  and b0['rows'][i + 1][j] != '.')
    expect('a setup cell recoloured to another piece (the piece counts are not whole pieces)',
           offline_checks(with_rows(s0['id'], lambda rows: set_cell(rows, br, bc, 'T' if rows[br][bc] != 'T' else 'I'))),
           True)
    expect('a setup cell emptied (a パフェ board no longer finishes it)',
           offline_checks(with_rows(s0['id'], lambda rows: set_cell(rows, br, bc, '.'))), True)
    pc = s0['pcs'][0]
    pb = next(b for b in data['boards'] if b['id'] == pc)
    gr, gc = next((i, j) for i, row in enumerate(pb['rows']) for j, ch in enumerate(row) if ch == 'G')
    pr, pcol = next((i, j) for i, row in enumerate(pb['rows']) for j, ch in enumerate(row) if ch in PIECES)
    expect('a G cell and a piece cell swapped on a パフェ board',
           offline_checks(with_rows(pc, lambda rows: set_cell(set_cell(rows, gr, gc, rows[pr][pcol]), pr, pcol, 'G'))), True)
    d = copy.deepcopy(data)
    d['setups'][0]['t_cells'][0][1] += 1
    expect('a recorded T cell edited', offline_checks(d), True)
    d = copy.deepcopy(data)
    d['setups'][0]['same_as'] = [] if d['setups'][0]['same_as'] else ['p99.000']
    expect('a recorded same_as group edited', offline_checks(d), True)
    d = copy.deepcopy(data)
    d['boards'][1]['role'] = 'setup'
    expect('a board role edited', offline_checks(d), True)
    d = copy.deepcopy(data)
    d['pages'][0]['url'] = WATCH
    expect('a page linking the video without its time', offline_checks(d), True)
    d = copy.deepcopy(data)
    del d['source']['file']['sha256']
    expect('the download with no sha256', offline_checks(d), True)
    d = copy.deepcopy(data)
    d['boards'] = [b for b in d['boards'] if b['id'] != pc]
    expect('a パフェ board dropped (the layout no longer fits)', offline_checks(d), True)
    # the reader, on a synthetic frame drawn the video's way
    page = [b['rows'] for b in data['boards'] if b['page'] == s0['page']][:3]
    expect('a synthetic frame reads back to its boards (control)', [] if read_frame(render_frame(page)) == page else ['differs'],
           False)
    planted = [list(rows) for rows in page]
    planted[0] = set_cell(planted[0], br, bc, '.')
    expect('...and a cell blanked in it is read as blanked',
           [] if read_frame(render_frame(planted)) == page else ['differs'], True)
    print(f'selftest: {killed} killed, {survived} survived')
    return 1 if survived else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or '').split('\n')[0])
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--video', type=Path)
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.write:
        if not a.video:
            print('FAIL --write needs --video')
            return 1
        return write(a.video)
    data = json.loads(OUT.read_text())
    if a.video:
        return report(video_checks(data, a.video), f'{len(PAGES)} pages re-read off the video to the '
                      f'{len(data["boards"])} recorded boards')
    return report(offline_checks(data), f'{len(data["boards"])} boards, {len(data["setups"])} setups re-derive')


if __name__ == '__main__':
    raise SystemExit(main())

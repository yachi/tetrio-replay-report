"""Gate the boards read off YouTube videos (`video-examples.json`): the 中盤 and DPC examples they show.

    python3 -m pipeline.openers.check_video_examples              # verify the committed file (offline, CI)
    python3 -m pipeline.openers.check_video_examples --selftest   # prove the verifier has teeth

THE SOURCES (`sources`) are YouTube videos, each naming the board sides it holds (`players`; a side key
belongs to one video, so a board's `side` says which video it is from):
  * 「vs kazuさん 15先×2 Part1【ぷよぷよテトリス２】」 (`Pjn05duM_gQ`), a Puyo Puyo Tetris 2 match, sides L and R:
    two boards side by side, both players dealt the same pieces (yachi, 2026-11-05);
  * 「【ゆっくり解説】空中で組めるTスピンテンプレ＆組み方紹介【テトリス講座】」 (`cFcBAIvuQjU`), a T-spin tutorial,
    side Y: one board, clips cut together, some shown twice — a repeated board is filed once (yachi, 2026-11-06).
None of it is corpus data. Nobody in the corpus played these games, nothing here enters a count, a claim or
a report, and the file says `report_eligible: false`. The site shows them on each technique page and the
DPC page in a section of their own, beside the source drawings and never mixed into them: the windows, the
whole-shape rule and every corpus figure are unchanged by this file.

NOTHING OF A VIDEO IS COMMITTED (no frame, no clip). Each was downloaded through www.snapyt.app (yt-dlp is
refused here), so a source's `file` sha256 is ours alone. The boards were read off the frames by scratch
readers (palette sampling; each line clear flashes its rows white, so a board is read on the last frame
before the flash) that are NOT committed: nothing re-reads them, which is an open item. A cell the reader
matched to no colour (a sparkle, a flash, an effect over the garbage) is `?`, and every verdict below is
computed TWICE, with every `?` read empty and read filled, and must not change.

WHAT IS CHECKED, per board (`boards`): 20 rows of 10 (`.` empty, `G` garbage, the seven pieces, `?`
unread), with any cell corrected by hand listed in `hand_reads` (what was read, what it is, and why); `t_cells` is a T, drawn `T`; the rows full on the board are exactly `cleared` and the T has a cell
in one of them, so the T made the clear (`lines` = how many).

Per technique example (`technique_examples`): the page's window (`technique_transcription.window_fires`,
the corpus predicate's Python twin) fires at that T in the recorded hand; and the build reasons are
recomputed from the board. The video gives no piece ownership, so the reasons are an APPROXIMATION of the
corpus `qualify` rules, said so on every page:
  * `fragment`: a key cell (`key_cells`, the cells technique-qualify.ts names for the variant, placed on the
    board; the bun test `video-examples.test.ts` re-derives them from that file) that no whole piece covers:
    the key cells of each same-colour connected region must be covered by pairwise disjoint placements of
    THAT letter's tetromino inside the region, and the region's other cells are remnants a clear cut
    (`whole_cover`). Until 2026-11-07 the rule was 「the region is a multiple of four cells」, which failed a
    whole piece touching a one- or two-cell remnant of its own colour and passed four cells no piece of
    that letter fits (yachi on the めぞん boards, checked by an independent reading);
  * `garbage_in_shape`: a key cell is garbage;
  * `z_not_one_piece` (階段のドネイト): the stood Z's four cells are not one same-colour region;
  * `dpc`: a Perfect Clear by the same player within `pc_window_s` seconds either side of the T (the
    corpus rule is 14 locks; a time is all a video gives);
  * `kaidan_window` (社畜トレイン): the 階段のドネイト window fires at the same T, in either hand, AND its stood
    Z passes the one-piece test there. The window alone fires on every 社畜トレイン built over a hole (it reads
    only the cell under the second nub, which the 社畜 window does not); the two piece tests cannot both pass,
    since the cell over the Z is the L/J hook for a 社畜 and the Z's own colour for a 階段.
A `verdict` of `qualifies` means no reason. Whether the whole drawn shape stands (`whole_board`) is the TS
rule (`technique-wholeshape.ts`) and is checked by the bun test, not here.

Per DPC example (`dpc_examples`): `pc_t` is one of the player's Perfect Clears (`pc_times`, each checked
by eye on the frames for the PERFECT CLEAR banner and an empty board), the board is the first T-spin after
it and before the next, and its catalogue match is recomputed against `dpc-setups.json` the way
`dpc-facts.ts` does (complete garbage rows stripped from the bottom, occupancy with the T's cells, as drawn
and mirrored). `kind`: `matched` (a catalogue setup), `near` (a setup once `ignore_cells` are taken away,
named in `note`), `new` (no setup, within `dpc_gap_s` of the Perfect Clear), `late` (no setup, later).
`pc_after` says whether the same player cleared the board again within 4 s.
"""
from __future__ import annotations

import argparse
import copy
import importlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILE = os.path.join(REPO, "pipeline", "openers", "video-examples.json")
DPC_SETUPS = os.path.join(REPO, "pipeline", "openers", "dpc-setups.json")
H, W = 20, 10
PIECES = set("IJLOSZT")
CELLS = PIECES | set(".G?")
T_SHAPES = None  # set of normalised T cell sets, built lazily


def _t_shapes():
    global T_SHAPES
    if T_SHAPES is None:
        base = [(0, 0), (0, 1), (0, 2), (1, 1)]
        out, cur = set(), base
        for _ in range(4):
            cur = [(c, -r) for r, c in cur]
            r0, c0 = min(r for r, _ in cur), min(c for _, c in cur)
            out.add(frozenset((r - r0, c - c0) for r, c in cur))
        T_SHAPES = out
    return T_SHAPES


def is_t(cells):
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells) in _t_shapes()


def load(path=FILE):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def board_of(doc, bid):
    return next(b for b in doc["boards"] if b["id"] == bid)


def regions(rows):
    """Same-colour 4-connected regions of piece cells: (r, c) -> size."""
    seen, size = {}, {}
    for r in range(H):
        for c in range(W):
            ch = rows[r][c]
            if ch not in PIECES or (r, c) in seen:
                continue
            st, grp = [(r, c)], []
            seen[(r, c)] = grp
            while st:
                x = st.pop()
                grp.append(x)
                for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    y = (x[0] + dr, x[1] + dc)
                    if 0 <= y[0] < H and 0 <= y[1] < W and y not in seen and rows[y[0]][y[1]] == ch:
                        seen[y] = grp
                        st.append(y)
    return seen


_BASE = {"I": [(0, 0), (0, 1), (0, 2), (0, 3)], "O": [(0, 0), (0, 1), (1, 0), (1, 1)],
         "T": [(0, 1), (1, 0), (1, 1), (1, 2)], "S": [(0, 1), (0, 2), (1, 0), (1, 1)],
         "Z": [(0, 0), (0, 1), (1, 1), (1, 2)], "J": [(0, 0), (1, 0), (1, 1), (1, 2)],
         "L": [(0, 2), (1, 0), (1, 1), (1, 2)]}


def _rotations(cells):
    out, cur = set(), cells
    for _ in range(4):
        mr, mc = min(r for r, _ in cur), min(c for _, c in cur)
        out.add(tuple(sorted((r - mr, c - mc) for r, c in cur)))
        cur = [(c, -r) for r, c in cur]
    return out


SHAPES = {k: _rotations(v) for k, v in _BASE.items()}


def placements(region, letter, cell):
    """Every placement of `letter`'s tetromino lying inside `region` and covering `cell`."""
    out = []
    for s in SHAPES[letter]:
        for ar, ac in s:
            p = frozenset((cell[0] - ar + dr, cell[1] - ac + dc) for dr, dc in s)
            if p <= region and p not in out:
                out.append(p)
    return out


def whole_cover(rows, region, keys):
    """True iff the key cells of one same-colour region are covered by pairwise disjoint placements of that
    colour's tetromino inside the region (an exact cover of the keys, the rest of the region left over)."""
    letter = rows[next(iter(region))[0]][next(iter(region))[1]]

    def go(todo, used):
        if not todo:
            return True
        k = todo[0]
        if k in used:
            return go(todo[1:], used)
        return any(go(todo[1:], used | p) for p in placements(region, letter, k) if not (p & used))
    return go(sorted(keys), frozenset())


def _low(lock):
    return max(lock)


def kaidan_z_offsets(doc=None):
    """The stood Z of 階段のドネイト as offsets (dr, dc) from the T's lowest cell, as drawn. Read off the file's
    own 階段 examples, whose `one_piece` groups the bun test ties to technique-qualify.ts; every one must
    give the same offsets, so this is that module's cells, not a second copy."""
    doc = doc or load()
    seen = set()
    for ex in doc["technique_examples"]:
        if ex["page"] != "kaidan":
            continue
        b = board_of(doc, ex["board"])
        lr, lc = _low({tuple(x) for x in b["t_cells"]})
        sg = -1 if ex["mirrored"] else 1
        g = next(g for g in ex["one_piece"] if g["name"] == "z")
        seen.add(tuple(sorted((r - lr, sg * (c - lc)) for r, c in g["cells"])))
    assert len(seen) == 1, f"the 階段 examples disagree on the stood Z: {seen}"
    return next(iter(seen))


_KZ = []


def kaidan_z_whole(rows, lock, mirrored):
    """The 階段 stood Z's four cells, placed at this T in this hand, are one whole Z (or S, mirrored)."""
    if not _KZ:
        _KZ.append(kaidan_z_offsets())
    lr, lc = _low(lock)
    sg = -1 if mirrored else 1
    cells = frozenset((lr + dr, lc + sg * dc) for dr, dc in _KZ[0])
    if any(not (0 <= r < H and 0 <= c < W) for r, c in cells):
        return False
    letters = {rows[r][c] for r, c in cells}
    return len(letters) == 1 and letters <= {"Z", "S"} and any(cells == p for p in placements(cells, letters.pop(), min(cells)))


def filled_fn(rows, lock, unread_filled):
    def f(R, C):
        if (R, C) in lock:
            return False
        ch = rows[R][C]
        return ch not in ".?" or (ch == "?" and unread_filled)
    return f


def board_problems(b):
    bad, rows = [], b["rows"]
    if len(rows) != H or any(len(r) != W or set(r) - CELLS for r in rows):
        return [f"{b['id']}: not 20 rows of 10 known cells"]
    lock = {tuple(x) for x in b["t_cells"]}
    if len(lock) != 4 or not is_t(lock):
        bad.append(f"{b['id']}: t_cells is not a T")
    elif any(rows[r][c] != "T" for r, c in lock):
        bad.append(f"{b['id']}: a t_cell is not drawn T")
    for unread in (False, True):
        full = [r for r in range(H) if all(rows[r][c] not in ".?" or (rows[r][c] == "?" and unread) for c in range(W))]
        if full != sorted(b["cleared"]):
            bad.append(f"{b['id']}: the full rows {full} are not `cleared` {b['cleared']} (unread read "
                       f"{'filled' if unread else 'empty'})")
    for h in b.get("hand_reads", []):
        r, c = h["cell"]
        if rows[r][c] != h["as"] or h["as"] == h["read"] or not h.get("why"):
            bad.append(f"{b['id']}: hand read at {h['cell']} is not applied, or has no reason")
    if b["lines"] != len(b["cleared"]) or not any(r in b["cleared"] for r, _ in lock):
        bad.append(f"{b['id']}: the T did not make a {b['lines']}-line clear")
    return bad


def _technique(key):
    mod = importlib.import_module(f"pipeline.openers.extract_{key}_shapes")
    with open(os.path.join(REPO, "pipeline", "openers", f"{key}-technique.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    return mod.SPEC, data


def fires(key, variant, rows, lock, mirrored, unread):
    from pipeline.openers import technique_transcription as TT
    spec, data = _technique(key)
    var = next(v for v in data["variants"] if v["id"] == variant)
    return TT.window_fires(data, var, spec, rows, lock, mirrored, filled_fn(rows, lock, unread))


def near_pc(doc, side, t):
    return [p for p in doc["pc_times"].get(side, []) if abs(t - p) < doc["pc_window_s"]]


def technique_reasons(doc, ex, b, unread):
    rows, lock = b["rows"], {tuple(x) for x in b["t_cells"]}
    reg = regions(rows)
    out, keys = [], {}
    for r, c in ex["key_cells"]:
        ch = rows[r][c]
        if ch == "G":
            out.append("garbage_in_shape")
        elif ch in ".?" or (r, c) in lock:
            out.append("shape_cell_empty")
        else:
            keys.setdefault(id(reg[(r, c)]), (reg[(r, c)], set()))[1].add((r, c))
    if any(not whole_cover(rows, frozenset(g) - lock, k) for g, k in keys.values()):
        out.append("fragment")
    for g in ex.get("one_piece", []):
        if len({id(reg.get(tuple(x))) for x in g["cells"]}) != 1 or any(tuple(x) not in reg for x in g["cells"]):
            out.append(f"{g['name']}_not_one_piece")
    if near_pc(doc, b["side"], b["t"]):
        out.append("dpc")
    if ex["page"] == "shachikutrain" and any(
            fires("kaidan", "kaidan", rows, lock, m, unread) is True and kaidan_z_whole(rows, lock, m)
            for m in (False, True)):
        out.append("kaidan_window")
    return sorted(set(out))


def strip_garbage(rows):
    n = H
    while n > 0 and "G" in rows[n - 1]:
        n -= 1
    return n


def dpc_setups(b, ignore=()):
    """The catalogue setups the board before the T is (dpc-facts.ts's comparison, garbage stripped)."""
    with open(DPC_SETUPS, encoding="utf-8") as fh:
        st = json.load(fh)["setups"]
    lock = {tuple(x) for x in b["t_cells"]}
    ign = {tuple(x) for x in ignore}
    occ = [[(b["rows"][r][c] not in ".?") and (r, c) not in lock and (r, c) not in ign for c in range(W)]
           for r in range(H)]
    bot = strip_garbage(b["rows"])
    out = []
    for s in st:
        for mi in (False, True):
            base = [r[::-1] for r in s["base"]] if mi else s["base"]
            tc = {(r, W - 1 - c if mi else c) for r, c in s["t_cells"]}
            k = len(base)
            off = bot - k
            if off < 0:
                continue
            ok = all(occ[off + r][c] == (base[r][c] != ".") for r in range(k) for c in range(W))
            # the frame starts at the setup's topmost row, so the T's cells sit `frame_rows - k` above it
            sh = s["frame_rows"] - k
            if ok and {(r - off + sh, c) for r, c in lock} == tc:
                out.append([s["id"], mi])
    return out


def dpc_fields(doc, ex, b):
    ts = doc["pc_times"][b["side"]]
    later = [p for p in ts if p > ex["pc_t"]]
    nxt = later[0] if later else None
    setups = dpc_setups(b)
    near = dpc_setups(b, ex.get("ignore_cells", [])) if ex.get("ignore_cells") else []
    gap = round(b["t"] - ex["pc_t"], 2)
    if setups:
        kind = "matched"
    elif near:
        kind = "near"
    elif gap <= doc["dpc_gap_s"]:
        kind = "new"
    else:
        kind = "late"
    return {"next_pc": nxt, "setups": setups, "near_setups": near, "gap_s": gap, "kind": kind,
            "pc_after": any(0 < p - b["t"] < 4 for p in ts), "garbage_rows": H - strip_garbage(b["rows"])}


def verify(doc):
    bad = []
    if doc.get("schema") != "video-examples/2" or doc.get("report_eligible") is not False:
        bad.append("schema must be video-examples/2 and report_eligible false")
    owner = {}
    for src in doc.get("sources", []):
        for side in src.get("players", {}):
            if side in owner:
                bad.append(f"side {side} named by two sources")
            owner[side] = src.get("video")
        if not src.get("video") or not src.get("title"):
            bad.append(f"source {src.get('key')}: no video id or title")
    if set(doc["pc_times"]) != set(owner):
        bad.append(f"pc_times sides {sorted(doc['pc_times'])} are not the sources' sides {sorted(owner)}")
    ids = [b["id"] for b in doc["boards"]]
    if len(set(ids)) != len(ids):
        bad.append("a board id twice")
    for b in doc["boards"]:
        bad += board_problems(b)
        if b["side"] not in owner:
            bad.append(f"{b['id']}: side {b['side']} belongs to no source")
        if b["id"] != f"{b['side']}{b['t']}":
            bad.append(f"{b['id']}: the id is not side+time")
    used = set()
    for ex in doc["technique_examples"]:
        b = board_of(doc, ex["board"])
        used.add(b["id"])
        lock = {tuple(x) for x in b["t_cells"]}
        tag = f"{ex['board']} {ex['page']}/{ex['variant']}"
        for unread in (False, True):
            if fires(ex["page"], ex["variant"], b["rows"], lock, ex["mirrored"], unread) is not True:
                bad.append(f"{tag}: the window does not fire in the recorded hand")
            got = technique_reasons(doc, ex, b, unread)
            if got != sorted(ex["reasons"]):
                bad.append(f"{tag}: reasons {got} recomputed, {ex['reasons']} recorded")
        if (ex["verdict"] == "qualifies") != (not ex["reasons"]) or ex["verdict"] not in ("qualifies", "rejected"):
            bad.append(f"{tag}: the verdict does not follow from the reasons")
    for ex in doc["dpc_examples"]:
        b = board_of(doc, ex["board"])
        used.add(b["id"])
        if ex["pc_t"] not in doc["pc_times"][b["side"]]:
            bad.append(f"{ex['board']}: pc_t is not one of the player's Perfect Clears")
            continue
        f = dpc_fields(doc, ex, b)
        if not (ex["pc_t"] < b["t"] and (f["next_pc"] is None or b["t"] < f["next_pc"])):
            bad.append(f"{ex['board']}: the T is not between its Perfect Clear and the next")
        for k, v in f.items():
            if k != "next_pc" and ex.get(k) != v:
                bad.append(f"{ex['board']}: {k} {v} recomputed, {ex.get(k)} recorded")
        if ex["kind"] == "near" and not ex.get("note"):
            bad.append(f"{ex['board']}: a near match without its note")
    # the first T-spin after each Perfect Clear: no earlier board of that player sits between them
    for ex in doc["dpc_examples"]:
        b = board_of(doc, ex["board"])
        for o in doc["boards"]:
            if o["side"] == b["side"] and ex["pc_t"] < o["t"] < b["t"] and o["id"] in used:
                bad.append(f"{ex['board']}: {o['id']} is a T-spin between its Perfect Clear and it")
    if set(ids) - used:
        bad.append(f"boards no example uses: {sorted(set(ids) - used)}")
    return bad


def selftest():
    doc = load()
    fails = []

    def expect(label, mutate):
        d = copy.deepcopy(doc)
        mutate(d)
        caught = bool(verify(d))
        print(f"  {'caught' if caught else 'SURVIVED'}: {label}")
        if not caught:
            fails.append(label)

    if verify(doc):
        print("  the committed file fails its own check")
        return 1
    print("  control: the committed file passes")

    def rule(label, ok):
        print(f"  {'caught' if ok else 'SURVIVED'}: {label}")
        if not ok:
            fails.append(label)
    blank = ["." * W] * H
    def grid(cells, ch):
        g = [list(r) for r in blank]
        for r, c in cells:
            g[r][c] = ch
        return ["".join(r) for r in g]
    s_rem = [(18, 6), (18, 7), (19, 5), (19, 6), (19, 4)]
    rule("an S beside a one-cell S remnant read as a fragment",
         whole_cover(grid(s_rem, "S"), frozenset(s_rem), {(18, 6), (19, 5)}))
    rule("the remnant itself read as whole",
         not whole_cover(grid(s_rem, "S"), frozenset(s_rem), {(19, 4)}))
    bar = [(7, 0), (7, 1), (7, 2), (7, 3)]
    rule("four L cells in a bar read as an L", not whole_cover(grid(bar, "L"), frozenset(bar), {(7, 0)}))
    two = [(5, 0), (5, 1), (6, 0), (6, 1), (7, 0), (7, 1), (8, 0), (8, 1)]
    rule("two key cells of one O sharing one placement read as two pieces",
         whole_cover(grid(two, "O"), frozenset(two), {(5, 0), (8, 1)})
         and not whole_cover(grid(two[:6], "O"), frozenset(two[:6]), {(5, 0), (7, 1)}))
    sh = next(e for e in doc["technique_examples"] if e["board"] == "M44.8" and e["page"] == "shachikutrain")
    rule("a 社畜 whose 階段 Z is not one piece rejected as kaidan_window",
         "kaidan_window" not in technique_reasons(doc, sh, board_of(doc, sh["board"]), False))
    kd = next(e for e in doc["technique_examples"] if e["page"] == "shachikutrain" and "kaidan_window" in e["reasons"])
    rule("a 社畜 whose 階段 Z IS one piece let through",
         "kaidan_window" in technique_reasons(doc, kd, board_of(doc, kd["board"]), False))
    q = next(e for e in doc["technique_examples"] if e["verdict"] == "qualifies")
    r = next(e for e in doc["technique_examples"] if "fragment" in e["reasons"])
    dm = next(e for e in doc["dpc_examples"] if e["kind"] == "matched")
    dn = next(e for e in doc["dpc_examples"] if e["kind"] == "new")

    def setcell(d, bid, r, c, ch):
        b = board_of(d, bid)
        b["rows"][r] = b["rows"][r][:c] + ch + b["rows"][r][c + 1:]

    expect("a qualifying example's key cell read as garbage",
           lambda d: setcell(d, q["board"], *q["key_cells"][0], "G"))
    expect("a fragment's reason dropped",
           lambda d: next(e for e in d["technique_examples"] if e is not None and e["board"] == r["board"]
                          and e["page"] == r["page"]).update(reasons=[x for x in r["reasons"] if x != "fragment"],
                                                              verdict="qualifies" if r["reasons"] == ["fragment"] else "rejected"))
    expect("an example read in the other hand",
           lambda d: next(e for e in d["technique_examples"] if e["board"] == q["board"]
                          and e["page"] == q["page"]).update(mirrored=not q["mirrored"]))
    expect("an example filed under a page whose window does not fire",
           lambda d: next(e for e in d["technique_examples"] if e["board"] == q["board"]
                          and e["page"] == q["page"]).update(page="imperialcross" if q["page"] != "imperialcross" else "stsd",
                                                             variant="imperialcross" if q["page"] != "imperialcross" else "stsd"))
    expect("a T moved one column", lambda d: board_of(d, q["board"]).update(
        t_cells=[[a, b + 1] for a, b in board_of(doc, q["board"])["t_cells"]]))
    expect("a cleared row emptied", lambda d: setcell(d, q["board"], board_of(doc, q["board"])["cleared"][0], 0, "."))
    expect("a Perfect Clear deleted", lambda d: d["pc_times"][board_of(doc, dm["board"])["side"]].remove(dm["pc_t"]))
    expect("a Perfect Clear moved next to a qualifying T",
           lambda d: d["pc_times"][board_of(doc, q["board"])["side"]].append(board_of(doc, q["board"])["t"] + 1))
    expect("a matched DPC's setup list emptied",
           lambda d: next(e for e in d["dpc_examples"] if e["board"] == dm["board"]).update(setups=[], kind="new"))
    expect("a new DPC filed as matched",
           lambda d: next(e for e in d["dpc_examples"] if e["board"] == dn["board"]).update(kind="matched"))
    expect("a DPC base cell flipped", lambda d: setcell(
        d, dm["board"], strip_garbage(board_of(doc, dm["board"])["rows"]) - 1,
        next(c for c in range(W) if board_of(doc, dm["board"])["rows"][strip_garbage(board_of(doc, dm["board"])["rows"]) - 1][c] == "."),
        "O"))
    expect("an unread cell inside a window read as a stack cell",
           lambda d: setcell(d, q["board"], *_window_empty_cell(doc, q), "?"))
    expect("report_eligible flipped", lambda d: d.update(report_eligible=True))
    def unowned(d):
        b = board_of(d, q["board"])
        new = f"Q{b['t']}"
        for e in d["technique_examples"] + d["dpc_examples"]:
            if e["board"] == b["id"]:
                e["board"] = new
        b.update(side="Q", id=new)
    expect("a board on a side no source names", unowned)
    expect("a source's side dropped", lambda d: d["sources"][-1]["players"].clear())
    expect("a board no example uses", lambda d: d["boards"].append(dict(board_of(doc, q["board"]), id="L9999.0", t=9999.0)))
    print(f"{len(fails)} survivor(s)")
    return 1 if fails else 0


def _window_empty_cell(doc, ex):
    """A cell the example's window needs EMPTY (so reading a `?` there as filled must break the fire)."""
    from pipeline.openers import technique_transcription as TT
    spec, data = _technique(ex["page"])
    var = next(v for v in data["variants"] if v["id"] == ex["variant"])
    b = board_of(doc, ex["board"])
    lock = {tuple(x) for x in b["t_cells"]}
    fm = TT.frame_map(data, var, spec, lock, ex["mirrored"])
    Wc = TT.window_cells(data, var, spec, False)
    for (r, c), v in Wc.items():
        if v not in ("T", "#"):
            R, C = fm(r, c)
            if (R, C) not in lock:
                return R, C
    raise AssertionError("no empty window cell")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    doc = load()
    bad = verify(doc)
    for x in bad:
        print("FAIL", x)
    if not bad:
        n_t = len(doc["technique_examples"])
        n_q = sum(e["verdict"] == "qualifies" for e in doc["technique_examples"])
        print(f"ok: {len(doc['boards'])} boards, {n_t} technique examples ({n_q} qualify), "
              f"{len(doc['dpc_examples'])} DPC examples")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

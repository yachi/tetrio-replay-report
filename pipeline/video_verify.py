"""影片時間對分數 — check a night's video.json against the VOD's frames.

    python3 -m pipeline.video_verify sessions/<date> --video <mp4>
    python3 -m pipeline.video_verify --selftest

`pipeline/video_snap.py` snaps every round to a GO inside a 2 s window of its
walk-back prediction. `max_snap_s` is the largest |snap − prediction|. That is
not enough: extra GOs are common (the 2026-11-26 VOD has 82 GOs for 75 replay
rounds — some mid-round false jumps, some between matches), and a unique nearest
GO can still be the wrong round if the real start sits just outside the window.
The linked timestamp is only right if the in-game FT7 score at `play_start_s`
equals that round's pre-round running score in facts.json, the boards are a
start of a round, not mid-play, AND the opening piece sequence on screen
(current + NEXT queue) matches that round's replay `seq`. Win counters
alone can agree while the VOD is still a different round with the same
score, or while the HTML replay's left/right seating is swapped vs the
VOD (2026-11-26 m7r10: bag and 4-5 score matched, but the report drew
yachi on the left and the VOD has pinglamb there).

In-round moment links (report 「睇第一次（mXrY，落 T 之前）」, title
「喺直播影片睇呢一刻」) use the same file: `t = floor(play_start_s + frames/60
- link_lead_s)`, where `frames` is the replay's cumulative 60 fps count from
GO to the T lock (`video_links.moment_url`). Those too must be checked: at the
linked second the FT7 win counters must match the labeled round (0-0 is r1 of
that match; a-b is round a+b+1). A small `max_snap_s` does not do this.
yachi: 「喺直播影片睇呢一刻 link 時間錯哂」 is this tooltip, and 「00 係第一
round」「果個係勝利數字」 means the on-screen win counters, not video 0:00.

This is the check. `video_snap --write` runs it before writing. `--selftest`
uses committed fixtures (no ffmpeg, no VOD) and plants a wrong score, a
mid-play board, a moment bar labeled as the wrong round, and a m7r10-style
opening-queue / wrong-`seq` mismatch. Needs ffmpeg/ffprobe on PATH for
`--video`; no Python dependency beyond the standard library for `--selftest`.

The score-digit boxes and playfield boxes are this channel's 640x360 layout,
as fractions, the same way video_snap.NEXT_BOXES are. A different layout needs
new boxes (and new digit templates); the tool fails loudly rather than guessing.
"""
import argparse
import base64
import json
import math
import subprocess
import sys
import zlib
from pathlib import Path

import colorsys

from pipeline.video_section import check
from pipeline.video_snap import NEXT_BOXES, probe

ROOT = Path(__file__).resolve().parent.parent
FIX = Path(__file__).resolve().parent / "video_verify_fixtures"

# Digit windows as fractions of a 640x360 frame of this channel's layout.
# Left = blue score (first player of the chosen mapping), right = red.
# The 8x10 template is the tight glyph; search is ±2 x, ±1 y around the anchor.
SCORE_POS = {"L": (309 / 640, 9 / 360), "R": (325 / 640, 9 / 360)}
TW, TH = 8, 10
# Playfields, excluding each player's NEXT queue (see video_snap.NEXT_BOXES).
BOARD_BOXES = [
    (90 / 640, 70 / 360, 150 / 640, 230 / 360),
    (350 / 640, 70 / 360, 150 / 640, 230 / 360),
]
# Spawn window of the current piece at GO (above the visible stack). Fractions
# of the same 640x360 layout. Tight enough to miss the gold GO! flash.
CURRENT_BOXES = [
    (120 / 640, 40 / 360, 90 / 640, 60 / 360),
    (390 / 640, 40 / 360, 90 / 640, 60 / 360),
]
# First N letters of seq compared against current + NEXT (5 preview slots).
OPENING_N = 6
# max(left, right) colourful-pixel fraction. Every 11-26 GO frame was ≤ 0.052;
# mid-play +15 s frames were typically 0.10–0.24. A start of a round may be a
# little busy (GO! flash, leftover from a previous test); mid-play is not 0.05.
BUSY = 0.10
K = 5


def expected_scores(facts):
    """{(match index, round): {player: score at the start of that round}}."""
    out = {}
    for m in facts["matches"]:
        score = {p: 0 for p in facts["players"]}
        for i, r in enumerate(m["rounds"], 1):
            out[(m["index"], i)] = dict(score)
            w = r["winner"]
            if w not in score:
                raise ValueError(f"m{m['index']}r{i}: winner {w!r} is not a player")
            score[w] += 1
    return out


def _ink(buf, w, x, y):
    i = (y * w + x) * 3
    r, g, b = buf[i], buf[i + 1], buf[i + 2]
    return r if r > b else b


def _vec(buf, w, x0, y0, tw=TW, th=TH):
    """Background-subtracted, L2-normalised 8x10 ink crop + three contrasts."""
    vals = [_ink(buf, w, x, y) for y in range(y0, y0 + th) for x in range(x0, x0 + tw)]
    bg = sorted(vals)[len(vals) // 5]
    vals = [max(0, v - bg) for v in vals]
    n = math.sqrt(sum(v * v for v in vals)) or 1.0
    unit = [v / n for v in vals]

    def pix(dx, dy):
        return _ink(buf, w, x0 + dx, y0 + dy)

    ring_u = (pix(2, 3) + pix(5, 3) + pix(2, 5) + pix(5, 5)) / 4 + 1
    ring_l = (pix(2, 5) + pix(5, 5) + pix(2, 7) + pix(5, 7)) / 4 + 1
    mid_m = (pix(3, 4) + pix(4, 4) + pix(3, 5) + pix(4, 5)) / 4 + 1
    hole_u = (pix(3, 4) + pix(4, 4)) / 2
    hole_l = (pix(3, 6) + pix(4, 6)) / 2
    left_m = (pix(1, 4) + pix(1, 5)) / 2
    unit += [hole_u / ring_u, hole_l / ring_l, left_m / mid_m]
    return tuple(unit)


def _load_templates():
    data = json.loads((FIX / "digits.json").read_text(encoding="utf-8"))
    # Rebuild each stored 8x10 crop as a feature vector via a tiny fake frame
    # so training and reading go through the same function.
    tw, th = data["tw"], data["th"]
    out = []
    for d in data["digits"]:
        buf = bytearray(tw * th * 3)
        for i, v in enumerate(d["p"]):
            buf[i * 3] = buf[i * 3 + 1] = buf[i * 3 + 2] = v
        out.append((d["d"], _vec(buf, tw, 0, 0, tw, th)))
    return out


_TEMPLATES = None


def templates():
    global _TEMPLATES
    if _TEMPLATES is None:
        _TEMPLATES = _load_templates()
    return _TEMPLATES


def _dist(a, b):
    return sum((x - y) * (x - y) for x, y in zip(a, b))


def _knn(feat, bank, k=K):
    """Nearest template wins. `n` is how many of the k neighbours agree with it.

    Majority-of-k was wrong for 0 vs 6: a 6 whose exact template is in the bank
    still lost when three slightly farther 0s outvoted it.
    """
    top = sorted((_dist(feat, t[1]), t[0]) for t in bank)[:k]
    nearest_dist, nearest = top[0]
    n = sum(1 for _, d in top if d == nearest)
    return nearest, n, nearest_dist


def read_digit(buf, w, h, anchor, bank=None):
    """Best digit around `anchor` (x, y) in pixel coords, or (None, reason)."""
    bank = templates() if bank is None else bank
    ax, ay = anchor
    best = None
    for dy in (-1, 0, 1):
        for dx in range(-2, 3):
            x0, y0 = ax + dx, ay + dy
            if x0 < 0 or y0 < 0 or x0 + TW > w or y0 + TH > h:
                continue
            feat = _vec(buf, w, x0, y0)
            dig, n, dist = _knn(feat, bank)
            # Prefer the alignment whose nearest template is closest, not the
            # one with the most agreeing neighbours (a 1-pixel shift of a 5
            # can find five 1s farther away and beat the exact 5).
            rec = (-dist, n, dig, dx, dy)
            if best is None or rec[:2] > best[:2]:
                best = rec
    if best is None:
        return None, "unreadable digit"
    return best[2], best[1]


def read_score(buf, w, h, bank=None):
    """(left digit, right digit) of the FT7 overlay, or (None, reason)."""
    pair = []
    for side in ("L", "R"):
        fx, fy = SCORE_POS[side]
        dig, why = read_digit(buf, w, h, (round(fx * w), round(fy * h)), bank)
        if dig is None:
            return None, why
        pair.append(dig)
    return tuple(pair), None


def board_fill(buf, w, h, boxes=None):
    """Colourful-pixel fraction of each playfield, sampled every other pixel."""
    out = []
    for fx, fy, fw, fh in (boxes or BOARD_BOXES):
        x0, y0 = round(fx * w), round(fy * h)
        x1, y1 = x0 + round(fw * w), y0 + round(fh * h)
        colourful = n = 0
        for y in range(y0, min(y1, h), 2):
            for x in range(x0, min(x1, w), 2):
                i = (y * w + x) * 3
                r, g, b = buf[i], buf[i + 1], buf[i + 2]
                n += 1
                mx, mn = max(r, g, b), min(r, g, b)
                if mx > 80 and mx - mn > 30:
                    colourful += 1
        out.append(colourful / n if n else 0.0)
    return out


def _hue_piece(r, g, b):
    """Map a TETR.IO mino colour to a piece letter, or None if not a mino."""
    mx, mn = max(r, g, b), min(r, g, b)
    if mx < 80 or mx - mn < 30:
        return None
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if s < 0.20 or v < 0.18:
        return None
    deg = h * 360
    if deg < 15 or deg >= 345:
        return "Z"
    if deg < 45:
        return "L"
    if deg < 75:
        return "O"
    if deg < 150:
        return "S"
    if deg < 200:
        return "I"
    if deg < 255:
        return "J"
    return "T"


def _classify_box(buf, w, h, box):
    """Majority piece letter in a (fx, fy, fw, fh) fraction box, or '?'."""
    fx, fy, fw, fh = box
    x0, y0 = round(fx * w), round(fy * h)
    x1, y1 = x0 + max(1, round(fw * w)), y0 + max(1, round(fh * h))
    counts = {}
    for y in range(max(0, y0), min(y1, h)):
        row = y * w * 3
        for x in range(max(0, x0), min(x1, w)):
            i = row + x * 3
            let = _hue_piece(buf[i], buf[i + 1], buf[i + 2])
            if let:
                counts[let] = counts.get(let, 0) + 1
    if not counts:
        return "?"
    return max(counts, key=counts.get)


def read_next(buf, w, h, boxes=None):
    """The five NEXT preview letters for each side, as 5-character strings."""
    out = []
    for fx, fy, fw, fh in (boxes or NEXT_BOXES):
        slot_h = fh / 5
        letters = []
        for i in range(5):
            # inset slightly so the NEXT label / box border is not counted
            box = (fx + fw * 0.10, fy + i * slot_h + slot_h * 0.08,
                   fw * 0.80, slot_h * 0.84)
            letters.append(_classify_box(buf, w, h, box))
        out.append("".join(letters))
    return out


def read_current(buf, w, h, boxes=None):
    """The current/spawn piece letter for each side, or '?'."""
    return [_classify_box(buf, w, h, box) for box in (boxes or CURRENT_BOXES)]


def opening_ok(cur, nxt, seq, n=OPENING_N):
    """True if one side's current+NEXT is this round's opening bag (or a first-piece hold).

    At GO, current is seq[0] and NEXT is seq[1:6]. During the last countdown frame
    NEXT may still show seq[0:5]. A player who already held seq[0] shows
    current=seq[1] and NEXT=seq[2:7]. Any of these is this round; a different
    bag is not, even if the FT7 win counters happen to match.
    """
    if not seq or not nxt or len(nxt) < 5 or "?" in nxt:
        return False
    want = seq[:n]
    if nxt == want[1:6] or nxt == want[:5]:
        return True
    if cur and cur != "?" and (cur + nxt)[:n] == want:
        return True
    # first piece already held
    if len(seq) >= 7 and (nxt == seq[2:7] or (cur and cur != "?" and (cur + nxt)[:n] == seq[1:7])):
        return True
    return False


def read_opening(buf, w, h):
    """((left current, left NEXT), (right current, right NEXT))."""
    nxt = read_next(buf, w, h)
    cur = read_current(buf, w, h)
    return (cur[0], nxt[0]), (cur[1], nxt[1])


def load_seqs(session, repo=ROOT):
    """{(match, round): seq} from sim/replay-facts.json, or None if the artefact is missing."""
    path = Path(repo) / "sessions" / session / "sim" / "replay-facts.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return {(r["match"], r["round"] + 1): r["seq"] for r in data["rounds"]}


def _frame_at(video, t, w, h):

    """One RGB24 frame at t seconds (input-seek)."""
    size = w * h * 3
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video),
         "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        check=True, capture_output=True)
    if len(p.stdout) < size:
        raise ValueError(f"ffmpeg returned {len(p.stdout)} bytes at t={t}, expected {size}")
    return p.stdout[:size]


def _mapping(reads, expecteds, players):
    """A consistent (left_player, right_player) or None if none / both fit."""
    if len(players) != 2:
        raise ValueError(f"video_verify expects two players, got {players}")
    a, b = players
    ok = []
    for left, right in ((a, b), (b, a)):
        if all(got == (exp[left], exp[right]) for got, exp in zip(reads, expecteds)):
            ok.append((left, right))
    return ok[0] if len(ok) == 1 else None



def link_t(play_start_s, frames, lead):
    """YouTube t= second for a moment `frames` into a round (video_links.Video.at)."""
    return max(0, int(play_start_s + frames / 60 - lead))


def iter_moments(session, repo=ROOT):
    """The report's mid-round 「落 T 之前」 hits: first qualifying hit per technique variant per player.

    Same selection as pipeline/routes_techniques_section.compute. Empty if the
    night has no routes-techniques section.
    """
    from pipeline.routes_techniques_section import load, compute
    report = Path(repo) / "sessions" / session / "report"
    facts = json.loads((report / "facts.json").read_text(encoding="utf-8"))
    src = load(str(report), repo=str(repo))
    if src is None:
        return []
    out = []
    for t in src["techs"]:
        site = src["sites"][t.href]
        hs = [h for h in t.art["hits"] if h["session"] == session]
        for vid, var in t.variants.items():
            for p in facts["players"]:
                mine = [h for h in hs if h["variant"] == vid and h["player"] == p]
                if t.art.get("qualify"):
                    mine = [h for h in mine if h["qualifies"]]
                if not mine:
                    continue
                first = min(mine, key=lambda h: (h["match"], h["round"], h["lock"]))
                r = site._replay_round(first["session"], first["file"], first["round_index0"])
                frames = r["frames"][first["player"]][first["lock"]]
                out.append({
                    "tech": t.name, "player": p, "match": first["match"],
                    "round": first["round"], "lock": first["lock"], "frames": frames,
                    "label": f"m{first['match']}r{first['round']}",
                })
    return out


def verify_moments(facts, data, video, session, repo=ROOT, sides=None, w=None, h=None, dur=None):
    """Raise ValueError if a mid-round moment link is in the wrong round or outside the round."""
    from pipeline.video_links import Video
    v = Video(data)
    exp = expected_scores(facts)
    players = list(facts["players"])
    if w is None:
        w, h, dur = probe(video)
    starts = {(m["position"], r["round"]): r for m in data["matches"] for r in m["rounds"]}
    moments = iter_moments(session, repo)
    bad = []
    reads = []
    for mo in moments:
        key = (mo["match"], mo["round"])
        if key not in starts:
            bad.append(f"{mo['label']} {mo['tech']}: no play_start in video.json")
            continue
        rnd = starts[key]
        t = link_t(rnd["play_start_s"], mo["frames"], v.lead)
        t_lock = rnd["play_start_s"] + mo["frames"] / 60
        if not (rnd["play_start_s"] < t_lock <= rnd["play_start_s"] + rnd["replay_s"] + 1):
            bad.append(
                f"{mo['label']} {mo['player']} {mo['tech']}: T lock at {t_lock:.2f}s "
                f"is outside the round ({rnd['play_start_s']:.2f}+{rnd['replay_s']:.2f})"
            )
        if t < 0 or t >= dur:
            bad.append(f"{mo['label']} {mo['player']} {mo['tech']}: t={t}s is outside the video")
            continue
        buf = _frame_at(video, t, w, h)
        got, why = read_score(buf, w, h)
        want = exp[key]
        reads.append((got, want, mo, t))
        if got is None:
            bad.append(f"{mo['label']} {mo['player']} {mo['tech']} @ t={t}s: {why}")
    if sides is None and all(g is not None for g, _, _, _ in reads) and reads:
        sides = _mapping([g for g, _, _, _ in reads], [e for _, e, _, _ in reads], players)
        if sides is None:
            bad.append(
                "no single left/right mapping makes every moment-link score equal "
                "the labeled round's pre-round running score (the link is in the wrong round)"
            )
    if sides is not None:
        left, right = sides
        for got, want, mo, t in reads:
            if got is None:
                continue
            if got != (want[left], want[right]):
                bad.append(
                    f"{mo['label']} {mo['player']} {mo['tech']} @ t={t}s: "
                    f"win counters {got[0]}-{got[1]} are not this round's "
                    f"{want[left]}-{want[right]} (0-0 is r1; a-b is r{{a+b+1}})"
                )
    if bad:
        raise ValueError("video_verify moments failed:\n  " + "\n  ".join(bad))
    return reads


def verify(facts, data, video, session=None, repo=ROOT):
    """Raise ValueError naming every round (and, if session is set, every moment link) that fails."""
    check(facts, data)
    w, h, dur = probe(video)
    exp = expected_scores(facts)
    players = list(facts["players"])
    seqs = load_seqs(session, repo) if session is not None else None
    if session is not None and seqs is None:
        raise ValueError(
            f"{session}: sim/replay-facts.json is missing; cannot check opening "
            "piece sequences against the VOD"
        )
    rows = []
    bad = []
    sides = None
    for m in data["matches"]:
        for r in m["rounds"]:
            t = r["play_start_s"]
            label = f"m{m['position']}r{r['round']}"
            if t < 0 or t >= dur:
                bad.append(f"{label}: play_start_s {t} is outside the video (0–{dur:.2f})")
                continue
            buf = _frame_at(video, t, w, h)
            got, why = read_score(buf, w, h)
            fills = board_fill(buf, w, h)
            busy = max(fills) > BUSY
            want = exp[(m["position"], r["round"])]
            opening = read_opening(buf, w, h)
            seq = seqs.get((m["position"], r["round"])) if seqs is not None else None
            bag_ok = None
            if seq is not None:
                bag_ok = all(opening_ok(cur, nxt, seq) for cur, nxt in opening)
            rows.append((label, t, got, want, fills, busy, why, opening, seq, bag_ok))
            if got is None:
                bad.append(f"{label} @ {t:.2f}s: {why}")
            if busy:
                bad.append(
                    f"{label} @ {t:.2f}s: playfields look mid-play "
                    f"(fill {fills[0]:.3f}/{fills[1]:.3f} > {BUSY})"
                )
            if seqs is not None:
                if seq is None:
                    bad.append(f"{label}: no seq in replay-facts.json")
                elif not bag_ok:
                    (Lc, Ln), (Rc, Rn) = opening
                    bad.append(
                        f"{label} @ {t:.2f}s: opening queue L={Lc}+{Ln} R={Rc}+{Rn} "
                        f"does not match replay seq {seq[:OPENING_N]}"
                    )
    readable = [(g, e) for _, _, g, e, *_ in rows if g is not None]
    if len(readable) == len(rows):
        sides = _mapping([g for g, _ in readable], [e for _, e in readable], players)
        if sides is None:
            bad.append(
                "no single left/right player mapping makes every readable score "
                "equal the facts.json running score (the snapped GO is the wrong "
                "round, or the overlay layout changed)"
            )
        else:
            # Re-check is already implied by _mapping; record the mapping for the log.
            pass
    elif not bad:
        bad.append("not every round's score could be read")
    if bad:
        raise ValueError("video_verify failed:\n  " + "\n  ".join(bad))
    moment_rows = []
    if session is not None:
        moment_rows = verify_moments(
            facts, data, video, session, repo=repo, sides=sides, w=w, h=h, dur=dur)
    return rows, moment_rows


def _decode_fix(entry):
    return zlib.decompress(base64.b64decode(entry["z"])), entry["w"], entry["h"]


def selftest():
    """Read committed score-bar and board fixtures; plant a wrong score and a mid-play board."""
    bad = []
    bank = templates()
    if len(bank) < 50:
        bad.append(f"digit bank has only {len(bank)} templates")

    # Every stored glyph classifies as itself (kNN against the rest of the bank).
    data = json.loads((FIX / "digits.json").read_text(encoding="utf-8"))
    tw, th = data["tw"], data["th"]
    miss = 0
    for i, d in enumerate(data["digits"]):
        buf = bytearray(tw * th * 3)
        for j, v in enumerate(d["p"]):
            buf[j * 3] = buf[j * 3 + 1] = buf[j * 3 + 2] = v
        feat = _vec(buf, tw, 0, 0, tw, th)
        rest = [t for k, t in enumerate(bank) if k != i]
        dig, n, _ = _knn(feat, rest)
        if dig != d["d"]:
            miss += 1
    # Leave-one-out on 8x10 glyphs (no search) is allowed a few misses: 0/6 and
    # 5/4 are close at this resolution. The bar fixtures below go through the
    # real search path and must all be exact.
    if miss > 6:
        bad.append(f"leave-one-out digit misses: {miss} (expected a handful, not {miss})")

    bars = json.loads((FIX / "bars.json").read_text(encoding="utf-8"))
    for bar in bars:
        raw, w, h = _decode_fix(bar)
        # The strip is the top `h` rows of a 640-wide frame; SCORE_POS uses
        # fractions of 360 high, so build a padded 640x360 canvas.
        frame = bytearray(640 * 360 * 3)
        row = w * 3
        for y in range(h):
            frame[y * 640 * 3:y * 640 * 3 + row] = raw[y * row:(y + 1) * row]
        got, why = read_score(bytes(frame), 640, 360)
        want = tuple(bar["expected"])
        if got != want:
            bad.append(f"{bar['label']} bar: read {got} ({why}), expected {want}")

    # A correct bar with the wrong expected score must be refused.
    bar = bars[0]
    raw, w, h = _decode_fix(bar)
    frame = bytearray(640 * 360 * 3)
    row = w * 3
    for y in range(h):
        frame[y * 640 * 3:y * 640 * 3 + row] = raw[y * row:(y + 1) * row]
    got, _ = read_score(bytes(frame), 640, 360)
    if got == tuple(bar["expected"]) and got != (1, 1):
        # Plant: claim this 0-0 opening is 1-1. Mapping must reject it.
        fake_exp = [{"yachi": 1, "pinglamb": 1}]
        sides = _mapping([got], fake_exp, ["yachi", "pinglamb"])
        if sides is not None:
            bad.append("a bar whose expected score was planted wrong was accepted")
    else:
        bad.append(f"fixture {bar['label']} could not be used as a wrong-score plant ({got})")

    boards = json.loads((FIX / "boards.json").read_text(encoding="utf-8"))
    for b in boards:
        fills = []
        for crop in b["boards"]:
            raw, w, h = _decode_fix(crop)
            colourful = n = 0
            for y in range(h):
                for x in range(w):
                    i = (y * w + x) * 3
                    r, g, bb = raw[i], raw[i + 1], raw[i + 2]
                    n += 1
                    mx, mn = max(r, g, bb), min(r, g, bb)
                    if mx > 80 and mx - mn > 30:
                        colourful += 1
            fills.append(colourful / n if n else 0.0)
        busy = max(fills) > BUSY
        if b["kind"] == "go" and busy:
            bad.append(f"{b['label']} GO fixture looks mid-play ({fills})")
        if b["kind"] == "mid" and not busy:
            bad.append(f"{b['label']} mid-play fixture was not flagged ({fills})")

    # expected_scores walks the winners. 0-0 is r1; a-b is round a+b+1.
    facts = {
        "players": ["a", "b"],
        "matches": [{"index": 1, "rounds": [
            {"winner": "a"}, {"winner": "b"}, {"winner": "a"}]}],
    }
    got = expected_scores(facts)
    if got[(1, 1)] != {"a": 0, "b": 0} or got[(1, 2)] != {"a": 1, "b": 0} or got[(1, 3)] != {"a": 1, "b": 1}:
        bad.append(f"expected_scores walked winners wrong: {got}")
    if link_t(530.5, 3798, 1) != 592:
        bad.append(f"link_t m1r7 T is {link_t(530.5, 3798, 1)}, expected 592")

    # Mid-round moment bars (win counters at the published t=) must read the labeled
    # round's score; a bar from r7 (3-3) labeled as r1 (0-0) must be refused.
    mbars = json.loads((FIX / "moment_bars.json").read_text(encoding="utf-8"))
    moment_ok = 0
    for bar in mbars:
        raw, w, h = _decode_fix(bar)
        frame = bytearray(640 * 360 * 3)
        row = w * 3
        for y in range(h):
            frame[y * 640 * 3:y * 640 * 3 + row] = raw[y * row:(y + 1) * row]
        got, why = read_score(bytes(frame), 640, 360)
        want = tuple(bar["expected"])
        if got != want:
            bad.append(f"moment {bar['label']}: read {got} ({why}), expected {want}")
        else:
            moment_ok += 1
    # plant: first moment bar with a different round's score
    planted = False
    for bar in mbars:
        raw, w, h = _decode_fix(bar)
        frame = bytearray(640 * 360 * 3)
        row = w * 3
        for y in range(h):
            frame[y * 640 * 3:y * 640 * 3 + row] = raw[y * row:(y + 1) * row]
        got, _ = read_score(bytes(frame), 640, 360)
        if got and got != (0, 0):
            sides = _mapping([got], [{"pinglamb": 0, "yachi": 0}], ["pinglamb", "yachi"])
            if sides is not None:
                bad.append(f"moment {bar['label']} accepted as 0-0 (r1) but read {got}")
            planted = True
            break
    if not planted:
        bad.append("no mid-round moment bar could be used as a wrong-round plant")

    # Opening piece sequence: the m7r10 GO frame's current+NEXT must read as
    # TZOSIL, and the same frame checked against m7r9's TIOJSL bag must be
    # refused. Win counters on that frame are 4-5 (m7r10's start score); a
    # score-only check would not catch a different bag with the same first
    # letter (both r9 and r10 start with T) or a seating swap vs YouTube.
    opening_fix = json.loads((FIX / "openings.json").read_text(encoding="utf-8"))
    frame = bytearray(640 * 360 * 3)

    def paste(entry, x0, y0):
        raw, cw, ch = _decode_fix(entry)
        for y in range(ch):
            src = y * cw * 3
            dst = ((y0 + y) * 640 + x0) * 3
            frame[dst:dst + cw * 3] = raw[src:src + cw * 3]

    paste(opening_fix["bar"], 0, 0)
    for box, crop in zip(NEXT_BOXES, opening_fix["next"]):
        paste(crop, round(box[0] * 640), round(box[1] * 360))
    for box, crop in zip(CURRENT_BOXES, opening_fix["current"]):
        paste(crop, round(box[0] * 640), round(box[1] * 360))
    frame = bytes(frame)
    (Lc, Ln), (Rc, Rn) = read_opening(frame, 640, 360)
    seq = opening_fix["seq"]
    if not (opening_ok(Lc, Ln, seq) and opening_ok(Rc, Rn, seq)):
        bad.append(
            f"m7r10 GO fixture opening L={Lc}+{Ln} R={Rc}+{Rn} did not match seq {seq[:6]}"
        )
    wrong = opening_fix["wrong_seq"]
    if opening_ok(Lc, Ln, wrong) and opening_ok(Rc, Rn, wrong):
        bad.append(
            f"m7r10 GO fixture was accepted as {wrong[:6]} (m7r9-style wrong bag)"
        )
    got_bar, _ = read_score(frame, 640, 360)
    if got_bar != tuple(opening_fix["bar"]["expected"]):
        bad.append(f"m7r10 GO fixture bar read {got_bar}, expected {opening_fix['bar']['expected']}")

    for line in bad:
        print("FAIL", line)
    print(
        f"{'ok ' if not bad else 'FAIL'} video_verify selftest: {len(bars)} score-bar "
        f"fixtures read, {moment_ok} moment bars, wrong expected score refused, "
        f"wrong-round moment refused, mid-play boards flagged, opening sequence "
        f"matched and wrong bag refused, {len(bank)} digit templates"
    )
    return 1 if bad else 0


def main(argv):
    ap = argparse.ArgumentParser(prog="python3 -m pipeline.video_verify")
    ap.add_argument("session", nargs="?")
    ap.add_argument("--video")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not (a.session and a.video):
        ap.error("session and --video are required")
    sess = Path(a.session)
    facts = json.loads((sess / "report" / "facts.json").read_text(encoding="utf-8"))
    data = json.loads((sess / "video" / "video.json").read_text(encoding="utf-8"))
    try:
        rows, moments = verify(facts, data, a.video, session=sess.name)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    print(f"{len(rows)} rounds: in-game score matches facts.json, boards are a start of a "
          "round, opening piece sequence matches the replay")
    print(f"{len(moments)} moment links: win counters match the labeled round")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

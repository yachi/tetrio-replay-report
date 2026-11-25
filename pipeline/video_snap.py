"""影片時間對畫面 — write a night's video.json by snapping every round start to the video's frames.

    python3 -m pipeline.video_snap sessions/<date> --video <mp4> --id <youtube id> [--write]
           [--fetched YYYY-MM-DD] [--format-note "<how it was downloaded>"]
    python3 -m pipeline.video_snap --selftest

The method is the one 2026-11-17's video.json records, now committed instead of re-written by hand
each night:

* a replay's `ts` is its match's END; facts.json carries it and every round's length (the longer
  of the two players' `finaltime_ms`);
* the video is sampled at 4 frames a second, and each sample is reduced to how much the two NEXT
  queues changed since the previous one. During TETR.IO's empty-board countdown both queues stand
  still; at GO both shift at once. So a GO is a sample where BOTH queues jump (>= HI) after at
  least QUIET_S of both standing still (< LO). That is "the first frame after the countdown";
* one constant maps the replay clock onto the video (11-17's files agree on it to about 0.05 s
  across matches): it is chosen as the offset that puts the most matches' last rounds on a GO;
* then, per match, the last round is snapped to the GO nearest its prediction, and each earlier
  round is predicted GAP_S plus its own length before the next round's SNAPPED start and snapped
  in turn ("walking back"). A round with no GO within WINDOW_S of its prediction is an error,
  never a guess.

`max_snap_s` in the file is the largest |snapped - predicted| over every round.

The NEXT-queue boxes are this channel's 640x360 layout (NEXT_BOXES, as fractions of the frame, so
any resolution of the same layout works). A different layout needs new boxes; the tool fails
loudly (too few GOs) rather than snapping to something else. Trust tier: VIDEO, as
pipeline/video_links.py says. The written file is checked with pipeline/video_section.check.
Needs ffmpeg/ffprobe on PATH; no Python dependency beyond the standard library.
"""
import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FPS = 4
STEP = 1 / FPS
# (x, y, w, h) of each player's NEXT queue, as fractions of a 640x360 frame of this channel's layout.
NEXT_BOXES = [(255 / 640, 70 / 360, 57 / 640, 180 / 360), (505 / 640, 70 / 360, 57 / 640, 180 / 360)]
CELL_W, CELL_H = 12, 36      # each box is reduced to this many grey cells
HI = 8.0                     # mean |diff| per cell that counts as "the queue moved"
LO = 3.0                     # below this the queue "stood still" (encoder noise peaks near 2)
QUIET_S = 1.5                # standing still this long before a GO
GAP_S = 10.0                 # nominal time from one round's end to the next round's GO
WINDOW_S = 2.0               # how far a snap may move a prediction
OFFSET_TOL_S = 1.0           # a match's last round "lands on a GO" within this


def rlen(r):
    return max(p["finaltime_ms"] for p in r["players"].values()) / 1000


def _unix(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def probe(video):
    """(width, height, duration_s) of the video."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", str(video)],
                         check=True, capture_output=True, text=True).stdout
    j = json.loads(out)
    s = j["streams"][0]
    return s["width"], s["height"], float(j["format"]["duration"])


def signal(video):
    """Per 1/4 s sample: (left NEXT change, right NEXT change), mean |grey diff| per cell."""
    w, h, _ = probe(video)
    chains, labels = [], []
    for k, (fx, fy, fw, fh) in enumerate(NEXT_BOXES):
        cw, ch, cx, cy = round(fw * w), round(fh * h), round(fx * w), round(fy * h)
        chains.append(f"[s{k}]crop={cw}:{ch}:{cx}:{cy},scale={CELL_W}:{CELL_H}[c{k}]")
        labels.append(f"[c{k}]")
    fc = (f"[0:v]fps={FPS},split={len(NEXT_BOXES)}" + "".join(f"[s{k}]" for k in range(len(NEXT_BOXES)))
          + ";" + ";".join(chains) + ";" + "".join(labels)
          + f"hstack=inputs={len(NEXT_BOXES)},format=gray[o]")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-filter_complex", fc,
                          "-map", "[o]", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    nb, row = len(NEXT_BOXES), len(NEXT_BOXES) * CELL_W
    size, cells = row * CELL_H, CELL_W * CELL_H
    out, prev = [], None
    while True:
        b = p.stdout.read(size)
        if len(b) < size:
            break
        if prev is None:
            out.append(tuple(0.0 for _ in range(nb)))
        else:
            out.append(tuple(
                sum(abs(b[y * row + k * CELL_W + x] - prev[y * row + k * CELL_W + x])
                    for y in range(CELL_H) for x in range(CELL_W)) / cells
                for k in range(nb)))
        prev = b
    if p.wait() != 0:
        raise SystemExit(f"ffmpeg failed on {video}")
    return out


def gos(sig):
    """Video times (s) of every GO: both queues jump after QUIET_S of both standing still.

    One queue may jump one sample after the other (2026-11-24 m5r2: the left NEXT box moved a
    quarter second after the right one); the GO is the first sample either queue moved.
    """
    q = round(QUIET_S * FPS)
    out = []
    for i in range(q, len(sig)):
        if max(sig[i]) < HI or not all(max(s) < LO for s in sig[i - q:i]):
            continue
        nxt = sig[i + 1] if i + 1 < len(sig) else sig[i]
        if all(max(a, b) >= HI for a, b in zip(sig[i], nxt)):
            out.append(i * STEP)
    return out


def _nearest(events, t, tol):
    best = min(events, key=lambda e: abs(e - t), default=None)
    return best if best is not None and abs(best - t) <= tol else None


def snap(facts, events):
    """[(match, [(snapped, predicted), ...])], every round of every match snapped to a GO."""
    ms = facts["matches"]
    # The replay->video offset: video_t = unix_t - c. Try every (last round, GO) pairing.
    best = None
    for m in ms:
        for e in events:
            c = _unix(m["ts"]) - rlen(m["rounds"][-1]) - e
            hits = [_nearest(events, _unix(n["ts"]) - c - rlen(n["rounds"][-1]), OFFSET_TOL_S)
                    for n in ms]
            score = (sum(h is not None for h in hits),
                     -sum(abs(h - (_unix(n["ts"]) - c - rlen(n["rounds"][-1])))
                          for h, n in zip(hits, ms) if h is not None))
            if best is None or score > best[0]:
                best = (score, c)
    if best is None or best[0][0] < len(ms):
        got = 0 if best is None else best[0][0]
        raise ValueError(f"no single replay->video offset puts every match's last round on a GO "
                         f"({got} of {len(ms)}; {len(events)} GOs found)")
    c = best[1]
    out = []
    for m in ms:
        rounds = m["rounds"]
        pred = _unix(m["ts"]) - c - rlen(rounds[-1])
        res = [None] * len(rounds)
        for i in range(len(rounds) - 1, -1, -1):
            s = _nearest(events, pred, WINDOW_S)
            if s is None:
                raise ValueError(f"m{m['index']}r{i + 1}: no GO within {WINDOW_S} s of "
                                 f"{pred:.2f} s")
            res[i] = (s, pred)
            if i:
                pred = s - GAP_S - rlen(rounds[i - 1])
        out.append((m, res))
    return out


def build(facts, events, video_meta):
    snapped = snap(facts, events)
    worst = max(abs(s - p) for _, res in snapped for s, p in res)
    return {
        "schema": "session-video/1",
        "video": video_meta,
        "report_eligible": False,
        "alignment": {
            "method": ("each replay's ts is the match's end; walking back by the replay's own round "
                       "lengths plus the gap between rounds, every round start is snapped to the "
                       "first frame after the empty-board countdown in the video, sampled at 4 "
                       "frames a second (pipeline/video_snap.py)"),
            "max_snap_s": round(worst, 2),
            "link_lead_s": 1},
        "matches": [{"position": m["index"], "file": m["file"],
                     "rounds": [{"round": i + 1, "play_start_s": round(s, 2),
                                 "replay_s": round(rlen(r), 3)}
                                for i, ((s, _), r) in enumerate(zip(res, m["rounds"]))]}
                    for m, res in snapped],
    }


def per_match_snap(facts, events):
    """{position: largest |snap - prediction|} for the report."""
    return {m["index"]: max(abs(s - p) for s, p in res) for m, res in snap(facts, events)}


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    ap = argparse.ArgumentParser(prog="python3 -m pipeline.video_snap")
    ap.add_argument("session", nargs="?")
    ap.add_argument("--video")
    ap.add_argument("--id")
    ap.add_argument("--fetched", default=dt.date.today().isoformat())
    ap.add_argument("--format-note", default="360p mp4 via yt-dlp")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not (a.session and a.video and a.id):
        ap.error("session, --video and --id are required")
    from pipeline.video_section import check
    sess = Path(a.session)
    facts = json.loads((sess / "report" / "facts.json").read_text(encoding="utf-8"))
    _, _, dur = probe(a.video)
    meta = {"id": a.id, "url": f"https://www.youtube.com/watch?v={a.id}", "fetched": a.fetched,
            "format": a.format_note, "sha256": _sha256(a.video), "duration_s": int(dur)}
    events = gos(signal(a.video))
    data = build(facts, events, meta)
    check(facts, data)
    for pos, w in per_match_snap(facts, events).items():
        print(f"m{pos}: max snap {w:.2f} s")
    print(f"{len(events)} GOs in the video; max_snap_s {data['alignment']['max_snap_s']}")
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    if a.write:
        out = sess / "video" / "video.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print("wrote", out)
    else:
        sys.stdout.write(text)
    return 0


def _synthetic(starts, lengths, tail=30.0):
    """A signal with a GO at each start: quiet countdown before it, a queue move every 1/2 s of
    play (never QUIET_S still), quiet again between rounds."""
    n = int((max(s + l for s, l in zip(starts, lengths)) + tail) * FPS)
    sig = [(0.5, 0.5)] * n
    for s, l in zip(starts, lengths):
        i0 = round(s * FPS)
        for i in range(i0, min(n, i0 + int(l * FPS))):
            sig[i] = (20.0, 20.0) if (i - i0) % 2 == 0 else (0.5, 20.0)
    return sig


def selftest():
    """Rebuild 2026-11-17's committed frame-snapped file from a synthetic signal with GOs at its
    own starts, then plant faults that must each be refused."""
    import copy
    from pipeline.video_section import check
    sess = ROOT / "sessions" / "2026-11-17"
    facts = json.loads((sess / "report" / "facts.json").read_text(encoding="utf-8"))
    ref = json.loads((sess / "video" / "video.json").read_text(encoding="utf-8"))
    starts = [r["play_start_s"] for m in ref["matches"] for r in m["rounds"]]
    lengths = [r["replay_s"] for m in ref["matches"] for r in m["rounds"]]
    events = gos(_synthetic(starts, lengths))
    bad = []
    data = build(facts, events, ref["video"])
    check(facts, data)
    if data["matches"] != ref["matches"]:
        bad.append("the synthetic 11-17 signal does not rebuild 11-17's committed rounds")
    if data["alignment"]["max_snap_s"] > 0.75:
        bad.append(f"max snap {data['alignment']['max_snap_s']} on a clean signal")

    def refused(name, f, ev=events):
        try:
            build(f, ev, ref["video"])
        except ValueError:
            return
        bad.append(f"planted {name} was not caught")

    f = copy.deepcopy(facts)
    t = _unix(f["matches"][1]["ts"]) + 30
    f["matches"][1]["ts"] = dt.datetime.fromtimestamp(t, dt.timezone.utc).isoformat()
    refused("one match's ts shifted 30 s", f)
    f = copy.deepcopy(facts)
    del f["matches"][0]["rounds"][2]
    refused("a round missing from a match", f)
    f = copy.deepcopy(facts)
    f["matches"][2]["rounds"].insert(0, copy.deepcopy(f["matches"][2]["rounds"][0]))
    refused("an extra round in a match", f)
    gone = round(starts[3] * FPS) * STEP
    refused("one countdown missing from the video", facts, [e for e in events if e != gone])
    moved = build(facts, [e + 400 for e in events], ref["video"])
    if [r["play_start_s"] for m in moved["matches"] for r in m["rounds"]] != \
            [round(x + 400, 2) for x in starts]:
        bad.append("a video starting 400 s later did not move every start by 400 s")
    noisy = _synthetic(starts, lengths)
    for i in range(len(noisy)):
        noisy[i] = (noisy[i][0], 0.5)   # one queue box sees nothing: wrong layout
    if gos(noisy):
        bad.append("a GO was found with one NEXT box never moving")
    stag = _synthetic(starts, lengths)
    i0 = round(starts[3] * FPS)
    stag[i0] = (0.5, 20.0)              # the left queue moves one sample late
    stag[i0 + 1] = (20.0, 0.5)
    if i0 * STEP not in gos(stag):
        bad.append("a GO with the two queues one sample apart was not found")
    stag[i0 + 1] = (0.5, 0.5)           # ... but never at all: no GO
    stag[i0 + 2] = (0.5, 0.5)
    if i0 * STEP in gos(stag):
        bad.append("a GO was found where only one queue moved")
    for b in bad:
        print("FAIL", b)
    print(f"{'ok ' if not bad else 'FAIL'} video_snap selftest: 11-17 rebuilt from a synthetic "
          f"signal, {len(events)} GOs; 4 planted faults refused, 1 shifted video followed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""影片連結 — every place the site links a replay also links the same moment in the night's video.

    python3 -m pipeline.video_links --selftest

A session with `sessions/<date>/video/video.json` (schema `session-video/1`, checked against
facts.json by `pipeline/video_section.py`) has a timestamp for every replay round: `play_start_s`,
the first video frame after that round's countdown. A replay frame counts from that point (a
round's first lock lands under a second in), so a moment `frames` into a round is at
`play_start_s + frames / 60` in the video. Every link starts `link_lead_s` seconds earlier, so the
moment is on screen when it plays, and is floored to a whole second, which is all YouTube's `t=`
takes.

Trust tier: VIDEO. The timestamps are an alignment (described in the file), not a measurement any
claim rests on, so a video link is never badged and never counted. A session without the file gets
no video links at all — every caller treats `None` as 「no link」, never as a link to round start.
"""
import html
import json
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "session-video/1"
FPS = 60
CLASS = "rl-v"
TITLE = "喺直播影片睇呢一刻（影片時間係對齊出嚟，大約）"
TEXT = "▶ 影片"


class Video:
    def __init__(self, data):
        if data.get("schema") != SCHEMA:
            raise ValueError(f"video.json schema {data.get('schema')!r} != {SCHEMA!r}")
        self.url = data["video"]["url"]
        self.lead = data["alignment"]["link_lead_s"]
        self.starts = {(m["position"], r["round"]): r["play_start_s"]
                       for m in data["matches"] for r in m["rounds"]}

    def at(self, seconds):
        return f"{self.url}&t={max(0, int(seconds - self.lead))}s"

    def round_url(self, m, r):
        s = self.starts.get((m, r))
        return None if s is None else self.at(s)

    def moment_url(self, m, r, frames):
        s = self.starts.get((m, r))
        return None if s is None else self.at(s + frames / FPS)


@lru_cache(maxsize=None)
def _load(path):
    p = Path(path)
    if not p.is_file():
        return None
    return Video(json.loads(p.read_text(encoding="utf-8")))


def for_session(session, root=ROOT):
    """The session's Video, or None when it has no video.json."""
    return _load(str(Path(root) / "sessions" / session / "video" / "video.json"))


def anchor(url, text=TEXT, cls=CLASS):
    """One video link, opening in a new tab. `url` None gives ''."""
    if url is None:
        return ""
    return (f'<a class="{cls}" href="{html.escape(url)}" target="_blank" rel="noopener" '
            f'title="{TITLE}">{text}</a>')


def round_anchor(session, m, r, text=TEXT, root=ROOT):
    """The video link for match position `m`, round `r` of `session`, or '' without a video."""
    v = for_session(session, root)
    return "" if v is None else anchor(v.round_url(m, r), text)


def _selftest():
    v = Video({"schema": SCHEMA, "video": {"url": "https://www.youtube.com/watch?v=X"},
               "alignment": {"link_lead_s": 5},
               "matches": [{"position": 1, "rounds": [{"round": 1, "play_start_s": 107.25},
                                                      {"round": 2, "play_start_s": 3.0}]}]})
    bad = []
    for got, want in [(v.round_url(1, 1), "https://www.youtube.com/watch?v=X&t=102s"),
                      (v.round_url(1, 2), "https://www.youtube.com/watch?v=X&t=0s"),
                      (v.moment_url(1, 1, 600), "https://www.youtube.com/watch?v=X&t=112s"),
                      (v.round_url(2, 1), None), (anchor(None), "")]:
        if got != want:
            bad.append(f"{got!r} != {want!r}")
    if 'href="https://www.youtube.com/watch?v=X&amp;t=102s"' not in anchor(v.round_url(1, 1)):
        bad.append("anchor does not escape the href")
    try:
        Video({"schema": "x"})
        bad.append("a wrong schema was accepted")
    except ValueError:
        pass
    real = for_session("2026-11-05")
    if real is None or real.round_url(1, 1) is None:
        bad.append("2026-11-05 has no video links")
    if for_session("2026-07-22") is not None:
        bad.append("a session with no video.json got video links")
    for b in bad:
        print("FAIL", b)
    print(f"{'ok ' if not bad else 'FAIL'} video_links selftest")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(_selftest() if "--selftest" in sys.argv else 0)

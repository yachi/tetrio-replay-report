"""影片時間由直播時鐘對出嚟 — video.json for a night whose stream video cannot be downloaded.

    python3 -m pipeline.video_clock --write      # (re)write every night's video.json below
    python3 -m pipeline.video_clock --check      # the committed files are what this writes
    python3 -m pipeline.video_clock --selftest   # the method against 2026-11-05's frame-snapped file

2026-11-05's video.json was aligned frame by frame against the downloaded video. The other nights'
streams on the same channel could not be downloaded from the cloud container (YouTube's bot check,
2026-11-06), so their round starts come from two clocks instead:

* a replay's `ts` is the match's END, in UTC;
* a live stream's VOD starts at its `startDate` (YouTube's own metadata, read 2026-11-06).

So the last round of a match starts at `ts - startDate + END_LAG - replay_s(last)`, and each earlier
round `GAP + replay_s` before the next. END_LAG and GAP are fitted on 11-05's frame-snapped rounds,
where they reproduce every start to about a second (`--selftest` measures it and fails past
SELFTEST_MAX_S). Nothing here is a measurement any figure rests on: the trust tier is VIDEO, the
same as video_links.py's, and the 影片 section says the times are aligned from the clocks.
"""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
END_LAG = 7.25      # s from a match's replay ts to the end of its last round in the VOD
GAP = 10.04         # s between one round's end and the next round's start
SELFTEST_MAX_S = 2.0
FETCHED = "2026-11-06"

# night -> [(video id, YouTube startDate, duration_s)], in stream order. A night whose matches span
# two streams lists both; each match goes to the last stream that started before it ended.
STREAMS = {
    "2026-09-10": [("MX3rN6S62-Y", "2026-09-10T15:35:21Z", 5380)],
    "2026-09-18": [("baRUL0XUPLQ", "2026-09-18T15:36:41Z", 5500),
                   ("gP3P9vRwMOY", "2026-09-18T17:09:39Z", 6645)],
    "2026-09-19": [("Qocj1uRcrPc", "2026-09-19T14:11:25Z", 15766)],
    "2026-10-22": [("Do03WFp68Uc", "2026-10-22T16:11:20Z", 5895)],
    "2026-10-29": [("YrHKbxDx4XU", "2026-10-29T15:54:08Z", 5784)],
    "2026-11-01": [("R8wnmc9BHEA", "2026-11-01T15:10:59Z", 11955)],
}
CALIBRATION = ("2026-11-05", "2026-11-05T16:37:33Z")


def _t(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))


def rlen(r):
    return max(p["finaltime_ms"] for p in r["players"].values()) / 1000


def starts(match, start_iso):
    """Every round's start in the VOD that began at `start_iso`."""
    t = (_t(match["ts"]) - _t(start_iso)).total_seconds() + END_LAG
    out = [0.0] * len(match["rounds"])
    for i in range(len(match["rounds"]) - 1, -1, -1):
        out[i] = t - rlen(match["rounds"][i])
        t = out[i] - GAP
    return out


def build(session):
    facts = json.loads((ROOT / "sessions" / session / "report" / "facts.json").read_text())
    streams = STREAMS[session]
    vids = [{"id": vid, "url": f"https://www.youtube.com/watch?v={vid}", "fetched": FETCHED,
             "format": "not downloaded: aligned from the stream's startDate",
             "started": start, "duration_s": dur} for vid, start, dur in streams]
    matches = []
    for m in facts["matches"]:
        end = _t(m["ts"])
        k = max(i for i, (_, s, _) in enumerate(streams) if _t(s) < end)
        ss = starts(m, streams[k][1])
        entry = {"position": m["index"], "file": m["file"]}
        if k:
            entry["video"] = k
        entry["rounds"] = [{"round": i + 1, "play_start_s": round(s, 2),
                            "replay_s": round(rlen(r), 3)}
                           for i, (s, r) in enumerate(zip(ss, m["rounds"]))]
        matches.append(entry)
    data = {"schema": "session-video/1", "video": vids[0]}
    if len(vids) > 1:
        data["more_videos"] = vids[1:]
    data.update({
        "report_eligible": False,
        "alignment": {
            "kind": "stream_clock",
            "method": ("not frame-snapped: each match's replay ts (its end, UTC) less the stream's "
                       f"startDate, plus {END_LAG} s, is the end of its last round in the video; "
                       f"each earlier round starts {GAP} s plus its own replay length before the "
                       "next. Both constants are fitted on 2026-11-05's frame-snapped video.json "
                       "(pipeline/video_clock.py --selftest)"),
            "max_snap_s": None,
            "link_lead_s": 5},
        "matches": matches})
    return data


def path(session):
    return ROOT / "sessions" / session / "video" / "video.json"


def text(session):
    return json.dumps(build(session), ensure_ascii=False, indent=1) + "\n"


def selftest():
    session, start = CALIBRATION
    facts = json.loads((ROOT / "sessions" / session / "report" / "facts.json").read_text())
    snapped = json.loads(path(session).read_text())
    worst = 0.0
    for m, v in zip(facts["matches"], snapped["matches"]):
        for s, r in zip(starts(m, start), v["rounds"]):
            worst = max(worst, abs(s - r["play_start_s"]))
    ok = worst <= SELFTEST_MAX_S
    print(f"{'ok ' if ok else 'FAIL'} video_clock selftest: worst round start {worst:.2f} s from "
          f"{session}'s frame-snapped file (limit {SELFTEST_MAX_S})")
    return 0 if ok else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    bad = 0
    for session in STREAMS:
        p, t = path(session), text(session)
        if "--write" in argv:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(t, encoding="utf-8")
            print("wrote", p.relative_to(ROOT))
        elif not p.exists() or p.read_text(encoding="utf-8") != t:
            print("FAIL stale", p.relative_to(ROOT))
            bad = 1
    return bad


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

"""影片 — every match and round linked to its moment in the session's video, plus any match the
video holds that has no replay.

Data: `<session>/video/video.json` (schema `session-video/1`), written by hand from the video and
checked here. A session without that file gets no section (`build` returns None), so the region is
conditional and self-inserting, like 全消.

Trust tier: VIDEO, not replay. The timestamps come from aligning each replay's own round lengths
with the video's frames (the alignment is described in the file), and a recovered match's round
winners are read off TETR.IO's between-round score overlay. Nothing here enters facts.json, a
count, a claim or a badge, and the section says so. What IS checked, against facts.json:

* every replay match and round of the session has exactly one timestamp, in order, and the
  file name and position match facts.json;
* each round's timestamp is later than the previous round's start plus its replay length (the
  video cannot show a round starting before the last one ended);
* a recovered match's per-round winners agree with its own running score, end on the format's
  target, and sit between the two replay matches it names, in video time.

`--selftest` plants a violation of each and requires it to be caught.
"""
import copy
import html
import json
import sys
from pathlib import Path

from pipeline import report_charts
from pipeline.claims.build_claims import SIMPLIFIED
from pipeline.video_links import video_of, videos

SCHEMA = "session-video/1"

# The closing sentence says how the times were found, per `alignment.kind` (default "frames").
NOTES = {
    "frames": ("時間點係用 replay 每局嘅長度對返影片畫面得出嚟，每局相差唔夠 1 秒；"
               "係影片對出嚟，唔係 replay 證出嚟，所以冇 claim 亦冇 ✓。"),
    "stream_clock": ("呢晚嘅影片冇下載到，所以時間點唔係對畫面：係用每場 replay 記低嘅完場時間，"
                     "減直播開始嘅時間，再用每局嘅長度倒推出嚟（pipeline/video_clock.py）。"
                     "同一個方法放喺 11-05 對畫面嗰份上面，每局相差唔夠 1 秒，"
                     "但呢晚冇畫面核對過，所以當佢大約；冇 claim 亦冇 ✓。"),
}

CSS = """
<style>
/* ---------- 影片 (generated) ---------- */
/* Scoped under #video, every class prefixed vd-: a generated section's <style> is injected into
   the body and at equal specificity beats the report's own stylesheet. */
#video .vd-list { margin: 1.4rem 0 0; display: grid; gap: .7rem; }
#video .vd-match { border: 1px solid var(--border); border-radius: 10px; padding: .75rem .9rem; }
#video .vd-match.vd-rec { border-style: dashed; }
#video .vd-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: .4rem .9rem; }
#video .vd-name { font-weight: 700; }
#video .vd-score { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
#video .vd-tag { font-family: var(--font-mono); font-size: .62rem; letter-spacing: .06em;
  color: var(--muted); }
#video .vd-list { grid-template-columns: repeat(auto-fill, minmax(11rem, 1fr)); }
#video .vd-note { margin: .9rem 0 0; font-size: .8rem; line-height: 1.8; color: var(--muted); }
</style>
"""


def path_for(report_dir):
    return Path(report_dir).parent / "video" / "video.json"


def load(report_dir):
    p = path_for(report_dir)
    return json.loads(p.read_text()) if p.exists() else None


def _clock(s):
    s = int(s)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def _href(video, s, lead):
    return f'{video["url"]}&amp;t={max(0, int(s - lead))}s'


def check(facts, data):
    """Raise ValueError naming the first inconsistency between video.json and facts.json."""
    if data.get("schema") != SCHEMA:
        raise ValueError(f"schema is {data.get('schema')!r}, expected {SCHEMA!r}")
    if data.get("report_eligible") is not False:
        raise ValueError("report_eligible must be false: video data is not replay data")
    if data["alignment"].get("kind", "frames") not in NOTES:
        raise ValueError(f"alignment kind {data['alignment']['kind']!r} is not one of {sorted(NOTES)}")
    vids = videos(data)
    vm, fm = data["matches"], facts["matches"]
    if len(vm) != len(fm):
        raise ValueError(f"{len(vm)} video matches against {len(fm)} replay matches")
    prev_end = None
    prev_vid = 0
    match_span = {}
    for v, m in zip(vm, fm):
        k = v.get("video", 0)
        if not (isinstance(k, int) and 0 <= k < len(vids)):
            raise ValueError(f"m{v['position']}: no video {k!r} (the night has {len(vids)})")
        if k < prev_vid:
            raise ValueError(f"m{v['position']} is in video {k}, after a match in video {prev_vid}")
        if k != prev_vid:
            prev_end = None     # a new video's clock starts at 0
        prev_vid = k
        first, last = v["rounds"][0], v["rounds"][-1]
        if first["play_start_s"] < 0 or last["play_start_s"] + last["replay_s"] > vids[k]["duration_s"]:
            raise ValueError(f"m{v['position']} runs outside its video (0 to "
                             f"{vids[k]['duration_s']} s)")
        if (v["position"], v["file"]) != (m["index"], m["file"]):
            raise ValueError(f"match {v['position']} {v['file']} is not facts.json's "
                             f"{m['index']} {m['file']}")
        if len(v["rounds"]) != len(m["rounds"]):
            raise ValueError(f"m{v['position']}: {len(v['rounds'])} timestamps for "
                             f"{len(m['rounds'])} rounds")
        for i, r in enumerate(v["rounds"]):
            if r["round"] != i + 1:
                raise ValueError(f"m{v['position']}: round {r['round']} out of order")
            if prev_end is not None and r["play_start_s"] < prev_end:
                raise ValueError(f"m{v['position']}r{r['round']} starts at {r['play_start_s']} "
                                 f"before the previous round ended ({prev_end:.2f})")
            prev_end = r["play_start_s"] + r["replay_s"]
        match_span[v["position"]] = (v["rounds"][0]["play_start_s"], prev_end)
    players = set(facts["players"])
    for rec in data.get("recovered", []):
        a = rec["after_position"]
        if a not in match_span:
            raise ValueError(f"recovered match after m{a}: no such replay match")
        target = int(rec["format"].removeprefix("FT"))
        score = {p: 0 for p in players}
        last = match_span[a][1]
        for i, r in enumerate(rec["rounds"]):
            if r["round"] != i + 1:
                raise ValueError(f"recovered round {r['round']} out of order")
            if r["winner"] not in players:
                raise ValueError(f"recovered round {r['round']}: unknown winner {r['winner']!r}")
            if not last <= r["play_start_s"] < r["end_s"]:
                raise ValueError(f"recovered round {r['round']}: times out of order")
            last = r["end_s"]
            score[r["winner"]] += 1
            if score != r["score_after"]:
                raise ValueError(f"recovered round {r['round']}: running score {score} is not "
                                 f"the overlay's {r['score_after']}")
        if max(score.values()) != target or sorted(score.values())[0] >= target:
            raise ValueError(f"recovered match ends {score}, not a finished {rec['format']}")
        nxt = match_span.get(a + 1)
        if nxt and last > nxt[0]:
            raise ValueError(f"recovered match after m{a} runs into m{a + 1}")


def _score(winners, players):
    return " : ".join(str(sum(w == p for w in winners)) for p in players)


def build(facts, report_dir):
    data = load(report_dir)
    if data is None:
        return None
    check(facts, data)
    lead = data["alignment"]["link_lead_s"]
    vids = videos(data)
    players = facts["players"]
    recovered = {r["after_position"]: r for r in data.get("recovered", [])}
    n_rec = len(recovered)
    vid_of = {v["position"]: video_of(data, v) for v in data["matches"]}

    def link(v):
        return (f'<a href="{html.escape(v["url"])}" target="_blank" rel="noopener">錄影</a>'
                f'（長 {_clock(v["duration_s"])}）')
    if len(vids) == 1:
        intro = f'成晚有{link(vids[0])}。'
    else:
        intro = ('成晚嘅直播分咗 ' + str(len(vids)) + ' 段：'
                 + '、'.join(f'第 {i + 1} 段{link(v)}' for i, v in enumerate(vids)) + '。')
    out = [CSS, '<section id="video">', '  <div class="wrap">',
           '    <div class="eyebrow">影片 · VIDEO</div>',
           '    <h2 class="section-title">每一局喺影片邊度</h2>',
           f'    <p class="section-lede">{intro}時間軸上每條色線係一局，顏色係嗰局邊個贏，'
           f'撳落去開影片嗰局，會早 {lead} 秒開始，等你睇到倒數；'
           f'下面每場連去佢第一局。戰況嗰張逐局圖每粒點都連到影片。</p>',
           '<style>' + report_charts.css("video") + '</style>']
    for i, vd in enumerate(vids):
        part = dict(data, video=vd,
                    matches=[v for v in data["matches"] if v.get("video", 0) == i])
        part["recovered"] = [r for r in data.get("recovered", [])
                             if vid_of[r["after_position"]] is vd]
        pf = dict(facts, matches=[m for v, m in zip(data["matches"], facts["matches"])
                                  if v.get("video", 0) == i])
        if len(vids) > 1:
            out.append(f'    <p class="vd-note">第 {i + 1} 段</p>')
        out.append(report_charts.video_timeline(
            pf, part, lambda t, vd=vd: _href(vd, t, lead).replace("&amp;", "&")))
    out.append('    <div class="vd-list">')
    for v, m in zip(data["matches"], facts["matches"]):
        winners = [r["winner"] for r in m["rounds"]]
        first = v["rounds"][0]["play_start_s"]
        video = vid_of[v["position"]]
        part = f'第 {v.get("video", 0) + 1} 段 ' if len(vids) > 1 else ''
        out += ['      <div class="vd-match">',
                '        <div class="vd-head">'
                f'<a class="vd-name" href="{_href(video, first, lead)}" target="_blank" '
                f'rel="noopener">m{v["position"]}</a>'
                f'<span class="vd-score">{_score(winners, players)}</span>'
                f'<span class="vd-tag">{part}{_clock(first)}</span></div>', '      </div>']
        rec = recovered.get(v["position"])
        if rec:
            ws = [r["winner"] for r in rec["rounds"]]
            t0 = rec["rounds"][0]["play_start_s"]
            out += ['      <div class="vd-match vd-rec">',
                    '        <div class="vd-head">'
                    f'<a class="vd-name" href="{_href(video, t0, lead)}" target="_blank" '
                    'rel="noopener">冇 replay 嗰場</a>'
                    f'<span class="vd-score">{_score(ws, players)}</span>'
                    f'<span class="vd-tag">{_clock(t0)} · 由影片讀返</span></div>',
                    '      </div>']
    out.append('    </div>')
    if n_rec:
        out.append('    <p class="vd-note"><strong>虛線嗰場冇 replay</strong>，每局邊個贏係由 TETR.IO '
                   '局與局之間嘅比數畫面讀出嚟。<strong>呢場唔計入呢份戰報任何一個數</strong>；'
                   'm 後面個號係 replay 嘅次序，佢之後嗰幾場當晚其實遲一場打。</p>')
    out.append(f'    <p class="vd-note">{NOTES[data["alignment"].get("kind", "frames")]}</p>')
    out += ['  </div>', '</section>']
    markup = "\n".join(out)
    bad = sorted(set(markup) & SIMPLIFIED)
    if bad:
        raise SystemExit(f"video_section: simplified glyph(s) {bad}")
    return markup


def selftest(report_dir):
    report_dir = Path(report_dir)
    facts = json.loads((report_dir / "facts.json").read_text())
    data = load(report_dir)
    if data is None:
        raise SystemExit(f"{report_dir}: no video.json to selftest against")
    check(facts, data)
    assert build(facts, report_dir) == build(facts, report_dir)

    def plant(name, f):
        d = copy.deepcopy(data)
        f(d)
        try:
            check(facts, d)
        except ValueError:
            print(f"  killed: {name}")
            return 0
        print(f"  SURVIVED: {name}")
        return 1

    def first_rec(d):
        return d["recovered"][0] if d.get("recovered") else None

    mutants = [
        ("eligible", lambda d: d.__setitem__("report_eligible", True)),
        ("drop a match", lambda d: d["matches"].pop()),
        ("drop a round", lambda d: d["matches"][0]["rounds"].pop()),
        ("wrong file", lambda d: d["matches"][0].__setitem__("file", "x.ttrm")),
        ("round overlaps previous", lambda d: d["matches"][0]["rounds"][1].__setitem__(
            "play_start_s", d["matches"][0]["rounds"][0]["play_start_s"] + 1)),
        ("swap two matches", lambda d: d["matches"].__setitem__(
            slice(0, 2), d["matches"][1::-1])),
        ("starts before the video", lambda d: d["matches"][0]["rounds"][0].__setitem__(
            "play_start_s", -1)),
        ("runs past the video's end", lambda d: d["matches"][-1]["rounds"][-1].__setitem__(
            "replay_s", 1e7)),
        ("no such video", lambda d: d["matches"][0].__setitem__("video", 9)),
        ("unknown alignment kind", lambda d: d["alignment"].__setitem__("kind", "guess")),
    ]
    if data.get("more_videos"):
        mutants.append(("back into an earlier video", lambda d: d["matches"][-1].__setitem__(
            "video", 0)))
    if first_rec(data):
        p0 = facts["players"][0]
        mutants += [
            ("flip a recovered winner", lambda d: first_rec(d)["rounds"][0].__setitem__(
                "winner", next(p for p in facts["players"]
                               if p != first_rec(d)["rounds"][0]["winner"]))),
            ("unfinished recovered match", lambda d: first_rec(d)["rounds"].pop()),
            ("recovered before its anchor", lambda d: first_rec(d)["rounds"][0].__setitem__(
                "play_start_s", 0)),
            ("unknown winner", lambda d: first_rec(d)["rounds"][0].__setitem__("winner", p0 + "x")),
            ("recovered into next match", lambda d: first_rec(d)["rounds"][-1].__setitem__(
                "end_s", 1e9)),
        ]
    survived = sum(plant(n, f) for n, f in mutants)
    if survived:
        raise SystemExit(f"video_section --selftest: {survived} mutant(s) survived")
    print(f"video_section --selftest: {len(mutants)}/{len(mutants)} killed")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--selftest":
        for rd in args[1:] or ["sessions/2026-11-05/report", "sessions/2026-09-18/report"]:
            selftest(rd)
    else:
        rd = Path(args[0])
        print(build(json.loads((rd / "facts.json").read_text()), rd) or "(no video.json)")

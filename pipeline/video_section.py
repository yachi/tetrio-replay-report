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

SCHEMA = "session-video/1"

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
    vm, fm = data["matches"], facts["matches"]
    if len(vm) != len(fm):
        raise ValueError(f"{len(vm)} video matches against {len(fm)} replay matches")
    prev_end = None
    match_span = {}
    for v, m in zip(vm, fm):
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
    video, lead = data["video"], data["alignment"]["link_lead_s"]
    players = facts["players"]
    recovered = {r["after_position"]: r for r in data.get("recovered", [])}
    n_rec = len(recovered)

    out = [CSS, '<section id="video">', '  <div class="wrap">',
           '    <div class="eyebrow">影片 · VIDEO</div>',
           '    <h2 class="section-title">每一局喺影片邊度</h2>',
           '    <p class="section-lede">成晚有<a href="'
           f'{html.escape(video["url"])}" target="_blank" rel="noopener">錄影</a>'
           f'（長 {_clock(video["duration_s"])}）。時間軸上每條色線係一局，顏色係嗰局邊個贏，'
           f'撳落去開影片嗰局，會早 {lead} 秒開始，等你睇到倒數；'
           f'下面每場連去佢第一局。戰況嗰張逐局圖每粒點都連到影片。</p>',
           '<style>' + report_charts.css("video") + '</style>',
           report_charts.video_timeline(
               facts, data, lambda t: _href(video, t, lead).replace("&amp;", "&")),
           '    <div class="vd-list">']
    for v, m in zip(data["matches"], facts["matches"]):
        winners = [r["winner"] for r in m["rounds"]]
        first = v["rounds"][0]["play_start_s"]
        out += ['      <div class="vd-match">',
                '        <div class="vd-head">'
                f'<a class="vd-name" href="{_href(video, first, lead)}" target="_blank" '
                f'rel="noopener">m{v["position"]}</a>'
                f'<span class="vd-score">{_score(winners, players)}</span>'
                f'<span class="vd-tag">{_clock(first)}</span></div>', '      </div>']
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
        out.append('    <p class="vd-note"><strong>虛線嗰場冇 replay</strong>，影片有、'
                   '匯出嘅檔案冇。佢每局邊個贏，係由 TETR.IO 局與局之間嗰個比數畫面讀出嚟，'
                   '最後一局睇結束畫面。<strong>呢場唔計入呢份戰報任何一個數</strong>：'
                   '比數、局數、每粒攻擊、claim 同 ✓ 全部淨係由 replay 嚟，'
                   '所以上面同下面講嘅「成晚」都唔包佢；m 後面個號亦係 replay 嘅次序，'
                   '佢之後嗰幾場喺當晚其實係遲一場打嘅。</p>')
    out.append('    <p class="vd-note">時間點係咁對出嚟：每個 replay 記低咗場波幾時完，'
               '再用 replay 自己每局嘅長度倒推返去，每局開始都對準影片入面倒數完、'
               '兩塊板仲係空嘅最後一格（每秒睇 4 格），每局都對得到，相差唔夠 1 秒。'
               '呢個係由影片畫面對出嚟，唔係由 replay 證出嚟，所以冇 claim 亦冇 ✓。</p>')
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
    ]
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
        selftest(args[1] if len(args) > 1 else "sessions/2026-11-05/report")
    else:
        rd = Path(args[0])
        print(build(json.loads((rd / "facts.json").read_text()), rd) or "(no video.json)")

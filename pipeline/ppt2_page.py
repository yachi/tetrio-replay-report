"""docs/ppt2-syakegohan.html — syakegohan's Puyo Puyo Tetris 2 games, measured from YouTube video.

NOT PART OF THE TETR.IO CORPUS AND NOT IN THE PROOF CHAIN. There are no replay files: every count in
`analysis/ppt2-syakegohan/games.csv` was read off video frames by two independently written
extractors (NEXT-queue shifts; cell accounting), reconciled, and spot-checked by a third reader.
Attack is COMPUTED from the clears with PPT2's attack table, never observed, so no figure here is
comparable with a TETR.IO figure. The page says all of that in its own words, and carries no claim
id, no ✓ and no `data-claim`.

Rendered by `bin/build-docs`, so `--check` byte-compares it against this renderer and the committed
CSV: the pooled figures are recomputed on every check and cannot drift from the rows they pool.
Every figure FLOORS at the printed precision (`_fl`), the repo's 約 convention, so no figure reads
higher than the data.
"""
import csv
import math
import re
from collections import defaultdict
from html import escape
from pathlib import Path

DATA_REL = "analysis/ppt2-syakegohan/games.csv"
#: cells corrected by hand from the video, each with the chain value it replaced and its source
HAND_REL = "analysis/ppt2-syakegohan/hand-edits.csv"
PAGE = "ppt2-syakegohan.html"
CHANNEL = "https://www.youtube.com/channel/UCjaIDXm6AZz1fMkBT-OU8Ag"
ME = "syakegohan"
MIN_GAMES = 10
#: seconds of lead-in before a game's first piece in each video link
LEAD_S = 3

SUMS = ("duration_s", "pieces", "lines_cleared", "attack", "garbage_cleared", "garbage_received_rows",
        "single", "double", "triple", "quad", "tss", "tsd", "tst", "tsmini", "pc")
MAXES = ("max_combo", "max_b2b")


def _hand_edits(repo):
    with open(Path(repo) / HAND_REL, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def apply_hand_edits(rows, edits):
    """Lay the video-verified hand edits over the extractor chain's rows, in place. An edit applies only
    where the chain still gives the value it was written against (`was`), or already gives `value`; any
    other chain value means the chain moved under the edit, so it raises for a review instead of
    overwriting a value nobody has looked at."""
    at = {(r["id"], r["player"]): r for r in rows}
    for e in edits:
        r = at.get((e["id"], e["player"]))
        if r is None or e["field"] not in r:
            raise ValueError(f"hand edit names no cell: {e['id']} {e['player']} {e['field']}")
        if r[e["field"]] not in (e["was"], e["value"]):
            raise ValueError(f"{e['id']} {e['player']} {e['field']}: the chain gives {r[e['field']]!r}, "
                             f"the hand edit was written against {e['was']!r}; review it in the video")
        r[e["field"]] = e["value"]
    return rows


def load(repo):
    with open(Path(repo) / DATA_REL, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    # games.csv is the chain's output with the hand edits laid over it. A rebuild that writes the chain
    # output alone silently drops them (2026-10-15 did, all 24 rows), so the page refuses to render one.
    for e in _hand_edits(repo):
        got = next((r[e["field"]] for r in rows if (r["id"], r["player"]) == (e["id"], e["player"])), None)
        if got != e["value"]:
            raise ValueError(f"{DATA_REL}: {e['id']} {e['player']} {e['field']} is {got!r}, the hand edit says "
                             f"{e['value']!r}; rebuild with python3 -m pipeline.ppt2_page --apply <chain.csv>")
    games = defaultdict(dict)
    for r in rows:
        games[r["id"]][r["player"]] = r
    for gid, g in games.items():
        if set(g) != {"p1", "p2"}:
            raise ValueError(f"{gid}: expected one p1 and one p2 row, got {sorted(g)}")
        if g["p1"]["excluded"] != g["p2"]["excluded"]:
            raise ValueError(f"{gid}: one player excluded and not the other")
        if g["p1"]["won"] == g["p2"]["won"]:
            raise ValueError(f"{gid}: both players have won={g['p1']['won']}")
    return dict(games)


def _fl(x, dp):
    """Floor `x` to `dp` decimals and print it — never reads higher than the data."""
    q = 10 ** dp
    return f"{math.floor(x * q + 1e-9) / q:.{dp}f}"


def pool(rows):
    s = defaultdict(float)
    for r in rows:
        for k in SUMS:
            s[k] += float(r[k])
        for k in MAXES:
            s[k] = max(s[k], float(r[k]))
        s["games"] += 1
        s["won"] += r["won"] == "1"
    return s


def rates(s):
    t, m = s["duration_s"], s["duration_s"] / 60
    clears = sum(s[k] for k in ("single", "double", "triple", "quad", "tss", "tsd", "tst", "tsmini"))
    tspins = s["tss"] + s["tsd"] + s["tst"]
    return {
        "PPS": s["pieces"] / t, "APM": 60 * s["attack"] / t,
        "VS": 100 * (s["attack"] + s["garbage_cleared"]) / t, "APP": s["attack"] / s["pieces"],
        "DSP": s["garbage_cleared"] / s["pieces"], "LPM": 60 * s["lines_cleared"] / t,
        "QPM": s["quad"] / m, "TSPM": tspins / m, "TSDPM": s["tsd"] / m,
        "QPCT": 100 * s["quad"] / clears, "TSPCT": 100 * tspins / clears,
        "RECV": 60 * s["garbage_received_rows"] / t, "MEAN": t / s["games"],
    }


def _video(r):
    t = max(0, math.floor(float(r["start_s"])) - LEAD_S)
    return f"https://www.youtube.com/watch?v={r['video']}&t={t}s"


def _date(dataset):
    return dataset.split("-", 1)[1]


CSS = """
*,*::before,*::after{box-sizing:border-box}
:root{--bg:#f5f6fa;--card:#fff;--ink:#12141c;--muted:#6b7080;--line:rgba(18,20,28,.12);
  --me:#0e8f9e;--opp:#7c3aed;--warn:#b45309;--accent:#0e8f9e}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0a0c12;--card:#141824;
  --ink:#eef1f8;--muted:#8f96ab;--line:rgba(255,255,255,.10);--me:#22d3ee;--opp:#a78bfa;
  --warn:#fbbf24;--accent:#22d3ee}}
:root[data-theme="dark"]{--bg:#0a0c12;--card:#141824;--ink:#eef1f8;--muted:#8f96ab;
  --line:rgba(255,255,255,.10);--me:#22d3ee;--opp:#a78bfa;--warn:#fbbf24;--accent:#22d3ee}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"PingFang HK","Hiragino Sans CNS","Noto Sans HK","Microsoft JhengHei",
    -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.65;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:clamp(2rem,6vw,4rem) 16px 5rem}
.kicker{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.75rem;letter-spacing:.14em;
  text-transform:uppercase;color:var(--muted)}
h1{font-size:clamp(1.7rem,5vw,2.6rem);line-height:1.2;margin:.5rem 0 1rem}
h2{font-size:1.05rem;margin:2.6rem 0 .9rem;padding-bottom:.5rem;border-bottom:1px solid var(--line)}
p,li{max-width:75ch}
.muted{color:var(--muted)}
.warn{border-left:3px solid var(--warn);padding:.6rem 1rem;background:var(--card);border-radius:8px}
.tw{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:12px}
table{border-collapse:collapse;width:100%;font-size:.86rem;font-variant-numeric:tabular-nums}
th,td{padding:.4rem .6rem;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
th{font-weight:600;color:var(--muted);position:sticky;top:0;background:var(--card)}
td.l,th.l{text-align:left}
tr.me td{color:var(--me);font-weight:600}
tr.small td{color:var(--muted);font-style:italic}
tr.ex td{color:var(--muted)}
tr.sep td{border-top:2px solid var(--line)}
.w{color:var(--me);font-weight:600} .lo{color:var(--opp)}
a{color:var(--accent)}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.86em}
footer{margin-top:3rem;padding-top:1.2rem;border-top:1px solid var(--line);font-size:.85rem;color:var(--muted)}
.grid{display:grid;gap:1rem;grid-template-columns:repeat(auto-fill,minmax(min(100%,260px),1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:1.1rem 1.2rem;
  text-decoration:none;color:inherit;display:block;min-width:0;transition:border-color .15s ease}
.card:hover{border-color:var(--accent)}
.card .date{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.78rem;color:var(--muted)}
.card .kind{font-size:.78rem;color:var(--warn)}
.card .kind.live{color:var(--muted)}
.card .title{font-weight:650;font-size:1.08rem;margin:.3rem 0 .1rem;overflow-wrap:anywhere}
.card .vs{display:flex;align-items:baseline;gap:.5rem;margin:.5rem 0 .3rem;flex-wrap:wrap}
.card .vs b{font-size:1.4rem;font-variant-numeric:tabular-nums}
.card .meta{font-size:.82rem;color:var(--muted)}
.card table{font-size:.8rem;margin-top:.5rem}
.card th,.card td{padding:.2rem .35rem}
.card th{position:static}
.card.small{opacity:.75}
.card.small .title,.card.small .vs,.card.small td{font-style:italic;color:var(--muted)}
.me-c{color:var(--me)} .opp-c{color:var(--opp)}
.trend{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:.8rem;
  display:grid;gap:.6rem;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr))}
.trend svg{width:100%;height:auto;display:block}
.trend .ax{stroke:var(--line)} .trend .ln{stroke:var(--me);fill:none;stroke-width:1.6}
.trend .pt{fill:var(--me);stroke:var(--me);stroke-width:1.4} .trend .pt.small{fill:var(--card)}
.trend text{fill:var(--muted);font-size:10px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.trend text.cap{fill:var(--ink);font-size:11px;font-weight:600}
nav.back{font-size:.9rem;margin-bottom:.4rem}
"""

PLAYER_COLS = [("PPS", 3), ("APM", 2), ("VS", 2), ("APP", 3), ("DSP", 3), ("LPM", 2), ("QPM", 2),
               ("TSPM", 2), ("TSDPM", 2), ("QPCT", 1), ("TSPCT", 1), ("RECV", 2)]
PLAYER_HEAD = ["PPS", "APM", "VS", "APP", "DS/粒", "LPM", "Tetris/分", "T-spin/分", "TSD/分",
               "Tetris %", "T-spin %", "食/分"]


def _player_row(name, s, cls=""):
    r = rates(s)
    cells = "".join(f"<td>{_fl(r[k], dp)}</td>" for k, dp in PLAYER_COLS)
    return (f"<tr class='{cls}'><td class='l'>{escape(name)}</td><td>{int(s['games'])}</td>"
            f"<td>{int(s['won'])}</td>{cells}<td>{int(s['pc'])}</td><td>{int(s['max_combo'])}</td>"
            f"<td>{int(s['max_b2b'])}</td><td>{_fl(r['MEAN'], 1)}</td></tr>")


PLAYER_TABLE_HEAD = ("<tr><th class='l'>玩家</th><th>局數</th><th>贏</th>"
                     + "".join(f"<th>{h}</th>" for h in PLAYER_HEAD)
                     + "<th>全消</th><th>最長 REN</th><th>最長 B2B</th><th>平均局長 (秒)</th></tr>")

GAME_HEAD = ("<tr><th class='l'>局</th><th class='l'>日期</th><th class='l'>影片</th><th class='l'>對手</th>"
             "<th class='l'>開局</th><th class='l'>贏家</th><th>局長 (秒)</th>"
             "<th>syake PPS</th><th>syake APM</th><th>syake APP</th>"
             "<th>對手 PPS</th><th>對手 APM</th><th>對手 APP</th><th class='l'>備註</th></tr>")


def _game_key(g):
    return (g["p1"]["dataset"], g["p1"]["video"], float(g["p1"]["start_s"]))


def _game_row(gid, g):
    """One row of the per-game table, with its YouTube link. ONE copy, shared by the overview's
    full list and every card page's list."""
    p1, p2 = g["p1"], g["p2"]
    ex = p1["excluded"] == "1"
    winner = f"<span class='w'>{ME}</span>" if p1["won"] == "1" else f"<span class='lo'>{escape(p2['opponent'] or '對手')}</span>"
    t = float(p1["duration_s"])

    def st(r):
        if ex:
            return "<td>—</td><td>—</td><td>—</td>"
        return (f"<td>{_fl(float(r['pieces']) / t, 3)}</td><td>{_fl(60 * float(r['attack']) / t, 2)}</td>"
                f"<td>{_fl(float(r['attack']) / float(r['pieces']), 3)}</td>")
    note = "；".join(sorted({x for x in (p1["reason"], p2["reason"]) if x})) if ex else ""
    return (
        f"<tr class='{'ex' if ex else ''}'><td class='l'><code>{escape(gid)}</code></td>"
        f"<td class='l'>{escape(_date(p1['dataset']))}</td>"
        f"<td class='l'><a href='{escape(_video(p1))}' target='_blank' rel='noopener'>"
        f"{escape(p1['video'])} @ {int(float(p1['start_s']) // 60)}:{int(float(p1['start_s']) % 60):02d}</a></td>"
        f"<td class='l'>{escape(p2['opponent'] or '（冇讀名）')}</td><td class='l'>{escape(p1['opener'] or '—')}</td>"
        f"<td class='l'>{winner}</td><td>{_fl(t, 1)}</td>{st(p1)}{st(p2)}"
        f"<td class='l'>{escape('剔除：' + note) if ex else ''}</td></tr>")


def _warn_box(small):
    """The 點樣讀呢版 box. ONE copy: the overview and every card page print it, so the caveats about
    how these numbers were read off video cannot drift apart between pages. `small` is the HTML list
    of opponents under MIN_GAMES that the page is about."""
    return (
        "<div class='warn'><p><strong>點樣讀呢版：</strong></p><ul>"
        "<li><strong>唔係 TETR.IO 數字。</strong>PPT2 嘅攻擊表同 TETR.IO 唔同，APM、VS、APP 唔可以同"
        "呢個網站其他戰報比較。</li>"
        "<li><strong>冇 replay 檔。</strong>每個數都係由影片逐格讀出嚟：兩個獨立寫嘅抽取器"
        "（一個睇 NEXT 列移位，一個數格仔），對數之後再由第三個讀者抽查。冇 claim 編號、冇 ✓。</li>"
        "<li><strong>攻擊係計出嚟，唔係睇到。</strong>由每次清行嘅種類用 PPT2 攻擊表計"
        "（B2B、REN、全消照計），抵銷咗嘅攻擊喺片入面睇唔到。全消同其他加成點疊係假設。</li>"
        "<li><strong>已知缺陷：最尾一粒。</strong>KO 以輸家個板開始傾側嗰格計，比爆頂遲大約半秒；"
        "贏家喺 KO 格或之前鎖低嘅方塊同清行都計。KO 畫面好多時遮住 T-spin 字幕，所以補返嘅清行"
        "逐局睇片（字幕同分數變化）先定種類。如果贏家最後一粒冇消行、又啱啱喺 KO 嗰格鎖低，"
        "抽取器睇唔到；睇片搵到兩局，已經人手改正，其他局最多少計一粒。"
        "局長由第一粒到 KO，同睇片量度相差唔多過 0.11 秒。</li>"
        f"<li>局數少過 {MIN_GAMES} 嘅對手用斜體灰色：{small or '冇'}。只當例子睇，唔好拎嚟比較。</li>"
        "<li>所有比率都係「總和對總和」（例如 PPS = 總粒數 ÷ 總秒數），數字一律向下取。</li>"
        "</ul></div>")


def render(games):
    inc = {k: g for k, g in games.items() if g["p1"]["excluded"] == "0"}
    by_opp = defaultdict(list)
    for gid, g in inc.items():
        by_opp[g["p2"]["opponent"]].append(g)
    if "" in by_opp:
        raise ValueError(f"included games with no opponent name: {[g['p1']['id'] for g in by_opp['']]}")
    order = sorted(by_opp, key=lambda o: (-len(by_opp[o]), o))
    me_all = pool(g["p1"] for g in inc.values())
    opp_all = pool(g["p2"] for g in inc.values())
    videos = sorted({(g["p1"]["dataset"], g["p1"]["video"]) for g in games.values()})
    n_small = [o for o in order if len(by_opp[o]) < MIN_GAMES]

    t1 = [PLAYER_TABLE_HEAD, _player_row(f"{ME}（全部）", me_all, "me"), _player_row("全部對手", opp_all)]
    for i, o in enumerate(order):
        cls = ("small " if len(by_opp[o]) < MIN_GAMES else "") + ("sep" if i == 0 else "")
        t1.append(_player_row(o, pool(g["p2"] for g in by_opp[o]), cls))

    t2 = ["<tr><th class='l'>對手</th><th>局數</th><th>syakegohan 戰績</th>"
          "<th>syake PPS</th><th>對手 PPS</th><th>syake APM</th><th>對手 APM</th>"
          "<th>syake VS</th><th>對手 VS</th><th>syake APP</th><th>對手 APP</th></tr>"]
    for o in order:
        a, b = pool(g["p1"] for g in by_opp[o]), pool(g["p2"] for g in by_opp[o])
        ra, rb = rates(a), rates(b)
        cls = "small" if len(by_opp[o]) < MIN_GAMES else ""
        t2.append(f"<tr class='{cls}'><td class='l'>{escape(o)}</td><td>{int(a['games'])}</td>"
                  f"<td>{int(a['won'])}–{int(b['won'])}</td>"
                  + "".join(f"<td>{_fl(ra[k], dp)}</td><td>{_fl(rb[k], dp)}</td>"
                            for k, dp in (("PPS", 3), ("APM", 2), ("VS", 2), ("APP", 3)))
                  + "</tr>")

    t3 = [GAME_HEAD] + [_game_row(gid, games[gid]) for gid in sorted(games, key=lambda k: _game_key(games[k]))]

    vids = "".join(
        f"<li><code>{escape(_date(d))}</code> · {'直播' if d.startswith('stream') else '上載'} · "
        f"<a href='https://www.youtube.com/watch?v={escape(v)}' target='_blank' rel='noopener'>{escape(v)}</a> · "
        f"{sum(1 for g in games.values() if g['p1']['video'] == v)} 局</li>" for d, v in videos)
    small = "、".join(f"{escape(o)}（{len(by_opp[o])} 局）" for o in n_small)
    n_ex = len(games) - len(inc)
    ra, rb = rates(me_all), rates(opp_all)

    return "".join([
        '<!doctype html><html lang="zh-HK"><head><meta charset="utf-8">',
        "<title>syakegohan PPT2 數據</title>",
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="description" content="しゃけごはん（syakegohan）喺 ぷよぷよテトリス２ 嘅 Tetris 對戰數據，'
        '由 YouTube 影片逐格抽出，每一局都有影片連結。">',
        f"<style>{CSS}</style></head><body><div class='wrap'>",
        "<p class='kicker'>PUYO PUYO TETRIS 2 · 影片抽取 · 唔喺證明鏈入面</p>",
        "<h1>syakegohan（しゃけごはん）PPT2 對戰數據</h1>",
        f"<p>由 <a href='{CHANNEL}' target='_blank' rel='noopener'>syakegohan 個 YouTube 頻道</a> "
        f"{len(videos)} 條片入面搵到 <strong>{len(games)}</strong> 局 Tetris 對 Tetris，"
        f"計入 <strong>{len(inc)}</strong> 局（剔除 {n_ex} 局）。syakegohan 戰績 "
        f"<strong>{int(me_all['won'])}–{int(opp_all['won'])}</strong>，PPS {_fl(ra['PPS'], 3)} 對 "
        f"{_fl(rb['PPS'], 3)}、APM {_fl(ra['APM'], 2)} 對 {_fl(rb['APM'], 2)}、APP {_fl(ra['APP'], 3)} 對 "
        f"{_fl(rb['APP'], 3)}。每一局喺最尾個表都有影片連結，撳落去直接跳去嗰局開始之前 {LEAD_S} 秒。</p>",
        _warn_box(small),
        _cards_section(cards(games)),
        "<h2>每個玩家（只計入選嘅局）</h2><div class='tw'><table>", "".join(t1), "</table></div>",
        "<p class='muted'>DS/粒 = 每粒清走幾多行垃圾；食/分 = 每分鐘有幾多行垃圾真係落咗喺自己個板；"
        "Tetris % 同 T-spin % 係佔所有清行次數嘅百分比；T-spin 唔計 Mini。</p>",
        "<h2>syakegohan 對每個對手</h2><div class='tw'><table>", "".join(t2), "</table></div>",
        f"<h2>逐局（{len(games)} 局，連影片）</h2><div class='tw'><table>", "".join(t3), "</table></div>",
        "<h2>影片</h2><ul>", vids, "</ul>",
        _footer(False),
        "</div></body></html>",
    ])


# ---- one card per (date, opponent) --------------------------------------------------------------
#: every card page is docs/<CARD_PREFIX><YYYY-MM-DD>-<n>.html; bin/build-docs treats any other file
#: under that prefix as drift. The overview PAGE does not match the prefix (no dash after it).
CARD_PREFIX = "ppt2-syakegohan-"
UNKNOWN = "對手未知"
KIND = {"stream": "直播", "upload": "上載日期（唔一定係打嘅日子）"}
_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")


def _kind(dataset):
    k = dataset.split("-", 1)[0]
    if k not in KIND or not _ISO.fullmatch(_date(dataset)):
        raise ValueError(f"dataset {dataset!r} is not stream-YYYY-MM-DD or upload-YYYY-MM-DD")
    return k


def cards(games):
    """The games grouped by (dataset, opponent), ordered by date then by the group's first game in
    its video; `n` is the 1-based position within its DATE, so a stream and an upload posted the same
    day share one numbering and never one filename. Nothing about the groups is typed here: they are
    whatever games.csv holds when this runs."""
    groups = defaultdict(list)
    for gid, g in games.items():
        groups[(g["p1"]["dataset"], g["p2"]["opponent"])].append(gid)
    out = []
    for (ds, opp), gids in groups.items():
        _kind(ds)
        gids.sort(key=lambda k: _game_key(games[k]))
        inc = [k for k in gids if games[k]["p1"]["excluded"] == "0"]
        out.append({"dataset": ds, "date": _date(ds), "kind": _kind(ds), "opponent": opp,
                    "label": opp or UNKNOWN, "gids": gids, "inc": inc,
                    "me": pool(games[k]["p1"] for k in inc), "opp": pool(games[k]["p2"] for k in inc),
                    "first": float(games[gids[0]]["p1"]["start_s"])})
    out.sort(key=lambda c: (c["date"], c["first"], c["dataset"], c["opponent"]))
    per_date = defaultdict(int)
    for c in out:
        per_date[c["date"]] += 1
        c["n"] = per_date[c["date"]]
        c["page"] = f"{CARD_PREFIX}{c['date']}-{c['n']}.html"
        c["small"] = len(c["inc"]) < MIN_GAMES
    return out


def _r(c, side):
    return rates(c[side]) if c["inc"] else None


def _cell(r, k, dp):
    return _fl(r[k], dp) if r else "—"


CARD_METRICS = (("PPS", 3), ("APM", 2), ("APP", 3))


def _card_html(c, href_prefix=""):
    me, op = _r(c, "me"), _r(c, "opp")
    won = int(c["me"]["won"])
    n_inc, n_ex = len(c["inc"]), len(c["gids"]) - len(c["inc"])
    rows = "".join(
        f"<tr><td class='l {cls}'>{escape(who)}</td>"
        + "".join(f"<td>{_cell(r, k, dp)}</td>" for k, dp in CARD_METRICS) + "</tr>"
        for who, r, cls in ((ME, me, "me-c"), ("對手", op, "opp-c")))
    return (
        f"<a class='card{' small' if c['small'] else ''}' href='{escape(href_prefix + c['page'])}'>"
        f"<div class='date'>{escape(c['date'])} · #{c['n']}</div>"
        f"<div class='kind{' live' if c['kind'] == 'stream' else ''}'>{escape(KIND[c['kind']])}</div>"
        f"<div class='title'>{escape(c['label'])}</div>"
        f"<div class='vs'><span class='me-c'>{ME}</span><b>{won}–{n_inc - won}</b>"
        f"<span class='opp-c'>{escape(c['label'])}</span></div>"
        f"<div class='meta'>計入 {n_inc} 局 · 剔除 {n_ex} 局</div>"
        "<table><tr><th class='l'></th>" + "".join(f"<th>{k}</th>" for k, _ in CARD_METRICS)
        + "</tr>" + rows + "</table></a>")


def _trend_svg(cs, key, dp, caption):
    """One small line chart of syakegohan's `key` per card, in date order. Inline SVG, no library;
    a card with no included game has no point. Hollow points are cards under MIN_GAMES."""
    pts = [(i, rates(c["me"])[key], c) for i, c in enumerate(cs) if c["inc"]]
    W, H, L, R, T, B = 360, 150, 40, 10, 22, 22
    if not pts:
        return ""
    vals = [v for _, v, _ in pts]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.12 or 0.05 * (hi or 1)
    lo, hi = lo - pad, hi + pad
    n = max(len(cs) - 1, 1)

    def x(i):
        return L + (W - L - R) * i / n

    def y(v):
        return T + (H - T - B) * (hi - v) / (hi - lo)
    path = " ".join(f"{'M' if j == 0 else 'L'}{x(i):.1f},{y(v):.1f}" for j, (i, v, _) in enumerate(pts))
    dots = "".join(
        f"<circle class='pt{' small' if c['small'] else ''}' cx='{x(i):.1f}' cy='{y(v):.1f}' r='3.2'>"
        f"<title>#{i + 1} {escape(c['date'])} {escape(c['label'])}：{key} {_fl(v, dp)}"
        f"（計入 {len(c['inc'])} 局）</title></circle>" for i, v, c in pts)
    ticks = "".join(f"<text x='{x(i):.1f}' y='{H - 6}' text-anchor='middle'>{i + 1}</text>"
                    for i in range(len(cs)))
    return (
        f"<svg viewBox='0 0 {W} {H}' role='img' aria-label='{escape(caption)}'>"
        f"<text class='cap' x='{L}' y='13'>{escape(caption)}</text>"
        f"<line class='ax' x1='{L}' y1='{H - B}' x2='{W - R}' y2='{H - B}'/>"
        f"<line class='ax' x1='{L}' y1='{T}' x2='{L}' y2='{H - B}'/>"
        f"<text x='{L - 4}' y='{y(max(vals)) + 3:.1f}' text-anchor='end'>{_fl(max(vals), dp)}</text>"
        f"<text x='{L - 4}' y='{y(min(vals)) + 3:.1f}' text-anchor='end'>{_fl(min(vals), dp)}</text>"
        f"<path class='ln' d='{path}'/>{dots}{ticks}</svg>")


def _cards_section(cs):
    grid = "".join(_card_html(c) for c in cs)
    rows = []
    for i, c in enumerate(cs):
        me, op = _r(c, "me"), _r(c, "opp")
        won = int(c["me"]["won"])
        rows.append(
            f"<tr class='{'small' if c['small'] else ''}'><td>{i + 1}</td>"
            f"<td class='l'><a href='{escape(c['page'])}'>{escape(c['date'])}</a></td>"
            f"<td class='l'>{'直播' if c['kind'] == 'stream' else '上載'}</td>"
            f"<td class='l'>{escape(c['label'])}</td><td>{len(c['inc'])}</td>"
            f"<td>{won}–{len(c['inc']) - won}</td>"
            f"<td>{_cell(me, 'PPS', 3)}</td><td>{_cell(me, 'APP', 3)}</td>"
            f"<td>{_cell(op, 'PPS', 3)}</td><td>{_cell(op, 'APP', 3)}</td></tr>")
    return "".join([
        "<h2>每晚每個對手</h2>",
        "<p class='muted'>一張卡 = 同一日、同一個對手打嘅局（上載嗰啲可以橫跨幾條片，逐局表按片排）。日期由資料集嚟：直播係直播當日；"
        "上載係條片上載嘅日子，唔一定係打嘅日子。局數少過 "
        f"{MIN_GAMES} 嘅卡用斜體灰色。PPS、APM、APP 一樣係總和對總和、向下取。</p>",
        f"<div class='grid'>{grid}</div>",
        "<h2>syakegohan 逐張卡嘅走勢</h2>",
        "<div class='trend'>", _trend_svg(cs, "APP", 3, f"{ME} APP（每粒攻擊）"),
        _trend_svg(cs, "PPS", 3, f"{ME} PPS（每秒粒數）"), "</div>",
        "<p class='muted'>橫軸係卡嘅次序（按日期），號碼對返下面個表；空心點係局數少過 "
        f"{MIN_GAMES} 嘅卡；冇計入局嘅卡冇點。唔同對手、唔同日子，所以呢條線唔係「進步」嘅證據。</p>",
        "<div class='tw'><table><tr><th>#</th><th class='l'>日期</th><th class='l'>種類</th>"
        "<th class='l'>對手</th><th>計入</th><th>syakegohan 戰績</th><th>syake PPS</th><th>syake APP</th>"
        "<th>對手 PPS</th><th>對手 APP</th></tr>", "".join(rows), "</table></div>",
    ])


def _footer(back_overview):
    return (
        "<footer><p>PPT2 攻擊表：<a href='https://tetris.wiki/Puyo_Puyo_Tetris'>tetris.wiki/Puyo_Puyo_Tetris</a>；"
        "REN 加成：<a href='https://howtotetris.com/combos'>howtotetris.com/combos</a>。</p>"
        f"<p>數據：<code>{DATA_REL}</code>；由 <code>pipeline/ppt2_page.py</code> 生成，"
        "<code>bin/build-docs --check</code> 每次都會重新計過再逐 byte 比較。影片版權屬原作者，"
        "呢版只連去 YouTube，冇轉載任何畫面。</p>"
        + (f"<p><a href='{PAGE}'>← 返 syakegohan PPT2 總覽</a></p>" if back_overview else "")
        + "<p><a href='index.html'>← 返主頁</a></p></footer>")


def render_card(games, c):
    me, op = _r(c, "me"), _r(c, "opp")
    won = int(c["me"]["won"])
    n_inc, n_ex = len(c["inc"]), len(c["gids"]) - len(c["inc"])
    small = f"{escape(c['label'])}（{n_inc} 局）" if c["small"] else ""
    if c["inc"]:
        figures = (f"syakegohan 戰績 <strong>{won}–{n_inc - won}</strong>，PPS {_fl(me['PPS'], 3)} 對 "
                   f"{_fl(op['PPS'], 3)}、APM {_fl(me['APM'], 2)} 對 {_fl(op['APM'], 2)}、APP "
                   f"{_fl(me['APP'], 3)} 對 {_fl(op['APP'], 3)}。")
        table = ("<h2>呢張卡嘅每個玩家（只計入選嘅局）</h2><div class='tw'><table>" + PLAYER_TABLE_HEAD
                 + _player_row(ME, c["me"], "me") + _player_row(c["label"], c["opp"], "small" if c["small"] else "")
                 + "</table></div>")
    else:
        figures = "呢張卡冇一局計入，所以冇戰績、冇比率。"
        table = ""
    videos = sorted({games[k]["p1"]["video"] for k in c["gids"]})
    vids = "、".join(f"<a href='https://www.youtube.com/watch?v={escape(v)}' target='_blank' rel='noopener'>"
                    f"{escape(v)}</a>" for v in videos)
    title = f"syakegohan 對 {c['label']} · {c['date']}" + ("（上載日期）" if c["kind"] == "upload" else "")
    return "".join([
        '<!doctype html><html lang="zh-HK"><head><meta charset="utf-8">',
        f"<title>{escape(title)} · PPT2</title>",
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f'<meta name="description" content="{escape(title)}：PPT2 對戰數據，由 YouTube 影片逐格抽出。">',
        f"<style>{CSS}</style></head><body><div class='wrap'>",
        f"<nav class='back'><a href='{PAGE}'>← syakegohan PPT2 總覽</a></nav>",
        "<p class='kicker'>PUYO PUYO TETRIS 2 · 影片抽取 · 唔喺證明鏈入面</p>",
        f"<h1>{escape(title)}</h1>",
        f"<p><strong>{escape(c['date'])}</strong> · {escape(KIND[c['kind']])} · 影片 {vids}。"
        f"呢張卡有 <strong>{len(c['gids'])}</strong> 局，計入 <strong>{n_inc}</strong> 局（剔除 {n_ex} 局）。"
        f"{figures}每一局喺下面個表都有影片連結，撳落去直接跳去嗰局開始之前 {LEAD_S} 秒。</p>",
        _warn_box(small),
        table,
        f"<h2>逐局（{len(c['gids'])} 局，連影片）</h2><div class='tw'><table>", GAME_HEAD,
        "".join(_game_row(k, games[k]) for k in c["gids"]), "</table></div>",
        _footer(True),
        "</div></body></html>",
    ])


def render_all(games):
    """{docs file name: html} for the overview and every card page — what bin/build-docs publishes,
    and the whole of it: any other docs/ppt2-syakegohan-*.html is drift."""
    out = {PAGE: render(games)}
    for c in cards(games):
        if c["page"] in out:
            raise ValueError(f"two cards render {c['page']}")
        out[c["page"]] = render_card(games, c)
    return out


def card(games):
    inc = [g for g in games.values() if g["p1"]["excluded"] == "0"]
    won = sum(g["p1"]["won"] == "1" for g in inc)
    return {"href": PAGE, "games": len(inc), "won": won, "lost": len(inc) - won}


def _main(argv):
    """`--apply <chain.csv>`: write games.csv as the extractor chain's output with the hand edits laid
    over it. The chain itself lives outside the repo; this is the one step of the rebuild that is in it."""
    if len(argv) != 2 or argv[0] != "--apply":
        raise SystemExit("usage: python3 -m pipeline.ppt2_page --apply <chain games.csv>")
    repo = Path(__file__).resolve().parent.parent
    with open(argv[1], encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        cols = list(reader.fieldnames or ())
    apply_hand_edits(rows, _hand_edits(repo))
    with open(repo / DATA_REL, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    load(repo)


if __name__ == "__main__":
    import sys
    _main(sys.argv[1:])

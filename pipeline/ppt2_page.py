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
from collections import defaultdict
from html import escape
from pathlib import Path

DATA_REL = "analysis/ppt2-syakegohan/games.csv"
PAGE = "ppt2-syakegohan.html"
CHANNEL = "https://www.youtube.com/channel/UCjaIDXm6AZz1fMkBT-OU8Ag"
ME = "syakegohan"
MIN_GAMES = 10
#: seconds of lead-in before a game's first piece in each video link
LEAD_S = 3

SUMS = ("duration_s", "pieces", "lines_cleared", "attack", "garbage_cleared", "garbage_received_rows",
        "single", "double", "triple", "quad", "tss", "tsd", "tst", "tsmini", "pc")
MAXES = ("max_combo", "max_b2b")


def load(repo):
    with open(Path(repo) / DATA_REL, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
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

    head = ("<tr><th class='l'>玩家</th><th>局數</th><th>贏</th>"
            + "".join(f"<th>{h}</th>" for h in PLAYER_HEAD)
            + "<th>全消</th><th>最長 REN</th><th>最長 B2B</th><th>平均局長 (秒)</th></tr>")
    t1 = [head, _player_row(f"{ME}（全部）", me_all, "me"), _player_row("全部對手", opp_all)]
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

    t3 = ["<tr><th class='l'>局</th><th class='l'>日期</th><th class='l'>影片</th><th class='l'>對手</th>"
          "<th class='l'>開局</th><th class='l'>贏家</th><th>局長 (秒)</th>"
          "<th>syake PPS</th><th>syake APM</th><th>syake APP</th>"
          "<th>對手 PPS</th><th>對手 APM</th><th>對手 APP</th><th class='l'>備註</th></tr>"]
    for gid in sorted(games, key=lambda k: (games[k]["p1"]["dataset"], float(games[k]["p1"]["start_s"]))):
        g = games[gid]
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
        t3.append(
            f"<tr class='{'ex' if ex else ''}'><td class='l'><code>{escape(gid)}</code></td>"
            f"<td class='l'>{escape(_date(p1['dataset']))}</td>"
            f"<td class='l'><a href='{escape(_video(p1))}' target='_blank' rel='noopener'>"
            f"{escape(p1['video'])} @ {int(float(p1['start_s']) // 60)}:{int(float(p1['start_s']) % 60):02d}</a></td>"
            f"<td class='l'>{escape(p2['opponent'] or '（冇讀名）')}</td><td class='l'>{escape(p1['opener'] or '—')}</td>"
            f"<td class='l'>{winner}</td><td>{_fl(t, 1)}</td>{st(p1)}{st(p2)}"
            f"<td class='l'>{escape('剔除：' + note) if ex else ''}</td></tr>")

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
        "<div class='warn'><p><strong>點樣讀呢版：</strong></p><ul>"
        "<li><strong>唔係 TETR.IO 數字。</strong>PPT2 嘅攻擊表同 TETR.IO 唔同，APM、VS、APP 唔可以同"
        "呢個網站其他戰報比較。</li>"
        "<li><strong>冇 replay 檔。</strong>每個數都係由影片逐格讀出嚟：兩個獨立寫嘅抽取器"
        "（一個睇 NEXT 列移位，一個數格仔），對數之後再由第三個讀者抽查。冇 claim 編號、冇 ✓。</li>"
        "<li><strong>攻擊係計出嚟，唔係睇到。</strong>由每次清行嘅種類用 PPT2 攻擊表計"
        "（B2B、REN、全消照計），抵銷咗嘅攻擊喺片入面睇唔到。全消同其他加成點疊係假設。</li>"
        "<li><strong>已知缺陷：最後一下清行可能漏咗。</strong>抽查 6 局，有 2 局（i033、j008）"
        "漏咗贏嗰下嘅清行，因為記錄嘅完結時間早咗少少。呢個會令贏家嘅攻擊偏低。</li>"
        f"<li>局數少過 {MIN_GAMES} 嘅對手用斜體灰色：{small or '冇'}。只當例子睇，唔好拎嚟比較。</li>"
        "<li>所有比率都係「總和對總和」（例如 PPS = 總粒數 ÷ 總秒數），數字一律向下取。</li>"
        "</ul></div>",
        "<h2>每個玩家（只計入選嘅局）</h2><div class='tw'><table>", "".join(t1), "</table></div>",
        "<p class='muted'>DS/粒 = 每粒清走幾多行垃圾；食/分 = 每分鐘有幾多行垃圾真係落咗喺自己個板；"
        "Tetris % 同 T-spin % 係佔所有清行次數嘅百分比；T-spin 唔計 Mini。</p>",
        "<h2>syakegohan 對每個對手</h2><div class='tw'><table>", "".join(t2), "</table></div>",
        f"<h2>逐局（{len(games)} 局，連影片）</h2><div class='tw'><table>", "".join(t3), "</table></div>",
        "<h2>影片</h2><ul>", vids, "</ul>",
        "<footer><p>PPT2 攻擊表：<a href='https://tetris.wiki/Puyo_Puyo_Tetris'>tetris.wiki/Puyo_Puyo_Tetris</a>；"
        "REN 加成：<a href='https://howtotetris.com/combos'>howtotetris.com/combos</a>。</p>"
        f"<p>數據：<code>{DATA_REL}</code>；由 <code>pipeline/ppt2_page.py</code> 生成，"
        "<code>bin/build-docs --check</code> 每次都會重新計過再逐 byte 比較。影片版權屬原作者，"
        "呢版只連去 YouTube，冇轉載任何畫面。</p>"
        "<p><a href='index.html'>← 返主頁</a></p></footer>",
        "</div></body></html>",
    ])


def card(games):
    inc = [g for g in games.values() if g["p1"]["excluded"] == "0"]
    won = sum(g["p1"]["won"] == "1" for g in inc)
    return {"href": PAGE, "games": len(inc), "won": won, "lost": len(inc) - won}

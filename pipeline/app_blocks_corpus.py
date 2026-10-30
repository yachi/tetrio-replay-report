"""Blocks 5, 6 of 每粒攻擊 — the two CORPUS blocks. Contract: pipeline/app_section.py.

    break_even(ctx)  block 5  APP 差 -> 贏局機會: every round of the corpus AS OF THIS REPORT'S DATE
                              in which both players placed >= MIN_PIECES pieces, binned by
                              (players[0] APP - players[1] APP) in steps of 0.05 (clamped to
                              +/-0.30), players[0]'s round-win rate per bin, the interpolated 50%
                              crossing (打和線) and the win rate at equal APP.
    trend(ctx)       block 6  每晚嘅 APP: each player's session APP for every session up to and
                              including this one, the gap between them shaded, this night marked.

The corpus is `app_common.corpus(ctx)` — sessions/*/report/facts.json dated <= ctx["date"], so an
old report does not move when a new session lands. Player order is not stable across files, so
every corpus figure is keyed by USERNAME (this report's players[0] / players[1]); a session whose
player set differs is skipped and counted. Both blocks return None when ctx["date"] is None, and
break_even when no round qualifies, trend when fewer than two sessions do.

Neither block is ever badged: these are corpus measurements, not proved claims, and APP and
winning are correlated, not cause and effect. All arithmetic deciding a bin, a crossing, an order
or a rank is exact (fractions / cross-multiplied integers); floats appear only as SVG coordinates.
Every printed decimal goes through app_svg.num / rate / pct with a rule and a site name.
"""
from fractions import Fraction

from pipeline.app_common import P_CLASS, SCROLL_HINT, block, corpus, is_corpus_session, pname
from pipeline.app_svg import (Scale, axis_label, axis_line, coord, el, esc, grid_y, num, pct,
                              rate, svg, title)

SITE = "app_blocks_corpus"
EYEBROW = "每粒攻擊 · 成個 corpus"
W = 720

MIN_PIECES = 20            # a round counts for the curve only if BOTH players placed this many
BIN_STEPS = 20             # bins per 1.0 of APP difference, i.e. 0.05 wide
CLAMP = 6                  # bin index clamp: +/-6 steps = +/-0.30


# ------------------------------------------------------------------ helpers

def _chart(svg_markup):
    return f'<div class="ap-chart">{svg_markup}</div>' + SCROLL_HINT


def _tspan(text, i, bold=False):
    # `#app .ap-svg text` sets a fill that outranks `#app .ap-f1`; a tspan is not matched by it.
    return el("tspan", {"class": f"ap-f{i + 1}", "font-weight": 700 if bold else None}, text=text)


def _note(text_html):
    return f"<b>點睇：</b>{text_html}"


def _frac(q, dp, site, signed=True):
    """A Fraction printed at `dp` places with its MAGNITUDE floored and the sign re-applied, so a
    negative 約 figure never overstates its size (flooring -0.0332 toward -inf would print
    -0.034); an explicit + for non-negative values."""
    s = rate(abs(q.numerator), q.denominator, dp, site=site)
    if q < 0:
        return "-" + s
    return ("+" + s) if signed else s


def _bin_label(k, site):
    v = num(k * 1000 // BIN_STEPS, 2, site=site)
    v = ("+" + v) if k > 0 else v
    if k == -CLAMP:
        return "≤" + v
    if k == CLAMP:
        return "≥" + v
    return v


def _sessions(ctx):
    """[(date, facts)] of the corpus sessions whose players are exactly this report's, and the
    count skipped."""
    want = set(ctx["players"])
    keep, skipped = [], 0
    for s in corpus(ctx):
        if set(s["facts"]["players"]) == want:
            keep.append((s["date"], s["facts"]))
        else:
            skipped += 1
    return keep, skipped


def _session_totals(facts, names):
    """[(attack, pieces)] per name over every round of the session."""
    out = []
    for n in names:
        a = p = 0
        for m in facts["matches"]:
            for r in m["rounds"]:
                s = r["players"][n]
                a += s["garbage_attack"]
                p += s["pieces"]
        out.append((a, p))
    return out


# ------------------------------------------------------------------ block 5

def _bins(ctx):
    """{k: [wins of players[0], rounds]} over qualifying corpus rounds, and the totals."""
    names = ctx["players"]
    sessions, skipped = _sessions(ctx)
    bins = {}
    for _, facts in sessions:
        for m in facts["matches"]:
            for r in m["rounds"]:
                s0, s1 = r["players"][names[0]], r["players"][names[1]]
                if s0["pieces"] < MIN_PIECES or s1["pieces"] < MIN_PIECES:
                    continue
                diff = (Fraction(s0["garbage_attack"], s0["pieces"])
                        - Fraction(s1["garbage_attack"], s1["pieces"]))
                k = int((diff * BIN_STEPS + Fraction(1, 2)).__floor__())
                k = max(-CLAMP, min(CLAMP, k))
                b = bins.setdefault(k, [0, 0])
                b[0] += 1 if r["winner"] == names[0] else 0
                b[1] += 1
    return dict(sorted(bins.items())), len(sessions), skipped


def _crossing(bins):
    """The interpolated APP difference at which players[0]'s win rate crosses 50% going UP, as a
    Fraction; of several, the one nearest zero. None when the curve never crosses upward."""
    ks = list(bins)
    half = Fraction(1, 2)
    best = None
    for a, b in zip(ks, ks[1:]):
        pa = Fraction(bins[a][0], bins[a][1])
        pb = Fraction(bins[b][0], bins[b][1])
        if pa < half <= pb:
            x = Fraction(a, BIN_STEPS) + (half - pa) / (pb - pa) * Fraction(b - a, BIN_STEPS)
            if best is None or abs(x) < abs(best):
                best = x
    return best


def break_even(ctx):
    if not ctx["date"]:
        return None
    bins, n_sessions, skipped = _bins(ctx)
    if not bins:
        return None
    site = f"{SITE}.break_even"
    total = sum(n for _, n in bins.values())
    cross = _crossing(bins)

    H, L, R, T, B = 300, 52, 20, 18, 50
    sx = Scale(-CLAMP, CLAMP, L + 18, W - R - 18)   # inset: the end dots clear the y labels
    sy = Scale(0, 1, H - B, T)
    parts = []
    for v in (0, 250, 500, 750, 1000):
        y = sy(v / 1000)
        parts.append(el("line", {"class": "ap-ax" if v == 500 else "ap-grid",
                                 "x1": L, "x2": W - R, "y1": y, "y2": y}))
        parts.append(el("text", {"class": "ap-tick", "x": L - 6, "y": y + 4, "text-anchor": "end"},
                        text=num(v * 100, 0, site=site) + "%"))
    for k in range(-CLAMP, CLAMP + 1):
        parts.append(el("text", {"class": "ap-tick", "x": sx(k), "y": H - B + 16,
                                 "text-anchor": "middle"}, text=_bin_label(k, site)))
    parts.append(el("line", {"class": "ap-ax", "x1": sx(0), "x2": sx(0), "y1": T, "y2": H - B}))
    parts.append(axis_label((L + W - R) / 2, H - 10,
                            f"{ctx['players'][0]} APP − {ctx['players'][1]} APP（嗰局）"))
    parts.append(axis_label(14, (T + H - B) / 2, f"{ctx['players'][0]} 贏局率", rotate=True))

    pts = [(sx(k), sy(w / n)) for k, (w, n) in bins.items()]
    d = "".join(("M" if i == 0 else "L") + f"{coord(x)} {coord(y)}" for i, (x, y) in enumerate(pts))
    parts.append(el("path", {"class": "ap-s1", "d": d, "fill": "none", "stroke-width": 2.5}))
    biggest = max(n for _, n in bins.values())
    for k, (w, n) in bins.items():
        r = 3 + 6 * (n / biggest) ** 0.5
        tip = (f"{_bin_label(k, site)}：{w} / {n} 局 {ctx['players'][0]} 贏"
               f"（{pct(w, n, 1, site=site)}%）")
        parts.append(el("circle", {"class": "ap-f1", "cx": sx(k), "cy": sy(w / n), "r": r,
                                   "opacity": 0.85}, title(tip)))
    if cross is not None:
        cx = sx(float(cross) * BIN_STEPS)
        parts.append(el("line", {"class": "ap-ref", "x1": cx, "x2": cx, "y1": T, "y2": H - B,
                                 "stroke-width": 1.5}))
        # an S-curve rising through 50% at the crossing leaves the corner below-right of the
        # line empty (below-left when the line is in the right half), so the label goes there,
        # just above the x axis, with a halo in case a dot still reaches it
        left = cx > (L + W - R) / 2
        parts.append(el("text", {"class": "ap-halo", "x": cx - 6 if left else cx + 6,
                                 "y": H - B - 8, "text-anchor": "end" if left else "start"},
                        text="打和線 " + _frac(cross, 3, site)))
    chart = _chart(svg(W, H, parts, "APP 差同贏局率：成個 corpus 每局分組"))

    p0, p1 = pname(ctx, 0), pname(ctx, 1)
    lede = (f"截至呢晚嘅 {n_sessions} 個 session、{total} 局（兩個人都落咗 {MIN_PIECES} 粒或以上），"
            f"按嗰局 {p0} APP 減 {p1} APP 分組（每格 0.05，兩邊去到 ±0.30 為止），"
            f"睇每組入面 {p0} 贏咗幾多成。點越大，嗰組局數越多。")
    if skipped:
        lede += f"另外有 {skipped} 個 session 唔係呢兩個人對打，冇計。"
    body = f'<p class="ap-sub">{lede}</p>{chart}'

    sents = []
    if cross is not None:
        c_abs = rate(abs(cross.numerator), cross.denominator, 2, site=site)
        sents.append(f"條線由下面過 50% 嘅位（虛線，{_frac(cross, 3, site)}）就係打和線")
        if cross < 0:
            sents.append(f"即係 {p0} 嘅 APP 低過 {p1} 唔多過 {c_abs} 左右，嗰局大概仲有一半機會贏")
        elif cross > 0:
            sents.append(f"即係 {p0} 嘅 APP 要高過 {p1} {c_abs} 左右，先有一半機會贏")
        else:
            sents.append("即係兩個人 APP 一樣就啱啱一半一半")
    else:
        sents.append("條線冇由下面過到 50%，所以畫唔到打和線")
    if 0 in bins:
        w, n = bins[0]
        sents.append(f"兩個人 APP 差唔多（差唔夠 0.025）嘅 {n} 局，{p0} 贏 {w} 局，"
                     f"即 {pct(w, n, 1, site=site)}%")
    t0, t1 = ctx["totals"]
    if t0["pieces"] and t1["pieces"]:
        tonight = Fraction(t0["attack"], t0["pieces"]) - Fraction(t1["attack"], t1["pieces"])
        s = f"今晚成晚計 {p0} 減 {p1} 係 {_frac(tonight, 3, site)}"
        if cross is not None and tonight != cross:
            s += "，喺打和線" + ("贏面嗰邊" if tonight > cross else "輸面嗰邊")
        sents.append(s)
    note = _note("；".join(sents) + "。呢個係截至呢晚為止成個 corpus 嘅量度，唔係證明；之後先加嘅 session 唔會改呢份報告。"
                 "APP 同贏局係相關，唔係因果：輸家最後嗰幾粒係頂住壓力落嘅，本身就會拉低佢嗰局嘅 APP，"
                 "所以唔好讀成「APP 提高幾多就會贏幾多」。")
    return block("APP 差幾多先打和？", EYEBROW, body, note, block_id="breakeven")


# ------------------------------------------------------------------ block 6

def _cmp(x, y):
    """Sign of x[0]/x[1] - y[0]/y[1], exactly."""
    d = x[0] * y[1] - y[0] * x[1]
    return (d > 0) - (d < 0)


def trend(ctx):
    if not ctx["date"]:
        return None
    sessions, skipped = _sessions(ctx)
    names = ctx["players"]
    rows = [(date, _session_totals(f, names)) for date, f in sessions]
    rows = [(d, t) for d, t in rows if t[0][1] and t[1][1]]
    # A subset report (subsets/<date>-<suffix>/report) is drawn from the night sessions/<date>,
    # which IS in the corpus; its own figures are ctx["totals"]. So 「今晚」 must be the subset's
    # numbers, not the full night's, or this block contradicts block 1 of the same report.
    subset = not is_corpus_session(ctx)
    tot = ctx["totals"]
    mine = [(tot[i]["attack"], tot[i]["pieces"]) for i in (0, 1)]
    if subset and mine[0][1] and mine[1][1]:
        if rows and rows[-1][0] == ctx["date"]:
            rows[-1] = (rows[-1][0], mine)
        else:
            rows.append((ctx["date"], mine))
    if len(rows) < 2:
        return None
    assert not (mine[0][1] and mine[1][1]) or rows[-1][1] == mine, \
        "trend: the 今晚 row is not this report's own totals"
    site = f"{SITE}.trend"
    n = len(rows)
    vals = [t[i][0] / t[i][1] for _, t in rows for i in (0, 1)]
    step = 50
    lo = int(min(vals) * 1000) // step * step
    hi = -(-int(max(vals) * 1000 + 1) // step) * step
    if hi <= lo:
        hi = lo + step

    H, L, R, T, B = 270, 52, 20, 18, 58
    sx = Scale(0, n - 1, L + 8, W - R - 8)
    sy = Scale(lo / 1000, hi / 1000, H - B, T)
    tv = list(range(lo, hi + 1, step))
    parts = [grid_y(sy, [v / 1000 for v in tv], L, W - R,
                    labels=[num(v, 2, site=site) for v in tv])]
    parts.append(axis_line(L, H - B, W - R, H - B))
    every = 1 if n <= 10 else 2
    for i, (d, _) in enumerate(rows):
        if i % every == 0 or i == n - 1:
            x, y = sx(i), H - B + 14
            parts.append(el("text", {"class": "ap-tick", "x": x, "y": y, "text-anchor": "end",
                                     "transform": f"rotate(-40 {coord(x)} {coord(y)})"},
                            text=d[5:]))
    parts.append(axis_label(14, (T + H - B) / 2, "APP（每粒攻擊）", rotate=True))

    # gap band: one segment per pair of sessions, filled in the colour of whoever is higher there,
    # split where the two lines cross so each piece belongs to one player
    def pt(i, j):
        return sx(i), sy(rows[i][1][j][0] / rows[i][1][j][1])
    for i in range(n - 1):
        a0, a1 = pt(i, 0), pt(i, 1)
        b0, b1 = pt(i + 1, 0), pt(i + 1, 1)
        da = a1[1] - a0[1]          # > 0: player 0 drawn higher (smaller y)
        db = b1[1] - b0[1]
        polys = []
        if da * db >= 0:
            who = 0 if (da + db) > 0 else 1
            polys.append(([a0, b0, b1, a1], who))
        else:
            t = da / (da - db)
            m = (a0[0] + t * (b0[0] - a0[0]), a0[1] + t * (b0[1] - a0[1]))
            polys.append(([a0, m, a1], 0 if da > 0 else 1))
            polys.append(([m, b0, b1], 0 if db > 0 else 1))
        for pts, who in polys:
            p = " ".join(f"{coord(x)},{coord(y)}" for x, y in pts)
            parts.append(el("polygon", {"class": f"ap-f{who + 1}", "points": p,
                                        "fill-opacity": 0.16}))
    xn = sx(n - 1)
    parts.append(el("line", {"class": "ap-ref", "x1": xn, "x2": xn, "y1": T, "y2": H - B}))
    parts.append(el("text", {"x": xn - 6, "y": T + 10, "text-anchor": "end"}, text="今晚"))
    for j in (0, 1):
        d = "".join(("M" if i == 0 else "L") + f"{coord(pt(i, j)[0])} {coord(pt(i, j)[1])}"
                    for i in range(n))
        parts.append(el("path", {"class": f"ap-s{j + 1}", "d": d, "fill": "none",
                                 "stroke-width": 2.2}))
        for i, (date, t) in enumerate(rows):
            x, y = pt(i, j)
            tip = f"{date} {names[j]}：{rate(t[j][0], t[j][1], 3, site=site)}"
            parts.append(el("circle", {"class": f"ap-f{j + 1}", "cx": x, "cy": y,
                                       "r": 5 if i == n - 1 else 3}, title(tip)))
    chart = _chart(svg(W, H, parts, "每個 session 兩個人嘅 APP"))

    legend = ('<div class="ap-legend">'
              + "".join(f'<span><i class="ap-key ap-k{j + 1}"></i>'
                        f'{esc(names[j])}</span>' for j in (0, 1))
              + '<span>色帶 = 兩個人之間嘅差，顏色跟高嗰個</span><span>虛直線 = 今晚</span></div>')

    higher = [0, 0]
    ties = 0
    for _, t in rows:
        c = _cmp(t[0], t[1])
        if c > 0:
            higher[0] += 1
        elif c < 0:
            higher[1] += 1
        else:
            ties += 1
    last = rows[-1][1]
    ranks = [1 + sum(1 for _, t in rows if _cmp(t[j], last[j]) > 0) for j in (0, 1)]
    p0, p1 = pname(ctx, 0), pname(ctx, 1)
    sents = [f"截至呢晚有 {n} 個 session，{p0} 高嘅有 {higher[0]} 個，{p1} 高嘅有 {higher[1]} 個"
             + (f"，打和 {ties} 個" if ties else "")]
    sents.append(f"今晚 {p0} 嘅 {rate(last[0][0], last[0][1], 3, site=site)} 喺佢自己 {n} 晚入面"
                 f"排第 {ranks[0]}，{p1} 嘅 {rate(last[1][0], last[1][1], 3, site=site)} "
                 f"排第 {ranks[1]}（由高數起，同分計同一個名次）")
    sents.append("每晚嘅 APP 係將嗰晚所有局嘅攻擊加埋除以粒數，局長嘅局佔多啲份量")
    note_txt = "；".join(sents) + "。呢條線係截至呢晚為止嘅量度，唔係證明；之後先加嘅 session 唔會畫落呢份報告。"
    if subset:
        note_txt += ("呢份報告係嗰晚揀出嚟嘅一部分（subset），所以「今晚」嗰點同佢嘅排名用嘅係呢個 subset "
                     "自己嘅數，唔係成晚；其他點係每晚成晚計。")
    if skipped:
        note_txt += f"有 {skipped} 個 session 唔係呢兩個人對打，冇畫。"
    body = legend + chart
    return block("每晚嘅 APP", EYEBROW, body, _note(note_txt), block_id="trend")

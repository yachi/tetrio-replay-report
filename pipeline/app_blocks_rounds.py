"""Blocks 2 and 3 of 每粒攻擊 — per-round views. Contract: pipeline/app_section.py's docstring.

    speed_scatter(ctx)  block 2, 快定重: one dot per (round, player), x = PPS, y = APP, with
                        APM iso-curves (APM = 60 · APP · PPS) and each player's session diamond.
    round_strip(ctx)    block 3, 逐局 APP 差: one signed bar per round (players[0] APP minus
                        players[1] APP), coloured by the round's winner, grouped by match.

Both are measurements from facts.json, not proved claims, so neither carries a badge: the only
APP claim per round (`app_decides_rounds`) pools won rounds against lost ones, which is not the
count printed here. Every comparison between two APPs is an integer cross-multiplication; floats
are used for coordinates only. Every printed decimal goes through app_svg.num/rate/pct.
"""
from pipeline.app_common import P_CLASS, SCROLL_HINT, block, pname
from pipeline.app_svg import (Scale, axis_label, axis_line, coord, el, esc, num, pct, rate, svg,
                              title)

#: A player-round with fewer pieces than this is left off the scatter: its APP and PPS rest on a
#: handful of pieces (a round lost inside the opener), and one such dot sits far off any axis.
MIN_PIECES = 15

_F = ("ap-f1", "ap-f2")
_S = ("ap-s1", "ap-s2")


# ------------------------------------------------------------------ small helpers

def _cmp_app(a0, p0, a1, p1):
    """sign(a0/p0 - a1/p1) by cross-multiplication; pieces are > 0."""
    d = a0 * p1 - a1 * p0
    return (d > 0) - (d < 0)


def _key(kind, i):
    """A legend swatch as a tiny inline SVG, coloured by the section's positional classes."""
    if kind == "dot":
        mark = el("circle", {"class": _F[i], "cx": 6, "cy": 6, "r": 4.5})
    elif kind == "hollow":
        mark = el("circle", {"class": f"ap-hollow {_S[i]}", "cx": 6, "cy": 6, "r": 4.2})
    elif kind == "bar":
        mark = el("rect", {"class": _F[i], "x": 2, "y": 1, "width": 8, "height": 10})
    elif kind == "hbar":
        mark = el("rect", {"class": f"ap-hollow {_S[i]}", "x": 2.5, "y": 1.5, "width": 7,
                           "height": 9})
    else:                                  # diamond
        mark = (el("rect", {"class": f"ap-hollow {_S[i]}", "x": 2, "y": 2, "width": 8,
                            "height": 8, "transform": "rotate(45 6 6)"})
                + el("rect", {"class": _F[i], "x": 4, "y": 4, "width": 4, "height": 4,
                              "transform": "rotate(45 6 6)"}))
    return el("svg", {"width": 12, "height": 12, "viewBox": "0 0 12 12", "aria-hidden": "true",
                      "class": "ap-keysvg"}, mark)


def _legend(items):
    return ('<div class="ap-legend">'
            + "".join(f"<span>{k}{t}</span>" for k, t in items) + "</div>")


def _fig(big, sub):
    return (f'<div class="ap-fig"><span class="ap-big">{big}</span>'
            f'<span class="ap-sub">{sub}</span></div>')


def _tenths_floor(n, d):
    return (n * 10) // d


def _tenths_ceil(n, d):
    return -(-(n * 10) // d)


# ------------------------------------------------------------------ block 2

def speed_scatter(ctx):
    players = ctx["players"]
    pts, skipped = [], [0, 0]
    for r in ctx["rounds"]:
        for i in (0, 1):
            s = r["p"][i]
            if s["pieces"] < MIN_PIECES or s["lifetime"] <= 0:
                skipped[i] += 1
                continue
            pts.append((i, r, s))
    tot = ctx["totals"]

    if not pts:
        return block("快定重？逐局速度 × 每粒攻擊", "每粒攻擊 · 逐局",
                     '<p class="ap-muted">呢晚冇一局有人落夠 '
                     f'{MIN_PIECES} 粒方塊，冇得畫。</p>', block_id="scatter")

    # Domain in integer tenths, so every tick is an exact multiple of 0.1. The session diamonds
    # are inside it too (they are pooled over every round, the short ones included).
    xs_lo = [_tenths_floor(s["pieces"] * 1000, s["lifetime"]) for _, _, s in pts]
    xs_hi = [_tenths_ceil(s["pieces"] * 1000, s["lifetime"]) for _, _, s in pts]
    ys_lo = [_tenths_floor(s["attack"], s["pieces"]) for _, _, s in pts]
    ys_hi = [_tenths_ceil(s["attack"], s["pieces"]) for _, _, s in pts]
    for t in tot:
        if t["pieces"] and t["lifetime"]:
            xs_lo.append(_tenths_floor(t["pieces"] * 1000, t["lifetime"]))
            xs_hi.append(_tenths_ceil(t["pieces"] * 1000, t["lifetime"]))
            ys_lo.append(_tenths_floor(t["attack"], t["pieces"]))
            ys_hi.append(_tenths_ceil(t["attack"], t["pieces"]))
    kx0, kx1 = min(xs_lo), max(xs_hi)
    ky0, ky1 = min(ys_lo), max(ys_hi)
    if kx1 == kx0:
        kx1 += 1
    if ky1 == ky0:
        ky1 += 1
    x0, x1, y0, y1 = kx0 / 10, kx1 / 10, ky0 / 10, ky1 / 10

    W, H, L, R, T, B = 720, 400, 52, 20, 14, 44
    sx, sy = Scale(x0, x1, L, W - R), Scale(y0, y1, H - B, T)
    parts = []

    # grid + tick labels (step 0.1, or 0.2 when the span is wide)
    def tick_ks(k0, k1):
        step = 1 if k1 - k0 <= 12 else 2
        return [k for k in range(k0, k1 + 1) if k % step == 0]
    for k in tick_ks(kx0, kx1):
        x = sx(k / 10)
        parts.append(el("line", {"class": "ap-grid", "x1": x, "x2": x, "y1": T, "y2": H - B}))
        parts.append(el("text", {"class": "ap-tick", "x": x, "y": H - B + 16,
                                 "text-anchor": "middle"},
                        text=num(k * 100, 1, site="app_blocks_rounds.scatter_xtick")))
    for k in tick_ks(ky0, ky1):
        y = sy(k / 10)
        parts.append(el("line", {"class": "ap-grid", "x1": L, "x2": W - R, "y1": y, "y2": y}))
        parts.append(el("text", {"class": "ap-tick", "x": L - 6, "y": y + 4,
                                 "text-anchor": "end"},
                        text=num(k * 100, 1, site="app_blocks_rounds.scatter_ytick")))
    parts.append(axis_line(L, H - B, W - R, H - B))
    parts.append(axis_line(L, T, L, H - B))
    parts.append(axis_label((L + W - R) / 2, H - 6, "PPS（每秒落幾多粒）"))
    parts.append(axis_label(14, (T + H - B) / 2, "APP（每粒攻擊）", rotate=True))

    clip = "ap-clip-scatter"
    parts.append(el("clipPath", {"id": clip},
                    el("rect", {"x": L, "y": T, "width": W - R - L, "height": H - B - T})))
    inner = []

    # APM iso-curves: APM = 60 · APP · PPS, i.e. APP = APM / (60 · PPS)
    apm_lo, apm_hi = 60 * y0 * x0, 60 * y1 * x1
    step = next(s for s in (5, 10, 20, 25, 50, 100) if (apm_hi - apm_lo) / s <= 10)
    apm = (int(apm_lo // step) + 1) * step
    while apm < apm_hi:
        d = []
        for j in range(61):
            x = x0 + (x1 - x0) * j / 60
            d.append(("M" if j == 0 else "L") + coord(sx(x)) + " " + coord(sy(apm / (60 * x))))
        inner.append(el("path", {"class": "ap-ref", "d": "".join(d), "opacity": 0.55}))
        xl = x1 - (x1 - x0) * 0.02
        yl = apm / (60 * xl)
        if y0 + (y1 - y0) * 0.04 < yl < y1 - (y1 - y0) * 0.04:
            inner.append(el("text", {"class": "ap-axlabel", "x": sx(xl), "y": sy(yl) - 4,
                                     "text-anchor": "end"}, text=f"{apm} APM"))
        apm += step

    won_hi = [[0, 0], [0, 0]]               # [player][won?] dots at or above own session APP
    won_n = [[0, 0], [0, 0]]
    for i, r, s in pts:
        won = r["winner"] == i
        x = sx(s["pieces"] * 1000 / s["lifetime"])
        y = sy(s["attack"] / s["pieces"])
        t = tot[i]
        won_n[i][won] += 1
        if s["attack"] * t["pieces"] >= t["attack"] * s["pieces"]:
            won_hi[i][won] += 1
        cls = _F[i] if won else f"ap-hollow {_S[i]}"
        tip = (f'{players[i]} m{r["match"]}r{r["round"]}：PPS '
               f'{rate(s["pieces"] * 1000, s["lifetime"], 2, site="app_blocks_rounds.scatter_tip_pps")}'
               f'，APP {rate(s["attack"], s["pieces"], 3, site="app_blocks_rounds.scatter_tip_app")}'
               f'（{s["attack"]} 行 ÷ {s["pieces"]} 粒），{"贏" if won else "輸"}')
        inner.append(el("circle", {"class": cls, "cx": x, "cy": y, "r": 4.2,
                                   "stroke-width": 1.5, "opacity": 0.85}, title(tip)))
    parts.append(el("g", {"clip-path": f"url(#{clip})"}, *inner))

    # session diamonds, pooled over every round
    for i in (0, 1):
        t = tot[i]
        if not (t["pieces"] and t["lifetime"]):
            continue
        cx, cy = sx(t["pieces"] * 1000 / t["lifetime"]), sy(t["attack"] / t["pieces"])
        rot = f"rotate(45 {coord(cx)} {coord(cy)})"
        tip = (f'{players[i]} 全晚：PPS '
               f'{rate(t["pieces"] * 1000, t["lifetime"], 2, site="app_blocks_rounds.scatter_mean_pps")}'
               f'，APP {rate(t["attack"], t["pieces"], 3, site="app_blocks_rounds.scatter_mean_app")}')
        parts.append(el("g", None,
                        el("rect", {"class": f"ap-hollow {_S[i]}", "x": cx - 8, "y": cy - 8,
                                    "width": 16, "height": 16, "transform": rot,
                                    "stroke-width": 2.5}),
                        el("rect", {"class": _F[i], "x": cx - 4.5, "y": cy - 4.5, "width": 9,
                                    "height": 9, "transform": rot}),
                        title(tip)))

    chart = ('<div class="ap-chart">'
             + svg(W, H, parts, "逐局 PPS 對每粒攻擊散點圖，連同 APM 等值線") + "</div>" + SCROLL_HINT)
    legend = _legend([(_key("dot", 0), pname(ctx, 0)), (_key("dot", 1), pname(ctx, 1)),
                      (_key("hollow", 0) + _key("hollow", 1), "空心 = 嗰局輸"),
                      (_key("diamond", 0) + _key("diamond", 1), "菱形 = 全晚合計"),
                      ("", "虛線 = 同一個 APM")])
    lede = ('<p class="ap-sub">每點係一局入面一個人。橫軸 PPS（每秒落幾多粒），直軸 APP（每粒攻擊）。'
            '虛線弧係同一個 APM：APM ＝ 60 × APP × PPS，所以沿住同一條弧，慢少少但每粒重少少係打和。</p>')

    # --- the reading, player-agnostic
    t0, t1 = tot
    sents = []
    if t0["lifetime"] and t1["lifetime"] and t0["pieces"] and t1["pieces"]:
        pps_s = [rate(t["pieces"] * 1000, t["lifetime"], 2, site="app_blocks_rounds.note_pps")
                 for t in tot]
        app_s = [rate(t["attack"], t["pieces"], 3, site="app_blocks_rounds.note_app") for t in tot]
        apm_s = [rate(t["attack"] * 60000, t["lifetime"], 1, site="app_blocks_rounds.note_apm")
                 for t in tot]
        dpps = t0["pieces"] * t1["lifetime"] - t1["pieces"] * t0["lifetime"]
        fast = 0 if dpps > 0 else 1 if dpps < 0 else None
        dapp = t0["attack"] * t1["pieces"] - t1["attack"] * t0["pieces"]
        heavy = 0 if dapp > 0 else 1 if dapp < 0 else None
        dapm = t0["attack"] * t1["lifetime"] - t1["attack"] * t0["lifetime"]
        more = 0 if dapm > 0 else 1 if dapm < 0 else None
        if fast is None:
            sents.append(f"全晚 PPS 兩個人一樣（{pps_s[0]}）")
        else:
            o = 1 - fast
            g = pct(tot[fast]["pieces"] * tot[o]["lifetime"] - tot[o]["pieces"] * tot[fast]["lifetime"],
                    tot[o]["pieces"] * tot[fast]["lifetime"], 1, site="app_blocks_rounds.note_pps_gap")
            sents.append(f"全晚 {pname(ctx, fast)} 快啲：PPS {pps_s[fast]} 對 {pps_s[o]}，"
                         f"快約 {g}%")
        if heavy is None:
            sents.append(f"每粒攻擊兩個人一樣（{app_s[0]}）")
        else:
            o = 1 - heavy
            g = pct(tot[heavy]["attack"] * tot[o]["pieces"] - tot[o]["attack"] * tot[heavy]["pieces"],
                    tot[o]["attack"] * tot[heavy]["pieces"], 1,
                    site="app_blocks_rounds.note_app_gap") if tot[o]["attack"] else None
            gtxt = f"，重約 {g}%" if g is not None else ""
            sents.append(f"{pname(ctx, heavy)} 每粒重啲：APP {app_s[heavy]} 對 {app_s[o]}{gtxt}")
        if more is None:
            apm_txt = f"兩個人全晚 APM 一樣（{apm_s[0]}）"
        else:
            apm_txt = (f"兩樣乘埋，全晚 APM 係 {pname(ctx, 0)} {apm_s[0]} 對 "
                       f"{pname(ctx, 1)} {apm_s[1]}，{pname(ctx, more)} 高啲")
            if fast is not None and heavy is not None and fast != heavy:
                apm_txt += ("：快嗰個" + ("補得返" if more == fast else "冇補得返") + "輕")
        sents.append(apm_txt)
    within = []
    for i in (0, 1):
        if won_n[i][1] and won_n[i][0]:
            within.append(f"{pname(ctx, i)} 嘅實心點 {won_hi[i][1]} / {won_n[i][1]} 喺佢自己全晚 APP "
                          f"或以上，空心點係 {won_hi[i][0]} / {won_n[i][0]}")
    note = ["<b>點睇：</b>" + "；".join(sents) + "。"] if sents else ["<b>點睇：</b>"]
    if within:
        # "solid dots sit higher" only when, for BOTH players, the won share beats the lost share
        higher = all(won_n[i][1] and won_n[i][0]
                     and won_hi[i][1] * won_n[i][0] > won_hi[i][0] * won_n[i][1] for i in (0, 1))
        tail = ("。兩個人都係實心點比空心點多喺高位，即係同一個人入面，贏輸同直軸（APP）有關。"
                if higher else "。今晚唔係兩個人都係實心點較多喺高位。")
        note.append("同一個人入面比：" + "；".join(within) + tail
                    + "呢個係相關，唔係因果：輸家最後幾粒係頂住壓力落嘅，本身就會拉低嗰局嘅 APP。")
    sk = [f"{pname(ctx, i)} {skipped[i]} 局" for i in (0, 1) if skipped[i]]
    note.append("菱形係全晚合計（攻擊總數 ÷ 方塊總數，方塊總數 ÷ 總時間），包埋所有局。"
                + (f"落少過 {MIN_PIECES} 粒嘅局冇畫點（{'、'.join(sk)}），"
                   "因為幾粒方塊嘅 APP 同 PPS 唔穩陣。" if sk else
                   f"每局兩個人都落夠 {MIN_PIECES} 粒，冇局要略過。"))
    return block("快定重？逐局速度 × 每粒攻擊", "每粒攻擊 · 逐局",
                 lede + legend + chart, " ".join(note), block_id="scatter")


# ------------------------------------------------------------------ block 3

def round_strip(ctx):
    players = ctx["players"]
    rounds = ctx["rounds"]
    n = len(rounds)
    if not n:
        return block("逐局 APP 差", "每粒攻擊 · 逐局", '<p class="ap-muted">冇局。</p>',
                     block_id="strip")

    def app(s):
        return s["attack"] / s["pieces"] if s["pieces"] else 0.0

    diffs = [app(r["p"][0]) - app(r["p"][1]) for r in rounds]
    # y half-range in integer tenths (layout only), at least 0.1
    kd = max(1, max(-(-int(abs(d) * 1000) // 100) for d in diffs))
    m = kd / 10

    nm = len({r["mi"] for r in rounds})
    W, H, L, R, T, B, gap = 720, 240, 48, 8, 14, 34, 6
    bw = (W - L - R - gap * (nm - 1)) / n
    sy = Scale(-m, m, H - B, T)
    parts = []
    for v1000, k in ((kd * 100, "+"), (kd * 50, "+"), (0, ""), (-kd * 50, ""), (-kd * 100, "")):
        y = sy(v1000 / 1000)
        parts.append(el("line", {"class": "ap-ax" if v1000 == 0 else "ap-grid",
                                 "x1": L, "x2": W - R, "y1": y, "y2": y}))
        lab = "0" if v1000 == 0 else k + num(v1000, 2, site="app_blocks_rounds.strip_ytick")
        parts.append(el("text", {"class": "ap-tick", "x": L - 6, "y": y + 4,
                                 "text-anchor": "end"}, text=lab))

    agree, ties, exc = 0, 0, [0, 0]
    x, start, prev = L, L, rounds[0]["mi"]
    labels = []
    y0 = sy(0)
    for r, d in zip(rounds, diffs):
        if r["mi"] != prev:
            labels.append((start, x, None, prev))
            x += gap
            start, prev = x, r["mi"]
        w = r["winner"]
        a, b = r["p"]
        if a["pieces"] and b["pieces"]:
            c = _cmp_app(a["attack"], a["pieces"], b["attack"], b["pieces"])
        else:
            c = 0
        hi = None if c == 0 else (0 if c > 0 else 1)
        if hi is None:
            ties += 1
        elif hi == w:
            agree += 1
        else:
            exc[w] += 1
        y = sy(max(-m, min(m, d)))
        exception = hi is not None and hi != w
        # an exception is drawn hollow and the note asks the reader to count those bars, so it
        # gets a minimum height a hollow box stays visible at, on the side its sign points to
        h = max(abs(y - y0), 6 if exception else 1)
        top = y0 - h if (y < y0 or (y == y0 and hi == 0)) else y0
        cls = f"ap-hollow {_S[w]}" if exception else _F[w]
        apps = [rate(s["attack"], s["pieces"], 3, site="app_blocks_rounds.strip_tip_app")
                if s["pieces"] else "—" for s in (a, b)]
        tip = (f'm{r["match"]}r{r["round"]}：{players[0]} {apps[0]} ／ {players[1]} {apps[1]}，'
               f'{players[w]} 贏')
        inset = 0.5 if bw > 3 else 0
        parts.append(el("rect", {"class": cls, "x": x + inset, "y": top,
                                 "width": max(bw - 2 * inset, 1), "height": h,
                                 "stroke-width": 1.2 if bw > 3 else 0.8}, title(tip)))
        x += bw
    labels.append((start, x, None, prev))
    mpos = {mm["mi"]: mm["match"] for mm in ctx["matches"]}
    every = 1
    narrow = min(e - s for s, e, _, _ in labels)
    if narrow < 16:
        every = 2 if narrow >= 8 else 4
    for j, (s, e, _, mi) in enumerate(labels):
        if j % every:
            continue
        parts.append(el("text", {"class": "ap-tick", "x": (s + e) / 2, "y": H - B + 18,
                                 "text-anchor": "middle"}, text=f"m{mpos[mi]}"))
    parts.append(el("text", {"class": "ap-axlabel", "x": W - R, "y": T + 10,
                             "text-anchor": "end"}, text=f"↑ {players[0]} 每粒重啲"))
    parts.append(el("text", {"class": "ap-axlabel", "x": W - R, "y": H - B - 6,
                             "text-anchor": "end"}, text=f"↓ {players[1]} 每粒重啲"))

    chart = ('<div class="ap-chart">'
             + svg(W, H, parts, f"逐局 APP 差：{players[0]} 減 {players[1]}，按場分組") + "</div>" + SCROLL_HINT)
    lede = (f'<p class="ap-sub">每條係一局：向上 ＝ {pname(ctx, 0)} 嗰局 APP 高過 {pname(ctx, 1)}，'
            f'向下 ＝ {pname(ctx, 1)} 高啲；條嘅高度就係兩個人 APP 相差幾多。顏色係嗰局邊個贏。</p>')
    legend = _legend([(_key("bar", 0), f"{pname(ctx, 0)} 贏"),
                      (_key("bar", 1), f"{pname(ctx, 1)} 贏"),
                      (_key("hbar", 0) + _key("hbar", 1), "空心 = APP 低嗰個反而贏")])
    decided = n - ties
    figs = ['<div class="ap-figs">',
            _fig(f"{agree} / {decided}", "APP 高嗰個贏嘅局"),
            _fig(str(exc[0]), f"{pname(ctx, 0)} APP 低過但都贏"),
            _fig(str(exc[1]), f"{pname(ctx, 1)} APP 低過但都贏")]
    figs.append("</div>")
    tie_txt = (f"有 {ties} 局兩個人 APP 一樣（或者有人一粒都冇落），唔計入分母。" if ties else "")
    note = ("<b>點睇：</b>顏色同方向夾唔夾：向上而且係 "
            f"{pname(ctx, 0)} 色、向下而且係 {pname(ctx, 1)} 色，就係 APP 高嗰個贏。"
            "空心嗰幾條係例外，值得返去睇返嗰局。" + tie_txt
            + "APP 高同贏局係相關，唔係因果：輸家最後幾粒係頂住壓力落嘅，"
              "本身就會拉低佢嗰局嘅 APP，所以「APP 高所以贏」同「贏緊所以 APP 高」兩樣都有份。")
    return block("逐局 APP 差", "每粒攻擊 · 逐局", lede + legend + chart + "".join(figs), note,
                 block_id="strip")

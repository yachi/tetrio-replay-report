"""Blocks 1, 4a, 4b of 每粒攻擊 — the session-level APP blocks. Contract: pipeline/app_section.py.

    scoreboard(ctx)  block 1  APP 計分板: both players' session APP, the ratio gap, 每 100 粒打幾多行,
                              and the volume meter (the lower-APP player's piece surplus against the
                              surplus that would have covered the gap — the shortfall).
    per_match(ctx)   block 4a 逐場 APP: one dumbbell per match, winner ringed, score at the right.
    won_lost(ctx)    block 4b 贏局 vs 輸局: each player's pooled APP over the rounds he won and lost.

Every figure is computed here from ctx (facts.json). Every printed decimal goes through
app_svg.num / rate / pct (-> pipeline.fmt) with an explicit rule and a site name; comparisons are
exact (cross-multiplied integers), never on floats. Nothing is bound to a player NAME: the
"higher" and "lower" player are found from the data, and colour is positional (P_CLASS).

A ✓ badge is attached only where a verified generated claim's SPEC is exactly the statement
beside it (`_find`): the raw session totals (total_garbage_attack / total_pieces), the session
APP ordering (per_piece_garbage_attack), and each player's won-vs-lost ordering
(rate_split_garbage_attack / app_decides_rounds). Nothing else in these blocks is proved.
"""
from pipeline.app_common import P_CLASS, SCROLL_HINT, badge, block, claims_of, pname
from pipeline.app_svg import Scale, axis_label, el, esc, grid_x, num, pct, rate, svg, title

SITE = "app_blocks_session"
W = 720
#: The two narrow charts (per-100 bars, volume meter) draw on a smaller viewBox so their text
#: stays readable when the chart shrinks to a phone column; CSS caps their width on desktop.
WN = 480


# ------------------------------------------------------------------ helpers

def _app(ctx, i):
    t = ctx["totals"][i]
    return t["attack"], t["pieces"]


def _cmp(a0, p0, a1, p1):
    """Sign of a0/p0 - a1/p1, exactly (pieces > 0)."""
    d = a0 * p1 - a1 * p0
    return (d > 0) - (d < 0)


def _find(ctx, family, ok):
    """The id of a VERIFIED claim of `family` whose spec satisfies `ok(spec)`, or None."""
    for c in claims_of(ctx, family):
        if c.get("verified") and ok(c["spec"]):
            return c["id"]
    return None


def _badge_if(cid):
    return badge(cid) if cid else ""


def _eq_totals(spec, field, values):
    """spec is and(eq(sum_round(pl, field), lit v), ...) for exactly these {pl: v}."""
    if spec.get("p") != "and":
        return False
    got = {}
    for x in spec.get("xs", []):
        a, b = x.get("a", {}), x.get("b", {})
        if (x.get("p") != "eq" or a.get("e") != "sum_round" or a.get("f") != field
                or b.get("e") != "lit"):
            return False
        got[a.get("pl")] = b.get("v")
    return got == values


def _per_piece_gt(hi, lo):
    """sum(hi.attack)·sum(lo.pieces) > sum(lo.attack)·sum(hi.pieces) — hi's APP is higher."""
    s = lambda pl, f: {"e": "sum_round", "pl": pl, "f": f}  # noqa: E731
    return {"p": "gt", "a": {"e": "mul", "a": s(hi, "garbage_attack"), "b": s(lo, "pieces")},
            "b": {"e": "mul", "a": s(lo, "garbage_attack"), "b": s(hi, "pieces")}}


def _won_gt_lost(me, other):
    """me's APP over rounds me won > over rounds `other` won (the rate_split spec)."""
    def s(f, w):
        return {"e": "sum_round_where", "pl": me, "f": f, "cond": {"c": "winner", "pl": w}}
    return {"p": "gt", "a": {"e": "mul", "a": s("garbage_attack", me), "b": s("pieces", other)},
            "b": {"e": "mul", "a": s("garbage_attack", other), "b": s("pieces", me)}}


def _chart(svg_markup, narrow=False):
    out = f'<div class="ap-chart{" ap-narrow" if narrow else ""}">{svg_markup}</div>'
    return out if narrow else out + SCROLL_HINT


def _tspan(text, i, bold=False):
    # Coloured SVG text goes in a <tspan>: `#app .ap-svg text` outranks `#app .ap-f1`, while a
    # tspan is not matched by it and takes the fill class.
    return el("tspan", {"class": f"ap-f{i + 1}", "font-weight": 700 if bold else None}, text=text)


def _x_ticks(lo1000, hi1000, step1000=50):
    """Tick values (x1000 ints) covering [lo, hi], padded out to whole steps."""
    lo = (lo1000 // step1000) * step1000
    hi = -((-hi1000) // step1000) * step1000
    if hi == lo:
        lo, hi = lo - step1000, hi + step1000
    return list(range(lo, hi + 1, step1000))


def _note(text_html):
    return f"<b>點睇：</b>{text_html}"


# ------------------------------------------------------------------ block 1

def scoreboard(ctx):
    names = ctx["players"]
    (a0, p0), (a1, p1) = _app(ctx, 0), _app(ctx, 1)
    s = _cmp(a0, p0, a1, p1)
    site = f"{SITE}.scoreboard"

    tot_att = _find(ctx, "total_garbage_attack",
                    lambda sp: _eq_totals(sp, "garbage_attack", {names[0]: a0, names[1]: a1}))
    tot_pcs = _find(ctx, "total_pieces",
                    lambda sp: _eq_totals(sp, "pieces", {names[0]: p0, names[1]: p1}))

    def side(i):
        a, p = _app(ctx, i)
        return (f'<div class="ap-fig"><span class="ap-sub">{pname(ctx, i)}</span>'
                f'<span class="ap-big {P_CLASS[i]}">{rate(a, p, 3, site=f"{site}.app")}</span>'
                f'<span class="ap-sub"><span class="ap-num">{a}</span> 行攻擊 ÷ '
                f'<span class="ap-num">{p}</span> 粒方塊'
                f'{_badge_if(tot_att)}{_badge_if(tot_pcs)}</span></div>')

    if s == 0:
        mid = ('<div class="ap-fig"><span class="ap-sub">差距</span>'
               '<span class="ap-big">0%</span>'
               '<span class="ap-sub">兩個人每粒一樣重</span></div>')
        hi = lo = None
    else:
        hi, lo = (0, 1) if s > 0 else (1, 0)
        (ah, ph), (al, pl) = _app(ctx, hi), _app(ctx, lo)
        gap = (pct(ah * pl - al * ph, al * ph, 2, site=f"{site}.gap") if al
               else None)
        g042 = _find(ctx, "per_piece_garbage_attack",
                     lambda sp: sp == _per_piece_gt(names[hi], names[lo]))
        mid = ('<div class="ap-fig"><span class="ap-sub">差距（比率）</span>'
               f'<span class="ap-big {P_CLASS[hi]}">'
               f'{"+" + gap + "%" if gap is not None else "—"}</span>'
               f'<span class="ap-sub">{pname(ctx, hi)} 每粒重過 {pname(ctx, lo)}'
               f'{_badge_if(g042)}</span></div>')
    figs = f'<div class="ap-figs">{side(0)}{mid}{side(1)}</div>'

    body = [figs, _per100(ctx, hi, lo, site)]
    meter, meter_note = _meter(ctx, hi, lo, site)
    if meter:
        body.append(meter)

    note = ("APP 係攻擊行數除以方塊數，兩邊嘅原數就寫喺個數下面。"
            "「每 100 粒方塊打幾多行」係同一個數乘一百，讀落比較有手感。")
    if meter_note:
        note += meter_note
    note += "差距係比率：高嗰個嘅 APP 除以低嗰個，減一。所有小數都係捨去（約數），唔係四捨五入。"
    return block("APP 計分板", "每粒攻擊 · 成晚", "\n".join(body), _note(note), block_id="score")


def _per100(ctx, hi, lo, site):
    vals = [_app(ctx, i) for i in (0, 1)]
    top = max(a * 100 / p for a, p in vals) * 1.3 or 1.0
    L, R, row = 96, 70, 30
    H = 2 * row + 12
    sx = Scale(0, top, L, WN - R)
    parts = []
    for i, (a, p) in enumerate(vals):
        y = 6 + row * i
        v = a * 100 / p
        parts.append(el("text", {"x": L - 10, "y": y + 15, "text-anchor": "end"},
                        _tspan(ctx["players"][i], i, bold=True)))
        parts.append(el("rect", {"class": "ap-ax", "x": L, "y": y + 3, "width": sx(top) - L,
                                 "height": 16, "fill": "none"}))
        parts.append(el("rect", {"class": f"ap-f{i + 1}", "x": L, "y": y + 3,
                                 "width": max(sx(v) - L, 1), "height": 16},
                        title(f"{ctx['players'][i]}：每 100 粒方塊 "
                              f"{rate(a * 100, p, 1, site=f'{site}.per100')} 行")))
        parts.append(el("text", {"x": sx(v) + 8, "y": y + 15, "text-anchor": "start"},
                        text=f"{rate(a * 100, p, 1, site=f'{site}.per100')} 行"))
    chart = _chart(svg(WN, H, parts, "每 100 粒方塊打幾多行"), narrow=True)
    head = '<div class="ap-sub">每 100 粒方塊打幾多行</div>'
    if hi is None:
        cap = '<div class="ap-sub">每 100 粒方塊，兩個人打出一樣咁多行。</div>'
    else:
        (ah, ph), (al, pl) = _app(ctx, hi), _app(ctx, lo)
        diff = rate((ah * pl - al * ph) * 100, ph * pl, 1, site=f"{site}.per100_diff")
        cap = (f'<div class="ap-sub">每 100 粒方塊：{pname(ctx, hi)} 打多約 '
               f'<span class="ap-num">{diff}</span> 行。</div>')
    return head + chart + cap


def _meter(ctx, hi, lo, site):
    """The volume meter, or (None, note) when there is nothing to measure."""
    if hi is None:
        return None, ""
    (ah, ph), (al, pl) = _app(ctx, hi), _app(ctx, lo)
    if al == 0:
        return None, ""
    L, H = pname(ctx, lo), pname(ctx, hi)
    gap = pct(ah * pl - al * ph, al * ph, 2, site=f"{site}.meter_gap")
    gap_f = 100 * (ah * pl - al * ph) / (al * ph)
    if pl <= ph:
        # the lower-APP player also placed no more pieces: no surplus to measure
        less = ph - pl
        note = (f"{L} 每粒輕過 {H}，粒數亦冇多過佢"
                + (f"（少 <span class=\"ap-num\">{less}</span> 粒）" if less else "")
                + "，所以冇得靠量追，量尺就唔畫。")
        txt = (f'<div class="ap-sub">{L} 每粒輕啲，粒數亦冇多過 {H}，'
               f'追平 APP 差要多放 +<span class="ap-num">{gap}</span>% 粒數，'
               f'而佢一粒都冇多。總攻擊差 <span class="ap-num">{ah - al}</span> 行。</div>')
        return txt, note
    sur = pct(pl - ph, ph, 2, site=f"{site}.meter_surplus")
    sur_f = 100 * (pl - ph) / ph
    # shortfall = gap - surplus = 100·pl·(ah - al) / (al·ph), exactly
    if ah > al:
        short = pct(pl * (ah - al), al * ph, 2, site=f"{site}.meter_shortfall")
        cap = (f"差約 <span class=\"ap-num\">{short}</span> 個百分點冇追到，"
               f"所以總攻擊 {L} 仲係少 <span class=\"ap-num\">{ah - al}</span> 行。")
    elif ah < al:
        over = pct(pl * (al - ah), al * ph, 2, site=f"{site}.meter_over")
        cap = (f"多放嘅粒數蓋過咗 APP 差約 <span class=\"ap-num\">{over}</span> 個百分點，"
               f"所以總攻擊反而係 {L} 多 <span class=\"ap-num\">{al - ah}</span> 行。")
    else:
        cap = "多放嘅粒數啱啱好抵銷 APP 差，兩邊總攻擊一樣。"

    top = max(sur_f, gap_f) * 1.2 or 1.0
    Lx, Rx = 20, 20
    sx = Scale(0, top, Lx, WN - Rx)
    y0, h = 34, 18
    lo_i, hi_i = lo + 1, hi + 1
    parts = [
        el("text", {"x": Lx, "y": 20, "text-anchor": "start"},
           _tspan(ctx["players"][lo], lo, bold=True),
           el("tspan", None, text=f" 多放咗 +{sur}%")),
        # the gap label sits under the bar, centred on its dashed marker (clamped to the chart)
        el("text", {"x": min(max(sx(gap_f), Lx + 70), WN - Rx - 70), "y": y0 + h + 22,
                    "text-anchor": "middle"},
           el("tspan", None, text="追平要多放 "), _tspan(f"+{gap}%", hi, bold=True)),
        el("rect", {"class": "ap-ax", "x": Lx, "y": y0, "width": WN - Lx - Rx, "height": h,
                    "fill": "none"}),
        el("rect", {"class": f"ap-f{lo_i}", "x": Lx, "y": y0,
                    "width": max(sx(sur_f) - Lx, 1), "height": h},
           title(f"{ctx['players'][lo]} 粒數多過 {ctx['players'][hi]} 約 {sur}%")),
        el("line", {"class": f"ap-ref ap-s{hi_i}", "x1": sx(gap_f), "x2": sx(gap_f),
                    "y1": y0 - 6, "y2": y0 + h + 6, "stroke-width": 2.5},
           title(f"追平 APP 差要多放約 {gap}% 粒數")),
    ]
    chart = _chart(svg(WN, y0 + h + 30, parts, "粒數多咗幾多，對比追平 APP 差所需"), narrow=True)
    head = (f'<div class="ap-sub">靠量追：{L} 每粒輕啲，但如果落多啲方塊，'
            f'總攻擊都可以追返。實心係佢多放咗嘅粒數，虛線係追平要多放幾多。</div>')
    note = (f"量尺嘅意思：{H} 嘅 APP 高過 {L} 約 {gap}%，所以 {L} 要多放約 {gap}% 嘅方塊，總攻擊先追得平；"
            f"佢實際多放咗約 {sur}%。兩個數之差就係冇追到（或者追過咗頭）嘅部分。")
    return head + chart + f'<div class="ap-sub">{cap}</div>', note


# ------------------------------------------------------------------ block 4a

def per_match(ctx):
    ms = ctx["matches"]
    names = ctx["players"]
    site = f"{SITE}.per_match"
    vals = [m["attack"][i] * 1000 / m["pieces"][i] for m in ms for i in (0, 1)
            if m["pieces"][i]]
    tk = _x_ticks(int(min(vals)), int(max(vals)) + 1)
    L, R, T, B, row = 50, 80, 14, 30, 30
    H = T + B + row * len(ms)
    sx = Scale(tk[0], tk[-1], L, W - R)
    parts = [grid_x(sx, tk, T - 6, H - B,
                    labels=[num(v, 2, site=f"{site}.tick") for v in tk])]
    parts.append(axis_label((L + W - R) / 2, H - 2, "APP（每粒攻擊）"))
    lead = decided = 0
    for k, m in enumerate(ms):
        y = T + row * k + row / 2
        a, p = m["attack"], m["pieces"]
        if not (p[0] and p[1]):
            continue
        c = _cmp(a[0], p[0], a[1], p[1])
        if c:
            decided += 1
            lead += (0 if c > 0 else 1) == m["winner"]
        xs = [sx(a[i] * 1000 / p[i]) for i in (0, 1)]
        parts.append(el("text", {"x": L - 10, "y": y + 4, "text-anchor": "end"},
                        text=f"m{m['match']}"))
        parts.append(el("line", {"class": "ap-ax", "x1": xs[0], "x2": xs[1], "y1": y, "y2": y,
                                 "stroke-width": 3}))
        for i in (0, 1):
            tip = (f"{names[i]} m{m['match']}：APP {rate(a[i], p[i], 3, site=f'{site}.app')}"
                   f"（{a[i]} 行 ÷ {p[i]} 粒）" + ("，贏咗呢場" if m["winner"] == i else ""))
            if m["winner"] == i:
                parts.append(el("circle", {"class": f"ap-s{i + 1}", "cx": xs[i], "cy": y,
                                           "r": 10, "fill": "none", "stroke-width": 2}))
            parts.append(el("circle", {"class": f"ap-f{i + 1}", "cx": xs[i], "cy": y, "r": 6},
                            title(tip)))
        sc = m["score"]
        parts.append(el("text", {"x": W - R + 14, "y": y + 4, "text-anchor": "start"},
                        _tspan(str(sc[0]), 0, bold=m["winner"] == 0),
                        el("tspan", None, text=" : "),
                        _tspan(str(sc[1]), 1, bold=m["winner"] == 1)))
    legend = (f'<div class="ap-legend"><span><i class="ap-key ap-k1">'
              f'</i>{esc(names[0])}</span><span><i class="ap-key ap-k2">'
              f'</i>{esc(names[1])}</span><span>有圈嘅點 = 嗰場贏家</span>'
              f'<span>右邊係局數比分</span></div>')
    body = legend + _chart(svg(W, H, parts, "逐場 APP，每場兩粒點"))
    n = len(ms)
    tie = n - decided
    note = (f"每行係一場，兩粒點係兩個人嗰場嘅 APP（成場攻擊 ÷ 成場方塊），中間條線越長，"
            f"嗰場每粒差得越遠。今晚 <span class=\"ap-num\">{n}</span> 場入面，"
            f"APP 高嗰個贏咗 <span class=\"ap-num\">{lead}</span> / "
            f"<span class=\"ap-num\">{decided}</span> 場"
            + (f"（另外 <span class=\"ap-num\">{tie}</span> 場兩個人 APP 一樣）" if tie else "")
            + "。APP 高同贏場係有相關，唔係因果：輸家最尾幾粒係頂住壓力落嘅，本身會拉低佢嘅 APP；"
            "一場亦可以靠快、靠量贏返。")
    return block("逐場 APP", "每粒攻擊 · 逐場", body, _note(note), block_id="match")


# ------------------------------------------------------------------ block 4b

def won_lost(ctx):
    names = ctx["players"]
    tot = ctx["totals"]
    site = f"{SITE}.won_lost"
    pts = []  # (player, kind, x1000 float)
    for i in (0, 1):
        t = tot[i]
        for kind in ("won", "lost"):
            if t[f"{kind}_pieces"]:
                pts.append((i, kind, t[f"{kind}_attack"] * 1000 / t[f"{kind}_pieces"]))
    if not pts:
        return block("贏局 vs 輸局嘅 APP", "每粒攻擊 · 贏輸分開", "冇局可以分。",
                     block_id="wonlost")
    tk = _x_ticks(int(min(p[2] for p in pts)) - 25, int(max(p[2] for p in pts)) + 26)
    L, R, T, B, row = 100, 30, 18, 34, 56
    H = T + B + row * 2
    sx = Scale(tk[0], tk[-1], L, W - R)
    parts = [grid_x(sx, tk, T - 6, H - B,
                    labels=[num(v, 2, site=f"{site}.tick") for v in tk]),
             axis_label((L + W - R) / 2, H - 2, "APP（每粒攻擊）")]
    for i in (0, 1):
        t = tot[i]
        y = T + row * i + row / 2 + 4
        parts.append(el("text", {"x": L - 12, "y": y + 4, "text-anchor": "end"},
                        _tspan(names[i], i, bold=True)))
        mine = {k: x for (j, k, x) in pts if j == i}
        if len(mine) == 2:
            parts.append(el("line", {"class": f"ap-s{i + 1}", "x1": sx(mine["lost"]),
                                     "x2": sx(mine["won"]), "y1": y, "y2": y,
                                     "stroke-width": 3, "opacity": 0.45}))
        for kind, word in (("lost", "輸"), ("won", "贏")):
            if kind not in mine:
                continue
            v = rate(t[f"{kind}_attack"], t[f"{kind}_pieces"], 3, site=f"{site}.app")
            cx = sx(mine[kind])
            tip = (f"{names[i]} {word}嘅 {t[f'{kind}_rounds']} 局：APP {v}"
                   f"（{t[f'{kind}_attack']} 行 ÷ {t[f'{kind}_pieces']} 粒）")
            cls = f"ap-f{i + 1}" if kind == "won" else f"ap-hollow ap-s{i + 1}"
            parts.append(el("circle", {"class": cls, "cx": cx, "cy": y, "r": 7}, title(tip)))
            ly = y - 13 if kind == "won" else y + 22
            parts.append(el("text", {"x": cx, "y": ly, "text-anchor": "middle"},
                            text=f"{word} {v}"))
    legend = ('<div class="ap-legend"><span>實心 = 嗰個人贏嘅局</span>'
              '<span>空心 = 嗰個人輸嘅局</span><span>每粒點都係嗰啲局嘅攻擊總數 ÷ 方塊總數</span></div>')
    body = legend + _chart(svg(W, H, parts, "贏局同輸局嘅 APP，每人一行"))

    # --- the note: per player, won vs lost; then between players, per regime
    sents = []
    both_up = True
    for i in (0, 1):
        t = tot[i]
        if not (t["won_pieces"] and t["lost_pieces"]):
            both_up = False
            missing = "贏" if not t["won_pieces"] else "輸"
            sents.append(f"{pname(ctx, i)} 今晚冇{missing}過一局，所以得一粒點。")
            continue
        c = _cmp(t["won_attack"], t["won_pieces"], t["lost_attack"], t["lost_pieces"])
        if c > 0:
            up = pct(t["won_attack"] * t["lost_pieces"] - t["lost_attack"] * t["won_pieces"],
                     t["lost_attack"] * t["won_pieces"], 1, site=f"{site}.within") \
                if t["lost_attack"] else None
            cid = _find(ctx, "rate_split_garbage_attack",
                        lambda sp, i=i: sp == _won_gt_lost(names[i], names[1 - i]))
            # the claim proves the DIRECTION only, so the badge sits on 「高過輸局」 and the size
            # follows it in brackets, outside the badged clause
            sents.append(f"{pname(ctx, i)} 贏局嘅 APP 高過輸局{_badge_if(cid)}"
                         + (f"（約 <span class=\"ap-num\">{up}</span>%）" if up else "")
                         + "。")
        else:
            both_up = False
            sents.append(f"{pname(ctx, i)} 贏局嘅 APP 冇高過輸局"
                         + ("（兩邊一樣）" if c == 0 else "（反而低啲）") + "。")
    lead = ""
    if both_up:
        specs = [_won_gt_lost(names[0], names[1]), _won_gt_lost(names[1], names[0])]
        cid = _find(ctx, "app_decides_rounds",
                    lambda sp: sp.get("p") == "and" and len(sp.get("xs", [])) == 2
                    and sp["xs"] in (specs, specs[::-1]))
        lead = f"兩個人都係實心喺空心右邊，即係贏局每粒重啲{_badge_if(cid)}。"
    cross = []
    for kind, word in (("won", "贏局"), ("lost", "輸局")):
        k0, k1 = tot[0], tot[1]
        if not (k0[f"{kind}_pieces"] and k1[f"{kind}_pieces"]):
            continue
        a0, p0 = k0[f"{kind}_attack"], k0[f"{kind}_pieces"]
        a1, p1 = k1[f"{kind}_attack"], k1[f"{kind}_pieces"]
        c = _cmp(a0, p0, a1, p1)
        if c == 0:
            cross.append(f"{word}兩個人一樣")
            continue
        h, l = (0, 1) if c > 0 else (1, 0)
        ah, ph = (a0, p0) if h == 0 else (a1, p1)
        al, pl = (a1, p1) if h == 0 else (a0, p0)
        if not al:
            cross.append(f"{word} {pname(ctx, h)} 高")
            continue
        g = pct(ah * pl - al * ph, al * ph, 1, site=f"{site}.between")
        cross.append(f"{word} {pname(ctx, h)} 高約 <span class=\"ap-num\">{g}</span>%")
    note = (lead + "".join(sents)
            + (("兩個人之間比：" + "，".join(cross) + "。") if cross else "")
            + "贏局同輸局邊一邊差得遠啲，就睇得出今晚兩個人嘅分別係喺打得好定打得差嘅時候。"
            "注意輸局嘅 APP 本身會偏低：輸家最尾嗰幾粒係頂住垃圾落嘅，所以呢個係相關，唔係因果。")
    return block("贏局 vs 輸局嘅 APP", "每粒攻擊 · 贏輸分開", body, _note(note),
                 block_id="wonlost")

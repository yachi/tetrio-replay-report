"""數據對決's two simulator panels — the night's opener routes and mid-game techniques as grouped bars.

The numbers are `routes_techniques_section.compute`'s, i.e. the same cells the 定式路線同中盤手法 tables
print further down; this module only draws them. The form copies 清行類型分布 (the inline script's
`renderClearsBar`): 96px groups, two 30px player bars, dashed gridlines at four steps, the raw count
above each bar, a bold label under each group, an SVG <title> on a full-height hit area. The SVG is
generated here rather than by the shell's script, because the shell is committed per report and a new
renderer there would have to be pasted into every one of them.

One visual rule is added and it means the same thing in both panels: the outer bar (pale) counts what
matched, the narrower solid bar inside it the subset that went one step further — reached bag 2 for an
opener (and a narrower one again, bag 3 or later), fired the page's next step for a technique. Nested
rather than stacked, because a subset is not a part of a sum.

QUARANTINE. Simulator output, outside the proof chain: no claim id, no ✓, no `data-claim`, and each
panel's footnote says so. No rate is printed — a night has a handful of rounds per opener or technique.
"""
import html

from pipeline import routes_techniques_section as rts

GROUP_W, BAR_W, GAP, PAD_L, PAD_T, PAD_B, PLOT_H = 96, 30, 4, 40, 34, 44, 230
INNER_W, INNERMOST_W = 18, 10

# Both route pages file the same bag-1 board (CLAUDE.md, ### SDPC Spin): drawn side by side, last, under
# one bracket, so the chart does not invite adding them.
SAME_BAG1 = ("stick spin（SDパフェ）", "SDPC Spin")

QUARANTINE = ("呢兩張圖嘅數嚟自 replay 模擬器，喺證明鏈之外：冇 claim 編號、冇 ✓。"
              "逐格對得上嗰頁嘅圖先算，對唔上唔代表冇打過；詳細同連結喺下面"
              "<a href=\"#routes-techniques\">定式路線同中盤手法</a>。")

STYLE = """  <style>
    /* Scoped under the section id with an rc- prefix (check_generated_css). */
    #stats .rc-key { display: flex; gap: 18px; flex-wrap: wrap; margin: -6px 0 14px;
      font-family: var(--font-mono); font-size: 0.74rem; color: var(--muted); }
    #stats .rc-key span { display: inline-flex; align-items: center; gap: 6px; }
    #stats .rc-sw { display: inline-block; width: 14px; height: 10px; border-radius: 3px; }
    #stats .rc-sw.rc-pale { background: color-mix(in srgb, var(--muted) 45%, transparent); }
    #stats .rc-sw.rc-solid { background: var(--muted); }
    #stats .rc-sw.rc-hatch { background: repeating-linear-gradient(45deg, var(--muted) 0 2px, transparent 2px 5px); }
    #stats .rc-zero { color: var(--muted); font-size: 0.8rem; margin-top: 8px; }
    #stats svg a.rc-link:hover text { text-decoration: underline; }
  </style>"""


def _svg(tag, attrs, inner=""):
    a = "".join(f' {k}="{html.escape(str(v))}"' for k, v in attrs.items())
    return f"<{tag}{a}>{inner}</{tag}>" if inner or tag not in ("rect", "line") else f"<{tag}{a}/>"


def _text(x, y, s, size, anchor="middle", **kw):
    return _svg("text", {"x": x, "y": y, "font-size": size, "text-anchor": anchor, **kw}, html.escape(s))


def _label(name):
    """A group label as at most two lines: the name, then its full-width parenthetical."""
    if "（" in name:
        head, tail = name.split("（", 1)
        return [head.strip(), "（" + tail]
    return [name]


def _nice_max(v, floor):
    return max(floor, -(-v // 5) * 5)


def chart(groups, players, ymax, top_label, hatch_of=None, bracket=None):
    """groups: [{"label", "vals": {player: (outer, inner, innermost|None, extra|None, title)}}]."""
    n = len(groups)
    W = PAD_L + n * GROUP_W + 20
    H = PAD_T + PLOT_H + PAD_B + (18 if bracket else 0)
    out = []
    if hatch_of:
        out.append('<defs>' + "".join(
            f'<pattern id="rc-hatch-{pi}" width="5" height="5" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate(45)"><rect width="5" height="5" fill="var(--p{pi + 1})" '
            f'fill-opacity="0.25"/><line x1="0" y1="0" x2="0" y2="5" stroke="var(--p{pi + 1})" '
            f'stroke-width="2" stroke-opacity="0.7"/></pattern>' for pi in range(len(players))) + '</defs>')
    step = next(st for st in (1, 2, 5, 10, 20, 25, 50, 100) if ymax / st <= 5)
    ticks = [v for v in range(0, ymax, step) if ymax - v >= step / 2] + [ymax]
    for val in ticks:
        y = round(PAD_T + PLOT_H - val / ymax * PLOT_H, 2)
        out.append(_svg("line", {"class": "grid-line", "x1": PAD_L, "x2": W - 10, "y1": y, "y2": y}))
        out.append(_text(PAD_L - 8, round(y + 3, 2), top_label if val == ymax else str(val), 9, "end"))
    base = PAD_T + PLOT_H
    out.append(_svg("line", {"class": "axis-line", "x1": PAD_L, "x2": W - 10, "y1": base, "y2": base}))

    for i, g in enumerate(groups):
        gx = PAD_L + i * GROUP_W + GROUP_W / 2
        for pi, p in enumerate(players):
            outer, inner, innermost, extra, title = g["vals"][p]
            col = f"var(--p{pi + 1})"
            bx = gx - BAR_W - GAP / 2 + pi * (BAR_W + GAP)
            h = outer / ymax * PLOT_H
            by = base - h
            if outer == 0:
                out.append(_svg("rect", {"x": bx, "y": base - 2, "width": BAR_W, "height": 2, "fill": col}))
            else:
                fill = f"url(#rc-hatch-{pi})" if hatch_of and hatch_of(g) else col
                op = {} if hatch_of and hatch_of(g) else {"fill-opacity": "0.42"}
                out.append(_svg("rect", {"x": bx, "y": round(by, 2), "width": BAR_W,
                                         "height": round(max(h, 1), 2), "rx": 4, "ry": 4,
                                         "fill": fill, **op}))
                for w, v in ((INNER_W, inner), (INNERMOST_W, innermost)):
                    if v:
                        ih = v / ymax * PLOT_H
                        out.append(_svg("rect", {"x": bx + (BAR_W - w) / 2, "y": round(base - ih, 2),
                                                 "width": w, "height": round(max(ih, 1), 2),
                                                 "rx": 2, "ry": 2, "fill": col}))
            ly = by - 5
            out.append(_text(bx + BAR_W / 2, round(ly, 2), str(outer), 9.5, fill="var(--ink-secondary)",
                             **{"font-family": "var(--font-mono)"}))
            if extra:
                out.append(_text(bx + BAR_W / 2, round(ly - 11, 2), extra, 8.5, fill=col,
                                 **{"font-family": "var(--font-mono)"}))
            out.append(_svg("rect", {"x": bx, "y": PAD_T, "width": BAR_W, "height": PLOT_H,
                                     "fill": "transparent"}, _svg("title", {}, html.escape(title))))
        lines = _label(g["label"])
        lab = _text(gx, base + 18, lines[0], 10.5, **{"font-weight": "700", "fill": "var(--ink)"})
        if len(lines) > 1:
            lab += _text(gx, base + 31, lines[1], 8.5)
        out.append(_svg("a", {"class": "rc-link", "href": "#routes-techniques"}, lab))

    if bracket:
        i0, i1, text = bracket
        x0, x1 = PAD_L + i0 * GROUP_W + 10, PAD_L + (i1 + 1) * GROUP_W - 10
        y = base + PAD_B - 4
        # a polyline, not a path: a path's "H606"-style commands read as claim ids to check_badge_links
        out.append(_svg("polyline", {"points": f"{x0},{y - 5} {x0},{y} {x1},{y} {x1},{y - 5}", "fill": "none",
                                 "stroke": "var(--muted)", "stroke-dasharray": "3 3"}))
        out.append(_text((x0 + x1) / 2, y + 13, text, 9))
    return (f'<svg viewBox="0 0 {W} {H}" role="img" style="width:100%;min-width:{W}px;height:auto;">'
            + "".join(out) + "</svg>")


def _route_groups(d):
    pl = d["players"]

    def total(r):
        return sum(c["cases"] for c in r["cells"].values() if c)
    plain = [r for r in d["routes"] if r["name"] not in SAME_BAG1]
    pair = [r for r in d["routes"] if r["name"] in SAME_BAG1]
    order = sorted(plain, key=total, reverse=True) + pair
    groups = []
    for r in order:
        vals = {}
        for p in pl:
            c = r["cells"][p]
            if c is None:
                vals[p] = (0, 0, 0, None, f"{p} · {r['name']} · 對上 0 局")
                continue
            b1, b2, b3 = c["reach"]
            t = f"{p} · {r['name']} · 對上 {c['cases']} 局 · 入第二巡 {b2} · 第三巡或之後 {b3}"
            if c["pc"]:
                t += f" · 全消 {c['pc']}"
            vals[p] = (c["cases"], b2, b3, f"◆{c['pc']}" if c["pc"] else None, t)
        groups.append({"label": r["name"], "vals": vals})
    bracket = None
    if len(pair) == 2:
        bracket = (len(order) - 2, len(order) - 1, "同一塊第一巡板，唔好加埋")
    return groups, bracket


def _tech_groups(d):
    pl = d["players"]
    rows, zero = [], []
    for t in d["techs"]:
        if not any(t["cells"][p]["hits"] for p in pl):
            zero.append(t["name"])
            continue
        rows.append(t)
    rows.sort(key=lambda t: sum(t["cells"][p]["hits"] for p in pl), reverse=True)
    groups = []
    for t in rows:
        follow = "Tetris" if t["payoff"] else "第二個 T-spin"
        vals = {}
        for p in pl:
            c = t["cells"][p]
            if not c["hits"]:
                vals[p] = (0, 0, None, None, f"{p} · {t['name']} · 0 次")
                continue
            title = (f"{p} · {t['name']} · {c['hits']} 次 · 接到{follow} {c['fired']} 次"
                     f" · 開局 {c['opener']} · 中盤 {c['mid']}")
            vals[p] = (c["hits"], c["fired"], None, f"→{c['fired']}" if c["fired"] else None, title)
        groups.append({"label": t["name"], "spin": t["spin"], "vals": vals})
    return groups, zero


def panels(d):
    """The two panels' HTML, or '' when the night has no route / technique data."""
    e = html.escape
    pl = d["players"]
    out = [STYLE]

    groups, bracket = _route_groups(d)
    svg = chart(groups, pl, d["nrounds"], f"{d['nrounds']} 局", bracket=bracket)
    out += ['', '    <div class="chart-panel">',
            '      <h3>開局定式——今晚邊個開咗乜（模擬器，未經證明）</h3>',
            f'      <p class="cap">每條柱係嗰位玩家今晚有幾多局個第一巡對得上嗰頁嘅圖，頂格係今晚嘅 '
            f'{d["nrounds"]} 局；柱入面實色嗰條係喺可核範圍入面行到第二巡，再窄嗰條係第三巡或之後，'
            f'「◆」係打出嗰頁畫嘅全消。</p>',
            '      <div class="rc-key"><span><span class="rc-sw rc-pale"></span>對上第一巡</span>'
            '<span><span class="rc-sw rc-solid"></span>行到下一巡</span></div>',
            f'      <div class="scroll-x">{svg}</div>',
            f'      <p class="footnote">{QUARANTINE}</p>',
            '    </div>']

    groups, zero = _tech_groups(d)
    tsd = " / ".join(f"{e(p)} {d['tsd_den'][p]}" for p in pl)
    ymax = _nice_max(max([0] + [v[0] for g in groups for v in g["vals"].values()]), 10)
    out += ['', '    <div class="chart-panel">',
            '      <h3>中盤手法——T-spin 之前個形（模擬器，未經證明）</h3>',
            f'      <p class="cap">每條柱係嗰位玩家今晚有幾多個 T-spin 落之前個形對到嗰個手法；'
            f'柱入面實色嗰條係有幾多次接到嗰頁畫嘅下一步（第二個 T-spin，或者欄干同階段嘅 Tetris），'
            f'「→」係接到嘅次數。分母係今晚可核嘅 TSD：{tsd}；斜紋柱係 TSS 嘅形，冇每晚嘅分母。'
            f'幾次之差唔好當傾向。</p>',
            '      <div class="rc-key"><span><span class="rc-sw rc-pale"></span>對到個形</span>'
            '<span><span class="rc-sw rc-solid"></span>接到下一步</span>'
            '<span><span class="rc-sw rc-hatch"></span>TSS 嘅形</span></div>']
    if groups:
        svg = chart(groups, pl, ymax, str(ymax), hatch_of=lambda g: g["spin"] != "TSD")
        out.append(f'      <div class="scroll-x">{svg}</div>')
    if zero:
        out.append(f'      <p class="rc-zero">今晚兩位都係 0 次：{e("、".join(zero))}。</p>')
    shape = [(t["name"], sum(t["cells"][p].get("shape_only") or 0 for p in pl)) for t in d["techs"]]
    shape = [(n, k) for n, k in shape if k]
    if shape:
        # A `qualify` technique (社畜トレイン) is drawn by its qualifying hits only; say what was left out.
        out.append('      <p class="rc-zero">' + "、".join(f"{e(n)}另外有 {k} 次個形對到" for n, k in shape)
                   + "，但唔算砌出嚟（碎塊、垃圾、Kaidan 或 DPC），冇畫入柱。</p>")
    out += [f'      <p class="footnote">{QUARANTINE}</p>', '    </div>']
    return "\n".join(out)


def build(facts, report_dir):
    data = rts.load(report_dir)
    if data is None:
        return ""
    d = rts.compute(facts, data)
    d["tsd_den"] = data["tsd"]
    return panels(d)

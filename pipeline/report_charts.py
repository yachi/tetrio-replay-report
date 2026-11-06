"""Four small server-side charts that sit inside existing sections of the report.

    race_strip      戰況     — every match as a line of rounds: who led after each one
    video_timeline  影片     — the whole video on one axis, one tick per round
    intense_bars    最癲一局 — the selected round's table drawn as paired bars
    pc_squares      全消     — the rounds only one player had a Perfect Clear, won or lost

Added 2026-11-06 at yachi's request, after three independent reviews of the 2026-11-05 report
each asked for the first two and the third. Each chart draws numbers the section ALREADY prints
(or, for the race strip, the per-round winners the match cards already show as pips), so it adds
no figure a reader could not find in the text beside it: the strip and the timeline print no
number at all, and the bars and squares print only values the host section reads out of its own
proved claims and hands in here. Printed values go through `app_svg.num` (and so `fmt.quant`
with a `site=`); everything else here is a viewBox coordinate (`app_svg.coord`).

No script, no `innerHTML`, deterministic output. Colour is positional (`is-p1` / `is-p2` on the
legacy `--yachi` / `--pinglamb` tokens, which every report's :root defines). Every class is
`rc-` prefixed and `css(section_id)` scopes each rule under the host section's id, because
`check_generated_css` fails a rule that could match outside its own region and the same `rc-`
classes appear in four regions.
"""
from pipeline import app_svg
from pipeline.app_svg import coord, el, esc

_CSS = """
{s} .rc-fig {{ margin: 1.2rem 0 0; }}
{s} .rc-svg {{ display: block; width: 100%; height: auto; overflow: visible; }}
{s} .rc-svg text {{ font-family: var(--font-mono); font-size: 11px; fill: var(--muted); }}
{s} .rc-svg text.rc-lab {{ font-family: inherit; font-size: 13px; fill: var(--ink); }}
{s} .rc-svg text.rc-strong {{ font-weight: 700; fill: var(--ink); }}
{s} .rc-p1 {{ fill: var(--yachi); }}
{s} .rc-p2 {{ fill: var(--pinglamb); }}
{s} .rc-sp1 {{ stroke: var(--yachi); fill: none; }}
{s} .rc-sp2 {{ stroke: var(--pinglamb); fill: none; }}
{s} .rc-faint {{ opacity: .4; }}
{s} .rc-axis {{ stroke: var(--border-strong, var(--border)); stroke-width: 1; }}
{s} .rc-grid {{ stroke: var(--border); stroke-width: 1; stroke-dasharray: 2 3; }}
{s} .rc-line {{ stroke: var(--muted); stroke-width: 1.5; fill: none; }}
{s} .rc-ring {{ stroke: var(--ink); stroke-width: 1.5; fill: none; }}
{s} .rc-span {{ fill: var(--bg-sunken, var(--border)); }}
{s} .rc-rec {{ stroke-dasharray: 3 2; stroke: var(--muted); stroke-width: 1; }}
{s} .rc-legend {{ display: flex; flex-wrap: wrap; gap: .25rem 1rem; margin: .5rem 0 0;
  font-size: .78rem; color: var(--muted); }}
{s} .rc-note {{ margin: .4rem 0 0; font-size: .8rem; line-height: 1.8; color: var(--muted); }}
{s} .rc-key {{ display: inline-block; width: .6rem; height: .6rem; border-radius: 50%;
  margin-right: .3rem; vertical-align: -.05rem; }}
{s} .rc-key.rc-k1 {{ background: var(--yachi); }}
{s} .rc-key.rc-k2 {{ background: var(--pinglamb); }}
{s} .rc-key.rc-kring {{ background: none; border: 1.5px solid var(--ink); }}
"""


def css(section_id):
    """The chart rules, every selector pinned under `#<section_id>`."""
    return _CSS.format(s=f"#{section_id}")


def _cls(players, who, prefix="rc-p"):
    return f"{prefix}{1 if who == players[0] else 2}"


def legend(players, ring=None):
    """The key under a chart: one dot per player, plus an optional ring entry."""
    bits = [f'<span><span class="rc-key rc-k1"></span>{esc(players[0])} 贏</span>',
            f'<span><span class="rc-key rc-k2"></span>{esc(players[1])} 贏</span>']
    if ring:
        bits.append(f'<span><span class="rc-key rc-kring"></span>{esc(ring)}</span>')
    return '<div class="rc-legend">' + "".join(bits) + '</div>'


def _figure(svg_markup, players, ring=None):
    return ('<figure class="rc-fig">' + svg_markup + legend(players, ring) + '</figure>')


# ------------------------------------------------------------------ 1. race strip

def race_strip(facts, recovered=None, href=None):
    """One row per match: a dot per round in the winner's colour, drawn at the running lead.

    `recovered` is video.json's recovered list (or None); a recovered match is drawn after the
    replay match it follows with dashed dots and labelled 影片場, and its winners come from the
    video, not from facts.json. `href(match_position_or_None, round_index, rec)` returns a link for
    a dot, or None. The deciding round of a match that reached 4:4 is ringed.
    """
    players = facts["players"]
    rows = []
    rec_after = {r["after_position"]: r for r in (recovered or [])}
    for m in facts["matches"]:
        rows.append(("m", m, [r["winner"] for r in m["rounds"]]))
        if m["index"] in rec_after:
            rec = rec_after[m["index"]]
            rows.append(("v", rec, [r["winner"] for r in rec["rounds"]]))
    longest = max(len(ws) for _k, _m, ws in rows)
    step, x0, rh, amp = 40, 76, 44, 7
    width = x0 + (longest - 1) * step + 70
    height = 22 + len(rows) * rh
    kids = [el("text", {"x": x0, "y": 12, "text_anchor": "middle"}, text="第1局"),
            el("text", {"x": x0 + (longest - 1) * step, "y": 12, "text_anchor": "middle"},
               text=f"第{longest}局")]
    for i, (kind, m, ws) in enumerate(rows):
        mid = 22 + i * rh + rh / 2
        name = "影片場" if kind == "v" else f"第{m['index']}場"
        kids.append(el("text", {"class": "rc-lab", "x": 0, "y": mid + 4}, text=name))
        kids.append(el("line", {"class": "rc-axis", "x1": x0 - 12,
                                "x2": x0 + (longest - 1) * step + 12, "y1": mid, "y2": mid}))
        lead, pts = 0, [(x0 - 12, mid)]
        for j, w in enumerate(ws):
            lead += 1 if w == players[0] else -1
            pts.append((x0 + j * step, mid - lead * amp))
        kids.append(el("polyline", {"class": "rc-line",
                                    "points": " ".join(f"{coord(a)},{coord(b)}" for a, b in pts)}))
        tally = {p: 0 for p in players}
        final = max(ws.count(p) for p in players)
        for j, w in enumerate(ws):
            before = dict(tally)
            tally[w] += 1
            cx, cy = pts[j + 1]
            dot_cls = _cls(players, w) + (" rc-rec" if kind == "v" else "")
            tip = (f"{name} 第{j + 1}局 · {w} 贏 · 打完 "
                   f"{tally[players[0]]}:{tally[players[1]]}")
            parts = [app_svg.title(tip),
                     el("circle", {"class": dot_cls, "cx": cx, "cy": cy, "r": 7})]
            if j == len(ws) - 1 and before[players[0]] == before[players[1]] == final - 1:
                parts.append(el("circle", {"class": "rc-ring", "cx": cx, "cy": cy, "r": 11}))
            link = href(m["index"] if kind == "m" else None, j, m if kind == "v" else None) \
                if href else None
            kids.append(el("a", {"href": link, "target": "_blank", "rel": "noopener"}, *parts)
                        if link else el("g", None, *parts))
        kids.append(el("text", {"class": "rc-lab", "x": width, "y": mid + 4,
                                "text_anchor": "end"},
                       el("tspan", {"class": "rc-p1"}, text=str(tally[players[0]])),
                       el("tspan", None, text=":"),
                       el("tspan", {"class": "rc-p2"}, text=str(tally[players[1]]))))
    svg = app_svg.svg(width, height, kids, "每場逐局邊個領先", cls="rc-svg")
    return _figure(svg, players, ring="打到 4:4 嘅決勝局")


# ------------------------------------------------------------------ 2. video timeline

def _clock(s):
    s = int(s)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def video_timeline(facts, data, href):
    """The whole video on one axis: a grey span per match and one tick per round in the winner's
    colour, each linking to that round. A recovered (video-only) match's span is dashed."""
    players = facts["players"]
    dur = data["video"]["duration_s"]
    width, height = 720, 80
    sx = lambda s: 6 + s / dur * (width - 12)  # noqa: E731
    kids = []
    tick = 0
    while tick <= dur:
        x = sx(tick)
        kids.append(el("line", {"class": "rc-grid", "x1": x, "x2": x, "y1": 14, "y2": 58}))
        kids.append(el("text", {"x": x, "y": 74, "text_anchor": "start" if tick == 0 else "middle"},
                       text=_clock(tick)[:-3] if tick >= 3600 else _clock(tick)))
        tick += 1800
    spans = []
    rec_after = {r["after_position"]: r for r in data.get("recovered", [])}
    for v, m in zip(data["matches"], facts["matches"]):
        spans.append((str(v["position"]), [r["play_start_s"] for r in v["rounds"]],
                      [r["winner"] for r in m["rounds"]], [r["replay_s"] for r in v["rounds"]],
                      False))
        rec = rec_after.get(v["position"])
        if rec:
            spans.append(("影", [r["play_start_s"] for r in rec["rounds"]],
                          [r["winner"] for r in rec["rounds"]],
                          [r["end_s"] - r["play_start_s"] for r in rec["rounds"]], True))
    for label, starts, winners, lengths, is_rec in spans:
        a, b = sx(starts[0]), sx(starts[-1] + lengths[-1])
        kids.append(el("rect", {"class": "rc-span" + (" rc-rec" if is_rec else ""),
                                "x": a, "y": 20, "width": max(b - a, 2), "height": 32, "rx": 3}))
        kids.append(el("text", {"x": (a + b) / 2, "y": 12, "text_anchor": "middle"}, text=label))
        for j, (t, w) in enumerate(zip(starts, winners)):
            name = "影片場" if is_rec else f"第{label}場"
            bar = el("rect", {"class": _cls(players, w), "x": sx(t) - 1.5, "y": 24,
                              "width": 3, "height": 24})
            kids.append(el("a", {"href": href(t), "target": "_blank", "rel": "noopener"},
                           app_svg.title(f"{name} 第{j + 1}局 · {w} 贏 · {_clock(t)}"), bar))
    svg = app_svg.svg(width, height, kids, "成晚每一局喺影片邊度", cls="rc-svg")
    return _figure(svg, players)


# ------------------------------------------------------------------ 3. intense-round bars

def intense_bars(players, rows, winner):
    """Paired horizontal bars, loser on the left and winner on the right.

    `rows` is [(label, {player: value}, printed {player: str}, winner_behind)] — the values and
    their printed strings come from the host section's proved claims, so nothing is formatted
    here. A row the winner trailed on is bold, and on it the LEADING side is drawn solid and the
    other faint, so the eye goes straight to where the winner lost.
    """
    loser = next(p for p in players if p != winner)
    width, rh, half, gap = 560, 26, 180, 52
    c = width / 2
    height = 26 + len(rows) * rh
    kids = [el("text", {"class": "rc-lab", "x": c - gap, "y": 14, "text_anchor": "end"},
               text=f"{loser}（輸）"),
            el("text", {"class": "rc-lab", "x": c + gap, "y": 14}, text=f"{winner}（贏）")]
    for i, (label, vals, shown, behind) in enumerate(rows):
        y = 24 + i * rh
        top = max(vals[loser], vals[winner]) or 1
        wl, ww = vals[loser] / top * half, vals[winner] / top * half
        lead_is_loser = vals[loser] > vals[winner]
        kids.append(el("rect", {"class": _cls(players, loser) + ("" if lead_is_loser else " rc-faint"),
                                "x": c - gap - wl, "y": y, "width": wl, "height": 16}))
        kids.append(el("rect", {"class": _cls(players, winner) + (" rc-faint" if lead_is_loser else ""),
                                "x": c + gap, "y": y, "width": ww, "height": 16}))
        kids.append(el("text", {"class": "rc-lab" + (" rc-strong" if behind else ""),
                                "x": c, "y": y + 12, "text_anchor": "middle"}, text=label))
        kids.append(el("text", {"x": c - gap - wl - 4, "y": y + 12, "text_anchor": "end"},
                       text=shown[loser]))
        kids.append(el("text", {"x": c + gap + ww + 4, "y": y + 12}, text=shown[winner]))
    svg = app_svg.svg(width, height, kids, "最癲一局兩邊每項數據對比", cls="rc-svg")
    return '<figure class="rc-fig">' + svg + '</figure>'


# ------------------------------------------------------------------ 4. PC squares

def pc_squares(players, rows):
    """One square per round in which only this player had a Perfect Clear: solid if they won
    it, outlined if they lost. `rows` is [(player, solo, lost)] from the proved pc_solo_lost
    claims; the printed figures are those two counts."""
    width, rh, size, step = 560, 34, 22, 28
    height = 8 + len(rows) * rh
    kids = []
    for i, (who, solo, lost) in enumerate(rows):
        y = 6 + i * rh
        kids.append(el("text", {"class": "rc-lab", "x": 0, "y": y + 16}, text=who))
        won = solo - lost
        for j in range(solo):
            cls = _cls(players, who) if j < won else _cls(players, who, "rc-sp")
            kids.append(el("rect", {"class": cls, "x": 90 + j * step, "y": y, "width": size,
                                    "height": size, "rx": 4, "stroke_width": 2}))
        kids.append(el("text", {"x": 90 + solo * step + 6, "y": y + 16},
                       text=f"{solo} 局，輸咗 {lost}"))
    svg = app_svg.svg(width, height, kids, "淨係一個人有全消嗰啲局邊個贏", cls="rc-svg")
    key = ('<div class="rc-legend"><span>實心：有全消嗰個贏咗嗰局</span>'
           '<span>空心：佢輸咗</span></div>')
    return '<figure class="rc-fig">' + svg + key + '</figure>'

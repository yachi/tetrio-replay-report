"""TST 開局排名 — the two-bag TST shapes ranked by how likely a random deal builds them and then clears a
Perfect Clear: `docs/tst-openers.html`.

    python3 -m pipeline.tst_openers_page --out-dir /tmp/tst   # render it somewhere other than docs/
    python3 -m pipeline.tst_openers_page --selftest           # the audit's mutants

Inputs, both committed and nothing else: `analysis/tst-openers.json` (the merged enumeration: per shape its
tilings with their counts, and the sampled bag-4 lines) and `pipeline/openers/tst-openers-shapes.json` (the
shapes: source names, cells, the T's slot, and the `sources` block). The artefact is CONSTRUCTED and
quarantined: nobody played these boards, no claim id, no badge. The audit reuses
`replay_page.audit_quarantine` and adds:

* every ranked shape has exactly one card, in rank order, and every card's four figures are RECOMPUTED from the
  artefact (a second, independent computation: best tiling by direct search, exact fractions);
* the inlined data island equals what the renderer builds from the artefact;
* `未計` where the two-bag count is zero (never a `0%` PC), `≈` on every sampled bag-4 figure;
* no simplified glyph, no external request, no markup sink.

ROUNDING: every percentage is FLOORED, never rounded (the repo's 約 convention, `fmt.py`): a figure supporting
a ranking must not read higher than the exact value. Computation is exact (`fractions.Fraction`), so a floor is
never an artefact of float noise; the JS only draws strings this module has already floored.
"""
import argparse
import html
import json
import math
import os
import re
import sys
from fractions import Fraction

from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline.claims.build_claims import SIMPLIFIED

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OVERVIEW = "tst-openers.html"
PREFIX = "tst-openers"
ART_PATH = os.path.join(REPO, "analysis", "tst-openers.json")
SHAPES_PATH = os.path.join(REPO, "pipeline", "openers", "tst-openers-shapes.json")
PROSE_PATH = os.path.join(HERE, "tst_openers_prose.json")
CSS_PATH = os.path.join(HERE, "tst_openers_page.css")
JS_PATH = os.path.join(HERE, "tst_openers_page.js")
DATA_ID = "data"

BAG = math.factorial(7)           # deals of one bag; two bags give BAG ** 2 orders
N2 = BAG * BAG
LEFT_NOTE_MIN = 3                 # a leftover of this many pieces or more makes the PC count approximate
WALL = 2                          # a TST this close to a side wall (cells) counts as 近牆
HID_SHOWN = 6                     # how many hidden wall ranks the filter note names
COL = dict(I="#2fb8c9", O="#e3b425", T="#9a46d6", S="#4cb648", Z="#d9433d", J="#3b61d6", L="#e5792a")

_CARD = re.compile(r'<article class="card[^"]*" data-pos="[^"]*" data-card="(\d+)" data-rk="([^"]*)">(.*?)</article>', re.S)
_FIG = re.compile(r'data-f="(\w+)">(.*?)</b>', re.S)
_ISLAND = re.compile(r'<script id="data" type="application/json">(.*?)</script>', re.S)


def _need(cond, msg):
    if not cond:
        raise ValueError(f"tst openers page: {msg}")


def _esc(s):
    return html.escape(str(s), quote=True)


# ------------------------------------------------------------------ figures

def pct(v):
    """A percentage of the exact fraction `v`, FLOORED (see the module note): one decimal from 0.1%, two
    below it, `0%` for exactly zero and `<0.01%` for a positive value that floors to nothing."""
    v = Fraction(v)
    if v == 0:
        return "0%"
    if v >= Fraction(1, 1000):
        n = math.floor(v * 1000)
        return f"{n // 10}.{n % 10}%"
    n = math.floor(v * 10000)
    return "<0.01%" if n == 0 else f"0.{n:02d}%"


def load_inputs(repo=REPO):
    with open(os.path.join(repo, "analysis", "tst-openers.json"), encoding="utf-8") as f:
        art = json.load(f)
    with open(os.path.join(repo, "pipeline", "openers", "tst-openers-shapes.json"), encoding="utf-8") as f:
        shp = json.load(f)
    _need(art.get("report_eligible") is False and art.get("constructed") is True,
          "the artefact is not marked report_eligible: false / constructed: true")
    _need([s["id"] for s in art["shapes"]] == list(range(len(art["shapes"]))), "artefact shape ids are not the index")
    by = {s["id"]: s for s in shp["shapes"]}
    _need(set(by) == {s["id"] for s in art["shapes"]}, "the shapes file and the artefact name different shapes")
    return art, shp


def load_prose(path=PROSE_PATH):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    _need(not (set(text) & SIMPLIFIED), f"the prose carries simplified glyph(s) {sorted(set(text) & SIMPLIFIED)}")
    return json.loads(text)


def p4_index(art):
    """'rows|left' -> its sampled record; a record with no draws is no record (gen.py's `not r['n']`)."""
    return {r["line"]: r for r in art["pc4"] if r["n"]}


def line_of(o, t):
    return ",".join(map(str, o["rows"])) + "|" + t["left"]


def tiling_p4(o, t, idx):
    """(P(PC by bag 4) as an exact fraction or None, draws behind it, 0 when exact)."""
    if t["p5"] >= BAG:
        return Fraction(1), 0
    r = idx.get(line_of(o, t))
    if not r:
        return None, 0
    return Fraction(t["p5"] * r["n"] + (BAG - t["p5"]) * r["ok"], BAG * r["n"]), r["n"]


def score(t, p4):
    """What a tiling is ranked by: its two-bag count times its bag-4 PC chance (the bag-3 chance when none)."""
    return t["B"] * (p4 if p4 is not None else Fraction(t["p5"], BAG))


def fig_strings(t, p4, n4):
    """The four printed figures of one tiling: (two-bag, bag-3 PC, bag-4 PC, joint) as display strings."""
    two = pct(Fraction(t["B"], N2))
    if t["B"] == 0:
        pc3 = pc4 = "未計"
    else:
        pc3 = pct(Fraction(t["p5"], BAG))
        pc4 = "–" if p4 is None else (("≈" + pct(p4)) if n4 else pct(p4))
    return two, pc3, pc4, pct(score(t, p4) / N2)


def grid(t):
    g = {}
    for k, cs in t["pieces"]:
        for c in cs:
            g[c] = k
    H = max(c // 10 for c in g) + 1
    return "".join("".join(g.get(y * 10 + x, ".") for x in range(10)) for y in range(H - 1, -1, -1))


def mirror_key(s):
    occ = frozenset(map(tuple, s["cells"]))
    t = frozenset(map(tuple, s["tst"]))
    m = lambda S: frozenset((9 - x, y) for x, y in S)
    a = (tuple(sorted(occ)), tuple(sorted(t)))
    b = (tuple(sorted(m(occ))), tuple(sorted(m(t))))
    return min(a, b)


def entries(art, shp):
    """The ranked list: one entry per shape up to left-right mirroring, best tiling picked, sorted by
    (-joint, -two); a shape with no tiling at all is not ranked."""
    shapes = {s["id"]: s for s in shp["shapes"]}
    idx = p4_index(art)
    rows = {}
    for o in art["shapes"]:
        if not o["til"]:
            continue
        s = shapes[o["id"]]
        scored = [(t, *tiling_p4(o, t, idx)) for t in o["til"]]
        best = max(scored, key=lambda x: (score(x[0], x[1]), x[0]["B"]))
        t, p4, n4 = best
        e = dict(s=s, o=o, best=t, p4=p4, n4=n4, joint=score(t, p4) / N2, two=Fraction(t["B"], N2), scored=scored)
        k = mirror_key(s)
        if k in rows:
            p = rows[k]
            names = sorted(set(p["names"]) | set(s["names"]))
            p["names"] = names
            p["mirror"] = True
            if (e["joint"], e["two"]) > (p["joint"], p["two"]):
                e["names"], e["mirror"] = names, True
                rows[k] = e
        else:
            e["names"], e["mirror"] = list(s["names"]), False
            rows[k] = e
    return sorted(rows.values(), key=lambda e: (-e["joint"], -e["two"]))


def dist(s):
    xs = [x for x, y in s["tst"]]
    return min(min(xs), 9 - max(xs))


def is_me(e):
    return any(x.strip() == "yachi" for x in e["names"])


def structure(ents):
    """full cells, the full list, the partial groups (ordered: the group holding the player first, then by size)."""
    full = max(len(e["s"]["cells"]) for e in ents)
    F = [e for e in ents if len(e["s"]["cells"]) == full]
    P = [e for e in ents if len(e["s"]["cells"]) < full]
    groups = {}
    for e in P:
        groups.setdefault(len(e["s"]["cells"]), []).append(e)
    order = sorted(groups, key=lambda n: (not any(is_me(e) for e in groups[n]), -n))
    me_cells = next((n for n in order if any(is_me(e) for e in groups[n])), 0)
    me = next((i + 1 for i, e in enumerate(groups.get(me_cells, [])) if is_me(e)), 0)
    return full, F, P, groups, order, me_cells, me


def build_data(ents, prose):
    """The island: per shape the player-facing rows (grid, four figure strings, leftover), best first."""
    shapes = {}
    for e in ents:
        rows = sorted(e["scored"], key=lambda x: -score(x[0], x[1]))
        shapes[f"s{e['s']['id']}"] = dict(
            tst=e["s"]["tst"],
            t=[[grid(t), *fig_strings(t, p4, n4), t["left"]] for t, p4, n4 in rows])
    return dict(labels=prose["labels"], filter_default=prose["pos_centre"], shapes=shapes)


# ------------------------------------------------------------------ drawing

def svg(cells, H, cs=14, tst=()):
    W = 10
    r = [f'<svg class="board" width="{W * cs}" height="{H * cs}" viewBox="0 0 {W * cs} {H * cs}" role="img">',
         f'<rect width="{W * cs}" height="{H * cs}" fill="var(--well)"/>']
    for x in range(W):
        for y in range(H):
            r.append(f'<rect x="{x * cs + .5}" y="{(H - 1 - y) * cs + .5}" width="{cs - 1}" height="{cs - 1}" fill="var(--grid)"/>')
    for (x, y), k in cells.items():
        r.append(f'<rect x="{x * cs + .5}" y="{(H - 1 - y) * cs + .5}" width="{cs - 1}" height="{cs - 1}" fill="{COL.get(k, "#8a8f9c")}"/>')
    for (x, y) in tst:
        r.append(f'<rect x="{x * cs + 2}" y="{(H - 1 - y) * cs + 2}" width="{cs - 4}" height="{cs - 4}" fill="none" '
                 f'stroke="#c77dff" stroke-width="2" stroke-dasharray="3 2"/>')
    r.append("</svg>")
    return "".join(r)


def card(rk, e, PR, badge=""):
    C = PR["card"]
    s, b = e["s"], e["best"]
    cells = {}
    for k, cs in b["pieces"]:
        for c in cs:
            cells[(c % 10, c // 10)] = k
    H = max(y for x, y in cells) + 1
    tst = [tuple(t) for t in s["tst"]]
    for t in tst:
        cells.pop(t, None)
    res = {}
    for y, r in enumerate(e["o"]["rows"]):
        for x in range(10):
            if r >> x & 1:
                res[(x, y)] = "G"
    rh = max(4, len(e["o"]["rows"]))
    names = [PR["me_name"] if x.strip() == "yachi" else x.strip() for x in e["names"]]
    shown = ", ".join(_esc(x) for x in names[:4]) + (PR["names_more"].format(c=len(names)) if len(names) > 4 else "")
    d = dist(s)
    pos = PR["pos_centre"] if d >= WALL else PR["pos_wall"]
    left = b["left"] or C["no_left"]
    two, pc3, pc4, joint = fig_strings(b, e["p4"], e["n4"])
    pc4_html = f'<span title="{_esc(C["sample_title"].format(n=e["n4"]))}">{_esc(pc4)}</span>' if pc4.startswith("≈") else _esc(pc4)
    note = ""
    if b["B"] == 0:
        note = C["uncounted_note"]
    elif len(b["left"]) >= LEFT_NOTE_MIN:
        note = C["left_note"].format(c=len(b["left"]))
    note = f'<div class="muted sm warn">{_esc(note)}</div>' if note else ""
    cls = " me" if PR["me_name"] in names else ""
    line = C["pos_line"].format(pos=pos, d=d, cells=len(s["cells"]), nt=e["o"]["ntil"], left=left,
                                mirror=C["mirror"] if e["mirror"] else "")
    return (f'<article class="card{cls}" data-pos="{pos}" data-card="{s["id"]}" data-rk="{_esc(rk)}">'
            f'<div class="rk num">{_esc(rk)}</div>{badge}\n'
            f'<div class="bd">{svg(cells, max(H, 8), 15, tst)}<div class="small"><div class="lab">{_esc(C["left_title"])}</div>{svg(res, rh, 9)}</div></div>\n'
            f'<div class="meta"><div class="src">{shown}</div>\n'
            f'<div class="stats"><span>{C["two"]} <b class="num" data-f="two">{two}</b></span>'
            f'<span>{C["pc3"]} <b class="num" data-f="pc3">{_esc(pc3)}</b></span>'
            f'<span>{C["pc4"]} <b class="num" data-f="pc4">{pc4_html}</b></span>'
            f'<span class="j">{C["joint"]} <b class="num" data-f="joint">{joint}</b></span></div>{note}\n'
            f'<div class="muted sm">{_esc(line)}</div>\n'
            f'<details data-s="s{s["id"]}"><summary>{_esc(C["details"].format(nt=e["o"]["ntil"]))}</summary><div class="tl"></div></details></div></article>')


def render(art, shp, PR):
    ents = entries(art, shp)
    full, F, P, groups, order, me_cells, me = structure(ents)
    cent = [i + 1 for i, e in enumerate(F) if dist(e["s"]) >= WALL]
    hid = [i + 1 for i, e in enumerate(F) if dist(e["s"]) < WALL and i + 1 < cent[0] + 10]
    sample = max(r["n"] for r in art["pc4"])
    jb = "、".join(k.replace("johnbeak Gamushiro ", "") for k in shp["sources"]["johnbeak"]["fumens"])
    fmt = dict(n=len(ents), n_hd=len(shp["sources"]["harddrop"]["titles"]), jb=jb, sample=sample, full=full, pieces=full // 4,
               nf=len(F), np=len(P), me=me, me_cells=me_cells, nc=len(cent), left_min=LEFT_NOTE_MIN, wall=WALL,
               hid="、".join(f"#{i}" for i in hid[:HID_SHOWN]))
    me_sentence = PR["me_sentence"].format(**fmt) if me else ""
    cards = "\n".join(card(f"#{i + 1}", e, PR) for i, e in enumerate(F))
    pc = []
    for n in order:
        g = groups[n]
        k = (full - n) // 4
        pc.append(f'<h3 class="gh">{_esc(PR["group_head"].format(n=n, k=k, c=len(g)))}</h3><div class="grid">')
        pc += [card(f"{n}格 #{i + 1}", e, PR, f'<div class="badge">{_esc(PR["group_badge"].format(n=n, k=k))}</div>') for i, e in enumerate(g)]
        pc.append("</div>")
    title = PR["title"] + RS.TITLE_MARK
    data = json.dumps(build_data(ents, PR), separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    with open(CSS_PATH, encoding="utf-8") as f:
        css = f.read().strip("\n")
    with open(JS_PATH, encoding="utf-8") as f:
        js = f.read().strip("\n")
    out = ['<!doctype html><html lang="zh-HK"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           f"<title>{_esc(title)}</title>", f'<meta name="description" content="{_esc(PR["desc"])}">',
           "<style>", css, "</style></head><body><main>",
           f'<nav class="sm"><a href="index.html">{_esc(PR["back"])}</a></nav>',
           f'<div class="eyebrow">{RS.EYEBROW}</div>', f"<h1>{_esc(title)}</h1>",
           f'<p class="quar">{PR["quarantine"]}</p>']
    out += [f"<p>{t.format(me_sentence=me_sentence, **fmt)}</p>" for t in PR["intro"]]
    out += [f'<p class="muted sm">{_esc(PR["note_names"])}</p>',
            f'<details class="sm"><summary><b>{_esc(PR["reading_summary"])}</b></summary>\n<ul>']
    out += [f"<li>{t.format(**fmt)}</li>" for t in PR["reading"]]
    out += ["</ul></details>",
            f'<div class="bar"><button aria-pressed="true" data-f="{PR["pos_centre"]}">{_esc(PR["filter_centre"].format(**fmt))}</button>'
            f'<button aria-pressed="false" data-f="all">{_esc(PR["filter_all"])}</button></div>',
            f'<p class="muted sm">{_esc(PR["filter_note"].format(**fmt))}</p>',
            f'<h2>{_esc(PR["h2_full"].format(**fmt))}</h2>', '<div class="grid" id="g">', cards, "</div>",
            f'<h2>{_esc(PR["h2_partial"].format(**fmt))}</h2>',
            f'<p class="muted">{_esc(PR["partial_note"].format(me_top=PR["me_top"].format(**fmt) if me else "", **fmt))}</p>']
    out += pc
    out += ["</main>", f'<script id="{DATA_ID}" type="application/json">{data}</script>', "<script>", js, "</script></body></html>"]
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ audit

def expected_card(art, sid, idx):
    """The four figures of shape `sid`, computed from the artefact alone and by a different route from
    `entries()`: a direct scan for the best tiling, exact fractions throughout."""
    o = art["shapes"][sid]
    best = None
    for t in o["til"]:
        if t["p5"] >= BAG:
            p4, n4 = Fraction(1), 0
        else:
            r = idx.get(",".join(str(x) for x in o["rows"]) + "|" + t["left"])
            p4, n4 = (None, 0) if r is None else (Fraction(t["p5"]) / BAG + (1 - Fraction(t["p5"]) / BAG) * Fraction(r["ok"], r["n"]), r["n"])
        sc = t["B"] * (p4 if p4 is not None else Fraction(t["p5"], BAG))
        if best is None or (sc, t["B"]) > (best[0], best[1]["B"]):
            best = (sc, t, p4, n4)
    sc, t, p4, n4 = best
    two = pct(Fraction(t["B"], N2))
    if t["B"] == 0:
        return [two, "未計", "未計", pct(sc / N2)]
    pc4 = "–" if p4 is None else (("≈" if n4 else "") + pct(p4))
    return [two, pct(Fraction(t["p5"], BAG)), pc4, pct(sc / N2)]


def audit(page, art, shp, PR):
    bad = RP.audit_quarantine(page, [RS.EYEBROW, RS.NO_CLAIM, PR["quarantine"]], DATA_ID)
    if set(page) & SIMPLIFIED:
        bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
    ents = entries(art, shp)
    idx = p4_index(art)
    cards = _CARD.findall(page)
    full, F, P, groups, order, me_cells, me = structure(ents)
    want = [e["s"]["id"] for e in F] + [e["s"]["id"] for n in order for e in groups[n]]
    got = [int(c[0]) for c in cards]
    if got != want:
        bad.append(f"the cards are not one per ranked shape in rank order (page {len(got)}, artefact {len(want)})")
    for sid, rk, body in cards:
        figs = {k: re.sub(r"<[^>]+>", "", html.unescape(v)) for k, v in _FIG.findall(body)}
        exp = expected_card(art, int(sid), idx)
        pr = [figs.get(k) for k in ("two", "pc3", "pc4", "joint")]
        if pr != exp:
            bad.append(f"card {rk}: printed figures {pr} are not the recomputed {exp}")
        if "未計" in exp and ("0%" in pr[1:3]):
            bad.append(f"card {rk}: a 0% PC where 未計 is required")
        if ("≈" in exp[2]) != ("≈" in (pr[2] or "")):
            bad.append(f"card {rk}: the ≈ of a sampled figure is missing or spurious")
    m = _ISLAND.search(page)
    if not m:
        bad.append("no data island")
    else:
        try:
            island = json.loads(m.group(1).replace("<\\/", "</"))
        except ValueError:
            island = None
        if island != build_data(ents, PR):
            bad.append("the data island is not what the artefact builds")
    return bad


# ------------------------------------------------------------------ driver

def render_all(repo=REPO, inputs=None, prose=None):
    art, shp = inputs or load_inputs(repo)
    PR = prose or load_prose()
    page = render(art, shp, PR)
    bad = audit(page, art, shp, PR)
    _need(not bad, "; ".join(bad[:5]))
    return {OVERVIEW: page}


def selftest(repo=REPO):
    art, shp = load_inputs(repo)
    PR = load_prose()
    page = render(art, shp, PR)
    killed = survived = 0

    def expect(label, mutated, want):
        nonlocal killed, survived
        bad = audit(mutated, art, shp, PR)
        if bool(bad) == want:
            killed += want
            print(f'  {"killed" if want else "passed"}: {label}')
        else:
            survived += 1
            print(f'  {"SURVIVED" if want else "FAILED control"}: {label} {bad[:2]}', file=sys.stderr)

    def sub(pattern, fn, flags=0):
        m = re.search(pattern, page, flags)
        _need(m, f"selftest: nothing to plant at {pattern!r}")
        return page[:m.start(1)] + fn(m.group(1)) + page[m.end(1):]

    expect("the rendered page (control)", page, False)
    expect("the quarantine sentence deleted", page.replace(PR["quarantine"], "", 1), True)
    expect("a claim badge planted", page.replace("</h1>", '<span data-claim="C001">✓</span></h1>', 1), True)
    expect("a card's joint figure edited", sub(r'data-f="joint">(\d)', lambda d: str((int(d) + 1) % 10)), True)
    expect("a card's two-bag figure edited", sub(r'data-f="two">(\d)', lambda d: str((int(d) + 1) % 10)), True)
    m = _CARD.search(page)
    expect("a card dropped", page.replace(m.group(0), "", 1), True)
    expect("a simplified glyph", page.replace("</h1>", "<p>实</p></h1>", 1), True)
    expect("≈ removed from a sampled figure", sub(r'data-f="pc4"><span title="[^"]*">(≈)', lambda _: ""), True)
    _need("未計" in page, "selftest: no 未計 card to plant 0% at")
    expect("0% shown where 未計 is required", sub(r'data-f="pc3">(未計)', lambda _: "0%"), True)
    expect("an island figure edited", sub(r'"t":\[\["[A-Z.]+","[^"]*","[^"]*","[^"]*","(\d)', lambda d: str((int(d) + 1) % 10)), True)
    expect("an external request planted", page.replace("<style>", '<link rel="stylesheet" href="https://x.example/a.css"><style>', 1), True)
    print(f"selftest: {killed} killed, {survived} survived")
    return 1 if survived else 0


def site_card(inputs=None, prose=None):
    art, shp = inputs or load_inputs()
    PR = prose or load_prose()
    return {"href": OVERVIEW, "cases": len(entries(art, shp)), "unit": "個形", "kicker": PR["index_card"]["kicker"],
            "title": PR["overview_title"], "blurb": PR["index_card"]["blurb"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    d = a.out_dir or os.path.join(REPO, "docs")
    os.makedirs(d, exist_ok=True)
    for name, page in render_all().items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(page)
        print(f"wrote {os.path.join(d, name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

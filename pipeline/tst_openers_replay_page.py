"""實戰對照: for every night and round, the bag-1 board each player really built against the board the TST opener ranking
(`docs/tst-openers.html`) says is best for the bag-1 order dealt: `docs/tst-openers-choices.html`.

    python3 -m pipeline.tst_openers_replay_page --out-dir /tmp/tst   # render it somewhere other than docs/
    python3 -m pipeline.tst_openers_replay_page --selftest           # the audit's mutants

Input: `analysis/tst-openers-tp-replay.json` (`pipeline/sim/emit-tst-opener-choices.py`, one row per player-round, integer
chance numerators out of 5040^2) and the ranking artefact `analysis/tst-openers-tp.json` (the boards' pieces, for drawing).
CONSTRUCTED and quarantined: the replays are the corpus's, the chances are the ranking's, nobody played the ranking's
boards: no claim id, no badge. Every figure is read off the artefact; a mean is taken over MATCHED rounds only and is always
printed as N / M, and the page says matched rounds are a selected subset and that J assumes a TST-then-PC plan.

The audit (inside `render_all`) recomputes every printed figure by a second route (explicit loops over the rows, written
independently of the renderer's), checks every per-round chance and status against the artefact, the status partition, the md5s
of every input, every drawn board against the ranking's pieces (read back out of the svg), the replay links, and the
quarantine, glyph and badge rules. ROUNDING: every percentage is floored (`tst_openers_page.pct`), computed in exact fractions.
"""
import argparse
import copy
import hashlib
import html
import json
import math
import os
import re
import sys
from fractions import Fraction

from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline import tst_openers_page as OP
from pipeline.claims.build_claims import SIMPLIFIED

HERE = OP.HERE
REPO = OP.REPO
OVERVIEW = "tst-openers-choices.html"
RANKING = "tst-openers.html"
ART_PATH = os.path.join(REPO, "analysis", "tst-openers-tp-replay.json")
TP_PATH = os.path.join(REPO, "analysis", "tst-openers-tp.json")
B1_PATH = os.path.join(REPO, "analysis", "tst-openers-tp-b1.json")
EMIT_PATH = os.path.join(REPO, "pipeline", "sim", "emit-tst-opener-choices.py")
PROSE_PATH = os.path.join(HERE, "tst_openers_replay_prose.json")
CSS_PATH = os.path.join(HERE, "tst_openers_replay_page.css")
DATA_ID = "data"
BK_SHOWN = "2"
SWAPS_SHOWN = 6
SEVEN_SHOWN = 8
COL = OP.COL
BY_COL = {v: k for k, v in COL.items()}
STATUSES = ["matched", "not_kept", "garbage_or_clear", "seven_placed_no_hold", "hold_not_bag1", "short_round"]
SCHEMA = "tst-openers-replay/1"


def _need(cond, msg):
    if not cond:
        raise ValueError(f"tst openers replay page: {msg}")


def _esc(s):
    return html.escape(str(s), quote=True)


def md5(b):
    return hashlib.md5(b).hexdigest()


def pct(num, den):
    return OP.pct(Fraction(num, den)) if den else "–"


def fl1(v):
    """A non-negative exact fraction FLOORED to one decimal place."""
    v = Fraction(v)
    n = math.floor(v * 10)
    return f"{n // 10}.{n % 10}"


# ------------------------------------------------------------------ inputs

def load_inputs(repo=REPO):
    """(artefact, ranking artefact). Refuses an artefact built from other inputs."""
    with open(os.path.join(repo, "analysis", "tst-openers-tp-replay.json"), "rb") as f:
        art = json.loads(f.read())
    with open(os.path.join(repo, "analysis", "tst-openers-tp.json"), "rb") as f:
        tp_raw = f.read()
    with open(os.path.join(repo, "analysis", "tst-openers-tp-b1.json"), "rb") as f:
        b1_raw = f.read()
    with open(os.path.join(repo, "pipeline", "sim", "emit-tst-opener-choices.py"), "rb") as f:
        em_raw = f.read()
    _need(art["schema"] == SCHEMA and art["report_eligible"] is False and art["constructed"] is True,
          f"the artefact is not {SCHEMA} marked report_eligible: false / constructed: true")
    m = art["md5"]
    _need(m["tp"] == md5(tp_raw), "analysis/tst-openers-tp-replay.json was built from another analysis/tst-openers-tp.json")
    _need(m["b1"] == md5(b1_raw), "analysis/tst-openers-tp-replay.json was built from another analysis/tst-openers-tp-b1.json")
    _need(m["emitter"] == md5(em_raw), "analysis/tst-openers-tp-replay.json was built by another emit-tst-opener-choices.py")
    _need(sorted(m["replay_facts"]) == sorted(art["sessions"]), "the artefact's replay md5s do not name its sessions")
    for s, h in m["replay_facts"].items():
        with open(os.path.join(repo, "sessions", s, "sim", "replay-facts.json"), "rb") as f:
            _need(md5(f.read()) == h, f"{s}'s replay-facts.json changed since the artefact was built")
    return art, json.loads(tp_raw)


def load_prose(path=PROSE_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def users(art):
    return sorted({r["u"] for r in art["rows"]})


# ------------------------------------------------------------------ figures (renderer's route)

def stats(rows, bk, n2):
    """Integer sums over `rows` (one player's, or one player-night's) at budget `bk`."""
    st = dict(M=len(rows), N=0, sa=0, sr=0, sg=0, sf=0, hit=0, near=0, ghit=0)
    for r in rows:
        if r["st"] != "matched":
            continue
        a, rj, _rb, gj, _gb, fj, _fb = r["j"][bk]
        st["N"] += 1
        st["sa"] += a
        st["sr"] += rj
        st["sg"] += gj
        st["sf"] += fj
        loss = rj - a
        if loss == 0:
            st["hit"] += 1
        elif 100 * loss <= n2:
            st["near"] += 1
        if gj == a:
            st["ghit"] += 1
    return st


KEYS = ["match", "actual", "rep", "glob", "fam", "hit", "near", "ghit"]


def figure_cells(st, n2):
    """{data-k: printed text} of a stats dict."""
    n = st["N"]
    d = n * n2
    return {"match": f'{n} / {st["M"]}', "actual": pct(st["sa"], d), "rep": pct(st["sr"], d), "glob": pct(st["sg"], d),
            "fam": pct(st["sf"], d), "hit": f'{st["hit"]} / {n}', "near": f'{st["near"]} / {n}', "ghit": f'{st["ghit"]} / {n}'}


def cells_html(cells):
    return "".join(f'<td class="num" data-k="{k}">{_esc(cells[k])}</td>' for k in KEYS)


# ------------------------------------------------------------------ drawing

def tile_html(order):
    return "".join(f'<span class="pt pt-{k}">{k}</span>' for k in order)


def piece_str(pieces):
    return "/".join(f"{k}:{','.join(map(str, sorted(cs)))}" for k, cs in sorted(pieces))


def parse_pieces(s):
    out = []
    for part in s.split("/"):
        k, cs = part.split(":")
        out.append((k, [int(c) for c in cs.split(",")]))
    return out


def board_svg(pieces, cs=10):
    cells = {}
    for k, ps in pieces:
        for c in ps:
            cells[(c % 10, c // 10)] = k
    return OP.svg(cells, max(4, max(y for x, y in cells) + 1), cs)


def board_fig(name, pieces, caption, cs=10):
    return (f'<figure class="bf" data-b="{_esc(name)}" data-pieces="{_esc(piece_str(pieces))}">'
            f'{board_svg(pieces, cs)}<figcaption>{caption}</figcaption></figure>')


def read_svg(svg):
    """{(letter, x, y)} of the coloured cells of an `OP.svg` board, read back from its rects."""
    w = int(re.search(r'width="(\d+)"', svg).group(1))
    h = int(re.search(r'height="(\d+)"', svg).group(1))
    cs = w // 10
    H = h // cs
    got = set()
    for x, y, fill in re.findall(r'<rect x="([\d.]+)" y="([\d.]+)" width="[\d.]+" height="[\d.]+" fill="(#[0-9a-f]{6})"/>', svg):
        if fill in BY_COL:
            got.add((BY_COL[fill], round((float(x) - .5) / cs), H - 1 - round((float(y) - .5) / cs)))
    return got


def replay_href(r):
    return f'{r["s"]}-replay.html#m{r["m"]}r{r["r"] + 1}'


# ------------------------------------------------------------------ sections

def best_of(rows, bk, n2):
    """Costliest swaps: per (user, built board, repertoire-best board), the summed loss and the round losing most."""
    g = {}
    for r in rows:
        if r["st"] != "matched":
            continue
        a, rj, rb, *_ = r["j"][bk]
        if rj > a:
            e = g.setdefault((r["u"], r["b"], rb), dict(n=0, loss=0, worst=None))
            e["n"] += 1
            e["loss"] += rj - a
            if e["worst"] is None or rj - a > e["worst"][0]:
                e["worst"] = (rj - a, r)
    return g


def render(art, tp, PR):
    n2 = art["params"]["n2"]
    rows = art["rows"]
    bk = BK_SHOWN
    pcs = {b["name"]: [(k, list(cs)) for k, cs in b["pieces"]] for b in tp["boards"]}
    held = {b["name"]: b["held"] for b in tp["boards"]}
    us = users(art)
    C = PR["cols"]
    fm = dict(budget=PR["budgets"][bk], rep_min=art["params"]["repertoire_min"])
    by_u = {u: [r for r in rows if r["u"] == u] for u in us}

    def cap(n, extra=""):
        h = held[n]
        return f'<b>{_esc(n)}</b>{extra} · hold {h}'

    def head():
        return "".join(f"<th>{_esc(C[k])}</th>" for k in ("match", "actual", "rep", "glob", "fam", "hit", "near", "ghit"))

    out = []
    # totals
    trs = []
    for u in us:
        trs.append(f'<tr data-g="tot:{_esc(u)}"><th scope="row">{_esc(u)}</th>{cells_html(figure_cells(stats(by_u[u], bk, n2), n2))}</tr>')
    out += [f'<h2>{_esc(PR["h_totals"])}</h2>', f'<p class="muted sm">{_esc(PR["totals_note"])}</p>',
            f'<div class="tw"><table class="rt"><thead><tr><th>{_esc(C["who"])}</th>{head()}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>']
    trs = []
    for u in us:
        for k in art["params"]["budgets"]:
            trs.append(f'<tr data-g="bud:{_esc(u)}:{k}"><th scope="row">{_esc(u)} · {_esc(PR["budgets"][k])}</th>'
                       f'{cells_html(figure_cells(stats(by_u[u], k, n2), n2))}</tr>')
    out += [f'<details class="sm"><summary>{_esc(PR["h_budgets"])}</summary><div class="tw"><table class="rt"><thead><tr><th>{_esc(C["who"])} · {_esc(C["budget"])}</th>{head()}</tr></thead>'
            f'<tbody>{"".join(trs)}</tbody></table></div></details>']
    # repertoire cards
    out += [f'<h2>{_esc(PR["h_rep"])}</h2>', f'<p class="muted sm">{_esc(PR["rep_note"].format(**fm))}</p>']
    for u in us:
        cards = []
        for n in art["repertoire"][u]:
            built = [r for r in by_u[u] if r["st"] == "matched" and r["b"] == n]
            right = sum(1 for r in built if r["j"][bk][0] == r["j"][bk][1])
            should = sum(1 for r in by_u[u] if r["st"] == "matched" and r["j"][bk][2] == n and r["j"][bk][1] > r["j"][bk][0])
            cards.append(f'<div class="rc" data-g="rep:{_esc(u)}:{_esc(n)}">{board_fig(n, pcs[n], cap(n), 12)}'
                         f'<div class="sm">{_esc(PR["rep_built"])} <b class="num" data-k="built">{len(built)}</b> · '
                         f'{_esc(PR["rep_right"])} <b class="num" data-k="right">{right}</b> · '
                         f'{_esc(PR["rep_should"])} <b class="num" data-k="should">{should}</b></div></div>')
        out += [f"<h3>{_esc(u)}</h3>", f'<div class="rcs">{"".join(cards)}</div>']
    # costliest swaps
    g = best_of(rows, bk, n2)
    out += [f'<h2>{_esc(PR["h_swaps"])}</h2>', f'<p class="muted sm">{_esc(PR["swaps_note"])}</p>']
    for u in us:
        lst = sorted((k for k in g if k[0] == u), key=lambda k: (-g[k]["loss"], k))[:SWAPS_SHOWN]
        trs = []
        for k in lst:
            e = g[k]
            _l, w = e["worst"]
            trs.append(f'<tr data-g="swap:{_esc(u)}:{_esc(k[1])}:{_esc(k[2])}">'
                       f'<td>{board_fig(k[1], pcs[k[1]], cap(k[1]), 9)}</td><td>{board_fig(k[2], pcs[k[2]], cap(k[2]), 9)}</td>'
                       f'<td class="num" data-k="n">{e["n"]}</td><td class="num" data-k="sum">{fl1(Fraction(e["loss"], n2))}</td>'
                       f'<td><a href="{replay_href(w)}" data-w="{w["s"]}|{w["m"]}|{w["r"]}|{_esc(u)}">{w["s"]} m{w["m"]}r{w["r"] + 1}</a>'
                       f'<div class="tiles" data-o="{w["o"]}" title="{_esc(PR["tiles_alt"])}">{tile_html(order_of(w["o"]))}</div></td></tr>')
        out += [f"<h3>{_esc(u)}</h3>",
                f'<div class="tw"><table class="rt sw"><thead><tr><th>{_esc(PR["sw_actual"])}</th><th>{_esc(PR["sw_should"])}</th><th>{_esc(PR["sw_n"])}</th>'
                f'<th>{_esc(PR["sw_sum"])}</th><th>{_esc(PR["sw_ex"])} · {_esc(PR["sw_deal"])}</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div>']
    # per night
    sess = art["sessions"]
    trs = []
    for s in sess:
        for u in us:
            sub = [r for r in by_u[u] if r["s"] == s]
            trs.append(f'<tr data-g="night:{s}:{_esc(u)}"><th scope="row"><a href="#n{s}">{s}</a> · {_esc(u)}</th>{cells_html(figure_cells(stats(sub, bk, n2), n2))}</tr>')
    out += [f'<h2>{_esc(PR["h_nights"])}</h2>', f'<p class="muted sm">{_esc(PR["nights_note"])}</p>',
            f'<div class="tw"><table class="rt"><thead><tr><th>{_esc(C["night"])} · {_esc(C["who"])}</th>{head()}</tr></thead><tbody>{"".join(trs)}</tbody></table></div>']
    R = PR["rd"]
    for s in sess:
        rr = []
        for r in rows:
            if r["s"] != s:
                continue
            if r["st"] == "matched":
                a, rj, rb, *_ = r["j"][bk]
                mid = (f'<td>{_esc(r["b"])} <span class="num">{pct(a, n2)}</span></td><td>{_esc(rb)} <span class="num">{pct(rj, n2)}</span></td>'
                       f'<td class="num">{pct(rj - a, n2)}</td>')
                dj = f' data-j="{",".join(str(x) for x in r["j"][bk])}"'
            else:
                mid, dj = '<td>–</td><td>–</td><td>–</td>', ""
            rr.append(f'<tr data-row="{r["m"]}|{r["r"]}|{_esc(r["u"])}" data-st="{r["st"]}"{dj}>'
                      f'<td><a href="{replay_href(r)}">m{r["m"]}r{r["r"] + 1}</a></td><td>{_esc(r["u"])}</td>'
                      f'<td class="sm">{_esc(PR["status"][r["st"]].split("：")[0])}</td><td class="num">{"".join(order_of(r["o"]))}</td>{mid}</tr>')
        out += [f'<details class="night" id="n{s}" data-night="{s}"><summary>{s} · {_esc(PR["night_rounds"])} ({sum(1 for r in rows if r["s"] == s)})</summary>'
                f'<div class="tw"><table class="rt"><thead><tr><th>{_esc(R["round"])}</th><th>{_esc(R["who"])}</th><th>{_esc(R["status"])}</th><th>{_esc(R["deal"])}</th>'
                f'<th>{_esc(R["actual"])}</th><th>{_esc(R["rep"])}</th><th>{_esc(R["loss"])}</th></tr></thead><tbody>{"".join(rr)}</tbody></table></div></details>']
    # unmatched
    out += [f'<h2>{_esc(PR["h_unmatched"])}</h2>', f'<p class="muted sm">{_esc(PR["unmatched_note"])}</p>']
    trs = []
    for st in STATUSES:
        cnt = {u: sum(1 for r in by_u[u] if r["st"] == st) for u in us}
        trs.append(f'<tr data-g="st:{st}"><td>{_esc(PR["status"][st])}</td>'
                   + "".join(f'<td class="num" data-k="{_esc(u)}">{cnt[u]}</td>' for u in us) + "</tr>")
    trs.append(f'<tr data-g="st:total"><td><b>{_esc(PR["status_total"])}</b></td>'
               + "".join(f'<td class="num" data-k="{_esc(u)}">{len(by_u[u])}</td>' for u in us) + "</tr>")
    out += [f'<div class="tw"><table class="rt"><thead><tr><th></th>' + "".join(f"<th>{_esc(u)}</th>" for u in us)
            + f'</tr></thead><tbody>{"".join(trs)}</tbody></table></div>']
    lay = {}
    for r in rows:
        if r["st"] == "seven_placed_no_hold":
            e = lay.setdefault(r["l"], dict(n=0, f=r["f"]))
            e["n"] += 1
    top = sorted(lay, key=lambda k: (-lay[k]["n"], k))[:SEVEN_SHOWN]
    out += [f'<h3>{_esc(PR["h_seven"])}</h3>', f'<p class="muted sm">{_esc(PR["seven_note"])}</p>', '<div class="rcs">']
    for k in top:
        e = lay[k]
        fam = PR["seven_fam"] if e["f"] is not None else PR["seven_nofam"]
        out.append(f'<div class="rc" data-g="seven:{_esc(k)}"><figure class="bf" data-b="layout" data-pieces="{_esc(k)}">{board_svg(parse_pieces(k), 12)}'
                   f'<figcaption>{_esc(fam)}</figcaption></figure><div class="sm">{_esc(PR["seven_n"])} <b class="num" data-k="n">{e["n"]}</b></div></div>')
    out.append("</div>")
    return out, fm


def order_of(o):
    return PERMS[o]


PERMS = ["".join(p) for p in __import__("itertools").permutations("IOTSZJL")]


def page_html(art, tp, PR):
    body, fm = render(art, tp, PR)
    title = PR["title"] + RS.TITLE_MARK
    css = open(OP.CSS_PATH, encoding="utf-8").read().strip("\n") + "\n" + open(CSS_PATH, encoding="utf-8").read().strip("\n")
    css += "\n" + "\n".join(f".pt-{k}{{background:{v}}}" for k, v in sorted(COL.items()))
    island = json.dumps({"schema": art["schema"], "rows": len(art["rows"]), "budget": BK_SHOWN}, separators=(",", ":"))
    out = ['<!doctype html><html lang="zh-HK"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           f"<title>{_esc(title)}</title>", f'<meta name="description" content="{_esc(PR["desc"])}">',
           "<style>", css, "</style></head><body><main>",
           f'<nav class="sm"><a href="index.html">{_esc(PR["back"])}</a> · <a href="{RANKING}">{_esc(PR["to_ranking"])}</a></nav>',
           f'<div class="eyebrow">{RS.EYEBROW}</div>', f"<h1>{_esc(title)}</h1>",
           f'<p class="quar">{PR["quarantine"]}</p>', f'<p class="ref">{PR["subset"]}</p>', f'<p class="ref">{PR["assume"]}</p>']
    out += [f"<p>{t.format(**fm)}</p>" for t in PR["intro"]]
    out += body
    out += [f'<p class="muted sm">{_esc(PR["closing"])}</p>', "</main>",
            f'<script id="{DATA_ID}" type="application/json">{island}</script></body></html>']
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ audit (a second route: explicit loops)

TR = re.compile(r'<tr data-g="([^"]+)">(.*?)</tr>', re.S)
RC = re.compile(r'<div class="rc" data-g="([^"]+)">(.*?</b>)</div>', re.S)
TD = re.compile(r'data-k="(\w+)">(.*?)</(?:td|b)>', re.S)
ROWRE = re.compile(r'<tr data-row="(\d+)\|(\d+)\|(\w+)" data-st="(\w+)"( data-j="([\w,]+)")?')
FIG = re.compile(r'<figure class="bf" data-b="([^"]*)" data-pieces="([^"]*)">(<svg.*?</svg>)', re.S)
LINK = re.compile(r'href="(\d{4}-\d\d-\d\d)-replay\.html#m(\d+)r(\d+)"')


def ex_figs(rows, bk, n2):
    """The printed cells of a row set, by explicit loops written apart from `stats`/`figure_cells`."""
    matched = [r for r in rows if r["st"] == "matched"]
    n = len(matched)
    act = sum(r["j"][bk][0] for r in matched)
    rep = sum(r["j"][bk][1] for r in matched)
    glo = sum(r["j"][bk][3] for r in matched)
    fam = sum(r["j"][bk][5] for r in matched)
    hit = len([1 for r in matched if r["j"][bk][1] == r["j"][bk][0]])
    near = len([1 for r in matched if 0 < r["j"][bk][1] - r["j"][bk][0] and 100 * (r["j"][bk][1] - r["j"][bk][0]) <= 5040 * 5040])
    gh = len([1 for r in matched if r["j"][bk][3] == r["j"][bk][0]])
    den = n * 5040 * 5040
    return {"match": f"{n} / {len(rows)}", "actual": pct(act, den), "rep": pct(rep, den), "glob": pct(glo, den), "fam": pct(fam, den),
            "hit": f"{hit} / {n}", "near": f"{near} / {n}", "ghit": f"{gh} / {n}"}


def audit_rows(art, tp, bad):
    """Per-row invariants of the artefact itself."""
    names = {b["name"] for b in tp["boards"]}
    reps = {u: set(v) for u, v in art["repertoire"].items()}
    sess = set(art["sessions"])
    seen = set()
    for r in art["rows"]:
        key = (r["s"], r["m"], r["r"], r["u"])
        tag = f'{r["s"]} m{r["m"]}r{r["r"] + 1} {r["u"]}'
        if key in seen:
            bad.append(f"{tag} appears twice")
        seen.add(key)
        if r["s"] not in sess:
            bad.append(f"{tag}: a night the artefact does not list")
        if r["st"] not in STATUSES:
            bad.append(f"{tag}: unknown status {r['st']!r}")
            continue
        if r["st"] != "matched":
            if r["j"] is not None or r["b"] is not None:
                bad.append(f"{tag}: an unmatched round ({r['st']}) carries a board or a chance")
            continue
        if r["b"] not in names or r["b"] is None:
            bad.append(f"{tag}: built board {r['b']!r} is not a board of the ranking")
            continue
        prev = None
        for k in art["params"]["budgets"]:
            a, rj, rb, gj, gb, fj, fb = r["j"][k]
            if not (a <= rj <= gj and a <= fj <= gj):
                bad.append(f"{tag} budget {k}: the chances are not ordered actual <= repertoire/family <= ceiling")
            if rb not in reps[r["u"]] and rb != r["b"]:
                bad.append(f"{tag} budget {k}: repertoire best {rb} is not in {r['u']}'s repertoire")
            if gb not in names or fb not in names:
                bad.append(f"{tag} budget {k}: a best board is not a board of the ranking")
            if a > 5040 * 5040:
                bad.append(f"{tag} budget {k}: a chance above 1")
            if prev is not None and a < prev:
                bad.append(f"{tag}: the chance falls as the soft-drop budget grows")
            prev = a
    if sum(1 for r in art["rows"] if r["st"] in STATUSES) != len(art["rows"]):
        bad.append("the statuses do not cover every row")


def audit(page, art, tp, PR, repo=REPO):
    bad = RP.audit_quarantine(page, [RS.EYEBROW, RS.NO_CLAIM, PR["quarantine"], PR["subset"], PR["assume"]], DATA_ID)
    if set(page) & SIMPLIFIED:
        bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
    # the inputs are current
    try:
        cur, _ = load_inputs(repo)
        if cur["md5"] != art["md5"]:
            bad.append("the artefact's md5s are not the current inputs'")
    except ValueError as e:
        bad.append(str(e))
    for k, p in (("tp", TP_PATH), ("b1", B1_PATH), ("emitter", EMIT_PATH)):
        with open(os.path.join(repo, os.path.relpath(p, REPO)), "rb") as f:
            if art["md5"][k] != md5(f.read()):
                bad.append(f"the artefact's {k} md5 is stale")
    audit_rows(art, tp, bad)
    if bad:
        return bad
    n2 = art["params"]["n2"]
    rows, us, bk = art["rows"], users(art), BK_SHOWN
    if n2 != 5040 * 5040:
        bad.append("n2 is not 5040^2")
    # the status partition and the per-user totals
    if len(rows) != sum(1 for r in rows if r["st"] in STATUSES):
        bad.append("the statuses do not partition the rows")
    # every printed figure row
    groups = {g: dict(TD.findall(b)) for g, b in TR.findall(page)}
    groups.update({g: dict(TD.findall(b)) for g, b in RC.findall(page)})

    def want(g, got, exp):
        if got != exp:
            bad.append(f"{g}: printed {got} but the artefact gives {exp}")
    for u in us:
        mine = [r for r in rows if r["u"] == u]
        want(f"tot:{u}", groups.get(f"tot:{u}"), ex_figs(mine, bk, n2))
        for k in art["params"]["budgets"]:
            want(f"bud:{u}:{k}", groups.get(f"bud:{u}:{k}"), ex_figs(mine, k, n2))
        for s in art["sessions"]:
            want(f"night:{s}:{u}", groups.get(f"night:{s}:{u}"), ex_figs([r for r in mine if r["s"] == s], bk, n2))
        for n in art["repertoire"][u]:
            built = [r for r in mine if r["st"] == "matched" and r["b"] == n]
            right = len([1 for r in built if r["j"][bk][0] == r["j"][bk][1]])
            should = len([1 for r in mine if r["st"] == "matched" and r["j"][bk][2] == n and r["j"][bk][1] > r["j"][bk][0]])
            want(f"rep:{u}:{n}", groups.get(f"rep:{u}:{n}"), {"built": str(len(built)), "right": str(right), "should": str(should)})
    for st in STATUSES:
        want(f"st:{st}", groups.get(f"st:{st}"), {u: str(len([1 for r in rows if r["u"] == u and r["st"] == st])) for u in us})
    want("st:total", groups.get("st:total"), {u: str(len([1 for r in rows if r["u"] == u])) for u in us})
    tot = sum(int(v) for st in STATUSES for v in groups.get(f"st:{st}", {}).values())
    if tot != len(rows):
        bad.append(f"the unmatched table sums to {tot}, not {len(rows)} rounds")
    # swaps: every printed group is a recomputed one, in loss order, top SWAPS_SHOWN per user
    gs = best_of(rows, bk, n2)
    for u in us:
        exp = sorted((k for k in gs if k[0] == u), key=lambda k: (-gs[k]["loss"], k))[:SWAPS_SHOWN]
        got = [g for g in groups if g.startswith(f"swap:{u}:")]
        if got != [f"swap:{u}:{k[1]}:{k[2]}" for k in exp]:
            bad.append(f"the costliest swaps of {u} are not the recomputed top {SWAPS_SHOWN}")
        for k in exp:
            e = gs[k]
            want(f"swap:{u}:{k[1]}:{k[2]}", groups.get(f"swap:{u}:{k[1]}:{k[2]}"),
                 {"n": str(e["n"]), "sum": fl1(Fraction(e["loss"], 5040 * 5040))})
    # the nights: each folds open to exactly its rounds, and every chance printed is the artefact's
    for s in art["sessions"]:
        m = re.search(rf'<details class="night" id="n{s}" data-night="{s}">(.*?)</details>', page, re.S)
        if not m:
            bad.append(f"the night {s} is missing from the page")
            continue
        got = [(int(a), int(b), c, d, j) for a, b, c, d, _x, j in ROWRE.findall(m.group(1))]
        exp = [(r["m"], r["r"], r["u"], r["st"], ",".join(str(x) for x in r["j"][bk]) if r["j"] else "")
               for r in rows if r["s"] == s]
        if got != exp:
            bad.append(f"the rounds of {s} are not the artefact's ({len(got)} against {len(exp)})")
    # drawn boards equal the ranking's pieces, read back out of the svg
    pieces = {b["name"]: [(k, list(cs)) for k, cs in b["pieces"]] for b in tp["boards"]}
    figs = FIG.findall(page)
    if not figs:
        bad.append("the page draws no board")
    for name, ps, svg in figs:
        parsed = parse_pieces(ps)
        if name != "layout" and piece_str(pieces.get(name, [])) != ps:
            bad.append(f"the board {name} is drawn from pieces the ranking does not hold")
        if read_svg(svg) != {(k, c % 10, c // 10) for k, cs in parsed for c in cs}:
            bad.append(f"the drawing of {name} is not its pieces")
    # the replay links name real rounds
    have = {(r["s"], r["m"], r["r"] + 1) for r in rows}
    for s, m, r in LINK.findall(page):
        if (s, int(m), int(r)) not in have:
            bad.append(f"a replay link {s}#m{m}r{r} names no round")
            break
    # the layouts' counts
    lay = {}
    for r in rows:
        if r["st"] == "seven_placed_no_hold":
            lay[r["l"]] = lay.get(r["l"], 0) + 1
    topl = sorted(lay, key=lambda k: (-lay[k], k))[:SEVEN_SHOWN]
    for k in topl:
        want(f"seven:{k}", groups.get(f"seven:{k}"), {"n": str(lay[k])})
    return bad


def render_all(repo=REPO, inputs=None, prose=None):
    art, tp = inputs or load_inputs(repo)
    PR = prose or load_prose()
    page = page_html(art, tp, PR)
    bad = audit(page, art, tp, PR, repo)
    _need(not bad, "; ".join(bad[:5]))
    return {OVERVIEW: page}


def site_card(inputs=None, prose=None):
    art, _tp = inputs or load_inputs()
    PR = prose or load_prose()
    return {"href": OVERVIEW, "cases": sum(1 for r in art["rows"] if r["st"] == "matched"), "unit": "局", "kicker": PR["index_card"]["kicker"],
            "title": PR["title"], "blurb": PR["index_card"]["blurb"]}


# ------------------------------------------------------------------ selftest

def selftest(repo=REPO):
    art, tp = load_inputs(repo)
    PR = load_prose()
    page = page_html(art, tp, PR)
    base = audit(page, art, tp, PR, repo)
    if base:
        print("FAIL the unmutated page does not pass its own audit:", base[:3], file=sys.stderr)
        return 1
    n2 = art["params"]["n2"]
    us = users(art)
    fails = 0

    def expect(name, pg, a=art):
        nonlocal fails
        if audit(pg, a, tp, PR, repo):
            print(f"  killed  {name}")
        else:
            print(f"  SURVIVED {name}")
            fails += 1
    # one J bumped (artefact side: the page prints the exact integers per round)
    a1 = copy.deepcopy(art)
    next(r for r in a1["rows"] if r["st"] == "matched")["j"][BK_SHOWN][0] += 1
    expect("one chance numerator bumped", page, a1)
    # a hit flipped (page side)
    m = re.search(rf'(<tr data-g="tot:{us[0]}">.*?data-k="hit">)(\d+)( / )', page, re.S)
    expect("a printed hit count changed", page[:m.start(2)] + str(int(m.group(2)) + 1) + page[m.end(2):])
    # a quarantine sentence deleted
    expect("the quarantine sentence deleted", page.replace(PR["quarantine"], "", 1))
    expect("the selected-subset sentence deleted", page.replace(PR["subset"], "", 1))
    expect("the J-assumption sentence deleted", page.replace(PR["assume"], "", 1))
    # an unmatched row given a J
    a2 = copy.deepcopy(art)
    r = next(x for x in a2["rows"] if x["st"] == "not_kept")
    r["j"] = copy.deepcopy(next(x for x in a2["rows"] if x["st"] == "matched")["j"])
    expect("an unmatched row given a chance", page, a2)
    # a night dropped
    s0 = art["sessions"][0]
    expect("a night dropped", re.sub(rf'<details class="night" id="n{s0}".*?</details>', "", page, count=1, flags=re.S))
    # the mean over all rounds instead of matched rounds
    mine = [r for r in art["rows"] if r["u"] == us[0]]
    st = stats(mine, BK_SHOWN, n2)
    right = pct(st["sa"], st["N"] * n2)
    wrong = pct(st["sa"], st["M"] * n2)
    _need(right != wrong, "the all-rounds mean equals the matched mean; the mutant would not change the page")
    expect("the mean taken over all rounds", page.replace(f'data-k="actual">{right}<', f'data-k="actual">{wrong}<', 1))
    # a stale md5
    a3 = copy.deepcopy(art)
    a3["md5"]["tp"] = "0" * 32
    expect("a stale ranking md5", page, a3)
    a4 = copy.deepcopy(art)
    a4["md5"]["replay_facts"][art["sessions"][0]] = "0" * 32
    expect("a stale replay md5", page, a4)
    # a drawn board moved
    expect("a drawn board changed", re.sub(r'(<figure class="bf" data-b="[^"]+" data-pieces=")([A-Z]):', r'\1X:', page, count=1))
    print("selftest:", "FAIL" if fails else "ok")
    return 1 if fails else 0


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

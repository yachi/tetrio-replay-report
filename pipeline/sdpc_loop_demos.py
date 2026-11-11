"""SDPC 循環 — every constructed loop, played: `docs/sdpc-loop-demos.html`.

Rendered by `pipeline.sdpc_loop_page` beside the video page, from `analysis/sdpc-loop-demos.json`
(`pipeline/sim/emit-sdpc-loop-demos.ts`, checked by `pipeline/openers/sdpc-loop-demos.test.ts`).

CONSTRUCTED, quarantined harder than the video page: nobody played these games. No claim id, no ✓, no
`data-claim`, and no figure from them enters any count. The audit reuses `replay_page.audit_quarantine`
and `audit_player`, and adds:

* every loop of the artefact is embedded exactly once and linked exactly once from the table;
* every EMBEDDED loop is decoded again from an empty board with `replay_section.decode_boards` (a second
  decoder, not the engine): five whole 7-bags, nothing held, the board empty after lock 20 and lock 35 and
  at no other lock, and T-spins exactly at the locks the artefact names;
* every printed figure (`data-figure`) is recounted from the artefact;
* no `%` outside quoted source text, no simplified glyph.
"""
import html
import json
import os
import re

from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline import route_page as RT
from pipeline.claims.build_claims import SIMPLIFIED

_esc, board_svg, DATA_ID = RT._esc, RT.board_svg, RT.DATA_ID
PAGE = "sdpc-loop-demos.html"
ARTEFACT = "analysis/sdpc-loop-demos.json"
STICKSPIN_DEMOS_PAGE = "stickspin-demos.html"

_FIGURE = re.compile(r'data-figure="([^"]+)">([^<]*)<')
_LINK = re.compile(r'<a class="scp-case" href="#(demo-[a-z0-9-]+)" data-round="(demo-[a-z0-9-]+)"')
_HALF = re.compile(r'data-half="([^"]+)"')


def _need(cond, msg):
    if not cond:
        raise ValueError(f"sdpc loop demos page: {msg}")


def slug(loop_id):
    """`2.sd.pc#1+p06.001.mirror` -> `demo-sd-pc1-p06-001-mirror`."""
    s = loop_id[2:] if loop_id.startswith("2.") else loop_id
    return "demo-" + re.sub(r"[^a-z0-9]+", "-", s.replace("#", "").lower()).strip("-")


def load(repo):
    with open(os.path.join(repo, ARTEFACT), encoding="utf-8") as f:
        a = json.load(f)
    _need(a.get("report_eligible") is False and a.get("constructed") is True,
          "the artefact is not marked report_eligible: false, constructed: true")
    return a


def _data(a):
    return {"board": {"width": a["board"]["width"], "rows": a["board"]["rows"]}, "shapes": a["shapes"]}


def decode_problems(a, loop_id, seq, locks):
    """The embedded loop, decoded from an empty board by the Python decoder. Returns the problems."""
    bad = []
    try:  # the decoder throws on a lock whose `lines` disagree with the board, or a piece off the queue
        boards = [(piece, len(full), all(v is None for row in board for v in row))
                  for piece, full, board in RS.decode_boards(_data(a), seq, locks, RS.NEXT_SHOWN)]
    except (Exception, SystemExit) as e:  # replay_section's _need raises SystemExit
        return [f"{loop_id}: {e}"]
    if len(locks) != 35:
        bad.append(f"{loop_id}: {len(locks)} locks")
    for b in range(5):
        if "".join(sorted(seq[7 * b:7 * b + 7])) != "IJLOSTZ":
            bad.append(f"{loop_id}: bag {b + 1} is not a 7-bag")
    if any(lk[5] for lk in locks):
        bad.append(f"{loop_id}: a lock holds")
    spins = []
    for i, ((piece, full, empty), lk) in enumerate(zip(boards, locks)):
        if empty != (i in (19, 34)):
            bad.append(f"{loop_id}: lock {i + 1}: board {'' if empty else 'not '}empty")
        if lk[3] > 0 and full:
            spins.append(f"{i}:{piece}{lk[3]}/{full}")
    if " ".join(spins) != "6:T2/1 13:T2/2 27:T2/2":
        bad.append(f"{loop_id}: spins {' '.join(spins)}")
    return bad


def recount(a):
    loops = a["loops"]
    out = {"loops": str(len(loops)), "sd": str(len({L["sd"] for L in loops})),
           "dpc": str(len(a["dpc_halves"])), "dups": str(len(a["dpc_unbuilt"]))}
    for k in sorted({L["leftover"] for L in loops}):
        out[f"loops.{k}"] = str(sum(1 for L in loops if L["leftover"] == k))
    for h in a["dpc_halves"]:
        out[f"used.{h['dpc']}"] = str(sum(1 for L in loops if L["dpc"] == h["dpc"]))
    return out


def _board_before(a, L, upto, mark):
    """Rows top->bottom of the decoded board after `upto` locks, with lock `mark`'s cells drawn as the dashed U."""
    for i, (_p, _f, board) in enumerate(RS.decode_boards(_data(a), L["seq"], L["locks"], RS.NEXT_SHOWN)):
        if i == upto - 1:
            g = [list(r) for r in board]
            break
    piece = RS.queue_states(L["seq"], L["locks"], RS.NEXT_SHOWN)[mark][0]
    w, rows = a["board"]["width"], a["board"]["rows"]
    cells = list(RS._place_cells(a["shapes"], w, rows, piece, L["locks"][mark][1]))
    for c in cells:
        y, x = divmod(c, w)
        _need(g[y][x] is None, f"{L['id']}: lock {mark}'s cells are filled before it")
        g[y][x] = "U"
    top = max(y for y in range(rows) if any(g[y]))
    return ["".join("-" if v is None else "U" if v == "U" else v.lower() if v in "IJLOSTZ" else "c" for v in g[y])
            for y in range(top, -1, -1)]


def _payload(a, L, DP, sd_name, dpc_name):
    moments = []
    for e in L["events"]:
        q = e["lock"] + 1
        if e["kind"] == "PC":
            moments.append([q, 0, "pc", DP["pc"].format(n=q, lines=e["half_lines"])])
        else:
            moments.append([q, 0, "tspin", DP["spin"].format(n=q, name=RS.SPIN_NAMES[(e["spin"], e["lines"])])])
    h = L["dpc_half"]
    notes = [DP["note_sd"].format(sd=sd_name, left=L["leftover"]),
             DP["note_dpc"].format(left=L["leftover"], q4=h["queue4"], q5=h["queue5"])]
    return {"label": slug(L["id"]), "title": DP["now"].format(sd=sd_name, dpc=dpc_name),
            "seq": L["seq"], "order": "0" * len(L["locks"]), "winner": None,
            "players": [{"user": DP["user"], "slot": 0, "ending": None, "frames": L["frames"],
                         "pieces": len(L["locks"]), "locks": L["locks"], "ge": [],
                         "verified_to": None, "after": None, "failed_at": None}],
            "moments": moments, "flags": [], "notes": notes}


class DemoPage:
    def __init__(self, prose):
        self.PROSE = prose
        self.DP = prose["demos"]
        self.REQUIRED = (RS.EYEBROW, RS.TITLE_MARK, RS.NO_CLAIM, *self.DP["sentences"])

    def sd_name(self, L):
        kind = "もっちパフェ" if ".mochi." in L["sd"] else "SDパフェ"
        return f'{kind} 第 {L["sd"].split("#")[1]} 款'

    @staticmethod
    def dpc_name(h):
        # the heading's leftover is the source's hand, so a mirrored half names the setup and its own leftover
        return f'{h["setup"]} {h["heading"][0]}（剩 {h["leftover"]}）· {h["pc"]}' + (" ↔" if h["mirrored"] else "")

    def render(self, a, sd_demos, overview):
        DP, S, W = self.DP, self.DP["sections"], self.DP["words"]
        halves = {h["dpc"]: h for h in a["dpc_halves"]}
        fig = recount(a)
        title = f'{DP["title"]}{RS.TITLE_MARK}'
        css = [RP._tokens_css(), RP.BASE_CSS.strip("\n"), RT.PAGE_CSS.strip("\n"),
               RS._color_css([{"user": DP["user"]}]), RS.CSS.strip("\n"),
               ".sld-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr)); gap: .6rem; }",
               ".sld-tab td, .sld-tab th { text-align: center; padding: .15rem .3rem; white-space: nowrap; }",
               ".sld-tab th.sld-sd { text-align: left; }"]
        with open(RT.PAGE_JS, encoding="utf-8") as fh:
            page_js = fh.read().rstrip()
        out = ["<!doctype html>", '<html lang="zh-HK">', "<head>", '<meta charset="utf-8">',
               '<meta name="viewport" content="width=device-width, initial-scale=1">',
               f"<title>{_esc(title)}</title>", f'<meta name="description" content="{_esc(DP["desc"])}">',
               "<style>", "  " + "\n".join(css), "</style>", "</head>", "<body>", '<div class="wrap-wide">',
               '  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a>'
               f'<a href="{overview}">{_esc(W["back"])}</a></nav>',
               '  <header class="scp-head">', f'    <div class="eyebrow">{RS.EYEBROW}</div>',
               f'    <h1 class="section-title">{_esc(title)}</h1>', f'    <p>{_esc(DP["lede"])}</p>',
               "  </header>", '  <div class="method-note">',
               f'    <p><strong>呢版唔屬於信任鏈，亦唔係對局。</strong>所以呢版<strong>{RS.NO_CLAIM}</strong>。</p>']
        out += [f"    <p>{s}</p>" for s in DP["sentences"]]
        out += ["  </div>",
                f'  <p>{_esc(W["counts"])} <span data-figure="loops">{fig["loops"]}</span> {_esc(W["loops"])}：'
                f'<span data-figure="sd">{fig["sd"]}</span> {_esc(W["sd"])}，'
                f'<span data-figure="dpc">{fig["dpc"]}</span> {_esc(W["dpc"])}。</p>',
                f'  <section id="{RS.SECTION_ID}" aria-labelledby="rpg-now">',
                '    <h2 class="rpg-now" id="rpg-now" aria-live="polite"></h2>',
                f'    <p class="scp-idle">{_esc(DP["idle"])}</p>',
                '    <p class="rpg-notes"></p>',
                f'    <p class="rpg-flag" hidden>{RS.FLAG_WORDS}</p>',
                f'    <p class="rpg-missing" hidden>{_esc(self.PROSE.get("missing", "搵唔到呢個示範。"))}</p>',
                '    <noscript><p>重播要開 JavaScript 先用到。</p></noscript>',
                '    <div class="rpg-host"></div>',
                f'    <template id="{RT.TEMPLATE_ID}">',
                *["  " + line for line in RS.player_box("", [DP["user"]], bands=False)],
                '    </template>', '  </section>']

        # 1. the combination table, one per leftover
        rounds = {}
        by = {(L["sd"], L["dpc"]): L for L in a["loops"]}
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["table"])}</h2>', f'    <p>{_esc(S["table_note"])}</p>']
        for left in sorted({L["leftover"] for L in a["loops"]}):
            sds = sorted({L["sd"] for L in a["loops"] if L["leftover"] == left},
                         key=lambda s: (".mochi." in s, int(s.split("#")[1])))
            hs = [h for h in a["dpc_halves"] if h["leftover"] == left]
            out += [f'    <h3>{_esc(W["left"])} {left}（<span data-figure="loops.{left}">{fig[f"loops.{left}"]}</span> {_esc(W["loops"])}）</h3>',
                    '    <div class="scp-index-wrap"><table class="scp-table sld-tab">',
                    "    <tr><th></th>" + "".join(
                        f'<th title="{_esc(self.dpc_name(h))}">{_esc(h["pc"])}{_esc(W["mirror"]) if h["mirrored"] else ""}</th>'
                        for h in hs) + "</tr>"]
            for sd in sds:
                any_l = next(L for L in a["loops"] if L["sd"] == sd)
                cells = []
                for h in hs:
                    L = by.get((sd, h["dpc"]))
                    if L is None:
                        cells.append("<td>—</td>")
                        continue
                    s = slug(L["id"])
                    rounds[s] = _payload(a, dict(L, dpc_half=h), DP, self.sd_name(L), self.dpc_name(h))
                    cells.append(f'<td><a class="scp-case" href="#{s}" data-round="{s}" '
                                 f'title="{_esc(self.sd_name(L))} + {_esc(self.dpc_name(h))}">{_esc(W["play"])}</a></td>')
                sd_slug = RT.demo_slug(sd)
                out.append(f'    <tr><th class="sld-sd"><a href="{STICKSPIN_DEMOS_PAGE}#{sd_slug}">{_esc(self.sd_name(any_l))}</a></th>'
                           + "".join(cells) + "</tr>")
            out.append("    </table></div>")
        out.append("  </section>")

        # 2. every DPC half, its board just before the T
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["halves"])}</h2>', f'    <p>{_esc(S["halves_note"])}</p>',
                '    <div class="sld-grid">']
        for h in a["dpc_halves"]:
            L = next(L for L in a["loops"] if L["dpc"] == h["dpc"])
            nm = self.dpc_name(h)
            cond = (W["cond_met"].format(cond=h["condition"]) if h.get("condition") and h["condition_met"]
                    else W["cond_none"])
            _need(not h.get("condition") or h["condition_met"], f"{h['dpc']}: its order condition is not met")
            out.append(f'    <div class="scp-node" data-half="{_esc(h["dpc"])}"><h4 class="scp-name">{_esc(nm)}</h4>'
                       f'{board_svg(_board_before(a, L, 27, 27), nm, RT.PIECE_CLASS)}'
                       f'<p class="scp-tag">{_esc(cond)}</p><p class="scp-count">'
                       + _esc(W["used"]).format(n=f'<span data-figure="used.{_esc(h["dpc"])}">{fig["used." + h["dpc"]]}</span>')
                       + "</p></div>")
        out += ["    </div>", "  </section>"]

        # 3. SD Perfect Clears no DPC of the catalogue follows
        used = {L["sd"] for L in a["loops"]}
        lost = [d for d in sd_demos if re.match(r"^2\.(sd|mochi)\.pc#\d+$", d["node"]) and d["node"] not in used]
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["none"])}</h2>', f'    <p>{_esc(S["none_note"])}</p>', "    <ul>"]
        for d in sorted(lost, key=lambda d: (d["bags"][2]["unused"], ".mochi." in d["node"], int(d["node"].split("#")[1]))):
            fake = {"sd": d["node"]}
            out.append(f'    <li><a href="{STICKSPIN_DEMOS_PAGE}#{RT.demo_slug(d["node"])}">{_esc(self.sd_name(fake))}</a>：'
                       f'{_esc(W["left"])} {_esc(d["bags"][2]["unused"])}</li>')
        out += ["    </ul>", "  </section>"]

        # 4. duplicates
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["dups"])}（<span data-figure="dups">{fig["dups"]}</span>）</h2>',
                f'    <p>{_esc(S["dups_note"])}</p>', "    <ul>"]
        for u in a["dpc_unbuilt"]:
            out.append(f'    <li>{_esc(u["dpc"])}：{_esc(W["same_as"].format(other=u["same_as"]))}</li>')
        out += ["    </ul>", "  </section>"]
        island = {"shared": {"shapes": a["shapes"], "width": a["board"]["width"], "rows": a["board"]["rows"],
                             "visible": a["board"]["visible_rows"], "next": RS.NEXT_SHOWN, "flag_words": RS.FLAG_WORDS},
                  "rounds": rounds, "cases": [{"case": k, "round": k} for k in rounds], "figures": fig}
        out += RT._tail(island, (RS.player_js(), page_js))
        return "\n".join(out)

    def audit(self, page, a):
        bad = RP.audit_quarantine(page, self.REQUIRED, DATA_ID) + RP.audit_player(page)
        if set(page) & SIMPLIFIED:
            bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
        vis = RT._visible(page)
        if "%" in re.sub(r"<[^>]+>", "", vis):
            bad.append("a % on the page — it prints counts, never computed rates")
        want = sorted(slug(L["id"]) for L in a["loops"])
        links = _LINK.findall(page)
        if any(h != r for h, r in links) or sorted(h for h, _ in links) != want:
            bad.append("the table does not link every loop exactly once")
        if sorted(_HALF.findall(page)) != sorted(h["dpc"] for h in a["dpc_halves"]):
            bad.append("the page does not draw every DPC half exactly once")
        figs = {}
        for k, v in _FIGURE.findall(page):
            if k in figs:
                bad.append(f"figure {k} printed twice")
            figs[k] = html.unescape(v)
        rc = recount(a)
        if figs != rc:
            bad.append(f"the printed figures are not recounted: {sorted(k for k in set(figs) | set(rc) if figs.get(k) != rc.get(k))[:4]}")
        m = RT._ISLAND.search(page)
        if not m:
            return bad + ["no data island"]
        island = json.loads(m.group(1))
        if sorted(island["rounds"]) != want:
            bad.append("the page does not embed every loop exactly once")
        by = {slug(L["id"]): L for L in a["loops"]}
        for s, r in island["rounds"].items():
            if s in by:
                bad += decode_problems(a, by[s]["id"], r["seq"], r["players"][0]["locks"])
        return bad

    def selftest(self, a, sd_demos, overview):
        page = self.render(a, sd_demos, overview)
        survived = killed = 0

        def expect(label, bad, want):
            nonlocal survived, killed
            if bool(bad) == want:
                killed += want
                print(f'  {"killed" if want else "passed"}: {label}')
            else:
                survived += 1
                print(f'  {"SURVIVED" if want else "FAILED control"}: {label} {bad[:2]}')

        expect("demo page (control)", self.audit(page, a), False)
        expect("demo page: a quarantine sentence deleted", self.audit(page.replace(self.DP["sentences"][0], ""), a), True)
        expect("demo page: a badge planted", self.audit(page.replace("</h1>", '<span data-claim="C001">✓</span></h1>', 1), a), True)
        lk = _LINK.search(page)
        expect("demo page: a table link dropped", self.audit(page.replace(lk.group(0), "<a", 1), a), True)
        m = re.search(r'data-figure="loops">(\d+)<', page)
        expect("demo page: a figure edited", self.audit(page[:m.start(1)] + str(int(m.group(1)) + 1) + page[m.end(1):], a), True)
        hb = _HALF.search(page)
        expect("demo page: a DPC half drawn twice", self.audit(page.replace(hb.group(0), hb.group(0) + " " + hb.group(0), 1), a), True)
        mi = RT._ISLAND.search(page)
        island = json.loads(mi.group(1))
        k = sorted(island["rounds"])[0]

        def with_island(f):
            isl = json.loads(json.dumps(island))
            f(isl)
            return page[:mi.start(1)] + RT._island(isl) + page[mi.end(1):]

        def move(isl):
            lks = isl["rounds"][k]["players"][0]["locks"]
            lks[25][1] += 1
        expect("demo page: an embedded lock moved", self.audit(with_island(move), a), True)

        def hold(isl):
            isl["rounds"][k]["players"][0]["locks"][21][5] = 1
        expect("demo page: an embedded piece held", self.audit(with_island(hold), a), True)

        def drop(isl):
            isl["rounds"][k]["players"][0]["locks"].pop()
        expect("demo page: an embedded lock dropped", self.audit(with_island(drop), a), True)
        expect("demo page: a computed rate printed", self.audit(page.replace("</h1>", "<p>27%</p></h1>", 1), a), True)
        return killed, survived

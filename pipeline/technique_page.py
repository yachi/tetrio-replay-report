"""中盤手法頁 — the shared MID-GAME TECHNIQUE PAGES renderer: for one shiwehi.com technique page (STSD,
…) one overview and one constructed-demo page, each audited before it is returned.

    python3 -m pipeline.stsd_page --out-dir /tmp/stsd   # STSD's pages, through its profile module
    python3 -m pipeline.stsd_page --selftest            # its audit's mutants

ONE RENDERER, ONE AUDIT. A `TechniqueSite` is this module bound to one technique's
`TechniqueSiteProfile` (file names, schemas, the variant, the board letters) and its prose file. It is
a SIBLING of `route_page.py`, not a profile of it: a technique page has no bags, no route tree and no
per-node case pages, so it imports the route renderer's low-level pieces (`board_svg`, the page CSS,
the island and tail, the source line, `demo_slug`, `PAGE_JS`) and edits none of them — no route page
moves because a technique exists.

Inputs, all committed: the technique's transcription (`pipeline/openers/<x>-technique.json`, gated by
`technique_transcription.py`), its corpus artefact (`technique-facts.ts`) and its demo artefact
(`technique-demos.ts`). Pure Python, so `bin/build-docs` renders it in the `docs` job, which has no
bun. The overview embeds no replay: each case links to its night's `<date>-replay.html#m<pos>r<round>`,
an anchor that page already reads.

QUARANTINE. Simulator output, the replay pages' tier: no claim ids, no ✓, no `data-claim`, and both
artefacts must say `report_eligible: false` (the demos `constructed: true` as well). The audit reuses
`replay_page.audit_quarantine` / `audit_player` — one copy of each rule — and adds its own:

* every transcribed board appears exactly once on the overview, and exactly once on the demo page
  (reached by a demo, or unbuilt with its reason);
* every hit is indexed exactly once;
* every figure (`data-figure`) is the artefact's, and the hit-derived ones are RE-COUNTED from the
  hit list rather than read from the aggregates the renderer printed, so the two halves of the
  artefact must agree for the page to render;
* the control sentence is present whenever the headline table is (a shape test printed without its
  controls reads as a finding);
* the only `%` are inside quoted source text, and no simplified glyph anywhere;
* each embedded demo is decoded again with `replay_section.decode_boards` (a second implementation
  of the bun test's `reachProblems`) and must stand on every board it claims.

FIGURES. Counts only, rendered from the artefacts, always 「N / M」 with the denominator. No rate is
computed, so no rounding rule is exercised.
"""
import argparse
import html
import json
import os
import re
from dataclasses import dataclass, field

from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline import route_page as RT
from pipeline.claims.build_claims import SIMPLIFIED

HERE, REPO = RT.HERE, RT.REPO
_esc, _src, board_svg, demo_slug = RT._esc, RT._src, RT.board_svg, RT.demo_slug
DATA_ID, TEMPLATE_ID = RT.DATA_ID, RT.TEMPLATE_ID

_FIGURE = re.compile(r'data-figure="([^"]+)">([^<]*)<')
_BOARD = re.compile(r'data-board="([^"]+)"')
_CASE = re.compile(r'data-case="([^"]+)"')
_DEMO_BLOCK = re.compile(r'data-demo-node="([^"]+)" data-demo="(built|unbuilt)"')
_REACH = re.compile(r'data-reach="([^"]+)"')
_SRC_QUOTE = re.compile(r'<q class="scp-src">.*?</q>', re.S)
_TAG = re.compile(r"<[^>]+>")


@dataclass
class TechniqueSiteProfile:
    """One technique's half of the pages. Every reader-visible string is in the prose file."""
    module: str
    #: docs file prefix: `<prefix>.html` and `<prefix>-demos.html`
    prefix: str
    transcription_rel: str
    facts_rel: str
    demos_rel: str
    prose_path: str
    transcription_schema: str
    facts_schema: str
    demos_schema: str
    #: the variant every figure is about, and the denominators key of its opportunity
    variant: str
    opportunity: str
    #: board letters beyond route_page.PIECE_CLASS, and the CSS for them
    cell_classes: dict = field(default_factory=dict)
    extra_css: str = ""
    max_page_bytes: int = 0


def case_key(h):
    return f"{h['session']} m{h['match']}r{h['round']} {h['player']} lock {h['lock']}"


def _nn(n, m):
    return f"{n} / {m}"


class TechniqueSite:
    """The pages of one technique: this module's renderer and audit bound to one profile."""

    def __init__(self, p: TechniqueSiteProfile):
        self.p = p
        self.OVERVIEW = f"{p.prefix}.html"
        self.DEMO_PAGE = f"{p.prefix}-demos.html"
        self.PROSE = self.load_prose(p.prose_path)
        PS = self.PS = self.PROSE["page_sentences"]
        self.PAGE_SENTENCES = (PS["source"], PS["midgame"], PS["window"], PS["garbage"], PS["our_reading"])
        self.OVERVIEW_REQUIRED = ((RS.EYEBROW, RS.TITLE_MARK, RS.NO_CLAIM, RS.HOLE_SENTENCE)
                                  + self.PAGE_SENTENCES + (PS["control"],))
        self.DP = self.PROSE["demo"]
        DS = self.DP["sentences"]
        self.DEMO_SENTENCES = (DS["demo"], DS["engine"], DS["base"], DS["order"], DS["rule"])
        self.DEMO_REQUIRED = (RS.EYEBROW, RS.TITLE_MARK, RS.NO_CLAIM, PS["source"]) + self.DEMO_SENTENCES
        self.CLASSES = {**RT.PIECE_CLASS, **p.cell_classes}

    # ------------------------------------------------------------ inputs

    def _need(self, cond, msg):
        if not cond:
            raise SystemExit(f"{self.p.module}: {msg}")

    def _no_simplified(self, text, where):
        bad = sorted(set(text) & SIMPLIFIED)
        self._need(not bad, f"{where}: simplified glyph(s) {bad} — this report is traditional-character Cantonese")
        return text

    def load_prose(self, path):
        with open(path, encoding="utf-8") as fh:
            prose = json.load(fh)
        for s in RT._walk_strings(prose):
            self._no_simplified(s, os.path.basename(path))
        return prose

    def load_inputs(self, repo=REPO):
        """(transcription, facts artefact, demos artefact)."""
        out = []
        for rel in (self.p.transcription_rel, self.p.facts_rel, self.p.demos_rel):
            with open(os.path.join(repo, rel), encoding="utf-8") as fh:
                out.append(json.load(fh))
        return tuple(out)

    def check_inputs(self, tr, art, demos):
        self._need(tr.get("schema") == self.p.transcription_schema, f"unknown transcription schema {tr.get('schema')!r}")
        self._need(art.get("schema") == self.p.facts_schema, f"unknown facts schema {art.get('schema')!r}")
        self._need(demos.get("schema") == self.p.demos_schema, f"unknown demos schema {demos.get('schema')!r}")
        self._need(art.get("report_eligible") is False,
                   f"{os.path.basename(self.p.facts_rel)} must declare report_eligible: false — simulator boards "
                   "are not trust-chain data")
        self._need(demos.get("report_eligible") is False and demos.get("constructed") is True,
                   f"{os.path.basename(self.p.demos_rel)} must declare report_eligible: false and constructed: true")
        self._need(self.p.variant in art["variants"], f"the facts artefact has no variant {self.p.variant!r}")

    def variant(self, tr):
        v = [x for x in tr["variants"] if x["id"] == self.p.variant]
        self._need(len(v) == 1, f"the transcription has {len(v)} variants {self.p.variant!r}")
        return v[0]

    def name(self, nid):
        names = self.PROSE["names"]
        self._need(nid in names, f"no Cantonese name for board {nid!r} in the prose file")
        return names[nid]

    # ------------------------------------------------------------ figures

    def figures(self, art):
        """Every figure the overview prints, by key, from the artefact's AGGREGATES."""
        v = art["variants"][self.p.variant]
        den, opp = art["denominators"], self.p.opportunity
        out = {}
        for u in sorted(den):
            h = v["hits_by_player"][u]
            for k in ("all", "in_opener", "mid_game"):
                out[f"hits.{u}.{k}"] = _nn(h[k], den[u][opp][k])
            out[f"mirrored.{u}"] = _nn(h["mirrored"], h["all"])
            out[f"garbage.{u}"] = _nn(h["garbage_in_window"], h["all"])
            f = v["followup_by_player"][u]
            out[f"fired.{u}"] = _nn(f["fired"], h["all"])
            for r, n in f["not_fired"].items():
                out[f"reason.{u}.{r}"] = _nn(n, h["all"])
            c = v["controls"]
            for kind, by in c["under"].items():
                out[f"under.{kind}.{u}"] = _nn(by[u], den[u][kind]["all"])
            for ab, by in c["ablation"].items():
                out[f"ablation.{ab}.{u}"] = _nn(by[u], den[u][opp]["all"])
            out[f"baseline.{u}"] = _nn(c["orientation_baseline"][u], den[u][opp]["all"])
        cr = art.get("cross_route")
        if cr:
            out["cross"] = _nn(cr["with_hit_after"], cr["rounds"])
        return out

    def recount(self, art):
        """The hit-derived figures again, RE-COUNTED from the hit list (the audit's half): the
        renderer prints the aggregates, so the page renders only when the two agree."""
        v = art["variants"][self.p.variant]
        den, opp = art["denominators"], self.p.opportunity
        hits = [h for h in art["hits"] if h["variant"] == self.p.variant]
        out = {}
        for u in sorted(den):
            mine = [h for h in hits if h["player"] == u]
            out[f"hits.{u}.all"] = _nn(len(mine), den[u][opp]["all"])
            out[f"hits.{u}.in_opener"] = _nn(sum(h["in_opener"] for h in mine), den[u][opp]["in_opener"])
            out[f"hits.{u}.mid_game"] = _nn(sum(not h["in_opener"] for h in mine), den[u][opp]["mid_game"])
            out[f"mirrored.{u}"] = _nn(sum(h["mirrored"] for h in mine), len(mine))
            out[f"garbage.{u}"] = _nn(sum(h["garbage_in_window"] for h in mine), len(mine))
            out[f"fired.{u}"] = _nn(sum(h["followup"]["fired"] for h in mine), len(mine))
            for r in sorted({h["followup"]["reason"] for h in mine if not h["followup"]["fired"]}):
                out[f"reason.{u}.{r}"] = _nn(sum(h["followup"]["reason"] == r for h in mine), len(mine))
            c = v["controls"]
            for kind, by in c["under"].items():
                out[f"under.{kind}.{u}"] = _nn(by[u], den[u][kind]["all"])
            for ab, by in c["ablation"].items():
                out[f"ablation.{ab}.{u}"] = _nn(by[u], den[u][opp]["all"])
            out[f"baseline.{u}"] = _nn(c["orientation_baseline"][u], den[u][opp]["all"])
        cr = art.get("cross_route")
        if cr:
            out["cross"] = _nn(sum(r["hit_lock"] is not None for r in cr["by_round"]), len(cr["by_round"]))
        return out

    # ------------------------------------------------------------ page shell

    def _head(self, title, desc, users, with_player):
        css = [RP._tokens_css(), RP.BASE_CSS.strip("\n"), RT.PAGE_CSS.strip("\n")]
        if self.p.extra_css:
            css.append(self.p.extra_css.strip("\n"))
        if with_player:
            css += [RS._color_css([{"user": u} for u in users]), RS.CSS.strip("\n")]
        return [
            "<!doctype html>",
            '<html lang="zh-HK">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{_esc(title)}</title>",
            f'<meta name="description" content="{_esc(desc)}">',
            "<style>",
            "  " + "\n".join(css),
            "</style>",
            "</head>",
            "<body>",
            '<div class="wrap-wide">',
        ]

    def _nav(self, other_href, other_words):
        return ['  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a>'
                f'<a href="{_esc(other_href)}">{_esc(other_words)}</a></nav>']

    def _window_rows(self, tr, v, mirrored):
        rows = [n for n in tr["nodes"] if n["id"] == v["board"]][0]["rows"]
        empties = tr.get("empty_letters", "")
        (r0, r1), (c0, c1) = v["window"]["rows"], v["window"]["cols"]
        tcells = {(r, c) for r, c in v["t_cells"]}
        out = []
        for r in range(r0, r1 + 1):
            line = ""
            for c in range(c0, c1 + 1):
                ch = rows[r][c]
                line += "U" if (r, c) in tcells else ("-" if ch == "-" or ch in empties else "c")
            out.append(line[::-1] if mirrored else line)
        return out

    def _thumb(self, tr, v, h):
        """A hit's window before the T, its letters as the artefact records them, the T's cells as the
        dashed slot (mirrored with the window)."""
        (r0, _r1), (c0, c1) = v["window"]["rows"], v["window"]["cols"]
        w = c1 - c0
        tcells = {(r - r0, (w - (c - c0)) if h["mirrored"] else (c - c0)) for r, c in v["t_cells"]}
        rows = []
        for r, line in enumerate(h["window_letters"]):
            s = ""
            for c, ch in enumerate(line):
                if (r, c) in tcells:
                    s += "U"
                elif ch == ".":
                    s += "-"
                elif ch == "G":
                    s += "c"
                else:
                    s += ch.lower()
            rows.append(s)
        return board_svg(rows, case_key(h), self.CLASSES)

    # ------------------------------------------------------------ the overview

    def render_overview(self, tr, art, demos):
        PR, T, S = self.PROSE, self.PROSE["table"], self.PROSE["sections"]
        v = self.variant(tr)
        fig = self.figures(art)
        users = sorted(art["denominators"])
        title = f"{PR['title']}{RS.TITLE_MARK}"
        out = self._head(title, PR["desc"], users, False)
        out += self._nav(self.DEMO_PAGE, self.DP["title"])
        out += ['  <header class="scp-head">',
                f'    <div class="eyebrow">{RS.EYEBROW}</div>',
                f'    <h1 class="section-title">{_esc(title)}</h1>',
                f'    <p>{_esc(PR["lede"])}</p>',
                RT._source_line(tr, PR.get("source_credit")),
                '  </header>',
                '  <div class="method-note">',
                '    <p><strong>呢版唔屬於信任鏈。</strong>每個盤面都係<strong>一個 replay 模擬器</strong>'
                '（Triangle 引擎）重跑操作記錄推導出嚟，冇第二份獨立實作；邊一下 TSD 對到呢個形亦係由佢推出嚟。'
                f'所以呢版<strong>{RS.NO_CLAIM}</strong>。</p>']
        out += [f"    <p>{s}</p>" for s in self.PAGE_SENTENCES]
        out += [f"    <p>{RS.HOLE_SENTENCE}</p>", "  </div>"]

        # 1. the boards, page order then the derived terrains
        quotes = {q["id"]: q["verbatim"] for q in tr["quotes"]}
        disc = {d["id"].split(":")[0]: d["id"] for d in tr["known_discrepancies"]}
        order = list(tr["page_order"]) + [n["id"] for n in tr["nodes"] if n["id"] not in tr["page_order"]]
        by_id = {n["id"]: n for n in tr["nodes"]}
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["boards"])}</h2>',
                f'    <p class="scp-quote">{_esc(S["boards_note"])}</p>', '    <div class="scp-grid">']
        for nid in order:
            n = by_id[nid]
            bits = [f'<div class="scp-node" data-board="{_esc(nid)}">', f'<h4 class="scp-name">{_esc(self.name(nid))}</h4>']
            if n.get("caption_quote"):
                bits.append(f'<p class="scp-jp">原頁：{_src(quotes[n["caption_quote"]])}</p>')
            bits.append(board_svg(n["rows"], self.name(nid), self.CLASSES))
            if n.get("derived"):
                bits.append(f'<p class="scp-tag">{_esc(PR["derived_note"])}</p>')
            if nid in disc:
                bits.append(f'<p class="scp-tag">{_esc(PR["discrepancies"][disc[nid]])}</p>')
            bits.append("</div>")
            out.append("    " + "".join(bits))
        out += ["    </div>", "  </section>"]

        # 2. the window
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["window"])}</h2>',
                f'    <p>{_esc(S["window_note"])}</p>', '    <div class="scp-grid">']
        for mirrored, words in ((False, S["window_drawn"]), (True, S["window_mirrored"])):
            out.append(f'    <div class="scp-node"><h4 class="scp-name">{_esc(words)}</h4>'
                       f'{board_svg(self._window_rows(tr, v, mirrored), words, self.CLASSES)}</div>')
        out += ["    </div>", "  </section>"]

        # 3. the headline, with the control sentence beside it
        cell = lambda k: f'<td data-figure="{_esc(k)}">{_esc(fig[k])}</td>'
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["headline"])}</h2>',
                f'    <p>{_esc(S["headline_note"].format(pieces=art["window_pieces"] + 1, last=art["window_pieces"]))}</p>',
                f'    <p>{self.PS["control"]}</p>',
                '    <div class="scp-index-wrap"><table class="scp-table">',
                f'    <tr><th>{_esc(T["player"])}</th><th>{_esc(T["all"])}</th><th>{_esc(T["in_opener"])}</th>'
                f'<th>{_esc(T["mid_game"])}</th><th>{_esc(T["mirrored"])}</th><th>{_esc(T["garbage"])}</th></tr>']
        for u in users:
            out.append(f"    <tr><th>{_esc(u)}</th>" + "".join(cell(k) for k in (
                f"hits.{u}.all", f"hits.{u}.in_opener", f"hits.{u}.mid_game", f"mirrored.{u}", f"garbage.{u}")) + "</tr>")
        out += ["    </table></div>"]

        # 4. controls
        ctl = art["variants"][self.p.variant]["controls"]
        out += [f'    <h3>{_esc(S["controls"])}</h3>', '    <div class="scp-index-wrap"><table class="scp-table">',
                f'    <caption>{_esc(T["denominator_note"])}</caption>',
                f'    <tr><th>{_esc(T["row"])}</th>' + "".join(f"<th>{_esc(u)}</th>" for u in users) + "</tr>"]
        for kind in ctl["under"]:
            out.append(f'    <tr><th>{_esc(T["under"].format(kind=PR["spin_kinds"][kind]))}</th>'
                       + "".join(cell(f"under.{kind}.{u}") for u in users) + "</tr>")
        for ab in ctl["ablation"]:
            out.append(f'    <tr><th>{_esc(T["ablation"][ab])}</th>' + "".join(cell(f"ablation.{ab}.{u}") for u in users) + "</tr>")
        out.append(f'    <tr><th>{_esc(T["baseline"])}</th>' + "".join(cell(f"baseline.{u}") for u in users) + "</tr>")
        out += ["    </table></div>", "  </section>"]

        # 5. the follow-up
        reasons = sorted({k.split(".", 2)[2] for k in fig if k.startswith("reason.")})
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["followup"])}</h2>',
                f'    <p>{_esc(S["followup_note"])}</p>',
                '    <div class="scp-index-wrap"><table class="scp-table">',
                f'    <tr><th>{_esc(T["followup_head"])}</th>' + "".join(f"<th>{_esc(u)}</th>" for u in users) + "</tr>",
                f'    <tr><th>{_esc(T["fired"])}</th>' + "".join(cell(f"fired.{u}") for u in users) + "</tr>"]
        for r in reasons:
            out.append(f'    <tr><th>{_esc(PR["reasons"][r])}</th>' + "".join(
                cell(f"reason.{u}.{r}") if f"reason.{u}.{r}" in fig else "<td>—</td>" for u in users) + "</tr>")
        out += ["    </table></div>", "  </section>"]

        # 6. the cross-source
        cr = art.get("cross_route")
        if cr:
            out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["cross"])}</h2>',
                    f'    <p>{_esc(S["cross_note"])}</p>',
                    f'    <p class="scp-count" data-figure="cross">{_esc(fig["cross"])}</p>',
                    '    <div class="scp-index-wrap"><table class="scp-table">',
                    f'    <tr><th>{_esc(T["cross_round"])}</th><th>{_esc(T["cross_node"])}</th>'
                    f'<th>{_esc(T["cross_hit"])}</th><th>{_esc(T["reason"])}</th></tr>']
            for r in cr["by_round"]:
                out.append(f'    <tr><td>{_esc(r["round"])}</td><td>{r["node_lock"]}</td>'
                           f'<td>{"—" if r["hit_lock"] is None else r["hit_lock"]}</td>'
                           f'<td><code>{_esc(r["reason"] or "")}</code></td></tr>')
            out += ["    </table></div>", "  </section>"]

        # 7. the cases
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["cases"])}</h2>',
                f'    <p>{_esc(S["cases_note"])}</p>',
                '    <div class="scp-index-wrap"><table class="scp-table">',
                f'    <tr><th>{_esc(T["date"])}</th><th>{_esc(T["round"])}</th><th>{_esc(T["player"])}</th>'
                f'<th>{_esc(T["lock"])}</th><th>{_esc(T["phase"])}</th><th>{_esc(T["window_col"])}</th>'
                f'<th>{_esc(T["followup_col"])}</th></tr>']
        for h in art["hits"]:
            if h["variant"] != self.p.variant:
                continue
            fu = h["followup"]
            fw = T["yes"].format(lock=fu["lock"]) if fu["fired"] else PR["reasons"][fu["reason"]]
            href = f'{h["session"]}-replay.html#m{h["match"]}r{h["round"]}'
            out.append(f'    <tr data-case="{_esc(case_key(h))}"><td>{_esc(h["session"])}</td>'
                       f'<td><a href="{_esc(href)}">m{h["match"]}r{h["round"]}</a></td><td>{_esc(h["player"])}</td>'
                       f'<td>{h["lock"]}{_esc(T["mirrored_mark"]) if h["mirrored"] else ""}</td>'
                       f'<td>{_esc(T["phase_opener"] if h["in_opener"] else T["phase_mid"])}</td>'
                       f'<td>{self._thumb(tr, v, h)}</td><td>{_esc(fw)}</td></tr>')
        out += ["    </table></div>", "  </section>"]
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["demos"])}</h2>',
                f'    <p><a href="{_esc(self.DEMO_PAGE)}">{_esc(S["demos_link"])}</a></p>', '  </section>']
        out += RT._tail({"figures": fig})
        return "\n".join(out)

    # ------------------------------------------------------------ the demo page

    def reach_problems(self, d, demos, tr):
        """The page's own check of one demo, a second implementation of `technique-demos.ts`'s
        `reachProblems`: decoded from an empty board with `replay_section.decode_boards`."""
        by_id = {n["id"]: n for n in tr["nodes"]}
        v = self.variant(tr)
        empties = tr.get("empty_letters", "")
        b = demos["board"]
        width, rows_n = b["width"], b["rows"]
        try:
            steps = [(p, [list(r) for r in board]) for p, _f, board in
                     RS.decode_boards(demos, d["seq"], d["locks"], RS.NEXT_SHOWN)]
        except SystemExit as e:
            return [f"{d['node']}: does not decode: {e}"]

        def ok(board, rows, cols=None):
            h = len(rows)
            for y, line in enumerate(board):
                for x, val in enumerate(line):
                    ch = rows[h - 1 - y][x] if y < h else "-"
                    strict = cols is None or cols[0] <= x <= cols[1]
                    if ch == "-" or ch in empties:
                        if strict and val is not None:
                            return False
                    elif val is None:
                        return False
                    elif strict and ch.islower() and ch != "c" and val != ch.upper():
                        return False
            return True

        def cells(i):
            return sorted(RS._place_cells(demos["shapes"], width, rows_n, steps[i][0], d["locks"][i][1]))

        def drawn(rows, letters):
            h = len(rows)
            return sorted((h - 1 - i) * width + x for i, row in enumerate(rows) for x, ch in enumerate(row)
                          if ch in letters)

        bad = []
        for r in d["reaches"]:
            n, i, where = by_id.get(r["node"]), r["lock"], f"{d['node']} → {r['node']}"
            if n is None or not 0 <= i < len(steps):
                bad.append(f"{where}: no such board or lock")
                continue
            lk = d["locks"][i]
            if r["check"] == "board":
                if not ok(steps[i][1], n["rows"]):
                    bad.append(f"{where}: the board after lock {i + 1} is not the drawing")
            elif r["check"] == "spin":
                if steps[i][0] != "T" or lk[3] != 2 or lk[2] != n["lines"] or cells(i) != drawn(n["rows"], "Tt"):
                    bad.append(f"{where}: lock {i + 1} is not the drawing's T")
                elif not ok(steps[i - 1][1], by_id[n["spin_of"]]["rows"]):
                    bad.append(f"{where}: the board before lock {i + 1} is not {n['spin_of']}")
            elif r["check"] == "after":
                h = len(n["rows"])
                slot = sorted((h - 1 - row) * width + col for row, col in v["followup"]["t_cells_after"])
                cols = (v["window"]["cols"][0] + d["offset"]["dc"], v["window"]["cols"][1] + d["offset"]["dc"])
                if steps[i][0] != "T" or lk[3] != 2 or lk[2] != v["followup"]["lines"] or cells(i) != slot:
                    bad.append(f"{where}: lock {i + 1} is not the drawn follow-up")
                elif not ok(steps[i - 1][1], n["rows"], cols):
                    bad.append(f"{where}: the board before lock {i + 1} does not show the drawing")
            else:
                bad.append(f"{where}: unknown check {r['check']!r}")
        return bad

    def _demo_payload(self, d):
        moments = []
        for e in d["events"]:
            nm = RS.SPIN_NAMES.get((e["spin"], e["lines"]))
            self._need(nm is not None, f"{d['node']}: spin {e['spin']} with {e['lines']} lines has no name")
            moments.append([e["lock"] + 1, 0, "tspin", self.DP["spin"].format(n=e["lock"] + 1, name=nm)])
        return {"label": demo_slug(d["node"]), "title": self.DP["now"].format(name=self.name(d["node"])),
                "seq": d["seq"], "order": "0" * len(d["locks"]), "winner": None,
                "players": [{"user": self.DP["user"], "slot": 0, "ending": None, "frames": d["frames"],
                             "pieces": len(d["locks"]), "locks": d["locks"], "ge": [],
                             "verified_to": None, "after": None, "failed_at": None}],
                "moments": moments, "flags": [], "notes": [self._chain_words(d)]}

    def _chain_words(self, d):
        pieces = [q for q, _h in RS.queue_states(d["seq"], d["locks"], RS.NEXT_SHOWN)]
        roles = d["roles"]
        part = lambda code: "".join(p for p, r in zip(pieces, roles) if r == code)
        words = [self.DP["base_words"].format(n=d["base_locks"], pieces=part("b")),
                 self.DP["page_words"].format(pieces=part("p"))]
        if part("f"):
            words.append(self.DP["fill_words"].format(pieces=part("f")))
        return self.DP["chain"].format(chain="；".join(words))

    def render_demo_page(self, tr, demos):
        bad = [x for d in demos["demos"] for x in self.reach_problems(d, demos, tr)]
        self._need(not bad, "; ".join(bad))
        DP = self.DP
        title = f"{DP['title']}{RS.TITLE_MARK}"
        shared = {"shapes": demos["shapes"], "width": demos["board"]["width"], "rows": demos["board"]["rows"],
                  "visible": demos["board"]["visible_rows"], "next": RS.NEXT_SHOWN, "flag_words": RS.FLAG_WORDS}
        by_id = {n["id"]: n for n in tr["nodes"]}
        with open(RT.PAGE_JS, encoding="utf-8") as fh:
            page_js = fh.read().rstrip()
        self._need("</script" not in page_js.lower(), "stray_cannon_page.js may not contain a closing script tag")
        out = self._head(title, DP["desc"], [DP["user"]], True)
        out += self._nav(self.OVERVIEW, self.PROSE["overview_title"])
        out += ['  <header class="scp-head">',
                f'    <div class="eyebrow">{RS.EYEBROW}</div>',
                f'    <h1 class="section-title">{_esc(title)}</h1>',
                f'    <p>{_esc(DP["lede"])}</p>',
                RT._source_line(tr, self.PROSE.get("source_credit")),
                '  </header>',
                '  <div class="method-note">',
                f'    <p><strong>呢版唔屬於信任鏈，亦唔係對局。</strong>所以呢版<strong>{RS.NO_CLAIM}</strong>。</p>']
        out += [f"    <p>{s}</p>" for s in (self.PS["source"],) + self.DEMO_SENTENCES]
        out.append("  </div>")
        out += [f'  <section id="{RS.SECTION_ID}" aria-labelledby="rpg-now">',
                '    <h2 class="rpg-now" id="rpg-now" aria-live="polite"></h2>',
                f'    <p class="scp-idle">{_esc(DP["idle"])}</p>',
                '    <p class="rpg-notes"></p>',
                f'    <p class="rpg-flag" hidden>{RS.FLAG_WORDS}</p>',
                f'    <p class="rpg-missing" hidden>{_esc(self.PROSE["missing"])}</p>',
                '    <noscript><p>重播要開 JavaScript 先用到。</p></noscript>',
                '    <div class="rpg-host"></div>',
                f'    <template id="{TEMPLATE_ID}">',
                *["  " + line for line in RS.player_box("", [DP["user"]], bands=False)],
                '    </template>',
                '  </section>',
                '  <div class="scp-grid scd-grid">']
        rounds = {}
        for d in demos["demos"]:
            slug = demo_slug(d["node"])
            rounds[slug] = self._demo_payload(d)
            n = by_id[d["node"]]
            bits = [f'    <div class="scp-node" id="{slug}" data-demo-node="{_esc(d["node"])}" data-demo="built">',
                    f'<h4 class="scp-name">{_esc(self.name(d["node"]))}</h4>',
                    board_svg(n["rows"], self.name(d["node"]), self.CLASSES),
                    f'<p><a class="scp-case" href="#{slug}" data-round="{slug}">{_esc(DP["play"])}</a></p>',
                    f'<p class="scp-tag">{_esc(self._chain_words(d))}</p>',
                    f'<p class="scp-cond">{_esc(DP["events"].format(events="，".join(m[3] for m in rounds[slug]["moments"])))}</p>',
                    f'<p class="scp-cond">{_esc(DP["reaches"].format(boards=""))}'
                    + "、".join(f'<span data-reach="{_esc(r["node"])}">{_esc(self.name(r["node"]))}</span>'
                               for r in d["reaches"]) + "</p>",
                    "</div>"]
            out.append("".join(bits))
        out.append("  </div>")
        out += [f'  <h2 class="scp-sec">{_esc(DP["unbuilt_title"])}</h2>', '  <div class="scp-grid">']
        for u in demos["unbuilt"]:
            n = by_id[u["node"]]
            out.append(f'    <div class="scp-node" data-demo-node="{_esc(u["node"])}" data-demo="unbuilt">'
                       f'<h4 class="scp-name">{_esc(self.name(u["node"]))}</h4>'
                       f'{board_svg(n["rows"], self.name(u["node"]), self.CLASSES)}'
                       f'<p class="scp-count">{_esc(DP["unbuilt"].format(reason=u["reason"]))}</p></div>')
        out.append("  </div>")
        island = {"shared": shared, "rounds": rounds, "cases": [{"case": k, "round": k} for k in rounds]}
        out += RT._tail(island, (RS.player_js(), page_js))
        return "\n".join(out)

    # ------------------------------------------------------------ audits

    def audit_text(self, page):
        bad = []
        vis = RT._visible(page)
        if set(page) & SIMPLIFIED:
            bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
        if "%" in _TAG.sub("", _SRC_QUOTE.sub("", vis)):
            bad.append("a % outside quoted source text — this page prints counts, never computed rates")
        return bad

    def audit_overview(self, page, tr, art):
        bad = RP.audit_quarantine(page, self.OVERVIEW_REQUIRED, DATA_ID) + self.audit_text(page)
        boards = _BOARD.findall(page)
        if sorted(boards) != sorted(n["id"] for n in tr["nodes"]):
            bad.append(f"the overview does not draw every board exactly once ({len(boards)} drawn, {len(tr['nodes'])} boards)")
        cases = _CASE.findall(page)
        want = sorted(case_key(h) for h in art["hits"] if h["variant"] == self.p.variant)
        if sorted(html.unescape(c) for c in cases) != want:
            bad.append(f"the case index does not list every hit exactly once ({len(cases)} rows, {len(want)} hits)")
        figs = {}
        for k, val in _FIGURE.findall(page):
            if k in figs:
                bad.append(f"figure {k} printed twice")
            figs[k] = html.unescape(val)
        rc = self.recount(art)
        if figs != rc:
            diff = sorted(k for k in set(figs) | set(rc) if figs.get(k) != rc.get(k))
            bad.append(f"the printed figures are not the artefact's, recounted: {diff[:4]}")
        if any(k.startswith("hits.") for k in figs) and self.PS["control"] not in page:
            bad.append("the headline is printed without the control sentence")
        if f'href="{self.DEMO_PAGE}"' not in page:
            bad.append("the overview does not link the demo page")
        return bad

    def audit_demo_page(self, page, tr, demos):
        bad = (RP.audit_quarantine(page, self.DEMO_REQUIRED, DATA_ID) + RP.audit_player(page)
               + self.audit_text(page))
        blocks = _DEMO_BLOCK.findall(page)
        seen = [nid for nid, _st in blocks]
        if len(seen) != len(set(seen)):
            bad.append("a demo block appears twice on the demo page")
        want = {d["node"]: "built" for d in demos["demos"]}
        want.update({u["node"]: "unbuilt" for u in demos["unbuilt"]})
        if dict(blocks) != want:
            bad.append("the demo page's blocks are not every demo and every unbuilt board")
        reached = _REACH.findall(page)
        cover = sorted(reached + [u["node"] for u in demos["unbuilt"]])
        if cover != sorted(n["id"] for n in tr["nodes"]):
            bad.append("the demo page does not account for every board exactly once (reached or unbuilt)")
        m = RT._ISLAND.search(page)
        if not m:
            return bad + ["no data island on the demo page"]
        island = json.loads(m.group(1))
        if sorted(island["rounds"]) != sorted(demo_slug(d["node"]) for d in demos["demos"]):
            bad.append("the demo page does not embed every demo exactly once")
        for d in demos["demos"]:
            r = island["rounds"].get(demo_slug(d["node"]))
            if r is None:
                continue
            shown = dict(d, seq=r["seq"], locks=r["players"][0]["locks"])
            bad += [f"embedded {x}" for x in self.reach_problems(shown, demos, tr)]
        return bad

    def audit_all(self, pages, tr, art, demos):
        return (self.audit_overview(pages[self.OVERVIEW], tr, art)
                + self.audit_demo_page(pages[self.DEMO_PAGE], tr, demos))

    def render_all(self, repo=REPO, inputs=None):
        tr, art, demos = inputs or self.load_inputs(repo)
        self.check_inputs(tr, art, demos)
        self._need(self.figures(art) == self.recount(art),
                   "the facts artefact's aggregates disagree with its own hit list")
        pages = {self.OVERVIEW: self.render_overview(tr, art, demos), self.DEMO_PAGE: self.render_demo_page(tr, demos)}
        for name, page in pages.items():
            self._no_simplified(page, name)
            size = len(page.encode())
            self._need(not self.p.max_page_bytes or size <= self.p.max_page_bytes,
                       f"{name} is {size} bytes, over the profile's {self.p.max_page_bytes}")
        bad = self.audit_all(pages, tr, art, demos)
        self._need(not bad, "; ".join(bad))
        return pages

    # ------------------------------------------------------------ selftest

    def _selftest(self):
        inputs = self.load_inputs(REPO)
        tr, art, demos = inputs
        pages = self.render_all(REPO, inputs)
        ov, dp = pages[self.OVERVIEW], pages[self.DEMO_PAGE]
        first_case = _CASE.search(ov)
        case_line = [l for l in ov.split("\n") if first_case.group(0) in l][0]
        fig = _FIGURE.search(ov)
        isl = RT._ISLAND.search(dp)
        island = json.loads(isl.group(1))
        slug = demo_slug(demos["demos"][0]["node"])
        bad_island = json.loads(isl.group(1))
        bad_island["rounds"][slug]["players"][0]["locks"][0][1] += 1
        corrupt = dp.replace(isl.group(1), RT._island(bad_island))
        reach = _REACH.search(dp).group(0)
        cases = [
            ("overview: a required sentence dropped", "ov", ov.replace(self.PS["midgame"], "")),
            ("overview: a badge", "ov", ov.replace("</body>", '<span data-claim="G001">✓</span></body>')),
            ("overview: an innerHTML", "ov", ov.replace("</body>", "<script>x.innerHTML=1</script></body>")),
            ("overview: a hit row dropped", "ov", ov.replace(case_line + "\n", "")),
            ("overview: a hit row duplicated", "ov", ov.replace(case_line, case_line + "\n" + case_line)),
            ("overview: a figure changed", "ov",
             ov.replace(fig.group(0), f'data-figure="{fig.group(1)}">{fig.group(2)}0<', 1)),
            ("overview: the control sentence dropped", "ov", ov.replace(self.PS["control"], "")),
            ("overview: a board dropped", "ov", RT._drop_line(ov, 'data-board="basic.after"')),
            ("overview: a %", "ov", ov.replace("</header>", "<p>12%</p></header>")),
            ("overview: a simplified glyph", "ov", ov.replace("</header>", "<p>这</p></header>")),
            ("demo: an embedded lock moved", "dp", corrupt),
            ("demo: a reach dropped", "dp", dp.replace(reach, "<span>", 1)),
            ("demo: a demo block dropped", "dp", RT._drop_line(dp, f'id="{slug}"')),
            ("demo: a required sentence dropped", "dp", dp.replace(self.DS_rule(), "")),
        ]
        ok = True
        for name, which, page in cases:
            if page == (ov if which == "ov" else dp):
                print(f"  BAD {name}: the plant changed nothing")
                ok = False
                continue
            got = (self.audit_overview(page, tr, art) if which == "ov" else self.audit_demo_page(page, tr, demos))
            good = bool(got)
            ok &= good
            print(f"  {'ok ' if good else 'BAD'} {name}: {got[:1]}")
        # input-level refusals
        refused = 0
        for name, mutate in (
                ("facts not quarantined", lambda t, a, d: a.__setitem__("report_eligible", True)),
                ("demos not constructed", lambda t, a, d: d.__setitem__("constructed", False)),
                ("an aggregate disagrees with the hit list",
                 lambda t, a, d: a["variants"][self.p.variant]["followup_by_player"][sorted(a["denominators"])[0]]
                 .__setitem__("fired", a["variants"][self.p.variant]["followup_by_player"][sorted(a["denominators"])[0]]["fired"] + 1))):
            t2, a2, d2 = (json.loads(json.dumps(x)) for x in inputs)
            mutate(t2, a2, d2)
            try:
                self.render_all(REPO, (t2, a2, d2))
                good = False
            except SystemExit:
                good = True
            ok &= good
            refused += 1
            print(f"  {'ok ' if good else 'BAD'} refused: {name}")
        print(f"{'ok ' if ok else 'FAIL'} {self.p.module} selftest: {len(cases) + refused} corruptions, "
              f"{'all caught' if ok else 'SOME MISSED'}")
        return 0 if ok else 1

    def DS_rule(self):
        return self.DP["sentences"]["rule"]

    def main(self, argv=None, doc=None):
        ap = argparse.ArgumentParser(description=(doc or __doc__).splitlines()[0])
        ap.add_argument("--out-dir")
        ap.add_argument("--selftest", action="store_true")
        a = ap.parse_args(argv)
        if a.selftest:
            return self._selftest()
        if not a.out_dir:
            ap.error("need --out-dir, or --selftest")
        os.makedirs(a.out_dir, exist_ok=True)
        for name, page in self.render_all(REPO).items():
            with open(os.path.join(a.out_dir, name), "w", encoding="utf-8") as fh:
                fh.write(page)
            print(f"wrote {os.path.join(a.out_dir, name)} ({len(page.encode())} bytes)")
        return 0


def site_card(site, art):
    """The index card's words and count for one technique (`bin/build-docs`)."""
    card = site.PROSE["index_card"]
    return {"href": site.OVERVIEW, "cases": sum(h["variant"] == site.p.variant for h in art["hits"]),
            "kicker": card["kicker"], "title": site.PROSE["overview_title"], "blurb": card["blurb"]}

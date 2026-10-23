"""DPC — the page for harddrop's DPC setups against the corpus: `docs/dpc.html`, audited before it is returned.

    python3 -m pipeline.dpc_page --out-dir /tmp/dpc   # render it somewhere other than docs/
    python3 -m pipeline.dpc_page --selftest           # the audit's mutants

Inputs, all committed: the setups transcription (`pipeline/openers/dpc-setups.json`, gated by
`extract_dpc_setups`) and the corpus artefact (`analysis/dpc-facts.json`, from `pipeline/sim/dpc-facts.ts`).
Pure Python, so `bin/build-docs` renders it in the `docs` job. Not a route page and not a technique page
(`pipeline.sites` lists neither it nor its artefacts, because the replay labels and the report's routes
section read those lists): a DPC setup is a whole board from empty after a Perfect Clear, so it has its
own small matcher and this own small page. It imports the shared pieces and edits none of them:
`board_svg`, the page CSS, the tail, and the technique pages' replay-position reader (`_replay_round` /
`replay_href`, borrowed as methods, ONE copy of that rule).

QUARANTINE, the technique pages' tier: no claim ids, no ✓, no `data-claim`, the artefact must say
`report_eligible: false`. The audit reuses `replay_page.audit_quarantine` and adds:

* every setup in the transcription is drawn exactly once (`data-board`), and every case indexed exactly once;
* every printed figure (`data-figure`) is RECOUNTED from the case list, never read from the aggregates;
* every case link is read back from the replay side: the position's next step is the case player's lock at
  the case's lock index, a T with the case's spin and lines;
* the anchor sentence is printed with the artefact's agreement, and the page refuses to render if any
  player-round disagrees;
* no `%` outside quoted source text, no simplified glyph.

FIGURES. Counts only, 「N / M」 where there is a denominator; no rate is computed.
"""
import argparse
import html
import json
import os
import re
import sys

from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline import route_page as RT
from pipeline import technique_page as TP
from pipeline.claims.build_claims import SIMPLIFIED

HERE, REPO = RT.HERE, RT.REPO
_esc, board_svg, DATA_ID = RT._esc, RT.board_svg, RT.DATA_ID
PREFIX = "dpc"
OVERVIEW = "dpc.html"
SETUPS_REL = "pipeline/openers/dpc-setups.json"
ARTEFACT_REL = "analysis/dpc-facts.json"
PROSE_PATH = os.path.join(HERE, "dpc_prose.json")
SPIN_CODE = {"full": 2, "mini": 1}

_FIGURE = re.compile(r'data-figure="([^"]+)">([^<]*)<')
_BOARD = re.compile(r'data-board="([^"]+)"')
_CASE = re.compile(r'data-case="([^"]+)"')
_CASE_LINK = re.compile(r'<tr data-case="([^"]+)">.*?<a href="([^"]+)">')
_REPLAY_HREF = re.compile(r'^(\d{4}-\d{2}-\d{2})-replay\.html#(m\d+r\d+)@p(\d+)$')


def _need(cond, msg):
    if not cond:
        raise ValueError(f"dpc page: {msg}")


def case_key(c):
    return f'{c["session"]} m{c["match"]}r{c["round"]} {c["player"]} @{c["lock"]}'


def load_prose(path=PROSE_PATH):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    _need(not (set(text) & SIMPLIFIED), f"the prose carries simplified glyph(s) {sorted(set(text) & SIMPLIFIED)}")
    return json.loads(text)


class Replays:
    """The technique pages' replay-position reader, bound to this page: `_replay_round` and `replay_href` are
    `technique_page.TechniqueSite`'s own functions, so a case link here is computed by the same rule."""
    _replay_round = TP.TechniqueSite._replay_round
    replay_href = TP.TechniqueSite.replay_href

    def __init__(self, repo):
        self._repo = repo

    def _need(self, cond, msg):
        _need(cond, msg)


class DpcSite:
    def __init__(self, prose_path=PROSE_PATH):
        self.PROSE = load_prose(prose_path)
        self.OVERVIEW = OVERVIEW
        self.REQUIRED = (RS.EYEBROW, RS.TITLE_MARK, RS.NO_CLAIM, *self.PROSE["page_sentences"])

    def load_inputs(self, repo=REPO):
        with open(os.path.join(repo, SETUPS_REL), encoding="utf-8") as f:
            tr = json.load(f)
        with open(os.path.join(repo, ARTEFACT_REL), encoding="utf-8") as f:
            art = json.load(f)
        _need(art.get("report_eligible") is False, "the artefact is not marked report_eligible: false")
        _need(art["setups"] == len(tr["setups"]), "the artefact was built from another setups transcription")
        _need(not art["pc_anchor"]["disagree"], f"PC points disagree with the replay: {art['pc_anchor']['disagree'][:3]}")
        return tr, art

    # ------------------------------------------------------------ figures

    @staticmethod
    def recount(art):
        """Every printed figure, from the case list (and the per-player PC tallies, which the anchor checks)."""
        out = {}
        users = sorted(art["by_player"])
        for u in users:
            mine = [c for c in art["cases"] if c["player"] == u]
            p = art["by_player"][u]
            out[f"pcs.{u}"] = str(p["pc_points"])
            out[f"no_tspin.{u}"] = str(p["no_tspin"])
            for k, f in (("cases", lambda c: True), ("matched", lambda c: c["outcome"] == "matched"),
                         ("unmatched", lambda c: c["outcome"] != "matched")):
                out[f"{k}.{u}"] = str(sum(1 for c in mine if f(c)))
                out[f"{k}_v.{u}"] = str(sum(1 for c in mine if f(c) and c["verified"]))
        a = art["pc_anchor"]
        out["anchor"] = f'{a["rounds_agree"]}/{a["rounds"]}/{a["pcs_replay"]}'
        for c in art["cases"]:
            if c["outcome"] == "matched":
                k = f'setup.{c["setups"][0]}.{c["player"]}'
                out[k] = str(int(out.get(k, "0")) + 1)
        return out

    # ------------------------------------------------------------ boards

    @staticmethod
    def _setup_rows(tr, sid):
        """The setup as harddrop draws it, the T's cells as the dashed slot."""
        b = [b for b in tr["boards"] if b["id"] == sid][0]
        rows = list(b["rows"])
        while rows and rows[0] == "." * 10:
            rows.pop(0)
        conv = {".": "-", "P": "U"}
        return ["".join(conv.get(ch, ch.lower() if ch in "IJLOSTZijlostz" else "c") for ch in r) for r in rows]

    @staticmethod
    def _shape_rows(shape):
        return ["".join("c" if ch == "x" else "-" for ch in r) for r in shape]

    def name(self, tr, sid):
        s = [s for s in tr["setups"] if s["id"] == sid][0]
        page = [p for p in tr["pages"] if p["key"] == s["page"]][0]
        return f'{page["title"]} · {" › ".join(s["heading"])}'

    # ------------------------------------------------------------ the page

    def render(self, tr, art, repo=REPO):
        PR, S, T, Wd = self.PROSE, self.PROSE["sections"], self.PROSE["table"], self.PROSE["words"]
        fig = self.recount(art)
        users = sorted(art["by_player"])
        rp = Replays(repo)
        title = f'{PR["title"]}{RS.TITLE_MARK}'
        css = [RP._tokens_css(), RP.BASE_CSS.strip("\n"), RT.PAGE_CSS.strip("\n")]
        out = ["<!doctype html>", '<html lang="zh-HK">', "<head>", '<meta charset="utf-8">',
               '<meta name="viewport" content="width=device-width, initial-scale=1">',
               f"<title>{_esc(title)}</title>", f'<meta name="description" content="{_esc(PR["desc"])}">',
               "<style>", "  " + "\n".join(css), "</style>", "</head>", "<body>", '<div class="wrap-wide">',
               '  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a></nav>',
               '  <header class="scp-head">', f'    <div class="eyebrow">{RS.EYEBROW}</div>',
               f'    <h1 class="section-title">{_esc(title)}</h1>', f'    <p>{_esc(PR["lede"])}</p>',
               f'    <p class="scp-src-line">{_esc(PR["source_words"])}']
        links = [f'<a href="{_esc(p["url"])}">{_esc(p["title"])}</a>'
                 f'（<a href="https://harddrop.com/w/index.php?oldid={p["oldid"]}">revision {p["oldid"]}</a>）'
                 for p in tr["pages"]]
        out += ["    " + "、".join(links) + "。" + _esc(PR["source_terms"]) + "</p>",
                f'    <p>{_esc(PR["definition_intro"])}<q class="scp-src">{_esc(tr["source"]["definition"])}</q></p>',
                "  </header>", '  <div class="method-note">',
                '    <p><strong>呢版唔屬於信任鏈。</strong>每個盤面都係<strong>一個 replay 模擬器</strong>'
                '（Triangle 引擎）重跑操作記錄推導出嚟，冇第二份獨立實作；邊一下 T 對到邊個 setup 亦係由佢推出嚟。'
                f'所以呢版<strong>{RS.NO_CLAIM}</strong>。</p>']
        out += [f"    <p>{s}</p>" for s in PR["page_sentences"]]
        out += ["  </div>"]

        # 1. figures
        a = art["pc_anchor"]
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["figures"])}</h2>',
                f'    <p>{_esc(S["figures_note"])}</p>',
                f'    <p class="scp-count" data-figure="anchor">{a["rounds_agree"]}/{a["rounds"]}/{a["pcs_replay"]}</p>',
                f'    <p>{_esc(Wd["anchor"].format(agree=a["rounds_agree"], rounds=a["rounds"], pcs=a["pcs_replay"]))}</p>',
                '    <div class="scp-index-wrap"><table class="scp-table">',
                f'    <tr><th>{_esc(T["player"])}</th><th>{_esc(T["pcs"])}</th><th>{_esc(T["no_tspin"])}</th>'
                f'<th>{_esc(T["cases"])}</th><th>{_esc(T["matched"])}</th><th>{_esc(T["unmatched"])}</th></tr>']

        def cell(k, u):
            return (f'<td><span data-figure="{k}.{u}">{fig[f"{k}.{u}"]}</span>'
                    f'<span class="scp-tag">{_esc(T["verified_suffix"].split("{v}")[0])}'
                    f'<span data-figure="{k}_v.{u}">{fig[f"{k}_v.{u}"]}</span>'
                    f'{_esc(T["verified_suffix"].split("{v}")[1])}</span></td>')
        for u in users:
            out.append(f'    <tr><td>{_esc(u)}</td><td data-figure="pcs.{u}">{fig[f"pcs.{u}"]}</td>'
                       f'<td data-figure="no_tspin.{u}">{fig[f"no_tspin.{u}"]}</td>'
                       + cell("cases", u) + cell("matched", u) + cell("unmatched", u) + "</tr>")
        out += ["    </table></div>", "  </section>"]

        # 2. matched groups
        groups = {}
        for c in art["cases"]:
            if c["outcome"] == "matched":
                groups.setdefault(c["setups"][0], []).append(c)
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["matched"])}</h2>',
                f'    <p class="scp-quote">{_esc(S["matched_note"])}</p>', '    <div class="scp-grid">']
        for g in sorted(groups, key=lambda k: (-len(groups[k]), k)):
            cs = groups[g]
            names = "；".join(self.name(tr, sid) for sid in cs[0]["setups"])
            counts = "、".join(f'{_esc(u)}：<span data-figure="setup.{g}.{u}">{fig[f"setup.{g}.{u}"]}</span>'
                              for u in users if f"setup.{g}.{u}" in fig)
            out.append(f'    <div class="scp-node"><h4 class="scp-name">{_esc(names)}</h4>'
                       f'{board_svg(self._setup_rows(tr, g), names, RT.PIECE_CLASS)}<p class="scp-count">{counts}</p></div>')
        out += ["    </div>", "  </section>"]

        # 3. unmatched shapes seen at least twice
        multi = [s for s in art["unmatched_shapes"] if s["cases"] >= 2]
        single = sum(1 for s in art["unmatched_shapes"] if s["cases"] < 2)
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["unmatched"])}</h2>',
                f'    <p class="scp-quote">{_esc(S["unmatched_note"])}</p>', '    <div class="scp-grid">']
        for i, s in enumerate(multi):
            counts = "、".join(f"{_esc(u)}：{n}" for u, n in s["by_player"].items() if n)
            out.append(f'    <div class="scp-node" data-shape="{i}"><h4 class="scp-name">#{i + 1}（{s["cases"]}）</h4>'
                       f'{board_svg(self._shape_rows(s["shape"]), f"shape {i + 1}", RT.PIECE_CLASS)}'
                       f'<p class="scp-count">{counts}</p></div>')
        out += ["    </div>", f'    <p>{_esc(Wd["singletons"].format(n=single))}</p>', "  </section>"]

        # 4. every setup
        count = {}
        for c in art["cases"]:
            for sid in c["setups"]:
                count[sid] = count.get(sid, 0) + 1
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["setups"])}</h2>',
                f'    <p class="scp-quote">{_esc(S["setups_note"])}</p>']
        for p in tr["pages"]:
            mine = [s for s in tr["setups"] if s["page"] == p["key"]]
            out += [f'    <h3>{_esc(p["title"])}</h3>', '    <div class="scp-grid">']
            for s in mine:
                nm = " › ".join(s["heading"])
                tag = Wd["cleared_before"].format(n=s["cleared_before"]) if s["cleared_before"] else ""
                out.append(f'    <div class="scp-node" data-board="{_esc(s["id"])}"><h4 class="scp-name">{_esc(nm)}</h4>'
                           f'{board_svg(self._setup_rows(tr, s["id"]), nm, RT.PIECE_CLASS)}'
                           f'<p class="scp-tag">{_esc(Wd["lines"].format(n=s["lines"]))}'
                           f'{"；" + _esc(tag) if tag else ""}</p>'
                           f'<p class="scp-count">{count.get(s["id"], 0)}</p></div>')
            out.append("    </div>")
        out += ["  </section>"]

        # 5. the case index
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["cases"])}</h2>', f'    <p>{_esc(S["cases_note"])}</p>',
                '    <div class="scp-index-wrap"><table class="scp-table">',
                "    <tr>" + "".join(f"<th>{_esc(T[k])}</th>" for k in
                                     ("case", "pc_lines", "pc_lock", "t_lock", "spin", "garbage", "verified", "setup", "next_pc"))
                + "</tr>"]
        for c in art["cases"]:
            href = rp.replay_href(c)
            setup = (Wd["unmatched"] if c["outcome"] != "matched"
                     else c["setups"][0] + (Wd["mirrored"] if c["mirrored"] else ""))
            spin = f'{Wd[c["spin"]]} {Wd["lines"].format(n=c["lines"])}'
            out.append(f'    <tr data-case="{_esc(case_key(c))}"><td><a href="{_esc(href)}">{_esc(case_key(c))}</a></td>'
                       f'<td>{c["pc_lines"]}</td><td>{c["pc_lock"] + 1}</td><td>{c["lock"] + 1}</td><td>{_esc(spin)}</td>'
                       f'<td>{c["garbage_rows"]}</td><td>{Wd["yes"] if c["verified"] else Wd["no"]}</td>'
                       f'<td>{_esc(setup)}</td><td>{Wd["none"] if c["next_pc"] is None else c["next_pc"] + 1}</td></tr>')
        out += ["    </table></div>", "  </section>"]
        out += RT._tail({"figures": fig})
        return "\n".join(out)

    # ------------------------------------------------------------ the audit

    def audit(self, page, tr, art, repo=REPO):
        bad = RP.audit_quarantine(page, self.REQUIRED, DATA_ID)
        if set(page) & SIMPLIFIED:
            bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
        vis = RT._visible(page)
        if "%" in re.sub(r"<[^>]+>", "", re.sub(r'<q class="scp-src">.*?</q>', "", vis, flags=re.S)):
            bad.append("a % outside quoted source text — this page prints counts, never computed rates")
        if sorted(_BOARD.findall(page)) != sorted(s["id"] for s in tr["setups"]):
            bad.append("the page does not draw every setup exactly once")
        if sorted(html.unescape(c) for c in _CASE.findall(page)) != sorted(case_key(c) for c in art["cases"]):
            bad.append("the case index does not list every case exactly once")
        figs = {}
        for k, v in _FIGURE.findall(page):
            if k in figs:
                bad.append(f"figure {k} printed twice")
            figs[k] = html.unescape(v)
        rc = self.recount(art)
        if figs != rc:
            bad.append(f"the printed figures are not the artefact's, recounted: "
                       f"{sorted(k for k in set(figs) | set(rc) if figs.get(k) != rc.get(k))[:4]}")
        a = art["pc_anchor"]
        if a["disagree"] or a["rounds_agree"] != a["rounds"]:
            bad.append("the anchor disagrees, and the page would print cases from PCs the game did not count")
        bad += self.audit_links(page, art, repo)
        return bad

    @staticmethod
    def audit_links(page, art, repo=REPO):
        bad = []
        rp = Replays(repo)
        cases = {case_key(c): c for c in art["cases"]}
        links = _CASE_LINK.findall(page)
        for ck, href in links:
            ck, href = html.unescape(ck), html.unescape(href)
            c, m = cases.get(ck), _REPLAY_HREF.match(href)
            if c is None or not m or m.group(1) != c["session"] or m.group(2) != f'm{c["match"]}r{c["round"]}':
                bad.append(f"{ck}: the case link {href!r} is not this case's replay round")
                continue
            r = rp._replay_round(c["session"], c["file"], c["round_index0"])
            n = int(m.group(3))
            if n >= len(r["order"]):
                bad.append(f"{ck}: position {n} is past the round")
                continue
            slot = r["order"][n]
            k = r["order"][:n].count(slot)
            user = r["users"][int(slot)]
            piece, cleared, spin = r["locks"][user][k]
            if user != c["player"] or k != c["lock"] or piece != "T" or spin != SPIN_CODE[c["spin"]] or cleared != c["lines"]:
                bad.append(f"{ck}: position {n} steps into {user}'s lock {k} ({piece}, spin {spin}, {cleared} lines), "
                           "not the case's T")
        if len(links) != len(_CASE.findall(page)):
            bad.append("a case row carries no replay link")
        return bad

    def render_all(self, repo=REPO, inputs=None):
        tr, art = inputs or self.load_inputs(repo)
        page = self.render(tr, art, repo)
        bad = self.audit(page, tr, art, repo)
        _need(not bad, "; ".join(bad))
        return {OVERVIEW: page}

    # ------------------------------------------------------------ selftest

    def selftest(self, repo=REPO):
        tr, art = self.load_inputs(repo)
        page = self.render(tr, art, repo)
        survived = killed = 0

        def expect(label, bad, want):
            nonlocal survived, killed
            if bool(bad) == want:
                killed += want
                print(f'  {"killed" if want else "passed"}: {label}')
            else:
                survived += 1
                print(f'  {"SURVIVED" if want else "FAILED control"}: {label} {bad[:2]}', file=sys.stderr)

        expect("the rendered page (control)", self.audit(page, tr, art, repo), False)
        expect("a quarantine sentence deleted", self.audit(page.replace(self.PROSE["page_sentences"][0], ""), tr, art, repo), True)
        expect("a badge planted", self.audit(page.replace("</h1>", '<span data-claim="C001">✓</span></h1>', 1), tr, art, repo), True)
        m = _FIGURE.search(page)
        expect("a figure edited", self.audit(page[:m.start(2)] + str(int(m.group(2).split("/")[0]) + 1)
                                             + page[m.end(2):], tr, art, repo), True)
        first = _BOARD.search(page)
        expect("a setup drawn twice", self.audit(page.replace(first.group(0), first.group(0) + " " + first.group(0), 1),
                                                 tr, art, repo), True)
        row = re.search(r'    <tr data-case="[^"]+">.*?</tr>\n', page)
        expect("a case row dropped", self.audit(page.replace(row.group(0), "", 1), tr, art, repo), True)
        lk = re.search(r'@p(\d+)"', page)
        expect("a case link one position late",
               self.audit(page[:lk.start(1)] + str(int(lk.group(1)) + 1) + page[lk.end(1):], tr, art, repo), True)
        expect("a computed rate printed", self.audit(page.replace("</h1>", "<p>27%</p></h1>", 1), tr, art, repo), True)
        expect("a simplified glyph", self.audit(page.replace("</h1>", "<p>实</p></h1>", 1), tr, art, repo), True)
        bad_art = json.loads(json.dumps(art))
        bad_art["pc_anchor"]["disagree"] = ["planted"]
        expect("the anchor disagreeing", self.audit(page, tr, bad_art, repo), True)
        print(f"selftest: {killed} killed, {survived} survived")
        return 1 if survived else 0


def site_card(site, art):
    card = site.PROSE["index_card"]
    return {"href": OVERVIEW, "cases": len(art["cases"]), "kicker": card["kicker"],
            "title": site.PROSE["overview_title"], "blurb": card["blurb"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    site = DpcSite()
    if a.selftest:
        return site.selftest()
    pages = site.render_all()
    d = a.out_dir or os.path.join(REPO, "docs")
    for name, page in pages.items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(page)
        print(f"wrote {os.path.join(d, name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

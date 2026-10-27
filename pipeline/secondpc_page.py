"""第二次全消 — the page for harddrop's Second Perfect Clear setups against the corpus: `docs/secondpc.html`,
audited before it is returned.

    python3 -m pipeline.secondpc_page --out-dir /tmp/spc   # render it somewhere other than docs/
    python3 -m pipeline.secondpc_page --selftest           # the audit's mutants

Inputs, all committed: the setups transcription (`pipeline/openers/secondpc-setups.json`, gated by
`extract_secondpc_setups`) and the corpus artefact (`analysis/secondpc-facts.json`, from
`pipeline/sim/secondpc-facts.ts`). Pure Python, so `bin/build-docs` renders it in the `docs` job, beside the
DPC page and in the same loop shape: not a route page and not a technique page (`pipeline.sites` lists
neither), because a second PC is a whole layout from empty after a Perfect Clear. It imports the shared
pieces and edits none of them (`board_svg`, the page CSS, the tail, the DPC page's replay-position reader).

QUARANTINE, the technique pages' tier: no claim ids, no ✓, no `data-claim`, the artefact must say
`report_eligible: false`. The audit reuses `replay_page.audit_quarantine` and adds:

* every setup and every solution in the transcription is drawn exactly once (`data-board`), and every case
  is indexed exactly once;
* every printed figure (`data-figure`) is RECOUNTED from the case list and the per-player tallies;
* every case link is read back from the replay side: the position's next step is the case player's lock at
  the case's first lock;
* the anchor is printed with the artefact's agreement, and the page refuses to render if any player-round
  disagrees;
* no `%` outside quoted source text, no simplified glyph.

FIGURES. Counts only; no rate is computed.
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
from pipeline.claims.build_claims import SIMPLIFIED
from pipeline.dpc_page import Replays

HERE, REPO = RT.HERE, RT.REPO
_esc, board_svg, DATA_ID = RT._esc, RT.board_svg, RT.DATA_ID
PREFIX = "secondpc"
OVERVIEW = "secondpc.html"
SETUPS_REL = "pipeline/openers/secondpc-setups.json"
ARTEFACT_REL = "analysis/secondpc-facts.json"
PROSE_PATH = os.path.join(HERE, "secondpc_prose.json")
OUTCOMES = ("solution", "setup", "unmatched")

_FIGURE = re.compile(r'data-figure="([^"]+)">([^<]*)<')
_BOARD = re.compile(r'data-board="([^"]+)"')
_CASE = re.compile(r'data-case="([^"]+)"')
_CASE_LINK = re.compile(r'<tr data-case="([^"]+)">.*?<a href="([^"]+)">')
_REPLAY_HREF = re.compile(r'^(\d{4}-\d{2}-\d{2})-replay\.html#(m\d+r\d+)@p(\d+)$')


def _need(cond, msg):
    if not cond:
        raise ValueError(f"secondpc page: {msg}")


def case_key(c):
    return f'{c["session"]} m{c["match"]}r{c["round"]} {c["player"]} @{c["pc_lock"]}'


def load_prose(path=PROSE_PATH):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    _need(not (set(text) & SIMPLIFIED), f"the prose carries simplified glyph(s) {sorted(set(text) & SIMPLIFIED)}")
    return json.loads(text)


def draw_rows(rows):
    """A transcribed or corpus board for `board_svg`: empty '-', the page's grey (G, the setup's cells drawn
    without their colours) 'c', a piece letter (either case) its piece."""
    body = list(rows)
    while body and body[0] == "." * 10:
        body.pop(0)
    return ["".join("-" if ch == "." else "c" if ch == "G" else ch.lower() for ch in r) for r in body]


class SecondPcSite:
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

    @staticmethod
    def recount(art):
        out = {}
        for u in sorted(art["by_player"]):
            mine = [c for c in art["cases"] if c["player"] == u]
            p = art["by_player"][u]
            for k in ("pc_points", "no_next_pc", "other_lines", "garbage"):
                out[f"{k}.{u}"] = str(p[k])
            out[f"cases.{u}"] = str(len(mine))
            out[f"cases_v.{u}"] = str(sum(1 for c in mine if c["verified"]))
            for o in OUTCOMES:
                out[f"{o}.{u}"] = str(sum(1 for c in mine if c["outcome"] == o))
        a = art["pc_anchor"]
        out["anchor"] = f'{a["rounds_agree"]}/{a["rounds"]}/{a["pcs_replay"]}'
        return out

    def render(self, tr, art, repo=REPO):
        PR, S, T, Wd = self.PROSE, self.PROSE["sections"], self.PROSE["table"], self.PROSE["words"]
        fig = self.recount(art)
        users = sorted(art["by_player"])
        rp = Replays(repo)
        boards = {b["id"]: b for b in tr["boards"]}
        title = f'{PR["title"]}{RS.TITLE_MARK}'
        css = [RP._tokens_css(), RP.BASE_CSS.strip("\n"), RT.PAGE_CSS.strip("\n")]
        p0 = tr["pages"][0]
        out = ["<!doctype html>", '<html lang="zh-HK">', "<head>", '<meta charset="utf-8">',
               '<meta name="viewport" content="width=device-width, initial-scale=1">',
               f"<title>{_esc(title)}</title>", f'<meta name="description" content="{_esc(PR["desc"])}">',
               "<style>", "  " + "\n".join(css), "</style>", "</head>", "<body>", '<div class="wrap-wide">',
               '  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a></nav>',
               '  <header class="scp-head">', f'    <div class="eyebrow">{RS.EYEBROW}</div>',
               f'    <h1 class="section-title">{_esc(title)}</h1>', f'    <p>{_esc(PR["lede"])}</p>',
               f'    <p class="scp-src-line">{_esc(PR["source_words"])}'
               f'<a href="{_esc(p0["url"])}">{_esc(p0["title"])}</a>'
               f'（<a href="https://harddrop.com/w/index.php?oldid={p0["oldid"]}">revision {p0["oldid"]}</a>）。'
               f'{_esc(PR["source_terms"])}</p>',
               f'    <p>{_esc(PR["definition_intro"])}<q class="scp-src">{_esc(tr["source"]["definition"])}</q></p>']
        dec = tr["source"]["declined"][0]
        out += [f'    <p>{_esc(PR["declined"].split("{link}")[0])}<a href="{_esc(dec["url"])}">{_esc(dec["title"])}</a>'
                f'{_esc(PR["declined"].split("{link}")[1])}</p>', "  </header>", '  <div class="method-note">',
                '    <p><strong>呢版唔屬於信任鏈。</strong>每個盤面都係<strong>一個 replay 模擬器</strong>'
                '（Triangle 引擎）重跑操作記錄推導出嚟，冇第二份獨立實作；十粒方塊點擺亦係由佢推出嚟。'
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
                "    <tr>" + "".join(f"<th>{_esc(T[k])}</th>" for k in
                                     ("player", "pc_points", "no_next_pc", "other_lines", "garbage", "cases",
                                      "solution", "setup", "unmatched")) + "</tr>"]
        for u in users:
            cells = "".join(f'<td data-figure="{k}.{u}">{fig[f"{k}.{u}"]}</td>'
                            for k in ("pc_points", "no_next_pc", "other_lines", "garbage"))
            cases = (f'<td><span data-figure="cases.{u}">{fig[f"cases.{u}"]}</span><span class="scp-tag">'
                     f'{_esc(T["verified_suffix"].split("{v}")[0])}<span data-figure="cases_v.{u}">{fig[f"cases_v.{u}"]}</span>'
                     f'{_esc(T["verified_suffix"].split("{v}")[1])}</span></td>')
            outc = "".join(f'<td data-figure="{o}.{u}">{fig[f"{o}.{u}"]}</td>' for o in OUTCOMES)
            out.append(f"    <tr><td>{_esc(u)}</td>{cells}{cases}{outc}</tr>")
        out += ["    </table></div>", "  </section>"]

        # 2. the cases, each drawn
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["cases"])}</h2>', f'    <p>{_esc(S["cases_note"])}</p>',
                '    <div class="scp-grid">']
        for c in art["cases"]:
            what = Wd[c["outcome"]] + (" " + "、".join(c["solutions"] or c["setups"]) if c["setups"] else "")
            out.append(f'    <div class="scp-node"><h4 class="scp-name">{_esc(case_key(c))}</h4>'
                       f'{board_svg(draw_rows(c["layout"]), case_key(c), RT.PIECE_CLASS)}'
                       f'<p class="scp-tag">{_esc(what)}</p></div>')
        out += ["    </div>", '    <div class="scp-index-wrap"><table class="scp-table">',
                "    <tr>" + "".join(f"<th>{_esc(T[k])}</th>" for k in
                                     ("case", "prev_pc_lines", "pieces_before", "pc_lock", "verified", "outcome")) + "</tr>"]
        for c in art["cases"]:
            href = rp.replay_href({**c, "lock": c["first_lock"]})
            out.append(f'    <tr data-case="{_esc(case_key(c))}"><td><a href="{_esc(href)}">{_esc(case_key(c))}</a></td>'
                       f'<td>{c["prev_pc_lines"]}</td><td>{c["pieces_before"]}</td><td>{c["pc_lock"] + 1}</td>'
                       f'<td>{Wd["yes"] if c["verified"] else Wd["no"]}</td><td>{_esc(Wd[c["outcome"]])}</td></tr>')
        out += ["    </table></div>", "  </section>"]

        # 3. every setup with its solutions
        count = {}
        for c in art["cases"]:
            for sid in c["setups"]:
                count[sid] = count.get(sid, 0) + 1
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["setups"])}</h2>',
                f'    <p class="scp-quote">{_esc(S["setups_note"])}</p>']
        for s in tr["setups"]:
            nm = " › ".join(s["heading"])
            out += [f'    <h3>{_esc(nm)}</h3>', '    <div class="scp-grid">',
                    f'    <div class="scp-node" data-board="{_esc(s["id"])}"><h4 class="scp-name">{_esc(Wd["setup_name"])}</h4>'
                    f'{board_svg(draw_rows(s["rows"]), nm, RT.PIECE_CLASS)}'
                    f'<p class="scp-tag">{_esc(Wd["pieces"].format(p=s["pieces"]))}</p>'
                    f'<p class="scp-count">{count.get(s["id"], 0)}</p></div>']
            for i, sol in enumerate(s["solutions"]):
                out.append(f'    <div class="scp-node" data-board="{_esc(sol)}"><h4 class="scp-name">'
                           f'{_esc(Wd["solution_name"].format(n=i + 1))}</h4>'
                           f'{board_svg(draw_rows(boards[sol]["rows"]), f"{nm} {i + 1}", RT.PIECE_CLASS)}</div>')
            if not s["solutions"]:
                out.append(f'    <p class="scp-tag">{_esc(Wd["no_solution"])}</p>')
            out.append("    </div>")
        out += ["  </section>"]
        out += RT._tail({"figures": fig})
        return "\n".join(out)

    def audit(self, page, tr, art, repo=REPO):
        bad = RP.audit_quarantine(page, self.REQUIRED, DATA_ID)
        if set(page) & SIMPLIFIED:
            bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
        vis = RT._visible(page)
        if "%" in re.sub(r"<[^>]+>", "", re.sub(r'<q class="scp-src">.*?</q>', "", vis, flags=re.S)):
            bad.append("a % outside quoted source text — this page prints counts, never computed rates")
        want = sorted([s["id"] for s in tr["setups"]] + [x for s in tr["setups"] for x in s["solutions"]])
        if sorted(_BOARD.findall(page)) != want:
            bad.append("the page does not draw every setup and solution exactly once")
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
            if user != c["player"] or k != c["first_lock"]:
                bad.append(f"{ck}: position {n} steps into {user}'s lock {k}, not the case's first piece")
        if len(links) != len(_CASE.findall(page)):
            bad.append("a case row carries no replay link")
        return bad

    def render_all(self, repo=REPO, inputs=None):
        tr, art = inputs or self.load_inputs(repo)
        page = self.render(tr, art, repo)
        bad = self.audit(page, tr, art, repo)
        _need(not bad, "; ".join(bad))
        return {OVERVIEW: page}

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
        expect("a quarantine sentence deleted",
               self.audit(page.replace(self.PROSE["page_sentences"][0], ""), tr, art, repo), True)
        expect("a badge planted", self.audit(page.replace("</h1>", '<span data-claim="C001">✓</span></h1>', 1), tr, art, repo), True)
        m = re.search(r'data-figure="pc_points\.[^"]+">(\d+)<', page)
        expect("a figure edited", self.audit(page[:m.start(1)] + str(int(m.group(1)) + 1) + page[m.end(1):], tr, art, repo), True)
        first = _BOARD.search(page)
        expect("a setup drawn twice", self.audit(page.replace(first.group(0), first.group(0) + " " + first.group(0), 1),
                                                 tr, art, repo), True)
        sol = next(x for s in tr["setups"] for x in s["solutions"])
        expect("a solution not drawn", self.audit(page.replace(f'data-board="{sol}"', 'data-board="none"', 1), tr, art, repo), True)
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
    site = SecondPcSite()
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

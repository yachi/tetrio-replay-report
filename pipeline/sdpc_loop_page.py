"""SDPC 循環 — JayKob's SDPC loop video, read against the boards this repo already transcribes: `docs/sdpc-loop.html`.

    python3 -m pipeline.sdpc_loop_page --out-dir /tmp/sdpc   # render it somewhere other than docs/
    python3 -m pipeline.sdpc_loop_page --selftest            # the audit's mutants

Inputs, all committed: the video read (`pipeline/openers/sdpc-loop.json`, gated by
`pipeline.openers.check_sdpc_loop`), stick spin's route transcription and corpus artefact, and the DPC
setups transcription and corpus artefact. The loop adds NO board of its own: its two halves are stick spin's
SDパフェ route and the くるまDPC setup, drawn from those transcriptions, so a board here cannot drift from
the page it belongs to.

VIDEO TIER, quarantined like the DPC page: no claim ids, no ✓, no `data-claim`; the video data is in no count.
The audit reuses `replay_page.audit_quarantine` and adds:

* every board of the loop is drawn exactly once (`data-board`), every Perfect Clear has exactly one row
  (`data-pc`), and every read is linked once, at its own time;
* every printed figure (`data-figure`) is RECOUNTED from the read and the two artefacts;
* the gate's checks pass on the read the page is rendered from;
* no `%` outside quoted source text, no simplified glyph.
"""
import argparse
import html
import json
import os
import re
import sys

from pipeline import dpc_page as DP
from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline import route_page as RT
from pipeline.claims.build_claims import SIMPLIFIED
from pipeline.openers import check_sdpc_loop as CL

HERE, REPO = RT.HERE, RT.REPO
_esc, board_svg, DATA_ID = RT._esc, RT.board_svg, RT.DATA_ID
PREFIX = "sdpc-loop"
OVERVIEW = "sdpc-loop.html"
PROSE_PATH = os.path.join(HERE, "sdpc_loop_prose.json")
STICKSPIN_ART = "analysis/stickspin-facts.json"
DPC_ART = "analysis/dpc-facts.json"
LEAD = 3

_FIGURE = re.compile(r'data-figure="([^"]+)">([^<]*)<')
_BOARD = re.compile(r'data-board="([^"]+)"')
_PC = re.compile(r'data-pc="(\d+)"')
_READ = re.compile(r'<a data-read="(\d+)" href="([^"]+)">')


def _need(cond, msg):
    if not cond:
        raise ValueError(f"sdpc loop page: {msg}")


def _mmss(t):
    t = int(t)
    return f"{t // 60}:{t % 60:02d}"


def video_href(d, t):
    return f'{d["source"]["url"]}&t={max(0, int(t - LEAD))}s'


def load_prose(path=PROSE_PATH):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    _need(not (set(text) & SIMPLIFIED), f"the prose carries simplified glyph(s) {sorted(set(text) & SIMPLIFIED)}")
    return json.loads(text)


class SdpcLoopSite:
    def __init__(self, prose_path=PROSE_PATH):
        self.PROSE = load_prose(prose_path)
        self.OVERVIEW = OVERVIEW
        self.REQUIRED = (RS.EYEBROW, RS.TITLE_MARK, RS.NO_CLAIM, *self.PROSE["page_sentences"])

    def load_inputs(self, repo=REPO):
        d = CL.load()
        st, dp = CL.transcriptions()
        bad = CL.check(d, st, dp)
        _need(not bad, f"the video read fails its gate: {bad[:2]}")
        with open(os.path.join(repo, STICKSPIN_ART), encoding="utf-8") as f:
            sa = json.load(f)
        with open(os.path.join(repo, DPC_ART), encoding="utf-8") as f:
            da = json.load(f)
        _need(sa.get("report_eligible") is False and da.get("report_eligible") is False,
              "a corpus artefact is not marked report_eligible: false")
        return d, st, dp, sa, da

    # ------------------------------------------------------------ figures

    @staticmethod
    def recount(d, sa, da):
        out = {}
        h = CL.halves(d)
        n = len(d["pcs"]["t"])
        out["pcs"] = str(n)
        out["sdpc"] = str(sum(1 for v in h.values() if v == "sdpc"))
        out["dpc"] = str(sum(1 for v in h.values() if v == "dpc"))
        out["unread"] = str(sum(1 for s in range(n) if s not in h))
        out["laps"] = str(len(CL.laps(d)))
        for c in sa["cases"]:
            k = f'sd.{c["deepest"]}'
            out[k] = str(int(out.get(k, "0")) + 1)
        out["sd.cases"] = str(len(sa["cases"]))
        out["sd.reached_2"] = str(sum(1 for c in sa["cases"] if not c["deepest"].startswith("bag1")))
        setup = d["loop"]["dpc"]["setup"]
        for u in sorted(da["by_player"]):
            out[f"dpc.{u}"] = str(sum(1 for c in da["cases"] if c["player"] == u and c["outcome"] == "matched"
                                      and c["setups"][0] == setup))
        return out

    # ------------------------------------------------------------ boards

    @staticmethod
    def stick_rows(st, nid):
        return [n for n in st["nodes"] if n["id"] == nid][0]["rows"]

    def board_name(self, st, dp, board):
        k, ident = board.split(":", 1)
        if board in self.PROSE["board_names"]:
            return self.PROSE["board_names"][board]
        if k == "stickspin":
            n = [n for n in st["nodes"] if n["id"] == ident][0]
            return n.get("label_jp") or n["label"]
        base = ident.split("+")[0]
        s = [s for s in dp["setups"] if s["id"] == base][0]
        return " · ".join(s["heading"]) + ("＋T" if ident.endswith("+T") else "")

    # ------------------------------------------------------------ the page

    def render(self, d, st, dp, sa, da):
        PR, S, T, W = self.PROSE, self.PROSE["sections"], self.PROSE["table"], self.PROSE["words"]
        fig = self.recount(d, sa, da)
        src = d["source"]
        title = f'{PR["title"]}{RS.TITLE_MARK}'
        css = [RP._tokens_css(), RP.BASE_CSS.strip("\n"), RT.PAGE_CSS.strip("\n"),
               ".sl-row { display: grid; grid-template-columns: repeat(auto-fill, minmax(10rem, 1fr)); gap: .6rem; }"]
        out = ["<!doctype html>", '<html lang="zh-HK">', "<head>", '<meta charset="utf-8">',
               '<meta name="viewport" content="width=device-width, initial-scale=1">',
               f"<title>{_esc(title)}</title>", f'<meta name="description" content="{_esc(PR["desc"])}">',
               "<style>", "  " + "\n".join(css), "</style>", "</head>", "<body>", '<div class="wrap-wide">',
               '  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a></nav>',
               '  <header class="scp-head">', f'    <div class="eyebrow">{RS.EYEBROW}</div>',
               f'    <h1 class="section-title">{_esc(title)}</h1>', f'    <p>{_esc(PR["lede"])}</p>',
               f'    <p class="scp-src-line">{_esc(PR["source_words"])}<a href="{_esc(src["url"])}">'
               f'{_esc(src["channel"])}「{_esc(src["title"])}」</a>（YouTube）。{_esc(PR["source_terms"])}</p>',
               "  </header>", '  <div class="method-note">',
               f'    <p>呢版<strong>{RS.NO_CLAIM}</strong>。</p>']
        out += [f"    <p>{s}</p>" for s in PR["page_sentences"]]
        out += ["  </div>"]

        # 1. the loop, from the two transcriptions
        setup = d["loop"]["dpc"]["setup"]
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["loop"])}</h2>', f'    <p>{_esc(S["loop_note"])}</p>',
                f'    <h3><a href="stickspin.html">{_esc(W["sdpc"])}</a>（{_esc(W["sd_page"])}）</h3>', '    <div class="sl-row">']
        for nid in d["loop"]["sdpc"]["stickspin"]:
            nm = self.board_name(st, dp, f"stickspin:{nid}")
            out.append(f'    <div class="scp-node" data-board="stickspin:{_esc(nid)}"><h4 class="scp-name">{_esc(nm)}</h4>'
                       f'{board_svg(self.stick_rows(st, nid), nm, RT.PIECE_CLASS)}</div>')
        nm = self.board_name(st, dp, f"dpc:{setup}")
        out += ["    </div>", f'    <h3><a href="dpc.html">{_esc(W["dpc"])}</a>（{_esc(W["dpc_page"])}）</h3>', '    <div class="sl-row">',
                f'    <div class="scp-node" data-board="dpc:{_esc(setup)}"><h4 class="scp-name">{_esc(nm)}</h4>'
                f'{board_svg(DP.DpcSite._setup_rows(dp, setup), nm, RT.PIECE_CLASS)}</div>', "    </div>"]
        sd, dc, sl, dl, _ = CL.loop_arithmetic(d, st, dp)
        s0 = [s for s in dp["setups"] if s["id"] == setup][0]
        out += [f'    <h3>{_esc(S["arith"])}</h3>',
                f'    <p>{_esc(W["arith"].format(pc=sl - CL.SPIN_LINES["TSS"] - CL.SPIN_LINES["TSD"], sl=sl, sd=sd, tsd=s0["lines"], dpc_pc=dl - s0["lines"], dl=dl, dc=dc, total=sd + dc, bags=(sd + dc) // 7))}</p>',
                "  </section>"]

        # 2. the video, Perfect Clear by Perfect Clear
        h = CL.halves(d)
        by_seg = {}
        for i, r in enumerate(d["reads"]):
            by_seg.setdefault(r["segment"], []).append((i, r))
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["video"])}</h2>', f'    <p>{_esc(S["video_note"])}</p>',
                "    <p>" + _esc(W["counts"]).format(pcs=f'<span data-figure="pcs">{fig["pcs"]}</span>') + "</p>",
                '    <div class="scp-index-wrap"><table class="scp-table">',
                f'    <tr><th>{_esc(W["sdpc"])}</th><th>{_esc(W["dpc"])}</th><th>{_esc(W["unread"])}</th><th>{_esc(W["laps"])}</th></tr>',
                f'    <tr><td data-figure="sdpc">{fig["sdpc"]}</td><td data-figure="dpc">{fig["dpc"]}</td>'
                f'<td data-figure="unread">{fig["unread"]}</td><td data-figure="laps">{fig["laps"]}</td></tr>',
                "    </table></div>",
                '    <div class="scp-index-wrap"><table class="scp-table">',
                "    <tr>" + "".join(f"<th>{_esc(T[k])}</th>" for k in ("n", "t", "half", "reads")) + "</tr>"]
        for s, t in enumerate(d["pcs"]["t"]):
            reads = []
            for i, r in by_seg.get(s, []):
                rt = r["frame"] / 60
                nm = self.board_name(st, dp, r["board"]) + (W["mirrored"] if r["mirrored"] else "")
                reads.append(f'<a data-read="{i}" href="{_esc(video_href(d, rt))}">{_mmss(rt)} {_esc(nm)}</a>')
            half = W[h[s]] if s in h else W["unread"]
            out.append(f'    <tr data-pc="{s}"><td>{s + 1}</td><td><a href="{_esc(video_href(d, t))}">▶ {_mmss(t)}</a></td>'
                       f'<td>{_esc(half)}</td><td>{"<br>".join(reads) or "—"}</td></tr>')
        end = d["source"]["end"]
        out += ["    </table></div>",
                f'    <p>{_esc(W["end"])}<q class="scp-src">{_esc(" / ".join(end["quote"]))}</q>'
                f'（<a href="{_esc(video_href(d, end["t"]))}">{_mmss(end["t"])}</a>）</p>', "  </section>"]

        # 3. the corpus
        order = ("bag1.left", "bag1.pc", "2.sd", "2.sd.after")
        deep = "、".join(f'{_esc(self.board_name(st, dp, "stickspin:" + k))}：<span data-figure="sd.{k}">{fig[f"sd.{k}"]}</span>'
                        for k in order if f"sd.{k}" in fig)
        tail = W["corpus_sd_tail"] if fig["sd.reached_2"] == "0" else ""
        dpcs = "、".join(f'{_esc(u)}：<span data-figure="dpc.{u}">{fig[f"dpc.{u}"]}</span>' for u in sorted(da["by_player"]))
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["corpus"])}</h2>', f'    <p>{_esc(S["corpus_note"])}</p>',
                f'    <p>{_esc(W["corpus_sd"])}{deep}（共 <span data-figure="sd.cases">{fig["sd.cases"]}</span> 個 case）。'
                f'{_esc(W["corpus_sd_reached"])}<span data-figure="sd.reached_2">{fig["sd.reached_2"]}</span>。{_esc(tail)}</p>',
                f'    <p>{_esc(W["corpus_dpc"])}{dpcs}。</p>', "  </section>"]
        out += RT._tail({"figures": fig})
        return "\n".join(out)

    # ------------------------------------------------------------ the audit

    def audit(self, page, d, st, dp, sa, da):
        bad = RP.audit_quarantine(page, self.REQUIRED, DATA_ID)
        if set(page) & SIMPLIFIED:
            bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
        vis = RT._visible(page)
        if "%" in re.sub(r"<[^>]+>", "", re.sub(r'<q class="scp-src">.*?</q>', "", vis, flags=re.S)):
            bad.append("a % outside quoted source text — this page prints counts, never computed rates")
        want = sorted([f"stickspin:{k}" for k in d["loop"]["sdpc"]["stickspin"]] + [f'dpc:{d["loop"]["dpc"]["setup"]}'])
        if sorted(_BOARD.findall(page)) != want:
            bad.append("the page does not draw every board of the loop exactly once")
        if sorted(int(x) for x in _PC.findall(page)) != list(range(len(d["pcs"]["t"]))):
            bad.append("the page does not list every Perfect Clear exactly once")
        links = _READ.findall(page)
        if sorted(int(i) for i, _ in links) != list(range(len(d["reads"]))):
            bad.append("the page does not link every read exactly once")
        for i, href in links:
            r = d["reads"][int(i)]
            if html.unescape(href) != video_href(d, r["frame"] / 60):
                bad.append(f"read {i}: its link is not at its own time")
        figs = {}
        for k, v in _FIGURE.findall(page):
            if k in figs:
                bad.append(f"figure {k} printed twice")
            figs[k] = html.unescape(v)
        rc = self.recount(d, sa, da)
        if figs != rc:
            bad.append(f"the printed figures are not recounted: {sorted(k for k in set(figs) | set(rc) if figs.get(k) != rc.get(k))[:4]}")
        bad += [f"gate: {b}" for b in CL.check(d, st, dp)]
        return bad

    def render_all(self, repo=REPO, inputs=None):
        inp = inputs or self.load_inputs(repo)
        page = self.render(*inp)
        bad = self.audit(page, *inp)
        _need(not bad, "; ".join(bad))
        return {OVERVIEW: page}

    # ------------------------------------------------------------ selftest

    def selftest(self, repo=REPO):
        inp = self.load_inputs(repo)
        d = inp[0]
        page = self.render(*inp)
        survived = killed = 0

        def expect(label, bad, want):
            nonlocal survived, killed
            if bool(bad) == want:
                killed += want
                print(f'  {"killed" if want else "passed"}: {label}')
            else:
                survived += 1
                print(f'  {"SURVIVED" if want else "FAILED control"}: {label} {bad[:2]}', file=sys.stderr)

        expect("the rendered page (control)", self.audit(page, *inp), False)
        expect("a quarantine sentence deleted", self.audit(page.replace(self.PROSE["page_sentences"][0], ""), *inp), True)
        expect("a badge planted", self.audit(page.replace("</h1>", '<span data-claim="C001">✓</span></h1>', 1), *inp), True)
        m = re.search(r'data-figure="laps">(\d+)<', page)
        expect("a figure edited", self.audit(page[:m.start(1)] + str(int(m.group(1)) + 1) + page[m.end(1):], *inp), True)
        b = _BOARD.search(page)
        expect("a loop board drawn twice", self.audit(page.replace(b.group(0), b.group(0) + " " + b.group(0), 1), *inp), True)
        row = re.search(r'    <tr data-pc="\d+">.*?</tr>\n', page)
        expect("a Perfect Clear row dropped", self.audit(page.replace(row.group(0), "", 1), *inp), True)
        lk = re.search(r'data-read="0" href="[^"]*&amp;t=(\d+)s"', page)
        expect("a read linked a second late", self.audit(page[:lk.start(1)] + str(int(lk.group(1)) + 1) + page[lk.end(1):], *inp), True)
        expect("a computed rate printed", self.audit(page.replace("</h1>", "<p>27%</p></h1>", 1), *inp), True)
        expect("a simplified glyph", self.audit(page.replace("</h1>", "<p>实</p></h1>", 1), *inp), True)
        bad_d = json.loads(json.dumps(d))
        bad_d["reads"][0]["segment"] += 3
        expect("a read the gate refuses", self.audit(page, bad_d, *inp[1:]), True)
        print(f"selftest: {killed} killed, {survived} survived")
        return 1 if survived else 0


def site_card(site, inputs):
    card = site.PROSE["index_card"]
    return {"href": OVERVIEW, "cases": len(inputs[0]["pcs"]["t"]), "kicker": card["kicker"],
            "title": site.PROSE["overview_title"], "blurb": card["blurb"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    site = SdpcLoopSite()
    if a.selftest:
        return site.selftest()
    pages = site.render_all()
    d = a.out_dir or os.path.join(REPO, "docs")
    os.makedirs(d, exist_ok=True)
    for name, page in pages.items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(page)
        print(f"wrote {os.path.join(d, name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

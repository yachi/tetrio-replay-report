"""T-Spin Forecast — the 中盤手法 page for every counted T-spin Forecast in the corpus, plus the examples read off
one live video: `docs/forecast.html`, audited before it is returned.

    python3 -m pipeline.forecast_page --out-dir /tmp/fc   # render it somewhere other than docs/
    python3 -m pipeline.forecast_page --selftest          # the audit's mutants

Inputs, all committed: the corpus artefact (`analysis/forecast-events.json`, from
`pipeline/sim/emit-forecast-events.ts`, whose test holds its per-(session, player) counts equal to every
`sessions/*/sim/forecast-facts.json`) and the video read (`pipeline/openers/forecast-video.json`). Pure
Python, so `bin/build-docs` renders it in the DPC / 2nd PC loop: not a route page and not a technique page
(`pipeline.sites` lists neither), because a forecast is a definition over the whole board (forecast.ts), not a
window.

QUARANTINE, the technique pages' tier: no claim ids, no ✓, no `data-claim`, the artefact must say
`report_eligible: false`. The audit reuses `replay_page.audit_quarantine` and adds:

* every event is drawn exactly once (`data-case`), and every video example exactly once (`data-video`);
* every printed figure (`data-figure`) is RECOUNTED from the event list;
* every case link is read back from the replay side: the position's next step is the event player's T lock,
  and that lock (decoded from an empty board) is a T with a full or mini spin clearing the event's lines;
* every video link opens the declared video at the example's own second, a few seconds early;
* no `%`, no simplified glyph.

The video examples are VIDEO TIER: read by eye off a live stream, in no count and no figure.
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
PREFIX = "forecast"
OVERVIEW = "forecast.html"
ARTEFACT_REL = "analysis/forecast-events.json"
VIDEO_REL = "pipeline/openers/forecast-video.json"
PROSE_PATH = os.path.join(HERE, "forecast_prose.json")
SPIN_WORD = {1: "TSS", 2: "TSD", 3: "TST"}

_FIGURE = re.compile(r'data-figure="([^"]+)">([^<]*)<')
_CASE = re.compile(r'data-case="([^"]+)"')
_VIDEO = re.compile(r'data-video="([^"]+)"')
_CASE_LINK = re.compile(r'<tr data-case="([^"]+)">.*?<a href="([^"]+)">')
_VIDEO_LINK = re.compile(r'<tr data-video="([^"]+)">.*?<a class="vx" href="([^"]+)"')
_REPLAY_HREF = re.compile(r'^(\d{4}-\d{2}-\d{2})-replay\.html#(m\d+r\d+)@p(\d+)$')


def _need(cond, msg):
    if not cond:
        raise ValueError(f"forecast page: {msg}")


def case_key(e):
    return f'{e["session"]} m{e["match"]}r{e["round"]} {e["player"]} @{e["lock"]}'


def load_prose(path=PROSE_PATH):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    _need(not (set(text) & SIMPLIFIED), f"the prose carries simplified glyph(s) {sorted(set(text) & SIMPLIFIED)}")
    return json.loads(text)


def video_url(vid, t, lead):
    """The example's moment, `lead` seconds early, floored to a second."""
    return f'https://www.youtube.com/watch?v={vid}&t={max(0, int(t) - lead)}s'


class Replays:
    """The technique pages' replay readers, bound to this page, so a case link and a case board are computed by
    the same rule as theirs."""
    _replay_round = TP.TechniqueSite._replay_round
    _round_boards = TP.TechniqueSite._round_boards
    _rows_of = staticmethod(TP.TechniqueSite._rows_of)
    replay_href = TP.TechniqueSite.replay_href
    video_link = TP.TechniqueSite.video_link

    def __init__(self, repo):
        self._repo = repo

    def _need(self, cond, msg):
        _need(cond, msg)

    def moments(self, e):
        """Three boards: right after the roof lock (the slot built, the T-spin not yet doable), right after the
        line clear that made it doable, and just before the T (its cells dashed)."""
        bs = self._round_boards(e)
        k, roof, mech = e["lock"], e["roof_lock"], e["mechanism_step"]
        _need(roof is not None and mech is not None and roof < mech < k, f"{case_key(e)}: roof, clear and T out of order")
        moments = [(bs[roof][2], set()), (bs[mech][2], set()), (bs[k - 1][2], set(bs[k][1]))]
        top = max([y + 1 for b, _m in moments for y in range(len(b)) if any(v is not None for v in b[y])]
                  + [c // 10 + 1 for _b, m in moments for c in m])
        return [self._rows_of(b, m, top + 1) for b, m in moments]


class ForecastSite:
    def __init__(self, prose_path=PROSE_PATH):
        self.PROSE = load_prose(prose_path)
        self.OVERVIEW = OVERVIEW
        self.REQUIRED = (RS.EYEBROW, RS.TITLE_MARK, RS.NO_CLAIM, *self.PROSE["page_sentences"])

    def load_inputs(self, repo=REPO):
        with open(os.path.join(repo, ARTEFACT_REL), encoding="utf-8") as f:
            art = json.load(f)
        with open(os.path.join(repo, VIDEO_REL), encoding="utf-8") as f:
            vid = json.load(f)
        _need(art.get("report_eligible") is False, "the artefact is not marked report_eligible: false")
        _need(vid.get("report_eligible") is False, "the video read is not marked report_eligible: false")
        return vid, art  # (the read, the artefact): the order build-docs' PC-page loop expects

    @staticmethod
    def recount(art):
        out = {}
        ev = art["events"]
        for u in sorted({e["player"] for e in ev}):
            mine = [e for e in ev if e["player"] == u]
            out[f"events.{u}"] = str(len(mine))
            for n in (1, 2, 3):
                out[f"lines{n}.{u}"] = str(sum(1 for e in mine if e["lines"] == n))
            out[f"sessions.{u}"] = str(len({e["session"] for e in mine}))
        out["events"] = str(len(ev))
        return out

    def render(self, art, vid, repo=REPO):
        PR, S, T, Wd = self.PROSE, self.PROSE["sections"], self.PROSE["table"], self.PROSE["words"]
        fig = self.recount(art)
        users = sorted({e["player"] for e in art["events"]})
        rp = Replays(repo)
        title = f'{PR["title"]}{RS.TITLE_MARK}'
        css = [RP._tokens_css(), RP.BASE_CSS.strip("\n"), RT.PAGE_CSS.strip("\n"),
               ".fc-strip { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .4rem; }",
               ".fc-strip p { font-size: .72rem; color: var(--ink-secondary); margin: 0; }"]
        out = ["<!doctype html>", '<html lang="zh-HK">', "<head>", '<meta charset="utf-8">',
               '<meta name="viewport" content="width=device-width, initial-scale=1">',
               f"<title>{_esc(title)}</title>", f'<meta name="description" content="{_esc(PR["desc"])}">',
               "<style>", "  " + "\n".join(css), "</style>", "</head>", "<body>", '<div class="wrap-wide">',
               '  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a></nav>',
               '  <header class="scp-head">', f'    <div class="eyebrow">{RS.EYEBROW}</div>',
               f'    <h1 class="section-title">{_esc(title)}</h1>', f'    <p>{_esc(PR["lede"])}</p>']
        out += [f"    <p>{_esc(p)}</p>" for p in PR["rule"]]
        out += ["  </header>", '  <div class="method-note">',
                '    <p><strong>呢版唔屬於信任鏈。</strong>每個盤面都係<strong>一個 replay 模擬器</strong>'
                '（Triangle 引擎）重跑操作記錄推導出嚟，冇第二份獨立實作。'
                f'所以呢版<strong>{RS.NO_CLAIM}</strong>。</p>']
        out += [f"    <p>{s}</p>" for s in PR["page_sentences"]]
        out += ["  </div>"]

        # 1. figures
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["figures"])}</h2>',
                f'    <p>{_esc(S["figures_note"])}</p>',
                f'    <p class="scp-count">{_esc(Wd["total"].split("{n}")[0])}<span data-figure="events">{fig["events"]}</span>'
                f'{_esc(Wd["total"].split("{n}")[1])}</p>',
                '    <div class="scp-index-wrap"><table class="scp-table">',
                "    <tr>" + "".join(f"<th>{_esc(T[k])}</th>" for k in
                                     ("player", "events", "lines1", "lines2", "lines3", "sessions")) + "</tr>"]
        for u in users:
            cells = "".join(f'<td data-figure="{k}.{u}">{fig[f"{k}.{u}"]}</td>'
                            for k in ("events", "lines1", "lines2", "lines3", "sessions"))
            out.append(f"    <tr><td>{_esc(u)}</td>{cells}</tr>")
        out += ["    </table></div>", "  </section>"]

        # 2. every corpus event, drawn
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["cases"])}</h2>', f'    <p>{_esc(S["cases_note"])}</p>',
                '    <div class="scp-grid">']
        for e in art["events"]:
            boards = rp.moments(e)
            strip = "".join(f'<div>{board_svg(rows, f"{case_key(e)} {w}", RT.PIECE_CLASS)}<p>{_esc(w)}</p></div>'
                            for rows, w in zip(boards, Wd["moments"]))
            out.append(f'    <div class="scp-node"><h4 class="scp-name">{_esc(case_key(e))}</h4>'
                       f'<div class="fc-strip">{strip}</div>'
                       f'<p class="scp-tag">{_esc(Wd["spin"].format(spin=SPIN_WORD[e["lines"]], gap=e["lock"] - e["roof_lock"]))}</p></div>')
        out += ["    </div>", '    <div class="scp-index-wrap"><table class="scp-table">',
                "    <tr>" + "".join(f"<th>{_esc(T[k])}</th>" for k in
                                     ("case", "spin", "roof_lock", "clear_lock", "t_lock")) + "</tr>"]
        for e in art["events"]:
            href = rp.replay_href(e)
            out.append(f'    <tr data-case="{_esc(case_key(e))}"><td><a href="{_esc(href)}">{_esc(case_key(e))}</a>'
                       f'{rp.video_link(e)}</td><td>{SPIN_WORD[e["lines"]]}</td><td>{e["roof_lock"] + 1}</td>'
                       f'<td>{e["mechanism_step"] + 1}</td><td>{e["lock"] + 1}</td></tr>')
        out += ["    </table></div>", "  </section>"]

        # 3. the live video's examples
        v = vid["video"]
        out += ['  <section class="scp-sec">', f'    <h2>{_esc(S["video"])}</h2>',
                f'    <p>{_esc(S["video_note"].split("{link}")[0])}<a href="{_esc(v["url"])}">{_esc(v["title"])}</a>'
                f'{_esc(S["video_note"].split("{link}")[1])}</p>',
                '    <div class="scp-index-wrap"><table class="scp-table">',
                "    <tr>" + "".join(f"<th>{_esc(T[k])}</th>" for k in ("video_example", "side", "spin", "kind", "note")) + "</tr>"]
        for x in vid["examples"]:
            url = video_url(v["id"], x["clear_s"], vid["link_lead_s"])
            out.append(f'    <tr data-video="{_esc(x["id"])}"><td><a class="vx" href="{_esc(url)}" target="_blank" rel="noopener">'
                       f'▶ {_esc(Wd["clock"].format(t=_clock(x["clear_s"])))}</a></td><td>{_esc(Wd["side_" + x["side"]])}</td>'
                       f'<td>{_esc(x["spin"])}</td><td>{_esc(Wd["kind_" + x["kind"]])}</td><td>{_esc(x["note"])}</td></tr>')
        out += ["    </table></div>", f'    <p class="scp-tag">{_esc(S["video_limit"])}</p>', "  </section>"]
        out += RT._tail({"figures": fig})
        return "\n".join(out)

    def audit(self, page, art, vid, repo=REPO):
        bad = RP.audit_quarantine(page, self.REQUIRED, DATA_ID)
        if set(page) & SIMPLIFIED:
            bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
        if "%" in re.sub(r"<[^>]+>", "", RT._visible(page)):
            bad.append("a % on the page — this page prints counts, never computed rates")
        if sorted(html.unescape(c) for c in _CASE.findall(page)) != sorted(case_key(e) for e in art["events"]):
            bad.append("the case index does not list every event exactly once")
        if sorted(_VIDEO.findall(page)) != sorted(x["id"] for x in vid["examples"]):
            bad.append("the video table does not list every example exactly once")
        figs = {}
        for k, val in _FIGURE.findall(page):
            if k in figs:
                bad.append(f"figure {k} printed twice")
            figs[k] = html.unescape(val)
        rc = self.recount(art)
        if figs != rc:
            bad.append(f"the printed figures are not the artefact's, recounted: "
                       f"{sorted(k for k in set(figs) | set(rc) if figs.get(k) != rc.get(k))[:4]}")
        ex = {x["id"]: x for x in vid["examples"]}
        for xid, href in _VIDEO_LINK.findall(page):
            x = ex.get(xid)
            if x is None or html.unescape(href) != video_url(vid["video"]["id"], x["clear_s"], vid["link_lead_s"]):
                bad.append(f"{xid}: the video link is not the example's own moment")
        if len(_VIDEO_LINK.findall(page)) != len(_VIDEO.findall(page)):
            bad.append("a video row carries no video link")
        bad += self.audit_links(page, art, repo)
        return bad

    @staticmethod
    def audit_links(page, art, repo=REPO):
        bad = []
        rp = Replays(repo)
        events = {case_key(e): e for e in art["events"]}
        links = _CASE_LINK.findall(page)
        for ck, href in links:
            ck, href = html.unescape(ck), html.unescape(href)
            e, m = events.get(ck), _REPLAY_HREF.match(href)
            if e is None or not m or m.group(1) != e["session"] or m.group(2) != f'm{e["match"]}r{e["round"]}':
                bad.append(f"{ck}: the case link {href!r} is not this event's replay round")
                continue
            r = rp._replay_round(e["session"], e["file"], e["round_index0"])
            n = int(m.group(3))
            if n >= len(r["order"]):
                bad.append(f"{ck}: position {n} is past the round")
                continue
            slot = r["order"][n]
            k = r["order"][:n].count(slot)
            user = r["users"][int(slot)]
            if user != e["player"] or k != e["lock"]:
                bad.append(f"{ck}: position {n} steps into {user}'s lock {k}, not the event's T")
                continue
            piece, lines, spin = r["locks"][user][k]
            if piece.lower() != "t" or lines != e["lines"] or spin not in (1, 2):
                bad.append(f"{ck}: that lock is {piece} clearing {lines} (spin {spin}), not the event's T-spin")
        if len(links) != len(_CASE.findall(page)):
            bad.append("a case row carries no replay link")
        return bad

    def render_all(self, repo=REPO, inputs=None):
        vid, art = inputs or self.load_inputs(repo)
        page = self.render(art, vid, repo)
        bad = self.audit(page, art, vid, repo)
        _need(not bad, "; ".join(bad))
        return {OVERVIEW: page}

    def selftest(self, repo=REPO):
        vid, art = self.load_inputs(repo)
        page = self.render(art, vid, repo)
        survived = killed = 0

        def expect(label, bad, want):
            nonlocal survived, killed
            if bool(bad) == want:
                killed += want
                print(f'  {"killed" if want else "passed"}: {label}')
            else:
                survived += 1
                print(f'  {"SURVIVED" if want else "FAILED control"}: {label} {bad[:2]}', file=sys.stderr)

        expect("the rendered page (control)", self.audit(page, art, vid, repo), False)
        expect("a quarantine sentence deleted",
               self.audit(page.replace(self.PROSE["page_sentences"][0], ""), art, vid, repo), True)
        expect("a badge planted", self.audit(page.replace("</h1>", '<span data-claim="C001">✓</span></h1>', 1), art, vid, repo), True)
        m = re.search(r'data-figure="events\.[^"]+">(\d+)<', page)
        expect("a figure edited", self.audit(page[:m.start(1)] + str(int(m.group(1)) + 1) + page[m.end(1):], art, vid, repo), True)
        row = re.search(r'    <tr data-case="[^"]+">.*?</tr>\n', page)
        expect("a case row dropped", self.audit(page.replace(row.group(0), "", 1), art, vid, repo), True)
        lk = re.search(r'@p(\d+)"', page)
        expect("a case link one position early",
               self.audit(page[:lk.start(1)] + str(int(lk.group(1)) - 1) + page[lk.end(1):], art, vid, repo), True)
        vr = re.search(r'    <tr data-video="[^"]+">.*?</tr>\n', page)
        expect("a video row dropped", self.audit(page.replace(vr.group(0), "", 1), art, vid, repo), True)
        vt = re.search(r'<tr data-video="[^"]+">.*?&amp;t=(\d+)s', page)
        expect("a video link a minute late",
               self.audit(page[:vt.start(1)] + str(int(vt.group(1)) + 60) + page[vt.end(1):], art, vid, repo), True)
        expect("a computed rate printed", self.audit(page.replace("</h1>", "<p>27%</p></h1>", 1), art, vid, repo), True)
        expect("a simplified glyph", self.audit(page.replace("</h1>", "<p>实</p></h1>", 1), art, vid, repo), True)
        print(f"selftest: {killed} killed, {survived} survived")
        return 1 if survived else 0


def _clock(s):
    s = int(s)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"


def site_card(site, art):
    card = site.PROSE["index_card"]
    return {"href": OVERVIEW, "cases": len(art["events"]), "kicker": card["kicker"],
            "title": site.PROSE["overview_title"], "blurb": card["blurb"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    site = ForecastSite()
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

"""行錯咗嗰一步 — the corpus page: every night's `sim/pc-miss-facts.json` rolled up into `docs/pc-miss.html`,
audited before it is returned.

    python3 -m pipeline.pc_miss_page --out-dir /tmp/pcm   # render it somewhere other than docs/
    python3 -m pipeline.pc_miss_page --selftest           # the audit's mutants

Inputs, all committed: each session's `sim/pc-miss-facts.json` (`pipeline/sim/pc-miss.ts`), its
`replay-facts.json` and `facts.json` (for the replay links). The night's own section
(`pipeline/pc_miss_section.py`) draws that night's misses; this page counts every night, per player
and category, links each night's section, and draws per player and category the `SHOW` LATEST
misses (by date, then match, round and lock). It reuses the section's cards, CSS and method note, so
the two say one thing.

QUARANTINE, the section's tier: no claim ids, no ✓, no `data-claim`, every artefact must say
`report_eligible: false`. The audit reuses `replay_page.audit_quarantine` and adds:

* every printed figure (`data-figure`) is RECOUNTED from the artefacts;
* every night with an artefact is linked exactly once, to `<date>.html#pc-miss`;
* the examples are exactly the selection rule's, in order (`data-case`);
* every example's replay link is read back from the replay side (`dpc_page.Replays`, the technique
  pages' reader, not the section's `Locator`): the position's next step is the miss player's lock
  `i`, and that lock places the piece the card draws;
* no `%`, no simplified glyph.

FIGURES. Counts only; no rate is computed.
"""
import argparse
import glob
import html
import json
import os
import re
import sys

from pipeline import pc_miss_section as PS
from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline import route_page as RT
from pipeline.claims.build_claims import SIMPLIFIED
from pipeline.dpc_page import Replays

HERE, REPO = RT.HERE, RT.REPO
DATA_ID = RT.DATA_ID
PREFIX = "pc-miss"
OVERVIEW = "pc-miss.html"
TITLE = "行錯咗嗰一步：搞到全消唔到"
DESC = "每晚每個玩家，擺完之後全消由做得到變做唔到嗰一粒，分四類數，再畫例子。模擬器推導，唔屬於信任鏈。"
LATEST_MARKER = "每類畫最近嗰三粒（日子最新、喺嗰晚比賽次序最後）"
KICKER = "全消循環 · PC solver"
BLURB = "擺完之後全消由做得到變做唔到嗰一粒：蓋住窿、疊得太高、揀錯粒、擺錯位，逐晚逐個玩家數。"

_FIGURE = re.compile(r'data-figure="([^"]+)">([^<]*)<')
_NIGHT = re.compile(r'<a data-night="([^"]+)" href="([^"]+)">')
_CASE = re.compile(r'<div class="pm-card" data-case="([^"]+)">.*?<a href="([^"]+)">重播呢一步</a>', re.S)
_HREF = re.compile(r'^(\d{4}-\d{2}-\d{2})-replay\.html#(m\d+r\d+)@p(\d+)$')


def _need(cond, msg):
    if not cond:
        raise ValueError(f"pc-miss page: {msg}")


def load_all(repo=REPO):
    out = []
    for p in sorted(glob.glob(os.path.join(repo, "sessions", "*", PS.FACTS_REL))):
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        _need(d.get("report_eligible") is False, f"{p} is not marked report_eligible: false")
        _need(d["session"] == p.split(os.sep)[-3], f"{p} names session {d['session']}")
        out.append(d)
    _need(out, "no session has a pc-miss artefact")
    return out


def misses(arts):
    """(session, round, kind, miss) for every REPORTED miss, in date then artefact order."""
    out = []
    for d in arts:
        for r in d["rounds"]:
            for w in r["windows"]:
                for m in w["misses"]:
                    if PS.reported(m):
                        _need(m.get("category") in dict((k, 0) for k, _, _ in PS.CATEGORIES),
                              f"{d['session']} m{r['match']} {r['user']} lock {m['i']}: no category")
                        out.append((d["session"], r, w["kind"], m))
    return out


def case_key(s, r, m):
    return f'{s} m{r["match"]}r{r["round"] + 1} {r["user"]} {m["i"] + 1}'


def players(arts, repo=REPO):
    with open(os.path.join(repo, "sessions", arts[-1]["session"], "report", "facts.json"), encoding="utf-8") as f:
        ps = json.load(f)["players"]
    seen = sorted({r["user"] for d in arts for r in d["rounds"]})
    _need(sorted(ps) == seen, f"the latest night's players {ps} are not the artefacts' {seen}")
    return ps


def recount(arts, users):
    ms = misses(arts)
    out = {}
    for u in users:
        for k, _, _ in PS.CATEGORIES:
            out[f"{k}.{u}"] = str(sum(1 for s, r, _, m in ms if r["user"] == u and m["category"] == k))
        out[f"all.{u}"] = str(sum(1 for s, r, _, m in ms if r["user"] == u))
        for d in arts:
            mine = [m for s, r, _, m in ms if s == d["session"] and r["user"] == u]
            out[f"{d['session']}.{u}"] = str(len(mine))
            for k, _, _ in PS.CATEGORIES:
                out[f"{d['session']}.{k}.{u}"] = str(sum(1 for m in mine if m["category"] == k))
    out["nights"] = str(len(arts))
    out["all"] = str(len(ms))
    return out


def selection(arts, users):
    """Per user and category, the SHOW latest misses, drawn oldest first."""
    ms = misses(arts)
    return {(u, k): [x for x in ms if x[1]["user"] == u and x[3]["category"] == k][-PS.SHOW:]
            for u in users for k, _, _ in PS.CATEGORIES}


def render(arts, repo=REPO):
    users = players(arts, repo)
    fig = recount(arts, users)
    sel = selection(arts, users)
    locs = {}

    def loc(s):
        if s not in locs:
            locs[s] = PS.Locator(os.path.join(repo, "sessions", s), s)
        return locs[s]

    title = f"{TITLE}{RS.TITLE_MARK}"
    css = [RP._tokens_css(), RP.BASE_CSS.strip("\n"), RT.PAGE_CSS.strip("\n")]
    note = PS.method_note(arts[-1])
    note = [ln.replace(PS.SELECT_MARKER, LATEST_MARKER).replace("同上面幾節一樣，", "") for ln in note]
    F = lambda k: f'<span data-figure="{html.escape(k)}">{fig[k]}</span>'
    out = ["<!doctype html>", '<html lang="zh-HK">', "<head>", '<meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width, initial-scale=1">',
           f"<title>{html.escape(title)}</title>", f'<meta name="description" content="{html.escape(DESC)}">',
           "<style>", "  " + "\n".join(css), "</style>", "</head>", "<body>", '<div class="wrap-wide">',
           '  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a></nav>',
           '<section id="pc-miss">', PS.CSS,
           f'    <div class="eyebrow">{RS.EYEBROW}</div>',
           f'    <h1 class="section-title">{html.escape(title)}</h1>',
           f'    <p>{F("nights")} 晚，兩個玩家加埋 {F("all")} 粒。每晚戰報嘅「行錯咗嗰一步」一節畫嗰晚自己嘅例子；'
           f'呢版逐晚數，再每類畫最近嘅例子。{RS.NO_CLAIM}。</p>',
           *note]

    # 1. corpus totals
    out += ["    <h2>全部晚加埋</h2>",
            '    <div class="scp-index-wrap"><table class="scp-table"><tr><th>類別</th>'
            + "".join(f"<th>{PS._who(i, u)}</th>" for i, u in enumerate(users)) + "</tr>"]
    for k, name, why in PS.CATEGORIES:
        out.append(f"    <tr><td>{name}<br><span class=\"pm-tag\">{why}</span></td>"
                   + "".join(f'<td class="pm-num">{F(f"{k}.{u}")}</td>' for u in users) + "</tr>")
    out.append('    <tr><td>合計</td>' + "".join(f'<td class="pm-num">{F(f"all.{u}")}</td>' for u in users)
               + "</tr></table></div>")

    # 2. per night
    out += ["    <h2>逐晚</h2>", "    <p>撳日子去嗰晚戰報嘅「行錯咗嗰一步」一節。每格係嗰晚嗰個玩家嘅粒數：蓋住窿／疊得太高／揀錯粒／擺錯位。</p>",
            '    <div class="scp-index-wrap"><table class="scp-table"><tr><th>日子</th>'
            + "".join(f"<th>{PS._who(i, u)}</th>" for i, u in enumerate(users)) + "</tr>"]
    for d in reversed(arts):
        s = d["session"]
        cells = "".join(f'<td class="pm-num"><strong>{F(f"{s}.{u}")}</strong>　'
                        + "／".join(F(f"{s}.{k}.{u}") for k, _, _ in PS.CATEGORIES) + "</td>" for u in users)
        out.append(f'    <tr><td><a data-night="{s}" href="{s}.html#pc-miss">{s}</a></td>{cells}</tr>')
    out.append("    </table></div>")

    # 3. latest examples
    out.append("    <h2>最近嘅例子</h2>")
    for i, u in enumerate(users):
        out.append(f"    <h3>{PS._who(i, u)}</h3>")
        for k, name, why in PS.CATEGORIES:
            got = sel[(u, k)]
            if not got:
                continue
            out += [f"    <h4>{name}</h4>", f"    <p>{why}</p>", '    <div class="pm-grid">']
            for s, r, kind, m in got:
                c = PS.card(m, kind, loc(s), r["file"], r["round"], u)
                c = c.replace('<div class="pm-card">', f'<div class="pm-card" data-case="{html.escape(case_key(s, r, m))}">', 1)
                c = c.replace("<strong>", f"<strong>{s} ", 1)
                out.append(c)
            out.append("    </div>")
    out.append("</section>")
    out += RT._tail({"figures": fig})
    return "\n".join(out)


REQUIRED = (RS.EYEBROW, RS.TITLE_MARK, RS.NO_CLAIM, LATEST_MARKER,
            *(m for m in PS.REQUIRED if m != PS.SELECT_MARKER))


def audit(page, arts, repo=REPO):
    bad = RP.audit_quarantine(page, REQUIRED, DATA_ID)
    if set(page) & SIMPLIFIED:
        bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
    if "%" in re.sub(r"<[^>]+>", "", RT._visible(page)):
        bad.append("a % on the page — it prints counts, never computed rates")
    users = players(arts, repo)
    figs = {}
    for k, v in _FIGURE.findall(page):
        k = html.unescape(k)
        if k in figs and figs[k] != html.unescape(v):
            bad.append(f"figure {k} printed twice with two values")
        figs[k] = html.unescape(v)
    rc = recount(arts, users)
    if figs != rc:
        bad.append(f"the printed figures are not the artefacts', recounted: "
                   f"{sorted(k for k in set(figs) | set(rc) if figs.get(k) != rc.get(k))[:4]}")
    nights = _NIGHT.findall(page)
    if sorted(n for n, _ in nights) != sorted(d["session"] for d in arts) or any(h != f"{n}.html#pc-miss" for n, h in nights):
        bad.append("the night table does not link every night's section exactly once")
    want = [case_key(s, r, m) for u in users for k, _, _ in PS.CATEGORIES for s, r, _, m in selection(arts, users)[(u, k)]]
    cases = _CASE.findall(page)
    if [html.unescape(c) for c, _ in cases] != want:
        bad.append("the examples are not the selection rule's, in order")
    rp = Replays(repo)
    byk = {case_key(s, r, m): (s, r, m) for s, r, _, m in misses(arts)}
    for ck, href in cases:
        ck, href = html.unescape(ck), html.unescape(href)
        hit, mt = byk.get(ck), _HREF.match(href)
        if hit is None or not mt or mt.group(1) != hit[0]:
            bad.append(f"{ck}: the replay link {href!r} is not this miss's night")
            continue
        s, r, m = hit
        rr = rp._replay_round(s, r["file"], r["round"])
        n = int(mt.group(3))
        if mt.group(2) != rr["label"] or n >= len(rr["order"]):
            bad.append(f"{ck}: {href!r} is not a position of this round")
            continue
        slot = rr["order"][n]
        k = rr["order"][:n].count(slot)
        who = rr["users"][int(slot)]
        if who != r["user"] or k != m["i"]:
            bad.append(f"{ck}: position {n} steps into {who}'s lock {k}, not the miss")
        elif rr["locks"][who][k][0] != m["state"]["piece"]:
            bad.append(f"{ck}: the replay places {rr['locks'][who][k][0]} there, the card draws {m['state']['piece']}")
    return bad


def render_all(repo=REPO, arts=None):
    arts = arts or load_all(repo)
    page = render(arts, repo)
    bad = audit(page, arts, repo)
    _need(not bad, "; ".join(bad))
    return {OVERVIEW: page}


def selftest(repo=REPO):
    arts = load_all(repo)
    page = render(arts, repo)
    survived = killed = 0

    def expect(label, bad, want):
        nonlocal survived, killed
        if bool(bad) == want:
            killed += want
            print(f'  {"killed" if want else "passed"}: {label}')
        else:
            survived += 1
            print(f'  {"SURVIVED" if want else "FAILED control"}: {label} {bad[:2]}', file=sys.stderr)

    expect("the rendered page (control)", audit(page, arts, repo), False)
    for s in REQUIRED:
        expect(f"every copy of a required sentence deleted ({s[:16]})", audit(page.replace(s, ""), arts, repo), True)
    expect("a badge planted", audit(page.replace("</h1>", '<span data-claim="C001">✓</span></h1>', 1), arts, repo), True)
    m = re.search(r'data-figure="all\.[^"]+">(\d+)<', page)
    expect("a figure edited", audit(page[:m.start(1)] + str(int(m.group(1)) + 1) + page[m.end(1):], arts, repo), True)
    nm = _NIGHT.search(page)
    expect("a night unlinked", audit(page.replace(nm.group(0), nm.group(0).replace("#pc-miss", ""), 1), arts, repo), True)
    cs = re.search(r'<div class="pm-card" data-case="[^"]+">', page)
    expect("an example dropped from the selection",
           audit(page.replace(cs.group(0), '<div class="pm-card">', 1), arts, repo), True)
    lk = re.search(r'@p(\d+)">重播', page)
    expect("an example link one position late",
           audit(page[:lk.start(1)] + str(int(lk.group(1)) + 1) + page[lk.end(1):], arts, repo), True)
    expect("a computed rate printed", audit(page.replace("</h1>", "<p>27%</p></h1>", 1), arts, repo), True)
    expect("a simplified glyph", audit(page.replace("</h1>", "<p>实</p></h1>", 1), arts, repo), True)
    expect("an artefact edited after rendering (a category moved)",
           audit(page, _move_category(arts), repo), True)
    print(f"selftest: {killed} killed, {survived} survived")
    return 1 if survived else 0


def _move_category(arts):
    a = json.loads(json.dumps(arts))
    for d in a:
        for r in d["rounds"]:
            for w in r["windows"]:
                for m in w["misses"]:
                    if PS.reported(m):
                        m["category"] = next(k for k, _, _ in PS.CATEGORIES if k != m["category"])
                        return a
    raise ValueError("no reported miss")


def site_card(arts):
    return {"href": OVERVIEW, "cases": len(misses(arts)), "kicker": KICKER, "title": TITLE, "blurb": BLURB}


def main(argv=None):
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    d = a.out_dir or os.path.join(REPO, "docs")
    for name, page in render_all().items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(page)
        print(f"wrote {os.path.join(d, name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

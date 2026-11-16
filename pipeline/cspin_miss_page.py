"""C-Spin 冇砌 — the corpus page: every night's `sim/cspin-miss-facts.json` rolled up into
`docs/cspin-miss.html`, audited before it is returned.

    python3 -m pipeline.cspin_miss_page --out-dir /tmp/csm   # render it somewhere other than docs/
    python3 -m pipeline.cspin_miss_page --selftest           # the audit's mutants

Inputs, all committed: each session's `sim/cspin-miss-facts.json` (`pipeline/sim/cspin-miss.ts`), its
`replay-facts.json` and `facts.json` (for the replay links). The night's own section
(`pipeline/cspin_miss_section.py`) draws that night's cases; this page counts every night per player
(holes, cold-clear's C-Spins, both, the player's alone, cold-clear's alone), links each night's
section, and draws EVERY case, newest night first. It reuses the section's cards, CSS, script and
method note, so the two say one thing.

QUARANTINE, the section's tier: no claim ids, no ✓, no `data-claim`, every artefact must say
`report_eligible: false`. The audit reuses `replay_page.audit_quarantine` and adds:

* every printed figure (`data-figure`) is RECOUNTED from the artefacts' windows, not their counts;
* every night with an artefact is linked exactly once, to `<date>.html#cspin-miss`;
* the cards are exactly every case, in order (`data-case`);
* every card's replay link is read back from the replay side (`dpc_page.Replays`): the position's
  next step is the case player's lock, and that lock places the piece the player placed;
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

from pipeline import cspin_miss_section as CM
from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline import route_page as RT
from pipeline.claims.build_claims import SIMPLIFIED
from pipeline.dpc_page import Replays

HERE, REPO = RT.HERE, RT.REPO
DATA_ID = RT.DATA_ID
PREFIX = "cspin-miss"
OVERVIEW = "cspin-miss.html"
TITLE = "C-Spin 冇砌：cold-clear 會砌嘅窿"
DESC = "每晚每個玩家，開局之後差少少可以砌成 C-Spin 位嘅窿，交俾 cold-clear 用同一啲粒行 14 粒：佢砌到 C-Spin 而玩家冇嘅，逐個畫出嚟。bot 同模擬器推導，唔屬於信任鏈。"
ALL_MARKER = "下面畫晒每一個，最新嗰晚排先"
KICKER = "C-Spin · cold-clear"
BLURB = "盤底差少少可以砌成 C-Spin 位嘅窿：cold-clear 用同一啲粒砌到 C-Spin，而玩家冇，逐晚逐個玩家數。"
KEYS = ("windows", "cc", "both", "human_only", "miss")
NIGHT_KEYS = ("windows", "cc", "miss")
NAMES = (("windows", "窿"), ("cc", "cold-clear 砌到"), ("both", "兩邊都砌到"),
         ("human_only", "淨係佢砌到"), ("miss", "cold-clear 砌到而佢冇"))

_FIGURE = re.compile(r'data-figure="([^"]+)">([^<]*)<')
_NIGHT = re.compile(r'<a data-night="([^"]+)" href="([^"]+)">')
_CASE = re.compile(r'<div class="cm-card" data-case="([^"]+)">.*?<a href="([^"]+)">重播呢一刻</a>', re.S)
_HREF = re.compile(r'^(\d{4}-\d{2}-\d{2})-replay\.html#(m\d+r\d+)@p(\d+)$')


def _need(cond, msg):
    if not cond:
        raise ValueError(f"cspin-miss page: {msg}")


def load_all(repo=REPO):
    out = []
    for p in sorted(glob.glob(os.path.join(repo, "sessions", "*", CM.FACTS_REL))):
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        _need(d.get("report_eligible") is False, f"{p} is not marked report_eligible: false")
        _need(d["session"] == p.split(os.sep)[-3], f"{p} names session {d['session']}")
        out.append(d)
    _need(out, "no session has a cspin-miss artefact")
    return out


def players(arts, repo=REPO):
    with open(os.path.join(repo, "sessions", arts[-1]["session"], "report", "facts.json"), encoding="utf-8") as f:
        ps = json.load(f)["players"]
    seen = sorted({u for d in arts for u in d["counts"]["by_player"]})
    _need(sorted(ps) == seen, f"the latest night's players {ps} are not the artefacts' {seen}")
    return ps


def tally(windows, user):
    """The five counts, from the windows' own verdicts (never from the artefact's counts)."""
    t = dict.fromkeys(KEYS, 0)
    for w in windows:
        if w["id"].split("/")[2] != user:
            continue
        cc, hu = bool(w["cc"]["fire"]), bool(w["human"]["fire"])
        t["windows"] += 1
        t["cc"] += cc
        t["both"] += cc and hu
        t["human_only"] += hu and not cc
        t["miss"] += cc and not hu
    return t


def recount(arts, users):
    out = {"nights": str(len(arts))}
    for u in users:
        tot = dict.fromkeys(KEYS, 0)
        for d in arts:
            t = tally(d["windows"], u)
            for k in KEYS:
                tot[k] += t[k]
                if k in NIGHT_KEYS:
                    out[f"{d['session']}.{k}.{u}"] = str(t[k])
        for k in KEYS:
            out[f"{k}.{u}"] = str(tot[k])
    out["miss"] = str(sum(int(out[f"miss.{u}"]) for u in users))
    return out


def every_case(arts):
    """(session, case) for every case, newest night first, then the artefact's order."""
    out = []
    for d in reversed(arts):
        want = [w["id"] for w in d["windows"] if w["cc"]["fire"] and not w["human"]["fire"]]
        _need([c["id"] for c in d["cases"]] == want, f"{d['session']}: cases are not cc-fire-and-not-human")
        out += [(d["session"], c) for c in d["cases"]]
    return out


def render(arts, repo=REPO):
    users = players(arts, repo)
    fig = recount(arts, users)
    locs = {}

    def loc(s):
        if s not in locs:
            locs[s] = CM.Locator(os.path.join(repo, "sessions", s), s)
        return locs[s]

    title = f"{TITLE}{RS.TITLE_MARK}"
    css = [RP._tokens_css(), RP.BASE_CSS.strip("\n"), RT.PAGE_CSS.strip("\n")]
    F = lambda k: f'<span data-figure="{html.escape(k)}">{fig[k]}</span>'
    out = ["<!doctype html>", '<html lang="zh-HK">', "<head>", '<meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width, initial-scale=1">',
           f"<title>{html.escape(title)}</title>", f'<meta name="description" content="{html.escape(DESC)}">',
           "<style>", "  " + "\n".join(css), "</style>", "</head>", "<body>", '<div class="wrap-wide">',
           '  <nav class="scp-top" aria-label="返去"><a href="index.html">← 全部戰報</a></nav>',
           '<section id="cspin-miss">', CM.CSS,
           f'    <div class="eyebrow">{RS.EYEBROW}</div>',
           f'    <h1 class="section-title">{html.escape(title)}</h1>',
           f'    <p>{F("nights")} 晚，兩個玩家加埋 {F("miss")} 個窿係 cold-clear 砌到 C-Spin 而佢冇。'
           f'每晚戰報嘅「C-Spin 冇砌」一節畫嗰晚自己嘅；{ALL_MARKER}。{RS.NO_CLAIM}。</p>',
           *CM.method_note(arts[-1])]

    head = "".join(f"<th>{CM._who(i, u)}</th>" for i, u in enumerate(users))
    out += ["    <h2>全部晚加埋</h2>",
            '    <div class="scp-index-wrap"><table class="scp-table"><tr><th></th>' + head + "</tr>"]
    for k, name in NAMES:
        out.append(f"    <tr><td>{name}</td>" + "".join(f'<td class="cm-num">{F(f"{k}.{u}")}</td>' for u in users) + "</tr>")
    out.append("    </table></div>")

    out += ["    <h2>逐晚</h2>",
            "    <p>撳日子去嗰晚戰報嘅「C-Spin 冇砌」一節。每格：窿／cold-clear 砌到／cold-clear 砌到而佢冇。</p>",
            '    <div class="scp-index-wrap"><table class="scp-table"><tr><th>日子</th>' + head + "</tr>"]
    for d in reversed(arts):
        s = d["session"]
        cells = "".join('<td class="cm-num">' + "／".join(F(f"{s}.{k}.{u}") for k in NIGHT_KEYS) + "</td>"
                        for u in users)
        out.append(f'    <tr><td><a data-night="{s}" href="{s}.html#cspin-miss">{s}</a></td>{cells}</tr>')
    out.append("    </table></div>")

    out.append("    <h2>每一個</h2>")
    wins = {}
    for d in arts:
        wins.update(CM.lookup(d))
    cases = every_case(arts)
    for i, u in enumerate(users):
        mine = [(s, c) for s, c in cases if c["user"] == u]
        out.append(f"    <h3>{CM._who(i, u)}</h3>")
        if not mine:
            out.append("    <p>一個都冇。</p>")
            continue
        out.append('    <div class="cm-grid">')
        for s, c in mine:
            card = CM.card(c, wins[c["id"]], loc(s))
            card = card.replace('<div class="cm-card">', f'<div class="cm-card" data-case="{html.escape(c["id"])}">', 1)
            card = card.replace("<strong>", f"<strong>{s} ", 1)
            out.append(card)
        out.append("    </div>")
    out.append(CM.SCRIPT)
    out.append("</section>")
    out += RT._tail({"figures": fig})
    return "\n".join(out)


REQUIRED = (RS.EYEBROW, RS.TITLE_MARK, RS.NO_CLAIM, ALL_MARKER, *CM.REQUIRED)


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
    if sorted(n for n, _ in nights) != sorted(d["session"] for d in arts) or any(h != f"{n}.html#cspin-miss" for n, h in nights):
        bad.append("the night table does not link every night's section exactly once")
    cases = every_case(arts)
    want = [c["id"] for u in users for _, c in cases if c["user"] == u]
    got = _CASE.findall(page)
    if [html.unescape(c) for c, _ in got] != want:
        bad.append("the cards are not every case, in order")
    rp = Replays(repo)
    byid = {c["id"]: (s, c) for s, c in cases}
    for cid, href in got:
        cid, href = html.unescape(cid), html.unescape(href)
        hit, mt = byid.get(cid), _HREF.match(href)
        if hit is None or not mt or mt.group(1) != hit[0]:
            bad.append(f"{cid}: the replay link {href!r} is not this case's night")
            continue
        s, c = hit
        rr = rp._replay_round(s, c["file"], c["round"])
        n = int(mt.group(3))
        if mt.group(2) != rr["label"] or n >= len(rr["order"]):
            bad.append(f"{cid}: {href!r} is not a position of this round")
            continue
        slot = rr["order"][n]
        k = rr["order"][:n].count(slot)
        who = rr["users"][int(slot)]
        if who != c["user"] or k != c["lock"]:
            bad.append(f"{cid}: position {n} steps into {who}'s lock {k}, not the case")
        elif rr["locks"][who][k][0] != c["human"][0]["piece"]:
            bad.append(f"{cid}: the replay places {rr['locks'][who][k][0]} there, the card draws {c['human'][0]['piece']}")
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
    m = re.search(r'data-figure="miss\.[^"]+">(\d+)<', page)
    expect("a figure edited", audit(page[:m.start(1)] + str(int(m.group(1)) + 1) + page[m.end(1):], arts, repo), True)
    nm = _NIGHT.search(page)
    expect("a night unlinked", audit(page.replace(nm.group(0), nm.group(0).replace("#cspin-miss", ""), 1), arts, repo), True)
    cs = re.search(r'<div class="cm-card" data-case="[^"]+">', page)
    expect("a card dropped", audit(page.replace(cs.group(0), '<div class="cm-card">', 1), arts, repo), True)
    lk = re.search(r'@p(\d+)">重播呢一刻', page)
    expect("a card link one position late",
           audit(page[:lk.start(1)] + str(int(lk.group(1)) + 1) + page[lk.end(1):], arts, repo), True)
    expect("a computed rate printed", audit(page.replace("</h1>", "<p>27%</p></h1>", 1), arts, repo), True)
    expect("a simplified glyph", audit(page.replace("</h1>", "<p>实</p></h1>", 1), arts, repo), True)
    a = json.loads(json.dumps(arts))
    cid = next(c["id"] for d in a for c in d["cases"])
    w = next(w for d in a for w in d["windows"] if w["id"] == cid)
    w["human"]["fire"] = True
    expect("a window's verdict moved after rendering", _guard(lambda: audit(page, a, repo)), True)
    print(f"selftest: {killed} killed, {survived} survived")
    return 1 if survived else 0


def _guard(f):
    try:
        return f()
    except ValueError as e:
        return [str(e)]


def site_card(arts):
    return {"href": OVERVIEW, "cases": sum(len(d["cases"]) for d in arts), "kicker": KICKER, "title": TITLE, "blurb": BLURB}


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

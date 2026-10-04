"""逐局重播 — one self-contained replay page per session, every round inlined.

    python3 -m pipeline.replay_page sessions/2026-10-03 --out /tmp/x.html   # render one page
    python3 -m pipeline.replay_page --selftest                              # the audit's mutants

Published by `bin/build-docs` as `docs/<date>-replay.html` (the name is
`replay_section.page_name`, the same function the report's 「睇成晚每一局」 link calls). build-docs
RENDERS it from the session's `sim/replay-facts.json` + `report/facts.json` rather than copying a
committed file, and `--check` re-renders and byte-compares, exactly as it does `docs/index.html` —
so the page cannot drift from either input, nor from the shared player, without CI saying so.

ONE PLAYER. The boards, seek bar, keys and key moments are `replay_player.js` — the very file the
report's 最癲一局 region inlines — mounted once per round the viewer picks, on the markup
`replay_section.player_box` emits for both. The per-round JSON is `replay_section.round_payload`, so
the region and the page cannot decode a round two ways. What this page adds is page-only and lives
in `replay_page.js`: the round picker, the hash (`#m<pos>r<round>@p<n>`), and the attack chart.

QUARANTINE. Same tier as the region: one simulator, no claim ids, no ✓ badges, no `data-claim`
anywhere on the page, and every sentence in `replay_section.REQUIRED` present. `audit()` enforces
that (plus zero external requests and no markup sinks) on every render, and `--selftest` gives each
rule a mutant.

THE CHART IS NOT SIMULATOR OUTPUT, AND IT IS NOT 食. It plots each player's RECORDED incoming
garbage events (`garbage_events` in facts.json, read by both extractors — the same `ge` the round
table's drawer uses), i.e. 射埋: what the opponent queued, BEFORE cancellation. Nothing on it is a
claim, so it carries no badge either; it says which it is. Each event's frame is on the receiving
player's own clock, while the playhead is the player's shared lock clock — the method note says so.

FIGURES. The match and round scores are counts of `winner` in facts.json; every other figure the
page prints is an integer count, or a rate computed in the browser and FLOORED (`fmt`'s rule).
"""
import argparse
import html
import json
import os
import re
import sys

from pipeline import replay_section as RS
from pipeline import skeleton

PAGE_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "replay_page.js")
PAGE_DATA_ID = "rpg-data"
TEMPLATE_ID = "rpg-player-tpl"
# Fields every round's payload carries identically; inlined once per page, not once per round.
SHARED = ("session", "shapes", "width", "rows", "visible", "next", "flag_words")

# The chart's own wording. Named so `audit` demands it: deleting the 「not 食」 half is the edit
# that turns a queued-attack chart into a received-garbage one without changing a pixel.
CHART_TITLE = "射埋（對手射過嚟、抵銷之前）"
CHART_SOURCE = ("呢幅圖<strong>唔係模擬器出嚟</strong>：每一級係 replay 記錄嘅一次攻擊事件"
                "（<code>facts.json</code> 嘅 <code>garbage_events</code>，兩個 parser 都抽到），"
                "畫嘅係<strong>射埋</strong>，即係對手射過嚟、抵銷之前嘅行數，"
                "<strong>唔係食</strong>咗幾多行垃圾。佢冇 claim 覆蓋，所以一樣冇 ✓。")
CHART_CLOCK = ("每次攻擊嘅時間係收嗰個玩家自己嘅 frame 鐘；直線係重播共用嘅時鐘，"
               "兩個玩家嘅鐘每局差大約半秒，所以直線同級數嘅對位係近似。"
               "撳圖入面任何一點，就會跳去嗰個時間之前最後一粒。")
PAGE_REQUIRED = RS.REQUIRED + (CHART_TITLE, CHART_SOURCE)

BADGE = re.compile(r"data-claim|claim-badge|已驗證")
NOTIFY_WITH_PLAYING = "opts.onChange(pos, t, playing)"
# every page-side hash write is `writeHash(p)`; capture what guards it
# show() must silence the hash before tearing the old player down: destroy() pauses, and that
# pause notifies with playing false while `cur` is still the OLD round
QUIET_BEFORE_DESTROY = "quiet = true;\n    if (handle) { handle.destroy(); handle = null; }"
PAGE_HASH_CALL = re.compile(r"(if \(!playing\) |)writeHash\(p\)")
MARKUP_SINK = re.compile(r"\binnerHTML\b|\bouterHTML\b|insertAdjacentHTML|document\.write")
# Zero external requests: no element may fetch anything. The page links OUT with <a href>, which a
# browser does not fetch, so href is allowed; src=, <link>, @import, url( and fetch( are not.
EXTERNAL = re.compile(r"\ssrc\s*=|<link\b|@import|\burl\(|\bfetch\(|XMLHttpRequest|\bimport\(")


def _need(cond, msg):
    if not cond:
        raise SystemExit(f"replay_page: {msg}")


def _tokens_css():
    """The report shell's token block (light, dark, both data-theme overrides), cut out of
    `skeleton.CSS` rather than copied, so the page's colours are the reports' colours."""
    css = skeleton.CSS
    head = "/* ============================= TOKENS ============================= */"
    tail = "/* ============================= RESET / BASE"
    i, j = css.find(head), css.find(tail)
    _need(0 <= i < j, "skeleton.CSS no longer has its TOKENS / RESET banners")
    return css[i + len(head):j].strip()


BASE_CSS = """
  * { box-sizing: border-box; }
  html { color-scheme: light dark; }
  body { margin: 0; background: var(--bg); color: var(--ink); font-family: var(--font-cjk);
    font-size: 16px; line-height: 1.7; -webkit-font-smoothing: antialiased; overflow-x: hidden; }
  a { color: inherit; }
  code { font-family: var(--font-mono); font-size: .86em; }
  .wrap-wide { max-width: var(--wide-w); margin: 0 auto; padding: 0 20px; }
  .eyebrow { font-family: var(--font-mono); font-size: .76rem; letter-spacing: .14em;
    text-transform: uppercase; color: var(--muted); margin: 0 0 10px; }
  .section-title { font-size: clamp(1.4rem, 3.4vw, 2rem); font-weight: 800; margin: 0 0 .4rem;
    line-height: 1.3; }
  .method-note { margin: 1.2rem 0; padding: 16px 20px; border-radius: 14px; font-size: .9rem;
    background: var(--bg-raised); border: 1px solid var(--border); color: var(--ink-secondary); }
  .method-note p { margin: 0 0 .7em; }
  .method-note p:last-child { margin-bottom: 0; }
  .method-note summary { cursor: pointer; font-weight: 700; color: var(--ink); }
  .rpg-top { display: flex; gap: 1rem; flex-wrap: wrap; padding: 14px 0 0; font-size: .85rem;
    font-family: var(--font-mono); }
  .rpg-top a { color: var(--ink-secondary); }
  .rpg-head { padding: 22px 0 6px; }
  .rpg-picker { margin: .6rem 0 1rem; }
  .rpg-picker h2 { font-size: .95rem; margin: 0 0 .4rem; }
  .rpg-matches { display: flex; gap: .4rem; overflow-x: auto; padding: 2px 2px 8px;
    scrollbar-width: thin; }
  .rpg-match { flex: none; font: 600 .82rem var(--font-mono); padding: .35rem .6rem;
    border: 1px solid var(--border-strong); border-radius: 8px; background: var(--bg-raised);
    color: var(--ink); cursor: pointer; font-variant-numeric: tabular-nums; }
  .rpg-match[aria-expanded="true"] { border-color: var(--ink); box-shadow: inset 0 -3px 0 var(--ink); }
  .rpg-match .rpg-w0 { color: var(--p1); }
  .rpg-match .rpg-w1 { color: var(--p2); }
  .rpg-rounds { list-style: none; margin: .5rem 0 0; padding: 0; display: flex; flex-wrap: wrap;
    gap: .35rem; }
  .rpg-rounds[hidden] { display: none; }
  .rpg-round { display: inline-block; font: .8rem var(--font-mono); padding: .25rem .55rem;
    border: 1px solid var(--border); border-radius: 6px; text-decoration: none;
    color: var(--ink-secondary); font-variant-numeric: tabular-nums; }
  .rpg-round[data-w="0"] { border-left: 3px solid var(--p1); }
  .rpg-round[data-w="1"] { border-left: 3px solid var(--p2); }
  .rpg-round[aria-current="true"] { border-color: var(--ink); color: var(--ink); font-weight: 700; }
  .rpg-round .rpg-star { color: var(--pending); }
  .rpg-now { margin: 1.2rem 0 .2rem; font-size: 1.05rem; font-weight: 800; }
  .rpg-notes { font-size: .82rem; color: var(--ink-secondary); margin: 0; }
  .rpg-flag { font-size: .85rem; font-weight: 700; color: var(--rp-bad); margin: .3rem 0 0; }
  .rpg-flag[hidden] { display: none; }
  .rpg-missing { font-size: .85rem; color: var(--rp-bad); margin: .4rem 0 0; }
  .rpg-missing[hidden] { display: none; }
  .rpg-chart { margin: 1rem 0 0; }
  .rpg-chart figcaption { font-size: .8rem; color: var(--ink-secondary); margin-top: .35rem; }
  .rpg-chart-title { font-size: .9rem; font-weight: 700; margin: 0 0 .25rem; }
  .rpg-legend { display: flex; flex-wrap: wrap; gap: .2rem 1rem; font-size: .78rem;
    color: var(--ink-secondary); margin: 0 0 .3rem; }
  .rpg-legend i { display: inline-block; width: 1.2rem; height: 3px; vertical-align: middle;
    margin-right: .3rem; border-radius: 2px; }
  .rpg-legend i[data-slot="0"] { background: var(--rp-c0); }
  .rpg-legend i[data-slot="1"] { background: var(--rp-c1); }
  .rpg-canvas { display: block; width: 100%; height: 150px; cursor: crosshair;
    background: var(--bg-sunken); border-radius: 8px; touch-action: manipulation; }
  footer { margin: 3rem 0 2rem; padding-top: 1rem; border-top: 1px solid var(--border);
    font-size: .8rem; color: var(--muted); }
  @media (max-width: 640px) {
    .wrap-wide { padding: 0 12px; }
    .method-note { padding: 12px 14px; }
    .rpg-canvas { height: 120px; }
  }
  @media print { .rpg-picker, .rpg-chart { display: none; } }
"""


# ---------------------------------------------------------------- data

def _score(rounds, users, upto=None):
    """Round wins per player (in `users` order) over `rounds[:upto]`."""
    w = [0, 0]
    for r in rounds[:upto]:
        _need(r["winner"] in users, f"round winner {r['winner']!r} is not a player")
        w[users.index(r["winner"])] += 1
    return w


def page_data(data, facts):
    """(shared, rounds, picker, default label) for one session. Every round of facts.json must
    have exactly one replay entry — a missing round is a refusal, never a gap in the picker."""
    RS.check_artefact(data)
    users = list(facts["players"])
    _need(len(users) == 2, "a replay page is for a two-player session")
    sel = RS.select(facts)
    default = shared = None
    rounds, picker = [], []
    n_facts = 0
    for mi, m in enumerate(facts["matches"]):
        _need(m["winner"] in users, f"match winner {m['winner']!r} is not a player")
        items = []
        for ri, r in enumerate(m["rounds"]):
            n_facts += 1
            pl = RS.round_payload(data, facts, mi, ri)
            if shared is None:
                shared = {k: pl[k] for k in SHARED}
            # inlined once, so it must BE the same for every round, not assumed to be
            _need(all(pl[k] == shared[k] for k in SHARED),
                  f"{pl['label']}: a field the page shares across rounds differs")
            lean = {k: v for k, v in pl.items() if k not in SHARED}
            lean["notes"] = [RS._player_note(p, esc=str) for p in pl["players"]]
            rounds.append(lean)
            intense = sel is not None and (sel[0], sel[1]) == (mi, ri)
            if intense:
                default = pl["label"]
            items.append({"label": pl["label"], "round": ri + 1,
                          "w": users.index(r["winner"]), "winner": r["winner"],
                          "score": _score(m["rounds"], users, ri + 1), "intense": intense})
        picker.append({"match": m["index"], "file": m["file"], "w": users.index(m["winner"]),
                       "winner": m["winner"], "score": _score(m["rounds"], users), "rounds": items})
    _need(len(data["rounds"]) == n_facts,
          f"replay-facts.json holds {len(data['rounds'])} rounds, facts.json {n_facts}")
    return shared, rounds, picker, default or (rounds[0]["label"] if rounds else None)


# ---------------------------------------------------------------- markup

def _picker_html(picker, users):
    esc = html.escape
    out = ['    <nav class="rpg-picker" aria-label="揀局">',
           '      <h2>揀局：先揀場，再揀局（顏色係贏家）</h2>',
           '      <div class="rpg-matches">']
    for m in picker:
        a, b = m["score"]
        out.append(f'        <button type="button" class="rpg-match" data-m="{m["match"]}" '
                   f'aria-expanded="false" aria-controls="rpg-r{m["match"]}" '
                   f'title="{esc(m["file"])}">第 {m["match"]} 場 '
                   f'<span class="rpg-w{m["w"]}">{a}:{b}</span></button>')
    out.append('      </div>')
    for m in picker:
        out.append(f'      <ol class="rpg-rounds" id="rpg-r{m["match"]}" data-m="{m["match"]}" '
                   f'aria-label="第 {m["match"]} 場（{esc(m["winner"])} 贏，'
                   f'{esc(users[0])} {m["score"][0]}:{m["score"][1]} {esc(users[1])}）" hidden>')
        for r in m["rounds"]:
            star = ' <span class="rpg-star">★ 最癲一局</span>' if r["intense"] else ""
            out.append(f'        <li><a class="rpg-round" href="#{r["label"]}" '
                       f'data-label="{r["label"]}" data-w="{r["w"]}">第 {r["round"]} 局 · '
                       f'{esc(r["winner"])} 贏 · {r["score"][0]}:{r["score"][1]}{star}</a></li>')
        out.append('      </ol>')
    out.append('    </nav>')
    return out


def render(data, facts, report_href):
    """The whole page, or None when the session has no replay artefact. Audited before return."""
    if data is None:
        return None
    shared, rounds, picker, default = page_data(data, facts)
    _need(rounds, "no rounds to replay")
    users = list(facts["players"])
    session = shared["session"]
    esc = html.escape
    blob = json.dumps({"shared": shared, "rounds": rounds, "default": default},
                      ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    with open(PAGE_JS, encoding="utf-8") as fh:
        page_js = fh.read().rstrip()
    _need("</script" not in page_js.lower(), "replay_page.js may not contain a closing script tag")
    names = "、".join(esc(u) for u in users)
    title = f"{session} 逐局重播{RS.TITLE_MARK}"
    css = _tokens_css()
    out = [
        '<!doctype html>',
        '<html lang="zh-HK">',
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f'<title>{esc(title)}</title>',
        f'<meta name="description" content="{esc(session)} 每一局嘅模擬重播：模擬器推導，唔屬於信任鏈。">',
        '<style>',
        '  ' + css,
        BASE_CSS.strip('\n'),
        RS._color_css([{"user": u} for u in users]),
        RS.CSS.strip('\n'),
        '</style>',
        '</head>',
        '<body>',
        '<div class="wrap-wide">',
        '  <nav class="rpg-top" aria-label="返去">'
        '<a href="index.html">← 全部戰報</a>'
        f'<a href="{esc(report_href)}">{esc(session)} 完整戰報</a></nav>',
        '  <header class="rpg-head">',
        f'    <div class="eyebrow">{RS.EYEBROW}</div>',
        f'    <h1 class="section-title">{esc(title)}</h1>',
        '  </header>',
        '  <div class="method-note">',
        f'    <p><strong>呢版唔屬於信任鏈。</strong>佢逐局重播 {esc(session)} 呢一晚（{names}）'
        '嘅每一局：盤面係<strong>一個 replay 模擬器</strong>（Triangle 引擎）重跑操作記錄推導出嚟，'
        'replay 檔本身冇記錄過任何盤面，所以冇一格曾經同遊戲逐格對過，亦冇第二份獨立實作。'
        f'所以呢版<strong>{RS.NO_CLAIM}</strong>；有證明嘅數字喺'
        f'<a href="{esc(report_href)}">當晚嘅完整戰報</a>入面。</p>',
        '    <details>',
        '      <summary>點樣讀呢個重播（必讀嘅限制）</summary>',
        f'      <p>{RS.DROP_SENTENCE}</p>',
        f'      <p>{RS.HOLE_SENTENCE}</p>',
        '      <p>盤邊條直柱係<strong>射埋</strong>嘅垃圾：攞對手射過嚟、記錄喺 replay 嘅數'
        '（抵銷之前），減去引擎自己抵銷咗同塞咗落盤嘅行數。未必全部都會食到。</p>',
        f'      <p>{RS.BOUNDARY_SENTENCE}</p>',
        '      <p>每一局都會核成局總數（粒數、消行、hold、清垃圾、攻擊、全消、每種 T-spin）同 '
        '<code>facts.json</code> 夾唔夾，同埋引擎個盤爆唔爆同遊戲記錄夾唔夾；有一項唔夾，嗰局就會寫'
        f'「{RS.FLAG_WORDS}」。對得上只係講總數，<strong>唔會</strong>令呢版入返信任鏈。</p>',
        '      <p>上面嘅場數同局數比數係 <code>facts.json</code> 數出嚟嘅贏家，唔係模擬器嘅。</p>',
        '    </details>',
        '  </div>',
        *['  ' + line for line in _picker_html(picker, users)],
        f'  <section id="{RS.SECTION_ID}" aria-labelledby="rpg-now">',
        '    <h2 class="rpg-now" id="rpg-now" aria-live="polite"></h2>',
        '    <p class="rpg-notes"></p>',
        f'    <p class="rpg-flag" hidden>{RS.FLAG_WORDS}</p>',
        '    <p class="rpg-missing" hidden>呢個連結指住嘅局唔存在，而家顯示緊預設嗰局。</p>',
        '    <noscript><p>重播同揀局要開 JavaScript 先用到。</p></noscript>',
        '    <div class="rpg-host"></div>',
        '    <figure class="rpg-chart">',
        f'      <p class="rpg-chart-title">{CHART_TITLE}：累積行數</p>',
        '      <div class="rpg-legend" aria-hidden="true"></div>',
        '      <canvas class="rpg-canvas" role="img"></canvas>',
        f'      <figcaption>{CHART_SOURCE}{CHART_CLOCK}</figcaption>',
        '    </figure>',
        f'    <template id="{TEMPLATE_ID}">',
        *['  ' + line for line in RS.player_box("", users)],
        '    </template>',
        '  </section>',
        '  <footer><p>模擬器推導嘅重播，唔屬於信任鏈；'
        f'Dafny 證明嘅係戰報入面嘅 claim，唔係呢度嘅盤面。</p></footer>',
        '</div>',
        f'<script type="application/json" id="{PAGE_DATA_ID}">{blob}</script>',
        '<script>\n' + RS.player_js() + '\n</script>',
        '<script>\n' + page_js + '\n</script>',
        '</body>',
        '</html>',
        '',
    ]
    page = RS._no_simplified("\n".join(out))
    bad = audit(page)
    _need(not bad, "; ".join(bad))
    return page


# ---------------------------------------------------------------- the audit

def audit(page):
    """Every reason `page` breaks the quarantine or the single-file rule; empty means clean."""
    bad = []
    if BADGE.search(page):
        bad.append("the page carries a claim badge — simulator boards must not be badged")
    for s in PAGE_REQUIRED:
        if s not in page:
            bad.append(f"a quarantine sentence is gone: {s[:40]!r}…")
    if MARKUP_SINK.search(page):
        bad.append("the page assigns markup (innerHTML or similar) — build nodes instead")
    if EXTERNAL.search(page):
        bad.append("the page makes an external request — it must be one self-contained file")
    if page.count(f'id="{PAGE_DATA_ID}"') != 1:
        bad.append("the page must inline exactly one data island")
    # The player calls onChange on every animation frame while playing; a history write there
    # passes WebKit's ~100-calls rate limit within seconds at 4x and the throw kills the rAF
    # loop. So the player must report `playing`, and the page may write the hash only without it.
    if NOTIFY_WITH_PLAYING not in page:
        bad.append("the player's notify() no longer passes `playing` to onChange — the page cannot tell a play frame from a pause")
    if QUIET_BEFORE_DESTROY not in page:
        bad.append("show() tears down the old player before setting quiet — its teardown pause rewrites the hash with the OLD round")
    calls = PAGE_HASH_CALL.findall(page)
    if not calls or any(g != "if (!playing) " for g in calls):
        bad.append("the page writes the hash while playing — history writes must wait for pause")
    return bad


def _selftest():
    """The audit must pass a clean page and catch each planted corruption by its own message."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sdir = os.path.join(root, "sessions", "2026-07-24")
    data, facts = load(sdir)
    page = render(data, facts, "2026-07-24.html")
    cases = [("control: the rendered page", page, None)]
    cases.append(("a claim badge", page.replace(RS.TITLE_MARK, RS.TITLE_MARK + '<span class="claim-badge">✓</span>', 1), "claim badge"))
    cases.append(("a data-claim attribute", page.replace('class="rpg-picker"', 'class="rpg-picker" data-claim="C001"', 1), "claim badge"))
    for s in PAGE_REQUIRED:
        cases.append((f"required sentence deleted ({s[:16]}…)", page.replace(s, ""), "quarantine sentence"))
    cases.append(("an innerHTML assignment", page.replace('"use strict";', '"use strict"; document.body.innerHTML = "";', 1), "assigns markup"))
    cases.append(("the hash written while playing", page.replace("if (!playing) writeHash(p)", "writeHash(p)", 1), "while playing"))
    cases.append(("notify() drops the playing flag", page.replace(NOTIFY_WITH_PLAYING, "opts.onChange(pos, t)", 1), "no longer passes"))
    cases.append(("destroy() before quiet", page.replace(QUIET_BEFORE_DESTROY, "if (handle) { handle.destroy(); handle = null; }\n    quiet = true;", 1), "OLD round"))
    cases.append(("an external script", page.replace("<script>", '<script src="https://cdn.example/x.js"></script><script>', 1), "external request"))
    cases.append(("an external stylesheet", page.replace("<style>", '<link rel="stylesheet" href="x.css"><style>', 1), "external request"))
    cases.append(("a second data island", page.replace("</body>", f'<script type="application/json" id="{PAGE_DATA_ID}">{{}}</script></body>', 1), "data island"))
    ok = True
    for name, p, want in cases:
        applied = p != page or want is None
        found = audit(p)
        good = applied and ((not found) if want is None else any(want in f for f in found))
        ok &= good
        print(f"  {'ok ' if good else 'BAD'} {name}: {'rejected' if found else 'accepted'}"
              f"{'' if applied else '  <- the mutant did not apply'}")
    eligible = json.loads(json.dumps(data))
    eligible["report_eligible"] = True
    try:
        render(eligible, facts, "x.html")
        print("  BAD a report-eligible artefact rendered")
        ok = False
    except SystemExit as e:
        print(f"  ok  a report-eligible artefact is refused: {str(e)[:60]}…")
    short = json.loads(json.dumps(data))
    short["rounds"] = short["rounds"][:-1]
    try:
        render(short, facts, "x.html")
        print("  BAD an artefact missing a round rendered")
        ok = False
    except SystemExit as e:
        print(f"  ok  an artefact missing a round is refused: {str(e)[:60]}…")
    print(f"{'ok ' if ok else 'FAIL'} replay_page selftest: {len(cases) - 1 + 2} corruptions, "
          f"{'all caught' if ok else 'SOME MISSED'}")
    return 0 if ok else 1


def load(session_dir):
    """(replay facts or None, facts) for `session_dir` (sessions/<date>)."""
    report = os.path.join(session_dir, "report")
    with open(os.path.join(report, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    return RS.load(report), facts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("session", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    if not a.session or not a.out:
        ap.error("need a session dir and --out, or --selftest")
    data, facts = load(a.session)
    page = render(data, facts, os.path.basename(os.path.normpath(a.session)) + ".html")
    if page is None:
        print(f"{a.session} has no {RS.FACTS_REL}; no page", file=sys.stderr)
        return 1
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"wrote {a.out} ({len(page.encode())} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

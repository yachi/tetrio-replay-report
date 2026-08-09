"""C-Spin 同 DT 砲 — 模擬器推導區，同 forecast 一樣刻意排喺信任鏈之外。

Renders `sim/opener-facts.json`. Everything the forecast section's docstring says about
quarantine applies here word for word and is not repeated: one simulator, no second
independent implementation, therefore no claim ids, no ✓ badges, and nothing merged into
facts.json. `check_opener_section.py` is this section's drift gate.

WHAT THIS SECTION IS FOR. Two openers that the report kept gesturing at without measuring:

    DT 砲 (DT Cannon, 開幕DT砲)  = a T-spin Double THEN a T-spin Triple
    C-Spin                       = a T-spin Triple THEN a T-spin Double

They are the same pair of events in the two orders, which is why one section covers both and
why the ordering table is the section's spine. Order is a property only the simulator knows —
`facts.json` counts `tspin_doubles` and `tspin_triples` but not which came first — so this is
exactly the kind of question the quarantined tier exists to answer.

THREE TABLES, THREE CONTROLS. Each table is paired with the thing that says what it is NOT,
because each of these metrics has a way of looking like a finding when it is an artefact:

  ordering      control = exposure. Scored only on rounds holding BOTH spins, so a zero is over
                rounds that had the material for either order — and re-run over the whole
                simulated round as well, so the verified-prefix window cannot manufacture it.
  first bag     control = set choice. The C-Spin name set is genuinely doubtful (`isCSpin`
                selects `Fake C-Spin`, `Secspin` and an `SDPC-Spin` compound), so the answer is
                shown over a narrow and a widest reading of BOTH openers. What is reportable is
                that it does not move.
  slot geometry control = the cross-tab by lines. ~9 in 10 Triples match the wiki window and
                ~1 in 10 Doubles do, which is what a Triple-shaped slot looks like rather than
                what an opener looks like. The section must state that in the same breath as
                the number; rendering the share alone would publish a C-Spin count this data
                cannot support.

`_no_simplified` runs over the finished markup. The prose here is authored in this module
rather than in `prose/*.json`, so it is not covered by any of the loaders' glyph checks, and
reviews have repeatedly caught 净/实/约 slipping into hand-written Cantonese in this repo.
"""
import html
import json
import os

from pipeline.claims.build_claims import SIMPLIFIED

# Session-scoped, exactly like forecast_section.FACTS_REL: a session with no simulator output
# has no such section, and a hardcoded path would graft one session's numbers into another's
# report — the bug that produced DRIFT on three sessions when the forecast section was added.
FACTS_REL = os.path.join("sim", "opener-facts.json")

# The order the first-bag table's rows are drawn in, narrowest reading first within each opener.
# `any` heads the table because a distance to the C-Spin set means nothing until you know how
# close these boards get to ANY catalogued opener — without it, "6 cells away" reads as a
# statement about the C-Spin when it is mostly a statement about the players.
#
# `any`'s label carries the catalogue's opener COUNT, which is why it is a format string rather
# than a literal: 360 is a property of the pinned upstream commit, and vendoring a newer catalogue
# must move the label with the data instead of leaving a stale number in the one row whose job is
# to say how big the comparison set is.
SET_ROWS = [
    ("any", "全部 {openers} 個定式"),
    ("cspin", "C-Spin（照名揀）"),
    ("cspin_or_tki", "C-Spin 或者 TKI"),
    ("dt_cannon", "DT 砲"),
    ("dt_family", "DT 家族（最闊）"),
]


def facts_path(report_dir):
    """`<session>/sim/opener-facts.json` for the session owning `report_dir`."""
    return os.path.join(os.path.dirname(os.path.abspath(report_dir)), FACTS_REL)


def load(report_dir):
    """The session's opener facts, or None when it has none."""
    path = facts_path(report_dir)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _pct(x1000):
    """x1000 integer -> one-decimal percent string, or an absence.

    None means the quantity had no denominator. It renders as 「—」 and never as 0.0%: a rate
    over nothing is an ABSENCE, and printing zero for it would publish "measured, and the
    effect is exactly nothing" — which this data cannot say. Same rule as `forecast_section._stat`.
    """
    return "—" if x1000 is None else f"{x1000 / 10:.1f}%"


def _cells(n):
    """A Hamming distance in cells, or an absence when no page shares the board's cell count."""
    return "—" if n is None else f"{n} 格"


def _players(data):
    """Players in a stable order — most C-Spin-ordered rounds first, then by name.

    Sorted rather than taken as emitted, because `emit-opener-facts.ts` walks `loadCases`, and
    the order players appear in the replay files is NOT stable across sessions (the same trap
    `facts.json` documents for `users` / `leaderboard`). An unsorted table would reorder its own
    columns between sessions for no reason a reader could see.
    """
    return sorted(data["ordering"]["players"],
                  key=lambda p: (-p["cspin_order"], p["user"]))


def _ordering_note(data):
    """The ordering result in words, with the exposure control and the full-round agreement.

    Everything here is DERIVED. An earlier draft of this paragraph said "not one round in any
    session ran the DT order" as prose; that is the kind of sentence that stays in the document
    after the data stops supporting it, so it is computed and the wording follows the numbers.
    """
    ps = data["ordering"]["players"]
    full = data["ordering_full_round"]["players"]
    both = sum(p["rounds_with_both"] for p in ps)
    cs = sum(p["cspin_order"] for p in ps)
    dt = sum(p["dt_order"] for p in ps)
    scored = sum(p["rounds_scored"] for p in ps)
    both_f = sum(p["rounds_with_both"] for p in full)
    dt_f = sum(p["dt_order"] for p in full)
    cs_f = sum(p["cspin_order"] for p in full)

    if not both:
        return ("呢個 session 冇任何一個回合<em>同時</em>有 T-spin Double 同 T-spin Triple，"
                "所以次序呢一項<strong>量唔到</strong>——冇材料就唔會有次序，"
                "而唔係話兩個定式都冇出現過。")

    lead = (f"可核嗰段入面，有 <strong>{both}</strong> 個回合"
            f"（全部 {scored} 個入面）同時有 T-spin Double 同 T-spin Triple，"
            "即係話呢啲回合本身有足夠材料行任何一個次序。")
    if dt == 0 and cs == both:
        body = (f"而 <strong>{both} 個全部都係先 Triple 後 Double</strong>，"
                f"即係 C-Spin 嗰個次序；行 DT 砲次序嘅係 <strong>0</strong> 個。"
                "呢個唔係「差唔多」，係完全冇重疊。")
    else:
        body = (f"其中先 Triple 後 Double（C-Spin 次序）有 <strong>{cs}</strong> 個，"
                f"先 Double 後 Triple（DT 砲次序）有 <strong>{dt}</strong> 個。")

    # The window is the obvious confound: the verified prefix is short, so an ordering result
    # could be an artefact of only ever seeing the first ~20 locks. Re-running over the whole
    # simulated round is the check.
    #
    # What has to agree is the SPLIT, not the counts. Dropping the verification requirement adds
    # exposure — more rounds qualify — so the counts SHOULD move, and an earlier version of this
    # branch read that expected growth as a disagreement and printed "so how long you look
    # matters", which is the opposite of what the wider window shows. The question the control
    # asks is whether the separation survives more exposure.
    if both_f == both and cs_f == cs and dt_f == dt:
        window = ("攤開成個模擬回合（唔限可核嗰段）計多次，逐個數都一模一樣，"
                  "所以呢個結果唔係「可核嗰段太短、睇唔到後面」整出嚟嘅。")
    elif dt_f == 0 and cs_f == both_f:
        window = (f"攤開成個模擬回合（唔限可核嗰段）再計一次，就有 {both_f} 個回合兩種都有——"
                  f"睇長咗自然多咗回合入圍——但係<strong>分家嘅方式一模一樣</strong>："
                  f"C-Spin 次序 {cs_f} 個、DT 砲次序<strong>依然係 0</strong> 個。"
                  "即係話呢個零唔係可核嗰段太短睇漏咗後面，睇多啲反而更加乾淨。")
    else:
        window = (f"攤開成個模擬回合（唔限可核嗰段）計多次：{both_f} 個回合兩種都有，"
                  f"C-Spin 次序 {cs_f} 個、DT 砲次序 {dt_f} 個。"
                  "同可核嗰段唔一樣，所以睇幾長本身有影響，兩組數要一齊睇。")
    return lead + body + window


def _first_bag_note(data):
    """Whether the first-bag answer moves between the narrow and the widest name set."""
    sets = data["catalogue"]["sets"]
    players = data["first_bag"]["players"]

    def agg(key):
        mins = [p["nearest"][key]["min_cells"] for p in players
                if p["nearest"][key]["min_cells"] is not None]
        return (min(mins) if mins else None,
                sum(p["nearest"][key]["within_threshold"] for p in players))

    near = data["near_cells"]
    c_min, c_in = agg("cspin")
    ct_min, ct_in = agg("cspin_or_tki")
    d_min, d_in = agg("dt_cannon")
    df_min, df_in = agg("dt_family")

    # Reported per opener, not as one verdict. Collapsing them hid the interesting case: on
    # 2026-07-22 the C-Spin answer is identical across both readings while the DT answer moves
    # (one board lands 4 cells from a DT-family page that the narrow set does not contain), and
    # a single "the answer moved" sentence made the stable half look unstable too.
    # The verdict tracks the REPORTABLE quantity — how many rounds land within the threshold —
    # not the minimum distance. The minimum legitimately moves when a wider set simply contains
    # more pages to be near; judging on it made 2026-08-09 read as "the answer moved" when both
    # readings put zero rounds inside the threshold, i.e. when nothing reportable had changed.
    # A moved minimum that leaves the count alone is said as the smaller thing it is.
    def verdict(subject, n_in, w_in, n_min, w_min):
        if n_in != w_in:
            return f"{subject}闊咗之後個答案有郁，所以要連住佢係邊個集出嚟先講得通"
        if n_min != w_min:
            return f"{subject}窄定闊都係同一個答案（最近嗰版遠近唔同咗，但 {near} 格以內嘅回合數一樣）"
        return f"{subject}窄定闊都係同一個答案"

    stable = (verdict("C-Spin ", c_in, ct_in, c_min, ct_min) + "；"
              + verdict("DT ", d_in, df_in, d_min, df_min))
    return (
        f"「最近」係<strong>逐格數唔同</strong>（Hamming），"
        f"淨係同格數一樣嘅定式頁比，正著同反轉都比。"
        f"揀邊啲頁做「C-Spin」同「DT 砲」本身就係一個判斷，所以呢度<strong>窄同闊兩種讀法都報</strong>："
        f"C-Spin 照名揀得 {sets['cspin']['openers']} 個定式（{sets['cspin']['pages']} 頁），"
        f"加埋 TKI 就 {sets['cspin_or_tki']['openers']} 個（{sets['cspin_or_tki']['pages']} 頁）；"
        f"DT 砲照名揀 {sets['dt_cannon']['openers']} 個（{sets['dt_cannon']['pages']} 頁），"
        f"闊到「個名有 DT」就 {sets['dt_family']['openers']} 個（{sets['dt_family']['pages']} 頁）。"
        f"{stable}——C-Spin 最近 {_cells(c_min)}／{_cells(ct_min)}，"
        f"DT 最近 {_cells(d_min)}／{_cells(df_min)}，"
        f"{near} 格以內嘅回合數係 {c_in}／{ct_in} 同 {d_in}／{df_in}。"
    )


def _coverage_note(data):
    """The caveat that bounds every first-bag null, stated as a limit of the DATA."""
    sets = data["catalogue"]["sets"]
    names = sets["cspin"]["names"]
    listed = "、".join(html.escape(n.split("{")[0].strip()) for n in names) if names else "冇"
    return (
        "<strong>呢個零係俾定式庫嘅覆蓋率封住嘅，唔係俾比對程式封住。</strong>"
        f"照個名揀出嚟嘅所謂「C-Spin」頁得 {sets['cspin']['openers']} 個定式，"
        f"而且個個都可疑：{listed}——"
        "第一個自己個名就叫「假」（偽TKI），第二個係名尾啱啱好有嗰幾個字母，"
        "第三個係一版夾埋八個名嘅合併頁。"
        "所以呢一格數講得出嘅係「唔係<em>呢啲</em>頁」，"
        "<strong>永遠唔係「冇打過 C-Spin」</strong>。"
        "要講到後者，要嘅係更闊嘅定式庫（或者由 J、L 搭蓋冚單格井去<em>窮舉</em>成個家族），"
        "唔係更好嘅比對程式——比對程式已經逐頁餵返自己、認得返鏡像、"
        "亂砌嘅板認唔出、差一行嘅板一定更遠。"
    )


def _slot_note(data):
    """THE control. This paragraph is why the share may be printed at all."""
    rows = {r["lines"]: r for r in data["slot_geometry"]["rows"]}
    three, two = rows.get(3), rows.get(2)
    total = sum(r["n"] for r in data["slot_geometry"]["rows"])
    if not three or three["share_x1000"] is None or not two or two["share_x1000"] is None:
        return ("呢個 session 可核嘅 T-spin 唔夠，砌唔到對照，所以呢個表只係列數，"
                "唔可以攞嚟講定式。")
    return (
        f"<strong>睇個對照，唔好淨係睇 {_pct(three['share_x1000'])}。</strong>"
        f"消三行嘅 T-spin 有 {_pct(three['share_x1000'])} 撞到 wiki 個槽位，"
        f"但消兩行嘅只有 {_pct(two['share_x1000'])}。"
        f"兩個數擺埋一齊講嘅係：呢個測試分得出「三行定兩行」，分唔出「係咪 C-Spin 開局」——"
        "T-Spin Triple 本來就要一隻直放嘅 T 塞入一條有蓋單格井，"
        "個形就係咁，同用邊個開局打出嚟冇關係。"
        f"所以呢 {total} 個可核 T-spin 入面撞到槽位嗰啲，"
        "<strong>唔可以當成 C-Spin 嘅次數</strong>，只可以當成「個窿位嘅形同 wiki 畫嘅一樣」。"
    )


def _ordering_table(data):
    ps = _players(data)
    head = ["<th>玩家</th>", "<th>可核回合</th>", "<th>兩種 T-spin 都有</th>",
            "<th>C-Spin 次序（先 Triple）</th>", "<th>DT 砲次序（先 Double）</th>",
            "<th>第一個 Triple 喺第幾手（min／中位／max）</th>"]
    rows = []
    for p in ps:
        ft = p["first_triple_lock"]
        span = "—" if ft["min"] is None else f"{ft['min']}／{ft['median']}／{ft['max']}"
        rows.append(
            "          <tr>"
            f"<td>{html.escape(p['user'])}</td>"
            f"<td class=\"mono\">{p['rounds_scored']}</td>"
            f"<td class=\"mono\">{p['rounds_with_both']}</td>"
            f"<td class=\"mono\">{p['cspin_order']}</td>"
            f"<td class=\"mono\">{p['dt_order']}</td>"
            f"<td class=\"mono\">{span}</td>"
            "</tr>")
    return head, rows


def _first_bag_table(data):
    ps = _players(data)
    fb = {p["user"]: p for p in data["first_bag"]["players"]}
    head = ["<th>定式集</th>"]
    for p in ps:
        u = html.escape(p["user"])
        head.append(f"<th>{u} 最近</th>")
        head.append(f"<th>{u} ≤{data['near_cells']} 格</th>")
    rows = []
    for key, label in SET_ROWS:
        cells = [f"<td>{label.format(openers=data['catalogue']['openers'])}</td>"]
        for p in ps:
            n = fb.get(p["user"], {}).get("nearest", {}).get(key)
            if n is None:
                cells.append('<td class="mono">—</td><td class="mono">—</td>')
                continue
            cells.append(f'<td class="mono">{_cells(n["min_cells"])}</td>'
                         f'<td class="mono">{n["within_threshold"]}</td>')
        rows.append("          <tr>" + "".join(cells) + "</tr>")
    return head, rows


def _slot_table(data):
    head = ["<th>消行數</th>", "<th>可核 T-spin</th>", "<th>撞到 wiki 槽位</th>", "<th>比率</th>"]
    rows = []
    for r in sorted(data["slot_geometry"]["rows"], key=lambda r: -r["lines"]):
        rows.append(
            "          <tr>"
            f"<td class=\"mono\">{r['lines']} 行</td>"
            f"<td class=\"mono\">{r['n']}</td>"
            f"<td class=\"mono\">{r['matched']}</td>"
            f"<td class=\"mono\">{_pct(r['share_x1000'])}</td>"
            "</tr>")
    return head, rows


def _table(head, rows):
    return ['    <div class="scroll-x">',
            '      <table class="appendix-table">',
            '        <thead>',
            '          <tr>' + "".join(head) + '</tr>',
            '        </thead>',
            '        <tbody>',
            *rows,
            '        </tbody>',
            '      </table>',
            '    </div>']


def _no_simplified(markup):
    """The rendered markup must carry no simplified glyph. Authored prose lives in this module,
    so no prose loader's check reaches it; without this the section is the one place in the
    report where 开/个/两 could ship."""
    bad = sorted(set(markup) & SIMPLIFIED)
    if bad:
        raise SystemExit(f"opener_section: simplified glyph(s) {bad} — this report is "
                         "traditional-character Cantonese")
    return markup


def section(data):
    if data is None:
        return None
    cat = data["catalogue"]
    exact = {}
    for p in data["first_bag"]["players"]:
        for e in p["exact_matches"]:
            exact[e["name"]] = exact.get(e["name"], 0) + e["rounds"]
    exact_line = (
        "冇一個開局 bag 同任何一版定式一模一樣。" if not exact else
        "一模一樣嘅開局 bag 有："
        + "、".join(f"{html.escape(n.split('{')[0].strip())} <strong>{k}</strong> 個回合"
                    for n, k in sorted(exact.items(), key=lambda kv: -kv[1]))
        + "。")

    out = [
        '<section id="openers">',
        # Every selector is pinned under #openers, which is what check_generated_css requires and
        # what the .rec-grid incident taught: a generated section's <style> lands in the BODY, so
        # at equal specificity it beats the report's own stylesheet and a bare `h3` rule here
        # would restyle the chart headings three sections up. No new class names, no colours —
        # the only thing wrong without this is that the sub-headings sit flush against the table
        # above them, which reads as though they label it rather than what follows.
        '  <style>',
        '    #openers h3 { margin: 2.2rem 0 .1rem; font-size: 1.05rem; }',
        '    #openers h3:first-of-type { margin-top: 1.4rem; }',
        '  </style>',
        '  <div class="wrap-wide">',
        '    <div class="eyebrow">模擬器推導 · 唔屬於信任鏈</div>',
        '    <h2 class="section-title">C-Spin 同 DT 砲（未經證明）</h2>',
        '',
        '    <div class="method-note">',
        '      <p><strong>同上面 T-Spin Forecast 一樣，呢節唔屬於信任鏈，請當佢係探索性資料。</strong>'
        '上面每個數都係兩個獨立 parser 抽出嚟、再由 Dafny 引理逐條證明；'
        '呢節嘅數由<strong>一個 replay 模擬器</strong>重跑操作記錄推導出嚟，得一份實作，'
        f'所以<strong>冇 claim 編號、冇 ✓ 標記</strong>。</p>',
        '      <p>兩個定式，講嘅係同一對 T-spin 嘅兩個<strong>次序</strong>：'
        '<strong>DT 砲</strong>（開幕DT砲，Double Triple Cannon）係<em>先 Double 後 Triple</em>；'
        '<strong>C-Spin</strong> 係<em>先 Triple 後 Double</em>。'
        '次序係 <code>facts.json</code> 冇嘅嘢——佢淨係數到 <code>tspin_doubles</code> 同 '
        '<code>tspin_triples</code> 各有幾多個，數唔到邊個行先——'
        '所以呢條問題本來就只有模擬器答得到，亦都因為咁佢擺喺呢一節而唔係上面。</p>',
        '    </div>',
        '',
        '    <h3>一 · 次序</h3>',
        '    <div class="method-note"><p>' + _ordering_note(data) + '</p></div>',
        *_table(*_ordering_table(data)),
        '',
        '    <h3>二 · 開局第一個 bag 對唔對得上社群定式庫</h3>',
        '    <div class="method-note">',
        f'      <p>七手落完、冇消行、冇食垃圾嘅板一定有 28 格。'
        f'攞佢同定式庫入面每一版同格數嘅圖比：'
        f'{cat["pages"]} 版圖、{cat["openers"]} 個定式，'
        f'出處係 <code>{html.escape(str(cat["source"]))}</code>，'
        f'釘死喺 commit <code>{html.escape(str(cat["commit"]))[:8]}</code>。'
        f'呢個 session 有 <strong>{data["first_bag"]["clean"]}</strong> 個乾淨開局 bag'
        f'（全部 {data["first_bag"]["rounds"]} 個回合入面）。{exact_line}</p>',
        '      <p>' + _first_bag_note(data) + '</p>',
        '    </div>',
        *_table(*_first_bag_table(data)),
        '    <div class="method-note"><p>' + _coverage_note(data) + '</p></div>',
        '',
        '    <h3>三 · 槽位幾何對唔對得上 wiki 畫嘅 C-Spin</h3>',
        '    <div class="method-note">',
        f'      <p>攞 harddrop.com/wiki/C-Spin 自己嗰 '
        f'{data["wiki_cspin"]["placements"]} 個擺法做尺：每個擺法抽出隻 T 塞入去嗰陣、'
        '佢周圍嗰笪位嘅「有格／冇格」形狀（隻 T 自己嗰四格當冇），'
        '再攞真實對局落子前一刻同一笪位比。形一樣就係同一個槽位，唔理佢喺板邊個位。</p>',
        '    </div>',
        *_table(*_slot_table(data)),
        '    <div class="method-note"><p>' + _slot_note(data) + '</p></div>',
        '  </div>',
        '</section>',
    ]
    return _no_simplified("\n".join(out))

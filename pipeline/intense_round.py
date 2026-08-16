"""最癲一局 — the session's most intense round, in detail.

The round is whichever one `generators.most_intense_round` selects: the highest
combined VS among rounds of `QUALIFYING_MS` or more. That qualifier is not
decoration — VS is a per-minute rate, so a sum of two of them carries both
denominators and a 20-second round would win this contest on arithmetic alone.

Why the section exists. Every other per-round number in the report lives in
逐局全數據, where all rounds get the same row and none gets an explanation. This
takes one round and says *how it was won*, which is a different question from
*what the numbers were* — and the answer is often not the one the attacking
columns suggest. In three of the six sessions the winner of this round was behind
on APM, on attack, or on both.

Every figure is read out of the claims' own specs — the operands of what the
verifier proved — never re-derived from facts.json. A session whose claims are
missing gets no section rather than a re-derived one. Same rule as pc_section,
for the same reason: a section that recomputes can print a number no lemma covers.

What this section must never become. It is ONE round. It can show that a mechanism
operated; it cannot show a tendency, and the closing note says so in those words.
The session-level version of the same question is 數據對決's job.

The lede states ONE corpus result, and stating it strengthens the n=1 caveat rather
than weakening it. The old rule here was that the corpus is never restated in this
section; that rule was protecting against the section claiming a tendency FROM its one
round, and a corpus figure labelled with its own n, its adjustment and its controls is
the opposite of that — it is what lets the closing note say "the corpus says the
mechanism is real, this round is the illustration, and neither is the other". What is
still banned is a corpus figure the round appears to license, or the round's numbers
generalised without one.

The result: over 380 decided rounds in six sessions, downstacking is the only printed
measure that becomes MORE decisive as rounds intensify — paired AUC across terciles of
combined VS runs 62.3 → 65.0 → 83.5 for the per-piece rate (Spearman rho +0.210 against
intensity, Holm-adjusted p 0.0002 over the 20 columns tested; raw 清走 +0.200, p 0.0020).
It survives both controls the closing note quotes: it is not round LENGTH (the same test
against duration is rho +0.058, Holm p 1.000, while APM's and 攻擊's apparent decay IS a
length effect at rho −0.187 / −0.184, Holm p 0.0040 / 0.0098 — which is why the attacking
lede this section used to carry was not supported as stated), and it is not the loser
dying with garbage still on the board (normalising by how much garbage ARRIVED strengthens
it to rho +0.236, and 食 — which carries that same death bias but no skill — does not
trend, rho +0.096, p 0.06). That death bias is real all the same, and the note keeps it.
"""
import html

from pipeline import claim_cards
from pipeline.claims.build_claims import SIMPLIFIED
from pipeline.claims.generators import INTENSE_AXES, axis_verdict

# Printed in this order. The labels match the claim Cantonese so a reader moving
# between the table and the claims island sees the same words.
#
# 入力 and 手順失誤 are gone — see the note above `INTENSE_AXES` in generators.py for the
# measurements. They were the only two rows the section had to talk the reader OUT of, and
# the disclaimer paragraph that did so went with them; keeping one of the two would have
# left that paragraph paying rent for a single row. They are also the only rows here that
# 逐局全數據 does not already print, so a reader who wants them still has nowhere fewer
# places to look than before: they were never anywhere else either, and a column whose
# direction reverses with exposure is not made trustworthy by being proved.
FIELDS = [
    ("apm_x1000", "APM", "r1"),
    ("pps_x1000", "PPS", "r2"),
    ("vs_x1000", "VS", "r1"),
    ("pieces", "粒數", None),
    ("garbage_attack", "攻擊", None),
    ("garbagesent", "射埋", None),
    ("garbagereceived", "食", None),
    ("garbage_cleared", "清走", None),
    ("lines", "行數", None),
    ("maxspike", "最大單波", None),
    ("topbtb", "最高 B2B", None),
]

# field -> label, and field -> axis, both derived from the generator's own axis map so the
# section cannot group the sentence differently from the way the claim counted it.
EDGE_LABELS = {f: label for _axis, cols in INTENSE_AXES for f, label in cols}
EDGE_AXIS = {f: axis for axis, cols in INTENSE_AXES for f, _label in cols}

CSS = """
<style>
/* ---------- 最癲一局 (generated) ---------- */
/* Scoped under #intense-round and every class carries the ir- prefix. A generated
   section's <style> is injected into the body, so at equal specificity it beats the
   report's own stylesheet — 全場之最 once defined .rec-grid and silently collapsed
   the coaching columns that had used that name for months. */
#intense-round .ir-scroll { overflow-x: auto; margin: 1.3rem 0 0; }
#intense-round .ir-table { width: 100%; border-collapse: collapse; font-size: .86rem;
  min-width: 30rem; }
#intense-round .ir-table th, #intense-round .ir-table td { padding: .5rem .7rem;
  border-bottom: 1px solid var(--border); text-align: right; }
#intense-round .ir-table th:first-child, #intense-round .ir-table td:first-child {
  text-align: left; }
#intense-round .ir-table thead th { font-family: var(--font-mono); font-size: .64rem;
  letter-spacing: .07em; text-transform: uppercase; color: var(--muted); font-weight: 600; }
#intense-round .ir-table td.ir-num { font-variant-numeric: tabular-nums; }
/* The losing side of a comparison the winner lost — the section's whole point, so it
   is marked rather than left for the reader to diff two columns by eye. */
#intense-round .ir-table td.ir-behind { font-weight: 700; }
#intense-round .ir-who { display: flex; align-items: center; gap: .45rem; white-space: nowrap; }
#intense-round .ir-dot { width: .5rem; height: .5rem; border-radius: 50%; flex: none; }
/* Positional classes, legacy tokens: the four earliest reports' :root predates the
   positional --p1/--p2 slots and defines only --yachi/--pinglamb. Same rule
   build_round_table follows. --accent is NOT used anywhere here: it is defined only
   on .match-card[data-winner=...] and resolves empty elsewhere, which silently
   invalidates any color-mix() that references it. */
#intense-round .ir-dot.is-p1 { background: var(--yachi); }
#intense-round .ir-dot.is-p2 { background: var(--pinglamb); }
#intense-round .ir-cid { font-family: var(--font-mono); font-size: .6rem; color: var(--muted); }
#intense-round .ir-find { margin: 1.2rem 0 0; font-size: .95rem; line-height: 1.9; }
#intense-round .ir-split { margin: 1.1rem 0 0; font-size: .88rem; line-height: 1.85; }
#intense-round .ir-note { margin: .9rem 0 0; font-size: .8rem; line-height: 1.8;
  color: var(--muted); }
@media print {
  #intense-round .ir-scroll { overflow-x: visible; }
}
</style>
"""


def _r1(x):
    return f"{x // 100 / 10:.1f}"


def _r2(x):
    return f"{x // 10 / 100:.2f}"


def _fmt(value, how):
    return {"r1": _r1, "r2": _r2}[how](value) if how else f"{value:,}"


def _conjuncts(spec):
    spec = spec or {}
    return spec.get("xs", []) if spec.get("p") == "and" else [spec]


def _profile(claim):
    """{player, match, round, fields:{f: v}} from an `intense_round_profile` claim."""
    out, where = {}, None
    for x in _conjuncts(claim.get("spec")):
        if x.get("p") == "eq" and (x.get("a") or {}).get("e") == "round" \
                and (x.get("b") or {}).get("e") == "lit":
            a = x["a"]
            out[a["f"]] = x["b"]["v"]
            where = (a["mi"], a["ri"], a["pl"])
    if not where:
        return None
    return {"player": where[2], "match": where[0] + 1, "round": where[1] + 1,
            "fields": out, "id": claim["id"], "verified": claim["verified"]}


def _edges(claim):
    """{winner, behind:[field], ahead:[field], level:[field]} from `intense_round_edges`."""
    winner, behind, ahead, level = None, [], [], []
    for x in _conjuncts(claim.get("spec")):
        if x.get("p") == "round_winner":
            winner = x["pl"]
            continue
        a, b = x.get("a") or {}, x.get("b") or {}
        if a.get("e") != "round" or b.get("e") != "round" or a.get("f") != b.get("f"):
            continue
        # `.get(x.get("p"), [])` typed as `str | None` into a `str` key — a spec with no `p`
        # would look up None, miss, and append to the throwaway list, i.e. silently drop an edge
        # rather than fail. Read the operator once and skip when it is absent.
        op = x.get("p")
        if op in ("lt", "gt", "eq"):
            {"lt": behind, "gt": ahead, "eq": level}[op].append(a["f"])
    if winner is None:
        return None
    return {"winner": winner, "behind": behind, "ahead": ahead, "level": level,
            "id": claim["id"], "verified": claim["verified"]}


def _dir(edges, f):
    """"behind" / "ahead" / "level" for one column, out of the proved edge claim.

    Raises rather than defaulting. A column named in `INTENSE_AXES` but absent from the
    claim means the ledger and the axis map disagree about what was compared, and the
    plausible default ("level") would silently drop it from the axis count — the same
    shape as the `?? 0` that published 「一個 Perfect Clear 都冇出過」 for five sessions.
    """
    for key in ("behind", "ahead", "level"):
        if f in edges[key]:
            return key
    raise SystemExit(f"intense_round: {edges['id']} proves no direction for {f!r}, but "
                     "generators.INTENSE_AXES counts it — regenerate the ledger")


def _pinned_rate(between):
    """The value a `between(mul(lit(k), round(...)), v*den, (v+1)*den)` pins.

    Recovered rather than recomputed: `den = hi - lo` and `v = lo // den`, so the
    figure printed is arithmetically the one inside the proved bound. Returns
    (player, field, v) or None when the conjunct is some other shape.
    """
    x = between.get("x") or {}
    if x.get("e") != "mul":
        return None
    inner = x.get("b") or {}
    if inner.get("e") != "round":
        return None
    den = between["hi"] - between["lo"]
    if den <= 0:
        return None
    return inner["pl"], inner["f"], between["lo"] // den


def _rates(claim):
    """{field, values:{player: x1000}} from an `intense_round_*_rate` claim."""
    vals, field = {}, None
    for x in _conjuncts(claim.get("spec")):
        if x.get("p") != "between":
            continue
        got = _pinned_rate(x)
        if got:
            pl, field, v = got
            vals[pl] = v
    if not vals:
        return None
    return {"field": field, "values": vals, "id": claim["id"],
            "verified": claim["verified"]}


def _vs_split(claim):
    """{player, attack, downstack, residual_x1000} from `intense_round_vs_split`."""
    terms, resid, player = {}, None, None
    for x in _conjuncts(claim.get("spec")):
        if x.get("p") != "between":
            continue
        got = _pinned_rate(x)
        if got:
            player, f, v = got
            terms[f] = v
            continue
        # the residual bound: between(sub(...), -resid, resid + 1) — its own x is a
        # `sub`, not a `mul`, which is what distinguishes it from the two term pins.
        if (x.get("x") or {}).get("e") == "sub":
            resid = x["hi"] - 1
    if player is None or "garbage_attack" not in terms or "garbage_cleared" not in terms:
        return None
    return {"player": player, "attack": terms["garbage_attack"],
            "downstack": terms["garbage_cleared"], "residual": resid,
            "id": claim["id"], "verified": claim["verified"]}


def collect(report_dir):
    """Everything the section prints, read out of the proved claims."""
    claims = claim_cards.load(report_dir)
    by_family = {}
    for c in claims:
        by_family.setdefault(c["family"], []).append(c)

    profiles = [p for p in (_profile(c) for c in by_family.get("intense_round_profile", [])) if p]
    if not profiles:
        return None
    edges = next((e for e in (_edges(c) for c in by_family.get("intense_round_edges", [])) if e), None)
    rates = {}
    for fam in ("intense_round_attack_rate", "intense_round_downstack_rate"):
        got = next((r for r in (_rates(c) for c in by_family.get(fam, [])) if r), None)
        if got:
            rates[got["field"]] = got
    splits = [s for s in (_vs_split(c) for c in by_family.get("intense_round_vs_split", [])) if s]
    return {"profiles": profiles, "edges": edges, "rates": rates, "splits": splits}


def build(facts, report_dir):
    data = collect(report_dir)
    if not data or not data["edges"]:
        return None
    profiles, edges, rates, splits = (data["profiles"], data["edges"],
                                      data["rates"], data["splits"])
    p1 = facts["players"][0]
    win = edges["winner"]
    ref = profiles[0]
    # Winner's column first: the section's sentences are all about what the winner
    # did or did not lead on, and a reader should not have to hunt for that column.
    cols = sorted(profiles, key=lambda p: p["player"] != win)
    ids = sorted({p["id"] for p in profiles} | {edges["id"]}
                 | {r["id"] for r in rates.values()} | {s["id"] for s in splits})
    pending = [p for p in profiles if not p["verified"]] + \
              ([edges] if not edges["verified"] else []) + \
              [r for r in rates.values() if not r["verified"]] + \
              [s for s in splits if not s["verified"]]

    out = [CSS, '<section id="intense-round">', '  <div class="wrap">',
           '    <div class="eyebrow">最癲一局 · THE ROUND BOTH SWUNG HARDEST</div>',
           f'    <h2 class="section-title">全晚打得最癲嘅一局：第 {ref["match"]} 場第 '
           f'{ref["round"]} 局</h2>',
           '    <p class="section-lede">呢一局係成晚<strong>兩邊 VS 加埋最高</strong>嗰局——'
           '即係雙方都攻得最狠嗰一局。'
           '揀嘅時候淨係計打足一分鐘以上嘅局：VS 係「每分鐘」嘅速率，'
           '短局個分母細，唔設下限嘅話贏嘅次次都係最短嗰局。'
           '點解要專登揀最癲嗰局出嚟拆：'
           '<strong>局打得越癲，越決定勝負嗰樣係「清走」，唔係攻擊</strong>。'
           '呢句唔係由下面呢一局睇出嚟嘅——係喺六個 session、380 局有勝負嘅局度量返嚟：'
           '將全部局按「兩邊 VS 加埋」由低到高分三份，'
           '每粒棋清走呢個速率分辨到邊個贏嘅準確度，'
           '由 62.3% 升到 65.0% 再升到 83.5%'
           '（Spearman rho ＋0.210，Holm 校正後 p 0.0002），'
           '而攻擊同 APM 完全冇呢個升勢。'
           '下面呢一局係<strong>個例子</strong>，唔係個證據——'
           '兩個控制實驗喺最尾嗰段。'
           '每個數都係由 claim 本身證嗰條式度攞返嚟，'
           '唔係喺呢度重新計一次。</p>',
           '    <div class="ir-scroll">',
           '      <table class="ir-table">',
           '        <thead><tr><th>數據</th>'
           + "".join('<th><span class="ir-who"><span class="ir-dot '
                     + ("is-p1" if c["player"] == p1 else "is-p2") + '"></span>'
                     + html.escape(c["player"])
                     + ("（贏）" if c["player"] == win else "") + '</span></th>'
                     for c in cols)
           + '</tr></thead>',
           '        <tbody>']
    for f, label, how in FIELDS:
        cells = []
        for c in cols:
            v = c["fields"].get(f)
            behind = (c["player"] == win and f in edges["behind"])
            cls = "ir-num ir-behind" if behind else "ir-num"
            cells.append(f'<td class="{cls}">'
                         + ("—" if v is None else _fmt(v, how)) + '</td>')
        out.append(f'          <tr><td>{label}</td>' + "".join(cells) + '</tr>')
    out += ['        </tbody>', '      </table>', '    </div>']

    # The finding. Two shapes, because the selected round genuinely comes both ways:
    # in three of six sessions the winner trailed on real attacking columns, and in
    # the others he simply led. The flat case is printed as the result it is — a
    # generator that only had the dramatic sentence would be writing for the sessions
    # it liked.
    lose = [c["player"] for c in cols if c["player"] != win]
    lose = lose[0] if lose else ""
    # Count AXES, not columns. APM is 攻擊 over the player's own clock and PPS is 粒數 over
    # the same, so a flat count says "he lost two things" where the data says one. The
    # bold cells stay per-column — every column's direction is proved, so every one that
    # ran against the winner is still marked — and the sentence explains why there are
    # more bold cells than axes. Grouping comes from the generator's own map, so the
    # number quoted here and the number inside the claim cannot drift apart.
    behind_ax = [a for a, _c in INTENSE_AXES
                 if axis_verdict([_dir(edges, f) for f, _l in _c]) == "behind"]
    ahead_ax = [a for a, _c in INTENSE_AXES
                if axis_verdict([_dir(edges, f) for f, _l in _c]) == "ahead"]
    paired = [a for a, c in INTENSE_AXES if len(c) > 1]
    if behind_ax:
        names = "、".join(behind_ax)
        # The bold cells are per-column, so there are more of them than axes exactly when a
        # trailing axis is one of the two paired ones. Saying so unconditionally was wrong
        # on 2026-07-28, whose only trailing axis is the singleton 行數 — one cell, one
        # axis. The counts are printed rather than described for the same reason: a reader
        # can check them against the table, which a claim about their relative size is not.
        n_cells = len(edges["behind"])
        gap = (f'：<strong>{n_cells} 格、{len(behind_ax)} 條軸</strong>——'
               f'因為 APM 就係攻擊除返自己嘅時間、PPS 就係粒數除返自己嘅時間，'
               f'同一件事數兩次會將個發現吹大，所以數「輸幾多樣」係數軸，唔係數格。'
               if n_cells > len(behind_ax) else '。')
        out.append(f'    <p class="ir-find">贏嘅係 <strong>{html.escape(win)}</strong>，'
                   f'但佢喺 <strong>{names}</strong> 呢 {len(behind_ax)} 條軸'
                   f'{"都" if len(behind_ax) > 1 else ""}<strong>輸蝕</strong>'
                   f'畀 {html.escape(lose)}——'
                   f'即係話呢局<strong>唔係攻得多嗰個贏</strong>。'
                   f'表入面粗體嗰啲就係佢落後嗰幾格{gap}</p>')
    else:
        rest_ax = [a for a, _c in INTENSE_AXES if a not in behind_ax and a not in ahead_ax]
        # Mirrors the claim's three branches — a level axis is named as level, never
        # swept under 「每一條軸都領先」 while the list quietly omits it.
        lead = (f'而佢喺 <strong>{"、".join(ahead_ax)}</strong> 每一條軸都'
                f'<strong>領先</strong>' if not rest_ax else
                f'佢喺 <strong>{"、".join(ahead_ax)}</strong> 領先，'
                f'喺 <strong>{"、".join(rest_ax)}</strong> 打成平手，一條軸都冇輸')
        out.append(f'    <p class="ir-find">贏嘅係 <strong>{html.escape(win)}</strong>，'
                   f'{lead}——'
                   f'呢局冇得拗，唔使靠守就贏咗。'
                   f'呢個結果本身值得記低：最癲嘅一局唔係次次都有反轉。'
                   f'（{"、".join(paired)}每條軸都係一個總數加返佢自己嘅速率，'
                   f'兩格當一條軸計。）</p>')

    # The two per-piece rates, which is where these rounds are usually decided.
    if rates:
        bits = []
        for f, label in (("garbage_attack", "每粒棋攻擊"), ("garbage_cleared", "每粒棋清走")):
            r = rates.get(f)
            if not r:
                continue
            pairs = "、".join(f'{html.escape(p)} 約 {r["values"][p] / 1000:.3f}'
                             for p in [c["player"] for c in cols] if p in r["values"])
            bits.append(f'<strong>{label}</strong>：{pairs}')
        out.append('    <p class="ir-split">' + "；".join(bits) + '。'
                   '兩個率都係用「乘返上去」嘅方式證嘅——'
                   'claim 裏面冇除數，所以比較係 <code>甲×乙嘅粒數</code> 對 '
                   '<code>乙×甲嘅粒數</code>，印出嚟嗰三個位就係個界證住嘅數。</p>')

    # The VS split. This is the one place the section explains an inversion instead of
    # merely pointing at it, so it carries its own caveat: the identity is OBSERVED in
    # this data, not a published formula, and the claim is a bound, never an equality.
    if splits:
        bits = []
        for s in sorted(splits, key=lambda s: s["player"] != win):
            bits.append(f'{html.escape(s["player"])} 嘅 VS ＝ 攻 約 {_r1(s["attack"])} '
                        f'＋ 清垃圾 約 {_r1(s["downstack"])}')
        out.append('    <p class="ir-split">' + "；".join(bits) + '。'
                   'VS 唔淨係攻擊——<strong>清走幾多垃圾都計埋落去</strong>，'
                   '所以一個攻少啲但清得快好多嘅人，VS 可以高過對面。'
                   '呢個拆法係<strong>喺呢批數據度睇返出嚟</strong>嘅，'
                   '唔係邊度公佈過嘅公式，所以 claim 證嘅係'
                   '「兩邊加埋同實際 VS 相差唔超過幾多」，'
                   '<strong>唔係「等於」</strong>。</p>')

    out.append('    <p class="ir-note">'
               '讀呢節要記住：<strong>呢度得一局</strong>。'
               '一局可以話畀你聽「有件事發生咗」，'
               '<strong>話唔到你聽「呢個人一向係咁」</strong>。'
               '開頭嗰個清走升勢係成個 corpus 嘅結果，<strong>唔係呢一局證出嚟</strong>；'
               '呢一局淨係做個例子，話畀你睇件事點樣發生。'
               '兩者邊個都唔證明到對方——'
               '成晚嘅走勢喺「數據對決」嗰節，逐局嘅原始數字喺「逐局全數據」。'
               '另外：<strong>射埋</strong>係對面掟過嚟排緊隊嗰啲，'
               '<strong>食</strong>係抵銷完之後真係跌落塊板嗰啲，兩個唔同數。</p>')
    # The corpus figure in the lede is the one number here that is not a claim, so the
    # two things that could manufacture it are stated where the reader meets it. Both
    # were measured before the lede was written, not after — the death bias in
    # particular is an objection this section already documented against itself.
    out.append('    <p class="ir-note">'
               '個升勢查咗兩樣嘢先敢寫：'
               '一，<strong>唔係局長效應</strong>——同一個測試改成對住局嘅長度，'
               'rho 得 ＋0.058、Holm 校正後 p 1.000，即係乜都冇；'
               '反而 APM 同攻擊嗰種「越癲越唔準」嘅樣，先至係局長效應'
               '（rho −0.187 同 −0.184，p 0.0040 同 0.0098）——'
               '所以呢節以前用攻擊做主打嗰句，其實撐唔住。'
               '二，<strong>唔係「垃圾掟多咗、輸嗰個死咗冇得清」</strong>——'
               '除返收到幾多垃圾之後個升勢仲強（rho ＋0.236），'
               '而「食」呢個帶住同一個死亡偏差、但唔帶技術嘅數，冇顯著升勢'
               '（rho ＋0.096，p 0.06）。'
               '不過個偏差本身係真嘅，唔好當佢唔存在：'
               '<strong>清走同食對輸嗰個嚟講係有偏差嘅</strong>，'
               '因為佢死嗰陣塊板上面嗰啲垃圾，按定義就係冇清到。</p>')
    out.append('    <p class="ir-note">Claim：'
               + html.escape(" · ".join(ids))
               + (" ⏳" if pending else " ✓") + '</p>')
    out += ['  </div>', '</section>']

    markup = "\n".join(out)
    # This section's Cantonese is authored here, not in prose/*.json, so no loader's
    # glyph check reaches it — the same hole pc_section and opener_section close the
    # same way. 净/实/约 have all been caught in review in this repo before.
    bad = sorted(set(markup) & SIMPLIFIED)
    if bad:
        raise SystemExit(f"intense_round: simplified glyph(s) {bad} — this report is "
                         "traditional-character Cantonese")
    return markup

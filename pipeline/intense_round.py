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
The session-level version of the same question is 數據對決's job, and the corpus
version is the AUC block in CLAUDE.md — neither is restated here.
"""
import html

from pipeline import claim_cards
from pipeline.claims.build_claims import SIMPLIFIED

# Printed in this order. The labels match the claim Cantonese so a reader moving
# between the table and the claims island sees the same words.
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
    ("inputs", "入力", None),
    ("finesse_faults", "手順失誤", None),
]

EDGE_LABELS = {
    "apm_x1000": "APM", "pps_x1000": "PPS", "pieces": "粒數",
    "garbage_attack": "攻擊", "maxspike": "最大單波", "topbtb": "最高 B2B",
    "lines": "行數",
}

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
        {"lt": behind, "gt": ahead, "eq": level}.get(x.get("p"), []).append(a["f"])
    if winner is None:
        return None
    return {"winner": winner, "behind": behind, "ahead": ahead, "level": level,
            "id": claim["id"], "verified": claim["verified"]}


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
           '下面每個數都係由 claim 本身證嗰條式度攞返嚟，'
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
    if edges["behind"]:
        names = "、".join(EDGE_LABELS.get(f, f) for f in edges["behind"])
        out.append(f'    <p class="ir-find">贏嘅係 <strong>{html.escape(win)}</strong>，'
                   f'但佢喺 <strong>{names}</strong> 呢 {len(edges["behind"])} 樣'
                   f'都<strong>輸蝕</strong>畀 {html.escape(lose)}——'
                   f'即係話呢局<strong>唔係攻得多嗰個贏</strong>。'
                   f'表入面粗體嗰啲就係佢落後嗰幾格。</p>')
    else:
        names = "、".join(EDGE_LABELS.get(f, f) for f in edges["ahead"])
        out.append(f'    <p class="ir-find">贏嘅係 <strong>{html.escape(win)}</strong>，'
                   f'而佢喺 <strong>{names}</strong> 每一樣都<strong>領先</strong>——'
                   f'呢局冇得拗，唔使靠守就贏咗。'
                   f'呢個結果本身值得記低：最癲嘅一局唔係次次都有反轉。</p>')

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
               '<strong>話唔到你聽「呢個人一向係咁」</strong>——'
               '成晚嘅走勢喺「數據對決」嗰節，逐局嘅原始數字喺「逐局全數據」。'
               '另外三樣：<strong>射埋</strong>係對面掟過嚟排緊隊嗰啲，'
               '<strong>食</strong>係抵銷完之後真係跌落塊板嗰啲，兩個唔同數；'
               '<strong>清走／食</strong>對輸嗰個嚟講係有偏差嘅，'
               '因為佢死嗰陣塊板上面嗰啲垃圾按定義就係冇清到；'
               '<strong>入力同手順失誤唔預測邊個贏</strong>——'
               'KPP 喺六個 session 嘅 AUC 都喺五成上下，'
               '擺喺度係當負面結果報，唔係當賣點。</p>')
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

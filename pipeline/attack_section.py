"""攻擊由邊度嚟 — where each player's attack per piece comes from. The fourth quarantined section.

Source: the SESSION's `sim/attack-facts.json` (`pipeline/sim/emit-attack-facts.ts`), never
facts.json. Every lock of every round is re-run through the vendored Triangle engine and its
pre-cancel attack (`res.rawGarbage`) is split by clear type, by window (the first `window_pieces`
locks against the rest) and by component (base value, back-to-back, combo, Perfect Clear, and what
the integer model leaves over).

WHY IT IS QUARANTINED, and which half is not. Two anchors are printed with every table: the engine's
attack total against the replay's own `garbage.attack`, and its clear-type counts against the
replay's own `clears.*` counters, per player-round. Both counters are twice-extracted, so where the
anchors agree the COUNT columns are as good as facts.json. How much attack each clear CARRIED, and
the component split, have one implementation, so the section mints no claim ids, carries no ✓ and
says so — the same tier as the forecast, opener and replay sections. `check_attack_section.py` is
the gate that keeps those sentences in.

THE ARITHMETIC IT PRINTS, so a reader can check it. APP = lines per piece x attack per line, both
over the replay's own pieces. The gap between the two players is then split two ways that add to
the same total:
  - by WINDOW: each window's attack over the player's whole pieces, so the two contributions sum
    to the APP gap;
  - by CLEAR TYPE (Kitagawa 1955): for each type k with clears-per-piece r and attack-per-clear v,
    mix_k = (r1 - r0)(v1 + v0)/2 and value_k = (v1 - v0)(r1 + r0)/2, which sum to the gap exactly.
The decomposition uses the ENGINE's attack (the windows), which differs from the replay's total
only in the player-rounds the attack anchor names.

Prose is sign-agnostic: whichever player has the higher APP is the subject, and a tie is its own
sentence. No session in the corpus exercises the reverse sign or the tie, so `--selftest` does.
"""
import html
import json
import os
from fractions import Fraction

from pipeline import fmt
from pipeline.claims.build_claims import SIMPLIFIED

FACTS_REL = os.path.join("sim", "attack-facts.json")

#: print order and Cantonese label of each clear class
LABELS = [("TSD", "T-Spin Double"), ("TST", "T-Spin Triple"), ("Q", "四行（Quad）"),
          ("TSS", "T-Spin Single"), ("T", "三行"), ("D", "兩行"), ("S", "一行"),
          ("mTSS", "Mini T-Spin Single"), ("mTSD", "Mini T-Spin Double")]
COMPONENTS = [("base", "基本值"), ("b2b", "B2B"), ("combo", "Combo"), ("allclear", "全消"),
              ("residual", "其他")]

# The sentences the gate demands. Each is the reason a table beside it may be printed at all.
QUARANTINE_MARKER = "呢節唔屬於信任鏈"
ATTACK_ANCHOR_MARKER = "引擎重算嘅攻擊總數"
COUNT_ANCHOR_MARKER = "每種消行嘅次數"
ENGINE_ONLY_MARKER = "淨係得引擎一份實作"
NOT_A_RESULT_MARKER = "唔係邊個贏"
ROUNDING_MARKER = "各項獨立取整"
REQUIRED = (QUARANTINE_MARKER, ATTACK_ANCHOR_MARKER, COUNT_ANCHOR_MARKER, ENGINE_ONLY_MARKER,
            NOT_A_RESULT_MARKER, ROUNDING_MARKER)
TITLE = "攻擊由邊度嚟（未經證明）"

CSS = """  <style>
    /* Scoped under #attack-sources and every class carries the as- prefix: a generated
       section's <style> lands in the body and beats the report's own stylesheet. */
    #attack-sources h3 { margin: 2.2rem 0 .1rem; font-size: 1.05rem; }
    #attack-sources h3:first-of-type { margin-top: 1.4rem; }
    #attack-sources td.as-num { text-align: right; font-variant-numeric: tabular-nums; }
    #attack-sources .as-dot { display: inline-block; width: .5rem; height: .5rem;
      border-radius: 50%; margin-right: .4rem; }
    #attack-sources .as-dot.is-p1 { background: var(--yachi); }
    #attack-sources .as-dot.is-p2 { background: var(--pinglamb); }
  </style>"""


def facts_path(report_dir):
    return os.path.join(os.path.dirname(os.path.abspath(report_dir)), FACTS_REL)


def load(report_dir):
    path = facts_path(report_dir)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- figures (all declared rules)

def _rate(num, den, dp, site):
    """A non-negative ratio printed at `dp` places, floored: 約 means at least this much."""
    if den == 0:
        return "—"
    return fmt.quant(fmt.permille(num, den, "floor", site=site), dp, "floor", site=site)


def _per100(num, den, site):
    return _rate(100 * num, den, 2, site)


def _signed(frac, site):
    """A signed decomposition term per 100 pieces, ROUNDED (half up) once from the exact value:
    flooring a negative term would overstate its magnitude, and these terms are read against each
    other in both directions, so neither one-sided rule fits."""
    s = fmt.quantf(float(frac * 100), 2, "round", site=site)
    return s if s.startswith("-") else "+" + s


# ---------------------------------------------------------------- the decomposition

def _whole(p):
    """Per-class {n, attack} over both windows, and the engine attack over both."""
    w = p["windows"]
    cls = {k: {"n": w["opener"]["classes"][k]["n"] + w["mid"]["classes"][k]["n"],
               "attack": w["opener"]["classes"][k]["attack"] + w["mid"]["classes"][k]["attack"]}
           for k in w["opener"]["classes"]}
    return cls, w["opener"]["attack"] + w["mid"]["attack"]


def decompose(hi, lo):
    """Exact (Fraction) decomposition of hi's engine APP minus lo's, per piece.

    Returns {"gap", "windows": {opener, mid}, "mix", "value", "terms": [(k, mix_k, value_k)]}.
    Both splits sum to `gap` exactly; that is asserted, not assumed."""
    ch, ah = _whole(hi)
    cl, al = _whole(lo)
    ph, pl = hi["pieces"], lo["pieces"]
    gap = Fraction(ah, ph) - Fraction(al, pl)
    win = {w: Fraction(hi["windows"][w]["attack"], ph) - Fraction(lo["windows"][w]["attack"], pl)
           for w in ("opener", "mid")}
    terms = []
    for k in ch:
        nh, nl = ch[k]["n"], cl[k]["n"]
        rh, rl = Fraction(nh, ph), Fraction(nl, pl)
        vh = Fraction(ch[k]["attack"], nh) if nh else Fraction(0)
        vl = Fraction(cl[k]["attack"], nl) if nl else Fraction(0)
        terms.append((k, (rh - rl) * (vh + vl) / 2, (vh - vl) * (rh + rl) / 2))
    mix = sum((t[1] for t in terms), Fraction(0))
    value = sum((t[2] for t in terms), Fraction(0))
    if win["opener"] + win["mid"] != gap or mix + value != gap:
        raise SystemExit("attack_section: the decomposition does not sum to the gap — "
                         "an artefact field is inconsistent")
    return {"gap": gap, "windows": win, "mix": mix, "value": value, "terms": terms}


def _order(data, players):
    by = {p["user"]: p for p in data["players"]}
    if sorted(by) != sorted(players):
        raise SystemExit(f"attack_section: artefact players {sorted(by)} are not facts.json's "
                         f"{sorted(players)}")
    return [by[u] for u in players]


# ---------------------------------------------------------------- markup

def _who(i, user):
    return f'<span class="as-dot is-p{i + 1}"></span>{html.escape(user)}'


def _table(head, rows):
    return ['    <div class="scroll-x">',
            '      <table class="appendix-table">',
            '        <thead><tr>' + "".join(f"<th>{h}</th>" for h in head) + '</tr></thead>',
            '        <tbody>',
            *['          <tr>' + "".join(rows_i) + '</tr>' for rows_i in rows],
            '        </tbody>',
            '      </table>',
            '    </div>']


def _num(s):
    return f'<td class="as-num">{s}</td>'


def _anchor_note(data):
    a = data["anchor"]
    at, ct = a["attack"], a["counts"]

    def exc(rows, show):
        return "、".join(f"<code>{html.escape(e['file'])}</code> 第 {e['round'] + 1} 局 "
                        f"{html.escape(e['user'])}（{show(e)}）" for e in rows)
    s = (f"{ATTACK_ANCHOR_MARKER}，<strong>{at['agree']} / {at['rounds']}</strong> 個 player-round "
         "同 replay 自己個 <code>garbage.attack</code> counter 一樣")
    s += "。" if not at["exceptions"] else (
        "；唔一樣嘅係 " + exc(at["exceptions"], lambda e: f"引擎 {e['engine']}、replay {e['replay']}")
        + "。")
    s += (f"{COUNT_ANCHOR_MARKER}（一行到 T-Spin Triple 同 Mini，全部種類），"
          f"<strong>{ct['agree']} / {ct['rounds']}</strong> 個 player-round 同 replay 自己個 "
          "<code>clears</code> counter 一樣")
    if ct["unknown"]:
        s += f"，另外 {ct['unknown']} 個冇 counter、當未知，唔當零"
    s += "。" if not ct["exceptions"] else (
        "；唔一樣嘅係 " + exc(ct["exceptions"], lambda e: "，".join(
            f"{k} 引擎 {v[0]}、replay {v[1]}" for k, v in e["engine_vs_replay"].items())) + "。")
    return s


def section(data, players):
    if data is None:
        return None
    ps = _order(data, players)
    W = data["window_pieces"]

    app = [Fraction(p["attack"], p["pieces"]) for p in ps]
    tie = app[0] == app[1]
    # a tie still decomposes (into zero), so it needs an order; players[1] minus players[0]
    hi, lo = (ps[1], ps[0]) if tie or app[1] > app[0] else (ps[0], ps[1])
    d = decompose(hi, lo)

    # ---- table 1: APP = lines per piece x attack per line, and the two windows
    t1 = []
    for i, p in enumerate(ps):
        w = p["windows"]
        t1.append([f"<td>{_who(i, p['user'])}</td>",
                   _num(_rate(p["attack"], p["pieces"], 3, "attack_section.app")),
                   _num(_rate(p["lines"], p["pieces"], 3, "attack_section.lpp")),
                   _num(_rate(p["attack"], p["lines"], 3, "attack_section.apl")),
                   _num(_rate(w["opener"]["attack"], w["opener"]["pieces"], 3, "attack_section.app_w")),
                   _num(_rate(w["mid"]["attack"], w["mid"]["pieces"], 3, "attack_section.app_w"))])
    head1 = ["", "每粒攻擊", "每粒清行", "每行攻擊", f"頭 {W} 粒 每粒攻擊", f"第 {W + 1} 粒起 每粒攻擊"]

    if tie:
        lede = ("兩個人嘅每粒攻擊一樣，所以下面嘅分解冇差距可以分；兩個表照印，"
                "睇嘅係兩個人攻擊嘅<em>組成</em>有冇唔同。")
    else:
        lede = (f"<strong>{html.escape(hi['user'])}</strong> 每 100 粒多 "
                f"<strong>{_signed(d['gap'], 'attack_section.gap')[1:]}</strong> 行攻擊（引擎數）。"
                f"每粒攻擊 = 每粒清行 × 每行攻擊，所以兩欄邊欄爭得多就係差距喺邊。"
                f"按時間拆：頭 {W} 粒 {_signed(d['windows']['opener'], 'attack_section.win')}、"
                f"之後 {_signed(d['windows']['mid'], 'attack_section.win')}"
                "（每 100 粒，兩段加埋就係成個差距）。")

    # ---- table 2: clears per 100 pieces in each window, and attack per clear
    t2 = []
    for k, label in LABELS:
        cells = [f"<td>{html.escape(label)}</td>"]
        seen = False
        for p in ps:
            w = p["windows"]
            no, nm = w["opener"]["classes"][k]["n"], w["mid"]["classes"][k]["n"]
            atk = w["opener"]["classes"][k]["attack"] + w["mid"]["classes"][k]["attack"]
            seen |= bool(no or nm)
            cells += [_num(_per100(no, w["opener"]["pieces"], "attack_section.per100")),
                      _num(_per100(nm, w["mid"]["pieces"], "attack_section.per100")),
                      _num(_rate(atk, no + nm, 2, "attack_section.per_clear"))]
        if seen:
            t2.append(cells)
    head2 = ["消行"] + [h for p in ps for h in
                        (f"{html.escape(p['user'])} 頭 {W} 粒", f"{html.escape(p['user'])} 之後",
                         f"{html.escape(p['user'])} 每次攻擊")]

    terms = sorted(d["terms"], key=lambda t: -abs(t[1]))
    top = [t for t in terms if t[1] != 0][:3]
    label = dict(LABELS)
    if tie:
        kit = ""
    else:
        kit = (f"將差距再拆做兩份（Kitagawa 拆法，兩份加埋等於成個差距）："
               f"<strong>消行組合</strong>——即係每粒有幾多次係邊種消行——"
               f"佔 {_signed(d['mix'], 'attack_section.kit')}；"
               f"<strong>每次攻擊值</strong>——即係同一種消行 {html.escape(hi['user'])} "
               f"每次打出幾多——佔 {_signed(d['value'], 'attack_section.kit')}（每 100 粒）。"
               "組合入面郁得最多嘅係："
               + "、".join(f"{html.escape(label[k])} {_signed(m, 'attack_section.kit_term')}"
                          for k, m, _ in top) + "。")

    # ---- table 3: components per 100 pieces
    t3 = []
    for i, p in enumerate(ps):
        w = p["windows"]
        comp = {c: w["opener"]["components"][c] + w["mid"]["components"][c] for c, _ in COMPONENTS}
        total = w["opener"]["attack"] + w["mid"]["attack"]
        t3.append([f"<td>{_who(i, p['user'])}</td>"]
                  + [_num(_per100(comp[c], p["pieces"], "attack_section.comp")) if comp[c] >= 0
                     else _num("−" + _per100(-comp[c], p["pieces"], "attack_section.comp"))
                     for c, _ in COMPONENTS]
                  + [_num(_per100(total, p["pieces"], "attack_section.comp"))])
    head3 = [""] + [lab for _, lab in COMPONENTS] + ["合計"]

    out = [
        '<section id="attack-sources">',
        CSS,
        '  <div class="wrap-wide">',
        '    <div class="eyebrow">模擬器推導 · 唔屬於信任鏈</div>',
        f'    <h2 class="section-title">{TITLE}</h2>',
        '',
        '    <div class="method-note">',
        f'      <p><strong>同上面 C-Spin 同 DT 砲一樣，{QUARANTINE_MARKER}。</strong>'
        '呢節將每一局用 replay 模擬器（vendored Triangle 引擎）由頭重跑，'
        '逐粒讀返佢未抵消之前打出嘅攻擊，再按消行種類、時間同攻擊成分拆開。'
        '冇 claim 編號、冇 ✓ 標記。</p>',
        f'      <p>{_anchor_note(data)}所以次數嗰幾欄同 facts.json 一樣可信；'
        f'每次攻擊同埋 B2B／Combo 嘅拆分{ENGINE_ONLY_MARKER}，冇第二個獨立實作對過。</p>',
        f'      <p>分母係 replay 自己數嘅粒數。「頭 {W} 粒」即係每局頭 {W} 粒（三個 bag），'
        '大約係開局定式嘅範圍；之後嘅就係中盤。'
        f'呢節答嘅係攻擊由邊種消行嚟，{NOT_A_RESULT_MARKER}。</p>',
        '    </div>',
        '',
        '    <h3>一 · 每粒攻擊 = 每粒清行 × 每行攻擊</h3>',
        *_table(head1, t1),
        f'    <div class="method-note"><p>{lede}</p></div>',
        '',
        '    <h3>二 · 每 100 粒有幾多次係邊種消行，同每次打出幾多攻擊</h3>',
        *_table(head2, t2),
        '    <div class="method-note"><p>「每次攻擊」包埋 B2B、Combo 同全消，'
        '所以同一種消行喺唔同局面值唔同。' + kit + '</p></div>',
        '',
        '    <h3>三 · 攻擊由咩成分組成（每 100 粒）</h3>',
        *_table(head3, t3),
        '    <div class="method-note"><p>基本值係 TETR.IO 攻擊表（T-Spin Double 4、Triple 6、'
        '四行 4）；B2B 同 Combo 係佢哋喺基本值上面加咗幾多；全消係 Perfect Clear 自己嗰份攻擊（10 行）；'
        '「其他」係引擎打出、而整數模型解釋唔到嘅部分（三分鐘之後嘅攻擊倍率，同埋引擎用小數 B2B '
        f'等級喺 Combo 倍數之後先取整）。五欄加埋就係引擎嘅攻擊；表入面{ROUNDING_MARKER}，'
        '所以加埋未必剛好等於合計。</p></div>',
        '  </div>',
        '</section>',
    ]
    markup = "\n".join(out)
    bad = sorted(set(markup) & SIMPLIFIED)
    if bad:
        raise SystemExit(f"attack_section: simplified glyph(s) {bad} — this report is "
                         "traditional-character Cantonese")
    return markup


def build(facts, report_dir):
    return section(load(report_dir), facts["players"])

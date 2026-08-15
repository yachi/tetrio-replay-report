"""全場之最 — the session's records, as stat tiles built from proved claims.

The claim generator already finds every session superlative (the highest single
round APM, VS, spike, B2B chain, combo, T-spin count and line count, plus the
longest and shortest round). Until now they were only readable as rows in the
52-row appendix, which is the wrong form for a headline number.

Each tile's figure is read out of the claim's own spec — the operands of the
equality Dafny proved — never re-derived from facts.json, so a tile cannot print
a number the proof does not cover. A claim whose spec is not a single round
equality gets no tile rather than an invented figure, and the count of those is
reported at build time instead of being silently dropped.

Form, per the dataviz procedure: this is a KPI row of stat tiles, not a chart —
a one-bar bar chart of a single record would be strictly worse. So there is no
hover layer, values use proportional figures (`tabular-nums` is for columns that
align vertically, and makes a standalone `121` look loose), and identity is a
coloured dot beside ink-coloured text rather than a value painted in the player's
hue. No new colours are introduced: the validated yachi/pinglamb pair is reused.
"""
import html

from pipeline import claim_cards, fmt
from pipeline.claims import generators

# (family, label, unit, how to format the proved integer)
#
# Ordered by how much each measure actually says about who won the round — the
# paired AUC over both sessions' 129 rounds (VS 100%, APM 94.6%, 攻/lines strong,
# spike and B2B weaker, COMBO 45% i.e. nothing). Records that decide games come
# first; COMBO is last because its tile is a curiosity, not a finding.
RECORDS = [
    ("round_max_vs_x1000", "單局最高 VS", "", "r1"),
    ("round_max_apm_x1000", "單局最高 APM", "", "r1"),
    ("round_max_lines", "單局最多清行", "行", "int"),
    ("round_duration_max", "最長嘅一局", "", "clock"),
    ("round_duration_min", "最短嘅一局", "", "clock"),
    ("round_max_maxspike", "最大單一 spike", "行", "int"),
    ("round_max_topbtb", "最長 B2B 鏈", "段", "int"),
    ("round_max_tspins", "單局最多 T-spin", "個", "int"),
    ("round_max_topcombo", "最長 COMBO", "下", "int"),
    # Listed on purpose even though it never yields a tile: its claim is a range
    # over a whole match rather than one round's value, so `round_operand` returns
    # nothing and it lands in the footnote. Leaving it out of this table instead
    # would be a silent cap — a record the section quietly decided not to mention.
    ("match_apm_max", "整場 match 最高 APM", "", "r1"),
]

CSS = """
<style>
/* ---------- 全場之最 (generated) ---------- */
/* The host report defines --accent only on .match-card[data-winner], where it is
   set from the winner; anywhere else it resolves to an empty string and silently
   invalidates any color-mix() using it. This section carries its own token. */
#records { --sr-accent: var(--yachi); }
#records .sr-grid { display: grid; gap: .8rem; margin: 1.4rem 0 0;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 232px), 1fr)); }
#records .sr-tile { border: 1px solid var(--border); border-radius: 10px; padding: .85rem .95rem 1rem;
  background: var(--bg-raised); display: flex; flex-direction: column; gap: .3rem; }
#records .sr-label { font-family: var(--font-mono); font-size: .66rem; letter-spacing: .08em;
  text-transform: uppercase; color: var(--muted); }
/* Proportional figures, not tabular: these are standalone display numbers, and
   equal-width digits make a value like 121 read loose at this size. */
#records .sr-value { font-size: 1.7rem; font-weight: 700; line-height: 1.1; color: var(--ink);
  font-variant-numeric: proportional-nums; }
#records .sr-value small { font-size: .62em; font-weight: 600; color: var(--muted); margin-left: .18em; }
/* Identity is a coloured dot plus ink-coloured text. A figure painted in the
   player's hue would be colour-as-information and reads worse. */
#records .sr-who { font-size: .78rem; color: var(--ink-secondary); display: flex;
  align-items: center; gap: .4rem; }
#records .sr-dot { width: .5rem; height: .5rem; border-radius: 50%; flex: none; }
#records .sr-dot.is-y { background: var(--yachi); }
#records .sr-dot.is-p { background: var(--pinglamb); }
#records .sr-note { margin: .35rem 0 0; font-size: .78rem; line-height: 1.7;
  color: var(--ink-secondary); }
#records .sr-cid { font-family: var(--font-mono); font-size: .6rem; color: var(--muted);
  margin-top: auto; padding-top: .5rem; }
#records .sr-foot { font-size: .8rem; color: var(--muted); margin: 1.1rem 0 0; }
@media print {
  #records .sr-tile { break-inside: avoid; }
}
</style>
"""


def _value(kind, unit, v):
    """The proved integer, printed the way the claim's own sentence prints it."""
    if kind == "r1":
        # 約 because the claim's Cantonese says 約 — same floored digits, same word.
        return "約" + fmt.r1(v), unit
    if kind == "clock":
        # m:ss only earns its space once there are minutes to read — under a
        # minute it just prints the same number twice (「21 秒（0:21）」).
        s = fmt.secs(v)
        return f"{s}", f"秒（{fmt.fmt_clock(v)}）" if s >= 60 else "秒"
    return f"{v:,}", unit


def collect(report_dir):
    """(tiles, skipped) — tiles in RECORDS order; skipped claims keep their ids."""
    claims = {c["family"]: c for c in claim_cards.load(report_dir)}
    tiles, skipped = [], []
    for family, label, unit, kind in RECORDS:
        c = claims.get(family)
        if not c:
            continue
        op = claim_cards.round_operand(c)
        if not op:
            skipped.append(c["id"])
            continue
        value, suffix = _value(kind, unit, op["value"])
        tiles.append({"label": label, "value": value, "suffix": suffix,
                      "player": op["player"], "match": op["match"],
                      "round": op["round"], "canto": c["canto"],
                      "id": c["id"], "verified": c["verified"]})
    return tiles, skipped


def build(facts, report_dir):
    p1, _p2 = facts["players"]
    tiles, skipped = collect(report_dir)
    if not tiles:
        raise SystemExit(f"{report_dir}: no session-record claims found — run "
                         "pipeline.claims.build_claims first")
    out = [CSS, '<section id="records">', '  <div class="wrap">',
           '    <div class="eyebrow">紀錄 · SESSION RECORDS</div>',
           '    <h2 class="section-title">全場之最</h2>',
           '    <p class="section-lede">每格都係 pipeline 由 facts.json 自己搵出嚟、'
           '再逐條用 Dafny 證過嘅紀錄（claim id 喺格仔下面）。格仔嘅數字就係嗰條 claim '
           '證嘅同一個數，唔係另外再算一次；下面嗰句連埋原本嘅注解一齊擺，'
           '所以「呢個數全場出現過幾次」呢類話唔會跌咗。</p>',
           '    <div class="sr-grid">']
    for t in tiles:
        dot = "is-y" if t["player"] == p1 else "is-p"
        tick = "✓ Dafny 已證" if t["verified"] else "⏳ 待證"
        suffix = (f'<small>{html.escape(t["suffix"])}</small>' if t["suffix"] else "")
        out += [
            '      <div class="sr-tile">',
            f'        <div class="sr-label">{html.escape(t["label"])}</div>',
            f'        <div class="sr-value">{html.escape(t["value"])}{suffix}</div>',
            f'        <div class="sr-who"><span class="sr-dot {dot}"></span>'
            f'{html.escape(t["player"])} · m{t["match"]} 第{t["round"]}局</div>',
            f'        <p class="sr-note">{html.escape(t["canto"])}</p>',
            f'        <div class="sr-cid">{html.escape(t["id"])} · {tick}</div>',
            '      </div>',
        ]
    out.append('    </div>')
    # Why two kinds of record live in one grid. Without this the reader sees a
    # 打足 60 秒 qualifier on some tiles and not others and has to guess whether
    # it is a rule or an oversight.
    # CORPUS FIGURES, HAND-MAINTAINED. These describe every session pooled, so no single
    # session's facts.json can derive them and nothing here can go stale loudly. They come
    # from `Rscript analysis/rate_records.R`, whose session list is hardcoded for the same
    # reason — when a session is added, re-run it and copy the new numbers into BOTH places.
    # They were left at four sessions / 492 player-rounds through two additions before
    # anyone read the rendered footnote.
    out.append(f'    <p class="sr-foot">APM／VS 呢類 <strong>速率</strong>紀錄只計'
               f'打足 {generators.QUALIFYING_MS // 1000} 秒嘅局。速率係「攻擊 ÷ 時間」，'
               '局數愈短分母愈細，個數就愈飄——六個 session 夾埋 760 個 player-round 度'
               '量過：VS 嘅標準差由 59.9（約 19 秒嗰批）跌到 14.5（約 150 秒嗰批），'
               '足足細咗四倍；同一段路平均數反而由 104 升到 120，即係短局唔止唔係打得好啲，'
               '仲要係量得唔準好多。'
               '未設限之前，六個 session 全部 18 項速率紀錄都落喺最短嗰四分一嘅局度。'
               '<strong>清行數、spike、combo、B2B、T-spin 呢類「計數」紀錄照計全部局</strong>'
               '——短局入面塞得落更多，係難咗唔係易咗。分析喺 <code>analysis/rate_records.R</code>。</p>')
    if skipped:
        out.append('    <p class="sr-foot">另外有 '
                   f'{len(skipped)} 條紀錄類 claim（{", ".join(html.escape(i) for i in skipped)}）'
                   '嘅講法唔係「某一局某個數係幾多」，冇做成格仔，要睇就去下面嘅證明附錄。</p>')
    out += ['  </div>', '</section>']
    return "\n".join(out)

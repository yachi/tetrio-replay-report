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
import json
import math
from pathlib import Path

from analysis import rate_records_artefact
from pipeline import claim_cards, fmt
from pipeline.claims import generators

# ── the footnote's corpus scope ────────────────────────────────────────────────
#
# The footnote describes EVERY session pooled, so the session being built cannot
# derive it — which is exactly how it came to be typed by hand, and how it sat at
# 四個 session / 492 player-round through two additions before anyone read the
# rendered page. The two numbers a glob CAN derive are derived here; what remains
# hand-maintained is guarded below.
_CN_DIGITS = "零一二三四五六七八九十"


def _cn(n):
    """Chinese numeral for a small count, digits past ten.

    Exists so the count can be DERIVED without changing a single byte of the
    rendered string: the footnote has always read 「六個 session」, and every
    committed report is byte-identity gated on what this function emits.
    """
    return _CN_DIGITS[n] if 0 <= n <= 10 else str(n)


def corpus_scope():
    """(sessions, player-rounds) over every committed session.

    Located from THIS file, not from the report directory the caller passed: that
    argument names one session and this figure is about all of them. Same reason
    `analysis/rate_records.R` resolves its `repo` from the script's own path — an
    assumption about the caller's cwd is how a corpus figure ends up describing a
    different tree than the one it ships in.
    """
    root = Path(__file__).resolve().parents[1]
    facts = sorted(root.glob("sessions/*/report/facts.json"))
    if not facts:
        raise SystemExit(f"records.py: no sessions/*/report/facts.json under {root} — "
                         "the footnote's corpus figures cannot be derived")
    rounds = 0
    for f in facts:
        d = json.loads(f.read_text(encoding="utf-8"))
        rounds += sum(len(r["players"]) for m in d["matches"] for r in m["rounds"])
    return len(facts), rounds


# ── the R-derived statistics, READ from the committed artefact ─────────────
#
# `analysis/rate-records.json`, written by `Rscript analysis/rate_records.R --json`.
# These were hand-copied literals until 2026-08-23, guarded only by a session COUNT.
# The count could not see the class that actually happened: on 2026-08-16 apm/pps/vs
# were re-sourced from the live `player.stats` tick to `results.aggregatestats`, which
# moved the shortest bin's VS SD from 59.91 to 59.60 with the corpus unchanged at six
# sessions, and the footnote kept saying 59.9. The artefact fingerprints every
# facts.json it read and the script itself, so `load()` refuses on all three staleness
# routes — a session lands, the data moves, the analysis moves.
#
# Read at build time rather than at import: a module-level `SystemExit` would take out
# every importer of `records` (including gates that never render the footnote) over an
# artefact only `build` consumes.


def _dp1(x):
    """One decimal place, FLOORED, as the string `ratio1` wants.

    Floors for the same reason everything in `fmt` does. It also puts the numerator of
    the SD ratio on the safe side; the denominator is the unsafe side, which is what
    `_check_sd_ratio` measures rather than assumes.
    """
    return fmt.quantf(x, 1, "floor", site="records._dp1")


def r_stats():
    """The R figures the footnote prints, at the precision it prints them.

    The two bin lengths floor because the sentence prefixes them with 約, which this repo
    defines as "at least this much". The SD endpoints floor too, on `fmt`'s convention.
    The mean endpoints ROUND: they carry no 約 and they are a rise, so flooring the low
    end would print a bigger rise than was measured. The six-session values (104.1, 120.1)
    floored and rounded to the same integers, which is why that had not come up before.
    """
    art = rate_records_artefact.load()
    vs = art["metrics"]["vs"]
    sd_short, sd_long = _dp1(vs["sd_short"]), _dp1(vs["sd_long"])
    return {
        "sessions": len(art["sessions"]),
        "sd_short": sd_short,
        "sd_long": sd_long,
        "t_short": math.floor(vs["t_short"]),
        "t_long": math.floor(vs["t_long"]),
        "mean_short": round(vs["mean_short"]),
        "mean_long": round(vs["mean_long"]),
        # Derived from the two PRINTED strings, so a reader dividing the digits in the
        # sentence gets the digits in the sentence — `ratio1`'s whole reason for taking
        # decimal strings. `_check_sd_ratio` is what says that route never overstates the
        # true fall, which flooring the denominator could in principle do.
        "sd_ratio": fmt.ratio1(sd_short, sd_long),
        "sd_ratio_exact": vs["sd_short"] / vs["sd_long"],
        "mean_ratio": vs["mean_long"] / vs["mean_short"],
        "n_records": art["records"]["n"],
    }


# The floor the FOOTNOTE'S ARGUMENT needs, which is not the floor today's number happens to
# sit near. The argument is "the spread moves a lot while the mean barely moves", so what
# has to hold is that the SD effect dominates the mean effect — the mean moves 1.12x over
# the same span. Below 2 the SD does not even halve while the rounds get ~7.7x longer, and
# 「量得唔準好多」 stops being supported by its own numbers.
#
# Deliberately NOT 4. Pinning it at 4 would re-freeze the value this guard exists because
# somebody froze, and would fail the build for a corpus that still supports every word of
# the sentence. A guard set to today's measurement is a copy of the measurement.
_MIN_SD_RATIO = 2.0


def _check_sd_ratio(r):
    """Two conditions, and the second is why the printed digits may be divided at all.

    (1) the fall is big enough for the sentence's argument, and (2) the ratio derived
    from the two PRINTED endpoints does not exceed the ratio the unrounded data gives.
    Flooring the denominator inflates a quotient, so 足足 could in principle end up
    asserting a floor the corpus does not support — one comparison, and it never has to
    be reasoned about again.
    """
    if float(r["sd_ratio"]) > r["sd_ratio_exact"]:
        raise SystemExit(
            f"records.py: the footnote would print 足足細咗 {r['sd_ratio']} 倍 from the "
            f"printed endpoints {r['sd_short']} / {r['sd_long']}, but the unrounded data "
            f"gives only {r['sd_ratio_exact']:.4f}x. 足足 asserts a floor, so the printed "
            f"ratio may never exceed the measured one.")
    if float(r["sd_ratio"]) < _MIN_SD_RATIO:
        raise SystemExit(
            f"records.py: the VS SD falls only {r['sd_ratio']}x from the shortest bin "
            f"({r['sd_short']}) to the longest ({r['sd_long']}), under the "
            f"{_MIN_SD_RATIO}x this footnote's argument needs. The sentence claims the "
            f"spread moves far more than the mean, and at this ratio it no longer does. "
            f"Do not lower this bound to make the build pass — rewrite the footnote "
            f"around what the corpus now shows, and re-check whether QUALIFYING_MS is "
            f"still justified by `Rscript analysis/rate_records.R`.")


# (family, label, unit, how to format the proved integer)
#
# Ordered by how much each measure actually says about who won the round — the
# paired AUC (VS 100%, APM 93.8%, 攻/lines strong, spike and B2B weaker, COMBO
# weakest of all). Records that decide games come first; COMBO is last because
# its tile is a curiosity, not a finding.
# APM read 94.6% here until 2026-08-17 and matches no session at any pooling —
# 93.8 pooled, 93.7 and 94.0 apart. Re-derived from facts.json, winner vs loser
# per round, ties at half a win (the convention in pipeline/sim/pairs.ts).
# COMBO read "45.0% i.e. nothing" here until 2026-08-19, and 45.0 was correct when
# written: it is the paired AUC over the 129 rounds of the FIRST TWO sessions,
# which is all there was. It is not a corpus figure and never was. Re-derived the
# same way over all 450 rounds of seven sessions it is 56.22 — raw p 0.00179 by a
# sign-flip permutation, still 0.030 after Bonferroni over the 17 columns tested,
# so the column carries weak signal rather than none. The per-session series drifts
# steadily: 41.1 · 51.0 · 62.5 · 55.7 · 57.0 · 58.9 · 67.9.
# COMBO's POSITION here is unaffected, and that was measured rather than assumed:
# over the same 450 rounds the seven families with a per-round value rank COMBO
# 56.22 < B2B 64.22 < spike 68.00 < T-spin 68.33 < 清行 81.33 < APM 92.89 < VS
# 100.0, so it is still last. This is a stale sentence, not a stale ordering, and
# nothing below moves.
# The rule the two corrections share: an AUC quoted from the sessions that existed
# when it was written goes stale without anyone touching this file. Re-derive
# before quoting, and say which corpus the number is over.
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
    #
    # The session and player-round counts are DERIVED (`corpus_scope`); the R
    # statistics are not, and this is where the two meet. A seventh session makes
    # the derived half describe seven while the copied half still describes six,
    # so refuse to render rather than publish a footnote that is two-thirds true.
    n_sessions, n_player_rounds = corpus_scope()
    r = r_stats()
    _check_sd_ratio(r)
    if r["sessions"] != n_sessions:
        raise SystemExit(
            f"records.py: analysis/rate-records.json was measured over {r['sessions']} "
            f"session(s) but sessions/*/report/facts.json now holds {n_sessions}. "
            f"Run `{rate_records_artefact.REGEN}` and commit the artefact.")
    # The R analysis takes one record per session from THREE metrics; the report ranks
    # two of them (`generators._SUPERLATIVES` has no pps entry). The footnote's count is
    # the evidence's, not the tile row's, which is right — the claim it makes is about
    # what the unqualified argmax does, and pps is an unqualified argmax too. Read out
    # of the artefact so it cannot disagree with the run that produced the p-value.
    n_rate_records = r["n_records"]
    sd_short, sd_long, sd_ratio = r["sd_short"], r["sd_long"], r["sd_ratio"]
    t_short, t_long = r["t_short"], r["t_long"]
    mean_short, mean_long = r["mean_short"], r["mean_long"]
    out.append(f'    <p class="sr-foot">APM／VS 呢類 <strong>速率</strong>紀錄只計'
               f'打足 {generators.QUALIFYING_MS // 1000} 秒嘅局。速率係「攻擊 ÷ 時間」，'
               f'局數愈短分母愈細，個數就愈飄——{_cn(n_sessions)}個 session 夾埋 '
               f'{n_player_rounds} 個 player-round 度'
               f'量過：VS 嘅標準差由 {sd_short}（約 {t_short} 秒嗰批）跌到 '
               f'{sd_long}（約 {t_long} 秒嗰批），'
               f'足足細咗 {sd_ratio} 倍；'
               f'同一段路平均數反而由 {mean_short} 升到 {mean_long}，'
               '即係短局唔止唔係打得好啲，'
               '仲要係量得唔準好多。'
               f'未設限之前，{_cn(n_sessions)}個 session 全部 {n_rate_records} 項速率紀錄'
               '都落喺最短嗰四分一嘅局度。'
               '<strong>清行數、spike、combo、B2B、T-spin 呢類「計數」紀錄照計全部局</strong>'
               '——短局入面塞得落更多，係難咗唔係易咗。分析喺 <code>analysis/rate_records.R</code>。</p>')
    if skipped:
        out.append('    <p class="sr-foot">另外有 '
                   f'{len(skipped)} 條紀錄類 claim（{", ".join(html.escape(i) for i in skipped)}）'
                   '嘅講法唔係「某一局某個數係幾多」，冇做成格仔，要睇就去下面嘅證明附錄。</p>')
    out += ['  </div>', '</section>']
    return "\n".join(out)

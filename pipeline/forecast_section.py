"""T-Spin Forecast — 模擬器推導區，刻意排喺信任鏈之外。

This section exists because the metric was asked for in the report. It is built to be
impossible to mistake for a proved claim, because it is not one:

  * Its numbers come from `sim/forecast-facts.json`, NOT `facts.json`. They are produced by a
    single replay SIMULATOR. The repo's trust argument is two independently written extractors
    agreeing byte-for-byte; there is no second simulator, so that argument does not cover this.
  * Therefore no claim IDs and no ✓ badges. Every badge in this report resolves to a Dafny
    lemma over facts.json; minting one here would blur simulation into extraction, which is
    the failure mode every audit round in this project has caught.
  * The section states its own null result. The metric shows no effect at any unit of
    analysis, and a report that printed the rates without that would be misleading by
    omission.

It renders inside a generated region, so `check_prose_figures` skips it (that check is for
hand-written 約-figures); the numbers here are exact and carry their own intervals. A
dedicated guard, `check_forecast_section.py`, verifies the rendered numbers against the JSON
so the two cannot drift.

If a second independent simulator is ever written and agrees, this section can be promoted
into the normal claims pipeline and this module deleted. Until then it is quarantined on
purpose.
"""
import html
import json
import os

# Session-scoped, NOT global. The first version hardcoded the 2026-07-22 path and was
# registered for every session, so `build_report --check` on 2026-07-24 and 2026-07-28
# reported DRIFT — it was trying to graft one session's simulator output into another
# session's report. A session that has no forecast-facts.json simply has no such section.
FACTS_REL = os.path.join("sim", "forecast-facts.json")


def facts_path(report_dir):
    """`<session>/sim/forecast-facts.json` for the session owning `report_dir`."""
    return os.path.join(os.path.dirname(os.path.abspath(report_dir)), FACTS_REL)


def load(report_dir):
    """The session's forecast facts, or None when it has none."""
    path = facts_path(report_dir)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _pct(x1000):
    """x1000 integer -> one-decimal percent string: 121 -> "12.1%".

    This step drops nothing — an x1000 integer has exactly one decimal at percent scale.
    The 約-convention is upheld one level up instead, in `emit-forecast-facts.ts`: point
    estimates and lower bounds floor, upper bounds ceil (`_bound_dp`'s rule). Saying
    "never rounded up" here was a claim about the *input* that the emitter did not honour
    — it used `Math.round`, and this function faithfully printed 12.2% for 12.1739%.
    """
    return f"{x1000 / 10:.1f}%"


def _num(x1000):
    """x1000 integer -> exact 3-decimal string: 517 -> "0.517", -337 -> "−0.337".

    Three decimals because that is exactly what an x1000 integer carries; rendering at two
    would re-round a value whose direction was already decided in `emit-forecast-facts.ts`,
    and this module must not make a second rounding decision. Uses U+2212 MINUS, matching the
    typography the rest of the report uses for negative figures.
    """
    return f"{x1000 / 1000:.3f}".replace("-", "−")


def _stat(data, *path):
    """`data["statistics"][a][b]...`, or None as soon as any level is null or missing.

    Every caller must handle None by printing an ABSENCE. A session where a quantity could
    not be computed has no figure for it, and substituting 0 would publish "measured, and the
    effect is exactly nothing" — a finding this data cannot support.
    """
    cur = data.get("statistics") or {}
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
        if cur is None:
            return None
    return cur


def _units_clause(data):
    """The 「三個分析單位都試過」 sentence, built from whichever units are computable.

    Every figure in here was a literal until 2026-08-02. This module renders for EVERY
    session, so those literals described 2026-07-22 and would have been published as another
    session's numbers the moment a second session emitted a forecast artifact.
    """
    parts = []
    rnd = _stat(data, "round")
    if rnd and rnd.get("auc_x1000") is not None and rnd.get("exact_p_x1000") is not None:
        parts.append(f"每局（AUC {_pct(rnd['auc_x1000'])}，p = {_num(rnd['exact_p_x1000'])}）")

    atk = _stat(data, "event", "attack")
    if atk and atk.get("diff_x1000") is not None:
        lo, hi = atk.get("ci95_lo_x1000"), atk.get("ci95_hi_x1000")
        ci = (f"，95% CI [{_num(lo)}, {_num(hi)}]"
              + ("，含 0" if not atk.get("excludes_zero") else "，唔含 0")) if lo is not None else ""
        nc = _stat(data, "event", "negative_control")
        # The negative control is only worth a sentence when it FIRED — a difference that also
        # shows up where the mechanism cannot act is evidence the two arms are incomparable.
        nc_txt = ("，而且事前定好嘅 negative control 有反應，證明兩組本身就唔可比"
                  if nc and nc.get("fires") else "")
        parts.append(f"每次 T-spin（forecast 比 reactive 多送 {_num(atk['diff_x1000'])} attack{ci}{nc_txt}）")

    ply = _stat(data, "player")
    if ply and ply.get("exact_p_x1000") is not None:
        parts.append(f"每個玩家（p = {_num(ply['exact_p_x1000'])}）")

    if not parts:
        return "呢一節冇一個分析單位夠數計得出結果。"
    if len(parts) == 1:
        return "淨係得一個分析單位計得出——" + parts[0] + "。"
    return f"{'三個' if len(parts) == 3 else f'{len(parts)} 個'}分析單位都試過——" + "、".join(parts) + "。"


# A p at or below this is called significant; x1000, so 50 is p = 0.05.
ALPHA_X1000 = 50


def _effects(data):
    """The units, if any, that show an effect on THIS session's data.

    The section's headline used to assert 「搵唔到效果」 unconditionally. That is a conclusion,
    and a module rendered for every session must not carry one session's conclusion as a
    constant any more than it may carry its figures — a later session that did show something
    would have had the null printed over it.
    """
    found = []
    rnd = _stat(data, "round")
    if rnd and rnd.get("exact_p_x1000") is not None and rnd["exact_p_x1000"] <= ALPHA_X1000:
        found.append("每局")
    atk = _stat(data, "event", "attack")
    nc = _stat(data, "event", "negative_control")
    # A firing negative control means the same difference appears where the mechanism cannot
    # act, so an interval excluding zero is evidence the arms differ, not that forecasting
    # works. That is not an effect and must not be counted as one.
    if atk and atk.get("excludes_zero") and not (nc and nc.get("fires")):
        found.append("每次 T-spin")
    ply = _stat(data, "player")
    if ply and ply.get("exact_p_x1000") is not None and ply["exact_p_x1000"] <= ALPHA_X1000:
        found.append("每個玩家")
    return found


def _headline(data):
    found = _effects(data)
    if not found:
        return "<strong>統計結論係：搵唔到效果。</strong>"
    listed = "同".join(found)
    # 「每次 T-spin」ends in a Latin character, and this repo sets a space at a Latin/CJK
    # boundary everywhere else it renders one.
    sep = " " if listed[-1].isascii() else ""
    return ("<strong>統計結論係：" + listed + sep + ("呢個" if len(found) == 1 else "呢啲")
            + "單位見到差異。</strong>"
            "但呢節嘅數依然係一個模擬器出嘅，冇第二個獨立實作對得上，"
            "所以<strong>唔可以當成證實咗嘅結論</strong>，只可以當成值得再查嘅線索。")


def _reliability_clause(data):
    """The split-half sentence — the reason the unit is the player and not the round."""
    rel = _stat(data, "reliability")
    if not rel:
        return ""
    rs = rel.get("split_half_r_x1000") or {}
    named = [(u, v) for u, v in rs.items() if v is not None]
    if not named:
        return ""
    listed = "同 ".join(f"{_num(v)}（{html.escape(u)}）" for u, v in named)
    return ("而且每局嘅數<strong>連自己都對唔上自己</strong>："
            f"split-half reliability 得 {listed}，"
            "即係每局一個數喺呢個事件密度下根本唔可能穩定，"
            "幾好嘅模擬器都救唔到。所以下面只列<strong>每個玩家嘅總計</strong>。")


def _coverage_clause(data):
    """Why the sample is small: how much of the session the simulator could reproduce."""
    ses = data.get("session") or {}
    rounds, cov = ses.get("player_rounds"), ses.get("coverage_x1000")
    if rounds is None or cov is None:
        return "呢節嘅樣本細，因為只有對得返上真實對局嘅落子先計得入。"
    return (f"全 {rounds} 個 player-round 入面，只有 {_pct(cov)} 嘅落子對得上，所以樣本先咁細。")


def _spread_clause(data):
    """Sampling spread vs simulator spread, and what that comparison does NOT establish."""
    widths = []
    for p in data["players"]:
        samp = p["sampling_ci95_hi_x1000"] - p["sampling_ci95_lo_x1000"]
        sim = p["simulator_range_hi_x1000"] - p["simulator_range_lo_x1000"]
        if sim > 0:
            widths.append((samp, sim, samp / sim))
    if not widths:
        # Every simulator config agrees exactly — which happens when the verified count is 0 and
        # stays 0 however the simulator is perturbed. That is a RESULT, not a missing figure, and
        # rendering an empty paragraph would hide the most robust thing in the section.
        return ("七個模擬器設定全部計出同一個數，飄幅係零。"
                "即係話下面個數<strong>唔係模擬器調校出嚟嘅結果</strong>——"
                "點樣改模擬器都係同一個答案。")
    sim_lo, sim_hi = min(w[1] for w in widths), max(w[1] for w in widths)
    sa_lo, sa_hi = min(w[0] for w in widths), max(w[0] for w in widths)
    ratio_lo, ratio_hi = min(w[2] for w in widths), max(w[2] for w in widths)
    span = (lambda a, b: _pct(a) if a == b else f"{_pct(a)}–{_pct(b)}")
    return (
        "兩者一比就答咗一條好重要嘅問題："
        f"<strong>模擬器嘅飄幅（{span(sim_lo, sim_hi)}）遠細過抽樣嘅飄幅（{span(sa_lo, sa_hi)}）</strong>，"
        f"爭大約 {ratio_lo:.0f}–{ratio_hi:.0f} 倍。"
        "即係話喺<em>呢七個設定掃到嘅範圍之內</em>，改模擬器對收窄呢個數幫助有限，要收窄佢就要更多場數。"
        # The sweep varies seven FITTED options of one simulator. It bounds parameter
        # sensitivity and nothing else: a shared modelling error — something every one of the
        # seven configs gets wrong the same way — moves all of them together and never appears
        # in this range. Saying flatly that the bottleneck "is not simulator accuracy" claimed
        # more than the sweep measures, so it is stated as the scope-limited fact it is.
        "要留意呢個掃描只係換咗同一個模擬器嘅七個設定，"
        "<strong>量度唔到七個設定一齊錯嘅嗰種偏差</strong>，所以佢並唔等於證明咗模擬器本身準。"
    )


def _overlap_clause(data):
    """Whether the players' sampling intervals overlap — checked, not assumed.

    This sentence used to assert 「兩個玩家嘅區間幾乎完全重疊」 unconditionally. It is true of
    all four sessions today, which is exactly why it survived review: an assertion that happens
    to hold is indistinguishable from a derivation until the day it does not. It also assumed
    there are two players.
    """
    ps = sorted(data["players"], key=lambda p: -p["forecast_rate_x1000"])
    n = len(ps)
    if n < 2:
        return "得一個玩家有可核數據，所以呢度冇任何玩家之間嘅比較。"
    apart = [(a, b) for i, a in enumerate(ps) for b in ps[i + 1:]
             if min(a["sampling_ci95_hi_x1000"], b["sampling_ci95_hi_x1000"])
             <= max(a["sampling_ci95_lo_x1000"], b["sampling_ci95_lo_x1000"])]
    if not apart:
        return f"{n} 個玩家嘅抽樣區間互相重疊，所以呢度<strong>冇聲稱邊個 forecast 多啲</strong>。"
    pairs = "、".join(f"{html.escape(a['user'])} 同 {html.escape(b['user'])}" for a, b in apart)
    # Still no claim: the section is outside the trust chain whatever the intervals do. Only
    # the REASON changes, and stating an overlap that is not there would be a false one.
    return (f"{pairs} 嘅抽樣區間冇重疊。不過呢節嘅數係模擬器出嘅、唔屬於信任鏈，"
            "所以依然<strong>冇聲稱邊個 forecast 多啲</strong>，只可以當成值得再查嘅線索。")


def _mechanism_clause(data):
    """Why the verified count is what it is, and where the other T-spins went.

    Added 2026-08-02 with the causal correction. Without it a reader sees 0.0% beside a table of
    real T-spins and has no way to tell a measurement from a bug. Rewritten later the same day
    when localising the mechanism to a single step replaced the counterfactual, and the line-clear
    bucket stopped being untestable — 85 of its 86 events turned out to be the player's own piece.
    """
    ps = data["players"]
    tot = sum(p["verified_tspins"] for p in ps)
    fg = sum(p.get("forecast_garbage", 0) for p in ps)
    lc = sum(p.get("forecast_lineclear", 0) for p in ps)
    sb = sum(p.get("self_built", 0) for p in ps)
    re_ = sum(p.get("reactive", 0) for p in ps)
    if not tot:
        return ""
    parts = [
        "<strong>「Forecast」要求個窿位係<em>由外力</em>整出嚟嘅</strong>——"
        "即係垃圾升起或者消行，唔係自己砌出嚟。"
        "所以唔係問「嗰段時間有冇垃圾、有冇消行」，而係<strong>逐格倒帶</strong>："
        "每落一隻棋都有一張板，搵返個 T-spin 係<em>邊一步</em>先至出現；"
        "而喺嗰一步入面，模擬器係先落棋、再消行、最後升垃圾，"
        "所以嗰三個動作可以逐個拆開，睇個窿位到底邊個動作整出嚟。"
        "咁樣就唔使靠反事實：三張中間板都係由上一張板砌返出嚟，"
        "而且當嗰步冇垃圾升起嘅時候，砌返出嚟嗰張<strong>一定要同實際嗰張逐格一樣</strong>——"
        "呢點係查咗先算數，唔係當佢啱。",
        f"喺呢個 session 全部 {tot} 個可核 T-spin 入面："
        f"<strong>{fg} 個</strong>係垃圾造成個窿位；"
        f"<strong>{lc} 個</strong>係消行造成——消嗰行啱啱夾喺天花板同窿位中間，"
        "消走咗兩者先貼埋一齊（下面表入面嘅數，就係呢兩種加埋）；"
        f"{sb} 個係<strong>玩家自己落嗰隻棋整出嚟</strong>嘅——開局定式（例如 C-Spin）就係咁，"
        "個天花板早過個窿位係定式本身嘅砌法，唔係預測；"
        f"其餘 {re_} 個個窿位本身冇變好。",
    ]
    if fg + lc == 0:
        parts.append(
            "<strong>換句話講：呢個 session 冇一個可核 T-spin 嘅窿位係外力造成嘅。</strong>"
            "之前呢節報過嘅 forecast 數，係「垃圾或者消行喺窗口入面出現過」就算數——"
            "喺平均相隔 11 隻棋嘅窗口入面，幾乎實會有，"
            "所以嗰個數量到嘅係<em>開局定式</em>，唔係預測。")
    else:
        parts.append(
            "要留意：呢個數細到<strong>一兩件事就當唔到係習慣</strong>，"
            "抽樣區間亦都已經包含咗零，"
            "所以呢度<strong>唔係話邊個識 forecast</strong>，"
            "只係話喺可核範圍入面，符合定義嘅情況搵到幾多次。")
    return "".join(parts)


def section(data):
    if data is None:
        return None
    players = sorted(data["players"], key=lambda p: -p["forecast_rate_x1000"])
    rows = []
    for p in players:
        rows.append(
            "          <tr>"
            f"<td>{html.escape(p['user'])}</td>"
            f"<td class=\"mono\">{p['forecast_total']} / {p['verified_tspins']}</td>"
            f"<td class=\"mono\">{_pct(p['forecast_rate_x1000'])}</td>"
            f"<td class=\"mono\">[{_pct(p['sampling_ci95_lo_x1000'])}, {_pct(p['sampling_ci95_hi_x1000'])}]</td>"
            f"<td class=\"mono\">[{_pct(p['simulator_range_lo_x1000'])}, {_pct(p['simulator_range_hi_x1000'])}]</td>"
            "</tr>")

    out = [
        '<section id="forecast">',
        '  <div class="wrap-wide">',
        '    <div class="eyebrow">模擬器推導 · 唔屬於信任鏈</div>',
        '    <h2 class="section-title">T-Spin Forecast（未經證明）</h2>',
        '',
        '    <div class="method-note">',
        '      <p><strong>呢一節同上面所有數唔同級數，請當佢係探索性資料，唔好當結論。</strong>'
        '上面每個數都係兩個獨立 parser 抽出嚟、再由 Dafny 引理逐條證明；'
        '呢節嘅數係由<strong>一個 replay 模擬器</strong>重跑操作記錄推導出嚟，'
        '得一份實作，冇第二個獨立實作對得上，所以套唔到同一個信任鏈——'
        '亦都因為咁，呢節<strong>冇 claim 編號、冇 ✓ 標記</strong>。</p>',
        '      <p>「Forecast」係指打 T-spin 之前，個窿位<em>仲未成形</em>：'
        '搭個天花板嗰陣打得到嘅 T-spin 冇咁好，之後靠垃圾行升起或者消行先至變好。'
        '（唔係淨係「本來完全冇」——維基自己嘅例子入面，有啲係本來得一行、'
        '垃圾升完變兩行，嗰啲一樣算。）對照組叫 reactive，即係個位本身冇變好過。</p>',
        '      <p>' + _headline(data) + _units_clause(data) + _reliability_clause(data) + '</p>',
        '      <p>' + _mechanism_clause(data) + '</p>',
        '      <p>「可核 T-spin」係指嗰段棋盤可以同真實對局對得返上（用對手嘅 ige 事件流逐次攻擊校對），'
        '唔係話條數經過 Dafny 證明——呢節冇任何嘢經過證明。'
        + _coverage_clause(data) + '</p>',
        '    </div>',
        '',
        '    <div class="scroll-x">',
        '      <table class="appendix-table">',
        '        <thead>',
        '          <tr>',
        '            <th>玩家</th>',
        # The header names what the numerator IS, and has to be re-read whenever the numerator
        # changes: it said 「垃圾造成嘅」 for one commit after the line-clear mechanism joined the
        # count, which made pinglamb's single clear-formed event read as garbage-caused. A column
        # heading is a factual claim about the column.
        '            <th>外力造成嘅 Forecast / 可核 T-spin</th>',
        '            <th>比率</th>',
        '            <th>抽樣 95% CI</th>',
        '            <th>模擬器敏感度範圍</th>',
        '          </tr>',
        '        </thead>',
        '        <tbody>',
        *rows,
        '        </tbody>',
        '      </table>',
        '    </div>',
        '',
        '    <div class="method-note">',
        '      <p>兩欄唔確定性係分開報，因為佢哋講緊兩件事。'
        '<strong>抽樣</strong>係樣本細（Clopper–Pearson 精確區間）；'
        f'<strong>模擬器敏感度</strong>係攞 {len(data["simulator_configs_for_range"])} 個'
        '<em>用唔同方式出錯</em>嘅模擬器設定'
        '（kick table、blockout、lock delay、gravity、垃圾佇列、input clock）各自重算一次，'
        '睇個數飄幾多。</p>',
        '      <p>' + _spread_clause(data) + '</p>',
        '      <p>' + _overlap_clause(data) + '</p>',
        '    </div>',
        '  </div>',
        '</section>',
    ]
    return "\n".join(out)

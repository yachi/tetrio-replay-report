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
        # Every r is null. Under isVerifiedForecast the per-round rate is identically 0, so the
        # odd/even series is constant and the correlation is undefined — a strictly stronger
        # statement than "low". Returning "" here is how the section came to rest on a
        # reliability from the SUPERSEDED numerator; render the degenerate case instead of
        # dropping it. (If the rate is ever non-zero and r is still null for another reason,
        # say nothing rather than assert the zero-rate story.)
        players = data.get("players") or []
        if players and all(p.get("forecast_rate_x1000") == 0 for p in players):
            return ("而且每局嘅數<strong>根本冇得同自己比</strong>："
                    "每局嘅 forecast rate 全部係 0，冇任何變化，"
                    "所以 split-half reliability 係<strong>冇定義</strong>（唔係低）——"
                    "冇變化就冇嘢可以穩定唔穩定。所以下面只列<strong>每個玩家嘅總計</strong>。")
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
    # The sweep's size, READ from the artifact — never the literal 「七」. `simulator_configs_for_range`
    # is emitted from `CONFIGS`, and item 11 proposes adding four more; a hardcoded 七 here would then
    # contradict the count `_coverage_clause` computes from the same list.
    n_cfg = len(data["simulator_configs_for_range"])
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
        return (f"{n_cfg} 個模擬器設定全部計出同一個數，飄幅係零。"
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
        f"即係話喺<em>呢 {n_cfg} 個設定掃到嘅範圍之內</em>，改模擬器對收窄呢個數幫助有限，要收窄佢就要更多場數。"
        # The sweep varies seven FITTED options of one simulator. It bounds parameter
        # sensitivity and nothing else: a shared modelling error — something every one of the
        # seven configs gets wrong the same way — moves all of them together and never appears
        # in this range. Saying flatly that the bottleneck "is not simulator accuracy" claimed
        # more than the sweep measures, so it is stated as the scope-limited fact it is.
        f"要留意呢個掃描只係換咗同一個模擬器嘅 {n_cfg} 個設定，"
        f"<strong>量度唔到呢 {n_cfg} 個設定一齊錯嘅嗰種偏差</strong>，所以佢並唔等於證明咗模擬器本身準。"
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
    # The denominator's SCOPE, measured (schema 8), so `tot` is not published as "all verifiable
    # T-spins": it is the TUCKED, line-clearing subset. `admitted` is every line-clearing verifiable
    # T-spin; `excl` are the line-clearing ones dropped for having no overhang (or no provenance
    # snapshot to read one from), i.e. not tucked.
    admitted = sum(p.get("admitted_lineclearing_tspins", p["verified_tspins"]) for p in ps)
    excl = sum(p.get("tspins_excluded_untucked", 0) + p.get("tspins_excluded_no_snapshot", 0) for p in ps)
    fg = sum(p.get("forecast_garbage", 0) for p in ps)
    lc = sum(p.get("forecast_lineclear", 0) for p in ps)
    # Bare, deliberately, exactly as `_rejection_clause` reads `rejected_by`. A schema-9 artifact
    # that was never re-emitted has no such key and must break the build; `.get(..., 0)` would fold
    # the fifth bucket into 「其餘」 and publish a confident, wrong remainder — the shape that
    # published 「一個 Perfect Clear 都冇出過」 for five sessions against 65 real ones.
    po = sum(p["path_opened"] for p in ps)
    sb = sum(p.get("self_built", 0) for p in ps)
    re_ = sum(p.get("reactive", 0) for p in ps)
    mech = sum(p.get("mechanism_established", 0) for p in ps)
    fc = sum(p.get("forecast_total", 0) for p in ps)
    pre = sum(p.get("floor_pre_existed", 0) for p in ps)
    late = sum(p.get("floor_arrived_later", 0) for p in ps)
    und = sum(p.get("floor_undetermined", 0) for p in ps)
    # `clause2_undecided` is no longer read here. It used to render its own trailing paragraph
    # (「另外有 N 個機制成立、但呢一項查唔到答案」) beside a sentence that had ALREADY counted the
    # same events as clause-2 rejections, so an undecidable event was narrated twice and as two
    # different things. `_rejection_clause` enumerates every uncounted event exactly once, and it
    # keeps the undecidable ones' 「唔會當佢啱亦都唔會當佢錯」 wording. The count itself is still
    # gated: `forecast-facts.test.ts` asserts `clause2_undecided` equals the two undecidable
    # buckets of `rejected_by`, so dropping the read here cannot let the field drift unnoticed.

    # The five kinds partition the tucked line-clearing T-spins, so 「其餘」 below is a REMAINDER and
    # not a fifth number that happens to be printed last. Asserted in the same shape as
    # `_rejection_clause`'s: a bucket the emitter grows without a sentence here would otherwise be
    # swallowed silently, which is precisely how `path_opened` would have shipped as `reactive`.
    if fg + lc + po + sb + re_ != tot:
        raise ValueError(
            "the mechanism buckets do not partition the tucked line-clearing T-spins: "
            f"forecast_garbage {fg} + forecast_lineclear {lc} + path_opened {po} + "
            f"self_built {sb} + reactive {re_} = {fg + lc + po + sb + re_} "
            f"vs verified_tspins {tot}")
    if not tot:
        return ""

    # The fifth bucket, rendered ONLY when it fired. Four of the six sessions have none, and this
    # repo's rule is that an absence renders as an absence — 「0 個」 reads as a measured zero.
    #
    # The reason it is not a forecast is CLAUSE 3 and nothing else. `spec/Forecast.dfy`'s GapClosed
    # is the strictly-inside rule; an access event's cleared rows lie OUTSIDE [roofAt, floorAt], so
    # `IsForecast` is already false on geometry before clause 2 (個底幾時到) or clause 4
    # (埋尾嗰下係咪 T-spin) is ever asked. Do NOT reword it as either of those, and do NOT let it
    # read as a near miss: two published reports already carried a wrong clause here, and the gate
    # re-renders from the same artifact, so it compares the sentence against itself and never
    # against the truth. Nor may it be worded as 自己砌 — that names `self_built`, and this event is
    # not in it.
    #
    # SAY WHAT THE PREDICATE SAYS, AND NOTHING MORE. The branch tests two things and only two:
    # the cleared rows lie outside the slot's own rows (so the clear did not FORM it — a cleared row
    # outside displaces the slot rigidly), and `bestTspinLines(withoutRows(A, clearedRows)) >= target`
    # (the clear ALONE, with the piece never placed, already reaches the executed spin). The second
    # is what takes the credit off the piece, which is the editorial defect this bucket retracts.
    #
    # It does NOT test that the slot is unchanged cell for cell. An earlier draft of this sentence
    # said 「個窿位一格都冇變過，一早就已經喺度」, which is measured and true of both corpus events
    # (`forecast-access-class.test.ts`'s ACCESS_CLASS records rows 34-39 and 24-39 bit-identical) and
    # is NOT what put them in this bucket — nothing stops a future event satisfying the predicate
    # while the piece contributes a wall. This module renders off the artefact's `path_opened` COUNT
    # and never sees that list, so the sentence would have been resting on a property the renderer
    # cannot check. Nor may the per-event detail be smuggled back in as 「呢兩件事上面…」: a
    # corpus-shaped figure hardcoded into per-session prose is the same defect as the 「平均相隔 11
    # 隻棋」 line two paragraphs down, which this section already had to remove once.
    po_txt = (
        f"<strong>{po} 個</strong>係消行<strong>通咗條路</strong>，唔係整咗個窿位出嚟——"
        "<strong>消嗰行自己一個就已經夠</strong>：就算隻棋根本冇落過，"
        "淨係喺落棋之前嗰塊板度刪走同一批行，個 T-spin 就已經入得到，"
        "所以功勞唔算得落隻棋度。"
        "呢一類唔計 forecast，而且唔係差少少："
        "forecast 要求消嗰行啱啱夾喺天花板同窿位中間（即係上面嗰句），"
        "而呢啲消行喺嗰個範圍以外——單睇消嗰行喺邊就已經唔合格，"
        "後面「個底喺唔喺度」同「埋尾嗰下消行係咪 T-spin」根本問都唔使問；"
        if po else "")

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
        (f"呢個 session {admitted} 個消到行嘅可核 T-spin 入面，"
         f"<strong>{tot} 個</strong>係 tucked（T 上面有蓋），先至問得到「個蓋係咪預先搭喺窿位上面」；"
         f"另外 {excl} 個冇蓋，唔算 tucked，唔喺 forecast 範圍。呢 {tot} 個入面："
         if excl else
         f"呢個 session <strong>{tot} 個</strong> tucked（T 上面有蓋）、消到行嘅可核 T-spin 入面"
         "（消行 T-spin 全部有蓋）：")
        + f"<strong>{fg} 個</strong>係垃圾造成個窿位；"
        f"<strong>{lc} 個</strong>係消行造成——消嗰行啱啱夾喺天花板同窿位中間，"
        "消走咗兩者先貼埋一齊；"
        f"{sb} 個係<strong>玩家自己落嗰隻棋整出嚟</strong>嘅——開局定式（例如 C-Spin）就係咁，"
        "個天花板早過個窿位係定式本身嘅砌法，唔係預測；"
        + po_txt
        + f"其餘 {re_} 個個窿位本身冇變好。",
        # Clause 2. Added 2026-08-03: the mechanism clause says WHAT closed the gap, and says
        # nothing about whether there was a hole to close onto. Without it a roof dropped on solid
        # stack that opens up underneath scores exactly like a roof laid over a cavity on purpose.
        "<strong>仲有一個前提：搭天花板嗰陣，個窿位要已經喺度。</strong>"
        "如果落天花板嗰時下面係實心，之後先至開窿，"
        "咁就唔係「預先搭喺個窿上面」，只係執返個之後先出現嘅位。"
        "呢一項唔使追格——provenance 格網記住每一格係邊一手落嘅，"
        "睇住 T <strong>四格全部</strong>各自踩住嗰格係邊一手放低就得——"
        "唔淨止睇最低嗰行：T 塞入去嘅時候多數係兩邊膊頭承住、個鼻尖吊喺個窿度，"
        "淨睇鼻尖下面嗰格會睇到一格空氣，乜都問唔到。"
        f"全部 {tot} 個入面："
        f"<strong>{pre} 個</strong>承住佢嘅格全部早過天花板；"
        f"<strong>{late} 個</strong>個底係天花板之後先至出現；"
        f"{und} 個查唔到（個底係垃圾，而垃圾喺天花板前後都升過，唔追格就分唔到邊行係邊行）。"
        "下面表入面嘅數，係<strong>四項條件全部符合</strong>先計。",
    ]
    if mech > fc:
        parts.append(_rejection_clause(ps, mech, fc))
    if fc == 0:
        parts.append(
            # The old justification here was 「喺平均相隔 11 隻棋嘅窗口入面，幾乎實會有」 — a
            # hardcoded 11 that matches no measured quantity (the real mean roof-to-spin separation
            # over these events is ~4.4, and garbage/clear co-occurs in only 35–44%, not "almost
            # always"). It was a corpus-shaped figure asserted in per-session prose. Regrounded in
            # the finding that DOES hold: co-occurrence is not causation, and reverse-tracing the
            # step shows most were the player's own opener placement (the large self_built count).
            "<strong>換句話講：呢個 session 冇一個 tucked 消行 T-spin 符合曬四項條件。</strong>"
            "之前呢節報過嘅 forecast 數，係「垃圾或者消行喺窗口入面出現過」就算數——"
            "但「出現過」唔等於「整咗個窿位出嚟」：真正要核嘅係嗰下消行或者垃圾有冇造成個窿位，"
            "倒帶逐格一睇，嗰啲數量到嘅多數係<em>開局定式</em>（自己落嘅棋砌個窿），唔係預測。")
    else:
        parts.append(
            "要留意：呢個數細到<strong>一兩件事就當唔到係習慣</strong>，"
            "抽樣區間亦都已經包含咗零，"
            "所以呢度<strong>唔係話邊個識 forecast</strong>，"
            "只係話喺 tucked 消行嘅可核 T-spin 入面，符合定義嘅情況搵到幾多次。")
    # The "openers explain self_built" line above was asserted for weeks with no number beside it.
    # This is that number, and it is the only figure in this section that owes nothing to the
    # simulator — so it says so rather than inheriting the section's disclaimer by silence.
    parts.append(_cspin_clause(data))
    return "".join(parts)


# The six buckets of `rejected_by`, in the emitter's order. Named here so a bucket the emitter
# grows without a sentence to render it is a KeyError in `_rejection_clause`, not a silent drop.
CLAUSE_VERDICTS = (
    "counted",
    "floor_arrived_later",
    "closing_clear_was_spin",
    "floor_arrived_later_and_closing_clear_was_spin",
    "floor_undecidable",
    "floor_undecidable_and_closing_clear_was_spin",
)

# What to SAY about each rejecting bucket, in the order they are listed. Written to read as a
# reason clause, so it works both after 「計唔到數——」 and after 「N 個因為」.
_REJECTION_WORDING = (
    ("floor_arrived_later",
     "個底係天花板之後先至嚟"),
    ("closing_clear_was_spin",
     "埋尾整成個窿位嗰下消行，本身就係一個 T-spin"),
    ("floor_arrived_later_and_closing_clear_was_spin",
     "兩樣都中——個底係天花板之後先至嚟，而且埋尾整成個窿位嗰下消行本身就係一個 T-spin"),
    ("floor_undecidable",
     "個底查唔到（個底係垃圾，而垃圾喺天花板前後都升過）——唔會當佢啱，亦都唔會當佢錯"),
    ("floor_undecidable_and_closing_clear_was_spin",
     "埋尾整成個窿位嗰下消行本身就係一個 T-spin，而個底又查唔到"),
)

# The buckets clause 4 rejected. The gloss below is printed whenever any of them fired.
_CLAUSE4_BUCKETS = ("closing_clear_was_spin",
                    "floor_arrived_later_and_closing_clear_was_spin",
                    "floor_undecidable_and_closing_clear_was_spin")


def _rejection_clause(ps, mech, fc):
    """WHY the mechanism-established events did not count — READ, never assumed.

    This sentence hardcoded clause 2 (「個底係天花板之後先至嚟」) as the reason from 2026-08-03
    until 2026-08-16. Nothing in the artifact said which clause had rejected an event, so the
    renderer picked one, and it picked wrong on two published reports: 2026-08-09 and 2026-08-14
    are both clause 4 — the clear that formed the slot was itself a T-spin — and 08-14's is the
    round carrying the corpus's only DT Cannon. `check_forecast_section.py` re-renders and
    byte-compares, so it could not see it either: both sides read the same absent fact.

    Each clause gets its own wording, and a session where both fired says both with counts.
    Writing 「clause 2 或者 clause 4」 would satisfy the checker and tell the reader nothing,
    which is the trade this repo refuses everywhere else.
    """
    # Bare `p["rejected_by"][k]`, deliberately. A schema-8 artifact that was never re-emitted has
    # no such key and must break the build here; `.get(k, 0)` would render a confident, wrong
    # sentence off an all-zero breakdown — the shape that published 「一個 Perfect Clear 都冇出過」
    # for five sessions against 65 real ones.
    rej = {k: sum(p["rejected_by"][k] for p in ps) for k in CLAUSE_VERDICTS}
    bits = [(rej[k], text) for k, text in _REJECTION_WORDING if rej[k]]
    # The breakdown is exhaustive over the mechanism-established events, so anything that fails to
    # add up means the artifact and this sentence disagree about how many events there are.
    n_rejected = sum(n for n, _ in bits)
    if rej["counted"] != fc or n_rejected != mech - fc:
        raise ValueError(
            f"rejected_by does not partition the mechanism-established events: "
            f"counted {rej['counted']} vs forecast_total {fc}, "
            f"rejected {n_rejected} vs mechanism_established - forecast_total {mech - fc}")

    lead = ("但佢哋全部" if fc == 0 and mech > 1
            else "但佢" if fc == 0
            else f"但當中 {mech - fc} 個")
    if len(bits) == 1:
        body = f"{lead}計唔到數——{bits[0][1]}。"
    else:
        body = (f"{lead}計唔到數："
                + "；".join(f"{n} 個因為{text}" for n, text in bits) + "。")

    # Clause 4 needs its "so what" spelled out;「埋尾嗰下消行係 T-spin」disqualifies for a reason a
    # reader cannot infer from the phrase. Clause 2's own reason is already spelled out in the
    # paragraph above, so it needs none here.
    #
    # DO NOT word this as 「自己砌」 or as "not an outside force". Both are wrong in this section's
    # own vocabulary, which is set two paragraphs up: 外力 is defined there as 「垃圾升起或者消行」,
    # so a line clear IS one, and 自己砌 names the `self_built` bucket — which this event is not in.
    # It is a `forecast_lineclear`, and a reader who was told it was 自己砌 would rightly ask why it
    # is not in that count. The actual disqualifier is circularity: the clear that opened the slot
    # was the spin itself, so the slot and its use are one event rather than a slot that was waiting
    # under a roof built earlier. `spec/Forecast.dfy`'s GapClosedIsExactlyRowsRemoved says the same
    # thing formally — the C-Spin closes its own gap, which is why clause 3 passes there and the
    # rejection has to come from clause 4.
    gloss = ("「埋尾嗰下消行本身係 T-spin」點解唔算數：咁樣即係嗰下 T-spin 自己消走啲行、"
             "自己開返個窿位出嚟，跟住即刻用返佢——個窿位同用個窿位係同一下嘢，"
             "唔係個窿位早就喺度、等住個蓋搭落去。"
             if any(rej[k] for k in _CLAUSE4_BUCKETS) else "")

    return (f"<strong>今次真係有數畀呢啲條件篩走咗。</strong>有 {mech} 個嘅機制係成立嘅"
            f"（消行或者垃圾真係整咗個窿位出嚟），{body}{gloss}")


def _cspin_clause(data):
    """The C-Spin's signature clear, counted by the GAME rather than by the simulator.

    A T-Spin Triple can only be made by a vertical T in a one-wide covered well, which is the shape
    the C-Spin (TKI積み) builds — so this counts the shape, not the opener, and the wording must not
    promote one to the other. What is NOT here is the wiki's full pattern (a Triple followed by a
    Double within three bags): that needs ordering, which only the simulator gives, and the verified
    prefix is both small and a PREFIX, so a Triple near its end has nowhere for its 21-placement
    window to fit. Measured while writing this: 21 to 45 Triples per player per session have no
    room, leaving 1 to 7 observable. A rate over those would be a rate about prefix length.
    """
    ps = data["players"]
    if not any("tspin_triples_game_stats" in p for p in ps):
        return ""
    bits = "、".join(
        f"{html.escape(p['user'])} <strong>{p['tspin_triples_game_stats']}</strong> 個"
        for p in sorted(ps, key=lambda p: -p.get("tspin_triples_game_stats", 0)))
    rounds = max(p.get("rounds_played", 0) for p in ps)
    return (
        "<strong>順帶一提 C-Spin。</strong>"
        "T-Spin Triple 一定要一隻直放嘅 T 塞入一條有蓋嘅單格井——即係 C-Spin（TKI積み）砌嘅嗰個形。"
        f"呢個 session {rounds} 個回合入面，T-Spin Triple 嘅數目係："
        f"{bits}。"
        "呢個數<strong>唔係模擬器計嘅</strong>，係遊戲自己 <code>results.stats</code> 入面嘅記錄，"
        "覆蓋每一個回合而唔止可核嗰段，亦都係兩個獨立 parser 各自抽出嚟對過數嗰一條。"
        "留意佢數嘅係<em>個形</em>唔係<em>開局</em>——TST 唔一定係 C-Spin 開局打出嚟。"
        "至於 wiki 講嘅完整 C-Spin 定式（打完 Triple 之後三個 bag 之內接返個 Double），"
        "要知道次序先計得到，而次序淨係模擬器有；"
        "可核嗰段太短，多數 Triple 根本冇位裝落個 21 手嘅窗口，所以呢度<strong>唔報</strong>。")


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
        '表入面個分母淨係計<em>tucked</em>（T 上面有蓋）、消到行嗰啲——冇蓋就無「預先搭喺個窿上面」可言，'
        '消唔到行就唔係一個 forecast——所以佢係可核 T-spin 嘅一個<strong>子集</strong>，唔係全部。'
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
        '            <th>四項條件全部符合嘅 Forecast / tucked 消行可核 T-spin</th>',
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

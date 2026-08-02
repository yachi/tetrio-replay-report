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
        '      <p>「Forecast」係指打 T-spin 之前，個窿位<em>當時仲未存在</em>：'
        '搭個天花板嗰陣打唔到 T-spin，之後靠垃圾行升起或者消行先至浮出嚟。'
        '對照組叫 reactive，即係位早就喺度。</p>',
        '      <p><strong>統計結論係：搵唔到效果。</strong>'
        '三個分析單位都試過——每局（AUC 58.6%，p = 0.210）、'
        '每次 T-spin（forecast 比 reactive 多送 0.52 attack，95% CI [−0.34, 1.28]，含 0，'
        '而且事前定好嘅 negative control 有反應，證明兩組本身就唔可比）、'
        '每個玩家（p = 0.848）。'
        '而且每局嘅數<strong>連自己都對唔上自己</strong>：'
        'split-half reliability 得 0.29（pinglamb）同 0.064（yachi），'
        '即係每局一個數喺呢個事件密度下根本唔可能穩定，'
        '幾好嘅模擬器都救唔到。所以下面只列<strong>每個玩家嘅總計</strong>。</p>',
        '      <p>「可核 T-spin」係指嗰段棋盤可以同真實對局對得返上（用對手嘅 ige 事件流逐次攻擊校對），'
        '唔係話條數經過 Dafny 證明——呢節冇任何嘢經過證明。'
        '全 158 個 player-round 入面，只有 17.9% 嘅落子對得上，所以樣本先咁細。</p>',
        '    </div>',
        '',
        '    <div class="scroll-x">',
        '      <table class="appendix-table">',
        '        <thead>',
        '          <tr>',
        '            <th>玩家</th>',
        '            <th>Forecast / 可核 T-spin</th>',
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
        '<strong>模擬器敏感度</strong>係攞七個<em>用唔同方式出錯</em>嘅模擬器設定'
        '（kick table、blockout、lock delay、gravity、垃圾佇列、input clock）各自重算一次，'
        '睇個數飄幾多。</p>',
        '      <p>兩者一比就答咗一條好重要嘅問題：'
        '<strong>模擬器嘅飄幅（約 1.5–3 個百分點）遠細過抽樣嘅飄幅（約 13–14 個百分點）。</strong>'
        '即係話呢個數嘅樽頸<strong>唔係</strong>模擬器準唔準，而係局數唔夠——爭大約五倍。'
        '再花力氣改模擬器，對呢個數幫助好有限；要收窄佢就要更多場數。</p>',
        '      <p>兩個玩家嘅區間幾乎完全重疊，所以呢度<strong>冇聲稱邊個 forecast 多啲</strong>。</p>',
        '    </div>',
        '  </div>',
        '</section>',
    ]
    return "\n".join(out)

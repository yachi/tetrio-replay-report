"""The pooled T-Spin Forecast figure for the landing page — simulator-derived, outside the chain.

`bin/build-docs` renders this into `docs/index.html`, so `bin/build-docs --check` regenerates it
from the four `sessions/*/sim/forecast-facts.json` and byte-compares. There is deliberately no
intermediate pooled artefact: an artefact would be one more thing that can go stale, whereas a
figure computed at render time cannot disagree with its inputs.

Everything the per-session section promises applies here and is asserted the same way — no claim
IDs, no ✓ badges, an explicit 未經證明 marker, and prose that states the null. See
`pipeline/forecast_section.py` for why: these numbers come from ONE replay simulator, and the
repo's trust argument is two independently written extractors agreeing byte-for-byte.

**Pooling is checked, not assumed.** Combining sessions is only honest if the sessions are
measuring the same thing, so this computes a chi-square test of homogeneity across sessions and
REFUSES to publish a pooled rate when they disagree. FORECAST-PLAN.md asserted the licence from
figures measured once by hand (p = 0.865 / 0.931 / 0.978); an assertion that happened to hold when
it was written is exactly the defect this section spent a day removing from the per-session
renderer, so it is recomputed on every build.

**No between-player claim.** Pooling narrows the interval on the LEVEL, and the plan measured that
the between-player gap's sign FLIPS under the `frame_clock` simulator config. The level is
simulator-robust; the difference is not. This renders one pooled rate and each player's interval,
and never orders them.
"""
import glob
import json
import math
import os

# A p at or below this says the sessions are NOT measuring the same thing, and pooling them would
# average away a real difference rather than sharpen a real level.
HOMOGENEITY_ALPHA = 0.05


def _lower_gamma_reg(s, x):
    """Regularized lower incomplete gamma P(s, x), by series or continued fraction.

    Written out rather than imported because this repo has no scipy dependency and adding one to
    render a landing page would be a poor trade. Both branches are the standard ones; the series
    converges fast for x < s+1 and the continued fraction for x >= s+1.
    """
    if x < 0 or s <= 0:
        raise ValueError("domain")
    if x == 0:
        return 0.0
    if x < s + 1:
        term = 1.0 / s
        total = term
        n = s
        for _ in range(1000):
            n += 1
            term *= x / n
            total += term
            if abs(term) < abs(total) * 1e-15:
                break
        return total * math.exp(-x + s * math.log(x) - math.lgamma(s))
    # continued fraction for Q(s, x), then P = 1 - Q
    tiny = 1e-300
    b = x + 1 - s
    c = 1 / tiny
    d = 1 / b if b != 0 else 1 / tiny
    h = d
    for i in range(1, 1000):
        an = -i * (i - s)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    q = math.exp(-x + s * math.log(x) - math.lgamma(s)) * h
    return 1 - q


def chi2_sf(x, df):
    """P(X > x) for chi-square with `df` degrees of freedom."""
    if df <= 0:
        return float("nan")
    if x <= 0:
        return 1.0
    return 1.0 - _lower_gamma_reg(df / 2.0, x / 2.0)


def _log_c(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def _binom_cdf(k, n, p):
    """P(X <= k)."""
    if p <= 0:
        return 1.0
    if p >= 1:
        return 1.0 if k >= n else 0.0
    return min(1.0, sum(math.exp(_log_c(n, i) + i * math.log(p) + (n - i) * math.log(1 - p))
                        for i in range(k + 1)))


def clopper_pearson(k, n, alpha=0.05):
    """Exact binomial interval, by bisection on the tails.

    Mirrors `pipeline/sim/emit-forecast-facts.ts`. A second implementation of a
    statistic is a liability in this repo, so `selftest()` requires this one to reproduce EVERY
    per-player interval already committed in the four artefacts — if the two ever disagree, that
    is a failure, not a rounding difference. Computing here rather than emitting a pooled artefact
    is what keeps the figure from going stale, and this cross-check is the price.
    """
    if n == 0:
        return 0.0, 1.0

    def solve(f):
        lo, hi = 0.0, 1.0
        for _ in range(200):
            m = (lo + hi) / 2
            if f(m) > 0:
                lo = m
            else:
                hi = m
        return (lo + hi) / 2

    # `solve` bisects a DECREASING function, so each target is written that way. The upper bound's
    # sign has to be flipped for that reason; getting it wrong prints an upper bound of 0, which
    # is a bug this project has already shipped once.
    lower = 0.0 if k == 0 else solve(lambda p: (alpha / 2) - (1 - _binom_cdf(k - 1, n, p)))
    upper = 1.0 if k == n else solve(lambda p: _binom_cdf(k, n, p) - (alpha / 2))
    return max(0.0, lower), min(1.0, upper)


def load_all(repo):
    """Every session's committed forecast artefact, oldest first. Missing ones are simply absent."""
    out = []
    for path in sorted(glob.glob(os.path.join(repo, "sessions", "*", "sim", "forecast-facts.json"))):
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        out.append((os.path.basename(os.path.dirname(os.path.dirname(path))), data))
    return out


def homogeneity(artefacts):
    """Chi-square test that the sessions share one forecast rate, per player and overall.

    Returns None when there is nothing to test (fewer than two sessions, or no events). A null
    here means "not testable", and the caller must refuse to pool rather than assume licence.
    """
    per_user = {}
    for _, data in artefacts:
        for p in data["players"]:
            per_user.setdefault(p["user"], []).append((p["forecast_total"], p["verified_tspins"]))
    cells = []
    for cnts in per_user.values():
        if len(cnts) >= 2:
            cells.append(cnts)
    if not cells:
        return None
    results = {}
    for user, cnts in per_user.items():
        if len(cnts) < 2:
            continue
        stat = _chi2_stat(cnts)
        if stat is None:
            continue
        results[user] = {"chi2": stat, "df": len(cnts) - 1,
                         "p": chi2_sf(stat, len(cnts) - 1)}
    if not results:
        return None
    return results


def _chi2_stat(cnts):
    """Chi-square for a 2xK table of (successes, trials) against the pooled rate."""
    tot_k = sum(k for k, _ in cnts)
    tot_n = sum(n for _, n in cnts)
    if tot_n == 0 or tot_k == 0 or tot_k == tot_n:
        return None
    p = tot_k / tot_n
    stat = 0.0
    for k, n in cnts:
        if n == 0:
            continue
        for obs, exp in ((k, n * p), (n - k, n * (1 - p))):
            if exp <= 0:
                return None
            stat += (obs - exp) ** 2 / exp
    return stat


def pool(artefacts):
    """Pooled counts and intervals, or None when there is nothing publishable.

    x1000 integers, in the direction the repo's 約 convention requires: point estimates and
    interval LOWER bounds FLOOR, UPPER bounds CEIL, so an interval can only widen.
    """
    if not artefacts:
        return None
    per_user = {}
    sessions = []
    for name, data in artefacts:
        sessions.append(name)
        for p in data["players"]:
            u = per_user.setdefault(p["user"], {"fc": 0, "ts": 0})
            u["fc"] += p["forecast_total"]
            u["ts"] += p["verified_tspins"]
    total_fc = sum(u["fc"] for u in per_user.values())
    total_ts = sum(u["ts"] for u in per_user.values())
    if total_ts == 0:
        return None

    def interval(k, n):
        lo, hi = clopper_pearson(k, n)
        return math.floor(1000 * lo), math.ceil(1000 * hi)

    lo, hi = interval(total_fc, total_ts)
    players = []
    for user in sorted(per_user):
        u = per_user[user]
        if u["ts"] == 0:
            continue
        plo, phi = interval(u["fc"], u["ts"])
        players.append({"user": user, "fc": u["fc"], "ts": u["ts"],
                        "rate_x1000": math.floor(1000 * u["fc"] / u["ts"]),
                        "lo_x1000": plo, "hi_x1000": phi})
    hom = homogeneity(artefacts)
    # Licence to pool: every player's rate must be consistent across the sessions. `None` means
    # the question could not be asked, which is NOT the same as a pass.
    poolable = bool(hom) and all(r["p"] > HOMOGENEITY_ALPHA for r in hom.values())
    return {
        "sessions": sessions,
        "forecast_total": total_fc,
        "verified_tspins": total_ts,
        "rate_x1000": math.floor(1000 * total_fc / total_ts),
        "ci95_lo_x1000": lo,
        "ci95_hi_x1000": hi,
        "players": players,
        "homogeneity": hom,
        "poolable": poolable,
    }


def _pct(x1000):
    return f"{x1000 / 10:.1f}%"


def section(pooled):
    """The landing-page card, or None when there is nothing honest to show."""
    if pooled is None:
        return None
    n_sessions = len(pooled["sessions"])
    parts = [
        "<h2>T-Spin Forecast（模擬器推導 · 未經證明）</h2>",
        "<div class='grid'><div class='card'>",
        "<div class='date'>SIMULATOR-DERIVED · NOT IN THE PROOF CHAIN</div>",
    ]
    if not pooled["poolable"]:
        # Refusing is the honest outcome, and it must read as a refusal rather than as a missing
        # number. Either the sessions disagree, or the question could not be asked at all.
        why = ("各 session 之間嘅比率唔一致"
               if pooled["homogeneity"] else "夠唔夠格合併呢個問題本身答唔到")
        parts += [
            "<div class='title'>唔合併</div>",
            f"<p class='blurb'>{why}，所以呢度<strong>唔出一個合併數字</strong>。"
            f"逐個 session 嘅數字喺各自嘅戰報入面。</p>",
            "</div></div>",
        ]
        return "".join(parts)
    parts += [
        f"<div class='title'>{_pct(pooled['rate_x1000'])}"
        f"<span style='font-size:.8rem;color:var(--muted)'> "
        f"[{_pct(pooled['ci95_lo_x1000'])}, {_pct(pooled['ci95_hi_x1000'])}]</span></div>",
        f"<div class='meta'>{pooled['forecast_total']} / {pooled['verified_tspins']} "
        f"可核 T-spin · {n_sessions} 個 session 合併</div>",
        "<p class='blurb'>喺可核（早局）嘅 tucked T-spin 入面，"
        "打之前個窿位仲未存在嘅大約佔咁多。"
        "呢個數<strong>唔係</strong>由兩個獨立 parser 抽出嚟、亦<strong>冇</strong>經 Dafny 證明——"
        "佢由一個 replay 模擬器重跑操作記錄推導出嚟，所以冇 claim 編號、冇 ✓ 標記。</p>",
        "<p class='blurb'>合併之前有驗過各 session 一唔一致（"
        + "、".join(f"{u} p = {r['p']:.3f}" for u, r in sorted(pooled["homogeneity"].items()))
        + "）。合併淨係令<em>水平</em>嘅區間窄咗；"
        "兩個玩家邊個高呢一點<strong>唔穩陣</strong>（換個模擬器設定就會反轉），所以呢度唔排名。</p>",
        "<div class='meta'>"
        + " · ".join(f"{p['user']} {_pct(p['rate_x1000'])} "
                     f"[{_pct(p['lo_x1000'])}, {_pct(p['hi_x1000'])}]"
                     for p in pooled["players"])
        + "</div>",
        "<span class='pill'>未經證明 · 探索性資料</span>",
        "</div></div>",
    ]
    return "".join(parts)


def selftest(repo):
    """Controls. Returns a list of failures; empty means the module agrees with the artefacts."""
    bad = []
    artefacts = load_all(repo)
    if not artefacts:
        # A repo with no forecast artefacts is a legitimate state, and `section()` renders
        # nothing for it. Failing here would break the docs build for that state. Losing the
        # artefacts is still caught, one level up: regeneration would omit the card and the
        # byte-compare against the committed index.html would report drift.
        return []

    # 1. The Python Clopper-Pearson must reproduce EVERY interval the TypeScript emitter already
    #    committed. This is the whole justification for having a second implementation.
    checked = 0
    for name, data in artefacts:
        for p in data["players"]:
            lo, hi = clopper_pearson(p["forecast_total"], p["verified_tspins"])
            want_lo, want_hi = p["sampling_ci95_lo_x1000"], p["sampling_ci95_hi_x1000"]
            got_lo, got_hi = math.floor(1000 * lo), math.ceil(1000 * hi)
            if (got_lo, got_hi) != (want_lo, want_hi):
                bad.append(f"{name} {p['user']}: python CP [{got_lo}, {got_hi}] != "
                           f"committed [{want_lo}, {want_hi}]")
            checked += 1
    if checked == 0:
        bad.append("no player intervals were cross-checked — the control proved nothing")

    # 2. The pooled point estimate must be the floored quotient of the counts it is printed beside.
    pooled = pool(artefacts)
    if pooled is None:
        bad.append("pool() returned None over committed artefacts")
    else:
        r, k, n = pooled["rate_x1000"], pooled["forecast_total"], pooled["verified_tspins"]
        if not (r * n <= 1000 * k < (r + 1) * n):
            bad.append(f"pooled rate {r} is not the floored quotient of {k}/{n}")
        if not (pooled["ci95_lo_x1000"] <= r <= pooled["ci95_hi_x1000"]):
            bad.append("pooled point estimate lies outside its own interval")

    # 3. Heterogeneous input must be REFUSED, not silently pooled. Without this the licence check
    #    is decorative — the committed corpus is homogeneous, so the refusal path never runs.
    fake = [(n, json.loads(json.dumps(d))) for n, d in artefacts]
    if len(fake) >= 2:
        for p in fake[0][1]["players"]:
            p["forecast_total"] = 0
        for p in fake[-1][1]["players"]:
            p["forecast_total"] = p["verified_tspins"]
        forced = pool(fake)
        if forced is not None and forced["poolable"]:
            bad.append("pool() accepted a corpus whose sessions plainly disagree")
        if forced is not None and "唔合併" not in (section(forced) or ""):
            bad.append("the refusal path does not render as a refusal")

    # 4. The rendered card must never look like a proved claim.
    html = section(pooled) or ""
    if "未經證明" not in html:
        bad.append("the pooled card does not declare itself unproved")
    for token in ("data-claim", "claim-badge", "已驗證"):
        if token in html:
            bad.append(f"the pooled card carries {token} — simulator output must not be badged")
    return bad

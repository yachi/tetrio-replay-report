# Phase-2 convergence review — SESSION-2 (2026-07-24) report

Scope: `claims-narrative.json` (C001–C024) + `narrative-beats.md`; `claims-coaching.json` (R001–R024) + `recommendations.md`; verified against `facts.json` via `check_claims.py` and targeted probes.

Baseline: **48/48 python_checks pass** (24 C + 24 R, 0 fail). ID hygiene clean — no duplicate ids, no dangling (defined-not-used) or missing (used-not-defined) ids in either md↔ledger pair. Register scan found **no simplified glyphs** and no standard-written-Chinese constructions (the single `不` on `narrative-beats.md:31` is inside colloquial `不過`, acceptable). Checks are Dafny-translatable: no float division, no `sorted`, no `statistics`/`.mean`; variance claims R019/R020 correctly use the integer identity `50*sum(x^2) - (sum x)^2`.

Ground truth reconciled: match winners P,Y,P,P,P,Y,Y; scores m1 0-5, m2 5-2, m3 3-5, m4 0-5, m5 3-5, m6 5-3, m7 5-4; round wins P29/Y21 of 50; sweeps m1,m4 (both pinglamb); decider m7 (yachi). All superlatives (C007 apm 95498, C008 vs 178457, C009 shortest 21023, C010 spike 17, C011 longest 240131, C013 combo 8, C018 tspins 18, C019 btb 8, C020 match-apm 64901, R013 spikes 17/15, R016 gaps 12215/14055) verified to quantify over all candidates and land on the true extremum.

---

## BLOCKER

### B1 — Session-1 numeric leakage `6:4` in published prose
`narrative-beats.md:5` — 「上場俾 yachi 6:4 壓住嚟打嘅 pinglamb」. The figure `6:4` is a SESSION-1 match score. This dataset contains only the 7 SESSION-2 matches (series 4-3); `6:4` is **not derivable from `facts.json`**, carries no claim id, and cannot be given one. This violates the rule that prose may reference the prior session only qualitatively and that every countable statement in the report must be a verified ledger entry — an unverifiable factual number would ship.
**Fix:** delete the number, keep the qualitative revenge framing, e.g. 「上場俾 yachi 壓住嚟打嘅 pinglamb」. The 「復仇/攞返場」 framing and the qualitative `narrative-beats.md:37` line 「上場輸咗嘅人今次贏返個 title」 are fine as-is.

---

## MAJOR

### M1 — Four middle-match final scores stated in prose with no covering claim
`narrative-beats.md` states four per-match final scores as bare numbers with no claim id:
- `:15` m2 「反手 5:2 贏返嚟」 (actual y5-p2 ✓)
- `:19` m3 「pinglamb 最後 3:5 收咗呢場」 (actual y3-p5 ✓)
- `:27` m5 「一路壓住 5:3 攞落」 (actual y3-p5, pinglamb-first ✓)
- `:31` m6 「第六場反手 5:3 贏返」 (actual y5-p3 ✓)

The numbers are correct against `facts.json`, but only m1/m4/m7 scores are gate-verified and claimed (C003/C004/C014); m2/m3/m5/m6 are neither in the gate list nor in any ledger entry. Rule: every factual claim in the report MUST be a ledger entry.
Secondary nit inside this finding: score orientation is inconsistent — m2/m6 written winner-first, m5 winner(pinglamb)-first, but m3 written loser-first `3:5`. Standardize to one convention.
**Fix:** add four score claims, e.g.
`facts['matches'][1]['score']=={'yachi':5,'pinglamb':2}` (m2),
`facts['matches'][2]['score']=={'yachi':3,'pinglamb':5}` (m3),
`facts['matches'][4]['score']=={'yachi':3,'pinglamb':5}` (m5),
`facts['matches'][5]['score']=={'yachi':5,'pinglamb':3}` (m6); all four evaluate True. Tag the four prose lines with the new ids.

---

## MINOR

### m1 — C023 canto mislabels m6/m7 position
`claims-narrative.json` C023 canto: 「yachi 尾二尾三兩場 m6 同 m7 連贏」. m6/m7 are the **last two** matches (尾一/尾二), not 尾二/尾三. `narrative-beats.md:37` already uses the correct 「封尾」. Since canto is "text as it may appear in the report," fix to 「yachi 尾二尾一兩場 m6 同 m7 連贏」 or 「最後兩場 m6 同 m7」.

### m2 — C006 nine-round streak concatenates across the m3→m4 match boundary
C006 check spans `flat[16:25]` = last 4 rounds of m3 + all 5 of m4 (verified: `flat[15]`=yachi, `flat[16:20]`=PPPP within m3, `flat[20:25]`=PPPPP m4, `flat[25]`=yachi). The rounds are genuinely consecutive and the prose discloses the span (`narrative-beats.md:23` 「由 m3 尾到 m4 收爐」), so it is defensible — but 「連續贏咗九局都冇停過手」 glosses the intervening match reset (m3 ended at 5-3, m4 is a fresh game). Consider softening to 「跨住兩場連贏九局」.

### m3 — kills stat (C021 / R009, 29:21) is identical to round wins by construction
Probe: leaderboard kills = round-level kills = round wins = P29/Y21 for both players (1 KO per round win in first-to-death 1v1). C021/R009 checks are non-vacuous (they sum real fields), but `narrative-beats.md:5` presents 「殺人數一樣係 29 比 21」 alongside the round-win line as if corroborating evidence when it is the same figure (the canto's 「一樣」 half-acknowledges this). Consider noting they coincide, or drop one to avoid implying two independent signals.

### m4 — uncited approximate duration 「打足成三分鐘」
`narrative-beats.md:15` (m2 round index 2) — actual max lifetime 179950 ms ≈ 179.9 s, so 「成三分鐘」 is accurate color but is an uncited number. Either keep as pure qualitative color or add a bounded claim (`179000 <= ... < 180000`).

### m5 — C024 rounding deviates from the guide's floor convention
C024 「約25秒」 for lifetime 24942 ms (24.94 s). The guide's stated convention (「約51」→`51000<=x<52000`, i.e. floor) would render this 「約24秒」, and the check bound `24000<=24942<25000` corresponds to floor-24. Nearest-integer rounding to 25 is defensible, but it is inconsistent with C009 (21023→「約21」, floor) and C011 (240131→「約240」, floor). Either state 「約24秒」 or accept nearest-integer and note the convention exception.

---

FINDINGS: 1 blocker, 1 major, 5 minor

---

## Round 2

Re-verified against current files: **28/28 checks pass** (C001–C028), ID hygiene clean (28 ids, 0 dup, 0 dangling, 0 missing), no simplified glyphs, no SWC markers (的/了/是/在/他 all zero) in the edited prose.

Round-1 findings — all resolved:
- **B1 (blocker)** RESOLVED — `narrative-beats.md:5` now 「上場俾 yachi 壓住嚟打嘅 pinglamb」; grep for session-1 numeric scores returns 0 hits. Revenge framing kept qualitatively.
- **M1 (major)** RESOLVED — four new score claims added: C025 (m2 5-2, idx1), C026 (m3 5-3, idx2), C027 (m5 5-3, idx4), C028 (m6 5-3, idx5); each pins the correct match index and asserts the winner (non-vacuous). Prose lines :15/:19/:27/:31 tagged accordingly. Score orientation standardized to winner-first throughout (m3 flipped 3:5→5:3).
- **m1** RESOLVED — C023 canto now 「yachi 最後兩場 m6 同 m7 連贏」 (was 「尾二尾三」).
- **m2** RESOLVED — C006 canto/gloss now 「跨住兩場連贏九局」/"spanning the end of m3 into m4"; prose :23 discloses the reset (「中間 m3 打完重新開過 m4」).
- **m3** RESOLVED — kills stat reframed at :5 as 「1v1 一局一命，呢 29 條命亦即係佢收埋嘅殺人數 [C021]」 — now stated as identical-by-mechanic, not independent evidence.
- **m4** RESOLVED — uncited 「成三分鐘」 replaced with qualitative 「拖到好長命」 (no number).
- **m5** RESOLVED — C024 now 「約 24 秒」 (canto + prose :35); floor convention consistent with C009 (21) and C011 (240).

Fresh sweep on new/changed claims and prose: no new blocker/major/minor. C025–C028 winner assertions prevent vacuity; C006 gloss matches the check; C024 bound `24000<=24942<25000` matches 「約24」. Semantic-honesty, cross-ledger, and Dafny-translatability dimensions unchanged from round 1 (new claims are integer dict-equality checks).

ROUND-2 FINDINGS: 0 blocker, 0 major, 0 minor. CONVERGED.

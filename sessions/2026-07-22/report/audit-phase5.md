# Phase 5 — Adversarial Audit of report.html

Auditor: agent V (final gate before publication). Everything was scripted with `python3` /
Playwright against `report.html`, `facts.json`, the claim ledgers, the proof map, the Dafny
sources, and the raw `.ttrm` files. Nothing was skimmed visually only.

**FINDINGS: 0 blocker, 0 major, 3 minor**

The artifact is publishable. Every factual/countable statement in the body prose, the
JS-rendered per-match cards, the charts, and the appendix is backed by a badge whose ledger
`python_check` I re-evaluated to `True` against `facts.json`, and I re-derived 10 rendered
claims all the way back to the raw `.ttrm` files with exact agreement. The three minor findings
are character-variant typos and one presentation nuance — none affects a number, a proof, or the
trust chain.

---

## What passed (evidence)

### 1. Claim coverage
- Two badge mechanisms exist: `<span class="badge" data-claim="Cxxx">` (76 instances, 44 unique,
  JS-rewritten into `<a href="#claim-…">✓Cxxx</a>`) in static prose + charts, and `<b>Cxxx</b>`
  markers (20 unique) inside the `match-copy` per-card narratives. **Union = all 54 claims** are
  referenced somewhere outside the appendix; 0 orphans.
- Every countable in the static prose and in all 10 match cards sits next to a badge that covers
  it. Per-match final scores (5-2, 4-5, 4-5, 5-3, 5-3, 5-1, 3-5, 5-3, 2-5, 5-4) are covered by
  **C026** (which lists all ten verbatim) plus per-card badges (C022/C011/C025/C014/C004…).
- All chart numbers recompute exactly from `facts.json`: `per_match` apm/pps/vs (÷1000),
  `grouped_clears` (729/755, 359/302, 105/93, 373/293, 53/40, 292/339, 53/82), and the stat panel
  (pieces 7546/6971, attack-per-piece 0.596/0.642, garbage_cleared 1368/1324, finesse 14.6%/21.5%,
  hold 38.3%/36.7%). 0 mismatches.

### 2. Badge ↔ ledger ↔ proof bijection
- 27 narrative (C0xx) + 27 coaching (R0xx) = 54 unique ids; no dups. All 54 present in
  `claims-proof-map.json` with `status: "verified"`; 0 extras.
- **All 54 `python_check`s re-evaluate to `True`** against `facts.json` (I ran them; 0 fail).
- Rendered appendix has exactly **54 rows**; every row's canto + english_gloss + lemma name match
  the ledgers **verbatim** (0 mismatches). Every row shows `✓ 已驗證`.
- 109 badge anchors, **0 broken** — each resolves to its `#claim-Cxxx` appendix row.
- Every one of the 54 lemma names in the proof map exists in `dafny/Claims_narrative.dfy` /
  `Claims_coaching.dfy`, and spot-checked bodies (C001, C015) carry real non-trivial `ensures`
  clauses encoding the claim, not `assert true`.

### 3. Numeric rendering
- x1000 fields render ÷1000 correctly (spot-checked ~15: apm/pps/vs across per_match + m10 final
  round 135.9/94.0/74/43, attack-per-piece, finesse/hold rates).
- `lifetime` ms→s correct: 228310 ms → "228.3s" / 約228秒; 15054 → 約15秒; 262582 vs → 262.6.
- 「約」 present on every canto that states a rounded rate/duration (all decimal- and 秒-bearing
  claims checked; 0 missing).

### 4. Semantics
- Queued-attack vs materialized-garbage discipline holds: **R019** distinguishes 射埋嚟嘅攻擊
  (queued, `garbage_events` sum = 3667) from 真係食咗嘅垃圾 (materialized, `garbagereceived` = 3127);
  **C016/C027** use 真係食 (garbagereceived); the m2 card says "真係食咗127行 / pinglamb 得109行"
  (materialized). No conflation.
- Methodology 附錄 is honest: it attributes extraction trust to the **dual parsers** (step 1) and
  claim trust to the **Dafny lemmas** (step 2) separately. It does **not** claim Dafny proves the
  extraction. The "窮舉證明 vs 跑幾個 sample" contrast is fair for full-dataset formal verification.

### 5. Cantonese register
- No 書面語/Mandarin markers anywhere (swept 的/了/是/在/他們/沒有/什麼/嗎/吧/和/很… → 0 hits) in
  prose, cards, or canto. Register matches `narrative-beats.md`. (See minor #1 for character
  variants.)

### 6. Technical
- Self-contained: only external URI is the SVG `xmlns` (`http://www.w3.org/2000/svg`); **0**
  fetch/XHR/`<link>`/`src=`/`@import`. `<meta charset="utf-8">` present. Title set.
- At 390px width, `document.scrollWidth == clientWidth == 390` — **no body-level horizontal
  scroll**. Wide charts (sw 520–732) live inside `.scroll-x` containers with `overflow-x:auto`.
- Light and dark both render correctly; `:root[data-theme]` overrides win over
  `prefers-color-scheme` in both directions (screenshots captured).

### 7. Truth spot-check (deepest end-to-end)
Re-derived directly from the raw `.ttrm` files, bypassing `facts.json`, all exact:
C001 (6/4, match order), C002 (43/36/79), R004 (7546/6971, Δ575), R008 (quads 373/293),
C020/R012 (allclear 12/7), R011 (tspins 406/482, Δ76), C013 (maxspike 16, ×3), C006 (228.31s @
m2r2), C007/C023 (204 lines, 127/109 garbage), C004 (m10: down 2-4 after r6, won last 3 → 5-4).
Also confirmed `facts.json` and `facts2.json` are byte-identical under `jq -S`.

---

## Minor findings

### MINOR-1 — Simplified-character contamination in visible traditional text
Three user-visible locations mix simplified glyphs into an otherwise fully-traditional document.
Same words, fully legible, no meaning change — a register/polish defect, not a factual one:
- Coaching section H3 heading: **「慢工實净型」** — `净` should be `淨` (note it even mixes 實(trad)+净(simp) in one 4-char label, so clearly a typo).
- Appendix row **R006**: 「…每局平均 APM **净**係叻 yachi 少少」 — `净` → `淨`.
- Appendix row **R007**: 「…佢慢啲但係打得**实净**」 — `实净` → `實淨`.

(Also `关键时刻` appears inside a **CSS comment** `/* STAT GRID (关键时刻) */` — not rendered,
trivia only.) These simplified glyphs live in the source ledgers/HTML, so a fix means editing
`claims-coaching.json` (R006, R007) + report.html heading and re-running `build_appendix.py`.

### MINOR-2 — Two different "T-spin total" figures for the same players (both correct, never juxtaposed)
The coaching prose cites 整體 T-spin **482** (pinglamb) / **406** (yachi) from the raw `tspins`
stat field (claim R011, verified). The clears-distribution chart shows the line-type breakdown,
whose T-spin bars sum to **461** / **398**. The gap is the standard TETR.IO distinction (`tspins`
counts all T-spin placements incl. no-line/mini; `clears.tspin*` counts only line-clearing ones).
Both numbers are individually verified and the report never labels 461/398 as "整體 T-spin", so
there is no on-screen contradiction — but an attentive reader who sums the chart bars against the
text may be confused. Consider a one-line footnote if desired. Non-blocking.

### MINOR-3 — Display headline numbers omit 「約」 (by design, acceptable)
Stat-card headline figures render exact values without 約 ("228.3s", "262.6 vs", "16") while the
adjacent claim sentences correctly use 約228秒 etc. This is the intended split (exact display vs
hedged prose) and matches the ledger discipline; logged only for completeness, no action needed.

---

## Verdict
**FINDINGS: 0 blocker, 0 major, 3 minor.** Ship it. The only edit worth making before publication
is MINOR-1 (four simplified glyphs → traditional in the R006/R007 canto and the pinglamb heading).

## Round 2 — Fix verification & convergence

Scope: verify H's MINOR-1/MINOR-2 fixes in the current `report.html` + `claims-coaching.json`; no
re-litigation of accepted round-1 cosmetics (MINOR-3, CSS-comment glyphs). Re-ran programmatically.

**FINDINGS: 0 blocker, 0 major, 0 minor — CONVERGED.**

- **MINOR-1 (simplified glyphs) fixed and clean.** Ledger now reads R006 「…APM **淨**係叻…」 and
  R007 「…打得**實淨**」; the coaching heading is 「慢工**實淨**型」. A full simplified-glyph sweep over
  all *visible* text (prose + 10 cards + 54 canto, with `<script>/<style>/comments` stripped)
  returns **0** hits — including 约/净/实. Rendered appendix cells for R006/R007 show the corrected
  淨/實淨 verbatim.
- **MINOR-2 (T-spin figure) fixed honestly.** New chart footnote: 「呢個圖表淨係計有消行嘅 T-spin，
  所以會少過整體 T-spin 總數 ✓R011——整體總數連冇消行嘅 T-spin 都計埋。」 Correct Cantonese, correct 淨
  glyph, **no Mandarin markers, and no new bare number** (it defers the count to R011 rather than
  restating 482/461), so no untagged countable is introduced. The R011 badge in the footnote
  renders as ✓R011 and its anchor resolves to the appendix row (verified in-browser).
- **Island / appendix intact.** Regenerated `claims-data` island: 54 claims,
  `total_claims`/`verified_count` = 54/54, `proof_map_available` true; **0** canto/gloss/lemma/
  status mismatches vs the updated ledgers (R006/R007 carried through). Rendered appendix = **54
  rows, all 54 「已驗證」**. Badge anchors 109 → **110** (the single new R011 footnote badge), **0
  broken**. All 54 claims still referenced outside the appendix.
- **Regression clean.** All 54 `python_check`s still evaluate `True`. Chart `per_match` (0 errors
  vs facts) and `totals` (pieces/attack, 0 errors) unchanged. The 20 unique per-match-card
  `<b>Cxxx</b>` badges are byte-identical to round 1 (same set, same per-card assignment). Only
  three deltas exist versus round 1: the corrected heading glyph, the R006/R007 canto glyphs
  (ledger + island + appendix), and the added footnote (+1 R011 badge). Nothing else changed
  semantically.

**Verdict: converged — 0 findings. Ship it.**

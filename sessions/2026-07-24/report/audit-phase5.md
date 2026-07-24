# Phase 5 — Adversarial Audit of report.html (SESSION-2)

Auditor: agent V. Everything scripted with `python3` + Playwright against `report.html`,
`facts.json`, the claim ledgers, the proof map, the Dafny sources, and the raw `../*.ttrm` files.
Same rubric as the session-1 audit.

**FINDINGS: 0 blocker, 1 major, 0 minor**

One factual error in visible prose: the yachi coaching-overview reverses the fast-game win/loss
record (says yachi won 11 / lost 5 when he won 5 / lost 11). Everything else — coverage, the
badge↔ledger↔proof bijection, numeric rendering, the three-way T-spin reconciliation, semantics,
register, self-containment, responsiveness, and a 12-claim end-to-end re-derivation from the raw
`.ttrm` files — passes clean.

---

## MAJOR-1 — Fast-game record reversed in the yachi coaching overview
The yachi "問題係" overview paragraph reads:

> 快局崩盤：40 秒內收工嘅快局，**yachi 5 敗 11 勝**（對 pinglamb 反轉）〔R010〕

Literally "yachi 5 losses, 11 wins" — i.e. it claims yachi **won 11** fast games. That is the
exact reverse of the truth. Ground truth, verified three independent ways:
- Ledger R010: 「40 秒內收工嘅快局，pinglamb 贏 11 局，yachi 得 5 局」 (python_check passes).
- Dafny lemma name: `R010_in_rounds_ending_under_40s_pinglamb_won_11_yachi_5`.
- **Raw `.ttrm` re-derivation**: rounds with `max(lifetime) < 40000ms` → pinglamb wins 11, yachi 5.

So yachi **wins 5 / loses 11** in fast games. The sentence is self-contradictory (its own framing
word 「快局崩盤」 = *fast-game collapse* is incompatible with "won 11"), it contradicts the badge it
carries (R010), and it contradicts the **same figure stated correctly twice elsewhere in the
report**:
- Recommendation #1 (yachi): 「40 秒內嘅局 **5 勝 11 敗**」 ✓ correct.
- pinglamb overview: 「40 秒內快局 **11 勝 5 敗**」 ✓ correct.

Scope: prose-only in `report.html`; the ledger, proof map, and Dafny lemma are all correct — only
this one rendered sentence is wrong. Fix is a two-character swap: **「yachi 5 敗 11 勝」 → 「yachi 5
勝 11 敗」** (the 「（對 pinglamb 反轉）」 parenthetical then still reads correctly). Rated MAJOR rather
than BLOCKER because the artifact is otherwise sound, the correct number appears twice more, and
the intended meaning is unambiguous — but it MUST be fixed before publication, since a sentence
stating the opposite of its own verified badge directly undercuts the report's whole premise.

---

## What passed (evidence)

### 1. Claim coverage
- Two badge mechanisms: `<span data-claim>` (87 instances, 40 unique) + `<b>Cxxx</b>` markers in
  the `match-copy` cards (23 unique). Union = **all 52 claims** referenced outside the appendix; 0
  orphans.
- Every badged countable in prose/cards/charts recomputes from `facts.json` **except MAJOR-1**.
  Spot-checked highlight cards all exact: longest round 240.1s (m3r3), shortest 21s (m5r2),
  95.5 APM / 178.5 vs (m5r2, both session-max), spike 17 pinglamb / 15 yachi, m7 5:4, 8-combo
  (m3r3) vs 8-B2B (m6r5) correctly distinguished.
- All chart numbers recompute exactly: clears bars (Single 451/485 … TSD 189/232, TST 32/52),
  stat panel (pieces 4748/4439, attack-per-piece 0.611/0.669, cleared 874/886, finesse 16.0%/17.6%,
  hold 37.7%/38.4%). 0 errors.

### 2. Badge ↔ ledger ↔ proof bijection
- 28 C-claims + 24 R-claims = 52 unique; all present in the proof map as `verified`; 0 dups/extras.
- **All 52 `python_check`s re-evaluate True** against `facts.json`; `facts.json` == `facts2.json`
  byte-identical under `jq -S`.
- Rendered appendix = **52 rows**, all 「已驗證」; canto + gloss + lemma match the ledgers
  **verbatim** (0 mismatches). 110 badge anchors, **0 broken**; **0** badges show ✓ without
  `data-status="verified"`. Every one of the 52 lemma names exists in the Dafny sources.

### 3. Numeric rendering
- ×1000 → ÷1000 correct across apm/pps/vs, attack-per-piece, finesse/hold rates, and SVG chart
  labels (~15+ spot-checks). `lifetime` ms→s correct (240.1s, ~21s, ~24s). 「約」 present on every
  rounded rate/duration claim; R010's "40秒" is a threshold (not a rounded measurement), so its
  lack of 約 is correct.

### 4. Semantics
- Queued vs materialized discipline holds: C011/C012 use 「射埋嚟嘅攻擊」 for `garbage_events`
  (m3r3 177/158, queued), and R022 frames cancel = queued − received (yachi 333, pinglamb 329).
- **T-spin three-way figure is handled cleanly, no conflation.** The report uses: R007 TSD 232/189,
  R023 TST 52/32, and R008 「T-spin double + triple」 = **284/221** (doubles+triples). The chart
  shows TSS/TSD/TST bars separately, and a footnote explicitly reconciles: 「TSD 同 TST 兩條 bar 加埋
  …（pinglamb 284、yachi 221）〔R008〕——TSS 冇計落嗰個總數度」 (verified: 232+52=284, 189+32=221).
  The raw `tspins` stat (321/266) is used only for C018's single-round max (18). No unlabeled
  255/307 or 266/321 "total" is ever shown, so the three sums never collide on screen.
- Methodology 附錄 honest: attributes extraction trust to the dual parsers (7 `.ttrm` files) and
  claim trust to the Dafny lemmas separately; does **not** claim Dafny proves the extraction.
- **Zero session-1 numbers.** Revenge references are purely qualitative (「上場俾 yachi 壓住嚟打」,
  「上場輸咗嘅人今次贏返個 title」). A fingerprint scan for session-1 values (79 rounds, 6-4, 228.3s,
  262.6, 7546…) is clean (the lone "79" hit is inside "1792", the hold count).

### 5. Cantonese register
- **0 simplified glyphs**, **0 書面語/Mandarin markers** across prose + 7 cards + 52 canto.

### 6. Technical
- Self-contained: only external URI is the SVG `xmlns`; **0** fetch/XHR/`<link>`/`@import`.
  `<meta charset="utf-8">` is the **first** line. Title set. Balanced structure.
- At 390px, `scrollWidth == clientWidth == 390` — **no body-level horizontal scroll**.
- Light and dark both render correctly; `:root[data-theme]` overrides win in both directions
  (screenshots captured).

### 7. Truth spot-check (deepest end-to-end)
Re-derived 12 claims straight from the raw `../*.ttrm` files, all exact: C001 (yachi 3 / pinglamb
4, order p,y,p,p,p,y,y), C002 (21/29), C003 (m1 pinglamb 5-0), C004 (m4 pinglamb 5-0), R007 (quads
248/191), R008 (TSD+TST 221/284), C010 (spike 15/17), C011 (240.1s @ m3r3), **R010 (fast games
yachi 5 / pinglamb 11 — confirms MAJOR-1)**, C014/C017 (m7 5-4 yachi), C018 (m2r3 pinglamb 18
tspins), R024 (holds 1792/1703).

---

## Verdict
**FINDINGS: 0 blocker, 1 major, 0 minor.** Fix MAJOR-1 (swap 敗/勝 in the one yachi fast-game
overview sentence) and the artifact is publishable; the verification chain, coverage, rendering,
and register are otherwise clean.

## Round 2 — MAJOR-1 fix verification & convergence

Scope: confirm the fast-game record fix; sweep the edited line; confirm nothing else changed.

**FINDINGS: 0 blocker, 0 major, 0 minor — CONVERGED.**

- **MAJOR-1 fixed, exactly as specified.** The buggy string 「yachi 5 敗 11 勝」 now appears **0**
  times; 「yachi 5 勝 11 敗（對 pinglamb 反轉）」 appears **exactly once**. The R010 badge is still
  adjacent to the sentence. The three statements of the figure now all agree with each other and
  with the R010 ground truth (ledger/island: 「pinglamb 贏 11 局，yachi 得 5 局」):
  - yachi overview: 「快局崩盤…yachi **5 勝 11 敗**（對 pinglamb 反轉）」〔R010〕 ✓ (collapse framing now
    consistent — yachi loses 11 fast games)
  - yachi recommendation #1: 「40 秒內嘅局 **5 勝 11 敗**」 ✓
  - pinglamb overview: 「40 秒內快局 **11 勝 5 敗**」 ✓
- **Edited line clean.** The swapped characters are traditional 勝/敗 (no simplified 胜 introduced);
  0 simplified glyphs and 0 Mandarin markers in the edit region and across all visible text.
- **Nothing else changed.** The edit was prose-only in report.html, so all **52 python_checks
  still evaluate True** (ledger/facts untouched). Badge inventory is identical to round 1 (87 span
  instances, 40 unique, **52** total referenced), and the appendix, chart data, and proof chain are
  unaffected by a two-character text swap.

**Verdict: converged — 0 findings. Ship it.**

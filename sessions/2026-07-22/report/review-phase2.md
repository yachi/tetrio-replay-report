# Phase-2 Convergence Review — claims ledgers + Cantonese writeups

Scope: `claims-narrative.json` (C0xx), `claims-coaching.json` (R0xx), `narrative-beats.md`, `recommendations.md`, checked adversarially against `facts.json` with python probes. Both ledgers currently pass `check_claims.py` (23/23 and 27/27) — every finding below is about *what the passing checks fail to pin* or *what the prose says beyond the check*.

---

## BLOCKER

### B1 — C021 「連贏五局…全場最長嘅連勝」 is a cross-match artifact and partly bridges a LOST match
`narrative-beats.md` lines 37, 65 and claim C021 headline yachi as having **twice won 5 rounds in a row**, "全場最長嘅連勝", used as a core momentum beat and in the 一句總結.

Evidence (probe over `facts.json`, rounds in file order):
- **Within any single match, yachi's longest round-win streak is only 4** (m1 rounds idx3–6 = `yyyy`). pinglamb's within-match max is 3.
- The "5" only exists by **concatenating rounds across a match boundary**. First streak = m1 idx3,4,5,6 (`yyyy`) + **m2 idx0** (`y`). But **m2 was won by pinglamb 4-5** — the 5th "win" is the opening round of a match yachi *lost*. Framing this as yachi momentum is affirmatively misleading.
- The check hardcodes the two index lists and **never proves the superlative** "全場最長" — it does not assert that no ≥5 streak exists elsewhere nor that pinglamb had none.

Fix: either (a) drop the "5連勝" framing and state the honest within-match max (4, m1 idx3–6), or (b) explicitly reword to "跨場連贏五局(單場最多四局)" AND add a check that (i) computes the global concat max streak = 5 for yachi / 3 for pinglamb so the superlative is pinned, and (ii) discloses that the first streak's 5th round opens m2 which yachi lost. The second streak (m5 idx6,7 + m6 idx0,1,2) is both-yachi-wins so is defensible once disclosed as cross-match.

---

## MAJOR

### M1 — R006 「總攻擊速度净係叻 yachi 少少」 contradicts the real total-attack metric
The canto says pinglamb has marginally higher **total attack** ("總攻擊速度"). The check only compares the **sum of per-round `apm_x1000`** (each round weighted equally regardless of length): pinglamb 4,127,267 vs yachi 4,115,629 (diff 11,638, <20000 ✓). But that is a sum of *rates*, not total attack. The genuine total attack sent (`garbage_attack`) is **yachi 4501 > pinglamb 4473** — yachi sent *more* total attack, because he placed far more pieces (7546 vs 6971). So the word 總 (total) points the reader in the wrong direction, and it sits awkwardly next to R007 which (correctly) says pinglamb only wins on *per-piece* attack.
Fix: reword R006 to be strictly about per-round APM (e.g. 「逐局 APM 打成平手,pinglamb 嘅逐局平均高少少」) and delete 「總攻擊速度」; or, if a "total attack" line is wanted, base it on `garbage_attack` (yachi higher) with its own claim.

### M2 — Untagged countable numbers in `narrative-beats.md` (violates guide rule 5)
Every countable statement must carry a claim id; these do not:
- L29 (m3): 「第6局佢 vs 爆到約203」 — verified m3 idx5 yachi vs=203902 (also m3-round max), but no claim id.
- L33 (m4): 「一度打成 3-3(yachi 先贏三局、pinglamb 追返三局)」 and 「5-3」 — verified winners `yyypppyy`, but untagged.
- L37 (m5) 「5-3」, L45 (m7) 「3-5」, L49 (m8) 「5-3」, L51 (m9) 「5-2」 — per-match final scores, all untagged (verified: m5 5-3, m7 3-5, m8 5-3, m9 2-5).
- L63: 「yachi 佔咗大多數」 of the 8 comeback rounds — verified yachi 6 / pinglamb 2, but the "大多數" split is not pinned by C016 (which only asserts the total ==8).
Fix: add claims for each per-match score used in prose (and for the m3 vs≈203, m4 3-3 sequence, and the 6/8 comeback split), or remove the numbers. Cheapest: one claim per match final score.

### M3 — R026 / R027 use `statistics.pstdev` (float sqrt) — not Dafny-translatable as written
Both checks compare population std-devs of per-round series. Dafny with integer arithmetic can't do sqrt/float. Since both series have the same n=79, `pstdev_a < pstdev_b` ⟺ `n·Σx² − (Σx)² ` comparison (exact integers). Verified equivalence:
- PPS: yachi `n*Σx²−(Σx)²` = 144,391,380 < pinglamb 156,606,704 → R026 holds.
- APM: yachi 1,784,418,329,518 > pinglamb 1,384,786,301,868 → pinglamb steadier → R027 holds.
Fix (drop-in, keeps meaning, integer-only), with `Y=[...yachi...]`, `P=[...pinglamb...]` per-round lists:
`R026: 79*sum(x*x for x in Y) - sum(Y)**2 < 79*sum(x*x for x in P) - sum(P)**2` (Y=yachi pps_x1000, P=pinglamb pps_x1000)
`R027: 79*sum(x*x for x in P) - sum(P)**2 < 79*sum(x*x for x in Y) - sum(Y)**2` (using apm_x1000).

---

## MINOR

### m1 — C013 vs R024: the 16-spike record is a tie, but only the coaching side says so, and R024 is unused
C013 (narrative) presents the session-max single spike (16) as yachi's signature (m4 idx2, won). Probe shows **16 was reached three times**: yachi m4 idx2 (won), yachi m3 idx1 (LOST), pinglamb m2 idx4 (LOST). R024 correctly says "both peaked at 16" — but **R024 is never referenced in `recommendations.md`** (only unused ledger claim). A narrative-only reader is left thinking 16 is uniquely yachi's. Fix: soften C013 (「session 最大單發 spike 16,兩邊都試過,yachi 呢一嘢仲贏埋局」) and actually cite R024 in the coaching text.

### m2 — C006 「差唔多3分半鐘」 undershoots
228310 ms = 228.3 s = **3 min 48 s** ≈ "差唔多四分鐘", not 3分半 (3:30). The x1000-second value is pinned; only the parenthetical minutes gloss is loose. Reword to 差唔多四分鐘 / 三分四十八秒.

### m3 — C009 「15秒閃電殺」 unpinned and rounds the wrong way
m7 idx1 max lifetime = 15730 ms = **15.7 s** (~16 s), and the check does NOT pin lifetime at all. Same "15秒" wording is reused for m6 idx1 (15.05 s, *is* pinned via C008). Fix: say 約16秒 and add a lifetime bound to C009's check (e.g. `15000<=max(...)<16000`).

### m4 — R015 「四成半」 understates the value the check itself enforces
Actual finesse-fault-rate ratio pinglamb/yachi = 0.2146/0.1462 = **+46.8%**; the check bounds it 46–48%. 「四成半」 = 45%. Reword to 「成四成七」 / 「近五成」 so prose matches the 46–48% the check proves.

### m5 — 「成體」 typo ×2 in `recommendations.md` (lines 13, 21) — should be 整體 (matches R011's canto which uses 整體).

### m6 — Rounded numbers without 約 (guide rule 2): C005 「APM 74 對 43」 are floors of 74.1 / 43.x; add 約 or bound-note. Low priority.

### m7 — `SCHEMA.md` internal contradiction on `lifetime` unit: line 20 says MILLISECONDS (correct — 228310 ms = 228 s is sane; as frames it'd be ~63 min), line 44 struct comment says "(frames)". The narrative author already flagged this (narrative-beats.md L3). Fix the struct comment to `// player.lifetime (milliseconds)`.

---

## Positives (no action)
- Cantonese register is clean: scanned both .md and both ledgers for 的/了/是/在/他/們/和/沒/這/那/很 — **zero** non-quotative Mandarin markers.
- Garbage semantics are disciplined: C007/C016/R019 correctly split queued attack (`garbage_events`, 「射埋嚟」) from materialized (`garbagereceived`, 「真係食咗」). R019's ~15% cancel figure checks out (q=3667, r=3127, 540/3667=14.7%).
- No duplicate ids; no md→ledger dangling references; C-ledger fully used. Only R024 is unused (see m1).
- C015 (all 79 rounds winner-has-higher-vs) is a genuine universal, not vacuous.

---

FINDINGS: 1 blocker, 4 major, 7 minor

---

## Round 2

Re-verified every round-1 finding against the updated files (both ledgers pass 27/27) with fresh probes, and swept the new/changed claims (C021, C024–C027) and reworded coaching claims (R006, R015, R024, R026, R027).

### Round-1 findings — all resolved (verified, not just claimed)
- **B1 (C021)** RESOLVED. New check pins the superlative directly: concat max round-win streak yachi=5 / pinglamb=3, within-match yachi max=4, and `matches[1].winner=='pinglamb'`. Independent probe confirms exactly two yachi runs ≥5, starting at m1r3 and m5r6 — no hidden third streak. New canto honestly discloses (a) it's a cross-match streak, (b) within-match max is only 4, (c) the m1→m2 streak's 5th round opens a match yachi lost 4-5. The narrative body no longer frames the m1→m2 run as momentum.
- **M1 (R006)** RESOLVED. Wording dropped 「總攻擊速度」; now 「逐局 APM 打成平手,pinglamb 每局平均 APM 净係叻少少」, which matches the sum-of-per-round-APM check (diff 11638 over 79 rounds, i.e. ~0.15 APM/round). No longer contradicts the true total (garbage_attack).
- **M2 (untagged narrative numbers)** RESOLVED. Added C024 (m3 yachi vs≈203.9, pinned as m3 all-player max = 203902), C025 (m4 winners + 5-3), C026 (all 10 final scores, exact), C027 (comeback split 6/2). Every per-match title and the L29/L63 numbers now carry ids.
- **M3 (R026/R027 Dafny)** RESOLVED. Both restated integer-only as `79*Σx² − (Σx)²` comparisons; directions confirmed (PPS 144,391,380<156,606,704 → yachi steadier; APM pinglamb 1.385e12<yachi 1.784e12 → pinglamb steadier).
- **Minors** all resolved: C013 now says the 16-spike was reached 3× by both sides (check adds `count(==16)==3`), and R024 is now cited in recommendations rec-2; C006 → 「三分四十八秒,差唔多四分鐘」; C009 → 「約16秒」 with lifetime bound `15000<=…<16000`; R015 → 「接近五成」 (actual +46.8%, check 46–48%); 「成體」→「整體」 (gone); C005 → 「約74 對約43」; SCHEMA.md line 43 comment now reads MILLISECONDS.

### Fresh sweep on new/changed items — no new issues
- C024: check proves yachi's 203902 is the max vs across BOTH players in m3 (pinglamb m3 max only 150083), which is ≥ the prose's weaker 「佢嗰場單局最高」 — honest, not vacuous.
- C026/C027 are exact-tuple / exact-count checks; C027's 6+2 is disjoint by construction and reconciles with C016's 8.
- Register clean: zero Mandarin markers across all four files. No duplicate ids; no dangling md refs; no unused ledger claims (R024 now used).

FINDINGS (Round 2): 0 blocker, 0 major, 0 minor — CONVERGED.

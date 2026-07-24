# Plan: TETR.IO 激烈戰況 Cantonese HTML Report — with Dafny-Proven Claims

## 0. Ground truth (already verified in main thread)

- 10 × `.ttrm` multiplayer replays (JSON), **yachi vs pinglamb**, 2026-07-22 17:21–19:04, all FT5.
- Match score **yachi 6 : 4 pinglamb**; round score **43 : 36**. Three matches went to 5-4 deciders → genuinely 激烈.
- Per-round data available without engine simulation:
  - `leaderboard[].stats`: apm, pps, vsscore, garbagesent/received, kills, btb
  - `rounds[i][p].stats` + `replay.results.stats`: lines, pieces, holds, clears breakdown (quads, T-spin singles/doubles/triples, all-clears), `garbage.maxspike`, `garbage.attack/cleared`, finesse (faults, perfectpieces, combo), topcombo, topbtb
  - `replay.events`: keydown/keyup (input rate, per-piece timing), `ige` interactions = frame-stamped incoming garbage (amt, frame) → momentum-swing / clutch analysis
  - `lifetime` per round → round length; `alive` → winner per round
- Environment: `dafny 4.11.0` at `/opt/homebrew/bin/dafny`, python3 available.
- **Scope guard**: no full board reconstruction (would need a tetris engine). All claims must be derivable from stats/results/ige/event-timing fields. Claims needing board state (e.g. "survived a 18-high board") are OUT of scope.

## 1. Architecture: the trust chain

```
.ttrm files ──(A: extractor #1, python)──► facts.json
           └─(B: extractor #2, independent impl)──► facts2.json ── diff == ∅ gate
facts.json ──(codegen)──► Facts.dfy (data as const literals)
claims ledger (claims.json) ──(codegen)──► Claims.dfy (1 lemma per claim)
`dafny verify` PASS  +  mutation test (flip a constant → MUST fail)
HTML report: every factual sentence carries a claim-ID badge ↔ verified lemma
auditor agent: extract claims from HTML → bijection check vs verified lemmas → loop to 0
```

Honest framing baked into the report footer: Dafny proves **claims ⇔ extracted data**; extraction correctness is established by two independent parsers agreeing + spot checks, not by Dafny.

### Claim ledger schema (`claims.json`)
```json
{ "id": "C012",
  "canto": "yachi 十場入面贏咗六場",
  "predicate": "CountMatchWins(matches, YACHI) == 6",
  "kind": "exact-count | threshold | comparison | ratio",
  "scale": "integers only; rates scaled ×1000 (APM 51.8 → 51800/1000) — no Dafny reals" }
```
Rules: every number, comparison, or superlative in the HTML must have an id. Subjective color commentary (「打到火花四濺」) needs no proof but must not smuggle in numbers.

## 2. Phases & agent assignments

### Phase 1 — Extraction (2 agents, parallel)
- **Agent E1 (sonnet)**: write `extract.py` → `facts.json`. Per match: score, winner, per round: winner, lifetime, per player: apm/pps/vs (×1000 int), sent/recv, clears breakdown, maxspike, topcombo/topbtb, finesse, tspin total; plus derived: comeback rounds (won after trailing in garbage interactions), longest/shortest round, biggest spike, decider-round record.
- **Agent E2 (sonnet)**: independent extractor `extract2.ts` (bun) — same output schema, written WITHOUT seeing E1's code (prompt contains schema only).
- **Gate (main thread)**: `diff <(jq -S . facts.json) <(jq -S . facts2.json)` must be empty. Any mismatch → root-cause before proceeding.

### Phase 2 — Analysis & claims (2 opus agents, parallel, then converge)
- **Agent A1 (opus) — 戰況 narrative**: match-by-match drama arc from facts.json: deciders, comebacks, spikes, momentum swings (ige timing), kill rounds. Output: claims.json entries + Cantonese narrative beats.
- **Agent A2 (opus) — coaching**: per-player diagnosis: yachi (faster PPS 1.44 vs 1.34, fewer garbage sent 3543 vs 3667 — efficiency vs pressure tradeoff), pinglamb (higher attack per piece?), finesse faults, hold usage, T-spin vs quad mix, deciding-round performance (choke analysis). Output: ≥3 recommendations per player, EACH tied to claim IDs.
- **Convergence reviewer (opus)**: checks contradictions between A1/A2, unprovable claims, missing angles. Loop until 0 new findings (expect 2 rounds).

### Phase 3 — Dafny proof layer (1 opus agent)
- **Agent D (opus)**: write `codegen_dafny.py` that emits:
  - `Facts.dfy`: datatypes `Match`, `Round`, `PlayerStats`; all data as `const` literals generated from facts.json.
  - `Claims.dfy`: pure functions (CountMatchWins, TotalSent, AvgScaled, MaxSpike…) + one `lemma C012_...()` per ledger entry with `ensures` matching the predicate.
  - Integer-only arithmetic; averages proven as `sum * 1000 / n` with explicit rounding claim wording.
- **Gates (main thread)**: `dafny verify` exit 0; **mutation test**: script flips one literal per claim class → verify MUST fail (proves lemmas aren't vacuous); re-flip back, verify green.

### Phase 4 — HTML report (1 sonnet agent, frontend-design + dataviz skills)
- **Agent H (sonnet)**: single self-contained `report.html`, 廣東話口語 (sports-commentary register: 「第七局yachi一嘢12行spike直接打穿pinglamb」), sections:
  1. 總覽 scoreboard (6:4 / 43:36) 2. 逐場戰況 timeline 3. 數據對決 (APM/PPS/VS charts, inline SVG) 4. 關鍵時刻 (spikes, deciders, comebacks) 5. 俾yachi嘅建議 / 俾pinglamb嘅建議 6. 證明附錄: claims table (id, 廣東話 claim, lemma name, ✓ verified) + methodology note.
  - Every factual sentence gets a superscript badge `[C012 ✓]` linking to the appendix row.
  - No external resources; light/dark theme aware.

### Phase 5 — Adversarial audit loop (1 opus agent + main thread)
- **Agent V (opus)**: parse report.html, extract EVERY factual claim → verify: (a) has claim ID, (b) lemma exists and verified, (c) Cantonese wording matches the predicate semantics (e.g. 「平均」 vs proven scaled-sum), (d) Cantonese is natural 口語 not 書面語.
- Loop Phase 4↔5 until V reports 0 findings for one full round (≥2 rounds mandatory).
- **Main thread final**: rerun `dafny verify`, rerun both extractors, open report in browser (Playwright headed) for visual check, then deliver.

## 3. Agent ops rules (from global CLAUDE.md)
- All agents: `bypassPermissions`, "DO NOT commit", opus for analysis/proofs/audit, sonnet for mechanical build.
- Main thread only orchestrates + runs gates; validates every agent's numeric output against facts.json itself (agents fabricate — trust the gates, not the prose).
- Working dir for outputs: `./report/` (facts.json, claims.json, *.dfy, report.html, mutation_test.sh).

## 4. Risks
- Dafny reals/float: avoided by ×1000 integer scaling — wording in report must say 「約」 for rounded averages, and the proven predicate is the exact scaled integer.
- 65k-line JSON: extractors must stream/`json.load` whole-file (fine, ≤1.5MB each).
- Cantonese quality: sonnet drafts, opus auditor checks register; flag 書面語 as a finding.
- ige `interaction` vs `interaction_confirm` double-count: extractor must count only `interaction_confirm` (confirmed garbage) — verify totals ≈ leaderboard garbagereceived as a cross-check gate.

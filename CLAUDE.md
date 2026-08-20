# tetrio-replay-report — operating context

Public repo: <https://github.com/yachi/tetrio-replay-report> · Site: <https://yachi.github.io/tetrio-replay-report/>

Turns a batch of TETR.IO `.ttrm` replays into a Cantonese match report where every
factual sentence is badge-linked to a Dafny-verified lemma. Seven sessions so far
(2026-07-22: yachi 6:4 · 2026-07-24: pinglamb 4:3 · 2026-07-28: pinglamb 6:2 ·
2026-08-01: yachi 4:3 · 2026-08-09: pinglamb 6:0 · 2026-08-14: pinglamb 7:4 ·
2026-08-19: pinglamb 7:3), 450 rounds, 614 generated claims plus the hand ledgers —
count those from `sessions/*/report/claims-narrative.json` and `claims-coaching.json`
rather than from a total typed here, because hand prose lands after the session does.
2026-08-14 is the largest session by both matches (11) and rounds (84). 2026-08-19 is
third by rounds (70, behind 07-22's 79) and **ties** 07-22 at 10 matches rather than
sitting second alone.

## The one invariant

**Dafny proves "claim ⇔ extracted data", not the extraction.** That the dataset matches
the `.ttrm` files rests on two independently written extractors agreeing byte-for-byte.
Never let a report, README, or commit message blur those two things — every audit round
in this project's history caught someone doing exactly that.

Corollaries that are gates, not preferences:
- a proof-map status may only come from real `dafny verify` output, never stamped by codegen
- a proof-map entry must name a lemma that still exists. `codegen` builds lemma *names* from
  each claim's `english_gloss`, so editing a gloss renames the lemma and strands the badge's
  link while the verifier still reports 0 errors and the status gate still counts 54/54.
  `pipeline/check_proof_links.py` is the gate; rebuild a stranded map with the session's
  `build_proof_map.py` (the committed hand layout) or `pipeline.build_proof_map` (generated)
- a lemma that no mutation can kill is decorative; `mutation_test.sh` must kill every mutant
- every countable statement in a report needs a claim id whose predicate covers *that*
  number — not a weaker one nearby
- a **rate** record (APM, VS) is only over rounds of `generators.QUALIFYING_MS` or more;
  **count** records (lines, spike, combo, B2B, T-spin) are over every round. See
  「速率紀錄要有局長下限」 below — the rule is measured, not a preference

## Relevant skills / tools

R 4.6.1 with `jsonlite` is installed; `analysis/rate_records.R` is the worked example of
using it against `sessions/*/report/facts.json`. Reach for it before changing a metric's
definition — the qualifier below came out of it and the argument for the threshold is a
regression, not an opinion.

## Commands

```bash
bin/new-session sessions/<date> <replay-dir>   # extract → claims → Dafny → verify → proof map
bin/verify-session sessions/<date>/report      # re-run all gates (MUTATION=1 adds mutation test)
bin/build-docs                                 # regenerate docs/ (the Pages site) from sessions
python3 -m pipeline.build_report sessions/<date>/report         # regenerate the derived report sections
python3 -m pipeline.build_report sessions/<date>/report --check # CI gate: fail if they drifted from facts.json
python3 -m pipeline.check_prose_figures sessions/<date>/report   # CI gate: every 約-figure is floored
python3 -m pipeline.check_proof_links sessions/<date>/report      # CI gate: every badge's lemma exists
python3 -m pipeline.check_generated_css sessions/<date>/report    # CI gate: generated CSS stays in its region
python3 -m pipeline.build_round_table sessions/<date>/report   # regenerate the 逐局全數據 section
python3 -m pipeline.claims.build_claims <facts> --out <ledger> # generated ledger
python3 -m pipeline.codegen <facts> --claims <ledger> --outdir <dir>
python3 -m pipeline.claims.equiv <facts> --hand <ledgers...>   # coverage by exhaustive mutation
python3 -m pipeline.codegen_smt <facts> --claims <ledger> --out <dir>/claims.smt2
python3 -m pipeline.check_smt sessions/<date>/report --regen --mutate 12
python3 -m pipeline.check_dead_consts sessions/<date>/report
python3 -m pipeline.check_rate_coverage sessions/<date>/report  # CI gate: short rounds' rates still pinned
python3 -m pipeline.check_badge_links sessions/<date>/report    # CI gate: every badge citation resolves
python3 -m pipeline.check_report_shell sessions/<date>/report   # CI gate: no hand-written <section> in the body
python3 -m pipeline.check_cross_artefact             # CI gate: two artefacts of ONE session agree
python3 -m pipeline.check_cross_artefact --selftest  #   its mutants (8 planted, 4 controls)
python3 -m pipeline.check_finesse_denominator sessions/<date>/report  # CI gate: every per-piece rate names 每粒
python3 -m pipeline.check_finesse_denominator sessions/<date>/report --selftest  # its mutants
python3 -m pipeline.check_opener_section sessions/<date>/report  # CI gate: the C-Spin / DT 砲 section
python3 -m pipeline.check_opener_section sessions/<date>/report --selftest
python3 -m pipeline.openers.extract_wiki_openers            # CI gate: harddrop's own opener drawings
python3 -m pipeline.openers.extract_wiki_openers --selftest # its mutants
python3 -m pipeline.openers.extract_wiki_techniques            # CI gate: the Donation / STMB Cave
python3 -m pipeline.openers.extract_wiki_techniques --selftest #   drawings and their controls
python3 -m pipeline.openers.extract_wiki_openers \
  --html-dir <dir> --write                                 # re-transcribe (needs the pages fetched)
REPLAY_DIR=sessions/<date> bun pipeline/sim/emit-opener-facts.ts \
  --out sessions/<date>/sim/opener-facts.json                   # the C-Spin / DT Cannon metrics
Rscript analysis/rate_records.R                                 # the evidence for QUALIFYING_MS
dafny verify spec/Forecast.dfy spec/ForecastExamples.dfy       # the hand-written concept spec
dafny verify spec/BfsKey.dfy               # why bestTspin's visited key carries the arrival mode
bash spec/mutate-bfskey.sh                 # its mutants — a lemma none can kill is decorative
bash spec/mutate-forecast-spec.sh          # spec mutants — a TIMEOUT is UNRESOLVED, not killed
dafny verify spec/DonationCave.dfy         # why the naive Donation clause and the cave's roof test
bash spec/mutate-donationcave.sh           #   discriminate nothing; 10 mutants, all killed
python3 spec/check_spec_vacuity.py         # no lemma in the spec is vacuously true — controls are
python3 spec/check_spec_vacuity.py spec/DonationCave.dfy   # per-module, so run it once per file
python3 -m pipeline.forecast_examples      # the drawn boards (example-boards.ts) agree with the
                                           #   proven witnesses (ForecastExamples.dfy); --write regens
                                           #   spec/forecast-examples.json, --selftest proves teeth
python3 -m pipeline.sim.extract_jp_forecast # re-extract the 38 Tetrisちゃんねる forecast diagrams from
                                           #   their JPEGs (needs Pillow); --write regens the JSON.
                                           #   CI gate is bun test pipeline/sim/jp-forecast.test.ts
python3 -m pipeline.sim.extract_four_forecast # re-decode four.lol's 26 forecast frames from the
                                           #   committed fumen codes (needs py_fumen); CI gate is
                                           #   bun test pipeline/sim/four-forecast.test.ts
```

## Three backends, one spec

`pipeline/claims/spec.py` renders each claim to a **Python** predicate, a **Dafny**
`ensures`, and **SMT-LIB 2.6** (`pipeline/claims/smt.py`). One spec, three targets, so what
Python evaluates, what Dafny proves and what a solver refutes cannot drift apart — the
dual-extractor argument applied to the proof side.

Why SMT-LIB exists alongside Dafny: **every generated lemma has an empty body** and uses no
quantifiers, functions or loops, so the obligation is ground integer arithmetic that Dafny
hands to Boogie which hands it to Z3. Going straight to SMT-LIB skips two layers and is about
two orders of magnitude faster — measured, over the same claims:

| | Dafny (`--cores 4`) | `claims.smt2` + z3 |
|---|---|---|
| 2026-07-22 · 144 claims | ~8.3 s (the 54 committed hand lemmas) | **100 ms** |
| 2026-07-24 · 141 claims | ~3.8 s (the 52 committed hand lemmas) | **60 ms** |

That speed is what makes the anti-vacuity mutation test affordable on every push
(`--mutate 12` finishes in under a second) rather than weekly. `claims.smt2` is committed and
byte-identity gated, so it doubles as a portable artefact: any SMT-LIB solver can re-check the
claims without this pipeline.

**The `.smt2` covers every ledger of every session — there is no longer a second kind.** Hand
claims are written as **specs** in `sessions/<date>/report/hand_claims*.py` and built with
`pipeline.claims.build_hand`, so they render to all three backends and need no per-session
emitter: `--claims` on `codegen`, `codegen_smt` and `build_proof_map` takes several ledgers,
and `pipeline.codegen.session_ledgers` defines their canonical order. A session may hold more
than one hand ledger (07-22 and 07-24 split theirs narrative/coaching); the module→ledger
mapping is `build_hand.hand_ledgers`, which **raises on a ledger no module rebuilds** rather
than skipping it, because a skip is what leaves a ledger with nothing checking it.

Two windowed operators exist for claims about how a session *changed*:
`sum_round_range` / `count_rounds_range` restrict to a contiguous window of matches. The
window is part of the claim's identity (like `sum_ge`'s explicit mi/ri), so it is rendered by
emitting only the in-window terms — never `if <window> then x else 0`, whose folded-away
`if false` would leave a const referenced in the text but unread by the proof, i.e. a mutation
that can never be killed. Windows of different sizes must be compared as cross-multiplied
rates, never as raw sums.

**Encoding, and why it is what it is.** Strings are integer codes with a legend in the header
(`1 = yachi`), not the `String` sort — the sort restricted the file to the two solvers with a
string theory, which defeats emitting a standard format. The logic is `QF_NIA`, not `QF_LIA`:
the integer variance identity squares a datum, and `QF_LIA` rejects `(* v v)` outright. Both
facts were found by a solver refusing the file, not by reading a spec.

**Mutating the SMT artefact needs an operator per kind of datum.** `check_smt --mutate`
perturbs a *stratified* sample (every kind of datum, not a uniform draw) because both bugs this
gate has had were confined to a kind:

| Kind | Operator | Why the obvious one fails |
|---|---|---|
| categorical code (`_winner`, `_gameoverreason`) | try the **other codes** | claims count members of a category; `5 → 6` changes no count, `5 → 3` does |
| measurement | escalate **both ways** (+1, −1, +1000, −1000, far up, 0) | many claims are one-sided — "yachi's KPP is lower than pinglamb's" survives *any* increase to pinglamb |

Coded-ness is read from the constant's **name** (the emitter marks them with a trailing
`; label`), never from its value — detecting by value quietly reclassified a `topcombo` of 4 as
"the code for topout" and reported six real measurements as survivors.

**Two solvers, and they agree.** z3 4.16.0 and cvc5 1.3.4 both answer `unsat` on all 153
generated claims (77 + 76). `check_smt` runs every solver on PATH and names the ones it did not
find, so a single-solver run is stated rather than implied. Each solver needs different argv —
z3 reads stdin only with `-in`, cvc5 needs `--incremental` before it honours the file's
`push`/`pop` — so `SOLVERS` maps a name to its flags and the file is passed as a path.

Installing cvc5: the documented way is the project's **own Homebrew tap, as a cask**, which is
why `brew install cvc5` and `brew search --formula cvc5` both come up empty:

```fish
brew install --cask cvc5/cvc5/cvc5
```

The PyPI `cvc5` package is Python bindings only — no CLI. yices2 installs from core
(`brew install yices2`) but its nonlinear support is limited, so it may refuse the variance
claims.

CI pins cvc5 by sha256 (`CVC5_SHA256` in the workflow), and that hash has **two independent
authorities that agree**: cvc5's own Homebrew cask and GitHub's asset digest — verified against
the downloaded bytes before use.

**Both solvers run in CI, on different artefacts, and the difference between them is the PIN, not
the presence.** The `verify` job installs z3 4.14.1 (`Z3_VERSION` / `Z3_SHA256`) because
verify-session step 7's lemma-vacuity gate needs a solver and fails rather than skips without one —
and it must be z3: cvc5 produced no result in 120 s on 2026-07-24's 78 claims where z3 settles them
in 2.6 s, so the two are not interchangeable for those free-variable queries. 4.14.1 is the newest
release still shipping an `x64-glibc-2.35` build, which is what the `ubuntu-22.04` runner has. What
that pin lacks is a second authority: GitHub publishes no asset `digest` for **any** z3 build
against glibc-2.35, and the release carries no signature, checksum or SBOM, so the hash is
trust-on-first-use — it defends against the asset changing from here on, not against it having been
wrong when first fetched. The `pipeline` job installs cvc5 for `check_smt` over the committed
`claims.smt2`. So "z3 locally, cvc5 in CI" is true of the **.smt2** artefact only, which is where
that sentence came from; as a statement about the workflow it is false.

Every generator replaces only the region between its HTML comment markers, so all of them are
idempotent and safe to re-run over a hand-edited report. `pipeline/region.py` owns that
mechanism (`markers()` / `replace()`); `build_round_table.py` predates it and carries its own
equivalent marker pair.

## Workflow

- **I commit; the user pushes.** `git push` and remote changes are blocked for the agent.
  Stage, commit with a Conventional Commit message, then tell the user to push.
- CI (6 jobs) re-runs every gate on push, including regenerating each ledger and checking it
  is byte-identical to what is committed. Weekly runs add mutation testing.
- Report prose is Hong Kong colloquial Cantonese, traditional characters. `build_claims.py`
  asserts no simplified glyphs; reviews have repeatedly caught 净/实/约 slipping in.
- **Closing a ROADMAP item means striking it AT ITS ORIGINAL SITE, not only writing a new dated
  section.** An audit on 2026-08-16 found **six** items filed as open that were already done in
  committed code — 最癲一局 items 4 and 5, Re-classified item 7 (done the same day it was filed
  "not yet actioned"), the `cc-movegen` standing gate, the `## P5 — in progress` header contradicted
  by its own body 266 lines later, and Original TODO item 2 (false for eighteen days) — plus one
  obsolete item arguing about a mechanism that had been deleted. Every one has the same shape: the
  closure landed in a NEW section or in a commit message, and the original entry was never touched.
  A commit message is not documentation; nothing re-derives it. **A DONE record that repeats a wrong
  reason is worth less than none** — item 7's justification for its `<= 3` bound was measurably false
  in both the item text and the commit that closed it.
## 冇第二份 — a number whose only home is this prose

**A figure whose only copy is here has nothing to disagree with it, so it cannot go stale loudly.**
It goes stale silently, stays published, and reads exactly like a measurement until somebody happens
to re-derive it by hand. Every other class of drift in this repo announces itself — a ledger stops
being byte-identical, a lemma stops verifying, a gate goes red. This one has no announcement
mechanism at all, which is what makes it the hardest class the document carries.

Four instances, all live as of 2026-08-19, and they are not the same kind of thing on the surface:

| | what it was | how it failed |
|---|---|---|
| the repertoire ranges | Honey Cup 17-25, MS1 11-25, TKI-3 5-8 | **two of three already false when 08-14 landed**; five days published. `grep` confirms no file in the repo ever contained them |
| the `cavity ≥ 1` band | 74.6-77.0% | nothing recomputes it; it survives only because 08-14 ties 08-09 at one decimal, and it must be re-measured by hand every session |
| the raw-DS AUC series | 68.4 · 62.0 · 81.2 · 83.0 · 64.0 | quoted from a probe; stopped at five sessions and nothing said so |
| the `760` numerators | 183, 257, 245, 201, 650/750 … | correct when written, silently wrong the moment the corpus reached 900 |

**A gate can have the same defect, so "it is checked" is not the test.**
`expect(out).toBe(sum(width_ge_3))` in `openers.test.ts` looked like a gate and was arithmetic
standing in for the empirical claim "no ≥3-wide hit is ever in an opener" — true only while
`in_opener` was 0 everywhere, so it was a tautology of the data it was written against, and it broke
on the day that stopped being true. The question is never "is there a check", it is **"what would
have to change for this number to be recomputed"**.

The corollary, and it is where to look next: **the remaining exposure is concentrated wherever a
figure was quoted from a probe that was never committed.** A probe that ships an artefact leaves
something to diff; a probe run once and discarded leaves a number in prose and no way back to it.
So before writing a figure here, ask what re-derives it — and when the answer is "nothing", either
point at what does (a committed artefact, a test, a generator) or say plainly, in the sentence
itself, that it is hand-measured and must be re-measured. Both of those are done for each of the
four rows below; a bare number is not.

**A count measured against a pinned SET is void the moment that set changes.** The fifth instance
arrived while this section was being written, and it is the one that should worry a reader most.
`forecast-access-class.test.ts` carried 「20 planted, 16 killed, 4 survive」 in its header — a
mutation score measured on 2026-08-16 against an `ACCESS_CLASS` holding two entries. 2026-08-19
added two more, and the score silently became a statement about a file that no longer existed.
**That file already knew.** It carries a paragraph warning against exactly this, and the warning
did not prevent the recurrence, for the reason the whole section is about: *prose cannot fail*.
The header now says which five mutants were re-run and which fifteen were not. The actionable
rule: when a pinned set changes, every count measured against the old set is void until it is
re-run or explicitly scoped to the set it was measured on.

## Data semantics that cost real debugging

- `lifetime` is **milliseconds**, not frames (verify via `pieces / pps`; 60 fps is ~15× off).
- `ige` `interaction_confirm` events are **queued incoming attack**, before cancellation —
  consistently ~10–20% above `garbagereceived`, which is what materialised. The reports say
  射埋 vs 食 and must never conflate them.
- The raw `tspins` counter includes spins that cleared nothing, so it exceeds the sum of the
  T-spin clear types. Always say which measure is meant.
- Kills equal round wins by construction in first-to-death 1v1 — never presented as a second
  independent signal.
- Player order in `users` / `leaderboard` is **not stable across files**; key by username.
- A match's `index` is its **position in the session**, not the export number in the
  filename — the filename stays in `file`. The two agreed by accident until 2026-08-01,
  whose exports are numbered 2-8: claims have always said `m{position}` while the report
  card printed `第 {index} 場`, so a badge proving something about m1 would have sat on a
  card labelled 第 2 場. Both extractors renumber after sorting; every earlier session's
  `facts.json` is byte-identical under the change, which is what makes it safe.
- **A round carries THREE stat objects and both extractors mix two of them.** `player.stats` is a
  live in-game tick; `player.replay.results.stats` is the final snapshot; `player.replay.results.`
  `aggregatestats` = `{apm, pps, vsscore}` is the final *rate* triple and nothing in the repo reads
  it. `apm_x1000`/`pps_x1000`/`vs_x1000` come from the live tick while `garbage_attack` /
  `garbage_cleared` / `finaltime_ms` come from the final snapshot, so a rate and its own counters
  can be one tick apart — the whole of the VS-identity residual. **Every count in the rest of this
  bullet and the next was measured over the 760 player-rounds of the first six sessions and has not
  been re-run at 900; the ratios are what to carry forward, not the numerators.** The live tick is
  stale in 183 of 760 player-rounds and **181 of those are the round's SURVIVOR**: the survivor keeps playing frames after
  the opponent tops out and `player.stats` freezes before those frames fold in, so a per-player skew
  in the residual is a fact about whose round ran longer, never about how someone plays.
  `aggregatestats` reproduces every rate to ≤4.2e-16 over 760 player-rounds as
  `100·(attack+cleared)/T`, `60·attack/T`, `pieces/T` — where **T is the integer FRAME count, and
  `finaltime_ms` does not yield it.** `⌊finaltime_ms·60/1000⌋/60` gives the wrong frame count on
  **257 of the 760** and leaves up to 1.5e-3, because `finaltime_ms` is `results.stats.finaltime`
  rounded to the millisecond (`extract.py`'s `x1`) while the clock ticks every 1/60 s — the rounding
  destroys the frame the flooring is trying to recover. Recover it from `pps` instead:
  `round(60·pieces/pps)` is an integer to 1.8e-12 on all 760, and under **T = round(60·pieces/pps)/60**
  the residual is 2.4e-16 for APM and 4.2e-16 for VS, which is where the ≤4.2e-16 came from. PPS is
  exact by construction on that route, so the **checkable** statement is the T-free identity
  `vs·60·attack == apm·100·(attack+cleared)`: worst relative residual **6.1e-16** over the 758 rounds
  with a nonzero APM and VS. A probe that uses `finaltime_ms/1000` reports a discrepancy the data
  does not have — up to 1.2e-3, and above 1e-4 on 245 of the 760.
- **`kills` runs the OTHER way, so do not "finish the job" by moving the rest of `player.stats`.**
  The 2026-08-16 re-source moved `apm`/`pps`/`vs` off the live tick because the tick predates the end
  of the round. `kills` has the opposite problem: `results.stats.kills` disagrees with
  `player.stats.kills` in **201 of 760** player-rounds, and every one is the live tick reading 1
  against the results snapshot reading 0 for a player who SURVIVED — because the results snapshot is
  taken when that player's own game ends, while the kill is credited later, when the opponent tops
  out. For `kills` the live tick is the correct source and the final snapshot is the stale one.
  `aggregatestats` carries only `apm`/`pps`/`vsscore`, so the re-source is complete as scoped rather
  than truncated; `garbagesent`/`garbagereceived` differ from their `results.stats` counterparts in 7
  and 1 of 760 and are a different measure anyway (both sides are already extracted, as
  `garbage_sent_raw` / `garbage_received_raw`). Moving any of these for consistency would introduce
  the bug the rate change removed.
- **The finesse counters are on two different units, so any finesse rate must name its denominator.**
  `perfectpieces` counts **pieces**; `faults` counts **fault events**, and one piece can register
  several — pooled, 11 865 faults over 7 510 non-perfect pieces = **1.580 per faulty piece**. Four
  defensible rates, four different numbers, and only one is what TETR.IO displays:
  `faults/pieces` = **16.83%** is fault events per piece; the share of pieces that were faulty is
  `1 − perfect/pieces` = **10.65%**; TETR.IO's own figure is `perfect/pieces` = **89.35%**; and
  `faults/(faults+perfect)` = **15.85%** is on no meaningful denominator and must not be used. A
  bare「失誤率」 reads as the 10.65% and is usually the 16.83%. osk publishes no definition for any
  of the three fields, so the per-excess-input granularity is inferred, not specified. (Pooled over
  the first six sessions; not re-run at 900 player-rounds. The four rates are definitions, so they
  keep their meaning at any n — the four *numbers* are a six-session measurement.)

  **All six reports then in the corpus shipped the bare label, and
  `pipeline/check_finesse_denominator.py` is now the
  gate.** The tape chart plotted `faults/pieces` as 「finesse 失誤率」 formatted `(v*100).toFixed(1)+"%"`
  — 16.8% under a label that reads as 10.65%. The row is 「每粒 finesse 失誤」 rendered `toFixed(3)`
  now, matching 每粒攻擊 beside it, because **a percentage rendering asserts a share** and a label
  alone does not undo one: 16.8% reads as a share however the row is titled. `hold 使用率` keeps its
  percentage — a hold IS at most one per piece, which is what the gate's `SHARE` kind records. The
  data refutes the share reading outright: in **650 of 750** player-rounds the faults outnumber the
  non-perfect pieces, and 07-24 m2r0 puts **7 faults on a single non-perfect piece**.

  Two things this cost that are worth keeping. **The defect lived where no gate looked** — the chart's
  renderer is in each session's committed shell, outside every marker region, so `build_report --check`
  never saw it and fixing `skeleton.py` alone would have shipped to no existing report; all six
  `report.html` had to be patched directly. So this gate reads the WHOLE document, generated regions
  included, unlike `check_prose_figures`. And **every accessor the chart plots must be classified**
  COUNT/SHARE/EVENT_RATE — an unclassified key fails, so a new row forces the decision instead of
  leaving it to whoever writes the label.

## What the data actually says (measured, not asserted)

Paired AUC over 129 rounds — how often the round's winner held the higher value. **This block is
07-22 and 07-24 pooled**, and its buckets are therefore two-session buckets; the numbers were
always labelled with their n, but the bucket NAMES read as corpus verdicts and two of them are
false at 450 rounds. See the pooled correction below the per-session paragraphs.

- **Strong**: VS 100% · APM 93.8 · 攻 93.8 · APP 91.5 · 送 88.0 · 射埋 12.0 (88 inverted) ·
  食 14.3 · 分 85.3
- **Filed here as "no signal" on two sessions**: COMBO 45.0 · PC 50.8 (89% zeros) · TST 55.8 ·
  TSD 60.9 · KPP 39.9 — COMBO and TST do not survive to 450 rounds as no-signal; PC does
- Near-constant (CV 0.05): KPP, FIN% — their flatness is the finding, not a column of numbers

2026-07-28 (64 rounds) reproduces all of it independently: VS 100% · APP 96.9 · APM 95.3 ·
攻 93.8 · DS 75.0 · 食 12.5 · 射埋 14.1 — and **KPP 42.2**, below chance for a third time.

2026-08-01 (53 rounds) is the fourth independent reproduction: VS 100% · 攻 90.6 · APM 90.6 ·
APP 83.0 · 食 15.1 · 射埋 19.8 — **DS 84.0, the highest of any session** (66.5 · 60.0 · 75.0 · 84.0
across the four) — and **KPP 53.8**, i.e. chance, for a fourth time.

2026-08-09 (50 rounds) is the fifth: VS 100% · 攻 94.0 · APM 94.0 · APP 88.0 · 分 86.0 ·
食 20.0 · 射埋 23.0 · DS 66.0 — and **KPP 58.0**, i.e. chance from the other side, for a fifth
time. DS is the per-*piece* variant throughout (raw `garbage_cleared` gives 68.4 · 62.0 · 81.2 ·
83.0 · 64.0 and is a different series); the 129-round headline block above is 07-22 and 07-24
pooled, not one session.

2026-08-14 (84 rounds) is the sixth, and the largest: VS 100% · 攻 91.1 · APM 90.5 · 送 82.7 ·
**APP 81.0, still the lowest of seven** · 分 79.8 · DS 70.2 · 食 17.9 · 射埋 18.5 — and **KPP 40.5**, below
chance for a sixth time.

2026-08-19 (70 rounds) is the seventh: VS 100.0 · 攻 93.6 · APM 92.9 · **分 91.4, the highest of
seven by 5.4 points** · APP 87.1 · 送 87.1 · DS 73.6 (raw 75.7) · 食 15.0 · 射埋 12.9 — and
**KPP 41.4**, the seventh measurement and the fifth of the seven below chance. Three columns take
their corpus high here (分 91.4 · COMBO 67.9 · FIN% 67.1) and **PC 48.6 is the first below 50 in
seven**, which is the least surprising thing on the list: see 全消 below for why PC has no
denominator worth a rate.

**Two of the 129-round block's "no signal" entries are false at 450 rounds, and the fault is
provenance, not arithmetic.** COMBO 45.0 and TST 55.8 were measured on the FIRST TWO SESSIONS
ONLY; the label was then carried forward as if it ranged over the corpus. Pooled over all 450
rounds, Bonferroni-corrected across the 17 columns:

| | pooled AUC | raw p | ×17 | verdict |
|---|---|---|---|---|
| COMBO | 56.22 | 0.00179 | 0.030 | **survives correction** |
| TST | 56.11 | 0.00031 | 0.0053 | **survives correction** |
| KPP | 44.22 | 0.0156 | 0.26 | below chance, but **not** distinguishable from chance once corrected |
| PC | 50.67 | 0.586 | — | genuinely no signal, confirmed at n = 450 |

COMBO's per-session series drifts upward the whole way — 41.1 · 51.0 · 62.5 · 55.7 · 57.0 ·
58.9 · **67.9** — so 45.0 was not *wrong* when written. It was a two-session figure that the
document kept presenting as a corpus verdict, which is the same defect as the 「70-89%」 donation
figure below wearing a different disguise: **a bucket label is a claim about the corpus even when
the number under it is honest about its n.** KPP is a sharpening rather than a reversal — below
chance in 5 of the 7 sessions and pooled below 50, but not distinguishable from chance after
correction, so it stays a negative result and must not be upgraded to "inverted".

Coaching conclusions, cross-validated over seven sessions: **APP is the lever** — higher in rounds
won than rounds lost in 14 of 14 player-sessions, though the *size* of that separation is not
stable and does not settle (yachi's own series runs 24.9 · 17.4 · 23.2 · 15.9 · 31.5 · **7.2** ·
23.1, so 08-14's +7.2% is the outlier of his series, not a level he fell to); **DS matters** in 9
of 10 player-sessions through 08-09; **KPP is flat** (0–3%) — reported as a negative result. When
adding a column or a claim, run `pipeline/claims/equiv.py` or the AUC probe rather than assuming a
stat is informative.

**08-09 splits APP the other way, and that is the finding of the fifth session.** Every earlier
session had one player ahead in *both* regimes by a similar margin — a style difference. Pool
attack over pieces after splitting the 50 rounds by who won them and the two regimes come
apart: won .6738 vs .6862 (+1.8%), lost .5124 vs .6425 (+25.4%) [C002]。個 won-gap 得一局撐住
（留一局：抽走 m2r5，數字變 +4.26%，即係郁 2.41 pp），50 局入面排第一，係第二大嗰局嘅
1.38 倍——所以「+1.8，成個 corpus 最細」講得，「兩邊贏嘅局打成平手」講唔得。yachi's won-round rate
is above pinglamb's *lost*-round rate [C003]. The rank test says this is not a variance
artefact — **both p's two-sided**: over losing rounds P(yachi > pinglamb) = 0.138, permutation
p = 1e-5; over winning rounds 0.464, p = 0.68 — and it survives dropping the three near-zero
rounds. (The winning-rounds figure was published as `p = 0.34` for months, which is the *one*-sided
value beside a two-sided one; the two-sided is exactly 2× it. Nothing here compares p's across the
two regimes, so the conclusion never moved — but a mixed convention in one sentence is how a
comparison across them would go wrong silently.) The per-session won-gap runs +5.8 · +10.8 · +5.9 ·
+7.9 · **+1.8**, the lost-gap +12.8 · +7.3 · +6.0 · +6.1 · **+25.4**. Two consequences worth
knowing before writing another report:

- **The volume route is not a law.** 08-01's headline was that 326 extra pieces bought back a
  7% efficiency gap to within 32 lines. 08-09 ran the same route into 382 extra pieces and
  **271 fewer** lines of attack, 8%+ of pinglamb's total [C004] — because buying it back
  requires the per-piece value not to collapse, and here it collapsed on one side only.
  (Seven sessions later this has a mechanism and a number; see 「個 shortfall 先係話事嗰個」 below.
  08-09 is the worst shortfall in the corpus, which is why it is the worst outcome.)
- **Advice taken can leave the score wider.** 08-01 flagged that 6 of 8 topouts were yachi's.
  08-09 has 4 topouts, all pinglamb's, yachi none [C006] — and the match score went 4:3 to 0:6.
  A metric moving the right way is not the same as the metric that decides. **08-19 is the second
  instance and it runs the other way** — 08-14's 11-of-13 did not persist, the split came back to
  4:3, and the series still went 4:7 → 3:7. Two independent instances from opposite directions, so
  this is a pattern in the corpus and not one night's anecdote.

**08-14 is 08-09's mirror, and that pair is why the split must be re-derived every session.**
Same decomposition, opposite answer: won .6032 vs .7174 (+18.9%), lost .5629 vs .5729 (+1.8%)
[C002]. The floors have met; the ceilings have not. 但個 lost-gap 得一局撐住
（留一局：抽走 m11r2，數字變 +4.65%，即係郁 2.87 pp），84 局入面排第一，係第二大嗰局嘅
1.72 倍——「地板撞埋」係成晚嘅講法,「差 1.8 pp」唔係。

**08-19 is the control on that pair, and it says the swing was an excursion.** Same decomposition
again: won .6803 vs .7226 (+6.22 pp), lost .5528 vs .6140 (+11.05 pp), session gap +12.40 pp
(112.4%) — which is 07-22's shape almost exactly (+5.8/+12.8 against +6.2/+11.1): ceilings close,
floors apart. The seven-session series now read

    won-gap    +5.8  +10.8  +5.9  +7.9   +1.8  +18.9   +6.2
    lost-gap  +12.8   +7.3  +6.0  +6.1  +25.4   +1.8  +11.1

so **the 17-point swing between 08-09 and 08-14 was a two-session excursion, not a trend in either
direction**, and the split returned to where the corpus started. That is the strongest support this
corpus has produced for the standing rule that the decomposition must be re-derived every session
rather than extrapolated: the *session-level* APP gap (110.0% on 08-14, 118.1% on 08-09, 112.4% on
08-19) tells you nothing about which regime carries it, and neither does the previous session's
decomposition.

Said within a player, 08-14 has pinglamb separating his own won and lost rounds by +25.2% and yachi
by only +7.2% [C003]. **That was a one-night state, not a standing property of either player.** The
(yachi, pinglamb) separation series runs (24.9, 17.1) (17.4, 21.3) (23.2, 23.1) (15.9, 17.9)
(31.5, 6.8) **(7.2, 25.2)** (23.1, 17.7) — so 08-14 is the only session where the separation is
effectively one player's alone, and yachi's +7.2 there is the outlier of his own series, not a
level he settled at; on 08-19 he is back to +23.05% against pinglamb's +17.70%. Likewise his
won-round rate, which had sat in a .657–.674 band for five sessions and fell to .6032 on 08-14, is
.6803 on 08-19. Read the 08-14 figures in this block as that night's, not as a trajectory.
His ceiling on 08-14 sat nearer pinglamb's floor (+5.3%) than pinglamb's ceiling (−15.9%) [C004].

Three consequences:

- **The volume route failed a second time.** 415 more pieces, 206 less attack, over 4% of
  pinglamb's total [C005] — after 08-09's 382 for −271. ~~Two runs, two failures; 08-01's success
  is the outlier, not the rule.~~ **That reading is wrong and 08-19 is what falsifies it** — the
  route is not unreliable, it is *bounded*, and the bound is arithmetic. See below.
- **The topout column swung from one extreme to the other in one session.** 11 of 13 are yachi's
  [C006] — his worst — where 08-09 had all 4 on pinglamb and yachi none. A single night's death
  tally is not a trend, and 08-19 confirms it did not become one: **4:3, the most balanced split
  of any session**, at 10.0% of rounds — the second-lowest rate of seven. The full series is
  y:p = 8:3 · 4:4 · 5:4 · 6:2 · 0:4 · 11:2 · 4:3, at 13.9 · 16.0 · 14.1 · 15.1 · 8.0 · 15.5 ·
  10.0 % of rounds. What made 08-14's worth acting on was that it moved *with* the piece surplus,
  i.e. there was a mechanism; what 08-19 shows is that acting on it moved the tally and **not the
  series**, which went 4:7 → 3:7.
- **The night has three acts and the gap tracks them**: over 17% across matches 1-3, under 7%
  across 4-9, over 11% across 10-11 [C007] — and all four of yachi's match wins fall in the
  middle window [C001]. Per-match, m9 is the only one of eleven where his attack per piece beats
  pinglamb's [C019].

### 個 shortfall 先係話事嗰個 — the volume route is bounded, not unreliable

08-19 ran the route a third time: **+312 pieces, −236 lines of attack** (−6.13% of pinglamb's
total), −61 639 in-game score, +100 lines. Three consecutive failures, and 08-01's success is 1 of
4 — which is exactly where this stops being a story about volume being unreliable.

A piece surplus buys back an APP gap of **exactly** `100·(surplus_pieces/other_pieces − 1)`
percentage points. That is the whole of what volume can do, and it is arithmetic rather than a
tendency. Subtract it from the session's APP gap and the remainder — the **shortfall** —
rank-orders the attack difference *perfectly* across all seven sessions:

| shortfall (pp) | −0.67 | +0.50 | +1.00 | +2.66 | +4.61 | +6.89 | +10.04 |
|---|---|---|---|---|---|---|---|
| yachi's attack − pinglamb's (lines) | +28 | −15 | −32 | −72 | −206 | **−236** | −271 |

08-01's surplus bought 6.27 pp against a 7.27 pp gap — shortfall 1.00, and it landed within 32
lines. 08-19's bought **5.51 against a 12.40 gap** — shortfall 6.89. **So 08-19 did not fail for
lack of volume: its surplus is 08-01's.** It failed because the gap it was asked to cover was 1.7×
bigger. Never write 「加粒數買唔返」 without the shortfall beside it — the route works, and what
predicts the outcome is how much of the gap was handed to it.

**Nothing in 08-19 needs a 「得一局撐住」 annotation, and that absence is itself a measurement.** No
published figure flips sign under leave-one-out and none reaches `check_loo.THRESHOLD = 0.5`; the
largest relative move is **0.281** (the won-gap, dropping m1r5). It is the first session since
07-24 to need none — worth stating because 07-28, 08-01, 08-09 and 08-14 each carry one above, and
four in a row reads as though the caveat were universal rather than measured per figure.

**`equiv.py`'s single-value 100% for 07-28 was an artefact, and `--two-site` now measures it
as 60%.** A windowed claim shares its rounds with the session total meant to imply it, so no
*single*-value mutation falsifies one without the other. Two changes break the tie: moving
pieces from a match-3 round to a match-1 round keeps `total_pieces`, `total_garbage_attack`
and C008 true while flipping C005 false. The second family does exactly that, and the four
claims that drop out (C002, C004, C005, C006) are precisely 07-28's windowed ones.
Measured with `--two-site round`. Per-session, over the six sessions that have an
`equiv-coverage.json`: 07-22 81% → **79%**, 07-24 96% → **94%**, 07-28 100% → **60%**,
08-01 100% → **92%**, 08-09 82% → **73%**, 08-14 84% → **68%**. 2026-08-19 has no artefact
yet — the sweep needs the session's hand ledgers, which land after the session does, so a
seven-session figure is not available and must not be inferred from the six.

**07-28 is not the exception — five of the six measured sessions lose coverage to the second
family**, and
every claim that drops is windowed or per-match (08-01 C002, 08-09 C005, 08-14 C007/C019/C020).
`sum_round_range` arrived at 07-28 and every session since uses it, so a single-value figure
published alone is blind to exactly the headline claims. `check_equiv_coverage.py` fails the
build if one is published without its two-site companion for a session holding windowed claims.

**The single-value figures were a seeded sample until 2026-08-15.** One perturbation kind was
drawn per site, so 07-22 read 85% at the committed seed, 87% at seed 3, 83% at seed 42 — with
the denominator moving too — while the docstring claimed the whole space of one-value changes.
Every kind is enumerated now: ~5× the mutants, deterministic across seed and `PYTHONHASHSEED`,
and 07-22 settles at 81%. `--seed` survives only because `--samples` still draws.

**The delta is HALF the source, and that is not a detail.** The first implementation moved the
whole value, leaving every source round at 0 — 145 615 of 145 615 moves — so its evidence was
rounds like `pieces=0, lines=48, lifetime=65591`, which no extractor can emit. It also made
both its asserts tautologies (`(va-d)+(vb+d)==va+vb` is an integer identity; `va-d>=0` with
`d==va` is `0>=0`), i.e. decorative guards sitting under a comment claiming the very standard
the code broke. And it *inflated* the result: 07-24 read 96% under whole-value moves against
98% under legal ones. Sources below 2 are dropped and counted. The surviving guard
(`1 <= d <= va - 1`) is unreachable by data and guards the delta *rule* — mutate it to `d = va`
and it fires, which is the mutation test that licenses keeping it.

`--two-site` is off by default; `match` granularity is an upper bound on coverage and `round`
must be re-run before publishing a figure.

07-28's own finding is about *change over a night*, which no earlier session asked: yachi won
the first two matches and lost six straight, but his rate did not collapse — in matches 1-2 the
two players' APP were level (0.62305 vs 0.62216, yachi ahead by 0.0009) and from match 3 they
separated, pinglamb +4.99% and yachi −4.92%. Both totals are nearly equal (attack 3264 vs 3249)
because yachi threw 378 more pieces to get there. 企得穩嘅係「兩邊差唔多」,唔係個差額:
「差 15 行」得一局撐住（留一局：抽走 m8r8，數字變 -49 行，即係郁 34 行），連正負號都反轉。
That is what `sum_round_range` exists for.

08-01 asks the next question down: **APP decides a round, and it does not decide a night.**
pinglamb's APP was higher in all seven matches and in both regimes — his won rounds beat
yachi's won rounds, his lost rounds beat yachi's lost rounds — yet he lost the series 3:4. The
totals land on top of each other (attack 3394 vs 3426, in-game score 1087345 vs 1087921, 0.05%
apart) because yachi bought the 7% efficiency gap back with 326 extra pieces at a higher PPS
in all seven matches. 兩個差額都係一局話事——攻擊差額
（留一局：抽走 m1r4，數字變 -1 行，即係郁 31 行），分數差額
（留一局：抽走 m6r5，數字變 +11480 分，即係郁 12056 分），兩個都會反轉正負號。
所以「差 32 行」同「差 576 分」唔好照抄,企得穩嘅係「兩邊撞埋一齊」。 Two routes, one destination; the night was then decided by *which* rounds
fell where — the seven matches alternate winners perfectly, so it came down to the last one.
Same window operator, per-match windows this time: `sum_round_range(pl, f, mi, mi+1)` is how
"in all seven matches" gets proved match by match instead of asserted from a session sum.
The visible cost of the volume route is in the death tally: 6 of the 8 topouts are yachi's.

## 速率紀錄要有局長下限 — and the two holes cutting one opens

For three sessions the APM/VS records were the plain argmax and were **all** short-round
artifacts. A rate has the round's length in its denominator, so over a short round it is a
sample mean over a small n. Measured in `analysis/rate_records.R` over all 900 player-rounds
(seven sessions): regressing log SD on log t gives **−0.625 for VS and −0.715 for APM**, slope 0
rejected for both (p 8.6e-05 / 5.3e-05). All **21** unqualified records (3 metrics × 7 sessions)
came from the shortest quartile — p = 2.3e-13 — and 07-22's headline 約262.6 was a 15.6 s round,
46% above that session's qualified peak.

**Two things in that paragraph changed when the sixth session was added, and the honest version
is weaker than the five-session one. Both still hold at seven.** (a) APM's −0.5 is **outside**
its CI — [−0.918, −0.525] at six, [−0.887, −0.542] at seven — so the decay is *steeper* than a
pure sample mean and the conclusion holds a fortiori, but "both with −0.5 inside the CI" is no
longer true; (b) the mean is **no longer flat for VS** (106.9 → 119.4 across the bins, p = 0.01)
— longer rounds do carry a mildly higher mean VS. The SD still falls several times over the same
span, so the variance effect dominates and the qualifier stands, but the control is now "the mean
moves a little, the spread moves a lot", not "the mean is flat". PPS's mean is still flat
(p = 0.25).

**Do not quote a number for that SD fall from here, and do not put one in the report either.**
It is `pipeline/records.R_VS_SD_RATIO`, derived from `R_VS_SD_SHORT` / `R_VS_SD_LONG` through
`fmt.ratio1`, which floors — 4.1× at six sessions, **3.8× at seven**. The report's footnote said
「足足細咗四倍」 as a typed word for six sessions, where it was true, and shipped **false into all
seven rendered reports** the day 08-19 landed, because 足足 asserts a floor of four and the ratio
had fallen to 3.82. Nothing could catch it: `check_prose_figures` resolves 約-figures against
facts.json, and this is a derived R statistic that appears in no dataset. It is computed now, and
guarded — `_MIN_SD_RATIO = 2.0`, which is the ratio the *argument* needs (the mean moves 1.11×
over the same span, so the spread must clearly dominate it), deliberately not the 4 the number
happens to sit near. A guard set to today's measurement is a copy of the measurement.

The script's session list is hardcoded, so **adding a session means editing it and re-running**
— otherwise the evidence for `QUALIFYING_MS` silently stops covering the newest data. Adding
08-09 also broke it: the records test carried a literal `12` for "3 metrics × 4 sessions", and
`binom.test(15, 12, ...)` aborts. It derives `n_records` from `sessions` now. `repo` used to be
an absolute path to one checkout, which meant a git worktree silently regressed the *other*
tree's sessions; it resolves from the script's own location now.

`QUALIFYING_MS = 60_000` is where definition and data agree: APM and VS are per-*minute*, and
each session's record names the same round for every cut-off from 50 s to 70 s, so nothing
rests on the number. Counts are deliberately unqualified — fitting more lines into a short
round is harder, not easier.

Two holes opened the moment the qualifier was written, and both are now gated:

1. **The record's `count_rounds(... > v) == 0` conjuncts stopped ranging over short rounds**,
   so their APM/VS constants lost their upper bound — the only remaining constraint,
   "the winner had the higher VS", survives every increase. `mutation_test.sh` caught it
   with a 14-of-4557 random sample, i.e. by luck. `unqualified_rate_peaks` fixes it by
   keeping the unqualified maximum as its own claim (worded as the burst it is), and
   `pipeline/check_rate_coverage.py` is the deterministic gate: every short round, both
   players, both fields, must be falsifiable by *raising*. Checking "some perturbation is
   caught" is too weak (the winner-gt-loser claim catches every decrease) and checking both
   directions is too strong (a round loser's VS has never been pinned from below, and
   inventing a claim to fix that would be writing for the checker, not the reader).
2. **`==` had never appeared in a Cond**, so nobody had noticed `smt.py` passed the operator
   through verbatim — SMT-LIB spells equality `=`, and both solvers answered
   `unknown constant ==` rather than a verdict. Only `check_smt` caught it; Python and Dafny
   accept `==` happily. `smt.py` now maps operators explicitly and dies on an unknown one,
   and `spec.py`'s `c_field`/`c_dur` reject an unsupported operator at construction, so the
   failure is a build error rather than a solver error.

## C-Spin 同 DT 砲 — the second quarantined section, and its three controls

`sim/opener-facts.json` → `pipeline/opener_section.py`, gated by `check_opener_section.py`. Same
quarantine as the forecast section and for the same reason: one simulator, no second independent
implementation, so **no claim ids and no ✓ badges**, and nothing merges into `facts.json`.

The two openers are the same pair of T-spins in the two orders — **DT 砲 is a Double then a Triple,
the C-Spin a Triple then a Double** — which is why one section covers both. Order is a property
`facts.json` does not have (it counts `tspin_doubles` and `tspin_triples`, not which came first), so
it is exactly the kind of question the quarantined tier exists for.

Each metric ships with the control that says what it is NOT, and each control is enforced, not
merely documented:

- **ordering** — control is *exposure*: scored only on rounds holding both spins, and re-run over
  the whole simulated round so the short verified prefix cannot manufacture the result. Seven
  sessions: **527 of 528 run the C-Spin order and exactly one runs the DT order** (08-19 adds 73
  rounds and 73 C-Spin orders, `dt_order` 0 for both players).
  **That one is the corpus's first positive, and two independent metrics name the same round.**
  yachi, `replay-2026-08-14-2.ttrm` round 3 (m3r4): a T-spin Double on lock 13 and a Triple on
  lock 18, and — from a completely different input, the board's occupancy at the end of bag 1 —
  an **exact** match against harddrop's DT Cannon page, as drawn and mirrored. Through five
  sessions every exact first-bag match had been a PCO, which made "the instrument only ever finds
  one thing" a fair worry; it is answered. Both facts are pinned in `openers.test.ts`
  (`DT_ORDER_IN_OPENER`, and the exact-match block) as a *named exception list* rather than a
  relaxed bound, so a second one has to be investigated instead of absorbed. The verified prefix
  of that round runs to lock 208, so it is not the short-prefix artefact the window control exists
  to rule out. `opener_section.py` needed no change — it already had the branch for a non-zero
  DT count, and prints「先 Double 後 Triple（DT 砲次序）有 1 個」.
  **It names a CLASS, not the C-Spin, and that was found by measuring the named openers.**
  harddrop files **38** openers under `Category:Triple Double openers` — C-Spin, Honey Cup, Stray
  Cannon and Mountainous Stacking among them — and every one opens Triple-before-Double. A session
  playing Honey Cup every round produces the identical 221-of-221. The category is transcribed into
  `wiki-openers.json` (a class this repo drew itself would be a class chosen to fit the result) and
  `check_opener_section.py` fails if the table is published without the paragraph saying so.
- **first bag vs the catalogue** — control is *set choice*. `isCSpin` is a substring match whose
  three hits are `Fake C-Spin`, `Secspin` and an `SDPC-Spin` compound — arguably no real C-Spin at
  all — so every number is reported over a narrow and a widest reading of both openers
  (`NAME_SETS`). The reportable finding is that the answer does not move. A null here is always
  "not these catalogued pages", never "not this opener".
- **slot geometry vs harddrop's 38 diagrams** — control is the *cross-tab by lines*, and it is the
  reason this may be printed at all: ~9 in 10 Triples match the window against ~1 in 10 Doubles, so
  it detects a Triple-shaped slot, not an opener. `check_opener_section.py` fails if the Doubles
  sentence is deleted while the share stays, because that edit turns a shape test into "89% of
  these were C-Spins".

`emit-opener-facts.ts` exports `build()` so `openers.test.ts` can assert the committed artefact
reproduces byte-for-byte — the same rule facts.json, the ledgers and the .dfy are held to.

## 六個具名定式 — the fourth table, and the coverage bug it exposed

Honey Cup, Stray Cannon, Mountainous Stacking 1/2/3, TKI-3, PCO. Same quarantine; the metric is
"is the opening board this opener's field, cell for cell".

**Sampling at seven locks only was a coverage bug, not a choice.** A player who holds a piece
through bag 1 has locked **six** pieces when the bag ends, and that is how harddrop draws four of
the six (Stray Cannon says "keep either S or Z in hold"). A 24-cell field can never equal a 28-cell
board, so those openers were never *compared*, not scoring zero. `OPENER_LOCKS = [6, 7]` fixes it
and also reaches the 75 clean 24-cell catalogue pages that were invisible — including the PCO setup
that keeps I on hold. Pre-existing blocks re-emit byte-identical on all pre-existing sessions.

**`opener_db` alone cannot answer this**, which is why `wiki-openers.json` exists: 484 of its 783
pages are drawn on a filled base, and a page with a full row is a state that would have cleared.
TKI-3 has 12 catalogue pages and **none** are clean. Where both sources draw an opener (MS1, PCO)
they agree cell-for-cell — `cross_check()` gates that, and the mutant proving it flips a cell on an
opener both draw.

**Read the exact column, never `≤4 格`.** The baseline — the same boards against openers the player
is *not* playing — reaches the ≤4 band about as often, because these boards sit 3-4 cells from
almost any opener page. Only exact separates. `occupancy_aliases` and `round_overlap` name the
columns that are the same rounds twice: MS1 and MS2 are one bag-1 shape built from different
pieces, so their rows are identical in every session and must never be added.

The repertoires split, reproduced independently in all seven sessions (pinned in `openers.test.ts`):
**pinglamb opens Honey Cup** more than yachi does, **yachi opens Mountainous Stacking** more than
pinglamb does **and is the only one who plays TKI-3 at all** (pinglamb 0, every session). PCO
appears only for yachi, only on 07-24 and 08-01. **The per-session counts are deliberately not
written here** — read them off `sim/opener-facts.json`, or off the `openers.test.ts` assertions,
which pin the ORDERING and nothing else.

**That is a decision, not an omission, and it comes out of a defect.** This paragraph used to carry
per-session ranges — Honey Cup 17-25, MS1 11-25, TKI-3 5-8 — and **two of the three were already
false when 2026-08-14 landed**, five days before anyone looked: the true seven-session ranges are
17-30, 11-26 and 5-15. Nothing noticed because **no file in the repo contains those numbers**;
they existed only in this prose, so there was nothing to re-derive them from and nothing to
disagree with them. The obvious repair — a gate that recomputes the bands — is the wrong one:
three of the five bands moved inside seven sessions, so its normal state would be red, and a gate
whose normal state is red is not a gate. The ordinal claims are what has actually reproduced
seven times, so those are what is published.

**PCO's payoff is bounded by facts.json, and its timing is the one simulator figure with a verified
counterpart.** PCO is defined by an outcome, so the row splits in two. HOW MANY perfect clears is
`clears.allclear`, twice-extracted — see 全消 below. WHEN each landed only the simulator can say, and
what licenses printing it is that `perfect_clear_timing` compares the simulator's per-round count
with the replay's own counter for **every** player-round and emits the piece numbers as `null` unless
all of them agree. They do: **900/900 rounds, 95/95 perfect clears**, seven sessions, no unknowns.
`check_opener_section` fails if the piece numbers are published without that agreement figure or
without harddrop's ten-piece deadline beside them.

The finding is that **3 of the 95 arrived inside that deadline** — still the same three, because
08-14's twenty all landed on piece 15 or later and 08-19's ten did too (yachi 15 · 20 ×4,
pinglamb 20 ×5) — and the bulk land on piece 20. These are mid-game perfect clears, not the
opener. 08-01 holds the corpus's only completed PCO: yachi matched the field twice and delivered
once. 08-14 has the most All Clears of any session (20: yachi 11, pinglamb 9) and **none of them
is inside the window**; 08-19's ten (5 each) are likewise all outside, so the denominator has
grown by 10 without moving the numerator — the reading is *reinforced* by the seventh session
rather than merely surviving it.

**An earlier revision of this section said the opposite** — that `eng.board.perfectClear` invented
clears the sessions did not have — and it was wrong for a reason worth keeping: the facts.json
lookup it rested on read `players[u].allclear`, one level above the counter, and `?? 0` turned every
undefined into a plausible zero. All five reports published 「一個 Perfect Clear 都冇出過」 while the
`.ttrm` files held 65. Nothing caught it: the value was in range, the artefact re-emitted
byte-identically, and the test recomputed the total down the same wrong path, so it agreed with
itself. Two rules came out of it — **a required field that goes missing must throw, never default**
(`sessionPerfectClears` declares `clears.allclear` non-optional and dies on a non-number), and **a
test that re-derives a value the way the code does can only catch a typo** (`openers.test.ts` now
pins each session's counts as literals and asserts the total is not zero).

## 全消 — the Perfect Clear section, and the two questions it keeps apart

`pipeline/pc_section.py`, region `perfect-clear`, **inside** the trust chain: every figure is read
out of the proved claims' own specs (`pc_rounds`, `pc_solo_lost`, `clears_allclear`), never
re-derived from facts.json, so the table cannot print a number no lemma covers. `clears.allclear` is
read out of the `.ttrm` independently by both extractors, which is why this one is badged while the
opener tables are not.

The point is not the count. Across seven sessions, **83 rounds had exactly one player with a perfect
clear and that player lost 39 of them** — the AUC block above says the same thing (PC **50.67**
pooled over 450 rounds with p = 0.586, 52.4 on 08-14 with 68 of 84 rounds tied at zero, 48.6 on
08-19). So the section prints "rounds won" beside "rounds with one" and refuses to print a rate: the
denominators are 3-12 rounds per player, and a percentage over three rounds reads far more confident
than the data is. Two more controls it may not lose: 全消次數 ≠ 有全消嘅局 (a round can hold two), and
"whether" is facts.json while "when" is the simulator's, in the quarantined section below.

## 最癲一局 — one round, deep-dived, and why it needed no new operator

`pipeline/intense_round.py`, region `intense-round`, **inside** the trust chain. The round is the one
`most_intense_round` already selects — highest combined VS among rounds of `QUALIFYING_MS` or more —
via the shared `generators._intense_round`, so the section and the claim that announces it cannot
describe different rounds. Seven new families per session (`intense_round_profile` ×2, `_edges`,
`_attack_rate`, `_downstack_rate`, `_vs_split` ×2); every printed figure is read back out of the
proved spec by `intense_round.py`'s readers, never re-derived.

**The selected round is often won by the player losing the attacking exchange**, which is the reason
the section exists: 逐局全數據 gives every round the same row and explains none.

| session | round | winner trailed on | DS/piece W:L |
|---|---|---|---|
| 07-22 | m1r5 | APM, attack, PPS, maxspike, **APP** | ×2.00 |
| 07-24 | m6r8 | APM, attack, maxspike, topbtb, **APP** | ×2.20 |
| 07-28 | m8r8 | lines | ×0.51 |
| 08-01 | m7r3 | topbtb | ×1.12 |
| 08-09 | m5r7 | **nothing — led on everything** | ×0.82 |
| 08-14 | m11r2 | APM, PPS, pieces, attack, maxspike, topbtb | ×1.81 |
| 08-19 | m8r2 | lines | ×0.74 |

The 08-19 row is read out of that session's proved claims (G084's axis count and non-axis column,
G086's two per-piece figures), not re-derived — the same route `intense_round.py`'s readers take.
It is 07-28's shape: the winner trailed on one column only, led on APP (0.929 vs 0.669 [G085]),
and is behind on one *non-axis* column (清走) which the table does not list because the claim does
not count it as an axis.

The table lists **columns**, while the claim and the rendered section count **axes** — APM and 攻擊量
are one axis, PPS and 粒數 are another, so 07-22's five columns are three axes and the section says
「3 條軸」. That is two vocabularies on purpose (a reader scanning the table wants the columns; the
claim must not double-count an axis), and the bolded **APP** is a third thing again: it comes from
`intense_round_attack_rate`, not from `_edges`, so it is proved but it is not one of the axes the
count ranges over. Do not reconcile these by making the numbers agree — check which family a figure
came from first.

08-09 is why the generator has two shapes. A section that only had the dramatic sentence would be
writing for the sessions it liked; the flat case prints「呢局冇得拗」 as the result it is.

**07-22's PPS entry arrived on 2026-08-16 and is the sharpest argument in the repo for sourcing a
rate at results-time.** Under the old `player.stats` tick both players read PPS 1465 in that round, so
`intense_round_edges` rendered `==` and 落速 was not a trailing axis — the claim said "2 of 4". They
threw the same 108 pieces, but yachi survived 250 ms longer (73982 vs 73732 ms), so his PPS is
strictly lower: 108/73.9667 = 1.4601 against 108/73.7167 = 1.46506, exact under the frame-count T.
The tie was two stale samples coinciding, and a verified lemma was proving it. Nothing but
re-sourcing finds that class: the value was in range, every gate was green, and an equality is
exactly the shape a mutation test cannot flag as suspicious.

**Two idioms worth reusing, both of which the algebra already supported.** The algebra has no
division, so a derived rate is *pinned* — not merely compared — by bounding the numerator against the
denominator: `v = floor(1000·num/den)` iff `v·den <= 1000·num < (v+1)·den`, one `between`. It has
teeth because the band is `den` wide while a one-unit change to `num` moves the left side by 1000.
And `|d| <= ε` is `between(d, -ε, ε+1)` — `between` is `lo <= x < hi` in all three backends.

**The VS split is a BOUND, never an equality, and that wording is load-bearing.** `vs_x1000 ·
finaltime_ms == 10⁸ · (garbage_attack + garbage_cleared)` is an identity *observed in this data*;
TETR.IO publishes no such formula and this repo must not assert one. Corpus-wide the residual is
median 1.1e-4 for the player who died and at most **6.3e-4** for a survivor, so `intense_round_vs_split`
**skips any player whose residual reaches half a unit** rather than print a bound wide enough to
swallow a line of attack. On the six selected rounds through 08-14 the worst residual is 0.028 of a one-unit change,
which is also what makes every one of them mutation-killable.

**That paragraph read "reaches 13.4% for a survivor" and "0.489" until 2026-08-16, and the 13.4% was
an artefact of the reader, not a property of the data.** The rates came from `player.stats`, a live
in-game tick sampled before the round ended, so a survivor's mid-round VS was being checked against an
end-of-round attack count — the asymmetry was in the timestamp, which is exactly why it fell on
survivors. Re-sourced from `results.aggregatestats` the identity holds to floating point, and the guard
that fired on **13 of 760** player-rounds now fires on **0 of 760**. Do not read that as a reason to
delete it: the residual does not go to zero, it goes to a quantization floor. (Both `760` figures
are the first six sessions; the guard's per-session output is what says whether it still fires at
900, and it is checked per session rather than re-pooled here.) `finaltime_ms` is
milliseconds while the clock is frames, so the residual grows with `attack + cleared`; the corpus's
worst player-round sits at 0.057 of the trigger (~18× headroom), and on that round `attack + cleared`
would have to reach ~1114 against its actual 63. That is a fact about how much garbage these two move
in a round, not a theorem.

Two gate gaps the new figures exposed, both now closed in `check_prose_figures.pools`: it had no
per-*round* derived rates (only session aggregates), and its seconds pool held `lifetime` but not
`finaltime_ms` — 169748 ms floors to 169 and no `lifetime` in that session does. A correctly floored
figure that resolves against nothing is the state the gate cries wolf from.

**Every column in `_INTENSE_EDGES` must also be a row the section prints.** In-game `score` was in it
and is not now: it has no row (it rewards drop distance, so it is not an attack proxy), which made the
claim count seven trailing columns while the table could only mark six — and the section's sentence
points *at* the marked cells. Caught by reading the rendered page, not by any gate.

## 捐窿 同 STMB Cave — two techniques that are not openers, and the arithmetic trap under one

`pipeline/openers/wiki-tspin-techniques.json` → tables five and six of the quarantined section.
Same tier as slot geometry: a **per-T-spin board-state predicate over the whole round**, scored on
the verified prefix, no claim ids and no badges.

**Neither page is an opener, and reading them as openers is the first mistake available.** harddrop
files both under `T-Spin techniques / Mid-game T-Spin setups`; their diagrams are 24-112 cells drawn
on partial stacks, so a 24- or 28-cell opening board can never equal one. Putting them in the
六個具名定式 table would have printed a column of zeros meaning "never compared" while reading as
"these players never do this" — the same shape as the `OPENER_LOCKS` coverage bug.

**The naive Donation clause is forced by arithmetic: it fires on 100% of T-spin clears.**
"The well column is filled through the rows the spin cleared" cannot fail: a full row *requires*
every column filled, so that clause counts line clears. That is not a measurement any more — it is
`NaiveClauseForced` in `spec/DonationCave.dfy`, and the corpus agrees at exactly 100.00% of all
**4763** scored clears. As a *predicate* — the shipped thresholds (cavity ≥ 4, walled) with the
re-opening clause deleted — it fires on **29-37%**. All the discriminating power is in the
**re-opening** clause: every filled cell of the column must lie inside the cleared rows, so the
clear leaves it open surface-to-floor. With it, the rate drops to 2.1-3.3% per session
(**127** donations across seven sessions).

**This paragraph said 70-89% until 2026-08-14, and that figure names no variant of the clause it
describes.** The bare clause is 100%; at the shipped thresholds it is 28.9-36.8%; only a composite
with `cavity ≥ 1` lands in the band (74.6-77.0%), and it never reaches 89%. A rate was being quoted
for something proved to be always true — the same shape as the 3379-vs-3142 note above, and the same
lesson: a figure quoted in prose is not the thing it describes.

**Quote the band as a band, and re-measure it every session — it moved on the sixth.** Through five
sessions the shipped-thresholds-minus-re-opening rate sat in 28.9-33.6%; 2026-08-14 fires at
**36.8%**, three points above that ceiling, while the pooled rate barely moves (31.1% → 32.4%). The
pooled figure alone would have hidden it. The `cavity ≥ 1` composite is the opposite case: its
74.6-77.0% survives verbatim, but only because 08-14's 77.04% ties 08-09's 76.99% at one decimal
place — a seventh session past 77.05 moves it. Both bands are per-session ranges, so a new session
can break one without changing any pooled number.
`D = 4` and "walled at the **deepest** 4 cavity rows" are harddrop's numbers, not tuned: of its 20
named setups 17 draw a four-cell cavity and 3 draw five, never three or six; and requiring *every*
cavity row to be walled drops TSS L Donation, which the page draws as a donation.

**Both bands survive the seventh session, and both survive for the reason that paragraph warned
about rather than by a margin.** The per-session series now read 28.93 · 33.64 · 30.99 · 29.74 ·
33.27 · 36.84 · **36.13** for shipped-minus-re-opening (08-14's 36.84 is still the ceiling) and
74.72 · 76.84 · 74.60 · 76.80 · 76.99 · 77.04 · **76.51** for the `cavity ≥ 1` composite. So
74.6-77.0 still rests entirely on 08-14 tying 08-09 at one decimal place, and an eighth session
anywhere in 77.05-77.94 moves it. Pooled, neither says anything: noReopen 32.37 → 32.94, cav1
76.13 → 76.19. **Nothing in the repo re-derives either band** — like the repertoire ranges above,
they exist only in this prose, so re-measuring them by hand is part of adding a session, and the
per-session series is written out here so the next hand has something to check against.

**Every donation in this corpus sits on a garbage-derived well — 0 self-built, all seven sessions**
(08-19 adds 24 of 24; **0 of 127** corpus-wide).
The oracle keeps the engine's own seeded-RNG garbage hole *columns*, which disagree with the
ige-recorded ones 97 of 103 times over the first six sessions (`oracle-source.ts`), so the count
says the board offered the
shape that often and can never say which column was donated into. The check that finds this must
read the row's **filled** cells for the `-1` garbage sentinel: the well cell is empty by
construction and carries `null`, so testing it directly is a guard nothing can fire — that exact
bug reported every well as self-built for a whole round of measurement.

**The STMB cave is OFFSET from the T and its roof test is vacuous.** The cave shares two of the T's
three columns and reaches one past them, so the test is *overlap*, never containment — containment
misses all six drawn Basic Structures. And the cave's roof is the nub row the Double just
completed, which roofs everything beneath it by definition. A roof test would have been a decorative
guard — and since 2026-08-14 that is **proved, so there is no count here to keep current**. Two
five-session counts used to stand in for the proof and had drifted into disagreeing with each other
by 2026-08-17 — "0 unroofed runs in 1914" here against "0 of 2378 real T-spin Doubles" at
`emit-opener-facts.ts:324` — neither re-derivable from any committed artefact, because nothing emits
a count of unroofed runs. Both are deleted rather than re-measured: a corpus count is weaker evidence
than the proof it now duplicates, and it is the half that goes stale every session
(`RoofForced` / `RoofCannotDiscriminate` in `spec/DonationCave.dfy`:
conjoining a roof test
to the cave predicate yields an equivalent predicate, over the whole board width and not merely over
cave runs). The proof also shows the code assumes more than it needs: **maximality is not used** —
any cleared row above the run roofs it, and a Double always has two full rows. `IsMaxCleared` and the
two-row hypothesis are kept for fidelity to `caveAt`, not because the argument rests on them.

Two cross-tabs, and the section may print neither number without both: **by depth**, 48 of the 49
width≥3 hits are one row deep — a dimple, not a cave — leaving exactly **1 genuine cave in 900
player-rounds**; **by lines**, the same gap appears under T-spin Triples at a *higher* rate (9.0%
vs 1.7% on 08-09; 58 hits under Triples against 49 under Doubles over the seven sessions), where it
is ordinary TST residue. A shape that fires more often under the spin the technique is not about is
a shape test.

**The class control is the article's own comparison list, not a category.** harddrop has no
"floating T-spin" category; `Mid-game T-Spin setups` (63 pages) is a *when*, not a shape, and
`Back-to-Back T-Spin setups` (38) does not even contain STMB Cave. The page itself says the cave
"is just Sky Prop but with 3 columns wide hole" and that a variant "has the same shape and steps as
Shachiku Train", so the metric names a **class** — the same move the `Triple Double openers`
category makes for the ordering metric. All three category counts are recorded as evidence.

Both metrics are licensed by one check: the per-lock board snapshot plus the lock's cells must make
exactly the rows full that the engine independently recorded clearing. Different state, so it is a
real gate — **4763/4763 across seven sessions**, and a spin it cannot reconstruct is dropped, never
scored. (This line read **3379/3379** until 2026-08-14. 3379 is the *whole-round* T-spin clear total
over the five sessions there were then; the check is scoped to the verified prefix, which was 3142.
The figure was written from a whole-round probe and matched no committed artefact —
`donation.check.tspin_clears` is what sums to the gate, and the whole-round total is now 5078, so
the two still differ by 315. Nothing caught it because CLAUDE.md is prose: a gate figure quoted here
is not the gate.)

### 分母錨咗 replay 自己數嘅 counter — the one part of this section that is not simulator-only

The reconstruction check above is *internal*: two states the same engine built separately. It says
the boards are coherent; it cannot say the engine counts T-spins the way the game does. That
question has an outside witness — `results.stats.clears.tspindoubles` and its seven siblings, which
`extract.py` and `extract2.ts` each read into facts.json as `tspin_doubles` etc. **Both extractors
agree on them, so they are inside the trust chain**, and `tspinCounterCheck` compares them per
player-round, per kind, over the whole round:

| | |
|---|---|
| rounds where every kind agrees | **900 / 900** (seven sessions, no unknowns, 0 unclassified sim clears) |
| whole-round T-spin clears, sim vs replay | **5078 = 5078** |
| what the verified prefix scores of them | **4763**, i.e. **93.80%** coverage |

So the two tables' **denominator** leaves quarantine: `tspin_clears_scored` is now a subset of a
total the trust chain already carries, and 「可核覆蓋」 names the subset. This is the
`perfect_clear_timing` pattern (900/900 against `clears.allclear`) applied to a denominator instead
of a timing.

**The numerators do not.** Which clear was a donation, and how wide the gap under it was, still come
from one simulator with no second implementation — so the section keeps `report_eligible: false`,
mints no claim ids and carries no ✓ badges. `ANCHOR_MARKERS` / `CAVE_ANCHOR_MARKERS` in
`check_opener_section.py` demand **both** sentences at both tables, because deleting the second
while keeping the first is exactly the edit that reads as "this table has been verified".

Two traps, both of which have shipped here before in other forms:

- **Minis are part of the denominator**, so they are part of the anchor. The collection loop scores
  any T lock with `spin !== 'none'` that cleared, so an anchor over `tspinsingles/doubles/triples`
  alone would license a smaller set than it covers. All eight kinds are enumerated in
  `TSPIN_COUNTERS`, including the four that are zero throughout — a kind that starts appearing must
  surface as a disagreement, not vanish from both sides.
- **A missing counter is UNKNOWN, never 0.** `?? 0` on both sides makes a corpus of zeros agree with
  itself and `agrees` stay true — the same shape as the `?? 0` that published 「一個 Perfect Clear
  都冇出過」 for five sessions holding 65. A round carrying none of the eight counters is excluded
  and counted in `unknown_rounds`; `openers.test.ts` pins `tspin_clears_replay` per session as a
  literal and asserts it is nonzero, and the mutant that zeroes both sides is killed by it.

### 第二個引擎 — `dual_engine`, and why its headline rate is never the sentence

The other route is a second implementation, and two engines already exist that share no code: the
hand-port `runCase` and the vendored clean-room Triangle `runCaseOracle`. `dualEngineCheck` runs
both over every case and compares the two board-state verdicts lock by lock, as far as **both** are
verified.

**What is published is the confusion matrix, never the agreement rate**, and that distinction is the
whole finding. Both verdicts are rare — 49 caves and 127 donations in 4763 scored clears — so an
overall rate is negatives agreeing with negatives. Split by the oracle's own verdict, over seven
sessions:

| | overall | **on the positives** |
|---|---|---|
| cave | 2019/2019 (100%) | **23 / 23** |
| donation | 1944/2019 (96.3%) | **11 / 58** (19.0%) |

The donation's 96.3% is **1933 of 1944** agreements being both engines saying "no". On the thing the
table actually counts the two engines disagree about **four donations in five** — the opposite
reading from the one the rate gives, and the same failure mode as a detector clause entailed by its
siblings. `openers.test.ts` asserts `both_no / overall_agreements > 0.99` (it is 0.9943 at seven
sessions) so a future change cannot quietly make the rate look meaningful, and `DUAL_ENGINE_MARKER`
fails the build if the section prints a rate without the sentence saying what is in its denominator.

**Neither metric leaves quarantine on this.** The hand-port verifies a far shorter prefix (27 locks
against 81 on average), so the comparison reaches **2019 of 4763** scored clears — cave's 23
positives are 23 of the corpus's 49. It is a check on the verdicts, not a re-scoping of the tables,
exactly as the counter anchor licenses a denominator without redefining it. What it buys the
donation table is a *caveat it did not have*: the one metric here with no second implementation
backing it, stated as a measurement.

**The disagreement is the BOARD, not the predicate, and that is what `board_split` says.** Only
**1146 of the 2019** comparison points put the two engines on the same board, so at **43.2%** of
them they are judging boards that differ cell for cell (median 12 cells), and every figure in the
table above is read inside that. Split the positives by board equality and the donation resolves
completely:

| | positives | on identical boards | agree | **agree · identical** | **agree · differing** |
|---|---|---|---|---|---|
| cave | 23 | 4 | 23/23 | 4/4 | 19/19 |
| donation | 58 | 7 | 11/58 | **7 / 7** | **4 / 51** |

So the two engines do not disagree about what a donation *is* — they disagree about the board, which
is `oracle-source.ts`'s garbage-hole problem showing through. **The cave's row is a different claim
and must never be worded like the donation's**: agreeing 19 of 19 on boards that differ is the
verdict being *robust* to the drift (consistent with the drift sitting in low garbage rows while the
cave is local to the spin), not nineteen independent confirmations. `DUAL_SPLIT_MARKER` and
`CAVE_SPLIT_MARKER` fail the build if either sentence goes missing.

A false start worth not repeating: the first version of that probe pushed both engines through the
reconstruction check and the hand-port licensed **0 of 1355** (over the five sessions there were
then). A 0%/100% split is a bug report about the comparison, not a result. **The reason recorded here
was wrong until 2026-08-14** — it said `records[].clearedRows` means different things in the two
engines, "the hand-port leaves it empty on most clearing locks". Measured: **0 empty of 5472**, and
`clearedRows.length == lines` every time in both engines. The real cause is that `records` and
`locks` are **index-aligned in the oracle only** (`records[i].frame == locks[i].frame` 18951/18951);
`sim.ts` pushes a record only inside the clear branch, and twice on an all-clear bonus, so the
alignment holds **0 of 5472** times there and `records[i]` reads an unrelated record. Looked up by
the lock's own **frame**, the hand-port passes the strong check at that call site on every
comparable lock — **2019 of 2019** at seven sessions (the per-session figures are each session's
`locks_comparable`, so the artefacts cross-check it and this number tracks them), so
`dualVerdict` now uses the same reconstruction
check as the shipped path — the weaker licence is gone, and every artefact was byte-identical
under the change.

Two things that follow, and both are load-bearing:

- **The strong licence has no teeth from the artefacts.** Reverting to the index lookup or
  off-by-one-ing the frame collapses `locks_comparable` to 0 and byte-identity catches it; but
  weakening the *licence* (back to `rows.length == lk.cleared`, or comparing only the length of
  `clearedRows`) leaves every artefact byte-identical — re-checked on the sixth session, both
  mutants, rather than carried over. `dualVerdict` is exported and tested directly on synthetic
  boards for exactly that reason. A guard no gate can falsify is decorative.
- **A missing record is an EQUIVALENT mutant, not a coverage gap.** `?? []` instead of excluding it
  cannot change any output: a lock with `cleared > 0` always makes at least one row full, so an empty
  `theirs` never matches. The branch was also unreachable through the first six sessions (0 of
  2027). It is written
  explicitly because it states the intent — do not add a test that pretends to cover it.

## 開局定式 定 中盤手法 — the window was asserted, now it is measured

Three metrics answer "opener or mid-game" three different ways, and only one of them used to answer
it at all:

- **全消** always did: `pco_window_locks = 10`, `within_pco_window` per player, 3 of 95 inside it.
- **The ordering metric did NOT.** Its spins are filtered to lock ≤ `WINDOW_PIECES` before counting,
  so mid-game pairs were *excluded rather than counted*, and「先 Triple 後 Double」 was a claim about
  openings that a reader had no way to check — it reads identically to a claim about how these
  players throw T-spins at any point in a round, and the two mean completely different things about
  the C-Spin. `ordering.players[].mid_game` is the missing control. **Inside the window 528 rounds
  hold both spins and 527 run Triple-first — one exception in seven sessions, and it is a real DT
  Cannon (see above); outside it, 16 rounds hold both and the order goes BOTH ways (12
  Triple-first, 9 Double-first — a round can register both, so these do not sum to 16).** The rate of
  Double-first orders is orders of magnitude higher outside the window than inside it, so the
  window is doing real work — and the test asserts that ratio rather than a bare zero, which is
  what let the one genuine exception be recorded instead of absorbed.
- **Donation / STMB Cave** now carry `in_opener` / `mid_game` too. Donation splits about 1:2.3
  (39 in-opener, 88 mid-game), so it is not purely mid-game.

**The cave's window result was an absolute for six sessions and 2026-08-19 broke half of it. Read
the two halves apart — they are not one claim.**

- the **SHAPE** claim — "no ≥3-wide hit falls inside the opener window". Held 0 of 39 for six
  sessions. **BROKEN.** 08-19 has two, both in `replay-2026-08-19-9.ttrm`: round 4, pinglamb,
  lock 20, and round 5, yachi, lock 17 — width exactly 3, `minDepth` 1 each. Corpus-wide the
  width≥3 hits are now **49: 47 outside the window, 2 inside**.
- the **CAVE** claim — "no genuine cave falls inside the opener window". **UNBROKEN**, and it is
  the one the section's sentence rests on. Both hits are `minDepth` 1, i.e. dimples; 08-19's
  `min_depth_ge_2` is **0**; and the corpus still holds exactly **one** genuine cave in 900
  player-rounds, which is not in an opener. So harddrop's filing of the technique under
  `Mid-game T-Spin setups` is still a measurement and not a citation — what was lost is the right
  to state it as an absolute over the *raw width column*, which is the trap `width_ge_3` sets
  everywhere else in this file arriving from a new direction.

Neither hit is a short-prefix artefact: the two rounds verify to lock 62 and 64 against spins at
20 and 17. Both are pinned in `openers.test.ts` as `CAVE_IN_OPENER_EXCEPTIONS`, a **named exception
list** rather than a relaxed bound (following `DT_ORDER_IN_OPENER`), so a third one — or either of
these moving — fails and has to be investigated instead of absorbed. **What makes that a list and
not a bound in disguise is structural, and you can see it by reading the assertion**: it compares
each player's `in_opener` against *the number of entries naming that session and that player*, so a
phantom entry fails by construction (`known` exceeds a count the data does not support) and a
deleted real hit fails the same way from the other side. A bound — `in_opener <= 2` — would be
satisfied by any two in-opener hits anywhere in the corpus; this is satisfied only by these two.
Note what is deliberately *not* claimed here: nothing in the repo re-runs a mutation over this, so
the evidence is the shape of the assertion, not a mutation score. **The cave claim is now
enforced rather than commented**: a session
carrying an in-opener exception must have `min_depth_ge_2 === 0`, so the two claims can never be
separated by session without the test saying so. That the two hits share a file, sit in consecutive
rounds and take one player each is recorded **with no proposed mechanism** — two events are not a
pattern, and inventing a story for them is how a coincidence becomes a finding.

`ordering_full_round` is **not** the mid-game counterpart and must not be read as one — it applies
the *same* 21-piece window and only drops the verification requirement, so its numbers are within a
round of `ordering`'s rather than identical, which is the whole of what dropping verification buys:
**529 / 528 / 1** against `ordering`'s **528 / 527 / 1** (rounds with both · C-Spin order · DT order,
summed over the seven committed artefacts). One extra round clears the window unverified — the same
one round at seven sessions as at six, i.e. 08-19 added none. It answers "did the verified prefix
manufacture this", not "what happens later in the round" — and the answer being *one round*, not
zero, is what makes it evidence instead of a tautology.

**The mid-game denominator is 16 rounds corpus-wide, so it is printed as counts and never as a rate**
— rounds usually end before accumulating both spin types that late, and the verified prefix truncates
what is left. Same rule 全消 follows for its 3-12 round denominators; two of the seven sessions
(07-24, 08-01) have no such round at all, which renders as an absence rather than a zero.

New claim families go at the **end** of `generators.py`. `build_claims` numbers claims in FAMILIES
order, prose cites those ids, and a shifted id still resolves — to the wrong claim. Nothing checks
that.

**A new `SECTIONS` entry must also be placed in `skeleton.LAYOUT` or named in `SELF_INSERTING`,
and a CONDITIONAL section belongs in the latter.** `skeleton._check_coverage` refuses to emit
otherwise, which is how 2026-08-14 — the first session created after 全消 shipped — failed at step
6 of `bin/new-session` with `build_report.SECTIONS owns ['perfect-clear'] but LAYOUT does not place
it`. The fix is `SELF_INSERTING`, not `LAYOUT`: `generators.perfect_clears` emits nothing for a
session with no All Clear, so `pc_section.build` returns `None`, and an unconditional empty region
in the skeleton would then trip `render`'s stale-region guard on that session instead. Same shape
as `forecast` and `openers`.

A `SECTIONS` entry's anchor must be a **marker comment**, not a `<section id=…>` tag. `<section
id="coaching">` lives inside the coaching region, so anchoring there inserts the new block into a
span a later pass rewrites: `build_report` prints `inserted: <name>` and the finished file contains
nothing at all.

## Front-end traps in report.html (each one shipped a silent bug)

- **A generated section's `<style>` is injected into the body, so at equal specificity it beats
  the report's own stylesheet.** 全場之最 defined `.rec-grid` for its tile grid; 建議 had used
  `.rec-grid` for its two-column layout since long before, and the coaching columns silently
  collapsed into narrow auto-fit ones — the new section itself looked perfect, which is why
  eyeballing the section you just added does not cover this. Name generated classes with a
  section-specific prefix (`sr-`, `rt-`) and scope the rules under the section id.
  `pipeline/check_generated_css.py` is the gate: it fails any selector that could match an
  element outside its own region.
- `--accent` is defined **only** on `.match-card[data-winner=…]`. It resolves to an empty
  string everywhere else, which silently invalidates any `color-mix()` using it — that
  painted invisible bars and an unstyled card border. The round-table section carries its
  own `--rt-accent`.
- **Sticky cells must be fully opaque.** The player tints are translucent; a translucent
  sticky cell lets the scrolling columns show through, printing stat values on top of the
  pinned player name. Paint the tint as `background-image` over an opaque `background-color`.
- **`data-v` must be computed before any markup is wrapped around a cell value**, or the sort
  key becomes the markup — this broke sorting and the summary means on the four barred columns.
- Build the column-name→index map from **one** header row. Querying across all tables lets the
  last table's indices win, putting every lookup past the end of a row.
- Scores render in **player order** (`players[0] : players[1]`), never champion-first — that
  reversed the meaning on the site index once.
- **An unresolved badge is indistinguishable from a pending one.** `check_badge_links.py`
  is now the gate, and it reads `expandShorthandBadges`' regex out of the report rather
  than assuming one, because the failure was that regex being narrower than the prose.
  Both mutants are killed: a typo'd `data-claim`, and the expander narrowed back to
  `[CR]\d{3}`. It renders `⏳ G014` linked
  to an anchor that does not exist, which reads as "still being proved". Two ways that
  happened on 07-28, the first session whose prose cites generated claims: the claims island
  listed only the hand ledgers, and `expandShorthandBadges` matched `[CR]\d{3}` so `<b>G004</b>`
  in match-card copy stayed literal text. `appendix._rows` now includes every ledger the
  session's committed `claims-proof-map.json` covers — a rule that leaves 07-22 at 54 rows and
  07-24 at 52 while giving 07-28 all **96** — its `claims-proof-map.json` holds 96 entries, its
  appendix 96 data rows (`<tr>` in the region, less the header) and its island 96 claims, which is
  the rule holding exactly. It said 83 until 2026-08-17, and 83 was correct when written: the proof
  map held 83 entries that day. The rule is "every ledger the proof map covers", so its output
  tracks the map and a number written beside it does not — and `claim_cards.load` falls back to
  that map when a
  ledger has no `<stem>-proof-map.json` of its own, which is what made the round table's
  verdict cards show 待證 for claims the verifier had proved. Counting `.badge[data-status]`
  in the DOM does **not** catch either one; both were found by reading a screenshot.
- The `.ttrm` files are single-line JSON; `.gitattributes` marks them `-diff linguist-vendored`.

## 約 means the floored value — everywhere, and it is gated

`pipeline/fmt.py` floors; every generator uses it. Hand-written text is where a *rounded*
figure gets in, and it did: for weeks 約262.6 (C009/C010) and 約262.5 (G017) were the same
`vs_x1000 == 262582`, in one report. 45 figures across both sessions were rewritten on
2026-07-26 — Cantonese, `english_gloss` (which ships inside the claims island, so it is just
as published), and the prose typed straight into `report.html`.

`pipeline/check_prose_figures.py` is now the gate: it resolves every 約 / `~` / `≈` figure
against `facts.json` and fails when no datum *floors* to it but one *rounds* to it. Run it on
any session whose prose changed:

```bash
python3 -m pipeline.check_prose_figures sessions/<date>/report
```

Notes for future prose: a figure the checker cannot resolve is reported, not failed — sums and
differences legitimately print values no single datum produces. Figures in minutes are skipped
(a different divisor). `check_claims` will never catch this class, because every predicate
compares the integer, not the printed text.

**The gate used to skip the generated ledger, on the grounds that the generators floor by
construction. They did not.** Several families formatted the Cantonese with `_one_dp`/`_two_dp`
and the `english_gloss` with a bare `:.1f`, so one claim published 約167.9 and "VS 168.0" for
the same datum across all three sessions; the flat-rate family printed "差距唔夠 0.01 / under
0.01" for a bound its lemma only proved at 0.015 — a sentence strictly stronger than its proof.
Fixed 2026-07-28: every printed figure goes through a helper, and `_bound_dp` **ceils** because
an upper bound is the one figure that must round the other way. `check_prose_figures` now scans
every ledger, and its datum pool includes the derived quantities a generator can legitimately
print (per-round means, and the won/lost per-piece rates) — without them a correctly floored
rate resolves against no datum, collides with some unrelated datum's rounded rendering, and the
gate cries wolf at exactly the figures it just added.

## Perturbation is in place now, and that trade needs a guard

Two gates ask *"if I change this one datum, which claims flip?"* — `claims/equiv.py` 4 440
times per session (7 019 on 07-22) and `check_rate_coverage.py` up to 164 times. Both used
to answer it with `copy.deepcopy(facts)`, rebuilding a 300-480 KB object graph to write one
integer: 76.5 million deepcopy calls per `equiv` run, 88 % of its wall clock.

`pipeline/perturb.py` replaces that with **make/unmake** — write in place, evaluate, write
the old value back. Same mutants, O(1) instead of O(|facts|). `equiv` went 51.8 s → 13.9 s
on 07-22, output byte-identical.

**What it costs is the one thing deepcopy gave for free: the original cannot be corrupted.**
A sweep that restores 4 439 of 4 440 sites leaves every later mutant on a wrong baseline,
prints a plausible coverage figure and exits 0 — and for `check_rate_coverage` the drift is
in the direction that makes the gate *pass*, hiding a hole rather than inventing one. So
both callers fingerprint the tree either side of the sweep and assert it came back, and
`pipeline/test_perturb.sh` plants a disabled restore to prove that assertion fires. Do not
delete the fingerprint because it "obviously can't happen" — it is the only thing standing
where deepcopy's structure used to.

Preconditions, neither enforced at runtime: the code inside the `with` must not mutate
`facts` (both callers `eval` a pure comparison), and a write must name a container and key
that already exist.

`equiv.py`'s truth vectors are **bitmaps**, not lists — `defined` and `value`, one bit per
mutant, so three-valued logic survives (`defined ^ value` is "decided and False"). The
pair-coverage search is O(|hand| × |gen|²), which was 167 M interpreter steps in one
generator expression; as `&` over ~110 machine words it is free. `implies`, `==` and the
conjunction all changed representation — anything new that consumes a truth vector must go
through `Vec`, which is why the old list-shaped `truth_vector()` was deleted rather than
left for reuse.

**`check_dead_consts` tokenises once instead of searching per const** (9.1 s → 0.04 s, 206×).
It was `re.search(rf"\b{n}\b", body)` for each of ~4 700 names over ~600 KB. Aho-Corasick
(CACM 18(6), 1975) is the general answer, but every pattern here is `\b<word>\b` over `\w+`,
and `\b` *is* a token boundary — so a `set` of `re.findall(r"\w+", body)` gives the identical
answer in one pass. The hazard is that a tokeniser which is too generous prints exactly what
a clean run prints, so `--selftest` plants prefix and suffix substrings (`abc` against
`abcd`) that a naive containment check would wave through. It runs before the gate in CI.

**A profiler share is not a wall-clock share.** `cProfile` said deepcopy was 68 % of
`check_rate_coverage`; removing it gained 1.4×, because per-call instrumentation inflates
millions of tiny recursive `deepcopy` calls far more than it inflates one `eval`. Profile to
find *where* the time goes, then time the change to find out *how much*.

## Relevant skills

- `dataviz` (bundled) — its palette validator is authoritative: run
  `node scripts/validate_palette.js "<hex,hex>" --mode light|dark`. The yachi/pinglamb pair
  passes all six checks in both modes, so colour is not the thing to change.
- `html-skills:html-data-explorer` (installed from `f-labs-io/agent-html-skills`) — the round
  table follows its structure: row count, live summary, detail drawer, export, URL hash, plus
  its mandatory secret-scan-before-embedding rule.
- `web-artifacts-builder` is a **bad fit** here: it pulls React + Tailwind + shadcn (~150KB)
  for interactivity already delivered by ~20KB of vanilla JS, and the reports are deliberately
  single-file with zero external requests.

## Known remaining work

1. One `innerHTML` assignment left in `report.html`, and it is the legitimate one: the
   match-card body expands authored prose carrying badge shorthand (`<b>C001</b>`). The other
   two are gone — the match-card score builds nodes, and the appendix row builder was deleted
   with the section it served. Re-verify after touching anything near them by running the gate —
   `python3 -m pipeline.check_badge_links sessions/<date>/report` — which resolves every citation
   against the claims island and prints its own counts. **Not by comparing a badge count**: the
   "110" that used to sit here matched no report on any measure, and there are two measures that
   disagree by design. `data-claim` *occurrences* in the document run 77 / 88 / 96 / 111 / 119 / 119
   over the first six sessions — 08-19 is not on that list because its prose is still being written,
   which is exactly why the list is not the instruction
   (`grep -o 'data-claim=' report.html | wc -l`; `grep -c` counts lines, and
   this file puts many on one). The gate counts **distinct cited ids** and prints 43 / 40 / 49 / 55 /
   56 / 57 badge plus 20 / 23 / 27 / 33 / 31 / 48 shorthand `<b>C001</b>` citations — lower because a
   claim cited three times is one id. No single number was ever right for more than one session, so
   the instruction is to re-run the gate, not to match a figure. The appendix's 54 / 52 rows for
   07-22 / 07-24 do check out (`<tr>` inside the appendix region, less its header).
2. ROADMAP P5. **The report body is fully generated** (`pipeline/build_report.py`,
   CI-gated with `--check`): hero/scoreboard, 戰況, 數據對決, 關鍵時刻, 全場之最, 建議, the
   appendix, and the `chart-data`, `match-copy` and `claims-data` islands, plus the round
   table from its own generator. That sentence was first written while 戰況 was still
   hand-written — it had been checked by counting `SECTIONS` entries rather than by
   scanning the document. `pipeline/check_report_shell.py` now scans the document, so the
   claim is enforced instead of asserted.

   **P5 is done.** `bin/new-session` emits the report too (`pipeline/skeleton.py`): raw
   replays in, a complete rendering report out, with every generated region filled and
   TODO prose files to write into. A session no longer starts by copying the previous
   one's report.html — which is what had been silently propagating stale constants
   between sessions. Step 6 never touches an existing report.html.

   What a person still writes by hand: the five `prose/*.json` files, `narrative-beats.md`
   / `recommendations.md`, `hand_claims.py`, and the `<title>` — the only string in the
   document no generator owns.

   **Nothing in the pipeline is bound to the players' names any more.** The last one was
   `build_round_table.py`, whose `tr[data-who="yachi"]` bar-tint and filter rules matched
   nothing for any other pair — the bars fell back to grey `--muted` and no gate noticed,
   because the table still rendered. Those four rules are derived per session now
   (`player_css`), and the filter classes are positional `f-p1` / `f-p2`. The colour
   tokens stay `--yachi` / `--pinglamb`: the shell defines them as aliases of `--p1` /
   `--p2`, and pointing at the slots directly would break the four committed reports whose
   `:root` predates the aliases — the `--accent` trap again. `report.html` carries the shell and marker pairs, nothing
   else. What remains of P5 is the skeleton, so `bin/new-session` emits a report instead of
   expecting one copied from the previous session.

   **Moving prose into a file can narrow a checker.** `check_prose_figures` enumerated
   `hero.json` and `matches.json` by name, so lifting 關鍵時刻 into `prose/moments.json`
   took its figures out of the scan — the region left behind is generated and therefore
   skipped, and the new file was on nobody's list. The count went 102 → 98 and nothing
   said so. It now walks `prose/*.json` and every string leaf in them, which also picked
   up fields nobody had enumerated. When adding a prose file, check the figure count goes
   UP. Add each as a new entry in `SECTIONS`; the marker region and the
   drift gate come for free.

   A `SECTIONS` entry may keep pre-existing markers instead of the standard pair — the
   `claims-data` island does, because things locate it by those comments (`check_prose_figures`
   skips it by them).

   A section that cites claims uses `pipeline/claim_cards.py` — one loader for ledger + proof
   map, so every section agrees on what "verified" means. `round_operand()` reads a figure out
   of the claim's own spec (the operands of the proved equality) rather than re-deriving it
   from `facts.json`; a spec of another shape returns None so the section skips the claim
   instead of inventing a number. Number formatting lives in `pipeline/fmt.py` and **floors**,
   because 約 has to mean "at least this much" everywhere.

   The split every section follows: numbers from `facts.json`, words from
   `<report_dir>/prose/*.json`. Prose is inserted as raw HTML because it legitimately contains
   `<span class="hl-y">` and badge spans — derived values are escaped, prose is trusted, and
   each loader runs the same simplified-glyph check as the claim generator.

   Editorial constants belong in prose, not in the script: `hero_match` (which card gets the
   spotlight) and `score_claim` (the badge on every card's score) were `m.index === 7` and a
   literal `data-claim="C026"` inside each report's inline JS, which is a large part of why the
   script could not be shared between sessions.

   **The inline script is still player-hardcoded** — ~110 occurrences of `yachi`/`pinglamb` in
   colours, keys and labels. The card renderer and the small multiples now read `CD.players`
   by position; the rest is the report-skeleton step's job, not something to chip at.
3. `sessions/2026-07-24/proof/` is a *second, lighter* report with its own 20-claim proof layer.
   It is a cross-check, not a published report — every fact in it is covered by that session's
   full report. Keep it gated by CI; do not resurrect it onto the site.

   **What made it a cross-check was unenforced until 2026-08-16.** `bin/verify-session` takes ONE
   artefact directory and every gate it runs is internal to that directory, so `proof/` and
   `report/` both went green while describing the same night differently — and the only thing
   keeping them together was somebody remembering to re-extract `proof/` whenever `report/` moved
   (most recently for the apm/pps/vs change on 2026-08-15; it was remembered, and nothing would
   have said so otherwise). `pipeline/check_cross_artefact.py` is the gate: 6 012 shared values,
   globbed over `sessions/*` so a second artefact anywhere is covered without an edit, and no pair
   at all is a failure rather than a quiet pass. The two schemas genuinely differ — `report/`
   carries 30 per-player fields `proof/` never had — so the gate **names** every uncompared field
   instead of silently intersecting, and separates a FIELD on one side only (tolerated, named)
   from a RECORD on one side only (a missing match, round, player or garbage event — a failure).

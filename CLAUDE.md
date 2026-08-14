# tetrio-replay-report — operating context

Public repo: <https://github.com/yachi/tetrio-replay-report> · Site: <https://yachi.github.io/tetrio-replay-report/>

Turns a batch of TETR.IO `.ttrm` replays into a Cantonese match report where every
factual sentence is badge-linked to a Dafny-verified lemma. Five sessions so far
(2026-07-22: yachi 6:4 · 2026-07-24: pinglamb 4:3 · 2026-07-28: pinglamb 6:2 ·
2026-08-01: yachi 4:3 · 2026-08-09: pinglamb 6:0), 296 rounds, 144 hand-written +
380 generated claims.

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
python3 spec/check_spec_vacuity.py         # no lemma in the spec is vacuously true
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
| 2026-07-22 · 77 generated claims | ~4.6 s (54 hand claims) | **40 ms** |
| 2026-07-24 · 76 generated claims | ~3 s (52 hand claims) | **10 ms** |

That speed is what makes the anti-vacuity mutation test affordable on every push
(`--mutate 12` finishes in under a second) rather than weekly. `claims.smt2` is committed and
byte-identity gated, so it doubles as a portable artefact: any SMT-LIB solver can re-check the
claims without this pipeline.

The `.smt2` covers every **spec-carrying** ledger. For 07-22 and 07-24 that is the generated
one only — their hand ledgers predate the spec algebra, carry a bare `python_check`, and are
proved by a session-local ~500-line `codegen_dafny.py`. From 2026-07-28 on, hand claims are
written as **specs** in `sessions/<date>/report/hand_claims.py` and built with
`pipeline.claims.build_hand`, so they render to all three backends and need no per-session
emitter: `--claims` on `codegen`, `codegen_smt` and `build_proof_map` takes several ledgers,
`pipeline.codegen.session_ledgers` defines their canonical order, and `check_smt` **names**
any ledger it had to leave out rather than silently narrowing what the artefact covers.

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
the downloaded bytes before use. z3 is *not* in CI because recent z3 releases only ship
`x64-glibc-2.39` builds, which cannot run on the `ubuntu-22.04` runner the Dafny step pins
(glibc 2.35); z3 ≤ 4.14.1 has 2.35 builds but GitHub reports no digest for those assets. So the
split is z3 locally, cvc5 in CI, both over the same committed artefact.

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

## What the data actually says (measured, not asserted)

Paired AUC over 129 rounds — how often the round's winner held the higher value:

- **Strong**: VS 100% · APM 94.6 · 攻 93.8 · APP 91.5 · 送 88.0 · 射埋 12.0 (88 inverted) ·
  食 14.3 · 分 85.3
- **No signal**: COMBO 45.0 · PC 50.8 (89% zeros) · TST 55.8 · TSD 60.9 · KPP 39.9
- Near-constant (CV 0.05): KPP, FIN% — their flatness is the finding, not a column of numbers

2026-07-28 (64 rounds) reproduces all of it independently: VS 100% · APP 96.9 · APM 95.3 ·
攻 93.8 · DS 75.0 · 食 12.5 · 射埋 14.1 — and **KPP 42.2**, below chance for a third time.

2026-08-01 (53 rounds) is the fourth independent reproduction: VS 100% · 攻 90.6 · APM 90.6 ·
APP 83.0 · 食/射埋 15.1 — **DS 84.0, the highest of any session** (66.5 · 60.0 · 75.0 · 84.0
across the four) — and **KPP 53.8**, i.e. chance, for a fourth time.

2026-08-09 (50 rounds) is the fifth: VS 100% · 攻 94.0 · APM 94.0 · APP 88.0 · 分 86.0 ·
食 20.0 · 射埋 23.0 · DS 66.0 — and **KPP 58.0**, i.e. chance from the other side, for a fifth
time. DS is the per-*piece* variant throughout (raw `garbage_cleared` gives 68.4 · 62.0 · 81.2 ·
83.0 · 64.0 and is a different series); the 129-round headline block above is 07-22 and 07-24
pooled, not one session.

Coaching conclusions, cross-validated over five sessions: **APP is the lever** (16–52% higher
in rounds won, both players, 10 of 10 player-sessions); **DS matters** in 9 of 10 player-sessions
(only 07-24 pinglamb is negative); **KPP is flat** (0–3%) — reported as a negative result. When
adding a column or a claim, run `pipeline/claims/equiv.py` or the AUC probe rather than
assuming a stat is informative.

**08-09 splits APP the other way, and that is the finding of the fifth session.** Every earlier
session had one player ahead in *both* regimes by a similar margin — a style difference. Pool
attack over pieces after splitting the 50 rounds by who won them and the two regimes come
apart: won .6738 vs .6862 (+1.8%), lost .5124 vs .6425 (+25.4%) [C002]. yachi's won-round rate
is above pinglamb's *lost*-round rate [C003]. The rank test says this is not a variance
artefact — over losing rounds P(yachi > pinglamb) = 0.138, permutation p = 1e-5; over winning
rounds 0.464, p = 0.34 — and it survives dropping the three near-zero rounds. The per-session
won-gap runs +5.8 · +10.8 · +5.9 · +7.9 · **+1.8**, the lost-gap +12.8 · +7.3 · +6.0 · +6.1 ·
**+25.4**. Two consequences worth knowing before writing another report:

- **The volume route is not a law.** 08-01's headline was that 326 extra pieces bought back a
  7% efficiency gap to within 32 lines. 08-09 ran the same route into 382 extra pieces and
  **271 fewer** lines of attack, 8%+ of pinglamb's total [C004] — because buying it back
  requires the per-piece value not to collapse, and here it collapsed on one side only.
- **Advice taken can leave the score wider.** 08-01 flagged that 6 of 8 topouts were yachi's.
  08-09 has 4 topouts, all pinglamb's, yachi none [C006] — and the match score went 4:3 to 0:6.
  A metric moving the right way is not the same as the metric that decides.

**`equiv.py` reports 100% for 07-28 and the number is an artefact** — read it before quoting
it. It tries every *single*-value mutation, and a windowed claim shares its rounds with a
session total, so nothing it can try falsifies one without the other. Two changes break the
tie: moving 120 pieces from a match-3 round to a match-1 round keeps `total_pieces`,
`total_garbage_attack` and C008 true while flipping C005 false. Extending it to
value-preserving two-site moves is the obvious next step and is not done.

07-28's own finding is about *change over a night*, which no earlier session asked: yachi won
the first two matches and lost six straight, but his rate did not collapse — in matches 1-2 the
two players' APP were level (0.62305 vs 0.62216, yachi ahead by 0.0009) and from match 3 they
separated, pinglamb +4.99% and yachi −4.92%. Both totals are nearly equal (attack 3264 vs 3249)
because yachi threw 378 more pieces to get there. That is what `sum_round_range` exists for.

08-01 asks the next question down: **APP decides a round, and it does not decide a night.**
pinglamb's APP was higher in all seven matches and in both regimes — his won rounds beat
yachi's won rounds, his lost rounds beat yachi's lost rounds — yet he lost the series 3:4. The
totals land on top of each other (attack 3394 vs 3426, in-game score 1087345 vs 1087921, 0.05%
apart) because yachi bought the 7% efficiency gap back with 326 extra pieces at a higher PPS
in all seven matches. Two routes, one destination; the night was then decided by *which* rounds
fell where — the seven matches alternate winners perfectly, so it came down to the last one.
Same window operator, per-match windows this time: `sum_round_range(pl, f, mi, mi+1)` is how
"in all seven matches" gets proved match by match instead of asserted from a session sum.
The visible cost of the volume route is in the death tally: 6 of the 8 topouts are yachi's.

## 速率紀錄要有局長下限 — and the two holes cutting one opens

For three sessions the APM/VS records were the plain argmax and were **all** short-round
artifacts. A rate has the round's length in its denominator, so over a short round it is a
sample mean over a small n. Measured in `analysis/rate_records.R` over all 592 player-rounds:
regressing log SD on log t gives **−0.648 for VS and −0.726 for APM**, both with −0.5 inside
the 95% CI and slope 0 rejected (p 0.0006 / 0.0002), while the **mean stays flat** (100 → 119
across the bins). Short rounds are not better play, only noisier. All 15 unqualified records
(3 metrics × 5 sessions) came from the shortest quartile — p = 9e-10 — and 07-22's headline
約262.6 was a 15.6 s round, 45% above that session's qualified peak.

The script's session list is hardcoded, so **adding a session means editing it and re-running**
— otherwise the evidence for `QUALIFYING_MS` silently stops covering the newest data. Adding
08-09 also broke it: the records test carried a literal `12` for "3 metrics × 4 sessions", and
`binom.test(15, 12, ...)` aborts. It derives `n_records` from `sessions` now.

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
  the whole simulated round so the short verified prefix cannot manufacture the result. Five
  sessions: 221 of 221 run the C-Spin order, 0 the DT order; unwindowed, 277 of 277.
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
that keeps I on hold. Pre-existing blocks re-emit byte-identical on all five sessions.

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

The repertoires split, reproduced independently in all five sessions (pinned in `openers.test.ts`):
**pinglamb opens Honey Cup** (17-25 exact per session vs yachi's 6-11), **yachi opens Mountainous
Stacking** (11-25 vs 2-11) **and is the only one who plays TKI-3 at all** (5-8; pinglamb 0, every
session). PCO appears only for yachi, only on 07-24 and 08-01.

**PCO's payoff is bounded by facts.json, and its timing is the one simulator figure with a verified
counterpart.** PCO is defined by an outcome, so the row splits in two. HOW MANY perfect clears is
`clears.allclear`, twice-extracted — see 全消 below. WHEN each landed only the simulator can say, and
what licenses printing it is that `perfect_clear_timing` compares the simulator's per-round count
with the replay's own counter for **every** player-round and emits the piece numbers as `null` unless
all of them agree. They do: **592/592 rounds, 65/65 perfect clears**, five sessions. `check_opener_
section` fails if the piece numbers are published without that agreement figure or without
harddrop's ten-piece deadline beside them.

The finding is that **3 of the 65 arrived inside that deadline** and 53 landed on piece 20 — these
are mid-game perfect clears, not the opener. 08-01 holds the corpus's only completed PCO: yachi
matched the field twice and delivered once.

**An earlier revision of this section said the opposite** — that `eng.board.perfectClear` invented
clears the sessions did not have — and it was wrong for a reason worth keeping: the facts.json
lookup it rested on read `players[u].allclear`, one level above the counter, and `?? 0` turned every
undefined into a plausible zero. All five reports published 「一個 Perfect Clear 都冇出過」 while the
`.ttrm` files held 65. Nothing caught it: the value was in range, the artefact re-emitted
byte-identically, and the test recomputed the total down the same wrong path, so it agreed with
itself. Two rules came out of it — **a required field that goes missing must throw, never default**
(`sessionPerfectClears` declares `clears.allclear` non-optional and dies on a non-number), and **a
test that re-derives a value the way the code does can only catch a typo** (`openers.test.ts` now
pins the five sessions' counts as literals and asserts the total is not zero).

## 全消 — the Perfect Clear section, and the two questions it keeps apart

`pipeline/pc_section.py`, region `perfect-clear`, **inside** the trust chain: every figure is read
out of the proved claims' own specs (`pc_rounds`, `pc_solo_lost`, `clears_allclear`), never
re-derived from facts.json, so the table cannot print a number no lemma covers. `clears.allclear` is
read out of the `.ttrm` independently by both extractors, which is why this one is badged while the
opener tables are not.

The point is not the count. Across five sessions, **60 rounds had exactly one player with a perfect
clear and that player lost 28 of them** — the AUC block above says the same thing (PC 50.8, 89%
zeros). So the section prints "rounds won" beside "rounds with one" and refuses to print a rate: the
denominators are 3-12 rounds per player, and a percentage over three rounds reads far more confident
than the data is. Two more controls it may not lose: 全消次數 ≠ 有全消嘅局 (a round can hold two), and
"whether" is facts.json while "when" is the simulator's, in the quarantined section below.

## 捐窿 同 STMB Cave — two techniques that are not openers, and the arithmetic trap under one

`pipeline/openers/wiki-tspin-techniques.json` → tables five and six of the quarantined section.
Same tier as slot geometry: a **per-T-spin board-state predicate over the whole round**, scored on
the verified prefix, no claim ids and no badges.

**Neither page is an opener, and reading them as openers is the first mistake available.** harddrop
files both under `T-Spin techniques / Mid-game T-Spin setups`; their diagrams are 24-112 cells drawn
on partial stacks, so a 24- or 28-cell opening board can never equal one. Putting them in the
六個具名定式 table would have printed a column of zeros meaning "never compared" while reading as
"these players never do this" — the same shape as the `OPENER_LOCKS` coverage bug.

**The naive Donation predicate is forced by arithmetic, and it fires on 70-89% of T-spin clears.**
"The well column is filled through the rows the spin cleared" cannot fail: a full row *requires*
every column filled, so that clause counts line clears. All the discriminating power is in the
**re-opening** clause — every filled cell of the column must lie inside the cleared rows, so the
clear leaves it open surface-to-floor. With it, the rate drops to ~2.5% (82 across five sessions).
`D = 4` and "walled at the **deepest** 4 cavity rows" are harddrop's numbers, not tuned: of its 20
named setups 17 draw a four-cell cavity and 3 draw five, never three or six; and requiring *every*
cavity row to be walled drops TSS L Donation, which the page draws as a donation.

**Every donation in this corpus sits on a garbage-derived well — 0 self-built, all five sessions.**
The oracle keeps the engine's own seeded-RNG garbage hole *columns*, which disagree with the
ige-recorded ones 97 of 103 times (`oracle-source.ts`), so the count says the board offered the
shape that often and can never say which column was donated into. The check that finds this must
read the row's **filled** cells for the `-1` garbage sentinel: the well cell is empty by
construction and carries `null`, so testing it directly is a guard nothing can fire — that exact
bug reported every well as self-built for a whole round of measurement.

**The STMB cave is OFFSET from the T and its roof test is vacuous.** The cave shares two of the T's
three columns and reaches one past them, so the test is *overlap*, never containment — containment
misses all six drawn Basic Structures. And the cave's roof is the nub row the Double just
completed, which roofs everything beneath it by definition: measured, **0 unroofed runs in 1914**.
A roof test would have been a decorative guard.

Two cross-tabs, and the section may print neither number without both: **by depth**, 29 of the 30
width≥3 hits are one row deep — a dimple, not a cave — leaving exactly **1 genuine cave in 592
player-rounds**; **by lines**, the same gap appears under T-spin Triples at a *higher* rate (9.0%
vs 1.7% on 08-09), where it is ordinary TST residue. A shape that fires more often under the spin
the technique is not about is a shape test.

**The class control is the article's own comparison list, not a category.** harddrop has no
"floating T-spin" category; `Mid-game T-Spin setups` (63 pages) is a *when*, not a shape, and
`Back-to-Back T-Spin setups` (38) does not even contain STMB Cave. The page itself says the cave
"is just Sky Prop but with 3 columns wide hole" and that a variant "has the same shape and steps as
Shachiku Train", so the metric names a **class** — the same move the `Triple Double openers`
category makes for the ordering metric. All three category counts are recorded as evidence.

Both metrics are licensed by one check: the per-lock board snapshot plus the lock's cells must make
exactly the rows full that the engine independently recorded clearing. Different state, so it is a
real gate — **3142/3142 across five sessions**, and a spin it cannot reconstruct is dropped, never
scored. (This line read **3379/3379** until 2026-08-14. 3379 is the corpus's *whole-round* T-spin
clear total; the check is scoped to the verified prefix and has always been 3142. The figure was
written from a whole-round probe and matched no committed artefact — `donation.check.tspin_clears`
sums to 3142 in the five `opener-facts.json`. Nothing caught it because CLAUDE.md is prose: a gate
figure quoted here is not the gate.)

### 分母錨咗 replay 自己數嘅 counter — the one part of this section that is not simulator-only

The reconstruction check above is *internal*: two states the same engine built separately. It says
the boards are coherent; it cannot say the engine counts T-spins the way the game does. That
question has an outside witness — `results.stats.clears.tspindoubles` and its seven siblings, which
`extract.py` and `extract2.ts` each read into facts.json as `tspin_doubles` etc. **Both extractors
agree on them, so they are inside the trust chain**, and `tspinCounterCheck` compares them per
player-round, per kind, over the whole round:

| | |
|---|---|
| rounds where every kind agrees | **592 / 592** (five sessions, no unknowns) |
| whole-round T-spin clears, sim vs replay | **3379 = 3379** |
| what the verified prefix scores of them | **3142**, i.e. **93.0%** coverage |

So the two tables' **denominator** leaves quarantine: `tspin_clears_scored` is now a subset of a
total the trust chain already carries, and 「可核覆蓋」 names the subset. This is the
`perfect_clear_timing` pattern (592/592 against `clears.allclear`) applied to a denominator instead
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

**The other route into the chain is a second engine, and it is measured but not taken.** Both engines
already exist — the hand-port `runCase` and the vendored Triangle `runCaseOracle`. Scored lock by
lock over the prefix where both verify (1346 comparable T-spin clears), they agree on **lines
1346/1346**, on **cave 1346/1346**, and on **donation 1301/1346 (96.7%)**. So the cave metric is a
real candidate for dual-implementation membership; donation is not, and the 45 disagreements sit
where the documented garbage-hole-column problem is. Not shipped — the probe is the finding.

A false start worth not repeating: the first version of that probe pushed both engines through the
reconstruction check and the hand-port licensed **0 of 1355**. A 0%/100% split is a bug report about
the comparison, not a result — `records[].clearedRows` does not mean the same thing in the two
engines (the hand-port leaves it empty on most clearing locks), while its board is fine. Compare the
**metric**, from each engine's own pre-lock board plus its own T cells.

## 開局定式 定 中盤手法 — the window was asserted, now it is measured

Three metrics answer "opener or mid-game" three different ways, and only one of them used to answer
it at all:

- **全消** always did: `pco_window_locks = 10`, `within_pco_window` per player, 3 of 65 inside it.
- **The ordering metric did NOT.** Its spins are filtered to lock ≤ `WINDOW_PIECES` before counting,
  so mid-game pairs were *excluded rather than counted*, and「先 Triple 後 Double」 was a claim about
  openings that a reader had no way to check — it reads identically to a claim about how these
  players throw T-spins at any point in a round, and the two mean completely different things about
  the C-Spin. `ordering.players[].mid_game` is the missing control. **Inside the window 354 rounds
  hold both spins and 354 run Triple-first, zero exceptions; outside it, 9 rounds hold both and the
  order goes BOTH ways (7 Triple-first, 5 Double-first).** So the window is doing real work.
- **Donation / STMB Cave** now carry `in_opener` / `mid_game` too. The cave's is the cleanest result
  in the section: **0 of 30 fall inside the opener window, in every session** — which turns
  harddrop's filing of it under `Mid-game T-Spin setups` from a citation into a measurement.
  Donation splits about 1:3 (23 in-opener, 59 mid-game), so it is not purely mid-game.

`ordering_full_round` is **not** the mid-game counterpart and must not be read as one — it applies
the *same* 21-piece window and only drops the verification requirement, which is why its numbers are
identical to `ordering`'s. It answers "did the verified prefix manufacture this", not "what happens
later in the round".

**The mid-game denominator is 9 rounds corpus-wide, so it is printed as counts and never as a rate**
— rounds usually end before accumulating both spin types that late, and the verified prefix truncates
what is left. Same rule 全消 follows for its 3-12 round denominators; two of the five sessions have
no such round at all, which renders as an absence rather than a zero.

New claim families go at the **end** of `generators.py`. `build_claims` numbers claims in FAMILIES
order, prose cites those ids, and a shifted id still resolves — to the wrong claim. Nothing checks
that.

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
  07-24 at 52 while giving 07-28 all 83 — and `claim_cards.load` falls back to that map when a
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
   with the section it served. Re-verify the 110 badge count and 54/52 appendix rows after
   touching anything near them.
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

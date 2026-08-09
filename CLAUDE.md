# tetrio-replay-report — operating context

Public repo: <https://github.com/yachi/tetrio-replay-report> · Site: <https://yachi.github.io/tetrio-replay-report/>

Turns a batch of TETR.IO `.ttrm` replays into a Cantonese match report where every
factual sentence is badge-linked to a Dafny-verified lemma. Four sessions so far
(2026-07-22: yachi 6:4 · 2026-07-24: pinglamb 4:3 · 2026-07-28: pinglamb 6:2 ·
2026-08-01: yachi 4:3), 246 rounds, 132 hand-written + 304 generated claims.

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
Rscript analysis/rate_records.R                                 # the evidence for QUALIFYING_MS
dafny verify spec/Forecast.dfy spec/ForecastExamples.dfy       # the hand-written concept spec
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

Coaching conclusions, cross-validated over four sessions: **APP is the lever** (16–25% higher
in rounds won, both players, 8 of 8 player-sessions); **DS matters** in 7 of 8 player-sessions
(only 07-24 pinglamb is negative); **KPP is flat** (0–2%) — reported as a negative result. When
adding a column or a claim, run `pipeline/claims/equiv.py` or the AUC probe rather than
assuming a stat is informative.

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
sample mean over a small n. Measured in `analysis/rate_records.R` over all 492 player-rounds:
regressing log SD on log t gives **−0.616 for VS and −0.697 for APM**, both with −0.5 inside
the 95% CI and slope 0 rejected (p 0.001 / 0.0003), while the **mean stays flat** (108 → 118
across the bins). Short rounds are not better play, only noisier. All 12 unqualified records
(3 metrics × 4 sessions) came from the shortest quartile — p = 6e-08 — and 07-22's headline
約262.6 was a 15.6 s round, 45% above that session's qualified peak.

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

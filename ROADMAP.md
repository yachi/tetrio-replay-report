# Plan: `tetrio-replay-report` — a repo that turns a batch of .ttrm replays into a proof-backed Cantonese report

Decisions locked: **public repo**, **everything included** (replays + reports + full pipeline), goal = **repeatable: drop in a batch of replays → get a report**.

## 0. What the repo is

Not an archive with two reports in it. A **tool** (`pipeline/`) plus **data** (`sessions/`), where adding a session is one command plus an optional prose pass.

```
tetrio-replay-report/
├── README.md                  # what it is, honest trust chain, how to run
├── LICENSE                    # MIT for code (data note in README)
├── .gitattributes             # *.ttrm linguist-vendored + -diff (65k-char single-line JSON)
├── .gitignore                 # .playwright-cli/ __pycache__/ .playwright/ shots/ *.zip
├── pipeline/
│   ├── extract.py             # extractor A (python)      — parameterized by session dir
│   ├── extract2.ts            # extractor B (typescript)  — independent impl, diff gate
│   ├── claims/
│   │   ├── generators.py      # ~20 claim FAMILIES (the core new work — see §2)
│   │   ├── dafny_lib.py       # generic emitters harvested from codegen_dafny.py
│   │   └── build_claims.py    # facts.json → claims.json (canto + python_check + dafny body)
│   ├── codegen_dafny.py       # claims.json → Facts.dfy + Claims.dfy   (already data-driven)
│   ├── check_claims.py        # python_check gate
│   ├── build_proof_map.py     # verifier output → proof map (never aspirational)
│   ├── build_report.py        # facts + claims + proof map + prose → report.html
│   ├── templates/             # design system, SVG chart renderers, appendix (from session-1/2 HTML)
│   ├── mutation_test.sh       # anti-vacuity gate
│   └── gen_consistency.sh     # codegen byte-identity gate
├── sessions/
│   ├── 2026-07-22/  replays/*.ttrm  facts.json  claims.json  dafny/  prose/  report.html
│   └── 2026-07-24/  (same shape; also keeps the lighter report-2026-07-24.html)
├── tools/analyzer.html        # standalone drop-a-.ttrm analyzer (client-side)
├── docs/                      # GitHub Pages: index + one page per session report
├── bin/new-session            # the one command (see §3)
└── .github/workflows/verify.yml   # CI re-runs every gate on push (SHA-pinned actions)
```

## 1. Reuse audit (measured, not assumed)

| Component | Today | Repo |
|---|---|---|
| `extract.py` / `extract2.ts` | filename glob hardcoded per session | parameterize input dir + ordering rule → **reuse as-is** |
| `check_claims.py` | already generic (argv) | **reuse unchanged** |
| `codegen_dafny.py` Facts emitter + helper lib | generic (`bal`, `sum_rf`, `sumsq_rf`, `max_pp_is`, `rmin_is`, `rmax_is`, `lb_max_is`, `variance`, `count_expr`) | **promote to `dafny_lib.py`** |
| `codegen_dafny.py` claim bodies | **hand-written `bC001…bR024` per session** ← the bottleneck | replaced by generators (§2) |
| Claim text + predicates | hand-written by 2 opus agents per session | auto-generated for ~85%, agents add flavor |
| `mutation_test.sh` / `gen_consistency.sh` / `build_proof_map.py` | near-generic | parameterize paths → **reuse** |
| report HTML | prose+layout hand-built per session | split: auto layer (scoreboard, match cards, charts, appendix) + prose layer |

## 2. Core work: claim generators (the thing that makes it repeatable)

One generator = one claim family = works on every future session. Each emits all three artifacts so nothing is hand-written downstream:

```python
class Generator:
    def find(facts) -> list[Params]      # locate the instances in THIS session (argmax, streak scan, …)
    def canto(p)   -> str                # 口語廣東話 sentence, with 約 + floor convention applied
    def check(p)   -> str                # python_check expression (integer-only)
    def dafny(p)   -> str                # lemma body via dafny_lib helpers
```

Families harvested from the 52 existing claims (each already proven twice):

**Structural / score** — series result; round-win totals; per-match final scores; sweeps (5-0) and who owns them; deciders (full-length matches); match-win order.
**Superlatives** — session-max single-round APM / VS / spike / combo / B2B / T-spins; longest & shortest round; highest match-level APM; per-player maxima. (`max_pp_is` / `rmin_is` / `lb_max_is` already exist.)
**Streaks** — longest consecutive round-win run, with the cross-match-boundary disclosure baked into the wording (session-2 review finding, now permanent).
**Pressure / comeback** — rounds won while facing more queued attack; queued-vs-materialized cancellation totals (semantics enforced in wording, not left to a writer).
**Player aggregates** — totals & per-piece rates for attack, quads, T-spin subtypes, all-clears, holds, finesse faults/perfects, inputs; kills.
**Consistency** — integer variance identity `n·Σx² − (Σx)²` comparisons (already integer-only).
**Situational** — fast-round (<40s) records, high-APM-round records, bounce-back-after-loss rates, sweep-match collapse stats.

Guardrails encoded once, so past bugs cannot recur:
- floor convention for 「約N秒」 (session-2 minor m5)
- streak wording must disclose match boundaries (session-2 minor m2)
- queued vs materialized garbage phrasing (session-1 recurring)
- no simplified glyphs in generated text (assert on output)
- kills ≡ round wins in 1v1 — never presented as independent corroboration (session-2 minor m3)

**Validation gate for this refactor:** regenerate both existing sessions with the generators and diff against the committed hand-made ledgers. Target ≥85% of the 52 claims reproduced with an equivalent predicate; the remainder stay as per-session bespoke entries. This is the phase's acceptance test — no hand-waving.

## 3. The one command

```fish
bin/new-session sessions/2026-08-01 ~/Downloads/replay-batch/
```
Runs, failing loudly at the first bad gate:
1. copy/normalize replays → `sessions/<id>/replays/`
2. both extractors → `facts.json` + `facts2.json`, **diff gate**
3. `build_claims.py` → `claims.json` (auto families) + `check_claims.py` **100% gate**
4. `codegen_dafny.py` → `dafny/*.dfy`; `dafny verify` **0-errors gate**; `mutation_test.sh` **all-killed gate**; `gen_consistency.sh` **byte-identity gate**
5. `build_proof_map.py` → statuses from real verifier output only
6. `build_report.py` → `report.html` with charts, scoreboard, match cards, 52-row appendix — prose sections marked `TODO`
7. print a summary table + the paths

Then the optional prose pass (Claude Code, the phase that genuinely needs judgment): narrative beats + coaching recommendations written against the auto claims, re-run `build_report.py`. The adversarial audit prompt ships in the repo as `docs/AUDIT-PROMPT.md` so the review loop is reproducible too.

## 4. CI + Pages

- `.github/workflows/verify.yml`: on push/PR — install Dafny, then re-run for every session: extractor diff → `check_claims` → `dafny verify` → mutation test → consistency. **The repo's central claim is "these numbers are proven"; CI is what keeps that true.** Actions SHA-pinned.
- GitHub Pages from `docs/`: index listing sessions (date, players, result) → each report + the analyzer tool. Reports are already self-contained, so publishing is a copy.
- Badge in README: verification workflow status.

## 5. Migration of existing work

Both sessions land intact, then get re-verified through the new pipeline (their committed reports stay as-is; only the tooling path changes). Excluded from git: `.playwright-cli/`, `__pycache__/`, `.playwright/`, `proof/shots/`, `*.zip` (~11 MB of QA screenshots). Payload ≈ **17 MB / 83 files** — comfortable.

Session-2's `proof/` (the lighter 20-claim report and its Dafny layer) moves under `sessions/2026-07-24/` as a second artifact rather than being deleted.

## 6. Phasing

| Phase | Output | Ships when |
|---|---|---|
| P1 | Repo created, both sessions + reports + existing scripts committed, README, .gitignore/.gitattributes, Pages live | immediately usable as an archive |
| P2 | CI green: every gate re-runs on push for both sessions | proves the archive's claims stay honest |
| P3 | `pipeline/` extracted & parameterized; both sessions reproducible from it | tool separated from data |
| P4 | Claim generators + `build_claims.py`; ≥85% reproduction gate against existing ledgers | **new sessions become one command** |
| P5 | `build_report.py` templating; prose-only agent pass | full loop |

P1+P2 are mechanical. P4 is the real engineering.

## 7. Open risks

- **Third-party data**: public repo publishes pinglamb's replays, TETR.IO user ID, and a critique of their weaknesses. Worth a heads-up to them; README should credit both players. An `--anonymize` flag in the pipeline is cheap insurance if they'd rather not be named.
- **Generator coverage**: if a future session's drama doesn't fit a family, the pipeline still produces a valid report — bespoke claims are additive, never required.
- **Dafny in CI**: pin the Dafny version (4.11.0 locally); verify time is ~3-5s per session, so CI stays fast.
- **`.ttrm` churn**: single-line JSON; marked `-diff` so PRs stay readable.

---

## P4 — DONE (2026-07-25)

Claim generators shipped. A session's ledger and its Dafny proofs are now generated from
`facts.json` by `bin/new-session`; only the Cantonese prose still needs a person.

**Design.** A family never writes a predicate string. It builds a *spec* (a nested dict
in `pipeline/claims/spec.py`) which is rendered to a Python predicate and to a Dafny
`ensures` clause by two backends, so the checked statement and the proved statement
cannot drift apart. 32 families live in `pipeline/claims/generators.py`.

**Measured coverage** (`pipeline/claims/equiv.py`). Comparing generated to hand-written
predicates by string is useless — every predicate is True on the real data. Instead every
single-value mutation of the dataset is applied (exhaustive: 4,440 sites for the 7-match
session, 7,019 for the 10-match one) and a hand claim counts as covered only when a
generated claim's truth is impossible without it, and both are falsifiable somewhere.

| Session | Coverage | Identical behaviour |
|---|---|---|
| 2026-07-22 (10 matches, 54 hand claims) | 45/53 testable = **85%** | 24 |
| 2026-07-24 (7 matches, 52 hand claims) | 48/49 testable = **98%** | 28 |

Combined 93/102 = **91%**, clearing the ≥85% acceptance gate. Claims no mutation can
falsify are reported separately rather than counted as covered.

**Bugs this phase's own gates caught**
* the "only one decider" claim restated that match's score without proving it was the
  *only* one — fixed by adding a match-margin counter to the algebra
* `total_rounds` rendered to Dafny as a literal, making "50 rounds" the tautology
  `50 == 50` — real in Python, vacuous in Dafny; now the sum of the `nrounds` consts
* `Facts.dfy` emitted the whole dataset, leaving dead consts no lemma reads, so mutation
  survivors were meaningless — now only load-bearing data is emitted
* `+1` mutations could not kill values that are only constrained beyond a threshold; the
  operator escalates before calling a mutant a survivor (14/14 killed)

## P5 — in progress

Report templating: `build_report.py` generating the scoreboard, match cards, charts and
appendix from `facts.json` + the ledger, leaving prose sections as the only hand-written
part. That closes the loop from replays to published report.

**Shipped (2026-07-25): the `chart-data` island.** Every chart in the report — the per-match
scoreboard strip, the VS small multiples, the clear-type bars, the tape chart, the match
timeline — reads one JSON island that until now was written by hand. Nothing tied it to
`facts.json`, so a chart could disagree with the proved data and no gate would notice; in a
repo whose whole claim is "these numbers are checked", that was the largest remaining hole.

`pipeline/chart_data.py` derives it, `pipeline/build_report.py` injects it into a marker
region, and `--check` fails CI if the committed report differs from what `facts.json`
generates.

Validation, in the same style as P4:
* the generator reproduces both committed islands exactly on the first run — every count,
  every float — with a single addition: session 2026-07-22's island was missing `kills`
  (43/36), which 2026-07-24's already carried
* the drift gate was mutation-tested (perturb one committed value → `--check` exits 1;
  restore → 0), so it is not decorative
* both reports were re-rendered in a browser: 10/7 match cards, 10/7 small multiples, both
  charts, 110 badges, 54/52 appendix rows, 158/100 round rows, no console errors

**Shipped (2026-07-25): the hero and scoreboard**, and with it the prose split the rest of P5
follows. `pipeline/hero.py` derives the date, both player names and the series score from
`facts.json`; the headline, taglines, lede and the optional eyebrow kicker come from
`<report_dir>/prose/hero.json`. Derived values are HTML-escaped; prose is inserted raw because
it legitimately carries `<span class="hl-y">`, `<strong>` and badge spans.

Validation:
* both committed heroes were *extracted* into prose files and regenerated **byte-for-byte** —
  the migration only wrote a prose file where the round-trip was exact, so no prose was
  silently rewritten. The reports' only diff is the two marker lines.
* five adversarial probes, all caught: hero drift vs the committed report, a simplified glyph
  in prose, an empty prose field, a missing prose file, and a session whose replay timestamps
  disagree with the directory it was dropped into
* both heroes re-rendered in a browser: one `.hero`, correct eyebrow (including 07-24's
  第二回合 kicker), score in player order (6:4 / 3:4), taglines, and every badge resolving

**Shipped (2026-07-25): the match cards.** `pipeline/matches.py` generates the `match-copy`
island from `<report_dir>/prose/matches.json`; the card's numbers (score, winner, the
per-round pip trail) already came from the chart island.

The interesting part was what had to stop being code. Two editorial constants were baked into
each report's inline script — `m.index === 7` (which card gets the spotlight) and a literal
`data-claim="C026"` on every card's score — and they differed per session, which is a large
part of why the script could not be shared. Both are now `hero_match` and `score_claim` in the
prose file. The score itself is built from DOM nodes instead of an `innerHTML` string, and
reads `CD.players` by position rather than `m.score.yachi`, so that renderer no longer knows
who is playing. `chart_data` emits `players` for it.

Validation: both islands round-trip (the committed copy regenerates exactly); six adversarial
probes all caught (a match with no card, an unknown card index, an empty body, `hero_match`
out of range, a simplified glyph, and drift in the committed island); both reports re-rendered
— 10/7 cards, exactly one spotlight card at the right index, scores in player order with
07-22's C026 badge and none on 07-24, pip trails summing to 79/50 rounds, 110 badges, no
console errors.

**Shipped (2026-07-26): 全場之最 — the session records.** The generators already found every
session superlative; they were only readable as rows in the 52-row appendix, which is the wrong
form for a headline number. Nine stat tiles per session now carry them (single-round max VS,
APM, lines, spike, B2B, T-spin, combo, plus the longest and shortest round), ordered by how
much each measure actually says about who won the round — the paired AUC, so COMBO's tile comes
last rather than first.

Design references: Leetify's "NEW PERSONAL BEST" callouts (a superlative deserves a card, not a
table row) and Lichess's habit of stating the finding as a sentence under the figure. The form
follows the bundled `dataviz` procedure: a KPI row of stat tiles, no hover layer, proportional
figures (`tabular-nums` is for columns), identity as a coloured dot beside ink-coloured text,
and no new colours.

The load-bearing decision: **each tile's figure is read out of the claim's own spec** — the
operands of the equality Dafny proved — via `claim_cards.round_operand()`, never re-derived
from `facts.json`. Swap the literal in a spec and the tile changes with it; give a claim a spec
of another shape and it gets no tile at all rather than an invented figure. `match_apm_max` is
listed in the table on purpose so its exclusion prints in a footnote instead of vanishing. The
claim's full sentence sits under every figure, which is what keeps disclosures like
「呢個數字全場出現過 3 次」 attached to the number.

Also folded out: `pipeline/fmt.py` (the floored formatters) and `pipeline/claim_cards.py` (one
ledger + proof-map loader), both of which `build_round_table.py` now uses instead of its own
copies — its output verified byte-identical after the change.

This surfaced a **pre-existing inconsistency**, since fixed (below): the hand ledgers rounded
their 約 figures while the generated ledger floors them (C009 約262.6 vs G017 約262.5, one
integer).

## The 約 convention, enforced (2026-07-26)

45 rounded figures were rewritten to their floored values across both sessions — 25 + 6 in the
Cantonese and prose, 12 + 2 in `english_gloss`, which ships inside the claims island and is
therefore just as published. Every replacement was computed from `facts.json` and applied only
where the data gave exactly one floored candidate, so nothing but the last digit changed.

Three passes were needed, and each found what the previous one had missed — worth recording,
because the misses were all *scope* misses rather than logic errors:

1. one-decimal 約-figures in the ledgers and prose files
2. figures in seconds (「約128.6秒」 is the same artifact), and prose typed straight into
   `report.html` rather than into a prose file
3. two-decimal figures (`約1.84` — the pattern for one decimal never matched it) and the
   `~` / `≈` markers used in `english_gloss`

`pipeline/check_prose_figures.py` now closes the class instead of the instances: it resolves
every 約 / `~` / `≈` figure in every hand-written surface against `facts.json` and fails when no
datum floors to it but one rounds to it. Wired into CI per session. `check_claims` could never
have caught this — every predicate compares the integer, not the printed text.

### The second-order bug it caused

`codegen` builds each lemma's *name* from the claim's `english_gloss`, so correcting 14 glosses
renamed 14 lemmas and stranded 8 proof-map entries — badges pointing at lemmas that no longer
existed. Every existing gate stayed green: the verifier still reported 0 errors, and the
status check still counted 54/54 verified, because it only reads statuses. The maps were rebuilt
from real verifier output, and `pipeline/check_proof_links.py` now fails when any entry names a
missing lemma (mutation-tested). It runs per artefact in CI, plus once against the generated
`Claims.dfy` in the temp directory CI builds it in, since those lemmas are not committed.

Worth remembering as a pattern: a *derived identifier* (lemma name ← gloss text) turns a
cosmetic edit into a structural one. Nothing in the pipeline had declared that dependency.

## SMT-LIB as a third backend (2026-07-26)

**The finding that motivated it, measured not assumed:** all 106 hand lemmas and all 153
generated ones have **empty bodies**, and use no quantifiers, no functions and no loops. Dafny
was translating a ground arithmetic statement into Boogie, which generated a verification
condition, which Z3 evaluated. None of Dafny's proving machinery was in use — only its syntax,
and the Boogie layer that caused the balanced-tree workaround in `spec.bal`.

So `pipeline/claims/smt.py` renders the same specs to SMT-LIB 2.6, `pipeline/codegen_smt.py`
emits one self-contained `claims.smt2` per session (facts as `define-fun`, one
`(assert (not claim))/(check-sat)` per claim, every answer must be `unsat`), and
`pipeline/check_smt.py` gates it. Constant names match `Facts.dfy` exactly so the two backends
can be read side by side; sums are emitted n-ary because an s-expression has no AST-depth limit
to work around.

Measured over the same claims: **40 ms and 10 ms** versus Dafny's ~4.6 s and ~3 s. That is what
makes the anti-vacuity mutation test cheap enough to run on **every push** (`--mutate 12`, under
a second) instead of weekly — the mutation escalates (+1, +1000, far) because banded predicates
like `135000 <= v < 136000` survive +1 by design.

Validation: 77/77 and 76/76 `unsat`; the committed file regenerates byte-for-byte; 12/12
perturbations falsified at least one claim. Dafny stays exactly as it was — this is a
cross-check, not a replacement, and the report's badges still cite Dafny lemmas.

**Two encoding facts, both found by a solver refusing the file rather than by reasoning:**

* strings are **integer codes** with a legend in the header, not the `String` sort. The sort
  worked with z3 and cvc5 and locked everyone else out, which defeats the point of emitting a
  standard format so an independent solver can read it.
* the logic is **`QF_NIA`**, not `QF_LIA`. The integer variance identity squares a datum, and
  `QF_LIA` rejects `(* v v)` outright.

The second attempt at that first point also exposed a hole in the gate itself: with the wrong
logic declared, z3 answered nothing and printed `(error "logic does not support nonlinear
arithmetic")` per claim — and the token-based output parser read the words inside those errors
as claim ids and answers, so a **refused file reported 15 kills per mutation**. The parser is
line-based now, solver errors are a failure in their own right, and that is mutation-tested by
re-declaring the wrong logic.

### What CI caught that local runs did not (2026-07-28)

The first push with cvc5 went red, and the failure was real rather than environmental: CI
sampled 12 constants where local runs had sampled 6, and hit
`m5_r2_yachi_gameoverreason` — a constant **no perturbation could kill**. Chasing it found
three separate defects in the mutation operator, each hidden behind the last:

1. **Categorical codes need a category, not an offset.** That constant is `5 = winner`, and
   G065 counts death reasons (42 `garbagesmash`, 8 `topout`). Adding 1, 1000 or 10⁶ moves it to
   a value that is still neither, so both counts hold. `5 → 3` falsifies it immediately.
2. **Coded-ness must come from the name, not the value.** The first fix asked "is this value in
   the code range 1–5?", which reclassified a `topcombo` of **4** as a category and mutated it
   to 1/2/3/5 — none of which crosses the `> 6` its claim tests. Six genuine measurements were
   reported as survivors. The emitter already marks coded constants with a trailing `; label`,
   so that is what is read now.
3. **Escalation has to go both ways.** `m4_r3_pinglamb_inputs` feeds "yachi's keys-per-piece is
   lower than pinglamb's" — *raising* pinglamb's keypresses keeps that true at any magnitude.
   Only lowering it (to 0) falsifies anything. The operator was increase-only.

The sample is now **stratified by kind of datum** rather than uniform, since all three bugs
lived in a kind, and CI mutates 96 constants covering all 32 kinds instead of 12 uniform draws.
Both sessions: 96/96 killed, and a 250-constant sweep also came back 500/500 clean.

The lesson worth keeping: a mutation gate reporting "all killed" says as much about the operator
as about the data, and an operator that only knows one kind of perturbation will certify
whatever it cannot express.

### The second solver, done (2026-07-26)

**z3 4.16.0 and cvc5 1.3.4 both answer `unsat` on all 153 generated claims.** That is the
argument the SMT backend existed to make: the same file, two independently implemented solvers,
same verdict — the dual-extractor design applied to the proof side.

Finding cvc5 took a wrong turn worth recording: `brew install cvc5` fails and
`brew search --formula cvc5` finds nothing, because cvc5 is packaged as a **cask in the
project's own tap** (`brew install --cask cvc5/cvc5/cvc5`). The PyPI package is Python bindings
with no CLI. The cask is also what makes CI pinning trustworthy — it carries the release
sha256, GitHub's asset digest reports the same hash, and the downloaded bytes matched both
before the binary was run.

Then two invocation facts, both found by the solver refusing to work rather than by reading
docs: `check_smt` had hardcoded z3's `-in`, which cvc5 rejects outright, and cvc5 will not
honour the file's `push`/`pop` without `--incremental` (it errors with
`cannot push when not solving incrementally`). `SOLVERS` maps each name to its flags now, and
the file is passed as a path, which every front end accepts.

Cost of the whole gate with both solvers, byte-identity and 8 mutations: **0.33 s**.

z3 is deliberately not in CI: recent z3 releases ship only `x64-glibc-2.39` builds, which cannot
run on the `ubuntu-22.04` runner the Dafny step pins (glibc 2.35), and the ≤ 4.14.1 builds that
target 2.35 have no GitHub-reported digest to pin against. So z3 runs locally and cvc5 in CI,
over the same committed artefact.

### Dead constants, found by the same probe

Mutating `m9_r8_yachi_vs` killed nothing, which turned out to be correct (a banded predicate),
but checking why exposed a real defect: the per-session `codegen_dafny.py` scripts emitted the
whole dataset, so **157 constants in 2026-07-22, 6 in 2026-07-24 and 15 in `proof/` were read
by no lemma**. A const nothing reads cannot be killed by a mutation, so it inflates how much of
the data the proofs appear to pin down. `pipeline/codegen.py` had filtered the generated ledger
this way from the start; the three legacy scripts now do too, and
`pipeline/check_dead_consts.py` keeps it that way. All three artefacts re-verify: 56, 52 and 22
lemmas, 0 errors.

## The appendix (2026-07-26)

`pipeline/appendix.py` now owns 證明附錄 — the trust-chain note, the status line, and one table
row per claim — plus the `claims-data` island the badges resolve through. The rows are **static
HTML** rather than assembled in the browser, which deletes the last concatenating row builder
(44 lines of JS per report), makes the appendix exist without JavaScript, and lets it print.
The two per-session `build_appendix.py` scripts are deleted: the pipeline supersedes them.

Three things stopped being hand-maintained:

* the island's `generated_at` timestamp, which nothing displayed and which made the artefact
  differ on every run — the opposite of what every other gate here checks
* 「7 個 replay 檔案」 and 「52 條」 in the trust-chain prose, typed by hand per session and now
  derived from `facts.json` and the ledgers
* the three status-line wordings, which all shipped in the JS so the browser could pick one;
  only the applicable branch is emitted now

Verified by snapshotting the JS-rendered appendix in a browser *before* the change and comparing
after: 54 and 52 rows, **every cell identical**, same status line, same `data-all-verified`, 110
badges. Probes: a hand-edited row fails `--check`; a claim downgraded in the proof map renders
驗證中（failed） with `data-all-verified="false"` and no tick; markup injected into a claim's
Cantonese comes out escaped.

**關鍵時刻 done (2026-08-02)** — `pipeline/moments.py` + `prose/moments.json`, extracted from
the committed HTML rather than retyped and verified to render identical content in all four
reports. The trivia numbers stopped being hand-typed (they are positional now), and the
figures gained per-field attribution: `prose/moments.json cards[3].body` instead of an
anonymous "report.html hand-written prose". Doing it exposed that `check_prose_figures`
enumerated prose files by NAME, so the move silently removed 4 figures per session from the
scan; it now walks `prose/*.json` generically.

**數據對決 and 建議 done (2026-08-02)** — `pipeline/stats_section.py` and
`pipeline/coaching.py`, built in parallel by two agents and wired in serially, because both
touch `build_report.SECTIONS` and all four reports. Verified by an independent harness rather
than by the agents' own reports: all 8 section renders are content-identical to the committed
markup, the element-id sets match (the chart mount points are read by the inline JS, so
losing one silently blanks a chart), and each whole report reproduces its own content. The
`約`-figure coverage landed back on 102/49/43/48 — the number to watch, since moving prose out
of report.html is what silently narrowed that gate when 關鍵時刻 moved.

**P5 — DONE (2026-08-02).** `pipeline/skeleton.py` emits the shell, the marker regions
in document order, and TODO prose; `bin/new-session` calls it as step 6 and never touches a
report.html that exists. Verified end to end from raw replays: 6617 lines, every region
filled, `build_report --check` clean, `check_report_shell` clean, and re-running leaves a
written report byte-unchanged.

The copy-forward workflow it replaces had been propagating stale constants. The VS small
multiples' emphasised rounds were literals computed once for 07-24 and carried into three
later reports, where they marked unremarkable rounds and missed the real extremes (07-28's
168s marathon, 08-01's 206s). Now derived in `chart_data.extreme_rounds()`, so they are
covered by `build_report --check`. Two more of the same shape were fixed on the way: BSD
`cp -n` exits 1 when it skips, so `set -e` aborted `bin/new-session` at step 1 on any
re-run; and the player colours are now positional `--p1`/`--p2` with `--yachi`/`--pinglamb`
kept as aliases, because `records.py` and `build_round_table.py` emit `var(--yachi)`
literally into the regions they own.

Residue, deliberately not done: the four committed reports still declare the palette under
the old names (the aliases make both spellings work), and the `<title>` is the one authored
string outside any region.
2. a report skeleton, so `bin/new-session` emits a report with TODO prose rather than
   expecting one to be copied from a previous session. This is also where the inline script
   stops being player-hardcoded: ~110 occurrences of `yachi`/`pinglamb` remain in colours,
   keys and labels, and they should be resolved once, by the template, not chipped at.


---

## Board reconstruction — open (2026-07-29)

Everything above derives from `results.stats`. A whole class of question cannot: where the stack
was, how deep the well ran, what the board looked like when the kill landed. Those need the board,
and the board needs a simulator that replays the input stream.

**What exists.** A frame-stepped TETR.IO simulator (session scratchpad, not in this repo) on top of
the SRS geometry from `yachi/td-opener-trainer`. Solved and verified: the piece queue (MINSTD
`16807`/`2147483647` over the `ZLOSIJT` bag, 158/158 rounds well-formed), the 60 fps frame clock
(`frames == finaltime_ms * 0.06`, 158/158), incoming garbage content (`amt`/`x`/`size` are in the
`ige` payload — no RNG derivation), and the outgoing attack timeline (recoverable from the
*opponent's* ige stream, 156/158 against `garbage.sent`).

**What blocks it.** Attack timing is **100% correct before the first garbage and ~6% after**. The
insertion rule is wrong, not its parameters — 40 combinations of `garbagespeed`/`garbagecap`/insert
mode/cancel mode were swept and the best still survives only 7/158 rounds. So the board is provable
only on a *prefix* of each round, using the opponent's ige stream as a per-attack oracle:
**2001/14517 placements, 13.8%**, and systematically the early part of every round.

**What it produced so far.** One metric, T-Spin Forecast, written up in
`sessions/2026-07-22/forecast-metric.md`. It came back a **negative result** — AUC 61.4%, on top of
TSD's 60.9%, inside the no-signal band. Worth reading before extending this work, because the
loose version of the same metric scored 72.7% and would have looked like a finding.

**Superseded 2026-08-02 — see [`FORECAST-PLAN.md`](FORECAST-PLAN.md).** The instrument was pointed
at the other three sessions (it had always honoured `REPLAY_DIR`; nobody had tried). On the three
sessions it was *not* tuned on the round-level signal is **exactly 50.0%** — 17W-17L-43T, p = 1.000
— against 68.8% on 2026-07-22, at 78% power versus a true 70% effect. The descriptive level
survives and is homogeneous across all four sessions (χ² p = 0.978): **14.5% [11.9%, 17.5%]** over
654 verified T-spins. That document also records four defects the work found in committed code,
and the plan for P0–P4.

### 1 — DONE (2026-07-29): the triage says no

Eight board-derived measures, paired AUC over the 26 rounds with a decided winner and a verified
prefix on both sides:

| measure | AUC | W-L-T | two-sided p | 95% CI |
|---|---|---|---|---|
| height when garbage lands | 28.6% (inv) | 4-10-0 | 0.180 | 45–88% |
| holes at end of prefix | 32.7% (inv) | 7-16-3 | 0.093 | 49–84% |
| max stack height | 36.5% (inv) | 8-15-3 | 0.210 | 45–81% |
| bumpiness | 38.5% (inv) | 10-16-0 | 0.327 | 43–78% |
| well depth | 38.5% (inv) | 10-16-0 | 0.327 | 43–78% |
| holes per piece | 42.3% (inv) | 10-14-2 | 0.541 | 39–76% |
| clear rate | 46.2% | — | — | — |
| average height | 50.0% | — | — | — |

**Nothing reaches significance**, and every confidence interval includes chance. All six
non-trivial measures point the same way — lower, cleaner board wins — which reads less like six
findings than like six proxies for *played well*, a thing `APP` already measures at 91.5% AUC
straight out of `results.stats`. Against a baseline of VS 100% / APM 94.6% / APP 91.5%, a
board metric would have to be far stronger than any of these to earn a column.

**Caveat, stated so nobody over-reads this:** n=26 is underpowered, and the verified prefix is
systematically the *early* part of every round — precisely excluding the deep stacks and heavy
downstacking where these measures should matter most. This is "not justified on current evidence",
not "proven worthless". If the simulator ever gets fixed for another reason, re-run the triage on
full coverage before concluding again.

### 2 — DONE (2026-07-29): mutation coverage closed, 5/5

The two survivors needed adversarial boards, and both took a search rather than an argument:

* **accepts non-rotation landings** — a vertical T slides down a 2-wide channel and comes to rest
  with three corners filled. It satisfies the corner rule but the last action was a downward move,
  so it is a placement, not a spin. Dropping the `rot` guard scores it 2 lines.
* **`bestTspinLines` drops the spin test** — a 3-deep 1-wide well; the T rotates in and completes a
  row with only two corners filled. Dropping the corner test scores it 1.

The first search for the second board returned boards whose rows were **already full**, which
cannot persist in a real game — an invalid state that would have certified a mutant as equivalent.
Excluding pre-existing full rows found a valid one immediately. Worth remembering: a mutation
search over synthesised boards needs the game's own invariants applied to the search space, or it
answers with states the game can never reach.

### 3 — advanced, not finished (2026-07-29)

Worked on despite (1), at the user's direction. Two hypotheses tested and refuted: rising the
*remaining* garbage after a clearing placement (`insertAfterClear`), and using the ige wrapper's
frame rather than the outer event frame for arrival. Neither moved the matched-attack prefix.

**The attack table is not the problem — it is now confirmed correct.** Aggregating every attack
against the opponent's ige stream, keeping only samples where nothing was cancelled:

| signature | observed | formula |
|---|---|---|
| `full-3 b2b0` | 6 (n=50) | TST 6 |
| `full-2 b2b0/1/2/3` | 4 / 5 / 5 / 6 | base 4, then +1, +1, +2 |
| `none-4 b2b0/1/2/3` | 4 / 5 / 5 / 6 | quad 4, same escalation |
| `none-2 c0/c1/c2` | 1 / 1 / 1 | combo multiplier ×1.25, ×1.5, floored |
| `full-2 b2b1 c1` | 6 (n=2) | (4+1)×1.25 = 6.25 → 6 |

**The residual is a board error, and specifically a line-count one.** The minority readings are
`full-1 b2b0 → 6` (the sim cleared 1 line where the real game cleared 3) and `none-2 b2b-1 → 4`
(the sim called a T-spin double a plain double). A missed line also breaks the B2B chain, so a
single early board error cascades into every later attack — which is why one mistake destroys a
whole round rather than one claim.

**Where the error starts, measured:** of the 42 rounds that diverge, **16 diverge before any
garbage has been inserted at all**, 25 after, 1 with no garbage in the round. So this is not one
bug in the garbage model — there is a garbage-independent placement bug too, and it is the more
tractable of the two because no garbage timing is involved. That is the next thing to chase.

**IRS/IHS implemented and refuted (2026-07-29).** The handling block carries `irs: "tap"` and
`ihs: "tap"`, and 3 of 35 pieces in a sample round are hard-dropped with a rotate or hold key still
held — so initial-rotation looked like a strong candidate for the garbage-free bug. Implementing it
made things sharply *worse* (matched attacks 197 → 76, survivors 7 → 2). The reading is that
**"tap" mode fires only on a fresh press, not on a key held across a spawn**, so the baseline was
already correct. Kept behind a default-off flag; the refutation is the result worth keeping,
because it removes handling from the suspect list.

**A note on formal methods, since it comes up:** Dafny and the SMT backend prove *claim ⇔ extracted
data*. Whether the simulator matches TETR.IO is an empirical question about an external system, and
no proof assistant can settle it — only the replay oracle can. Formal proof becomes applicable
once the sim passes its gate and its outputs enter `facts.json` as data, at which point claims
about those numbers are provable like any other.

This corrects the earlier claim that timing is "100% correct pre-garbage": that was measured over
the prefix before the first garbage *arrival*, a shorter window than before the first *insertion*.

### 3b — the method was wrong, and fixing it localised the bug to single pieces (2026-07-29)

Six hypotheses had been refuted one at a time, each costing a full 158-round sweep. That is the
wrong shape for this problem. The field this belongs to is **deterministic-lockstep desync
debugging**, and its standard method is *per-tick state checksums on both sides, compare every
frame, then per-subsystem hashes to narrow which subsystem broke* — a search over **time**, not
over hypotheses. The companion technique is **ddmin** (Zeller & Hildebrandt, IEEE TSE 2002), which
minimises a failing input until removing any single element makes the failure vanish.

Sources: Zeller & Hildebrandt, *Simplifying and Isolating Failure-Inducing Input*;
`bugnet.io/blog/how-to-debug-desync-in-deterministic-lockstep-games`;
`gafferongames.com/post/deterministic_lockstep`.

Applying the search-over-time half properly — bisecting each round on the opponent's ige stream and
keeping only divergences that occur before any garbage is inserted — narrows the bug from "somewhere
in the round" to **a single piece**:

| replay | round | player | piece | sim said | real |
|---|---|---|---|---|---|
| `…-3.ttrm` | 1 | yachi | **14** (O) | 2 lines, no spin → 11 | 1 |
| `…-2.ttrm` | 6 | yachi | **19** (T) | 2 lines, no spin → 11 | 1 |
| `…22-.ttrm` | 0 | pinglamb | **20** (T) | 2 lines, full spin → 6 | 7 |
| `…-9.ttrm` | 0 | pinglamb | **33** (I) | 3 lines, no spin → 1 | 2 |

Nine such single-piece cases exist. An attack of **11** for a two-line non-spin clear can only be
`double(1) + allclear(10)`, so at those pieces the simulated board is empty when the real one is
not. Aggregate check: the sim reports **7** perfect clears where the real games had **19** — it is
losing real all-clears, another board-divergence signature rather than a scoring one.

**What remains is the oracle half.** TETR.IO's own client is the reference implementation (a
`.ttrm` dropped into the PC or web client plays back); no third-party board renderer exists. With
the window already down to one piece, the capture needed is a handful of board states from one
round — a bounded task, not the screen-scraping pipeline it was estimated as earlier. It needs a
logged-in TETR.IO session, which the agent cannot and must not do.

### 3c — differential test run, and it found a mechanic that was never modelled (2026-07-29)

The oracle half was executed: `replay-2026-07-22-3.ttrm` round 1 loaded in the TETR.IO client,
paused, scrubbed to a chosen frame. The transport exposes a **frame counter** under the scrubber
(`0:27.583 FRAME 1655`), which independently re-confirms the 60 fps clock and makes frame-accurate
comparison possible.

At **frame 421**, yachi's real board against the simulator's board at its last preceding lock
(frame 387):

```
sim @387            real @421
36 XXX..XXXXX       XXX..XXXXX     <- identical
37 XXX..XXXXX       XXX..XXXXX     <- identical
38 XXX...XXXX       XXXXXXXXXX     <- full, magenta T at cols 3,4,5
39 XXXX.XXXXX       XXXXXXXXXX     <- full, magenta at col 4
```

The overlapping stack matches **cell for cell**. The two bottom rows are full in the real client
because a T-spin Double had just completed them and they were still on screen — caught mid
**line-clear animation**. The simulator performs the same TSD at frame 429 and reaches the same
`XXX..XXXXX / XXX..XXXXX`.

**So placement geometry is not the bug.** Queue, hold, DAS/ARR, rotation and hard drop all produce
the right stack. What differs is *when a completed row vacates*: the simulator clears instantly on
lock, while TETR.IO holds completed rows for a **line-clear delay** — about 34 frames in this
instance. Nothing in the simulator models that, and it was not on the suspect list, which is why
six hypothesis sweeps walked straight past it.

It also explains the phantom perfect clear: at frame 449 the simulator drops an O into the two
remaining gaps, empties the board and scores `double + allclear = 11`, where the real game sent 1.
With a clear delay, a piece can land before the rows vacate, leaving residue that makes a perfect
clear impossible.

**Next:** capture frames 429–470 the same way and confirm what the real board holds when the
simulator empties it, then model the line-clear delay (and check whether `results.stats` or the
options block pins its length rather than fitting it).

### 4 — not started

Gated on (3). Nothing from a simulator can carry a badge without a second independent
implementation agreeing byte-for-byte, and there is no point writing one against a simulator that
still fails its own gate.

### Original TODO, for reference

1. **AUC-triage candidate board metrics on the existing 13.8%.** Before spending days on simulator
   fidelity, ask whether *any* board-derived measure carries signal: stack height when garbage
   lands, covered holes created per piece, well depth, downstack rate under pressure, height
   differential at the kill. The probe already exists. If they all sit at 50–60% like forecast did,
   stop here — that is the whole answer and it costs an hour.
2. **Close the two surviving mutants** on the T-spin availability probe ("accepts non-rotation
   landings", "`bestTspinLines` drops the spin test"). Either construct a board that distinguishes
   them or demonstrate equivalence. Currently recorded as open, not as equivalent.
3. **Fix the post-garbage divergence** — only if (1) says the sim is worth finishing. The per-attack
   oracle localises failures to individual pieces now, so this iterates far faster than it did.
4. **A second independent simulator**, agreeing byte-for-byte on emitted per-round values. The
   dual-extractor rule applied to derived data; nothing from a simulator can carry a badge without
   it.

Items 3 and 4 are gated on 1. Item 2 is independent and small.

---

## T-Spin Forecast — the mechanism is settled, the gate in front of it is not (2026-08-02)

The metric now establishes a mechanism for every event it counts (`1a5ce30`): the window is walked
to find the step where the executed spin became available, and that step is decomposed into
place → clear → insert garbage, so whichever edit the availability crosses IS the cause. Rate is
**1 of 654**. What remains open is not the mechanism test but the gate that decides which events
reach it.

### 0 — RESOLVED: the user's own definition agrees with the published number

Stated by the user on 2026-08-02: *"putting an overhang over a few lines far of a hole, when the lines
between them clear, like 1,2,3,4,5+ **cleared by not tspin**, it becomes a tspin hole."* Implemented in
full it is a **necessity** test — track the overhang cell and the cell the T lands on, and count the
event when rows are removed from between them — plus the clause that the removing clear must not itself
be a T-spin.

Measured over all four sessions:

| step | events |
|---|---|
| gap between overhang and landing cell closes | 181 |
| ... rows removed **only by T-spin clears** | 180 |
| ... mixed | 0 |
| ... rows removed **only by plain clears** | **1** |

The 180 are the C-Spin: a T-spin triple removes three rows under an overhang laid in bag 2 (174 of 181
roofs are pieces 7-13), the overhang descends three, the T-spin double goes in. The clear that opens the
slot is itself a T-spin, so the "not tspin" clause excludes them — correctly, since that is the opener,
not a read of the board. The single survivor is `pinglamb replay-2026-07-28-6 r5 lock 32`, closed by a
plain double then a plain single, overhang at piece 19.

**That is the same event the committed metric publishes.** Four routes reach it independently: step
localisation with the straddle test (the shipped rule), the gap-closure necessity test, the not-a-tspin
clause, and a hand-check of the raw boards. No figure changes.

Two things this settled that were previously recorded here as open puzzles:

* **Prophecy and Forecasting are not independent axes.** Implemented as separate predicates over 649
  events, both off-diagonal cells are EMPTY (181 both, 0 either-only). Nothing except a line clear can
  lower an overhang — filling under it does not move it and garbage pushes it up — so placing a roof
  above its final position forces a clear to be what completes it. four.lol's two sections describe one
  event from its two ends.
* **The bimodal gap distribution was not an artefact.** Gap-at-placement being 2 or 5 and never 3 or 4
  is a T-spin triple removing exactly three rows, every time.

### 1 — CLOSED: the leak was not a leak, and the defect was in the counterfactual's deletion set

This item used to read: *"`improved` collapses the board to one number, so a mechanism that replaces
one two-line spin with a different two-line spin moves nothing… 1 event of 654 has garbage that IS
load-bearing at execution."* The sizing run it asked for was done on 2026-08-04. **Every part of that
claim is false except the arithmetic.**

**The event is not load-bearing.** `yachi replay-2026-07-28-1 r5 lock 36`: the T tucks into a garbage
row that arrived at **lock 11**, and the roof is at lock 33. The only garbage that arrived inside the
window `(33, 36]` is a single row at lock 34, sitting at the very bottom of the field twelve rows
below the slot. Delete just that row and the executed spin is untouched — still two lines. The 2 → 1
drop comes from `withoutGarbage` stripping **all thirteen** garbage rows, including the one that is
the slot's own floor and predates the roof by 22 locks. The scalar falls because the board was
mangled, not because any post-roof garbage held the spin up.

**Zero events of 654 depend on post-roof garbage.** Restricting the deletion set to rows whose derived
arrival lock is in `(j, k]`: 121 events have such a row (`|D|` from 1 to 14), and the executed spin
survives its removal in **all 121** — 0 gone, 0 degraded, 0 undecidable. The remap was mutation-tested
(drop the row-shift term → 0 reachable / 121 gone), the arrival tagging was validated against the
board at 17,076 lock-steps with 0 disagreements, and a BFS matching the executed cell set reproduces
the actual placement, line count and spin grade on 654/654 events.

**The proposed replacement does not subsume `improved`; it contradicts it in the wrong direction.**
`improved` asks about the board's best slot, the executed-spin test asks about the one slot the player
used, and those differ whenever the mechanism opens a *better* slot than the one executed. At least
**81** currently-accepted events get re-decided INDEPENDENT by the garbage arm alone. Direction B —
`improved = false` and the executed spin DEPENDS — is **empty**. And the line-clear arm has no
execution-time form at all: re-inserting a cleared row yields a board carrying a full row, a state
`lockPiece` cannot leave behind. Back-mapping the executed cells across a cleared row leaves a shape
that is not a T in 47 of 50 cases, so a naive version reports "load-bearing" for 100% of clearing
steps. Retiring `improved` in its favour would delete the corpus's only positive, which is a
`forecast_lineclear`.

**The deletion set is now restricted, and the last disagreement is gone.** `withoutGarbage` is
replaced by `withoutRows(board, garbageArrivedAfter(r, j, k))`. Arrival is derived rather than
tracked, by replaying each step's row edits over one boolean per row; the marks reproduce the real
garbage mask of `boards[t]` at all **110,927 lock-steps** of the four sessions across all seven
swept configs, ordered oldest-on-top everywhere — including `reference_queue`, the one config that
inserts garbage before the piece rather than after it. `loadBearingButNotImproved` is 0, the four
`forecast-facts.json` regenerate byte-identical (the counterfactual observes, it does not classify),
and five new mutants guard the set, `deletion-set-unrestricted` among them.

Note what the corpus test now asserts: `0` is a far weaker statement than the `1` it replaces. It
says only that the two instruments never diverge. The census and the mutants are what hold the rule
in place now, which is the usual cost of fixing the event a test was pinning.

**Also settled:** the sizing sweep costs **2.1 seconds** for all four sessions, not the hour this item
budgeted. `audit-mechanism.ts` already walks them cross-session and needs no `REPLAY_DIR`.

### 2 — CLOSED: the two-slot board exists, and the mutant is live (2026-08-05)

`metric/localise-skip-placement` sat unlisted as "equivalent for every step in the corpus": with no
clear at the causing step `B` IS `Bpre`, so the next branch runs the identical test, and all 388
placement attributions land on steps that cleared nothing. The separating shape has now been built
by hand and the mutant is in the sweep.

What made it awkward is worth recording, because the obvious construction cannot work. The board
needs a second slot that reaches the target in `Bpre` while the post-clear best slot straddles the
cleared row — but **a slot's rows go full, so nothing can descend past them**. Any ordinary second
slot placed above the low well seals it in both `Bpre` and `B`, and the low slot is never reachable.
Three attempts died there.

The way through is that `bestTspin` counts every full row in the board it produces, including the
one about to be cleared. So the high spin need clear nothing of its own: a nook confined to the
right-hand columns, worth exactly 1 in `Bpre` and 0 in `B`, blocking no column. With `target = 1`
the early return fires and the answer is `placement`; drop the early return and the same board is
`line-clear`. The fixture asserts both, so it also demonstrates the two branches genuinely disagree
rather than merely that one of them runs.

### Closed since the last roadmap entry

The "Original TODO" item 2 above — the two surviving mutants on the availability probe
(`best/no-rotation`, `best/no-spin-test`) — is **done**. Both are killed in the current sweep,
which stands at **36/36**. The probe they guard is now `bestTspin`, a single BFS returning both the
line count and the slot's rows; the second copy that once carried a different cap is gone.

### 3 — CLOSED: the garbage-floor events were the same five events as item 1, and they are decidable

This item used to read: *"When the cell the T lands on is GARBAGE it has no placing lock… That is 5
events."* Both halves are now settled, and the two items turned out to describe one population.

The five are `pinglamb 07-24-2 r6 lock 45`, `pinglamb 07-24-3 r7 lock 29`, `yachi 07-24-5 r7 lock 20`,
`yachi 07-28-1 r5 lock 36`, `yachi 07-28-8 r6 lock 21` — every one a TSD tucking into a garbage well
whose lower row is garbage. Item 1's "leak" is the fourth of them. They looked undecidable only under
the strip-all deletion set; under the restricted one **D never touches the slot in any of the five**,
because in every case the in-slot garbage arrived 8 to 22 locks *before* that event's own roof. All
five are decidable and none depends on post-roof garbage.

The tracing problem is also gone, and not by tracking cells. Clause 2 now reads **every cell holding
the piece up**, not the deepest row alone, so a garbage cell under the nose is no longer the only
evidence available — the shoulders usually rest on player stack whose provenance is exact. Where a
genuine support *is* garbage, the existing two-ended test decides it (no garbage at the roof ⇒ it
arrived later; no garbage event in the window ⇒ it predates), and only a straddling window is reported
`undetermined`. Corpus-wide that is **10 of 654**, reported and never counted either way.

What prompted the rewrite was measuring the branch this item leaned on. `floorOrigin` used to return
`'field-floor'` — documented as "the nose reaches the bottom of the playfield, which predates all
play" — in two structurally different situations, and the second one had inspected nothing at all.
Measured over 654 events: 161 nose-on-row-39 and **95 nose-over-empty**, all counted clause 2 TRUE.
Judging the real supports flips **36** of them (35 true→false, 1 true→null). The label is deleted: a
piece supported by the playfield bottom **alone** occurs 0 times in 654 events across all seven
configs, so the case it named does not exist. More generally the inspected cells were a *proper
subset* of the genuine supports in **all 654** events — 294 missed one, 204 two, 156 three — and the
missed cells carried strictly newer provenance in 258 of the 398 events where both sets were
non-empty. The old rule was reaching the right verdict from an input that did not entail it.

The published rate is unchanged at **0 of 654**, under all seven simulator configs.

### 6 — CLOSED: the scalar does conflate slots, and it changes nothing (2026-08-05)

Opened by the player disputing the published sentence — *"forecast is quite common"* — and closed by
the same player reading the boards. Both directions were wrong before the evidence arrived, mine
worse than theirs.

**The mechanism is real.** `localiseMechanism` and `improved` both track `avail(t)`, the board's
BEST T-spin, so neither can see a new slot born beside an existing one of equal line count. Item 1
said exactly this and was closed on 2026-08-04 by testing the GARBAGE arm alone — the line-clear arm
has no counterfactual, so the scalar was never checked there.

**The consequence is nil, and the first three measurements of it were wrong.** A slot-tracking test —
carry the executed T's cells back through every row edit and ask in each frame whether the slot is
spinnable — settles it, but only once it SELF-CHECKS: it must report spinnable at the frame the T
was really executed in. Two versions did not, and each produced a confident number. Requiring every
row the T occupies to fill (a T-Spin Single spans two rows and fills one) gave 323 events where the
spin demonstrably happened but the slot "did not exist"; requiring the roof above a TOP-ROW cell (a
vertical T's roof usually sits over the other column) gave 298. A looser straddle test gave 183.
With the self-check passing 654/654:

| what first made the executed slot spinnable | n |
|---|---|
| already spinnable when the overhang landed — the roof was the last piece | 585 |
| the player's own later placement | 64 |
| garbage | 4 |
| a line clear | 1 |

Four of the five fail clause 2. The survivor, `pinglamb 07-28-6 r6 lock 19`, is a vertical-T
three-row clear in a well walled by the player's own pieces, with the garbage five rows below it;
the arrival only shifted the stack. **So the published 0 of 654 holds under the player's own
criterion** — a clear or garbage before the hole becomes spinnable — and a slot-tracking rewrite
would land on 0 as well. It is therefore not worth doing.

**Re-probed 2026-08-09 from the executed-slot angle, and now GATED.** Recomputing `improved`
slot-locally — `bestTspin`'s BFS constrained to the columns the T actually occupied — over every
reactive event in all four sessions: **0 of 265** rose slot-locally (probe validated: 0 probe-misses,
and it reports a rise on 385/388 self_built and 1/1 forecast_lineclear, so it discriminates). 122 of
the 265 had garbage/clear co-occurrence in-window and none formed the executed slot. So a slot-local
gate reclassifies nothing; the 0% is real, not a saturation artifact. `forecast-saturation.test.ts`
pins it with a non-vacuity self-check (mutation-killed) — if a future session ever makes a reactive
event's own slot rise, that test fails and forces the slot-local rewrite decision on the data.

**What the detour found.** The 183 the loose test flagged are the C-Spin: **179** have a vertical T
clearing three rows as the piece that closes the gap, 175 laid the overhang in bag 1-2, and 173
executed in bag 3 — matching harddrop.com/wiki/C-Spin, *"a T-Spin Triple which is usually followed
by a T-Spin Double within three bags"*. Nothing in the code knows that. They are excluded because
the slot was already spinnable when the overhang landed, which is what an opener is, and clause 2 is
no help — it returns `pre-existed` for 146 of them. `forecast-corpus.test.ts` now pins the outcome
as an oracle (46 such events in 2026-07-28, 0 counted), demonstrated to fail when openers are
admitted. Deliberately NOT a rule in `forecast.ts`: a "vertical T, three rows, first bags"
blacklist needs one entry per named opener and encodes folklore where a property will do.

The wiki is reachable at `harddrop.com/wiki/<page>?action=raw`; the rendered HTML is 403.

### 4 — CLOSED: a dangling nose is still an overhang over a hole, at any depth (2026-08-05)

This item asked whether a T whose nose hangs into a well, with the shoulders carrying the piece,
is really "an overhang over a hole" — the worry being that there might be no cavity under the
overhang at all. **Ruled by the player, and the answer is that depth is not a criterion:** the hole
under a T-spin may be arbitrarily deep, and the nose failing to reach its floor only means the
shoulders got there first. The well the nose points into IS the hole. Nothing changes.

Re-derived while putting the decision to them, and the population was misstated here: it is **95**
events with a dangling nose, of which clause 2 already rejects 21. The **74** was the surviving
subset, not the population. Depth of the well beneath the nose, among those 74:

| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 9 |
|---|---|---|---|---|---|---|---|
| 36 | 8 | 13 | 4 | 3 | 7 | 1 | 2 |

Half sit at depth 1, which is simply what an ordinary T-Spin Double looks like — the cell under the
nose stays empty, and that is exactly why it clears two rows rather than three. Had a cutoff been
adopted anywhere it would only have moved the clause-2 census (568 `pre-existed`, down to 494 at
most); the published rate is 0 of 654 either way. Also confirmed while measuring: **0** events have
a piece resting on nothing at all, which is the case `'field-floor'` used to name.

No code change. The item is closed because the question was answered, not because it was worked
around, and clause 2 was right as written.

### 5 — CLOSED: the simulator's tests ran nowhere, and a dead import proved it

`forecast.test.ts` imported `isForecastOrUnverified`, which no file in the repo exports. It had been
there for weeks and the suite was green throughout, because three things are true at once: Bun does
not validate named exports, a name that is imported but never called is never evaluated, and there
is no `tsc` step. The third is the one that mattered — `bun test` was not in CI at all. Only
`cross-extractor` runs Bun, and only to re-run the extractors, so every assertion about this metric
(the corpus census, the wiki fixtures, the clause-2 verdicts, the mutation-guarded gates) was
verified on a laptop and nowhere else.

Both halves are fixed by a `typescript` job: `pipeline/check_ts_imports.py`, then the suite, which
takes under four seconds. The gate has a `--selftest` like `check_forecast_section` does, and it was
run against the actual historical defect — restoring the import makes it fail with the right
message. It reports rather than skips any import form it cannot parse, because a checker that
silently ignores what it does not recognise reports "all clear" for the files it never read.

It is deliberately not a typechecker. A real `tsc` pass would subsume it and is worth doing; it
needs a `tsconfig.json` and a pinned `typescript`, which is a dependency decision, not a gate.

---

## Original TODO 1 — DONE (2026-08-06): four of five candidates are dead, one is not

`pipeline/sim/board-metrics.ts`, all four sessions, 120 rounds with a decided winner and a verified
prefix on both sides. Everything is computed over the verified prefix only, so none of it depends on
the part of the simulation known to diverge. Paired winner-vs-loser AUC through the same
`decideWinner` the forecast AUC uses, with Holm across the five candidates.

| metric | pairs | decided | AUC | p | p (Holm) |
|---|---|---|---|---|---|
| height at garbage | 54 | 50 | 53.7% | 0.672 | 1.000 |
| holes per piece | 120 | 104 | 54.2% | 0.378 | 1.000 |
| well depth | 120 | 114 | 55.0% | 0.303 | 1.000 |
| **downstack rate under pressure** | 54 | 51 | **67.6%** | **0.011** | 0.077 |
| height at end | 120 | 109 | 45.4% | 0.338 | 1.000 |

Four land in the 45–55% band this project already files under "no signal", which is the answer the
item was asking for: **items 3 and 4 (post-garbage divergence, a second simulator) are not justified
by any of them.**

The exception is downstack rate under pressure — rows cleared per piece while garbage is on the
board. Two pre-declared controls were computed in the same run, before the result was read:

- **clear rate with NO garbage on the board: 45.4%** (p=0.343). The winner does not simply clear
  more; the effect is specific to pressure, which is what a confound would not respect.
- **verified prefix length: 59.6%** (raw p=0.033). Exposure is imbalanced — winners' prefixes are
  longer — and that is a caveat, not a refutation, since the metric is a rate per pressure-lock.

Per session the sign is the same in all four (71.9 · 71.9 · 58.3 · 65.0), none individually
significant at 9–15 decided pairs each.

**What it does NOT license.** Holm-adjusted p = 0.077 is not significant, and all four sessions have
now been used, so nothing is held out. This is exploratory. Confirming it needs a NEW session, run
against a pre-registered direction and threshold — the same exploratory/confirmatory split the
forecast metric used, with git as the audit trail. Until then it is a candidate, not a finding, and
it does not earn a column.

### Fallout: a stale cache was feeding the published artifacts

`pairs-cache.json` was keyed on the rule flags and the replay directory but not on the code that
decides the rows. Clause 2 changed `isVerifiedForecast` on 2026-08-05 without bumping `CACHE_V`, so
every consumer kept reading pre-clause-2 rows: the committed `forecast-facts.json` carried
`round AUC p=0.211` on 16 decided pairs while the live classifier scored 0 forecasts for everyone
and therefore tied every pair. Fixed by keying the cache on a sha256 of `forecast.ts`, `sim.ts` and
`verified-prefix.ts`, so a rule change invalidates it without anyone remembering to. All four
artifacts re-emitted. `emit-forecast-facts.ts` now also says "round AUC undecidable — 0 decided
pairs" instead of silently dropping the line when the test has nothing to decide.

---

## Open — 2026-08-07

### 1 — Pre-register `downstack rate under pressure` BEFORE the next session is recorded

The triage above left exactly one candidate alive: rows cleared per piece while garbage is on the
board. Pooled AUC **67.6%** on 51 decided pairs, exact p=0.011, Holm 0.077, same sign in all four
sessions (71.9 / 71.9 / 58.3 / 65.0), and its pre-declared control — the same rate with *no* garbage
on the board — sits at 45.4%, so it is not "clears more" in disguise.

It cannot be strengthened with the data already in this repo. All four sessions were used to find it,
so nothing is held out, and re-reading them is exactly how a 0.077 turns into a 0.03 that means
nothing. The only thing that can move it is a session that does not exist yet — and only if the
prediction predates that session. So it is written down now, in full:

- **Estimand** — paired AUC, winner vs loser, of `downstack rate` exactly as `board-metrics.ts`
  computes it today: rows cleared per piece over locks whose PRE-lock board carries at least one
  garbage row, over the verified prefix only. No re-definition afterwards.
- **Unit** — the player-round, paired by `decideWinner` (the player still alive at the end).
- **Direction** — ONE-SIDED, winner higher. A significant result the other way is a failure, not a
  discovery.
- **Test** — exact sign test over decided pairs, with the decided count always printed beside it.
- **Threshold** — p < 0.05 one-sided **on the new data alone**. Pooling the new session with these
  four is not a confirmation and must not be reported as one.
- **Controls that must also hold** — the calm-clear-rate control stays inside 45–55%, and the
  verified-prefix-length imbalance is reported alongside (59.6%, raw p=0.033 on the exploratory set:
  exposure is not balanced, and that is a caveat carried forward, not a fixed bug).
- **What kills it** — a new session at or below 50%, or the calm control moving with it.

**How much data this actually needs, computed rather than hoped:** the exact sign test needs
≥12 of 15 wins to clear 0.05 one-sided, which at the observed 68% has **24% power**. One session
(9–15 decided pairs) cannot decide this and running it as though it could is how a null gets called
a finding.

| decided pairs | wins needed | power at true 68% | at true 60% |
|---|---|---|---|
| 12 | 10 | 21% | 8% |
| 15 | 12 | 24% | 9% |
| 30 | 20 | 65% | 29% |
| 50 | 32 | 78% | 34% |

So: bank sessions until **~50 decided pairs exist outside the exploratory four** (roughly four more
sessions at the current rate), test once, and report whatever comes out. Anything short of that is
parked, not pending. Nothing here goes in a report until the above is satisfied.

### 2 — The C-Spin negative is bounded by CATALOGUE COVERAGE, not by the matcher

**Updated 2026-08-10: the corpus is five sessions now (358 clean bags), the same null holds, and it
has been shown to survive the set choice — which is what the rest of this item asked for.** See
`pipeline/openers/README.md` for the table. Two things changed:

- **The C-Spin set is worse than "3 openers" suggested.** Not one of the three names `isCSpin`
  selects is the C-Spin as harddrop draws it: `Fake C-Spin {JP: 偽TKI}` is by its own name a fake,
  `Secspin` merely ends in those letters, and the third is a compound page listing `SDPC-Spin`
  among eight names. The set arguably contains **zero** genuine C-Spins, so a null computed over it
  alone was a statement about very little. `openers.test.ts` now asserts the three names, so this
  paragraph fails a test rather than quietly outliving the catalogue.
- **Widening it does not move the answer**, which is the finding that makes the null reportable.
  C-Spin is commonly identified with TKI; `TKI-3 {Alt: TKI}` is catalogued with 12 pages `isCSpin`
  does not select; adding them (6 openers, 24 pages) leaves the nearest bag at **6 cells** and the
  within-4 count at **0**. So the null no longer depends on settling whether C-Spin *is* TKI. Same
  shape for DT Cannon: narrow (6 openers) and widest (48 openers, any name carrying "DT") agree.

What remains true and unfixed is the sentence below.

`pipeline/openers/` establishes: 0 of 358 clean first bags come within four cells of a catalogued
C-Spin. The catalogue behind that sentence is **3 distinct C-Spin openers across 8 drawn pages**, out
of 360 openers and 783 pages. So the claim the repo can make is "**not these C-Spins**". "No C-Spin
anywhere" is not available at any distance threshold, and no amount of tuning gets it.

Better matching code cannot fix this. The matcher already round-trips every C-Spin page it holds,
finds their mirrors, rejects a junk board, and is alignment-checked against a one-row shift. What is
missing is **data**:

- harddrop's own C-Spin page draws setups the community catalogue does not carry —
  `pipeline/sim/wiki-cspin-boards.json` already holds 38 placements parsed from it, in a different
  format, so a converter would widen coverage today;
- the wiki calls C-Spin a **family** ("there are many C-Spin openers", ZST core, vertical and
  horizontal T), which means an enumeration BY CONSTRUCTION — J and L building an overhang over a
  1-wide covered well — would bound the family instead of sampling it;
- `knewjade/solution-finder` enumerates setups satisfying a pattern, and is the right tool for that
  enumeration if it is worth doing.

Until one of those exists, every C-Spin statement in this repo carries the coverage caveat, and
`pipeline/openers/README.md` says so in the same words.

**What the first bag could never answer, and now is answered elsewhere.** Board comparison asks
"did they build this shape", which coverage bounds. The two openers are also distinguishable by
something coverage cannot touch — the ORDER of their two T-spins. DT Cannon (開幕DT砲, "Double
Triple Cannon") is a Double then a Triple; the C-Spin is a Triple then a Double. Over five sessions,
of the 221 verified rounds holding both spins, **221 run the C-Spin order and 0 run the DT order**,
and dropping the verified-prefix window widens it to 277/277 with the split unchanged. That is a
clean separation with no catalogue in it at all, and it is the spine of the new report section
(`pipeline/opener_section.py`, fed by `pipeline/sim/emit-opener-facts.ts`, quarantined outside the
claims chain like the forecast section).

### 2b — The saturation gate has fired, and the decision it defers is now live

**`forecast-saturation.test.ts` held `reactiveRose === 0` over four sessions. On 2026-08-10 it went
to one:** `2026-08-09 pinglamb replay-2 r5 lock 26` rises 1 → 2 slot-locally while the board's
global best does not move, out of 313 reactive events across five sessions. So `improved`'s
global-max gate is losing exactly one forecast today, and the slot-local rewrite the test was
written to force is no longer hypothetical.

**Not done here, deliberately.** Changing `improved` moves every published forecast figure in four
sessions; that is a decision to take on its own terms, not as a side effect of adding an unrelated
metric. The test now pins the riser BY IDENTITY rather than by count, so a second one still fails —
a count can only be updated by writing a bigger number, which is how a gate that found something
becomes a gate that records that something was found.

**How it stayed hidden is the more useful half.** That test's `SESSIONS` admits a session only once
it has a `sim/` directory. 2026-08-09 had none until `opener-facts.json` was written into one, so
the test scanned four sessions while appearing to scan every session present — a corpus defined by
an incidental directory's existence, reporting full coverage. Worth a sweep for the same shape
elsewhere; `pipeline/sim/cross-tslot.test.ts` carries a hardcoded four-session list and has
likewise never seen 2026-08-09.

## T-Spin Forecast — covering the definition's state space (2026-08-08)

A four-agent sweep enumerated the metric's dimensions and cross-tabbed every cell against corpus
instances, fixtures and lemmas. Two commits landed from it (`7b4eb51`, `58378a5`). What follows is
the part that did **not** land: the inventory is the deliverable here, so "cover all possibilities"
is a finite task rather than an aspiration. Roughly a third of it is done.

Every item is marked **measured** (I ran it) or **unverified** (reported by an agent, not reproduced).
That distinction is load-bearing — of the four agent reports, each contained at least one claim that
did not survive checking: a wrong symptom, a wrong file path, a crash misread as a false positive, a
re-derivation of an already-closed finding, and a "surviving" mutant that dies.

### 1 — The two-piece roof: a rule the corpus can NEVER exercise. Highest value.

**measured.** `Math.max(...placers)` (`pipeline/sim/forecast.ts`) is the whole "the roof's most recent
builder is the piece that set up the slot" rule. Censused over all 654 tucked T-spins: **every roof is
exactly one cell, 654 of 654.** So `placers` is a singleton in every real event and the corpus cannot
distinguish `max` from `min` — not now, and not at any corpus size. One fixture exists
(`forecast.test.ts`, provs {1,5}) and it is the only thing killing `metric/roof-oldest-builder`.

Near-forced rather than surprising: a flat T needs a three-wide pocket and covering a second cell
seals its only entry. That makes it permanent, which is exactly why it needs a fixture rather than
more data. Build a second two-placer board where `j` differs between `max` and `min`, and assert the
window, `separation` and clause 2's comparison base all move with it.

### 2 — A mini spin has never been the EXECUTED spin

**measured.** `forecast.ts` admits any `spin !== 'none'`, and `bestTspin` counts minis as available.
Across the four sessions the verified prefix holds **exactly one mini lock**; it cleared lines and is
excluded only by the no-roof filter, never by the spin filter. So: 0 of 654 records, 0 fixtures. The
`mk` helper defaults `spin: 'full'` and the clause-4 loop varies the CLOSING clear's spin, not the
executed one. Any mini/full asymmetry is invisible today.

### 3 — `bestTspinLines` counts pre-existing full rows, and only `Bpre` has any

**CLOSED 2026-08-09 — the count is correct, not a latent bug.** `bestTspin` sets `lines` to the
TOTAL full-row count of the post-placement board, not the rows the T completes. That is the
game-faithful contract: the game clears every full row on lock, so "the lines this T-spin would
clear if it locked here" IS the total full-row count, and reading only the rows the T's own cells
complete would be the wrong number. It never misattributes because `bestTspin` only ever sees a full
row on `Bpre`, and every such row was completed by that step's own placement: `A = boards[t-1]` is
post-clear (never full), `B` and every `avail(t)` board have their full rows removed, and
`Bpre = A + this step's placement` — so the full rows are the placement's. The comment above
`localiseMechanism` ("can only LOWER avail(Bpre)") describes the descent-blocking effect; the
inflating effect it fights with only ever applies to placement-completed rows, so it credits
`placement` exactly rather than by mistake.

Probed on a real TSD to see the two effects: 0 extra full rows -> 2, one -> **3**, two -> **3**,
three or more -> **0** (the rows block the T's descent). Those extra full rows are a constructed
input, not a corpus one — exposure is **1 of 389** events whose causing step clears anything (the
single line-clear event), and even its inflated reading stayed under target, so nothing moves.
`bestTspin`'s doc now states the contract so the "total full-row count" is not re-read as a bug.

### 4 — `forecast_garbage` has no corpus instance and no spec backing

**measured.** 0 of 654 events, 0 with `mechanism = 'garbage'`, 0 with `garbageLoadBearing = true`,
and `roofIsGarbage` false for all 654. The arm rests on three hand fixtures over wiki boards.

`58378a5` establishes why the spec cannot help: `GarbageAmountCannotChangeAnyGap` proves two steps
clearing the same rows and differing only in `garbageRows` are indistinguishable to every gap-based
predicate, so **the model cannot adjudicate this branch in either direction** — it fires on garbage
CONTENT and `Step` has no hole column. `GarbageAloneCannotMakeAForecast` is not a refutation of it.
Adjudicating it needs `Step` to carry the hole column per inserted row, which is a model change.

Related and open: `garbageLoadBearing` is vacuous. Garbage arrives in-window in **121 of 654** events
and the flag is true in 0, so the corpus test asserting classifier/oracle agreement asserts `0 === 0`.
It needs the anti-vacuity treatment `property-forecast.test.ts` already applies elsewhere.

### 5 — Clause 2 `'undetermined'` has never reached a forecast kind

**measured.** `undecidedClause2` and the emitted `clause2_undecided` are 0 in all four artifacts. The
verdict is unit-tested but the reporting path that exists to stop a zero rate hiding an undecidable
case has never carried a non-zero value.

### 6 — Clause 3 is still witness-only

**measured.** Clauses 2 and 4 each have a universal `...IsNotAForecast` lemma; `58378a5` added clause
1's (`NotASpinIsNeverAForecast`). Clause 3 has none — nothing states `!GapClosed ==> !IsForecast`, and
`GapClosesOnlyByClearsBetween` / `GarbageNeverClosesAGap` are both single-step. Three proposals, in
dependency order:

- `GapEqualsRowsRemovedBetween` — lift the header's identity to a window of any length. Induct via
  `TrackSplit` / `RemovedBetweenSplit` with `h` symbolic, so the three-step ground blow-up does not
  apply. Needs `CountBetweenIsDistinctCount` (landed) as a prerequisite.
- `Clause3FollowsFromClause4` — turns the prose claim that `GapClosed` is redundant beside clause 4 at
  `minLines >= 1` into a theorem. One-line corollary of the above.
- `NothingRemovedIsNotEvenForecastShaped` — clause 3's first universal; strictly generalises
  `GapClauseIsLoadBearingAtZero` and the `minLines == 0` case `GarbageAloneCannotMakeAForecast` excludes.

### 7 — Modelling `improved` in Dafny is BLOCKED, not pending

**measured, from the codebase's own words.** It needs `BestTspinLines` as a max over reachable
placements; a finite max needs a bounded position set; `forecast.ts` states outright that the ROW
coordinate is not bounded by the engine (`vendor/core/srs.ts` is `if (row < 0) continue`), that the
`4*10*42 = 1680` bound is an ASSUMPTION resting on kick-table reasoning "nobody has turned into a
proof", and that `h < 40000` is "a LIVE belt rather than dead code". Discharging that boundedness
lemma is the prerequisite; until then the spec's clause 3 and the implementation's are different
predicates and the repo should keep saying so.

### 8 — Two sources of truth for "was a spin"

**measured.** In every witness in both spec files `e.spinAtK == true` while `h[e.k - 1]` has
`wasSpin == false`, and nothing relates them. More broadly `WellFormed` never relates `spinAtK`,
`holeOpenAtJ`, `roofAt` or `floorAt` to `h` at all — clauses 1 and 2 have **zero history-side
content**, so the spec can prove the predicate reads those flags and never that a flag is right. The
corpus result turns on clause 2, which is one of the two.

### 9 — The spec mutation suite is 15 killed + 1 unresolved, not 16/16

**measured.** `58378a5` made `mutate-forecast-spec.sh` read the verifier's output instead of its exit
code, because Dafny exits 4 on a TIMEOUT and the harness scored that as a kill. It immediately
reclassified "gap test inverted (>= not <)", which times out at the default and resolves to KILLED at
`DAFNY_TIME_LIMIT=300`. Either speed that obligation up or run the suite at the higher limit in CI; a
standing TIMEOUT is an unread survivor.

### 10 — Unverified, carried from the sweep so they are not lost

Neither was reproduced. Do not act on them without checking first.

- **Negative-row slots.** `bestRows` appends `min(rows) - 1`, so a slot topping at row 0 yields roof
  row -1; `back(-1)` then finds no match and returns -1, and the straddle test would admit every
  cleared row below the slot's bottom — over-attribution to `'line-clear'`. Claimed 0 of 7,579 boards
  observed, constructible.
- **Three unreachable guards** that survive mutation: `avail(t) >= target` at the garbage branch (the
  walk's exit condition may already establish it), `if (!slot)` after a positive `bestTspinLines`, and
  the `t <= j` early return. If genuinely unreachable they want deletion or a comment, not a mutant.

### 11 — Decision, not a task: does `insertMode` join the swept configs?

**measured.** `insertMode: 'immediate'` is legal, is used by `coverage-strict.ts` and
`triage-garbage-totals.ts`, and is not among the seven swept. Before `7b4eb51` it returned **13
verified forecasts** across the four sessions (2.83%) against 0.00% for `best`, every one
`mechanism: 'garbage'` with `garbageLoadBearing: false`. It now throws 20 times instead, and all seven
swept configs are unaffected. So the metric no longer reports a number it cannot justify — but the
published 0% is still a claim about seven configs, and whether that set is the right one is an
editorial call about what the figure asserts, not a bug.

## T-Spin Forecast — inventory resolved (2026-08-09)

A parallel expert sweep (four implementation agents + a fable-model reviewer + a read-only
verifier) worked the inventory above. Three commits landed: `33b233b` (sim fixtures + mutants +
the j=-1 fix), `6866f7a` (spec + the spec's first CI job), `5cc6573` (a numerator bug the
inventory could not see). Every agent claim was reproduced on the main thread before landing;
several did not survive that check and are called out below.

### Closed

- **1 — two-piece roof.** Second multi-placer fixture whose *answer* moves with max-vs-min, not
  just an intermediate. With both it and the provs-{1,5} fixture skipped, the max→min mutant
  survives the whole corpus — the "no corpus can distinguish them" claim, now measured, not argued.
- **2 — mini executed spin.** No asymmetry exists (nothing reads `lk.spin` but the admission test
  and the record's field); the identity is pinned so a future asymmetry fails, and it is the right
  answer — clause 4 already refuses a size exemption at the other end of the window.
- **4b — `garbageLoadBearing` vacuity.** Reachable: 288 constructed cases, 144 load-bearing via a
  landing shift, 144 not. The corpus's 0 is now asserted against a population where the flag is
  true, not `0 === 0`. Reproduced the 121/654-and-0 census independently.
- **5 — clause 2 `'undetermined'`.** Constructed end to end by the strict rule; `undecidedClause2`
  carries 1 for the first time.
- **6 — clause 3 universals.** `GapEqualsRowsRemovedBetween` (any-length window),
  `Clause3FollowsFromClause4`, `NothingRemovedIsNotEvenForecastShaped`. One correction to the
  inventory: clause 3 is **not** unconditionally redundant beside clause 4 at `minLines >= 1` —
  only given `BothSurvive`; the old `IsForecastShape` comment claimed the stronger thing and was
  provably imprecise.
- **8 — grounding `spinAtK`.** `WellFormed` now requires `spinAtK == h[k-1].wasSpin`. This exposed
  that `OnlyClause1SeparatesAFromF` was green only because the flag floated free of the history; 17
  witnesses carried the same defect. Fixed all without weakening the invariant.
- **9 — spec mutation suite.** Root cause was the harness testing timeout before error (a mutant
  with nine proved errors behind one slow obligation scored as a whole-file timeout). Fixed, and
  the obligation sped up. 18/18 killed, was 15 + 1 unread timeout.
- **The numerator blind spot (new, not on the list).** Four published reports carried a split-half
  reliability from the superseded `kind !== 'reactive'` numerator; under the live metric the figure
  does not exist. Fixed, re-emitted, and closed with a source scanner + an artifact test, both of
  which fail on the pre-fix artifact. This is the class the inventory structurally could not see:
  every item asked "is each cell of the definition exercised?", none asked "does every published
  figure come from this definition?". See `5cc6573`.
- **Item 10 — refuted, not fixed.** Claim A (negative roof rows) is a **non-bug**: the negative
  bound is the correct generalisation and clamping it would regress the straddle test — a comment
  records why, no code change. Two of the three "unreachable guards" are reachable via the exported
  `localiseMechanism` and got mutants + contract fixtures rather than deletion; the third is
  provably unreachable and got a comment. The census is **7,544 boards, not 7,579** (7,544 matches
  project memory; the inventory's figure was the outlier). The `j = -1` crash the sweep surfaced is
  fixed (it read `boards[-1]`, contradicting its own doc comment; 0 corpus exposure).

### Re-classified (fable-model review; not yet actioned)

- **3 — `bestTspinLines` counts pre-existing full rows — CLOSED, the count is correct** (fable
  reversed its own "recommend fixing" on second look; the main thread had already reverted the code
  change). Measured under a patched classifier over 654 events × 6 configs: **zero classification
  changes, zero rate changes**. The reversal: counting every full row of the resulting board IS the
  contract — `bestTspin.lines` is "the lines this T-spin would clear if it locked here", and the game
  clears every full row on lock, not "the rows the T's own cells complete". `bestTspin` only ever
  sees a full row on `Bpre`: `A = boards[t-1]` is post-clear so never full, and `B` and every
  `avail(t)` board have their full rows removed, so every full row in `Bpre = A + this step's
  placement` was completed by THAT placement — crediting `placement` is exact, not an artifact.
  Subtracting the pre-existing count would be identity on every corpus board and would BREAK the
  contract on the constructed boards where it is not, so nothing is subtracted. Verified against
  `localiseMechanism` source before closing; `bestTspin`'s doc now carries the contract line.
- **7 — modelling `improved` was NOT blocked.** The premise "a finite max needs a bounded position
  set" is false: `BestTspinLines` is a max over LINE COUNTS, bounded by 3, regardless of the
  position set's size. Cheap path (hours): add `availAtJ`/`availAtK: nat` to `Event` (exactly like
  the two flags already there, `<= 3`), prove `Improved` and `GapClosed` are *different* predicates
  with two witnesses + an anti-vacuity witness. No boundedness lemma. This matters: `improved`
  performs 653 of 654 corpus exclusions and is the single largest unmodelled thing.
- **11 — `insertMode`, keep seven not eight.** Four *other* legal garbage-timing configs
  (`cancelMode:inTransit`, `readyFrom:confirm`, `garbagespeed:0`, `insertAfterClear`) all measure 0
  without throwing, which strengthens the 0%. But the published `simulator_range [0,0]` is over seven
  configs, six of which vary piece kinematics and only one touches garbage — the axis the metric is
  actually about. Recommend: add the four that run (free, all 0), and emit the `insertMode`
  exclusion as data (`simulator_configs_excluded`) rather than dropping a throwing config silently.

### Consolidated

- **4 (main) + 8 (clause 2) are one model change.** Grounding `holeOpenAtJ`/`roofAt`/`floorAt` and
  adjudicating `forecast_garbage` both need a board-carrying `Step` (column information, which
  `Step` has none of today). Grounding clause 2 strictly subsumes `forecast_garbage`: clause 2 needs
  to know which cells each *placement* filled (`roofIsGarbage` is false for all 654), of which
  garbage hole columns are a subset. Driver is clause 2. Cheaper than it sounds — `Cell`, `Board`,
  `Filled`, `Width` are already declared in `Forecast.dfy` and referenced by nothing (dead today).

### New, carried so they are not lost

- **`roofIsGarbage` anti-vacuity — CLOSED 2026-08-09.** Was 0 of 654 with no fixture, same vacuity
  class as 4b. Unlike `garbageLoadBearing` it gates no classification — it is the diagnostic
  `run-forecast.ts` prints as "roof literally IS garbage (strongest signal)" — so the fix is one
  discriminating pair rather than a population: `roofOwner: -1` (garbage overhang) → true,
  `roofOwner: 2` (built) → false, both non-empty, mutation-checked (hardcoding the flag false fails
  the test). `forecast.test.ts`.
- **`determinable` degrades silently at `j = -1`.** Even with the crash fixed, a garbage roof has
  `determinable === false`, so the strict clause-2 rule falls back to loose co-occurrence there.
- **Layer 1 of the numerator gate is deferred.** A branded `VerifiedCount` type would make a
  hand-rolled numerator a *compile* error rather than a scanner finding — the right fix — but this
  tree has no typechecker (no tsconfig, no tsc step; `check_ts_imports.py` is the homemade stand-in).
  Its true cost is "adopt a typecheck step for the whole TS tree", a separate decision.

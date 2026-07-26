# tetrio-replay-report — operating context

Public repo: <https://github.com/yachi/tetrio-replay-report> · Site: <https://yachi.github.io/tetrio-replay-report/>

Turns a batch of TETR.IO `.ttrm` replays into a Cantonese match report where every
factual sentence is badge-linked to a Dafny-verified lemma. Two sessions so far
(2026-07-22: yachi 6:4 · 2026-07-24: pinglamb 4:3), 129 rounds, 106 hand-written +
153 generated claims.

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

## Commands

```bash
bin/new-session sessions/<date> <replay-dir>   # extract → claims → Dafny → verify → proof map
bin/verify-session sessions/<date>/report      # re-run all gates (MUTATION=1 adds mutation test)
bin/build-docs                                 # regenerate docs/ (the Pages site) from sessions
python3 -m pipeline.build_report sessions/<date>/report         # regenerate the derived report sections
python3 -m pipeline.build_report sessions/<date>/report --check # CI gate: fail if they drifted from facts.json
python3 -m pipeline.check_prose_figures sessions/<date>/report   # CI gate: every 約-figure is floored
python3 -m pipeline.check_proof_links sessions/<date>/report      # CI gate: every badge's lemma exists
python3 -m pipeline.build_round_table sessions/<date>/report   # regenerate the 逐局全數據 section
python3 -m pipeline.claims.build_claims <facts> --out <ledger> # generated ledger
python3 -m pipeline.codegen <facts> --claims <ledger> --outdir <dir>
python3 -m pipeline.claims.equiv <facts> --hand <ledgers...>   # coverage by exhaustive mutation
```

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

## What the data actually says (measured, not asserted)

Paired AUC over 129 rounds — how often the round's winner held the higher value:

- **Strong**: VS 100% · APM 94.6 · 攻 93.8 · APP 91.5 · 送 88.0 · 射埋 12.0 (88 inverted) ·
  食 14.3 · 分 85.3
- **No signal**: COMBO 45.0 · PC 50.8 (89% zeros) · TST 55.8 · TSD 60.9 · KPP 39.9
- Near-constant (CV 0.05): KPP, FIN% — their flatness is the finding, not a column of numbers

Coaching conclusions, cross-validated over both sessions: **APP is the lever** (17–24% higher
in rounds won, both players, both sessions); **DS matters** in 3 of 4 player-sessions;
**KPP is flat** (0–2%) — reported as a negative result. When adding a column or a claim, run
`pipeline/claims/equiv.py` or the AUC probe rather than assuming a stat is informative.

## Front-end traps in report.html (each one shipped a silent bug)

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

1. Two `innerHTML` sites left in `report.html` concatenate into markup: the appendix row
   builder, and the badge-prose expander. The expander is legitimate — card and lede prose is
   authored HTML — so the real target is the appendix builder, which the P5 appendix section
   will replace anyway. (The match-card score was the third; it now builds nodes.) Re-verify
   the 110 badge count and 52 appendix rows after touching either.
2. ROADMAP P5, in progress. Generated so far (`pipeline/build_report.py`, CI-gated with
   `--check`): the hero/scoreboard, 全場之最, the `chart-data` island, and the `match-copy`
   island. Still hand-built: the coaching section and the appendix. Add each as a new entry
   in `SECTIONS`; the marker region and the drift gate come for free.

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

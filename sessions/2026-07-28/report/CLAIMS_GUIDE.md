# Claims for this session

This session does **not** use the hand-written `python_check` ledger format that
`sessions/2026-07-22` and `sessions/2026-07-24` use (their copies of this file describe it,
and their hand claims are proved by a session-local ~500-line `codegen_dafny.py`).

Here there are two ledgers and neither is typed by hand:

| File | Built by | Claims |
|---|---|---|
| `claims-generated.json` | `python3 -m pipeline.claims.build_claims facts.json --out claims-generated.json` | 71 |
| `claims-narrative.json` | `python3 -m pipeline.claims.build_hand hand_claims.py --facts facts.json --out claims-narrative.json` | 12 |

Both carry a `spec` — a nested dict in the predicate algebra of `pipeline/claims/spec.py` —
and never a hand-written predicate string. The spec renders to all three backends:

- **Python** (`to_python`) → the `python_check` the gate evaluates
- **Dafny** (`to_dafny`) → the `ensures` of an empty-bodied lemma in `dafny/Claims.dfy`
- **SMT-LIB** (`pipeline/claims/smt.py`) → one `push`/`assert not`/`check-sat`/`pop` in `claims.smt2`

so what Python evaluates, what Dafny proves and what a solver refutes cannot drift apart.
Both ledgers compile into one `Facts.dfy` / `Claims.dfy` and one `claims-proof-map.json`
covering all 83 lemmas.

## Adding or editing a claim

Edit `hand_claims.py`, then regenerate and re-verify:

```bash
cd "$(git rev-parse --show-toplevel)"
W=sessions/2026-07-28/report
python3 -m pipeline.claims.build_hand $W/hand_claims.py --facts $W/facts.json --out $W/claims-narrative.json
python3 -m pipeline.codegen $W/facts.json --claims $W/claims-generated.json $W/claims-narrative.json --outdir $W/dafny
python3 -m pipeline.build_proof_map $W/claims-generated.json $W/claims-narrative.json --dafny-dir $W/dafny --out $W/claims-proof-map.json
python3 -m pipeline.codegen_smt $W/facts.json --claims $W/claims-generated.json $W/claims-narrative.json --out $W/claims.smt2
bin/verify-session $W
```

Two things that bite:

1. **`english_gloss` is the lemma name.** Editing a gloss renames the lemma and strands every
   badge that links to it, while the verifier still reports 0 errors. Rebuild the proof map
   after any gloss change; `pipeline/check_proof_links.py` is the gate.
2. **Windows of different sizes are compared as rates, never as sums.** Matches 1-2 hold 15
   rounds and matches 3-8 hold 49, so every windowed claim here cross-multiplies into an
   integer inequality (`rate_gt` / `rate_lt` in `hand_claims.py`).

Wording rules (口語廣東話, traditional characters only, 約 means the *floored* value, 射埋 vs 食
never conflated, anything countable needs a claim id) are unchanged — `build_hand` runs the same
validation as `build_claims`, and `pipeline/check_prose_figures.py` gates the figures.

Field semantics (`garbage_events` vs `garbagereceived`, `lifetime` in milliseconds, the raw
`tspins` counter including spins that cleared nothing) are documented in `SCHEMA.md` and in the
repo's `CLAUDE.md`.

# facts.json — EXACT schema (both extractors MUST produce semantically identical JSON)

Input: the 8 `*.ttrm` files in the parent directory (`..` relative to this file).
Output: valid JSON. Key order/whitespace irrelevant (gate compares via `jq -S`). ALL numbers MUST be integers — no floats anywhere.

## Rounding rule (mandatory, exact)
For any float `v` scaled to an int: `x1000 = floor(v * 1000 + 0.5)` computed in IEEE-754 double arithmetic (Python: `math.floor(v*1000+0.5)`; JS: `Math.floor(v*1000+0.5)`). Do NOT use Python round() (banker's) or any decimal library.

## Ordering rules
- `matches`: sorted by numeric file suffix; `replay-2026-07-24-1.ttrm` = index 1 … `replay-2026-07-24-7.ttrm` = 7 (numeric suffix IS the index; there are exactly 7 files).
- `rounds`: in file order (array order of `replay.rounds`).
- `garbage_events`: in the order they appear in the player's `replay.events` array.

## Structure

```jsonc
{
  "players": ["yachi", "pinglamb"],          // fixed, this exact order
  "matches": [
    {
      "index": 1,                            // 1..10 per file-suffix rule
      "file": "replay-2026-07-22-.ttrm",
      "ts": "<top-level ts string verbatim>",
      "winner": "<username with max leaderboard wins>",
      "score": { "yachi": <wins>, "pinglamb": <wins> },   // from replay.leaderboard[].wins
      "leaderboard": {
        "<username>": {
          "wins": int,
          // A leaderboard entry has no aggregatestats, so these three stay on the live tick
          // while the per-round ones below are results-time. Round sums therefore do NOT
          // reconcile against these; that is a stated decision, not an oversight.
          "apm_x1000": int,                  // from leaderboard[].stats.apm
          "pps_x1000": int,
          "vs_x1000": int,                   // stats.vsscore
          "garbagesent": int,
          "garbagereceived": int,
          "kills": int
        }
      },
      "rounds": [
        {
          "index": 0,                        // 0-based array position
          "winner": "<username of the player object with alive == true>",
          "players": {
            "<username>": {
              "lifetime": int,               // player.lifetime (MILLISECONDS — verified empirically vs pieces/pps)
              "alive": true|false,           // player.alive
              // ---- rates: from player.replay.results.aggregatestats, the FINAL snapshot ----
              // NOT player.stats, which is a live in-game tick and predates the round's end in
              // 183 of 760 player-rounds (181 of them the round winner, APM too high in 172).
              // Only aggregatestats satisfies vs*60*attack == apm*100*(attack+cleared).
              "apm_x1000": int,              // player.replay.results.aggregatestats.apm
              "pps_x1000": int,              // player.replay.results.aggregatestats.pps
              "vs_x1000": int,               // player.replay.results.aggregatestats.vsscore
              "garbagesent": int,            // player.stats.garbagesent
              "garbagereceived": int,        // player.stats.garbagereceived
              "kills": int,                  // player.stats.kills
              // ---- from player.replay.results.stats ----
              "lines": int,
              "pieces": int,                 // piecesplaced
              "inputs": int,
              "holds": int,
              "topcombo": int,
              "topbtb": int,
              "tspins": int,
              "clears": {                    // from results.stats.clears (rename keys)
                "singles": int, "doubles": int, "triples": int, "quads": int,
                "tspin_singles": int,        // tspinsingles
                "tspin_doubles": int,        // tspindoubles
                "tspin_triples": int,        // tspintriples
                "mini_tspin_singles": int,   // minitspinsingles
                "mini_tspin_doubles": int,   // minitspindoubles
                "allclear": int
              },
              // ---- from results.stats.garbage ----
              "garbage_attack": int,         // garbage.attack
              "garbage_cleared": int,        // garbage.cleared
              "maxspike": int,               // garbage.maxspike
              // ---- from results.stats.finesse ----
              "finesse_faults": int,         // finesse.faults
              "finesse_perfect": int,        // finesse.perfectpieces
              // ---- incoming garbage timeline ----
              "garbage_events": [            // events where type=="ige" AND data.type=="interaction_confirm" AND data.data.type=="garbage"
                { "frame": int,              // data.frame (the ige-level frame, NOT outer event frame)
                  "amt": int }               // data.data.amt
              ]
            }
          }
        }
      ]
    }
  ]
}
```

## Notes
- Exactly 2 players per round; usernames come from the round player objects.
- If a documented field is missing/null in some round, use 0 — and print a warning line to stderr listing file/round/field (warnings go in your report, not the JSON).
- Do not add any extra keys. Do not compute derived values (averages, totals) — raw per-round facts only.

## Extended per-round fields (added 2026-07-25)

Everything below is also emitted per round player. These come from
`replay.results.stats` and are what the in-game end screen leaves out.

```jsonc
"score": int,                  // results.stats.score — in-game score
"finesse_combo": int,          // finesse.combo — longest run of perfect placements
"combo_power": int,            // combopower
"btb_power": int,              // btbpower
"garbage_sent_raw": int,       // garbage.sent (after multipliers)
"garbage_sent_nomult": int,    // garbage.sent_nomult (before multipliers)
"maxspike_nomult": int,        // garbage.maxspike_nomult
"garbage_received_raw": int,   // garbage.received (results-level counter)
"finaltime_ms": int,           // results.stats.finaltime, floor(v + 0.5) — exact game length
"gameoverreason": str,         // results.gameoverreason: "winner" for the survivor,
                               // "garbagesmash" or "topout" for the player who died
"clears": {                    // in addition to the fields above
  "mini_tspin_triples": int,   // minitspintriples
  "tspin_quads": int,          // tspinquads
  "pentas": int,               // pentas
  "real_tspins": int,          // realtspins
  "mini_tspins": int           // minitspins
}
```

Notes
- `garbage_sent_raw` minus `garbage_sent_nomult` is the damage that came from
  multipliers rather than raw sends.
- `gameoverreason` is a string, so claims about it use the string-field cond in the
  spec algebra rather than integer arithmetic.
- `finaltime_ms` is the engine's own duration and agrees with `lifetime` to within a
  frame; `lifetime` remains the field the duration claims use.
- Derived rates used in the report (not stored, computed from the above): APP =
  `garbage_attack / pieces`, KPP = `inputs / pieces`, DS = `garbage_cleared / pieces`,
  finesse rate = `finesse_perfect / pieces`.

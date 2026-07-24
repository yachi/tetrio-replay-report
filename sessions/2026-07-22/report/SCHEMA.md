# facts.json — EXACT schema (both extractors MUST produce semantically identical JSON)

Input: the 10 `*.ttrm` files in the parent directory (`..` relative to this file).
Output: valid JSON. Key order/whitespace irrelevant (gate compares via `jq -S`). ALL numbers MUST be integers — no floats anywhere.

## Rounding rule (mandatory, exact)
For any float `v` scaled to an int: `x1000 = floor(v * 1000 + 0.5)` computed in IEEE-754 double arithmetic (Python: `math.floor(v*1000+0.5)`; JS: `Math.floor(v*1000+0.5)`). Do NOT use Python round() (banker's) or any decimal library.

## Ordering rules
- `matches`: sorted by numeric file suffix; `replay-2026-07-22-.ttrm` = index 1, `-2.ttrm` = 2, … `-10.ttrm` = 10.
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
              "apm_x1000": int,              // player.stats.apm
              "pps_x1000": int,              // player.stats.pps
              "vs_x1000": int,               // player.stats.vsscore
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

# Claims ledger rules (claims-*.json)

Every factual claim that will appear in the final report MUST be an entry:

```jsonc
{
  "id": "C001",                       // A1 uses C0xx, A2 uses R0xx (recommendations' supporting facts)
  "canto": "yachi 十場入面贏咗六場",   // 口語廣東話, exactly as it may appear in the report
  "english_gloss": "yachi won 6 of 10 matches",
  "category": "score | pace | attack | clutch | style | finesse | duration | spike | comeback",
  "python_check": "sum(1 for m in facts['matches'] if m['winner']=='yachi') == 6"
}
```

## Hard rules
1. `python_check` is a single Python expression over the dict `facts` (= parsed facts.json). It MUST evaluate to `True`. Verify EVERY check yourself by running it against facts.json before returning; a claim whose check fails or errors must be fixed or dropped.
2. Integer arithmetic preferred. Rates are stored ×1000 (`apm_x1000` etc.). For averages/comparisons compare scaled sums exactly, e.g. "yachi 平均 PPS 高過 pinglamb": compare `sum(pps_x1000)*<n_other>` vs cross-multiplied — avoid float division in checks (cross-multiply instead). If the Cantonese states a rounded number, use 「約」 and make the check assert exact bounds, e.g. `51000 <= x < 52000` for 「約51」.
3. Semantics you MUST respect:
   - `garbage_events` = incoming attack QUEUED at the player (frame-stamped, pre-cancellation). It is NOT garbage received. Leaderboard `garbagereceived` = actually materialized. Sums differ ~10-20%. Word claims accordingly (「射埋嚟嘅攻擊」 vs 「真係食咗嘅垃圾行」).
   - `lifetime` is in MILLISECONDS (verified empirically: pieces/pps cross-check, 0.4% median error; session range 15.1s–228.3s). Seconds = lifetime/1000 → use 「約X秒」 with a bounds check on the raw ms integer.
   - `maxspike` = biggest single spike dealt by that player in that round.
   - Round winner = the player with `alive == true`.
   - `x1000` fields were rounded with floor(v*1000+0.5) — a claim like 「APM 52.9」 should say 約 and bound-check the x1000 int.
4. No claim may require board-state reconstruction (piece positions, board height). Stats/events fields only.
5. Subjective color (「殺到眼都紅」) is allowed in narrative text but must not contain numbers or comparatives; anything countable needs a claim id.
6. Output claims as a JSON array in your assigned file. Also output a companion .md with your narrative/recommendations, where each sentence that uses a claim references its id like: 「……贏咗六場 [C001]」.

## Session facts already gate-verified (you may reuse, still write claims for them)
- Match wins: yachi 6, pinglamb 4. Round wins: yachi 43, pinglamb 36. Total rounds 79. 10 matches, all first-to-5.
- Matches went 5-4 (deciders): m2 (pinglamb), m3 (pinglamb), m10 (yachi).
- Match winners in order 1..10: yachi, pinglamb, pinglamb, yachi, yachi, yachi, pinglamb, yachi, pinglamb, yachi.

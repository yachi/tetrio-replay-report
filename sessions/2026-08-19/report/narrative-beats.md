# 2026-08-19 — narrative beats

Seventh session. **pinglamb 7 : yachi 3** over 10 matches and 70 rounds.

Every beat below names the claim that pins it. Nothing goes into the report that does not.
Anything that would need to range over more than this one session's `facts.json` is
listed at the bottom under "dropped" — a claim's spec covers exactly one session, so a
cross-session count is unbadgeable by construction and must not appear as a countable
statement in the body.

---

## 1. The shape of the night

pinglamb 7:3 [G001]; rounds 42:28 [G002]. yachi won matches 1, 4 and 7; pinglamb won the
other seven, including the last three [C001]. Per-match scores are [G004]–[G013], and the
whole score table is one claim [G060].

Round-by-round, each match is pinned in its own claim [C009]–[C018]:

| m | rounds | sequence (Y = yachi) | score | claims |
|---|---|---|---|---|
| 1 | 8 | P Y Y Y P Y P Y | 5-3 Y | C009 · G004 |
| 2 | 6 | Y P P P P P | 1-5 | C010 · G005 |
| 3 | 5 | P P P P P | 0-5 | C011 · G006 · G014 |
| 4 | 8 | Y P P Y Y Y P Y | 5-3 Y | C012 · G007 |
| 5 | 7 | Y P P P Y P P | 2-5 | C013 · G008 |
| 6 | 7 | Y P P P Y P P | 2-5 | C014 · G009 |
| 7 | 6 | Y Y Y Y P Y | 5-1 Y | C015 · G010 |
| 8 | 6 | P P Y P P P | 1-5 | C016 · G011 |
| 9 | 9 | P Y P P Y Y Y P P | 4-5 | C017 · G012 · G015 |
| 10 | 8 | Y P P P P Y Y P | 3-5 | C018 · G013 |

**C017's own gloss is wrong and the prose does not follow it.** Its Cantonese says yachi
「連贏三局追到 4 比 4」 and its `english_gloss` says "won three straight to level at 4-4".
The running score after those three rounds is **4-3 to yachi** — he took the lead, he did
not level; the match only reached 4-4 after pinglamb won round 8. The predicate is the
nine-round winner sequence, which is correct and entails the right reading, so the lemma is
sound and the *gloss beside it* is not. Every mention in the report says 「由 1 比 3 連贏
三局反超做 4 比 3」 instead. `hand_claims.py` is outside this task's write scope, so the
canto and gloss still need fixing at source — and because `codegen` builds lemma names from
`english_gloss`, that edit renames C017's lemma and strands its badge until the proof map is
rebuilt.

Matches 5 and 6 run the identical sequence — first and fifth rounds only, 2-5 both times
[C013] [C014]. One sweep, m3 [G014]; one match decided in its final round, m9 [G015].
The longest streak of the night is pinglamb's ten rounds running from m2 into m3 [G016].

**Not a beat: the spacing of yachi's three wins.** m1, m4, m7 is an arithmetic progression.
P(three wins land on *some* evenly spaced set of ten) = 20/120 = 0.167 — a one-in-six
coincidence with no mechanism and no lemma. It is not mentioned anywhere in the report,
not even as a gesture.

## 2. The finding: the ceilings are near, the floors are apart

Split all 70 rounds by who won them and pool attack over pieces [C002] [G068] [G069]:

```
rounds won     yachi ~0.68    pinglamb ~0.72   → pinglamb +6-7%    [C002]
rounds lost    yachi ~0.55    pinglamb ~0.61   → pinglamb +11-12%  [C002]
```

Both figures are ranges because that is what the claim proves — a two-sided `between`, not
a point estimate. Quote the range, never a midpoint.

Said within a player [C003]: yachi separates his own won and lost rounds by 23-24%,
pinglamb by 17-18%. **yachi is the one who swings more**, which is the opposite of the
reading a reader expects from a 3:7. He is not flat; he is unstable, and the instability
is on the downside — his losing rounds are where the gap opens.

Over the whole session pinglamb's attack per piece is 12-13% above yachi's [C004]. That
single number is the one that tells you least: it is an average over two regimes that are
6-7% and 11-12% apart, so it names neither.

## 3. The per-match separation is the sharpest thing in the data

[C007]: in each of the three matches yachi won, pinglamb's attack per piece is **under 1%**
above his. In each of the seven pinglamb won, it is **over 11%** above. Nothing lands in
between — the gap in the middle is the story.

**Do not write this as a sign test.** "yachi won the matches where his APP was higher" is
FALSE: m4 is a yachi win with pinglamb still ahead (by under 1%). A lemma worded that way
was tested and fails to verify. The correct wording is the separation: his three wins are
the three closest matches on attack per piece, and there is no match in the 1-11% band.

## 4. The volume route, again

yachi placed 312 more pieces than pinglamb yet landed 236 less attack — 6-7% of pinglamb's
total [C005]. Supporting totals: pieces 5975 to 5663 [G031], attack 3851 to 3615 [G032],
per-round PPS ~1.41 to ~1.35 [G042], per-round APM ~56.9 to ~51.2 [G043], per-piece attack
pinglamb ahead [G044].

## 5. What is NOT the mechanism this time

- **Deaths are nearly even.** Seven rounds ended in a topout, four yachi's and three
  pinglamb's [C006]; the other 63 ended on garbage [G066]. Whatever separated these two,
  it was not one of them stacking himself out.
- **Inputs are the flattest column in the session.** KPP 3.628 to 3.639, under 0.3% apart
  [C008]; yachi is the marginally cheaper of the two [G065]. Within each player, KPP moves
  under 2% between won and lost rounds [G070] [G071] — it does not decide a round for
  either of them.
- **Perfect Clears do not decide rounds.** 5 each [G040]; yachi 5 rounds with one, won 2
  [G078]; pinglamb 5 rounds, won 2 [G080]. Eight rounds had exactly one player with a
  perfect clear and that player lost five of them — yachi 4 solo rounds, lost 2 [G079];
  pinglamb 4 solo rounds, lost 3 [G081]. Counts only; the denominators are 4-5 rounds and
  a percentage over four rounds reads far more confident than the data is.

So the report has an unusually clean negative: the two players do the same amount of work
per piece [C008], die about equally often [C006], and clear almost exactly the same amount
of garbage in total (1184 to 1183) [G033]. What differs is what a piece buys [C004].

## 6. Rounds and records worth a card

- **m8 round 2 — the night's most intense round** [G064], combined VS ~313.5. Both rate
  records are in it: pinglamb's single-round APM ~80.7 [G017] and VS ~171.8 [G018], both
  over the 24 rounds that ran a full minute. The deep-dive numbers are [G082] (yachi) and
  [G083] (pinglamb); pinglamb won it while trailing on lines and on downstacking [G084],
  attack per piece ~0.929 to ~0.669 [G085], downstack per piece ~0.256 to ~0.348 [G086].
- **m9 round 1 — 12 seconds** [G025], the shortest of the night; pinglamb ate zero garbage
  [G062] and threw the session's biggest single spike, 25 lines [G019]. His APM in it,
  ~122.6, is the session's unqualified peak and is explicitly *not* a record — a 12-second
  denominator [G076]. Same for yachi's ~205.6 VS in m4 round 6, over ~21 seconds [G077].
- **m9 round 7 — 158 lines**, the session's highest single-round clear count, yachi's
  [G023]. It is the last of the three straight rounds that took him from 1-3 to a 4-3
  lead; pinglamb then took rounds 8 and 9 [C017].
- **m1 round 5 — ~172 seconds** [G024], the longest round; pinglamb survived it.
- **m10 round 7 — the hardest hold** [G028]: yachi took 124 lines of incoming against
  pinglamb's 94 and won anyway.
- **m6 round 5 — B2B 9** [G021], yachi's, the session's longest chain; **m3 round 4 —
  combo 8** [G020], pinglamb's; **m6 round 2 — 15 T-spins** in one round [G022],
  pinglamb's, counting spins that cleared nothing.
- **m8** carries the highest match-level APM, pinglamb's ~65.0 [G026]; **m3**'s sweep came
  with a match-average APM gap of more than 10 [G059].

## 7. Dropped for lack of a lemma

Each of these is true and measured elsewhere in the repo, and none of them can carry a
badge, so none appears in the body:

- Anything comparing this session to another: "the third night the volume route failed",
  "the most even topout split of the corpus", "KPP flat for a seventh session", every AUC
  figure, the won-gap/lost-gap series across sessions. A claim's spec ranges over one
  `facts.json`; there is no operator that reaches a second one.
- The ceiling-vs-floor cross-comparison — yachi's won-round ~0.68 against pinglamb's
  lost-round ~0.61. Both operands are badged ([G068], [G069]) but no claim proves the
  comparison, and putting two badged numbers next to each other does not badge the
  sentence between them.
- Which rounds the seven topouts were. [C006] proves the counts, not their positions, so
  no match card names a topout.
- Any finesse *rate* as a percentage. The counts are badgeable — faults 1123 to 976 [G034]
  — and the per-piece direction is [G045], but a bare percentage would assert a share the
  data does not support, so the report names the denominator or drops the figure.

# 2026-09-10 — narrative beats

Eight matches, 65 rounds. **The series is drawn 4-4** [G001] on a round split of 32-33 [G002].
Every match was first-to-5 [G003]. No session in the corpus's first nine ended level in matches,
and none came within three rounds; 2026-08-25's 5-4 / 38-35 was the closest on both measures and
is now second on both.

## The shape of the night — it stays level all the way to the last round

yachi took m1, m5, m6 and m7; pinglamb took m2, m3, m4 and m8 [C001]. Four of the eight went to
a deciding final round and they split two apiece — m2 and m8 to pinglamb, m5 and m6 to yachi
[G012]. **After seven matches the round count was level at 28-28** [C010]; m8 decided both
columns, and pinglamb took it 5-4.

The one lopsided match is m3, 5-1 [G006] — yachi won only the fifth round of it [C013].
pinglamb's longest run is seven rounds, spanning m4 into m5 [G013].

The last round of the night is worth reading on its own. m8's decider is not a close one:
pinglamb VS ~94.2 / APM ~56.5 against yachi's VS ~5.7 / APM ~3.4 [G061]. A drawn night ends on
the most one-sided decider of the four.

## The coincidence — m5 and m6 ran the same nine rounds

Both matches went 0-3 down, both took round 4, both lost round 5, both won the last four to
finish 5-4 [C015][C016]. Nine slots, the same winner in every one, back to back.

There is no claim conjoining the two and there should not be: the two `round_seq` runs pin it
exactly, and a claim saying "these are equal" would be entailed by them. Nothing here proposes a
mechanism — two matches is two matches.

## The finding — level on the scoreboard is not level in the rounds

Split the rounds by who won them and the regimes come apart about as far as this corpus puts
them:

    attack per piece   won rounds    yachi .6271   pinglamb .7022   -> +11.99%
                       lost rounds   yachi .5317   pinglamb .5384   ->  +1.25%

C002 pins both. **+1.25% is the narrowest lost-regime gap in the corpus**, under 2026-08-14's
+1.78%. So this is the second session of ten to take 08-14's shape — ceilings apart, floors
together — against three in the mirror shape and four level in both.

**得一局撐住.** `check_loo` puts the lost gap at `rel` 2.081, third-largest in the corpus: drop
m8r4 and +1.25 becomes +3.86. m8r4 is the round where yachi took 81 lines of incoming to
pinglamb's 102 and still lost [G025] on an APP of .7207 — his second-highest of the night, in a
round he lost, which lifts his losing-round pool by itself. 「地板貼到實」 is that round's
statement as much as the night's. The direction survives; the size does not.

Said within a player: yachi separates his own won and lost rounds by +17.94%, pinglamb by
**+30.44%** [C003]. That is pinglamb's own corpus high, past his +25.22% on 2026-08-14, and the
second-widest player-session of the twenty behind yachi's +31.49% on 2026-08-09.

## The volume route — a sixth failure, and the one that lands where the ordering says

yachi threw 276 more pieces for 47 fewer lines of attack [C005]. The arithmetic:

    surplus     276 pieces = 5.14% of pinglamb's count  -> buys back 5.14 pp [C009]
    the gap     6.65 pp                                  [C004]
    shortfall   1.51 pp

The corpus ordering — sessions ranked by shortfall, ranked the same way by attack difference —
puts 1.51 between 2026-08-01's 1.00 (−32 lines) and 2026-07-24's 2.66 (−72), predicting an
attack difference in that band. Measured: **−47**. In its slot.

That is the second out-of-sample test the ordering has had. 2026-09-03 was the first and it
missed, taking Spearman from 1.000 to 0.950; this one hits, and ρ rises to 0.9636 (exact
permutation p = 2.5e-05) with 09-03 still the single inversion. The reading that survives is the
one 09-03 forced — a strong monotone relationship, not an exact ranking — and it now has a point
arriving on each side of it.

**得一局撐住, again.** The attack difference is `rel` 0.766: m2r9 alone is 36 of the 47 lines,
and without it the difference is −11. m2r9 is the round where yachi cleared 150 lines — the
session's most — and pinglamb survived it anyway [G020]. 「爭 47 行」 is one round's;
「兩邊嘅總攻擊撞埋一齊」 is the night's.

**C004's 6.65% is the narrowest session-level APP gap in the corpus**, under 2026-08-01's 7.27%.
So the night is level on the scoreboard, level in the rounds, and closest-ever on the efficiency
gap — three different measures agreeing, which is not something the previous nine sessions
offered.

## The columns

- **KPP is the flattest it has ever been**: yachi 3.598, pinglamb 3.606, 0.214% apart [C008],
  narrower than 2026-09-03's 0.285%. Within each player it barely moves between won and lost
  rounds either [G068][G069].
- **Deaths 5-6** [C006], 11 topouts over 65 rounds; the other 54 were garbage [G064].
- **Downstacking is nearly level too** — pinglamb .18372 per piece against yachi .18324, 0.262%
  apart [G073], flatter than KPP. That is why C008's superlative is scoped to the corpus and not
  to this night.
- **The routes still differ**: yachi's Quads 267 to 185 [G034]; pinglamb's T-spin doubles 258 to
  212 [G035] and triples 66 to 41 [G036]. yachi drops faster (PPS ~1.46 to ~1.38 [G039]),
  pinglamb hits harder per piece [G041].
- **Perfect Clears** pinglamb 9, yachi 5 [G037], and they do not decide rounds: of the 9 rounds
  only pinglamb cleared one, he lost 1 [G079]; of the 5 only yachi did, he lost 1 [G077].
- VS decides every one of the 65 rounds [G024], for the tenth session running — and it is not a
  second signal, since KO count equals round count in first-to-death 1v1 [G038].

## What did NOT reproduce

The per-match APP separation (2026-08-19 and 2026-08-25) does not, and there is no weakened
version of it available either. yachi won m5 at pinglamb +18.89% — the LARGEST per-match gap of
the eight — and also m7 at −8.43%, the smallest. He also leads attack per piece outright in m1
and m7, so 「pinglamb leads every match」 is false here too. Two of ten sessions separate.

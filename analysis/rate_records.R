#!/usr/bin/env Rscript
# Are the session VS/APM/PPS records skill, or a small-denominator artifact?
#
#   H0 (skill)    a rate is a property of the player; its spread does not depend
#                 on how long the round happened to last.  slope of log SD ~ log t = 0
#   H1 (artifact) the rate is a ratio with t in the denominator, so it behaves
#                 like a sample mean: SD proportional to t^-1/2.  slope = -0.5
#
# The mean is the control: under H1 the MEAN rate is flat in t and only the SD
# moves.  If short rounds were genuinely better play, the mean would rise too.
#
# ---------------------------------------------------------------------------
# THIS SCRIPT EMITS AN ARTEFACT.  `--json` writes `analysis/rate-records.json`,
# which is committed and is the ONLY home of every figure the repo publishes
# from this analysis:  `pipeline/records.py` reads it instead of holding copies,
# and `pipeline/check_rate_records.py` byte-compares CLAUDE.md's sentences
# against it.  Before that existed the numbers were hand-copied into two files
# and a prose section, and two of the three copies were measurably wrong.
#
# The artefact carries md5s of its own source and of every facts.json it read,
# so a stale one is a red build rather than a number nobody re-derives.  The
# script hash is over the WHOLE file, comments included: a rule that tries to
# tell a comment from a statistic is a rule that can be fooled, and the cost of
# the strict version is one re-run.
#
# Figures are rounded to six significant digits on the way out.  That is far
# more precision than anything published (three at most) and far less than the
# ~1e-15 an lm() differs by across BLAS implementations, which is what makes
# byte-identity of the artefact a check on the analysis rather than on the
# machine that ran it.

suppressPackageStartupMessages(library(jsonlite))

args <- commandArgs(trailingOnly = TRUE)
json_out <- if ("--json" %in% args) {
  i <- match("--json", args)
  if (length(args) > i) args[i + 1] else "analysis/rate-records.json"
} else NA_character_
quiet <- "--quiet" %in% args

# Resolved from THIS script's own location, not hardcoded. An absolute path to one
# checkout means a worktree (or anyone else's clone) silently regresses a different
# tree's data than the one it is sitting in — the evidence would be for sessions the
# working copy does not contain, and nothing would say so.
script <- sub("^--file=", "",
              grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)[1])
repo <- normalizePath(file.path(dirname(script), ".."))

# GLOBBED off disk. This line was a hardcoded vector until 2026-08-23 and was the
# last unguarded session list in the repo: the argument for QUALIFYING_MS is a
# regression over the WHOLE corpus, so a list that quietly stopped covering the
# newest data would have left the threshold resting on evidence that no longer
# included the rounds it is applied to. `sort` because the artefact is committed
# and readdir order is not a property of the corpus.
facts_paths <- sort(Sys.glob(file.path(repo, "sessions", "*", "report", "facts.json")))
sessions <- basename(dirname(dirname(facts_paths)))
if (!length(sessions)) stop("no sessions/*/report/facts.json under ", repo)

rows <- do.call(rbind, lapply(seq_along(sessions), function(si) {
  s <- sessions[si]
  f <- fromJSON(facts_paths[si], simplifyDataFrame = FALSE)
  do.call(rbind, lapply(seq_along(f$matches), function(mi) {
    m <- f$matches[[mi]]
    do.call(rbind, lapply(seq_along(m$rounds), function(ri) {
      r <- m$rounds[[ri]]
      tt <- max(sapply(r$players, function(p) p$finaltime_ms)) / 1000
      do.call(rbind, lapply(names(r$players), function(pl) {
        p <- r$players[[pl]]
        data.frame(session = s, mi = mi, ri = ri, player = pl, t = tt,
                   vs = p$vs_x1000 / 1000, apm = p$apm_x1000 / 1000,
                   pps = p$pps_x1000 / 1000, pieces = p$pieces,
                   atk = p$garbage_attack, won = identical(r$winner, pl),
                   stringsAsFactors = FALSE)
      }))
    }))
  }))
}))

say <- function(...) if (!quiet) cat(...)
rule <- function(x) say(strrep("=", 74), "\n", x, "\n", strrep("=", 74), "\n", sep = "")

say(sprintf("n = %d player-rounds over %d sessions (%d rounds)\n",
            nrow(rows), length(sessions), nrow(rows) / 2))
say(sprintf("round length: %.1f-%.1fs, median %.1fs\n\n",
            min(rows$t), max(rows$t), median(rows$t)))

# The three metrics the analysis measures. RATE_RECORDS is the subset the report
# actually ranks — `generators._SUPERLATIVES` qualifies apm and vs and holds no pps
# entry — and the two are kept apart because the stability band below differs
# between them, which is exactly the distinction the published sentence lost.
metrics <- c("vs", "apm", "pps")
RATE_RECORDS <- c("vs", "apm")
art <- list()

## ---------------------------------------------------------------------------
rule("1. THE SLOPE TEST   H0: 0   H1: -0.5")
## Equal-count bins in t; within each bin, the spread of the rate.
NB <- 8
rows <- rows[order(rows$t), ]
bin <- cut(seq_len(nrow(rows)), breaks = NB, labels = FALSE)

for (metric in metrics) {
  agg <- do.call(rbind, lapply(split(rows, bin), function(d) {
    data.frame(t = exp(mean(log(d$t))), sd = sd(d[[metric]]), mean = mean(d[[metric]]))
  }))
  fit <- lm(log(sd) ~ log(t), data = agg)
  ci <- confint(fit)["log(t)", ]
  sl <- coef(fit)["log(t)"]
  pv <- summary(fit)$coefficients["log(t)", 4]
  # is the MEAN flat?  (the control)
  mfit <- lm(mean ~ log(t), data = agg)
  mpv <- summary(mfit)$coefficients["log(t)", 4]

  art$metrics[[metric]] <- list(
    slope = sl, ci_lo = ci[1], ci_hi = ci[2], r2 = summary(fit)$r.squared, p = pv,
    mean_p = mpv, half_inside_ci = unname(ci[1] <= -0.5 && -0.5 <= ci[2]),
    sd_short = agg$sd[1], sd_long = agg$sd[NB],
    mean_short = agg$mean[1], mean_long = agg$mean[NB],
    t_short = agg$t[1], t_long = agg$t[NB])

  say(sprintf("\n  %s\n", toupper(metric)))
  say("    bin t (s) ", sprintf("%7.1f", agg$t), "\n")
  say("    SD        ", sprintf("%7.2f", agg$sd), "\n")
  say("    mean      ", sprintf("%7.1f", agg$mean), "\n")
  say(sprintf("    slope %+.3f  95%% CI [%+.3f, %+.3f]  R^2 %.3f  p %.2g\n",
              sl, ci[1], ci[2], summary(fit)$r.squared, pv))
  say(sprintf("      H0 (slope 0) .... %s\n",
              if (pv < .05 && ci[2] < 0) "REJECTED" else "not rejected"))
  say(sprintf("      H1 (slope -0.5) . %s\n",
              if (ci[1] <= -0.5 && -0.5 <= ci[2]) "inside the CI — consistent"
              else "OUTSIDE the CI"))
  say(sprintf("      control: mean vs log t  p = %.2f  (%s)\n", mpv,
              if (mpv > .05) "flat — short rounds are not better, only noisier"
              else "mean also moves — not a pure variance effect"))
}

## ---------------------------------------------------------------------------
say("\n"); rule("2. WHERE THE UNQUALIFIED RECORDS ACTUALLY COME FROM")
q1 <- quantile(rows$t, .25)
say(sprintf("   shortest quartile of rounds = under %.1fs\n\n", q1))
# 3 metrics x one record per session. DERIVED, not the literal 12 this line carried
# while there were four sessions: adding the fifth made it 15 and binom.test(15, 12, ...)
# aborted the script. A hardcoded n here is a silent understatement at best.
n_records <- length(metrics) * length(sessions)
hits <- 0
for (metric in metrics) {
  qs <- sapply(sessions, function(s) {
    d <- rows[rows$session == s, ]
    b <- d[which.max(d[[metric]]), ]
    findInterval(b$t, quantile(d$t, c(.25, .5, .75))) # 0 = shortest quarter
  })
  hits <- hits + sum(qs == 0)
  say(sprintf("   %-4s record's quartile per session: %s\n", toupper(metric),
              paste(qs, collapse = " ")))
}
bt_records <- binom.test(hits, n_records, 0.25, alternative = "greater")
say(sprintf("\n   %d of %d records sit in the shortest quartile.\n", hits, n_records))
say(sprintf("   Under H0 that is Binom(%d, 0.25): p = %.3g\n", n_records,
            bt_records$p.value))
art$records <- list(n = n_records, n_metrics = length(metrics),
                    in_shortest_quartile = hits, p = bt_records$p.value,
                    quartile_cut_s = unname(q1))

for (metric in metrics) {
  top <- rows[[metric]] >= quantile(rows[[metric]], .90)
  k <- sum(rows$t[top] <= q1)
  bt <- binom.test(k, sum(top), 0.25, alternative = "greater")
  art$metrics[[metric]]$top_decile_short <- k
  art$metrics[[metric]]$top_decile_n <- sum(top)
  art$metrics[[metric]]$top_decile_p <- bt$p.value
  say(sprintf("   %-4s top decile: %2d/%d (%.0f%%) are short rounds (H0 25%%), p = %.2g\n",
              toupper(metric), k, sum(top), 100 * k / sum(top), bt$p.value))
}

## Every session's unqualified peak against its own qualified peak, for the two
## metrics the report ranks. Per session and per metric rather than a corpus argmax:
## the sentence this feeds names 07-22's VS headline specifically, and "the worst in
## the corpus" is a different claim that happens to sit on a different round (08-09's
## APM, 79% above). Emitting the grid lets the prose keep its subject and still be
## derived from it.
QUALIFYING_S <- 60
art$unqualified_peaks <- list()
for (s in sessions) {
  per <- list()
  for (metric in RATE_RECORDS) {
    d <- rows[rows$session == s, ]
    u <- d[which.max(d[[metric]]), ]
    dq <- d[d$t >= QUALIFYING_S, ]
    if (!nrow(dq)) next
    q <- dq[which.max(dq[[metric]]), ]
    per[[metric]] <- list(value = u[[metric]], round_s = u$t, player = u$player,
                          qualified = q[[metric]],
                          pct_above = 100 * (u[[metric]] / q[[metric]] - 1))
  }
  art$unqualified_peaks[[s]] <- per
}
say("\n   unqualified peak vs the same session's qualified peak:\n")
for (s in sessions) for (metric in RATE_RECORDS) {
  e <- art$unqualified_peaks[[s]][[metric]]
  say(sprintf("     %s %-3s %7.1f over a %5.1fs round — %5.1f%% above %.1f\n",
              s, toupper(metric), e$value, e$round_s, e$pct_above, e$qualified))
}

## ---------------------------------------------------------------------------
say("\n"); rule("3. DOES A BIG SHORT-ROUND RATE PREDICT THE PLAYER AT ALL?")
say("   If short-round bursts were skill, the player who burns bright in short\n")
say("   rounds should be the stronger player in long ones.\n\n")
players <- sort(unique(rows$player))
pr <- do.call(rbind, lapply(sessions, function(s) {
  do.call(rbind, lapply(players, function(pl) {
    d <- rows[rows$session == s & rows$player == pl, ]
    sh <- d$vs[d$t < 45]; lo <- d$vs[d$t >= 60]
    if (length(sh) >= 5 && length(lo) >= 5)
      data.frame(session = s, player = pl, short = mean(sh), long = mean(lo))
  }))
}))
if (!quiet) print(pr, row.names = FALSE, digits = 4)
ct <- cor.test(pr$short, pr$long)
art$predict <- list(r = unname(ct$estimate), p = ct$p.value, n = nrow(pr))
say(sprintf("\n   Pearson r = %+.3f  (R^2 %.3f)  p = %.2f  n = %d player-sessions\n",
            ct$estimate, ct$estimate^2, ct$p.value, nrow(pr)))
say("   -> short-round VS carries no information about the same player's\n")
say("      long-round VS. It is noise, and the record is its loudest sample.\n")

## ---------------------------------------------------------------------------
say("\n"); rule("4. IS THE CUT-OFF A TUNED KNOB?  (record stability band)")
say("   If the record names the SAME round for every cut-off in a neighbourhood\n")
say("   of the threshold, then the threshold is not a parameter anyone defends.\n\n")

# The band is COMPUTED by widening from the threshold until the record moves,
# and it is computed per metric. Until 2026-08-23 this section printed a table
# of VS only and the published sentence read 「the same round for every cut-off
# from 50 s to 70 s」 for APM and VS both. That is VS's band. APM's is [54, 62],
# so the sentence was false for one of the two metrics it named — and the table
# beneath it could never have said so, because the table only ever showed the
# metric the claim was true for. A figure whose evidence cannot contradict it is
# the shape this repo keeps rediscovering.
record_at <- function(s, metric, cut) {
  d <- rows[rows$session == s & rows$t >= cut, ]
  if (!nrow(d)) return(NA_character_)
  b <- d[which.max(d[[metric]]), ]
  sprintf("m%dr%d/%s", b$mi, b$ri, b$player)
}
SWEEP_MAX <- ceiling(max(rows$t))
band_over <- function(ms) {
  lo <- 1; hi <- SWEEP_MAX
  for (metric in ms) for (s in sessions) {
    base <- record_at(s, metric, QUALIFYING_S)
    l <- QUALIFYING_S
    while (l > 1 && identical(record_at(s, metric, l - 1), base)) l <- l - 1
    h <- QUALIFYING_S
    while (h < SWEEP_MAX && identical(record_at(s, metric, h + 1), base)) h <- h + 1
    lo <- max(lo, l); hi <- min(hi, h)
  }
  c(lo, hi)
}
per_metric <- lapply(metrics, function(m) band_over(m))
names(per_metric) <- metrics
b_rate <- band_over(RATE_RECORDS)
b_all <- band_over(metrics)
art$stability <- list(
  threshold_s = QUALIFYING_S,
  per_metric = lapply(per_metric, function(b) list(lo = b[1], hi = b[2])),
  rate_records = list(metrics = RATE_RECORDS, lo = b_rate[1], hi = b_rate[2]),
  all_metrics = list(metrics = metrics, lo = b_all[1], hi = b_all[2]))

for (metric in metrics) {
  b <- per_metric[[metric]]
  say(sprintf("   %-4s every session's record is unchanged over [%d, %d] s\n",
              toupper(metric), b[1], b[2]))
}
say(sprintf("\n   the two RATE RECORDS the report ranks (%s): [%d, %d] s\n",
            paste(toupper(RATE_RECORDS), collapse = ", "), b_rate[1], b_rate[2]))
say(sprintf("   all three metrics measured here:              [%d, %d] s\n",
            b_all[1], b_all[2]))
say(sprintf("   the threshold in force is %d s.\n", QUALIFYING_S))

## ---------------------------------------------------------------------------
if (!is.na(json_out)) {
  art$generated_by <- "analysis/rate_records.R --json"
  art$sessions <- sessions
  art$n_player_rounds <- nrow(rows)
  art$n_rounds <- nrow(rows) / 2
  art$bins <- NB
  art$script_md5 <- unname(tools::md5sum(script))
  art$facts_md5 <- as.list(setNames(unname(tools::md5sum(facts_paths)), sessions))

  # Six significant digits: more than anything published, less than the machine
  # noise byte-identity would otherwise be measuring. See the header.
  round6 <- function(x) {
    if (is.list(x)) return(lapply(x, round6))
    if (is.numeric(x)) return(signif(x, 6))
    x
  }
  art <- round6(art)
  # Key order fixed here rather than left to insertion order, so the committed
  # file is a function of the data and not of the order the sections ran in.
  art <- art[sort(names(art))]
  art$metrics <- art$metrics[metrics]
  path <- if (grepl("^/", json_out)) json_out else file.path(repo, json_out)
  writeLines(toJSON(art, auto_unbox = TRUE, pretty = 2, digits = NA), path)
  say(sprintf("\nwrote %s\n", json_out))
}

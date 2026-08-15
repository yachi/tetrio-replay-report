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

suppressPackageStartupMessages(library(jsonlite))

# Resolved from THIS script's own location, not hardcoded. An absolute path to one
# checkout means a worktree (or anyone else's clone) silently regresses a different
# tree's data than the one it is sitting in — the evidence would be for sessions the
# working copy does not contain, and nothing would say so.
script <- sub("^--file=", "",
              grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)[1])
repo <- normalizePath(file.path(dirname(script), ".."))
# Hardcoded, and adding a session means editing this line: the argument for
# QUALIFYING_MS is a regression over the WHOLE corpus, so a list that quietly stops
# covering the newest data leaves the threshold resting on evidence that no longer
# includes the rounds it is applied to.
sessions <- c("2026-07-22", "2026-07-24", "2026-07-28", "2026-08-01", "2026-08-09",
              "2026-08-14")

rows <- do.call(rbind, lapply(sessions, function(s) {
  f <- fromJSON(file.path(repo, "sessions", s, "report", "facts.json"),
                simplifyDataFrame = FALSE)
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

cat(sprintf("n = %d player-rounds over %d sessions (%d rounds)\n",
            nrow(rows), length(sessions), nrow(rows) / 2))
cat(sprintf("round length: %.1f-%.1fs, median %.1fs\n\n",
            min(rows$t), max(rows$t), median(rows$t)))

rule <- function(x) cat(strrep("=", 74), "\n", x, "\n", strrep("=", 74), "\n", sep = "")

## ---------------------------------------------------------------------------
rule("1. THE SLOPE TEST   H0: 0   H1: -0.5")
## Equal-count bins in t; within each bin, the spread of the rate.
NB <- 8
rows <- rows[order(rows$t), ]
bin <- cut(seq_len(nrow(rows)), breaks = NB, labels = FALSE)

for (metric in c("vs", "apm", "pps")) {
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

  cat(sprintf("\n  %s\n", toupper(metric)))
  cat("    bin t (s) ", sprintf("%7.1f", agg$t), "\n")
  cat("    SD        ", sprintf("%7.2f", agg$sd), "\n")
  cat("    mean      ", sprintf("%7.1f", agg$mean), "\n")
  cat(sprintf("    slope %+.3f  95%% CI [%+.3f, %+.3f]  R^2 %.3f  p %.2g\n",
              sl, ci[1], ci[2], summary(fit)$r.squared, pv))
  cat(sprintf("      H0 (slope 0) .... %s\n",
              if (pv < .05 && ci[2] < 0) "REJECTED" else "not rejected"))
  cat(sprintf("      H1 (slope -0.5) . %s\n",
              if (ci[1] <= -0.5 && -0.5 <= ci[2]) "inside the CI — consistent"
              else "OUTSIDE the CI"))
  cat(sprintf("      control: mean vs log t  p = %.2f  (%s)\n", mpv,
              if (mpv > .05) "flat — short rounds are not better, only noisier"
              else "mean also moves — not a pure variance effect"))
}

## ---------------------------------------------------------------------------
cat("\n"); rule("2. WHERE THE UNQUALIFIED RECORDS ACTUALLY COME FROM")
q1 <- quantile(rows$t, .25)
cat(sprintf("   shortest quartile of rounds = under %.1fs\n\n", q1))
# 3 metrics x one record per session. DERIVED, not the literal 12 this line carried
# while there were four sessions: adding the fifth made it 15 and binom.test(15, 12, ...)
# aborted the script. A hardcoded n here is a silent understatement at best.
metrics <- c("vs", "apm", "pps")
n_records <- length(metrics) * length(sessions)
hits <- 0
for (metric in metrics) {
  qs <- sapply(sessions, function(s) {
    d <- rows[rows$session == s, ]
    b <- d[which.max(d[[metric]]), ]
    findInterval(b$t, quantile(d$t, c(.25, .5, .75))) # 0 = shortest quarter
  })
  hits <- hits + sum(qs == 0)
  cat(sprintf("   %-4s record's quartile per session: %s\n", toupper(metric),
              paste(qs, collapse = " ")))
}
cat(sprintf("\n   %d of %d records sit in the shortest quartile.\n", hits, n_records))
cat(sprintf("   Under H0 that is Binom(%d, 0.25): p = %.3g\n", n_records,
            binom.test(hits, n_records, 0.25, alternative = "greater")$p.value))

for (metric in metrics) {
  top <- rows[[metric]] >= quantile(rows[[metric]], .90)
  k <- sum(rows$t[top] <= q1)
  bt <- binom.test(k, sum(top), 0.25, alternative = "greater")
  cat(sprintf("   %-4s top decile: %2d/%d (%.0f%%) are short rounds (H0 25%%), p = %.2g\n",
              toupper(metric), k, sum(top), 100 * k / sum(top), bt$p.value))
}

## ---------------------------------------------------------------------------
cat("\n"); rule("3. DOES A BIG SHORT-ROUND RATE PREDICT THE PLAYER AT ALL?")
cat("   If short-round bursts were skill, the player who burns bright in short\n")
cat("   rounds should be the stronger player in long ones.\n\n")
pr <- do.call(rbind, lapply(sessions, function(s) {
  do.call(rbind, lapply(c("yachi", "pinglamb"), function(pl) {
    d <- rows[rows$session == s & rows$player == pl, ]
    sh <- d$vs[d$t < 45]; lo <- d$vs[d$t >= 60]
    if (length(sh) >= 5 && length(lo) >= 5)
      data.frame(session = s, player = pl, short = mean(sh), long = mean(lo))
  }))
}))
print(pr, row.names = FALSE, digits = 4)
ct <- cor.test(pr$short, pr$long)
cat(sprintf("\n   Pearson r = %+.3f  (R^2 %.3f)  p = %.2f  n = %d player-sessions\n",
            ct$estimate, ct$estimate^2, ct$p.value, nrow(pr)))
cat("   -> short-round VS carries no information about the same player's\n")
cat("      long-round VS. It is noise, and the record is its loudest sample.\n")

## ---------------------------------------------------------------------------
cat("\n"); rule("4. IS THE CUT-OFF A TUNED KNOB?  (record stability sweep)")
cat("   If the record names the SAME round for every plausible cut-off, then\n")
cat("   the threshold is not a parameter anyone has to defend.\n\n")
cuts <- c(0, 20, 30, 40, 45, 50, 55, 60, 70, 80, 90)
cat(sprintf("   %-11s %6s", "session", "kept"), sprintf("%13s", paste0(">=", cuts, "s")), "\n")
for (s in sessions) {
  d <- rows[rows$session == s, ]
  lab <- sapply(cuts, function(cut) {
    dd <- d[d$t >= cut, ]
    if (nrow(dd) == 0) return("-")
    b <- dd[which.max(dd$vs), ]
    sprintf("%.1f m%dr%d", b$vs, b$mi, b$ri)
  })
  cat(sprintf("   %-11s %5.0f%%", s, 100 * mean(d$t >= 60)), sprintf("%13s", lab), "\n")
}
cat("\n   (cell = the session's VS record under that cut-off)\n")

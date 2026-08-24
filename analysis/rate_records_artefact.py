"""The committed output of `analysis/rate_records.R`, and the check that it is current.

`Rscript analysis/rate_records.R --json` writes `analysis/rate-records.json`. Everything
this repo publishes from that analysis — the report footnote's SD and mean figures, and
fourteen figures in CLAUDE.md's 速率紀錄 section — is read out of it. Nothing is copied.

**Why an artefact and not a re-implementation.** The analysis is two log-log regressions,
a binomial tail and a stability sweep; porting it to Python would give the repo two
implementations of one statistic and no oracle to say which is right. The dual-extractor
argument does not apply here — there is no independent reading of the same bytes to agree
with, only the same arithmetic written twice.

**What makes the artefact trustworthy is the fingerprint, not the re-run.** It records the
md5 of every `facts.json` it read and of the R script itself, so the three ways it can go
stale are all loud:

  * a session lands            → `sessions` no longer matches the glob
  * the DATA moves under it    → a `facts_md5` no longer matches
  * the ANALYSIS moves under it → `script_md5` no longer matches

The second is the one that has actually happened. On 2026-08-16 `apm`/`pps`/`vs` were
re-sourced from the live `player.stats` tick to `results.aggregatestats`, moving the
shortest bin's VS SD from 59.91 to 59.60 with the corpus unchanged at six sessions — and
the guard in place then was a session COUNT, which cannot see that class at all.

The script hash is over the whole file, comments included. A rule that tries to tell a
comment from a statistic is a rule that can be fooled; the cost of the strict version is
one re-run of a script that takes a second.
"""
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARTEFACT = REPO / "analysis" / "rate-records.json"
SCRIPT = REPO / "analysis" / "rate_records.R"
REGEN = "Rscript analysis/rate_records.R --json analysis/rate-records.json"


def _md5(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def staleness(root=REPO):
    """Every reason the committed artefact does not describe the tree it sits in."""
    art_path = Path(root) / "analysis" / "rate-records.json"
    if not art_path.exists():
        return [f"{art_path.relative_to(root)} is missing. Run `{REGEN}`"], None
    art = json.loads(art_path.read_text(encoding="utf-8"))
    out = []

    facts = sorted(Path(root).glob("sessions/*/report/facts.json"))
    on_disk = [f.parent.parent.name for f in facts]
    if art["sessions"] != on_disk:
        out.append(f"the artefact was measured over {art['sessions']} but the tree holds "
                   f"{on_disk}. Run `{REGEN}`")
    else:
        for name, f in zip(on_disk, facts):
            got = _md5(f)
            if art["facts_md5"].get(name) != got:
                out.append(f"{name}: facts.json is {got}, the artefact was measured over "
                           f"{art['facts_md5'].get(name)}. The DATA moved under the "
                           f"statistic — this is the class a session-count guard cannot "
                           f"see. Run `{REGEN}`")

    script = Path(root) / "analysis" / "rate_records.R"
    got = _md5(script)
    if art["script_md5"] != got:
        out.append(f"analysis/rate_records.R is {got}, the artefact records "
                   f"{art['script_md5']}. The hash is over the whole file — if you only "
                   f"edited a comment, re-run and commit the artefact anyway. A rule that "
                   f"tries to tell a comment from a statistic can be fooled. Run `{REGEN}`")
    return out, art


def load(root=REPO):
    """The artefact, or SystemExit naming every way it is stale.

    Refuse-to-render rather than warn: the footnote's other half (session and
    player-round counts) IS derived from disk, so a stale artefact publishes a
    paragraph that is two-thirds true, which reads exactly like one that is.
    """
    problems, art = staleness(root)
    if problems:
        raise SystemExit("analysis/rate-records.json is stale:\n  - "
                         + "\n  - ".join(problems))
    return art

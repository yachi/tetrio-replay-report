"""Shared pieces of the 每粒攻擊 (`app`) section that the block modules import.

Lives apart from `app_section` so that `app_blocks_session`, `app_blocks_rounds` and
`app_blocks_corpus` can import it at module load without a cycle: `app_section` imports the
three block modules, and they import only this module and `app_svg` — never `app_section`.

The ctx contract itself is documented in `app_section`'s docstring and built by
`app_section.build_ctx`; the helpers here only read it.
"""
import functools
import glob
import json
import os
import re

from pipeline.app_svg import esc
from pipeline.claims.build_claims import SIMPLIFIED

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Positional player classes, by index into ctx["players"] (facts order). The section's CSS
#: colours them from --p1/--p2 with --yachi/--pinglamb as the fallback the four earliest reports'
#: :root needs (it predates the positional slots). Never a player NAME in a class or selector.
P_CLASS = ("ap-p1", "ap-p2")

#: Shown under every WIDE chart, and only at a width where that chart scrolls inside its box
#: (CSS `.ap-scrollhint`): the chart is drawn at native scale there, so its right part is off
#: screen until the reader scrolls.
SCROLL_HINT = '<div class="ap-scrollhint">← 個圖可以打橫拉 →</div>'

_SESSION_DIR = re.compile(r"(?:^|/)sessions/(\d{4}-\d{2}-\d{2})/report/?$")
_SUBSET_DIR = re.compile(r"(?:^|/)subsets/(\d{4}-\d{2}-\d{2})(?:-[^/]+)?/report/?$")


def session_date(report_dir):
    """The report's night as "YYYY-MM-DD", from its PATH, or None.

    sessions/<date>/report            -> <date>
    subsets/<date>-<suffix>/report    -> <date>   (the night the subset is drawn from)
    anything else (a scratch copy)    -> None, and the corpus blocks render nothing.

    The path, not facts.json's first timestamp: a match exported after midnight UTC would move
    a report onto the next day's corpus, and the directory name is what every other gate keys on.
    """
    norm = os.path.abspath(report_dir).replace(os.sep, "/")
    m = _SESSION_DIR.search(norm) or _SUBSET_DIR.search(norm)
    return m.group(1) if m else None


def is_corpus_session(ctx):
    """True when this report IS a corpus session (sessions/<date>/report); False for a subset or a
    scratch copy, whose own figures are not the corpus row for its date."""
    norm = os.path.abspath(ctx["report_dir"]).replace(os.sep, "/")
    return bool(_SESSION_DIR.search(norm))


@functools.lru_cache(maxsize=None)
def _corpus_upto(date):
    out = []
    for path in sorted(glob.glob(os.path.join(REPO, "sessions", "*", "report", "facts.json"))):
        d = path.replace(os.sep, "/").split("/")[-3]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) or d > date:
            continue
        with open(path, encoding="utf-8") as fh:
            out.append({"date": d, "facts": json.load(fh)})
    return tuple(out)


def corpus(ctx):
    """Every `sessions/<d>/report/facts.json` with d <= ctx["date"], in date order, as
    [{"date": d, "facts": facts}] — this report's own session included. [] when ctx["date"] is None.

    Bounded by date so an old report does not move when a new session lands. Subsets are never
    part of the corpus. The facts are SHARED (cached) objects: read them, never mutate them.
    Player order is NOT stable across files — key every corpus figure by username, and skip a
    session whose players are not exactly ctx["players"] as a set.
    """
    if not ctx.get("date"):
        return []
    return list(_corpus_upto(ctx["date"]))


def claims_of(ctx, family):
    """Generated claims of exactly this `family`, ledger order. Each is a claim_cards dict
    (id, family, canto, english_gloss, spec, verified, …)."""
    return [c for c in ctx["claims"] if c["family"] == family]


def badge(claim_id):
    """The report's badge markup for a claim id. Attach ONLY where that claim proves exactly the
    number beside it — check its spec, not its family name."""
    return f'<span class="badge" data-claim="{esc(claim_id)}"></span>'


def pname(ctx, i, cls=True):
    """Player i's name, escaped, wrapped in its positional colour class."""
    n = esc(ctx["players"][i])
    return f'<span class="ap-who {P_CLASS[i]}">{n}</span>' if cls else n


def block(title, eyebrow, body_html, note_html=None, block_id=None):
    """One of the section's six blocks, in the one shared frame.

    title      plain text (escaped) — the block's <h3>
    eyebrow    plain text (escaped) — the small mono line above it
    body_html  trusted markup the block built (SVG, tables, figures)
    note_html  trusted markup or None — the muted footnote (method, skipped rows, caveats)
    block_id   None, or a short slug; rendered as id="app-<slug>" so a link can land on it
    """
    ident = f' id="app-{esc(block_id)}"' if block_id else ""
    out = [f'<div class="ap-block"{ident}>',
           f'  <div class="ap-eyebrow">{esc(eyebrow)}</div>',
           f'  <h3 class="ap-title">{esc(title)}</h3>',
           f'  <div class="ap-body">{body_html}</div>']
    if note_html:
        out.append(f'  <p class="ap-note">{note_html}</p>')
    out.append('</div>')
    return "\n".join(out)


def check_glyphs(text, where):
    """Refuse simplified glyphs — the same guard the claim generator and every prose loader run."""
    bad = sorted(set(text) & SIMPLIFIED)
    if bad:
        raise SystemExit(f"{where}: simplified glyph(s) {bad} — this report is traditional "
                         "characters only")

"""練習卡 — two cards per player, picked by rule from the two simulator sections a player can practise
from, and placed right under 建議. The seventh quarantined section.

    python3 -m pipeline.practice_section sessions/2026-11-05/report            # gate
    python3 -m pipeline.practice_section sessions/2026-11-05/report --selftest  # its mutants

yachi agreed on 2026-11-14 (the report re-ordering): 行錯咗嗰一步 and finesse were the most usable
sections and sat under 39 000 px of a 50 000 px page, with nothing in 建議 pointing at them. This
section prints, per player, the first card of each and links to the whole section:

  1. 行錯咗嗰一步: the opener window's category with the most reported misses (ties go to the
     section's own category order), and that category's FIRST miss in match order — exactly the first
     card the pc-miss section draws for it. With no opener-window miss, the post-PC window's, by the
     same rule. With neither, a sentence.
  2. finesse: the placement ranked first (most fault events), the finesse section's first card.

Nothing is computed here. Each card is rendered by its own section's renderer (`pc_miss_section.card`,
`finesse_section._card`) from the same artefact, so a card here and its twin further down cannot
disagree; the gate checks that the two carry the same markup. Same tier as those sections: no claim
id, no ✓, the eyebrow and the quarantine sentence say so.
"""
import argparse
import html
import json
import os
import sys

from pipeline import finesse_section, pc_miss_section, region
from pipeline.claims.build_claims import SIMPLIFIED

NAME = "practice"
QUARANTINE_MARKER = "呢節唔屬於信任鏈"
SELECT_MARKER = "每人兩張，按規則揀，唔係人手揀"
SAME_MARKER = "張卡同下面全節嗰張一模一樣"
REQUIRED = (QUARANTINE_MARKER, SELECT_MARKER, SAME_MARKER)
TITLE = "練習卡（未經證明）"

OWN_CSS = """  <style>
    /* Scoped under #practice, own classes carry the pr- prefix. The two sections' card rules are
       copied below with their section id swapped for #practice, so the cards look the same here. */
    #practice .pr-cols { display: grid; gap: 1.2rem 2rem; margin-top: 1rem;
      grid-template-columns: repeat(auto-fit, minmax(min(100%, 26rem), 1fr)); }
    #practice .pr-col { min-width: 0; }
    #practice .pr-col h3 { margin: .4rem 0 .2rem; }
    #practice .pr-col h4 { margin: 1.2rem 0 .2rem; font-size: .98rem; }
    #practice .pr-more { display: inline-block; margin: .3rem 0 0; font-size: .9rem; }
    #practice .pr-sum { font-size: .9rem; margin: .2rem 0 .4rem; }
  </style>"""


def _swap(text, old):
    return text.replace(f"#{old}", f"#{NAME}")


# Functions, not module constants: build_report -> practice_section -> pc_miss_section ->
# replay_page -> skeleton -> build_report is a cycle, so the two modules may be half-imported here.
def _css():
    return "\n".join([OWN_CSS, _swap(pc_miss_section.CSS, "pc-miss"),
                      _swap(finesse_section.CSS, "finesse-placements")])


def _script():
    return pc_miss_section.SCRIPT.replace("#pc-miss .pm-anim", f"#{NAME} .pm-anim")


def _fail(msg):
    raise SystemExit(f"practice_section: {msg}")


def pick_miss(t):
    """(kind, round, miss, category key, count in it, total in the window) or None."""
    for kind in ("tst", "pc"):
        ms = [x for x in t["misses"] if x[0] == kind]
        if not ms:
            continue
        counts = {k: sum(1 for x in ms if x[2]["category"] == k) for k, _, _ in pc_miss_section.CATEGORIES}
        best = max(pc_miss_section.CATEGORIES, key=lambda c: (counts[c[0]], -pc_miss_section.CATEGORIES.index(c)))
        first = next(x for x in ms if x[2]["category"] == best[0])
        return first[0], first[1], first[2], best[0], counts[best[0]], len(ms)
    return None


def _cat_name(key):
    return next(name for k, name, _ in pc_miss_section.CATEGORIES if k == key)


def _miss_block(i, user, t, loc):
    p = pick_miss(t)
    if p is None:
        return [f'      <h4>1 · 行錯咗嗰一步</h4>',
                '      <p class="pr-sum">呢晚冇一粒行錯，冇卡。</p>']
    kind, r, m, key, n, total = p
    return [
        f'      <h4>1 · {pc_miss_section.KIND[kind]}最常錯：{_cat_name(key)}（{n} 粒）</h4>',
        f'      <p class="pr-sum">{pc_miss_section.KIND[kind]}一共行錯 {total} 粒；呢張係「{_cat_name(key)}」嘅第一粒。</p>',
        pc_miss_section.card(m, kind, loc, r["file"], r["round"], user),
        f'      <a class="pr-more" href="#pc-miss">睇晒 {total} 粒 →</a>',
    ]


def _finesse_block(i, p, positions):
    if not p["top"]:
        return ['      <h4>2 · finesse</h4>', '      <p class="pr-sum">呢晚冇一個擺位有多按，冇卡。</p>']
    m = p["top"][0]
    return [
        f'      <h4>2 · finesse 錯得最多：{html.escape(m["piece"])} 由左邊數第 {m["col"] + 1} 格起</h4>',
        f'      <p class="pr-sum">成晚多按 {p["faults"]} 下，呢個擺位佔 {m["faults"]} 下。</p>',
        finesse_section._card(1, m, i + 1, positions),
        '      <a class="pr-more" href="#finesse-placements">睇晒 finesse →</a>',
    ]


def section(pm_data, fin_data, players, loc, positions):
    if pm_data is None or fin_data is None:
        return None
    if pm_data.get("report_eligible") is not False or fin_data.get("report_eligible") is not False:
        _fail("an artefact declares itself report-eligible")
    t = pc_miss_section.tally(pm_data)
    if sorted(t) != sorted(players):
        _fail(f"pc-miss players {sorted(t)} are not facts.json's {sorted(players)}")
    fin = finesse_section._order(fin_data, players)
    cols = []
    for i, u in enumerate(players):
        cols += ['    <div class="pr-col">',
                 f'      <h3>{pc_miss_section._who(i, u)}</h3>',
                 *_miss_block(i, u, t[u], loc),
                 *_finesse_block(i, fin[i], positions),
                 '    </div>']
    out = [
        f'<section id="{NAME}">',
        _css(),
        '  <div class="wrap-wide">',
        '    <div class="eyebrow">模擬器推導 · 唔屬於信任鏈</div>',
        f'    <h2 class="section-title">{TITLE}</h2>',
        '    <div class="method-note">',
        f'      <p><strong>{QUARANTINE_MARKER}</strong>，同「行錯咗嗰一步」同 finesse 兩節一樣係模擬器推導，'
        '冇 claim 編號、冇 ✓ 標記。'
        f'{SELECT_MARKER}：第一張係「行錯咗嗰一步」入面開局 TST 之後最多粒嗰類（打和就照嗰節嘅類別次序）嘅第一粒'
        '（冇嘅話就用全消之後嗰段），第二張係 finesse 多按得最多嗰個擺位。'
        f'每{SAME_MARKER}，點計、點揀、有咩限制都喺嗰兩節寫。</p>',
        '    </div>',
        '    <div class="pr-cols">',
        *cols,
        '    </div>',
        '  </div>',
        _script(),
        '</section>',
    ]
    markup = "\n".join(out)
    bad = sorted(set(markup) & SIMPLIFIED)
    if bad:
        _fail(f"simplified glyph(s) {bad} — this report is traditional-character Cantonese")
    return markup


def build(facts, report_dir):
    pm = pc_miss_section.load(report_dir)
    fin = finesse_section.load(report_dir)
    if pm is None or fin is None:
        return None
    session_dir = os.path.dirname(os.path.abspath(report_dir))
    loc = pc_miss_section.Locator(session_dir, pm["session"])
    return section(pm, fin, facts["players"], loc, finesse_section.positions(facts))


# ---------------------------------------------------------------- gate

def _region(doc, name):
    start, end = region.markers(name, "pipeline/build_report.py")
    if start not in doc:
        return None
    i = doc.index(start) + len(start)
    return doc[i:doc.index(end, i)]


def _cards(body, cls):
    """Each `<div class="{cls}">` card block, as rendered (they are emitted one per line run)."""
    out, lines, cur = [], body.split("\n"), None
    for ln in lines:
        if ln.strip() == f'<div class="{cls}">':
            cur = [ln.strip()]
        elif cur is not None:
            cur.append(ln.strip())
            if ln.strip() == "</div>" and ln.startswith("      </div>") and len(ln) - len(ln.lstrip()) == 6:
                out.append("\n".join(cur))
                cur = None
    return out


def problems(doc, facts, report_dir, expected=None):
    body = _region(doc, NAME)
    if expected is None:
        expected = build(facts, report_dir)
    if expected is None:
        return ["report has a practice region but the session has no pc-miss or finesse artefact"] \
            if body is not None else []
    if body is None:
        return ["the session has both artefacts but the report has no practice region"]
    out = []
    for m in REQUIRED:
        if m not in body:
            out.append(f"control sentence missing: {m}")
    if "data-claim" in body or "claim-badge" in body or "✓</" in body:
        out.append("a claim badge appears on engine output")
    if body.strip() != expected.strip():
        out.append("the region is not what rendering the two artefacts produces")
    pm, fin = _region(doc, "pc-miss") or "", _region(doc, "finesse-placements") or ""
    for card in _cards(body, "pm-card"):
        if card not in "\n".join(_cards(pm, "pm-card")):
            out.append("a 行錯咗嗰一步 card here is not one the pc-miss section draws")
    for card in _cards(body, "fp-card"):
        if card not in "\n".join(_cards(fin, "fp-card")):
            out.append("a finesse card here is not one the finesse section draws")
    return out


def _load(report_dir):
    with open(os.path.join(report_dir, "report.html"), encoding="utf-8") as fh:
        doc = fh.read()
    with open(os.path.join(report_dir, "facts.json"), encoding="utf-8") as fh:
        facts = json.load(fh)
    return doc, facts


def _selftest(report_dir):
    doc, facts = _load(report_dir)
    expected = build(facts, report_dir)
    if expected is None:
        print("  --  no artefacts in this session; nothing to plant")
        return 0
    base = problems(doc, facts, report_dir, expected)
    if base:
        print("FAIL the committed report already fails: " + "; ".join(base))
        return 1
    s, e = region.markers(NAME, "pipeline/build_report.py")
    body = _region(doc, NAME)
    pm = _region(doc, "pc-miss")

    def swap(new_body):
        return doc.replace(s + body + e, s + new_body + e, 1)

    cases = [
        ("quarantine sentence dropped", swap(body.replace(QUARANTINE_MARKER, "呢節"))),
        ("selection sentence dropped", swap(body.replace(SELECT_MARKER, "揀咗兩張"))),
        ("a badge planted", swap(body.replace("</h2>", ' <span data-claim="C001">✓</span></h2>', 1))),
        ("a card's count edited", swap(body.replace("多按 <strong>", "多按 <strong>9", 1))),
        ("the region deleted", doc.replace(s + body + e, "", 1)),
        ("the pc-miss twin edited", doc.replace(pm, pm.replace("佢擺咗", "佢放咗"), 1) if pm else None),
    ]
    ok = True
    for name, mutant in cases:
        if mutant is None:
            print(f"  --  {name}: not plantable here")
            continue
        caught = bool(problems(mutant, facts, report_dir, expected))
        ok &= caught
        print(f"  {'ok ' if caught else 'BAD'} {name}: {'rejected' if caught else 'ACCEPTED'}")
    print(f"{'ok ' if ok else 'FAIL'} practice_section selftest")
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report_dir")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return _selftest(args.report_dir)
    doc, facts = _load(args.report_dir)
    bad = problems(doc, facts, args.report_dir)
    for b in bad:
        print(f"FAIL {args.report_dir}: {b}", file=sys.stderr)
    if not bad:
        print(f"  ok  {args.report_dir}: practice region")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

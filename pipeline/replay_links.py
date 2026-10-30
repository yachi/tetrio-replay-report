"""撳得落嘅場·局 — every match and round a published report names links to that night's replay page.

    python3 -m pipeline.replay_links sessions/2026-10-29/report --out /tmp/x.html   # link one report
    python3 -m pipeline.replay_links --selftest                                   # its mutants

`bin/build-docs` publishes `docs/<date>.html` through `link_report` instead of copying report.html
byte for byte, so every reference the page makes to a match or a round — 「m3r8」, 「m2 第3局」,
「第3場第5局」, 「第 4 場」, a bare 「m7」, the round table's 「R5」 cells, the 第N局 in a match card's
prose, the card's own 「第 N 場」 heading and its pips — opens `<date>-replay.html#m<pos>r<round>`
(round 1 for a match). report.html itself is never edited, so no ledger, region or gate moves: the
links exist on the site only, where the replay page they point at exists.

WHAT IT MAY CHANGE IS ONLY TAGS. `link_report` adds `<a>` elements around text it already holds and
nothing else, and checks that on every render (`_same_text`): the page's text with every tag
stripped must equal report.html's, and the match-copy island's prose likewise. A pattern that
swallowed or duplicated a character is a build error, not a page.

WHAT IT LINKS IS ONLY WHAT EXISTS. A reference is linked only when its match and round are in the
session's facts.json; anything else (an out-of-range 「m30」, a 「R12」 past the match's end) stays
plain text and is counted in `unresolved`, which build-docs prints. Text inside `<a>`, `<script>`
(except the match-copy island), `<style>`, `<title>`, `<textarea>`, `<svg>` and HTML comments is
never touched, so an existing link, a chart tooltip or a JSON island keeps its bytes.

THREE READINGS ARE OURS, and they are the whole rule set:
* a bare 「m<N>」 not followed by r<N> is match N — the reports use it that way throughout (「m1-m3」);
* 「第 N 場」 is match N, and 「第 N 局」 alone is a round only inside a match card, whose match is the
  card's; elsewhere a bare 第N局 has no match to belong to and is left alone;
* a round-table 「R<N>」 cell is round N of the table's `data-match`.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

# Longest form first; a bare mN must not be the head of an mNrN.
_LEAD = r"(?<![A-Za-z0-9_#])"
REF = re.compile(
    r"(?P<f_f>[A-Za-z0-9_.-]+\.ttrm)\s?第\s?(?P<f_r>\d+)\s?局"
    r"|第\s?(?P<a_m>\d+)\s?場\s?第\s?(?P<a_r>\d+)\s?局"
    rf"|{_LEAD}m(?P<b_m>\d+)\s?第\s?(?P<b_r>\d+)\s?局"
    rf"|{_LEAD}m(?P<c_m>\d+)\s?r(?P<c_r>\d+)(?![A-Za-z0-9_])"
    r"|第\s?(?P<d_m>\d+)\s?場"
    rf"|{_LEAD}m(?P<e_m>\d+)(?![A-Za-z0-9_])")
# Inside a match card only: a round of the card's match, in Arabic or Chinese numerals.
CARD_ROUND = re.compile(r"第\s?(?P<r>\d+|[一二三四五六七八九十]{1,3})\s?局")
RD_CELL = re.compile(r'(<td class="c-rd"[^>]*>)R(\d+)(</td>)')

RAW = ("script", "style", "title", "textarea", "svg")
TAG = re.compile(r"<!--.*?-->|<(/?)([A-Za-z][A-Za-z0-9-]*)\b[^>]*>", re.S)

LINK_CLASS = "rl"
CARD_SCRIPT_ID = "rl-cards"


def _cn(s):
    if s.isdigit():
        return int(s)
    if s == "十":
        return 10
    if s.startswith("十"):
        return 10 + NUM[s[1]]
    if len(s) >= 2 and s[1] == "十":
        return NUM[s[0]] * 10 + (NUM[s[2]] if len(s) == 3 else 0)
    return NUM.get(s)


def href(session, m, r):
    return f"{session}-replay.html#m{m}r{r}"


class Linker:
    def __init__(self, session, rounds, files=None):
        self.session = session
        self.rounds = rounds          # {match index: number of rounds}
        self.files = files or {}      # {replay file name: match index}
        self.match_alias = None       # {第 N 場's N: match index}, where N is not the position
        self.linked = 0
        self.unresolved = []

    def _a(self, m, r, text):
        n = self.rounds.get(m)
        if not n or not 1 <= r <= n:
            self.unresolved.append(text)
            return None
        self.linked += 1
        return f'<a class="{LINK_CLASS}" href="{html.escape(href(self.session, m, r))}">{text}</a>'

    def text(self, s, card=None):
        """Link every reference in one text node (no tags inside)."""
        def sub(mo):
            g = mo.groupdict()
            if g["f_f"]:
                m = self.files.get(g["f_f"])
                if m is None:
                    self.unresolved.append(mo.group())
                    return mo.group()
                r = int(g["f_r"])
            elif g["a_m"]:
                m, r = int(g["a_m"]), int(g["a_r"])
            elif g["b_m"]:
                m, r = int(g["b_m"]), int(g["b_r"])
            elif g["c_m"]:
                m, r = int(g["c_m"]), int(g["c_r"])
            elif g["d_m"]:
                m, r = int(g["d_m"]), 1
                if self.match_alias is not None:
                    if m not in self.match_alias:
                        self.unresolved.append(mo.group())
                        return mo.group()
                    m = self.match_alias[m]
            else:
                m, r = int(g["e_m"]), 1
            return self._a(m, r, mo.group()) or mo.group()
        out = REF.sub(sub, s)
        if card is None:
            return out
        # The card's own 第N局: only in the stretches the first pass left as plain text.
        parts = re.split(r"(<a [^>]*>.*?</a>)", out)
        for i in range(0, len(parts), 2):
            parts[i] = CARD_ROUND.sub(
                lambda mo: (self._a(card, _cn(mo.group("r")) or 0, mo.group()) or mo.group()), parts[i])
        return "".join(parts)

    def fragment(self, frag, card=None):
        """Link the text of an HTML fragment, leaving tags, links and raw-text elements alone."""
        out, pos, depth_a, low = [], 0, 0, frag.lower()
        while True:
            mo = TAG.search(frag, pos)
            if not mo:
                break
            chunk = frag[pos:mo.start()]
            out.append(chunk if depth_a else self.text(chunk, card))
            tok, pos = mo.group(), mo.end()
            out.append(tok)
            if tok.startswith("<!--"):
                continue
            close, name = mo.group(1), mo.group(2).lower()
            if name in RAW and not close and not tok.endswith("/>"):
                # Raw text runs to its own close tag, found by plain search: a `<` inside a
                # script is not a tag and must not be parsed as one.
                end = low.find(f"</{name}", pos)
                end = len(frag) if end < 0 else end
                out.append(frag[pos:end])
                pos = end
            elif name == "a":
                depth_a += -1 if close else 1
        tail = frag[pos:]
        out.append(tail if depth_a else self.text(tail, card))
        return "".join(out)


def _strip(s):
    return TAG.sub("", s)


def _round_table(page, lk):
    """R<N> cells, per table: the table names its match in `data-match`."""
    def table(mo):
        m = int(mo.group(1))
        def cell(c):
            return c.group(1) + (lk._a(m, int(c.group(2)), f"R{c.group(2)}") or f"R{c.group(2)}") + c.group(3)
        return RD_CELL.sub(cell, mo.group(0))
    return re.sub(r'<table class="rt-tbl" data-match="(\d+)">.*?</table>', table, page, flags=re.S)


CARD_JS = """<script id="%s">
/* Published-site only (pipeline/replay_links.py): the match cards are built by the report's own
   script, so their 第 N 場 heading and their pips are linked here, by structure, after it runs. */
document.addEventListener("DOMContentLoaded", function () {
  var base = %s;
  document.querySelectorAll(".match-card").forEach(function (card) {
    var idx = card.querySelector(".mc-idx");
    var mo = idx && /第 (\\d+) 場/.exec(idx.textContent);
    if (!mo) return;
    var m = mo[1];
    var a = document.createElement("a");
    a.className = "%s";
    a.href = base + "#m" + m + "r1";
    while (idx.firstChild) a.appendChild(idx.firstChild);
    idx.appendChild(a);
    card.querySelectorAll(".pip-trail .pip").forEach(function (pip, i) {
      var p = document.createElement("a");
      for (var k = 0; k < pip.attributes.length; k++) p.setAttribute(pip.attributes[k].name, pip.attributes[k].value);
      p.href = base + "#m" + m + "r" + (i + 1);
      p.style.cursor = "pointer";
      pip.parentNode.replaceChild(p, pip);
    });
  });
});
</script>
"""


def link_report(page, session, rounds, files=None):
    """report.html's text -> the published page's. Returns (html, Linker)."""
    lk = Linker(session, rounds, files)
    island = re.compile(r'(<script type="application/json" id="match-copy">)(.*?)(</script>)', re.S)
    mo = island.search(page)
    if mo:
        data = json.loads(mo.group(2))
        before = {k: c.get("body", "") for k, c in data.get("cards", {}).items()}
        for k, c in data.get("cards", {}).items():
            if "body" in c:
                c["body"] = lk.fragment(c["body"], card=int(k))
        for k, c in data.get("cards", {}).items():
            if _strip(c.get("body", "")) != _strip(before[k]):
                raise ValueError(f"match-copy card {k}: linking changed its text")
        body = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
        page = page[:mo.start(2)] + body + page[mo.end(2):]
    page = _round_table(page, lk)
    # The openers region's per-match table labels a match by its file's EXPORT number, on purpose
    # (opener_section._match_label: the table joins against the artefact, which keys on `file`).
    # There 第 N 場 is file N, so it is linked through the file map; everywhere else N is the position.
    reg = re.compile(r"(<!-- BEGIN generated openers [^>]*-->)(.*?)(<!-- END generated openers -->)", re.S)
    mo = reg.search(page)
    if mo:
        lk.match_alias = {int(t): m for f, m in lk.files.items()
                          for t in [f.rsplit(".", 1)[0].rsplit("-", 1)[-1]] if t.isdigit()}
        page = page[:mo.start(2)] + lk.fragment(mo.group(2)) + page[mo.end(2):]
        lk.match_alias = None
    out = lk.fragment(page)
    js = CARD_JS % (CARD_SCRIPT_ID, json.dumps(f"{session}-replay.html"), LINK_CLASS)
    # The report shell is a body fragment that ends on its last script; the card linker follows it.
    i = out.rfind("</body>")
    i = len(out) if i < 0 else i
    out = out[:i] + js + out[i:]
    if not _same_text(page, out[:i] + out[i + len(js):]):
        raise ValueError("linking changed the page's text")
    return out, lk


def _same_text(a, b):
    def visible(s):
        return _strip(re.sub(r'<script type="application/json" id="match-copy">.*?</script>', "", s, flags=re.S))
    return visible(a) == visible(b)


def rounds_of(facts):
    return {m["index"]: len(m["rounds"]) for m in facts["matches"]}


def files_of(facts):
    """A match's file name is its export number, not its position (see CLAUDE.md, 08-01)."""
    return {Path(m["file"]).name: m["index"] for m in facts["matches"]}


def _selftest():
    rounds = {1: 7, 2: 9, 3: 8}
    S = "2026-01-01"
    lk = Linker(S, rounds, {"replay-x-09.ttrm": 3})
    cases = [
        ("replay-x-09.ttrm 第 7 局", [(3, 7)]), ("replay-x-02.ttrm 第 7 局", []),
        ("m2r3", [(2, 3)]), ("抽走m3r6，", [(3, 6)]), ("m2 第3局", [(2, 3)]), ("第3場第5局", [(3, 5)]),
        ("第 1 場", [(1, 1)]), ("m1-m3", [(1, 1), (3, 1)]), ("m30", []), ("m2r10", []),
        ("html m2x", []), ("#m2r3", []),
    ]
    bad = []
    for src, want in cases:
        got = re.findall(r'#m(\d+)r(\d+)"', lk.text(src))
        if [(int(a), int(b)) for a, b in got] != want:
            bad.append(f"{src!r}: {got} != {want}")
    card = lk.fragment('第五局佢打<span class="badge" data-claim="C1"></span>，m1r2 同第十二局', card=2)
    if re.findall(r'#m(\d+)r(\d+)"', card) != [("2", "5"), ("1", "2")]:
        bad.append(f"card: {card}")
    frag = '<a href="x">m2r3</a><script>m2r3</script><svg><title>m2r3</title></svg><!-- m2r3 -->m1'
    if lk.fragment(frag) != frag.replace("-->m1", f'--><a class="rl" href="{S}-replay.html#m1r1">m1</a>'):
        bad.append(f"raw/existing: {lk.fragment(frag)}")
    page = ('<html><body><table class="rt-tbl" data-match="2"><tr><td class="c-rd" data-v="0">R9</td>'
            '<td class="c-rd" data-v="1">R10</td></tr></table>'
            '<script type="application/json" id="match-copy">{"cards": {"3": {"title": "x", "body": "第八局"}}}</script>'
            '<p>第3場第5局</p></body></html>')
    out, l2 = link_report(page, S, rounds)
    op = ('<!-- BEGIN generated openers (x) --><td class="mono">第 9 場</td> m1r2<!-- END generated openers -->'
          '<p>第 3 場</p>')
    o2, _ = link_report(op, S, rounds, {"replay-x-9.ttrm": 2})
    if re.findall(r'#m(\d+)r(\d+)"', o2) != [("2", "1"), ("1", "2"), ("3", "1")]:
        bad.append(f"openers export numbering: {o2}")
    for want in ("#m2r9", "#m3r8", "#m3r5"):
        if want not in out:
            bad.append(f"page lacks {want}")
    if "#m2r10" in out or "R10" not in l2.unresolved:
        bad.append("R10 past the match's end was linked")
    # The text-equality guard must fire on a linker that alters text.
    orig = Linker.text
    Linker.text = lambda self, s, card=None: s[1:]
    try:
        link_report(page, S, rounds)
        bad.append("a text-altering linker was not refused")
    except ValueError:
        pass
    finally:
        Linker.text = orig
    for b in bad:
        print("FAIL", b)
    print(f"{'ok ' if not bad else 'FAIL'} replay_links selftest: {len(cases) + 6} cases")
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("report_dir", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    d = Path(a.report_dir)
    facts = json.loads((d / "facts.json").read_text(encoding="utf-8"))
    out, lk = link_report((d / "report.html").read_text(encoding="utf-8"), d.parent.name, rounds_of(facts),
                          files_of(facts))
    Path(a.out).write_text(out, encoding="utf-8")
    print(f"linked {lk.linked}, unresolved {len(lk.unresolved)}: {sorted(set(lk.unresolved))[:20]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

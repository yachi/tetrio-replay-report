"""千鳥格子練習場 — `docs/practice-cutcopy.html`, the 千鳥格子 (Cut Copy) practice page, audited before it is returned.

    python3 -m pipeline.cutcopy_practice_page --out-dir /tmp/pc   # render it somewhere other than docs/
    python3 -m pipeline.cutcopy_practice_page --selftest          # the audit's mutants

One self-contained file. It inlines, and nothing else:
  * the practice engine, `pipeline/cutcopy_practice_engine.js`;
  * the page script, `pipeline/cutcopy_practice_page.js`;
  * the drills artefact, `analysis/cutcopy-drills.json` (from `pipeline/sim/emit-cutcopy-drills.ts`, gated by
    `pipeline/openers/cutcopy-drills.test.ts`), as the data island `#cc-drills`, byte for byte as parsed;
  * its stylesheet, `pipeline/cutcopy_practice_page.css`, and its words, `pipeline/cutcopy_practice_prose.json`.

It is NOT a technique page (`pipeline.sites` does not list it, and nothing in the report reads it): its prefix,
`practice-cutcopy`, does not start with `cutcopy`, so the 千鳥格子 site's stale-page glob never sees it.
`bin/build-docs` renders it in its own block and byte-compares it under `--check`.

QUARANTINE. The drills are CONSTRUCTED practice boards, not corpus measurements: the artefact must say
`report_eligible: false`, `constructed: true` and `practice: true`, and the page carries no claim id and no ✓.
The audit reuses `replay_page.audit_quarantine` (no badge, every required sentence, no markup sink, no external
request, exactly one data island) and adds:

* the island parses to the artefact exactly, and still says `report_eligible: false`;
* every drill is listed exactly once (`data-drill`), with the artefact's own difficulty label and its source;
* every printed figure (`data-figure`) is RECOUNTED from the artefact, never typed;
* no claim id (C001, G012, R003…) anywhere on the page, no simplified glyph.
"""
import argparse
import html
import json
import os
import re
import sys

from pipeline import replay_page as RP
from pipeline import replay_section as RS
from pipeline.claims.build_claims import SIMPLIFIED

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PREFIX = "practice-cutcopy"
OVERVIEW = "practice-cutcopy.html"
ARTEFACT_REL = "analysis/cutcopy-drills.json"
ENGINE_PATH = os.path.join(HERE, "cutcopy_practice_engine.js")
SCRIPT_PATH = os.path.join(HERE, "cutcopy_practice_page.js")
CSS_PATH = os.path.join(HERE, "cutcopy_practice_page.css")
PROSE_PATH = os.path.join(HERE, "cutcopy_practice_prose.json")
DATA_ID = "cc-drills"
KINDS = ("corpus", "selfplay", "page", "own")

_FIGURE = re.compile(r'data-figure="([^"]+)">([^<]*)<')
_DRILL = re.compile(r'<tr data-drill="([^"]+)"><td>[^<]*</td><td data-difficulty>([^<]*)</td>'
                    r'<td>(\d+)</td><td>([^<]*)</td></tr>')
_ISLAND = re.compile(r'<script type="application/json" id="' + DATA_ID + r'">(.*?)</script>', re.S)
_CLAIM_ID = re.compile(r"\b[CGR]\d{3}\b")


def _esc(s):
    return html.escape(str(s), quote=True)


def _need(cond, msg):
    if not cond:
        raise ValueError(f"practice-cutcopy page: {msg}")


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_prose(path=PROSE_PATH):
    text = _read(path)
    _need(not (set(text) & SIMPLIFIED), f"the prose carries simplified glyph(s) {sorted(set(text) & SIMPLIFIED)}")
    return json.loads(text)


def island_json(art):
    """The artefact as the page carries it: compact, and safe inside <script> (no `</`)."""
    return json.dumps(art, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


class PracticeSite:
    def __init__(self, prose_path=PROSE_PATH):
        self.PROSE = load_prose(prose_path)
        self.OVERVIEW = OVERVIEW
        self.REQUIRED = (RS.EYEBROW, RS.NO_CLAIM, *self.PROSE["page_sentences"])

    @staticmethod
    def load_inputs(repo=REPO):
        art = json.loads(_read(os.path.join(repo, ARTEFACT_REL)))
        _need(art.get("report_eligible") is False, "the artefact is not marked report_eligible: false")
        _need(art.get("constructed") is True and art.get("practice") is True,
              "the artefact is not marked constructed: true and practice: true")
        return art

    def source_words(self, d):
        """The drill's source in words, from the artefact's own `source` record."""
        s, K = d["source"], self.PROSE["kinds"]
        _need(s["kind"] == d["kind"] and d["kind"] in K, f"{d['id']}: unknown source kind {s['kind']!r}")
        return K[d["kind"]].format(**s)

    @staticmethod
    def recount(art):
        dr = art["drills"]
        out = {"drills": str(len(dr))}
        for k in KINDS:
            out[k] = str(sum(1 for d in dr if d["kind"] == k))
        out["sessions"] = str(len({d["source"]["session"] for d in dr if d["kind"] == "corpus"}))
        return out

    def render(self, art):
        PR, T = self.PROSE, self.PROSE["table"]
        fig = self.recount(art)
        counts = PR["counts"]
        for k, v in fig.items():
            counts = counts.replace("{" + k + "}", f'<span data-figure="{k}">{v}</span>')
        _need("{" not in counts, "the counts sentence names a figure the page does not recount")
        rows = []
        for d in art["drills"]:
            rows.append(f'<tr data-drill="{_esc(d["id"])}"><td>{_esc(d["id"])}</td>'
                        f'<td data-difficulty>{_esc(d["difficulty"]["label"])}</td><td>{d["need"]}</td>'
                        f'<td>{_esc(self.source_words(d))}</td></tr>')
        out = [
            "<!doctype html>", '<html lang="zh-HK">', "<head>", '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">',
            f'<title>{_esc(PR["title"])}</title>', f'<meta name="description" content="{_esc(PR["desc"])}">',
            "<style>", _read(CSS_PATH).rstrip("\n"), "</style>", "</head>", "<body>",
            '<div class="wrap">',
            f'<p class="back"><a href="cutcopy.html">{_esc(PR["back"])}</a></p>',
            f'<p class="eyebrow">{RS.EYEBROW}</p>',
            '<div class="top">',
            f'  <h1>{_esc(PR["h1"])}</h1>',
            '  <select id="psel" class="psel" aria-label="揀題"></select>',
            '  <div class="modes" role="group" aria-label="操作模式"><button class="btn" id="mDrag">拖放</button>'
            '<button class="btn" id="mKey">按鍵</button></div>',
            "</div>",
            '<div class="qn">',
            *[f"  <p>{_esc(s)}</p>" for s in PR["page_sentences"]],
            f"  <p>所以呢版{RS.NO_CLAIM}。{counts}</p>",
            "</div>",
            '<div class="picker" id="picker"></div>',
            "",
            '<div class="main">',
            '  <div class="col" id="play">',
            '    <div id="status" class="fb"></div>',
            '    <div class="row act">',
            '      <button class="btn" id="undo">↶ 上一步</button>',
            '      <button class="btn" id="reset">重嚟</button>',
            '      <button class="btn" id="hint">目標形</button>',
            '      <button class="btn pri" id="demoBtn">示範</button>',
            "    </div>",
            '    <div class="demo" id="demo">',
            '      <div class="row">',
            '        <button class="btn" id="d0">⏮</button><button class="btn" id="dp">◀</button>'
            '<button class="btn" id="dn">▶</button><button class="btn" id="d9">⏭</button>',
            '        <button class="btn" id="dexit">返去自己砌</button>',
            "      </div>",
            '      <p id="dcap"></p>',
            "    </div>",
            '    <div class="stage">',
            '      <div class="side"><div class="box"><b>HOLD</b><canvas id="hold" width="56" height="40"></canvas></div></div>',
            '      <canvas id="board" tabindex="0" aria-label="練習盤面"></canvas>',
            '      <div class="side"><div class="box"><b>NEXT</b><canvas id="next" width="56" height="200"></canvas></div></div>',
            "    </div>",
            '    <div class="pad" id="pad">',
            '      <button class="btn" data-a="ccw">↺</button><button class="btn" data-a="180">180</button>'
            '<button class="btn" data-a="cw">↻</button><button class="btn" data-a="hold">Hold</button>',
            '      <button class="btn dk" data-a="undo" aria-label="上一步">↶</button>',
            '      <button class="btn k" data-a="left">←</button><button class="btn k" data-a="soft">↓</button>'
            '<button class="btn k" data-a="right">→</button><button class="btn pri k" data-a="hard">硬降</button>',
            "    </div>",
            "  </div>",
            '  <div class="panel">',
            '    <h2 id="ptitle"></h2>',
            '    <p class="note" id="pnote"></p>',
            '    <ol class="log" id="log"></ol>',
            "  </div>",
            "</div>",
            "",
            "<details>",
            f'<summary>{_esc(PR["play_summary"])}</summary>',
            *[f'<p class="lede">{_esc(p)}</p>' for p in PR["play"]],
            f'<p class="note">{_esc(PR["drag"])}</p>',
            f'<p class="keys">{PR["keys"]}</p>',
            "</details>",
            "<details>",
            f'<summary>{_esc(PR["recognise_summary"])}</summary>',
            f'<p class="note" style="margin-top:8px">{_esc(PR["recognise"])}</p>',
            '<div class="legend" id="legend"></div>',
            f'<p class="note">{PR["links"]}</p>',
            "</details>",
            "<details>",
            f'<summary>{_esc(PR["sources_summary"])}</summary>',
            f'<p class="note" style="margin-top:8px">{_esc(PR["sources_note"])}</p>',
            '<div class="dtw"><table class="dt">',
            "<tr>" + "".join(f"<th>{_esc(T[k])}</th>" for k in ("id", "difficulty", "need", "source")) + "</tr>",
            *rows,
            "</table></div>",
            "</details>",
            "</div>",
            f'<script type="application/json" id="{DATA_ID}">{island_json(art)}</script>',
            "<script>", _read(ENGINE_PATH).rstrip("\n"), "</script>",
            "<script>", _read(SCRIPT_PATH).rstrip("\n"), "</script>",
            "</body>", "</html>", "",
        ]
        return "\n".join(out)

    def audit(self, page, art):
        bad = RP.audit_quarantine(page, self.REQUIRED, DATA_ID)
        if set(page) & SIMPLIFIED:
            bad.append(f"the page carries simplified glyph(s) {sorted(set(page) & SIMPLIFIED)}")
        ids = sorted(set(_CLAIM_ID.findall(page)))
        if ids:
            bad.append(f"the page names claim id(s) {ids[:4]} — practice boards cite no claim")
        m = _ISLAND.search(page)
        if not m:
            bad.append("no drills island")
        else:
            try:
                isl = json.loads(m.group(1))
            except ValueError as e:
                isl = None
                bad.append(f"the drills island does not parse: {e}")
            if isl is not None:
                if isl.get("report_eligible") is not False:
                    bad.append("the drills island is not marked report_eligible: false")
                if isl != art:
                    bad.append("the drills island is not the artefact")
        rows = _DRILL.findall(page)
        want = {d["id"]: d for d in art["drills"]}
        if sorted(html.unescape(r[0]) for r in rows) != sorted(want):
            bad.append("the drill list does not list every drill exactly once")
        for did, lab, need, src in rows:
            d = want.get(html.unescape(did))
            if d is None:
                continue
            if html.unescape(lab) != d["difficulty"]["label"]:
                bad.append(f"{did}: the listed difficulty is not the artefact's")
            if int(need) != d["need"]:
                bad.append(f"{did}: the listed need is not the artefact's")
            if html.unescape(src) != self.source_words(d):
                bad.append(f"{did}: the listed source is not the drill's own")
        figs = {}
        for k, val in _FIGURE.findall(page):
            if k in figs:
                bad.append(f"figure {k} printed twice")
            figs[k] = html.unescape(val)
        rc = self.recount(art)
        if figs != rc:
            bad.append(f"the printed figures are not the artefact's, recounted: "
                       f"{sorted(k for k in set(figs) | set(rc) if figs.get(k) != rc.get(k))[:4]}")
        return bad

    def render_all(self, repo=REPO, inputs=None):
        art = inputs if inputs is not None else self.load_inputs(repo)
        page = self.render(art)
        bad = self.audit(page, art)
        _need(not bad, "; ".join(bad))
        return {OVERVIEW: page}

    def selftest(self, repo=REPO):
        art = self.load_inputs(repo)
        page = self.render(art)
        survived = killed = 0

        def expect(label, bad, want):
            nonlocal survived, killed
            if bool(bad) == want:
                killed += want
                print(f'  {"killed" if want else "passed"}: {label}')
            else:
                survived += 1
                print(f'  {"SURVIVED" if want else "FAILED control"}: {label} {bad[:2]}', file=sys.stderr)

        expect("the rendered page (control)", self.audit(page, art), False)
        for s in self.PROSE["page_sentences"]:
            expect(f"a quarantine sentence deleted ({s[:12]}…)", self.audit(page.replace(_esc(s), ""), art), True)
        # an island cell edited: the first drill's first start row, one cell flipped
        d0 = art["drills"][0]
        row = d0["start"][-1]
        flipped = ("G" if row[0] == "." else ".") + row[1:]
        isl = island_json(art)
        needle = json.dumps(d0["start"], ensure_ascii=False, separators=(",", ":"))
        _need(isl.count(needle) >= 1, "selftest: the first drill's start rows are not in the island")
        edited = needle.replace(json.dumps(row), json.dumps(flipped))
        expect("an island cell edited", self.audit(page.replace(needle, edited, 1), art), True)
        # a difficulty swapped between two drills of different labels in the list
        labs = [(d["id"], d["difficulty"]["label"]) for d in art["drills"]]
        a = labs[0]
        b = next(x for x in labs if x[1] != a[1])
        sw = page
        for (did, lab), new in ((a, b[1]), (b, a[1])):
            sw = re.sub(rf'(<tr data-drill="{re.escape(_esc(did))}"><td>[^<]*</td><td data-difficulty>){re.escape(lab)}<',
                        lambda m, new=new: m.group(1) + new + "<", sw, count=1)
        _need(sw != page, "selftest: the difficulty swap changed nothing")
        expect("two difficulties swapped", self.audit(sw, art), True)
        m = re.search(r'data-figure="drills">(\d+)<', page)
        expect("a printed count changed",
               self.audit(page[:m.start(1)] + str(int(m.group(1)) + 1) + page[m.end(1):], art), True)
        expect("an external script added",
               self.audit(page.replace("</head>", '<script src="https://example.com/x.js"></script></head>', 1), art), True)
        expect("a claim id added", self.audit(page.replace("</h1>", " C001</h1>", 1), art), True)
        expect("a badge added", self.audit(page.replace("</h1>", '<span data-claim="x">✓</span></h1>', 1), art), True)
        flip = json.loads(json.dumps(art))
        flip["report_eligible"] = True
        expect("report_eligible set true in the island",
               self.audit(page.replace(island_json(art), island_json(flip), 1), art), True)
        expect("report_eligible set true in the artefact", self.audit(self.render(flip), flip), True)
        expect("a drill row dropped",
               self.audit(re.sub(r'<tr data-drill="[^"]+">.*?</tr>\n', "", page, count=1), art), True)
        expect("a simplified glyph", self.audit(page.replace("</h1>", "实</h1>", 1), art), True)
        print(f"selftest: {killed} killed, {survived} survived")
        return 1 if survived else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out-dir")
    a = ap.parse_args(argv)
    site = PracticeSite()
    if a.selftest:
        return site.selftest()
    pages = site.render_all()
    d = a.out_dir or os.path.join(REPO, "docs")
    os.makedirs(d, exist_ok=True)
    for name, page in pages.items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(page)
        print(f"wrote {os.path.join(d, name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

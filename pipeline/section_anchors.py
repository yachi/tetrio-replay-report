"""撳得落嘅大標題 — every section's big title on a published report links to its own section.

    python3 -m pipeline.section_anchors --selftest

`bin/build-docs` passes every report it publishes (`docs/<date>.html`, and a subset's page) through
`anchor()`, after `replay_links` has added its links. Each `<section id="X">`'s FIRST
`<h2 class="section-title">` becomes a link to `#X`: the title's text is wrapped in
`<a class="sa" href="#X">`, so clicking it puts the section's address in the location bar, ready to
copy. A `#` appears beside the title on hover (CSS only, so it is not text). report.html itself is
never edited, so no ledger, region or gate moves, exactly as for `replay_links`.

A title that already holds a link (`replay_links` links 「第 9 場第 7 局」 inside 最癲一局's title) keeps
it: HTML forbids an `<a>` inside an `<a>`, so only the text OUTSIDE the existing links is wrapped,
each run on its own.

Every render checks itself (`_check`): the page's text with tags and `<style>` stripped must not
change, and every section holding a section-title must come out with exactly one title linking to
its own id. A section that does not is a build error, not a page.
"""
import argparse
import re
import sys

CLASS = "sa"
STYLE_ID = "sa-style"
CSS = (f'<style id="{STYLE_ID}">\n'
       f'  h2.section-title a.{CLASS} {{ color: inherit; text-decoration: none; }}\n'
       f'  h2.section-title a.{CLASS}:hover {{ text-decoration: underline; text-underline-offset: .15em; }}\n'
       f'  h2.section-title:has(a.{CLASS}):hover::after {{ content: " #"; opacity: .45; }}\n'
       f'  section[id] {{ scroll-margin-top: 1rem; }}\n'
       f'</style>')

SECTION = re.compile(r'<section id="([^"]+)"[^>]*>')
TITLE = re.compile(r'(<h2 class="section-title">)(.*?)(</h2>)', re.S)
LINK = re.compile(r'<a\b[^>]*>.*?</a>', re.S)


def _wrap(inner, sid):
    """Wrap every run of `inner` outside an existing <a>…</a> in a link to #sid."""
    out, pos = [], 0
    for m in list(LINK.finditer(inner)) + [None]:
        end = m.start() if m else len(inner)
        run = inner[pos:end]
        if run.strip():
            out.append(f'<a class="{CLASS}" href="#{sid}">{run}</a>')
        else:
            out.append(run)
        if m:
            out.append(m.group(0))
            pos = m.end()
    return "".join(out)


def anchor(page):
    """Return `page` with every section's first big title linking to its section."""
    if f'id="{STYLE_ID}"' in page:
        raise SystemExit("section_anchors: page already anchored")
    starts = [(m.start(), m.end(), m.group(1)) for m in SECTION.finditer(page)]
    out, pos = [], 0
    for i, (_, body, sid) in enumerate(starts):
        limit = starts[i + 1][0] if i + 1 < len(starts) else len(page)
        t = TITLE.search(page, body, limit)
        if not t:
            continue
        out += [page[pos:t.start(2)], _wrap(t.group(2), sid)]
        pos = t.end(2)
    out.append(page[pos:])
    res = "".join(out)
    if "</title>" not in res:
        raise SystemExit("section_anchors: page has no </title> to carry its style after")
    res = res.replace("</title>", "</title>" + CSS, 1)
    _check(page, res)
    return res


def _visible(s):
    s = re.sub(r"<style\b.*?</style>", "", s, flags=re.S)
    s = re.sub(r"<script\b.*?</script>", "", s, flags=re.S)
    return re.sub(r"<!--.*?-->|<[^>]+>", "", s, flags=re.S)


def _check(before, after):
    if _visible(before) != _visible(after):
        raise SystemExit("section_anchors: anchoring changed the page's text")
    starts = [(m.start(), m.end(), m.group(1)) for m in SECTION.finditer(after)]
    for i, (_, body, sid) in enumerate(starts):
        limit = starts[i + 1][0] if i + 1 < len(starts) else len(after)
        t = TITLE.search(after, body, limit)
        if not t:
            continue
        own = re.findall(rf'<a class="{CLASS}" href="#([^"]+)">', t.group(2))
        if not own or set(own) != {sid}:
            raise SystemExit(f"section_anchors: section {sid!r}'s title links to {own}, not to itself")
        if re.search(r"<a\b[^>]*>(?:(?!</a>).)*<a\b", t.group(2), re.S):
            raise SystemExit(f"section_anchors: section {sid!r}'s title nests a link inside a link")


def _selftest():
    page = ("<html><head><title>t</title></head><body>"
            '<section id="a"><h2 class="section-title">甲節</h2><h2 class="section-title">唔係大標題</h2></section>'
            '<section id="b"><h2 class="section-title">最癲：<a class="rl" href="x#m9r7">m9r7</a>（未經證明）</h2></section>'
            '<section id="c"><p>冇標題</p></section></body></html>')
    res = anchor(page)
    bad = []
    if '<a class="sa" href="#a">甲節</a>' not in res:
        bad.append("plain title not wrapped")
    if '>唔係大標題<' not in res or 'href="#a">唔係大標題' in res:
        bad.append("second h2 of a section was wrapped")
    if ('<a class="sa" href="#b">最癲：</a><a class="rl" href="x#m9r7">m9r7</a>'
            '<a class="sa" href="#b">（未經證明）</a>') not in res:
        bad.append("title with an inner link not split around it")
    if 'href="#c"' in res:
        bad.append("section without a title got a link")
    killed = 0
    mutants = {
        "wrong id": res.replace('href="#a"', 'href="#b"', 1),
        "dropped link": res.replace('<a class="sa" href="#a">甲節</a>', "甲節"),
        "text changed": res.replace("甲節", "乙節", 1),
        "nested link": res.replace('<a class="sa" href="#b">最癲：</a><a class="rl" href="x#m9r7">m9r7</a>',
                                   '<a class="sa" href="#b">最癲：<a class="rl" href="x#m9r7">m9r7</a></a>'),
    }
    for name, m in mutants.items():
        try:
            _check(page, m)
            bad.append(f"mutant survived: {name}")
        except SystemExit:
            killed += 1
    try:
        anchor(res)
        bad.append("double anchoring accepted")
    except SystemExit:
        killed += 1
    for b in bad:
        print("FAIL", b)
    print(f"section_anchors selftest: {killed} of {len(mutants) + 1} mutants killed")
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return _selftest()
    ap.error("nothing to do (use --selftest; bin/build-docs calls anchor())")


if __name__ == "__main__":
    sys.exit(main())

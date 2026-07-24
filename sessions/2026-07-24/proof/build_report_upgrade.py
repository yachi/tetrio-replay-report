#!/usr/bin/env python3
"""build_report_upgrade.py — upgrade report-2026-07-24.html IN PLACE from
"runtime JS-verified" to "Dafny-verified", using proof-map-24.json (real
verifier results). Deterministic string edits (no client JS added); every
pattern count is asserted so a layout change upstream fails loudly rather than
silently mis-editing. Keeps a .orig backup in proof/ for re-runnability.
"""
import json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(HERE, "..", "report-2026-07-24.html")
BACKUP = os.path.join(HERE, "report-2026-07-24.orig.html")

# reject any Simplified-only glyph slipping into inserted 口語 text
SIMPLIFIED = set("证据链两写对样应关结独录来个过验说话难严将会显题间实这为动战报点导运线书车轻")

pm = {e["id"]: e for e in json.load(open(os.path.join(HERE, "proof-map-24.json")))}
assert len(pm) == 20 and all(e["status"] == "verified" for e in pm.values()), "proof map not 20/20 verified"

# start from the pristine original if we already have a backup (idempotent re-runs)
if os.path.exists(BACKUP):
    s = open(BACKUP, encoding="utf-8").read()
else:
    s = open(REPORT, encoding="utf-8").read()
    shutil.copy(REPORT, BACKUP)

NEW_METHOD = (
    '<b>方法論(要老實講):</b>呢版已經由「即場 JS 驗證」升級做<b>離線 Dafny 形式證明</b>。'
    '成條信任鏈係咁:兩個各自寫嘅 parser(Python + TypeScript)由 .ttrm 抽數,<code>jq -S</code> '
    'diff 要 byte 對 byte 一樣 → 每條 claim 寫低一句 python_check,20/20 全部 pass → codegen 由 '
    'facts-24.json 自動砌 Dafny(flat const,冇一個數字係手打)→ 每條 claim 對應一條 lemma,'
    '<code>dafny verify</code> 行到 0 error → 再做 mutation test,改一個數據或者一個 predicate '
    '都即刻爆 verify(證明啲 lemma 唔係空口講白話)。要老實講清楚:Dafny 證嘅係「claim ⇔ 抽出嚟嘅'
    '數據」呢個等價關係;至於數據本身抽得啱唔啱,就靠兩個 parser 獨立寫、結果 byte 對 byte 一致嚟兜底。'
    '下面附錄每條都列埋佢對應嘅 Dafny lemma 名。'
)

# (old, new, expected_count) — plain-string swaps
SWAPS = [
    ('<span class="ic">✓</span>即場驗證</a>', '<span class="ic">✓</span>Dafny 已證明</a>', 22),
    (' · 即場驗證通過"', ' · Dafny 已證明"', 22),
    ('✓ 全部 20 條 claim 即場驗證通過。', '✓ 全部 20 條 claim 已用 Dafny 形式證明。', 1),
    ('下面每個數字都即場用 JS 驗返,禁個 ✓ 即場驗證 章睇得到。',
     '下面每個數字都經離線 Dafny 形式證明過,禁個 ✓ Dafny 已證明 章就睇到佢對應嘅 lemma。', 1),
    ('每條建議都貼住即場驗證嘅數字。', '每條建議都貼住 Dafny 已證明嘅數字。', 1),
    ('即場驗證 · Claims Ledger', 'Dafny 形式證明 · Claims Ledger', 1),
    ('<th>Predicate（source）</th><th>結果</th>',
     '<th>Predicate（source）</th><th>Dafny lemma</th><th>結果</th>', 1),
    ('>✓ 通過</span>', '>✓ Dafny 已證明</span>', 20),
    ('</style>',
     'table.appendix .lemma-cell { font-family: var(--font-mono); font-size: 0.72rem; '
     'color: var(--muted); word-break: break-all; max-width: 210px; }\n</style>', 1),
]

for old, new, n in SWAPS:
    got = s.count(old)
    assert got == n, f"pattern count mismatch: {old!r} expected {n} got {got}"
    s = s.replace(old, new)

# method-note: replace inner html (regex, exactly one)
s, k = re.subn(r'(<div class="method-note">).*?(</div>)', lambda m: m.group(1) + NEW_METHOD + m.group(2), s, flags=re.S)
assert k == 1, f"method-note replaced {k} times"

# appendix rows: insert per-row Dafny lemma cell before the status pill
def fix_row(m):
    row = m.group(0)
    cid = re.search(r'claim-(C\d+)', row).group(1)
    lemma = pm[cid]["lemma"]
    cell = f'<td class="lemma-cell"><code>{lemma}</code></td>'
    assert '<td><span class="status-pill"' in row, f"no pill td in {cid}"
    return row.replace('<td><span class="status-pill"', cell + '<td><span class="status-pill"', 1)

s, nrows = re.subn(r'<tr id="claim-C\d+">.*?</tr>', fix_row, s, flags=re.S)
assert nrows == 20, f"processed {nrows} appendix rows"

# guard: no Simplified glyphs, no stale live-verify wording left
leftovers = s.count("即場驗證")
assert leftovers == 0, f"{leftovers} stale 即場驗證 left"
bad = SIMPLIFIED & set(NEW_METHOD)
assert not bad, f"Simplified glyphs in method text: {bad}"

open(REPORT, "w", encoding="utf-8").write(s)
print(f"upgraded report-2026-07-24.html: 22 badges + 20 pills -> Dafny, "
      f"lemma column added to {nrows} rows, methodology rewritten, 0 stale 即場驗證")

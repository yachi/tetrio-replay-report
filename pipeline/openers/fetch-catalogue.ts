/**
 * Regenerate `opener-fields.json` from the community opener catalogue. Run by hand, never in CI.
 *
 * The catalogue is `swng/opener_db`, itself a scrape of Ivan(28283)'s Comprehensive Opener Database.
 * It is fetched at a PINNED COMMIT, not at `main`: the upstream is a data dump that changes without
 * notice, and a figure computed here must stay attached to the bytes it was computed from.
 *
 * What gets vendored is the DECODED fields, not the fumen strings. Decoding needs knewjade's
 * `tetris-fumen`, and `pipeline/` has no dependencies by design — so the decode happens once, here,
 * and everything downstream reads plain 10-wide row strings. That also means the vendored file is
 * diffable: a change in the catalogue shows up as changed boards rather than as changed base64.
 *
 *   bun add tetris-fumen                     # or: FUMEN_LIB=/path/to/tetris-fumen/index.js
 *   bun run pipeline/openers/fetch-catalogue.ts
 */
import { createHash } from 'node:crypto';

const COMMIT = 'b4a66878a47466b557165dec9171701bfeafab93';   // swng/opener_db, 2023-05-01 "data update"
const URL = `https://raw.githubusercontent.com/swng/opener_db/${COMMIT}/data.json`;

const lib = process.env.FUMEN_LIB ?? 'tetris-fumen';
const { decoder } = await import(lib) as { decoder: { decode(s: string): any[] } };

const res = await fetch(URL);
if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${URL}`);
const bytes = new Uint8Array(await res.arrayBuffer());
const sha256 = createHash('sha256').update(bytes).digest('hex');
const data = JSON.parse(new TextDecoder().decode(bytes)) as any[];

const FUMEN_RE = /[?]?[vmd]115@[A-Za-z0-9+/?]+/g;

/** A fumen field as bottom-aligned row strings, trimmed to the occupied part. `.` is empty. */
function rowsOf(field: any): string[] | null {
  const rows: string[] = [];
  for (let y = 22; y >= 0; y--) {                      // fumen y = 0 is the BOTTOM row
    let line = '';
    for (let x = 0; x < 10; x++) {
      const at = field.at(x, y);
      line += at === '_' || at === undefined ? '.' : at;
    }
    rows.push(line);
  }
  const first = rows.findIndex(r => r !== '..........');
  return first < 0 ? null : rows.slice(first);
}

const pages: any[] = [];
let decoded = 0, failed = 0;
for (const o of data) {
  const texts: string[] = [];
  for (const key of ['SEARCH', 'Image']) {
    const v = o[key];
    if (!v) continue;
    for (const item of (Array.isArray(v) ? v.flat(3) : [v])) if (typeof item === 'string') texts.push(item);
  }
  const seen = new Set<string>();
  for (const t of texts) {
    for (const code of t.match(FUMEN_RE) ?? []) {
      const clean = code.replace(/^\?/, '');
      if (seen.has(clean)) continue;
      seen.add(clean);
      let ps: any[];
      try { ps = decoder.decode(clean); decoded++; } catch { failed++; continue; }
      ps.forEach((p, i) => {
        const rows = rowsOf(p.field);
        if (!rows) return;
        pages.push({ name: o.name, tag: o.tag_primary ?? null, fumen: clean, page: i, rows });
      });
    }
  }
}

const out = {
  provenance: {
    source: 'https://github.com/swng/opener_db',
    upstream_of: "Ivan(28283)'s Comprehensive Opener Database",
    commit: COMMIT,
    url: URL,
    data_json_sha256: sha256,
    entries: data.length,
    decoder: `tetris-fumen (${lib === 'tetris-fumen' ? 'npm' : lib})`,
    fumens_decoded: decoded,
    fumens_failed: failed,
    // Deliberately no fetch timestamp: it would make this file differ on every regeneration and
    // hide the only change that matters, which is the boards.
  },
  pages,
};
await Bun.write(`${import.meta.dir}/opener-fields.json`, JSON.stringify(out, null, 0));
console.log(`entries ${data.length}  fumens decoded ${decoded} (failed ${failed})  pages ${pages.length}`);
console.log(`distinct openers with at least one page: ${new Set(pages.map(p => p.name)).size}`);
console.log(`data.json sha256 ${sha256}`);

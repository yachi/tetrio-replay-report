// Drive the rendered Pages site in a real browser and fail on what only a browser can see.
//
//   node tools/site-check/check.js <site-dir> [--shots <dir>] [--jobs N]
//
// <site-dir> is a `bin/build-docs --out <dir>` render (CI: the docs job's _site, before it is
// uploaded). It is served over http on 127.0.0.1, so what is checked is the bytes `deploy` publishes.
//
// Every page, at phone width (390 px):
//   - no uncaught exception, no console error, no failed request, no request off this host;
//   - no horizontal page scroll (the page's scrollWidth is the viewport's);
//   - every same-site link names a page that exists, and a #fragment that page carries
//     (an id, or a replay page's #m<pos>r<round>[@p<n>], resolved against its own round list).
// Then, on the pages where a click does something:
//   - a report's tier nav: each link scrolls its tier into view and lights up (rn-on);
//   - a replay page: a #m..r..@p<n> link opens that round at that position, and ▶ steps one;
//   - every ▶ 影片 link is a YouTube watch URL with a whole-second t;
//   - a 中盤 page's case links open the replay at the hit, and the round is found;
//   - tst-openers: a class tile opens its build panel and the board animates.
// --shots writes screenshots at deviceScaleFactor 2 for a person to look at.
'use strict';
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const http = require('http');

const args = process.argv.slice(2);
const root = path.resolve(args[0] || '');
const opt = (k) => { const i = args.indexOf(k); return i < 0 ? null : args[i + 1]; };
const shots = opt('--shots');
const jobs = +(opt('--jobs') || 4);
if (!args[0] || !fs.existsSync(path.join(root, 'index.html'))) {
  console.error('usage: node tools/site-check/check.js <site-dir> [--shots <dir>] [--jobs N]');
  process.exit(2);
}
if (shots) fs.mkdirSync(shots, { recursive: true });

const PHONE = { width: 390, height: 844 };
const YT = /^https:\/\/www\.youtube\.com\/watch\?v=[\w-]{11}&t=\d+s$/;
const REPLAY_HASH = /^#m(\d+)r(\d+)(?:@p(\d+))?$/;
// stray_cannon_page.js's own hash grammar (route, technique-demo and loop pages)
const CASE_HASH = /^#((?:\d{4}-\d{2}-\d{2}-m\d+r\d+)|(?:demo-[a-z0-9-]+))(?:@p(\d+))?$/;

const failures = [];
const fail = (where, what) => failures.push(`${where}: ${what}`);

function serve() {
  const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css',
    '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon' };
  const srv = http.createServer((req, res) => {
    const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    let f = path.join(root, u.endsWith('/') ? u + 'index.html' : u);
    if (!f.startsWith(root) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'content-type': types[path.extname(f)] || 'application/octet-stream' });
    fs.createReadStream(f).pipe(res);
  });
  return new Promise((ok) => srv.listen(0, '127.0.0.1', () => ok(srv)));
}

async function pool(items, n, fn) {
  let i = 0;
  await Promise.all(Array.from({ length: Math.min(n, items.length) }, async () => {
    while (i < items.length) { const k = i++; await fn(items[k], k); }
  }));
}

// Named exceptions, not a bound: the only pages allowed to ask another host for anything.
// The two Cold Clear replay pages are committed as they were drawn (tools/cc-coach/pages/) and load
// their fonts from Google; the check still answers those requests empty, so CI never depends on them.
const OFFSITE_OK = {
  'cc-yachi.html': ['fonts.googleapis.com', 'fonts.gstatic.com'],
  'cc-pinglamb.html': ['fonts.googleapis.com', 'fonts.gstatic.com'],
};

// A page opened with every listener the checks need. `errs` collects what must stay empty.
async function open(ctx, base, rel) {
  const pg = await ctx.newPage();
  const errs = [];
  pg.on('pageerror', (e) => errs.push(`uncaught: ${e.message}`));
  pg.on('console', (m) => { if (m.type() === 'error') errs.push(`console error: ${m.text()}`); });
  pg.on('requestfailed', (r) => errs.push(`request failed: ${r.url()} (${r.failure() && r.failure().errorText})`));
  pg.on('request', (r) => {
    const u = r.url();
    if (u.startsWith(base) || /^(data|about|blob):/.test(u)) return;
    const host = new URL(u).host;
    if ((OFFSITE_OK[rel] || []).includes(host)) return;
    errs.push(`off-site request: ${u}`);
  });
  pg.on('response', (r) => { if (r.status() >= 400) errs.push(`HTTP ${r.status()}: ${r.url()}`); });
  await pg.goto(base + rel, { waitUntil: 'load' });
  return { pg, errs };
}

(async () => {
  const srv = await serve();
  const base = `http://127.0.0.1:${srv.address().port}/`;
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: PHONE, deviceScaleFactor: shots ? 2 : 1 });
  // Never leave the host: a ▶ 影片 link or any other off-site navigation is answered empty.
  await ctx.route(/^https?:\/\/(?!127\.0\.0\.1)/, (r) => r.fulfill({ status: 204, body: '' }));

  const pages = fs.readdirSync(root).filter((f) => f.endsWith('.html')).sort();
  const ids = new Map();      // page -> Set of ids
  const replays = new Map();  // replay page -> Set of "m<pos>r<round>" labels
  const cases = new Map();    // route / demo page -> Set of case keys its scp-data holds
  const links = [];           // [from, href]

  // ---- 1. every page: errors, layout, ids, links ----
  await pool(pages, jobs, async (rel) => {
    const { pg, errs } = await open(ctx, base, rel);
    await pg.waitForTimeout(300);
    const got = await pg.evaluate(() => ({
      sw: document.documentElement.scrollWidth, iw: window.innerWidth,
      ids: [...document.querySelectorAll('[id]')].map((e) => e.id),
      hrefs: [...document.querySelectorAll('a[href]')].map((a) => a.getAttribute('href')),
      labels: [...document.querySelectorAll('.rpg-round[data-label]')].map((a) => a.getAttribute('data-label')),
      // a route / demo page routes #<date>-mNrN@pN and #demo-<slug>@pN through scp-data's rounds
      cases: (() => { const d = document.getElementById('scp-data'); const r = d && JSON.parse(d.textContent).rounds; return r ? Object.keys(r) : null; })(),
    }));
    for (const e of errs) fail(rel, e);
    if (got.sw > got.iw + 1) fail(rel, `scrolls sideways at ${PHONE.width} px (scrollWidth ${got.sw})`);
    ids.set(rel, new Set(got.ids));
    if (rel.endsWith('-replay.html')) {
      replays.set(rel, new Set(got.labels));
      if (!got.labels.length) fail(rel, 'replay page lists no rounds');
    }
    if (got.cases) cases.set(rel, new Set(got.cases));
    for (const h of got.hrefs) links.push([rel, h]);
    await pg.close();
  });
  console.log(`opened ${pages.length} pages at ${PHONE.width} px`);

  // ---- 2. every same-site link resolves ----
  let checked = 0, yt = 0;
  for (const [from, h] of links) {
    if (/^https:\/\/www\.youtube\.com\//.test(h) || /youtu\.be\//.test(h)) {
      yt++;
      if (/\/watch\?/.test(h) && /[?&]t=/.test(h) && !YT.test(h)) fail(from, `video link is not watch?v=<id>&t=<n>s: ${h}`);
      continue;
    }
    if (/^[a-z]+:/i.test(h) || h.startsWith('//')) continue;  // other sites: not ours to check
    const cut = h.indexOf('#');
    const file = cut < 0 ? h : h.slice(0, cut), frag = cut < 0 ? null : h.slice(cut + 1);
    const target = file === '' ? from : path.posix.normalize(path.posix.join(path.posix.dirname(from), file));
    checked++;
    if (!ids.has(target)) {
      if (!fs.existsSync(path.join(root, target))) fail(from, `link to a page that does not exist: ${h}`);
      continue;  // a non-html asset
    }
    if (frag == null || frag === '') continue;
    const m = REPLAY_HASH.exec('#' + frag);
    const c = CASE_HASH.exec('#' + frag);
    if (c && cases.has(target)) {
      if (!cases.get(target).has(c[1])) fail(from, `case link to a case the page does not hold: ${h}`);
    } else if (m && replays.has(target)) {
      if (!replays.get(target).has(`m${m[1]}r${m[2]}`)) fail(from, `replay link to a round the page does not list: ${h}`);
    } else if (!ids.get(target).has(decodeURIComponent(frag))) {
      fail(from, `link to a fragment the page does not carry: ${h}`);
    }
  }
  console.log(`checked ${checked} same-site links and ${yt} video links`);

  // ---- 3. interactions ----
  const reports = pages.filter((p) => /^\d{4}-\d\d-\d\d\.html$/.test(p));
  const latest = reports[reports.length - 1];

  // 3a. the report's tier nav
  {
    const { pg, errs } = await open(ctx, base, latest);
    const n = await pg.locator('#report-nav a').count();
    if (!n) fail(latest, 'no tier nav (#report-nav)');
    for (let i = 0; i < n; i++) {
      const a = pg.locator('#report-nav a').nth(i);
      const href = await a.getAttribute('href');
      const id = await a.getAttribute('data-target');  // empty on the first link: back to the top
      await a.click();
      // the nav scrolls smoothly: wait until scrollY has stopped moving
      let last = -1, still = 0;
      for (let k = 0; k < 60 && still < 3; k++) {
        await pg.waitForTimeout(100);
        const y = await pg.evaluate(() => window.pageYOffset);
        still = y === last ? still + 1 : 0;
        last = y;
      }
      const st = await pg.evaluate(([id, i]) => {
        const nav = document.getElementById('report-nav');
        const t = id ? document.getElementById(id) : null;
        return { found: !id || !!t, top: t ? t.getBoundingClientRect().top : -window.pageYOffset,
          lit: nav.querySelectorAll('a')[i].className === 'rn-on', hash: location.hash };
      }, [id, i]);
      if (!st.found) { fail(latest, `tier nav link ${href} names no section (${id})`); continue; }
      if (st.top > PHONE.height / 2 || st.top < -PHONE.height / 2) fail(latest, `tier nav link ${href} did not bring its section to the top (top ${Math.round(st.top)})`);
      if (!st.lit) fail(latest, `tier nav link ${href} is not lit after its click`);
      if (shots && i === 1) await pg.screenshot({ path: path.join(shots, 'report-nav.png') });
    }
    for (const e of errs) fail(latest + ' (nav clicks)', e);
    console.log(`clicked ${n} tier nav links on ${latest}`);
    await pg.close();
  }

  // 3b. the replay page: open at a position, step once
  async function replayAt(rel, label, p, tag) {
    const { pg, errs } = await open(ctx, base, `${rel}#${label}@p${p}`);
    await pg.waitForTimeout(400);
    const st = await pg.evaluate(() => ({
      missing: !document.querySelector('.rpg-missing').hidden,
      now: document.getElementById('rpg-now').textContent,
      seek: document.querySelector('#round-replay .rp-seek') && +document.querySelector('#round-replay .rp-seek').value,
      hash: location.hash,
    }));
    if (st.missing) fail(`${rel}#${label}@p${p}`, 'replay page says the round is missing');
    if (!st.now.includes(`（${label}）`)) fail(`${rel}#${label}@p${p}`, `replay opened another round: ${st.now}`);
    if (st.seek !== p) fail(`${rel}#${label}@p${p}`, `replay opened at position ${st.seek}, not ${p}`);
    if (tag) {
      await pg.click('#round-replay [data-act="fwd"]');
      await pg.waitForTimeout(300);
      const after = await pg.evaluate(() => ({ seek: +document.querySelector('#round-replay .rp-seek').value, hash: location.hash }));
      if (after.seek !== p + 1) fail(rel, `▶ stepped to ${after.seek}, not ${p + 1}`);
      if (after.hash !== `#${label}@p${p + 1}`) fail(rel, `▶ left the hash at ${after.hash}`);
      const v = await pg.getAttribute('.rpg-video-a', 'href').catch(() => null);
      if (v && !YT.test(v)) fail(rel, `the replay's video link is not watch?v=<id>&t=<n>s: ${v}`);
      if (shots) await pg.screenshot({ path: path.join(shots, `${tag}.png`) });
    }
    for (const e of errs) fail(`${rel}#${label}@p${p}`, e);
    await pg.close();
  }
  {
    const rel = latest.replace('.html', '-replay.html');
    const label = [...replays.get(rel)][0];
    await replayAt(rel, label, 5, 'replay');
    console.log(`stepped ${rel}#${label}@p5`);
  }

  // 3c. a 中盤 page's case links open the replay at the hit (the first three of each page)
  {
    let n = 0;
    const tech = [...new Set(links.filter(([from, h]) => !/^\d{4}-/.test(from) && /-replay\.html#m\d+r\d+@p\d+$/.test(h)).map(([from]) => from))];
    for (const from of tech) {
      const mine = links.filter(([f, h]) => f === from && /-replay\.html#m\d+r\d+@p\d+$/.test(h)).slice(0, 3);
      for (const [, h] of mine) {
        const cut = h.indexOf('#');
    const file = cut < 0 ? h : h.slice(0, cut), frag = cut < 0 ? null : h.slice(cut + 1);
        const m = /^(m\d+r\d+)@p(\d+)$/.exec(frag);
        await replayAt(file, m[1], +m[2], null);
        n++;
      }
    }
    if (!n) fail('site', 'no 中盤 page links a replay position');
    console.log(`opened ${n} case links from ${tech.length} pages`);
  }

  // 3d. tst-openers: a class tile opens its build and the board animates
  if (pages.includes('tst-openers.html')) {
    const rel = 'tst-openers.html';
    const { pg, errs } = await open(ctx, base, rel);
    const d = pg.locator('details[data-s]').first();
    await d.locator('summary').click();
    const tile = d.locator('.tl figure').first();
    await tile.waitFor();
    await tile.click();
    const panel = d.locator('.bo');
    await pg.waitForTimeout(200);
    const a = await panel.evaluate((p) => ({ hidden: p.hidden, svg: p.querySelectorAll('svg').length, html: p.innerHTML.length && p.querySelector('svg') && p.querySelector('svg').innerHTML }));
    if (a.hidden || !a.svg) fail(rel, 'a class tile did not open its build panel');
    if ((await tile.getAttribute('aria-expanded')) !== 'true') fail(rel, 'the clicked tile is not marked expanded');
    await pg.waitForTimeout(1500);
    const b = await panel.evaluate((p) => p.querySelector('svg') && p.querySelector('svg').innerHTML);
    if (a.html === b) fail(rel, 'the build panel did not animate in 1.5 s');
    if (shots) { await panel.scrollIntoViewIfNeeded(); await pg.screenshot({ path: path.join(shots, 'tst-openers-tile.png') }); }
    for (const e of errs) fail(rel + ' (tile click)', e);
    console.log(`opened a class tile on ${rel}`);
    await pg.close();
  }

  if (shots) {
    const { pg } = await open(ctx, base, 'index.html');
    await pg.screenshot({ path: path.join(shots, 'index.png') });
    await pg.close();
    const r = await open(ctx, base, latest);
    await r.pg.screenshot({ path: path.join(shots, 'report-top.png') });
    await r.pg.close();
  }

  await browser.close();
  srv.close();
  if (failures.length) {
    console.error(`\n${failures.length} problem(s):`);
    for (const f of failures) console.error('  ' + f);
    process.exit(1);
  }
  console.log('site check: ok');
})().catch((e) => { console.error(e); process.exit(1); });

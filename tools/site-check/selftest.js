// check.js's mutants: copy a rendered site, plant one defect per kind, and require check.js to
// report every one of them. A check that passes a planted defect is a comment, not a gate.
//
//   node tools/site-check/selftest.js <site-dir>
//
// The control is the CI step before this one: check.js on the same unplanted site, which must pass.
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const src = path.resolve(process.argv[2] || '');
if (!process.argv[2] || !fs.existsSync(path.join(src, 'index.html'))) {
  console.error('usage: node tools/site-check/selftest.js <site-dir>');
  process.exit(2);
}
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'site-check-'));
fs.cpSync(src, dir, { recursive: true });

const pages = fs.readdirSync(dir).filter((f) => f.endsWith('.html')).sort();
const latest = pages.filter((p) => /^\d{4}-\d\d-\d\d\.html$/.test(p)).pop();
const replay = latest.replace('.html', '-replay.html');
const route = pages.find((p) => p === 'stray-cannon-ideal.html');

function edit(rel, fn) {
  const f = path.join(dir, rel);
  const s = fs.readFileSync(f, 'utf8');
  const t = fn(s);
  if (t === s) throw new Error(`mutant did not apply to ${rel}`);
  fs.writeFileSync(f, t);
}
const atBodyEnd = (html) => (s) => (s.includes('</body>') ? s.replace('</body>', html + '</body>') : s + html);

// [what is planted, the problem check.js must print]
const MUTANTS = [
  ['an uncaught exception', 'index.html: uncaught: planted-error',
    () => edit('index.html', atBodyEnd('<script>throw new Error("planted-error")</script>'))],
  ['a request to another host', 'index.html: off-site request: https://example.com/planted.png',
    () => edit('index.html', atBodyEnd('<img src="https://example.com/planted.png" alt="">'))],
  ['a video link with a fractional time', 'video link is not watch?v=<id>&t=<n>s',
    () => edit('index.html', atBodyEnd('<a href="https://www.youtube.com/watch?v=abcdefghijk&t=3.5s">v</a>'))],
  ['a link to a page that is not there', 'link to a page that does not exist: planted-missing.html',
    () => edit('index.html', atBodyEnd('<a href="planted-missing.html">x</a>'))],
  ['an element wider than a phone', `${latest}: scrolls sideways`,
    () => edit(latest, atBodyEnd('<div style="width:600px;height:1px"></div>'))],
  ['a replay link to a round the night does not have', 'replay link to a round the page does not list',
    () => edit(latest, atBodyEnd(`<a href="${replay}#m99r1">r</a>`))],
  ['a case link to a case the page does not hold', 'case link to a case the page does not hold',
    () => edit(latest, atBodyEnd(`<a href="${route}#2000-01-01-m1r1@p3">c</a>`))],
  ['an id link to an id that is not there', 'link to a fragment the page does not carry: index.html#planted-id',
    () => edit(latest, atBodyEnd('<a href="index.html#planted-id">i</a>'))],
  ['a tier nav that never lights', 'is not lit after its click',
    () => edit(latest, (s) => s.split('j === on ? "rn-on"').join('j === on ? "rn-x"'))],
  ['a replay page that ignores the position in its hash', 'opened at position',
    () => edit(replay, (s) => s.replace('<script', '<script>history.replaceState(null,"",location.pathname+location.hash.replace(/@p\\d+$/,""))</script><script'))],
  ['a class tile that never opens', 'a class tile did not open its build panel',
    () => edit('tst-openers.html', (s) => s.replace('<script', '<script>addEventListener("click",function(e){if(e.target.closest&&e.target.closest("[role=button]"))e.stopImmediatePropagation()},true)</script><script'))],
];

for (const [, , plant] of MUTANTS) plant();
const r = spawnSync(process.execPath, [path.join(__dirname, 'check.js'), dir], { encoding: 'utf8', maxBuffer: 1 << 28 });
fs.rmSync(dir, { recursive: true, force: true });
const out = r.stdout + r.stderr;
let survived = 0;
for (const [what, expect] of MUTANTS) {
  const killed = out.includes(expect);
  if (!killed) survived++;
  console.log(`${killed ? 'killed  ' : 'SURVIVED'} ${what}`);
}
if (r.status === 0) { console.error('check.js passed a site with every mutant planted'); process.exit(1); }
if (survived) {
  console.error(`${survived} of ${MUTANTS.length} mutants survived; check.js printed:\n${out}`);
  process.exit(1);
}
console.log(`site-check selftest: ${MUTANTS.length} of ${MUTANTS.length} mutants killed`);

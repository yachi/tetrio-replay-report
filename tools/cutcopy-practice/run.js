// t7.js adapted to the rendered docs/practice-cutcopy.html: it injects a CC_STATE hook into the page script before running.
const { chromium, devices } = require('playwright');
const fs = require('fs');
(async () => {
  const [page, art, out = process.cwd()] = process.argv.slice(2);
  fs.mkdirSync(`${out}/solved`, { recursive: true });
  let html = fs.readFileSync(page, 'utf8');
  const i = html.lastIndexOf('})();');
  html = html.slice(0, i) + '\nwindow.CC_STATE={piece:()=>piece&&piece.p,failed:()=>run.failed,locks:()=>run.locks,vis0:()=>VIS0,ids:()=>PZ.map(p=>p.id)};\n' + html.slice(i);
  const A = JSON.parse(fs.readFileSync(art, 'utf8'));
  const b = await chromium.launch();
  const ctx = await b.newContext({ ...devices['iPhone 13'] });
  const pg = await ctx.newPage(); pg.setDefaultTimeout(3000); const errs = []; pg.on('pageerror', e => errs.push(e.message));
  const reqs = []; pg.on('request', r => { if (!r.url().startsWith('data:') && !r.url().startsWith('about:')) reqs.push(r.url()); });
  await pg.setContent(html);
  const ids = await pg.evaluate(() => CC_STATE.ids());
  const sw = await pg.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  console.log('scrollWidth/innerWidth', sw);
  async function drop(s) {
    for (let k = 0; k < s.r; k++) await pg.click('.pad [data-a="cw"]');
    const pos = await pg.evaluate(([s]) => {
      const E = CCE, bc = document.getElementById('board'), rect = bc.getBoundingClientRect(), CS = rect.width / 10;
      const top = CC_STATE.vis0();
      const cells = E.cellsOf(s.piece, s.x, s.y, s.r); const xs = cells.map(c => c[0]), ys = cells.map(c => c[1]);
      const minx = Math.min(...xs), maxx = Math.max(...xs), miny = Math.min(...ys), maxy = Math.max(...ys);
      return { x: rect.left + (minx + (maxx - minx + 1) / 2) * CS, y: rect.top + ((miny - top) + (maxy - miny + 1) + 1) * CS };
    }, [s]);
    await pg.evaluate(({ x, y }) => { const bc = document.getElementById('board');
      const ev = (t, X, Y) => bc.dispatchEvent(new PointerEvent(t, { clientX: X, clientY: Y, pointerId: 1, pointerType: 'touch', bubbles: true }));
      ev('pointerdown', x, y - 60); ev('pointermove', x, y - 30); ev('pointermove', x, y); ev('pointerup', x, y); }, pos);
    await pg.waitForTimeout(80);
  }
  const rows = [];
  for (const [idx, id] of ids.entries()) {
    const pz = A.drills.find(d => d.id === id);
    await pg.selectOption('#psel', String(idx)); await pg.waitForTimeout(100);
    let passedAt = null; const log = [];
    for (let k = 0; k < pz.need + 1; k++) {
      const s = k < pz.need ? pz.solution[k] : null;
      if (!s) break;
      let curP = await pg.evaluate(() => CC_STATE.piece());
      if (curP !== s.piece) { await pg.click('.pad [data-a="hold"]'); curP = await pg.evaluate(() => CC_STATE.piece()); log.push('hold'); }
      if (curP !== s.piece) { log.push(`want ${s.piece} got ${curP}`); break; }
      await drop(s); log.push(s.piece);
      const st = await pg.textContent('#status');
      if (st.startsWith('✓')) { passedAt = k + 1; break; }
      if (await pg.evaluate(() => CC_STATE.failed())) { log.push('FAILED ' + st.slice(0, 30)); break; }
    }
    const st = (await pg.textContent('#status')).slice(0, 40);
    await pg.locator('#board').screenshot({ path: `${out}/solved/${idx}.png` });
    await pg.click('#reset'); await pg.click('#demoBtn'); await pg.waitForTimeout(6000);
    const cap = (await pg.textContent('#dcap')).slice(0, 60);
    await pg.locator('#board').screenshot({ path: `${out}/solved/${idx}-demo.png` });
    await pg.click('#demoBtn').catch(() => {}); await pg.click('#reset').catch(() => {});
    const row = { idx, id, label: pz.difficulty.label, need: pz.need, passedAt, locks: await pg.evaluate(() => CC_STATE.locks()), status: st, demo: cap, log: log.join(' ') };
    rows.push(row); console.log(JSON.stringify(row));
  }
  await pg.screenshot({ path: `${out}/full.png`, fullPage: true });
  console.log('errors', errs, 'requests', reqs);
  await b.close();
})();

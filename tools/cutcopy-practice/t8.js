const { chromium, devices } = require('playwright');
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ ...devices['iPhone 13'] });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(e.message));
  const html = require('fs').readFileSync('cc-test.html', 'utf8');
  await pg.setContent('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + html + '</body></html>');
  const n = await pg.$$eval('#psel option', o => o.length);
  for (let i = 0; i < n; i++) {
    await pg.selectOption('#psel', String(i)); await pg.waitForTimeout(100);
    // is any cell of the waiting piece's colour drawn in the board's top 3 visible rows?
    const vis = await pg.evaluate(() => { const bc = document.getElementById('board'), x = bc.getContext('2d'); const d = x.getImageData(0,0,bc.width,Math.round(bc.height*0)+Math.round(bc.width/10*3)).data; let n=0; for (let k=0;k<d.length;k+=4){ if (Math.max(d[k],d[k+1],d[k+2])>120) n++; } return n; });
    console.log(i, await pg.$eval('#psel', s=>s.options[s.selectedIndex].text), 'pieceVisible', vis>50);
    await pg.locator('.main').screenshot({ path: `vis/${i}.png` });
  }
  console.log('errors', errs); await b.close();
})();

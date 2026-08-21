import pkg from '/opt/node22/lib/node_modules/playwright/index.js';
const { chromium } = pkg;

const url = 'file:///home/user/prompt-generator/kiosk/screens.html';
const ids = ['s1','s2','s3','s4','s5','s6','s7'];

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 2 });
await page.goto(url, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(400);

for (const id of ids) {
  const el = await page.$('#' + id);
  await el.screenshot({ path: `/home/user/prompt-generator/kiosk/${id}.png` });
  console.log('shot', id);
}
await browser.close();
console.log('done');

import pkg from '/opt/node22/lib/node_modules/playwright/index.js';
const { chromium } = pkg;
const ids = ['s3en','s4en','s5en','s6en','s7en'];
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 2 });
await page.goto('file:///home/user/prompt-generator/kiosk/screens_en.html', { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(400);
for (const id of ids) {
  const el = await page.$('#' + id);
  await el.screenshot({ path: `/home/user/prompt-generator/kiosk/${id.replace('en','')}_en.png` });
  console.log('shot', id);
}
await browser.close();

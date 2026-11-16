const { chromium } = require('playwright');
const assert = require('node:assert/strict');

const origin = 'http://127.0.0.1:4173';
const edition = '/editions/v000100/2026/a000100/';

(async () => {
  const browser = await chromium.launch();
  try {
    for (const width of [390, 1440]) {
      const page = await browser.newPage({ viewport: { width, height: 840 } });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const home = await page.goto(origin + '/');
      assert(home.ok());
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      await page.locator('#q').fill('小滘');
      await page.locator('#searchResults a[href="' + edition + '"]').waitFor();
      await page.locator('#searchResults a[href^="/branch/"]').first().waitFor();
      await page.locator('#q').fill('p1');
      await page.locator('#searchResults a[href="' + edition + 'persons/p000001/"]').waitFor();
      await page.locator('#q').fill('729');
      await page.locator('#q').press('Enter');
      await page.waitForURL('**/reader.html?p=759');
      await page.locator('#info').getByText('原书第 729 页').waitFor();

      await page.goto(origin + '/reader.html?p=1300');
      await page.locator('#info').getByText('汉字繁简对照表（续）').waitFor();
      await page.locator('#mSingle').click();
      await page.keyboard.press('ArrowRight');
      await page.waitForURL('**/reader.html?p=1301');
      await page.locator('#info').getByText('封底').waitFor();
      await page.locator('#singlePage').click();
      await page.locator('#imageDialog[open]').waitFor();
      await page.locator('#imageZoom').click();
      await page.locator('#imageLarge.zoomed').waitFor();
      await page.locator('#imageClose').click();

      await page.goto(origin + edition + 'pages/pg000001/');
      const downloads = page.getByRole('link', { name: '下载本页 PDF' });
      const pdf = await page.request.get(origin + await downloads.getAttribute('href'));
      assert(pdf.ok() && (await pdf.body()).subarray(0, 4).toString() === '%PDF');
      await page.locator('#editionName').fill('馮允思');
      await page.locator('#editionSearchResults a[href="' + edition + 'persons/p000001/"]').waitFor();
      await page.locator('#editionName').fill('p1');
      await page.locator('#editionSearchResults a[href="' + edition + 'persons/p000001/"]').waitFor();
      await page.goto(origin + edition);
      const searchInput = page.locator('#editionName');
      const results = page.locator('#editionSearchResults a');
      const targets = () => results.evaluateAll(links => links.map(link => link.getAttribute('href')));
      const sheet15 = edition + 'pages/pg000015/';
      const person15 = edition + 'persons/p000015/';
      await searchInput.fill('15');
      await results.nth(1).waitFor();
      assert.deepEqual(await targets(), [sheet15, person15]);
      assert.match(await results.nth(1).innerText(), /人物.*冯世达.*p000015/s);
      await searchInput.press('Enter');
      await results.nth(1).waitFor();
      assert.deepEqual(await targets(), [sheet15, person15]);
      for (const [query, target] of [['第15页', sheet15], ['15页', sheet15], ['p15', person15]]) {
        await searchInput.fill(query);
        await page.getByText('找到 1 条相关记录', { exact: true }).waitFor();
        assert.deepEqual(await targets(), [target]);
      }
      await page.locator('#editionName').fill('冯杜泮');
      await page.locator('#editionSearchResults a[href="' + edition + 'persons/p001069/"]').waitFor();
      assert.equal(await page.locator('#editionSearchResults a').count(), 1);
      await page.goto(origin + edition + 'read/?p=3');
      await page.locator('#mScroll[aria-pressed="true"]').waitFor();
      if (width <= 650) {
        assert(await page.locator('#jumpToggle').isVisible());
        const bar = await page.locator('.edition-readerbar').boundingBox();
        assert(bar.height < 50);
        await page.locator('#jumpToggle').click();
      }
      await page.locator('#jump').fill('6');
      await page.locator('#jump').press('Enter');
      await page.waitForURL('**/read/?p=6');
      await page.locator('#mSingle').click();
      await page.locator('#mSingle[aria-pressed="true"]').waitFor();
      assert.deepEqual(errors, []);
      console.log(`Search and reading flows passed at ${width}px`);
      await page.close();
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

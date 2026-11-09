// Run against an explicitly launched packaged app with an isolated fixture library.
// Arguments: fixture.json, phase (markdown, recording, delete).
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.VIOLILT_PLAYWRIGHT || 'playwright');

(async () => {
  const fixture = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const phase = process.argv[3];
  const browser = await chromium.connectOverCDP(process.env.VIOLILT_TEST_CDP || 'http://127.0.0.1:9235');
  try {
    const page = browser.contexts().flatMap(context => context.pages()).find(page => page.url().startsWith('http://127.0.0.1:'));
    assert(page, 'Packaged application page must exist');
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.waitForFunction(() => typeof window.pywebview?.api?.reveal_document === 'function' && typeof window.pywebview?.api?.reveal_recording === 'function');
    const state = await page.evaluate(() => window.pywebview.api.get_state());
    assert.equal(path.resolve(state.storage), path.resolve(fixture.data), 'Never test against the user library');
    assert.equal(await page.locator('.preview-label').count(), 0);
    const menu = page.getByRole('menu');
    if (phase === 'markdown') {
      await page.getByRole('button', {name: 'Home', exact: true}).click();
      await page.locator('.recent-reading').filter({hasText: 'Packaged context menu'}).click({button: 'right'});
      assert.equal(await menu.getByRole('menuitem').count(), 2);
      await page.screenshot({path: path.join(fixture.root, 'packaged-markdown-menu.png')});
      await menu.getByRole('menuitem', {name: 'Show in File Explorer'}).click();
    } else if (phase === 'recording') {
      await page.getByRole('button', {name: 'Home', exact: true}).click();
      await page.locator('.saved-reading').click({button: 'right'});
      await menu.getByRole('menuitem', {name: 'Show in File Explorer'}).click();
    } else if (phase === 'delete') {
      const original = fs.readFileSync(fixture.source);
      await page.locator('.document-list > button').filter({hasText: 'Keep this reading'}).click();
      await page.getByRole('button', {name: 'Edit', exact: true}).click();
      const editor = page.getByLabel('Markdown editor');
      const before = await editor.inputValue();
      await page.locator('.document-list > button').filter({hasText: 'Packaged context menu'}).click({button: 'right'});
      await menu.getByRole('menuitem', {name: 'Delete…'}).click();
      await page.getByRole('dialog').getByRole('button', {name: 'Remove', exact: true}).click();
      await page.waitForFunction(() => document.querySelectorAll('.document-list > button').length === 1);
      assert.equal(await editor.inputValue(), before);
      assert.deepEqual(fs.readFileSync(fixture.source), original);
      await page.getByRole('button', {name: 'Your recordings'}).click();
      await page.locator('.recording-card').click({button: 'right'});
      await menu.getByRole('menuitem', {name: 'Delete…'}).click();
      await page.getByRole('dialog').getByRole('button', {name: 'Remove', exact: true}).click();
      await page.waitForFunction(() => !document.querySelector('.recording-card'));
      assert(fs.existsSync(fixture.audio), 'Default recording removal must retain audio');
      assert(await page.getByTitle('Export recording', {exact: true}).isDisabled());
      await page.screenshot({path: path.join(fixture.root, 'packaged-after-removal.png')});
    } else throw new Error('Choose markdown, recording, or delete phase');
    assert.equal(await page.locator('.error-banner').count(), 0);
    assert.deepEqual(errors, []);
    const result = {success: true, phase, packaged: true, storage: state.storage, pageErrors: errors};
    fs.writeFileSync(path.join(fixture.root, `result-${phase}.json`), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });

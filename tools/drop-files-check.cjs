// Native file drop check against a source or packaged WebView2 app launched with
// an isolated --data-dir and an explicit local remote-debugging port.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.LILT_PLAYWRIGHT || 'playwright');

(async () => {
  const root = path.resolve(process.argv[2]);
  const endpoint = process.argv[3] || 'http://127.0.0.1:9237';
  let browser;
  const deadline = Date.now() + 20000;
  while (!browser) {
    try { browser = await chromium.connectOverCDP(endpoint); }
    catch (error) {
      if (Date.now() >= deadline) throw error;
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }
  try {
    const page = browser.contexts().flatMap(context => context.pages()).find(page => page.url().startsWith('http://127.0.0.1:'));
    assert(page, 'Native application page must exist');
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.locator('.home-page').waitFor({timeout: 25000});
    const state = await page.evaluate(() => window.pywebview.api.get_state());
    assert.equal(path.resolve(state.storage), path.join(root, 'data'), 'Use only the isolated test library');
    const files = [path.join(root, 'Dropped, with spaces & symbols.md'), path.join(root, 'Second reading.markdown')];
    const text = ['# A reading that landed\n\nKeep this original intact.', '# Another little reading\n\nA few words worth listening to.'];
    files.forEach((file, index) => fs.writeFileSync(file, text[index], 'utf8'));
    const session = await page.context().newCDPSession(page);
    const drag = {items: [], files, dragOperationsMask: 1};
    await session.send('Input.dispatchDragEvent', {type: 'dragEnter', x: 100, y: 200, data: drag});
    await session.send('Input.dispatchDragEvent', {type: 'dragOver', x: 450, y: 350, data: drag});
    await page.locator('.file-drop-overlay.visible').waitFor();
    await page.screenshot({path: path.join(root, 'native-drop-hover.png')});
    await session.send('Input.dispatchDragEvent', {type: 'drop', x: 450, y: 350, data: drag});
    await page.locator('.studio-layout').waitFor({timeout: 20000});
    await page.waitForFunction(count => document.querySelectorAll('.document-list > button').length === count, state.documents.length + 2);
    const next = await page.evaluate(() => window.pywebview.api.get_state());
    for (const file of files) assert(next.documents.some(doc => path.resolve(doc.source || '') === file), 'Original file paths must survive the drop');
    for (let index = 0; index < files.length; index++) assert.equal(fs.readFileSync(files[index], 'utf8'), text[index]);
    assert.equal(await page.locator('.error-banner').count(), 0);
    assert.deepEqual(errors, []);
    await page.screenshot({path: path.join(root, 'native-drop-imported.png')});
    const result = {success: true, nativeFileObjects: true, imported: files.length, originalPathsRetained: true, originalsUntouched: true, pageErrors: errors};
    fs.writeFileSync(path.join(root, 'drop-check.json'), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });

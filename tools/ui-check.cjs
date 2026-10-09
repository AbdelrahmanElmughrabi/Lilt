const { chromium } = require(process.env.LILT_PLAYWRIGHT || 'playwright');
const path = require('node:path');
const fs = require('node:fs');

(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
  const pages = browser.contexts().flatMap(context => context.pages());
  const page = pages.find(page => page.url().startsWith('http://127.0.0.1:'));
  if (!page) throw new Error('Desktop WebView was not found');
  await page.reload();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.getByRole('heading', { name: 'Find your rhythm.' }).waitFor({ timeout: 15000 });
  if (await page.getByText('Interface preview', { exact: true }).count()) throw new Error('The desktop bridge did not initialize');
  await page.getByRole('button', { name: /^The art of paying attention/ }).click();
  const state = await page.evaluate(() => window.pywebview.api.get_state());
  fs.mkdirSync(path.resolve('artifacts'), { recursive: true });
  await page.screenshot({ path: path.resolve('artifacts/ui-studio.png'), animations: 'disabled' });
  const overflow = await page.evaluate(() => ({
    documentWidth: document.documentElement.scrollWidth,
    viewport: window.innerWidth,
    panel: document.querySelector('.voice-panel').getBoundingClientRect().toJSON(),
  }));
  await page.getByRole('button', { name: 'Edit', exact: true }).click();
  const editor = page.getByRole('textbox', { name: 'Markdown editor' });
  if (!(await editor.inputValue()).includes('The art of paying attention')) throw new Error('Editor did not load the sample');
  await page.getByRole('button', { name: 'Spoken', exact: true }).click();
  await page.getByRole('heading', { name: 'A clear view of every word.' }).waitFor();
  if ((await page.locator('.spoken-text').innerText()).includes('print(')) throw new Error('Code appeared in the default speech preview');
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('button', { name: /After hours/ }).click();
  await page.locator('.app-shell.dark').waitFor();
  await page.screenshot({ path: path.resolve('artifacts/ui-settings-dark.png'), animations: 'disabled' });
  await page.getByRole('button', { name: /Daylight/ }).click();
  await page.getByRole('button', { name: /^Your recordings/ }).click();
  await page.getByRole('heading', { name: 'Your listening shelf.' }).waitFor();
  await page.screenshot({ path: path.resolve('artifacts/ui-library.png'), animations: 'disabled' });
  await page.getByRole('button', { name: 'Reading room', exact: true }).click();
  await page.getByRole('button', { name: 'Read', exact: true }).click();
  console.log(JSON.stringify({ success: true, nativeBridge: true, model: state.model.state,
    availableVoices: state.model.voices.length, overflow, pageErrors: errors,
    screenshots: ['artifacts/ui-studio.png', 'artifacts/ui-settings-dark.png', 'artifacts/ui-library.png'] }));
  if (errors.length || overflow.documentWidth > overflow.viewport) process.exitCode = 1;
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });

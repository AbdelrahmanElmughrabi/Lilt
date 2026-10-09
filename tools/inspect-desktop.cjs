const { chromium } = require(process.env.LILT_PLAYWRIGHT || 'playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
  const page = browser.contexts().flatMap(context => context.pages()).find(page => page.url().startsWith('http://127.0.0.1:'));
  console.log(JSON.stringify(await page.evaluate(async () => ({
    state: await window.pywebview.api.get_state(),
    audio: { src: document.querySelector('audio').src, ready: document.querySelector('audio').readyState, error: document.querySelector('audio').error?.message },
    alert: document.querySelector('.error-banner')?.innerText,
  })), null, 2));
  await page.screenshot({path:'artifacts/desktop-debug.png'});
  await browser.close();
})().catch(error => {console.error(error); process.exit(1);});

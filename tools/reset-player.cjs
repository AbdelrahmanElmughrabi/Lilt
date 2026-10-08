const {chromium} = require(process.env.FOLIO_PLAYWRIGHT || 'playwright');
(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
  const page = browser.contexts().flatMap(context => context.pages()).find(page => page.url().startsWith('http://127.0.0.1:'));
  await page.evaluate(async () => {
    const audio = document.querySelector('audio');
    audio.pause(); audio.currentTime = 0;
    const id = audio.src.match(/media\/([a-f0-9]+)\.wav/)[1];
    await window.pywebview.api.save_position(id, 0);
  });
  await page.screenshot({path:'artifacts/ui-studio.png',animations:'disabled'});
  await browser.close();
})().catch(error => {console.error(error);process.exit(1);});

const { chromium } = require(process.env.VIOLILT_PLAYWRIGHT || 'playwright');
const path = require('node:path');
const fs = require('node:fs');

(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
  const page = browser.contexts().flatMap(context => context.pages()).find(page => page.url().startsWith('http://127.0.0.1:'));
  if (!page) throw new Error('Violilt desktop window was not found');
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.locator('.home-page').waitFor({ timeout: 15000 });
  await page.getByRole('button', { name: 'Reading room', exact: true }).first().click();
  await page.getByRole('heading', { name: 'Find your rhythm.' }).waitFor({ timeout: 15000 });
  const initial = await page.evaluate(() => window.pywebview.api.get_state());
  if (initial.model.state !== 'ready') throw new Error('Bundled voice assets were not recognized');
  const started = Date.now();
  let jobId = initial.active?.id;
  if (!jobId && process.env.VIOLILT_REUSE_JOB) jobId = initial.jobs.find(job => !job.preview)?.id;
  if (!jobId) {
    await page.getByRole('button', { name: 'Create your audio', exact: false }).click();
    await page.getByRole('button', { name: 'Stop generation', exact: true }).waitFor();
    jobId = await page.evaluate(async () => (await window.pywebview.api.get_state()).active.id);
  }
  // Reading controls must remain usable while inference runs in the child process.
  await page.getByRole('button', { name: 'Edit', exact: true }).click();
  await page.getByRole('textbox', { name: 'Markdown editor' }).waitFor();
  await page.getByRole('button', { name: 'Read', exact: true }).click();
  while (true) {
    const job = await page.evaluate(async id => (await window.pywebview.api.get_state()).jobs.find(job => job.id === id), jobId);
    if (job.state === 'failed') throw new Error(job.message);
    if (job.state === 'completed') break;
    if (Date.now() - started > 300000) throw new Error('Generation did not finish within five minutes');
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  await page.waitForFunction(() => document.querySelector('audio').readyState >= 1);
  await page.evaluate(() => { document.querySelector('audio').muted = true; });
  await page.getByRole('button', { name: 'Play', exact: true }).click();
  await page.waitForFunction(() => !document.querySelector('audio').paused && document.querySelector('audio').currentTime > 0);
  await page.getByRole('button', { name: 'Pause', exact: true }).click();
  await page.getByRole('button', { name: 'Forward 10 seconds', exact: true }).click();
  await page.evaluate(async id => {
    const audio = document.querySelector('audio');
    await window.pywebview.api.save_position(id, audio.currentTime);
  }, jobId);
  const playback = await page.evaluate(() => ({ duration: document.querySelector('audio').duration, position: document.querySelector('audio').currentTime }));
  if (playback.duration < 30 || playback.position < 10) throw new Error('Playback duration or seeking failed');
  fs.mkdirSync(path.resolve('artifacts'), { recursive: true });
  await page.screenshot({ path: path.resolve('artifacts/ui-studio.png') });
  await page.getByRole('button', { name: /^Your recordings/ }).click();
  await page.getByRole('heading', { name: 'Your listening shelf.' }).waitFor();
  await page.screenshot({ path: path.resolve('artifacts/ui-library.png') });
  await page.reload();
  await page.waitForFunction(() => document.querySelector('audio')?.readyState >= 1);
  const restoredPosition = await page.evaluate(() => document.querySelector('audio').currentTime);
  if (Math.abs(restoredPosition - playback.position) > 0.6) throw new Error('Listening position did not survive a reload');
  const finished = await page.evaluate(async id => (await window.pywebview.api.get_state()).jobs.find(job => job.id === id), jobId);
  console.log(JSON.stringify({ success: true, packagedDesktop: true, generationSeconds: (Date.now() - started) / 1000,
    job: { id: jobId, words: finished.words, sections: finished.total, duration: finished.duration }, playback, restoredPosition, pageErrors: errors }));
  if (errors.length) process.exitCode = 1;
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });

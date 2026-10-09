const { chromium } = require(process.env.LILT_PLAYWRIGHT || 'playwright');
const path = require('node:path');
const fs = require('node:fs');

(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
  const page = browser.contexts().flatMap(context => context.pages()).find(page => page.url().startsWith('http://127.0.0.1:'));
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.getByRole('heading', {name:'Find your rhythm.'}).waitFor();
  await page.getByTitle('New reading', {exact:true}).click();
  await page.getByRole('textbox', {name:'Markdown editor'}).fill('# A temporary reading\n\nWords that save automatically.');
  await page.getByRole('button', {name:/^A temporary reading/}).waitFor();
  await page.getByTitle('Remove reading', {exact:true}).click();
  const dialog = page.getByRole('dialog', {name:'Remove this reading?'});
  await dialog.waitFor();
  await dialog.getByRole('button', {name:'Keep it',exact:true}).click();
  await dialog.waitFor({state:'hidden'});
  await page.getByTitle('Remove reading', {exact:true}).click();
  await dialog.getByRole('button', {name:'Remove',exact:true}).click();
  await dialog.waitFor({state:'hidden'});
  if ((await page.evaluate(() => window.pywebview.api.get_state())).documents.some(doc => doc.title === 'A temporary reading')) throw new Error('Working-copy removal failed');

  await page.evaluate(() => { document.querySelector('audio').muted = true; });
  await page.getByRole('button', {name:/Listen to a sample/}).click();
  const previewId = await page.evaluate(async () => (await window.pywebview.api.get_state()).active.id);
  const deadline = Date.now() + 120000;
  while (true) {
    const job = await page.evaluate(async id => (await window.pywebview.api.get_state()).jobs.find(job => job.id === id), previewId);
    if (job.state === 'failed') throw new Error(job.message);
    if (job.state === 'completed') break;
    if (Date.now() > deadline) throw new Error('Voice preview did not finish');
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  await page.locator('.player-track strong').filter({hasText:'A little voice preview'}).waitFor();
  await page.evaluate(() => document.querySelector('audio').pause());
  await page.getByRole('button', {name:/^Your recordings/}).click();
  const longCard = page.locator('.recording-card').filter({has:page.getByRole('heading',{name:'A longer afternoon',exact:true})});
  if (await longCard.count()) {
    await longCard.getByTitle('Remove recording', {exact:true}).click();
    const remove = page.getByRole('dialog', {name:'Remove this recording?'});
    if (await remove.getByRole('checkbox').isChecked()) throw new Error('Audio deletion must default to off');
    await remove.getByRole('button',{name:'Remove',exact:true}).click();
    await remove.waitFor({state:'hidden'});
  }
  const sampleCard = page.locator('.recording-card').filter({has:page.getByRole('heading',{name:'The art of paying attention',exact:true})});
  await sampleCard.getByRole('button',{name:'Listen',exact:true}).click();
  await page.waitForFunction(() => document.querySelector('audio').readyState >= 1);
  await page.evaluate(() => document.querySelector('audio').pause());
  await page.screenshot({path:path.resolve('artifacts/ui-library.png'),animations:'disabled'});
  await page.getByRole('button',{name:/^A longer afternoon/}).click();
  await page.getByTitle('Remove reading',{exact:true}).click();
  await page.getByRole('dialog',{name:'Remove this reading?'}).getByRole('button',{name:'Remove',exact:true}).click();
  await page.getByRole('dialog',{name:'Remove this reading?'}).waitFor({state:'hidden'});
  await page.getByRole('button',{name:/^The art of paying attention/}).click();
  await page.getByRole('button',{name:'Read',exact:true}).click();
  await page.screenshot({path:path.resolve('artifacts/ui-studio.png'),animations:'disabled'});
  if (errors.length) throw new Error(errors.join('; '));
  const status = { success:true, autosave:true, removalDialogs:true, explicitAudioDeletion:true, realVoicePreview:true, olderRecordingSelection:true, pageErrors:errors };
  fs.writeFileSync(path.resolve('artifacts/library-check.json'),JSON.stringify(status,null,2));
  console.log(JSON.stringify(status));
  await browser.close();
})().catch(error => {console.error(error);process.exit(1);});

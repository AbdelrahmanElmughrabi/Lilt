const { chromium } = require(process.env.VIOLILT_PLAYWRIGHT || 'playwright');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
  const page = browser.contexts().flatMap(context => context.pages()).find(page => page.url().startsWith('http://127.0.0.1:'));
  const paragraph = 'A long reading should leave room for a thought to develop. We can follow a question through several paragraphs, pause at a heading, and come back to an earlier idea. The document keeps its own order. Each completed section is saved before the next begins, so a pause in the work does not mean starting again. There is time to listen, and time to return.';
  const markdown = '# A longer afternoon\n\n' + Array.from({ length: 10 }, (_, i) => `## Chapter ${i + 1}\n\n${paragraph}`).join('\n\n');
  const job = await page.evaluate(async text => {
    const api = window.pywebview.api;
    const document = await api.new_document();
    await api.save_document(document.id, text);
    const settings = (await api.get_state()).settings;
    return api.generate(document.id, text, { ...settings, speed: 1.8 });
  }, markdown);
  console.log(JSON.stringify({ started: job.id, words: job.words, sections: job.total }));
  const started = Date.now();
  let cancelled = false, firstSectionTime;
  const firstSection = path.resolve('.app-data', 'jobs', job.id, 'section-000000.wav');
  while (true) {
    const current = await page.evaluate(async id => (await window.pywebview.api.get_state()).jobs.find(job => job.id === id), job.id);
    if (current.state === 'failed') throw new Error(current.message);
    if (!cancelled && current.completed >= 1) {
      await page.evaluate(() => window.pywebview.api.cancel_generation());
      while ((await page.evaluate(() => window.pywebview.api.get_state())).active) await new Promise(resolve => setTimeout(resolve, 300));
      firstSectionTime = fs.statSync(firstSection).mtimeMs;
      await page.evaluate(id => window.pywebview.api.resume_job(id), job.id);
      cancelled = true;
      console.log('Cancelled at a section boundary and resumed the same immutable job.');
    }
    if (current.state === 'completed') {
      if (!cancelled || fs.statSync(firstSection).mtimeMs !== firstSectionTime) throw new Error('The completed section was regenerated on resume');
      console.log(JSON.stringify({ success: true, localPackagedWorker: true, words: current.words, sections: current.total,
        duration: current.duration, elapsed: (Date.now() - started) / 1000, cancellationAndResume: true, reusedSection: true }));
      break;
    }
    if (Date.now() - started > 600000) throw new Error('Long-reading generation exceeded ten minutes');
    // The main UI must continue answering layout/read requests while speech runs.
    if (!(await page.getByRole('button', {name:'Read',exact:true}).isVisible())) throw new Error('Reading controls disappeared');
    await new Promise(resolve => setTimeout(resolve, 700));
  }
  await browser.close();
})().catch(error => {console.error(error); process.exit(1);});

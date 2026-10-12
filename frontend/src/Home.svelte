<script lang="ts">
  import { ArrowRight, BookOpen, Download, FileText, FolderOpen, Headphones, Play, Plus, RotateCcw } from '@lucide/svelte';
  import type { DocumentSummary, Job } from './api';
  let { documents, jobs, generating, openDocument, importDocument, newDocument, listen, exportAudio, continueJob, showLibrary, showStudio, voiceName }: {
    documents: DocumentSummary[]; jobs: Job[]; generating: boolean;
    openDocument: (id: string) => void; importDocument: () => void; newDocument: () => void;
    listen: (job: Job) => void; exportAudio: (job: Job) => void; continueJob: (job: Job) => void;
    showLibrary: () => void; showStudio: () => void; voiceName: (id: string) => string;
  } = $props();
  const saved = $derived(jobs.filter(job => !job.preview && job.state === 'completed'));
  const unfinished = $derived(jobs.filter(job => !job.preview && ['cancelled', 'failed', 'interrupted'].includes(job.state)));
  const recent = $derived([...documents].sort((a, b) => (b.opened || b.created) - (a.opened || a.created)).slice(0, 5));
  const resume = $derived([...saved].filter(job => job.position > 0 && job.position < job.duration - 2).sort((a, b) => (b.last_listened || b.created) - (a.last_listened || a.created))[0]);
  const featured = $derived(resume || saved[0]);
  const minutes = $derived(Math.round(saved.reduce((total, job) => total + job.duration, 0) / 60));
  function time(value: number) { return `${Math.floor(value / 60)}:${String(Math.floor(value % 60)).padStart(2, '0')}`; }
  function opened(value: number) { const day = new Date(value * 1000); return day.toLocaleDateString('en', { month: 'short', day: 'numeric' }) + ' · ' + day.toLocaleTimeString('en', { hour: 'numeric', minute: '2-digit' }); }
  function filename(doc: DocumentSummary) { return doc.source?.split(/[\\/]/).pop() || 'Markdown reading'; }
</script>

<main class="home-page">
  <div class="home-heading"><div><span class="eyebrow">YOUR WORDS, WAITING FOR YOU</span><h1>A little space<br />for <em>listening.</em></h1><p>Pick up a reading. Return to a familiar voice.</p></div><div class="home-totals"><span><strong>{saved.length}</strong> saved {saved.length === 1 ? 'recording' : 'recordings'}</span><span><strong>{minutes}</strong> minutes on your shelf</span></div></div>
  <div class="home-top-grid">
    <section class="listen-card" aria-label={resume ? 'Continue listening' : 'Your next listen'}>
      <div class="listen-art" aria-hidden="true">{#each [18, 34, 50, 30, 64, 44, 72, 38, 56, 26, 42, 20] as height}<span style:height={`${height}px`}></span>{/each}</div>
      <div class="listen-content"><span class="eyebrow">{resume ? 'RIGHT WHERE YOU LEFT OFF' : 'MAKE YOURSELF COMFORTABLE'}</span><h2>{featured ? featured.title : 'Good words deserve a voice.'}</h2><p>{featured ? `${voiceName(featured.voice)} · ${time(featured.duration)} · Saved WAV` : 'Your first listen starts with a Markdown file or a few words of your own.'}</p>
        {#if featured}{#if resume}<div class="resume-track" aria-label={`${time(resume.position)} listened of ${time(resume.duration)}`}><span style:width={`${Math.min(100, resume.position / resume.duration * 100)}%`}></span></div>{/if}<div class="listen-actions"><button class="primary-button" onclick={() => listen(featured)}><Play size={15} fill="currentColor" /> {resume ? 'Continue listening' : 'Listen now'}</button>{#if resume}<span>{time(resume.position)} of {time(resume.duration)}</span>{/if}</div>{:else}<button class="primary-button" onclick={importDocument}><FolderOpen size={16} /> Import Markdown <ArrowRight size={16} /></button>{/if}
      </div>
    </section>
    <section class="start-card" aria-label="Start a reading"><span class="eyebrow">SOMETHING NEW</span><h2>Bring your words.</h2><p>A note, an article, a whole chapter.<br />We’ll keep your place.</p><button onclick={importDocument}><FolderOpen size={18} /><span>Import Markdown<small>Choose a .md or .markdown file</small></span><ArrowRight size={16} /></button><button onclick={newDocument}><Plus size={18} /><span>New reading<small>Write or paste your text</small></span><ArrowRight size={16} /></button></section>
  </div>
  <div class="home-shelf-grid">
    <section class="home-section" aria-label="Recent readings"><div class="section-heading"><h2><BookOpen size={17} /> Recent readings</h2><button onclick={showStudio}>Reading room <ArrowRight size={14} /></button></div>{#if recent.length}<div class="recent-list">{#each recent as doc}<button class="recent-reading" onclick={() => openDocument(doc.id)}><span class="file-tile"><FileText size={19} strokeWidth={1.4} /></span><span class="reading-details"><strong>{doc.title}</strong><small>{filename(doc)} {#if doc.words}· {doc.words.toLocaleString()} words{/if}</small><small>{doc.opened ? 'Opened' : 'Added'} {opened(doc.opened || doc.created)}</small></span><ArrowRight size={15} /></button>{/each}</div>{:else}<div class="home-empty"><FileText size={23} /><p>Your readings will be waiting here.<br />Import a file or start a new reading.</p></div>{/if}</section>
    <section class="home-section" aria-label="Saved recordings"><div class="section-heading"><h2><Headphones size={17} /> Saved recordings</h2><button onclick={showLibrary}>View all <ArrowRight size={14} /></button></div>{#if saved.length}<div class="saved-list">{#each saved.slice(0, 4) as job}<div class="saved-reading"><button class="saved-play" aria-label={`Play ${job.title}`} onclick={() => listen(job)}><Play size={15} fill="currentColor" /></button><div class="reading-details"><strong>{job.title}</strong><small>{voiceName(job.voice)} · {time(job.duration)} · WAV</small></div><button class="icon-button" aria-label={`Export ${job.title} as WAV`} title="Export WAV" onclick={() => exportAudio(job)}><Download size={17} /></button></div>{/each}</div><p class="saved-hint">Saved automatically. Listen again without generating.</p>{:else}<div class="home-empty"><Headphones size={23} /><p>Audio saves here when a reading is finished.<br />Ready whenever you want another listen.</p></div>{/if}
      {#if unfinished.length}<div class="unfinished"><h3>Unfinished readings</h3>{#each unfinished.slice(0, 3) as job}<div class="unfinished-row"><div class="reading-details"><strong>{job.title}</strong><small>{job.completed} of {job.total} sections saved</small>{#if job.resume_message}<small class="resume-note">{job.resume_message}</small>{/if}</div>{#if (job.available_duration || 0) > 0}<button class="icon-button" title="Listen to available audio" aria-label={`Listen to available audio for ${job.title}`} onclick={() => listen(job)}><Headphones size={16} /></button>{/if}{#if job.can_resume !== false}<button class="finish-button" disabled={generating} onclick={() => continueJob(job)}><RotateCcw size={13} /> Continue</button>{/if}</div>{/each}</div>{/if}
    </section>
  </div>
</main>

<style>
  .home-page { flex: 1; min-height: 0; overflow: auto; padding: 32px clamp(24px, 3.7vw, 58px) 40px; scrollbar-width: thin; }
  .home-heading { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 27px; gap: 24px; }
  .home-heading h1 { font: 46px/1.1 Georgia, serif; letter-spacing: -1.7px; margin: 13px 0 12px; }
  .home-heading h1 em { color: var(--accent); font-weight: normal; }
  .home-heading p { color: var(--muted); margin: 0; font-size: 12px; }
  .home-totals { display: flex; gap: 24px; color: var(--muted); font-size: 10px; padding-bottom: 3px; white-space: nowrap; }
  .home-totals strong { display: block; font: 25px Georgia, serif; color: var(--ink); margin-bottom: 7px; }
  .home-top-grid { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(235px, 1fr); gap: 20px; margin-bottom: 32px; }
  .listen-card { display: flex; align-items: center; gap: 25px; background: var(--surface-alt); border: 1px solid var(--line); border-radius: 12px; padding: 28px 24px; min-width: 0; }
  .listen-art { display: flex; align-items: center; justify-content: center; gap: 4px; width: 88px; flex-shrink: 0; height: 120px; }
  .listen-art span { width: 3px; border-radius: 4px; background: var(--accent); opacity: .65; }
  .listen-content { min-width: 0; flex: 1; }
  .listen-content h2 { font: 25px/1.25 Georgia, serif; letter-spacing: -.5px; margin: 13px 0 10px; overflow-wrap: anywhere; }
  .listen-content p { font-size: 10px; line-height: 1.6; color: var(--muted); margin: 0 0 17px; }
  .listen-content .eyebrow { font-size: 8px; letter-spacing: 1.2px; }
  .listen-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; }
  .listen-actions > span { color: var(--muted); font-size: 9px; }
  .resume-track { height: 3px; background: var(--line-strong); border-radius: 3px; margin: 0 0 16px; overflow: hidden; }
  .resume-track span { display: block; height: 100%; background: var(--accent); }
  .start-card { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 24px; }
  .start-card h2 { font: 22px Georgia, serif; letter-spacing: -.4px; margin: 11px 0 8px; }
  .start-card p { color: var(--muted); font-size: 11px; line-height: 1.7; margin: 0 0 13px; }
  .start-card > button { display: flex; align-items: center; gap: 11px; text-align: left; width: 100%; padding: 12px 0; border-top: 1px solid var(--line); }
  .start-card > button:hover { color: var(--accent); }
  .start-card > button > span { flex: 1; font-size: 11px; }
  .start-card small { display: block; margin-top: 4px; font-size: 9px; color: var(--muted); }
  .start-card > button > :global(svg:first-child) { color: var(--accent); }
  .home-shelf-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 32px; }
  .home-section { min-width: 0; }
  .section-heading { display: flex; justify-content: space-between; gap: 10px; align-items: center; padding-bottom: 15px; border-bottom: 1px solid var(--line-strong); }
  .section-heading h2 { margin: 0; display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 600; }
  .section-heading h2 :global(svg) { color: var(--muted); }
  .section-heading > button { display: flex; align-items: center; gap: 5px; color: var(--muted); font-size: 9px; padding: 4px 0; white-space: nowrap; }
  .section-heading > button:hover { color: var(--accent); }
  .recent-reading, .saved-reading { display: flex; align-items: center; gap: 12px; width: 100%; border-bottom: 1px solid var(--line); padding: 17px 0; text-align: left; }
  .recent-reading:hover .reading-details strong { color: var(--accent); }
  .recent-reading > :global(svg) { color: var(--muted); }
  .file-tile { display: grid; place-items: center; width: 37px; height: 45px; border: 1px solid var(--line); border-radius: 5px; color: var(--muted); background: var(--surface); flex-shrink: 0; }
  .reading-details { flex: 1; min-width: 0; }
  .reading-details strong { font-weight: 500; font-size: 12px; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .reading-details small { display: block; color: var(--muted); font-size: 9px; line-height: 1.5; margin-top: 5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .saved-play { display: grid; place-items: center; width: 37px; height: 37px; border-radius: 50%; background: var(--accent-soft); color: var(--accent); flex-shrink: 0; }
  .saved-play:hover { background: var(--accent); color: var(--accent-ink); }
  .saved-hint { margin: 13px 0 0; color: var(--muted); font-size: 9px; }
  .home-empty { display: flex; align-items: center; gap: 14px; padding: 29px 4px; color: var(--muted); }
  .home-empty p { font-size: 11px; line-height: 1.8; margin: 0; }
  .unfinished { margin-top: 24px; }
  .unfinished h3 { font-size: 10px; color: var(--muted); font-weight: 500; margin: 0 0 6px; }
  .reading-details small.resume-note { white-space: normal; }
  .unfinished-row { display: flex; align-items: center; gap: 10px; padding: 12px 0; border-bottom: 1px solid var(--line); }
  .finish-button { display: flex; align-items: center; gap: 5px; font-size: 10px; color: var(--accent); }
  @media (max-width: 1180px) { .listen-art { display: none; } .home-totals { gap: 17px; } .home-heading h1 { font-size: 40px; } .home-top-grid { gap: 16px; } .home-shelf-grid { gap: 24px; } }
  @media (max-width: 760px) { .home-heading { align-items: flex-start; } .home-totals { flex-direction: column; gap: 10px; } .home-totals strong { font-size: 20px; margin-bottom: 2px; } .home-top-grid, .home-shelf-grid { grid-template-columns: 1fr; } .home-heading h1 { font-size: 34px; } }
</style>

<script lang="ts">
  import { AudioLines, Check, Download, FolderOpen, LoaderCircle, RotateCcw } from '@lucide/svelte';
  import type { Model } from './api';
  let { model, pending = false, disabled = false, preview = false, error = '', setup }: {
    model: Model | undefined; pending?: boolean; disabled?: boolean; preview?: boolean; error?: string;
    setup: (method: 'download' | 'import') => Promise<void>;
  } = $props();
  const ready = $derived(model?.state === 'ready');
  const downloading = $derived(model?.state === 'downloading');
  const failed = $derived(model?.state === 'error');
  const size = $derived(model?.download_bytes ? `${Math.ceil(model.download_bytes / 1_000_000)} MB` : 'about 120 MB');
  const percent = $derived(Math.max(0, Math.min(100, model?.percent || 0)));
</script>

<section class="voice-setup" aria-label="Voice setup">
  <div class="setup-heading"><span class="setup-icon"><AudioLines size={22} strokeWidth={1.5} /></span><div><h3>{ready ? 'Your voices are ready.' : downloading ? 'Your voices are on their way.' : 'First, add your voices.'}</h3><p>{ready ? 'Choose a voice and make your first reading.' : 'One download. Violilt takes care of the setup.'}</p></div>{#if ready}<Check size={20} class="ready-check" />{/if}</div>
  {#if !ready}
    <p class="setup-explanation">The voice engine turns your text into speech on this PC. Download it here once ({size}) from the Kokoro-ONNX project on GitHub. No separate installer or account is needed.</p>
    {#if downloading}<div class="download-status" role="status">{model?.message || 'Downloading voices…'}</div><div class="download-progress" role="progressbar" aria-label="Voice download" aria-valuemin="0" aria-valuemax="100" aria-valuenow={percent}><span style:width={`${percent}%`}></span></div><p class="setup-note">{percent}% · You can explore Violilt while the download finishes.</p>
    {:else if failed}<p class="setup-error" role="alert">{model?.message}</p>{/if}
    <div class="setup-actions"><button class="primary-button" disabled={disabled || pending || downloading || preview} onclick={() => setup('download')}>{#if pending || downloading}<LoaderCircle size={16} class="spin" /> {downloading ? 'Downloading voices…' : 'Starting setup…'}{:else if failed}<RotateCcw size={16} /> Retry download{:else}<Download size={16} /> Download voices · {size}{/if}</button><button class="existing-files" disabled={disabled || pending || downloading || preview} onclick={() => setup('import')}><FolderOpen size={15} /> Use existing files</button></div>
    <p class="setup-note">After setup, narration works offline. You can also import documents and explore before downloading.</p>
  {:else}<p class="setup-explanation">The voice engine is already available. There is nothing else to download for CPU narration.</p><button class="existing-files" disabled={disabled || pending || preview} onclick={() => setup('import')}><FolderOpen size={15} /> Use existing files</button>{/if}
  {#if preview}<p class="setup-note">Downloads and file selection are available in the desktop app.</p>{/if}
  {#if error}<p class="setup-error" role="alert">{error}</p>{/if}
</section>

<style>
  .voice-setup { text-align: left; }
  .setup-heading { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
  .setup-icon { display: grid; place-items: center; width: 40px; height: 40px; flex-shrink: 0; border-radius: 12px; background: var(--accent-soft); color: var(--accent); }
  h3 { margin: 0 0 5px; font-size: 15px; font-weight: 600; }
  .setup-heading p { margin: 0; color: var(--muted); font-size: 11px; line-height: 1.5; }
  .setup-heading :global(.ready-check) { margin-left: auto; color: var(--accent); }
  .setup-explanation { margin: 0 0 15px; font-size: 12px; line-height: 1.75; color: var(--muted); }
  .setup-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 18px; }
  .setup-actions .primary-button { font-size: 12px; }
  .existing-files { display: inline-flex; align-items: center; gap: 6px; padding: 8px 0; color: var(--muted); font-size: 11px; text-decoration: underline; text-underline-offset: 3px; }
  .setup-note { margin: 12px 0 0; color: var(--muted); font-size: 11px; line-height: 1.65; }
  .download-status { font-size: 12px; line-height: 1.6; margin-bottom: 10px; }
  .download-progress { height: 5px; background: var(--line); border-radius: 6px; overflow: hidden; }
  .download-progress span { display: block; height: 100%; background: var(--accent); transition: width .2s; }
  .download-progress + .setup-note { margin-bottom: 15px; }
  .setup-error { margin: 12px 0; border-left: 3px solid var(--accent); padding-left: 12px; font-size: 12px; line-height: 1.6; }
</style>

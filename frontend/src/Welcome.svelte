<script lang="ts">
  import { ArrowRight, BookOpen, ChevronDown, Headphones, ShieldCheck } from '@lucide/svelte';
  import type { API, Model } from './api';
  import brandIcon from './assets/violilt.png';
  import MicrosoftPrivacy from './MicrosoftPrivacy.svelte';
  import VoiceSetup from './VoiceSetup.svelte';
  let { open = $bindable(false), api, model, preview, disabled = false, setupPending, setupError, saving, error, setup, finish }: {
    open: boolean; api: API | undefined; model: Model | undefined; preview: boolean; disabled?: boolean;
    setupPending: boolean; setupError: string; saving: boolean; error: string;
    setup: (method: 'download' | 'import') => Promise<void>;
    finish: (destination: 'home' | 'studio' | 'close', remember?: boolean) => Promise<void>;
  } = $props();
  let dialog: HTMLDialogElement;
  let title = $state<HTMLHeadingElement>();
  $effect(() => { if (open) { dialog?.showModal(); title?.focus(); } else dialog?.close(); });
</script>

<dialog bind:this={dialog} class="welcome-dialog" aria-labelledby="welcome-title" oncancel={event => { event.preventDefault(); void finish('close'); }}>
  {#if open}
    <header class="welcome-heading"><img src={brandIcon} alt="" /><span class="eyebrow">YOUR WORDS, OUT LOUD</span><h1 bind:this={title} tabindex="-1" id="welcome-title">Welcome to <em>Violilt.</em></h1><p>A page you saved. A chapter you love.<br />Give your words a voice, right here on your PC.</p></header>
    <div class="welcome-content">
      <div class="welcome-setup"><VoiceSetup {model} pending={setupPending} {disabled} {preview} error={setupError} {setup} /></div>
      <details class="welcome-guide"><summary><BookOpen size={17} /><span>A first listen in three small steps</span><ChevronDown size={16} /></summary><ol><li><strong>Bring your words.</strong><span>Import Markdown, TXT or PDF, or paste text into a new reading.</span></li><li><strong>Find your voice.</strong><span>Choose a voice and adjust the pace in the reading room.</span></li><li><strong>Make yourself comfortable.</strong><span>Press Create your audio. Listen as it arrives, then find the recording on your shelf.</span></li></ol></details>
      <section class="welcome-privacy" aria-labelledby="welcome-privacy-title"><h2 id="welcome-privacy-title"><ShieldCheck size={16} /> A little about privacy</h2><p class="local-note">Your documents are processed and narrated on this device.</p><MicrosoftPrivacy {api} compact /></section>
    </div>
    <footer class="welcome-footer">
      {#if error}<p class="welcome-error" role="alert">{error}</p>{/if}
      <div class="welcome-buttons">{#if model?.state === 'ready'}<button class="primary-button" disabled={saving} onclick={() => finish('studio')}><Headphones size={16} /> {saving ? 'Opening…' : 'Start reading'}<ArrowRight size={16} /></button>{/if}<button class:primary-button={model?.state !== 'ready'} class:secondary-button={model?.state === 'ready'} disabled={saving} onclick={() => finish('home')}>{saving ? 'Opening…' : model?.state === 'ready' ? 'Explore Violilt' : 'Explore for now'}{#if model?.state !== 'ready'}<ArrowRight size={16} />{/if}</button>{#if error}<button class="session-button" disabled={saving} onclick={() => finish('home', false)}>Continue for this session</button>{/if}</div>
      <p>You can reopen this guide and the privacy information from Settings or About. Continuing does not change privacy preferences or consent to optional collection.</p>
    </footer>
  {/if}
</dialog>

<style>
  .welcome-dialog { width: min(700px, calc(100vw - 32px)); max-height: calc(100dvh - 32px); padding: 0; border: 1px solid var(--line); border-radius: 18px; background: var(--paper); color: var(--ink); overflow-y: auto; box-shadow: 0 24px 100px #0003; }
  .welcome-dialog::backdrop { background: #10152066; backdrop-filter: blur(4px); }
  .welcome-heading { padding: 30px 36px 25px; text-align: center; background: linear-gradient(140deg, var(--surface-alt), var(--paper)); border-bottom: 1px solid var(--line); }
  .welcome-heading img { width: 48px; height: 48px; object-fit: contain; margin-bottom: 15px; }
  .welcome-heading .eyebrow { justify-content: center; font-size: 8px; }
  h1 { margin: 13px 0 12px; font: 37px/1.15 Georgia, serif; letter-spacing: -1px; outline: none; }
  h1 em { color: var(--accent); font-weight: normal; }
  .welcome-heading p { margin: 0; font-size: 13px; line-height: 1.7; color: var(--muted); }
  .welcome-content { padding: 24px 32px 0; }
  .welcome-setup { padding: 20px; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; }
  .welcome-guide { margin-top: 17px; }
  summary { display: flex; align-items: center; gap: 10px; padding: 12px 3px; cursor: pointer; font-size: 12px; list-style: none; }
  summary::-webkit-details-marker { display: none; }
  summary span { flex: 1; }
  summary :global(svg:last-child) { color: var(--muted); transition: transform .15s; }
  details[open] summary :global(svg:last-child) { transform: rotate(180deg); }
  summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
  ol { margin: 8px 0 0; padding: 0 0 0 28px; }
  li { padding: 0 0 14px 7px; font-size: 12px; line-height: 1.65; }
  li::marker { color: var(--accent); }
  li strong, li span { display: block; }
  li strong { font-weight: 600; margin-bottom: 3px; }
  li span { color: var(--muted); }
  .welcome-privacy { padding: 18px 3px 0; border-top: 1px solid var(--line); margin-top: 4px; }
  h2 { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 600; margin: 0 0 10px; }
  .local-note { font-size: 11px; line-height: 1.65; color: var(--muted); margin: 0 0 12px; }
  .welcome-footer { padding: 17px 32px 23px; }
  .welcome-buttons { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
  .welcome-footer > p { color: var(--muted); font-size: 10px; line-height: 1.65; margin: 14px 0 0; }
  .welcome-footer p.welcome-error { color: var(--ink); font-size: 12px; margin: 0 0 15px; }
  .session-button { padding: 9px 0; font-size: 11px; text-decoration: underline; text-underline-offset: 3px; }
  @media (max-width: 540px) { .welcome-heading { padding: 25px 20px 20px; } h1 { font-size: 31px; } .welcome-content { padding: 18px 18px 0; } .welcome-setup { padding: 16px; } .welcome-footer { padding: 16px 21px 21px; } }
</style>

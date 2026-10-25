<script lang="ts">
  import { withTimeout, type API } from './api';
  let { api, compact = false }: { api: API | undefined; compact?: boolean } = $props();
  let linkError = $state('');
  async function openReference(event: MouseEvent, reference: 'privacy-statement' | 'smartscreen') {
    event.preventDefault(); linkError = '';
    try {
      if (!api) throw new Error('The desktop service is not connected yet. Retry after connecting, or copy the address into your browser.');
      if (await withTimeout(api.open_microsoft_privacy(reference)) !== true) throw new Error('The browser could not be opened. Retry, or copy the address into your browser.');
    } catch (error) { linkError = error instanceof Error ? error.message : String(error); }
  }
</script>

<div class:compact class="microsoft-privacy">
  <p>{compact ? 'Violilt uses Microsoft Edge WebView2. Microsoft receives required diagnostic data from WebView2 and safety-check information from its Microsoft Defender SmartScreen feature.' : 'Violilt uses Microsoft WebView2, which includes Microsoft Defender SmartScreen. SmartScreen helps protect against unsafe websites and downloads, and collects and sends your information to Microsoft as described in the references below.'}</p>
  <div class="privacy-references"><a href="https://privacy.microsoft.com/privacystatement" onclick={event => openReference(event, 'privacy-statement')}>{compact ? 'Microsoft Privacy Statement' : 'Microsoft privacy statement'}</a><a href="https://learn.microsoft.com/en-us/legal/microsoft-edge/privacy#smartscreen" onclick={event => openReference(event, 'smartscreen')}>{compact ? 'WebView2 privacy information' : 'SmartScreen privacy information'}</a></div>
  <p>{compact ? 'Optional diagnostic data follows your Windows settings.' : 'WebView2 collects required diagnostic data for performance and reliability. Windows controls optional diagnostic data in Settings → Privacy & security → Diagnostics & feedback.'}</p>
  {#if !compact}<p>These references open in your default browser. Dismissing this notice does not change diagnostic settings or give consent to optional collection.</p>{/if}
  {#if !compact || linkError}<div class="reference-addresses"><span>https://privacy.microsoft.com/privacystatement</span><span>https://learn.microsoft.com/en-us/legal/microsoft-edge/privacy#smartscreen</span></div>{/if}
  {#if linkError}<p class="notice-error" role="alert">{linkError}</p>{/if}
</div>

<style>
  p { margin: 0 0 12px; font-size: 12px; line-height: 1.65; color: var(--muted); }
  .privacy-references { display: flex; gap: 8px 20px; flex-wrap: wrap; margin: 0 0 12px; }
  a { color: var(--ink); font-size: 12px; text-decoration: underline; text-underline-offset: 3px; }
  a:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }
  .reference-addresses { display: grid; gap: 5px; overflow-wrap: anywhere; color: var(--muted); font-size: 10px; user-select: text; }
  .notice-error { margin-top: 12px; color: var(--ink); border-left: 3px solid var(--accent); padding-left: 10px; }
  .compact p, .compact a { font-size: 11px; }
</style>

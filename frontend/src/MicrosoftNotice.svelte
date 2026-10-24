<script lang="ts">
  import { withTimeout, type API } from './api';

  let { open = $bindable(false), api }: { open: boolean; api: API | undefined } = $props();
  let dialog: HTMLDialogElement;
  let continueButton: HTMLButtonElement;
  let linkError = $state('');

  $effect(() => {
    if (open) {
      linkError = '';
      dialog?.showModal();
      continueButton?.focus();
    } else dialog?.close();
  });

  async function openReference(event: MouseEvent, reference: 'privacy-statement' | 'smartscreen') {
    event.preventDefault();
    linkError = '';
    try {
      if (!api) throw new Error('The desktop service is not connected yet. Retry after connecting, or copy the address below into your browser.');
      if (await withTimeout(api.open_microsoft_privacy(reference)) !== true) {
        throw new Error('The browser could not be opened. Retry, or copy the address below into your browser.');
      }
    } catch (error) {
      linkError = error instanceof Error ? error.message : String(error);
    }
  }
</script>

<dialog bind:this={dialog} class="about-modal microsoft-notice" aria-labelledby="microsoft-notice-title"
  onclose={() => open = false} oncancel={() => open = false}>
  <h2 id="microsoft-notice-title">Microsoft services &amp; privacy</h2>
  <p>Violilt includes Microsoft Defender SmartScreen, which collects and sends your information to Microsoft as described in the references below. SmartScreen helps protect you from unsafe sites and downloads.</p>
  <ul>
    <li><a href="https://privacy.microsoft.com/privacystatement" onclick={event => openReference(event, 'privacy-statement')}>Microsoft privacy statement</a><span class="reference-address">https://privacy.microsoft.com/privacystatement</span></li>
    <li><a href="https://learn.microsoft.com/en-us/legal/microsoft-edge/privacy#smartscreen" onclick={event => openReference(event, 'smartscreen')}>SmartScreen privacy information</a><span class="reference-address">https://learn.microsoft.com/en-us/legal/microsoft-edge/privacy#smartscreen</span></li>
  </ul>
  <p>Violilt's interface uses Microsoft WebView2. It collects required diagnostic data for performance and reliability. Optional diagnostic data is controlled by Windows Settings → Privacy &amp; security → Diagnostics &amp; feedback → Diagnostic data.</p>
  <p>This notice appears each time you open Violilt. You can return to it from About Violilt. Continuing dismisses this notice; it does not change diagnostic settings or give consent to optional collection. Links open in your default browser.</p>
  {#if linkError}<p class="notice-error" role="alert">{linkError}</p>{/if}
  <button bind:this={continueButton} class="primary-button" onclick={() => open = false}>Continue</button>
</dialog>

<style>
  .microsoft-notice { width: min(560px, calc(100vw - 40px)); max-height: calc(100dvh - 40px); overflow-y: auto; text-align: left; }
  ul { padding-left: 20px; font-size: 13px; line-height: 1.6; }
  li + li { margin-top: 14px; }
  a { color: var(--ink); text-decoration: underline; text-underline-offset: 3px; }
  a:focus-visible, button:focus-visible { outline: 2px solid var(--ink); outline-offset: 4px; }
  .reference-address { display: block; overflow-wrap: anywhere; color: var(--muted); font-size: 11px; user-select: text; }
  .notice-error { color: var(--ink); border-left: 3px solid var(--ink); padding-left: 10px; }
</style>

<script lang="ts">
  import type { API } from './api';
  import MicrosoftPrivacy from './MicrosoftPrivacy.svelte';

  let { open = $bindable(false), api }: { open: boolean; api: API | undefined } = $props();
  let dialog: HTMLDialogElement;
  let continueButton: HTMLButtonElement;

  $effect(() => {
    if (open) {
      dialog?.showModal();
      continueButton?.focus();
    } else dialog?.close();
  });

</script>

<dialog bind:this={dialog} class="about-modal microsoft-notice" aria-labelledby="microsoft-notice-title"
  onclose={() => open = false} oncancel={() => open = false}>
  <h2 id="microsoft-notice-title">Microsoft services &amp; privacy</h2>
  {#if open}<MicrosoftPrivacy {api} />{/if}
  <p class="notice-access">You can return to this information from Settings or About Violilt.</p>
  <button bind:this={continueButton} class="primary-button" onclick={() => open = false}>Continue</button>
</dialog>

<style>
  .microsoft-notice { width: min(560px, calc(100vw - 40px)); max-height: calc(100dvh - 40px); overflow-y: auto; text-align: left; }
  .notice-access { font-size: 12px; color: var(--muted); line-height: 1.6; }
</style>

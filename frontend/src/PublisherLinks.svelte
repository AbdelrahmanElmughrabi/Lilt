<script lang="ts">
  import { withTimeout, type API, type PublisherLinks, type PublisherReference } from './api';
  let { api, links }: { api: API | undefined; links: PublisherLinks | undefined } = $props();
  let linkError = $state('');
  let failedAddress = $state('');
  const references: { id: PublisherReference; label: string }[] = [
    { id: 'app', label: 'Violilt website' },
    { id: 'privacy', label: 'Privacy policy' },
    { id: 'support', label: 'Support' },
    { id: 'publisher', label: 'Publisher website' },
  ];
  async function openLink(event: MouseEvent, reference: PublisherReference) {
    event.preventDefault(); linkError = ''; failedAddress = '';
    try {
      if (!api || typeof api.open_publisher_link !== 'function') throw new Error('The desktop service is not connected yet. Retry after connecting, or copy the address into your browser.');
      if (await withTimeout(api.open_publisher_link(reference)) !== true) throw new Error('The browser could not be opened. Retry, or copy the address into your browser.');
    } catch (error) {
      linkError = error instanceof Error ? error.message : String(error);
      failedAddress = links?.[reference] || '';
    }
  }
</script>

{#if links}
  <nav class="publisher-links" aria-label="Violilt website and support">
    {#each references as reference}
      <a href={links[reference.id]} onclick={event => openLink(event, reference.id)}>{reference.label}</a>
    {/each}
    {#if linkError}
      <div class="publisher-link-error" role="alert"><span>{linkError}</span><span class="publisher-link-address">{failedAddress}</span></div>
    {/if}
  </nav>
{/if}

<style>
  .publisher-links { display: flex; flex-wrap: wrap; gap: 10px 20px; margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--line); }
  a { color: var(--ink); font-size: 12px; line-height: 1.6; text-decoration: underline; text-underline-offset: 3px; }
  a:hover { color: var(--accent); }
  a:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }
  .publisher-link-error { flex-basis: 100%; display: grid; gap: 5px; color: var(--ink); font-size: 12px; line-height: 1.6; border-left: 3px solid var(--accent); padding-left: 10px; }
  .publisher-link-address { overflow-wrap: anywhere; user-select: text; color: var(--muted); }
</style>

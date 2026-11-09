<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { FolderOpen, Trash2 } from '@lucide/svelte';
  import type { FileMenu, FileItem } from './context-menu';
  let { menu, canDelete, close, remove, reveal }: {
    menu: FileMenu; canDelete: boolean; close: () => void;
    remove: (item: FileItem) => void; reveal: (item: FileItem) => void;
  } = $props();
  let element: HTMLDivElement;
  let x = $state(0), y = $state(0);
  const canReveal = $derived(menu.item.kind === 'recording' || !!menu.item.source);
  function dismiss(restore = true) { const anchor = menu.anchor; close(); if (restore && anchor.isConnected) anchor.focus({ preventScroll: true }); }
  function choose(action: (item: FileItem) => void) { const item = menu.item; dismiss(); action(item); }
  function outside(event: PointerEvent) { if (!element?.contains(event.target as Node)) dismiss(false); }
  function keyboard(event: KeyboardEvent) {
    event.stopPropagation();
    const buttons = [...element.querySelectorAll<HTMLButtonElement>('button:not(:disabled)')];
    const index = buttons.indexOf(window.document.activeElement as HTMLButtonElement);
    if (event.key === 'Escape') { event.preventDefault(); dismiss(); }
    else if (event.key === 'Tab') dismiss(false);
    else if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
      event.preventDefault();
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? buttons.length - 1 : (index + (event.key === 'ArrowDown' ? 1 : -1) + buttons.length) % buttons.length;
      buttons[next]?.focus({ preventScroll: true });
    }
  }
  onMount(() => {
    void tick().then(() => {
      const rect = element.getBoundingClientRect();
      x = Math.max(8, Math.min(menu.x, window.innerWidth - rect.width - 8));
      y = Math.max(8, Math.min(menu.y, window.innerHeight - rect.height - 8));
      (element.querySelector<HTMLButtonElement>('button:not(:disabled)') || element).focus({ preventScroll: true });
    });
    const scroll = () => dismiss(false);
    window.addEventListener('scroll', scroll, true);
    return () => window.removeEventListener('scroll', scroll, true);
  });
</script>

<svelte:window onpointerdown={outside} onresize={() => dismiss(false)} onblur={() => dismiss(false)} />
<div bind:this={element} class="file-context-menu" role="menu" tabindex="-1" aria-label={`Actions for ${menu.item.title}`} style:left={`${x}px`} style:top={`${y}px`} onkeydown={keyboard}>
  <button role="menuitem" tabindex="-1" disabled={!canDelete} onclick={() => choose(remove)}><Trash2 size={15} /> Delete…</button>
  <button role="menuitem" tabindex="-1" disabled={!canReveal} title={canReveal ? 'Reveal the associated file or output folder' : 'This reading has no original file'} onclick={() => choose(reveal)}><FolderOpen size={15} /> Show in File Explorer</button>
</div>

<style>
  .file-context-menu { position: fixed; z-index: 50; min-width: 215px; padding: 5px; border: 1px solid var(--line-strong); border-radius: 8px; background: var(--surface); color: var(--ink); box-shadow: 0 8px 30px #0003; }
  button { display: flex; align-items: center; gap: 10px; width: 100%; padding: 10px; text-align: left; border-radius: 4px; font-size: 12px; }
  button:not(:disabled):hover, button:focus-visible { background: var(--surface-alt); }
</style>

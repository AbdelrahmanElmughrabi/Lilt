<script lang="ts">
  import { tick, untrack } from 'svelte';
  import { Search, ChevronUp, ChevronDown, X } from '@lucide/svelte';

  let { content, revision, enabled }: { content: HTMLElement | undefined; revision: string; enabled: boolean } = $props();
  let open = $state(false);
  let query = $state('');
  let current = $state(0);
  let matches = $state<{ start: number; end: number; range?: Range }[]>([]);
  let input = $state<HTMLInputElement>();
  let trigger: HTMLButtonElement;
  const highlights = (CSS as unknown as { highlights?: Map<string, unknown> }).highlights;
  const HighlightClass = (window as unknown as { Highlight?: new (...ranges: Range[]) => unknown }).Highlight;

  function clearHighlights() {
    highlights?.delete('document-find');
    highlights?.delete('document-find-current');
  }

  async function show() {
    if (!enabled) return;
    open = true;
    await tick();
    input?.focus();
    input?.select();
  }

  function close() {
    open = false;
    clearHighlights();
    trigger?.focus();
  }

  function keyboard(event: KeyboardEvent) {
    if (!enabled || window.document.querySelector('dialog[open]')) return;
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'f') {
      event.preventDefault();
      void show();
    } else if (open && event.key === 'Escape') {
      event.preventDefault();
      close();
    } else if (open && (event.key === 'F3' || (event.key === 'Enter' && event.target === input))) {
      event.preventDefault();
      move(event.shiftKey ? -1 : 1);
    }
  }

  function move(direction: number) {
    if (matches.length) current = (current + direction + matches.length) % matches.length;
  }

  // Rebuild ranges after Svelte has rendered the selected view or edited text.
  $effect(() => {
    const root = content;
    const needle = query;
    const active = open && enabled;
    revision;
    let cancelled = false;
    void tick().then(() => {
      if (cancelled) return;
      clearHighlights();
      const found: typeof matches = [];
      if (active && root && needle) {
        const nodes: { node: Text; start: number; end: number }[] = [];
        let text = '';
        if (root instanceof HTMLTextAreaElement) text = root.value;
        else {
          const walker = window.document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
          let node: Node | null;
          let previousBlock: Element | null = null;
          while ((node = walker.nextNode())) {
            const block = node.parentElement?.closest('p, h1, h2, h3, h4, li, pre, td, th, blockquote') || null;
            if (text && block !== previousBlock) text += '\n';
            previousBlock = block;
            const start = text.length;
            text += node.textContent || '';
            nodes.push({ node: node as Text, start, end: text.length });
          }
        }
        // Escaped literal regex preserves source offsets even for Unicode case folding.
        const pattern = new RegExp(needle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
        for (const match of text.matchAll(pattern)) {
          const start = match.index!;
          const end = start + match[0].length;
          let range: Range | undefined;
          if (nodes.length) {
            const first = nodes.find(n => n.end > start)!;
            const last = nodes.find(n => n.end >= end)!;
            range = window.document.createRange();
            range.setStart(first.node, start - first.start);
            range.setEnd(last.node, end - last.start);
          }
          found.push({ start, end, range });
        }
      }
      matches = found;
      current = 0;
      if (HighlightClass && highlights) highlights.set('document-find', new HighlightClass(...found.flatMap(m => m.range ? [m.range] : [])));
    });
    return () => { cancelled = true; clearHighlights(); };
  });

  $effect(() => {
    const match = matches[current];
    const root = content;
    if (!open || !match || !root) return;
    if (match.range) {
      if (HighlightClass && highlights) highlights.set('document-find-current', new HighlightClass(match.range));
      const scroller = root.closest('.document-scroll');
      if (scroller) {
        const bounds = match.range.getBoundingClientRect();
        const viewport = scroller.getBoundingClientRect();
        scroller.scrollTop += bounds.top - viewport.top - viewport.height / 2;
      }
    } else if (root instanceof HTMLTextAreaElement) {
      root.setSelectionRange(match.start, match.end);
      // Measure wrapped lines with the editor's actual font and width.
      const mirror = window.document.createElement('div');
      const style = getComputedStyle(root);
      for (const property of ['font', 'line-height', 'letter-spacing', 'padding', 'border', 'box-sizing', 'tab-size']) {
        mirror.style.setProperty(property, style.getPropertyValue(property));
      }
      Object.assign(mirror.style, { position: 'fixed', visibility: 'hidden', width: `${root.offsetWidth}px`, whiteSpace: 'pre-wrap', overflowWrap: 'break-word' });
      mirror.textContent = root.value.slice(0, match.start);
      const marker = window.document.createElement('span');
      marker.textContent = root.value.slice(match.start, match.end) || ' ';
      mirror.append(marker);
      window.document.body.append(mirror);
      root.scrollTop = marker.offsetTop - root.clientHeight / 2;
      mirror.remove();
      untrack(() => root.scrollIntoView({ block: 'nearest' }));
    }
  });
</script>

<svelte:window onkeydown={keyboard} />

<div class="document-find">
  <button bind:this={trigger} class="find-trigger" disabled={!enabled} onclick={show} title="Find in document (Ctrl+F)" aria-expanded={open}><Search size={15} /> Find <kbd>Ctrl F</kbd></button>
  {#if open}
    <div class="find-bar" role="search" aria-label="Find in document">
      <Search size={15} />
      <input bind:this={input} bind:value={query} aria-label="Find in document" placeholder="Find in this view…" spellcheck="false" />
      <span class="find-count" role="status">{query ? (matches.length ? `${current + 1} of ${matches.length}` : 'No matches') : 'Type to find'}</span>
      <button class="icon-button" disabled={!matches.length} onclick={() => move(-1)} title="Previous match (Shift+Enter)" aria-label="Previous match"><ChevronUp size={16} /></button>
      <button class="icon-button" disabled={!matches.length} onclick={() => move(1)} title="Next match (Enter)" aria-label="Next match"><ChevronDown size={16} /></button>
      <button class="icon-button" onclick={close} title="Close find (Escape)" aria-label="Close find"><X size={16} /></button>
    </div>
  {/if}
</div>

<style>
  .document-find { padding: 0 42px 12px; }
  .find-trigger { display: flex; align-items: center; gap: 7px; color: var(--muted); font-size: 12px; }
  kbd { font: inherit; font-size: 10px; opacity: .7; }
  .find-bar { display: flex; align-items: center; gap: 7px; margin-top: 10px; padding: 7px 10px; border: 1px solid var(--line-strong); border-radius: 6px; background: var(--surface); color: var(--muted); }
  input { flex: 1; width: 0; min-width: 50px; border: 0; background: transparent; color: var(--ink); font: inherit; font-size: 12px; padding: 5px; }
  .find-count { font-size: 11px; white-space: nowrap; }
  :global(::highlight(document-find)) { background: #f5df8a; color: #252218; }
  :global(::highlight(document-find-current)) { background: #b8bdf1; color: #161c29; text-decoration: underline; }
  @media (max-width: 900px) { .document-find { padding-left: 25px; padding-right: 25px; } }
</style>

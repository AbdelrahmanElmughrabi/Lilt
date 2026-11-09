<script lang="ts">
  import { onMount } from 'svelte';
  import { ArrowDown, FileText, LoaderCircle, AudioLines } from '@lucide/svelte';

  let { enabled, importFiles }: { enabled: boolean; importFiles: (files: File[]) => Promise<void> } = $props();
  let hovering = $state(false);
  let importing = $state(false);
  let count = $state(1);
  let overlay: HTMLDivElement;
  let depth = 0;
  let expiry: ReturnType<typeof setTimeout>;
  const visible = $derived(enabled && (hovering || importing));

  $effect(() => {
    if (!overlay) return;
    if (visible) {
      if (overlay.showPopover) overlay.showPopover();
      else overlay.removeAttribute('popover');
    } else if (overlay.hidePopover) overlay.hidePopover();
  });

  function isFiles(event: DragEvent) {
    return Array.from(event.dataTransfer?.types || []).includes('Files') || !!event.dataTransfer?.files.length;
  }
  function reset() { depth = 0; hovering = false; clearTimeout(expiry); }
  function keepVisible() {
    hovering = true;
    clearTimeout(expiry);
    // A canceled native drag does not always deliver dragleave to WebView2.
    expiry = setTimeout(reset, 1800);
  }
  function enter(event: DragEvent) {
    if (!isFiles(event)) return;
    event.preventDefault();
    if (!enabled || importing) return;
    depth++;
    count = Array.from(event.dataTransfer?.items || []).filter(item => item.kind === 'file').length || 1;
    keepVisible();
  }
  function over(event: DragEvent) {
    if (!isFiles(event)) return;
    event.preventDefault();
    if (event.dataTransfer) event.dataTransfer.dropEffect = enabled && !importing ? 'copy' : 'none';
    if (enabled && !importing) keepVisible();
  }
  function leave(event: DragEvent) {
    if (!isFiles(event) && !hovering) return;
    depth = Math.max(0, depth - 1);
    if (!depth || event.clientX <= 0 || event.clientY <= 0 || event.clientX >= window.innerWidth || event.clientY >= window.innerHeight) reset();
  }
  async function drop(event: DragEvent) {
    if (!isFiles(event)) return;
    event.preventDefault();
    event.stopPropagation();
    const files = Array.from(event.dataTransfer?.files || []);
    reset();
    if (!enabled || importing || !files.length) return;
    count = files.length;
    importing = true;
    try { await importFiles(files); } finally { importing = false; }
  }

  onMount(() => {
    window.addEventListener('dragenter', enter, true);
    window.addEventListener('dragover', over, true);
    window.addEventListener('dragleave', leave, true);
    window.addEventListener('drop', drop, true);
    window.addEventListener('dragend', reset);
    window.addEventListener('blur', reset);
    return () => {
      clearTimeout(expiry);
      window.removeEventListener('dragenter', enter, true);
      window.removeEventListener('dragover', over, true);
      window.removeEventListener('dragleave', leave, true);
      window.removeEventListener('drop', drop, true);
      window.removeEventListener('dragend', reset);
      window.removeEventListener('blur', reset);
    };
  });
</script>

<div bind:this={overlay} popover="manual" class="file-drop-overlay" class:visible class:importing role="status" aria-live="polite" aria-atomic="true">
  {#if visible}
    <div class="drop-frame">
      <div class="drop-art" aria-hidden="true">
        <div class="paper paper-back"></div>
        <div class="paper paper-middle"></div>
        <div class="paper paper-front"><FileText size={34} strokeWidth={1.2} /><span></span><span></span><span></span></div>
        <div class="drop-tray"><AudioLines size={28} strokeWidth={1.2} /></div>
        <span class="drop-arrow">{#if importing}<LoaderCircle size={18} class="spin" />{:else}<ArrowDown size={18} />{/if}</span>
      </div>
      <span class="drop-eyebrow">A LITTLE SPACE FOR YOUR WORDS</span>
      <h2>{#if importing}Making room<br />on your shelf.{:else}Drop your<br /><em>words here.</em>{/if}</h2>
      <p>{importing ? 'Adding your readings. Keep a little room for listening.' : count > 1 ? `${count} files. A few more things worth listening to.` : 'A note, an article, a whole chapter. Let it land.'}</p>
      <div class="drop-filetypes"><span>.md</span><span>.markdown</span><span>.txt</span><span>.pdf</span><span class="drop-divider"></span><small>Your originals stay untouched</small></div>
    </div>
  {/if}
</div>

<style>
  .file-drop-overlay { display: none; position: fixed; inset: 14px; margin: 0; width: auto; height: auto; max-width: none; max-height: none; padding: 13px; border: 1px solid var(--line-strong); border-radius: 16px; color: var(--ink); background: color-mix(in srgb, var(--paper) 93%, transparent); backdrop-filter: blur(9px); pointer-events: none; z-index: 80; }
  .file-drop-overlay.visible { display: grid; animation: drop-arrive .2s ease-out both; }
  .drop-frame { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 28px; border: 1px dashed var(--accent); border-radius: 10px; text-align: center; background: radial-gradient(ellipse at 50% 40%, color-mix(in srgb, var(--accent) 10%, transparent), transparent 60%); }
  .drop-art { position: relative; width: 180px; height: 158px; margin-bottom: 25px; }
  .paper { position: absolute; top: 4px; left: 53px; width: 76px; height: 99px; border: 1px solid var(--line-strong); border-radius: 5px; transform-origin: 50% 100%; }
  .paper-back { background: var(--art); transform: rotate(-17deg) translate(-13px, 5px); animation: paper-back 2.8s ease-in-out infinite; }
  .paper-middle { background: var(--surface-alt); transform: rotate(13deg) translate(13px, 3px); animation: paper-middle 2.8s ease-in-out infinite; }
  .paper-front { display: flex; flex-direction: column; align-items: center; gap: 5px; padding-top: 13px; background: var(--surface); color: var(--accent); box-shadow: 0 8px 20px color-mix(in srgb, var(--accent) 20%, transparent); animation: paper-float 2.8s ease-in-out infinite; }
  .paper-front span { width: 37px; height: 2px; background: var(--line-strong); }
  .paper-front span:last-child { width: 23px; margin-right: 14px; }
  .drop-tray { position: absolute; bottom: 0; left: 22px; right: 22px; height: 34px; border: 1px solid var(--art); border-top: 0; border-radius: 0 0 12px 12px; color: var(--status-ready); background: color-mix(in srgb, var(--art) 12%, transparent); }
  .drop-arrow { position: absolute; right: 10px; top: 65px; display: grid; place-items: center; width: 30px; height: 30px; border-radius: 50%; background: var(--surface-alt); color: var(--accent); animation: arrow-float 1.4s ease-in-out infinite; }
  .drop-eyebrow { color: var(--muted); font-size: 9px; letter-spacing: 2px; }
  h2 { font: 50px/1.08 Georgia, serif; letter-spacing: -1.4px; margin: 16px 0 15px; }
  h2 em { color: var(--accent); font-weight: normal; }
  p { color: var(--muted); font-size: 12px; line-height: 1.7; margin: 0 0 23px; }
  .drop-filetypes { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 8px; color: var(--muted); }
  .drop-filetypes > span:not(.drop-divider) { font-size: 10px; padding: 5px 8px; background: var(--surface); border: 1px solid var(--line); border-radius: 4px; }
  .drop-divider { width: 1px; height: 13px; background: var(--line-strong); margin: 0 5px; }
  small { font-size: 10px; }
  .importing .paper, .importing .drop-arrow { animation: none; }
  @keyframes drop-arrive { from { opacity: 0; transform: scale(.99); } to { opacity: 1; transform: scale(1); } }
  @keyframes paper-float { 0%, 100% { transform: translateY(0) rotate(-2deg); } 50% { transform: translateY(-8px) rotate(2deg); } }
  @keyframes paper-back { 0%, 100% { transform: rotate(-17deg) translate(-13px, 5px); } 50% { transform: rotate(-22deg) translate(-16px, 0); } }
  @keyframes paper-middle { 0%, 100% { transform: rotate(13deg) translate(13px, 3px); } 50% { transform: rotate(18deg) translate(16px, -2px); } }
  @keyframes arrow-float { 0%, 100% { transform: translateY(-3px); } 50% { transform: translateY(3px); } }
  @media (max-height: 650px) { .drop-art { transform: scale(.75); margin: -20px 0 0; } h2 { font-size: 38px; } }
  @media (prefers-reduced-motion: reduce) { .file-drop-overlay, .paper, .drop-arrow, .drop-arrow :global(.spin) { animation: none !important; } }
</style>

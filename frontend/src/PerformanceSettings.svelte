<script lang="ts">
  import { Archive, AudioLines, Gauge, Headphones, Play, Square, Trash2, Zap } from '@lucide/svelte';
  import type { Settings, Performance, Cache } from './api';
  let { settings = $bindable(), performance, cache, busy, ready, onchange, action }: {
    settings: Settings; performance: Performance | null; cache: Cache; busy: boolean; ready: boolean;
    onchange: () => Promise<void>; action: (name: 'test' | 'stop' | 'warm' | 'release' | 'clear') => Promise<void>;
  } = $props();
  let releasing = $state(false);
  const memoryBusy = $derived(performance?.memory?.state === 'busy' || performance?.memory?.state === 'releasing');
  const testing = $derived(['running', 'cancelling'].includes(performance?.benchmark.state || ''));
  const results = $derived(performance?.benchmark.results.length ? performance.benchmark.results : performance?.recommendation?.results || []);
  // Warmup's last success can outlive the loaded process. Prefer its current
  // memory state, retaining preparation failures and in-flight preparation.
  const memoryStatus = $derived(performance?.warmup.state === 'loading' ? performance.warmup.message
    : performance?.memory?.message || (performance?.warmup.state === 'failed' ? performance.warmup.message
    : performance?.memory?.state === 'releasing' ? 'Releasing voice memory…'
    : performance?.memory?.state === 'unloaded' ? 'Voice memory released · loads when needed'
    : performance?.memory?.state === 'busy' ? 'Voice process in use'
    : performance?.memory?.state === 'idle' ? 'Voice process idle' : ''));
  async function release() {
    releasing = true;
    try { await action('release'); } finally { releasing = false; }
  }
  const presets = [{id:'quiet',name:'Quiet',detail:'Lower priority'}, {id:'balanced',name:'Balanced',detail:'Moderate thread use'}, {id:'fast',name:'Fast',detail:'Measured best pace'}, {id:'custom',name:'Custom',detail:'Choose CPU threads'}] as const;
</script>

<section class="settings-card performance-card">
  <div class="settings-title"><Gauge size={23} strokeWidth={1.4} /><h2>Processing</h2></div>
  <div class="performance-presets">{#each presets as preset}<button class:selected={settings.performance_mode === preset.id} aria-pressed={settings.performance_mode === preset.id} onclick={() => { settings.performance_mode = preset.id; void onchange(); }}><strong>{preset.name}</strong><span>{preset.detail}</span></button>{/each}</div>
  <div class="performance-fields">
    <label><span>Processing device</span><select aria-label="Processing device" bind:value={settings.processing_device} onchange={onchange}><option value="auto">Auto · use speed test</option><option value="cpu">CPU</option><option value="gpu" disabled={!performance?.gpu_ready}>NVIDIA GPU {performance?.gpu_ready ? '' : '· runtime needed'}</option></select></label>
    <label><span>CPU threads</span><select aria-label="CPU threads" bind:value={settings.cpu_threads} disabled={settings.performance_mode !== 'custom'} onchange={onchange}><option value={0}>Auto · measured recommendation</option>{#each Array.from({length: performance?.logical_processors || 1}, (_,i) => i+1) as count}<option value={count}>{count} {count === 1 ? 'thread' : 'threads'}</option>{/each}</select></label>
    {#if settings.processing_device === 'gpu'}<label class="full-field"><span>Graphics card</span><select aria-label="Graphics card" bind:value={settings.gpu_device} onchange={onchange}><option value={-1}>Auto</option>{#each performance?.adapters || [] as adapter}<option value={adapter.id}>{adapter.name}</option>{/each}</select></label>{/if}
  </div>
  <p class="settings-hint">Next reading: <strong>{performance?.configuration.label || 'CPU'} · {performance?.configuration.threads || 4} CPU threads</strong>. More threads can be slower; usage is measured while generating.</p>
  {#if busy}<p class="settings-hint pending-hint">Changes apply to your next reading or continuation.</p>{/if}
  <div class="speed-test"><div><strong>Speed test</strong><p role="status">{testing ? performance?.benchmark.message : performance?.recommendation ? `Recommended: ${performance.recommendation.best.label} · ${performance.recommendation.best.throughput?.toFixed(1)}× real time` : 'Compare CPU settings and the available GPU with a short local reading.'}</p></div><button class="secondary-button" disabled={!ready || (busy && !testing) || performance?.benchmark.state === 'cancelling'} onclick={() => action(testing ? 'stop' : 'test')}>{#if testing}<Square size={14} /> Stop test{:else}<Zap size={15} /> Run speed test{/if}</button></div>
  {#if testing}<div class="progress-track"><span style:width={`${(performance?.benchmark.completed || 0) / Math.max(1,performance?.benchmark.total || 1)*100}%`}></span></div>{/if}
  {#if results.length}<div class="speed-results">{#each results as result}<div><span>{result.label}</span><strong>{result.error ? 'Unavailable' : `${result.throughput?.toFixed(1)}×`}</strong></div>{/each}<p>Audio seconds produced per processing second. Loading and cache reuse are excluded.</p></div>{/if}
  {#if performance?.benchmark.state === 'cancelled' || performance?.benchmark.state === 'failed'}<p class="settings-hint" class:settings-error={performance.benchmark.state === 'failed'} role="status">{performance.benchmark.message}</p>{/if}
</section>

<section class="settings-card listening-card">
  <div class="settings-title"><Headphones size={23} strokeWidth={1.4} /><h2>Listening</h2></div>
  <div class="performance-fields"><label class="full-field"><span>When listening catches up</span><select aria-label="Listening buffer" bind:value={settings.buffer_mode} onchange={onchange}><option value="sooner">Start sooner · smaller buffer</option><option value="balanced">Balanced · adapt to generation speed</option><option value="smooth">Fewer interruptions · more audio ahead</option></select></label></div>
  <label class="toggle-row"><span>Listen as audio arrives<small>Start playback automatically once enough audio is ready.</small></span><input type="checkbox" bind:checked={settings.auto_listen} onchange={onchange} /><span class="toggle-track"></span></label>
</section>

<section class="settings-card memory-card">
  <div class="settings-title"><AudioLines size={23} strokeWidth={1.4} /><h2>Voice memory</h2></div>
  <label class="toggle-row"><span>Prepare voices when Violilt opens<small>Less initial setup time; uses model memory sooner</small></span><input type="checkbox" bind:checked={settings.warm_start} onchange={onchange} /><span class="toggle-track"></span></label>
  <div class="performance-fields"><label class="full-field"><span>Release voice model</span><select aria-label="Release voice model" bind:value={settings.model_release} onchange={onchange}><option value="idle">After 2 minutes idle</option><option value="immediate">After each operation</option><option value="keep">Keep loaded</option></select></label></div>
  <p class="settings-hint">Releasing memory keeps playback available; the next reading reloads the model. Idle time starts when generation, preparation or a speed test finishes or stops.</p>
  <div class="settings-actions memory-actions"><button class="secondary-button" disabled={busy || !ready || memoryBusy || releasing || performance?.warmup.state === 'loading'} onclick={() => action('warm')}><Play size={14} /> {performance?.warmup.state === 'loading' ? 'Preparing…' : 'Prepare voice now'}</button><button class="secondary-button" disabled={busy || !ready || memoryBusy || releasing || performance?.memory?.state !== 'idle'} onclick={release}><Trash2 size={14} /> {releasing || performance?.memory?.state === 'releasing' ? 'Releasing…' : 'Release memory now'}</button></div>
  <p class="settings-hint memory-status" class:settings-error={performance?.warmup.state === 'failed' || !!performance?.memory?.message && performance?.memory?.state === 'releasing'} role="status">{memoryStatus}</p>
</section>

<section class="settings-card reusable-card">
  <div class="settings-title"><Archive size={23} strokeWidth={1.4} /><h2>Reusable audio</h2></div>
  <label class="toggle-row"><span>Reuse unchanged passages<small>Save audio locally for quicker repeats and small edits.</small></span><input type="checkbox" bind:checked={settings.cache_enabled} onchange={onchange} /><span class="toggle-track"></span></label>
  <div class="cache-controls"><label><span>Reusable audio limit</span><select aria-label="Cache limit" bind:value={settings.cache_limit_mb} onchange={onchange}>{#each [128,256,512] as limit}<option value={limit}>{limit} MB</option>{/each}</select></label><button class="secondary-button" disabled={busy || !cache.count} onclick={() => action('clear')}><Trash2 size={14} /> Clear reusable audio</button>
    <p class="settings-hint cache-usage" role="status">{#if cache.available === false}{cache.message}{:else}{cache.count || 0} passages · {((cache.bytes || 0)/1048576).toFixed(1)} MB. Clearing reusable audio keeps your recordings.{/if}</p>
  </div>
</section>

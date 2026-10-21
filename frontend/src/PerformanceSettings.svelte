<script lang="ts">
  import { Gauge, Play, Square, Trash2, Zap } from '@lucide/svelte';
  import type { Settings, Performance, Cache } from './api';
  let { settings = $bindable(), performance, cache, busy, ready, onchange, action }: {
    settings: Settings; performance: Performance | null; cache: Cache; busy: boolean; ready: boolean;
    onchange: () => Promise<void>; action: (name: 'test' | 'stop' | 'warm' | 'release' | 'clear') => Promise<void>;
  } = $props();
  let releasing = $state(false);
  const memoryBusy = $derived(performance?.memory?.state === 'busy' || performance?.memory?.state === 'releasing');
  const testing = $derived(['running', 'cancelling'].includes(performance?.benchmark.state || ''));
  const results = $derived(performance?.benchmark.results.length ? performance.benchmark.results : performance?.recommendation?.results || []);
  async function release() {
    releasing = true;
    try { await action('release'); } finally { releasing = false; }
  }
  const presets = [{id:'quiet',name:'Quiet',detail:'A lighter touch'}, {id:'balanced',name:'Balanced',detail:'Everyday reading'}, {id:'fast',name:'Fast',detail:'Measured best pace'}, {id:'custom',name:'Custom',detail:'Choose CPU threads'}] as const;
</script>

<section class="settings-card performance-card">
  <div class="settings-title"><Gauge size={23} strokeWidth={1.4} /><div><h2>Less waiting. More listening.</h2><p>Give your PC a pace that feels comfortable.</p></div><span class="performance-badge">LOCAL</span></div>
  <div class="performance-presets">{#each presets as preset}<button class:selected={settings.performance_mode === preset.id} onclick={() => { settings.performance_mode = preset.id; void onchange(); }}><strong>{preset.name}</strong><span>{preset.detail}</span></button>{/each}</div>
  <div class="performance-fields">
    <label><span>Processing device</span><select aria-label="Processing device" bind:value={settings.processing_device} onchange={onchange}><option value="auto">Auto · use speed test</option><option value="cpu">CPU</option><option value="gpu" disabled={!performance?.gpu_ready}>NVIDIA GPU {performance?.gpu_ready ? '' : '· runtime needed'}</option></select></label>
    <label><span>CPU threads</span><select aria-label="CPU threads" bind:value={settings.cpu_threads} disabled={settings.performance_mode !== 'custom'} onchange={onchange}><option value={0}>Auto · measured recommendation</option>{#each Array.from({length: performance?.logical_processors || 1}, (_,i) => i+1) as count}<option value={count}>{count} {count === 1 ? 'thread' : 'threads'}</option>{/each}</select></label>
    {#if settings.processing_device === 'gpu'}<label class="full-field"><span>Graphics card</span><select aria-label="Graphics card" bind:value={settings.gpu_device} onchange={onchange}><option value={-1}>Auto</option>{#each performance?.adapters || [] as adapter}<option value={adapter.id}>{adapter.name}</option>{/each}</select></label>{/if}
  </div>
  <p class="settings-hint">Next reading: <strong>{performance?.configuration.label || 'CPU'} · {performance?.configuration.threads || 4} CPU threads</strong>. Quiet lowers process priority. More threads can be slower; usage is measured while generating.</p>
  {#if busy}<p class="settings-hint pending-hint">Changes apply to your next reading or continuation.</p>{/if}
  <div class="speed-test"><div><strong>Find your PC’s sweet spot</strong><p>{testing ? performance?.benchmark.message : performance?.recommendation ? `Recommended: ${performance.recommendation.best.label} · ${performance.recommendation.best.throughput?.toFixed(1)}× real time` : 'Compare CPU settings and the available GPU with a short local reading.'}</p></div><button class="secondary-button" disabled={!ready || (busy && !testing) || performance?.benchmark.state === 'cancelling'} onclick={() => action(testing ? 'stop' : 'test')}>{#if testing}<Square size={14} /> Stop test{:else}<Zap size={15} /> Run speed test{/if}</button></div>
  {#if testing}<div class="progress-track"><span style:width={`${(performance?.benchmark.completed || 0) / Math.max(1,performance?.benchmark.total || 1)*100}%`}></span></div>{/if}
  {#if results.length}<div class="speed-results">{#each results as result}<div><span>{result.label}</span><strong>{result.error ? 'Unavailable' : `${result.throughput?.toFixed(1)}×`}</strong></div>{/each}<p>Audio seconds produced per processing second. Loading and cache reuse are excluded.</p></div>{/if}
  {#if performance?.benchmark.state === 'cancelled' || performance?.benchmark.state === 'failed'}<p class="settings-hint">{performance.benchmark.message}</p>{/if}
  <div class="performance-divider"></div>
  <div class="performance-fields"><label class="full-field"><span>When listening catches up</span><select aria-label="Listening buffer" bind:value={settings.buffer_mode} onchange={onchange}><option value="sooner">Start sooner · smaller buffer</option><option value="balanced">Balanced · adapt to generation speed</option><option value="smooth">Fewer interruptions · more audio ahead</option></select></label></div>
  <label class="toggle-row"><span>Listen as audio arrives<small>Start automatically once enough is ready</small></span><input type="checkbox" bind:checked={settings.auto_listen} onchange={onchange} /><span class="toggle-track"></span></label>
  <label class="toggle-row"><span>Prepare voices when Violilt opens<small>Less initial setup time; uses model memory sooner</small></span><input type="checkbox" bind:checked={settings.warm_start} onchange={onchange} /><span class="toggle-track"></span></label>
  <div class="settings-actions warm-actions"><button class="secondary-button" disabled={busy || !ready || memoryBusy || releasing || performance?.warmup.state === 'loading'} onclick={() => action('warm')}><Play size={14} /> {performance?.warmup.state === 'loading' ? 'Preparing…' : 'Prepare voice now'}</button><span>{performance?.warmup.message}</span></div>
  <div class="performance-fields"><label class="full-field"><span>Release voice model</span><select aria-label="Release voice model" bind:value={settings.model_release} onchange={onchange}><option value="idle">After 2 minutes idle</option><option value="immediate">After each operation</option><option value="keep">Keep loaded</option></select></label></div>
  <p class="settings-hint">Idle starts after generation, voice preparation, or a speed test finishes or stops. Listening can continue. The next reading reloads the model when needed.</p>
  <div class="settings-actions warm-actions"><button class="secondary-button" disabled={busy || !ready || memoryBusy || releasing || performance?.memory?.state !== 'idle'} onclick={release}><Trash2 size={14} /> {releasing ? 'Releasing…' : 'Release memory now'}</button><span role="status">{performance?.memory?.message || (performance?.memory?.state === 'unloaded' ? 'Voice memory released · loads when needed' : memoryBusy ? 'Voice process in use' : performance?.memory?.state === 'idle' ? 'Voice process idle' : '')}</span></div>
  <div class="performance-divider"></div>
  <label class="toggle-row"><span>Reuse unchanged passages<small>Quicker repeats and small edits, saved locally</small></span><input type="checkbox" bind:checked={settings.cache_enabled} onchange={onchange} /><span class="toggle-track"></span></label>
  <div class="cache-controls"><label><span>Reusable audio limit</span><select aria-label="Cache limit" bind:value={settings.cache_limit_mb} onchange={onchange}>{#each [128,256,512] as limit}<option value={limit}>{limit} MB</option>{/each}</select></label><button class="secondary-button" disabled={busy || !cache.count} onclick={() => action('clear')}><Trash2 size={14} /> Clear reusable audio</button></div>
  <p class="settings-hint">{cache.count || 0} passages · {((cache.bytes || 0)/1048576).toFixed(1)} MB. Clearing reusable audio keeps your recordings.</p>
</section>

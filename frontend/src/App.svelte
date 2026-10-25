<script lang="ts">
  import { onMount, onDestroy, tick, untrack } from 'svelte';
  import { House } from '@lucide/svelte';
  import { marked } from 'marked';
  import DOMPurify from 'dompurify';
  import { BookOpen, Headphones, Library, Settings2, Plus, ArrowUpRight, FileText, FolderOpen, ChevronDown, Check, Play, Pause, SkipBack, SkipForward, Volume2, Download, SlidersHorizontal, X, LoaderCircle, Moon, Sun, Monitor, CircleHelp, RotateCcw, Pencil, AlignLeft, Eye, AlertCircle, Square, Search, PanelLeft, AudioLines, ArrowRight, Trash2 } from '@lucide/svelte';
  import { getAPI, withTimeout, defaultSettings, type API, type Settings, type Document, type Job, type Prepared, type State } from './api';
  import Home from './Home.svelte';
  import FileContextMenu from './FileContextMenu.svelte';
  import FileDrop from './FileDrop.svelte';
  import { fileContext, type FileMenu, type FileItem } from './context-menu';
  import DocumentFind from './DocumentFind.svelte';
  import brandIcon from './assets/violilt.png';
  import PerformanceSettings from './PerformanceSettings.svelte';
  import MicrosoftNotice from './MicrosoftNotice.svelte';
  import Welcome from './Welcome.svelte';
  import VoiceSetup from './VoiceSetup.svelte';
  import { primeAudio, StreamPlayer } from './stream-player';

  let api = $state.raw<API>(null!);
  let ready = $state(false);
  let startupError = $state('');
  let starting = false;
  let startupVersion = 0;
  let preview = $state(false);
  let appState = $state<State | null>(null);
  let document = $state<Document | null>(null);
  let settings = $state<Settings>({ ...defaultSettings });
  let page = $state<'home' | 'studio' | 'library' | 'settings'>('home');
  let tab = $state<'read' | 'edit' | 'spoken'>('read');
  let searchContent = $state<HTMLElement>();
  let prepared = $state<Prepared | null>(null);
  let dirty = $state(false);
  let busy = $state(false);
  let startingGeneration = $state(false);
  let toast = $state('');
  let error = $state('');
  let dismissedRecoveryCount = $state(0);
  let help = $state(false);
  let microsoftNotice = $state(false);
  let welcome = $state(false);
  let welcomeSaving = $state(false);
  let welcomeError = $state('');
  let welcomeTrigger: HTMLButtonElement | undefined;
  let modelSetupPending = $state(false);
  let modelSetupError = $state('');
  let removal = $state<{ id: string; title: string; kind: 'document' | 'recording' } | null>(null);
  let deleteAudio = $state(false);
  let fileMenu = $state<FileMenu | null>(null);
  function openFileMenu(menu: FileMenu) { fileMenu = menu; }
  function requestFileRemoval(item: FileItem) { deleteAudio = false; removal = { id: item.id, title: item.title, kind: item.kind }; }
  async function revealFile(item: FileItem) { await act(() => item.kind === 'document' ? api.reveal_document(item.id) : api.reveal_recording(item.id)); }
  let helpDialog: HTMLDialogElement;
  let removalDialog: HTMLDialogElement;
  let closeDialog: HTMLDialogElement;
  let closeRequest = $state<string | null>(null);
  let closeError = $state('');
  let closeAttempt = 0;
  let shelf = $state(false);
  let voiceMenu = $state(false);
  let voiceTrigger = $state<HTMLButtonElement>();
  let voicePopup = $state<HTMLDivElement>();
  let shelfTrigger: HTMLButtonElement;
  let shelfPanel: HTMLElement;
  let query = $state('');
  let audio: HTMLAudioElement;
  let selectedJob = $state<Job | null>(null);
  let playing = $state(false);
  let streaming = $state(false);
  let buffering = $state(false);
  let wanted = $state(false);
  let ahead = $state(0);
  let streamPlayer: StreamPlayer | null = null;
  let refreshTask: Promise<void> | null = null;
  let selectionVersion = 0;
  let position = $state(0);
  let duration = $state(0);
  let volume = $state(0.8);
  let playbackSpeed = $state(1);
  let completedSeen = new Set<string>();
  let failuresSeen = new Set<string>();
  let poll: ReturnType<typeof setInterval>;
  let debounce: ReturnType<typeof setTimeout>;
  let maxSaveDelay: ReturnType<typeof setTimeout> | undefined;
  let toastTimer: ReturnType<typeof setTimeout>;
  let prepareVersion = 0;
  let saveChain = Promise.resolve();
  let pendingSaves = $state(0);
  let lastPositionSaved = 0;
  let systemDark = $state(false);

  const voiceDetails: Record<string, { name: string; description: string; accent: string; tone: string }> = {
    af_heart: { name: 'Heart', description: 'Warm, easy, and a little thoughtful.', accent: 'American English', tone: 'Warm & conversational' },
    af_bella: { name: 'Bella', description: 'Bright and clear, with a gentle rhythm.', accent: 'American English', tone: 'Clear & expressive' },
    af_sarah: { name: 'Sarah', description: 'A calm voice for a slower kind of reading.', accent: 'American English', tone: 'Calm & balanced' },
    am_michael: { name: 'Michael', description: 'A grounded voice with an unhurried pace.', accent: 'American English', tone: 'Steady & grounded' },
    am_adam: { name: 'Adam', description: 'A deeper voice with a direct delivery.', accent: 'American English', tone: 'Deep & direct' },
    bf_emma: { name: 'Emma', description: 'A soft British voice with a natural flow.', accent: 'British English', tone: 'Soft & considered' },
    bm_george: { name: 'George', description: 'A rich British voice for your next chapter.', accent: 'British English', tone: 'Rich & measured' },
  };
  const voice = $derived(voiceDetails[settings.voice] || { name: settings.voice.split('_').slice(1).join(' '), description: 'Find a voice that makes these words feel like yours.', accent: settings.voice.startsWith('b') ? 'British English' : 'American English', tone: 'English narration' });
  const voices = $derived(appState?.model.voices.length ? appState.model.voices : ['af_heart', 'af_bella', 'af_sarah', 'am_michael', 'bf_emma']);
  const engineReady = $derived(appState?.model.state === 'ready');
  const active = $derived(appState?.active);
  const testing = $derived(['running', 'cancelling'].includes(appState?.performance?.benchmark.state || ''));
  const words = $derived(prepared?.words || 0);
  const estimate = $derived(Math.max(1, Math.ceil(words / (155 * settings.speed))));
  const dark = $derived(settings.theme === 'dark' || (settings.theme === 'system' && systemDark));
  const recordings = $derived(appState?.jobs.filter(job => !job.preview && job.title.toLowerCase().includes(query.toLowerCase())) || []);
  const html = $derived(DOMPurify.sanitize(marked.parse(document?.markdown || '', { async: false }) as string, {
    ALLOWED_TAGS: ['h1', 'h2', 'h3', 'h4', 'p', 'br', 'strong', 'em', 'blockquote', 'ul', 'ol', 'li', 'code', 'pre', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'a', 'del'],
    ALLOWED_ATTR: [],
  }));

  $effect(() => { page; untrack(() => { fileMenu = null; }); });
  $effect(() => { if (help) helpDialog?.showModal(); else helpDialog?.close(); });
  $effect(() => { if (removal) removalDialog?.showModal(); else removalDialog?.close(); });
  $effect(() => { if (closeRequest) closeDialog?.showModal(); else closeDialog?.close(); });

  function notify(message: string) { toast = message; clearTimeout(toastTimer); toastTimer = setTimeout(() => toast = '', 4500); }
  async function act(operation: () => Promise<unknown>) {
    error = '';
    try { return await operation(); } catch (e) { error = e instanceof Error ? e.message : String(e); return null; }
  }
  async function refresh(afterMutation = false) {
    if (!api) return;
    if (refreshTask) {
      await refreshTask;
      if (!afterMutation) return;
    }
    // A removal must fetch state after any older poll has finished.
    if (!refreshTask) refreshTask = loadState().finally(() => { refreshTask = null; });
    await refreshTask;
  }
  async function loadState() {
    const next = await withTimeout(api.get_state()); appState = next;
    if (selectedJob) {
      const updated = next.jobs.find(job => job.id === selectedJob!.id);
      if (updated) selectedJob = updated;
      if (streamPlayer) {
        const version = selectionVersion;
        const data = await api.get_stream(selectedJob.id);
        if (version === selectionVersion) streamPlayer?.update(data);
      }
    }
    const newlyCompleted = next.jobs.filter(job => job.state === 'completed' && !completedSeen.has(job.id));
    newlyCompleted.forEach(job => completedSeen.add(job.id));
    const latest = newlyCompleted[0];
    if (latest) {
      if (selectedJob?.id !== latest.id) selectRecording(latest, latest.preview);
      if (!latest.preview) notify('Your reading is ready. Make yourself comfortable.');
    }
    const failure = next.jobs.find(job => job.state === 'failed' && !failuresSeen.has(job.id));
    next.jobs.filter(job => job.state === 'failed').forEach(job => failuresSeen.add(job.id));
    if (failure) error = failure.message;
  }
  async function review() {
    if (!document) return;
    const snapshot = { id: document.id, markdown: document.markdown };
    const version = ++prepareVersion;
    const result = await api.prepare_document(snapshot.markdown, { ...settings });
    if (version === prepareVersion && document?.id === snapshot.id && document.markdown === snapshot.markdown) prepared = result;
  }
  async function selectDocument(id: string) {
    await flushSave();
    await act(async () => { document = await api.get_document(id); dirty = false; page = 'studio'; shelf = false; tab = 'read'; await review(); await refresh(); });
  }
  async function showHome() { await act(async () => { await flushSave(); page = 'home'; shelf = false; await refresh(); }); }
  function showStudio() {
    if (!document && appState?.documents.length) void selectDocument(appState.documents[0].id);
    else { page = 'studio'; shelf = false; }
  }
  function editChanged() {
    dirty = true;
    ++prepareVersion;
    clearTimeout(debounce);
    debounce = setTimeout(() => { void act(flushSave); }, 1000);
    // Continuous typing must not postpone saving indefinitely.
    maxSaveDelay ??= setTimeout(() => { void act(flushSave); }, 5000);
  }
  function cancelAutosave() {
    clearTimeout(debounce);
    clearTimeout(maxSaveDelay);
    maxSaveDelay = undefined;
  }
  async function flushSave(prepareSpoken = true) {
    while (true) {
      cancelAutosave();
      if (document && dirty) {
        const snapshot = { ...document };
        dirty = false;
        pendingSaves++;
        saveChain = saveChain.catch(() => {}).then(async () => {
          try {
            const saved = await api.save_document(snapshot.id, snapshot.markdown);
            if (document?.id === snapshot.id && document.markdown === snapshot.markdown) {
              document = saved;
              dirty = false;
            }
          } catch (e) {
            if (document?.id === snapshot.id) dirty = true;
            throw e;
          } finally { pendingSaves--; }
        });
      }
      const pending = saveChain;
      try { await pending; } catch (e) {
        if (saveChain === pending) saveChain = Promise.resolve();
        throw e;
      }
      if (saveChain !== pending || (document && dirty)) continue;
      // Refresh errors must not mark a durable write dirty or delay close.
      // Normal saves update the shelf and Spoken; closing only needs the writes.
      if (prepareSpoken) {
        void refresh().catch(e => error = e instanceof Error ? e.message : String(e));
        await review();
      }
      if (saveChain === pending && (!document || !dirty)) return;
    }
  }
  function postCloseMessage(message: object) {
    const desktop = window as Window & { chrome?: { webview?: { postMessage(message: object): void } } };
    desktop.chrome?.webview?.postMessage(message);
  }
  function keepEditing() {
    const id = closeRequest;
    ++closeAttempt;
    closeRequest = null;
    closeError = '';
    if (id) postCloseMessage({ type: 'violilt:close-response', id, saved: false });
  }
  async function saveBeforeClose() {
    const id = closeRequest;
    if (!id) return;
    const attempt = ++closeAttempt;
    closeError = '';
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      // Drain durable writes without waiting for a Spoken preview. A timeout
      // cancels close approval, never an already-running database write.
      await Promise.race([flushSave(false), new Promise<never>((_resolve, reject) => {
        timer = setTimeout(() => reject(new Error('Saving is taking longer than expected. Your window is still open. Keep editing or retry saving before closing.')), 10000);
      })]);
      if (attempt === closeAttempt && closeRequest === id) {
        postCloseMessage({ type: 'violilt:close-response', id, saved: true });
      }
    } catch (e) {
      if (attempt === closeAttempt && closeRequest === id) {
        closeError = e instanceof Error ? e.message : String(e);
      }
    } finally { clearTimeout(timer); }
  }
  function requestNativeClose(event: Event) {
    const id = (event as CustomEvent<{ id?: unknown }>).detail?.id;
    if (closeRequest || typeof id !== 'string' || !/^[A-Za-z0-9]{1,64}$/.test(id)) return;
    microsoftNotice = false; welcome = false; help = false; removal = null; fileMenu = null; voiceMenu = false;
    closeRequest = id;
    void saveBeforeClose();
  }
  async function changeSettings() {
    ++prepareVersion;
    streamPlayer?.preferences(settings.buffer_mode, playbackSpeed, volume);
    await act(async () => { await api.save_settings({ ...settings }); await review(); await refresh(); });
  }
  async function setupVoices(method: 'download' | 'import') {
    if (!ready || preview || modelSetupPending || (method === 'download' && engineReady) || appState?.model.state === 'downloading') return;
    modelSetupPending = true; modelSetupError = '';
    try {
      const model = method === 'download' ? await withTimeout(api.setup_model()) : await api.import_model();
      if (model && appState) appState = { ...appState, model };
      await refresh(true);
    } catch (e) { modelSetupError = e instanceof Error ? e.message : String(e); }
    finally { modelSetupPending = false; }
  }
  function openWelcome() {
    const focused = window.document.activeElement;
    welcomeTrigger = focused instanceof HTMLButtonElement ? focused : undefined;
    help = false; welcomeError = ''; welcome = true;
  }
  async function finishWelcome(destination: 'home' | 'studio' | 'close', remember = true) {
    if (welcomeSaving) return;
    welcomeSaving = true; welcomeError = '';
    try {
      if (remember && (appState?.welcome_version || 0) < 1) {
        if (await withTimeout(api.complete_welcome()) !== true) throw new Error('Your welcome preference could not be saved. Retry, or continue for this session.');
        if (appState) appState = { ...appState, welcome_version: 1 };
      }
      welcome = false;
      if (destination === 'studio') { if (!appState?.documents.length) await newDocument(); else showStudio(); }
      else if (destination === 'home') await showHome();
      await tick();
      const target = welcomeTrigger?.isConnected && welcomeTrigger.getClientRects().length ? welcomeTrigger : window.document.querySelector<HTMLButtonElement>('.brand');
      target?.focus();
    } catch (e) { welcomeError = e instanceof Error ? e.message : String(e); }
    finally { welcomeSaving = false; }
  }
  async function performanceAction(name: 'test' | 'stop' | 'warm' | 'release' | 'clear') {
    await act(async () => {
      if (name === 'test') await api.start_benchmark();
      else if (name === 'stop') await api.stop_benchmark();
      else if (name === 'warm') await api.warm_engine();
      else if (name === 'release') { await api.release_engine(); notify('Voice memory released. It reloads for your next reading.'); }
      else { await api.clear_cache(); notify('Reusable audio cleared. Your recordings are kept.'); }
      await refresh();
    });
  }
  async function importDocument() {
    await act(async () => { await flushSave(); const imported = await api.import_document(); if (imported) { document = imported; dirty = false; page = 'studio'; tab = 'read'; await review(); await refresh(); notify('Added to your shelf. The original file stays untouched.'); } });
  }
  async function importDroppedFiles(files: File[]) {
    await act(async () => {
      await flushSave();
      const result = await api.import_dropped_documents(files);
      if (result.documents.length) {
        help = false; removal = null; fileMenu = null; voiceMenu = false; shelf = false;
        document = result.documents[0]; dirty = false; page = 'studio'; tab = 'read';
        await review(); await refresh(true);
        notify(result.documents.length === 1 ? 'Added to your shelf. The original file stays untouched.' : `Added ${result.documents.length} readings to your shelf. Your originals stay untouched.`);
      }
      if (result.errors.length) error = result.errors.slice(0, 3).map(item => `${item.name}: ${item.message}`).join(' ') + (result.errors.length > 3 ? ` And ${result.errors.length - 3} more files could not be added.` : '');
    });
  }
  async function newDocument() {
    await act(async () => { await flushSave(); document = await api.new_document(); dirty = false; page = 'studio'; tab = 'edit'; await review(); await refresh(); });
  }
  async function generate() {
    if (!document || busy) return;
    if (!engineReady) { page = 'settings'; return; }
    if (settings.auto_listen) primeAudio();
    busy = true;
    startingGeneration = true;
    try {
      await act(async () => { await flushSave(); const job = await api.generate(document!.id, document!.markdown, { ...settings }); selectRecording(job, settings.auto_listen); await refresh(); });
    } finally { busy = false; startingGeneration = false; }
  }
  async function voicePreview() {
    if (!engineReady) { page = 'settings'; return; }
    busy = true;
    await act(async () => { await api.preview_voice(settings.voice, settings.speed); await refresh(); });
    busy = false;
  }
  function selectRecording(job: Job, autoplay = false) {
    if (selectedJob) void api.save_position(selectedJob.id, streaming ? position : audio.currentTime);
    streamPlayer?.dispose(); streamPlayer = null; ++selectionVersion;
    if (audio) audio.pause();
    streaming = job.state !== 'completed'; buffering = false; wanted = false; ahead = 0;
    position = job.position || 0;
    if (job.state === 'completed' && position >= job.duration - .5) position = 0;
    selectedJob = { ...job, position };
    duration = job.available_duration || job.duration;
    playing = false;
    lastPositionSaved = position;
    if (streaming) {
      const version = selectionVersion;
      streamPlayer = new StreamPlayer(job.id, position, state => {
        if (version !== selectionVersion) return;
        position = state.position; duration = state.duration; playing = state.playing; buffering = state.waiting; ahead = state.ahead; wanted = state.wanted;
        if (Math.abs(position - lastPositionSaved) >= 5) { lastPositionSaved = position; void api.save_position(job.id, position); }
      }, message => error = message);
      streamPlayer.preferences(settings.buffer_mode, playbackSpeed, volume);
      void api.get_stream(job.id).then(data => { if (version === selectionVersion) streamPlayer?.update(data); }).catch(e => error = String(e));
      if (autoplay) streamPlayer.play(true);
    } else {
      if (audio?.readyState >= 1 && audio.currentSrc.endsWith(`/media/${job.id}.wav`)) loadedAudio();
      if (autoplay) setTimeout(() => { if (selectedJob?.id === job.id) void audio?.play().catch(() => notify('Your audio is ready. Press play to listen.')); }, 120);
    }
  }
  async function continueJob(job: Job) {
    if (settings.auto_listen) primeAudio();
    await act(async () => { const resumed = await api.resume_job(job.id); if (selectedJob?.id !== job.id) selectRecording(resumed, settings.auto_listen); await refresh(); notify('Continuing from the last completed section.'); });
  }
  function loadedAudio() { if (selectedJob && !streaming) { audio.currentTime = Math.min(selectedJob.position || 0, audio.duration || 0); audio.volume = volume; audio.playbackRate = playbackSpeed; duration = audio.duration; } }
  async function togglePlay() {
    if (!selectedJob) return;
    if (streamPlayer) { if (wanted) { streamPlayer.pause(); void api.save_position(selectedJob.id, position); } else streamPlayer.play(); return; }
    if (audio.paused) await act(() => audio.play()); else audio.pause();
  }
  function seek(value: number) { if (streamPlayer) streamPlayer.seek(value); else if (audio && selectedJob) { audio.currentTime = Math.max(0, Math.min(value, duration)); position = audio.currentTime; } if (selectedJob) void api.save_position(selectedJob.id, position); }
  function changePlayback() { playbackSpeed = playbackSpeed >= 2 ? 0.75 : playbackSpeed === 0.75 ? 1 : playbackSpeed + 0.25; if (streamPlayer) streamPlayer.preferences(settings.buffer_mode, playbackSpeed, volume); else audio.playbackRate = playbackSpeed; }
  function changeVolume() { if (streamPlayer) streamPlayer.preferences(settings.buffer_mode, playbackSpeed, volume); else if (audio) audio.volume = volume; }
  function timeUpdate() {
    if (streaming) return;
    position = audio.currentTime;
    if (selectedJob && Math.abs(position - lastPositionSaved) >= 5) { lastPositionSaved = position; void api.save_position(selectedJob.id, position); }
  }
  function formatTime(value: number) { if (!Number.isFinite(value)) return '0:00'; return `${Math.floor(value / 60)}:${String(Math.floor(value % 60)).padStart(2, '0')}`; }
  function date(value: number) { return new Date(value * 1000).toLocaleDateString('en', { month: 'short', day: 'numeric' }); }
  function jobLabel(job: Job) { if (job.can_resume === false && ['cancelled', 'failed', 'interrupted'].includes(job.state)) return 'Saved audio available'; return job.state === 'completed' ? formatTime(job.duration) : job.state === 'cancelled' ? 'Paused generation' : job.state === 'interrupted' ? 'Continue reading' : job.state === 'failed' ? 'Needs a retry' : job.state; }
  async function exportAudio(job = selectedJob) { if (job) await act(async () => { const path = await api.export_recording(job.id); if (path) notify('Recording exported. Ready to take with you.'); }); }
  async function confirmRemoval() {
    if (!removal || busy) return;
    busy = true;
    await act(async () => {
      const item = removal!;
      if (item.kind === 'document') {
        await flushSave(); await api.remove_document(item.id);
        const wasOpen = document?.id === item.id;
        if (wasOpen) { ++prepareVersion; document = null; prepared = null; dirty = false; }
        await refresh(true);
        if (wasOpen && page === 'studio' && appState?.documents.length) await selectDocument(appState.documents[0].id);
      } else {
        await api.remove_recording(item.id, deleteAudio);
        if (selectedJob?.id === item.id) { streamPlayer?.dispose(); streamPlayer = null; ++selectionVersion; audio.pause(); selectedJob = null; streaming = buffering = wanted = false; position = duration = 0; }
        await refresh(true);
      }
      removal = null; deleteAudio = false; notify('Removed from your shelf.');
    });
    busy = false;
  }
  function capturePopupFocus(region: HTMLElement | undefined, trigger: HTMLButtonElement | undefined) {
    const focused = window.document.activeElement;
    return region && trigger && focused && region.contains(focused) ? { region, trigger, focused } : null;
  }
  async function restorePopupFocus(focus: ReturnType<typeof capturePopupFocus>, closed: () => boolean, hidden = false) {
    if (!focus) return;
    await tick();
    const { region, trigger, focused } = focus;
    const current = window.document.activeElement;
    if (!closed() || closeRequest || window.document.querySelector('dialog[open]')) return;
    if (hidden && getComputedStyle(region).display !== 'none') return;
    // A different control may intentionally acquire focus while dismissal renders.
    if (current && current !== window.document.body && current !== focused) return;
    if (!trigger.isConnected || trigger.disabled || !trigger.getClientRects().length || getComputedStyle(trigger).visibility === 'hidden') return;
    trigger.focus({ preventScroll: true });
  }
  function closeVoiceMenu() {
    const focus = capturePopupFocus(voicePopup, voiceTrigger);
    voiceMenu = false;
    void restorePopupFocus(focus, () => !voiceMenu);
  }
  function dismissPopups() {
    const voiceFocus = voiceMenu ? capturePopupFocus(voicePopup, voiceTrigger) : null;
    const shelfFocus = !voiceFocus && shelf ? capturePopupFocus(shelfPanel, shelfTrigger) : null;
    voiceMenu = false; shelf = false;
    void restorePopupFocus(voiceFocus || shelfFocus, () => !voiceMenu && !shelf, !!shelfFocus);
  }
  function keyboard(event: KeyboardEvent) {
    if (microsoftNotice || welcome) {
      if ((event.ctrlKey || event.metaKey) && ['o', 's'].includes(event.key)) event.preventDefault();
      return; // Let the native dialog handle Tab, Enter, Space and Escape.
    }
    if (!ready) return;
    if (closeRequest) {
      if ((event.ctrlKey || event.metaKey) && ['o', 's'].includes(event.key)) event.preventDefault();
      return;
    }
    if (help || removal || window.document.querySelector('dialog[open]')) {
      if ((event.ctrlKey || event.metaKey) && ['o', 's'].includes(event.key.toLowerCase())) event.preventDefault();
      return; // Preserve native modal button activation and Escape cancellation.
    }
    if (fileMenu) return;
    const editing = ['INPUT', 'TEXTAREA', 'SELECT'].includes((event.target as HTMLElement)?.tagName);
    if ((event.ctrlKey || event.metaKey) && event.key === 'o') { event.preventDefault(); void importDocument(); }
    if ((event.ctrlKey || event.metaKey) && event.key === 's') { event.preventDefault(); void act(flushSave); }
    if (event.code === 'Space' && !editing && selectedJob && !(event.target as HTMLElement)?.closest('button, summary')) { event.preventDefault(); void togglePlay(); }
    if (event.key === 'Escape') { help = false; removal = null; dismissPopups(); }
  }

  async function initialize() {
    if (starting) return;
    starting = true; startupError = ''; error = '';
    const version = ++startupVersion;
    try {
      const connection = await getAPI();
      const state = await withTimeout(connection.api.get_state());
      if (version !== startupVersion) return;
      api = connection.api; preview = connection.preview;
      appState = state; settings = { ...defaultSettings, ...state.settings };
      completedSeen = new Set(state.jobs.filter(job => job.state === 'completed').map(job => job.id));
      failuresSeen = new Set(state.jobs.filter(job => job.state === 'failed').map(job => job.id));
      if (!preview) postCloseMessage({ type: 'violilt:close-ready' });
      ready = true;
      welcome = (state.welcome_version || 0) < 1;
      const available = state.jobs.filter(job => !job.preview && (job.state === 'completed' || (job.available_duration || 0) > 0));
      const latest = [...available].filter(job => job.position > 0 && job.position < (job.duration || job.available_duration || 0) - 2).sort((a, b) => (b.last_listened || b.created) - (a.last_listened || a.created))[0] || available[0];
      if (latest) selectRecording(latest);
      clearInterval(poll);
      poll = setInterval(() => { void refresh().catch(e => error = e instanceof Error ? e.message : String(e)); }, 900);
    } catch (e) {
      if (version === startupVersion) startupError = e instanceof Error ? e.message : String(e);
    } finally { starting = false; }
  }

  onMount(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    systemDark = media.matches;
    const themeChanged = () => systemDark = media.matches;
    media.addEventListener('change', themeChanged);
    window.addEventListener('violilt:close-request', requestNativeClose);
    void initialize();
    return () => {
      media.removeEventListener('change', themeChanged);
      window.removeEventListener('violilt:close-request', requestNativeClose);
    };
  });
  onDestroy(() => { ++startupVersion; if (selectedJob) void api.save_position(selectedJob.id, position); streamPlayer?.dispose(); clearInterval(poll); cancelAutosave(); clearTimeout(toastTimer); });
</script>

<svelte:window onkeydown={keyboard} />

<div class:dark class="app-shell" data-palette={settings.palette}>
  <FileDrop enabled={ready && !closeRequest && !microsoftNotice && !welcome} importFiles={importDroppedFiles} />
  <aside bind:this={shelfPanel} class:opened={shelf} class="sidebar">
    <button class="brand" onclick={showHome} disabled={!ready} aria-label="Violilt home"><img class="brand-icon" src={brandIcon} alt="" /><span class="brand-name">Violilt<span>YOUR WORDS, OUT LOUD</span></span></button>
    <div class="sidebar-rule"></div>
    <nav aria-label="Main navigation">
      <button class:current={page === 'home'} onclick={showHome} disabled={!ready}><House size={19} strokeWidth={1.6} /><span>Home</span><span class="nav-dot"></span></button>
      <button class:current={page === 'studio'} onclick={showStudio} disabled={!ready}><BookOpen size={19} strokeWidth={1.6} /><span>Reading room</span><span class="nav-dot"></span></button>
      <button class:current={page === 'library'} disabled={!ready} onclick={() => { page = 'library'; shelf = false; }}><Library size={19} strokeWidth={1.6} /><span>Your recordings</span>{#if appState?.jobs.filter(j => !j.preview && j.state === 'completed').length}<span class="count">{appState.jobs.filter(j => !j.preview && j.state === 'completed').length}</span>{/if}</button>
    </nav>
    <div class="shelf-heading"><span>ON YOUR SHELF</span><button title="New reading" onclick={newDocument} disabled={!ready}><Plus size={16} /></button></div>
    <div class="document-list">
      {#each appState?.documents || [] as doc}
        <button use:fileContext={{ item: { ...doc, kind: 'document' }, open: openFileMenu }} class:chosen={document?.id === doc.id && page === 'studio'} aria-current={document?.id === doc.id && page === 'studio' ? 'true' : undefined} onclick={() => selectDocument(doc.id)}><FileText size={17} strokeWidth={1.5} /><span>{doc.title}<small>Reading</small></span></button>
      {/each}
      {#if ready && !appState?.documents.length}<p class="shelf-empty">A home for the words<br />you want to return to.</p>{/if}
    </div>
    <button class="add-reading" onclick={importDocument} disabled={!ready}><Plus size={16} /> Add a reading <span>↗</span></button>
    <div class="sidebar-bottom">
      <div class="quiet-note"><p>A little less scrolling.<br /><strong>A little more listening.</strong></p></div>
      <button class:current={page === 'settings'} class="sidebar-settings" disabled={!ready} onclick={() => { page = 'settings'; shelf = false; }}><Settings2 size={18} strokeWidth={1.5} /><span>Settings</span></button>
      <div class="sidebar-footer"><img class="footer-mark" src={brandIcon} alt="" /><div>Made for your own pace<small>Violilt · local audio studio</small></div><button title="About Violilt" onclick={() => help = true}><CircleHelp size={16} /></button></div>
    </div>
  </aside>

  <div class="workspace">
    <header class="topbar">
      <div class="breadcrumb"><button bind:this={shelfTrigger} class="shelf-toggle" title="Toggle shelf" aria-expanded={shelf} onclick={() => shelf = !shelf}><PanelLeft size={18} /></button><span>Workspace</span><span class="breadcrumb-slash">/</span><strong>{page === 'home' ? 'Home' : page === 'studio' ? 'Reading room' : page === 'library' ? 'Recordings' : 'Settings'}</strong></div>
      <div class="top-actions">{#if preview}<span class="preview-label">Interface preview</span>{/if}<button class="engine-pill" disabled={!ready} onclick={() => page = 'settings'}><span class:ready={engineReady} class="status-dot"></span>{engineReady ? 'Voice engine ready' : appState?.model.state === 'downloading' ? 'Setting up voices' : 'Voice setup'}<ArrowUpRight size={13} /></button><span class="top-separator"></span><button class="import-button" onclick={importDocument} disabled={!ready}><FolderOpen size={16} /> Import document <span>Ctrl O</span></button></div>
    </header>

    {#if error}<div class="error-banner" role="alert"><AlertCircle size={17} /><span>{error}</span><button title="Dismiss error" onclick={() => error = ''}><X size={16} /></button></div>{/if}
    {#if appState?.recovery && appState.recovery.count > dismissedRecoveryCount}<div class="error-banner" role="alert"><AlertCircle size={17} /><span>{appState.recovery.message}</span><button title="Dismiss recovery notice" onclick={() => dismissedRecoveryCount = appState?.recovery?.count || 0}><X size={16} /></button></div>{/if}

    {#if !ready}
      <div class="loading-screen"><img class="loading-brand" src={brandIcon} alt="Violilt" />
        {#if startupError}<AlertCircle size={24} /><h2>Let’s get you back to your library.</h2><p class="startup-message" role="alert">{startupError}</p><button class="primary-button" onclick={initialize}><RotateCcw size={16} /> Retry connection</button>
        {:else}<LoaderCircle size={23} class="spin" /><p>Opening your library…</p>{/if}
      </div>
    {:else if page === 'home'}
      <Home {openFileMenu} documents={appState?.documents || []} jobs={appState?.jobs || []} model={appState?.model} setupPending={modelSetupPending} setupError={modelSetupError} setup={setupVoices} {preview} generating={!!active || testing} openDocument={selectDocument} {importDocument} {newDocument} listen={(job) => selectRecording(job, true)} {exportAudio} {continueJob} showLibrary={() => page = 'library'} {showStudio} voiceName={(id) => voiceDetails[id]?.name || id.split('_').slice(1).join(' ')} />
    {:else if page === 'studio'}
      <div class="studio-layout">
        <main class="reading-workspace">
          <div class="document-toolbar"><div class="eyebrow"><span class="small-square"></span> A PLACE FOR YOUR WORDS</div><div class="document-tabs" role="group" aria-label="Document view"><button class:active={tab === 'read'} aria-pressed={tab === 'read'} onclick={() => tab = 'read'} title="Read document"><Eye size={15} /> Read</button><button class:active={tab === 'edit'} aria-pressed={tab === 'edit'} onclick={() => tab = 'edit'} title="Edit Markdown"><Pencil size={14} /> Edit</button><button class:active={tab === 'spoken'} aria-pressed={tab === 'spoken'} onclick={() => tab = 'spoken'} title="Preview spoken text"><AlignLeft size={15} /> Spoken</button></div></div>
          <DocumentFind content={searchContent} revision={`${document?.id}:${tab}:${tab === 'spoken' ? prepared?.text : document?.markdown}`} enabled={!!document} />
          <div class="document-scroll">
            {#if document}
              <div class="reading-meta"><span><FileText size={13} /> READING</span><span class="meta-dot">·</span><span>{pendingSaves ? 'Saving changes…' : dirty ? 'Unsaved changes' : 'Saved to your shelf'}</span></div>
              {#if document.source?.toLowerCase().endsWith('.pdf')}<div class="omission-note" role="note">PDF import includes selectable text only. Images and scanned pages are not included. Review the text and reading order before generating.</div>{/if}
              {#if tab === 'edit'}
                <div class="editor-heading"><h1>Your words.<br /><em>Your way.</em></h1><p>Write or paste Markdown. Your working copy saves automatically.</p></div>
                <textarea bind:this={searchContent} aria-label="Markdown editor" class="markdown-editor" spellcheck="false" bind:value={document.markdown} oninput={editChanged}></textarea>
              {:else if tab === 'spoken'}
                <div class="spoken-heading"><span class="eyebrow">WHAT YOUR VOICE WILL READ</span><h1>A clear view<br /><em>of every word.</em></h1><p>Formatting becomes natural pauses. The wording stays yours.</p></div>
                {#if prepared?.omissions.code_blocks || prepared?.omissions.metadata}<div class="omission-note"><Check size={15} /> {prepared.omissions.code_blocks ? `${prepared.omissions.code_blocks} code block${prepared.omissions.code_blocks === 1 ? '' : 's'} skipped. ` : ''}{prepared.omissions.metadata ? 'Document metadata omitted.' : ''}</div>{/if}
                {#if prepared?.unread_count}<div class="omission-note"><Check size={15} /> {prepared.unread_count} symbol{prepared.unread_count === 1 ? '' : 's'} omitted from speech. Details will be saved in unread.txt with your recording.</div>{/if}
                <div bind:this={searchContent} class="spoken-text">{prepared?.text || (prepared?.unread_count ? 'No readable text remains after symbol handling.' : 'Add some text to begin your reading.')}</div>
              {:else}
                <article bind:this={searchContent} class="reading-article">{@html html}</article>
              {/if}
              <div class="document-end"><span></span><AudioLines size={20} strokeWidth={1.3} /><span></span></div>
              <div class="endnote">Words worth keeping. A voice to carry them.</div>
            {:else}
              <div class="empty-reading"><BookOpen size={38} strokeWidth={1} /><h1>Your next reading<br /><em>starts here.</em></h1><p>Bring a Markdown, TXT or PDF file, or begin with a blank page.</p><button class="primary-button" onclick={newDocument}><Plus size={17} /> New reading</button></div>
            {/if}
          </div>
          <footer class="reading-footer"><span><span class="status-dot ready"></span> Working copy saved locally {#if document}<button class="icon-button remove-reading" title="Remove reading" onclick={() => { removal = { id: document!.id, title: document!.title, kind: 'document' }; }}><Trash2 size={13} /></button>{/if}</span><span>{words.toLocaleString()} words<span class="meta-dot">·</span>About {estimate} min of listening</span></footer>
        </main>

        <aside class="voice-panel"><div class="voice-controls">
          <div class="panel-heading"><span class="eyebrow">GIVE YOUR WORDS A VOICE</span><SlidersHorizontal size={16} strokeWidth={1.4} /></div>
          <h2>Find your rhythm.</h2>
          <p class="panel-intro">A voice that feels right.<br />A pace that feels like you.</p>
          <div class="voice-art" aria-hidden="true"><div class="orb-rings"><span></span><span></span><span></span><span></span></div><div class="art-caption">a little warmth<br />in every word.</div><span class="art-number">01 / VOICE</span></div>
          <div class="voice-selector-wrap"><button bind:this={voiceTrigger} class:expanded={voiceMenu} class="voice-selector" onclick={() => voiceMenu = !voiceMenu} aria-expanded={voiceMenu}><div><small>YOUR NARRATOR</small><strong>{voice.name}</strong><span>{voice.accent}</span></div><ChevronDown size={17} /></button>
            {#if voiceMenu}<div bind:this={voicePopup} class="voice-menu">{#each voices as item}<button class:selected={item === settings.voice} onclick={() => { settings.voice = item; closeVoiceMenu(); void changeSettings(); }}><span>{voiceDetails[item]?.name || item.split('_').slice(1).join(' ')}<small>{item.startsWith('b') ? 'British' : 'American'} · {item.includes('m_') ? 'Male' : 'Female'}</small></span>{#if item === settings.voice}<Check size={16} />{/if}</button>{/each}</div>{/if}
          </div>
          <button class="preview-voice" onclick={voicePreview} disabled={!!active || testing || busy}><Play size={13} fill="currentColor" /> Listen to a sample <span>{active?.preview ? 'Preparing…' : '≈ 8 sec'}</span></button>
          <div class="control-group"><div class="control-label"><span>Narration speed</span><strong>{settings.speed.toFixed(1)}<small>×</small></strong></div><input type="range" min="0.5" max="2" step="0.1" aria-label="Narration speed" bind:value={settings.speed} onchange={changeSettings} /><div class="range-labels"><span>A little slower</span><span>A little quicker</span></div></div>
          <div class="reading-options"><span class="control-label">THE LITTLE DETAILS</span><label class="toggle-row"><span>Read code blocks<small>Included only when you want them</small></span><input type="checkbox" bind:checked={settings.include_code} onchange={changeSettings} /><span class="toggle-track"></span></label><label class="pause-control"><span>Space between paragraphs</span><select aria-label="Paragraph pause" bind:value={settings.paragraph_pause} onchange={changeSettings}><option value={0.15}>Short</option><option value={0.3}>Natural</option><option value={0.6}>Unhurried</option></select></label></div>
          <div class="processing-control"><div><span>PROCESSING PACE</span><button onclick={() => page = 'settings'}>Tune it <ArrowUpRight size={12} /></button></div><div class="compact-presets">{#each ['quiet', 'balanced', 'fast', 'custom'] as mode}<button class:selected={settings.performance_mode === mode} aria-pressed={settings.performance_mode === mode} onclick={() => { settings.performance_mode = mode as Settings['performance_mode']; void changeSettings(); }}>{mode.charAt(0).toUpperCase()+mode.slice(1)}</button>{/each}</div><p class="processing-caption">{active?.engine?.label || appState?.performance?.configuration.label || 'CPU'} · {active?.engine?.threads || appState?.performance?.configuration.threads || 4} threads{active ? ' · Changes apply to the next reading' : ' · Listen while the rest is prepared'}</p></div>
          </div><div class="generation-area">
            {#if active}
              {@const usingGpu = ['CUDAExecutionProvider', 'DmlExecutionProvider'].includes(active.engine?.provider || '')}
              <div class="generation-progress" role="status">
                <div><span>{active.state === 'preparing' ? 'Preparing your reading…' : active.state === 'assembling' ? 'Saving recording…' : active.state === 'cancelling' ? 'Stopping generation…' : 'Generating audio…'}</span><strong>{Math.round(active.completed / Math.max(1, active.total) * 100)}%</strong></div>
                <div class="progress-track"><span style:width={`${active.completed / Math.max(1, active.total) * 100}%`}></span></div>
                <p>{active.message}</p>
                {#if active.unread_count}<p class="settings-hint" title={`${appState?.storage}/jobs/${active.id}/unread.txt`}>{active.unread_count} symbol{active.unread_count === 1 ? '' : 's'} omitted from speech. Details saved in unread.txt.</p>{/if}
                {#each active.pronunciation_warnings || [] as warning}<p class="settings-hint">{warning}</p>{/each}
                <div class="live-metrics">
                  {#if active.state === 'generating'}<span>Model loaded</span>{/if}
                  {#if active.throughput}<span><strong>{active.throughput.toFixed(1)}×</strong> generation</span>{/if}
                  {#if (active.available_duration || 0) > 0}<span><strong>{formatTime(active.available_duration || 0)}</strong> ready</span>{/if}
                  {#if active.first_audio_seconds != null}<span>First audio <strong>{active.first_audio_seconds.toFixed(1)}s</strong></span>{/if}
                  {#if active.cache_hits}<span>{active.cache_hits} reused</span>{/if}
                </div>
                {#if appState?.performance?.cpu_percent != null || (usingGpu && appState?.performance?.gpu_percent != null)}
                  <details class="hardware-usage">
                    <summary>Performance details</summary>
                    <div class="live-metrics">
                      {#if appState?.performance?.cpu_percent != null}<span title="Speech worker usage, as a percentage of total CPU capacity."><strong>{appState.performance.cpu_percent}%</strong> CPU usage</span>{/if}
                      {#if usingGpu && appState?.performance?.gpu_percent != null}<span title="Speech worker's busiest GPU engine. Other applications are excluded."><strong>{appState.performance.gpu_percent}%</strong> GPU usage</span>{/if}
                    </div>
                  </details>
                {/if}
              </div>
              <button class="secondary-button" onclick={() => act(async () => { await api.cancel_generation(); await refresh(); })} disabled={active.state === 'cancelling'}><Square size={13} /> {active.state === 'cancelling' ? 'Stopping after this section…' : 'Stop generation'}</button>
            {:else}<div class="generation-summary"><span>Your next listen</span><strong>~{estimate} <small>min</small></strong></div><button class="primary-button generate-button" onclick={generate} disabled={busy || testing || !words}>{#if startingGeneration}<LoaderCircle size={18} class="spin" /> Preparing your reading…{:else}<Headphones size={18} /> {engineReady ? 'Create your audio' : 'Set up & start listening'} <ArrowRight size={17} />{/if}</button><p class="generation-footnote">{engineReady ? 'Listen as it arrives. Saved to your library.' : 'One free model download. Then local speech.'}</p>{/if}
          </div>
        </aside>
      </div>
    {:else if page === 'library'}
      <main class="library-page"><div class="page-heading"><div><span class="eyebrow">WORDS YOU CAN RETURN TO</span><h1>Your listening shelf<span>.</span></h1><p>A home for finished recordings and readings in progress.</p></div><div class="search-field"><Search size={17} /><input aria-label="Search recordings" placeholder="Find a reading…" bind:value={query} /></div></div>
        <div class="library-stats"><span><Headphones size={16} /> {appState?.jobs.filter(j => !j.preview && j.state === 'completed').length || 0} saved recordings</span><span>At your pace, whenever you like.</span></div>
        {#if recordings.length}<div class="recording-grid">{#each recordings as job}<div class="recording-card" role="group" aria-label={`Recording: ${job.title}`} use:fileContext={{ item: { ...job, kind: 'recording' }, open: openFileMenu }}><div class="recording-art"><div class="mini-waves" aria-hidden="true">{#each [14, 26, 38, 22, 46, 32, 50, 28, 42, 20, 34, 14] as height}<span style:height={`${height}px`}></span>{/each}</div><span>{job.state === 'completed' ? 'READY FOR A LISTEN' : 'A WORK IN PROGRESS'}</span></div><div class="recording-info"><div class="card-date">{date(job.created)}<span>{jobLabel(job)}</span></div><h2>{job.title}</h2><p>{voiceDetails[job.voice]?.name || job.voice} <span>·</span> {job.speed.toFixed(1)}× narration</p><div class="recording-actions">{#if job.state !== 'completed' && (job.available_duration || 0) > 0}<button class="icon-button" title="Listen to available audio" onclick={() => selectRecording(job, true)}><Headphones size={16} /></button>{/if}{#if job.state === 'completed'}<button class="card-play" onclick={() => selectRecording(job, true)}><Play size={14} fill="currentColor" /> Listen</button><button class="icon-button" title="Export WAV" onclick={() => exportAudio(job)}><Download size={17} /></button>{:else if ['cancelled', 'failed', 'interrupted'].includes(job.state)}{#if job.can_resume !== false}<button class="card-play" disabled={!!active || testing} onclick={() => continueJob(job)}><RotateCcw size={14} /> Continue</button>{/if}{:else}<button class="card-play" onclick={() => { if (job.completed) selectRecording(job, true); page = 'studio'; }}><LoaderCircle size={14} class="spin" /> In progress</button>{/if}{#if ['completed', 'cancelled', 'failed', 'interrupted'].includes(job.state)}<button class="icon-button" title="Remove recording" onclick={() => { deleteAudio = false; removal = { id: job.id, title: job.title, kind: 'recording' }; }}><Trash2 size={16} /></button>{/if}</div>{#if job.resume_message}<p class="job-error">{job.resume_message}</p>{:else if job.state === 'failed'}<p class="job-error">{job.message}</p>{/if}{#each job.pronunciation_warnings || [] as warning}<p class="settings-hint">{warning}</p>{/each}</div></div>{/each}</div>{:else}<div class="library-empty"><div class="empty-art"><Headphones size={48} strokeWidth={1} /></div><h2>Good words deserve<br /><em>a second listen.</em></h2><p>{query ? 'No recordings match that search.' : 'Your recordings will live here. Start with a reading, choose a voice, and make something worth keeping.'}</p><button class="primary-button" onclick={() => page = 'studio'}>Back to the reading room <ArrowRight size={17} /></button></div>{/if}
      </main>
    {:else}
      <main class="settings-page"><div class="page-heading"><div><span class="eyebrow">MAKE YOURSELF AT HOME</span><h1>The little details<span>.</span></h1><p>Your voice, your space, your pace.</p></div></div>
        <section class="settings-card"><VoiceSetup model={appState?.model} pending={modelSetupPending} disabled={!!active || testing} error={modelSetupError} setup={setupVoices} {preview} /></section>
        <section class="settings-card"><div class="settings-title"><CircleHelp size={22} strokeWidth={1.4} /><div><h2>Getting started &amp; privacy</h2><p>A little guidance, whenever you need it.</p></div></div><div class="settings-actions"><button class="secondary-button" onclick={openWelcome}>Welcome &amp; quick guide</button><button class="secondary-button" onclick={() => microsoftNotice = true}>Microsoft services &amp; privacy</button></div></section>
        <PerformanceSettings bind:settings performance={appState?.performance || null} cache={appState?.cache || {count:0,bytes:0,limit_mb:256}} busy={!!active || testing || appState?.performance?.warmup.state === 'loading'} ready={!!engineReady && !preview} onchange={changeSettings} action={performanceAction} />
        <section class="settings-card"><div class="settings-title"><Sun size={22} strokeWidth={1.4} /><div><h2>A space that feels like yours</h2><p>Choose your palette, then the light you like to read in.</p></div></div><div class="palette-choices" role="group" aria-label="Theme palette">
          {#each [{id: 'violilt', name: 'Violilt', description: 'Ivory, lilac & soft sage', colors: ['#F7F5EF', '#202726', '#7C83C9', '#A8C3B6']}, {id: 'classic', name: 'Classic', description: 'Warm paper, copper & sage', colors: ['#F7F5EF', '#252B27', '#B75C36', '#DBE3D5']}] as palette}
            <button class:selected={settings.palette === palette.id} aria-pressed={settings.palette === palette.id} onclick={() => { settings.palette = palette.id as Settings['palette']; void changeSettings(); }}>
              <span class="palette-swatches" aria-hidden="true">{#each palette.colors as color}<span style:background={color}></span>{/each}</span>
              <strong>{palette.name}{#if palette.id === 'violilt'}<small>DEFAULT</small>{/if}</strong><span class="palette-description">{palette.description}</span>{#if settings.palette === palette.id}<Check class="theme-check" size={16} />{/if}
            </button>
          {/each}
        </div><div class="appearance-label">APPEARANCE</div><div class="theme-choices">{#each [{ id: 'light', name: 'Daylight', description: 'Warm paper & quiet contrast', icon: Sun }, { id: 'dark', name: 'After hours', description: 'Soft light for late reading', icon: Moon }, { id: 'system', name: 'Follow your device', description: 'Changes with your system', icon: Monitor }] as theme}<button class:selected={settings.theme === theme.id} aria-pressed={settings.theme === theme.id} onclick={() => { settings.theme = theme.id as Settings['theme']; void changeSettings(); }}><theme.icon size={23} strokeWidth={1.4} /><strong>{theme.name}</strong><span>{theme.description}</span>{#if settings.theme === theme.id}<Check class="theme-check" size={16} />{/if}</button>{/each}</div></section>
        <section class="settings-card storage-card"><div class="settings-title"><FolderOpen size={22} strokeWidth={1.4} /><div><h2>A home for your recordings</h2><p>Documents, settings, and audio are saved locally.</p></div></div><code>{appState?.storage}</code><p class="settings-hint">Imported files stay untouched. Use Export to save a recording wherever you want.</p></section>
      </main>
    {/if}

    <footer class:has-audio={!!selectedJob} class="player-bar">
      <div class="player-track"><div class="track-icon"><AudioLines size={23} strokeWidth={1.5} /></div><div><strong>{selectedJob?.title || 'Your next listen is waiting.'}</strong><span>{selectedJob ? `${voiceDetails[selectedJob.voice]?.name || selectedJob.voice} · ${selectedJob.preview ? 'Voice preview' : buffering ? 'Waiting for the next words…' : streaming && selectedJob.state !== 'completed' ? `${formatTime(ahead)} buffered ahead` : 'Your recording'}` : 'Choose a voice. Bring your words to life.'}</span>{#if selectedJob?.unread_count}<span title={`${appState?.storage}/jobs/${selectedJob.id}/unread.txt`}>{selectedJob.unread_count} symbol{selectedJob.unread_count === 1 ? '' : 's'} omitted from speech · unread.txt</span>{/if}</div></div>
      <div class="player-center"><div class="player-buttons"><button title="Back 10 seconds" disabled={!selectedJob} onclick={() => seek(position - 10)}><SkipBack size={16} fill="currentColor" /></button><button class="play-button" title={playing || wanted ? 'Pause' : 'Play'} data-buffering={buffering} disabled={!selectedJob} onclick={togglePlay}>{#if buffering}<LoaderCircle size={18} class="spin" />{:else if playing}<Pause size={18} fill="currentColor" />{:else}<Play size={18} fill="currentColor" />{/if}</button><button title="Forward 10 seconds" disabled={!selectedJob} onclick={() => seek(position + 10)}><SkipForward size={16} fill="currentColor" /></button></div><div class="player-timeline"><span>{formatTime(position)}</span><input aria-label="Seek audio" type="range" min="0" max={duration || 1} step="0.1" value={position} oninput={(e) => seek(Number(e.currentTarget.value))} disabled={!selectedJob} /><span>{selectedJob ? formatTime(duration) : '-:-'}</span></div></div>
      <div class="player-extra"><button class="playback-rate" disabled={!selectedJob} title="Playback speed" onclick={changePlayback}>{playbackSpeed}×</button><Volume2 size={17} /><input type="range" aria-label="Volume" min="0" max="1" step="0.05" bind:value={volume} oninput={changeVolume} /><button class="export-button" disabled={!selectedJob || selectedJob.state !== 'completed'} onclick={() => exportAudio()} title="Export recording"><Download size={18} /></button></div>
    </footer>
    <audio bind:this={audio} preload="metadata" src={selectedJob && !streaming ? `/media/${selectedJob.id}.wav` : undefined} onloadedmetadata={loadedAudio} ontimeupdate={timeUpdate} onplay={() => { if (!streaming) playing = true; }} onpause={() => { if (!streaming) { playing = false; if (selectedJob) void api.save_position(selectedJob.id, position); } }} onended={() => { if (!streaming) playing = false; }} onerror={() => { if (selectedJob && !streaming) error = 'This recording could not be opened. Check that its audio file is still available.'; }}></audio>
  </div>
  {#if toast}<div class="toast" role="status"><Check size={17} />{toast}<button title="Dismiss notification" onclick={() => toast = ''}><X size={15} /></button></div>{/if}
  <dialog bind:this={helpDialog} class="about-modal" aria-labelledby="about-title" onclose={() => help = false} oncancel={() => help = false}><button class="modal-close" title="Close" onclick={() => help = false}><X size={20} /></button><img class="about-brand" src={brandIcon} alt="Violilt" /><span class="eyebrow">YOUR WORDS, OUT LOUD</span><h2 id="about-title">A little less rushing.<br /><em>A little more listening.</em></h2><p>Violilt is your local reading room. Bring Markdown, TXT or PDF, find a voice, and take your words with you.</p><div class="keyboard-list"><span>Import document <kbd>Ctrl O</kbd></span><span>Save working copy <kbd>Ctrl S</kbd></span><span>Find in document <kbd>Ctrl F</kbd></span><span>Play / pause <kbd>Space</kbd></span></div><p class="about-note">Narration processes your documents on this device. Microsoft's WebView2 runtime also handles security and diagnostic information.</p><button class="secondary-button" onclick={openWelcome}>Welcome &amp; quick guide</button><button class="secondary-button" onclick={() => microsoftNotice = true}>Microsoft services &amp; privacy</button></dialog>

  <Welcome bind:open={welcome} {api} model={appState?.model} {preview} disabled={!!active || testing}
    setupPending={modelSetupPending} setupError={modelSetupError} saving={welcomeSaving} error={welcomeError}
    setup={setupVoices} finish={finishWelcome} />
  <MicrosoftNotice bind:open={microsoftNotice} {api} />
  {#if fileMenu}
    {#key fileMenu}<FileContextMenu menu={fileMenu} canDelete={!busy && (fileMenu.item.kind === 'document' || ['completed', 'cancelled', 'failed', 'interrupted'].includes(fileMenu.item.state || ''))} close={() => fileMenu = null} remove={requestFileRemoval} reveal={revealFile} />{/key}
  {/if}

  <dialog bind:this={closeDialog} class="about-modal removal-modal" aria-labelledby="save-close-title" oncancel={(event) => { event.preventDefault(); keepEditing(); }}>
    <h2 id="save-close-title">Save before closing</h2>
    {#if closeError}<p role="alert">{closeError}</p>
    {:else}<p role="status"><LoaderCircle size={16} class="spin" /> Saving your changes before closing…</p>{/if}
    <div class="settings-actions">
      <button class="secondary-button" onclick={keepEditing}>Keep editing</button>
      {#if closeError}<button class="primary-button" onclick={saveBeforeClose}>Retry save and close</button>{/if}
    </div>
  </dialog>

  <dialog bind:this={removalDialog} class="about-modal removal-modal" aria-labelledby="removal-title" onclose={() => removal = null} oncancel={() => removal = null}>
    {#if removal}
      <button class="modal-close" title="Close" onclick={() => removal = null}><X size={20} /></button>
      <span class="eyebrow">MAKE ROOM ON YOUR SHELF</span>
      <h2 id="removal-title">Remove this {removal.kind === 'document' ? 'reading' : 'recording'}?</h2>
      <p><strong>{removal.title}</strong></p>
      <p>{removal.kind === 'document' ? 'This removes the working copy from Violilt. Your original file and existing recordings stay where they are.' : 'Remove this recording from the library. Its saved audio stays on disk unless you choose to delete it below.'}</p>
      {#if removal.kind === 'recording'}<label class="delete-audio"><input type="checkbox" bind:checked={deleteAudio} /> Also delete the saved audio files</label>{/if}
      <div class="settings-actions"><button class="secondary-button" onclick={() => removal = null}>Keep it</button><button class="primary-button" disabled={busy} onclick={confirmRemoval}><Trash2 size={16} /> Remove</button></div>
    {/if}
  </dialog>
</div>

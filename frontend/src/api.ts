export type Settings = { palette: 'lilt' | 'classic'; theme: 'light' | 'dark' | 'system'; voice: string; speed: number; include_code: boolean; heading_pause: number; paragraph_pause: number; performance_mode: 'quiet' | 'balanced' | 'fast' | 'custom'; cpu_threads: number; processing_device: 'auto' | 'cpu' | 'gpu'; gpu_device: number; buffer_mode: 'sooner' | 'balanced' | 'smooth'; auto_listen: boolean; warm_start: boolean; cache_enabled: boolean; cache_limit_mb: number };
export const defaultSettings: Settings = { palette: 'lilt', theme: 'light', voice: 'af_heart', speed: 1, include_code: false, heading_pause: 0.6, paragraph_pause: 0.3, performance_mode: 'balanced', cpu_threads: 0, processing_device: 'auto', gpu_device: -1, buffer_mode: 'balanced', auto_listen: true, warm_start: false, cache_enabled: true, cache_limit_mb: 256 };
export type Configuration = { provider: string; label: string; threads: number; device_id: number; mode?: string };
export type Measurement = Configuration & { throughput?: number; processing_seconds?: number; audio_seconds?: number; error?: string };
export type Performance = { logical_processors: number; physical_cores: number; adapters: { id: number; name: string; memory_mb: number }[]; gpu_ready: boolean; gpu_message: string; configuration: Configuration; cpu_percent: number | null; benchmark: { state: string; completed: number; total: number; message: string; results: Measurement[] }; warmup: { state: string; message: string }; recommendation: { cpu: Measurement; best: Measurement; results: Measurement[] } | null };
export type Cache = { count: number; bytes: number; limit_mb: number };
export type Section = { index: number; start: number; duration: number; pause: number };
export type Stream = { id: string; state: string; sections: Section[]; available: number; total: number; complete: boolean; running: boolean; throughput: number };
export type Document = { id: string; title: string; markdown: string; created: number; opened?: number | null; source?: string };
export type DocumentSummary = Omit<Document, 'markdown'> & { words?: number };
export type Job = { id: string; title: string; document_id: string; voice: string; speed: number; words: number; preview: boolean; state: string; completed: number; total: number; duration: number; position: number; message: string; created: number; last_listened?: number; available_duration?: number; engine?: Configuration; throughput?: number; cache_hits?: number; first_audio_seconds?: number; can_resume?: boolean; resume_message?: string; pronunciation_warnings?: string[]; unread_count?: number };
export type Prepared = { title: string; text: string; words: number; chunks: { text: string; pause: number; block: number }[]; omissions: { code_blocks: number; metadata: number }; unread_count?: number };
export type Model = { state: string; percent: number; message: string; voices: string[] };
export type State = { documents: DocumentSummary[]; jobs: Job[]; active: Job | null; model: Model; settings: Settings; storage: string; performance: Performance | null; cache: Cache };
export type API = {
  get_state(): Promise<State>;
  get_stream(id: string): Promise<Stream>;
  start_benchmark(): Promise<boolean>;
  stop_benchmark(): Promise<boolean>;
  warm_engine(): Promise<boolean>;
  clear_cache(): Promise<boolean>;
  get_document(id: string): Promise<Document>;
  save_document(id: string, text: string): Promise<Document>;
  new_document(): Promise<Document>;
  remove_document(id: string): Promise<boolean>;
  remove_recording(id: string, deleteAudio: boolean): Promise<boolean>;
  import_document(): Promise<Document | null>;
  prepare_document(text: string, options: Settings): Promise<Prepared>;
  save_settings(settings: Settings): Promise<Settings>;
  generate(id: string, text: string, settings: Settings): Promise<Job>;
  preview_voice(voice: string, speed: number): Promise<Job>;
  cancel_generation(): Promise<boolean>;
  resume_job(id: string): Promise<Job>;
  save_position(id: string, position: number): Promise<boolean>;
  export_recording(id: string): Promise<string | null>;
  setup_model(): Promise<Model>;
  import_model(): Promise<Model | null>;
};

declare global { interface Window { pywebview?: { api: API } } }

export const sampleText = `# The art of paying attention

There is a small kind of freedom in choosing what gets your attention. Not every notification deserves an answer. Not every quiet moment needs to be filled.

We spend so much time collecting things to read that we sometimes forget the pleasure of actually reading them. A saved article. A page of notes. A thought that felt important enough to write down.

## A different pace

Listening gives those words a little more room. You can take them on a walk, make a cup of coffee, or simply close your eyes. The text stays the same. Your relationship with it changes.

> Attention is not something we find. It is something we make room for.

There is no perfect way to begin. Start with a paragraph that makes you curious. Choose a voice that feels comfortable. Let the next sentence arrive when it is ready.

## Keep what matters

- A little less rushing.
- A little more noticing.
- A place for the words you want to return to.

This is a sample document for your first listen. Replace it with your own Markdown file whenever you are ready.
`;

export async function getAPI(): Promise<{ api: API; preview: boolean }> {
  const previewMode = import.meta.env.DEV || new URLSearchParams(window.location.search).get('preview') === '1';
  if (!previewMode) {
    for (let i = 0; i < 120; i++) {
      const api = window.pywebview?.api;
      if (typeof api?.get_state === 'function' && typeof api?.save_settings === 'function' && typeof api?.generate === 'function') return { api, preview: false };
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw new Error('Lilt could not connect to its desktop service. Retry, or close and reopen Lilt. Your readings and recordings remain saved.');
  }
  // Only used for frontend development and visual verification. No simulated speech.
  let doc: Document = { id: 'preview-document', title: 'The art of paying attention', markdown: sampleText, created: Date.now() / 1000 };
  let settings: Settings = { ...defaultSettings };
  const unavailable = async (): Promise<never> => { throw new Error('Open the desktop app to use local speech and file dialogs.'); };
  const api: API = {
    get_state: async () => ({ documents: [doc], jobs: [], active: null, model: { state: 'missing', percent: 0, message: 'Open the desktop app to set up your voice engine.', voices: [] }, settings, storage: 'Desktop app storage', performance: null, cache: {count: 0, bytes: 0, limit_mb: 256} }),
    get_stream: unavailable, start_benchmark: unavailable, stop_benchmark: unavailable, warm_engine: unavailable, clear_cache: unavailable,
    get_document: async () => doc,
    save_document: async (_id, text) => (doc = { ...doc, markdown: text, title: text.match(/^#\s+(.+)$/m)?.[1] || 'Untitled reading' }),
    new_document: async () => (doc = { ...doc, markdown: '# Untitled reading\n\nPut your words here.', title: 'Untitled reading' }),
    remove_document: unavailable, remove_recording: unavailable,
    import_document: unavailable,
    prepare_document: async (text) => ({ title: doc.title, text: text.replace(/^#+\s*/gm, '').replace(/[>*]/g, ''), words: text.split(/\s+/).filter(Boolean).length, chunks: [], omissions: { code_blocks: 0, metadata: 0 } }),
    save_settings: async value => (settings = value),
    generate: unavailable, preview_voice: unavailable, cancel_generation: unavailable, resume_job: unavailable,
    save_position: async () => true, export_recording: unavailable, setup_model: unavailable, import_model: unavailable,
  };
  return { api, preview: true };
}

export async function withTimeout<T>(operation: Promise<T>, milliseconds = 10000): Promise<T> {
  let timer: ReturnType<typeof setTimeout>;
  try {
    return await Promise.race([operation, new Promise<never>((_resolve, reject) => {
      timer = setTimeout(() => reject(new Error('Your library is taking too long to respond. Retry, or close and reopen Lilt. Your saved files are kept.')), milliseconds);
    })]);
  } finally { clearTimeout(timer!); }
}

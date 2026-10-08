import type { Settings, Stream } from './api';

let context: AudioContext | undefined;
export function primeAudio() {
  context ||= new AudioContext();
  void context.resume();
}
export type PlayerState = { position: number; duration: number; playing: boolean; waiting: boolean; ahead: number; wanted: boolean };

/** A bounded, evolving timeline. Exported WAV and streamed speech share offsets. */
export class StreamPlayer {
  private ctx: AudioContext;
  private gain: GainNode;
  private data: Stream;
  private buffers = new Map<number, AudioBuffer>();
  private loading = new Set<number>();
  private nodes = new Map<number, AudioBufferSourceNode>();
  private request = new AbortController();
  private timer: ReturnType<typeof setInterval>;
  private pos = 0;
  private anchorPos = 0;
  private anchorTime = 0;
  private end = 0;
  private rate = 1;
  private running = false;
  private wanted = false;
  private manual = false;
  private dead = false;
  private failed = false;
  private initialized = false;
  private mode: Settings['buffer_mode'] = 'balanced';

  constructor(id: string, position: number, private change: (state: PlayerState) => void, private error: (message: string) => void) {
    primeAudio();
    this.ctx = context!;
    this.gain = this.ctx.createGain();
    this.gain.connect(this.ctx.destination);
    this.data = { id, sections: [], available: 0, total: 0, state: 'preparing', running: true, complete: false, throughput: 0 };
    this.pos = Math.max(0, position);
    this.timer = setInterval(() => this.tick(), 80);
  }

  update(data: Stream) { if (this.dead || data.id !== this.data.id) return; this.data = data; this.initialized = true; this.prefetch(); this.tick(); }
  preferences(mode: Settings['buffer_mode'], rate: number, volume: number) {
    this.mode = mode;
    this.gain.gain.value = volume;
    if (rate !== this.rate) { this.hold(); this.rate = rate; }
    this.tick();
  }
  play(automatic = false) {
    this.failed = false;
    if (!this.data.running && this.pos >= this.data.available - 0.02) this.pos = 0;
    this.wanted = true; this.manual = !automatic;
    void this.ctx.resume().then(() => this.tick()).catch(() => this.error('Press play to allow audio.'));
    this.tick();
  }
  pause() { this.hold(); this.wanted = false; this.tick(); }
  seek(value: number) { this.hold(); this.pos = Math.max(0, Math.min(value, this.data.available)); this.prefetch(); this.tick(); }
  dispose() { this.hold(); this.wanted = false; this.dead = true; clearInterval(this.timer); this.request.abort(); this.gain.disconnect(); this.buffers.clear(); }

  private clock() { return this.running ? Math.min(this.end, this.anchorPos + Math.max(0, this.ctx.currentTime - this.anchorTime) * this.rate) : this.pos; }
  private hold() {
    this.pos = this.clock(); this.running = false;
    for (const node of this.nodes.values()) { node.onended = null; try { node.stop(); } catch { /* already ended */ } node.disconnect(); }
    this.nodes.clear();
  }
  private decodedEnd() {
    let end = this.pos;
    for (const section of this.data.sections) {
      if (section.start + section.duration + section.pause <= this.pos + 0.001) continue;
      if (!this.buffers.has(section.index)) break;
      end = section.start + section.duration + section.pause;
      if (end > this.pos + 60) break;
    }
    return end;
  }
  private prefetch() {
    if (this.dead || this.failed || !this.initialized) return;
    const pos = this.clock();
    for (const [index] of this.buffers) {
      const section = this.data.sections[index];
      if (section && (section.start + section.duration + section.pause < pos - 5 || section.start > pos + 90)) this.buffers.delete(index);
    }
    const candidates = this.data.sections.filter(section => section.start + section.duration + section.pause > pos && section.start < pos + 60);
    for (const section of candidates) {
      if (this.loading.size >= 3) break;
      if (this.buffers.has(section.index) || this.loading.has(section.index)) continue;
      this.loading.add(section.index);
      void fetch(`/media/${this.data.id}/section-${String(section.index).padStart(6, '0')}.wav`, { signal: this.request.signal })
        .then(response => { if (!response.ok) throw new Error('A saved audio section could not be opened.'); return response.arrayBuffer(); })
        .then(bytes => this.ctx.decodeAudioData(bytes))
        .then(buffer => { if (!this.dead) this.buffers.set(section.index, buffer); })
        .catch(e => { if (!this.dead) { this.failed = true; this.wanted = false; this.hold(); this.error(String(e)); } })
        .finally(() => { this.loading.delete(section.index); if (!this.dead) { this.prefetch(); this.tick(); } });
    }
  }
  private schedule(end: number) {
    for (const section of this.data.sections) {
      const buffer = this.buffers.get(section.index);
      if (!buffer || this.nodes.has(section.index) || section.start >= end || section.start + section.duration <= this.pos) continue;
      const offset = Math.max(0, this.anchorPos - section.start);
      const at = this.anchorTime + Math.max(0, section.start - this.anchorPos) / this.rate;
      // An underrun freezes the timeline before restarting; never skip late speech.
      if (at < this.ctx.currentTime - 0.1) continue;
      const node = this.ctx.createBufferSource();
      node.buffer = buffer; node.playbackRate.value = this.rate; node.connect(this.gain);
      this.nodes.set(section.index, node);
      node.onended = () => { this.nodes.delete(section.index); node.disconnect(); };
      node.start(Math.max(at, this.ctx.currentTime), offset);
    }
    this.end = end;
  }
  private tick() {
    if (this.dead || !this.initialized) return;
    this.pos = this.clock();
    if (this.running && this.pos >= this.end - 0.003) this.hold();
    const end = this.decodedEnd();
    if (this.wanted && this.ctx.state === 'running') {
      if (this.running) this.schedule(end);
      else {
        const target = this.manual ? 0.02 : this.mode === 'sooner' ? 1 : this.mode === 'smooth' ? 24 : this.data.throughput >= this.rate * 1.2 ? 4 : 10;
        if (end - this.pos >= target || (!this.data.running && end > this.pos + 0.01)) {
          this.running = true; this.anchorPos = this.pos; this.anchorTime = this.ctx.currentTime + 0.04;
          this.schedule(end);
        } else if (!this.data.running && this.pos >= this.data.available - 0.02) this.wanted = false;
      }
    }
    this.prefetch();
    this.change({ position: this.pos, duration: this.data.available, playing: this.running,
                  waiting: this.wanted && !this.running, ahead: Math.max(0, end - this.pos), wanted: this.wanted });
  }
}

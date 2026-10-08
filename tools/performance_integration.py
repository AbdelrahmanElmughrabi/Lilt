"""Real CPU/GPU generation, early media, caching, timeline, and benchmark checks."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.documents import prepare
from backend.jobs import Jobs
from backend.models import Models
from backend.storage import Store


def wait_job(jobs, key, early=None):
    deadline = time.monotonic() + 180
    first = None
    while time.monotonic() < deadline:
        job = jobs.store.get('jobs', key)
        if job['completed'] and first is None:
            first = time.monotonic()
            data = jobs.stream(key)
            assert data['available'] > 0 and len(data['sections']) > 0
            if early:
                early(job)
        if job['state'] in {'failed', 'cancelled'}:
            raise RuntimeError(job['message'])
        if job['state'] == 'completed':
            while jobs.state():
                time.sleep(.01)
            return job
        time.sleep(.04)
    raise RuntimeError('Generation timeout')


def verify_audio(jobs, job):
    import numpy as np
    import soundfile as sf
    folder = jobs.store.root / 'jobs' / job['id']
    complete, rate = sf.read(folder / 'recording.wav', dtype='int16')
    offset = 0
    for section in jobs.stream(job['id'])['sections']:
        raw, _ = sf.read(folder / f"section-{section['index']:06d}.wav", dtype='int16')
        assert abs(offset / rate - section['start']) < 1 / rate
        assert np.array_equal(raw, complete[offset:offset+len(raw)])
        offset += len(raw)
        pause = round(section['pause'] * rate)
        assert not np.any(complete[offset:offset+pause])
        offset += pause
    assert offset == len(complete)


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    store = Store(root / 'artifacts' / ('performance-test-' + str(int(time.time()))))
    jobs = Jobs(store, Models(root / '.app-data' / 'models'))
    evidence = {}
    try:
        store.save_settings({'processing_device': 'gpu', 'performance_mode': 'balanced', 'cache_enabled': True})
        markdown = '# A room for listening\n\n' + '\n\n'.join(f'Passage {i+1}. A long reading begins with a little room for curiosity. Listen to the first words while the next thought is prepared. Let each sentence arrive at its own pace.' for i in range(8))
        doc = store.document(markdown, 'A room for listening')
        prepared = prepare(markdown)
        observed = []
        started = time.monotonic()
        first = jobs.start(prepared, doc, 'af_heart', 1)
        first = wait_job(jobs, first['id'], lambda job: observed.append(job['state'] not in {'completed', 'assembling'}))
        assert any(observed), 'No early audio was observed'
        verify_audio(jobs, first)
        evidence['gpu'] = {key: first.get(key) for key in ['engine', 'first_audio_seconds', 'duration', 'processing_seconds', 'throughput', 'cache_hits']}
        print('GPU generation and exact streamed/exported samples passed', flush=True)
        cached = jobs.start(prepared, doc, 'af_heart', 1)
        cached = wait_job(jobs, cached['id'])
        assert cached['cache_hits'] == cached['total'] and cached['generated_sections'] == 0, cached
        verify_audio(jobs, cached)
        evidence['cached'] = {'hits': cached['cache_hits'], 'sections': cached['total'], 'seconds': cached['processing_seconds']}
        edited = markdown.replace('Passage 4.', 'An edited passage.')
        third = jobs.start(prepare(edited), doc | {'markdown': edited}, 'af_heart', 1)
        third = wait_job(jobs, third['id'])
        assert third['cache_hits'] >= third['total'] - 2 and third['generated_sections'] > 0
        evidence['edited'] = {'hits': third['cache_hits'], 'sections': third['total'], 'generated': third['generated_sections']}
        store.save_settings({'processing_device': 'cpu', 'performance_mode': 'quiet', 'cache_enabled': False})
        cpu = jobs.start(prepare('A short CPU reading uses one thread and leaves more room for other applications.'), doc, 'af_heart', 1)
        cpu = wait_job(jobs, cpu['id'])
        assert cpu['engine']['threads'] == 1 and cpu['engine']['background']
        verify_audio(jobs, cpu)
        evidence['quiet_cpu'] = {'engine': cpu['engine'], 'throughput': cpu['throughput']}
        jobs.benchmark()
        jobs.stop_benchmark()
        while jobs.operation:
            time.sleep(.1)
        assert jobs.performance.benchmark['state'] == 'cancelled'
        assert jobs.performance.recommendation() is None
        jobs.benchmark()
        deadline = time.monotonic() + 180
        while jobs.operation and time.monotonic() < deadline:
            time.sleep(.2)
        assert jobs.performance.benchmark['state'] == 'completed', jobs.performance.benchmark
        result = jobs.performance.recommendation()
        assert result and result['best']['provider'] == 'CUDAExecutionProvider', result
        evidence['benchmark'] = result
        store.save_settings({'performance_mode': 'fast', 'processing_device': 'auto'})
        assert jobs.performance.resolve(store.settings())['provider'] == 'CUDAExecutionProvider'
        (root / 'artifacts' / 'performance-integration.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
        print(json.dumps({'success': True, 'gpu_throughput': first['throughput'], 'first_audio_seconds': first['first_audio_seconds'], 'cache_seconds': cached['processing_seconds'], 'benchmark_best': result['best']}), flush=True)
    finally:
        jobs.close()

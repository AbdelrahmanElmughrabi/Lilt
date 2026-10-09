"""Real synthesis + cancel/resume integration check (uses already-downloaded assets)."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.documents import prepare
from backend.jobs import Jobs
from backend.models import Models
from backend.storage import Store


def await_job(store, key, limit=150):
    start, previous = time.monotonic(), None
    while time.monotonic() - start < limit:
        job = store.get('jobs', key)
        marker = (job['state'], job['completed'])
        if marker != previous:
            print(job['message'], flush=True)
            previous = marker
        if job['state'] in {'completed', 'failed', 'cancelled'}:
            return job
        time.sleep(.25)
    raise RuntimeError('Synthesis did not complete within the test limit')


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    store = Store(root / 'artifacts' / 'smoke-data')
    models = Models(root / '.app-data' / 'models')
    jobs = Jobs(store, models)
    try:
        markdown = '# A first listen\n\nLilt turns your words into a place you can return to.\n\nTake a breath. Make a little room for listening.\n\nEvery section is saved, so a long reading can continue where it stopped.'
        prepared = prepare(markdown)
        doc = store.document(markdown, prepared['title'])
        started = time.monotonic()
        job = jobs.start(prepared, doc, 'af_heart', 1.0)
        # Cancel after a completed section, then resume the same immutable job.
        while store.get('jobs', job['id'])['completed'] < 1:
            if time.monotonic() - started > 90:
                raise RuntimeError('First section did not finish')
            current = store.get('jobs', job['id'])
            if current['state'] == 'failed':
                raise RuntimeError(current['message'])
            time.sleep(.1)
        jobs.stop()
        cancelled = await_job(store, job['id'])
        assert cancelled['state'] == 'cancelled', cancelled
        first = store.root / 'jobs' / job['id'] / 'section-000000.wav'
        original_mtime = first.stat().st_mtime_ns
        # Listener clears active immediately after persisting the terminal state.
        while jobs.state():
            time.sleep(.05)
        jobs.start(prepared, doc, 'af_heart', 1.0, resume=job['id'])
        finished = await_job(store, job['id'])
        assert finished['state'] == 'completed', finished
        assert first.stat().st_mtime_ns == original_mtime, 'Resume regenerated a saved section'
        import soundfile as sf
        audio = store.root / 'jobs' / job['id'] / 'recording.wav'
        info = sf.info(audio)
        assert info.frames > 24000 and info.channels == 1 and info.samplerate == 24000
        print(json.dumps({'success': True, 'audio_seconds': round(info.duration, 2),
                          'elapsed_seconds': round(time.monotonic() - started, 2),
                          'sections': len(prepared['chunks']), 'output': str(audio)}), flush=True)
    finally:
        jobs.close()

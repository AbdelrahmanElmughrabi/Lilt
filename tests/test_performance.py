import os
import hashlib
import json
import tempfile
import time
import unittest
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import soundfile as sf

from backend.cache import SectionCache, section_key
from backend.documents import prepare
from backend.jobs import Jobs
from backend.models import FILES
from backend.performance import validate
from backend.sections import listening_chunks, published_sections
from backend.server import AppServer
from backend.storage import Store


class PerformanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_settings_have_real_bounds_and_types(self):
        for value in [True, -1, 0.5, (os.cpu_count() or 1) + 1, 'four']:
            with self.assertRaises(ValueError):
                validate({'cpu_threads': value})
        for settings in [{'performance_mode': 'turbo'}, {'buffer_mode': 'never'}, {'warm_start': 1}, {'cache_limit_mb': 1000}]:
            with self.assertRaises(ValueError):
                validate(settings)
        validate({'cpu_threads': 0, 'processing_device': 'auto', 'warm_start': True})

    def test_performance_preferences_do_not_change_spoken_snapshot(self):
        markdown = '# Read me\n\nA paragraph worth reading.'
        first = prepare(markdown, {'performance_mode': 'quiet', 'cpu_threads': 1})
        second = prepare(markdown, {'performance_mode': 'fast', 'cpu_threads': 4})
        self.assertEqual(first, second)

    def test_short_opening_preserves_every_word_and_final_pause(self):
        chunks = prepare(' '.join(f'word{i}' for i in range(300)))['chunks']
        shortened = listening_chunks(chunks)
        self.assertEqual(' '.join(item['text'] for item in chunks), ' '.join(item['text'] for item in shortened))
        self.assertLessEqual(len(shortened[0]['text']), 180)
        self.assertEqual(shortened[-1]['pause'], chunks[-1]['pause'])

    def test_cache_identity_changes_with_speech_inputs(self):
        original = section_key('hello', 'af_heart', 1, ['model-v1'])
        for text, voice, speed, identity in [('bye', 'af_heart', 1, ['model-v1']), ('hello', 'bf_emma', 1, ['model-v1']), ('hello', 'af_heart', 1.2, ['model-v1']), ('hello', 'af_heart', 1, ['model-v2'])]:
            self.assertNotEqual(original, section_key(text, voice, speed, identity))

    def test_cache_evicts_oldest_and_clear_retains_recording(self):
        source = self.root / 'recording.wav'
        sf.write(source, np.zeros(2400), 24000, subtype='PCM_16')
        cache = SectionCache(self.root / 'cache')
        cache.limit = source.stat().st_size + 10
        first, second = 'a' * 64, 'b' * 64
        cache.put(first, source)
        old = cache.root / (first + '.wav')
        os.utime(old, (1, 1))
        cache.put(second, source)
        self.assertFalse(old.exists())
        self.assertTrue(cache.fetch(second, self.root / 'copy.wav'))
        cache.clear()
        self.assertTrue(source.exists())
        self.assertTrue((self.root / 'copy.wav').exists())

    def test_timeline_uses_exact_samples_and_stops_at_gap(self):
        chunks = [{'text': 'one', 'pause': 0.3333333}, {'text': 'two', 'pause': 0.6}, {'text': 'three', 'pause': 1}]
        sf.write(self.root / 'section-000000.wav', np.zeros(12345), 24000, subtype='PCM_16')
        sf.write(self.root / 'section-000002.wav', np.zeros(1000), 24000, subtype='PCM_16')
        sections, available = published_sections({'chunks': chunks}, self.root)
        self.assertEqual(len(sections), 1)
        self.assertAlmostEqual(available * 24000, 12345 + int(0.3333333 * 24000))

    def test_position_updates_keep_active_generation_progress(self):
        store = Store(self.root / 'data')
        jobs = Jobs(store, None)
        try:
            job = {'id': uuid.uuid4().hex, 'state': 'generating', 'completed': 3, 'total': 10, 'available_duration': 12, 'position': 0}
            store.put('jobs', job)
            jobs.active = job
            jobs.save_position(job['id'], 8)
            self.assertEqual(jobs.active['completed'], 3)
            self.assertEqual(jobs.active['position'], 8)
            jobs.active.update(completed=4, available_duration=16)
            store.put('jobs', jobs.active)
            self.assertEqual(store.get('jobs', job['id'])['position'], 8)
        finally:
            jobs.close()

    def test_continuation_never_unpublishes_saved_audio(self):
        store = Store(self.root / 'data')
        jobs = Jobs(store, None)
        try:
            sections = [{'index': i, 'start': i * 2, 'duration': 2, 'pause': 0} for i in range(3)]
            job = {'id': uuid.uuid4().hex, 'state': 'preparing', 'completed': 3, 'total': 5, 'sections': sections, 'available_duration': 6, 'position': 4}
            store.put('jobs', job)
            jobs.active = job
            jobs.events.put({'id': job['id'], 'state': 'generating', 'completed': 1, 'sections': sections[:1], 'available_duration': 2, 'message': 'checkpoint scanned'})
            deadline = time.monotonic() + 3
            while store.get('jobs', job['id']).get('message') != 'checkpoint scanned' and time.monotonic() < deadline:
                time.sleep(.01)
            result = store.get('jobs', job['id'])
            self.assertEqual(result['completed'], 3)
            self.assertEqual(result['available_duration'], 6)
            self.assertEqual(result['sections'], sections)
            self.assertEqual(result['position'], 4)
        finally:
            jobs.close()

    def test_shutdown_cannot_replace_interrupted_with_worker_failure(self):
        store = Store(self.root / 'data')
        jobs = Jobs(store, None)
        key = uuid.uuid4().hex
        job = {'id':key,'state':'generating','completed':2,'total':8,'position':1,'available_duration':5}
        store.put('jobs',job)
        jobs.active = job
        jobs.process = SimpleNamespace(is_alive=lambda:False)
        jobs.close()
        time.sleep(.6)
        self.assertEqual(store.get('jobs',key)['state'],'interrupted')

    def test_first_release_job_can_continue_more_than_once(self):
        store = Store(self.root / 'data')
        jobs = Jobs(store, None)
        model_folder = self.root / 'models'
        model_folder.mkdir()
        for name in FILES:
            (model_folder / name).write_bytes(b'unchanged fixture model')
        jobs.models = SimpleNamespace(root=model_folder, status=lambda: {'state':'ready', 'voices':['af_heart']})
        jobs.performance = SimpleNamespace(resolve=lambda _: {'model':str(model_folder / FILES[0]), 'provider':'CPUExecutionProvider'}, gpu_runtime=None, runtime='fixture')
        jobs._worker = lambda: None
        try:
            text = '# Legacy reading\n\nEvery word keeps its original place.'
            options = {'theme':'dark', 'voice':'af_heart', 'speed':1, 'include_code':False, 'heading_pause':.6, 'paragraph_pause':.3}
            prepared = prepare(text, options)
            doc = store.document(text, prepared['title'])
            old = {'text':prepared['text'], 'options':options, 'voice':'af_heart', 'speed':1.0,
                   'model':[(name,(model_folder / name).stat().st_size,(model_folder / name).stat().st_mtime_ns) for name in FILES]}
            job = {'id':uuid.uuid4().hex,'document_id':doc['id'],'title':doc['title'],'markdown':text,'voice':'af_heart','speed':1.0,'preview':False,
                   'chunks':prepared['chunks'],'options':options,'fingerprint':hashlib.sha256(json.dumps(old,sort_keys=True).encode()).hexdigest(),
                   'created':1,'state':'interrupted','completed':0,'total':len(prepared['chunks']),'position':0,'duration':0}
            store.put('jobs', job)
            for _ in range(2):
                resumed = jobs.start(prepared, doc, 'af_heart', 1, resume=job['id'])
                command = jobs.commands.get(timeout=2)
                self.assertEqual(command['job']['chunks'], prepared['chunks'])
                self.assertEqual(resumed['state'], 'preparing')
                jobs.active.update(state='interrupted')
                store.put('jobs', jobs.active)
                jobs.active = None
        finally:
            jobs.close()

    def test_server_only_exposes_published_sections_and_blocks_partial_export(self):
        store = Store(self.root / 'data')
        assets = self.root / 'assets'
        assets.mkdir()
        server = AppServer(assets, store)
        server.start()
        try:
            key = uuid.uuid4().hex
            folder = store.root / 'jobs' / key
            folder.mkdir()
            for name in ['section-000000.wav', 'section-000001.wav', 'recording.wav']:
                (folder / name).write_bytes(b'0123456789')
            store.put('jobs', {'id': key, 'state': 'generating', 'completed': 1, 'total': 2})
            with urllib.request.urlopen(urllib.request.Request(f'{server.url}/media/{key}/section-000000.wav', headers={'Range': 'bytes=2-5'})) as response:
                self.assertEqual(response.status, 206)
                self.assertEqual(response.read(), b'2345')
            for path in [f'/media/{key}.wav', f'/media/{key}/section-000001.wav', f'/media/{key}/section-000000.part']:
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(server.url + path)
                self.assertEqual(error.exception.code, 404)
        finally:
            server.close()

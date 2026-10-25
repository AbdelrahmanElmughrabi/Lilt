import os
import copy
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
from unittest.mock import Mock, patch

import numpy as np
from backend.pcm_audio import audio_info, write_pcm16

from backend.cache import SectionCache, section_key
from backend.documents import prepare
from backend.jobs import Jobs, public_job
from backend.models import FILES
from backend.performance import Performance, validate
from backend.sections import listening_chunks, published_sections
from backend.server import AppServer
from backend.storage import Store
from tests.test_pcm_audio import pcm


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
        write_pcm16(source, np.zeros(2400), 24000)
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

    def test_changed_pronunciation_invalidates_performance_recommendation(self):
        store = Store(self.root / 'data')
        model_folder = self.root / 'models'
        model_folder.mkdir()
        for name in FILES:
            (model_folder / name).write_bytes(b'unchanged fixture model')
        performance = Performance.__new__(Performance)
        performance.store, performance.models = store, SimpleNamespace(root=model_folder)
        performance.logical, performance.physical = 8, 4
        performance.adapters, performance.runtime, performance.gpu_runtime = [], 'fixture', None
        performance._identity, performance._pronunciation_identity = None, None
        with patch('backend.performance.pronunciation_identity', return_value={'engine': 'fixture', 'revision': 1}):
            original = performance.identity()
            result = {'identity': original, 'cpu': {'threads': 2}, 'best': {'provider': 'CPUExecutionProvider', 'threads': 2}}
            store.save_settings({'benchmark_result': result})
            self.assertEqual(performance.recommendation(), result)
        with patch('backend.performance.pronunciation_identity', return_value={'engine': 'fixture', 'revision': 2}):
            self.assertNotEqual(performance.identity(), original)
            self.assertIsNone(performance.recommendation())
        # Invalidating a recommendation must retain the old measurement record.
        self.assertEqual(store.settings()['benchmark_result'], result)

    def test_timeline_uses_exact_samples_and_stops_at_gap(self):
        chunks = [{'text': 'one', 'pause': 0.3333333}, {'text': 'two', 'pause': 0.6}, {'text': 'three', 'pause': 1}]
        write_pcm16(self.root / 'section-000000.wav', np.zeros(12345), 24000)
        write_pcm16(self.root / 'section-000002.wav', np.zeros(1000), 24000)
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

    def reading_fixture(self):
        store = Store(self.root / 'data')
        jobs = Jobs(store, None)
        model_folder = self.root / 'models'
        model_folder.mkdir()
        for name in FILES:
            (model_folder / name).write_bytes(b'unchanged fixture model')
        jobs.models = SimpleNamespace(root=model_folder, status=lambda: {'state':'ready', 'voices':['af_heart']})
        jobs.performance = SimpleNamespace(resolve=Mock(return_value={'model':str(model_folder / FILES[0]), 'provider':'CPUExecutionProvider'}), gpu_runtime=None, runtime='fixture')
        jobs._worker = Mock()
        text = '# Saved reading\n\n' + ' '.join(f'word{i}' for i in range(70)) + '.\n\nEvery word keeps its original place.'
        prepared = prepare(text)
        doc = store.document(text, prepared['title'])
        return store, jobs, doc, prepared

    def interrupted_fixture(self, store, jobs, doc, prepared):
        jobs.start(prepared, doc, 'af_heart', 1)
        command = jobs.commands.get(timeout=2)
        job = copy.deepcopy(command['job'])
        directory = store.root / 'jobs' / job['id']
        directory.mkdir()
        audio = directory / 'section-000000.wav'
        write_pcm16(audio, np.zeros(2400), 24000)
        job['sections'], job['available_duration'] = published_sections(job, directory)
        job.update(state='interrupted', completed=len(job['sections']), position=.05)
        store.put('jobs', job)
        jobs.active = None
        jobs._worker.reset_mock()
        jobs.performance.resolve.reset_mock()
        return job, audio

    def test_legacy_jobs_are_not_promoted_or_modified_during_resume(self):
        store, jobs, doc, prepared = self.reading_fixture()
        try:
            job, audio = self.interrupted_fixture(store, jobs, doc, prepared)
            job.pop('pronunciation_identity')
            original_audio_identity = job.pop('audio_identity')
            old = {'text':prepared['text'], 'options':prepared['options'], 'voice':'af_heart', 'speed':1.0,
                   'model':[(name,(jobs.models.root / name).stat().st_size,(jobs.models.root / name).stat().st_mtime_ns) for name in FILES]}
            job['fingerprint'] = hashlib.sha256(json.dumps(old, sort_keys=True).encode()).hexdigest()
            for identity in (None, original_audio_identity):
                with self.subTest(legacy_identity=identity):
                    if identity is not None:
                        job['audio_identity'] = identity
                    store.put('jobs', job)
                    before, audio_before = store.get('jobs', job['id']), audio.read_bytes()
                    with self.assertRaisesRegex(ValueError, 'different pronunciation engine'):
                        jobs.start(prepared, doc, 'af_heart', 1, resume=job['id'])
                    self.assertEqual(store.get('jobs', job['id']), before)
                    self.assertEqual(audio.read_bytes(), audio_before)
                    self.assertEqual(jobs.stream(job['id'])['sections'], job['sections'])
                    self.assertFalse(public_job(job)['can_resume'])
                    jobs._worker.assert_not_called()
                    jobs.performance.resolve.assert_not_called()
                    self.assertIsNone(jobs.active)
        finally:
            jobs.close()

    def test_changed_pronunciation_rejects_resume_and_separates_cache(self):
        store, jobs, doc, prepared = self.reading_fixture()
        try:
            job, audio = self.interrupted_fixture(store, jobs, doc, prepared)
            before, audio_before = store.get('jobs', job['id']), audio.read_bytes()
            next_pronunciation = job['pronunciation_identity'] | {'revision': 'a-new-integration'}
            old_key = section_key(job['chunks'][0]['text'], job['voice'], job['speed'], job['audio_identity'])
            jobs.cache.put(old_key, audio)
            with patch('backend.jobs.pronunciation_identity', return_value=next_pronunciation):
                with self.assertRaisesRegex(ValueError, 'different pronunciation engine'):
                    jobs.start(prepared, doc, 'af_heart', 1, resume=job['id'])
                changed_identity = jobs._audio_identity(FILES[0])
                changed_key = section_key(job['chunks'][0]['text'], job['voice'], job['speed'], changed_identity)
                self.assertNotEqual(changed_key, old_key)
                self.assertFalse(jobs.cache.fetch(changed_key, self.root / 'incompatible.wav'))
                self.assertFalse(public_job(job)['can_resume'])
            self.assertEqual(jobs._audio_identity(FILES[0]), job['audio_identity'])
            self.assertEqual(store.get('jobs', job['id']), before)
            self.assertEqual(audio.read_bytes(), audio_before)
            self.assertTrue((jobs.cache.root / (old_key + '.wav')).exists())
            jobs._worker.assert_not_called()
            jobs.performance.resolve.assert_not_called()
        finally:
            jobs.close()

    def test_compatible_job_continues_twice_with_immutable_snapshot_and_timeline(self):
        store, jobs, doc, prepared = self.reading_fixture()
        try:
            job, audio = self.interrupted_fixture(store, jobs, doc, prepared)
            audio_before = audio.read_bytes()
            snapshot = {field: copy.deepcopy(job[field]) for field in
                        ('chunks', 'options', 'markdown', 'pronunciation_identity', 'audio_identity', 'sections', 'available_duration', 'position')}
            # New chunking policies must not replace the persisted section layout.
            prepared['chunks'].reverse()
            for _ in range(2):
                resumed = jobs.start(prepared, doc, 'af_heart', 1, resume=job['id'])
                command = jobs.commands.get(timeout=2)
                for field, expected in snapshot.items():
                    self.assertEqual(command['job'][field], expected)
                self.assertEqual(resumed['state'], 'preparing')
                self.assertTrue(public_job(job)['can_resume'])
                self.assertEqual(audio.read_bytes(), audio_before)
                jobs.active.update(state='interrupted')
                store.put('jobs', jobs.active)
                jobs.active = None
        finally:
            jobs.close()

    def test_public_resume_status_keeps_completed_recordings_and_warning_metadata(self):
        completed = {'id': uuid.uuid4().hex, 'state': 'completed', 'pronunciation_warnings': ['Unfamiliar name spelled out.']}
        before = copy.deepcopy(completed)
        result = public_job(completed)
        self.assertFalse(result['can_resume'])
        self.assertEqual(result['resume_message'], '')
        self.assertEqual(result['pronunciation_warnings'], completed['pronunciation_warnings'])
        self.assertEqual(completed, before)
        legacy = completed | {'state': 'interrupted'}
        self.assertIn('saved audio is kept', public_job(legacy)['resume_message'])

    def test_new_job_snapshot_does_not_follow_mutable_pronunciation_or_options(self):
        store, jobs, doc, prepared = self.reading_fixture()
        pronunciation = {'engine': 'fixture', 'revision': 1, 'assets': {'lexicon': 'original'}}
        try:
            with patch('backend.jobs.pronunciation_identity', return_value=pronunciation):
                created = jobs.start(prepared, doc, 'af_heart', 1)
                command = jobs.commands.get(timeout=2)
            snapshot = store.get('jobs', created['id'])
            pronunciation['assets']['lexicon'] = 'different'
            prepared['options']['paragraph_pause'] = 10
            self.assertEqual(jobs.active['pronunciation_identity'], snapshot['pronunciation_identity'])
            self.assertEqual(jobs.active['audio_identity'], snapshot['audio_identity'])
            self.assertEqual(jobs.active['options'], snapshot['options'])
            self.assertEqual(command['job']['pronunciation_identity'], snapshot['pronunciation_identity'])
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
                (folder / name).write_bytes(pcm(samples=b'0123456789'))
            store.put('jobs', {'id': key, 'state': 'generating', 'completed': 1, 'total': 2})
            with urllib.request.urlopen(urllib.request.Request(f'{server.url}/media/{key}/section-000000.wav', headers={'Range': 'bytes=46-49'})) as response:
                self.assertEqual(response.status, 206)
                self.assertEqual(response.read(), b'2345')
            for path in [f'/media/{key}.wav', f'/media/{key}/section-000001.wav', f'/media/{key}/section-000000.part']:
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(server.url + path)
                self.assertEqual(error.exception.code, 404)
        finally:
            server.close()

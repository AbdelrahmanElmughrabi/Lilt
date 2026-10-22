"""Brand-only revisions must preserve saved speech checkpoints and cache keys."""
import copy
import queue
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import soundfile as sf

from backend.cache import section_key
from backend.documents import prepare
from backend.jobs import Jobs, public_job
from backend.models import FILES
from backend.pronunciation import pronunciation_identity
from backend.sections import published_sections
from backend.speech import speech_worker
from backend.storage import Store


class ContinuationBrandingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        assets = self.root / 'pronunciation'
        for name in ('misaki/data/gb_gold.json', 'misaki/data/gb_silver.json',
                     'misaki/data/us_gold.json', 'misaki/data/us_silver.json',
                     'en_core_web_sm/en_core_web_sm-3.8.0/tokenizer', 'num2words/__init__.py'):
            path = assets / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'disposable pronunciation fixture')
        versions = {'misaki': '0.9.4', 'en_core_web_sm': '3.8.0', 'num2words': '0.5.14'}
        distributions = patch('backend.pronunciation._distribution', side_effect=lambda name:
                              SimpleNamespace(version=versions.get(name, '1.0'), locate_file=lambda path: assets / path))
        distributions.start()
        self.addCleanup(distributions.stop)
        self.store = Store(self.root / 'library')
        with patch('backend.jobs.threading.Thread'):
            self.jobs = Jobs(self.store, None)
        models = self.root / 'models'
        models.mkdir()
        for name in FILES:
            (models / name).write_bytes(b'disposable fixture model')
        self.jobs.models = SimpleNamespace(root=models, status=lambda: {'state': 'ready', 'voices': ['af_heart']})
        self.jobs.performance = SimpleNamespace(resolve=Mock(return_value={
            'model': str(models / FILES[0]), 'provider': 'CPUExecutionProvider',
            'device_id': -1, 'threads': 1}), gpu_runtime=None, runtime='fixture')
        self.jobs._worker = Mock()
        markdown = 'First saved sentence.\n\nSecond sentence still needs speech.'
        self.prepared = prepare(markdown)
        self.document = self.store.document(markdown, self.prepared['title'])

    def tearDown(self):
        self.jobs.close()
        for channel in (self.jobs.commands, self.jobs.events):
            channel.cancel_join_thread()
            channel.close()
        self.temporary.cleanup()

    def saved_reading(self, brand, state='interrupted'):
        # Reproduce each historical identity, including the policy-dependent
        # symbol digest; do not manufacture an incomplete identity to bypass it.
        with patch('backend.pronunciation.PRONUNCIATION_REVISION', brand + '-misaki-english-v4'), \
             patch('backend.pronunciation.ADAPTER_REVISION', brand + '-kokoro-0.6.1-v1'), \
             patch('backend.speech_text.SYMBOL_POLICY', brand + '-speech-symbols-v3'):
            saved_identity = pronunciation_identity()
        with patch('backend.jobs.pronunciation_identity', return_value=saved_identity):
            self.jobs.start(self.prepared, self.document, 'af_heart', 1)
        command = self.jobs.commands.get(timeout=2)
        job = command['job']
        directory = Path(command['directory'])
        directory.mkdir()
        audio = directory / 'section-000000.wav'
        sf.write(audio, np.full(2400, .1), 24000, subtype='PCM_16')
        job['sections'], job['available_duration'] = published_sections(job, directory)
        job.update(state=state, completed=1, position=.05)
        self.store.put('jobs', job)
        self.jobs.active = None
        self.jobs._worker.reset_mock()
        self.jobs.performance.resolve.reset_mock()
        return job, audio, command

    def run_worker(self, command):
        commands, events = queue.Queue(), queue.Queue()
        commands.put(command)
        commands.put(None)
        engine = SimpleNamespace(create=Mock(return_value=(np.full(3600, .2), 24000)))
        # Run the real publication loop with synthetic samples and no native
        # inference or changes to this test process's scheduling priority.
        with patch('backend.performance.create_engine', return_value=engine), patch('psutil.Process'):
            speech_worker(commands, events, self.jobs.cancel)
        messages = []
        while not events.empty():
            messages.append(events.get_nowait())
        return messages, engine

    def test_both_brand_histories_resume_with_immutable_snapshots_and_cache(self):
        for brand in ('lilt', 'violilt'):
            for state in ('interrupted', 'cancelled', 'failed'):
                with self.subTest(brand=brand, state=state):
                    job, audio, _ = self.saved_reading(brand, state)
                    before, audio_before = copy.deepcopy(job), audio.read_bytes()
                    key = section_key(job['chunks'][0]['text'], job['voice'], job['speed'], job['audio_identity'])
                    self.jobs.cache.put(key, audio)
                    self.assertTrue(public_job(job)['can_resume'])
                    self.jobs.start(self.prepared, self.document, 'af_heart', 1, resume=job['id'])
                    resumed = self.jobs.commands.get(timeout=2)['job']
                    for field in ('chunks', 'markdown', 'options', 'pronunciation_identity', 'audio_identity',
                                  'sections', 'available_duration', 'position', 'completed'):
                        self.assertEqual(resumed[field], before[field], field)
                    self.assertEqual(audio.read_bytes(), audio_before)
                    self.assertTrue(self.jobs.cache.fetch(key, self.root / 'cached.wav'))
                    self.assertEqual((self.root / 'cached.wav').read_bytes(), audio_before)
                    self.jobs.active = None

    def test_worker_extends_both_brand_histories_and_retains_saved_audio(self):
        for brand in ('lilt', 'violilt'):
            with self.subTest(brand=brand):
                job, audio, command = self.saved_reading(brand)
                before, audio_before = copy.deepcopy(job), audio.read_bytes()
                messages, engine = self.run_worker(command)
                self.assertEqual(messages[-1]['state'], 'completed', messages)
                self.assertEqual(messages[-1]['completed'], len(job['chunks']))
                self.assertEqual(engine.create.call_count, len(job['chunks']) - 1)
                self.assertEqual(audio.read_bytes(), audio_before)
                self.assertEqual(job, before)
                self.assertEqual(self.store.get('jobs', job['id']), before)
                self.assertGreater(sf.info(audio.parent / 'recording.wav').frames, sf.info(audio).frames)

    def test_new_readings_reuse_the_pre_rebrand_speech_cache(self):
        old, audio, _ = self.saved_reading('lilt')
        key = section_key(old['chunks'][0]['text'], old['voice'], old['speed'], old['audio_identity'])
        self.jobs.cache.put(key, audio)
        self.jobs.start(self.prepared, self.document, 'af_heart', 1)
        command = self.jobs.commands.get(timeout=2)
        current = command['job']
        current_key = section_key(current['chunks'][0]['text'], current['voice'], current['speed'], current['audio_identity'])
        self.assertTrue(self.jobs.cache.fetch(current_key, self.root / 'cached.wav'))
        messages, _ = self.run_worker(command)
        self.assertEqual(messages[-1]['state'], 'completed', messages)
        progress = [item for item in messages if 'cache_hits' in item][-1]
        self.assertEqual(progress['cache_hits'], 1)
        self.assertEqual(progress['generated_sections'], len(current['chunks']) - 1)

    def test_aliases_do_not_accept_changed_speech_assets_rules_models_or_runtime(self):
        for brand in ('lilt', 'violilt'):
            job, audio, command = self.saved_reading(brand)
            original, audio_before = copy.deepcopy(job), audio.read_bytes()
            variants = []
            for field in ('revision', 'adapter', 'fallback', 'lexicon_sha256', 'model_sha256', 'num2words_sha256'):
                changed = copy.deepcopy(original)
                changed['pronunciation_identity'][field] += '-changed'
                variants.append((field, changed, 'different pronunciation engine'))
            for field in ('sha256', 'revision'):
                changed = copy.deepcopy(original)
                changed['pronunciation_identity']['symbols'][field] += '-changed'
                variants.append(('symbols ' + field, changed, 'different pronunciation engine'))
            changed = copy.deepcopy(original)
            changed['pronunciation_identity']['versions']['num2words'] += '-changed'
            variants.append(('dependency version', changed, 'different pronunciation engine'))
            changed = copy.deepcopy(original)
            changed['pronunciation_identity']['revision'] = ('violilt' if brand == 'lilt' else 'lilt') + '-misaki-english-v4'
            variants.append(('mixed brand identifiers', changed, 'different pronunciation engine'))
            for index in (0, 1, 2):
                changed = copy.deepcopy(original)
                changed['audio_identity'][index] = 'changed model, voice or runtime'
                variants.append(('audio input ' + str(index), changed, 'original text, voice, and model files'))
            for name, changed, message in variants:
                with self.subTest(brand=brand, change=name):
                    self.store.put('jobs', changed)
                    before = self.store.get('jobs', job['id'])
                    with self.assertRaisesRegex(ValueError, message):
                        self.jobs.start(self.prepared, self.document, 'af_heart', 1, resume=job['id'])
                    if not name.startswith('audio input'):
                        self.assertFalse(public_job(changed)['can_resume'])
                        messages, engine = self.run_worker(command | {'job': changed})
                        self.assertEqual(messages[-1]['state'], 'failed')
                        engine.create.assert_not_called()
                    self.assertEqual(self.store.get('jobs', job['id']), before)
                    self.assertEqual(audio.read_bytes(), audio_before)
                    self.assertIsNone(self.jobs.active)
                    self.jobs._worker.assert_not_called()


if __name__ == '__main__':
    unittest.main()

"""Generation status follows actual model loading and inference boundaries."""
import queue
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import soundfile as sf

from backend.speech import speech_worker


class GenerationStatusTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.model, self.voices = self.root / 'model', self.root / 'voices'
        self.model.write_bytes(b'disposable model')
        self.voices.write_bytes(b'disposable voices')
        self.commands, self.events = queue.Queue(), queue.Queue()
        self.cancel = threading.Event()
        self.engine = SimpleNamespace(create=Mock(return_value=(np.full(2400, .1), 24000)))

    def command(self, key='reading'):
        return {'job': {'id': key, 'voice': 'af_heart', 'speed': 1,
                        'pronunciation_identity': {'fixture': True}, 'audio_identity': ['fixture'],
                        'created': time.time(), 'chunks': [{'text': 'A disposable reading.', 'pause': 0}]},
                'directory': str(self.root / key), 'voices': str(self.voices),
                'config': {'model': str(self.model), 'provider': 'CPUExecutionProvider',
                           'device_id': -1, 'threads': 1},
                'cache': str(self.root / 'cache'), 'cache_enabled': False, 'cache_limit_mb': 256}

    def messages(self, key='reading'):
        return [event for event in self.events.queue if event.get('id') == key]

    def run_worker(self, *commands, factory=None):
        for command in commands:
            self.commands.put(command)
        self.commands.put(None)
        with patch('backend.pronunciation.pronunciation_identity', return_value={'fixture': True}), \
             patch('backend.performance.create_engine', side_effect=factory or (lambda *_: self.engine)) as load, \
             patch('psutil.Process'):
            speech_worker(self.commands, self.events, self.cancel)
        return load

    def test_cold_load_is_preparing_until_engine_is_ready_then_generating(self):
        def load(*_):
            latest = self.messages()[-1]
            self.assertEqual(latest['state'], 'preparing')
            self.assertEqual(latest['message'], 'Loading model…')
            return self.engine

        def create(*_, **__):
            latest = self.messages()[-1]
            self.assertEqual(latest['state'], 'generating')
            self.assertIn('Model loaded.', latest['message'])
            return np.full(2400, .1), 24000

        self.engine.create.side_effect = create
        self.run_worker(self.command(), factory=load)
        self.assertEqual(self.messages()[-1]['state'], 'completed', self.messages())
        self.engine.create.assert_called_once()
        self.assertTrue((self.root / 'reading' / 'recording.wav').is_file())

    def test_warm_model_does_not_report_another_load(self):
        load = self.run_worker(self.command(), self.command('second'))
        load.assert_called_once()
        self.assertTrue(any(event['message'] == 'Loading model…' for event in self.messages()))
        self.assertFalse(any(event['message'] == 'Loading model…' for event in self.messages('second')))
        for key in ('reading', 'second'):
            self.assertTrue(any(event['state'] == 'generating' and 'Model loaded.' in event['message']
                                for event in self.messages(key)))
            self.assertEqual(self.messages(key)[-1]['state'], 'completed')

    def test_load_failure_never_claims_generation_started(self):
        def load(*_):
            raise OSError('fixture load failure')

        self.run_worker(self.command(), factory=load)
        self.assertEqual(self.messages()[-1]['state'], 'failed')
        self.assertIn('fixture load failure', self.messages()[-1]['message'])
        self.assertFalse(any(event['state'] == 'generating' for event in self.messages()))
        self.engine.create.assert_not_called()

    def test_saved_audio_does_not_claim_loading_or_generation(self):
        command = self.command()
        directory = Path(command['directory'])
        directory.mkdir()
        section = directory / 'section-000000.wav'
        sf.write(section, np.full(2400, .1), 24000, subtype='PCM_16')
        before = section.read_bytes()
        load = self.run_worker(command)
        load.assert_not_called()
        self.engine.create.assert_not_called()
        self.assertEqual(self.messages()[-1]['state'], 'completed')
        self.assertFalse(any(event['state'] == 'generating' or event['message'] == 'Loading model…'
                             for event in self.messages()))
        self.assertTrue(any('Reusing saved audio' in event['message'] for event in self.messages()))
        self.assertEqual(section.read_bytes(), before)

    def test_cancel_during_load_does_not_start_inference(self):
        def load(*_):
            self.cancel.set()
            return self.engine

        self.run_worker(self.command(), factory=load)
        self.engine.create.assert_not_called()
        self.assertEqual(self.messages()[-1]['state'], 'cancelled')
        self.assertFalse(any(event['state'] == 'generating' for event in self.messages()))


if __name__ == '__main__':
    unittest.main()

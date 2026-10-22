"""Worker storage boundaries with synthetic audio and a fake inference engine."""
import queue
import tempfile
import threading
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
import soundfile as sf

from backend.speech import speech_worker


class WorkerIOTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.model, self.voices = self.root / 'model', self.root / 'voices'
        self.model.write_bytes(b'synthetic model')
        self.voices.write_bytes(b'synthetic voices')
        self.commands, self.events, self.cancel = queue.Queue(), queue.Queue(), threading.Event()
        self.engine = SimpleNamespace(create=Mock(return_value=(np.full(2400, .1), 24000)))

    def command(self, key='reading', cache=True):
        return {'job': {'id': key, 'voice': 'af_heart', 'speed': 1,
                        'pronunciation_identity': {'fixture': True}, 'audio_identity': ['fixture'],
                        'created': 1, 'chunks': [{'text': 'Synthetic reading.', 'pause': 0}]},
                'directory': str(self.root / key), 'voices': str(self.voices),
                'config': {'model': str(self.model), 'provider': 'CPUExecutionProvider', 'device_id': -1, 'threads': 1},
                'cache': str(self.root / 'cache'), 'cache_enabled': cache, 'cache_limit_mb': 256}

    def run_worker(self, *commands):
        for command in commands:
            self.commands.put(command)
        self.commands.put(None)
        errors = []
        with patch('backend.pronunciation.pronunciation_identity', return_value={'fixture': True}), \
             patch('backend.performance.create_engine', return_value=self.engine), patch('psutil.Process'):
            try:
                speech_worker(self.commands, self.events, self.cancel)
            except OSError as error:
                errors.append(str(error))
        self.assertEqual(errors, [], 'An output setup error escaped the per-job boundary.')

    def last(self, key='reading'):
        return [event for event in self.events.queue if event.get('id') == key][-1]

    def test_job_folder_failure_reports_failure_and_worker_accepts_next_job(self):
        mkdir = Path.mkdir

        def constrained(path, *args, **kwargs):
            if path == self.root / 'reading':
                raise OSError(28, 'injected job directory full')
            return mkdir(path, *args, **kwargs)

        with patch('pathlib.Path.mkdir', constrained):
            self.run_worker(self.command(cache=False), self.command('next', cache=False))
        self.assertEqual(self.last()['state'], 'failed')
        self.assertEqual(self.last('next')['state'], 'completed')

    def test_optional_cache_initialization_failure_keeps_generation_usable(self):
        mkdir = Path.mkdir

        def constrained(path, *args, **kwargs):
            if path == self.root / 'cache':
                raise PermissionError('injected cache permission failure')
            return mkdir(path, *args, **kwargs)

        with patch('pathlib.Path.mkdir', constrained):
            self.run_worker(self.command())
        self.assertEqual(self.last()['state'], 'completed')
        self.assertTrue((self.root / 'reading/recording.wav').is_file())

    def test_optional_cache_fetch_and_put_failures_keep_generation_usable(self):
        for method in ('fetch', 'put'):
            with self.subTest(method=method), patch('backend.cache.SectionCache.' + method, side_effect=OSError('injected cache failure')):
                key = 'reading-' + method
                self.run_worker(self.command(key))
                self.assertEqual(self.last(key)['state'], 'completed')
                self.assertTrue((self.root / key / 'recording.wav').is_file())

    def test_failed_final_assembly_preserves_published_section_bytes(self):
        command = self.command(cache=False)
        directory = self.root / 'reading'
        directory.mkdir()
        section = directory / 'section-000000.wav'
        sf.write(section, np.full(2400, .1), 24000, subtype='PCM_16')
        before = section.read_bytes()
        open_wave = wave.open

        def constrained(file, *args, **kwargs):
            mode = kwargs.get('mode', args[0] if args else None)
            if Path(file) == directory / 'recording.part' and mode in ('w', 'wb'):
                raise OSError(28, 'injected final output full')
            return open_wave(file, *args, **kwargs)

        with patch('backend.speech.wave.open', side_effect=constrained):
            self.run_worker(command)
        self.assertEqual(self.last()['state'], 'failed')
        self.assertEqual(section.read_bytes(), before)
        self.assertFalse((directory / 'recording.wav').exists())

    def test_resume_cache_and_assembly_use_no_native_stored_audio_decoder(self):
        command = self.command()
        command['job']['chunks'] = [{'text':'Saved section.', 'pause':.025}, {'text':'New section.', 'pause':0}]
        directory = self.root / 'reading'; directory.mkdir()
        section = directory / 'section-000000.wav'
        sf.write(section, np.full(2400, .1), 24000, subtype='PCM_16')
        with wave.open(str(section), 'rb') as original:
            samples = original.readframes(2400)
        soundfile = sf.SoundFile

        def output_only(file, *args, **kwargs):
            mode = kwargs.get('mode', args[0] if args else 'r')
            self.assertTrue(mode.startswith('w'), 'A stored section reached native decoding')
            return soundfile(file, *args, **kwargs)

        with patch('soundfile.SoundFile', side_effect=output_only), \
             patch('soundfile.info', side_effect=AssertionError('Native metadata inspection forbidden')):
            self.run_worker(command)
        self.assertEqual(self.last()['state'], 'completed')
        self.assertEqual(self.engine.create.call_count, 1)
        with wave.open(str(directory / 'recording.wav'), 'rb') as final:
            self.assertEqual(final.getnframes(), 5400)
            self.assertEqual(final.readframes(2400), samples)
            self.assertEqual(final.readframes(600), bytes(1200))
            self.assertEqual(final.readframes(2400), samples)

    def test_unsupported_saved_section_and_recording_retained_before_regeneration(self):
        command = self.command(cache=False)
        directory = self.root / 'reading'; directory.mkdir()
        section = directory / 'section-000000.wav'
        sf.write(section, np.zeros(120), 24000, format='AIFF', subtype='PCM_16')
        before = section.read_bytes()
        recording = directory / 'recording.wav'
        recording.write_bytes(before)
        with patch('soundfile.info', side_effect=AssertionError('Native inspection forbidden')):
            self.run_worker(command)
        self.assertEqual(self.last()['state'], 'completed')
        retained = list(directory.glob('section-000000.wav.unreadable-*'))
        self.assertEqual(len(retained), 1)
        self.assertEqual(retained[0].read_bytes(), before)
        self.assertTrue(section.read_bytes().startswith(b'RIFF'))
        retained_recordings = list(directory.glob('recording.wav.unreadable-*'))
        self.assertEqual(len(retained_recordings), 1)
        self.assertEqual(retained_recordings[0].read_bytes(), before)
        self.assertTrue(recording.read_bytes().startswith(b'RIFF'))


if __name__ == '__main__':
    unittest.main()

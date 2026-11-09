import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from backend.kokoro_engine import Kokoro
from backend.pronunciation import PronunciationError


class FakePronunciation:
    def __init__(self, phonemes='a.'):
        self.phonemes = phonemes
        self.last_warnings = []
        self.calls = []

    def phonemize(self, text, lang):
        self.calls.append((text, lang))
        self.last_warnings = ['Some words were spelled out.'] if text == 'unknown' else []
        return self.phonemes


class FakeSession:
    def __init__(self, *, token_name='tokens', token_type='tensor(int64)', style_type='tensor(float)', speed_type='tensor(float)', vocab=None, durations=False):
        self.inputs = [SimpleNamespace(name=token_name, type=token_type), SimpleNamespace(name='style', type=style_type), SimpleNamespace(name='speed', type=speed_type)]
        self.outputs = [SimpleNamespace(name='audio')]
        if durations:
            self.outputs.append(SimpleNamespace(name='duration'))
        self.metadata = {} if vocab is None else {'kokoro_config': json.dumps({'vocab': vocab})}
        self.calls = []

    def get_inputs(self):
        return self.inputs

    def get_outputs(self):
        return self.outputs

    def get_modelmeta(self):
        return SimpleNamespace(custom_metadata_map=self.metadata)

    def run(self, names, inputs):
        self.calls.append(inputs)
        output = [np.full(4096, .1, dtype=np.float32)]
        if len(self.outputs) > 1:
            token_input = next(value for name, value in inputs.items() if name in {'tokens', 'input_ids'})
            output.append(np.ones(token_input.shape[1], dtype=np.int64))
        return output


class KokoroAdapterTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.voices = Path(self.folder.name) / 'voices.bin'
        self.style = np.arange(510, dtype=np.float32).reshape(510, 1, 1)
        with self.voices.open('wb') as output:
            np.savez(output, af_heart=self.style, bf_emma=self.style + 1000)
        self.engines = []

    def tearDown(self):
        for engine in self.engines:
            engine.voices.close()
        self.engines.clear()
        self.folder.cleanup()

    def engine(self, session=None, pronunciation=None):
        engine = Kokoro(session or FakeSession(), self.voices, pronunciation=pronunciation or FakePronunciation())
        self.engines.append(engine)
        return engine

    def test_model_dtype_names_padding_and_style_row_are_preserved(self):
        session = FakeSession(token_name='input_ids', token_type='tensor(int32)', style_type='tensor(float16)')
        engine = self.engine(session, FakePronunciation('aaa'))
        audio, rate = engine.create('hello', 'af_heart', speed=1.25, trim=False)
        inputs = session.calls[0]
        self.assertEqual(inputs['input_ids'].dtype, np.dtype(np.int32))
        self.assertEqual(inputs['style'].dtype, np.dtype(np.float16))
        self.assertEqual(inputs['speed'].dtype, np.dtype(np.float32))
        self.assertEqual(inputs['input_ids'].tolist(), [[0, engine.vocab['a'], engine.vocab['a'], engine.vocab['a'], 0]])
        self.assertEqual(float(inputs['style'][0, 0]), 2)
        self.assertAlmostEqual(float(inputs['speed'][0]), 1.25)
        self.assertEqual(rate, 24000)
        self.assertTrue(np.all(np.isfinite(audio)))

    def test_model_embedded_vocabulary_overrides_fallback(self):
        session = FakeSession(vocab={'a': 77, '.': 55})
        engine = self.engine(session)
        engine.create('hello', 'af_heart', trim=False)
        self.assertEqual(session.calls[0]['tokens'].tolist(), [[0, 77, 55, 0]])

    def test_unsupported_symbol_stops_before_inference(self):
        session = FakeSession()
        engine = self.engine(session, FakePronunciation('a❓'))
        with self.assertRaisesRegex(PronunciationError, 'cannot read'):
            engine.create('hello', 'af_heart')
        self.assertEqual(session.calls, [])

    def test_long_unbroken_word_is_split_without_losing_tail(self):
        phonemes = 'a' * 1100 + 'z'
        session = FakeSession()
        engine = self.engine(session, FakePronunciation(phonemes))
        engine.create('very long', 'af_heart', trim=False)
        tokens = [token for call in session.calls for token in call['tokens'][0, 1:-1]]
        self.assertEqual(len(tokens), len(phonemes))
        self.assertEqual(tokens[-1], engine.vocab['z'])
        self.assertTrue(all(call['tokens'].shape[1] <= 512 for call in session.calls))

    def test_batch_joins_retain_sentence_pause_and_trimming(self):
        session = FakeSession()
        engine = self.engine(session, FakePronunciation('a' * 508 + '. b'))
        with patch('backend.kokoro_engine.trim_audio', side_effect=lambda audio: (audio[5:-5], (5, len(audio) - 5))):
            audio, _ = engine.create('long sentence', 'af_heart', sentence_pause=.25)
        self.assertEqual(len(session.calls), 2)
        self.assertEqual(len(audio), 2 * (4096 - 10) + 6000)
        self.assertTrue(np.all(audio[4086:10086] == 0))

    def test_duration_models_keep_phoneme_timings(self):
        engine = self.engine(FakeSession(durations=True), FakePronunciation('aa'))
        audio, rate, timings = engine.create_timed('hello', 'af_heart', trim=False)
        self.assertEqual(rate, 24000)
        self.assertEqual(len(timings), 2)
        self.assertEqual([item.phoneme for item in timings], ['a', 'a'])
        self.assertGreater(timings[0].end, timings[0].start)
        self.assertEqual(len(audio), 4096)

    def test_warning_and_language_contract_resets_per_call(self):
        pronunciation = FakePronunciation()
        engine = self.engine(pronunciation=pronunciation)
        engine.create('unknown', 'bf_emma', lang='en-gb', trim=False)
        self.assertTrue(engine.last_pronunciation_warnings)
        self.assertEqual(pronunciation.calls[-1], ('unknown', 'en-gb'))
        engine.create('known', 'af_heart', trim=False)
        self.assertEqual(engine.last_pronunciation_warnings, [])

    def test_invalid_speed_and_empty_phonemes_fail_before_inference(self):
        engine = self.engine()
        for speed in (float('nan'), float('inf'), 0, 2.1, True):
            with self.subTest(speed=speed), self.assertRaises(ValueError):
                engine.create('hello', 'af_heart', speed=speed)
        engine.pronunciation.phonemes = ''
        with self.assertRaises(PronunciationError):
            engine.create('hello', 'af_heart')
        self.assertEqual(engine.sess.calls, [])

    def test_from_session_uses_our_pronunciation_adapter(self):
        with patch('backend.kokoro_engine.EnglishPronunciation', return_value=FakePronunciation()) as pronunciation:
            engine = Kokoro.from_session(FakeSession(), self.voices)
        self.engines.append(engine)
        pronunciation.assert_called_once_with()
        self.assertEqual(engine.get_voices(), ['af_heart', 'bf_emma'])


if __name__ == '__main__':
    unittest.main()

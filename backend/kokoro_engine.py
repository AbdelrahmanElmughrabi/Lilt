"""Kokoro inference using Violilt's offline English pronunciation.

Adapted from Kokoro-ONNX 0.6.1, Copyright (c) 2025 github.com/thewh1teagle, MIT.
See backend/_vendor/kokoro/LICENSE. This adaptation removes the upstream
pronunciation imports and rejects unsupported symbols instead of dropping them.
The model, voice styles, batching, trimming and pause algorithms are retained.
"""
from __future__ import annotations

import json
import math
import warnings

import numpy as np

from ._vendor.kokoro.chunker import pause_after, split_phonemes
from ._vendor.kokoro.config import DEFAULT_VOCAB, MAX_PHONEME_LENGTH, SAMPLE_RATE
from ._vendor.kokoro.pauses import insert as insert_pauses
from ._vendor.kokoro.sliding import synthesize, timings, token_edges
from ._vendor.kokoro.trim import trim as trim_audio
from .pronunciation import EnglishPronunciation, PronunciationError


_NUMPY_TYPES = {
    'tensor(float)': np.dtype(np.float32), 'tensor(float16)': np.dtype(np.float16),
    'tensor(double)': np.dtype(np.float64), 'tensor(int32)': np.dtype(np.int32),
    'tensor(int64)': np.dtype(np.int64),
}


class Kokoro:
    def __init__(self, session, voices_path, *, pronunciation=None, vocab=None):
        self.sess = session
        self.voices = np.load(str(voices_path), allow_pickle=False)
        self.pronunciation = pronunciation if pronunciation is not None else EnglishPronunciation()
        self.last_pronunciation_warnings = []
        metadata = session.get_modelmeta().custom_metadata_map.get('kokoro_config')
        if vocab is None and metadata:
            try:
                vocab = json.loads(metadata)['vocab']
            except (ValueError, KeyError, TypeError) as error:
                raise ValueError('The model pronunciation vocabulary is invalid.') from error
        self.vocab = DEFAULT_VOCAB if vocab is None else vocab
        if not isinstance(self.vocab, dict) or not self.vocab or any(
                not isinstance(symbol, str) or len(symbol) != 1 or isinstance(value, bool)
                or not isinstance(value, int) or value <= 0 for symbol, value in self.vocab.items()):
            raise ValueError('The model pronunciation vocabulary is invalid.')
        self._input_dtypes = {}
        for item in session.get_inputs():
            if item.type not in _NUMPY_TYPES:
                raise ValueError(f'The model input {item.name} has an unsupported type.')
            self._input_dtypes[item.name] = _NUMPY_TYPES[item.type]
        self._tokens_input = 'input_ids' if 'input_ids' in self._input_dtypes else 'tokens'
        if not {self._tokens_input, 'style', 'speed'} <= self._input_dtypes.keys():
            raise ValueError('The model is missing its speech inputs.')
        output_names = [output.name for output in session.get_outputs()]
        self._audio_output = output_names.index('audio') if 'audio' in output_names else 0
        self._duration_output = output_names.index('duration') if 'duration' in output_names else None
        self.has_timings = self._duration_output is not None
        self._stops = frozenset(self.vocab[mark] for mark in '.!?' if mark in self.vocab)
        self._spaces = frozenset(self.vocab[mark] for mark in ' ' if mark in self.vocab)

    @classmethod
    def from_session(cls, session, voices_path):
        return cls(session, voices_path)

    def __del__(self):
        archive = getattr(self, 'voices', None)
        if archive is not None and hasattr(archive, 'close'):
            archive.close()

    def get_voices(self):
        return sorted(self.voices.keys())

    def get_voice_style(self, name):
        return self.voices[name]

    def _tokenize(self, phonemes, limit=MAX_PHONEME_LENGTH):
        unknown = sorted(set(phonemes) - self.vocab.keys())
        if unknown:
            codes = ', '.join(f'U+{ord(symbol):04X}' for symbol in unknown[:5])
            raise PronunciationError(f'Pronunciation produced symbols the speech model cannot read ({codes}). No words were dropped.')
        tokens = [self.vocab[symbol] for symbol in phonemes]
        if limit is not None and len(tokens) > limit:
            raise ValueError('The speech batch exceeds the model context; no phonemes were truncated.')
        if not tokens:
            raise PronunciationError('This section produced no supported speech.')
        return tokens

    def _speed_value(self, speed):
        dtype = self._input_dtypes['speed']
        if dtype.kind in 'iu' and float(speed) != int(speed):
            rounded = max(1, round(speed))
            warnings.warn(f'This model takes integer speech speeds; using {rounded}.', RuntimeWarning, stacklevel=2)
            return rounded
        return speed

    def _infer(self, tokens, style, speed):
        inputs = {
            self._tokens_input: np.array([[0, *tokens, 0]], dtype=self._input_dtypes[self._tokens_input]),
            'style': np.asarray(style, dtype=self._input_dtypes['style']),
            'speed': np.array([self._speed_value(speed)], dtype=self._input_dtypes['speed']),
        }
        outputs = self.sess.run(None, inputs)
        audio = np.asarray(outputs[self._audio_output]).ravel()
        duration = np.asarray(outputs[self._duration_output]).ravel() if self.has_timings else None
        return audio, duration

    @staticmethod
    def _style_for(voice, length):
        # Upstream voice artifacts have one row per phoneme count: n - 1.
        if not len(voice):
            raise ValueError('The selected voice has no style vectors.')
        return voice[min(length, len(voice)) - 1]

    def _prepare(self, text, voice, speed, lang, is_phonemes, sentence_pause, clause_pause):
        if not isinstance(speed, (int, float)) or isinstance(speed, bool) or not math.isfinite(speed) or not 0.5 <= speed <= 2:
            raise ValueError('Speed should be between 0.5 and 2.0.')
        for pause in (sentence_pause, clause_pause):
            if not isinstance(pause, (int, float)) or not math.isfinite(pause) or pause < 0:
                raise ValueError('Speech pauses must be finite and nonnegative.')
        if isinstance(voice, str):
            if voice not in self.voices:
                raise ValueError('The selected voice is missing from the voice file.')
            voice = self.get_voice_style(voice)
        phonemes = text if is_phonemes else self.pronunciation.phonemize(text, lang)
        if not is_phonemes:
            self.last_pronunciation_warnings = list(self.pronunciation.last_warnings)
        phonemes = ' '.join(phonemes.split())
        # Validate the complete string before splitting or invoking inference.
        self._tokenize(phonemes, limit=None)
        batches = split_phonemes(phonemes, MAX_PHONEME_LENGTH)
        if not batches:
            raise PronunciationError('This section produced no supported speech.')
        return voice, phonemes, [(batch, pause_after(batch, sentence_pause, clause_pause))
                                 for batch in batches[:-1]] + [(batches[-1], 0.0)]

    def _create_batch(self, phonemes, voice, speed, trim, pause=0):
        tokens = self._tokenize(phonemes)
        audio, duration = self._infer(tokens, self._style_for(voice, len(tokens)), speed)
        edges = token_edges(duration, len(audio))[1:] if duration is not None else None
        if trim:
            audio, (head, _) = trim_audio(audio)
            if edges is not None:
                edges = np.clip(edges - head, 0, len(audio))
            if pause:
                audio = np.concatenate([audio, np.zeros(int(pause * SAMPLE_RATE), dtype=audio.dtype)])
        return audio, edges

    def _create_batches(self, batches, voice, speed, trim):
        parts, spoken, offset = [], [], 0
        for phonemes, pause in batches:
            audio, edges = self._create_batch(phonemes, voice, speed, trim, pause)
            if edges is not None:
                spoken += timings(phonemes, edges + offset, SAMPLE_RATE)
            parts.append(audio)
            offset += len(audio)
        return np.concatenate(parts), spoken

    def _create_continuous(self, phonemes, voice, speed):
        if not self.has_timings:
            raise ValueError('Continuous synthesis needs a model that reports durations.')
        tokens = self._tokenize(phonemes, limit=None)
        style = self._style_for(voice, len(tokens))
        audio, edges = synthesize(lambda window: self._infer(window, style, speed), tokens,
                                  sample_rate=SAMPLE_RATE, stops=self._stops, spaces=self._spaces)
        return audio, timings(phonemes, edges, SAMPLE_RATE)

    def create(self, text, voice, speed=1.0, lang='en-us', is_phonemes=False, trim=True,
               sentence_pause=0.25, clause_pause=0.1, continuous=False):
        audio, rate, _ = self.create_timed(text, voice, speed, lang, is_phonemes, trim,
                                          sentence_pause, clause_pause, continuous)
        return audio, rate

    def create_timed(self, text, voice, speed=1.0, lang='en-us', is_phonemes=False, trim=True,
                     sentence_pause=0.25, clause_pause=0.1, continuous=False):
        self.last_pronunciation_warnings = []
        voice, phonemes, batches = self._prepare(text, voice, speed, lang, is_phonemes, sentence_pause, clause_pause)
        audio, spoken = self._create_continuous(phonemes, voice, speed) if continuous else self._create_batches(batches, voice, speed, trim)
        audio, spoken = insert_pauses(audio, spoken, SAMPLE_RATE, sentence_pause, clause_pause)
        return audio, SAMPLE_RATE, spoken

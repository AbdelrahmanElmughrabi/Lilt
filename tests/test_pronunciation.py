import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from backend.pronunciation import EnglishPronunciation, PronunciationError, pronunciation_identity
from backend.documents import prepare
from backend.speech_text import SYMBOL_NAMES


class PronunciationIdentityTests(unittest.TestCase):
    def test_identity_is_json_safe_and_does_not_import_speech_libraries(self):
        root = Path(__file__).resolve().parents[1]
        code = """
import builtins, json, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'spacy', 'misaki', 'phonemizer', 'espeakng_loader', 'torch', 'transformers'}:
        raise AssertionError('Unexpected heavy pronunciation import: ' + name)
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from backend.pronunciation import pronunciation_identity
first = pronunciation_identity()
assert first == pronunciation_identity()
print(json.dumps(first))
"""
        result = subprocess.run([sys.executable, '-X', 'utf8', '-c', code], cwd=root, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)['revision'], 'lilt-misaki-english-v2')

    def test_actual_lexicon_model_and_replaceable_library_change_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            lexicons = root / 'misaki' / 'data'
            lexicons.mkdir(parents=True)
            for name in ('gb_gold.json', 'gb_silver.json', 'us_gold.json', 'us_silver.json'):
                (lexicons / name).write_text('{}', encoding='utf-8')
            model = root / 'en_core_web_sm' / 'en_core_web_sm-3.8.0'
            model.mkdir(parents=True)
            (model / 'tokenizer').write_bytes(b'model')
            numbers = root / 'num2words'
            numbers.mkdir()
            (numbers / '__init__.py').write_text('original = True', encoding='utf-8')
            versions = {'misaki': '0.9.4', 'en_core_web_sm': '3.8.0', 'num2words': '0.5.14'}
            def distribution(name):
                return SimpleNamespace(version=versions.get(name, '1.0'), locate_file=lambda path: root / path)
            with patch('backend.pronunciation._distribution', side_effect=distribution):
                original = pronunciation_identity()
                for path, key in [(lexicons / 'us_gold.json', 'lexicon_sha256'),
                                  (model / 'tokenizer', 'model_sha256'),
                                  (numbers / '__init__.py', 'num2words_sha256')]:
                    path.write_bytes(path.read_bytes() + b' altered')
                    modified = pronunciation_identity()
                    self.assertNotEqual(original[key], modified[key])
                    self.assertEqual(modified, pronunciation_identity())
                (numbers / '__pycache__').mkdir()
                (numbers / '__pycache__' / 'cache.pyc').write_bytes(b'irrelevant cache')
                self.assertEqual(modified, pronunciation_identity())
                versions['num2words'] = 'replacement'
                self.assertNotEqual(modified, pronunciation_identity())

    def test_missing_dependencies_have_stable_identity(self):
        with patch('backend.pronunciation._distribution', return_value=None):
            identity = pronunciation_identity()
            self.assertEqual(identity['lexicon_sha256'], 'missing')
            self.assertEqual(identity['model_sha256'], 'missing')
            self.assertEqual(identity['num2words_sha256'], 'missing')
            self.assertEqual(identity, pronunciation_identity())


try:
    _misaki_available = importlib.metadata.version('misaki') == '0.9.4' and importlib.metadata.version('en_core_web_sm') == '3.8.0'
except importlib.metadata.PackageNotFoundError:
    _misaki_available = False


@unittest.skipUnless(_misaki_available, 'The isolated evaluation environment supplies the offline pronunciation assets.')
class OfflineEnglishTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import spacy.cli
        from misaki import en
        with patch.object(spacy.cli, 'download', side_effect=AssertionError('Runtime download attempted')), \
             patch.object(en.G2P, '__init__', side_effect=AssertionError('Unsafe upstream initializer used')):
            cls.engine = EnglishPronunciation()

    def test_regular_english_and_numbers_have_no_fallback_warning(self):
        phonemes = self.engine.phonemize('A little room for listening. It costs $12.50, or twenty five percent.')
        self.assertIn('.', phonemes)
        self.assertNotIn('❓', phonemes)
        self.assertEqual(self.engine.last_warnings, [])

    def test_currency_amount_does_not_repeat_the_suppressed_symbol(self):
        phonemes = self.engine.phonemize('$12.50')
        lexicon = self.engine.engines[False].lexicon
        self.assertEqual(phonemes.count(lexicon.golds['dollar']), 1)
        self.assertEqual(phonemes.count(lexicon.golds['cent']), 1)
        self.assertEqual(self.engine.last_warnings, [])

    def test_unknown_ascii_words_are_spelled_and_warning_is_reset(self):
        phonemes = self.engine.phonemize('qzxwvu')
        lexicon = self.engine.engines[False].lexicon
        expected = ' '.join(lexicon.golds[letter.upper()] for letter in 'qzxwvu')
        self.assertEqual(phonemes, expected)
        self.assertTrue(any('spelled out' in warning for warning in self.engine.last_warnings))
        self.assertTrue(all('qzxwvu' not in warning for warning in self.engine.last_warnings))
        self.engine.phonemize('Hello world.')
        self.assertEqual(self.engine.last_warnings, [])

    def test_british_engine_and_letter_names_are_selected(self):
        us = self.engine.phonemize('qzxwvu', 'en-us')
        gb = self.engine.phonemize('qzxwvu', 'en-gb')
        self.assertNotEqual(us, gb)
        self.assertIn(self.engine.engines[True].lexicon.golds['zed'], gb)
        self.assertTrue(self.engine.engines[True].british)

    def test_practical_accented_latin_words_are_covered_with_notice(self):
        phonemes = self.engine.phonemize('café naïve résumé coöperate')
        self.assertTrue(phonemes)
        self.assertNotIn('❓', phonemes)
        self.assertTrue(any('accented Latin' in warning for warning in self.engine.last_warnings))

    def test_literal_markup_cannot_override_or_suppress_words(self):
        literal = self.engine.phonemize('[hello](/bye/)')
        override = self.engine.phonemize('bye')
        self.assertNotEqual(literal, override)
        self.assertIn(self.engine.engines[False].lexicon.golds['H'], literal)

    def test_unsupported_scripts_and_symbols_stop_clearly(self):
        for text in ('λ', 'Hello 🦊 world.', '中文'):
            with self.subTest(text=text), self.assertRaisesRegex(PronunciationError, 'cannot pronounce'):
                self.engine.phonemize(text)

    def test_prepared_symbols_preserve_complete_sentence_in_both_accents(self):
        for original, spoken in [('Before➔middle 🦊 after. Next sentence stays.',
                                  'Before right arrow middle after. Next sentence stays.'),
                                 ('Hello 🦊́ world. café stays.', 'Hello world. café stays.')]:
            prepared = prepare(original)
            self.assertEqual(prepared['text'], spoken)
            for lang in ('en-us', 'en-gb'):
                actual = self.engine.phonemize(prepared['chunks'][0]['text'], lang)
                self.assertEqual(actual, self.engine.phonemize(spoken, lang))
                self.assertTrue(actual)

    def test_all_listed_symbol_names_have_real_offline_pronunciation(self):
        for lang in ('en-us', 'en-gb'):
            for symbol, name in SYMBOL_NAMES.items():
                with self.subTest(symbol=symbol, lang=lang):
                    prepared = prepare('Before ' + symbol + ' after.')
                    self.assertEqual(self.engine.phonemize(prepared['text'], lang),
                                     self.engine.phonemize('Before ' + name + ' after.', lang))

    def test_symbol_policy_digest_is_part_of_pronunciation_identity(self):
        original = pronunciation_identity()
        with patch.dict(SYMBOL_NAMES, {'➔': 'changed arrow'}):
            self.assertNotEqual(pronunciation_identity()['symbols'], original['symbols'])

    def test_substantive_words_cannot_be_dropped_by_tokenizer(self):
        engine = self.engine._engine(False)
        token = self.engine._en.MToken('hello', 'NN', '', phonemes='')
        with patch.object(type(engine), '__call__', return_value=('', [token])):
            with self.assertRaisesRegex(PronunciationError, 'omitted'):
                self.engine.phonemize('hello')

    def test_changed_assets_require_fresh_engine(self):
        changed = dict(self.engine.identity, num2words_sha256='replacement')
        with patch('backend.pronunciation.pronunciation_identity', return_value=changed):
            with self.assertRaisesRegex(PronunciationError, 'Restart'):
                self.engine.phonemize('hello')


if __name__ == '__main__':
    unittest.main()

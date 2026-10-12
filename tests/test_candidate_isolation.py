"""Candidate data isolation and pronunciation notices across section reuse."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import soundfile as sf

from backend.cache import SectionCache
from backend.storage import Store, data_directory


class CandidateIsolationTests(unittest.TestCase):
    def test_evaluation_profile_does_not_migrate_or_open_existing_library(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = Store(root / 'Folio')
            legacy.document('Original words', 'Original')
            before = legacy.db.read_bytes()
            with patch.dict(os.environ, {'LOCALAPPDATA': str(root)}, clear=True):
                selected = data_directory('Lilt-Pronunciation-Evaluation')
            evaluation = Store(selected)
            self.assertEqual(selected, root / 'Lilt-Pronunciation-Evaluation')
            self.assertEqual(evaluation.all('documents'), [])
            self.assertEqual(legacy.db.read_bytes(), before)
            self.assertFalse((root / 'Lilt').exists())

    def test_candidate_override_is_separate_from_baseline_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict(os.environ, {'LOCALAPPDATA': directory, 'LILT_DATA_DIR': str(root / 'baseline')}, clear=True):
                self.assertEqual(data_directory('Lilt-Pronunciation-Evaluation'), root / 'Lilt-Pronunciation-Evaluation')
                with patch.dict(os.environ, {'LILT_EVALUATION_DATA_DIR': str(root / 'candidate')}):
                    self.assertEqual(data_directory('Lilt-Pronunciation-Evaluation'), root / 'candidate')

    def test_cache_preserves_notices_and_clears_only_its_sidecars(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'section-000000.wav'
            sf.write(source, np.zeros(1000), 24000, subtype='PCM_16')
            notices = ['An unfamiliar word was spelled aloud.']
            SectionCache.write_warnings(source, notices)
            cache = SectionCache(root / 'cache')
            key = 'a' * 64
            cache.put(key, source)
            copy = root / 'section-000001.wav'
            self.assertTrue(cache.fetch(key, copy))
            self.assertEqual(SectionCache.read_warnings(copy), notices)
            cache.clear()
            self.assertFalse((cache.root / (key + '.pronunciation.json')).exists())
            self.assertEqual(SectionCache.read_warnings(copy), notices)
            self.assertEqual(SectionCache.read_warnings(source), notices)

    def test_fetch_without_notice_removes_stale_destination_notice(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, copy = root / 'source.wav', root / 'copy.wav'
            sf.write(source, np.zeros(1000), 24000, subtype='PCM_16')
            SectionCache.write_warnings(copy, ['Stale notice'])
            cache = SectionCache(root / 'cache')
            key = 'b' * 64
            cache.put(key, source)
            self.assertTrue(cache.fetch(key, copy))
            self.assertEqual(SectionCache.read_warnings(copy), [])

    def test_interrupted_cache_publication_cannot_leave_unwarned_reusable_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.wav'
            sf.write(source, np.zeros(1000), 24000, subtype='PCM_16')
            notices = ['Some words outside the pronunciation dictionary were spelled out.']
            SectionCache.write_warnings(source, notices)
            cache = SectionCache(root / 'cache')
            original_replace = Path.replace

            def interruption(path, target):
                if Path(target).suffix == '.wav':
                    raise OSError('Simulated interruption before audio publication')
                return original_replace(path, target)

            key = 'c' * 64
            with patch.object(Path, 'replace', interruption), self.assertRaises(OSError):
                cache.put(key, source)
            self.assertFalse(cache.fetch(key, root / 'unpublished.wav'))
            cache.put(key, source)
            with patch.object(Path, 'replace', interruption), self.assertRaises(OSError):
                cache.fetch(key, root / 'copy.wav')
            self.assertFalse((root / 'copy.wav').exists())
            self.assertTrue(cache.fetch(key, root / 'copy.wav'))
            self.assertEqual(SectionCache.read_warnings(root / 'copy.wav'), notices)

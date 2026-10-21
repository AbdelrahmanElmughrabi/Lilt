import hashlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from backend.model_trust import APPROVED, DOWNLOAD_ROOT, verify_file
from backend.models import FILES, GPU_FILE, Models
from backend.performance import create_engine


class ModelTrustTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        voices = io.BytesIO()
        np.savez(voices, af_heart=np.zeros((1, 1)))
        self.blobs = {FILES[0]: b'approved synthetic CPU fixture', FILES[1]: voices.getvalue(),
                      GPU_FILE: b'approved synthetic GPU fixture'}
        pins = {name: (len(body), hashlib.sha256(body).hexdigest()) for name, body in self.blobs.items()}
        self.pin_patch = patch.dict(APPROVED, pins, clear=True)
        self.pin_patch.start()

    def tearDown(self):
        self.pin_patch.stop()
        self.temporary.cleanup()

    def files(self, directory, gpu=False):
        directory.mkdir(parents=True, exist_ok=True)
        for name in list(FILES) + ([GPU_FILE] if gpu else []):
            (directory / name).write_bytes(self.blobs[name])
        return directory

    def test_readiness_requires_exact_content_and_gpu_failure_keeps_cpu(self):
        directory = self.files(self.root / 'models', gpu=True)
        model = Models(directory)
        self.assertEqual(model.status()['state'], 'ready')
        self.assertTrue(model.gpu_verified)
        (directory / GPU_FILE).write_bytes(b'x' * len(self.blobs[GPU_FILE]))
        model._refresh()
        self.assertEqual(model.status()['state'], 'ready')
        self.assertFalse(model.gpu_verified)
        self.assertTrue(model.gpu_error)
        (directory / FILES[0]).write_bytes(b'x' * len(self.blobs[FILES[0]]))
        model._refresh()
        self.assertEqual(model.status()['state'], 'error')

    def test_bad_import_preserves_previous_usable_set(self):
        directory = self.files(self.root / 'models')
        model = Models(directory)
        source = self.files(self.root / 'import')
        (source / FILES[1]).write_bytes(b'invalid voices')
        with self.assertRaises(ValueError):
            model.import_directory(source)
        self.assertEqual(model.status()['state'], 'ready')
        for name in FILES:
            self.assertEqual((directory / name).read_bytes(), self.blobs[name])

    def test_failed_second_replacement_rolls_back_first_and_keeps_backup_retryable(self):
        directory = self.files(self.root / 'models')
        model = Models(directory)
        source = self.files(self.root / 'import')
        old_pin = APPROVED[FILES[0]]
        changed = b'approved new CPU fixture'
        (source / FILES[0]).write_bytes(changed)
        APPROVED[FILES[0]] = (len(changed), hashlib.sha256(changed).hexdigest())
        original_replace = Path.replace

        def fail_second(path, target):
            if path.name == FILES[1] and path.parent.name.startswith('.model-stage-'):
                raise OSError('simulated replacement failure')
            return original_replace(path, target)

        with patch.object(Path, 'replace', fail_second), self.assertRaises(OSError):
            model.import_directory(source)
        APPROVED[FILES[0]] = old_pin
        self.assertEqual(Models(directory).status()['state'], 'ready')
        self.assertEqual((directory / FILES[0]).read_bytes(), self.blobs[FILES[0]])
        self.assertFalse((directory / '.model-rollback').exists())

    def test_restart_restores_a_pending_transaction(self):
        directory = self.files(self.root / 'models')
        backup = self.files(directory / '.model-rollback')
        (backup / 'state.json').write_text(json.dumps({'names': list(FILES), 'previous': list(FILES), 'state': 'pending'}))
        (directory / FILES[0]).write_bytes(b'interrupted replacement')
        self.assertEqual(Models(directory).status()['state'], 'ready')
        self.assertEqual((directory / FILES[0]).read_bytes(), self.blobs[FILES[0]])
        self.assertFalse(backup.exists())

    def test_invalid_recovery_journal_keeps_evidence_and_cannot_escape_root(self):
        directory = self.files(self.root / 'models')
        backup = directory / '.model-rollback'
        backup.mkdir()
        (backup / 'state.json').write_text(json.dumps({'names': ['../outside'], 'previous': [], 'state': 'pending'}))
        self.assertEqual(Models(directory).status()['state'], 'error')
        self.assertTrue(backup.exists())

    def test_download_uses_pins_without_accepting_remote_hash_claims(self):
        directory = self.root / 'models'
        model = Models(directory)
        with patch.object(model, '_open', side_effect=[io.BytesIO(self.blobs[FILES[0]]), io.BytesIO(b'unverified')]) as request:
            model._download()
        self.assertEqual(model.status()['state'], 'error')
        self.assertFalse((directory / FILES[0]).exists())
        self.assertEqual(request.call_args_list[0].args, (DOWNLOAD_ROOT + FILES[0],))
        with patch.object(model, '_open', side_effect=[io.BytesIO(self.blobs[name]) for name in FILES]):
            model._download()
        self.assertEqual(model.status()['state'], 'ready')

    def test_inference_does_not_open_an_unverified_model(self):
        directory = self.files(self.root / 'models')
        (directory / FILES[0]).write_bytes(b'x' * len(self.blobs[FILES[0]]))
        with patch('onnxruntime.InferenceSession') as parser:
            with self.assertRaises(ValueError):
                create_engine(directory / FILES[0], directory / FILES[1], {})
            parser.assert_not_called()

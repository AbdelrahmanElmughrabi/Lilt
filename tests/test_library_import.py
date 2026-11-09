import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend.instance import LibraryInUse, library_lock
from backend.storage import Store, import_library


class LibraryImportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = Store(self.root / 'source')
        self.document = self.source.document('# Keep these words', 'Keep')
        self.destination = self.root / 'destination'

    def tearDown(self):
        self.temporary.cleanup()

    def test_junction_content_is_rejected_before_any_copy(self):
        outside = self.root / 'outside'
        outside.mkdir()
        marker = outside / 'private-marker.txt'
        marker.write_text('fixture only')
        link = self.source.root / 'models' / 'linked'
        if os.name == 'nt':
            subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(link), str(outside)],
                           check=True, capture_output=True)
        else:
            link.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'link or junction'):
            import_library(self.source.root, self.destination)
        self.assertFalse(self.destination.exists())
        self.assertEqual(marker.read_text(), 'fixture only')
        self.assertFalse(list(self.root.glob('.violilt-migration-*')))

    def test_active_source_is_not_imported(self):
        with library_lock(self.source.root):
            with self.assertRaises(LibraryInUse):
                import_library(self.source.root, self.destination)
        self.assertFalse(self.destination.exists())

    def test_unmanaged_files_are_excluded(self):
        (self.source.root / 'unexpected.exe').write_bytes(b'fixture only')
        imported = Store(import_library(self.source.root, self.destination))
        self.assertEqual(imported.get('documents', self.document['id']), self.document)
        self.assertFalse((imported.root / 'unexpected.exe').exists())

    def test_source_changes_abandon_the_staged_copy(self):
        model = self.source.root / 'models' / 'fixture.bin'
        model.write_bytes(b'before')
        original = shutil.copytree

        def change_source(*args, **kwargs):
            result = original(*args, **kwargs)
            model.write_bytes(b'changed during copy')
            return result

        with patch('backend.storage.shutil.copytree', side_effect=change_source):
            with self.assertRaisesRegex(ValueError, 'changed during import'):
                import_library(self.source.root, self.destination)
        self.assertFalse(self.destination.exists())
        self.assertFalse(list(self.root.glob('.violilt-migration-*')))
        self.assertEqual(self.source.get('documents', self.document['id']), self.document)

    def test_low_disk_and_copy_limit_do_not_publish_partial_library(self):
        with patch('backend.storage.shutil.disk_usage', return_value=SimpleNamespace(free=0)):
            with self.assertRaisesRegex(ValueError, 'free space'):
                import_library(self.source.root, self.destination)
        with patch('backend.storage.MAX_LIBRARY_IMPORT_BYTES', 1):
            with self.assertRaisesRegex(ValueError, 'import limit'):
                import_library(self.source.root, self.destination)
        self.assertFalse(self.destination.exists())

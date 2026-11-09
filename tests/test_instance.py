import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from backend.instance import LibraryInUse, library_lock
from backend.storage import Store


class LibraryInstanceTests(unittest.TestCase):
    def test_second_instance_cannot_recover_or_modify_active_library(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with library_lock(root):
                store = Store(root)
                store.put('jobs', {'id': 'active-reading', 'state': 'generating'})
                original = store.db.read_bytes()
                with self.assertRaises(LibraryInUse):
                    with library_lock(root):
                        self.fail('Second instance entered the library')
                self.assertEqual(store.db.read_bytes(), original)
                self.assertEqual(store.get('jobs', 'active-reading')['state'], 'generating')
                with library_lock(root / 'separate-library'):
                    pass
            with library_lock(root):
                self.assertEqual(Store(root).get('jobs', 'active-reading')['state'], 'generating')

    def test_process_exit_releases_lock_without_deleting_library(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / 'keep.txt'
            marker.write_text('keep')
            code = ('import os,sys\nfrom pathlib import Path\n'
                    'from backend.instance import library_lock\n'
                    'with library_lock(Path(sys.argv[1])):\n'
                    ' print("locked",flush=True)\n'
                    ' sys.stdin.readline()\n'
                    ' os._exit(0)\n')
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            process = subprocess.Popen([sys.executable, '-c', code, str(root)],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True,
                                       cwd=Path(__file__).parents[1], creationflags=flags)
            try:
                self.assertEqual(process.stdout.readline().strip(), 'locked')
                with self.assertRaises(LibraryInUse):
                    with library_lock(root):
                        self.fail('Another process owns this library')
                process.communicate('\n', timeout=10)
                self.assertEqual(process.returncode, 0)
                with library_lock(root):
                    self.assertEqual(marker.read_text(), 'keep')
            finally:
                if process.poll() is None:
                    process.kill()
                process.communicate(timeout=10)


if __name__ == '__main__':
    unittest.main()

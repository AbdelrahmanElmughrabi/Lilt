import tempfile
import unittest
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from backend.storage import Store
from backend.server import AppServer


class StorageServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / 'data')
        assets = self.root / 'assets'
        assets.mkdir()
        (assets / 'index.html').write_text('Folio', encoding='utf-8')
        self.server = AppServer(assets, self.store)
        self.server.start()

    def tearDown(self):
        self.server.close()
        self.temp.cleanup()

    def test_document_copy_persists_across_store_instances(self):
        source = self.root / 'original.md'
        source.write_text('# Original', encoding='utf-8')
        doc = self.store.document('# Original', 'Original', str(source))
        self.store.document('# Changed', 'Changed', key=doc['id'])
        reopened = Store(self.store.root)
        self.assertEqual(reopened.get('documents', doc['id'])['markdown'], '# Changed')
        self.assertEqual(source.read_text(), '# Original')
        self.assertEqual(reopened.get('documents', doc['id'])['source'], str(source))

    def test_settings_remembered(self):
        self.store.save_settings({'theme': 'dark', 'speed': 1.2, 'include_code': True})
        self.assertEqual(Store(self.store.root).settings()['speed'], 1.2)

    def test_media_range_for_seeking_and_unknown_recording(self):
        key = uuid.uuid4().hex
        folder = self.store.root / 'jobs' / key
        folder.mkdir()
        (folder / 'recording.wav').write_bytes(b'0123456789')
        self.store.put('jobs', {'id': key, 'state': 'completed'})
        request = urllib.request.Request(f'{self.server.url}/media/{key}.wav', headers={'Range': 'bytes=2-5'})
        with urllib.request.urlopen(request) as response:
            self.assertEqual(response.status, 206)
            self.assertEqual(response.read(), b'2345')
            self.assertEqual(response.headers['Content-Range'], 'bytes 2-5/10')
        with self.assertRaises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(f'{self.server.url}/media/{uuid.uuid4().hex}.wav')
        self.assertEqual(error.exception.code, 404)

    def test_host_and_directory_traversal_rejected(self):
        for path, headers in [('/', {'Host': 'external.example'}), ('/%2e%2e/data/library.sqlite3', {})]:
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(urllib.request.Request(self.server.url + path, headers=headers))
            self.assertEqual(error.exception.code, 403)


if __name__ == '__main__':
    unittest.main()

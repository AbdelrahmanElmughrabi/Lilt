"""Source-preparation guards for a production environment without SoundFile."""
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import assemble_pronunciation_notices as notices


class NoticeAudioRetirementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name)

    def prepare(self):
        def response(request, **kwargs):
            name = request.full_url.split('/')[-3]
            return io.BytesIO(json.dumps({'urls':[{'packagetype':'sdist','url':'https://synthetic.invalid/'+name,
                'filename':name+'.tar.gz','digests':{'sha256':'synthetic'}}]}).encode())
        def fetch(url, path, digest=None):
            path.write_bytes(b'synthetic source placeholder')
            return {'filename':path.name,'url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        versions = dict.fromkeys(('num2words','certifi','tqdm','proxy_tools'), 'synthetic')
        with patch.object(notices, 'SOURCE_CACHE', self.cache), \
             patch.object(notices.metadata, 'version', side_effect=lambda name: versions[name]), \
             patch.object(notices.urllib.request, 'urlopen', side_effect=response), \
             patch.object(notices, 'fetch', side_effect=fetch), \
             patch.object(notices, 'prepare_eigen_source', return_value={
                 'component': 'onnxruntime-eigen', 'filename': 'synthetic-eigen.zip',
                 'sha256': 'synthetic-unit-fixture'}) as eigen:
            result = notices.prepare_sources()
            eigen.assert_called_once_with()
            return result

    def test_fresh_preparation_needs_no_soundfile_metadata_or_native_source(self):
        result = self.prepare()
        self.assertEqual({r['component'] for r in result}, {'num2words','certifi','tqdm','proxy_tools','onnxruntime-eigen'})

    def test_existing_audio_review_archives_are_preserved_and_pinned(self):
        old = []
        for component in ('soundfile','libsndfile'):
            path = self.cache/(component+'.tar.gz')
            path.write_bytes(b'preserved legacy review fixture')
            old.append({'component':component,'filename':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        (self.cache/'source-manifest.json').write_text(json.dumps(old))
        result = self.prepare()
        self.assertEqual([row for row in result if row['component'] in {'soundfile','libsndfile'}], old)
        self.assertEqual((self.cache/'libsndfile.tar.gz').read_bytes(), b'preserved legacy review fixture')

    def test_corrupt_legacy_archive_cannot_silently_replace_its_manifest(self):
        old = [{'component':'libsndfile','filename':'libsndfile.tar.gz','sha256':'wrong'}]
        (self.cache/'libsndfile.tar.gz').write_bytes(b'preserved')
        original = json.dumps(old)
        (self.cache/'source-manifest.json').write_text(original)
        with self.assertRaisesRegex(ValueError, 'Retained legacy audio'):
            self.prepare()
        self.assertEqual((self.cache/'source-manifest.json').read_text(), original)

"""Import titles survive the real save/job paths without running speech inference."""
from contextlib import contextmanager
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from backend.bridge import Bridge
from backend.jobs import Jobs
from backend.storage import Store
from tests.test_pdf_import import pdf_bytes


class ImportTitleTests(unittest.TestCase):
    @contextmanager
    def reading(self, suffix, text='# Literal source heading\n\nWords for a disposable reading.'):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / f'Imported reading.v2{suffix}'
            if suffix == '.pdf':
                source.write_bytes(pdf_bytes([text]))
            else:
                source.write_text(text, encoding='utf-8')
            original = source.read_bytes()
            store = Store(root / 'library')
            # Exercise real Jobs.start and SQLite job snapshots. Only the model,
            # runtime identity and inference startup are doubles; no models load.
            with patch('backend.jobs.threading.Thread'):
                jobs = Jobs(store, None)
            models = SimpleNamespace(root=root / 'fixture-models',
                                     status=lambda: {'state': 'ready', 'voices': ['af_heart']})
            jobs.models = models
            jobs.performance = SimpleNamespace(resolve=lambda settings: {
                'model': str(models.root / 'fixture.onnx'), 'provider': 'CPUExecutionProvider'})
            jobs._audio_identity = Mock(return_value=['disposable-runtime-identity'])
            jobs._worker = Mock()
            bridge = Bridge(store, models, jobs)
            try:
                result = bridge.import_dropped_documents([str(source)])
                self.assertEqual(result['errors'], [])
                document = result['documents'][0]
                yield bridge, jobs, store, document, source
            finally:
                jobs.close()
                for channel in (jobs.commands, jobs.events):
                    channel.cancel_join_thread()
                    channel.close()
                self.assertEqual(source.read_bytes(), original, 'Original import must stay byte-identical')

    def reopened(self, store, key):
        return Bridge(Store(store.root), None, None).get_document(key)

    def assert_job_title(self, bridge, jobs, store, document, markdown, title):
        created = bridge.generate(document['id'], markdown, store.settings())
        command = jobs.commands.get(timeout=2)
        restarted = Store(store.root)
        titles = {'returned job': created['title'],
                  'worker command': command['job']['title'],
                  'saved job': restarted.get('jobs', created['id'])['title'],
                  'reopened reading': self.reopened(store, document['id'])['title']}
        for stage, actual in titles.items():
            with self.subTest(stage=stage):
                self.assertEqual(actual, title)
        self.assertEqual(command['job']['markdown'], markdown)
        self.assertEqual(restarted.get('documents', document['id'])['markdown'], markdown)

    def test_imported_filename_survives_unchanged_edited_and_empty_saves(self):
        for suffix in ('.txt', '.pdf'):
            with self.subTest(format=suffix), self.reading(suffix) as (bridge, _, store, document, source):
                self.assertEqual(document['title'], source.stem)
                # The apparent source heading was imported literally, not as Markdown.
                for markdown in (document['markdown'], 'An ordinary edited paragraph.', ''):
                    with self.subTest(markdown=markdown):
                        saved = bridge.save_document(document['id'], markdown)
                        reopened = self.reopened(store, document['id'])
                        self.assertEqual(saved['title'], source.stem)
                        self.assertEqual(reopened['title'], source.stem)
                        self.assertEqual(reopened['markdown'], markdown)
                        self.assertEqual(reopened['source'], str(source))

    def test_direct_generation_keeps_imported_title_without_a_prior_save(self):
        for suffix in ('.txt', '.pdf'):
            with self.subTest(format=suffix), self.reading(suffix) as (bridge, jobs, store, document, source):
                self.assert_job_title(bridge, jobs, store, document, document['markdown'], source.stem)

    def test_save_reopen_then_generation_keeps_the_filename_in_job_titles(self):
        for suffix in ('.txt', '.pdf'):
            with self.subTest(format=suffix), self.reading(suffix) as (bridge, jobs, store, document, source):
                markdown = 'Saved and reopened words, without a heading.'
                bridge.save_document(document['id'], markdown)
                document = self.reopened(store, document['id'])
                self.assert_job_title(bridge, jobs, store, document, markdown, source.stem)

    def test_existing_title_is_preserved_even_when_different_from_the_filename(self):
        for suffix in ('.txt', '.pdf'):
            with self.subTest(format=suffix), self.reading(suffix) as (bridge, jobs, store, document, _):
                store.document(document['markdown'], 'Existing library title', key=document['id'])
                saved = bridge.save_document(document['id'], 'A paragraph without a heading.')
                self.assertEqual(saved['title'], 'Existing library title')
                self.assert_job_title(bridge, jobs, store, saved, saved['markdown'], 'Existing library title')

    def test_explicit_working_copy_heading_replaces_imported_title_on_save(self):
        for suffix in ('.txt', '.pdf'):
            with self.subTest(format=suffix), self.reading(suffix) as (bridge, _, store, document, _):
                saved = bridge.save_document(document['id'], '# Chosen **heading**\n\nNew words.')
                self.assertEqual(saved['title'], 'Chosen heading')
                self.assertEqual(self.reopened(store, document['id'])['title'], 'Chosen heading')

    def test_explicit_heading_controls_generation_and_saved_job_titles(self):
        for suffix in ('.txt', '.pdf'):
            for heading in ('# Chosen **heading**', '## Chosen heading', 'Chosen heading\n==='):
                with self.subTest(format=suffix, heading=heading), self.reading(suffix) as (bridge, jobs, store, document, _):
                    self.assert_job_title(bridge, jobs, store, document, heading + '\n\nNew words.', 'Chosen heading')

    def test_heading_removal_preserves_latest_title_for_existing_markdown(self):
        with self.reading('.md', '# Original heading\n\nOriginal words.') as (bridge, jobs, store, document, _):
            self.assertEqual(document['title'], 'Original heading')
            saved = bridge.save_document(document['id'], '# Replacement heading\n\nEdited words.')
            self.assertEqual(saved['title'], 'Replacement heading')
            bridge.save_document(document['id'], 'The heading has been removed.')
            self.assertEqual(self.reopened(store, document['id'])['title'], 'Replacement heading')
            self.assert_job_title(bridge, jobs, store, document, 'New generation without a heading.', 'Replacement heading')


if __name__ == '__main__':
    unittest.main()

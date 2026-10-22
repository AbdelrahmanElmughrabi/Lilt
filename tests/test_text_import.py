"""TXT imports use disposable files and the existing editable reading format."""
import codecs
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from backend.bridge import Bridge
from backend.documents import prepare
from backend.limits import MAX_FILE_BATCH, MAX_MARKDOWN_BYTES
from backend.speech_text import normalize_symbols
from backend.storage import Store


class TextImportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = Store(self.root / 'library')
        self.bridge = Bridge(self.store, None, None)

    def import_path(self, source):
        result = self.bridge.import_dropped_documents([str(source)])
        self.assertEqual(result['errors'], [], result)
        self.assertEqual(len(result['documents']), 1)
        return result['documents'][0]

    def test_picker_supports_unicode_encodings_without_changing_originals(self):
        text = 'A little reading.\r\n\r\nTurkish characters: ş, ğ, ı. Café.'
        bodies = [text.encode('utf-8'), text.encode('utf-8-sig'),
                  codecs.BOM_UTF16_LE + text.encode('utf-16-le'),
                  codecs.BOM_UTF16_BE + text.encode('utf-16-be')]
        for index, body in enumerate(bodies):
            with self.subTest(encoding=index):
                source = self.root / f'Reading {index}.TXT'
                source.write_bytes(body)
                self.bridge._window = Mock()
                self.bridge._window.create_file_dialog.return_value = (str(source),)
                try:
                    document = self.bridge.import_document()
                except ValueError as error:
                    self.fail(f'A supported Unicode TXT file was rejected: {error}')
                filters = self.bridge._window.create_file_dialog.call_args.kwargs['file_types']
                self.assertIn('*.txt', ' '.join(filters))
                self.assertEqual(document['title'], source.stem)
                self.assertEqual(document['source'], str(source))
                self.assertEqual(prepare(document['markdown'])['text'], text.replace('\r\n', '\n'))
                self.bridge.save_document(document['id'], document['markdown'] + '\n\nAn edit.')
                self.assertEqual(source.read_bytes(), body)

    def test_txt_remains_literal_in_spoken_chunks_and_saved_working_copy(self):
        text = ('---\nauthor: keep this metadata\n---\n\n'
                '# Literal heading\n\n```python\nkeep_this_code()\n```\n\n'
                '    Indented words stay.\n\n\tTabbed words stay too.\n\n'
                '<script>keep this script text</script>\n\n'
                '<style>keep this style text</style>\n\n'
                '[visible label](https://example.invalid/keep-target)\n\n'
                '<https://example.invalid/keep-autolink>\n\n'
                '![alt text](keep-image.png)\n\n'
                'Name | Value\n--- | ---\nkeep_table | keep_cell\n\n'
                '**keep emphasis** &copy; &#65; \\keep_backslash\n\n'
                '1. Numbered words\n> Quoted words\n- Listed words\n')
        source = self.root / 'Literal note.txt'
        source.write_text(text, encoding='utf-8')
        original = source.read_bytes()
        document = self.import_path(source)
        prepared = prepare(document['markdown'], {'include_code': False})
        expected, _ = normalize_symbols(' '.join(text.split()))
        self.assertEqual(' '.join(prepared['text'].split()), expected)
        self.assertEqual(' '.join(chunk['text'] for chunk in prepared['chunks']), expected)
        self.assertEqual(prepared['omissions'], {'code_blocks': 0, 'metadata': 0})
        self.assertEqual(document['title'], source.stem)
        self.assertTrue(all(block['kind'] == 'paragraph' for block in prepared['blocks']))
        saved = self.bridge.save_document(document['id'], document['markdown'])
        reopened = Bridge(Store(self.store.root), None, None).get_document(document['id'])
        self.assertEqual(reopened['markdown'], saved['markdown'])
        self.assertEqual(reopened['source'], str(source))
        self.assertEqual(prepare(reopened['markdown'])['text'], prepared['text'])
        self.assertEqual(source.read_bytes(), original)

    def test_mixed_drop_keeps_markdown_behavior_and_reports_individual_errors(self):
        text, markdown, other_markdown = (self.root / name for name in ('plain.txt', 'note.MD', 'more.markdown'))
        text.write_text('# Literal heading\n\n```\nKeep this code.\n```', encoding='utf-8')
        markdown.write_bytes(b'\xef\xbb\xbf# Markdown heading\n\n```\nOmit this code.\n```')
        other_markdown.write_text('# Another heading', encoding='utf-8')
        bad, unsupported = self.root / 'legacy.txt', self.root / 'later.pdf'
        bad.write_bytes('ş'.encode('cp1254'))
        unsupported.write_bytes(b'disposable unsupported document')
        folder = self.root / 'folder.txt'
        folder.mkdir()
        paths = [text, markdown, other_markdown, text, bad, unsupported, folder, self.root / 'missing.txt']
        originals = {path: path.read_bytes() for path in paths if path.is_file()}
        result = self.bridge.import_dropped_documents([str(path) for path in paths])
        self.assertEqual([doc['title'] for doc in result['documents']], ['plain', 'Markdown heading', 'Another heading'])
        self.assertEqual([error['name'] for error in result['errors']], ['legacy.txt', 'later.pdf', 'folder.txt', 'missing.txt'])
        self.assertEqual(len(self.store.all('documents')), 3)
        self.assertEqual(result['documents'][1]['markdown'], markdown.read_text(encoding='utf-8-sig'))
        self.assertEqual(prepare(result['documents'][1]['markdown'])['omissions']['code_blocks'], 1)
        for path, body in originals.items():
            self.assertEqual(path.read_bytes(), body)

    @patch('backend.bridge.select_file')
    def test_reveal_txt_original_after_edit_and_restart(self, select):
        source = self.root / 'notes, with spaces & symbols.txt'
        source.write_text('Original text.', encoding='utf-8')
        # Saved source metadata already supports TXT without any schema extension.
        document = self.store.document('Original text.', 'notes', source=str(source))
        self.bridge.save_document(document['id'], '# Edited working copy')
        bridge = Bridge(Store(self.store.root), None, None)
        try:
            self.assertTrue(bridge.reveal_document(document['id']))
        except ValueError as error:
            self.fail(f'The saved TXT original could not be revealed: {error}')
        select.assert_called_once_with(source)
        self.assertEqual(source.read_text(encoding='utf-8'), 'Original text.')
        source.unlink()
        with self.assertRaises(ValueError):
            bridge.reveal_document(document['id'])
        select.assert_called_once()

    def test_invalid_or_unmarked_encodings_fail_before_library_mutation(self):
        bodies = [b'caf\xe9', b'\xff\xfe\x41', b'\xfe\xff\xd8\x00',
                  b'A\x00B\x00', b'\x00A\x00B',
                  codecs.BOM_UTF32_LE + 'Words'.encode('utf-32-le'),
                  codecs.BOM_UTF32_BE + 'Words'.encode('utf-32-be')]
        for index, body in enumerate(bodies):
            with self.subTest(encoding=index):
                source = self.root / f'invalid-{index}.txt'
                source.write_bytes(body)
                with self.assertRaisesRegex(ValueError, 'UTF-8.*UTF-16'):
                    self.bridge._import_document_path(source)
                self.assertEqual(self.store.all('documents'), [])
                self.assertEqual(source.read_bytes(), body)

    def test_source_and_converted_size_limits_apply_before_parsing_or_writes(self):
        bodies = [b'x' * (MAX_MARKDOWN_BYTES + 1),
                  b'*' * (MAX_MARKDOWN_BYTES // 2 + 1),
                  codecs.BOM_UTF16_LE + ('漢' * (MAX_MARKDOWN_BYTES // 3 + 1)).encode('utf-16-le')]
        for index, body in enumerate(bodies):
            with self.subTest(limit=index):
                source = self.root / f'oversize-{index}.txt'
                source.write_bytes(body)
                with patch('backend.bridge.prepare') as parser:
                    with self.assertRaisesRegex(ValueError, '2 MB'):
                        self.bridge._import_document_path(source)
                    parser.assert_not_called()
                self.assertEqual(self.store.all('documents'), [])
                self.assertEqual(source.read_bytes(), body)
        with self.assertRaises(ValueError):
            self.bridge.import_dropped_documents([str(source)] * (MAX_FILE_BATCH + 1))
        self.assertEqual(self.store.all('documents'), [])

    def test_empty_txt_and_line_endings_keep_paragraphs_without_omissions(self):
        for index, text in enumerate(('', ' \t\r\n', 'First line.\rSecond line.\r\rThird paragraph.')):
            with self.subTest(text=index):
                source = self.root / f'paragraphs-{index}.txt'
                source.write_bytes(codecs.BOM_UTF8 + text.encode('utf-8'))
                prepared = prepare(self.import_path(source)['markdown'])
                self.assertEqual(prepared['text'], 'First line. Second line.\n\nThird paragraph.' if index == 2 else '')
                self.assertEqual(prepared['omissions'], {'code_blocks': 0, 'metadata': 0})

    def test_exact_file_and_batch_boundaries_are_accepted(self):
        source = self.root / 'boundary.txt'
        source.write_bytes(b'x' * MAX_MARKDOWN_BYTES)
        # The parser's own size bound is covered separately; isolate file admission here.
        with patch('backend.bridge.prepare', return_value={'title': 'boundary'}):
            document = self.import_path(source)
        self.assertEqual(len(document['markdown'].encode('utf-8')), MAX_MARKDOWN_BYTES)
        paths = []
        for index in range(MAX_FILE_BATCH):
            path = self.root / f'batch-{index}.txt'
            path.write_text('A small disposable reading.', encoding='utf-8')
            paths.append(str(path))
        result = self.bridge.import_dropped_documents(paths)
        self.assertEqual(result['errors'], [])
        self.assertEqual(len(result['documents']), MAX_FILE_BATCH)
        before = len(self.store.all('documents'))
        with self.assertRaises(ValueError):
            self.bridge.import_dropped_documents(paths + [str(source)])
        self.assertEqual(len(self.store.all('documents')), before)


if __name__ == '__main__':
    unittest.main()

"""Selectable-text PDF imports use generated fixtures and disposable libraries."""
import io
import multiprocessing
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, NumberObject, DecodedStreamObject

from backend.bridge import Bridge
from backend import pdf_import
from backend.documents import prepare
from backend.speech_text import normalize_symbols
from backend.storage import Store


def stalled_worker(*args):
    time.sleep(30)


def crashed_worker(*args):
    os._exit(17)


def invalid_response_worker(body, connection, *args):
    connection.send_bytes(b'not JSON')
    connection.close()


def pdf_bytes(pages, *, encrypted=False):
    """Build small, real PDFs without another test-only dependency."""
    writer = PdfWriter()
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                             NameObject('/Subtype'): NameObject('/Type1'),
                             NameObject('/BaseFont'): NameObject('/Helvetica'),
                             NameObject('/Encoding'): NameObject('/WinAnsiEncoding')})
    for text in pages:
        page = writer.add_blank_page(width=612, height=792)
        if text is None:
            # An image-only page, deliberately without a hidden text layer.
            image = DecodedStreamObject()
            image.set_data(b'\x70\x90\xb0')
            image.update({NameObject('/Type'): NameObject('/XObject'),
                          NameObject('/Subtype'): NameObject('/Image'),
                          NameObject('/Width'): NumberObject(1), NameObject('/Height'): NumberObject(1),
                          NameObject('/ColorSpace'): NameObject('/DeviceRGB'),
                          NameObject('/BitsPerComponent'): NumberObject(8)})
            page[NameObject('/Resources')] = DictionaryObject({NameObject('/XObject'):
                DictionaryObject({NameObject('/Image'): writer._add_object(image)})})
            content = b'q 200 0 0 200 72 450 cm /Image Do Q'
        else:
            page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):
                DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
            lines = []
            for line in text.split('\n'):
                escaped = line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
                lines.append(f'({escaped}) Tj T*')
            content = ('BT /F1 12 Tf 16 TL 72 720 Td ' + ' '.join(lines) + ' ET').encode('cp1252')
        stream = DecodedStreamObject()
        stream.set_data(content)
        page[NameObject('/Contents')] = writer._add_object(stream)
        page.compress_content_streams()
    if encrypted:
        # Reject encryption even if an empty password could open it.
        writer.encrypt('', owner_password='disposable-owner-password')
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


class PdfImportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.store = Store(self.root / 'library')
        self.bridge = Bridge(self.store, None, None)

    def source(self, name, pages, **kwargs):
        path = self.root / name
        path.write_bytes(pdf_bytes(pages, **kwargs))
        return path

    def import_path(self, path):
        result = self.bridge.import_dropped_documents([str(path)])
        self.assertEqual(result['errors'], [], result)
        self.assertEqual(len(result['documents']), 1)
        return result['documents'][0]

    def test_picker_imports_pages_as_literal_editable_text_and_keeps_original(self):
        pages = ['# Literal heading\n```\nKeep this code.\n```\n<script>Keep these words.</script>',
                 'Second page. Café.\n[Keep link](https://example.invalid/read) &copy;']
        path = self.source('Two pages.PDF', pages)
        before = path.read_bytes()
        self.bridge._window = Mock()
        self.bridge._window.create_file_dialog.return_value = (str(path),)
        try:
            document = self.bridge.import_document()
        except ValueError as error:
            self.fail(f'A selectable-text PDF was rejected: {error}')
        self.assertIn('*.pdf', ' '.join(self.bridge._window.create_file_dialog.call_args.kwargs['file_types']))
        self.assertEqual(document['title'], path.stem)
        self.assertEqual(document['source'], str(path))
        prepared = prepare(document['markdown'])
        expected, _ = normalize_symbols(' '.join(' '.join(pages).split()))
        self.assertEqual(' '.join(prepared['text'].split()), expected)
        self.assertEqual(prepared['omissions'], {'code_blocks': 0, 'metadata': 0})
        self.assertTrue(all(block['kind'] == 'paragraph' for block in prepared['blocks']))
        self.assertIn('\n\nSecond page.', prepared['text'])
        saved = self.bridge.save_document(document['id'], document['markdown'] + '\n\nAn edit.')
        reopened = Bridge(Store(self.store.root), None, None).get_document(document['id'])
        self.assertEqual(reopened['markdown'], saved['markdown'])
        self.assertEqual(reopened['source'], str(path))
        self.assertEqual(path.read_bytes(), before)

    def test_mixed_drop_keeps_successes_deduplicates_and_reports_pdf_failures(self):
        pdf = self.source('selectable.pdf', ['A PDF reading.'])
        text, markdown = self.root / 'plain.txt', self.root / 'note.md'
        text.write_text('# Literal TXT', encoding='utf-8')
        markdown.write_text('# Markdown title', encoding='utf-8')
        scanned = self.source('scan.pdf', [None])
        encrypted = self.source('locked.pdf', ['Secret fixture.'], encrypted=True)
        malformed = self.root / 'broken.pdf'
        malformed.write_bytes(b'%PDF-1.7\nnot a document')
        paths = [pdf, text, markdown, pdf, scanned, encrypted, malformed]
        before = {path: path.read_bytes() for path in paths}
        result = self.bridge.import_dropped_documents([str(path) for path in paths])
        self.assertEqual([doc['title'] for doc in result['documents']], ['selectable', 'plain', 'Markdown title'])
        self.assertEqual([error['name'] for error in result['errors']], ['scan.pdf', 'locked.pdf', 'broken.pdf'])
        for message, expected in zip(result['errors'], ['selectable text', 'encrypted', 'could not']):
            self.assertIn(expected, message['message'].lower())
        self.assertEqual(len(self.store.all('documents')), 3)
        for path, body in before.items():
            self.assertEqual(path.read_bytes(), body)

    def test_blank_and_image_only_pdfs_are_rejected_without_library_mutation(self):
        for name, pages in [('blank.pdf', ['']), ('scan.pdf', [None]), ('zero.pdf', [])]:
            with self.subTest(name=name):
                path = self.source(name, pages)
                with self.assertRaisesRegex(ValueError, 'selectable text'):
                    self.bridge._import_document_path(path)
                self.assertEqual(self.store.all('documents'), [])

    def test_text_on_either_side_of_an_image_only_page_is_kept_in_order(self):
        document = self.import_path(self.source('mixed.pdf', ['First page.', None, 'Last page.']))
        self.assertEqual(prepare(document['markdown'])['text'], 'First page.\n\nLast page.')

    def test_pdf_source_and_page_limits_reject_before_library_writes(self):
        path = self.root / 'oversize.pdf'
        with path.open('wb') as output:
            output.write(b'%PDF-1.7\n')
            output.truncate(20 * 1024 * 1024 + 1)
        with patch('backend.bridge.prepare') as parser:
            with self.assertRaisesRegex(ValueError, '20 MB'):
                self.bridge._import_document_path(path)
            parser.assert_not_called()
        path = self.source('too-many-pages.pdf', ['Small.'] * 201)
        with patch('backend.bridge.prepare') as parser:
            with self.assertRaisesRegex(ValueError, '200 pages'):
                self.bridge._import_document_path(path)
            parser.assert_not_called()
        self.assertEqual(self.store.all('documents'), [])

    @patch('backend.bridge.select_file')
    def test_reveal_pdf_original_after_edit_and_restart(self, select):
        path = self.source('original, with spaces.pdf', ['Original.'])
        before = path.read_bytes()
        document = self.store.document('Original.', 'original', source=str(path))
        self.bridge.save_document(document['id'], '# Edited working copy')
        try:
            self.assertTrue(Bridge(Store(self.store.root), None, None).reveal_document(document['id']))
        except ValueError as error:
            self.fail(f'The PDF original could not be revealed: {error}')
        select.assert_called_once_with(path)
        self.assertEqual(path.read_bytes(), before)

    def test_text_and_escaped_working_copy_limits_precede_parsing_and_writes(self):
        for text, target, limit, message in [
            ('Long text over the extraction limit.', 'backend.pdf_import.MAX_MARKDOWN_BYTES', 16, '2 MB of text'),
            ('*' * 20, 'backend.limits.MAX_MARKDOWN_BYTES', 32, 'PDF file.*editable working copy'),
        ]:
            with self.subTest(limit=target):
                path = self.source('expanded.pdf', [text])
                with patch(target, limit), patch('backend.bridge.prepare') as parser:
                    with self.assertRaisesRegex(ValueError, message):
                        self.bridge._import_document_path(path)
                    parser.assert_not_called()
                self.assertEqual(self.store.all('documents'), [])

    def test_exact_page_and_extracted_text_boundaries_are_accepted(self):
        path = self.source('boundary-pages.pdf', ['A.'] * 200)
        self.assertEqual(prepare(self.import_path(path)['markdown'])['text'].count('A.'), 200)
        with patch('backend.pdf_import.MAX_MARKDOWN_BYTES', 16):
            self.assertEqual(pdf_import.extract_pdf_text(pdf_bytes(['x' * 16])), 'x' * 16)

    def test_source_bound_is_independent_of_the_smaller_editable_text_limit(self):
        path = self.source('large-source.pdf', ['A small text layer.'])
        # Source admission is independent of PDF syntax; isolate that boundary.
        with path.open('ab') as output:
            output.truncate(20 * 1024 * 1024)
        with patch('backend.bridge.extract_pdf_text', return_value='A small text layer.') as extract:
            document = self.import_path(path)
        self.assertEqual(len(extract.call_args.args[0]), 20 * 1024 * 1024)
        self.assertEqual(prepare(document['markdown'])['text'], 'A small text layer.')

    def test_stalled_and_memory_limited_workers_are_stopped_without_writes(self):
        path = self.source('resource-test.pdf', ['A reading.'])
        cases = [('backend.pdf_import.PDF_TIMEOUT_SECONDS', 0.15, 'too long'),
                 ('backend.pdf_import.PDF_MEMORY_BYTES', 1, 'too much memory')]
        for target, limit, message in cases:
            with self.subTest(limit=target):
                started = time.monotonic()
                with patch('backend.pdf_import._extract_worker', stalled_worker), patch(target, limit):
                    with self.assertRaisesRegex(ValueError, message):
                        self.bridge._import_document_path(path)
                self.assertLess(time.monotonic() - started, 10)
                self.assertEqual(self.store.all('documents'), [])
                self.assertFalse(any(child.name == 'Violilt PDF import' for child in multiprocessing.active_children()))
        # A stopped extraction must release the lock and allow the next import.
        self.assertEqual(prepare(self.import_path(path)['markdown'])['text'], 'A reading.')

    def test_crashed_or_invalid_worker_responses_fail_cleanly_and_allow_retry(self):
        path = self.source('worker-error.pdf', ['Retry works.'])
        for worker in (crashed_worker, invalid_response_worker):
            with self.subTest(worker=worker.__name__):
                with patch('backend.pdf_import._extract_worker', worker):
                    result = self.bridge.import_dropped_documents([str(path)])
                self.assertEqual(result['documents'], [])
                self.assertIn('could not be read', result['errors'][0]['message'])
                self.assertEqual(self.store.all('documents'), [])
                self.assertFalse(any(child.name == 'Violilt PDF import' for child in multiprocessing.active_children()))
        self.assertEqual(prepare(self.import_path(path)['markdown'])['text'], 'Retry works.')


if __name__ == '__main__':
    unittest.main()

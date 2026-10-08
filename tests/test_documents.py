import unittest

from backend.documents import prepare


class MarkdownTests(unittest.TestCase):
    def test_readable_structure_and_omissions(self):
        result = prepare('---\nauthor: test\n---\n# Hello\n\nA **bold** [link](https://example.org) and `value`.\n\n- One\n- Two\n\n```py\nsecret()\n```\n')
        self.assertEqual(result['text'], 'Hello\n\nA bold link and value.\n\nOne\n\nTwo')
        self.assertEqual(result['omissions'], {'code_blocks': 1, 'metadata': 1})

    def test_include_code_is_explicit(self):
        self.assertNotIn('print', prepare('# Test\n\n```py\nprint("hi")\n```')['text'])
        self.assertIn('print', prepare('# Test\n\n```py\nprint("hi")\n```', {'include_code': True})['text'])

    def test_every_word_covered_once_in_long_unpunctuated_text(self):
        original = ' '.join(f'word{i}' for i in range(4000))
        result = prepare(original)
        self.assertGreater(len(result['chunks']), 50)
        self.assertEqual(' '.join(c['text'] for c in result['chunks']), original)

    def test_markdown_tables_and_alt_text(self):
        result = prepare('| Name | Count |\n| --- | --- |\n| Apple | 2 |\n\n![An apple](https://example.org/image.png)')
        self.assertEqual(result['text'], 'Name; Count.\n\nApple; 2.\n\nAn apple')

    def test_html_is_extracted_without_execution(self):
        result = prepare('<div>Hello <strong>world</strong>.</div>\n\n<script>steal()</script>')
        self.assertEqual(result['text'], 'Hello world.')

    def test_inline_scripts_and_styles_are_omitted_from_speech(self):
        result = prepare('Hello <script>private()</script> <style>body {color: red;}</style> **world**.')
        self.assertEqual(result['text'], 'Hello world.')

    def test_empty_or_code_only_document_has_no_sections(self):
        self.assertEqual(prepare('')['chunks'], [])
        self.assertEqual(prepare('```\ncode\n```')['chunks'], [])

    def test_heading_pause_is_only_on_last_section(self):
        result = prepare('# ' + ' '.join(['Heading'] * 120), {'heading_pause': 1.1})
        self.assertGreater(len(result['chunks']), 1)
        self.assertEqual(result['chunks'][-1]['pause'], 1.1)
        self.assertEqual(result['chunks'][0]['pause'], 0.12)


if __name__ == '__main__':
    unittest.main()

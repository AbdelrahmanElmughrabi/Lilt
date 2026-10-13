import unittest
from unittest.mock import patch

from backend.documents import prepare
from backend.speech_text import SYMBOL_NAMES, normalize_symbols, symbol_identity


class SymbolPreparationTests(unittest.TestCase):
    def test_names_replace_only_the_listed_symbol(self):
        speech, unread = normalize_symbols('A➔B × C ≤ D. Next sentence stays.')
        self.assertEqual(speech, 'A right arrow B multiplication sign C less than or equal to D. Next sentence stays.')
        self.assertEqual(unread, [])

    def test_unlisted_symbols_preserve_every_surrounding_word_and_sentence(self):
        for source, expected in [('🦊First sentence. Next sentence.', 'First sentence. Next sentence.'),
                                 ('First🦊sentence. Next sentence.', 'First sentence. Next sentence.'),
                                 ('First sentence.🦊 Next sentence.🦊', 'First sentence. Next sentence.')]:
            with self.subTest(source=source):
                speech, unread = normalize_symbols(source)
                self.assertEqual(speech, expected)
                self.assertEqual(unread, ['🦊'] * source.count('🦊'))

    def test_multiple_symbols_and_joined_words(self):
        self.assertEqual(normalize_symbols('one🦊🐙two ➔ three'),
                         ('one two right arrow three', ['🦊', '🐙']))

    def test_compound_emoji_is_omitted_without_consuming_adjacent_letters(self):
        self.assertEqual(normalize_symbols('one👨‍👩‍👧two 🇬🇧three'),
                         ('one two three', ['👨‍👩‍👧', '🇬🇧']))

    def test_accent_on_an_unlisted_graphic_is_not_left_to_break_pronunciation(self):
        self.assertEqual(normalize_symbols('Hello 🦊́ world. café stays.'),
                         ('Hello world. café stays.', ['🦊́']))

    def test_variation_selectors_do_not_break_listed_arrows(self):
        self.assertEqual(normalize_symbols('A➔️B ☀️C'), ('A right arrow B C', ['☀️']))

    def test_decorated_digits_and_letters_retain_their_base(self):
        self.assertEqual(normalize_symbols('Take 1️⃣ and a⃝ today.'),
                         ('Take 1 and a today.', ['\ufe0f\u20e3', '\u20dd']))

    def test_letters_numbers_and_accents_are_never_classified_as_unread_symbols(self):
        source = 'cafe\u0301 naïve café λ 中文 Ⅳ 123'
        self.assertEqual(normalize_symbols(source), (source, []))

    def test_existing_punctuation_currency_numbers_and_ascii_syntax_are_preserved(self):
        source = '“Hello”—don’t stop… $12.50 £3 €4 1/2 2026-10-14 foo_bar a@b.com [x](/y/)'
        self.assertEqual(normalize_symbols(source), (source, []))

    def test_controls_are_logged_and_separate_words(self):
        self.assertEqual(normalize_symbols('one\x00two\u200bthree\tend'),
                         ('one two three end', ['\x00', '\u200b']))

    def test_cleaned_text_is_idempotent(self):
        speech, _ = normalize_symbols('A➔B 🦊 café 1️⃣. $12.50')
        self.assertEqual(normalize_symbols(speech), (speech, []))

    def test_table_change_changes_policy_identity(self):
        original = symbol_identity()
        with patch.dict(SYMBOL_NAMES, {'➔': 'different arrow'}):
            self.assertNotEqual(symbol_identity(), original)
        self.assertEqual(symbol_identity(), original)

    def test_title_is_original_but_preview_and_chunks_are_cleaned(self):
        markdown = '# Original ➔ title\n\nA➔B 🦊 C. Next sentence stays.'
        result = prepare(markdown)
        self.assertEqual(result['title'], 'Original ➔ title')
        self.assertEqual(markdown, '# Original ➔ title\n\nA➔B 🦊 C. Next sentence stays.')
        self.assertEqual(result['text'], 'Original right arrow title\n\nA right arrow B C. Next sentence stays.')
        self.assertEqual(result['unread_symbols'], ['🦊'])
        self.assertEqual(result['unread_count'], 1)
        self.assertEqual(' '.join(c['text'] for c in result['chunks']), result['text'].replace('\n\n', ' '))

    def test_empty_blocks_have_no_empty_audio_sections_or_missing_following_words(self):
        result = prepare('🦊\n\nHello.\n\n🐙\n\nNext sentence.')
        self.assertEqual([c['text'] for c in result['chunks']], ['Hello.', 'Next sentence.'])
        self.assertEqual([c['block'] for c in result['chunks']], [1, 3])
        self.assertEqual(result['text'], 'Hello.\n\nNext sentence.')
        self.assertEqual(result['unread_symbols'], ['🦊', '🐙'])
        self.assertEqual(prepare('🦊')['chunks'], [])
        self.assertEqual(prepare('🦊')['words'], 0)

    def test_omitted_code_and_metadata_are_not_added_to_unread(self):
        result = prepare('---\nauthor: 🦊\n---\nHello.\n\n```\n🐙\n```')
        self.assertEqual(result['unread_symbols'], [])
        self.assertEqual(result['omissions'], {'code_blocks': 1, 'metadata': 1})
        self.assertEqual(prepare('```\n🐙\n```', {'include_code': True})['unread_symbols'], ['🐙'])

    def test_tables_alt_text_inline_code_html_and_literal_bullets_use_same_pass(self):
        result = prepare('| Item | Action |\n| --- | --- |\n| A | ➔ B 🦊 |\n\n'
                         '![Alt 🐙 text](image.png)\n\n`one➔two`\n\n<div>Three ☀ four.</div>\n\n• Five')
        self.assertEqual(result['text'], 'Item; Action.\n\nA; right arrow B .\n\n'
                         'Alt text\n\none right arrow two\n\nThree four.\n\nbullet Five')
        self.assertEqual(result['unread_symbols'], ['🦊', '🐙', '☀'])


if __name__ == '__main__':
    unittest.main()

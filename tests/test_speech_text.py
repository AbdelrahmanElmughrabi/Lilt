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
        self.assertEqual(normalize_symbols(source),
                         (source.replace('[x](/y/)', '[ x ] ( /y/ )'), []))

    def test_function_calls_and_assignments_get_spacing_without_word_rewriting(self):
        for source, expected in [('pet = generate(seed, version).', 'pet = generate ( seed, version ).'),
                                 ('body=3,earStyle=1,tailType=5,colorHue=210.',
                                  'body = 3, earStyle = 1, tailType = 5, colorHue = 210.')]:
            self.assertEqual(normalize_symbols(source), (expected, []))
            self.assertEqual(''.join(source.split()), ''.join(expected.split()))

    def test_brackets_and_commas_remain_characters_without_spoken_names(self):
        self.assertEqual(normalize_symbols('{body=3} [seed,version].'),
                         ('{ body = 3 } [ seed, version ].', []))
        self.assertEqual(normalize_symbols('seed,version'), ('seed, version', []))
        self.assertEqual(normalize_symbols('eyeCount>2 <path>'), ('eyeCount > 2 < path >', []))

    def test_numeric_commas_decimals_currency_signs_and_ranges_are_protected(self):
        source = 'Values[0,0,0,…] 1,000 12.050 $12.50 £3.40 €4.20 –0.1 1–5 ~10 2026-10-14'
        self.assertEqual(normalize_symbols(source), (source.replace('Values[0,0,0,…]', 'Values [ 0,0,0, … ]'), []))

    def test_straight_and_curly_apostrophes_and_quotes_are_untouched(self):
        source = "Don't change John's words. Don’t change John’s words. 'seed' “version”"
        self.assertEqual(normalize_symbols(source), (source, []))
        self.assertEqual(normalize_symbols("body='seed'"), ("body = 'seed'", []))

    def test_common_addresses_keep_query_operators_grouping_and_numeric_commas(self):
        for source in ('https://example.com/f(seed)?a=3&v=1,000', 'www.example.com/f(seed)?a=3',
                       'name+tag=field@example.com', "o'brien@example.com"):
            self.assertEqual(normalize_symbols(source), (source, []))
        self.assertEqual(normalize_symbols('(name@example.com)'), ('( name@example.com )', []))

    def test_spacing_is_idempotent_and_long_words_are_preserved(self):
        source = "pet=generate(seed,version), John's body=3; https://example.com?a=3"
        prepared, _ = normalize_symbols(source)
        self.assertEqual(normalize_symbols(prepared), (prepared, []))
        long_word = 'a' * 20000
        self.assertEqual(normalize_symbols(long_word), (long_word, []))

    def test_spacing_rules_are_part_of_policy_identity(self):
        original = symbol_identity()
        with patch('backend.speech_text._SPACING_MARKS', frozenset('=()')):
            self.assertNotEqual(symbol_identity(), original)

    def test_original_code_title_and_spoken_job_text_use_the_correct_copies(self):
        markdown = '# generate(seed)\n\n`body=3,earStyle=1`'
        prepared = prepare(markdown)
        self.assertEqual(prepared['title'], 'generate(seed)')
        self.assertEqual(prepared['text'], 'generate ( seed )\n\nbody = 3, earStyle = 1')
        self.assertEqual(' '.join(chunk['text'] for chunk in prepared['chunks']),
                         prepared['text'].replace('\n\n', ' '))
        self.assertEqual(prepared['unread_count'], 0)

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

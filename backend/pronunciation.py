"""Local English pronunciation with explicit coverage and artifact identity.

Misaki 0.9.4 is loaded without its English extra or its downloading constructor.
Unknown English words are spelled instead of being silently omitted. Third-party
code and dictionary licenses remain attached to their installed distributions.
"""
from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import hashlib
import importlib.metadata
from pathlib import Path
import re
import unicodedata

from .speech_text import symbol_identity


MISAKI_VERSION = '0.9.4'
MODEL_PACKAGE = 'en_core_web_sm'
MODEL_VERSION = '3.8.0'
PRONUNCIATION_REVISION = 'lilt-misaki-english-v3'
FALLBACK_POLICY = 'latin-english-contextual-punctuation-and-spelling-v2'
ADAPTER_REVISION = 'lilt-kokoro-0.6.1-v1'
_LEXICONS = ('gb_gold.json', 'gb_silver.json', 'us_gold.json', 'us_silver.json')
_CODE_PACKAGES = ('misaki', 'spacy', 'thinc', 'regex', 'addict', 'numpy', 'num2words')
_LOADED_CODE_IDENTITY = None


class PronunciationError(ValueError):
    """Text or local pronunciation assets cannot be read safely."""


def _distribution(name):
    try:
        return importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError:
        return None


@lru_cache(maxsize=64)
def _hash_snapshot(snapshot):
    """Hash content once for each set of file sizes and modification times."""
    digest = hashlib.sha256()
    for relative, absolute, size, modified in snapshot:
        digest.update(relative.encode('utf-8'))
        digest.update(b'\0')
        with Path(absolute).open('rb') as source:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(block)
    return digest.hexdigest()


def _content_identity(root, paths):
    snapshot = []
    try:
        for path in sorted(paths):
            stat = path.stat()
            snapshot.append((path.relative_to(root).as_posix(), str(path.resolve()), stat.st_size, stat.st_mtime_ns))
        return _hash_snapshot(tuple(snapshot)) if snapshot else 'missing'
    except OSError:
        return 'missing'


def _payload_files(root, suffix=None):
    if not root.is_dir():
        return []
    return [path for path in root.rglob('*') if path.is_file()
            and '__pycache__' not in path.parts and path.suffix not in {'.pyc', '.pyo'}
            and (suffix is None or path.suffix == suffix)]


def pronunciation_identity():
    """Return a cheap, JSON-safe identity without importing spaCy or Misaki.

    Content hashes are memoized by file stats. External library replacements,
    changed lexicons, and a changed tagging model produce new cache identities.
    Missing assets have a stable identity so saved recordings remain browsable.
    """
    packages = {name: _distribution(name) for name in (*_CODE_PACKAGES, MODEL_PACKAGE)}
    versions = {name: package.version if package else 'missing' for name, package in packages.items()}
    misaki = packages['misaki']
    lexicon_root = Path(misaki.locate_file('misaki/data')) if misaki else Path('__missing_misaki__')
    lexicon_paths = [lexicon_root / name for name in _LEXICONS]
    model = packages[MODEL_PACKAGE]
    model_root = Path(model.locate_file(f'{MODEL_PACKAGE}/{MODEL_PACKAGE}-{model.version}')) if model else Path('__missing_english_model__')
    numbers = packages['num2words']
    numbers_root = Path(numbers.locate_file('num2words')) if numbers else Path('__missing_num2words__')
    return {
        'revision': PRONUNCIATION_REVISION,
        'adapter': ADAPTER_REVISION,
        'versions': versions,
        'lexicon_sha256': _content_identity(lexicon_root, lexicon_paths),
        'model_sha256': _content_identity(model_root, _payload_files(model_root)),
        'num2words_sha256': _content_identity(numbers_root, _payload_files(numbers_root, '.py')),
        'fallback': FALLBACK_POLICY,
        'symbols': symbol_identity(),
    }


_DIGITS = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')
_SYMBOL_NAMES = {
    "'": 'apostrophe', '-': 'hyphen', '_': 'underscore', '/': 'slash', '.': 'dot',
    ':': 'colon', '+': 'plus', '@': 'at', '&': 'and', '%': 'percent', '=': 'equal',
    '#': 'hash', '$': 'dollar', '*': 'asterisk', '\\': 'backslash', '~': 'tilde',
    '^': 'caret', '|': 'pipe', '<': 'less than', '>': 'greater than',
    '!': 'exclamation mark', '?': 'question mark', ';': 'semicolon', '"': 'quote',
}
# These are model punctuation, not words such as "comma" or "quote".
_PUNCTUATION = {c: c for c in ',;:.!?—…"“”()'}
_PUNCTUATION.update({'[': '(', ']': ')', '{': '(', '}': ')', '–': '—', '`': ''})
_CURRENCY_NAMES = {'$': 'dollar', '£': 'pound', '€': 'euro'}
# Recognize English thousands/decimal formats before handling separators.
_NUMBER = re.compile(r'(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]+)?|\.[0-9]+')
_NUMERIC_TEXT = re.compile(r'[0-9][0-9,.]*')
_RANGE_END = re.compile(r'[0-9](?:[kKmMbB])?$')
_LATIN_REPLACEMENTS = {'æ': 'ae', 'œ': 'oe', 'ø': 'o', 'ł': 'l', 'ß': 'ss', 'đ': 'd', 'ð': 'th', 'þ': 'th'}
_SPELLING_WARNING = 'Some words outside the pronunciation dictionary were spelled out.'
_LATIN_WARNING = 'Some accented Latin text used its English spelling for pronunciation.'
_SYMBOL_WARNING = 'Some symbols were read by their English names.'


def _latin_ascii(text):
    result, changed = [], False
    for character in unicodedata.normalize('NFC', text):
        if character in ('‘', '’'):
            result.append("'")
            continue
        if character.isascii():
            result.append(character)
            continue
        if character in _PUNCTUATION or character in _CURRENCY_NAMES:
            result.append(character)
            continue
        name = unicodedata.name(character, '')
        if not name.startswith('LATIN '):
            return None, False
        base = _LATIN_REPLACEMENTS.get(character.lower())
        if base is None:
            decomposition = unicodedata.normalize('NFKD', character)
            base = ''.join(c for c in decomposition if not unicodedata.combining(c))
        if not base or not base.isascii() or not base.isalpha():
            return None, False
        if character.isupper():
            base = base.upper()
        result.append(base)
        changed = True
    return ''.join(result), changed


class EnglishPronunciation:
    def __init__(self):
        global _LOADED_CODE_IDENTITY
        self.identity = pronunciation_identity()
        versions = self.identity['versions']
        if versions['misaki'] != MISAKI_VERSION:
            raise PronunciationError(f'Lilt needs the bundled Misaki {MISAKI_VERSION} pronunciation package. Repair this evaluation build.')
        if versions[MODEL_PACKAGE] != MODEL_VERSION or self.identity['model_sha256'] == 'missing':
            raise PronunciationError('The bundled English pronunciation model is missing or unsupported. Repair this evaluation build; pronunciation never downloads models.')
        if self.identity['lexicon_sha256'] == 'missing' or self.identity['num2words_sha256'] == 'missing':
            raise PronunciationError('The local pronunciation dictionaries or replaceable number-reading library are missing. Repair this evaluation build.')
        code_identity = (tuple(sorted(versions.items())), self.identity['num2words_sha256'])
        if _LOADED_CODE_IDENTITY is not None and code_identity != _LOADED_CODE_IDENTITY:
            raise PronunciationError('A pronunciation library changed while Lilt was running. Restart Lilt to use the replacement safely.')

        # Import only after checking the local artifacts. In particular, do not
        # use G2P.__init__: it can invoke spacy.cli.download on missing assets.
        from misaki import en
        import spacy
        model_distribution = _distribution(MODEL_PACKAGE)
        model_root = Path(model_distribution.locate_file(f'{MODEL_PACKAGE}/{MODEL_PACKAGE}-{MODEL_VERSION}'))
        self.nlp = spacy.load(model_root, enable=['tok2vec', 'tagger'])
        self.engines = {}
        self.last_warnings = []
        self._en = en
        _LOADED_CODE_IDENTITY = code_identity

    def _warn(self, message):
        if message not in self.last_warnings:
            self.last_warnings.append(message)

    @staticmethod
    def _unsupported(text):
        character = next((c for c in text if not c.isascii()), text[:1])
        code = f'U+{ord(character):04X}' if character else 'unknown'
        raise PronunciationError(f'Lilt cannot pronounce a character in this text ({code}). Replace it with an English description and try again.')

    def _word(self, lexicon, name):
        pieces = []
        for word in name.split():
            value = lexicon.golds.get(word)
            if isinstance(value, dict):
                value = value.get('DEFAULT')
            if not value:
                raise PronunciationError('A required English spelling entry is missing from the local dictionary. Repair this evaluation build.')
            pieces.append(value)
        return ' '.join(pieces)

    def _number(self, text, lexicon, currency=None):
        if '.' in text and (currency is None or len(text.partition('.')[2]) > 2):
            whole, _, fraction = text.partition('.')
            pieces = [self._number(whole, lexicon)] if whole else []
            pieces.append(self._word(lexicon, 'point'))
            pieces.extend(self._word(lexicon, _DIGITS[int(c)]) for c in fraction)
            phonemes = ' '.join(pieces)
            return lexicon.append_currency(phonemes, currency) if currency else phonemes
        # A leading-zero identifier must retain each digit.
        if currency is None and len(text) > 1 and text[0] == '0' and text.isdigit():
            return ' '.join(self._word(lexicon, _DIGITS[int(c)]) for c in text)
        token = self._en.MToken(text, 'CD', '', _=self._en.MToken.Underscore(
            is_head=True, num_flags='', currency=currency))
        phonemes, _ = lexicon(token, self._en.TokenContext())
        if not phonemes:
            raise PronunciationError('A number has no supported English pronunciation.')
        return phonemes

    def _spell(self, text, lexicon, british):
        pieces = []
        index = 0
        while index < len(text):
            character = text[index]
            before, after = text[:index], text[index + 1:]
            if character.isspace():
                index += 1
                continue
            # Keep code ranges (0..7) distinct from a decimal (.7).
            if text.startswith('..', index):
                end = index + 2
                while end < len(text) and text[end] == '.':
                    end += 1
                pieces.append('…' if end - index >= 3 else self._word(lexicon, 'dot dot'))
                index = end
                continue
            number = _NUMBER.match(text, index)
            if number:
                pieces.append(self._number(number.group(), lexicon))
                index = number.end()
                continue
            if character in _CURRENCY_NAMES:
                amount = _NUMBER.match(text, index + 1)
                if amount:
                    pieces.append(self._number(amount.group(), lexicon, character))
                    index = amount.end()
                    continue
                pieces.append(self._word(lexicon, _CURRENCY_NAMES[character]))
                self._warn(_SYMBOL_WARNING)
            elif character == '–' and _RANGE_END.search(before) and _NUMBER.match(after):
                pieces.append(self._word(lexicon, 'to'))
            elif character in '-–' and _NUMBER.match(after) and (not before or not before[-1].isalnum()):
                pieces.append(self._word(lexicon, 'minus'))
            elif character == '~' and _NUMBER.match(after):
                pieces.append(self._word(lexicon, 'about'))
            elif character == '.' and before and after and before[-1].isalnum() and after[0].isalpha():
                pieces.append(self._word(lexicon, 'dot'))
                self._warn(_SYMBOL_WARNING)
            elif character in _PUNCTUATION:
                pieces.append(_PUNCTUATION[character])
            elif character.isascii() and character.isalpha():
                key = 'zed' if british and character.lower() == 'z' else character.upper()
                pieces.append(self._word(lexicon, key))
                self._warn(_SPELLING_WARNING)
            elif character in _SYMBOL_NAMES:
                pieces.append(self._word(lexicon, _SYMBOL_NAMES[character]))
                self._warn(_SYMBOL_WARNING)
            else:
                self._unsupported(character)
            index += 1
        return ' '.join(piece for piece in pieces if piece)

    def _fallback(self, token, lexicon, british):
        text, changed = _latin_ascii(token.text)
        if text is None:
            self._unsupported(token.text)
        if changed:
            self._warn(_LATIN_WARNING)
            normalized = replace(token, text=text, _=replace_attributes(token._, self._en))
            normalized._.alias = None
            phonemes, rating = lexicon(normalized, self._en.TokenContext())
            if phonemes:
                return phonemes, rating
        return self._spell(text, lexicon, british), 1

    def _engine(self, british):
        if british not in self.engines:
            engine = self._en.G2P.__new__(self._en.G2P)
            engine.version = None
            engine.british = british
            engine.nlp = self.nlp
            engine.lexicon = self._en.Lexicon(british)
            engine.unk = '❓'

            def fallback(token):
                return self._fallback(token, engine.lexicon, british)

            engine.fallback = fallback
            self.engines[british] = engine
        return self.engines[british]

    def phonemize(self, text, lang='en-us'):
        self.last_warnings = []
        if lang not in {'en-us', 'en-gb'}:
            raise PronunciationError('This Lilt build supports English pronunciation only.')
        if pronunciation_identity() != self.identity:
            raise PronunciationError('Pronunciation assets changed during this reading. Restart Lilt before continuing.')
        engine = self._engine(lang == 'en-gb')
        _, tokens = engine(text, preprocess=False)
        original = ''.join(c for c in unicodedata.normalize('NFKC', text) if c.isalnum())
        covered = ''.join(c for c in unicodedata.normalize('NFKC', ''.join(token.text for token in tokens)) if c.isalnum())
        if original != covered:
            raise PronunciationError('Pronunciation did not preserve every word in this section. Generation stopped before saving incomplete speech.')
        for index, token in enumerate(tokens):
            numeric = _NUMERIC_TEXT.fullmatch(token.text)
            if numeric and (('..' in token.text) or (',' in token.text and not _NUMBER.fullmatch(token.text))
                            or (len(token.text) > 1 and token.text[0] == '0' and token.text.isdigit())):
                # Misaki accepts malformed grouping as a single number (0,0,0
                # becomes zero). Preserve individual values and separators.
                token.phonemes = self._spell(token.text, engine.lexicon, lang == 'en-gb')
            if not token.phonemes and any(c.isalnum() for c in token.text) and token.tag in self._en.PUNCT_TAGS:
                # spaCy sometimes tags ~10's numeric subtokens as punctuation.
                # Repair only that proven punctuation path, never an empty word.
                if _NUMBER.fullmatch(token.text) or any(c in _PUNCTUATION or c in _SYMBOL_NAMES for c in token.text):
                    token.phonemes, _ = self._fallback(token, engine.lexicon, lang == 'en-gb')
            before = tokens[index - 1] if index else None
            after = tokens[index + 1] if index + 1 < len(tokens) else None
            if token.text in {'~', '–'} and after and not token.whitespace and _NUMBER.match(after.text):
                if token.text == '~':
                    token.phonemes = self._word(engine.lexicon, 'about')
                elif before and not before.whitespace and _RANGE_END.search(before.text):
                    token.phonemes = self._word(engine.lexicon, 'to')
                else:
                    token.phonemes = self._word(engine.lexicon, 'minus')
            if token.phonemes is None or '❓' in token.phonemes:
                raise PronunciationError('A word has no English pronunciation. Generation stopped before saving incomplete speech.')
            if not token.phonemes and any(c.isalnum() for c in token.text):
                raise PronunciationError('Pronunciation omitted a word or number. Generation stopped before saving incomplete speech.')
            if not token.phonemes and token.text.strip():
                # Misaki attaches the currency to the numeric token and leaves
                # its separate symbol empty. Naming it again duplicates dollars.
                if token.text in self._en.CURRENCIES and any(
                        later._.get('currency') == token.text for later in tokens[index + 1:index + 4]):
                    continue
                token.phonemes, _ = self._fallback(token, engine.lexicon, lang == 'en-gb')
        return ''.join(token.phonemes + token.whitespace for token in tokens).strip()


def replace_attributes(attributes, en):
    """Copy Misaki's mutable token attributes before normalizing a fallback."""
    return en.MToken.Underscore(dict(attributes)) if attributes is not None else en.MToken.Underscore()

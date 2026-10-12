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
import unicodedata


MISAKI_VERSION = '0.9.4'
MODEL_PACKAGE = 'en_core_web_sm'
MODEL_VERSION = '3.8.0'
PRONUNCIATION_REVISION = 'lilt-misaki-english-v1'
FALLBACK_POLICY = 'latin-english-normalization-and-letter-spelling-v1'
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
    }


_DIGITS = ('zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine')
_SYMBOL_NAMES = {
    "'": 'apostrophe', '-': 'hyphen', '_': 'underscore', '/': 'slash', '.': 'dot',
    ':': 'colon', '+': 'plus', '@': 'at', '&': 'and', '%': 'percent', '=': 'equal',
    '#': 'hash', '$': 'dollar', '*': 'asterisk', '\\': 'backslash', '~': 'tilde',
    '^': 'caret', '|': 'pipe', '<': 'less than', '>': 'greater than',
    '!': 'exclamation mark', '?': 'question mark', ';': 'semicolon', '"': 'quote',
}
_ORNAMENTS = frozenset('[]{}()`')
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

    def _spell(self, text, lexicon, british):
        pieces = []
        for character in text:
            if character.isspace() or character in _ORNAMENTS:
                continue
            if character.isascii() and character.isalpha():
                key = 'zed' if british and character.lower() == 'z' else character.upper()
                pieces.append(self._word(lexicon, key))
            elif character in '0123456789':
                pieces.append(self._word(lexicon, _DIGITS[int(character)]))
            elif character in _SYMBOL_NAMES:
                pieces.append(self._word(lexicon, _SYMBOL_NAMES[character]))
            else:
                self._unsupported(character)
        if not pieces:
            raise PronunciationError('A word has no supported English pronunciation.')
        return ' '.join(pieces)

    def _engine(self, british):
        if british not in self.engines:
            engine = self._en.G2P.__new__(self._en.G2P)
            engine.version = None
            engine.british = british
            engine.nlp = self.nlp
            engine.lexicon = self._en.Lexicon(british)
            engine.unk = '❓'

            def fallback(token):
                text, changed = _latin_ascii(token.text)
                if text is None:
                    self._unsupported(token.text)
                if changed:
                    self._warn(_LATIN_WARNING)
                    normalized = replace(token, text=text, _=replace_attributes(token._, self._en))
                    normalized._.alias = None
                    phonemes, rating = engine.lexicon(normalized, self._en.TokenContext())
                    if phonemes:
                        return phonemes, rating
                self._warn(_SPELLING_WARNING)
                return self._spell(text, engine.lexicon, british), 1

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
                meaningful = ''.join(c for c in token.text if not c.isspace() and c not in _ORNAMENTS)
                if meaningful:
                    normalized, _ = _latin_ascii(meaningful)
                    if normalized is None or any(c not in _SYMBOL_NAMES for c in normalized):
                        self._unsupported(meaningful)
                    self._warn(_SYMBOL_WARNING)
                    token.phonemes = self._spell(normalized, engine.lexicon, lang == 'en-gb')
        return ''.join(token.phonemes + token.whitespace for token in tokens).strip()


def replace_attributes(attributes, en):
    """Copy Misaki's mutable token attributes before normalizing a fallback."""
    return en.MToken.Underscore(dict(attributes)) if attributes is not None else en.MToken.Underscore()

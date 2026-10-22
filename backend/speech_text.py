"""Prepare graphic symbols and speech boundaries without changing the source."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata


# Persisted speech identities are versioned independently of the product name.
SYMBOL_POLICY = 'lilt-speech-symbols-v3'
SYMBOL_NAMES = {
    '→': 'right arrow', '➔': 'right arrow', '➜': 'right arrow',
    '➝': 'right arrow', '➞': 'right arrow', '➡': 'right arrow', '➤': 'right arrow',
    '←': 'left arrow', '⬅': 'left arrow',
    '↑': 'up arrow', '⬆': 'up arrow', '↓': 'down arrow', '⬇': 'down arrow',
    '↔': 'left right arrow', '↕': 'up down arrow',
    '↗': 'up right arrow', '↘': 'down right arrow',
    '↙': 'down left arrow', '↖': 'up left arrow',
    '⇒': 'double right arrow', '⇐': 'double left arrow',
    '⇑': 'double up arrow', '⇓': 'double down arrow',
    '⇔': 'double left right arrow', '⇕': 'double up down arrow',
    '×': 'multiplication sign', '÷': 'division sign', '±': 'plus or minus',
    '≤': 'less than or equal to', '≥': 'greater than or equal to',
    '≠': 'not equal to', '≈': 'approximately equal to',
    '∞': 'infinity', '√': 'square root', '°': 'degree sign', '•': 'bullet',
    '©': 'copyright', '®': 'registered trademark', '™': 'trademark',
}
# Misaki already handles these as punctuation or part of a currency amount.
_PASSTHROUGH = frozenset('‘’“”–—…£€')
_SPACING_MARKS = frozenset('=()[]{}<>')
_ADDRESS = re.compile(r'(?<![a-z0-9+.-])(?:[a-z][a-z0-9+.-]*://|www\.)\S+|'
                      r"(?<![a-z0-9.!#$%&'*+/=?^_`{|}~-])"
                      r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.[a-z]{2,}", re.I)


def symbol_identity(*, revision=None):
    """Cheap identity; an explicit revision verifies the historical brand alias."""
    revision = SYMBOL_POLICY if revision is None else revision
    policy = [revision, SYMBOL_NAMES, sorted(_PASSTHROUGH), unicodedata.unidata_version,
              sorted(_SPACING_MARKS), _ADDRESS.pattern, 'non-numeric-comma-spacing-v1']
    return {'revision': revision,
            'sha256': hashlib.sha256(json.dumps(policy, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}


def _variation_selector(character):
    return '\ufe00' <= character <= '\ufe0f' or '\U000e0100' <= character <= '\U000e01ef'


def _ordinary(character):
    if character.isspace() or (character.isascii() and character.isprintable()) or character in _PASSTHROUGH:
        return True
    category = unicodedata.category(character)
    # Keep words, numbers and linguistic accents, including unsupported scripts.
    # Enclosing marks and variation selectors are graphic decorations.
    return category[0] in 'LN' or (category[0] == 'M' and category != 'Me'
                                  and not _variation_selector(character))


def _speech_spacing(text):
    """Separate selected syntax without rewriting words, punctuation or addresses."""
    def space_part(part):
        pieces = []
        for index, character in enumerate(part):
            after = part[index + 1:index + 2]
            before = part[index - 1:index] if index else ''
            if character in _SPACING_MARKS:
                pieces.extend((' ', character))
                # A closing group stays attached to its following sentence mark.
                if character not in ')]}' or after not in ',;:.!?':
                    pieces.append(' ')
            else:
                pieces.append(character)
                if character == ',' and after and not after.isspace() and not (before.isdigit() and after.isdigit()):
                    pieces.append(' ')
        return ''.join(pieces)

    pieces, end = [], 0
    for match in _ADDRESS.finditer(text):
        pieces.extend((space_part(text[end:match.start()]), match.group()))
        end = match.end()
    pieces.append(space_part(text[end:]))
    return ' '.join(''.join(pieces).split())


def normalize_symbols(text):
    """Return cleaned speech and an ordered list of only the omitted symbols.

    Work on graphemes so compound emoji are one omission, but never consume an
    alphanumeric base/linguistic accent along with a graphic decoration.
    """
    import regex

    pieces, unread = [], []
    for cluster in regex.findall(r'\X', text):
        base = ''.join(c for c in cluster if not _variation_selector(c))
        word_base = any(unicodedata.category(c)[0] in 'LN' for c in cluster)
        ordinary = [_ordinary(c) and (word_base or unicodedata.category(c)[0] != 'M') for c in cluster]
        if base in SYMBOL_NAMES:
            pieces.append(' ' + SYMBOL_NAMES[base] + ' ')
        elif all(ordinary):
            pieces.append(cluster)
        elif not any(ordinary):
            unread.append(cluster)
            pieces.append(' ')
        else:
            # For example, preserve the digit in 1️⃣ and omit its decoration.
            graphic = ''
            for character, keep in zip(cluster, ordinary):
                if keep:
                    if graphic:
                        unread.append(graphic)
                        pieces.append(' ')
                        graphic = ''
                    pieces.append(character)
                else:
                    graphic += character
            if graphic:
                unread.append(graphic)
                pieces.append(' ')
    return _speech_spacing(''.join(pieces)), unread

"""Prepare graphic symbols for speech without changing the source document."""
from __future__ import annotations

import hashlib
import json
import unicodedata


SYMBOL_POLICY = 'lilt-speech-symbols-v2'
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


def symbol_identity():
    """Cheap identity; importing pronunciation identity must not load regex/G2P."""
    policy = [SYMBOL_POLICY, SYMBOL_NAMES, sorted(_PASSTHROUGH), unicodedata.unidata_version]
    return {'revision': SYMBOL_POLICY,
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
    return ' '.join(''.join(pieces).split()), unread

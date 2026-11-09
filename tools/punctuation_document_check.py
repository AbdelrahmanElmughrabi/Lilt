"""Check every immutable job section against both offline English engines."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def check(snapshot, allow_spacing=False):
    from backend._vendor.kokoro.config import DEFAULT_VOCAB
    from backend.documents import prepare
    from backend.pronunciation import EnglishPronunciation
    from backend.sections import listening_chunks

    job = json.loads(snapshot.read_text(encoding='utf-8'))
    prepared = prepare(job['markdown'], job['options'], job['title'])
    chunks = listening_chunks(prepared['chunks'])
    unchanged = chunks == job['chunks']
    if allow_spacing:
        assert ''.join(prepared['text'].split()) == ''.join(''.join(c['text'] for c in job['chunks']).split()), 'Preparation changed more than whitespace.'
    else:
        assert unchanged, 'Preparation changed the saved speech input.'
    engine = EnglishPronunciation()
    result = {'sections': len(chunks), 'original_sections': len(job['chunks']),
              'preparation_unchanged': unchanged, 'whitespace_only_change': allow_spacing,
              'prepared_text': prepared['text'],
              'original_sha256': hashlib.sha256(job['markdown'].encode()).hexdigest(),
              'identity': engine.identity, 'languages': {}}
    for lang in ('en-us', 'en-gb'):
        failures = []
        digests = []
        spelled_sections = []
        for index, chunk in enumerate(chunks):
            try:
                phonemes = engine.phonemize(chunk['text'], lang)
                if not phonemes or set(phonemes) - DEFAULT_VOCAB.keys():
                    raise ValueError('Empty or unsupported model pronunciation.')
                digests.append(hashlib.sha256(phonemes.encode()).hexdigest())
                if any('spelled out' in warning for warning in engine.last_warnings):
                    spelled_sections.append(index + 1)
            except Exception as error:
                failures.append({'section': index + 1, 'error': str(error)})
        result['languages'][lang] = {'passed': len(chunks) - len(failures), 'spelled_sections': spelled_sections,
                                     'failures': failures, 'phoneme_sha256': digests}
        print(f'{lang}: {len(chunks) - len(failures)} / {len(chunks)} sections passed.', flush=True)
    result['success'] = all(not value['failures'] for value in result['languages'].values())
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-spacing', action='store_true', help='Require whitespace-only differences and check newly prepared sections.')
    arguments = parser.parse_args()
    if arguments.output.exists():
        raise FileExistsError('Use a new output path; existing evidence is never overwritten.')
    result = check(arguments.snapshot, arguments.allow_spacing)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())

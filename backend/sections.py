"""Immutable job section layout and sample-accurate streaming timeline."""
from __future__ import annotations

from .cache import audio_info
from .documents import section_text


def listening_chunks(chunks):
    result = []
    first_passage = True
    for chunk in chunks:
        if first_passage and chunk['text'].count(' ') >= 18:
            pieces = section_text(chunk['text'], limit=180)
            for index, text in enumerate(pieces):
                result.append({**chunk, 'text': text, 'pause': chunk['pause'] if index == len(pieces) - 1 else 0.12})
            first_passage = False
        else:
            result.append(dict(chunk))
    return result


def published_sections(job, directory):
    sections, start = [], 0
    for index, chunk in enumerate(job.get('chunks', [])):
        info = audio_info(directory / f'section-{index:06d}.wav')
        if info is None:
            break
        pause = int(chunk['pause'] * 24000) / 24000 if index < len(job['chunks']) - 1 else 0
        sections.append({'index': index, 'start': start, 'duration': info.frames / 24000, 'pause': pause})
        start += info.frames / 24000 + pause
    return sections, start


def manifest(job):
    sections = job.get('sections', [])
    return {'id': job['id'], 'state': job['state'], 'sections': sections,
            'available': job.get('available_duration', 0), 'total': job['total'],
            'complete': job['state'] == 'completed', 'throughput': job.get('throughput', 0),
            'running': job['state'] in {'preparing', 'generating', 'assembling', 'cancelling'}}

"""Shared validation for public preferences and saved settings."""
from __future__ import annotations

import json
import math
import re


def defaults():
    from .performance import DEFAULTS
    return {'theme': 'light', 'palette': 'violilt', 'voice': 'af_heart', 'speed': 1.0,
            'include_code': False, 'heading_pause': 0.6, 'paragraph_pause': 0.3} | DEFAULTS


def validate_settings(values, *, internal=False, voices=None):
    from .performance import validate
    if not isinstance(values, dict):
        raise ValueError('Settings must be an object.')
    allowed = set(defaults()) | ({'benchmark_result'} if internal else set())
    if values.keys() - allowed:
        raise ValueError('Unknown settings field.')
    result = values.copy()
    for key, choices in {'theme': {'light', 'dark', 'system'}, 'palette': {'violilt', 'classic'}}.items():
        if key in result and (not isinstance(result[key], str) or result[key] not in choices):
            raise ValueError(f'Unknown {key} setting.')
    for key in ('speed', 'heading_pause', 'paragraph_pause'):
        if key not in result:
            continue
        value = result[key]
        low, high = (0.5, 2.0) if key == 'speed' else (0.0, 2.0)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'Choose a {key.replace("_", " ")} between {low:g} and {high:g}.')
    if 'include_code' in result and not isinstance(result['include_code'], bool):
        raise ValueError('Include code must be on or off.')
    if 'voice' in result:
        voice = result['voice']
        if (not isinstance(voice, str) or re.fullmatch(r'(?:af|am|bf|bm)_[a-z0-9_]{1,48}', voice) is None
                or voices is not None and voice not in voices):
            raise ValueError('Choose an available English voice.')
    try:
        validate(result)
    except (TypeError, OverflowError) as error:
        raise ValueError('Choose valid performance settings.') from error
    if 'benchmark_result' in result:
        benchmark = result['benchmark_result']
        if not isinstance(benchmark, dict) or not isinstance(benchmark.get('identity'), str):
            raise ValueError('Invalid saved speed-test result.')
        for key in ('cpu', 'best'):
            entry = benchmark.get(key)
            if not isinstance(entry, dict) or isinstance(entry.get('threads'), bool) or not isinstance(entry.get('threads'), int) or not 1 <= entry['threads'] <= 1024:
                raise ValueError('Invalid saved speed-test result.')
        try:
            if len(json.dumps(benchmark, allow_nan=False)) > 256 * 1024:
                raise ValueError('The saved speed-test result is too large.')
        except (TypeError, OverflowError, RecursionError) as error:
            raise ValueError('Invalid saved speed-test result.') from error
    return result

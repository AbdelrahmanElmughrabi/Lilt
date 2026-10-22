"""Shared validation for public preferences and saved settings."""
from __future__ import annotations

import json
import math
import re


def defaults():
    from .performance import DEFAULTS
    return {'theme': 'light', 'palette': 'violilt', 'voice': 'af_heart', 'speed': 1.0,
            'include_code': False, 'heading_pause': 0.6, 'paragraph_pause': 0.3} | DEFAULTS


def finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _validate_benchmark(benchmark):
    if not isinstance(benchmark, dict) or not isinstance(benchmark.get('identity'), str):
        raise ValueError('Invalid saved speed-test result.')

    def measurement(entry, *, cpu=False):
        if not isinstance(entry, dict):
            raise ValueError('Invalid saved speed-test measurement.')
        threads = entry.get('threads')
        if type(threads) is not int or not 1 <= threads <= 1024:
            raise ValueError('Invalid saved speed-test thread count.')
        # Older CPU recommendations contain just a thread count. The best
        # measurement needs its provider, which Performance.resolve consumes.
        provider = entry.get('provider', 'CPUExecutionProvider' if cpu else None)
        if (not isinstance(provider, str) or provider not in {
                'CPUExecutionProvider', 'CUDAExecutionProvider', 'DmlExecutionProvider'}
                or cpu and provider != 'CPUExecutionProvider'):
            raise ValueError('Invalid saved speed-test provider.')
        device = entry.get('device_id', -1 if provider == 'CPUExecutionProvider' else None)
        if type(device) is not int or device < (-1 if provider == 'CPUExecutionProvider' else 0):
            raise ValueError('Invalid saved speed-test device.')
        for key in ('label', 'error'):
            if key in entry and not isinstance(entry[key], str):
                raise ValueError('Invalid saved speed-test description.')
        for key in ('throughput', 'load_seconds', 'processing_seconds', 'audio_seconds'):
            if key in entry and (not finite_number(entry[key]) or entry[key] < 0):
                raise ValueError('Invalid saved speed-test timing.')

    measurement(benchmark.get('cpu'), cpu=True)
    measurement(benchmark.get('best'))
    if 'created' in benchmark and (not finite_number(benchmark['created']) or benchmark['created'] < 0):
        raise ValueError('Invalid saved speed-test date.')
    if 'results' in benchmark:
        if not isinstance(benchmark['results'], list):
            raise ValueError('Invalid saved speed-test measurements.')
        for entry in benchmark['results']:
            measurement(entry)
    try:
        if len(json.dumps(benchmark, allow_nan=False)) > 256 * 1024:
            raise ValueError('The saved speed-test result is too large.')
    except (TypeError, OverflowError, RecursionError) as error:
        raise ValueError('Invalid saved speed-test result.') from error


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
        if not finite_number(value) or not low <= value <= high:
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
        _validate_benchmark(result['benchmark_result'])
    return result

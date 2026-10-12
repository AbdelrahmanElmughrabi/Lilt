"""Minimal configuration adapted from Kokoro-ONNX 0.6.1 (MIT).

This adaptation removes pronunciation library configuration.
"""
import json
from pathlib import Path

MAX_PHONEME_LENGTH = 510
SAMPLE_RATE = 24000

with (Path(__file__).parent / 'config.json').open(encoding='utf-8') as source:
    DEFAULT_VOCAB = json.load(source)['vocab']

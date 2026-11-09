"""Generate current-engine listening samples without importing baseline dependencies."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.pronunciation_integration import digest


def create_samples(arguments):
    import numpy as np
    import soundfile as sf
    config = {'provider': 'CUDAExecutionProvider' if arguments.device == 'gpu' else 'CPUExecutionProvider',
              'device_id': 0 if arguments.device == 'gpu' else -1, 'cuda_device': 0,
              'threads': 2 if arguments.device == 'gpu' else 4, 'spinning': False}
    model = arguments.models / ('kokoro-v1.0.fp16-gpu.onnx' if arguments.device == 'gpu' else 'kokoro-v1.0.int8.onnx')
    voices = arguments.models / 'voices-v1.0.bin'
    if arguments.device == 'gpu':
        from backend.runtime import activate_gpu_runtime, gpu_runtime_directory
        runtime = gpu_runtime_directory()
        if runtime is None:
            raise ValueError('Validate the optional GPU runtime before generating GPU samples.')
        activate_gpu_runtime(runtime)
    started = time.perf_counter()
    from backend.performance import create_engine
    engine = create_engine(model, voices, config)
    loading = time.perf_counter() - started
    corpus = [
        ('ordinary-us', 'af_heart', 'The next sentence is waiting. Listen to the first words while the next thought is prepared.'),
        ('numbers-us', 'af_heart', 'Dr. Smith paid $12.50 on October 12, 2026. The CPU uses 4 threads; version 2.0 is ready.'),
        ('ordinary-gb', 'bf_emma', 'A quiet library gives each thought a little room. The colour of the sky changes as we read.'),
        ('fallback-gb', 'bf_emma', 'Zorblyx met José at the café. Their new project was called VioliltTTS.'),
    ]
    results = []
    for name, voice, text in corpus:
        started = time.perf_counter()
        samples, rate = engine.create(text, voice=voice, speed=1, lang='en-gb' if voice.startswith('b') else 'en-us')
        elapsed = time.perf_counter() - started
        assert rate == 24000 and len(samples) and np.all(np.isfinite(samples)) and np.any(samples)
        target = arguments.output / f'{name}.wav'
        sf.write(target, samples, rate, subtype='PCM_16')
        results.append({'sample': name, 'text': text, 'voice': voice, 'seconds': elapsed,
                        'audio_seconds': len(samples) / rate, 'sha256': digest(target),
                        'warnings': getattr(engine, 'last_pronunciation_warnings', [])})
        print(f'candidate {arguments.device}: {name} ready', flush=True)
    return {'engine': 'candidate', 'device': arguments.device, 'load_seconds': loading,
            'samples': results, 'listening_review': 'Pending human A/B review; valid audio is not a naturalness verdict.'}



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--models', type=Path, default=ROOT / '.app-data/models')
    parser.add_argument('--device', choices=['cpu', 'gpu'], default='cpu')
    arguments = parser.parse_args()
    arguments.output = arguments.output.resolve()
    if arguments.output.exists():
        parser.error('Use a new listening-sample directory; existing recordings are never overwritten.')
    arguments.output.mkdir(parents=True)
    evidence = create_samples(arguments)
    (arguments.output / 'results.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print(json.dumps({'success': True, 'evidence': str(arguments.output / 'results.json')}), flush=True)

if __name__ == '__main__':
    main()

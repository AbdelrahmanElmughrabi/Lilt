"""Validate a separate optional runtime without modifying the preserved baseline."""
import argparse
import json
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from backend.models import GPU_FILE, FILES

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, default=root / '.tmp/pronunciation-gpu-runtime')
    parser.add_argument('--models', type=Path, default=root / '.tmp/pronunciation-eval/data/models')
    parser.add_argument('--output', type=Path, default=root / '.tmp/pronunciation-eval/cuda-probe.json')
    arguments = parser.parse_args()
    runtime = arguments.runtime.resolve()
    if not (runtime / 'onnxruntime/__init__.py').is_file():
        parser.error('Install the optional GPU runtime in the selected directory first.')
    sys.path.insert(0, str(runtime))
    import numpy as np
    import onnxruntime as ort
    from backend.performance import create_engine
    model_root = arguments.models.resolve()
    config = {'provider': 'CUDAExecutionProvider', 'device_id': 0, 'cuda_device': 0, 'threads': 2,
              'spinning': False, 'background': False, 'profile': True, 'model': str(model_root / GPU_FILE)}
    started = time.perf_counter()
    engine = create_engine(config['model'], model_root / FILES[1], config)
    load = time.perf_counter() - started
    engine.create('A little room for listening.', voice='af_heart', speed=1, lang='en-us')
    results = []
    for text in ['A long reading can begin with a small passage. Listen to the first words while the next part is prepared, and let each thought arrive at its own pace.',
                 'The next chapter can be ready before you finish the first. We are checking real local inference, with every word kept in the order you wrote it. A complete recording is still saved for later.']:
        started = time.perf_counter()
        audio, rate = engine.create(text, voice='af_heart', speed=1, lang='en-us')
        elapsed = time.perf_counter() - started
        assert np.all(np.isfinite(audio)) and np.max(np.abs(audio)) > .01 and rate == 24000
        results.append({'audio_seconds': len(audio) / rate, 'processing_seconds': elapsed, 'throughput': len(audio) / rate / elapsed})
    profile_path = Path(engine.sess.end_profiling())
    profile = json.loads(profile_path.read_text())
    cuda_nodes = [event for event in profile if event.get('args', {}).get('provider') == 'CUDAExecutionProvider']
    assert len(cuda_nodes) > 0, 'No operations actually ran on CUDA'
    result = {'success': True, 'runtime': ort.__version__, 'load_seconds': load, 'results': results, 'cuda_nodes': len(cuda_nodes)}
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(result, indent=2))
    (runtime / 'violilt-runtime.json').write_text(json.dumps({'provider': 'CUDAExecutionProvider', 'runtime': ort.__version__, 'tested_model': GPU_FILE}))
    print(json.dumps(result), flush=True)

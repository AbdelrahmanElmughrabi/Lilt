import json
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / '.cuda-probe'))
import numpy as np
import onnxruntime as ort
from backend.models import GPU_FILE, FILES
from backend.performance import create_engine

if __name__ == '__main__':
    model_root = root / '.app-data' / 'models'
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
    (root / 'artifacts' / 'cuda-probe.json').write_text(json.dumps(result, indent=2))
    (root / '.cuda-probe' / 'folio-runtime.json').write_text(json.dumps({'provider': 'CUDAExecutionProvider', 'runtime': ort.__version__, 'tested_model': GPU_FILE}))
    print(json.dumps(result), flush=True)

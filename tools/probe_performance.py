import json
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / '.gpu-probe'))
from backend.performance import create_engine, Performance
from backend.models import Models, FILES
from backend.storage import Store

if __name__ == '__main__':
    store = Store(root / 'artifacts' / 'performance-probe')
    models = Models(root / '.app-data' / 'models')
    performance = Performance(store, models)
    results = []
    for config in performance.candidates():
        if len(sys.argv) > 1:
            if config['provider'] != 'DmlExecutionProvider' or config['device_id'] != 0:
                continue
            config['model'] = str(models.root / sys.argv[1])
        try:
            started = time.perf_counter()
            engine = create_engine(config['model'], models.root / FILES[1], config)
            load = time.perf_counter() - started
            engine.create('A little room for listening.', voice='af_heart', speed=1, lang='en-us')
            started = time.perf_counter()
            audio, rate = engine.create('A long reading can begin with a small passage. Listen to the first words while the next part is prepared, and let each thought arrive at its own pace.', voice='af_heart', speed=1, lang='en-us')
            elapsed = time.perf_counter() - started
            result = {**config, 'load_seconds': round(load, 3), 'seconds': round(elapsed, 3),
                      'audio_seconds': round(len(audio) / rate, 3), 'throughput': round(len(audio) / rate / elapsed, 3)}
            del engine
        except Exception as error:
            result = {**config, 'error': str(error)}
        results.append(result)
        print(json.dumps(result), flush=True)
    (root / 'artifacts' / 'performance-probe.json').write_text(json.dumps(results, indent=2), encoding='utf-8')

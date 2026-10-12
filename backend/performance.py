"""Real inference settings, hardware identity, and process resource feedback."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import time
from pathlib import Path

from .devices import gpu_adapters
from .models import FILES, GPU_FILE
from .pronunciation import pronunciation_identity

DEFAULTS = {'performance_mode': 'balanced', 'cpu_threads': 0, 'processing_device': 'auto',
            'gpu_device': -1, 'buffer_mode': 'balanced', 'auto_listen': True,
            'warm_start': False, 'cache_enabled': True, 'cache_limit_mb': 256}


def validate(settings):
    for key, values in {'performance_mode': {'quiet', 'balanced', 'fast', 'custom'},
                        'processing_device': {'auto', 'cpu', 'gpu'},
                        'buffer_mode': {'sooner', 'balanced', 'smooth'}}.items():
        if key in settings and settings[key] not in values:
            raise ValueError(f'Unknown {key.replace("_", " ")} setting.')
    if 'cpu_threads' in settings:
        value = settings['cpu_threads']
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value or not 0 <= value <= (os.cpu_count() or 1):
            raise ValueError('Choose Auto or an available CPU thread count.')
    if 'gpu_device' in settings and (isinstance(settings['gpu_device'], bool) or not isinstance(settings['gpu_device'], int) or settings['gpu_device'] < -1):
        raise ValueError('Unknown GPU device.')
    if 'cache_limit_mb' in settings and settings['cache_limit_mb'] not in {128, 256, 512}:
        raise ValueError('Choose a cache limit of 128, 256, or 512 MB.')
    for key in ('auto_listen', 'warm_start', 'cache_enabled'):
        if key in settings and not isinstance(settings[key], bool):
            raise ValueError(f'{key.replace("_", " ")} must be on or off.')


def model_identity(path):
    path = Path(path)
    # Content identity remains stable when copying bundled models to a new folder.
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def create_engine(model, voices, config):
    import onnxruntime as ort
    from .kokoro_engine import Kokoro
    options = ort.SessionOptions()
    options.intra_op_num_threads = int(config['threads'])
    options.add_session_config_entry('session.intra_op.allow_spinning', '1' if config.get('spinning') else '0')
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    options.enable_profiling = bool(config.get('profile', False))
    providers = ['CPUExecutionProvider']
    if config['provider'] == 'DmlExecutionProvider':
        if 'DmlExecutionProvider' not in ort.get_available_providers():
            raise ValueError('This runtime does not include DirectML. Choose CPU.')
        options.enable_mem_pattern = False
        providers = [('DmlExecutionProvider', {'device_id': str(config['device_id'])}), 'CPUExecutionProvider']
    elif config['provider'] == 'CUDAExecutionProvider':
        if 'CUDAExecutionProvider' not in ort.get_available_providers():
            raise ValueError('The optional NVIDIA runtime is unavailable. Choose CPU.')
        import sys
        # cuDNN loads further sublibraries at inference time, beyond ORT's preload.
        for entry in sys.path:
            folder = Path(entry) / 'nvidia'
            if folder.is_dir():
                bins = [str(path) for path in folder.glob('*/bin') if path.is_dir()]
                os.environ['PATH'] = os.pathsep.join(bins + [os.environ.get('PATH', '')])
        ort.preload_dlls(directory='')
        providers = [('CUDAExecutionProvider', {'device_id': str(config.get('cuda_device', 0)),
                      'cudnn_conv_algo_search': 'HEURISTIC', 'do_copy_in_default_stream': '1'}), 'CPUExecutionProvider']
    session = ort.InferenceSession(str(model), sess_options=options, providers=providers)
    if config['provider'] not in session.get_providers():
        raise ValueError('The selected inference backend could not be initialized.')
    session.disable_fallback()
    return Kokoro.from_session(session, str(voices))


class Performance:
    def __init__(self, store, models):
        import psutil
        import onnxruntime as ort
        self.store, self.models = store, models
        self.logical = psutil.cpu_count() or 1
        self.physical = psutil.cpu_count(logical=False) or self.logical
        self.adapters = gpu_adapters()
        self.providers = ort.get_available_providers()
        from .runtime import gpu_runtime_info
        self.gpu_runtime = gpu_runtime_info()
        if self.gpu_runtime and any('NVIDIA' in adapter['name'] for adapter in self.adapters):
            self.providers = self.providers + ['CUDAExecutionProvider']
        self.runtime = ort.__version__
        self.benchmark = {'state': 'idle', 'completed': 0, 'total': 0, 'results': [], 'message': 'Find a good pace for this PC.'}
        self.warmup = {'state': 'idle', 'message': ''}
        self._process = None
        self._sampled = 0
        self._usage = None
        self._identity = None
        self._pronunciation_identity = None

    def identity(self):
        pronunciation = pronunciation_identity()
        if self._identity is None or pronunciation != self._pronunciation_identity:
            model_files = [(name, (self.models.root / name).stat().st_size, (self.models.root / name).stat().st_mtime_ns)
                           for name in (*FILES, GPU_FILE) if (self.models.root / name).is_file()]
            self._identity = hashlib.sha256(json.dumps([platform.processor(), self.logical, self.physical,
                self.adapters, self.runtime, self.gpu_runtime, pronunciation, model_files], sort_keys=True).encode()).hexdigest()
            self._pronunciation_identity = pronunciation
        return self._identity

    def recommendation(self):
        result = self.store.settings().get('benchmark_result')
        return result if result and result.get('identity') == self.identity() else None

    def gpu_ready(self):
        return ('CUDAExecutionProvider' in self.providers or 'DmlExecutionProvider' in self.providers) and bool(self.gpu_devices()) and (self.models.root / GPU_FILE).is_file()

    def gpu_devices(self):
        return [adapter for adapter in self.adapters if 'NVIDIA' in adapter['name']] if 'CUDAExecutionProvider' in self.providers else self.adapters

    def resolve(self, settings):
        mode = settings.get('performance_mode', 'balanced')
        recommendation = self.recommendation()
        best_cpu = (recommendation or {}).get('cpu', {}).get('threads', min(4, self.physical))
        threads = {'quiet': 1, 'balanced': max(1, min(best_cpu, max(1, self.physical // 2))),
                   'fast': best_cpu, 'custom': settings.get('cpu_threads', 0) or best_cpu}[mode]
        configuration = {'provider': 'CPUExecutionProvider', 'device_id': -1, 'label': 'CPU',
                         'threads': int(threads), 'spinning': False, 'background': mode == 'quiet',
                         'pace': 0.1 if mode == 'quiet' else 0, 'mode': mode}
        requested = settings.get('processing_device', 'auto')
        best = (recommendation or {}).get('best')
        if requested == 'gpu' or (requested == 'auto' and mode != 'quiet' and best and best['provider'] != 'CPUExecutionProvider'):
            if not self.gpu_ready():
                if requested == 'gpu':
                    raise ValueError('GPU runtime/model files are unavailable. Choose Auto or CPU.')
            else:
                identifier = settings.get('gpu_device', -1)
                if identifier < 0:
                    identifier = best['device_id'] if best and best['provider'] != 'CPUExecutionProvider' else max(self.gpu_devices(), key=lambda item: item['memory_mb'])['id']
                adapter = next((item for item in self.gpu_devices() if item['id'] == identifier), None)
                if adapter is None:
                    raise ValueError('The selected GPU is no longer available. Choose Auto.')
                provider = 'CUDAExecutionProvider' if 'CUDAExecutionProvider' in self.providers else 'DmlExecutionProvider'
                configuration.update(provider=provider, device_id=identifier, label=adapter['name'],
                                     cuda_device=next((i for i, item in enumerate(self.gpu_devices()) if item['id'] == identifier), 0))
                if mode in {'balanced', 'fast'}:
                    configuration['threads'] = best['threads'] if best and best['provider'] == provider and best['device_id'] == identifier else min(2, self.physical)
        configuration['model'] = str(self.models.root / (GPU_FILE if configuration['provider'] != 'CPUExecutionProvider' else FILES[0]))
        return configuration

    def candidates(self):
        counts = sorted({1, min(2, self.physical), min(4, self.physical), min(8, self.physical)})
        candidates = [{'provider': 'CPUExecutionProvider', 'device_id': -1, 'label': f'CPU · {count} thread' + ('s' if count != 1 else ''),
                       'threads': count, 'spinning': False, 'background': False, 'model': str(self.models.root / FILES[0])} for count in counts]
        if self.gpu_ready():
            provider = 'CUDAExecutionProvider' if 'CUDAExecutionProvider' in self.providers else 'DmlExecutionProvider'
            candidates += [{'provider': provider, 'device_id': adapter['id'], 'cuda_device': index, 'label': adapter['name'],
                            'threads': 2, 'spinning': False, 'background': False, 'model': str(self.models.root / GPU_FILE)} for index, adapter in enumerate(self.gpu_devices())]
        return candidates

    def usage(self, process):
        import psutil
        if not process or not process.is_alive():
            self._process, self._usage = None, None
            return None
        try:
            if not self._process or self._process.pid != process.pid:
                self._process = psutil.Process(process.pid)
                self._process.cpu_percent()
                self._sampled, self._usage = time.monotonic(), None
            elif time.monotonic() - self._sampled >= 0.5:
                self._usage = round(min(100, self._process.cpu_percent() / self.logical), 1)
                self._sampled = time.monotonic()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self._usage = None
        return self._usage

    def status(self, process=None):
        try:
            configuration = self.resolve(self.store.settings())
        except ValueError as error:
            configuration = {'label': 'Unavailable', 'threads': 0, 'message': str(error)}
        return {'logical_processors': self.logical, 'physical_cores': self.physical, 'adapters': self.gpu_devices(),
                'gpu_ready': self.gpu_ready(), 'gpu_message': 'Optional GPU runtime and model ready.' if self.gpu_ready() else 'GPU needs the optional runtime and GPU model.',
                'benchmark': self.benchmark.copy(), 'warmup': self.warmup.copy(), 'recommendation': self.recommendation(),
                'configuration': configuration, 'cpu_percent': self.usage(process)}

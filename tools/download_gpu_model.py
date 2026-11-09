"""Fetch the pinned official GPU model, verifying it before replacement."""
import argparse
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.models import GPU_FILE
from backend.model_trust import APPROVED, DOWNLOAD_ROOT, verify_file

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', type=Path, default=Path(__file__).resolve().parents[1] / '.tmp/pronunciation-eval/data/models',
                        help='Isolated evaluation model directory')
    arguments = parser.parse_args()
    name = GPU_FILE
    directory = arguments.models.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    try:
        digest = verify_file(target)
    except (OSError, ValueError):
        with tempfile.TemporaryDirectory(prefix='.gpu-stage-', dir=directory) as temporary:
            staged = Path(temporary) / name
            request = urllib.request.Request(DOWNLOAD_ROOT + name, headers={'User-Agent': 'Violilt-Desktop/0.2'})
            size = 0
            with urllib.request.urlopen(request, timeout=45) as response, staged.open('wb') as output:
                while block := response.read(1024 * 1024):
                    size += len(block)
                    if size > APPROVED[name][0]:
                        raise ValueError('GPU model exceeds its approved size.')
                    output.write(block)
            digest = verify_file(staged)
            staged.replace(target)
    print(json.dumps({'model': str(target), 'bytes': target.stat().st_size, 'sha256': digest}))

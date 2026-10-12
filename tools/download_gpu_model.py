"""Fetch the optional official GPU model with release size verification."""
import hashlib
import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.models import GPU_FILE, RELEASE

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', type=Path, default=Path(__file__).resolve().parents[1] / '.tmp/pronunciation-eval/data/models',
                        help='Isolated evaluation model directory')
    arguments = parser.parse_args()
    name = GPU_FILE
    directory = arguments.models.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(RELEASE, headers={'User-Agent': 'Lilt-Desktop/0.2'})
    with urllib.request.urlopen(request, timeout=30) as response:
        asset = next(item for item in json.load(response)['assets'] if item['name'] == name)
    target = directory / name
    if not target.is_file() or target.stat().st_size != asset['size']:
        temporary = target.with_suffix('.download')
        request = urllib.request.Request(asset['browser_download_url'], headers={'User-Agent': 'Lilt-Desktop/0.2'})
        with urllib.request.urlopen(request, timeout=45) as response, temporary.open('wb') as output:
            while block := response.read(1024 * 1024):
                output.write(block)
        if temporary.stat().st_size != asset['size']:
            raise RuntimeError('GPU model download was incomplete')
        temporary.replace(target)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    if asset.get('digest') and asset['digest'] != 'sha256:' + digest:
        raise RuntimeError('GPU model integrity check failed')
    print(json.dumps({'model': str(target), 'bytes': target.stat().st_size, 'sha256': digest}))

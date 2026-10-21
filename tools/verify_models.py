"""Verify the approved bytes before packaging, without loading model parsers."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.models import FILES, GPU_FILE
from backend.model_trust import verify_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    parser.add_argument('--include-gpu', action='store_true')
    arguments = parser.parse_args()
    names = list(FILES) + ([GPU_FILE] if arguments.include_gpu else [])
    print(json.dumps({name: verify_file(arguments.directory / name) for name in names}))

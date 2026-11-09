"""Download speech assets into this branch's isolated evaluation library."""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.models import Models
from backend.storage import Store, data_directory

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, help='Explicit evaluation library folder')
    arguments = parser.parse_args()
    store = Store(arguments.data_dir.resolve() if arguments.data_dir else data_directory('Violilt-Pronunciation-Evaluation'))
    models = Models(store.root / "models")
    models.download()
    previous = -1
    while models.status()["state"] == "downloading":
        state = models.status()
        if state["percent"] // 10 != previous:
            previous = state["percent"] // 10
            print(state["message"], flush=True)
        time.sleep(0.5)
    print(models.status()["message"], flush=True)
    sys.exit(0 if models.status()["state"] == "ready" else 1)

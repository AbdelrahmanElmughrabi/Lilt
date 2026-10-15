from __future__ import annotations

import argparse
import json
import logging
import multiprocessing
import os
import sys
from pathlib import Path


def main():
    from backend.bridge import Bridge
    from backend.documents import prepare
    from backend.jobs import Jobs
    from backend.models import Models
    from backend.server import AppServer
    from backend.storage import Store, data_directory

    parser = argparse.ArgumentParser(description="Lilt - local Markdown to speech")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--data-dir", type=Path, help="Explicit library folder for an isolated evaluation")
    parser.add_argument("--serve-preview", action="store_true", help="Serve UI for developer visual checks; no speech API is exposed")
    arguments = parser.parse_args()
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    candidate = {"data_profile": "Lilt-Pronunciation-Evaluation"}
    if getattr(sys, "frozen", False):
        marker = Path(sys.executable).parent / "lilt-candidate.json"
        if not marker.is_file():
            raise ValueError("The evaluation build's lilt-candidate.json marker is missing.")
        candidate = json.loads(marker.read_text(encoding="utf-8"))
        if candidate.get("data_profile") != "Lilt-Pronunciation-Evaluation":
            raise ValueError("Unknown candidate data profile.")
    assets = root / "frontend" / "dist"
    if not assets.is_dir():
        raise RuntimeError("Build the interface first: cd frontend && npm run build")
    store = Store(arguments.data_dir.resolve() if arguments.data_dir else data_directory(
        candidate.get("data_profile") if candidate else None))
    logging.basicConfig(filename=str(store.root / "lilt.log"), level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    bundled_models = Path(sys.executable).parent / "models" if getattr(sys, "frozen", False) else None
    models = Models(store.root / "models", bundled_models)
    jobs = Jobs(store, models)
    if not store.all("documents"):
        sample = (root / "examples" / "first-reading.md").read_text(encoding="utf-8")
        store.document(sample, prepare(sample)["title"])
    bridge = Bridge(store, models, jobs)
    server = AppServer(assets, store)
    server.start()
    if arguments.serve_preview:
        print(server.url + '?preview=1', flush=True)
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            jobs.close()
            server.close()
        return
    import webview
    from backend.desktop import install_csp_bridge
    install_csp_bridge(root / 'assets' / 'desktop-api.js')
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "Lilt.PronunciationEvaluation" if candidate else "Lilt.Desktop")
    # Both WebView cache and app data use explicit per-user locations.
    os.environ["WEBVIEW2_USER_DATA_FOLDER"] = str(store.root / "webview")
    window = webview.create_window("Lilt - Pronunciation Evaluation" if candidate else "Lilt", server.url, js_api=bridge,
                                   width=1440, height=960, min_size=(1024, 720),
                                   background_color="#f7f5ef", text_select=True)
    bridge._window = window
    def prepare_startup():
        if store.settings().get('warm_start'):
            try:
                jobs.warmup()
            except Exception:
                logging.exception('Startup voice preparation failed')
    window.events.shown += prepare_startup
    try:
        webview.start(gui="edgechromium", debug=arguments.debug, private_mode=False,
                      storage_path=str(store.root / "webview"), icon=str(root / "assets" / "lilt.ico"))
    finally:
        jobs.close()
        server.close()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

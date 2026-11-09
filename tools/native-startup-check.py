"""Exercise a normal WebView2 startup with strict CSP and isolated test data.

No remote debugging port, production data changes or speech downloads.
"""
from __future__ import annotations

import json
import math
import struct
import sys
import tempfile
import time
import traceback
import uuid
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import webview
    from backend.bridge import Bridge
    from backend.desktop import install_csp_bridge
    from backend.jobs import Jobs
    from backend.models import Models
    from backend.server import AppServer
    from backend.storage import Store

    with tempfile.TemporaryDirectory(prefix='violilt-startup-') as temporary:
        store = Store(Path(temporary))
        first = store.document('# The art of paying attention\n\nA quiet thought.', 'The art of paying attention', 'C:/notes/attention.md')
        store.document('# A slower kind of morning\n\nThe next sentence is waiting.', 'A slower kind of morning')
        key = uuid.uuid4().hex
        folder = store.root / 'jobs' / key
        folder.mkdir()
        with wave.open(str(folder / 'recording.wav'), 'wb') as audio:
            audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(24000)
            audio.writeframes(b''.join(struct.pack('<h', int(100 * math.sin(i / 20))) for i in range(24000 * 8)))
        store.put('jobs', {'id': key, 'title': first['title'], 'document_id': first['id'], 'state': 'completed',
                          'voice': 'af_heart', 'speed': 1, 'words': 10, 'preview': False, 'created': time.time(),
                          'completed': 1, 'total': 1, 'duration': 8, 'available_duration': 8, 'position': 3, 'message': 'Ready'})
        store.save_settings({'warm_start': False, 'performance_mode': 'quiet', 'processing_device': 'cpu'})
        models = Models(store.root / 'models', ROOT / '.app-data/models')
        jobs = Jobs(store, models)
        bridge = Bridge(store, models, jobs)
        server = AppServer(ROOT / 'frontend/dist', store)
        server.start()
        install_csp_bridge(ROOT / 'assets/desktop-api.js')
        window = webview.create_window('Violilt startup check', server.url, js_api=bridge, width=1120, height=800)
        bridge._window = window
        failures = []

        # Use the engine's raw script execution for instrumentation. The generic
        # Window.evaluate_js wraps source in eval and cannot run under strict CSP.
        def evaluate(expression):
            return window.gui.evaluate_js('JSON.stringify(' + expression + ')', window.uid, True)

        def until(expression, timeout=25):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                result = evaluate(expression)
                if result:
                    return result
                time.sleep(.1)
            raise AssertionError('Timed out: ' + expression)

        def probe():
            try:
                window.events.loaded.wait(20)
                until('!!document.querySelector(".home-page")')
                assert evaluate('document.querySelectorAll(".recent-reading").length') == 2
                assert evaluate('document.querySelectorAll(".saved-reading").length') == 1
                assert not evaluate('!!document.querySelector(".preview-label")')
                until('document.querySelector("audio").readyState >= 1')
                assert abs(evaluate('document.querySelector("audio").currentTime') - 3) < .2
                assert not evaluate('!!document.querySelector(".error-banner")')
                # Home buttons dispatch through Svelte to real native APIs.
                window.run_js('Array.from(document.querySelectorAll(".recent-reading")).find(row => row.textContent.includes("The art of paying attention")).click()')
                until('!!document.querySelector(".studio-layout")')
                until('document.querySelector(".document-tabs") !== null')
                assert store.get('documents', first['id'])['opened'] > first['opened']
                window.run_js('document.querySelector(".brand").click()')
                until('!!document.querySelector(".home-page")')
                window.run_js('document.querySelector(".saved-play").click()')
                until('!document.querySelector("audio").paused')
                until('document.querySelector("audio").currentTime > 3.4')
                window.run_js('document.querySelector("audio").pause()')
                time.sleep(.3)
                assert store.get('jobs', key)['position'] > 3.3
                window.run_js('window.pywebview.api.save_position(' + json.dumps(key) + ', 8)')
                deadline = time.monotonic() + 5
                while store.get('jobs', key)['position'] != 8 and time.monotonic() < deadline:
                    time.sleep(.1)
                assert store.get('jobs', key)['position'] == 8
                time.sleep(1.1)  # Let the normal library poll receive the end position.
                window.run_js('document.querySelector(".saved-play").click()')
                until('!document.querySelector("audio").paused && document.querySelector("audio").currentTime < 1')
                window.run_js('document.querySelector("audio").pause()')
                print(json.dumps({'success': True, 'debug': False, 'native_bridge': True, 'home': True,
                                  'recent_open': True, 'saved_wav': True, 'resume_playback': True, 'replay_finished': True}), flush=True)
            except Exception as error:
                failures.append(str(error))
                print(json.dumps({'success': False, 'error': str(error), 'traceback': traceback.format_exc()}), flush=True)
            finally:
                window.destroy()

        try:
            webview.start(probe, gui='edgechromium', debug=False, private_mode=True)
        finally:
            jobs.close(); server.close()
        return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())

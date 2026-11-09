"""Exercise normal WinForms close with real WebView2/Bridge/SQLite, synthetic data only.

Run once per case in a fresh process. Requires built frontend and the existing
project environment; never downloads models or opens an existing user library.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing
import sys
import threading
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CASES = ('immediate', 'inflight', 'retry', 'cancel', 'timeout', 'clean')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New folder inside this workspace .tmp')
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.tmp') or output == ROOT / '.tmp':
        parser.error('Use a new subdirectory inside this workspace .tmp.')
    output.mkdir(parents=True, exist_ok=False)

    import webview
    from backend.bridge import Bridge
    from backend.desktop import install_csp_bridge
    from backend.jobs import Jobs
    from backend.models import Models
    from backend.server import AppServer
    from backend.storage import Store
    from backend.window_close import install_close_guard

    store = Store(output / 'library')
    original = 'Original synthetic close fixture.'
    document = store.document(original, 'Close fixture')
    store.save_settings({'warm_start': False, 'processing_device': 'cpu'})
    models = Models(store.root / 'models')
    jobs = Jobs(store, models)
    bridge = Bridge(store, models, jobs)
    entered = threading.Event()
    release = threading.Event()
    controls = {'hold': False, 'fail': False, 'saves': [], 'close_requested': False}
    save_document = bridge.save_document

    def traced_save(identifier, markdown):
        controls['saves'].append({'text': markdown, 'after_close_request': controls['close_requested']})
        entered.set()
        if controls['hold'] and not release.wait(25):
            raise TimeoutError('Disposable native save gate timed out.')
        if controls['fail']:
            raise OSError('Disposable native save failure. Your edit is still open.')
        return save_document(identifier, markdown)

    bridge.save_document = traced_save
    server = AppServer(ROOT / 'frontend/dist', store)
    server.start()
    install_csp_bridge(ROOT / 'assets/desktop-api.js')
    window = webview.create_window('Violilt R-01 close check: ' + args.case, server.url,
                                   js_api=bridge, width=1120, height=800)
    bridge._window = window
    guard = install_close_guard(window)
    failures = []
    expected = original
    observations = []

    def evaluate(expression):
        # Raw engine execution avoids the generic eval wrapper under strict CSP.
        return window.gui.evaluate_js('JSON.stringify(' + expression + ')', window.uid, True)

    def until(expression, timeout=20):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            result = evaluate(expression)
            if result:
                return result
            time.sleep(.05)
        raise AssertionError('Timed out: ' + expression)

    def click(label):
        return evaluate('(() => { const button = Array.from(document.querySelectorAll("button"))'
                        '.find(button => button.textContent.trim() === ' + json.dumps(label) + ');'
                        'if (!button) return false; button.click(); return true; })()')

    def edit(text):
        evaluate('(() => {const input = document.querySelector("textarea.markdown-editor"); '
                 'input.value = ' + json.dumps(text) + '; input.dispatchEvent(new Event("input", '
                 '{bubbles: true})); return true;})()')

    def normal_close():
        controls['close_requested'] = True
        # destroy() calls WinForms Close(), including the same cancellable
        # FormClosing event used by the title-bar X/Alt+F4.
        window.destroy()

    def probe():
        nonlocal expected
        try:
            assert window.events.loaded.wait(25), 'WebView did not load.'
            until('!!document.querySelector(".home-page")')
            assert guard.armed, 'Frontend did not arm the native close guard.'
            evaluate('document.querySelector(".recent-reading").click()')
            until('!!document.querySelector(".reading-article")')
            assert click('Edit')
            until('!!document.querySelector("textarea.markdown-editor")')
            expected = 'Synthetic native close edit: ' + args.case + '.'

            if args.case == 'clean':
                expected = original
                normal_close()
            elif args.case == 'immediate':
                edit(expected)
                assert not controls['saves'], 'Autosave fired before the close test.'
                normal_close()
            elif args.case == 'inflight':
                controls['hold'] = True
                edit('Earlier native close snapshot.')
                evaluate('window.dispatchEvent(new KeyboardEvent("keydown", {key:"s", ctrlKey:true, bubbles:true}))')
                assert entered.wait(10)
                edit(expected)
                normal_close()
                until('!!document.querySelector("dialog[open] #save-close-title")')
                assert not window.events.closed.is_set()
                assert store.get('documents', document['id'])['markdown'] == original
                controls['hold'] = False
                release.set()
            elif args.case == 'retry':
                controls['fail'] = True
                edit(expected)
                normal_close()
                until('document.querySelector("dialog[open] [role=alert]")?.textContent.includes("Disposable native save failure")')
                assert not window.events.closed.is_set()
                assert store.get('documents', document['id'])['markdown'] == original
                assert evaluate('document.querySelector("textarea.markdown-editor").value') == expected
                observations.append('Failed save kept the window/editor open and SQLite unchanged.')
                controls['fail'] = False
                assert click('Retry save and close')
            else:
                controls['hold'] = True
                edit(expected)
                normal_close()
                assert entered.wait(10)
                until('!!document.querySelector("dialog[open] #save-close-title")')
                if args.case == 'timeout':
                    until('document.querySelector("dialog[open] [role=alert]")?.textContent.includes("taking longer")', timeout=15)
                    observations.append('Real ten-second save timeout kept the window open.')
                assert click('Keep editing')
                until('!document.querySelector("dialog[open] #save-close-title")')
                controls['hold'] = False
                release.set()
                if args.case == 'cancel':
                    expected = 'Synthetic edit after cancelling native close.'
                    edit(expected)
                    evaluate('window.dispatchEvent(new KeyboardEvent("keydown", {key:"s", ctrlKey:true, bubbles:true}))')
                deadline = time.monotonic() + 10
                while store.get('documents', document['id'])['markdown'] != expected and time.monotonic() < deadline:
                    time.sleep(.05)
                time.sleep(.2)
                assert not window.events.closed.is_set(), 'A canceled request closed after late save completion.'
                assert guard.request is None
                observations.append('Keep editing revoked close; late completion did not close the window.')
                normal_close()

            assert window.events.closed.wait(20), 'Successful save did not finish native closing.'
        except Exception as error:
            failures.append({'error': str(error), 'traceback': traceback.format_exc()})
        finally:
            controls['hold'] = False
            release.set()
            if not window.events.closed.is_set():
                # Test cleanup only: remove this test's guard so failure cannot
                # strand its disposable window/process. Never a production path.
                window.events.closing -= guard.on_closing
                window.destroy()

    try:
        webview.start(probe, gui='edgechromium', debug=False, private_mode=True,
                      storage_path=str(output / 'webview'))
    finally:
        jobs.close()
        server.close()

    # New Store connection after native shutdown: do not rely on frontend memory.
    reopened = Store(store.root).get('documents', document['id'])['markdown']
    if reopened != expected:
        failures.append({'error': 'Reopened synthetic SQLite did not contain the expected latest text.'})
    result = {'success': not failures, 'case': args.case, 'debug': False,
              'native_form_closing': True, 'real_bridge_sqlite': True,
              'reopened_sqlite_matches': reopened == expected, 'saves': controls['saves'],
              'observations': observations, 'failures': failures,
              'limits': ['Programmatic native Close, not a physical title-bar click.',
                         'Save failure/delay injected; not physical disk-full or OS shutdown.',
                         'Source WebView2 app; not frozen/installed MSIX. No speech generation.']}
    (output / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
    return 1 if failures else 0


if __name__ == '__main__':
    multiprocessing.freeze_support()
    raise SystemExit(main())

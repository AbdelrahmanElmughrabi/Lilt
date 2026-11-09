"""Source navigation/media probes with fresh synthetic libraries and loopback origins."""
from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import shutil
import socket
import struct
import subprocess
import sys
import threading
import time
import traceback
import uuid
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('navigation', 'media'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / '.tmp') or output == ROOT / '.tmp':
        parser.error('Use a new output subdirectory inside this workspace .tmp.')
    output.mkdir(parents=True, exist_ok=False)
    foreign_requests = []

    class Foreign(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            foreign_requests.append({'path': self.path, 'referer': self.headers.get('Referer'),
                                     'cookie': self.headers.get('Cookie')})
            body = b'<!doctype html><title>Controlled foreign origin</title><h1>Foreign fixture</h1>'
            if args.mode == 'navigation':
                body += (b'<script>fetch("/executed-foreign-page"); window.chrome?.webview?.postMessage('
                         b'["save_settings", "[{\\"theme\\":\\"dark\\"}]", "foreignProbe"]);</script>')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    from backend.server import AppServer
    from backend.storage import Store
    store = Store(output / 'library')
    foreign = ThreadingHTTPServer(('127.0.0.1', 0), Foreign)
    threading.Thread(target=foreign.serve_forever, daemon=True).start()
    foreign_url = f'http://127.0.0.1:{foreign.server_port}/'
    server = None
    jobs = None
    result = {'success': False, 'mode': args.mode, 'checks': []}
    try:
        if args.mode == 'media':
            assets = output / 'assets'
            assets.mkdir()
            (assets / 'index.html').write_text('<!doctype html><title>Local resource fixture</title><h1>Local fixture</h1>', encoding='utf-8')
            key = uuid.uuid4().hex
            folder = store.root / 'jobs' / key
            folder.mkdir()
            with wave.open(str(folder / 'recording.wav'), 'wb') as audio:
                audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(24000)
                audio.writeframes(b''.join(struct.pack('<h', 1000 if index % 40 < 20 else -1000) for index in range(24000)))
            shutil.copyfile(folder / 'recording.wav', folder / 'section-000000.wav')
            store.put('jobs', {'id': key, 'state': 'completed', 'completed': 1, 'total': 1,
                              'title': 'Synthetic tone', 'created': 1, 'duration': 1})
            server = AppServer(assets, store); server.start()
            command = [shutil.which('node'), str(ROOT / 'tools/r02-media-check.cjs'),
                       server.url, foreign_url, key, str(output / 'browser-results.json')]
            run = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=60)
            (output / 'browser.log').write_text(run.stdout + run.stderr, encoding='utf-8')
            result = json.loads((output / 'browser-results.json').read_text())
            result['exit_code'] = run.returncode
            if run.returncode:
                result['success'] = False
        else:
            import webview
            from backend.bridge import Bridge
            from backend.desktop import install_csp_bridge
            from backend.jobs import Jobs
            from backend.models import Models
            from backend.window_close import install_close_guard

            document = store.document('Original navigation fixture.', 'Navigation fixture')
            models = Models(store.root / 'models')
            jobs = Jobs(store, models)
            bridge = Bridge(store, models, jobs)
            server = AppServer(ROOT / 'frontend/dist', store); server.start()
            install_csp_bridge(ROOT / 'assets/desktop-api.js')
            window = webview.create_window('Violilt R-02 navigation check', server.url, js_api=bridge, width=1120, height=800)
            bridge._window = window
            guard = install_close_guard(window)
            marker = uuid.uuid4().hex
            expected = 'Synthetic pending edit survives canceled navigation.'
            navigation = []
            with socket.socket() as reservation:
                reservation.bind(('127.0.0.1', 0))
                debug_port = reservation.getsockname()[1]
            os.environ['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = f'--remote-debugging-port={debug_port}'

            def ui(operation):
                from System import Action
                done = threading.Event()
                box = {}

                def invoke():
                    try:
                        box['value'] = operation(window.native.browser.webview.CoreWebView2)
                    except Exception as error:
                        box['error'] = error
                    finally:
                        done.set()

                window.native.browser.webview.BeginInvoke(Action(invoke))
                if not done.wait(5):
                    raise TimeoutError('Native UI dispatch timed out.')
                if 'error' in box:
                    raise box['error']
                return box.get('value')

            def evaluate(expression):
                task = ui(lambda core: core.ExecuteScriptAsync('JSON.stringify(' + expression + ')'))
                if not task.Wait(5000):
                    raise TimeoutError('Raw WebView script timed out; native state is separate from CDP locators.')
                value = json.loads(str(task.Result))
                return json.loads(value) if isinstance(value, str) else value

            def until(expression, timeout=15):
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    value = evaluate(expression)
                    if value:
                        return value
                    time.sleep(.05)
                raise AssertionError('Timed out: ' + expression)

            def observe(_sender, event):
                navigation.append({'uri': str(event.Uri), 'canceled': bool(event.Cancel)})

            def probe():
                nonlocal expected
                try:
                    assert window.events.loaded.wait(25)
                    until('!!document.querySelector(".home-page")')
                    ui(lambda core: window.native.browser.webview.NavigationStarting.__iadd__(observe))
                    evaluate('document.querySelector(".recent-reading").click()')
                    until('!!document.querySelector(".reading-article")')
                    evaluate('Array.from(document.querySelectorAll(".document-tabs button")).find(b => b.textContent.trim() === "Edit").click()')
                    until('!!document.querySelector("textarea.markdown-editor")')
                    evaluate('(() => {window.__r02OldApi = window.pywebview.api; window.__r02Marker = ' + json.dumps(marker) + ';'
                             'const input = document.querySelector("textarea.markdown-editor"); input.value = ' + json.dumps(expected) + ';'
                             'input.dispatchEvent(new Event("input", {bubbles:true})); return true;})()')
                    result['cases'] = []
                    for method in ('href', 'assign', 'replace', 'native'):
                        destination = foreign_url + 'navigation-' + method
                        if method == 'native':
                            ui(lambda core: core.Navigate(destination))
                        else:
                            script = ('window.location.href = ' + json.dumps(destination) if method == 'href' else
                                      'window.location.' + method + '(' + json.dumps(destination) + ')')
                            ui(lambda core: core.ExecuteScriptAsync(script))  # Do not infer navigation success from its return value.
                        time.sleep(.25)
                        snapshot = {'method': method, 'native_source': ui(lambda core: str(core.Source))}
                        snapshot['dom'] = evaluate('({body: !!document.body, marker: window.__r02Marker, '
                                                   'text: document.querySelector("textarea.markdown-editor")?.value})')
                        result['cases'].append(snapshot)
                        assert snapshot['native_source'].rstrip('/') == server.url
                        assert snapshot['dom']['marker'] == marker and snapshot['dom']['text'] == expected
                        evaluate('(() => {window.__r02ApiReplies = null; Promise.all([window.pywebview.api.get_state(), '
                                 'window.__r02OldApi.get_state()]).then(values => window.__r02ApiReplies = '
                                 'values.map(value => value.documents.length)); return true;})()')
                        snapshot['fresh_and_old_api'] = until('window.__r02ApiReplies')
                        assert snapshot['fresh_and_old_api'] == [1, 1]
                        evaluate('Array.from(document.querySelectorAll(".document-tabs button")).find(b => b.textContent.trim() === "Read").click()')
                        until('!!document.querySelector(".reading-article")')
                        evaluate('Array.from(document.querySelectorAll(".document-tabs button")).find(b => b.textContent.trim() === "Edit").click()')
                        until('!!document.querySelector("textarea.markdown-editor")')
                        snapshot['ui_action'] = True
                    evaluate('(() => {const frame = document.createElement("iframe"); frame.src = ' + json.dumps(foreign_url + 'frame') + '; document.body.append(frame); return true;})()')
                    time.sleep(.25)
                    cdp_run = subprocess.run([shutil.which('node'), str(ROOT / 'tools/r02-navigation-cdp.cjs'),
                                              str(debug_port), foreign_url, str(output / 'cdp-results.json'), server.url, marker],
                                             capture_output=True, text=True, encoding='utf-8', timeout=30)
                    (output / 'cdp.log').write_text(cdp_run.stdout + cdp_run.stderr, encoding='utf-8')
                    result['cdp'] = json.loads((output / 'cdp-results.json').read_text())
                    assert cdp_run.returncode == 0, result['cdp']
                    assert result['cdp'].get('success') is True, result['cdp']
                    result['native_after_cdp'] = {'source': ui(lambda core: str(core.Source)),
                        'dom': evaluate('({body:!!document.body,marker:window.__r02Marker,text:document.querySelector("textarea.markdown-editor")?.value})')}
                    assert result['native_after_cdp']['source'].rstrip('/') == server.url
                    assert result['native_after_cdp']['dom']['marker'] == marker
                    evaluate('(() => {window.__r02ApiReplies = null; window.pywebview.api.get_state().then(value => '
                             'window.__r02ApiReplies = value.documents.length); return true;})()')
                    assert until('window.__r02ApiReplies') == 1
                    # WebView2 may issue a preliminary GET while NavigationStarting
                    # is handled. Cancellation protects the committed document and
                    # bridge; it is not a zero-network guarantee (Microsoft docs).
                    assert not any(item['path'] in {'/executed-foreign-page', '/frame'} for item in foreign_requests)
                    assert not any(item['referer'] or item['cookie'] for item in foreign_requests)
                    assert store.settings()['theme'] != 'dark', 'Foreign content reached the native bridge.'
                    assert len(navigation) >= 4 and all(item['canceled'] for item in navigation)
                    expected += ' Final edit immediately before closing.'
                    evaluate('(() => {const input = document.querySelector("textarea.markdown-editor"); input.value = ' +
                             json.dumps(expected) + '; input.dispatchEvent(new Event("input", {bubbles:true})); return true;})()')
                    assert store.get('documents', document['id'])['markdown'] != expected
                    window.destroy()
                    assert window.events.closed.wait(15), 'Normal close failed after canceled navigation.'
                    assert Store(store.root).get('documents', document['id'])['markdown'] == expected
                    result.update(success=True, navigation_events=navigation, foreign_requests=foreign_requests,
                                  debug=False, loopback_cdp_instrumentation=True, close_after_navigation=True,
                                  checks=['Four foreign top-level attempts retained native source, document identity/text, fresh/old API and UI actions.',
                                          'Foreign frame/response script did not execute or reach bridge; normal close retained synthetic text.'],
                                  navigation_network_limit='Preliminary GETs may reach the destination even when navigation is canceled; none carried Referer/cookies here.',
                                  navigation_reference='https://learn.microsoft.com/en-us/microsoft-edge/webview2/reference/win32/icorewebview2navigationstartingeventargs',
                                  limits=['Raw native WebView task and loopback CDP instrumentation; script/native Close, not physical clicks.',
                                          'One source WebView2/Windows machine; not an installed package or speech-generation check.'])
                except Exception as error:
                    result.update(error=str(error), traceback=traceback.format_exc(), navigation_events=navigation,
                                  foreign_requests=foreign_requests)
                    result['close_guard'] = {'armed': guard.armed, 'request': guard.request,
                                             'finishing': guard.finishing, 'approved': guard.approved}
                    result['saved_text_after_failure'] = store.get('documents', document['id'])['markdown']
                    try:
                        result['close_ui_after_failure'] = evaluate('({dialog:document.querySelector("dialog[open]")?.innerText,'
                            'editor:document.querySelector("textarea.markdown-editor")?.value,'
                            'error:document.querySelector(".error-banner")?.textContent})')
                    except Exception as diagnostic:
                        result['close_ui_diagnostic_error'] = str(diagnostic)
                    try:
                        result['native_source_after_failure'] = ui(lambda core: str(core.Source))
                    except Exception:
                        pass
                finally:
                    if not window.events.closed.is_set():
                        window.events.closing -= guard.on_closing  # Disposable test cleanup only.
                        window.destroy()

            webview.start(probe, gui='edgechromium', debug=False, private_mode=True, storage_path=str(output / 'webview'))
    except Exception as error:
        result.update(error=str(error), traceback=traceback.format_exc())
    finally:
        if jobs:
            jobs.close()
        if server:
            server.close()
        foreign.shutdown(); foreign.server_close()
        (output / 'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
    return 0 if result['success'] else 1


if __name__ == '__main__':
    multiprocessing.freeze_support()
    raise SystemExit(main())

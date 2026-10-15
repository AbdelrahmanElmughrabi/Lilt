from __future__ import annotations

from pathlib import Path
import json
import threading


def _install_file_drop_transport(window):
    """Resolve real File objects using WebView2, without exposing path strings in JS.

    Like the CSP adapter, this targets the pinned pywebview 6.2.1 Windows backend.
    Other messages continue through its original native handler unchanged.
    """
    if getattr(window, '_lilt_drop_transport', False) is True:
        return
    browser = window.native.browser
    control = browser.webview
    original = browser.on_script_notify

    def receive(sender, args):
        try:
            message = json.loads(args.get_WebMessageAsJson())
        except (ValueError, TypeError):
            return original(sender, args)
        if not isinstance(message, dict) or message.get('type') != 'lilt:file-drop':
            return original(sender, args)
        request = message.get('id')
        if not isinstance(request, str) or not request.isalnum():
            return
        try:
            objects = args.get_AdditionalObjects()
            paths = [str(item.Path) for item in (list(objects) if objects is not None else [])
                     if 'CoreWebView2File' in str(type(item))]
        except Exception:
            paths = []

        def import_files():
            try:
                result = window._js_api.import_dropped_documents(paths)
                response = {'value': json.dumps(result)}
            except Exception as exc:
                response = {'isError': True, 'value': json.dumps({
                    'name': type(exc).__name__, 'message': str(exc), 'stack': ''})}
            window.run_js('window.pywebview._returnValuesCallbacks["import_dropped_documents"]['
                          + json.dumps(request) + '](' + json.dumps(response) + ')')

        threading.Thread(target=import_files, daemon=True).start()

    control.WebMessageReceived -= original
    control.WebMessageReceived += receive
    # Keep the Python delegate alive for the lifetime of the native window.
    window._lilt_drop_handler = receive
    window._lilt_drop_transport = True


def install_csp_bridge(script: Path):
    """Replace API construction before pywebview runs its ready script.

    This process-local adapter targets pywebview 6.2.1's JS loader. It leaves
    installed library files, native IPC and the application's CSP unchanged.
    """
    from webview import util

    if getattr(util.load_js_files, '_lilt_csp_bridge', False) is True:
        return
    original = util.load_js_files
    builder = script.read_text(encoding='utf-8')

    def load_js_files(window, platform):
        if platform == 'edgechromium' and getattr(window, 'native', None) is not None:
            _install_file_drop_transport(window)
        # Native return delivery also calls evaluate_js, whose generic wrapper
        # uses eval. These callback statements do not need an evaluated result.
        if getattr(window, '_lilt_csp_callbacks', False) is not True:
            evaluate = window.evaluate_js

            def evaluate_js(code, callback=None):
                if callback is None and code.startswith('window.pywebview._returnValuesCallbacks['):
                    return window.run_js(code)
                return evaluate(code, callback)

            window.evaluate_js = evaluate_js
            window._lilt_csp_callbacks = True
        code, finish = original(window, platform)
        return code + '\n' + builder, finish

    load_js_files._lilt_csp_bridge = True
    util.load_js_files = load_js_files

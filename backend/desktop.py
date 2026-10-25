from __future__ import annotations

from pathlib import Path
import json
import re
import threading
from urllib.parse import urlsplit


# Explicit transport contract: private attributes and newly added methods are
# never exposed implicitly by pywebview's dotted-attribute resolver.
NATIVE_METHODS = {
    'get_state': (0, 0), 'get_stream': (1, 1), 'start_benchmark': (0, 0),
    'stop_benchmark': (0, 0), 'warm_engine': (0, 0), 'release_engine': (0, 0),
    'clear_cache': (0, 0), 'get_document': (1, 1), 'save_document': (2, 2),
    'new_document': (0, 0), 'remove_document': (1, 1), 'reveal_document': (1, 1),
    'reveal_recording': (1, 1), 'remove_recording': (1, 2), 'import_document': (0, 0),
    'prepare_document': (2, 2), 'save_settings': (1, 1), 'generate': (3, 3),
    'preview_voice': (2, 3), 'cancel_generation': (0, 0), 'resume_job': (1, 1),
    'save_position': (2, 2), 'export_recording': (1, 1), 'setup_model': (0, 0),
    'import_model': (0, 0), 'open_microsoft_privacy': (1, 1), 'complete_welcome': (0, 0),
    'open_publisher_link': (1, 1),
}
MAX_NATIVE_MESSAGE_BYTES = 8 * 1024 * 1024


def _request_id(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9]{1,64}', value) is not None


def _allowed_native_call(window, message):
    if not isinstance(message, list) or len(message) != 3:
        return False
    name, encoded, identifier = message
    if not isinstance(name, str) or not isinstance(encoded, str) or not _request_id(identifier):
        return False
    try:
        params = json.loads(encoded)
    except (ValueError, TypeError, RecursionError):
        return False
    if name == 'pywebviewAsyncCallback':
        # Only callbacks already registered by Python may be delivered. Other
        # framework proxies (DOM/state/window movement) are unused by this app.
        callbacks = getattr(window, '_callbacks', {})
        return isinstance(callbacks, dict) and callable(callbacks.get(identifier))
    bounds = NATIVE_METHODS.get(name)
    return (bounds is not None and isinstance(params, list)
            and bounds[0] <= len(params) <= bounds[1]
            and callable(getattr(window._js_api, name, None)))


def _trusted_page(window, value):
    """Pin the native bridge to the original loopback app page, not its current URL."""
    try:
        original, requested = urlsplit(window.original_url), urlsplit(str(value))
        return (original.scheme == requested.scheme == 'http'
                and original.hostname == '127.0.0.1' and original.port is not None
                and requested.netloc == original.netloc
                and original.username is None and original.password is None
                and requested.path in {'', '/', '/index.html'})
    except (AttributeError, TypeError, ValueError):
        return False


def _install_file_drop_transport(window):
    """Pin navigation/native messages and resolve WebView2 File objects.

    Like the CSP adapter, this targets the pinned pywebview 6.2.1 Windows backend.
    Only the explicit native call contract reaches the original handler.
    """
    if getattr(window, '_violilt_drop_transport', False) is True:
        return
    browser = window.native.browser
    control = browser.webview
    original = browser.on_script_notify

    def navigation(_sender, args):
        if not _trusted_page(window, args.Uri):
            args.Cancel = True

    def frame_navigation(_sender, args):
        args.Cancel = True

    control.NavigationStarting += navigation
    control.CoreWebView2.FrameNavigationStarting += frame_navigation

    completed = getattr(browser, 'on_navigation_completed', None)
    if callable(completed) and hasattr(control, 'NavigationCompleted'):
        def navigation_completed(sender, args):
            # pywebview 6.2.1 reinjects on every completion, including canceled
            # navigation. The original document is intact on cancellation;
            # reinjection would reset callbacks for its in-flight save/poll.
            if (not args.IsSuccess and str(args.WebErrorStatus) == 'OperationCanceled'
                    and _trusted_page(window, sender.Source)):
                return
            return completed(sender, args)

        control.NavigationCompleted -= completed
        control.NavigationCompleted += navigation_completed
        window._violilt_navigation_completed_handler = navigation_completed

    def receive(sender, args):
        # Guard ordinary pywebview calls as well as the custom file-drop path.
        # WebMessageReceived.Source is supplied by WebView2, not by message JSON.
        if not _trusted_page(window, args.Source):
            return
        try:
            encoded = args.get_WebMessageAsJson()
            if not isinstance(encoded, str) or len(encoded.encode('utf-8')) > MAX_NATIVE_MESSAGE_BYTES:
                return
            message = json.loads(encoded)
        except (ValueError, TypeError, RecursionError):
            return
        if isinstance(message, dict) and message.get('type') in {'violilt:close-ready', 'violilt:close-response'}:
            guard = getattr(window, '_violilt_close_guard', None)
            if guard is not None:
                if message['type'] == 'violilt:close-ready':
                    guard.armed = True
                elif _request_id(message.get('id')):
                    guard.respond(message['id'], message.get('saved'))
            return
        if not isinstance(message, dict) or message.get('type') != 'violilt:file-drop':
            if _allowed_native_call(window, message):
                return original(sender, args)
            return
        request = message.get('id')
        if not _request_id(request):
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
            script = ('window.pywebview._returnValuesCallbacks["import_dropped_documents"]['
                      + json.dumps(request) + '](' + json.dumps(response) + ')')

            def deliver():
                core = control.CoreWebView2
                if _trusted_page(window, core.Source):
                    # Do not use run_js here: its result wait blocks the UI thread.
                    core.ExecuteScriptAsync(script)

            # WebView2 properties and script dispatch both belong to the UI thread.
            from System import Action
            control.BeginInvoke(Action(deliver))

        threading.Thread(target=import_files, daemon=True).start()

    control.WebMessageReceived -= original
    control.WebMessageReceived += receive
    # Keep the Python delegate alive for the lifetime of the native window.
    window._violilt_drop_handler = receive
    window._violilt_navigation_handler = navigation
    window._violilt_frame_handler = frame_navigation
    window._violilt_drop_transport = True


def install_csp_bridge(script: Path):
    """Replace API construction before pywebview runs its ready script.

    This process-local adapter targets pywebview 6.2.1's JS loader. It leaves
    installed library files, native IPC and the application's CSP unchanged.
    """
    from webview import util

    if getattr(util.load_js_files, '_violilt_csp_bridge', False) is True:
        return
    original = util.load_js_files
    builder = script.read_text(encoding='utf-8')

    def load_js_files(window, platform):
        if platform == 'edgechromium' and getattr(window, 'native', None) is not None:
            _install_file_drop_transport(window)
        # Native return delivery also calls evaluate_js, whose generic wrapper
        # uses eval. These callback statements do not need an evaluated result.
        if getattr(window, '_violilt_csp_callbacks', False) is not True:
            evaluate = window.evaluate_js

            def evaluate_js(code, callback=None):
                if callback is None and code.startswith('window.pywebview._returnValuesCallbacks['):
                    return window.run_js(code)
                return evaluate(code, callback)

            window.evaluate_js = evaluate_js
            window._violilt_csp_callbacks = True
        code, finish = original(window, platform)
        return code + '\n' + builder, finish

    load_js_files._violilt_csp_bridge = True
    util.load_js_files = load_js_files

from __future__ import annotations

from pathlib import Path


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

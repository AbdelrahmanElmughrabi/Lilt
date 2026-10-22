"""Normal-close handshake; all native callbacks run on the WebView UI thread."""
from __future__ import annotations

import json
import logging
import uuid


class CloseGuard:
    def __init__(self, window):
        self.window = window
        self.armed = False
        self.request = None
        self.finishing = False
        self.approved = False

    def _queue(self, callback):
        from System import Action
        self.window.native.browser.webview.BeginInvoke(Action(callback))

    def _trusted(self):
        from backend.desktop import _trusted_page
        return _trusted_page(self.window, self.window.native.browser.webview.CoreWebView2.Source)

    def on_closing(self):
        if self.approved:
            self.approved = False
            self.request = None
            self.finishing = False
            return True
        # Before frontend initialization there is no editable document to drain.
        if not self.armed:
            return True
        if self.request is None:
            request = self.request = uuid.uuid4().hex

            def dispatch():
                if self.request != request:
                    return
                try:
                    if not self._trusted():
                        self.request = None
                        return
                    script = ('window.dispatchEvent(new CustomEvent("violilt:close-request", '
                              '{detail: {id: ' + json.dumps(request) + '}}));')
                    self.window.native.browser.webview.CoreWebView2.ExecuteScriptAsync(script)
                except Exception:
                    self.request = None
                    logging.exception('Could not request a safe window close')

            try:
                # Closing is synchronous on the UI thread. Never wait for JS here.
                self._queue(dispatch)
            except Exception:
                self.request = None
                logging.exception('Could not dispatch a safe window close')
        return False

    def respond(self, request, saved):
        if (not isinstance(request, str) or request != self.request
                or type(saved) is not bool):
            return
        if not saved:
            self.request = None
            self.finishing = False
            return
        if self.finishing:
            return
        self.finishing = True

        def finish():
            try:
                if self.request == request and self._trusted():
                    self.approved = True
                    self.window.destroy()
            except Exception:
                logging.exception('Could not finish a safe window close')
            finally:
                self.approved = False
                if self.request == request:
                    self.finishing = False
                    self.request = None

        try:
            self._queue(finish)
        except Exception:
            self.finishing = False
            self.request = None
            logging.exception('Could not dispatch window close completion')


def install_close_guard(window):
    guard = getattr(window, '_violilt_close_guard', None)
    if guard is None:
        guard = CloseGuard(window)
        window._violilt_close_guard = guard
        window.events.closing += guard.on_closing
    return guard

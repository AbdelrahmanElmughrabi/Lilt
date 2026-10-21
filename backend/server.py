from __future__ import annotations

import mimetypes
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit


class AppServer:
    def __init__(self, assets, store):
        self.assets, self.store = assets.resolve(), store
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                self._send(False)

            def do_HEAD(self):
                self._send(True)

            def _send(self, head):
                if self.headers.get("Host") not in {f"127.0.0.1:{owner.httpd.server_port}", f"localhost:{owner.httpd.server_port}"}:
                    self.send_error(403)
                    return
                route = unquote(urlsplit(self.path).path)
                media = re.fullmatch(r"/media/([0-9a-f]{32})\.wav", route)
                section = re.fullmatch(r"/media/([0-9a-f]{32})/section-(\d{6})\.wav", route)
                if section:
                    try:
                        job = owner.store.get('jobs', section[1])
                        index = int(section[2])
                        if index >= job.get('completed', 0) or index >= job['total']:
                            raise ValueError()
                    except (ValueError, KeyError):
                        self.send_error(404)
                        return
                    path = owner.store.root / 'jobs' / section[1] / f'section-{index:06d}.wav'
                    content_type = 'audio/wav'
                elif media:
                    try:
                        job = owner.store.get("jobs", media[1])
                        if job["state"] != "completed":
                            raise ValueError()
                    except ValueError:
                        self.send_error(404)
                        return
                    path = owner.store.root / "jobs" / media[1] / "recording.wav"
                    content_type = "audio/wav"
                else:
                    path = (owner.assets / (route.lstrip("/") or "index.html")).resolve()
                    if not path.is_relative_to(owner.assets):
                        self.send_error(403)
                        return
                    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
                    if path.suffix == ".js":
                        content_type = "text/javascript"
                if not path.is_file():
                    self.send_error(404)
                    return
                size = path.stat().st_size
                start, end, status = 0, size - 1, 200
                requested = self.headers.get("Range")
                if requested:
                    match = re.fullmatch(r"bytes=(\d*)-(\d*)", requested)
                    if not match or not any(match.groups()):
                        self.send_error(416)
                        return
                    if match[1]:
                        start, end = int(match[1]), min(int(match[2]), end) if match[2] else end
                    else:
                        start = max(0, size - int(match[2]))
                    if start > end or start >= size:
                        self.send_response(416)
                        self.send_header("Content-Range", f"bytes */{size}")
                        self.end_headers()
                        return
                    status = 206
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(end - start + 1))
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("X-Frame-Options", "DENY")
                self.send_header("Content-Security-Policy", "frame-ancestors 'none'")
                self.send_header("Cross-Origin-Resource-Policy", "same-origin")
                if status == 206:
                    self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.end_headers()
                if not head:
                    try:
                        with path.open("rb") as audio:
                            audio.seek(start)
                            remaining = end - start + 1
                            while remaining:
                                block = audio.read(min(65536, remaining))
                                if not block:
                                    break
                                self.wfile.write(block)
                                remaining -= len(block)
                    except (ConnectionResetError, BrokenPipeError):
                        pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.httpd.daemon_threads = True
        self.url = f"http://127.0.0.1:{self.httpd.server_port}"

    def start(self):
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()

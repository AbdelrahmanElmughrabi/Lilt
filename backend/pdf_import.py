"""Bound selectable-text extraction in a disposable process; never execute PDF actions."""
from __future__ import annotations

import io
import json
import multiprocessing
import threading
import time

import psutil

from .limits import MAX_MARKDOWN_BYTES

MAX_PDF_BYTES = 20 * 1024 * 1024
MAX_PDF_PAGES = 200
PDF_TIMEOUT_SECONDS = 20
PDF_MEMORY_BYTES = 512 * 1024 * 1024
_extraction_lock = threading.Lock()
_ERRORS = {
    'read': 'This PDF could not be read. It may be damaged or use unsupported PDF features.',
    'encrypted': 'This PDF is encrypted. Import an unencrypted copy that you are allowed to use.',
    'pages': 'Choose a PDF with up to 200 pages. Split larger documents into smaller readings.',
    'empty': 'This PDF has no selectable text. Scanned PDFs need OCR before import.',
    'text': 'This PDF needs more than 2 MB of text. Split it into smaller readings.',
}


class _ImportError(ValueError):
    pass


def _read_text(body, page_limit, text_limit):
    # Keep parser imports in the worker. Strict parsing avoids silent file repair.
    from pypdf import PdfReader
    from pypdf.errors import DependencyError

    try:
        reader = PdfReader(io.BytesIO(body), strict=True)
    except DependencyError:
        # Encryption can require an optional crypto extra even before page access.
        raise _ImportError('encrypted') from None
    if reader.is_encrypted:
        raise _ImportError('encrypted')
    if len(reader.pages) > page_limit:
        raise _ImportError('pages')
    parts, size = [], 0
    for page in reader.pages:
        text = (page.extract_text() or '').strip()
        if not text:
            continue
        size += len(text.encode('utf-8')) + (2 if parts else 0)
        if size > text_limit:
            raise _ImportError('text')
        parts.append(text)
    if not parts:
        raise _ImportError('empty')
    return '\n\n'.join(parts)


def _extract_worker(body, connection, page_limit, text_limit):
    try:
        try:
            result = {'text': _read_text(body, page_limit, text_limit)}
        except _ImportError as error:
            result = {'error': str(error)}
        except Exception:
            # Do not expose parser diagnostics, file contents or paths to the UI.
            result = {'error': 'read'}
        connection.send_bytes(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    finally:
        connection.close()


def extract_pdf_text(body):
    """Return text or a reviewable error, terminating stalled/oversize workers.

    The RSS threshold is monitored, not an OS sandbox or an instantaneous cap.
    No source path is passed to the parser and no source file is modified.
    """
    if not isinstance(body, bytes) or len(body) > MAX_PDF_BYTES:
        raise ValueError('Choose a PDF up to 20 MB. Split larger documents into smaller readings.')
    with _extraction_lock:
        context = multiprocessing.get_context('spawn')
        receiver, sender = context.Pipe(duplex=False)
        process = context.Process(target=_extract_worker,
                                  args=(body, sender, MAX_PDF_PAGES, MAX_MARKDOWN_BYTES),
                                  name='Violilt PDF import', daemon=True)
        started = False
        try:
            process.start()
            started = True
            sender.close()
            deadline = time.monotonic() + PDF_TIMEOUT_SECONDS
            monitor = psutil.Process(process.pid)
            while True:
                try:
                    if monitor.memory_info().rss > PDF_MEMORY_BYTES:
                        raise ValueError('This PDF used too much memory to import. Split it into smaller readings.')
                except psutil.NoSuchProcess:
                    pass
                if time.monotonic() >= deadline:
                    raise ValueError('This PDF took too long to import. Split it into smaller readings.')
                if receiver.poll(0.05):
                    # JSON bytes avoid unpickling any result from the parser process.
                    wire = receiver.recv_bytes(6 * MAX_MARKDOWN_BYTES + 4096)
                    result = json.loads(wire.decode('utf-8'))
                    if not isinstance(result, dict) or not isinstance(result.get('text'), str):
                        code = result.get('error') if isinstance(result, dict) else None
                        raise ValueError(_ERRORS.get(code, _ERRORS['read']) if isinstance(code, str) else _ERRORS['read'])
                    text = result['text']
                    if len(text.encode('utf-8')) > MAX_MARKDOWN_BYTES:
                        raise ValueError(_ERRORS['text'])
                    return text
                if not process.is_alive():
                    raise ValueError(_ERRORS['read'])
        except (OSError, EOFError, UnicodeError, json.JSONDecodeError, psutil.Error, RuntimeError):
            raise ValueError(_ERRORS['read']) from None
        finally:
            sender.close()
            receiver.close()
            if started:
                if process.is_alive():
                    process.terminate()
                process.join(timeout=1)
                if process.is_alive():
                    process.kill()
                    process.join(timeout=1)
                process.close()

"""Hold an OS-released lock before opening or recovering a library."""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path


class LibraryInUse(RuntimeError):
    pass


@contextmanager
def library_lock(directory: Path):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    # Keep the file in place after closing: unlinking a lock file can let another
    # process lock a different file while a previous handle still owns the old one.
    stream = (directory / '.violilt-instance.lock').open('a+b')
    acquired = False
    try:
        if os.name == 'nt':
            import msvcrt
            if stream.seek(0, os.SEEK_END) == 0:
                stream.write(b'\0')
                stream.flush()
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise LibraryInUse('Violilt is already open for this library. Close its existing window and try again.') from exc
        else:
            import fcntl
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise LibraryInUse('Violilt is already open for this library. Close its existing window and try again.') from exc
        acquired = True
        yield directory
    finally:
        try:
            if acquired:
                if os.name == 'nt':
                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        finally:
            stream.close()

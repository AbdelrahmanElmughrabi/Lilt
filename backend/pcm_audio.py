"""Bounded stored-PCM reads, without native codec autodetection."""
from __future__ import annotations

import os
import struct
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

RATE = 24000
MAX_AUDIO_BYTES = 4_000_000_000
MAX_METADATA_BYTES = 1024 * 1024
MAX_CHUNKS = 1024
BLOCK_BYTES = 131072
PCM_GUID = bytes.fromhex('0100000000001000800000aa00389b71')
INVALID = 'This saved audio is not a complete supported PCM WAV recording.'


@dataclass(frozen=True)
class PCMInfo:
    frames: int
    data_offset: int
    data_bytes: int
    samplerate: int = RATE
    channels: int = 1
    subtype: str = 'PCM_16'
    format: str = 'WAV'

    @property
    def duration(self):
        return self.frames / self.samplerate


def _stamp(stream):
    stat = os.fstat(stream.fileno())
    return stat.st_size, stat.st_mtime_ns


def _inspect(stream, size):
    header = stream.read(12)
    if len(header) != 12 or size < 46:
        raise ValueError(INVALID)
    magic, declared, kind = struct.unpack('<4sI4s', header)
    if magic != b'RIFF' or kind != b'WAVE' or declared + 8 != size:
        raise ValueError(INVALID)
    offset, count, metadata = 12, 0, 0
    seen_format, data = False, None
    while offset < size:
        count += 1
        if count > MAX_CHUNKS or size - offset < 8:
            raise ValueError(INVALID)
        stream.seek(offset)
        chunk = stream.read(8)
        if len(chunk) != 8:
            raise ValueError(INVALID)
        name, length = struct.unpack('<4sI', chunk)
        start = offset + 8
        end = start + length
        offset = end + (length & 1)
        if offset > size:
            raise ValueError(INVALID)
        if name == b'data':
            if not seen_format or data is not None or not 0 < length <= MAX_AUDIO_BYTES or length % 2:
                raise ValueError(INVALID)
            data = (start, length)
            continue
        metadata += length + 8 + (length & 1)
        if metadata > MAX_METADATA_BYTES:
            raise ValueError(INVALID)
        if name != b'fmt ':
            continue  # Never interpret incidental metadata; omit it from the view.
        if seen_format or length not in (16, 18, 40):
            raise ValueError(INVALID)
        fmt = stream.read(length)
        if len(fmt) != length:
            raise ValueError(INVALID)
        code, channels, rate, byte_rate, alignment, bits = struct.unpack('<HHIIHH', fmt[:16])
        if (channels, rate, byte_rate, alignment, bits) != (1, RATE, RATE * 2, 2, 16):
            raise ValueError(INVALID)
        if code == 1:
            if length != 16 and (length != 18 or fmt[16:] != b'\0\0'):
                raise ValueError(INVALID)
        elif code == 0xFFFE:
            if length != 40:
                raise ValueError(INVALID)
            extension, valid_bits, mask = struct.unpack('<HHI', fmt[16:24])
            if extension != 22 or valid_bits != 16 or mask.bit_count() > 1 or fmt[24:] != PCM_GUID:
                raise ValueError(INVALID)
        else:
            raise ValueError(INVALID)
        seen_format = True
    if data is None:
        raise ValueError(INVALID)
    return PCMInfo(data[1] // 2, data[0], data[1])


class PCMReader:
    """Canonical WAV view over a validated handle; each read is bounded."""
    def __init__(self, stream):
        self._stream = stream
        self._initial = _stamp(stream)
        self.info = _inspect(stream, self._initial[0])
        self.size = 44 + self.info.data_bytes
        self._header = struct.pack('<4sI4s4sIHHIIHH4sI', b'RIFF', self.size - 8, b'WAVE',
                                   b'fmt ', 16, 1, 1, RATE, RATE * 2, 2, 16, b'data', self.info.data_bytes)
        self._position = 0
        self._unchanged()

    def _unchanged(self):
        if _stamp(self._stream) != self._initial:
            raise ValueError('The saved audio changed while it was being read. Try again.')

    def seek(self, offset):
        if not isinstance(offset, int) or not 0 <= offset <= self.size:
            raise ValueError('Invalid audio position.')
        self._position = offset

    def read(self, size):
        if not isinstance(size, int) or size < 0:
            raise ValueError('Use bounded audio reads.')
        self._unchanged()
        count = min(size, BLOCK_BYTES, self.size - self._position)
        prefix = self._header[self._position:min(44, self._position + count)] if self._position < 44 else b''
        self._position += len(prefix)
        count -= len(prefix)
        if count:
            self._stream.seek(self.info.data_offset + self._position - 44)
            block = self._stream.read(count)
            if len(block) != count:
                raise ValueError('The saved audio became incomplete while it was being read.')
            self._position += count
            prefix += block
        self._unchanged()
        return prefix

    def blocks(self):
        self.seek(44)
        while block := self.read(BLOCK_BYTES):
            yield block


@contextmanager
def open_pcm(path):
    with Path(path).open('rb') as stream:
        yield PCMReader(stream)


def audio_info(path):
    try:
        with open_pcm(path) as reader:
            return reader.info
    except (OSError, ValueError):
        return None


def copy_pcm(source, destination):
    # Source validation precedes opening the destination. Callers stage writes
    # when replacing existing files so a later I/O failure cannot damage them.
    with open_pcm(source) as reader, Path(destination).open('wb') as output:
        while block := reader.read(BLOCK_BYTES):
            output.write(block)

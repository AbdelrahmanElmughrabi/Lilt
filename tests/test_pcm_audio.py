"""Stored PCM boundary: no native codec input and no unbounded inspection."""
import io
import os
import sys
import struct
import tempfile
import unittest
import urllib.error
import urllib.request
import uuid
import wave
from pathlib import Path
from unittest.mock import patch

from backend.cache import SectionCache
from backend.pcm_audio import (BLOCK_BYTES, MAX_CHUNKS, MAX_METADATA_BYTES, PCM_GUID,
                               audio_info, copy_pcm, open_pcm)
from backend.sections import published_sections
from backend.server import AppServer
from backend.storage import Store


SAMPLES = b'\x00\x80\xff\x7f\x01\x00'
FMT = struct.pack('<HHIIHH', 1, 1, 24000, 48000, 2, 16)


def chunk(name, body):
    return name + struct.pack('<I', len(body)) + body + (b'\0' if len(body) % 2 else b'')


def wav(*chunks):
    body = b'WAVE' + b''.join(chunks)
    return b'RIFF' + struct.pack('<I', len(body)) + body


def pcm(samples=SAMPLES, fmt=FMT, metadata=b''):
    return wav(chunk(b'fmt ', fmt), metadata, chunk(b'data', samples))


class PCMTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'section.wav'

    def write(self, body):
        self.path.write_bytes(body)
        return self.path

    def assert_invalid(self, body):
        self.write(body)
        before = self.path.read_bytes()
        with patch.dict(sys.modules, {'soundfile': None, '_soundfile': None}):
            self.assertIsNone(audio_info(self.path))
            with self.assertRaises(ValueError):
                with open_pcm(self.path):
                    self.fail('Unsupported file opened')
        self.assertEqual(self.path.read_bytes(), before)

    def test_standard_pcm_has_exact_info_and_canonical_bytes_without_native_calls(self):
        self.write(pcm())
        with patch.dict(sys.modules, {'soundfile': None, '_soundfile': None}):
            info = audio_info(self.path)
            self.assertEqual((info.frames, info.channels, info.samplerate, info.subtype), (3, 1, 24000, 'PCM_16'))
            self.assertEqual(info.duration, 3 / 24000)
            with open_pcm(self.path) as source:
                self.assertEqual(source.read(100), pcm())
                self.assertEqual(source.read(1), b'')
                self.assertEqual(b''.join(source.blocks()), SAMPLES)

    def test_metadata_and_pcm_extensions_produce_one_canonical_view(self):
        for fmt in (FMT, FMT + b'\0\0', struct.pack('<HHIIHHHHI', 0xFFFE, 1, 24000, 48000, 2, 16, 22, 16, 4) + PCM_GUID):
            with self.subTest(fmt_length=len(fmt)):
                original = pcm(fmt=fmt, metadata=chunk(b'JUNK', b'odd'))
                self.write(original)
                with open_pcm(self.path) as source:
                    self.assertEqual(source.size, len(pcm()))
                    self.assertEqual(source.read(1000), pcm())
                self.assertEqual(self.path.read_bytes(), original)

    def test_renamed_containers_are_rejected_before_native_open(self):
        for body in (b'FORM\0\0\0\x10AIFF' + b'\0' * 40, b'\0' * 80, b'OggS' + b'\0' * 60,
                     b'RF64' + pcm()[4:], b'RIFX' + pcm()[4:]):
            with self.subTest(magic=body[:4]):
                self.assert_invalid(body)

    def test_compression_channels_rate_width_and_alignment_are_rejected(self):
        for values in ((3, 1, 24000, 48000, 2, 16), (17, 1, 24000, 48000, 2, 16),
                       (1, 2, 24000, 96000, 4, 16), (1, 1, 44100, 88200, 2, 16),
                       (1, 1, 24000, 72000, 3, 24), (1, 1, 24000, 123, 2, 16),
                       (1, 1, 24000, 48000, 4, 16)):
            with self.subTest(format=values):
                self.assert_invalid(pcm(fmt=struct.pack('<HHIIHH', *values)))

    def test_extensible_subformat_and_valid_bits_are_checked(self):
        for bits, mask, guid in ((15, 4, PCM_GUID), (16, 3, PCM_GUID), (16, 4, bytes(16))):
            self.assert_invalid(pcm(fmt=struct.pack('<HHIIHHHHI', 0xFFFE, 1, 24000, 48000, 2, 16, 22, bits, mask) + guid))

    def test_duplicate_missing_and_out_of_order_chunks_are_rejected(self):
        for body in (wav(chunk(b'data', SAMPLES), chunk(b'fmt ', FMT)),
                     wav(chunk(b'fmt ', FMT), chunk(b'fmt ', FMT), chunk(b'data', SAMPLES)),
                     wav(chunk(b'fmt ', FMT), chunk(b'data', SAMPLES), chunk(b'data', SAMPLES)),
                     wav(chunk(b'fmt ', FMT)), wav(chunk(b'data', SAMPLES))):
            self.assert_invalid(body)

    def test_truncation_trailing_bytes_padding_and_declared_extents_are_checked(self):
        valid = pcm()
        cases = [valid[:cut] for cut in (0, 11, 23, 43, len(valid) - 1)]
        cases += [valid + b'extra', valid[:4] + struct.pack('<I', 0xFFFFFFFF) + valid[8:],
                  wav(chunk(b'fmt ', FMT), b'data' + struct.pack('<I', 100) + SAMPLES),
                  wav(chunk(b'fmt ', FMT), chunk(b'JUNK', b'odd')[:-1]),
                  pcm(samples=b''), pcm(samples=b'\0')]
        for body in cases:
            with self.subTest(size=len(body)):
                self.assert_invalid(body)

    def test_chunk_and_metadata_work_is_bounded(self):
        self.assert_invalid(pcm(metadata=chunk(b'JUNK', b'x' * MAX_METADATA_BYTES)))
        self.assert_invalid(pcm(metadata=chunk(b'JUNK', b'') * MAX_CHUNKS))

    def test_inspection_seeks_over_large_sample_data_and_reads_in_bounded_blocks(self):
        data_bytes = 8 * 1024 * 1024
        self.path.write_bytes(pcm(samples=b'\0\0')[:40] + struct.pack('<I', data_bytes))
        with self.path.open('r+b') as stream:
            stream.seek(4); stream.write(struct.pack('<I', data_bytes + 36))
            stream.truncate(44 + data_bytes)
        with open_pcm(self.path) as source:
            self.assertEqual(source.info.frames, data_bytes // 2)
            self.assertLessEqual(len(source.read(10**9)), BLOCK_BYTES)
            source.seek(source.size - 4)
            self.assertEqual(source.read(100), bytes(4))
            with self.assertRaises(ValueError): source.read(-1)

    def test_changed_or_truncated_handle_aborts_before_more_output(self):
        self.write(pcm())
        with open_pcm(self.path) as source:
            with self.path.open('r+b') as changed:
                changed.truncate(45)
            with self.assertRaises(ValueError): source.read(100)

    def test_path_replacement_does_not_switch_the_validated_handle(self):
        self.write(pcm())
        replacement = self.root / 'replacement.wav'
        replacement.write_bytes(b'FORM' + bytes(60))
        with open_pcm(self.path) as source:
            try:
                replacement.replace(self.path)
            except PermissionError:
                self.skipTest('OS disallows replacing this open handle')
            self.assertEqual(source.read(100), pcm())
        self.assertIsNone(audio_info(self.path))

    def test_copy_validation_preserves_source_and_existing_destination(self):
        self.write(b'FORM' + bytes(60))
        target = self.root / 'export.wav'; target.write_bytes(b'previous')
        with self.assertRaises(ValueError): copy_pcm(self.path, target)
        self.assertEqual(target.read_bytes(), b'previous')
        self.assertEqual(self.path.read_bytes(), b'FORM' + bytes(60))

    def test_cache_rejects_renamed_audio_and_retains_existing_section(self):
        cache = SectionCache(self.root / 'cache')
        key = 'a' * 64
        (cache.root / (key + '.wav')).write_bytes(b'FORM' + bytes(60))
        destination = self.root / 'section.wav'; destination.write_bytes(pcm())
        self.assertFalse(cache.fetch(key, destination))
        self.assertEqual(destination.read_bytes(), pcm())
        self.assertEqual(list(self.root.glob('.violilt-cache-*')), [])

    def test_cache_canonical_copy_retains_samples_and_source_metadata(self):
        original = pcm(metadata=chunk(b'LIST', b'abc'))
        self.write(original)
        cache = SectionCache(self.root / 'cache'); cache.put('b' * 64, self.path)
        destination = self.root / 'copied.wav'
        self.assertTrue(cache.fetch('b' * 64, destination))
        self.assertEqual(destination.read_bytes(), pcm())
        self.assertEqual(self.path.read_bytes(), original)

    def test_published_sections_stop_before_an_unsupported_container(self):
        (self.root / 'section-000000.wav').write_bytes(pcm())
        (self.root / 'section-000001.wav').write_bytes(b'FORM' + bytes(60))
        sections, available = published_sections({'chunks':[{'pause':0.25},{'pause':0}]}, self.root)
        self.assertEqual(len(sections), 1)
        self.assertEqual(available, 3 / 24000 + .25)


class PCMMediaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.store = Store(self.root / 'library')
        assets = self.root / 'assets'; assets.mkdir()
        self.server = AppServer(assets, self.store); self.server.start(); self.addCleanup(self.server.close)
        self.key = uuid.uuid4().hex
        self.folder = self.store.root / 'jobs' / self.key; self.folder.mkdir()
        self.store.put('jobs', {'id':self.key,'state':'completed','completed':1,'total':1})

    def test_invalid_completed_and_published_audio_is_not_delivered(self):
        for name, url in (('recording.wav', f'/media/{self.key}.wav'),
                          ('section-000000.wav',f'/media/{self.key}/section-000000.wav')):
            (self.folder / name).write_bytes(b'FORM' + bytes(60))
            for method in ('GET', 'HEAD'):
                with self.subTest(name=name,method=method), self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(urllib.request.Request(self.server.url+url,method=method))
                self.assertEqual(error.exception.code,404)

    def test_media_canonical_head_and_ranges_do_not_include_original_metadata(self):
        original = pcm(metadata=chunk(b'JUNK', b'never serve this metadata'))
        target = self.folder / 'recording.wav'; target.write_bytes(original)
        url=self.server.url+f'/media/{self.key}.wav'
        with urllib.request.urlopen(urllib.request.Request(url,method='HEAD')) as response:
            self.assertEqual(int(response.headers['Content-Length']),len(pcm()))
        for requested,expected in (('bytes=0-3',b'RIFF'),('bytes=42-47',pcm()[42:48]),('bytes=-4',pcm()[-4:])):
            with urllib.request.urlopen(urllib.request.Request(url,headers={'Range':requested})) as response:
                self.assertEqual(response.status,206); self.assertEqual(response.read(),expected)
        with urllib.request.urlopen(url) as response:
            self.assertEqual(response.read(),pcm())
        self.assertEqual(target.read_bytes(),original)


if __name__ == '__main__': unittest.main()

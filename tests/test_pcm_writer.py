"""Generated PCM16 contract; synthetic arrays only, never SoundFile/inference."""
import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

import numpy as np

from backend import pcm_audio


def source_pcm16(value):
    """Scalar reference for libsndfile 1.2.2's clipping-enabled f/d2les path.

    The ordinary nearest/even floating-point mode is assumed. This is source
    reasoning, not execution or attestation of the selected supplier DLL.
    """
    scaled = float(value) * 2147483648.0
    if scaled >= 2147483647.0:
        return 32767
    if scaled <= -2147483648.0:
        return -32768
    return round(scaled) >> 16


class PCMWriterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'section.part'

    def write_and_read(self, values):
        before = values.copy()
        pcm_audio.write_pcm16(self.path, values)
        np.testing.assert_array_equal(values, before)
        raw = self.path.read_bytes()
        with wave.open(str(self.path), 'rb') as reader:
            self.assertEqual(reader.getparams()[:4], (1, 2, 24000, len(values)))
            self.assertEqual(reader.getcomptype(), 'NONE')
            data = reader.readframes(len(values)+1)
        self.assertEqual(len(raw), 44 + len(values)*2)
        self.assertEqual(raw[:4], b'RIFF')
        self.assertEqual(struct.unpack_from('<I', raw, 4)[0], len(raw)-8)
        self.assertEqual(raw[8:16], b'WAVEfmt ')
        self.assertEqual(raw[36:40], b'data')
        self.assertEqual(struct.unpack_from('<I', raw, 40)[0], len(data))
        with pcm_audio.open_pcm(self.path) as reader:
            self.assertEqual(reader.read(len(raw)), raw[:pcm_audio.BLOCK_BYTES])
        return np.frombuffer(data, dtype='<i2').copy()

    def test_all_65536_pcm_codes_round_trip_from_both_float_dtypes(self):
        codes = np.arange(-32768, 32768, dtype=np.int32)
        for dtype in (np.float32, np.float64):
            with self.subTest(dtype=dtype):
                values = codes.astype(dtype)/32768
                np.testing.assert_array_equal(self.write_and_read(values), codes)

    def test_halfway_neighbors_clipping_and_source_scalar_reference(self):
        tiny_ties = [(n + .5)/2147483648.0 for n in (-131073, -65537, -65536, -1, 0, 1, 65535, 65536, 131071)]
        values = [-2, -1, -.1, -1/32768, -1e-10, -0.0, 0.0, 1e-10, .1, 1/32768, 1, 2] + tiny_ties
        for dtype in (np.float32, np.float64):
            base = np.asarray(values, dtype=dtype)
            data = np.concatenate([base, np.nextafter(base, dtype(-math.inf)), np.nextafter(base, dtype(math.inf))])
            expected = np.asarray([source_pcm16(v) for v in data], dtype=np.int16)
            np.testing.assert_array_equal(self.write_and_read(data), expected)
        # A generic round-at-16-bits rewrite would change existing PCM samples.
        self.assertEqual(source_pcm16(np.float64(.1)), 3276)
        self.assertEqual(round(.1*32768), 3277)

    def test_extreme_finite_floats_clip_without_numpy_overflow(self):
        for dtype in (np.float32, np.float64):
            values = np.array([-np.finfo(dtype).max, np.finfo(dtype).max], dtype=dtype)
            with np.errstate(all='raise'):
                np.testing.assert_array_equal(self.write_and_read(values), [-32768, 32767])

    def test_int16_is_unscaled_and_int32_uses_arithmetic_high_bits(self):
        small = np.array([-32768, -32767, -1, 0, 1, 32767], dtype=np.int16)
        np.testing.assert_array_equal(self.write_and_read(small), small)
        large = np.array([-2147483648, -65537, -65536, -1, 0, 65535, 65536, 2147483647], dtype=np.int32)
        np.testing.assert_array_equal(self.write_and_read(large), [-32768, -2, -1, -1, 0, 0, 1, 32767])

    def test_mono_column_strides_and_explicit_little_endian(self):
        source = np.array([[-32768, 9], [-1, 8], [0, 7], [32767, 6]], dtype='>i2')
        mono = source[:, :1]
        self.assertFalse(mono.flags.c_contiguous)
        actual = self.write_and_read(mono)
        np.testing.assert_array_equal(actual, [-32768, -1, 0, 32767])

    def test_bad_dtype_shape_rate_or_empty_never_opens_destination(self):
        bad = [np.array([], dtype=np.float32), np.array(1.0), np.zeros((3, 2)), np.zeros((2, 1, 1)),
               np.array([True]), np.array([1], dtype=np.int64), np.array([1], dtype=np.uint16),
               np.array([.1], dtype=np.float16), np.array([1j]), np.array([object()])]
        for values in bad:
            self.path.write_bytes(b'previous staging bytes')
            with self.subTest(dtype=values.dtype, shape=values.shape), patch('wave.open') as opened:
                with self.assertRaises(ValueError):
                    pcm_audio.write_pcm16(self.path, values)
                opened.assert_not_called()
            self.assertEqual(self.path.read_bytes(), b'previous staging bytes')
        for rate in (0, 48000, True, '24000'):
            with self.subTest(rate=rate), patch('wave.open') as opened:
                with self.assertRaises(ValueError):
                    pcm_audio.write_pcm16(self.path, np.ones(1), rate)
                opened.assert_not_called()

    def test_late_nan_or_infinity_is_rejected_before_destination_open(self):
        for invalid in (math.nan, math.inf, -math.inf):
            values = np.zeros(pcm_audio.BLOCK_BYTES//2 + 3, dtype=np.float64)
            values[-1] = invalid
            self.path.write_bytes(b'previous')
            with self.subTest(invalid=invalid), patch('wave.open') as opened:
                with self.assertRaises(ValueError):
                    pcm_audio.write_pcm16(self.path, values)
                opened.assert_not_called()
            self.assertEqual(self.path.read_bytes(), b'previous')

    def test_oversize_zero_stride_view_rejects_before_scan_or_open(self):
        # Huge logical size, one backing scalar: no multi-gigabyte allocation.
        values = np.broadcast_to(np.array(0, dtype=np.float32), (pcm_audio.MAX_AUDIO_BYTES//2 + 1,))
        self.path.write_bytes(b'previous')
        with patch('numpy.isfinite') as scanned, patch('wave.open') as opened:
            with self.assertRaises(ValueError):
                pcm_audio.write_pcm16(self.path, values)
            scanned.assert_not_called()
            opened.assert_not_called()
        self.assertEqual(self.path.read_bytes(), b'previous')

    def test_finite_masks_and_written_payloads_are_bounded(self):
        masks, writes = [], []
        original_finite, original_write = np.isfinite, wave.Wave_write.writeframesraw
        def finite(values):
            masks.append(len(values))
            return original_finite(values)
        def write(output, data):
            writes.append(len(data))
            return original_write(output, data)
        values = np.full(2*(pcm_audio.BLOCK_BYTES//2)+7, .1, dtype=np.float64)
        with patch('numpy.isfinite', side_effect=finite), patch('wave.Wave_write.writeframesraw', write):
            pcm_audio.write_pcm16(self.path, values)
        self.assertEqual(masks, [65536, 65536, 7])
        self.assertEqual(writes, [131072, 131072, 14])
        with wave.open(str(self.path), 'rb') as reader:
            self.assertEqual(reader.getnframes(), len(values))

    def test_partial_staging_io_failure_never_changes_published_file(self):
        published = self.path.with_suffix('.wav')
        published.write_bytes(b'previous published bytes')
        original = wave.Wave_write.writeframesraw
        calls = []
        def fail(output, data):
            calls.append(len(data))
            if len(calls) == 2:
                raise OSError('synthetic staging full')
            return original(output, data)
        with patch('wave.Wave_write.writeframesraw', fail), self.assertRaises(OSError):
            pcm_audio.write_pcm16(self.path, np.zeros(70000, dtype=np.float32))
        self.assertEqual(published.read_bytes(), b'previous published bytes')
        self.assertEqual(len(calls), 2)


if __name__ == '__main__':
    unittest.main()

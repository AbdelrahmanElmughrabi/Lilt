"""Guard the dormant-import hole found in the first candidate executable."""
import unittest

from tools.package_pronunciation_audit import REMOVED_AUDIO, removed_imports


class PackageAuditTests(unittest.TestCase):
    def test_dormant_nested_baseline_import_is_detected_without_execution(self):
        source = "def compare():\n    def baseline():\n        from kokoro_onnx import Kokoro\n"
        self.assertEqual(removed_imports(compile(source, '<dormant comparison>', 'exec')), {'kokoro_onnx'})

    def test_optional_espeak_import_form_is_detected(self):
        self.assertEqual(removed_imports(compile('from misaki import espeak', '<fallback>', 'exec')), {'misaki.espeak'})

    def test_required_attribution_and_current_engine_import_remain_allowed(self):
        source = '\"\"\"Derived from MIT Kokoro-ONNX; eSpeak stage removed.\"\"\"\nfrom backend.kokoro_engine import Kokoro\n'
        self.assertEqual(removed_imports(compile(source, '<current engine>', 'exec')), set())


    def test_dormant_native_audio_imports_are_rejected(self):
        code = compile('def dormant():\n    import soundfile\n    from _soundfile_data import x\n', '<removed audio>', 'exec')
        self.assertEqual(removed_imports(code, REMOVED_AUDIO), {'soundfile', '_soundfile_data'})

"""Startup gates must prevent OCR from starting with an unavailable model."""

import io
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import ensure_lmstudio as startup


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(startup.os.environ, {
            "LMSTUDIO_BASE_URL": "http://127.0.0.1:1234",
            "LMSTUDIO_MODEL": "glm-ocr",
            "LMSTUDIO_MODEL_KEY": "glm-ocr",
            "LMSTUDIO_LOAD_TIMEOUT": "180",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.find = patch.object(startup, "find_lms", return_value="lms.exe")
        self.find.start()
        self.addCleanup(self.find.stop)

    def ready_opener(self):
        opener = MagicMock()
        opener.open.side_effect = lambda *a, **kw: io.BytesIO(
            b'{"data": [{"id": "glm-ocr"}]}'
        )
        return opener

    def test_loaded_model_is_reused(self):
        with patch.object(startup, "run_lms", side_effect=[
            {"status": "running"}, [{"identifier": "glm-ocr"}],
        ]) as command, patch.object(startup, "build_opener", return_value=self.ready_opener()):
            startup.ensure_backend()
        self.assertEqual(command.call_count, 2)

    def test_stopped_runtime_loads_model_and_starts_server(self):
        opener = self.ready_opener()
        opener.open.side_effect = [
            OSError("not listening"), io.BytesIO(b'{"data": [{"id": "glm-ocr"}]}'),
        ]
        with patch.object(startup, "run_lms", side_effect=[
            {"status": "stopped"}, None, [], [{"modelKey": "glm-ocr"}],
            None, [{"identifier": "glm-ocr"}], None,
        ]) as command, patch.object(startup, "build_opener", return_value=opener):
            startup.ensure_backend()
        command.assert_any_call("lms.exe", "daemon", "up", timeout=60)
        command.assert_any_call(
            "lms.exe", "load", "glm-ocr", "--identifier", "glm-ocr", "-y", timeout=180,
        )
        command.assert_any_call("lms.exe", "server", "start", "--port", "1234")

    def test_missing_model_fails_without_download(self):
        with patch.object(startup, "run_lms", side_effect=[
            {"status": "running"}, [], [],
        ]) as command:
            with self.assertRaisesRegex(RuntimeError, "not downloaded"):
                startup.ensure_backend()
        self.assertEqual(command.call_count, 3)

    def test_load_success_without_model_in_memory_is_failure(self):
        with patch.object(startup, "run_lms", side_effect=[
            {"status": "running"}, [], [{"modelKey": "glm-ocr"}], None, [],
        ]):
            with self.assertRaisesRegex(RuntimeError, "still not loaded"):
                startup.ensure_backend()

    def test_api_failure_has_bounded_wait(self):
        opener = MagicMock()
        opener.open.side_effect = OSError("not listening")
        with patch.object(startup, "run_lms", side_effect=[
            {"status": "running"}, [{"identifier": "glm-ocr"}], None,
        ]), patch.object(startup, "build_opener", return_value=opener), \
                patch.object(startup.time, "monotonic", side_effect=[0, 16]):
            with self.assertRaisesRegex(RuntimeError, "did not expose"):
                startup.ensure_backend()

    def test_cli_timeout_is_reported_as_startup_failure(self):
        with patch.object(startup.subprocess, "run", side_effect=subprocess.TimeoutExpired("lms", 1)):
            with self.assertRaisesRegex(RuntimeError, "timed out after 1s"):
                startup.run_lms("lms.exe", "ps", timeout=1)

    def test_portable_entry_uses_service_settings(self):
        settings = SimpleNamespace(
            lmstudio_api_url="http://127.0.0.1:2345/v1/chat/completions",
            lmstudio_model="custom-ocr", vlm_api_mode="openai",
        )
        with patch("config.settings", settings), patch.dict(startup.os.environ, {}, clear=True), \
                patch.object(startup, "ensure_backend") as ensure:
            self.assertEqual(startup.main(), 0)
            self.assertEqual(startup.os.environ["LMSTUDIO_MODEL"], "custom-ocr")
            self.assertEqual(startup.os.environ["LMSTUDIO_BASE_URL"], "http://127.0.0.1:2345")
            ensure.assert_called_once()

    def test_remote_configuration_does_not_start_local_backend(self):
        settings = SimpleNamespace(
            lmstudio_api_url="http://192.168.1.10:1234/v1/chat/completions",
            lmstudio_model="glm-ocr", vlm_api_mode="openai",
        )
        with patch("config.settings", settings), patch.object(startup, "ensure_backend") as ensure:
            self.assertEqual(startup.main(), 0)
            ensure.assert_not_called()


if __name__ == "__main__":
    unittest.main()

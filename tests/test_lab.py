"""Testes offline; não substituem as validações reais da Sprint 1."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("lab", Path(__file__).resolve().parents[1] / "scripts/lab.py")
lab = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lab)

CONFIG = {"services": {
    "juice-shop": {"ports": [{"host_ip": "127.0.0.1", "published": "3000"}]},
    "ollama": {"ports": [{"host_ip": "127.0.0.1", "published": "11434"}],
               "environment": {"LAB_MODEL": "qwen3:1.7b"}}
}}


class LabTests(unittest.TestCase):
    def setUp(self):
        lab.RECORD = {"steps": []}

    def test_accepts_loopback_lan_and_private_vpn(self):
        for url in ("http://127.0.0.1:3000/", "http://192.168.1.50:3000",
                    "http://100.101.2.3:3000", "http://[::1]:3000"):
            with self.subTest(url=url):
                self.assertEqual(lab.validate_target(url), url.rstrip("/"))

    def test_rejects_external_or_ambiguous_targets(self):
        for url in ("http://8.8.8.8:3000", "http://example.org:3000",
                    "http://127.0.0.1", "http://user:pass@127.0.0.1:3000",
                    "http://127.0.0.1:3000/path", "http://127.0.0.1:3000?url=x",
                    "http://127.0.0.1:3000#x", "http://0.0.0.0:3000",
                    "http://169.254.169.254:3000", "http://[ff02::1]:3000"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                lab.validate_target(url)

    def test_redirect_is_never_followed(self):
        with self.assertRaisesRegex(RuntimeError, "Redirecionamento"):
            lab.NoRedirect().redirect_request(None, None, 302, "Found", {}, "http://example.org")

    def test_incomplete_generation_is_not_a_success(self):
        for reply in ({"done": True, "response": ""}, {"done": False, "response": "texto"}):
            with self.subTest(reply=reply), patch.object(lab, "http", side_effect=["html", {}, {}, reply]):
                with self.assertRaisesRegex(RuntimeError, "resposta completa"):
                    lab.check(CONFIG)

    def test_reset_requires_explicit_confirmation_before_docker_access(self):
        with patch("sys.argv", ["lab.py", "reset"]), patch.object(lab, "configuration") as config:
            with self.assertRaises(SystemExit) as error:
                lab.main()
            self.assertEqual(error.exception.code, 2)
            config.assert_not_called()

    def reset_with_baseline(self, baseline):
        with patch.object(lab, "compose", side_effect=["old", "", "", "new", ""]) as compose:
            with patch.object(lab, "run", side_effect=["sha256:same", "sha256:same"]):
                with patch.object(lab, "http", side_effect=["html", baseline]):
                    lab.reset(CONFIG)
        recreate = compose.call_args_list[2].args
        self.assertIn("--no-deps", recreate)
        self.assertIn("--force-recreate", recreate)
        self.assertEqual(recreate[-1], "juice-shop")

    def test_reset_accepts_verified_fresh_state(self):
        self.reset_with_baseline({"data": [{"solved": False}]})
        self.assertEqual(lab.RECORD["restoration"]["solved_challenges"], 0)

    def test_reset_rejects_solved_or_missing_baseline(self):
        for baseline in ({"data": [{"solved": True}]}, {"data": []}, {"data": [{}]}):
            with self.subTest(baseline=baseline), self.assertRaises(RuntimeError):
                self.reset_with_baseline(baseline)

    def test_reset_rejects_image_change(self):
        with patch.object(lab, "compose", side_effect=["old", "", "", "new"]):
            with patch.object(lab, "run", side_effect=["sha256:one", "sha256:two"]):
                with self.assertRaisesRegex(RuntimeError, "mesma imagem"):
                    lab.reset(CONFIG)

    def test_failed_diagnostic_is_saved_as_failure(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(lab, "ROOT", Path(directory)):
            with patch("sys.argv", ["lab.py", "check"]):
                with patch.object(lab, "configuration", side_effect=RuntimeError("Docker indisponível")):
                    self.assertEqual(lab.main(), 1)
            records = list((Path(directory) / "evidencias/sprint-1").glob("*.json"))
            self.assertEqual(len(records), 1)
            record = json.loads(records[0].read_text())
            self.assertFalse(record["success"])
            self.assertIn("Docker indisponível", record["error"])


if __name__ == "__main__":
    unittest.main()

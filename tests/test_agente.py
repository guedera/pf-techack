"""Testes offline do agente supervisionado; não substituem a validação no laboratório.
Cobrem as verificações da Sprint 3: rejeição não executa, ação modificada executa só os
parâmetros finais, destino fora do escopo é bloqueado antes de qualquer contato, resposta
inválida do modelo não executa nada, redirecionamento não é seguido e a saída completa é
preservada no registro mesmo quando a prévia ao modelo é reduzida."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "agente", Path(__file__).resolve().parents[1] / "scripts/agente.py")
agente = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agente)


class ScopeTests(unittest.TestCase):
    def test_build_url_accepts_only_authorized_host(self):
        url = agente._build_http_url("/rest/products/search?q=apple")
        self.assertTrue(url.startswith(agente.TARGET))

    def test_build_url_rejects_scheme_relative_and_absolute(self):
        for path in ("//example.org/", "http://example.org", "rest/x", ""):
            with self.subTest(path=path), self.assertRaises(ValueError):
                agente._build_http_url(path)

    def test_http_method_is_restricted(self):
        for bad in ("TRACE", "CONNECT", "FETCH"):
            with self.subTest(method=bad), self.assertRaises(ValueError):
                agente.tool_http_request({"method": bad, "path": "/"})

    def test_allowed_methods_build_without_network_rejection(self):
        # métodos válidos passam da validação (falham só na rede, não na checagem)
        self.assertEqual(agente.ALLOWED_METHODS, ("GET", "POST", "PUT", "DELETE", "PATCH"))

    def test_headers_validation(self):
        self.assertEqual(agente._clean_headers(None), {})
        self.assertEqual(agente._clean_headers({"Authorization": "Bearer x"}),
                         {"Authorization": "Bearer x"})
        for bad in ({"X": "a\r\nSet-Cookie: y"}, {"X": "v" * 9000}, [1, 2], {"a": {}}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                agente._clean_headers(bad)

    def test_port_spec_is_validated_and_bounded(self):
        self.assertEqual(agente._parse_ports("80,443"), [80, 443])
        self.assertEqual(agente._parse_ports("3000-3002"), [3000, 3001, 3002])
        for bad in ("; rm -rf", "1-99999", "1-200", "abc"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                agente._parse_ports(bad)


class ModelParsingTests(unittest.TestCase):
    def test_extracts_json_ignoring_think_and_prose(self):
        raw = '<think>hmm</think> aqui: {"tool":"http_request","params":{"path":"/"}} fim'
        self.assertEqual(agente.extract_json(raw)["tool"], "http_request")

    def test_returns_none_for_no_json(self):
        self.assertIsNone(agente.extract_json("sem json aqui"))


class SuperviseTests(unittest.TestCase):
    def test_reject_returns_reason_and_no_execution_flag(self):
        with patch.object(agente, "ask", side_effect=["r", "fora do escopo"]):
            decision, params, why = agente.supervise(
                {"tool": "http_request", "params": {"path": "/"}, "rationale": "x"})
        self.assertEqual(decision, "rejeitado")
        self.assertEqual(why, "fora do escopo")

    def test_modify_requires_reapproval_and_keeps_final_params(self):
        # modifica uma vez, depois autoriza
        with patch.object(agente, "ask",
                          side_effect=["m", '{"method":"GET","path":"/rest/user/whoami"}', "a", "Verificar identidade"]):
            decision, params, _ = agente.supervise(
                {"tool": "http_request", "params": {"path": "/"}, "rationale": "x"})
        self.assertEqual(decision, "autorizado")
        self.assertEqual(params, {"method": "GET", "path": "/rest/user/whoami"})


class LogTests(unittest.TestCase):
    def test_full_output_preserved_in_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(agente, "ROOT", Path(tmp)):
                log = agente.Log("99")
                big = "A" * (agente.MODEL_PREVIEW + 5000)
                log.event(1, "execucao", result={"body": big})
                lines = log.path.read_text(encoding="utf-8").strip().splitlines()
                rec = json.loads(lines[-1])
        self.assertEqual(len(rec["result"]["body"]), agente.MODEL_PREVIEW + 5000)


class RedirectTests(unittest.TestCase):
    def test_redirect_handler_does_not_follow(self):
        # redirect_request devolve None => urllib não segue o 3xx
        self.assertIsNone(
            agente.NoRedirect().redirect_request(None, None, 302, "Found", {}, "http://example.org"))


class RegressionTests(unittest.TestCase):
    def test_session_references_resolve_only_from_captured_values(self):
        source = {"method": "GET", "path": "/rest/basket/$last_basket_id",
                  "headers": {"Authorization": "Bearer $last_token"}}
        resolved, refs = agente.resolve_session_references(
            source, {"token": "token-real", "basket_id": "42"})
        self.assertEqual(resolved["path"], "/rest/basket/42")
        self.assertEqual(resolved["headers"]["Authorization"], "Bearer token-real")
        self.assertEqual(refs, ["$last_token", "$last_basket_id"])
        self.assertEqual(source["path"], "/rest/basket/$last_basket_id")
        with self.assertRaises(ValueError):
            agente.resolve_session_references(source, {})

    def test_login_session_metadata_is_extracted_without_other_fields(self):
        result = {"status": 200, "body": json.dumps({"authentication": {
            "token": "token-real", "bid": 42, "umail": "test@lab.local"}})}
        self.assertEqual(agente.capture_session_values(result),
                         {"token": "token-real", "basket_id": "42"})

    def test_scan_blocks_other_ports_before_socket(self):
        with patch.object(agente.socket, "socket") as sock:
            with self.assertRaises(ValueError):
                agente.tool_tcp_scan({"ports": "80,443"})
            sock.assert_not_called()

    def test_headers_block_placeholder_and_host(self):
        for headers in ({"Host": "other"}, {"Authorization": "Bearer <token>"}):
            with self.assertRaises(ValueError):
                agente._clean_headers(headers)

    def test_proposal_validation_is_side_effect_free(self):
        with patch.object(agente.urllib.request, "build_opener") as opener:
            agente.validate_tool_params("http_request", {"method": "GET", "path": "/"})
            opener.assert_not_called()
        with self.assertRaises(ValueError):
            agente.validate_tool_params("http_request", {
                "method": "GET", "path": "/rest/user/whoami",
                "headers": {"Authorization": "Bearer <token>"}})

    def test_json_with_braces_inside_string(self):
        self.assertEqual(agente.extract_json('{"interpretation":"literal } na resposta"}')['interpretation'], "literal } na resposta")

    def test_history_includes_response_and_human_correction(self):
        result = agente.compact_history([dict(step=1, tool="http_request", params={},
            decision="autorizado", evidence='{"status":200,"body":"HTML"}',
            human_evaluation="HTML não demonstra acesso a dados")])
        self.assertIn('"body":"HTML"', result)
        self.assertIn("HTML não demonstra acesso", result)

    def test_sessions_are_separate(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(agente, "ROOT", Path(tmp)):
            a, b = agente.Log("01"), agente.Log("01")
            self.assertNotEqual(a.path, b.path)
            a.event(0, "objetivo")
            self.assertEqual(json.loads(a.path.read_text())["session_id"], a.session_id)

    def test_placeholder_never_calls_model(self):
        with patch.object(agente, "model_generate") as model:
            with self.assertRaises(ValueError):
                agente.run("<objetivo da investigação 1>", "01", 3)
            model.assert_not_called()

    def test_empty_supervision_reason_reprompts(self):
        with patch.object(agente, "ask", side_effect=["a", "", "Verificar endpoint"]):
            decision, _, reason = agente.supervise({"tool":"http_request","params":{}})
            self.assertEqual((decision, reason), ("autorizado", "Verificar endpoint"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

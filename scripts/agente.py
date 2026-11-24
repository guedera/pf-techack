#!/usr/bin/env python3
"""Agente supervisionado — Sprint 3 da Avaliação Final de Tecnologias Hackers.

Ciclo (enunciado, seção 2):
  objetivo -> o modelo local propõe UMA ação (JSON) -> a dupla autoriza, modifica
  ou rejeita -> a ferramenta roda apenas se autorizada -> o resultado volta ao
  modelo -> o modelo interpreta -> propõe a próxima ação, considerando o histórico.

Decisões de projeto:
  - Só biblioteca padrão, como o scripts/lab.py (Python 3.9+; sem dependências).
  - O alvo é TRAVADO no Juice Shop autorizado lido do .env; nenhuma ferramenta
    aceita outro host. Redirecionamentos HTTP não são seguidos.
  - Duas ferramentas delimitadas, com validação de parâmetros e sem acesso livre
    ao terminal: `http_request` (interage direto com o Juice Shop) e `tcp_scan`
    (reconhecimento de portas no host do alvo).
  - Toda proposta, decisão humana, execução, erro e interpretação é gravada em
    JSONL (um evento por linha), preservando a saída completa das ferramentas
    mesmo quando ao modelo é enviada apenas uma prévia.

NÃO é um agente autônomo: nada executa sem autorização humana explícita.
"""
import argparse
import datetime as dt
import ipaddress
import json
import math
import re
import socket
import subprocess
import sys
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit, urlencode

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 200_000       # teto do que a ferramenta lê/guarda
MODEL_PREVIEW = 1500      # quanto do resultado vai ao modelo (o log guarda tudo)
HISTORY_STEPS = 6         # quantos passos anteriores resumir para o modelo


# --------------------------------------------------------------------------- #
# Configuração e escopo
# --------------------------------------------------------------------------- #
def load_env():
    env = {}
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def validate_target(url):
    """Mesma política do lab.py: só loopback/LAN/VPN privada, sem caminho/credenciais."""
    parsed = urlsplit(url)
    if (parsed.scheme != "http" or parsed.username or parsed.password
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("Use http://IP_PRIVADO:PORTA, sem caminho ou credenciais.")
    address = ipaddress.ip_address(parsed.hostname or "")
    private = any(address in block for block in (
        ipaddress.ip_network("10.0.0.0/8"), ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"), ipaddress.ip_network("100.64.0.0/10"),
        ipaddress.ip_network("fc00::/7")))
    if not (address.is_loopback or private) or not parsed.port:
        raise ValueError("Informe IP de loopback, LAN privada ou VPN privada e porta explícita.")
    return url.rstrip("/")


ENV = load_env()
TARGET = validate_target("http://{}:{}".format(
    ENV.get("LAB_BIND_IP", "127.0.0.1"), ENV.get("JUICE_SHOP_PORT", "3000")))
_t = urlsplit(TARGET)
TARGET_HOST, TARGET_PORT = _t.hostname, _t.port
OLLAMA_URL = "http://127.0.0.1:{}".format(ENV.get("OLLAMA_PORT", "11434"))
MODEL = ENV.get("OLLAMA_MODEL", "qwen3:1.7b")


# --------------------------------------------------------------------------- #
# Ferramentas delimitadas (toda validação acontece antes de qualquer contato)
# --------------------------------------------------------------------------- #
class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Não segue redirecionamentos; o 3xx volta como resposta para ser analisado."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _build_http_url(path):
    if not isinstance(path, str) or not path.startswith("/") or path.startswith("//"):
        raise ValueError("path deve ser uma string começando com '/' e não com '//'.")
    url = TARGET + path
    p = urlsplit(url)
    if p.scheme != "http" or p.hostname != TARGET_HOST or p.port != TARGET_PORT:
        raise ValueError("Fora do escopo: a ação só pode atingir " + TARGET)
    return url


ALLOWED_METHODS = ("GET", "POST", "PUT", "DELETE", "PATCH")


def _clean_headers(raw):
    """Valida os cabeçalhos propostos (evita injeção de CR/LF e abuso de tamanho)."""
    if raw in (None, ""):
        return {}
    if not isinstance(raw, dict):
        raise ValueError("headers deve ser um objeto {nome: valor}.")
    if len(raw) > 20:
        raise ValueError("máximo de 20 cabeçalhos por ação.")
    clean = {}
    for k, v in raw.items():
        if not isinstance(k, str) or not isinstance(v, (str, int, float)):
            raise ValueError("nome e valor de cabeçalho devem ser texto.")
        v = str(v)
        if k.lower() in ("host", "content-length", "transfer-encoding", "connection", "proxy-authorization"):
            raise ValueError("Cabeçalho controlado pelo transporte: " + k)
        if "<token>" in v.lower():
            raise ValueError("Substitua <token> pelo token real da conta de teste.")
        if len(k) > 128 or len(v) > 8192 or re.search(r"[\r\n]", k + v):
            raise ValueError("cabeçalho inválido (tamanho ou quebra de linha).")
        clean[k] = v
    return clean


def validate_tool_params(tool, params):
    """Valida uma proposta sem executar rede ou abrir sockets."""
    if tool not in TOOLS:
        raise ValueError("Ferramenta desconhecida: " + str(tool))
    if not isinstance(params, dict):
        raise ValueError("params deve ser um objeto JSON.")
    if tool == "http_request":
        method = str(params.get("method", "GET")).upper()
        if method not in ALLOWED_METHODS:
            raise ValueError("method deve ser um de: " + ", ".join(ALLOWED_METHODS) + ".")
        _build_http_url(params.get("path", "/"))
        timeout = float(params.get("timeout", 15))
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout deve ser positivo e finito.")
        headers = _clean_headers(params.get("headers"))
        if params.get("body") is not None and method != "GET":
            body = params["body"]
            content_type = params.get("content_type", "application/json")
            if not isinstance(content_type, str) or not content_type.strip():
                raise ValueError("content_type deve ser texto não vazio.")
            if isinstance(body, dict) and content_type == "application/x-www-form-urlencoded":
                urlencode(body).encode()
            elif not isinstance(body, str):
                json.dumps(body).encode()
            headers.setdefault("Content-Type", content_type)
            _clean_headers(headers)
        return
    ports = _parse_ports(params.get("ports", str(TARGET_PORT)))
    if ports != [TARGET_PORT]:
        raise ValueError("Fora do escopo: somente a porta {} do Juice Shop é autorizada.".format(TARGET_PORT))
    timeout = float(params.get("timeout", 1.0))
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout deve ser positivo e finito.")


def capture_session_values(result):
    """Extrai referências efêmeras de uma resposta de login sem expor o token ao modelo."""
    if not isinstance(result, dict) or result.get("status") != 200:
        return {}
    try:
        authentication = json.loads(result.get("body", "")).get("authentication", {})
    except (TypeError, ValueError):
        return {}
    token, basket_id = authentication.get("token"), authentication.get("bid")
    captured = {}
    if isinstance(token, str) and token.strip():
        captured["token"] = token
    if isinstance(basket_id, int) or (isinstance(basket_id, str) and basket_id.isdigit()):
        captured["basket_id"] = str(basket_id)
    return captured


def resolve_session_references(params, session):
    """Resolve referências aprovadas pela dupla só no instante da execução.

    O modelo vê apenas ``$last_token`` e ``$last_basket_id``. A referência só vale
    nesta sessão, exige valor capturado em resposta anterior e não é escrita no log.
    """
    resolved = json.loads(json.dumps(params))
    refs = []
    headers = resolved.get("headers")
    if isinstance(headers, dict) and headers.get("Authorization") == "Bearer $last_token":
        token = session.get("token")
        if not token:
            raise ValueError("Nenhum token real foi capturado nesta sessão.")
        headers["Authorization"] = "Bearer " + token
        refs.append("$last_token")
    path = resolved.get("path")
    if isinstance(path, str) and "$last_basket_id" in path:
        basket_id = session.get("basket_id")
        if not basket_id:
            raise ValueError("Nenhum ID de carrinho foi capturado nesta sessão.")
        resolved["path"] = path.replace("$last_basket_id", basket_id)
        refs.append("$last_basket_id")
    raw = json.dumps(resolved)
    if "$last_token" in raw or "$last_basket_id" in raw:
        raise ValueError("Referência de sessão inválida ou não suportada.")
    return resolved, refs


def tool_http_request(params):
    method = str(params.get("method", "GET")).upper()
    if method not in ALLOWED_METHODS:
        raise ValueError("method deve ser um de: " + ", ".join(ALLOWED_METHODS) + ".")
    url = _build_http_url(params.get("path", "/"))
    timeout = min(float(params.get("timeout", 15)), 30)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout deve ser positivo e finito.")
    headers = _clean_headers(params.get("headers"))
    data = None
    if params.get("body") is not None and method != "GET":
        body = params["body"]
        content_type = params.get("content_type", "application/json")
        if isinstance(body, dict) and content_type == "application/x-www-form-urlencoded":
            data = urlencode(body).encode()
        else:
            data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        headers.setdefault("Content-Type", content_type)
        headers = _clean_headers(headers)
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    start = time.monotonic()
    try:
        resp = opener.open(req, timeout=timeout)
        status, raw, hdrs = resp.status, resp.read(MAX_BYTES + 1), dict(resp.headers)
    except urllib.error.HTTPError as e:            # 4xx/5xx são respostas válidas para análise
        status, raw, hdrs = e.code, e.read(MAX_BYTES + 1), dict(e.headers)
    truncated = len(raw) > MAX_BYTES
    raw = raw[:MAX_BYTES]
    resp_headers = {k: str(v)[:1024] for k, v in list(hdrs.items())[:40]}  # Set-Cookie etc.
    return {
        "url": url, "method": method, "status": status,
        "seconds": round(time.monotonic() - start, 3), "bytes": len(raw),
        "truncated": truncated, "location": hdrs.get("Location"),
        "content_type": hdrs.get("Content-Type"),
        "request_headers": sorted(headers.keys()), "response_headers": resp_headers,
        "body": raw.decode("utf-8", "replace"),
    }


def _parse_ports(spec):
    spec = str(spec)
    if not re.fullmatch(r"[0-9,\-]{1,64}", spec):
        raise ValueError("ports: use dígitos, vírgula e hífen (ex.: '3000', '1-1024', '80,443').")
    ports = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            if not 1 <= int(a) <= int(b) <= 65535 or int(b) - int(a) >= 100:
                raise ValueError("Intervalo de portas inválido ou excessivo.")
            ports.extend(range(int(a), int(b) + 1))
        elif part:
            if not 1 <= int(part) <= 65535:
                raise ValueError("Porta fora do intervalo válido.")
            ports.append(int(part))
    ports = sorted({p for p in ports if 1 <= p <= 65535})
    if not ports:
        raise ValueError("ports: nenhuma porta válida.")
    if len(ports) > 100:
        raise ValueError("ports: máximo de 100 portas por ação (limite do laboratório).")
    return ports


def tool_tcp_scan(params):
    """Reconhecimento: TCP connect só no HOST autorizado (nunca em outro IP)."""
    ports = _parse_ports(params.get("ports", str(TARGET_PORT)))
    if ports != [TARGET_PORT]:
        raise ValueError("Fora do escopo: somente a porta {} do Juice Shop é autorizada.".format(TARGET_PORT))
    timeout = min(float(params.get("timeout", 1.0)), 3.0)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout deve ser positivo e finito.")
    results, start = [], time.monotonic()
    for port in ports:
        family = socket.AF_INET6 if ":" in TARGET_HOST else socket.AF_INET
        s = socket.socket(family, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((TARGET_HOST, port))
            state = "open"
        except ConnectionRefusedError:
            state = "closed"
        except (socket.timeout, OSError):
            state = "filtered"
        finally:
            s.close()
        results.append({"port": port, "state": state})
    return {"host": TARGET_HOST, "scanned": len(ports),
            "seconds": round(time.monotonic() - start, 3),
            "open": [r["port"] for r in results if r["state"] == "open"],
            "results": results}


TOOLS = {
    "http_request": {
        "run": tool_http_request,
        "help": ('UMA requisição HTTP ao Juice Shop (interage direto com o alvo). '
                 'Métodos: GET, POST, PUT, DELETE, PATCH. '
                 'params: {"method":"GET","path":"/rest/...","headers":{},'
                 '"body":<opcional>,"content_type":<opcional>}. Só inclua Authorization quando '
                 'o humano fornecer um token real; nunca use valores placeholder.'),
    },
    "tcp_scan": {
        "run": tool_tcp_scan,
        "help": ('Varredura TCP connect de portas NO host do alvo (reconhecimento). '
                 'params: {"ports":"' + str(TARGET_PORT) + '"}; somente a porta do Juice Shop é autorizada.'),
    },
}


# --------------------------------------------------------------------------- #
# Modelo local (Ollama)
# --------------------------------------------------------------------------- #
def model_generate(system, prompt, num_predict=520, timeout=300):
    payload = {
        "model": MODEL, "system": system, "prompt": prompt, "stream": False,
        "think": False, "keep_alive": "5m",
        "options": {"num_ctx": 2048, "num_predict": num_predict, "temperature": 0},
    }
    req = urllib.request.Request(OLLAMA_URL + "/api/generate",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as resp:
        reply = json.loads(resp.read())
    if reply.get("done") is not True or not reply.get("response", "").strip():
        raise RuntimeError("Resposta do modelo incompleta ou vazia.")
    return reply["response"]


def extract_json(text):
    """Extrai o primeiro objeto JSON balanceado da resposta do modelo."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
            return value
        except json.JSONDecodeError:
            continue
    return None


def tool_catalog():
    return "\n".join("- {}: {}".format(n, t["help"]) for n, t in TOOLS.items())


def compact_history(history):
    if not history:
        return "(sem ações anteriores)"
    lines = []
    for h in history[-HISTORY_STEPS:]:
        obs = (h.get("interpretation") or h.get("status") or "")[:200]
        lines.append("[{}] {} {} | decisão={} | {}".format(
            h["step"], h["tool"], json.dumps(h["params"], ensure_ascii=False),
            h["decision"], obs))
        lines.append("Evidência: " + h.get("evidence", "não executada"))
        lines.append("Avaliação humana: " + h.get("human_evaluation", ""))
        session = h.get("session", {})
        if session:
            lines.append("Referências de sessão disponíveis: token={}, carrinho={}".format(
                "sim" if session.get("token") else "não",
                session.get("basket_id", "não")))
    return "\n".join(lines)


PROPOSAL_SYSTEM = (
    "Você é um assistente de testes de segurança SUPERVISIONADO. O único alvo "
    "autorizado é {target} e nenhum outro host. A cada passo proponha UMA ação com "
    "uma das ferramentas. Responda SOMENTE com um objeto JSON, sem texto fora dele:\n"
    '{{"rationale":"por que esta ação ajuda a investigar","tool":"<nome>","params":{{...}}}}\n'
    "Ferramentas disponíveis:\n{tools}\n"
    "Reaproveite evidências dos passos anteriores (por exemplo, um token Bearer ou um id "
    "obtido numa resposta) nos headers ou no path da próxima ação. "
    "Você NÃO executa nada; a dupla decide. Baseie a próxima ação nos resultados anteriores. "
    "Mantenha os parâmetros mínimos e completos: não invente tokens, não use placeholders "
    "e não replique listas inteiras de dados quando um único item já observado basta. "
    "Se o histórico não contém um token Bearer real obtido numa execução anterior, omita "
    "headers por completo: nunca escreva Authorization, Bearer ou <token>. "
    "Não responda com observações, next_action ou texto explicativo; responda somente no esquema "
    "rationale/tool/params exigido. Quando o histórico disser que há referências de sessão, "
    "use exatamente Authorization:'Bearer $last_token' e/ou $last_basket_id no path; "
    "elas são resolvidas internamente apenas depois de autorização humana. Nunca copie token bruto."
)

INTERPRET_SYSTEM = (
    "Você interpreta o resultado de uma ferramenta de teste de segurança sobre o alvo "
    "autorizado. Responda SOMENTE com JSON:\n"
    '{"interpretation":"o que o resultado mostra, com cautela","hypothesis":"suporta|refuta|inconclusivo","done":false}\n'
    "Uma sugestão não é prova: só afirme o que a evidência sustenta. "
    "Timeout ou erro de ferramenta implica resultado inconclusivo. HTML de uma SPA "
    "com status 200 não demonstra autenticação nem acesso ao carrinho. Não copie o "
    "texto do exemplo. Ausência de evidência não prova segurança."
)


# --------------------------------------------------------------------------- #
# Registro (JSONL, um evento por linha)
# --------------------------------------------------------------------------- #
class Log:
    def __init__(self, investigation):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", investigation):
            raise ValueError("Identificador inválido.")
        self.investigation = investigation
        self.session_id = uuid.uuid4().hex
        self.dir = ROOT / "evidencias" / ("investigacao-" + investigation)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / ("registro-" + self.session_id + ".jsonl")

    def event(self, step, phase, **data):
        rec = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(),
               "investigation": self.investigation, "session_id": self.session_id,
               "step": step, "phase": phase}
        rec.update(data)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec


# --------------------------------------------------------------------------- #
# Supervisão humana
# --------------------------------------------------------------------------- #
def ask(prompt):
    if not sys.stdin.isatty():
        raise RuntimeError("Sessão não interativa: a supervisão humana é obrigatória.")
    return input(prompt).strip()


def ask_required(prompt):
    while True:
        value = ask(prompt)
        if value:
            return value
        print("Preencha este campo para manter a investigação verificável.")


def supervise(proposal):
    """Devolve (decision, final_params, justification). Uma ação modificada é reaprovada."""
    params = proposal.get("params", {})
    while True:
        print("\n  Ferramenta: {}".format(proposal["tool"]))
        print("  Parâmetros: {}".format(json.dumps(params, ensure_ascii=False)))
        print("  Justificativa do modelo: {}".format(proposal.get("rationale", "")))
        choice = ask("  [a]utorizar  [m]odificar  [r]ejeitar  [e]ncerrar > ").lower()
        if choice in ("a", "autorizar"):
            return "autorizado", params, ask_required("  Justificativa técnica: ")
        if choice in ("r", "rejeitar"):
            return "rejeitado", params, ask_required("  Motivo da rejeição: ")
        if choice in ("e", "encerrar"):
            return "encerrar", params, ""
        if choice in ("m", "modificar"):
            raw = ask("  Novos params em JSON: ")
            try:
                updated = json.loads(raw)
                if not isinstance(updated, dict):
                    raise ValueError("params precisa ser um objeto JSON")
                params = updated
                proposal = dict(proposal, params=params)  # reaprovação na volta do laço
            except ValueError as exc:
                print("  JSON inválido ({}); parâmetros mantidos.".format(exc))


# --------------------------------------------------------------------------- #
# Laço principal de uma investigação
# --------------------------------------------------------------------------- #
def run(objective, investigation, max_steps):
    if not objective or re.search(r"<objetivo|\[preencher\]", objective, re.I):
        raise ValueError("Informe um objetivo concreto, sem placeholders.")
    if max_steps < 1:
        raise ValueError("max_steps deve ser positivo.")
    log = Log(investigation)
    log.event(0, "objetivo", objective=objective, target=TARGET, model=MODEL)
    print("Alvo autorizado: {}\nModelo: {}\nRegistro: {}\n".format(TARGET, MODEL, log.path))
    print("Objetivo: {}".format(objective))

    history, step = [], 0
    session = {}
    repair_note = ""
    while step < max_steps:
        step += 1
        # 1) Proposta do modelo ------------------------------------------------
        system = PROPOSAL_SYSTEM.format(target=TARGET, tools=tool_catalog())
        prompt = "Objetivo: {}\n\nHistórico:\n{}{}\n\nProponha a próxima ação como JSON.".format(
            objective, compact_history(history), repair_note)
        try:
            raw = model_generate(system, prompt)
        except (urllib.error.URLError, RuntimeError, OSError) as exc:
            log.event(step, "erro_modelo", error=str(exc))
            print("\n[passo {}] Falha ao consultar o modelo: {}".format(step, exc))
            if ask("  [r]epetir  [e]ncerrar > ").lower().startswith("e"):
                break
            step -= 1
            continue

        proposal = extract_json(raw)
        if not isinstance(proposal, dict) or proposal.get("tool") not in TOOLS \
                or not isinstance(proposal.get("params", {}), dict):
            log.event(step, "erro_modelo", raw=raw[:MODEL_PREVIEW],
                      reason="proposta inválida ou ferramenta desconhecida")
            print("\n[passo {}] Proposta inválida do modelo (nada será executado).".format(step))
            print("  Resposta bruta: {}".format(raw[:400]))
            if ask("  [r]epetir  [e]ncerrar > ").lower().startswith("e"):
                break
            repair_note = (
                "\n\nA resposta anterior foi inválida e NÃO foi executada: {}"
                "\nAgora responda somente com o objeto JSON exigido, incluindo "
                '"tool":"http_request" ou "tool":"tcp_scan" e "params".'
            ).format(raw[:MODEL_PREVIEW])
            step -= 1
            continue
        repair_note = ""
        log.event(step, "proposta", tool=proposal["tool"],
                  params=proposal.get("params", {}), rationale=proposal.get("rationale", ""))

        # 2) Supervisão humana -------------------------------------------------
        print("\n[passo {}] Proposta do modelo:".format(step))
        decision, final_params, justification = supervise(proposal)
        modified = (decision == "autorizado"
                    and final_params != proposal.get("params", {}))
        if modified:
            decision = "modificado"
        log.event(step, "supervisao", decision=decision,
                  proposed_params=proposal.get("params", {}),
                  final_params=final_params, human_justification=justification)

        if decision == "encerrar":
            print("Investigação encerrada pela dupla.")
            break
        if decision == "rejeitado":
            print("Ação rejeitada; não executada.")
            history.append({"step": step, "tool": proposal["tool"],
                            "params": proposal.get("params", {}),
                            "decision": "rejeitado",
                            "status": "não executada: " + justification})
            continue

        # 3) Execução (só do que foi autorizado) ------------------------------
        try:
            execution_params, resolved_refs = resolve_session_references(final_params, session)
            validate_tool_params(proposal["tool"], execution_params)
            result = TOOLS[proposal["tool"]]["run"](execution_params)
            status = "ok"
            log.event(step, "execucao", tool=proposal["tool"], final_params=final_params,
                      resolved_references=resolved_refs, status=status, result=result)
            session.update(capture_session_values(result))
        except (ValueError, RuntimeError, OSError) as exc:
            status = "erro"
            result = {"error": str(exc)}
            log.event(step, "erro_ferramenta", tool=proposal["tool"],
                      final_params=final_params, error=str(exc))
            print("  Erro ao executar: {}".format(exc))

        preview = json.dumps(result, ensure_ascii=False)[:MODEL_PREVIEW]
        print("  Resultado (prévia): {}".format(preview[:600]))

        # 4) Interpretação do modelo ------------------------------------------
        interpretation = ""
        try:
            raw_i = model_generate(
                INTERPRET_SYSTEM,
                "Objetivo: {}\nAção: {} {}\nResultado (prévia):\n{}\n\nInterprete como JSON.".format(
                    objective, proposal["tool"], json.dumps(final_params, ensure_ascii=False),
                    preview),
                num_predict=260)
            parsed = extract_json(raw_i)
            if not isinstance(parsed, dict) or not isinstance(parsed.get("interpretation"), str) or not parsed["interpretation"].strip() or parsed.get("hypothesis") not in ("suporta", "refuta", "inconclusivo"):
                raise RuntimeError("Interpretação inválida: " + raw_i[:300])
            interpretation = parsed.get("interpretation", raw_i[:300])
            log.event(step, "interpretacao", interpretation=interpretation,
                      hypothesis=parsed.get("hypothesis"), model_done=parsed.get("done"))
            print("  Interpretação do modelo: {}".format(interpretation))
            if parsed.get("hypothesis"):
                print("  Situação da hipótese (modelo): {}".format(parsed["hypothesis"]))
        except (urllib.error.URLError, RuntimeError, OSError) as exc:
            log.event(step, "erro_modelo", phase_detail="interpretacao", error=str(exc))
            print("  Modelo não interpretou o resultado: {}".format(exc))

        # 5) Avaliação da dupla e decisão de continuar ------------------------
        if status == "erro":
            print("  Atenção: falha da ferramenta não confirma nem refuta a hipótese.")
        evaluation = ask_required("\n  Sua avaliação deste resultado: ")
        cont = ask("  Continuar a investigação? [s/n] > ").lower()
        log.event(step, "decisao", human_evaluation=evaluation,
                  continue_investigation=cont.startswith("s"))
        history.append({"step": step, "tool": proposal["tool"], "params": final_params,
                        "decision": decision, "status": status,
                        "interpretation": interpretation, "evidence": preview,
                        "human_evaluation": evaluation, "session": dict(session)})
        if not cont.startswith("s"):
            print("Investigação encerrada pela dupla.")
            break
    else:
        print("Limite de {} passos atingido.".format(max_steps))

    conclusion = ask_required("\nConclusão da investigação (hipótese sustentada/rejeitada/inconclusiva e limites): ")
    log.event(step, "conclusao", conclusion=conclusion)
    print("\nRegistro completo em: {}".format(log.path))


def read_plan(path, number):
    """Monta o objetivo da investigação <number> a partir do plano humano.

    Usa o aspecto investigado e a hipótese inicial escritos pela dupla, para que o
    objetivo passado ao agente venha do planejamento, e não digitado à mão.
    """
    text = Path(path).read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^##\s+Investiga\u00e7\u00e3o\s+", text)
    found = None
    for block in blocks[1:]:
        if block.lstrip().startswith(str(number)):
            found = block
            break
    if found is None:
        raise ValueError("Investiga\u00e7\u00e3o {} n\u00e3o encontrada em {}.".format(number, path))

    def field(name):
        m = re.search(r"-\s+\*\*" + re.escape(name) + r":\*\*\s*(.+)", found)
        return m.group(1).strip() if m else ""

    aspecto = field("Aspecto da aplica\u00e7\u00e3o investigado")
    hipotese = field("Hip\u00f3tese inicial")
    if not aspecto and not hipotese:
        raise ValueError("Investiga\u00e7\u00e3o {}: aspecto/hip\u00f3tese vazios no plano.".format(number))
    for v in (aspecto, hipotese):
        if "[preencher]" in v:
            raise ValueError("Investiga\u00e7\u00e3o {} ainda tem campos [preencher].".format(number))
    objetivo = "Aspecto: {}. Hip\u00f3tese a investigar: {}".format(aspecto, hipotese)
    return objetivo.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--id", required=True, help="Identificador (ex.: 01, 02, 03).")
    parser.add_argument("--objetivo", help="Objetivo da investigação (texto livre).")
    parser.add_argument("--plano", help="Arquivo do plano humano; lê a investigação pelo número do --id.")
    parser.add_argument("--max-steps", type=int, default=20, help="Teto de passos (padrão 20).")
    args = parser.parse_args()
    if bool(args.objetivo) == bool(args.plano):
        parser.error("informe exatamente um de --objetivo ou --plano.")
    try:
        if args.plano:
            numero = int(re.sub(r"\D", "", args.id) or "0")
            objetivo = read_plan(args.plano, numero)
            print("Objetivo lido do plano (investigação {}):\n  {}\n".format(numero, objetivo))
        else:
            objetivo = args.objetivo
        run(objetivo, args.id, args.max_steps)
    except KeyboardInterrupt:
        print("\nInterrompido. O registro parcial foi preservado.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

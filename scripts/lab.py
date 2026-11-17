#!/usr/bin/env python3
"""Diagnósticos da Sprint 1, com biblioteca padrão. Não é o agente da Sprint 3."""
import argparse
import datetime as dt
import ipaddress
import json
import platform
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "compose.lock.json"
RECORD = {"started_at": dt.datetime.now(dt.timezone.utc).isoformat(), "steps": []}


def run(args, timeout=120, stream=False):
    print("+ " + " ".join(args), flush=True)
    started = time.monotonic()
    item = {"command": args}
    RECORD["steps"].append(item)
    result = subprocess.run(args, cwd=ROOT, text=True, timeout=timeout,
                            stdout=None if stream else subprocess.PIPE,
                            stderr=None if stream else subprocess.PIPE)
    item.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr,
                seconds=round(time.monotonic() - started, 3))
    if result.returncode:
        raise RuntimeError(result.stderr or "Comando falhou (código {}): {}. Consulte a saída no terminal.".format(result.returncode, " ".join(args)))
    return (result.stdout or "").strip()


def compose(*args, **kwargs):
    cmd = ["docker", "compose", "-f", str(ROOT / "compose.yaml")]
    if LOCK.exists():
        cmd += ["-f", str(LOCK)]
    return run(cmd + list(args), **kwargs)


def configuration():
    return json.loads(compose("--profile", "tools", "config", "--format", "json"))


def service_url(config, service):
    port = config["services"][service]["ports"][0]
    host = port.get("host_ip", "127.0.0.1")
    if host in ("0.0.0.0", "::"):
        host = "127.0.0.1"
    if ":" in host:
        host = "[" + host + "]"
    return validate_target("http://{}:{}".format(host, port["published"]))


def validate_target(url):
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


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError("Redirecionamento bloqueado no diagnóstico: " + newurl)


def http(url, payload=None, timeout=15, json_response=True):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    item = {"url": url, "method": "GET" if data is None else "POST", "request": payload}
    RECORD["steps"].append(item)
    start = time.monotonic()
    with opener.open(request, timeout=timeout) as response:
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise RuntimeError("Resposta acima do limite do diagnóstico (2 MB).")
        result = json.loads(raw) if json_response else raw.decode("utf-8", errors="replace")
        item.update(status=response.status, seconds=round(time.monotonic() - start, 3))
        item["response" if json_response else "body_bytes"] = result if json_response else len(raw)
        return result


def check(config):
    target = service_url(config, "juice-shop")
    model_url = service_url(config, "ollama")
    model = config["services"]["ollama"]["environment"]["LAB_MODEL"]
    http(target + "/", json_response=False)
    http(model_url + "/api/version")
    http(model_url + "/api/tags")
    reply = http(model_url + "/api/generate", {
        "model": model, "prompt": "Responda em português com uma frase curta: o que é um laboratório local?",
        "stream": False, "think": False, "keep_alive": 0,
        "options": {"num_ctx": 2048, "num_predict": 80, "temperature": 0}
    }, timeout=300)
    if reply.get("done") is not True or not reply.get("response", "").strip():
        raise RuntimeError("O modelo não retornou uma resposta completa e não vazia.")
    print("Juice Shop acessível; inferência local confirmada: " + reply["response"])


def pin_images(config):
    services = {}
    for service in ("juice-shop", "ollama"):
        ref = config["services"][service]["image"]
        details = json.loads(run(["docker", "image", "inspect", ref]))[0]
        digests = details.get("RepoDigests", [])
        if not digests:
            raise RuntimeError("Imagem sem RepoDigest; não foi possível fixar " + ref)
        services[service] = {"image": digests[0]}
    LOCK.write_text(json.dumps({"services": services}, indent=2) + "\n")


def inventory(config):
    RECORD["host"] = {"system": platform.system(), "release": platform.release(),
                      "machine": platform.machine(), "python": platform.python_version()}
    if platform.system() == "Darwin":
        run(["sw_vers"])
    run(["docker", "version"])
    compose("version")
    compose("ps", "--format", "json")
    for service in ("juice-shop", "ollama"):
        cid = compose("ps", "-q", service)
        if not cid:
            raise RuntimeError(service + " não está em execução.")
        run(["docker", "inspect", "--format",
             "{{.Name}} image={{.Image}} platform={{.Platform}} ports={{json .NetworkSettings.Ports}}", cid])
    compose("exec", "-T", "juice-shop", "/nodejs/bin/node", "-p", "require('./package.json').version")
    compose("exec", "-T", "ollama", "ollama", "--version")
    compose("exec", "-T", "ollama", "ollama", "list")
    model_url = service_url(config, "ollama")
    http(model_url + "/api/tags")
    http(model_url + "/api/show", {"model": config["services"]["ollama"]["environment"]["LAB_MODEL"]})
    for tool in ("curl", "nmap", "python3"):
        compose("run", "--rm", "--no-deps", "tools", tool, "--version")
    run(["docker", "image", "inspect", "pf-techack-tools", "--format", "{{.Id}}"])


def up(config):
    run(["docker", "info", "--format", "{{.ServerVersion}}"])
    compose("pull", "juice-shop", "ollama", timeout=1800, stream=True)
    pin_images(config)
    compose("up", "-d", "--wait", "--wait-timeout", "240", "juice-shop", "ollama", timeout=300, stream=True)
    model = config["services"]["ollama"]["environment"]["LAB_MODEL"]
    compose("exec", "-T", "ollama", "ollama", "pull", model, timeout=1800, stream=True)
    compose("build", "tools", timeout=1800, stream=True)
    compose("run", "--rm", "--no-deps", "tools", "curl", "--fail", "--silent",
            "--show-error", "--max-time", "15", "--output", "/dev/null", "http://juice-shop:3000/")
    # Read the configuration again so the evidence contains the resolved digests.
    config = configuration()
    check(config)
    inventory(config)


def reset(config):
    before = compose("ps", "-q", "juice-shop")
    if not before:
        raise RuntimeError("Inicie o laboratório antes de testar sua restauração.")
    image_before = run(["docker", "inspect", "--format", "{{.Image}}", before])
    compose("exec", "-T", "juice-shop", "/nodejs/bin/node", "-e",
            "require('fs').writeFileSync('/tmp/pf-techack-reset-marker','sprint-1')")
    compose("up", "-d", "--no-deps", "--force-recreate", "--pull", "never",
            "--wait", "--wait-timeout", "240", "juice-shop", timeout=300, stream=True)
    after = compose("ps", "-q", "juice-shop")
    image_after = run(["docker", "inspect", "--format", "{{.Image}}", after])
    if before == after or image_before != image_after:
        raise RuntimeError("A restauração não recriou o contêiner com a mesma imagem.")
    compose("exec", "-T", "juice-shop", "/nodejs/bin/node", "-e",
            "process.exit(require('fs').existsSync('/tmp/pf-techack-reset-marker')?1:0)")
    target = service_url(config, "juice-shop")
    http(target + "/", json_response=False)
    baseline = http(target + "/api/Challenges")
    challenges = baseline.get("data")
    if (not isinstance(challenges, list) or not challenges
            or any(c.get("solved") is not False for c in challenges)):
        raise RuntimeError("Estado inicial não confirmado: esperados desafios não resolvidos.")
    RECORD["restoration"] = {"before": before, "after": after, "image": image_after,
                             "marker_removed": True, "solved_challenges": 0}
    print("Restauração confirmada. Limpe os dados do site no navegador antes de reutilizá-lo.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["up", "check", "inventory", "reset", "kali-check"])
    parser.add_argument("--confirm", action="store_true", help="Confirma descarte do estado do Juice Shop")
    parser.add_argument("--target", help="URL autorizada, obrigatória para kali-check")
    args = parser.parse_args()
    if args.action == "reset" and not args.confirm:
        parser.error("reset descarta o estado do Juice Shop; use --confirm após guardar evidências")
    RECORD["action"] = args.action
    success = False
    try:
        if args.action == "kali-check":
            if not args.target:
                raise ValueError("Informe --target http://IP_PRIVADO_DO_MAC:3000")
            target = validate_target(args.target)
            RECORD["target"] = target
            RECORD["os"] = platform.platform()
            for tool in ("curl", "nmap", "python3"):
                run([tool, "--version"])
            http(target + "/", json_response=False)
            print("HTTP 200 no alvo e ferramentas disponíveis. Confira a página também no navegador do Kali.")
        else:
            config = configuration()
            {"up": up, "check": check, "inventory": inventory, "reset": reset}[args.action](config)
        success = True
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        RECORD["error"] = str(exc)
        print("ERRO: " + str(exc), file=sys.stderr)
    finally:
        RECORD["success"] = success
        RECORD["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        directory = ROOT / "evidencias" / "sprint-1"
        directory.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output = directory / (stamp + "-" + args.action + ".json")
        output.write_text(json.dumps(RECORD, indent=2, ensure_ascii=False) + "\n")
        print("Registro: " + str(output))
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

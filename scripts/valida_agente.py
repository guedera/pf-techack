#!/usr/bin/env python3
"""Validação de infraestrutura do agente (NÃO é uma investigação).

Rode no Mac, com o laboratório de pé, para comprovar que:
  1. a ferramenta http_request alcança o Juice Shop autorizado;
  2. a ferramenta tcp_scan faz reconhecimento no host autorizado;
  3. o escopo bloqueia um destino externo antes de qualquer contato;
  4. o modelo local propõe uma ação em JSON e interpreta um resultado.

Exercita as PEÇAS do agente, sem simular supervisão humana: não autoriza nada
automaticamente no laço supervisionado. O resultado vai para
evidencias/validacao-agente/ e serve como evidência da Sprint 3, separada das
investigações finais.
"""
import datetime as dt
import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("agente", ROOT / "scripts/agente.py")
ag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ag)

rec = {"started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
       "target": ag.TARGET, "model": ag.MODEL, "checks": []}


def check(name, fn):
    item = {"name": name}
    try:
        item["result"] = fn()
        item["ok"] = True
        print("[OK] {}".format(name))
    except Exception as exc:                       # noqa: BLE001 — validação registra qualquer falha
        item["ok"] = False
        item["error"] = str(exc)
        print("[FALHA] {}: {}".format(name, exc))
    rec["checks"].append(item)


def c_http():
    r = ag.tool_http_request({"method": "GET", "path": "/rest/products/search?q="})
    assert r["status"] in (200, 304), "status inesperado: {}".format(r["status"])
    return {"status": r["status"], "content_type": r["content_type"],
            "bytes": r["bytes"], "redirect": r["location"]}


def c_tcp():
    r = ag.tool_tcp_scan({"ports": str(ag.TARGET_PORT)})
    assert ag.TARGET_PORT in r["open"], "porta do alvo não aberta"
    return r


def c_scope():
    for bad in ("//example.org/", "http://8.8.8.8/"):
        try:
            ag._build_http_url(bad)
            raise AssertionError("escopo não bloqueou " + bad)
        except ValueError:
            pass
    return "destinos externos bloqueados antes de qualquer requisição"


def c_model_proposal():
    sysp = ag.PROPOSAL_SYSTEM.format(target=ag.TARGET, tools=ag.tool_catalog())
    prompt = ("Objetivo: enumerar a API REST da aplicação.\n\nHistórico:\n"
              "(sem ações anteriores)\n\nProponha a próxima ação como JSON.")
    t = time.monotonic()
    raw = ag.model_generate(sysp, prompt)
    prop = ag.extract_json(raw)
    out = {"seconds": round(time.monotonic() - t, 1), "parsed": bool(prop)}
    if isinstance(prop, dict):
        out["tool"] = prop.get("tool")
        out["valid_tool"] = prop.get("tool") in ag.TOOLS
        out["params"] = prop.get("params")
    else:
        out["raw_preview"] = raw[:200]
    return out


def c_model_interpret():
    res = ag.tool_http_request({"method": "GET", "path": "/rest/products/search?q="})
    prev = json.dumps(res, ensure_ascii=False)[:ag.MODEL_PREVIEW]
    raw = ag.model_generate(
        ag.INTERPRET_SYSTEM,
        "Objetivo: enumerar a API.\nAção: http_request GET /rest/products/search\n"
        "Resultado (prévia):\n{}\n\nInterprete como JSON.".format(prev),
        num_predict=220)
    parsed = ag.extract_json(raw) or {}
    return {"hypothesis": parsed.get("hypothesis"),
            "interpretation": (parsed.get("interpretation") or raw)[:300]}


check("http_request alcança o Juice Shop", c_http)
check("tcp_scan no host autorizado", c_tcp)
check("escopo bloqueia destino externo", c_scope)
check("modelo propõe ação em JSON", c_model_proposal)
check("modelo interpreta resultado", c_model_interpret)

rec["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
rec["success"] = all(c["ok"] for c in rec["checks"])
out_dir = ROOT / "evidencias" / "validacao-agente"
out_dir.mkdir(parents=True, exist_ok=True)
stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
path = out_dir / (stamp + "-validacao.json")
path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
print("\nsucesso={}  registro={}".format(rec["success"], path))

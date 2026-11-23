# Agente supervisionado — Sprint 3

`scripts/agente.py`. Só biblioteca padrão (Python 3.9+), como o `lab.py`.
Não é um agente autônomo: **nenhuma ação roda sem autorização humana**.

## Ciclo

```
objetivo → modelo propõe UMA ação (JSON) → dupla autoriza / modifica / rejeita
        → ferramenta roda só se autorizada → resultado volta ao modelo
        → modelo interpreta → próxima proposta considera o histórico
```

A próxima ação depende dos resultados anteriores (o histórico entra no prompt);
não é uma sequência fixa de comandos.

## Arquitetura

- **Modelo local:** Ollama em `127.0.0.1:11434`, modelo do `.env` (`qwen3:1.7b`),
  via `/api/generate` com `think:false`, `temperature:0`, `num_ctx:2048`. A saída
  do modelo é lida como JSON (`extract_json`); resposta sem JSON válido é tratada
  como proposta inválida e **nada é executado**.
- **Ferramentas** (catálogo em `TOOLS`), cada uma com validação de parâmetros e
  sem acesso livre ao terminal:
  - `http_request` — uma requisição HTTP ao Juice Shop (interage direto com o
    alvo). `params`: `method` (GET/POST/PUT/DELETE/PATCH), `path` (começa com
    `/`), `headers` (objeto; permite `Authorization: Bearer <token>` para testar
    autenticação e autorização), `body` e `content_type` opcionais. Cabeçalhos
    são validados (sem CR/LF, máx. 20). A resposta devolve status, cabeçalhos
    (inclui `Set-Cookie`) e corpo. Não segue redirecionamentos (o 3xx volta para
    análise); 4xx/5xx também voltam como resposta.
  - `tcp_scan` — TCP connect no host do alvo (reconhecimento). `params`: `ports`
    (`"3000"`, `"1-1024"`, `"80,443"`; máximo 100 portas).
- **Escopo travado:** o alvo vem do `.env` e passa por `validate_target` (só
  loopback/LAN/VPN privada). Toda requisição é reconstruída e tem host/porta
  conferidos contra o alvo **antes** de qualquer contato; `tcp_scan` só usa o
  host autorizado. Um destino externo é recusado sem nenhuma conexão.
- **Limites:** HTTP lê no máximo 200 KB e tem timeout ≤ 30 s; `tcp_scan` tem
  timeout curto por porta. Ao modelo vai só uma prévia (1500 caracteres); o
  registro guarda a saída completa.

## Registro (JSONL)

`evidencias/investigacao-<id>/registro.jsonl`, um evento por linha, com fases:
`objetivo`, `proposta`, `supervisao` (decisão + parâmetros propostos e finais +
justificativa humana), `execucao`, `erro_ferramenta`, `interpretacao`, `decisao`
(avaliação da dupla) e `conclusao`. Ações rejeitadas e falhas também entram, o
que permite reconstruir a sessão inteira.

## Como rodar (no Mac, com o laboratório de pé)

```bash
python3 scripts/agente.py --id 01 --objetivo "enumerar a API REST da aplicação"
```

A cada proposta: `[a]utorizar  [m]odificar  [r]ejeitar  [e]ncerrar`. Uma ação
modificada é mostrada de novo e precisa ser autorizada. Ao fim, informe a
conclusão (hipótese sustentada, rejeitada ou inconclusiva e seus limites).

Validação de infraestrutura (uma vez, não é investigação):

```bash
python3 scripts/valida_agente.py
```

## Verificações da Sprint 3 e onde estão cobertas

| Verificação | Onde |
| --- | --- |
| Ação rejeitada não executa | `supervise` + laço; `tests/test_agente.py::test_reject...` |
| Ação modificada executa só os parâmetros finais | `supervise`; `test_modify_requires_reapproval...` |
| Destino fora do escopo bloqueado antes do contato | `_build_http_url`/`tool_tcp_scan`; `test_build_url_rejects...`, `valida_agente` |
| As duas ferramentas funcionam | `valida_agente.py` (no Mac) |
| Resultado volta ao modelo e influencia a próxima proposta | laço `run` (histórico no prompt) |
| Falha/resposta inválida não interrompe o registro nem executa | `erro_modelo`/`erro_ferramenta`; `test_returns_none_for_no_json` |
| Registros reconstroem a sessão | eventos JSONL por fase |
| Redirecionamento não é seguido | `NoRedirect`; `test_redirect_handler...` |
| Saída completa preservada quando a prévia é reduzida | `Log`; `test_full_output_preserved_in_log` |

## Limitações conhecidas (para o relatório)

- `qwen3:1.7b` é pequeno: pode devolver JSON malformado ou propor ações pouco
  úteis. O agente trata isso sem executar nada e deixa a decisão com a dupla.
- As ferramentas são propositalmente estreitas; investigações que peçam outra
  capacidade exigem estender `TOOLS`, com nova validação e justificativa.
- O transporte é HTTP sem TLS por construção do laboratório; não confundir isso
  com uma falha da aplicação.

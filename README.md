# PF-TecHaker — laboratório local

Avaliação final de Tecnologias Hackers: OWASP Juice Shop, LLM local e, na Sprint 3,
um agente supervisionado. **O ambiente será executado nas máquinas pessoais da
dupla, em substituição ao kit da faculdade, conforme orientação informada pelo
grupo. Essa adaptação deve constar no relatório final.**

## Sprint 1

- Mac de Luiz: Docker Desktop com Juice Shop, Ollama e ferramentas auxiliares.
- Máquina da dupla: VM Kali para acessar exclusivamente o Juice Shop autorizado.
- Rede entre as máquinas: LAN do laboratório WannaCry; exemplo de configuração começa em loopback.
- Modelo inicial: `qwen3:1.7b`, considerando o Mac M1 com 8 GB; configurável.

Abra o Docker Desktop e, no terminal do Mac, dentro deste repositório:

```bash
cp .env.example .env
python3 scripts/lab.py up
```

Não repita o `cp` se já personalizou `.env`. O comando `up` baixa as imagens,
inicializa os serviços, baixa o modelo, prepara curl/Nmap/Python no contêiner de
ferramentas, valida o HTTP e a geração local e grava evidências. O primeiro uso
depende de internet para downloads; a inferência é local.

Abra <http://127.0.0.1:3000>. Depois valide a restauração:

```bash
python3 scripts/lab.py reset --confirm
python3 scripts/lab.py inventory
```

`reset` descarta o estado do Juice Shop deste projeto; guarde as evidências antes.
Não remove o volume do modelo. As imagens baixadas são fixadas por digest em
`compose.lock.json` durante `up`; preserve esse arquivo na entrega.

**Estado atual:** inicialização, inferência local, ferramentas e restauração
validadas em 17/11/2026 pelos registros de sucesso de `up` e `reset`.
LAN WannaCry: `172.16.50.247:3000` respondeu HTTP 200 no Mac e no script do Kali.
Interface no Firefox do Kali confirmada após desativar o proxy do navegador.
O critério funcional da Sprint 1 foi atendido; faltam trazer o JSON original e a
captura da aplicação aberta no Kali e completar seu inventário. O
[print do JSON do Kali](evidencias/sprint-1/kali-check-json.png) já está incluído nas
[evidências da Sprint 1](evidencias/sprint-1/README.md). Próxima etapa: preencher
[o planejamento humano](docs/plano-humano.md), posteriormente registrado no commit `5191db0`.
O problema inicial do caminho do Node foi corrigido. Consulte
[o registro da preparação](docs/sprint-1-status.md).

As instruções de recursos, acesso da dupla, ferramentas, versões e solução de
problemas estão em [docs/laboratorio.md](docs/laboratorio.md).
O planejamento completo está em [sprints.md](sprints.md).

## Agente supervisionado (Sprint 3)

O agente (`scripts/agente.py`) integra o modelo local a duas ferramentas
delimitadas (`http_request` no Juice Shop e `tcp_scan` de reconhecimento). O
modelo propõe uma ação, a dupla autoriza, modifica ou rejeita, a ferramenta roda
só se autorizada e o resultado volta ao modelo. O alvo é travado no Juice Shop
autorizado e tudo é gravado em `evidencias/investigacao-<id>/registro.jsonl`.

```bash
python3 scripts/agente.py --id 01 --plano docs/plano-humano.md   # objetivo vindo do plano
python3 scripts/agente.py --id 01 --objetivo "texto livre"        # ou objetivo digitado
python3 scripts/valida_agente.py   # valida ferramentas e modelo (não é investigação)
```

Detalhes, limites e verificações em [docs/agente.md](docs/agente.md). Testes
offline: `python3 -m unittest discover -s tests`.

## Retomada em 23/11/2026

O plano original já está registrado. O agente corrigido passou em 29 testes offline.
Em 23/11/2026, o laboratório subiu com sucesso e a validação real confirmou HTTP,
TCP, bloqueio de destino externo, proposta em JSON e interpretação pelo modelo.
Os três registros históricos não sustentam confirmação ou rejeição das hipóteses.
Suas conclusões foram reavaliadas em resumos separados, sem alterar os JSONL.

- [Passos para concluir a entrega](docs/proximos-passos.md)
- [Plano revisado com apoio de IA](docs/plano-revisado.md)
- [Análise crítica baseada nas evidências existentes](docs/analise-critica.md)
- [Relatório técnico — versão de trabalho](docs/relatorio-tecnico.md)
- [Roteiro do vídeo](docs/roteiro-video.md)

Cada nova sessão gera `registro-<sessao>.jsonl`. Justificativas e avaliação humana
são obrigatórias. A ferramenta TCP permite somente a porta do Juice Shop,
e o histórico inclui evidências e correções humanas. O laboratório está pronto; o
próximo marco é executar as três sessões com decisões humanas reais.

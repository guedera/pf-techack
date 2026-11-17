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
LAN WannaCry: `.env` local preparado para `172.16.50.247:3000`; falta aplicar
essa configuração no Docker, validar o acesso pelo Kali e completar seu inventário.
O problema inicial do caminho do Node foi corrigido. Consulte
[o registro da preparação](docs/sprint-1-status.md).

As instruções de recursos, acesso da dupla, ferramentas, versões e solução de
problemas estão em [docs/laboratorio.md](docs/laboratorio.md).
O planejamento completo está em [sprints.md](sprints.md).

O planejamento inicial das investigações (Sprint 2) deverá ser escrito pela dupla
sem apoio do LLM, conforme o enunciado. Os diagnósticos desta sprint apenas
validam a infraestrutura.

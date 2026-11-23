# Retomada e fechamento da entrega

## Estado em 23/11/2026

Laboratório e agente possuem implementação e registros históricos. O agente foi corrigido após revisão das evidências. As três investigações históricas são inconclusivas pelos motivos descritos em `analise-critica.md`; os registros foram preservados. O plano revisado é uma proposta com apoio de IA, a ser avaliada pela dupla.

Em 23/11/2026, Guilherme iniciou o laboratório e guardou o registro `evidencias/sprint-1/20261123T221802982327Z-up.json`. O Juice Shop e o Ollama ficaram saudáveis. Após corrigir a checagem de parâmetros, a validação confirmou HTTP, TCP, bloqueio de destino externo, geração em JSON e interpretação local. O registro válido mais recente é `evidencias/validacao-agente/20261123T222212507024Z-validacao.json`; a execução anterior foi preservada porque documenta o falso positivo com `<token>`.

## 1. Serviços e validação concluídos

Os comandos executados foram:

```bash
python3 scripts/lab.py up
python3 scripts/valida_agente.py
```

Sem `.env`, os padrões são loopback, portas 3000/11434 e Qwen3 1.7B. Se já houver `.env`, conferir os valores antes; não sobrescrevê-lo. A primeira inicialização neste Mac baixa imagens/modelo e constrói ferramentas. O lock fixa as imagens. O `up` executa pull do modelo, cujo digest deve ser comparado com os registros históricos. Registrar eventual mudança de modelo/host, sem tratar a reprodução como a sessão anterior.

Após uma correção adicional para rejeitar também parâmetros inválidos antes da execução, rodar novamente apenas `python3 scripts/valida_agente.py`. Validar também o acesso a partir do Kali usando o endereço privado efetivamente configurado; loopback do Mac não é acessível como localhost dentro da VM.

## 2. Revisar o plano

Ler `plano-revisado.md` e preencher as decisões reais em `revisao-plano.md`. O assistente propôs os ajustes técnicos; as justificativas da dupla não foram inventadas. Preservar o planejamento original.

## 3. Executar as sessões supervisionadas

Guardar dados úteis antes de cada reset, pois ele descarta o estado do Juice Shop. Abrir uma sessão privada nova no navegador. Repetir para IDs 01, 02 e 03:

```bash
python3 scripts/lab.py reset --confirm
python3 scripts/agente.py --id 01 --plano docs/plano-revisado.md
```

O agente lê o objetivo do plano, mas a dupla informa descobertas, tokens e IDs reais ao modificar parâmetros e avaliar resultados. Não autorizar placeholders ou conclusões baseadas apenas em HTTP 200. A próxima proposta recebe a prévia do resultado e a avaliação humana. Os novos arquivos `registro-<sessao>.jsonl` não sobrescrevem os antigos.

Ao terminar, atualizar o resumo de cada investigação com o estado inicial, a sessão nova, intervenções e conclusão. Citar o nome do arquivo e a etapa para não confundir sessões.

## 4. Preparar a entrega

- Completar inventário atual do host e Kali; trazer JSON original/captura do Kali, se disponíveis. Não reconstruir registros como se fossem originais.
- Incorporar resultados novos na análise crítica e no relatório técnico. Renderizar e conferir 4–6 páginas; Markdown não garante paginação.
- Gravar vídeo de até 10 minutos com `roteiro-video.md`.
- Reproduzir o laboratório pelas instruções, guardar validação real e conferir cinco entregáveis: laboratório, código, registros, relatório e vídeo.
- Conferir prazo, formato e canal de submissão na disciplina.

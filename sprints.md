# Sprints — Avaliação Final de Tecnologias Hackers

## Objetivo

Construir, no kit de laboratório da disciplina, um ambiente reproduzível com OWASP Juice Shop, um LLM local e um agente supervisionado; realizar três investigações de segurança; entregar código, configurações, registros, relatório e vídeo.

Este guia organiza os requisitos do enunciado **AF - Tecnologias Hackers 26-2.pdf**. A divisão em sprints, os nomes dos arquivos e as escolhas de implementação sugeridas abaixo são propostas de organização, não exigências adicionais do professor.

## Como usar

- Executar as sprints na ordem e marcar os itens apenas após verificá-los.
- Distribuir responsáveis e datas entre os integrantes conforme a disponibilidade do grupo.
- Guardar evidências durante o trabalho, sem depender de reconstruí-las na hora de escrever o relatório.
- Avançar quando o critério de conclusão da sprint estiver atendido.
- Manter todos os testes restritos à instância local do Juice Shop.

> **Planejamento inicial sem IA:** o enunciado exige que a estratégia inicial seja elaborada pelo próprio grupo, sem apoio do LLM. Este documento é um guia de execução produzido com IA e não deve ser apresentado como o planejamento humano. Na Sprint 2, o grupo deverá formular e registrar suas próprias hipóteses, ferramentas e evidências antes de pedir revisão ao modelo.

## Visão geral

| Sprint | Resultado esperado |
| --- | --- |
| 1 — Laboratório | Juice Shop e LLM local acessíveis, ferramentas disponíveis e restauração verificada |
| 2 — Planejamento humano | Estratégia inicial registrada antes da revisão pelo modelo |
| 3 — Agente supervisionado | Ciclo de proposta, supervisão, execução, interpretação e registro funcionando |
| 4 — Investigações | Três investigações distintas concluídas e documentadas |
| 5 — Análise e relatório | Análise crítica sustentada por evidências e relatório de 4 a 6 páginas |
| 6 — Reprodução e entrega | Documentação validada, vídeo de até 10 minutos e pacote final conferido |

## Sprint 1 — Preparar o laboratório

### Tarefas

- [ ] Definir onde cada componente será executado no kit: Juice Shop, Kali, modelo local e agente.
- [ ] Registrar máquinas, sistemas, endereços, portas e versões utilizadas.
- [ ] Instalar e iniciar uma instância local do OWASP Juice Shop.
- [ ] Confirmar que o Kali consegue acessar essa instância.
- [ ] Instalar Ollama ou solução equivalente e disponibilizar um LLM local para integração.
- [ ] Escolher o modelo conforme os recursos do kit; Qwen3 4B quantizado é um exemplo do enunciado, não uma obrigação.
- [ ] Confirmar que o programa poderá consultar o modelo pela interface local escolhida.
- [ ] Preparar as ferramentas que poderão ser integradas ao agente.
- [ ] Definir o endereço e a porta autorizados para os testes.
- [ ] Documentar um procedimento de reinício ou restauração do Juice Shop a um estado conhecido.
- [ ] Executar esse procedimento e verificar que o estado esperado foi recuperado.
- [ ] Registrar os comandos e configurações necessários para reproduzir a instalação e a inicialização.

### Saídas sugeridas

- `docs/laboratorio.md`: arquitetura, requisitos, versões, instalação, inicialização e restauração.
- Arquivos de configuração e scripts usados para preparar o ambiente, conforme a solução escolhida.

### Critério de conclusão

O Kali acessa o Juice Shop, o LLM responde localmente e o grupo consegue restaurar a aplicação seguindo as instruções registradas. O ambiente está pronto para receber o agente.

## Sprint 2 — Registrar o planejamento humano

### Tarefas

- [ ] Fazer a análise inicial do ambiente sem apoio do LLM e guardar as observações relevantes.
- [ ] Escolher três situações distintas a investigar e justificar sua relevância para a disciplina.
- [ ] Para cada situação, registrar o aspecto da aplicação que será investigado.
- [ ] Formular a hipótese inicial e explicar sua motivação.
- [ ] Descrever como o grupo realizaria o teste.
- [ ] Indicar quais ferramentas poderiam contribuir e por quê.
- [ ] Definir as evidências necessárias para sustentar a conclusão e as condições de encerramento do teste.
- [ ] Salvar uma versão datada do planejamento antes de qualquer revisão pelo modelo, preferencialmente em um commit separado.

O enunciado sugere reconhecimento e enumeração, autenticação ou autorização, e tratamento de entradas, requisições ou acesso a recursos. Outros temas são permitidos, desde que justificados. A escolha e o desenvolvimento das hipóteses iniciais cabem ao grupo.

### Saída sugerida

- `docs/plano-humano.md`: estratégia original das três investigações, preservada para comparação posterior.

### Critério de conclusão

As três investigações possuem hipóteses, estratégias, ferramentas possíveis e evidências esperadas registradas pelo grupo, sem revisão prévia do LLM.

## Sprint 3 — Desenvolver e validar o agente supervisionado

### Tarefas

- [ ] Escolher a linguagem e uma arquitetura que todos os integrantes consigam explicar.
- [ ] Implementar a comunicação com o modelo local.
- [ ] Integrar no mínimo duas ferramentas, sendo pelo menos uma capaz de interagir diretamente com o Juice Shop.
- [ ] Definir os parâmetros aceitos e os limites de cada ferramenta.
- [ ] Implementar a entrada de um objetivo de investigação.
- [ ] Fazer o modelo analisar o histórico disponível e propor uma ferramenta, seus parâmetros e a justificativa da ação.
- [ ] Exibir a proposta antes da execução e permitir ao grupo **autorizar, modificar ou rejeitar**.
- [ ] Exigir aprovação também para a versão modificada de uma ação.
- [ ] Executar apenas ações autorizadas e devolver o resultado ao modelo.
- [ ] Solicitar a interpretação do resultado e permitir que a próxima proposta considere as evidências anteriores.
- [ ] Permitir que o grupo registre sua avaliação do resultado e encerre a investigação.
- [ ] Registrar falhas de execução e tratar respostas inválidas do modelo sem executar ações não validadas.
- [ ] Aplicar limites de tempo e de saída das ferramentas; preservar o resultado completo nos registros quando o conteúdo enviado ao modelo for reduzido.
- [ ] Restringir o destino das ferramentas ao Juice Shop autorizado, incluindo o tratamento de redirecionamentos HTTP.
- [ ] Evitar acesso irrestrito ao terminal: disponibilizar operações delimitadas com validação de parâmetros.
- [ ] Implementar o registro completo das interações e decisões relevantes.

Uma implementação possível é um programa Python com integração ao Ollama e duas ferramentas delimitadas baseadas em `curl` e Nmap. Essa escolha é opcional e deve ser justificada pelo grupo conforme o plano de testes.

### Registro mínimo por etapa

| Informação | Conteúdo |
| --- | --- |
| Identificação | Investigação, execução, etapa e data/hora |
| Proposta | Ação, justificativa, ferramenta e parâmetros sugeridos pelo modelo |
| Supervisão | Autorização, modificação ou rejeição, com justificativa humana |
| Execução | Parâmetros efetivamente utilizados, saída, erros e status da ferramenta |
| Interpretação | Análise apresentada pelo modelo sobre o resultado |
| Decisão posterior | Avaliação do grupo e decisão sobre continuidade ou encerramento |

JSONL é uma opção prática para os registros, mas o formato fica a critério do grupo. Ações rejeitadas também devem aparecer no histórico, identificadas como não executadas.

### Verificações

- [ ] Uma ação rejeitada não executa a ferramenta.
- [ ] Uma ação modificada executa apenas os parâmetros finais autorizados.
- [ ] Uma proposta para um destino fora do escopo é bloqueada antes de qualquer contato com esse destino.
- [ ] As duas ferramentas integradas funcionam no laboratório.
- [ ] O resultado de uma ferramenta retorna ao modelo e influencia a proposta seguinte.
- [ ] Uma falha de ferramenta ou resposta inválida não interrompe o registro nem provoca execução indevida.
- [ ] Os registros permitem reconstruir uma sessão de ponta a ponta.

### Saídas sugeridas

- Código-fonte do agente, configuração de exemplo e declaração de dependências.
- Instruções de execução no `README.md`.
- Registros de validação separados dos registros das investigações finais.

### Critério de conclusão

O ciclo objetivo → proposta → decisão humana → execução → interpretação → nova proposta funciona com pelo menos duas ferramentas. O comportamento depende dos resultados obtidos, e todas as decisões relevantes ficam registradas.

## Sprint 4 — Revisar o plano e executar três investigações

### Revisão do planejamento

- [ ] Apresentar ao modelo o planejamento humano já registrado.
- [ ] Guardar as sugestões recebidas sem sobrescrever a estratégia original.
- [ ] Registrar quais sugestões foram aceitas, modificadas ou rejeitadas, com justificativa técnica.
- [ ] Definir a versão do plano que orientará os experimentos, permitindo novas hipóteses durante a investigação.

### Checklist para cada investigação

Repetir esta lista para as investigações 1, 2 e 3:

- [ ] Registrar hipótese inicial, motivação e estratégia proposta pelo grupo.
- [ ] Estabelecer e registrar o estado inicial do Juice Shop; usar a restauração quando necessário para repetir ou comparar testes.
- [ ] Informar o objetivo ao agente e iniciar uma sessão identificada.
- [ ] Avaliar cada ação proposta, registrando autorização, modificação ou rejeição e seus motivos.
- [ ] Guardar as ações executadas, parâmetros, resultados e interpretações do modelo.
- [ ] Relacionar cada conclusão às evidências concretas coletadas.
- [ ] Registrar intervenções humanas e mudanças de hipótese ou estratégia.
- [ ] Encerrar com uma conclusão: hipótese sustentada, rejeitada ou resultado inconclusivo, explicando os limites das evidências.
- [ ] Identificar os trechos de registro que serão citados no relatório.

### Saídas sugeridas

- `docs/revisao-plano.md`: sugestões da IA e decisões do grupo.
- `evidencias/investigacao-01/`, `evidencias/investigacao-02/` e `evidencias/investigacao-03/`: registros completos e evidências de cada investigação.
- Um resumo por investigação contendo hipótese, estratégia, contribuição do agente, execução, intervenção humana e conclusão.

### Critério de conclusão

Existem três investigações distintas, com registros completos e conclusões sustentadas pelas evidências. Não é necessário confirmar uma vulnerabilidade em todas elas; uma hipótese rejeitada por testes adequados também é um resultado válido.

## Sprint 5 — Analisar a IA e escrever o relatório

### Análise crítica

- [ ] Comparar a estratégia humana inicial com as contribuições e decisões do agente.
- [ ] Identificar sugestões tecnicamente adequadas e avaliar a coerência das ferramentas escolhidas.
- [ ] Mostrar se os resultados anteriores influenciaram as ações seguintes, citando etapas dos registros.
- [ ] Verificar interpretações incorretas ou conclusões sem evidência.
- [ ] Identificar ações repetitivas, desnecessárias ou inadequadas, quando ocorrerem.
- [ ] Explicar em quais momentos a intervenção humana foi necessária.
- [ ] Discutir limitações do modelo e da integração desenvolvida.
- [ ] Apresentar **pelo menos um exemplo concreto de limitação, erro ou dificuldade observada**, explicando como foi identificado e tratado.

Usar acontecimentos efetivamente registrados. Se ainda não houver um exemplo concreto de dificuldade ou limitação, revisar os registros e realizar uma validação complementar no laboratório para observar e documentar o comportamento; não inventar uma ocorrência.

### Relatório técnico — 4 a 6 páginas

- [ ] Apresentar objetivo, escopo e arquitetura do laboratório.
- [ ] Explicar o funcionamento do agente, as ferramentas integradas e os limites aplicados.
- [ ] Descrever a estratégia de testes e a revisão pelo modelo.
- [ ] Apresentar as três investigações com seus resultados e evidências relevantes.
- [ ] Incluir a análise crítica da IA e a comparação com a estratégia inicial.
- [ ] Relacionar as conclusões aos registros disponíveis.
- [ ] Priorizar interpretação dos resultados; manter instruções extensas de instalação na documentação do laboratório.
- [ ] Usar capturas de tela somente quando contribuírem para uma análise.
- [ ] Conferir a extensão de 4 a 6 páginas no documento final renderizado.

### Critério de conclusão

O relatório tem de 4 a 6 páginas, cobre arquitetura, estratégia, resultados e análise crítica, e permite localizar as evidências que sustentam suas conclusões. Os registros completos continuam disponíveis fora do relatório.

## Sprint 6 — Validar a reprodução e preparar a entrega

### Reprodução

- [ ] Seguir as instruções de preparação em um ambiente limpo ou restaurado, preferencialmente com outro integrante executando os passos.
- [ ] Confirmar que as instruções cobrem Juice Shop, modelo local, agente, ferramentas e restauração.
- [ ] Conferir versões, dependências e valores de configuração necessários.
- [ ] Reproduzir uma sessão do agente e verificar a geração dos registros.
- [ ] Corrigir qualquer etapa que dependa de conhecimento não documentado.

### Vídeo — até 10 minutos

- [ ] Apresentar brevemente o laboratório e a arquitetura do agente.
- [ ] Demonstrar o funcionamento do agente.
- [ ] Apresentar pelo menos uma investigação completa, da hipótese inicial à conclusão.
- [ ] Destacar as decisões do modelo e as intervenções do grupo.
- [ ] Mostrar evidências e explicar o que elas permitem concluir.
- [ ] Conferir áudio, legibilidade e duração máxima de 10 minutos.

### Conferência final dos entregáveis

- [ ] **Laboratório reproduzível:** instruções e configurações para executar os componentes no kit.
- [ ] **Código do agente:** fontes, integrações, dependências e instruções de execução.
- [ ] **Registros dos testes:** evidências completas das três investigações, disponíveis para consulta e verificação.
- [ ] **Relatório técnico:** documento final de 4 a 6 páginas.
- [ ] **Vídeo:** apresentação de até 10 minutos com uma investigação completa.
- [ ] Conferir o prazo, o canal de submissão e os formatos de envio na orientação da disciplina; esses detalhes não estão especificados no PDF analisado.
- [ ] Verificar se os arquivos e eventuais links de entrega abrem corretamente.

### Critério de conclusão

Todos os cinco entregáveis estão prontos, consistentes entre si e acessíveis para avaliação. O laboratório pode ser reproduzido a partir da documentação fornecida.

## Pesos da avaliação

| Critério | Peso |
| --- | --- |
| Funcionamento e reprodução do laboratório | 15% |
| Desenvolvimento e integração do agente supervisionado | 20% |
| Planejamento e qualidade técnica dos testes | 20% |
| Qualidade das evidências e interpretação dos resultados | 20% |
| Análise crítica da contribuição da IA | 20% |
| Documentação e apresentação | 5% |

A quantidade de vulnerabilidades identificadas e o nível de autonomia do agente não são os critérios centrais da avaliação. A prioridade é conduzir testes bem fundamentados, supervisionar as ações e sustentar as conclusões com evidências.

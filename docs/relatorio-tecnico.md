# Testes de segurança com agente de IA supervisionado

**Luiz Miguel e Guilherme Guedes — Tecnologias Hackers**
**Versão consolidada: 24/11/2026**

## 1. Objetivo e escopo

O trabalho avalia o uso de um modelo de linguagem local como apoio a testes de segurança supervisionados. O alvo é exclusivamente uma instância local e isolada do OWASP Juice Shop. O agente não possui terminal livre, não aceita outro destino e somente dispõe de requisições HTTP ao alvo e de diagnóstico TCP da porta autorizada. Cada ação proposta exige uma decisão explícita da dupla: autorizar, modificar, rejeitar ou encerrar.

O objetivo não foi provar autonomia do modelo. O experimento avalia se suas propostas ajudam a investigar hipóteses verificáveis e como a supervisão humana corrige erros de rota, parâmetros, interpretação e conclusão. Todas as contas, produtos e dados usados nas investigações foram fictícios e criados no laboratório.

## 2. Ambiente e agente

O laboratório utiliza Docker para executar Juice Shop e Ollama. A aplicação foi acessada localmente em `http://127.0.0.1:3000`; o modelo usado foi `qwen3:1.7b`. As imagens são fixadas em `compose.lock.json`, e `scripts/lab.py` registra inicialização, verificação e restauração em JSON. Os registros de Sprint 1 documentam a disponibilidade do Juice Shop, do modelo e do ambiente.

O agente, implementado em `scripts/agente.py` apenas com biblioteca padrão do Python, registra cada objetivo, proposta, decisão humana, execução, interpretação e conclusão em JSONL. A ferramenta HTTP valida host, porta, método e cabeçalhos antes do contato com o alvo. Ela não segue redirecionamentos e limita o tamanho da resposta. A ferramenta TCP só permite a porta configurada do Juice Shop.

Durante o experimento, o agente foi ajustado em resposta a limitações observadas do modelo: propostas JSON truncadas, placeholders de token, repetição de respostas inválidas e tentativa de copiar tokens no prompt. A versão final usa referências internas aprováveis (`$last_token` e `$last_basket_id`) que só são resolvidas no instante da execução e não precisam aparecer no histórico do modelo. Os testes unitários locais do agente passaram após essas alterações.

## 3. Método

O plano revisado definiu, antes da execução, critérios de sustentação, rejeição e inconclusão. Cada investigação combinou controles e uma conclusão limitada ao endpoint e estado realmente avaliados.

1. **Login:** comparar falha de senha de uma conta fictícia existente com falha para endereço inexistente, depois de confirmar o login válido.
2. **Carrinhos:** comprovar propriedade de dois carrinhos de contas fictícias A e B, inserir um produto conhecido em B e tentar a leitura de B usando a sessão de A.
3. **Arquivos internos:** usar `robots.txt` somente como pista, consultar uma lista curta de caminhos justificados e verificar se algum recurso interno é entregue sem autenticação.

As sessões históricas permanecem preservadas em `registro.jsonl`. Elas serviram para evidenciar limitações iniciais, mas as conclusões abaixo foram produzidas somente a partir dos novos registros citados em cada resumo.

## 4. Resultados

| Investigação | Evidência principal | Resultado |
| --- | --- | --- |
| 1 — Login | Dois logins inválidos retornaram a mesma assinatura: HTTP 401, 26 bytes e mesmo ETag | Hipótese rejeitada no recorte |
| 2 — Carrinhos | Sessão de A leu o carrinho 7 de B, contendo item conhecido, com HTTP 200 e 747 bytes | Hipótese sustentada no recorte |
| 3 — Arquivos | Sem autenticação, `/ftp/incident-support.kdbx` retornou HTTP 200, `application/octet-stream` e 3.246 bytes | Hipótese sustentada no recorte |

### 4.1 Tratamento do login

O agente inicialmente propôs rota, campos e token fictícios incorretos. A dupla modificou as ações para criar uma conta fictícia, confirmar o cadastro com HTTP 201 e validar `POST /rest/user/login` por meio de um controle positivo com HTTP 200. Só então foram executados os dois controles negativos.

Para a conta existente com senha errada e para o endereço inexistente com a mesma senha errada, a aplicação retornou HTTP 401, corpo de 26 bytes e o mesmo ETag. Não foi observada diferença que revelasse a existência da conta. Portanto, a hipótese de enumeração de usuários foi rejeitada para esse endpoint, parâmetros e versão do laboratório. O resultado não permite generalizar para outros fluxos de autenticação.

Os registros principais são `evidencias/investigacao-01/registro-80a1c220c6994810aa1779250e3222c7.jsonl` e `evidencias/investigacao-01/registro-119f0bf0a571414ba9a905360feb7df3.jsonl`.

### 4.2 Autorização de leitura de carrinhos

Foram criadas duas contas fictícias. Os controles próprios associaram o carrinho 6 à conta A e o carrinho 7 à conta B. A conta B inseriu o produto público de ID 1 em seu carrinho; a leitura autenticada de B retornou uma resposta JSON de 747 bytes.

Depois, uma nova sessão autenticada de A requisitou `GET /rest/basket/7`. A resposta retornou HTTP 200, 747 bytes e o mesmo ETag visto na consulta do próprio carrinho de B. Como a propriedade dos carrinhos e o item preparado haviam sido comprovados antes, a resposta demonstra leitura cruzada causada pela alteração do identificador.

A hipótese de leitura indevida foi sustentada para `GET /rest/basket/:id`. Não foram testadas alterações no carrinho de outra conta, outros métodos ou outros recursos. Os registros principais são `evidencias/investigacao-02/registro-a97c20578c8f4c4f97d08219e20d932f.jsonl` e `evidencias/investigacao-02/registro-7f02c9b0faf14e5995efe78d1317fa8c.jsonl`.

### 4.3 Exposição de arquivos internos

O primeiro scan TCP confirmou a disponibilidade da porta, mas não contribuía para a hipótese. A dupla registrou essa limitação e prosseguiu com `GET /robots.txt`. O arquivo apontou para `/ftp`; a consulta desse diretório retornou uma listagem HTML real, contendo nomes internos como `incident-support.kdbx`, `package.json.bak` e `suspicious_errors.yml`.

Foi feita uma única verificação adicional, sem autenticação, de `GET /ftp/incident-support.kdbx`. A aplicação retornou HTTP 200, tipo `application/octet-stream` e 3.246 bytes. Isso comprova que um arquivo interno identificado na listagem é entregue publicamente. O conteúdo binário não foi processado e não houve tentativa de extrair senhas ou credenciais.

Assim, a hipótese foi sustentada quanto à exposição de arquivo interno. A conclusão não afirma conhecimento do conteúdo lógico do arquivo KDBX. O registro é `evidencias/investigacao-03/registro-ab6d025aa74943e3b13197bcdd6a5b0a.jsonl`.

## 5. Análise crítica do agente

O modelo local contribuiu com propostas iniciais e recebeu os resultados anteriores, mas apresentou limitações relevantes. Ele sugeriu endpoints inexistentes, campos trocados, tokens placeholder, objetos JSON fora do esquema e interpretações que confundiam preparação com evidência. Em mais de uma ocasião, classificou incorretamente a hipótese como sustentada ou refutada antes de haver comparação suficiente.

A supervisão foi essencial. Na investigação 1, ela exigiu controle positivo e impediu que a consulta de perguntas de segurança fosse tratada como autenticação. Na investigação 2, ela estabeleceu a propriedade dos carrinhos antes da leitura cruzada, corrigiu a confusão entre A e B e impediu a exposição de token ao modelo. Na investigação 3, ela distinguiu `robots.txt` como pista de uma listagem de diretório e limitou a verificação do arquivo KDBX a metadados observáveis.

As correções no agente melhoraram a segurança e a auditabilidade da execução, mas não eliminam a necessidade de análise humana. Em particular, modificar os parâmetros de uma proposta não troca a ferramenta selecionada pelo modelo; isso ficou explícito na primeira etapa da investigação 3. Esse comportamento foi documentado, e a consulta HTTP foi proposta e aprovada separadamente.

## 6. Conclusão

O laboratório forneceu evidências reproduzíveis e delimitadas para as três hipóteses. Não houve indício observável de enumeração de contas no login testado. Em contraste, a leitura autenticada de um carrinho de B pela sessão de A demonstrou falha de autorização no endpoint de carrinho, e a entrega pública do arquivo `incident-support.kdbx` demonstrou exposição de recurso interno sem autenticação.

O resultado principal sobre IA é que o modelo local não substituiu a investigação técnica. Seus erros de formato, parâmetros e interpretação foram parte importante do experimento e ficaram registrados. A dupla, ao definir controles, autorizar cada ação e limitar as conclusões, tornou os resultados verificáveis e evitou que respostas plausíveis, porém incorretas, virassem evidência.

## Referências internas

- Enunciado: `AF - Tecnologias Hackers 26-2.pdf`.
- Planejamento original e revisão: `docs/plano-humano.md`, `docs/revisao-plano.md` e `docs/plano-revisado.md`.
- Ambiente e restauração: `docs/laboratorio.md` e `evidencias/sprint-1/`.
- Resumos e registros brutos: `evidencias/investigacao-01/`, `evidencias/investigacao-02/` e `evidencias/investigacao-03/`.
- Implementação e validações: `scripts/agente.py`, `scripts/lab.py`, `scripts/valida_agente.py` e `tests/test_agente.py`.

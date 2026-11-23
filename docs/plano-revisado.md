# Plano revisado — com apoio de IA

Revisão de 23/11/2026. O planejamento humano original permanece em `plano-humano.md`, no commit `5191db0`. Este documento é uma proposta técnica elaborada com apoio do assistente após a análise das primeiras execuções. Não constitui decisão humana já tomada nem registro retroativo de procedimentos realizados.

Antes de executar, a dupla registra em `revisao-plano.md` quais sugestões aceita, modifica ou rejeita. O agente continua escolhendo ações conforme o histórico, com supervisão humana em cada etapa. Os procedimentos abaixo orientam a supervisão e os controles; não são uma sequência automática imposta ao modelo.

## Preparação comum

- Confirmar o host atual e o alvo no `.env`. A rede `172.16.50.247` é histórica; não presumir que ainda corresponda ao laboratório.
- Executar `python3 scripts/lab.py check` e `python3 scripts/valida_agente.py` no host que executa os serviços. Guardar os resultados.
- Preservar os JSONL antigos: são evidências das limitações observadas.
- Para as novas sessões, restaurar o Juice Shop após guardar dados úteis e abrir sessão privada nova. Citar o JSON do reset no resumo. A restauração antes de cada investigação é a opção metodológica deste plano, não uma exigência literal do PDF.
- Usar apenas contas e dados fictícios do laboratório. Capturas devem limitar-se ao alvo e sua porta.
- Observar as requisições reais pelo navegador e informar as descobertas na avaliação humana do agente. Não inferir endpoints pelo nome da página.
- Se uma resposta retornar apenas o HTML da aplicação, distinguir carregamento da interface de resposta da API. Timeout torna aquela tentativa inconclusiva.

## Investigação 1

- **Aspecto da aplicação investigado:** Tratamento de login e exposição de informações.
- **Hipótese inicial:** As respostas da autenticação permitem distinguir uma conta existente de uma inexistente, quando a senha fornecida é inválida.
- **Relação com o original:** Recorte verificável da suspeita de exposição de informações no login; a presença da senha no corpo enviado ao servidor não demonstra vazamento.
- **Estratégia:** Criar uma conta fictícia conhecida; identificar a requisição real de login; comparar a resposta para essa conta com senha errada e para um endereço inexistente com senha errada. Usar login válido como controle de que o endpoint e o formato de envio estão corretos. Repetir os casos para verificar consistência.
- **Ferramentas:** `http_request` para comparar requisições/respostas; navegador/DevTools para identificar endpoint e confirmar comportamento.
- **Evidências:** Método, caminho, estrutura do corpo enviado, status e corpo das respostas, identificação dos controles e avaliações humanas.
- **Sustentada se:** As respostas distinguirem consistentemente os dois casos de falha por informação relacionada à existência da conta.
- **Rejeitada no recorte testado se:** O endpoint tiver sido validado e as respostas de falha não distinguirem os casos nos testes realizados.
- **Inconclusiva se:** Houver timeout, endpoint incorreto, retorno apenas de HTML, ou controles insuficientes. Não generalizar para todos os mecanismos de autenticação.

## Investigação 2

- **Aspecto da aplicação investigado:** Autorização de leitura de carrinhos.
- **Hipótese inicial:** Uma conta autenticada consegue ler o conteúdo do carrinho de outra conta alterando o identificador do recurso.
- **Estratégia:** Criar contas A e B e colocar produtos diferentes em seus carrinhos. Identificar o endpoint real, os IDs e as sessões. Comparar A acessando seu carrinho, B acessando o próprio, A solicitando o de B, e a solicitação sem autenticação. Usar tokens reais obtidos no laboratório, não o texto `<token>`.
- **Ferramentas:** `http_request` e navegador/DevTools para validar identidade e propriedade dos dados.
- **Evidências:** Requisições, respostas e produtos conhecidos que comprovem de quem é cada carrinho. Registrar preparação manual; não atribuí-la ao agente.
- **Sustentada se:** A resposta autenticada como A contiver dados comprovadamente pertencentes ao carrinho de B.
- **Rejeitada no recorte testado se:** O servidor impedir a leitura cruzada e os controles de acesso próprio funcionarem.
- **Inconclusiva se:** Token/ID não for válido, identidade não for comprovada, houver falha de rede ou só HTML. HTTP 200 isoladamente não comprova IDOR.
- **Limite:** Investigar leitura. Alteração de dados exigiria uma hipótese adicional e evidências próprias.

## Investigação 3

- **Aspecto da aplicação investigado:** Exposição de arquivos internos sem autenticação.
- **Hipótese inicial:** Caminhos descobertos durante o reconhecimento permitem obter arquivos internos ou dados sensíveis sem autenticação.
- **Estratégia:** Consultar `robots.txt` como ponto de partida; avaliar uma lista curta de caminhos justificados pelo conteúdo observado. Verificar o conteúdo efetivo de recursos acessíveis sem sessão. Comparar com um caminho inexistente para detectar retorno genérico da interface.
- **Ferramentas:** `http_request`; `tcp_scan` apenas na porta configurada do Juice Shop para diagnóstico de disponibilidade, se necessário.
- **Evidências:** Origem de cada caminho, resposta HTTP e trecho do conteúdo que caracterize dado interno. Considerar sensíveis credenciais, dados pessoais fictícios, backups e configurações internas; catálogo público e `robots.txt` isoladamente não contam.
- **Sustentada se:** Um recurso sem autenticação expuser conteúdo interno identificável, com evidência preservada.
- **Rejeitada no recorte testado se:** Os caminhos investigados não expuserem esse conteúdo e as requisições/controles forem válidos. Limitar a conclusão aos caminhos examinados.
- **Inconclusiva se:** Houver apenas erro de transporte, resultado genérico ou conteúdo insuficiente para classificação.

## Encerramento

Para cada investigação: concluir a sessão no agente; criar `resumo.md` na pasta correspondente; citar o nome do JSONL da sessão e as etapas relevantes; distinguir interpretação do modelo da conclusão humana. Se a IA errar, registrar a correção e observar se a próxima proposta incorpora a avaliação.

A revisão original foi feita por Claude externo. Isso deve ser declarado. Se a dupla também consultar Qwen para revisar este plano, salvar a resposta e as decisões como uma revisão posterior, sem substituir a versão original.

# Análise crítica das execuções registradas

Análise documental em 23/11/2026. Fonte: os três arquivos históricos `evidencias/investigacao-0N/registro.jsonl`. Nenhuma nova investigação foi executada para produzir este texto.

## Contribuições e limites observados

O agente integrou propostas de um modelo local a ferramentas HTTP e TCP, e registrou decisões de autorização/rejeição, resultados e interpretações. Esses registros permitem auditar erros e identificar mudanças no processo. A existência do ciclo funcional, entretanto, não demonstra que a investigação tenha sido tecnicamente suficiente.

Na investigação 1, a sessão inicial recebeu um objetivo placeholder e verificou as portas 80 e 443 do host, embora o serviço autorizado estivesse em 3000. A inferência de que não havia serviços ativos na rede excedeu a evidência de duas portas fechadas. A sessão seguinte fez GET e POST em `/login`, recebendo HTML com o mesmo tamanho. Isso não comprova que o mecanismo de autenticação tenha sido exercitado. A conclusão humana registrada como hipótese refutada não é sustentada por esses testes; a reavaliação documental é inconclusiva.

Na investigação 2, o modelo propôs `/cart` e `/user`, incluindo um cabeçalho literal `Bearer <token>`. As respostas retornaram o HTML da aplicação, sem evidência de identidade autenticada, carrinhos distintos ou propriedade dos itens. O modelo classificou o site como seguro, mas a avaliação humana do passo 3 reconheceu que os dados eram insuficientes. Esse é um exemplo concreto de intervenção humana útil: a dupla não aceitou a generalização da IA naquele passo. A sessão terminou sem conclusão preenchida.

Na investigação 3, a dupla rejeitou a consulta à raiz por considerá-la pouco útil à hipótese. A consulta seguinte a `/users` falhou por timeout. A interpretação marcou `hypothesis: refuta`, apesar de não haver resposta da aplicação. O erro foi identificado ao confrontar a interpretação com o evento `erro_ferramenta`. Uma falha de transporte não distingue um recurso protegido de um recurso vulnerável. A reavaliação é inconclusiva. Não há correção humana registrada naquela sessão; o tratamento posterior é documentar a limitação e repetir a investigação com disponibilidade e controles validados.

## Comparação com a estratégia humana

| Tema | Plano humano original | Comportamento registrado | Avaliação |
| --- | --- | --- | --- |
| Login | Inspecionar credenciais no tráfego | GET/POST em `/login` e interpretação do HTML | Tanto o critério original quanto o teste precisaram de refinamento; senha no corpo da requisição não basta para demonstrar vazamento |
| Carrinho | Alterar ID e observar itens | Consultas genéricas, sem token válido ou comparação entre contas | O agente não realizou a comparação que sustentaria a hipótese |
| Dados sensíveis | Examinar `robots.txt` e caminhos | Raiz rejeitada, `/users` com timeout | A proposta não seguiu a pista humana nem produziu evidência sobre exposição |

## Limitações da integração e correções posteriores

A análise do código mostrou que o histórico usado para propor a próxima ação continha parâmetros e uma interpretação curta, mas omitia a resposta da ferramenta e a avaliação humana. Portanto, atribuir a dificuldade exclusivamente ao tamanho do Qwen seria injustificado. A integração também fornecia exemplos com placeholders, permitia justificativas vazias e misturava sessões no mesmo arquivo.

Na revisão de 23/11, foram implementados: histórico com prévia da evidência e avaliação humana; bloqueio de token placeholder; justificativas e conclusão obrigatórias; arquivo e identificador próprios por sessão; restrição TCP à porta autorizada; correção da codificação de formulários; e validação que não marca JSON inválido como sucesso. O prompt de interpretação agora explicita que erro de transporte e HTML genérico não refutam hipóteses. Essas mudanças passaram em testes offline, mas sua eficácia com o modelo real depende de nova execução. A classificação equivocada do modelo continua sendo preservada no registro, sem reescrita automática de sua resposta.

Há ainda limites: apenas uma prévia do resultado é enviada ao modelo, o contexto é finito e as ferramentas cobrem somente um conjunto delimitado de ações. O corpo HTTP é limitado a 200 KB, sinalizando truncamento. A dupla precisa conferir a evidência completa disponível, corrigir conclusões e decidir quando testar novamente. Não foi demonstrada superioridade da IA; o resultado mais bem sustentado até aqui é a necessidade de supervisão técnica ativa.

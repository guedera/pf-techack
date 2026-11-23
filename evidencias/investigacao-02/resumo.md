# Investigação 2 — autorização de carrinhos

Reavaliação documental em 23/11/2026; fonte: `registro.jsonl`, sessão iniciada em 19/11 às 13:12 UTC. Não houve nova execução.

## 1. Hipótese inicial

Um usuário poderia acessar o carrinho de outro alterando seu identificador.

## 2. Estratégia proposta pelo grupo

Alterar o ID armazenado no cliente e observar os itens. Para concluir sobre autorização, é necessário comprovar a identidade da sessão, a propriedade dos carrinhos e a resposta do servidor.

## 3. Contribuição do agente

Propôs consultas a `/cart` e `/user`, incluindo literalmente `Authorization: Bearer <token>` e repetindo ações semelhantes.

## 4. Execução

Os passos 1, 3 e 4 produziram HTML de 9.984 bytes, com status 200. Não há comparação de duas contas/carrinhos nem token válido demonstrado. Não há estado inicial ou reset específico citado na sessão.

## 5. Intervenção humana

O passo 2 foi rejeitado com justificativa sem conteúdo técnico. No passo 3, a dupla registrou que o resultado era insuficiente para provar ausência da falha, contrapondo-se à interpretação do modelo de que o site seria seguro. A sessão foi encerrada no passo 5.

## 6. Conclusão

**Inconclusiva.** A conclusão histórica está vazia; esta é uma análise posterior, não uma decisão registrada durante a execução. O HTML retornado não prova acesso ao conteúdo de carrinhos. Repetir com contas, tokens, IDs e controles reais do laboratório.

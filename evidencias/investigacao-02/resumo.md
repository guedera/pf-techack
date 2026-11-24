# Investigação 2 — autorização de leitura de carrinhos

## 1. Hipótese

Uma conta autenticada conseguiria ler o carrinho de outra ao alterar o identificador do recurso.

## 2. Sessões e preparação controlada

Os registros históricos em `registro.jsonl` são preservados, mas não demonstravam identidade, propriedade ou resposta útil da API. A evidência válida está nas sessões `registro-720fcb4ce8e9496f82d185a191a8d1ce.jsonl`, `registro-a97c20578c8f4c4f97d08219e20d932f.jsonl` e `registro-7f02c9b0faf14e5995efe78d1317fa8c.jsonl`.

A dupla criou duas contas fictícias, A e B, e autenticou ambas pelo endpoint validado `POST /rest/user/login`. Os logins capturaram internamente token e ID de carrinho, sem registrar o token no resumo. Os controles próprios confirmaram o carrinho 6 para A e o carrinho 7 para B. O produto público de ID 1 foi inserido, sob a sessão de B, no carrinho 7; uma consulta posterior de B retornou 747 bytes, confirmando o item preparado.

## 3. Teste cruzado

Com uma sessão nova de A, a dupla requisitou `GET /rest/basket/7` usando somente a referência interna ao token de A. A resposta foi HTTP 200, JSON de 747 bytes e ETag `W/"2eb-auV7F46/alYsyWxF5c5nzCb+XX0"`, idênticos aos observados quando B leu o próprio carrinho 7 com o produto conhecido.

## 4. Intervenções e limitações do agente

O modelo propôs endpoints, cabeçalhos e formatos incorretos, além de confundir A e B nas interpretações. A dupla modificou os parâmetros antes das execuções, rejeitou repetição inútil e registrou o motivo. Para evitar cópia ou exposição de JWT no prompt, o agente passou a resolver internamente as referências aprovadas `$last_token` e `$last_basket_id` somente no instante da execução.

## 5. Conclusão

**Hipótese sustentada no recorte testado.** A sessão de A recebeu o conteúdo do carrinho 7, comprovadamente pertencente a B, após a alteração do identificador no caminho. A conclusão cobre apenas leitura no endpoint `GET /rest/basket/:id`, com as contas e dados fictícios do laboratório; nenhuma alteração de carrinho alheio foi investigada.

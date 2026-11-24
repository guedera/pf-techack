# Investigação 3 — exposição de arquivos internos

## 1. Hipótese

Caminhos descobertos durante o reconhecimento poderiam entregar arquivos internos ou dados sensíveis sem autenticação.

## 2. Sessão e encadeamento das evidências

Os registros históricos em `registro.jsonl` permanecem como referência das limitações anteriores. A investigação válida está em `registro-ab6d025aa74943e3b13197bcdd6a5b0a.jsonl`.

O primeiro passo proposto foi um TCP scan. A modificação de parâmetros não troca a ferramenta, portanto apenas confirmou que a porta 3000 estava aberta; a dupla registrou que isso não examinava `robots.txt`. Na etapa seguinte, `GET /robots.txt` sem autenticação retornou HTTP 200 e indicou `/ftp` como pista. Em seguida, `GET /ftp/` retornou uma listagem HTML real de 11.265 bytes, incluindo `incident-support.kdbx`, `package.json.bak` e `suspicious_errors.yml`.

## 3. Verificação do recurso sensível

A dupla selecionou somente `GET /ftp/incident-support.kdbx`, por ser um arquivo interno identificado na listagem. Sem autenticação, a resposta foi HTTP 200, `application/octet-stream` e 3.246 bytes. O conteúdo binário não foi processado e não houve tentativa de extrair credenciais.

## 4. Intervenções e limitações do agente

O modelo adicionou indevidamente uma referência de token a uma consulta que deveria ser anônima e interpretou a resposta como inconclusiva. A dupla removeu o cabeçalho, delimitou a análise a status, tipo e tamanho e corrigiu a conclusão com base na resposta preservada.

## 5. Conclusão

**Hipótese sustentada no recorte testado.** O diretório público e o recurso `incident-support.kdbx` foram entregues sem autenticação, o que comprova exposição de arquivo interno potencialmente sensível. A conclusão não afirma acesso ao conteúdo lógico do banco KDBX nem extração de credenciais; limita-se à exposição pública observada no estado atual do laboratório.

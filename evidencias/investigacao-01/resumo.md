# Investigação 1 — tratamento do login

## 1. Hipótese

As respostas de autenticação poderiam distinguir uma conta existente de uma inexistente quando ambas recebessem senha inválida.

## 2. Sessões e controles

As sessões históricas em `registro.jsonl` são preservadas como evidência das limitações iniciais: consultaram a SPA em `/login` e não validaram a API de autenticação. A investigação válida foi composta pelas sessões `registro-80a1c220c6994810aa1779250e3222c7.jsonl` e `registro-119f0bf0a571414ba9a905360feb7df3.jsonl`.

Na primeira, a dupla corrigiu propostas incorretas do modelo, obteve uma pergunta de segurança, criou uma conta fictícia e confirmou o controle positivo: `POST /api/Users` retornou HTTP 201 e o login válido em `POST /rest/user/login` retornou HTTP 200. Assim, endpoint, método e formato do corpo ficaram comprovados antes dos testes negativos.

## 3. Execução

Na sessão final, foram comparados dois `POST /rest/user/login` com a mesma senha inválida:

| Caso | Status | Corpo | ETag |
| --- | ---: | ---: | --- |
| Conta fictícia existente | 401 | 26 bytes | `W/"1a-ARJvVK+smzAF3QQve2mDSG+3Eus"` |
| Endereço fictício inexistente | 401 | 26 bytes | `W/"1a-ARJvVK+smzAF3QQve2mDSG+3Eus"` |

## 4. Intervenções e limitações do agente

O Qwen3 1.7B inicialmente propôs rotas, campos e tokens fictícios. A dupla rejeitou ou modificou essas ações, exigiu o controle positivo e corrigiu interpretações que tratavam preparação como evidência de autenticação. Houve também propostas JSON incompletas; elas foram registradas e não executadas.

## 5. Conclusão

**Hipótese rejeitada no recorte testado.** As duas falhas de login tiveram a mesma assinatura observável, sem diferença que permitisse enumerar a existência da conta. A conclusão limita-se ao endpoint `POST /rest/user/login`, aos parâmetros usados e ao estado atual do laboratório.

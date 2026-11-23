# Testes de segurança com agente de IA supervisionado

**Luiz Miguel e Guilherme Guedes — Tecnologias Hackers**

**Versão de trabalho, 23/11/2026.** Este texto descreve as evidências existentes. A conclusão das novas sessões, a revisão da dupla e a conferência de 4–6 páginas no documento renderizado são necessárias antes da entrega.

## 1. Objetivo e escopo

O projeto investiga a contribuição de um modelo de linguagem local para testes de segurança no OWASP Juice Shop. O agente seleciona ferramentas e propõe ações; os integrantes avaliam cada proposta e permanecem responsáveis por sua execução e pela interpretação técnica dos resultados. O objetivo é avaliar a qualidade do processo investigativo, incluindo erros, limitações e intervenções humanas.

O ambiente documentado inicialmente utiliza máquinas pessoais, conforme alternativa informada pelo grupo. Essa adaptação substitui o kit mencionado no enunciado. O único alvo de testes é a instância local do Juice Shop; o serviço de inferência e os demais serviços do host não fazem parte do escopo ofensivo.

## 2. Arquitetura e reprodução

Na preparação registrada em 17/11, o MacBook Air M1 com 8 GB de Luiz hospedou Juice Shop e Ollama em Docker. A VM Kali da dupla acessou a aplicação na LAN do laboratório, pelo endereço `172.16.50.247:3000`. A API do Ollama ficou publicada apenas em loopback, na porta 11434. O endereço é uma referência histórica e precisa ser atualizado ao reproduzir o ambiente em outra rede.

O modelo inicial foi Qwen3 1.7B, quantizado em Q4_K_M, executado localmente. As imagens dos serviços foram fixadas por digest em `compose.lock.json`. O script `scripts/lab.py` inicializa os serviços, verifica HTTP e inferência, coleta inventário e registra resultados em JSON. O Juice Shop não usa volume persistente: sua recriação permite restaurar o estado, enquanto os pesos do modelo permanecem em volume separado.

Os registros de 17/11 comprovam inicialização e restauração bem-sucedidas. A restauração verificou alteração do ID do contêiner, manutenção da imagem, remoção de um marcador e zero desafios resolvidos na API. O registro `20261117T141308210590Z-reset.json` sustenta essa conclusão. Os dados do navegador exigem tratamento separado, como uso de uma nova sessão privada.

O agente foi desenvolvido em Python com biblioteca padrão e integra duas ferramentas: requisição HTTP ao alvo e conexão TCP. As ações exigem autorização humana; a dupla pode modificar parâmetros, rejeitar ou encerrar. Os resultados são enviados ao modelo para interpretação e orientação da proposta seguinte. O programa registra propostas, parâmetros, decisões, execuções, interpretações e conclusões em JSONL.

## 3. Planejamento

O planejamento humano original foi preservado no commit `5191db0` e abordou login, controle de acesso a carrinhos e exposição de informações. A revisão externa registrada em `docs/revisao-plano.md` foi feita por Claude, distinguindo-se do modelo local usado pelo agente. Sua tabela de decisões humanas ainda precisa ser concluída pela dupla.

A análise posterior identificou necessidade de delimitar melhor as hipóteses. Credenciais presentes no corpo enviado ao login não demonstram, isoladamente, vazamento. Alterar o ID no navegador só constitui evidência de falha de autorização se o servidor devolver dados de outra conta. A presença de caminhos em `robots.txt` é uma pista, mas sua publicidade não demonstra exposição indevida.

O plano revisado propõe controles e critérios explícitos: comparar respostas de autenticação para contas existentes e inexistentes; verificar leitura cruzada entre dois carrinhos de propriedade conhecida; e examinar conteúdo de recursos descobertos sem autenticação. A autoria assistida dessa revisão está declarada, mantendo intacta a estratégia original.

## 4. Resultados das sessões históricas

| Investigação | Evidência obtida | Conclusão da reavaliação |
| --- | --- | --- |
| Login | Scan de 80/443; GET/POST em `/login` com HTML de 9.984 bytes | Inconclusiva: não foi demonstrado teste válido da autenticação |
| Carrinho | GET em `/cart` e `/user`, incluindo token placeholder; retorno HTML | Inconclusiva: não houve comprovação de acesso a carrinho alheio |
| Dados sensíveis | Raiz rejeitada; `/users` com timeout | Inconclusiva: nenhuma resposta permite avaliar o conteúdo |

Na investigação 1, o arquivo contém duas sessões. A primeira começou com objetivo placeholder; a segunda terminou com conclusão humana de hipótese refutada. Essa conclusão excede as evidências, pois o HTML recebido não demonstra operação do login nem comparação adequada de respostas. A análise posterior preserva o registro e explicita a divergência.

Na investigação 2, o modelo sugeriu credencial literal `<token>` e não estabeleceu identidades ou carrinhos de referência. A dupla reconheceu no passo 3 que o resultado era insuficiente para provar ausência de falha. Essa intervenção é relevante porque contrasta com a classificação de segurança apresentada pelo modelo. A conclusão final da sessão ficou vazia.

Na investigação 3, a ferramenta falhou por timeout, mas o modelo marcou a hipótese como refutada. Não houve resposta da aplicação nem avaliação humana final preenchida. A classificação posterior é inconclusiva. Os detalhes, datas e referências às etapas estão nos `resumo.md` das respectivas pastas de evidências.

## 5. Análise crítica e correções

Os registros demonstram propostas repetitivas, uso de parâmetros fictícios e generalizações sem evidência. O caso mais direto é a interpretação do timeout como refutação: o erro foi identificado ao comparar a interpretação com o evento de falha da ferramenta. Ausência de resposta não permite distinguir um recurso protegido de um recurso vulnerável.

A qualidade da integração também influenciou o desempenho. O código anterior enviava à próxima etapa apenas um resumo da interpretação, omitindo respostas das ferramentas e avaliações humanas. Assim, não é possível atribuir os problemas exclusivamente ao tamanho do modelo. A correção implementada inclui evidência e avaliação humana no histórico, além de reforçar a cautela sobre HTML genérico e falhas de transporte no prompt.

Outras correções bloqueiam tokens placeholder e cabeçalhos de transporte indevidos, restringem o TCP à porta do Juice Shop, corrigem formulários URL-encoded, exigem justificativas e separam arquivos por sessão. A validação foi ajustada para reprovar propostas, parâmetros ou interpretações inválidos. Vinte e nove testes offline passaram; eles comprovam comportamentos locais e regressões específicas, não a qualidade do novo comportamento do modelo em uma investigação real.

Em 23/11, Guilherme reproduziu o laboratório no Mac. O registro de inicialização confirma Docker 29.9.3, imagens fixadas, Juice Shop 20.4.0-SNAPSHOT em ARM64 e Qwen3 1.7B Q4_K_M. O registro de validação confirmou acesso HTTP ao alvo, porta 3000 aberta, bloqueio de destinos externos e comunicação com o modelo. A primeira execução também revelou que a checagem aceitava os parâmetros apenas estruturalmente: o modelo repetiu `Bearer <token>`. O executor bloquearia esse valor, mas o validador registrou sucesso. A validação foi então endurecida para verificar os parâmetros sem executar rede, mostrando novamente como uma saída formalmente válida pode continuar tecnicamente inadequada.

As limitações remanescentes incluem contexto finito, envio de prévias em vez de todo o resultado e conjunto restrito de ferramentas. O corpo HTTP é limitado a 200 KB e sinaliza truncamento. A supervisão deve conferir os registros e delimitar as conclusões ao que foi efetivamente testado. A análise detalhada encontra-se em `docs/analise-critica.md`.

## 6. Conclusão provisória

O projeto dispõe de laboratório reproduzível, agente supervisionado e registros que permitem identificar erros concretos da IA e insuficiências na condução dos testes. As sessões históricas não permitem confirmar ou refutar adequadamente as três hipóteses. Seu valor principal é evidenciar por que a supervisão técnica e a validação dos parâmetros são necessárias.

Para consolidar os resultados experimentais, as novas sessões devem aplicar os controles definidos no plano revisado e documentar as intervenções reais da dupla. A infraestrutura corrigida foi exercitada com o modelo local, mas sua eficácia investigativa depende dessas três sessões. Não foi demonstrada superioridade da IA sobre a estratégia humana.

## Fontes do projeto

- Enunciado: `AF - Tecnologias Hackers 26-2.pdf`.
- Laboratório e restauração: `docs/laboratorio.md` e `evidencias/sprint-1/`.
- Estratégia original e revisão: `docs/plano-humano.md`, `docs/revisao-plano.md` e `docs/plano-revisado.md`.
- Registros brutos: `evidencias/investigacao-01/registro.jsonl`, `evidencias/investigacao-02/registro.jsonl` e `evidencias/investigacao-03/registro.jsonl`.
- Implementação: `scripts/agente.py`, `scripts/lab.py` e `scripts/valida_agente.py`.

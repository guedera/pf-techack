# Revisão do planejamento pela IA

- **Plano revisado:** `docs/plano-humano.md`, commit `5191db0` (18/11/2026, 20h59, UTC−3).
- **Revisor:** Claude (Anthropic), pelo aplicativo Claude, em 18/11/2026. **Não** é o LLM
  local do laboratório (`qwen3:1.7b`); ver nota no fim.
- **Regra:** o plano original não é alterado. As sugestões abaixo são propostas; a dupla
  decide cada uma na tabela final, com justificativa técnica. Uma sugestão da IA não é
  evidência de vulnerabilidade.

## Sugestões gerais

**G1 — Registrar a análise inicial que de fato foi feita.** "Nenhuma anomalia identificada"
não mostra o que foi examinado. Listar as ações (páginas visitadas, ferramentas abertas,
contas criadas), com data e evidência. Do jeito atual, as três hipóteses parecem vir de
conhecimento prévio sobre aplicações web, e não da análise; se for o caso, declarar isso
no relatório é melhor do que deixar implícito.

**G2 — Definir antes do teste o que refuta cada hipótese.** O roteiro aceita hipótese
rejeitada como resultado, mas, para isso, o critério de rejeição precisa existir antes da
execução. Sem ele, há risco de viés de confirmação (interpretar qualquer resultado como
apoio). Sugestão: para cada investigação, uma linha "sustentada se…", outra "rejeitada
se…" e uma "inconclusiva se…".

**G3 — Separar procedimento de evidência.** Nas investigações 2 e 3, o campo de evidências
descreve *o que fazer*, não *o que precisa ser observado e guardado*. A evidência é o
artefato final: a requisição e a resposta salvas, com data, que outra pessoa consegue
conferir.

**G4 — Compatibilizar as ferramentas com o agente.** O roteiro exige um agente com pelo
menos duas ferramentas integradas, uma delas interagindo diretamente com o Juice Shop.
DevTools, Burp Suite e Wireshark são interfaces gráficas, difíceis de entregar a um modelo.
Indicar, em cada investigação, quais observações poderiam ser feitas por uma ferramenta
de requisições HTTP delimitada (que o agente usaria) e quais ficam para validação humana
nas ferramentas gráficas. Isso também prepara a comparação "estratégia humana × agente"
da análise crítica.

**G5 — Restringir capturas e testes ao alvo.** Todos os testes ficam em
`172.16.50.247:3000`. Se o Wireshark for usado na LAN WannaCry, aplicar filtro de captura
para esse host e porta, evitando registrar tráfego de outros grupos.

**G6 — Estado e local das evidências.** Rodar `scripts/lab.py reset --confirm` antes de cada
investigação (e usar sessão privada nova no navegador), citando o JSON gerado. Guardar
tudo em `evidencias/investigacao-0N/`.

**G7 — Cobertura dos eixos sugeridos.** As investigações 1 e 2 caem no eixo
autenticação/autorização e a 3 em reconhecimento/acesso a recursos. Nenhuma trata
diretamente de tratamento de entradas. O roteiro só sugere os eixos, então isso é
aceitável, mas vale justificar a escolha no relatório.

## Investigação 1 — tratamento do login

**I1.1 — A evidência proposta não distingue falha de funcionamento normal.** Toda tela de
login precisa enviar e-mail e senha ao servidor no corpo da requisição; ver as credenciais
no payload do POST acontece em qualquer aplicação, segura ou não. Do jeito que está, a
hipótese seria "confirmada" mesmo sem haver vazamento. Definir o que seria um vazamento,
por exemplo: credenciais em lugares onde não deveriam estar (URL ou parâmetros de consulta,
que ficam em histórico e logs), dados que voltam na *resposta* além do necessário, ou
mensagens de erro diferentes para usuário inexistente e senha errada (revelando quais
contas existem).

**I1.2 — Reescrever a hipótese de forma verificável.** "Não faz o handler adequado" é vago.
Formato sugerido: "Suspeitamos que [o login] [expõe X] em [Y], o que verificaremos
observando [Z]".

**I1.3 — Transporte HTTP é condição do laboratório.** O Juice Shop está servido em HTTP
sem TLS por construção do ambiente. Se a hipótese for sobre credenciais em texto claro na
rede, isso precisa aparecer como limitação, para não ser apresentado como falha da
aplicação.

**I1.4 — Ferramentas.** Se a pergunta for sobre o conteúdo da requisição e da resposta,
DevTools ou Burp bastam; o Wireshark só acrescenta algo se a pergunta for sobre o
transporte. Escolher uma ferramenta principal e justificar.

## Investigação 2 — acesso ao carrinho de outro usuário

**I2.1 — Hipótese boa e verificável.** É um caso clássico de controle de acesso quebrado
(referência direta a objeto sem verificação de autorização), coerente com a disciplina.

**I2.2 — A conclusão é sobre o servidor, não sobre o navegador.** Mudar um valor no
armazenamento local só altera o que o cliente *pede*. A falha existe se o *servidor*
entregar dados de um carrinho que não pertence ao usuário autenticado. A evidência
deve ser a resposta da API, não apenas a mudança na tela.

**I2.3 — Usar duas contas criadas pela dupla.** Com contas A e B próprias, e itens
conhecidos em cada carrinho, a propriedade dos dados é comprovável. Assim a evidência
mostra "a conta A recebeu os itens que a dupla colocou no carrinho de B".

**I2.4 — Incluir controles.** Comparar com a mesma requisição para o próprio carrinho
(resultado esperado) e sem autenticação. Se o servidor recusar o acesso ao carrinho
alheio, a hipótese está rejeitada, e esse também é um resultado válido.

**I2.5 — Extensão opcional.** Leitura e alteração são perguntas diferentes. Se quiserem,
uma segunda hipótese pode tratar de modificação do carrinho alheio; manter separado para
não misturar conclusões.

## Investigação 3 — exposição de dados sensíveis

**I3.1 — Hipótese ampla demais.** "Informações importantes e credenciais por algum acesso
indevido" não tem como ser refutada. Delimitar que tipo de dado e por qual caminho:
por exemplo, "arquivos ou recursos acessíveis sem autenticação contêm [tipo de dado]".

**I3.2 — Definir "sensível" antes do teste.** Ter uma lista do que contaria (credenciais,
dados pessoais, configuração interna, backups) evita classificar qualquer arquivo
encontrado como vazamento.

**I3.3 — `robots.txt` é ponto de partida, não evidência.** Esse arquivo é público por
definição; listar caminhos não é uma falha. A evidência seria um caminho que entregue
conteúdo sensível sem autenticação. Registrar também os caminhos que *não* entregaram
nada, para mostrar o que foi descartado.

**I3.4 — Ferramentas e limites.** A parte de reconhecimento pode ser feita por uma
ferramenta de requisições HTTP com uma lista curta e justificada de caminhos, sem
varredura extensa. Isso se encaixa no agente (G4) e mantém o volume de requisições
controlado.

## Decisões da dupla

**Atualização em 23/11/2026:** as sugestões técnicas foram incorporadas à proposta
`plano-revisado.md`, produzida com apoio de IA. A tabela abaixo permanece destinada
às decisões efetivas da dupla: incorporar uma sugestão à proposta não equivale a
registrar que os integrantes a aceitaram ou que já a executaram. Preencher antes
das novas sessões e registrar a data real da decisão, sem retroagir ao plano original.

Preencher para cada sugestão: **aceita**, **modificada** ou **rejeitada**, com justificativa
técnica. O plano que guiará os testes deve ser registrado em seguida, sem apagar o original.

**Decisão registrada em 23/11/2026 por Guilherme Guedes:** aceita as três revisões de
investigação e o `plano-revisado.md` na íntegra. Portanto, as sugestões abaixo ficam
aceitas conforme as justificativas técnicas já descritas em cada item; sua eficácia será
avaliada nas novas sessões, sem alterar o planejamento humano original.

| ID | Decisão | Justificativa técnica |
| --- | --- | --- |
| G1 | Aceita | Delimitar hipóteses torna a evidência verificável. |
| G2 | Aceita | Controles permitem distinguir falha de teste de resultado válido. |
| G3 | Aceita | Critérios prévios evitam conclusões além das evidências. |
| G4 | Aceita | Ações dinâmicas permanecem sob autorização humana. |
| G5 | Aceita | Evidência bruta e avaliação humana permitem auditoria. |
| G6 | Aceita | Estado inicial conhecido melhora a comparação entre sessões. |
| G7 | Aceita | Falhas e incertezas devem resultar em conclusão inconclusiva. |
| I1.1 | Aceita | A hipótese passa a comparar respostas observáveis do login. |
| I1.2 | Aceita | O endpoint real será confirmado antes da conclusão. |
| I1.3 | Aceita | Conta conhecida, inexistente e login válido funcionam como controles. |
| I1.4 | Aceita | Status e corpo sustentam a comparação de respostas. |
| I2.1 | Aceita | Leitura cruzada é uma hipótese de autorização objetiva. |
| I2.2 | Aceita | Tokens e IDs reais evitam parâmetros fictícios. |
| I2.3 | Aceita | Itens diferentes comprovam a propriedade de cada carrinho. |
| I2.4 | Aceita | Acesso próprio e sem sessão são controles necessários. |
| I2.5 | Aceita | O teste fica limitado à leitura, sem misturar alteração. |
| I3.1 | Aceita | O recorte limita a hipótese a recursos sem autenticação. |
| I3.2 | Aceita | A definição prévia evita classificar conteúdo público como sensível. |
| I3.3 | Aceita | `robots.txt` será tratado como pista, não como vulnerabilidade. |
| I3.4 | Aceita | A lista curta mantém o reconhecimento controlado e reproduzível. |

## Nota sobre o revisor

O roteiro diz que "o modelo" poderá revisar o planejamento. Esta revisão foi feita por um
modelo externo (Claude), não pelo LLM local. Declarar isso no relatório. Se a dupla quiser,
pode também submeter o plano ao `qwen3:1.7b` e comparar as duas revisões; a diferença de
qualidade entre elas é material útil para a análise crítica da seção 6.

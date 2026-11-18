# Registro de preparação — Sprint 1

Data: 17/11/2026. Estado: **critério funcional da Sprint 1 atendido; organização das evidências e inventário pendentes**.

## Decisões

- Ambiente em máquinas pessoais, conforme alternativa informada pelo usuário.
- Docker Desktop no MacBook Air M1/8 GB de Luiz hospeda Juice Shop e Ollama.
- VM Kali na máquina do outro integrante; mesma LAN WannaCry, isolada no laboratório
  conforme informado pelo usuário.
- Publicação inicialmente validada em loopback. `.env` ajustado para a LAN WannaCry,
  `172.16.50.247:3000`; HTTP validado no Mac e pelo script no Kali, conforme evidências abaixo.
- Modelo inicial Qwen3 1.7B quantizado para avaliar viabilidade com 8 GB.
- Agente planejado para o Mac, com implementação na Sprint 3.

## Preparado

- `compose.yaml`, `.env.example` e imagem de ferramentas curl/Nmap/Python.
- Script para inicialização, consulta ao modelo, inventário, verificação pelo Kali
  e restauração do Juice Shop com registro em JSON.
- Fixação das imagens baixadas por digest na primeira inicialização.
- Instruções de reprodução, conexão da dupla e registro da adaptação no relatório.

## Verificações e impedimentos

- Docker CLI 29.4.3 e Compose v5.1.3 identificados no host.
- Configuração Compose validada sem acesso ao Engine.
- Nove testes offline passaram: limites de endereço, bloqueio de redirecionamentos,
  rejeição de resposta incompleta do modelo, confirmação de descarte, checagem de
  restauração e registro de falhas. As chamadas aos serviços nesses testes são
  simuladas; não comprovam funcionamento dos contêineres.
- Também foram validados a publicação inicial em loopback, a ausência de volume
  no Juice Shop, o modelo padrão, a troca de IP/porta para LAN e o carregamento de
  um lock JSON pelo Compose, sem iniciar serviços.
- `.env` local preparado a partir do exemplo; ignorado pelo Git.
- O acesso da sessão ao socket do Docker retornou `permission denied`.
  Não foi possível consultar o Engine, baixar imagens, criar contêineres ou testar
  a API real. Isso não permite concluir que o Docker do usuário esteja parado.
- A validação real foi executada no terminal do usuário com o Docker Desktop ativo;
  os registros de sucesso foram conferidos nesta sessão, conforme seção abaixo.
- Não houve execução de investigações de segurança nem formulação do plano humano.

## Pendências para concluir

- [x] Executar `python3 scripts/lab.py up` no terminal do Mac (primeira tentativa com falha).
- [x] Conferir o primeiro JSON, o lock e a confirmação de acesso pelo navegador.
- [x] Reexecutar `up` após corrigir o caminho do Node e obter um registro de sucesso.
- [x] Executar `python3 scripts/lab.py reset --confirm` e confirmar a restauração do servidor.
- [ ] Limpar os dados do site ou usar uma nova sessão privada antes dos próximos testes.
- [x] Definir LAN ou VPN e registrar IP/porta do alvo autorizado: LAN WannaCry, `172.16.50.247:3000`.
- [x] Aplicar o novo vínculo de porta no Docker e verificar HTTP pelo IP da LAN.
- [x] Executar `kali-check` na VM: captura enviada pelo usuário mostra HTTP 200 e sucesso.
- [x] Confirmar a interface no Firefox do Kali: usuário informou acesso após desativar o proxy.
- [x] Adicionar o print original do JSON do Kali em `evidencias/sprint-1/kali-check-json.png`.
- [ ] Copiar o JSON original do Kali e uma captura da aplicação aberta para o repositório.
- [ ] Completar inventário da máquina da dupla, versão do Kali e integrantes.
- [x] Atualizar as tarefas em `sprints.md` com base nos registros locais e na confirmação do usuário; manter pendências de documentação abertas.

## Primeira execução no terminal do usuário

Registro: `evidencias/sprint-1/20261117T140326841338Z-up.json`, iniciado às 10h53
e encerrado às 11h03, horário de São Paulo. O registro tem `success: false`:
Docker Engine 29.4.3 respondeu; as duas imagens foram baixadas e fixadas em
`compose.lock.json`; `compose up --wait` retornou código 1. O usuário confirmou
que o Juice Shop está acessível no navegador do Mac.

Os metadados da imagem Juice Shop mostram o executável `/nodejs/bin/node` fora
do PATH. O healthcheck usava `node`, incompatível com essa imagem. Corrigidos o
healthcheck e os comandos de inventário/restauração para o caminho absoluto.
O erro do healthcheck em execução ainda não foi consultado diretamente, pois a
sessão de preparação não tem acesso ao socket Docker.

Essa tentativa parou antes de `ollama pull qwen3:1.7b`, da construção das
ferramentas e da consulta ao modelo; portanto, baixar a imagem Ollama não comprova
que os pesos do Qwen foram baixados. Essas verificações foram concluídas na reexecução abaixo.
Este problema é de preparação da infraestrutura; não é uma evidência de erro do
agente supervisionado, que ainda não foi implementado.

## Reexecução e restauração verificadas

- `evidencias/sprint-1/20261117T141229823136Z-up.json`: `success: true`,
  finalizado às 11h12 de São Paulo. Juice Shop acessível por HTTP no Mac e pelo
  contêiner auxiliar; modelo disponível e resposta local não vazia com `done: true`;
  inventário de serviços e ferramentas concluído.
- `evidencias/sprint-1/20261117T141308210590Z-reset.json`: `success: true`,
  finalizado às 11h13 de São Paulo. O ID do contêiner mudou, a imagem foi mantida,
  o marcador foi removido e a API confirmou zero desafios resolvidos.
- Modelo `qwen3:1.7b`, Q4_K_M; a consulta levou 29,857 s, dos quais cerca de
  20,502 s corresponderam ao carregamento. É uma medida de uma consulta inicial,
  não um benchmark nem validação da qualidade das futuras investigações.
- Versões observadas: Juice Shop `20.4.0-SNAPSHOT`, Ollama `0.40.16`,
  curl `7.88.1`, Nmap `7.93` e Python do contêiner auxiliar `3.11.2`.
  A imagem Juice Shop permanece fixada pelo digest do lock, apesar do nome SNAPSHOT.
- O endereço validado nesses registros é `http://127.0.0.1:3000`, apenas no Mac.
  A conexão da VM Kali foi validada posteriormente na LAN, conforme seção abaixo.

## Preparação do acesso pela LAN

Em 17/11/2026 o grupo mudou da rede comum da faculdade para a rede do laboratório
WannaCry, informada como isolada pelo usuário. Na nova conexão a interface `en0`
foi observada ativa com IPv4 `172.16.50.247` e máscara `255.255.255.0`.
O `.env` local foi ajustado para `LAB_BIND_IP=172.16.50.247`, porta 3000.
O IP anterior `10.102.23.64` pertence à configuração anterior e não deve ser usado
nos comandos desta sessão. O alvo autorizado para os testes pela LAN
é exclusivamente `http://172.16.50.247:3000`; os demais serviços e dispositivos
da rede ficam fora do escopo. A API Ollama permanece em `127.0.0.1:11434`.

O usuário aplicou a configuração; os comandos para reaplicá-la são:

```bash
docker compose -f compose.yaml -f compose.lock.json up -d --no-deps --pull never --wait juice-shop
python3 scripts/lab.py check
```

A recriação descarta o estado do Juice Shop; a restauração anterior já estabeleceu
um estado inicial conhecido. Depois, no Kali com a versão atual do script:

```bash
python3 scripts/lab.py kali-check --target http://172.16.50.247:3000
```

Preservar o registro gerado no Kali e confirmar a aplicação no navegador. Se o
Mac trocar de rede ou receber outro IP, atualizar `.env` antes de recriar o serviço.

## Diagnóstico do navegador no Kali

O registro local `evidencias/sprint-1/20261117T142522280487Z-check.json` tem
`success: true` e confirma HTTP 200 no IP da LAN, além da inferência local.
O usuário também enviou uma captura do JSON produzido no Kali: GET para
`http://172.16.50.247:3000/`, HTTP 200, 9.986 bytes, duração de 0,027 s e
`success: true`. curl, Nmap e Python retornaram código zero na verificação de
versão. A captura original está em
[kali-check-json.png](../evidencias/sprint-1/kali-check-json.png), adicionada em
18/11/2026. O arquivo JSON original do Kali ainda precisa ser copiado para este
repositório; a imagem não foi convertida em um registro JSON reconstruído.

O HTTP direto funcionava, mas a página não abria no Firefox. Em seguida, o usuário
confirmou que a dupla desativou o proxy do navegador e conseguiu abrir a aplicação.
O script desativa proxies (`ProxyHandler({})`), o que explica a diferença de
comportamento entre o diagnóstico direto e o navegador com proxy configurado.
Não foi identificado qual proxy estava em uso. Não foi necessário alterar
NAT/bridge ou desativar o firewall.

O critério funcional da Sprint 1 está atendido: acesso pelo Kali, inferência local
e restauração do Juice Shop. Permanecem pendentes a cópia do JSON original do Kali,
a captura da aplicação aberta e o complemento do inventário da dupla. O próximo
trabalho é registrar o planejamento humano da Sprint 2, antes de revisão pela IA.

# Sprint 1 — laboratório nas máquinas da dupla

## Adaptação do ambiente e escopo

Conforme informado por Luiz em 17/11/2026, a disciplina permite usar máquinas
pessoais, desde que isso seja declarado no relatório. O PDF original menciona o
kit da faculdade; este projeto adota a alternativa local informada pelo grupo.

**Registrar no relatório final:** execução em máquinas pessoais; Juice Shop e LLM
em Docker no Mac de Luiz; Kali em VM na máquina do outro integrante; tipo de rede
utilizado; endereços/portas autorizados; versões e recursos efetivamente usados.
Não declarar testes como realizados antes de coletar as evidências.

O único alvo autorizado é o Juice Shop deste projeto, no endereço e porta
configurados. O host macOS, a API de inferência e demais equipamentos não são
alvos. A API Ollama é um componente de apoio à integração.

## Arquitetura proposta

| Componente | Local | Endereço inicial | Persistência |
| --- | --- | --- | --- |
| Juice Shop | Docker no Mac | `http://127.0.0.1:3000` | Sem volume; recriação descarta os testes |
| Ollama | Docker no Mac | `http://127.0.0.1:11434` | Volume `ollama-data` com os modelos |
| curl, Nmap e Python | Contêiner auxiliar no Mac | Juice Shop via `http://juice-shop:3000` | Contêiner descartável |
| Kali Linux | VM na máquina da dupla | Acessa o IP privado do Mac após configurar a rede | Gerenciada pela dupla |
| Agente supervisionado | Implementado para o host do laboratório | API local do Ollama e ferramentas delimitadas | Código em `scripts/agente.py`; evidências em JSONL |

Juice Shop/ferramentas e Ollama usam redes Docker separadas. Nenhum contêiner
recebe acesso ao socket Docker ou arquivos pessoais do host. A separação de redes
não equivale a um bloqueio geral de saída para a internet.

O Kali remoto usa o **IP do Mac**, nunca o IP interno do contêiner. `localhost`
dentro do Kali aponta para o próprio Kali. Caso a dupla prefira hospedar o agente
no Kali, definiremos um acesso privado à API Ollama na Sprint 3; por enquanto a
porta 11434 não está publicada na LAN.

## Recursos e versões

Informações observadas durante a preparação:

| Item | Valor |
| --- | --- |
| Computador de Luiz | MacBook Air, Apple M1, ARM64, 8 GB RAM |
| macOS | 27.2.1, build 26B131 |
| Docker CLI | 29.4.3 |
| Docker Compose | v5.1.3 |
| Python do host | 3.9.6 |
| Docker Engine | 29.4.3, verificado pelo terminal do usuário |
| Juice Shop | 20.4.0-SNAPSHOT; imagem fixada por digest em `compose.lock.json` |
| Ollama e modelo | 0.40.16; `qwen3:1.7b`, Q4_K_M, digest no registro de `up` |
| Ferramentas no contêiner auxiliar | curl 7.88.1; Nmap 7.93; Python 3.11.2 |
| Máquina/versão Kali, IP e responsável da dupla | A preencher após configuração |

Ponto de partida sugerido: cerca de 4 GB de memória para o Docker Desktop, sem
outras cargas pesadas simultâneas. Os limites por contêiner são 768 MB para Juice
Shop, 3 GB para Ollama e 256 MB para ferramentas; não são reservas de memória.
Observe `docker stats` e a pressão de memória no Monitor de Atividade. Se houver
encerramento por falta de memória, ajuste os limites e reduza as cargas.

O modelo inicial `qwen3:1.7b` é quantizado em Q4_K_M e o download indicado no
catálogo é de aproximadamente 1,4 GB; o consumo em execução é maior. Usa contexto
de 2048 tokens e uma requisição por vez. É uma escolha inicial de infraestrutura,
não uma validação de qualidade para as investigações. A escolha final depende de
latência, consumo e comportamento observado.

O Ollama neste Docker Desktop/macOS utiliza CPU. Uma alternativa futura é Ollama
nativo no Mac para aproveitar a GPU; essa alternativa ainda não está configurada.
Para experimentar `qwen3:4b`, altere `OLLAMA_MODEL` no `.env`, reveja o limite de
memória (por exemplo, `OLLAMA_MEMORY=4g`) e a memória disponível no Docker Desktop,
e execute novamente `up`. Em um host de 8 GB, isso pode causar pressão de memória.

## 1. Inicializar no Mac

Abra o Docker Desktop e espere o Engine ficar pronto. No terminal, dentro do
repositório, execute:

```bash
docker version
cp .env.example .env
python3 scripts/lab.py up
```

Faça a cópia de `.env` somente uma vez. Python 3.9+ e Compose v2+ são necessários;
não há dependências Python externas. `up`:

1. Valida a configuração e verifica o acesso ao Docker.
2. Baixa Juice Shop/Ollama e grava suas referências imutáveis em `compose.lock.json`.
3. Aguarda os healthchecks dos serviços.
4. Baixa o modelo para o volume persistente e constrói a imagem de ferramentas.
5. Verifica HTTP pelo contêiner de ferramentas e pelo Mac.
6. Faz uma geração curta pela API local e registra resultado e duração.
7. Registra versões, IDs das imagens, detalhes e digest do modelo.

Abra <http://127.0.0.1:3000>. Cada execução do script salva um JSON datado em UTC
em `evidencias/sprint-1/`, incluindo falhas. Downloads/build exibem o progresso no
terminal; seu conteúdo completo não é guardado no JSON. Diagnósticos, versões e
resposta da API são registrados. O diagnóstico HTTP rejeita redirecionamentos.

Para repetir apenas a verificação ou o inventário:

```bash
python3 scripts/lab.py check
python3 scripts/lab.py inventory
```

Se o comando falhar, leia a etapa indicada e seu registro; não marque a sprint como
concluída. Se necessário, veja `docker compose logs --tail=100 juice-shop ollama`.

## 2. Fixar e preservar o ambiente

Na primeira execução, `latest` serve somente para obter imagens. O script grava
os digests em `compose.lock.json` e passa esse arquivo a todas as operações
posteriores. **Versione o lock junto com as evidências e mantenha-o na reprodução.**
Para comandos manuais que criem/recriem serviços, utilize os dois arquivos:

```bash
docker compose -f compose.yaml -f compose.lock.json up -d --wait juice-shop ollama
```

Alterar `JUICE_SHOP_IMAGE` ou `OLLAMA_IMAGE` no `.env` não substitui as imagens já
fixadas no lock. Uma atualização deve ser deliberada, preservando o lock anterior
e as evidências antes de gerar outro.

O modelo é identificado por tag e seu digest é registrado por `/api/tags`.
`up` volta a executar `ollama pull`; após iniciar as investigações, prefira o
comando manual acima e `check` para retomar sem atualizar o modelo. Preserve o
volume de modelos e registre mudanças de digest, se ocorrerem.

A imagem de ferramentas usa Debian Bookworm e pacotes dos repositórios da
distribuição; uma reconstrução futura pode mudar suas versões. O inventário
registra as versões efetivas e o ID da imagem. Para reprodução exata dessa imagem,
é possível arquivá-la com `docker save pf-techack-tools -o /tmp/pf-techack-tools.tar`
e carregá-la na máquina compatível com `docker load -i /tmp/pf-techack-tools.tar`.
O arquivo pode ser grande; não o inclua no Git.

## 3. Conectar o Kali da dupla

### Se estiverem na mesma rede privada

**Sessão de 17/11/2026:** a dupla mudou para a LAN do laboratório WannaCry,
informada como isolada pelo usuário. O Mac foi observado com IP `172.16.50.247`
na interface ativa `en0`, e o `.env` local já foi ajustado.
O endereço `http://172.16.50.247:3000` já respondeu HTTP 200 no Mac e no script
do Kali; o usuário confirmou que a interface abriu no Firefox após desativar o
proxy do navegador. Os comandos abaixo usam esse IP;
atualize-o ao reproduzir o ambiente em outra rede.

No Mac, veja o IPv4 da interface ativa em Ajustes do Sistema → Rede. Se o Wi-Fi
estiver em `en0`, também é possível usar `ipconfig getifaddr en0`.

O `.env` já está configurado com o IP observado do Mac na WannaCry:

```dotenv
LAB_BIND_IP=172.16.50.247
```

Recrie somente o Juice Shop para aplicar o novo vínculo. Isso também descarta seu
estado; faça antes das investigações ou depois de guardar as evidências:

```bash
docker compose -f compose.yaml -f compose.lock.json up -d --no-deps --pull never --wait juice-shop
python3 scripts/lab.py check
```

A partir desse momento use `http://IP_DO_MAC:3000` também no navegador do Mac;
o vínculo anterior com `127.0.0.1:3000` foi substituído. Se o IP mudar, atualize
`.env` e recrie o serviço.

No Kali, NAT da VM costuma permitir conexões de saída para a LAN; bridge também
pode funcionar se a rede permitir. Não é necessário expor portas da VM para
acessar o Mac. Host-only isolado não conecta por si só máquinas físicas distintas.

No Kali, copie/clone este repositório e prepare as ferramentas:

```bash
sudo apt update
sudo apt install -y curl nmap python3
# IP observado do Mac na rede WannaCry:
python3 scripts/lab.py kali-check --target http://172.16.50.247:3000
```

Abra a mesma URL no navegador do Kali. Preserve o JSON gerado na VM e uma captura
de tela que mostre a URL e a aplicação. O script verifica ferramentas e HTTP 200;
a confirmação visual distingue a aplicação de algum outro serviço naquela porta.
Traga essas evidências para a entrega do grupo e registre IP/versão do Kali.

Wi-Fi de convidados ou da faculdade pode isolar clientes, mesmo na mesma rede.
Nesse caso, use uma rede privada que permita comunicação ou a alternativa abaixo.
Se o firewall do macOS bloquear o Docker, ajuste somente a permissão necessária;
não desative o firewall inteiro.

### Se estiverem em redes diferentes

Será necessária uma VPN privada (por exemplo Tailscale ou WireGuard) com rota
entre o Mac e o Kali. O provedor ainda não foi escolhido/configurado. Configurar
a VPN diretamente na VM Kali e no Mac simplifica a conectividade; colocá-la só
no host da VM pode exigir configuração adicional de roteamento.

Depois de estabelecer a VPN, use o IP privado da VPN do Mac em `LAB_BIND_IP`,
recrie Juice Shop e execute `kali-check` com esse mesmo IP. A instalação da VPN,
a rota e o vínculo Docker com a interface virtual precisam ser verificados nas
máquinas reais. Não encaminhe a porta no roteador nem publique a aplicação em um
túnel público. Restrinja o acesso aos participantes do laboratório.

## 4. Ferramentas auxiliares no Mac

Disponíveis após `up`, sem instalar Nmap no macOS:

```bash
docker compose run --rm tools curl --fail --max-time 15 http://juice-shop:3000/
docker compose run --rm tools nmap --version
docker compose run --rm tools python3 --version
```

O contêiner é não privilegiado; uma futura integração de Nmap deverá usar modos
compatíveis, como conexão TCP (`-sT`), com destino e porta delimitados. As
ferramentas desse contêiner não são as usadas pelo agente atual, que implementa
HTTP e conexão TCP diretamente em Python. A seleção definitiva das
ferramentas de investigação cabe à dupla após o planejamento humano da Sprint 2.

## 5. Restauração verificável

Guarde as evidências, pare os testes da dupla e feche a página nos dois navegadores.
Então execute:

```bash
python3 scripts/lab.py reset --confirm
```

O script cria um marcador temporário no contêiner, recria somente o Juice Shop,
confirma a mudança do ID com manutenção da imagem, verifica que o marcador sumiu,
valida HTTP e confirma que `/api/Challenges` apresenta zero desafios resolvidos.
Essa consulta é uma checagem de estado inicial, sem executar soluções dos desafios.
Se a API mudar ou o estado não corresponder, o script falha e registra a divergência.

Limpe cookies, localStorage e demais dados do site nos navegadores do Mac e Kali,
ou abra sessões privadas novas. A restauração do servidor não limpa o navegador;
dados de progresso no cliente podem reaparecer. Evite abas antigas conectadas
durante a validação. O volume Ollama e a pasta de evidências não são removidos.

Para encerrar o laboratório sem excluir os modelos:

```bash
docker compose down
```

Não use `down -v` para um reinício comum: isso apaga também o volume do modelo.

## 6. Fechamento da Sprint 1

Para validar apenas o código de preparação sem iniciar serviços:

```bash
docker compose --profile tools config --quiet
python3 -m unittest discover -s tests -v
```

Esses testes usam respostas simuladas e não substituem os testes nas duas máquinas.

Concluir somente após ter evidências reais de:

- `up`/`check` bem-sucedidos, incluindo geração local não vazia.
- Inventário e `compose.lock.json` preservados.
- `kali-check` bem-sucedido na VM da dupla e aplicação confirmada no navegador.
- Restauração bem-sucedida e dados dos navegadores limpos.
- Endereço/porta do Juice Shop autorizados e rede efetiva registrados.

## Referências de implementação

- [Execução oficial do Juice Shop](https://help.owasp-juice.shop/part1/running.html)
- [Ollama em Docker](https://docs.ollama.com/docker)
- [Ollama: execução local, GPU e desativação da nuvem](https://docs.ollama.com/faq)
- [API de geração](https://docs.ollama.com/api/generate)
- [Modelo inicial Qwen3 1.7B](https://ollama.com/library/qwen3:1.7b)
- [Publicação de portas Docker](https://docs.docker.com/engine/network/port-publishing/)

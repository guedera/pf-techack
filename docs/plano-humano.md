# Planejamento dos testes — versão original da dupla

Feito sem apoio do LLM, conforme a seção 3 do roteiro.

- Integrantes: Luiz Miguel e Guilherme Guedes

## Análise inicial do ambiente

Nenhuma anomalia identificada.

## Investigação 1

- **Aspecto da aplicação investigado:** Tratamento de login
- **Hipótese inicial:** Suspeitamos que o site nao faz o handler adequado para evitar vazar informacoes de usuario na tela de login
- **Ferramentas que podem contribuir:** DevTools, BurpSuite ou WireShark.
- **Evidências necessárias para sustentar as conclusões:** Credenciais aparecer no payload ou cabecalho da requisicao.

## Investigação 2

- **Aspecto da aplicação investigado:** Controle de acesso inseguro
- **Hipótese inicial:** Suspeitamos que o site permitia acessar o carrinho de outros usuarios
- **Ferramentas que podem contribuir:** BurpSuite ou DevTools
- **Evidências necessárias para sustentar as conclusões:** Mudar o ID do carrinho do usuario (dentro do local-database) para outro ID e verificar se mudou os itens do carrinho.

## Investigação 3

- **Aspecto da aplicação investigado:** Exposição de Dados Sensíveis
- **Hipótese inicial:** Suspeitamos que o site vazava informacoes importantes e credenciais por algum acesso indevido.
- **Ferramentas que podem contribuir:** BurpSuite
- **Evidências necessárias para sustentar as conclusões:** testar acesso por "/robots.txt" e verificar possiveis caminhos para informacoes de credenciais e informacoes importantes.

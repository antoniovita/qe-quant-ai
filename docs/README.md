# Projeto Quant — Desafio Itaú Asset Quant AI 2026

## Visão geral

Ciclos de afrouxamento monetário sustentam artificialmente empresas
estruturalmente frágeis (*zombie firms*). Quando o ciclo de Selic reverte,
essas empresas sofrem reprecificação negativa previsível. A estratégia
identifica essas empresas antes da virada e monta uma posição long-short
(comprada em qualidade, vendida em fragilidade), condicionada ao regime
monetário.

A contribuição metodológica central é um **ICR contrafactual com
decomposição de spread**: em vez de recalcular o custo de dívida com uma
taxa normalizada única para todas as empresas, preserva o spread de crédito
específico de cada uma e substitui apenas o componente de política
monetária (Selic → Selic normalizada). Isso produz um rótulo de
"dependência de ciclo" que serve de alvo para um modelo de ML treinado em
features fundamentalistas cross-sectional.

## Índice da documentação

1. [Tese e Fundamentação](01-tese-e-fundamentacao.md) — a ideia central, a
   literatura de zombie firms, e por que o mecanismo é Selic e não QE.
2. [Metodologia — ICR Contrafactual](02-metodologia-icr-contrafactual.md) —
   a fórmula completa, passo a passo, com decomposição de spread e
   tratamento de casos-limite.
3. [Base de Dados](03-base-de-dados.md) — pipeline de coleta CVM,
   decisões de tratamento, validações realizadas e limitações conhecidas.
4. [Fontes de Dados](04-fontes-de-dados.md) — tabela de fontes adicionais
   necessárias (preços, Selic, setorial, aluguel de ações, Japão).
5. [Portfólio e Universo](05-portfolio-e-universo.md) — regras de
   elegibilidade, montagem long-short e overlay de regime monetário.
6. [Modelo de ML](06-modelo-ml.md) — features, modelos candidatos,
   interpretabilidade (SHAP) e disciplina metodológica.
7. [Backtest](07-backtest.md) — princípios obrigatórios (look-ahead,
   survivorship, custos) e o capítulo opcional de validação no Japão.

## Estado do projeto

Ver [/tasks](../tasks/) para o backlog detalhado:

- [tasks/done.md](../tasks/done.md) — o que já foi feito
- [tasks/current.md](../tasks/current.md) — em andamento
- [tasks/backlog.md](../tasks/backlog.md) — próximos passos

## Princípios metodológicos gerais

Aplicam-se a todo o projeto, não só ao backtest:

- **Look-ahead bias:** sinal em `t`, execução em `t+1`; fundamentos
  filtrados por data de publicação, não de referência.
- **Survivorship bias:** sempre usar fontes que preservam empresas
  deslistadas/falidas (CVM para fundamentos, COTAHIST para preços).
- **Premissa conservadora na dúvida:** sempre a favor de jogar contra a
  estratégia — se o alfa sobrevive, é robusto.
- **Validar antes de escalar:** auditar uma amostra pequena antes de rodar
  o pipeline completo.
- **Mediana, não média:** dados financeiros têm cauda gorda.

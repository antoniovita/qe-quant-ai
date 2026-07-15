# 1. Tese e Fundamentação

## 1.1 Ideia central

Ciclos de afrouxamento monetário (juros baixos) sustentam artificialmente
empresas estruturalmente frágeis. Quando o ciclo de juros reverte, essas
empresas sofrem reprecificação negativa previsível.

A estratégia identifica essas empresas antes da virada do ciclo e monta uma
posição long-short:

- **Long:** empresas de qualidade, estruturalmente saudáveis
- **Short:** empresas frágeis, dependentes de juro baixo para sobreviver

A exposição é **condicionada ao regime monetário** — a estratégia se
intensifica quando o ciclo de alta de juros está em curso e reduz exposição
quando o ciclo está em queda ou estável.

## 1.2 Fundamentação teórica

A tese se apoia na literatura de **zombie firms**:

- Caballero, Hoshi & Kashyap (2008) — empresas que sobrevivem em fragilidade
  estrutural porque conseguem rolar dívida indefinidamente sob crédito
  barato.
- Banerjee & Hofmann (BIS) — caracterização e mensuração de empresas-zumbi em
  mercados desenvolvidos.

### Por que não QE

A fundamentação original cogitava usar Quantitative Easing (QE) como
mecanismo de sustentação artificial. Essa hipótese foi **descartada**: o BIS
Working Paper 1286 mostra que QE beneficia principalmente empresas grandes e
bem avaliadas — o oposto do que a tese propõe (sustentação das mais frágeis).

Como o Brasil não pratica QE, o mecanismo de transmissão relevante é a
**taxa básica de juros (Selic)**, não expansão de balanço do banco central.
O ciclo de referência da estratégia é, portanto, o **ciclo de Selic**.

## 1.3 Extensão internacional (Japão, opcional)

Validação out-of-sample do modelo treinado no Brasil, sem retreinamento,
aplicada ao mercado japonês pós-normalização de juros do BOJ. Ver
[07-backtest.md](07-backtest.md#capítulo-japão-opcional-validação-out-of-sample)
para detalhes de implementação e critérios de inclusão no escopo final.

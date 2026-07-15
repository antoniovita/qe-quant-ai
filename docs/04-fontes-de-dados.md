# 4. Fontes de Dados Adicionais Necessárias

| Dado | Fonte | Uso |
|---|---|---|
| ITR (trimestral) | Portal Dados Abertos CVM (`dados.cvm.gov.br`, dataset `cia_aberta-doc-itr`) | Migrar o painel de anual para trimestral para o backtest final |
| Preços históricos, incl. deslistadas | COTAHIST B3 | Retornos, sinal de preço, evita survivorship bias |
| Selic histórica (série e meta) | BCB SGS (série 432 — Selic meta; 4390 — Selic acumulada) | Cálculo do spread e da Selic normalizada |
| Taxa neutra real | BCB — Relatório de Política Monetária | Selic normalizada (Passo 3, [02-metodologia-icr-contrafactual.md](02-metodologia-icr-contrafactual.md)) |
| Meta de inflação | BCB/CMN | Selic normalizada (Passo 3) |
| Classificação setorial | B3 | Normalização de features por setor (z-score setorial) |
| Custo de aluguel de ações (BTC) | B3 — Banco de Títulos CBLC | Custo de transação da perna short |
| Registro de companhias canceladas | CVM | Diferenciar quebra de M&A/fechamento de capital voluntário |
| (Opcional) Fundamentos Japão | J-Quants API, plano Premium (~R$600/mês, 1 mês) | Capítulo de validação out-of-sample ([07-backtest.md](07-backtest.md)) |

## Notas de uso

- Todas as fontes de fundamentos e preços devem preservar empresas
  deslistadas/falidas — ver princípio de survivorship bias em
  [README.md](README.md#princípios-metodológicos-gerais).
- Dados point-in-time (data de publicação, não período de referência) são
  obrigatórios para fundamentos usados no backtest.

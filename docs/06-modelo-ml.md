# 6. Camada de Machine Learning

## 6.1 As quatro camadas do projeto

1. **Base de dados** — feito (ver [03-base-de-dados.md](03-base-de-dados.md))
2. **Rótulo (ICR contrafactual)** — regra determinística
   ([02-metodologia-icr-contrafactual.md](02-metodologia-icr-contrafactual.md)),
   não é ML
3. **Score de fragilidade via ML** — aqui entra o ML (este documento)
4. **Estratégia e backtest** — ver [05-portfolio-e-universo.md](05-portfolio-e-universo.md)
   e [07-backtest.md](07-backtest.md)

## 6.2 Papel do ML

O rótulo do ICR contrafactual (`Ciclo_dependente`, Passo 7 da metodologia) é
a variável-alvo (label). O modelo aprende a prever esse rótulo a partir de
**outras** features fundamentalistas — **não** usa despesa de juros/dívida
diretamente como feature, apenas como componente do label.

Isso é proposital:

- Permite que o modelo generalize o padrão para situações de dado
  incompleto (ex.: Japão, onde despesa de juros custa caro na API)
- Produz um **score contínuo/rankável** em vez de uma flag binária

## 6.3 Features candidatas

Todas em **z-score setorial**, mesmo trimestre.

| Categoria | Variável |
|---|---|
| Alavancagem | Dívida líquida / EBITDA |
| Alavancagem | Dívida líquida / Patrimônio Líquido |
| Estrutura de dívida | % dívida de curto prazo sobre dívida total |
| Geração de caixa | FCO / Dívida total |
| Geração de caixa | FCO / Receita |
| Margens | Margem EBITDA |
| Margens | Margem líquida |
| Crescimento | Variação da dívida bruta trimestre a trimestre |
| Crescimento | Variação de receita YoY |
| Liquidez | Liquidez corrente |
| Tamanho (controle) | Log do ativo total |
| Mercado | Book-to-market |
| Contexto macro | Spread Selic vigente vs. normalizada |

## 6.4 Modelos previstos

- **Baseline:** regressão logística regularizada — transparente, fácil de
  defender.
- **Modelo principal:** gradient boosting (XGBoost/LightGBM), comparado
  contra o baseline.
- **Interpretabilidade:** reportar SHAP values para (a) validar que o
  modelo não está apenas replicando o próprio ICR observado (checagem de
  vazamento de informação) e (b) suportar a apresentação.

## 6.5 Disciplina metodológica

ML fica restrito à **camada cross-sectional** (comparação entre empresas no
mesmo momento). O regime monetário (quando operar) usa regras simples
baseadas na Selic — ver overlay de regime em
[05-portfolio-e-universo.md](05-portfolio-e-universo.md#53-overlay-de-regime-monetário).

Motivo: poucos ciclos históricos de Selic tornariam qualquer ML nesse
componente temporal propenso a overfitting.

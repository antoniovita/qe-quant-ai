# 5. Universo de Ativos e Regras de Portfólio

## 5.1 Universo elegível

Recalculado **point-in-time** a cada rebalanceamento:

- Ações não-financeiras da B3 com ≥ 8 trimestres de histórico de balanço
- ADTV (volume médio diário) acima de piso de liquidez (início: R$1M/dia,
  testar sensibilidade)
- Patrimônio líquido positivo, sem recuperação judicial ativa

**Estimativa:** 120–200 papéis elegíveis por trimestre, variando ao longo
do tempo.

## 5.2 Montagem do portfólio

Rebalanceamento **trimestral**, sincronizado com divulgação de balanços.

### Long

- Quintil inferior de probabilidade de ciclo-dependência (score do modelo)
- Peso igual ou levemente inclinado por qualidade (ROE/margem)

### Short

- Quintil superior de probabilidade, ponderado pela própria probabilidade
  prevista
- Cap por posição (sugestão: 8–10% do book por posição)

### Neutro

- Os ~60% do meio ficam fora da estratégia naquele trimestre

## 5.3 Overlay de regime monetário

Multiplicador de exposição na perna short baseado em regra simples sobre a
trajetória da Selic:

| Regime | Multiplicador |
|---|---|
| Selic em queda | 0.5x |
| Selic estável | 1x |
| Selic em alta | 1.3x – 1.5x |

**Regra determinística, não ML** — poucos ciclos históricos de Selic
tornariam qualquer componente de ML nessa camada propenso a overfitting.
Ver disciplina metodológica em [06-modelo-ml.md](06-modelo-ml.md#disciplina-metodológica).

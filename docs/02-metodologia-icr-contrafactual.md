# 2. Metodologia: ICR Contrafactual com Decomposição de Spread

## 2.1 Definição base

**ICR (Interest Coverage Ratio)** = EBIT ÷ Despesa de Juros.

ICR < 1 significa que o lucro operacional não cobre os juros da dívida —
definição clássica de empresa-zumbi.

**Problema:** com juros baixos, a despesa de juros cai e o ICR "melhora" sem
a empresa melhorar de fato — a política monetária mascara a fragilidade
estrutural.

## 2.2 Fórmula final (versão refinada, com decomposição de spread)

A versão inicial aplicava uma taxa normalizada única (mediana histórica) a
todas as empresas. A versão refinada **preserva o spread de crédito
específico de cada empresa** e substitui apenas o componente de política
monetária. Essa é a contribuição metodológica central do projeto.

### Passo 1 — Taxa implícita da dívida da empresa

Para empresa $i$, período $t$:

```
r_implícita(i,t) = Despesa Financeira(i,t) [anualizada] / Dívida Bruta Média(i,t)
```

Dívida Bruta Média = média entre dívida bruta no início e fim do período
(evita distorção de captações/amortizações no meio do período).

### Passo 2 — Spread de crédito da empresa

```
spread(i,t) = r_implícita(i,t) − Selic(t)
```

Reflete o risco de crédito específico da empresa — informação real sobre
qualidade de crédito, não estímulo monetário.

### Passo 3 — Selic normalizada (taxa neutra)

```
Selic_normalizada(t) = Selic_neutra_real (BC) + Meta_de_Inflação(t)
```

- **Preferencial:** série de taxa neutra real publicada pelo Banco Central
  (Relatório de Política Monetária) somada à meta de inflação vigente.
- **Alternativa mais simples** (se a série do BC não for usada): média móvel
  de 10 anos da Selic real, somada de volta à meta de inflação vigente.

Evita o problema de quebra estrutural de usar a média de todo o histórico da
Selic, que misturaria o regime de juros altos pré-2000 com o regime
pós-metas de inflação.

### Passo 4 — Taxa contrafactual da empresa

```
r_contrafactual(i,t) = Selic_normalizada(t) + spread(i,t)
```

### Passo 5 — Despesa financeira contrafactual

```
Despesa_Financeira_contrafactual(i,t) = r_contrafactual(i,t) × Dívida_Bruta_Média(i,t)
```

### Passo 6 — Os dois ICRs

```
ICR_observado(i,t)     = EBIT(i,t) / Despesa_Financeira(i,t)
ICR_contrafactual(i,t) = EBIT(i,t) / Despesa_Financeira_contrafactual(i,t)
```

### Passo 7 — Rótulo final (empresa ciclo-dependente)

```
Ciclo_dependente(i,t) = 1[ICR_observado(i,t) > 1] AND 1[ICR_contrafactual(i,t) < 1]
```

Ou seja: a empresa parece saudável hoje (com juro baixo), mas não
sobreviveria pagando uma taxa de juros normalizada. Essa divergência é a
tese em forma de fórmula, e é o **label** usado na camada de ML
(ver [06-modelo-ml.md](06-modelo-ml.md)).

## 2.3 Casos-limite e tratamento

- **Despesa financeira zero → ICR "infinito":** tratar como dado faltante,
  não como cobertura infinita.
- **Outliers de custo de dívida implícito:** filtrar valores fora do
  intervalo [0%, 60%] antes de qualquer cálculo de mediana/spread.
- **Mediana, não média:** preferir mediana em todas as agregações — dados
  financeiros têm cauda gorda.
- **Ruído no spread ano a ano:** considerar suavização com média móvel de
  2-3 anos por empresa como refinamento futuro. Documentar como limitação
  se não implementado na v1.

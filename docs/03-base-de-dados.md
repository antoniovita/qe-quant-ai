# 3. Base de Dados

## 3.1 Fonte

**Dados Abertos da CVM** — Demonstrações Financeiras Padronizadas (DFP,
anuais), série **2013–2024** (12 anos).

O início em 2013 evita inconsistências de layout dos primeiros anos
pós-convergência IFRS (2010–2012).

## 3.2 Pipeline

Script Python (`pipeline_cvm.py`) que:

1. Baixa os arquivos diretamente do servidor da CVM (`dados.cvm.gov.br`)
2. Trata encoding ISO-8859-1 e separador `;`
3. Consolida tudo em um único CSV

## 3.3 Artefato atual

`base_fundamentalista_consolidada.csv`

- **4.405** observações empresa-ano
- **615** empresas distintas
- Colunas: EBIT, Despesa Financeira, Dívida Bruta (por empresa e ano)

## 3.4 Decisões de tratamento de dados (já validadas)

- **Extração de contas por texto (`DS_CONTA`), não por código
  (`CD_CONTA`)** — o código de conta é instável entre empresas; o texto é
  mais confiável.
- **Dívida bruta = soma apenas dos totais de nível 2 do plano de contas:
  2.01.04 (circulante) + 2.02.01 (não circulante)** — evita dupla contagem
  (empréstimos + debêntures + arrendamento somados junto com o total).
- **Balanço é foto de instante (estoque)**, não tem `DT_INI_EXERC` — só a
  DRE (fluxo) tem período.
- **Bancos e seguradoras são excluídos naturalmente** (plano de contas de
  Intermediação Financeira é diferente) — comportamento desejado, ICR não
  se aplica a essas instituições.
- **Normalização de escala** (empresas reportam em milhares ou unidades)
  para reais.

## 3.5 Validações realizadas

- EBIT da Ambev bate com Status Invest/Investing.
- Sanity check via `CD_CVM` (identificador estável) em Vale, Ambev, WEG,
  Gerdau, Telefônica, Magazine Luiza, Petrobras — trajetórias batem com a
  realidade conhecida (ex.: Petrobras com EBIT negativo em 2014–2015).
- Custo efetivo de dívida mediano segue a Selic com spread positivo
  consistente (~20% no pico de 2016, ~13% no fundo de 2020–21) — evidência
  de sinal econômico real na base.

## 3.6 Limitações documentadas

- **Dívida em moeda estrangeira** (Petrobras, Vale, exportadoras) tem custo
  de dívida subestimado — parte do custo cai em variação cambial, não em
  juros.
- A linha "Despesas Financeiras" às vezes embute câmbio e outros itens além
  de juros puros.
- **Dados anuais (DFP) são mais ruidosos que trimestrais** para o cálculo
  do spread — mitigado por mediana e filtro de outliers. Migração para ITR
  (trimestral) está no backlog (ver [tasks/backlog.md](../tasks/backlog.md)).

# 7. Backtest

> O backtest corresponde a **55% da nota do desafio** — a execução desta
> etapa merece rigor proporcional.

## 7.1 Princípios obrigatórios

- **Sinal gerado em `t`, execução em `t+1`** — evita look-ahead bias
- **Fundamentos filtrados por data de publicação/entrega**, não pelo
  período de referência (point-in-time real)
- **Preços via COTAHIST da B3**, incluindo empresas deslistadas — evita
  survivorship bias (as quebradas são o lucro do short)
- **Custos de transação + custo de aluguel de ações** na perna short, com
  análise de sensibilidade
- **Empresa deslistada no meio do teste:** fechar posição no último preço
  observado (premissa conservadora)
- **Na dúvida entre premissas, sempre escolher a que joga CONTRA a
  estratégia**

Estes princípios se conectam diretamente aos princípios metodológicos
gerais do projeto — ver [README.md](README.md#princípios-metodológicos-gerais).

## 7.2 Capítulo Japão (opcional, validação out-of-sample)

- Aplicar o score treinado no Brasil **sem retreinar**, testar se prevê
  underperformance de empresas frágeis japonesas desde 2024
- Excluir financeiras via classificação setorial `Sector33`
- Usar **operating profit** como EBIT equivalente (nunca *ordinary
  profit*)
- Controlar mistura de padrões contábeis (JGAAP majoritário vs. IFRS em
  ~270 empresas grandes)

**Decisão de escopo:** incluir este capítulo fica condicionado ao núcleo
Brasil estar pronto. Se apertar no cronograma, vira seção de "extensão
proposta" no relatório final, sem necessidade de execução completa.

Fonte de dados: J-Quants API, plano Premium — ver
[04-fontes-de-dados.md](04-fontes-de-dados.md).

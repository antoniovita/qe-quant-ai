import pandas as pd
import numpy as np
import matplotlib.pyplot as plt 
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

#O objetivo desse código é calcularmos a taxa normalizada que servirá de contrafactual para identificarmos as empresas ciclo-dependentes
#Calcularemos o custo da dívida de cada empresa diretamente dos demonstrativos (despesas financeiras/dívida bruta) e tiraremos a mediana, após fiktrar os outliers

#adicioanremos uma nova coluna cahamada "custos" e filtraremos os valores que carregam uma dívida nula ou custos absurdamente altos (60% por exemplo)

df = pd.read_csv('base_fundamentalista_v2.csv')
#pd.set_option("display.float_format", lambda x: f"{x:,.0f}")

# trateremos as linhas com dívida bruta nula

#df['DIVIDA_BRUTA_calculo'] = df[df['DIVIDA_BRUTA'] > 0] aqui deu erro pq o filtro filtra as colunas que decidimos, mas devolve o datraframe inteiro filtrado, não apenas a coluna

#a solução é criar um novo dataframe, um dataframe filtrado

df_filtrado = df[df["DIVIDA_BRUTA"]> 0].copy()

df_filtrado['CUSTO'] = df_filtrado["DESPESA_FINANCEIRA_ABS"] / df_filtrado['DIVIDA_BRUTA']

#print(df_filtrado[['CUSTO', 'ANO']])          #aqui damos print em uma tabela apenas coom as colunas custo e ANO
df_final = df_filtrado[(df_filtrado['CUSTO'] > 0) & (df_filtrado['CUSTO'] < 0.6)].copy()

# print(df_final['CUSTO'].describe())
print(df_final.groupby('ANO')['CUSTO'].median())        ### Ao rodar essa linha, encontramos a mediana da taxa nos períodos de alta em cerca de 17% e será nossa taxa normalizada

#Agora, vamos criar outro dataframe mas sem os filtros anteriores que usamos aopenas para calcular a taxa normalizada

df_rotulo = df[df['DIVIDA_BRUTA'] > 0].copy()  #esse filtro ainda existe pq empresas sem dívidas são estruturalmente não influenciadas pelo ciclo

df_rotulo['DESPESA_TRATADA'] = df_rotulo['DESPESA_FINANCEIRA_ABS'].replace(0, np.nan)

#Agora calculamos a cobertura de juros observada (EBIT/despesa com juros)

df_rotulo['ICR_OBSERVADO'] = df_rotulo['EBIT'] / df_rotulo['DESPESA_TRATADA']

print(df_rotulo['ICR_OBSERVADO'].describe() )

#Com base na taxa normalizada, veremos quais empresas se sustentariam sob essa taxa mais alta

#Com base na taxa normalizada, veremos quais empresas se sustentariam sob essa taxa mais alta

taxa_normalizada = 0.17
tolerancia_icr = 1.2   #zona de tolerância: cobrir juros por margem de até 20% sob taxa normal ainda é fragilidade (evita que oscilações mínimas em torno de 1,0 quebrem a classificação)

df_rotulo['DESPESA_CONTRAFACTUAL'] = df_rotulo['DIVIDA_BRUTA'] * taxa_normalizada
df_rotulo['ICR_CONTRAFACTUAL'] = df_rotulo['EBIT'] / df_rotulo['DESPESA_CONTRAFACTUAL']

#Classificamos cada empresa-ano em um dos três estados (np.select testa na ordem e para na 1ª verdadeira)
#Usamos a ZONA DE TOLERÂNCIA (< tolerancia_icr, não < 1) para o contrafactual: quem cobre os juros por margem fina também está sendo considerado
condicoes = [
    df_rotulo['EBIT'] < 0,
    (df_rotulo['ICR_OBSERVADO'] > 1) & (df_rotulo['ICR_CONTRAFACTUAL'] < tolerancia_icr)
]
resultados = ['ja_fragil', 'ciclo_dependente']

df_rotulo['ESTADO_ANO'] = np.select(condicoes, resultados, default='saudavel')

#Persistência: só é rótulo de verdade se o estado se repete em 2 anos consecutivos (evita ano ruim pontual)
df_rotulo = df_rotulo.sort_values(['CD_CVM', 'ANO'])
df_rotulo['ESTADO_ANO_ANTERIOR'] = df_rotulo.groupby('CD_CVM')['ESTADO_ANO'].shift(1)

condicoes_persist = [
    (df_rotulo['ESTADO_ANO'] == 'ja_fragil') & (df_rotulo['ESTADO_ANO_ANTERIOR'] == 'ja_fragil'),
    (df_rotulo['ESTADO_ANO'] == 'ciclo_dependente') & (df_rotulo['ESTADO_ANO_ANTERIOR'] == 'ciclo_dependente')
]
resultados_persist = ['ja_fragil', 'ciclo_dependente']

df_rotulo['ROTULO_FINAL'] = np.select(condicoes_persist, resultados_persist, default='saudavel')

print(df_rotulo['ROTULO_FINAL'].value_counts())

df_rotulo['EBIT_POSITIVO'] = df_rotulo['EBIT'].where(df_rotulo['EBIT'] > 0)
 
#FEATURE 1 - Alavancagem (dívida líquida / EBIT). Peso esperado: POSITIVO (mais dívida = mais frágil)
df_rotulo['FEAT_ALAVANCAGEM'] = df_rotulo['DIVIDA_LIQUIDA'] / df_rotulo['EBIT_POSITIVO']
 
#FEATURE 2 - Custo de dívida (despesa financeira / dívida bruta). Peso esperado: POSITIVO
df_rotulo['FEAT_CUSTO_DIVIDA'] = df_rotulo['DESPESA_FINANCEIRA_ABS'] / df_rotulo['DIVIDA_BRUTA']
 
#FEATURE 3 - Accruals: (lucro - caixa operacional)/ativo. Mede qualidade do lucro (lucro que não vira caixa)
df_rotulo['FEAT_ACCRUALS'] = (df_rotulo['LUCRO_LIQUIDO'] - df_rotulo['CAIXA_OPERACIONAL']) / df_rotulo['ATIVO_TOTAL']
 
#FEATURE 4 - Crescimento dívida vs receita (precisa do ano anterior via shift). Peso esperado: POSITIVO
df_rotulo['DIVIDA_ANT'] = df_rotulo.groupby('CD_CVM')['DIVIDA_BRUTA'].shift(1)
df_rotulo['RECEITA_ANT'] = df_rotulo.groupby('CD_CVM')['RECEITA'].shift(1)
df_rotulo['CRESC_DIVIDA'] = (df_rotulo['DIVIDA_BRUTA'] - df_rotulo['DIVIDA_ANT']) / df_rotulo['DIVIDA_ANT']
df_rotulo['CRESC_RECEITA'] = (df_rotulo['RECEITA'] - df_rotulo['RECEITA_ANT']) / df_rotulo['RECEITA_ANT']
df_rotulo['FEAT_CRESC_DIV_REC'] = df_rotulo['CRESC_DIVIDA'] - df_rotulo['CRESC_RECEITA']
 
#FEATURE 5 - Margem EBIT (EBIT / receita). Peso esperado: NEGATIVO (mais margem = menos frágil)
df_rotulo['FEAT_MARGEM'] = df_rotulo['EBIT'] / df_rotulo['RECEITA']
 
feats = ['FEAT_ALAVANCAGEM','FEAT_CUSTO_DIVIDA','FEAT_ACCRUALS','FEAT_CRESC_DIV_REC','FEAT_MARGEM']
 
#TRATAMENTO 1 - infinitos: divisões por zero (receita nula) geram inf -> viram NaN
df_rotulo[feats] = df_rotulo[feats].replace([np.inf, -np.inf], np.nan)
 
#TRATAMENTO 2 - winsorização (p1-p99): apara outliers extremos que distorceriam o z-score
for f in feats:
    p1, p99 = df_rotulo[f].quantile(0.01), df_rotulo[f].quantile(0.99)
    df_rotulo[f] = df_rotulo[f].clip(lower=p1, upper=p99)
 
#TRATAMENTO 3 - z-score ((valor-média/desv. padrão)): padroniza para média 0, desvio 1, deixando as features comparáveis
for f in feats:
    df_rotulo[f + '_Z'] = (df_rotulo[f] - df_rotulo[f].mean()) / df_rotulo[f].std()
 
feats_z = [f + '_Z' for f in feats]
print(df_rotulo[feats_z].describe().round(3).to_string())

#Agora iremos tornar o rótulo em binário 1- ciclo-dependente 0- não ciclo-dependente

df_rotulo['ALVO'] = (df_rotulo['ROTULO_FINAL'] == 'ciclo_dependente').astype(int)    #astype transformamos true em 1 e false em 0

# print(df_rotulo['ALVO'].value_counts())

feats_z = ['FEAT_ALAVANCAGEM_Z','FEAT_CUSTO_DIVIDA_Z','FEAT_ACCRUALS_Z','FEAT_CRESC_DIV_REC_Z','FEAT_MARGEM_Z']
df_rotulo[feats_z] = df_rotulo[feats_z].fillna(0)           #para aqueles valores nan, definimos um z-score de 0, que significa que a empresa assume um comportamento médio

print(df_rotulo[feats_z].isna().sum())


feats_z = ['FEAT_ALAVANCAGEM_Z','FEAT_CUSTO_DIVIDA_Z','FEAT_ACCRUALS_Z','FEAT_CRESC_DIV_REC_Z','FEAT_MARGEM_Z']

# treino: até 2021 | teste: 2022 em diante
treino = df_rotulo[df_rotulo['ANO'] <= 2021]
teste = df_rotulo[df_rotulo['ANO'] >= 2022]

X_treino = treino[feats_z]   # treina de 2013-2021 sob os z-score dos features
y_treino = treino['ALVO']    #como se fosse o gabarito do modelo, o que ele vê como resultado e tenta prever o padrão nos features que levam a ele
X_teste = teste[feats_z]     # testa de 2022-2025
y_teste = teste['ALVO']

# print("Treino - alvo:", y_treino.value_counts().to_dict())
# print("Teste  - alvo:", y_teste.value_counts().to_dict())

# criar o modelo, com tratamento de desbalanceamento
modelo = LogisticRegression(class_weight='balanced', max_iter=1000)

# treinar (o modelo aprende os pesos olhando o passado)
modelo.fit(X_treino, y_treino)

# prever no teste (dados que ele nunca viu)
previsoes = modelo.predict(X_teste)

print(classification_report(y_teste, previsoes))
print("---")
print("Empresas classificadas como ciclo-dependentes no teste:", previsoes.sum())

print("\nPesos aprendidos:")
for feature, peso in zip(feats_z, modelo.coef_[0]):
    print(f"  {feature}: {peso:.3f}")

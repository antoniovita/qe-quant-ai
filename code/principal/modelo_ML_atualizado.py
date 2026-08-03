import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

#=============================================================================
# MODELO DE ML - versão REFORMULADA
#=============================================================================
# MUDANÇA CENTRAL: o modelo antigo previa "é ciclo-dependente HOJE", que é um
# alvo DETERMINÍSTICO (o rótulo é uma fórmula fechada de EBIT, dívida e despesa
# do mesmo ano) -> não há o que aprender, o ML fracassava.
# Agora prevemos "esta empresa saudável VAI ENTRAR em ciclo-dependência no
# PRÓXIMO ano?" -> isso é genuinamente incerto e economicamente valioso
# (antecipa a fragilidade em vez de constatá-la).
#=============================================================================

df = pd.read_csv('base_fundamentalista_v2.csv')

#--- reconstrução do rótulo (igual ao arquivo de calibração, até o ESTADO_ANO) ---
df_rotulo = df[df['DIVIDA_BRUTA'] > 0].copy()
df_rotulo['DESPESA_TRATADA'] = df_rotulo['DESPESA_FINANCEIRA_ABS'].replace(0, np.nan)
df_rotulo['ICR_OBSERVADO'] = df_rotulo['EBIT'] / df_rotulo['DESPESA_TRATADA']

taxa_normalizada = 0.17
tolerancia_icr = 1.2
df_rotulo['DESPESA_CONTRAFACTUAL'] = df_rotulo['DIVIDA_BRUTA'] * taxa_normalizada
df_rotulo['ICR_CONTRAFACTUAL'] = df_rotulo['EBIT'] / df_rotulo['DESPESA_CONTRAFACTUAL']

condicoes = [
    df_rotulo['EBIT'] < 0,
    (df_rotulo['ICR_OBSERVADO'] > 1) & (df_rotulo['ICR_CONTRAFACTUAL'] < tolerancia_icr)
]
df_rotulo['ESTADO_ANO'] = np.select(condicoes, ['ja_fragil', 'ciclo_dependente'], default='saudavel')

#ordenar por empresa e ano é ESSENCIAL: as features de tendência e o alvo futuro
#usam shift(), que só faz sentido com as linhas de cada empresa em ordem cronológica
df_rotulo = df_rotulo.sort_values(['CD_CVM', 'ANO'])
g = df_rotulo.groupby('CD_CVM')   #agrupa por empresa, para os shifts não vazarem entre empresas

#=============================================================================
# FEATURES
#=============================================================================
# Duas famílias: NÍVEL (N_) = o estado da empresa hoje; TENDÊNCIA (T_) = como
# esse estado está MUDANDO. A tendência é o que dá poder ao modelo, pois
# deterioração é um PROCESSO (a empresa vai piorando ano a ano até virar frágil).
#=============================================================================

df_rotulo['EBIT_POSITIVO'] = df_rotulo['EBIT'].where(df_rotulo['EBIT'] > 0)

#--- FEATURES DE NÍVEL (estado atual) ---
df_rotulo['N_ALAVANCAGEM']   = df_rotulo['DIVIDA_LIQUIDA'] / df_rotulo['EBIT_POSITIVO']       #quanto deve vs o que gera
df_rotulo['N_ACCRUALS']      = (df_rotulo['LUCRO_LIQUIDO'] - df_rotulo['CAIXA_OPERACIONAL']) / df_rotulo['ATIVO_TOTAL']  #qualidade do lucro
df_rotulo['N_MARGEM']        = df_rotulo['EBIT'] / df_rotulo['RECEITA']                       #rentabilidade
df_rotulo['N_EBIT_DIVIDA']   = df_rotulo['EBIT'] / df_rotulo['DIVIDA_BRUTA']                  #proximidade do limiar do rótulo
df_rotulo['N_DIVIDA_ATIVO']  = df_rotulo['DIVIDA_BRUTA'] / df_rotulo['ATIVO_TOTAL']           #endividamento sobre ativos
df_rotulo['N_CAIXAOP_DIVIDA']= df_rotulo['CAIXA_OPERACIONAL'] / df_rotulo['DIVIDA_BRUTA']     #capacidade de pagar dívida com caixa

#--- FEATURES DE TENDÊNCIA (variação em 1 ano: a coisa está piorando?) ---
df_rotulo['T_MARGEM_VAR']     = df_rotulo['N_MARGEM'] - g['N_MARGEM'].shift(1)                #margem caindo?
df_rotulo['T_ALAVANCAGEM_VAR']= df_rotulo['N_ALAVANCAGEM'] - g['N_ALAVANCAGEM'].shift(1)      #alavancagem subindo?
df_rotulo['T_ICR_VAR']        = df_rotulo['ICR_OBSERVADO'] - g['ICR_OBSERVADO'].shift(1)      #cobertura encolhendo?
df_rotulo['T_EBITDIV_VAR']    = df_rotulo['N_EBIT_DIVIDA'] - g['N_EBIT_DIVIDA'].shift(1)      #caminhando para o limiar?

#crescimento de dívida menos crescimento de receita: dívida crescendo mais rápido = insustentável
df_rotulo['CRESC_DIVIDA']  = (df_rotulo['DIVIDA_BRUTA'] - g['DIVIDA_BRUTA'].shift(1)) / g['DIVIDA_BRUTA'].shift(1)
df_rotulo['CRESC_RECEITA'] = (df_rotulo['RECEITA'] - g['RECEITA'].shift(1)) / g['RECEITA'].shift(1)
df_rotulo['T_DIV_MENOS_REC']= df_rotulo['CRESC_DIVIDA'] - df_rotulo['CRESC_RECEITA']

#--- FEATURES DE TENDÊNCIA (variação em 2 anos: aceleração da deterioração) ---
df_rotulo['T_MARGEM_2A']  = df_rotulo['N_MARGEM'] - g['N_MARGEM'].shift(2)
df_rotulo['T_EBITDIV_2A'] = df_rotulo['N_EBIT_DIVIDA'] - g['N_EBIT_DIVIDA'].shift(2)

#--- FEATURE de sensibilidade ao juro: VARIAÇÃO do custo de dívida ---
#INTUIÇÃO: não é o NÍVEL do custo (estrutural - setor, porte - e VAZA, pois se liga
#à definição do rótulo via ICR observado), mas o MOVIMENTO. Custo subindo sinaliza:
#(1) dívida sensível ao juro sendo repassada = empresa exposta ao ciclo;
#(2) mercado de crédito encarecendo o crédito dela = risco piorando;
#(3) troca de dívida barata por cara = perda de barganha.
df_rotulo['CUSTO'] = df_rotulo['DESPESA_FINANCEIRA_ABS'] / df_rotulo['DIVIDA_BRUTA']
df_rotulo['T_CUSTO_VAR'] = df_rotulo['CUSTO'] - g['CUSTO'].shift(1)

#NOTA: o NÍVEL do custo de dívida foi REMOVIDO de propósito (vazava - teve peso -12
#no modelo antigo). Só a VARIAÇÃO entra, que é a parte limpa e informativa.

feats = ['N_ALAVANCAGEM','N_ACCRUALS','N_MARGEM','N_EBIT_DIVIDA','N_DIVIDA_ATIVO','N_CAIXAOP_DIVIDA',
         'T_MARGEM_VAR','T_ALAVANCAGEM_VAR','T_ICR_VAR','T_EBITDIV_VAR','T_DIV_MENOS_REC',
         'T_MARGEM_2A','T_EBITDIV_2A','T_CUSTO_VAR']

#--- TRATAMENTOS (iguais aos de antes: infinitos -> NaN, winsorização, z-score) ---
df_rotulo[feats] = df_rotulo[feats].replace([np.inf, -np.inf], np.nan)
for f in feats:
    p1, p99 = df_rotulo[f].quantile(0.01), df_rotulo[f].quantile(0.99)
    df_rotulo[f] = df_rotulo[f].clip(lower=p1, upper=p99)          #winsorização: apara outliers
    df_rotulo[f + '_Z'] = (df_rotulo[f] - df_rotulo[f].mean()) / df_rotulo[f].std()  #z-score
feats_z = [f + '_Z' for f in feats]
df_rotulo[feats_z] = df_rotulo[feats_z].fillna(0)                  #NaN vira 0 = comportamento médio

#=============================================================================
# O ALVO: prever a ENTRADA em ciclo-dependência no próximo ano
#=============================================================================
#shift(-1) pega o estado do PRÓXIMO ano da mesma empresa (o -1 olha para frente)
df_rotulo['ESTADO_PROXIMO'] = g['ESTADO_ANO'].shift(-1)
df_rotulo['ALVO'] = (df_rotulo['ESTADO_PROXIMO'] == 'ciclo_dependente').astype(float)
df_rotulo.loc[df_rotulo['ESTADO_PROXIMO'].isna(), 'ALVO'] = np.nan   #último ano de cada empresa não tem "próximo"

#AMOSTRA: só empresas SAUDÁVEIS hoje. As já-frágeis (EBIT<0) NUNCA podem virar
#ciclo-dependentes (isso exige ICR observado > 1, logo EBIT positivo). Incluí-las
#poluiria o modelo com empresas incapazes de realizar o alvo (ex: em recuperação judicial).
amostra = df_rotulo[(df_rotulo['ESTADO_ANO'] == 'saudavel') & (df_rotulo['ALVO'].notna())].copy()

#=============================================================================
# MATRIZ DE TRANSIÇÃO: como os estados evoluem de um ano para o outro
#=============================================================================
#Mede a PERSISTÊNCIA de cada estado: uma empresa num estado hoje vira qual no
#próximo ano? shift(-1) pega o estado do ANO SEGUINTE da mesma empresa.
#normalize='index' faz cada LINHA somar 100% (vira "das que estavam no estado X,
#quantos % foram para cada estado no ano seguinte").
df_rotulo['ESTADO_PROXIMO'] = df_rotulo.groupby('CD_CVM')['ESTADO_ANO'].shift(-1)
matriz_transicao = pd.crosstab(df_rotulo['ESTADO_ANO'], df_rotulo['ESTADO_PROXIMO'], normalize='index')

print("\nMATRIZ DE TRANSICAO (linha = hoje, coluna = proximo ano, em %):")
print((matriz_transicao * 100).round(1).to_string())
#LEITURA: a diagonal é a persistência. Ciclo-dependente persiste só ~45% -> estado
#transitório, o que (1) explica o ML modesto - alvo volátil é difícil de prever,
#(2) justifica rebalancear a carteira com frequência - metade "sai" do estado em 1 ano.

#=============================================================================
# TREINO E AVALIAÇÃO
#=============================================================================
treino = amostra[amostra['ANO'] <= 2021]     #passado: o modelo aprende aqui
teste  = amostra[amostra['ANO'] >= 2022].copy()  #futuro: avalia em dados nunca vistos

X_treino, y_treino = treino[feats_z], treino['ALVO']
X_teste,  y_teste  = teste[feats_z],  teste['ALVO']

modelo = LogisticRegression(class_weight='balanced', max_iter=2000)
modelo.fit(X_treino, y_treino)

#predict_proba dá a PROBABILIDADE (o score contínuo), não a decisão binária.
#[:,1] pega a coluna da classe 1 (probabilidade de entrar em ciclo-dependência).
#Usamos o RANKING por esse score (as N mais prováveis), não o corte de 0,5 -
#é assim que a estratégia vai montar a carteira (as top-N mais frágeis).
teste['SCORE'] = modelo.predict_proba(X_teste)[:, 1]

#AUC: mede a capacidade de ORDENAR (0,5 = aleatório, quanto maior melhor)
auc = roc_auc_score(y_teste, teste['SCORE'])
taxa_base = y_teste.mean() * 100
print(f"AUC: {auc:.3f}  (0.5 = aleatório) | taxa base: {taxa_base:.1f}%\n")

#LIFT: quantas vezes o topo do ranking é melhor que o acaso
ordenado = teste.sort_values('SCORE', ascending=False)
print(f"{'Top N':<8}{'Acertos':<10}{'Precisao':<12}{'Lift'}")
for n in [10, 20, 30, 50]:
    ac = int(ordenado.head(n)['ALVO'].sum())
    prec = ac/n*100
    print(f"{n:<8}{ac:<10}{prec:>6.1f}%{prec/taxa_base:>10.2f}x")

#SANITY CHECK: os pesos batem com a teoria econômica?
print("\nPesos aprendidos (ordenados por magnitude):")
for f, p in sorted(zip(feats_z, modelo.coef_[0]), key=lambda x: -abs(x[1])):
    print(f"  {f:22}: {p:+.3f}")

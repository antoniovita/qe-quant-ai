"""
================================================================================
 PIPELINE CVM v2 — base fundamentalista EXPANDIDA (8 contas), 2013-2025.
================================================================================
 Extrai de cada ano (DFP anual, consolidado):
   DRE  -> EBIT, Despesa Financeira, Receita, Lucro Líquido
   BPP  -> Dívida Bruta (empréstimos circ + não circ)
   BPA  -> Caixa e Equivalentes, Ativo Total
   DFC  -> Caixa Operacional (método indireto)

 Cada conta é localizada pela regra AUDITADA no arquivo real (código quando
 estável; texto quando o código é ambíguo). Ver comentários em cada extração.

 Uso:
   pip install pandas requests
   python pipeline_cvm_v2.py
 Se os zips já estão em cache_cvm/, não rebaixa.
 Saída: base_fundamentalista_v2.csv
================================================================================
"""
import zipfile
import requests
import pandas as pd
import numpy as np
from pathlib import Path

# ---------------- CONFIGURAÇÃO ----------------
ANO_INICIO = 2013
ANO_FIM = 2025
PASTA_CACHE = Path("cache_cvm")
PASTA_CACHE.mkdir(exist_ok=True)
SAIDA = "base_fundamentalista_v2.csv"
BASE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/"


# ---------------- DOWNLOAD (com cache) ----------------
def baixar_zip(ano):
    nome = f"dfp_cia_aberta_{ano}.zip"
    destino = PASTA_CACHE / nome
    if destino.exists():
        print(f"  [cache] {nome}")
        return destino
    url = BASE_URL + nome
    print(f"  baixando {url} ...")
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=120)
    r.raise_for_status()
    destino.write_bytes(r.content)
    print(f"  salvo ({len(r.content)/1e6:.1f} MB)")
    return destino


def ler_csv_do_zip(caminho_zip, nome_interno):
    with zipfile.ZipFile(caminho_zip) as z:
        if nome_interno not in z.namelist():
            return None
        with z.open(nome_interno) as f:
            return pd.read_csv(f, sep=";", encoding="ISO-8859-1", dtype=str)


# ---------------- TRATAMENTO BASE (comum a todos os arquivos) ----------------
def tratar_bruto(df):
    """Filtra ÚLTIMO exercício, normaliza escala p/ reais, ano cheio, versão."""
    df = df[df["ORDEM_EXERC"] == "ÚLTIMO"].copy()
    df["VL_CONTA"] = pd.to_numeric(df["VL_CONTA"], errors="coerce")
    df["VL_REAIS"] = df["VL_CONTA"] * np.where(df["ESCALA_MOEDA"] == "MIL", 1000, 1)
    # DRE/DFC são FLUXO (têm DT_INI_EXERC): manter só ano cheio (início jan).
    # BPP/BPA são ESTOQUE (foto de 31/dez): não têm DT_INI_EXERC.
    if "DT_INI_EXERC" in df.columns:
        df["DT_INI"] = pd.to_datetime(df["DT_INI_EXERC"], errors="coerce")
        mask = df["DT_INI"].dt.month.eq(1) & df["DT_INI"].dt.day.eq(1)
        df = df[mask | df["DT_INI"].isna()].copy()
    df["VERSAO"] = pd.to_numeric(df["VERSAO"], errors="coerce")
    df = df.sort_values("VERSAO").drop_duplicates(
        subset=["CD_CVM", "DT_REFER", "CD_CONTA", "DS_CONTA"], keep="last")
    df["CD_CVM"] = pd.to_numeric(df["CD_CVM"], errors="coerce")
    return df


def por_texto(df, texto, nome, menor_nivel=False):
    """Extrai conta casando por DS_CONTA (texto exato). menor_nivel=True pega
    o registro com CD_CONTA de menor profundidade (evita subcontas)."""
    m = df["DS_CONTA"].str.strip().str.lower() == texto.lower()
    sub = df[m].copy()
    if menor_nivel:
        sub["nivel"] = sub["CD_CONTA"].str.count(r"\.")
        sub = sub.sort_values("nivel").drop_duplicates("CD_CVM", keep="first")
    return (sub.groupby("CD_CVM")["VL_REAIS"].first().rename(nome))


def por_codigo(df, codigos, nome):
    """Extrai casando por CD_CONTA exato. Se lista, SOMA (ex: dívida circ+ncirc)."""
    if isinstance(codigos, str):
        codigos = [codigos]
    sub = df[df["CD_CONTA"].isin(codigos)]
    return (sub.groupby("CD_CVM")["VL_REAIS"].sum().rename(nome))


# ---------------- PROCESSAR UM ANO ----------------
def cadastro_datas(zpath, ano):
    """Lê o arquivo de cadastro (metadados) do zip e retorna, por empresa,
    a DATA DE REFERÊNCIA (DT_REFER, fim do exercício) e a DATA DE PUBLICAÇÃO
    (DT_RECEB, quando o dado ficou público na CVM). A DT_RECEB é essencial para
    evitar look-ahead bias no backtest: só se pode usar o demonstrativo a partir
    dela. Casa pela versão mais recente de cada empresa-exercício."""
    cad = ler_csv_do_zip(zpath, f"dfp_cia_aberta_{ano}.csv")
    if cad is None:
        return None
    cad["CD_CVM"] = pd.to_numeric(cad["CD_CVM"], errors="coerce")
    cad["VERSAO"] = pd.to_numeric(cad["VERSAO"], errors="coerce")
    cad = cad.sort_values("VERSAO").drop_duplicates(["CD_CVM", "DT_REFER"], keep="last")
    return cad.set_index("CD_CVM")[["DT_REFER", "DT_RECEB"]]


def processar_ano(ano):
    zpath = baixar_zip(ano)
    dre = ler_csv_do_zip(zpath, f"dfp_cia_aberta_DRE_con_{ano}.csv")
    bpp = ler_csv_do_zip(zpath, f"dfp_cia_aberta_BPP_con_{ano}.csv")
    bpa = ler_csv_do_zip(zpath, f"dfp_cia_aberta_BPA_con_{ano}.csv")
    dfc = ler_csv_do_zip(zpath, f"dfp_cia_aberta_DFC_MI_con_{ano}.csv")
    datas = cadastro_datas(zpath, ano)
    if any(x is None for x in (dre, bpp, bpa, dfc)):
        print(f"  [aviso] {ano}: algum arquivo consolidado faltando")
        return None

    dre, bpp, bpa, dfc = map(tratar_bruto, (dre, bpp, bpa, dfc))

    # --- DRE (texto p/ contas de código instável; código p/ lucro líquido) ---
    ebit = por_texto(dre, "Resultado Antes do Resultado Financeiro e dos Tributos", "EBIT")
    desp = por_texto(dre, "Despesas Financeiras", "DESPESA_FINANCEIRA")
    receita = por_texto(dre, "Receita de Venda de Bens e/ou Serviços", "RECEITA")
    lucro = por_codigo(dre, "3.11", "LUCRO_LIQUIDO")

    # --- BPP: dívida = totais nível 2 (evita dupla contagem c/ subcontas) ---
    divida = por_codigo(bpp, ["2.01.04", "2.02.01"], "DIVIDA_BRUTA")

    # --- BPA: ativo total por código (estável); caixa por texto (1.01 ambíguo) ---
    ativo = por_codigo(bpa, "1", "ATIVO_TOTAL")
    caixa = por_texto(bpa, "Caixa e Equivalentes de Caixa", "CAIXA", menor_nivel=True)

    # --- DFC-MI: caixa operacional por código 6.01 (texto varia) ---
    caixa_op = por_codigo(dfc, "6.01", "CAIXA_OPERACIONAL")

    # nomes das empresas (da DRE)
    nomes = dre.groupby("CD_CVM")["DENOM_CIA"].first()

    base = pd.concat([nomes, ebit, desp, receita, lucro, divida,
                      ativo, caixa, caixa_op], axis=1)
    base = base[base["EBIT"].notna()].copy()   # sem EBIT = financeira/incompleta
    base["ANO"] = ano
    base["DESPESA_FINANCEIRA_ABS"] = base["DESPESA_FINANCEIRA"].abs()
    base["DIVIDA_LIQUIDA"] = base["DIVIDA_BRUTA"] - base["CAIXA"]
    # juntar DT_REFER (fim do exercício) e DT_RECEB (data de publicação).
    # DT_RECEB é o que permite point-in-time no backtest (evita look-ahead).
    if datas is not None:
        base = base.join(datas, how="left")
    return base.reset_index()


def main():
    partes = []
    for ano in range(ANO_INICIO, ANO_FIM + 1):
        print(f"\n=== DFP {ano} ===")
        try:
            p = processar_ano(ano)
            if p is not None:
                partes.append(p)
                print(f"  {ano}: {len(p)} empresas")
        except Exception as e:
            print(f"  [ERRO] {ano}: {e}")

    if not partes:
        print("Nada processado.")
        return
    cons = pd.concat(partes, ignore_index=True).sort_values(["DENOM_CIA", "ANO"])
    cons.to_csv(SAIDA, index=False, encoding="utf-8")
    print(f"\n{'='*60}\nSALVO: {SAIDA}")
    print(f"Linhas: {len(cons):,} | Empresas: {cons['CD_CVM'].nunique()} "
          f"| Anos: {cons['ANO'].min()}-{cons['ANO'].max()}")
    print(f"Colunas: {list(cons.columns)}")


if __name__ == "__main__":
    main()

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

RISCO_DICT = {
    "C100": "Baixo",
    "C101": "Alto",
    "C102": "Médio",
    "C103": "Baixo",
    "C104": "Alto",
}


def carregar_transacoes(caminho: Path) -> pd.DataFrame:
    """Lê transacoes.csv respeitando o encoding latin1."""
    return pd.read_csv(caminho, encoding="latin1")


def carregar_cotacoes(caminho: Path) -> pd.DataFrame:
    """Lê o arquivo auxiliar de cotações."""
    cotacoes = pd.read_csv(caminho, encoding="utf-8")
    cotacoes["data"] = pd.to_datetime(cotacoes["data"])
    return cotacoes


def limpar_e_transformar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1) Imputação da mediana de valor por estado.
    medianas_por_estado = df.groupby("estado_cliente")["valor"].transform("median")
    df["valor"] = df["valor"].fillna(medianas_por_estado)

    # 2) Rastreabilidade do pipeline.
    df["plataforma"] = "Mobile"

    # 3) Conversão temporal + timezone.
    df["data_transacao"] = pd.to_datetime(df["data_transacao"])
    df["data_transacao"] = df["data_transacao"].dt.tz_localize(
        "America/Sao_Paulo"
    )

    # 4) Novas colunas temporais utilizando o acessor .dt.
    df["dia_semana"] = df["data_transacao"].dt.day_name()
    df["mes"] = df["data_transacao"].dt.month

    # 5) Remove duplicatas, mantendo a primeira ocorrência.
    df = df.drop_duplicates(keep="first").copy()

    # 6) Mapeia risco do cliente com .map().
    df["nivel_risco"] = df["id_cliente"].map(RISCO_DICT).fillna("Não classificado")

    return df


def filtrar_transacoes_setembro(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtro obrigatoriamente vetorizado com operadores bitwise:
    setembro AND (SP OR RJ) AND valor > 5000.
    """
    filtro = (
        (df["mes"] == 9)
        & (
            (df["estado_cliente"] == "SP")
            | (df["estado_cliente"] == "RJ")
        )
        & (df["valor"] > 5000)
    )
    return df.loc[filtro].copy()


def criar_pivot_risco(df: pd.DataFrame) -> pd.DataFrame:
    return pd.pivot_table(
        df,
        index="mes",
        columns="nivel_risco",
        values="valor",
        aggfunc="sum",
        margins=True,
        margins_name="Total",
        fill_value=0,
    )


def adicionar_zscore_por_estado(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula Z-Score por estado de forma vetorizada, sem laços for:
    Z = (x - média_do_estado) / desvio_padrão_do_estado
    """
    df = df.copy()

    medias = df.groupby("estado_cliente")["valor"].transform("mean")
    desvios = df.groupby("estado_cliente")["valor"].transform("std")

    # Evita divisão por zero em grupos de variância nula.
    desvios = desvios.replace(0, np.nan)

    df["z_score"] = ((df["valor"] - medias) / desvios).fillna(0)
    return df


def detectar_anomalias(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[df["z_score"] > 2.5].copy()


def consolidar_com_cotacoes(
    transacoes: pd.DataFrame, cotacoes: pd.DataFrame
) -> pd.DataFrame:
    """
    Consolida os dois arquivos gerados pelo script anexo por data.
    Esta etapa é complementar aos requisitos principais.
    """
    transacoes = transacoes.copy()
    transacoes["data"] = (
        transacoes["data_transacao"]
        .dt.tz_localize(None)
        .dt.normalize()
    )

    consolidado = transacoes.merge(
        cotacoes,
        how="left",
        on="data",
        validate="many_to_one",
    )

    consolidado["valor_usd"] = (
        consolidado["valor"] / consolidado["cotacao_usd"]
    )

    return consolidado


def gerar_grafico(df: pd.DataFrame, caminho_saida: Path) -> pd.DataFrame:
    """
    Gera gráfico usando a API orientada a objetos do Matplotlib.
    """
    total_diario = (
        df.set_index("data_transacao")["valor"]
        .resample("D")
        .sum()
        .rename("total_diario")
        .to_frame()
    )

    total_diario["media_movel_7d"] = (
        total_diario["total_diario"].rolling(7).mean()
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(
        total_diario.index,
        total_diario["total_diario"],
        label="Valor total diário",
    )
    ax.plot(
        total_diario.index,
        total_diario["media_movel_7d"],
        label="Média móvel de 7 dias",
    )

    ax.set_ylim(bottom=0)
    ax.set_title("Desempenho diário das transações")
    ax.set_xlabel("Data")
    ax.set_ylabel("Valor total (R$)")
    ax.legend()
    ax.grid(alpha=0.25)

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(caminho_saida, dpi=150)
    plt.close(fig)

    return total_diario


def exportar_resultados(
    tratadas: pd.DataFrame,
    filtradas: pd.DataFrame,
    pivot: pd.DataFrame,
    anomalias: pd.DataFrame,
    consolidado: pd.DataFrame,
    serie_diaria: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    tratadas.to_csv(
        OUTPUT_DIR / "transacoes_tratadas.csv",
        index=False,
        encoding="utf-8-sig",
    )
    filtradas.to_csv(
        OUTPUT_DIR / "filtro_setembro_sp_rj_maior_5000.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pivot.to_csv(
        OUTPUT_DIR / "pivot_risco.csv",
        encoding="utf-8-sig",
    )
    anomalias.to_csv(
        OUTPUT_DIR / "anomalias_zscore.csv",
        index=False,
        encoding="utf-8-sig",
    )
    consolidado.to_csv(
        OUTPUT_DIR / "transacoes_com_cotacao.csv",
        index=False,
        encoding="utf-8-sig",
    )
    serie_diaria.to_csv(
        OUTPUT_DIR / "serie_diaria_media_movel.csv",
        encoding="utf-8-sig",
    )


def exibir_resumo(
    original: pd.DataFrame,
    tratadas: pd.DataFrame,
    filtradas: pd.DataFrame,
    pivot: pd.DataFrame,
    anomalias: pd.DataFrame,
) -> None:
    print("\n=== RELATÓRIO RESUMIDO ===")
    print(f"Registros carregados: {len(original)}")
    print(f"Registros após limpeza de duplicatas: {len(tratadas)}")
    print(
        "Filtro setembro + SP/RJ + valor > R$ 5.000: "
        f"{len(filtradas)} registros"
    )
    print(f"Potenciais anomalias com Z-Score > 2.5: {len(anomalias)}")
    print("\nTabela dinâmica por mês e nível de risco:")
    print(pivot)
    print(f"\nArquivos gerados em: {OUTPUT_DIR}")


def main() -> None:
    caminho_transacoes = BASE_DIR / "transacoes.csv"
    caminho_cotacoes = BASE_DIR / "cotacoes.csv"

    if not caminho_transacoes.exists() or not caminho_cotacoes.exists():
        raise FileNotFoundError(
            "Arquivos transacoes.csv e/ou cotacoes.csv não encontrados. "
            "Execute primeiro: python criar_dados.py"
        )

    original = carregar_transacoes(caminho_transacoes)
    cotacoes = carregar_cotacoes(caminho_cotacoes)

    tratadas = limpar_e_transformar(original)
    filtradas = filtrar_transacoes_setembro(tratadas)

    pivot = criar_pivot_risco(tratadas)

    tratadas_z = adicionar_zscore_por_estado(tratadas)
    anomalias = detectar_anomalias(tratadas_z)

    consolidado = consolidar_com_cotacoes(tratadas_z, cotacoes)

    serie_diaria = gerar_grafico(
        tratadas_z,
        OUTPUT_DIR / "relatorio_transacoes.png",
    )

    exportar_resultados(
        tratadas=tratadas_z,
        filtradas=filtradas,
        pivot=pivot,
        anomalias=anomalias,
        consolidado=consolidado,
        serie_diaria=serie_diaria,
    )

    exibir_resumo(
        original=original,
        tratadas=tratadas_z,
        filtradas=filtradas,
        pivot=pivot,
        anomalias=anomalias,
    )


if __name__ == "__main__":
    main()

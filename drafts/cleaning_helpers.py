import pandas as pd

ordner = "../data/raw_data/socioeconomic_factors/time_series_socio_factors/"

register = pd.read_csv(
    "../data/raw_data/geographic_reference/bfs_municipalities/BFS_Gemeindeverzeichnis_2026-01-01.csv"
)
zh_gemeinden = register[(register["Level"] == 3) & (register["BfsCode"] <= 298)]


def clean_datei(dateiname, neuer_name):
    df = pd.read_csv(ordner + dateiname)
    df = df.drop(columns=["Unnamed: 11"])
    df = df[df["BFS_NR"] != 0]
    df = df[df["BFS_NR"].isin(zh_gemeinden["BfsCode"])]
    df = df[["BFS_NR", "INDIKATOR_JAHR", "INDIKATOR_VALUE"]]
    df = df.rename(
        columns={
            "BFS_NR": "GDENR",
            "INDIKATOR_JAHR": "year",
            "INDIKATOR_VALUE": neuer_name,
        }
    )
    return df

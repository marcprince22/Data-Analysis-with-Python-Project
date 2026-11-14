# This script cleans the Zurich socioeconomic time series and merges them
# into one panel (one row per municipality and year).
#
# Input:  data/raw_data/socioeconomic_factors/time_series_socio_factors/
#         data/raw_data/geographic_reference/bfs_municipalities/BFS_Gemeindeverzeichnis_2026-01-01.csv
# Output: data/clean_data/zh_socioeconomic_panel.csv

from pathlib import Path
import pandas as pd


# Paths, built from the location of this script so it runs on every device
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_FOLDER = PROJECT_ROOT / "data" / "raw_data" / "socioeconomic_factors" / "time_series_socio_factors"
REGISTER_FILE = PROJECT_ROOT / "data" / "raw_data" / "geographic_reference" / "bfs_municipalities" / "BFS_Gemeindeverzeichnis_2026-01-01.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "clean_data" / "zh_socioeconomic_panel.csv"


# register lists all municipalities which still exist in 2026
register = pd.read_csv(REGISTER_FILE)
# filter for municipalities via Level and for Zurich via BfsCode
zh_gemeinden = register[(register["Level"] == 3) & (register["BfsCode"] <= 298)]


# cleaning steps for one Gemeindeporträt file
def clean_datei(dateiname, neuer_name):
    df = pd.read_csv(RAW_FOLDER / dateiname)
    df = df.drop(columns=["Unnamed: 11"])                 # empty column
    df = df[df["BFS_NR"] != 0]                            # drop districts, regions, canton
    df = df[df["BFS_NR"].isin(zh_gemeinden["BfsCode"])]   # keep only municipalities of 2026
    df = df[["BFS_NR", "INDIKATOR_JAHR", "INDIKATOR_VALUE"]]
    df = df.rename(columns={
        "BFS_NR": "GDENR",
        "INDIKATOR_JAHR": "year",
        "INDIKATOR_VALUE": neuer_name
    })
    return df


def main():
    # Gemeindeporträt files
    foreigner = clean_datei("Ausländeranteil_1978–2025_ZH_per_mun.csv", "foreigner_rate")
    social = clean_datei("Sozialhilfequote_2007–2024_ZH_per_mun.csv", "social_assistance_rate")
    unemployment = clean_datei("Arbeitslosenanteil_15–64_2011–2024_ZH_per_mun.csv", "unemployment_rate")
    income = clean_datei("Steuerb.Einkommen_Median_1999–2022_ZH_per_mun.csv", "median_income")
    old_age = clean_datei("Altersquotient_1998–2025_ZH_per_mun.csv", "old_age_ratio")
    density = clean_datei("Bevölkerungsdichte_1962–2025_ZH_per_mun.csv", "population_density")

    # education file (different layout, separator ";")
    tertiary = pd.read_csv(RAW_FOLDER / "education.csv", sep=";")
    tertiary = tertiary[tertiary["GDENR"] <= 298]         # keep only Zurich
    tertiary = tertiary[["GDENR", "ERHJAHR", "TERTIARY"]]
    tertiary = tertiary.rename(columns={
        "ERHJAHR": "year",
        "TERTIARY": "tertiary_share"
    })

    # merge all factors on municipality and year, keep all rows
    panel = foreigner.merge(social, on=["GDENR", "year"], how="outer")
    panel = panel.merge(unemployment, on=["GDENR", "year"], how="outer")
    panel = panel.merge(tertiary, on=["GDENR", "year"], how="outer")
    panel = panel.merge(income, on=["GDENR", "year"], how="outer")
    panel = panel.merge(old_age, on=["GDENR", "year"], how="outer")
    panel = panel.merge(density, on=["GDENR", "year"], how="outer")

    # checks: stop the script if something is wrong
    if panel.duplicated(subset=["GDENR", "year"]).sum() != 0:
        raise ValueError("There are duplicate municipality-year rows")
    if panel["GDENR"].nunique() != 160:
        raise ValueError("The panel does not contain exactly 160 municipalities")

    panel = panel.sort_values(["GDENR", "year"])
    panel.to_csv(OUTPUT_FILE, index=False)

    print("Saved", OUTPUT_FILE.name, panel.shape)


if __name__ == "__main__":
    main()

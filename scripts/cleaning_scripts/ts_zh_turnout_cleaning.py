from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "data" / "clean_data" / "voting_turnout_clean.csv.zip"
OUTPUT_FILE = PROJECT_ROOT / "data" / "clean_data" / "ts_zh_turnout_clean.csv"


def main():

    vt = pd.read_csv(
        INPUT_FILE, dtype={"GDENR": str}, na_values="...", low_memory=False
    )

    df = vt[vt["Geografietyp"] == "Gemeinde"]
    df = df[df["Kanton"] == "Zürich"]
    df = df[df["Sonderfall"] == False]

    df = df.copy()

    df["year"] = df["Datum und Vorlage"].str[:4]
    df["year"] = df["year"].astype(int)
    df["GDENR"] = df["GDENR"].astype(int)

    df = df[["GDENR", "year", "Beteiligung in %"]]
    df = df.rename(columns={"Beteiligung in %": "turnout"})

    turnout = df.groupby(["GDENR", "year"])["turnout"].mean()
    turnout = turnout.reset_index()

    if turnout.duplicated(subset=["GDENR", "year"]).sum() != 0:
        raise ValueError("There are duplicate municipality-year rows")
    if turnout["GDENR"].nunique() != 160:
        raise ValueError("The turnout data does not contain exactly 160 municipalities")

    turnout.to_csv(OUTPUT_FILE, index=False)

    print("Saved", OUTPUT_FILE.name, turnout.shape)


if __name__ == "__main__":
    main()

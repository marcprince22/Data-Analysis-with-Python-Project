from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TURNOUT_FILE = PROJECT_ROOT / "data" / "clean_data" / "ts_zh_turnout_clean.csv"
SOCIO_FILE = (
    PROJECT_ROOT / "data" / "clean_data" / "ts_zh_socioeconomic_panel_clean.csv"
)
OUTPUT_FILE = PROJECT_ROOT / "data" / "clean_data" / "zh_regression_panel.csv"


def main():
    turnout = pd.read_csv(TURNOUT_FILE)
    socio = pd.read_csv(SOCIO_FILE)

    panel = turnout.merge(socio, on=["GDENR", "year"], how="inner")

    if panel.duplicated(subset=["GDENR", "year"]).sum() != 0:
        raise ValueError("There are duplicate municipality-year rows")
    if panel["GDENR"].nunique() != 160:
        raise ValueError("The panel does not contain exactly 160 municipalities")

    panel = panel.sort_values(["GDENR", "year"])
    panel.to_csv(OUTPUT_FILE, index=False)

    print("Saved", OUTPUT_FILE.name, panel.shape)


if __name__ == "__main__":
    main()

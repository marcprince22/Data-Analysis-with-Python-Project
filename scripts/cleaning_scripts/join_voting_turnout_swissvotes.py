from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLEAN_DATA_DIR = PROJECT_ROOT / "data" / "clean_data"

TURNOUT_FILE = CLEAN_DATA_DIR / "voting_turnout_clean.csv"
CROSSWALK_FILE = CLEAN_DATA_DIR / "voting_turnout_swissvotes_crosswalk.csv"
OUTPUT_FILE = CLEAN_DATA_DIR / "voting_turnout_swissvotes_joined.csv"

JOIN_COLUMNS = ["Datum", "Vorlage"]


def join_swissvotes(chunk, crosswalk):
    chunk[JOIN_COLUMNS] = chunk["Datum und Vorlage"].str.extract(
        r"^(?P<Datum>\d{4}-\d{2}-\d{2})\s+(?P<Vorlage>.+)$"
    )
    chunk["Jahr"] = pd.to_datetime(chunk["Datum"], format="%Y-%m-%d").dt.year

    joined = chunk.merge(
        crosswalk,
        on=JOIN_COLUMNS,
        how="left",
        validate="many_to_one",
    )

    missing_id = joined["Swissvotes_ID"].isna()
    if missing_id.any():
        examples = joined.loc[missing_id, "Datum und Vorlage"].drop_duplicates()
        raise ValueError(f"Missing Swissvotes IDs for: {examples.head(5).tolist()}")

    return joined


def main():
    crosswalk = pd.read_csv(
        CROSSWALK_FILE,
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
    )

    temporary_output = OUTPUT_FILE.with_suffix(".csv.tmp")
    rows_written = 0

    with (
        pd.read_csv(
            TURNOUT_FILE,
            dtype={"GDENR": str},
            chunksize=100_000,
        ) as reader,
        temporary_output.open("w", encoding="utf-8", newline="") as output,
    ):
        for chunk_number, chunk in enumerate(reader):
            joined = join_swissvotes(chunk, crosswalk)
            joined.to_csv(output, index=False, header=chunk_number == 0)
            rows_written += len(joined)

    temporary_output.replace(OUTPUT_FILE)
    print(f"Wrote {rows_written:,} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

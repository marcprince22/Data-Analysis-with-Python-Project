from io import TextIOWrapper
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLEAN_DATA_DIR = PROJECT_ROOT / "data" / "clean_data"

INPUT_FILE = CLEAN_DATA_DIR / "voting_turnout_swissvotes_joined.csv.zip"
OUTPUT_FILE = CLEAN_DATA_DIR / "voting_turnout_municipalities.csv.zip"

OUTPUT_COLUMNS = {
    "Name": "Gemeinde",
    "GDENR": "BFS Gemeindecode",
    "Datum": "Datum",
    "Jahr": "Jahr",
    "Rechtsform_Code": "Rechtsform",
    "Titel_offiziell_Swissvotes": "Titel",
}

LEGAL_FORM_LABELS = {
    "1": "Obligatorisches Referendum",
    "2": "Fakultatives Referendum",
    "3": "Volksinitiative",
    "4": "Direkter Gegenentwurf zu einer Volksinitiative",
    "5": "Stichfrage",
}


# Filter municipal rows and export
def main():
    temporary_output = OUTPUT_FILE.with_suffix(".zip.tmp")
    rows_written = 0

    with (
        pd.read_csv(
            INPUT_FILE,
            usecols=[*OUTPUT_COLUMNS, "Geografietyp", "Sonderfall"],
            dtype={"GDENR": str, "Rechtsform_Code": str},
            chunksize=100_000,
        ) as reader,
        ZipFile(
            temporary_output,
            mode="w",
            compression=ZIP_DEFLATED,
        ) as archive,
        archive.open(OUTPUT_FILE.stem, mode="w") as member,
        TextIOWrapper(member, encoding="utf-8-sig", newline="") as output,
    ):
        for chunk_number, chunk in enumerate(reader):
            is_municipality = (
                chunk["Geografietyp"].eq("Gemeinde")
                & chunk["Sonderfall"].eq(False)
                & chunk["GDENR"].notna()
            )

            municipal = chunk.loc[is_municipality, list(OUTPUT_COLUMNS)]
            municipal = municipal.rename(columns=OUTPUT_COLUMNS)
            codes = municipal["Rechtsform"].str.strip()
            labels = codes.map(LEGAL_FORM_LABELS)

            if labels.isna().any():
                unknown = codes[labels.isna()].drop_duplicates().tolist()
                raise ValueError(
                    f"Unknown or missing Swissvotes legal forms: {unknown}"
                )

            municipal["Rechtsform"] = labels
            municipal.to_csv(
                output,
                sep=";",
                index=False,
                header=(chunk_number == 0),
            )
            rows_written += len(municipal)

    temporary_output.replace(OUTPUT_FILE)
    print(f"Wrote {rows_written:,} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

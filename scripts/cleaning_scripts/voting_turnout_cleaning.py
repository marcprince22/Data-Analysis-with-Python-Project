from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

TURNOUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw_data"
    / "voting_turnout"
    / "px-x-1703030000_101_20261105-145939.csv.zip"
)

BFS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw_data"
    / "geographic_reference"
    / "bfs_municipalities"
    / "BFS_Gemeindeverzeichnis_2026-01-01.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "clean_data"
OUTPUT_FILE = OUTPUT_DIR / "voting_turnout_clean.csv"

SPECIAL_TERMS = (
    "Ausland-CH",
    "Anderes",
    "Korrespondenzweg",
    "CH de l'étranger",
    "-autres",
    "CH-all'estero",
    "-altri",
    "-voto per corrispondenza",
)


# load municipalities file to join with turnoutfile. Bc in turnoutfile there are no municipality codes
def load_municipality_lookup():
    bfs = pd.read_csv(
        BFS_FILE,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    municipalities = bfs.loc[
        bfs["Level"].eq("3"),
        ["BfsCode", "Name"],
    ].copy()

    if municipalities["Name"].duplicated().any():
        raise ValueError("Municipality names are not unique in the BFS file.")

    if municipalities["BfsCode"].duplicated().any():
        raise ValueError("BFS municipality codes are not unique.")

    return dict(zip(municipalities["Name"], municipalities["BfsCode"]))


# Tidy up names of geographical instances
def parse_geography(raw_value):
    value = raw_value.strip()

    if value == "Schweiz":
        geography_type, name = "Schweiz", "Schweiz"
    elif value.startswith("- "):
        geography_type, name = "Kanton", value[2:]
    elif value.startswith(">>"):
        geography_type, name = "Bezirk", value[2:].strip()
    elif value.startswith("......"):
        geography_type, name = "Gemeinde", value[6:]
    else:
        raise ValueError(f"Unrecognized geography: {raw_value}")

    is_special = any(term in name for term in SPECIAL_TERMS)
    return geography_type, name, is_special


# Bc voting turnout file is too big use chunks. Add column with municipalitiy code
def add_geography_columns(chunk, municipality_lookup):
    parsed = [
        parse_geography(value)
        for value in chunk["Kanton (-) / Bezirk (>>) / Gemeinde (......)"]
    ]

    chunk[["Geografietyp", "Name", "Sonderfall"]] = pd.DataFrame(
        parsed,
        index=chunk.index,
        columns=["Geografietyp", "Name", "Sonderfall"],
    )

    chunk["GDENR"] = [
        municipality_lookup.get(name.partitition(" (Gemeinsame Urne,")[0].strip(), "")
        if geography_type == "Gemeinde" and not is_special
        else ""
        for geography_type, name, is_special in parsed
    ]

    return chunk


# For each geographical instance we add its canton. For Switherland there is "" added
def add_canton_column(chunk, current_canton):
    canton_names = []

    for geography_type, name in zip(
        chunk["Geografietyp"],
        chunk["Name"],
    ):
        if geography_type == "Kanton":
            current_canton = name

        if geography_type == "Schweiz":
            canton_names.append("")
        else:
            canton_names.append(current_canton or "")

    chunk["Kanton"] = canton_names
    return chunk, current_canton


def main():
    """
    preview = pd.read_csv(TURNOUT_FILE, encoding="cp1252", sep=";", nrows=5)
    print(preview.columns.tolist())
    print(preview.to_string(index=False))
    """

    municipality_lookup = load_municipality_lookup()
    current_canton = None
    unmatched_names = set()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with pd.read_csv(
        TURNOUT_FILE, sep=";", encoding="cp1252", chunksize=100_000
    ) as reader:
        for chunk_number, chunk in enumerate(reader):
            chunk = add_geography_columns(chunk, municipality_lookup)
            chunk, current_canton = add_canton_column(chunk, current_canton)

            unmatched = (
                chunk["Geografietyp"].eq("Gemeinde")
                & ~chunk["Sonderfall"]
                & chunk["GDENR"].eq("")
            )
            unmatched_names.update(chunk.loc[unmatched, "Name"])

            first_chunk = chunk_number == 0
            chunk.to_csv(
                OUTPUT_FILE,
                mode="w" if first_chunk else "a",
                header=first_chunk,
                index=False,
            )

    print(f"Cleaned data written to {OUTPUT_FILE}")
    print(f"Distinct municipality names without a BFS code: {len(unmatched_names)}")
    for name in sorted(unmatched_names):
        print(f"  {name}")


if __name__ == "__main__":
    main()

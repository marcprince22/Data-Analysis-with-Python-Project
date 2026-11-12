from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SWISSVOTES_FILE = (
    PROJECT_ROOT / "data" / "raw_data" / "voting_turnout" / "swissvotes.csv"
)
TURNOUT_FILE = PROJECT_ROOT / "data" / "clean_data" / "voting_turnout_clean.csv.zip"
CROSSWALK_FILE = (
    PROJECT_ROOT / "data" / "clean_data" / "voting_turnout_swissvotes_crosswalk.csv"
)

MANUAL_MATCHES_FILE = SWISSVOTES_FILE.with_name("swissvotes_manual_matches.csv")


def normalize_titles(titles):
    return (
        titles.fillna("")
        .str.lower()
        .str.replace("ä", "ae", regex=False)
        .str.replace("ö", "oe", regex=False)
        .str.replace("ü", "ue", regex=False)
        .str.replace(r"\bart\.\s*", "art.", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )


def load_swissvotes():
    columns = ["anr", "datum", "titel_off_d", "titel_kurz_d", "rechtsform"]

    for encoding in ("utf-8-sig", "cp1252"):
        try:
            swissvotes = pd.read_csv(
                SWISSVOTES_FILE,
                sep=";",
                encoding=encoding,
                dtype=str,
                usecols=columns,
            )
            break
        except UnicodeDecodeError:
            if encoding == "cp1252":
                raise

    swissvotes["Datum"] = pd.to_datetime(
        swissvotes["datum"],
        format="%d.%m.%Y",
    ).dt.strftime("%Y-%m-%d")

    return swissvotes


def build_title_lookup(swissvotes):
    titles = swissvotes.melt(
        id_vars=["anr", "Datum"],
        value_vars=["titel_off_d", "titel_kurz_d"],
        value_name="Titel",
    )

    titles["Titel_key"] = normalize_titles(titles["Titel"])

    return titles.loc[
        titles["Titel_key"].ne(""), ["Datum", "Titel_key", "anr"]
    ].drop_duplicates()


def load_turnout_proposals():
    proposal_parts = []

    with pd.read_csv(
        TURNOUT_FILE,
        usecols=["Geografietyp", "Datum und Vorlage"],
        chunksize=100_000,
    ) as reader:
        for chunk in reader:
            national_titles = chunk.loc[
                chunk["Geografietyp"].eq("Schweiz"),
                "Datum und Vorlage",
            ]
            if not national_titles.empty:
                proposal_parts.append(national_titles)

    if not proposal_parts:
        raise ValueError("No national proposals found in the turnout file.")

    raw_titles = pd.concat(proposal_parts, ignore_index=True).drop_duplicates()
    proposals = raw_titles.str.extract(
        r"^(?P<Datum>\d{4}-\d{2}-\d{2})\s+(?P<Vorlage>.+)$"
    )

    invalid = proposals["Datum"].isna()
    if invalid.any():
        examples = raw_titles.loc[invalid].head(5).tolist()
        raise ValueError(f"Could not split date and proposal: {examples}")

    proposals["Titel_key"] = normalize_titles(proposals["Vorlage"])
    return proposals


def match_turnout_proposals(proposals, title_lookup):
    join_columns = ["Datum", "Titel_key"]
    ambiguous = title_lookup.duplicated(subset=join_columns, keep=False)
    unique_lookup = title_lookup.loc[~ambiguous].rename(
        columns={"anr": "Swissvotes_ID"}
    )

    return proposals.merge(
        unique_lookup,
        on=join_columns,
        how="left",
        validate="many_to_one",
    )


def complete_crosswalk(matches, swissvotes):
    keys = ["Datum", "Vorlage"]
    id_column = "Swissvotes_ID"

    manual = pd.read_csv(
        MANUAL_MATCHES_FILE,
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
        usecols=keys + [id_column],
    )

    has_id = matches[id_column].notna()
    automatic = matches.loc[has_id, keys + [id_column]].assign(
        Zuordnung="Titelabgleich"
    )

    reviewed = matches.loc[~has_id, keys].merge(
        manual,
        on=keys,
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    if reviewed["_merge"].ne("both").any() or reviewed[id_column].isna().any():
        raise ValueError("Manual matches must cover exactly the open proposals.")

    reviewed = reviewed.drop(columns="_merge").assign(
        Zuordnung="Manuell anhand Datum und Vorlage geprüft"
    )
    crosswalk = pd.concat([automatic, reviewed], ignore_index=True)

    metadata = swissvotes[
        ["anr", "Datum", "titel_kurz_d", "titel_off_d", "rechtsform"]
    ].rename(
        columns={
            "anr": id_column,
            "titel_kurz_d": "Name_aus_Swissvotes",
            "titel_off_d": "Titel_offiziell_Swissvotes",
            "rechtsform": "Rechtsform_Code",
        }
    )

    crosswalk = crosswalk.merge(
        metadata,
        on=[id_column, "Datum"],
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    if crosswalk["_merge"].ne("both").any():
        raise ValueError(
            "At least one Swissvotes ID is missing or has a different date."
        )

    return crosswalk.drop(columns="_merge")


def main():
    swissvotes = load_swissvotes()
    title_lookup = build_title_lookup(swissvotes)
    proposals = load_turnout_proposals()
    matches = match_turnout_proposals(proposals, title_lookup)

    if not MANUAL_MATCHES_FILE.exists():
        review = matches.loc[
            matches["Swissvotes_ID"].isna(),
            ["Datum", "Vorlage", "Swissvotes_ID"],
        ]
        with MANUAL_MATCHES_FILE.open("x", encoding="utf-8-sig", newline="") as output:
            review.to_csv(output, sep=";", index=False)

        print(f"Exported {len(review)} open proposals to {MANUAL_MATCHES_FILE}")
        print("Fill in Swissvotes_ID and run this script again.")
        return

    crosswalk = complete_crosswalk(matches, swissvotes)
    crosswalk.to_csv(CROSSWALK_FILE, sep=";", encoding="utf-8-sig", index=False)
    print(f"Wrote {len(crosswalk)} proposals to {CROSSWALK_FILE}")
    print(crosswalk["Zuordnung"].value_counts().to_string())


if __name__ == "__main__":
    main()

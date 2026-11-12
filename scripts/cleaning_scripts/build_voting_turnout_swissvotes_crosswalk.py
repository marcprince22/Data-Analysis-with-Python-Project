from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SWISSVOTES_FILE = (
    PROJECT_ROOT / "data" / "raw_data" / "voting_turnout" / "swissvotes.csv"
)
TURNOUT_FILE = PROJECT_ROOT / "data" / "clean_data" / "voting_turnout_clean.csv"
CROSSWALK_FILE = (
    PROJECT_ROOT / "data" / "clean_data" / "voting_turnout_swissvotes_crosswalk.csv"
)


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


if __name__ == "__main__":
    swissvotes = load_swissvotes()
    title_lookup = build_title_lookup(swissvotes)
    proposals = load_turnout_proposals()
    matches = match_turnout_proposals(proposals, title_lookup)

    unmatched = matches.loc[
        matches["Swissvotes_ID"].isna(),
        ["Datum", "Vorlage"],
    ]
    review_file = (
        PROJECT_ROOT
        / "data"
        / "raw_data"
        / "voting_turnout"
        / "swissvotes_manual_matches.csv"
    )

    review = unmatched.copy()
    review["Swissvotes_ID"] = ""

    with review_file.open("x", encoding="utf-8-sig", newline="") as output:
        review.to_csv(output, sep=";", index=False)

    print(f"Exported {len(review)} proposals for manual review to {review_file}")

    print(f"National proposals: {len(matches)}")
    print(f"Automatic matches: {matches['Swissvotes_ID'].notna().sum()}")
    print(f"Open for review: {len(unmatched)}")
    print(unmatched.head(10).to_string(index=False))

# Voting turnout data preparation

    This workflow cleans the BFS voting turnout data, assigns BFS municipality
    codes (`GDENR`), and links each voting proposal to its Swissvotes ID.

    ## Requirements and inputs

    Use Python 3.10 or newer with `pandas` installed. Run the commands below
    from the repository root.

    | Input | Location |
    | --- | --- |
    | BFS voting turnout export (`.csv.zip`) | `data/raw_data/voting_turnout/` |
    | BFS municipality register (`BFS_Gemeindeverzeichnis_2026-01-01.csv`) | `data/raw_data/geographic_reference/bfs_municipalities/` |
    | Swissvotes dataset (`swissvotes.csv`) | `data/raw_data/voting_turnout/` |
    | Reviewed Swissvotes matches (`swissvotes_manual_matches.csv`) | `data/raw_data/voting_turnout/` |

    ## 1. Clean the voting turnout data

    ```bash
    python scripts/cleaning_scripts/voting_turnout_cleaning.py
    ```

    The script identifies the geographic level of each row, adds the canton,
    and assigns `GDENR` to regular municipality rows using the BFS register
    dated 1 January 2026. For municipalities with a shared ballot box, it
    uses the municipality name before the ballot-box annotation. Special
    categories, such as Swiss voters abroad, remain in the data and are
    flagged in `Sonderfall`.

    Output file → `data/clean_data/voting_turnout_clean.csv.zip`

    ## 2. Build the Swissvotes crosswalk

    ```bash
    python scripts/cleaning_scripts/build_voting_turnout_swissvotes_crosswalk.py
    ```

    The script matches national voting proposals to Swissvotes using the
    voting date and a normalised version of the official or short title.
    For the current input data, 414 of the 511 proposals match automatically.
    The remaining 97 use the reviewed IDs in `swissvotes_manual_matches.csv`.

    If the manual matches file is missing, the script creates a review list
    and stops. For each row, compare the date and proposal with
    `swissvotes.csv` and enter the matching `anr` in `Swissvotes_ID`.
    Keep `Datum` and `Vorlage` unchanged, then run the script again.
    The script checks that the manual list covers exactly the open proposals
    and that each ID exists in Swissvotes for the recorded date.

    Output file → `data/clean_data/voting_turnout_swissvotes_crosswalk.csv`

    ## 3. Join turnout data with Swissvotes

    ```bash
    python scripts/cleaning_scripts/join_voting_turnout_swissvotes.py
    ```

    The script joins the crosswalk to the turnout data by voting date and
    original proposal title. It checks that every turnout row receives a
    Swissvotes ID. For the current inputs, the output contains 1,207,493 rows.

    Output file → `data/clean_data/voting_turnout_swissvotes_joined.csv.zip`

    ## Use the output for analysis

    Pandas can read the final ZIP directly. The file includes national,
    cantonal, district, and municipal rows. For a municipality-level
    analysis, select rows with `Geografietyp == "Gemeinde"`,
    `Sonderfall == False`, and a populated `GDENR`. Check the values in
    `Beteiligung in %` before converting the column to a numeric type.

# Zurich socioeconomic time series

Cleans six Gemeindeporträt indicators of the Statistisches Amt Kanton Zürich
and the BFS education data, and merges them into one panel for the
160 Zurich municipalities of 1 January 2026.

    python scripts/cleaning_scripts/socioeconomic_factors_panel_cleaning.py

Inputs → `data/raw_data/socioeconomic_factors/time_series_socio_factors/`
and `BFS_Gemeindeverzeichnis_2026-01-01.csv`.

Steps: drop districts, regions and canton (`BFS_NR` 0); keep only
municipalities that exist in 2026 (drops merged "(bis ...)" municipalities);
keep municipality, year and value; merge all factors on `GDENR` and `year`.

Output → `data/clean_data/ts_zh_socioeconomic_panel_clean.csv`

| Column | Unit | Years |
| --- | --- | --- |
| `GDENR` | BFS municipality number | |
| `foreigner_rate` | % of population | 1978–2025 |
| `social_assistance_rate` | % of population | 2007–2024 |
| `unemployment_rate` | % of population aged 15–64 | 2011–2024 |
| `tertiary_share` | % of population aged 25–64 | 1990, 2000, 2017–2023 |
| `median_income` | CHF, taxable income | 1999–2022 |
| `old_age_ratio` | 65+ per 100 aged 20–64 | 1998–2025 |
| `population_density` | inhabitants per km² | 1962–2025 |

Known gaps: social assistance and unemployment are suppressed for some
small municipalities (privacy). For merged municipalities (codes 291–298),
some indicators only start in the merger year.

# Zurich turnout per municipality and year

This workflow takes the cleaned BFS turnout data (`data/clean_data/voting_turnout_clean.csv.zip`) and computes the average turnout per Zurich municipality and year.

```bash
python scripts/cleaning_scripts/ts_zh_turnout_cleaning.py
```

**Steps:**
1. Keep only rows with Geografietyp "Gemeinde", Kanton "Zürich" and Sonderfall False (no Swiss abroad).
2. Take the year from the first 4 characters of "Datum und Vorlage".
3. Average the turnout of all votes per municipality and year.
4. Checks: no duplicate GDENR × year rows, exactly 160 municipalities.

**Output:** `data/clean_data/ts_zh_turnout_clean.csv`

| Column  | Description                                   |
|---------|-----------------------------------------------|
| GDENR   | BFS municipality number (2026 municipalities) |
| year    | Year of the votes (1960–2026)                 |
| turnout | Mean turnout of all federal votes in that year, in % |

Municipalities that merged later (291–298) are already on the 2026 boundaries back to 1960.

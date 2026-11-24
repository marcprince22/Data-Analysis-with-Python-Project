import json
from math import expm1, log1p
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
YEAR = 2019
ZURICH_CANTON = 1
MAP_HEIGHT = 670

# Labels, display units and precision for each mapped indicator.
INDICATORS = {
    "turnout_2019": ("Ø Stimmbeteiligung", "%", 1),
    "population_density": ("Bevölkerungsdichte", "Einw./km²", 1),
    "share_age_0_19": ("Anteil 0–19 Jahre", "%", 1),
    "share_age_65plus": ("Anteil ab 65 Jahren", "%", 1),
    "share_foreign": ("Anteil ausländische Bevölkerung", "%", 1),
    "social_assistance_rate": ("Sozialhilfequote", "%", 1),
}
MAP_GRADIENT = ("#e0f5ed", "#17467a")
MISSING_COLOR = (145, 151, 160)

map_click = st.components.v2.component(
    "map_click",
    js=Path(__file__).with_name("map_click.mjs").read_text(encoding="utf-8"),
)


@st.cache_data
def load_map_data() -> tuple[pd.DataFrame, list[dict]]:
    indicators = pd.read_csv(DATA_DIR / "clean_data" / "regression_data.csv")
    votes = pd.read_csv(
        DATA_DIR / "clean_data" / "voting_turnout_swissvotes_joined.csv.zip",
        usecols=["GDENR", "Jahr", "Geografietyp", "Sonderfall", "Beteiligung in %"],
        low_memory=False,
    )
    votes = votes.loc[
        votes["Jahr"].eq(YEAR) & votes["Geografietyp"].eq("Gemeinde") & votes["Sonderfall"].eq(False)
    ].copy()
    votes["Beteiligung in %"] = pd.to_numeric(votes["Beteiligung in %"], errors="coerce")
    turnout = votes.groupby("GDENR")["Beteiligung in %"].agg(
        turnout_2019="mean", n_votes_2019="count"
    )
    indicators = indicators.set_index("GDENR").join(turnout, validate="one_to_one")

    with (DATA_DIR / "raw_data/app_data/municipalities_api_50m.geojson").open(encoding="utf-8") as file:
        features = json.load(file)["features"]

    municipal_features = [
        feature for feature in features
        if feature["properties"].get("kantonsnummer") is not None
    ]
    return indicators, municipal_features


def format_value(value: float, unit: str, digits: int) -> str:
    if pd.isna(value):
        return "Keine Angabe"
    formatted = f"{value:,.{digits}f}".replace(",", "’")
    return f"{formatted} {unit}".rstrip()


def show_legend(
    low: float, high: float, unit: str, digits: int, *,
    logarithmic: bool, has_missing: bool,
) -> None:
    start, end = MAP_GRADIENT
    inverse = expm1 if logarithmic else float
    fractions = (0, 0.25, 0.5, 0.75, 1) if high != low else (0.5,)
    ticks = "".join(
        f"<span>{format_value(inverse(low + (high - low) * fraction), '', digits)}</span>"
        for fraction in fractions
    )
    st.html(
        '<div aria-label="Farblegende">'
        f'<div style="height:.65rem;border-radius:.25rem;background:linear-gradient(90deg,{start},{end})"></div>'
        f'<div style="display:flex;justify-content:space-between;font-size:.8rem">{ticks}</div>'
        '</div>'
    )
    st.caption(f"{unit} · logarithmische Farbskala" if logarithmic else f"{unit} · lineare Farbskala")
    if has_missing:
        st.caption("Grau: keine Angabe")


@st.fragment
def render_municipality_profile(
    chart_key: str, municipalities: pd.DataFrame, variable: str
) -> None:
    selection_key = f"{chart_key}_municipality"
    selected_id = st.session_state.get(selection_key)
    result = map_click(
        key=f"{chart_key}_click",
        data={"chartKey": chart_key, "selectedId": selected_id, "variable": variable},
        default={"municipality": selected_id},
        on_municipality_change=lambda: None,
    )
    municipality_id = result.municipality
    if municipality_id in municipalities.index:
        selected_id = municipality_id
        st.session_state[selection_key] = selected_id
    show_municipality(selected_id, municipalities, variable)


def show_municipality(
    municipality_id: int | None, municipalities: pd.DataFrame, variable: str
) -> None:
    with st.container(border=True, height=MAP_HEIGHT):
        st.subheader("Gemeindeprofil")
        if municipality_id is None:
            st.write("Klicke auf eine Gemeinde in der Karte.")
            return

        row = municipalities.loc[municipality_id]
        st.markdown(f"**{row['name']}**")
        st.caption(f"{row['canton']} · BFS-Nr. {municipality_id}")
        label, unit, digits = INDICATORS[variable]
        st.metric(f"{label} {YEAR}", format_value(row[variable], unit, digits))

        st.markdown(f"**Kennzahlen {YEAR}**")
        st.write(f"Einwohnerzahl: **{format_value(row['population'], '', 0)}**")
        for field, (label, unit, digits) in INDICATORS.items():
            if field != variable:
                st.write(f"{label}: **{format_value(row[field], unit, digits)}**")
        st.caption("Bevölkerungsdichte: Einwohnerzahl 2019, Fläche 2016.")
        count = row["n_votes_2019"]
        st.caption(f"Stimmbeteiligung aus {0 if pd.isna(count) else int(count)} von 3 Abstimmungen.")


def render_municipality_map(*, zurich_only: bool) -> None:
    try:
        indicators, features = load_map_data()
    except FileNotFoundError as error:
        missing_file = Path(error.filename).name if error.filename else "unbekannt"
        st.error(f"Die Karte kann nicht geladen werden. Fehlende Projektdatei: {missing_file}")
        return

    scope = "zuerich" if zurich_only else "schweiz"
    variable = st.selectbox(
        f"Kennzahl für {YEAR}", options=list(INDICATORS),
        format_func=lambda field: INDICATORS[field][0], key=f"{scope}_indicator",
        width=390,
    )
    _, unit, digits = INDICATORS[variable]
    values = indicators[variable]
    is_density = variable == "population_density"
    chart_key = f"{scope}_plotly_map"

    if zurich_only:
        features = [
            feature for feature in features
            if feature["properties"]["kantonsnummer"] == ZURICH_CANTON
        ]
    municipalities = pd.DataFrame(
        feature["properties"] for feature in features
    ).drop_duplicates(subset="bfs_nummer").set_index("bfs_nummer").join(indicators)
    local_values = municipalities[variable]
    municipalities["display_value"] = [
        format_value(value, unit, digits) for value in local_values
    ]

    # Der Schweizer Wertebereich gilt auch für den Ausschnitt Zürich.
    transform = log1p if is_density else float
    valid = values.dropna()
    low = 0.0 if is_density or valid.empty else transform(valid.min())
    high = low if valid.empty else transform(valid.max())
    span = high - low
    missing = f"rgb{MISSING_COLOR}"
    start_color, end_color = MAP_GRADIENT
    # Reserviere -1 für fehlende Werte, ausserhalb des Verlaufs von 0 bis 1.
    scale = [(0, missing), (0.5, missing), (0.5, start_color), (1, end_color)]
    municipalities["color_value"] = [
        -1 if pd.isna(value) else (transform(value) - low) / span if span else 0.5
        for value in local_values
    ]
    fig = px.choropleth(
        municipalities,
        geojson={"type": "FeatureCollection", "features": features},
        locations=municipalities.index,
        featureidkey="properties.bfs_nummer",
        hover_name="name",
        custom_data=[municipalities.index, "display_value"],
        color="color_value",
        color_continuous_scale=scale,
        range_color=(-1, 1),
        basemap_visible=False,
    )
    transparent = "rgba(0, 0, 0, 0)"
    longitude, latitude = (
        ([7.873, 9.387], [46.98, 47.82]) if zurich_only else ([5.12, 11.28], [45.15, 48.60])
    )
    fig.update_geos(
        bgcolor=transparent, projection_type="mercator",
        lonaxis_range=longitude, lataxis_range=latitude,
    )
    fig.update_layout(
        paper_bgcolor=transparent,
        plot_bgcolor=transparent,
        coloraxis_showscale=False,
        clickmode="event",
        dragmode="pan",
        uirevision=scope,
        margin=dict(l=0, r=0, t=0, b=0),
    )
    fig.update_traces(
        marker_line_color="rgba(99, 122, 141, 0.9)",
        marker_line_width=0.75,
        hovertemplate="<b>%{hovertext}</b><br>%{customdata[1]}<extra></extra>",
    )

    map_column, details = st.columns([2, 1], gap="medium")
    with map_column:
        with st.container(key=chart_key):
            st.plotly_chart(fig, height=MAP_HEIGHT, config={"displayModeBar": False, "scrollZoom": True})
        show_legend(
            low, high, unit, 0 if is_density else digits,
            logarithmic=is_density, has_missing=local_values.isna().any(),
        )
        if is_density:
            st.caption("Bevölkerungsdichte: Einwohnerzahl 2019, Fläche 2016.")
    with details:
        render_municipality_profile(chart_key, municipalities, variable)

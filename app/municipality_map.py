import json
from math import expm1, log1p
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
YEAR = 2019
ZURICH_CANTON = 1
MAP_HEIGHT = 670
YEAR_CONTROLS_HEIGHT = 155

# Labels, display units and precision for each mapped indicator.
INDICATORS = {
    "turnout_2019": ("Average voter turnout", "%", 1),
    "population_density": ("Population density", "people/km²", 1),
    "share_age_0_19": ("Share aged 0–19", "%", 1),
    "share_age_65plus": ("Share aged 65 and over", "%", 1),
    "share_foreign": ("Share of foreign nationals", "%", 1),
    "social_assistance_rate": ("Social assistance rate", "%", 1),
}
ZURICH_INDICATORS = {
    "turnout": INDICATORS["turnout_2019"],
    "population_density": INDICATORS["population_density"],
    "foreigner_rate": INDICATORS["share_foreign"],
    "social_assistance_rate": INDICATORS["social_assistance_rate"],
    "unemployment_rate": ("Unemployment rate (ages 15–64)", "%", 1),
    "tertiary_share": ("Tertiary education attainment (ages 25–64)", "%", 1),
    "median_income": ("Median taxable income", "CHF", 0),
    "old_age_ratio": ("Old-age dependency ratio (65+)", "per 100 aged 20–64", 1),
}
MAP_GRADIENT = ("#ffe46b", "#b71932")
MISSING_COLOR = (145, 151, 160)

map_click = st.components.v2.component(
    "map_click",
    js=Path(__file__).with_name("map_click.mjs").read_text(encoding="utf-8"),
)


@st.cache_data
def load_swiss_indicators() -> pd.DataFrame:
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
    return indicators.set_index("GDENR").join(turnout, validate="one_to_one")


@st.cache_data
def load_zurich_panel() -> pd.DataFrame:
    panel = pd.read_csv(DATA_DIR / "clean_data" / "zh_regression_panel.csv")
    return panel.set_index(["year", "GDENR"], verify_integrity=True).sort_index()


@st.cache_data
def load_municipal_features() -> list[dict]:
    with (DATA_DIR / "raw_data/app_data/municipalities_api_50m.geojson").open(encoding="utf-8") as file:
        features = json.load(file)["features"]

    return [
        feature for feature in features
        if feature["properties"].get("kantonsnummer") is not None
    ]


def format_value(value: float, unit: str, digits: int) -> str:
    if pd.isna(value):
        return "No data"
    formatted = f"{value:,.{digits}f}"
    if unit == "%":
        return f"{formatted}%"
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
        '<div aria-label="Colour legend">'
        f'<div style="height:.65rem;border-radius:.25rem;background:linear-gradient(90deg,{start},{end})"></div>'
        f'<div style="display:flex;justify-content:space-between;font-size:.8rem">{ticks}</div>'
        '</div>'
    )
    st.caption(f"{unit} · logarithmic colour scale" if logarithmic else f"{unit} · linear colour scale")
    if has_missing:
        st.caption("Grey indicates missing data.")


@st.fragment
def render_municipality_profile(
    chart_key: str, municipalities: pd.DataFrame, variable: str, labels: dict,
    year: int, panel: pd.DataFrame | None, years: list[int],
) -> None:
    selection_key = f"{chart_key}_municipality"
    selected_id = st.session_state.get(selection_key)
    result = map_click(
        key=f"{chart_key}_click",
        data={
            "chartKey": chart_key,
            "selectedId": selected_id,
            "variable": variable,
            "timeline": panel is not None,
        },
        default={"municipality": selected_id, "year": year},
        on_municipality_change=lambda: None,
        on_year_change=lambda: None,
    )
    if result.municipality in municipalities.index:
        selected_id = result.municipality
        st.session_state[selection_key] = selected_id
    if panel is not None:
        if result.year in years:
            year = result.year
        st.session_state[f"{chart_key}_year"] = year
        municipalities = municipalities.join(panel.loc[year])

    with st.container(border=True, height=MAP_HEIGHT):
        st.subheader("Municipality profile")
        if selected_id is None:
            st.write("Click a municipality on the map.")
            return

        row = municipalities.loc[selected_id]
        st.markdown(f"**{row['name']}**")
        st.caption(f"{row['canton']} · FSO municipality code {selected_id}")
        label, unit, digits = labels[variable]
        st.metric(f"{label} {year}", format_value(row[variable], unit, digits))
        st.markdown(f"**Indicators for {year}**")
        if panel is None:
            st.write(f"Population: **{format_value(row['population'], '', 0)}**")
        for field, (label, unit, digits) in labels.items():
            if field != variable:
                st.write(f"{label}: **{format_value(row[field], unit, digits)}**")
        if panel is None:
            st.caption("Population density uses 2019 population and 2016 land area.")
            count = row["n_votes_2019"]
            st.caption(f"Turnout is based on {0 if pd.isna(count) else int(count)} of the 3 federal votes.")


def map_colors(values: pd.Series, transform, low: float, high: float) -> list[float]:
    span = high - low
    colors = (values.map(transform, na_action="ignore") - low) / span if span else values.where(values.isna(), 0.5)
    return colors.fillna(-1).tolist()


def consecutive_years(values: pd.Series) -> list[int]:
    years = sorted(values.dropna().index.get_level_values("year").unique().tolist())
    if not years:
        return []
    # Pick the longest annual run, favouring the more recent one in a tie.
    starts = [0, *[
        i for i, (previous, current) in enumerate(zip(years, years[1:]), start=1)
        if current != previous + 1
    ]]
    start, end = max(
        zip(starts, [*starts[1:], len(years)]),
        key=lambda run: (run[1] - run[0], run[1]),
    )
    return years[start:end]


def add_year_controls(fig: go.Figure, frames: list[go.Frame], years: list[int], year: int) -> None:
    fig.frames = frames
    jump = dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0))
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=YEAR_CONTROLS_HEIGHT),
        sliders=[dict(
            active=years.index(year), x=0, len=1, y=0, yanchor="top", pad=dict(t=12),
            currentvalue=dict(prefix="Year: ", font=dict(size=14)), transition=dict(duration=0),
            steps=[
                dict(label=str(value), method="animate", args=[[str(value)], jump])
                for value in years
            ],
        )],
        updatemenus=[dict(
            type="buttons", direction="right", showactive=False,
            x=0, xanchor="left", y=0, yanchor="top", pad=dict(t=105), font=dict(size=13),
            buttons=[
                dict(label="▶ Play", method="animate", args=[None, dict(
                    mode="immediate", fromcurrent=True,
                    frame=dict(duration=500, redraw=True), transition=dict(duration=0),
                )]),
                dict(label="❚❚ Pause", method="animate", args=[[], jump]),
            ],
        )],
    )


def render_municipality_map(*, zurich_only: bool) -> None:
    try:
        features = load_municipal_features()
        panel = load_zurich_panel() if zurich_only else None
        indicators = panel if panel is not None else load_swiss_indicators()
    except FileNotFoundError as error:
        missing_file = Path(error.filename).name if error.filename else "unknown"
        st.error(f"The map could not load because a project file is missing: {missing_file}")
        return

    scope = "zuerich" if zurich_only else "schweiz"
    labels = ZURICH_INDICATORS if zurich_only else INDICATORS
    variable = st.selectbox(
        "Indicator" if zurich_only else f"Indicator for {YEAR}", options=list(labels),
        format_func=lambda field: labels[field][0], key=f"{scope}_indicator",
        width=390,
    )
    _, unit, digits = labels[variable]
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
    ).drop_duplicates(subset="bfs_nummer").set_index("bfs_nummer")
    if panel is None:
        municipalities = municipalities.join(indicators)
        local_values = municipalities[variable]
        years = []
        year = YEAR
    else:
        municipalities["canton"] = "Zurich"
        years = consecutive_years(values)
        if not years:
            st.info("No annual data are available for this indicator.")
            return
        last_year = st.session_state.get(f"{chart_key}_year", YEAR)
        year = min(years, key=lambda candidate: abs(candidate - last_year))
        local_values = panel.loc[year, variable].reindex(municipalities.index)
        values = values[values.index.get_level_values("year").isin(years)]

    # Fix the scale across the entire period, so colours remain comparable between years.
    transform = log1p if is_density else float
    valid = values.dropna()
    low = 0.0 if is_density or valid.empty else transform(valid.min())
    high = low if valid.empty else transform(valid.max())
    missing = f"rgb{MISSING_COLOR}"
    start_color, end_color = MAP_GRADIENT
    scale = [(0, missing), (0.5, missing), (0.5, start_color), (1, end_color)]
    municipalities["color_value"] = map_colors(local_values, transform, low, high)
    municipalities["display_value"] = [format_value(value, unit, digits) for value in local_values]

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

    has_missing = -1 in municipalities["color_value"].array
    if panel is not None:
        frames = []
        municipality_ids = municipalities.index.tolist()
        for frame_year in years:
            frame_values = panel.loc[frame_year, variable].reindex(municipalities.index)
            frame_colors = map_colors(frame_values, transform, low, high)
            has_missing = has_missing or -1 in frame_colors
            frames.append(go.Frame(
                name=str(frame_year), traces=[0],
                data=[go.Choropleth(
                    z=frame_colors,
                    customdata=[
                        [number, format_value(value, unit, digits)]
                        for number, value in zip(municipality_ids, frame_values)
                    ],
                )],
            ))
        add_year_controls(fig, frames, years, year)

    map_column, details = st.columns([2, 1], gap="medium")
    with map_column:
        with st.container(key=chart_key):
            st.plotly_chart(
                fig, height=MAP_HEIGHT + (YEAR_CONTROLS_HEIGHT if zurich_only else 0),
                config={"displayModeBar": False, "scrollZoom": True},
            )
        show_legend(
            low, high, unit, 0 if is_density else digits,
            logarithmic=is_density,
            has_missing=has_missing,
        )
        if zurich_only:
            st.caption("The colour scale is fixed across the years shown. Municipal boundaries are from 2026.")
        elif is_density:
            st.caption("Population density uses 2019 population and 2016 land area.")
    with details:
        render_municipality_profile(chart_key, municipalities, variable, labels, year, panel, years)

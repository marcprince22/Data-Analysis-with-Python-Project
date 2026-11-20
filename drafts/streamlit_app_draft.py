import streamlit as st
import json
from pathlib import Path
import pandas as pd
import plotly.express as px

# For mockup numbers to color municipalities
from random import Random

# -----------------------streamlit configuration-----------------------
st.set_page_config(layout="wide")

st.html("""
<style>
.st-key-map_panel {
    height: 82dvh;
}
</style>
""")

# -----------------------data-----------------------

project_root = Path(__file__).resolve().parents[1]
geojson_path = (
    project_root / "data" / "raw_data" / "app_data" / "municipalities_api_50m.geojson"
)


@st.cache_data
def load_municipalities(path: Path, modified_at: int) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


municipalities = load_municipalities(
    geojson_path,
    geojson_path.stat().st_mtime_ns,
)

swiss_features = [
    feature
    for feature in municipalities["features"]
    if feature["properties"].get("kantonsnummer") is not None
]
swiss_geojson = {"type": "FeatureCollection", "features": swiss_features}

swiss_municipalities = (
    pd.DataFrame(feature["properties"] for feature in swiss_features)[
        ["bfs_nummer", "name"]
    ]
    .drop_duplicates(subset="bfs_nummer")
    .sort_values("bfs_nummer")
)

rng = Random(42)
swiss_municipalities["demo_value"] = [
    rng.randint(0, 100) for _ in range(len(swiss_municipalities))
]

fig = px.choropleth(
    swiss_municipalities,
    geojson=swiss_geojson,
    locations="bfs_nummer",
    featureidkey="properties.bfs_nummer",
    hover_name="name",
    hover_data={"bfs_nummer": False, "demo_value": True},
    color="demo_value",
    color_continuous_scale="Blues",
    range_color=(0, 100),
    labels={"demo_value": "Zufallswert"},
    fitbounds="locations",
    basemap_visible=False,
)

transparent = "rgba(0, 0, 0, 0)"
fig.update_geos(bgcolor=transparent)
fig.update_layout(
    paper_bgcolor=transparent,
    plot_bgcolor=transparent,
)
fig.update_traces(
    marker_line_color="rgba(100, 116, 139, 0.55)",
    marker_line_width=0.35,
)

fig.update_layout(
    autosize=True,
    height=None,
    margin=dict(l=0, r=0, t=10, b=0),
)
_, map_column, _ = st.columns([1, 8, 1], gap=None)

with map_column:
    st.title("Schweizer Gemeinden")
    st.html("""
    <div style="font-size: 25px !important; line-height: 1.5;">
        In unsere Seminararbeit haben wir die Wahlbeteiligung Schweizer Gemeinden
        auf sozioökonomische Faktoren verglichen. Die Ergebnisse sind als reine
        Korrelationsanalyse gedacht und sollten nicht als Kausalität interpretiert werden.
    </div>
    """)
    with st.container(key="map_panel", height=850, border=False):
        st.plotly_chart(fig, width="stretch", height="stretch")

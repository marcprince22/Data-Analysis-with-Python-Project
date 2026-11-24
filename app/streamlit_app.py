import streamlit as st

from municipality_map import render_municipality_map


def show_placeholder(label: str) -> None:
    st.html(f'<div class="atlas-placeholder"><span>{label}</span></div>')


def overview() -> None:
    st.title("Gemeindeatlas")
    st.markdown(
        "In unserer Seminararbeit untersuchen wir die Stimmbeteiligung in "
        "Schweizer Gemeinden und ihren Zusammenhang mit sozioökonomischen Merkmalen."
    )

    st.markdown(
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
        "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
        "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute "
        "irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
        "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia "
        "deserunt mollit anim id est laborum. Integer posuere erat a ante venenatis dapibus "
        "posuere velit aliquet. Curabitur blandit tempus porttitor, donec ullamcorper nulla "
        "non metus auctor fringilla. Maecenas faucibus mollis interdum. Vivamus sagittis "
        "lacus vel augue laoreet rutrum faucibus dolor auctor. Praesent commodo cursus "
        "magna, vel scelerisque nisl consectetur et. Aenean lacinia bibendum nulla sed "
        "consectetur. Cras mattis consectetur purus sit amet fermentum. Donec sed odio dui. "
        "Nullam quis risus eget urna mollis ornare vel eu leo. Morbi leo risus, porta ac "
        "consectetur ac, vestibulum at eros."
    )
    st.space("small")

    with st.container(border=True):
        summary, chart = st.columns([3, 2], gap="medium", vertical_alignment="center")
        with summary:
            st.subheader("Schweiz")
            st.write(
                "Stimmbeteiligung im Gemeindevergleich über die ganze Schweiz.\n\n"
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod "
                "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, "
                "quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
            )
            st.page_link(swiss_page, label="Schweiz erkunden", icon=":material/arrow_forward:")
        with chart:
            show_placeholder("Diagramm zur Schweiz")

    with st.container(border=True):
        chart, summary = st.columns([2, 3], gap="medium", vertical_alignment="center")
        with chart:
            show_placeholder("Diagramm zu Zürich")
        with summary:
            st.subheader("Zürich")
            st.write(
                "Ein genauerer Blick auf die Gemeinden im Kanton Zürich.\n\n"
                "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore "
                "eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt "
                "in culpa qui officia deserunt mollit anim id est laborum."
            )
            st.page_link(zurich_page, label="Zürich erkunden", icon=":material/arrow_forward:")


def region(name: str, *, zurich_only: bool = False) -> None:
    st.title(name)
    render_municipality_map(zurich_only=zurich_only)

    st.header("Ergebnisse")
    for title, description, placeholder in (
        (
            "Verteilung",
            "Wie verteilt sich die Stimmbeteiligung über die Gemeinden?",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
            "incididunt ut labore et dolore magna aliqua. Aenean eu leo quam. Pellentesque ornare "
            "sem lacinia quam venenatis vestibulum. Donec id elit non mi porta gravida at eget metus.",
        ),
        (
            "Gemeindevergleich",
            "Wie stark unterscheidet sich die Beteiligung zwischen Gemeinden?",
            "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut "
            "aliquip ex ea commodo consequat. Integer posuere erat a ante venenatis dapibus posuere "
            "velit aliquet. Maecenas faucibus mollis interdum. Sed posuere consectetur est at lobortis.",
        ),
        (
            "Zusammenhänge",
            "Wie hängt die Beteiligung mit sozioökonomischen Merkmalen zusammen?",
            "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore "
            "eu fugiat nulla pariatur. Cras mattis consectetur purus sit amet fermentum. Praesent "
            "commodo cursus magna, vel scelerisque nisl consectetur et. Nullam id dolor id nibh ultricies.",
        ),
    ):
        with st.container(border=True):
            chart, explanation = st.columns([1, 2], gap="medium", vertical_alignment="center")
            with chart:
                show_placeholder(f"Diagramm · {title}")
            with explanation:
                st.subheader(title, anchor=False)
                st.markdown(f"{description}\n\n{placeholder}")


def switzerland() -> None:
    region("Schweiz")


def zurich() -> None:
    region("Zürich", zurich_only=True)


def data_sources() -> None:
    st.title("Woher kommen unsere Daten?")
    st.write(
        "Auf dieser Seite dokumentieren wir die Quellen, Bezugszeiträume und "
        "Aufbereitung der für die App verwendeten Daten."
    )
    with st.container(border=True):
        st.subheader("Datenquellen")


st.set_page_config(page_title="Gemeindeatlas", layout="wide")

swiss_page = st.Page(switzerland, title="Schweiz", url_path="schweiz")
zurich_page = st.Page(zurich, title="Zürich", url_path="zuerich")
current_page = st.navigation(
    [
        st.Page(overview, title="Übersicht", default=True),
        swiss_page,
        zurich_page,
        st.Page(data_sources, title="Daten", url_path="daten"),
    ],
    position="top",
)

st.html("""
<style>
/* Balance the space on either side of Streamlit's top navigation. */
@media (min-width: 640px) {
    [data-testid="stToolbar"] > div {
        display: grid;
        grid-template-columns: 8rem minmax(0, 1fr) 8rem;
    }
    [data-testid="stToolbar"] > div > :nth-child(2) {
        justify-content: center;
    }
}
.choroplethlocation.atlas-municipality-selected {
    stroke: #f3ab42 !important;
    stroke-width: 2px !important;
}
.atlas-placeholder {
    display: grid;
    place-items: center;
    min-height: 7rem;
    padding: 1rem;
    border: 1px dashed color-mix(in srgb, currentColor 25%, transparent);
    border-radius: .75rem;
    background: color-mix(in srgb, #398779 10%, transparent);
    text-align: center;
}
</style>
""")

with st.container(horizontal=True, horizontal_alignment="center"):
    width = 1250 if current_page.url_path in {"schweiz", "zuerich"} else 1100
    with st.container(width=width):
        current_page.run()

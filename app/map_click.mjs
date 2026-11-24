export default function ({ data, setStateValue }) {
    const selector = `.st-key-${data.chartKey} .js-plotly-plot`;
    const listeners = new AbortController();
    let graph;
    let previousPath;
    let selectedId = data.selectedId;
    let press;

    function markSelection() {
        const paths = graph.querySelectorAll(".choroplethlocation");
        const selectedPath = Array.from(paths).find(path => Number(path.__data__?.loc) === selectedId);
        previousPath?.classList.remove("atlas-municipality-selected");
        previousPath = selectedPath;
        previousPath?.classList.add("atlas-municipality-selected");
    }

    function trackMovement(event) {
        if (!press || press.pointerId !== event.pointerId) return;
        if (Math.hypot(event.clientX - press.x, event.clientY - press.y) > 5) {
            press.dragged = true;
        }
    }

    function selectMunicipality({ points }) {
        const id = points?.[0]?.customdata?.[0];
        if (!press || press.dragged || !Number.isInteger(id)) return;
        press = undefined;
        selectedId = id;
        markSelection();
        setStateValue("municipality", id);
    }

    function connect() {
        graph = document.querySelector(selector);
        if (typeof graph?.on !== "function") return;
        observer.disconnect();

        const options = { capture: true, signal: listeners.signal };
        graph.addEventListener("pointerdown", (event) => {
            if (event.isPrimary && event.button === 0) {
                press = { pointerId: event.pointerId, x: event.clientX, y: event.clientY, dragged: false };
            }
        }, options);
        document.addEventListener("pointermove", trackMovement, options);
        document.addEventListener("pointerup", trackMovement, options);
        document.addEventListener("pointercancel", () => { press = undefined; }, options);
        graph.on("plotly_click", selectMunicipality);
        graph.on("plotly_afterplot", markSelection);
        markSelection();
    }

    const observer = new MutationObserver(connect);
    observer.observe(document.body, { childList: true, subtree: true });
    connect();

    return () => {
        observer.disconnect();
        listeners.abort();
        graph?.removeListener?.("plotly_click", selectMunicipality);
        graph?.removeListener?.("plotly_afterplot", markSelection);
    };
}

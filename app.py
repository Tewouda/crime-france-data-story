"""Fewer thefts, more reported violence — a data story on recorded crime in France (2016–2025).

Run with:  streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Recorded crime in France 2016–2025 · Data story",
    layout="wide",
    initial_sidebar_state="expanded",
)

from sections import conclusions, data_quality, deep_dives, intro, overview, whatif  # noqa: E402
from utils.constants import DEFAULT_INDICATOR, FAMILIES, INDICATORS, PER_DWELLING, REGIONS  # noqa: E402
from utils.io import LICENSE_TEXT, department_names, load_data, load_geojson  # noqa: E402
from utils.prep import (  # noqa: E402
    clean, filter_scope, missingness_table, national_series, quality_checks,
)


# --------------------------------------------------------------------------- #
# Data (cached: loaded and cleaned once per server process)
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner="Loading département boundaries…")
def get_geo() -> dict:
    return load_geojson()


@st.cache_data(show_spinner="Downloading & cleaning SSMSI data…")
def get_data():
    geo = get_geo()
    raw = load_data()
    df = clean(raw, department_names(geo))
    geo_codes = {f["properties"]["code"] for f in geo["features"]}
    checks = quality_checks(raw, df, geo_codes)
    return raw, df, checks, missingness_table(raw)


@st.cache_data(show_spinner=False)
def get_scope(regions: tuple[str, ...], include_overseas: bool):
    _, df, _, _ = get_data()
    scope = filter_scope(df, regions, include_overseas)
    return scope, national_series(scope)


raw, df, checks, missing = get_data()
geo = get_geo()

# --------------------------------------------------------------------------- #
# Sidebar: navigation + filters (every control changes something on the page)
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("### Story chapters")
    st.markdown(
        "1. [Why it matters](#why-it-matters)\n"
        "2. [The big picture](#the-big-picture)\n"
        "3. [Where & who](#where-and-who)\n"
        "4. [What if reporting changed?](#what-if-reporting-changed)\n"
        "5. [Data quality](#data-quality)\n"
        "6. [Takeaways](#takeaways)"
    )
    st.divider()
    st.header("Filters")
    years = sorted(df["year"].unique())
    y0, y1 = st.select_slider(
        "Period (start → end year)", options=years, value=(years[0], years[-1]),
        help="Start year is the baseline (index = 100); end year is used for maps and rankings.",
    )
    if y0 == y1:
        st.warning("Pick two different years to compare.")
        y0 = years[0] if y1 != years[0] else years[1]

    region_options = sorted(REGIONS.values())
    regions = st.multiselect("Regions", region_options, placeholder="All of France",
                             help="Leave empty to analyse the whole country.")
    include_overseas = st.toggle("Include overseas départements (DROM)", value=True,
                                 help="Guadeloupe, Martinique, Guyane, La Réunion, Mayotte.")

    main_indicators = [v[0] for v in INDICATORS.values() if not v[3]]
    by_family = {v[0]: v[1] for v in INDICATORS.values()}
    ordered = sorted(main_indicators, key=lambda i: (FAMILIES.index(by_family[i]), i))
    indicator = st.selectbox(
        "Focus indicator (maps, rankings, drill-down)", ordered,
        index=ordered.index(DEFAULT_INDICATOR),
        format_func=lambda i: f"{i}  ·  {by_family[i]}",
    )
    st.divider()
    st.caption(LICENSE_TEXT)

scope, nat = get_scope(tuple(regions), include_overseas)
if scope.empty:
    st.error("No département matches these filters (e.g. only overseas regions selected with DROM excluded).")
    st.stop()

ctx = {
    "df": df,
    "raw": raw,
    "scope": scope,
    "nat": nat,
    "geo": geo,
    "checks": checks,
    "missing": missing,
    "y0": int(y0),
    "y1": int(y1),
    "regions": regions,
    "include_overseas": include_overseas,
    "indicator": indicator,
    "family": by_family[indicator],
    "unit_label": "per 1,000 dwellings" if indicator in PER_DWELLING else "per 1,000 inhabitants",
    "scope_label": ", ".join(regions) if regions else ("France" if include_overseas else "Mainland France"),
}

# --------------------------------------------------------------------------- #
# The story
# --------------------------------------------------------------------------- #
intro.render(ctx)
overview.render(ctx)
deep_dives.render(ctx)
whatif.render(ctx)
data_quality.render(ctx)
conclusions.render(ctx)

"""Chapter 5 — Data quality: validation checks, missingness, sparsity, definitions."""
import streamlit as st

from utils import viz
from utils.constants import DATASET_PAGE, SOURCES


def render(ctx: dict) -> None:
    raw, df, checks = ctx["raw"], ctx["df"], ctx["checks"]
    st.header("Data quality", anchor="data-quality", divider="gray")
    n_pass = int(checks["Status"].eq("Pass").sum())
    n_fail = int(checks["Status"].eq("Fail").sum())
    st.subheader(f"{n_pass} of {len(checks)} automated checks pass"
                 + ("; the remaining warnings concern interpretation, not errors." if n_fail == 0
                    else f"; {n_fail} check(s) FAIL — read the table below."))

    a, b, c, d = st.columns(4)
    a.metric("Rows (raw)", f"{len(raw):,}")
    b.metric("Départements", df["dep_code"].nunique())
    c.metric("Years", f"{df['year'].min()}–{df['year'].max()}")
    d.metric("Indicators", f"{df['indicator'].nunique()} (16 main + 2 sub)")

    st.dataframe(checks, hide_index=True, width="stretch")

    l, r = st.columns([1, 1.4])
    with l:
        st.markdown("**Missing values per column (raw file)**")
        st.dataframe(
            ctx["missing"], hide_index=True, width="stretch",
            column_config={"missing_pct": st.column_config.ProgressColumn(
                "Missing (%)", min_value=0, max_value=100, format="%.1f%%")},
        )
    with r:
        viz.show(
            viz.zero_heatmap(df),
            "Heatmap of the share of départements recording zero cases per indicator and year. Only "
            "homicides and attempted homicides, and fixed drug fines before 2020, have frequent zeros.",
        )

    with st.expander("Cleaning & feature-engineering steps"):
        st.markdown(
            "1. Read the CSV with `;` separator, French decimal comma and BOM-safe UTF-8; keep codes as text "
            "(`01`, `2A`, `971`).\n"
            "2. Rename to English snake_case; translate the 18 indicators; group them into 5 families.\n"
            "3. Join département names from the boundary file and region names from INSEE codes.\n"
            "4. **Recompute** each rate from counts and the right denominator (population, or dwellings for "
            "burglary) and check it against the published rate.\n"
            "5. Aggregations always **sum counts and denominators, then divide**; rates are never averaged.\n"
            "6. Exclude the two drug-use sub-indicators (fixed fines / other) from totals to avoid double counting.\n"
            "7. Derived features: % change, index (base year = 100), OLS trend per year, ratio to the average, "
            "robust z-score of log-rates (median/MAD) to flag outliers."
        )
    with st.expander("Known limitations & definition changes"):
        st.markdown(
            "- **Recording, not occurrence**: counts depend on reporting propensity and police activity.\n"
            "- **Place of commission** for most indicators, but **place of residence of the victim** for fraud.\n"
            "- **Drug offences** count persons charged when the case is solved; fixed fines (AFD) started "
            "in Sept. 2020, which mechanically raises 2020–2025 numbers.\n"
            "- **Physical violence** was redefined in July 2025 (domestic / non-domestic, including minors) "
            "and back-cast to 2016 by SSMSI, so the series is consistent but differs from older publications.\n"
            "- **Population vintages**: 2024–2025 rates use the 2023 census population; Mayotte uses 2017 "
            "throughout (its population is uncertain), so its rates are approximate.\n"
            "- **Year of recording** ≠ year of the facts: old cases (especially sexual violence) can be "
            "recorded years later, which inflates recent figures.\n"
            "- **Small numbers**: homicides are rare at département level; % changes there are noisy."
        )
    st.markdown("**Download**")
    d1, d2, d3 = st.columns(3)
    d1.download_button("Clean data, current selection (CSV)",
                       ctx["scope"].to_csv(index=False).encode("utf-8"),
                       file_name="crime_france_clean_selection.csv", mime="text/csv")
    d2.download_button("Validation report (CSV)", checks.to_csv(index=False).encode("utf-8"),
                       file_name="validation_report.csv", mime="text/csv")
    d3.link_button("Original dataset on data.gouv.fr", DATASET_PAGE)
    st.caption(f"Pinned source file: {SOURCES['crime_dep']['url']} (SHA-256 {SOURCES['crime_dep']['sha256'][:12]}…)")

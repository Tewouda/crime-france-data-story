"""Chapter 3 — Where and who: map, regional small multiples, rankings, outliers, drill-down."""
import streamlit as st

from utils import viz
from utils.prep import aggregate_series, dept_profile, dept_snapshot, scatter_fit


def render(ctx: dict) -> None:
    ind, y0, y1, unit = ctx["indicator"], ctx["y0"], ctx["y1"], ctx["unit_label"]
    scope, nat = ctx["scope"], ctx["nat"]
    snap = dept_snapshot(scope, ind, y0, y1)
    nat_ind = nat[(nat["indicator"] == ind) & nat["year"].between(y0, y1)]
    scope_rate = float(nat_ind.loc[nat_ind["year"] == y1, "rate"].iloc[0])

    st.header("Where and who", anchor="where-and-who", divider="gray")

    # ---- 3.1 Map ---------------------------------------------------------- #
    top = snap.sort_values("rate_end").iloc[-1]
    rise = snap.dropna(subset=["pct_change"]).sort_values("pct_change")
    n_up = int((snap["pct_change"] > 0).sum())
    st.subheader(
        f"{ind}: the rate rose in {n_up} of {len(snap)} départements; the highest level is in "
        f"{top['dep_name']} ({top['rate_end']:.2f} {unit})."
    )
    mode = st.segmented_control(
        "Map shows", ["Rate in end year", "Change since start year"], default="Rate in end year",
        help="Rate = recorded per 1,000 inhabitants (dwellings for burglary). Change = % change of that rate.",
    ) or "Rate in end year"
    metric = "rate" if mode.startswith("Rate") else "change"
    m1, m2 = st.columns([1.8, 1.2])
    with m1:
        viz.show(
            viz.choropleth(snap, ctx["geo"], metric, ind, unit, y0, y1),
            f"Choropleth map of French départements (overseas départements shown as insets on the left) "
            f"coloured by {'the ' + ind + ' rate in ' + str(y1) if metric == 'rate' else 'the % change in rate since ' + str(y0)}. "
            f"Highest: {top['dep_name']}. Largest increase: {rise.iloc[-1]['dep_name']} "
            f"({rise.iloc[-1]['pct_change']:+.0f}%).",
        )
    with m2:
        st.markdown("**Largest increases**")
        st.dataframe(
            rise.tail(8).iloc[::-1][["dep_name", "rate_start", "rate_end", "pct_change"]]
            .rename(columns={"dep_name": "Département", "rate_start": f"{y0} ‰",
                             "rate_end": f"{y1} ‰", "pct_change": "Change %"}),
            hide_index=True, width="stretch",
            column_config={"Change %": st.column_config.NumberColumn(format="%+.0f%%"),
                           f"{y0} ‰": st.column_config.NumberColumn(format="%.2f"),
                           f"{y1} ‰": st.column_config.NumberColumn(format="%.2f")},
        )
        st.markdown("**Smallest increases / decreases**")
        st.dataframe(
            rise.head(5)[["dep_name", "rate_start", "rate_end", "pct_change"]]
            .rename(columns={"dep_name": "Département", "rate_start": f"{y0} ‰",
                             "rate_end": f"{y1} ‰", "pct_change": "Change %"}),
            hide_index=True, width="stretch",
            column_config={"Change %": st.column_config.NumberColumn(format="%+.0f%%"),
                           f"{y0} ‰": st.column_config.NumberColumn(format="%.2f"),
                           f"{y1} ‰": st.column_config.NumberColumn(format="%.2f")},
        )
        st.caption("Small départements with few cases can show large % swings: check the counts in the tooltip.")

    # ---- 3.2 Small multiples by region ----------------------------------- #
    st.subheader("Is the trend the same in every region?")
    reg = aggregate_series(scope[(scope["indicator"] == ind) & scope["year"].between(y0, y1)],
                           ["region_name", "year"])
    reg_chg = reg.pivot(index="region_name", columns="year", values="rate")
    reg_chg = (reg_chg[y1] / reg_chg[y0] - 1) * 100
    st.markdown(
        f"Across regions, the {y0}→{y1} change in **{ind}** ranges from "
        f"**{reg_chg.min():+.0f}%** ({reg_chg.idxmin()}) to **{reg_chg.max():+.0f}%** ({reg_chg.idxmax()}). "
        "Same shared y-axis in every panel, so levels are directly comparable."
    )
    viz.show(
        viz.small_multiples(reg, nat_ind, ind, unit),
        f"Small multiples: one line chart per region showing the {ind} rate from {y0} to {y1}, with the "
        "dotted average of the selection repeated in each panel for comparison.",
    )

    # ---- 3.3 Rankings & distribution ------------------------------------- #
    st.subheader("Rankings, spread and outliers")
    r1, r2 = st.columns([1, 1.2])
    with r1:
        n = st.slider("Number of départements at each end", 3, 15, 8,
                      help="Top N (highest rates) and bottom N (lowest rates).")
        viz.show(
            viz.ranking_bar(snap, n, scope_rate, ind, unit, y1),
            f"Bar chart of the {n} départements with the highest {ind} rates (red) and the {n} lowest (blue) "
            f"in {y1}, with a dashed line at the average rate of {scope_rate:.2f}.",
        )
    with r2:
        dist = scope[(scope["indicator"] == ind) & scope["year"].between(y0, y1)]
        viz.show(
            viz.distribution_chart(dist, ind, unit),
            f"Box plots with every département as a dot, one box per year, showing how the {ind} rate is "
            "distributed across départements and whether the gap between them widens.",
        )
        q = dist.groupby("year")["rate"].quantile([0.1, 0.9]).unstack()
        ratio = q[0.9] / q[0.1]
        st.caption(
            f"Inequality: the 90th-percentile département has **{ratio[y1]:.1f}×** the rate of the "
            f"10th-percentile one in {y1} (vs {ratio[y0]:.1f}× in {y0})."
        )

    if len(snap) < 5:
        st.info("Select at least 5 départements (e.g. a larger region or all of France) to see the "
                "size-effect scatter plot and outlier detection.")
    else:
        s1, s2 = st.columns([1.3, 1])
        fit = scatter_fit(snap["population"], snap["rate_end"])
        with s1:
            viz.show(
                viz.scatter_population(snap, fit, ind, unit, y1),
                f"Scatter plot of département population (log scale) against the {ind} rate in {y1}. "
                f"The dashed fitted line has a correlation of r = {fit['r']:.2f}; outliers are highlighted in red and named.",
            )
        with s2:
            strength = "weak" if abs(fit["r"]) < 0.3 else ("moderate" if abs(fit["r"]) < 0.6 else "strong")
            direction = "higher" if fit["slope"] > 0 else "lower"
            st.markdown(
                f"**Size effect.** Population explains little of the rate on its own: correlation with "
                f"log(population) is **{strength}** (r = {fit['r']:.2f}, n = {fit['n']}); a 10× larger "
                f"département has on average a **{abs(fit['slope']):.2f} ‰ {direction}** rate."
            )
            outl = snap[snap["outlier"]].sort_values("robust_z", ascending=False)
            st.markdown(f"**Statistical outliers** (|robust z| > 2.5 on log-rate): {len(outl)}")
            if len(outl):
                st.dataframe(
                    outl[["dep_name", "rate_end", "ratio_to_scope", "robust_z"]].rename(
                        columns={"dep_name": "Département", "rate_end": f"Rate {y1}",
                                 "ratio_to_scope": "× average", "robust_z": "Robust z"}),
                    hide_index=True, width="stretch",
                    column_config={c: st.column_config.NumberColumn(format="%.2f")
                                   for c in [f"Rate {y1}", "× average", "Robust z"]},
                )
            st.caption("Correlation is not causation: urban density, tourism, police presence and reporting "
                       "habits all differ between départements.")

    # ---- 3.4 Drill-down --------------------------------------------------- #
    st.subheader("Drill-down: one département's profile")
    deps = snap.sort_values("dep_code")
    default = int(deps.reset_index(drop=True).index[deps["dep_code"].values == top["dep_code"]][0])
    dep = st.selectbox("Choose a département", deps["dep_code"].tolist(), index=default,
                       format_func=lambda c: f"{c} – {deps.set_index('dep_code').loc[c, 'dep_name']}")
    dep_name = deps.set_index("dep_code").loc[dep, "dep_name"]
    d1, d2 = st.columns([1.2, 1])
    with d1:
        prof = dept_profile(scope, dep, y1, nat)
        viz.show(
            viz.profile_bar(prof, dep_name, y1),
            f"Bar chart of {dep_name}'s rate for each indicator divided by the selection average in {y1}. "
            f"Bars beyond 1 (red) mean higher than average. Highest: {prof.iloc[-1]['indicator']} "
            f"({prof.iloc[-1]['ratio']:.2f}×); lowest: {prof.iloc[0]['indicator']} ({prof.iloc[0]['ratio']:.2f}×).",
        )
    with d2:
        dd = scope[(scope["dep_code"] == dep) & (scope["indicator"] == ind) & scope["year"].between(y0, y1)]
        viz.show(
            viz.dept_trend_chart(dd, nat_ind, dep_name, ind, unit),
            f"Line chart of the {ind} rate in {dep_name} from {y0} to {y1} compared with the dotted selection average.",
        )

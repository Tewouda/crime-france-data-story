"""Chart factory: every figure goes through here so styling stays consistent.

Conventions: one y-axis per chart, units in every axis title, hover tooltips on
every mark, blue = decrease / red = increase, family colours fixed by entity.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from utils.constants import (
    DECREASE_COLOR, DIV_SCALE, EVENTS, FAMILIES, FAMILY_COLORS, GRID, INCREASE_COLOR, INK, INK_2,
    MUTED, NATIONAL_COLOR, SEQ_SCALE, SURFACE,
)

FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"

pio.templates["story"] = go.layout.Template(
    layout=dict(
        font=dict(family=FONT, size=13, color=INK),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        colorway=list(FAMILY_COLORS.values()),
        xaxis=dict(gridcolor=GRID, linecolor="#c3c2b7", zeroline=False, tickfont=dict(color=INK_2),
                   automargin=True, title=dict(standoff=10, font=dict(color=INK_2))),
        yaxis=dict(gridcolor=GRID, linecolor="#c3c2b7", zeroline=False, tickfont=dict(color=INK_2),
                   automargin=True, title=dict(standoff=10, font=dict(color=INK_2))),
        hoverlabel=dict(font=dict(family=FONT, size=13), bgcolor="white"),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0, xanchor="left", title_text=""),
        margin=dict(l=10, r=20, t=96, b=10),
        title=dict(font=dict(size=16, color=INK), x=0.01, xanchor="left", xref="container",
                   y=0.98, yref="container", yanchor="top"),
    )
)
pio.templates.default = "story"


def show(fig: go.Figure, alt: str, key: str | None = None) -> None:
    """Render a figure followed by a text description (alt text for screen readers)."""
    st.plotly_chart(fig, theme=None, width="stretch", key=key,
                    config={"displaylogo": False, "toImageButtonOptions": {"scale": 2}})
    st.caption(f"*Chart description:* {alt}")


def fmt_pct(v: float) -> str:
    return "n/a" if pd.isna(v) else f"{v:+.0f}%"


# --------------------------------------------------------------------------- #
# Overview
# --------------------------------------------------------------------------- #
def family_index_chart(fam: pd.DataFrame, base_year: int) -> go.Figure:
    fig = go.Figure()
    last_year = fam["year"].max()
    for family in FAMILIES:
        s = fam[fam["family"] == family]
        if s.empty:
            continue
        fig.add_trace(go.Scatter(
            x=s["year"], y=s["index"], name=family, mode="lines+markers",
            line=dict(color=FAMILY_COLORS[family], width=2.5), marker=dict(size=7),
            customdata=s["count"],
            hovertemplate=f"<b>{family}</b><br>%{{x}}: index %{{y:.0f}}"
                          f"<br>%{{customdata:,.0f}} recorded<extra></extra>",
        ))
        end = s[s["year"] == last_year]
        if not end.empty:
            fig.add_annotation(x=last_year, y=end["index"].iloc[0], text=f"{end['index'].iloc[0]:.0f}",
                               showarrow=False, xanchor="left", xshift=8,
                               font=dict(color=FAMILY_COLORS[family], size=12))
    fig.add_hline(y=100, line=dict(color=MUTED, width=1, dash="dot"),
                  annotation_text=f"{base_year} level", annotation_position="bottom right",
                  annotation_font_color=INK_2)
    _add_events(fig, fam["year"].min(), last_year)
    fig.update_layout(
        title=f"Recorded offences by family, index {base_year} = 100",
        xaxis_title="Year of recording", yaxis_title=f"Index (counts, {base_year} = 100)",
        height=460, hovermode="x unified",
    )
    fig.update_xaxes(dtick=1, range=[fam["year"].min() - 0.3, last_year + 0.6])
    return fig


def _add_events(fig: go.Figure, y0: int, y1: int) -> None:
    for k, (year, label) in enumerate(EVENTS):
        if y0 <= year <= y1:
            if year == 2020:
                fig.add_vrect(x0=2019.5, x1=2020.5, fillcolor=GRID, opacity=0.5, line_width=0)
            else:
                fig.add_vline(x=year, line=dict(color=MUTED, width=1, dash="dash"))
            bottom = year == 2020  # keep the lockdown label clear of the 2017/2019 labels
            fig.add_annotation(x=year, y=0.02 if bottom else 0.99 - 0.07 * k, yref="paper", text=label,
                               showarrow=False, xanchor="left", yanchor="bottom" if bottom else "top",
                               xshift=3, align="left",
                               font=dict(size=10.5, color=INK_2), bgcolor="rgba(252,252,251,0.85)")


def change_bar(chg: pd.DataFrame, y0: int, y1: int) -> go.Figure:
    c = chg.dropna(subset=["pct_change"]).sort_values("pct_change")
    colors = np.where(c["pct_change"] >= 0, INCREASE_COLOR, DECREASE_COLOR)
    fig = go.Figure(go.Bar(
        x=c["pct_change"], y=c["indicator"], orientation="h", marker_color=colors,
        text=[fmt_pct(v) for v in c["pct_change"]], textposition="outside",
        textfont=dict(color=INK_2),
        customdata=np.stack([c["family"], c["rate_start"], c["rate_end"]], axis=1),
        hovertemplate="<b>%{y}</b> (%{customdata[0]})<br>"
                      f"Rate {y0}: %{{customdata[1]:.2f}} ‰<br>Rate {y1}: %{{customdata[2]:.2f}} ‰"
                      "<br>Change: %{x:+.1f}%<extra></extra>",
    ))
    fig.add_vline(x=0, line=dict(color=INK, width=1))
    lo, hi = min(0, c["pct_change"].min()), max(0, c["pct_change"].max())
    pad = (hi - lo) * 0.18
    fig.update_traces(cliponaxis=False)
    fig.update_layout(
        title=f"Change in rate per 1,000, {y0} → {y1}",
        xaxis_title="Change in rate (%)", yaxis_title=None, height=560, showlegend=False,
        xaxis=dict(range=[lo - 1.6 * pad, hi + pad], ticksuffix="%"),
        margin=dict(t=60, r=40), bargap=0.25,
    )
    return fig


# --------------------------------------------------------------------------- #
# Deep dives
# --------------------------------------------------------------------------- #
def choropleth(snap: pd.DataFrame, geo: dict, metric: str, indicator: str, unit_label: str,
               y0: int, y1: int) -> go.Figure:
    hover = (
        "<b>%{customdata[0]}</b> (%{location})<br>%{customdata[1]}<br>"
        f"Rate {y1}: %{{customdata[2]:.2f}} {unit_label}<br>"
        f"Rate {y0}: %{{customdata[3]:.2f}}<br>Change: %{{customdata[4]:+.0f}}%"
        "<br>Recorded: %{customdata[5]:,.0f}<extra></extra>"
    )
    custom = np.stack([snap["dep_name"], snap["region_name"], snap["rate_end"], snap["rate_start"],
                       snap["pct_change"], snap["count_end"]], axis=1)
    if metric == "rate":
        z, scale, zmid, zmin, zmax = snap["rate_end"], SEQ_SCALE, None, None, snap["rate_end"].quantile(0.98)
        cb_title, title = f"Rate {unit_label}", f"{indicator}: rate in {y1}"
    else:
        lim = float(np.nanquantile(snap["pct_change"].abs(), 0.95)) or 1.0
        z, scale, zmid, zmin, zmax = snap["pct_change"], DIV_SCALE, 0, -lim, lim
        cb_title, title = "Change (%)", f"{indicator}: change in rate {y0} → {y1}"
    fig = go.Figure(go.Choropleth(
        geojson=geo, featureidkey="properties.code", locations=snap["dep_code"], z=z,
        colorscale=scale, zmid=zmid, zmin=zmin, zmax=zmax, customdata=custom, hovertemplate=hover,
        marker_line_color="white", marker_line_width=0.5,
        colorbar=dict(title=dict(text=cb_title), thickness=12, len=0.75),
    ))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor=SURFACE, projection_type="mercator")
    fig.add_annotation(text="Overseas départements (insets, not to scale): Guadeloupe, Martinique, "
                       "Guyane, La Réunion, Mayotte (top to bottom)", x=0, y=0, xref="paper", yref="paper",
                       xanchor="left", yanchor="bottom", showarrow=False, font=dict(size=10, color=INK_2))
    fig.update_layout(title=title, height=620, margin=dict(l=0, r=0, t=50, b=0))
    return fig


def small_multiples(reg: pd.DataFrame, nat: pd.DataFrame, indicator: str, unit_label: str) -> go.Figure:
    fig = px.line(
        reg, x="year", y="rate", facet_col="region_name", facet_col_wrap=6,
        facet_row_spacing=0.09, facet_col_spacing=0.03,
        labels={"rate": unit_label, "year": "", "region_name": "Region"},
        custom_data=["region_name", "count"],
    )
    fig.update_traces(line=dict(color=FAMILY_COLORS["Violence against persons"], width=2),
                      hovertemplate="<b>%{customdata[0]}</b><br>%{x}: %{y:.2f} ‰"
                                    "<br>%{customdata[1]:,.0f} recorded<extra></extra>")
    n_facets = reg["region_name"].nunique()
    # Add the reference line to every facet via the facet axes
    for ax in [a for a in fig.layout if a.startswith("xaxis")]:
        suffix = ax.replace("xaxis", "")
        fig.add_trace(go.Scatter(
            x=nat["year"], y=nat["rate"], mode="lines", xaxis=f"x{suffix}", yaxis=f"y{suffix}",
            line=dict(color=MUTED, width=1.5, dash="dot"), name="Selected-scope average",
            showlegend=(suffix == ""), hovertemplate="Scope average: %{y:.2f} ‰<extra></extra>",
        ))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1], font=dict(size=11)))
    rows = int(np.ceil(n_facets / 6))
    fig.update_layout(title=f"{indicator}: rate by region over time (dotted = average of selection)",
                      height=max(320, 210 * rows), hovermode="closest", margin=dict(t=120),
                      legend=dict(y=1.08))
    fig.update_xaxes(tickvals=[2016, 2020, 2025], tickfont=dict(size=10))
    fig.update_yaxes(matches="y", tickfont=dict(size=10))
    fig.update_yaxes(title_text="")
    fig.add_annotation(text=unit_label, x=-0.04, y=0.5, xref="paper", yref="paper",
                       textangle=-90, showarrow=False, font=dict(color=INK_2))
    return fig


def ranking_bar(snap: pd.DataFrame, n: int, scope_rate: float, indicator: str, unit_label: str,
                year: int) -> go.Figure:
    s = snap.sort_values("rate_end")
    sel = pd.concat([s.head(n).assign(group=f"Bottom {n}"), s.tail(n).assign(group=f"Top {n}")])
    sel["label"] = sel["dep_name"] + " (" + sel["dep_code"] + ")"
    colors = np.where(sel["group"].str.startswith("Top"), INCREASE_COLOR, DECREASE_COLOR)
    fig = go.Figure(go.Bar(
        x=sel["rate_end"], y=sel["label"], orientation="h", marker_color=colors,
        text=[f"{v:.2f}" for v in sel["rate_end"]], textposition="outside", textfont=dict(color=INK_2),
        customdata=np.stack([sel["region_name"], sel["ratio_to_scope"], sel["count_end"]], axis=1),
        hovertemplate="<b>%{y}</b> – %{customdata[0]}<br>Rate: %{x:.2f} ‰"
                      "<br>%{customdata[1]:.2f}× the average<br>%{customdata[2]:,.0f} recorded<extra></extra>",
    ))
    fig.add_vline(x=scope_rate, line=dict(color=NATIONAL_COLOR, width=1.5, dash="dash"),
                  annotation_text=f"Average {scope_rate:.2f}", annotation_position="top")
    fig.update_layout(title=f"{indicator}: highest (red) and lowest (blue) rates in {year}",
                      xaxis_title=f"Rate {unit_label}", yaxis_title=None,
                      height=max(360, 28 * 2 * n + 120), showlegend=False,
                      xaxis=dict(range=[0, sel["rate_end"].max() * 1.15]))
    return fig


def distribution_chart(d: pd.DataFrame, indicator: str, unit_label: str) -> go.Figure:
    fig = px.box(d, x="year", y="rate", points="all", hover_name="dep_name",
                 hover_data={"region_name": True, "rate": ":.2f", "year": False},
                 labels={"rate": unit_label, "year": "Year", "region_name": "Region"})
    fig.update_traces(marker=dict(size=5, opacity=0.55, color=FAMILY_COLORS["Violence against persons"]),
                      line=dict(color=INK_2, width=1.2), fillcolor="rgba(42,120,214,0.10)",
                      jitter=0.4, pointpos=0)
    fig.update_layout(title=f"{indicator}: how the 101 départements spread each year",
                      height=440, showlegend=False)
    fig.update_xaxes(dtick=1)
    return fig


def scatter_population(snap: pd.DataFrame, fit: dict, indicator: str, unit_label: str, year: int) -> go.Figure:
    s = snap.copy()
    s["Status"] = np.where(s["outlier"], "Statistical outlier", "Département")
    fig = px.scatter(
        s, x="population", y="rate_end", color="Status", log_x=True, hover_name="dep_name",
        color_discrete_map={"Département": FAMILY_COLORS["Violence against persons"],
                            "Statistical outlier": INCREASE_COLOR},
        hover_data={"region_name": True, "population": ":,", "rate_end": ":.2f", "Status": False},
        labels={"population": "Population (log scale)", "rate_end": f"Rate {unit_label}",
                "region_name": "Region"},
    )
    fig.update_traces(marker=dict(size=9, line=dict(color="white", width=1)))
    xs = np.logspace(np.log10(s["population"].min()), np.log10(s["population"].max()), 50)
    fig.add_trace(go.Scatter(x=xs, y=fit["intercept"] + fit["slope"] * np.log10(xs), mode="lines",
                             line=dict(color=INK_2, dash="dash", width=1.5),
                             name=f"Linear fit on log(pop), r = {fit['r']:.2f}", hoverinfo="skip"))
    for _, row in s[s["outlier"]].iterrows():
        fig.add_annotation(x=np.log10(row["population"]), y=row["rate_end"], text=row["dep_name"],
                           showarrow=False, yshift=12, font=dict(size=11, color=INK_2))
    fig.update_layout(title=f"{indicator}: are bigger départements different? ({year})", height=460)
    return fig


def profile_bar(profile: pd.DataFrame, dep_name: str, year: int) -> go.Figure:
    p = profile.copy()
    colors = np.where(p["ratio"] >= 1, INCREASE_COLOR, DECREASE_COLOR)
    fig = go.Figure(go.Bar(
        x=p["ratio"], y=p["indicator"], orientation="h", marker_color=colors, base=0,
        text=[f"{v:.2f}×" for v in p["ratio"]], textposition="outside", textfont=dict(color=INK_2),
        customdata=np.stack([p["rate"], p["ref_rate"], p["count"]], axis=1),
        hovertemplate="<b>%{y}</b><br>%{x:.2f}× the average<br>Rate %{customdata[0]:.2f} ‰ vs "
                      "%{customdata[1]:.2f} ‰<br>%{customdata[2]:,.0f} recorded<extra></extra>",
    ))
    fig.add_vline(x=1, line=dict(color=INK, width=1.5), annotation_text="= average",
                  annotation_position="top")
    fig.update_layout(title=f"{dep_name} in {year}: rate relative to the selection average",
                      xaxis_title="Ratio to average (1 = same as average)", yaxis_title=None,
                      height=520, showlegend=False)
    fig.update_xaxes(range=[0, max(2.2, p["ratio"].max() * 1.2)])
    return fig


def dept_trend_chart(d: pd.DataFrame, nat: pd.DataFrame, dep_name: str, indicator: str,
                     unit_label: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=nat["year"], y=nat["rate"], name="Selection average", mode="lines",
                             line=dict(color=MUTED, dash="dot", width=2),
                             hovertemplate="Average %{x}: %{y:.2f} ‰<extra></extra>"))
    fig.add_trace(go.Scatter(x=d["year"], y=d["rate"], name=dep_name, mode="lines+markers",
                             line=dict(color=FAMILY_COLORS["Violence against persons"], width=2.5),
                             marker=dict(size=7), customdata=d["count"],
                             hovertemplate=f"{dep_name} %{{x}}: %{{y:.2f}} ‰"
                                           "<br>%{customdata:,.0f} recorded<extra></extra>"))
    fig.update_layout(title=f"{indicator} in {dep_name} vs average", xaxis_title="Year",
                      yaxis_title=f"Rate {unit_label}", height=380, hovermode="x unified")
    fig.update_xaxes(dtick=1)
    return fig


# --------------------------------------------------------------------------- #
# What-if
# --------------------------------------------------------------------------- #
def whatif_chart(recorded: float, reporting: float, implied: float) -> go.Figure:
    labels = ["Recorded by police", "Assumed change in reporting", "Implied change in actual victimisation"]
    vals = [recorded, reporting, implied]
    colors = [INCREASE_COLOR if v >= 0 else DECREASE_COLOR for v in vals]
    colors[1] = MUTED
    fig = go.Figure(go.Bar(x=vals, y=labels, orientation="h", marker_color=colors,
                           text=[fmt_pct(v) for v in vals], textposition="outside",
                           textfont=dict(color=INK_2),
                           hovertemplate="%{y}: %{x:+.1f}%<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=INK, width=1))
    lim = max(abs(v) for v in vals) * 1.3 + 5
    fig.update_layout(title="Decomposing recorded growth: (1 + recorded) = (1 + reporting) × (1 + actual)",
                      xaxis_title="Change over the period (%)", height=300, showlegend=False,
                      xaxis=dict(range=[-lim, lim], ticksuffix="%"))
    fig.update_yaxes(autorange="reversed")
    return fig


# --------------------------------------------------------------------------- #
# Data quality
# --------------------------------------------------------------------------- #
def zero_heatmap(df: pd.DataFrame) -> go.Figure:
    z = (df[~df["is_sub"]].assign(zero=lambda x: x["count"] == 0)
         .pivot_table(index="indicator", columns="year", values="zero", aggfunc="mean") * 100)
    z = z.loc[z.mean(axis=1).sort_values().index]
    fig = go.Figure(go.Heatmap(
        z=z.values, x=z.columns, y=z.index, colorscale=SEQ_SCALE, zmin=0, zmax=max(10, float(z.values.max())),
        hovertemplate="%{y}, %{x}: %{z:.0f}% of départements recorded 0<extra></extra>",
        colorbar=dict(title=dict(text="% zero"), thickness=12), xgap=2, ygap=2,
    ))
    fig.update_layout(title="Share of départements with zero recorded cases (sparsity → volatile rates)",
                      xaxis_title="Year", height=460)
    fig.update_xaxes(dtick=1)
    return fig
